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
    except Exception as e:
        print(f"Clone: Error getting settings - {e}")
        return {}

async def get_start_text(client, user_mention):
    """Get custom start text or default"""
    settings = await get_clone_settings(client)
    custom_text = settings.get('start_message') if settings else None
    
    # Replace {mention} placeholder
    if custom_text:
        return custom_text.replace('{mention}', user_mention)
    return DEFAULT_START_TEXT.format(user_mention)

async def get_start_keyboard(client):
    """Get keyboard for start message with custom button if set"""
    settings = await get_clone_settings(client)
    buttons = [
        [
            InlineKeyboardButton('💁‍♀️ ʜᴇʟᴘ', callback_data='clone_help'),
            InlineKeyboardButton('😊 ᴀʙᴏᴜᴛ', callback_data='clone_about')
        ]
    ]
    
    # Add custom button if set
    custom_btn = settings.get('start_button') if settings else None
    if custom_btn and ' - ' in custom_btn:
        try:
            btn_text, btn_url = custom_btn.split(' - ', 1)
            buttons.append([InlineKeyboardButton(btn_text.strip(), url=btn_url.strip())])
        except:
            pass
    
    return InlineKeyboardMarkup(buttons)

async def check_force_sub(client, user_id):
    """Check if user is subscribed to force sub channels"""
    settings = await get_clone_settings(client)
    if not settings:
        return True, None
    
    fsub_channels = settings.get('force_sub_channels', [])
    if not fsub_channels:
        return True, None
    
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
    
    # Get DB channel (where files are stored)
    db_channel = settings.get('db_channel') if settings else None
    if not db_channel:
        db_channel = LOG_CHANNEL
    
    if not db_channel:
        await message.reply("<b>❌ File storage not configured!</b>")
        return False
    
    try:
        file_msg = await client.get_messages(db_channel, file_id)
        
        if not file_msg or not file_msg.media:
            await message.reply("<b>❌ Fɪʟᴇ ɴᴏᴛ ғᴏᴜɴᴅ!</b>")
            return False
        
        # Custom caption if set
        caption = file_msg.caption
        custom_caption = settings.get('file_caption') if settings else None
        if custom_caption:
            caption = custom_caption.replace('{filename}', file_msg.document.file_name if file_msg.document else 'File')
            caption = caption.replace('{size}', str(file_msg.document.file_size) if file_msg.document else '0')
            caption = caption.replace('{caption}', file_msg.caption or '')
        
        # Check protect mode
        protect = settings.get('protect_content', False) if settings else False
        
        sent_msg = await file_msg.copy(
            chat_id=message.from_user.id,
            caption=caption,
            protect_content=protect
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
        
        # Update last used time
        if DB_LOADED:
            bot_info = await client.get_me()
            await clone_db.update_last_used(bot_info.id)
        
        return True
        
    except Exception as e:
        print(f"Clone: Error sending file - {e}")
        await message.reply(f"<b>❌ Eʀʀᴏʀ: {str(e)}</b>")
        return False

# ==================== START COMMAND ====================
@Client.on_message(filters.command("start") & filters.private, group=1)
async def clone_start(client, message):
    """Clone bot start handler"""
    print(f"Clone: Start command received from {message.from_user.id}")
    
    try:
        # Check maintenance mode
        settings = await get_clone_settings(client)
        if settings and settings.get('maintenance', False):
            return await message.reply(
                "<b>🔧 Maintenance Mode</b>\n\n"
                "Bot is under maintenance. Please try again later."
            )
        
        # Check force subscribe
        if DB_LOADED:
            is_subscribed, channels = await check_force_sub(client, message.from_user.id)
            if not is_subscribed and channels:
                buttons = []
                for channel in channels:
                    ch_name = channel.replace('@', '')
                    buttons.append([InlineKeyboardButton(f'📢 Join {ch_name}', url=f'https://t.me/{ch_name}')])
                buttons.append([InlineKeyboardButton('🔄 Try Again', callback_data='clone_start')])
                
                return await message.reply(
                    "<b>⚠️ Join Required Channels!</b>\n\n"
                    "You must join our channels to use this bot.",
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
        keyboard = await get_start_keyboard(client)
        
        # Send with photo if set
        start_photo = settings.get('start_photo') if settings else None
        if start_photo:
            try:
                await message.reply_photo(start_photo, caption=start_text, reply_markup=keyboard)
            except:
                await message.reply(start_text, reply_markup=keyboard)
        else:
            await message.reply(start_text, reply_markup=keyboard)
        
        print(f"Clone: Start message sent to {message.from_user.id}")
        
    except Exception as e:
        print(f"Clone: Error in start - {e}")
        import traceback
        traceback.print_exc()
        await message.reply("<b>❌ Error occurred!</b>")

# ==================== CALLBACKS ====================
@Client.on_callback_query(filters.regex("^clone_"))
async def clone_callbacks(client, query: CallbackQuery):
    """Handle clone bot callbacks"""
    data = query.data
    
    try:
        # Check force sub on callback
        if data == "clone_start" and DB_LOADED:
            is_subscribed, channels = await check_force_sub(client, query.from_user.id)
            if not is_subscribed and channels:
                buttons = []
                for channel in channels:
                    ch_name = channel.replace('@', '')
                    buttons.append([InlineKeyboardButton(f'📢 Join {ch_name}', url=f'https://t.me/{ch_name}')])
                buttons.append([InlineKeyboardButton('🔄 Try Again', callback_data='clone_start')])
                
                return await query.message.edit_text(
                    "<b>⚠️ Join Required Channels!</b>",
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
            keyboard = await get_start_keyboard(client)
            await query.message.edit_text(start_text, reply_markup=keyboard)
        
        await query.answer()
    except Exception as e:
        print(f"Clone: Error in callback - {e}")
        await query.answer("Error occurred!", show_alert=True)

# ==================== HELP/ABOUT COMMANDS ====================
@Client.on_message(filters.command(["help", "about"]) & filters.private, group=1)
async def clone_help_about(client, message):
    """Handle help and about commands"""
    try:
        command = message.command[0].lower()
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton('🏠 ʜᴏᴍᴇ', callback_data='clone_start')
        ]])
        
        if command == "help":
            await message.reply(HELP_TEXT, reply_markup=keyboard)
        else:
            await message.reply(ABOUT_TEXT, reply_markup=keyboard)
    except Exception as e:
        print(f"Clone: Error in help/about - {e}")

