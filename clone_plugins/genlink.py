# clone_plugins/genlink.py - Corrected Link Generation Handler

import asyncio
import base64
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import StopPropagation

# Import specific variables from the config file
from config import CHANNEL_ID, ADMINS

# Database import (optional - will work without database)
try:
    from database.database import db
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("⚠️ Database module not found. Bot will work without database features.")

# Function to encode message ID for shareable link
def encode_file_id(s: str) -> str:
    string_bytes = s.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    return base64_bytes.decode("ascii").strip("=")

# Function to decode message ID from shareable link
def decode_file_id(s: str) -> str:
    s = s + "=" * (-len(s) % 4)
    string_bytes = base64.urlsafe_b64decode(s)
    return string_bytes.decode("ascii")

# Handle file sharing and link generation
@Client.on_message(filters.private & (filters.document | filters.video | filters.audio | filters.photo))
async def handle_file_share(client: Client, message: Message):
    user_id = message.from_user.id
    
    if DATABASE_AVAILABLE:
        try:
            await db.add_user(user_id)
        except Exception as e:
            print(f"Database error: {e}")

    processing_msg = await message.reply_text(
        "🔄 **Processing your file...**\n\n⏳ Please wait while I generate a shareable link for you!"
    )
    
    try:
        if CHANNEL_ID:
            forwarded_msg = await message.forward(CHANNEL_ID)
            file_id = forwarded_msg.id
        else:
            file_id = message.id
        
        encoded_file_id = encode_file_id(str(file_id))
        bot_username = (await client.get_me()).username
        shareable_link = f"https://t.me/{bot_username}?start=file_{encoded_file_id}"
        
        if DATABASE_AVAILABLE:
            try:
                await db.add_file(file_id, user_id)
            except Exception as e:
                print(f"Database error: {e}")

        file_name, file_size = "Unknown", "Unknown"
        
        media = message.document or message.video or message.audio or message.photo
        if media:
            file_name = getattr(media, 'file_name', 'Photo') or "Unknown"
            if media.file_size:
                file_size = f"{media.file_size / (1024*1024):.2f} MB"
        
        success_text = f"""✅ **FILE SUCCESSFULLY PROCESSED!**

📁 **File Name:** `{file_name}`
📏 **File Size:** `{file_size}`
🔗 **Shareable Link:** `{shareable_link}`

**📋 How to use:**
• Copy the link above
• Share it with anyone
• They can download the file using this link"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 COPY LINK", url=shareable_link)],
            [InlineKeyboardButton("🔗 GENERATE MORE", callback_data="generate_more")]
        ])
        
        await processing_msg.edit_text(
            success_text,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
        print(f"✅ File processed successfully for user {user_id}: {file_name}")
        
    except Exception as e:
        error_text = f"❌ **ERROR PROCESSING FILE**\n\n**Error Details:** `{e}`"
        await processing_msg.edit_text(error_text)
        print(f"❌ Error processing file for user {user_id}: {e}")

# This handler now has priority (group=-1) to run before other start handlers
@Client.on_message(filters.command("start") & filters.private, group=-1)
async def handle_file_access(client: Client, message: Message):
    if len(message.command) > 1 and message.command[1].startswith("file_"):
        try:
            encoded_file_id = message.command[1].replace("file_", "")
            file_id = int(decode_file_id(encoded_file_id))
            
            loading_msg = await message.reply_text("🔄 **Loading your file...**")
            
            try:
                if CHANNEL_ID:
                    await client.copy_message(
                        chat_id=message.from_user.id,
                        from_chat_id=CHANNEL_ID,
                        message_id=file_id
                    )
                else:
                    await loading_msg.edit_text("❌ **File not found.** (Storage channel not configured).")
                    raise StopPropagation

                await loading_msg.delete()
                await message.reply_text("✅ **File delivered successfully!**")
                print(f"✅ File delivered successfully to user {message.from_user.id}")
                
            except Exception as e:
                await loading_msg.edit_text(f"❌ **Error accessing file:** `{e}`")
                print(f"❌ Error accessing file: {e}")
        
        except Exception as e:
            await message.reply_text(f"❌ **Invalid file link:** `{e}`")
            print(f"❌ Invalid file link: {e}")
        
        # This stops the other /start handler in commands.py from running
        raise StopPropagation

# Callback handlers
@Client.on_callback_query(filters.regex("generate_more|try_again"))
async def utility_callbacks(client: Client, query):
    await query.edit_message_text(
        "📤 **READY FOR MORE FILES!**\n\n**Send me any file and I'll generate a shareable link for you.**"
    )

# Admin stats command
@Client.on_message(filters.command("filestats") & filters.private)
async def file_stats(client: Client, message: Message):
    if not (ADMINS and message.from_user.id in ADMINS):
        return await message.reply_text("❌ **Access Denied!**")
    
    if not DATABASE_AVAILABLE:
        return await message.reply_text("📊 **Stats unavailable (Database disabled).**")

    try:
        total_files = await db.total_files_count()
        total_users = await db.total_users_count()
        stats_text = f"""📊 **FILE STATISTICS**

📁 **Total Files Stored:** {total_files}
👥 **Total Users:** {total_users}"""
        await message.reply_text(stats_text)
        
    except Exception as e:
        await message.reply_text(f"❌ **Error fetching stats:** `{e}`")

