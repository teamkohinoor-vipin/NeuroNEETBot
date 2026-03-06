from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.config import SUPPORT_CHANNEL, DEVELOPER_USERNAME
from bot.database.db import db
from bot.database.models import get_config   # 👈 NEW IMPORT

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

    # 👇 Check if question submission is enabled
    question_enabled = await get_config("question_add_enabled", True)

    if chat_type == "private":
        keyboard_buttons = [
            [InlineKeyboardButton("❓ Help", callback_data="help")],
        ]
        if question_enabled:
            keyboard_buttons.append([InlineKeyboardButton("➕ Add Question", callback_data="add_question")])
        # If disabled, button is simply not shown
        keyboard_buttons.extend([
            [InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{DEVELOPER_USERNAME}")],
            [InlineKeyboardButton("📢 Support Channel", url=f"https://t.me/{SUPPORT_CHANNEL}")]
        ])
        keyboard = keyboard_buttons
    else:
        bot_username = context.bot.username
        keyboard = [
            [InlineKeyboardButton("❓ Help", callback_data="help")],
            [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard_menu")],
        ]
        if question_enabled:
            keyboard.append([InlineKeyboardButton("➕ Add Question (Private)", url=f"https://t.me/{bot_username}?start=add")])
        keyboard.extend([
            [InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{DEVELOPER_USERNAME}")],
            [InlineKeyboardButton("📢 Support Channel", url=f"https://t.me/{SUPPORT_CHANNEL}")]
        ])

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
