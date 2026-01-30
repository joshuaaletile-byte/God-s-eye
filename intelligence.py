import feedparser
from bs4 import BeautifulSoup

def clean_text(text, limit=600):
    text = ' '.join(text.split())
    return text[:limit]

def web_summary(query):
    feeds = [
        "https://news.google.com/rss/search?q=" + query,
        "https://www.reddit.com/search.rss?q=" + query
    ]

    collected = []

    for url in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
            if hasattr(entry, "summary"):
                soup = BeautifulSoup(entry.summary, "html.parser")
                collected.append(soup.get_text())

    if not collected:
        return "I couldn’t find recent reliable information on that topic."

    combined = " ".join(collected)
    return clean_text(combined)
