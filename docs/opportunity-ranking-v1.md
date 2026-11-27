# Market Mind opportunity ranking v1

The technical scanner now uses a transparent research-priority score (0–100). It is a ranking heuristic, not a probability, prediction, or recommendation.

## Components
- Price above 20-day average: 12 points
- Price above 50-day average: 12 points
- 20-day average above 50-day average: 12 points
- Momentum: 5–15 points for positive 20-session returns, with higher awards for stronger returns
- Breakout above the previous 20-session high: 18 points
- Relative volume: 5–15 points when available, based on thresholds of 1.2x, 1.5x and 2x
- Relative strength vs a broad benchmark over 20 sessions: 5–16 points

The score is capped at 100. Signals require at least 50 points to be surfaced in the technical signal cards. The top five eligible signals are shown.

## Additional context
- Five-session relative strength is displayed as context, but does not directly add points.
- Benchmark: ASX-listed symbols use the ASX 200 (^AXJO); US symbols use the S&P 500 (^GSPC).
- Risk flags note weak momentum, below-average trend conditions, large daily declines and missing volume data.
- The benchmark comparison is a rough broad-market proxy; it does not adjust for sector or industry.

## Limitations
- This is a prototype heuristic; thresholds and weights require backtesting and ongoing evaluation.
- Data is sourced from the prototype market endpoint and may be delayed or incomplete.
- Missing fields are not treated as positive evidence.
- Review company announcements, liquidity, fundamentals, catalysts, risk and portfolio suitability independently.
