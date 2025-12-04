from Data_Layer.database import Database
from Data_Layer.notification_service import NotificationService

class InventoryService:
    def __init__(self, db: Database, notify: NotificationService):
        self.db = db
        self.notify = notify

    def list_inventory(self):
        return self.db.query_all("SELECT * FROM inventory ORDER BY name ASC")

    def add_item(self, name: str, quantity: int):
        existing = self.db.query_one("SELECT * FROM inventory WHERE name=?", (name,))
        if existing:
            new_qty = existing['quantity'] + quantity
            self.db.execute("UPDATE inventory SET quantity=? WHERE id=?", (new_qty, existing['id']))
        else:
            self.db.execute("INSERT INTO inventory (name, quantity) VALUES (?, ?)", (name, quantity))

        if quantity < 5:  # Arbitrary low-stock threshold
            self.notify.send(1, f"Low stock alert: {name} only {quantity} left!")  # manager id assumed 1

    def reduce_stock(self, name: str, quantity: int):
        existing = self.db.query_one("SELECT * FROM inventory WHERE name=?", (name,))
        if not existing:
            raise ValueError(f"{name} not found in inventory")
        new_qty = max(existing['quantity'] - quantity, 0)
        self.db.execute("UPDATE inventory SET quantity=? WHERE id=?", (new_qty, existing['id']))

        if new_qty < 5:
            self.notify.send(1, f"Low stock alert: {name} only {new_qty} left!")
