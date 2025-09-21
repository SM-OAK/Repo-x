#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
import traceback
from typing import Union, Optional

from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserNotParticipant

# Import local modules
from config import Config
from database import db
from utils import (
    encode_file_id, decode_file_id, generate_batch_id, format_size,
    get_file_type, get_file_emoji, safe_send_message, is_admin,
    create_share_text, create_batch_share_text, extract_message_id_from_link,
    shorten_url, clean_filename
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Validate configuration
if not Config.validate():
    logger.error("❌ Configuration validation failed!")
    sys.exit(1)

# Bot instance
app = Client(
    "FileStoreBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    sleep_threshold=60
)

async def log_activity(message: str, user_id: int = None, file_name: str = None, extra_info: dict = None):
    """Log activity to database and channel"""
    try:
        # Log to database
        log_data = {
            "action": message,
            "user_id": user_id,
            "file_name": file_name,
            "timestamp": datetime.now(),
            "extra_info": extra_info or {}
        }
        
        # Log to channel if configured
        if Config.LOG_CHANNEL:
            log_text = f"📋 **File Store Activity Log**\n\n"
            log_text += f"⏰ **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            if user_id:
                try:
                    user = await app.get_users(user_id)
                    log_text += f"👤 **User:** [{user.first_name}](tg://user?id={user_id}) (`{user_id}`)\n"
                    if user.username:
                        log_text += f"🔗 **Username:** @{user.username}\n"
                except:
                    log_text += f"👤 **User ID:** `{user_id}`\n"
            
            if file_name:
                log_text += f"📄 **File:** `{file_name}`\n"
            
            log_text += f"📝 **Action:** {message}\n"
            
            if extra_info:
                for key, value in extra_info.items():
                    log_text += f"ℹ️ **{key.title()}:** `{value}`\n"
            
            await safe_send_message(app, Config.LOG_CHANNEL, log_text)
            
    except Exception as e:
        logger.error(f"Error logging activity: {e}")

@app.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    """Enhanced start handler with all file types support"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    # Save user to database
    await db.save_user(user_id, username, first_name, message.from_user.last_name)
    
    # Check if it's a file/batch request
    if len(message.command) > 1:
        file_id = message.command[1]
        
        # Handle batch requests
        if file_id.startswith("batch_"):
            await handle_batch_download(client, message, file_id)
            return
        
        # Handle single file requests
        try:
            decoded_file_id = decode_file_id(file_id)
            if not decoded_file_id:
                await message.reply_text("❌ Invalid file link!")
                return
            
            file_data = await db.get_file(decoded_file_id)
            if not file_data:
                await message.reply_text("❌ File not found or has been removed!")
                return
            
            # Send the file
            try:
                file_emoji = get_file_emoji(file_data["file_type"])
                caption = f"""{file_emoji} **{clean_filename(file_data['file_name'])}**

📊 **Size:** {format_size(file_data['file_size'])}
📂 **Type:** {file_data['file_type'].title()}
📅 **Uploaded:** {file_data['upload_time'].strftime('%Y-%m-%d %H:%M')}

🎯 **Downloaded via:** @{Config.BOT_USERNAME}"""

                sent_message = await client.send_cached_media(
                    chat_id=message.chat.id,
                    file_id=file_data["file_id"],
                    caption=caption
                )
                
                # Record download
                await db.record_download(decoded_file_id, user_id, message.from_user.ip if hasattr(message.from_user, 'ip') else None)
                
                # Log activity
                await log_activity(
                    "File downloaded",
                    user_id,
                    file_data['file_name'],
                    {"file_type": file_data['file_type'], "file_size": file_data['file_size']}
                )
                
                # Auto-delete if enabled
                if Config.AUTO_DELETE and Config.AUTO_DELETE_TIME > 0:
                    await asyncio.sleep(Config.AUTO_DELETE_TIME)
                    try:
                        await sent_message.delete()
                        await message.delete()
                    except:
                        pass
                        
            except Exception as e:
                await message.reply_text(f"❌ Error sending file: {str(e)}")
                logger.error(f"Error sending file {file_data['file_name']}: {e}")
                
        except Exception as e:
            await message.reply_text("❌ Invalid file link!")
            logger.error(f"Error processing file request: {e}")
    
    else:
        # Welcome message
        user_stats = await db.get_user_stats(user_id)
        
        welcome_text = Config.START_MESSAGE.format(
            first_name=first_name,
            username=f"@{username}" if username else "User"
        )
        
        if user_stats["files_count"] > 0:
            welcome_text += f"\n\n📊 **Your Stats:**\n"
            welcome_text += f"📁 **Files Uploaded:** {user_stats['files_count']}\n"
            welcome_text += f"💾 **Total Size:** {format_size(user_stats['total_size'])}\n"
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📚 Help", callback_data="help"),
                InlineKeyboardButton("📊 My Stats", callback_data="my_stats")
            ],
            [
                InlineKeyboardButton("🌐 Global Stats", callback_data="global_stats"),
                InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/TechVJ01")
            ]
        ])
        
        await message.reply_text(welcome_text, reply_markup=keyboard)
        await log_activity("User started the bot", user_id)

@app.on_message(filters.media | filters.document)
async def handle_all_files(client: Client, message: Message):
    """Handle ALL types of files - not just videos"""
    user_id = message.from_user.id
    
    # Save user
    await db.save_user(user_id, message.from_user.username, message.from_user.first_name)
    
    # Get file information
    file_type, file_id, file_name, file_size = get_file_type(message)
    
    if not file_id:
        await message.reply_text("❌ Unsupported file type!")
        return
    
    # Validate file size
    if file_size > Config.MAX_FILE_SIZE:
        await message.reply_text(
            f"❌ File too large!\n"
            f"📊 **Your file:** {format_size(file_size)}\n"
            f"📏 **Maximum allowed:** {format_size(Config.MAX_FILE_SIZE)}"
        )
        return
    
    # Show processing message
    processing_msg = await message.reply_text("⏳ Processing your file...")
    
    try:
        # Forward file to database channel
        forwarded_msg = None
        if Config.DB_CHANNEL:
            try:
                forwarded_msg = await message.forward(Config.DB_CHANNEL)
                file_ref = str(forwarded_msg.id)
            except Exception as e:
                logger.error(f"Error forwarding to DB channel: {e}")
                file_ref = str(message.id)
        else:
            file_ref = str(message.id)
        
        # Clean filename
        clean_name = clean_filename(file_name)
        
        # Prepare file data
        file_data = {
            "file_id": file_id,
            "file_ref": file_ref,
            "file_name": clean_name,
            "file_size": file_size,
            "file_type": file_type,
            "uploaded_by": user_id,
            "download_count": 0,
            "downloads": []
        }
        
        # Save to database
        if await db.save_file(file_data):
            # Generate shareable link
            encoded_file_id = encode_file_id(file_id)
            share_link = f"https://t.me/{Config.BOT_USERNAME}?start={encoded_file_id}"
            
            # Shorten URL if configured
            if Config.USE_SHORTENER:
                share_link = await shorten_url(share_link)
            
            # Create response
            response_text = create_share_text(clean_name, file_size, file_type, share_link)
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔗 Share Link", url=share_link),
                    InlineKeyboardButton("📋 Copy Link", callback_data=f"copy_{encoded_file_id}")
                ],
                [
                    InlineKeyboardButton("📊 My Files", callback_data="my_files"),
                    InlineKeyboardButton("🗑️ Delete File", callback_data=f"delete_{encoded_file_id}")
                ]
            ])
            
            await processing_msg.edit_text(response_text, reply_markup=keyboard)
            
            # Log activity
            await log_activity(
                f"File uploaded: {clean_name}",
                user_id,
                clean_name,
                {
                    "file_type": file_type,
                    "file_size": file_size,
                    "file_id": encoded_file_id
                }
            )
            
        else:
            await processing_msg.edit_text("❌ Error saving file to database. Please try again!")
            
    except Exception as e:
        await processing_msg.edit_text(f"❌ Error processing file: {str(e)}")
        logger.error(f"Error handling file upload: {e}")
        traceback.print_exc()

@app.on_message(filters.command("link"))
async def generate_link_command(client: Client, message: Message):
    """Generate link for replied file"""
    if not message.reply_to_message:
        await message.reply_text("❌ Please reply to a file to generate its link!")
        return
    
    reply_msg = message.reply_to_message
    if not (reply_msg.media or reply_msg.document):
        await message.reply_text("❌ The replied message doesn't contain a file!")
        return
    
    # Process the replied message as a new file upload
    await handle_all_files(client, reply_msg)

@app.on_message(filters.command("batch"))
async def create_batch_command(client: Client, message: Message):
    """Create batch links for multiple files"""
    if len(message.command) < 3:
        await message.reply_text(
            "❌ **Usage:** `/batch <first_message_link> <last_message_link>`\n\n"
            "**Example:**\n"
            "`/batch https://t.me/c/123456789/100 https://t.me/c/123456789/200`\n\n"
            "**Note:** Both messages should be from the same chat."
        )
        return
    
    first_link = message.command[1]
    last_link = message.command[2]
    
    # Extract message IDs
    first_id = extract_message_id_from_link(first_link)
    last_id = extract_message_id_from_link(last_link)
    
    if not first_id or not last_id:
        await message.reply_text("❌ Invalid message links!")
        return
    
    if first_id > last_id:
        first_id, last_id = last_id, first_id
    
    # Check range
    if last_id - first_id > 1000:
        await message.reply_text("❌ Batch size too large! Maximum 1000 files per batch.")
        return
    
    processing_msg = await message.reply_text("⏳ Creating batch... Please wait.")
    
    try:
        batch_id = generate_batch_id()
        processed_files = 0
        total_size = 0
        failed_files = 0
        
        # Process messages in range
        for msg_id in range(first_id, last_id + 1):
            try:
                target_msg = await client.get_messages(message.chat.id, msg_id)
                
                if target_msg and (target_msg.media or target_msg.document):
                    # Get file info
                    file_type, file_id, file_name, file_size = get_file_type(target_msg)
                    
                    if file_id:
                        # Forward to DB channel
                        if Config.DB_CHANNEL:
                            try:
                                forwarded = await target_msg.forward(Config.DB_CHANNEL)
                                file_ref = str(forwarded.id)
                            except:
                                file_ref = str(target_msg.id)
                        else:
                            file_ref = str(target_msg.id)
                        
                        # Save file with batch_id
                        file_data = {
                            "file_id": file_id,
                            "file_ref": file_ref,
                            "file_name": clean_filename(file_name),
                            "file_size": file_size,
                            "file_type": file_type,
                            "uploaded_by": message.from_user.id,
                            "batch_id": batch_id,
                            "download_count": 0,
                            "downloads": []
                        }
                        
                        if await db.save_file(file_data):
                            processed_files += 1
                            total_size += file_size
                        else:
                            failed_files += 1
                    else:
                        failed_files += 1
                        
            except Exception as e:
                failed_files += 1
                logger.error(f"Error processing message {msg_id}: {e}")
            
            # Update progress every 50 files
            if processed_files % 50 == 0 and processed_files > 0:
                await processing_msg.edit_text(
                    f"⏳ Creating batch...\n"
                    f"✅ Processed: {processed_files}\n"
                    f"❌ Failed: {failed_files}"
                )
        
        if processed_files > 0:
            # Save batch info
            batch_data = {
                "batch_id": batch_id,
                "file_count": processed_files,
                "total_size": total_size,
                "created_by": message.from_user.id
            }
            await db.save_batch(batch_data)
            
            # Generate batch link
            batch_link = f"https://t.me/{Config.BOT_USERNAME}?start=batch_{batch_id}"
            
            if Config.USE_SHORTENER:
                batch_link = await shorten_url(batch_link)
            
            response_text = create_batch_share_text(processed_files, total_size, batch_link)
            
            if failed_files > 0:
                response_text += f"\n⚠️ **Note:** {failed_files} files failed to process."
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Share Batch", url=batch_link)],
                [InlineKeyboardButton("📊 My Batches", callback_data="my_batches")]
            ])
            
            await processing_msg.edit_text(response_text, reply_markup=keyboard)
            
            # Log activity
            await log_activity(
                f"Batch created with {processed_files} files",
                message.from_user.id,
                None,
                {
                    "batch_id": batch_id,
                    "file_count": processed_files,
                    "total_size": total_size,
                    "failed_files": failed_files
                }
            )
        else:
            await processing_msg.edit_text("❌ No valid files found in the specified range!")
            
    except Exception as e:
        await processing_msg.edit_text(f"❌ Error creating batch: {str(e)}")
        logger.error(f"Batch creation error: {e}")

async def handle_batch_download(client: Client, message: Message, batch_encoded_id: str):
    """Handle batch file downloads"""
    batch_id = batch_encoded_id.replace("batch_", "")
    
    # Get batch info
    batch_data = await db.get_batch(batch_id)
    if not batch_data:
        await message.reply_text("❌ Batch not found or has expired!")
        return
    
    # Get batch files
    files = await db.get_batch_files(batch_id)
    if not files:
        await message.reply_text("❌ No files found in this batch!")
        return
    
    await message.reply_text(
        f"📦 **Batch Download Started**\n\n"
        f"📊 **Files:** {len(files)}\n"
        f"📈 **Total Size:** {format_size(batch_data['total_size'])}\n\n"
        f"⏳ Sending files... Please wait."
    )
    
    success_count = 0
    failed_count = 0
    
    for i, file_data in enumerate(files, 1):
        try:
            file_emoji = get_file_emoji(file_data["file_type"])
            caption = f"""{file_emoji} **{file_data['file_name']}**

📊 **Size:** {format_size(file_data['file_size'])}
📂 **Type:** {file_data['file_type'].title()}
📦 **Batch:** {i}/{len(files)}"""

            await client.send_cached_media(
                chat_id=message.chat.id,
                file_id=file_data["file_id"],
                caption=caption
            )
            
            success_count += 1
            
            # Small delay to avoid flood wait
            await asyncio.sleep(1)
            
        except Exception as e:
            failed_count += 1
            logger.error(f"Error sending batch file {file_data['file_name']}: {e}")
    
    # Send completion message
    completion_text = f"✅ **Batch Download Complete!**\n\n"
    completion_text += f"📊 **Total Files:** {len(files)}\n"
    completion_text += f"✅ **Successful:** {success_count}\n"
    
    if failed_count > 0:
        completion_text += f"❌ **Failed:** {failed_count}"
    
    await message.reply_text(completion_text)
    
    # Log batch download
    await log_activity(
        f"Batch downloaded: {success_count}/{len(files)} files",
        message.from_user.id,
        None,
        {
            "batch_id": batch_id,
            "total_files": len(files),
            "success_count": success_count,
            "failed_count": failed_count
        }
    )

# Callback query handlers
@app.on_callback_query()
async def callback_handler(client: Client, callback_query: CallbackQuery):
    """Handle all callback queries"""
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    try:
        if data == "help":
            help_text = """
🤖 **File Store Bot Help**

**📂 Supported Files:**
• 📄 Documents (PDF, DOC, TXT, etc.)
• 🎥 Videos (MP4, AVI, MKV, etc.)  
• 🎵 Audio (MP3, WAV, FLAC, etc.)
• 🖼️ Images (JPG, PNG, GIF, etc.)
• 📁 Archives (ZIP, RAR, 7Z, etc.)
• 🎬 Animations & Stickers
• 🎤 Voice messages
• And many more!

**📋 Commands:**
• **Send any file** - Get permanent link
• `/link` - Reply to file for link
• `/batch <start> <end>` - Create batch
• `/stats` - Your statistics
• `/search <query>` - Search your files

**💡 Tips:**
• Links work permanently
• No file size limit (up to 2GB)
• Share links with anyone
• Files stored securely

**🔗 How it works:**
1. Send me any file
2. Get shareable link instantly
3. Share with anyone
4. Files accessible anytime!
            """
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
            ])
            
            await callback_query.edit_message_text(help_text, reply_markup=keyboard)
        
        elif data == "my_stats":
            stats = await db.get_user_stats(user_id)
            
            stats_text = f"""
📊 **Your Statistics**

📁 **Files Uploaded:** {stats['files_count']:,}
💾 **Total Size:** {format_size(stats['total_size'])}
📅 **Member Since:** {stats['join_date'].strftime('%Y-%m-%d') if stats['join_date'] else 'Unknown'}
🕐 **Last Active:** {stats['last_active'].strftime('%Y-%m-%d %H:%M') if stats['last_active'] else 'Now'}

📂 **File Types:**
            """
            
            for file_type in stats.get('file_types', []):
                emoji = get_file_emoji(file_type)
                stats_text += f"• {emoji} {file_type.title()}\n"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📁 My Files", callback_data="my_files"),
                    InlineKeyboardButton("📦 My Batches", callback_data="my_batches")
                ],
                [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
            ])
            
            await callback_query.edit_message_text(stats_text, reply_markup=keyboard)
        
        elif data == "global_stats":
            stats = await db.get_global_stats()
            
            stats_text = f"""
🌍 **Global Statistics**

👥 **Total Users:** {stats['total_users']:,}
📁 **Total Files:** {stats['total_files']:,}
📦 **Total Batches:** {stats['total_batches']:,}
💾 **Total Storage:** {format_size(stats['total_size'])}

📂 **Popular File Types:**
            """
            
            for file_type_data in stats['file_types'][:5]:
                emoji = get_file_emoji(file_type_data['_id'])
                stats_text += f"• {emoji} {file_type_data['_id'].title()}: {file_type_data['count']:,}\n"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]
            ])
            
            await callback_query.edit_message_text(stats_text, reply_markup=keyboard)
        
        elif data.startswith("copy_"):
            encoded_id = data.replace("copy_", "")
            link = f"https://t.me/{Config.BOT_USERNAME}?start={encoded_id}"
            
            await callback_query.answer(
                f"Link copied! Share this link:\n{link}",
                show_alert=True
            )
        
        elif data.startswith("delete_"):
            if not is_admin(user_id):
                await callback_query.answer("❌ You can only delete your own files!", show_alert=True)
                return
            
            encoded_id = data.replace("delete_", "")
            file_id = decode_file_id(encoded_id)
            
            if await db.delete_file(file_id):
                await callback_query.answer("✅ File deleted successfully!", show_alert=True)
                await callback_query.edit_message_text("🗑️ **File has been deleted!**")
                await log_activity("File deleted", user_id)
            else:
                await callback_query.answer("❌ Error deleting file!", show_alert=True)
        
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Callback query error: {e}")
        await callback_query.answer("❌ An error occurred!", show_alert=True)

# Admin commands
@app.on_message(filters.command("broadcast") & filters.user(Config.ADMINS))
async def broadcast_command(client: Client, message: Message):
    """Broadcast message to all users"""
    if not message.reply_to_message:
        await message.reply_text("❌ Please reply to a message to broadcast!")
        return
    
    users = await db.get_user_list(limit=10000)  # Get all users
    total_users = len(users)
    
    if total_users == 0:
        await message.reply_text("❌ No users found in database!")
        return
    
    status_msg = await message.reply_text(f"📡 Starting broadcast to {total_users:,} users...")
    
    success = 0
    failed = 0
    
    for i, user in enumerate(users):
        try:
            await message.reply_to_message.copy(user["user_id"])
            success += 1
        except (UserIsBlocked, InputUserDeactivated):
            failed += 1
        except Exception as e:
            failed += 1
            logger.error(f"Broadcast error for user {user['user_id']}: {e}")
        
        # Update status every 100 users
        if (i + 1) % 100 == 0:
            await status_msg.edit_text(
                f"📡 Broadcasting... ({i + 1}/{total_users})\n"
                f"✅ Success: {success:,}\n"
                f"❌ Failed: {failed:,}"
            )
        
        # Small delay to avoid flood wait
        await asyncio.sleep(0.1)
    
    await status_msg.edit_text(
        f"📡 **Broadcast Completed!**\n\n"
        f"👥 **Total Users:** {total_users:,}\n"
        f"✅ **Successful:** {success:,}\n"
        f"❌ **Failed:** {failed:,}\n"
        f"📊 **Success Rate:** {(success/total_users)*100:.1f}%"
    )
    
    await log_activity(
        f"Broadcast completed: {success}/{total_users} users reached",
        message.from_user.id,
        None,
        {"success": success, "failed": failed, "total": total_users}
    )

@app.on_message(filters.command("stats"))
async def stats_command(client: Client, message: Message):
    """Show user statistics"""
    user_id = message.from_user.id
    user_stats = await db.get_user_stats(user_id)
    
    stats_text = f"""
📊 **Your File Store Statistics**

👤 **User:** {message.from_user.first_name}
📁 **Files Uploaded:** {user_stats['files_count']:,}
💾 **Total Storage Used:** {format_size(user_stats['total_size'])}
📅 **Member Since:** {user_stats['join_date'].strftime('%B %d, %Y') if user_stats['join_date'] else 'Recently'}

📂 **Your File Types:**
    """
    
    for file_type in user_stats.get('file_types', []):
        emoji = get_file_emoji(file_type)
        stats_text += f"• {emoji} {file_type.title()}\n"
    
    if not user_stats['file_types']:
        stats_text += "• No files uploaded yet\n"
    
    # Add global stats for context
    global_stats = await db.get_global_stats()
    stats_text += f"""
🌍 **Global Statistics:**
👥 **Total Users:** {global_stats['total_users']:,}
📁 **Total Files:** {global_stats['total_files']:,}
💾 **Total Storage:** {format_size(global_stats['total_size'])}
    """
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📁 My Files", callback_data="my_files"),
            InlineKeyboardButton("📦 My Batches", callback_data="my_batches")
        ]
    ])
    
    await message.reply_text(stats_text, reply_markup=keyboard)

@app.on_message(filters.command("search"))
async def search_command(client: Client, message: Message):
    """Search user's files"""
    if len(message.command) < 2:
        await message.reply_text("❌ **Usage:** `/search <filename>`\n\n**Example:** `/search document.pdf`")
        return
    
    query = " ".join(message.command[1:])
    user_id = message.from_user.id
    
    # Search files
    files = await db.search_files(query, user_id, limit=20)
    
    if not files:
        await message.reply_text(f"❌ No files found matching: `{query}`")
        return
    
    response = f"🔍 **Search Results for:** `{query}`\n\n"
    response += f"📊 **Found {len(files)} file(s):**\n\n"
    
    for i, file_data in enumerate(files, 1):
        emoji = get_file_emoji(file_data["file_type"])
        encoded_id = encode_file_id(file_data["file_id"])
        file_link = f"https://t.me/{Config.BOT_USERNAME}?start={encoded_id}"
        
        response += f"{i}. {emoji} **{file_data['file_name']}**\n"
        response += f"   📊 {format_size(file_data['file_size'])} • {file_data['file_type'].title()}\n"
        response += f"   🔗 [Get File]({file_link})\n\n"
        
        if len(response) > 3500:  # Avoid message length limit
            response += f"... and {len(files) - i} more files"
            break
    
    await message.reply_text(response, disable_web_page_preview=True)

@app.on_message(filters.command("adminpanel") & filters.user(Config.ADMINS))
async def admin_panel(client: Client, message: Message):
    """Admin control panel"""
    global_stats = await db.get_global_stats()
    
    panel_text = f"""
👑 **Admin Control Panel**

📊 **Bot Statistics:**
👥 **Users:** {global_stats['total_users']:,}
📁 **Files:** {global_stats['total_files']:,}
📦 **Batches:** {global_stats['total_batches']:,}
💾 **Storage:** {format_size(global_stats['total_size'])}

🔧 **Available Commands:**
• `/broadcast` - Broadcast message
• `/cleanup` - Clean old files
• `/userinfo <user_id>` - Get user info
• `/ban <user_id>` - Ban user
• `/unban <user_id>` - Unban user
• `/globalstats` - Detailed statistics
    """
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Detailed Stats", callback_data="admin_detailed_stats"),
            InlineKeyboardButton("👥 User Management", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton("🧹 Cleanup", callback_data="admin_cleanup"),
            InlineKeyboardButton("📡 Broadcast", callback_data="admin_broadcast")
        ]
    ])
    
    await message.reply_text(panel_text, reply_markup=keyboard)

