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
import asyncio
import signal
import pytz
from datetime import date, datetime
from aiohttp import web

# Logging setup
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from config import LOG_CHANNEL, ON_HEROKU, CLONE_MODE, PORT, API_ID, API_HASH, DB_URI
from Script import script
from TechVJ.server import web_server
from TechVJ.bot import StreamBot
from TechVJ.utils.keepalive import ping_server
from TechVJ.bot.clients import initialize_clients

# -------------------------------
# Active clones for graceful shutdown
# -------------------------------
try:
    from plugins.clone_manager import active_clones
except ImportError:
    active_clones = {}

# -------------------------------
# Graceful Shutdown
# -------------------------------
async def shutdown(signal_received=None):
    print(f"⚠️ Shutdown initiated. Signal: {signal_received}")
    # Stop all clone bots
    for bot_id, bot_client in active_clones.items():
        try:
            await bot_client.stop()
            print(f"✅ Stopped clone bot {bot_id}")
        except Exception as e:
            print(f"❌ Failed to stop clone {bot_id}: {e}")
    # Stop main bot
    try:
        await StreamBot.stop()
        print("✅ Main bot stopped")
    except Exception as e:
        print(f"❌ Failed to stop main bot: {e}")
    # Stop event loop
    asyncio.get_event_loop().stop()

# Register OS signals
for sig in (signal.SIGINT, signal.SIGTERM):
    asyncio.get_event_loop().add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s)))

# -------------------------------
# Safe import restart_bots
# -------------------------------
try:
    from plugins.clone_manager import restart_bots
except ImportError:
    print("⚠️ plugins.clone not found, using fallback restart function")
    async def restart_bots():
        """Restart all clones from DB"""
        try:
            from pymongo import MongoClient
            mongo_client = MongoClient(DB_URI)
            mongo_db = mongo_client["cloned_vjbotz"]
            bots = list(mongo_db.bots.find())
            if not bots:
                print("No clones to restart")
                return
            print(f"Found {len(bots)} clone(s) to restart...")
            for bot in bots:
                bot_token = bot.get('bot_token')
                bot_username = bot.get('username', 'unknown')
                if not bot_token:
                    continue
                try:
                    clone_client = Client(
                        f"clone_{bot_token[:8]}",
                        API_ID,
                        API_HASH,
                        bot_token=bot_token,
                        plugins={"root": "clone_plugins"}
                    )
                    await clone_client.start()
                    active_clones[bot.get('bot_id')] = clone_client
                    print(f"  ✅ Restarted clone: @{bot_username}")
                except Exception as e:
                    print(f"  ❌ Failed to restart @{bot_username}: {e}")
            print("Clone restart process completed")
        except Exception as e:
            print(f"Error in restart_bots: {e}")

# -------------------------------
# Load Plugins
# -------------------------------
# Main bot plugins
ppath = "plugins/*.py"
files = glob.glob(ppath)

# Clone plugins
clone_ppath = "clone_plugins/*.py"
clone_files = glob.glob(clone_ppath)

StreamBot.start()
loop = asyncio.get_event_loop()

async def start():
    print("\nInitializing Tech VJ Bot...")
    bot_info = await StreamBot.get_me()
    StreamBot.username = bot_info.username

    # Initialize clients
    await initialize_clients()

    # Load main plugins
    print("\n🔹 Loading Main Plugins...")
    for name in files:
        with open(name) as a:
            plugin_name = Path(a.name).stem
            plugins_dir = Path(f"plugins/{plugin_name}.py")
            import_path = f"plugins.{plugin_name}"
            spec = importlib.util.spec_from_file_location(import_path, plugins_dir)
            load = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(load)
            sys.modules["plugins." + plugin_name] = load
            print(f"  ✅ Main Plugin => {plugin_name}")

    # Load clone plugins if enabled
    if CLONE_MODE:
        print("\n🔸 Loading Clone Plugins...")
        for name in clone_files:
            with open(name) as a:
                plugin_name = Path(a.name).stem
                if plugin_name == "__init__":
                    continue
                plugins_dir = Path(f"clone_plugins/{plugin_name}.py")
                import_path = f"clone_plugins.{plugin_name}"
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

    # Keepalive for Heroku
    if ON_HEROKU:
        asyncio.create_task(ping_server())

    # Start web server
    app = web.AppRunner(await web_server())
    await app.setup()
    bind_address = "0.0.0.0"
    await web.TCPSite(app, bind_address, PORT).start()

    # Send restart message to LOG_CHANNEL
    tz = pytz.timezone("Asia/Kolkata")
    today = date.today()
    now = datetime.now(tz)
    time = now.strftime("%H:%M:%S %p")
    await StreamBot.send_message(chat_id=LOG_CHANNEL, text=script.RESTART_TXT.format(today, time))

    # Restart clone bots
    if CLONE_MODE:
        print("\n🔄 Restarting existing clone bots...")
        try:
            await restart_bots()
        except Exception as e:
            print(f"❌ Error restarting clones: {e}")

    # Startup complete
    print("\n✅ Bot Started Successfully!")
    print(f"👤 Bot Username: @{bot_info.username}")
    print(f"🆔 Bot ID: {bot_info.id}")
    print(f"📦 Pyrogram Version: {__version__}")
    print(f"🔧 Python Version: {sys.version.split()[0]}")
    print("\n⚡ Powered By @VJ_Botz\n")

    # Idle with graceful shutdown
    try:
        await idle()
    finally:
        await shutdown("idle finished")

# -------------------------------
# Run bot
# -------------------------------
if __name__ == "__main__":
    try:
        loop.run_until_complete(start())
    except KeyboardInterrupt:
        logging.info("Service stopped by user 👋")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
