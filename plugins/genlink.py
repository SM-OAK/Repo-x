# plugins/commands.py - Modified by Gemini
# Added live toggle for link generation mode for admins.
# Don't Remove Credit Tg - @VJ_Botz

import os
import logging
import random
import asyncio
from validators import domain
from Script import script
from plugins.dbusers import db
from pyrogram import Client, filters, enums
from plugins.users_api import get_user, update_user_info
from pyrogram.errors import ChatAdminRequired, FloodWait
from pyrogram.types import *
from utils import verify_user, check_token, check_verification, get_token
# MODIFIED: Import the entire config module to allow live changes
import config 
import re
import json
import base64
from urllib.parse import quote_plus
from TechVJ.utils.file_properties import get_name, get_hash, get_media_file_size
logger = logging.getLogger(__name__)

BATCH_FILES = {}

# ... (keep get_size and formate_file_name functions as they are)

@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await client.send_message(config.LOG_CHANNEL, script.LOG_TEXT.format(message.from_user.id, message.from_user.mention))
    
    # Handle deep links first
    if len(message.command) > 1:
        data = message.command[1]
        
        # ... (Your existing deep link logic for verify, BATCH, and files)

        # MODIFIED: File access part to use `config.`
        try:
            bot_id = (await client.get_me()).id
            if not config.LINK_GENERATION_MODE and bot_id == config.OWNER_BOT_ID:
                await message.reply("File access is currently disabled on the main management bot.")
                return

            # ... (Rest of your file access logic, making sure to use config.LOG_CHANNEL etc.)

        except Exception as e:
            await message.reply(f"Error accessing file: {e}")
        return

    # Default /start menu
    buttons = [[
        InlineKeyboardButton('💝 sᴜʙsᴄʀɪʙᴇ ᴍʏ ʏᴏᴜᴛᴜʙᴇ ᴄʜᴀɴɴᴇʟ', url='https://youtube.com/@Tech_VJ')
        ],[
        InlineKeyboardButton('🔍 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ', url='https://t.me/vj_bot_disscussion'),
        InlineKeyboardButton('🤖 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url='https://t.me/vj_botz')
        ],[
        InlineKeyboardButton('💁‍♀️ ʜᴇʟᴘ', callback_data='help'),
        InlineKeyboardButton('😊 ᴀʙᴏᴜᴛ', callback_data='about')
    ]]
    if config.CLONE_MODE:
        buttons.append([InlineKeyboardButton('🤖 ᴄʀᴇᴀᴛᴇ ʏᴏᴜʀ ᴏᴡɴ ᴄʟᴏɴᴇ ʙᴏᴛ', callback_data='clone')])
    
    # ADDED: Admin-only button to toggle link mode
    if message.from_user.id in config.ADMINS:
        if config.LINK_GENERATION_MODE:
            status_text = "🟢 Links ON"
        else:
            status_text = "🔴 Links OFF"
        buttons.append([InlineKeyboardButton(f"Toggle Main Bot Links: {status_text}", callback_data="toggle_links")])

    reply_markup = InlineKeyboardMarkup(buttons)
    await message.reply_photo(
        photo=random.choice(config.PICS),
        caption=script.START_TXT.format(message.from_user.mention, client.me.mention),
        reply_markup=reply_markup
    )


# ADDED: New commands for admins to toggle link mode
@Client.on_message(filters.command("enable_links") & filters.user(config.ADMINS))
async def enable_links_handler(client, message):
    if config.LINK_GENERATION_MODE:
        await message.reply("✅ Link generation is already enabled.")
    else:
        config.LINK_GENERATION_MODE = True
        await message.reply("✅ Link generation has been **enabled** for the main bot.")

@Client.on_message(filters.command("disable_links") & filters.user(config.ADMINS))
async def disable_links_handler(client, message):
    if not config.LINK_GENERATION_MODE:
        await message.reply("❌ Link generation is already disabled.")
    else:
        config.LINK_GENERATION_MODE = False
        await message.reply("❌ Link generation has been **disabled** for the main bot.")


@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    # ADDED: Handle the new toggle button
    if query.data == "toggle_links":
        if query.from_user.id not in config.ADMINS:
            return await query.answer("This is an admin-only button!", show_alert=True)
        
        # Flip the setting
        config.LINK_GENERATION_MODE = not config.LINK_GENERATION_MODE
        
        # Rebuild the buttons to show the new status
        buttons = [[
            InlineKeyboardButton('💝 sᴜʙsᴄʀɪʙᴇ ᴍʏ ʏᴏᴜᴛᴜʙᴇ ᴄʜᴀɴɴᴇʟ', url='https://youtube.com/@Tech_VJ')
            ],[
            InlineKeyboardButton('🔍 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ', url='https://t.me/vj_bot_disscussion'),
            InlineKeyboardButton('🤖 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url='https://t.me/vj_botz')
            ],[
            InlineKeyboardButton('💁‍♀️ ʜᴇʟᴘ', callback_data='help'),
            InlineKeyboardButton('😊 ᴀʙᴏᴜᴛ', callback_data='about')
        ]]
        if config.CLONE_MODE:
            buttons.append([InlineKeyboardButton('🤖 ᴄʀᴇᴀᴛᴇ ʏᴏᴜʀ ᴏᴡɴ ᴄʟᴏɴᴇ ʙᴏᴛ', callback_data='clone')])
        
        if config.LINK_GENERATION_MODE:
            status_text = "🟢 Links ON"
        else:
            status_text = "🔴 Links OFF"
        buttons.append([InlineKeyboardButton(f"Toggle Main Bot Links: {status_text}", callback_data="toggle_links")])

        try:
            await query.message.edit_reply_markup(InlineKeyboardMarkup(buttons))
            await query.answer(f"Link Generation is now {'ENABLED' if config.LINK_GENERATION_MODE else 'DISABLED'}")
        except:
            pass # Ignore if message is too old to edit

    elif query.data == "close_data":
        await query.message.delete()
    
    # ... (rest of your cb_handler logic for 'about', 'start', 'clone', 'help')
    # Make sure to use config.PICS and config.CLONE_MODE here as well.
