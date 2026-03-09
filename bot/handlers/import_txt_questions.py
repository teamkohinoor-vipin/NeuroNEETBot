from telegram import Update
from telegram.ext import ContextTypes
import re
from bot.database.models import add_question

# user import mode
import_mode = {}


async def import_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    import_mode[user_id] = True

    await update.message.reply_text(
        "📂 Send TXT file to import questions\n\n"
        "Format:\n"
        "Subject: Biology\n"
        "Chapter: Animal Kingdom"
    )


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

    for line in text.splitlines():

        if line.lower().startswith("subject:"):
            subject = line.split(":",1)[1].strip()

        if line.lower().startswith("chapter:"):
            chapter = line.split(":",1)[1].strip()

        if subject and chapter:
            break

    pattern = r"Q:\s*(.*?)\nA\s*(.*?)\nB\s*(.*?)\nC\s*(.*?)\nD\s*(.*?)\nAnswer:\s*([ABCD])"

    matches = re.findall(pattern, text, re.S)

    added = 0

    for q in matches:

        options = [q[1], q[2], q[3], q[4]]

        correct_index = ["A","B","C","D"].index(q[5])

        data = {
            "question": q[0],
            "options": options,
            "correct_index": correct_index,
            "subject": subject,
            "chapter": chapter,
            "approved": True
        }

        await add_question(data)

        added += 1

    import_mode.pop(user_id, None)

    await update.message.reply_text(
        f"✅ {added} questions imported\n"
        f"📚 Subject: {subject}\n"
        f"📖 Chapter: {chapter}"
    )
