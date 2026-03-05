import json
import io
from telegram import Update
from telegram.ext import ContextTypes
from bot.database.db import db
from bot.config import ADMIN_ID
from bson import ObjectId
from datetime import datetime


# -------- DATA CONVERTER --------
def convert_data(data):

    if isinstance(data, ObjectId):
        return str(data)

    if isinstance(data, datetime):
        return data.isoformat()

    if isinstance(data, list):
        return [convert_data(i) for i in data]

    if isinstance(data, dict):
        return {k: convert_data(v) for k, v in data.items()}

    return data


# -------- FULL DATABASE BACKUP --------
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

                doc = convert_data(doc)

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


# -------- RESTORE DATABASE --------
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
