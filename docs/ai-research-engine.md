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

The endpoint accepts JSON with 1–12 source records. Each record must have an ID, title, HTTP(S) URL, publication timestamp and excerpt.

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
