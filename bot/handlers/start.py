from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.config import SUPPORT_CHANNEL, DEVELOPER_USERNAME
from bot.database.db import db


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.first_name
    chat_type = update.effective_chat.type

    # Save user
    user_id = update.effective_user.id
    username = update.effective_user.username

    await db.db.users.update_one(
        {"user_id": user_id},
        {"$set": {
            "user_id": user_id,
            "username": username
        }},
        upsert=True
    )

    text = (
        f"🧪 *Welcome {user} to NEET Quiz Bot!* 🧪\n\n"

        "I send automatic NEET quizzes every 20 minutes.\n\n"

        "🌅 *6:00 AM – 12:00 PM* → Physics ⚛️\n"
        "☀️ *12:00 PM – 6:00 PM* → Chemistry 🧪\n"
        "🌙 *6:00 PM – 12:00 AM* → Biology 🧬\n"
        "😴 *12:00 AM – 6:00 AM* → Sleep Mode\n\n"

        "📊 *Scoring System*\n"
        "✅ Correct → +1 point\n"
        "❌ Wrong → -1 point\n\n"

        "🏆 Use `/leaderboard` in group to see rankings.\n\n"

        "👇 Use the buttons below:"
    )

    if chat_type == "private":

        keyboard = [
            [InlineKeyboardButton("❓ Help", callback_data="help")],
            [InlineKeyboardButton("➕ Add Question", callback_data="add_question")],
            [InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{DEVELOPER_USERNAME}")],
            [InlineKeyboardButton("📢 Support Channel", url=f"https://t.me/{SUPPORT_CHANNEL}")]
        ]

    else:

        bot_username = context.bot.username

        keyboard = [
            [InlineKeyboardButton("❓ Help", callback_data="help")],

            # leaderboard menu open karega
            [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard_menu")],

            [InlineKeyboardButton("➕ Add Question (Private)", url=f"https://t.me/{bot_username}?start=add")],
            [InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{DEVELOPER_USERNAME}")],
            [InlineKeyboardButton("📢 Support Channel", url=f"https://t.me/{SUPPORT_CHANNEL}")]
        ]

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    text = (
        "📘 *Help Menu*\n\n"

        "*📅 Quiz Schedule*\n"
        "Every 20 minutes\n\n"

        "*📊 Scoring*\n"
        "Correct → +1\n"
        "Wrong → -1\n\n"

        "*🤖 Commands*\n"
        "`/leaderboard` → Top users\n"
        "`/start` → Start menu\n\n"

        "Questions can be added in private chat."
    )

    await query.edit_message_text(
        text,
        parse_mode="Markdown"
    )
