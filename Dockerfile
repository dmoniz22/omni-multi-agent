FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    libpq-dev \
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
        lxml \
        aiosqlite \
        psycopg[binary]

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV API_PORT=8000

EXPOSE 8000 7860

COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
