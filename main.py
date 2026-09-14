import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import config
from handlers import commands, tts_handler, ai_tools

async def main():
    logging.basicConfig(level=logging.INFO)
    
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # تسجيل الـ Routers (المتحكمات)
    dp.include_router(commands.router)
    dp.include_router(tts_handler.router)
    dp.include_router(ai_tools.router)

    print("🚀 Bot is up and running cleanly...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped!")
