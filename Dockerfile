FROM python:3.12-slim AS base

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY kaggle.json.example /root/.kaggle/kaggle.json.example
COPY pyproject.toml .
COPY src/ src/
COPY configs/ configs/
COPY main.py .

RUN useradd -m -u 1000 app && chown -R app:app /app /root/.kaggle
USER app

ENV AGENT_MODE=baseline
ENV LOG_LEVEL=INFO

ENTRYPOINT ["python", "main.py"]

FROM base AS agent
# Same as base — explicit alias for clarity

FROM base AS dev

USER root
COPY .pre-commit-config.yaml .
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt "pytest>=8.0" "ruff>=0.5" "mypy>=1.10" "pre-commit>=4.0"
COPY tests/ tests/
USER app

FROM base AS marimo

USER root
RUN pip install --no-cache-dir "marimo>=0.12"
USER app

EXPOSE 2718
ENTRYPOINT ["marimo", "run", "notebooks/", "--host", "0.0.0.0", "--port", "2718"]
