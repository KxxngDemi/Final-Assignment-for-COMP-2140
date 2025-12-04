from Data_Layer.database import Database

class NotificationService:
    def __init__(self, db: Database):
        self.db = db

    def send(self, user_id: int, message: str):
        # Save in DB
        self.db.execute(
            "INSERT INTO notifications (user_id, message, created_at) VALUES (?, ?, datetime('now'))",
            (user_id, message)
        )

    def list_for_user(self, user_id: int):
        return self.db.query_all(
            "SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC",
            (user_id,)
        )
