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
  const add = (type, score, title, explanation, watch, extra={}) =>
    signals.push({type,score,title,explanation,watch,...extra});

  const spx=get("^GSPC"), vix=get("^VIX"), oil=get("CL=F"), aud=get("AUDUSD=X"),
    tnx=get("^TNX"), gold=get("GC=F"), asx=get("^AXJO");

  // Cross-asset relationships: observations are signals, not causal explanations.
  if (spx && vix && spx.pct < -0.7 && vix.pct > 2)
    add("cross-asset",94,"Equities lower as volatility rises","US equities are falling while the VIX is rising.","Check rates and current macro or company headlines before assigning a cause.");
  if (oil && aud && oil.pct > 0.8 && aud.pct < -0.4)
    add("cross-asset",88,"Oil higher while the Australian dollar falls","Energy is moving higher while AUD/USD is moving lower.","Watch US dollar moves, bond yields and inflation expectations.");
  if (tnx && spx && tnx.pct > 0.8 && spx.pct < -0.5)
    add("cross-asset",86,"Yields higher as equities weaken","Treasury yields are moving higher while equities are falling.","Look for inflation, labour-market or central-bank catalysts.");
  if (gold && tnx && gold.pct > 0.8 && tnx.pct > 0.8)
    add("cross-asset",72,"Gold and yields are rising together","Gold and Treasury yields are both moving higher.","Compare the move with the US dollar and inflation expectations.");

  // Sector rotation using equal-weighted constituent returns; minimum coverage is required.
  const sectors = {
    Materials:["BHP.AX","RIO.AX","FMG.AX"],
    Financials:["CBA.AX","NAB.AX","WBC.AX","ANZ.AX","MQG.AX"],
    Healthcare:["CSL.AX","COH.AX"],
    Property:["GMG.AX"],
    Industrials:["TCL.AX"],
    Consumer:["WES.AX","WOW.AX","COL.AX"],
    Technology:["XRO.AX","CAR.AX"],
    Energy:["STO.AX","WDS.AX","ORG.AX"]
  };
  const sectorRows = Object.entries(sectors).map(([name,symbols]) => {
    const rows=symbols.map(get).filter(x=>x && Number.isFinite(x.return5d));
    return {name,count:rows.length,total:symbols.length,return5d:rows.length?rows.reduce((s,x)=>s+x.return5d,0)/rows.length:null,
      breadth:rows.length?rows.filter(x=>x.return5d>0).length/rows.length:null,
      leaders:rows.slice().sort((a,b)=>b.return5d-a.return5d).slice(0,2).map(x=>({symbol:x.symbol,return5d:x.return5d}))};
  }).filter(x=>x.count>=Math.min(2,x.total)&&x.return5d!==null);
  const rankedSectors=sectorRows.slice().sort((a,b)=>b.return5d-a.return5d);
  const covered=rankedSectors.filter(x=>x.count>=2);
  if(covered.length>=2){
    const leader=covered[0],laggard=covered[covered.length-1];
    if(leader.return5d-laggard.return5d>=2.5)
      add("sector-rotation",Math.min(90,Math.round(60+(leader.return5d-laggard.return5d)*5)),
        leader.name+" leading the five-day sector tape",
        leader.name+" constituents average "+leader.return5d.toFixed(2)+"% over five sessions, versus "+laggard.name+" at "+laggard.return5d.toFixed(2)+"%.",
        "Check constituent breadth, earnings news and whether the move persists; sector coverage is a partial proxy, not a complete index.",
        {leaders:leader.leaders,laggards:laggard.leaders,spread:leader.return5d-laggard.return5d});
  }

  // Trend and volume scans on individual ASX names.
  const stockSymbols=["BHP.AX","RIO.AX","FMG.AX","CBA.AX","NAB.AX","WBC.AX","ANZ.AX","MQG.AX",
    "CSL.AX","COH.AX","GMG.AX","TCL.AX","WES.AX","WOW.AX","COL.AX","REA.AX","XRO.AX","CAR.AX","TLS.AX","STO.AX","WDS.AX","ORG.AX"];
  const candidates=stockSymbols.map(get).filter(x=>x && Number.isFinite(x.return20d));
  const rankedStocks=candidates.map(x=>{
    let score=0, reasons=[];
    if(x.aboveMa20===true){score+=15;reasons.push("price above 20-day average");}
    if(x.aboveMa50===true){score+=15;reasons.push("price above 50-day average");}
    if(x.maBullish===true){score+=15;reasons.push("20-day average above 50-day average");}
    if(x.return20d>3){score+=15;reasons.push("positive 20-day momentum");}
    if(x.breakout20d===true){score+=20;reasons.push("above prior 20-session high");}
    if(x.volumeRatio>=1.5){score+=20;reasons.push("volume at least 1.5x its 20-session average");}
    return {...x,score,reasons};
  }).sort((a,b)=>b.score-a.score);
  for(const x of rankedStocks.filter(x=>x.score>=45).slice(0,5)){
    add("technical",x.score,x.symbol+" showing a technical setup",
      x.reasons.join("; ")+". 20-session return: "+x.return20d.toFixed(2)+"%.",
      "Check liquidity, announcements, valuation, trend durability and downside levels. A technical screen is not a buy recommendation.",
      {symbol:x.symbol,price:x.price,return5d:x.return5d,return20d:x.return20d,ma20:x.ma20,ma50:x.ma50,volumeRatio:x.volumeRatio,breakout20d:x.breakout20d,reasons:x.reasons});
  }

  // Existing basic sector divergence monitor retained for continuity.
  for (const [group,symbols] of Object.entries({Materials:["BHP.AX","RIO.AX","FMG.AX"],Financials:["CBA.AX","NAB.AX","WBC.AX","ANZ.AX","MQG.AX"]})) {
    const rows=symbols.map(get).filter(Boolean);
    if(rows.length<2) continue;
    const average=rows.reduce((sum,x)=>sum+x.pct,0)/rows.length;
    const breadth=rows.filter(x=>x.pct>0).length/rows.length;
    if(Math.abs(average)>=1.2 && breadth>0 && breadth<1)
      add("sector-dispersion",Math.min(82,Math.round(55+Math.abs(average)*12)),group+" stocks are diverging",
        "The "+group.toLowerCase()+" group is showing mixed daily performance.",
        "Compare individual company headlines before treating the move as sector-wide.");
  }

  signals.sort((a,b)=>b.score-a.score);
  const cards=signals.map(s=>({...s,framework:{
    confirmed:"A rule-based condition has been detected in retrieved market data.",
    expectation:"The cause still requires confirmation from current news and macro releases.",
    implication:s.explanation,watch:s.watch
  }}));
  const snapshot = {
    asx200:asx?{price:asx.price,dayPct:asx.pct,return5d:asx.return5d,return20d:asx.return20d}:null,
    sp500:spx?{price:spx.price,dayPct:spx.pct,return5d:spx.return5d,return20d:spx.return20d}:null,
    vix:vix?{price:vix.price,dayPct:vix.pct}:null,
    us10:tnx?{price:tnx.price,dayPct:tnx.pct}:null,
    oil:oil?{price:oil.price,dayPct:oil.pct}:null,
    aud:aud?{price:aud.price,dayPct:aud.pct}:null
  };
  return Response.json({
    updatedAt:new Date().toISOString(),version:"0.4.0",source:"Market Mind intelligence layer",
    methodology:"Rule-based cross-asset, sector rotation, moving-average, momentum, breakout and volume screens. No broker-revision or institutional-flow feed is connected.",
    marketCount:data.length,signalCount:cards.length,signals:cards,sectorRotation:rankedSectors,
    technicalLeaders:rankedStocks.slice(0,8).map(x=>({symbol:x.symbol,score:x.score,price:x.price,return5d:x.return5d,return20d:x.return20d,ma20:x.ma20,ma50:x.ma50,volumeRatio:x.volumeRatio,breakout20d:x.breakout20d,reasons:x.reasons})),
    snapshot,headlines:(news.items||[]).slice(0,6)
  },{headers:{"Cache-Control":"public, max-age=60"}});
}
