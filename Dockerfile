FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright browsers
RUN pip install playwright && \
    playwright install chromium && \
    playwright install-deps

COPY pyproject.toml README.md ./
COPY src/ ./src/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir . && \
    pip install --no-cache-dir \
        pyautogui \
        mss \
        pygetwindow \
        playwright \
        httpx \
        beautifulsoup4 \
        lxml

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000 7860

# Run both API and Dashboard in background
CMD python -m uvicorn omni.api.app:app --host 0.0.0.0 --port 8000 & \
    python -m omni.dashboard.main
