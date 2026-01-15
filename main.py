import requests
import time
import json
import os
from collections import Counter
from flask import Flask
from openai import OpenAI

# ================= CONFIG =================

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_ID = os.getenv("ADMIN_ID")
ADMIN_ID = int(ADMIN_ID) if ADMIN_ID and ADMIN_ID.isdigit() else None

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
client = OpenAI(api_key=OPENAI_API_KEY)

PAIR_FILE = "paired.json"

# ================= WEB SERVER (Render) =================

app = Flask(__name__)

@app.route("/")
def home():
    return "God's Eye Bot is running."

# ================= UTILITIES =================

def load_pairs():
    if not os.path.exists(PAIR_FILE):
        return {}
    with open(PAIR_FILE, "r") as f:
        return json.load(f)

def save_pairs(data):
    with open(PAIR_FILE, "w") as f:
        json.dump(data, f, indent=2)

def send_message(chat_id, text):
    url = f"{BASE_URL}/sendMessage"
    requests.post(url, json={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    })

def clean(text):
    return "".join(c.lower() for c in text if c.isalnum() or c.isspace())

# ================= DATA SOURCES =================

def hackernews_data():
    try:
        res = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10)
        ids = res.json()[:5]
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
        res = requests.get("https://dev.to/api/articles?top=5", timeout=10)
        return [a["title"] for a in res.json()[:5]]
    except:
        return []

# ================= AI FUNCTIONS =================

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

    common = Counter(words).most_common(6)
    topics = ", ".join(w for w, _ in common)

    return (
        "Based on continuous analysis of public discussions, "
        f"current trending topics revolve around {topics}. "
        "These subjects are receiving sustained attention online."
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

# ================= ROBOT WELCOME =================

def robot_welcome(chat_id):
    for dots in ["•", "• •", "• • •"]:
        send_message(chat_id, f"Initializing{dots}")
        time.sleep(0.7)

    message = (
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
    send_message(chat_id, message)

# ================= BOT LOOP =================

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
                text = message.get("text", "")

                # START
                if text == "/start":
                    robot_welcome(chat_id)
                    continue

                # PAIR
                if text == "/pair":
                    pairs = load_pairs()
                    pairs[str(chat_id)] = True
                    save_pairs(pairs)
                    send_message(chat_id, "✅ This chat has been successfully paired.")
                    continue

                # UNPAIR
                if text == "/unpair":
                    pairs = load_pairs()
                    pairs.pop(str(chat_id), None)
                    save_pairs(pairs)
                    send_message(chat_id, "❌ This chat has been unpaired.")
                    continue

                # TRENDING
                if text == "/trending":
                    data = hackernews_data() + devto_data()
                    answer = ai_style_trending(data)
                    send_message(chat_id, f"🔥 **Trending Now**:\n\n{answer}")
                    continue

                # REQUESTS (AI)
                if text.startswith("/requests"):
                    question = text.replace("/requests", "").strip()
                    if not question:
                        send_message(chat_id, "❓ Please type your question after /requests")
                        continue

                    context = " ".join((hackernews_data() + devto_data())[:5])
                    answer = ai_answer(question, context)
                    send_message(chat_id, f"🤖 **Answer:**\n\n{answer}")
                    continue

                # COMPLAINTS
                if text.startswith("/complaints"):
                    complaint = text.replace("/complaints", "").strip()
                    if not complaint:
                        send_message(chat_id, "📝 Please write your complaint after /complaints")
                        continue

                    if ADMIN_ID:
    send_message(
        ADMIN_ID,
        f"📩 **New Complaint**\nFrom chat `{chat_id}`:\n\n{complaint}"
    )
                    send_message(chat_id, "✅ Your complaint has been sent to the developer.")
                    continue

        except Exception as e:
            time.sleep(3)

# ================= START =================

if __name__ == "__main__":
    from threading import Thread
    Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
