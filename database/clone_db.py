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
            'created_at': datetime.now(timezone.utc),  # UTC aware
            'settings': {
                'start_message': None,
                'force_sub_channels': [],  # plural, consistent with code
                'auto_delete': False,
                'auto_delete_time': 1800,
                'no_forward': False,
                'admins': [],  # consistent with clone_customize.py
                'mode': 'public'
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
        await self.col.update_one(
            {'bot_id': bot_id},
            {'$set': {f'settings.{setting_key}': value}}
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

    # -----------------------------
    # GET NUMBER OF USERS (placeholder)
    # -----------------------------
    async def get_clone_users_count(self, bot_id):
        # Placeholder, future implementation if user tracking per clone is added
        return 0

# -----------------------------
# INSTANCE
# -----------------------------
clone_db = CloneDatabase(DB_URI)
