#!/usr/bin/env python3
"""Turn search results you have just read into a SERP dataset.

Only your web search tool can tell you what ranks, so the ranking half of this
pipeline passes through you. This script makes that as cheap as possible: dump
the results under a keyword heading in whatever shape they arrived, and it
normalises, dedupes, positions and merges them.

It reads the shapes you will actually have to hand:

    ## best espresso machine
    [{"title":"The best espresso machines","url":"https://cnn.com/..."}]

    ## espresso machine for home
    1. https://example.com/guide | The Best Home Espresso Machines
    2. https://other.com/review
    - https://third.com/

    {"keyword": "espresso machine vs nespresso", "results": [{"url": "..."}]}

Rank comes from order, so paste results in the order they were returned. Titles
are optional -- fetch_pages.py reads the real <title> off every page anyway,
and where the two differ, that gap is itself a finding.

Merging is by keyword: re-recording a keyword replaces its results, so a
re-run after a better search is safe. `--targets` reports which keywords you
have not captured yet, which is how you keep track across a long capture.

Usage:
    python3 record_serp.py --ledger batch1.md --out serp.json
    python3 record_serp.py --ledger batch2.md --out serp.json --targets serp_targets.txt
    cat batch3.md | python3 record_serp.py --ledger - --out serp.json
"""

import argparse
import json
import os
import re
import sys
import urllib.parse
from datetime import datetime, timezone

# Tracking junk that makes two records of the same page look like two pages.
TRACKING = re.compile(r"^(utm_|gclid|fbclid|mc_|ref|ref_src|source|si|igshid|"
                      r"_hs|hsa_|msclkid|yclid|spm|scid)", re.I)

HEADER = re.compile(r"""^\s*(?:\#{1,6}\s*|[-*]\s+)?
                        (?:keyword|query|q)\s*[:=]\s*(?P<a>.+?)\s*$
                      | ^\s*\#{1,6}\s*(?P<b>.+?)\s*$
                      | ^\s*(?P<c>.+?)\s*:\s*$""", re.X | re.I)

# Parens are legal in URLs (Wikipedia disambiguation pages live on them), so
# they are allowed through here and an unbalanced trailing one is trimmed in
# clean_url, where the count is known.
URL_RE = re.compile(r"https?://[^\s<>\"'|\]]+")

# Search engines wrap the destination; the wrapper is not the ranking page.
REDIRECTORS = {
    "duckduckgo.com": "uddg", "www.google.com": "url", "google.com": "url",
    "www.bing.com": "u", "r.jina.ai": "", "vertexaisearch.cloud.google.com": "",
}


def clean_url(raw):
    """Normalise a result URL so the same page counts once."""
    raw = (raw or "").strip().strip(".,;]}’\"'")
    # Only shed a trailing ")" that has no opener -- en.wikipedia.org/wiki/Espresso_(disambiguation)
    # is a real URL, and trimming its bracket turns a live page into a 404.
    while raw.endswith(")") and raw.count("(") < raw.count(")"):
        raw = raw[:-1]
    raw = raw.rstrip(".,;")
    if not raw:
        return ""
    raw = raw.replace("\\/", "/")
    if not raw.startswith("http"):
        raw = "https://" + raw.lstrip("/")
    try:
        parts = urllib.parse.urlsplit(raw)
    except ValueError:
        return ""
    if parts.scheme not in ("http", "https") or not parts.netloc:
        return ""
    host = parts.netloc.lower().split(":")[0]
    # Unwrap a redirector before anything else, or every result is one domain.
    if host in REDIRECTORS:
        key = REDIRECTORS[host]
        qs = urllib.parse.parse_qs(parts.query)
        target = (qs.get(key, [""])[0] if key else "")
        if target:
            return clean_url(urllib.parse.unquote(target))
    query = urllib.parse.parse_qsl(parts.query, keep_blank_values=False)
    kept = [(k, v) for k, v in query if not TRACKING.match(k)]
    path = re.sub(r"//+", "/", parts.path) or "/"
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    return urllib.parse.urlunsplit((parts.scheme.lower(), host, path,
                                    urllib.parse.urlencode(kept), ""))


