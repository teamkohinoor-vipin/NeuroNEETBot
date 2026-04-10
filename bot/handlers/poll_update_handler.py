import logging
from telegram import Update, Poll
from telegram.ext import ContextTypes
from bot.handlers.chapter_quiz import chapter_quiz_sessions, send_next_question
from bot.database.models import get_poll_log

logger = logging.getLogger(__name__)

async def poll_update_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Called when a poll is closed (e.g., timer expired)"""
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

    # Prevent double advance
    if not session.get("waiting_for_closure"):
        return

    session["waiting_for_closure"] = False
    session["current_index"] += 1
    await send_next_question(context, session_id)
