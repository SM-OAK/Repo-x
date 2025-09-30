# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import glob
import importlib
from pathlib import Path
from pyrogram import idle, Client, __version__
import logging
import logging.config
import asyncio
import pytz
from datetime import date, datetime
from aiohttp import web

logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

from config import LOG_CHANNEL, ON_HEROKU, CLONE_MODE, PORT
from Script import script
from TechVJ.server import web_server
from TechVJ.bot import StreamBot
from TechVJ.utils.keepalive import ping_server
from TechVJ.bot.clients import initialize_clients

def load_plugins(plugin_path):
    path = f"{plugin_path}/*.py"
    files = glob.glob(path)
    for name in files:
        with open(name) as a:
            patt = Path(a.name)
            plugin_name = patt.stem
            if plugin_name == "__init__": continue
            try:
                import_path = f"{plugin_path}.{plugin_name}"
                spec = importlib.util.spec_from_file_location(import_path, f"{plugin_path}/{plugin_name}.py")
                load = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(load)
                sys.modules[import_path] = load
                print(f"  ✅ Imported => {plugin_name}")
            except Exception as e:
                print(f"  ❌ Error importing {plugin_name}: {e}")

StreamBot.start()
StreamBot.ACTIVE_CLONES = {} # Initialize the live session tracker
loop = asyncio.get_event_loop()

async def start():
    print('Initializing Bot...')
    await initialize_clients()
    
    print("\n🔹 Loading Main Bot Plugins...")
    load_plugins("plugins")
    
    if ON_HEROKU:
        asyncio.create_task(ping_server())
    
    me = await StreamBot.get_me()
    
    app = web.AppRunner(await web_server())
    await app.setup()
    bind_address = "0.0.0.0"
    await web.TCPSite(app, bind_address, PORT).start()
    
    if CLONE_MODE:
        print("\n🔄 Restarting existing clone bots...")
        from plugins.clone_manager import restart_bots
        await restart_bots(StreamBot) # Pass the main client instance
    
    print(f"\n✅ Bot Started Successfully!\n👤 @{me.username}\n")
    await idle()
    print("\n🛑 Bot Stopped!")

if __name__ == '__main__':
    try:
        loop.run_until_complete(start())
    except KeyboardInterrupt:
        logging.info('Service Stopped Bye 👋')
