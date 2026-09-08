---
name: serp-landscape
description: Find out what is ranking on Google for a topic and why, from a single seed keyword. It expands the seed into thousands of real autocomplete queries, groups them into topics, runs web searches across a sample of ~100 of them, reads every ranking page to extract its real title, meta description, heading ladder, word count, freshness and page type, then delivers an Excel workbook of every keyword with the extracted titles and descriptions plus a set of 2x2 maps whose axes are computed from the data and verified against it. Use this whenever someone mentions SERPs, what ranks on Google, why a page or competitor is ranking, keyword research or a keyword universe, search intent, long-tail or related keywords, topic and keyword clustering, content gap or content strategy, title tag and meta description analysis, share of voice in search, "what should I write to rank", who owns a topic in search, or asks for a 2x2 of keywords or search demand — including when they hand over nothing but one keyword and ask what is going on in that search results page.
---

# SERP landscape

One seed keyword goes in. A map of what Google actually rewards for that topic
comes out, built from three kinds of evidence that are cheap to get and hard to
argue with:

- **what people search** — live autocomplete, thousands of queries deep
- **what ranks** — the results your web search tool returns for a sample of them
- **why it ranks** — the real title, meta description, heading ladder, length,
  freshness and format of every page that shows up

That last layer is the point. Anyone can tell you a page ranks first. This
tells you it is a 5,985-word listicle with 2026 in the title, updated three
months ago, carrying FAQ schema — and that eight of the ten pages around it
look the same. A ranking without the page behind it is trivia; the pattern
across the pages is the answer to "what do I have to write".

## Shape of the work

```
seed keyword
   |
   v  expand_keywords.py   autocomplete, 3 levels deep -> ~5,000 keywords
   |                       grouped into ~600 topics, ~100 sampled for SERPs
   v  web search           the sampled keywords, 8-12 searches per turn
   v  record_serp.py       paste the results; it normalises and dedupes them
   v  fetch_pages.py       every unique ranking URL, read once
   v  serp_metrics.py      intent, clusters, share of voice, 0-10 axis metrics
   v  analysis.json        you write this: the 2x2s and what they mean
   v  check_analysis.py    recomputes every measured coordinate
   |
   v  workbook.xlsx + report.html
```

The asymmetry in the middle drives everything else. Autocomplete is free, so
the keyword universe is thousands. A web search costs a tool call, so SERPs are
sampled — one keyword per topic, biggest topics first, each carrying the demand
mass of the topic it stands for. That is also how a real SEO team works: you
map demand broadly, then look closely at the queries that represent it.

## Before you start

Settle these in one pass. Pick sensible defaults, say what you picked, and get
moving rather than interviewing the user:

- **The seed.** One keyword or phrase, the way a searcher would type it —
  `espresso machine`, not `espresso machines (commercial + domestic)`. If the
  user gives a brand or a URL instead, the seed is the *category* it competes
  in; say which you chose. A seed with two meanings ("mercury", "swift") will
  produce two unrelated markets, so check the first autocomplete round and
  split or narrow if it did.
- **Locale.** Default `en-US`. Rankings and autocomplete are both
  locale-specific, and a UK or German run genuinely differs — ask only if the
  user's context hints at one.
- **How many SERPs.** Default 100. This is the number that decides how long
  the run takes, because each one is a search call.
- **Where output goes.** Default a new folder `<seed-slug>-serp/`.

Then say what to expect: a few thousand keywords in about a minute, ~100
searches over several turns, a few hundred pages read, two files at the end.

## Pipeline

Set the paths once:

```bash
SKILL=<absolute path to the directory holding this SKILL.md>
OUT=<seed-slug>-serp
mkdir -p "$OUT"
```

### 1. Build the keyword universe

```bash
python3 "$SKILL/scripts/expand_keywords.py" "<seed>" \
    --target 5000 --sample 100 --locale en-US --out "$OUT/keywords.json"
```

