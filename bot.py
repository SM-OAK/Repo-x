# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import sys
import glob
import importlib
from pathlib import Path
import logging
import logging.config
import asyncio
import pytz
from datetime import date, datetime 
from aiohttp import web

from pyrogram import Client, __version__, idle
from pyrogram.raw.all import layer
from config import (LOG_CHANNEL, ON_HEROKU, CLONE_MODE, PORT, API_ID, API_HASH, 
                    BOT_TOKEN, DB_URI, PING_INTERVAL, URL, SLEEP_THRESHOLD)
from Script import script 

# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

# --- NEW: Define the Bot Client directly here ---
StreamBot = Client(
    "StreamBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    sleep_threshold=SLEEP_THRESHOLD,
    plugins={"root": "plugins"}
)

# --- NEW: Define Keep-Alive and Web Server functions ---
async def ping_server():
    """Ping the web server to keep it alive on free hosting."""
    sleep_time = PING_INTERVAL
    while True:
        await asyncio.sleep(sleep_time)
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(URL) as resp:
                    print(f"Pinged server with status: {resp.status}")
        except Exception as e:
            print(f"An error occurred while pinging the server: {e}")

async def web_server():
    """Create a simple aiohttp web server."""
    async def handle(request):
        return web.Response(text="Bot is alive!")
    app = web.Application()
    app.add_routes([web.get('/', handle)])
    return app

async def initialize_clients():
    """Placeholder for client initialization if needed in the future."""
    print("Client initialization placeholder.")
    pass # No multi-client setup, so this is not needed.

# --- Fallback restart_bots function (from your original file) ---
try:
    from plugins.clone_manager import restart_bots
except ImportError:
    print("⚠️ plugins.clone_manager not found, using built-in restart function")
    async def restart_bots():
        """Restart all existing clone bots from database"""
        try:
            from pymongo import MongoClient
            
            mongo_client = MongoClient(DB_URI)
            db_name = DB_URI.split("/")[-1].split("?")[0] # Get DB name from URI
            mongo_db = mongo_client[db_name]
            
            bots = list(mongo_db.bots.find()) # Assuming collection name is 'bots'
            
            if not bots:
                print("No clones to restart")
                return
            
            print(f"Found {len(bots)} clone(s) to restart...")
            
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
                    print(f"  ✅ Restarted clone: @{bot_username}")
                    
                except Exception as e:
                    print(f"  ❌ Failed to restart @{bot_username}: {e}")
            
            print("Clone restart process completed")
            
        except Exception as e:
            print(f"Error in built-in restart_bots: {e}")

# --- Main Application Logic ---
async def start_bot():
    print('Initializing Bot...')
    await StreamBot.start()
    bot_info = await StreamBot.get_me()
    StreamBot.username = bot_info.username
    await initialize_clients()
    
    # Load plugins
    ppath = "plugins/*.py"
    files = glob.glob(ppath)
    print("\n🔹 Loading Main Bot Plugins...")
    for name in files:
        with open(name) as a:
            patt = Path(a.name)
            plugin_name = patt.stem
            plugins_dir = Path(f"plugins/{plugin_name}.py")
            import_path = f"plugins.{plugin_name}"
            spec = importlib.util.spec_from_file_location(import_path, plugins_dir)
            load = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(load)
            sys.modules[import_path] = load
            print(f"  ✅ Main Plugin => {plugin_name}")

    if CLONE_MODE:
        clone_ppath = "clone_plugins/*.py"
        clone_files = glob.glob(clone_ppath)
        print("\n🔸 Loading Clone Bot Plugins...")
        for name in clone_files:
            with open(name) as a:
                patt = Path(a.name)
                plugin_name = patt.stem
                if plugin_name == "__init__":
                    continue
                plugins_dir = Path(f"clone_plugins/{plugin_name}.py")
                import_path = f"clone_plugins.{plugin_name}"
                try:
                    spec = importlib.util.spec_from_file_location(import_path, plugins_dir)
                    load = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(load)
                    sys.modules[import_path] = load
                    print(f"  ✅ Clone Plugin => {plugin_name}")
                except Exception as e:
                    print(f"  ❌ Error loading clone plugin {plugin_name}: {e}")
    else:
        print("\n⚠️ Clone Mode Disabled - Skipping clone plugins")
    
    # Start web server and keep-alive
    if ON_HEROKU:
        asyncio.create_task(ping_server())
    
    app = web.AppRunner(await web_server())
    await app.setup()
    bind_address = "0.0.0.0"
    await web.TCPSite(app, bind_address, PORT).start()
    
    # Send restart message
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
        print(f"Error sending restart message to LOG_CHANNEL: {e}")

    # Restart existing clone bots
    if CLONE_MODE:
        print("\n🔄 Restarting existing clone bots...")
        await restart_bots()
    
    print("\n✅ Bot Started Successfully!")
    print(f"👤 Bot Username: @{bot_info.username}")
    print(f"🆔 Bot ID: {bot_info.id}")
    
    await idle()

if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(start_bot())
    except KeyboardInterrupt:
        logging.info('Service Stopped Bye 👋')
    except Exception as e:
        logging.error(f'Fatal Error: {e}', exc_info=True)
