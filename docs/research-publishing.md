# Market Mind editorial research publishing

## Architecture

Market Mind has two distinct intelligence layers:

1. **Editorial research** — human/assistant-authored analysis, source-checked and published to `data/research/latest.json`.
2. **Scanner signals** — deterministic observations from `/api/mind`. These are prompts for further research, not conclusions or recommendations.

The scanner does not write editorial research and does not generate investment theses.

## Publish a research card

Add a card to the `cards` array in `data/research/latest.json`, validate it against `data/research/card.schema.json`, then commit it to the deployed branch.

Each card should explain:
- What happened, with a primary source and publication timestamp.
- What the market may be missing or mispricing.
- Why the development matters for earnings, cash flows, valuation or risk.
- The investment angle, including catalysts, risks and what would invalidate the thesis.
- What to watch next.

Use concise, evidence-led writing. Distinguish reported facts, sourced data and analytical judgement. Include a source URL and source publication time for every factual story. If either is unavailable, do not present the item as a verified news card.

## Card fields

- `tag`: category, e.g. `THE OPPORTUNITY`, `THE ROTATION`, `THE SIGNAL`, `DEEP DIVE`.
- `time`: short display label.
- `title`, `dek`: headline and short summary.
- `data`: up to four label/value pairs.
- `insight`: core analysis.
- `whyItMatters`: transmission to earnings, valuation, capital allocation or risk.
- `investmentOpportunity`: balanced research angle, catalysts, risks and invalidation.
- `source`, `sourcePublishedAt`, `link`: attribution.
- `rank`: editorial ordering only; not a probability or expected return.

## Quality controls

- Never invent a price, broker target, consensus revision, institutional flow or probability.
- Avoid unsupported claims about what "the market" expects.
- Do not call a company cheap without a defensible valuation framework and assumptions.
- Include the bear case and thesis invalidation.
- Flag stale, delayed or incomplete data.
- Do not present research as personal financial advice.
- Keep unsuccessful ideas in the historical record; do not silently delete them.

## Display

The app loads editorial cards from `/data/research/latest.json` and places them before scanner signals and the existing daily feed. If the file is empty or unavailable, the existing feed continues to work.
