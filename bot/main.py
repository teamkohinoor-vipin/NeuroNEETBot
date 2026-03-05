import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    PollAnswerHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ChatMemberHandler
)

from bot.config import BOT_TOKEN
from bot.database.db import connect_db, close_db
from bot.scheduler import start_scheduler
from bot.database.models import add_group

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

# ✅ BACKUP IMPORT
from bot.handlers.backup import backup, restore


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


# -------- AUTO GROUP SAVE --------
async def track_groups(update: Update, context):

    chat = update.effective_chat

    if chat and chat.type in ["group", "supergroup"]:
        await add_group(chat.id)


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

    # ✅ BACKUP COMMANDS
    application.add_handler(CommandHandler("backup", backup))
    application.add_handler(CommandHandler("restore", restore))

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

    application.add_handler(
        CallbackQueryHandler(admin_callback, pattern="^admin_")
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

    # -------- AUTO GROUP TRACK (bot added) --------
    application.add_handler(
        ChatMemberHandler(track_groups, ChatMemberHandler.MY_CHAT_MEMBER)
    )

    # -------- AUTO GROUP TRACK (any message in group) --------
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
