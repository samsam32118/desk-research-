#!/usr/bin/env python3
"""Read every page that ranks, and record what it actually says.

The search result gives you a position and a rewritten snippet. This gives you
the page: its real <title>, its meta description, its heading ladder, how long
it is, when it was published, what structured data it declares, and what kind
of page it is. That is the evidence layer -- "this ranks because it is a
3,000-word comparison guide updated this year, not because it is a product
page" is a claim you can only make from here.

The gap between the SERP title and the page's own <title> is worth keeping:
where Google rewrote a title, it is telling you the original did not match the
query well enough.

Every URL is fetched once no matter how many keywords it ranks for, requests to
one host are spaced out, robots.txt is honoured, and a page that blocks us is
recorded as blocked rather than quietly dropped -- a page missing from the
corpus and a page that returned nothing look identical in a chart otherwise.

Usage:
    python3 fetch_pages.py --serp serp.json --out pages.jsonl
    python3 fetch_pages.py --serp serp.json --out pages.jsonl --max-rank 10 --workers 8
    python3 fetch_pages.py --urls urls.txt --out pages.jsonl
"""

import argparse
import concurrent.futures as futures
import gzip
import json
import os
import re
import ssl
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import zlib
from collections import defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

SKIP_TEXT_TAGS = {"script", "style", "noscript", "svg", "template", "iframe", "nav", "footer"}
HEADING_TAGS = {"h1", "h2", "h3"}

DATE_META = ["article:published_time", "article:modified_time", "og:updated_time",
             "date", "pubdate", "publishdate", "publish_date", "dc.date.issued",
             "dcterms.modified", "lastmod", "last-modified", "datepublished", "datemodified"]

# What kind of page is this? Read from URL shape, structured data and title --
# three weak signals that agree often enough to be useful, and disagree loudly
# enough to be checkable.
UGC_HOSTS = ("reddit.com", "quora.com", "stackexchange.com", "stackoverflow.com",
             "trustpilot.com", "tripadvisor.com", "answers.com", "medium.com",
             "substack.com", "discourse", "forum", "community.")
VIDEO_HOSTS = ("youtube.com", "youtu.be", "vimeo.com", "tiktok.com", "dailymotion.com")
MARKETPLACE_HOSTS = ("amazon.", "ebay.", "walmart.com", "etsy.com", "alibaba.com",
                     "aliexpress.", "target.com", "bestbuy.com", "costco.com",
                     "wayfair.com", "idealo.", "temu.com")
WIKI_HOSTS = ("wikipedia.org", "wikihow.com", "fandom.com", "britannica.com")

LIST_TITLE = re.compile(r"(?:^|\b)(\d{1,3})\s*(?:\+|)\s*(?:best|top|of the|great|ways|things|"
                        r"tips|reasons|examples|ideas|tools|steps)\b", re.I)
LEADING_NUM = re.compile(r"^\s*(?:the\s+)?(\d{1,3})\b", re.I)
YEAR_RE = re.compile(r"\b(20[2-3]\d)\b")
QUESTION_START = re.compile(r"^(how|what|why|when|which|where|who|is|are|can|does|do|should)\b", re.I)


def log(msg, quiet=False):
    if not quiet:
        print(msg, file=sys.stderr, flush=True)


