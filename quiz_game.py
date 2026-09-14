        import random
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from google import genai
import os

class QuizStates(StatesGroup):
    waiting_for_words = State()
    waiting_for_count = State()
    waiting_for_timer = State()
    playing = State()

router = Router()
quiz_sessions = {}

# تهيئة عميل Gemini داخل الكويز لإنتاج أسئلة ذكية وخيارات دقيقة
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-3.6-flash"

@router.message(Command("quiz"))
async def cmd_quiz(message: Message, state: FSMContext):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if message.chat.type in ["group", "supergroup"]:
        member = await message.bot.get_chat_member(chat_id, user_id)
        if member.status not in ["creator", "administrator"]:
            await message.answer("⚠️ Oh, adorable visitor! Only the glorious group owner or administrators have the majestic privilege to launch this magnificent quiz challenge.")
            return

    quiz_sessions[chat_id] = {"host": user_id, "scores": {}}
    
    await message.answer(
        "🤖 Welcome to the ultimate AI-powered English challenge for 'Abd al-Karim' bot!\n\n"
        "Send your list of words right now (each word on a new line) so Gemini can craft wonderful smart questions for you:"
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
    await message.answer(f"✨ Magnificent! I have received {len(words)} stellar words.\n\nHow many questions would you like to conquer in this quiz? (Just send a number, like 3, 5 or 10):")
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
        f"🎯 **Your perfect AI quiz is fully prepared!**\n"
        f"- Total Questions: {quiz_sessions[chat_id]['count']}\n"
        f"- Question Timer: {quiz_sessions[chat_id]['timer']} seconds\n\n"
        f"Type **بدء الاختبار** right now to start the game!"
    )
    await state.set_state(QuizStates.playing)

@router.message(QuizStates.playing, F.text == "بدء الاختبار")
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

    selected_words = random.sample(words, min(count, len(words)))

    await message.answer("🚀 **The game is on! Gemini is generating smart questions...**")
    await asyncio.sleep(1)

    for i, target_word in enumerate(selected_words, 1):
        # توليد سؤال ذكي وخيارات دقيقة عبر Gemini AI
        prompt = f"""
        For the English word '{target_word}', generate:
        1. A short, clear question or definition in English testing its meaning.
        2. 4 multiple-choice options (1 correct meaning, 3 wrong but plausible meanings).
        Format strictly as:
        QUESTION: [The question here]
        CORRECT: [The correct option]
        WRONG1: [Wrong option 1]
        WRONG2: [Wrong option 2]
        WRONG3: [Wrong option 3]
        """
        try:
            res = client.models.generate_content(model=MODEL_NAME, contents=prompt)
            lines = res.text.strip().split('\n')
            q_text, correct_opt, wrongs = "", "", []
            for line in lines:
                if line.startswith("QUESTION:"): q_text = line.replace("QUESTION:", "").strip()
                elif line.startswith("CORRECT:"): correct_opt = line.replace("CORRECT:", "").strip()
                elif line.startswith("WRONG"): wrongs.append(line.split(":", 1)[1].strip())
            
            if not q_text or not correct_opt:
                q_text = f"What is the marvelous meaning of '{target_word}'?"
                correct_opt = target_word
                wrongs = ["Wrong option A", "Wrong option B", "Wrong option C"]

            options = wrongs + [correct_opt]
            random.shuffle(options)

            # تجهيز الأزرار التفاعلية لتتبع من أجاب بأسماء حسابات تليجرام الحقيقية
            keyboard_buttons = []
            for opt in options:
                # نحفظ الإجابة في الـ callback_data بطريقة ذكية
                is_correct_flag = "1" if opt == correct_opt else "0"
                keyboard_buttons.append([InlineKeyboardButton(text=opt, callback_data=f"qans_{is_correct_flag}")])
            
            markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

            q_msg = await message.bot.send_message(
                chat_id=chat_id,
                text=f"✨ **Question {i}/{count}**\n\n{q_text}\n\n⏱️ *You have {timer} seconds!*",
                reply_markup=markup,
                parse_mode="Markdown"
            )

            # انتظار انتهاء الوقت للسؤال الحالي
            await asyncio.sleep(timer)

            # تعطيل الأزرار بعد انتهاء الوقت
            try:
                await q_msg.edit_text(
                    text=f"🔒 **Question {i} Closed!**\n\n{q_text}\n\n✅ *Correct Answer was:* **{correct_opt}**",
                    reply_markup=None,
                    parse_mode="Markdown"
                )
            except Exception:
                pass

        except Exception as e:
            await message.answer(f"⚠️ Error generating question: {e}")
            continue

    # حساب وتصدير لوحة الصدارة بأسماء اللاعبين الحقيقية
    scores = session["scores"]
    if scores:
        sorted_players = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        leaderboard_text = ""
        medals = ["🥇", "🥈", "🥉"]
        for idx, (p_name, score) in enumerate(sorted_players[:3]):
            medal = medals[idx] if idx < 3 else "🎖️"
            leaderboard_text += f"{medal} **{p_name}**: {score} points - *Phenomenal achievement!*\n"
    else:
        leaderboard_text = "💡 *No players scored points this time, but the effort was adorable!*"

    await message.answer(
        f"🏁 **The brilliant challenge has concluded!**\n\n"
        f"🏆 **The Glorious Leaderboard & Rankings:**\n\n"
        f"{leaderboard_text}\n\n"
        f"🌟 *To all adorable participants: You are completely unstoppable! Keep shining!*"
    )
    
    await state.clear()
    if chat_id in quiz_sessions:
        del quiz_sessions[chat_id]

# معالجة ضغط الأزرار وتسجيل النقاط بأسماء اللاعبين
@router.callback_query(F.data.startswith("qans_"))
async def handle_quiz_answer(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    user_name = callback.from_user.full_name
    is_correct = callback.data.split("_")[1] == "1"

    if chat_id in quiz_sessions:
        scores = quiz_sessions[chat_id]["scores"]
        if user_name not in scores:
            scores[user_name] = 0
        
        if is_correct:
            scores[user_name] += 1
            await callback.answer("✨ Magnificent! Correct choice, brilliant genius!", show_alert=False)
        else:
            await callback.answer("❌ Adorable try, but incorrect! Keep your head up!", show_alert=False)
    else:
        await callback.answer("⚠️ This quiz session has already expired.", show_alert=True)

def register_quiz_handler(dp):
    dp.include_router(router)


