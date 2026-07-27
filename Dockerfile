FROM python:3.12-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY kaggle.json.example /root/.kaggle/kaggle.json.example
COPY src/ src/
COPY configs/ configs/
COPY main.py .

RUN useradd -m -u 1000 app && chown -R app:app /app /root/.kaggle
USER app

ENV AGENT_MODE=baseline
ENV LOG_LEVEL=INFO

ENTRYPOINT ["uv", "run", "main.py"]

FROM base AS agent

FROM base AS dev

USER root
COPY .pre-commit-config.yaml .
RUN uv sync --frozen
COPY tests/ tests/
USER app

FROM base AS marimo

USER root
RUN uv sync --frozen --group notebooks
USER app

EXPOSE 2718
ENTRYPOINT ["uv", "run", "marimo", "run", "notebooks/", "--host", "0.0.0.0", "--port", "2718"]