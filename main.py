import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ===== ENV VARIABLES =====
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))

# ===== BOT INIT =====
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ===== START COMMAND =====
@bot.message_handler(commands=['start'])
def start(message):
    text = (
        "🤖 <b>God Eye Bot</b>\n\n"
        "System initialized...\n"
        "Connection established successfully.\n\n"
        "<b>Available Commands:</b>\n"
        "• /website – Open web version\n"
        "• /complaint – Send a complaint\n\n"
        "Powered by <b>PH03NIX</b>"
    )
    bot.send_message(message.chat.id, text)

# ===== WEBSITE COMMAND =====
@bot.message_handler(commands=['website'])
def website(message):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(
            "🌐 Open PH03NIX Website",
            url="https://joshuaaletile-byte.github.io/Ph03nix-link-bot/"
        )
    )

    bot.send_message(
        message.chat.id,
        "Click below to access the website:",
        reply_markup=markup
    )

# ===== COMPLAINT COMMAND =====
@bot.message_handler(commands=['complaint'])
def complaint(message):
    msg = bot.send_message(
        message.chat.id,
        "✍️ Please type your complaint below:"
    )
    bot.register_next_step_handler(msg, process_complaint)

def process_complaint(message):
    complaint_text = (
        "📩 <b>New Complaint Received</b>\n\n"
        f"👤 User ID: <code>{message.from_user.id}</code>\n"
        f"📝 Message:\n{message.text}"
    )

    bot.send_message(ADMIN_ID, complaint_text)
    bot.reply_to(message, "✅ Complaint sent successfully.")

# ===== FALLBACK =====
@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.reply_to(
        message,
        "❓ I didn’t understand that.\nUse /start to see commands."
    )

# ===== RUN BOT =====
print("God Eye Bot is running...")
bot.infinity_polling(skip_pending=True)
