# News catalyst matching v1

The news endpoint adds heuristic metadata to RSS headlines:
- Keyword categories (earnings, guidance, contracts, corporate actions, regulatory, macro, commodities, analyst, risk)
- Watch-universe entity/ticker matching
- Basic classification and relevance labels
- Graceful JSON error response when the upstream is unavailable

These matches are not verified catalysts or sentiment analysis. Headlines may be incomplete, ambiguous, stale or matched on a keyword alone.
