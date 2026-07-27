FROM python:3.12-slim AS base

COPY --from=ghcr.io/astral-sh/uv:0.9.5 /uv /uvx /bin/

WORKDIR /app

ENV PATH="/app/.venv/bin:${PATH}" \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src/ src/
COPY configs/ configs/
COPY main.py .

RUN useradd -m -u 1000 app \
    && mkdir -p /home/app/.kaggle /app/data /app/notebooks /app/reports \
    && chown -R app:app /app /home/app/.kaggle
COPY --chown=app:app kaggle.json.example /home/app/.kaggle/kaggle.json.example

USER app

ENV AGENT_MODE=baseline
ENV LOG_LEVEL=INFO

FROM base AS agent

CMD ["python", "main.py"]

FROM base AS dev

USER root
COPY .pre-commit-config.yaml .
RUN uv sync --frozen --group dev
COPY tests/ tests/
USER app

CMD ["bash"]

FROM base AS marimo

USER root
RUN uv sync --frozen --no-dev --group notebooks
USER app

EXPOSE 2718
CMD ["marimo", "run", "notebooks/", "--host", "0.0.0.0", "--port", "2718"]
