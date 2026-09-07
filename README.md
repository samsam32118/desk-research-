# desk-research-

Skills for desk research — competitive and market analysis you can run from a
terminal.

## `competitor-landscape`

Give it one company. It maps the market around that company two levels out,
built from what the companies themselves publish: meta titles, meta
descriptions, and the H1/H2/H3 ladder on their marketing pages.

```
level 0   the anchor company            1 company
level 1   its competitors and partners  5-8 companies
level 2   their competitors             3-5 each -> ~25-35 total
```

Out comes an Excel workbook (companies, pages, every heading, matrix
coordinates, market vocabulary, sources) and an HTML report of 2x2 maps —
positioning, offering, buyer, messaging, value, commercial model — with every
dot traceable to the line of copy that put it there.

### Using it

The skill lives in `.claude/skills/competitor-landscape/`, so any Claude Code
session opened in this repo can use it. Just ask:

> map the competitive landscape around cal.com, two levels out, and give me the
> spreadsheet and some 2x2s

To install it elsewhere, copy that folder into `~/.claude/skills/`, or hand
someone the packaged `.skill` file.

### The scripts stand alone

They need nothing but Python 3.8+ — no `pip install`, no openpyxl, no pandas —
so they are usable on their own:

```bash
S=.claude/skills/competitor-landscape/scripts

# what does a company's marketing copy actually say?
python3 $S/scan_site.py stripe.com adyen.com --out data/ --max-pages 8
python3 $S/digest.py --data data/

# who claims a thing, who stays silent — with the heading each hit came from
python3 $S/facets.py --data data/ --terms "self-host,governance"

# turn a scan (plus an analysis.json you wrote) into deliverables
python3 $S/check_analysis.py --analysis analysis.json --data data/
python3 $S/build_workbook.py --data data/ --analysis analysis.json --out map.xlsx
python3 $S/render_report.py --analysis analysis.json --data data/ --out map.html
```

`scan_site.py` probes for the pages that matter (`/alternatives`, `/pricing`)
rather than only following links, mines pricing pages for figures that live
outside headings, honours robots.txt, spaces its requests per site, and never
raises on a bad domain — sites that block or render client-side are recorded in
`notes` with `headings_found: 0` so a gap can never be mistaken for a finding.

### Design notes

- **Copy, not commentary.** Analyst write-ups tell you what a market is; an H1
  tells you what a company decided to say when it had one sentence to win a
  buyer.
- **Evidence per coordinate.** Every position on every 2x2 carries a quote and
  its page. A position nobody can trace is an opinion with a chart around it.
- **Axes have to separate.** An axis where everyone scores 6-8 gets replaced,
  not stretched.
- **Works on companies nobody writes about.** When "X competitors" returns
  nothing, the search is rebuilt from the anchor's own category language. That
  fallback is the point, not a corner case.

Eval prompts and assertions used to test the skill are in
`.claude/skills/competitor-landscape/evals/`.

## `serp-landscape`

Give it one keyword. It finds out what is ranking on Google for that topic and
why, from three layers of evidence:

```
autocomplete   ~5,000 real queries, three levels deep, grouped into ~600 topics
web search     the SERP for ~100 sampled keywords, one per topic
page fetch     every ranking URL read: real title, meta description, H1/H2s,
               word count, published/modified date, schema, page type
```

Out comes an Excel workbook (the whole keyword universe, one row per keyword
per ranking position with the extracted title and meta description, pages,
domains, clusters, matrices, title vocabulary, sources) and an HTML report of
2x2 maps — opportunity, intent, format, depth, freshness, who wins — with dots
sized by the demand behind them.

The axes are computed, not asserted. A matrix binds an axis to a named metric,
and `check_analysis.py` recomputes every bound coordinate and fails on any that
has drifted.

### Using it

```
what's ranking for "espresso machine" and why? go deep on keywords, give me
the spreadsheet and some 2x2s
```

### The scripts stand alone

Python 3.8+, standard library only — no `pip install`, no API key:

```bash
S=.claude/skills/serp-landscape/scripts

# ~5,000 keywords from live autocomplete in about 35 seconds
python3 $S/expand_keywords.py "espresso machine" --target 5000 --sample 100

# paste search results in any of four shapes; it normalises and tracks progress
python3 $S/record_serp.py --ledger batch1.md --out serp.json --targets serp_targets.txt

# read every unique ranking page once
python3 $S/fetch_pages.py --serp serp.json --out pages.jsonl

# intent, clusters, share of voice, and 0-10 axis metrics
python3 $S/serp_metrics.py --serp serp.json --pages pages.jsonl \
    --keywords keywords.json --out metrics.json --digest digest.md

python3 $S/check_analysis.py --analysis analysis.json --metrics metrics.json
python3 $S/build_workbook.py --metrics metrics.json --keywords keywords.json \
    --serp serp.json --analysis analysis.json --out map.xlsx
python3 $S/render_report.py --analysis analysis.json --metrics metrics.json --out map.html
```

### Design notes

- **Autocomplete is free, search is not.** So the keyword universe is thousands
  and the SERPs are a sample — one keyword per topic, each carrying the demand
  mass of the topic it stands for. That is also how the work is really done.
- **Intent comes from the SERP.** "Best espresso machine" sounds commercial; if
  Google answers it with nine guides, it is informational and a product page
  will not rank. The disagreements between wording and SERP are the most
  actionable output of a run.
- **No invented volume.** Autocomplete gives shape, not volume, and the skill
  never pretends otherwise. Where a weight is needed it counts keywords.
- **A blocked page is recorded as blocked.** A page missing from the corpus and
  a page that returned nothing look identical in a chart, and the second
  silently biases every median.

Eval prompts and assertions are in `.claude/skills/serp-landscape/evals/`.
