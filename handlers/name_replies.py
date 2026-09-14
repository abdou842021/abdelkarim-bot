import random

from aiogram import Router, F
from aiogram.types import Message

import config

router = Router()


@router.message(F.text)
async def name_trigger_handler(message: Message):
    text = message.text.lower().strip()

    # Ignore commands
    if text.startswith("/"):
        return

    # Check if one of the bot's name triggers appears
    for trigger in config.NAME_TRIGGERS:
        if trigger.lower() in text:
            reply = random.choice(
                config.NAME_REPLIES
            )

            await message.reply(reply)
            break
