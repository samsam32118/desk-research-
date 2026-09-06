# Reading a company's copy

`scan_site.py` does the collecting. This is what it takes, what it deliberately
ignores, and what to do when a site does not cooperate.

## What it collects

Per page: meta title, meta description, og:title, og:description, canonical
URL, every H1/H2/H3 in document order, call-to-action button text, and a word
count. Per site: the brand name, the pages it chose, comparison and partner
URLs it noticed, competitor names parsed off comparison pages, and a `notes`
list of everything that went wrong.

It picks pages by type, capped so one section cannot crowd out the rest:
home, pricing, product, platform, solutions, use cases, industries, features,
comparison, about. It scores top-level paths above deep ones, because
positioning lives near the root — `/pricing` is the pricing page, and
`/method/product-direction` is an essay.

It skips blog, news, press, careers, legal, docs, support, help, login,
webinars, resources, case studies, integrations directories, and non-English
locale trees. Those pages are written for different readers and dilute the
signal you are trying to compare. `--include-case-studies` brings customer
stories back if you specifically want proof points.

## Running it

```bash
# one company, deeper
python3 scripts/scan_site.py blixon.com --out data/ --max-pages 12

# the whole roster in one call (parallel across sites, polite within each)
python3 scripts/scan_site.py $(cat domains.txt) --out data/ --max-pages 8 --workers 6
```

Useful flags:

| Flag | Why |
|---|---|
| `--max-pages N` | Pages per site including the homepage. 8 is plenty for level 2; 10-12 for the anchor. |
| `--workers N` | Sites scanned in parallel. 6 is comfortable; each site is still rate-limited on its own. |
| `--user-agent "..."` | Retry a site that served a stripped or agent-specific page. |
| `--ignore-robots` | Off by default and should stay off unless the user owns the site. |
| `--delay S` | Seconds between requests to one site. Raise it if a site starts throttling. |

Requests default to a browser user-agent, honour robots.txt, and are spaced per
site. It never raises on a bad site — failures land in `notes` so a single dead
domain cannot cost you the run.

## Do not read the raw JSON in bulk

Thirty scan files will eat the context you need for thinking, and most of it is
repetition. Use the digest:

```bash
python3 scripts/digest.py --data data/ --roster roster.json --out digest.md
```

It prints the strongest signal per company plus a vocabulary table across the
whole corpus. Open an individual JSON only when you need a specific company's
detail — checking a pricing page's exact H2s before scoring an axis, say.

## When a site does not cooperate

Check `notes` and `headings_found` on every scan before trusting it.

**`headings_found: 0`** — the site is JS-rendered, parked, or blocking. Open
the scan file before doing anything else: the meta title and description are
often still there, because they sit in the HTML head even when the body renders
client-side. That is real, verbatim evidence and it costs nothing. Only when
those are empty too, fall back to `WebFetch` for that one domain:

```
WebFetch(url="https://example.com/",
         prompt="Give the exact meta title, meta description, H1, and every H2
                 in order. Quote them verbatim, do not summarise.")
```

Verbatim matters. A summarised H1 cannot be used as evidence for a coordinate.

**"served an agent/machine version"** — the site detected automation and
returned a stripped page. Re-run that domain with `--user-agent`, or use
`WebFetch`. The content may still be usable; it just is not the copy a buyer
sees, so note it.

**HTTP 403 or 429** — raise `--delay` and retry that domain alone. If it stays
blocked, use `WebFetch` and record the gap.

**The scan returns the wrong company.** A platform vendor scanned by root
domain gives you corporate copy: `paloaltonetworks.com` returns "Control the
chaos. Secure every identity.", not Cortex XSOAR. The page-scoring heuristic is
right for a single-product company and wrong here. Rescan with the product URL —
`scan_site.py paloaltonetworks.com/cortex/cortex-xsoar` — which scopes discovery
to that subtree. Use `--also-urls` to add specific pages discovery missed.

**A site defeats every method.** Some sites (Hexagon, Motorola Solutions, Coupa,
JAGGAER) sit behind protection that neither the scanner nor `WebFetch` gets
past. That is a coverage class, not a bug. Keep the company in the workbook with
the gap flagged, keep it off the matrices, and name it when you hand over — an
under-populated quadrant looks exactly like whitespace to a reader who does not
know a real competitor is missing from it.

**Homepage unreachable** — the scanner already retried with and without `www`.
Check whether the company still exists; a dead domain is itself a finding, and
belongs in the report rather than being silently dropped.

## Reading the output

```json
{
  "domain": "acme.com", "name": "Acme", "reachable": true, "headings_found": 63,
  "pages": [{"page_type": "home", "final_url": "...", "title": "...",
             "meta_description": "...", "h1": ["..."], "h2": ["..."],
             "h3": ["..."], "ctas": ["Book a demo"], "word_count": 812,
             "price_signals": ["$23 per user", "free forever"]}],
  "signal_urls": {"compare": ["..."], "partners": ["..."]},
  "named_competitors": ["Globex", "Initech"],
  "probes": {"/pricing": 404, "/plans": 404, "/alternatives": 200},
  "candidates_found": 12,
  "notes": ["..."]
}
```

Three things worth reading closely every time:

- **The homepage H1 and meta description together.** The H1 is what they say to
  a visitor; the meta description is what they say to someone still choosing a
  tab. Where those diverge, the company is unsure who it is for.
- **The pricing page and `price_signals`.** Note it is a **per-page** field —
  `pages[].price_signals`, not a site-level key — so gather it across pages
  before concluding a company publishes nothing.
  Prices live in divs and tables, not
  headings, so the scanner mines the visible text of pricing pages for figures
  and phrases ("$23 per user", "contact sales", "free forever"). When no pricing
  page turns up in discovery, it probes `/pricing`, `/plans`, `/pricing-plans`
  and `/price` and records the result, so `notes` distinguishes "this company
  publishes no price" — a finding — from "we did not look".
- **CTA text.** "Book a demo" and "Start free" are different businesses.
