from telegram import Update
from telegram.ext import ContextTypes
from bot.database.models import get_poll_log, get_question_by_poll, update_user_stats, record_answer, get_user
import logging

logger = logging.getLogger(__name__)

# store score messages per group
score_messages = {}

async def poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.poll_answer
    user = answer.user
    poll_id = answer.poll_id
    selected_option = answer.option_ids[0] if answer.option_ids else None

    poll_log = await get_poll_log(poll_id)
    if not poll_log:
        logger.warning(f"Poll {poll_id} not found in logs")
        return

    chat_id = poll_log["chat_id"]
    question_id = poll_log["question_id"]

    question = await get_question_by_poll(poll_id)
    if not question:
        logger.warning(f"Question not found for poll {poll_id}")
        return

    correct_index = question["correct_index"]
    is_correct = (selected_option == correct_index)
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
    total_points = user_data.get("total_points", 0)

    mention = f"@{user.username}" if user.username else user.first_name
    emoji = "✅" if is_correct else "❌"
    text = f"{mention} {emoji} {points_change:+d} | Total: {total_points}"

    msg = await context.bot.send_message(chat_id=chat_id, text=text)

    # store message id
    if chat_id not in score_messages:
        score_messages[chat_id] = []

    score_messages[chat_id].append(msg.message_id)
