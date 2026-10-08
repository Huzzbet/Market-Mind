#!/usr/bin/env python3
import json, re, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
UA="MarketMindBot/1.0 (+https://github.com/Huzzbet/Market-Mind)"
FEED=Path("data/feed.json")
def get(url, timeout=15):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=timeout) as r: return r.read()
def yahoo(symbol,range_="5d",interval="1d"):
    u="https://query1.finance.yahoo.com/v8/finance/chart/"+urllib.parse.quote(symbol,safe="")+"?range="+range_+"&interval="+interval
    d=json.loads(get(u))["chart"]["result"][0]
    c=[x for x in d.get("indicators",{}).get("quote",[{}])[0].get("close",[]) if x is not None]
    if not c: raise ValueError("no close for "+symbol)
    p=float(c[-1]); prev=float(c[-2]) if len(c)>1 else p
    return p, ((p/prev)-1)*100 if prev else 0

def history(symbol, range_="3y", interval="1mo"):
    u="https://query1.finance.yahoo.com/v8/finance/chart/"+urllib.parse.quote(symbol,safe="")+"?range="+range_+"&interval="+interval
    d=json.loads(get(u))["chart"]["result"][0]
    q=d.get("indicators",{}).get("quote",[{}])[0]
    closes=q.get("close",[]); stamps=d.get("timestamp",[])
    out=[]
    for ts,c in zip(stamps,closes):
        if c is not None: out.append([datetime.fromtimestamp(ts,timezone.utc).strftime("%Y-%m"),round(float(c),2)])
    return out

def consensus(slug):
    fallbacks={
      "quote/asx/BHP":{"rating":"Hold","target":60.77,"analysts":17},
      "quote/asx/CBA":{"rating":"Strong Sell","target":125.64,"analysts":14},
      "stocks/nvda":{"rating":"Strong Buy","target":328.72,"analysts":61},
      "stocks/msft":{"rating":"Strong Buy","target":587.63,"analysts":56}
    }
    try:
        html=get("https://stockanalysis.com/"+slug+"/forecast/").decode("utf-8","ignore")
        m=re.search(r'consensus rating of "([^"]+)"',html,re.I)
        p=re.search(r'average price target (?:is|of)\s*\$([0-9.,]+)\b',html,re.I)
        if not p: p=re.search(r'Price Target[^$]{0,120}\$([0-9.,]+)\b',html,re.I)
        n=re.search(r'According to ([0-9]+) analysts',html,re.I)
        out={"rating":m.group(1) if m else None,"target":float(p.group(1).replace(",","")) if p else None,"analysts":int(n.group(1)) if n else None,"source":"Stock Analysis"}
        fb=fallbacks.get(slug,{})
        return {"rating":out["rating"] or fb.get("rating"),"target":out["target"] or fb.get("target"),"analysts":out["analysts"] or fb.get("analysts"),"source":out["source"] if out["rating"] or out["target"] else "Stock Analysis fallback"}
    except Exception as e:
        print("Warning: consensus",slug,e)
        fb=fallbacks.get(slug,{})
        return {"rating":fb.get("rating"),"target":fb.get("target"),"analysts":fb.get("analysts"),"source":"Stock Analysis fallback"}

def fmt(v,n=2): return format(v,",."+str(n)+"f")
def pct(v): return ("+" if v>=0 else "")+format(v,".2f")+"%"
def stock_title(label,headline):
    titles={
      "BHP":"BHP · Mining outlook in focus",
      "CBA":"CBA · Income story in focus",
      "NVDA":"Nvidia · AI earnings power in focus",
      "MSFT":"Microsoft · AI valuation in focus"
    }
    return titles.get(label, label+" · Latest catalyst")
def catalyst_text(headline):
    text=re.sub(r"\s+-\s+(The Motley Fool|Simply Wall St.*|Yahoo Finance|Reuters|AFR|SMH.*)$","",headline,flags=re.I).strip()
    text=re.sub(r"^(BREAKING|EXCLUSIVE|UPDATE)[:\-]\s*","",text,flags=re.I)
    return text if len(text)<=88 else text[:85].rstrip()+"…"

