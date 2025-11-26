# syntax=docker/dockerfile:1
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=0 \
    HUGGINGFACE_HUB_CACHE=/app/models/cache

WORKDIR /app

# System deps for building some python wheels (e.g., sentencepiece)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      gcc \
      openjdk-21-jre-headless \
      fontconfig \
      libfreetype6 \
      libharfbuzz0b \
      fonts-dejavu-core && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure local package resolution
ENV PYTHONPATH=/app

EXPOSE 8501

CMD ["streamlit", "run", "app/main.py", "--server.headless", "true", "--server.address", "0.0.0.0", "--server.port", "8501"]
