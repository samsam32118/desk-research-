# Building 2x2s that say something

A 2x2 is a claim: *these two questions are the ones that separate this market,
and here is who answers them how.* Most 2x2s fail because the axes were chosen
before the data was read, so every dot lands in a diagonal smear and the reader
learns nothing they did not already believe.

## Contents

- [Choose axes from the corpus](#choose-axes-from-the-corpus)
- [Axis library](#axis-library) — a prompt, not a menu to copy
- [Scoring](#scoring)
- [Evidence](#evidence)
- [Choosing the set](#choosing-the-set)
- [Writing the reading](#writing-the-reading)
- [Failure modes](#failure-modes)

## Choose axes from the corpus

Read the digest and its vocabulary table first, then ask what actually varies:

- Which words does nearly every site use? Those are table stakes. "AI-powered"
  on twenty of twenty-five homepages cannot be an axis — nobody moves.
- Which words does one company own? That is a candidate pole.
- Where do companies contradict each other? One says "no implementation
  needed", another sells a 12-week onboarding. That disagreement is an axis.
- What did you notice that you did not expect? Surprise is a good axis detector.

Then name the axis in the market's own language. "Self-serve signup vs.
procurement-led" is falsifiable from a pricing page; "Ease of adoption" is not.

## Axis library

Use these to prompt your own thinking, not as a checklist. Each names the
evidence that scores it, because an axis you cannot evidence is an axis you
cannot defend.

| Axis | Low pole | High pole | Read it from |
|---|---|---|---|
| Scope of promise | one workflow | end-to-end platform | H1 nouns; how many product pages |
| Buyer seniority | practitioner | executive / procurement | CTA text, "for teams" vs "for CFOs" |
| Segment | SMB / individual | enterprise | logos, compliance and security language, seat minimums |
| Price transparency | contact sales | published price | pricing page, or its absence |
| Value framing | saves time and effort | makes or saves money | verbs in H1 and meta description |
| Specialisation | horizontal, any industry | one vertical | industries pages, industry nouns in headings |
| Proof style | adjectives and claims | numbers, named customers, certifications | H2s, stat blocks |
| Delivery | pure software | software plus service | "managed", "done for you", implementation pages |
| Time to value | project with onboarding | instant self-serve | CTA text, onboarding language |
| Configurability | opinionated and turnkey | API-first and configurable | developer language on marketing pages |
| AI posture | AI as a feature | AI as the product | where AI appears — a bullet or the H1 |
| Category stance | enters an existing category | invents a new noun | does the H1 use the market's word or their own |
| Geography | one country or region | global | locale pages, currency, "worldwide" claims |

Good pairs put two *independent* questions on the same chart. Scope against
value framing works. Segment against price transparency does not — they measure
nearly the same thing, and you will get a diagonal.

## Scoring

Anchor the poles before you score anyone:

1. Find the most extreme company in the corpus for each end. Give them 9 and 1.
2. Place everyone else relative to those two, not against an abstract ideal.
3. Use the whole 0-10 range. If your scores cluster in 4-7, you are hedging.
4. Check the spread. If the gap between highest and lowest is under 4 points,
   the axis does not separate this market — replace it. Do not stretch scores to
   rescue an axis you like.

Score what the company *says*, not what you believe is true. This is a map of
stated positioning. If a company claims enterprise readiness with no evidence,
it still scores as enterprise-positioned — and that gap between claim and proof
is worth a sentence in the reading.

## Evidence

Every point carries an `evidence` string: a short quote plus where it came
from.

Good: `"H1 on /pricing: 'Start free, upgrade when you outgrow it'"`
Bad: `"self-serve oriented"`

The report shows this on hover, so a reader who disagrees can check you in one
move. If you cannot produce a quote for a coordinate, you inferred it — either
go read that company's pricing page properly, or leave them off that matrix and
say why in the reading.

## Choosing the set

Six matrices by default, up to ten for a rich market. Cover different families
so the set is not one idea wearing hats:

- **positioning** — what they claim to be
- **offering** — what they actually sell, and how much of it
- **buyer** — who they say it is for
- **messaging** — how they argue, what proof they use
- **value** — what outcome they promise
- **commercial** — how they ask to be bought

Before you keep an axis, check it against the ones you already have: if two
matrices rank the companies in nearly the same order, they are one axis drawn
twice. Keep the one with better evidence.

The anchor appears on every matrix. It is the reason the map exists.

## Writing the reading

Two to four sentences per matrix, answering: where are the clusters, which
quadrant is empty, and where does the anchor sit relative to both. Name
companies. "Three of the five cluster in the top right" is a description;
"Everyone claiming the platform story also hides their pricing, which leaves
published-price-plus-platform empty" is a finding.

The empty quadrant deserves a sentence of scepticism as well as excitement.
Sometimes it is white space; sometimes it is empty because that combination
does not sell. Say which you think it is.

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| All dots on a diagonal | The two axes measure the same thing | Replace one with an independent question |
| Everyone in one quadrant | Axis does not separate, or poles are badly placed | Re-anchor to the extremes, or drop the axis |
| Axes named "High/Low" | The axis has no content | Name the poles in the market's words |
| Anchor missing from a matrix | Scoring dodge | Score it or drop the matrix |
| Evidence reads like a summary | Position was inferred, not read | Go back to the copy and quote it |
| Ten matrices, six insights | Padding | Cut to the ones that changed your mind |
