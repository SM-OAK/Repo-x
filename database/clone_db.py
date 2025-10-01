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
        self.db.bots.create_index("bot_id", unique=True)
        self.db.bots.create_index("bot_token", unique=True)

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
    # GET CLONE
    # -----------------------------
    async def get_clone(self, bot_id):
        return await self.col.find_one({'bot_id': bot_id})

    async def get_clone_by_token(self, bot_token):
        return await self.col.find_one({'bot_token': bot_token})

    async def get_clones_by_user(self, user_id):
        cursor = self.col.find({'user_id': user_id})
        return await cursor.to_list(length=None)

    async def get_all_clones(self):
        cursor = self.col.find({})
        return await cursor.to_list(length=None)

    # -----------------------------
    # UPDATE CLONE SETTINGS
    # -----------------------------
    async def update_clone_setting(self, bot_id, setting_key, value):
        """Update a specific setting"""
        await self.col.update_one(
            {'bot_id': bot_id},
            {'$set': {f'settings.{setting_key}': value}}
        )
        return True
    
    async def update_last_used(self, bot_id):
        """Update last used timestamp"""
        await self.col.update_one(
            {'bot_id': bot_id},
            {'$set': {'last_used': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}}
        )
        return True

    # -----------------------------
    # DELETE CLONE
    # -----------------------------
    async def delete_clone_by_id(self, bot_id):
        await self.col.delete_one({'bot_id': bot_id})
        return True

    # -----------------------------
    # ACTIVATE / DEACTIVATE CLONE
    # -----------------------------
    async def toggle_clone_status(self, bot_id, status: bool):
        await self.col.update_one(
            {'bot_id': bot_id},
            {'$set': {'is_active': status}}
        )
        return True
    
    async def deactivate_clone(self, bot_id):
        """Deactivate a clone"""
        return await self.toggle_clone_status(bot_id, False)
    
    async def activate_clone(self, bot_id):
        """Activate a clone"""
        return await self.toggle_clone_status(bot_id, True)

    # -----------------------------
    # GET NUMBER OF USERS
    # -----------------------------
    async def get_clone_users_count(self, bot_id):
        """Get user count for specific clone - placeholder for now"""
        # You can implement actual user tracking later
        return 0

# -----------------------------
# INSTANCE
# -----------------------------
clone_db = CloneDatabase(DB_URI)
