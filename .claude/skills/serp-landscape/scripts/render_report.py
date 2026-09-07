#!/usr/bin/env python3
"""Render the analysis as a standalone HTML report of 2x2 maps.

Each matrix becomes an SVG scatter with named poles and quadrant labels. Dots
are sized by the demand behind them, so a keyword carrying two hundred
variations reads bigger than a one-off. Hovering a dot shows the evidence,
because a position nobody can trace back to a number or a quote is an opinion.

Below the maps sit the tables the maps are built on: the pages doing the work,
who holds the topic, and what the winning titles have in common.

Usage:
    python3 render_report.py --analysis analysis.json --metrics metrics.json --out report.html
"""

import argparse
import html
import json
import os
from datetime import datetime, timezone

W, H = 640, 570
DENSE_W, DENSE_H = 820, 720
DENSE_AT = 22
PAD = {"l": 96, "r": 36, "t": 46, "b": 94}

INTENT_COLOUR = {"transactional": "var(--tx)", "commercial": "var(--cm)",
                 "informational": "var(--inf)", "mixed": "var(--mx)", "unknown": "var(--mut)"}


def esc(text):
    return html.escape(str(text or ""))


def ellipsis(text, n):
    text = str(text or "")
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def place_labels(points, x0, x1, blocked=(), char_w=6.4):
    """Nudge labels off each other and off the quadrant captions.

    Anything that cannot be placed clear gets no label: the dot keeps its hover
    text and the roster underneath carries the name, and an unreadable label is
    worse than no label.
    """
    taken, placed = list(blocked), []
    for px, py, text in points:
        w = char_w * len(text) + 10
        right = [(11, 4), (11, -11), (11, 15), (11, -22), (11, 26), (11, -33)]
        left = [(-w - 9, 4), (-w - 9, -11), (-w - 9, 15), (-w - 9, -22), (-w - 9, 26)]
        options = (left + right) if px + 11 + w > x1 else (right + left)
        for dx, dy in options:
            x, y = px + dx, py + dy
            if x < x0 - 70 or x + w > x1 + 70:
                continue
            box = (x, y - 11, x + w, y + 3)
            if all(box[2] < o[0] or box[0] > o[2] or box[3] < o[1] or box[1] > o[3]
                   for o in taken):
                taken.append(box)
                placed.append((x, y, text))
                break
        else:
            placed.append(None)
    return placed


