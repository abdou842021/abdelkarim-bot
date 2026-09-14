import asyncio
import datetime
import os
import random
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
from google import genai
from PIL import Image

import config
from quiz_game import register_quiz_handler

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-2.5-flash"

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

register_quiz_handler(dp)


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
        await message.reply("Failed: Text is empty.")
        return

    words = text.split()
    if len(words) > config.MAX_WORDS:
        await message.reply("Failed: Text exceeds max words.")
        return

    output_audio = f"tts_{message.message_id}.mp3"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_audio)

    flag = "🇺🇸" if is_us else "🇬🇧"
    caption = f"{flag} {text}"

    # تم توسيع نطاق جلب الفونتيك ليشمل حتى 10 كلمات لضمان ظهوره بشكل متكرر
    if len(words) <= 10:
        accent_type = "American" if is_us else "British"
        prompt = (
            f"Provide ONLY the {accent_type} English IPA phonetic transcription "
            f"for this text enclosed in standard brackets like [phonetic], with no markdown or extra text: '{text}'"
        )
        try:
            res = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )
            phonetic = res.text.strip().replace("```", "").strip()
            if phonetic:
                if not phonetic.startswith("["):
                    phonetic = f"[{phonetic}"
                if not phonetic.endswith("]"):
                    phonetic = f"{phonetic}]"
                caption += f"\n🗣 {phonetic}"
        except Exception as e:
            print(f"TTS Phonetic Error: {e}")

    audio_file = FSInputFile(output_audio)
    await message.reply_audio(audio=audio_file, caption=caption)

    if os.path.exists(output_audio):
        os.remove(output_audio)


@dp.message(F.text & ~F.text.startswith("/"))
async def check_name_mention(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    
    text = message.text.lower()
    names = ["عبد الكريم", "abdelkarim", "abdulkarim", "karim", "abdelkrim", "كريم"]
    
    if any(name in text for name in names):
        responses = [
            "✨ May success follow you everywhere, and may all your dreams come true!",
            "🌟 Wishing you a wonderful day filled with peace, joy, and endless blessings!",
            "🤲 May your hard work lead you to great achievements and bright victories!",
            "💎 Sending you prayers for happiness, prosperity, and a brilliant future!",
            "🙏 May Allah bless your path and open all doors of opportunity for you!",
            "🚀 Wishing you continuous growth, good health, and immense success!",
            "🌟 May your life be filled with wonderful moments and remarkable triumphs!",
            "✨ Hoping your journey is smooth and your ambitions turn into reality!",
            "🌿 May every single step you take bring you closer to your ultimate goals.",
            "☀️ Wishing you strength, clarity, and boundless energy to conquer your day.",
            "💫 May your heart find peace and your mind find brilliant inspiration today.",
            "🍀 May fortune favor you and bring you wonderful surprises around every corner.",
            "🕊️ Sending you positive vibes, calm energy, and deep heartfelt prayers.",
            "⭐ May your dedication shine bright and inspire everyone around you.",
            "🌊 May your path be clear, your burdens light, and your horizon completely bright."
        ]
        await message.reply(random.choice(responses))


async def time_greetings_loop(bot: Bot):
    algeria_tz = datetime.timezone(datetime.timedelta(hours=1))
    last_morning_sent = None
    last_night_sent = None
    
    while True:
        now = datetime.datetime.now(algeria_tz)
        current_date = now.date()
        current_hour = now.hour
        current_minute = now.minute
        
        if current_hour == 8 and current_minute == 0 and last_morning_sent != current_date:
            morning_texts = [
                "☀️ Good morning everyone! May this beautiful new day bring boundless energy, brilliant opportunities, and remarkable success to your lives. May all your hard work be richly rewarded, and may your hearts be filled with peace, positivity, and unwavering motivation throughout the entire day. Have a wonderfully blessed morning! ☕✨",
                "🌅 Wishing you all a truly magnificent and radiant good morning! May the sun shine brightly on your paths, illuminating every goal and ambition you strive for today. Embrace every single moment with enthusiasm, confidence, and a grateful heart, knowing great things are destined for you. Stay inspired and keep shining! 💛"
            ]
            text = random.choice(morning_texts)
            for gid in list(config.ALLOWED_GROUP_IDS):
                try:
                    await bot.send_message(gid, text)
                except Exception:
                    pass
            last_morning_sent = current_date
        
        if current_hour == 1 and current_minute == 0 and last_night_sent != current_date:
            night_texts = [
                "🌙 Good night everyone! As the quiet hours settle in, it is time to gently lay down the day's worries and rest your mind and body. May you be blessed with deeply peaceful sleep, comforting dreams, and total restoration, waking up tomorrow ready to conquer new heights. Sweet dreams and sleep tight! ✨💤",
                "🌌 Wishing you all a wonderfully calm and restful night! May the gentle embrace of sleep wash away all fatigue and bring tranquility to your spirit. Rest well, recharge your energy, and look forward to a brighter, more successful tomorrow. Good night and sweet dreams to you all! 💫😴"
            ]
            text = random.choice(night_texts)
            for gid in list(config.ALLOWED_GROUP_IDS):
                try:
                    await bot.send_message(gid, text)
                except Exception:
                    pass
            last_night_sent = current_date
        
        await asyncio.sleep(60)


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


@dp.message(Command("start"))
@dp.message(Command("help"))
async def cmd_start(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    WELCOME_MESSAGE = (
        "Welcome to Abd al-Karim Bot for learning English! 🇩🇿🇬🇧🇺🇸\n\n"
        "✨ **Available Commands:**\n"
        "• `/sus` + Text : American Pronunciation & IPA 🇺🇸\n"
        "• `/suk` + Text : British Pronunciation & IPA 🇬🇧\n"
        "• `/trab` + Text : Translate to Arabic 🇩🇿\n"
        "• `/treng` + Text : Translate to English 🇬🇧\n"
        "• `/syn` + Word : Synonyms, Antonyms & Example ⚡\n"
        "• `/cor` + Text : Grammar & Spelling Correction ✏️\n"
        "• `/exp` + Word : Detailed Word Explanation & Forms 📚\n"
        "• `/txt` (reply to an image) : Extract text from images 📝\n"
        "• `/stt` (reply to a voice) : Convert voice to text 🎙"
    )
    await message.reply(WELCOME_MESSAGE, parse_mode="Markdown")


@dp.message(Command("suk"))
async def cmd_suk(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    text = await get_text_from_msg(
        message, message.text.replace("/suk", "").strip()
    )
    await process_tts(message, text, config.VOICE_BRITISH, is_us=False)


@dp.message(Command("sus"))
async def cmd_sus(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    text = await get_text_from_msg(
        message, message.text.replace("/sus", "").strip()
    )
    await process_tts(message, text, config.VOICE_AMERICAN, is_us=True)


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
        Provide information for the word or phrase: '{text}'.
        You MUST provide:
        1. Meaning (المعنى بالعربية)
        2. Synonyms (المرادفات: 2-3 words)
        3. Antonyms (الأضداد: 2-3 words)
        4. Short example sentence with translation (مثال قصير مع الترجمة)
        Keep it concise, clear, and well-structured using markdown.
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
        if translated:
            await message.reply(translated)
        else:
            await message.reply("Failed")
    except Exception:
        await message.reply("Failed")


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
        if translated:
            await message.reply(translated)
        else:
            await message.reply("Failed")
    except Exception:
        await message.reply("Failed")


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


async def main():
    print("Bot is running...")
    asyncio.create_task(time_greetings_loop(bot))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
