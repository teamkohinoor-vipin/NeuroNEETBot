import asyncio
import random
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Poll
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler
from bot.database.db import db

logger = logging.getLogger(__name__)

SUBJECT, CHAPTER, QUESTION_COUNT, TIMER = range(4)

chapter_quiz_sessions = {}


def format_time(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f} sec"
    mins = int(seconds // 60)
    secs = seconds % 60
    return f"{mins} min {secs:.0f} sec"


def build_chapter_keyboard(chapters, page=0, per_page=10):
    start = page * per_page
    end = start + per_page
    page_chapters = chapters[start:end]
    keyboard = []
    row = []
    for i, ch in enumerate(page_chapters, 1):
        row.append(InlineKeyboardButton(ch, callback_data=f"quiz_chapter_{ch}"))
        if i % 2 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"quiz_chap_page_{page-1}"))
    if end < len(chapters):
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"quiz_chap_page_{page+1}"))
    if nav:
        keyboard.append(nav)
    keyboard.append([InlineKeyboardButton("🔙 Back to Subjects", callback_data="quiz_back_subject")])
    return InlineKeyboardMarkup(keyboard)


async def get_chapters_by_subject(subject):
    chapters = await db.db.questions.distinct("chapter", {"subject": subject, "approved": True})
    return sorted(chapters)


async def get_random_questions(subject, chapter, limit=None):
    query = {"subject": subject, "chapter": chapter, "approved": True}
    cursor = db.db.questions.find(query)
    if limit:
        cursor = cursor.limit(limit)
    questions = await cursor.to_list(length=limit or 1000)
    random.shuffle(questions)
    return questions


async def start_quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    is_group = update.effective_chat.type != "private"

    if is_group:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status not in ["administrator", "creator"]:
            await update.message.reply_text("❌ Only group admins can start a quiz.")
            return ConversationHandler.END

    context.user_data.clear()
    context.user_data["is_group"] = is_group
    context.user_data["chat_id"] = chat_id
    context.user_data["user_id"] = user_id

    keyboard = [
        [InlineKeyboardButton("⚛️ Physics", callback_data="quiz_subject_Physics"),
         InlineKeyboardButton("🧪 Chemistry", callback_data="quiz_subject_Chemistry"),
         InlineKeyboardButton("🧬 Biology", callback_data="quiz_subject_Biology")],
        [InlineKeyboardButton("❌ Cancel", callback_data="quiz_cancel")]
    ]
    await update.message.reply_text("📚 *Select Subject for Quiz:*", parse_mode="Markdown",
                                    reply_markup=InlineKeyboardMarkup(keyboard))
    return SUBJECT


async def quiz_subject_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    subject = query.data.split("_")[2]
    context.user_data["quiz_subject"] = subject

    chapters = await get_chapters_by_subject(subject)
    if not chapters:
        await query.edit_message_text("❌ No chapters found for this subject.")
        return ConversationHandler.END
    context.user_data["quiz_chapters"] = chapters
    context.user_data["quiz_chapter_page"] = 0

    reply_markup = build_chapter_keyboard(chapters, page=0)
    await query.edit_message_text(f"📖 *Select Chapter for {subject}:*", parse_mode="Markdown",
                                  reply_markup=reply_markup)
    return CHAPTER


async def quiz_chapter_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    page = int(query.data.split("_")[-1])
    chapters = context.user_data.get("quiz_chapters", [])
    context.user_data["quiz_chapter_page"] = page
    reply_markup = build_chapter_keyboard(chapters, page=page)
    subject = context.user_data.get("quiz_subject", "")
    await query.edit_message_text(f"📖 *Select Chapter for {subject}:*", parse_mode="Markdown",
                                  reply_markup=reply_markup)
    return CHAPTER


async def quiz_chapter_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chapter = query.data.split("_")[2]
    context.user_data["quiz_chapter"] = chapter

    keyboard = [
        [InlineKeyboardButton("10", callback_data="quiz_count_10"),
         InlineKeyboardButton("20", callback_data="quiz_count_20"),
         InlineKeyboardButton("50", callback_data="quiz_count_50")],
        [InlineKeyboardButton("70", callback_data="quiz_count_70"),
         InlineKeyboardButton("100", callback_data="quiz_count_100"),
         InlineKeyboardButton("Full", callback_data="quiz_count_full")],
        [InlineKeyboardButton("🔙 Back", callback_data="quiz_back_chapter")]
    ]
    await query.edit_message_text(f"📊 *How many questions?* (Chapter: {chapter})", parse_mode="Markdown",
                                  reply_markup=InlineKeyboardMarkup(keyboard))
    return QUESTION_COUNT


