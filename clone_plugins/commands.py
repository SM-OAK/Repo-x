# clone_plugins/commands.py
import base64
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Import config and database with fallback
try:
    from config import LOG_CHANNEL, ADMINS, AUTO_DELETE_MODE, AUTO_DELETE_TIME
    CONFIG_LOADED = True
except:
    LOG_CHANNEL = None
    ADMINS = []
    AUTO_DELETE_MODE = False
    AUTO_DELETE_TIME = 1800
    CONFIG_LOADED = False

try:
    from database.clone_db import clone_db
    DB_LOADED = True
except:
    DB_LOADED = False

# User states for multi-step processes
user_states = {}

# Default texts
DEFAULT_START_TEXT = """<b>Hᴇʟʟᴏ {} ✨

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

async def get_clone_settings(client):
    """Get settings for this clone bot"""
    try:
        if not DB_LOADED:
            return None
        bot_info = await client.get_me()
        clone = await clone_db.get_clone(bot_info.id)
        return clone.get('settings', {}) if clone else {}
    except:
        return {}

async def get_start_text(client, user_mention):
    """Get custom start text or default"""
    settings = await get_clone_settings(client)
    custom_text = settings.get('start_message') if settings else None
    return custom_text if custom_text else DEFAULT_START_TEXT.format(user_mention)

def get_start_keyboard():
    """Get keyboard for start message"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('💁‍♀️ ʜᴇʟᴘ', callback_data='clone_help'),
            InlineKeyboardButton('😊 ᴀʙᴏᴜᴛ', callback_data='clone_about')
        ]
    ])

async def check_force_sub(client, user_id):
    """Check if user is subscribed to force sub channels"""
    settings = await get_clone_settings(client)
    if not settings:
        return True
    
    fsub_channels = settings.get('force_sub_channels', [])
    if not fsub_channels:
        return True
    
    not_joined = []
    for channel in fsub_channels:
        try:
            member = await client.get_chat_member(channel, user_id)
            if member.status in ['left', 'kicked']:
                not_joined.append(channel)
        except:
            not_joined.append(channel)
    
    return len(not_joined) == 0, not_joined if not_joined else None

async def decode_file_id(data):
    """Decode file ID from various formats"""
    try:
        if data.startswith("file_"):
            return int(data[5:])
        
        decoded = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("ascii")
        
        if decoded.startswith("file_"):
            return int(decoded[5:])
        
        if "_" in decoded:
            _, file_id = decoded.split("_", 1)
            return int(file_id)
        
        return int(decoded)
    except Exception as e:
        print(f"Clone: Decode error - {e}")
        return None

async def send_file_to_user(client, message, file_id):
    """Retrieve and send file to user with custom settings"""
    settings = await get_clone_settings(client)
    
    # Get log channel (custom or default)
    log_channel = settings.get('log_channel') if settings else None
    if not log_channel:
        log_channel = LOG_CHANNEL
    
    if not log_channel:
        return False
    
    try:
        file_msg = await client.get_messages(log_channel, file_id)
        
        if not file_msg or not file_msg.media:
            await message.reply("<b>❌ Fɪʟᴇ ɴᴏᴛ ғᴏᴜɴᴅ!</b>")
            return False
        
        sent_msg = await file_msg.copy(
            chat_id=message.from_user.id,
            caption=file_msg.caption
        )
        
        # Auto-delete based on settings
        auto_delete = settings.get('auto_delete', AUTO_DELETE_MODE) if settings else AUTO_DELETE_MODE
        delete_time = settings.get('auto_delete_time', AUTO_DELETE_TIME) if settings else AUTO_DELETE_TIME
        
        if auto_delete:
            minutes = delete_time // 60
            seconds = delete_time % 60
            time_str = f"{minutes} minutes" if minutes > 0 else f"{seconds} seconds"
            
            warning = await message.reply(
                f"<b>⚠️ IMPORTANT</b>\n\n"
                f"This file will be deleted in <b>{time_str}</b>.\n"
                f"Please forward to Saved Messages!"
            )
            
            await asyncio.sleep(delete_time)
            
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

