# -*- coding: utf-8 -*-
# clone_plugins/clonemade.py
import base64
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import PeerIdInvalid, ChannelInvalid, UserNotParticipant, FloodWait

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
    """Send a single file from DB channel to user. Used for single file links."""
    settings = await get_clone_settings(client)
    db_ch = settings.get('db_channel') or LOG_CHANNEL
    
    if not db_ch:
        await msg.reply("<b>❌ DB Channel not configured!</b>")
        return False
    
    try:
        file_msg = await client.get_messages(db_ch, file_id)
        if not file_msg or not file_msg.media:
            return False
        
        media = file_msg.document or file_msg.video or file_msg.audio or file_msg.photo
        filename = getattr(media, 'file_name', 'N/A')
        filesize = getattr(media, 'file_size', 0)
        
        caption = file_msg.caption
        custom_cap = settings.get('file_caption')
        if custom_cap:
            caption = custom_cap.replace('{filename}', filename)
            caption = caption.replace('{size}', f"{filesize / (1024*1024):.2f} MB")
            caption = caption.replace('{caption}', file_msg.caption or '')
        
        protect = settings.get('protect_mode', False)
        sent = await file_msg.copy(msg.from_user.id, caption=caption, protect_content=protect)
        
        if settings.get('auto_delete', AUTO_DELETE_MODE):
            del_time = settings.get('auto_delete_time', AUTO_DELETE_TIME)
            mins, secs = divmod(del_time, 60)
            time_str = f"{mins}m {secs}s" if mins else f"{secs}s"
            warn = await msg.reply(f"<b>⚠️ This file will be deleted in {time_str}. Save it now!</b>")
            
            async def delete_after():
                await asyncio.sleep(del_time)
                try:
                    await sent.delete()
                    await warn.edit_text("✅ File deleted.")
                except: pass
            
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
    
    if settings.get('maintenance', False):
        return await msg.reply("<b>🔧 Maintenance mode. Try later!</b>")
    
    log_ch = settings.get('log_channel')
    if log_ch:
        try: await client.send_message(log_ch, f"👤 **New User**\n{msg.from_user.mention}\nID: `{msg.from_user.id}`")
        except Exception as e: logger.error(f"Log error: {e}")
    
    subscribed, channels = await check_force_sub(client, msg.from_user.id)
    if not subscribed:
        buttons = []
        for ch_id in channels:
            link, title = await get_channel_info(client, ch_id)
            if link: buttons.append([InlineKeyboardButton(f'📢 {title}', url=link)])
        buttons.append([InlineKeyboardButton('🔄 Try Again', callback_data='clone_start')])
        return await msg.reply("<b>⚠️ Join channels first!</b>", reply_markup=InlineKeyboardMarkup(buttons))
    
    # --- DEEP LINK & BATCH HANDLING ---
    if len(msg.command) > 1:
        data = msg.command[1]
        first_id, last_id = decode_batch_range(data)
        
        # --- OPTIMIZED BATCH SENDING LOGIC ---
        if first_id and last_id:
            db_ch = settings.get('db_channel') or LOG_CHANNEL
            if not db_ch:
                return await msg.reply("<b>❌ DB Channel not configured! Cannot send batch.</b>")

            loading = await msg.reply("<b>🚀 Preparing your batch... Please wait.</b>")
            message_ids = list(range(first_id, last_id + 1))
            total = len(message_ids)
            protect = settings.get('protect_mode', False)
            sent_count = 0

            try:
                # Use the efficient copy_messages for speed
                sent_messages = await client.copy_messages(
                    chat_id=msg.from_user.id,
                    from_chat_id=db_ch,
                    message_ids=message_ids,
                    protect_content=protect
                )
                sent_count = len(sent_messages)
                await loading.edit_text(f"<b>✅ Batch Sent!</b>\n\nSent {sent_count} of {total} files.")

                # Handle auto-delete for the entire batch at once
                if sent_count > 0 and settings.get('auto_delete', AUTO_DELETE_MODE):
                    del_time = settings.get('auto_delete_time', AUTO_DELETE_TIME)
                    mins, secs = divmod(del_time, 60)
                    time_str = f"{mins}m {secs}s" if mins else f"{secs}s"
                    warn = await msg.reply(f"<b>⚠️ These {sent_count} files will be deleted in {time_str}. Please save them now!</b>")
                    
                    async def delete_batch_after():
                        await asyncio.sleep(del_time)
                        try:
                            ids_to_delete = [m.id for m in sent_messages]
                            await client.delete_messages(msg.from_user.id, ids_to_delete)
                            await warn.edit_text(f"✅ All {sent_count} batch files have been deleted.")
                        except Exception as e:
                            logger.error(f"Auto-delete batch error: {e}")
                            await warn.edit_text(f"❌ Could not delete all batch files.")
                    
                    asyncio.create_task(delete_batch_after())

            except FloodWait as fw:
                await asyncio.sleep(fw.value)
                await loading.edit_text(f"<b>⏳ Flood wait... Retrying in {fw.value}s.</b>")
                # You might want to add retry logic here if needed
            except Exception as e:
                logger.error(f"Batch sending error: {e}")
                await loading.edit_text(f"<b>❌ An error occurred sending the batch. Sent {sent_count}/{total}.</b>")
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
        try: await msg.reply_photo(photo, caption=text, reply_markup=keyboard)
        except: await msg.reply(text, reply_markup=keyboard, disable_web_page_preview=True)
    else:
        await msg.reply(text, reply_markup=keyboard, disable_web_page_preview=True)

