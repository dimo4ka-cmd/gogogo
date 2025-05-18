from telegram import Update
from telegram.ext import ContextTypes
from payout_config import ADMIN_IDS, logger
from payout_database import PayoutDatabase
from payout_keyboards import payout_panel, admin_payout_panel, back_button, admin_back_button, support_status_buttons, payout_status_buttons

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_payout_panel(update, context)

async def show_payout_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = PayoutDatabase(context.bot_data["db_file"])
    support_status = db.get_support_status()
    text = f"Статус поддержки: {support_status}\nВыберите действие:"
    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=payout_panel())
    else:
        await update.message.reply_text(text, reply_markup=payout_panel())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    db = PayoutDatabase(context.bot_data["db_file"])
    chat_id = query.from_user.id

    if query.data == "payout_request":
        context.user_data["awaiting_payout"] = True
        await query.message.edit_text("Отправьте сумму для выплаты.", reply_markup=back_button())

    elif query.data == "ask_question":
        context.user_data["awaiting_question"] = True
        await query.message.edit_text("Введите ваш вопрос.", reply_markup=back_button())

    elif query.data == "back":
        context.user_data.pop("awaiting_payout", None)
        context.user_data.pop("awaiting_question", None)
        await show_payout_panel(update, context)

    elif query.data == "admin_payouts":
        requests = db.get_payout_requests()
        if not requests:
            await query.message.edit_text("Заявок нет.", reply_markup=admin_back_button())
            return
        text = "Заявки на выплату:\n"
        for req in requests:
            text += f"ID: {req[0]}, Chat ID: {req[1]}, Сумма: ${req[2]:.2f}, Статус: {req[3]}\n"
        await query.message.edit_text(text, reply_markup=payout_status_buttons(requests[0][0]))

    elif query.data == "admin_support":
        await query.message.edit_text("Установите статус поддержки:", reply_markup=support_status_buttons())

    elif query.data == "admin_reply":
        context.user_data["awaiting_reply"] = True
        await query.message.edit_text("Отправьте: <chat_id> <сообщение>", reply_markup=admin_back_button())

    elif query.data == "admin_block":
        context.user_data["awaiting_block"] = True
        await query.message.edit_text("Отправьте: <chat_id>", reply_markup=admin_back_button())

    elif query.data == "set_support_active":
        db.set_support_status("active")
        await query.message.edit_text("Статус поддержки: active", reply_markup=admin_back_button())
        logger.info("Support status set to active")

    elif query.data == "set_support_inactive":
        db.set_support_status("inactive")
        await query.message.edit_text("Статус поддержки: inactive", reply_markup=admin_back_button())
        logger.info("Support status set to inactive")

    elif query.data.startswith("payout_"):
        action, request_id = query.data.split("_")[1], int(query.data.split("_")[2])
        status = "approved" if action == "approve" else "rejected"
        db.update_payout_status(request_id, status)
        await query.message.edit_text(f"Заявка {request_id} {status}", reply_markup=admin_back_button())
        logger.info(f"Payout request {request_id} {status}")

    elif query.data == "admin_back":
        await show_admin_payout_panel(update, context)

async def handle_payout_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    text = update.message.text
    db = PayoutDatabase(context.bot_data["db_file"])

    if "awaiting_payout" in context.user_data:
        try:
            amount = float(text)
            db.add_payout_request(chat_id, amount)
            context.user_data.pop("awaiting_payout", None)
            await update.message.reply_text("Заявка на выплату создана.", reply_markup=payout_panel())
            for admin_id in ADMIN_IDS:
                await context.bot.send_message(
                    admin_id,
                    f"Новая заявка на выплату: Chat ID: {chat_id}, Сумма: ${amount:.2f}"
                )
            logger.info(f"User {chat_id} requested payout: ${amount:.2f}")
        except Exception as e:
            await update.message.reply_text(f"Ошибка: {str(e)}", reply_markup=back_button())

    elif "awaiting_question" in context.user_data:
        for admin_id in ADMIN_IDS:
            await context.bot.send_message(
                admin_id,
                f"Вопрос от Chat ID: {chat_id}\n{text}"
            )
        context.user_data.pop("awaiting_question", None)
        await update.message.reply_text("Вопрос отправлен.", reply_markup=payout_panel())
        logger.info(f"User {chat_id} asked: {text}")

async def handle_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("Доступно только администраторам.")
        return
    text = update.message.text
    db = PayoutDatabase(context.bot_data["db_file"])

    if "awaiting_reply" in context.user_data:
        args = text.split(maxsplit=1)
        if len(args) != 2:
            await update.message.reply_text("Формат: <chat_id> <сообщение>", reply_markup=admin_back_button())
            return
        try:
            chat_id = int(args[0])
            message = args[1]
            await context.bot.send_message(chat_id, f"Администратор: {message}")
            context.user_data.pop("awaiting_reply", None)
            await update.message.reply_text(f"Сообщение отправлено: {chat_id}", reply_markup=admin_payout_panel())
            logger.info(f"Admin replied to {chat_id}: {message}")
        except Exception as e:
            await update.message.reply_text(f"Ошибка: {str(e)}", reply_markup=admin_back_button())

    elif "awaiting_block" in context.user_data:
        try:
            chat_id = int(text)
            with sqlite3.connect(context.bot_data["db_file"]) as conn:
                c = conn.cursor()
                c.execute("UPDATE users SET status = ? WHERE chat_id = ?", ("banned", chat_id))
                conn.commit()
            await context.bot.send_message(chat_id, "Вы заблокированы.")
            context.user_data.pop("awaiting_block", None)
            await update.message.reply_text(f"Пользователь {chat_id} заблокирован.", reply_markup=admin_payout_panel())
            logger.info(f"User {chat_id} blocked by admin")
        except Exception as e:
            await update.message.reply_text(f"Ошибка: {str(e)}", reply_markup=admin_back_button())

async def show_admin_payout_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("Доступно только администраторам.")
        return
    if update.callback_query:
        await update.callback_query.message.edit_text("Админ-панель (выплаты):", reply_markup=admin_payout_panel())
    else:
        await update.message.reply_text("Админ-панель (выплаты):", reply_markup=admin_payout_panel())
