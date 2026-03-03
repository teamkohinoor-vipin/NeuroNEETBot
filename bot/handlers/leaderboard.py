from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from bot.database.models import get_top_users
from bot.utils.decorators import group_only

@group_only
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Daily", callback_data="leaderboard_daily"),
            InlineKeyboardButton("Weekly", callback_data="leaderboard_weekly"),
            InlineKeyboardButton("All Time", callback_data="leaderboard_all")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select leaderboard period:", reply_markup=reply_markup)

async def leaderboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    period = query.data.split("_")[1]

    now = datetime.utcnow()
    if period == "daily":
        since = now - timedelta(days=1)
    elif period == "weekly":
        since = now - timedelta(weeks=1)
    else:
        since = None

    users = await get_top_users(limit=10, since=since)
    if not users:
        await query.edit_message_text("No data yet.")
        return

    lines = ["🏆 *Top 10*"]
    for i, user in enumerate(users, 1):
        name = user.get("username", "Anonymous")
        points = user.get("points") if since else user.get("total_points", 0)
        lines.append(f"{i}. {name} – {points} pts")
    await query.edit_message_text("\n".join(lines), parse_mode="Markdown")