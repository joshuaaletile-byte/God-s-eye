import requests
import os
import time
import re
import json
from collections import Counter
from threading import Thread
from flask import Flask

# ===============================
# 🌐 KEEP-ALIVE WEB SERVER
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

# 🔴 PUT YOUR TELEGRAM USER ID HERE
ADMIN_ID = 123456789  # <-- replace this

# ===============================
# 💾 PERSISTENT STORAGE
# ===============================
PAIR_FILE = "paired_chats.json"

def load_pairs():
    if not os.path.exists(PAIR_FILE):
        return set()
    with open(PAIR_FILE, "r") as f:
        return set(json.load(f))

def save_pairs(pairs):
    with open(PAIR_FILE, "w") as f:
        json.dump(list(pairs), f)

paired_chats = load_pairs()

# ===============================
# 🔎 DATA SOURCES
# ===============================
def hackernews_data():
    r = requests.get("https://hn.algolia.com/api/v1/search?tags=story", timeout=10)
    if r.status_code != 200:
        return []
    return [hit["title"] for hit in r.json()["hits"][:20]]

def devto_data():
    r = requests.get("https://dev.to/api/articles", timeout=10)
    if r.status_code != 200:
        return []
    return [a["title"] for a in r.json()[:20]]

# ===============================
# 🧠 TEXT PROCESSING
# ===============================
def clean(text):
    text = text.lower()
    return re.sub(r"[^a-z\s]", "", text)

def ai_style_answer(question, texts):
    keywords = clean(question).split()
    relevant = []

    for t in texts:
        score = sum(1 for k in keywords if k in clean(t))
        if score > 0:
            relevant.append(t)

    if not relevant:
        return "Based on available public discussions, there is currently limited information addressing that topic directly."

    summary_words = []
    for text in relevant:
        summary_words.extend(clean(text).split())

    common = Counter(summary_words).most_common(12)
    topic_words = ", ".join([w for w, _ in common])

    return (
        f"Based on recent public discussions across multiple platforms, "
        f"the topic of '{question}' is being associated with key themes such as "
        f"{topic_words}. These discussions suggest ongoing interest and activity "
        f"around this subject in the public domain."
    )

# ===============================
# 🤖 TELEGRAM HELPERS
# ===============================
def send_message(chat_id, text):
    requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=10
    )

def get_updates(offset=None):
    return requests.get(
        f"{TELEGRAM_API}/getUpdates",
        params={"timeout": 100, "offset": offset},
        timeout=120
    ).json()

# ===============================
# 🚀 BOT LOOP
# ===============================
def run_bot():
    offset = None
    print("🤖 God's Eye Bot running...")

    while True:
        updates = get_updates(offset)

        for update in updates.get("result", []):
            offset = update["update_id"] + 1
            msg = update.get("message")
            if not msg:
                continue

            chat_id = msg["chat"]["id"]
            text = msg.get("text", "").strip()

            if text == "/start":
                send_message(
                    chat_id,
                    "👁️ Welcome to God's Eye Bot\n"
                    "Created by Ph03nix\n\n"
                    "Commands:\n"
                    "/pair – Pair this chat\n"
                    "/unpair – Remove pairing\n"
                    "/trending – Show public trends\n"
                    "/requests <question> – Ask the internet\n"
                    "/complaints <message> – Send feedback"
                )
                continue

            if text == "/pair":
                paired_chats.add(chat_id)
                save_pairs(paired_chats)
                send_message(chat_id, "✅ Chat paired successfully.")
                continue

            if text == "/unpair":
                paired_chats.discard(chat_id)
                save_pairs(paired_chats)
                send_message(chat_id, "❌ Chat unpaired.")
                continue

            if chat_id not in paired_chats:
                send_message(chat_id, "⚠️ Please /pair this chat first.")
                continue

            if text == "/trending":
                data = hackernews_data() + devto_data()
                if not data:
                    send_message(chat_id, "No trends found at the moment.")
                    continue

                words = Counter(" ".join(data).split()).most_common(6)
                reply = "🔥 Current public trends:\n\n"
                for w, c in words:
                    reply += f"- {w}\n"
                send_message(chat_id, reply)
                continue

            if text.startswith("/requests"):
                question = text.replace("/requests", "").strip()
                if not question:
                    send_message(chat_id, "Usage: /requests <your question>")
                    continue

                data = hackernews_data() + devto_data()
                answer = ai_style_answer(question, data)
                send_message(chat_id, answer)
                continue

            if text.startswith("/complaints"):
                complaint = text.replace("/complaints", "").strip()
                if not complaint:
                    send_message(chat_id, "Usage: /complaints <your message>")
                    continue

                send_message(
                    ADMIN_ID,
                    f"📩 New complaint:\nFrom chat {chat_id}\n\n{complaint}"
                )
                send_message(chat_id, "✅ Your complaint has been sent. Thank you.")
                continue

        time.sleep(1)

# ===============================
# ▶️ START
# ===============================
if __name__ == "__main__":
    Thread(target=run_web).start()
    run_bot()
