from datetime import datetime
from bot.database.db import db
from bson import ObjectId
import re


# ---------- NORMALIZE QUESTION ----------
def normalize_question(text: str):
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
# ---------------------------------------


# ---------- Users ----------
async def get_user(user_id: int):
    return await db.db.users.find_one({"user_id": user_id})


async def update_user_stats(user_id: int, username: str, correct: bool, chapter: str):

    await db.db.users.update_one(
        {"user_id": user_id},
        {"$setOnInsert": {
            "user_id": user_id,
            "username": username,
            "total_correct": 0,
            "total_wrong": 0,
            "total_points": 0,
            "chapter_stats": {}
        }},
        upsert=True
    )

    update = {
        "$inc": {
            "total_correct" if correct else "total_wrong": 1,
            "total_points": 1 if correct else -1,
            f"chapter_stats.{chapter}.correct" if correct else f"chapter_stats.{chapter}.wrong": 1
        },
        "$set": {"username": username}
    }

    await db.db.users.update_one({"user_id": user_id}, update)


# ---------- Leaderboard ----------
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


# ---------- Questions ----------
async def add_question(question_data: dict):

    result = await db.db.questions.insert_one(question_data)

    return result.inserted_id


async def get_random_question(subject: str):

    pipeline = [
        {"$match": {"subject": subject, "approved": True}},
        {"$sample": {"size": 1}}
    ]

    cursor = db.db.questions.aggregate(pipeline)

    questions = await cursor.to_list(length=1)

    return questions[0] if questions else None


# ---------- SMART Duplicate Question Check ----------
async def question_exists(question_text: str):

    normalized = normalize_question(question_text)

    cursor = db.db.questions.find({}, {"question": 1})

    async for q in cursor:

        existing = normalize_question(q["question"])

        if existing == normalized:
            return True

    return False


# ---------- Pending Batches ----------
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


# ---------- Poll Logs ----------
async def log_poll(poll_id: int, question_id: ObjectId, subject: str, chapter: str, chat_id: int):

    await db.db.poll_logs.insert_one({
        "poll_id": poll_id,
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


# ---------- Answers ----------
async def record_answer(user_id: int, username: str, question_id: ObjectId, points_change: int, chat_id: int):

    await db.db.answers.insert_one({
        "user_id": user_id,
        "username": username,
        "question_id": question_id,
        "points_change": points_change,
        "chat_id": chat_id,
        "timestamp": datetime.utcnow()
    })


# =========================================================
# MULTI GROUP SUPPORT
# =========================================================

async def add_group(chat_id: int):

    await db.db.groups.update_one(
        {"chat_id": chat_id},
        {"$set": {"chat_id": chat_id}},
        upsert=True
    )


async def remove_group(chat_id: int):

    await db.db.groups.delete_one({"chat_id": chat_id})


async def get_all_groups():

    cursor = db.db.groups.find({})

    groups = await cursor.to_list(length=None)

    return [g["chat_id"] for g in groups]