Roughly 700 autocomplete calls, half a minute, no API key. Read the summary it
prints before going further — `by_intent_prior` and the cluster labels tell you
whether the seed meant what you thought. If `dropped_off_topic` is huge or the
top clusters look like a different market, the seed was ambiguous: fix it now,
because everything downstream inherits it.

**Then read `serp_targets.txt` before spending a single search on it.** A seed
word with two lives pulls in real demand for a different subject — an "espresso
machine" run picks up a video-game item and a Mac text editor, all genuinely
searched. Thirty seconds of eyeballing the sample is the cheapest point in the
whole pipeline to catch that; after the searches are spent it costs a rerun.
Strays that survive show up again in the digest as SERPs sharing nothing with
the rest of the corpus, but by then you have paid for them.

Raise `--target` and `--branch` freely for a bigger universe; add
`--sources google,youtube` when the topic has a how-to or visual half, since
YouTube autocomplete returns about 50% different phrasing. Full options and the
non-English notes: **`references/keyword-expansion.md`**.

### 2. Capture the SERPs

This is the only part that costs turns. `$OUT/serp_targets.txt` holds the
sampled keywords.

Work in batches: **issue 8-12 web searches in one turn**, then write what came
back into a ledger file and record it. Do not search one keyword per turn — the
searches do not depend on each other, and running them together is the
difference between a five-minute job and an hour.

**Sessions have a web-search budget, and a 100-keyword run will get close to
it.** Both full-scale test runs ran out before finishing their sample, at 90
and 60 keywords. So spend the allowance on the sample rather than on
exploratory searching, work down `serp_targets.txt` in its existing order —
biggest topics first, so an early stop still covers the demand — and if you run
out, say how many of the planned keywords you captured instead of implying the
sample was the plan. Falling short is a coverage gap like any other; hiding it
is the only real failure.

The ledger is forgiving. The cheapest thing to write is the results array from
each search, under a heading:

```
## espresso machine for home
[{"title":"...","url":"https://..."},{"title":"...","url":"https://..."}]

## espresso machine with grinder
1. https://example.com/guide | The Best Home Espresso Machines
2. https://other.com/review
```

```bash
python3 "$SKILL/scripts/record_serp.py" --ledger "$OUT/batch1.md" \
    --out "$OUT/serp.json" --targets "$OUT/serp_targets.txt"
```

It reports `targets_missing` and writes the remaining keywords to a file, so
you always know where you are. Re-recording a keyword replaces it, so a
re-search after a bad batch is safe. Keep going until the remaining list is
empty or you have what you need.

Rank comes from the order you paste, so keep it. Titles are optional — step 3
reads the real one off the page. Details and the gap-handling rules:
**`references/serp-capture.md`**.

### 3. Read every ranking page

```bash
python3 "$SKILL/scripts/fetch_pages.py" --serp "$OUT/serp.json" \
    --out "$OUT/pages.jsonl" --workers 8
```

One fetch per unique URL however many keywords it ranks for. Check
`coverage_pct` in the output. Publishers block bots, so 70-85% is a normal,
good run; below ~60% the medians are resting on too little and you should say
so in the write-up rather than quietly averaging what is left.

Blocked URLs are written to `pages_blocked.txt`. If a blocked page holds a top
position across several keywords, it matters enough to spend a `WebFetch` on —
ask for the exact title, meta description and H2s, verbatim, because a
paraphrase cannot be used as evidence. Everything still unreachable goes in the
report as a named gap.

### 4. Compute the metrics

```bash
python3 "$SKILL/scripts/serp_metrics.py" --serp "$OUT/serp.json" \
    --pages "$OUT/pages.jsonl" --keywords "$OUT/keywords.json" \
    --out "$OUT/metrics.json" --digest "$OUT/digest.md"
```

Then **read `digest.md`**. It is written to be read, and it is where the
analysis actually happens:

- **Who holds this topic** — share of voice by domain
- **The pages doing the work** — with length, freshness, schema and the meta
  description quoted, which is where the "why" lives
