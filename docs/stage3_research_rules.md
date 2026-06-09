# Stage 3 Research Rules

## Valid Research Packet

A valid packet must contain at least:

- 1 bull fact
- 1 bear fact
- 1 neutral fact
- 1 thesis-supporting fact
- 1 thesis-challenging fact
- 1 missing data item
- 1 cited source
- 0 forbidden recommendation-language hits

## Lint Scope

Forbidden-language lint applies only to:

- `research_packets.summary_text`
- `research_facts.fact_text`
- `macro_context_packets.summary_text`

It does not apply to source titles, field labels, fixed report disclaimers, CLI help text, docs, or QA failure explanations.

## Forbidden Output

Stage 3 research must not include buy/sell recommendations, position sizing, target price conclusions, fair value conclusions, order instructions, or approval language.
