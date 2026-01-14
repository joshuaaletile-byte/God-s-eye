import requests
import os
import time
import re
from collections import Counter
from threading import Thread
from flask import Flask

# ===============================
# 🌐 KEEP-ALIVE WEB SERVER (RENDER)
# ===============================
app = Flask(__name__)

@app.route("/")
def home():
    return "God's Eye Bot is running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ===============================
# 🔑 TELEGRAM CONFIG
# ===============================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ===============================
# 📌 PAIRING STORAGE (IN-MEMORY)
# ===============================
paired_chats = set()

# ===============================
# 🔎 PUBLIC DATA SOURCES
# ===============================
def hackernews_trends(limit=15):
    url = "https://hn.algolia.com/api/v1/search?tags=story"
    r = requests.get(url, timeout=10)
    if r.status_code != 200:
        return []
    return [hit["title"] for hit in r.json()["hits"][:limit]]

def devto_trends(limit=15):
    r = requests.get("https://dev.to/api/articles", timeout=10)
    if r.status_code != 200:
        return []
    return [a["title"] for a in r.json()[:limit]]

# ===============================
# 🧠 TEXT ANALYSIS
# ===============================
def clean_text(text):
    text = text.lower()
    return re.sub(r"[^a-z\s]", "", text)

def extract_trends(texts):
    stopwords = {
        "the","and","with","from","this","that","about",
        "your","into","when","what","where","have"
    }
    words = []
    for text in texts:
        for w in clean_text(text).split():
            if w not in stopwords and len(w) > 3:
                words.append(w)
    return Counter(words).most_common(8)

# ===============================
# 🤖 TELEGRAM FUNCTIONS
# ===============================
def send_message(chat_id, text):
    requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=10
    )

def get_updates(offset=None):
    params = {"timeout": 100, "offset": offset}
    r = requests.get(f"{TELEGRAM_API}/getUpdates", params=params, timeout=120)
    return r.json()

# ===============================
# 🚀 BOT LOGIC
# ===============================
def run_bot():
    offset = None
    print("🤖 God's Eye Bot running...")

    while True:
        updates = get_updates(offset)

        for update in updates.get("result", []):
            offset = update["update_id"] + 1
            message = update.get("message")
            if not message:
                continue

            chat_id = message["chat"]["id"]
            text = message.get("text", "").strip()

            # /start
            if text == "/start":
                send_message(
                    chat_id,
                    "👁️ *Welcome to God's Eye Bot*\n"
                    "Created by *Ph03nix*\n\n"
                    "I analyze *public internet trends* only.\n\n"
                    "📌 Commands:\n"
                    "/pair – Pair bot to this chat\n"
                    "/unpair – Remove pairing\n"
                    "/trending – Show current trends\n"
                    "/requests <question> – Ask the internet\n\n"
                    "Examples:\n"
                    "`/trending`\n"
                    "`/requests football transfer news`"
                )
                continue

            # /pair
            if text == "/pair":
                paired_chats.add(chat_id)
                send_message(chat_id, "✅ This chat has been paired.")
                continue

            # /unpair
            if text == "/unpair":
                paired_chats.discard(chat_id)
                send_message(chat_id, "❌ This chat has been unpaired.")
                continue

            # Block unpaired chats
            if chat_id not in paired_chats:
                send_message(chat_id, "⚠️ This chat is not paired. Use /pair first.")
                continue

            # /trending
            if text == "/trending":
                posts = hackernews_trends() + devto_trends()
                if not posts:
                    send_message(chat_id, "No trends found right now.")
                    continue

                trends = extract_trends(posts)
                reply = "🔥 *Current Internet Trends:*\n\n"
                for word, count in trends:
                    reply += f"- {word} ({count})\n"

                send_message(chat_id, reply)
                continue

            # /requests
            if text.startswith("/requests"):
                query = text.replace("/requests", "").strip()
                if not query:
                    send_message(chat_id, "❓ Usage: /requests <your question>")
                    continue

                posts = hackernews_trends() + devto_trends()
                matched = [p for p in posts if query.lower() in p.lower()]

                if not matched:
                    send_message(chat_id, "No public answers found.")
                else:
                    reply = f"🌍 *Public answers for:* {query}\n\n"
                    for m in matched[:5]:
                        reply += f"- {m}\n"
                    send_message(chat_id, reply)

        time.sleep(1)

# ===============================
# ▶️ START EVERYTHING
# ===============================
if __name__ == "__main__":
    Thread(target=run_web).start()
    run_bot()
