# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import sys
import glob
import importlib.util
from pathlib import Path
import logging
import logging.config
import asyncio
import pytz
from datetime import date, datetime 
from aiohttp import web
import aiohttp

from pyrogram import Client, idle
from config import (
    LOG_CHANNEL, ON_HEROKU, CLONE_MODE, PORT, API_ID, API_HASH, 
    BOT_TOKEN, DB_URI, PING_INTERVAL, URL, SLEEP_THRESHOLD
)
from Script import script

# Setup logging
try:
    logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
except Exception as e:
    # Fallback to basic logging if logging.conf doesn't exist
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    print(f"Warning: Could not load logging.conf: {e}")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

# Initialize Main Bot
StreamBot = Client(
    "StreamBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    sleep_threshold=SLEEP_THRESHOLD,
    plugins={"root": "plugins"}
)

# Keep-alive ping for Heroku or other free hosting
async def ping_server():
    """Keep the bot alive on free hosting platforms"""
    while True:
        await asyncio.sleep(PING_INTERVAL)
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(URL) as resp:
                    logger.info(f"Pinged server with status: {resp.status}")
        except asyncio.TimeoutError:
            logger.warning("Ping timeout - server didn't respond in time")
        except Exception as e:
            logger.warning(f"Error while pinging server: {e}")

# Simple Web Server
async def web_server():
    """Simple web server to keep bot alive"""
    routes = web.RouteTableDef()
    
    @routes.get('/')
    async def handle_root(request):
        return web.Response(text="✅ Bot is alive and running!")
    
    @routes.get('/status')
    async def handle_status(request):
        return web.json_response({
            'status': 'online',
            'bot_username': StreamBot.username if hasattr(StreamBot, 'username') else 'unknown'
        })
    
    app = web.Application()
    app.add_routes(routes)
    return app

# Clone Restart Handler
async def restart_bots():
    """Restart all clone bots from database"""
    try:
        from database.database import db
        
        bots = await db.get_all_bots()
        if not bots:
            logger.info("No clones found to restart.")
            return
        
        logger.info(f"Found {len(bots)} clone(s) to restart...")
        
        for bot_data in bots:
            bot_token = bot_data.get('token')
            bot_username = bot_data.get('username', 'unknown')
            user_id = bot_data.get('user_id', 'unknown')
            
            if not bot_token:
                logger.warning(f"Skipping clone @{bot_username} - no token found")
                continue
            
            try:
                clone_client = Client(
                    f"clone_{user_id}",
                    api_id=API_ID,
                    api_hash=API_HASH,
                    bot_token=bot_token,
                    sleep_threshold=SLEEP_THRESHOLD,
                    plugins={"root": "clone_plugins"}
                )
                await clone_client.start()
                logger.info(f"✅ Restarted clone: @{bot_username}")
                
            except Exception as e:
                logger.error(f"❌ Failed to restart @{bot_username}: {e}")
                # Optionally notify owner about failed clone
                try:
                    await StreamBot.send_message(
                        user_id,
                        f"⚠️ Failed to restart your clone bot @{bot_username}\n\n"
                        f"Error: {str(e)[:100]}\n\n"
                        f"Please create a new clone or contact support."
                    )
                except:
                    pass
                    
    except ImportError:
        logger.warning("database.database module not found. Using fallback restart handler.")
        await restart_bots_fallback()
    except Exception as e:
        logger.error(f"Error in restart_bots: {e}", exc_info=True)

async def restart_bots_fallback():
    """Fallback method using direct MongoDB connection"""
    try:
        from pymongo import MongoClient
        
        if not DB_URI:
            logger.warning("DB_URI not configured - cannot restart clones")
            return
            
        mongo_client = MongoClient(DB_URI)
        db_name = DB_URI.split("/")[-1].split("?")[0]
        mongo_db = mongo_client[db_name]
        
        bots = list(mongo_db.bots.find())
        if not bots:
            logger.info("No clones to restart.")
            mongo_client.close()
            return
        
        logger.info(f"Found {len(bots)} clone(s) to restart...")
        
        for bot in bots:
            bot_token = bot.get('token')
            bot_username = bot.get('username', 'unknown')
            user_id = bot.get('user_id', 'unknown')
            
            if not bot_token:
                continue
                
            try:
                clone_client = Client(
                    f"clone_{user_id}",
                    api_id=API_ID,
                    api_hash=API_HASH,
                    bot_token=bot_token,
                    sleep_threshold=SLEEP_THRESHOLD,
                    plugins={"root": "clone_plugins"}
                )
                await clone_client.start()
                logger.info(f"✅ Restarted clone: @{bot_username}")
            except Exception as e:
                logger.error(f"❌ Failed to restart @{bot_username}: {e}")
        
        mongo_client.close()
    except ImportError:
        logger.error("pymongo not installed - cannot restart clones")
    except Exception as e:
        logger.error(f"Error in fallback restart_bots: {e}", exc_info=True)

