#!/usr/bin/env python3
import json, re, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo
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
    # No hard-coded consensus fallbacks: unavailable data must stay visibly unavailable.
    try:
        html=get("https://stockanalysis.com/"+slug+"/forecast/").decode("utf-8","ignore")
        m=re.search(r'consensus rating of "([^"]+)"',html,re.I)
        p=re.search(r'average price target (?:is|of)\s*\$([0-9.,]+)\b',html,re.I)
        if not p: p=re.search(r'Price Target[^$]{0,120}\$([0-9.,]+)\b',html,re.I)
        n=re.search(r'According to ([0-9]+) analysts',html,re.I)
        out={"rating":m.group(1) if m else None,"target":float(p.group(1).replace(",","")) if p else None,"analysts":int(n.group(1)) if n else None,"source":"Stock Analysis"}
        return {"rating":out["rating"],"target":out["target"],"analysts":out["analysts"],"source":"Stock Analysis" if out["rating"] or out["target"] else "Unavailable"}
    except Exception as e:
        print("Warning: consensus",slug,e)
        return {"rating":None,"target":None,"analysts":None,"source":"Unavailable"}

def fmt(v,n=2): return format(v,",."+str(n)+"f")
def pct(v): return ("+" if v>=0 else "")+format(v,".2f")+"%"
def stock_title(label,headline):
    names={"BHP":"BHP","RIO":"Rio Tinto","FMG":"Fortescue","CBA":"CBA","NAB":"NAB","WES":"Wesfarmers","CSL":"CSL","GMG":"Goodman Group","MQG":"Macquarie Group","TLS":"Telstra","NVDA":"Nvidia","MSFT":"Microsoft"}
    if headline == "No verified fresh company-specific catalyst found today":
        return names.get(label,label)+" · No verified fresh catalyst"
    return names.get(label,label)+" · "+catalyst_text(headline)

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
    names={"BHP":["bhp"],"RIO":["rio tinto","rio"],"FMG":["fortescue","fmg"],"CBA":["cba","commonwealth bank"],"NAB":["nab","national australia bank"],"WES":["wesfarmers","bunnings","kmart"],"CSL":["csl"],"GMG":["goodman group","goodman"],"MQG":["macquarie"],"TLS":["telstra"],"NVDA":["nvidia","nvda"],"MSFT":["microsoft","msft"]}
    if not any(n in title for n in names.get(label,[])): return -100
    generic=("stock price, news, quote and history","stock forecasts","stock forecast","share price, news","stock price today","price, news, quote and history","stock analysis forecast")
    if any(term in title for term in generic): return -100
    score=20
    strong={"results":10,"earnings":10,"guidance":10,"profit":9,"revenue":8,"dividend":8,"upgrade":9,"downgrade":9,"price target":9,"target":6,"contract":8,"deal":8,"acquisition":9,"merger":9,"buyback":8,"outlook":8,"forecast":7,"production":7,"shipments":6,"order":7,"partnership":7,"regulatory":8,"approval":7,"project":6,"site visit":5,"cash flow":6,"margin":7}
    for word,weight in strong.items():
        if word in title: score+=weight
    weak={"best stock":-9,"should i buy":-9,"how much":-8,"passive income":-7,"is it a buy":-7,"top stocks":-7,"could":-3,"what you need to know":-5,"stock to buy":-8}
    for word,weight in weak.items():
        if word in title: score+=weight
    if any(x in source for x in ("reuters","afr","market index","marketscreener","fnarena","investsmart")): score+=5
    if "motley fool" in source or "simply wall st" in source: score-=2
    if "dealroom" in source: score-=5
    if label in ("BHP","CBA") and any(x in title for x in ("broker","ubs","macquarie","bofa","jpmorgan","morgan stanley","jefferies","rbc","deutsche bank")): score+=5
    if len(title)>115: score-=1
    return score
def news(q,limit=3):
    u="https://news.google.com/rss/search?"+urllib.parse.urlencode({"q":q+" when:1d","hl":"en-AU","gl":"AU","ceid":"AU:en"})
    root=ET.fromstring(get(u)); out=[]
    cutoff=datetime.now(timezone.utc)-timedelta(hours=36)
    for it in root.findall("./channel/item"):
        title=(it.findtext("title") or "").strip()
        link=(it.findtext("link") or "").strip()
        se=it.find("source")
        source=(se.text if se is not None else "Market news") or "Market news"
        raw_date=(it.findtext("pubDate") or "").strip()
        try:
            published=parsedate_to_datetime(raw_date) if raw_date else None
            if published and published.tzinfo is None: published=published.replace(tzinfo=timezone.utc)
            if published: published=published.astimezone(timezone.utc)
        except (TypeError,ValueError,OverflowError): published=None
        if not published or published<cutoff or published>datetime.now(timezone.utc)+timedelta(minutes=10): continue
        if title and link:
            out.append({"title":re.sub(r"\\s+"," ",title),"link":link,"source":source.strip(),"publishedAt":published.isoformat(timespec="seconds")})
        if len(out)>=limit: break
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


