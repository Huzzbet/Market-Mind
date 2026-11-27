# Sector rotation engine v2

Market Mind compares available constituents using equal-weighted return proxy baskets.

## Metrics
- Average 5-session and 20-session return.
- Positive-return breadth for both periods.
- Counts above the 20-day and 50-day moving averages.
- Two strongest and weakest available constituents by 20-session return (fallback to 5-session).
- Coverage count and coverage ratio against the defined basket.

## Interpretation and limitations
- These are **partial constituent proxy baskets**, not official sector indices or ETFs.
- Basket coverage is shown explicitly; single-member groups are context only and are excluded from the cross-sector leader/laggard comparison.
- Constituents are limited to the scanner universe and data availability.
- Equal weighting can distort large sectors; basket definitions are illustrative and not benchmark methodology.
- Yahoo Finance data can be delayed, incomplete, throttled or otherwise unreliable. Confirm quotes and announcements from primary sources.
- Rankings describe recent price behaviour and are not forecasts or investment recommendations.
