import os
import json
import asyncio
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "237989670"))

CATEGORIES = [
    "Шоу", "Фотографы", "Декораторы", "Площадки",
    "Образ", "Оборудование", "Координаторы", "Другое"
]

(
    NAME, CATEGORY, DESCRIPTION, PHONE, EMAIL,
    WEBSITE, CITY, TELEGRAM_HANDLE, INSTAGRAM, PRICE_FROM, PRICE_TO, PHOTO
) = range(12)

# In-memory state (per user)
user_states = {}
user_data = {}

def get_state(user_id):
    return user_states.get(user_id, None)

def set_state(user_id, state):
    user_states[user_id] = state

def get_data(user_id):
    if user_id not in user_data:
        user_data[user_id] = {}
    return user_data[user_id]

async def process_update(update_dict):
    bot = Bot(token=BOT_TOKEN)
    update = Update.de_json(update_dict, bot)

    if not update.message:
        return

    user_id = update.effective_user.id
    text = update.message.text or ""
    state = get_state(user_id)
    data = get_data(user_id)

    # /start
    if text == "/start":
        user_data[user_id] = {}
        set_state(user_id, NAME)
        await bot.send_message(
            chat_id=user_id,
            text="👋 Привет! Это форма для размещения в каталоге свадебных подрядчиков *Fata*.\n\nЯ задам несколько вопросов — это займёт около 2 минут.\n\nНапишите *название вашей компании или имя*:",
            parse_mode="Markdown"
        )
        return

    # /cancel
    if text == "/cancel":
        user_data[user_id] = {}
        set_state(user_id, None)
        await bot.send_message(chat_id=user_id, text="Заявка отменена. Напишите /start чтобы начать заново.")
        return

    if state == NAME:
        data["name"] = text
        set_state(user_id, CATEGORY)
        keyboard = [[cat] for cat in CATEGORIES]
        await bot.send_message(
            chat_id=user_id,
            text="Выберите *категорию*:",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        )

    elif state == CATEGORY:
        data["category"] = text
        set_state(user_id, DESCRIPTION)
        await bot.send_message(
            chat_id=user_id,
            text="Напишите *описание* ваших услуг (до 300 символов):",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )

    elif state == DESCRIPTION:
        if len(text) > 300:
            await bot.send_message(chat_id=user_id, text="⚠️ Слишком длинно! Пожалуйста, сократите до 300 символов.")
            return
        data["description"] = text
        set_state(user_id, PHONE)
        await bot.send_message(chat_id=user_id, text="Укажите *телефон* для связи:", parse_mode="Markdown")

    elif state == PHONE:
        data["phone"] = text
        set_state(user_id, EMAIL)
        await bot.send_message(chat_id=user_id, text="Укажите *email* (или напишите «нет»):", parse_mode="Markdown")

    elif state == EMAIL:
        data["email"] = text
        set_state(user_id, WEBSITE)
        await bot.send_message(chat_id=user_id, text="Укажите *сайт* (или напишите «нет»):", parse_mode="Markdown")

    elif state == WEBSITE:
        data["website"] = text
        set_state(user_id, CITY)
        await bot.send_message(chat_id=user_id, text="В каком *городе* работаете?", parse_mode="Markdown")

    elif state == CITY:
        data["city"] = text
        set_state(user_id, TELEGRAM_HANDLE)
        await bot.send_message(chat_id=user_id, text="Ваш *Telegram* username (например @username, или «нет»):", parse_mode="Markdown")

    elif state == TELEGRAM_HANDLE:
        data["telegram"] = text
        set_state(user_id, INSTAGRAM)
        await bot.send_message(chat_id=user_id, text="Ваш *Instagram* (или «нет»):", parse_mode="Markdown")

    elif state == INSTAGRAM:
        data["instagram"] = text
        set_state(user_id, PRICE_FROM)
        await bot.send_message(chat_id=user_id, text="Укажите *минимальную цену* в рублях (только цифры, например: 15000):", parse_mode="Markdown")

    elif state == PRICE_FROM:
        if not text.strip().isdigit():
            await bot.send_message(chat_id=user_id, text="⚠️ Введите только цифры, например: 15000")
            return
        data["price_from"] = text
        set_state(user_id, PRICE_TO)
        await bot.send_message(chat_id=user_id, text="Укажите *максимальную цену* в рублях (или «нет»):", parse_mode="Markdown")

    elif state == PRICE_TO:
        data["price_to"] = text
        set_state(user_id, PHOTO)
        await bot.send_message(chat_id=user_id, text="Загрузите *фото* (логотип или фото команды). Или напишите «нет»:", parse_mode="Markdown")

    elif state == PHOTO:
        if update.message.photo:
            data["photo_file_id"] = update.message.photo[-1].file_id
            data["photo"] = "✅ Фото загружено"
        else:
            data["photo"] = text
            data["photo_file_id"] = None

        set_state(user_id, None)

        # Send to admin
        msg = (
            f"📋 *Новая заявка подрядчика*\n\n"
            f"👤 От: @{update.effective_user.username or 'нет'} (ID: {user_id})\n\n"
            f"🏷 *Название:* {data.get('name', '—')}\n"
            f"📂 *Категория:* {data.get('category', '—')}\n"
            f"📝 *Описание:* {data.get('description', '—')}\n"
            f"📞 *Телефон:* {data.get('phone', '—')}\n"
            f"📧 *Email:* {data.get('email', '—')}\n"
            f"🌐 *Сайт:* {data.get('website', '—')}\n"
            f"📍 *Город:* {data.get('city', '—')}\n"
            f"✈️ *Telegram:* {data.get('telegram', '—')}\n"
            f"📸 *Instagram:* {data.get('instagram', '—')}\n"
            f"💰 *Цена от:* {data.get('price_from', '—')} ₽\n"
            f"💰 *Цена до:* {data.get('price_to', '—')}\n"
            f"🖼 *Фото:* {data.get('photo', '—')}\n"
        )

        photo_id = data.get("photo_file_id")
        if photo_id:
            await bot.send_photo(chat_id=ADMIN_ID, photo=photo_id, caption=msg, parse_mode="Markdown")
        else:
            await bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode="Markdown")

        await bot.send_message(
            chat_id=user_id,
            text="✅ *Спасибо! Ваша заявка отправлена.*\n\nМы рассмотрим её и свяжемся с вами в течение 1-2 рабочих дней.\n\nПо вопросам: @fatawedding",
            parse_mode="Markdown"
        )
    else:
        await bot.send_message(chat_id=user_id, text="Напишите /start чтобы начать заполнение анкеты.")


def handler(request):
    if request.method == "POST":
        body = request.body
        update_dict = json.loads(body)
        asyncio.run(process_update(update_dict))
        return {"statusCode": 200, "body": "ok"}
    return {"statusCode": 200, "body": "Fata Vendors Bot"}
