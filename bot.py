# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import sys
import glob
import importlib
import logging
import logging.config
import asyncio
from pathlib import Path

# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("aiohttp.access").setLevel(logging.WARNING)

from pyrogram import Client, idle
from config import LOG_CHANNEL, ON_HEROKU, CLONE_MODE, PORT
from Script import script
from datetime import date, datetime
import pytz
from aiohttp import web

# --- Local Imports ---
from TechVJ.server import web_server
from TechVJ.bot import StreamBot
from TechVJ.utils.keepalive import ping_server
from TechVJ.bot.clients import initialize_clients
from plugins.clone import restart_all_clones # Corrected function name

async def main():
    """Main function to initialize and run the bot."""
    
    # Start the main bot client first
    await StreamBot.start()
    
    bot_info = await StreamBot.get_me()
    StreamBot.username = bot_info.username
    
    print("\nInitializing Client...")
    await initialize_clients()
    
    # Dynamically import all plugins
    ppath = "plugins/*.py"
    files = glob.glob(ppath)
    print("\nImporting Plugins...")
    for name in files:
        try:
            with open(name) as a:
                patt = Path(a.name)
                plugin_name = patt.stem
                import_path = f"plugins.{plugin_name}"
                spec = importlib.util.spec_from_file_location(import_path, name)
                load = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(load)
                sys.modules[import_path] = load
                print(f"✅ Imported: {plugin_name}")
        except Exception as e:
            print(f"❌ Failed to import {name}: {e}")

    # Start the web server if on Heroku
    if ON_HEROKU:
        asyncio.create_task(ping_server())
        app = web.AppRunner(await web_server())
        await app.setup()
        await web.TCPSite(app, "0.0.0.0", PORT).start()
        print("\nWeb Server Started!")

    # Send restart message
    tz = pytz.timezone('Asia/Kolkata')
    today = date.today()
    now = datetime.now(tz)
    time = now.strftime("%H:%M:%S %p")
    try:
        await StreamBot.send_message(
            chat_id=LOG_CHANNEL, 
            text=script.RESTART_TXT.format(today, time)
        )
    except Exception as e:
        print(f"Error sending restart message to LOG_CHANNEL: {e}")
    
    # Restart all cloned bots if clone mode is enabled
    if CLONE_MODE:
        print("\nRestarting Cloned Bots...")
        await restart_all_clones()

    print("\nBot Started! Powered By @VJ_Botz")
    await idle()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info('Service Stopped Bye 👋')
