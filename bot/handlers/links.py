from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.database.models import get_all_groups
from bot.config import ADMIN_ID
from bot.database.db import db
import asyncio
import logging

logger = logging.getLogger(__name__)

GROUPS_PER_PAGE = 5


# ===== COMMAND =====
async def links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    msg = await update.message.reply_text("⏳ Loading group links...")
    asyncio.create_task(load_and_display_links(msg, context))


# ===== BACKGROUND LOADER =====
async def load_and_display_links(message, context):
    try:
        group_ids = await get_all_groups()
        if not group_ids:
            await message.edit_text("No groups found.")
            return

        context.user_data["group_ids"] = group_ids
        await fetch_group_details(group_ids, context.bot)
        await display_page(message, context, page=0)
    except Exception as e:
        logger.error(f"Error loading links: {e}")
        await message.edit_text("❌ Failed to load group links.")


# ===== FETCH GROUP DETAILS IN PARALLEL =====
async def fetch_group_details(group_ids, bot):
    semaphore = asyncio.Semaphore(5)

    async def fetch_one(chat_id):
        async with semaphore:
            # Check if already in DB
            existing = await db.db.groups.find_one({"chat_id": chat_id})
            if existing and existing.get("invite_link") and existing.get("title"):
                return

            try:
                chat = await asyncio.wait_for(bot.get_chat(chat_id), timeout=3)
                title = chat.title
                link = await asyncio.wait_for(bot.export_chat_invite_link(chat_id), timeout=3)
                await db.db.groups.update_one(
                    {"chat_id": chat_id},
                    {"$set": {"title": title, "invite_link": link}},
                    upsert=True
                )
            except Exception as e:
                logger.warning(f"Could not fetch data for {chat_id}: {e}")
                await db.db.groups.update_one(
                    {"chat_id": chat_id},
                    {"$set": {"title": "Unknown Group", "invite_link": "❌ Link not available"}},
                    upsert=True
                )

    await asyncio.gather(*[fetch_one(cid) for cid in group_ids])


# ===== DISPLAY PAGE (common for both initial and callback) =====
async def display_page(message_or_query, context, page):
    group_ids = context.user_data.get("group_ids")
    if not group_ids:
        group_ids = await get_all_groups()
        context.user_data["group_ids"] = group_ids

    total = len(group_ids)
    if total == 0:
        await edit_text(message_or_query, "No groups found.")
        return

    start = page * GROUPS_PER_PAGE
    end = min(start + GROUPS_PER_PAGE, total)

    page_groups = group_ids[start:end]

    text = "📢 *Bot Group Links*\n\n"
    for cid in page_groups:
        group_data = await db.db.groups.find_one({"chat_id": cid})
        if group_data:
            title = group_data.get("title", "Unknown Group")
            link = group_data.get("invite_link", "❌ Link not available")
        else:
            title = "Unknown Group"
            link = "❌ Link not available"
        text += f"*{title}*\n{link}\n\n"

    # Buttons
    keyboard = []
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Back", callback_data=f"links_page_{page-1}"))
    if end < total:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"links_page_{page+1}"))
    if nav:
        keyboard.append(nav)

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

    await edit_text(message_or_query, text, reply_markup)


async def edit_text(target, text, reply_markup=None):
    if hasattr(target, "edit_message_text"):
        try:
            await target.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup,
                                           disable_web_page_preview=True)
        except Exception as e:
            logger.warning(f"Edit failed: {e}")
    else:
        try:
            await target.edit_text(text, parse_mode="Markdown", reply_markup=reply_markup,
                                   disable_web_page_preview=True)
        except Exception as e:
            logger.warning(f"Edit failed: {e}")


# ===== CALLBACK HANDLER =====
async def link_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    page = int(query.data.split("_")[-1])
    await display_page(query, context, page)
