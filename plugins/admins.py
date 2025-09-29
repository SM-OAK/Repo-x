import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from config import ADMINS
from database.database import db

logger = logging.getLogger("Admins")

# 📊 Show total users
@Client.on_message(filters.command("users") & filters.user(ADMINS))
async def users_command(client, message: Message):
    try:
        total_users = await db.total_users_count()
        await message.reply(f"<b>📊 Total Users: {total_users}</b>")
    except Exception as e:
        logger.error(f"Error fetching user count: {e}", exc_info=True)
        await message.reply("❌ Failed to fetch user count.")


# 📢 Broadcast a message
@Client.on_message(filters.command("broadcast") & filters.user(ADMINS))
async def broadcast_command(client, message: Message):
    if not message.reply_to_message:
        return await message.reply("<b>Reply to a message to broadcast!</b>")

    users = await db.get_all_users()
    if not users:
        return await message.reply("⚠️ No users found in database.")

    total_users = len(users)
    success, failed = 0, 0

    status_msg = await message.reply(
        f"<b>📢 Broadcast Started...\n\n"
        f"Total Users: {total_users}\n"
        f"✅ Success: {success}\n"
        f"❌ Failed: {failed}</b>"
    )

    for user_id in users:
        try:
            await message.reply_to_message.copy(chat_id=user_id)
            success += 1
        except Exception as e:
            failed += 1
            logger.error(f"Broadcast failed for {user_id}: {e}")

        if (success + failed) % 20 == 0:  # update every 20 users
            try:
                await status_msg.edit_text(
                    f"<b>📢 Broadcast In Progress...\n\n"
                    f"Total: {total_users}\n"
                    f"✅ Success: {success}\n"
                    f"❌ Failed: {failed}</b>"
                )
            except:
                pass

    await status_msg.edit_text(
        f"<b>✅ Broadcast Completed!\n\n"
        f"Total: {total_users}\n"
        f"✅ Success: {success}\n"
        f"❌ Failed: {failed}</b>"
    )


# 🔨 Ban a user
@Client.on_message(filters.command("ban") & filters.user(ADMINS))
async def ban_user(client, message: Message):
    if len(message.command) < 2:
        return await message.reply("<b>Usage: /ban user_id</b>")

    try:
        user_id = int(message.command[1])
        if hasattr(db, "delete_user"):
            await db.delete_user(user_id)
        await message.reply(f"<b>✅ User {user_id} banned successfully.</b>")
    except Exception as e:
        logger.error(f"Ban failed: {e}", exc_info=True)
        await message.reply("❌ Failed to ban user.")


# 📈 Bot statistics
@Client.on_message(filters.command("stats") & filters.user(ADMINS))
async def stats_command(client, message: Message):
    try:
        total_users = await db.total_users_count()
        stats_text = (
            f"<b>📊 Bot Statistics</b>\n\n"
            f"👥 Total Users: {total_users}\n"
            f"🤖 Bot: @{client.me.username}\n"
            f"📛 Bot Name: {client.me.first_name}"
        )
        await message.reply(stats_text)
    except Exception as e:
        logger.error(f"Stats failed: {e}", exc_info=True)
        await message.reply("❌ Failed to fetch stats.")


# 🔄 Restart the bot
@Client.on_message(filters.command("restart") & filters.user(ADMINS))
async def restart_bot(client, message: Message):
    await message.reply("<b>🔄 Restarting bot...</b>")
    import os
    import sys
    try:
        os.execl(sys.executable, sys.executable, *sys.argv)
    except Exception as e:
        logger.error(f"Restart failed: {e}", exc_info=True)
        await message.reply("❌ Restart failed.")
