import asyncio
from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import LOG_CHANNEL, AUTO_DELETE_MODE, AUTO_DELETE, AUTO_DELETE_TIME, STREAM_MODE, URL
from urllib.parse import quote_plus
import logging

logger = logging.getLogger(__name__)

def get_file_name(msg):
    if msg.document:
        return msg.document.file_name
    elif msg.video:
        return msg.video.file_name or "video.mp4"
    elif msg.audio:
        return msg.audio.file_name or "audio.mp3"
    elif msg.photo:
        return "photo.jpg"
    return "file"

def format_file_name(name):
    if len(name) > 60:
        return name[:57] + "..."
    return name

def get_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

def get_hash(msg):
    return str(abs(hash(str(msg.id))))

async def send_file(client: Client, message, file_id: int):
    try:
        msg = await client.get_messages(LOG_CHANNEL, file_id)
        if not msg or not msg.media:
            return await message.reply("❌ File not found or deleted!")

        # Safely get media object
        if msg.document:
            media = msg.document
        elif msg.video:
            media = msg.video
        elif msg.audio:
            media = msg.audio
        elif msg.photo:
            media = msg.photo
        else:
            media = None

        file_name = format_file_name(get_file_name(msg))
        file_size = get_size(media.file_size) if media and hasattr(media, 'file_size') else "Unknown"

        caption = f"<b>📁 {file_name}</b>\n<b>📊 {file_size}</b>"

        reply_markup = None
        if STREAM_MODE and (msg.video or msg.document):
            stream_url = f"{URL}watch/{file_id}/{quote_plus(get_file_name(msg))}?hash={get_hash(msg)}"
            download_url = f"{URL}{file_id}/{quote_plus(get_file_name(msg))}?hash={get_hash(msg)}"
            buttons = [[
                InlineKeyboardButton("⬇️ ᴅᴏᴡɴʟᴏᴀᴅ", url=download_url),
                InlineKeyboardButton('▶️ ᴡᴀᴛᴄʜ', url=stream_url)
            ]]
            reply_markup = InlineKeyboardMarkup(buttons)

        sent_msg = await msg.copy(
            chat_id=message.from_user.id,
            caption=caption,
            reply_markup=reply_markup
        )

        if AUTO_DELETE_MODE:
            warning = await message.reply(
                f"<b>⚠️ IMPORTANT</b>\n\n"
                f"This file will be deleted in <b>{AUTO_DELETE} minutes</b> due to copyright.\n\n"
                f"Please forward it to Saved Messages to keep it!"
            )
            await asyncio.sleep(AUTO_DELETE_TIME)
            try:
                await sent_msg.delete()
                await warning.edit_text("✅ File deleted successfully!")
            except Exception as e:
                logger.warning(f"Could not delete file or edit warning: {e}")
                await warning.edit_text("⚠️ Could not delete the file.")

        return True
    except Exception as e:
        logger.error(f"Error sending file: {e}")
        await message.reply("❌ An error occurred while sending the file.")
        return False
