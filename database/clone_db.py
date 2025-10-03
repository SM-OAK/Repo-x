# database/clone_db.py
import motor.motor_asyncio
from config import DB_URI
from datetime import datetime, timezone

class CloneDatabase:
    def __init__(self, uri):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client["cloned_vjbotz"]
        self.col = self.db.bots

        # Ensure indexes for uniqueness
        self.col.create_index("bot_id", unique=True)
        self.col.create_index("bot_token", unique=True)

    # -----------------------------
    # ADD NEW CLONE
    # -----------------------------
    async def add_clone(self, bot_id, user_id, bot_token, username, name):
        """Add new clone to database"""
        clone_data = {
            'bot_id': bot_id,
            'user_id': user_id,
            'bot_token': bot_token,
            'username': username,
            'name': name,
            'is_active': True,
            'created_at': datetime.now(timezone.utc),
            'last_used': 'Never',
            'settings': {
                # Appearance
                'start_message': None,
                'start_photo': None,
                'start_button': None,
                'file_caption': None,
                
                # Security
                'force_sub_channels': [],
                'auto_delete': False,
                'auto_delete_time': 1800,
                'protect_mode': False,
                'verification': False,
                'shortlink_api': None,
                'shortlink_url': None,
                'tutorial_link': None,
                
                # Files
                'protect_forward': False,
                'file_size_limit': 0,
                'allowed_types': ['all'],
                
                # Database
                'mongo_db': None,
                'log_channel': None,
                'db_channel': None,
                
                # Admins & Bot Settings
                'admins': [],
                'public_use': True,
                'maintenance': False,
                'language': 'en',
                'timezone': 'UTC'
            }
        }
        await self.col.insert_one(clone_data)
        return True

    # -----------------------------
    # GET CLONE INFO
    # -----------------------------
    async def get_clone(self, bot_id):
        """Get a single clone by its bot ID."""
        return await self.col.find_one({'bot_id': bot_id})

    async def get_clone_by_token(self, bot_token):
        """Get a single clone by its bot token."""
        return await self.col.find_one({'bot_token': bot_token})

    async def get_clones_by_user(self, user_id):
        """Get all clones owned by a specific user."""
        cursor = self.col.find({'user_id': user_id})
        return await cursor.to_list(length=None)

    async def get_all_clones(self):
        """Get all clones in the database."""
        cursor = self.col.find({})
        return await cursor.to_list(length=None)

    # -----------------------------
    # UPDATE CLONE INFO
    # -----------------------------
    async def update_clone_field(self, bot_id, field, value):
        """
        Update a top-level field for a clone (e.g., 'is_active', 'username').
        """
        await self.col.update_one(
            {'bot_id': bot_id},
            {'$set': {field: value}}
        )
        return True

    async def update_clone_setting(self, bot_id, setting_key, value):
        """
        Update a specific key within the 'settings' dictionary.
        This will overwrite the existing value.
        """
        await self.col.update_one(
            {'bot_id': bot_id},
            {'$set': {f'settings.{setting_key}': value}}
        )
        return True
    
    async def update_last_used(self, bot_id):
        """Update the 'last_used' timestamp to the current time."""
        await self.col.update_one(
            {'bot_id': bot_id},
            {'$set': {'last_used': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}}
        )
        return True

    # -----------------------------
    # ADVANCED LIST-BASED UPDATES (NEW & ENHANCED)
    # -----------------------------
    async def add_to_list_setting(self, bot_id, list_key, value):
        """
        Add an item to a list within the 'settings' dictionary (e.g., 'force_sub_channels', 'admins').
        """
        await self.col.update_one(
            {'bot_id': bot_id},
            {'$push': {f'settings.{list_key}': value}}
        )
        return True

    async def remove_from_list_setting(self, bot_id, list_key, value):
        """
        Remove an item from a list within 'settings' by its value.
        """
        await self.col.update_one(
            {'bot_id': bot_id},
            {'$pull': {f'settings.{list_key}': value}}
        )
        return True
        
    async def remove_from_list_setting_by_index(self, bot_id, list_key, index):
        """
        Remove an item from a list within 'settings' by its index (position).
        """
        # Step 1: Set the element at the specified index to null
        await self.col.update_one(
            {'bot_id': bot_id},
            {'$unset': {f'settings.{list_key}.{index}': 1}}
        )
        # Step 2: Remove (pull) all null values from the list to compact it
        await self.col.update_one(
            {'bot_id': bot_id},
            {'$pull': {f'settings.{list_key}': None}}
        )
        return True

    # -----------------------------
    # DELETE CLONE
    # -----------------------------
    async def delete_clone_by_id(self, bot_id):
        """Delete a clone document entirely from the database."""
        await self.col.delete_one({'bot_id': bot_id})
        return True

    # -----------------------------
    # GET NUMBER OF USERS (Placeholder)
    # -----------------------------
    async def get_clone_users_count(self, bot_id):
        """Get user count for a specific clone - placeholder for now."""
        # This would require a separate collection to track users per bot.
        return 0

# -----------------------------
# INSTANCE
# -----------------------------
clone_db = CloneDatabase(DB_URI)
