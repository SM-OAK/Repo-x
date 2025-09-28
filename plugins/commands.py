# plugins/commands.py - Fixed and integrated
# Don't Remove Credit Tg - @VJ_Botz

import os
import logging
import random
import asyncio
from validators import domain
from Script import script
from pyrogram import Client, filters
from pyrogram.errors import ChatAdminRequired, FloodWait
from pyrogram.types import *
import config

logger = logging.getLogger(__name__)

# --- Helper to build the start menu buttons ---
def get_start_buttons(message):
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
    
    if message.from_user.id in config.ADMINS:
        buttons.append([InlineKeyboardButton("⚙️ Admin Power Panel", callback_data="admin_panel")])
    return InlineKeyboardMarkup(buttons)

@Client.on_message(filters.command("start") & filters.private)
async def start(client, message):
    if len(message.command) > 1: return # Ignore deep links for now
    
    await message.reply_photo(
        photo=random.choice(config.PICS),
        caption=script.START_TXT.format(message.from_user.mention, client.me.mention),
        reply_markup=get_start_buttons(message)
    )

# NOTE: The /api and /base_site commands were removed as they depended on a database
# system (get_user, update_user_info) that was not provided. If you need them,
# you must also provide the files that contain those functions.

# --- Public Callback Handler ---
# This handler now ignores admin callbacks, which are handled by power.py
@Client.on_callback_query(~filters.regex(r"^(toggle_|admin_panel|manage_clones_menu|clone_settings_|set_)"))
async def public_cb_handler(client: Client, query: CallbackQuery):
    data = query.data

    if data == "start":
        buttons = get_start_buttons(query)
        try:
            # Edit the message to show the start menu again
            await query.message.edit_caption(
                caption=script.START_TXT.format(query.from_user.mention, client.me.mention),
                reply_markup=buttons
            )
        except:
            # If editing fails (e.g., no photo), send a new message
            await query.message.edit_text(
                script.START_TXT.format(query.from_user.mention, client.me.mention),
                reply_markup=buttons
            )

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