def norm(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def collapse_repeats(text):
    """Responsive markup often ships the same headline once per breakpoint."""
    m = re.fullmatch(r"(.{4,}?)(?:\s*\1)+", text)
    return m.group(1).strip() if m else text


def registrable(url):
    host = urllib.parse.urlsplit(url).netloc.lower().split(":")[0]
    host = host[4:] if host.startswith("www.") else host
    parts = host.split(".")
    if len(parts) <= 2:
        return host
    if parts[-2] in ("co", "com", "org", "net", "gov", "ac", "edu") and len(parts[-1]) == 2:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.meta = {}
        self.canonical = ""
        self.lang = ""
        self.headings = {"h1": [], "h2": [], "h3": []}
        self.jsonld = []
        self.times = []
        self.words = 0
        self.paragraphs = []
        self.links_internal = 0
        self.links_external = 0
        self.images = 0
        self.tables = 0
        self.lists = 0
        self._skip = 0
        self._capture = None
        self._buf = []
        self._in_title = False
        self._in_ld = False
        self._ld_buf = []
        self._in_p = False
        self._p_buf = []

    def _attr(self, attrs, key):
        for k, v in attrs:
            if k.lower() == key:
                return v or ""
        return ""

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if self._capture and tag not in SKIP_TEXT_TAGS:
            self._buf.append(" ")
        if tag in SKIP_TEXT_TAGS:
            if tag == "script" and "ld+json" in self._attr(attrs, "type").lower():
                self._in_ld = True
                self._ld_buf = []
            self._skip += 1
            return
        if tag == "html":
            self.lang = self._attr(attrs, "lang")[:12]
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            name = (self._attr(attrs, "name") or self._attr(attrs, "property")
                    or self._attr(attrs, "itemprop")).lower()
            content = norm(self._attr(attrs, "content"))
            if name and content and name not in self.meta:
                self.meta[name] = content
        elif tag == "link":
            if "canonical" in self._attr(attrs, "rel").lower():
                self.canonical = self._attr(attrs, "href")
        elif tag == "time":
            dt = self._attr(attrs, "datetime")
            if dt:
                self.times.append(dt)
        elif tag in HEADING_TAGS:
            self._capture = tag
            self._buf = []
        elif tag == "p":
            self._in_p = True
            self._p_buf = []
        elif tag == "a":
            href = self._attr(attrs, "href")
            if href.startswith("http"):
                self.links_external += 1
            elif href and not href.startswith(("#", "mailto:", "tel:", "javascript:")):
                self.links_internal += 1
        elif tag == "img":
            self.images += 1
        elif tag == "table":
            self.tables += 1
        elif tag in ("ul", "ol"):
            self.lists += 1

    def handle_endtag(self, tag):
        tag = tag.lower()
        if self._capture and tag not in SKIP_TEXT_TAGS and tag not in HEADING_TAGS:
            self._buf.append(" ")
        if tag in SKIP_TEXT_TAGS:
            if tag == "script" and self._in_ld:
                blob = "".join(self._ld_buf).strip()
                if blob:
                    self.jsonld.append(blob[:60000])
                self._in_ld = False
            self._skip = max(0, self._skip - 1)
            return
        if tag == "title":
            self._in_title = False
        elif tag in HEADING_TAGS and self._capture == tag:
            text = collapse_repeats(norm("".join(self._buf)))
            if 1 < len(text) <= 300:
                self.headings[tag].append(text)
            self._capture = None
            self._buf = []
        elif tag == "p" and self._in_p:
            text = norm("".join(self._p_buf))
            if len(text) > 60 and len(self.paragraphs) < 3:
                self.paragraphs.append(text[:600])
            self._in_p = False
            self._p_buf = []

    def handle_data(self, data):
        if self._in_ld:
            self._ld_buf.append(data)
            return
        if self._skip:
            return
        if self._in_title:
            self.title += data
        if self._capture:
            self._buf.append(data)
        if self._in_p:
            self._p_buf.append(data)
        self.words += len(data.split())


def parse_jsonld(blobs):
    """Structured data says what the publisher claims the page is."""
    types, dates = [], {}

    def walk(node):
        if isinstance(node, dict):
            t = node.get("@type")
            for item in ([t] if isinstance(t, str) else (t or [])):
                if isinstance(item, str):
                    types.append(item)
            for key, target in (("datePublished", "published"), ("dateModified", "modified")):
                val = node.get(key)
                if isinstance(val, str) and target not in dates:
                    dates[target] = val
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    for blob in blobs:
        try:
            walk(json.loads(blob))
        except Exception:                                 # noqa: BLE001
            # Malformed JSON-LD is common; the @type is still readable.
            types += re.findall(r'"@type"\s*:\s*"([A-Za-z]+)"', blob)
    return list(dict.fromkeys(types))[:12], dates


DATE_PAT = re.compile(r"(20[0-2]\d)[-/](\d{1,2})[-/](\d{1,2})")


def clean_date(value):
    m = DATE_PAT.search(str(value or ""))
    if not m:
        return ""
    y, mo, d = m.groups()
    try:
        return "%04d-%02d-%02d" % (int(y), int(mo), int(d))
    except ValueError:
        return ""


def classify_page(url, title, schema_types, h1, word_count):
    """Best guess at the format of the page, from three weak signals."""
    host = urllib.parse.urlsplit(url).netloc.lower()
    path = urllib.parse.urlsplit(url).path.lower()
    types = {t.lower() for t in schema_types}
    head = " ".join([title] + (h1 or [])).lower()

    if any(h in host for h in VIDEO_HOSTS) or "videoobject" in types:
        return "video"
    if any(h in host for h in UGC_HOSTS) or "discussionforumposting" in types \
            or "qapage" in types or re.search(r"/(forum|thread|comments|discussion)/", path):
        return "forum/ugc"
    if any(h in host for h in WIKI_HOSTS):
        return "reference"
    if any(h in host for h in MARKETPLACE_HOSTS):
        return "marketplace"
    if re.search(r"/(docs?|documentation|support|help|manual|kb)(/|$)", path):
        return "docs/support"
    if "product" in types or re.search(r"/(product|dp|p|item|sku)/", path):
        return "product"
    looks_like_list = bool(LIST_TITLE.search(title or "") or LEADING_NUM.match(title or ""))
    if not looks_like_list and (re.search(r"/(categor(y|ies)|collections?|shop|catalog|"
                                          r"browse|range)/", path) or "itemlist" in types):
        return "category"
    # Shopify parks every blog under /blogs/news/, so the path alone is not news.
    blog_path = re.search(r"/blogs?/", path)
    if "newsarticle" in types or (re.search(r"/(news|press)/", path) and not blog_path):
        return "news"
    if re.search(r"\bvs\.?\b|versus|comparison", head) or re.search(r"-vs-|/compare", path):
        return "comparison"
    if looks_like_list:
        return "listicle"
    if "howto" in types or re.match(r"^how to\b", head) or re.search(r"/how-to/", path):
        return "how-to"
    if "faqpage" in types:
        return "faq"
    if re.search(r"\breview(s|ed)?\b", head) or "review" in types:
        return "review"
    if QUESTION_START.match(title or ""):
        return "question/answer"
    if path in ("", "/"):
        return "homepage"
    if "article" in types or "blogposting" in types or word_count > 700:
        return "article/guide"
    return "other"


class Fetcher:
    def __init__(self, timeout=20, delay=1.0, respect_robots=True, ua=UA):
        self.timeout = timeout
        self.delay = delay
        self.respect_robots = respect_robots
        self.ua = ua
        self._ctx = ssl.create_default_context()
        self._robots = {}
        self._last = defaultdict(float)
        self._locks = defaultdict(threading.Lock)
        self._guard = threading.Lock()

    def _host_lock(self, host):
        with self._guard:
            return self._locks[host]

    def get(self, url):
        """Return (final_url, status, text, ctype, error). Never raises."""
        host = urllib.parse.urlsplit(url).netloc.lower()
        with self._host_lock(host):
            gap = time.time() - self._last[host]
            if gap < self.delay:
                time.sleep(self.delay - gap)
            self._last[host] = time.time()
        req = urllib.request.Request(url, headers={
            "User-Agent": self.ua,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.5",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
        })
        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=self._ctx) as resp:
                raw = resp.read(2_500_000)
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
                try:
                    text = raw.decode(charset, errors="replace")
                except LookupError:
                    text = raw.decode("utf-8", errors="replace")
                return resp.geturl(), resp.status, text, ctype, ""
        except urllib.error.HTTPError as e:
            return url, e.code, "", "", "HTTP %s" % e.code
        except Exception as e:                            # noqa: BLE001
            return url, 0, "", "", "%s: %s" % (type(e).__name__, e)

    def allowed(self, url):
        if not self.respect_robots:
            return True
        parts = urllib.parse.urlsplit(url)
        root = "%s://%s" % (parts.scheme, parts.netloc)
        with self._guard:
            known = root in self._robots
        if not known:
            rp = urllib.robotparser.RobotFileParser()
            _, status, text, _, _ = self.get(root + "/robots.txt")
            if status == 200 and text:
                try:
                    rp.parse(text.splitlines())
                except Exception:                         # noqa: BLE001
                    rp = None
            else:
                rp = None
            with self._guard:
                self._robots[root] = rp
        rp = self._robots[root]
        if rp is None:
            return True
        try:
            return rp.can_fetch(self.ua, url) or rp.can_fetch("*", url)
        except Exception:                                 # noqa: BLE001
            return True


