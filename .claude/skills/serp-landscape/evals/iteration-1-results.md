# serp-landscape — iteration 1

| eval | config | tokens | min | 2x2s | points | evidence | measured axes | generic poles | xlsx w/ kw+title+desc |
|---|---|---|---|---|---|---|---|---|---|
| consumer-product-full-run | with_skill | 330k | 25.9 | 6 | 433 | 100% | 11 | 0 | yes |
| consumer-product-full-run | without_skill | 470k | 79.4 | 2* | 0 | — | — | — | yes |
| b2b-saas-why-ranking | with_skill | 290k | 27.0 | 6 | 311 | 100% | 10 | 0 | yes |
| b2b-saas-why-ranking | without_skill | 258k | 69.3 | 0 | 0 | — | — | — | yes |
| fast-shallow-scope | with_skill | 131k | 9.0 | 3 | 64 | 100% | 6 | 0 | yes |
| fast-shallow-scope | without_skill | 55k | 2.5 | 0 | 0 | — | — | — | — |

\* Baselines produce no analysis.json, so their charts were counted by hand from
their output files: the eval-1 baseline shipped two genuine 2x2s plus a ranked
bar chart as PNG/SVG, the eval-2 baseline six charts of which none was a 2x2,
and the shallow baseline none (none were asked for). Their dots carry no
machine-checkable coordinates, which is the difference that matters here --
not whether a quadrant chart exists.

## Confound

All six runs drew on one shared per-session web-search budget and exhausted it.
The with-skill runs started first and took 90/100 and 60/100 of their samples;
the eval-2 baseline reported 200/200 spent on its first call and fell back to
Brave via WebFetch, and the eval-1 baseline used DuckDuckGo for all 115 keywords.
Page-level extraction is unaffected on every run, but rank ordering is not
comparable across configurations, so the token and time deltas are not a clean
measurement of the skill. The qualitative gap below survives the confound.

## What survives

- Both with-skill full runs produced 6 matrices with 100% of points carrying
  evidence, zero generic axis poles, and every measured coordinate recomputed
  by check_analysis (0 errors). No baseline verified a coordinate.
- Baselines are strong: one harvested 34,165 autocomplete queries and read 944
  pages, the other built a 9-sheet workbook. A capable model reinvents much of
  this pipeline unprompted — which is evidence the architecture is right, and
  evidence that the skill's value is repeatability rather than capability.
- URLs are real on every run checked (20/20 on both baselines, 8/8 and 11/12
  with skill). Neither configuration fabricated results.
- No run presented invented search-volume figures.

## Fixed as a result

1. build_points.py — two agents independently wrote their own point generators.
2. Native Excel scatter charts — one agent hand-built six because the workbook
   shipped chartless against an 'excel + charts' request.
3. Search-budget guidance — both full runs ran out mid-sample.
4. Reverted a bad off-topic detector that flagged 'espresso machine india' and
   'buy espresso machine canada' as strays while missing the real ones.
5. SKILL.md now says to read serp_targets.txt before spending searches on it.

## Not fixed, worth knowing

- The eval-1 baseline measured DuckDuckGo showing ~0% Reddit where Brave shows
  21% on the same queries. Engine choice materially changes the UGC picture,
  which is why this skill requires a Google-grade search tool rather than
  scraping a fallback engine.