export async function onRequestGet({ request }) {
  const url = new URL(request.url);
  const defaults = [
    "^AXJO","^GSPC","^IXIC","^VIX","^TNX","CL=F","GC=F","AUDUSD=X",
    "BHP.AX","RIO.AX","FMG.AX","CBA.AX","NAB.AX","WBC.AX","ANZ.AX","MQG.AX",
    "CSL.AX","COH.AX","GMG.AX","TCL.AX","WES.AX","WOW.AX","COL.AX","REA.AX",
    "XRO.AX","CAR.AX","TLS.AX","STO.AX","WDS.AX","ORG.AX"
  ];
  const symbols = (url.searchParams.get("symbols") || defaults.join(","))
    .split(",").map(s => s.trim()).filter(Boolean).slice(0, 40);

  const average = values => values.length ? values.reduce((a,b)=>a+b,0)/values.length : null;
  const pctReturn = (latest, base) => Number.isFinite(latest) && Number.isFinite(base) && base !== 0 ? ((latest/base)-1)*100 : null;

  const results = await Promise.all(symbols.map(async symbol => {
    try {
      const endpoint = "https://query1.finance.yahoo.com/v8/finance/chart/" +
        encodeURIComponent(symbol) + "?range=3mo&interval=1d";
      const response = await fetch(endpoint, { headers: { "User-Agent": "MarketMind/1.0" } });
      if (!response.ok) throw new Error("upstream " + response.status);
      const json = await response.json();
      const r = json.chart?.result?.[0];
      const meta = r?.meta || {};
      const quote = r?.indicators?.quote?.[0] || {};
      const closes = (quote.close || []).filter(Number.isFinite);
      const volumes = (quote.volume || []).filter(v => Number.isFinite(v) && v > 0);
      const price = Number.isFinite(meta.regularMarketPrice) ? meta.regularMarketPrice : closes.at(-1);
      const previous = Number.isFinite(meta.previousClose) ? meta.previousClose : closes.at(-2);
      const change = Number.isFinite(price) && Number.isFinite(previous) ? price - previous : null;
      const pct = Number.isFinite(change) && previous ? (change / previous) * 100 : null;
      const ma20 = average(closes.slice(-20));
      const ma50 = closes.length >= 50 ? average(closes.slice(-50)) : null;
      const latestClose = closes.at(-1);
      const prior20 = closes.slice(-21,-1);
      const priorHigh20 = prior20.length ? Math.max(...prior20) : null;
      const latestVolume = volumes.at(-1);
      const averageVolume20 = average(volumes.slice(-21,-1));
      const volumeRatio = latestVolume && averageVolume20 ? latestVolume / averageVolume20 : null;
      const timestamps = r?.timestamp || [];
      const high = Number.isFinite(meta.regularMarketDayHigh) ? meta.regularMarketDayHigh : null;
      const low = Number.isFinite(meta.regularMarketDayLow) ? meta.regularMarketDayLow : null;
      return {
        symbol, price, change, pct,
        return5d: pctReturn(price, closes.at(-6)),
        return20d: pctReturn(price, closes.at(-21)),
        return60d: pctReturn(price, closes.at(-61)),
        ma20, ma50,
        aboveMa20: Number.isFinite(price) && Number.isFinite(ma20) ? price > ma20 : null,
        aboveMa50: Number.isFinite(price) && Number.isFinite(ma50) ? price > ma50 : null,
        maBullish: Number.isFinite(ma20) && Number.isFinite(ma50) ? ma20 > ma50 : null,
        priorHigh20,
        breakout20d: Number.isFinite(price) && Number.isFinite(priorHigh20) ? price > priorHigh20 : null,
        latestVolume, averageVolume20, volumeRatio,
        high, low, observations: closes.length,
        lastTimestamp: timestamps.at(-1) || null,
        currency: meta.currency || null, exchange: meta.exchangeName || null, ok: true
      };
    } catch (error) {
      return { symbol, ok: false, error: String(error) };
    }
  }));

  return Response.json({
    updatedAt: new Date().toISOString(),
    provider: "Yahoo Finance chart endpoint — prototype only; validate before investment use",
    methodology: "Daily bars; 5/20/60-session returns; 20/50-session moving averages; 20-session breakout and volume comparison.",
    data: results
  }, { headers: { "Cache-Control": "public, max-age=60" }});
}
