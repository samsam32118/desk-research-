#!/usr/bin/env python3
"""Render the analysis as a standalone HTML report of 2x2 maps.

Each matrix becomes an SVG scatter with named poles, quadrant labels, and the
anchor company highlighted. Hovering a dot shows the line of copy that put it
there, because a position nobody can trace back to evidence is just an opinion.

Usage:
    python3 render_report.py --analysis analysis.json --data data/ --out report.html
"""

import argparse
import glob
import html
import json
import os
from datetime import datetime, timezone

W, H = 620, 560
PAD = {"l": 92, "r": 34, "t": 44, "b": 92}


def esc(text):
    return html.escape(str(text or ""))


def wrap(text, width):
    words, lines, cur = str(text or "").split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= width:
            cur = (cur + " " + w).strip()
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def place_labels(points, x0, x1):
    """Nudge labels off each other, and inward, so a crowded corner stays readable."""
    taken, placed = [], []
    for px, py, text in points:
        w = 6.6 * len(text) + 10
        right = [(11, 4), (11, -11), (11, 15), (11, -22), (11, 26)]
        left = [(-w - 9, 4), (-w - 9, -11), (-w - 9, 15), (-w - 9, -22), (-w - 9, 26)]
        # A dot near the right edge gets its label on the inside, or it runs off.
        options = (left + right) if px + 11 + w > x1 else (right + left)
        for dx, dy in options:
            x, y = px + dx, py + dy
            if x < x0 - 60 or x + w > x1 + 60:
                continue
            box = (x, y - 11, x + w, y + 3)
            if all(box[2] < o[0] or box[0] > o[2] or box[3] < o[1] or box[1] > o[3] for o in taken):
                taken.append(box)
                placed.append((x, y, text))
                break
        else:
            x = px - w - 9 if px + 11 + w > x1 else px + 11
            taken.append((x, py - 7, x + w, py + 7))
            placed.append((x, py + 4, text))
    return placed


