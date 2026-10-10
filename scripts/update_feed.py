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

def news_insight(item):
    title=item.get("title","").lower()
    if any(w in title for w in ("ipo","listing","market debut","shares plunge","stock market listing")):
        return "The key test is the gap between the story investors are buying and the price being paid. Watch liquidity, valuation assumptions and any updated company disclosures; early trading alone does not establish fair value."
    if any(w in title for w in ("earnings","results","revenue","profit","guidance","forecast","outlook")):
        return "For this development, separate reported performance from expectations. Revenue and profit matter, but guidance, margins and cash conversion help show whether the change is likely to persist. Check the company's release before drawing a conclusion."
    if any(w in title for w in ("oil","crude","energy","opec","gas prices")):
        return "Energy news can flow through to fuel costs, inflation expectations and company margins. Watch whether the reported development changes expected supply or demand, then compare oil's reaction with bond yields and energy shares."
    if any(w in title for w in ("rates","yield","inflation","reserve bank","federal reserve","central bank")):
        return "The market impact depends on how this changes the expected path of interest rates, not just the headline. Watch government bond yields and rate expectations for confirmation, and consider the knock-on effect on currency and equity valuations."
    if any(w in title for w in ("artificial intelligence"," ai ","nvidia","microsoft","semiconductor","data centre","datacenter","cloud")):
        return "For AI-related businesses, distinguish demand headlines from realised revenue and returns on investment. Watch customer spending, order conversion, margins and capital expenditure; strong thematic interest alone does not determine whether a valuation is attractive."
    if any(w in title for w in ("bank","lending","mortgage","credit","bad debt","loan")):
        return "For banks, the important transmission channels are net interest margins, loan growth, funding costs and credit quality. Watch management guidance and arrears data to judge whether the development affects earnings or risk."
    if any(w in title for w in ("property","real estate","reit","office","housing")):
        return "Property is sensitive to financing costs, occupancy and the income outlook. Watch bond yields alongside rental growth, vacancies and refinancing needs; the impact differs materially between property sectors."
    return "Start with the primary source and identify what has actually changed: earnings, expected cash flows, rates, regulation or sentiment. The next useful signal is a measurable follow-up—company guidance, market pricing or a new data release—rather than the headline alone."

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
def next_macro_watch(now):
    """Pull upcoming catalysts from official Australian and US release calendars.

    Calendar requests are best-effort: if a provider changes its page layout or
    is temporarily unavailable, the feed still publishes with a clearly labelled
    official-calendar fallback rather than stale hard-coded dates.
    """
    from html.parser import HTMLParser
    from calendar import month_abbr

    class TextParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.parts = []
        def handle_data(self, data):
            if data.strip():
                self.parts.append(data.strip())

    class CellParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.cells = []
            self.active = False
            self.buf = []
        def handle_starttag(self, tag, attrs):
            if tag.lower() == "td":
                self.active = True
                self.buf = []
        def handle_endtag(self, tag):
            if tag.lower() == "td" and self.active:
                self.cells.append(" ".join(self.buf))
                self.active = False
        def handle_data(self, data):
            if self.active and data.strip():
                self.buf.append(data.strip())

    today = now.date()
    events = []

    def add_event(date_text, label, url, time_text=""):
        try:
            date = datetime.strptime(date_text, "%d %B %Y").date()
        except ValueError:
            return
        if date >= today:
            when = date.strftime("%a %-d %b")
            if time_text:
                when += " " + time_text
            events.append((date, label, when, url))

    # New York Fed calendar: the month-specific official calendar exposes each
    # release in its own table cell. Check this month and the next two months.
    month_start = today.replace(day=1)
    for offset in range(3):
        month_index = month_start.month - 1 + offset
        year = month_start.year + month_index // 12
        month = month_index % 12 + 1
        url = "https://www.newyorkfed.org/research/calendars/i-%s%02d.html" % (month_abbr[month].lower(), year % 100)
        try:
            parser = CellParser()
            parser.feed(get(url).decode("utf-8", "ignore"))
            for cell in parser.cells:
                m = re.match(r"^\s*(\d{1,2})\s+(.*)$", cell, re.S)
                if not m:
                    continue
                day = int(m.group(1))
                body = re.sub(r"\s+", " ", m.group(2)).strip()
                if not body:
                    continue
                date_text = "%02d %s %04d" % (day, month_abbr[month], year)
                # Keep the most market-sensitive scheduled release labels.
                labels = (
                    (("Consumer Price Index", "CPI"), "US CPI"),
                    (("Employment Situation", "Nonfarm Payroll", "Employment Report"), "US jobs report"),
                    (("Advance Retail Sales", "Retail Sales"), "US retail sales"),
                    (("Producer Price Index", "PPI"), "US PPI inflation"),
                    (("Personal Income and the PCE Deflator", "PCE Deflator"), "US PCE inflation"),
                    (("Gross Domestic Product",), "US GDP"),
                    (("ISM Manufacturing",), "US ISM manufacturing survey"),
                    (("ISM Non-Manufacturing", "ISM Services"), "US ISM services survey"),
                )
                for phrases, label in labels:
                    found = next((p for p in phrases if p.lower() in body.lower()), None)
                    if found:
                        tm = re.search(r"\((\d{1,2}:\d{2})\)", body)
                        time_text = (tm.group(1) + " ET") if tm else ""
                        # strptime accepts abbreviated month names through %b.
                        try:
                            date = datetime.strptime(date_text, "%d %b %Y").date()
                        except ValueError:
                            continue
                        if date >= today:
                            when = date.strftime("%a %-d %b") + ((" " + time_text) if time_text else "")
                            events.append((date, label, when, url))
                        break
        except Exception as e:
            print("Warning: US release calendar unavailable", url, e)

    # RBA calendar: find upcoming monetary-policy minutes and decision statements.
    rba_url = "https://www.rba.gov.au/schedules-events/calendar.html?topics=monetary-policy-board"
    try:
        parser = TextParser()
        parser.feed(get(rba_url).decode("utf-8", "ignore"))
        rba_text = " ".join(parser.parts)
        for pattern, label in (
            (r"Minutes of the [A-Za-z]+ \d{4} Monetary Policy Board Meeting", "RBA monetary-policy minutes"),
            (r"Monetary Policy Decision Statement", "RBA monetary-policy decision"),
        ):
            for match in re.finditer(pattern, rba_text, re.I):
                tail = rba_text[match.end():match.end() + 240]
                dm = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", tail)
                if dm:
                    date_text = "%s %s %s" % (dm.group(1), dm.group(2), dm.group(3))
                    tm = re.search(r"(\d{1,2}\.\d{2}\s*(?:am|pm)\s*A[ES]T)", tail, re.I)
                    add_event(date_text, label, rba_url, tm.group(1) if tm else "")
                    break
    except Exception as e:
        print("Warning: RBA calendar unavailable", e)

    # ABS future releases: the date precedes the release heading on its calendar.
    abs_url = "https://www.abs.gov.au/release-calendar/future-releases"
    try:
        parser = TextParser()
        parser.feed(get(abs_url).decode("utf-8", "ignore"))
        abs_text = " ".join(parser.parts)
        date_re = re.compile(r"(?:Monday|Tuesday|Wednesday|Thursday|Friday),?\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})\s+(\d{1,2}:\d{2}\s*(?:am|pm)\s*AEDT)", re.I)
        for match in date_re.finditer(abs_text):
            tail = abs_text[match.end():match.end() + 260]
            label = None
            if re.search(r"Labour Force, Australia", tail, re.I):
                label = "Australian Labour Force"
            elif re.search(r"Consumer Price Index, Australia", tail, re.I):
                label = "Australian CPI"
            elif re.search(r"Wage Price Index, Australia", tail, re.I):
                label = "Australian wages"
            if label:
                date_text = "%s %s %s" % (match.group(1), match.group(2), match.group(3))
                add_event(date_text, label, abs_url, match.group(4))
    except Exception as e:
        print("Warning: ABS release calendar unavailable", e)

    # Deduplicate identical event/date pairs, then surface the next few catalysts.
    unique = {}
    for event in sorted(events, key=lambda item: (item[0], item[1])):
        unique[(event[0], event[1])] = event
    upcoming = sorted(unique.values(), key=lambda item: (item[0], item[1]))[:3]
    if upcoming:
        descriptions = [label + ": " + when for _, label, when, _ in upcoming]
        urls = []
        for _, _, _, url in upcoming:
            if url not in urls:
                urls.append(url)
        return ("; ".join(descriptions) + ". Watch inflation and labour-market surprises against bond-yield pricing; dates and times can change, so verify with the official calendars.",
                urls[0])

    return ("Upcoming catalyst dates could not be verified from the live calendars. Check the official RBA, ABS and New York Fed release calendars before trading around an event.",
            "https://www.rba.gov.au/schedules-events/calendar.html?topics=monetary-policy-board")

