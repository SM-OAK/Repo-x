# clone_plugins/commands.py
import base64
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import UserNotParticipant

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
        if not DB_LOADED: return {}
        bot_info = await client.get_me()
        clone = await clone_db.get_clone(bot_info.id)
        return clone.get('settings', {}) if clone else {}
    except Exception as e:
        print(f"Clone: Error getting settings - {e}")
        return {}

async def get_start_text(client, user_mention):
    """Get custom start text or default"""
    settings = await get_clone_settings(client)
    custom_text = settings.get('start_message')
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
    custom_btn = settings.get('start_button')
    if custom_btn and ' - ' in custom_btn:
        try:
            btn_text, btn_url = custom_btn.split(' - ', 1)
            buttons.append([InlineKeyboardButton(btn_text.strip(), url=btn_url.strip())])
        except: pass
    return InlineKeyboardMarkup(buttons)

async def check_force_sub(client, user_id):
    """Check if user is subscribed to force sub channels"""
    settings = await get_clone_settings(client)
    if not settings: return True, None
    fsub_channels = settings.get('force_sub_channels', [])
    if not fsub_channels: return True, None
    
    not_joined = []
    for channel in fsub_channels:
        try:
            await client.get_chat_member(channel, user_id)
        except UserNotParticipant:
            not_joined.append(channel)
        except Exception:
            not_joined.append(channel)
    
    return len(not_joined) == 0, not_joined if not_joined else None

async def decode_file_id(data):
    """Decode file ID from various formats"""
    try:
        if data.startswith("file_"): return int(data[5:])
        decoded = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("ascii")
        if decoded.startswith("file_"): return int(decoded[5:])
        if "_" in decoded: _, file_id = decoded.split("_", 1); return int(file_id)
        return int(decoded)
    except: return None

async def send_file_to_user(client, message, file_id):
    """Retrieve and send file to user with custom settings"""
    settings = await get_clone_settings(client)
    db_channel = settings.get('db_channel') or LOG_CHANNEL
    if not db_channel:
        await message.reply("<b>❌ File storage not configured!</b>")
        return False
    
    try:
        file_msg = await client.get_messages(db_channel, file_id)
        if not file_msg or not file_msg.media:
            await message.reply("<b>❌ Fɪʟᴇ ɴᴏᴛ ғᴏᴜɴᴅ!</b>"); return False
        
        caption = file_msg.caption
        custom_caption = settings.get('file_caption')
        if custom_caption:
            file_name = getattr(file_msg, file_msg.media.value).file_name if getattr(file_msg, file_msg.media.value) else 'File'
            file_size = getattr(file_msg, file_msg.media.value).file_size if getattr(file_msg, file_msg.media.value) else 0
            
            caption = custom_caption.replace('{filename}', file_name)
            caption = caption.replace('{size}', str(file_size))
            caption = caption.replace('{caption}', file_msg.caption or '')
        
        protect = settings.get('protect_content', False)
        sent_msg = await file_msg.copy(message.from_user.id, caption=caption, protect_content=protect)
        
        auto_delete = settings.get('auto_delete', AUTO_DELETE_MODE)
        if auto_delete:
            delete_time = settings.get('auto_delete_time', AUTO_DELETE_TIME)
            minutes, seconds = divmod(delete_time, 60)
            time_str = f"{minutes} minute(s)" if minutes > 0 else f"{seconds} second(s)"
            
            warning = await message.reply(f"<b>⚠️ This file will be deleted in {time_str}.</b>")
            await asyncio.sleep(delete_time)
            try:
                await sent_msg.delete()
                await warning.edit_text("✅ File deleted!")
            except: pass
        
        if DB_LOADED: await clone_db.update_last_used((await client.get_me()).id)
        return True
    except Exception as e:
        print(f"Clone: Error sending file - {e}"); await message.reply(f"<b>❌ Eʀʀᴏʀ: {str(e)}</b>"); return False

