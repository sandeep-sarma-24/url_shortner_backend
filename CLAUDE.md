# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture

This is a FastAPI-based URL shortener backend with the following key architectural components:

### Core Structure
- **FastAPI Application**: Main application entry point at `app/main.py` with ASGI configuration in `app/asgi.py`
- **API Versioning**: Organized under `app/api/v1/` with route separation by domain (urls, analytics, health)
- **Database Layer**: SQLAlchemy models in `app/models/` with database session management in `app/db/`
- **Service Layer**: Business logic separated into `app/services/` (url_service, analytics_service, cache_service)
- **Schema Layer**: Pydantic schemas in `app/schemas/` for request/response validation

### Key Components
- **Models**: URL, Click, Analytics models with base model inheritance
- **Services**: URL shortening, analytics tracking, caching layer
- **Middleware**: Authentication, CORS, rate limiting in `app/api/middleware/`
- **Security**: JWT authentication and security utilities in `app/core/security.py`
- **Configuration**: Environment-based config management in `app/configs/config.py`

### Infrastructure
- **Containerization**: Docker configuration with deployment scripts
- **CI/CD**: Jenkins pipelines for development, QA, and production environments
- **Monitoring**: Prometheus metrics and health checks in `monitoring/`
- **Database Scripts**: Migration, seeding, and backup utilities in `scripts/`

## Development Commands

### Testing
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run with coverage
pytest --cov=app
```

### Dependencies
```bash
# Install dependencies
pip install -r requirements.txt

# Development setup
python setup.py develop
```

### Database Operations
```bash
# Setup database
python scripts/setup_db.py

# Run migrations
python scripts/migrate.py

# Seed test data
python scripts/seed_data.py

# Backup database
python scripts/backup_db.py
```

### Docker Operations
```bash
# Build image
docker build -t url-shortener-backend .

# Run container
docker run -p 8000:8000 url-shortener-backend
```

## Project Structure Notes

- API routes are organized by domain in `app/api/v1/routes/`
- Database models follow SQLAlchemy declarative base pattern
- All schemas use Pydantic for validation
- Services layer provides business logic abstraction
- Middleware handles cross-cutting concerns (auth, CORS, rate limiting)
- Configuration supports multiple deployment environments
- Comprehensive test structure with fixtures and separate test categories
- Monitoring and observability built-in with Prometheus and custom health checks