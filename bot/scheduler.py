from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from pytz import timezone
from telegram import Bot, Poll
import logging
import random
import asyncio
import re

from bot.config import TIMEZONE, QUIZ_INTERVAL_MINUTES
from bot.database.models import get_random_question, log_poll, get_all_groups, get_config, remove_group
from bot.handlers.backup import backup

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone=timezone(TIMEZONE))

last_polls = {}

SUBJECTS = ["Physics", "Chemistry", "Biology"]

# Max length per option allowed by Telegram
MAX_OPTION_LENGTH = 100


def truncate_options(options):
    """Truncate each option to MAX_OPTION_LENGTH characters."""
    return [opt[:MAX_OPTION_LENGTH] for opt in options]


async def send_quiz_to_group(chat_id: int, bot: Bot):
    try:
        subject = random.choice(SUBJECTS)

        question = await get_random_question(subject, chat_id)

        if not question:
            logger.warning(f"No question found for {subject} in group {chat_id}")
            return

        options = question["options"]
        correct_option_id = question["correct_index"]

        # Truncate options if needed
        if any(len(opt) > MAX_OPTION_LENGTH for opt in options):
            options = truncate_options(options)
            logger.debug(f"Truncated options for group {chat_id}")

        # Read suffix from config
        suffix = await get_config("question_suffix", "")
        question_text = question["question"]
        if suffix:
            question_text = f"{question_text} {suffix}"

        # Delete previous poll
        if chat_id in last_polls:
            try:
                await bot.delete_message(chat_id, last_polls[chat_id])
            except Exception as e:
                logger.debug(f"Could not delete previous poll in {chat_id}: {e}")

        # Send new poll
        message = await bot.send_poll(
            chat_id=chat_id,
            question=question_text,
            options=options,
            type=Poll.QUIZ,
            correct_option_id=correct_option_id,
            is_anonymous=False
        )

        last_polls[chat_id] = message.message_id

        await log_poll(
            poll_id=message.poll.id,
            message_id=message.message_id,
            question_id=question["_id"],
            subject=subject,
            chapter=question["chapter"],
            chat_id=chat_id
        )

        logger.info(f"✅ Quiz sent to group {chat_id} ({subject})")

    except Exception as e:
        error_msg = str(e)
        logger.warning(f"Quiz failed in group {chat_id}: {error_msg}")

        # Handle group migration
        match = re.search(r"New chat id: (-\d+)", error_msg)
        if match:
            new_chat_id = int(match.group(1))
            logger.info(f"🔄 Migrating group {chat_id} → {new_chat_id}")
            from bot.database.models import add_group, remove_group
            await remove_group(chat_id)
            await add_group(new_chat_id)
            # Optionally resend immediately to new group
            # await send_quiz_to_group(new_chat_id, bot)
            return

        # Remove group if bot kicked or group deleted
        if "bot was kicked" in error_msg or "group chat was deleted" in error_msg:
            logger.info(f"🗑️ Removing invalid group {chat_id}")
            await remove_group(chat_id)
            return

        # Log other errors
        logger.error(f"Unhandled error for group {chat_id}: {error_msg}", exc_info=True)


async def send_quiz(bot: Bot):
    """Send a quiz to all groups."""
    try:
        groups = await get_all_groups()
        logger.info(f"📋 Found {len(groups)} groups to send quiz")

        if not groups:
            logger.warning("⚠️ No groups found in database. Quiz not sent.")
            return

        for chat_id in groups:
            await send_quiz_to_group(chat_id, bot)
            await asyncio.sleep(0.7)  # avoid rate limits

        logger.info("✅ Quiz sent to all groups")

    except Exception as e:
        logger.error(f"❌ Error in send_quiz: {e}", exc_info=True)


async def send_test_quiz(bot: Bot):
    """Send a test quiz immediately to verify scheduler works."""
    logger.info("🔍 Sending test quiz on startup...")
    await send_quiz(bot)


async def start_scheduler(bot: Bot):
    """Start the scheduler and send an initial test quiz."""
    try:
        if scheduler.running:
            logger.info("⏰ Scheduler already running")
            return

        # Add main quiz job
        scheduler.add_job(
            send_quiz,
            trigger=IntervalTrigger(minutes=QUIZ_INTERVAL_MINUTES),
            args=[bot],
            id="quiz_job",
            replace_existing=True
        )

        # Add backup job (daily)
        scheduler.add_job(
            backup,
            trigger=IntervalTrigger(hours=24),
            args=[None, None],
            id="backup_job",
            replace_existing=True
        )

        scheduler.start()
        logger.info("⏰ Scheduler started successfully!")

        # Immediately send a test quiz to confirm it works
        await send_test_quiz(bot)

    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}", exc_info=True)
