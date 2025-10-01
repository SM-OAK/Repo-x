# clone_plugins/commands.py
import base64
import asyncio
import logging

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserNotParticipant, ChatAdminRequired

logger = logging.getLogger(__name__)

# ───────────────────────────────
# Local project imports
# ───────────────────────────────
try:
    from database.clone_db import clone_db
    DB_LOADED = True
except ImportError:
    DB_LOADED = False
    logger.error("Clone DB not loaded!")

# ───────────────────────────────
# Default texts
# ───────────────────────────────
START_TEXT = """<b>Hᴇʟʟᴏ {} ✨

I ᴀᴍ ᴀ ᴘᴇʀᴍᴀɴᴇɴᴛ ғɪʟᴇ sᴛᴏʀᴇ ʙᴏᴛ. Usᴇʀs ᴄᴀɴ ᴀᴄᴄᴇss ғɪʟᴇs ʙʏ ᴜsɪɴɢ ᴀ sʜᴀʀᴇᴀʙʟᴇ ʟɪɴᴋ.

Tᴏ ᴋɴᴏᴡ ᴍᴏʀᴇ, ᴄʟɪᴄᴋ ᴛʜᴇ ʜᴇʟᴘ ʙᴜᴛᴛᴏɴ.</b>"""

HELP_TEXT = """<b>📚 Hᴇʟᴘ Mᴇɴᴜ

🔹 Sᴇɴᴅ ᴍᴇ ᴀɴʏ ғɪʟᴇ/ᴠɪᴅᴇᴏ/ᴘʜᴏᴛᴏ
🔹 I ᴡɪʟʟ ɢɪᴠᴇ ʏᴏᴜ ᴀ sʜᴀʀᴇᴀʙʟᴇ ʟɪɴᴋ
🔹 Aɴʏᴏɴᴇ ᴄᴀɴ ᴀᴄᴄᴇss ғɪʟᴇs ғʀᴏᴍ ᴛʜᴇ ʟɪɴᴋ

💡 Jᴜsᴛ sᴇɴᴅ ᴍᴇ ᴀɴʏ ғɪʟᴇ ᴛᴏ ɢᴇᴛ sᴛᴀʀᴛᴇᴅ!</b>"""

ABOUT_TEXT = """<b>━━━━━━━━━━━━━━━━━━━
◈ Mʏ Nᴀᴍᴇ: Fɪʟᴇ Sᴛᴏʀᴇ Cʟᴏɴᴇ
◈ Cʀᴇᴀᴛᴏʀ: @VJ_Botz
◈ Lɪʙʀᴀʀʏ: Pʏʀᴏɢʀᴀᴍ
◈ Lᴀɴɢᴜᴀɢᴇ: Pʏᴛʜᴏɴ 3
━━━━━━━━━━━━━━━━━━━</b>"""

def get_start_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('💁‍♀️ ʜᴇʟᴘ', callback_data='clone_help'),
         InlineKeyboardButton('😊 ᴀʙᴏᴜᴛ', callback_data='clone_about')]
    ])

# ───────────────────────────────
# Helper functions
# ───────────────────────────────
async def get_clone_data(bot_id):
    """Get complete clone data from database"""
    if not DB_LOADED:
        logger.error("Database not loaded")
        return None
    
    try:
        clone = await clone_db.get_clone(bot_id)
        if not clone:
            logger.error(f"Clone not found for bot_id: {bot_id}")
            return None
        
        # Update last used timestamp
        await clone_db.update_last_used(bot_id)
        
        return clone
    except Exception as e:
        logger.error(f"Error getting clone data: {e}")
        return None

async def get_clone_settings(clone_data):
    """Extract settings from clone data"""
    if not clone_data:
        return {}
    return clone_data.get('settings', {})

async def get_log_channel(clone_data):
    """Get log channel from clone settings or db_channel"""
    if not clone_data:
        return None
    
    settings = clone_data.get('settings', {})
    
    # First check db_channel (where files are stored)
    db_channel = settings.get('db_channel')
    if db_channel:
        return db_channel
    
    # Fallback to log_channel
    log_channel = settings.get('log_channel')
    if log_channel:
        return log_channel
    
    return None

async def is_user_admin(clone_data, user_id):
    """Check if user is admin or owner"""
    if not clone_data:
        return False
    
    owner_id = clone_data.get('user_id')
    settings = clone_data.get('settings', {})
    admins = settings.get('admins', [])
    
    return user_id == owner_id or user_id in admins

