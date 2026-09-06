#!/usr/bin/env python3
"""Pull the marketing copy that carries a company's positioning.

For each company you point it at, this finds the pages where positioning
actually lives -- home, product, platform, solutions, use cases, pricing,
comparison pages -- and extracts the fields marketers agonise over: the meta
title, the meta description, and the H1/H2/H3 heading ladder. Blog posts,
docs, careers and legal pages are skipped: they dilute the signal.

Usage:
    python3 scan_site.py blixon.com acme.io --out data/
    python3 scan_site.py https://stripe.com --out data/ --max-pages 12

Writes one JSON file per company into --out (slugified domain), plus prints a
one-line summary per company. Never raises on a single bad site; unreachable
pages are recorded with their error so the analysis can note the gap.
"""

import argparse
import concurrent.futures as futures
import gzip
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import zlib
from datetime import datetime, timezone
from html.parser import HTMLParser

# We want the page a buyer sees. Some sites serve bots a stripped "machine
# version" with none of the marketing copy, which is exactly the copy we came
# for -- so the default is a normal browser string. Use --user-agent BOT_UA
# (or any string) when a site asks to be crawled differently. robots.txt is
# honoured either way, and requests are rate-limited per site.
DEFAULT_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
BOT_UA = "Mozilla/5.0 (compatible; CompetitorLandscapeBot/1.0; +https://claude.com/claude-code)"

# Page types worth reading, highest-signal first. The number is a base score;
# shallower URLs win ties because /pricing beats /company/legacy/pricing-2019.
TYPE_PRIORITY = {
    "home": 1000,
    "pricing": 100,
    "product": 85,
    "platform": 80,
    "solutions": 72,
    "use_case": 64,
    "industry": 58,
    "features": 52,
    "compare": 44,
    "about": 30,
}

# How many of each type to keep, so one section can't crowd out the rest.
TYPE_CAP = {
    "pricing": 1, "product": 3, "platform": 2, "solutions": 2,
    "use_case": 2, "industry": 1, "features": 1, "compare": 2, "about": 1,
}

TYPE_PATTERNS = [
    ("pricing", r"/(pricing|prices?|plans|packages|subscriptions?|tariffs?|cost)(/|$|\.)"),
    ("compare", r"/(compare|comparison|vs|versus|alternatives?|competitors?)(/|$|-)"),
    ("platform", r"/(platform|technology|how-it-works|the-platform)(/|$|-)"),
    ("product", r"/(products?|solutions?/product|software|apps?|modules?|services?)(/|$|-)"),
    ("solutions", r"/(solutions?|offerings?|capabilities|what-we-do)(/|$|-)"),
    ("use_case", r"/(use-?cases?|for/|by-(role|team|need)|who-we-serve)(/|$|-)"),
    ("industry", r"/(industr(y|ies)|verticals?|sectors?|by-industry)(/|$|-)"),
    ("features", r"/(features?|benefits?|why-[a-z0-9-]+)(/|$|-)"),
    ("about", r"/(about|about-us|company|our-story|mission)(/|$|\.)"),
]

# Anchor text is often a better classifier than the URL ("Pricing" -> /plans-2).
ANCHOR_HINTS = [
    ("pricing", r"^(pricing|plans?|pricing & plans|price)$"),
    ("product", r"^(products?|product overview|our products?)$"),
    ("platform", r"^(platform|the platform|technology|how it works)$"),
    ("solutions", r"^(solutions?|what we do|capabilities|offerings?)$"),
    ("use_case", r"^(use cases?|for .+)$"),
    ("industry", r"^(industries|sectors|verticals)$"),
    ("about", r"^(about|about us|company|our story)$"),
]

