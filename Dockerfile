FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY tests/ ./tests/
COPY pytest.ini .

RUN mkdir -p logs app/static/uploaded app/static/edited app/static/detected

RUN pytest --cov=app --cov-report=term-missing --cov-fail-under=80 || exit 1

RUN pip uninstall -y \
    pytest \
    pytest-asyncio \
    pytest-cov \
    pytest-mock \
    faker \
    httpx \
    coverage \
    && rm -rf /app/tests /app/pytest.ini /app/htmlcov /app/.pytest_cache /app/.coverage

RUN apt-get purge -y build-essential libjpeg-dev zlib1g-dev libpng-dev && \
    apt-get install -y --no-install-recommends \
    libjpeg62-turbo \
    zlib1g \
    libpng16-16 \
    && apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

