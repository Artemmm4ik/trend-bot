import datetime
import urllib.request
import xml.etree.ElementTree as ET
from googleapiclient.discovery import build
def get_trends(geo='RU'):
    """
    Получает горячие тренды через официальный публичный RSS-фид Google Trends.
    Не требует pytrends и не блокируется на серверах Render/AWS.
    geo: код страны, например 'RU', 'US', 'DE'
    """
    try:
        url = f"https://trends.google.com/trending/rss?geo={geo}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        # Парсим теги <title> внутри <item>
        trends = []
        for item in root.findall('./channel/item'):
            title_el = item.find('title')
            if title_el is not None and title_el.text:
                trends.append(title_el.text.strip())
        print(f"[Trends RSS] Получено {len(trends)} трендов для geo={geo}")
        return trends[:10]
    except Exception as e:
        print(f"Ошибка получения трендов через RSS: {e}")
        return []
def check_youtube_supply(keyword, api_key):
    """
    Проверяет количество свежих видео по ключевому слову на YouTube (за последние 7 дней).
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
