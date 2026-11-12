# Market Mind

Market Mind is a mobile-first market intelligence terminal with a swipeable research feed. The opening Pulse view connects global markets, cross-asset conditions, sector rotation and technical setups.

## Current capabilities

- Pulse dashboard as the opening screen
- ASX and US index, volatility, rates, commodity and currency snapshots
- Daily market history with 5/20/60-session returns
- 20- and 50-session moving averages
- Prior 20-session high breakout checks
- Relative volume comparison against the prior 20 sessions
- Rule-based cross-asset condition detection
- Partial-coverage sector rotation and breadth analysis
- ASX technical momentum and trend radar
- Swipeable daily research feed, watchlist and market views

## Intelligence methodology

Signals are generated from transparent, deterministic rules. A score is a prioritisation aid, not a probability of success or expected return. Price relationships do not establish causation. Sector groupings are partial constituent proxies, not official sector indices.

The technical radar rewards alignment above the 20- and 50-session averages, positive 20-session momentum, breakouts above the prior 20-session high and volume at least 1.5 times the 20-session average. A candidate is surfaced when its rule score reaches 45/100.

The current build does **not** have licensed institutional flow data, verified broker recommendation/revision history, consensus earnings estimates or a production-grade fundamentals feed. Those should be integrated from authorised providers before being described as live institutional signals.

## Data and deployment

The frontend is static and the live endpoints use Cloudflare Pages Functions:

- `/api/market` — market snapshots and daily technical statistics
- `/api/news` — Google News RSS headlines
- `/api/mind` — cross-asset, sector and technical signal engine
- `/api/health` — deployment diagnostics

The market endpoint currently uses Yahoo Finance chart data as a prototype source. It is not a licensed production feed; quotes may be delayed, incomplete or rate-limited. Validate the data and licensing before relying on it commercially or for client-facing advice.

## Deployment

1. Connect `Huzzbet/Market-Mind` to Cloudflare Pages.
2. Use the repository root as the build directory.
3. No build command is required.
4. Deploy the intended branch.
5. Confirm `/api/health`, `/api/market` and `/api/mind` return valid JSON.
6. Check the Pulse view on desktop and mobile after deployment.

## Next data integrations

1. Licensed ASX/US market data with reliable historical bars and volume.
2. Corporate actions, earnings calendar and results.
3. Broker consensus and recommendation/revision history.
4. Licensed fund-flow and institutional ownership data.
5. Fundamental valuation and estimate revision history.
6. Source-attributed news classification and event alerts.
