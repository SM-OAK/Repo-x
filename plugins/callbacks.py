import random
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import PICS, ADMINS
from Script import script
from database.database import db

@Client.on_callback_query(filters.regex("^start$"))
async def start_callback(client, query: CallbackQuery):
    """Handle start button callback"""
    if query.from_user.id in ADMINS:
        buttons = [
            [
                InlineKeyboardButton('👤 ᴜsᴇʀs', callback_data='stats'),
                InlineKeyboardButton('📢 ʙʀᴏᴀᴅᴄᴀsᴛ', callback_data='broadcast')
            ],
            [InlineKeyboardButton('🤖 ᴍᴀɴᴀɢᴇ ᴄʟᴏɴᴇs', callback_data='manage_clones')],
            [InlineKeyboardButton('⚙️ sᴇᴛᴛɪɴɢs', callback_data='settings')]
        ]
        await query.message.edit_text(
            script.ADMIN_START.format(query.from_user.mention),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        buttons = [
            [
                InlineKeyboardButton('💁‍♀️ ʜᴇʟᴘ', callback_data='help'),
                InlineKeyboardButton('😊 ᴀʙᴏᴜᴛ', callback_data='about')
            ],
            [InlineKeyboardButton('🤖 ᴄʀᴇᴀᴛᴇ ʏᴏᴜʀ ᴏᴡɴ ᴄʟᴏɴᴇ ʙᴏᴛ', callback_data='clone')],
            [InlineKeyboardButton('📢 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url='https://t.me/your_channel')]
        ]
        await query.message.edit_text(
            script.START_TXT.format(query.from_user.mention, client.me.mention),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

@Client.on_callback_query(filters.regex("^help$"))
async def help_callback(client, query: CallbackQuery):
    """Handle help button callback"""
    buttons = [[InlineKeyboardButton('🏠 ʜᴏᴍᴇ', callback_data='start')]]
    await query.message.edit_text(script.HELP_TXT, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^about$"))
async def about_callback(client, query: CallbackQuery):
    """Handle about button callback"""
    buttons = [[InlineKeyboardButton('🏠 ʜᴏᴍᴇ', callback_data='start')]]
    await query.message.edit_text(script.ABOUT_TXT, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^stats$"))
async def stats_callback(client, query: CallbackQuery):
    """Handle stats button callback (Admin only)"""
    if query.from_user.id not in ADMINS:
        return await query.answer("Admin only!", show_alert=True)
    
    total_users = await db.total_users_count()
    buttons = [[InlineKeyboardButton('🔙 ʙᴀᴄᴋ', callback_data='start')]]
    await query.message.edit_text(
        f"<b>📊 Bᴏᴛ Sᴛᴀᴛɪsᴛɪᴄs</b>\n\n👥 Tᴏᴛᴀʟ Usᴇʀs: {total_users}\n🤖 Bᴏᴛ: @{client.me.username}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex("^broadcast$"))
async def broadcast_callback(client, query: CallbackQuery):
    """Handle broadcast button callback (Admin only)"""
    if query.from_user.id not in ADMINS:
        return await query.answer("Admin only!", show_alert=True)
    
    await query.message.edit_text(
        "<b>📢 Bʀᴏᴀᴅᴄᴀsᴛ Mᴇssᴀɢᴇ</b>\n\nSᴇɴᴅ ᴛʜᴇ ᴍᴇssᴀɢᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ.\n\nUsᴇ /cancel ᴛᴏ ᴄᴀɴᴄᴇʟ."
    )

@Client.on_callback_query(filters.regex("^settings$"))
async def settings_callback(client, query: CallbackQuery):
    """Handle settings button callback (Admin only)"""
    if query.from_user.id not in ADMINS:
        return await query.answer("Admin only!", show_alert=True)
    
    buttons = [
        [
            InlineKeyboardButton('🔒 ғᴏʀᴄᴇ sᴜʙ', callback_data='toggle_fsub'),
            InlineKeyboardButton('⏱️ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ', callback_data='toggle_autodel')
        ],
        [
            InlineKeyboardButton('📁 ғɪʟᴇ sᴛᴏʀᴇ', callback_data='toggle_filestore'),
            InlineKeyboardButton('🌊 sᴛʀᴇᴀᴍ', callback_data='toggle_stream')
        ],
        [InlineKeyboardButton('🔙 ʙᴀᴄᴋ', callback_data='start')]
    ]
    
    await query.message.edit_text(
        "<b>⚙️ Bᴏᴛ Sᴇᴛᴛɪɴɢs</b>\n\nMᴀɴᴀɢᴇ ʏᴏᴜʀ ʙᴏᴛ ᴄᴏɴғɪɢᴜʀᴀᴛɪᴏɴ:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query()
async def callback_handler(client, query: CallbackQuery):
    """Generic callback handler for answer"""
    data = query.data
    
    if data.startswith("close"):
        await query.message.delete()
    elif data == "pages":
        await query.answer("Use the navigation buttons!", show_alert=False)
