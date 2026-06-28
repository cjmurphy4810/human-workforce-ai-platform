# Human Workforce AI Platform

A multi-agent AI platform for human workforce intelligence. Agent 1 (Research) discovers and scores industry news from RSS feeds, stores articles in SQLite, and generates Executive Briefs — exposed as a production REST API.

## Stack

| Layer | Technology |
|---|---|
| API | FastAPI · Python 3.12 · Pydantic v2 |
| Agent 1 | asyncio · feedparser · SQLAlchemy async · SQLite |
| AI / LLM | Anthropic Python SDK (Claude) — future agents |
| Containers | Docker · Docker Compose |
| CI/CD | GitHub Actions |

## Quick Start

```bash
make setup-dev                # python venv + deps + pre-commit hooks
make dev                      # FastAPI API on :8000 (hot-reload)
make research                 # run Agent 1 pipeline once (CLI)
make test                     # run full test suite (73 tests)
```

API docs available at `http://localhost:8000/docs` once the server is running.

## REST API

### Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | System status, DB connectivity, sources count |
| `GET` | `/stats` | Article counts (total, 7d, 30d), last fetch time |
| `GET` | `/brief/latest` | Most recent Executive Brief markdown |
| `POST` | `/run` | Execute the full research pipeline |
| `GET` | `/articles` | Stored articles with filtering and pagination |
| `GET` | `/topics` | Scoring-dimension summaries with top articles |
| `GET` | `/sources` | Configured RSS sources merged with DB stats |

### Article Filters (`GET /articles`)

| Parameter | Type | Description |
|---|---|---|
| `date` | `YYYY-MM-DD` | Filter by published date |
| `source` | string | Partial match on source name |
| `min_score` | float 0–1 | Minimum overall score |
| `topic` | string | Sort by dimension: `business_impact`, `executive_interest`, `consulting_opportunity`, `podcast_potential`, `urgency` |
| `limit` | int 1–200 | Page size (default 50) |
| `offset` | int | Pagination offset |

### Authentication

API key auth is stubded in `api/auth.py` — currently a pass-through. To enable, uncomment the body of `verify_api_key` and set `X-API-Key` header.

## Project Structure

```
├── agent1-research/         # Research pipeline (RSS fetch → score → brief)
│   ├── config/              # Pydantic config loader + config.yaml
│   ├── fetcher/             # Async RSS feed fetcher (feedparser)
│   ├── models/              # Article, ArticleScore, ScoredArticle
│   ├── pipeline/            # Deduplicator, scorer, brief builder, orchestrator
│   └── storage/             # SQLAlchemy ORM, database setup, repository
├── api/                     # FastAPI service layer
│   ├── models/responses.py  # All Pydantic response schemas
│   ├── routers/             # One router per endpoint group
│   ├── auth.py              # API key gate (stubbed)
│   └── dependencies.py      # FastAPI dependency injection
├── output/                  # Generated Executive Briefs (YYYY-MM-DD/)
├── tests/
│   ├── unit/api/            # 39 API unit tests (mocked repo)
│   └── integration/agent1/  # 34 Agent 1 integration tests
└── docs/                    # Architecture and installation documentation
```

## Development Commands

```bash
make help           # list all available targets
make dev            # start API server with hot-reload on :8000
make research       # run Agent 1 research pipeline once
make test           # full test suite with coverage
make test-unit      # unit tests only
make test-integration  # integration tests only
make lint           # ruff linter
make format         # ruff auto-formatter
make type-check     # mypy strict
make docker-up      # start full stack with Docker Compose
```

## Agent 1 Pipeline

The research pipeline runs end-to-end in a single command:

1. Reads RSS feed sources from `agent1-research/config/config.yaml`
2. Fetches and parses articles concurrently with `asyncio`
3. Deduplicates via SHA-256 content fingerprint
4. Scores each article on 5 dimensions (Business Impact, Executive Interest, Consulting Opportunity, Podcast Potential, Urgency)
5. Persists new articles to SQLite
6. Generates `output/YYYY-MM-DD/executive_brief.md` with Top 10 Stories, Top Consulting Opportunities, Top Podcast Ideas, and Source Citations

## License

Proprietary.
