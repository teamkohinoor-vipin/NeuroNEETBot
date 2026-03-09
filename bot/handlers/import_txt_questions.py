import re
from telegram import Update
from telegram.ext import ContextTypes
from bot.database.models import add_question
from bot.database.db import db

# users in import mode
import_mode = set()


# start import command
async def import_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    import_mode.add(user_id)

    await update.message.reply_text(
        "📂 TXT Import Mode Started\n\n"
        "Send TXT files to import questions.\n"
        "You can send multiple files.\n\n"
        "Stop with /stopimport"
    )


# stop import
async def stop_import(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id in import_mode:
        import_mode.remove(user_id)

    await update.message.reply_text("🛑 TXT Import Mode Stopped")


# txt file handler
async def import_txt_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in import_mode:
        return

    if not update.message.document:
        return

    file = await update.message.document.get_file()
    content = await file.download_as_bytearray()

    text = content.decode("utf-8")

    subject = None
    chapter = None

    # detect subject and chapter
    for line in text.splitlines():

        if line.lower().startswith("subject:"):
            subject = line.split(":",1)[1].strip()

        if line.lower().startswith("chapter:"):
            chapter = line.split(":",1)[1].strip()

        if subject and chapter:
            break

    if not subject or not chapter:

        await update.message.reply_text(
            "❌ Subject or Chapter missing in file"
        )

        return

    # improved question pattern
    pattern = r"Q:\s*(.*?)\nA[\)\.\-:]?\s*(.*?)\nB[\)\.\-:]?\s*(.*?)\nC[\)\.\-:]?\s*(.*?)\nD[\)\.\-:]?\s*(.*?)\nAnswer:\s*([ABCD])"

    matches = re.findall(pattern, text, re.S)

    if not matches:

        await update.message.reply_text("❌ No questions found in file")
        return

    questions_bulk = []

    for q in matches:

        question = q[0].strip()

        options = [
            q[1].strip(),
            q[2].strip(),
            q[3].strip(),
            q[4].strip()
        ]

        correct_index = ["A","B","C","D"].index(q[5])

        data = {
            "question": question,
            "options": options,
            "correct_index": correct_index,
            "subject": subject,
            "chapter": chapter,
            "approved": True
        }

        questions_bulk.append(data)

    # ⚡ BULK INSERT (FAST)
    if questions_bulk:
        await db.db.questions.insert_many(questions_bulk)

    await update.message.reply_text(
        f"✅ {len(questions_bulk)} questions imported\n"
        f"📚 Subject: {subject}\n"
        f"📖 Chapter: {chapter}"
    )
