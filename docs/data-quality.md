# Market Mind data-quality checks

## Market endpoint

The market snapshot endpoint uses Yahoo Finance chart data as a prototype source. The app must label this source as delayed/possibly incomplete and must not imply exchange-grade realtime data.

### Implemented check
- Preserve close/volume alignment by building observations from the same indexed daily-bar arrays. Previously, separately filtering close and volume arrays could shift volume readings and misstate the relative-volume calculation.
- The relative-volume calculation uses valid prior observations and excludes the latest observation from the 20-observation comparison.

### Beta validation checklist
- Confirm provider responses and symbol errors are visible as per-symbol failures, not silently treated as zero.
- Validate quote timestamps and distinguish last close from live market price.
- Test missing, zero and null volume values.
- Confirm thinly traded instruments do not receive misleading relative-volume signals.
- Check symbol-specific corporate actions, currency and exchange metadata.
- Confirm feed health reflects the quality and freshness of the payload, not merely successful HTTP loading.
- Review source licensing and commercial-use restrictions before public launch.

## Signal interpretation
Technical signals and research scores are screening tools only. They are not probabilities, forecasts or investment recommendations. Confirm catalysts and downside risks independently.
