import random

from aiogram import Router
from aiogram.types import Message

import config

router = Router()


# =========================================================
# New member welcome
# =========================================================

@router.message()
async def welcome_new_member(message: Message):
    if not message.new_chat_members:
        return

    if message.chat.type not in {
        "group",
        "supergroup",
    }:
        return

    for member in message.new_chat_members:
        # Don't welcome the bot itself
        if member.is_bot:
            continue

        name = member.first_name or "there"

        await message.reply(
            f"👋 Welcome, {name}!\n\n"
            f"{config.WELCOME_NEW_MEMBER}"
        )


# =========================================================
# Bot added to a group
# =========================================================

@router.message()
async def bot_added_message(message: Message):
    if not message.new_chat_members:
        return

    me = await message.bot.me()

    for member in message.new_chat_members:
        if member.id == me.id:
            await message.reply(
                "🤖 Thank you for adding Abdelkarim "
                "English Learning Bot! 🇬🇧\n\n"
                "Please wait for the owner to activate "
                "this group."
            )
            break
