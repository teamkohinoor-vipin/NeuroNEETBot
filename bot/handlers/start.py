from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.config import SUPPORT_CHANNEL, DEVELOPER_USERNAME
from bot.database.db import db
from bot.database.models import get_config

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

    # ✨ Custom welcome message with user's name
    text = (
        f"🧪 *Welcome {user} to NEET Quiz Bot!* 🧪\n\n"
        
        "I can send automatic NEET quizzes every 20 minutes.\n\n"
        
        "🌅 *6:00 AM – 12:00 PM* → Physics ⚛️\n"
        "☀️ *12:00 PM – 6:00 PM* → Chemistry 🧪\n"
        "🌙 *6:00 PM – 12:00 AM* → Biology 🧬\n"
        "😴 *12:00 AM – 6:00 AM* → Sleep Mode\n\n"
        
        "📊 *Scoring System*\n"
        "✅ Correct → +1 point\n"
        "❌ Wrong → -1 point\n\n"
        
        "🎯 Just add me in your group and make me Admin.\n\n"
        
        "👇 *Use the buttons below:*"
    )

    # 👇 Check if question submission is enabled
    question_enabled = await get_config("question_add_enabled", True)

    # 👇 Add Group Button (always show)
    add_group_button = InlineKeyboardButton(
        "📢 Add Bot to Group",
        url=f"https://t.me/{context.bot.username}?startgroup=true"
    )

    if chat_type == "private":
        keyboard_buttons = [
            [InlineKeyboardButton("❓ Help", callback_data="help")],
        ]
        if question_enabled:
            keyboard_buttons.append([InlineKeyboardButton("➕ Add Question", callback_data="add_question")])
        keyboard_buttons.extend([
            [add_group_button],
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
            [add_group_button],
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

    help_text = """
📖 *NEET QUIZ BOT – HELP GUIDE*

This bot provides automated NEET quiz practice in Telegram groups.

━━━━━━━━━━━━━━━━

👨‍🎓 *User Commands*

/start  
Start the bot and view menu.

➕ Add Question  
Submit NEET questions to the quiz database.

━━━━━━━━━━━━━━━━

👥 *Group Commands*

/leaderboard  
Show top quiz players in the group.

━━━━━━━━━━━━━━━━

👑 *Admin Commands*

Only bot admin can use these.

/broadcast  
Send message to all groups.

/stats  
View bot statistics.

/adminpanel  
Open admin control panel.

━━━━━━━━━━━━━━━━

⚙️ *Quiz System*

• Questions are sent automatically  
• Quiz runs every **20 minutes**  
• Questions are NEET-level MCQ

━━━━━━━━━━━━━━━━

🏆 *Leaderboard*

Compete with other students and climb the leaderboard.

━━━━━━━━━━━━━━━━

💡 *Tip*

Practice daily quizzes to improve speed and accuracy for NEET.

Good luck with your preparation! 🚀
"""

    back_button = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(back_button)

    await query.edit_message_text(
        help_text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )
