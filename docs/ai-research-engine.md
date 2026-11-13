# Market Mind AI research engine

## What this adds

POST /api/intelligence is a private Cloudflare Pages Function that sends a supplied, source-attributed research pack to the OpenAI Responses API and returns a schema-constrained Market Mind research draft.

It does not fetch market data, verify the truth of supplied source excerpts, save a report, update the public research feed, or publish investment ideas. Those are deliberately separate stages. The endpoint requires authenticated server-to-server use and is not intended to be called directly by the public browser app.

## Required Cloudflare configuration

In the Cloudflare Pages project, open **Settings → Variables and Secrets** and configure:

- OPENAI_API_KEY — encrypted secret containing the OpenAI API key.
- MARKET_MIND_ENGINE_TOKEN — encrypted, high-entropy bearer token used by the trusted scheduler/orchestrator.
- OPENAI_MODEL — model identifier enabled for the API project.

Set values for both Preview and Production environments as appropriate. Never put these values in source code, browser JavaScript, committed Wrangler vars, or a public GitHub Actions log. For local development, use an ignored .dev.vars file.

Cloudflare guidance: https://developers.cloudflare.com/pages/functions/bindings/

OpenAI Responses API reference: https://developers.openai.com/api/reference/resources/responses/methods/create

Structured Outputs guide: https://developers.openai.com/api/docs/guides/structured-outputs

API usage is billed separately from a ChatGPT subscription.

## Request

The endpoint accepts either a supplied research pack or a live Market Mind snapshot request. The live mode collects the existing `/api/market`, `/api/mind` and `/api/news` responses server-side, then passes a bounded source pack to the research model. It does not scrape article bodies. Market prices and scanner observations remain prototype Yahoo Finance-derived data.

    {
      "focus": "Australian and US markets; capital rotation and quality compounders",
      "marketContext": "Dated, sourced market observations go here.",
      "sources": [
        {
          "id": "rba-outlook-2026-11",
          "title": "Example source title",
          "url": "https://example.com/research",
          "publishedAt": "2026-11-14T08:00:00+11:00",
          "publisher": "Example publisher",
          "excerpt": "A short, attributable extract or factual summary."
        }
      ]
    }

Call with Authorization: Bearer <MARKET_MIND_ENGINE_TOKEN>. Keep the token in the trusted server-side orchestrator only.

## Response and publication boundary

Successful responses have status: draft_for_review and publication: not_published. They include a structured market read, opportunity map, catalysts, risks, invalidation conditions, caveats and source references.

The function validates that model-generated source IDs refer to records in the submitted source pack. This is a reference-integrity check, not independent verification that a source supports every claim. A human reviewer must check the original sources and underlying figures before publication or investment use.

## Request limits and safety

- POST only; bearer-token authentication required.
- Maximum request body: 40 KB.
- 1–12 source records; excerpts capped at 5,000 characters each.
- Only HTTP(S) source links accepted.
- The model receives supplied evidence only; this endpoint does not enable web search or autonomous browsing.
- No auto-publication, trading, client-specific advice, or changes to the Conviction List.
- The frontend must never receive either secret.

## Next stages

1. Connect trusted data/news ingestion with timestamps and provider attribution.
2. Add independent validation for market values, dates and financial metrics.
3. Add a review queue and approval action.
4. Publish approved cards into data/research/latest.json.
5. Add scheduled orchestration only after provider access, cost limits, monitoring and failure handling are configured.


## Live snapshot mode

A trusted server-side caller can request the current Market Mind data pack without assembling sources itself:

    {
      "mode": "live_snapshot",
      "focus": "Assess cross-asset risk, sector rotation and the strongest research candidates."
    }

The function collects up to 20 successful market observations, current deterministic scanner/sector observations and up to eight RSS headlines. It includes timestamps, provider notes and explicit caveats that headlines are not article text and the market feed is a prototype. The resulting model output remains a draft requiring review.

This is the first connected ingestion path, not yet a complete production data pipeline. The Google News RSS feed is an aggregator and Yahoo Finance is not a licensed production feed.
