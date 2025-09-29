from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from config import FORCE_SUB_CHANNEL
import logging

logger = logging.getLogger(__name__)

async def handle_force_sub(client, message):
    """Check if user is subscribed to force sub channel"""
    if not FORCE_SUB_CHANNEL:
        return True
    
    try:
        user = await client.get_chat_member(FORCE_SUB_CHANNEL, message.from_user.id)
        if user.status in ["kicked", "left"]:
            raise UserNotParticipant
        return True
        
    except UserNotParticipant:
        try:
            invite_link = await client.create_chat_invite_link(FORCE_SUB_CHANNEL)
            buttons = [[
                InlineKeyboardButton("🔔 Jᴏɪɴ Cʜᴀɴɴᴇʟ", url=invite_link.invite_link)
            ], [
                InlineKeyboardButton("🔄 Tʀʏ Aɢᴀɪɴ", url=f"https://t.me/{client.me.username}?start={message.command[1]}")
            ]]
            
            await message.reply_text(
                "<b>🔒 Yᴏᴜ ᴍᴜsᴛ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴜsᴇ ᴛʜɪs ʙᴏᴛ!</b>\n\n"
                "Pʟᴇᴀsᴇ ᴊᴏɪɴ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ᴀɴᴅ ᴄʟɪᴄᴋ 'Tʀʏ Aɢᴀɪɴ' ʙᴜᴛᴛᴏɴ.",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return False
            
        except Exception as e:
            logger.error(f"Force sub error: {e}")
            await message.reply_text(
                "Sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ. Pʟᴇᴀsᴇ ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ."
            )
            return False
    
    except Exception as e:
        logger.error(f"Unexpected fsub error: {e}")
        return True
