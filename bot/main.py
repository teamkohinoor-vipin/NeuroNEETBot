import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    PollAnswerHandler,
    MessageHandler,
    filters,
    ChatMemberHandler,
    ContextTypes
)

from bot.config import BOT_TOKEN, SUPPORT_CHANNEL, DEVELOPER_USERNAME
from bot.database.db import connect_db, close_db
from bot.scheduler import start_scheduler
from bot.database.models import add_group, get_config

from bot.handlers.start import start, help_callback, help_page
from bot.handlers.leaderboard import leaderboard, leaderboard_callback
from bot.handlers.poll_answer import poll_answer

from bot.handlers.admin import admin_callback
from bot.handlers.error import error_handler

from bot.handlers.admin_stats import stats
from bot.handlers.broadcast import broadcast

from bot.handlers.backup import backup, restore
from bot.handlers.reset_database import reset_database_command
from bot.handlers.admin_panel import admin_panel, admin_panel_callback

from bot.handlers.import_txt_questions import (
    import_command,
    stop_import,
    import_txt_questions
)

from bot.handlers.groups import groups, group_page_callback


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# ---------------- GROUP TRACK ---------------- #

async def track_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat = update.effective_chat

    if not chat:
        return

    if chat.type not in ["group", "supergroup"]:
        return

    try:
        await add_group(chat.id)
    except Exception as e:
        logger.warning(f"group save failed: {e}")


# ---------------- BACK TO MAIN ---------------- #

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

        keyboard = [
            [InlineKeyboardButton("❓ Help", callback_data="help")],
            [add_group_button],
            [InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{DEVELOPER_USERNAME}")],
            [InlineKeyboardButton("📢 Support Channel", url=f"https://t.me/{SUPPORT_CHANNEL}")]
        ]

    else:

        keyboard = [
            [InlineKeyboardButton("❓ Help", callback_data="help")],
            [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard_menu")],
        ]

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ---------------- MAIN ---------------- #

def main():

    application = Application.builder().token(BOT_TOKEN).build()

    application.post_init = connect_db
    application.post_shutdown = close_db

    if application.job_queue:
        application.job_queue.run_once(
            lambda ctx: start_scheduler(ctx.bot),
            when=5
        )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("broadcast", broadcast))

    application.add_handler(CommandHandler("groups", groups))

    application.add_handler(
        CallbackQueryHandler(group_page_callback, pattern="^group_page_")
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

    application.add_handler(
        CallbackQueryHandler(help_callback, pattern="^help$")
    )

    application.add_handler(
        CallbackQueryHandler(help_page, pattern="^help_")
    )

    application.add_handler(
        CommandHandler("leaderboard", leaderboard)
    )

    application.add_handler(
        CallbackQueryHandler(leaderboard_callback, pattern="^leaderboard_")
    )

    application.add_handler(
        PollAnswerHandler(poll_answer)
    )

    application.add_handler(CommandHandler("adminpanel", admin_panel))

    application.add_handler(
        CallbackQueryHandler(admin_panel_callback, pattern="^admin_(toggle|panel|close)")
    )

    application.add_handler(
        CallbackQueryHandler(admin_callback, pattern="^admin_")
    )

    application.add_handler(
        CallbackQueryHandler(back_to_main, pattern="^back_to_main$")
    )

    # BOT ADD GROUP SAVE
    application.add_handler(
        ChatMemberHandler(track_groups, ChatMemberHandler.MY_CHAT_MEMBER)
    )

    # MESSAGE DETECT GROUP SAVE
    application.add_handler(
        MessageHandler(filters.ALL & filters.ChatType.GROUPS, track_groups)
    )

    application.add_error_handler(error_handler)

    logger.info("🤖 Bot started")

    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
