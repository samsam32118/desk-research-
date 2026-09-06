# Finding the companies

The map is only as good as the roster. This is how to build one that a person
who knows the market would recognise.

## Contents

- [The ladder](#the-ladder) — query patterns in order of precision
- [When the anchor is unknown](#when-the-anchor-is-unknown) — the fallback that matters most
- [Level 2](#level-2)
- [Who counts as a company](#who-counts-as-a-company) — exclusions
- [Dedupe](#dedupe)
- [roster.json](#rosterjson)

## The ladder

Work down it and stop when you have 5-8 solid level-1 names. Precision falls as
you descend, so spend the early steps properly.

**0. Trust the site over the coverage.** When search results and a company's
own pages disagree about what it does, the site wins. For young companies the
normal failure is stale-but-recent press: riff.ai's own Series A coverage
describes an enterprise vibe-coding product it has since pivoted away from, and
building the roster from that would have produced an entirely wrong market. Read
the anchor's copy first, and treat anything search tells you that contradicts it
as history.

**1. The anchor's own comparison pages.** `scan_site.py` surfaces these as
`named_competitors` (parsed from `/compare/x-vs-y`, `/alternatives/x`, and
"vs X" headings) and `signal_urls.compare`. It also probes `/alternatives`,
`/compare`, `/competitors` and `/vs` directly, because a site with thousands of
generated pages can bury its own competitor index.

**When `signal_urls.compare` contains an index page, open it.** `named_competitors`
is parsed from URLs and headings the crawl happened to reach, so it under-reports:
on atlas.co it returned 14 names while the index itself listed 46, grouped under
the segments Atlas uses to describe its own market. That page is the single
richest artifact in this whole pipeline — one fetch, and the level-1 roster is
done before you run a search. A company that publishes a page
arguing it beats Acme has told you Acme is a competitor. Nothing beats that for
precision — start here, and fetch one or two of those pages if the names are
thin.

**2. Direct search.** Run these as separate queries; they surface different
lists:

```
"<company>" competitors
"<company>" alternatives
<company> vs
best alternatives to <company> <year>
<company> competitors <country>        # when the anchor is regional
```

**3. Category search built from the anchor's own copy.** Take the category noun
from the anchor's H1 or meta title — "spend management", "field service
software", "2G ethanol production" — and the buyer from its subheads:

```
best <category> software
<category> platform for <buyer>
top <category> companies <country>
<category> vendors <industry>
leading <category> suppliers
```

**4. Directory and review-site rosters.** G2, Capterra, TrustRadius, Software
Advice, Gartner category pages, trade-press "top 10" lists, industry
association member lists. Mine them for names. They are sources, never dots.

**5. Adjacency sweep.** One query for who sits next to the category rather than
inside it: `<category> vs <adjacent category>`, `<category> integrations`,
partner and marketplace pages (`signal_urls.partners`, `signal_urls.integrations`).
Partners and adjacent players belong on the map — they show where the category
is drifting and who might enter it. Label them in `discovered_via` so the
distinction survives into the workbook.

## When the anchor is unknown

Small, young, or regional companies have no "X alternatives" listicles. Steps 1
and 2 return nothing, and that is not a failure state — it is the normal case
this skill was built for. Step 3 carries the whole thing:

1. Read the anchor's digest. Write down the category noun, the buyer, the
   geography, and two or three claims it makes.
2. Search each of those as a category, not as a brand.
3. For each result, open the site and check it sells to the same buyer with a
   similar promise. A company sharing a keyword but selling to a different buyer
   is not a competitor; note it as adjacent or drop it.

If even the category is unclear because the anchor's site gave no copy, say so
plainly in the final message. A map built on a guessed category is worse than
no map, because the reader cannot see the guess.

## Level 2

For each level-1 company, one or two searches (`"<company>" competitors`,
`"<company>" alternatives`) plus its own comparison pages. Take 3-5 names each,
dedupe against the roster, and record the parent in `discovered_via`
("competitor of Acme").

Level 2 exists to reveal the shape of the market, so favour names that appear
across *several* level-1 companies' lists — repeated appearance is a market
telling you who matters. Cap the total roster at ~35.

## Who counts as a company

Include: operating companies with their own website that sell to a
recognisably similar buyer. Direct substitutes, adjacent players, partners,
and regional equivalents all earn a dot as long as their level and
`discovered_via` say what they are.

Exclude, always:

- Directories and review sites: g2, capterra, trustradius, softwareadvice,
  getapp, gartner, forrester, crunchbase, tracxn, owler, zoominfo, pitchbook,
  builtwith, similarweb
- Social and community: linkedin, facebook, x/twitter, reddit, quora, youtube,
  medium, substack, producthunt, wikipedia
- Press and job boards: trade publications, news sites, indeed, glassdoor
- Consultancies and agencies writing *about* the category rather than selling
  into it — unless the anchor is itself an agency
- The anchor, and anything that redirects to the anchor's domain

A quick test: would this organisation show up on a buyer's shortlist? If it
would only show up in their browser history while researching, it is a source.

## Dedupe

Check all four; each catches a different duplicate:

- **Registrable domain** — `acme.com` and `www.acme.com` are one company.
- **Redirects** — after scanning, compare `final_url`. A rebrand or acquisition
  shows up as two roster entries pointing at one site.
- **Parent and subsidiary** — same product under two brands is one dot with the
  parent recorded, unless they genuinely sell to different buyers, in which case
  keep both and say why.
- **Country sites** — `acme.de` and `acme.com` are one company.

## roster.json

Keep this current as you discover; it is the provenance trail that reaches the
workbook.

```json
[
  {"domain": "blixon.com", "name": "Blixon", "level": 0,
   "discovered_via": "anchor", "parent": ""},
  {"domain": "acme.com", "name": "Acme", "level": 1,
   "discovered_via": "named on blixon.com/compare/acme", "parent": ""},
  {"domain": "widgetco.io", "name": "WidgetCo", "level": 2,
   "discovered_via": "search: \"acme alternatives\"", "parent": "acme.com"}
]
```

`digest.py --roster` uses it to order and label the brief; the same fields go
into `analysis.json` and end up as columns in the workbook.
