# database/clone_db.py

import motor.motor_asyncio
from datetime import datetime
# FIX: Import the correct variables for the CLONE database
from config import CLONE_DB_URI, CDB_NAME

class CloneDatabase:
    def __init__(self, uri, db_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[db_name]
        self.col = self.db.bots
    
    async def add_clone(self, bot_id, user_id, bot_token, username, name):
        """Add or update clone in the database to prevent duplicates"""
        update_data = {
            'user_id': user_id, 'token': bot_token, 'username': username,
            'name': name, 'is_active': True
        }
        new_clone_data = {
            'bot_id': bot_id, 'created_at': datetime.now(),
            'settings': {
                'start_message': None, 'start_photo': None,
                'force_sub_channels': [], 'auto_delete': False,
                'auto_delete_time': 1800, 'custom_thumbnail': None
            }
        }
        await self.col.update_one(
            {'bot_id': bot_id},
            {'$set': update_data, '$setOnInsert': new_clone_data},
            upsert=True
        )
    
    async def get_clone(self, bot_id):
        return await self.col.find_one({'bot_id': bot_id})
    
    async def get_user_clones(self, user_id):
        clones = self.col.find({'user_id': user_id})
        return await clones.to_list(length=None)
    
    async def update_clone_setting(self, bot_id, key, value):
        await self.col.update_one({'bot_id': bot_id}, {'$set': {f'settings.{key}': value}})

    async def add_fsub_channel(self, bot_id, channel_id):
        await self.col.update_one({'bot_id': bot_id}, {'$push': {'settings.force_sub_channels': channel_id}})

    async def remove_fsub_channel(self, bot_id, channel_id):
        await self.col.update_one({'bot_id': bot_id}, {'$pull': {'settings.force_sub_channels': channel_id}})

    async def delete_clone_by_id(self, bot_id):
        await self.col.delete_one({'bot_id': bot_id})

# FIX: Initialize with the correct variables for the clone database
clone_db = CloneDatabase(CLONE_DB_URI, CDB_NAME)
