# plugins/genlink.py - Fixed for your existing setup
# Works with your existing commands.py and config

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, UsernameInvalid
import base64
import asyncio
import logging
from datetime import datetime

# Import your existing config
from config import (
    ADMINS, 
    LOG_CHANNEL, 
    CHANNEL_ID,  # Your file storage channel
    PUBLIC_FILE_STORE, 
    WEBSITE_URL_MODE, 
    WEBSITE_URL,
    BOT_USERNAME,
    CUSTOM_FILE_CAPTION
)

# Database import (optional) 
try:
    from plugins.dbusers import db
    DATABASE_AVAILABLE = True
except:
    try:
        from database.database import db
        DATABASE_AVAILABLE = True
    except:
        DATABASE_AVAILABLE = False

def encode_file_id(s: str) -> str:
    """Encode message ID for shareable link (your existing format)"""
    try:
        string_bytes = s.encode("ascii")
        base64_bytes = base64.urlsafe_b64encode(string_bytes)
        return base64_bytes.decode("ascii").strip("=")
    except Exception as e:
        logging.error(f"Encoding error: {e}")
        raise

def decode_file_id(s: str) -> str:
    """Decode message ID from shareable link (your existing format)"""
    try:
        # Add padding if needed
        s = s + "=" * (-len(s) % 4)
        string_bytes = base64.urlsafe_b64decode(s)
        return string_bytes.decode("ascii")
    except Exception as e:
        logging.error(f"Decoding error: {e}")
        raise

async def allowed(_, __, message):
    """Check if user is allowed to use the bot"""
    if PUBLIC_FILE_STORE:
        return True
    if message.from_user and message.from_user.id in ADMINS:
        return True
    return False

# Handle file uploads and generate links
@Client.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.private & filters.create(allowed))
async def incoming_gen_link(client: Client, message: Message):
    """Generate shareable link for uploaded files (your existing logic)"""
    
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or "Unknown"
    
    # Add user to database
    if DATABASE_AVAILABLE:
        try:
            if not await db.is_user_exist(user_id):
                await db.add_user(user_id, message.from_user.first_name)
        except Exception as e:
            logging.error(f"Database error: {e}")
    
    try:
        # Copy file to LOG_CHANNEL (your existing method)
        post = await message.copy(LOG_CHANNEL)
        file_id = str(post.id)
        
        # Generate link using your existing format
        string = 'file_'
        string += file_id
        outstr = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
        
        # Create shareable link
        if WEBSITE_URL_MODE and WEBSITE_URL:
            share_link = f"{WEBSITE_URL}?start={outstr}"
        else:
            share_link = f"https://t.me/{BOT_USERNAME}?start={outstr}"
        
        # Log to console (your existing debug format)
        print(f"✅ File {file_id} added for user {user_id}")
        print(f"🔗 Link: {share_link}")
        
        # Send success message
        await message.reply(f"<b>⭕ ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\n🔗 ᴏʀɪɢɪɴᴀʟ ʟɪɴᴋ :- {share_link}</b>")
        
    except Exception as e:
        await message.reply(f"❌ **Error generating link:** `{str(e)}`")
        logging.error(f"Error processing file for user {user_id}: {str(e)}")

# Handle /link command for replied messages  
@Client.on_message(filters.command(['link']) & filters.create(allowed))
async def gen_link_s(client: Client, message: Message):
    """Generate link for replied message (your existing logic)"""
    
    replied = message.reply_to_message
    if not replied:
        return await message.reply('Reply to a message to get a shareable link.')
    
    try:
        post = await replied.copy(LOG_CHANNEL)
        file_id = str(post.id)
        string = f"file_"
        string += file_id
        outstr = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
        
        if WEBSITE_URL_MODE and WEBSITE_URL:
            share_link = f"{WEBSITE_URL}?start={outstr}"
        else:
            share_link = f"https://t.me/{BOT_USERNAME}?start={outstr}"
        
        await message.reply(f"<b>⭕ ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\n🔗 ᴏʀɪɢɪɴᴀʟ ʟɪɴᴋ :- {share_link}</b>")
        
    except Exception as e:
        await message.reply(f"❌ **Error:** `{str(e)}`")

