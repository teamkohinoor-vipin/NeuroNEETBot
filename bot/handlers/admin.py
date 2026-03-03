from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.database import db
from bot.database.models import get_pending_batch
from bot.config import ADMIN_ID
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

def admin_review_keyboard(batch_id: str, q_index: int, total: int):
    keyboard = [
        [
            InlineKeyboardButton("✅ Accept", callback_data=f"admin_accept_{batch_id}_{q_index}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_{batch_id}_{q_index}"),
            InlineKeyboardButton("🗑️ Delete Q", callback_data=f"admin_deleteq_{batch_id}_{q_index}")  # 👈 New: Delete single question
        ],
        [
            InlineKeyboardButton("🗑️ Delete Batch", callback_data=f"admin_delete_{batch_id}")  # 👈 Delete entire batch
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
    
    if update.effective_user.id != ADMIN_ID:
        await query.edit_message_text("❌ Unauthorized.")
        return

    data = query.data.split("_")
    action = data[1]          # accept, reject, deleteq, delete, next, prev
    batch_id = data[2]
    q_index = int(data[3]) if len(data) > 3 else 0

    batch = await get_pending_batch(ObjectId(batch_id))
    if not batch:
        await query.edit_message_text("❌ Batch not found.")
        return

    # 🗑️ Delete entire batch
    if action == "delete":
        await db.db.pending_batches.delete_one({"_id": ObjectId(batch_id)})
        await query.edit_message_text("✅ Batch deleted permanently.")
        # Notify user
        await context.bot.send_message(
            chat_id=batch["user_id"],
            text="❌ Your question batch was rejected by admin."
        )
        return

    questions = batch.get("questions", [])
    if not questions:
        await query.edit_message_text("No questions in this batch.")
        return

    total = len(questions)

    # ⏭️ Next / ⏮️ Prev navigation
    if action == "next":
        q_index = (q_index + 1) % total
    elif action == "prev":
        q_index = (q_index - 1) % total
    
    # ✅ Accept / ❌ Reject / 🗑️ Delete single question
    elif action in ["accept", "reject", "deleteq"]:
        question = questions[q_index]
        
        if action == "accept":
            question["approved"] = True
            await db.db.questions.insert_one(question)
            await query.answer("✅ Question accepted!")
        
        elif action == "reject":
            await query.answer("❌ Question rejected!")
        
        elif action == "deleteq":  # 👈 Delete single question
            questions.pop(q_index)
            await db.db.pending_batches.update_one(
                {"_id": ObjectId(batch_id)},
                {"$set": {"questions": questions}}
            )
            await query.answer("🗑️ Question deleted!")
            
            if not questions:
                # Batch empty after deletion
                await db.db.pending_batches.delete_one({"_id": ObjectId(batch_id)})
                await query.edit_message_text("✅ All questions processed. Batch closed.")
                await context.bot.send_message(
                    chat_id=batch["user_id"],
                    text="✅ Your question batch has been fully reviewed. Thank you!"
                )
                return
            
            total = len(questions)
            if q_index >= total:
                q_index = total - 1
        
        # For accept/reject, remove question from batch
        if action in ["accept", "reject"]:
            questions.pop(q_index)
            await db.db.pending_batches.update_one(
                {"_id": ObjectId(batch_id)},
                {"$set": {"questions": questions}}
            )
            
            if not questions:
                await db.db.pending_batches.delete_one({"_id": ObjectId(batch_id)})
                await query.edit_message_text("✅ All questions processed. Batch closed.")
                await context.bot.send_message(
                    chat_id=batch["user_id"],
                    text="✅ Your question batch has been fully reviewed. Thank you!"
                )
                return
            
            total = len(questions)
            if q_index >= total:
                q_index = total - 1

    # Show current question
    q = questions[q_index]
    text = (
        f"📝 *Question {q_index+1}/{total}*\n\n"
        f"{q['question']}\n"
        f"A) {q['options'][0]}\n"
        f"B) {q['options'][1]}\n"
        f"C) {q['options'][2]}\n"
        f"D) {q['options'][3]}\n"
        f"✅ *Correct:* {chr(65+q['correct_index'])}\n"
        f"📅 *Year:* {q.get('year', 'N/A')}"
    )
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=admin_review_keyboard(batch_id, q_index, total)
    )
