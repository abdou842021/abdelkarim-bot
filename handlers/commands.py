from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
import config

router = Router()

def is_allowed(chat_id: int, user_id: int) -> bool:
    if chat_id > 0:
        return True
    return chat_id in config.ALLOWED_GROUP_IDS or user_id == config.OWNER_ID

@router.message(Command("start", "help"))
async def cmd_start(message: Message):
    if not is_allowed(message.chat.id, message.from_user.id):
        return
    text = (
        "Welcome to Abd al-Karim Bot! 🇩🇿🇬🇧🇺🇸\n\n"
        "✨ **الأوامر المتاحة:**\n"
        "• `/sus` + النص : نطق أمريكي + الفونتيك 🇺🇸\n"
        "• `/suk` + النص : نطق بريطاني + الفونتيك 🇬🇧\n"
        "• `/trab` + النص : ترجمة إلى العربية 🇩🇿\n"
        "• `/treng` + النص : ترجمة إلى الإنجليزية 🇬🇧\n"
        "• `/cor` + النص : تصحيح القواعد والإملاء ✏️"
    )
    await message.reply(text, parse_mode="Markdown")

@router.message(Command("groups"))
async def list_groups(message: Message):
    if message.from_user.id != config.OWNER_ID:
        return
    if not config.ALLOWED_GROUP_IDS:
        await message.reply("لا توجد مجموعات مفعلة حالياً.")
        return
    text = "📋 **المجموعات المفعلة:**\n\n"
    for gid in config.ALLOWED_GROUP_IDS:
        text += f"• `{gid}`\n"
    await message.reply(text, parse_mode="Markdown")
