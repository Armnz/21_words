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
- **POST /api/v1/sessions/** - Start a new 21-words session
- **GET /api/v1/sessions/{id}/** - Get session state and current prompt
- **POST /api/v1/sessions/{id}/attempt/** - Validate one word attempt and update score
- **POST /api/v1/sessions/{id}/publish/** - Publish a submitted score to leaderboard
- **GET /api/v1/leaderboard/?limit=100** - Read leaderboard
- **GET /api/schema/** - OpenAPI schema JSON
- **GET /api/docs/** - Swagger UI

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

Postgres is bound to the host on port **5432**, so you can point a client such as DBeaver to:

```
Host:     localhost          # or 127.0.0.1
Port:     5432
Database: wordrush
User:     user
Password: pass
```

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
│   ├── settings.py          # Settings with logging, REST_FRAMEWORK, admin
│   ├── urls.py              # Main URL router + admin
│   └── wsgi.py              # WSGI application
├── game/                     # Main Django app
│   ├── models.py            # Game models (Word, Prompt, Session, LeaderboardEntry)
│   ├── admin.py             # Django admin config
│   ├── apps.py              # App configuration
│   ├── api/
│   │   ├── views.py        # API views (health check)
│   │   └── urls.py         # API URL routes
│   ├── services/
│   │   └── validation.py   # Word normalization helper
│   ├── migrations/          # Database migrations
│   └── tests/
│       └── test_health.py  # Tests for health endpoint
├── pyproject.toml           # uv, pytest, ruff configuration
└── README.md               # This file
```

## Game Schema

### Models

The game uses a simplified schema optimized for the 21-word challenge:

- **Word** – canonical word entries (normalized form only).
- **Prompt** – game prompts with rule snapshots (e.g., "starts with A").
- **Session** – game session state with frozen prompt and answer snapshots (JSONB) to preserve game state at play-time.
- **LeaderboardEntry** – tied to submitted sessions, ranked by score (desc) then created_at (asc).

### Migrations

Apply migrations locally after pulling:

```bash
python manage.py migrate
```

In Docker, migrations are applied automatically during `docker compose up`.

Verify tables exist (local):
```bash
python manage.py dbshell
# then: \dt (PostgreSQL) or .tables (SQLite)
```

Or check via Django admin at http://localhost:8000/admin/ after creating a superuser:
```bash
python manage.py createsuperuser
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

## Docker Development Workflow

1. **Copy environment file:**

   ```bash
   cp .env.example .env
   ```

2. **Start services:**

   ```bash
   docker compose -f docker-compose.dev.yml up --build
   ```

   The compose file will:
   - Build the API image using the Dockerfile
   - Start a Postgres 16 database
   - Run `python manage.py migrate` inside the API container
   - Start Django on `http://localhost:8000`

3. **Access the application:**

   - API health: http://localhost:8000/api/health/
   - Django admin: http://localhost:8000/admin/

4. **Stop services:**

   ```bash
   docker compose -f docker-compose.dev.yml down -v
   ```

   The `-v` flag removes the database volume; omit it to persist data.

## Next Steps

- Add Tezaurs import pipeline for production-sized dictionary
- Tune prompt set and balance by `valid_words_count`
- Add frontend integration and contract type generation
- Add authentication/session management if needed

## OpenAPI schema generation

Generate schema file:

```bash
python manage.py spectacular --file openapi/schema.json
```

With Docker:

```bash
docker compose -f docker-compose.dev.yml exec api python manage.py spectacular --file openapi/schema.json
```
