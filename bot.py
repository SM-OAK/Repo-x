import logging
import asyncio
import sys
from pyrogram import Client, idle
from config import API_ID, API_HASH, BOT_TOKEN, BOT_USERNAME

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- Main Bot Client ---
app = Client(
    "main_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins={"root": "plugins"}
)

async def main():
    """
    Asynchronous main function to start, run, and stop the bot gracefully.
    """
    logger.info("--- Starting Bot ---")

    # Check for essential configuration variables
    if not all([API_ID, API_HASH, BOT_TOKEN, BOT_USERNAME]):
        logger.critical("FATAL ERROR: One or more essential config variables are missing.")
        sys.exit(1) # Exit the script with an error code

    try:
        # Start the main bot client
        await app.start()
        bot_info = await app.get_me()
        logger.info(f"✅ Bot started successfully as @{bot_info.username}")

        # Dynamically import and run the restart function only if it exists
        # This prevents errors if you decide to remove the file later
        try:
            from plugins.clone_manager import restart_bots
            logger.info("Attempting to restart clone bots...")
            await restart_bots()
            logger.info("✅ All clone bots restarted.")
        except ImportError:
            logger.warning("Could not import 'restart_bots'. Skipping clone restarts.")
        except Exception as e:
            logger.error(f"An error occurred during clone restart: {e}")

        # Keep the bot running until it's stopped
        await idle()

    except Exception as e:
        logger.error(f"An unexpected error occurred in the main bot loop: {e}", exc_info=True)
    finally:
        # Ensure the bot stops gracefully
        logger.info("--- Stopping Bot ---")
        await app.stop()
        logger.info("❌ Bot stopped successfully.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process interrupted by user (Ctrl+C). Shutting down.")

