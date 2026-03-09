import logging

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

    chat_id = poll_log["chat_id"]

    question = await get_question_by_poll(poll_id)

    if not question:
        return

    correct_index = question["correct_index"]

    is_correct = selected_option == correct_index

    points_change = 1 if is_correct else -1

    # update stats
    await update_user_stats(
        user_id=user.id,
        username=user.username or user.first_name,
        correct=is_correct,
        chapter=question["chapter"]
    )

    # record answer
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

    # ✅ check mention setting
    mention_enabled = await get_config("answer_mentions", True)

    if mention_enabled:

        msg = await context.bot.send_message(chat_id=chat_id, text=text)

        if chat_id not in score_messages:
            score_messages[chat_id] = []

        score_messages[chat_id].append(msg.message_id)

        # memory safety
        if len(score_messages[chat_id]) > 50:
            score_messages[chat_id].pop(0)
