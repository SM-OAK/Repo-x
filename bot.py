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
# We are now using the official pyrogram library
try:
    from pyrogram import Client, idle
    from pyrogram.errors import AuthKeyUnregistered, UserDeactivated
except ImportError:
    print("FATAL: pyrogram is not installed. Please run: python3 -m pip install -U pyrogram TgCrypto")
    sys.exit(1)

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# --- Main Bot Application ---
# Re-added the 'plugins' argument, which is correct for the official pyrogram library
app = Client(
    "main_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins={"root": "plugins"}
)

async def main():
    """Main function to start the bot and handle startup errors."""
    logger.info("--- Attempting to start bot using Pyrogram ---")

    try:
        await app.start()
        bot_info = await app.get_me()
        logger.info(f"✅ Bot logged in as @{bot_info.username} (ID: {bot_info.id})")

    except AuthKeyUnregistered:
        logger.critical("CRITICAL ERROR: AUTH_KEY_UNREGISTERED")
        logger.critical("Your BOT_TOKEN is invalid. Get a new one from @BotFather and delete main_bot.session")
        sys.exit(1)
    except UserDeactivated:
        logger.critical("CRITICAL ERROR: USER_DEACTIVATED")
        logger.critical("The bot account has been deleted. Create a new bot on @BotFather.")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"--- BOT FAILED TO START: {type(e).__name__} ---")
        logger.critical(e)
        sys.exit(1)

    logger.info("✅ Bot started successfully with all plugins loaded. Running idle...")
    await idle()
    
    logger.info("--- Bot is stopping ---")
    await app.stop()
    logger.info("❌ Bot stopped.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process interrupted by user.")