async def check_user_subscription(client, user_id, channels):
    """Check if user is subscribed to all force sub channels"""
    if not channels:
        return True, []
    
    not_joined = []
    
    for channel in channels:
        try:
            # Get chat member status
            member = await client.get_chat_member(channel, user_id)
            # Check if user is member, admin, or creator
            if member.status not in ["member", "administrator", "creator"]:
                not_joined.append(channel)
        except UserNotParticipant:
            not_joined.append(channel)
        except ChatAdminRequired:
            logger.warning(f"Bot is not admin in {channel}")
            continue
        except Exception as e:
            logger.error(f"Error checking subscription for {channel}: {e}")
            continue
    
    return len(not_joined) == 0, not_joined

async def generate_force_sub_buttons(not_joined_channels):
    """Generate buttons for channels user needs to join"""
    buttons = []
    
    for idx, channel in enumerate(not_joined_channels, 1):
        # Format channel name for button
        if channel.startswith('@'):
            channel_username = channel[1:]
            button_text = f"📢 Join Channel {idx}"
            invite_link = f"https://t.me/{channel_username}"
        elif channel.startswith('-100'):
            button_text = f"📢 Join Channel {idx}"
            # For private channels, you need to generate invite link
            invite_link = f"https://t.me/c/{channel[4:]}/1"
        else:
            button_text = f"📢 Join Channel {idx}"
            invite_link = f"https://t.me/{channel}"
        
        buttons.append([InlineKeyboardButton(button_text, url=invite_link)])
    
    # Add "Try Again" button
    buttons.append([InlineKeyboardButton("✅ I Joined, Try Again", callback_data="check_fsub")])
    
    return InlineKeyboardMarkup(buttons)

async def decode_file_id(data):
    """Decode file ID from base64"""
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
        logger.error(f"Decode error: {e}")
        return None

async def send_file_to_user(client, message, file_id, clone_data):
    """Send file to user with auto-delete if enabled"""
    
    log_channel = await get_log_channel(clone_data)
    
    if not log_channel:
        await message.reply("<b>❌ Fɪʟᴇ sᴛᴏʀᴀɢᴇ ɴᴏᴛ ᴄᴏɴғɪɢᴜʀᴇᴅ!</b>")
        return False
    
    try:
        # Get file from log/db channel
        file_msg = await client.get_messages(log_channel, file_id)
        
        if not file_msg or not file_msg.media:
            await message.reply("<b>❌ Fɪʟᴇ ɴᴏᴛ ғᴏᴜɴᴅ!</b>")
            return False
        
        settings = await get_clone_settings(clone_data)
        protect_content = settings.get('no_forward', False)
        
        # Send file to user
        sent_msg = await file_msg.copy(
            chat_id=message.from_user.id,
            caption=file_msg.caption,
            protect_content=protect_content
        )
        
        # Auto delete functionality
        auto_delete = settings.get('auto_delete', False)
        auto_delete_time = settings.get('auto_delete_time', 300)
        
        if auto_delete:
            minutes = auto_delete_time // 60
            seconds = auto_delete_time % 60
            time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
            
            warning = await message.reply(
                f"<b>⚠️ IMPORTANT</b>\n\n"
                f"This file will be automatically deleted in <b>{time_str}</b>.\n"
                f"Please save it to your Saved Messages if needed!"
            )
            
            await asyncio.sleep(auto_delete_time)
            
            try:
                await sent_msg.delete()
                await warning.edit_text("✅ File has been deleted as per auto-delete settings!")
            except Exception as e:
                logger.error(f"Error deleting file: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error sending file: {e}")
        await message.reply(f"<b>❌ Eʀʀᴏʀ: {str(e)}</b>")
        return False

async def log_to_channel(client, clone_data, message_text):
    """Log activity to log channel"""
    settings = await get_clone_settings(clone_data)
    log_channel = settings.get('log_channel')
    
    if log_channel:
        try:
            await client.send_message(log_channel, message_text)
        except Exception as e:
            logger.error(f"Error logging to channel: {e}")

