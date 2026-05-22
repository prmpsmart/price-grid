# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.13-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first (layer cache — only re-runs if these change)
COPY pyproject.toml uv.lock ./

# Install dependencies into a virtual environment inside the image
# --frozen: respect lockfile exactly, no updates
# --no-install-project: skip installing the app itself (just deps for now)
RUN uv sync --frozen --no-install-project

# Copy application source
COPY . .

# Install the project itself
RUN uv sync --frozen


# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.13-slim AS runtime

WORKDIR /app

# Copy the virtual environment and app from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app /app

# Make sure the venv is on PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]