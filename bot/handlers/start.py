from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.config import SUPPORT_CHANNEL, DEVELOPER_USERNAME

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        await update.message.reply_text("Please use /start in private chat with me.")
        return

    text = (
        "🧪 Welcome to NEET Quiz Bot!\n\n"
        "I send automatic NEET quizzes in the group every 20 minutes, rotating subjects:\n"
        "🌅 6AM–12PM: Physics\n"
        "☀️ 12PM–6PM: Chemistry\n"
        "🌙 6PM–12AM: Biology\n"
        "😴 12AM–6AM: Sleep mode (no quizzes)\n\n"
        "Scoring: ✅ +1 | ❌ -1\n"
        "Compete on the leaderboard!\n\n"
        "Use the buttons below to get started."
    )
    keyboard = [
        [InlineKeyboardButton("❓ Help", callback_data="help")],
        [InlineKeyboardButton("➕ Add Question", callback_data="add_question")],
        [InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{DEVELOPER_USERNAME}")],
        [InlineKeyboardButton("📢 Support Channel", url=f"https://t.me/{SUPPORT_CHANNEL}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = (
        "📘 *Help Menu*\n\n"
        "*Quiz Schedule:*\n"
        "Every 20 minutes, subject based on time block.\n\n"
        "*Scoring:*\n"
        "Correct: +1 point\n"
        "Wrong: -1 point\n\n"
        "*Commands:*\n"
        "/leaderboard – View top 10 (group only)\n"
        "/start – This menu (private)\n\n"
        "*Adding Questions:*\n"
        "Click 'Add Question' and follow the steps. "
        "Send questions in strict format:\n"
        "`Q: ... A) ... B) ... C) ... D) ... Answer: A Year: 2024`\n\n"
        "Use /next after each question, /done to submit batch for admin approval."
    )
    await query.edit_message_text(text, parse_mode="Markdown")