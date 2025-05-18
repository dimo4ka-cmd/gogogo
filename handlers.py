import re
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_IDS, RATE_LIMIT_SECONDS, logger
from database import Database

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Отправьте номер WhatsApp в формате +1234567890."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text
    user = update.message.from_user
    db = Database(context.bot_data["db_file"])

    user_data = db.get_user(chat_id)
    if user_data and user_data[3] == "banned":
        await update.message.reply_text("Вы заблокированы.")
        return

    if not re.match(r"^\+\d{10,15}$", text):
        await update.message.reply_text("Номер должен быть в формате +1234567890.")
        return

    if user_data and (datetime.now().timestamp() - user_data[4]) < RATE_LIMIT_SECONDS:
        await update.message.reply_text("Подождите перед повторной отправкой.")
        return

    db.add_user(chat_id, text, user.username or user.first_name)
    await update.message.reply_text("Номер сохранён. Администратор свяжется с вами.")
    for admin_id in ADMIN_IDS:
        await context.bot.send_message(
            chat_id=admin_id,
            text=f"Новая заявка: Chat ID: {chat_id}, Номер: {text}, Имя: {user.username or user.first_name}"
        )
    logger.info(f"User {chat_id} submitted phone number {text}")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("Доступно только администраторам.")
        return

    db = Database(context.bot_data["db_file"])
    users = db.get_all_users()
    if not users:
        await update.message.reply_text("Нет заявок.")
        return

    response = "Заявки:\n"
    for user in users:
        response += f"Chat ID: {user[0]}, Номер: {user[1]}, Имя: {user[2]}, Статус: {user[3]}\n"
    response += "\n/reply <chat_id> <сообщение>\n/ban <chat_id>\n/stats"
    await update.message.reply_text(response)

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("Доступно только администраторам.")
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Использование: /reply <chat_id> <сообщение>")
        return

    try:
        chat_id = int(args[0])
        message = " ".join(args[1:])
        await context.bot.send_message(chat_id=chat_id, text=f"Администратор: {message}")
        await update.message.reply_text(f"Сообщение отправлено: {chat_id}")
        logger.info(f"Admin replied to {chat_id}: {message}")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("Доступно только администраторам.")
        return

    args = context.args
    if not args:
        await update.message.reply_text("Использование: /ban <chat_id>")
        return

    try:
        chat_id = int(args[0])
        db = Database(context.bot_data["db_file"])
        db.ban_user(chat_id)
        await context.bot.send_message(chat_id=chat_id, text="Вы заблокированы.")
        await update.message.reply_text(f"Пользователь {chat_id} заблокирован.")
        logger.info(f"User {chat_id} banned by admin")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("Доступно только администраторам.")
        return

    db = Database(context.bot_data["db_file"])
    total_users, banned_users, total_submissions = db.get_stats()
    response = (
        f"Статистика:\n"
        f"Всего пользователей: {total_users}\n"
        f"Заблокировано: {banned_users}\n"
        f"Всего заявок: {total_submissions}"
    )
    await update.message.reply_text(response)
    logger.info("Stats requested by admin")
