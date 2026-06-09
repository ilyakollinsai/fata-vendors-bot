import os
import json
import asyncio
from http.server import BaseHTTPRequestHandler
import telegram

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "237989670"))

CATEGORIES = [
    "Шоу", "Фотографы", "Декораторы", "Площадки",
    "Образ", "Оборудование", "Координаторы", "Другое"
]

NAME, CATEGORY, DESCRIPTION, PHONE, EMAIL, WEBSITE, CITY, TG, IG, PRICE_FROM, PRICE_TO, PHOTO = range(12)

user_states = {}
user_data_store = {}

def get_state(uid): return user_states.get(uid)
def set_state(uid, s): user_states[uid] = s
def get_data(uid):
    if uid not in user_data_store:
        user_data_store[uid] = {}
    return user_data_store[uid]

async def handle(update_dict):
    bot = telegram.Bot(token=BOT_TOKEN)
    update = telegram.Update.de_json(update_dict, bot)

    if not update.message:
        return

    msg = update.message
    user_id = update.effective_user.id
    text = msg.text or ""
    state = get_state(user_id)
    data = get_data(user_id)

    async def send(text, **kwargs):
        await bot.send_message(chat_id=user_id, text=text, parse_mode="Markdown", **kwargs)

    if text == "/start":
        user_data_store[user_id] = {}
        set_state(user_id, NAME)
        await send("👋 Привет! Это форма для размещения в каталоге свадебных подрядчиков *Fata*.\n\nЯ задам несколько вопросов — около 2 минут.\n\nНапишите *название вашей компании или имя*:")
        return

    if text == "/cancel":
        user_data_store[user_id] = {}
        set_state(user_id, None)
        await send("Заявка отменена. Напишите /start чтобы начать заново.")
        return

    if state is None:
        await send("Напишите /start чтобы начать заполнение анкеты.")
        return

    if state == NAME:
        data["name"] = text
        set_state(user_id, CATEGORY)
        kb = [[c] for c in CATEGORIES]
        await send("Выберите *категорию*:",
            reply_markup=telegram.ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True))

    elif state == CATEGORY:
        data["category"] = text
        set_state(user_id, DESCRIPTION)
        await send("Напишите *описание* ваших услуг (до 300 символов):",
            reply_markup=telegram.ReplyKeyboardRemove())

    elif state == DESCRIPTION:
        if len(text) > 300:
            await send("⚠️ Слишком длинно! Сократите до 300 символов.")
            return
        data["description"] = text
        set_state(user_id, PHONE)
        await send("Укажите *телефон* для связи:")

    elif state == PHONE:
        data["phone"] = text
        set_state(user_id, EMAIL)
        await send("Укажите *email* (или напишите «нет»):")

    elif state == EMAIL:
        data["email"] = text
        set_state(user_id, WEBSITE)
        await send("Укажите *сайт* (или напишите «нет»):")

    elif state == WEBSITE:
        data["website"] = text
        set_state(user_id, CITY)
        await send("В каком *городе* работаете?")

    elif state == CITY:
        data["city"] = text
        set_state(user_id, TG)
        await send("Ваш *Telegram* username (например @username, или «нет»):")

    elif state == TG:
        data["telegram"] = text
        set_state(user_id, IG)
        await send("Ваш *Instagram* (или «нет»):")

    elif state == IG:
        data["instagram"] = text
        set_state(user_id, PRICE_FROM)
        await send("Укажите *минимальную цену* в рублях (только цифры, например: 15000):")

    elif state == PRICE_FROM:
        if not text.strip().isdigit():
            await send("⚠️ Введите только цифры, например: 15000")
            return
        data["price_from"] = text
        set_state(user_id, PRICE_TO)
        await send("Укажите *максимальную цену* в рублях (или «нет»):")

    elif state == PRICE_TO:
        data["price_to"] = text
        set_state(user_id, PHOTO)
        await send("Загрузите *фото* (логотип или фото команды). Или напишите «нет»:")

    elif state == PHOTO:
        if msg.photo:
            data["photo_file_id"] = msg.photo[-1].file_id
            data["photo"] = "✅ Фото загружено"
        else:
            data["photo"] = text
            data["photo_file_id"] = None

        set_state(user_id, None)

        admin_msg = (
            f"📋 *Новая заявка подрядчика*\n\n"
            f"👤 От: @{update.effective_user.username or 'нет'} (ID: {user_id})\n\n"
            f"🏷 *Название:* {data.get('name','—')}\n"
            f"📂 *Категория:* {data.get('category','—')}\n"
            f"📝 *Описание:* {data.get('description','—')}\n"
            f"📞 *Телефон:* {data.get('phone','—')}\n"
            f"📧 *Email:* {data.get('email','—')}\n"
            f"🌐 *Сайт:* {data.get('website','—')}\n"
            f"📍 *Город:* {data.get('city','—')}\n"
            f"✈️ *Telegram:* {data.get('telegram','—')}\n"
            f"📸 *Instagram:* {data.get('instagram','—')}\n"
            f"💰 *Цена от:* {data.get('price_from','—')} ₽\n"
            f"💰 *Цена до:* {data.get('price_to','—')}\n"
            f"🖼 *Фото:* {data.get('photo','—')}\n"
        )

        photo_id = data.get("photo_file_id")
        if photo_id:
            await bot.send_photo(chat_id=ADMIN_ID, photo=photo_id, caption=admin_msg, parse_mode="Markdown")
        else:
            await bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="Markdown")

        await send("✅ *Спасибо! Ваша заявка отправлена.*\n\nМы рассмотрим её и свяжемся с вами в течение 1-2 рабочих дней.\n\nПо вопросам: @fatawedding")


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            update_dict = json.loads(body)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(handle(update_dict))
            loop.close()
        except Exception as e:
            print(f"Error: {e}")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Fata Vendors Bot is running")
