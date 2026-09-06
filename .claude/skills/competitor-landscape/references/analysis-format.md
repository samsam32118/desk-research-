# analysis.json

The one file you write by hand. `build_workbook.py` and `render_report.py` both
read it, so the field names matter.

## Schema

```jsonc
{
  "anchor": {"id": "blixon", "name": "Blixon", "domain": "blixon.com"},

  "market_definition": "One paragraph naming the market in the companies' own
                        vocabulary, and the axis of disagreement running
                        through it. Appears at the top of the report.",

  "generated_at": "2026-09-06",          // optional; filled in if absent

  "companies": [
    {
      "id": "acme",                       // short slug; matrices refer to this
      "name": "Acme",
      "domain": "acme.com",               // must match the scan filename's domain
      "level": 1,                         // 0 anchor, 1 direct set, 2 wider market
      "discovered_via": "named on blixon.com/compare/acme",
      "parent": "",                       // for subsidiaries, or the level-1 it came from
      "category": "field service software",
      "segment": "SMB to mid-market",
      "hq": "UK",
      "one_liner": "What they say they are, in their words",
      "positioning": "Fuller reading of the stance their copy takes",
      "icp": "Who the copy says it is for",
      "pricing_model": "per-seat, published",
      "price_signal": "from £29/user/mo",
      "key_claims": ["claim lifted from their H2s", "another"]
    }
  ],

  "matrices": [
    {
      "id": "wedge",
      "title": "Wedge: what they lead with",
      "why_it_matters": "One line on why this question separates this market",
      "x": {"label": "Product surface", "low": "single workflow",
            "high": "full platform"},
      "y": {"label": "Buyer promise", "low": "saves admin time",
            "high": "makes or saves money"},
      "quadrants": {"tl": "Efficiency tools", "tr": "Operating systems",
                    "bl": "Point utilities", "br": "Platform bets"},
      "points": [
        {"company": "acme",               // must match a companies[].id
         "x": 7.5, "y": 3.0,              // 0-10, both axes
         "evidence": "H1 on /pricing: 'Start free, upgrade when you outgrow it'"}
      ],
      "reading": "Two to four sentences: clusters, empty quadrant, where the
                  anchor sits."
    }
  ],

  "takeaways": [
    "Three to five findings, each specific enough to argue with."
  ],

  "sources": [
    {"url": "https://g2.com/categories/...", "used_for": "level-1 roster"}
  ]
}
```

## Rules the scripts depend on

- `points[].company` matches a `companies[].id`. A mismatch renders as a bare
  id with no level colour.
- `companies[].domain` matches the domain in the scan JSON, or the workbook
  cannot join copy to profile.
- `x` and `y` are numbers on 0-10. Out-of-range values are clamped, which
  silently distorts the chart — keep them in range.
- `quadrants` is optional; supplying it makes the chart far more readable, and
  the labels also appear in the workbook's Matrices sheet.
- `level` drives colour: 0 is the highlighted anchor, 1 the direct set, 2 the
  wider market.

## Where each field lands

| Field | Workbook | Report |
|---|---|---|
| `companies[]` | Companies sheet | company table |
| `matrices[].points[]` | Matrices sheet, one row per company per matrix | dots |
| `evidence` | Matrices sheet column | hover text on each dot |
| `market_definition`, `takeaways` | — | header and findings list |
| `sources[]` | Sources sheet | — |
| scan JSON | Pages, Headings, Vocabulary sheets | page and coverage counts |

## Validate before rendering

```bash
python3 scripts/check_analysis.py --analysis analysis.json --data data/
```

Errors (unknown company ids, out-of-range coordinates, an anchor missing from
its own matrix, an axis with no poles) must be fixed before rendering.

Warnings are judgement calls worth taking seriously:

- **Axis spread under 4** — that axis is not separating this market. Replace
  the question rather than stretching the scores.
- **Two axes ranking companies almost identically** — within one matrix that
  means the chart is a diagonal line; across two it means you drew one axis
  twice. Keep the better-evidenced question and find a genuinely independent
  one for the other.
- **Evidence under 15 characters** — that is a label, not evidence. Go back to
  the copy and quote it.
- **A company with no scan** — its profile is not grounded in its own words,
  so either scan it or say so in the report.
