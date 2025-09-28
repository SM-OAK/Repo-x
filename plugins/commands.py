# plugins/commands.py - Corrected and integrated

import random
from Script import script
from pyrogram import Client, filters
from pyrogram.types import *
import config

def get_start_buttons(message):
    buttons = [
        [InlineKeyboardButton('💝 sᴜʙsᴄʀɪʙᴇ ᴍʏ ʏᴏᴜᴛᴜʙᴇ ᴄʜᴀɴɴᴇʟ', url='https://youtube.com/@Tech_VJ')],
        [InlineKeyboardButton('🔍 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ', url='https://t.me/vj_bot_disscussion'), InlineKeyboardButton('🤖 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url='https://t.me/vj_botz')],
        [InlineKeyboardButton('💁‍♀️ ʜᴇʟᴘ', callback_data='help'), InlineKeyboardButton('😊 ᴀʙᴏᴜᴛ', callback_data='about')]
    ]
    if config.CLONE_MODE:
        buttons.append([InlineKeyboardButton('🤖 ᴄʀᴇᴀᴛᴇ ʏᴏᴜʀ ᴏᴡɴ ᴄʟᴏɴᴇ ʙᴏᴛ', callback_data='clone')])
    if message.from_user.id in config.ADMINS:
        buttons.append([InlineKeyboardButton("⚙️ Admin Power Panel", callback_data="admin_panel")])
    return InlineKeyboardMarkup(buttons)

@Client.on_message(filters.command("start") & filters.private)
async def start(client, message):
    if len(message.command) > 1: return
    await message.reply_photo(
        photo=random.choice(config.PICS),
        caption=script.START_TXT.format(message.from_user.mention, client.me.mention),
        reply_markup=get_start_buttons(message)
    )

@Client.on_callback_query(~filters.regex(r"^(toggle_|admin_panel|manage_clones_menu|clone_settings_|set_)"))
async def public_cb_handler(client: Client, query: CallbackQuery):
    data = query.data
    if data == "start":
        await query.message.edit_caption(
            caption=script.START_TXT.format(query.from_user.mention, client.me.mention),
            reply_markup=get_start_buttons(query)
        )
    elif data == "help":
        await query.message.edit_text(script.HELP_TXT, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('Hᴏᴍᴇ', callback_data='start'), InlineKeyboardButton('🔒 Cʟᴏsᴇ', callback_data='close_data')]
        ]))
    elif data == "about":
        await query.message.edit_text(script.ABOUT_TXT.format(client.me.mention), reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('Hᴏᴍᴇ', callback_data='start'), InlineKeyboardButton('🔒 Cʟᴏsᴇ', callback_data='close_data')]
        ]))
    elif data == "clone":
        await query.message.edit_text(script.CLONE_TXT.format(query.from_user.mention), reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('Hᴏᴍᴇ', callback_data='start'), InlineKeyboardButton('🔒 Cʟᴏsᴇ', callback_data='close_data')]
        ]))
    elif data == "close_data":
        await query.message.delete()
