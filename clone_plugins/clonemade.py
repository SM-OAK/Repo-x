# -*- coding: utf-8 -*-
# clone_plugins/clonemade.py
import base64
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import PeerIdInvalid, ChannelInvalid, UserNotParticipant

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from config import LOG_CHANNEL, ADMINS, AUTO_DELETE_MODE, AUTO_DELETE_TIME
    CONFIG_LOADED = True
except ImportError:
    LOG_CHANNEL = None
    ADMINS = []
    AUTO_DELETE_MODE = False
    AUTO_DELETE_TIME = 1800
    CONFIG_LOADED = False
    logger.warning("config.py not found, using defaults.")

try:
    from database.clone_db import clone_db
    DB_LOADED = True
except ImportError:
    DB_LOADED = False
    logger.warning("database/clone_db.py not found.")

# Default texts
DEFAULT_START_TEXT = """<b>Hello {} ✨

I am a file store bot. Send me files and I'll give you shareable links!

Click Help to learn more.</b>"""

HELP_TEXT = """<b>📚 How to Use:

1️⃣ Send any file/video/audio
2️⃣ Get a shareable link
3️⃣ Share with anyone!

<b>📦 Batch Commands:</b>
• /batch - Manual batch (collect files)
• /genbatch - Quick batch (from channel)
• /done - Finish manual batch
• /cancel - Cancel batch</b>"""

ABOUT_TEXT = """<b>━━━━━━━━━━━━━━━━━━━
◈ File Store Clone Bot
◈ Creator: @VJ_Botz
◈ Library: Pyrogram
◈ Language: Python 3
━━━━━━━━━━━━━━━━━━━</b>"""

# Batch storage
batch_data = {}

# ==================== HELPER FUNCTIONS ====================
async def get_clone_settings(client):
    """Get clone settings from database."""
    if not DB_LOADED:
        return {}
    try:
        bot_info = await client.get_me()
        clone = await clone_db.get_clone(bot_info.id)
        return clone.get('settings', {}) if clone else {}
    except Exception as e:
        logger.error(f"Settings error: {e}")
        return {}

async def get_start_text(client, user_mention):
    """Get custom or default start text."""
    settings = await get_clone_settings(client)
    custom = settings.get('start_message')
    if custom:
        return custom.replace('{mention}', user_mention).replace('{username}', f"@{client.me.username}")
    return DEFAULT_START_TEXT.format(user_mention)

async def get_start_keyboard(client):
    """Build start keyboard with optional custom button."""
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
            text, url = custom_btn.split(' - ', 1)
            buttons.append([InlineKeyboardButton(text.strip(), url=url.strip())])
        except ValueError:
            pass
    return InlineKeyboardMarkup(buttons)

async def check_force_sub(client, user_id):
    """Check force subscription status."""
    settings = await get_clone_settings(client)
    if not settings:
        return True, None
    
    fsub = settings.get('force_sub_channels', [])
    if not fsub:
        return True, None
    
    not_joined = []
    for ch in fsub:
        ch_id = int(ch.get('id') if isinstance(ch, dict) else ch)
        try:
            await client.get_chat_member(ch_id, user_id)
        except UserNotParticipant:
            not_joined.append(ch_id)
        except Exception as e:
            logger.error(f"ForceSub check error for {ch_id}: {e}")
            
    return not not_joined, not_joined or None

async def get_channel_info(client, ch_id):
    """Get channel title and invite link."""
    try:
        chat = await client.get_chat(ch_id)
        link = f"https://t.me/{chat.username}" if chat.username else await client.export_chat_invite_link(chat.id)
        return link, chat.title
    except Exception as e:
        logger.error(f"Channel info error for {ch_id}: {e}")
        return None, "Channel"

def decode_file_id(data):
    """Decode Base64 file ID."""
    try:
        decoded = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("ascii")
        return int(decoded.split("_", 1)[1]) if decoded.startswith("file_") else None
    except Exception as e:
        logger.error(f"Decode error: {e}")
        return None

def encode_file_id(file_id):
    """Encode file ID to Base64."""
    return base64.urlsafe_b64encode(f"file_{file_id}".encode("ascii")).decode().strip("=")

def encode_batch_range(first_id, last_id):
    """Encode batch range to Base64."""
    return base64.urlsafe_b64encode(f"batch_{first_id}_{last_id}".encode("ascii")).decode().strip("=")

