import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

import config


ALGERIA_TZ = ZoneInfo("Africa/Algiers")


MORNING_MESSAGES = [
    "🌅 Good morning everyone! May your day be peaceful and productive. 🇬🇧",
    "☀️ Good morning! Wishing you a beautiful day full of learning and success. 📚",
    "🌿 Good morning! May Allah bless your day with peace, goodness, and beneficial knowledge. 🤲",
    "🌞 A new day, a new opportunity to learn something useful. Good morning! 🇬🇧",
]


NIGHT_MESSAGES = [
    "🌙 Good night everyone. May Allah grant you peace and a restful night. 🤲",
    "🌃 Good night! May tomorrow bring you goodness, success, and beneficial knowledge. 🌿",
    "🌙 Time to rest. May Allah protect you and give you a peaceful night. 🤍",
    "✨ Good night everyone. Rest well and get ready for a new day of learning. 📚",
]


async def send_scheduled_message(bot, message_list):
    if not config.ALLOWED_GROUP_IDS:
        return

    for group_id in list(config.ALLOWED_GROUP_IDS):
        try:
            import random

            message = random.choice(message_list)

            await bot.send_message(
                chat_id=group_id,
                text=message,
            )

        except Exception as error:
            print(
                f"Could not send scheduled message "
                f"to {group_id}: {error}"
            )


async def scheduler_loop(bot):
    morning_sent = None
    night_sent = None

    while True:
        now = datetime.now(ALGERIA_TZ)

        # 08:00 Algeria time
        if (
            now.hour == 8
            and now.minute == 0
            and morning_sent != now.date()
        ):
            await send_scheduled_message(
                bot,
                MORNING_MESSAGES,
            )

            morning_sent = now.date()

        # 01:00 Algeria time
        if (
            now.hour == 1
            and now.minute == 0
            and night_sent != now.date()
        ):
            await send_scheduled_message(
                bot,
                NIGHT_MESSAGES,
            )

            night_sent = now.date()

        await asyncio.sleep(30)