def catalyst_score(label,item):
    title=item.get("title","").lower()
    source=item.get("source","").lower()
    names={"BHP":["bhp"],"CBA":["cba","commonwealth bank"],"NVDA":["nvidia","nvda"],"MSFT":["microsoft","msft"]}
    if not any(n in title for n in names.get(label,[])): return -100
    score=20
    strong={"results":10,"earnings":10,"guidance":10,"profit":9,"revenue":8,"dividend":8,"upgrade":9,"downgrade":9,"price target":9,"target":6,"contract":8,"deal":8,"acquisition":9,"merger":9,"buyback":8,"outlook":8,"forecast":7,"production":7,"shipments":6,"order":7,"partnership":7,"regulatory":8,"approval":7,"project":6,"site visit":5,"cash flow":6,"margin":7}
    for word,weight in strong.items():
        if word in title: score+=weight
    weak={"best stock":-9,"should i buy":-9,"how much":-8,"passive income":-7,"is it a buy":-7,"top stocks":-7,"could":-3}
    for word,weight in weak.items():
        if word in title: score+=weight
    if any(x in source for x in ("reuters","afr","market index","marketscreener","fnarena","investsmart")): score+=5
    if "motley fool" in source or "simply wall st" in source: score-=2
    if label in ("BHP","CBA") and any(x in title for x in ("broker","ubs","macquarie","bofa","jpmorgan","morgan stanley","jefferies","rbc","deutsche bank")): score+=5
    if len(title)>115: score-=1
    return score
def news(q,limit=3):
    u="https://news.google.com/rss/search?"+urllib.parse.urlencode({"q":q+" when:1d","hl":"en-AU","gl":"AU","ceid":"AU:en"})
    root=ET.fromstring(get(u)); out=[]
    for it in root.findall("./channel/item")[:limit]:
        title=(it.findtext("title") or "").strip(); link=(it.findtext("link") or "").strip(); se=it.find("source")
        source=(se.text if se is not None else "Market news") or "Market news"
        if title and link: out.append({"title":re.sub(r"\s+"," ",title),"link":link,"source":source.strip()})
    return out