# ───────────────────────────────
# Command Handlers
# ───────────────────────────────
@Client.on_message(filters.command("start") & filters.private, group=1)
async def clone_start(client, message):
    """Handle /start command"""
    bot_info = await client.get_me()
    bot_id = bot_info.id
    
    # Get clone data from database
    clone_data = await get_clone_data(bot_id)
    
    if not clone_data:
        return await message.reply("<b>❌ Cʟᴏɴᴇ ɴᴏᴛ ғᴏᴜɴᴅ ɪɴ ᴅᴀᴛᴀʙᴀsᴇ!</b>")
    
    settings = await get_clone_settings(clone_data)
    
    # Add user to clone users
    if DB_LOADED:
        await clone_db.add_clone_user(bot_id, message.from_user.id)
    
    # Handle file request
    if len(message.command) > 1:
        parameter = message.command[1]
        file_id = await decode_file_id(parameter)
        
        if file_id:
            # Check force subscription for all channels
            force_sub_channels = settings.get('force_sub_channels', [])
            
            if force_sub_channels:
                is_subscribed, not_joined = await check_user_subscription(
                    client, 
                    message.from_user.id, 
                    force_sub_channels
                )
                
                if not is_subscribed:
                    buttons = await generate_force_sub_buttons(not_joined)
                    return await message.reply(
                        f"<b>⚠️ YOU MUST JOIN ALL CHANNELS TO USE THIS BOT!</b>\n\n"
                        f"Please join the following channels and try again:",
                        reply_markup=buttons
                    )
            
            # Send file if subscribed
            loading = await message.reply("<b>🔄 Fᴇᴛᴄʜɪɴɢ ғɪʟᴇ...</b>")
            success = await send_file_to_user(client, message, file_id, clone_data)
            
            try: 
                await loading.delete()
            except: 
                pass
            
            if success:
                # Log file access
                await log_to_channel(
                    client, 
                    clone_data,
                    f"📥 <b>File Accessed</b>\n\n"
                    f"👤 User: {message.from_user.mention}\n"
                    f"🆔 ID: <code>{message.from_user.id}</code>\n"
                    f"📄 File ID: <code>{file_id}</code>"
                )
                return
    
    # Normal start message
    start_message = settings.get('start_message')
    start_photo = settings.get('start_photo')
    start_button = settings.get('start_button')
    
    text = start_message if start_message else START_TEXT.format(message.from_user.mention)
    
    # Prepare keyboard
    keyboard = get_start_keyboard()
    
    # Add custom start button if available
    if start_button:
        custom_btn = [[InlineKeyboardButton(start_button['text'], url=start_button['url'])]]
        keyboard.inline_keyboard = custom_btn + keyboard.inline_keyboard
    
    # Send message with photo or text
    if start_photo:
        try:
            await message.reply_photo(
                photo=start_photo, 
                caption=text, 
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
            await message.reply(text, reply_markup=keyboard)
    else:
        await message.reply(text, reply_markup=keyboard)

@Client.on_callback_query(filters.regex("^clone_"))
async def clone_callbacks(client, query: CallbackQuery):
    """Handle clone callback queries"""
    data = query.data
    bot_info = await client.get_me()
    bot_id = bot_info.id
    
    clone_data = await get_clone_data(bot_id)
    
    if not clone_data:
        return await query.answer("❌ Clone not found!", show_alert=True)
    
    settings = await get_clone_settings(clone_data)
    
    start_message = settings.get('start_message')
    start_photo = settings.get('start_photo')
    start_button = settings.get('start_button')
    
    text = start_message if start_message else START_TEXT.format(query.from_user.mention)
    
    # Prepare keyboard
    keyboard = get_start_keyboard()
    
    # Add custom start button if available
    if start_button:
        custom_btn = [[InlineKeyboardButton(start_button['text'], url=start_button['url'])]]
        keyboard.inline_keyboard = custom_btn + keyboard.inline_keyboard
    
    if data == "clone_help":
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('🏠 ʜᴏᴍᴇ', callback_data='clone_start')]])
        await query.message.edit_text(HELP_TEXT, reply_markup=keyboard)
    
    elif data == "clone_about":
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('🏠 ʜᴏᴍᴇ', callback_data='clone_start')]])
        await query.message.edit_text(ABOUT_TEXT, reply_markup=keyboard)
    
    elif data == "clone_start":
        try:
            if start_photo:
                await query.message.delete()
                await client.send_photo(
                    chat_id=query.message.chat.id, 
                    photo=start_photo, 
                    caption=text,
                    reply_markup=keyboard
                )
            else:
                await query.message.edit_text(text, reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Error in callback: {e}")
            await query.message.edit_text(text, reply_markup=keyboard)
    
    await query.answer()

@Client.on_callback_query(filters.regex("^check_fsub"))
async def check_fsub_callback(client, query: CallbackQuery):
    """Handle force sub check callback"""
    bot_info = await client.get_me()
    bot_id = bot_info.id
    
    clone_data = await get_clone_data(bot_id)
    
    if not clone_data:
        return await query.answer("❌ Clone not found!", show_alert=True)
    
    settings = await get_clone_settings(clone_data)
    force_sub_channels = settings.get('force_sub_channels', [])
    
    if not force_sub_channels:
        await query.answer("No force subscription required!", show_alert=True)
        return
    
    is_subscribed, not_joined = await check_user_subscription(
        client, 
        query.from_user.id, 
        force_sub_channels
    )
    
    if is_subscribed:
        await query.answer("✅ Verified! Now send the command again.", show_alert=True)
        await query.message.delete()
    else:
        await query.answer(
            f"❌ You still need to join {len(not_joined)} channel(s)!", 
            show_alert=True
        )

@Client.on_message(filters.command(["help", "about"]) & filters.private, group=1)
async def clone_help_about(client, message):
    """Handle help and about commands"""
    command = message.command[0].lower()
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('🏠 ʜᴏᴍᴇ', callback_data='clone_start')]])
    
    if command == "help":
        await message.reply(HELP_TEXT, reply_markup=keyboard)
    else:
        await message.reply(ABOUT_TEXT, reply_markup=keyboard)

