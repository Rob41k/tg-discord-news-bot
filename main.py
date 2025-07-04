import requests
from bs4 import BeautifulSoup
import time
import os

WEBHOOK_URL = os.getenv("https://discord.com/api/webhooks/1390800496746430525/abVOuWQ7FDHjsZAJvwm047eJN5TaCjs-JqBj342Nc7_9KYVcsEjh3hVGtvNhkcdXjK3-")
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

def send_to_discord(post):
    embed = {
        "title": post["title"],
        "description": post["description"],
        "url": post["link"]
    }
    if post["image"]:
        embed["image"] = {"url": post["image"]}

    payload = {"embeds": [embed]}
    r = requests.post(WEBHOOK_URL, json=payload)
    print("✅ Надіслано в Discord:", r.status_code)

def main():
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
