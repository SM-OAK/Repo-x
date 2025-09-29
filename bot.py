# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import sys
import glob
import importlib
from pathlib import Path
from pyrogram import idle
import logging
import logging.config

# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from config import LOG_CHANNEL, ON_HEROKU, CLONE_MODE, PORT
from typing import Union, Optional, AsyncGenerator
from pyrogram import types
from Script import script 
from datetime import date, datetime 
import pytz
from aiohttp import web
from TechVJ.server import web_server

import asyncio
from pyrogram import idle
from plugins.clone import restart_bots
from TechVJ.bot import StreamBot
from TechVJ.utils.keepalive import ping_server
from TechVJ.bot.clients import initialize_clients

# Load main bot plugins
ppath = "plugins/*.py"
files = glob.glob(ppath)

# Load clone plugins
clone_ppath = "clone_plugins/*.py"
clone_files = glob.glob(clone_ppath)

StreamBot.start()
loop = asyncio.get_event_loop()

async def start():
    print('\n')
    print('Initializing Tech VJ Bot')
    bot_info = await StreamBot.get_me()
    StreamBot.username = bot_info.username
    await initialize_clients()
    
    # Load main bot plugins
    print("\n🔹 Loading Main Bot Plugins...")
    for name in files:
        with open(name) as a:
            patt = Path(a.name)
            plugin_name = patt.stem.replace(".py", "")
            plugins_dir = Path(f"plugins/{plugin_name}.py")
            import_path = "plugins.{}".format(plugin_name)
            spec = importlib.util.spec_from_file_location(import_path, plugins_dir)
            load = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(load)
            sys.modules["plugins." + plugin_name] = load
            print(f"  ✅ Main Plugin => {plugin_name}")
    
    # Load clone plugins if CLONE_MODE is enabled
    if CLONE_MODE:
        print("\n🔸 Loading Clone Bot Plugins...")
        for name in clone_files:
            with open(name) as a:
                patt = Path(a.name)
                plugin_name = patt.stem.replace(".py", "")
                
                # Skip __init__.py
                if plugin_name == "__init__":
                    continue
                    
                plugins_dir = Path(f"clone_plugins/{plugin_name}.py")
                import_path = "clone_plugins.{}".format(plugin_name)
                
                try:
                    spec = importlib.util.spec_from_file_location(import_path, plugins_dir)
                    load = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(load)
                    sys.modules["clone_plugins." + plugin_name] = load
                    print(f"  ✅ Clone Plugin => {plugin_name}")
                except Exception as e:
                    print(f"  ❌ Error loading clone plugin {plugin_name}: {e}")
    else:
        print("\n⚠️ Clone Mode Disabled - Skipping clone plugins")
    
    # Start keepalive if on Heroku
    if ON_HEROKU:
        asyncio.create_task(ping_server())
    
    # Get bot info
    me = await StreamBot.get_me()
    tz = pytz.timezone('Asia/Kolkata')
    today = date.today()
    now = datetime.now(tz)
    time = now.strftime("%H:%M:%S %p")
    
    # Start web server
    app = web.AppRunner(await web_server())
    await StreamBot.send_message(
        chat_id=LOG_CHANNEL, 
        text=script.RESTART_TXT.format(today, time)
    )
    await app.setup()
    bind_address = "0.0.0.0"
    await web.TCPSite(app, bind_address, PORT).start()
    
    # Restart existing clone bots if enabled
    if CLONE_MODE:
        print("\n🔄 Restarting existing clone bots...")
        await restart_bots()
    
    print("\n✅ Bot Started Successfully!")
    print(f"👤 Bot Username: @{me.username}")
    print(f"🆔 Bot ID: {me.id}")
    print(f"📦 Pyrogram Version: {__version__}")
    print(f"🔧 Python Version: {sys.version.split()[0]}")
    print("\n⚡ Powered By @VJ_Botz\n")
    
    await idle()

# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

if __name__ == '__main__':
    try:
        loop.run_until_complete(start())
    except KeyboardInterrupt:
        logging.info('Service Stopped Bye 👋')
    except Exception as e:
        logging.error(f'Fatal Error: {e}')

# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01
