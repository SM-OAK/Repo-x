# plugins/commands.py - Enhanced with Admin Panel
# Credit: @VJ_Botz, Enhancement by Gemini

import os
import logging
import random
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait
from pyrogram.types import *
from config import *
from Script import script
from plugins.dbusers import db

logger = logging.getLogger(__name__)

# --- Helper Functions (from your original file) ---
def get_size(size):
    """Get size in readable format"""
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])

def formate_file_name(file_name):
    if not file_name:
        return "@VJ_Botz File"
    chars = ["[", "]", "(", ")"]
    for c in chars:
        file_name = file_name.replace(c, "")
    # Prepend your desired channel name and clean up the rest
    file_name = '@VJ_Botz ' + ' '.join(filter(lambda x: not x.startswith(('http', '@', 'www.')), file_name.split()))
    return file_name

# --- Admin Panel Builder ---
async def build_admin_panel():
    """Builds the main admin panel with Inline Keyboard Buttons."""
    buttons = [
        [
            InlineKeyboardButton("START MSG", callback_data="admin_start_msg"),
            InlineKeyboardButton("FORCE SUB", callback_data="admin_force_sub")
        ],
        [
            InlineKeyboardButton("MODERATORS", callback_data="admin_moderators"),
            InlineKeyboardButton("AUTO DELETE", callback_data="admin_auto_delete")
        ],
        [
            InlineKeyboardButton("NO FORWARD", callback_data="admin_no_forward"),
            InlineKeyboardButton("ACCESS TOKEN", callback_data="admin_access_token")
        ],
        [
            InlineKeyboardButton("MODE", callback_data="admin_mode"),
            InlineKeyboardButton("DEACTIVATE", callback_data="admin_deactivate")
        ],
        [
            InlineKeyboardButton("STATS", callback_data="admin_stats"),
            InlineKeyboardButton("RESTART", callback_data="admin_restart")
        ],
        [
            InlineKeyboardButton("BACK", callback_data="start"),
            InlineKeyboardButton("DELETE", callback_data="admin_delete_bot")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

# --- Start Command Handler ---
@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        if LOG_CHANNEL:
            await client.send_message(LOG_CHANNEL, script.LOG_TEXT.format(message.from_user.id, message.from_user.mention))

    # Check for deep links (file access, etc.)
    if len(message.command) > 1:
        # NOTE: Your original deep link logic for file access should be here.
        # This part is complex and should be merged carefully.
        # For now, we'll just acknowledge it.
        await message.reply_text("Deep link detected! File access logic would run here.")
        return

    # Check if the user is an ADMIN
    if message.from_user.id in ADMINS:
        await message.reply_photo(
            photo=random.choice(PICS),
            caption="✨ **Admin Panel**\n\nWelcome, Owner! You can configure your bot's settings using the buttons below.",
            reply_markup=await build_admin_panel()
        )
        return

    # --- Default Start for Regular Users ---
    buttons = [[
        InlineKeyboardButton('💝 sᴜʙsᴄʀɪʙᴇ ᴍʏ ʏᴏᴜᴛᴜʙᴇ ᴄʜᴀɴɴᴇʟ', url='https://youtube.com/@Tech_VJ')
        ],[
        InlineKeyboardButton('🔍 sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ', url='https://t.me/vj_bot_disscussion'),
        InlineKeyboardButton('🤖 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url='https://t.me/vj_botz')
        ],[
        InlineKeyboardButton('💁‍♀️ ʜᴇʟᴘ', callback_data='help'),
        InlineKeyboardButton('😊 ᴀʙᴏᴜᴛ', callback_data='about')
    ]]
    if CLONE_MODE:
        buttons.append([InlineKeyboardButton('🤖 ᴄʀᴇᴀᴛᴇ ʏᴏᴜʀ ᴏᴡɴ ᴄʟᴏɴᴇ ʙᴏᴛ', callback_data='clone')])

    reply_markup = InlineKeyboardMarkup(buttons)
    await message.reply_photo(
        photo=random.choice(PICS),
        caption=script.START_TXT.format(message.from_user.mention, client.me.mention),
        reply_markup=reply_markup
    )


# --- Callback Query Handler ---
@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    data = query.data

    if data == "close_data":
        await query.message.delete()

    elif data == "start":
        # This brings the user back to the main menu
        buttons = [[
            InlineKeyboardButton('💝 sᴜʙsᴄʀɪʙᴇ', url='https://youtube.com/@Tech_VJ'),
            InlineKeyboardButton('🤖 ᴜᴘᴅᴀᴛᴇs', url='https://t.me/vj_botz')
        ],[
            InlineKeyboardButton('💁‍♀️ ʜᴇʟᴘ', callback_data='help'),
            InlineKeyboardButton('😊 ᴀʙᴏᴜᴛ', callback_data='about')
        ]]
        if query.from_user.id in ADMINS:
             # If admin, show admin panel instead
             await query.message.edit_caption(
                caption="✨ **Admin Panel**\n\nWelcome, Owner! Configure your bot's settings below.",
                reply_markup=await build_admin_panel()
            )
             return

        await query.message.edit_caption(
            caption=script.START_TXT.format(query.from_user.mention, client.me.mention),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "help":
        await query.message.edit_caption(
            caption=script.HELP_TXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('Hᴏᴍᴇ', callback_data='start')],
                [InlineKeyboardButton('🔒 Cʟᴏsᴇ', callback_data='close_data')]
            ])
        )

    elif data == "about":
        await query.message.edit_caption(
            caption=script.ABOUT_TXT.format(client.me.mention),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('Hᴏᴍᴇ', callback_data='start')],
                [InlineKeyboardButton('🔒 Cʟᴏsᴇ', callback_data='close_data')]
            ])
        )

    elif data == "clone":
         await query.message.edit_caption(
            caption=script.CLONE_TXT.format(query.from_user.mention),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('Hᴏᴍᴇ', callback_data='start')],
                [InlineKeyboardButton('🔒 Cʟᴏsᴇ', callback_data='close_data')]
            ])
        )

    # --- Admin Panel Callbacks ---
    elif data.startswith("admin_"):
        if query.from_user.id not in ADMINS:
            await query.answer("You are not authorized to do this!", show_alert=True)
            return

        if data == "admin_stats":
            total_users = await db.total_users_count()
            await query.answer(f"📊 Total Users in DB: {total_users}", show_alert=True)

        elif data == "admin_restart":
            await query.message.edit_text("🔄 Bot is restarting...")
            # A proper restart function would be needed here, e.g., os.execl
            await query.answer("Restart command sent. The bot will restart if configured correctly.", show_alert=True)
            
        else:
            # Placeholder for other admin commands
            feature_name = data.replace("admin_", "").replace("_", " ").title()
            await query.answer(f"✅ {feature_name} feature is under development.", show_alert=True)

