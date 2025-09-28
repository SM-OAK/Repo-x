# genlink.py - Fixed for existing config
# Works with your existing config.py setup

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
    CHANNEL_ID as FILE_STORAGE_CHANNEL,  # Using your CHANNEL_ID as storage
    PUBLIC_FILE_STORE, 
    WEBSITE_URL_MODE, 
    WEBSITE_URL,
    BOT_USERNAME,
    CUSTOM_FILE_CAPTION
)

# Database import (optional)
try:
    from database.database import db
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    logging.warning("Database not available, running without DB support")

def encode_file_id(s: str) -> str:
    """Encode message ID for shareable link"""
    try:
        string_bytes = s.encode("ascii")
        base64_bytes = base64.urlsafe_b64encode(string_bytes)
        return base64_bytes.decode("ascii").strip("=")
    except Exception as e:
        logging.error(f"Encoding error: {e}")
        raise

def decode_file_id(s: str) -> str:
    """Decode message ID from shareable link"""
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

async def log_activity(client: Client, user_id: int, username: str, action: str, file_info: dict):
    """Log bot activities to LOG_CHANNEL"""
    try:
        log_text = f"""
📊 **FILE STORE ACTIVITY**

👤 **User:** [{username}](tg://user?id={user_id})
🆔 **ID:** `{user_id}`
⚡ **Action:** {action}
📁 **File:** `{file_info.get('name', 'Unknown')}`
📏 **Size:** `{file_info.get('size', 'Unknown')}`
🕐 **Time:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`
"""
        await client.send_message(LOG_CHANNEL, log_text)
    except Exception as e:
        logging.error(f"Failed to log activity: {e}")

@Client.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.private & filters.create(allowed))
async def handle_file_share(client: Client, message: Message):
    """Handle incoming files and generate shareable links"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or "Unknown"
    
    # Add user to database if available
    if DATABASE_AVAILABLE:
        try:
            await db.add_user(user_id)
        except Exception as e:
            logging.error(f"Database error: {e}")
    
    # Processing message
    processing_msg = await message.reply_text(
        "🔄 **Processing your file...**\n\n⏳ Please wait while I generate a shareable link for you!"
    )
    
    try:
        # Get file details first
        file_info = {"name": "Unknown", "size": "Unknown", "type": "Unknown"}
        
        if message.document:
            file_info["name"] = message.document.file_name or "Document"
            file_info["size"] = f"{message.document.file_size / (1024*1024):.2f} MB" if message.document.file_size else "Unknown"
            file_info["type"] = "Document"
        elif message.video:
            file_info["name"] = message.video.file_name or "Video"
            file_info["size"] = f"{message.video.file_size / (1024*1024):.2f} MB" if message.video.file_size else "Unknown"
            file_info["type"] = "Video"
        elif message.audio:
            file_info["name"] = message.audio.file_name or message.audio.title or "Audio"
            file_info["size"] = f"{message.audio.file_size / (1024*1024):.2f} MB" if message.audio.file_size else "Unknown"
            file_info["type"] = "Audio"
        elif message.photo:
            file_info["name"] = "Photo"
            file_info["size"] = f"{message.photo.file_size / (1024*1024):.2f} MB" if message.photo.file_size else "Unknown"
            file_info["type"] = "Photo"
        
        # Copy file to CHANNEL_ID (your file storage channel)
        try:
            # Copy with custom caption if available
            if CUSTOM_FILE_CAPTION:
                post = await message.copy(FILE_STORAGE_CHANNEL, caption=CUSTOM_FILE_CAPTION)
            else:
                post = await message.copy(FILE_STORAGE_CHANNEL)
            
            file_id = str(post.id)
            logging.info(f"File stored in channel with ID: {file_id}")
        except Exception as e:
            logging.error(f"Failed to copy to storage channel: {e}")
            await processing_msg.edit_text(
                "❌ **Storage Error**\n\n"
                "Unable to store file. Please contact admin.\n\n"
                "**Possible issues:**\n"
                "• Bot not added to storage channel\n"
                "• Missing permissions\n"
                "• Incorrect channel ID"
            )
            return
        
        # Generate shareable link (using your existing format)
        string = 'file_' + file_id
        encoded_file_id = encode_file_id(string)
        
        # Create shareable link based on your config
        if WEBSITE_URL_MODE and WEBSITE_URL:
            share_link = f"{WEBSITE_URL}?start={encoded_file_id}"
        else:
            share_link = f"https://t.me/{BOT_USERNAME}?start={encoded_file_id}"
        
        # Store file info in database if available
        if DATABASE_AVAILABLE:
            try:
                await db.add_file(file_id, user_id, FILE_STORAGE_CHANNEL)
            except Exception as e:
                logging.error(f"Database error: {e}")
        
        # Log activity to LOG_CHANNEL
        await log_activity(client, user_id, username, "File Upload", file_info)
        
        # Success message
        success_text = f"""✅ **FILE LINK GENERATED!**

