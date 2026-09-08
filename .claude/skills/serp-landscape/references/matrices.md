# Building 2x2s that say something

A 2x2 is a claim: *these two questions separate this market, and here is who
answers them how.* Most fail because the axes were chosen before the data was
read, so every dot lands in a diagonal smear and the reader learns nothing.

This skill has an advantage a positioning 2x2 does not: most of the axes worth
drawing are already measured. Use that. An axis bound to a metric can be
checked by anyone with the workbook, and `check_analysis.py` checks it for you.

## Contents

- [Pick axes from the digest](#pick-axes-from-the-digest)
- [The measured axes](#the-measured-axes)
- [Judged axes](#judged-axes)
- [Choosing the set](#choosing-the-set)
- [Evidence](#evidence)
- [Demand mass](#demand-mass)
- [Writing the reading](#writing-the-reading)
- [Failure modes](#failure-modes)

## Pick axes from the digest

`digest.md` ends with candidate axes ranked by interquartile range — how much
each one actually spreads this corpus. Start there rather than from a favourite
framework. An axis with an IQR near zero puts every dot in one band; that is a
fact about the market (everyone writes long, say) and belongs in a sentence,
not on an axis.

Then read three other sections before choosing:

- **Where the wording and the SERP disagree.** Queries that read commercial and
  return guides are the most actionable thing in the whole run, and usually
  deserve an axis of their own.
- **Keyword groups Google answers with the same pages.** Cluster size tells you
  where the mass is; a map that spreads its dots evenly across clusters
  misrepresents the topic.
- **The pages doing the work.** If the top ten pages all share a shape, that
  shape is a pole.

## The measured axes

Bind an axis by naming the metric. Coordinates then come from
`metrics.json` → `axes.<unit>.<metric>.values`, copied verbatim.

**Per keyword** — the unit that answers "which queries should I go after".

| metric | what it measures | reads as |
|---|---|---|
| `commercial_serp` | money pages and buying guides in the top 10 | guides win ↔ product pages win |
| `transactional_serp` | product, category and marketplace pages only | research ↔ ready to buy |
| `informational_serp` | guides, how-tos, Q&A, reference, forums | commercial ↔ explanatory |
| `ugc_share` | forum and community results | publisher-owned ↔ Reddit owns it |
| `video_share` | video results | text answers ↔ needs showing |
| `content_depth` | median word count of ranking pages, log scaled | short answers win ↔ long guides win |
| `freshness` | how recently ranking pages were updated | evergreen ↔ must be current |
| `dated_titles` | ranking titles carrying a year | timeless ↔ dated-title market |
| `listicle_share` | numbered list pages in the top 10 | prose ↔ listicle format |
| `title_match` | how literally ranking titles repeat the query | semantic ↔ exact-match titles |
| `domain_diversity` | distinct domains across the top 10 | one publisher ↔ wide open |
| `incumbent_share` | top 10 held by domains that rank across this corpus | contestable ↔ locked up |
| `demand_mass` | keywords in the universe behind this query, log scaled | niche ↔ large topic |
| `specificity` | words in the query | head term ↔ long tail |
| `question_titles` | ranking titles phrased as a question | statements ↔ questions |

**Per page** — the unit that answers "why does this rank".

| metric | what it measures |
|---|---|
| `keyword_coverage` | sampled keywords the page ranks for |
| `visibility` | position-weighted visibility across the corpus |
| `position_strength` | average position, inverted |
| `depth` | word count, log scaled |
| `freshness` | how recently updated |
| `title_match` | how literally the title repeats the queries it ranks for |
| `structure` | headings, tables and lists — how navigable it is |
| `title_length` | characters in the title tag |

Good pairs put two *independent* questions on one chart. `commercial_serp`
against `content_depth` works. `commercial_serp` against `transactional_serp`
does not — they measure nearly the same thing and you will get a diagonal.
`incumbent_share` against `demand_mass` is the classic opportunity map: big
topics nobody owns are the top-left, and they are usually the reason the user
asked.

Coordinates are filled by `build_points.py`, not typed — see
`references/analysis-format.md`. Your job is choosing the pair and writing what
the chart means.

## Judged axes

Some questions are real and not measured. How a title frames its promise
(feature versus outcome), whether ranking pages sell or explain, whether the
copy speaks to a beginner or a specialist — those need reading, and a judged
axis is the right tool. Leave `metric` out and every point then needs a quote.

Two rules keep judged axes honest. Anchor the poles to the two most extreme
pages in the corpus and score everyone relative to them, not against an
abstract ideal. And score what the copy *says*, not what you believe is true:
this is a map of what ranks, and a thin page that ranks first is a finding, not
an error to correct.

Keep judged axes to a minority of the set. When half the axes are unmeasured,
the deliverable stops being data-backed and starts being an essay with a chart.

## Choosing the set

Six to eight matrices. Mix the units — keyword maps answer "what should I go
after", page maps answer "what do I have to write" — and cover different
families so the set is not one idea wearing hats:

- **opportunity** — demand against how locked-up the SERP is
- **intent** — what Google decided the query means, against how the keyword reads
- **format** — what shape of page wins
- **depth** — how much content it takes
- **freshness** — whether the topic decays
- **who wins** — publishers, vendors, marketplaces, forums
- **craft** — what winning titles and descriptions do (usually the judged one)

Before keeping an axis, check it against the ones you already have. If two
matrices rank the corpus in nearly the same order they are one axis drawn
twice; `check_analysis.py` reports the rank correlation.

A near-diagonal inside one matrix is not automatically a failure. If two or
three keywords break the line they are usually the most interesting thing on
the chart — a high-demand query with a wide-open SERP, say. Keep it and name
them in the reading. Replace it only when nothing breaks the line.

## Evidence

Every point carries an `evidence` string. For a measured axis, cite the number
and what produced it. For a judged axis, quote the copy.

Good: `"8 of 10 results are buying guides; #1 is a 5,985-word listicle titled 'Top 5 Best Espresso Machines with Grinders in 2026'"`
Good: `"median ranking page 3,048 words against a corpus median of 1,134"`
Bad: `"high commercial intent"`

The report shows this on hover, so a reader who disagrees can check you in one
move. If you cannot produce a number or a quote for a coordinate, you inferred
it — go read the record, or leave the point off and say why in the reading.

## Demand mass

Dots are sized by the keywords standing behind them, so a query representing
200 variations reads bigger than one representing two. This changes what a
chart means: three small dots in an empty quadrant is not the same finding as
one enormous one, and a reading that ignores dot size is describing a chart the
reader is not looking at.

Override the default weighting per point with `"size"` when you have a better
measure of importance — a client's priority list, say — and say in
`why_it_matters` what the size means when you do.

## Writing the reading

Two to four sentences per matrix: where the clusters are, which quadrant is
empty, and what someone should do differently because of it. Name keywords and
pages.

"Three of the five cluster top-right" is a description. "Every query where
Google returns guides is also a query where the ranking pages run past 3,000
words, so the short comparison pages this site publishes cannot compete on any
of them" is a finding.

The empty quadrant deserves scepticism as well as excitement. Sometimes it is
an opening; sometimes it is empty because that combination does not work — a
query with big demand and no incumbent is often one Google answers with a map
pack. Say which you think it is, and check the occupancy line
`check_analysis.py` prints before calling anything empty.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| All dots on a diagonal, no exceptions | The two axes measure the same thing | Replace one; take the next independent metric down the digest list |
| A diagonal with two or three off it | Not necessarily broken | Keep it if those outliers are the insight, and name them |
| Everything in one quadrant | Axis does not separate this corpus | Check its IQR in the digest and take a wider one |
| `check_analysis.py` says a coordinate disagrees with its metric | You retyped instead of copying | Take the computed value |
| Evidence reads like a summary | Position was inferred | Go back to the record and quote the number or the copy |
| Half the axes are judged | The measured layer is going unused | Rebuild from the digest's candidate list |
| A quadrant called empty that is not | The reading was written before the scores | Fix the claim or scope it ("empty of vendor pages") |
| Eight matrices, three insights | Padding | Cut to the ones that changed your mind |
