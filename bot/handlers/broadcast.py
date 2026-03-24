from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.error import Forbidden, BadRequest
from bot.config import ADMIN_ID
from bot.database.db import db
from bot.database.models import get_all_groups
import asyncio

# 🔴 GLOBAL FLAG
broadcast_running = False


# 🔘 BUTTONS
def get_buttons():
    keyboard = [
        [InlineKeyboardButton("➕ Add Bot", url="https://t.me/NeuroNEETBot?startgroup=true")],
        [InlineKeyboardButton("📢 Support Channel", url="https://t.me/TeamKohinoorOfficial7")]
    ]
    return InlineKeyboardMarkup(keyboard)


# 🔥 FIXED SEND (AUTO CLEAN USERS)
async def send_message_with_buttons(context, chat_id, msg):
    try:
        await context.bot.copy_message(
            chat_id=chat_id,
            from_chat_id=msg.chat_id,
            message_id=msg.message_id,
            reply_markup=get_buttons()
        )
        return True

    except Forbidden:
        await db.db.users.delete_one({"user_id": chat_id})
        return False

    except BadRequest:
        await db.db.users.delete_one({"user_id": chat_id})
        return False

    except Exception:
        return False


# ================= USER BROADCAST =================
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

    # 🔥 OPTIMIZED USER FETCH
    cursor = db.db.users.find({}, {"user_id": 1})
    users = []
    async for u in cursor:
        users.append(u)

    sent = 0
    failed = 0

    batch_size = 20   # 🔥 FIXED

    await update.message.reply_text(f"🚀 User Broadcast Started\n👥 Total Users: {len(users)}")

    for i in range(0, len(users), batch_size):

        if not broadcast_running:
            break

        batch = users[i:i + batch_size]

        tasks = []
        for user in batch:
            if not broadcast_running:
                break
            tasks.append(send_message_with_buttons(context, user["user_id"], msg))

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
        f"❌ Failed: {failed}"
    )


# ================= GROUP BROADCAST =================
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

    sent = 0
    failed = 0

    batch_size = 20   # 🔥 FIXED

    await update.message.reply_text(f"🚀 Group Broadcast Started\n👥 Total Groups: {len(groups)}")

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
        f"❌ Failed: {failed}"
    )


# ================= STOP =================
async def stopbroadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global broadcast_running

    if update.effective_user.id != ADMIN_ID:
        return

    if not broadcast_running:
        await update.message.reply_text("❌ No active broadcast")
        return

    broadcast_running = False

    await update.message.reply_text("🛑 Broadcast stopping..."
