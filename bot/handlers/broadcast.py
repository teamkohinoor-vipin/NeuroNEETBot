from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.error import Forbidden, BadRequest
from bot.config import ADMIN_ID
from bot.database.db import db
from bot.database.models import get_all_groups
import asyncio

broadcast_running = False


def get_buttons():
    keyboard = [
        [InlineKeyboardButton("➕ Add Bot", url="https://t.me/NeuroNEETBot?startgroup=true")],
        [InlineKeyboardButton("📢 Support Channel", url="https://t.me/TeamKohinoorOfficial7")]
    ]
    return InlineKeyboardMarkup(keyboard)


async def send_message_with_buttons(context, chat_id, msg):
    try:
        await context.bot.copy_message(
            chat_id=chat_id,
            from_chat_id=msg.chat_id,
            message_id=msg.message_id,
            reply_markup=get_buttons()
        )
        return True
    except (Forbidden, BadRequest):
        # Remove invalid user
        await db.db.users.delete_one({"user_id": chat_id})
        return False
    except Exception:
        return False


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global broadcast_running

    if update.effective_user.id != ADMIN_ID:
        return

    if broadcast_running:
        await update.message.reply_text("⚠️ Broadcast already running")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Reply to a message to broadcast")
        return

    broadcast_running = True

    msg = update.message.reply_to_message

    # ✅ Fetch unique user IDs (avoid duplicates)
    unique_users = await db.db.users.distinct("user_id")
    total_users = len(unique_users)

    await update.message.reply_text(f"🚀 User Broadcast Started\n👥 Total Users: {total_users}")

    sent = 0
    failed = 0
    batch_size = 20

    for i in range(0, total_users, batch_size):
        if not broadcast_running:
            break
        batch = unique_users[i:i + batch_size]
        tasks = []
        for user_id in batch:
            if not broadcast_running:
                break
            tasks.append(send_message_with_buttons(context, user_id, msg))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if r is True:
                sent += 1
            else:
                failed += 1
        await asyncio.sleep(0.05)

    broadcast_running = False
    await update.message.reply_text(
        f"📊 User Broadcast Completed/Stopped\n\n"
        f"✅ Sent: {sent}\n"
        f"❌ Failed: {failed}\n"
        f"📊 Total Users: {total_users}"
    )


async def group_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global broadcast_running

    if update.effective_user.id != ADMIN_ID:
        return

    if broadcast_running:
        await update.message.reply_text("⚠️ Broadcast already running")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Reply to a message to broadcast")
        return

    broadcast_running = True

    msg = update.message.reply_to_message
    groups = await get_all_groups()
    total_groups = len(groups)

    await update.message.reply_text(f"🚀 Group Broadcast Started\n👥 Total Groups: {total_groups}")

    sent = 0
    failed = 0
    batch_size = 20

    for i in range(0, len(groups), batch_size):
        if not broadcast_running:
            break
        batch = groups[i:i + batch_size]
        tasks = []
        for chat_id in batch:
            if not broadcast_running:
                break
            tasks.append(send_message_with_buttons(context, chat_id, msg))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if r is True:
                sent += 1
            else:
                failed += 1
        await asyncio.sleep(0.05)

    broadcast_running = False
    await update.message.reply_text(
        f"📊 Group Broadcast Completed/Stopped\n\n"
        f"✅ Sent: {sent}\n"
        f"❌ Failed: {failed}\n"
        f"📊 Total Groups: {total_groups}"
    )


async def stopbroadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global broadcast_running
    if update.effective_user.id != ADMIN_ID:
        return
    if not broadcast_running:
        await update.message.reply_text("❌ No active broadcast")
        return
    broadcast_running = False
    await update.message.reply_text("🛑 Broadcast stop requested. It will stop after current batch.")
