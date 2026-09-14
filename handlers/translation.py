from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from deep_translator import GoogleTranslator

router = Router()


def get_text(message: Message) -> str:
    if message.text:
        parts = message.text.split(maxsplit=1)
        if len(parts) > 1:
            return parts[1].strip()

    if message.reply_to_message:
        return (
            message.reply_to_message.text
            or message.reply_to_message.caption
            or ""
        ).strip()

    return ""


@router.message(Command("trab"))
async def translate_to_arabic(message: Message):
    text = get_text(message)

    if not text:
        await message.reply(
            "⚠️ Please send a text after /trab "
            "or reply to a message."
        )
        return

    try:
        translated = GoogleTranslator(
            source="auto",
            target="ar"
        ).translate(text)

        await message.reply(
            f"🇩🇿 Arabic:\n{translated}"
        )

    except Exception:
        await message.reply(
            "❌ Translation failed. Please try again."
        )


@router.message(Command("treng"))
async def translate_to_english(message: Message):
    text = get_text(message)

    if not text:
        await message.reply(
            "⚠️ Please send a text after /treng "
            "or reply to a message."
        )
        return

    try:
        translated = GoogleTranslator(
            source="auto",
            target="en"
        ).translate(text)

        await message.reply(
            f"🇬🇧 English:\n{translated}"
        )

    except Exception:
        await message.reply(
            "❌ Translation failed. Please try again."
)
