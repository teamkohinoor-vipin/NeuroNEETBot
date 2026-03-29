from telegram import Update
from telegram.ext import ContextTypes
from bot.config import ADMIN_ID
from bot.database.db import db

async def clean_duplicate_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove duplicate user entries (admin only)"""
    if update.effective_user.id != ADMIN_ID:
        return

    msg = await update.message.reply_text("🧹 Cleaning duplicate users...")

    # Find all user_ids that appear more than once
    pipeline = [
        {"$group": {"_id": "$user_id", "count": {"$sum": 1}, "docs": {"$push": "$_id"}}},
        {"$match": {"count": {"$gt": 1}}}
    ]
    cursor = db.db.users.aggregate(pipeline)

    deleted = 0
    async for doc in cursor:
        keep = doc["docs"][0]
        to_delete = doc["docs"][1:]
        for _id in to_delete:
            await db.db.users.delete_one({"_id": _id})
            deleted += 1

    unique_count = len(await db.db.users.distinct("user_id"))
    await msg.edit_text(
        f"✅ Removed {deleted} duplicate user entries.\n"
        f"👥 Unique users now: {unique_count}"
    )
