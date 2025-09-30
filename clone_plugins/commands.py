# In clone_plugins/commands.py

import base64
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.clone_db import clone_db # Make sure this import works

# Simplified texts for clone
START_TEXT = "Hᴇʟʟᴏ {}. I am your personal file store bot."
HELP_TEXT = "Send me any file and I will give you a shareable link."
ABOUT_TEXT = "I am a clone bot created using @VJ_Botz File Store."

@Client.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.private, group=1)
async def clone_file_upload(client, message: Message):
    """Handle file uploads in clone bot"""
    bot_id = client.me.id
    clone = await clone_db.get_clone(bot_id)
    
    # Check if a log channel is configured for this clone
    log_channel = clone.get('settings', {}).get('log_channel')
    if not log_channel:
        return await message.reply("<b>❌ Fɪʟᴇ sᴛᴏʀᴀɢᴇ ɴᴏᴛ ᴄᴏɴғɪɢᴜʀᴇᴅ!</b>\n\nPlease set a Log Channel in the main bot's customize menu.")
    
    try:
        # Copy to the clone's specific log channel
        post = await message.copy(log_channel)
        
        # Generate link
        string = f'file_{post.id}'
        encoded = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
        share_link = f"https://t.me/{client.me.username}?start={encoded}"
        
        await message.reply(f"<b>⭕ Hᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\n🔗 {share_link}</b>")
        
    except Exception as e:
        print(f"Clone Upload Error for bot {bot_id}: {e}")
        await message.reply("<b>❌ Fᴀɪʟᴇᴅ ᴛᴏ sᴀᴠᴇ ғɪʟᴇ!</b>\n\nMake sure I am an admin in your Log Channel.")

@Client.on_message(filters.command("start") & filters.private, group=1)
async def clone_start(client, message: Message):
    """Clone bot start handler"""
    if len(message.command) > 1:
        # Handle file access
        bot_id = client.me.id
        clone = await clone_db.get_clone(bot_id)
        log_channel = clone.get('settings', {}).get('log_channel')
        
        if not log_channel:
            return await message.reply("<b>❌ Fɪʟᴇ sᴛᴏʀᴀɢᴇ ɴᴏᴛ ᴄᴏɴғɪɢᴜʀᴇᴅ!</b>")

        try:
            data = message.command[1]
            # Simple decoding
            decoded_data = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("ascii")
            _, file_id = decoded_data.split("_", 1)

            file_msg = await client.get_messages(log_channel, int(file_id))
            await file_msg.copy(message.from_user.id)
        except Exception as e:
            await message.reply("❌ Invalid or expired link.")
        return

    # Regular start message
    await message.reply(
        START_TEXT.format(message.from_user.mention),
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('💁‍♀️ ʜᴇʟᴘ', callback_data='clone_help'),
            InlineKeyboardButton('😊 ᴀʙᴏᴜᴛ', callback_data='clone_about')
        ]])
    )

@Client.on_callback_query(filters.regex("^clone_"))
async def clone_callbacks(client, query: CallbackQuery):
    """Handle clone bot callbacks"""
    data = query.data
    if data == "clone_help":
        await query.message.edit_text(HELP_TEXT, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🏠 ʜᴏᴍᴇ', callback_data='clone_start')]]))
    elif data == "clone_about":
        await query.message.edit_text(ABOUT_TEXT, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🏠 ʜᴏᴍᴇ', callback_data='clone_start')]]))
    elif data == "clone_start":
        await query.message.edit_text(START_TEXT.format(query.from_user.mention), reply_markup=query.message.reply_markup)
    await query.answer()

print("✅ Clone commands loaded!")