- **Keyword groups Google answers with the same pages** — keywords sharing 4+
  of their top 10, so one page serves the group
- **Where the wording and the SERP disagree** — queries that read commercial
  but return guides, and vice versa. This is usually the most valuable section:
  it is a list of queries people are writing the wrong format for
- **Candidate axes ranked by how much they separate** — pick your 2x2 axes from
  the top of this list

Do not pull `metrics.json` or `pages.jsonl` into context wholesale. They are
large and repetitive, and you need the context for thinking. Open a specific
record when you need one page's exact H2s.

### 5. Write `analysis.json`

Six to eight matrices, mixing keyword-unit maps (which queries to go after) and
page-unit maps (what winning pages have in common). Axes should bind to a
computed metric wherever one exists:

```json
{"id": "intent-depth", "unit": "keyword",
 "x": {"label": "Commercial pull", "low": "guides win",
       "high": "product and category pages win", "metric": "commercial_serp"},
 "y": {"label": "Depth that ranks", "low": "under 800 words",
       "high": "3,000+ words", "metric": "content_depth"},
 "points": [{"id": "espresso machine for home", "x": 7.2, "y": 8.6,
             "evidence": "8 of 10 are buying guides; #1 is a 5,985-word listicle"}]}
```

Then leave `points` out and let the coordinates be filled from the data:

```bash
python3 "$SKILL/scripts/build_points.py" --metrics "$OUT/metrics.json" \
    --analysis "$OUT/analysis.json" --write --limit 60
```

Six matrices over a 100-keyword run is around six hundred coordinates; typing
those is slow, and a number copied by hand is a number that can drift from the
measurement it claims. This fills every matrix whose axes both name a metric,
generates evidence from the same numbers, and prints each matrix's spread and
quadrant occupancy — which is what you need to write the `reading`. It leaves
judged matrices alone, because their points are yours to quote.

Then write the `reading` for each matrix, the `takeaways` and the
`content_findings` yourself. That is the part nobody can compute.

An axis with no measurement is allowed when the question is genuinely
qualitative — how a title frames its promise, say — but then every point needs
a quote. Mark it by leaving `metric` out. Axis library, scoring rules and the
full schema: **`references/matrices.md`** and **`references/analysis-format.md`**.

### 6. Check it before you draw it

```bash
python3 "$SKILL/scripts/check_analysis.py" --analysis "$OUT/analysis.json" \
    --metrics "$OUT/metrics.json"
```

This is the cheapest quality gate in the pipeline and the one that makes "data
backed" mean something: it recomputes every metric-bound coordinate and fails
on any that has drifted. It also catches an axis where nobody moves, two
matrices asking the same question, a dot with no evidence, a "nobody is here"
claim about a populated quadrant, and coordinates resting on keywords whose
SERPs barely resolved.

Errors have to be fixed. Warnings are judgement calls — read each one and
either fix it or be able to say why not.

### 7. Build the deliverables

```bash
python3 "$SKILL/scripts/build_workbook.py" --metrics "$OUT/metrics.json" \
    --keywords "$OUT/keywords.json" --serp "$OUT/serp.json" \
    --analysis "$OUT/analysis.json" --out "$OUT/<seed-slug>-serp.xlsx"
python3 "$SKILL/scripts/render_report.py" --analysis "$OUT/analysis.json" \
    --metrics "$OUT/metrics.json" --out "$OUT/<seed-slug>-serp.html"
```

The workbook carries Keywords (the whole universe), SERP results (one row per
keyword per position, with the title Google showed, the title the page carries
and its meta description), Pages, Domains, Clusters, Matrices, a **2x2 charts**
sheet holding a native Excel scatter per matrix, Titles and Sources. The charts
read from the Matrices sheet, so someone who edits a coordinate there moves the
dot — worth saying when you hand it over, because people re-cut workbook charts
in a way they cannot re-cut a picture. Open the report before handing it over: overlapping labels or every
dot in one corner means go back to step 5.

