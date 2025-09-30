from pyrogram import Client, filters
from pyrogram.types import Message
from config import ADMINS
from database.database import db
import asyncio
import logging

logger = logging.getLogger(__name__)

@Client.on_message(filters.command("users") & filters.user(ADMINS))
async def users_command(client, message: Message):
    """Get total users count"""
    total_users = await db.total_users_count()
    await message.reply(f"<b>📊 Tᴏᴛᴀʟ Usᴇʀs: {total_users}</b>")

@Client.on_message(filters.command("broadcast") & filters.user(ADMINS))
async def broadcast_command(client, message: Message):
    """Broadcast message to all users"""
    if message.reply_to_message:
        msg_to_send = message.reply_to_message
    else:
        return await message.reply(
            "<b>Rᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ!</b>"
        )
    
    users = await db.get_all_users()
    
    total_users = await db.total_users_count()
    success = 0
    failed = 0
    
    status_msg = await message.reply(
        f"<b>📢 Bʀᴏᴀᴅᴄᴀsᴛ Sᴛᴀʀᴛᴇᴅ...\n\n"
        f"Tᴏᴛᴀʟ Usᴇʀs: {total_users}\n"
        f"Sᴜᴄᴄᴇss: {success}\n"
        f"Fᴀɪʟᴇᴅ: {failed}</b>"
    )
    
    async for user in users:
        try:
            await msg_to_send.copy(chat_id=user['id'])
            success += 1
        except Exception as e:
            failed += 1
            logger.error(f"Broadcast failed for {user['id']}: {e}")
        
        if (success + failed) % 20 == 0:
            await status_msg.edit_text(
                f"<b>📢 Bʀᴏᴀᴅᴄᴀsᴛ Iɴ Pʀᴏɢʀᴇss...\n\n"
                f"Tᴏᴛᴀʟ: {total_users}\n"
                f"Sᴜᴄᴄᴇss: {success}\n"
                f"Fᴀɪʟᴇᴅ: {failed}</b>"
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
    
    user_id = int(message.command[1])
    await db.delete_user(user_id)
    await message.reply(f"<b>✅ Usᴇʀ {user_id} ʙᴀɴɴᴇᴅ!</b>")

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
    await message.reply("<b>🔄 Rᴇsᴛᴀʀᴛɪɴɢ ʙᴏᴛ...</b>")
    # Add restart logic here
    import sys
    import os
    os.execl(sys.executable, sys.executable, *sys.argv)
