"""Simple migration script — runs create_all for now. Use Alembic for production migrations."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.setup_db import setup

if __name__ == "__main__":
    setup()
