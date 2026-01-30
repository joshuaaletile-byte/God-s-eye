from flask import Flask
import threading
import main

app = Flask(__name__)

@app.route("/")
def home():
    return "God’s Eye Bot is running — POWERED BY PH03NIX"

if __name__ == "__main__":
    threading.Thread(target=main.run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
