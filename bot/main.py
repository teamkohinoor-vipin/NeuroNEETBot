import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    PollAnswerHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ChatMemberHandler,
    ContextTypes
)

from bot.config import BOT_TOKEN, SUPPORT_CHANNEL, DEVELOPER_USERNAME
from bot.database.db import connect_db, close_db
from bot.scheduler import start_scheduler
from bot.database.models import add_group, get_config

from bot.handlers.start import start, help_callback
from bot.handlers.leaderboard import leaderboard, leaderboard_callback
from bot.handlers.poll_answer import poll_answer

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
from bot.handlers.broadcast import broadcast

# BACKUP
from bot.handlers.backup import backup, restore

# RESET DATABASE
from bot.handlers.reset_database import reset_database_command

# ADMIN PANEL
from bot.handlers.admin_panel import admin_panel, admin_panel_callback

# ✅ TXT IMPORT FEATURE (NEW)
from bot.handlers.import_txt_questions import import_txt_questions


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


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user = query.from_user.first_name
    chat_type = query.message.chat.type

    question_enabled = await get_config("question_add_enabled", True)

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

    add_group_button = InlineKeyboardButton(
        "📢 Add Bot to Group",
        url=f"https://t.me/{context.bot.username}?startgroup=true"
    )

    if chat_type == "private":

        keyboard_buttons = [
            [InlineKeyboardButton("❓ Help", callback_data="help")],
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

    # BACKUP
    application.add_handler(CommandHandler("backup", backup))
    application.add_handler(CommandHandler("restore", restore))

    # RESET DATABASE
    application.add_handler(CommandHandler("resetdatabase", reset_database_command))

    # restore file accept
    application.add_handler(
        MessageHandler(filters.Document.ALL, restore)
    )

    # ✅ TXT QUESTION IMPORT
    application.add_handler(
        MessageHandler(filters.Document.FileExtension("txt"), import_txt_questions)
    )

    application.add_handler(
        CallbackQueryHandler(help_callback, pattern="^help$")
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

    conv_handler = ConversationHandler(

        entry_points=[
            CommandHandler("addquestion", add_question_start),
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

                CallbackQueryHandler(
                    chapter_page,
                    pattern="^chap_"
                ),

                CallbackQueryHandler(
                    chapter_callback,
                    pattern="^chapter_"
                )

            ],

            QUESTION: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    receive_question
                )
            ],

            NEXT_ACTION: [
                CallbackQueryHandler(
                    next_action_callback,
                    pattern="^(next_q|done_q)$"
                )
            ]

        },

        fallbacks=[
            CommandHandler("cancel", cancel)
        ],

        per_user=True,
        per_chat=True,
        allow_reentry=True,
        conversation_timeout=600
    )

    application.add_handler(conv_handler)

    application.add_handler(
        ChatMemberHandler(track_groups, ChatMemberHandler.MY_CHAT_MEMBER)
    )

    application.add_handler(
        MessageHandler(filters.ChatType.GROUPS, track_groups)
    )

    application.add_handler(
        CallbackQueryHandler(unmatched_callback)
    )

    application.add_error_handler(error_handler)

    logger.info("🤖 Bot started")

    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
