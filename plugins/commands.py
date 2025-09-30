import random
import asyncio
import base64
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from config import ADMINS, LOG_CHANNEL, PICS, FORCE_SUB_CHANNEL
from database.database import db
from plugins.fsub import handle_force_sub
from plugins.file_handler import send_file
from Script import script
import logging

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("start") & filters.private, group=0)
async def start(client, message):
    """Main bot start command - highest priority (group=0)"""
    try:
        # Add user to database
        if not await db.is_user_exist(message.from_user.id):
            await db.add_user(message.from_user.id, message.from_user.first_name)
            if LOG_CHANNEL:
                try:
                    await client.send_message(
                        LOG_CHANNEL, 
                        script.LOG_TEXT.format(message.from_user.id, message.from_user.mention)
                    )
                except Exception as e:
                    logger.error(f"Error sending log: {e}")

        # Handle deep links (file access)
        if len(message.command) > 1:
            if not await handle_force_sub(client, message):
                return
            data = message.command[1]
            try:
                if data.startswith("file_"):
                    decode_file_id = data.replace("file_", "")
                else:
                    decoded_data = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("ascii")
                    if "_" in decoded_data:
                        _, decode_file_id = decoded_data.split("_", 1)
                    else:
                        decode_file_id = decoded_data
                await send_file(client, message, int(decode_file_id))
                return
            except Exception as e:
                logger.error(f"Error processing deep link: {e}")
                await message.reply("❌ Invalid or expired link.")
                return

        # Show admin or user menu
        if message.from_user.id in ADMINS:
            buttons = [
                [InlineKeyboardButton('👤 Users', callback_data='stats'),
                 InlineKeyboardButton('📢 Broadcast', callback_data='broadcast')],
                [InlineKeyboardButton('🤖 Manage Clones', callback_data='manage_clones')],
                [InlineKeyboardButton('⚙️ Settings', callback_data='settings')]
            ]
            await message.reply_photo(
                photo=random.choice(PICS),
                caption=script.ADMIN_START.format(message.from_user.mention),
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        else:
            buttons = [
                [InlineKeyboardButton('💁 Help', callback_data='help'),
                 InlineKeyboardButton('😊 About', callback_data='about')],
                [InlineKeyboardButton('🤖 Create Clone Bot', callback_data='clone')],
                [InlineKeyboardButton('📢 Updates', url='https://t.me/your_channel')]
            ]
            await message.reply_photo(
                photo=random.choice(PICS),
                caption=script.START_TXT.format(message.from_user.mention, client.me.mention),
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await message.reply("❌ An error occurred.")


@Client.on_message(filters.command(["help", "about"]) & filters.private, group=0)
async def help_about(client, message):
    """Handle help and about commands for main bot"""
    command = message.command[0].lower()
    buttons = [[InlineKeyboardButton('🏠 Home', callback_data='start')]]
    
    if command == "help":
        await message.reply(script.HELP_TXT, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await message.reply(script.ABOUT_TXT, reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.private & filters.user(ADMINS), group=0)
async def handle_file_upload(client, message):
    """Handle file uploads for main bot (admin only)"""
    if not LOG_CHANNEL:
        return await message.reply("<b>❌ File storage not configured!</b>")
    
    try:
        post = await message.copy(LOG_CHANNEL)
        file_id = str(post.id)
        bot_username = (await client.get_me()).username
        string = f'file_{file_id}'
        encoded = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
        share_link = f"https://t.me/{bot_username}?start={encoded}"
        
        await message.reply(
            f"<b>⭕ Here is your link:\n\n🔗 Link: {share_link}</b>",
            quote=True
        )
    except Exception as e:
        logger.error(f"Upload error: {e}")
        await message.reply("<b>❌ Failed to generate link!</b>")


logger.info("✅ Main bot commands loaded (group=0)")
