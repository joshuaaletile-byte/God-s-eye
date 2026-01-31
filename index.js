const express = require("express");
const TelegramBot = require("node-telegram-bot-api");

const BOT_TOKEN = process.env.BOT_TOKEN;
const ADMIN_ID = process.env.ADMIN_ID;

const app = express();
app.use(express.json());

const bot = new TelegramBot(BOT_TOKEN);

// ----- COMMAND HANDLERS -----
bot.onText(/\/start/, (msg) => {
  bot.sendMessage(
    msg.chat.id,
    "🤖 Initializing God’s Eye Bot...\n" +
    "⏳ Booting intelligence core...\n" +
    "✅ System ready.\n\n" +
    "Welcome to *God’s Eye Bot* 🔥\n" +
    "Created by *PH03NIX*\n\n" +
    "Commands:\n" +
    "/start – Welcome\n" +
    "/help – Help\n\n" +
    "POWERED BY PH03NIX",
    { parse_mode: "Markdown" }
  );
});

bot.onText(/\/help/, (msg) => {
  bot.sendMessage(msg.chat.id, "More commands coming soon 🚀");
});

// ----- WEBHOOK -----
app.post(`/${BOT_TOKEN}`, (req, res) => {
  bot.processUpdate(req.body);
  res.sendStatus(200);
});

app.get("/", (req, res) => {
  res.send("God’s Eye Bot running — POWERED BY PH03NIX");
});

// ----- START SERVER -----
const PORT = process.env.PORT || 10000;
app.listen(PORT, () => {
  console.log("God’s Eye Bot is running");
});