def main():
    now=datetime.now(timezone.utc).astimezone(); syms={"asx200":"^AXJO","sp500":"^GSPC","vix":"^VIX","oil":"CL=F","gold":"GC=F","us10":"^TNX","aud":"AUDUSD=X"}; m={}
    for k,s in syms.items():
        try: m[k]=dict(zip(("price","pct"),yahoo(s)))
        except Exception as e: print("Warning:",s,e)
    stocks={}
    for k,sym in {"BHP":"BHP.AX","CBA":"CBA.AX","NVDA":"NVDA","MSFT":"MSFT"}.items():
        try:
            p,chg=yahoo(sym); hist=history(sym)
            stocks[k]={"symbol":sym,"price":p,"pct":chg,"history":hist}
        except Exception as e: print("Warning:",sym,e)
    if len(m)<7: raise SystemExit("Refusing to publish: incomplete market data")
    a,sp,vx,oil,gold,rate,aud=[m[k] for k in ("asx200","sp500","vix","oil","gold","us10","aud")]
    d=now.strftime("%-d %b").upper()
    cards=[
      {"tag":"ASX 200","time":d,"title":"ASX 200 is "+("higher" if a["pct"]>=0 else "lower"),"dek":"The ASX 200 is %s, %s on the latest session."%(fmt(a["price"],1),pct(a["pct"])),"data":[["ASX 200",fmt(a["price"],1)],["Session",pct(a["pct"])],["Context","Australian equities"]],"insight":"The key question is whether the move is broad-based or concentrated. Compare materials, banks, property and the Australian dollar before treating it as a wider regime signal.","source":"Yahoo Finance","rank":100},
      {"tag":"US MARKETS","time":d,"title":"US equities are "+("higher" if sp["pct"]>=0 else "lower"),"dek":"The S&P 500 is %s, %s on the latest session."%(fmt(sp["price"],2),pct(sp["pct"])),"data":[["S&P 500",fmt(sp["price"],2)],["Session",pct(sp["pct"])],["VIX",fmt(vx["price"],2)]],"insight":"Equity direction is more informative when read alongside volatility and Treasury yields. A rising index with contained volatility is a different signal from a rally driven by falling risk.","source":"Yahoo Finance","rank":99},
      {"tag":"RATES","time":d,"title":"US 10Y yield is "+("rising" if rate["pct"]>=0 else "falling"),"dek":"The US 10-year Treasury yield is about %s%%, %s on the latest session."%(fmt(rate["price"],2),pct(rate["pct"])),"data":[["US 10Y",fmt(rate["price"],2)+"%"],["Session",pct(rate["pct"])],["Risk","Equity valuations"]],"insight":"Rates remain one of the most important cross-asset variables because changes in discount rates can quickly alter equity valuations, currencies and property expectations.","source":"Yahoo Finance","rank":98},
      {"tag":"COMMODITIES","time":d,"title":"Oil is "+("higher" if oil["pct"]>=0 else "lower"),"dek":"WTI crude is about US$%s, %s on the latest session."%(fmt(oil["price"],2),pct(oil["pct"])),"data":[["WTI","US$"+fmt(oil["price"],2)],["Session",pct(oil["pct"])],["Theme","Inflation / growth"]],"insight":"Oil matters beyond energy stocks. A sustained move can feed into inflation expectations, transport costs, margins and central-bank policy.","source":"Yahoo Finance","rank":96},
      {"tag":"GOLD","time":d,"title":"Gold is "+("higher" if gold["pct"]>=0 else "lower"),"dek":"Gold is about US$%s, %s on the latest session."%(fmt(gold["price"],2),pct(gold["pct"])),"data":[["Gold","US$"+fmt(gold["price"],2)],["Session",pct(gold["pct"])],["AUD/USD",fmt(aud["price"],4)]],"insight":"Gold is most useful as a signal when viewed with Treasury yields and the US dollar. The combination can help distinguish inflation, currency and safe-haven demand.","source":"Yahoo Finance","rank":94},
      {"tag":"CURRENCY","time":d,"title":"Australian dollar is "+("higher" if aud["pct"]>=0 else "lower"),"dek":"AUD/USD is around %s, %s on the latest session."%(fmt(aud["price"],4),pct(aud["pct"])),"data":[["AUD/USD",fmt(aud["price"],4)],["Session",pct(aud["pct"])],["Theme","Global risk / commodities"]],"insight":"For Australian portfolios, currency moves can materially change the return on unhedged international assets even when the underlying asset price is unchanged.","source":"Yahoo Finance","rank":90},
    ]

    stock_cfg={
      "BHP":{"symbol":"BHP.AX","slug":"quote/asx/BHP"},
      "CBA":{"symbol":"CBA.AX","slug":"quote/asx/CBA"},
      "NVDA":{"symbol":"NVDA","slug":"stocks/nvda"},
      "MSFT":{"symbol":"MSFT","slug":"stocks/msft"}
    }
    stock_queries={
      "BHP":["BHP broker upgrade downgrade","BHP dividend results guidance","BHP copper iron ore news"],
      "CBA":["CBA broker upgrade downgrade","CBA results dividend outlook","Commonwealth Bank CBA news"],
      "NVDA":["Nvidia NVDA earnings guidance","Nvidia broker upgrade downgrade","Nvidia AI partnership buyback news"],
      "MSFT":["Microsoft MSFT earnings guidance","Microsoft broker upgrade downgrade","Microsoft AI cloud contract news"]
    }
    used_stock=set()
    for label,queries in stock_queries.items():
        candidates=[]
        seen_titles=set()
        for q in queries:
            for item in news(q,limit=4):
                key=item["title"].lower()
                if key in seen_titles: continue
                seen_titles.add(key)
                item["catalystScore"]=catalyst_score(label,item)
                candidates.append(item)
        candidates.sort(key=lambda x:x.get("catalystScore",0),reverse=True)
        x=candidates[0] if candidates else None
        st=stocks.get(label)
        if not st or not x: continue
        used_stock.add(label)
        st=stocks.get(label)
        if not st: continue
        used_stock.add(label)
        hist=st.get("history",[])
        cfg=stock_cfg[label]
        con=consensus(cfg["slug"])
        upside=((con["target"]/st["price"])-1)*100 if con.get("target") else None
        rating=(con.get("rating") or "Unavailable").upper()
        if "SELL" in rating and upside is not None and upside < 0: view="SELL"
        elif "BUY" in rating and upside is not None and upside > 10 and abs(st["pct"]) < 4: view="BUY"
        elif abs(st["pct"]) >= 4: view="HOLD"
        else: view="WATCH"
        target_txt=fmt(con["target"],2) if con.get("target") else "—"
        upside_txt=(("+" if upside>=0 else "")+format(upside,".1f")+"%") if upside is not None else "—"
        cards.append({
          "tag":"STOCK INTELLIGENCE / "+("AUSTRALIA" if label in ("BHP","CBA") else "US"),
          "time":d,
          "title":stock_title(label,x["title"]),
          "dek":x["source"]+" • "+fmt(st["price"],2)+" • "+pct(st["pct"])+" today.",
          "data":[["PRICE",fmt(st["price"],2)],["CONSENSUS",rating],["TARGET · "+str(con.get("analysts") or "—")+" ANALYSTS",target_txt]],
          "insight":"Market Mind: "+view+". Consensus target implies "+upside_txt+" versus the current price. Catalyst: "+catalyst_text(x["title"])+".",
          "source":x["source"],
          "link":x["link"],
          "rank":70,
          "stock":{"ticker":st["symbol"],"history":hist,"threeYearReturn":round(((hist[-1][1]/hist[0][1])-1)*100,1) if len(hist)>1 and hist[0][1] else None,"consensus":rating,"target":con.get("target"),"upside":upside,"view":view,"analysts":con.get("analysts")}
        })
    seen=set()
    for q in ("ASX Australian share market","US stocks S&P 500 Nasdaq","markets bonds oil gold"):
        for x in news(q):
            key=re.sub(r"[^a-z0-9]+","",x["title"].lower())
            if key in seen: continue
            seen.add(key); cards.append({"tag":"NEWS / MARKET INTELLIGENCE","time":d,"title":x["title"],"dek":x["source"]+" • Latest market coverage.","data":[["SOURCE",x["source"]],["TYPE","Market news"],["STATUS","Latest"]],"insight":"Read the headline in context: identify the directly exposed asset, sector, rate or currency and whether the market has already reacted.","source":x["source"],"link":x["link"],"rank":88})
            if len(cards)>=13: break
        if len(cards)>=9: break
    if len(cards)<10: raise SystemExit("Refusing to publish: fewer than 10 cards")
    def t(x): return {"value":x["value"],"direction":"up" if x["pct"]>=0 else "down","change":pct(x["pct"])}
    feed={"version":"1.4.0","updatedAt":now.isoformat(timespec="seconds"),"tickers":{},"cards":cards}
    feed["tickers"]={"asx200":t({"value":fmt(a["price"],1),"pct":a["pct"]}),"sp500":t({"value":fmt(sp["price"],2),"pct":sp["pct"]}),"vix":t({"value":fmt(vx["price"],2),"pct":vx["pct"]}),"oil":t({"value":"US$"+fmt(oil["price"],2),"pct":oil["pct"]}),"gold":t({"value":"US$"+fmt(gold["price"],2),"pct":gold["pct"]}),"us10":t({"value":fmt(rate["price"],2)+"%","pct":rate["pct"]}),"aud":t({"value":fmt(aud["price"],4),"pct":aud["pct"]})}
    FEED.write_text(json.dumps(feed,indent=2,ensure_ascii=False)+"\n"); print("Wrote",len(cards),"cards at",feed["updatedAt"])
if __name__=="__main__": main()