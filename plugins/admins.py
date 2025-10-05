from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from config import ADMINS
from database.database import db
import asyncio
import logging
import sys
import os

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("users") & filters.user(ADMINS))
async def users_command(client, message: Message):
    """Get total users count"""
    total_users = await db.total_users_count()
    await message.reply(f"<b>📊 Tᴏᴛᴀʟ Usᴇʀs: {total_users}</b>")

@Client.on_message(filters.command("broadcast") & filters.user(ADMINS))
async def broadcast_command(client, message: Message):
    """Broadcast message to all users"""
    if not message.reply_to_message:
        return await message.reply(
            "<b>Rᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ!</b>"
        )
    
    msg_to_send = message.reply_to_message
    users = await db.get_all_users()
    total_users = await db.total_users_count()
    success = 0
    failed = 0
    
    status_msg = await message.reply(
        f"<b>📢 Bʀᴏᴀᴅᴄᴀsᴛ Sᴛᴀʀᴛᴇᴅ...\n\n"
        f"Tᴏᴛᴀʟ Usᴇʀs: {total_users}</b>"
    )
    
    async for user in users:
        try:
            await msg_to_send.copy(chat_id=user['id'])
            success += 1
        except FloodWait as e:
            # Handle rate limits
            await asyncio.sleep(e.value)
            await msg_to_send.copy(chat_id=user['id'])
            success += 1
        except Exception:
            failed += 1
        
        # Edit status message less frequently to avoid hitting API limits
        if (success + failed) % 100 == 0 or (success + failed) == total_users:
            await status_msg.edit_text(
                f"<b>📢 Bʀᴏᴀᴅᴄᴀsᴛ Iɴ Pʀᴏɢʀᴇss...\n\n"
                f"Tᴏᴛᴀʟ: {total_users}\n"
                f"✅ Sᴜᴄᴄᴇss: {success}\n"
                f"❌ Fᴀɪʟᴇᴅ: {failed}</b>"
            )
    
    await status_msg.edit_text(
        f"<b>✅ Bʀᴏᴀᴅᴄᴀsᴛ Cᴏᴍᴘʟᴇᴛᴇᴅ!\n\n"
        f"Tᴏᴛᴀʟ: {total_users}\n"
        f"Sᴜᴄᴄᴇss: {success}\n"
        f"Fᴀɪʟᴇᴅ: {failed}</b>"
    )

@Client.on_message(filters.command("ban") & filters.user(ADMINS))
async def ban_user(client, message: Message):
    """Ban a user from using the bot"""
    if len(message.command) < 2:
        return await message.reply("<b>Usᴀɢᴇ: /ban user_id</b>")
    
    try:
        user_id = int(message.command[1])
        await db.delete_user(user_id)
        await message.reply(f"<b>✅ Usᴇʀ {user_id} ʙᴀɴɴᴇᴅ!</b>")
    except (ValueError, IndexError):
        await message.reply("<b>Invalid user ID format.</b>")

@Client.on_message(filters.command("stats") & filters.user(ADMINS))
async def stats_command(client, message: Message):
    """Get detailed bot statistics"""
    total_users = await db.total_users_count()
    
    stats_text = (
        f"<b>📊 Bᴏᴛ Sᴛᴀᴛɪsᴛɪᴄs</b>\n\n"
        f"👥 Tᴏᴛᴀʟ Usᴇʀs: {total_users}\n"
        f"🤖 Bᴏᴛ: @{client.me.username}\n"
        f"📛 Bᴏᴛ Nᴀᴍᴇ: {client.me.first_name}"
    )
    
    await message.reply(stats_text)

@Client.on_message(filters.command("restart") & filters.user(ADMINS))
async def restart_bot(client, message: Message):
    """Restart the bot"""
    await message.reply("<b>✅ Sᴇɴᴛ ʀᴇsᴛᴀʀᴛ ᴄᴏᴍᴍᴀɴᴅ... Bᴏᴛ ɪs ʀᴇsᴛᴀʀᴛɪɴɢ.</b>")
    # This is a more forceful restart method that works without a process manager
    os.execl(sys.executable, sys.executable, *sys.argv)