def decode_batch_range(data):
    """Decode batch range from Base64."""
    try:
        decoded = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("ascii")
        if decoded.startswith("batch_"):
            parts = decoded.split("_")
            return int(parts[1]), int(parts[2])
        return None, None
    except Exception as e:
        logger.error(f"Batch decode error: {e}")
        return None, None

async def send_file(client, msg, file_id):
    """Send file from DB channel to user."""
    settings = await get_clone_settings(client)
    db_ch = settings.get('db_channel') or LOG_CHANNEL
    
    if not db_ch:
        await msg.reply("<b>❌ DB Channel not configured!</b>")
        return False
    
    try:
        file_msg = await client.get_messages(db_ch, file_id)
        if not file_msg or not file_msg.media:
            return False
        
        # Get file details
        media = file_msg.document or file_msg.video or file_msg.audio or file_msg.photo
        filename = getattr(media, 'file_name', 'N/A')
        filesize = getattr(media, 'file_size', 0)
        
        # Custom caption
        caption = file_msg.caption
        custom_cap = settings.get('file_caption')
        if custom_cap:
            caption = custom_cap.replace('{filename}', filename)
            caption = caption.replace('{size}', f"{filesize / (1024*1024):.2f} MB")
            caption = caption.replace('{caption}', file_msg.caption or '')
        
        # Send with protection
        protect = settings.get('protect_mode', False)
        sent = await file_msg.copy(msg.from_user.id, caption=caption, protect_content=protect)
        
        # Auto-delete
        if settings.get('auto_delete', AUTO_DELETE_MODE):
            del_time = settings.get('auto_delete_time', AUTO_DELETE_TIME)
            mins, secs = divmod(del_time, 60)
            time_str = f"{mins}m {secs}s" if mins else f"{secs}s"
            
            warn = await msg.reply(f"<b>⚠️ File will be deleted in {time_str}. Save it now!</b>")
            
            async def delete_after():
                await asyncio.sleep(del_time)
                try:
                    await sent.delete()
                    await warn.edit_text("✅ File deleted.")
                except:
                    pass
            
            asyncio.create_task(delete_after())
        
        if DB_LOADED:
            await clone_db.update_last_used(client.me.id)
        return True
        
    except Exception as e:
        logger.error(f"Send file error: {e}")
        return False

# ==================== COMMANDS ====================
@Client.on_message(filters.command("start") & filters.private, group=1)
async def start_cmd(client, msg):
    settings = await get_clone_settings(client)
    
    # Maintenance check
    if settings.get('maintenance', False):
        return await msg.reply("<b>🔧 Maintenance mode. Try later!</b>")
    
    # Log new users
    log_ch = settings.get('log_channel')
    if log_ch:
        try:
            await client.send_message(log_ch, f"👤 **New User**\n{msg.from_user.mention}\nID: `{msg.from_user.id}`")
        except Exception as e:
            logger.error(f"Log error: {e}")
    
    # Force sub check
    subscribed, channels = await check_force_sub(client, msg.from_user.id)
    if not subscribed:
        buttons = []
        for ch_id in channels:
            link, title = await get_channel_info(client, ch_id)
            if link:
                buttons.append([InlineKeyboardButton(f'📢 {title}', url=link)])
        buttons.append([InlineKeyboardButton('🔄 Try Again', callback_data='clone_start')])
        return await msg.reply("<b>⚠️ Join channels first!</b>", reply_markup=InlineKeyboardMarkup(buttons))
    
    # Deep link handling
    if len(msg.command) > 1:
        data = msg.command[1]
        
        # Check for batch range
        first_id, last_id = decode_batch_range(data)
        if first_id and last_id:
            loading = await msg.reply("<b>📦 Sending batch files...</b>")
            total = last_id - first_id + 1
            sent_count = 0
            
            for file_id in range(first_id, last_id + 1):
                success = await send_file(client, msg, file_id)
                if success:
                    sent_count += 1
                await asyncio.sleep(0.5)  # Small delay to avoid flood
                
                # Update progress every 5 files
                if sent_count % 5 == 0 and sent_count > 0:
                    try:
                        await loading.edit_text(f"<b>📦 Sending... {sent_count}/{total}</b>")
                    except:
                        pass
            
            await loading.edit_text(f"<b>✅ Sent {sent_count}/{total} files!</b>")
            return
        
        # Single file
        file_id = decode_file_id(data)
        if file_id:
            loading = await msg.reply("<b>🔄 Fetching file...</b>")
            await send_file(client, msg, file_id)
            await loading.delete()
            return
    
    # Normal start
    text = await get_start_text(client, msg.from_user.mention)
    keyboard = await get_start_keyboard(client)
    photo = settings.get('start_photo')
    
    if photo:
        try:
            await msg.reply_photo(photo, caption=text, reply_markup=keyboard)
        except:
            await msg.reply(text, reply_markup=keyboard, disable_web_page_preview=True)
    else:
        await msg.reply(text, reply_markup=keyboard, disable_web_page_preview=True)

