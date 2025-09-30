from motor.motor_asyncio import AsyncIOMotorClient
from config import CLONE_DB_URI, CDB_NAME
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CloneDatabase:
    def __init__(self):
        try:
            self.client = AsyncIOMotorClient(CLONE_DB_URI)
            self.db = self.client[CDB_NAME]
            self.clones = self.db.clones
            logger.info("Clone database connected successfully")
        except Exception as e:
            logger.error(f"Clone database connection error: {e}")
    
    async def add_clone(self, bot_id, user_id, bot_token, username, name):
        """Add new clone to database"""
        try:
            clone = {
                'bot_id': bot_id,
                'user_id': user_id,
                'bot_token': bot_token,  # IMPORTANT: Field name is bot_token, not token
                'username': username,
                'name': name,
                'is_active': True,
                'created_at': datetime.now(),
                'settings': {}
            }
            await self.clones.insert_one(clone)
            logger.info(f"Clone added: {username} (ID: {bot_id})")
            return clone
        except Exception as e:
            logger.error(f"Error adding clone: {e}")
            return None
    
    async def get_clone(self, bot_id):
        """Get clone by bot ID"""
        try:
            return await self.clones.find_one({'bot_id': bot_id})
        except Exception as e:
            logger.error(f"Error getting clone: {e}")
            return None
    
    async def get_clone_by_token(self, token):
        """Get clone by token - FIXED field name"""
        try:
            return await self.clones.find_one({'bot_token': token})
        except Exception as e:
            logger.error(f"Error getting clone by token: {e}")
            return None
    
    async def get_user_clones(self, user_id):
        """Get all clones for a user"""
        try:
            cursor = self.clones.find({'user_id': user_id})
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error getting user clones: {e}")
            return []
    
    async def get_all_clones(self):
        """Get all clones"""
        try:
            cursor = self.clones.find({})
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error getting all clones: {e}")
            return []
    
    async def get_active_clones(self):
        """Get all active clones"""
        try:
            cursor = self.clones.find({'is_active': True})
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error getting active clones: {e}")
            return []
    
    async def update_clone(self, bot_id, data):
        """Update clone data"""
        try:
            result = await self.clones.update_one(
                {'bot_id': bot_id},
                {'$set': data}
            )
            logger.info(f"Clone {bot_id} updated: {data}")
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating clone: {e}")
            return False
    
    async def update_clone_setting(self, bot_id, key, value):
        """Update specific setting"""
        try:
            result = await self.clones.update_one(
                {'bot_id': bot_id},
                {'$set': {f'settings.{key}': value}}
            )
            logger.info(f"Clone {bot_id} setting updated: {key} = {value}")
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating clone setting: {e}")
            return False
    
    async def delete_clone(self, token):
        """Delete clone by token"""
        try:
            result = await self.clones.delete_one({'bot_token': token})
            logger.info(f"Clone with token deleted")
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting clone: {e}")
            return False
    
    async def delete_clone_by_id(self, bot_id):
        """Delete clone by ID"""
        try:
            result = await self.clones.delete_one({'bot_id': bot_id})
            logger.info(f"Clone {bot_id} deleted")
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting clone by ID: {e}")
            return False
    
    async def get_clone_users_count(self, bot_id):
        """Get user count for clone - placeholder for now"""
        # You can implement actual user tracking later
        return 0
    
    async def clone_exists(self, bot_id):
        """Check if clone exists"""
        try:
            count = await self.clones.count_documents({'bot_id': bot_id})
            return count > 0
        except Exception as e:
            logger.error(f"Error checking clone existence: {e}")
            return False

# Create global instance
clone_db = CloneDatabase()