def matrix_svg(matrix, labels_for, colour_for, size_for):
    x_axis, y_axis = matrix.get("x", {}), matrix.get("y", {})
    quads = matrix.get("quadrants", {})
    points = matrix.get("points", [])
    dense = len(points) > DENSE_AT
    w_, h_ = (DENSE_W, DENSE_H) if dense else (W, H)
    x0, x1 = PAD["l"], w_ - PAD["r"]
    y0, y1 = PAD["t"], h_ - PAD["b"]
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2

    def sx(v):
        return x0 + (max(0.0, min(10.0, float(v or 0))) / 10.0) * (x1 - x0)

    def sy(v):
        return y1 - (max(0.0, min(10.0, float(v or 0))) / 10.0) * (y1 - y0)

    s = ['<svg viewBox="0 0 %d %d" class="matrix%s" role="img" aria-label="%s">'
         % (w_, h_, " dense" if dense else "", esc(matrix.get("title", "2x2 matrix")))]
    s.append('<rect x="%g" y="%g" width="%g" height="%g" class="plot"/>'
             % (x0, y0, x1 - x0, y1 - y0))
    s.append('<rect x="%g" y="%g" width="%g" height="%g" class="q tr"/>'
             % (mx, y0, x1 - mx, my - y0))
    s.append('<rect x="%g" y="%g" width="%g" height="%g" class="q bl"/>'
             % (x0, my, mx - x0, y1 - my))
    s.append('<line x1="%g" y1="%g" x2="%g" y2="%g" class="mid"/>' % (mx, y0, mx, y1))
    s.append('<line x1="%g" y1="%g" x2="%g" y2="%g" class="mid"/>' % (x0, my, x1, my))

    blocked = []
    for key, cx, cy, anchor in (("tl", x0 + 10, y0 + 20, "start"), ("tr", x1 - 10, y0 + 20, "end"),
                                ("bl", x0 + 10, y1 - 10, "start"),
                                ("br", x1 - 10, y1 - 10, "end")):
        if quads.get(key):
            label = ellipsis(quads[key], 40)
            s.append('<text x="%g" y="%g" text-anchor="%s" class="qlabel">%s</text>'
                     % (cx, cy, anchor, esc(label)))
            width = 6.2 * len(label)
            left = cx - width if anchor == "end" else cx
            blocked.append((left, cy - 11, left + width, cy + 4))

    def axis_note(spec):
        return (" · measured: %s" % spec["metric"]) if spec.get("metric") else " · judged"

    s.append('<text x="%g" y="%g" text-anchor="middle" class="axis-name">%s<tspan class="src">%s'
             "</tspan></text>" % ((x0 + x1) / 2, h_ - 34, esc(x_axis.get("label", "")),
                                  esc(axis_note(x_axis))))
    s.append('<text x="%g" y="%g" text-anchor="start" class="pole">%s</text>'
             % (x0, y1 + 20, esc(ellipsis(x_axis.get("low", ""), 44))))
    s.append('<text x="%g" y="%g" text-anchor="end" class="pole">%s</text>'
             % (x1, y1 + 20, esc(ellipsis(x_axis.get("high", ""), 44))))
    s.append('<text transform="translate(26,%g) rotate(-90)" text-anchor="middle" '
             'class="axis-name">%s<tspan class="src">%s</tspan></text>'
             % ((y0 + y1) / 2, esc(y_axis.get("label", "")), esc(axis_note(y_axis))))
    s.append('<text transform="translate(46,%g) rotate(-90)" text-anchor="start" class="pole">%s'
             "</text>" % (y1, esc(ellipsis(y_axis.get("low", ""), 38))))
    s.append('<text transform="translate(46,%g) rotate(-90)" text-anchor="end" class="pole">%s'
             "</text>" % (y0, esc(ellipsis(y_axis.get("high", ""), 38))))

    drawn, label_seed = [], []
    for p in points:
        pid = p.get("id", "")
        cx, cy = sx(p.get("x")), sy(p.get("y"))
        drawn.append((cx, cy, pid, colour_for(p), size_for(p), p.get("evidence", "")))
        label_seed.append((cx, cy, ellipsis(labels_for(pid), 30 if dense else 26)))
    spots = place_labels(label_seed, x0, x1, blocked, 5.6 if dense else 6.4)
    # Big dots first so a small one is never hidden underneath.
    for i in sorted(range(len(drawn)), key=lambda i: -drawn[i][4]):
        cx, cy, pid, colour, radius, evidence = drawn[i]
        s.append('<g class="pt"><title>%s\n%s</title>'
                 '<circle cx="%g" cy="%g" r="%g" style="fill:%s"/>'
                 % (esc(labels_for(pid)), esc(evidence)[:420], cx, cy, radius, colour))
        if spots[i]:
            lx, ly, text = spots[i]
            s.append('<text x="%g" y="%g" class="plabel">%s</text>' % (lx, ly, esc(text)))
        s.append("</g>")
    s.append("</svg>")
    return "".join(s)


def quadrant_roster(matrix, labels_for):
    quads = matrix.get("quadrants", {})
    buckets = {"tl": [], "tr": [], "bl": [], "br": []}
    for p in matrix.get("points", []):
        key = ("t" if (p.get("y") or 0) >= 5 else "b") + ("r" if (p.get("x") or 0) >= 5 else "l")
        buckets[key].append(labels_for(p.get("id", "")))
    cells = []
    for key, fallback in (("tl", "top-left"), ("tr", "top-right"),
                          ("bl", "bottom-left"), ("br", "bottom-right")):
        names = buckets[key]
        shown = ", ".join(names[:10]) + (" +%d more" % (len(names) - 10) if len(names) > 10 else "")
        cells.append('<div class="quad"><div class="quad-h">%s <span>(%d)</span></div>'
                     '<div class="quad-n">%s</div></div>'
                     % (esc(quads.get(key) or fallback), len(names),
                        esc(shown) if names else "<span class='empty'>— empty</span>"))
    return '<div class="quads">%s</div>' % "".join(cells)


