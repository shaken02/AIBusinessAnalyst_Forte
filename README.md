# AI Code Review Assistant

Автоматический AI Code Review Assistant, который интегрируется с GitLab и анализирует код в Merge Requests с помощью Google Gemini API.

## Описание проекта

Это FastAPI backend-сервис, который:
- Принимает webhook'и от GitLab при создании/обновлении Merge Requests и push событиях
- Анализирует изменения в коде через Google Gemini API
- Автоматически публикует комментарии с детальным анализом в Merge Request
- Управляет лейблами и блокирует/разблокирует merge на основе вердикта AI
- Кэширует результаты анализа для оптимизации производительности

## Основные возможности

- **Автоматический анализ кода**: AI анализирует все файлы в MR одним запросом
- **Детальная обратная связь**: Для каждого файла предоставляется вердикт (APPROVE/CHANGES_REQUESTED/REJECT) с объяснением
- **Обнаружение проблем**: Находит баги, уязвимости безопасности, ошибки логики, плохие практики
- **Кэширование**: Результаты анализа кэшируются для избежания повторных запросов к Gemini
- **Push-time анализ**: Анализ начинается сразу при `git push`, даже до создания MR
- **Автоматическое управление**: Блокирует/разблокирует merge и управляет лейблами автоматически

## Структура проекта

```
AI-Code Review Assistant/
├── code_review_backend/          # Backend сервис
│   ├── __init__.py
│   ├── main.py                   # FastAPI приложение и webhook обработчик
│   ├── config.py                 # Конфигурация (GitLab, Gemini, сервер)
│   ├── gitlab_client.py          # Клиент для GitLab API
│   ├── review_engine.py          # Движок анализа кода через Gemini
│   ├── prompts.py                # Промпты для LLM
│   ├── webhook_handler.py        # Обработка и валидация webhook'ов
│   ├── requirements.txt          # Python зависимости
│   ├── start.sh                  # Скрипт запуска сервера
│   ├── good_code.py              # Пример хорошего кода (для тестирования)
│   ├── needs_fixes.py            # Пример кода, требующего улучшений
│   └── bad_code.py               # Пример кода с критическими проблемами
├── .env                          # Переменные окружения (НЕ коммитится)
├── .gitignore                    # Игнорируемые файлы
└── README.md                     # Этот файл
```

## Требования и установка

### Необходимое ПО

1. **Python 3.10+**
   ```bash
   python3 --version  # Должно быть 3.10 или выше
   ```

