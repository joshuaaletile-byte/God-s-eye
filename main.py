import os
import telebot
import requests
import json
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

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


# ===== START =====
@bot.message_handler(commands=['start'])
def start(message):
    register_user(message.from_user.id)

    text = (
        "🤖 <b>God Eye Bot</b>\n"
        "System initialized successfully.\n\n"

        "<b>Commands:</b>\n"
        "• /ask question\n"
        "• /trending\n"
        "• /website\n"
        "• /complaint\n\n"

        "Powered by <b>PH03NIX</b>"
    )
    bot.send_message(message.chat.id, text)


# ===== FREE AI ANSWER =====
def get_ai_answer(query):
    try:
        url = "https://api.duckduckgo.com/"
        params = {"q": query, "format": "json"}
        res = requests.get(url, params=params).json()

        if res.get("Abstract"):
            return res["Abstract"]

        return "I couldn't find a direct answer, try rephrasing."
    except:
        return "Knowledge service unavailable. Try again later."


@bot.message_handler(commands=['ask'])
def ask(message):
    register_user(message.from_user.id)

    query = message.text.replace("/ask", "").strip()
    if not query:
        bot.reply_to(message, "Example:\n/ask What is football?")
        return

    msg = bot.reply_to(message, "🔎 Thinking...")
    answer = get_ai_answer(query)

    bot.edit_message_text(answer, message.chat.id, msg.message_id)


# ===== TRENDING NEWS =====
@bot.message_handler(commands=['trending'])
def trending(message):
    register_user(message.from_user.id)

    try:
        url = "https://newsapi.org/v2/top-headlines?language=en&pageSize=5"
        res = requests.get(url)
        data = res.json()

        articles = data.get("articles", [])
        if not articles:
            bot.send_message(message.chat.id, "No trending news found.")
            return

        text = "🔥 <b>Trending Now:</b>\n\n"

        for a in articles[:5]:
            text += f"• {a['title']}\n"

        bot.send_message(message.chat.id, text)

    except:
        bot.send_message(message.chat.id, "Couldn't fetch trending news.")


# ===== WEBSITE BUTTON =====
@bot.message_handler(commands=['website'])
def website(message):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(
            "🌐 Open Website",
            url="https://joshuaaletile-byte.github.io/Ph03nix-link-bot/"
        )
    )
    bot.send_message(message.chat.id, "Access the web version:", reply_markup=markup)


# ===== COMPLAINT =====
@bot.message_handler(commands=['complaint'])
def complaint(message):
    msg = bot.send_message(message.chat.id, "Type your complaint:")
    bot.register_next_step_handler(msg, process_complaint)


def process_complaint(message):
    text = (
        f"📩 Complaint from {message.from_user.id}\n\n"
        f"{message.text}"
    )
    bot.send_message(ADMIN_ID, text)
    bot.reply_to(message, "Complaint sent.")


# ===== USER STATS (ADMIN ONLY) =====
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

    text = (
        "📊 <b>User Statistics</b>\n\n"
        f"Weekly Active Users: {weekly}\n"
        f"Monthly Active Users: {monthly}\n"
        f"Total Users: {len(users)}"
    )

    bot.send_message(message.chat.id, text)


# ===== FALLBACK =====
@bot.message_handler(func=lambda m: True)
def chat(message):
    register_user(message.from_user.id)
    bot.reply_to(message, get_ai_answer(message.text))


print("Bot running...")
bot.infinity_polling(skip_pending=True)
