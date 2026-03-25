from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.database.models import get_all_groups
from bot.config import ADMIN_ID

GROUPS_PER_PAGE = 5


async def links(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    group_ids = await get_all_groups()

    if not group_ids:
        await update.message.reply_text("No groups found.")
        return

    context.user_data["groups_list"] = group_ids

    await send_link_page(update, context, page=0)


async def send_link_page(update, context, page):

    group_ids = context.user_data.get("groups_list", [])

    start = page * GROUPS_PER_PAGE
    end = start + GROUPS_PER_PAGE

    groups_slice = group_ids[start:end]

    text = "📢 Bot Groups\n\n"

    for chat_id in groups_slice:
        text += f"Group ID: {chat_id}\n\n"

    keyboard = []
    nav_buttons = []

    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton("⬅️ Back", callback_data=f"links_page_{page-1}")
        )

    if end < len(group_ids):
        nav_buttons.append(
            InlineKeyboardButton("Next ➡️", callback_data=f"links_page_{page+1}")
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=reply_markup
        )


async def link_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    page = int(query.data.split("_")[-1])

    await send_link_page(update, context, page)
