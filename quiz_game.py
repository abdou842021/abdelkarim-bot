import random
import asyncio
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

class QuizStates(StatesGroup):
    waiting_for_words = State()
    waiting_for_count = State()
    waiting_for_timer = State()
    ready_to_start = State()

router = Router()
quiz_sessions = {}

@router.message(Command("quiz"))
async def cmd_quiz(message: Message, state: FSMContext):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # التحقق مما إذا كان المستخدم هو مشرف أو مالك المجموعة (أو محادثة خاصة)
    if message.chat.type in ["group", "supergroup"]:
        member = await message.bot.get_chat_member(chat_id, user_id)
        if member.status not in ["creator", "administrator"]:
            await message.answer("⚠️ Oh, adorable visitor! Only the glorious group owner or administrators have the majestic privilege to launch this magnificent quiz challenge.")
            return

    quiz_sessions[chat_id] = {"host": user_id}
    
    await message.answer(
        "🤖 Welcome to the ultimate English challenge for 'Abd al-Karim' bot!\n\n"
        "Send your list of new words right now (each word on a new line) so I can craft wonderful questions for you:"
    )
    await state.set_state(QuizStates.waiting_for_words)

@router.message(QuizStates.waiting_for_words)
async def process_words(message: Message, state: FSMContext):
    chat_id = message.chat.id
    words = [w.strip() for w in message.text.split('\n') if w.strip()]
    
    if len(words) < 2:
        await message.answer("⚠️ Please send at least two wonderful words so I can build the quiz!")
        return

    quiz_sessions[chat_id]["words"] = words
    await message.answer(f"✨ Magnificent! I have received {len(words)} stellar words.\n\nHow many questions would you like to conquer in this quiz? (Just send a number, like 5 or 10):")
    await state.set_state(QuizStates.waiting_for_count)

@router.message(QuizStates.waiting_for_count)
async def process_count(message: Message, state: FSMContext):
    chat_id = message.chat.id
    try:
        count = int(message.text.strip())
        max_w = len(quiz_sessions[chat_id]["words"])
        if count > max_w:
            count = max_w
        quiz_sessions[chat_id]["count"] = count
    except ValueError:
        await message.answer("⚠️ Oops! Please send a valid numeric value.")
        return

    await message.answer(
        "⏱️ Choose your adorable timer duration for each question in seconds:\n"
        "Type only one of these numbers: **10**, **15**, or **20**"
    )
    await state.set_state(QuizStates.waiting_for_timer)

@router.message(QuizStates.waiting_for_timer)
async def process_timer(message: Message, state: FSMContext):
    chat_id = message.chat.id
    text = message.text.strip()
    
    if text not in ["10", "15", "20"]:
        await message.answer("⚠️ Please choose a valid timer choice: exactly 10, 15, or 20 seconds.")
        return

    quiz_sessions[chat_id]["timer"] = int(text)
    
    await message.answer(
        f"🎯 **Your perfect quiz is fully prepared!**\n"
        f"- Total Questions: {quiz_sessions[chat_id]['count']}\n"
        f"- Question Timer: {quiz_sessions[chat_id]['timer']} seconds\n\n"
        f"Type **بدء الاختبار** right now to start the game!"
    )
    await state.set_state(QuizStates.ready_to_start)

@router.message(QuizStates.ready_to_start, F.text == "بدء الاختبار")
async def start_game_execution(message: Message, state: FSMContext):
    chat_id = message.chat.id
    session = quiz_sessions.get(chat_id)
    
    if not session:
        await message.answer("⚠️ No active session found. Please launch it using /quiz")
        await state.clear()
        return

    words = session["words"]
    count = session["count"]
    timer = session["timer"]

    selected = random.sample(words, min(count, len(words)))

    await message.answer("🚀 **The game is on! Get ready for absolute brilliance...**")
    await asyncio.sleep(2)

    for i, target in enumerate(selected, 1):
        wrongs = [w for w in words if w != target]
        distractors = random.sample(wrongs, min(3, len(wrongs)))
        options = distractors + [target]
        random.shuffle(options)
        correct_idx = options.index(target)

        await message.bot.send_poll(
            chat_id=chat_id,
            question=f"Question {i}: What is the marvelous meaning for '{target}'?",
            options=options,
            type="quiz",
            correct_option_id=correct_idx,
            is_anonymous=False,
            open_period=timer
        )
        
        await asyncio.sleep(timer + 2)

    await message.answer(
        "🏁 **The brilliant challenge has concluded!**\n\n"
        "🏆 **The Glorious Leaderboard & Rankings:**\n\n"
        "🥇 **1st Place:** Absolutely wonderful! You are a phenomenal linguistic genius, a true masterpiece of performance!\n"
        "🥈 **2nd Place:** Marvelous work! Adorable effort, you were exceptionally close to absolute perfection!\n"
        "🥉 **3rd Place:** Splendid job! A truly fantastic display of dedication!\n\n"
        "💡 *To the rest of the adorable players: Please review your marvelous lessons and shine brighter next time! You are completely unstoppable!*"
    )
    
    await state.clear()
    if chat_id in quiz_sessions:
        del quiz_sessions[chat_id]

def register_quiz_handler(dp):
    dp.include_router(router)

