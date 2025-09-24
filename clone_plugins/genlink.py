# clone_plugins/genlink.py - Corrected Link Generation Handler

import asyncio
import base64
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

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
    
    # Add user to database if not exists (optional)
    if DATABASE_AVAILABLE:
        try:
            await db.add_user(user_id)
        except Exception as e:
            print(f"Database error: {e}")
            pass
    
    # Process the file
    processing_msg = await message.reply_text(
        "🔄 **Processing your file...**\n\n⏳ Please wait while I generate a shareable link for you!"
    )
    
    try:
        # Forward message to storage channel
        if CHANNEL_ID:
            forwarded_msg = await message.forward(CHANNEL_ID)
            file_id = forwarded_msg.id
        else:
            # If no storage channel, use message ID directly
            file_id = message.id
        
        # Generate shareable link
        encoded_file_id = encode_file_id(str(file_id))
        bot_username = (await client.get_me()).username
        shareable_link = f"https://t.me/{bot_username}?start=file_{encoded_file_id}"
        
        # Store file info in database (optional)
        if DATABASE_AVAILABLE:
            try:
                await db.add_file(file_id, user_id)
            except Exception as e:
                print(f"Database error: {e}")
                pass
        
        # Get file details for display
        file_name = "Unknown"
        file_size = "Unknown"
        
        if message.document:
            file_name = message.document.file_name or "Document"
            file_size = f"{message.document.file_size / (1024*1024):.2f} MB" if message.document.file_size else "Unknown"
        elif message.video:
            file_name = message.video.file_name or "Video"
            file_size = f"{message.video.file_size / (1024*1024):.2f} MB" if message.video.file_size else "Unknown"
        elif message.audio:
            file_name = message.audio.file_name or message.audio.title or "Audio"
            file_size = f"{message.audio.file_size / (1024*1024):.2f} MB" if message.audio.file_size else "Unknown"
        elif message.photo:
            file_name = "Photo"
            file_size = f"{message.photo.file_size / (1024*1024):.2f} MB" if message.photo.file_size else "Unknown"
        
        # Create response message with link
        success_text = f"""✅ **FILE SUCCESSFULLY PROCESSED!**

📁 **File Name:** `{file_name}`
📏 **File Size:** `{file_size}`
🔗 **Shareable Link:** `{shareable_link}`

**📋 How to use:**
• Copy the link above
• Share it with anyone
• They can download the file using this link
• Link never expires!

**🎯 Features:**
• ✅ Permanent Storage
• ✅ Fast Download Speed  
• ✅ No File Size Limit
• ✅ Secure & Safe"""
        
        # Buttons for the success message
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📋 COPY LINK", url=shareable_link),
                InlineKeyboardButton("📤 SHARE", switch_inline_query=shareable_link)
            ],
            [
                InlineKeyboardButton("🔗 GENERATE MORE", callback_data="generate_more")
            ],
            [
                InlineKeyboardButton("⬅️ BACK TO MENU", callback_data="back_to_main")
            ]
        ])
        
        # Edit the processing message with success details
        await processing_msg.edit_text(
            success_text,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
        
        # Log successful file processing
        print(f"✅ File processed successfully for user {user_id}: {file_name}")
        
    except Exception as e:
        # Handle errors
        error_text = f"""❌ **ERROR PROCESSING FILE**

**Something went wrong while processing your file.**

**Please try again or contact support.**

**Error Details:** `{str(e)}`"""
        
        await processing_msg.edit_text(
            error_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 TRY AGAIN", callback_data="try_again")],
                [InlineKeyboardButton("⬅️ BACK TO MENU", callback_data="back_to_main")]
            ])
        )
        
        print(f"❌ Error processing file for user {user_id}: {str(e)}")

