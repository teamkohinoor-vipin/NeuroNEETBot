from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from pytz import timezone
from datetime import datetime
from bot.config import TIMEZONE, QUIZ_INTERVAL_MINUTES, GROUP_ID, SCHEDULE
from bot.database.models import get_random_question, log_poll
from telegram import Bot, Poll
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone=timezone(TIMEZONE))

def get_current_subject():
    now = datetime.now(timezone(TIMEZONE)).hour
    for block in SCHEDULE:
        if block["start"] <= now < block["end"]:
            return block["subject"]
    return None  # Sleep mode

async def send_quiz(bot: Bot):
    subject = get_current_subject()
    if not subject:
        logger.info("😴 Sleep mode – no quiz")
        return

    question = await get_random_question(subject)
    if not question:
        logger.warning(f"No approved question for {subject}")
        return

    options = question["options"]
    correct_option_id = question["correct_index"]

    message = await bot.send_poll(
        chat_id=GROUP_ID,
        question=question["question"],
        options=options,
        type=Poll.QUIZ,
        correct_option_id=correct_option_id,
        is_anonymous=False
    )

    await log_poll(
        poll_id=message.poll.id,
        question_id=question["_id"],
        subject=subject,
        chapter=question["chapter"],
        chat_id=GROUP_ID
    )
    logger.info(f"📊 Sent quiz: {question['question'][:30]}...")

async def start_scheduler(bot: Bot):
    scheduler.add_job(
        send_quiz,
        trigger=IntervalTrigger(minutes=QUIZ_INTERVAL_MINUTES),
        args=[bot],
        id="send_quiz_job",
        replace_existing=True
    )
    scheduler.start()
    logger.info("⏰ Scheduler started")