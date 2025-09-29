import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMINS
from database.database import db

logger = logging.getLogger("CloneManager")

# 🔹 Start clone process for a user
@Client.on_message(filters.command("clone") & filters.user(ADMINS))
async def clone_command(client, message: Message):
    if len(message.command) < 2:
        return await message.reply("<b>Usage: /clone user_id</b>")

    try:
        user_id = int(message.command[1])
        # Check if user exists
        user = await db.get_user(user_id)
        if not user:
            return await message.reply(f"⚠️ User {user_id} not found.")

        # Start cloning process (example placeholder)
        await message.reply(
            f"<b>🔹 Started cloning for user {user_id}...</b>"
        )
        # TODO: implement actual cloning logic here

    except Exception as e:
        logger.error(f"Clone failed for {message.text}: {e}", exc_info=True)
        await message.reply("❌ Failed to start cloning.")


# 🔹 Stop clone process
@Client.on_message(filters.command("stopclone") & filters.user(ADMINS))
async def stop_clone(client, message: Message):
    if len(message.command) < 2:
        return await message.reply("<b>Usage: /stopclone user_id</b>")

    try:
        user_id = int(message.command[1])
        # TODO: implement stopping logic here
        await message.reply(f"<b>🛑 Stopped cloning for user {user_id}.</b>")
    except Exception as e:
        logger.error(f"Stop clone failed: {e}", exc_info=True)
        await message.reply("❌ Failed to stop cloning.")


# 🔹 List all active clones
@Client.on_message(filters.command("clones") & filters.user(ADMINS))
async def list_clones(client, message: Message):
    try:
        clones = await db.get_active_clones()  # assume returns list of user_ids
        if not clones:
            return await message.reply("⚠️ No active clones found.")

        clone_text = "<b>📋 Active Clones:</b>\n"
        for idx, user_id in enumerate(clones, start=1):
            clone_text += f"{idx}. {user_id}\n"

        await message.reply(clone_text)
    except Exception as e:
        logger.error(f"Listing clones failed: {e}", exc_info=True)
        await message.reply("❌ Failed to fetch active clones.")


# 🔹 Clone management keyboard (optional helper)
def clone_keyboard(user_id: int):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Stop Clone", callback_data=f"stop_{user_id}")
            ]
        ]
    )


# 🔹 Callback query handler for stopping clone via inline button
@Client.on_callback_query(filters.regex(r"^stop_\d+$") & filters.user(ADMINS))
async def stop_clone_callback(client, callback_query):
    try:
        user_id = int(callback_query.data.split("_")[1])
        # TODO: implement actual stop logic here
        await callback_query.answer(f"🛑 Clone for {user_id} stopped!", show_alert=True)
    except Exception as e:
        logger.error(f"Callback stop clone failed: {e}", exc_info=True)
        await callback_query.answer("❌ Failed to stop clone.", show_alert=True)
