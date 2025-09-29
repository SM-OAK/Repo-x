import base64
from pyrogram import Client, filters
from pyrogram.types import Message
from config import ADMINS, LOG_CHANNEL, PUBLIC_FILE_STORE, WEBSITE_URL_MODE, WEBSITE_URL, BOT_USERNAME
from Script import script
import logging

logger = logging.getLogger(__name__)

async def allowed(_, __, message):
    """Check if user is allowed to generate links"""
    if PUBLIC_FILE_STORE:
        return True
    if message.from_user and message.from_user.id in ADMINS:
        return True
    return False

@Client.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.private & filters.create(allowed))
async def incoming_gen_link(bot, message):
    """Generate link for uploaded files"""
    try:
        username = (await bot.get_me()).username
        
        # Copy file to log channel
        post = await message.copy(LOG_CHANNEL)
        file_id = str(post.id)
        
        # Generate encoded string
        string = f'file_{file_id}'
        outstr = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
        
        # Generate share link
        if WEBSITE_URL_MODE:
            share_link = f"{WEBSITE_URL}?start={outstr}"
        else:
            share_link = f"https://t.me/{username}?start={outstr}"
        
        # Send link to user
        await message.reply(
            script.FILE_TXT.format(original_link=share_link),
            quote=True
        )
        
    except Exception as e:
        logger.error(f"Error generating link: {e}")
        await message.reply("❌ Aɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ ᴡʜɪʟᴇ ɢᴇɴᴇʀᴀᴛɪɴɢ ʟɪɴᴋ!")

@Client.on_message(filters.command(['link']) & filters.create(allowed))
async def gen_link_command(bot, message):
    """Generate link for replied message"""
    replied = message.reply_to_message
    if not replied:
        return await message.reply('Rᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ɢᴇᴛ ᴀ sʜᴀʀᴇᴀʙʟᴇ ʟɪɴᴋ.')
    
    try:
        username = (await bot.get_me()).username
        
        # Copy replied message to log channel
        post = await replied.copy(LOG_CHANNEL)
        file_id = str(post.id)
        
        # Generate encoded string
        string = f"file_{file_id}"
        outstr = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
        
        # Generate share link
        if WEBSITE_URL_MODE:
            share_link = f"{WEBSITE_URL}?start={outstr}"
        else:
            share_link = f"https://t.me/{username}?start={outstr}"
        
        # Send link to user
        await message.reply(
            script.FILE_TXT.format(original_link=share_link),
            quote=True
        )
        
    except Exception as e:
        logger.error(f"Error generating link from reply: {e}")
        await message.reply("❌ Aɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ!")

@Client.on_message(filters.command("batch") & filters.private & filters.user(ADMINS))
async def batch_link_command(bot, message):
    """Generate batch link for multiple messages"""
    await message.reply(
        "<b>📦 Bᴀᴛᴄʜ Lɪɴᴋ Gᴇɴᴇʀᴀᴛᴏʀ</b>\n\n"
        "Fᴏʀᴡᴀʀᴅ ᴛʜᴇ Fɪʀsᴛ Mᴇssᴀɢᴇ ғʀᴏᴍ DB Cʜᴀɴɴᴇʟ (ᴡɪᴛʜ ǫᴜᴏᴛᴇs).\n\n"
        "Usᴇ /cancel ᴛᴏ ᴄᴀɴᴄᴇʟ."
    )

# Debug command for testing
@Client.on_message(filters.command("debug") & filters.user(ADMINS))
async def debug_genlink(client, message):
    await message.reply(f"✅ Gᴇɴʟɪɴᴋ Wᴏʀᴋɪɴɢ\n\nLOG_CHANNEL: {LOG_CHANNEL}")

print("✅ Genlink plugin loaded successfully!")
