# clone_plugins/commands.py
import base64
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import PeerIdInvalid, ChannelInvalid, UserNotParticipant

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Import config and database with fallback ---
try:
    from config import LOG_CHANNEL, ADMINS, AUTO_DELETE_MODE, AUTO_DELETE_TIME
    CONFIG_LOADED = True
except ImportError:
    LOG_CHANNEL = None
    ADMINS = []
    AUTO_DELETE_MODE = False
    AUTO_DELETE_TIME = 1800
    CONFIG_LOADED = False
    logger.warning("config.py not found, using default values.")

try:
    from database.clone_db import clone_db
    DB_LOADED = True
except ImportError:
    DB_LOADED = False
    logger.warning("database/clone_db.py not found, database features will be disabled.")


# --- Default Texts ---
DEFAULT_START_TEXT = """<b>Hᴇʟʟᴏ {} ✨

I am a permanent file store bot. I can store private files in a specified channel and provide a shareable link.

To know more, click the Help button.</b>"""

HELP_TEXT = """<b>📚 Help Menu

How to use the bot:
1. Send me any file/video/audio.
2. I will provide you with a shareable link.
3. Users can access the files from the link after completing the necessary verifications.

It's that simple!</b>"""

ABOUT_TEXT = """<b>━━━━━━━━━━━━━━━━━━━
◈ My Name: File Store Clone
◈ Creator: @VJ_Botz
◈ Library: Pyrogram
◈ Language: Python 3
━━━━━━━━━━━━━━━━━━━</b>"""


# ==================== HELPER FUNCTIONS ====================
async def get_clone_settings(client):
    """Get settings for this specific clone bot from the database."""
    try:
        if not DB_LOADED: return {}
        bot_info = await client.get_me()
        clone = await clone_db.get_clone(bot_info.id)
        return clone.get('settings', {}) if clone else {}
    except Exception as e:
        logger.error(f"Clone: Error getting settings for bot {client.me.id}: {e}")
        return {}

async def get_start_text(client, user_mention):
    """Get custom start text from settings, or return the default."""
    settings = await get_clone_settings(client)
    custom_text = settings.get('start_message')
    if custom_text:
        return custom_text.replace('{mention}', user_mention).replace('{username}', f"@{client.me.username}")
    return DEFAULT_START_TEXT.format(user_mention)

async def get_start_keyboard(client):
    """Get the keyboard for the start message, including a custom button if set."""
    settings = await get_clone_settings(client)
    buttons = [
        [
            InlineKeyboardButton('💁‍♀️ Help', callback_data='clone_help'),
            InlineKeyboardButton('😊 About', callback_data='clone_about')
        ]
    ]
    custom_btn = settings.get('start_button')
    if custom_btn and ' - ' in custom_btn:
        try:
            btn_text, btn_url = custom_btn.split(' - ', 1)
            buttons.append([InlineKeyboardButton(btn_text.strip(), url=btn_url.strip())])
        except ValueError:
            logger.warning(f"Invalid custom button format for bot {client.me.id}")
    return InlineKeyboardMarkup(buttons)

async def check_force_sub(client, user_id):
    """Check if a user is subscribed to all required channels."""
    settings = await get_clone_settings(client)
    if not settings: return True, None
    
    fsub_channels = settings.get('force_sub_channels', [])
    if not fsub_channels: return True, None
    
    not_joined = []
    for channel_id in fsub_channels:
        try:
            await client.get_chat_member(channel_id, user_id)
        except UserNotParticipant:
            not_joined.append(channel_id)
        except (PeerIdInvalid, ChannelInvalid, ValueError):
            logger.warning(f"Invalid ForceSub channel ID: {channel_id} for bot {client.me.id}")
            continue
        except Exception as e:
            logger.error(f"Error checking ForceSub for channel {channel_id}: {e}")
            not_joined.append(channel_id)
            
    return not not_joined, not_joined or None

async def get_channel_info(client, channel_id):
    """Get a channel's title and a valid invite link."""
    try:
        chat = await client.get_chat(channel_id)
        if chat.username:
            link = f"https://t.me/{chat.username}"
        else:
            link = await client.export_chat_invite_link(chat.id)
        return link, chat.title
    except Exception as e:
        logger.error(f"Could not get info for channel {channel_id}: {e}")
        return None, "Channel"

