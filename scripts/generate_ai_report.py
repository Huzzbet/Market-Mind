#!/usr/bin/env python3
"""Use the OpenAI API to add a concise, evidence-aware daily research report to Market Mind."""
import json
import os
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

FEED = Path("data/feed.json")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

def call_openai(payload):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise SystemExit("OPENAI_API_KEY secret is missing. Add it in GitHub repository Settings > Secrets and variables > Actions.")
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as response:
        return json.loads(response.read().decode())

def main():
    feed = json.loads(FEED.read_text(encoding="utf-8"))
    base_cards = feed.get("cards", [])
    # Give the model a compact, source-grounded snapshot. It must not invent missing facts.
    snapshot = []
    for c in base_cards:
        snapshot.append({
            "tag": c.get("tag"), "title": c.get("title"), "dek": c.get("dek"),
            "insight": c.get("insight"), "source": c.get("source"),
            "link": c.get("link"), "publishedAt": c.get("sourcePublishedAt"),
            "data": c.get("data", [])[:5],
        })
    prompt = """You are the research editor for Market Mind, an Australian investor's swipeable market-intelligence app.
Create 4 to 6 additional cards for today's report using ONLY the supplied feed snapshot.
Prioritise: (1) ASX company catalysts and broker upgrades/downgrades, (2) US equities and major company catalysts,
(3) macro/rates/FX/commodities links, (4) what to watch next.
Do not browse or claim to have checked anything outside this snapshot. Do not invent figures, events, dates, consensus,
broker calls, or causal explanations. If the supplied snapshot does not support a claim, omit it. Prefer distinct insights
rather than repeating existing cards. These are research prompts, not buy/sell instructions.
Return JSON only: {"cards":[{"tag":"AI DAILY REPORT / ASX or US or MACRO","title":"short factual headline",
"dek":"one sentence summary","data":[["EVIDENCE","..."],["STATUS","Verified in feed"]],
"insight":"2-4 concise sentences distinguishing fact from interpretation and stating what to watch",
"source":"source label from the supplied snapshot","link":"exact HTTPS source link copied from the snapshot or null",
"sourcePublishedAt":"exact timestamp copied from the snapshot or null",
"whyItMatters":"one concise investor-relevant sentence",
"investmentOpportunity":"Research angle: ...; no trade instruction.",
"opportunityType":"RESEARCH"}]}
Only use a source link and timestamp if they belong to the specific evidence for that card. Cards based on broad cross-asset readings may use source "Market Mind • supplied market feed" and link null. Keep all text concise."""
    payload = {
        "model": MODEL,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": "Follow the supplied data strictly. Never fabricate market facts or sources."},
            {"role": "user", "content": prompt + "\n\nSUPPLIED FEED SNAPSHOT:\n" + json.dumps(snapshot, ensure_ascii=False)},
        ],
    }
    response = call_openai(payload)
    content = response["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    generated = parsed.get("cards", [])
    if not isinstance(generated, list) or not 3 <= len(generated) <= 6:
        raise SystemExit("AI report failed validation: expected 3-6 cards.")
    allowed = {"tag", "title", "dek", "data", "insight", "source", "link", "sourcePublishedAt",
               "whyItMatters", "investmentOpportunity", "opportunityType"}
    checked = []
    now = datetime.now(ZoneInfo("Australia/Melbourne"))
    for card in generated:
        if not isinstance(card, dict):
            continue
        card = {k: v for k, v in card.items() if k in allowed}
        for field in ("tag", "title", "dek", "insight", "source"):
            if not isinstance(card.get(field), str) or not card[field].strip():
                raise SystemExit("AI report failed validation: missing " + field)
        if card.get("link") and not str(card["link"]).startswith("https://"):
            card["link"] = None
        if not isinstance(card.get("data"), list):
            card["data"] = [["STATUS", "Research prompt"]]
        card["time"] = now.strftime("%d %b").upper()
        card["rank"] = 89
        card["reportType"] = "chatgpt-daily-report"
        checked.append(card)
    if len(checked) < 3:
        raise SystemExit("AI report failed validation: fewer than three usable cards.")
    # Keep core market cards and their existing order; place report cards immediately after the narrative.
    feed["cards"] = base_cards[:1] + checked + base_cards[1:]
    feed["aiReport"] = {
        "generatedAt": now.isoformat(timespec="seconds"),
        "model": MODEL,
        "cardsAdded": len(checked),
        "type": "OpenAI API-generated daily research report",
    }
    FEED.write_text(json.dumps(feed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Added", len(checked), "AI report cards using", MODEL)

if __name__ == "__main__":
    main()
