import sqlite3

class DBSession:

    def __init__(self, database="fruger.db"):
        self.db_path = database

    def connection(self):

        return sqlite3.connect(self.db_path)

    def execute(self, query, params=()):    # Insert, update, delete

        conn = self.connection()

        try:

            cur = conn.cursor()

            cur.execute(query, params)

            conn.commit()   # Commit before returning so callers know the write succeeded

            return cur.lastrowid
        
        finally:

            conn.close()        # Always close the connection, even if an error happens

    def multiple(self, query, params=()):      # Multiple rows reading

        conn = self.connection()

        try:

            cur = conn.cursor()

            cur.execute(query, params)

            results = cur.fetchall()  # Get all matching rows
            
            return results
        
        finally:

            conn.close()

    def one(self, query, params=()):      # For single row

        conn = self.connection()

        try:

            cur = conn.cursor()

            cur.execute(query, params)

            result = cur.fetchone()     # Get just the first matching row

            return result
        
        finally:

            conn.close()
