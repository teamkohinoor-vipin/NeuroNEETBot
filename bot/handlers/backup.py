import json
import io
from telegram import Update
from telegram.ext import ContextTypes
from bot.database.db import db
from bot.config import ADMIN_ID
from bson import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


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

        status_msg = await message.reply_text("⏳ Creating backup... Please wait.")

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

        # 🔥 FIX: default=str to handle any non-serializable data
        backup_json = json.dumps(data, indent=2, default=str)

        file = io.BytesIO(backup_json.encode('utf-8'))
        file.name = "neuroneetbot_backup.json"

        caption = (
            "📦 *Database Backup*\n\n"
            f"🧠 Questions : {stats['questions']}\n"
            f"👥 Users : {stats['users']}\n"
            f"📢 Groups : {stats['groups']}\n"
            f"📝 Answers : {stats['answers']}\n"
            f"📊 Poll Logs : {stats['poll_logs']}\n"
            f"⏳ Pending Batches : {stats['pending_batches']}\n\n"
            f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        await status_msg.delete()

        await message.reply_document(
            document=file,
            caption=caption,
            parse_mode="Markdown"
        )

        logger.info(f"Backup completed: {sum(stats.values())} total records")

    except Exception as e:

        logger.error(f"Backup error: {e}", exc_info=True)
        await message.reply_text(f"❌ Backup error:\n{str(e)}")


# -------- RESTORE DATABASE --------
async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = update.effective_message

    if update.effective_user.id != ADMIN_ID:
        await message.reply_text("❌ Admin only command")
        return

    document = message.document

    if not document:
        await message.reply_text("❌ Send backup JSON file.")
        return

    if not document.file_name.endswith('.json'):
        await message.reply_text("❌ Please send a .json file.")
        return

    try:

        status_msg = await message.reply_text("⏳ Restoring database... Please wait.")

        file = await document.get_file()
        data_bytes = await file.download_as_bytearray()
        data = json.loads(data_bytes.decode('utf-8'))

        total = 0
        collections = ["questions", "users", "groups", "answers", "poll_logs", "pending_batches"]

        for collection in collections:
            if collection in data:
                for doc in data[collection]:
                    doc.pop("_id", None)
                    await db.db[collection].insert_one(doc)
                    total += 1

        await status_msg.delete()

        await message.reply_text(
            f"✅ *Restore Complete*\n\n"
            f"📊 {total} records inserted.\n"
            f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode="Markdown"
        )

        logger.info(f"Restore completed: {total} records inserted")

    except json.JSONDecodeError as e:
        await message.reply_text(f"❌ Invalid JSON file:\n{str(e)}")
    except Exception as e:
        logger.error(f"Restore error: {e}", exc_info=True)
        await message.reply_text(f"❌ Restore error:\n{str(e)}")