CSS = """
:root{--bg:#f6f7f9;--card:#fff;--ink:#16202b;--muted:#5b6b7c;--line:#dde3ea;
--tx:#c2410c;--cm:#1f3b57;--inf:#2f7d5f;--mx:#7d92a6;--mut:#a9b6c4;
--tint:#eef2f6;--tint2:#f7f4ee;}
@media (prefers-color-scheme:dark){:root{--bg:#12171d;--card:#19212a;--ink:#e8edf2;
--muted:#9aabbc;--line:#2a3542;--tx:#ff8a4c;--cm:#7fb3e0;--inf:#5fc79b;--mx:#5d7a94;
--mut:#4a5a6b;--tint:#1e2731;--tint2:#231f1a;}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Helvetica,Arial,sans-serif;}
.wrap{max-width:1200px;margin:0 auto;padding:40px 24px 80px}
h1{font-size:30px;line-height:1.2;margin:0 0 6px}
h2{font-size:20px;margin:44px 0 12px}
h3{font-size:17px;margin:0 0 4px}
.sub{color:var(--muted);margin:0 0 18px}
.lede{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 20px;margin:18px 0}
.stats{display:flex;flex-wrap:wrap;gap:22px;margin:14px 0 0;padding:0;list-style:none;color:var(--muted);font-size:13px}
.stats b{display:block;color:var(--ink);font-size:20px;font-weight:600}
ul.take{margin:8px 0 0;padding-left:20px} ul.take li{margin:6px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(440px,1fr));gap:20px;margin-top:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 20px 16px;overflow:hidden}
.why{color:var(--muted);font-size:13.5px;margin:2px 0 10px}
.reading{font-size:13.5px;margin:10px 0 0;padding-top:10px;border-top:1px solid var(--line)}
svg.matrix{width:100%;height:auto;display:block}
.plot{fill:none;stroke:var(--line)} .q{fill:var(--tint)} .q.tr{fill:var(--tint2)}
.mid{stroke:var(--line);stroke-dasharray:4 4}
.axis-name{fill:var(--ink);font-size:13px;font-weight:600}
.src{fill:var(--muted);font-size:10.5px;font-weight:400}
.pole{fill:var(--muted);font-size:11.5px}
.qlabel{fill:var(--muted);font-size:11px;letter-spacing:.06em;text-transform:uppercase}
.pt circle{stroke:var(--card);stroke-width:1.5}
.plabel{fill:var(--ink);font-size:11.5px}
svg.dense .plabel{font-size:10.5px} svg.dense .qlabel{font-size:10px}
.pt:hover circle{stroke:var(--ink);stroke-width:2}
.quads{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px;font-size:12.5px}
.quad{background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:8px 10px}
.quad-h{color:var(--muted);text-transform:uppercase;letter-spacing:.05em;font-size:10.5px;margin-bottom:2px}
.quad-h span{text-transform:none;letter-spacing:0}
.empty{color:var(--muted)}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);
border-radius:12px;overflow:hidden;font-size:13.5px}
th,td{text-align:left;padding:9px 12px;border-bottom:1px solid var(--line);vertical-align:top}
th{background:var(--tint);font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}
td.n{text-align:right;font-variant-numeric:tabular-nums}
tr:last-child td{border-bottom:none}
.scroll{overflow-x:auto}
.legend{display:flex;flex-wrap:wrap;gap:16px;color:var(--muted);font-size:12.5px;margin:10px 0 0;align-items:center}
.key{width:11px;height:11px;border-radius:50%;display:inline-block;margin-right:6px;vertical-align:-1px}
.tag{display:inline-block;padding:1px 7px;border-radius:20px;font-size:11.5px;background:var(--tint);color:var(--muted)}
footer{margin-top:44px;padding-top:16px;border-top:1px solid var(--line);color:var(--muted);font-size:12.5px}
@media print{body{background:#fff}.card,table{break-inside:avoid}}
"""


