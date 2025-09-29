from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from config import FORCE_SUB_CHANNEL
import logging

logger = logging.getLogger(__name__)

async def handle_force_sub(client: Client, message):
    """
    Check if user is subscribed to the force-sub channel.
    Returns True if allowed, False if not.
    """
    if not FORCE_SUB_CHANNEL:
        return True

    try:
        user = await client.get_chat_member(FORCE_SUB_CHANNEL, message.from_user.id)
        if user.status in ["kicked", "left"]:
            raise UserNotParticipant
        return True

    except UserNotParticipant:
        try:
            # Generate invite link
            invite_link = await client.create_chat_invite_link(FORCE_SUB_CHANNEL)

            # Get bot username
            bot = await client.get_me()
            bot_username = bot.username or ""

            # Build try again URL
            start_param = message.command[1] if len(message.command) > 1 else ""
            try_again_url = f"https://t.me/{bot_username}?start={start_param}" if bot_username else ""

            buttons = [
                [InlineKeyboardButton("🔔 Join Channel", url=invite_link.invite_link)],
                [InlineKeyboardButton("🔄 Try Again", url=try_again_url)]
            ]

            await message.reply(
                "<b>🔒 You must join our channel to use this bot!</b>\n\n"
                "Please join the channel and click 'Try Again'.",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return False

        except Exception as e:
            logger.error(f"Force-sub invite error: {e}", exc_info=True)
            await message.reply(
                "⚠️ Something went wrong while checking channel. Please contact admin."
            )
            return False

    except Exception as e:
        logger.error(f"Unexpected force-sub error: {e}", exc_info=True)
        # Allow user in case of unexpected errors to prevent blocking
        return True
