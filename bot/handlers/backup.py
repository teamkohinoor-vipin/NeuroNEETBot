import json
import io
import asyncio
import tempfile
import os
from telegram import Update
from telegram.ext import ContextTypes
from bot.database.db import db
from bot.config import MONGO_URI, ADMIN_ID
from bson import ObjectId
from datetime import datetime
import logging
import pymongo

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


# ===== HEAVY WORK IN THREAD =====
# 🔥 PASS LOOP AS PARAMETER – NO get_event_loop() INSIDE THREAD
def do_backup_sync(status_msg, message, loop):
    """Synchronous backup – runs in a separate thread."""
    try:
        client = pymongo.MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=60000,
            connectTimeoutMS=60000,
            socketTimeoutMS=60000
        )
        backup_db = client["neetquiz"]

        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write('{\n')
            first_collection = True

            collections = [
                "questions",
                "users",
                "groups",
                "answers",
                "poll_logs",
                "pending_batches"
            ]
            stats = {}

            for col_name in collections:
                asyncio.run_coroutine_threadsafe(
                    status_msg.edit_text(f"⏳ Backing up {col_name}..."),
                    loop
                )
                logger.info(f"Backing up {col_name}")

                count = backup_db[col_name].count_documents({})
                stats[col_name] = count

                if not first_collection:
                    tmp_file.write(',\n')
                first_collection = False

                tmp_file.write(f'  "{col_name}": [\n')
                first_doc = True

                cursor = backup_db[col_name].find({}).batch_size(1000)
                doc_count = 0
                for doc in cursor:
                    doc = convert_data(doc)
                    if not first_doc:
                        tmp_file.write(',\n')
                    first_doc = False
                    json.dump(doc, tmp_file, default=str)
                    doc_count += 1
                    if doc_count % 100 == 0:
                        tmp_file.flush()

                tmp_file.write('\n  ]')
                logger.info(f"Finished {col_name} ({count} records)")

            tmp_file.write('\n}\n')
            tmp_file.flush()

        client.close()

        with open(tmp_path, 'rb') as f:
            file_data = f.read()
        file_bytes = io.BytesIO(file_data)
        file_bytes.name = "neuroneetbot_backup.json"

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

        asyncio.run_coroutine_threadsafe(status_msg.delete(), loop)
        asyncio.run_coroutine_threadsafe(
            message.reply_document(document=file_bytes, caption=caption, parse_mode="Markdown"),
            loop
        )

        os.unlink(tmp_path)
        logger.info("✅ Backup completed")
        return True

    except Exception as e:
        logger.error(f"❌ Backup error: {e}", exc_info=True)
        asyncio.run_coroutine_threadsafe(
            status_msg.edit_text(f"❌ Backup error:\n{str(e)}"),
            loop
        )
        return False


# ===== BACKUP COMMAND =====
async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        await message.reply_text("❌ Admin only command")
        return

    status_msg = await message.reply_text("⏳ Creating backup... This may take a few minutes. I'll send it when ready.")

    loop = asyncio.get_running_loop()
    # 🔥 Pass loop as argument – thread will use this instead of get_event_loop()
    await loop.run_in_executor(None, do_backup_sync, status_msg, message, loop)


# ===== RESTORE =====
async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        await message.reply_text("❌ Admin only command")
        return

    document = message.document
    if not document:
        await message.reply_text("📤 Please send a backup JSON file to restore the database.")
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
        collections = [
            "questions",
            "users",
            "groups",
            "answers",
            "poll_logs",
            "pending_batches"
        ]

        for collection in collections:
            if collection in data:
                for doc in data[collection]:
                    doc.pop("_id", None)
                    await db.db[collection].insert_one(doc)
                    total += 1
                logger.info(f"✅ Restored {len(data[collection])} records to {collection}")

        await status_msg.delete()
        await message.reply_text(
            f"✅ *Restore Complete*\n\n"
            f"📊 {total} records inserted.\n"
            f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode="Markdown"
        )

        logger.info(f"✅ Restore completed: {total} records inserted")

    except json.JSONDecodeError as e:
        await message.reply_text(f"❌ Invalid JSON file:\n{str(e)}")
    except Exception as e:
        logger.error(f"❌ Restore error: {e}", exc_info=True)
        await message.reply_text(f"❌ Restore error:\n{str(e)}")
