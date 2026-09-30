import os
import datetime
from pytrends.request import TrendReq
from googleapiclient.discovery import build

def get_trends(country='russia'):
    """
    Получает горячие тренды из Google Trends
    """
    try:
        # Используем подмену User-Agent, чтобы снизить шанс бана IP
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'}
        pytrends = TrendReq(hl='ru-RU', tz=180, requests_args={'headers': headers})
        
        # Получаем DataFrame с трендами
        df = pytrends.trending_searches(pn=country)
        return df[0].tolist()[:10]  # Возвращаем Топ-10
    except Exception as e:
        print(f"Ошибка получения трендов: {e}")
        return []

def check_youtube_supply(keyword, api_key):
    """
    Проверяет количество свежих видео по ключевому слову на YouTube (за последние 7 дней)
    """
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        # Считаем дату неделю назад
        week_ago = (datetime.datetime.utcnow() - datetime.timedelta(days=7)).isoformat() + "Z"
        
        # Запрос к API
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
        
        # Оценка ниши (от 1 до 10)
        # Если видео за неделю мало (спрос есть, а конкуренции нет) - это круто
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