def matrix_svg(matrix, by_id, anchor_id):
    x_axis, y_axis = matrix.get("x", {}), matrix.get("y", {})
    quads = matrix.get("quadrants", {})
    x0, x1 = PAD["l"], W - PAD["r"]
    y0, y1 = PAD["t"], H - PAD["b"]
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2

    def sx(v):
        return x0 + (max(0.0, min(10.0, float(v))) / 10.0) * (x1 - x0)

    def sy(v):
        return y1 - (max(0.0, min(10.0, float(v))) / 10.0) * (y1 - y0)

    s = ['<svg viewBox="0 0 %d %d" class="matrix" role="img" aria-label="%s">'
         % (W, H, esc(matrix.get("title", "2x2 matrix")))]
    s.append('<rect x="%g" y="%g" width="%g" height="%g" class="plot"/>' % (x0, y0, x1 - x0, y1 - y0))
    s.append('<rect x="%g" y="%g" width="%g" height="%g" class="q tr"/>' % (mx, y0, x1 - mx, my - y0))
    s.append('<rect x="%g" y="%g" width="%g" height="%g" class="q bl"/>' % (x0, my, mx - x0, y1 - my))
    s.append('<line x1="%g" y1="%g" x2="%g" y2="%g" class="mid"/>' % (mx, y0, mx, y1))
    s.append('<line x1="%g" y1="%g" x2="%g" y2="%g" class="mid"/>' % (x0, my, x1, my))

    corners = [("tl", x0 + 10, y0 + 20, "start"), ("tr", x1 - 10, y0 + 20, "end"),
               ("bl", x0 + 10, y1 - 10, "start"), ("br", x1 - 10, y1 - 10, "end")]
    for key, cx, cy, anchor in corners:
        if quads.get(key):
            s.append('<text x="%g" y="%g" text-anchor="%s" class="qlabel">%s</text>'
                     % (cx, cy, anchor, esc(quads[key])[:38]))

    # axes: name in the middle, poles at the ends
    s.append('<text x="%g" y="%g" text-anchor="middle" class="axis-name">%s</text>'
             % ((x0 + x1) / 2, H - 34, esc(x_axis.get("label", ""))))
    s.append('<text x="%g" y="%g" text-anchor="start" class="pole">%s</text>'
             % (x0, y1 + 20, esc(x_axis.get("low", ""))[:34]))
    s.append('<text x="%g" y="%g" text-anchor="end" class="pole">%s</text>'
             % (x1, y1 + 20, esc(x_axis.get("high", ""))[:34]))
    s.append('<text transform="translate(26,%g) rotate(-90)" text-anchor="middle" class="axis-name">%s</text>'
             % ((y0 + y1) / 2, esc(y_axis.get("label", ""))))
    s.append('<text transform="translate(46,%g) rotate(-90)" text-anchor="start" class="pole">%s</text>'
             % (y1, esc(y_axis.get("low", ""))[:30]))
    s.append('<text transform="translate(46,%g) rotate(-90)" text-anchor="end" class="pole">%s</text>'
             % (y0, esc(y_axis.get("high", ""))[:30]))

    pts, labels = [], []
    for p in matrix.get("points", []):
        prof = by_id.get(p.get("company")) or by_id.get(p.get("domain")) or {}
        name = prof.get("name") or p.get("company", "?")
        cx, cy = sx(p.get("x", 5)), sy(p.get("y", 5))
        is_anchor = (p.get("company") == anchor_id or prof.get("domain") == anchor_id
                     or prof.get("level") == 0)
        pts.append((cx, cy, name, is_anchor, prof.get("level", 1), p.get("evidence", "")))
        labels.append((cx, cy, name[:26]))
    for (cx, cy, name, is_anchor, level, evidence), (lx, ly, text) in zip(
            pts, place_labels(labels, x0, x1)):
        cls = "dot anchor" if is_anchor else "dot lvl%s" % (level if level in (1, 2) else 1)
        s.append('<g class="pt"><title>%s — %s</title>'
                 '<circle cx="%g" cy="%g" r="%g" class="%s"/>'
                 '<text x="%g" y="%g" class="plabel%s">%s</text></g>'
                 % (esc(name), esc(evidence)[:400], cx, cy, 8 if is_anchor else 5.5, cls,
                    lx, ly, " anchor" if is_anchor else "", esc(text)))
    s.append("</svg>")
    return "".join(s)


def quadrant_roster(matrix, by_id):
    quads = matrix.get("quadrants", {})
    buckets = {"tl": [], "tr": [], "bl": [], "br": []}
    for p in matrix.get("points", []):
        key = ("t" if p.get("y", 5) >= 5 else "b") + ("r" if p.get("x", 5) >= 5 else "l")
        prof = by_id.get(p.get("company")) or {}
        buckets[key].append(prof.get("name") or p.get("company", "?"))
    order = [("tl", "top-left"), ("tr", "top-right"), ("bl", "bottom-left"), ("br", "bottom-right")]
    cells = []
    for key, fallback in order:
        names = buckets[key]
        cells.append('<div class="quad"><div class="quad-h">%s</div><div class="quad-n">%s</div></div>'
                     % (esc(quads.get(key) or fallback),
                        esc(", ".join(names)) if names else "<span class='empty'>— empty</span>"))
    return '<div class="quads">%s</div>' % "".join(cells)


