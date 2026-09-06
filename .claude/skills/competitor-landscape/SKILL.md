---
name: competitor-landscape
description: Map a company's competitive landscape out of the words companies use to sell themselves. Give it one company name or domain; it finds competitors and adjacent players two levels deep with web search, pulls each site's meta title, meta description and H1/H2/H3 copy from the home, product, solutions and pricing pages, then delivers an Excel workbook plus a set of 2x2 maps placing every company on positioning, offering, messaging and value. Use this whenever someone mentions competitors, competitive or market analysis, landscape or category mapping, positioning or messaging comparison, "who else does this", alternatives to a product, market whitespace, or asks for a 2x2 or quadrant chart of companies — including when they hand over nothing but a domain and ask what the market around it looks like.
---

# Competitor landscape

One company goes in. A map of its market comes out, built from what the
companies themselves publish: meta titles, meta descriptions, and the H1/H2/H3
ladder on their marketing pages.

That source matters. Analyst summaries tell you what a market is; a homepage
H1 tells you what a company decided to say when it had one sentence to win a
buyer. Marketing pages are where companies spend real effort deciding who they
are for and what they claim, so the copy is the most honest available record of
stated positioning. Everything downstream — every axis, every dot on every 2x2
— has to trace back to a line of that copy. A position nobody can trace is just
an opinion with a chart around it.

## Shape of the work

```
level 0   the anchor company            1 company
level 1   its competitors and partners  5-8 companies
level 2   their competitors             3-5 each, deduped -> ~25-35 total
          |
          v  scan every site: meta + H1/H2/H3 from product, solutions, pricing
          v  write analysis.json: profiles + 2x2 axes + scored positions
          v  workbook.xlsx + report.html
```

Two levels is the point: level 1 tells you who you fight, level 2 tells you what
the market believes. Stop at level 1 only if the user asks for speed.

## Before you start

Settle these in one pass — pick sensible defaults and say what you picked
rather than stalling on questions:

- **Which company.** A name like "Blixon" can match several unrelated firms.
  Search it first. If more than one real company answers and the user gave a
  name rather than a domain, ask — this is the one question worth blocking on,
  because picking the wrong company makes every later step wrong. A domain
  settles it, so prefer one.
- **Depth.** Default 2. Level 1 only if they want it fast.
- **Where the output goes.** Default a new folder `<company>-landscape/` in the
  working directory.

Then tell them roughly what to expect: 25-35 companies, a few hundred pages
read, several minutes of work, two files at the end.

## Pipeline

The scripts live next to this file, and you are running from the user's
directory, so set the path once:

```bash
SKILL=<absolute path to the directory holding this SKILL.md>
OUT=<company>-landscape
```

### 1. Profile the anchor first

```bash
mkdir -p "$OUT/data"
python3 "$SKILL/scripts/scan_site.py" <domain> --out "$OUT/data" --max-pages 10
python3 "$SKILL/scripts/digest.py" --data "$OUT/data"
```

Read the digest before searching for anyone else. The anchor's own words give
you the category nouns ("spend management", "field service platform"), the
buyer ("for finance teams"), and the geography you will search with. Searching
before you read this produces generic results.

If the scan reports no headings — parked domain, JS-only site, bot blocking —
do not push on quietly. Try `WebFetch` on the homepage, and if that also comes
back empty, say so and build the category from search results instead.

### 2. Find level 1: 5-8 companies

Full query ladder, exclusion lists and dedupe rules: **`references/discovery.md`**.
The short version, in order of precision:

1. The anchor's own comparison pages — `scan_site.py` reports these as
   `named_competitors` and `signal_urls.compare`. A company naming a rival on
   its own site is the highest-confidence signal available.
2. `"<company>" competitors`, `"<company>" alternatives`, `<company> vs`.
3. **When 1 and 2 come back empty — which is normal for small or young
   companies — build the search from the anchor's own copy instead:**
   `best <category> software`, `<category> platform for <buyer>`,
   `<category> companies <country>`. This is the fallback that makes the skill
   work on companies nobody has written about yet.
4. Directory and review-site category pages (G2, Capterra, industry press) —
   read them for *names*, never count them as companies.

Fire these searches concurrently rather than one at a time — several queries in
one turn, then read the results together. Discovery is where the wall-clock
time goes, and the queries do not depend on each other.

Keep partners and adjacent players, not just head-to-head rivals: a market map
that only holds direct substitutes misses where the category is drifting. Mark
which is which in `discovered_via`.

Record every company in `$OUT/roster.json` as you go:

```json
[{"domain": "acme.com", "name": "Acme", "level": 1,
  "discovered_via": "search: \"blixon alternatives\"", "parent": ""}]
```

### 3. Expand to level 2

Run the same ladder against each level-1 company, but shallower — one or two
searches plus their comparison pages, 3-5 names each. Dedupe against everything
already in the roster. Cap the total at ~35; past that you are paying for pages
that will not change a single axis.

### 4. Scan every site in one batch

```bash
# one domain per line, everything in the roster except what you already scanned
python3 "$SKILL/scripts/scan_site.py" $(cat "$OUT/domains.txt") \
    --out "$OUT/data" --max-pages 8 --workers 6
```

One call, all domains — it scans sites in parallel while staying polite to each
one (robots.txt honoured, requests spaced). Do not fetch these pages into
context yourself: the script keeps the corpus faithful and cheap, and you need
the context budget for thinking, not for HTML.

Details of what it extracts, the flags that matter, and what to do about sites
that block: **`references/extraction.md`**.

### 5. Read the corpus, then write `analysis.json`