# CRITICAL: Handle file access within your existing start command
@Client.on_message(filters.command("start") & filters.private)
async def handle_file_access(client: Client, message: Message):
    """Handle file access requests - integrates with your existing start command"""
    
    # Only handle file access, let your main start command handle everything else
    if len(message.command) > 1:
        data = message.command[1]
        
        # Handle file access (your existing logic but fixed)
        if data.startswith("file_") or (not data.startswith("BATCH-") and not data.startswith("verify-") and len(data) > 10):
            try:
                # Decode using your existing method
                if data.startswith("file_"):
                    encoded_id = data.replace("file_", "")
                else:
                    # Handle your existing base64 encoded format
                    try:
                        decoded_data = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("ascii")
                        if "_" in decoded_data:
                            pre, file_id = decoded_data.split("_", 1)
                            encoded_id = base64.urlsafe_b64encode(f"file_{file_id}".encode("ascii")).decode().strip("=")
                        else:
                            return  # Let main commands handle it
                    except:
                        return  # Let main commands handle it
                
                # Decode the file ID
                decoded_string = decode_file_id(encoded_id)
                
                if decoded_string.startswith("file_"):
                    file_id = int(decoded_string[5:])  # Remove "file_" prefix
                else:
                    file_id = int(decoded_string)
                
                print(f"🔍 Debug: Trying to access file ID {file_id} from LOG_CHANNEL {LOG_CHANNEL}")
                
                # Send loading message
                loading_msg = await message.reply_text("🔄 **Fetching your file...**")
                
                try:
                    # Get the message from LOG_CHANNEL (your storage channel)
                    file_msg = await client.get_messages(LOG_CHANNEL, file_id)
                    
                    if file_msg and file_msg.media:
                        # Copy the file to user
                        await file_msg.copy(chat_id=message.from_user.id, protect_content=False)
                        await loading_msg.delete()
                        
                        success_msg = await message.reply_text("✅ **File delivered successfully!**")
                        print(f"✅ File {file_id} delivered to user {message.from_user.id}")
                        
                        # Auto-delete after 30 minutes if enabled in your config
                        try:
                            if hasattr(config, 'AUTO_DELETE_MODE') and config.AUTO_DELETE_MODE:
                                await asyncio.sleep(1800)  # 30 minutes
                                await success_msg.edit_text("🗑️ **File access expired**")
                        except:
                            pass
                        
                    else:
                        await loading_msg.edit_text("❌ **File not found or expired**")
                        
                except Exception as e:
                    await loading_msg.edit_text(
                        f"❌ **Cannot access file**\n\n**Error:** `{str(e)}`\n\n"
                        f"**Debug Info:**\n"
                        f"File ID: `{file_id}`\n"
                        f"Channel: `{LOG_CHANNEL}`"
                    )
                    print(f"❌ Error accessing file {file_id}: {str(e)}")
                
                return  # Stop here, don't let it continue to main start
                
            except Exception as e:
                await message.reply_text(f"❌ **Invalid link format**\n\n**Error:** `{str(e)}`")
                print(f"❌ Link decode error: {str(e)}")
                return
    
    # If we reach here, it's not a file access request - let your main start command handle it
    # This will be handled by your existing plugins/commands.py start command

# Debug command for admins
@Client.on_message(filters.command("debug") & filters.user(ADMINS))
async def debug_command(client: Client, message: Message):
    """Debug command to check bot status"""
    try:
        # Test channel access
        channel_info = await client.get_chat(LOG_CHANNEL)
        
        # Get recent message
        recent_msg = None
        async for msg in client.get_chat_history(LOG_CHANNEL, limit=1):
            recent_msg = msg
            break
        
        debug_text = f"""🔧 **DEBUG INFO**

**LOG_CHANNEL:** `{LOG_CHANNEL}`
**CHANNEL_ID:** `{CHANNEL_ID}` 
**Channel Name:** `{channel_info.title}`
**Bot Access:** ✅ Working
**Recent Message ID:** `{recent_msg.id if recent_msg else 'None'}`
**Database:** `{'✅ Available' if DATABASE_AVAILABLE else '❌ Not Available'}`

**Config Status:**
• `PUBLIC_FILE_STORE`: `{PUBLIC_FILE_STORE}`
• `WEBSITE_URL_MODE`: `{WEBSITE_URL_MODE}`
• `BOT_USERNAME`: `{BOT_USERNAME}`"""
        
        await message.reply_text(debug_text)
        
    except Exception as e:
        await message.reply_text(f"❌ Debug failed: {str(e)}")

print("✅ Genlink module loaded with existing config integration!")
print(f"📊 LOG_CHANNEL: {LOG_CHANNEL}")
print(f"💾 CHANNEL_ID: {CHANNEL_ID}")
print(f"🔧 DATABASE_AVAILABLE: {DATABASE_AVAILABLE}")
