from telegram import Update
from telegram.ext import ContextTypes
from bot.database.models import (
    get_poll_log,
    get_question_by_poll,
    update_user_stats,
    record_answer,
    get_user
)

import logging

logger = logging.getLogger(__name__)


async def poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):

    answer = update.poll_answer
    user = answer.user
    poll_id = answer.poll_id

    # safe option handling
    if not answer.option_ids:
        return

    selected_option = answer.option_ids[0]

    poll_log = await get_poll_log(poll_id)

    if not poll_log:
        logger.warning(f"Poll {poll_id} not found in logs")
        return

    chat_id = poll_log["chat_id"]

    question = await get_question_by_poll(poll_id)

    if not question:
        return

    correct_index = question["correct_index"]

    is_correct = selected_option == correct_index

    points_change = 1 if is_correct else -1

    # update user stats
    await update_user_stats(
        user_id=user.id,
        username=user.username or user.first_name,
        correct=is_correct,
        chapter=question["chapter"]
    )

    # leaderboard ke liye answer record
    await record_answer(
        user.id,
        user.username or user.first_name,
        question["_id"],
        points_change,
        chat_id
    )

    user_data = await get_user(user.id)

    total_points = user_data.get("total_points", 0)

    # mention system
    if user.username:
        mention = f"@{user.username}"
    else:
        mention = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"

    emoji = "✅" if is_correct else "❌"

    text = f"{mention} {emoji} {points_change:+d} | Total: {total_points}"

    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="HTML"
    )
