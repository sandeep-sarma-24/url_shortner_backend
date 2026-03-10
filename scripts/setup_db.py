"""Create all database tables."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import Base, engine
from app.models import User, URL, Click  # noqa: F401 — registers models


def setup():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Done! Tables created successfully.")


if __name__ == "__main__":
    setup()
