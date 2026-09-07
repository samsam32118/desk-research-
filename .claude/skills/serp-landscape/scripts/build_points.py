#!/usr/bin/env python3
"""Fill in the coordinates for every measured matrix.

A 100-keyword run with six matrices needs about six hundred coordinates. Typing
them is slow, and a number copied by hand is a number that can drift from the
measurement it claims -- which is exactly what check_analysis.py rejects. So
write the matrices with their axes, poles and quadrant labels, leave `points`
out, and let this fill them from metrics.json.

It only touches matrices where BOTH axes name a metric. A judged axis is a
judgement, and its points stay yours to write and to quote.

Evidence is generated from the same data as the coordinate -- the raw value
behind each axis plus the shape of that SERP or page -- so a reader hovering a
dot sees the numbers that put it there. Rewrite any of it by hand afterwards;
this only ever fills what is empty.

Usage:
    python3 build_points.py --metrics metrics.json --analysis analysis.json --write
    python3 build_points.py --metrics metrics.json --analysis analysis.json --limit 60
"""

import argparse
import json
import os


def top_ids(metrics, unit, limit):
    """Which entities to plot when there are more than a chart can hold.

    Keywords are ranked by the demand behind them and pages by visibility, so
    trimming drops the trivia rather than the market.
    """
    if unit == "keyword":
        rows = metrics.get("keywords", {})
        ranked = sorted(rows, key=lambda k: -(rows[k].get("demand_mass")
                                              or rows[k].get("cluster_size") or 0))
    elif unit == "page":
        rows = metrics.get("pages", {})
        ranked = sorted(rows, key=lambda u: -rows[u].get("visibility", 0))
    else:
        rows = {d["domain"]: d for d in metrics.get("domains", [])}
        ranked = sorted(rows, key=lambda d: -rows[d].get("visibility", 0))
    return ranked[:limit] if limit else ranked, rows


def kinds_phrase(page_kinds):
    if not page_kinds:
        return ""
    return ", ".join("%d %s" % (v, k) for k, v in list(page_kinds.items())[:3])


