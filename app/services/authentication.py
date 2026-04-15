import sqlite3
import hashlib
from app.services.database import DBSession

class AuthService:

    def __init__(self, database="fruger.db"):
        self.db = DBSession(database)
        self.table()

    def table(self):

        try:

            self.db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id       INTEGER PRIMARY KEY AUTOINCREMENT,
                    email    TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL
                )
            """)  # Create user table on startup

        except Exception as e:

            print(f"Error creating users table: {e}")

    def _hash(self, password):

        return hashlib.sha256(password.encode()).hexdigest()

    def register(self, email, password):

        try:

            if not email or not password:

                return {"error": "Email and password are required"}

            email = email.strip().lower()       # Lowercase so there aren't any dupe accounts created

            self.db.execute(
                "INSERT INTO users (email, password) VALUES (?, ?)",
                (email, self._hash(password))
            )

            return {"message": "User registered"}
        
        except sqlite3.IntegrityError:

            return {"error": "User already exists"}
        
        except Exception as e:

            return {"error": str(e)}

    def login(self, email, password):

        try:

            email = email.strip().lower()

            user = self.db.one(
                "SELECT id FROM users WHERE email=? AND password=?",
                (email, self._hash(password))
            )                                                               # Compare passwords by their hash

            if user:

                return {"message": "Login successful", "user_id": user[0]}
            
            return {"error": "Invalid credentials"}
        
        except Exception as e:
            
            return {"error": str(e)}
