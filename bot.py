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
from pyrogram import Client, idle, __version__
from pyrogram.raw.all import layer
from aiohttp import web
from datetime import date, datetime
import pytz

# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

from config import LOG_CHANNEL, ON_HEROKU, CLONE_MODE, PORT
from Script import script
from TechVJ.server import web_server
from TechVJ.bot import StreamBot
from TechVJ.utils.keepalive import ping_server
from TechVJ.bot.clients import initialize_clients
from plugins.clone_manager import start_bots # CORRECTED: Changed 'restart_bots' to 'start_bots'

# Load main bot plugins
ppath = "plugins/*.py"
files = glob.glob(ppath)

# Load clone plugins
clone_ppath = "clone_plugins/*.py"
clone_files = glob.glob(clone_ppath)

async def start():
    print("Initializing Tech VJ Bot")
    await StreamBot.start()
    bot_info = await StreamBot.get_me()
    StreamBot.username = bot_info.username
    await initialize_clients()
    
    # Load main bot plugins
    print("\n🔹 Loading Main Bot Plugins...")
    for name in files:
        with open(name) as a:
            patt = Path(a.name)
            plugin_name = patt.stem
            try:
                import_path = f"plugins.{plugin_name}"
                importlib.import_module(import_path)
                print(f"  ✅ Main Plugin => {plugin_name}")
            except Exception as e:
                print(f"  ❌ Error loading main plugin {plugin_name}: {e}")

    # Load clone plugins if CLONE_MODE is enabled
    if CLONE_MODE:
        print("\n🔸 Loading Clone Bot Plugins...")
        for name in clone_files:
            with open(name) as a:
                patt = Path(a.name)
                plugin_name = patt.stem
                if plugin_name == "__init__":
                    continue
                try:
                    import_path = f"clone_plugins.{plugin_name}"
                    importlib.import_module(import_path)
                    print(f"  ✅ Clone Plugin => {plugin_name}")
                except Exception as e:
                    print(f"  ❌ Error loading clone plugin {plugin_name}: {e}")
    else:
        print("\n⚠️ Clone Mode Disabled - Skipping clone plugins")
    
    # Start keepalive if on Heroku
    if ON_HEROKU:
        asyncio.create_task(ping_server())
    
    # Send restart message and start web server
    tz = pytz.timezone('Asia/Kolkata')
    time = datetime.now(tz).strftime("%H:%M:%S %p")
    today = date.today()
    await StreamBot.send_message(
        chat_id=LOG_CHANNEL, 
        text=script.RESTART_TXT.format(today, time)
    )
    app = web.AppRunner(await web_server())
    await app.setup()
    await web.TCPSite(app, "0.0.0.0", PORT).start()
    
    # Restart existing clone bots if enabled
    if CLONE_MODE:
        print("\n🔄 Restarting existing clone bots...")
        await start_bots() # CORRECTED: Changed 'restart_bots()' to 'start_bots()'
    
    print("\n✅ Bot Started Successfully!")
    print(f"👤 Bot Username: @{bot_info.username}")
    print(f"🆔 Bot ID: {bot_info.id}")
    
    await idle()


if __name__ == '__main__':
    try:
        asyncio.get_event_loop().run_until_complete(start())
    except KeyboardInterrupt:
        logging.info('Service Stopped Bye 👋')
    except Exception as e:
        logging.error(f'Fatal Error: {e}', exc_info=True)