async def decode_file_id(data):
    """Decode a file ID from a Base64 encoded string."""
    try:
        decoded_bytes = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))
        decoded_string = decoded_bytes.decode("ascii")
        if decoded_string.startswith("file_"):
            return int(decoded_string.split("_", 1)[1])
        return None
    except Exception as e:
        logger.error(f"Clone: File ID decode error - {e}")
        return None

async def send_file_to_user(client, message, file_id):
    """Retrieve a file from the database channel and send it to the user."""
    settings = await get_clone_settings(client)
    db_channel = settings.get('db_channel') or LOG_CHANNEL
    
    if not db_channel:
        await message.reply("<b>❌ File storage (DB Channel) is not configured by the admin.</b>")
        return False
    
    try:
        file_msg = await client.get_messages(db_channel, file_id)
        if not file_msg or not file_msg.media:
            await message.reply("<b>❌ File not found!</b>\nIt might have been deleted from the database.")
            return False
            
        # Get filename and size safely
        file_ref = file_msg.document or file_msg.video or file_msg.audio or file_msg.photo
        filename = getattr(file_ref, 'file_name', 'N/A')
        filesize = getattr(file_ref, 'file_size', 0)
        
        # Apply custom caption
        caption = file_msg.caption
        custom_caption = settings.get('file_caption')
        if custom_caption:
            caption = custom_caption.replace('{filename}', filename)
            caption = caption.replace('{size}', f"{filesize / (1024*1024):.2f} MB")
            caption = caption.replace('{caption}', file_msg.caption or '')

        protect = settings.get('protect_mode', False)
        
        sent_msg = await file_msg.copy(message.from_user.id, caption=caption, protect_content=protect)
        
        # Handle auto-delete
        if settings.get('auto_delete', AUTO_DELETE_MODE):
            delete_time = settings.get('auto_delete_time', AUTO_DELETE_TIME)
            minutes, seconds = divmod(delete_time, 60)
            time_str = (f"{minutes} minute(s)" if minutes else "") + (f" {seconds} second(s)" if seconds else "")
            
            warning = await message.reply(f"<b>⚠️ This file will be deleted in {time_str.strip()}. Please save it.</b>")
            await asyncio.sleep(delete_time)
            
            try:
                await sent_msg.delete()
                await warning.edit_text("✅ File deleted as per schedule.")
            except Exception: pass
            
        if DB_LOADED:
            await clone_db.update_last_used(client.me.id)
        return True
        
    except Exception as e:
        logger.error(f"Clone: Error sending file - {e}")
        await message.reply(f"<b>❌ An error occurred while sending the file.</b>")
        return False

# ==================== BOT COMMANDS & MESSAGE HANDLERS ====================
@Client.on_message(filters.command("start") & filters.private, group=1)
async def clone_start(client, message):
    settings = await get_clone_settings(client)
    if settings.get('maintenance', False):
        return await message.reply("<b>🔧 Bot is under maintenance. Please try again later.</b>")
    
    # Check Force Subscribe
    is_subscribed, channels = await check_force_sub(client, message.from_user.id)
    if not is_subscribed:
        buttons = []
        for channel_id in channels:
            link, title = await get_channel_info(client, channel_id)
            if link: buttons.append([InlineKeyboardButton(f'📢 Join {title}', url=link)])
        buttons.append([InlineKeyboardButton('🔄 Try Again', callback_data='clone_start')])
        await message.reply("<b>⚠️ You must join our channel(s) to use this bot.</b>", reply_markup=InlineKeyboardMarkup(buttons))
        return

    # Handle deep links for file access
    if len(message.command) > 1:
        file_id = await decode_file_id(message.command[1])
        if file_id:
            loading = await message.reply("<b>🔄 Fetching your file, please wait...</b>")
            await send_file_to_user(client, message, file_id)
            await loading.delete()
            return
            
    # Regular start message
    start_text = await get_start_text(client, message.from_user.mention)
    keyboard = await get_start_keyboard(client)
    start_photo = settings.get('start_photo')
    
    if start_photo:
        try:
            await message.reply_photo(start_photo, caption=start_text, reply_markup=keyboard)
        except Exception:
            await message.reply(start_text, reply_markup=keyboard, disable_web_page_preview=True)
    else:
        await message.reply(start_text, reply_markup=keyboard, disable_web_page_preview=True)

