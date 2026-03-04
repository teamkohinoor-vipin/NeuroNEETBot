from telegram import Update
from telegram.ext import ContextTypes
from bot.config import ADMIN_ID
from bot.database.db import db


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text(
            "Usage:\n/broadcast your message"
        )
        return

    message = " ".join(context.args)

    users_cursor = db.db.users.find({})
    users = await users_cursor.to_list(length=None)

    sent = 0
    failed = 0

    for user in users:

        try:

            await context.bot.send_message(
                chat_id=user["user_id"],
                text=f"📢 NeuroNEETBot Announcement\n\n{message}"
            )

            sent += 1

        except:

            failed += 1

    await update.message.reply_text(
        f"Broadcast Complete\n\nSent: {sent}\nFailed: {failed}"
    )
