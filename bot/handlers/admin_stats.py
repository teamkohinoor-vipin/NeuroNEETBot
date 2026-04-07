from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import Forbidden, BadRequest
from bot.database.db import db
from bot.config import ADMIN_ID


# 🔥 REAL USER COUNT + AUTO CLEAN
async def get_real_users(context):

    cursor = db.db.users.find({}, {"user_id": 1})

    real_users = 0

    async for user in cursor:
        try:
            await context.bot.get_chat(user["user_id"])
            real_users += 1

        except (Forbidden, BadRequest):
            # ❌ fake / blocked user हटाओ
            await db.db.users.delete_one({"user_id": user["user_id"]})

    return real_users


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    users = await get_real_users(context)

    groups = await db.db.groups.count_documents({})
    questions = await db.db.questions.count_documents({})
    pending = await db.db.pending_batches.count_documents({"status": "pending"})

    stats_db = await db.db.command("dbStats")
    db_size = round(stats_db["dataSize"] / (1024 * 1024), 2)

    text = (
        "📊 NeuroNEETBot Stats\n\n"
        f"👥 Users : {users}\n"
        f"👥 Groups : {groups}\n"
        f"🧠 Questions : {questions}\n"
        f"📝 Pending Batches : {pending}\n"
        f"💾 Database Size : {db_size} MB"
    )

    await update.message.reply_text(text)
