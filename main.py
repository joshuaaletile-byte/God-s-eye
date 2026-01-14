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

# 🔴 Replace with your numeric Telegram ID
ADMIN_ID = 123456789  # <-- Your Telegram numeric ID here

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
    try:
        r = requests.get("https://hn.algolia.com/api/v1/search?tags=story", timeout=10)
        if r.status_code != 200:
            return []
        return [hit["title"] for hit in r.json()["hits"][:20]]
    except:
        return []

def devto_data():
    try:
        r = requests.get("https://dev.to/api/articles", timeout=10)
        if r.status_code != 200:
            return []
        return [a["title"] for a in r.json()[:20]]
    except:
        return []

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

def ai_style_trending(texts):
    if not texts:
        return "There is currently no strong public trend detected."

    words = []
    stopwords = {
        "the","and","with","from","this","that","about","into",
        "have","will","they","their","what","when","where",
        "your","been","more","over","after","before","such"
    }

    for text in texts:
        cleaned = clean(text)
        for w in cleaned.split():
            if w not in stopwords and len(w) > 4:
                words.append(w)

    if not words:
        return "Public discussions are currently too scattered to identify a clear trend."

    common = Counter(words).most_common(6)
    topics = ", ".join([w for w, _ in common])

    return (
        "Based on continuous public discussions across technology and news platforms, "
        "current trending topics are centered around "
        f"{topics}. These subjects are receiving consistent attention and engagement "
        "from online communities, indicating ongoing relevance."
    )

# ===============================
# 🤖 TELEGRAM HELPERS
# ===============================
def send_message(chat_id, text):
    try:
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10
        )
    except:
        pass

def get_updates(offset=None):
    try:
        return requests.get(
            f"{TELEGRAM_API}/getUpdates",
            params={"timeout": 100, "offset": offset},
            timeout=120
        ).json()
    except:
        return {"result": []}

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

            # /start
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

            # /pair
            if text == "/pair":
                paired_chats.add(chat_id)
                save_pairs(paired_chats)
                send_message(chat_id, "✅ Chat paired successfully.")
                continue

            # /unpair
            if text == "/unpair":
                paired_chats.discard(chat_id)
                save_pairs(paired_chats)
                send_message(chat_id, "❌ Chat unpaired.")
                continue

            # Require pairing
            if chat_id not in paired_chats:
                send_message(chat_id, "⚠️ Please /pair this chat first.")
                continue

            # /trending
            if text == "/trending":
                data = hackernews_data() + devto_data()
                answer = ai_style_trending(data)
                send_message(chat_id, f"🔥 Trending Now:\n\n{answer}")
                continue

            # /requests
            if text.startswith("/requests"):
                question = text.replace("/requests", "").strip()
                if not question:
                    send_message(chat_id, "Usage: /requests <your question>")
                    continue

                data = hackernews_data() + devto_data()
                answer = ai_style_answer(question, data)
                send_message(chat_id, answer)
                continue

            # /complaints
            if text.startswith("/complaints"):
                complaint = text.replace("/complaints", "").strip()
                if not complaint:
                    send_message(chat_id, "Usage: /complaints <your message>")
                    continue

                # Send to admin
                send_message(
                    ADMIN_ID,
                    f"📩 New complaint from chat {chat_id}:\n\n{complaint}"
                )
                send_message(chat_id, "✅ Your complaint has been sent. Thank you.")
                continue

        time.sleep(1)

# ===============================
# ▶️ START EVERYTHING
# ===============================
if __name__ == "__main__":
    Thread(target=run_web).start()
    run_bot()
