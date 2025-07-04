import requests
from bs4 import BeautifulSoup
import time
import os
from flask import Flask
import threading
import html

# Flask app для Render
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

def run_flask():
    app.run(host="0.0.0.0", port=10000)

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
RSS_URL = "https://rsshub.app/telegram/channel/gruntmedia"
last_guid_file = "last_post.txt"

def get_last_guid():
    try:
        with open(last_guid_file, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def save_last_guid(guid):
    with open(last_guid_file, "w") as f:
        f.write(guid)

def fetch_latest_post():
    r = requests.get(RSS_URL)
    soup = BeautifulSoup(r.text, "xml")
    item = soup.find("item")
    if not item:
        return None

    title = item.title.text.strip()
    link = item.link.text.strip()
    guid = item.guid.text.strip()
    description_html = item.find("description").text

    description_html = html.unescape(description_html)
    soup_desc = BeautifulSoup(description_html, "html.parser")

    reply_block = soup_desc.find("blockquote")
    if reply_block:
        reply_block.decompose()

    # Обробка переносів рядків
    for tag in soup_desc.find_all(["br", "p", "div"]):
        tag.insert_after("\n")
        tag.unwrap()

    for tag in soup_desc.find_all(["b", "strong"]):
        tag.insert_before("**")
        tag.insert_after("**")
        tag.unwrap()

    for tag in soup_desc.find_all(["i", "em"]):
        tag.insert_before("*")
        tag.insert_after("*")
        tag.unwrap()

    description = soup_desc.get_text()
    img = soup_desc.find("img")
    image_url = img["src"] if img else None

    return {
        "title": title,
        "description": description.strip(),
        "link": link,
        "image": image_url,
        "guid": guid
    }

def send_to_discord(post):
    content = f"**{post['title']}**\n\n{post['description']}\n\n🔏 [Переглянути в Telegram]({post['link']})"

    payload = {"content": content}

    if post["image"]:
        payload["embeds"] = [{
            "image": {"url": post["image"]}
        }]

    headers = {"Content-Type": "application/json"}
    response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
    print("✅ Надіслано в Discord:", response.status_code)

def main():
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
            print("📫 Нових постів нема.")

        time.sleep(60)

if __name__ == "__main__":
    main()
