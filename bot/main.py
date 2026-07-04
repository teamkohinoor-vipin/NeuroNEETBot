import asyncio
import logging
import warnings
import re

# ===== SUPPRESS ALL HARMLESS WARNINGS =====
warnings.filterwarnings("ignore")
logging.getLogger("pymongo").setLevel(logging.ERROR)
logging.getLogger("motor").setLevel(logging.ERROR)
logging.getLogger("apscheduler").setLevel(logging.WARNING)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    PollAnswerHandler,
    PollHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ChatMemberHandler,
    ContextTypes
)

from bot.config import BOT_TOKEN, SUPPORT_CHANNEL, DEVELOPER_USERNAME, ADMIN_ID
from bot.database.db import connect_db, close_db
from bot.scheduler import start_scheduler, send_quiz_to_group
from bot.database.models import add_group, remove_group, get_config, set_config

from bot.handlers.start import start, help_callback, help_page
from bot.handlers.leaderboard import leaderboard, leaderboard_callback
from bot.handlers.poll_answer import poll_answer
from bot.handlers.poll_update_handler import poll_update_handler

from bot.handlers.question_submission import (
    add_question_start,
    subject_callback,
    class_callback,
    chapter_callback,
    chapter_page,
    receive_question,
    next_action_callback,
    cancel,
    SUBJECT,
    CLASS_,
    CHAPTER,
    QUESTION,
    NEXT_ACTION
)

from bot.handlers.admin import admin_callback
from bot.handlers.error import error_handler
from bot.handlers.admin_stats import stats
from bot.handlers.broadcast import broadcast, group_broadcast, stopbroadcast
from bot.handlers.backup import backup, restore
from bot.handlers.reset_database import reset_database_command
from bot.handlers.admin_panel import admin_panel, admin_panel_callback
from bot.handlers.import_txt_questions import (
    import_command,
    stop_import,
    import_txt_questions
)
from bot.handlers.links import links, link_page_callback