CSS = """
:root{--bg:#f6f7f9;--card:#fff;--ink:#16202b;--muted:#5b6b7c;--line:#dde3ea;
--accent:#c2410c;--l1:#1f3b57;--l2:#7d92a6;--tint:#eef2f6;--tint2:#f7f4ee;}
@media (prefers-color-scheme:dark){:root{--bg:#12171d;--card:#19212a;--ink:#e8edf2;
--muted:#9aabbc;--line:#2a3542;--accent:#ff8a4c;--l1:#7fb3e0;--l2:#5d7a94;--tint:#1e2731;--tint2:#231f1a;}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Helvetica,Arial,sans-serif;}
.wrap{max-width:1180px;margin:0 auto;padding:40px 24px 80px}
h1{font-size:30px;line-height:1.2;margin:0 0 6px}
h2{font-size:20px;margin:44px 0 12px}
h3{font-size:17px;margin:0 0 4px}
.sub{color:var(--muted);margin:0 0 18px}
.lede{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 20px;margin:18px 0}
.stats{display:flex;flex-wrap:wrap;gap:22px;margin:14px 0 0;padding:0;list-style:none;color:var(--muted);font-size:13px}
.stats b{display:block;color:var(--ink);font-size:20px;font-weight:600}
ul.take{margin:8px 0 0;padding-left:20px} ul.take li{margin:6px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(430px,1fr));gap:20px;margin-top:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px 20px 16px;overflow:hidden}
.why{color:var(--muted);font-size:13.5px;margin:2px 0 10px}
.reading{font-size:13.5px;margin:10px 0 0;padding-top:10px;border-top:1px solid var(--line)}
svg.matrix{width:100%;height:auto;display:block}
.plot{fill:none;stroke:var(--line)} .q{fill:var(--tint)} .q.tr{fill:var(--tint2)}
.mid{stroke:var(--line);stroke-dasharray:4 4}
.axis-name{fill:var(--ink);font-size:13px;font-weight:600}
.pole{fill:var(--muted);font-size:11.5px}
.qlabel{fill:var(--muted);font-size:11px;letter-spacing:.06em;text-transform:uppercase}
.dot{fill:var(--l1);stroke:var(--card);stroke-width:1.5}
.dot.lvl2{fill:var(--l2)} .dot.anchor{fill:var(--accent);stroke-width:2.5}
.plabel{fill:var(--ink);font-size:11.5px} .plabel.anchor{font-weight:700;fill:var(--accent)}
.pt:hover .dot{r:9}
.quads{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px;font-size:12.5px}
.quad{background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:8px 10px}
.quad-h{color:var(--muted);text-transform:uppercase;letter-spacing:.05em;font-size:10.5px;margin-bottom:2px}
.empty{color:var(--muted)}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);
border-radius:12px;overflow:hidden;font-size:13.5px}
th,td{text-align:left;padding:9px 12px;border-bottom:1px solid var(--line);vertical-align:top}
th{background:var(--tint);font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}
tr:last-child td{border-bottom:none}
tr.anchor td{background:var(--tint2);font-weight:600}
.legend{display:flex;gap:18px;color:var(--muted);font-size:12.5px;margin:10px 0 0;align-items:center}
.key{width:11px;height:11px;border-radius:50%;display:inline-block;margin-right:6px;vertical-align:-1px}
footer{margin-top:44px;padding-top:16px;border-top:1px solid var(--line);color:var(--muted);font-size:12.5px}
@media print{body{background:#fff}.card,table{break-inside:avoid}}
"""


