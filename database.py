import sqlite3
from datetime import datetime
from config import logger

class Database:
    def __init__(self, db_file):
        self.db_file = db_file
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS users
                         (chat_id INTEGER PRIMARY KEY, username TEXT, referral_code TEXT,
                          balance REAL, status TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS queue
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER,
                          phone_number TEXT, status TEXT, timestamp INTEGER)''')
            c.execute('''CREATE TABLE IF NOT EXISTS archive
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER,
                          phone_number TEXT, status TEXT, timestamp INTEGER  INTEGER)''')
            conn.commit()

    def add_user(self, chat_id, username, referral_code):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute('''INSERT OR IGNORE INTO users
                         (chat_id, username, referral_code, balance, status)
                         VALUES (?, ?, ?, ?, ?)''',
                      (chat_id, username, referral_code, 0.0, "active"))
            conn.commit()

    def get_user(self, chat_id):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
            return c.fetchone()

    def add_to_queue(self, chat_id, phone_number):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute('''INSERT INTO queue (chat_id, phone_number, status, timestamp)
                         VALUES (?, ?, ?, ?)''',
                      (chat_id, phone_number, "pending", int(datetime.now().timestamp())))
            conn.commit()

    def get_queue(self):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute("SELECT id, chat_id, phone_number, status FROM queue WHERE status = ? ORDER BY timestamp", ("pending",))
            return c.fetchall()

    def get_user_queue_count(self, chat_id):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM queue WHERE chat_id = ? AND status = ?", (chat_id, "pending"))
            return c.fetchone()[0]

    def update_queue_status(self, queue_id, status):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute("UPDATE queue SET status = ? WHERE id = ?", (status, queue_id))
            c.execute("SELECT chat_id, phone_number FROM queue WHERE id = ?", (queue_id,))
            result = c.fetchone()
            if result:
                chat_id, phone_number = result
                c.execute('''INSERT INTO archive (chat_id, phone_number, status, timestamp)
                             VALUES (?, ?, ?, ?)''',
                          (chat_id, phone_number, status, int(datetime.now().timestamp())))
            conn.commit()

    def get_archive(self, chat_id):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute("SELECT phone_number, status, timestamp FROM archive WHERE chat_id = ?", (chat_id,))
            return c.fetchall()

    def update_balance(self, chat_id, amount):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute("UPDATE users SET balance = balance + ? WHERE chat_id = ?", (amount, chat_id))
            conn.commit()

    def get_balance(self, chat_id):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute("SELECT balance FROM users WHERE chat_id = ?", (chat_id,))
            result = c.fetchone()
            return result[0] if result else 0.0

    def get_stats(self):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM users")
            total_users = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM queue WHERE status != ? AND date(timestamp, 'unixepoch') = date('now')", ("pending",))
            daily_submissions = c.fetchone()[0]
            return total_users, daily_submissions
