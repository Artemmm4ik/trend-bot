import datetime
from googleapiclient.discovery import build


def get_trends(api_key, region='RU'):
    """
    Получает горячие тренды прямо из YouTube — топ самых популярных видео страны прямо сейчас.
    Работает через официальный YouTube Data API v3.
    Не зависит от Google Trends и не блокируется на серверах.
    region: ISO-код страны, например 'RU', 'US', 'DE'
    """
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)

        # Запрашиваем топ-20 трендовых видео YouTube для страны
        request = youtube.videos().list(
            part='snippet',
            chart='mostPopular',
            regionCode=region,
            maxResults=20,
            videoCategoryId='0'  # 0 = все категории
        )
        response = request.execute()
        items = response.get('items', [])

        # Извлекаем ключевые слова из тегов и заголовков видео
        keywords = set()
        raw_titles = []

        for item in items:
            snippet = item.get('snippet', {})
            title = snippet.get('title', '')
            tags = snippet.get('tags', [])
            raw_titles.append(title)

            # Берём первые 3 тега каждого видео как потенциальные темы
            for tag in tags[:3]:
                if len(tag) > 3:  # Отфильтровываем слишком короткие теги
                    keywords.add(tag.lower())

        print(f"[YouTube Trends] Найдено {len(items)} трендовых видео, {len(keywords)} уникальных тем")
        
        # Возвращаем уникальные темы (из тегов) + оригинальные заголовки видео как запасной вариант
        keyword_list = list(keywords)[:7]
        
        # Если тегов нет — используем заголовки видео напрямую
        if len(keyword_list) < 3:
            keyword_list = raw_titles[:10]

        return keyword_list[:10]

    except Exception as e:
        print(f"Ошибка получения трендов YouTube: {e}")
        return []


def check_youtube_supply(keyword, api_key):
    """
    Проверяет количество свежих видео по ключевому слову на YouTube (за последние 7 дней).
    Оценивает, насколько тема ещё не занята конкурентами.
    """
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)

        # Дата неделю назад в формате RFC 3339
        week_ago = (datetime.datetime.utcnow() - datetime.timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')

        request = youtube.search().list(
            q=keyword,
            part='snippet',
            type='video',
            maxResults=5,
            publishedAfter=week_ago,
            order='viewCount'
        )
        response = request.execute()

        total_recent = response['pageInfo']['totalResults']
        items = response.get('items', [])

        # Оценка ниши: чем меньше конкуренции при горячем тренде — тем лучше
        score = 10
        if total_recent > 500:
            score -= 6
        elif total_recent > 100:
            score -= 3

        return {
            "keyword": keyword,
            "recent_videos_count": total_recent,
            "top_video_title": items[0]['snippet']['title'] if items else "Свежих видео не найдено!",
            "score": score,
            "opportunity": "🔥 ИДЕАЛЬНО" if score >= 8 else "👍 НОРМАЛЬНО" if score >= 5 else "❌ ПЕРЕГРЕТО"
        }

    except Exception as e:
        print(f"Ошибка YouTube API для '{keyword}': {e}")
        return None