async def quiz_count_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    count_str = query.data.split("_")[2]
    limit = None if count_str == "full" else int(count_str)
    context.user_data["quiz_limit"] = limit

    keyboard = [
        [InlineKeyboardButton("15 sec", callback_data="quiz_timer_15"),
         InlineKeyboardButton("30 sec", callback_data="quiz_timer_30"),
         InlineKeyboardButton("60 sec", callback_data="quiz_timer_60")],
        [InlineKeyboardButton("🔙 Back", callback_data="quiz_back_count")]
    ]
    await query.edit_message_text("⏱️ *Select time per question:*", parse_mode="Markdown",
                                  reply_markup=InlineKeyboardMarkup(keyboard))
    return TIMER


async def quiz_timer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    timer = int(query.data.split("_")[2])  # 15, 30, or 60
    context.user_data["quiz_timer"] = timer

    subject = context.user_data["quiz_subject"]
    chapter = context.user_data["quiz_chapter"]
    limit = context.user_data.get("quiz_limit")
    is_group = context.user_data["is_group"]
    chat_id = context.user_data["chat_id"]
    user_id = context.user_data["user_id"]

    questions = await get_random_questions(subject, chapter, limit)
    if not questions:
        await query.edit_message_text("❌ No questions found for this chapter.")
        return ConversationHandler.END

    total = len(questions)
    session_id = chat_id
    chapter_quiz_sessions[session_id] = {
        "chat_id": chat_id,
        "creator_id": user_id,
        "is_group": is_group,
        "questions": questions,
        "current_index": 0,
        "total": total,
        "timer": timer,
        "participants": {},
        "start_time": datetime.utcnow(),
        "active": True,
        "timeout_task": None
    }

    await query.edit_message_text(f"🚀 *Quiz Started!*\n\nChapter: {chapter}\nTotal questions: {total}\nTime per question: {timer} sec\n\nFirst question coming...")
    await asyncio.sleep(1)
    await send_next_question(context, session_id)
    return ConversationHandler.END


async def send_next_question(context, session_id):
    session = chapter_quiz_sessions.get(session_id)
    if not session or not session["active"]:
        return
    idx = session["current_index"]
    if idx >= session["total"]:
        await end_quiz(context, session_id)
        return
    q = session["questions"][idx]
    options = q["options"]
    correct_option_id = q["correct_index"]
    timer = session["timer"]
    message = await context.bot.send_poll(
        chat_id=session["chat_id"],
        question=q["question"],
        options=options,
        type=Poll.QUIZ,
        correct_option_id=correct_option_id,
        is_anonymous=False,
        explanation=f"Question {idx+1}/{session['total']} | ⏱️ Time limit: {timer} sec"
    )
    session["current_poll_id"] = message.poll.id
    session["current_message_id"] = message.message_id
    session["current_question_start"] = datetime.utcnow()
    session["answered_users"] = set()
    await db.db.poll_logs.update_one(
        {"poll_id": message.poll.id},
        {"$set": {"chapter_quiz_session": session_id, "question_index": idx}},
        upsert=True
    )

    # ✅ Timer task – auto-advance after timer seconds
    async def timeout():
        await asyncio.sleep(timer)
        # Check if still on the same question and quiz active
        if session_id in chapter_quiz_sessions and session["active"] and session["current_index"] == idx:
            session["active"] = False
            session["current_index"] += 1
            await send_next_question(context, session_id)
    task = asyncio.create_task(timeout())
    session["timeout_task"] = task


async def end_quiz(context, session_id):
    session = chapter_quiz_sessions.pop(session_id, None)
    if not session:
        return
    total = session["total"]
    is_group = session["is_group"]
    participants = session["participants"]
    if not participants:
        await context.bot.send_message(chat_id=session["chat_id"], text="No participants answered.")
        return

    total_answered = len(participants) * total
    chapter_name = session["questions"][0]["chapter"]

    if is_group:
        sorted_users = sorted(participants.items(), key=lambda x: (-x[1]["score"], x[1]["total_time"]))
        top_15 = sorted_users[:15]
        text = f"🏁 *The quiz '{chapter_name}' has finished!*\n\n{total_answered} questions answered\n\n"
        for idx, (uid, data) in enumerate(top_15, 1):
            name = data["name"]
            score = data["score"]
            time_str = format_time(data["total_time"])
            if idx == 1:
                text += f"🥇 {name} – {score} ({time_str})\n"
            elif idx == 2:
                text += f"🥈 {name} – {score} ({time_str})\n"
            elif idx == 3:
                text += f"🥉 {name} – {score} ({time_str})\n"
            else:
                text += f"{idx}. {name} – {score} ({time_str})\n"
        text += "\n🏆 *Congratulations to the winners!*"
        await context.bot.send_message(chat_id=session["chat_id"], text=text, parse_mode="Markdown")
    else:
        uid = list(participants.keys())[0]
        data = participants[uid]
        score = data["score"]
        time_str = format_time(data["total_time"])
        text = f"🏆 *Quiz Completed!*\n\nScore: {score}/{total}\nTotal time taken: {time_str}"
        await context.bot.send_message(chat_id=session["chat_id"], text=text, parse_mode="Markdown")


