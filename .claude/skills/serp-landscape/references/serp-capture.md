# Capturing the SERPs

This is the only step that costs turns, so it is the only one worth optimising
hard. Everything here is about spending searches well and losing nothing on the
way from the search result into the dataset.

## Contents

- [Batch, always](#batch-always)
- [The ledger](#the-ledger)
- [What counts as position](#what-counts-as-position)
- [Tracking progress](#tracking-progress)
- [When a search comes back thin](#when-a-search-comes-back-thin)
- [Reading the pages](#reading-the-pages)
- [Gaps, and why they must be named](#gaps-and-why-they-must-be-named)
- [Refreshing part of a run](#refreshing-part-of-a-run)

## Batch, always

Issue **8-12 searches in a single turn**, read them together, write one ledger
block, record it, and move to the next batch. The searches do not depend on
each other. Running them one per turn turns a five-minute job into an hour and
produces exactly the same dataset.

A 100-keyword run is therefore about nine to twelve turns of searching. Tell
the user that up front so the wait is expected rather than alarming.

Search the keyword **exactly as it appears** in `serp_targets.txt`. Do not
tidy it, expand it, or add "best" to it — the query is the measurement, and a
rephrased query measures a different SERP.

## The ledger

`record_serp.py` reads four shapes, so use whichever is cheapest for what you
have in front of you. The cheapest is almost always pasting the results array
straight under a heading:

```
## espresso machine for home
[{"title":"Espresso Machines for Home","url":"https://procoffeegear.com/collections/espresso-machines"},{"title":"The Best Espresso Machines","url":"https://coffeechronicler.com/gear/espresso-machines/"}]

## espresso machine with grinder
1. https://www.coffeeness.de/en/best-espresso-machine-with-grinder/ | Top 5 Best Espresso Machines with Grinders in 2026
2. https://www.seattlecoffeegear.com/collections/superautomatic-espresso-machines
- https://coffeebros.com/collections/espresso-machines

{"keyword": "espresso machine vs nespresso", "results": [{"url": "https://...", "title": "..."}]}
```

Headings can be `## keyword`, `keyword:`, or `keyword: <text>`. Result lines
can be numbered, bulleted or bare; a title can follow the URL after `|`, `—`,
` - ` or a tab. Anything that is not a heading and holds no URL is ignored.

Titles are optional. `fetch_pages.py` reads the real `<title>` off every page,
and the gap between the two is itself a finding — where Google rewrote a
title, it is saying the original did not match the query well enough. Include
the SERP titles when you have them and the comparison becomes available; skip
them and nothing else breaks.

## What counts as position

Rank comes from the order you paste, so **keep the order the search returned**.
Ads, People Also Ask boxes and video carousels are not organic positions — if
your search tool surfaces them, leave them out rather than letting them push
the real results down.

The same URL twice in one SERP is one position, and the recorder drops the
duplicate. Tracking parameters are stripped, redirector wrappers are unwrapped,
and trailing slashes are normalised, so the same page counts once across the
whole corpus no matter how it was linked.

## Tracking progress

```bash
python3 scripts/record_serp.py --ledger batch3.md --out serp.json \
    --targets serp_targets.txt
```

With `--targets` it reports `targets_captured`, `targets_missing` and the next
dozen keywords, and writes everything still outstanding to
`serp_targets_remaining.txt`. Work from that file after the first batch. There
is no state to keep in your head, and a long capture can be interrupted and
resumed without losing anything.

Recording a keyword again replaces its results, so re-searching one that came
back wrong is safe and cheap.

## When a search comes back thin

Fewer than five results usually means the query is too specific to be a real
SERP rather than that the search failed. Record what came back — a short SERP
is a signal about the query — and note it. `serp_metrics.py` counts results per
keyword, and `check_analysis.py` warns when a coordinate rests on a keyword
whose results barely resolved.

If a whole batch comes back thin, the sample has run past the point where the
topic has search demand. Stop there and say how far you got; the clusters that
did resolve are worth more than a hundred half-empty SERPs.

## Reading the pages

```bash
python3 scripts/fetch_pages.py --serp serp.json --out pages.jsonl --workers 8
```

Every unique URL is fetched once no matter how many keywords it ranks for — in
a 100-keyword run one guide often ranks for thirty of them. Requests to one
host are spaced a second apart, robots.txt is honoured, and nothing raises on a
bad page.

Per page it extracts: the real title and meta description, og:title and
og:description, canonical, language, the H1/H2/H3 ladder, word count, JSON-LD
`@type` list, published and modified dates, first paragraph, counts of images,
tables and lists, and an inferred page kind (listicle, comparison, how-to,
product, category, marketplace, forum/ugc, video, reference, docs, news,
question/answer, review, faq, homepage).

The page kind comes from three weak signals — URL shape, structured data and
title — that agree often enough to be useful. Two traps worth knowing: Shopify
parks every blog under `/blogs/news/`, which is not news, and `/collections/`
is a category page even when its title reads like a guide. Both are handled,
but if the kind mix looks wrong for a topic you know, open a few records before
building an axis on it.

Useful flags: `--max-rank` to analyse only the top 5, `--limit` to cap total
fetches, `--delay` to slow down for a fragile host, `--refresh` to refetch
pages already recorded.

## Gaps, and why they must be named

Publishers block bots. A run where 70-85% of ranking pages are readable is
normal and good. What matters is that a blocked page is recorded as blocked
rather than dropped: a page missing from the corpus and a page that returned
nothing look identical in a chart, and the second one silently biases every
median.

`fetch_pages.py` writes `pages_blocked.txt` with the domain, status and URL of
everything it could not read. Two rules:

1. **If a blocked page holds a top position across several keywords, spend a
   `WebFetch` on it.** Ask for the exact title, meta description and every H2,
   verbatim — a paraphrase cannot be used as evidence for a coordinate.
2. **Whatever is still unreadable goes in the report by name.** The rendered
   report already lists the blocked domains in its footer; say it in your
   closing message too, because a thin quadrant and an unread one look the same
   to a reader.

`robots.txt disallows` is a different case from `HTTP 403`. The first is a site
asking not to be crawled and should be respected; use `WebFetch` there only if
the page genuinely matters, and never pass `--ignore-robots` unless the user
owns the site.

## Refreshing part of a run

Rankings move. To re-check a subset later, re-search those keywords, record
them into the same `serp.json` (they replace in place), then re-run
`fetch_pages.py` — it skips URLs already in `pages.jsonl` unless you pass
`--refresh`, so only the new pages cost anything. Re-run `serp_metrics.py`
afterwards; every number downstream is derived, so nothing needs editing by
hand.
