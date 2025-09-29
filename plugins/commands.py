import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import ADMINS, PICS
from Script import script
from database.database import db
import logging

logger = logging.getLogger(__name__)

# Message handler for /start
@Client.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user_id = message.from_user.id
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id, message.from_user.first_name)

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


# Message handlers for /help and /about (optional, but good for direct commands)
@Client.on_message(filters.command("help") & filters.private)
async def help_command(client, message):
    buttons = [[InlineKeyboardButton('🏠 ʜᴏᴍᴇ', callback_data='start')]]
    await message.reply_text(script.HELP_TXT, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_message(filters.command("about") & filters.private)
async def about_command(client, message):
    buttons = [[InlineKeyboardButton('🏠 ʜᴏᴍᴇ', callback_data='start')]]
    await message.reply_text(script.ABOUT_TXT, reply_markup=InlineKeyboardMarkup(buttons))


# Now add callback query handlers for inline buttons (important!)
@Client.on_callback_query(filters.regex("^start$"))
async def start_callback(client, query: CallbackQuery):
    user_id = query.from_user.id
    await query.answer()  # answer callback query to remove loading spinner

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
