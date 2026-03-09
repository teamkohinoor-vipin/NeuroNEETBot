from telegram import Update
from telegram.ext import ContextTypes
from bot.database.models import reset_database
from bot.config import ADMIN_ID


async def reset_database_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not allowed to use this command.")
        return

    result = await reset_database()

    text = (
        "⚠ Database Reset Completed\n\n"
        f"Questions Deleted: {result['questions']}\n"
        f"Poll Logs Deleted: {result['poll_logs']}\n"
        f"Answers Deleted: {result['answers']}\n"
        f"Pending Batches Deleted: {result['pending_batches']}\n\n"
        "Groups Preserved ✅"
    )

    await update.message.reply_text(text)
