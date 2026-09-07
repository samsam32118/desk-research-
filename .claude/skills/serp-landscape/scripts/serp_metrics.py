#!/usr/bin/env python3
"""Work out what is ranking, and what the winners have in common.

This is where the corpus turns into numbers you can put on an axis. It joins
the keyword universe, the captured SERPs and the fetched pages, then computes
three things:

  per keyword   what kind of SERP Google returns -- intent read off the page
                types that actually rank, how deep the ranking content is, how
                fresh, how concentrated, how contestable
  per page      how many keywords it holds, weighted visibility, and the
                title/description/structure features that travel with winning
                pages
  per domain    share of voice across the sampled SERPs

Then it normalises the useful ones to a 0-10 scale and publishes them as a
metric catalogue. Matrices in analysis.json bind their axes to those metric
names, and check_analysis.py recomputes every bound coordinate -- which is what
keeps a 2x2 a measurement rather than a vibe.

The digest ends with the candidate axes ranked by how much they actually
separate this market, because an axis where everything scores 6-8 teaches a
reader nothing.

Usage:
    python3 serp_metrics.py --serp serp.json --pages pages.jsonl \\
        --keywords keywords.json --out metrics.json --digest digest.md
"""

import argparse
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timezone

# A weighting curve, not a traffic estimate. Position 1 counting ~14x position
# 10 is the point: a page that owns three number-ones matters more than one
# scraping the bottom of thirty SERPs, and a flat count hides that.
CTR = [0.27, 0.15, 0.11, 0.08, 0.07, 0.05, 0.04, 0.03, 0.03, 0.02]

# Page kinds grouped by what the searcher was evidently offered.
TRANSACTIONAL_KINDS = {"product", "category", "marketplace"}
COMMERCIAL_KINDS = {"listicle", "comparison", "review"}
INFORMATIONAL_KINDS = {"article/guide", "how-to", "question/answer", "reference",
                       "faq", "docs/support", "news"}
UGC_KINDS = {"forum/ugc"}

STOP = set("a an the and or of for to in on at by with without is are be as from that this "
           "your you my our it its how what why when which where who do does can should will "
           "not no vs versus best top get make use using more most new".split())

BRAND_TAIL = re.compile(r"\s[|–—·\-:]\s[^|–—·:]{2,40}$")