def investment_lens(card):
    """Create a cautious, actionable research angle from each card's stated data."""
    tag=(card.get("tag") or "").upper()
    title=(card.get("title") or "").lower()
    rows={str(x[0]).upper():str(x[1]) for x in card.get("data",[]) if isinstance(x,list) and len(x)>1}
    if "NARRATIVE" in tag:
        return {
            "why":"Equities, yields and energy prices can tell different stories. The relationship between them is more useful than any one headline move.",
            "opportunity":"Research angle: compare equity breadth with real yields and earnings revisions. Avoid calling a risk-on or risk-off regime from one session alone.",
            "stance":"MONITOR"
        }
    if "ASX 200" in tag:
        return {
            "why":"The index can be driven by a handful of large miners and banks, so the headline return may not reflect the wider market.",
            "opportunity":"Research angle: compare banks, materials, property and smaller companies with the index. Look for improving breadth and earnings support before identifying candidates.",
            "stance":"RESEARCH"
        }
    if "US MARKETS" in tag:
        return {
            "why":"Index direction alongside volatility helps frame risk appetite, but neither confirms that a move is broad or durable.",
            "opportunity":"Research angle: check equal-weight versus cap-weight performance, sector breadth and earnings revisions. A broadening rally is stronger evidence than index gains alone.",
            "stance":"MONITOR"
        }
    if "RATES" in tag:
        return {
            "why":"Bond yields feed into discount rates, borrowing costs and relative valuations across growth shares, property and bonds.",
            "opportunity":"Research angle: compare quality bond yields with equity earnings yields and property balance sheets. Consider duration only after checking inflation and central-bank expectations.",
            "stance":"COMPARE"
        }
    if "COMMODITIES" in tag:
        return {
            "why":"Oil can affect inflation, transport costs, consumer spending and margins differently across sectors.",
            "opportunity":"Research angle: map beneficiaries and losers across energy producers, airlines, transport and consumer businesses. Confirm whether the move reflects supply, demand or a temporary shock.",
            "stance":"RESEARCH"
        }
    if "GOLD" in tag:
        return {
            "why":"Gold responds to real yields, the US dollar and demand for defensive assets; a daily move alone cannot identify the driver.",
            "opportunity":"Research angle: compare gold with real yields and AUD/USD. For Australian investors, assess currency exposure and portfolio role before considering an allocation.",
            "stance":"COMPARE"
        }
    if "CURRENCY" in tag:
        return {
            "why":"AUD/USD changes the Australian-dollar return on unhedged overseas assets and affects exporters, importers and commodity-linked companies.",
            "opportunity":"Research angle: stress-test existing overseas holdings under a stronger and weaker AUD. Compare hedged and unhedged exposure against the portfolio's time horizon.",
            "stance":"REVIEW"
        }
    if "STOCK INTELLIGENCE" in tag:
        target=next((v for k,v in rows.items() if "TARGET" in k),None)
        rating=rows.get("CONSENSUS","Unavailable")
        price=rows.get("PRICE","Unavailable")
        catalyst=card.get("title","the company")
        stock=card.get("stock") or {}
        upside=stock.get("upside")
        if upside is None:
            upside_text="Consensus target comparison is unavailable"
        else:
            upside_text=("Consensus target is "+format(float(upside),".1f")+"% above" if upside>=0 else "Consensus target is "+format(abs(float(upside)),".1f")+"% below")+" the quoted price"
        return {
            "why":"Price and analyst consensus are reference points, not fair-value proof. The catalyst, earnings durability, balance sheet and valuation determine whether the market is mispricing the business.",
            "opportunity":"Research angle: "+upside_text+"; test the assumptions behind the "+rating+" consensus and verify the linked company-specific catalyst. Compare a downside case with expected returns before treating it as an opportunity.",
            "stance":"INVESTIGATE"
        }
    if "NEWS" in tag:
        return {
            "why":"A headline matters to investors only if it changes expected cash flows, risk, valuation or market pricing.",
            "opportunity":"Research angle: verify the primary source, identify the companies and sectors affected, then watch for a measurable follow-through in guidance, prices or earnings estimates. No trade is implied by the headline alone.",
            "stance":"VERIFY"
        }
    return {
        "why":"Market moves need to be connected to cash flows, valuation and risk before they can inform a decision.",
        "opportunity":"Research angle: identify the affected assets, test the key assumption and compare downside with potential return before acting.",
        "stance":"RESEARCH"
    }