@Client.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.private, group=1)
async def file_upload(client, msg):
    settings = await get_clone_settings(client)
    
    if settings.get('maintenance', False):
        return await msg.reply("<b>🔧 Maintenance mode!</b>")
    
    # Authorization check
    if not settings.get('public_use', True):
        clone = await clone_db.get_clone(client.me.id) if DB_LOADED else None
        admins = settings.get('admins', [])
        owner_id = clone['user_id'] if clone else 0
        if msg.from_user.id not in [owner_id] + admins:
            return await msg.reply("<b>⚠️ Private bot! Admins only.</b>")
    
    # Check batch mode
    user_id = msg.from_user.id
    if user_id in batch_data and isinstance(batch_data.get(user_id), dict):
        # Allow file collection for manual batch
        if batch_data[user_id].get('type') == 'manual':
            return
        return await msg.reply("<b>📦 You're in a different batch mode! Use /cancel to stop.</b>")
    
    # Upload to DB
    db_ch = settings.get('db_channel') or LOG_CHANNEL
    if not db_ch:
        return await msg.reply("<b>❌ DB Channel not configured!</b>")
    
    status = await msg.reply("<b>📤 Uploading...</b>")
    
    try:
        post = await msg.copy(db_ch)
        encoded = encode_file_id(post.id)
        link = f"https://t.me/{client.me.username}?start={encoded}"
        
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Open Link", url=link)],
            [InlineKeyboardButton("📋 Copy", callback_data=f"copy_{encoded}")]
        ])
        
        await status.edit_text(
            f"<b>✅ Uploaded!</b>\n\n<code>{link}</code>",
            reply_markup=buttons,
            disable_web_page_preview=True
        )
        
        if DB_LOADED:
            await clone_db.update_last_used(client.me.id)
    except Exception as e:
        logger.error(f"Upload error: {e}")
        await status.edit_text("<b>❌ Upload failed!</b>")

# ==================== MANUAL BATCH (Collect Files) ====================
@Client.on_message(filters.command("batch") & filters.private, group=1)
async def batch_start(client, msg):
    user_id = msg.from_user.id
    batch_data[user_id] = {'files': [], 'type': 'manual'}
    
    await msg.reply(
        "<b>📦 Manual Batch Mode Started!</b>\n\n"
        "📤 Send me your files one by one.\n"
        "✅ Use /done when you have sent all files.\n"
        "❌ Use /cancel to stop at any time."
    )

