export async function onRequestGet({ request }) {
  const origin = new URL(request.url).origin;
  const [marketResponse, newsResponse] = await Promise.all([
    fetch(new URL("/api/market", origin)),
    fetch(new URL("/api/news?q=ASX%20Australia%20markets%20OR%20US%20stocks%20OR%20RBA%20OR%20oil", origin))
  ]);
  const market = marketResponse.ok ? await marketResponse.json() : { data: [] };
  const news = newsResponse.ok ? await newsResponse.json() : { items: [] };
  const data = (market.data || []).filter(x => x.ok && Number.isFinite(x.pct));
  const get = symbol => data.find(x => x.symbol === symbol);
  const signals = [];
  const spx=get("^GSPC"), vix=get("^VIX"), oil=get("CL=F"), aud=get("AUDUSD=X"), tnx=get("^TNX"), gold=get("GC=F");

  if (spx && vix && spx.pct < -0.7 && vix.pct > 2) signals.push({type:"cross-asset",score:94,title:"Equities lower as volatility rises",explanation:"US equities are falling while the VIX is rising.",watch:"Check rates and current macro or company headlines before assigning a cause."});
  if (oil && aud && oil.pct > 0.8 && aud.pct < -0.4) signals.push({type:"cross-asset",score:88,title:"Oil higher while the Australian dollar falls",explanation:"Energy is moving higher while AUD/USD is moving lower.",watch:"Watch US dollar moves, bond yields and inflation expectations."});
  if (tnx && spx && tnx.pct > 0.8 && spx.pct < -0.5) signals.push({type:"cross-asset",score:86,title:"Yields higher as equities weaken",explanation:"Treasury yields are moving higher while equities are falling.",watch:"Look for inflation, labour-market or central-bank catalysts."});
  if (gold && tnx && gold.pct > 0.8 && tnx.pct > 0.8) signals.push({type:"cross-asset",score:72,title:"Gold and yields are rising together",explanation:"Gold and Treasury yields are both moving higher.",watch:"Compare the move with the US dollar and inflation expectations."});

  const groups={Materials:["BHP.AX","RIO.AX","FMG.AX"],Financials:["CBA.AX","NAB.AX","WBC.AX","ANZ.AX","MQG.AX"]};
  for (const [group,symbols] of Object.entries(groups)) {
    const rows=symbols.map(get).filter(Boolean);
    if(rows.length<2) continue;
    const average=rows.reduce((sum,x)=>sum+x.pct,0)/rows.length;
    const breadth=rows.filter(x=>x.pct>0).length/rows.length;
    if(Math.abs(average)>=1.2 && breadth>0 && breadth<1) signals.push({type:"sector",score:Math.min(82,Math.round(55+Math.abs(average)*12)),title:group+" stocks are diverging",explanation:"The "+group.toLowerCase()+" group is showing mixed performance.",watch:"Compare individual company headlines before treating the move as sector-wide."});
  }
  signals.sort((a,b)=>b.score-a.score);
  const cards=signals.map(s=>({...s,framework:{confirmed:"Price relationships detected in live market data.",expectation:"The cause still requires confirmation from current news and macro releases.",implication:s.explanation,watch:s.watch}}));
  return Response.json({updatedAt:new Date().toISOString(),version:"0.3.0",source:"Market Mind intelligence layer",methodology:"Rule-based cross-asset and sector signal detection; not investment advice.",marketCount:data.length,signalCount:cards.length,signals:cards,headlines:(news.items||[]).slice(0,6)},{headers:{"Cache-Control":"public, max-age=60"}});
}
