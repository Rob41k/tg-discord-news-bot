import requests
from bs4 import BeautifulSoup
import time
import os
from flask import Flask
import threading

# Flask app для Render
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

# Основні змінні
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
RSS_URL = "https://rsshub.app/telegram/channel/gruntmedia"
last_guid_file = "last_post.txt"

# Збереження останнього посту
def get_last_guid():
    try:
        with open(last_guid_file, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def save_last_guid(guid):
    with open(last_guid_file, "w") as f:
        f.write(guid)

# Завантаження посту з RSS
def fetch_latest_post():
    r = requests.get(RSS_URL)
    soup = BeautifulSoup(r.text, "xml")
    item = soup.find("item")
    if not item:
        return None

    title = item.title.text.strip()
    link = item.link.text.strip()
    description_html = item.find("description").text
    soup_desc = BeautifulSoup(description_html, "html.parser")
    description = soup_desc.get_text().strip()
    img = soup_desc.find("img")
    image_url = img["src"] if img else None
    guid = item.guid.text.strip()

    return {
        "title": title,
        "description": description,
        "link": link,
        "image": image_url,
        "guid": guid
    }

# Відправка в Discord
def send_to_discord(post):
    embed = {
        "title": post["title"],
        "description": f"{post['description']}\n\n🔗 [Переглянути в Telegram]({post['link']})"
    }
    if post["image"]:
        embed["image"] = {"url": post["image"]}

    payload = {"embeds": [embed]}
    r = requests.post(WEBHOOK_URL, json=payload)
    print("✅ Надіслано в Discord:", r.status_code)


# Головна логіка
def main():
    # Запускаємо Flask-сервер у фоні
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    while True:
        post = fetch_latest_post()
        if not post:
            print("⏳ Постів не знайдено.")
            time.sleep(60)
            continue

        last_guid = get_last_guid()
        if post["guid"] != last_guid:
            print("🆕 Новий пост! Відправляємо...")
            send_to_discord(post)
            save_last_guid(post["guid"])
        else:
            print("📭 Нових постів нема.")

        time.sleep(60)

if __name__ == "__main__":
    main()
