import os
import re

import httpx
import psycopg2
from dotenv import load_dotenv

load_dotenv()

YANDEX_API_KEY = os.getenv('YANDEX_API_KEY')
YANDEX_FOLDER_ID = os.getenv('YANDEX_FOLDER_ID')
if not YANDEX_FOLDER_ID:
    raise ValueError('YANDEX_FOLDER_ID не задан в переменных окружения')

MODEL_URI = f'gpt://{YANDEX_FOLDER_ID}/yandexgpt/latest'
UPL = 'https://llm.api.cloud.yandex.net/foundationModels/v1/completion'

HEADERS = {
    'Authorization': f'Api-Key {YANDEX_API_KEY}',
    'Content-Type': 'application/json',
}

# === Промпт ===
SCHEMA_PROMPT = """
У тебя есть две таблицы в PostgreSQL:

1. `videos`:
   - id UUID
   - creator_id UUID
   - video_created_at TIMESTAMPTZ — когда видео было опубликовано
   - views_count, likes_count, comments_count,
   reports_count — итоговые значения
   - created_at, updated_at

2. `video_snapshots`:
   - id UUID
   - video_id UUID → videos.id
   - views_count, likes_count, comments_count,
   reports_count — текущие значения на момент замера
   - delta_views_count, delta_likes_count и т.д. — прирост за последний час
   - created_at TIMESTAMPTZ — время замера (почасовой)

Правила:
- Всегда возвращай ТОЛЬКО валидный SQL-запрос на PostgreSQL.
- Запрос должен возвращать ОДНО ЧИСЛО (например,
через SELECT COUNT(...), SELECT SUM(...)).
- Не используй ``` или пояснения.
- Даты в вопросах могут быть в формате "28 ноября 2025" — преобразуй в
'2025-11-28'.
- Для диапазонов дат используй BETWEEN или >= / <=.
- Прирост за день — это SUM(delta_views_count) из video_snapshots,
где DATE(created_at) = '...'
- "Сколько видео" → COUNT(DISTINCT id) FROM videos
- "Набрало больше 100000 просмотров" → WHERE views_count > 100000
- Не галлюцинируй. Если не знаешь — верни 0.

Пример:
Вопрос: Сколько всего видео есть в системе?
Ответ: SELECT COUNT(*) FROM videos;
"""


def normalize_date(text):
    months = {
        'января': '01',
        'февраля': '02',
        'марта': '03',
        'апреля': '04',
        'мая': '05',
        'июня': '06',
        'июля': '07',
        'августа': '08',
        'сентября': '09',
        'октября': '10',
        'ноября': '11',
        'декабря': '12',
    }

    def repl(m):
        day = m.group(1)
        month = months.get(m.group(2).lower(), '01')
        year = m.group(3)
        return f'{year}-{month}-{day.zfill(2)}'

    return re.sub(r'(\d{1,2})\s+([а-яА-Я]+)\s+(\d{4})', repl, text)


def text_to_sql_result(query: str) -> int:
    query_norm = normalize_date(query.strip())

    messages = [
        {'role': 'system', 'text': SCHEMA_PROMPT},
        {'role': 'user', 'text': query_norm},
    ]

    payload = {
        'modelUri': MODEL_URI,
        'completionOptions': {
            'stream': False,
            'temperature': 0.0,
            'maxTokens': '150',
        },
        'messages': messages,
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                url=UPL,
                headers=HEADERS,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            sql = data['result']['alternatives'][0]['message']['text'].strip()

        # Очистка от пояснений
        sql = re.split(r'\n', sql)[0]  # берём первую строку
        sql = re.sub(r'^[^S]*', '', sql)  # убираем всё до "SELECT"
        sql = sql.split(';')[0] + ';'  # оставляем до первой ;

        # Защита
        if (
            not sql.lower().startswith('select')
            or 'delete' in sql.lower()
            or 'insert' in sql.lower()
        ):
            return 0

        with psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT'),
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                row = cur.fetchone()
                return int(row[0]) if row and row[0] is not None else 0

    except Exception as e:
        print(f'YandexGPT ошибка: {e}')
        return 0