def daily_narrative(a, sp, vx, oil, gold, rate, aud, nasdaq, now):
    nq = nasdaq or {"price": None, "pct": None}
    if nq["pct"] is not None and rate["pct"] >= 0.25 and nq["pct"] <= -0.5:
        link = ("US 10-year yields rose " + pct(rate["pct"]) + " while the Nasdaq fell " + pct(nq["pct"]) +
                ". That combination is consistent with higher discount rates weighing on long-duration growth valuations, although one session cannot establish causation.")
    elif nq["pct"] is not None and rate["pct"] < 0 and nq["pct"] > 0:
        link = ("US 10-year yields fell " + pct(rate["pct"]) + " while the Nasdaq rose " + pct(nq["pct"]) +
                ". Lower yields can support growth-stock valuations, but check whether earnings expectations and market breadth confirm the move.")
    elif nq["pct"] is not None:
        link = ("The S&P 500 moved " + pct(sp["pct"]) + ", the Nasdaq " + pct(nq["pct"]) +
                ", and the US 10-year yield " + pct(rate["pct"]) + ". Read them together: yields affect discount rates, while index breadth and earnings expectations help explain whether equity moves are durable.")
    else:
        link = ("The S&P 500 moved " + pct(sp["pct"]) + ", the VIX " + pct(vx["pct"]) +
                ", and the US 10-year yield " + pct(rate["pct"]) + ". Without a verified Nasdaq close, avoid claiming a specific technology-stock/yield relationship.")
    if oil["pct"] > 1 and rate["pct"] > 0:
        oil_note = " Oil also rose " + pct(oil["pct"]) + "; if sustained, higher energy costs can complicate the inflation outlook and keep yields under pressure."
    elif oil["pct"] < -1:
        oil_note = " Oil fell " + pct(oil["pct"]) + ", which may ease some near-term inflation pressure if the move persists."
    else:
        oil_note = " Oil moved " + pct(oil["pct"]) + "; a single session is not enough to infer a change in the inflation trend."
    watch, watch_url = next_macro_watch(now)
    return {
        "tag": "DAILY CROSS-ASSET NARRATIVE",
        "time": now.strftime("%-d %b").upper(),
        "title": "Rates, equities and inflation: the signals to connect",
        "dek": "A daily read-through across equity direction, bond yields, volatility and energy prices—not a standalone buy or sell signal.",
        "data": [["S&P 500", pct(sp["pct"])], ["US 10Y YIELD", fmt(rate["price"], 2) + "%"],
                 ["NASDAQ", pct(nq["pct"]) if nq["pct"] is not None else "Unavailable"]],
        "insight": link + oil_note + " Next release to watch: " + watch,
        "source": "Market Mind • Yahoo Finance • official calendars",
        "link": watch_url,
        "rank": 101
    }

