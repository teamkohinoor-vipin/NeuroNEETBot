from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.config import SUPPORT_CHANNEL, DEVELOPER_USERNAME

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Group mein /start karne par error message
    if update.effective_chat.type != "private":
        await update.message.reply_text("⚠️ Please use /start in private chat with me.")
        return

    # Attractive Welcome Message
    text = (
        "🧪 *Welcome to NEET Quiz Bot!* 🧪\n\n"
        "I send automatic NEET quizzes in the group every 20 minutes, with subject rotation:\n\n"
        "🌅 *6:00 AM – 12:00 PM*  →  Physics ⚛️\n"
        "☀️ *12:00 PM – 6:00 PM*  →  Chemistry 🧪\n"
        "🌙 *6:00 PM – 12:00 AM*  →  Biology 🧬\n"
        "😴 *12:00 AM – 6:00 AM*  →  Sleep Mode (no quizzes)\n\n"
        "📊 *Scoring System:*\n"
        "✅ Correct Answer  →  +1 point\n"
        "❌ Wrong Answer    →  –1 point\n\n"
        "🏆 Compete on the leaderboard with `/leaderboard` in the group!\n\n"
        "💞 Just add me in your group and i will send NEET Polls.\n\n"
        "👇 *Use the buttons below to get more information:*"
    )

    keyboard = [
        [InlineKeyboardButton("❓ Help & Commands", callback_data="help")],
        [InlineKeyboardButton("➕ Add Question", callback_data="add_question")],
        [InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{DEVELOPER_USERNAME}")],
        [InlineKeyboardButton("📢 Support Channel", url=f"https://t.me/{SUPPORT_CHANNEL}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = (
        "📘 *Help Menu*\n\n"
        "*📅 Quiz Schedule:*\n"
        "• Every 20 minutes\n"
        "• Subject changes automatically based on time block (Physics, Chemistry, Biology)\n"
        "• Sleep Mode: 12 AM – 6 AM (No quizzes)\n\n"
        
        "*📊 Scoring System:*\n"
        "• ✅ Correct Answer → +1 point\n"
        "• ❌ Wrong Answer   → –1 point\n"
        "• Real-time feedback in group after each answer\n\n"
        
        "*🤖 Commands:*\n"
        "• `/leaderboard` – View Top 10 users (Daily/Weekly/All-Time) – *Group only*\n"
        "• `/start` – Show this menu – *Private only*\n\n"
        
        "*➕ Adding Questions:*\n"
        "When you click 'Add Question', you'll help the entire community! Your questions will be sent to all groups where this bot is active (after admin approval).\n\n"
        "Please send questions in this *strict format*:\n\n"
        "```\n"
        "Q: How many bones are there in the human body?\n"
        "A) 206\n"
        "B) 100\n"
        "C) 300\n"
        "D) 500\n"
        "Answer: A\n"
        "Year: 2024 (optional)\n"
        "```\n\n"
        "• After sending, use `/next` for more questions or `/done` to submit batch for admin approval.\n"
        "• You'll be notified when your questions are accepted or rejected."
    )
    
    await query.edit_message_text(text, parse_mode="Markdown")