def norm(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def tokens(text):
    return [t for t in re.findall(r"[a-z0-9']+", str(text or "").lower()) if t not in STOP]


def median(values):
    values = sorted(v for v in values if v is not None)
    if not values:
        return 0
    mid = len(values) // 2
    return values[mid] if len(values) % 2 else (values[mid - 1] + values[mid]) / 2.0


def scale(value, lo, hi):
    """Min-max onto 0-10. A flat metric collapses to 5 rather than exploding."""
    if hi - lo < 1e-9:
        return 5.0
    return round(max(0.0, min(10.0, 10.0 * (value - lo) / (hi - lo))), 1)


def days_since(iso):
    if not iso:
        return None
    try:
        y, m, d = (int(x) for x in iso.split("-")[:3])
        return max(0, (date.today() - date(y, m, d)).days)
    except Exception:                                     # noqa: BLE001
        return None


def keyword_in_title(keyword, title):
    """Does this title actually answer the query, in the query's own words?"""
    title_low = " %s " % norm(title).lower()
    if not title_low.strip():
        return 0.0
    if (" %s " % keyword.lower()) in title_low:
        return 1.0
    kw_tokens = [t for t in tokens(keyword) if len(t) > 2]
    if not kw_tokens:
        return 0.0
    hits = sum(1 for t in kw_tokens if t in title_low)
    return round(hits / float(len(kw_tokens)), 2)


def load_pages(path):
    pages = {}
    if not path or not os.path.exists(path):
        return pages
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:                             # noqa: BLE001
                continue
            pages[rec.get("url", "")] = rec
            # A result URL that redirected is the same page under two names.
            final = rec.get("final_url")
            if final and final != rec.get("url"):
                pages.setdefault(final, rec)
    return pages


def serp_overlap_clusters(serp, top_n=10, min_shared=4):
    """Group keywords by the pages Google actually returns for them.

    Two queries that share four of ten results are, as far as the ranking
    system is concerned, one query -- and one page can serve both. This is the
    standard SERP-similarity test, and it is stronger evidence than any
    wording-based grouping because it is Google's own answer rather than ours.
    """
    sets = {kw: {r["url"] for r in entry.get("results", [])[:top_n]}
            for kw, entry in serp.items()}
    parent = {kw: kw for kw in sets}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    # Only compare keywords that share at least one URL.
    index = defaultdict(list)
    for kw, urls in sets.items():
        for url in urls:
            index[url].append(kw)
    pairs = Counter()
    for url, holders in index.items():
        if len(holders) > 60:            # a page on most SERPs joins nothing meaningfully
            continue
        for i, a in enumerate(holders):
            for b in holders[i + 1:]:
                pairs[(a, b) if a < b else (b, a)] += 1
    for (a, b), shared in pairs.items():
        if shared >= min_shared:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra
    groups = defaultdict(list)
    for kw in sets:
        groups[find(kw)].append(kw)
    return groups, pairs


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--serp", required=True)
    ap.add_argument("--pages", help="pages.jsonl from fetch_pages.py")
    ap.add_argument("--keywords", help="keywords.json from expand_keywords.py")
    ap.add_argument("--out", default="metrics.json")
    ap.add_argument("--digest", default="digest.md")
    ap.add_argument("--top-n", type=int, default=10, help="SERP depth to analyse (default 10)")
    ap.add_argument("--min-shared", type=int, default=4,
                    help="shared top-10 URLs needed to merge two keywords (default 4 = 40%%)")
    args = ap.parse_args()

    with open(args.serp, encoding="utf-8") as fh:
        serp_data = json.load(fh)
    serp = serp_data.get("keywords", {})
    if not serp:
        raise SystemExit("no keywords in %s -- record some SERPs first" % args.serp)
    pages = load_pages(args.pages)

    universe, clusters_by_kw, cluster_size = {}, {}, {}
    kw_data = {}
    if args.keywords and os.path.exists(args.keywords):
        with open(args.keywords, encoding="utf-8") as fh:
            kw_data = json.load(fh)
        universe = {k["keyword"]: k for k in kw_data.get("keywords", [])}
        for c in kw_data.get("clusters", []):
            cluster_size[c["id"]] = c["size"]
        for kw, entry in universe.items():
            clusters_by_kw[kw] = entry.get("cluster", "")

    # ---------------------------------------------------------------- pages
    appearances = defaultdict(list)          # url -> [(keyword, rank)]
    for kw, entry in serp.items():
        for r in entry.get("results", [])[: args.top_n]:
            appearances[r["url"]].append((kw, r["rank"], r.get("serp_title", "")))

    total_visibility = 0.0
    page_rows = {}
    for url, hits in appearances.items():
        rec = pages.get(url, {})
        vis = sum(CTR[min(rank, len(CTR)) - 1] for _, rank, _ in hits)
        total_visibility += vis
        title = rec.get("title") or rec.get("og_title") or ""
        matches = [keyword_in_title(kw, title) for kw, _, _ in hits] if title else []
        serp_titles = [t for _, _, t in hits if t]
        rewritten = bool(title and serp_titles
                         and not any(norm(t).lower() == norm(title).lower() for t in serp_titles))
        page_rows[url] = {
            "url": url, "domain": rec.get("domain") or url.split("/")[2].replace("www.", ""),
            "keywords_ranked": len(hits), "best_position": min(r for _, r, _ in hits),
            "avg_position": round(sum(r for _, r, _ in hits) / float(len(hits)), 2),
            "visibility": round(vis, 4),
            "ranks_for": sorted({kw for kw, _, _ in hits})[:40],
            "readable": rec.get("status") == 200 and not rec.get("blocked"),
            "status": rec.get("status", 0), "blocked": bool(rec.get("blocked")),
            "title": title, "serp_title": serp_titles[0] if serp_titles else "",
            "title_rewritten_by_google": rewritten,
            "meta_description": rec.get("meta_description") or rec.get("og_description", ""),
            "h1": (rec.get("h1") or [""])[0], "h2_count": len(rec.get("h2") or []),
            "word_count": rec.get("word_count", 0), "page_kind": rec.get("page_kind", "unknown"),
            "published": rec.get("published", ""), "modified": rec.get("modified", ""),
            "age_days": days_since(rec.get("modified") or rec.get("published")),
            "schema_types": rec.get("schema_types", []),
            "has_faq_schema": rec.get("has_faq_schema", False),
            "title_len": rec.get("title_len", len(title)),
            "desc_len": rec.get("desc_len", 0),
            "title_number": rec.get("title_number", False),
            "title_year": rec.get("title_year", ""),
            "title_question": rec.get("title_question", False),
            "title_brandtail": bool(BRAND_TAIL.search(title)),
            "tables": rec.get("tables", 0), "lists": rec.get("lists", 0),
            "images": rec.get("images", 0),
            "kw_in_title": round(sum(matches) / len(matches), 2) if matches else 0.0,
        }
    for row in page_rows.values():
        row["visibility_share"] = round(100.0 * row["visibility"] / max(1e-9, total_visibility), 2)

    # -------------------------------------------------------------- domains
    domain_rows = {}
    for row in page_rows.values():
        d = domain_rows.setdefault(row["domain"], {
            "domain": row["domain"], "urls": 0, "keywords": set(), "visibility": 0.0,
            "positions": [], "kinds": Counter(), "readable_pages": 0})
        d["urls"] += 1
        d["keywords"].update(row["ranks_for"])
        d["visibility"] += row["visibility"]
        d["positions"].append(row["avg_position"])
        d["kinds"][row["page_kind"]] += 1
        d["readable_pages"] += 1 if row["readable"] else 0
    domains = []
    for d in domain_rows.values():
        domains.append({
            "domain": d["domain"], "urls": d["urls"], "keywords_ranked": len(d["keywords"]),
            "visibility": round(d["visibility"], 4),
            "visibility_share": round(100.0 * d["visibility"] / max(1e-9, total_visibility), 2),
            "avg_position": round(sum(d["positions"]) / len(d["positions"]), 2),
            "top_kind": d["kinds"].most_common(1)[0][0] if d["kinds"] else "unknown",
            "readable_pages": d["readable_pages"],
        })
    domains.sort(key=lambda d: -d["visibility"])
    # Corpus-internal authority: a domain that turns up across many of the
    # sampled SERPs is one Google trusts for this topic. It is a proxy built
    # from this corpus, not a third-party authority score, and saying so keeps
    # anyone from reading it as Domain Rating.
    incumbent = {d["domain"] for d in domains if d["keywords_ranked"] >= max(3, 0.05 * len(serp))}

    # ------------------------------------------------------------- keywords
    keyword_rows = {}
    for kw, entry in serp.items():
        results = entry.get("results", [])[: args.top_n]
        rows = [page_rows[r["url"]] for r in results if r["url"] in page_rows]
        readable = [r for r in rows if r["readable"]]
        n = max(1, len(rows))
        kinds = Counter(r["page_kind"] for r in readable)
        kn = max(1, len(readable))
        shares = {
            "transactional": sum(kinds[k] for k in TRANSACTIONAL_KINDS) / float(kn),
            "commercial": sum(kinds[k] for k in COMMERCIAL_KINDS) / float(kn),
            "informational": sum(kinds[k] for k in INFORMATIONAL_KINDS) / float(kn),
            "ugc": sum(kinds[k] for k in UGC_KINDS) / float(kn),
            "video": kinds["video"] / float(kn),
        }
        if readable:
            intent = max(("transactional", shares["transactional"]),
                         ("commercial", shares["commercial"]),
                         ("informational", shares["informational"] + shares["ugc"]),
                         key=lambda p: p[1])
            serp_intent = intent[0] if intent[1] >= 0.4 else "mixed"
        else:
            serp_intent = "unknown"
        ages = [r["age_days"] for r in readable if r["age_days"] is not None]
        cid = clusters_by_kw.get(kw, "")
        entry_meta = universe.get(kw, {})
        keyword_rows[kw] = {
            "keyword": kw, "results": len(rows),
            "readable_results": len(readable),
            "coverage_pct": round(100.0 * len(readable) / n),
            "cluster": cid, "cluster_size": cluster_size.get(cid, 1),
            "intent_prior": entry_meta.get("intent_prior", ""),
            "serp_intent": serp_intent,
            "intent_agrees": bool(entry_meta.get("intent_prior") == serp_intent),
            "words": entry_meta.get("words", len(kw.split())),
            "level": entry_meta.get("level", ""),
            "relevance": entry_meta.get("relevance"),
            "share_transactional": round(shares["transactional"], 2),
            "share_commercial": round(shares["commercial"], 2),
            "share_informational": round(shares["informational"], 2),
            "share_ugc": round(shares["ugc"], 2),
            "share_video": round(shares["video"], 2),
            "share_listicle": round(kinds["listicle"] / float(kn), 2),
            "distinct_domains": len({r["domain"] for r in rows}),
            "domain_diversity": round(len({r["domain"] for r in rows}) / float(n), 2),
            "incumbent_share": round(sum(1 for r in rows if r["domain"] in incumbent) / float(n), 2),
            "median_word_count": int(median([r["word_count"] for r in readable])),
            "median_title_len": int(median([r["title_len"] for r in readable])),
            "median_desc_len": int(median([r["desc_len"] for r in readable])),
            "median_age_days": int(median(ages)) if ages else None,
            "share_title_year": round(sum(1 for r in readable if r["title_year"]) / float(kn), 2),
            "share_title_number": round(sum(1 for r in readable if r["title_number"]) / float(kn), 2),
            "share_title_question": round(
                sum(1 for r in readable if r["title_question"]) / float(kn), 2),
            "share_title_rewritten": round(
                sum(1 for r in readable if r["title_rewritten_by_google"]) / float(kn), 2),
            "kw_in_title": round(median([keyword_in_title(kw, r["title"]) for r in readable]), 2)
            if readable else 0.0,
            "top_domains": [r["domain"] for r in sorted(rows, key=lambda r: r["avg_position"])][:5],
            "page_kinds": dict(kinds.most_common()),
        }

    # How much of a keyword's SERP is shared with the rest of the corpus. A
    # keyword whose ranking domains appear nowhere else is competing in a set
    # of its own -- which usually means a different geography ("espresso
    # machine india" -> indiamart, kaapimachines) or a genuinely different
    # subject wearing the same word. Those two readings need opposite
    # responses, and nothing here can tell them apart, so this reports the
    # isolation and leaves the call to a person looking at the names.
    domain_users = defaultdict(set)
    for kw, entry in serp.items():
        for r in entry.get("results", [])[: args.top_n]:
            domain_users[r.get("domain", "")].add(kw)
    for kw, row in keyword_rows.items():
        doms = {r.get("domain", "") for r in serp[kw].get("results", [])[: args.top_n]}
        shared = [d for d in doms if len(domain_users[d]) > 1]
        row["corpus_domain_overlap"] = round(len(shared) / float(max(1, len(doms))), 2)
        row["serp_isolated"] = bool(len(serp) >= 10 and doms and not shared)

    # ------------------------------------------------- SERP-overlap clusters
    groups, pair_overlap = serp_overlap_clusters(serp, args.top_n, args.min_shared)
    serp_clusters = []
    for members in sorted(groups.values(), key=len, reverse=True):
        members.sort(key=lambda kw: -keyword_rows[kw]["cluster_size"])
        head = members[0]
        intents = Counter(keyword_rows[m]["serp_intent"] for m in members)
        demand = sum(keyword_rows[m]["cluster_size"] for m in members)
        cid = "s%03d" % (len(serp_clusters) + 1)
        serp_clusters.append({
            "id": cid, "head": head, "size": len(members), "members": members,
            "demand_mass": demand, "serp_intent": intents.most_common(1)[0][0],
            "shared_pages": sorted(
                set.intersection(*[{r["url"] for r in serp[m]["results"][: args.top_n]}
                                   for m in members]) if len(members) > 1 else [],
            )[:6],
        })
        for m in members:
            keyword_rows[m]["serp_cluster"] = cid
            keyword_rows[m]["serp_cluster_size"] = len(members)
            keyword_rows[m]["demand_mass"] = demand

    # ------------------------------------------------------ 0-10 axis metrics
    # Every axis a matrix can bind to lives here, with the raw value beside the
    # scaled one so a reader can audit the number rather than trust it.
    def build_axes(rows, spec):
        out = {}
        for name, (getter, note) in spec.items():
            raw = {}
            for key, row in rows.items():
                value = getter(row)
                if value is not None:
                    raw[key] = float(value)
            if not raw:
                continue
            lo, hi = min(raw.values()), max(raw.values())
            out[name] = {"note": note, "raw_min": round(lo, 3), "raw_max": round(hi, 3),
                         "values": {k: scale(v, lo, hi) for k, v in raw.items()},
                         "raw": {k: round(v, 3) for k, v in raw.items()}}
        return out

    kw_spec = {
        "commercial_serp": (lambda r: r["share_transactional"] + r["share_commercial"],
                            "how much of the top 10 is a money page or a buying guide"),
        "transactional_serp": (lambda r: r["share_transactional"],
                               "product, category and marketplace pages in the top 10"),
        "informational_serp": (lambda r: r["share_informational"] + r["share_ugc"],
                               "guides, how-tos, Q&A, reference and forum pages"),
        "ugc_share": (lambda r: r["share_ugc"], "forum and community results"),
        "video_share": (lambda r: r["share_video"], "video results"),
        "content_depth": (lambda r: math.log10(max(50, r["median_word_count"])),
                          "median word count of the ranking pages, log scaled"),
        "freshness": (lambda r: -math.log10(max(1, r["median_age_days"]))
                      if r["median_age_days"] is not None else None,
                      "how recently the ranking pages were updated"),
        "dated_titles": (lambda r: r["share_title_year"],
                         "ranking titles carrying a year"),
        "listicle_share": (lambda r: r["share_listicle"], "numbered list pages in the top 10"),
        "title_match": (lambda r: r["kw_in_title"],
                        "how literally the ranking titles repeat the query"),
        "domain_diversity": (lambda r: r["domain_diversity"],
                             "distinct domains across the top 10"),
        "incumbent_share": (lambda r: r["incumbent_share"],
                            "top 10 held by domains that rank across this corpus"),
        "demand_mass": (lambda r: math.log10(max(1, r.get("demand_mass", r["cluster_size"]))),
                        "keywords in the universe behind this query, log scaled"),
        "specificity": (lambda r: r["words"], "words in the query: head vs long tail"),
        "question_titles": (lambda r: r["share_title_question"],
                            "ranking titles phrased as a question"),
    }
    page_spec = {
        "keyword_coverage": (lambda r: r["keywords_ranked"],
                             "sampled keywords this page ranks for"),
        "visibility": (lambda r: r["visibility"], "position-weighted visibility"),
        "position_strength": (lambda r: -r["avg_position"], "average position, inverted"),
        "depth": (lambda r: math.log10(max(50, r["word_count"])) if r["readable"] else None,
                  "word count, log scaled"),
        "freshness": (lambda r: -math.log10(max(1, r["age_days"]))
                      if r["age_days"] is not None else None, "how recently updated"),
        "title_match": (lambda r: r["kw_in_title"],
                        "how literally the title repeats the queries it ranks for"),
        "structure": (lambda r: r["h2_count"] + 2 * r["tables"] + r["lists"]
                      if r["readable"] else None,
                      "headings, tables and lists: how navigable the page is"),
        "title_length": (lambda r: r["title_len"] if r["readable"] else None,
                         "characters in the title tag"),
    }
    axes = {"keyword": build_axes(keyword_rows, kw_spec),
            "page": build_axes(page_rows, page_spec)}

    # Spread tells you which axes are worth drawing. An axis where every dot
    # lands between 6 and 8 is a fact about the market, not a way to see it.
    def spread_of(block):
        out = []
        for name, data in block.items():
            vals = sorted(data["values"].values())
            if len(vals) < 3:
                continue
            q1, q3 = vals[len(vals) // 4], vals[(3 * len(vals)) // 4]
            mean = sum(vals) / len(vals)
            sd = (sum((v - mean) ** 2 for v in vals) / len(vals)) ** 0.5
            out.append({"metric": name, "range": round(vals[-1] - vals[0], 1),
                        "iqr": round(q3 - q1, 1), "stdev": round(sd, 2),
                        "note": data["note"]})
        out.sort(key=lambda a: (-a["iqr"], -a["stdev"]))
        return out

    separation = {"keyword": spread_of(axes["keyword"]), "page": spread_of(axes["page"])}

    # ------------------------------------------------------ title vocabulary
    title_terms, kw_terms = Counter(), Counter()
    for row in page_rows.values():
        if row["readable"] and row["title"]:
            title_terms.update(set(tokens(row["title"])))
    for kw in serp:
        kw_terms.update(set(tokens(kw)))
    ranked = len([r for r in page_rows.values() if r["readable"]]) or 1
    vocabulary = [{"term": t, "titles_using": c, "share_of_titles": round(c / float(ranked), 3),
                   "in_keywords": kw_terms.get(t, 0)}
                  for t, c in title_terms.most_common(120)]

    readable_pages = [r for r in page_rows.values() if r["readable"]]
    coverage = round(100.0 * len(readable_pages) / max(1, len(page_rows)))
    weak = [k for k, r in keyword_rows.items() if r["coverage_pct"] < 50]

    metrics = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "seed": serp_data.get("seed") or kw_data.get("seed", ""),
        "engine": serp_data.get("engine", ""),
        "locale": serp_data.get("locale", ""), "top_n": args.top_n,
        "summary": {
            "keywords_with_serps": len(serp),
            "universe_keywords": len(universe),
            "results": sum(len(e.get("results", [])) for e in serp.values()),
            "unique_pages": len(page_rows), "readable_pages": len(readable_pages),
            "page_coverage_pct": coverage, "unique_domains": len(domains),
            "serp_clusters": len(serp_clusters),
            "keywords_with_thin_coverage": len(weak),
            "serp_isolated_keywords": sum(1 for r in keyword_rows.values()
                                          if r.get("serp_isolated")),
            "intent_mix": dict(Counter(r["serp_intent"] for r in keyword_rows.values()).most_common()),
            "median_ranking_word_count": int(median([r["word_count"] for r in readable_pages])),
            "median_title_len": int(median([r["title_len"] for r in readable_pages])),
            "median_desc_len": int(median([r["desc_len"] for r in readable_pages])),
            "ctr_curve": CTR,
        },
        "keywords": keyword_rows, "pages": page_rows, "domains": domains,
        "serp_clusters": serp_clusters, "axes": axes, "separation": separation,
        "title_vocabulary": vocabulary,
        "incumbent_domains": sorted(incumbent),
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2, ensure_ascii=False)

    # ---------------------------------------------------------------- digest
    L = []
    s = metrics["summary"]
    L.append("# What is ranking for %s" % (metrics["seed"] or "this seed"))
    L.append("")
    L.append("%d keywords with SERPs out of a %d-keyword universe. %d unique pages, %d readable "
             "(%d%%), %d domains, %d SERP-overlap clusters."
             % (s["keywords_with_serps"], s["universe_keywords"], s["unique_pages"],
                s["readable_pages"], s["page_coverage_pct"], s["unique_domains"],
                s["serp_clusters"]))
    L.append("")
    L.append("Intent, read from the page types that actually rank: %s"
             % ", ".join("%s %d" % (k, v) for k, v in s["intent_mix"].items()))
    L.append("Median ranking page: %d words, %d-char title, %d-char description."
             % (s["median_ranking_word_count"], s["median_title_len"], s["median_desc_len"]))
    if weak:
        L.append("")
        L.append("**Thin coverage** on %d keyword(s) -- fewer than half their results could be "
                 "read, so their medians rest on very little: %s"
                 % (len(weak), ", ".join(weak[:8])))
    L.append("")

    L.append("## Who holds this topic")
    L.append("")
    L.append("| domain | keywords | pages | visibility share | avg pos | mostly |")
    L.append("|---|---|---|---|---|---|")
    for d in domains[:20]:
        L.append("| %s | %d | %d | %.1f%% | %.1f | %s |"
                 % (d["domain"], d["keywords_ranked"], d["urls"], d["visibility_share"],
                    d["avg_position"], d["top_kind"]))
    L.append("")

    L.append("## The pages doing the work")
    L.append("")
    L.append("Ranked by weighted visibility. A page holding many keywords is a hub -- that is "
             "the shape worth copying, not any single article.")
    L.append("")
    for row in sorted(page_rows.values(), key=lambda r: -r["visibility"])[:20]:
        L.append("- **%s** (%s, %s) — %d keyword(s), best #%d, %.1f%% visibility"
                 % (row["title"][:95] or row["url"][:95], row["domain"], row["page_kind"],
                    row["keywords_ranked"], row["best_position"], row["visibility_share"]))
        if row["readable"]:
            L.append("    - %d words, %d H2s%s%s%s"
                     % (row["word_count"], row["h2_count"],
                        ", updated %s" % row["modified"] if row["modified"] else "",
                        ", FAQ schema" if row["has_faq_schema"] else "",
                        ", title carries %s" % row["title_year"] if row["title_year"] else ""))
            if row["meta_description"]:
                L.append('    - meta: "%s"' % row["meta_description"][:190])
        else:
            L.append("    - not readable (%s) — kept out of the medians"
                     % (row["status"] or "blocked"))
    L.append("")

    L.append("## Keyword groups Google treats as one query")
    L.append("")
    L.append("Built from shared results: %d+ of the top %d URLs in common. Demand mass is how "
             "many keywords in the universe sit behind the group."
             % (args.min_shared, args.top_n))
    L.append("")
    L.append("| cluster | head keyword | keywords | demand mass | SERP intent |")
    L.append("|---|---|---|---|---|")
    for c in serp_clusters[:25]:
        L.append("| %s | %s | %d | %d | %s |"
                 % (c["id"], c["head"], c["size"], c["demand_mass"], c["serp_intent"]))
    L.append("")

    disagree = [r for r in keyword_rows.values()
                if r["intent_prior"] and r["serp_intent"] not in ("unknown", "")
                and not r["intent_agrees"]]
    if disagree:
        L.append("## Where the wording and the SERP disagree")
        L.append("")
        L.append("The query sounds like one thing and Google answers with another. These are the "
                 "queries most often written for the wrong format.")
        L.append("")
        for r in sorted(disagree, key=lambda r: -r["cluster_size"])[:15]:
            L.append("- **%s** — reads %s, ranks %s (%s)"
                     % (r["keyword"], r["intent_prior"], r["serp_intent"],
                        ", ".join("%s %d" % kv for kv in list(r["page_kinds"].items())[:3])))
        L.append("")

    isolated = [r for r in keyword_rows.values() if r.get("serp_isolated")]
    if isolated:
        L.append("## SERPs that share nothing with the rest of the corpus")
        L.append("")
        L.append("Not one domain in these keywords' top %d appears on any other SERP here. "
                 "Read the names before deciding what that means: a different geography or a "
                 "specialist niche is a real part of the topic that you are simply not "
                 "competing in yet, while a keyword that shares only a word with the seed is a "
                 "different subject and will invent a false empty quadrant if you map it. "
                 "Pass the strays to build_points.py as --drop once you have decided which "
                 "they are." % args.top_n)
        L.append("")
        for r in sorted(isolated, key=lambda r: -r["cluster_size"])[:15]:
            L.append("- **%s** — ranks: %s" % (r["keyword"], ", ".join(r["top_domains"][:4])))
        L.append("")

    L.append("## Candidate axes, ranked by how much they separate")
    L.append("")
    L.append("An axis whose interquartile range is near zero puts every dot in one band. Pick "
             "from the top of this list, and pair two that measure different things.")
    L.append("")
    for unit in ("keyword", "page"):
        L.append("**Per %s**" % unit)
        L.append("")
        for a in separation[unit][:10]:
            L.append("- `%s` — IQR %.1f, range %.1f — %s" % (a["metric"], a["iqr"], a["range"],
                                                             a["note"]))
        L.append("")

    L.append("## The words winning titles use")
    L.append("")
    L.append(" | ".join("%s %d" % (v["term"], v["titles_using"]) for v in vocabulary[:45]))
    L.append("")

    with open(args.digest, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))

    print(json.dumps({"metrics": os.path.abspath(args.out),
                      "digest": os.path.abspath(args.digest),
                      **s}, indent=2))


if __name__ == "__main__":
    main()
