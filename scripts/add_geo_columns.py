"""Add geolocation columns to clicks table.

Run this once after updating the Click model to add the new columns
to an existing database. For fresh databases, create_all handles it.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text
from app.db.database import engine


COLUMNS = [
    ("country_code", "VARCHAR(10)"),
    ("region", "VARCHAR(100)"),
    ("latitude", "DOUBLE PRECISION"),
    ("longitude", "DOUBLE PRECISION"),
    ("timezone", "VARCHAR(100)"),
    ("isp", "VARCHAR(200)"),
]


def migrate():
    with engine.connect() as conn:
        for col_name, col_type in COLUMNS:
            try:
                conn.execute(text(f"ALTER TABLE clicks ADD COLUMN {col_name} {col_type}"))
                print(f"Added column: {col_name}")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    print(f"Column already exists: {col_name}")
                else:
                    print(f"Error adding {col_name}: {e}")
            conn.commit()
    print("Migration complete.")


if __name__ == "__main__":
    migrate()
