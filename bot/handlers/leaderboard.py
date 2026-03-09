from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from bot.database.models import get_top_users
import pytz


IST = pytz.timezone("Asia/Kolkata")


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


# /leaderboard command
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = "📕 Click the below button to check leaderboard."

    await update.message.reply_text(
        text,
        reply_markup=leaderboard_keyboard()
    )


# START button leaderboard menu
async def leaderboard_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    text = "📕 Click the below button to check leaderboard."

    await query.edit_message_text(
        text,
        reply_markup=leaderboard_keyboard()
    )


async def leaderboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat.id
    period = query.data.split("_")[1]

    now = datetime.now(IST)

    # ---------- DAILY ----------
    if period == "daily":

        since = datetime(
            now.year,
            now.month,
            now.day,
            0, 0, 0,
            tzinfo=IST
        )

        title = "📅 Daily Leaderboard"

    # ---------- WEEKLY ----------
    elif period == "weekly":

        start_of_week = now - timedelta(days=now.weekday())

        since = datetime(
            start_of_week.year,
            start_of_week.month,
            start_of_week.day,
            0, 0, 0,
            tzinfo=IST
        )

        title = "📊 Weekly Leaderboard"

    # ---------- MONTHLY ----------
    else:

        since = datetime(
            now.year,
            now.month,
            1,
            0, 0, 0,
            tzinfo=IST
        )

        title = "📆 Monthly Leaderboard"


    users = await get_top_users(chat_id=chat_id, limit=10, since=since)

    if not users:

        text = "Leaderboard data not available right now."

    else:

        lines = [f"{title}\n"]

        for i, user in enumerate(users, 1):

            user_id = user.get("_id")

            try:
                member = await context.bot.get_chat_member(chat_id, user_id)
                first_name = member.user.first_name
            except:
                first_name = "User"

            points = user.get("points", 0)

            name = f"[{first_name}](tg://user?id={user_id})"

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
