from pyrogram import Client, filters
from pyrogram.types import Message
import base64
import logging

logger = logging.getLogger(__name__)

# Import configurations with graceful fallback
try:
    from config import LOG_CHANNEL, ADMINS, PUBLIC_FILE_STORE, WEBSITE_URL_MODE, WEBSITE_URL
    CONFIG_AVAILABLE = True
except:
    CONFIG_AVAILABLE = False
    LOG_CHANNEL = None
    ADMINS = []
    PUBLIC_FILE_STORE = True
    WEBSITE_URL_MODE = False
    WEBSITE_URL = ""

# Database import (optional)
try:
    from database.database import db
    DB_AVAILABLE = True
except:
    DB_AVAILABLE = False

async def allowed(_, __, message):
    """Check if user can upload files"""
    if PUBLIC_FILE_STORE:
        return True
    if message.from_user and message.from_user.id in ADMINS:
        return True
    return False

@Client.on_message(
    (filters.document | filters.video | filters.audio | filters.photo) & 
    filters.private & 
    filters.create(allowed),
    group=1  # Lower priority than main bot
)
async def clone_file_handler(client: Client, message: Message):
    """Handle file uploads for clone bots"""
    
    bot_info = await client.get_me()
    user_id = message.from_user.id
    
    logger.info(f"Clone {bot_info.username}: File from user {user_id}")
    
    # Add user to database
    if DB_AVAILABLE:
        try:
            if not await db.is_user_exist(user_id):
                await db.add_user(user_id, message.from_user.first_name)
        except Exception as e:
            logger.error(f"Clone DB error: {e}")
    
    # Check if storage is configured
    if not (CONFIG_AVAILABLE and LOG_CHANNEL):
        return await message.reply(
            "<b>❌ Fɪʟᴇ Sᴛᴏʀᴀɢᴇ Nᴏᴛ Cᴏɴғɪɢᴜʀᴇᴅ!</b>\n\n"
            "Cᴏɴᴛᴀᴄᴛ ᴛʜᴇ ʙᴏᴛ ᴏᴡɴᴇʀ ᴛᴏ sᴇᴛᴜᴘ ғɪʟᴇ sᴛᴏʀᴀɢᴇ."
        )
    
    try:
        # Copy file to log channel
        post = await message.copy(LOG_CHANNEL)
        file_id = str(post.id)
        
        # Generate encoded string
        string = f'file_{file_id}'
        encoded = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
        
        # Create shareable link
        if WEBSITE_URL_MODE and WEBSITE_URL:
            share_link = f"{WEBSITE_URL}?start={encoded}"
        else:
            share_link = f"https://t.me/{bot_info.username}?start={encoded}"
from pyrogram import Client, filters
from pyrogram.types import Message
import base64
import logging

logger = logging.getLogger(__name__)

# Import configurations with graceful fallback
try:
    from config import LOG_CHANNEL, ADMINS, PUBLIC_FILE_STORE, WEBSITE_URL_MODE, WEBSITE_URL
    CONFIG_AVAILABLE = True
except:
    CONFIG_AVAILABLE = False
    LOG_CHANNEL = None
    ADMINS = []
    PUBLIC_FILE_STORE = True
    WEBSITE_URL_MODE = False
    WEBSITE_URL = ""

# Database import (optional)
try:
    from database.database import db
    DB_AVAILABLE = True
except:
    DB_AVAILABLE = False

async def allowed(_, __, message):
    """Check if user can upload files"""
    if PUBLIC_FILE_STORE:
        return True
    if message.from_user and message.from_user.id in ADMINS:
        return True
    return False