@Client.on_message(filters.command("done") & filters.private, group=1)
async def batch_done(client, msg):
    user_id = msg.from_user.id
    
    if user_id not in batch_data or not isinstance(batch_data.get(user_id), dict) or batch_data[user_id].get('type') != 'manual':
        return await msg.reply("<b>❌ You are not in manual batch mode.</b>")
    
    files = batch_data[user_id].get('files', [])
    
    if not files:
        del batch_data[user_id]
        return await msg.reply("<b>❌ No files were added to the batch! Batch cancelled.</b>")
    
    if len(files) < 2:
        del batch_data[user_id]
        return await msg.reply("<b>❌ A batch needs at least 2 files! Batch cancelled.</b>")
    
    # Get DB channel
    settings = await get_clone_settings(client)
    db_ch = settings.get('db_channel') or LOG_CHANNEL
    if not db_ch:
        del batch_data[user_id]
        return await msg.reply("<b>❌ DB Channel not configured! Cannot create batch.</b>")

    status = await msg.reply("<b>📤 Uploading files to DB channel...</b>")
    
    message_ids = []
    try:
        for file_id in files:
            post = await client.copy_message(db_ch, from_chat_id=user_id, message_id=file_id)
            message_ids.append(post.id)
            await asyncio.sleep(0.5)
    except Exception as e:
        logger.error(f"Manual batch upload error: {e}")
        await status.edit_text("<b>❌ Failed to save batch files to DB! Please try again.</b>")
        del batch_data[user_id]
        return

    # Create batch link using range
    first_id = min(message_ids)
    last_id = max(message_ids)
    encoded = encode_batch_range(first_id, last_id)
    del batch_data[user_id]
    
    link = f"https://t.me/{client.me.username}?start={encoded}"
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Open Batch", url=link)],
        [InlineKeyboardButton("📋 Copy Link", callback_data=f"copy_batch_{encoded}")]
    ])
    
    await status.edit_text(
        f"<b>✅ Manual Batch Created!</b>\n\n"
        f"📦 Files: {len(message_ids)}\n"
        f"🔗 Link: <code>{link}</code>\n\n"
        f"<i>Users will get all files when they click the link.</i>",
        reply_markup=buttons,
        disable_web_page_preview=True
    )

# ==================== QUICK BATCH (From Channel Range) ====================
@Client.on_message(filters.command("genbatch") & filters.private, group=1)
async def genbatch_cmd(client, msg):
    settings = await get_clone_settings(client)
    
    # Authorization check
    clone = await clone_db.get_clone(client.me.id) if DB_LOADED else None
    admins = settings.get('admins', [])
    owner_id = clone['user_id'] if clone else 0
    
    if msg.from_user.id not in [owner_id] + admins:
        return await msg.reply("<b>⚠️ Only admins can use this command!</b>")
    
    user_id = msg.from_user.id
    batch_data[user_id] = {'type': 'genbatch'}
    
    await msg.reply(
        "<b>⚡ Quick Batch Mode!</b>\n\n"
        "<b>📝 Instructions:</b>\n"
        "1️⃣ Forward the <b>FIRST message</b> from your source channel.\n"
        "2️⃣ Forward the <b>LAST message</b> from the same channel.\n\n"
        "<i>Note: Both messages must be from the same channel.</i>\n\n"
        "❌ Use /cancel to stop."
    )

@Client.on_message(filters.forwarded & filters.private, group=3)
async def handle_genbatch_forward(client, msg):
    user_id = msg.from_user.id
    
    if user_id not in batch_data or batch_data.get(user_id, {}).get('type') != 'genbatch':
        return
    
    if not msg.forward_from_chat:
        return await msg.reply("<b>❌ Please forward messages from a public or private channel, not from a user.</b>")

    # --- START OF FIXED LOGIC ---
    batch_info = batch_data[user_id]

    # Step 1: Capture the first message and set the source channel
    if 'first_msg_id' not in batch_info:
        batch_info['first_msg_id'] = msg.forward_from_message_id
        batch_info['source_channel'] = msg.forward_from_chat.id # Dynamically set channel
        batch_info['source_channel_name'] = msg.forward_from_chat.title or "this channel"
        
        await msg.reply(
            f"<b>✅ First message saved!</b>\n"
            f"<b>Source Channel:</b> {batch_info['source_channel_name']}\n"
            f"<b>Message ID:</b> <code>{msg.forward_from_message_id}</code>\n\n"
            f"➡️ Now, forward the <b>LAST message</b> from the same channel."
        )
        return

    # Step 2: Capture the second message and validate it
    if 'last_msg_id' not in batch_info:
        # Check if the second message is from the SAME channel as the first
        if msg.forward_from_chat.id != batch_info['source_channel']:
            link, title = await get_channel_info(client, batch_info['source_channel'])
            keyboard = None
            if link:
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(f"🔗 Go to {title}", url=link)]])
            
            await msg.reply(
                f"<b>❌ Wrong Channel!</b>\n\nPlease forward a message from the channel you started with: <b>{title}</b>.",
                reply_markup=keyboard
            )
            return

        last_msg_id = msg.forward_from_message_id
        first_msg_id = batch_info['first_msg_id']
        
        if last_msg_id <= first_msg_id:
            await msg.reply("<b>❌ Error: The last message's ID must be greater than the first message's ID. Please forward them in the correct order.</b>")
            # Reset to let user try again with the last message
            del batch_info['last_msg_id']
            return
            
        total = last_msg_id - first_msg_id + 1
        encoded = encode_batch_range(first_msg_id, last_msg_id)
        link = f"https://t.me/{client.me.username}?start={encoded}"
        
        del batch_data[user_id] # Clean up
        
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Open Batch", url=link)],
            [InlineKeyboardButton("📋 Copy Link", callback_data=f"copy_batch_{encoded}")]
        ])
        
        await msg.reply(
            f"<b>⚡ Quick Batch Created!</b>\n\n"
            f"📦 Total Files: {total}\n"
            f"📍 From Message ID: <code>{first_msg_id}</code>\n"
            f"📍 To Message ID: <code>{last_msg_id}</code>\n"
            f"🔗 Link: <code>{link}</code>\n\n"
            f"<i>Share this link to provide access to all files in the range!</i>",
            reply_markup=buttons,
            disable_web_page_preview=True
        )
    # --- END OF FIXED LOGIC ---