# ==================== START COMMAND ====================
@Client.on_message(filters.command("start") & filters.private, group=1)
async def clone_start(client, message):
    settings = await get_clone_settings(client)
    if settings.get('maintenance', False):
        return await message.reply("<b>🔧 Bot is under maintenance. Please try again later.</b>")
    
    if DB_LOADED:
        is_subscribed, channels = await check_force_sub(client, message.from_user.id)
        if not is_subscribed:
            buttons = []
            for channel in channels:
                try:
                    chat = await client.get_chat(channel)
                    invite_link = await client.export_chat_invite_link(chat.id) if not chat.username else f"https://t.me/{chat.username}"
                    buttons.append([InlineKeyboardButton(f'📢 Join {chat.title}', url=invite_link)])
                except Exception as e: print(f"FSub Error for {channel}: {e}")
            buttons.append([InlineKeyboardButton('🔄 Try Again', callback_data='clone_start')])
            return await message.reply("<b>⚠️ You must join our channels to use this bot.</b>", reply_markup=InlineKeyboardMarkup(buttons))
    
    if len(message.command) > 1:
        file_id = await decode_file_id(message.command[1])
        if file_id:
            loading = await message.reply("<b>🔄 Fᴇᴛᴄʜɪɴɢ ғɪʟᴇ...</b>")
            success = await send_file_to_user(client, message, file_id)
            await loading.delete()
            if success: return
    
    start_text = await get_start_text(client, message.from_user.mention)
    keyboard = await get_start_keyboard(client)
    start_photo = settings.get('start_photo')
    if start_photo:
        try: await message.reply_photo(start_photo, caption=start_text, reply_markup=keyboard)
        except: await message.reply(start_text, reply_markup=keyboard)
    else: await message.reply(start_text, reply_markup=keyboard)

# ==================== CALLBACKS ====================
@Client.on_callback_query(filters.regex("^clone_"))
async def clone_callbacks(client, query: CallbackQuery):
    data = query.data
    try:
        if data == "clone_start":
            await query.answer()
            await clone_start(client, query.message) # Re-run the start logic
            return

        text, keyboard = None, None
        if data == "clone_help": text, keyboard = HELP_TEXT, InlineKeyboardMarkup([['🏠 ʜᴏᴍᴇ', 'clone_start']])
        elif data == "clone_about": text, keyboard = ABOUT_TEXT, InlineKeyboardMarkup([['🏠 ʜᴏᴍᴇ', 'clone_start']])
        
        if text: await query.message.edit_text(text, reply_markup=keyboard)
        await query.answer()
    except Exception as e: print(f"Clone: Callback error - {e}"); await query.answer("Error!", show_alert=True)

# ==================== HELP/ABOUT COMMANDS ====================
@Client.on_message(filters.command(["help", "about"]) & filters.private, group=1)
async def clone_help_about(client, message):
    command = message.command[0].lower()
    text = HELP_TEXT if command == "help" else ABOUT_TEXT
    await message.reply(text, reply_markup=InlineKeyboardMarkup([['🏠 ʜᴏᴍᴇ', 'clone_start']]))

# ==================== FILE UPLOAD ====================
@Client.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.private, group=1)
async def clone_file_upload(client, message):
    settings = await get_clone_settings(client)
    if settings.get('maintenance', False): return await message.reply("<b>🔧 Bot under maintenance!</b>")
    
    if not settings.get('public_use', True):
        clone = await clone_db.get_clone((await client.get_me()).id)
        if message.from_user.id != clone['user_id'] and message.from_user.id not in settings.get('admins', []):
            return await message.reply("<b>⚠️ Private Mode! Only owner and admins can upload.</b>")

    # --- Sudhara hua File Size Check ---
    file_size_limit_mb = settings.get('file_size_limit', 0)
    if file_size_limit_mb > 0:
        file = getattr(message, message.media.value)
        file_size_mb = file.file_size / (1024 * 1024) if file and hasattr(file, 'file_size') else 0
        if file_size_mb > file_size_limit_mb:
            return await message.reply(f"<b>❌ File too large! Max: {file_size_limit_mb}MB</b>")

    db_channel = settings.get('db_channel') or LOG_CHANNEL
    if not db_channel: return await message.reply("<b>❌ File storage not configured!</b>")
    
    try:
        post = await message.copy(db_channel)
        encoded = base64.urlsafe_b64encode(f'file_{post.id}'.encode("ascii")).decode().strip("=")
        share_link = f"https://t.me/{(await client.get_me()).username}?start={encoded}"
        await message.reply(f"<b>✅ File Uploaded!\n\n🔗 Link:</b>\n<code>{share_link}</code>")
        if DB_LOADED: await clone_db.update_last_used((await client.get_me()).id)
    except Exception as e: print(f"Clone: Upload error - {e}"); await message.reply("<b>❌ Upload Failed!</b>")

print("✅ Enhanced clone commands loaded with all corrections!")
