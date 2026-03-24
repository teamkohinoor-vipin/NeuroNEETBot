from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import Forbidden, BadRequest
from bot.database.db import db
from bot.config import ADMIN_ID
import asyncio


# ✅ REAL COUNT (FAST + SAFE LIMIT)
async def get_real_user_count(context):

    cursor = db.db.users.find({}, {"user_id": 1})

    real = 0
    checked = 0

    async for u in cursor:

        if checked >= 200:   # ⚡ LIMIT लगा दिया (freeze नहीं होगा)
            break

        try:
            await asyncio.wait_for(
                context.bot.get_chat(u["user_id"]),
                timeout=1.5
            )
            real += 1

        except (Forbidden, BadRequest):
            await db.db.users.delete_one({"user_id": u["user_id"]})

        except:
            continue

        checked += 1

    return real


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    users = await get_real_user_count(context)

    questions = await db.db.questions.count_documents({})
    pending = await db.db.pending_batches.count_documents({"status": "pending"})
    groups = await db.db.groups.count_documents({})

    stats_db = await db.db.command("dbStats")
    db_size = round(stats_db["dataSize"] / (1024 * 1024), 2)

    text = (
        "📊 NeuroNEETBot Stats\n\n"
        f"👥 Users : {users} (approx)\n"
        f"👥 Groups : {groups}\n"
        f"🧠 Questions : {questions}\n"
        f"📝 Pending Batches : {pending}\n"
        f"💾 Database Size : {db_size} MB"
    )

    await update.message.reply_text(text)