@Client.on_message(filters.command("cancel") & filters.private, group=1)
async def batch_cancel(client, msg):
    user_id = msg.from_user.id
    if user_id in batch_data:
        del batch_data[user_id]
        await msg.reply("<b>❌ Action cancelled!</b>")
    else:
        await msg.reply("<b>❌ Nothing to cancel.</b>")

@Client.on_message(filters.command(["help", "about"]) & filters.private, group=1)
async def help_about(client, msg):
    cmd = msg.command[0].lower()
    text = HELP_TEXT if cmd == "help" else ABOUT_TEXT
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('🏠 Home', callback_data='clone_start')]])
    await msg.reply(text, reply_markup=keyboard)

# ==================== CALLBACK HANDLERS ====================
@Client.on_callback_query(filters.regex("^clone_"))
async def callbacks(client, query: CallbackQuery):
    data = query.data
    
    if data == "clone_start":
        await query.answer()
        subscribed, channels = await check_force_sub(client, query.from_user.id)
        if not subscribed:
            buttons = []
            for ch_id in channels:
                link, title = await get_channel_info(client, ch_id)
                if link:
                    buttons.append([InlineKeyboardButton(f'📢 {title}', url=link)])
            buttons.append([InlineKeyboardButton('🔄 Try', callback_data='clone_start')])
            return await query.message.edit_text("<b>⚠️ Join first!</b>", reply_markup=InlineKeyboardMarkup(buttons))
        
        text = await get_start_text(client, query.from_user.mention)
        keyboard = await get_start_keyboard(client)
        await query.message.edit_text(text, reply_markup=keyboard, disable_web_page_preview=True)
        
    elif data == "clone_help":
        await query.answer()
        await query.message.edit_text(HELP_TEXT, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🏠 Home', callback_data='clone_start')]]))
        
    elif data == "clone_about":
        await query.answer()
        await query.message.edit_text(ABOUT_TEXT, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🏠 Home', callback_data='clone_start')]]))

@Client.on_callback_query(filters.regex("^copy_"))
async def copy_callback(client, query: CallbackQuery):
    parts = query.data.split("_", 2)
    
    if len(parts) >= 2 and parts[1] == "batch":
        encoded = parts[2]
        link_type = "Batch Link"
    else:
        encoded = parts[1]
        link_type = "File Link"

    link = f"https://t.me/{client.me.username}?start={encoded}"
    await query.answer(f"📋 {link_type} copied!\n\n{link}", show_alert=True)

# Handle batch file collection (manual batch)
@Client.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.private, group=2)
async def batch_collect(client, msg):
    user_id = msg.from_user.id
    
    if user_id not in batch_data or not isinstance(batch_data.get(user_id), dict) or batch_data[user_id].get('type') != 'manual':
        return
    
    try:
        # We store the message ID from the user's chat to copy it later
        batch_data[user_id]['files'].append(msg.id)
        count = len(batch_data[user_id]['files'])
        await msg.reply(f"<b>✅ File {count} added to batch! Use /done when finished.</b>")
    except Exception as e:
        logger.error(f"Batch collect error: {e}")
        await msg.reply("<b>❌ Failed to add file!</b>")

logger.info("✅ Clone commands loaded with improved batch system!")
