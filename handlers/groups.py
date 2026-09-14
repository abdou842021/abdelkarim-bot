from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

import config

router = Router()


def is_owner(message: Message) -> bool:
    return message.from_user.id == config.OWNER_ID


def is_group(message: Message) -> bool:
    return message.chat.type in {
        "group",
        "supergroup",
    }


def is_allowed_group(message: Message) -> bool:
    return (
        message.chat.id in config.ALLOWED_GROUP_IDS
    )


# =========================================================
# /groups
# Owner only
# =========================================================

@router.message(Command("groups"))
async def groups_command(message: Message):
    if not is_owner(message):
        await message.reply(
            "⛔ This command is for the bot owner only."
        )
        return

    if not config.ALLOWED_GROUP_IDS:
        await message.reply(
            "👥 No groups are activated."
        )
        return

    text = "👥 <b>Activated Groups</b>\n\n"

    for group_id in config.ALLOWED_GROUP_IDS:
        text += f"• <code>{group_id}</code>\n"

    await message.reply(
        text,
        parse_mode="HTML",
    )


# =========================================================
# New group activation request
# =========================================================

@router.my_chat_member()
async def bot_added_to_group(event):
    new_status = event.new_chat_member.status
    old_status = event.old_chat_member.status

    if new_status not in {
        "member",
        "administrator",
    }:
        return

    if old_status in {
        "member",
        "administrator",
    }:
        return

    chat = event.chat

    if chat.type not in {
        "group",
        "supergroup",
    }:
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Allow",
                    callback_data=f"group_allow:{chat.id}",
                ),
                InlineKeyboardButton(
                    text="❌ Deny",
                    callback_data=f"group_deny:{chat.id}",
                ),
            ]
        ]
    )

    try:
        await event.bot.send_message(
            config.OWNER_ID,
            (
                "👥 <b>New Group Request</b>\n\n"
                f"Name: {chat.title}\n"
                f"ID: <code>{chat.id}</code>\n\n"
                "Do you want to activate this group?"
            ),
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    except Exception:
        pass


# =========================================================
# Allow group
# =========================================================

@router.callback_query(
    F.data.startswith("group_allow:")
)
async def allow_group(callback: CallbackQuery):
    if callback.from_user.id != config.OWNER_ID:
        await callback.answer(
            "⛔ Owner only.",
            show_alert=True,
        )
        return

    group_id = int(
        callback.data.split(":", 1)[1]
    )

    config.ALLOWED_GROUP_IDS.add(group_id)

    await callback.message.edit_text(
        "✅ <b>Group activated.</b>\n\n"
        f"ID: <code>{group_id}</code>",
        parse_mode="HTML",
    )

    await callback.answer(
        "Group activated."
    )


# =========================================================
# Deny group
# =========================================================

@router.callback_query(
    F.data.startswith("group_deny:")
)
async def deny_group(callback: CallbackQuery):
    if callback.from_user.id != config.OWNER_ID:
        await callback.answer(
            "⛔ Owner only.",
            show_alert=True,
        )
        return

    group_id = int(
        callback.data.split(":", 1)[1]
    )

    config.ALLOWED_GROUP_IDS.discard(group_id)

    await callback.message.edit_text(
        "❌ <b>Group rejected.</b>\n\n"
        f"ID: <code>{group_id}</code>",
        parse_mode="HTML",
    )

    await callback.answer(
        "Group rejected."
  )
