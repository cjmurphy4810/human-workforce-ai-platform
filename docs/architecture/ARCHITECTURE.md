# Architecture — Human Workforce AI Platform

## Overview

The Human Workforce AI Platform is a multi-agent system built on a FastAPI backend, a React/TypeScript dashboard, and a shared SQLite → PostgreSQL data layer. Five specialized AI agents collaborate through a shared database and message bus, each responsible for a discrete stage of the workforce intelligence pipeline.

```
┌─────────────────────────────────────────────────────────────────┐
│                         Dashboard (React/TS)                     │
│              Tailwind · React Query · React Router               │
└──────────────────────────────┬──────────────────────────────────┘
                               │  REST  /api/v1
┌──────────────────────────────▼──────────────────────────────────┐
│                      FastAPI Gateway                             │
│                  Pydantic · python-jose · CORS                   │
└────┬──────────────┬──────────────┬──────────────┬───────────────┘
     │              │              │              │
┌────▼───┐   ┌─────▼──┐   ┌──────▼─┐   ┌───────▼─┐   ┌──────────┐
│ Agent 1│   │Agent 2 │   │Agent 3 │   │ Agent 4 │   │ Agent 5  │
│Research│   │Content │   │ Video  │   │Publish  │   │Analytics │
└────┬───┘   └─────┬──┘   └──────┬─┘   └───────┬─┘   └───┬──────┘
     └──────────────┴──────────────┴─────────────┴─────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                         Shared Library                           │
│               models · utils · constants · config               │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                  Database (SQLAlchemy async)                      │
│              SQLite (dev) → PostgreSQL (production)              │
│                   Alembic-managed migrations                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Layers

### Dashboard (`dashboard/`)

React 18 SPA served by Vite in development and as static files in production. Communicates with the backend exclusively over the `/api/v1` REST namespace. Tailwind CSS handles styling; React Query handles server-state caching and synchronization.

### API Gateway (`app/`)

FastAPI application responsible for routing, request validation, authentication middleware, and response serialization. All business logic delegates to the appropriate agent module — the gateway does not contain domain logic.

### Agent Modules

| Directory | Responsibility |
|---|---|
| `agent1-research/` | Source discovery, web retrieval, structured knowledge ingestion |
| `agent2-content/` | AI-driven content generation and transformation (Anthropic SDK) |
| `agent3-video/` | Media production, rendering pipeline, asset lifecycle |
| `agent4-publishing/` | Multi-channel distribution, scheduling, and delivery |
| `agent5-analytics/` | Performance tracking, metric aggregation, insight extraction |

Each agent is a self-contained module with no direct imports from sibling agents. Inter-agent coordination happens through the shared database or an event/task queue (to be added in a later phase).

### Shared Library (`shared/`)

Common code available to all agents and the gateway:

- `shared/models/` — Pydantic request/response schemas and SQLAlchemy base declarative classes
- `shared/utils/` — Logging helpers, date utilities, pagination primitives
- `shared/constants/` — Platform-wide enumerations and string constants

### Database (`database/`)

SQLAlchemy async engine with Alembic for schema migrations. The `DATABASE_URL` environment variable controls the active driver:

- Development: `sqlite+aiosqlite:///./data/hwai.db`
- Production: `postgresql+asyncpg://...`

Models live in `database/models/`. Migrations are generated and applied via `alembic` (see `make db-migrate` and `make db-upgrade`).

### Config (`config/`)

`pydantic-settings` `Settings` class reads from `.env` at startup. A cached `get_settings()` function is injected via FastAPI dependency injection throughout the application.

---

## Data Flow — Example: Research → Content Pipeline

```
1. Agent 1 (Research)  discovers and ingests a workforce data source → writes to DB
2. Agent 2 (Content)   reads the ingested data → calls Anthropic API → writes artifact to DB
3. Agent 3 (Video)     receives content artifact → renders media asset → writes to DB
4. Agent 4 (Publishing) packages artifact + media → distributes to configured channels
5. Agent 5 (Analytics)  records distribution metrics → surfaces insights via Dashboard
```

---

## Technology Decisions

| Decision | Choice | Rationale |
|---|---|---|
| API framework | FastAPI | Async-native, automatic OpenAPI docs, Pydantic integration |
| ORM | SQLAlchemy 2.x async | Single ORM covers SQLite and PostgreSQL; Alembic migrations included |
| Schema migration | Alembic | Industry standard; autogenerate from models |
| LLM SDK | Anthropic Python SDK | Direct access to Claude models; streaming and tool-use support |
| Frontend build | Vite | Fast HMR; native ESM; straightforward proxy config for dev API |
| Validation | Pydantic v2 | Shared between FastAPI models and settings; strict mode available |
| Linting | Ruff | Single tool for linting + formatting; 10–100× faster than alternatives |
| Type checking | mypy strict | Catches runtime errors at development time |
| Containerization | Docker multi-stage | Separates build deps from runtime; produces a minimal production image |

---

## Future Considerations

- **PostgreSQL migration**: change `DATABASE_URL`; add `asyncpg` + `psycopg2-binary` from `requirements.txt` optional group; run `make db-upgrade`.
- **Task queue**: Celery or ARQ for async agent job dispatch as workloads grow.
- **Authentication**: JWT-based auth is scaffolded via `python-jose` and `passlib`; implement the auth router when user accounts are required.
- **Observability**: Structured JSON logging is configured; add OpenTelemetry instrumentation before scaling to multiple instances.
