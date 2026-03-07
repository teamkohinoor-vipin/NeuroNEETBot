from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from pytz import timezone
from datetime import datetime
from telegram import Bot, Poll
import logging
import random

from bot.config import TIMEZONE, QUIZ_INTERVAL_MINUTES
from bot.database.models import get_random_question, log_poll, get_all_groups

# backup import
from bot.handlers.backup import backup

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone=timezone(TIMEZONE))

last_polls = {}

# PCB subjects
SUBJECTS = ["Physics", "Chemistry", "Biology"]


async def send_quiz(bot: Bot):

    groups = await get_all_groups()

    for chat_id in groups:

        try:

            # random subject
            subject = random.choice(SUBJECTS)

            question = await get_random_question(subject)

            if not question:
                logger.warning(f"No question found for {subject}")
                continue

            options = question["options"]
            correct_option_id = question["correct_index"]

            if chat_id in last_polls:
                try:
                    await bot.delete_message(chat_id, last_polls[chat_id])
                except:
                    pass

            message = await bot.send_poll(
                chat_id=chat_id,
                question=question["question"],
                options=options,
                type=Poll.QUIZ,
                correct_option_id=correct_option_id,
                is_anonymous=False
            )

            last_polls[chat_id] = message.message_id

            # FIXED log_poll
            await log_poll(
                poll_id=message.poll.id,
                message_id=message.message_id,
                question_id=question["_id"],
                subject=subject,
                chapter=question["chapter"],
                chat_id=chat_id
            )

        except Exception as e:
            logger.warning(f"Failed in {chat_id} : {e}")

    logger.info("📊 Quiz sent to all groups")


async def start_scheduler(bot: Bot):

    scheduler.add_job(
        send_quiz,
        trigger=IntervalTrigger(minutes=QUIZ_INTERVAL_MINUTES),
        args=[bot],
        id="quiz_job",
        replace_existing=True
    )

    # daily backup job
    scheduler.add_job(
        backup,
        trigger=IntervalTrigger(hours=24),
        args=[None, None],
        id="backup_job",
        replace_existing=True
    )

    scheduler.start()

    logger.info("⏰ Scheduler started")
