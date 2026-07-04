from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.config import ADMIN_ID
from bot.database.models import get_config, set_config


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return

    question_add_enabled = await get_config("question_add_enabled", True)
    question_status = "✅ ON" if question_add_enabled else "❌ OFF"

    answer_mentions = await get_config("answer_mentions", True)
    mention_status = "✅ ON" if answer_mentions else "❌ OFF"

    score_lifetime = await get_config("score_message_lifetime", 10)
    time_display = f"{score_lifetime}s"

    current_suffix = await get_config("question_suffix", "")
    suffix_display = current_suffix if current_suffix else "None"

    keyboard = [
        [InlineKeyboardButton(f"Toggle Question Add ({question_status})", callback_data="admin_toggle_question")],
        [InlineKeyboardButton(f"Answer Mentions ({mention_status})", callback_data="admin_toggle_mentions")],
        [InlineKeyboardButton(f"⏱️ Score Msg Delete ({time_display})", callback_data="admin_set_time")],
        [InlineKeyboardButton(f"✏️ Question Suffix ({suffix_display})", callback_data="admin_set_suffix")],
        [InlineKeyboardButton("Close", callback_data="admin_close")]
    ]

    await update.message.reply_text(
        "🛠 *Admin Panel*\n\nUse buttons to control features.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def admin_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    elif query.data == "admin_toggle_mentions":
        current = await get_config("answer_mentions", True)
        await set_config("answer_mentions", not current)
        new_status = "✅ ON" if not current else "❌ OFF"
        await query.edit_message_text(
            f"Answer mentions toggled to {new_status}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Back to Panel", callback_data="admin_panel_back")
            ]])
        )

    elif query.data == "admin_set_time":
        keyboard = [
            [InlineKeyboardButton("5 seconds", callback_data="admin_time_5")],
            [InlineKeyboardButton("10 seconds", callback_data="admin_time_10")],
            [InlineKeyboardButton("30 seconds", callback_data="admin_time_30")],
            [InlineKeyboardButton("60 seconds (1 min)", callback_data="admin_time_60")],
            [InlineKeyboardButton("300 seconds (5 min)", callback_data="admin_time_300")],
            [InlineKeyboardButton("✏️ Custom", callback_data="admin_time_custom")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_panel_back")]
        ]
        await query.edit_message_text(
            "⏱️ *Select score message delete time:*\n\n"
            "After answering a poll, the score update message will be deleted after this time.\n"
            "You can also choose 'Custom' and type your own time (e.g., `10 sec`, `1 min`, `5 min`).",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data.startswith("admin_time_") and query.data != "admin_time_custom":
        seconds = int(query.data.split("_")[2])
        await set_config("score_message_lifetime", seconds)
        await query.edit_message_text(
            f"✅ Score message delete time set to **{seconds} seconds**.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Panel", callback_data="admin_panel_back")
            ]])
        )

    elif query.data == "admin_time_custom":
        context.user_data["waiting_for_custom_time"] = True
        await query.edit_message_text(
            "✏️ *Please type your desired time.*\n\n"
            "Examples:\n"
            "`10 sec`\n"
            "`30 seconds`\n"
            "`1 min`\n"
            "`5 minutes`\n"
            "`2 mins`\n\n"
            "You can also type just a number (will be treated as seconds).\n"
            "Type `/cancel` to cancel.",
            parse_mode="Markdown"
        )

    elif query.data == "admin_set_suffix":
        # Clear any previous waiting state
        context.user_data["waiting_for_suffix"] = True
        # Also store that we are in suffix mode in a separate key to avoid conflicts
        context.user_data["suffix_mode"] = True
        await query.edit_message_text(
            "✏️ *Please type the suffix you want to add to every question.*\n\n"
            "Examples:\n"
            "`[Team Kohinoor]`\n"
            "`#NEETQuiz`\n"
            "`Powered by NeuroNEET`\n\n"
            "Type `none` to remove suffix.\n"
            "Type `/cancel` to cancel.",
            parse_mode="Markdown"
        )

    elif query.data == "admin_panel_back":
        question_add_enabled = await get_config("question_add_enabled", True)
        question_status = "✅ ON" if question_add_enabled else "❌ OFF"

        answer_mentions = await get_config("answer_mentions", True)
        mention_status = "✅ ON" if answer_mentions else "❌ OFF"

        score_lifetime = await get_config("score_message_lifetime", 10)
        time_display = f"{score_lifetime}s"

        current_suffix = await get_config("question_suffix", "")
        suffix_display = current_suffix if current_suffix else "None"

        keyboard = [
            [InlineKeyboardButton(f"Toggle Question Add ({question_status})", callback_data="admin_toggle_question")],
            [InlineKeyboardButton(f"Answer Mentions ({mention_status})", callback_data="admin_toggle_mentions")],
            [InlineKeyboardButton(f"⏱️ Score Msg Delete ({time_display})", callback_data="admin_set_time")],
            [InlineKeyboardButton(f"✏️ Question Suffix ({suffix_display})", callback_data="admin_set_suffix")],
            [InlineKeyboardButton("Close", callback_data="admin_close")]
        ]

        await query.edit_message_text(
            "🛠 *Admin Panel*\n\nUse buttons to control features.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "admin_close":
        await query.delete_message()