2. **Google Gemini API Key**
   - Получите API ключ на [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Каждый пользователь должен использовать свой собственный API ключ

3. **GitLab Access Token**
   - Создайте Personal Access Token в GitLab с правами:
     - `api` - для доступа к GitLab API
     - `write_repository` - для публикации комментариев и управления MR

4. **ngrok или Cloudflare Tunnel** (для локальной разработки)
   - Для получения публичного URL для webhook'ов от GitLab

### Установка зависимостей

1. **Клонируйте репозиторий:**
   ```bash
   git clone https://github.com/shaken02/AI-Code-Review-Assistant.git
   cd AI-Code-Review-Assistant
   ```

2. **Создайте виртуальное окружение:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # На Windows: venv\Scripts\activate
   ```

3. **Установите зависимости:**
   ```bash
   cd code_review_backend
   pip install -r requirements.txt
   ```

4. **Настройте переменные окружения:**
   
   Создайте файл `.env` в корне проекта на основе шаблона:
   ```bash
   cd ..
   cp .env.example .env
   ```
   
   Затем отредактируйте файл `.env` и заполните своими данными:
   - `GITLAB_ACCESS_TOKEN` - ваш Personal Access Token из GitLab (Settings -> Access Tokens)
   - `GEMINI_API_KEY` - ваш API ключ от Google Gemini (получите на https://makersuite.google.com/app/apikey)
   - Остальные параметры можно оставить по умолчанию или настроить под себя
   
   **Важно**: 
   - Не коммитьте файл `.env` в репозиторий (он уже в `.gitignore`)
   - Каждый пользователь должен создать свой собственный `.env` файл со своими ключами
   - Файл `.env.example` содержит только шаблон без реальных секретов

## Запуск сервера

### Способ 1: Использование скрипта (рекомендуется)

**На macOS/Linux:**
```bash
cd code_review_backend
chmod +x start_macos.sh
./start_macos.sh
```

**На Windows:**
```cmd
cd code_review_backend
start_windows.bat
```

Скрипт автоматически:
- Активирует виртуальное окружение
- Устанавливает зависимости (если нужно)
- Запускает FastAPI сервер на порту 8001

### Способ 2: Ручной запуск

```bash
cd code_review_backend
source ../venv/bin/activate  # или путь к вашему venv
export PYTHONPATH="${PWD}:${PYTHONPATH:-}"
uvicorn code_review_backend.main:app --host 0.0.0.0 --port 8001 --reload
```

### Проверка работы

После запуска сервер будет доступен по адресу:
- **API**: http://localhost:8001
- **Health check**: http://localhost:8001/health
- **Webhook endpoint**: http://localhost:8001/gitlab/webhook

## Настройка GitLab Webhook

1. **Получите публичный URL** (для локальной разработки):
   ```bash
   # Используя ngrok
   ngrok http 8001
   ```
   Скопируйте полученный URL (например: `https://abc123.ngrok-free.app`)

2. **Настройте webhook в GitLab:**
   - Перейдите в Settings → Webhooks вашего проекта
   - URL: `https://ваш-ngrok-url.ngrok-free.app/gitlab/webhook`
   - Secret token: значение из `GITLAB_WEBHOOK_SECRET_TOKEN` в `.env`
   - Включите события:
     - ✅ Merge request events
     - ✅ Push events
   - Сохраните webhook

3. **Проверьте работу:**
   - Создайте тестовый Merge Request
   - Проверьте логи сервера - должны появиться сообщения о получении webhook
   - В MR должен появиться комментарий от AI с анализом кода

## Как работает система

1. **Push событие**: При `git push` в ветку GitLab отправляет webhook
   - Backend анализирует изменения через Gemini API
   - Результат кэшируется для будущего MR

2. **Создание MR**: При создании Merge Request
   - Если есть кэш от push - используется кэш (без обращения к Gemini)
   - Если кэша нет - выполняется новый анализ

3. **Обновление MR**: При обновлении MR
   - Проверяется хеш diff
   - Если diff не изменился - анализ пропускается
   - Если diff изменился - выполняется новый анализ

4. **Результат анализа**:
   - AI публикует комментарий в MR с детальным анализом каждого файла
   - Устанавливаются лейблы: `ai-reviewed`, `ready-for-merge`, `changes-requested`, или `rejected`
   - MR блокируется/разблокируется в зависимости от вердикта

## Вердикты AI

- **✅ APPROVE**: Код одобрен, можно мержить
- **❓ CHANGES_REQUESTED**: Требуются изменения перед мержем
- **❌ REJECT**: Код отклонен, есть критические проблемы

## Настройки

### Модель Gemini

Модель настраивается в `.env`:
- `GEMINI_MODEL_NAME`: `gemini-2.5-flash` (быстрая) или `gemini-2.5-pro` (мощная)
- `GEMINI_TEMPERATURE`: 0.0-1.0 (креативность, рекомендуется 0.2)
- `GEMINI_TOP_P`: 0.0-1.0 (разнообразие, рекомендуется 0.9)
- `GEMINI_MAX_TOKENS`: максимальное количество токенов в ответе (рекомендуется 8192)

### Порт сервера

Измените `PORT` в `.env` или используйте флаг `--port` при запуске uvicorn.

## Решение проблем

### Сервер не запускается

- Проверьте Python версию: должна быть 3.10+
- Проверьте виртуальное окружение: должно быть активировано
- Проверьте зависимости: `pip install -r requirements.txt`
- Проверьте файл `.env`: должен существовать и содержать все необходимые ключи

### Webhook не работает

- Проверьте, что сервер запущен и доступен
- Проверьте URL webhook в GitLab (должен быть публичным)
- Проверьте `GITLAB_WEBHOOK_SECRET_TOKEN` в `.env` и в настройках webhook
- Проверьте логи сервера на наличие ошибок

### AI не анализирует код

- Проверьте `GEMINI_API_KEY` в `.env`
- Проверьте доступность Gemini API (интернет-соединение)
- Проверьте лимиты API (не превышены ли лимиты запросов)
- Проверьте логи сервера на наличие ошибок от Gemini API

### Дублирование комментариев

- Система автоматически предотвращает дублирование через кэширование
- Если комментарии дублируются, проверьте логи на наличие ошибок в кэшировании

## Архитектура

- **Backend**: FastAPI (Python)
- **LLM**: Google Gemini API
- **Git Integration**: GitLab API
- **Webhook**: GitLab Webhooks
- **Caching**: In-memory кэш для diff hash и результатов анализа

## Лицензия

Проект создан в рамках хакатона ForteBank AI Forte Case.

## Авторы

Разработано для автоматизации code review процесса.

---

**Важно**: 
- Убедитесь, что файл `.env` создан и содержит все необходимые ключи
- Не коммитьте `.env` файл в репозиторий
- Каждый пользователь должен использовать свой собственный API ключ от Google Gemini