def registrable(url):
    """Good-enough eTLD+1: enough to group results by publisher."""
    host = urllib.parse.urlsplit(url).netloc.lower().split(":")[0]
    host = host[4:] if host.startswith("www.") else host
    parts = host.split(".")
    if len(parts) <= 2:
        return host
    # co.uk, com.au, org.uk ... keep three labels for those.
    if parts[-2] in ("co", "com", "org", "net", "gov", "ac", "edu") and len(parts[-1]) == 2:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def parse_ledger(text):
    """Read the ledger. Forgiving on purpose: the cost of a strict format is
    paid on every batch, and a dropped result is worse than a loose regex."""
    blocks, current, notes = [], None, []

    def flush():
        if current and current["results"]:
            blocks.append(current)

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        # A whole record on one line.
        if stripped.startswith("{"):
            try:
                obj = json.loads(stripped)
            except Exception:                             # noqa: BLE001
                obj = None
            if isinstance(obj, dict) and obj.get("keyword"):
                flush()
                current = {"keyword": str(obj["keyword"]).strip().lower(), "results": []}
                for item in obj.get("results", []) or obj.get("links", []):
                    if isinstance(item, dict):
                        add_result(current, item.get("url"), item.get("title"),
                                   item.get("snippet") or item.get("description"))
                    elif isinstance(item, str):
                        add_result(current, item, "", "")
                flush()
                current = None
                continue

        # A pasted Links: [...] array from a web search result.
        if "[" in stripped and '"url"' in stripped:
            payload = stripped[stripped.index("["):]
            try:
                items = json.loads(payload)
            except Exception:                             # noqa: BLE001
                items = None
            if isinstance(items, list):
                if current is None:
                    notes.append("results with no keyword heading were skipped")
                    continue
                for item in items:
                    if isinstance(item, dict):
                        add_result(current, item.get("url"), item.get("title"),
                                   item.get("snippet") or item.get("description"))
                continue

        urls = URL_RE.findall(stripped)
        if urls:
            if current is None:
                notes.append("results with no keyword heading were skipped")
                continue
            title = ""
            rest = URL_RE.sub("", stripped)
            for sep in ("|", "—", " - ", "\t"):
                if sep in rest:
                    title = rest.split(sep, 1)[1].strip(" -|—\t")
                    break
            for url in urls:
                add_result(current, url, title, "")
                title = ""                                # a title belongs to one URL
            continue

        m = HEADER.match(stripped)
        if m:
            name = (m.group("a") or m.group("b") or m.group("c") or "").strip()
            name = re.sub(r"^(keyword|query|q)\s*[:=]\s*", "", name, flags=re.I).strip(" \"'*#")
            if name and len(name) < 160:
                flush()
                current = {"keyword": name.lower(), "results": []}
    flush()
    return blocks, notes


def add_result(block, url, title, snippet):
    url = clean_url(url)
    if not url:
        return
    if any(r["url"] == url for r in block["results"]):
        return                                            # same page twice is one position
    block["results"].append({
        "rank": len(block["results"]) + 1, "url": url,
        "serp_title": re.sub(r"\s+", " ", str(title or "")).strip()[:300],
        "snippet": re.sub(r"\s+", " ", str(snippet or "")).strip()[:500],
        "domain": registrable(url),
    })


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", required=True, help="file of pasted results, or - for stdin")
    ap.add_argument("--out", default="serp.json", help="dataset to create or merge into")
    ap.add_argument("--engine", default="google/websearch", help="what produced these results")
    ap.add_argument("--locale", default="en-US")
    ap.add_argument("--targets", help="serp_targets.txt: reports which keywords are still missing")
    ap.add_argument("--max-rank", type=int, default=10, help="results kept per keyword (default 10)")
    args = ap.parse_args()

    text = sys.stdin.read() if args.ledger == "-" else open(args.ledger, encoding="utf-8").read()
    blocks, notes = parse_ledger(text)

    data = {"engine": args.engine, "locale": args.locale, "keywords": {}}
    if os.path.exists(args.out):
        try:
            with open(args.out, encoding="utf-8") as fh:
                prior = json.load(fh)
            if isinstance(prior.get("keywords"), dict):
                data = prior
        except Exception as e:                            # noqa: BLE001
            notes.append("could not read existing %s (%s); starting fresh" % (args.out, e))

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    added, replaced = 0, 0
    for block in blocks:
        kw = block["keyword"]
        if kw in data["keywords"]:
            replaced += 1
        else:
            added += 1
        results = block["results"][: args.max_rank]
        for i, r in enumerate(results, start=1):
            r["rank"] = i
        data["keywords"][kw] = {"keyword": kw, "captured_at": now, "engine": args.engine,
                                "results": results, "result_count": len(results)}
    data["updated_at"] = now
    data["keyword_count"] = len(data["keywords"])

    all_results = [r for k in data["keywords"].values() for r in k["results"]]
    urls = {r["url"] for r in all_results}
    domains = {r["domain"] for r in all_results}
    empty = [k for k, v in data["keywords"].items() if not v["results"]]

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)

    summary = {"out": os.path.abspath(args.out), "keywords_in_batch": len(blocks),
               "keywords_new": added, "keywords_replaced": replaced,
               "keywords_total": len(data["keywords"]), "results_total": len(all_results),
               "unique_urls": len(urls), "unique_domains": len(domains),
               "keywords_with_no_results": empty[:10]}
    if args.targets and os.path.exists(args.targets):
        with open(args.targets, encoding="utf-8") as fh:
            wanted = [ln.strip().lower() for ln in fh if ln.strip()]
        missing = [k for k in wanted if k not in data["keywords"]]
        summary["targets_total"] = len(wanted)
        summary["targets_captured"] = len(wanted) - len(missing)
        summary["targets_missing"] = len(missing)
        summary["next_up"] = missing[:12]
        if missing:
            with open(os.path.splitext(args.targets)[0] + "_remaining.txt", "w",
                      encoding="utf-8") as fh:
                fh.write("\n".join(missing) + "\n")
            summary["remaining_file"] = os.path.abspath(
                os.path.splitext(args.targets)[0] + "_remaining.txt")
    if notes:
        summary["notes"] = sorted(set(notes))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
