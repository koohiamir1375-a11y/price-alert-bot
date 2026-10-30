import json
import os
import re
import time

import requests
from bs4 import BeautifulSoup

ALLOWED = "https://books.toscrape.com/"
STATE_FILE = "state.json"
INTERVAL = int(os.environ.get("CHECK_INTERVAL", "300"))
EXAMPLE = ALLOWED + "catalogue/a-light-in-the-attic_1000/index.html"


def load_token():
    with open(".env") as f:
        for line in f:
            if line.startswith("BOT_TOKEN="):
                return line.strip().split("=", 1)[1]
    raise SystemExit("BOT_TOKEN missing in .env")


API = "https://api.telegram.org/bot" + load_token() + "/"


def tg(method, **params):
    try:
        r = requests.post(API + method, json=params, timeout=40)
        return r.json()
    except (requests.RequestException, ValueError) as err:
        print("Telegram error:", type(err).__name__)
        return {"ok": False}


def send(chat_id, text):
    tg("sendMessage", chat_id=chat_id, text=text,
       disable_web_page_preview=True)


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"users": {}}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def fetch_book(url):
    r = requests.get(url, timeout=15,
                     headers={"User-Agent": "Mozilla/5.0 (price-alert demo)"})
    r.raise_for_status()
    r.encoding = "utf-8"
    soup = BeautifulSoup(r.text, "html.parser")
    title = soup.select_one("h1").text.strip()
    price_text = soup.select_one("p.price_color").text
    price = float(re.search(r"\d+(?:\.\d+)?", price_text).group())
    return title, price


def check_all(state, chat_filter=None):
    alerts = 0
    for chat_id, items in state["users"].items():
        if chat_filter and chat_id != chat_filter:
            continue
        for item in items:
            try:
                _, price = fetch_book(item["url"])
            except Exception as err:
                print("Check failed:", type(err).__name__)
                continue
            if price != item["price"]:
                arrow = "dropped" if price < item["price"] else "increased"
                send(chat_id,
                     f"Price {arrow}!\n{item['title']}\n"
                     f"{item['price']} -> {price}\n{item['url']}")
                item["price"] = price
                alerts += 1
    save_state(state)
    return alerts


HELP = (
    "Book Price Alert\n\n"
    "/track <url> - start tracking a book\n"
    "/list - show tracked books\n"
    "/untrack <number> - stop tracking\n"
    "/check - check prices now\n"
    "/simulate <number> - demo: fake an old price to test alerts\n\n"
    "Example:\n/track " + EXAMPLE
)


def handle(msg, state):
    chat_id = str(msg["chat"]["id"])
    parts = msg["text"].strip().split()
    cmd = parts[0].split("@")[0].lower()
    arg = parts[1] if len(parts) > 1 else None
    items = state["users"].setdefault(chat_id, [])

    if cmd in ("/start", "/help"):
        send(chat_id, HELP)
    elif cmd == "/track":
        if not arg or not arg.startswith(ALLOWED):
            send(chat_id, "Send a book link from books.toscrape.com.\n"
                          "Example:\n/track " + EXAMPLE)
            return
        if any(i["url"] == arg for i in items):
            send(chat_id, "Already tracking this book.")
            return
        try:
            title, price = fetch_book(arg)
        except Exception:
            send(chat_id, "Could not read that page. Check the link.")
            return
        items.append({"url": arg, "title": title, "price": price})
        save_state(state)
        send(chat_id, f"Tracking: {title}\nCurrent price: {price}")
    elif cmd == "/list":
        if not items:
            send(chat_id, "Nothing tracked yet. Use /track <url>")
        else:
            lines = [f"{n}. {i['title']} - {i['price']}"
                     for n, i in enumerate(items, 1)]
            send(chat_id, "\n".join(lines))
    elif cmd == "/untrack":
        if arg and arg.isdigit() and 1 <= int(arg) <= len(items):
            removed = items.pop(int(arg) - 1)
            save_state(state)
            send(chat_id, "Removed: " + removed["title"])
        else:
            send(chat_id, "Use /untrack <number> (see /list)")
    elif cmd == "/check":
        send(chat_id, "Checking prices...")
        if check_all(state, chat_id) == 0:
            send(chat_id, "No price changes.")
    elif cmd == "/simulate":
        if arg and arg.isdigit() and 1 <= int(arg) <= len(items):
            items[int(arg) - 1]["price"] += 10
            save_state(state)
            send(chat_id, "Demo: old price faked. Now send /check")
        else:
            send(chat_id, "Use /simulate <number> (see /list)")
    else:
        send(chat_id, HELP)


def main():
    state = load_state()
    offset = None
    last_check = time.time()
    print("Bot running. Press Ctrl+C to stop.")
    while True:
        params = {"timeout": 30}
        if offset:
            params["offset"] = offset
        data = tg("getUpdates", **params)
        if not data.get("ok"):
            time.sleep(5)
            continue
        for upd in data["result"]:
            offset = upd["update_id"] + 1
            msg = upd.get("message")
            if msg and "text" in msg:
                try:
                    handle(msg, state)
                except Exception as err:
                    print("Handler error:", type(err).__name__)
        if time.time() - last_check >= INTERVAL:
            check_all(state)
            last_check = time.time()


if __name__ == "__main__":
    main()
