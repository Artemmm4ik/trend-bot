import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiohttp import web
from dotenv import load_dotenv

from services import get_trends, check_youtube_supply

# Загружаем переменные окружения
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    welcome_text = (
        "Привет! Я **Детектор Зарождающихся Трендов** 🚀\n\n"
        "Я ищу темы, которые прямо сейчас разрывают Google Trends, и проверяю, "
        "много ли конкурентов уже успели снять про это на YouTube.\n\n"
        "Жми /scan чтобы найти свежие ниши!"
    )
    await message.answer(welcome_text, parse_mode="Markdown")

@dp.message(Command("scan"))
async def cmd_scan(message: Message):
    if not YOUTUBE_API_KEY:
        await message.answer("❌ Ошибка: Не настроен YOUTUBE_API_KEY на сервере.")
        return

    msg = await message.answer("⏳ Собираю топ-тренды из Google (это займет около 10 секунд)...")
    
    # Запускаем синхронный парсер в отдельном потоке, чтобы не блочить бота
    trends = await asyncio.to_thread(get_trends, 'russia')
    
    if not trends:
        await msg.edit_text("❌ Не удалось получить тренды. Возможно, Google заблокировал IP сервера. Попробуйте позже.")
        return
        
    await msg.edit_text(f"✅ Найдено {len(trends)} трендов. Анализирую конкуренцию на YouTube (берем топ-5)...")
    
    results_text = "📈 **Сводка по трендам (Россия)** 📈\n\n"
    
    # Берем топ-5 трендов, чтобы не тратить весь лимит YouTube API (лимит 10 000 квот в день, 1 поиск = 100 квот)
    for idx, trend in enumerate(trends[:5], 1):
        data = await asyncio.to_thread(check_youtube_supply, trend, YOUTUBE_API_KEY)
        # Небольшая пауза во избежание rate limit
        await asyncio.sleep(0.5)
        
        if data:
            results_text += f"**{idx}. {trend.capitalize()}**\n"
            results_text += f"📊 Оценка ниши: {data['score']}/10 ({data['opportunity']})\n"
            results_text += f"🎬 Новых видео за 7 дней: {data['recent_videos_count']}\n"
            results_text += f"🥇 Пример видео: *{data['top_video_title']}*\n\n"
        else:
            results_text += f"**{idx}. {trend}** - Ошибка анализа (возможно кончилась квота API)\n\n"
            
    await msg.edit_text(results_text, parse_mode="Markdown")

# --- НАСТРОЙКИ ДЛЯ RENDER.COM ---
# Render требует, чтобы web-сервис слушал определенный порт. 
# Мы создаем фейковый веб-сервер, пока бот работает в фоне.

async def handle_ping(request):
    return web.Response(text="Бот успешно запущен и работает!")

async def main():
    # Настраиваем веб-сервер
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    print(f"Fake Web Server запущен на порту {port} (для Health Check Render.com)")
    
    # Запускаем бота
    await bot.delete_webhook(drop_pending_updates=True)
    print("Бот начинает Long Polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
