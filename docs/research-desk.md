# Market Mind Research Desk — private draft storage

## What this stage adds

- AI-generated research is saved to a private Cloudflare D1 review queue when the `DB` binding is configured.
- `GET /api/research-drafts?status=pending` lists drafts.
- `PATCH /api/research-drafts` changes a pending draft to `approved` or `rejected`, with an optional reviewer note.
- Every endpoint requires the existing server-side `MARKET_MIND_ENGINE_TOKEN`.
- Approval is an internal review decision only. It does **not** publish a card, alter the Conviction List, or make a trading recommendation.

Without D1 configured, the intelligence endpoint still returns a draft but reports `persistence: not_configured`. It never pretends that a draft has been saved.

## Cloudflare setup

1. Create a D1 database in the same Cloudflare account as the Pages project.
2. Add a Pages binding named `DB` pointing to that database in **Settings → Functions → D1 database bindings** (check both Preview and Production).
3. Apply `migrations/0001_research_drafts.sql` to the database using Wrangler or the Cloudflare dashboard.
4. Keep `MARKET_MIND_ENGINE_TOKEN` as an encrypted secret. Do not place it in browser code.

Example Wrangler migration command:

```bash
npx wrangler d1 execute <DATABASE_NAME> --remote --file=migrations/0001_research_drafts.sql
```

## API examples

List pending drafts:

```http
GET /api/research-drafts?status=pending
Authorization: Bearer <MARKET_MIND_ENGINE_TOKEN>
```

Approve after source and figure checks:

```http
PATCH /api/research-drafts
Authorization: Bearer <MARKET_MIND_ENGINE_TOKEN>
Content-Type: application/json

{"id":"<draft-id>","status":"approved","reviewerNote":"Sources checked; ready for editorial formatting."}
```

Reject:

```json
{"id":"<draft-id>","status":"rejected","reviewerNote":"Insufficient primary-source support."}
```

## Security and publication boundary

The bearer token is server-to-server only. A browser-based Research Desk must not receive this token; before exposing an interactive review screen, put it behind Cloudflare Access and validate Access identity server-side (or use another authenticated admin session). The current endpoints are intentionally private.

Approved drafts remain in D1 and are not public. A later publishing stage will convert an approved draft into the existing research-card schema, preserve source links and timestamps, and require a separate explicit publish action. Rejected drafts remain available for audit.

## Data quality

The existing live snapshot still uses prototype Yahoo Finance observations and Google News RSS headlines. A generated draft is not independently fact-checked merely because its source IDs validate. Review original sources, dates, financial figures and valuation inputs before approval.
