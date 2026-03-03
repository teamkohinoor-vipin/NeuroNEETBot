import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    PollAnswerHandler, ConversationHandler, MessageHandler, filters
)
from bot.config import BOT_TOKEN
from bot.database.db import connect_db, close_db
from bot.scheduler import start_scheduler
from bot.handlers.start import start, help_callback
from bot.handlers.leaderboard import leaderboard, leaderboard_callback
from bot.handlers.poll_answer import poll_answer
from bot.handlers.question_submission import (
    add_question_start, subject_callback, class_callback,
    chapter_callback, receive_question, next_action_callback, cancel,
    SUBJECT, CLASS_, CHAPTER, QUESTION, NEXT_ACTION
)
from bot.handlers.admin import admin_callback
from bot.handlers.error import error_handler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def unmatched_callback(update: Update, context):
    """Fallback for truly unmatched callbacks (debug only)"""
    logger.warning(f"❓ Unmatched callback: {update.callback_query.data}")
    await update.callback_query.answer()


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.post_init = connect_db
    application.post_shutdown = close_db

    # Start scheduler safely
    if application.job_queue:
        application.job_queue.run_once(
            lambda ctx: start_scheduler(ctx.bot), when=5
        )

    # Basic commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(help_callback, pattern="^help$"))

    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(
        CallbackQueryHandler(leaderboard_callback, pattern="^leaderboard_")
    )

    application.add_handler(PollAnswerHandler(poll_answer))

    # 🔥 Conversation Handler (FIXED)
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("addquestion", add_question_start),
            CallbackQueryHandler(add_question_start, pattern="^add_question$")
        ],
        states={
            SUBJECT: [CallbackQueryHandler(subject_callback, pattern="^sub_")],
            CLASS_: [CallbackQueryHandler(class_callback, pattern="^class_")],
            CHAPTER: [CallbackQueryHandler(chapter_callback, pattern="^chap_")],
            QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_question)
            ],
            NEXT_ACTION: [
                CallbackQueryHandler(
                    next_action_callback, pattern="^(next_q|done_q)$"
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
        per_chat=True,
        per_message=True,   # ✅ IMPORTANT FIX
        conversation_timeout=600
    )

    application.add_handler(conv_handler)

    application.add_handler(
        CallbackQueryHandler(admin_callback, pattern="^admin_")
    )

    # 👇 Smart fallback (won't block add_question anymore)
    application.add_handler(
        CallbackQueryHandler(
            unmatched_callback,
            pattern="^(?!add_question$).*"
        )
    )

    application.add_error_handler(error_handler)

    logger.info("🤖 Bot started polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
