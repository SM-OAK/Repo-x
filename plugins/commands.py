# plugins/commands.py
import random
import asyncio
import base64
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMINS, LOG_CHANNEL, PICS
from database.database import db
from plugins.fsub import handle_force_sub
from plugins.file_handler import send_file
from Script import script
import logging

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("start") & filters.private)
async def start(client, message):
    try:
        user_id = message.from_user.id

        # 1️⃣ Add user to DB if not exists
        if not await db.is_user_exist(user_id):
            await db.add_user(user_id, message.from_user.first_name)
            if LOG_CHANNEL:
                try:
                    await client.send_message(
                        LOG_CHANNEL,
                        script.LOG_TEXT.format(user_id, message.from_user.mention)
                    )
                except Exception as e:
                    logger.warning(f"Failed to send log: {e}")

        # 2️⃣ Handle deep link (file access)
        if len(message.command) > 1:
            if not await handle_force_sub(client, message):
                return

            data = message.command[1]
            try:
                if data.startswith("file_"):
                    decode_file_id = int(data[5:])
                else:
                    decoded_data = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("ascii")
                    _, decode_file_id = decoded_data.split("_", 1)
                    decode_file_id = int(decode_file_id)

                await send_file(client, message, decode_file_id)
                return

            except Exception as e:
                logger.error(f"Error processing deep link: {e}")
                await message.reply("❌ Invalid or expired link. Please request a new one.")
                return

        # 3️⃣ Admin panel
        if user_id in ADMINS:
            buttons = [
                [
                    InlineKeyboardButton('👤 Users', callback_data='stats'),
                    InlineKeyboardButton('📢 Broadcast', callback_data='broadcast')
                ],
                [InlineKeyboardButton('🤖 Manage Clones', callback_data='clone')],
                [InlineKeyboardButton('⚙️ Settings', callback_data='settings')]
            ]
            await message.reply_photo(
                photo=random.choice(PICS) if PICS else None,
                caption=script.ADMIN_START.format(message.from_user.mention),
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return

        # 4️⃣ Regular user panel
        buttons = [
            [
                InlineKeyboardButton('💁‍♀️ Help', callback_data='help'),
                InlineKeyboardButton('😊 About', callback_data='about')
            ],
            [InlineKeyboardButton('🤖 Create Your Own Clone Bot', callback_data='clone')],
            [InlineKeyboardButton('📢 Update Channel', url='https://t.me/your_channel')]
        ]
        await message.reply_photo(
            photo=random.choice(PICS) if PICS else None,
            caption=script.START_TXT.format(message.from_user.mention, client.me.mention),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    except Exception as e:
        logger.error(f"Start command error: {e}")
        await message.reply("❌ Something went wrong while processing your request.")    
