import asyncio
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Update

from config import TOKEN
from handlers import main_menu, character, profile, leveling, combat, inventory

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Создание бота и диспетчера
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
dp.include_routers(
    main_menu.router,
    character.router,
    profile.router,
    leveling.router,
    combat.router,
    inventory.router,
)

# Обработчик webhook-запросов
async def webhook_handler(request: web.Request):
    update_data = await request.json()
    update = Update.model_validate(update_data)
    await dp.feed_update(bot, update)
    return web.Response()

# Создание и запуск Aiohttp приложения
async def main():
    app = web.Application()
    app.router.add_post("/", webhook_handler)

    # Установка вебхука Telegram
    webhook_url = "https://character-bot1.onrender.com/"  # без /webhook
    await bot.set_webhook(webhook_url)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=10000)  # Render ждёт PORT env
    await site.start()

    logging.info("Bot is running with webhook...")

    # Ждём бесконечно (чтобы не завершался)
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())