@Client.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.private, group=1)
async def clone_file_upload(client, message):
    settings = await get_clone_settings(client)
    if settings.get('maintenance', False):
        return await message.reply("<b>🔧 Bot is under maintenance. File uploads are temporarily disabled.</b>")
    
    # Check if user is authorized for private bots
    if not settings.get('public_use', True):
        clone = await clone_db.get_clone(client.me.id)
        admins = settings.get('admins', [])
        if message.from_user.id not in [clone['user_id']] + admins:
            return await message.reply("<b>⚠️ This is a private bot. Only the owner and authorized admins can upload files.</b>")
            
    # Get DB channel
    db_channel = settings.get('db_channel') or LOG_CHANNEL
    if not db_channel:
        return await message.reply("<b>❌ File storage is not configured. Please contact the bot owner.</b>")

    status_msg = await message.reply("<b>📤 Uploading file to database...</b>")
    
    try:
        post = await message.copy(db_channel)
        file_id = str(post.id)
        encoded = base64.urlsafe_b64encode(f"file_{file_id}".encode("ascii")).decode().strip("=")
        share_link = f"https://t.me/{client.me.username}?start={encoded}"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Open Shareable Link", url=share_link)],
            [InlineKeyboardButton("📋 Copy Link", callback_data=f"copy_{encoded}")]
        ])
        
        await status_msg.edit_text(
            f"<b>✅ File Uploaded Successfully!</b>\n\n"
            f"🔗 Your shareable link is ready:\n<code>{share_link}</code>",
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
        
        if DB_LOADED:
            await clone_db.update_last_used(client.me.id)
            
    except Exception as e:
        logger.error(f"Clone: Upload error - {e}")
        await status_msg.edit_text("<b>❌ Failed to upload file due to a server error.</b>")

@Client.on_message(filters.command(["help", "about"]) & filters.private, group=1)
async def clone_help_about(client, message):
    command = message.command[0].lower()
    text = HELP_TEXT if command == "help" else ABOUT_TEXT
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('🏠 Home', callback_data='clone_start')]])
    await message.reply(text, reply_markup=keyboard, disable_web_page_preview=True)

# ==================== CALLBACK HANDLERS ====================
@Client.on_callback_query(filters.regex("^clone_"))
async def clone_callbacks(client, query: CallbackQuery):
    data = query.data
    
    if data == "clone_start":
        await query.answer()
        is_subscribed, channels = await check_force_sub(client, query.from_user.id)
        if not is_subscribed:
            buttons = []
            for channel_id in channels:
                link, title = await get_channel_info(client, channel_id)
                if link: buttons.append([InlineKeyboardButton(f'📢 Join {title}', url=link)])
            buttons.append([InlineKeyboardButton('🔄 Try Again', callback_data='clone_start')])
            return await query.message.edit_text("<b>⚠️ Please join our channel(s) first.</b>", reply_markup=InlineKeyboardMarkup(buttons))
        
        start_text = await get_start_text(client, query.from_user.mention)
        keyboard = await get_start_keyboard(client)
        await query.message.edit_text(start_text, reply_markup=keyboard, disable_web_page_preview=True)
        
    elif data == "clone_help":
        await query.answer()
        await query.message.edit_text(HELP_TEXT, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🏠 Home', callback_data='clone_start')]]))
        
    elif data == "clone_about":
        await query.answer()
        await query.message.edit_text(ABOUT_TEXT, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🏠 Home', callback_data='clone_start')]]))

@Client.on_callback_query(filters.regex("^copy_"))
async def copy_link_callback(client, query: CallbackQuery):
    encoded = query.data.split("_", 1)[1]
    share_link = f"https://t.me/{client.me.username}?start={encoded}"
    await query.answer(f"Link copied!\n\n{share_link}", show_alert=True)


logger.info("✅ Clone bot commands module loaded successfully!")
