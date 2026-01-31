import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

app = Flask(__name__)

application = Application.builder().token(BOT_TOKEN).build()

# ---------------- COMMANDS ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 Initializing God's Eye Bot...\n"
        "⏳ Loading intelligence modules...\n"
        "✅ System ready.\n\n"
        "Welcome to *God's Eye Bot* 🔥\n"
        "Created by *PH03NIX*\n\n"
        "Commands:\n"
        "/start – Welcome message\n"
        "/help – Show help\n\n"
        "POWERED BY PH03NIX"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("More commands coming soon 🚀")

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_cmd))

# ---------------- WEBHOOK ----------------

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
async def telegram_webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    await application.process_update(update)
    return "ok"

@app.route("/")
def home():
    return "God's Eye Bot running — POWERED BY PH03NIX"

# ---------------- START ----------------

if __name__ == "__main__":
    application.initialize()
    application.start()
    app.run(host="0.0.0.0", port=10000)
