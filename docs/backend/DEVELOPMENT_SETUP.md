# MyFarm AI Backend — Development Setup

## Prerequisites

- Docker and Docker Compose
- Python 3.12+ (for local development)
- Ollama installed and running (for LLM inference)
- Git

## Quick Start with Docker

```bash
# Clone and enter project
cd MyFarmAI

# Start all services (backend + voice)
docker compose up -d

# Verify backend health
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/health

# Verify voice service
curl http://localhost:8001/health

# Initialize database
docker compose exec backend python -m app.db.init_db
```

## Local Development (without Docker)

### 1. Install Ollama

```bash
# Linux/macOS
curl -fsSL https://ollama.com/install.sh | sh

# Pull required model
ollama pull qwen3:4b
```

### 2. Set up Python environment

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp ../.env.example .env
# Edit .env as needed (see Configuration section)
```

### 4. Initialize database

```bash
python -m app.db.init_db
```

### 5. Run backend

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Run tests

```bash
pytest -v
```

## Configuration

All settings are loaded from `.env` file (see `.env.example` for template).

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | "My Farm AI Backend" | Application name |
| `APP_VERSION` | "0.2.0" | Application version |
| `ENVIRONMENT` | "development" | Environment name |
| `OLLAMA_BASE_URL` | "http://localhost:11434" | Ollama API base URL |
| `OLLAMA_MODEL` | "qwen3:4b" | Model name for chat |
| `OLLAMA_TIMEOUT_SECONDS` | 120 | Request timeout |
| `DATABASE_PATH` | "data/app.db" | SQLite database path |
| `CORS_ALLOWED_ORIGINS` | "http://localhost:3000,http://localhost:8081" | CORS origins |
| `LOG_LEVEL` | "INFO" | Log level |
| `VOICE_SERVICE_URL` | "http://voice:8001" | Voice service URL |
| `WEATHER_BASE_URL` | "https://api.open-meteo.com/v1/forecast" | Open-Meteo API base URL |
| `WEATHER_TIMEOUT_SECONDS` | 10 | Weather API request timeout |
| `WEATHER_CACHE_TTL_SECONDS` | 300 | Weather response cache TTL |
| `RESOURCES_CACHE_TTL_SECONDS` | 3600 | Agricultural resources cache TTL |
| `RATE_LIMIT_REQUESTS` | 60 | Maximum requests per window per client |
| `RATE_LIMIT_WINDOW_SECONDS` | 60 | Rate limit window in seconds |

### Docker Networking for Ollama

| Environment | OLLAMA_BASE_URL |
|-------------|-----------------|
| Host machine | `http://localhost:11434` |
| Docker (Docker Desktop) | `http://host.docker.internal:11434` |
| Docker (Linux, host network) | `http://localhost:11434` |
| Docker (Linux, bridge network) | `http://172.17.0.1:11434` |

The project uses `network_mode: host` for the backend container, so `http://localhost:11434` works on Linux.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Project info |
| GET | `/health` | Health check |
| GET | `/api/v1/health` | Health check (versioned) |
| POST | `/api/v1/chat` | Chat with AI assistant |
| GET | `/api/v1/weather` | Current weather + 7-day forecast |
| GET | `/api/v1/weather/current` | Current weather only |
| GET | `/api/v1/resources` | Agricultural resources catalogue |
| GET | `/api/v1/resources/categories` | List resource categories |
| GET | `/api/v1/resources/{category}` | Resources by category |

See [API.md](API.md) for detailed request/response schemas.

## Database

- **Type**: SQLite (file-based)
- **Location**: `data/app.db` (configurable via `DATABASE_PATH`)
- **Tables**: `conversations`, `messages`
- **Initialization**: `python -m app.db.init_db` or `docker compose exec backend python -m app.db.init_db`

## Voice Service

The voice service runs separately on port 8001:
- `GET /health` — Health check
- `POST /transcribe` — Speech-to-text (Hindi)

## Weather Service

The weather service uses Open-Meteo API (free, no API key required):
- Current weather + 7-day forecast
- WMO weather codes with human-readable descriptions
- Configurable via `WEATHER_BASE_URL`, `WEATHER_TIMEOUT_SECONDS`, `WEATHER_CACHE_TTL_SECONDS`

## Agricultural Resources

Curated catalogue of 12 verified Indian agricultural resources:
- Categories: schemes, advisory, market, weather, research, financial, digital
- Sources: ICAR, Ministry of Agriculture, IMD, NABARD, NPCI
- Configurable via `RESOURCES_CACHE_TTL_SECONDS`

## Code Quality

```bash
# Lint and format
ruff check app/ tests/
ruff format app/ tests/

# Type check
mypy app/ --config-file mypy.ini

# Run tests
pytest -v

# Pre-commit hooks
pre-commit install
pre-commit run --all-files
```

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app factory
│   ├── core/
│   │   └── config.py        # Pydantic Settings
│   ├── api/
│   │   └── v1/
│   │       ├── router.py    # API v1 router
│   │       ├── health.py    # Health endpoints
│   │       ├── chat.py      # Chat endpoint
│   │       ├── weather.py   # Weather endpoints
│   │       └── resources.py # Resources endpoints
│   ├── services/
│   │   ├── ollama.py        # Ollama HTTP client
│   │   ├── chat.py          # Chat orchestration
│   │   ├── weather.py       # Open-Meteo weather client
│   │   └── resources.py     # Agricultural resources catalogue
│   ├── db/
│   │   ├── __init__.py      # DB exports
│   │   ├── connection.py    # SQLite connection
│   │   ├── conversations.py # Conversation CRUD
│   │   └── init_db.py       # DB initialization script
│   └── schemas/
│       ├── chat.py          # Chat Pydantic models
│       ├── weather.py       # Weather Pydantic models
│       └── resources.py     # Resources Pydantic models
├── tests/
│   ├── conftest.py          # Pytest fixtures
│   ├── test_health.py       # Health endpoint tests
│   ├── test_database.py     # Database tests
│   ├── test_chat.py         # Chat endpoint tests
│   ├── test_schemas.py      # Schema validation tests
│   ├── test_weather.py      # Weather endpoint tests
│   └── test_resources.py    # Resources endpoint tests
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container image
├── ruff.toml                # Ruff config
├── mypy.ini                 # MyPy config
└── pytest.ini               # Pytest config
```

## Adding New Dependencies

1. Add to `requirements.txt`
2. Rebuild Docker image: `docker compose build backend`
3. Update `.venv`: `pip install -r requirements.txt`

## Troubleshooting

### Ollama Connection Failed
- Verify Ollama is running: `ollama ps`
- Check `OLLAMA_BASE_URL` in `.env`
- For Docker: ensure `network_mode: host` or correct bridge IP

### Database Errors
- Ensure `data/` directory exists and is writable
- Run `python -m app.db.init_db` to reinitialize
- Check file permissions on `data/app.db`

### Model Timeout
- Increase `OLLAMA_TIMEOUT_SECONDS` for slower hardware
- Use smaller model (e.g., `qwen3:0.6b`) for development

### Weather API Issues
- Verify internet connectivity for Open-Meteo
- Check `WEATHER_BASE_URL` and `WEATHER_TIMEOUT_SECONDS`
- Open-Meteo is free with no API key required

### Tests Hanging
- Chat/Weather tests require mocked clients (see `tests/conftest.py`)
- Database/schema/health/Resources tests run without external services