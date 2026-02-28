# WordRush API Backend

Minimal Django + DRF backend for WordRush game.

## Setup

### Install Dependencies

```bash
uv sync
```

### Run Development Server

Before starting the server be sure to apply migrations (created by Django core apps):

```bash
python manage.py migrate
```

Then start the server:

```bash
python manage.py runserver
```

Server runs on http://localhost:8000/

### API Endpoints

- **GET /** - Root health check, returns `{"status": "ok"}`
- **GET /api/health/** - Health check endpoint, returns `{"status": "ok"}`

## Development

### Run Tests

```bash
pytest
```

### Code Quality

Format code with ruff:
```bash
ruff format .
```

Lint code with ruff:
```bash
ruff check .
```

Check and fix all issues:
```bash
ruff check --fix .
ruff format .
```

### Docker development

An easy local environment is provided with Docker Compose.
Copy `.env.example` to `.env` and adjust secrets as needed.

Start services:

```bash
docker compose -f docker-compose.dev.yml up --build
```

Stop and remove containers/volumes:

```bash
docker compose -f docker-compose.dev.yml down -v
```

The API will be available at http://localhost:8000/ (health at `/api/health/`).

Environment variables available in `.env`:

- `DATABASE_URL` (postgres connection)
- `DJANGO_SECRET_KEY` (secret key)
- `DJANGO_DEBUG` (0 or 1)
- `ALLOWED_ORIGINS` (comma-separated origins for CORS)

## Project Structure

```
lv-wordrush-api/
├── manage.py                 # Django management script
├── config/                   # Django project config
│   ├── settings.py          # Settings with logging, REST_FRAMEWORK config
│   ├── urls.py              # Main URL router
│   └── wsgi.py              # WSGI application
├── game/                     # Main Django app
│   ├── apps.py             # App configuration
│   ├── api/
│   │   ├── views.py        # API views (health check)
│   │   └── urls.py         # API URL routes
│   └── tests/
│       └── test_health.py  # Tests for health endpoint
├── pyproject.toml           # uv, pytest, ruff configuration
└── README.md               # This file
```

## Configuration

- **Python**: 3.12
- **Django**: 4.2.17
- **Django REST Framework**: 3.14.0
- **Testing**: pytest + pytest-django
- **Linting/Formatting**: ruff

### Logging

Logging is configured to output to stdout at INFO level, suitable for Docker/container environments.

To change log level, set environment variable:
```bash
export DJANGO_LOG_LEVEL=DEBUG
python manage.py runserver
```

### Timezone

All times are handled in UTC with timezone awareness enabled.

## Next Steps

- Add models and serializers for game logic
- Add authentication when needed
- Configure database (currently SQLite for development)
- Add Docker support
