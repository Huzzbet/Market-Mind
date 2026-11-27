# Scanner universe and data reliability v2

## Expanded coverage
The default market scan now includes a wider watch universe across Australian materials, banks, healthcare, property, retail, industrials, energy, insurance and travel, plus large US equities and index ETFs.

The endpoint accepts a custom symbols query parameter, but caps the request at 75 symbols to constrain upstream request volume.

## Observation integrity
- Close, volume and timestamp are retained together in aligned bars.
- Missing close values are excluded without shifting associated volume or timestamp observations.
- Volume ratios are only calculated when the latest volume is valid and at least ten valid observations are available in the preceding 20-session window.
- The returned volume observation count exposes incomplete coverage.

## Beta limitations
The prototype makes individual upstream requests and can encounter rate limits, missing symbols, delays, and inconsistent provider metadata. The larger universe may increase latency or partial failures. This is not a licensed market-data service. Do not rely on it for execution or investment decisions.
