from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from bot.database.models import create_pending_batch, add_question_to_batch, get_pending_batch, question_exists
from bot.utils.validators import validate_question
from bot.config import ADMIN_ID, CHAPTERS, chapter_menu
from bson import ObjectId
import re

SUBJECT, CLASS_, CHAPTER, QUESTION, NEXT_ACTION = range(5)

BATCH_ID = "batch_id"
TEMP_SUBJECT = "temp_subject"
TEMP_CLASS = "temp_class"
TEMP_CHAPTER = "temp_chapter"


# ---------- NORMALIZE QUESTION ----------
def normalize_question(text):

    if not text:
        return ""

    text = text.lower()

    # remove punctuation
    text = re.sub(r"[^\w\s]", " ", text)

    # remove extra spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()
# ---------------------------------------


async def add_question_start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.clear()

    if update.effective_chat.type != "private":
        if update.message:
            await update.message.reply_text(
                "This command is only available in private chat."
            )
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton("⚛️Physics", callback_data="sub_Physics")],
        [InlineKeyboardButton("🧪Chemistry", callback_data="sub_Chemistry")],
        [InlineKeyboardButton("🧬Biology", callback_data="sub_Biology")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        query = update.callback_query
        await query.answer()

        await query.edit_message_text(
            "📚 Please select the subject given below:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "📚 Please select the subject given below:",
            reply_markup=reply_markup
        )

    return SUBJECT


async def subject_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    subject = query.data.split("_")[1]
    context.user_data[TEMP_SUBJECT] = subject

    keyboard = [
        [InlineKeyboardButton("🔘Class 11", callback_data="class_11")],
        [InlineKeyboardButton("🔘Class 12", callback_data="class_12")]
    ]

    await query.edit_message_text(
        "🎉Please select the class given below:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return CLASS_


async def class_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    class_ = int(query.data.split("_")[1])
    context.user_data[TEMP_CLASS] = class_

    subject = context.user_data[TEMP_SUBJECT]

    await query.edit_message_text(
        "🎯Please Select Chapter Name:",
        reply_markup=chapter_menu(subject, class_, 0)
    )

    return CHAPTER


async def chapter_page(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data.split("_")

    subject = data[1]
    class_ = int(data[2])
    page = int(data[3])

    await query.edit_message_text(
        "🎯Please Select Chapter Name:",
        reply_markup=chapter_menu(subject, class_, page)
    )


async def chapter_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data.split("_")

    subject = data[1]
    class_ = int(data[2])
    index = int(data[3])

    chapter = CHAPTERS[subject][class_][index]

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


async def receive_question(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    batch_id = context.user_data.get(BATCH_ID)

    if not batch_id:
        await update.message.reply_text(
            "Session expired. Start over with /start."
        )
        return ConversationHandler.END

    is_valid, result = validate_question(text)

    if not is_valid:
        await update.message.reply_text(
            f"❌ Invalid format: {result}\n\nPlease try again."
        )
        return QUESTION

    # ---------- SMART DUPLICATE CHECK ----------
    question_text = normalize_question(result["question"])

    exists = await question_exists(question_text)

    if exists:
        await update.message.reply_text(
            "❌ This question already someone uploaded.\nPlease send other question."
        )
        return QUESTION
    # ------------------------------------------

    question_data = {
        "subject": context.user_data[TEMP_SUBJECT],
        "class": context.user_data[TEMP_CLASS],
        "chapter": context.user_data[TEMP_CHAPTER],
        "question": question_text,
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

    await update.message.reply_text(
        "Question saved. What next?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return NEXT_ACTION


async def next_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.data == "next_q":
        await query.edit_message_text("Send the next question:")
        return QUESTION

    batch_id = context.user_data.get(BATCH_ID)
    batch = await get_pending_batch(ObjectId(batch_id))

    from bot.handlers.admin import admin_review_keyboard

    admin_text = (
        f"New question batch from @{update.effective_user.username} "
        f"(ID: {update.effective_user.id})\n"
        f"Subject: {batch['subject']}\n"
        f"Class: {batch['class']}\n"
        f"Chapter: {batch['chapter']}\n"
        f"Total questions: {len(batch['questions'])}"
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=admin_text,
        reply_markup=admin_review_keyboard(
            str(batch_id),
            0,
            len(batch['questions'])
        )
    )

    await query.edit_message_text(
        "📨 Your question has been sent for admin review.\nAfter approval it will be added to quiz system."
    )

    context.user_data.clear()

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("Question submission cancelled.")

    context.user_data.clear()

    return ConversationHandler.END
