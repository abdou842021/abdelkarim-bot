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

# استيراد المكتبة الرسمية الجديدة لـ Gemini
from google import genai
from PIL import Image

# استدعاء ملف الإعدادات
import config
from quiz_game import register_quiz_handler

# تهيئة عميل Gemini الجديد
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-3.6-flash"


bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()


register_quiz_handler(dp)

# ====================== الفلاتر والمساعدات ======================
def is_allowed(chat_id: int, user_id: int) -> bool:
    if chat_id > 0:  # المحادثات الخاصة (Private) مسموحة دائماً
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

    # التعديل هنا: الفونتيك يظهر فقط إذا كانت 4 كلمات أو أقل وحسب اللهجة
    if len(words) <= 4:
        accent_type = "American" if is_us else "British"
        prompt = (
            f"Provide ONLY the {accent_type} English IPA phonetic transcription "
            f"for this text without any extra text or intro: '{text}'"
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
        await message.reply("📋 لا توجد مجموعات مفعلة حالياً.")
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


# 4. الترحيب بالحي والمسح التلقائي بعد 15 ثانية
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


# 5. أمر البدء والمساعدة /start
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
    "• `/txt` (reply to an image) : Extract text from images 📝"
)

    await message.reply(welcome_text, parse_mode="Markdown")


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

# أمر الحصول على مرادفات وأضداد وتصاريف سريعة /syn
@dp.message(Command("syn"))
async def cmd_syn(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    text = await get_text_from_msg(message, message.text.replace("/syn", "").strip())
    if not text:
        await message.reply("❌ اكتب كلمة أو رد عليها لاستخراج المرادفات والأضداد.")
        return

    msg = await message.reply("🔍 جاري الجلب...")
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
        await msg.edit_text(res.text.strip())
    except Exception as e:
        await msg.edit_text(f"❌ حدث خطأ: {e}")

# 8. تصحيح الكتابة والقواعد /cor
@dp.message(Command("cor"))
async def cmd_cor(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    text = await get_text_from_msg(message, message.text.replace("/cor", "").strip())
    if not text:
        await message.reply("❌ اكتب نصاً أو رد على رسالة لتصحيحها.")
        return

    msg = await message.reply("⏳ جاري التصحيح...")
    try:
        prompt = f"Correct the spelling and grammar of this text. Return ONLY the corrected version:\n\n{text}"
        res = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        await msg.edit_text(f"✏️ **التصحيح:**\n{res.text.strip()}")
    except Exception as e:
        await msg.edit_text(f"❌ حدث خطأ أثناء التصحيح: {e}")


# 9. الترجمة إلى العربية /trab (مع علم الجزائر)
@dp.message(Command("trab"))
async def cmd_trab(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    text = await get_text_from_msg(message, message.text.replace("/trab", "").strip())
    if not text:
        await message.reply("❌ اكتب نصاً أو رد على رسالة لترجمتها.")
        return
    
    msg = await message.reply("⏳ جاري الترجمة...")
    try:
        prompt = f"Translate this English text to Arabic naturally:\n{text}"
        res = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        await msg.edit_text(f"🇩🇿 **الترجمة:**\n{res.text.strip()}")
    except Exception as e:
        await msg.edit_text(f"❌ حدث خطأ في الترجمة: {e}")


# 10. الترجمة إلى الإنجليزية /treng
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from google import genai
import os

router = Router()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-3.6-flash"

@router.message(Command("trab"))
async def translate_to_arabic(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Failed")
        return
    
    query = parts[1].strip()
    prompt = f"Translate the following text strictly into Arabic. Provide ONLY the direct translation without any explanation, notes, or extra words: '{query}'"
    
    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        translated_text = response.text.strip()
        if not translated_text:
            await message.answer("Failed")
            return
        await message.answer(translated_text)
    except Exception:
        await message.answer("Failed")

@router.message(Command("treng"))
async def translate_to_english(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Failed")
        return
    
    query = parts[1].strip()
    prompt = f"Translate the following text strictly into English. Provide ONLY the direct translation without any explanation, notes, or extra words: '{query}'"
    
    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        translated_text = response.text.strip()
        if not translated_text:
            await message.answer("Failed")
            return
        await message.answer(translated_text)
    except Exception:
        await message.answer("Failed")

def register_translator_handler(dp):
    dp.include_router(router)



# 11. الشرح والتحليل اللغوي /exp
@dp.message(Command("exp"))
async def cmd_exp(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    text = await get_text_from_msg(message, message.text.replace("/exp", "").strip())
    if not text:
        await message.reply("❌ اكتب كلمة/جملة أو رد عليها لشرحها.")
        return

    msg = await message.reply("🔍 جاري التحليل والشرح...")
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
        await msg.edit_text(res.text.strip())
    except Exception as e:
        await msg.edit_text(f"❌ حدث خطأ في الشرح: {e}")


# 12. تحويل النص داخل الصورة إلى كتابة /txt (بالرد أو إرسال الصورة مباشرة)

# 12. تحويل النص داخل الصورة إلى كتابة /txt (مع تصغير الحجم لسرعة المعالجة)
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
        await message.reply("❌ يرجى الرد على صورة باستخدام الأمر `/txt` أو إرسال الصورة مكتوباً عليها `/txt`.")
        return

    status_msg = await message.reply("🔍 جاري قراءة النص من الصورة...")
    photo_path = f"img_{message.message_id}.jpg"

    try:
        file = await bot.get_file(photo.file_id)
        await bot.download_file(file.file_path, photo_path)

        # فتح الصورة وتصغير حجمها لضمان سرعة الاستجابة
        img = Image.open(photo_path)
        img.thumbnail((1024, 1024))

        prompt = "Extract and write down all readable text inside this image clearly. Return ONLY the extracted text."
        
        res = client.models.generate_content(
            model=MODEL_NAME,
            contents=[img, prompt]
        )

        extracted_text = res.text.strip() if res.text else "لم أستطع قراءة أي نص."
        await status_msg.edit_text(f"📝 **النص المستخرج:**\n\n{extracted_text}")
    except Exception as e:
        await status_msg.edit_text(f"❌ حدث خطأ أثناء قراءة الصورة: {e}")
    finally:
        if os.path.exists(photo_path):
            os.remove(photo_path)


# تشغيل البوت
async def main():
    print("Bot is running...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
