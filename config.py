import logging

BOT_TOKEN = "7568460242:AAEoecvAVSPgLP-wJCJJXgfmoNsPcuAdWXA"
PAYOUT_BOT_USERNAME = "@hated2testbot"
ADMIN_IDS = [1828106357]
LOG_FILE = "bot.log"
DB_FILE = "users.db"
REFERRAL_CODE = "аренда11"
QUEUE_LIMIT = 3
NOTIFY_POSITION = 3

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
