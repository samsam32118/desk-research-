#!/usr/bin/env python3
"""Condense scanned sites into one readable brief you can hold in your head.

The raw scan JSON is faithful but bulky; reading 30 files of it burns context
you need for thinking. This prints the strongest signal per company -- meta
title, meta description, H1, the best H2s, pricing language, CTAs -- plus a
market-wide word-frequency table that shows which claims are table stakes and
which are actually differentiated.

Usage:
    python3 digest.py --data data/ --roster roster.json > digest.md
    python3 digest.py --data data/ --budget 1200      # chars per company
"""

import argparse
import glob
import json
import os
import re
from collections import Counter

STOPWORDS = set("""a an the and or but for with without to from of in on at by as is are be been
your you our we us it its their his her they them this that these those what which who how why
when where all any more most other some such no nor not only own same so than too very can will
just get got make made use used using new now one two three first best top over under between
into out up down off again further then once here there each few both about above below during
before after while because until against among through into""".split())


def load(data_dir):
    out = []
    for path in sorted(glob.glob(os.path.join(data_dir, "*.json"))):
        if os.path.basename(path) in ("roster.json", "analysis.json"):
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                out.append(json.load(fh))
        except Exception as e:                            # noqa: BLE001
            print("<!-- skipped %s: %s -->" % (path, e))
    return out


def clip(text, n):
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def company_block(site, meta, budget):
    lines = []
    label = meta.get("level")
    head = "## %s (%s)" % (site.get("name") or site["domain"], site["domain"])
    if label is not None:
        head += "  — level %s" % label
    lines.append(head)
    if meta.get("discovered_via"):
        lines.append("_found via: %s_" % clip(meta["discovered_via"], 160))
    if not site.get("reachable") or site.get("headings_found", 0) == 0:
        lines.append("**No copy extracted** — %s" % clip("; ".join(site.get("notes", [])[:2]), 300))
        return "\n".join(lines)

    pages = site.get("pages", [])
    home = next((p for p in pages if p["page_type"] == "home"), pages[0] if pages else None)
    if home:
        lines.append("- title: %s" % clip(home["title"] or home["og_title"], 140))
        lines.append("- meta desc: %s" % clip(home["meta_description"] or home["og_description"], 260))
        if home["h1"]:
            lines.append("- H1: %s" % clip(" / ".join(home["h1"][:2]), 200))
        if home["h2"]:
            lines.append("- home H2s: %s" % clip(" | ".join(home["h2"][:6]), 420))
        if home["ctas"]:
            lines.append("- CTAs: %s" % ", ".join(home["ctas"][:4]))

    for page in pages:
        if page["page_type"] in ("home",) or not (page["h1"] or page["h2"]):
            continue
        bits = clip(" | ".join(page["h1"][:1] + page["h2"][:5]), 300)
        lines.append("- %s (%s): %s" % (page["page_type"], page["final_url"].split("//")[-1], bits))

    if site.get("named_competitors"):
        lines.append("- names as rivals on its own site: %s" % ", ".join(site["named_competitors"][:10]))
    if site.get("signal_urls", {}).get("compare"):
        lines.append("- comparison pages: %d" % len(site["signal_urls"]["compare"]))

    text = "\n".join(lines)
    return text if len(text) <= budget else text[:budget].rstrip() + "…"


def vocabulary(sites, top=45):
    per_company, all_terms = {}, Counter()
    for site in sites:
        words = Counter()
        for page in site.get("pages", []):
            blob = " ".join([page["title"], page["meta_description"]]
                            + page["h1"] + page["h2"] + page["h3"])
            for w in re.findall(r"[a-zA-Z][a-zA-Z\-']{2,}", blob.lower()):
                if w not in STOPWORDS and len(w) > 2:
                    words[w] += 1
        per_company[site["domain"]] = words
        for w in words:
            all_terms[w] += 1          # document frequency, not raw count
    return all_terms.most_common(top), per_company


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True, help="directory of scan_site.py JSON files")
    ap.add_argument("--roster", help="optional roster.json: domain -> {level, discovered_via}")
    ap.add_argument("--budget", type=int, default=1400, help="max chars per company (default 1400)")
    ap.add_argument("--no-vocab", action="store_true")
    ap.add_argument("--out", help="write here instead of stdout")
    args = ap.parse_args()

    sites = load(args.data)
    roster = {}
    if args.roster and os.path.exists(args.roster):
        with open(args.roster, encoding="utf-8") as fh:
            raw = json.load(fh)
        entries = raw.get("companies", raw) if isinstance(raw, dict) else raw
        if isinstance(entries, list):
            roster = {e.get("domain", ""): e for e in entries}
        else:
            roster = entries

    sites.sort(key=lambda s: (roster.get(s["domain"], {}).get("level", 9), s["domain"]))
    parts = ["# Copy digest — %d companies" % len(sites), ""]
    empty = [s["domain"] for s in sites if s.get("headings_found", 0) == 0]
    parts.append("Scanned %d pages across %d sites. %s" % (
        sum(len(s.get("pages", [])) for s in sites), len(sites),
        ("No copy from: " + ", ".join(empty)) if empty else "All sites returned copy."))
    parts.append("")
    for site in sites:
        parts.append(company_block(site, roster.get(site["domain"], {}), args.budget))
        parts.append("")

    if not args.no_vocab:
        terms, _ = vocabulary(sites)
        n = max(1, len(sites))
        parts.append("## Shared vocabulary (how many of the %d sites use each term)" % n)
        parts.append("Terms most sites use are table stakes; terms one or two use are the "
                     "differentiation worth plotting.")
        parts.append("")
        parts.append(" | ".join("%s %d" % (w, c) for w, c in terms))
        parts.append("")

    text = "\n".join(parts)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("wrote %s (%d chars)" % (args.out, len(text)))
    else:
        print(text)


if __name__ == "__main__":
    main()
