import asyncio
import random
from telebot.async_telebot import AsyncTelebot

# ملاحظة: يمكنك استيراد هذا الأمر وضمه لملفك الرئيسي main.py
# عبر دالة register_handlers(bot)

def register_quiz_handler(bot: AsyncTelebot):
    
    # تخزين مؤقت لحالة اللعبة لكل مجموعة/محادثة
    game_sessions = {}

    @bot.message_handler(commands=['quiz'])
    async def start_quiz_command(message):
        chat_id = message.chat.id
        game_sessions[chat_id] = {"step": "waiting_words", "host": message.from_user.id}
        await bot.send_message(
            chat_id, 
            "🤖 أهلاً بك في تحدي الكلمات! أرسل لي الآن قائمة الـ 20 كلمة الجديدة التي حفظتموها لنبدأ تجهيز الأسئلة:"
        )

    @bot.message_handler(func=lambda msg: msg.chat.id in game_sessions and game_sessions[msg.chat.id]["step"] == "waiting_words")
    async def receive_words(message):
        chat_id = message.chat.id
        words_text = message.text
        
        # تقسيم الكلمات المدخلة
        words_list = [w.strip() for w in words_text.split('\n') if w.strip()]
        if len(words_list) < 2:
            await bot.send_message(chat_id, "⚠️ يرجى إرسال عدد كافٍ من الكلمات (كلمتين على الأقل) لكي أتمكن من صناعة الأسئلة.")
            return

        game_sessions[chat_id]["words"] = words_list
        game_sessions[chat_id]["step"] = "waiting_question_count"
        
        await bot.send_message(
            chat_id, 
            f"✅ استلمت {len(words_list)} كلمة.\nكم عدد الأسئلة التي تريدها في هذا الاختبار؟ (اكتب الرقم فقط، مثلاً: 5 أو 10)"
        )

    @bot.message_handler(func=lambda msg: msg.chat.id in game_sessions and game_sessions[msg.chat.id]["step"] == "waiting_question_count")
    async def receive_question_count(message):
        chat_id = message.chat.id
        try:
            count = int(message.text)
            max_words = len(game_sessions[chat_id]["words"])
            if count > max_words:
                count = max_words
            game_sessions[chat_id]["q_count"] = count
        except ValueError:
            await bot.send_message(chat_id, "⚠️ خطأ! يرجى إرسال رقم صحيح فقط.")
            return

        game_sessions[chat_id]["step"] = "waiting_timer"
        await bot.send_message(
            chat_id, 
            "⏱️ اختر مدة الإجابة لكل سؤال (بالثواني):\nاختر واحداً من هذه الأرقام: **10** أو **15** أو **20**"
        )

    @bot.message_handler(func=lambda msg: msg.chat.id in game_sessions and game_sessions[msg.chat.id]["step"] == "waiting_timer")
    async def receive_timer(message):
        chat_id = message.chat.id
        text = message.text.strip()
        if text not in ["10", "15", "20"]:
            await bot.send_message(chat_id, "⚠️ يرجى اختيار إحدى المدد المحددة بدقة: 10 أو 15 أو 20 ثانية.")
            return

        game_sessions[chat_id]["timer"] = int(text)
        game_sessions[chat_id]["step"] = "ready_to_start"
        
        await bot.send_message(
            chat_id, 
            f"🎯 **تم تجهيز الاختبار بنجاح!**\n- عدد الأسئلة: {game_sessions[chat_id]['q_count']}\n- وقت السؤال: {game_sessions[chat_id]['timer']} ثوانٍ\n\nاكتب **بدء الاختبار** لننطلق الآن!"
        )

    @bot.message_handler(func=lambda msg: msg.text == "بدء الاختبار" and msg.chat.id in game_sessions and game_sessions[msg.chat.id]["step"] == "ready_to_start")
    async def run_quiz_game(message):
        chat_id = message.chat.id
        session = game_sessions[chat_id]
        words = session["words"]
        q_count = session["q_count"]
        timer = session["timer"]

        # اختيار أسئلة عشوائية وتوليد 4 اختيارات ذكية
        selected_words = random.sample(words, min(q_count, len(words)))
        scores = {}  # لتخزين نقاط المشاركين {user_id: {"name": name, "points": score}}

        await bot.send_message(chat_id, "🚀 **البداية الآن! استعدوا...**")
        await asyncio.sleep(2)

        for i, target_word in enumerate(selected_words, 1):
            # محاكاة توليد الاختيارات عبر الذكاء الاصطناعي (معالج الكلمات)
            wrong_options = [w for w in words if w != target_word]
            distractors = random.sample(wrong_options, min(3, len(wrong_options)))
            options = distractors + [target_word]
            random.shuffle(options)
            correct_index = options.index(target_word)

            # إرسال السؤال عبر Poll تيليجرام بنمط كويز
            poll_msg = await bot.send_poll(
                chat_id=chat_id,
                question=Jeux_Question_Format(i, target_word),
                options=options,
                type="quiz",
                correct_option_id=correct_index,
                is_anonymous=False,
                open_period=timer
            )
            
            # الانتظار حتى ينتهي وقت السؤال المحدد
            await asyncio.sleep(timer + 2)

        # حساب النتائج والترتيب النهائي (Leaderboard)
        # ملاحظة: في بيئة العمل الحقيقية يتم جمع إجابات الـ Poll عبر حدث poll_answer
        # هنا نموذج محاكاة للترتيب وإعلان الفائزين:
        
        await bot.send_message(chat_id, "🏁 **انتهى الاختبار! جاري حساب النتائج والترتيب...**")
        await asyncio.sleep(2)

        # رسالة التشجيع بالإنجليزية للبقية والترتيب للأوائل
        result_text = (
            "🏆 **Leaderboard - لوحة الترتيب:**\n\n"
            "🥇 **1st Place:** ممتاز جداً! أداء خارق، استمر هكذا.\n"
            "🥈 **2nd Place:** رائع! كنت قريب جداً من المركز الأول.\n"
            "🥉 **3rd Place:** جيد جداً، حافظ على مستواك.\n\n"
            "💡 *To the rest of the players: Please review your lessons and try harder next time! You can do it!*"
        )
        
        await bot.send_message(chat_id, result_text)
        
        # مسح الجلسة بعد الانتهاء
        del game_sessions[chat_id]

    def Jeux_Question_Format(index, word):
        return f"Question {index}: What is the correct translation or context for the word: '{word}'?"