# Pages that eat budget without carrying positioning.
EXCLUDE_PATTERNS = [
    r"/(blog|news|press|newsroom|article|insights?|stories|magazine)(/|$|-)",
    r"/(careers?|jobs?|hiring|life-at|team/)(/|$|-)",
    r"/(legal|privacy|terms|cookies?|gdpr|dpa|imprint|impressum|accessibility)(/|$|-)",
    r"/(docs?|documentation|developers?|api|reference|changelog|release-notes)(/|$|-)",
    r"/(help|support|faq|knowledge-?base|community|forum|status)(/|$|-)",
    r"/(login|log-in|signin|sign-in|signup|sign-up|register|account|dashboard|app)(/|$|-)",
    r"/(webinars?|events?|podcasts?|videos?|ebooks?|whitepapers?|guides?|reports?|resources?|library|academy|courses?|glossary|templates?)(/|$|-)",
    r"/(search|tag|tags|category|categories|author|archive|feed|rss|sitemap)(/|$|-)",
    r"/(investors?|shareholders?|esg|sustainability-report)(/|$|-)",
    r"/(integrations?|marketplace|connectors?|apps-directory|add-ons?)(/|$|-)",
    r"/wp-(content|admin|json)/",
    r"\.(pdf|jpg|jpeg|png|gif|svg|webp|mp4|zip|xml|json|css|js|ico|woff2?)$",
    r"/[a-z]{2}(-[a-z]{2})?/(?=.)",           # /de/, /fr-ca/ locale trees
]

CASE_STUDY_PATTERN = r"/(customers?|case-stud(y|ies)|success-stories|testimonials)(/|$|-)"

# URLs that are not worth fetching but do name other companies.
SIGNAL_PATTERNS = {
    "compare": r"/(compare|vs|versus|alternatives?|competitors?)(/|$|-)",
    "integrations": r"/(integrations?|marketplace|apps?-directory|connectors?)(/|$|-)",
    "partners": r"/(partners?|resellers?|ecosystem)(/|$|-)",
    "customers": CASE_STUDY_PATTERN,
}

CTA_PHRASES = [
    "get started", "start free", "start for free", "free trial", "try free",
    "try it free", "book a demo", "request a demo", "get a demo", "see a demo",
    "watch demo", "contact sales", "talk to sales", "talk to us", "contact us",
    "get a quote", "request a quote", "request pricing", "sign up", "start now",
    "join the waitlist", "get in touch", "buy now", "shop now", "order now",
    "apply now", "start building", "create account", "book a call",
]

SKIP_TEXT_TAGS = {"script", "style", "noscript", "svg", "template", "iframe"}
HEADING_TAGS = {"h1", "h2", "h3"}


def log(msg, quiet=False):
    if not quiet:
        print(msg, file=sys.stderr, flush=True)


def norm_space(text):
    return re.sub(r"\s+", " ", (text or "")).strip()


def collapse_repeats(text):
    """Responsive markup often ships the same headline once per breakpoint."""
    m = re.fullmatch(r"(.{4,}?)(?:\s*\1)+", text)
    return m.group(1).strip() if m else text


def slugify(value):
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "site"


