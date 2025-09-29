import logging
import asyncio
from pyrofork import Client, idle   # ✅ correct import, no extra comment!
from config import API_ID, API_HASH, BOT_TOKEN, BOT_USERNAME
from clone_manager import restart_bots

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Main bot client
app = Client(
    "main_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins={"root": "plugins"}
)

async def main():
    try:
        await app.start()
        logger.info(f"✅ Bot started as @{BOT_USERNAME}")

        # Restart all clone bots from DB
        await restart_bots()

        logger.info("✅ All clone bots restarted")
        await idle()

    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        await app.stop()
        logger.info("❌ Bot stopped")

if __name__ == "__main__":
    asyncio.run(main())
