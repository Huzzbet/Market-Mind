# Market Mind Daily Edition

## Purpose
A dated, source-backed daily intelligence edition, designed for the mobile swipe feed. This format is distinct from the deterministic scanner endpoint and does not imply real-time quotes.

## Sections
- **Pulse:** global overnight and local market context.
- **ASX:** ranked research candidates.
- **US:** ranked US research candidates.
- **Rotation:** relative sector strength and weakness.
- **Macro:** rates, currencies, commodities, policy and events.
- **Risk:** risk signals, adverse catalysts and thesis warnings.
- **Watchlist:** follow-up items and conditional setups.

## Card standards
Every opportunity card includes:
- a 0–100 **research priority score**, not a probability, return forecast or recommendation;
- evidence and data points, with data timestamps;
- catalyst or reason for attention;
- key risks and an explicit invalidation condition;
- source name and source link.

Scores must be explainable and must not be represented as machine-learning probabilities. Distinguish reported facts, scanner observations and analyst interpretation. Avoid unsupported valuation claims and stale prices. Missing data should be stated, not filled in.

## Publishing
The daily-edition contract lives at `data/daily/edition.schema.json`. The initial `edition.json` is a clean empty shell. The scheduled ChatGPT morning brief currently delivers to ChatGPT and does not yet publish automatically to this repository. Automatic publication requires a separately configured and permissioned GitHub publishing workflow.

## Data caveats
Prototype market data is sourced from Yahoo Finance chart endpoints. Quotes may be delayed, incomplete, adjusted, or rate-limited. Validate licensing, corporate actions and data quality before investment or commercial use.
