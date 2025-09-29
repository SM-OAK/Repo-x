import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import ADMINS, PICS
from Script import script
from database.database import db  # Your DB module for user management

# Main /start handler (group=2 so clone bot handlers run before this)
@Client.on_message(filters.command("start") & filters.private, group=2)
async def start(client, message):
    user_id = message.from_user.id
    
    # Add user to DB if not exists
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)
    
    # Admin buttons
    if user_id in ADMINS:
        buttons = [
            [
                InlineKeyboardButton('👤 ᴜsᴇʀs', callback_data='stats'),
                InlineKeyboardButton('📢 ʙʀᴏᴀᴅᴄᴀsᴛ', callback_data='broadcast')
            ],
            [InlineKeyboardButton('🤖 ᴍᴀɴᴀɢᴇ ᴄʟᴏɴᴇs', callback_data='manage_clones')],
            [InlineKeyboardButton('⚙️ sᴇᴛᴛɪɴɢs', callback_data='settings')]
        ]
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.ADMIN_START.format(message.from_user.mention),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    # Regular user buttons
    else:
        buttons = [
            [
                InlineKeyboardButton('💁‍♀️ ʜᴇʟᴘ', callback_data='help'),
                InlineKeyboardButton('😊 ᴀʙᴏᴜᴛ', callback_data='about')
            ],
            [InlineKeyboardButton('🤖 ᴄʀᴇᴀᴛᴇ ʏᴏᴜʀ ᴏᴡɴ ᴄʟᴏɴᴇ ʙᴏᴛ', callback_data='clone')],
            [InlineKeyboardButton('📢 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url='https://t.me/your_channel')]
        ]
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.START_TXT.format(message.from_user.mention, client.me.mention),
            reply_markup=InlineKeyboardMarkup(buttons)
        )


# /help command handler
@Client.on_message(filters.command("help") & filters.private, group=2)
async def help_command(client, message):
    buttons = [[InlineKeyboardButton('🏠 ʜᴏᴍᴇ', callback_data='start')]]
    await message.reply_text(script.HELP_TXT, reply_markup=InlineKeyboardMarkup(buttons))


# /about command handler
@Client.on_message(filters.command("about") & filters.private, group=2)
async def about_command(client, message):
    buttons = [[InlineKeyboardButton('🏠 ʜᴏᴍᴇ', callback_data='start')]]
    await message.reply_text(script.ABOUT_TXT, reply_markup=InlineKeyboardMarkup(buttons))


# Callback query for buttons
@Client.on_callback_query(filters.regex("^start$"))
async def start_callback(client, query: CallbackQuery):
    await query.answer()  # Remove loading spinner
    
    user_id = query.from_user.id
    
    if user_id in ADMINS:
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
    await query.answer()
    buttons = [[InlineKeyboardButton('🏠 ʜᴏᴍᴇ', callback_data='start')]]
    await query.message.edit_text(script.HELP_TXT, reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_callback_query(filters.regex("^about$"))
async def about_callback(client, query: CallbackQuery):
    await query.answer()
    buttons = [[InlineKeyboardButton('🏠 ʜᴏᴍᴇ', callback_data='start')]]
    await query.message.edit_text(script.ABOUT_TXT, reply_markup=InlineKeyboardMarkup(buttons))
