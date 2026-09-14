import asyncio
import datetime
import os
import random
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
import config
from quiz_game import register_quiz_handler
from handlers import commands, tts_handler, ai_tools

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

# تسجيل ألعاب الكويز وربط الرواترز للملفات المقسمة
register_quiz_handler(dp)
dp.include_router(commands.router)
dp.include_router(tts_handler.router)
dp.include_router(ai_tools.router)


def is_allowed(chat_id: int, user_id: int) -> bool:
    if chat_id > 0:
        return True
    return chat_id in config.ALLOWED_GROUP_IDS or user_id == config.OWNER_ID


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


async def main():
    print("Bot is running cleanly...")
    asyncio.create_task(time_greetings_loop(bot))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