@Client.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.private, group=1)
async def file_upload(client, msg):
    settings = await get_clone_settings(client)
    
    if settings.get('maintenance', False): return await msg.reply("<b>🔧 Maintenance mode!</b>")
    
    if not settings.get('public_use', True):
        clone = await clone_db.get_clone(client.me.id) if DB_LOADED else None
        admins = settings.get('admins', [])
        owner_id = clone['user_id'] if clone else 0
        if msg.from_user.id not in [owner_id] + admins:
            return await msg.reply("<b>⚠️ Private bot! Admins only.</b>")
    
    user_id = msg.from_user.id
    if user_id in batch_data and isinstance(batch_data.get(user_id), dict):
        if batch_data[user_id].get('type') == 'manual': return
        return await msg.reply("<b>📦 You're in a different batch mode! Use /cancel to stop.</b>")
    
    db_ch = settings.get('db_channel') or LOG_CHANNEL
    if not db_ch: return await msg.reply("<b>❌ DB Channel not configured!</b>")
    
    status = await msg.reply("<b>📤 Uploading...</b>")
    
    try:
        post = await msg.copy(db_ch)
        encoded = encode_file_id(post.id)
        link = f"https://t.me/{client.me.username}?start={encoded}"
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Open Link", url=link)],
            [InlineKeyboardButton("📋 Copy", callback_data=f"copy_{encoded}")]
        ])
        await status.edit_text(f"<b>✅ Uploaded!</b>\n\n<code>{link}</code>", reply_markup=buttons, disable_web_page_preview=True)
        if DB_LOADED: await clone_db.update_last_used(client.me.id)
    except Exception as e:
        logger.error(f"Upload error: {e}")
        await status.edit_text("<b>❌ Upload failed!</b>")

# ==================== MANUAL BATCH ====================
@Client.on_message(filters.command("batch") & filters.private, group=1)
async def batch_start(client, msg):
    user_id = msg.from_user.id
    batch_data[user_id] = {'files': [], 'type': 'manual'}
    await msg.reply("<b>📦 Manual Batch Mode Started!</b>\n\n📤 Send files one by one.\n✅ Use /done when finished.\n❌ Use /cancel to stop.")

