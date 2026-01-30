from flask import Flask
import threading
import main

app = Flask(__name__)

@app.route("/")
def home():
    return "God’s Eye Bot is running — POWERED BY PH03NIX"

if __name__ == "__main__":
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=lambda: app.run(host="0.0.0.0", port=10000), daemon=True)
    flask_thread.start()

    # Run Telegram bot in main thread (blocking)
    main.run_bot()
