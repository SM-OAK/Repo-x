import logging
import asyncio
from pyrogram import Client, idle   # back to pyrogram
from config import API_ID, API_HASH, BOT_TOKEN, BOT_USERNAME
from clone_manager import restart_bots

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

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
