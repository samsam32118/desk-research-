# analysis.json

The one file you author. You write the matrices — the questions, the poles,
the quadrant labels and the reading; `build_points.py` fills the coordinates
from the data. `check_analysis.py`, `build_workbook.py` and `render_report.py`
all read it, so the field names matter.

## Schema

```jsonc
{
  "seed": "espresso machine",

  "market_definition": "One paragraph: what this search topic is, who is
                        currently answering it, and the tension running through
                        it. Appears at the top of the report.",

  "generated_at": "2026-09-07",          // optional; filled in if absent

  "matrices": [
    {
      "id": "opportunity",
      "unit": "keyword",                  // keyword | page | domain
      "title": "Where the demand is not already owned",
      "why_it_matters": "One line on why this question separates this topic",

      "x": {"label": "SERP lock-in", "low": "wide open",
            "high": "same three domains everywhere",
            "metric": "incumbent_share"}, // omit metric for a judged axis

      "y": {"label": "Demand behind the query", "low": "one-off phrasing",
            "high": "200+ variations", "metric": "demand_mass"},

      "quadrants": {"tl": "Big and open — write here first",
                    "tr": "Big and locked", "bl": "Small and open",
                    "br": "Small and locked"},

      // Leave "points" out and build_points.py fills it. Shown here so you
      // know what it produces, and so a judged matrix can be written by hand.
      "points": [
        {"id": "espresso machine for home",   // keyword, URL or domain
         "x": 3.2, "y": 8.6,                  // 0-10, from metrics.json
         "size": 122,                         // optional; defaults to demand mass
         "evidence": "8 of 10 results are buying guides; #1 is a 5,985-word
                      listicle titled 'Top 5 Best Espresso Machines with
                      Grinders in 2026'"}
      ],

      "reading": "Two to four sentences: clusters, the empty quadrant, and what
                  someone should do differently because of it."
    }
  ],

  "takeaways": [
    "Three to five findings, each specific enough to argue with."
  ],

  "content_findings": [
    "What the winning pages have in common: length, format, freshness, title
     shape, structured data. Rendered as its own section."
  ],

  "sources": [
    {"source": "manual", "url": "https://...", "used_for": "checked a blocked page"}
  ]
}
```

## Rules the scripts depend on

- **`points[].id` must exist in `metrics.json`** under the matrix's `unit`:
  a keyword string for `unit: keyword`, a result URL exactly as it appears in
  `serp.json` for `unit: page`, a registrable domain for `unit: domain`. A
  mismatch is an error, not a silent blank.
- **A bound axis must match the data.** When `x.metric` is set, every
  `points[].x` is compared against
  `metrics.json` → `axes.<unit>.<metric>.values[<id>]` and must agree within
  0.6. Let `build_points.py` write them rather than typing them.
- **`metric` names must be in the catalogue.** The error message lists what is
  available for that unit.
- `x` and `y` are numbers on 0-10.
- `quadrants` is optional, and supplying it makes the chart far more readable —
  the labels also reach the workbook's Matrices sheet.
- `size` is optional. Left out, a keyword dot is sized by demand mass and a
  page dot by how many keywords it ranks for.
- Every point needs `evidence`. Under 20 characters is warned as a label rather
  than evidence.

## Where each field lands

| Field | Workbook | Report |
|---|---|---|
| `matrices[].points[]` | Matrices sheet, one row per point | dots |
| `evidence` | Matrices sheet column | hover text on each dot |
| `x.metric` / `y.metric` | Matrices sheet columns | "measured: …" under the axis name |
| `market_definition`, `takeaways` | — | header and findings list |
| `content_findings` | — | "What the winning pages have in common" |
| `sources[]` | Sources sheet | — |
| `metrics.json` | Keywords, Pages, Domains, Clusters, Titles sheets | tables and footer |
| `keywords.json` | Keywords sheet (whole universe) | keyword count |
| `serp.json` | SERP results sheet | — |

The workbook and report read `metrics.json` directly, so the data sheets are
complete whether or not you have written `analysis.json` yet. If the user wants
to see the raw table before any interpretation, build the workbook first and
re-run it after the analysis to fill in the Matrices sheet.

## Filling the points

Do not type coordinates. Write the matrices with their axes, poles and quadrant
labels, leave `points` out, and run:

```bash
python3 scripts/build_points.py --metrics metrics.json --analysis analysis.json \
    --write --limit 60
```

It fills every matrix whose axes both name a metric, and reports each one's
spread and quadrant occupancy so you can write the `reading` from real counts.
Options:

- `--limit N` — most points per matrix. Keywords are kept by demand mass and
  pages by visibility, so trimming drops trivia rather than the market.
- `--refill` — replace points that are already there.
- `"only": ["kw1", "kw2"]` on a matrix — plot exactly these ids instead of the
  top N.

A matrix with a judged axis is skipped and stays yours to write, with a quote
on every point.

## Validate before rendering

```bash
python3 scripts/check_analysis.py --analysis analysis.json --metrics metrics.json
```

Errors must be fixed:

- a coordinate that disagrees with the metric it claims
- a metric name that is not in the catalogue
- a point id that is not in the dataset
- an axis missing a label or poles, a coordinate outside 0-10, a duplicated point

Warnings are judgement calls worth taking seriously:

- **Axis spread under 4** — that axis is not separating this corpus. Take a
  wider one from the digest rather than stretching scores.
- **Two axes ranking the corpus almost identically** — within one matrix that
  is a diagonal; across two it is one axis drawn twice.
- **Points plotted on thin SERPs** — under half the results readable means the
  medians behind that dot rest on very little.
- **A quadrant called empty that is not** — the occupancy line above the
  warning tells you the real count.
- **Fewer than 8 points on a matrix** — a 2x2 with five dots is an assertion
  with a chart around it.
- **Under 70% page coverage** — say so in the write-up; a thin quadrant and an
  unread one look identical to a reader.
