import requests
import time
import json
import os
from collections import Counter
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta
from openai import OpenAI

# ===================== CONFIG =====================

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

_admin_env = os.getenv("ADMIN_ID")
ADMIN_ID = int(_admin_env) if _admin_env and _admin_env.isdigit() else None

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
client = OpenAI(api_key=OPENAI_API_KEY)

PAIR_FILE = "paired.json"
STATS_FILE = "stats.json"

# ===================== WEB SERVER =====================

app = Flask(__name__)

@app.route("/")
def home():
    return "God's Eye Bot is running."

# ===================== UTILITIES =====================

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def send_message(chat_id, text):
    requests.post(
        f"{BASE_URL}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        },
        timeout=10
    )

def clean(text):
    return "".join(c.lower() for c in text if c.isalnum() or c.isspace())

# ===================== USER STATS =====================

def record_activity(user_id):
    stats = load_json(STATS_FILE)
    now = datetime.utcnow().isoformat()

    uid = str(user_id)
    stats.setdefault(uid, []).append(now)
    save_json(STATS_FILE, stats)

# ===================== DATA SOURCES =====================

def hackernews_data():
    try:
        ids = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=10
        ).json()[:5]

        titles = []
        for i in ids:
            item = requests.get(
                f"https://hacker-news.firebaseio.com/v0/item/{i}.json",
                timeout=10
            ).json()
            if item and "title" in item:
                titles.append(item["title"])
        return titles
    except:
        return []

def devto_data():
    try:
        res = requests.get(
            "https://dev.to/api/articles?top=5",
            timeout=10
        )
        return [a["title"] for a in res.json()[:5]]
    except:
        return []

# ===================== AI LOGIC =====================

def ai_style_trending(texts):
    if not texts:
        return "No strong public trends detected at the moment."

    words = []
    stopwords = {
        "the","and","with","from","this","that","about","into",
        "have","will","they","their","what","when","where",
        "your","been","more","over","after","before","such"
    }

    for text in texts:
        for w in clean(text).split():
            if w not in stopwords and len(w) > 4:
                words.append(w)

    if not words:
        return "Public discussions are currently too scattered to detect a trend."

    common = Counter(words).most_common(6)
    topics = ", ".join(w for w, _ in common)

    return (
        "Based on continuous analysis of public discussions, "
        f"current trending topics revolve around {topics}. "
        "These topics are receiving sustained online attention."
    )

def ai_answer(question, context):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful, intelligent assistant."},
                {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
            ],
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except:
        return "⚠️ I couldn't process that request right now."

# ===================== ROBOT WELCOME =====================

def robot_welcome(chat_id):
    for dots in ["•", "• •", "• • •"]:
        send_message(chat_id, f"Initializing{dots}")
        time.sleep(0.6)

    send_message(
        chat_id,
        "✅ Connection established.\n"
        "You are now **linked** to *God’s Eye Bot*.\n\n"
        "Created by **Ph03nix**, designed to monitor trends, "
        "analyze public information, and provide intelligent answers.\n\n"
        "📌 **Commands:**\n"
        "/start – Welcome & help\n"
        "/pair – Pair this chat\n"
        "/unpair – Remove pairing\n"
        "/trending – Live public trends\n"
        "/requests – Ask any question\n"
        "/complaints – Send feedback to the developer\n\n"
        "⚡ Powered by **PH03NIX**"
    )

# ===================== BOT LOOP =====================

def run_bot():
    offset = 0

    while True:
        try:
            updates = requests.get(
                f"{BASE_URL}/getUpdates",
                params={"offset": offset, "timeout": 30},
                timeout=35
            ).json()

            for update in updates.get("result", []):
                offset = update["update_id"] + 1
                message = update.get("message")
                if not message:
                    continue

                chat_id = message["chat"]["id"]
                text = message.get("text", "").strip()

                record_activity(chat_id)

                if text == "/start":
                    robot_welcome(chat_id)
                    continue

                if text == "/pair":
                    pairs = load_json(PAIR_FILE)
                    pairs[str(chat_id)] = True
                    save_json(PAIR_FILE, pairs)
                    send_message(chat_id, "✅ Chat paired successfully.")
                    continue

                if text == "/unpair":
                    pairs = load_json(PAIR_FILE)
                    pairs.pop(str(chat_id), None)
                    save_json(PAIR_FILE, pairs)
                    send_message(chat_id, "❌ Chat unpaired.")
                    continue

                if text == "/trending":
                    data = hackernews_data() + devto_data()
                    send_message(chat_id, f"🔥 **Trending Now**\n\n{ai_style_trending(data)}")
                    continue

                if text.startswith("/requests"):
                    q = text.replace("/requests", "").strip()
                    if not q:
                        send_message(chat_id, "❓ Type your question after /requests")
                        continue
                    context = " ".join((hackernews_data() + devto_data())[:5])
                    send_message(chat_id, f"🤖 **Answer**\n\n{ai_answer(q, context)}")
                    continue

                if text.startswith("/complaints"):
                    msg = text.replace("/complaints", "").strip()
                    if not msg:
                        send_message(chat_id, "📝 Write your complaint after /complaints")
                        continue

                    if ADMIN_ID:
                        send_message(
                            ADMIN_ID,
                            f"📩 **New Complaint**\nFrom `{chat_id}`:\n\n{msg}"
                        )
                    send_message(chat_id, "✅ Complaint sent.")
                    continue

                if text == "/stats":
                    if chat_id != ADMIN_ID:
                        send_message(chat_id, "⛔ Admin only.")
                        continue

                    stats = load_json(STATS_FILE)
                    now = datetime.utcnow()
                    week = set()
                    month = set()

                    for uid, times in stats.items():
                        for t in times:
                            dt = datetime.fromisoformat(t)
                            if now - dt <= timedelta(days=7):
                                week.add(uid)
                            if dt.month == now.month and dt.year == now.year:
                                month.add(uid)

                    send_message(
                        chat_id,
                        f"📊 **Bot Statistics**\n\n"
                        f"👥 Active (7 days): **{len(week)}**\n"
                        f"📅 Active (month): **{len(month)}**\n\n"
                        "⚡ Powered by PH03NIX"
                    )
                    continue

        except Exception:
            time.sleep(3)

# ===================== START =====================

if __name__ == "__main__":
    Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