def main():
    now=datetime.now(ZoneInfo("Australia/Melbourne")); syms={"asx200":"^AXJO","sp500":"^GSPC","vix":"^VIX","oil":"CL=F","gold":"GC=F","us10":"^TNX","aud":"AUDUSD=X"}; m={}
    nasdaq=None
    try:
        np,nchg=yahoo("^IXIC"); nasdaq={"price":np,"pct":nchg}
    except Exception as e: print("Warning: Nasdaq daily move unavailable",e)
    for k,s in syms.items():
        try: m[k]=dict(zip(("price","pct"),yahoo(s)))
        except Exception as e: print("Warning:",s,e)
    # Dynamic candidate pool
    stocks={}
    for k,sym in {"BHP":"BHP.AX","RIO":"RIO.AX","FMG":"FMG.AX","CBA":"CBA.AX","NAB":"NAB.AX","WES":"WES.AX","CSL":"CSL.AX","GMG":"GMG.AX","MQG":"MQG.AX","TLS":"TLS.AX","NVDA":"NVDA","MSFT":"MSFT"}.items():
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
    asx_history=[]
    try:
        asx_history=history("^AXJO")
        if len(asx_history)<2: asx_history=[]
    except Exception as e: print("Warning: ASX history unavailable",e)
    d=now.strftime("%-d %b").upper()
    cards=[
      {"tag":"ASX 200","time":d,"title":"ASX 200 is "+("higher" if a["pct"]>=0 else "lower"),"dek":"The ASX 200 is %s, %s on the latest session."%(fmt(a["price"],1),pct(a["pct"])),"data":[["ASX 200",fmt(a["price"],1)],["Session",pct(a["pct"])],["Context","Australian equities"]],"insight":("The ASX 200 rose "+pct(a["pct"])+" while the Australian dollar moved "+pct(aud["pct"])+". Compare sector breadth next: a headline index can be driven by a small number of large companies, so check banks, materials and property before calling it a broad rally." if a["pct"]>=0 else "The ASX 200 fell "+pct(a["pct"])+" while the Australian dollar moved "+pct(aud["pct"])+". Check whether banks, materials and property are all weaker or whether the index decline is concentrated. Sector breadth helps distinguish a broad risk-off session from rotation."),"source":"Yahoo Finance","rank":100,"marketHistory":{"asx200":asx_history}},
      {"tag":"US MARKETS","time":d,"title":"US equities are "+("higher" if sp["pct"]>=0 else "lower"),"dek":"The S&P 500 is %s, %s on the latest session."%(fmt(sp["price"],2),pct(sp["pct"])),"data":[["S&P 500",fmt(sp["price"],2)],["Session",pct(sp["pct"])],["VIX",fmt(vx["price"],2)]],"insight":(("The S&P 500 "+("rose " if sp["pct"]>=0 else "fell ")+pct(sp["pct"])+", while the VIX "+("rose " if vx["pct"]>=0 else "fell ")+pct(vx["pct"])+". ")+("A rising index with falling volatility is consistent with calmer near-term risk pricing, but does not prove the rally is broad-based." if sp["pct"]>=0 and vx["pct"]<0 else "The combination is worth watching: check Treasury yields and whether the Nasdaq confirms the move before inferring a change in market direction.")),"source":"Yahoo Finance","rank":99,"marketHistory":us_history},
      {"tag":"RATES","time":d,"title":"US 10Y yield is "+("rising" if rate["pct"]>=0 else "falling"),"dek":"The US 10-year Treasury yield is about %s%%, %s on the latest session."%(fmt(rate["price"],2),pct(rate["pct"])),"data":[["US 10Y",fmt(rate["price"],2)+"%"],["Session",pct(rate["pct"])],["Risk","Equity valuations"]],"insight":("The US 10-year yield is "+fmt(rate["price"],2)+"%, with the latest move "+pct(rate["pct"])+". Higher yields can pressure long-duration equity valuations and property financing costs, all else equal. Watch whether the move coincides with stronger growth data, firmer inflation expectations or changing rate-cut pricing."),"source":"Yahoo Finance","rank":98},
      {"tag":"COMMODITIES","time":d,"title":"Oil is "+("higher" if oil["pct"]>=0 else "lower"),"dek":"WTI crude is about US$%s, %s on the latest session."%(fmt(oil["price"],2),pct(oil["pct"])),"data":[["WTI","US$"+fmt(oil["price"],2)],["Session",pct(oil["pct"])],["Theme","Inflation / growth"]],"insight":("WTI moved "+pct(oil["pct"])+" in the latest session. For investors, the important transmission channel is whether energy prices stay elevated long enough to affect fuel costs, company margins and inflation expectations. Compare the move with gold and bond yields rather than extrapolating one session."),"source":"Yahoo Finance","rank":96},
      {"tag":"GOLD","time":d,"title":"Gold is "+("higher" if gold["pct"]>=0 else "lower"),"dek":"Gold is about US$%s, %s on the latest session."%(fmt(gold["price"],2),pct(gold["pct"])),"data":[["Gold","US$"+fmt(gold["price"],2)],["Session",pct(gold["pct"])],["AUD/USD",fmt(aud["price"],4)]],"insight":("Gold moved "+pct(gold["pct"])+" while the US 10-year yield moved "+pct(rate["pct"])+" and AUD/USD moved "+pct(aud["pct"])+". Those cross-currents matter: gold can respond to real yields, currency moves and demand for defensive assets. One session alone cannot identify the driver."),"source":"Yahoo Finance","rank":94},
      {"tag":"CURRENCY","time":d,"title":"Australian dollar is "+("higher" if aud["pct"]>=0 else "lower"),"dek":"AUD/USD is around %s, %s on the latest session."%(fmt(aud["price"],4),pct(aud["pct"])),"data":[["AUD/USD",fmt(aud["price"],4)],["Session",pct(aud["pct"])],["Theme","Global risk / commodities"]],"insight":("AUD/USD moved "+pct(aud["pct"])+" in the latest session. For an Australian investor holding unhedged US assets, a stronger Australian dollar reduces the AUD value of each US dollar of overseas holdings, all else equal; a weaker dollar has the opposite translation effect. Compare the currency move with US equity performance."),"source":"Yahoo Finance","rank":90},
    ]

    stock_cfg={
      "BHP":{"symbol":"BHP.AX","slug":"quote/asx/BHP"},
      "RIO":{"symbol":"RIO.AX","slug":"quote/asx/RIO"},
      "FMG":{"symbol":"FMG.AX","slug":"quote/asx/FMG"},
      "CBA":{"symbol":"CBA.AX","slug":"quote/asx/CBA"},
      "NAB":{"symbol":"NAB.AX","slug":"quote/asx/NAB"},
      "WES":{"symbol":"WES.AX","slug":"quote/asx/WES"},
      "CSL":{"symbol":"CSL.AX","slug":"quote/asx/CSL"},
      "GMG":{"symbol":"GMG.AX","slug":"quote/asx/GMG"},
      "MQG":{"symbol":"MQG.AX","slug":"quote/asx/MQG"},
      "TLS":{"symbol":"TLS.AX","slug":"quote/asx/TLS"},
      "NVDA":{"symbol":"NVDA","slug":"stocks/nvda"},
      "MSFT":{"symbol":"MSFT","slug":"stocks/msft"}
    }
    stock_queries={
      "BHP":["BHP ASX results guidance production iron ore copper","BHP broker upgrade downgrade price target","BHP dividend capital returns company announcement"],
      "RIO":["Rio Tinto ASX results guidance iron ore copper","RIO broker upgrade downgrade price target","Rio Tinto dividend production company announcement"],
      "FMG":["Fortescue ASX results guidance iron ore","FMG broker upgrade downgrade price target","Fortescue production energy company announcement"],
      "CBA":["Commonwealth Bank CBA ASX results guidance net interest margin","CBA broker upgrade downgrade price target","CBA dividend credit quality company announcement"],
      "NAB":["National Australia Bank NAB ASX results guidance","NAB broker upgrade downgrade price target","NAB lending credit quality company announcement"],
      "WES":["Wesfarmers ASX results Bunnings Kmart guidance","WES broker upgrade downgrade price target","Wesfarmers earnings company announcement"],
      "CSL":["CSL Limited ASX results guidance plasma","CSL broker upgrade downgrade price target","CSL earnings margin company announcement"],
      "GMG":["Goodman Group ASX results guidance data centre","GMG broker upgrade downgrade price target","Goodman Group property earnings company announcement"],
      "MQG":["Macquarie Group ASX results guidance earnings","MQG broker upgrade downgrade price target","Macquarie Group asset management company announcement"],
      "TLS":["Telstra ASX results guidance dividend","TLS broker upgrade downgrade price target","Telstra earnings company announcement"],
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
        x=next((item for item in candidates if item.get("catalystScore", -100)>0 and item.get("publishedAt")),None)
        if x is None:
            x={"title":"No verified fresh company-specific catalyst found today","source":"Market Mind","link":None,"publishedAt":None}
        st=stocks.get(label)
        if not st: continue
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
          "tag":"STOCK INTELLIGENCE / "+("AUSTRALIA" if label not in ("NVDA","MSFT") else "US"),
          "time":d,
          "title":stock_title(label,x["title"]),
          "dek":x["source"]+" • "+("A$" if label not in ("NVDA","MSFT") else "US$")+fmt(st["price"],2)+" • "+pct(st["pct"])+" latest session. Consensus: "+con.get("source","Unavailable")+".",
          "data":[["PRICE",("A$" if label not in ("NVDA","MSFT") else "US$")+fmt(st["price"],2)],["CONSENSUS",rating if con.get("rating") else "UNAVAILABLE"],["TARGET · "+str(con.get("analysts") or "—")+" ANALYSTS",(("A$" if label not in ("NVDA","MSFT") else "US$")+target_txt if target_txt!="—" else "Unavailable")]],
          "insight":(("No fresh verified company-specific catalyst was found in the last 36 hours. The quote and long-term chart are market data, not a news catalyst. Check the company ASX announcement page before attributing a move." if not x.get("publishedAt") else "Verified recent headline: "+catalyst_text(x["title"])+". "+news_insight(x)+" Consensus and price history are context, not proof of mispricing."),
          "source":x["source"],
          "link":x["link"],
          "sourcePublishedAt":x.get("publishedAt"),
          "rank":70,
          "stock":{"ticker":st["symbol"],"history":hist,"threeYearReturn":round(((hist[-1][1]/hist[0][1])-1)*100,1) if len(hist)>1 and hist[0][1] else None,"consensus":rating,"target":con.get("target"),"upside":upside,"view":view,"analysts":con.get("analysts")}
        })
    seen=set()
    for q in ("ASX company results announcements broker upgrades downgrades","ASX Australian share market","US stocks S&P 500 Nasdaq","markets bonds oil gold"):
        for x in news(q):
            key=re.sub(r"[^a-z0-9]+","",x["title"].lower())
            if key in seen: continue
            seen.add(key); cards.append({"tag":"NEWS / MARKET INTELLIGENCE","time":d,"title":x["title"],"dek":x["source"]+" • Published "+x["publishedAt"],"data":[["SOURCE",x["source"]],["TYPE","Market news"],["STATUS","Recent · verified timestamp"]],"insight":news_insight(x),"source":x["source"],"link":x["link"],"sourcePublishedAt":x.get("publishedAt"),"rank":88})
            if len(cards)>=13: break
        if len(cards)>=9: break
    cards.insert(0, daily_narrative(a, sp, vx, oil, gold, rate, aud, nasdaq, now))
    for card in cards:
        lens=investment_lens(card)
        card["whyItMatters"]=lens["why"]
        card["investmentOpportunity"]=lens["opportunity"]
        card["opportunityType"]=lens["stance"]
    if len(cards)<10: raise SystemExit("Refusing to publish: fewer than 10 cards")
    def t(x): return {"value":x["value"],"direction":"up" if x["pct"]>=0 else "down","change":pct(x["pct"])}
    feed={"version":"1.4.0","updatedAt":now.isoformat(timespec="seconds"),"timezone":"Australia/Melbourne","tickers":{},"cards":cards}
    feed["tickers"]={"asx200":t({"value":fmt(a["price"],1),"pct":a["pct"]}),"sp500":t({"value":fmt(sp["price"],2),"pct":sp["pct"]}),"vix":t({"value":fmt(vx["price"],2),"pct":vx["pct"]}),"oil":t({"value":"US$"+fmt(oil["price"],2),"pct":oil["pct"]}),"gold":t({"value":"US$"+fmt(gold["price"],2),"pct":gold["pct"]}),"us10":t({"value":fmt(rate["price"],2)+"%","pct":rate["pct"]}),"aud":t({"value":fmt(aud["price"],4),"pct":aud["pct"]})}
    FEED.write_text(json.dumps(feed,indent=2,ensure_ascii=False)+"\n"); print("Wrote",len(cards),"cards at",feed["updatedAt"])
if __name__=="__main__": main()