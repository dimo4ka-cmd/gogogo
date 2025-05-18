from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from payout_config import ADMIN_IDS, logger
from payout_database import PayoutDatabase

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_payout_panel(update, context)

async def show_payout_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = PayoutDatabase(context.bot_data["db_file"])
    support_status = db.get_support_status()
    keyboard = [
        [InlineKeyboardButton("Заявка на выплату", callback_data="payout_request")],
        [InlineKeyboardButton("Задать вопрос", callback_data="ask_question")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"Статус поддержки: {support_status}\nВыберите действие:"
    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    db = PayoutDatabase(context.bot_data["db_file"])
    chat_id = query.from_user.id

    if query.data == "payout_request":
        await query.message.edit_text("Введите: /request_payout <сумма>", reply_markup=back_button())

    elif query.data == "ask_question":
        await query.message.edit_text("Введите: /ask <вопрос>", reply_markup=back_button())

    elif query.data == "back":
        await show_payout_panel(update, context)

async def request_payout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Использование: /request_payout <сумма>")
        return
    try:
        amount = float(args[0])
        db = PayoutDatabase(context.bot_data["db_file"])
        db.add_payout_request(update.message.chat_id, amount)
        await update.message.reply_text("Заявка на выплату создана.")
        for admin_id in ADMIN_IDS:
            await context.bot.send_message(
                admin_id,
                f"Новая заявка на выплату: Chat ID: {update.message.chat_id}, Сумма: ${amount:.2f}"
            )
        logger.info(f"User {update.message.chat_id} requested payout: ${amount:.2f}")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Использование: /ask <вопрос>")
        return
    question = " ".join(args)
    for admin_id in ADMIN_IDS:
        await context.bot.send_message(
            admin_id,
            f"Вопрос от Chat ID: {update.message.chat_id}\n{question}"
        )
    await update.message.reply_text("Вопрос отправлен.")
    logger.info(f"User {update.message.chat_id} asked: {question}")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("Доступно только администраторам.")
        return
    await show_admin_payout_panel(update, context)

async def show_admin_payout_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Заявки на выплату", callback_data="admin_payouts")],
        [InlineKeyboardButton("Статус поддержки", callback_data="admin_support")],
        [InlineKeyboardButton("Ответить пользователю", callback_data="admin_reply")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.message.edit_text("Админ-панель (выплаты):", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Админ-панель (выплаты):", reply_markup=reply_markup)

async def admin_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    db = PayoutDatabase(context.bot_data["db_file"])

    if query.data == "admin_payouts":
        requests = db.get_payout_requests()
        if not requests:
            await query.message.edit_text("Заявок нет.", reply_markup=back_admin_button())
            return
        text = "Заявки на выплату:\n"
        for req in requests:
            text += f"ID: {req[0]}, Chat ID: {req[1]}, Сумма: ${req[2]:.2f}, Статус: {req[3]}\n"
        await query.message.edit_text(text, reply_markup=back_admin_button())

    elif query.data == "admin_support":
        await query.message.edit_text("Введите: /set_support <active/inactive>", reply_markup=back_admin_button())

    elif query.data == "admin_reply":
        await query.message.edit_text("Введите: /reply <chat_id> <сообщение>", reply_markup=back_admin_button())

    elif query.data == "admin_back":
        await show_admin_payout_panel(update, context)

async def set_support_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("Доступно только администраторам.")
        return
    args = context.args
    if not args or args[0] not in ["active", "inactive"]:
        await update.message.reply_text("Использование: /set_support <active/inactive>")
        return
    db = PayoutDatabase(context.bot_data["db_file"])
    db.set_support_status(args[0])
    await update.message.reply_text(f"Статус поддержки: {args[0]}")
    logger.info(f"Support status set to {args[0]}")

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
        await context.bot.send_message(chat_id, f"Администратор: {message}")
        await update.message.reply_text(f"Сообщение отправлено: {chat_id}")
        logger.info(f"Admin replied to {chat_id}: {message}")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")

async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("Доступно только администраторам.")
        return
    args = context.args
    if not args:
        await update.message.reply_text("Использование: /block <chat_id>")
        return
    try:
        chat_id = int(args[0])
        with sqlite3.connect(context.bot_data["db_file"]) as conn:
            c = conn.cursor()
            c.execute("UPDATE users SET status = ? WHERE chat_id = ?", ("banned", chat_id))
            conn.commit()
        await context.bot.send_message(chat_id, "Вы заблокированы.")
        await update.message.reply_text(f"Пользователь {chat_id} заблокирован.")
        logger.info(f"User {chat_id} blocked by admin")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")

def back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="back")]])

def back_admin_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="admin_back")]])