@Client.on_message(filters.command("done") & filters.private, group=1)
async def batch_done(client, msg):
    user_id = msg.from_user.id
    if user_id not in batch_data or batch_data.get(user_id, {}).get('type') != 'manual':
        return await msg.reply("<b>❌ You are not in manual batch mode.</b>")
    
    files = batch_data[user_id].get('files', [])
    if not files:
        del batch_data[user_id]
        return await msg.reply("<b>❌ No files added! Batch cancelled.</b>")
    if len(files) < 2:
        del batch_data[user_id]
        return await msg.reply("<b>❌ Batch needs at least 2 files! Batch cancelled.</b>")
    
    settings = await get_clone_settings(client)
    db_ch = settings.get('db_channel') or LOG_CHANNEL
    if not db_ch:
        del batch_data[user_id]
        return await msg.reply("<b>❌ DB Channel not configured! Cannot create batch.</b>")

    status = await msg.reply("<b>📤 Saving batch to DB...</b>")
    message_ids = []
    try:
        for file_id in files:
            post = await client.copy_message(db_ch, from_chat_id=user_id, message_id=file_id)
            message_ids.append(post.id)
            await asyncio.sleep(0.3)
    except Exception as e:
        logger.error(f"Manual batch upload error: {e}")
        del batch_data[user_id]
        return await status.edit_text("<b>❌ Failed to save batch! Please try again.</b>")

    first_id, last_id = min(message_ids), max(message_ids)
    encoded = encode_batch_range(first_id, last_id)
    del batch_data[user_id]
    link = f"https://t.me/{client.me.username}?start={encoded}"
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Open Batch", url=link)], [InlineKeyboardButton("📋 Copy Link", callback_data=f"copy_batch_{encoded}")]])
    await status.edit_text(f"<b>✅ Manual Batch Created!</b>\n\n📦 Files: {len(message_ids)}\n🔗 Link: <code>{link}</code>", reply_markup=buttons, disable_web_page_preview=True)

# ==================== QUICK BATCH ====================
@Client.on_message(filters.command("genbatch") & filters.private, group=1)
async def genbatch_cmd(client, msg):
    settings = await get_clone_settings(client)
    clone = await clone_db.get_clone(client.me.id) if DB_LOADED else None
    admins = settings.get('admins', [])
    owner_id = clone['user_id'] if clone else 0
    if msg.from_user.id not in [owner_id] + admins:
        return await msg.reply("<b>⚠️ Only admins can use this command!</b>")
    
    user_id = msg.from_user.id
    batch_data[user_id] = {'type': 'genbatch'}
    await msg.reply("<b>⚡ Quick Batch Mode!</b>\n\n📝 **Instructions:**\n1️⃣ Forward the <b>FIRST message</b> from your source channel.\n2️⃣ Forward the <b>LAST message</b> from the same channel.\n\n❌ Use /cancel to stop.")

@Client.on_message(filters.forwarded & filters.private, group=3)
async def handle_genbatch_forward(client, msg):
    user_id = msg.from_user.id
    if user_id not in batch_data or batch_data.get(user_id, {}).get('type') != 'genbatch': return
    if not msg.forward_from_chat: return await msg.reply("<b>❌ Please forward from a channel, not a user.</b>")

    batch_info = batch_data[user_id]

    if 'first_msg_id' not in batch_info:
        batch_info['first_msg_id'] = msg.forward_from_message_id
        batch_info['source_channel'] = msg.forward_from_chat.id
        batch_info['source_channel_name'] = msg.forward_from_chat.title or "this channel"
        await msg.reply(f"<b>✅ First message saved!</b>\n<b>From:</b> {batch_info['source_channel_name']}\n\n➡️ Now forward the <b>LAST message</b> from the same channel.")
        return

    if 'last_msg_id' not in batch_info:
        if msg.forward_from_chat.id != batch_info['source_channel']:
            link, title = await get_channel_info(client, batch_info['source_channel'])
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(f"🔗 Go to {title}", url=link)]]) if link else None
            return await msg.reply(f"<b>❌ Wrong Channel!</b>\nPlease forward from: <b>{title}</b>.", reply_markup=keyboard)

        last_msg_id = msg.forward_from_message_id
        first_msg_id = batch_info['first_msg_id']
        
        if last_msg_id <= first_msg_id:
            return await msg.reply("<b>❌ Last message must be after the first! Start over with /cancel.</b>")
            
        # --- NEW: ADD CHANNEL LINK TO CONFIRMATION ---
        ch_link, ch_title = await get_channel_info(client, batch_info['source_channel'])
        channel_info_text = f"🔗 Source: <a href='{ch_link}'>{ch_title}</a>\n" if ch_link else ""

        total = last_msg_id - first_msg_id + 1
        encoded = encode_batch_range(first_msg_id, last_msg_id)
        link = f"https://t.me/{client.me.username}?start={encoded}"
        del batch_data[user_id]
        buttons = InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Open Batch", url=link)], [InlineKeyboardButton("📋 Copy Link", callback_data=f"copy_batch_{encoded}")]])
        
        await msg.reply(
            f"<b>⚡ Quick Batch Created!</b>\n\n"
            f"{channel_info_text}"
            f"📦 Total Files: {total}\n"
            f"🔗 Link: <code>{link}</code>",
            reply_markup=buttons,
            disable_web_page_preview=True
        )

