import io

from google import genai
from google.genai import types

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

import config

router = Router()


def get_gemini_client():
    if not config.GEMINI_API_KEY:
        return None

    return genai.Client(
        api_key=config.GEMINI_API_KEY
    )


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


# =========================================================
# /cor
# Grammar and spelling correction
# =========================================================

@router.message(Command("cor"))
async def correct_text(message: Message):
    text = get_text(message)

    if not text and message.reply_to_message:
        text = (
            message.reply_to_message.text
            or message.reply_to_message.caption
            or ""
        ).strip()

    if not text:
        await message.reply(
            "⚠️ Please send text after /cor "
            "or reply to a message."
        )
        return

    client = get_gemini_client()

    if client is None:
        await message.reply(
            "❌ Gemini API is not configured."
        )
        return

    prompt = f"""
Correct the English text below.

Rules:
1. Keep the original meaning.
2. Fix grammar, spelling, punctuation, and natural phrasing.
3. If the sentence is already correct, say that it is correct.
4. Give the corrected version first.
5. Then briefly explain the important corrections.
6. Keep the explanation simple for an English learner.

Text:
{text}
"""

    try:
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt,
        )

        answer = response.text

        if not answer:
            raise ValueError("Empty Gemini response")

        await message.reply(
            f"✏️ <b>Correction</b>\n\n{answer}",
            parse_mode="HTML",
        )

    except Exception:
        await message.reply(
            "❌ Correction failed. Please try again."
        )


# =========================================================
# /ocr
# Read English text from an image
# =========================================================

@router.message(Command("ocr"))
async def ocr_command(message: Message):
    if not message.reply_to_message:
        await message.reply(
            "📷 Please reply to an image with /ocr."
        )
        return

    photo_message = message.reply_to_message

    if not photo_message.photo:
        await message.reply(
            "⚠️ The replied message does not contain an image."
        )
        return

    client = get_gemini_client()

    if client is None:
        await message.reply(
            "❌ Gemini API is not configured."
        )
        return

    try:
        photo = photo_message.photo[-1]

        file = await message.bot.get_file(
            photo.file_id
        )

        image_bytes = io.BytesIO()

        await message.bot.download_file(
            file.file_path,
            destination=image_bytes,
        )

        image_bytes.seek(0)

        prompt = """
Read the text visible in this image.

Return:
1. The text exactly as clearly as possible.
2. If it is English, correct obvious OCR mistakes only.
3. Do not invent missing words.
4. Do not translate unless necessary to identify unclear text.
"""

        image_part = types.Part.from_bytes(
            data=image_bytes.getvalue(),
            mime_type="image/jpeg",
        )

        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=[
                prompt,
                image_part,
            ],
        )

        answer = response.text

        if not answer:
            raise ValueError("Empty Gemini response")

        await message.reply(
            f"📷 <b>Text from image</b>\n\n{answer}",
            parse_mode="HTML",
        )

    except Exception:
        await message.reply(
            "❌ I couldn't read the text from this image."
      )
