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
                         (chat_id INTEGER PRIMARY KEY, phone_number TEXT, username TEXT,
                          status TEXT, last_submission INTEGER)''')
            c.execute('''CREATE TABLE IF NOT EXISTS submissions
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER,
                          phone_number TEXT, timestamp INTEGER)''')
            conn.commit()

    def add_user(self, chat_id, phone_number, username):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute('''INSERT OR REPLACE INTO users
                         (chat_id, phone_number, username, status, last_submission)
                         VALUES (?, ?, ?, ?, ?)''',
                      (chat_id, phone_number, username, "active", int(datetime.now().timestamp())))
            c.execute('''INSERT INTO submissions (chat_id, phone_number, timestamp)
                         VALUES (?, ?, ?)''',
                      (chat_id, phone_number, int(datetime.now().timestamp())))
            conn.commit()

    def get_user(self, chat_id):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
            return c.fetchone()

    def get_all_users(self):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute("SELECT chat_id, phone_number, username, status FROM users")
            return c.fetchall()

    def ban_user(self, chat_id):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute("UPDATE users SET status = ? WHERE chat_id = ?", ("banned", chat_id))
            conn.commit()

    def get_stats(self):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM users")
            total_users = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM users WHERE status = ?", ("banned",))
            banned_users = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM submissions")
            total_submissions = c.fetchone()[0]
            return total_users, banned_users, total_submissions
