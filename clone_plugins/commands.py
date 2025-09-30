# commands.py

import base64
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Try to import from config - fallback gracefully
try:
    from config import LOG_CHANNEL, ADMINS
    CONFIG_LOADED = True
except:
    LOG_CHANNEL = None
    ADMINS = []
    CONFIG_LOADED = False

# Try to import database - fallback gracefully
try:
    from database.clone_db import clone_db
    DB_LOADED = True
except:
    DB_LOADED = False

# ... (Keep START_TEXT, HELP_TEXT, ABOUT_TEXT, get_start_keyboard, decode_file_id functions as they are) ...

async def send_file_to_user(client, message, file_id):
    """Retrieve and send file to user, with clone-specific auto-delete"""
    if not LOG_CHANNEL:
        return False
    
    try:
        file_msg = await client.get_messages(LOG_CHANNEL, file_id)
        
        if not file_msg or not file_msg.media:
            await message.reply("<b>❌ Fɪʟᴇ ɴᴏᴛ ғᴏᴜɴᴅ!</b>")
            return False
        
        sent_msg = await file_msg.copy(
            chat_id=message.from_user.id,
            caption=file_msg.caption
        )
        
        # --- CLONE-SPECIFIC AUTO DELETE LOGIC ---
        if DB_LOADED:
            bot_id = client.me.id
            clone = await clone_db.get_clone(bot_id)
            
            if clone and clone.get('settings', {}).get('auto_delete', False):
                settings = clone['settings']
                delete_time_seconds = settings.get('auto_delete_time', 300)
                delete_time_str = f"{delete_time_seconds // 60} minutes"
                
                message_template = settings.get('auto_delete_message')
                if not message_template:
                    warning_text = (f"<b>⚠️ IMPORTANT</b>\n\nThis file will be deleted in <b>{delete_time_str}</b>.")
                else:
                    warning_text = message_template.format(time=delete_time_str)

                warning = await message.reply(warning_text)
                
                # Use a background task to delete messages without blocking
                async def delete_task():
                    await asyncio.sleep(delete_time_seconds)
                    try:
                        await sent_msg.delete()
                        await warning.edit_text("✅ File deleted!")
                    except Exception as e:
                        logger.error(f"Clone Auto-Delete Error: {e}")

                asyncio.create_task(delete_task())
        
        return True
        
    except Exception as e:
        logger.error(f"Clone: Error sending file - {e}", exc_info=True)
        await message.reply(f"<b>❌ Eʀʀᴏʀ: {str(e)}</b>")
        return False

# ... (Keep the rest of the file, including clone_start, clone_callbacks, etc., as it is) ...
