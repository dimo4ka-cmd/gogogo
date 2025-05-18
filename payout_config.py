import logging

BOT_TOKEN = "8173922692:AAHwEuTGQpQhIGEm-Gb8kvBvPTLMg-9bAmM"
ADMIN_IDS = [1828106357]
LOG_FILE = "payout_bot.log"
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
