from Data_Layer.database import Database   

class ReportService:
    def __init__(self, db: Database):
        self.db = db

    def summary(self) -> dict:
        total_orders = self.db.query_all('SELECT COUNT(*) as c FROM queue_entries')[0]['c']
        waiting = self.db.query_all("SELECT COUNT(*) as c FROM queue_entries WHERE status='waiting'")[0]['c']
        approved = self.db.query_all("SELECT COUNT(*) as c FROM queue_entries WHERE status='approved'")[0]['c']
        completed = self.db.query_all("SELECT COUNT(*) as c FROM queue_entries WHERE status='completed'")[0]['c']
        # average wait: compute average seconds between created_at and now for completed? simple version: N/A
        return {
            'total_orders': total_orders,
            'waiting': waiting,
            'approved': approved,
            'completed': completed
        }
