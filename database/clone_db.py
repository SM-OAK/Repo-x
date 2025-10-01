# database/clone_db.py
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CloneDatabase:
    def __init__(self, uri, database_name):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[database_name]
        self.clones = self.db.clones
        self.clone_users = self.db.clone_users
    
    async def add_clone(self, user_id: int, bot_id: int, bot_token: str, name: str, username: str):
        """Add a new clone bot"""
        try:
            clone_data = {
                'user_id': user_id,
                'bot_id': bot_id,
                'bot_token': bot_token,
                'name': name,
                'username': username,
                'is_active': True,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'last_used': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'settings': {
                    'start_message': None,
                    'start_photo': None,
                    'start_button': None,
                    'force_sub_channels': [],  # List of max 6 channels
                    'admins': [],  # List of admin user IDs
                    'auto_delete': False,
                    'auto_delete_time': 300,  # Default 5 minutes
                    'public_use': True,  # Public or private bot
                    'mongo_db': None,
                    'log_channel': None,
                    'db_channel': None
                }
            }
            await self.clones.insert_one(clone_data)
            logger.info(f"Clone added: {bot_id} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding clone: {e}")
            return False
    
    async def get_clone(self, bot_id: int):
        """Get clone by bot ID"""
        try:
            clone = await self.clones.find_one({'bot_id': bot_id})
            return clone
        except Exception as e:
            logger.error(f"Error getting clone: {e}")
            return None
    
    async def get_clone_by_token(self, bot_token: str):
        """Get clone by bot token"""
        try:
            clone = await self.clones.find_one({'bot_token': bot_token})
            return clone
        except Exception as e:
            logger.error(f"Error getting clone by token: {e}")
            return None
    
    async def get_user_clones(self, user_id: int):
        """Get all clones of a user"""
        try:
            clones = []
            async for clone in self.clones.find({'user_id': user_id}):
                clones.append(clone)
            return clones
        except Exception as e:
            logger.error(f"Error getting user clones: {e}")
            return []
    
    async def update_clone_setting(self, bot_id: int, setting_key: str, setting_value):
        """Update a specific clone setting"""
        try:
            await self.clones.update_one(
                {'bot_id': bot_id},
                {'$set': {f'settings.{setting_key}': setting_value}}
            )
            logger.info(f"Updated setting {setting_key} for clone {bot_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating clone setting: {e}")
            return False
    
    async def update_clone_info(self, bot_id: int, name: str = None, username: str = None):
        """Update clone bot name and username"""
        try:
            update_data = {}
            if name:
                update_data['name'] = name
            if username:
                update_data['username'] = username
            
            if update_data:
                await self.clones.update_one(
                    {'bot_id': bot_id},
                    {'$set': update_data}
                )
                logger.info(f"Updated clone info for {bot_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating clone info: {e}")
            return False
    
    async def update_last_used(self, bot_id: int):
        """Update last used timestamp"""
        try:
            await self.clones.update_one(
                {'bot_id': bot_id},
                {'$set': {'last_used': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}
            )
            return True
        except Exception as e:
            logger.error(f"Error updating last used: {e}")
            return False
    
    async def toggle_clone_status(self, bot_id: int):
        """Toggle clone active status"""
        try:
            clone = await self.get_clone(bot_id)
            if clone:
                new_status = not clone.get('is_active', True)
                await self.clones.update_one(
                    {'bot_id': bot_id},
                    {'$set': {'is_active': new_status}}
                )
                logger.info(f"Clone {bot_id} status: {new_status}")
                return new_status
            return None
        except Exception as e:
            logger.error(f"Error toggling clone status: {e}")
            return None
    
    async def deactivate_clone(self, bot_id: int):
        """Deactivate a clone bot"""
        try:
            await self.clones.update_one(
                {'bot_id': bot_id},
                {'$set': {'is_active': False}}
            )
            logger.info(f"Clone {bot_id} deactivated")
            return True
        except Exception as e:
            logger.error(f"Error deactivating clone: {e}")
            return False
    
    async def activate_clone(self, bot_id: int):
        """Activate a clone bot"""
        try:
            await self.clones.update_one(
                {'bot_id': bot_id},
                {'$set': {'is_active': True}}
            )
            logger.info(f"Clone {bot_id} activated")
            return True
        except Exception as e:
            logger.error(f"Error activating clone: {e}")
            return False
    
    async def delete_clone_by_id(self, bot_id: int):
        """Delete a clone bot"""
        try:
            # Delete clone data
            await self.clones.delete_one({'bot_id': bot_id})
            # Delete clone users
            await self.clone_users.delete_many({'bot_id': bot_id})
            logger.info(f"Clone {bot_id} deleted")
            return True
        except Exception as e:
            logger.error(f"Error deleting clone: {e}")
            return False
    
    async def add_clone_user(self, bot_id: int, user_id: int):
        """Add a user to clone bot"""
        try:
            user_data = {
                'bot_id': bot_id,
                'user_id': user_id,
                'joined_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            await self.clone_users.update_one(
                {'bot_id': bot_id, 'user_id': user_id},
                {'$set': user_data},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error adding clone user: {e}")
            return False
    
    async def get_clone_users_count(self, bot_id: int):
        """Get total users count for a clone"""
        try:
            count = await self.clone_users.count_documents({'bot_id': bot_id})
            return count
        except Exception as e:
            logger.error(f"Error getting clone users count: {e}")
            return 0
    
    async def get_clone_users(self, bot_id: int, limit: int = 100):
        """Get clone users list"""
        try:
            users = []
            async for user in self.clone_users.find({'bot_id': bot_id}).limit(limit):
                users.append(user)
            return users
        except Exception as e:
            logger.error(f"Error getting clone users: {e}")
            return []
    
    async def get_all_clones(self):
        """Get all clones"""
        try:
            clones = []
            async for clone in self.clones.find({}):
                clones.append(clone)
            return clones
        except Exception as e:
            logger.error(f"Error getting all clones: {e}")
            return []
    
    async def get_active_clones(self):
        """Get all active clones"""
        try:
            clones = []
            async for clone in self.clones.find({'is_active': True}):
                clones.append(clone)
            return clones
        except Exception as e:
            logger.error(f"Error getting active clones: {e}")
            return []
    
    async def get_total_clones_count(self):
        """Get total number of clones"""
        try:
            count = await self.clones.count_documents({})
            return count
        except Exception as e:
            logger.error(f"Error getting total clones count: {e}")
            return 0
    
    async def get_active_clones_count(self):
        """Get total number of active clones"""
        try:
            count = await self.clones.count_documents({'is_active': True})
            return count
        except Exception as e:
            logger.error(f"Error getting active clones count: {e}")
            return 0
    
    async def is_clone_exists(self, bot_id: int):
        """Check if clone exists"""
        try:
            clone = await self.clones.find_one({'bot_id': bot_id})
            return clone is not None
        except Exception as e:
            logger.error(f"Error checking clone exists: {e}")
            return False
    
    async def is_user_has_clone(self, user_id: int):
        """Check if user already has a clone"""
        try:
            clone = await self.clones.find_one({'user_id': user_id})
            return clone is not None
        except Exception as e:
            logger.error(f"Error checking user has clone: {e}")
            return False
    
    async def get_user_clone_count(self, user_id: int):
        """Get number of clones owned by user"""
        try:
            count = await self.clones.count_documents({'user_id': user_id})
            return count
        except Exception as e:
            logger.error(f"Error getting user clone count: {e}")
            return 0
    
    async def deactivate_inactive_clones(self, days: int = 7):
        """Deactivate clones not used for specified days"""
        try:
            threshold_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
            
            result = await self.clones.update_many(
                {
                    'last_used': {'$lt': threshold_date},
                    'is_active': True
                },
                {'$set': {'is_active': False}}
            )
            logger.info(f"Deactivated {result.modified_count} inactive clones")
            return result.modified_count
        except Exception as e:
            logger.error(f"Error deactivating inactive clones: {e}")
            return 0
    
    # Force Subscribe Channel Methods
    async def add_force_sub_channel(self, bot_id: int, channel: str):
        """Add a force subscribe channel (max 6)"""
        try:
            clone = await self.get_clone(bot_id)
            if clone:
                fsub_channels = clone.get('settings', {}).get('force_sub_channels', [])
                if len(fsub_channels) >= 6:
                    return False, "Maximum 6 channels allowed"
                
                if channel not in fsub_channels:
                    fsub_channels.append(channel)
                    await self.update_clone_setting(bot_id, 'force_sub_channels', fsub_channels)
                    return True, "Channel added successfully"
                else:
                    return False, "Channel already exists"
            return False, "Clone not found"
        except Exception as e:
            logger.error(f"Error adding force sub channel: {e}")
            return False, str(e)
    
    async def remove_force_sub_channel(self, bot_id: int, channel: str):
        """Remove a force subscribe channel"""
        try:
            clone = await self.get_clone(bot_id)
            if clone:
                fsub_channels = clone.get('settings', {}).get('force_sub_channels', [])
                if channel in fsub_channels:
                    fsub_channels.remove(channel)
                    await self.update_clone_setting(bot_id, 'force_sub_channels', fsub_channels)
                    return True, "Channel removed successfully"
                else:
                    return False, "Channel not found"
            return False, "Clone not found"
        except Exception as e:
            logger.error(f"Error removing force sub channel: {e}")
            return False, str(e)
    
    async def get_force_sub_channels(self, bot_id: int):
        """Get all force subscribe channels"""
        try:
            clone = await self.get_clone(bot_id)
            if clone:
                return clone.get('settings', {}).get('force_sub_channels', [])
            return []
        except Exception as e:
            logger.error(f"Error getting force sub channels: {e}")
            return []
    
    async def clear_force_sub_channels(self, bot_id: int):
        """Clear all force subscribe channels"""
        try:
            await self.update_clone_setting(bot_id, 'force_sub_channels', [])
            return True
        except Exception as e:
            logger.error(f"Error clearing force sub channels: {e}")
            return False
    
    # Admin Methods
    async def add_admin(self, bot_id: int, admin_id: int):
        """Add an admin to clone bot"""
        try:
            clone = await self.get_clone(bot_id)
            if clone:
                admins = clone.get('settings', {}).get('admins', [])
                if admin_id not in admins:
                    admins.append(admin_id)
                    await self.update_clone_setting(bot_id, 'admins', admins)
                    return True, "Admin added successfully"
                else:
                    return False, "Admin already exists"
            return False, "Clone not found"
        except Exception as e:
            logger.error(f"Error adding admin: {e}")
            return False, str(e)
    
    async def remove_admin(self, bot_id: int, admin_id: int):
        """Remove an admin from clone bot"""
        try:
            clone = await self.get_clone(bot_id)
            if clone:
                admins = clone.get('settings', {}).get('admins', [])
                if admin_id in admins:
                    admins.remove(admin_id)
                    await self.update_clone_setting(bot_id, 'admins', admins)
                    return True, "Admin removed successfully"
                else:
                    return False, "Admin not found"
            return False, "Clone not found"
        except Exception as e:
            logger.error(f"Error removing admin: {e}")
            return False, str(e)
    
    async def is_admin(self, bot_id: int, user_id: int):
        """Check if user is admin of clone bot"""
        try:
            clone = await self.get_clone(bot_id)
            if clone:
                admins = clone.get('settings', {}).get('admins', [])
                return user_id in admins or user_id == clone.get('user_id')
            return False
        except Exception as e:
            logger.error(f"Error checking admin: {e}")
            return False
    
    async def get_admins(self, bot_id: int):
        """Get all admins of a clone bot"""
        try:
            clone = await self.get_clone(bot_id)
            if clone:
                return clone.get('settings', {}).get('admins', [])
            return []
        except Exception as e:
            logger.error(f"Error getting admins: {e}")
            return []
    
    async def clear_admins(self, bot_id: int):
        """Clear all admins"""
        try:
            await self.update_clone_setting(bot_id, 'admins', [])
            return True
        except Exception as e:
            logger.error(f"Error clearing admins: {e}")
            return False
    
    # Stats Methods
    async def get_clone_stats(self, bot_id: int):
        """Get comprehensive clone statistics"""
        try:
            clone = await self.get_clone(bot_id)
            if not clone:
                return None
            
            users_count = await self.get_clone_users_count(bot_id)
            settings = clone.get('settings', {})
            
            stats = {
                'bot_id': clone['bot_id'],
                'username': clone['username'],
                'name': clone['name'],
                'is_active': clone.get('is_active', True),
                'created_at': clone.get('created_at'),
                'last_used': clone.get('last_used'),
                'total_users': users_count,
                'auto_delete': settings.get('auto_delete', False),
                'auto_delete_time': settings.get('auto_delete_time', 300),
                'public_use': settings.get('public_use', True),
                'force_sub_channels': len(settings.get('force_sub_channels', [])),
                'admins': len(settings.get('admins', []))
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting clone stats: {e}")
            return None
    
    async def get_global_stats(self):
        """Get global statistics"""
        try:
            total_clones = await self.get_total_clones_count()
            active_clones = await self.get_active_clones_count()
            total_users = await self.clone_users.count_documents({})
            
            stats = {
                'total_clones': total_clones,
                'active_clones': active_clones,
                'inactive_clones': total_clones - active_clones,
                'total_users': total_users
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting global stats: {e}")
            return None

# Initialize database instance
clone_db = None

def init_clone_db(uri: str, database_name: str):
    """Initialize clone database"""
    global clone_db
    clone_db = CloneDatabase(uri, database_name)
    logger.info("✅ Clone database initialized")
    return clone_db

logger.info("✅ Clone database module loaded")
