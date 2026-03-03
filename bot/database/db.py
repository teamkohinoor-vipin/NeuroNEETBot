from motor.motor_asyncio import AsyncIOMotorClient
from bot.config import MONGO_URI

class Database:
    client: AsyncIOMotorClient = None
    db = None

db = Database()

async def connect_db():
    db.client = AsyncIOMotorClient(MONGO_URI)
    db.db = db.client["neetquiz"]
    print("✅ MongoDB connected")

async def close_db():
    db.client.close()