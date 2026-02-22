FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src/ ./src/

RUN pip install --no-cache-dir uv && \
    uv pip install --system -r <(grep -v "dev" pyproject.toml | grep -v "test" || true) pyproject.toml

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000 7860

CMD ["python", "-m", "uvicorn", "omni.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