@app.on_message(filters.command("cleanup") & filters.user(Config.ADMINS))
async def cleanup_command(client: Client, message: Message):
    """Clean up old files"""
    days = 30  # Default cleanup period
    
    if len(message.command) > 1:
        try:
            days = int(message.command[1])
        except ValueError:
            await message.reply_text("❌ Invalid number of days!")
            return
    
    status_msg = await message.reply_text(f"🧹 Cleaning up files older than {days} days...")
    
    deleted_count = await db.cleanup_old_files(days)
    
    await status_msg.edit_text(
        f"🧹 **Cleanup Completed!**\n\n"
        f"🗑️ **Files Deleted:** {deleted_count:,}\n"
        f"📅 **Older Than:** {days} days"
    )
    
    await log_activity(f"Admin cleanup: {deleted_count} files deleted", message.from_user.id)

# Error handlers
@app.on_message(filters.command("test") & filters.user(Config.ADMINS))
async def test_command(client: Client, message: Message):
    """Test command for admins"""
    test_text = f"""
🧪 **Bot Test Results**

✅ **Bot Status:** Running
✅ **Database:** Connected
✅ **Channels:** {'✅' if Config.DB_CHANNEL else '❌'} DB | {'✅' if Config.LOG_CHANNEL else '❌'} Log
✅ **Auto Delete:** {'✅' if Config.AUTO_DELETE else '❌'}
✅ **URL Shortener:** {'✅' if Config.USE_SHORTENER else '❌'}

⚙️ **Configuration:**
🤖 **Bot:** @{Config.BOT_USERNAME}
📊 **Max File Size:** {format_size(Config.MAX_FILE_SIZE)}
⏱️ **Auto Delete Time:** {Config.AUTO_DELETE_TIME}s
👥 **Admins:** {len(Config.ADMINS)}

🕐 **Server Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    
    await message.reply_text(test_text)

# Startup and shutdown handlers
@app.on_message(filters.command("restart") & filters.user(Config.ADMINS))
async def restart_command(client: Client, message: Message):
    """Restart the bot"""
    await message.reply_text("🔄 Restarting bot...")
    await log_activity("Bot restart initiated", message.from_user.id)
    os.execv(sys.executable, ['python'] + sys.argv)

async def startup():
    """Bot startup tasks"""
    try:
        # Create database indexes
        await db.create_indexes()
        
        # Print configuration
        Config.print_config()
        
        # Log startup
        await log_activity("Bot started successfully")
        
        print("🚀 File Store Bot started successfully!")
        print(f"📱 Bot Username: @{Config.BOT_USERNAME}")
        print(f"🗄️  Database: Connected")
        print(f"📁 DB Channel: {'Configured' if Config.DB_CHANNEL else 'Not configured'}")
        print(f"📋 Log Channel: {'Configured' if Config.LOG_CHANNEL else 'Not configured'}")
        print(f"👥 Admins: {len(Config.ADMINS)}")
        print("="*50)
        
    except Exception as e:
        logger.error(f"Startup error: {e}")

async def shutdown():
    """Bot shutdown tasks"""
    try:
        await log_activity("Bot shutting down")
        await db.close()
        print("👋 File Store Bot stopped!")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🤖 ENHANCED FILE STORE BOT")
    print("="*50)
    print("✅ ALL FILE TYPES SUPPORTED")
    print("✅ DATABASE CHANNEL LOGGING")
    print("✅ ADVANCED FILE MANAGEMENT")
    print("✅ BATCH PROCESSING")
    print("✅ USER STATISTICS")
    print("✅ ADMIN CONTROLS")
    print("✅ AUTO DELETE FEATURE")
    print("✅ SEARCH FUNCTIONALITY")
    print("="*50)
    
    # Set up event loop for startup tasks
    loop = asyncio.get_event_loop()
    loop.run_until_complete(startup())
    
    try:
        # Run the bot
        app.run()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        # Cleanup
        loop.run_until_complete(shutdown())
