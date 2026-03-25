from datetime import datetime
from bot.database.db import db
from bson import ObjectId
import re
import logging

logger = logging.getLogger(__name__)


# ================= NORMALIZE =================
def normalize_question(text: str):
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ================= USER =================
async def get_user(user_id: int):
    return await db.db.users.find_one({"user_id": user_id})


async def update_user_stats(user_id: int, username: str, correct: bool, chapter: str):

    await db.db.users.update_one(
        {"user_id": user_id},
        {
            "$set": {"username": username},
            "$setOnInsert": {
                "user_id": user_id,
                "total_correct": 0,
                "total_wrong": 0,
                "total_points": 0,
                "chapter_stats": {}
            }
        },
        upsert=True
    )

    update = {
        "$inc": {
            "total_correct" if correct else "total_wrong": 1,
            "total_points": 1 if correct else -1,
            f"chapter_stats.{chapter}.correct" if correct else f"chapter_stats.{chapter}.wrong": 1
        }
    }

    await db.db.users.update_one({"user_id": user_id}, update)


# ================= LEADERBOARD =================
async def get_top_users(chat_id: int, limit: int = 10, since: datetime = None):

    match = {"chat_id": chat_id}

    if since:
        match["timestamp"] = {"$gte": since}

    pipeline = [
        {"$match": match},
        {"$group": {
            "_id": "$user_id",
            "username": {"$first": "$username"},
            "points": {"$sum": "$points_change"}
        }},
        {"$sort": {"points": -1}},
        {"$limit": limit}
    ]

    cursor = db.db.answers.aggregate(pipeline)
    return await cursor.to_list(length=limit)


# ================= QUESTIONS =================
async def add_question(question_data: dict):

    # 🔥 normalized field add (future fast check)
    question_data["normalized"] = normalize_question(question_data["question"])

    result = await db.db.questions.insert_one(question_data)
    return result.inserted_id


# ================= RANDOM QUESTION =================
async def get_random_question(subject: str, chat_id: int):

    used_ids = await db.db.poll_logs.distinct(
        "question_id",
        {"chat_id": chat_id, "subject": subject}
    )

    # ⚡ LIMIT (VERY IMPORTANT)
    if len(used_ids) > 5000:
        used_ids = used_ids[-5000:]

    pipeline = [
        {
            "$match": {
                "subject": subject,
                "approved": True,
                "_id": {"$nin": used_ids}
            }
        },
        {"$sample": {"size": 1}}
    ]

    cursor = db.db.questions.aggregate(pipeline)
    questions = await cursor.to_list(length=1)

    if questions:
        return questions[0]

    # 🔁 fallback
    logger.info(f"Restarting question cycle for {subject}")

    pipeline = [
        {
            "$match": {
                "subject": subject,
                "approved": True
            }
        },
        {"$sample": {"size": 1}}
    ]

    cursor = db.db.questions.aggregate(pipeline)
    questions = await cursor.to_list(length=1)

    return questions[0] if questions else None


# ================= QUESTION EXISTS (FIXED) =================
async def question_exists(question_text: str):

    normalized = normalize_question(question_text)

    doc = await db.db.questions.find_one({
        "normalized": normalized
    })

    return bool(doc)


# ================= BATCH =================
async def create_pending_batch(user_id: int, subject: str, class_: int, chapter: str):

    batch = {
        "user_id": user_id,
        "subject": subject,
        "class": class_,
        "chapter": chapter,
        "questions": [],
        "status": "pending",
        "created_at": datetime.utcnow()
    }

    result = await db.db.pending_batches.insert_one(batch)
    return result.inserted_id


async def add_question_to_batch(batch_id: ObjectId, question: dict):

    await db.db.pending_batches.update_one(
        {"_id": batch_id},
        {"$push": {"questions": question}}
    )


async def get_pending_batch(batch_id: ObjectId):
    return await db.db.pending_batches.find_one({"_id": batch_id})


async def update_batch_status(batch_id: ObjectId, status: str):

    await db.db.pending_batches.update_one(
        {"_id": batch_id},
        {"$set": {"status": status}}
    )


# ================= POLL =================
async def log_poll(poll_id: int, message_id: int, question_id: ObjectId, subject: str, chapter: str, chat_id: int):

    await db.db.poll_logs.insert_one({
        "poll_id": poll_id,
        "message_id": message_id,
        "question_id": question_id,
        "subject": subject,
        "chapter": chapter,
        "chat_id": chat_id,
        "timestamp": datetime.utcnow()
    })


async def get_poll_log(poll_id: int):
    return await db.db.poll_logs.find_one({"poll_id": poll_id})


async def get_question_by_poll(poll_id: int):

    log = await get_poll_log(poll_id)

    if log:
        return await db.db.questions.find_one({"_id": log["question_id"]})

    return None


# ================= ANSWER =================
async def record_answer(user_id: int, username: str, question_id: ObjectId, points_change: int, chat_id: int):

    await db.db.answers.insert_one({
        "user_id": user_id,
        "username": username,
        "question_id": question_id,
        "points_change": points_change,
        "chat_id": chat_id,
        "timestamp": datetime.utcnow()
    })


# ================= GROUP =================
async def add_group(chat_id: int):

    await db.db.groups.update_one(
        {"chat_id": chat_id},
        {"$set": {"chat_id": chat_id}},
        upsert=True
    )


async def remove_group(chat_id: int):
    await db.db.groups.delete_one({"chat_id": chat_id})


async def get_all_groups():

    cursor = db.db.groups.find({}, {"chat_id": 1})
    groups = await cursor.to_list(length=1000)

    return [g["chat_id"] for g in groups]


# ================= CONFIG =================
async def get_config(key: str, default=None):

    doc = await db.db.config.find_one({"_id": key})
    return doc["value"] if doc else default


async def set_config(key: str, value):

    await db.db.config.update_one(
        {"_id": key},
        {"$set": {"value": value}},
        upsert=True
    )


# ================= RESET =================
async def reset_database():

    questions = await db.db.questions.delete_many({})
    poll_logs = await db.db.poll_logs.delete_many({})
    answers = await db.db.answers.delete_many({})
    pending = await db.db.pending_batches.delete_many({})

    await db.db.users.update_many(
        {},
        {
            "$set": {
                "total_correct": 0,
                "total_wrong": 0,
                "total_points": 0,
                "chapter_stats": {}
            }
        }
    )

    return {
        "questions": questions.deleted_count,
        "poll_logs": poll_logs.deleted_count,
        "answers": answers.deleted_count,
        "pending_batches": pending.deleted_count
    }
