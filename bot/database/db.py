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

    # ✅ Create unique index on user_id to prevent duplicates
    try:
        await db.db.users.create_index("user_id", unique=True)
        print("✅ Unique index on users.user_id created")
    except Exception as e:
        print(f"⚠️ Index creation warning: {e}")

    # Performance indexes
    await db.db.poll_logs.create_index("poll_id")
    await db.db.poll_logs.create_index("chat_id")
    await db.db.questions.create_index("subject")
    await db.db.questions.create_index("approved")
    await db.db.pending_batches.create_index("status")
    await db.db.answers.create_index("chat_id")
    await db.db.answers.create_index("timestamp")

    print("✅ MongoDB connected and indexes ready")


async def close_db(app=None):
    if db.client:
        db.client.close()
