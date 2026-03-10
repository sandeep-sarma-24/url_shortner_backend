#!/bin/sh
set -e

echo "Running database setup..."
python -m scripts.setup_db

echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
