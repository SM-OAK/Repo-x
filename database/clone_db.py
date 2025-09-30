import motor.motor_asyncio
from config import DB_URI
from datetime import datetime

class CloneDatabase:
    def __init__(self, uri):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client["cloned_vjbotz"]
        self.col = self.db.bots
    
    async def add_clone(self, bot_id, user_id, bot_token, username, name):
        """Add or update clone in the database to prevent duplicates"""
        
        # Data that can be updated if the bot is re-added
        update_data = {
            'user_id': user_id,
            'token': bot_token,
            'username': username,
            'name': name,
            'is_active': True
        }
        
        # Data that should only be set when the bot is first created
        new_clone_data = {
            'bot_id': bot_id,
            'created_at': datetime.now(),
            'settings': {
                'start_message': None,
                'force_sub_channel': None,
                'auto_delete': False,
                'auto_delete_time': 1800,
                'no_forward': False,
                'moderators': [],
                'mode': 'public'
            }
        }

        # Use update_one with upsert=True to prevent duplicates
        await self.col.update_one(
            {'bot_id': bot_id},  # Filter by the unique bot_id
            {
                '$set': update_data,
                '$setOnInsert': new_clone_data
            },
            upsert=True  # This prevents creating duplicate entries
        )
        return True
    
    async def get_clone(self, bot_id):
        """Get clone by bot_id"""
        return await self.col.find_one({'bot_id': bot_id})
    
    async def get_clone_by_token(self, token):
        """Get clone by token"""
        return await self.col.find_one({'token': token})
    
    async def get_user_clones(self, user_id):
        """Get all clones by user"""
        clones = self.col.find({'user_id': user_id})
        return await clones.to_list(length=None)
    
    async def get_all_clones(self):
        """Get all clones"""
        clones = self.col.find({})
        return await clones.to_list(length=None)
    
    async def update_clone_setting(self, bot_id, setting_key, value):
        """Update specific clone setting"""
        await self.col.update_one(
            {'bot_id': bot_id},
            {'$set': {f'settings.{setting_key}': value}}
        )
        return True
    
    async def delete_clone(self, token):
        """Delete clone by token"""
        await self.col.delete_one({'token': token})
        return True
    
    async def delete_clone_by_id(self, bot_id):
        """Delete clone by bot_id"""
        await self.col.delete_one({'bot_id': bot_id})
        return True
    
    async def get_clone_users_count(self, bot_id):
        """Get user count for specific clone"""
        # This would need a separate users collection per clone
        return 0
    
    async def toggle_clone_status(self, bot_id, status):
        """Activate/Deactivate clone"""
        await self.col.update_one(
            {'bot_id': bot_id},
            {'$set': {'is_active': status}}
        )
        return True

clone_db = CloneDatabase(DB_URI)