@Client.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.private, group=1)
async def clone_file_upload(client, message):
    """Handle file uploads"""
    bot_info = await client.get_me()
    bot_id = bot_info.id
    
    # Get clone data
    clone_data = await get_clone_data(bot_id)
    
    if not clone_data:
        return await message.reply("<b>❌ Cʟᴏɴᴇ ɴᴏᴛ ғᴏᴜɴᴅ!</b>")
    
    # Get log channel
    log_channel = await get_log_channel(clone_data)
    
    if not log_channel:
        return await message.reply("<b>❌ Fɪʟᴇ sᴛᴏʀᴀɢᴇ ɴᴏᴛ ᴄᴏɴғɪɢᴜʀᴇᴅ!</b>")
    
    settings = await get_clone_settings(clone_data)
    
    # Check public/private mode
    public_use = settings.get('public_use', True)
    
    if not public_use:
        if not await is_user_admin(clone_data, message.from_user.id):
            return await message.reply(
                "<b>⚠️ This bot is in private mode!</b>\n"
                "Only owner and admins can upload files."
            )
    
    try:
        processing = await message.reply("<b>⏳ Pʀᴏᴄᴇssɪɴɢ ʏᴏᴜʀ ғɪʟᴇ...</b>")
        
        # Copy to log/db channel
        post = await message.copy(log_channel)
        file_id = str(post.id)
        
        # Generate share link
        bot_username = bot_info.username
        string = f'file_{file_id}'
        encoded = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
        share_link = f"https://t.me/{bot_username}?start={encoded}"
        
        await processing.delete()
        
        buttons = [
            [InlineKeyboardButton('🔗 Sʜᴀʀᴇ Lɪɴᴋ', url=share_link)],
            [InlineKeyboardButton('📋 Cᴏᴘʏ Lɪɴᴋ', callback_data='clone_start')]
        ]
        
        # Get file info
        file_name = "Unknown"
        if message.document:
            file_name = message.document.file_name
        elif message.video:
            file_name = message.video.file_name or "Video"
        elif message.audio:
            file_name = message.audio.file_name or message.audio.title or "Audio"
        elif message.photo:
            file_name = "Photo"
        
        await message.reply(
            f"<b>✅ Fɪʟᴇ Sᴛᴏʀᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ!</b>\n\n"
            f"📄 <b>File:</b> <code>{file_name}</code>\n"
            f"🔗 <b>Sʜᴀʀᴇᴀʙʟᴇ Lɪɴᴋ:</b>\n<code>{share_link}</code>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        
        # Log to log channel
        await log_to_channel(
            client,
            clone_data,
            f"📤 <b>New File Uploaded</b>\n\n"
            f"👤 User: {message.from_user.mention}\n"
            f"🆔 ID: <code>{message.from_user.id}</code>\n"
            f"📄 File: <code>{file_name}</code>\n"
            f"🔗 Link: <code>{share_link}</code>"
        )
                
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await clone_file_upload(client, message)
    except Exception as e:
        logger.error(f"Upload error: {e}")
        await message.reply(
            f"<b>❌ Fᴀɪʟᴇᴅ ᴛᴏ ɢᴇɴᴇʀᴀᴛᴇ ʟɪɴᴋ!</b>\n"
            f"Error: <code>{str(e)}</code>"
        )

@Client.on_message(filters.command("batch") & filters.private, group=1)
async def batch_handler(client, message):
    """Handle batch file uploads"""
    bot_info = await client.get_me()
    bot_id = bot_info.id
    
    clone_data = await get_clone_data(bot_id)
    
    if not clone_data:
        return await message.reply("<b>❌ Cʟᴏɴᴇ ɴᴏᴛ ғᴏᴜɴᴅ!</b>")
    
    # Check admin access
    if not await is_user_admin(clone_data, message.from_user.id):
        return await message.reply("<b>⚠️ Only admins/owner can use this command!</b>")

    # Start batch upload mode
    await message.reply(
        "<b>📦 Bᴀᴛᴄʜ Uᴘʟᴏᴀᴅ Mᴏᴅᴇ</b>\n\n"
        "Forward multiple files from a channel or chat.\n"
        "Send /done when finished."
    )

logger.info("✅ Clone commands module loaded with database integration")
