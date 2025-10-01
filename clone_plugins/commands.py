# clone_plugins/commands.py
import base64
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Try to import from config - fallback gracefully
try:
    from config import LOG_CHANNEL, ADMINS, AUTO_DELETE_MODE, AUTO_DELETE_TIME
    CONFIG_LOADED = True
except:
    LOG_CHANNEL = None
    ADMINS = []
    AUTO_DELETE_MODE = False
    AUTO_DELETE_TIME = 1800
    CONFIG_LOADED = False

# Try to import database - fallback gracefully
try:
    from database.clone_db import clone_db
    DB_LOADED = True
except:
    DB_LOADED = False

START_TEXT = """<b>Hᴇʟʟᴏ {} ✨

I ᴀᴍ ᴀ ᴘᴇʀᴍᴀɴᴇɴᴛ ғɪʟᴇ sᴛᴏʀᴇ ʙᴏᴛ ᴀɴᴅ ᴜsᴇʀs ᴄᴀɴ ᴀᴄᴄᴇss sᴛᴏʀᴇᴅ ᴍᴇssᴀɢᴇs ʙʏ ᴜsɪɴɢ ᴀ sʜᴀʀᴇᴀʙʟᴇ ʟɪɴᴋ ɢɪᴠᴇɴ ʙʏ ᴍᴇ.

Tᴏ ᴋɴᴏᴡ ᴍᴏʀᴇ ᴄʟɪᴄᴋ ʜᴇʟᴘ ʙᴜᴛᴛᴏɴ.</b>"""

HELP_TEXT = """<b>📚 Hᴇʟᴘ Mᴇɴᴜ

🔹 Sᴇɴᴅ ᴍᴇ ᴀɴʏ ғɪʟᴇ/ᴠɪᴅᴇᴏ
🔹 I ᴡɪʟʟ ɢɪᴠᴇ ʏᴏᴜ ᴀ sʜᴀʀᴇᴀʙʟᴇ ʟɪɴᴋ
🔹 Usᴇʀs ᴄᴀɴ ᴀᴄᴄᴇss ғɪʟᴇs ғʀᴏᴍ ᴛʜᴇ ʟɪɴᴋ

💡 Jᴜsᴛ sᴇɴᴅ ᴍᴇ ᴀɴʏ ғɪʟᴇ!</b>"""

ABOUT_TEXT = """<b>━━━━━━━━━━━━━━━━━━━
◈ Mʏ Nᴀᴍᴇ: Fɪʟᴇ Sᴛᴏʀᴇ Cʟᴏɴᴇ
◈ Cʀᴇᴀᴛᴏʀ: @VJ_Botz
◈ Lɪʙʀᴀʀʏ: Pʏʀᴏɢʀᴀᴍ
◈ Lᴀɴɢᴜᴀɢᴇ: Pʏᴛʜᴏɴ 3
━━━━━━━━━━━━━━━━━━━</b>"""

