#!/usr/bin/env python3
"""Ask the corpus one question at a time, and get the evidence back with it.

The digest tells you what each company says. This tells you who says a given
thing and who doesn't -- which is the shape an axis needs. Every hit comes back
with the heading it came from, so an axis arrives with its evidence attached
instead of being reconstructed later.

Usage:
    # who claims what, with quotes
    python3 facets.py --data data/ --terms "self-host,governance,agent,free"

    # no terms? show the words that actually separate this market
    python3 facets.py --data data/

Terms are matched case-insensitively as substrings, so "self-host" catches
"self-hosted" and "self-hosting". Comma-separated; use quotes for phrases.
"""

import argparse
import glob
import json
import os
import re
from collections import Counter

try:
    from digest import STOPWORDS
except ImportError:                                       # running from elsewhere
    STOPWORDS = set()


def load(data_dir):
    sites = []
    for path in sorted(glob.glob(os.path.join(data_dir, "*.json"))):
        if os.path.basename(path) in ("roster.json", "analysis.json"):
            continue
        with open(path, encoding="utf-8") as fh:
            sites.append(json.load(fh))
    return sites


def fields(site):
    """Every piece of copy, tagged with where it came from."""
    for page in site.get("pages", []):
        where = "%s %s" % (page.get("page_type", "?"),
                           page.get("final_url", "").split("//")[-1])
        if page.get("title"):
            yield page["title"], "title, " + where
        if page.get("meta_description"):
            yield page["meta_description"], "meta, " + where
        for tag in ("h1", "h2", "h3"):
            for text in page.get(tag, []):
                yield text, "%s, %s" % (tag.upper(), where)
        for cta in page.get("ctas", []):
            yield cta, "CTA, " + where
        for token in page.get("price_signals", []):
            yield token, "price, " + where


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True)
    ap.add_argument("--terms", default="", help="comma-separated terms or phrases")
    ap.add_argument("--quotes", type=int, default=2, help="example quotes per company (default 2)")
    ap.add_argument("--top", type=int, default=40, help="candidate terms to show when --terms is empty")
    ap.add_argument("--out")
    args = ap.parse_args()

    sites = load(args.data)
    if not sites:
        raise SystemExit("no scan files in %s" % args.data)
    names = {s["domain"]: s.get("name") or s["domain"] for s in sites}
    out = []

    if not args.terms.strip():
        # Words everyone uses are table stakes; words nobody but one company
        # uses are idiosyncratic. The middle is where axes live.
        doc_freq = Counter()
        for site in sites:
            seen = set()
            for text, _ in fields(site):
                for w in re.findall(r"[a-zA-Z][a-zA-Z\-']{3,}", text.lower()):
                    if w not in STOPWORDS:
                        seen.add(w)
            doc_freq.update(seen)
        n = len(sites)
        lo, hi = max(2, int(n * 0.15)), int(n * 0.7)
        picks = [(w, c) for w, c in doc_freq.most_common() if lo <= c <= hi][: args.top]
        out.append("# Terms that split this market (%d companies)" % n)
        out.append("")
        out.append("Used by between %d and %d of them — common enough to be a real claim, "
                   "rare enough to separate someone. Re-run with --terms to see who and why."
                   % (lo, hi))
        out.append("")
        for w, c in picks:
            out.append("- **%s** — %d of %d (%d%%)" % (w, c, n, round(100 * c / n)))
    else:
        terms = [t.strip() for t in args.terms.split(",") if t.strip()]
        for term in terms:
            low = term.lower()
            hits = []
            for site in sites:
                quotes, count = [], 0
                for text, where in fields(site):
                    if low in text.lower():
                        count += 1
                        if len(quotes) < args.quotes:
                            quotes.append((text.strip(), where))
                if count:
                    hits.append((names[site["domain"]], site["domain"], count, quotes))
            hits.sort(key=lambda h: -h[2])
            out.append('## "%s" — %d of %d companies' % (term, len(hits), len(sites)))
            out.append("")
            for name, domain, count, quotes in hits:
                out.append("- **%s** (%s) x%d" % (name, domain, count))
                for text, where in quotes:
                    out.append('    - "%s"  _(%s)_' % (text[:180], where))
            silent = [names[s["domain"]] for s in sites
                      if names[s["domain"]] not in {h[0] for h in hits}]
            if silent:
                out.append("")
                out.append("_Silent on this (%d): %s_" % (len(silent), ", ".join(silent)))
            out.append("")

    text = "\n".join(out)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("wrote %s (%d chars)" % (args.out, len(text)))
    else:
        print(text)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()
