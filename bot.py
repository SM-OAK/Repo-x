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
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
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
    plugins={"root": "plugins"}  # This still works but we use manual loading for clarity
)

# Keep-alive ping for Heroku or other free hosting
async def ping_server():
    while True:
        await asyncio.sleep(PING_INTERVAL)
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(URL) as resp:
                    logger.info(f"Pinged server with status: {resp.status}")
        except Exception as e:
            logger.warning(f"Error while pinging server: {e}")

# Simple Web Server
async def web_server():
    async def handle(request):
        return web.Response(text="Bot is alive!")
    app = web.Application()
    app.add_routes([web.get('/', handle)])
    return app

# Clone Restart Handler
try:
    from plugins.clone_manager import restart_bots
except ImportError:
    logger.warning("plugins.clone_manager not found. Using fallback restart handler.")
    async def restart_bots():
        try:
            from pymongo import MongoClient
            mongo_client = MongoClient(DB_URI)
            db_name = DB_URI.split("/")[-1].split("?")[0]
            mongo_db = mongo_client[db_name]
            bots = list(mongo_db.bots.find())
            if not bots:
                logger.info("No clones to restart.")
                return
            for bot in bots:
                bot_token = bot.get('token')
                bot_username = bot.get('username', 'unknown')
                if not bot_token:
                    continue
                try:
                    clone_client = Client(
                        f"clone_{bot_token[:8]}",
                        api_id=API_ID,
                        api_hash=API_HASH,
                        bot_token=bot_token,
                        plugins={"root": "clone_plugins"}
                    )
                    await clone_client.start()
                    logger.info(f"✅ Restarted clone: @{bot_username}")
                except Exception as e:
                    logger.error(f"❌ Failed to restart @{bot_username}: {e}")
        except Exception as e:
            logger.error(f"Error in fallback restart_bots: {e}")

# Start Main Bot
async def start_bot():
    logger.info('🚀 Starting Bot...')
    await StreamBot.start()
    bot_info = await StreamBot.get_me()
    StreamBot.username = bot_info.username

    # === Load Main Plugins ===
    logger.info("\n🔹 Loading Main Bot Plugins...")
    for plugin_path in glob.glob("plugins/*.py"):
        try:
            plugin_name = Path(plugin_path).stem
            if plugin_name == "__init__":
                continue
            import_path = f"plugins.{plugin_name}"
            spec = importlib.util.spec_from_file_location(import_path, plugin_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            sys.modules[import_path] = module
            logger.info(f"  ✅ Loaded plugin: {plugin_name}")
        except Exception as e:
            logger.error(f"  ❌ Failed to load plugin '{plugin_name}': {e}")

    # === Load Clone Plugins ===
    if CLONE_MODE:
        logger.info("\n🔸 Loading Clone Bot Plugins...")
        for plugin_path in glob.glob("clone_plugins/*.py"):
            try:
                plugin_name = Path(plugin_path).stem
                if plugin_name == "__init__":
                    continue
                import_path = f"clone_plugins.{plugin_name}"
                spec = importlib.util.spec_from_file_location(import_path, plugin_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                sys.modules[import_path] = module
                logger.info(f"  ✅ Loaded clone plugin: {plugin_name}")
            except Exception as e:
                logger.error(f"  ❌ Failed to load clone plugin '{plugin_name}': {e}")
    else:
        logger.info("⚠️ Clone Mode Disabled - Skipping clone plugins.")

    # Start aiohttp server if on Heroku
    if ON_HEROKU:
        asyncio.create_task(ping_server())

    app = web.AppRunner(await web_server())
    await app.setup()
    await web.TCPSite(app, "0.0.0.0", PORT).start()

    # Log restart message
    try:
        tz = pytz.timezone('Asia/Kolkata')
        today = date.today()
        now = datetime.now(tz)
        time = now.strftime("%H:%M:%S %p")
        await StreamBot.send_message(
            chat_id=LOG_CHANNEL, 
            text=script.RESTART_TXT.format(today, time)
        )
    except Exception as e:
        logger.warning(f"Could not send restart message to LOG_CHANNEL: {e}")

    # Restart Clones
    if CLONE_MODE:
        logger.info("\n🔄 Restarting existing clone bots...")
        await restart_bots()

    logger.info(f"\n✅ Bot Started Successfully!\n👤 Bot Username: @{bot_info.username}\n🆔 Bot ID: {bot_info.id}")
    await idle()

# Entrypoint
if __name__ == '__main__':
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user (KeyboardInterrupt).")
    except Exception as e:
        logger.exception(f"🔥 Fatal error: {e}")
