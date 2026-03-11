from telegram import Update
from telegram.ext import ContextTypes
from bot.database.models import get_all_groups
from bot.config import ADMIN_ID


async def groups(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    group_ids = await get_all_groups()

    if not group_ids:
        await update.message.reply_text("No groups found.")
        return

    text = "📢 Bot Groups\n\n"

    for chat_id in group_ids:

        try:

            chat = await context.bot.get_chat(chat_id)

            try:
                link = await context.bot.export_chat_invite_link(chat_id)
            except:
                link = "No invite link permission"

            text += f"{chat.title}\n{link}\n\n"

        except:
            continue

    await update.message.reply_text(text)
