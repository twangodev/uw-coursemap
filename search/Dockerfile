FROM python:3.12-slim AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONFAULTHANDLER=1
ENV PYTHONUNBUFFERED=1

FROM base AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.8.3 /uv /uvx /bin/

COPY pyproject.toml uv.lock ./

RUN uv sync --locked

FROM base AS runtime

COPY . .
COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
