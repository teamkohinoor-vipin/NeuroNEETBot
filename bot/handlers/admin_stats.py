from telegram import Update
from telegram.ext import ContextTypes
from bot.database.db import db
from bot.config import ADMIN_ID


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    users = await db.db.users.count_documents({})
    questions = await db.db.questions.count_documents({})
    pending = await db.db.pending_batches.count_documents({"status": "pending"})
    groups = await db.db.groups.count_documents({})

    stats = await db.db.command("dbStats")
    db_size = round(stats["dataSize"] / (1024 * 1024), 2)

    text = (
        "📊 NeuroNEETBot Stats\n\n"
        f"👥 Users : {users}\n"
        f"👥 Groups : {groups}\n"
        f"🧠 Questions : {questions}\n"
        f"📝 Pending Batches : {pending}\n"
        f"💾 Database Size : {db_size} MB"
    )

    await update.message.reply_text(text)
