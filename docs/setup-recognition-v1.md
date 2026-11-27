# Market Mind setup recognition v1

Setup labels are descriptive screen conditions, not predictive signals, trade recommendations or probability estimates.

## Setup types
- **Breakout:** price above prior 20-session high with relative volume >= 1.3.
- **Momentum continuation:** price above both 20/50-day averages, MA20 above MA50 and positive 20-session return.
- **Trend pullback:** price below MA20 but above MA50, bullish MA alignment and positive 20-session return.
- **Short-term recovery:** negative 5-session but positive 20-session return, price above MA20 and MA50.
- **Relative-strength leader:** >=8% positive 20-session return, positive 5-session return and price above MA50.

Each type includes descriptive conditions and a risk caveat. A stock may carry more than one label. The strength field is a display-priority heuristic, not a probability, forecast or backtested score.

## Limitations
- Daily data may be delayed or incomplete; Yahoo Finance prototype.
- These rules have not been backtested.
- No intraday data, spreads, execution costs, verified announcements or benchmark-relative scoring in these setup labels.
- Avoid treating classification as a recommendation.