def main():
    now=datetime.now(timezone.utc).astimezone(); syms={"asx200":"^AXJO","sp500":"^GSPC","vix":"^VIX","oil":"CL=F","gold":"GC=F","us10":"^TNX","aud":"AUDUSD=X"}; m={}
    nasdaq=None
    try:
        np,nchg=yahoo("^IXIC"); nasdaq={"price":np,"pct":nchg}
    except Exception as e: print("Warning: Nasdaq daily move unavailable",e)
    for k,s in syms.items():
        try: m[k]=dict(zip(("price","pct"),yahoo(s)))
        except Exception as e: print("Warning:",s,e)
    # Dynamic candidate pool
    stocks={}
    for k,sym in {"BHP":"BHP.AX","CBA":"CBA.AX","NVDA":"NVDA","MSFT":"MSFT"}.items():
        try:
            p,chg=yahoo(sym); hist=history(sym)
            stocks[k]={"symbol":sym,"price":p,"pct":chg,"history":hist}
        except Exception as e: print("Warning:",sym,e)
    if len(m)<7: raise SystemExit("Refusing to publish: incomplete market data")
    a,sp,vx,oil,gold,rate,aud=[m[k] for k in ("asx200","sp500","vix","oil","gold","us10","aud")]
    # Real monthly closes for the US market comparison chart; omit chart if source data fails.
    us_history={}
    for key,symbol in (("sp500","^GSPC"),("nasdaq","^IXIC")):
        try:
            rows=history(symbol)
            if len(rows)>=2: us_history[key]=rows
        except Exception as e: print("Warning: US history",symbol,e)
    d=now.strftime("%-d %b").upper()
    cards=[
      {"tag":"ASX 200","time":d,"title":"ASX 200 is "+("higher" if a["pct"]>=0 else "lower"),"dek":"The ASX 200 is %s, %s on the latest session."%(fmt(a["price"],1),pct(a["pct"])),"data":[["ASX 200",fmt(a["price"],1)],["Session",pct(a["pct"])],["Context","Australian equities"]],"insight":("The ASX 200 rose "+pct(a["pct"])+" while the Australian dollar moved "+pct(aud["pct"])+". Compare sector breadth next: a headline index can be driven by a small number of large companies, so check banks, materials and property before calling it a broad rally." if a["pct"]>=0 else "The ASX 200 fell "+pct(a["pct"])+" while the Australian dollar moved "+pct(aud["pct"])+". Check whether banks, materials and property are all weaker or whether the index decline is concentrated. Sector breadth helps distinguish a broad risk-off session from rotation."),"source":"Yahoo Finance","rank":100},
      {"tag":"US MARKETS","time":d,"title":"US equities are "+("higher" if sp["pct"]>=0 else "lower"),"dek":"The S&P 500 is %s, %s on the latest session."%(fmt(sp["price"],2),pct(sp["pct"])),"data":[["S&P 500",fmt(sp["price"],2)],["Session",pct(sp["pct"])],["VIX",fmt(vx["price"],2)]],"insight":(("The S&P 500 "+("rose " if sp["pct"]>=0 else "fell ")+pct(sp["pct"])+", while the VIX "+("rose " if vx["pct"]>=0 else "fell ")+pct(vx["pct"])+". ")+("A rising index with falling volatility is consistent with calmer near-term risk pricing, but does not prove the rally is broad-based." if sp["pct"]>=0 and vx["pct"]<0 else "The combination is worth watching: check Treasury yields and whether the Nasdaq confirms the move before inferring a change in market direction.")),"source":"Yahoo Finance","rank":99,"marketHistory":us_history},
      {"tag":"RATES","time":d,"title":"US 10Y yield is "+("rising" if rate["pct"]>=0 else "falling"),"dek":"The US 10-year Treasury yield is about %s%%, %s on the latest session."%(fmt(rate["price"],2),pct(rate["pct"])),"data":[["US 10Y",fmt(rate["price"],2)+"%"],["Session",pct(rate["pct"])],["Risk","Equity valuations"]],"insight":("The US 10-year yield is "+fmt(rate["price"],2)+"%, with the latest move "+pct(rate["pct"])+". Higher yields can pressure long-duration equity valuations and property financing costs, all else equal. Watch whether the move coincides with stronger growth data, firmer inflation expectations or changing rate-cut pricing."),"source":"Yahoo Finance","rank":98},
      {"tag":"COMMODITIES","time":d,"title":"Oil is "+("higher" if oil["pct"]>=0 else "lower"),"dek":"WTI crude is about US$%s, %s on the latest session."%(fmt(oil["price"],2),pct(oil["pct"])),"data":[["WTI","US$"+fmt(oil["price"],2)],["Session",pct(oil["pct"])],["Theme","Inflation / growth"]],"insight":("WTI moved "+pct(oil["pct"])+" in the latest session. For investors, the important transmission channel is whether energy prices stay elevated long enough to affect fuel costs, company margins and inflation expectations. Compare the move with gold and bond yields rather than extrapolating one session."),"source":"Yahoo Finance","rank":96},
      {"tag":"GOLD","time":d,"title":"Gold is "+("higher" if gold["pct"]>=0 else "lower"),"dek":"Gold is about US$%s, %s on the latest session."%(fmt(gold["price"],2),pct(gold["pct"])),"data":[["Gold","US$"+fmt(gold["price"],2)],["Session",pct(gold["pct"])],["AUD/USD",fmt(aud["price"],4)]],"insight":("Gold moved "+pct(gold["pct"])+" while the US 10-year yield moved "+pct(rate["pct"])+" and AUD/USD moved "+pct(aud["pct"])+". Those cross-currents matter: gold can respond to real yields, currency moves and demand for defensive assets. One session alone cannot identify the driver."),"source":"Yahoo Finance","rank":94},
      {"tag":"CURRENCY","time":d,"title":"Australian dollar is "+("higher" if aud["pct"]>=0 else "lower"),"dek":"AUD/USD is around %s, %s on the latest session."%(fmt(aud["price"],4),pct(aud["pct"])),"data":[["AUD/USD",fmt(aud["price"],4)],["Session",pct(aud["pct"])],["Theme","Global risk / commodities"]],"insight":("AUD/USD moved "+pct(aud["pct"])+" in the latest session. For an Australian investor holding unhedged US assets, a stronger Australian dollar reduces the AUD value of each US dollar of overseas holdings, all else equal; a weaker dollar has the opposite translation effect. Compare the currency move with US equity performance."),"source":"Yahoo Finance","rank":90},
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
            seen.add(key); cards.append({"tag":"NEWS / MARKET INTELLIGENCE","time":d,"title":x["title"],"dek":x["source"]+" • Latest market coverage.","data":[["SOURCE",x["source"]],["TYPE","Market news"],["STATUS","Latest"]],"insight":news_insight(x),"source":x["source"],"link":x["link"],"rank":88})
            if len(cards)>=13: break
        if len(cards)>=9: break
    cards.insert(0, daily_narrative(a, sp, vx, oil, gold, rate, aud, nasdaq, now))
    if len(cards)<10: raise SystemExit("Refusing to publish: fewer than 10 cards")
    def t(x): return {"value":x["value"],"direction":"up" if x["pct"]>=0 else "down","change":pct(x["pct"])}
    feed={"version":"1.3.3","updatedAt":now.isoformat(timespec="seconds"),"tickers":{},"cards":cards}
    feed["tickers"]={"asx200":t({"value":fmt(a["price"],1),"pct":a["pct"]}),"sp500":t({"value":fmt(sp["price"],2),"pct":sp["pct"]}),"vix":t({"value":fmt(vx["price"],2),"pct":vx["pct"]}),"oil":t({"value":"US$"+fmt(oil["price"],2),"pct":oil["pct"]}),"gold":t({"value":"US$"+fmt(gold["price"],2),"pct":gold["pct"]}),"us10":t({"value":fmt(rate["price"],2)+"%","pct":rate["pct"]}),"aud":t({"value":fmt(aud["price"],4),"pct":aud["pct"]})}
    FEED.write_text(json.dumps(feed,indent=2,ensure_ascii=False)+"\n"); print("Wrote",len(cards),"cards at",feed["updatedAt"])
if __name__=="__main__": main()