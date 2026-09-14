import asyncio
import threading
import os

from flask import Flask
from aiogram import Bot, Dispatcher

import config

from handlers.common import router as common_router
from handlers.translation import router as translation_router
from handlers.pronunciation import router as pronunciation_router
from handlers.synonyms import router as synonyms_router
from handlers.ai_tools import router as ai_tools_router
from handlers.quiz import router as quiz_router
from handlers.groups import router as groups_router
from handlers.welcome import router as welcome_router
from handlers.name_replies import router as name_replies_router
from handlers.scheduler import scheduler_loop


# =========================================================
# Flask - Render Web Service
# =========================================================

app = Flask(__name__)


@app.route("/")
def home():
    return "Abdelkarim English Learning Bot is running! 🇬🇧"


@app.route("/health")
def health():
    return "OK"


def run_flask():
    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
    )


# =========================================================
# Telegram Bot
# =========================================================

async def main():
    if not config.BOT_TOKEN:
        raise ValueError(
            "BOT_TOKEN is not set."
        )

    bot = Bot(
        token=config.BOT_TOKEN
    )

    dp = Dispatcher()

    # Register routers
    dp.include_router(common_router)
    dp.include_router(translation_router)
    dp.include_router(pronunciation_router)
    dp.include_router(synonyms_router)
    dp.include_router(ai_tools_router)
    dp.include_router(quiz_router)
    dp.include_router(groups_router)
    dp.include_router(welcome_router)
    dp.include_router(name_replies_router)

    print("Abdelkarim Bot is starting...")

    # Start scheduled messages
    asyncio.create_task(
        scheduler_loop(bot)
    )

    print("Bot is running...")

    await dp.start_polling(bot)


# =========================================================
# Start
# =========================================================

if __name__ == "__main__":
    flask_thread = threading.Thread(
        target=run_flask,
        daemon=True,
    )

    flask_thread.start()

    asyncio.run(main())
