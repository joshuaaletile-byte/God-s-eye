import os
import telebot
import requests
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import threading

# ===== ENV =====
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ===== FLASK APP (FOR WEBSITE) =====
app = Flask(__name__)

USERS_FILE = "users.json"


# ===== USER STORAGE =====
def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f)


def register_user(user_id):
    users = load_users()
    users[str(user_id)] = str(datetime.utcnow())
    save_users(users)


# ===== FREE AI ENGINE =====
def get_ai_answer(query):
    try:
        url = "https://api.duckduckgo.com/"
        params = {"q": query, "format": "json", "no_html": 1}
        res = requests.get(url, params=params).json()

        if res.get("Abstract"):
            return res["Abstract"]

        return "I couldn't find a clear answer. Try rephrasing."
    except:
        return "Knowledge service unavailable."


# ===== WEBSITE API ROUTE =====
@app.route("/")
def home():
    return "God Eye API Running"


@app.route("/ask")
def ask_api():
    query = request.args.get("q")
    answer = get_ai_answer(query)
    return jsonify({"answer": answer})


# ===== TELEGRAM COMMANDS =====
@bot.message_handler(commands=['start'])
def start(message):
    register_user(message.from_user.id)

    bot.send_message(
        message.chat.id,
        "🤖 <b>God Eye Bot</b>\nSystem initialized.\n\n"
        "Commands:\n"
        "/ask question\n"
        "/trending\n"
        "/complaint\n"
        "/stats (admin)\n\n"
        "Powered by PH03NIX"
    )


@bot.message_handler(commands=['ask'])
def ask(message):
    register_user(message.from_user.id)

    query = message.text.replace("/ask", "").strip()
    if not query:
        bot.reply_to(message, "Example:\n/ask What is AI?")
        return

    msg = bot.reply_to(message, "Thinking...")
    answer = get_ai_answer(query)

    bot.edit_message_text(answer, message.chat.id, msg.message_id)


# ===== TRENDING NEWS =====
@bot.message_handler(commands=['trending'])
def trending(message):
    register_user(message.from_user.id)

    try:
        url = "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"
        res = requests.get(url).text

        items = res.split("<item>")[1:6]

        text = "🔥 <b>Trending News</b>\n\n"
        for item in items:
            title = item.split("<title>")[1].split("</title>")[0]
            text += f"• {title}\n"

        bot.send_message(message.chat.id, text)

    except:
        bot.send_message(message.chat.id, "Couldn't fetch trending news.")


# ===== COMPLAINT =====
@bot.message_handler(commands=['complaint'])
def complaint(message):
    msg = bot.send_message(message.chat.id, "Type your complaint:")
    bot.register_next_step_handler(msg, process_complaint)


def process_complaint(message):
    text = f"📩 Complaint from {message.from_user.id}\n\n{message.text}"
    bot.send_message(ADMIN_ID, text)
    bot.reply_to(message, "Complaint sent successfully.")


# ===== USER STATS =====
@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id != ADMIN_ID:
        return

    users = load_users()
    now = datetime.utcnow()

    weekly = 0
    monthly = 0

    for t in users.values():
        last = datetime.fromisoformat(t)

        if now - last <= timedelta(days=7):
            weekly += 1
        if now - last <= timedelta(days=30):
            monthly += 1

    bot.send_message(
        message.chat.id,
        f"📊 Stats\n\nWeekly Users: {weekly}\nMonthly Users: {monthly}\nTotal Users: {len(users)}"
    )


# ===== RUN BOT + API TOGETHER =====
def run_bot():
    bot.infinity_polling(skip_pending=True)


threading.Thread(target=run_bot).start()

port = int(os.environ.get("PORT", 8080))
app.run(host="0.0.0.0", port=port)
