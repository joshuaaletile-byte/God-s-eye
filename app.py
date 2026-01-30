from flask import Flask
from main import run_bot
import threading

app = Flask(__name__)

@app.route("/")
def home():
    return "God’s Eye Bot is running — POWERED BY PH03NIX"

threading.Thread(target=run_bot).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
