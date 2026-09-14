import os
from aiogram import F, Router
from aiogram.types import FSInputFile, Message
import edge_tts
import eng_to_ipa as ipa
import config

router = Router()

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

async def process_tts(message: Message, text: str, voice: str, is_us: bool):
    if not text:
        await message.reply("⚠️ يرجى إرسال نص أو الرد على رسالة بها نص.")
        return

    words = text.split()
    if len(words) > config.MAX_WORDS:
        await message.reply("⚠️ النص طويل جداً.")
        return

    output_audio = f"tts_{message.message_id}.mp3"
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_audio)

        flag = "🇺🇸" if is_us else "🇬🇧"
        caption = f"{flag} {text}"

        # توليد الفونتيك محلياً وبشكل فوري
        phonetic = ipa.convert(text)
        if phonetic:
            caption += f"\n🗣 [{phonetic}]"

        audio_file = FSInputFile(output_audio)
        await message.reply_audio(audio=audio_file, caption=caption)
    except Exception as e:
        await message.reply(f"❌ حدث خطأ أثناء توليد الصوت: {e}")
    finally:
        if os.path.exists(output_audio):
            os.remove(output_audio)

@router.message(F.text.startswith("/sus"))
async def cmd_sus(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    text = await get_text_from_msg(message, message.text.replace("/sus", "").strip())
    await process_tts(message, text, config.VOICE_AMERICAN, is_us=True)

@router.message(F.text.startswith("/suk"))
async def cmd_suk(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    text = await get_text_from_msg(message, message.text.replace("/suk", "").strip())
    await process_tts(message, text, config.VOICE_BRITISH, is_us=False)
