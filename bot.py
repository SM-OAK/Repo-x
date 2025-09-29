import logging
import asyncio
import sys
from pyrogram import Client, idle
from pyrogram.errors import exceptions

# --- Configuration ---
# Make sure these are imported correctly from your config file
try:
    from config import API_ID, API_HASH, BOT_TOKEN, BOT_USERNAME
except ImportError:
    print("FATAL: config.py not found or variables are missing. Please check your configuration.")
    sys.exit(1)

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("pyrogram").setLevel(logging.WARNING) # Quieten pyrogram's own logs
logger = logging.getLogger(__name__)

# --- Main Bot Application ---
app = Client(
    "main_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins={"root": "plugins"}
)

async def main():
    """Main function to start the bot and handle startup errors."""
    logger.info("--- Attempting to start bot ---")

    # This block will try to start the bot and catch the specific first error.
    try:
        await app.start()
        bot_info = await app.get_me()
        logger.info(f"✅ Bot logged in as @{bot_info.username} (ID: {bot_info.id})")

        # The clone restart part is still commented out as per our last step.
        # If you fix the underlying data issue, you can re-enable this.
        # try:
        #     from plugins.clone_manager import restart_bots
        #     logger.info("Attempting to restart clone bots...")
        #     await restart_bots()
        #     logger.info("✅ All clone bots checked.")
        # except ImportError:
        #     logger.warning("Could not import 'restart_bots'. Skipping clone restarts.")

    except exceptions.bad_request_400.AuthKeyUnregistered:
        logger.critical("CRITICAL ERROR: AUTH_KEY_UNREGISTERED")
        logger.critical("Your BOT_TOKEN is invalid or has been revoked. Please get a new one from @BotFather.")
        sys.exit(1)
    except exceptions.bad_request_400.UserDeactivated:
        logger.critical("CRITICAL ERROR: USER_DEACTIVATED")
        logger.critical("The bot account has been deleted. Please create a new bot on @BotFather and use its token.")
        sys.exit(1)
    except Exception as e:
        # This will catch any other startup error.
        logger.critical("--- BOT FAILED TO START ---")
        logger.critical(f"AN UNEXPECTED ERROR OCCURRED: {type(e).__name__} - {e}")
        logger.critical("Please review your configuration and the error message above.")
        sys.exit(1)

    # If startup was successful, the bot will run idle.
    logger.info("✅ Bot started successfully. Running idle...")
    await idle()

    # Graceful shutdown
    logger.info("--- Bot is stopping ---")
    await app.stop()
    logger.info("❌ Bot stopped.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process interrupted by user. Shutting down.")

