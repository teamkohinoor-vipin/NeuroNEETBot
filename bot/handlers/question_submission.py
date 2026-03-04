from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.error import BadRequest
from bot.database.models import create_pending_batch, add_question_to_batch, get_pending_batch
from bot.utils.validators import validate_question
from bot.config import ADMIN_ID, subject_menu, class_menu, chapter_menu, CHAPTERS
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
    context.user_data.clear()

    if update.effective_chat.type != "private":
        if update.message:
            await update.message.reply_text("This command is only available in private chat.")
        return ConversationHandler.END

    reply_markup = subject_menu()

    if update.callback_query:
        query = update.callback_query
        await query.answer()
        try:
            await query.edit_message_text(
                "📚 *Choose a subject:*",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        except BadRequest:
            pass
    else:
        await update.message.reply_text(
            "📚 *Choose a subject:*",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    return SUBJECT

# ================= SUBJECT =================

async def subject_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    subject = query.data.split("_")[1]
    context.user_data[TEMP_SUBJECT] = subject

    reply_markup = class_menu(subject)

    try:
        await query.edit_message_text(
            f"📘 *Select class for {subject}:*",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except BadRequest:
        pass
    return CLASS_

# ================= CLASS =================

async def class_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("_")
    subject = data[1]

    # If data length is 2, it's a "back to class menu" request (without class number)
    if len(data) == 2:
        # Clear any previously selected class
        context.user_data.pop(TEMP_CLASS, None)
        reply_markup = class_menu(subject)
        try:
            await query.edit_message_text(
                f"📘 *Select class for {subject}:*",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        except BadRequest:
            pass
        return CLASS_

    # Normal class selection with class number
    class_no = int(data[2])
    context.user_data[TEMP_SUBJECT] = subject
    context.user_data[TEMP_CLASS] = class_no

    reply_markup = chapter_menu(subject, class_no, page=0)

    try:
        await query.edit_message_text(
            f"📖 *Select chapter for {subject} Class {class_no}:*",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except BadRequest:
        pass
    return CHAPTER

# ================= CHAPTER (with pagination) =================

async def chapter_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("_")

    # 🔙 Back to subject menu
    if query.data == "subject_menu":
        reply_markup = subject_menu()
        try:
            await query.edit_message_text(
                "📚 *Choose a subject:*",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        except BadRequest:
            pass
        return SUBJECT

    # 🔙 Back to class menu (callback: class_subject)
    if data[0] == "class" and len(data) == 2:
        subject = data[1]
        context.user_data.pop(TEMP_CLASS, None)
        reply_markup = class_menu(subject)
        try:
            await query.edit_message_text(
                f"📘 *Select class for {subject}:*",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        except BadRequest:
            pass
        return CLASS_

    # ⬅️➡️ Pagination (chap_subject_class_page)
    if data[0] == "chap":
        subject = data[1]
        class_no = int(data[2])
        page = int(data[3])
        reply_markup = chapter_menu(subject, class_no, page)
        try:
            await query.edit_message_text(
                f"📖 *Select chapter for {subject} Class {class_no}:*",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        except BadRequest:
            pass
        return CHAPTER

    # ✅ Chapter selection (chapter_subject_class_index)
    if data[0] == "chapter":
        subject = data[1]
        class_no = int(data[2])
        chap_index = int(data[3])

        # Get chapter name from CHAPTERS dict
        chapter = CHAPTERS[subject][class_no][chap_index]
        context.user_data[TEMP_CHAPTER] = chapter

        # Create pending batch
        batch_id = await create_pending_batch(
            user_id=update.effective_user.id,
            subject=subject,
            class_=class_no,
            chapter=chapter
        )
        context.user_data[BATCH_ID] = batch_id

        try:
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
        except BadRequest:
            pass
        return QUESTION

    # Fallback
    await query.answer("Invalid selection")
    return CHAPTER

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

    from telegram import InlineKeyboardButton
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
        try:
            await query.edit_message_text("Send the next question:")
        except BadRequest:
            pass
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

        try:
            await query.edit_message_text(
                "📨 *Your question has been sent for admin review.*\n\nAfter approval, it will be added to the quiz system.",
                parse_mode="Markdown"
            )
        except BadRequest:
            pass

        context.user_data.clear()
        return ConversationHandler.END

# ================= CANCEL =================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Question submission cancelled.")
    context.user_data.clear()
    return ConversationHandler.END
