import os
from aiogram import F, Router
from aiogram.types import Message
from deep_translator import GoogleTranslator
from google import genai
from PIL import Image
import config

router = Router()
client = genai.Client(api_key=config.GEMINI_API_KEY)
MODEL_NAME = "gemini-2.5-flash"

def is_allowed(chat_id: int, user_id: int) -> bool:
    if chat_id > 0:
        return True
    return chat_id in config.ALLOWED_GROUP_IDS or user_id == config.OWNER_ID

async def get_text_from_msg(message: Message, args: str) -> str:
    if args:
        return args.strip()
    if message.reply_to_message:
        reply = message.reply_to_message
        text = reply.text or reply.caption
        if text:
            return text.strip()
    return ""

@router.message(F.text.startswith("/trab"))
async def cmd_trab(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    text = await get_text_from_msg(message, message.text.replace("/trab", "").strip())
    if not text:
        await message.reply("⚠️ أرسل النص المراد ترجمته.")
        return
    try:
        translated = GoogleTranslator(source='auto', target='ar').translate(text)
        await message.reply(translated or "فشلت الترجمة.")
    except Exception:
        await message.reply("❌ حدث خطأ في الترجمة.")

@router.message(F.text.startswith("/treng"))
async def cmd_treng(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    text = await get_text_from_msg(message, message.text.replace("/treng", "").strip())
    if not text:
        await message.reply("⚠️ أرسل النص المراد ترجمته.")
        return
    try:
        translated = GoogleTranslator(source='auto', target='en').translate(text)
        await message.reply(translated or "فشلت الترجمة.")
    except Exception:
        await message.reply("❌ حدث خطأ في الترجمة.")

@router.message(F.text.startswith("/cor"))
async def cmd_cor(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    text = await get_text_from_msg(message, message.text.replace("/cor", "").strip())
    if not text:
        await message.reply("⚠️ أرسل النص للتصحيح.")
        return
    try:
        prompt = f"Correct the spelling and grammar of this text. Return ONLY the corrected version:\n\n{text}"
        res = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        await message.reply(res.text.strip() if res.text else "فشل التصحيح.")
    except Exception:
        await message.reply("❌ حدث خطأ أثناء الاتصال بالذكاء الاصطناعي.")