@Client.on_message(filters.command("cancel") & filters.private, group=1)
async def batch_cancel(client, msg):
    if msg.from_user.id in batch_data:
        del batch_data[msg.from_user.id]
        await msg.reply("<b>❌ Action cancelled!</b>")
    else:
        await msg.reply("<b>❌ Nothing to cancel.</b>")

@Client.on_message(filters.command(["help", "about"]) & filters.private, group=1)
async def help_about(client, msg):
    cmd = msg.command[0].lower()
    text = HELP_TEXT if cmd == "help" else ABOUT_TEXT
    await msg.reply(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🏠 Home', callback_data='clone_start')]]))

# ==================== CALLBACKS ====================
@Client.on_callback_query(filters.regex("^clone_"))
async def callbacks(client, query: CallbackQuery):
    data = query.data
    await query.answer()
    
    if data == "clone_start":
        subscribed, channels = await check_force_sub(client, query.from_user.id)
        if not subscribed:
            buttons = []
            for ch_id in channels:
                link, title = await get_channel_info(client, ch_id)
                if link: buttons.append([InlineKeyboardButton(f'📢 {title}', url=link)])
            buttons.append([InlineKeyboardButton('🔄 Try', callback_data='clone_start')])
            return await query.message.edit_text("<b>⚠️ Join first!</b>", reply_markup=InlineKeyboardMarkup(buttons))
        text = await get_start_text(client, query.from_user.mention)
        await query.message.edit_text(text, reply_markup=await get_start_keyboard(client), disable_web_page_preview=True)
    elif data == "clone_help":
        await query.message.edit_text(HELP_TEXT, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🏠 Home', callback_data='clone_start')]]))
    elif data == "clone_about":
        await query.message.edit_text(ABOUT_TEXT, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🏠 Home', callback_data='clone_start')]]))

@Client.on_callback_query(filters.regex("^copy_"))
async def copy_callback(client, query: CallbackQuery):
    parts = query.data.split("_", 2)
    link_type = "Batch Link" if len(parts) >= 2 and parts[1] == "batch" else "File Link"
    encoded = parts[-1]
    link = f"https://t.me/{client.me.username}?start={encoded}"
    await query.answer(f"📋 {link_type} copied!\n\n{link}", show_alert=True)

# Collect files for manual batch
@Client.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.private, group=2)
async def batch_collect(client, msg):
    user_id = msg.from_user.id
    if user_id not in batch_data or batch_data.get(user_id, {}).get('type') != 'manual': return
    try:
        batch_data[user_id]['files'].append(msg.id)
        await msg.reply(f"<b>✅ File {len(batch_data[user_id]['files'])} added! Use /done when finished.</b>")
    except Exception as e:
        logger.error(f"Batch collect error: {e}")
        await msg.reply("<b>❌ Failed to add file!</b>")

logger.info("✅ Clone commands loaded with OPTIMIZED batch system!")