def build_html(analysis, sites, title):
    companies = analysis.get("companies", [])
    by_id = {}
    for c in companies:
        by_id[c.get("id", c.get("domain", ""))] = c
        by_id[c.get("domain", "")] = c
    anchor = analysis.get("anchor", {})
    anchor_id = anchor.get("id") or anchor.get("domain", "")
    pages = sum(len(s.get("pages", [])) for s in sites)

    out = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
           '<meta name="viewport" content="width=device-width,initial-scale=1">',
           "<title>%s</title><style>%s</style></head><body><div class='wrap'>" % (esc(title), CSS)]
    out.append("<h1>%s</h1>" % esc(title))
    out.append('<p class="sub">Competitive landscape built from what these companies say about '
               "themselves — meta titles, meta descriptions and H1/H2/H3 copy on their own "
               "marketing pages.</p>")
    if analysis.get("market_definition"):
        out.append('<div class="lede">%s</div>' % esc(analysis["market_definition"]))
    out.append('<ul class="stats"><li><b>%d</b>companies mapped</li><li><b>%d</b>pages read</li>'
               '<li><b>%d</b>maps</li><li><b>%s</b>generated</li></ul>'
               % (len(companies) or len(sites), pages, len(analysis.get("matrices", [])),
                  esc((analysis.get("generated_at") or "")[:10])))

    if analysis.get("takeaways"):
        out.append("<h2>What the map says</h2><ul class='take'>")
        out += ["<li>%s</li>" % esc(t) for t in analysis["takeaways"]]
        out.append("</ul>")

    if analysis.get("matrices"):
        out.append("<h2>The maps</h2>")
        out.append('<div class="legend"><span><i class="key" style="background:var(--accent)"></i>%s'
                   '</span><span><i class="key" style="background:var(--l1)"></i>direct set (level 1)'
                   '</span><span><i class="key" style="background:var(--l2)"></i>wider market (level 2)'
                   "</span><span>hover a dot for the line of copy behind its position</span></div>"
                   % esc(anchor.get("name", "anchor company")))
        out.append('<div class="grid">')
        for m in analysis["matrices"]:
            out.append('<section class="card"><h3>%s</h3>' % esc(m.get("title", "")))
            if m.get("why_it_matters"):
                out.append('<p class="why">%s</p>' % esc(m["why_it_matters"]))
            out.append(matrix_svg(m, by_id, anchor_id))
            if len(m.get("points", [])) >= 6:
                out.append(quadrant_roster(m, by_id))
            if m.get("reading"):
                out.append('<p class="reading">%s</p>' % esc(m["reading"]))
            out.append("</section>")
        out.append("</div>")

    if companies:
        out.append("<h2>The companies</h2><table><tr><th>Level</th><th>Company</th>"
                   "<th>What they say they are</th><th>Who for</th><th>Pricing</th>"
                   "<th>Found via</th></tr>")
        for c in sorted(companies, key=lambda c: (c.get("level", 9), c.get("name", ""))):
            out.append("<tr%s><td>%s</td><td><b>%s</b><br><span class='why'>%s</span></td>"
                       "<td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                       % (" class='anchor'" if c.get("level") == 0 else "",
                          esc(c.get("level", "")), esc(c.get("name", "")), esc(c.get("domain", "")),
                          esc(c.get("one_liner") or c.get("positioning", "")), esc(c.get("icp", "")),
                          esc(c.get("pricing_model") or c.get("price_signal", "")),
                          esc(c.get("discovered_via", ""))))
        out.append("</table>")

    gaps = [s["domain"] for s in sites if s.get("headings_found", 0) == 0]
    out.append("<footer>Built from %d pages across %d sites%s. Positions are read from public "
               "marketing copy, not from product testing or pricing quotes — treat them as a map "
               "of stated positioning, which is what a buyer comparing tabs actually sees.%s</footer>"
               % (pages, len(sites),
                  " on " + esc((analysis.get("generated_at") or "")[:10]) if analysis.get("generated_at") else "",
                  (" No copy could be extracted from: " + esc(", ".join(gaps)) + ".") if gaps else ""))
    out.append("</div></body></html>")
    return "".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--analysis", required=True)
    ap.add_argument("--data", help="scan directory, for page counts and coverage gaps")
    ap.add_argument("--out", required=True)
    ap.add_argument("--title")
    args = ap.parse_args()

    with open(args.analysis, encoding="utf-8") as fh:
        analysis = json.load(fh)
    analysis.setdefault("generated_at", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    sites = []
    if args.data:
        for path in sorted(glob.glob(os.path.join(args.data, "*.json"))):
            if os.path.basename(path) in ("roster.json", "analysis.json"):
                continue
            with open(path, encoding="utf-8") as fh:
                sites.append(json.load(fh))
    anchor = analysis.get("anchor", {})
    title = args.title or "%s — competitive landscape" % (anchor.get("name") or anchor.get("domain", "Market"))
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(build_html(analysis, sites, title))
    print(json.dumps({"report": os.path.abspath(args.out),
                      "matrices": len(analysis.get("matrices", [])),
                      "companies": len(analysis.get("companies", []))}, indent=2))


if __name__ == "__main__":
    main()
