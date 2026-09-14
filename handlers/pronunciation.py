import os

import edge_tts
import eng_to_ipa as ipa

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import FSInputFile, Message

import config

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


async def make_pronunciation(
    message: Message,
    text: str,
    voice: str,
    flag: str,
):
    if not text:
        await message.reply(
            "⚠️ Please send a word or sentence after the command "
            "or reply to a message."
        )
        return

    if len(text.split()) > config.MAX_WORDS:
        await message.reply("⚠️ The text is too long.")
        return

    filename = f"voice_{message.chat.id}_{message.message_id}.mp3"

    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(filename)

        try:
            phonetic = ipa.convert(text)
        except Exception:
            phonetic = ""

        caption = f"{flag} {text}"

        if phonetic:
            caption += f"\n🗣️ [{phonetic}]"

        audio = FSInputFile(filename)

        await message.reply_audio(
            audio=audio,
            caption=caption,
        )

    except Exception:
        await message.reply(
            "❌ Sorry, I couldn't generate the pronunciation."
        )

    finally:
        if os.path.exists(filename):
            os.remove(filename)


@router.message(Command("sus"))
async def american_pronunciation(message: Message):
    text = get_text(message)

    await make_pronunciation(
        message,
        text,
        config.VOICE_AMERICAN,
        "🇺🇸",
    )


@router.message(Command("suk"))
async def british_pronunciation(message: Message):
    text = get_text(message)

    await make_pronunciation(
        message,
        text,
        config.VOICE_BRITISH,
        "🇬🇧",
      )
