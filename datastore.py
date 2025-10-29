import sqlite3
import json
from typing import Optional, Dict, Any


class DataStore:
    def __init__(self, db_path: str = "data_store.db"):
        """Initialize connection and create tables if needed."""
        self.db_path = db_path
        self._create_tables()
    def connect(self):
        return sqlite3.connect(self.db_path)

    def _get_conn(self):
        """Create a connection (safe for concurrent access)."""
        return sqlite3.connect(self.db_path, timeout=10)

    def _create_tables(self):
        """Ensure required tables exist."""
        conn = self._get_conn()
        cur = conn.cursor()

        # Observations table
        cur.execute('''
        CREATE TABLE IF NOT EXISTS observations (
            name TEXT PRIMARY KEY,
            duration INTEGER,
            status TEXT,
            transit_time TEXT,
            count_down REAL
        )
        ''')

        # System status table
        cur.execute('''
        CREATE TABLE IF NOT EXISTS system_status (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        ''')

        conn.commit()
        conn.close()

    # ------------------------------
    # Observation Operations
    # ------------------------------
    def add_or_update_observation(self, name: str, duration: int, status: str,
                                  transit_time: str, count_down: float):
        """Insert or update an observation."""
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute('''
        INSERT OR REPLACE INTO observations (name, duration, status, transit_time, count_down)
        VALUES (?, ?, ?, ?, ?)
        ''', (name, duration, status, transit_time, count_down))
        conn.commit()
        conn.close()

    def update_observation(self, name: str, **fields):
        """Update specific fields for an observation."""
        if not fields:
            return
        keys = ", ".join([f"{k}=?" for k in fields])
        values = list(fields.values()) + [name]
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(f'UPDATE observations SET {keys} WHERE name=?', values)
        conn.commit()
        conn.close()

    def get_observation(self, name: str) -> Optional[Dict[str, Any]]:
        """Get one observation by name."""
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute('SELECT * FROM observations WHERE name=?', (name,))
        row = cur.fetchone()
        conn.close()

        if row:
            return {
                "name": row[0],
                "duration": row[1],
                "status": row[2],
                "transit_time": row[3],
                "count_down": row[4],
            }
        return None

    def get_all_observations(self, order_by_countdown=False):
        """Return all observations as a list of dicts, optionally sorted by countdown."""
        conn = self._get_conn()
        cur = conn.cursor()
        if order_by_countdown:
            cur.execute('SELECT * FROM observations ORDER BY count_down ASC')
        else:
            cur.execute('SELECT * FROM observations')
        rows = cur.fetchall()
        conn.close()
        return [
            {"name": r[0], "duration": r[1], "status": r[2],
             "transit_time": r[3], "count_down": r[4]}
            for r in rows
        ]
    def delete_observation(self, name: str):
        """Delete a pulsar observation from the database by name."""
        conn = self._get_conn()  # get a valid connection
        with conn:  # use the same connection here
            conn.execute(
                "DELETE FROM observations WHERE name = ?",
                (name,)
            )
        conn.close()  # close it after done
        print(f"✅ Observation '{name}' deleted from DB.")
        
    # ------------------------------
    # System Status Operations
    # ------------------------------
    def set_system_status(self, key: str, value: str):
        """Store a system status entry directly as TEXT."""
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute('''
        INSERT OR REPLACE INTO system_status (key, value)
        VALUES (?, ?)
        ''', (key, value))
        conn.commit()
        conn.close()

    def get_system_status(self, key):
        """Retrieve stored value; split commas if it's a file list."""
        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT value FROM system_status WHERE key=?", (key,))
            result = cur.fetchone()

        if not result:
            return None

        val = result[0]
        # If it's a list-like comma string, return list
        if "," in val:
            return val.split(",")
        return val
        
        
    def update_system_status(self, key, value):
        """Store lists as comma-separated strings; plain strings stay as-is."""
        if isinstance(value, list):
            value = ",".join(value)
        elif isinstance(value, dict) and "current_file" in value:
            # Special case for Log_Current dicts
            value = ",".join(value["current_file"])

        with self.connect() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO system_status (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """, (key, value))
            conn.commit()
