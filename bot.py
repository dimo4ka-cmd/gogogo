from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from config import BOT_TOKEN, DB_FILE, logger
from handlers import start, handle_message, admin, add_balance, process_queue, show_user_panel, button_handler, admin_button_handler

async def error_handler(update, context):
    logger.error(f"Update {update} caused error {context.error}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.bot_data["db_file"] = DB_FILE

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("add_balance", add_balance))
    app.add_handler(CommandHandler("process", process_queue))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(queue|archive|stats|payout|back)$"))
    app.add_handler(CallbackQueryHandler(admin_button_handler, pattern="^(admin_queue|admin_balance|admin_process|admin_back)$"))
    app.add_error_handler(error_handler)

    app.run_polling()

if __name__ == "__main__":
    main()
