import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from bot.database.models import (
    get_poll_log,
    get_question_by_poll,
    update_user_stats,
    record_answer,
    get_user,
    get_config
)

from bot.handlers.chapter_quiz import chapter_quiz_sessions, send_next_question

logger = logging.getLogger(__name__)

score_messages = {}


async def poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.poll_answer
    user = answer.user
    poll_id = answer.poll_id
    selected_option = answer.option_ids[0] if answer.option_ids else None

    poll_log = await get_poll_log(poll_id)
    if not poll_log:
        return

    # ---------- CHAPTER QUIZ HANDLING ----------
    if poll_log.get("chapter_quiz_session"):
        session_id = poll_log["chapter_quiz_session"]
        session = chapter_quiz_sessions.get(session_id)
        if session and session["active"]:
            q_index = poll_log["question_index"]
            if q_index != session["current_index"]:
                # Old poll, ignore
                return
            user_id = user.id
            user_name = user.first_name or user.username or str(user_id)
            question = session["questions"][q_index]
            correct = (selected_option == question["correct_index"])
            time_taken = (datetime.utcnow() - session["current_question_start"]).total_seconds()
            time_taken = min(time_taken, session["timer"])

            # 🔥 NEW: Mark that this question was answered and reset inactivity counter
            session["answered_this_question"] = True
            session["no_answer_counter"] = 0

            if session["is_group"]:
                # Group quiz: record answer, do NOT advance – wait for timer
                if user_id not in session["participants"]:
                    session["participants"][user_id] = {"score": 0, "total_time": 0.0, "name": user_name}
                if correct:
                    session["participants"][user_id]["score"] += 1
                session["participants"][user_id]["total_time"] += time_taken
                session.setdefault("answered_users", set()).add(user_id)
                # Timer will advance after its sleep, but it will see answered_this_question=True and reset counter
                return
            else:
                # Private quiz: record answer, cancel timer, advance immediately
                # 🔥 Cancel the timer task to avoid duplicate advancement
                if session.get("current_timer_task"):
                    try:
                        session["current_timer_task"].cancel()
                    except:
                        pass
                    session["current_timer_task"] = None

                if user_id not in session["participants"]:
                    session["participants"][user_id] = {"score": 0, "total_time": 0.0, "name": user_name}
                if correct:
                    session["participants"][user_id]["score"] += 1
                session["participants"][user_id]["total_time"] += time_taken

                # Advance to next question immediately
                session["current_index"] += 1
                await send_next_question(context, session_id)
                return

    # ---------- NORMAL SCHEDULED QUIZ (unchanged) ----------
    chat_id = poll_log["chat_id"]
    question = await get_question_by_poll(poll_id)
    if not question:
        return

    correct_index = question["correct_index"]
    is_correct = selected_option == correct_index
    points_change = 1 if is_correct else -1

    await update_user_stats(
        user_id=user.id,
        username=user.username or user.first_name,
        correct=is_correct,
        chapter=question["chapter"]
    )

    await record_answer(
        user_id=user.id,
        username=user.username or user.first_name,
        question_id=question["_id"],
        points_change=points_change,
        chat_id=chat_id
    )

    user_data = await get_user(user.id)
    total_points = user_data.get("total_points", 0) if user_data else 0

    mention = f"@{user.username}" if user.username else user.first_name
    emoji = "✅" if is_correct else "❌"
    text = f"{mention} {emoji} {points_change:+d} | Total: {total_points}"

    mention_enabled = await get_config("answer_mentions", True)
    if mention_enabled:
        msg = await context.bot.send_message(chat_id=chat_id, text=text)
        if chat_id not in score_messages:
            score_messages[chat_id] = []
        score_messages[chat_id].append(msg.message_id)
        if len(score_messages[chat_id]) > 50:
            score_messages[chat_id].pop(0)
