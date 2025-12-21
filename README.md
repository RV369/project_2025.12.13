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
- Чтобы получить токен Telegram-бота, нужно создать бота через официального бота @BotFather.
```sh
/newbot
```
- BotFather попросит ввести:
Имя бота (public name, можно на русском, например: Аналитика видео).
Username бота (должен оканчиваться на bot, например: my_video_analytics_bot).

- Если всё сделано правильно, @BotFather пришлёт сообщение в котором будет содержатся токен, сохраните эу строку в файл .env 'BOT_TOKEN=your_bot_token'

- После запуска бота:

Найдите его в Telegram: t.me/my_video_analytics_bot
Нажмите «Start»
Отправьте вопрос, например:
Сколько всего видео есть в системе?

Если приходит число — всё работает!

## Архитектура и подход к NLP → SQL

- Общая архитектура:

Telegram-бот на aiogram 3+ принимает текстовые сообщения на русском языке.
Каждое сообщение передаётся в модуль NLP-обработки, который:
нормализует даты (например, «28 ноября 2025» → 2025-11-28);
формирует промпт с описанием схемы БД;
отправляет запрос в YandexGPT (через REST API);
получает от модели только SQL-запрос;
выполняет его в PostgreSQL и возвращает одно число.

- Подход к преобразованию текста в SQL:

Используется LLM (YandexGPT) с строго заданным системным промптом.
Промпт содержит:
описание структуры таблиц videos и video_snapshots;
правила формирования запросов (только SELECT, только агрегаты, без пояснений);
примеры вход/выход (few-shot prompting).
Все входные даты предварительно нормализуются с помощью регулярных выражений.
Для защиты от инъекций:
разрешены только SELECT-запросы;
запрещены ключевые слова INSERT, UPDATE, DELETE, DROP;
из ответа LLM извлекается только первая строка до ;.

- В проекте схема данных описывается в виде текстового промпта, который передаётся в LLM (YandexGPT) как системное сообщение (role: "system"). Этот промпт содержит:

чёткое описание структуры таблиц;
бизнес-логику полей;
строгие правила формата ответа;
примеры запросов.


```sh
У тебя есть две таблицы в PostgreSQL:

1. `videos`:
   - id UUID
   - creator_id UUID
   - video_created_at TIMESTAMPTZ — когда видео было опубликовано
   - views_count, likes_count, comments_count, reports_count — итоговые значения
   - created_at, updated_at

2. `video_snapshots`:
   - id UUID
   - video_id UUID → videos.id
   - views_count, likes_count, comments_count, reports_count — текущие значения на момент замера
   - delta_views_count, delta_likes_count и т.д. — прирост за последний час
   - created_at TIMESTAMPTZ — время замера (почасовой)

Правила:
- Всегда возвращай ТОЛЬКО валидный SQL-запрос на PostgreSQL.
- Запрос должен возвращать ОДНО ЧИСЛО (например, через SELECT COUNT(...), SELECT SUM(...)).
- Не используй ``` или пояснения.
- Даты в вопросах могут быть в формате "28 ноября 2025" — преобразуй в '2025-11-28'.
- Для диапазонов дат используй BETWEEN или >= / <=.
- Прирост за день — это SUM(delta_views_count) из video_snapshots, где DATE(created_at) = '...'
- "Сколько видео" → COUNT(DISTINCT id) FROM videos
- "Набрало больше 100000 просмотров" → WHERE views_count > 100000
- Не галлюцинируй. Если не знаешь — верни 0.

Пример:
Вопрос: Сколько всего видео есть в системе?
Ответ: SELECT COUNT(*) FROM videos;
```
