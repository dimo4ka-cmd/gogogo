import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from config import ADMIN_IDS, REFERRAL_CODE, QUEUE_LIMIT, NOTIFY_POSITION, PAYOUT_BOT_USERNAME, logger
from database import Database

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите реферальный код.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text
    user = update.message.from_user
    db = Database(context.bot_data["db_file"])

    user_data = db.get_user(chat_id)
    if not user_data:
        if text != REFERRAL_CODE:
            await update.message.reply_text("Неверный реферальный код.")
            return
        db.add_user(chat_id, user.username or user.first_name, text)
        await show_user_panel(update, context)
        return

    if user_data[4] == "banned":
        await update.message.reply_text("Вы заблокированы.")
        return

    if not re.match(r"^\+\d{10,15}$", text):
        await update.message.reply_text("Номер должен быть в формате +1234567890.")
        return

    if db.get_user_queue_count(chat_id) >= QUEUE_LIMIT:
        await update.message.reply_text(f"Лимит {QUEUE_LIMIT} номера в очереди.")
        return

    db.add_to_queue(chat_id, text)
    await update.message.reply_text("Номер добавлен в очередь.")
    queue = db.get_queue()
    for i, entry in enumerate(queue):
        if i + 1 == NOTIFY_POSITION:
            await context.bot.send_message(entry[1], "Ваш номер скоро будет взят, подготовьтесь.")
    await notify_admins(context, f"Новая заявка: Chat ID: {chat_id}, Номер: {text}")
    logger.info(f"User {chat_id} added number {text} to queue")

async def show_user_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Очередь", callback_data="queue")],
        [InlineKeyboardButton("Архив", callback_data="archive")],
        [InlineKeyboardButton("Статистика", callback_data="stats")],
        [InlineKeyboardButton("Вывести", callback_data="payout")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    balance = Database(context.bot_data["db_file"]).get_balance(update.effective_chat.id)
    text = f"Ваш баланс: ${balance:.2f}\nВыберите действие:"
    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    db = Database(context.bot_data["db_file"])
    chat_id = query.from_user.id

    if query.data == "queue":
        queue = db.get_queue()
        user_queue = [entry for entry in queue if entry[1] == chat_id]
        if not user_queue:
            await query.message.edit_text("Ваша очередь пуста.\nОтправьте номер для добавления.", reply_markup=back_button())
            return
        text = "Ваша очередь:\n"
        for i, entry in enumerate(queue):
            if entry[1] == chat_id:
                text += f"{i+1}. {entry[2]} ({entry[3]})\n"
        await query.message.edit_text(text, reply_markup=back_button())

    elif query.data == "archive":
        archive = db.get_archive(chat_id)
        if not archive:
            await query.message.edit_text("Архив пуст.", reply_markup=back_button())
            return
        text = "Архив:\n"
        for entry in archive:
            text += f"{entry[0]}: {entry[1]} ({entry[2].strftime('%Y-%m-%d')})\n"
        await query.message.edit_text(text, reply_markup=back_button())

    elif query.data == "stats":
        total_users, daily_submissions = db.get_stats()
        text = f"Статистика:\nУчастников: {total_users}\nСдано сегодня: {daily_submissions}"
        await query.message.edit_text(text, reply_markup=back_button())

    elif query.data == "payout":
        balance = db.get_balance(chat_id)
        if balance <= 0:
            await query.message.edit_text("Ваш баланс пуст.", reply_markup=back_button())
            return
        await query.message.edit_text(
            f"Заявка на выплату (${balance:.2f}) создана.\nПерейдите в {PAYOUT_BOT_USERNAME} для подачи.",
            reply_markup=back_button()
        )
        await notify_admins(context, f"Заявка на выплату: Chat ID: {chat_id}, Сумма: ${balance:.2f}")

    elif query.data == "back":
        await show_user_panel(update, context)

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMI
N_IDS:
        await update.message.reply_text("Доступно только администраторам.")
        return
    await show_admin_panel(update, context)

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Очередь", callback_data="admin_queue")],
        [InlineKeyboardButton("Начислить баланс", callback_data="admin_balance")],
        [InlineKeyboardButton("Обработать заявку", callback_data="admin_process")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.message.edit_text("Админ-панель:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Админ-панель:", reply_markup=reply_markup)

async def admin_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    db = Database(context.bot_data["db_file"])

    if query.data == "admin_queue":
        queue = db.get_queue()
        if not queue:
            await query.message.edit_text("Очередь пуста.", reply_markup=back_admin_button())
            return
        text = "Очередь:\n"
        for i, entry in enumerate(queue):
            text += f"ID: {entry[0]}, Chat ID: {entry[1]}, Номер: {entry[2]}, Статус: {entry[3]}\n"
        await query.message.edit_text(text, reply_markup=back_admin_button())

    elif query.data == "admin_balance":
        await query.message.edit_text("Введите: /add_balance <chat_id> <сумма>", reply_markup=back_admin_button())

    elif query.data == "admin_process":
        await query.message.edit_text("Введите: /process <queue_id> <status> (success/failed)", reply_markup=back_admin_button())

    elif query.data == "admin_back":
        await show_admin_panel(update, context)

async def add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("Доступно только администраторам.")
        return
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("Использование: /add_balance <chat_id> <сумма>")
        return
    try:
        chat_id = int(args[0])
        amount = float(args[1])
        db = Database(context.bot_data["db_file"])
        db.update_balance(chat_id, amount)
        await update.message.reply_text(f"Баланс обновлён: Chat ID: {chat_id}, Сумма: ${amount:.2f}")
        await context.bot.send_message(chat_id, f"Ваш баланс пополнен на ${amount:.2f}")
        logger.info(f"Admin added ${amount:.2f} to {chat_id}")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")

async def process_queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("Доступно только администраторам.")
        return
    args = context.args
    if len(args) != 2 or args[1] not in ["success", "failed"]:
        await update.message.reply_text("Использование: /process <queue_id> <status> (success/failed)")
        return
    try:
        queue_id = int(args[0])
        status = args[1]
        db = Database(context.bot_data["db_file"])
        db.update_queue_status(queue_id, status)
        queue = db.get_queue()
        for i, entry in enumerate(queue):
            if i + 1 == NOTIFY_POSITION:
                await context.bot.send_message(entry[1], "Ваш номер скоро будет взят, подготовьтесь.")
        await update.message.reply_text(f"Заявка {queue_id} обработана: {status}")
        logger.info(f"Admin processed queue ID {queue_id} as {status}")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")

async def notify_admins(context: ContextTypes.DEFAULT_TYPE, message: str):
    for admin_id in ADMIN_IDS:
        await context.bot.send_message(admin_id, message)

def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="back")]])

def back_admin_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="admin_back")]])