class PageParser(HTMLParser):
    """Collects the fields that carry positioning, ignoring page furniture."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.meta = {}
        self.canonical = ""
        self.headings = {"h1": [], "h2": [], "h3": []}
        self.links = []            # (href, anchor_text)
        self.words = 0
        self._skip_depth = 0
        self._capture = None       # heading tag currently open
        self._buf = []
        self._in_title = False
        self._link_href = None
        self._link_buf = []

    # -- helpers -----------------------------------------------------------
    def _attr(self, attrs, key):
        for k, v in attrs:
            if k.lower() == key:
                return v or ""
        return ""

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if self._capture and tag not in SKIP_TEXT_TAGS:
            self._buf.append(" ")   # <span>Intake</span><span>and…</span>
        if tag in SKIP_TEXT_TAGS:
            self._skip_depth += 1
            return
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            name = (self._attr(attrs, "name") or self._attr(attrs, "property")
                    or self._attr(attrs, "itemprop")
                    or self._attr(attrs, "http-equiv")).lower()
            content = norm_space(self._attr(attrs, "content"))
            if name and content and name not in self.meta:
                self.meta[name] = content
        elif tag == "link":
            if "canonical" in self._attr(attrs, "rel").lower():
                self.canonical = self._attr(attrs, "href")
        elif tag in HEADING_TAGS:
            self._capture = tag
            self._buf = []
        elif tag == "a":
            self._link_href = self._attr(attrs, "href")
            self._link_buf = []

    def handle_endtag(self, tag):
        tag = tag.lower()
        if self._capture and tag not in SKIP_TEXT_TAGS and tag not in HEADING_TAGS:
            self._buf.append(" ")
        if tag in SKIP_TEXT_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if tag == "title":
            self._in_title = False
        elif tag in HEADING_TAGS and self._capture == tag:
            text = collapse_repeats(norm_space("".join(self._buf)))
            if 1 < len(text) <= 300:
                self.headings[tag].append(text)
            self._capture = None
            self._buf = []
        elif tag == "a" and self._link_href is not None:
            self.links.append((self._link_href, norm_space("".join(self._link_buf))))
            self._link_href = None
            self._link_buf = []

    def handle_data(self, data):
        if self._skip_depth:
            return
        if self._in_title:
            self.title += data
        if self._capture:
            self._buf.append(data)
        if self._link_href is not None:
            self._link_buf.append(data)
        self.words += len(data.split())


def parse_markdown_ish(text):
    """Some sites now serve an LLM-friendly markdown version. Read it too."""
    p = PageParser()
    for line in text.splitlines():
        m = re.match(r"^(#{1,3})\s+(.*)", line.strip())
        if m:
            tag = "h%d" % len(m.group(1))
            heading = norm_space(re.sub(r"[*_`\[\]]|\(https?://[^)]*\)", "", m.group(2)))
            if heading:
                p.headings[tag].append(heading)
        p.words += len(line.split())
    if p.headings["h1"]:
        p.title = p.headings["h1"][0]
    return p


class Fetcher:
    def __init__(self, ua=DEFAULT_UA, timeout=20, delay=0.7, respect_robots=True):
        self.ua = ua
        self.timeout = timeout
        self.delay = delay
        self.respect_robots = respect_robots
        self._robots = {}
        self._last_hit = 0.0
        self._ctx = ssl.create_default_context()

    def _wait(self):
        gap = time.time() - self._last_hit
        if gap < self.delay:
            time.sleep(self.delay - gap)
        self._last_hit = time.time()

    def get(self, url, tries=2):
        """Return (final_url, status, text, error). Never raises."""
        last_err = ""
        for attempt in range(tries):
            self._wait()
            req = urllib.request.Request(url, headers={
                "User-Agent": self.ua,
                "Accept": "text/html,application/xhtml+xml,text/markdown;q=0.9,*/*;q=0.5",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate",
            })
            try:
                with urllib.request.urlopen(req, timeout=self.timeout, context=self._ctx) as resp:
                    raw = resp.read(3_000_000)
                    enc = (resp.headers.get("Content-Encoding") or "").lower()
                    if "gzip" in enc:
                        raw = gzip.decompress(raw)
                    elif "deflate" in enc:
                        raw = zlib.decompress(raw, -zlib.MAX_WBITS)
                    ctype = (resp.headers.get("Content-Type") or "").lower()
                    charset = "utf-8"
                    m = re.search(r"charset=([\w-]+)", ctype)
                    if m:
                        charset = m.group(1)
                    text = raw.decode(charset, errors="replace")
                    return resp.geturl(), resp.status, text, ctype, ""
            except urllib.error.HTTPError as e:
                return url, e.code, "", "", "HTTP %s" % e.code
            except Exception as e:                      # noqa: BLE001 - report, don't crash
                last_err = "%s: %s" % (type(e).__name__, e)
                if attempt + 1 < tries:
                    time.sleep(1.0)
        return url, 0, "", "", last_err

    def allowed(self, url):
        if not self.respect_robots:
            return True
        parts = urllib.parse.urlsplit(url)
        root = "%s://%s" % (parts.scheme, parts.netloc)
        if root not in self._robots:
            rp = urllib.robotparser.RobotFileParser()
            _, status, text, _, _ = self.get(root + "/robots.txt", tries=1)
            if status == 200 and text:
                try:
                    rp.parse(text.splitlines())
                except Exception:                        # noqa: BLE001
                    rp = None
            else:
                rp = None
            self._robots[root] = rp
        rp = self._robots[root]
        if rp is None:
            return True
        try:
            return rp.can_fetch(self.ua, url) or rp.can_fetch("*", url)
        except Exception:                                # noqa: BLE001
            return True


def classify(url, anchor_text=""):
    path = urllib.parse.urlsplit(url).path.lower() or "/"
    if path in ("/", ""):
        return "home"
    probe = path if path.endswith("/") else path + "/"
    for name, pattern in TYPE_PATTERNS:
        if re.search(pattern, probe):
            return name
    text = norm_space(anchor_text).lower()
    for name, pattern in ANCHOR_HINTS:
        if text and re.match(pattern, text):
            return name
    return ""


def excluded(url, include_case_studies=False):
    path = urllib.parse.urlsplit(url).path.lower() or "/"
    probe = path if path.endswith("/") else path + "/"
    if not include_case_studies and re.search(CASE_STUDY_PATTERN, probe):
        return True
    return any(re.search(p, probe) for p in EXCLUDE_PATTERNS)


def same_site(url, domain):
    host = urllib.parse.urlsplit(url).netloc.lower().split(":")[0]
    host = host[4:] if host.startswith("www.") else host
    base = domain[4:] if domain.startswith("www.") else domain
    return host == base or host.endswith("." + base)


def clean_url(base, href):
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
        return ""
    url = urllib.parse.urljoin(base, href.strip())
    parts = urllib.parse.urlsplit(url)
    if parts.scheme not in ("http", "https"):
        return ""
    path = re.sub(r"//+", "/", parts.path) or "/"
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, path, "", ""))


def sitemap_urls(fetcher, root, limit=3000):
    """Best-effort sitemap crawl: robots.txt pointers, then /sitemap.xml."""
    seeds, seen, out = [], set(), []
    _, status, text, _, _ = fetcher.get(root + "/robots.txt", tries=1)
    if status == 200:
        seeds += [urllib.parse.urljoin(root + "/", u)
                  for u in re.findall(r"(?im)^\s*sitemap:\s*(\S+)", text)]
    seeds += [root + "/sitemap.xml", root + "/sitemap_index.xml"]
    queue, fetched = list(dict.fromkeys(seeds)), 0
    while queue and fetched < 4 and len(out) < limit:
        sm = queue.pop(0)
        if sm in seen:
            continue
        seen.add(sm)
        _, status, text, _, _ = fetcher.get(sm, tries=1)
        fetched += 1
        if status != 200 or not text:
            continue
        locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", text)
        if "<sitemapindex" in text[:2000].lower():
            queue += [u for u in locs[:4] if u not in seen]
        else:
            out += locs
    return out[:limit]


CLIENT_REDIRECT = re.compile(
    r"""(?:window\.)?location(?:\.href|\.replace\()?\s*[=(]\s*["']([^"']{2,300})["']""")


def client_redirect_target(text, meta, base):
    """Parked domains and splash pages bounce you with JS or a meta refresh."""
    refresh = meta.get("refresh", "")
    m = re.search(r"url\s*=\s*['\"]?([^'\";]+)", refresh, re.I)
    if m:
        return urllib.parse.urljoin(base, m.group(1).strip())
    m = CLIENT_REDIRECT.search(text[:4000])
    if m:
        target = m.group(1).strip()
        host = urllib.parse.urlsplit(base).netloc
        # Only follow within the same site: an off-site bounce is a different company.
        if not target.startswith(("http", "//")) or host in target:
            return urllib.parse.urljoin(base, target)
    return ""


def extract_page(fetcher, url, page_type, notes, _followed=False):
    if not fetcher.allowed(url):
        notes.append("robots.txt disallows %s" % url)
        return None
    final_url, status, text, ctype, err = fetcher.get(url)
    page = {
        "url": url, "final_url": final_url, "page_type": page_type,
        "status": status, "error": err, "title": "", "meta_description": "",
        "og_title": "", "og_description": "", "canonical": "",
        "h1": [], "h2": [], "h3": [], "word_count": 0, "ctas": [],
    }
    if status != 200 or not text:
        return page
    if "html" in ctype or "<html" in text[:2000].lower():
        p = PageParser()
        try:
            p.feed(text)
        except Exception as e:                            # noqa: BLE001
            page["error"] = "parse: %s" % e
    else:
        p = parse_markdown_ish(text)
        page["error"] = page["error"] or "non-html body parsed as markdown"
    if not _followed and p.words < 40 and not p.headings["h1"]:
        target = client_redirect_target(text, p.meta, final_url)
        if target and target.rstrip("/") != final_url.rstrip("/"):
            notes.append("followed client-side redirect %s -> %s" % (final_url, target))
            deeper = extract_page(fetcher, target, page_type, notes, _followed=True)
            if deeper and deeper["status"] == 200:
                return deeper
    if re.search(r"machine[- ]version|llms?\.txt|agent[- ]friendly version", text[:1500], re.I):
        notes.append("%s served an agent/machine version rather than the marketing page" % url)
    page["title"] = norm_space(p.title)[:300]
    page["meta_description"] = p.meta.get("description", "")[:600]
    page["og_title"] = p.meta.get("og:title", "")[:300]
    page["og_description"] = p.meta.get("og:description", "")[:600]
    page["canonical"] = p.canonical
    page["h1"] = p.headings["h1"][:5]
    page["h2"] = p.headings["h2"][:25]
    page["h3"] = p.headings["h3"][:35]
    page["word_count"] = p.words
    ctas, seen = [], set()
    for _, text_ in p.links:
        low = text_.lower().strip(" →›»·|")
        if 2 < len(low) <= 40 and any(ph in low for ph in CTA_PHRASES) and low not in seen:
            seen.add(low)
            ctas.append(text_.strip())
    page["ctas"] = ctas[:6]
    page["_links"] = [(clean_url(final_url, h), t) for h, t in p.links]
    page["_site_name"] = p.meta.get("og:site_name", "")
    return page


def guess_name(title, site_name, domain):
    """Pick the brand out of an SEO title by matching it against the domain."""
    root = re.split(r"[.\-]", domain)[0].lower()
    parts = [p.strip() for p in re.split(r"\s[|\u2013\u2014\u00b7\-:]\s|\|", title or "") if p.strip()]
    if site_name:
        return site_name
    for part in parts:
        if re.sub(r"[^a-z0-9]", "", part.lower()) == root:
            return part
    for part in parts:
        if root in re.sub(r"[^a-z0-9]", "", part.lower()):
            return part
    return min(parts, key=len) if parts else domain


def named_competitors(urls, headings, own_name):
    """Comparison pages name rivals outright -- the cheapest signal there is."""
    found, own = [], own_name.lower()
    for url in urls:
        path = urllib.parse.urlsplit(url).path.lower()
        m = re.search(r"/(?:compare|vs|versus|alternatives?|competitors?)/([a-z0-9\-]+)", path)
        if not m:
            continue
        for chunk in re.split(r"-vs-|-versus-|-alternative[s]?", m.group(1)):
            name = norm_space(chunk.replace("-", " "))
            if 2 < len(name) < 30 and name.lower() not in (own, "us", "the competition"):
                found.append(name.title())
    for text in headings:
        for m in re.finditer(
            r"(?:vs\.?|versus|alternative to|compared to|switch from)\s+([A-Z][\w&.\-]*(?:\s+[A-Z][\w&.\-]*)?)",
            text,
        ):
            name = norm_space(m.group(1))
            if 2 < len(name) < 30 and name.lower() != own:
                found.append(name)
    out, seen = [], set()
    for n in found:
        if n.lower() not in seen:
            seen.add(n.lower())
            out.append(n)
    return out[:25]


def scan_company(target, fetcher, max_pages=8, include_case_studies=False, quiet=False):
    raw = target.strip()
    if not raw.startswith("http"):
        raw = "https://" + raw.lstrip("/")
    parts = urllib.parse.urlsplit(raw)
    domain = parts.netloc.lower().split(":")[0]
    domain = domain[4:] if domain.startswith("www.") else domain
    root = "%s://%s" % (parts.scheme, parts.netloc)
    notes = []

    result = {
        "slug": slugify(domain), "input": target, "domain": domain, "name": "",
        "final_url": "", "reachable": False,
        "scanned_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pages": [], "signal_urls": {}, "named_competitors": [],
        "sitemap_urls_seen": 0, "notes": notes,
    }

    home = extract_page(fetcher, root + (parts.path or "/"), "home", notes)
    if home is None or home["status"] != 200:
        # www. and the bare domain disagree surprisingly often.
        alt = root.replace("://www.", "://") if "://www." in root else root.replace("://", "://www.")
        notes.append("retrying via %s" % alt)
        home = extract_page(fetcher, alt + "/", "home", notes)
    if home is None or home["status"] != 200:
        notes.append("homepage unreachable (%s)" % (home and (home["error"] or home["status"])))
        log("  !! %s unreachable" % domain, quiet)
        return result

    result["reachable"] = True
    result["final_url"] = home["final_url"]
    root = "{0.scheme}://{0.netloc}".format(urllib.parse.urlsplit(home["final_url"]))
    site_name = home.pop("_site_name", "")
    result["name"] = guess_name(home["title"], site_name, domain)

    # Candidates: homepage nav first (curated by the company), then sitemap.
    candidates = {}
    for url, anchor in home.pop("_links", []):
        if url and same_site(url, domain) and not excluded(url, include_case_studies):
            kind = classify(url, anchor)
            if kind and kind != "home":
                candidates.setdefault(url, kind)
    try:
        sm = sitemap_urls(fetcher, root)
    except Exception as e:                                # noqa: BLE001
        notes.append("sitemap lookup failed: %s" % e)
        sm = []
    result["sitemap_urls_seen"] = len(sm)
    for url in sm:
        url = clean_url(root, url)
        if url and same_site(url, domain) and not excluded(url, include_case_studies):
            kind = classify(url)
            if kind and kind != "home" and url not in candidates:
                candidates[url] = kind
    if not candidates:
        notes.append("no nav or sitemap candidates; trying common paths")
        for guess, kind in [("/pricing", "pricing"), ("/products", "product"),
                            ("/solutions", "solutions"), ("/platform", "platform"),
                            ("/features", "features"), ("/about", "about")]:
            candidates[root + guess] = kind

    signal_pool = [clean_url(root, u) for u in sm] + [u for u, _ in candidates.items()]
    for label, pattern in SIGNAL_PATTERNS.items():
        hits = [u for u in dict.fromkeys(signal_pool)
                if u and same_site(u, domain) and re.search(pattern, urllib.parse.urlsplit(u).path.lower() + "/")]
        if hits:
            result["signal_urls"][label] = hits[:15]

    patterns = dict(TYPE_PATTERNS)

    def score(item):
        url, kind = item
        path = urllib.parse.urlsplit(url).path.strip("/")
        depth = path.count("/")
        base = TYPE_PRIORITY.get(kind, 10)
        first = "/" + (path.split("/")[0] if path else "") + "/"
        if kind in patterns and not re.search(patterns[kind], first):
            base *= 0.55    # matched a deep slug, not a top-level section
        return base - 10 * depth - len(url) / 1000.0

    picked, counts = [], {}
    for url, kind in sorted(candidates.items(), key=score, reverse=True):
        if len(picked) >= max_pages - 1:
            break
        if counts.get(kind, 0) >= TYPE_CAP.get(kind, 1):
            continue
        counts[kind] = counts.get(kind, 0) + 1
        picked.append((url, kind))

    pages = [home]
    for url, kind in picked:
        page = extract_page(fetcher, url, kind, notes)
        if page is None:
            continue
        page.pop("_links", None)
        page.pop("_site_name", None)
        if page["status"] == 200 and (page["h1"] or page["h2"] or page["title"]):
            pages.append(page)
        elif page["status"] != 200:
            notes.append("%s -> %s" % (url, page["error"] or page["status"]))
    result["pages"] = pages

    result["headings_found"] = sum(len(p["h1"]) + len(p["h2"]) + len(p["h3"]) for p in pages)
    if result["headings_found"] == 0:
        notes.append("no headings extracted: site is JS-rendered, parked, or blocking bots -- "
                     "fall back to WebFetch for this domain, or treat copy as unavailable")
    all_headings = [h for p in pages for h in p["h1"] + p["h2"]]
    compare_urls = result["signal_urls"].get("compare", []) + [u for u, k in picked if k == "compare"]
    result["named_competitors"] = named_competitors(compare_urls, all_headings, result["name"])
    log("  ok %-28s %d pages (%s)%s" % (
        domain, len(pages), ", ".join(sorted({p["page_type"] for p in pages})),
        "  competitors named: " + ", ".join(result["named_competitors"][:5])
        if result["named_competitors"] else ""), quiet)
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("targets", nargs="+", help="domains or URLs, e.g. blixon.com")
    ap.add_argument("--out", required=True, help="directory for per-company JSON")
    ap.add_argument("--max-pages", type=int, default=8, help="pages per company incl. homepage (default 8)")
    ap.add_argument("--timeout", type=int, default=20)
    ap.add_argument("--delay", type=float, default=0.7, help="seconds between requests to one site")
    ap.add_argument("--workers", type=int, default=4, help="companies scanned in parallel")
    ap.add_argument("--user-agent", default=DEFAULT_UA,
                    help="request UA; pass %r to identify as a bot" % BOT_UA)
    ap.add_argument("--ignore-robots", action="store_true")
    ap.add_argument("--include-case-studies", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    log("scanning %d site(s) -> %s" % (len(args.targets), args.out), args.quiet)

    def work(target):
        fetcher = Fetcher(args.user_agent, args.timeout, args.delay, not args.ignore_robots)
        try:
            return scan_company(target, fetcher, args.max_pages, args.include_case_studies, args.quiet)
        except Exception as e:                            # noqa: BLE001
            log("  !! %s crashed: %s" % (target, e), args.quiet)
            return {"slug": slugify(target), "input": target, "domain": target,
                    "reachable": False, "pages": [], "notes": ["crash: %s" % e],
                    "name": "", "signal_urls": {}, "named_competitors": []}

    results = []
    with futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        for res in pool.map(work, args.targets):
            results.append(res)
            path = os.path.join(args.out, res["slug"] + ".json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(res, fh, indent=2, ensure_ascii=False)

    ok = sum(1 for r in results if r.get("reachable"))
    pages = sum(len(r.get("pages", [])) for r in results)
    print(json.dumps({"companies": len(results), "reachable": ok, "pages": pages,
                      "out": os.path.abspath(args.out),
                      "unreachable": [r["domain"] for r in results if not r.get("reachable")]}, indent=2))


if __name__ == "__main__":
    main()
