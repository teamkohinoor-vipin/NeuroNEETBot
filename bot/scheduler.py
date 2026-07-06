from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from pytz import timezone
from telegram import Bot, Poll
import logging
import random
import asyncio
import re

from bot.config import TIMEZONE, QUIZ_INTERVAL_MINUTES
from bot.database.models import get_random_question, log_poll, get_all_groups, get_config, remove_group, add_group
from bot.handlers.backup import backup

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone=timezone(TIMEZONE))

last_polls = {}

SUBJECTS = ["Physics", "Chemistry", "Biology"]

MAX_OPTION_LENGTH = 100


def truncate_options(options):
    return [opt[:MAX_OPTION_LENGTH] for opt in options]


async def send_quiz_to_group(chat_id: int, bot: Bot):
    """Send a single quiz to a group."""
    try:
        logger.info(f"🔄 Sending quiz to group {chat_id}")

        subject = random.choice(SUBJECTS)

        question = await get_random_question(subject, chat_id)

        if not question:
            logger.warning(f"No question found for {subject} in group {chat_id}")
            return

        options = question["options"]
        correct_option_id = question["correct_index"]

        if any(len(opt) > MAX_OPTION_LENGTH for opt in options):
            options = truncate_options(options)
            logger.debug(f"Truncated options for group {chat_id}")

        suffix = await get_config("question_suffix", "")
        suffix_for_groups = await get_config("suffix_for_groups", True)
        
        question_text = question["question"]
        if suffix and suffix_for_groups:
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
        logger.error(f"❌ Quiz failed in group {chat_id}: {error_msg}", exc_info=True)

        # 🔥 Auto‑remove group for all known permission / membership errors
        if ("Not enough rights to send polls" in error_msg or
            "Channel direct messages topic must be specified" in error_msg or
            "bot is not a member" in error_msg or
            "bot was kicked" in error_msg or
            "group chat was deleted" in error_msg):
            
            logger.info(f"🗑️ Removing group {chat_id} due to error: {error_msg[:50]}")
            await remove_group(chat_id)
            return

        # Group migration (Telegram sometimes returns a new chat id)
        match = re.search(r"New chat id: (-\d+)", error_msg)
        if match:
            new_chat_id = int(match.group(1))
            logger.info(f"🔄 Migrating group {chat_id} → {new_chat_id}")
            await remove_group(chat_id)
            await add_group(new_chat_id)
            return

        # Other errors – just log
        logger.error(f"Unhandled error for group {chat_id}: {error_msg}", exc_info=True)


async def send_quiz(bot: Bot):
    """Send quiz to all groups."""
    try:
        groups = await get_all_groups()
        logger.info(f"📋 Found {len(groups)} groups to send quiz")

        if not groups:
            logger.warning("⚠️ No groups found in database. Quiz not sent.")
            return

        for chat_id in groups:
            await send_quiz_to_group(chat_id, bot)
            await asyncio.sleep(0.7)  # Rate limit

        logger.info(f"✅ Quiz sent to all {len(groups)} groups")

    except Exception as e:
        logger.error(f"❌ Error in send_quiz: {e}", exc_info=True)


async def start_scheduler(bot: Bot):
    """Start the scheduler and send an immediate test quiz."""
    try:
        if scheduler.running:
            logger.info("⏰ Scheduler already running")
            return

        # Schedule the quiz job
        scheduler.add_job(
            send_quiz,
            trigger=IntervalTrigger(minutes=QUIZ_INTERVAL_MINUTES),
            args=[bot],
            id="quiz_job",
            replace_existing=True,
            misfire_grace_time=60
        )

        scheduler.add_job(
            backup,
            trigger=IntervalTrigger(hours=24),
            args=[None, None],
            id="backup_job",
            replace_existing=True,
            misfire_grace_time=3600
        )

        scheduler.start()
        logger.info("⏰ Scheduler started successfully!")

        # Immediately send a quiz on startup (one-time) to verify functionality
        logger.info("🔍 Sending initial quiz on startup...")
        await send_quiz(bot)

    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}", exc_info=True)