# ==================== START COMMAND ====================
@Client.on_message(filters.command("start") & filters.private, group=1)
async def clone_start(client, message):
    """Clone bot start handler"""
    
    # Check force subscribe
    if DB_LOADED:
        is_subscribed, channels = await check_force_sub(client, message.from_user.id)
        if not is_subscribed and channels:
            buttons = []
            for channel in channels:
                buttons.append([InlineKeyboardButton(f'📢 Join Channel', url=f'https://t.me/{channel.replace("@", "")}')])
            buttons.append([InlineKeyboardButton('🔄 Try Again', callback_data='clone_start')])
            
            return await message.reply(
                "<b>⚠️ You must join our channels to use this bot!</b>\n\n"
                "Click the buttons below to join, then click 'Try Again'.",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    
    # Handle file access parameter
    if len(message.command) > 1:
        parameter = message.command[1]
        file_id = await decode_file_id(parameter)
        
        if file_id:
            print(f"Clone: Handling file access for ID {file_id}")
            loading = await message.reply("<b>🔄 Fᴇᴛᴄʜɪɴɢ ғɪʟᴇ...</b>")
            
            success = await send_file_to_user(client, message, file_id)
            
            try:
                await loading.delete()
            except:
                pass
            
            if success:
                return
    
    # Regular start message with custom text
    start_text = await get_start_text(client, message.from_user.mention)
    await message.reply(start_text, reply_markup=get_start_keyboard())

# ==================== CALLBACKS ====================
@Client.on_callback_query(filters.regex("^clone_"))
async def clone_callbacks(client, query: CallbackQuery):
    """Handle clone bot callbacks"""
    data = query.data
    
    # Check force sub on callback
    if data == "clone_start" and DB_LOADED:
        is_subscribed, channels = await check_force_sub(client, query.from_user.id)
        if not is_subscribed and channels:
            buttons = []
            for channel in channels:
                buttons.append([InlineKeyboardButton(f'📢 Join Channel', url=f'https://t.me/{channel.replace("@", "")}')])
            buttons.append([InlineKeyboardButton('🔄 Try Again', callback_data='clone_start')])
            
            return await query.message.edit_text(
                "<b>⚠️ You must join our channels to use this bot!</b>",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    
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
        start_text = await get_start_text(client, query.from_user.mention)
        await query.message.edit_text(start_text, reply_markup=get_start_keyboard())
    
    await query.answer()

# ==================== HELP/ABOUT COMMANDS ====================
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

# ==================== FILE UPLOAD ====================
@Client.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.private, group=1)
async def clone_file_upload(client, message):
    """Handle file uploads in clone bot"""
    
    settings = await get_clone_settings(client)
    
    # Check if public use is enabled
    if settings and not settings.get('public_use', True):
        bot_info = await client.get_me()
        clone = await clone_db.get_clone(bot_info.id)
        
        # Check if user is owner or admin
        admins = settings.get('admins', [])
        if message.from_user.id != clone['user_id'] and message.from_user.id not in admins:
            return await message.reply(
                "<b>⚠️ This bot is in private mode!</b>\n\n"
                "Only the owner and admins can upload files."
            )
    
    # Get log channel
    log_channel = settings.get('log_channel') if settings else None
    if not log_channel:
        log_channel = LOG_CHANNEL
    
    if not log_channel:
        return await message.reply(
            "<b>❌ Fɪʟᴇ sᴛᴏʀᴀɢᴇ ɴᴏᴛ ᴄᴏɴғɪɢᴜʀᴇᴅ!</b>"
        )
    
    try:
        post = await message.copy(log_channel)
        file_id = str(post.id)
        
        bot_username = (await client.get_me()).username
        string = f'file_{file_id}'
        encoded = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
        share_link = f"https://t.me/{bot_username}?start={encoded}"
        
        await message.reply(
            f"<b>⭕ Hᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\n"
            f"🔗 Lɪɴᴋ: {share_link}</b>"
        )
        
    except Exception as e:
        print(f"Clone: Upload error - {e}")
        await message.reply("<b>❌ Fᴀɪʟᴇᴅ ᴛᴏ ɢᴇɴᴇʀᴀᴛᴇ ʟɪɴᴋ!</b>")

print("✅ Enhanced clone commands loaded with customization features!")