async def stop_quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    session = chapter_quiz_sessions.get(chat_id)
    if not session:
        await update.message.reply_text("No active quiz to stop.")
        return
    if session["creator_id"] != user_id:
        await update.message.reply_text("Only the quiz creator can stop it.")
        return
    if session.get("timeout_task"):
        session["timeout_task"].cancel()
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=session["current_message_id"])
    except:
        pass
    chapter_quiz_sessions.pop(chat_id, None)
    await update.message.reply_text("🛑 Quiz stopped by command.")


async def quiz_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    session_id = query.message.chat.id
    if session_id in chapter_quiz_sessions:
        del chapter_quiz_sessions[session_id]
    await query.edit_message_text("❌ Quiz cancelled.")
    return ConversationHandler.END


async def quiz_back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "quiz_back_subject":
        keyboard = [
            [InlineKeyboardButton("⚛️ Physics", callback_data="quiz_subject_Physics"),
             InlineKeyboardButton("🧪 Chemistry", callback_data="quiz_subject_Chemistry"),
             InlineKeyboardButton("🧬 Biology", callback_data="quiz_subject_Biology")],
            [InlineKeyboardButton("❌ Cancel", callback_data="quiz_cancel")]
        ]
        await query.edit_message_text("📚 *Select Subject for Quiz:*", parse_mode="Markdown",
                                      reply_markup=InlineKeyboardMarkup(keyboard))
        return SUBJECT
    elif data == "quiz_back_chapter":
        subject = context.user_data.get("quiz_subject")
        chapters = context.user_data.get("quiz_chapters", [])
        page = context.user_data.get("quiz_chapter_page", 0)
        reply_markup = build_chapter_keyboard(chapters, page=page)
        await query.edit_message_text(f"📖 *Select Chapter for {subject}:*", parse_mode="Markdown",
                                      reply_markup=reply_markup)
        return CHAPTER
    elif data == "quiz_back_count":
        chapter = context.user_data.get("quiz_chapter")
        keyboard = [
            [InlineKeyboardButton("10", callback_data="quiz_count_10"),
             InlineKeyboardButton("20", callback_data="quiz_count_20"),
             InlineKeyboardButton("50", callback_data="quiz_count_50")],
            [InlineKeyboardButton("70", callback_data="quiz_count_70"),
             InlineKeyboardButton("100", callback_data="quiz_count_100"),
             InlineKeyboardButton("Full", callback_data="quiz_count_full")],
            [InlineKeyboardButton("🔙 Back", callback_data="quiz_back_chapter")]
        ]
        await query.edit_message_text(f"📊 *How many questions?* (Chapter: {chapter})", parse_mode="Markdown",
                                      reply_markup=InlineKeyboardMarkup(keyboard))
        return QUESTION_COUNT
    return ConversationHandler.END


chapter_quiz_conv = ConversationHandler(
    entry_points=[
        CommandHandler("startquiz", start_quiz_command),
        CallbackQueryHandler(start_quiz_command, pattern="^start_chapter_quiz$")
    ],
    states={
        SUBJECT: [CallbackQueryHandler(quiz_subject_callback, pattern="^quiz_subject_")],
        CHAPTER: [
            CallbackQueryHandler(quiz_chapter_callback, pattern="^quiz_chapter_"),
            CallbackQueryHandler(quiz_chapter_page_callback, pattern="^quiz_chap_page_"),
            CallbackQueryHandler(quiz_back_callback, pattern="^quiz_back_subject$")
        ],
        QUESTION_COUNT: [
            CallbackQueryHandler(quiz_count_callback, pattern="^quiz_count_"),
            CallbackQueryHandler(quiz_back_callback, pattern="^quiz_back_chapter$")
        ],
        TIMER: [
            CallbackQueryHandler(quiz_timer_callback, pattern="^quiz_timer_"),
            CallbackQueryHandler(quiz_back_callback, pattern="^quiz_back_count$")
        ]
    },
    fallbacks=[CallbackQueryHandler(quiz_cancel, pattern="^quiz_cancel")],
    per_user=True,
    per_chat=False,
    allow_reentry=True
)