```bash
python3 "$SKILL/scripts/digest.py" --data "$OUT/data" \
    --roster "$OUT/roster.json" --out "$OUT/digest.md"
```

If the user wants to see the raw table before you interpret anything, you can
build the workbook now — `build_workbook.py` runs fine without `--analysis` and
produces everything except the Matrices sheet. Re-run it after the analysis to
fill that in.

The digest ends with a vocabulary table showing how many sites use each term.
Read it carefully: words most of the market uses are table stakes and make
terrible axes; words one or two companies own are where the differentiation is.

Now write `$OUT/analysis.json` — company profiles, then the matrices. How to
choose axes that actually separate companies, how to score positions
consistently, and the full file schema: **`references/matrices.md`** and
**`references/analysis-format.md`**. Read both before writing the file.

Skeleton:

```json
{
  "anchor": {"id": "blixon", "name": "Blixon", "domain": "blixon.com"},
  "market_definition": "what this market is, in the companies' own words",
  "companies": [{"id": "acme", "name": "Acme", "domain": "acme.com", "level": 1,
                 "discovered_via": "...", "one_liner": "...", "icp": "...",
                 "pricing_model": "...", "positioning": "..."}],
  "matrices": [{"id": "wedge", "title": "...", "why_it_matters": "...",
                "x": {"label": "...", "low": "...", "high": "..."},
                "y": {"label": "...", "low": "...", "high": "..."},
                "quadrants": {"tl": "...", "tr": "...", "bl": "...", "br": "..."},
                "points": [{"company": "acme", "x": 7.5, "y": 3.0,
                            "evidence": "H1 on /pricing: '...'"}],
                "reading": "clusters, white space, where the anchor sits"}],
  "takeaways": ["..."]
}
```

Before rendering anything, check it:

```bash
python3 "$SKILL/scripts/check_analysis.py" --analysis "$OUT/analysis.json" --data "$OUT/data"
```

It catches what JSON hides but a chart exposes: an axis where nobody moves, two
matrices secretly asking the same question, a coordinate with no evidence, the
anchor missing from its own map. Errors have to be fixed. Warnings are
judgement calls — read each one and either fix it or be able to say why not.

### 6. Build the deliverables

```bash
python3 "$SKILL/scripts/build_workbook.py" --data "$OUT/data" \
    --analysis "$OUT/analysis.json" --out "$OUT/<company>-landscape.xlsx"
python3 "$SKILL/scripts/render_report.py" --analysis "$OUT/analysis.json" \
    --data "$OUT/data" --out "$OUT/<company>-landscape.html"
```

The workbook carries Companies, Pages, Headings, Matrices, Vocabulary and
Sources sheets — the Headings sheet is long-format so it pivots. The report
renders each 2x2 as a chart with the evidence on hover. Open the report to
check it before handing it over; overlapping labels or an axis where every dot
sits in one corner means go back to step 5.

### 7. Hand it over

Lead with the answer, not the file list: where the anchor sits, which quadrant
is crowded, which is empty, and the one thing in the data that would surprise
them. Then the two file paths. Then, plainly, what was thin — sites that
returned no copy, companies you could not verify, axes you dropped for lack of
evidence. A landscape that hides its gaps invites someone to over-trust it.

## What separates a good map from a bad one

- **Every position carries its evidence.** If you cannot quote the line of copy
  that put a company at x=8, you guessed. Guessing is fine as a hypothesis;
  shipping it as a coordinate is not.
- **Axes have to separate.** An axis where everyone scores 6-8 tells the reader
  nothing. Anchor each axis to its two extreme companies in the corpus first,
  then place everyone relative to them, and throw the axis out if the spread
  collapses.
- **Name axes in the market's language.** "Self-serve vs. procurement-led"
  beats "Ease of adoption" because it is falsifiable from a pricing page.
- **Companies, not directories.** G2, Crunchbase, LinkedIn and press outlets
  are sources. They never get a dot.
- **Say what you could not get.** Coverage gaps belong in the report and in
  your closing message, not buried.

## Markets that are not software

The pipeline is the same; the evidence moves. Manufacturers, industrial firms,
agencies and service businesses put their positioning on capabilities,
industries, certifications and process pages rather than product and pricing
pages, and most publish no price at all. Do not read a missing pricing page as
a missing signal — in those markets, quote-only pricing is the norm, and the
axis that separates companies is more likely to be scope of service,
accreditation, or geography served. Let the corpus tell you which questions
matter; the axis library in `references/matrices.md` is a prompt, not a menu.

## Budgets

| | level 1 only | level 2 (default) |
|---|---|---|
| companies | 6-9 | 25-35 |
| pages scanned | ~60 | ~250 |
| max pages per site | 8-10 | 8 |
| matrices | 4-6 | 6-10 |

Six matrices that separate companies beat ten that do not. Add more only while
each new one changes the picture.

## When things go wrong

| Symptom | What to do |
|---|---|
| Anchor name matches several companies | Search it, list the real candidates, ask which — or use the domain the user gave |
| Anchor site parked, JS-only, or blocking | `WebFetch` the homepage; if still empty, build the category from search and say the copy was unavailable |
| No competitor lists exist for the anchor | Fall back to category search built from the anchor's own copy (step 2, item 3) |
| A site returns 403 or an "agent version" | `scan_site.py` notes it; re-run that one domain with `--user-agent`, or `WebFetch` its key pages |
| Level 2 explodes past 35 companies | Keep the ones named most often across level-1 comparison pages; drop the rest and say so |
| Every company lands in one quadrant | The axis is dead — replace it, do not stretch the scores |
