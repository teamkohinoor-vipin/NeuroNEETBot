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

    print("✅ MongoDB connected")


async def close_db(app=None):
    if db.client:
        db.client.close()
