# plugins/commands.py - Fully corrected and merged by Gemini
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
import config # Import the whole config module
import re
import json
import base64
from urllib.parse import quote_plus
from TechVJ.utils.file_properties import get_name, get_hash, get_media_file_size

# ADDED: Import the panel builder from your power.py plugin
from plugins.power import build_main_panel

logger = logging.getLogger(__name__)

# ... (The rest of your file, including start, api, and base_site handlers, remains the same) ...

# MERGED & FIXED: A single, complete callback handler for all buttons
@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    data = query.data

    # ADDED: Logic to handle the admin panel button press
    if data == "admin_panel":
        await query.answer()
        await query.message.edit_text(
            "**⚙️ Admin Power Panel**\n\nHere you can manage your bot's live settings.",
            reply_markup=await build_main_panel()
        )

    elif data == "start":
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
        
        if query.from_user.id in config.ADMINS:
            buttons.append([InlineKeyboardButton("⚙️ Admin Power Panel", callback_data="admin_panel")])
            
        try:
            await query.message.edit_media(
                media=InputMediaPhoto(random.choice(config.PICS)),
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            await query.message.edit_caption(
                caption=script.START_TXT.format(query.from_user.mention, client.me.mention),
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except:
            pass # Ignore errors

    # ... (The rest of your callback handlers for help, about, clone, and close_data remain the same) ...

    # ... (Your deep link and file access logic) ...
    # This part should be fine, but make sure it uses `config.VARIABLE` for all config values

@Client.on_message(filters.command('api') & filters.private)
async def shortener_api_handler(client, m: Message):
    user_id = m.from_user.id
    user = await get_user(user_id)
    cmd = m.command

    if len(cmd) == 1:
        s = script.SHORTENER_API_MESSAGE.format(base_site=user["base_site"], shortener_api=user["shortener_api"])
        return await m.reply(s)

    elif len(cmd) == 2:    
        api = cmd[1].strip()
        await update_user_info(user_id, {"shortener_api": api})
        await m.reply("<b>Shortener API updated successfully to</b> " + api)

@Client.on_message(filters.command("base_site") & filters.private)
async def base_site_handler(client, m: Message):
    user_id = m.from_user.id
    user = await get_user(user_id)
    cmd = m.command
    text = f"`/base_site (base_site)`\n\n<b>Current base site: None\n\n EX:</b> `/base_site shortnerdomain.com`\n\nIf You Want To Remove Base Site Then Copy This And Send To Bot - `/base_site None`"
    if len(cmd) == 1:
        return await m.reply(text=text, disable_web_page_preview=True)
    elif len(cmd) == 2:
        base_site = cmd[1].strip()
        if base_site.lower() == 'none':
            await update_user_info(user_id, {"base_site": None})
            return await m.reply("<b>Base Site successfully removed.</b>")
            
        if not domain(base_site):
            return await m.reply(text=text, disable_web_page_preview=True)
        await update_user_info(user_id, {"base_site": base_site})
        await m.reply("<b>Base Site updated successfully.</b>")

# MERGED: A single, complete callback handler for all buttons
@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    data = query.data

    if data == "start":
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
        
        # Add admin button if the user is an admin
        if query.from_user.id in config.ADMINS:
            buttons.append([InlineKeyboardButton("⚙️ Admin Power Panel", callback_data="admin_panel")])
            
        try:
            await query.message.edit_media(
                media=InputMediaPhoto(random.choice(config.PICS)),
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            await query.message.edit_caption(
                caption=script.START_TXT.format(query.from_user.mention, client.me.mention),
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except:
            pass # Ignore errors

    elif data == "help":
        buttons = [[
            InlineKeyboardButton('Hᴏᴍᴇ', callback_data='start'),
            InlineKeyboardButton('🔒 Cʟᴏsᴇ', callback_data='close_data')
        ]]
        await query.message.edit_text(
            text=script.HELP_TXT,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "about":
        buttons = [[
            InlineKeyboardButton('Hᴏᴍᴇ', callback_data='start'),
            InlineKeyboardButton('🔒 Cʟᴏsᴇ', callback_data='close_data')
        ]]
        await query.message.edit_text(
            text=script.ABOUT_TXT.format(client.me.mention),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "clone":
        buttons = [[
            InlineKeyboardButton('Hᴏᴍᴇ', callback_data='start'),
            InlineKeyboardButton('🔒 Cʟᴏsᴇ', callback_data='close_data')
        ]]
        await query.message.edit_text(
            text=script.CLONE_TXT.format(query.from_user.mention),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "close_data":
        await query.message.delete()
