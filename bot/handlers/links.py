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

    msg = await update.message.reply_text("⏳ Loading group links...")

    # 🔥 background task (bot free रहेगा)
    asyncio.create_task(load_links(msg, context))


# ===== LOAD IN BACKGROUND =====
async def load_links(message, context):

    group_ids = await get_all_groups()

    if not group_ids:
        await message.edit_text("No groups found.")
        return

    context.user_data["groups_list"] = group_ids

    await send_link_page_from_message(message, context, page=0)


# ===== SAFE GET CHAT =====
async def safe_get_chat(context, chat_id):
    try:
        return await asyncio.wait_for(
            context.bot.get_chat(chat_id),
            timeout=2
        )
    except:
        return None


# ===== PAGE SYSTEM (MAIN) =====
async def send_link_page_from_message(message, context, page):

    group_ids = context.user_data.get("groups_list", [])

    valid_groups = []

    for chat_id in group_ids:

        chat = await safe_get_chat(context, chat_id)

        if not chat:
            valid_groups.append(("Unknown Group", "❌ Link not available"))
            continue

        group_data = await db.db.groups.find_one({"chat_id": chat_id})

        if group_data and group_data.get("invite_link"):
            link = group_data["invite_link"]
        else:
            try:
                link = await asyncio.wait_for(
                    context.bot.export_chat_invite_link(chat_id),
                    timeout=2
                )

                await db.db.groups.update_one(
                    {"chat_id": chat_id},
                    {"$set": {"invite_link": link}},
                    upsert=True
                )

            except:
                link = "❌ Link not available"

        valid_groups.append((chat.title, link))

        await asyncio.sleep(0.03)   # 🔥 anti-freeze


    # ===== PAGINATION =====
    start = page * GROUPS_PER_PAGE
    end = start + GROUPS_PER_PAGE

    groups_slice = valid_groups[start:end]

    text = "📢 Bot Group Links\n\n"

    for title, link in groups_slice:
        text += f"{title}\n{link}\n\n"


    # ===== BUTTONS =====
    keyboard = []
    nav_buttons = []

    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton("⬅️ Back", callback_data=f"links_page_{page-1}")
        )

    if end < len(valid_groups):
        nav_buttons.append(
            InlineKeyboardButton("Next ➡️", callback_data=f"links_page_{page+1}")
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await message.edit_text(
            text,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    except:
        pass


# ===== CALLBACK =====
async def link_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    page = int(query.data.split("_")[-1])

    # ⚠️ callback में normal function use करो
    await send_link_page(update, context, page)


# ===== CALLBACK PAGE FUNCTION =====
async def send_link_page(update, context, page):

    group_ids = context.user_data.get("groups_list", [])

    valid_groups = []

    for chat_id in group_ids:

        chat = await safe_get_chat(context, chat_id)

        if not chat:
            valid_groups.append(("Unknown Group", "❌ Link not available"))
            continue

        group_data = await db.db.groups.find_one({"chat_id": chat_id})

        if group_data and group_data.get("invite_link"):
            link = group_data["invite_link"]
        else:
            try:
                link = await asyncio.wait_for(
                    context.bot.export_chat_invite_link(chat_id),
                    timeout=2
                )

                await db.db.groups.update_one(
                    {"chat_id": chat_id},
                    {"$set": {"invite_link": link}},
                    upsert=True
                )

            except:
                link = "❌ Link not available"

        valid_groups.append((chat.title, link))


    start = page * GROUPS_PER_PAGE
    end = start + GROUPS_PER_PAGE

    groups_slice = valid_groups[start:end]

    text = "📢 Bot Group Links\n\n"

    for title, link in groups_slice:
        text += f"{title}\n{link}\n\n"


    keyboard = []
    nav_buttons = []

    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton("⬅️ Back", callback_data=f"links_page_{page-1}")
        )

    if end < len(valid_groups):
        nav_buttons.append(
            InlineKeyboardButton("Next ➡️", callback_data=f"links_page_{page+1}")
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    except:
        pass
