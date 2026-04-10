import logging
from telegram import Update, Poll
from telegram.ext import ContextTypes
from bot.handlers.chapter_quiz import chapter_quiz_sessions, send_next_question, end_quiz
from bot.database.models import get_poll_log

logger = logging.getLogger(__name__)

async def poll_update_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    poll: Poll = update.poll
    if not poll.is_closed:
        return

    poll_log = await get_poll_log(poll.id)
    if not poll_log or not poll_log.get("chapter_quiz_session"):
        return

    session_id = poll_log["chapter_quiz_session"]
    session = chapter_quiz_sessions.get(session_id)
    if not session or not session["active"]:
        return

    # Avoid double‑advance
    if not session.get("waiting_for_closure"):
        return

    # Check if any answers were given
    had_answers = poll.total_voter_count > 0
    if not had_answers:
        # No one answered this question – increment counter
        session["no_answer_counter"] = session.get("no_answer_counter", 0) + 1
        if session["no_answer_counter"] >= 4:
            # Stop the quiz due to inactivity
            session["active"] = False
            await end_quiz(context, session_id, stopped_by_inactivity=True)
            return
    else:
        # Reset counter when at least one answer is given
        session["no_answer_counter"] = 0

    session["waiting_for_closure"] = False
    session["current_index"] += 1
    await send_next_question(context, session_id)