# Start Main Bot
async def start_bot():
    """Main bot startup function"""
    logger.info('🚀 Starting Bot...')
    
    try:
        await StreamBot.start()
        bot_info = await StreamBot.get_me()
        StreamBot.username = bot_info.username
        logger.info(f"✅ Main bot started: @{bot_info.username}")
    except Exception as e:
        logger.error(f"Failed to start main bot: {e}", exc_info=True)
        return

    # === Load Main Plugins ===
    logger.info("\n🔹 Loading Main Bot Plugins...")
    plugin_count = 0
    for plugin_path in sorted(glob.glob("plugins/*.py")):
        try:
            plugin_name = Path(plugin_path).stem
            if plugin_name.startswith("__"):
                continue
            
            import_path = f"plugins.{plugin_name}"
            
            # Skip if already loaded
            if import_path in sys.modules:
                logger.debug(f"  ⏭️ Plugin already loaded: {plugin_name}")
                continue
            
            spec = importlib.util.spec_from_file_location(import_path, plugin_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[import_path] = module
                spec.loader.exec_module(module)
                logger.info(f"  ✅ Loaded plugin: {plugin_name}")
                plugin_count += 1
            else:
                logger.warning(f"  ⚠️ Could not create spec for: {plugin_name}")
        except Exception as e:
            logger.error(f"  ❌ Failed to load plugin '{plugin_name}': {e}", exc_info=True)
    
    logger.info(f"📦 Total main plugins loaded: {plugin_count}")

    # === Load Clone Plugins ===
    if CLONE_MODE:
        logger.info("\n🔸 Loading Clone Bot Plugins...")
        clone_plugin_count = 0
        for plugin_path in sorted(glob.glob("clone_plugins/*.py")):
            try:
                plugin_name = Path(plugin_path).stem
                if plugin_name.startswith("__"):
                    continue
                
                import_path = f"clone_plugins.{plugin_name}"
                
                # Skip if already loaded
                if import_path in sys.modules:
                    logger.debug(f"  ⏭️ Clone plugin already loaded: {plugin_name}")
                    continue
                
                spec = importlib.util.spec_from_file_location(import_path, plugin_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[import_path] = module
                    spec.loader.exec_module(module)
                    logger.info(f"  ✅ Loaded clone plugin: {plugin_name}")
                    clone_plugin_count += 1
                else:
                    logger.warning(f"  ⚠️ Could not create spec for: {plugin_name}")
            except Exception as e:
                logger.error(f"  ❌ Failed to load clone plugin '{plugin_name}': {e}", exc_info=True)
        
        logger.info(f"📦 Total clone plugins loaded: {clone_plugin_count}")
    else:
        logger.info("⚠️ Clone Mode Disabled - Skipping clone plugins.")

    # Start web server
    try:
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()
        logger.info(f"🌐 Web server started on {bind_address}:{PORT}")
    except Exception as e:
        logger.error(f"Failed to start web server: {e}")

    # Start keep-alive ping if on Heroku
    if ON_HEROKU:
        asyncio.create_task(ping_server())
        logger.info("📡 Keep-alive ping service started")

    # Log restart message
    try:
        tz = pytz.timezone('Asia/Kolkata')
        today = date.today()
        now = datetime.now(tz)
        time = now.strftime("%H:%M:%S %p")
        
        restart_text = script.RESTART_TXT.format(today, time) if hasattr(script, 'RESTART_TXT') else (
            f"<b>🔄 Bot Restarted Successfully!</b>\n\n"
            f"📅 Date: {today}\n"
            f"⏰ Time: {time}\n"
            f"🤖 Bot: @{bot_info.username}"
        )
        
        await StreamBot.send_message(
            chat_id=LOG_CHANNEL, 
            text=restart_text
        )
        logger.info("📨 Restart notification sent to LOG_CHANNEL")
    except Exception as e:
        logger.warning(f"Could not send restart message to LOG_CHANNEL: {e}")

    # Restart Clones
    if CLONE_MODE:
        logger.info("\n🔄 Restarting existing clone bots...")
        try:
            await restart_bots()
        except Exception as e:
            logger.error(f"Error during clone restart: {e}", exc_info=True)

    logger.info(f"\n{'='*50}")
    logger.info(f"✅ Bot Started Successfully!")
    logger.info(f"👤 Bot Username: @{bot_info.username}")
    logger.info(f"🆔 Bot ID: {bot_info.id}")
    logger.info(f"{'='*50}\n")
    
    await idle()

# Graceful shutdown
async def stop_bot():
    """Cleanup before shutdown"""
    logger.info("🛑 Stopping bot...")
    try:
        await StreamBot.stop()
        logger.info("✅ Bot stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping bot: {e}")

# Entrypoint
if __name__ == '__main__':
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user (KeyboardInterrupt).")
    except Exception as e:
        logger.exception(f"🔥 Fatal error: {e}")
    finally:
        logger.info("👋 Bot shutdown complete.")
