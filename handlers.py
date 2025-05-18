import re
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_IDS, REFERRAL_CODE, QUEUE_LIMIT, NOTIFY_POSITION, PAYOUT_BOT_USERNAME, PAGE_SIZE, logger
from database import Database
from keyboards import user_panel, admin_panel, cancel_button, admin_cancel_button, process_buttons, pagination_buttons, user_management_buttons
from datetime import datetime

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
        logger.info(f"User {chat_id} registered with referral code")
        return

    if user_data[4] == "banned":
        await update.message.reply_text("Вы заблокированы.")
        return

    if "awaiting_number" in context.user_data:
        if not re.match(r"^\+\d{10,15}$", text):
            await update.message.reply_text("Номер должен быть в формате +1234567890.", reply_markup=cancel_button())
            return
        if db.get_user_queue_count(chat_id) >= QUEUE_LIMIT:
            await update.message.reply_text(f"Лимит {QUEUE_LIMIT} номера в очереди.", reply_markup=cancel_button())
            return
        db.add_to_queue(chat_id, text)
        context.user_data.pop("awaiting_number")
        await update.message.reply_text("Номер добавлен в очередь.", reply_markup=user_panel())
        queue = db.get_queue()
        for i, entry in enumerate(queue):
            if i + 1 == NOTIFY_POSITION:
                await context.bot.send_message(entry[1], "Ваш номер скоро будет взят, подготовьтесь.")
        await notify_admins(context, f"Новая заявка: Chat ID: {chat_id}, Номер: {text}")
        logger.info(f"User {chat_id} added number {text} to queue")
        return

    if "awaiting_balance" in context.user_data and update.message.from_user.id in ADMIN_IDS:
        args = text.split()
        if len(args) != 2:
            await update.message.reply_text("Формат: <chat_id> <сумма>", reply_markup=admin_cancel_button())
            return
        try:
            target_chat_id = int(args[0])
            amount = float(args[1])
            db.update_balance(target_chat_id, amount)
            context.user_data.pop("awaiting_balance")
            await update.message.reply_text(f"Баланс обновлён: Chat ID: {target_chat_id}, Сумма: ${amount:.2f}", reply_markup=admin_panel())
            await context.bot.send_message(target_chat_id, f"Ваш баланс пополнен на ${amount:.2f}")
            logger.info(f"Admin added ${amount:.2f} to {target_chat_id}")
        except Exception as e:
            await update.message.reply_text(f"Ошибка: {str(e)}", reply_markup=admin_cancel_button())
        return

    if "awaiting_ban" in context.user_data and update.message.from_user.id in ADMIN_IDS:
        try:
            target_chat_id = int(text)
            db.update_user_status(target_chat_id, "banned")
            context.user_data.pop("awaiting_ban")
            await update.message.reply_text(f"Пользователь {target_chat_id} заблокирован.", reply_markup=admin_panel())
            await context.bot.send_message(target_chat_id, "Вы заблокированы.")
            logger.info(f"User {target_chat_id} banned by admin")
        except Exception as e:
            await update.message.reply_text(f"Ошибка: {str(e)}", reply_markup=admin_cancel_button())
        return

    if "awaiting_unban" in context.user_data and update.message.from_user.id in ADMIN_IDS:
        try:
            target_chat_id = int(text)
            db.update_user_status(target_chat_id, "active")
            context.user_data.pop("awaiting_unban")
            await update.message.reply_text(f"Пользователь {target_chat_id} разблокирован.", reply_markup=admin_panel())
            await context.bot.send_message(target_chat_id, "Вы разблокированы.")
            logger.info(f"User {target_chat_id} unbanned by admin")
        except Exception as e:
            await update.message.reply_text(f"Ошибка: {str(e)}", reply_markup=admin_cancel_button())
        return

    await update.message.reply_text("Используйте кнопки для действий.", reply_markup=user_panel())

