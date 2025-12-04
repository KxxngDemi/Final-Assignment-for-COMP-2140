import sqlite3
import os
import threading

class Database:
    def __init__(self, db_path="farmlink.db"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_dir, db_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        self.path = full_path
        self._lock = threading.Lock()

        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        self._init_schema()

    def _init_schema(self):
        # Users
        self.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                password TEXT NOT NULL
            );
        """)

        # Queue Entries
        self.execute("""
            CREATE TABLE IF NOT EXISTS queue_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'waiting',
            created_at TEXT NOT NULL,
            updated_at TEXT,
            delivery_time TEXT
            );

        """)

        # Inventory
        self.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                quantity INTEGER
            );
        """)

        # Notifications
        self.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        """)

        # Reports / History
        self.execute("""
            CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            queue_entry_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        """)

    def execute(self, sql, params=None):
        if params is None:
            params = ()

        with self._lock:
            cur = self.conn.cursor()
            cur.execute(sql, params)
            self.conn.commit()
            return cur

    def query_all(self, sql, params=None):
        return self.execute(sql, params).fetchall()

    def query_one(self, sql, params=None):
        row = self.execute(sql, params).fetchone()
        return dict(row) if row else None
