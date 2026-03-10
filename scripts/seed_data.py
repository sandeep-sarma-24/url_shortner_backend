"""Seed the database with sample data for development."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models import User, URL, Click
from app.core.security import hash_password
from datetime import datetime, timedelta, timezone
import random

SAMPLE_URLS = [
    ("https://example.com/very/long/url/that/needs/shortening", "xyz123"),
    ("https://github.com/my-awesome-project", "abc987"),
    ("https://dribbble.com/shots/1234567-my-design", "def456"),
    ("https://twitter.com/intent/tweet?text=Hello%20World", "ghi789"),
    ("https://youtube.com/watch?v=dQw4w9WgXcQ", "jkl012"),
]

REFERRERS = [None, "https://twitter.com/", "https://linkedin.com/", "https://facebook.com/", "https://google.com/"]
GEO_DATA = [
    {"country": "United States", "country_code": "US", "lat": 37.7749, "lng": -122.4194, "city": "San Francisco", "region": "California"},
    {"country": "United States", "country_code": "US", "lat": 40.7128, "lng": -74.0060, "city": "New York", "region": "New York"},
    {"country": "United States", "country_code": "US", "lat": 34.0522, "lng": -118.2437, "city": "Los Angeles", "region": "California"},
    {"country": "United Kingdom", "country_code": "GB", "lat": 51.5074, "lng": -0.1278, "city": "London", "region": "England"},
    {"country": "United Kingdom", "country_code": "GB", "lat": 53.4808, "lng": -2.2426, "city": "Manchester", "region": "England"},
    {"country": "Germany", "country_code": "DE", "lat": 52.5200, "lng": 13.4050, "city": "Berlin", "region": "Berlin"},
    {"country": "Germany", "country_code": "DE", "lat": 48.1351, "lng": 11.5820, "city": "Munich", "region": "Bavaria"},
    {"country": "India", "country_code": "IN", "lat": 12.9716, "lng": 77.5946, "city": "Bengaluru", "region": "Karnataka"},
    {"country": "India", "country_code": "IN", "lat": 19.0760, "lng": 72.8777, "city": "Mumbai", "region": "Maharashtra"},
    {"country": "India", "country_code": "IN", "lat": 28.6139, "lng": 77.2090, "city": "New Delhi", "region": "Delhi"},
    {"country": "Canada", "country_code": "CA", "lat": 43.6532, "lng": -79.3832, "city": "Toronto", "region": "Ontario"},
    {"country": "Canada", "country_code": "CA", "lat": 49.2827, "lng": -123.1207, "city": "Vancouver", "region": "British Columbia"},
    {"country": "Australia", "country_code": "AU", "lat": -33.8688, "lng": 151.2093, "city": "Sydney", "region": "New South Wales"},
    {"country": "Australia", "country_code": "AU", "lat": -37.8136, "lng": 144.9631, "city": "Melbourne", "region": "Victoria"},
    {"country": "Japan", "country_code": "JP", "lat": 35.6762, "lng": 139.6503, "city": "Tokyo", "region": "Tokyo"},
    {"country": "Japan", "country_code": "JP", "lat": 34.6937, "lng": 135.5023, "city": "Osaka", "region": "Osaka"},
]
DEVICES = ["Desktop", "Mobile", "Tablet"]
BROWSERS = ["Chrome", "Firefox", "Safari", "Edge"]
OS_LIST = ["Windows", "macOS", "Linux", "iOS", "Android"]


def seed():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == "john@example.com").first()
        if existing:
            print("Seed data already exists. Skipping.")
            return

        user = User(
            name="John Doe",
            email="john@example.com",
            hashed_password=hash_password("password123"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created user: {user.email}")

        now = datetime.now(timezone.utc)
        for original_url, code in SAMPLE_URLS:
            url = URL(
                original_url=original_url,
                short_code=code,
                user_id=user.id,
                is_active=True,
            )
            db.add(url)
            db.commit()
            db.refresh(url)

            num_clicks = random.randint(50, 500)
            for _ in range(num_clicks):
                click_time = now - timedelta(days=random.randint(0, 90), hours=random.randint(0, 23))
                geo = random.choice(GEO_DATA)
                click = Click(
                    url_id=url.id,
                    clicked_at=click_time,
                    ip_address=f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
                    referrer=random.choice(REFERRERS),
                    country=geo["country"],
                    country_code=geo["country_code"],
                    latitude=geo["lat"] + random.uniform(-0.5, 0.5),
                    longitude=geo["lng"] + random.uniform(-0.5, 0.5),
                    city=geo["city"],
                    region=geo["region"],
                    device_type=random.choice(DEVICES),
                    browser=random.choice(BROWSERS),
                    os=random.choice(OS_LIST),
                )
                db.add(click)
            db.commit()
            print(f"Created URL: {code} with {num_clicks} clicks")

        print("Seeding complete!")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
