export function onRequestGet() {
  return Response.json({
    ok: true,
    app: "Market Mind",
    version: "0.4.0",
    capabilities: ["market-snapshot", "cross-asset-signals", "sector-rotation", "technical-radar"],
    marketData: "Yahoo Finance chart endpoint — prototype only",
    timestamp: new Date().toISOString()
  }, { headers: { "Cache-Control": "no-store" } });
}
