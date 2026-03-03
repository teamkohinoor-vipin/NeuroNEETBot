from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from bot.database.models import create_pending_batch, add_question_to_batch, get_pending_batch
from bot.utils.validators import validate_question
from bot.config import ADMIN_ID, CHAPTERS
from bson import ObjectId

# States
SUBJECT, CLASS_, CHAPTER, QUESTION, NEXT_ACTION = range(5)

# Temp keys
BATCH_ID = "batch_id"
TEMP_SUBJECT = "temp_subject"
TEMP_CLASS = "temp_class"
TEMP_CHAPTER = "temp_chapter"


# ================= START ENTRY =================

async def add_question_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 🧹 Clear any previous conversation data to avoid state conflicts
    context.user_data.clear()

    if update.effective_chat.type != "private":
        if update.message:
            await update.message.reply_text("This command is only available in private chat.")
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton("Physics", callback_data="sub_Physics")],
        [InlineKeyboardButton("Chemistry", callback_data="sub_Chemistry")],
        [InlineKeyboardButton("Biology", callback_data="sub_Biology")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("Select subject:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Select subject:", reply_markup=reply_markup)

    return SUBJECT


# ================= SUBJECT =================

async def subject_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    subject = query.data.split("_")[1]
    context.user_data[TEMP_SUBJECT] = subject

    keyboard = [
        [InlineKeyboardButton("Class 11", callback_data="class_11")],
        [InlineKeyboardButton("Class 12", callback_data="class_12")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("Select class:", reply_markup=reply_markup)
    return CLASS_


# ================= CLASS =================

async def class_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    class_ = int(query.data.split("_")[1])
    context.user_data[TEMP_CLASS] = class_

    subject = context.user_data[TEMP_SUBJECT]
    chapters = CHAPTERS.get(subject, {}).get(class_, [])

    if not chapters:
        await query.edit_message_text("No chapters available for this subject/class.")
        return ConversationHandler.END

    keyboard = []
    row = []

    for ch in chapters:
        row.append(InlineKeyboardButton(ch, callback_data=f"chap_{ch}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Select chapter:", reply_markup=reply_markup)

    return CHAPTER


# ================= CHAPTER =================

async def chapter_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chapter = query.data.split("_", 1)[1]
    context.user_data[TEMP_CHAPTER] = chapter

    batch_id = await create_pending_batch(
        user_id=update.effective_user.id,
        subject=context.user_data[TEMP_SUBJECT],
        class_=context.user_data[TEMP_CLASS],
        chapter=chapter
    )

    context.user_data[BATCH_ID] = batch_id

    await query.edit_message_text(
        "Now send your question in this strict format:\n\n"
        "Q: Question text\n"
        "A) Option 1\n"
        "B) Option 2\n"
        "C) Option 3\n"
        "D) Option 4\n"
        "Answer: A\n"
        "Year: 2024 (optional)\n\n"
        "Send the question as a single message."
    )

    return QUESTION


# ================= RECEIVE QUESTION =================

async def receive_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    batch_id = context.user_data.get(BATCH_ID)

    if not batch_id:
        await update.message.reply_text("Session expired. Start over with /start.")
        return ConversationHandler.END

    is_valid, result = validate_question(text)

    if not is_valid:
        await update.message.reply_text(f"❌ Invalid format: {result}\n\nPlease try again.")
        return QUESTION

    question_data = {
        "subject": context.user_data[TEMP_SUBJECT],
        "class": context.user_data[TEMP_CLASS],
        "chapter": context.user_data[TEMP_CHAPTER],
        "question": result["question"],
        "options": result["options"],
        "correct_index": result["correct_index"],
        "year": result.get("year"),
        "approved": False,
        "submitted_by": update.effective_user.id
    }

    await add_question_to_batch(ObjectId(batch_id), question_data)

    keyboard = [
        [InlineKeyboardButton("➕ Next Question", callback_data="next_q")],
        [InlineKeyboardButton("✅ Done", callback_data="done_q")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Question saved. What next?", reply_markup=reply_markup)

    return NEXT_ACTION


# ================= NEXT ACTION =================

async def next_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action = query.data

    if action == "next_q":
        await query.edit_message_text("Send the next question:")
        return QUESTION

    else:  # done_q
        batch_id = context.user_data.get(BATCH_ID)

        batch = await get_pending_batch(ObjectId(batch_id))
        if not batch:
            await query.edit_message_text("Batch not found.")
            return ConversationHandler.END

        from bot.handlers.admin import admin_review_keyboard

        admin_text = (
            f"New question batch from @{update.effective_user.username} "
            f"(ID: {update.effective_user.id})\n"
            f"Subject: {batch['subject']}\n"
            f"Class: {batch['class']}\n"
            f"Chapter: {batch['chapter']}\n"
            f"Total questions: {len(batch['questions'])}\n\n"
            "Use buttons to review."
        )

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            reply_markup=admin_review_keyboard(str(batch_id), 0, len(batch['questions']))
        )

        await query.edit_message_text(
            "📨 *Your question has been sent for admin review.*\n\nAfter approval, it will be added to the quiz system.",
            parse_mode="Markdown"
        )

        context.user_data.clear()
        return ConversationHandler.END


# ================= CANCEL =================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Question submission cancelled.")
    context.user_data.clear()
    return ConversationHandler.END
