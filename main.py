import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from intelligence import web_summary
from stats import track, stats

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID") or 0)
WHATSAPP = os.getenv("WHATSAPP_NUMBER")

# ----------------- Commands -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track(update.effective_user.id)
    await update.message.reply_text(
        "🤖 Boot sequence initiated...\n"
        "⏳ Activating intelligence core...\n\n"
        "✅ You are now connected to God’s Eye Bot\n"
        "Created by PH03NIX 🔥\n\n"
        "Commands:\n"
        "/trending – Latest useful trends\n"
        "/requests – Ask any question\n"
        "/complaints – Send complaints\n"
        "/stats – Admin-only stats\n\n"
        "POWERED BY PH03NIX"
    )

async def requests_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("Usage: /requests your question")
        return
    query = " ".join(context.args)
    answer = web_summary(query)
    await update.message.reply_text(answer)

async def trending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track(update.effective_user.id)
    topics = ["football news", "celebrity news", "technology trends"]
    responses = [web_summary(t) for t in topics]
    await update.message.reply_text("\n\n".join(responses))

async def complaints(update: Update, context: ContextTypes.DEFAULT_TYPE):
    track(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("Usage: /complaints your message")
        return
    complaint = " ".join(context.args)
    link = f"https://wa.me/{WHATSAPP}?text={complaint}"
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📩 Complaint received:\n{complaint}\n\n"
             f"To enable faster transfer of messages kindly tap the link below:\n{link}"
    )
    await update.message.reply_text("✅ Complaint sent successfully.")

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    last7, month = stats()
    await update.message.reply_text(
        f"📊 Bot Stats\nActive users (7 days): {last7}\nActive users (30 days): {month}"
    )

# ----------------- Run Bot -----------------
def run_bot():
    print("🤖 Starting Telegram bot...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("requests", requests_cmd))
    app.add_handler(CommandHandler("trending", trending))
    app.add_handler(CommandHandler("complaints", complaints))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.run_polling()
