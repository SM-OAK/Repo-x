import asyncio
import logging
from pyrogram import Client
from pyrogram.errors import ApiIdInvalid, AccessTokenInvalid, UserDeactivated
from config import API_ID, API_HASH, CLONE_MODE, CLONE_DB_URI
from database.clone_db import clone_db

logger = logging.getLogger("CloneManager")

# Store active clone clients {bot_id: Client}
active_clones = {}

async def start_clone_bot(bot_data):
    """Start a single clone bot"""
    bot_id = bot_data['bot_id']
    bot_token = bot_data['bot_token']
    user_id = bot_data['user_id']
    
    try:
        logger.info(f"Starting clone bot {bot_id} for user {user_id}")
        
        # Create client instance
        clone_client = Client(
            name=f"clone_{bot_id}",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=bot_token,
            plugins=dict(root="clone_plugins"),
            workdir="./clone_sessions"
        )
        
        # Start the client
        await clone_client.start()
        
        # Get bot info
        me = await clone_client.get_me()
        logger.info(f"✅ Clone bot @{me.username} started successfully")
        
        # Update database with bot info
        await clone_db.update_clone(bot_id, {
            'username': me.username,
            'name': me.first_name,
            'is_active': True
        })
        
        # Store in active clones
        active_clones[bot_id] = clone_client
        
        return True
        
    except AccessTokenInvalid:
        logger.error(f"❌ Invalid bot token for clone {bot_id}")
        await clone_db.update_clone(bot_id, {'is_active': False, 'error': 'Invalid token'})
        return False
        
    except ApiIdInvalid:
        logger.error(f"❌ Invalid API credentials for clone {bot_id}")
        return False
        
    except Exception as e:
        logger.error(f"❌ Failed to start clone {bot_id}: {e}", exc_info=True)
        await clone_db.update_clone(bot_id, {'is_active': False, 'error': str(e)})
        return False


async def stop_clone_bot(bot_id):
    """Stop a clone bot"""
    try:
        if bot_id in active_clones:
            clone_client = active_clones[bot_id]
            await clone_client.stop()
            del active_clones[bot_id]
            logger.info(f"✅ Clone bot {bot_id} stopped")
            
            await clone_db.update_clone(bot_id, {'is_active': False})
            return True
        else:
            logger.warning(f"Clone {bot_id} not found in active clones")
            return False
            
    except Exception as e:
        logger.error(f"Error stopping clone {bot_id}: {e}", exc_info=True)
        return False


async def restart_clone_bot(bot_id):
    """Restart a specific clone bot"""
    try:
        # Stop if running
        await stop_clone_bot(bot_id)
        
        # Get bot data
        bot_data = await clone_db.get_clone(bot_id)
        if not bot_data:
            logger.error(f"Clone {bot_id} not found in database")
            return False
        
        # Start again
        return await start_clone_bot(bot_data)
        
    except Exception as e:
        logger.error(f"Error restarting clone {bot_id}: {e}", exc_info=True)
        return False


async def restart_all_clones():
    """Restart all active clone bots from database"""
    if not CLONE_MODE:
        logger.info("Clone mode disabled")
        return
    
    try:
        logger.info("🔄 Loading clone bots from database...")
        
        # Get all active cl
