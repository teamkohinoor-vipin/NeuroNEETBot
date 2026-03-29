# cleanup.py – run once to clean duplicates and create index
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

async def clean():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client["neetquiz"]
    # Remove duplicates
    pipeline = [
        {"$group": {"_id": "$user_id", "count": {"$sum": 1}, "docs": {"$push": "$_id"}}},
        {"$match": {"count": {"$gt": 1}}}
    ]
    cursor = db.users.aggregate(pipeline)
    deleted = 0
    async for doc in cursor:
        keep = doc["docs"][0]
        to_delete = doc["docs"][1:]
        for _id in to_delete:
            await db.users.delete_one({"_id": _id})
            deleted += 1
    print(f"Removed {deleted} duplicate entries")
    # Create unique index
    await db.users.create_index("user_id", unique=True)
    print("Unique index created")
    client.close()

if __name__ == "__main__":
    asyncio.run(clean())