# ==================== FILE UPLOAD ====================
@Client.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.private, group=1)
async def clone_file_upload(client, message):
    """Handle file uploads in clone bot"""
    
    try:
        settings = await get_clone_settings(client)
        
        # Check maintenance mode
        if settings and settings.get('maintenance', False):
            return await message.reply("<b>🔧 Bot is under maintenance!</b>")
        
        # Check if public use is enabled
        if settings and not settings.get('public_use', True):
            bot_info = await client.get_me()
            clone = await clone_db.get_clone(bot_info.id)
            
            # Check if user is owner or admin
            admins = settings.get('admins', [])
            if message.from_user.id != clone['user_id'] and message.from_user.id not in admins:
                return await message.reply(
                    "<b>⚠️ Private Mode Active!</b>\n\n"
                    "Only owner and admins can upload files."
                )
        
        # Check file type restrictions
        allowed_types = settings.get('allowed_types', ['all']) if settings else ['all']
        if 'all' not in allowed_types:
            file_type = None
            if message.document:
                file_type = 'document'
            elif message.video:
                file_type = 'video'
            elif message.audio:
                file_type = 'audio'
            elif message.photo:
                file_type = 'photo'
            
            if file_type and file_type not in allowed_types:
                return await message.reply(f"<b>❌ {file_type.title()} files not allowed!</b>")
        
        # Check file size limit
        file_size_limit = settings.get('file_size_limit', 0) if settings else 0
        if file_size_limit > 0:
            file_size_mb = 0
            if message.document:
                file_size_mb = message.document.file_size / (1024 * 1024)
            elif message.video:
                file_size_mb = message.video.file_size / (1024 * 1024)
            
            if file_size_mb > file_size_limit:
                return await message.reply(f"<b>❌ File too large! Max: {file_size_limit}MB</b>")
        
        # Get DB channel (where files are stored)
        db_channel = settings.get('db_channel') if settings else None
        if not db_channel:
            db_channel = LOG_CHANNEL
        
        if not db_channel:
            return await message.reply("<b>❌ File storage not configured!</b>")
        
        # Copy file to DB channel
        post = await message.copy(db_channel)
        file_id = str(post.id)
        
        # Generate shareable link
        bot_username = (await client.get_me()).username
        string = f'file_{file_id}'
        encoded = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
        share_link = f"https://t.me/{bot_username}?start={encoded}"
        
        await message.reply(
            f"<b>✅ File Uploaded Successfully!\n\n"
            f"🔗 Share Link:</b>\n<code>{share_link}</code>"
        )
        
        # Update last used
        if DB_LOADED:
            bot_info = await client.get_me()
            await clone_db.update_last_used(bot_info.id)
        
    except Exception as e:
        print(f"Clone: Upload error - {e}")
        import traceback
        traceback.print_exc()
        await message.reply("<b>❌ Failed to upload file!</b>")

print("✅ Enhanced clone commands loaded with full customization support!")