def build_html(analysis, metrics, title):
    kw_rows = metrics.get("keywords", {})
    page_rows = metrics.get("pages", {})
    summary = metrics.get("summary", {})

    def labels_for(pid):
        if pid in page_rows:
            row = page_rows[pid]
            return row.get("title") or row.get("domain") or pid
        return pid

    def colour_for(point):
        row = kw_rows.get(point.get("id"))
        if row:
            return INTENT_COLOUR.get(row.get("serp_intent"), "var(--mx)")
        page = page_rows.get(point.get("id"))
        if page:
            return INTENT_COLOUR.get(
                "transactional" if page.get("page_kind") in ("product", "category", "marketplace")
                else "commercial" if page.get("page_kind") in ("listicle", "comparison", "review")
                else "informational", "var(--mx)")
        return "var(--mx)"

    def size_for(point):
        # Dot area carries demand: a keyword standing for 200 variations should
        # not look like one standing for two.
        weight = point.get("size")
        if weight is None:
            row = kw_rows.get(point.get("id"), {})
            weight = row.get("demand_mass") or row.get("cluster_size") or 1
            if not row:
                weight = (page_rows.get(point.get("id"), {}).get("keywords_ranked") or 1) * 3
        try:
            weight = max(1.0, float(weight))
        except (TypeError, ValueError):
            weight = 1.0
        return round(min(15.0, 3.4 + 2.2 * (weight ** 0.5) / 2.2), 1)

    out = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
           '<meta name="viewport" content="width=device-width,initial-scale=1">',
           "<title>%s</title><style>%s</style></head><body><div class='wrap'>"
           % (esc(title), CSS)]
    out.append("<h1>%s</h1>" % esc(title))
    out.append('<p class="sub">What ranks for this topic and why, built from live autocomplete '
               "demand, the search results themselves, and the title, description and structure "
               "of every page that ranks.</p>")
    if analysis.get("market_definition"):
        out.append('<div class="lede">%s</div>' % esc(analysis["market_definition"]))
    out.append('<ul class="stats"><li><b>%s</b>keywords in the universe</li>'
               '<li><b>%s</b>SERPs captured</li><li><b>%s</b>ranking pages read</li>'
               '<li><b>%s</b>domains</li><li><b>%s</b>maps</li><li><b>%s</b>generated</li></ul>'
               % (summary.get("universe_keywords", "—"), summary.get("keywords_with_serps", "—"),
                  "%s of %s" % (summary.get("readable_pages", "—"),
                                summary.get("unique_pages", "—")),
                  summary.get("unique_domains", "—"), len(analysis.get("matrices", [])),
                  esc((analysis.get("generated_at") or "")[:10])))

    if analysis.get("takeaways"):
        out.append("<h2>What the data says</h2><ul class='take'>")
        out += ["<li>%s</li>" % esc(t) for t in analysis["takeaways"]]
        out.append("</ul>")

    if analysis.get("matrices"):
        out.append("<h2>The maps</h2>")
        out.append('<div class="legend">'
                   '<span><i class="key" style="background:var(--inf)"></i>informational SERP</span>'
                   '<span><i class="key" style="background:var(--cm)"></i>commercial SERP</span>'
                   '<span><i class="key" style="background:var(--tx)"></i>transactional SERP</span>'
                   '<span><i class="key" style="background:var(--mx)"></i>mixed</span>'
                   "<span>dot size = keywords in the universe behind it</span>"
                   "<span>hover a dot for the evidence</span></div>")
        out.append('<div class="grid">')
        for m in analysis["matrices"]:
            out.append('<section class="card"><h3>%s <span class="tag">%s</span></h3>'
                       % (esc(m.get("title", "")), esc(m.get("unit", "keyword"))))
            if m.get("why_it_matters"):
                out.append('<p class="why">%s</p>' % esc(m["why_it_matters"]))
            out.append(matrix_svg(m, labels_for, colour_for, size_for))
            if len(m.get("points", [])) >= 6:
                out.append(quadrant_roster(m, labels_for))
            if m.get("reading"):
                out.append('<p class="reading">%s</p>' % esc(m["reading"]))
            out.append("</section>")
        out.append("</div>")

    winners = sorted(page_rows.values(), key=lambda p: -p["visibility"])[:20]
    if winners:
        out.append("<h2>The pages doing the work</h2>")
        out.append('<p class="sub">Position-weighted across every captured SERP. A page holding '
                   "many keywords is a hub — that shape is the thing to copy, not any one "
                   "article.</p><div class='scroll'><table><tr><th>Page</th><th>Kind</th>"
                   "<th class='n'>Keywords</th><th class='n'>Best</th><th class='n'>Share</th>"
                   "<th class='n'>Words</th><th>Updated</th></tr>")
        for p in winners:
            out.append("<tr><td><b>%s</b><br><span class='why'>%s</span></td><td>%s</td>"
                       "<td class='n'>%s</td><td class='n'>#%s</td><td class='n'>%.1f%%</td>"
                       "<td class='n'>%s</td><td>%s</td></tr>"
                       % (esc(ellipsis(p["title"] or p["url"], 95)), esc(p["domain"]),
                          esc(p["page_kind"]), p["keywords_ranked"], p["best_position"],
                          p["visibility_share"],
                          p["word_count"] or "—" if p["readable"] else "blocked",
                          esc(p["modified"] or p["published"] or "—")))
        out.append("</table></div>")

    domains = metrics.get("domains", [])[:15]
    if domains:
        out.append("<h2>Who holds this topic</h2><div class='scroll'><table>"
                   "<tr><th>Domain</th><th class='n'>Keywords</th><th class='n'>Pages</th>"
                   "<th class='n'>Visibility</th><th class='n'>Avg position</th>"
                   "<th>Mostly</th></tr>")
        for d in domains:
            out.append("<tr><td>%s</td><td class='n'>%d</td><td class='n'>%d</td>"
                       "<td class='n'>%.1f%%</td><td class='n'>%.1f</td><td>%s</td></tr>"
                       % (esc(d["domain"]), d["keywords_ranked"], d["urls"],
                          d["visibility_share"], d["avg_position"], esc(d["top_kind"])))
        out.append("</table></div>")

    clusters = metrics.get("serp_clusters", [])[:15]
    if clusters:
        out.append("<h2>Keywords Google answers with the same pages</h2>")
        out.append('<p class="sub">Grouped where the top-10 results overlap: one page can serve '
                   "the whole group, so these are content briefs, not keyword lists.</p>"
                   "<div class='scroll'><table><tr><th>Head keyword</th><th class='n'>Keywords</th>"
                   "<th class='n'>Demand mass</th><th>SERP intent</th></tr>")
        for c in clusters:
            out.append("<tr><td>%s</td><td class='n'>%d</td><td class='n'>%d</td><td>%s</td></tr>"
                       % (esc(c["head"]), c["size"], c["demand_mass"], esc(c["serp_intent"])))
        out.append("</table></div>")

    if analysis.get("content_findings"):
        out.append("<h2>What the winning pages have in common</h2><ul class='take'>")
        out += ["<li>%s</li>" % esc(f) for f in analysis["content_findings"]]
        out.append("</ul>")

    blocked = [p for p in page_rows.values() if not p["readable"]]
    out.append("<footer>Built from %s keywords of live autocomplete demand, %s captured SERPs "
               "and %s pages read in full%s. Positions are a snapshot of one locale on one day, "
               "and rankings move. %s</footer>"
               % (summary.get("universe_keywords", "—"), summary.get("keywords_with_serps", "—"),
                  summary.get("readable_pages", "—"),
                  " on " + esc((analysis.get("generated_at") or "")[:10])
                  if analysis.get("generated_at") else "",
                  ("%d ranking page(s) could not be read (blocked or JS-only) and are excluded "
                   "from every median: %s." % (len(blocked),
                                               esc(", ".join(sorted({p["domain"] for p in blocked}))[:400]))
                   ) if blocked else "Every ranking page was readable."))
    out.append("</div></body></html>")
    return "".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--analysis", required=True)
    ap.add_argument("--metrics", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--title")
    args = ap.parse_args()

    with open(args.analysis, encoding="utf-8") as fh:
        analysis = json.load(fh)
    with open(args.metrics, encoding="utf-8") as fh:
        metrics = json.load(fh)
    analysis.setdefault("generated_at", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    seed = analysis.get("seed") or metrics.get("seed") or "this topic"
    title = args.title or "%s — what ranks, and why" % seed
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(build_html(analysis, metrics, title))
    print(json.dumps({"report": os.path.abspath(args.out),
                      "matrices": len(analysis.get("matrices", [])),
                      "points": sum(len(m.get("points", []))
                                    for m in analysis.get("matrices", []))}, indent=2))


if __name__ == "__main__":
    main()
