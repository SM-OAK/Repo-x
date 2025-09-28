# plugins/genlink.py - Updated by Gemini# plugins/genlink.py - Updated by Gemini
# Fully compatible with the Power Panel and live settings.
# Don't Remove Credit Tg - @VJ_Botz

import base64
from pyrogram import Client, filters
from pyrogram.types import Message
import config # Import the whole config module
from plugins.users_api import get_user, get_short_link

# This function now reads the public mode setting live from the config module
async def allowed(_, __, message):
    if config.PUBLIC_FILE_STORE:
        return True
    if message.from_user and message.from_user.id in config.ADMINS:
        return True
    return False

@Client.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.private & filters.create(allowed))
async def incoming_gen_link(bot, message):
    """Generate link for uploaded files"""
    bot_id = (await bot.get_me()).id
    # This check now reads the setting live from the config module
    if not config.LINK_GENERATION_MODE and bot_id == config.OWNER_BOT_ID:
        await message.reply("Link generation is currently disabled on the main management bot. Cloned bots are still active.")
        return

    username = (await bot.get_me()).username
    post = await message.copy(config.LOG_CHANNEL)
    file_id = str(post.id)
    outstr = base64.urlsafe_b64encode(f"file_{file_id}".encode("ascii")).decode().strip("=")
    user_id = message.from_user.id
    user = await get_user(user_id)
    
    if config.WEBSITE_URL_MODE:
        share_link = f"{config.WEBSITE_URL}?start={outstr}"
    else:
        share_link = f"https://t.me/{username}?start={outstr}"
        
    if user.get("base_site") and user.get("shortener_api"):
        short_link = await get_short_link(user, share_link)
        await message.reply(f"<b>⭕ ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\n🖇️ sʜᴏʀᴛ ʟɪɴᴋ :- {short_link}</b>")
    else:
        await message.reply(f"<b>⭕ ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\n🔗 ᴏʀɪɢɪɴᴀʟ ʟɪɴᴋ :- {share_link}</b>")

@Client.on_message(filters.command(['link']) & filters.create(allowed))
async def gen_link_s(bot, message):
    """Generate link for replied message"""
    bot_id = (await bot.get_me()).id
    # This check now reads the setting live from the config module
    if not config.LINK_GENERATION_MODE and bot_id == config.OWNER_BOT_ID:
        await message.reply("Link generation is currently disabled on the main management bot. Cloned bots are still active.")
        return

    username = (await bot.get_me()).username
    replied = message.reply_to_message
    if not replied or not replied.media:
        return await message.reply('Reply to a message containing a file to get a shareable link.')
    
    post = await replied.copy(config.LOG_CHANNEL)
    file_id = str(post.id)
    outstr = base64.urlsafe_b64encode(f"file_{file_id}".encode("ascii")).decode().strip("=")
    user_id = message.from_user.id
    user = await get_user(user_id)
    
    if config.WEBSITE_URL_MODE:
        share_link = f"{config.WEBSITE_URL}?start={outstr}"
    else:
        share_link = f"https://t.me/{username}?start={outstr}"
        
    if user.get("base_site") and user.get("shortener_api"):
        short_link = await get_short_link(user, share_link)
        await message.reply(f"<b>⭕ ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\n🖇️ sʜᴏʀᴛ ʟɪɴᴋ :- {short_link}</b>")
    else:
        await message.reply(f"<b>⭕ ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\n🔗 ᴏʀɪɢɪɴᴀʟ ʟɪɴᴋ :- {share_link}</b>")
