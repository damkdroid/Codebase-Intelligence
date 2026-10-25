
import sqlite3
from typing import Any, Dict, List, Optional
from sample_project.config import load_settings, setup_logger

logger = setup_logger("database")


class DatabaseClient:

    def __init__(self, db_path: Optional[str] = None):
        settings = load_settings()
        self.db_path = db_path or settings["database_url"].replace("sqlite:///", "")
        self._init_tables()

    def _init_tables(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    email TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user'
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    total_amount REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def execute_query(self, query: str, params: tuple = ()) -> List[tuple]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def insert_user_record(self, username: str, password_hash: str, email: str, role: str = "user") -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, password_hash, email, role) VALUES (?, ?, ?, ?)",
                (username, password_hash, email, role),
            )
            conn.commit()
            return cursor.lastrowid or 0

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        rows = self.execute_query(
            "SELECT id, username, password_hash, email, role FROM users WHERE username = ?",
            (username,),
        )
        if not rows:
            return None
        r = rows[0]
        return {"id": r[0], "username": r[1], "password_hash": r[2], "email": r[3], "role": r[4]}
