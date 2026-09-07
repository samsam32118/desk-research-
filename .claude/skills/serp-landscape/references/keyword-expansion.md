# Building the keyword universe

The map is only as good as the demand behind it. This is how to get from one
seed to thousands of queries a real person typed, and how to spot when the
expansion has gone somewhere you did not intend.

## Contents

- [Why autocomplete](#why-autocomplete)
- [The four sources](#the-four-sources)
- [How the probes work](#how-the-probes-work)
- [Going deeper](#going-deeper)
- [Topics and demand mass](#topics-and-demand-mass)
- [Choosing the SERP sample](#choosing-the-serp-sample)
- [Drift, and the token that stops it](#drift-and-the-token-that-stops-it)
- [Locales and non-English seeds](#locales-and-non-english-seeds)
- [Flags worth knowing](#flags-worth-knowing)

## Why autocomplete

A suggestion list is not a guess about demand — it is a record of queries
people actually completed, served by the engine itself, free, and without an
API key. It gives you no volume number, and pretending otherwise would be the
one dishonest thing in this pipeline. What it does give you is shape: which
questions exist, how they are phrased, and how they branch. Volume is what
paid tools sell; shape is what decides what you write.

Where the skill needs a weight, it uses **demand mass** — how many keywords in
the universe cluster around a topic — and says so. That is a real, countable
quantity from this corpus, not a smuggled volume estimate.

## The four sources

| source | per call | extras | overlap with Google web |
|---|---|---|---|
| `google` (`client=chrome`) | 15 | relevance scores, suggest subtypes | — |
| `youtube` (`ds=yt`) | 10 | video-intent phrasing | ~50% — genuinely different |
| `ddg` | 8 | — | ~60% |
| `bing` | 13 | — | ~70% |

Default is `google` alone, and for most runs that is right. Add `youtube` when
the topic has a demonstrable or visual half — repairs, recipes, techniques,
software walkthroughs — because it surfaces "how to descale...", "...not
working" phrasings that web autocomplete ranks lower. `ddg` and `bing` mostly
return subsets of Google; use them to corroborate a surprising keyword rather
than to pad the list, and remember every extra source multiplies the call
count.

## How the probes work

Autocomplete completes a *prefix*, so every probe is the seed plus a shape, and
the shapes decide which half of the market you see:

```
seed                          espresso machine
question words + seed         how espresso machine, why espresso machine, ...
seed + commercial words       espresso machine best, espresso machine vs, ...
seed + relation words         espresso machine for, espresso machine with, ...
seed + a..z                   espresso machine a, espresso machine b, ...
```

Around 90 probes at level 1. The order matters: the plain seed and the modifier
families run before the alphabet, so a run cut short still has the high-value
shapes rather than `seed a` through `seed f`.

## Going deeper

Completing the seed forever only ever returns the head of the market. Depth is
where the specific, low-competition tail lives, so each deeper level re-probes
keywords that already came back:

```
level 1   ~950 keywords     completions of the seed
level 2   ~2,400 keywords   completions of 150-300 level-1 keywords
level 3   ~1,500 keywords   completions of those
```

Branches are chosen by rotating through distinct modifier shapes rather than by
taking the top N. Ranking by relevance alone digs the same hole deeper: the top
150 completions of one seed are mostly one phrasing, and their completions are
too.

When the universe gets trimmed to `--target`, each level keeps a quota
(roughly 40/35/25 across levels 1-3). Sorting by level instead would put every
deep keyword last and a small target would silently throw away the entire point
of digging.

## Topics and demand mass

Each keyword is filed under its most-shared substantive word: "espresso machine
with grinder" and "does espresso machine come with grinder" both land under
`grinder`. Two guards make that useful:

- **Intent words cannot anchor a topic.** "best", "review", "2026", "reddit"
  describe *how* someone is searching, not what about. Without this guard half
  the universe files under "best" and the clustering tells you nothing.
- **A word used by more than `--df-ceiling` of the universe cannot anchor
  either.** For an "espresso machine" run, "coffee" appears in 8.7% of
  keywords; letting it anchor produced one 423-keyword cluster that meant
  nothing. At the 5% default the largest cluster is 3.6% of the corpus and 92%
  of keywords land in clusters of three or more.

Cluster size is the demand mass that later weights the dots on every 2x2.

This is wording-based grouping, and wording is a proxy for intent, not a
substitute. `serp_metrics.py` regroups the sampled keywords by the URLs Google
actually returns. Where the two disagree, Google wins.

## Choosing the SERP sample

One representative per topic, biggest topic first, then a second from each, and
so on. Spending searches this way spreads them across the demand instead of
piling ten of them on ten phrasings of one question. In a 4,891-keyword run a
120-keyword sample covered 119 distinct topics.

The seed itself is always in the sample. Each sampled keyword carries its
topic's size, so a dot on the map can be weighted by what stands behind it.

## Drift, and the token that stops it

Autocomplete walks away from your seed given half a chance: `how espresso
machine` completes to `how coffee machine`, and `a espresso machine` to `a
coffee machine game`. Left alone, a few hundred off-topic keywords enter the
universe and every downstream number is diluted.

The filter is one token — by default the longest content word in the seed —
that every keyword must contain. For "espresso machine" that is `espresso`,
which keeps "best espresso machine under $500" and drops "coffee machine
game". Dropped keywords are recorded with the reason in `keywords.json`, so
you can check the filter was not too aggressive.

Override it when the seed's defining word is not its longest:
`--must-include crm`. Pass `--must-include -` to keep everything, which is
occasionally right for a very broad seed and usually not.

**When `dropped_off_topic` is large relative to what was kept**, look at the
dropped list before doing anything else. Either the seed is ambiguous, or the
anchor token is wrong.

## Locales and non-English seeds

`--locale en-GB`, `--locale de-DE`, `--locale es-MX`. This sets `hl` and `gl`
on the autocomplete call, and both matter: a UK run returns different
suggestions and different spellings from a US one.

Two things to remember for non-English work. The stopword and intent lexicons
in `expand_keywords.py` are English, so `intent_prior` will mostly come back
`unclassified` — that costs you nothing, because intent is read from the SERP
later anyway and that step is language-independent. And keep the locale
consistent between expansion and search; a German keyword set scored against
US rankings is two datasets pretending to be one.

## Flags worth knowing

| Flag | Why |
|---|---|
| `--target N` | Universe size. 5,000 default; raise it freely, the calls are cheap |
| `--sample N` | Keywords marked for SERP capture. This one decides run length |
| `--depth 1..3` | 1 is seed-only and fast; 3 is the default and where the tail is |
| `--branch N` | Keywords re-probed per deeper level. 300 gets you ~5,000; 400+ for 10,000 |
| `--sources` | `google,youtube` when the topic has a how-to half |
| `--locale` | Autocomplete is locale-specific; match it to the market |
| `--must-include` | The relevance anchor. Set it when the seed's key word is not its longest |
| `--df-ceiling` | Lower it (0.03) if a near-synonym of the seed is swallowing topics |
| `--extra` / `--extra-file` | Keywords you found elsewhere — related searches, People Also Ask, the user's own list. Kept verbatim with `source: manual` |
| `--no-letters` | Skips the a-z round: ~25% fewer calls, noticeably less tail |

`--extra` is worth remembering. If the user hands you a list of keywords they
already care about, feed it in — those keywords join the universe, get
clustered and get sampled alongside everything discovered, instead of living in
a separate conversation.
