import re
from telegram import Update
from telegram.ext import ContextTypes
from bot.database.models import add_question


async def import_txt_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.document:
        return

    file = await update.message.document.get_file()
    content = await file.download_as_bytearray()

    text = content.decode("utf-8")

    subject = None
    chapter = None

    lines = text.splitlines()

    # detect subject + chapter
    for line in lines:

        if line.lower().startswith("subject:"):
            subject = line.split(":",1)[1].strip()

        if line.lower().startswith("chapter:"):
            chapter = line.split(":",1)[1].strip()

        if subject and chapter:
            break

    if not subject or not chapter:
        await update.message.reply_text(
            "❌ File format error\n\n"
            "First lines must contain:\n"
            "Subject: Biology\n"
            "Chapter: Animal Kingdom"
        )
        return

    # question regex
    pattern = r"Q:\s*(.*?)\nA\s*(.*?)\nB\s*(.*?)\nC\s*(.*?)\nD\s*(.*?)\nAnswer:\s*([ABCD])"

    matches = re.findall(pattern, text, re.S)

    if not matches:
        await update.message.reply_text("❌ No questions found in file")
        return

    added = 0

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

        await add_question(data)

        added += 1

    await update.message.reply_text(
        f"✅ {added} questions imported\n\n"
        f"📚 Subject: {subject}\n"
        f"📖 Chapter: {chapter}"
    )
