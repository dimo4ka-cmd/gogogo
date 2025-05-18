import logging

BOT_TOKEN = "7568460242:AAEoecvAVSPgLP-wJCJJXgfmoNsPcuAdWXA"
ADMIN_IDS = [1828106357]
LOG_FILE = "bot.log"
RATE_LIMIT_SECONDS = 300
DB_FILE = "users.db"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
