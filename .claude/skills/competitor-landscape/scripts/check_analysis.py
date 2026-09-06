#!/usr/bin/env python3
"""Check analysis.json before you render anything from it.

Catches the failures that are invisible in JSON but obvious in a chart: an axis
where every company scores the same, two matrices that secretly ask the same
question, a company plotted with no evidence behind it, an anchor missing from
its own map.

Usage:
    python3 check_analysis.py --analysis analysis.json --data data/

Exit code 1 if anything is broken (ERROR), 0 otherwise. Warnings are judgement
calls -- read them, then decide.
"""

import argparse
import glob
import json
import os
import sys
from itertools import combinations

MIN_SPREAD = 4.0        # below this an axis is not separating anyone
MIN_EVIDENCE = 15       # chars; shorter than this is a label, not evidence
DUP_AXIS_RHO = 0.9      # rank correlation above which two axes are one axis


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
    """Rank correlation, so we notice two axes that order companies alike."""
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
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--analysis", required=True)
    ap.add_argument("--data", help="scan directory, to cross-check coverage")
    args = ap.parse_args()

    with open(args.analysis, encoding="utf-8") as fh:
        a = json.load(fh)
    errors, warnings, notes = [], [], []

    companies = a.get("companies", [])
    ids = [c.get("id", "") for c in companies]
    if not companies:
        errors.append("no companies in analysis.json")
    for dup in {i for i in ids if ids.count(i) > 1}:
        errors.append("duplicate company id: %s" % dup)
    idset = set(ids)

    anchor = a.get("anchor", {})
    anchor_id = anchor.get("id") or anchor.get("domain", "")
    if anchor_id and anchor_id not in idset:
        by_domain = {c.get("domain"): c.get("id") for c in companies}
        anchor_id = by_domain.get(anchor.get("domain", ""), anchor_id)
        if anchor_id not in idset:
            errors.append("anchor %r is not in companies[]" % anchor_id)
    if not any(c.get("level") == 0 for c in companies):
        warnings.append("no company marked level 0 — the anchor will not be highlighted")

    matrices = a.get("matrices", [])
    if len(matrices) < 4:
        warnings.append("only %d matrices; 6 is the usual target" % len(matrices))

    axes = {}
    for m in matrices:
        mid = m.get("id", "?")
        pts = m.get("points", [])
        if not pts:
            errors.append("%s: no points" % mid)
            continue
        seen = [p.get("company") for p in pts]
        for c in seen:
            if c not in idset:
                errors.append("%s: point %r is not a known company id" % (mid, c))
        if anchor_id and anchor_id not in seen:
            errors.append("%s: anchor %r is not plotted" % (mid, anchor_id))
        missing = sorted(idset - set(seen))
        if missing:
            notes.append("%s: %d company(ies) unplotted: %s"
                         % (mid, len(missing), ", ".join(missing[:6])))
        for axis in ("x", "y"):
            spec = m.get(axis, {})
            if not spec.get("label") or not spec.get("low") or not spec.get("high"):
                errors.append("%s: %s axis needs label, low and high" % (mid, axis))
            elif spec["low"].strip().lower() in ("low", "less") or \
                    spec["high"].strip().lower() in ("high", "more"):
                warnings.append("%s: %s poles are generic (%r / %r) — name them in the "
                                "market's language" % (mid, axis, spec["low"], spec["high"]))
            vals = [p.get(axis) for p in pts]
            bad = [p.get("company") for p, v in zip(pts, vals)
                   if not isinstance(v, (int, float)) or not 0 <= v <= 10]
            if bad:
                errors.append("%s: %s out of 0-10 range for %s" % (mid, axis, ", ".join(map(str, bad))))
                continue
            spread = max(vals) - min(vals)
            if spread < MIN_SPREAD:
                warnings.append("%s: %s axis spread is only %.1f — this axis is not separating "
                                "anyone, replace it rather than stretching scores"
                                % (mid, axis, spread))
            axes["%s.%s" % (mid, axis)] = {p.get("company"): v for p, v in zip(pts, vals)}
        thin = [p.get("company") for p in pts if len(str(p.get("evidence", ""))) < MIN_EVIDENCE]
        if thin:
            warnings.append("%s: no real evidence for %s — a coordinate without a quote is a guess"
                            % (mid, ", ".join(map(str, thin[:6]))))

    for (ka, va), (kb, vb) in combinations(axes.items(), 2):
        shared = sorted(set(va) & set(vb))
        if len(shared) < 4:
            continue
        rho = spearman([va[c] for c in shared], [vb[c] for c in shared])
        if abs(rho) >= DUP_AXIS_RHO:
            if ka.split(".")[0] == kb.split(".")[0]:
                warnings.append("%s and %s rank companies almost identically (rho %.2f) — this "
                                "chart is a diagonal line, so one of its two axes is not asking a "
                                "separate question" % (ka, kb, rho))
            else:
                warnings.append("%s and %s rank companies almost identically (rho %.2f) — one axis "
                                "drawn twice across two matrices; keep the better-evidenced one"
                                % (ka, kb, rho))

    if args.data:
        scanned = {}
        for path in glob.glob(os.path.join(args.data, "*.json")):
            if os.path.basename(path) in ("roster.json", "analysis.json"):
                continue
            with open(path, encoding="utf-8") as fh:
                s = json.load(fh)
            scanned[s.get("domain", "")] = s.get("headings_found", 0)
        for c in companies:
            d = c.get("domain", "")
            if d not in scanned:
                warnings.append("%s (%s) has no scan — its profile is not grounded in its own copy"
                                % (c.get("name", "?"), d))
            elif scanned[d] == 0:
                notes.append("%s returned no copy; make sure the report says so" % d)

    for label, items in (("ERROR", errors), ("WARN", warnings), ("NOTE", notes)):
        for item in items:
            print("%-5s %s" % (label, item))
    print("\n%d companies, %d matrices, %d errors, %d warnings"
          % (len(companies), len(matrices), len(errors), len(warnings)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