### 8. Hand it over

Lead with the answer, not the file list. What kind of content wins this topic,
which handful of pages own it and what they have in common, which cluster is
underserved and what the evidence for that is, and the one thing in the data
that would surprise them. Then the two file paths. Then, plainly, what was
thin: pages that could not be read, keywords whose SERPs barely resolved, axes
you dropped. An under-populated quadrant and an unread one look identical to a
reader, so name the difference.

## What separates a good map from a bad one

- **Every coordinate is recomputable or quoted.** A metric-bound axis can be
  checked by anyone with the workbook. A judged axis needs the line of copy
  that put the dot there. Anything else is an opinion with a chart around it.
- **Intent comes from the SERP, not the wording.** "Best espresso machine"
  sounds commercial; if Google answers it with nine guides, it is an
  informational SERP and a product page will not rank. `serp_metrics.py` reads
  intent off the page types that actually rank, and the disagreements with the
  wording are a finding in their own right.
- **Axes have to separate.** The digest ranks candidate axes by interquartile
  range for exactly this reason. An axis where everything scores 6-8 is a fact
  about the market, not a way to see it — replace it rather than stretching the
  scores.
- **Pair independent questions.** Commercial pull against content depth works.
  Commercial pull against transactional share does not — they are the same
  measurement, and you get a diagonal.
- **Weight by demand.** A keyword standing for 200 variations is not the same
  finding as one standing for two. Dots are sized by demand mass; use it in the
  reading.
- **Say what you could not read.** Coverage gaps belong in the report and in
  your closing message, not buried.

## Topics that are not consumer products

The pipeline is unchanged; the evidence moves. In B2B software the ranking set
is vendor blogs, comparison sites and docs, published dates are often missing,
and the useful axes are more likely to be who the page is written for and
whether it names competitors. In local and service markets the top ten is
mostly directories and map packs, so domain diversity collapses and the finding
is usually which aggregator to be listed on rather than what to write. In
medical, legal and financial topics the ranking set skews to institutions, and
"why it ranks" is often authorship and citation rather than length. Let the
digest tell you which questions matter; the axis library is a prompt, not a
menu.

## Budgets

| | quick look | standard | deep |
|---|---|---|---|
| keyword universe | 800-1,500 | 4,000-6,000 | 10,000+ |
| SERPs captured | 25-40 | 100 | 200+ |
| search turns | 3-4 | 9-12 | 20+ |
| pages read | ~150 | 400-700 | 1,000+ |
| matrices | 3-4 | 6-8 | 8-10 |
| rough working time | ~8 min | ~25-40 min | 1 hour+ |

Six matrices that separate beat ten that do not. Add more only while each one
changes the picture.

## When things go wrong

| Symptom | What to do |
|---|---|
| Seed has two meanings (autocomplete returns two markets) | Narrow the seed, rerun step 1, and say which meaning you took |
| `dropped_off_topic` is huge | Autocomplete drifted; set `--must-include` to the token that defines the topic |
| Autocomplete returns almost nothing | The seed is too long or too rare — shorten it to the head term and let level 2 find the tail |
| Search returns fewer than 5 results for many keywords | Those queries are too specific to map; note it and lean on the clusters that did resolve |
| `coverage_pct` below 60 | Say so, `WebFetch` the top blocked pages, and keep unreadable pages off the medians |
| One domain holds most of the top 10 everywhere | That is the finding — check whether it is a marketplace or a directory before calling it competition |
| Every keyword lands in one quadrant | The axis is dead; take the next one down the digest's candidate list |
| `check_analysis.py` says a coordinate disagrees with its metric | Take the computed value. It is right and you are remembering |
| The universe is huge but the sample feels repetitive | Lower `--df-ceiling` so near-synonyms of the seed stop anchoring topics |
| Rankings look stale or contradictory | Results are a snapshot of one locale on one day; date the report and say so |