@Client.on_message(
    (filters.document | filters.video | filters.audio | filters.photo) & 
    filters.private & 
    filters.create(allowed),
    group=1  # Lower priority than main bot
)
async def clone_file_handler(client: Client, message: Message):
    """Handle file uploads for clone bots"""
    
    bot_info = await client.get_me()
    user_id = message.from_user.id
    
    logger.info(f"Clone {bot_info.username}: File from user {user_id}")
    
    # Add user to database
    if DB_AVAILABLE:
        try:
            if not await db.is_user_exist(user_id):
                await db.add_user(user_id, message.from_user.first_name)
        except Exception as e:
            logger.error(f"Clone DB error: {e}")
    
    # Check if storage is configured
    if not (CONFIG_AVAILABLE and LOG_CHANNEL):
        return await message.reply(
            "<b>❌ Fɪʟᴇ Sᴛᴏʀᴀɢᴇ Nᴏᴛ Cᴏɴғɪɢᴜʀᴇᴅ!</b>\n\n"
            "Cᴏɴᴛᴀᴄᴛ ᴛʜᴇ ʙᴏᴛ ᴏᴡɴᴇʀ ᴛᴏ sᴇᴛᴜᴘ ғɪʟᴇ sᴛᴏʀᴀɢᴇ."
        )
    
    try:
        # Copy file to log channel
        post = await message.copy(LOG_CHANNEL)
        file_id = str(post.id)
        
        # Generate encoded string
        string = f'file_{file_id}'
        encoded = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
        
        # Create shareable link
        if WEBSITE_URL_MODE and WEBSITE_URL:
            share_link = f"{WEBSITE_URL}?start={encoded}"
        else:
            share_link = f"https://t.me/{bot_info.username}?start={encoded}"
        
        # Send link to user
        await message.reply(
            f"<b>⭕ Hᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\n"
            f"🔗 Lɪɴᴋ: <code>{share_link}</code>\n\n"
            f"💡 Sʜᴀʀᴇ ᴛʜɪs ʟɪɴᴋ ᴛᴏ ᴀᴄᴄᴇss ᴛʜᴇ ғɪʟᴇ!</b>",
            quote=True
        )
        
        logger.info(f"Clone: File {file_id} → {share_link}")
        
    except Exception as e:
        logger.error(f"Clone file handler error: {e}")
        await message.reply(
            f"<b>❌ Eʀʀᴏʀ: {str(e)}</b>"
        )

@Client.on_message(
    filters.command(['link']) & 
    filters.private & 
    filters.create(allowed),
    group=1
)
async def clone_link_command(client: Client, message: Message):
    """Generate link for replied message"""
    
    replied = message.reply_to_message
    if not replied:
        return await message.reply(
            '<b>Rᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ɢᴇᴛ ᴀ sʜᴀʀᴇᴀʙʟᴇ ʟɪɴᴋ.</b>'
        )
    
    if not (replied.document or replied.video or replied.audio or replied.photo):
        return await message.reply(
            '<b>Pʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇᴅɪᴀ ғɪʟᴇ.</b>'
        )
    
    # Check storage
    if not (CONFIG_AVAILABLE and LOG_CHANNEL):
        return await message.reply(
            "<b>❌ Fɪʟᴇ sᴛᴏʀᴀɢᴇ ɴᴏᴛ ᴄᴏɴғɪɢᴜʀᴇᴅ!</b>"
        )
    
    try:
        bot_info = await client.get_me()
        
        # Copy to log channel
        post = await replied.copy(LOG_CHANNEL)
        file_id = str(post.id)
        
        # Generate link
        string = f'file_{file_id}'
        encoded = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
        
        if WEBSITE_URL_MODE and WEBSITE_URL:
            share_link = f"{WEBSITE_URL}?start={encoded}"
        else:
            share_link = f"https://t.me/{bot_info.username}?start={encoded}"
        
        await message.reply(
            f"<b>⭕ Hᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\n"
            f"🔗 Lɪɴᴋ: <code>{share_link}</code></b>",
            quote=True
        )
        
    except Exception as e:
        logger.error(f"Clone link command error: {e}")
        await message.reply(f"<b>❌ Eʀʀᴏʀ: {str(e)}</b>")

# Clone bot stats
@Client.on_message(filters.command("clonestats") & filters.private, group=1)
async def clone_stats(client: Client, message: Message):
    """Show clone bot statistics"""
    
    bot_info = await client.get_me()
    
    if DB_AVAILABLE:
        try:
            total_users = await db.total_users_count()
        except:
            total_users = "N/A"
    else:
        total_users = "N/A"
    
    storage_status = "✅ Cᴏɴɴᴇᴄᴛᴇᴅ" if (CONFIG_AVAILABLE and LOG_CHANNEL) else "❌ Nᴏᴛ Cᴏɴғɪɢᴜʀᴇᴅ"
    file_sharing = "✅ Pᴜʙʟɪᴄ" if PUBLIC_FILE_STORE else "❌ Rᴇsᴛʀɪᴄᴛᴇᴅ"
    
    await message.reply(
        f"<b>📊 Cʟᴏɴᴇ Bᴏᴛ Sᴛᴀᴛɪsᴛɪᴄs\n\n"
        f"🤖 Bᴏᴛ: @{bot_info.username}\n"
        f"👥 Usᴇʀs: {total_users}\n"
        f"💾 Sᴛᴏʀᴀɢᴇ: {storage_status}\n"
        f"🔗 Sʜᴀʀɪɴɢ: {file_sharing}\n\n"
        f"Sᴛᴀᴛᴜs: 🟢 Oɴʟɪɴᴇ</b>"
    )

print("✅ Clone genlink loaded - smart file handling!")
if CONFIG_AVAILABLE and LOG_CHANNEL:
    print(f"📊 Storage channel: {LOG_CHANNEL}")
else:
    print("⚠️ Storage not configured - limited functionality")
