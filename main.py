import asyncio
import os
import re
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, Message
import edge_tts
import google.generativeai as genai
from PIL import Image

# استدعاء ملف الإعدادات
import config

# تهيئة الذكاء الاصطناعي Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()


# ====================== الفلاتر والمساعدات ======================
def is_allowed(chat_id: int, user_id: int) -> bool:
    if chat_id > 0:  # المحادثات الخاصة (Private) مسموحة دائماً
        return True
    return chat_id in config.ALLOWED_GROUP_IDS or user_id == config.OWNER_ID


async def get_text_from_msg(message: Message, args: str) -> str:
    if args:
        return args.strip()
    if message.reply_to_message:
        return (
            message.reply_to_message.text
            or message.reply_to_message.caption
            or ""
        )
    return ""


async def process_tts(message: Message, text: str, voice: str, is_us: bool):
    if not text:
        await message.reply("❌ يرجى كتابة نص أو الرد على رسالة.")
        return

    words = text.split()
    if len(words) > config.MAX_WORDS:
        await message.reply(
            f"⚠️ النص طويل جداً! الحد الأقصى هو {config.MAX_WORDS} كلمة."
        )
        return

    output_audio = f"tts_{message.message_id}.mp3"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_audio)

    flag = "🇺🇸" if is_us else "🇬🇧"
    caption = f"{flag} {text}"

    # إذا كانت 4 كلمات أو أقل يضيف الفونتيك (IPA)
    if len(words) <= 4:
        prompt = f"Provide ONLY the IPA phonetic transcription for this text without any extra text or intro: '{text}'"
        try:
            res = model.generate_content(prompt)
            phonetic = res.text.strip()
            caption += f"\n🗣 [{phonetic}]"
        except Exception:
            pass

    audio_file = FSInputFile(output_audio)
    await message.reply_audio(audio=audio_file, caption=caption)

    if os.path.exists(output_audio):
        os.remove(output_audio)


# ====================== الأوامر والخصائص ======================


# 1. إذن تشغيل البوت في المجموعة (للأونر فقط)
@dp.message(Command("allow"))
async def cmd_allow(message: Message):
    if message.from_user.id != config.OWNER_ID:
        return
    config.ALLOWED_GROUP_IDS.add(message.chat.id)
    await message.reply("✅ تم السماح للبوت بالعمل في هذه المجموعة.")


@dp.message(Command("disallow"))
async def cmd_disallow(message: Message):
    if message.from_user.id != config.OWNER_ID:
        return
    config.ALLOWED_GROUP_IDS.discard(message.chat.id)
    await message.reply("🚫 تم إيقاف البوت في هذه المجموعة.")


# 2. الترحيب بالحي والمسح التلقائي بعد 15 ثانية كي لا يثقل الجروب
@dp.message(F.new_chat_members)
async def welcome_members(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    msg = await message.reply(config.WELCOME_NEW_MEMBER)
    await asyncio.sleep(15)
    try:
        await msg.delete()
    except Exception:
        pass


# 3. النطق البريطاني /suk
@dp.message(Command("suk"))
async def cmd_suk(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    text = await get_text_from_msg(
        message, message.text.replace("/suk", "").strip()
    )
    await process_tts(message, text, config.VOICE_BRITISH, is_us=False)


# 4. النطق الأمريكي /sus
@dp.message(Command("sus"))
async def cmd_sus(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    text = await get_text_from_msg(
        message, message.text.replace("/sus", "").strip()
    )
    await process_tts(message, text, config.VOICE_AMERICAN, is_us=True)


# 5. تصحيح الكتابة والقواعد /cor بالذكاء الاصطناعي
@dp.message(Command("cor"))
async def cmd_cor(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    text = await get_text_from_msg(
        message, message.text.replace("/cor", "").strip()
    )
    if not text:
        await message.reply("❌ اكتب نصاً أو رد على رسالة لتصحيحها.")
        return

    prompt = f"Correct the spelling and grammar of this text. Return ONLY the corrected version without explanations:\n\n{text}"
    res = model.generate_content(prompt)
    await message.reply(f"✏️ **التصحيح:**\n{res.text.strip()}")


# 6. الترجمة إلى العربية /trab
@dp.message(Command("trab"))
async def cmd_trab(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    text = await get_text_from_msg(
        message, message.text.replace("/trab", "").strip()
    )
    if not text:
        await message.reply("❌ اكتب نصاً أو رد على رسالة لترجمتها.")
        return
    prompt = f"Translate this English text to Arabic naturally and accurately:\n{text}"
    res = model.generate_content(prompt)
    await message.reply(f"🇸🇦 **الترجمة:**\n{res.text.strip()}")


# 7. الترجمة إلى الإنجليزية /treng
@dp.message(Command("treng"))
async def cmd_treng(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    text = await get_text_from_msg(
        message, message.text.replace("/treng", "").strip()
    )
    if not text:
        await message.reply("❌ اكتب نصاً أو رد على رسالة لترجمتها.")
        return
    prompt = f"Translate this Arabic text to English naturally and accurately:\n{text}"
    res = model.generate_content(prompt)
    await message.reply(f"🇬🇧 **Translation:**\n{res.text.strip()}")


# 8. الشرح والتحليل اللغوي /exp (مرادفات، أضداد، تصاريف)
@dp.message(Command("exp"))
async def cmd_exp(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    text = await get_text_from_msg(
        message, message.text.replace("/exp", "").strip()
    )
    if not text:
        await message.reply("❌ اكتب كلمة/جملة أو رد عليها لشرحها.")
        return

    prompt = f"""
    Analyze the word or phrase: '{text}'
    Provide in Arabic and English:
    1. Simple meaning (المعنى)
    2. Synonyms & Antonyms (المرادفات والأضداد)
    3. Word forms: Noun, Verb, Adjective (نوع الكلمة وتصاريفها)
    Keep the output well-formatted with markdown and clear headers.
    """
    res = model.generate_content(prompt)
    await message.reply(res.text.strip())


# 9. تحويل النص داخل الصورة إلى كتابة /txt بالرد على الصورة
@dp.message(Command("txt"))
async def cmd_txt(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply("❌ يجب الرد على صورة باستخدام الأمر /txt")
        return

    photo = message.reply_to_message.photo[-1]
    photo_path = f"img_{message.message_id}.jpg"
    await bot.download(photo, destination=photo_path)

    img = Image.open(photo_path)
    prompt = (
        "Extract and write down all readable text inside this image clearly."
    )
    res = model.generate_content([prompt, img])

    extracted_text = res.text.strip() if res.text else "لم أستطع قراءة أي نص."
    await message.reply(f"📝 **النص المستخرج:**\n\n{extracted_text}")

    if os.path.exists(photo_path):
        os.remove(photo_path)


# تشغيل البوت
async def main():
    print("Bot is running...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
