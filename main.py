import asyncio
import os
import re
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
import edge_tts
from deep_translator import GoogleTranslator

# استيراد المكتبة الرسمية لـ Gemini
from google import genai
from PIL import Image

# استدعاء ملف الإعدادات
import config
from quiz_game import register_quiz_handler

# تهيئة عميل Gemini
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-2.5-flash"

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# تسجيل معالج الألعاب
register_quiz_handler(dp)


# ====================== الفلاتر والمساعدات ======================
def is_allowed(chat_id: int, user_id: int) -> bool:
    if chat_id > 0:  # المحادثات الخاصة مسموحة دائماً
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
        await message.reply("Failed")
        return

    words = text.split()
    if len(words) > config.MAX_WORDS:
        await message.reply("Failed")
        return

    output_audio = f"tts_{message.message_id}.mp3"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_audio)

    flag = "🇺🇸" if is_us else "🇬🇧"
    caption = f"{flag} {text}"

    # الفونتيك يظهر أسفل النطق فقط إذا كانت 4 كلمات أو أقل
    if len(words) <= 4:
        accent_type = "American" if is_us else "British"
        prompt = (
            f"Provide ONLY the {accent_type} English IPA phonetic transcription "
            f"for this text without any extra text, intro, or brackets: '{text}'"
        )
        try:
            res = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )
            phonetic = res.text.strip()
            caption += f"\n🗣 [{phonetic}]"
        except Exception:
            pass

    audio_file = FSInputFile(output_audio)
    await message.reply_audio(audio=audio_file, caption=caption)

    if os.path.exists(output_audio):
        os.remove(output_audio)


# ====================== الأوامر والخصائص ======================

# 0. الرد التلقائي عند ذكر اسم عبد الكريم أو مشتقاته
@dp.message(F.text & ~F.text.startswith("/"))
async def check_name_mention(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    
    text = message.text.lower()
    names = ["عبد الكريم", "abdelkarim", "abdulkarim", "karim", "abdelkrim", "كريم"]
    
    if any(name in text for name in names):
        responses = [
            "✨ ربي يفتحها في وجهك يا الغالي عبد الكريم، ويكتب لك التوفيق في كل خطوة تخطوها! 🤲",
            "🌟 نعم يا سي عبد الكريم، ربي يبارك في عمرك ويحفظك ويجعل النجاح حليفك دائماً أينما وطأت قدمك! 🙏",
            "🔥 أهلاً بسيد الرجال عبد الكريم! ربي يسهل عليك صعب الأمور ويجعل التوفيق طريقك الدائم! 🤲",
            "💎 حيا الله الغالي عبد الكريم، ربي ينور دربك ويفتح عليك أبواب الخير الرزق الواسع! 🌟"
        ]
        import random
        await message.reply(random.choice(responses))


# 1. التنبيه عند إضافة البوت لمجموعة جديدة
@dp.my_chat_member()
async def bot_added_to_group(event):
    if event.new_chat_member.status in ["member", "administrator"]:
        group_title = event.chat.title
        group_id = event.chat.id
        added_by = event.from_user.full_name if event.from_user else "شخص ما"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ قبول التفعيل",
                        callback_data=f"allow_{group_id}",
                    ),
                    InlineKeyboardButton(
                        text="❌ رفض وخروج",
                        callback_data=f"disallow_{group_id}",
                    ),
                ]
            ]
        )

        text = (
            f"🔔 **طلب تفعيل جديد لمجموعة!**\n\n"
            f"📌 **اسم المجموعة:** {group_title}\n"
            f"🆔 **الآيدي:** `{group_id}`\n"
            f"👤 **أُضيف بواسطة:** {added_by}\n\n"
            f"هل تريد السماح للبوت بالعمل في هذه المجموعة؟"
        )
        await event.bot.send_message(
            config.OWNER_ID,
            text,
            reply_markup=keyboard,
            parse_mode="Markdown",
        )


