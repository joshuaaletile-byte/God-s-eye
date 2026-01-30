import json
from datetime import datetime, timedelta

FILE = "users.json"

def load():
    try:
        with open(FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save(data):
    with open(FILE, "w") as f:
        json.dump(data, f)

def track(user_id):
    data = load()
    data[str(user_id)] = datetime.utcnow().isoformat()
    save(data)

def stats():
    data = load()
    now = datetime.utcnow()

    last7 = sum(
        1 for t in data.values()
        if datetime.fromisoformat(t) > now - timedelta(days=7)
    )

    monthly = sum(
        1 for t in data.values()
        if datetime.fromisoformat(t) > now - timedelta(days=30)
    )

    return last7, monthly
