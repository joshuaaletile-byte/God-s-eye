from flask import Flask
import threading
import main

app = Flask(__name__)

@app.route("/")
def home():
    return "God’s Eye Bot is running — POWERED BY PH03NIX"

if __name__ == "__main__":
    # Run Flask in a daemon thread
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=10000), daemon=True).start()
    # Run Telegram bot in main thread
    main.run_bot()
