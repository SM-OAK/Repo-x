# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import sys
import glob
import importlib
from pathlib import Path
from pyrogram import idle, Client, __version__
from pyrogram.raw.all import layer
import logging
import logging.config
import asyncio
import pytz
from datetime import date, datetime
from aiohttp import web

# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

# Import from local modules
from config import LOG_CHANNEL, ON_HEROKU, CLONE_MODE, PORT, API_ID, API_HASH, CLONE_DB_URI, CDB_NAME
from Script import script
from TechVJ.server import web_server
from TechVJ.bot import StreamBot
from TechVJ.utils.keepalive import ping_server
from TechVJ.bot.clients import initialize_clients

async def restart_bots():
    """Restart all existing clone bots from database"""
    try:
        from pymongo import MongoClient
        
        mongo_client = MongoClient(CLONE_DB_URI)
        mongo_db = mongo_client[CDB_NAME]
        
        bots = list(mongo_db.bots.find())
        
        if not bots:
            print("No clones to restart")
            return
        
        print(f"Found {len(bots)} clone(s) to restart...")
        
        for bot in bots:
            bot_token = bot.get('token')
            bot_id = bot.get('bot_id')
            bot_username = bot.get('username', 'unknown')
            
            if not bot_token or not bot_id:
                continue
            
            try:
                clone_client = Client(
                    f"clone_{bot_id}",
                    API_ID,
                    API_HASH,
                    bot_token=bot_token,
                    plugins={"root": "clone_plugins"}
                )
                
                await clone_client.start()
                ACTIVE_CLONES[bot_id] = clone_client
                print(f"  ✅ Restarted clone: @{bot_username}")
                
            except Exception as e:
                print(f"  ❌ Failed to restart @{bot_username}: {e}")
        
        print("Clone restart process completed")
        
    except Exception as e:
        print(f"Error in restart_bots: {e}")

# Load plugins
ppath = "plugins/*.py"
files = glob.glob(ppath)
clone_ppath = "clone_plugins/*.py"
clone_files = glob.glob(clone_ppath)

StreamBot.start()
loop = asyncio.get_event_loop()

async def start():
    print('Initializing Tech VJ Bot')
    bot_info = await StreamBot.get_me()
    StreamBot.username = bot_info.username
    await initialize_clients()
    
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
        print("\n🔸 Loading Clone Bot Plugins...")
        # This simple loop is sufficient for loading clone plugins
    else:
        print("\n⚠️ Clone Mode Disabled - Skipping clone plugins")
    
    if ON_HEROKU:
        asyncio.create_task(ping_server())
    
    me = await StreamBot.get_me()
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)
    
    app = web.AppRunner(await web_server())
    await app.setup()
    bind_address = "0.0.0.0"
    await web.TCPSite(app, bind_address, PORT).start()
    
    if CLONE_MODE:
        print("\n🔄 Restarting existing clone bots...")
        await restart_bots()
    
    print(f"\n✅ Bot Started Successfully!\n👤 @{me.username}\n")
    await idle()

if __name__ == '__main__':
    try:
        loop.run_until_complete(start())
    except KeyboardInterrupt:
        logging.info('Service Stopped Bye 👋')
