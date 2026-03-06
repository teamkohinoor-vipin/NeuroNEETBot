from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.config import ADMIN_ID
from bot.database.models import get_config, set_config

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin panel command – only for bot owner."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return

    # Get current status of question submission
    question_add_enabled = await get_config("question_add_enabled", True)
    status_text = "✅ ON" if question_add_enabled else "❌ OFF"

    keyboard = [
        [InlineKeyboardButton(f"Toggle Question Add ({status_text})", callback_data="admin_toggle_question")],
        [InlineKeyboardButton("Close", callback_data="admin_close")]
    ]
    await update.message.reply_text(
        "🛠 *Admin Panel*\n\nUse buttons to control features.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callbacks from admin panel."""
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        await query.edit_message_text("❌ Not authorized.")
        return

    if query.data == "admin_toggle_question":
        current = await get_config("question_add_enabled", True)
        await set_config("question_add_enabled", not current)
        new_status = "✅ ON" if not current else "❌ OFF"
        await query.edit_message_text(
            f"Question submission toggled to {new_status}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Back to Panel", callback_data="admin_panel_back")
            ]])
        )
    elif query.data == "admin_panel_back":
        # Re‑show panel
        question_add_enabled = await get_config("question_add_enabled", True)
        status_text = "✅ ON" if question_add_enabled else "❌ OFF"
        keyboard = [
            [InlineKeyboardButton(f"Toggle Question Add ({status_text})", callback_data="admin_toggle_question")],
            [InlineKeyboardButton("Close", callback_data="admin_close")]
        ]
        await query.edit_message_text(
            "🛠 *Admin Panel*\n\nUse buttons to control features.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif query.data == "admin_close":
        await query.delete_message()
