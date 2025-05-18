from telegram import Update
from telegram.ext import ContextTypes
from payout_config import ADMIN_IDS, PAGE_SIZE, logger
from payout_database import PayoutDatabase
from payout_keyboards import payout_panel, admin_payout_panel, cancel_button, admin_cancel_button, support_status_buttons, payout_status_buttons, pagination_buttons

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_payout_panel(update, context)
    logger.info("User initiated /start in payout bot")

async def show_payout_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = PayoutDatabase(context.bot_data["db_file"])
    support_status = db.get_support_status()
    text = f"Статус поддержки: {support_status}\nВыберите действие:"
    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=payout_panel())
    else:
        await update.message.reply_text(text, reply_markup=payout_panel())
    logger.info(f"User {update.effective_chat.id} opened payout panel")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    db = PayoutDatabase(context.bot_data["db_file"])
    chat_id = query.from_user.id
    callback_data = query.data
    logger.info(f"User {chat_id} pressed button: {callback_data}")

    try:
        if callback_data == "payout_request":
            context.user_data["awaiting_payout"] = True
            await query.message.edit_text("Введите сумму для выплаты (например, 10.50).", reply_markup=cancel_button())
            logger.info(f"User {chat_id} initiated payout request")

        elif callback_data == "ask_question":
            context.user_data["awaiting_question"] = True
            await query.message.edit_text("Введите ваш вопрос.", reply_markup=cancel_button())
            logger.info(f"User {chat_id} initiated question")

        elif callback_data.startswith("my_payouts_"):
            page = int(callback_data.split("_")[2])
            requests = db.get_payout_requests(offset=page * PAGE_SIZE, limit=PAGE_SIZE)
            requests = [req for req in requests if req[1] == chat_id]
            if not requests:
                await query.message.edit_text("У вас нет заявок на выплату.", reply_markup=pagination_buttons(page, db.get_payout_request_count(), "my_payouts") or payout_panel())
                logger.info(f"User {chat_id} viewed empty payout requests")
                return
            text = "Ваши заявки на выплату:\n"
            for req in requests:
                text += f"ID: {req[0]}, Сумма: ${req[2]:.2f}, Статус: {req[3]}\n"
            await query.message.edit_text(text, reply_markup=pagination_buttons(page, db.get_payout_request_count(), "my_payouts") or payout_panel())
            logger.info(f"User {chat_id} viewed payout requests page {page}")

        elif callback_data == "cancel":
            context.user_data.clear()
            await show_payout_panel(update, context)
            logger.info(f"User {chat_id} cancelled action")

        elif callback_data.startswith("admin_payouts_"):
            if query.from_user.id not in ADMIN_IDS:
                await query.message.edit_text("Доступно только администраторам.")
                logger.warning(f"Non-admin {chat_id} attempted admin action")
                return
            page = int(callback_data.split("_")[2])
            requests = db.get_payout_requests(offset=page * PAGE_SIZE, limit=PAGE_SIZE)
            if not requests:
                await query.message.edit_text("Заявок нет.", reply_markup=pagination_buttons(page, db.get_payout_request_count(), "admin_payouts") or admin_payout_panel())
                logger.info(f"Admin {chat_id} viewed empty payout requests")
                return
            text = "Заявки на выплату:\n"
            for req in requests:
                text += f"ID: {req[0]}, Chat ID: {req[1]}, Сумма: ${req[2]:.2f}, Статус: {req[3]}\n"
            await query.message.edit_text(text, reply_markup=payout_status_buttons(requests[0][0]) if requests else admin_payout_panel())
            logger.info(f"Admin {chat_id} viewed payout requests page {page}")

        elif callback_data == "admin_support":
            if query.from_user.id not in ADMIN_IDS:
                await query.message.edit_text("Доступно только администраторам.")
                logger.warning(f"Non-admin {chat_id} attempted admin action")
                return
            await query.message.edit_text("Установите статус поддержки:", reply_markup=support_status_buttons())
            logger.info(f"Admin {chat_id} opened support status settings")

        elif callback_data == "admin_reply":
            if query.from_user.id not in ADMIN_IDS:
                await query.message.edit_text("Доступно только администраторам.")
                logger.warning(f"Non-admin {chat_id} attempted admin action")
                return
            context.user_data["awaiting_reply"] = True
            await query.message.edit_text("Введите: <chat_id> <сообщение>", reply_markup=admin_cancel_button())
            logger.info(f"Admin {chat_id} initiated reply")

        elif callback_data == "admin_block":
            if query.from_user.id not in ADMIN_IDS:
                await query.message.edit_text("Доступно только администраторам.")
                logger.warning(f"Non-admin {chat_id} attempted admin action")
                return
            context.user_data["awaiting_block"] = True
            await query.message.edit_text("Введите: <chat_id>", reply_markup=admin_cancel_button())
            logger.info(f"Admin {chat_id} initiated block")

        elif callback_data == "set_support_active":
            if query.from_user.id not in ADMIN_IDS:
                await query.message.edit_text("Доступно только администраторам.")
                logger.warning(f"Non-admin {chat_id} attempted admin action")
                return
            db.set_support_status("active")
            await query.message.edit_text("Статус поддержки: active", reply_markup=admin_payout_panel())
            logger.info(f"Admin {chat_id} set support status to active")

        elif callback_data == "set_support_inactive":
            if query.from_user.id not in ADMIN_IDS:
                await query.message.edit_text("Доступно только администраторам.")
                logger.warning(f"Non-admin {chat_id} attempted admin action")
                return
            db.set_support_status("inactive")
            await query.message.edit_text("Статус поддержки: inactive", reply_markup=admin_payout_panel())
            logger.info(f"Admin {chat_id} set support status to inactive")

        elif callback_data.startswith("payout_"):
            if query.from_user.id not in ADMIN_IDS:
                await query.message.edit_text("Доступно только администраторам.")
                logger.warning(f"Non-admin {chat_id} attempted admin action")
                return
            action, request_id = callback_data.split("_")[1], int(callback_data.split("_")[2])
            status = "approved" if action == "approve" else "rejected"
            db.update_payout_status(request_id, status)
            requests = db.get_payout_requests(limit=1)
            await query.message.edit_text(
                f"Заявка {request_id} {status}",
                reply_markup=payout_status_buttons(requests[0][0]) if requests else admin_payout_panel()
            )
            logger.info(f"Admin {chat_id} processed payout request {request_id} as {status}")

        elif callback_data == "admin_cancel":
            context.user_data.clear()
            await show_admin_payout_panel(update, context)
            logger.info(f"Admin {chat_id} cancelled action")

        elif callback_data == "admin_back":
            await show_admin_payout_panel(update, context)
            logger.info(f"Admin {chat_id} returned to admin payout panel")

        else:
            await query.message.edit_text("Неизвестное действие. Используйте кнопки.", reply_markup=payout_panel())
            logger.warning(f"User {chat_id} triggered unknown callback: {callback_data}")

    except Exception as e:
        await query.message.edit_text("Произошла ошибка. Попробуйте снова.", reply_markup=payout_panel())
        logger.error(f"Button handler error for {chat_id}, callback {callback_data}: {str(e)}")

async def handle_payout_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text
    db = PayoutDatabase(context.bot_data["db_file"])
    logger.info(f"User {chat_id} sent input: {text}")

    try:
        if "awaiting_payout" in context.user_data:
            amount = float(text)
            if amount <= 0:
                await update.message.reply_text("Сумма должна быть положительной.", reply_markup=cancel_button())
                logger.warning(f"User {chat_id} entered invalid payout amount: {text}")
                return
            db.add_payout_request(chat_id, amount)
            context.user_data.clear()
            await update.message.reply_text("Заявка на выплату успешно создана.", reply_markup=payout_panel())
            for admin_id in ADMIN_IDS:
                await context.bot.send_message(
                    admin_id,
                    f"Новая заявка на выплату: Chat ID: {chat_id}, Сумма: ${amount:.2f}"
                )
            logger.info(f"User {chat_id} requested payout: ${amount:.2f}")

        elif "awaiting_question" in context.user_data:
            for admin_id in ADMIN_IDS:
                await context.bot.send_message(
                    admin_id,
                    f"Вопрос от Chat ID: {chat_id}\n{text}"
                )
            context.user_data.clear()
            await update.message.reply_text("Вопрос успешно отправлен.", reply_markup=payout_panel())
            logger.info(f"User {chat_id} asked: {text}")

        else:
            await update.message.reply_text("Пожалуйста, используйте кнопки.", reply_markup=payout_panel())
            logger.info(f"User {chat_id} sent unhandled input: {text}")

    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}", reply_markup=cancel_button())
        logger.error(f"Payout input error for {chat_id}: {str(e)}")

async def handle_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("Доступно только администраторам.")
        logger.warning(f"Non-admin {update.message.from_user.id} attempted admin input")
        return
    text = update.message.text
    db = PayoutDatabase(context.bot_data["db_file"])
    logger.info(f"Admin {update.message.from_user.id} sent input: {text}")

    try:
        if "awaiting_reply" in context.user_data:
            args = text.split(maxsplit=1)
            if len(args) != 2:
                await update.message.reply_text("Формат: <chat_id> <сообщение>", reply_markup=admin_cancel_button())
                logger.warning(f"Admin {update.message.from_user.id} entered invalid reply input: {text}")
                return
            chat_id = int(args[0])
            message = args[1]
            await context.bot.send_message(chat_id, f"Администратор: {message}")
            context.user_data.clear()
            await update.message.reply_text(f"Сообщение отправлено: {chat_id}", reply_markup=admin_payout_panel())
            logger.info(f"Admin replied to {chat_id}: {message}")

        elif "awaiting_block" in context.user_data:
            chat_id = int(text)
            with sqlite3.connect(context.bot_data["db_file"]) as conn:
                c = conn.cursor()
                c.execute("UPDATE users SET status = ? WHERE chat_id = ?", ("banned", chat_id))
                conn.commit()
            await context.bot.send_message(chat_id, "Вы заблокированы.")
            context.user_data.clear()
            await update.message.reply_text(f"Пользователь {chat_id} заблокирован.", reply_markup=admin_payout_panel())
            logger.info(f"User {chat_id} blocked by admin")

        else:
            await update.message.reply_text("Пожалуйста, используйте кнопки.", reply_markup=admin_payout_panel())
            logger.info(f"Admin {update.message.from_user.id} sent unhandled input: {text}")

    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}", reply_markup=admin_cancel_button())
        logger.error(f"Admin input error for {update.message.from_user.id}: {str(e)}")

async def show_admin_payout_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("Доступно только администраторам.")
        logger.warning(f"Non-admin {update.message.from_user.id} attempted admin panel access")
        return
    if update.callback_query:
        await update.callback_query.message.edit_text("Админ-панель (выплаты):", reply_markup=admin_payout_panel())
    else:
        await update.message.reply_text("Админ-панель (выплаты):", reply_markup=admin_payout_panel())
    logger.info(f"Admin {update.effective_chat.id} opened admin payout panel")
