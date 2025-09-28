# clone_plugins/genlink.py - Smart file handling for clone bots

from pyrogram import Client, filters
from pyrogram.types import Message
import base64

# Try to import main bot config for file storage
try:
    from config import LOG_CHANNEL, ADMINS, PUBLIC_FILE_STORE, WEBSITE_URL_MODE, WEBSITE_URL
    MAIN_CONFIG_AVAILABLE = True
except:
    MAIN_CONFIG_AVAILABLE = False
    LOG_CHANNEL = None
    ADMINS = []
    PUBLIC_FILE_STORE = True

# Database import (optional)
try:
    from database.database import db
    DATABASE_AVAILABLE = True
except:
    DATABASE_AVAILABLE = False

async def allowed(_, __, message):
    """Check if user is allowed to use the bot"""
    if PUBLIC_FILE_STORE:
        return True
    if message.from_user and message.from_user.id in ADMINS:
        return True
    return False

@Client.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.private & filters.create(allowed))
async def clone_file_handler(client: Client, message: Message):
    """Handle file uploads for clone bots"""
    
    # Get bot info
    bot_info = await client.get_me()
    user_id = message.from_user.id
    
    print(f"Clone bot {bot_info.username}: File received from user {user_id}")
    
    # Add user to database if available
    if DATABASE_AVAILABLE:
        try:
            await db.add_user(user_id)
        except Exception as e:
            print(f"Clone database error: {e}")
    
    try:
        # For clone bots, store files in LOG_CHANNEL if available
        if MAIN_CONFIG_AVAILABLE and LOG_CHANNEL:
            # Copy file to main bot's storage channel
            post = await message.copy(LOG_CHANNEL)
            file_id = str(post.id)
            
            # Generate link using main bot format
            string = 'file_' + file_id
            outstr = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
            
            # Create shareable link
            if WEBSITE_URL_MODE and WEBSITE_URL:
                share_link = f"{WEBSITE_URL}?start={outstr}"
            else:
                share_link = f"https://t.me/{bot_info.username}?start={outstr}"
            
            # Success message
            await message.reply(
                f"<b>✅ FILE LINK GENERATED!</b>\n\n"
                f"<b>🔗 Link:</b> <code>{share_link}</code>\n\n"
                f"<b>📋 How to use:</b>\n"
                f"• Copy the link above\n"
                f"• Share it with anyone\n" 
                f"• They can download using this link\n"
                f"• Link never expires!"
            )
            
            print(f"Clone bot: File {file_id} processed for user {user_id}")
            print(f"Clone bot: Link generated: {share_link}")
            
        else:
            # No main config available - clone bot can't store files
            await message.reply(
                "❌ **File Storage Not Available**\n\n"
                "This clone bot is not properly configured for file storage.\n"
                "Please contact the bot owner to set up file storage."
            )
            
    except Exception as e:
        await message.reply(f"❌ **Error processing file:** `{str(e)}`")
        print(f"Clone bot error: {str(e)}")

@Client.on_message(filters.command(['link']) & filters.private & filters.create(allowed))
async def clone_link_command(client: Client, message: Message):
    """Generate link for replied message in clone bot"""
    
    replied = message.reply_to_message
    if not replied:
        return await message.reply('❌ Reply to a message to get a shareable link.')
    
    if not (replied.document or replied.video or replied.audio or replied.photo):
        return await message.reply('❌ Please reply to a media file.')
    
    # Process like a regular file upload
    await clone_file_handler(client, replied)

# Simple stats command for clone bots
@Client.on_message(filters.command("stats") & filters.private)
async def clone_stats(client: Client, message: Message):
    """Show simple stats for clone bot"""
    
    bot_info = await client.get_me()
    
    if DATABASE_AVAILABLE:
        try:
            total_users = await db.total_users_count()
        except:
            total_users = "Error loading"
    else:
        total_users = "N/A"
    
    stats_text = f"""📊 **CLONE BOT STATISTICS**

🤖 **Bot:** @{bot_info.username}
👥 **Total Users:** {total_users}
💾 **Storage:** {'✅ Available' if MAIN_CONFIG_AVAILABLE and LOG_CHANNEL else '❌ Not Configured'}
🔗 **File Sharing:** {'✅ Active' if PUBLIC_FILE_STORE else '❌ Restricted'}

**Bot Status:** Online and working!"""
    
    await message.reply_text(stats_text)

print("✅ Clone genlink loaded - smart file handling system!")
if MAIN_CONFIG_AVAILABLE:
    print(f"📊 Connected to main storage: {LOG_CHANNEL}")
else:
    print("⚠️ Main config not available - limited functionality")