def extract(fetcher, url):
    record = {"url": url, "final_url": "", "domain": registrable(url), "status": 0,
              "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "error": "", "blocked": False, "title": "", "meta_description": "",
              "og_title": "", "og_description": "", "canonical": "", "lang": "",
              "h1": [], "h2": [], "h3": [], "word_count": 0, "schema_types": [],
              "published": "", "modified": "", "first_paragraph": "",
              "images": 0, "tables": 0, "lists": 0,
              "links_internal": 0, "links_external": 0}
    if not fetcher.allowed(url):
        record["error"] = "robots.txt disallows"
        record["blocked"] = True
        return record
    final_url, status, text, ctype, err = fetcher.get(url)
    record.update(final_url=final_url, status=status, error=err)
    if status != 200 or not text:
        # 403/429 is a wall, not an empty page. Saying which matters: a page
        # kept off the charts for blocking is a coverage gap, and a gap that
        # looks like an absence invites a wrong conclusion.
        record["blocked"] = status in (401, 403, 429, 451) or status == 0
        return record
    if "html" not in ctype and "<html" not in text[:2000].lower():
        record["error"] = "not html (%s)" % (ctype.split(";")[0] or "unknown")
        return record

    p = PageParser()
    try:
        p.feed(text)
    except Exception as e:                                # noqa: BLE001
        record["error"] = "parse: %s" % type(e).__name__
    schema_types, ld_dates = parse_jsonld(p.jsonld)
    record.update(
        title=norm(p.title)[:300],
        meta_description=p.meta.get("description", "")[:600],
        og_title=p.meta.get("og:title", "")[:300],
        og_description=p.meta.get("og:description", "")[:600],
        canonical=p.canonical[:400], lang=p.lang,
        h1=p.headings["h1"][:4], h2=p.headings["h2"][:30], h3=p.headings["h3"][:30],
        word_count=p.words, schema_types=schema_types,
        first_paragraph=(p.paragraphs[0] if p.paragraphs else "")[:600],
        images=p.images, tables=p.tables, lists=p.lists,
        links_internal=p.links_internal, links_external=p.links_external,
    )
    published = ld_dates.get("published", "")
    modified = ld_dates.get("modified", "")
    for key in DATE_META:
        value = p.meta.get(key, "")
        if value and "modif" in key and not modified:
            modified = value
        elif value and not published and "modif" not in key:
            published = value
    if not published and p.times:
        published = p.times[0]
    record["published"] = clean_date(published)
    record["modified"] = clean_date(modified)

    title = record["title"] or record["og_title"]
    record["title_len"] = len(title)
    record["desc_len"] = len(record["meta_description"] or record["og_description"])
    record["h2_count"] = len(p.headings["h2"])
    record["has_faq_schema"] = any(t.lower() == "faqpage" for t in schema_types)
    record["title_year"] = (YEAR_RE.search(title).group(1) if YEAR_RE.search(title) else "")
    record["title_number"] = bool(LIST_TITLE.search(title) or LEADING_NUM.match(title))
    record["title_question"] = bool(QUESTION_START.match(title))
    record["page_kind"] = classify_page(record["final_url"] or url, title, schema_types,
                                        record["h1"], record["word_count"])
    # A shell with a <title> and nothing else is a JS-rendered page, not a thin
    # one. Recording which it is stops "this page ranks on 40 words" nonsense.
    if record["word_count"] < 120 and not record["h2"]:
        record["error"] = record["error"] or "thin or JS-rendered: little server-side text"
    return record


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--serp", help="serp.json from record_serp.py")
    ap.add_argument("--urls", help="file of URLs, one per line (instead of --serp)")
    ap.add_argument("--out", default="pages.jsonl")
    ap.add_argument("--max-rank", type=int, default=10,
                    help="only fetch results ranked this high or better (default 10)")
    ap.add_argument("--limit", type=int, default=1200, help="cap on unique URLs fetched")
    ap.add_argument("--workers", type=int, default=8, help="pages in flight at once")
    ap.add_argument("--delay", type=float, default=1.0, help="seconds between hits on one host")
    ap.add_argument("--timeout", type=int, default=20)
    ap.add_argument("--ignore-robots", action="store_true")
    ap.add_argument("--refresh", action="store_true",
                    help="refetch URLs already in --out (default is to keep them)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    urls = []
    if args.serp:
        with open(args.serp, encoding="utf-8") as fh:
            serp = json.load(fh)
        for entry in serp.get("keywords", {}).values():
            for r in entry.get("results", []):
                if r.get("rank", 99) <= args.max_rank:
                    urls.append(r["url"])
    if args.urls:
        with open(args.urls, encoding="utf-8") as fh:
            urls += [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]
    if not urls:
        raise SystemExit("nothing to fetch: pass --serp or --urls")

    done = {}
    if os.path.exists(args.out) and not args.refresh:
        with open(args.out, encoding="utf-8") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                    done[rec["url"]] = rec
                except Exception:                         # noqa: BLE001
                    continue

    # One fetch per URL however many keywords it ranks for -- in a 100-keyword
    # run the same guide often ranks for thirty of them.
    unique, seen = [], set()
    for u in urls:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    todo = [u for u in unique if u not in done][: args.limit]
    log("%d unique URLs across the corpus; %d already fetched; fetching %d"
        % (len(unique), len(unique) - len(todo), len(todo)), args.quiet)

    fetcher = Fetcher(args.timeout, args.delay, not args.ignore_robots)
    results, counter = [], [0]
    lock = threading.Lock()

    def work(url):
        try:
            rec = extract(fetcher, url)
        except Exception as e:                            # noqa: BLE001
            rec = {"url": url, "domain": registrable(url), "status": 0, "blocked": True,
                   "error": "crash: %s" % type(e).__name__, "title": "", "h1": [], "h2": [],
                   "word_count": 0, "page_kind": "other", "schema_types": []}
        with lock:
            counter[0] += 1
            if counter[0] % 25 == 0:
                log("  %d/%d" % (counter[0], len(todo)), args.quiet)
        return rec

    if todo:
        with futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            results = list(pool.map(work, todo))

    merged = list(done.values()) + results
    with open(args.out, "w", encoding="utf-8") as fh:
        for rec in merged:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    ok = [r for r in merged if r.get("status") == 200 and not r.get("blocked")]
    blocked = [r for r in merged if r.get("blocked") or r.get("status") not in (200,)]
    # A wall is not an absence. Listing the URLs makes the gap actionable --
    # WebFetch reaches some of these, and the ones nothing reaches belong in
    # the write-up rather than being silently missing from every chart.
    blocked_path = os.path.splitext(args.out)[0] + "_blocked.txt"
    if blocked:
        with open(blocked_path, "w", encoding="utf-8") as fh:
            for r in sorted(blocked, key=lambda r: r.get("domain", "")):
                fh.write("%s\t%s\t%s\n" % (r.get("domain", ""), r.get("status", 0),
                                             r.get("url", "")))
    kinds = defaultdict(int)
    for r in ok:
        kinds[r.get("page_kind", "other")] += 1
    words = sorted(r.get("word_count", 0) for r in ok)
    print(json.dumps({
        "out": os.path.abspath(args.out), "urls_seen": len(unique), "fetched_now": len(todo),
        "in_corpus": len(merged), "readable": len(ok), "blocked_or_failed": len(blocked),
        "coverage_pct": round(100.0 * len(ok) / max(1, len(merged))),
        "median_word_count": words[len(words) // 2] if words else 0,
        "page_kinds": dict(sorted(kinds.items(), key=lambda kv: -kv[1])),
        "blocked_domains": sorted({r["domain"] for r in blocked})[:20],
        "blocked_list": os.path.abspath(blocked_path) if blocked else "",
    }, indent=2))


if __name__ == "__main__":
    main()
