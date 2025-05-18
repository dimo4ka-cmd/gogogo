import re
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_IDS, REFERRAL_CODE, QUEUE_LIMIT, NOTIFY_POSITION, PAYOUT_BOT_USERNAME, PAGE_SIZE, logger
from database import Database
from keyboards import user_panel, admin_panel, cancel_button, admin_cancel_button, process_buttons, pagination_buttons, user_management_buttons
from datetime import datetime

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"User {update.effective_chat.id} initiated /start")
    await update.message.reply_text("Введите реферальный код для регистрации.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text
    user = update.message.from_user
    db = Database(context.bot_data["db_file"])
    logger.info(f"User {chat_id} sent message: {text}")

    user_data = db.get_user(chat_id)
    if not user_data:
        if text != REFERRAL_CODE:
            await update.message.reply_text("Неверный реферальный код. Попробуйте снова.")
            logger.warning(f"User {chat_id} entered invalid referral code: {text}")
            return
        db.add_user(chat_id, user.username or user.first_name, text)
        await show_user_panel(update, context)
        logger.info(f"User {chat_id} registered with referral code")
        return

    if user_data[4] == "banned":
        await update.message.reply_text("Вы заблокированы.")
        logger.info(f"Banned user {chat_id} attempted action")
        return

    if "awaiting_number" in context.user_data:
        if not re.match(r"^\+\d{10,15}$", text):
            await update.message.reply_text("Номер должен быть в формате +1234567890.", reply_markup=cancel_button())
            logger.warning(f"User {chat_id} entered invalid number: {text}")
            return
        if db.get_user_queue_count(chat_id) >= QUEUE_LIMIT:
            await update.message.reply_text(f"Лимит {QUEUE_LIMIT} номера в очереди.", reply_markup=cancel_button())
            logger.info(f"User {chat_id} reached queue limit")
            return
        db.add_to_queue(chat_id, text)
        context.user_data.clear()
        await update.message.reply_text("Номер успешно добавлен в очередь.", reply_markup=user_panel())
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
            logger.warning(f"Admin {chat_id} entered invalid balance input: {text}")
            return
        try:
            target_chat_id = int(args[0])
            amount = float(args[1])
            if amount <= 0:
                await update.message.reply_text("Сумма должна быть положительной.", reply_markup=admin_cancel_button())
                return
            db.update_balance(target_chat_id, amount)
            context.user_data.clear()
            await update.message.reply_text(f"Баланс обновлён: Chat ID: {target_chat_id}, Сумма: ${amount:.2f}", reply_markup=admin_panel())
            await context.bot.send_message(target_chat_id, f"Ваш баланс пополнен на ${amount:.2f}")
            logger.info(f"Admin added ${amount:.2f} to {target_chat_id}")
        except Exception as e:
            await update.message.reply_text(f"Ошибка: {str(e)}", reply_markup=admin_cancel_button())
            logger.error(f"Balance update error for {chat_id}: {str(e)}")
        return

    if "awaiting_ban" in context.user_data and update.message.from_user.id in ADMIN_IDS:
        try:
            target_chat_id = int(text)
            db.update_user_status(target_chat_id, "banned")
            context.user_data.clear()
            await update.message.reply_text(f"Пользователь {target_chat_id} заблокирован.", reply_markup=admin_panel())
            await context.bot.send_message(target_chat_id, "Вы заблокированы.")
            logger.info(f"User {target_chat_id} banned by admin")
        except Exception as e:
            await update.message.reply_text(f"Ошибка: {str(e)}", reply_markup=admin_cancel_button())
            logger.error(f"Ban error for {chat_id}: {str(e)}")
        return

    if "awaiting_unban" in context.user_data and update.message.from_user.id in ADMIN_IDS:
        try:
            target_chat_id = int(text)
            db.update_user_status(target_chat_id, "active")
            context.user_data.clear()
            await update.message.reply_text(f"Пользователь {target_chat_id} разблокирован.", reply_markup=admin_panel())
            await context.bot.send_message(target_chat_id, "Вы разблокированы.")
            logger.info(f"User {target_chat_id} unbanned by admin")
        except Exception as e:
            await update.message.reply_text(f"Ошибка: {str(e)}", reply_markup=admin_cancel_button())
            logger.error(f"Unban error for {chat_id}: {str(e)}")
        return

    await update.message.reply_text("Пожалуйста, используйте кнопки для действий.", reply_markup=user_panel())
    logger.info(f"User {chat_id} sent unhandled message: {text}")

async def show_user_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = Database(context.bot_data["db_file"])
    balance = db.get_balance(update.effective_chat.id)
    text = f"Ваш баланс: ${balance:.2f}\nВыберите действие:"
    try:
        if update.callback_query:
            await update.callback_query.message.edit_text(text, reply_markup=user_panel())
        else:
            await update.message.reply_text(text, reply_markup=user_panel())
        logger.info(f"User {update.effective_chat.id} opened user panel")
    except Exception as e:
        logger.error(f"Error showing user panel for {update.effective_chat.id}: {str(e)}")
        if update.message:
            await update.message.reply_text("Ошибка при открытии панели. Попробуйте снова.", reply_markup=user_panel())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        logger.error("Received update without callback_query")
        return
    chat_id = query.from_user.id
    callback_data = query.data
    logger.info(f"User {chat_id} pressed button with callback: {callback_data}")

    try:
        await query.answer()  # Подтверждаем получение callback
        db = Database(context.bot_data["db_file"])

        if callback_data == "add_number":
            context.user_data["awaiting_number"] = True
            await query.message.edit_text("Введите номер в формате +1234567890.", reply_markup=cancel_button())
            logger.info(f"User {chat_id} initiated number addition")

        elif callback_data.startswith("queue_"):
            page = int(callback_data.split("_")[1])
            queue = db.get_queue(offset=page * PAGE_SIZE, limit=PAGE_SIZE)
            user_queue = [entry for entry in queue if entry[1] == chat_id]
            if not user_queue:
                await query.message.edit_text("Ваша очередь пуста.", reply_markup=pagination_buttons(page, db.get_queue_count(), "queue") or user_panel())
                logger.info(f"User {chat_id} viewed empty queue")
                return
            text = "Ваша очередь:\n"
            for i, entry in enumerate(queue):
                if entry[1] == chat_id:
                    text += f"{i+1+page*PAGE_SIZE}. {entry[2]} ({entry[3]})\n"
            await query.message.edit_text(text, reply_markup=pagination_buttons(page, db.get_queue_count(), "queue") or user_panel())
            logger.info(f"User {chat_id} viewed queue page {page}")

        elif callback_data.startswith("archive_"):
            page = int(callback_data.split("_")[1])
            archive = db.get_archive(chat_id, offset=page * PAGE_SIZE, limit=PAGE_SIZE)
            if not archive:
                await query.message.edit_text("Архив пуст.", reply_markup=pagination_buttons(page, db.get_archive_count(chat_id), "archive") or user_panel())
                logger.info(f"User {chat_id} viewed empty archive")
                return
            text = "Архив:\n"
            for entry in archive:
                text += f"{entry[0]}: {entry[1]} ({datetime.fromtimestamp(entry[2]).strftime('%Y-%m-%d')})\n"
            await query.message.edit_text(text, reply_markup=pagination_buttons(page, db.get_archive_count(chat_id), "archive") or user_panel())
            logger.info(f"User {chat_id} viewed archive page {page}")

        elif callback_data == "stats":
            total_users, daily_submissions = db.get_stats()
            text = f"Статистика:\nУчастников: {total_users}\nСдано сегодня: {daily_submissions}"
            await query.message.edit_text(text, reply_markup=user_panel())
            logger.info(f"User {chat_id} viewed stats")

        elif callback_data == "balance":
            balance = db.get_balance(chat_id)
            await query.message.edit_text(f"Ваш баланс: ${balance:.2f}", reply_markup=user_panel())
            logger.info(f"User {chat_id} viewed balance")

        elif callback_data == "payout":
            balance = db.get_balance(chat_id)
            if balance <= 0:
                await query.message.edit_text("Ваш баланс пуст.", reply_markup=user_panel())
                logger.info(f"User {chat_id} attempted payout with zero balance")
                return
            await query.message.edit_text(
                f"Заявка на выплату (${balance:.2f}) создана.\nПерейдите в {PAYOUT_BOT_USERNAME} для подачи.",
                reply_markup=user_panel()
            )
            await notify_admins(context, f"Заявка на выплату: Chat ID: {chat_id}, Сумма: ${balance:.2f}")
            logger.info(f"User {chat_id} requested payout: ${balance:.2f}")

        elif callback_data == "support":
            await query.message.edit_text(f"Для поддержки перейдите в {PAYOUT_BOT_USERNAME}.", reply_markup=user_panel())
            logger.info(f"User {chat_id} accessed support link")

        elif callback_data == "cancel":
            context.user_data.clear()
            await show_user_panel(update, context)
            logger.info(f"User {chat_id} cancelled action")

        elif callback_data.startswith("admin_queue_"):
            if query.from_user.id not in ADMIN_IDS:
                await query.message.edit_text("Доступно только администраторам.")
                logger.warning(f"Non-admin {chat_id} attempted admin action")
                return
            page = int(callback_data.split("_")[2])
            queue = db.get_queue(offset=page * PAGE_SIZE, limit=PAGE_SIZE)
            if not queue:
                await query.message.edit_text("Очередь пуста.", reply_markup=pagination_buttons(page, db.get_queue_count(), "admin_queue") or admin_panel())
                logger.info(f"Admin {chat_id} viewed empty queue")
                return
            text = "Очередь:\n"
            for i, entry in enumerate(queue):
                text += f"ID: {entry[0]}, Chat ID: {entry[1]}, Номер: {entry[2]}, Статус: {entry[3]}\n"
            await query.message.edit_text(text, reply_markup=pagination_buttons(page, db.get_queue_count(), "admin_queue") or admin_panel())
            logger.info(f"Admin {chat_id} viewed queue page {page}")

        elif callback_data == "admin_balance":
            if query.from_user.id not in ADMIN_IDS:
                await query.message.edit_text("Доступно только администраторам.")
                logger.warning(f"Non-admin {chat_id} attempted admin action")
                return
            context.user_data["awaiting_balance"] = True
            await query.message.edit_text("Введите: <chat_id> <сумма>", reply_markup=admin_cancel_button())
            logger.info(f"Admin {chat_id} initiated balance addition")

        elif callback_data == "admin_process":
            if query.from_user.id not in ADMIN_IDS:
                await query.message.edit_text("Доступно только администраторам.")
                logger.warning(f"Non-admin {chat_id} attempted admin action")
                return
            queue = db.get_queue(limit=1)
            if not queue:
                await query.message.edit_text("Очередь пуста.", reply_markup=admin_panel())
                logger.info(f"Admin {chat_id} found empty queue for processing")
                return
            entry = queue[0]
            text = f"Заявка ID: {entry[0]}\nНомер: {entry[2]}\nСтатус: {entry[3]}"
            await query.message.edit_text(text, reply_markup=process_buttons(entry[0]))
            logger.info(f"Admin {chat_id} started processing queue ID {entry[0]}")

        elif callback_data == "admin_stats":
            if query.from_user.id not in ADMIN_IDS:
                await query.message.edit_text("Доступно только администраторам.")
                logger.warning(f"Non-admin {chat_id} attempted admin action")
                return
            total_users, daily_submissions = db.get_stats()
            text = f"Статистика:\nУчастников: {total_users}\nСдано сегодня: {daily_submissions}"
            await query.message.edit_text(text, reply_markup=admin_panel())
            logger.info(f"Admin {chat_id} viewed stats")

        elif callback_data == "admin_users":
            if query.from_user.id not in ADMIN_IDS:
                await query.message.edit_text("Доступно только администраторам.")
                logger.warning(f"Non-admin {chat_id} attempted admin action")
                return
            await query.message.edit_text("Выберите действие:", reply_markup=user_management_buttons())
            logger.info(f"Admin {chat_id} opened user management")

        elif callback_data == "admin_ban":
            if query.from_user.id not in ADMIN_IDS:
                await query.message.edit_text("Доступно только администраторам.")
                logger.warning(f"Non-admin {chat_id} attempted admin action")
                return
            context.user_data["awaiting_ban"] = True
            await query.message.edit_text("Введите: <chat_id>", reply_markup=admin_cancel_button())
            logger.info(f"Admin {chat_id} initiated ban")

        elif callback_data == "admin_unban":
            if query.from_user.id not in ADMIN_IDS:
                await query.message.edit_text("Доступно только администраторам.")
                logger.warning(f"Non-admin {chat_id} attempted admin action")
                return
            context.user_data["awaiting_unban"] = True
            await query.message.edit_text("Введите: <chat_id>", reply_markup=admin_cancel_button())
            logger.info(f"Admin {chat_id} initiated unban")

        elif callback_data.startswith("process_"):
            if query.from_user.id not in ADMIN_IDS:
                await query.message.edit_text("Доступно только администраторам.")
                logger.warning(f"Non-admin {chat_id} attempted admin action")
                return
            status = callback_data.split("_")[1]
            queue_id = int(callback_data.split("_")[2])
            db.update_queue_status(queue_id, status)
            queue = db.get_queue()
            for i, entry in enumerate(queue):
                if i + 1 == NOTIFY_POSITION:
                    await context.bot.send_message(entry[1], "Ваш номер скоро будет взят, подготовьтесь.")
            next_queue = db.get_queue(limit=1)
            await query.message.edit_text(
                f"Заявка {queue_id} обработана: {status}",
                reply_markup=process_buttons(next_queue[0][0]) if next_queue else admin_panel()
            )
            logger.info(f"Admin {chat_id} processed queue ID {queue_id} as {status}")

        elif callback_data == "admin_cancel":
            context.user_data.clear()
            await show_admin_panel(update, context)
            logger.info(f"Admin {chat_id} cancelled action")

        elif callback_data == "admin_back":
            await show_admin_panel(update, context)
            logger.info(f"Admin {chat_id} returned to admin panel")

        else:
            await query.message.edit_text("Неизвестное действие. Используйте кнопки.", reply_markup=user_panel())
            logger.warning(f"User {chat_id} triggered unknown callback: {callback_data}")

    except Exception as e:
        await query.message.edit_text("Произошла ошибка. Попробуйте снова.", reply_markup=user_panel())
        logger.error(f"Button handler error for {chat_id}, callback {callback_data}: {str(e)}")

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("Доступно только администраторам.")
        logger.warning(f"Non-admin {update.message.from_user.id} attempted admin panel access")
        return
    try:
        if update.callback_query:
            await update.callback_query.message.edit_text("Админ-панель:", reply_markup=admin_panel())
        else:
            await update.message.reply_text("Админ-панель:", reply_markup=admin_panel())
        logger.info(f"Admin {update.effective_chat.id} opened admin panel")
    except Exception as e:
        logger.error(f"Error showing admin panel for {update.effective_chat.id}: {str(e)}")
        if update.message:
            await update.message.reply_text("Ошибка при открытии админ-панели. Попробуйте снова.", reply_markup=admin_panel())

async def notify_admins(context: ContextTypes.DEFAULT_TYPE, message: str):
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(admin_id, message)
            logger.info(f"Sent admin notification to {admin_id}: {message}")
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {str(e)}")