def evidence_for(unit, row, metrics, xa, ya, xraw, yraw):
    """A sentence a reader can check, built from the same numbers as the dot."""
    def raw(name, value):
        if value is None:
            return ""
        shown = int(value) if float(value).is_integer() else round(value, 2)
        return "%s %s" % (name.replace("_", " "), shown)

    bits = []
    if unit == "keyword":
        # The kind counts cover the pages we could read, so say which number is
        # which rather than implying we classified results we never opened.
        if row.get("readable_results"):
            bits.append("%d results, %d readable: %s"
                        % (row.get("results", 0), row["readable_results"],
                           kinds_phrase(row.get("page_kinds"))))
        elif row.get("results"):
            bits.append("%d results, none readable" % row["results"])
        if row.get("median_word_count"):
            bits.append("median %s words" % format(row["median_word_count"], ","))
        if row.get("distinct_domains"):
            bits.append("%d distinct domains" % row["distinct_domains"])
        if row.get("serp_intent"):
            bits.append("SERP reads %s" % row["serp_intent"])
        if row.get("demand_mass"):
            bits.append("%d keywords behind it" % row["demand_mass"])

    elif unit == "page":
        if row.get("page_kind"):
            bits.append(row["page_kind"])
        if row.get("word_count"):
            bits.append("%s words" % format(row["word_count"], ","))
        if row.get("keywords_ranked"):
            bits.append("ranks for %d keyword(s), best #%s"
                        % (row["keywords_ranked"], row.get("best_position")))
        if row.get("modified") or row.get("published"):
            bits.append("updated %s" % (row.get("modified") or row.get("published")))
        if row.get("title"):
            bits.append('title: "%s"' % row["title"][:90])
    else:
        bits.append("%d keyword(s), %.1f%% visibility, avg position %.1f"
                    % (row.get("keywords_ranked", 0), row.get("visibility_share", 0),
                       row.get("avg_position", 0)))
    for name, value in ((xa, xraw), (ya, yraw)):
        text = raw(name, value)
        if text:
            bits.append(text)
    return "; ".join(b for b in bits if b)[:400]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--metrics", required=True)
    ap.add_argument("--analysis", required=True)
    ap.add_argument("--limit", type=int, default=60,
                    help="most points per matrix (default 60); 0 for everything")
    ap.add_argument("--write", action="store_true", help="write back into analysis.json")
    ap.add_argument("--refill", action="store_true",
                    help="replace points that are already there")
    ap.add_argument("--drop", default="",
                    help="comma-separated ids to leave off every map -- use it for keywords "
                         "you have looked at and judged to be a different subject that "
                         "happens to share a word with the seed. Nothing is dropped for you: "
                         "an isolated SERP is just as often a geography you do not compete "
                         "in yet, and that is a finding rather than noise")
    args = ap.parse_args()

    with open(args.metrics, encoding="utf-8") as fh:
        metrics = json.load(fh)
    with open(args.analysis, encoding="utf-8") as fh:
        analysis = json.load(fh)

    report = []
    for m in analysis.get("matrices", []):
        mid = m.get("id", "?")
        unit = m.get("unit", "keyword")
        xa = m.get("x", {}).get("metric")
        ya = m.get("y", {}).get("metric")
        if not xa or not ya:
            report.append({"matrix": mid, "action": "skipped",
                           "why": "axis %s is judged, so its points need your quotes"
                                  % ("x" if not xa else "y")})
            continue
        if m.get("points") and not args.refill:
            report.append({"matrix": mid, "action": "left alone",
                           "why": "%d points already written (--refill to replace)"
                                  % len(m["points"])})
            continue

        catalogue = metrics.get("axes", {}).get(unit, {})
        missing = [n for n in (xa, ya) if n not in catalogue]
        if missing:
            report.append({"matrix": mid, "action": "failed",
                           "why": "no metric %r for unit %s; available: %s"
                                  % (missing[0], unit, ", ".join(sorted(catalogue)))})
            continue

        xvals, yvals = catalogue[xa]["values"], catalogue[ya]["values"]
        xraws, yraws = catalogue[xa].get("raw", {}), catalogue[ya].get("raw", {})
        wanted = m.get("only")                            # optional explicit id list
        ids, rows = top_ids(metrics, unit, 0 if wanted else args.limit)
        if wanted:
            ids = [i for i in wanted if i in rows]

        drop = {d.strip() for d in args.drop.split(",") if d.strip()}
        points, dropped, strays = [], 0, 0
        for pid in ids:
            if pid not in xvals or pid not in yvals:
                dropped += 1
                continue
            row = rows.get(pid, {})
            if pid in drop:
                strays += 1
                continue
            points.append({
                "id": pid, "x": xvals[pid], "y": yvals[pid],
                "evidence": evidence_for(unit, row, metrics, xa, ya,
                                         xraws.get(pid), yraws.get(pid)),
            })
        m["points"] = points
        entry = {"matrix": mid, "action": "filled", "unit": unit, "points": len(points)}
        if dropped:
            entry["skipped_no_value"] = dropped
        if strays:
            entry["skipped_by_drop"] = strays
        if points:
            xs = [p["x"] for p in points]
            ys = [p["y"] for p in points]
            entry["x_spread"] = round(max(xs) - min(xs), 1)
            entry["y_spread"] = round(max(ys) - min(ys), 1)
            occ = {"tl": 0, "tr": 0, "bl": 0, "br": 0}
            for p in points:
                occ[("t" if p["y"] >= 5 else "b") + ("r" if p["x"] >= 5 else "l")] += 1
            entry["occupancy"] = occ
        report.append(entry)

    if args.write:
        with open(args.analysis, "w", encoding="utf-8") as fh:
            json.dump(analysis, fh, indent=2, ensure_ascii=False)

    print(json.dumps({"analysis": os.path.abspath(args.analysis),
                      "written": bool(args.write), "matrices": report,
                      "next": "check_analysis.py, then write the reading for each matrix "
                              "from the occupancy above"}, indent=2))


if __name__ == "__main__":
    main()
