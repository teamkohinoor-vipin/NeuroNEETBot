from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from pytz import timezone
from telegram import Bot, Poll
import logging
import random
import time

from bot.config import TIMEZONE, QUIZ_INTERVAL_MINUTES
from bot.database.models import get_random_question, log_poll, get_all_groups
from bot.handlers.poll_answer import score_messages
from bot.handlers.backup import backup

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone=timezone(TIMEZONE))

last_polls = {}
poll_time = {}
last_sent_time = {}

SUBJECTS = ["Physics", "Chemistry", "Biology"]


async def send_quiz(bot: Bot):

    groups = await get_all_groups()

    for chat_id in groups:

        try:

            now = time.time()

            # 🔒 overlap protection (10 sec)
            if chat_id in last_sent_time:
                if now - last_sent_time[chat_id] < 10:
                    continue

            last_sent_time[chat_id] = now

            subject = random.choice(SUBJECTS)

            # ⭐ random + non-repeat question
            question = await get_random_question(subject, chat_id)

            if not question:
                logger.warning(f"No question found for {subject}")
                continue

            options = question["options"]
            correct_option_id = question["correct_index"]

            # 🗑 delete previous poll safely
            if chat_id in last_polls:
                try:
                    if now - poll_time.get(chat_id, 0) > 30:
                        await bot.delete_message(chat_id, last_polls[chat_id])
                except:
                    pass

            # 🗑 delete score messages
            if chat_id in score_messages:

                for msg_id in score_messages[chat_id]:
                    try:
                        await bot.delete_message(chat_id, msg_id)
                    except:
                        pass

                score_messages[chat_id] = []

            # 📊 send new poll
            message = await bot.send_poll(
                chat_id=chat_id,
                question=question["question"],
                options=options,
                type=Poll.QUIZ,
                correct_option_id=correct_option_id,
                is_anonymous=False
            )

            last_polls[chat_id] = message.message_id
            poll_time[chat_id] = time.time()

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

    # 🔒 prevent duplicate scheduler
    if scheduler.running:
        logger.info("Scheduler already running")
        return

    scheduler.add_job(
        send_quiz,
        trigger=IntervalTrigger(minutes=QUIZ_INTERVAL_MINUTES),
        args=[bot],
        id="quiz_job",
        replace_existing=True
    )

    scheduler.add_job(
        backup,
        trigger=IntervalTrigger(hours=24),
        args=[None, None],
        id="backup_job",
        replace_existing=True
    )

    scheduler.start()

    logger.info("⏰ Scheduler started")
