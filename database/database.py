# database/database.py

import motor.motor_asyncio
from typing import Dict, List

# FIX: Import the correct variables directly from your config file
from config import DB_URI, DB_NAME

# NOTE: The SimpleDatabase class (JSON-based) is not shown here for brevity,
# but it should be included in your file if you need it as a fallback.

class MongoDatabase:
    """MongoDB Database Handler"""
    def __init__(self):
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
            self.db = self.client[DB_NAME]
            self.users = self.db.users
            self.files = self.db.files
            print("✅ Main Bot MongoDB Database connected")
        except Exception as e:
            print(f"❌ Main Bot MongoDB connection failed: {e}")
            raise e
    
    async def add_user(self, user_id):
        try:
            await self.users.insert_one({"_id": user_id})
        except:
            pass # User already exists

    async def total_users_count(self):
        try:
            return await self.users.count_documents({})
        except:
            return 0

    async def get_all_users(self):
        users = []
        async for user in self.users.find({}):
            users.append(user["_id"])
        return users

db = MongoDatabase()
