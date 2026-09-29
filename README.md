# Market Mind

Market Mind is a swipeable, mobile-first feed where every card teaches something interesting about markets, investing or the economy in 15–30 seconds.

## MVP

- Mobile-first swipeable cards
- Market/economic education cards
- Category tags
- Key takeaway metric
- Simple navigation shell
- No backend or API dependency yet, so the MVP works immediately as a static site

## Next build

1. Live ASX/US market data
2. News ingestion and source attribution
3. Market Mind scoring engine
4. Watchlists and personalised feeds
5. AI-generated 15–30 second explanations
6. Saved cards
7. Event-driven alerts
8. Production data/API layer

The first implementation is intentionally dependency-free so the core interaction can be tested before adding live-data complexity.


## Running the live MVP

The frontend is static, but the live data endpoints use Cloudflare Pages Functions.

### Recommended deployment
1. Connect `Huzzbet/Market-Mind` to Cloudflare Pages.
2. Use the repository root as the build directory.
3. No build command is required for this MVP.
4. Deploy.
5. Open the deployed URL and confirm `/api/health` returns JSON with `"ok": true`.

The browser calls:
- `/api/market` for market snapshot data
- `/api/news` for the prototype news feed
- `/api/health` for deployment diagnostics

### Important
The current market endpoint uses a Yahoo Finance chart endpoint as a prototype data source. Yahoo's public site provides market quotes, but production Market Mind should move to a licensed market-data provider before commercial use.

The architecture deliberately keeps the provider behind the server-side function so the frontend does not need to change when the data provider changes.
