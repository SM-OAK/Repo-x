import base64
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Config imports with fallback
try:
    from config import LOG_CHANNEL, ADMINS, AUTO_DELETE_MODE, AUTO_DELETE_TIME
except ImportError:
    LOG_CHANNEL = None
    ADMINS = []
    AUTO_DELETE_MODE = False
    AUTO_DELETE_TIME = 1800

# DB import fallback
try:
    from database.clone_db import clone_db
except ImportError:
    clone_db = None

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
    """Returns keyboard for clone bot start message"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('💁‍♀️ ʜᴇʟᴘ', callback_data='clone_help'),
            InlineKeyboardButton('😊 ᴀʙᴏᴜᴛ', callback_data='clone_about')
        ]
    ])


async def decode_file_id(data):
    """Decode file ID from various formats"""
    try:
        # Format 1: file_123
        if data.startswith("file_"):
            return int(data[5:])
        
        # Format 2: Base64 decode
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
    """Send file from LOG_CHANNEL to user"""
    if not LOG_CHANNEL:
        await message.reply("<b>❌ File storage not configured!</b>")
        return False
    
    try:
        file_msg = await client.get_messages(LOG_CHANNEL, file_id)
        
        if not file_msg or not file_msg.media:
            await message.reply("<b>❌ Fɪʟᴇ ɴᴏᴛ ғᴏᴜɴᴅ!</b>")
            return False
        
        sent_msg = await file_msg.copy(
            chat_id=message.from_user.id,
            caption=file_msg.caption
        )
        
        # Auto-delete if enabled
        if AUTO_DELETE_MODE:
            warning = await message.reply(
                f"<b>⚠️ IMPORTANT</b>\n\n"
                f"This file will be deleted in <b>{AUTO_DELETE_TIME // 60} minutes</b>.\n"
                f"Please forward to Saved Messages!"
            )
            
            await asyncio.sleep(AUTO_DELETE_TIME)
            
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


# Clone bot handlers - Use group=10 for lower priority
@Client.on_message(filters.command("start") & filters.private, group=10)
async def clone_start(client, message):
    """Clone bot start handler - lower priority"""
    
    # Handle deep links
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
        else:
            print(f"Clone: Invalid parameter - {parameter}")
    
    # Show start message
    await message.reply(
        START_TEXT.format(message.from_user.mention),
        reply_markup=get_start_keyboard()
    )


@Client.on_callback_query(filters.regex("^clone_"), group=10)
async def clone_callbacks(client, query: CallbackQuery):
    """Handle clone bot callback queries"""
    data = query.data
    
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
        await query.message.edit_text(
            START_TEXT.format(query.from_user.mention),
            reply_markup=get_start_keyboard()
        )
    
    await query.answer()


@Client.on_message(filters.command(["help", "about"]) & filters.private, group=10)
async def clone_help_about(client, message):
    """Handle help/about commands for clone bot"""
    command = message.command[0].lower()
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton('🏠 ʜᴏᴍᴇ', callback_data='clone_start')
    ]])
    
    if command == "help":
        await message.reply(HELP_TEXT, reply_markup=keyboard)
    else:
        await message.reply(ABOUT_TEXT, reply_markup=keyboard)


@Client.on_message(
    (filters.document | filters.video | filters.audio | filters.photo) & filters.private, 
    group=10
)
async def clone_file_upload(client, message):
    """Handle file uploads for clone bot"""
    if not LOG_CHANNEL:
        return await message.reply("<b>❌ Fɪʟᴇ sᴛᴏʀᴀɢᴇ ɴᴏᴛ ᴄᴏɴғɪɢᴜʀᴇᴅ!</b>")
    
    try:
        post = await message.copy(LOG_CHANNEL)
        file_id = str(post.id)
        bot_username = (await client.get_me()).username
        
        string = f'file_{file_id}'
        encoded = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
        share_link = f"https://t.me/{bot_username}?start={encoded}"
        
        await message.reply(
            f"<b>⭕ Hᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ:\n\n🔗 Lɪɴᴋ: {share_link}</b>",
            quote=True
        )
    except Exception as e:
        print(f"Clone: Upload error - {e}")
        await message.reply("<b>❌ Fᴀɪʟᴇᴅ ᴛᴏ ɢᴇɴᴇʀᴀᴛᴇ ʟɪɴᴋ!</b>")


print("✅ Clone bot commands loaded (group=10 - lower priority)")
