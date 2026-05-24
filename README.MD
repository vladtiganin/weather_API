# Weather API

Weather API is a small FastAPI application for fetching current weather by city name, storing every query in PostgreSQL, and viewing or exporting query history.

The project was built as a Python test task. It uses OpenWeatherMap Current Weather API, SQLAlchemy ORM, Alembic migrations, Docker Compose, structured JSON logging, simple caching, and basic in-memory rate limiting.

## Features

- Fetch current weather by city name.
- Support Celsius and Fahrenheit via the `unit` query parameter.
- Store every weather query in PostgreSQL.
- Store city name, query timestamp, weather details, unit, and cache flag.
- Reuse recently fetched weather for the same city and unit within 5 minutes.
- Still create a new history row when cached data is reused.
- View query history with pagination.
- Filter query history by city substring and date range.
- Export filtered query history as CSV.
- Basic per-IP rate limiting for the weather fetch endpoint.
- Health check endpoint for database connectivity and optional provider reachability.
- Structured JSON logs for request lifecycle, errors, and external provider latency.
- Docker Compose setup for the app and PostgreSQL.

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Pydantic Settings
- HTTPX
- Pytest
- Docker Compose
- OpenWeatherMap Current Weather API

## Environment Variables

Configuration is loaded from environment variables. In local and Docker Compose usage, the app reads values from `app/.env`.

| Variable | Description | Example |
| --- | --- | --- |
| `WEATHER_API_KEY` | OpenWeatherMap API key | `your_openweather_api_key_here` |
| `DB_DNS` | Async SQLAlchemy database URL used by the app | `postgresql+psycopg://postgres:postgres@db:5432/db` |
| `LOCAL_MIGRATION_DB_DNS` | Database URL used by Alembic migrations | `postgresql+psycopg://postgres:postgres@localhost:2222/db` |
| `RATE_LIMIT_REQUESTS` | Max requests allowed per IP per window | `30` |
| `RATE_LIMIT_WINDOW_SECONDS` | Rate limit window in seconds | `60` |

## `.env.sample`

The repository includes `.env.sample` with all required variable names. Copy it to `app/.env` before running the application:

```bash
cp .env.sample app/.env
```

Then set your real OpenWeatherMap API key:

```env
WEATHER_API_KEY=your_real_openweather_api_key
```

For Docker Compose, `DB_DNS` points to the `db` service. `LOCAL_MIGRATION_DB_DNS` is overridden in `docker-compose.yml` so migrations also run against the compose database. For local development outside Docker, adjust the database URLs if your PostgreSQL host or port is different.

## Docker Compose Quickstart

1. Copy the sample environment file:

```bash
cp .env.sample app/.env
```

2. Add your OpenWeatherMap API key to `app/.env`.

3. Build and start the app and PostgreSQL:

```bash
docker compose up --build
```

The app container runs Alembic migrations automatically before starting Uvicorn.

4. Open Swagger UI:

```text
http://localhost:8000/docs
```

## Local Development

You can run the API locally while using PostgreSQL from Docker Compose.

1. Create and activate a virtual environment:

```bash
python -m venv venv
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start PostgreSQL:

```bash
docker compose up db
```

4. Copy and edit environment variables:

```bash
cp .env.sample app/.env
```

For local host execution, set both database URLs to the published PostgreSQL port:

```env
DB_DNS=postgresql+psycopg://postgres:postgres@localhost:2222/db
LOCAL_MIGRATION_DB_DNS=postgresql+psycopg://postgres:postgres@localhost:2222/db
```

5. Run migrations:

```bash
alembic upgrade head
```

6. Start the app:

```bash
uvicorn app.main:app --reload
```

Swagger UI will be available at:

```text
http://localhost:8000/docs
```

## API Endpoints

### Fetch Weather

```http
GET /weather?city=Minsk&unit=celsius
```

Supported units:

- `celsius`
- `fahrenheit`

Example response:

```json
{
  "city_name": "Minsk",
  "timestamp": "2026-05-24T12:00:00Z",
  "served_from_cache": false,
  "data": {
    "temp": 20.5,
    "description": "clear sky",
    "units": "celsius"
  }
}
```

### Query History

```http
GET /weather/history?page=1&limit=10
```

With filters:

```http
GET /weather/history?city=min&date_from=2026-05-01&date_to=2026-05-24
```

### CSV Export

```http
GET /weather/history/export
```

The export supports the same filters:

```http
GET /weather/history/export?city=min&date_from=2026-05-01&date_to=2026-05-24
```

### Health Check

```http
GET /health
```

With optional external provider check:

```http
GET /health?include_provider=true
```

## Caching Behavior

The application implements a simple database-backed cache:

- If the same city and same unit are requested again within 5 minutes, the previous fresh weather record is reused.
- No external OpenWeatherMap API call is made on cache hit.
- A new query row is still created in PostgreSQL.
- The new row is marked with `served_from_cache = true`.
- The `/weather` response includes `served_from_cache`.
- CSV export includes the `served_from_cache` field.

This cache is intentionally simple and uses existing database records rather than Redis.

## Rate Limiting

The weather fetch endpoint is protected by a basic per-client-IP rate limit:

- Default limit: `30` requests per `60` seconds.
- Configured by `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW_SECONDS`.
- If the limit is exceeded, the API returns HTTP `429`.
- The response contains a friendly error message.
- The implementation is in memory for simplicity.

Redis could be used for both caching and rate limiting in a production or multi-instance setup. It was intentionally not added here because this is a small test task and Redis would make the solution unnecessarily heavy.

## Migrations

Alembic is used for database migrations.

Run migrations manually:

```bash
alembic upgrade head
```

Create a new migration after model changes:

```bash
alembic revision --autogenerate -m "describe change"
```

In Docker Compose, migrations are run automatically by the `weather_api` service before Uvicorn starts.

## Testing

Run tests:

```bash
pytest
```

Or, on Windows with the local virtual environment:

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

The test suite includes targeted coverage for:

- Cache reuse vs. fresh weather fetch.
- Rate limit returning HTTP `429` and preventing the service/DB write path.
- Filtering and pagination query logic.

## Notes and Limitations

- Authentication is not implemented because the test task does not require users.
- Rate limiting is in-memory and resets on application restart.
- In-memory rate limiting is not shared across multiple app instances.
- For more precise city search, pass city and country code, for example `Minsk,BY`.
- The cache is stored in PostgreSQL records and is intentionally simple for the scope of the task.