from bot.handlers.chapter_quiz import (
    chapter_quiz_conv,
    stop_quiz_command,
    quiz_cancel
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


async def unmatched_callback(update: Update, context):
    logger.warning(f"Unknown callback: {update.callback_query.data}")
    await update.callback_query.answer(
        "This button is not available. Use /start again."
    )


async def track_groups(update: Update, context):
    chat = update.effective_chat
    if chat and chat.type in ["group", "supergroup"]:
        await add_group(chat.id)


async def bot_added_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.my_chat_member
    if result.new_chat_member.status == "member" and result.old_chat_member.status == "left":
        chat_id = result.chat.id
        await add_group(chat_id)

        bot_username = context.bot.username
        welcome_text = (
            "🧪 *Welcome to NeuroNEETBot!* 🧪\n\n"
            "I can send automatic Random NEET quizzes every 5 minutes.\n\n"
            "📚 *Subjects Covered*\n"
            "⚛️ Physics\n"
            "🧪 Chemistry\n"
            "🧬 Biology\n\n"
            "📊 *Scoring System*\n"
            "✅ Correct → +1 point\n"
            "❌ Wrong → -1 point\n\n"
            "👇 *Use the buttons below:*"
        )

        add_group_button = InlineKeyboardButton(
            "📢 Add Bot to Group",
            url=f"https://t.me/{bot_username}?startgroup=true"
        )

        keyboard = [
            [InlineKeyboardButton("❓ Help", callback_data="help")],
            [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard_menu")],
            [add_group_button],
            [InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{DEVELOPER_USERNAME}")],
            [InlineKeyboardButton("📢 Support Channel", url=f"https://t.me/{SUPPORT_CHANNEL}")]
        ]

        await context.bot.send_message(
            chat_id=chat_id,
            text=welcome_text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        await send_quiz_to_group(chat_id, context.bot)


async def bot_removed_from_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.my_chat_member
    if result.new_chat_member.status in ["left", "kicked"] and result.old_chat_member.status in ["member", "administrator", "creator"]:
        chat_id = result.chat.id
        await remove_group(chat_id)
        logger.info(f"Group {chat_id} removed from database (bot left/kicked)")


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user.first_name
    chat_type = query.message.chat.type

    question_enabled = await get_config("question_add_enabled", True)

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

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ========== CUSTOM TIME PARSER ==========
def parse_time_string(text: str) -> int:
    text = text.strip().lower()
    match = re.match(r'^(\d+)\s*(?:sec(?:onds?)?|s)?$', text)
    if match:
        return int(match.group(1))
    match = re.match(r'^(\d+)\s*(?:min(?:ute)?s?|m)$', text)
    if match:
        return int(match.group(1)) * 60
    match = re.match(r'^(\d+)\s*(?:hour|hr)s?$', text)
    if match:
        return int(match.group(1)) * 3600
    if text.isdigit():
        return int(text)
    return None


# ========== SUFFIX INPUT HANDLER ==========
async def handle_suffix_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom suffix input from admin."""
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return

    if context.user_data.get("in_question_submission"):
        return

    if not context.user_data.get("waiting_for_suffix") and not context.user_data.get("suffix_mode"):
        return

    text = update.message.text.strip()

    if text.lower() == "/cancel":
        context.user_data["waiting_for_suffix"] = False
        context.user_data["suffix_mode"] = False
        await update.message.reply_text("❌ Suffix setting cancelled.")
        return

    if text.lower() == "none":
        await set_config("question_suffix", "")
        context.user_data["waiting_for_suffix"] = False
        context.user_data["suffix_mode"] = False
        await update.message.reply_text("✅ Question suffix removed.")
        return

    await set_config("question_suffix", text)
    context.user_data["waiting_for_suffix"] = False
    context.user_data["suffix_mode"] = False
    await update.message.reply_text(
        f"✅ Question suffix set to: `{text}`",
        parse_mode="Markdown"
    )


# ========== CUSTOM TIME INPUT HANDLER ==========
async def handle_custom_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return
    if not context.user_data.get("waiting_for_custom_time"):
        return
    text = update.message.text.strip()
    if text.lower() == "/cancel":
        context.user_data["waiting_for_custom_time"] = False
        await update.message.reply_text("❌ Custom time setting cancelled.")
        return
    seconds = parse_time_string(text)
    if seconds is None or seconds <= 0:
        await update.message.reply_text(
            "❌ Invalid time format. Please type something like:\n"
            "`10 sec`, `1 min`, `5 minutes`, `30` (seconds)\n"
            "or `/cancel` to cancel."
        )
        return
    await set_config("score_message_lifetime", seconds)
    context.user_data["waiting_for_custom_time"] = False
    await update.message.reply_text(
        f"✅ Score message delete time set to **{seconds} seconds**.",
        parse_mode="Markdown"
    )


# ========== MAIN ==========
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.post_init = connect_db
    application.post_shutdown = close_db

    # -------- COMMAND HANDLERS --------
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))

    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("groups", group_broadcast))
    application.add_handler(CommandHandler("stopbroadcast", stopbroadcast))

    application.add_handler(CommandHandler("links", links))
    application.add_handler(
        CallbackQueryHandler(link_page_callback, pattern="^links_page_")
    )

    application.add_handler(CommandHandler("backup", backup))
    application.add_handler(CommandHandler("restore", restore))

    application.add_handler(CommandHandler("resetdatabase", reset_database_command))

    application.add_handler(CommandHandler("import", import_command))
    application.add_handler(CommandHandler("stopimport", stop_import))

    application.add_handler(
        MessageHandler(filters.Document.FileExtension("txt"), import_txt_questions)
    )

    application.add_handler(
        MessageHandler(filters.Document.ALL, restore)
    )

    # -------- CALLBACK QUERY HANDLERS --------
    application.add_handler(
        CallbackQueryHandler(help_callback, pattern="^help$")
    )

    application.add_handler(
        CallbackQueryHandler(help_page, pattern="^help_")
    )

    application.add_handler(CommandHandler("leaderboard", leaderboard))

    application.add_handler(
        CallbackQueryHandler(leaderboard_callback, pattern="^leaderboard_")
    )

    application.add_handler(PollAnswerHandler(poll_answer))
    application.add_handler(PollHandler(poll_update_handler))

    application.add_handler(CommandHandler("adminpanel", admin_panel))

    application.add_handler(
        CallbackQueryHandler(admin_panel_callback, pattern="^admin_(toggle|panel|close|time|set_)")
    )

    application.add_handler(
        CallbackQueryHandler(admin_callback, pattern="^admin_")
    )

    application.add_handler(
        CallbackQueryHandler(back_to_main, pattern="^back_to_main$")
    )

    # ===== QUESTION SUBMISSION CONVERSATION HANDLER =====
    question_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_question_start, pattern="^add_question$")
        ],
        states={
            SUBJECT: [
                CallbackQueryHandler(subject_callback, pattern="^sub_")
            ],
            CLASS_: [
                CallbackQueryHandler(class_callback, pattern="^class_")
            ],
            CHAPTER: [
                CallbackQueryHandler(chapter_callback, pattern="^chapter_"),
                CallbackQueryHandler(chapter_page, pattern="^chap_"),
            ],
            QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_question)
            ],
            NEXT_ACTION: [
                CallbackQueryHandler(next_action_callback, pattern="^(next_q|done_q)$")
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.COMMAND, cancel)
        ],
        allow_reentry=True,
        per_user=True,
        per_chat=False,
    )

    application.add_handler(question_conv)

    # ===== CHAPTER QUIZ HANDLERS =====
    application.add_handler(chapter_quiz_conv)
    application.add_handler(CommandHandler("stopquiz", stop_quiz_command))
    application.add_handler(CallbackQueryHandler(quiz_cancel, pattern="^quiz_cancel"))

    # ===== SUFFIX INPUT HANDLER =====
    application.add_handler(
        MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_suffix_input)
    )

    # ===== CUSTOM TIME INPUT HANDLER =====
    application.add_handler(
        MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_custom_time_input)
    )

    # ===== BOT ADDED/REMOVED HANDLERS =====
    application.add_handler(
        ChatMemberHandler(bot_added_to_group, ChatMemberHandler.MY_CHAT_MEMBER)
    )
    application.add_handler(
        ChatMemberHandler(bot_removed_from_group, ChatMemberHandler.MY_CHAT_MEMBER)
    )
    application.add_handler(
        ChatMemberHandler(track_groups, ChatMemberHandler.MY_CHAT_MEMBER)
    )
    application.add_handler(
        MessageHandler(filters.ChatType.GROUPS, track_groups)
    )

    application.add_error_handler(error_handler)

    logger.info("🤖 Bot started")

    # 🔥 FIX: Start scheduler directly using asyncio.create_task
    # This ensures it runs in the background after the bot starts
    loop = asyncio.get_event_loop()
    asyncio.create_task(start_scheduler(application.bot))

    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
