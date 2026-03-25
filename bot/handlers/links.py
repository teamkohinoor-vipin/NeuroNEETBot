from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.database.models import get_all_groups
from bot.config import ADMIN_ID
from bot.database.db import db
import asyncio
import logging
import math

logger = logging.getLogger(__name__)

GROUPS_PER_PAGE = 5


async def links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    msg = await update.message.reply_text("⏳ Loading group links...")
    asyncio.create_task(load_and_display_links(msg, context))


async def load_and_display_links(message, context):
    try:
        group_ids = await get_all_groups()
        if not group_ids:
            await message.edit_text("No groups found.")
            return

        await fetch_group_details(group_ids, context.bot)

        valid_ids = await get_active_group_ids(context.bot, group_ids)
        if not valid_ids:
            await message.edit_text("No active groups found.")
            return

        context.user_data["group_ids"] = valid_ids
        await display_page(message, context, page=0)
    except Exception as e:
        logger.error(f"Error loading links: {e}")
        await message.edit_text("❌ Failed to load group links.")


async def fetch_group_details(group_ids, bot):
    semaphore = asyncio.Semaphore(5)

    async def fetch_one(chat_id):
        async with semaphore:
            existing = await db.db.groups.find_one({"chat_id": chat_id})
            if existing and existing.get("title") and existing.get("invite_link"):
                return

            try:
                chat = await asyncio.wait_for(bot.get_chat(chat_id), timeout=3)
                title = chat.title
                try:
                    link = await asyncio.wait_for(bot.export_chat_invite_link(chat_id), timeout=3)
                except:
                    link = "❌ Link not available"
                await db.db.groups.update_one(
                    {"chat_id": chat_id},
                    {"$set": {"title": title, "invite_link": link}},
                    upsert=True
                )
            except Exception as e:
                logger.info(f"Removing group {chat_id} (bot not present)")
                await db.db.groups.delete_one({"chat_id": chat_id})

    await asyncio.gather(*[fetch_one(cid) for cid in group_ids])


async def get_active_group_ids(bot, all_ids):
    valid = []
    for cid in all_ids:
        try:
            await asyncio.wait_for(bot.get_chat(cid), timeout=2)
            valid.append(cid)
        except:
            await db.db.groups.delete_one({"chat_id": cid})
    return valid


async def display_page(message_or_query, context, page):
    group_ids = context.user_data.get("group_ids")
    if not group_ids:
        group_ids = await get_active_group_ids(context.bot, await get_all_groups())
        context.user_data["group_ids"] = group_ids

    total = len(group_ids)
    if total == 0:
        await edit_text(message_or_query, "No active groups found.")
        return

    start = page * GROUPS_PER_PAGE
    end = min(start + GROUPS_PER_PAGE, total)
    page_groups = group_ids[start:end]

    text = "📢 *Bot Group Links*\n\n"
    for idx, cid in enumerate(page_groups, start=start+1):
        group_data = await db.db.groups.find_one({"chat_id": cid})
        if group_data:
            title = group_data.get("title", "Unknown Group")
            link = group_data.get("invite_link", "❌ Link not available")
        else:
            title = "Unknown Group"
            link = "❌ Link not available"
        text += f"{idx}. *{title}*\n{link}\n\n"

    # Pagination buttons with explicit page numbers
    total_pages = math.ceil(total / GROUPS_PER_PAGE)
    keyboard = []
    if total_pages > 1:
        # Calculate previous and next page numbers with wrap-around
        prev_page = (page - 1) % total_pages
        next_page = (page + 1) % total_pages
        nav = [
            InlineKeyboardButton("⬅️ Back", callback_data=f"links_page_{prev_page}"),
            InlineKeyboardButton("Next ➡️", callback_data=f"links_page_{next_page}")
        ]
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


async def link_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Extract target page from callback data
    page = int(query.data.split("_")[-1])  # format: links_page_<page>

    group_ids = context.user_data.get("group_ids")
    if not group_ids:
        # If context data missing, reload from DB
        group_ids = await get_active_group_ids(context.bot, await get_all_groups())
        context.user_data["group_ids"] = group_ids

    total = len(group_ids)
    if total == 0:
        await query.edit_message_text("No active groups found.")
        return

    total_pages = math.ceil(total / GROUPS_PER_PAGE)
    # Ensure page is within valid range (should be, but just in case)
    page = page % total_pages

    await display_page(query, context, page)
