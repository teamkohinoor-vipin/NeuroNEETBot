from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.config import SUPPORT_CHANNEL, DEVELOPER_USERNAME, ADMIN_ID
from bot.database.db import db
from bot.database.models import get_config
from datetime import datetime


HELP_PAGES = [

"""
📖 *NeuroNEETBot – HELP GUIDE*

This bot provides automated NEET quiz practice in Telegram groups.

━━━━━━━━━━━━━━━━

👨‍🎓 *User Commands*

/start  
Start the bot and view menu.

➕ Add Question  
Submit NEET questions to the quiz database.
""",

"""
👥 *Group Commands*

/leaderboard  
Show top quiz players in the group.

━━━━━━━━━━━━━━━━

👑 *Admin Commands*

/broadcast  
Send message to all groups.

/stats  
View bot statistics.

/adminpanel  
Open admin control panel.
""",

"""
💾 *Database Commands*

/backup  
Download Database backup file.

/restore  
Restore database by sending backup file.

━━━━━━━━━━━━━━━━

⚙️ *Quiz System*

• Questions are sent automatically  
• Quiz runs every **20 minutes**
""",

"""
🏆 *Leaderboard*

Compete with other students and climb the leaderboard.

━━━━━━━━━━━━━━━━

💡 *Tip*

Practice daily quizzes to improve speed and accuracy for NEET.

Good luck with your preparation 🚀
""",

"""
📖 *Chapter Quiz – Custom Quiz System*

Use `/startquiz` to start a custom quiz:
- Choose subject → chapter → number of questions
- Each question is sent as a Telegram poll
- You answer at your own pace (no timer)
- After all questions, you get your score and total time

Use `/stopquiz` to stop an ongoing quiz.

*Group quiz*: Only group admins can start. Multiple participants can answer, and a leaderboard with top 15 users is shown at the end (time‑based scoring).

Enjoy practicing NEET questions!
"""
]


def help_keyboard(page):

    buttons = []
    nav = []

    if page > 0:
        nav.append(
            InlineKeyboardButton("⬅️ Back", callback_data=f"help_{page-1}")
        )

    if page < len(HELP_PAGES) - 1:
        nav.append(
            InlineKeyboardButton("Next ➡️", callback_data=f"help_{page+1}")
        )

    if nav:
        buttons.append(nav)

    buttons.append(
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]
    )

    return InlineKeyboardMarkup(buttons)


# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.first_name
    chat_type = update.effective_chat.type

    user_id = update.effective_user.id
    username = update.effective_user.username

    existing_user = await db.db.users.find_one({"user_id": user_id})

    await db.db.users.update_one(
        {"user_id": user_id},
        {"$set": {
            "user_id": user_id,
            "username": username
        }},
        upsert=True
    )

    if not existing_user:

        total_users = await db.db.users.count_documents({})

        username_text = f"@{username}" if username else "No username"

        notify_text = (
            "🆕 New User Started the Bot!\n\n"
            f"👤 User: {user}\n"
            f"🆔 ID: {user_id}\n"
            f"📛 Username: {username_text}\n"
            f"👥 Total Users: {total_users}\n"
            f"⏰ Time: {datetime.now()}"
        )

        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=notify_text
            )
        except:
            pass

    text = (
    f"🧪 *Welcome {user} to NeuroNEETBot!* 🧪\n\n"
    "I can send automatic Random NEET quizzes every 5 minutes.\n\n"
    "📚 *Subjects Covered*\n"
    "⚛️ Physics\n"
    "🧪 Chemistry\n"
    "🧬 Biology\n\n"
    "📊 *Scoring System*\n"
    "✅ Correct → +1 point\n"
    "❌ Wrong → -1 point\n\n"
    "🎯 Just add me in your group and make me Admin.\n\n"
    "👇 *Use the buttons below:*"
    )

    question_enabled = await get_config("question_add_enabled", True)

    add_group_button = InlineKeyboardButton(
        "📢 Add Bot to Group",
        url=f"https://t.me/{context.bot.username}?startgroup=true"
    )

    if chat_type == "private":

        keyboard_buttons = [
            [InlineKeyboardButton("❓ Help", callback_data="help")],
            [InlineKeyboardButton("📚 Start Quiz", callback_data="start_chapter_quiz")],
        ]

        if question_enabled:
            keyboard_buttons.append(
                [InlineKeyboardButton("➕ Add Question", callback_data="add_question")]
            )

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
            keyboard.append(
                [InlineKeyboardButton("➕ Add Question (Private)", url=f"https://t.me/{bot_username}?start=add")]
            )

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


# ================= HELP BUTTON =================
async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    page = 0

    await query.edit_message_text(
        HELP_PAGES[page],
        parse_mode="Markdown",
        reply_markup=help_keyboard(page)
    )


# ================= HELP PAGE =================
async def help_page(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    page = int(query.data.split("_")[1])

    await query.edit_message_text(
        HELP_PAGES[page],
        parse_mode="Markdown",
        reply_markup=help_keyboard(page)
    )
