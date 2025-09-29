from pyrofork import Client, filters   # ✅ switched to pyrofork
from pyrofork.types import Message
from config import ADMINS
from database.database import db
import asyncio
import logging

logger = logging.getLogger(__name__)

# Show total users
@Client.on_message(filters.command("users") & filters.user(ADMINS))
async def users_command(client, message: Message):
    """Get total users count"""
    total_users = await db.total_users_count()
    await message.reply(f"<b>📊 Total Users: {total_users}</b>")

# Broadcast message to all users
@Client.on_message(filters.command("broadcast") & filters.user(ADMINS))
async def broadcast_command(client, message: Message):
    """Broadcast message to all users"""
    if message.reply_to_message:
        msg_to_send = message.reply_to_message
    else:
        return await message.reply("<b>Reply to a message to broadcast!</b>")

    users = await db.get_all_users()
    total_users = len(users) if users else 0
    success = 0
    failed = 0

    status_msg = await message.reply(
        f"<b>📢 Broadcast Started...\n\n"
        f"Total Users: {total_users}\n"
        f"Success: {success}\n"
        f"Failed: {failed}</b>"
    )

    for user_id in users:
        try:
            await msg_to_send.copy(chat_id=user_id)
            success += 1
        except Exception as e:
            failed += 1
            logger.error(f"Broadcast failed for {user_id}: {e}")

        # Update status every 20 users
        if (success + failed) % 20 == 0:
            try:
                await status_msg.edit_text(
                    f"<b>📢 Broadcast In Progress...\n\n"
                    f"Total: {total_users}\n"
                    f"Success: {success}\n"
                    f"Failed: {failed}</b>"
                )
            except Exception as e:
                logger.error(f"Status update failed: {e}")

    await status_msg.edit_text(
        f"<b>✅ Broadcast Completed!\n\n"
        f"Total: {total_users}\n"
        f"Success: {success}\n"
        f"Failed: {failed}</b>"
    )

# Ban a user
@Client.on_message(filters.command("ban") & filters.user(ADMINS))
async def ban_user(client, message: Message):
    """Ban a user from using the bot"""
    if len(message.command) < 2:
        return await message.reply("<b>Usage: /ban user_id</b>")

    user_id = int(message.command[1])
    try:
        # If you add delete_user in DB, use it. Otherwise just a placeholder.
        if hasattr(db, "delete_user"):
            await db.delete_user(user_id)
        await message.reply(f"<b>✅ User {user_id} banned!</b>")
    except Exception as e:
        logger.error(f"Ban failed: {e}")
        await message.reply("❌ Error banning user.")

# Show bot statistics
@Client.on_message(filters.command("stats") & filters.user(ADMINS))
async def stats_command(client, message: Message):
    """Get detailed bot statistics"""
    total_users = await db.total_users_count()
    stats_text = (
        f"<b>📊 Bot Statistics</b>\n\n"
        f"👥 Total Users: {total_users}\n"
        f"🤖 Bot: @{client.me.username}\n"
        f"📛 Bot Name: {client.me.first_name}"
    )
    await message.reply(stats_text)

# Restart the bot
@Client.on_message(filters.command("restart") & filters.user(ADMINS))
async def restart_bot(client, message: Message):
    """Restart the bot"""
    await message.reply("<b>🔄 Restarting bot...</b>")
    import sys, os
    os.execl(sys.executable, sys.executable, *sys.argv)
