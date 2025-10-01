import random
import asyncio
import base64
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from config import ADMINS, LOG_CHANNEL, PICS, FORCE_SUB_CHANNEL, AUTO_DELETE_MODE, AUTO_DELETE, AUTO_DELETE_TIME, STREAM_MODE, URL
from database.database import db
from plugins.fsub import handle_force_sub
from plugins.file_handler import get_file_details, send_file
from Script import script
import logging

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    # Add user to database
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        if LOG_CHANNEL:
            await client.send_message(
                LOG_CHANNEL, 
                script.LOG_TEXT.format(message.from_user.id, message.from_user.mention)
            )

    # Handle deep links (file access)
    if len(message.command) > 1:
        # Check force subscription first
        if not await handle_force_sub(client, message):
            return

        # Decode and send file
        data = message.command[1]
        try:
            # Decode file ID
            if data.startswith("file_"):
                decode_file_id = data[5:]
            else:
                decoded_data = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("ascii")
                _, decode_file_id = decoded_data.split("_", 1)

            # Send the file
            await send_file(client, message, int(decode_file_id))
            return

        except Exception as e:
            logger.error(f"Error processing deep link: {e}")
            await message.reply("❌ Invalid or expired link. Please request a new one.")
            return

    # Regular start command
    if message.from_user.id in ADMINS:
        # Admin panel
        buttons = [
            [
                InlineKeyboardButton('👤 ᴜsᴇʀs', callback_data='stats'),
                InlineKeyboardButton('📢 ʙʀᴏᴀᴅᴄᴀsᴛ', callback_data='broadcast')
            ],
            [InlineKeyboardButton('🤖 ᴍᴀɴᴀɢᴇ ᴄʟᴏɴᴇs', callback_data='clone')],
            [InlineKeyboardButton('⚙️ sᴇᴛᴛɪɴɢs', callback_data='settings')]
        ]
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.ADMIN_START.format(message.from_user.mention),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        # Regular user panel
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

@Client.on_message(filters.command("help"))
async def help_command(client, message):
    buttons = [
        [InlineKeyboardButton('🏠 ʜᴏᴍᴇ', callback_data='start')]
    ]
    await message.reply_text(
        script.HELP_TXT,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_message(filters.command("about"))
async def about_command(client, message):
    buttons = [
        [InlineKeyboardButton('🏠 ʜᴏᴍᴇ', callback_data='start')]
    ]
    await message.reply_text(
        script.ABOUT_TXT,
        reply_markup=InlineKeyboardMarkup(buttons)
    )
