#!/usr/bin/env python3
"""Check analysis.json against the data before you draw anything from it.

The important check here is one a competitive-landscape 2x2 cannot make. When
an axis names a metric, every coordinate on that axis is recomputable, so this
recomputes it and fails on any dot that has drifted from the measurement it
claims. That is the difference between "all data backed" as a promise and as a
property.

It also catches what JSON hides but a chart exposes: an axis where nobody
moves, two matrices asking the same question, a dot with no evidence, a
"nobody is here" reading about a quadrant holding six pages, and coordinates
resting on keywords whose SERPs barely resolved.

Usage:
    python3 check_analysis.py --analysis analysis.json --metrics metrics.json

Exit code 1 if anything is broken (ERROR), 0 otherwise. Warnings are judgement
calls -- read them, then decide.
"""

import argparse
import json
import re
import sys
from itertools import combinations

MIN_SPREAD = 4.0        # below this an axis is not separating anyone
MIN_EVIDENCE = 20       # chars; shorter than this is a label, not evidence
DUP_AXIS_RHO = 0.9      # rank correlation above which two axes are one axis
METRIC_TOLERANCE = 0.6  # how far a plotted point may sit from its computed value
THIN_COVERAGE = 50      # % of a keyword's results that must be readable


def ranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        shared = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            out[order[k]] = shared
        i = j + 1
    return out


