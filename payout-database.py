import sqlite3
from datetime import datetime
from payout_config import logger

class PayoutDatabase:
    def __init__(self, db_file):
        self.db_file = db_file
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS payout_requests
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER,
                          amount REAL, status TEXT, timestamp INTEGER)''')
            c.execute('''CREATE TABLE IF NOT EXISTS support
                         (chat_id INTEGER PRIMARY KEY, status TEXT)''')
            conn.commit()

    def add_payout_request(self, chat_id, amount):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute('''INSERT INTO payout_requests (chat_id, amount, status, timestamp)
                         VALUES (?, ?, ?, ?)''',
                      (chat_id, amount, "pending", int(datetime.now().timestamp())))
            conn.commit()

    def get_payout_requests(self):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute("SELECT id, chat_id, amount, status FROM payout_requests")
            return c.fetchall()

    def update_payout_status(self, request_id, status):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute("UPDATE payout_requests SET status = ? WHERE id = ?", (status, request_id))
            conn.commit()

    def set_support_status(self, status):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO support (chat_id, status) VALUES (?, ?)", (0, status))
            conn.commit()

    def get_support_status(self):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute("SELECT status FROM support WHERE chat_id = 0")
            result = c.fetchone()
            return result[0] if result else "active"
