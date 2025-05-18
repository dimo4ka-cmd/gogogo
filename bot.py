import os
import psutil
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from config import BOT_TOKEN, DB_FILE, logger
from handlers import start, handle_message, show_user_panel, button_handler, show_admin_panel

async def error_handler(update, context):
    logger.error(f"Update {update} caused error {context.error}")

def is_bot_running(script_name):
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if script_name in ' '.join(proc.info['cmdline']):
                return proc.info['pid'] != os.getpid()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def main():
    if is_bot_running(__file__):
        logger.error(f"Another instance of {__file__} is already running. Exiting.")
        exit(1)

    try:
        app = Application.builder().token(BOT_TOKEN).build()
        app.bot_data["db_file"] = DB_FILE

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("admin", show_admin_panel))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.add_handler(CallbackQueryHandler(button_handler))
        app.add_error_handler(error_handler)

        logger.info("Starting main bot")
        app.run_polling(allowed_updates=["message", "callback_query"])
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")
        raise

if __name__ == "__main__":
    main()
