import sqlite3
from typing import List, Optional
from Data_Layer.database import Database


import hashlib

class UserService:
    def __init__(self, db):
        self.db = db

    def create_user(self, name, role, password):
        if self.get_by_name(name):
            raise ValueError("User already exists")
        # Hash password
        hashed = hashlib.sha256(password.encode()).hexdigest()
        self.db.execute(
            "INSERT INTO users (name, role, password) VALUES (?, ?, ?)",
            (name, role, hashed)
        )

    def get_all(self):
        return self.db.query_all("SELECT * FROM users")

    def get_by_id(self, user_id):
        return self.db.query_one("SELECT * FROM users WHERE id = ?", (user_id,))

    def get_by_name(self, name):
        return self.db.query_one("SELECT * FROM users WHERE name = ?", (name,))

    def verify_user(self, name, password):
        hashed = hashlib.sha256(password.encode()).hexdigest()
        row = self.db.query_one(
            "SELECT * FROM users WHERE name = ? AND password = ?",
            (name, hashed)
        )
        return row


