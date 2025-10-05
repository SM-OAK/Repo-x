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
    """
    FIXED: Better logging and error handling during shutdown
    """
    print(f"\n⚠️ Shutdown initiated. Signal: {signal_received}")
    
    # Stop all clone bots
    if active_clones:
        print(f"🔄 Stopping {len(active_clones)} clone bot(s)...")
        for bot_id, bot_client in list(active_clones.items()):
            try:
                await bot_client.stop()
                print(f"  ✅ Stopped clone bot {bot_id}")
            except Exception as e:
                print(f"  ❌ Failed to stop clone {bot_id}: {e}")
    
    # Stop main bot
    try:
        await StreamBot.stop()
        print("✅ Main bot stopped")
    except Exception as e:
        print(f"❌ Failed to stop main bot: {e}")
    
    print("👋 Shutdown complete!")

# Register OS signals
def signal_handler(sig):
    asyncio.create_task(shutdown(sig))

for sig in (signal.SIGINT, signal.SIGTERM):
    asyncio.get_event_loop().add_signal_handler(sig, lambda s=sig: signal_handler(s))

# -------------------------------
# Safe import restart_bots
# -------------------------------
try:
    from plugins.clone_manager import restart_bots
except ImportError:
    print("⚠️ plugins.clone_manager not found, using fallback restart function")
    
    async def restart_bots():
        """
        Fallback function to restart clones if clone_manager import fails
        
        FIXED ISSUES:
        - ✅ Session naming now uses bot_id (consistent)
        - ✅ Better error handling
        """
        try:
            from pymongo import MongoClient
            mongo_client = MongoClient(DB_URI)
            mongo_db = mongo_client["cloned_vjbotz"]
            bots = list(mongo_db.bots.find())
            
            if not bots:
                print("No clones found in database")
                return
            
            print(f"Found {len(bots)} clone(s) in database...")
            success_count = 0
            
            for bot in bots:
                bot_id = bot.get('bot_id')
                bot_token = bot.get('bot_token')
                bot_username = bot.get('username', 'unknown')
                
                if not bot_token or not bot_id:
                    print(f"  ⚠️ Skipping invalid bot entry: {bot_username}")
                    continue
                
                try:
                    # FIX: Use bot_id as session name (consistent naming)
                    session_name = f"clone_sessions/{bot_id}"
                    clone_client = Client(
                        session_name,
                        API_ID,
                        API_HASH,
                        bot_token=bot_token,
                        plugins={"root": "clone_plugins"}
                    )
                    await clone_client.start()
                    active_clones[bot_id] = clone_client
                    success_count += 1
                    print(f"  ✅ Restarted clone: @{bot_username} (ID: {bot_id})")
                except Exception as e:
                    print(f"  ❌ Failed to restart @{bot_username}: {e}")
            
            print(f"✅ Successfully restarted {success_count}/{len(bots)} clone(s)")
            
        except Exception as e:
            print(f"❌ Error in restart_bots fallback: {e}")

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
    """
    FIXED: Better error handling and logging throughout startup
    """
    print("\n" + "="*50)
    print("🚀 Initializing Tech VJ Bot...")
    print("="*50 + "\n")
    
    try:
        bot_info = await StreamBot.get_me()
        StreamBot.username = bot_info.username
    except Exception as e:
        print(f"❌ Failed to get bot info: {e}")
        return

    # Initialize clients
    try:
        await initialize_clients()
        print("✅ Clients initialized")
    except Exception as e:
        print(f"⚠️ Client initialization warning: {e}")

    # Load main plugins
    print("\n🔹 Loading Main Plugins...")
    loaded_plugins = 0
    for name in files:
        try:
            with open(name) as a:
                plugin_name = Path(a.name).stem
                plugins_dir = Path(f"plugins/{plugin_name}.py")
                import_path = f"plugins.{plugin_name}"
                spec = importlib.util.spec_from_file_location(import_path, plugins_dir)
                load = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(load)
                sys.modules["plugins." + plugin_name] = load
                loaded_plugins += 1
                print(f"  ✅ {plugin_name}")
        except Exception as e:
            print(f"  ❌ Failed to load {plugin_name}: {e}")
    
    print(f"\n✅ Loaded {loaded_plugins} main plugins")

    # Load clone plugins if enabled
    if CLONE_MODE:
        print("\n🔸 Loading Clone Plugins...")
        loaded_clone_plugins = 0
        for name in clone_files:
            try:
                with open(name) as a:
                    plugin_name = Path(a.name).stem
                    if plugin_name == "__init__":
                        continue
                    plugins_dir = Path(f"clone_plugins/{plugin_name}.py")
                    import_path = f"clone_plugins.{plugin_name}"
                    spec = importlib.util.spec_from_file_location(import_path, plugins_dir)
                    load = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(load)
                    sys.modules["clone_plugins." + plugin_name] = load
                    loaded_clone_plugins += 1
                    print(f"  ✅ {plugin_name}")
            except Exception as e:
                print(f"  ❌ Failed to load clone plugin {plugin_name}: {e}")
        
        print(f"\n✅ Loaded {loaded_clone_plugins} clone plugins")
    else:
        print("\n⚠️ Clone Mode Disabled - Skipping clone plugins")

    # Keepalive for Heroku
    if ON_HEROKU:
        asyncio.create_task(ping_server())
        print("✅ Heroku keepalive started")

    # Start web server
    try:
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()
        print(f"✅ Web server started on port {PORT}")
    except Exception as e:
        print(f"⚠️ Web server error: {e}")

    # Send restart message to LOG_CHANNEL
    try:
        tz = pytz.timezone("Asia/Kolkata")
        today = date.today()
        now = datetime.now(tz)
        time = now.strftime("%H:%M:%S %p")
        await StreamBot.send_message(
            chat_id=LOG_CHANNEL, 
            text=script.RESTART_TXT.format(today, time)
        )
        print("✅ Restart notification sent")
    except Exception as e:
        print(f"⚠️ Failed to send restart notification: {e}")

    # Restart clone bots
    if CLONE_MODE:
        print("\n🔄 Restarting Clone Bots...")
        try:
            await restart_bots()
        except Exception as e:
            print(f"❌ Error restarting clones: {e}")

    # Startup complete
    print("\n" + "="*50)
    print("✅ Bot Started Successfully!")
    print("="*50)
    print(f"👤 Username: @{bot_info.username}")
    print(f"🆔 Bot ID: {bot_info.id}")
    print(f"📦 Pyrogram: v{__version__}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print(f"🤖 Active Clones: {len(active_clones)}")
    print("="*50)
    print("\n⚡ Powered By @VJ_Botz\n")

    # Idle with graceful shutdown
    try:
        await idle()
    except KeyboardInterrupt:
        print("\n⚠️ Keyboard interrupt received")
    finally:
        await shutdown("idle finished")

# -------------------------------
# Run bot
# -------------------------------
if __name__ == "__main__":
    try:
        loop.run_until_complete(start())
    except KeyboardInterrupt:
        logging.info("🛑 Service stopped by user (Ctrl+C)")
    except Exception as e:
        logging.error(f"💥 Fatal error: {e}", exc_info=True)
    finally:
        print("\n👋 Goodbye!")
