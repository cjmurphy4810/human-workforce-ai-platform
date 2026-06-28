# ── Stage 1: Build dashboard ──────────────────────────────────────────────────
FROM node:20-alpine AS dashboard-builder
WORKDIR /app
COPY package.json package-lock.json ./
COPY dashboard/package.json ./dashboard/
RUN npm ci --ignore-scripts
COPY dashboard/ ./dashboard/
RUN npm run build --workspace=dashboard

# ── Stage 2: Python base ──────────────────────────────────────────────────────
FROM python:3.12-slim AS python-base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ── Stage 3: Python dependencies ─────────────────────────────────────────────
FROM python-base AS python-deps
WORKDIR /app
COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ── Stage 4: Production image ─────────────────────────────────────────────────
FROM python-base AS production
WORKDIR /app

# Copy Python packages from deps stage
COPY --from=python-deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=python-deps /usr/local/bin /usr/local/bin

# Copy built dashboard assets
COPY --from=dashboard-builder /app/dashboard/dist ./static

# Copy application source
COPY . .

# Create non-root user and set ownership
RUN useradd --no-create-home --shell /bin/false appuser && \
    mkdir -p /app/data /app/logs && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