def spearman(a, b):
    n = len(a)
    if n < 3:
        return 0.0
    ra, rb = ranks(a), ranks(b)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    da = sum((x - ma) ** 2 for x in ra) ** 0.5
    db = sum((y - mb) ** 2 for y in rb) ** 0.5
    return num / (da * db) if da and db else 0.0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--analysis", required=True)
    ap.add_argument("--metrics", help="metrics.json, to recompute metric-bound coordinates")
    ap.add_argument("--tolerance", type=float, default=METRIC_TOLERANCE)
    args = ap.parse_args()

    with open(args.analysis, encoding="utf-8") as fh:
        a = json.load(fh)
    metrics = {}
    if args.metrics:
        with open(args.metrics, encoding="utf-8") as fh:
            metrics = json.load(fh)

    errors, warnings, notes = [], [], []
    axes_catalogue = metrics.get("axes", {})
    kw_rows = metrics.get("keywords", {})
    page_rows = metrics.get("pages", {})
    domain_rows = {d["domain"]: d for d in metrics.get("domains", [])}

    matrices = a.get("matrices", [])
    if not matrices:
        errors.append("no matrices in analysis.json")
    if len(matrices) < 4:
        warnings.append("only %d matrices; 6 is the usual target" % len(matrices))

    if metrics and not a.get("seed"):
        warnings.append("analysis.json has no seed; the report header will be thin")

    axis_values, bound, judged = {}, 0, 0
    for m in matrices:
        mid = m.get("id", "?")
        unit = m.get("unit", "keyword")
        if unit not in ("keyword", "page", "domain"):
            errors.append("%s: unit %r must be keyword, page or domain" % (mid, unit))
            unit = "keyword"
        known = {"keyword": kw_rows, "page": page_rows, "domain": domain_rows}[unit]

        points = m.get("points", [])
        if not points:
            errors.append("%s: no points" % mid)
            continue
        if len(points) < 8:
            warnings.append("%s: only %d points -- a 2x2 with this few dots is an assertion "
                            "with a chart around it" % (mid, len(points)))

        ids = [p.get("id") for p in points]
        for dup in {i for i in ids if ids.count(i) > 1}:
            errors.append("%s: %r plotted twice" % (mid, dup))
        if known:
            unknown = [i for i in ids if i not in known]
            if unknown:
                errors.append("%s: %d point(s) are not in metrics.json as a %s: %s"
                              % (mid, len(unknown), unit, ", ".join(map(str, unknown[:4]))))

        # Coordinates resting on a SERP we could barely read are the quietest
        # way for a chart to be wrong, so name them.
        if unit == "keyword" and kw_rows:
            thin = [i for i in ids
                    if kw_rows.get(i, {}).get("coverage_pct", 100) < THIN_COVERAGE]
            if thin:
                warnings.append("%s: %d keyword(s) plotted on SERPs where under half the "
                                "results could be read: %s"
                                % (mid, len(thin), ", ".join(map(str, thin[:5]))))

        for axis in ("x", "y"):
            spec = m.get(axis, {})
            if not spec.get("label") or not spec.get("low") or not spec.get("high"):
                errors.append("%s: %s axis needs label, low and high" % (mid, axis))
            elif str(spec.get("low", "")).strip().lower() in ("low", "less", "small") or \
                    str(spec.get("high", "")).strip().lower() in ("high", "more", "large"):
                warnings.append("%s: %s poles are generic (%r / %r) -- name them in the "
                                "language of the SERP" % (mid, axis, spec.get("low"),
                                                          spec.get("high")))
            vals = [p.get(axis) for p in points]
            bad = [p.get("id") for p, v in zip(points, vals)
                   if not isinstance(v, (int, float)) or not 0 <= v <= 10]
            if bad:
                errors.append("%s: %s out of 0-10 range for %s"
                              % (mid, axis, ", ".join(map(str, bad[:5]))))
                continue

            metric = spec.get("metric")
            if metric:
                bound += 1
                catalogue = axes_catalogue.get(unit, {})
                if metric not in catalogue:
                    errors.append("%s: %s axis binds to metric %r, which is not in metrics.json "
                                  "for unit %s. Available: %s"
                                  % (mid, axis, metric, unit,
                                     ", ".join(sorted(catalogue)[:10]) or "none"))
                else:
                    computed = catalogue[metric]["values"]
                    drift = []
                    for p in points:
                        want = computed.get(p.get("id"))
                        if want is None:
                            drift.append("%s (no computed value)" % p.get("id"))
                        elif abs(want - p.get(axis, 0)) > args.tolerance:
                            drift.append("%s plotted %.1f, computed %.1f"
                                         % (p.get("id"), p.get(axis), want))
                    if drift:
                        errors.append("%s: %s axis claims metric %r but %d point(s) disagree "
                                      "with it -- %s. Take the computed value, or drop the "
                                      "binding and defend the axis as judged"
                                      % (mid, axis, metric, len(drift), "; ".join(drift[:4])))
            else:
                judged += 1
                notes.append("%s: %s axis (%s) is judged, not measured -- every point needs a "
                             "quote" % (mid, axis, spec.get("label", "")))

            spread = max(vals) - min(vals)
            if spread < MIN_SPREAD:
                warnings.append("%s: %s axis spread is only %.1f -- this axis is not separating "
                                "anything. Check the candidate-axis table in the digest and "
                                "take one with a wider IQR" % (mid, axis, spread))
            axis_values["%s.%s" % (mid, axis)] = {p.get("id"): v for p, v in zip(points, vals)}

        stacked = {}
        for p in points:
            stacked.setdefault((round(p.get("x", 5)), round(p.get("y", 5))), []).append(p.get("id"))
        for (px, py), who in stacked.items():
            if len(who) >= max(4, len(points) // 4):
                warnings.append("%s: %d points sit on (%s, %s) -- %s. Either the axes do not "
                                "resolve them or the scores are hedged"
                                % (mid, len(who), px, py, ", ".join(map(str, who[:5]))))

        occ = {"tl": 0, "tr": 0, "bl": 0, "br": 0}
        for p in points:
            occ[("t" if (p.get("y") or 0) >= 5 else "b")
                + ("r" if (p.get("x") or 0) >= 5 else "l")] += 1
        notes.append("%s occupancy — tl:%d tr:%d bl:%d br:%d%s"
                     % (mid, occ["tl"], occ["tr"], occ["bl"], occ["br"],
                        "  (empty: %s)" % ", ".join(k for k, v in occ.items() if v == 0)
                        if any(v == 0 for v in occ.values()) else ""))

        # An empty quadrant is the most valuable claim a 2x2 makes and the
        # easiest to get wrong. The reading is prose; the occupancy is not.
        named = {"tl": r"top[- ]left|upper[- ]left", "tr": r"top[- ]right|upper[- ]right",
                 "bl": r"bottom[- ]left|lower[- ]left", "br": r"bottom[- ]right|lower[- ]right"}
        empty_word = (r"\b(empty|unoccupied|nobody|no one|nothing|no page|no keyword|vacant|"
                      r"white ?space|untouched|untaken|gap)\b")
        reading = "%s %s" % (m.get("reading", ""), m.get("why_it_matters", ""))
        for sentence in re.split(r"[.;]\s+", reading):
            if not re.search(empty_word, sentence, re.I):
                continue
            for key, pattern in named.items():
                if re.search(pattern, sentence, re.I) and occ[key] > 0:
                    warnings.append("%s: a sentence calls the %s quadrant empty while %d "
                                    "point(s) sit there. Scope the claim or fix it"
                                    % (mid, key, occ[key]))

        thin = [p.get("id") for p in points if len(str(p.get("evidence", ""))) < MIN_EVIDENCE]
        if thin:
            warnings.append("%s: no real evidence for %d point(s) -- %s. A coordinate without a "
                            "quote or a number is a guess"
                            % (mid, len(thin), ", ".join(map(str, thin[:5]))))

    for (ka, va), (kb, vb) in combinations(axis_values.items(), 2):
        shared = sorted(set(va) & set(vb))
        if len(shared) < 5:
            continue
        rho = spearman([va[c] for c in shared], [vb[c] for c in shared])
        if abs(rho) >= DUP_AXIS_RHO:
            same = ka.split(".")[0] == kb.split(".")[0]
            warnings.append("%s and %s rank the same way (rho %.2f) -- %s"
                            % (ka, kb, rho,
                               "this chart is a diagonal; keep it only if the outliers are the "
                               "point, and name them in the reading" if same else
                               "one axis drawn twice across two matrices; keep the "
                               "better-evidenced one"))

    if metrics:
        units_used = {m.get("unit", "keyword") for m in matrices}
        if "keyword" not in units_used:
            warnings.append("no keyword-unit matrix -- the question was which queries to go "
                            "after, and a map of pages alone does not answer it")
        if "page" not in units_used and len(matrices) >= 4:
            notes.append("no page-unit matrix; 'why does this rank' is easier to see on one")
        plotted = {p.get("id") for m in matrices if m.get("unit", "keyword") == "keyword"
                   for p in m.get("points", [])}
        missing = [k for k in kw_rows if k not in plotted]
        if missing:
            notes.append("%d keyword(s) with SERPs appear on no matrix: %s"
                         % (len(missing), ", ".join(missing[:6])))
        cov = metrics.get("summary", {}).get("page_coverage_pct", 100)
        if cov < 70:
            warnings.append("only %d%% of ranking pages could be read -- say so in the write-up, "
                            "because a thin quadrant and an unreadable one look identical" % cov)

    for label, items in (("ERROR", errors), ("WARN", warnings), ("NOTE", notes)):
        for item in items:
            print("%-5s %s" % (label, item))
    print("\n%d matrices, %d measured axes, %d judged axes, %d errors, %d warnings"
          % (len(matrices), bound, judged, len(errors), len(warnings)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
