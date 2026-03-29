from motor.motor_asyncio import AsyncIOMotorClient
from bot.config import MONGO_URI

class Database:
    client: AsyncIOMotorClient = None
    db = None

db = Database()


async def connect_db(app=None):
    db.client = AsyncIOMotorClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=5000,
        maxPoolSize=50,
        minPoolSize=5
    )

    db.db = db.client["neetquiz"]

    # -----------------------------------------------------------------
    # Step 1: Remove duplicate users (keep only one per user_id)
    # -----------------------------------------------------------------
    try:
        # Find all user_ids that appear more than once
        pipeline = [
            {"$group": {"_id": "$user_id", "count": {"$sum": 1}, "docs": {"$push": "$_id"}}},
            {"$match": {"count": {"$gt": 1}}}
        ]
        cursor = db.db.users.aggregate(pipeline)
        deleted = 0
        async for doc in cursor:
            keep = doc["docs"][0]          # keep the first document
            to_delete = doc["docs"][1:]    # delete the rest
            for _id in to_delete:
                await db.db.users.delete_one({"_id": _id})
                deleted += 1
        if deleted:
            print(f"🧹 Removed {deleted} duplicate user entries.")
    except Exception as e:
        print(f"⚠️ Duplicate removal warning: {e}")

    # -----------------------------------------------------------------
    # Step 2: Create unique index on user_id (safe now)
    # -----------------------------------------------------------------
    try:
        await db.db.users.create_index("user_id", unique=True)
        print("✅ Unique index on users.user_id created")
    except Exception as e:
        print(f"⚠️ Index creation warning: {e}")

    # -----------------------------------------------------------------
    # Step 3: Create other performance indexes (ignore conflicts)
    # -----------------------------------------------------------------
    try:
        await db.db.poll_logs.create_index("poll_id")
        await db.db.poll_logs.create_index("chat_id")
        await db.db.questions.create_index("subject")
        await db.db.questions.create_index("approved")
        await db.db.pending_batches.create_index("status")
        await db.db.answers.create_index("chat_id")
        await db.db.answers.create_index("timestamp")
    except Exception as e:
        print(f"⚠️ Performance index warning: {e}")

    print("✅ MongoDB connected and indexes ready")


async def close_db(app=None):
    if db.client:
        db.client.close()
