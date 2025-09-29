import logging
import asyncio
import sys
from pyrogram import Client, idle
from config import API_ID, API_HASH, BOT_TOKEN, BOT_USERNAME

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("MainBot")

# --- Main Bot Client ---
app = Client(
    "main_bot",
    api_id=int(API_ID) if API_ID else 0,
    api_hash=str(API_HASH),
    bot_token=str(BOT_TOKEN),
    plugins={"root": "plugins"}
)


async def safe_restart_bots():
    """
    Try to restart clone bots if restart_bots() exists.
    """
    try:
        from clone_manager import restart_bots  # ✅ fixed path
        logger.info("Attempting to restart clone bots...")
        await restart_bots()
        logger.info("✅ Clone bots restarted.")
    except ImportError:
        logger.warning("Clone manager not found. Skipping clone restarts.")
    except Exception as e:
        logger.error(f"Clone restart failed: {e}", exc_info=True)


async def main():
    """
    Asynchronous main function to start, run, and stop the bot gracefully.
    """
    logger.info("🚀 Starting bot...")

    # --- Config validation ---
    if not API_ID or not API_HASH or not BOT_TOKEN:
        logger.critical("❌ FATAL: Missing essential config variables (API_ID/API_HASH/BOT_TOKEN).")
        sys.exit(1)

    try:
        # Start bot
        await app.start()
        me = await app.get_me()
        logger.info(f"✅ Bot started successfully as @{me.username} (ID: {me.id})")

        # Restart clones if enabled
        await safe_restart_bots()

        # Keep alive
        await idle()

    except Exception as e:
        logger.critical(f"Unexpected error in main loop: {e}", exc_info=True)

    finally:
        # Ensure graceful shutdown
        logger.info("🛑 Stopping bot...")
        try:
            await app.stop()
            logger.info("❌ Bot stopped successfully.")
        except Exception as e:
            logger.error(f"Error while stopping bot: {e}", exc_info=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process interrupted by user (Ctrl+C). Exiting...")
    except RuntimeError as e:
        # Fix for "asyncio.run() cannot be called from a running event loop"
        logger.warning(f"RuntimeError: {e}. Falling back to loop.run_until_complete().")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