async def show_user_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    balance = Database(context.bot_data["db_file"]).get_balance(update.effective_chat.id)
    text = f"Ваш баланс: ${balance:.2f}\nВыберите действие:"
    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=user_panel())
    else:
        await update.message.reply_text(text, reply_markup=user_panel())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    db = Database(context.bot_data["db_file"])
    chat_id = query.from_user.id

    if query.data == "add_number":
        context.user_data["awaiting_number"] = True
        await query.message.edit_text("Введите номер в формате +1234567890.", reply_markup=cancel_button())

    elif query.data.startswith("queue_"):
        page = int(query.data.split("_")[1])
        queue = db.get_queue(offset=page * PAGE_SIZE, limit=PAGE_SIZE)
        user_queue = [entry for entry in queue if entry[1] == chat_id]
        if not user_queue:
            await query.message.edit_text("Ваша очередь пуста.", reply_markup=pagination_buttons(page, db.get_queue_count(), "queue"))
            return
        text = "Ваша очередь:\n"
        for i, entry in enumerate(queue):
            if entry[1] == chat_id:
                text += f"{i+1+page*PAGE_SIZE}. {entry[2]} ({entry[3]})\n"
        await query.message.edit_text(text, reply_markup=pagination_buttons(page, db.get_queue_count(), "queue"))

    elif query.data.startswith("archive_"):
        page = int(query.data.split("_")[1])
        archive = db.get_archive(chat_id, offset=page * PAGE_SIZE, limit=PAGE_SIZE)
        if not archive:
            await query.message.edit_text("Архив пуст.", reply_markup=pagination_buttons(page, db.get_archive_count(chat_id), "archive"))
            return
        text = "Архив:\n"
        for entry in archive:
            text += f"{entry[0]}: {entry[1]} ({datetime.fromtimestamp(entry[2]).strftime('%Y-%m-%d')})\n"
        await query.message.edit_text(text, reply_markup=pagination_buttons(page, db.get_archive_count(chat_id), "archive"))

    elif query.data == "stats":
        total_users, daily_submissions = db.get_stats()
        text = f"Статистика:\nУчастников: {total_users}\nСдано сегодня: {daily_submissions}"
        await query.message.edit_text(text, reply_markup=user_panel())

    elif query.data == "balance":
        balance = db.get_balance(chat_id)
        await query.message.edit_text(f"Ваш баланс: ${balance:.2f}", reply_markup=user_panel())

    elif query.data == "payout":
        balance = db.get_balance(chat_id)
        if balance <= 0:
            await query.message.edit_text("Ваш баланс пуст.", reply_markup=user_panel())
            return
        await query.message.edit_text(
            f"Заявка на выплату (${balance:.2f}) создана.\nПерейдите в {PAYOUT_BOT_USERNAME} для подачи.",
            reply_markup=user_panel()
        )
        await notify_admins(context, f"Заявка на выплату: Chat ID: {chat_id}, Сумма: ${balance:.2f}")
        logger.info(f"User {chat_id} requested payout: ${balance:.2f}")

    elif query.data == "support":
        await query.message.edit_text(f"Для поддержки перейдите в {PAYOUT_BOT_USERNAME}.", reply_markup=user_panel())

    elif query.data == "cancel":
        context.user_data.clear()
        await show_user_panel(update, context)

    elif query.data.startswith("admin_queue_"):
        if query.from_user.id not in ADMIN_IDS:
            await query.message.edit_text("Доступно только администраторам.")
            return
        page = int(query.data.split("_")[2])
        queue = db.get_queue(offset=page * PAGE_SIZE, limit=PAGE_SIZE)
        if not queue:
            await query.message.edit_text("Очередь пуста.", reply_markup=pagination_buttons(page, db.get_queue_count(), "admin_queue"))
            return
        text = "Очередь:\n"
        for i, entry in enumerate(queue):
            text += f"ID: {entry[0]}, Chat ID: {entry[1]}, Номер: {entry[2]}, Статус: {entry[3]}\n"
        await query.message.edit_text(text, reply_markup=pagination_buttons(page, db.get_queue_count(), "admin_queue"))

    elif query.data == "admin_balance":
        if query.from_user.id not in ADMIN_IDS:
            await query.message.edit_text("Доступно только администраторам.")
            return
        context.user_data["awaiting_balance"] = True
        await query.message.edit_text("Отправьте: <chat_id> <сумма>", reply_markup=admin_cancel_button())

    elif query.data == "admin_process":
        if query.from_user.id not in ADMIN_IDS:
            await query.message.edit_text("Доступно только администраторам.")
            return
        queue = db.get_queue(limit=1)
        if not queue:
            await query.message.edit_text("Очередь пуста.", reply_markup=admin_panel())
            return
        entry = queue[0]
        text = f"Заявка ID: {entry[0]}\nНомер: {entry[2]}\nСтатус: {entry[3]}"
        await query.message.edit_text(text, reply_markup=process_buttons(entry[0]))

    elif query.data == "admin_stats":
        if query.from_user.id not in ADMIN_IDS:
            await query.message.edit_text("Доступно только администраторам.")
            return
        total_users, daily_submissions = db.get_stats()
        text = f"Статистика:\nУчастников: {total_users}\nСдано сегодня: {daily_submissions}"
        await query.message.edit_text(text, reply_markup=admin_panel())

    elif query.data == "admin_users":
        if query.from_user.id not in ADMIN_IDS:
            await query.message.edit_text("Доступно только администраторам.")
            return
        await query.message.edit_text("Выберите действие:", reply_markup=user_management_buttons())

    elif query.data == "admin_ban":
        if query.from_user.id not in ADMIN_IDS:
            await query.message.edit_text("Доступно только администраторам.")
            return
        context.user_data["awaiting_ban"] = True
        await query.message.edit_text("Отправьте: <chat_id>", reply_markup=admin_cancel_button())

    elif query.data == "admin_unban":
        if query.from_user.id not in ADMIN_IDS:
            await query.message.edit_text("Доступно только администраторам.")
            return
        context.user_data["awaiting_unban"] = True
        await query.message.edit_text("Отправьте: <chat_id>", reply_markup=admin_cancel_button())

    elif query.data.startswith("process_"):
        if query.from_user.id not in ADMIN_IDS:
            await query.message.edit_text("Доступно только администраторам.")
            return
        status = query.data.split("_")[1]
        queue_id = int(query.data.split("_")[2])
        db.update_queue_status(queue_id, status)
        queue = db.get_queue()
        for i, entry in enumerate(queue):
            if i + 1 == NOTIFY_POSITION:
                await context.bot.send_message(entry[1], "Ваш номер скоро будет взят, подготовьтесь.")
        await query.message.edit_text(f"Заявка {queue_id} обработана: {status}", reply_markup=process_buttons(queue[0][0]) if queue else admin_panel())
        logger.info(f"Admin processed queue ID {queue_id} as {status}")

    elif query.data == "admin_cancel":
        context.user_data.clear()
        await show_admin_panel(update, context)

    elif query.data == "admin_back":
        await show_admin_panel(update, context)

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("Доступно только администраторам.")
        return
    if update.callback_query:
        await update.callback_query.message.edit_text("Админ-панель:", reply_markup=admin_panel())
    else:
        await update.message.reply_text("Админ-панель:", reply_markup=admin_panel())

async def notify_admins(context: ContextTypes.DEFAULT_TYPE, message: str):
    for admin_id in ADMIN_IDS:
        await context.bot.send_message(admin_id, message)
