# Market Mind Valuation Lab

## Purpose
A reusable scenario valuation workspace for the six flagship research candidates. It is an analyst-input prototype, not a live valuation service.

## Current implementation
- DCF: five-year explicit free-cash-flow forecast plus Gordon-growth terminal value.
- Enterprise-to-equity bridge: subtract net debt (negative net debt represents net cash) and divide by diluted shares.
- Bear/base/bull scenarios: alter growth, WACC and terminal growth transparently.
- Sensitivity matrix: WACC versus terminal growth.
- P/E cross-check: normalised forward EPS multiplied by a justified forward multiple.
- Current market price and its as-of date are required before implied upside/downside is shown.
- Assumptions can be saved locally in the user's browser.

## Formula
For year t, forecast FCF is FCF0 × (1 + g)^t. Enterprise value is the sum of discounted forecast FCF plus discounted terminal value, where terminal value = FCF5 × (1 + terminal growth) / (WACC − terminal growth). Equity value = enterprise value − net debt. Per-share value = equity value / diluted shares.

## Critical limitations
- The five-year DCF is a generic framework. It is not a substitute for sector-specific valuation.
- BHP requires through-cycle commodity prices, sustaining/growth capex and asset-level NAV checks.
- Goodman requires operating earnings/FFO/AFFO, NAV, cap rates, development yields, funding and dilution analysis. Generic DCF output is only a sensitivity aid.
- CSL requires normalised earnings, restructuring cost treatment, plasma economics and FX consistency.
- Alphabet, Microsoft and Amazon require explicit reinvestment, stock-based compensation, lease and incremental-return analysis. Amazon and Alphabet should be cross-checked with sum-of-the-parts.
- The model does not currently ingest a live price, consensus estimates, official company guidance tables or audited share-count/net-debt inputs. All such fields are deliberately blank.
- Currency consistency is essential. Do not mix USD cash flows with AUD market capitalisation or share price without explicit FX conversion.
- Terminal growth must be below WACC. Model outputs are highly sensitive to these assumptions.

## Source register
See the company source links embedded in valuation.html and the reference facts in data/valuation/models.json. These are reported historical results, not forward estimates.

## Next build phase
1. Add verified timestamped market-price snapshots with source, exchange, currency and stale-data checks.
2. Build a sourced financial input layer: diluted shares, net debt, cash flow, capex, SBC, lease liabilities and corporate actions.
3. Add sector-specific models: miner NAV / commodity deck, property FFO-NAV-cap-rate model, biotech earnings recovery, and technology SOTP / DCF.
4. Add forward estimates only from a clearly identified, authorised provider or explicit company guidance.
5. Add model versioning, assumption history and thesis/valuation change logs.
