from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

import config

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message):
    await message.reply(
        "🇬🇧 <b>Welcome to Abdelkarim English Learning Bot!</b>\n\n"
        "📚 Learn English through translation, pronunciation, "
        "vocabulary, correction, and more.\n\n"
        "Use /help to see the available commands.",
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def help_handler(message: Message):
    await message.reply(
        "📚 <b>Abdelkarim English Learning Bot</b>\n\n"

        "🌍 <b>Translation</b>\n"
        "/trab — Translate to Arabic 🇩🇿\n"
        "/treng — Translate to English 🇬🇧\n\n"

        "🗣 <b>Pronunciation</b>\n"
        "/sus — American pronunciation 🇺🇸\n"
        "/suk — British pronunciation 🇬🇧\n\n"

        "📖 <b>Vocabulary</b>\n"
        "/syn — Synonyms, antonyms, meaning & example\n\n"

        "✏️ <b>AI Tools</b>\n"
        "/cor — Correct English text\n"
        "/ocr — Read text from an image 📷\n\n"

        "👥 <b>Groups</b>\n"
        "/groups — Activated groups (owner only)\n\n"

        "🧠 <b>Quiz</b>\n"
        "/quiz — English vocabulary quiz\n\n"

        f"🤖 <b>{config.BOT_NAME}</b>"
        ,
        parse_mode="HTML",
    )
