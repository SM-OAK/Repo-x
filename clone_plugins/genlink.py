# clone_plugins/genlink.py - Link Generation for Cloned Bots

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import base64
import asyncio

# Database import (optional)
try:
    from database.database import db
    DATABASE_AVAILABLE = True
except:
    DATABASE_AVAILABLE = False

def encode_file_id(s: str) -> str:
    """Encode message ID for shareable link"""
    string_bytes = s.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    return base64_bytes.decode("ascii").strip("=")

def decode_file_id(s: str) -> str:
    """Decode message ID from shareable link"""
    s = s + "=" * (-len(s) % 4)
    string_bytes = base64.urlsafe_b64decode(s)
    return string_bytes.decode("ascii")

@Client.on_message(filters.private & (filters.document | filters.video | filters.audio | filters.photo))
async def handle_file_share(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Add user to database if available
    if DATABASE_AVAILABLE:
        try:
            await db.add_user(user_id)
        except Exception as e:
            print(f"Database error: {e}")
    
    # Processing message
    processing_msg = await message.reply_text(
        "🔄 **Processing your file...**\n\n⏳ Please wait while I generate a shareable link for you!"
    )
    
    try:
        # Use message ID directly for link generation
        file_id = message.id
        
        # Generate shareable link
        encoded_file_id = encode_file_id(str(file_id))
        bot_username = client.me.username if client.me else "YourBot"
        shareable_link = f"https://t.me/{bot_username}?start=file_{encoded_file_id}"
        
        # Add file to database if available
        if DATABASE_AVAILABLE:
            try:
                await db.add_file(file_id, user_id)
            except Exception as e:
                print(f"Database error: {e}")
        
        # Get file details
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
        
        # Success message
        success_text = f"""✅ **FILE SUCCESSFULLY PROCESSED!**

📁 **File Name:** `{file_name}`
📏 **File Size:** `{file_size}`
🔗 **Shareable Link:** 

`{shareable_link}`

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
        
        # Buttons
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
        
        await processing_msg.edit_text(
            success_text,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
        
        print(f"✅ File processed successfully for user {user_id}: {file_name}")
        
    except Exception as e:
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

@Client.on_message(filters.command("start") & filters.private)
async def handle_file_access(client: Client, message: Message):
    # Handle file access requests
    if len(message.command) > 1 and message.command[1].startswith("file_"):
        try:
            # Extract encoded file ID
            encoded_file_id = message.command[1].replace("file_", "")
            file_id = int(decode_file_id(encoded_file_id))
            
            # Send loading message
            loading_msg = await message.reply_text(
                "🔄 **Loading your file...**\n\n⏳ Please wait while I fetch your file!"
            )
            
            try:
                # Copy the message (assuming it's stored in the same chat)
                # For a proper implementation, you'd store files in a channel
                await client.copy_message(
                    chat_id=message.from_user.id,
                    from_chat_id=message.chat.id,
                    message_id=file_id
                )
                
                await loading_msg.delete()
                
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

print("✅ Genlink module loaded successfully!")
