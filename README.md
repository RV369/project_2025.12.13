# project_2025.12.13
# Video Analytics Telegram Bot

Бот отвечает на вопросы на русском языке по статистике видео.

## Запуск

- Склонируйте репозиторий

```sh
git clone git@github.com:RV369/project_2025.12.13.git
```

- Переместитесь в папку project_2025.12.13

```sh
cd project_2025.12.13
```

1. Создайте `.env`:
   ```env
   BOT_TOKEN=your_bot_token
   YANDEX_API_KEY=your_llm_api_key
   YANDEX_FOLDER_ID=your_folder_id
   HOST=localhost
   DB_NAME=video_analytics
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_PORT=5432
   ```
- Первый запуск микросервиса с наполнением тестовыми данными

```sh
docker compose up -d db && python scripts/load_data.py && docker compose up bot
```

- Запуск микросервиса если данные уже есть в базе данных

```sh
docker compose up
```