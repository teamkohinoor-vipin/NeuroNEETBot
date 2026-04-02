async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    cursor = db.db.users.find({}, {"user_id": 1})

    real_users = 0
    deleted = 0

    async for u in cursor:
        try:
            # 🔥 BEST CHECK
            await context.bot.send_chat_action(u["user_id"], "typing")
            real_users += 1

        except:
            # ❌ dead user remove
            await db.db.users.delete_one({"user_id": u["user_id"]})
            deleted += 1

    groups = await db.db.groups.count_documents({})
    questions = await db.db.questions.count_documents({})
    pending = await db.db.pending_batches.count_documents({"status": "pending"})

    stats_db = await db.db.command("dbStats")
    db_size = round(stats_db["dataSize"] / (1024 * 1024), 2)

    text = (
        "📊 NeuroNEETBot Stats\n\n"
        f"👥 Users : {real_users}\n"
        f"🧹 Removed Fake : {deleted}\n"
        f"👥 Groups : {groups}\n"
        f"🧠 Questions : {questions}\n"
        f"📝 Pending Batches : {pending}\n"
        f"💾 Database Size : {db_size} MB"
    )

    await update.message.reply_text(text)
