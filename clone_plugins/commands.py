# clone_plugins/commands.py
import base64
import asyncio
import logging

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated

# ───────────────────────────────
# Local project imports
# ───────────────────────────────
try:
    from config import LOG_CHANNEL, ADMINS
    CONFIG_LOADED = True
except ImportError:
    LOG_CHANNEL = None
    ADMINS = []
    CONFIG_LOADED = False

try:
    from database.clone_db import clone_db
    DB_LOADED = True
except ImportError:
    DB_LOADED = False

# Force-sub logic
try:
    from clone_plugins.forcesub import check_force_sub
except ImportError:
    async def check_force_sub(client, user_id, settings=None):
        return True  # fallback if forcesub not available

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
async def get_clone_settings(bot_id):
    if not DB_LOADED:
        return None
    try:
        clone = await clone_db.get_clone(bot_id)
        return clone.get('settings', {}) if clone else {}
    except Exception:
        return {}

async def decode_file_id(data):
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

async def send_file_to_user(client, message, file_id, settings):
    if not LOG_CHANNEL:
        return False
    try:
        file_msg = await client.get_messages(LOG_CHANNEL, file_id)
        if not file_msg or not file_msg.media:
            await message.reply("<b>❌ Fɪʟᴇ ɴᴏᴛ ғᴏᴜɴᴅ!</b>")
            return False
        protect_content = settings.get('no_forward', False) if settings else False
        sent_msg = await file_msg.copy(
            chat_id=message.from_user.id,
            caption=file_msg.caption,
            protect_content=protect_content
        )
        auto_delete = settings.get('auto_delete', False) if settings else False
        auto_delete_time = settings.get('auto_delete_time', 300) if settings else 300
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
            except:
                pass
        return True
    except Exception as e:
        print(f"Clone: Error sending file - {e}")
        await message.reply(f"<b>❌ Eʀʀᴏʀ: {str(e)}</b>")
        return False

# ───────────────────────────────
# Command Handlers
# ───────────────────────────────
@Client.on_message(filters.command("start") & filters.private, group=1)
async def clone_start(client, message):
    bot_info = await client.get_me()
    bot_id = bot_info.id
    settings = await get_clone_settings(bot_id)
    if len(message.command) > 1:
        parameter = message.command[1]
        file_id = await decode_file_id(parameter)
        if file_id:
            # Force-sub check
            if not await check_force_sub(client, message.from_user.id, settings):
                channel = settings.get('force_sub_channel')
                buttons = [[InlineKeyboardButton(
                    '🔔 Jᴏɪɴ Cʜᴀɴɴᴇʟ',
                    url=f'https://t.me/{channel[1:] if channel.startswith("@") else channel}'
                )]]
                return await message.reply(
                    "<b>⚠️ Yᴏᴜ ᴍᴜsᴛ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴜsᴇ ᴛʜɪs ʙᴏᴛ!</b>",
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
            loading = await message.reply("<b>🔄 Fᴇᴛᴄʜɪɴɢ ғɪʟᴇ...</b>")
            success = await send_file_to_user(client, message, file_id, settings)
            try: await loading.delete()
            except: pass
            if success: return
    start_message = settings.get('start_message') if settings else None
    start_photo = settings.get('start_photo') if settings else None
    text = start_message if start_message else START_TEXT.format(message.from_user.mention)
    if start_photo:
        try:
            await message.reply_photo(photo=start_photo, caption=text, reply_markup=get_start_keyboard())
        except:
            await message.reply(text, reply_markup=get_start_keyboard())
    else:
        await message.reply(text, reply_markup=get_start_keyboard())

@Client.on_callback_query(filters.regex("^clone_"))
async def clone_callbacks(client, query: CallbackQuery):
    data = query.data
    bot_info = await client.get_me()
    bot_id = bot_info.id
    settings = await get_clone_settings(bot_id)
    start_message = settings.get('start_message') if settings else None
    start_photo = settings.get('start_photo') if settings else None
    text = start_message if start_message else START_TEXT.format(query.from_user.mention)
    
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
                await client.send_photo(chat_id=query.message.chat.id, photo=start_photo, caption=text,
                                        reply_markup=get_start_keyboard())
            else:
                await query.message.edit_text(text, reply_markup=get_start_keyboard())
        except:
            await query.message.edit_text(text, reply_markup=get_start_keyboard())
    await query.answer()

@Client.on_message(filters.command(["help", "about"]) & filters.private, group=1)
async def clone_help_about(client, message):
    command = message.command[0].lower()
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton('🏠 ʜᴏᴍᴇ', callback_data='clone_start')]])
    if command == "help":
        await message.reply(HELP_TEXT, reply_markup=keyboard)
    else:
        await message.reply(ABOUT_TEXT, reply_markup=keyboard)

@Client.on_message((filters.document | filters.video | filters.audio | filters.photo) & filters.private, group=1)
async def clone_file_upload(client, message):
    if not LOG_CHANNEL:
        return await message.reply("<b>❌ Fɪʟᴇ sᴛᴏʀᴀɢᴇ ɴᴏᴛ ᴄᴏɴғɪɢᴜʀᴇᴅ!</b>")
    bot_info = await client.get_me()
    bot_id = bot_info.id
    settings = await get_clone_settings(bot_id)
    mode = settings.get('mode', 'public') if settings else 'public'
    moderators = settings.get('moderators', []) if settings else []
    if mode == 'private' and DB_LOADED:
        clone = await clone_db.get_clone(bot_id)
        owner_id = clone.get('user_id') if clone else None
        if message.from_user.id not in moderators and message.from_user.id != owner_id:
            return await message.reply("<b>⚠️ This bot is in private mode!</b>")
    try:
        processing = await message.reply("<b>⏳ Pʀᴏᴄᴇssɪɴɢ ʏᴏᴜʀ ғɪʟᴇ...</b>")
        post = await message.copy(LOG_CHANNEL)
        file_id = str(post.id)
        bot_username = bot_info.username
        string = f'file_{file_id}'
        encoded = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
        share_link = f"https://t.me/{bot_username}?start={encoded}"
        await processing.delete()
        buttons = [
            [InlineKeyboardButton('🔗 Sʜᴀʀᴇ Lɪɴᴋ', url=share_link)],
            [InlineKeyboardButton('📋 Cᴏᴘʏ Lɪɴᴋ', callback_data='clone_start')]
        ]
        await message.reply(
            f"<b>✅ Fɪʟᴇ Sᴛᴏʀᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ!</b>\n🔗 <b>Sʜᴀʀᴇᴀʙʟᴇ Lɪɴᴋ:</b>\n<code>{share_link}</code>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await clone_file_upload(client, message)
    except Exception as e:
        print(f"Clone: Upload error - {e}")
        await message.reply(f"<b>❌ Fᴀɪʟᴇᴅ ᴛᴏ ɢᴇɴᴇʀᴀᴛᴇ ʟɪɴᴋ!</b>\nError: <code>{str(e)}</code>")

@Client.on_message(filters.command("batch") & filters.private, group=1)
async def batch_handler(client, message):
    bot_info = await client.get_me()
    bot_id = bot_info.id
    settings = await get_clone_settings(bot_id)
    moderators = settings.get('
