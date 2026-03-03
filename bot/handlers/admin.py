from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.database import db as db_module  # db_module = Database instance
from bot.database.models import get_pending_batch
from bot.config import ADMIN_ID
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

def admin_review_keyboard(batch_id: str, q_index: int, total: int):
    keyboard = [
        [
            InlineKeyboardButton("✅ Accept", callback_data=f"admin_accept_{batch_id}_{q_index}"),
            InlineKeyboardButton("🗑️ Delete Q", callback_data=f"admin_deleteq_{batch_id}_{q_index}")
        ],
        [
            InlineKeyboardButton("🗑️ Delete Batch", callback_data=f"admin_delete_{batch_id}")
        ],
        [
            InlineKeyboardButton("⏭️ Next", callback_data=f"admin_next_{batch_id}_{q_index}"),
            InlineKeyboardButton("⏮️ Prev", callback_data=f"admin_prev_{batch_id}_{q_index}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    logger.info(f"🔔 Admin callback received: {query.data}")

    if update.effective_user.id != ADMIN_ID:
        logger.warning(f"❌ Unauthorized attempt by user {update.effective_user.id}")
        await query.edit_message_text("❌ You are not authorized to perform this action.")
        return

    data = query.data.split("_")
    action = data[1]
    batch_id = data[2]
    q_index = int(data[3]) if len(data) > 3 else 0

    logger.info(f"📦 Parsed: action={action}, batch_id={batch_id}, q_index={q_index}")

    batch = await get_pending_batch(ObjectId(batch_id))
    if not batch:
        await query.edit_message_text("❌ Batch not found. It may have been already processed.")
        return

    # ✅ Correct database access
    db = db_module.db  # actual MongoDB database

    # Submitter info
    submitter_id = batch.get("user_id", "Unknown")
    submitter_name = "Unknown"
    try:
        user = await db.users.find_one({"user_id": submitter_id})
        if user:
            submitter_name = user.get("username") or user.get("first_name") or f"ID: {submitter_id}"
        else:
            submitter_name = f"ID: {submitter_id}"
    except Exception as e:
        logger.error(f"❌ Error fetching user info: {e}")

    # 🗑️ Delete entire batch
    if action == "delete":
        try:
            await db_module.db.pending_batches.delete_one({"_id": ObjectId(batch_id)})
            await query.edit_message_text("✅ Batch deleted permanently.")
            await context.bot.send_message(
                chat_id=submitter_id,
                text="❌ Your question batch was rejected by admin."
            )
            logger.info(f"🗑️ Batch {batch_id} deleted by admin")
        except Exception as e:
            logger.error(f"❌ Error deleting batch: {e}")
            await query.edit_message_text("❌ Failed to delete batch.")
        return

    questions = batch.get("questions", [])
    if not questions:
        await query.edit_message_text("No questions in this batch.")
        return

    total = len(questions)
    if q_index < 0 or q_index >= total:
        q_index = 0

    # Navigation
    if action == "next":
        q_index = (q_index + 1) % total
    elif action == "prev":
        q_index = (q_index - 1) % total

    # Accept / Delete single question
    elif action in ["accept", "deleteq"]:
        question = questions[q_index]

        if action == "accept":
            try:
                question["approved"] = True
                await db.questions.insert_one(question)
                await query.answer("✅ Question accepted!")
                logger.info(f"✅ Question accepted: {question.get('question', '')[:50]}")
            except Exception as e:
                logger.error(f"❌ Error accepting question: {e}")
                await query.answer("❌ Failed to accept question.")
                return
        else:  # deleteq
            await query.answer("🗑️ Question deleted!")
            logger.info(f"🗑️ Question deleted from batch: {question.get('question', '')[:50]}")

        # Remove question from batch
        questions.pop(q_index)
        try:
            await db_module.db.pending_batches.update_one(
                {"_id": ObjectId(batch_id)},
                {"$set": {"questions": questions}}
            )
        except Exception as e:
            logger.error(f"❌ Error updating batch: {e}")
            await query.edit_message_text("❌ Failed to update batch.")
            return

        # If batch becomes empty, delete it
        if not questions:
            try:
                await db_module.db.pending_batches.delete_one({"_id": ObjectId(batch_id)})
                await query.edit_message_text("✅ All questions processed. Batch closed.")
                await context.bot.send_message(
                    chat_id=submitter_id,
                    text="✅ Your question batch has been fully reviewed. Thank you!"
                )
            except Exception as e:
                logger.error(f"❌ Error closing batch: {e}")
                await query.edit_message_text("❌ Failed to close batch.")
            return

        total = len(questions)
        if q_index >= total:
            q_index = total - 1

    # Show current question
    q = questions[q_index]
    text = (
        f"👤 *Submitted by:* {submitter_name}\n"
        f"🆔 *User ID:* `{submitter_id}`\n\n"
        f"📝 *Question {q_index+1}/{total}*\n\n"
        f"{q['question']}\n"
        f"A) {q['options'][0]}\n"
        f"B) {q['options'][1]}\n"
        f"C) {q['options'][2]}\n"
        f"D) {q['options'][3]}\n"
        f"✅ *Correct:* {chr(65+q['correct_index'])}\n"
        f"📅 *Year:* {q.get('year', 'N/A')}"
    )

    try:
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=admin_review_keyboard(batch_id, q_index, total)
        )
    except Exception as e:
        logger.error(f"❌ Error displaying question: {e}")
        await query.edit_message_text("❌ An error occurred while displaying the question.")
