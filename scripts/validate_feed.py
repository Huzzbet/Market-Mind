import json, math, re
from datetime import datetime, timezone, timedelta
from pathlib import Path
feed=json.loads(Path("data/feed.json").read_text(encoding="utf-8"))
now=datetime.now(timezone.utc)
try: updated=datetime.fromisoformat(feed.get("updatedAt","").replace("Z","+00:00"))
except ValueError: raise SystemExit("FAIL: invalid updatedAt")
if updated.tzinfo is None: raise SystemExit("FAIL: updatedAt must include timezone")
age=now-updated.astimezone(timezone.utc)
if age < timedelta(minutes=-10) or age > timedelta(hours=8): raise SystemExit(f"FAIL: feed generation outside six-hour refresh window ({age})")
cards=feed.get("cards")
if not isinstance(cards,list) or len(cards)<5: raise SystemExit("FAIL: fewer than five cards")
errors=[]
for n,c in enumerate(cards,1):
    for key in ("tag","title","dek","data","insight","source"):
        if not c.get(key): errors.append(f"card {n}: missing {key}")
    if c.get("link") and not re.match(r"^https://",str(c["link"]),re.I): errors.append(f"card {n}: source link is not HTTPS")
    pub=c.get("sourcePublishedAt")
    if pub:
        try: dt=datetime.fromisoformat(pub.replace("Z","+00:00"))
        except ValueError: errors.append(f"card {n}: invalid sourcePublishedAt"); continue
        if dt.tzinfo is None: errors.append(f"card {n}: sourcePublishedAt lacks timezone")
        elif dt>now+timedelta(minutes=10): errors.append(f"card {n}: source time is in future")
        elif dt<now-timedelta(days=2): errors.append(f"card {n}: stale source")
    st=c.get("stock")
    if st:
        p,ch=st.get("price"),st.get("pct")
        if p is not None and (not isinstance(p,(int,float)) or not math.isfinite(p) or p<=0): errors.append(f"card {n}: invalid stock price")
        if ch is not None and (not isinstance(ch,(int,float)) or not math.isfinite(ch) or abs(ch)>50): errors.append(f"card {n}: implausible daily move")
if errors: raise SystemExit("\n".join("FAIL: "+e for e in errors))
print(f"Validated {len(cards)} cards; generated {age.total_seconds()/3600:.2f} hours ago.")
for c in cards:
    if c.get("stock") and not c.get("sourcePublishedAt"): print("INFO: no fresh verified catalyst; explicitly labelled:",c.get("title"))
