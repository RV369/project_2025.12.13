import json
# import re
# from pathlib import Path
import psycopg2
from psycopg2.extras import execute_values

def extract_first_json_object(file_path):
    """Извлекает первый валидный JSON-объект из файла (даже если за ним идёт мусор)."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()

    # Убираем возможный мусор в начале (вроде {{
    if content.startswith('{'):
        depth = 0
        for i, char in enumerate(content):
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    json_str = content[:i+1]
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        continue
    raise ValueError('Не удалось найти валидный JSON-объект в файле')

def load_to_db(videos_data, conn):
    with conn.cursor() as cur:
        video_rows = []
        snapshot_rows = []

        for v in videos_data:
            # Убедимся, что это видео, а не снапшот
            if 'snapshots' in v and 'creator_id' in v:
                video_rows.append((
                    v['id'],
                    v['creator_id'],
                    v['video_created_at'],
                    v['views_count'],
                    v['likes_count'],
                    v['comments_count'],
                    v['reports_count'],
                    v['created_at'],
                    v['updated_at'],
                ))
                for s in v.get('snapshots', []):
                    snapshot_rows.append((
                        s['id'],
                        s['video_id'],
                        s['views_count'],
                        s['likes_count'],
                        s['comments_count'],
                        s['reports_count'],
                        s['delta_views_count'],
                        s['delta_likes_count'],
                        s['delta_comments_count'],
                        s['delta_reports_count'],
                        s['created_at'],
                        s['updated_at'],
                    ))

        if video_rows:
            execute_values(
                cur,
                """INSERT INTO videos (id, creator_id, video_created_at, views_count, likes_count, comments_count, reports_count, created_at, updated_at)
                   VALUES %s ON CONFLICT (id) DO NOTHING""",
                video_rows
            )
        if snapshot_rows:
            execute_values(
                cur,
                """INSERT INTO video_snapshots (id, video_id, views_count, likes_count, comments_count, reports_count,
                                                delta_views_count, delta_likes_count, delta_comments_count, delta_reports_count,
                                                created_at, updated_at)
                   VALUES %s ON CONFLICT (id) DO NOTHING""",
                snapshot_rows
            )
        conn.commit()
        print(f"Загружено: {len(video_rows)} видео и {len(snapshot_rows)} снапшотов")

if __name__ == '__main__':
    try:
        data = extract_first_json_object('data/videos.json')
        videos = data['videos']
        print(f'Найдено {len(videos)} видео в JSON')
    except Exception as e:
        print(f'Ошибка парсинга: {e}')
        exit(1)

    conn = psycopg2.connect(
        host='localhost',
        database='video_analytics',
        user='postgres',
        password='postgres'
    )
    load_to_db(videos, conn)
    conn.close()
