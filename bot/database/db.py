from motor.motor_asyncio import AsyncIOMotorClient
from bot.config import MONGO_URI

class Database:
    client: AsyncIOMotorClient = None
    db = None

db = Database()


async def ensure_index(collection, keys, unique=False):
    """
    Safely create an index only if it doesn't already exist with the same keys.
    This prevents 'Index already exists with a different name' warnings.
    
    Args:
        collection: MongoDB collection object
        keys: List of (field, direction) tuples, e.g., [("poll_id", 1)]
        unique: Boolean for unique index
    """
    existing = await collection.index_information()
    
    # Check if an index with the same key (fields) already exists
    for idx_name, idx_info in existing.items():
        if idx_info.get("key") == keys:
            # Index already exists with these exact keys, skip creation
            return
    
    # No index found with these keys, create it
    await collection.create_index(keys, unique=unique)


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
    # Step 1: Remove duplicate users (keep first per user_id)
    # -----------------------------------------------------------------
    try:
        before = await db.db.users.count_documents({})
        print(f"📊 Before cleanup: {before} user documents")

        pipeline = [
            {"$group": {"_id": "$user_id", "count": {"$sum": 1}, "docs": {"$push": "$_id"}}},
            {"$match": {"count": {"$gt": 1}}}
        ]
        cursor = db.db.users.aggregate(pipeline)
        deleted = 0
        async for doc in cursor:
            keep = doc["docs"][0]
            to_delete = doc["docs"][1:]
            for _id in to_delete:
                await db.db.users.delete_one({"_id": _id})
                deleted += 1
        if deleted:
            print(f"🧹 Removed {deleted} duplicate user entries.")
        after = await db.db.users.count_documents({})
        print(f"📊 After cleanup: {after} user documents")
    except Exception as e:
        print(f"⚠️ Duplicate removal warning: {e}")

    # -----------------------------------------------------------------
    # Step 2: Create unique index on user_id
    # -----------------------------------------------------------------
    try:
        await ensure_index(db.db.users, [("user_id", 1)], unique=True)
        print("✅ Unique index on users.user_id created/verified")
    except Exception as e:
        print(f"⚠️ Index creation warning: {e}")

    # -----------------------------------------------------------------
    # Step 3: Other performance indexes (check before creating)
    # -----------------------------------------------------------------
    try:
        # Poll logs
        await ensure_index(db.db.poll_logs, [("poll_id", 1)])
        await ensure_index(db.db.poll_logs, [("chat_id", 1)])
        
        # Questions
        await ensure_index(db.db.questions, [("subject", 1)])
        await ensure_index(db.db.questions, [("approved", 1)])
        
        # Pending batches
        await ensure_index(db.db.pending_batches, [("status", 1)])
        
        # Answers
        await ensure_index(db.db.answers, [("chat_id", 1)])
        await ensure_index(db.db.answers, [("timestamp", 1)])
        
        print("✅ All indexes created/verified")

    except Exception as e:
        # This will only catch unexpected errors now
        print(f"⚠️ Performance index warning: {e}")

    print("✅ MongoDB connected and indexes ready")


async def close_db(app=None):
    if db.client:
        db.client.close()
