# ---------- Builder ----------
FROM python:3.12-slim AS builder

WORKDIR /app

ENV PATH="/opt/venv/bin:$PATH"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libjpeg-dev \
        libpng-dev \
        zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY app ./app

RUN python -m venv /opt/venv && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# ---------- Test ----------
FROM builder AS test

COPY tests ./tests
COPY pytest.ini .

RUN pip install --no-cache-dir ".[test]" && \
    mkdir -p \
        logs \
        app/static/uploaded \
        app/static/edited \
        app/static/detected && \
    pytest \
        -m "not inference" \
        --cov=app \
        --cov-report=term-missing \
        --cov-fail-under=80

# ---------- Runtime ----------
FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        libjpeg62-turbo \
        libpng16-16 \
        zlib1g && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
COPY app ./app

COPY --from=test /app/pyproject.toml /tmp/.tests-passed

RUN mkdir -p \
    logs \
    app/static/uploaded \
    app/static/edited \
    app/static/detected

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -fsS http://localhost:8000/health/ready || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]