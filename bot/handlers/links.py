from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.database.models import get_all_groups
from bot.config import ADMIN_ID
from bot.database.db import db
import asyncio

GROUPS_PER_PAGE = 5


# ===== COMMAND =====
async def links(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text("⏳ Loading group links...")

    # background load (bot freeze नहीं होगा)
    asyncio.create_task(load_links(update, context))


# ===== LOAD GROUPS =====
async def load_links(update, context):

    group_ids = await get_all_groups()

    if not group_ids:
        await update.message.reply_text("No groups found.")
        return

    context.user_data["groups_list"] = group_ids

    await send_link_page(update, context, page=0)


# ===== PAGE SYSTEM =====
async def send_link_page(update, context, page):

    group_ids = context.user_data.get("groups_list", [])

    start = page * GROUPS_PER_PAGE
    end = start + GROUPS_PER_PAGE

    groups_slice = group_ids[start:end]

    text = "📢 *Bot Group Links*\n\n"

    for chat_id in groups_slice:

        try:
            chat = await context.bot.get_chat(chat_id)

            # 🔥 CHECK DB FIRST
            group_data = await db.db.groups.find_one({"chat_id": chat_id})

            if group_data and group_data.get("invite_link"):
                link = group_data["invite_link"]
            else:
                try:
                    link = await context.bot.export_chat_invite_link(chat_id)

                    # SAVE LINK
                    await db.db.groups.update_one(
                        {"chat_id": chat_id},
                        {"$set": {"invite_link": link}},
                        upsert=True
                    )
                except:
                    link = "No invite link permission"

            # ===== FORMAT =====
            text += f"{chat.title}\n{link}\n\n"

            await asyncio.sleep(0.05)  # anti-rate limit

        except:
            continue

    # ===== BUTTONS =====
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
            parse_mode="Markdown",
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )


# ===== CALLBACK =====
async def link_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    page = int(query.data.split("_")[-1])

    await send_link_page(update, context, page)