📁 **File:** `{file_info['name']}`
📊 **Type:** `{file_info['type']}`
📏 **Size:** `{file_info['size']}`
🔗 **Link:** 

`{share_link}`

**How to use:**
• Copy link above
• Share with anyone
• Download anytime
• Never expires!"""
        
        # Buttons
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📋 Copy Link", url=share_link),
                InlineKeyboardButton("📤 Share", switch_inline_query=share_link)
            ],
            [
                InlineKeyboardButton("🔗 Generate More", callback_data="generate_more")
            ]
        ])
        
        await processing_msg.edit_text(
            success_text,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
        
        logging.info(f"✅ File processed successfully for user {user_id}: {file_info['name']}")
        
    except Exception as e:
        error_text = f"""❌ **Processing Failed**

Something went wrong while processing your file.

**Error:** `{str(e)}`

Please try again or contact support."""
        
        await processing_msg.edit_text(
            error_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Try Again", callback_data="try_again")]
            ])
        )
        
        logging.error(f"❌ Error processing file for user {user_id}: {str(e)}")

@Client.on_message(filters.command("start") & filters.private)
async def handle_file_access(client: Client, message: Message):
    """Handle file access requests via start command"""
    
    # Check if it's a file access request
    if len(message.command) > 1 and message.command[1].startswith("file_"):
        try:
            # Extract encoded file ID (keeping your existing format)
            encoded_file_id = message.command[1].replace("file_", "")
            decoded_string = decode_file_id(encoded_file_id)
            
            # Extract file ID (remove 'file_' prefix)
            if decoded_string.startswith("file_"):
                file_id = int(decoded_string[5:])  # Remove 'file_' prefix
            else:
                file_id = int(decoded_string)
            
            # Send loading message
            loading_msg = await message.reply_text(
                "🔄 **Fetching File...**\n\n⏳ Please wait while I get your file!"
            )
            
            try:
                # Forward the message from CHANNEL_ID (your storage channel)
                await client.forward_messages(
                    chat_id=message.from_user.id,
                    from_chat_id=FILE_STORAGE_CHANNEL,
                    message_ids=file_id
                )
                
                await loading_msg.delete()
                
                # Log file access
                username = message.from_user.username or message.from_user.first_name or "Unknown"
                await log_activity(client, message.from_user.id, username, "File Downloaded", {"name": f"File ID: {file_id}", "size": "N/A"})
                
                await message.reply_text(
                    "✅ **File delivered!**\n\n📥 Your file is ready above.\n\n🔗 Want to create shareable links?\nJust send me any file!"
                )
                
                logging.info(f"✅ File delivered successfully to user {message.from_user.id}")
                
            except Exception as e:
                await loading_msg.edit_text(
                    f"❌ **File Not Found**\n\n"
                    f"This file might be deleted or the link is invalid.\n\n"
                    f"**Error:** `{str(e)}`"
                )
                logging.error(f"❌ Error accessing file {file_id}: {str(e)}")
                
        except Exception as e:
            await message.reply_text(
                f"❌ **Invalid Link**\n\n"
                f"The link format is incorrect or corrupted.\n\n"
                f"**Error:** `{str(e)}`"
            )
            logging.error(f"❌ Invalid file link: {str(e)}")

@Client.on_message(filters.command(["link"]) & filters.private & filters.create(allowed))
async def gen_link_command(client: Client, message: Message):
    """Generate link for replied message"""
    replied = message.reply_to_message
    if not replied:
        return await message.reply('❌ Reply to a message to get a shareable link.')
    
    if not (replied.document or replied.video or replied.audio or replied.photo):
        return await message.reply('❌ Please reply to a media file.')
    
    # Process the replied message
    await handle_file_share(client, replied)

@Client.on_callback_query(filters.regex("generate_more"))
async def generate_more_callback(client: Client, callback_query):
    await callback_query.edit_message_text(
        "📤 **Send More Files!**\n\n"
        "Send me any file and I'll generate a shareable link.\n\n"
        "**Supported:**\n"
        "• Documents (PDF, DOC, etc.)\n"
        "• Videos (MP4, AVI, etc.)\n"
        "• Audio (MP3, WAV, etc.)\n"
        "• Photos (JPG, PNG, etc.)"
    )

@Client.on_callback_query(filters.regex("try_again"))
async def try_again_callback(client: Client, callback_query):
    await callback_query.edit_message_text(
        "🔄 **Try Again**\n\n"
        "Please send your file again.\n\n"
        "**Tips:**\n"
        "• Check file isn't corrupted\n"
        "• Verify internet connection\n"
        "• Contact admin if issues persist"
    )

print("✅ Genlink module loaded with existing config!")
print(f"📊 LOG_CHANNEL: {LOG_CHANNEL}")
print(f"💾 FILE_STORAGE_CHANNEL: {FILE_STORAGE_CHANNEL}")
print(f"🔧 DATABASE_AVAILABLE: {DATABASE_AVAILABLE}")
print(f"🌐 WEBSITE_URL_MODE: {WEBSITE_URL_MODE}")
