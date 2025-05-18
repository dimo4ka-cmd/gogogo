from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from config import BOT_TOKEN, DB_FILE, logger
from handlers import start, handle_message, handle_admin_input, show_user_panel, button_handler, show_admin_panel

async def error_handler(update, context):
    logger.error(f"Update {update} caused error {context.error}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.bot_data["db_file"] = DB_FILE

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", show_admin_panel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_input))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_error_handler(error_handler)

    app.run_polling()

if __name__ == "__main__":
    main()
