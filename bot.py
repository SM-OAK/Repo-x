import logging
import asyncio
import sys

# --- Configuration ---
try:
    from config import API_ID, API_HASH, BOT_TOKEN, BOT_USERNAME
except ImportError:
    print("FATAL: config.py not found. Please check your configuration.")
    sys.exit(1)

# --- Library Import ---
# Switched from pyrogram to pyrofork to match your project's dependencies
try:
    from pyrofork import Client, idle
    from pyrofork.errors import AuthKeyUnregistered, UserDeactivated
except ImportError:
    print("FATAL: pyrofork is not installed. Please run: python3 -m pip install pyrofork")
    sys.exit(1)

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("pyrofork").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# --- Main Bot Application ---
# Removed the 'plugins' argument to fix the TypeError
app = Client(
    "main_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

async def main():
    """Main function to start the bot and handle startup errors."""
    logger.info("--- Attempting to start bot ---")

    try:
        await app.start()
        bot_info = await app.get_me()
        logger.info(f"✅ Bot logged in as @{bot_info.username} (ID: {bot_info.id})")

    except AuthKeyUnregistered:
        logger.critical("CRITICAL ERROR: AUTH_KEY_UNREGISTERED")
        logger.critical("Your BOT_TOKEN is invalid. Get a new one from @BotFather.")
        sys.exit(1)
    except UserDeactivated:
        logger.critical("CRITICAL ERROR: USER_DEACTIVATED")
        logger.critical("The bot account has been deleted. Create a new bot.")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"--- BOT FAILED TO START: {type(e).__name__} ---")
        logger.critical(e)
        sys.exit(1)

    logger.info("✅ Bot started successfully. Running idle...")
    await idle()
    
    logger.info("--- Bot is stopping ---")
    await app.stop()
    logger.info("❌ Bot stopped.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")
