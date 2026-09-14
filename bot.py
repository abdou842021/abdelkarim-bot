import asyncio
import random

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

import config


async def main():
    if not config.BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set.")

    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def start_handler(message: Message):
        await message.answer(
            "Welcome to Abdelkarim English Learning Bot! 🇬🇧🇺🇸\n\n"
            "Use /help to see all available commands."
        )

    @dp.message(Command("help"))
    async def help_handler(message: Message):
        await message.answer(
            "📚 English Learning Bot\n\n"
            "/trab - Translate to Arabic 🇩🇿\n"
            "/treng - Translate to English 🇬🇧\n"
            "/sus - American pronunciation 🇺🇸\n"
            "/suk - British pronunciation 🇬🇧\n"
            "/syn - Synonyms, antonyms and example 📖\n"
            "/cor - Grammar and spelling correction ✏️\n"
            "/quiz - English vocabulary quiz 🧠\n"
            "/ocr - Read text from an image 📷\n"
            "/groups - Manage activated groups 👥"
        )

    @dp.message(F.text)
    async def name_trigger_handler(message: Message):
        text = message.text.lower()

        if text.startswith("/"):
            return

        for trigger in config.NAME_TRIGGERS:
            if trigger.lower() in text:
                reply = random.choice(config.NAME_REPLIES)
                await message.reply(reply)
                break

    print("Bot is running...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
