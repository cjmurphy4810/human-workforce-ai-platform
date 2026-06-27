# Installation Guide — Human Workforce AI Platform

## Prerequisites

| Tool | Minimum Version | Install |
|---|---|---|
| Python | 3.12 | `brew install python@3.12` |
| Node.js | 20 LTS | `brew install node` |
| Docker Desktop | 4.x | [docs.docker.com](https://docs.docker.com/desktop/mac/install/) |
| Git | 2.x | `brew install git` |
| VS Code | 1.89+ | [code.visualstudio.com](https://code.visualstudio.com/) |

> macOS Apple Silicon: all dependencies above ship universal/ARM-native builds.

---

## 1. Clone the Repository

```bash
git clone https://github.com/<org>/human-workforce-ai-platform.git
cd human-workforce-ai-platform
```

---

## 2. Environment Variables

```bash
cp .env.example .env
```

Open `.env` and set at minimum:

```
APP_SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
ANTHROPIC_API_KEY=<your key from console.anthropic.com>
```

All other defaults work for local development.

---

## 3. Python Environment

```bash
make setup-dev
```

This creates a `.venv/` virtualenv using Python 3.12, installs all production and dev dependencies, and installs pre-commit hooks.

Activate the virtualenv in any new shell:

```bash
source .venv/bin/activate
```

---

## 4. Database Initialization

```bash
make db-upgrade
```

Applies all Alembic migrations against the SQLite database at `data/hwai.db` (created automatically).

---

## 5. Dashboard

```bash
make dashboard-install   # installs node_modules
make dashboard-dev       # starts Vite dev server on http://localhost:5173
```

The Vite dev server proxies `/api` requests to `http://localhost:8000`, so both servers must run concurrently during development.

---

## 6. API Server

In a separate terminal (with the virtualenv active):

```bash
make dev
```

API is available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

---

## 7. Running Tests

```bash
make test             # full suite with coverage
make test-unit        # unit tests only
make test-integration # integration tests only
```

---

## 8. Code Quality

```bash
make lint        # ruff linter
make format      # ruff formatter (auto-fixes)
make type-check  # mypy strict
make check       # lint + type-check together
```

Pre-commit hooks run `ruff check` and `ruff format` automatically on each commit.

---

## Docker Setup (Production-equivalent)

### SQLite mode (single container)

```bash
make docker-build
# Edit docker-compose.yml to remove the `db` service dependency,
# or run the API container standalone:
docker run --rm -p 8000:8000 --env-file .env human-workforce-ai-platform:latest
```

### PostgreSQL mode (full stack)

1. Add Postgres credentials to `.env`:
   ```
   POSTGRES_PASSWORD=<secure password>
   DATABASE_URL=postgresql+asyncpg://hwai:<password>@db:5432/hwai
   ```
2. Uncomment `asyncpg` and `psycopg2-binary` in `requirements.txt`.
3. Rebuild and start:
   ```bash
   make docker-build
   make docker-up
   ```
4. Run migrations inside the container:
   ```bash
   docker compose exec api alembic upgrade head
   ```

---

## VS Code Setup

1. Open the repository root in VS Code.
2. Accept the prompt to install recommended extensions (`.vscode/extensions.json`).
3. VS Code will automatically use the `.venv` Python interpreter.
4. Use **Run and Debug** (`⌘⇧D`) to launch `FastAPI — Dev Server` or `Pytest — All Tests`.

---

## Troubleshooting

**`make setup-dev` fails with "python3.12 not found"**
```bash
brew install python@3.12
# Then ensure it's on your PATH:
echo 'export PATH="/opt/homebrew/opt/python@3.12/bin:$PATH"' >> ~/.zprofile
source ~/.zprofile
```

**Vite dashboard can't reach API**
Ensure the FastAPI server is running on port 8000. The Vite proxy (`vite.config.ts`) forwards `/api` requests to `http://localhost:8000`.

**`alembic upgrade head` fails on a fresh database**
The `data/` directory is created by Docker or you may need to create it manually:
```bash
mkdir -p data
make db-upgrade
```

**Docker build fails on Apple Silicon**
Add `--platform linux/arm64` to `make docker-build` or set `DOCKER_DEFAULT_PLATFORM=linux/arm64` in your shell profile.
