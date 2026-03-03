from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from bot.config import GROUP_ID, ADMIN_ID

def group_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_chat.id != GROUP_ID:
            await update.message.reply_text("This command can only be used in the official group.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

def private_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_chat.type != "private":
            await update.message.reply_text("This command is only available in private chat.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper

def admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_user.id != ADMIN_ID:
            await update.message.reply_text("You are not authorized.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper