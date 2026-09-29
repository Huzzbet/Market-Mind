export async function onRequestGet({ request }) {
  const url = new URL(request.url);
  const symbols = (url.searchParams.get("symbols") || "^AXJO,^GSPC,^VIX,CL=F,GC=F,AUDUSD=X")
    .split(",").map(s => s.trim()).filter(Boolean).slice(0, 12);

  const results = await Promise.all(symbols.map(async symbol => {
    try {
      const endpoint = "https://query1.finance.yahoo.com/v8/finance/chart/" +
        encodeURIComponent(symbol) + "?range=1d&interval=5m";
      const response = await fetch(endpoint, {
        headers: { "User-Agent": "MarketMind/1.0" }
      });
      if (!response.ok) throw new Error("upstream " + response.status);
      const json = await response.json();
      const r = json.chart?.result?.[0];
      const meta = r?.meta || {};
      const quote = r?.indicators?.quote?.[0] || {};
      const closes = (quote.close || []).filter(Number.isFinite);
      const price = Number.isFinite(meta.regularMarketPrice) ? meta.regularMarketPrice : closes.at(-1);
      const previous = Number.isFinite(meta.previousClose) ? meta.previousClose : closes[0];
      const change = Number.isFinite(price) && Number.isFinite(previous) ? price - previous : null;
      const pct = Number.isFinite(change) && previous ? (change / previous) * 100 : null;
      return { symbol, price, change, pct, currency: meta.currency || null, exchange: meta.exchangeName || null, ok: true };
    } catch (error) {
      return { symbol, ok: false, error: String(error) };
    }
  }));

  return Response.json({
    updatedAt: new Date().toISOString(),
    provider: "Yahoo Finance chart endpoint — prototype only",
    data: results
  }, { headers: { "Cache-Control": "public, max-age=15" }});
}
