import re
from telegram import Update
from telegram.ext import ContextTypes
from bot.database.models import add_question


async def import_txt_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.document:
        return

    document = update.message.document

    # get file from telegram
    file = await document.get_file()

    content = await file.download_as_bytearray()

    text = content.decode("utf-8")

    # chapter name = filename
    chapter = document.file_name.replace(".txt", "")

    # question pattern
    pattern = r"Q:\s*(.*?)\nA\s*(.*?)\nB\s*(.*?)\nC\s*(.*?)\nD\s*(.*?)\nAnswer:\s*([ABCD])"

    matches = re.findall(pattern, text, re.S)

    added = 0

    for q in matches:

        question = q[0].strip()

        options = [
            q[1].strip(),
            q[2].strip(),
            q[3].strip(),
            q[4].strip()
        ]

        correct_index = ["A", "B", "C", "D"].index(q[5])

        data = {
            "question": question,
            "options": options,
            "correct_index": correct_index,
            "subject": "Biology",
            "chapter": chapter,
            "approved": True
        }

        await add_question(data)

        added += 1

    await update.message.reply_text(
        f"✅ {added} questions imported\n📚 Chapter: {chapter}"
    )