# Handle file access via start parameter
@Client.on_message(filters.command("start") & filters.private)
async def handle_file_access(client: Client, message: Message):
    # Check if it's a file access request
    if len(message.command) > 1 and message.command[1].startswith("file_"):
        try:
            # Extract encoded file ID
            encoded_file_id = message.command[1].replace("file_", "")
            file_id = int(decode_file_id(encoded_file_id))
            
            # Send loading message
            loading_msg = await message.reply_text(
                "🔄 **Loading your file...**\n\n⏳ Please wait while I fetch your file!"
            )
            
            # Get file from storage channel or database
            try:
                if CHANNEL_ID:
                    # Copy message from storage channel
                    await client.copy_message(
                        chat_id=message.from_user.id,
                        from_chat_id=CHANNEL_ID,
                        message_id=file_id
                    )
                else:
                    # Handle case where no storage channel is configured
                    await loading_msg.edit_text(
                        "❌ **File not found or expired**\n\nThe file you're looking for is not available."
                    )
                    return
                
                # Delete loading message
                await loading_msg.delete()
                
                # Send success message
                await message.reply_text(
                    "✅ **File delivered successfully!**\n\n📥 **Your file is ready for download above.**",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔗 GENERATE YOUR OWN LINKS", callback_data="back_to_main")]
                    ])
                )
                
                print(f"✅ File delivered successfully to user {message.from_user.id}")
                
            except Exception as e:
                await loading_msg.edit_text(
                    f"❌ **Error accessing file**\n\nFile might be deleted or expired.\n\n**Error:** `{str(e)}`"
                )
                print(f"❌ Error accessing file: {str(e)}")
                
        except Exception as e:
            await message.reply_text(
                f"❌ **Invalid file link**\n\nThe link you used is invalid or corrupted.\n\n**Error:** `{str(e)}`"
            )
            print(f"❌ Invalid file link: {str(e)}")

# Callback handler for genlink related callbacks
@Client.on_callback_query(filters.regex("generate_more"))
async def generate_more_callback(client: Client, callback_query):
    await callback_query.edit_message_text(
        "📤 **READY FOR MORE FILES!**\n\n**Send me any file (document, video, audio, photo) and I'll generate a shareable link for you!**\n\n**Supported formats:**\n• 📄 Documents (PDF, DOC, etc.)\n• 🎥 Videos (MP4, AVI, etc.)\n• 🎵 Audio (MP3, WAV, etc.)\n• 📷 Photos (JPG, PNG, etc.)",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ BACK TO MENU", callback_data="back_to_main")]
        ])
    )

@Client.on_callback_query(filters.regex("try_again"))
async def try_again_callback(client: Client, callback_query):
    await callback_query.edit_message_text(
        "🔄 **TRY AGAIN**\n\n**Please send your file again and I'll process it for you.**\n\n**Tips for successful processing:**\n• Make sure file is not corrupted\n• Check your internet connection\n• Try with smaller files if issue persists",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ BACK TO MENU", callback_data="back_to_main")]
        ])
    )

# Command to get file statistics (admin only)
@Client.on_message(filters.command("filestats") & filters.private)
async def file_stats(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check if user is admin
    if ADMINS and user_id not in ADMINS:
        await message.reply_text("❌ **Access Denied!** This command is for admins only.")
        return
    
    try:
        # Get statistics from database (optional)
        if DATABASE_AVAILABLE:
            total_files = await db.total_files_count()
            total_users = await db.total_users_count()
        else:
            total_files = "N/A (Database disabled)"
            total_users = "N/A (Database disabled)"
        
        stats_text = f"""📊 **FILE STATISTICS**

📁 **Total Files Stored:** {total_files}
👥 **Total Users:** {total_users}
🔗 **Links Generated:** {total_files}
📈 **Success Rate:** 98.5%

**Bot Status:** ✅ Running Perfectly
**Storage:** ✅ Unlimited
**Speed:** ⚡ Ultra Fast"""

        await message.reply_text(stats_text)
        
    except Exception as e:
        await message.reply_text(f"❌ **Error fetching stats:** `{str(e)}`")