def get_start_keyboard():
    """Get keyboard for start message"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('💁‍♀️ ʜᴇʟᴘ', callback_data='clone_help'),
            InlineKeyboardButton('😊 ᴀʙᴏᴜᴛ', callback_data='clone_about')
        ]
    ])

async def decode_file_id(data):
    """Decode file ID from various formats"""
    try:
        # Format 1: file_123
        if data.startswith("file_"):
            return int(data[5:])
        
        # Format 2: Base64 encoded
        decoded = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("ascii")
        
        # Format 2a: file_123 encoded
        if decoded.startswith("file_"):
            return int(decoded[5:])
        
        # Format 2b: prefix_123
        if "_" in decoded:
            _, file_id = decoded.split("_", 1)
            return int(file_id)
        
        # Format 3: Direct number
        return int(decoded)
    
    except Exception as e:
        print(f"Clone: Decode error - {e}")
        return None

async def send_file_to_user(client, message, file_id):
    """Retrieve and send file to user"""
    if not LOG_CHANNEL:
        return False
    
    try:
        # Get file from log channel
        file_msg = await client.get_messages(LOG_CHANNEL, file_id)
        
        if not file_msg or not file_msg.media:
            await message.reply("<b>❌ Fɪʟᴇ ɴᴏᴛ ғᴏᴜɴᴅ!</b>")
            return False
        
        # Send file to user
        sent_msg = await file_msg.copy(
            chat_id=message.from_user.id,
            caption=file_msg.caption
        )
        
        # Auto-delete if enabled
        if AUTO_DELETE_MODE:
            warning = await message.reply(
                f"<b>⚠️ IMPORTANT</b>\n\n"
                f"This file will be deleted in <b>{AUTO_DELETE_TIME // 60} minutes</b>.\n"
                f"Please forward to Saved Messages!"
            )
            
            await asyncio.sleep(AUTO_DELETE_TIME)
            
            try:
                await sent_msg.delete()
                await warning.edit_text("✅ File deleted!")
            except:
                pass
        
        return True
        
    except Exception as e:
        print(f"Clone: Error sending file - {e}")
        await message.reply(f"<b>❌ Eʀʀᴏʀ: {str(e)}</b>")
        return False

# PRIORITY: Clone bot only handles if main bot doesn't
@Client.on_message(filters.command("start") & filters.private, group=1)
async def clone_start(client, message):
    """Clone bot start handler - runs with lower priority"""
    
    # Check if there's a parameter
    if len(message.command) > 1:
        parameter = message.command[1]
        
        # Try to decode as file access
        file_id = await decode_file_id(parameter)
        
        if file_id:
            print(f"Clone: Handling file access for ID {file_id}")
            
            # Show loading
            loading = await message.reply("<b>🔄 Fᴇᴛᴄʜɪɴɢ ғɪʟᴇ...</b>")
            
            # Send file
            success = await send_file_to_user(client, message, file_id)
            
            # Delete loading message
            try:
                await loading.delete()
            except:
                pass
            
            if success:
                return  # Successfully handled
            else:
                # Fall through to show start message
                pass
        else:
            # Invalid parameter - show start message
            print(f"Clone: Invalid parameter - {parameter}")
    
    # Regular start message
    await message.reply(
        START_TEXT.format(message.from_user.mention),
        reply_markup=get_start_keyboard()
    )

@Client.on_callback_query(filters.regex("^clone_"))
async def clone_callbacks(client, query: CallbackQuery):
    """Handle clone bot callbacks"""
    data = query.data
    
    if data == "clone_help":
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton('🏠 ʜᴏᴍᴇ', callback_data='clone_start')
        ]])
        await query.message.edit_text(HELP_TEXT, reply_markup=keyboard)
    
    elif data == "clone_about":
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton('🏠 ʜᴏᴍᴇ', callback_data='clone_start')
        ]])
        await query.message.edit_text(ABOUT_TEXT, reply_markup=keyboard)
    
    elif data == "clone_start":
        await query.message.edit_text(
            START_TEXT.format(query.from_user.mention),
            reply_markup=get_start_keyboard()
        )
    
    await query.answer()

@Client.on_message(filters.command(["help", "about"]) & filters.private)
async def clone_help_about(client, message):
    """Handle help and about commands"""
    command = message.command[0].lower()
    
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton('🏠 ʜᴏᴍᴇ', callback_data='clone_start')
    ]])
    
    if command == "help":
        await message.reply(HELP_TEXT, reply_markup=keyboard)
    else:
        await message.reply(ABOUT_TEXT, reply_markup=keyboard)

# File upload handler for clone bots
@Client.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.private, group=1)
async def clone_file_upload(client, message):
    """Handle file uploads in clone bot"""
    
    if not LOG_CHANNEL:
        return await message.reply(
            "<b>❌ Fɪʟᴇ sᴛᴏʀᴀɢᴇ ɴᴏᴛ ᴄᴏɴғɪɢᴜʀᴇᴅ!</b>"
        )
    
    try:
        # Copy to log channel
        post = await message.copy(LOG_CHANNEL)
        file_id = str(post.id)
        
        # Generate link
        bot_username = (await client.get_me()).username
        string = f'file_{file_id}'
        encoded = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
        share_link = f"https://t.me/{bot_username}?start={encoded}"
        
        # Send link
        await message.reply(
            f"<b>⭕ Hᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\n"
            f"🔗 Lɪɴᴋ: {share_link}</b>"
        )
        
    except Exception as e:
        print(f"Clone: Upload error - {e}")
        await message.reply("<b>❌ Fᴀɪʟᴇᴅ ᴛᴏ ɢᴇɴᴇʀᴀᴛᴇ ʟɪɴᴋ!</b>")

print("✅ Clone commands loaded - non-conflicting mode with group=1 priority!")
