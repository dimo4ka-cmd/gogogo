import sqlite3
from datetime import datetime
import logging

class Database:
    def __init__(self, db_file):
        self.db_file = db_file
        self.logger = logging.getLogger("database")
        self.init_db()

    def init_db(self):
        try:
            with sqlite3.connect(self.db_file) as conn:
                c = conn.cursor()
                c.execute('''CREATE TABLE IF NOT EXISTS users (
                    chat_id INTEGER PRIMARY KEY,
                    username TEXT,
                    referral_code TEXT,
                    balance REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'active'
                )''')
                c.execute('''CREATE TABLE IF NOT EXISTS queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    number TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at INTEGER
                )''')
                c.execute('''CREATE TABLE IF NOT EXISTS archive (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    number TEXT,
                    status TEXT,
                    created_at INTEGER
                )''')
                conn.commit()
                self.logger.info("Database initialized successfully")
        except sqlite3.Error as e:
            self.logger.error(f"Database initialization error: {str(e)}")
            raise

    def add_user(self, chat_id, username, referral_code):
        try:
            with sqlite3.connect(self.db_file) as conn:
                c = conn.cursor()
                c.execute("INSERT OR REPLACE INTO users (chat_id, username, referral_code) VALUES (?, ?, ?)",
                          (chat_id, username, referral_code))
                conn.commit()
                self.logger.info(f"Added user {chat_id}")
        except sqlite3.Error as e:
            self.logger.error(f"Error adding user {chat_id}: {str(e)}")
            raise

    def get_user(self, chat_id):
        try:
            with sqlite3.connect(self.db_file) as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
                return c.fetchone()
        except sqlite3.Error as e:
            self.logger.error(f"Error getting user {chat_id}: {str(e)}")
            return None

    def update_user_status(self, chat_id, status):
        try:
            with sqlite3.connect(self.db_file) as conn:
                c = conn.cursor()
                c.execute("UPDATE users SET status = ? WHERE chat_id = ?", (status, chat_id))
                conn.commit()
                self.logger.info(f"Updated status for user {chat_id} to {status}")
        except sqlite3.Error as e:
            self.logger.error(f"Error updating user status {chat_id}: {str(e)}")
            raise

    def add_to_queue(self, chat_id, number):
        try:
            with sqlite3.connect(self.db_file) as conn:
                c = conn.cursor()
                c.execute("INSERT INTO queue (chat_id, number, created_at) VALUES (?, ?, ?)",
                          (chat_id, number, int(datetime.now().timestamp())))
                conn.commit()
                self.logger.info(f"Added number to queue for {chat_id}")
        except sqlite3.Error as e:
            self.logger.error(f"Error adding to queue for {chat_id}: {str(e)}")
            raise

    def get_queue(self, offset=0, limit=None):
        try:
            with sqlite3.connect(self.db_file) as conn:
                c = conn.cursor()
                if limit is not None:
                    c.execute("SELECT * FROM queue WHERE status = 'pending' ORDER BY created_at LIMIT ? OFFSET ?",
                              (limit, offset))
                else:
                    c.execute("SELECT * FROM queue WHERE status = 'pending' ORDER BY created_at")
                result = c.fetchall()
                self.logger.info(f"Retrieved queue (offset={offset}, limit={limit}): {len(result)} items")
                return result
        except sqlite3.Error as e:
            self.logger.error(f"Error retrieving queue: {str(e)}")
            return []

    def get_queue_count(self):
        try:
            with sqlite3.connect(self.db_file) as conn:
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM queue WHERE status = 'pending'")
                count = c.fetchone()[0]
                self.logger.info(f"Queue count: {count}")
                return count
        except sqlite3.Error as e:
            self.logger.error(f"Error getting queue count: {str(e)}")
            return 0

    def get_user_queue_count(self, chat_id):
        try:
            with sqlite3.connect(self.db_file) as conn:
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM queue WHERE chat_id = ? AND status = 'pending'", (chat_id,))
                count = c.fetchone()[0]
                self.logger.info(f"User {chat_id} queue count: {count}")
                return count
        except sqlite3.Error as e:
            self.logger.error(f"Error getting user queue count for {chat_id}: {str(e)}")
            return 0

    def update_queue_status(self, queue_id, status):
        try:
            with sqlite3.connect(self.db_file) as conn:
                c = conn.cursor()
                c.execute("SELECT chat_id, number, created_at FROM queue WHERE id = ?", (queue_id,))
                entry = c.fetchone()
                if entry:
                    c.execute("INSERT INTO archive (chat_id, number, status, created_at) VALUES (?, ?, ?, ?)",
                              (entry[0], entry[1], status, entry[2]))
                    c.execute("DELETE FROM queue WHERE id = ?", (queue_id,))
                    conn.commit()
                    self.logger.info(f"Updated queue status for ID {queue_id} to {status}")
                else:
                    self.logger.warning(f"Queue ID {queue_id} not found")
        except sqlite3.Error as e:
            self.logger.error(f"Error updating queue status for ID {queue_id}: {str(e)}")
            raise

    def get_archive(self, chat_id, offset=0, limit=None):
        try:
            with sqlite3.connect(self.db_file) as conn:
                c = conn.cursor()
                if limit is not None:
                    c.execute("SELECT id, number, status, created_at FROM archive WHERE chat_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                              (chat_id, limit, offset))
                else:
                    c.execute("SELECT id, number, status, created_at FROM archive WHERE chat_id = ? ORDER BY created_at DESC",
                              (chat_id,))
                result = c.fetchall()
                self.logger.info(f"Retrieved archive for {chat_id} (offset={offset}, limit={limit}): {len(result)} items")
                return result
        except sqlite3.Error as e:
            self.logger.error(f"Error retrieving archive for {chat_id}: {str(e)}")
            return []

    def get_archive_count(self, chat_id):
        try:
            with sqlite3.connect(self.db_file) as conn:
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM archive WHERE chat_id = ?", (chat_id,))
                count = c.fetchone()[0]
                self.logger.info(f"Archive count for {chat_id}: {count}")
                return count
        except sqlite3.Error as e:
            self.logger.error(f"Error getting archive count for {chat_id}: {str(e)}")
            return 0

    def update_balance(self, chat_id, amount):
        try:
            with sqlite3.connect(self.db_file) as conn:
                c = conn.cursor()
                c.execute("UPDATE users SET balance = balance + ? WHERE chat_id = ?", (amount, chat_id))
                conn.commit()
                self.logger.info(f"Updated balance for {chat_id} by {amount}")
        except sqlite3.Error as e:
            self.logger.error(f"Error updating balance for {chat_id}: {str(e)}")
            raise

    def get_balance(self, chat_id):
        try:
            with sqlite3.connect(self.db_file) as conn:
                c = conn.cursor()
                c.execute("SELECT balance FROM users WHERE chat_id = ?", (chat_id,))
                result = c.fetchone()
                balance = result[0] if result else 0.0
                self.logger.info(f"Retrieved balance for {chat_id}: {balance}")
                return balance
        except sqlite3.Error as e:
            self.logger.error(f"Error getting balance for {chat_id}: {str(e)}")
            return 0.0

    def get_stats(self):
        try:
            with sqlite3.connect(self.db_file) as conn:
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM users")
                total_users = c.fetchone()[0] or 0
                today = int(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
                c.execute("SELECT COUNT(*) FROM archive WHERE created_at >= ?", (today,))
                daily_submissions = c.fetchone()[0] or 0
                self.logger.info(f"Retrieved stats: users={total_users}, daily_submissions={daily_submissions}")
                return total_users, daily_submissions
        except sqlite3.Error as e:
            self.logger.error(f"Error getting stats: {str(e)}")
            return 0, 0
