import requests
import os

BOT_TOKEN = input("Введи токен бота: ")
WEBHOOK_URL = input("Введи URL вебхука (например https://fata-vendors.vercel.app/webhook): ")

r = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
    json={"url": WEBHOOK_URL}
)
print(r.json())