# 2. التفاعل مع أزرار القبول والرفض في الخاص
@dp.callback_query(
    F.data.startswith("allow_") | F.data.startswith("disallow_")
)
async def handle_group_decision(callback: CallbackQuery):
    if callback.from_user.id != config.OWNER_ID:
        return

    action, group_id_str = callback.data.split("_")
    group_id = int(group_id_str)

    if action == "allow":
        config.ALLOWED_GROUP_IDS.add(group_id)
        await callback.message.edit_text(
            f"{callback.message.text}\n\n✅ **الحالة:** تم التفعيل بنجاح."
        )
        try:
            await callback.bot.send_message(
                group_id,
                "✅ أهلاً بكم! تم تفعيل البوت في هذه المجموعة بنجاح.",
            )
        except Exception:
            pass
    elif action == "disallow":
        config.ALLOWED_GROUP_IDS.discard(group_id)
        await callback.message.edit_text(
            f"{callback.message.text}\n\n❌ **الحالة:** تم الرفض والخروج من المجموعة."
        )
        try:
            await callback.bot.leave_chat(group_id)
        except Exception:
            pass

    await callback.answer()


# 3. أمر عرض المجموعات الحالية وإدارتها (/groups)
@dp.message(Command("groups"))
async def list_groups(message: Message):
    if message.from_user.id != config.OWNER_ID:
        return

    if not config.ALLOWED_GROUP_IDS:
        await message.reply("Failed")
        return

    text = "📋 **المجموعات المفعلة حالياً:**\n\n"
    buttons = []
    for gid in list(config.ALLOWED_GROUP_IDS):
        text += f"• `{gid}`\n"
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"🚫 إيقاف {gid}", callback_data=f"disallow_{gid}"
                )
            ]
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.reply(text, reply_markup=keyboard, parse_mode="Markdown")


# 4. الترحيب بالعضو الجديد والمسح التلقائي بعد 15 ثانية
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


