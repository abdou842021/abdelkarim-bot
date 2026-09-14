import json
import random

from google import genai

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)

import config

router = Router()


# Store active quizzes
active_quizzes = {}


def get_gemini_client():
    if not config.GEMINI_API_KEY:
        return None

    return genai.Client(
        api_key=config.GEMINI_API_KEY
    )


# =========================================================
# /quiz
# =========================================================

@router.message(Command("quiz"))
async def quiz_command(message: Message):
    client = get_gemini_client()

    if client is None:
        await message.reply(
            "❌ Gemini API is not configured."
        )
        return

    prompt = """
Create ONE English vocabulary multiple-choice question.

Return ONLY valid JSON in this exact format:

{
  "question": "What does 'brave' mean?",
  "options": [
    "Afraid",
    "Courageous",
    "Lazy",
    "Angry"
  ],
  "answer": 1,
  "explanation": "Brave means having courage."
}

Rules:
- The question must be suitable for an English learner.
- Use exactly 4 options.
- "answer" must be the zero-based index of the correct option.
- Only one option can be correct.
- Keep the vocabulary around A2-B1 level.
- Do not use inappropriate content.
- Return JSON only.
"""

    try:
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt,
        )

        text = response.text.strip()

        # Remove possible markdown fences
        if text.startswith("```"):
            text = text.replace("```json", "")
            text = text.replace("```", "")
            text = text.strip()

        quiz = json.loads(text)

        question = quiz["question"]
        options = quiz["options"]
        answer = int(quiz["answer"])
        explanation = quiz.get(
            "explanation",
            ""
        )

        if len(options) != 4:
            raise ValueError(
                "Quiz must have exactly 4 options."
            )

        if answer not in range(4):
            raise ValueError(
                "Invalid answer index."
            )

        quiz_id = str(
            random.randint(
                100000,
                999999
            )
        )

        active_quizzes[quiz_id] = {
            "answer": answer,
            "explanation": explanation,
            "user_id": message.from_user.id,
        }

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"A. {options[0]}",
                        callback_data=f"quiz:{quiz_id}:0",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=f"B. {options[1]}",
                        callback_data=f"quiz:{quiz_id}:1",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=f"C. {options[2]}",
                        callback_data=f"quiz:{quiz_id}:2",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=f"D. {options[3]}",
                        callback_data=f"quiz:{quiz_id}:3",
                    )
                ],
            ]
        )

        await message.reply(
            "🧠 <b>English Quiz</b>\n\n"
            f"❓ {question}\n\n"
            "Choose the correct answer:",
            parse_mode="HTML",
            reply_markup=keyboard,
        )

    except Exception as error:
        print(f"Quiz error: {error}")

        await message.reply(
            "❌ I couldn't create the quiz right now. "
            "Please try again."
        )


# =========================================================
# Quiz answer
# =========================================================

@router.callback_query(
    F.data.startswith("quiz:")
)
async def quiz_answer(callback: CallbackQuery):
    try:
        _, quiz_id, selected = (
            callback.data.split(":")
        )

        selected = int(selected)

        quiz = active_quizzes.get(quiz_id)

        if not quiz:
            await callback.answer(
                "⏳ This quiz has expired.",
                show_alert=True,
            )
            return

        # Only the person who started the quiz
        # can answer it.
        if callback.from_user.id != quiz["user_id"]:
            await callback.answer(
                "⛔ This quiz belongs to another user.",
                show_alert=True,
            )
            return

        correct_answer = quiz["answer"]

        if selected == correct_answer:
            result = (
                "🎉 <b>Correct!</b>\n\n"
                f"💡 {quiz['explanation']}"
            )

        else:
            letters = ["A", "B", "C", "D"]

            result = (
                "❌ <b>Wrong answer.</b>\n\n"
                f"✅ Correct answer: "
                f"{letters[correct_answer]}\n\n"
                f"💡 {quiz['explanation']}"
            )

        # Delete quiz so it cannot be answered twice.
        del active_quizzes[quiz_id]

        await callback.message.edit_text(
            callback.message.text
            + "\n\n"
            + result,
            parse_mode="HTML",
        )

        await callback.answer()

    except Exception as error:
        print(f"Quiz callback error: {error}")

        await callback.answer(
            "❌ Something went wrong.",
            show_alert=True,
  )
