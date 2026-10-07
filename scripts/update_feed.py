#!/usr/bin/env python3
import json, re, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
UA="MarketMindBot/1.0 (+https://github.com/Huzzbet/Market-Mind)"
FEED=Path("data/feed.json")
def get(url, timeout=15):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=timeout) as r: return r.read()
def yahoo(symbol):
    u="https://query1.finance.yahoo.com/v8/finance/chart/"+urllib.parse.quote(symbol,safe="")+"?range=5d&interval=1d"
    d=json.loads(get(u))["chart"]["result"][0]
    c=[x for x in d.get("indicators",{}).get("quote",[{}])[0].get("close",[]) if x is not None]
    if not c: raise ValueError("no close for "+symbol)
    p=float(c[-1]); prev=float(c[-2]) if len(c)>1 else p
    return p, ((p/prev)-1)*100 if prev else 0
def fmt(v,n=2): return format(v,",."+str(n)+"f")
def pct(v): return ("+" if v>=0 else "")+format(v,".2f")+"%"
def news(q,limit=3):
    u="https://news.google.com/rss/search?"+urllib.parse.urlencode({"q":q+" when:1d","hl":"en-AU","gl":"AU","ceid":"AU:en"})
    root=ET.fromstring(get(u)); out=[]
    for it in root.findall("./channel/item")[:limit]:
        title=(it.findtext("title") or "").strip(); link=(it.findtext("link") or "").strip(); se=it.find("source")
        source=(se.text if se is not None else "Market news") or "Market news"
        if title and link: out.append({"title":re.sub(r"\\s+"," ",title),"link":link,"source":source.strip()})
    return out
def main():
    now=datetime.now(timezone.utc).astimezone(); syms={"asx200":"^AXJO","sp500":"^GSPC","vix":"^VIX","oil":"CL=F","gold":"GC=F","us10":"^TNX","aud":"AUDUSD=X"}; m={}
    for k,s in syms.items():
        try: m[k]=dict(zip(("price","pct"),yahoo(s)))
        except Exception as e: print("Warning:",s,e)
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
    seen=set()
    for q in ("ASX Australian share market","US stocks S&P 500 Nasdaq","markets bonds oil gold"):
        for x in news(q):
            key=re.sub(r"[^a-z0-9]+","",x["title"].lower())
            if key in seen: continue
            seen.add(key); cards.append({"tag":"NEWS / MARKET INTELLIGENCE","time":d,"title":x["title"],"dek":x["source"]+" • Latest market coverage.","data":[["SOURCE",x["source"]],["TYPE","Market news"],["STATUS","Latest"]],"insight":"Read the headline in context: identify the directly exposed asset, sector, rate or currency and whether the market has already reacted.","source":x["source"],"link":x["link"],"rank":88})
            if len(cards)>=9: break
        if len(cards)>=9: break
    if len(cards)<8: raise SystemExit("Refusing to publish: fewer than 8 cards")
    def t(x): return {"value":x["value"],"direction":"up" if x["pct"]>=0 else "down","change":pct(x["pct"])}
    feed={"version":"1.2.0","updatedAt":now.isoformat(timespec="seconds"),"tickers":{},"cards":cards}
    feed["tickers"]={"asx200":t({"value":fmt(a["price"],1),"pct":a["pct"]}),"sp500":t({"value":fmt(sp["price"],2),"pct":sp["pct"]}),"vix":t({"value":fmt(vx["price"],2),"pct":vx["pct"]}),"oil":t({"value":"US$"+fmt(oil["price"],2),"pct":oil["pct"]}),"gold":t({"value":"US$"+fmt(gold["price"],2),"pct":gold["pct"]}),"us10":t({"value":fmt(rate["price"],2)+"%","pct":rate["pct"]}),"aud":t({"value":fmt(aud["price"],4),"pct":aud["pct"]})}
    FEED.write_text(json.dumps(feed,indent=2,ensure_ascii=False)+"\\n"); print("Wrote",len(cards),"cards at",feed["updatedAt"])
if __name__=="__main__": main()