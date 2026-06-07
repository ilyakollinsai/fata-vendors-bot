import os
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "237989670"))

CATEGORIES = [
    "Шоу", "Фотографы", "Декораторы", "Площадки",
    "Образ", "Оборудование", "Координаторы", "Другое"
]

(
    NAME, CATEGORY, DESCRIPTION, PHONE, EMAIL,
    WEBSITE, CITY, TELEGRAM, INSTAGRAM, PRICE_FROM, PRICE_TO, PHOTO
) = range(12)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "👋 Привет! Это форма для размещения в каталоге свадебных подрядчиков Fata.\n\n"
        "Я задам несколько вопросов — это займёт около 2 минут.\n\n"
        "Напишите *название вашей компании или имя*:",
        parse_mode="Markdown"
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    keyboard = [[cat] for cat in CATEGORIES]
    await update.message.reply_text(
        "Выберите *категорию*:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CATEGORY


async def get_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["category"] = update.message.text
    await update.message.reply_text(
        "Напишите *описание* ваших услуг (до 300 символов):",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return DESCRIPTION


async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if len(text) > 300:
        await update.message.reply_text("⚠️ Слишком длинно! Пожалуйста, сократите до 300 символов.")
        return DESCRIPTION
    context.user_data["description"] = text
    await update.message.reply_text("Укажите *телефон* для связи:", parse_mode="Markdown")
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text
    await update.message.reply_text(
        "Укажите *email* (или напишите «нет»):",
        parse_mode="Markdown"
    )
    return EMAIL


async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["email"] = update.message.text
    await update.message.reply_text(
        "Укажите *сайт* (или напишите «нет»):",
        parse_mode="Markdown"
    )
    return WEBSITE


async def get_website(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["website"] = update.message.text
    await update.message.reply_text("В каком *городе* работаете?", parse_mode="Markdown")
    return CITY


async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["city"] = update.message.text
    await update.message.reply_text(
        "Ваш *Telegram* username (например @username, или напишите «нет»):",
        parse_mode="Markdown"
    )
    return TELEGRAM


async def get_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["telegram"] = update.message.text
    await update.message.reply_text(
        "Ваш *Instagram* (или напишите «нет»):",
        parse_mode="Markdown"
    )
    return INSTAGRAM


async def get_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["instagram"] = update.message.text
    await update.message.reply_text(
        "Укажите *минимальную цену* в рублях (только цифры, например: 15000):",
        parse_mode="Markdown"
    )
    return PRICE_FROM


async def get_price_from(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("⚠️ Введите только цифры, например: 15000")
        return PRICE_FROM
    context.user_data["price_from"] = text
    await update.message.reply_text(
        "Укажите *максимальную цену* в рублях (или напишите «нет»):",
        parse_mode="Markdown"
    )
    return PRICE_TO


async def get_price_to(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["price_to"] = update.message.text
    await update.message.reply_text(
        "Загрузите *фото* (логотип или фото команды). Или напишите «нет»:",
        parse_mode="Markdown"
    )
    return PHOTO


async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        file = update.message.photo[-1]
        context.user_data["photo_file_id"] = file.file_id
        context.user_data["photo"] = "✅ Фото загружено"
    else:
        context.user_data["photo"] = update.message.text
        context.user_data["photo_file_id"] = None

    await send_to_admin(update, context)
    await update.message.reply_text(
        "✅ *Спасибо! Ваша заявка отправлена.*\n\n"
        "Мы рассмотрим её и свяжемся с вами в течение 1-2 рабочих дней.\n\n"
        "По вопросам: @fatawedding",
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def send_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d = context.user_data
    user = update.effective_user
    text = (
        f"📋 *Новая заявка подрядчика*\n\n"
        f"👤 От: @{user.username or 'нет'} (ID: {user.id})\n\n"
        f"🏷 *Название:* {d.get('name', '—')}\n"
        f"📂 *Категория:* {d.get('category', '—')}\n"
        f"📝 *Описание:* {d.get('description', '—')}\n"
        f"📞 *Телефон:* {d.get('phone', '—')}\n"
        f"📧 *Email:* {d.get('email', '—')}\n"
        f"🌐 *Сайт:* {d.get('website', '—')}\n"
        f"📍 *Город:* {d.get('city', '—')}\n"
        f"✈️ *Telegram:* {d.get('telegram', '—')}\n"
        f"📸 *Instagram:* {d.get('instagram', '—')}\n"
        f"💰 *Цена от:* {d.get('price_from', '—')} ₽\n"
        f"💰 *Цена до:* {d.get('price_to', '—')}\n"
        f"🖼 *Фото:* {d.get('photo', '—')}\n"
    )

    photo_id = d.get("photo_file_id")
    if photo_id:
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo_id, caption=text, parse_mode="Markdown")
    else:
        await context.bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode="Markdown")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Заявка отменена. Напишите /start чтобы начать заново.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_category)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            WEBSITE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_website)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
            TELEGRAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_telegram)],
            INSTAGRAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_instagram)],
            PRICE_FROM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price_from)],
            PRICE_TO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price_to)],
            PHOTO: [
                MessageHandler(filters.PHOTO, get_photo),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_photo),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    app.run_polling()


if __name__ == "__main__":
    main()
