from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import RetryAfter
from bot.database import db as db_module
from bot.database.models import get_pending_batch
from bot.config import ADMIN_ID
from bson import ObjectId
from asyncio import Lock
import asyncio
import logging

logger = logging.getLogger(__name__)
admin_lock = Lock()


# ================= KEYBOARD =================

def admin_review_keyboard(batch_id: str, q_index: int, total: int):
    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Accept",
                callback_data=f"admin_accept_{batch_id}_{q_index}"
            ),
            InlineKeyboardButton(
                "🗑 Delete Q",
                callback_data=f"admin_deleteq_{batch_id}_{q_index}"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ Reject Batch",
                callback_data=f"admin_delete_{batch_id}_0"
            )
        ],
        [
            InlineKeyboardButton(
                "⏮ Prev",
                callback_data=f"admin_prev_{batch_id}_{q_index}"
            ),
            InlineKeyboardButton(
                "⏭ Next",
                callback_data=f"admin_next_{batch_id}_{q_index}"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


# ================= CALLBACK =================

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    try:
        await query.answer()
    except RetryAfter as e:
        await asyncio.sleep(e.retry_after)

    if update.effective_user.id != ADMIN_ID:
        await query.edit_message_text("❌ Not authorized.")
        return

    parts = query.data.split("_")
    if len(parts) < 4:
        await query.answer("Invalid data")
        return

    action = parts[1]
    batch_id = parts[2]
    q_index = int(parts[3])

    async with admin_lock:

        db = db_module.db.db
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

        # ===== Reject Full Batch =====
        if action == "delete":
            await db.pending_batches.delete_one({"_id": ObjectId(batch_id)})

            await query.edit_message_text("❌ Batch rejected.")

            try:
                await context.bot.send_message(
                    chat_id=submitter_id,
                    text="❌ Your question batch was rejected by Admin."
                )
            except:
                pass
            return

        # ===== Navigation =====
        if action == "next":
            q_index = (q_index + 1) % total
        elif action == "prev":
            q_index = (q_index - 1) % total

        # ===== Accept / Delete Single =====
        elif action in ["accept", "deleteq"]:

            question = questions[q_index]

            if action == "accept":
                question_copy = question.copy()
                question_copy.pop("_id", None)
                question_copy["approved"] = True
                await db.questions.insert_one(question_copy)

            await db.pending_batches.update_one(
                {"_id": ObjectId(batch_id)},
                {"$pull": {"questions": {"_id": question["_id"]}}}
            )

            # Reload batch
            batch = await get_pending_batch(ObjectId(batch_id))

            if not batch or not batch.get("questions"):
                await db.pending_batches.delete_one({"_id": ObjectId(batch_id)})

                await query.edit_message_text("✅ All questions processed.")

                # 🎉 Acceptance Message
                try:
                    await context.bot.send_message(
                        chat_id=submitter_id,
                        text="🎉 Congratulations 👏\n\nYour questions have been accepted by Admin."
                    )
                except:
                    pass
                return

            questions = batch["questions"]
            total = len(questions)

            if q_index >= total:
                q_index = total - 1

        # ===== Show Question =====
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

        try:
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=admin_review_keyboard(batch_id, q_index, total)
            )
        except:
            await query.message.reply_text(
                text,
                parse_mode="Markdown",
                reply_markup=admin_review_keyboard(batch_id, q_index, total)
            )