# 5. أمر البدء والمساعدة /start & /help
@dp.message(Command("start"))
@dp.message(Command("help"))
async def cmd_start(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    WELCOME_MESSAGE = (
        "Welcome to Abd al-Karim Bot for learning English! 🇩🇿🇬🇧🇺🇸\n\n"
        "✨ **Available Commands:**\n"
        "• `/sus` + Text : American Pronunciation 🇺🇸\n"
        "• `/suk` + Text : British Pronunciation 🇬🇧\n"
        "• `/trab` + Text : Translate to Arabic 🇩🇿\n"
        "• `/treng` + Text : Translate to English 🇬🇧\n"
        "• `/syn` + Word : Synonyms, Antonyms & Quick Forms ⚡\n"
        "• `/cor` + Text : Grammar & Spelling Correction ✏️\n"
        "• `/exp` + Word : Detailed Word Explanation & Forms 📚\n"
        "• `/txt` (reply to an image) : Extract text from images 📝\n"
        "• `/stt` (reply to a voice) : Convert voice to text 🎙"
    )
    await message.reply(WELCOME_MESSAGE, parse_mode="Markdown")


# 6. النطق البريطاني /suk
@dp.message(Command("suk"))
async def cmd_suk(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    text = await get_text_from_msg(
        message, message.text.replace("/suk", "").strip()
    )
    await process_tts(message, text, config.VOICE_BRITISH, is_us=False)


# 7. النطق الأمريكي /sus
@dp.message(Command("sus"))
async def cmd_sus(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    text = await get_text_from_msg(
        message, message.text.replace("/sus", "").strip()
    )
    await process_tts(message, text, config.VOICE_AMERICAN, is_us=True)


# 8. الحصول على مرادفات وأضداد وتصاريف سريعة /syn
@dp.message(Command("syn"))
async def cmd_syn(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    text = await get_text_from_msg(message, message.text.replace("/syn", "").strip())
    if not text:
        await message.reply("Failed")
        return

    try:
        prompt = f"""
        Provide a very concise summary (maximum 5-6 lines) for the word/phrase: '{text}'.
        Structure the output in clean Arabic/English as follows:
        - المعنى (Meaning)
        - نوع الكلمة والتصاريف (Noun, Verb, Adj forms)
        - المرادفات (Synonyms: 2-3 words)
        - الأضداد (Antonyms: 2-3 words)
        - مثال قصير (Short example sentence)
        Keep it extremely brief and direct.
        """
        res = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        if res.text:
            await message.reply(res.text.strip())
        else:
            await message.reply("Failed")
    except Exception:
        await message.reply("Failed")


# 9. تصحيح الكتابة والقواعد /cor
@dp.message(Command("cor"))
async def cmd_cor(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    text = await get_text_from_msg(message, message.text.replace("/cor", "").strip())
    if not text:
        await message.reply("Failed")
        return

    try:
        prompt = f"Correct the spelling and grammar of this text. Return ONLY the corrected version:\n\n{text}"
        res = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        if res.text:
            await message.reply(res.text.strip())
        else:
            await message.reply("Failed")
    except Exception:
        await message.reply("Failed")


# 10. الترجمة إلى العربية /trab
@dp.message(Command("trab"))
async def cmd_trab(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    text = await get_text_from_msg(message, message.text.replace("/trab", "").strip())
    if not text:
        await message.reply("Failed")
        return
    try:
        translated = GoogleTranslator(source='auto', target='ar').translate(text)
        await message.answer(translated if translated else "Failed")
    except Exception:
        await message.answer("Failed")


# 11. الترجمة إلى الإنجليزية /treng
@dp.message(Command("treng"))
async def cmd_treng(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    text = await get_text_from_msg(message, message.text.replace("/treng", "").strip())
    if not text:
        await message.reply("Failed")
        return
    try:
        translated = GoogleTranslator(source='auto', target='en').translate(text)
        await message.answer(translated if translated else "Failed")
    except Exception:
        await message.answer("Failed")


# 12. الشرح والتحليل اللغوي /exp
@dp.message(Command("exp"))
async def cmd_exp(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    text = await get_text_from_msg(message, message.text.replace("/exp", "").strip())
    if not text:
        await message.reply("Failed")
        return

    try:
        prompt = f"""
        Analyze the word or phrase: '{text}'
        Provide in Arabic and English:
        1. Simple meaning (المعنى)
        2. Synonyms & Antonyms (المرادفات والأضداد)
        3. Word forms: Noun, Verb, Adjective (نوع الكلمة وتصاريفها)
        Keep the output well-formatted with markdown and clear headers.
        """
        res = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        if res.text:
            await message.reply(res.text.strip())
        else:
            await message.reply("Failed")
    except Exception:
        await message.reply("Failed")


# 13. تحويل النص داخل الصورة إلى كتابة /txt
@dp.message(Command("txt"))
@dp.message(F.photo & F.caption.startswith("/txt"))
async def cmd_txt(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return

    photo = None
    if message.photo:
        photo = message.photo[-1]
    elif message.reply_to_message and message.reply_to_message.photo:
        photo = message.reply_to_message.photo[-1]

    if not photo:
        await message.reply("Failed")
        return

    photo_path = f"img_{message.message_id}.jpg"

    try:
        file = await bot.get_file(photo.file_id)
        await bot.download_file(file.file_path, photo_path)

        img = Image.open(photo_path)
        img.thumbnail((1024, 1024))

        prompt = "Extract and write down all readable text inside this image clearly. Return ONLY the extracted text."
        
        res = client.models.generate_content(
            model=MODEL_NAME,
            contents=[img, prompt]
        )

        extracted_text = res.text.strip() if res.text else ""
        if extracted_text:
            await message.reply(extracted_text)
        else:
            await message.reply("Failed")
    except Exception:
        await message.reply("Failed")
    finally:
        if os.path.exists(photo_path):
            os.remove(photo_path)


# 14. تحويل الصوت إلى نص /stt
@dp.message(Command("stt"))
@dp.message(F.voice | F.audio)
async def cmd_stt(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return

    voice = message.voice or message.audio
    if not voice and message.reply_to_message:
        if message.reply_to_message.voice:
            voice = message.reply_to_message.voice
        elif message.reply_to_message.audio:
            voice = message.reply_to_message.audio

    if not voice:
        await message.reply("Failed")
        return

    audio_path = f"voice_{message.message_id}.ogg"

    try:
        file = await bot.get_file(voice.file_id)
        await bot.download_file(file.file_path, audio_path)

        audio_file_ref = client.files.upload(file=audio_path)
        
        prompt = "Transcribe this audio file accurately. Return ONLY the transcribed text."
        res = client.models.generate_content(
            model=MODEL_NAME,
            contents=[audio_file_ref, prompt]
        )

        transcript = res.text.strip() if res.text else ""
        if transcript:
            await message.reply(transcript)
        else:
            await message.reply("Failed")
            
        client.files.delete(name=audio_file_ref.name)
    except Exception:
        await message.reply("Failed")
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)


# تشغيل البوت
async def main():
    print("Bot is running...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
