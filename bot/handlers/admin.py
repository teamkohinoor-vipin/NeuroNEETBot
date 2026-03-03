from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.database import db as db_module
from bot.database.models import get_pending_batch
from bot.config import ADMIN_ID
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)


# ================= KEYBOARD =================

def admin_review_keyboard(batch_id: str, q_index: int, total: int):
    keyboard = [
        [
            InlineKeyboardButton("✅ Accept Batch", callback_data=f"admin_accept_{batch_id}_{q_index}"),
            InlineKeyboardButton("🗑 Delete Question", callback_data=f"admin_deleteq_{batch_id}_{q_index}")
        ],
        [
            InlineKeyboardButton("❌ Reject Batch", callback_data=f"admin_delete_{batch_id}")
        ],
        [
            InlineKeyboardButton("⏮ Prev", callback_data=f"admin_prev_{batch_id}_{q_index}"),
            InlineKeyboardButton("⏭ Next", callback_data=f"admin_next_{batch_id}_{q_index}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


# ================= CALLBACK =================

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        await query.edit_message_text("❌ You are not authorized.")
        return

    # -------- Safe parsing --------
    parts = query.data.split("_", 2)
    action = parts[1]

    remaining = parts[2]

    if action == "delete":
        batch_id = remaining
        q_index = 0
    else:
        batch_id, q_index = remaining.rsplit("_", 1)
        q_index = int(q_index)

    logger.info(f"Admin action={action}, batch={batch_id}, index={q_index}")

    # -------- Correct DB access --------
    db = db_module.db.db   # IMPORTANT FIX

    batch = await get_pending_batch(ObjectId(batch_id))
    if not batch:
        await query.edit_message_text("❌ Batch not found.")
        return

    submitter_id = batch.get("user_id")

    questions = batch.get("questions", [])
    if not questions:
        await query.edit_message_text("No questions left.")
        return

    total = len(questions)

    # ================= REJECT FULL BATCH =================
    if action == "delete":
        await db.pending_batches.delete_one({"_id": ObjectId(batch_id)})

        await query.edit_message_text("❌ Batch rejected & deleted.")

        try:
            await context.bot.send_message(
                chat_id=submitter_id,
                text="❌ Your question batch was rejected by admin."
            )
        except:
            pass

        return

    # ================= NAVIGATION =================
    if action == "next":
        q_index = (q_index + 1) % total

    elif action == "prev":
        q_index = (q_index - 1) % total

    # ================= ACCEPT OR DELETE SINGLE =================
    elif action in ["accept", "deleteq"]:

        question = questions[q_index]

        if action == "accept":
            question.pop("_id", None)
            question["approved"] = True
            await db.questions.insert_one(question)

        # Remove from batch
        questions.pop(q_index)

        await db.pending_batches.update_one(
            {"_id": ObjectId(batch_id)},
            {"$set": {"questions": questions}}
        )

        # If no questions left → delete batch
        if not questions:
            await db.pending_batches.delete_one({"_id": ObjectId(batch_id)})

            await query.edit_message_text("✅ All questions processed. Batch closed.")

            try:
                await context.bot.send_message(
                    chat_id=submitter_id,
                    text="✅ Your question batch has been fully reviewed."
                )
            except:
                pass

            return

        total = len(questions)
        if q_index >= total:
            q_index = total - 1

    # ================= SHOW CURRENT QUESTION =================

    q = questions[q_index]

    text = (
        f"📝 *Question {q_index+1}/{total}*\n\n"
        f"{q['question']}\n\n"
        f"A) {q['options'][0]}\n"
        f"B) {q['options'][1]}\n"
        f"C) {q['options'][2]}\n"
        f"D) {q['options'][3]}\n\n"
        f"✅ *Correct:* {chr(65+q['correct_index'])}\n"
        f"📅 *Year:* {q.get('year', 'N/A')}"
    )

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=admin_review_keyboard(batch_id, q_index, total)
    )
