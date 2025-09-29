import logging
import asyncio
import sys

# --- Configuration ---
try:
    from config import API_ID, API_HASH, BOT_TOKEN, BOT_USERNAME
except ImportError:
    print("❌ FATAL: config.py not found. Please check your configuration.")
    sys.exit(1)

# --- Library Import ---
try:
    from pyrogram import Client, idle
    from pyrogram.errors import AuthKeyUnregistered, UserDeactivated
except ImportError:
    print("❌ FATAL: Pyrogram is not installed.")
    print("👉 Run: python3 -m pip install -U pyrogram TgCrypto")
    sys.exit(1)

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logger = logging.getLogger("MainBot")

# --- Main Bot Application ---
app = Client(
    "main_bot",
    api_id=int(API_ID) if API_ID else 0,
    api_hash=str(API_HASH),
    bot_token=str(BOT_TOKEN),
    plugins={"root": "plugins"}
)

async def main():
    """Main entrypoint: start bot, load plugins, handle errors."""
    logger.info("🚀 Attempting to start bot with Pyrogram...")

    # --- Config sanity check ---
    if not API_ID or not API_HASH or not BOT_TOKEN:
        logger.critical("❌ Missing essential configuration (API_ID/API_HASH/BOT_TOKEN).")
        sys.exit(1)

    try:
        await app.start()
        me = await app.get_me()
        logger.info(f"✅ Bot logged in as @{me.username} (ID: {me.id})")

        # --- Try restarting clones (if available) ---
        try:
            from clone_manager import restart_bots
            logger.info("🔄 Restarting clone bots...")
            await restart_bots()
            logger.info("✅ Clone bots restarted.")
        except ImportError:
            logger.warning("⚠️ clone_manager.py not found. Skipping clone restarts.")
        except Exception as e:
            logger.error(f"Clone restart failed: {e}", exc_info=True)

        logger.info("✅ All plugins loaded. Bot is now running...")
        await idle()

    except AuthKeyUnregistered:
        logger.critical("❌ AUTH_KEY_UNREGISTERED: Invalid BOT_TOKEN.")
        logger.critical("👉 Get a new token from @BotFather and delete main_bot.session")
        sys.exit(1)
    except UserDeactivated:
        logger.critical("❌ USER_DEACTIVATED: Bot account deleted.")
        logger.critical("👉 Create a new bot via @BotFather.")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"❌ BOT FAILED TO START: {type(e).__name__}")
        logger.critical(str(e))
        sys.exit(1)

    finally:
        logger.info("🛑 Stopping bot...")
        try:
            await app.stop()
            logger.info("❌ Bot stopped successfully.")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Process interrupted by user (Ctrl+C). Exiting...")
    except RuntimeError as e:
        # Fix for environments where asyncio.run() isn't supported
        logger.warning(f"RuntimeError: {e} — using loop.run_until_complete() fallback.")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
