import json
import io
from telegram import Update
from telegram.ext import ContextTypes
from bot.database.db import db
from bot.config import ADMIN_ID


async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = update.effective_message

    if update.effective_user.id != ADMIN_ID:
        await message.reply_text("❌ Admin only command")
        return

    try:

        data = {}

        collections = [
            "questions",
            "users",
            "groups",
            "answers",
            "poll_logs",
            "pending_batches"
        ]

        stats = {}

        for col in collections:

            data[col] = []

            cursor = db.db[col].find({})

            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                data[col].append(doc)

            stats[col] = len(data[col])

        backup_json = json.dumps(data, indent=2)

        file = io.BytesIO(backup_json.encode())
        file.name = "neuroneetbot_backup.json"

        caption = (
            "📦 Database Backup\n\n"
            f"🧠 Questions : {stats['questions']}\n"
            f"👥 Users : {stats['users']}\n"
            f"📢 Groups : {stats['groups']}\n"
            f"📝 Answers : {stats['answers']}\n"
            f"📊 Poll Logs : {stats['poll_logs']}\n"
            f"⏳ Pending Batches : {stats['pending_batches']}"
        )

        await message.reply_document(
            document=file,
            caption=caption
        )

    except Exception as e:

        await message.reply_text(f"Backup error:\n{e}")


async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = update.effective_message

    if update.effective_user.id != ADMIN_ID:
        await message.reply_text("❌ Admin only command")
        return

    document = message.document

    if not document:
        await message.reply_text("Send backup JSON file.")
        return

    file = await document.get_file()

    data_bytes = await file.download_as_bytearray()

    data = json.loads(data_bytes.decode())

    total = 0

    for collection, docs in data.items():

        for doc in docs:

            doc.pop("_id", None)

            await db.db[collection].insert_one(doc)

            total += 1

    await message.reply_text(
        f"✅ Restore complete\n\n{total} records inserted."
    )
