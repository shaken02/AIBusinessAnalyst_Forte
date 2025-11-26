# Используем официальный образ Python 3.10
FROM python:3.10-slim

# Устанавливаем метаданные
LABEL maintainer="AI Business Analyst Team"
LABEL description="AI Business Analyst - система автоматической генерации бизнес-документации"

# Устанавливаем системные зависимости и Java
# Используем Java 21, так как Java 17 больше не доступна в репозиториях
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends \
    openjdk-21-jre-headless \
    libharfbuzz0b \
    libfontconfig1 \
    curl \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements.txt и устанавливаем Python зависимости
COPY ai_ba_agent/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем весь код приложения
COPY ai_ba_agent/ .

# Устанавливаем переменные окружения
ENV PYTHONPATH=/app
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Проверяем, что Java установлена
RUN java -version

# Проверяем, что plantuml.jar существует
RUN test -f libs/plantuml.jar || (echo "ERROR: plantuml.jar not found in libs/" && exit 1)

# Открываем порт для Streamlit
EXPOSE 8501

# Команда запуска
CMD ["python", "-m", "streamlit", "run", "app/main.py", "--server.headless", "true", "--server.port", "8501", "--server.address", "0.0.0.0"]

