# Human Workforce AI Platform

A multi-agent AI platform for human workforce intelligence. Five specialized agents (Research, Content, Video, Publishing, Analytics) collaborate through a shared data layer and surface insights through a React dashboard.

## Stack

| Layer | Technology |
|---|---|
| API | FastAPI · Python 3.12 · Pydantic v2 |
| Database | SQLAlchemy async · Alembic · SQLite → PostgreSQL |
| AI / LLM | Anthropic Python SDK (Claude) |
| Dashboard | React 18 · TypeScript · Tailwind CSS · Vite |
| Containers | Docker · Docker Compose |
| CI/CD | GitHub Actions |

## Quick Start

```bash
cp .env.example .env          # add ANTHROPIC_API_KEY and APP_SECRET_KEY
make setup-dev                # python venv + deps + pre-commit hooks
make db-upgrade               # initialize SQLite database
make dev                      # FastAPI on :8000
make dashboard-dev            # Vite dashboard on :5173
```

Full setup and troubleshooting: [docs/installation/INSTALLATION.md](docs/installation/INSTALLATION.md)

## Project Structure

```
├── agent1-research/    # Source discovery and knowledge ingestion
├── agent2-content/     # AI-driven content generation
├── agent3-video/       # Media production and asset management
├── agent4-publishing/  # Multi-channel distribution
├── agent5-analytics/   # Performance tracking and insights
├── dashboard/          # React/TypeScript frontend (Vite)
├── database/           # SQLAlchemy models and Alembic migrations
├── shared/             # Shared models, utils, constants
├── config/             # Pydantic settings and logging config
├── docs/               # Architecture and installation documentation
├── tests/              # Unit, integration, and e2e test suites
└── logs/               # Runtime logs (git-ignored)
```

Architecture overview: [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md)

## Development Commands

```bash
make help           # list all available targets
make test           # run test suite with coverage
make lint           # ruff linter
make format         # ruff auto-formatter
make type-check     # mypy strict
make docker-up      # start full stack with Docker Compose
make db-migrate     # generate a new Alembic migration
```

## License

Proprietary.
