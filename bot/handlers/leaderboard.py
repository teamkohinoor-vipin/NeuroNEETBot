from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from bot.database.models import get_top_users
from bot.utils.decorators import group_only


def leaderboard_keyboard():

    keyboard = [
        [
            InlineKeyboardButton("📅 Daily", callback_data="leaderboard_daily"),
            InlineKeyboardButton("📊 Weekly", callback_data="leaderboard_weekly")
        ],
        [
            InlineKeyboardButton("📆 Monthly", callback_data="leaderboard_monthly")
        ]
    ]

    return InlineKeyboardMarkup(keyboard)


async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = (
        "📕 Click the below button to check leaderboard\n\n"
        "Leaderboard data not yet available."
    )

    await update.message.reply_text(
        text,
        reply_markup=leaderboard_keyboard()
    )


async def leaderboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    chat_id = query.message.chat.id

    period = query.data.split("_")[1]

    now = datetime.utcnow()

    if period == "daily":

        since = datetime(now.year, now.month, now.day)

        title = "📅 Daily Leaderboard"

    elif period == "weekly":

        since = now - timedelta(days=now.weekday())

        title = "📊 Weekly Leaderboard"

    else:

        since = datetime(now.year, now.month, 1)

        title = "📆 Monthly Leaderboard"

    users = await get_top_users(chat_id=chat_id, limit=10, since=since)

    if not users:

        text = "Data is not available right now."

    else:

        lines = [f"{title}\n"]

        for i, user in enumerate(users, 1):

            username = user.get("username")

            points = user.get("points", 0)

            if username:

                name = f"[{username}](https://t.me/{username})"

            else:

                name = "Anonymous"

            if i == 1:
                rank = "🥇"

            elif i == 2:
                rank = "🥈"

            elif i == 3:
                rank = "🥉"

            else:
                rank = f"{i}."

            lines.append(f"{rank} {name} — {points} pts")

        text = "\n".join(lines)

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=leaderboard_keyboard()
    )
