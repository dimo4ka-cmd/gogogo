from telegram.ext import Application, CommandHandler, MessageHandler, Filters
from config import BOT_TOKEN, DB_FILE, logger
from handlers import start, handle_message, admin, reply, ban, stats

async def error_handler(update, context):
    logger.error(f"Update {update} caused error {context.error}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.bot_data["db_file"] = DB_FILE

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("reply", reply))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    app.add_error_handler(error_handler)

    app.run_polling()

if __name__ == "__main__":
    main()
