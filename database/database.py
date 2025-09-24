# database/database.py - Database Handler

import motor.motor_asyncio
from config import Config
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(Config.DATABASE_URI)
        self.db = self.client[Config.DATABASE_NAME]
        self.users = self.db.users
        self.files = self.db.files
        
    async def add_user(self, user_id):
        """Add user to database"""
        try:
            user_data = {
                "_id": user_id,
                "user_id": user_id,
                "join_date": None
            }
            await self.users.insert_one(user_data)
            logger.info(f"User {user_id} added to database")
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")
            pass
    
    async def get_user(self, user_id):
        """Get user from database"""
        try:
            user = await self.users.find_one({"user_id": user_id})
            return user
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    async def total_users_count(self):
        """Get total users count"""
        try:
            count = await self.users.count_documents({})
            return count
        except Exception as e:
            logger.error(f"Error counting users: {e}")
            return 0
    
    async def add_file(self, file_id, user_id):
        """Add file to database"""
        try:
            file_data = {
                "_id": f"{user_id}_{file_id}",
                "file_id": file_id,
                "user_id": user_id,
                "upload_date": None
            }
            await self.files.insert_one(file_data)
            logger.info(f"File {file_id} added for user {user_id}")
        except Exception as e:
            logger.error(f"Error adding file {file_id}: {e}")
            pass
    
    async def get_file(self, file_id):
        """Get file from database"""
        try:
            file_data = await self.files.find_one({"file_id": file_id})
            return file_data
        except Exception as e:
            logger.error(f"Error getting file {file_id}: {e}")
            return None
    
    async def total_files_count(self):
        """Get total files count"""
        try:
            count = await self.files.count_documents({})
            return count
        except Exception as e:
            logger.error(f"Error counting files: {e}")
            return 0
    
    async def get_all_users(self):
        """Get all users for broadcast"""
        try:
            users = []
            async for user in self.users.find({}):
                users.append(user["user_id"])
            return users
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []

# Create database instance
db = Database()
