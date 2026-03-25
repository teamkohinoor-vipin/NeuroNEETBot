from telegram import Update
from telegram.ext import ContextTypes
from bot.database.db import db
from bot.config import ADMIN_ID


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    # Total documents in users collection
    total_docs = await db.db.users.count_documents({})
    
    # Unique users
    unique_users = await db.db.users.distinct("user_id")
    users_count = len(unique_users)

    groups = await db.db.groups.count_documents({})
    questions = await db.db.questions.count_documents({})
    pending = await db.db.pending_batches.count_documents({"status": "pending"})

    stats_db = await db.db.command("dbStats")
    db_size = round(stats_db["dataSize"] / (1024 * 1024), 2)

    # If duplicates exist, show warning
    duplicate_msg = ""
    if total_docs != users_count:
        duplicate_msg = f"\n⚠️ Duplicate entries: {total_docs - users_count} extra"

    text = (
        "📊 NeuroNEETBot Stats\n\n"
        f"👥 Users : {users_count}{duplicate_msg}\n"
        f"👥 Groups : {groups}\n"
        f"🧠 Questions : {questions}\n"
        f"📝 Pending Batches : {pending}\n"
        f"💾 Database Size : {db_size} MB"
    )

    await update.message.reply_text(text)
