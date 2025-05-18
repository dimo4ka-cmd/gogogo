from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from payout_config import BOT_TOKEN, DB_FILE, logger
from payout_handlers import start, request_payout, ask_question, admin, set_support_status, reply, block_user, show_payout_panel, button_handler, admin_button_handler

async def error_handler(update, context):
    logger.error(f"Update {update} caused error {context.error}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.bot_data["db_file"] = DB_FILE

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("request_payout", request_payout))
    app.add_handler(CommandHandler("ask", ask_question))
    app.add_handler(CommandHandler("set_support", set_support_status))
    app.add_handler(CommandHandler("reply", reply))
    app.add_handler(CommandHandler("block", block_user))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(payout_request|ask_question|back)$"))
    app.add_handler(CallbackQueryHandler(admin_button_handler, pattern="^(admin_payouts|admin_support|admin_reply|admin_back)$"))
    app.add_error_handler(error_handler)

    app.run_polling()

if __name__ == "__main__":
    main()
