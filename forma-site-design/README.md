# Forma Site Design — competitive landscape

Desk research on **Autodesk Forma Site Design**
(https://www.autodesk.com/products/forma-site-design/overview), run with the
`competitor-landscape` skill in this repo. Two levels deep: 30 companies,
136 marketing pages, 1,800+ headings, six 2x2 maps.

## Deliverables

| File | What it is |
|---|---|
| `forma-site-design-landscape.html` | The report — six 2x2s, evidence on hover over every dot |
| `forma-site-design-landscape.xlsx` | Companies, Pages, Headings, Matrices, Vocabulary, Sources |
| `digest.md` | Every company's meta title, description, H1 and heading ladder |
| `analysis.json` | Profiles, axes and scored positions (the hand-written file) |
| `roster.json` | Who was included, at what level, and how they were found |
| `data/` | One JSON per company — the raw scan |

## The market

Software that compresses the weeks between acquiring a site and committing to a
scheme. One disagreement runs through it: whether the early study exists to
establish **how a place will perform** (sun, wind, noise, density, carbon) or
**whether the deal makes money**. Forma is the clearest statement of the first
position; Aprao, Deepblocks and TestFit of the second.

## Coverage gaps — read these before trusting a quadrant

`www.autodesk.com` returns **HTTP 403 to this network on every path**, robots.txt
included (Akamai edge). The anchor's body copy therefore comes from
`blogs.autodesk.com/forma` — Autodesk's own Forma marketing blog — plus the
product pages' meta titles as indexed by search. Page URLs are preserved in
`data/autodesk-com.json` so every quote is traceable to the host it came from.

- **Bentley OpenSite+** — `www.bentley.com` serves a JS sign-in gate here. Meta
  titles only; plotted on four of six maps, left off `evidence` where no quote
  supports a position.
- **cove.tool (cove.inc)** — HTTP 202 bot challenge, no copy at all. In the
  workbook, on no map.
- **Geopogo** — client-side rendered; meta title and description only.
- **Hypar, Finch, Giraffe** — client-side rendered; copy recovered verbatim via
  WebFetch, or from Hypar's own `llms.txt` (which its robots.txt publishes for
  agents). Marked `recovered_via` on each page record.
- Hypar's robots.txt permits only `/`, `/pricing` and `/llms.txt`; a page the
  scanner pulled outside that list was dropped rather than used.

Anything the corpus could not read is absent from the maps, not estimated. An
under-populated quadrant may be a coverage gap rather than white space.

## Reproducing it

```bash
S=../.claude/skills/competitor-landscape/scripts
python3 $S/scan_site.py $(cat domains.txt) --out data/ --max-pages 8 --workers 8
python3 $S/digest.py  --data data/ --roster roster.json --out digest.md
python3 $S/facets.py  --data data/                       # candidate axes
python3 tools/build_analysis.py && python3 tools/build_matrices.py   # writes analysis.json
python3 $S/check_analysis.py  --analysis analysis.json --data data/
python3 $S/build_workbook.py  --data data/ --analysis analysis.json --out forma-site-design-landscape.xlsx
python3 $S/render_report.py   --analysis analysis.json  --data data/ --out forma-site-design-landscape.html
```

`tools/browser_scan.py` runs the same scanner through headless Chromium for
sites that answer a browser but not urllib. It is kept for reuse but was **not**
used for this run: Chromium cannot reach this environment's egress proxy, so the
JS-rendered sites were recovered with WebFetch instead.
