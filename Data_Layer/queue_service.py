import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional
from Data_Layer.database import Database
from Data_Layer.notification_service import NotificationService

class QueueService:
    def __init__(self, db: Database, notify: NotificationService):
        self.db = db
        self.notify = notify

    def _now(self) -> str:
        return datetime.utcnow().isoformat()

    def enqueue(self, user_id: int, item_type: str, quantity: int, delivery_time: Optional[str] = None) -> int:
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        now = self._now()

        # Prevent duplicates in 10 seconds
        recent = self.db.query_all(
            """SELECT * FROM queue_entries
               WHERE user_id=? AND item_type=? AND quantity=? AND created_at > datetime(?, '-10 seconds')""",
            (user_id, item_type, quantity, now)
        )
        if recent:
            raise ValueError("Possible duplicate submission detected")

        self.db.execute(
            """INSERT INTO queue_entries (user_id, item_type, quantity, status, created_at, delivery_time)
               VALUES (?, ?, ?, 'waiting', ?, ?)""",
            (user_id, item_type, quantity, now, delivery_time)
        )

        entry_id = self.db.execute('SELECT last_insert_rowid()').fetchone()[0]
        self.notify.send(user_id, f"Queue entry submitted. ID: {entry_id}")

        return entry_id

    def list_queue_for_user(self, user):
        role = user["role"]
        uid = user["id"]

        if role == "manager":
            return self.db.query_all(
                """SELECT q.*, u.name AS user_name
                   FROM queue_entries q
                   LEFT JOIN users u ON q.user_id = u.id
                   ORDER BY created_at ASC"""
            )

        else:
            return self.db.query_all(
                """SELECT q.*, u.name AS user_name
                   FROM queue_entries q
                   LEFT JOIN users u ON q.user_id = u.id
                   WHERE q.user_id=?
                   ORDER BY created_at ASC""",
                (uid,)
            )

    def approve(self, entry_id: int):
        row = self.db.query_one("SELECT * FROM queue_entries WHERE id=?", (entry_id,))
        if not row:
            raise ValueError("Entry not found")
        self.db.execute("UPDATE queue_entries SET status='processing' WHERE id=?", (entry_id,))
        self.notify.send(row['user_id'], f"Your request #{entry_id} is now being processed.")

    def complete(self, entry_id: int):
        row = self.db.query_one("SELECT * FROM queue_entries WHERE id=?", (entry_id,))
        if not row:
            raise ValueError("Entry not found")
        self.db.execute("UPDATE queue_entries SET status='completed' WHERE id=?", (entry_id,))

        # Log history
        self.db.execute(
            """INSERT INTO reports(queue_entry_id, user_id, action, quantity)
               VALUES (?, ?, ?, ?)""",
            (entry_id, row['user_id'], row['item_type'], row['quantity'])
        )
        self.notify.send(row['user_id'], f"Your request #{entry_id} has been completed.")

    def reorder(self, entry_id: int, new_position: int):
        waiting = self.db.query_all(
            """SELECT * FROM queue_entries WHERE status='waiting' ORDER BY created_at ASC"""
        )
        entries = list(waiting)
        entry = next((e for e in entries if e['id'] == entry_id), None)
        if not entry:
            raise ValueError("Entry not found or not waiting")

        entries.remove(entry)
        entries.insert(new_position - 1, entry)

        base = datetime.utcnow()
        for i, e in enumerate(entries):
            ts = (base - timedelta(seconds=(len(entries) - i))).isoformat()
            self.db.execute("UPDATE queue_entries SET created_at=? WHERE id=?", (ts, e['id']))

        self.notify.send(entry['user_id'], f"Your request #{entry_id} moved to position {new_position}")

    def top_three_notifications(self):
        waiting = self.db.query_all(
            """SELECT * FROM queue_entries WHERE status='waiting' ORDER BY created_at ASC LIMIT 3"""
        )
        for entry in waiting:
            self.notify.send(entry['user_id'], f"Your request #{entry['id']} is among the top 3 in the queue.")
    

    def start_processing(self, entry_id: int) -> None:
        row = self.db.query_one("SELECT * FROM queue_entries WHERE id = ?", (entry_id,))
        if not row:
            raise ValueError("Entry not found")

        # Only allow starting if status is waiting
        if row['status'].lower() != 'waiting':
            raise ValueError("Only waiting entries can be started")

        self.db.execute(
            "UPDATE queue_entries SET status='processing', updated_at=? WHERE id=?",
            (datetime.utcnow().isoformat(), entry_id)
        )

        # Notify the user
        self.notify.send(
            row['user_id'],
            f'Your request #{entry_id} is now being processed.'
        )