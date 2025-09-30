import base64
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Import system-wide settings and the database
from config import LOG_CHANNEL
from database.clone_db import clone_db

# --- Default Text and Keyboards ---

START_TEXT = """<b>Hᴇʟʟᴏ {} ✨

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

def get_start_keyboard():
    """Get keyboard for start message"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('💁‍♀️ ʜᴇʟᴘ', callback_data='clone_help'),
            InlineKeyboardButton('😊 ᴀʙᴏᴜᴛ', callback_data='clone_about')
        ]
    ])

# --- Helper Functions ---

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
    except:
        return None

async def send_file_to_user(client, message, file_id):
    """Retrieve and send file to user with custom settings"""
    if not LOG_CHANNEL:
        return False
    
    try:
        file_msg = await client.get_messages(LOG_CHANNEL, file_id)
        
        if not file_msg or not file_msg.media:
            await message.reply("<b>❌ Fɪʟᴇ ɴᴏᴛ ғᴏᴜɴᴅ!</b>")
            return False
        
        # Get custom settings from DB for this clone
        bot_id = client.me.id
        clone = await clone_db.get_clone(bot_id)
        settings = clone.get('settings', {})
        auto_delete_enabled = settings.get('auto_delete', False)
        auto_delete_time = settings.get('auto_delete_time', 1800)
        
        # Send file to user
        sent_msg = await file_msg.copy(
            chat_id=message.from_user.id,
            caption=file_msg.caption
        )
        
        # Auto-delete if enabled for this clone
        if auto_delete_enabled:
            await asyncio.sleep(auto_delete_time)
            try:
                await sent_msg.delete()
            except:
                pass # Ignore if message is already deleted
        
        return True
        
    except Exception as e:
        await message.reply(f"<b>❌ Eʀʀᴏʀ: {str(e)}</b>")
        return False

# --- Command and Message Handlers ---

@Client.on_message(filters.command("start") & filters.private, group=1)
async def clone_start(client, message):
    """Clone bot start handler with custom message support"""
    
    if len(message.command) > 1:
        parameter = message.command[1]
        file_id = await decode_file_id(parameter)
        if file_id:
            loading = await message.reply("<b>🔄 Fᴇᴛᴄʜɪɴɢ ғɪʟᴇ...</b>")
            success = await send_file_to_user(client, message, file_id)
            await loading.delete()
            if success:
                return

    # Get custom start message settings from DB
    bot_id = client.me.id
    clone = await clone_db.get_clone(bot_id)
    
    if clone and clone.get('settings'):
        settings = clone['settings']
        custom_photo = settings.get('start_photo')
        custom_message = settings.get('start_message')

        if custom_photo:
            await message.reply_photo(
                photo=custom_photo,
                caption=custom_message or "",
                reply_markup=get_start_keyboard()
            )
            return
            
        if custom_message:
            await message.reply_text(custom_message, reply_markup=get_start_keyboard())
            return

    # Fallback to default start message
    await message.reply(
        START_TEXT.format(message.from_user.mention),
        reply_markup=get_start_keyboard()
    )

@Client.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.private, group=1)
async def clone_file_upload(client, message):
    """Handle file uploads in clone bot"""
    if not LOG_CHANNEL:
        return await message.reply("<b>❌ Fɪʟᴇ sᴛᴏʀᴀɢᴇ ɴᴏᴛ ᴄᴏɴғɪɢᴜʀᴇᴅ!</b>")
    
    try:
        post = await message.copy(LOG_CHANNEL)
        file_id = str(post.id)
        
        bot_username = client.me.username
        string = f'file_{file_id}'
        encoded = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
        share_link = f"https://t.me/{bot_username}?start={encoded}"
        
        await message.reply(f"<b>⭕ Hᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\n🔗 {share_link}</b>")
    except Exception as e:
        await message.reply("<b>❌ Fᴀɪʟᴇᴅ ᴛᴏ ɢᴇɴᴇʀᴀᴛᴇ ʟɪɴᴋ!</b>")

# --- Callback and Other Command Handlers ---

@Client.on_callback_query(filters.regex("^clone_"))
async def clone_callbacks(client, query: CallbackQuery):
    """Handle clone bot callbacks for help/about"""
    data = query.data
    
    if data == "clone_help":
        await query.message.edit_text(HELP_TEXT, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🏠 ʜᴏᴍᴇ', callback_data='clone_start')]]))
    elif data == "clone_about":
        await query.message.edit_text(ABOUT_TEXT, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🏠 ʜᴏᴍᴇ', callback_data='clone_start')]]))
    elif data == "clone_start":
        await query.message.edit_text(START_TEXT.format(query.from_user.mention), reply_markup=get_start_keyboard())
    
    await query.answer()

@Client.on_message(filters.command(["help", "about"]) & filters.private)
async def clone_help_about(client, message):
    """Handle help and about text commands"""
    command = message.command[0].lower()
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('🏠 ʜᴏᴍᴇ', callback_data='clone_start')]])
    
    if command == "help":
        await message.reply(HELP_TEXT, reply_markup=keyboard)
    else:
        await message.reply(ABOUT_TEXT, reply_markup=keyboard)
