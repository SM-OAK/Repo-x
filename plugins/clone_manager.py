import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMINS

logger = logging.getLogger("CloneManager")

# Track active clone tasks {user_id: asyncio.Task}
active_clones = {}

# 🔹 Start clone process
@Client.on_message(filters.command("clone") & filters.user(ADMINS))
async def clone_command(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply("<b>Usage: /clone user_id</b>")

    try:
        user_id = int(message.command[1])

        if user_id in active_clones:
            return await message.reply(f"⚠️ Clone for user {user_id} is already running.")

        status_msg = await message.reply(
            f"<b>🔹 Started cloning for user {user_id}...\nProgress: 0%</b>",
            reply_markup=clone_keyboard(user_id)
        )

        # Start the clone task
        task = asyncio.create_task(run_clone(client, user_id, status_msg))
        active_clones[user_id] = task

    except Exception as e:
        logger.error(f"Clone command error: {e}", exc_info=True)
        await message.reply("❌ Failed to start cloning.")


# 🔹 Clone simulation task (replace with real logic)
async def run_clone(client: Client, user_id: int, status_msg: Message):
    try:
        total_steps = 10  # Example steps
        for i in range(1, total_steps + 1):
            if user_id not in active_clones:
                await status_msg.edit(f"🛑 Clone for user {user_id} stopped!")
                return
            await asyncio.sleep(1)  # Simulate work
            progress = int((i / total_steps) * 100)
            try:
                await status_msg.edit(
                    f"<b>🔹 Cloning user {user_id}...\nProgress: {progress}%</b>",
                    reply_markup=clone_keyboard(user_id)
                )
            except:
                pass
        await status_msg.edit(f"✅ Clone for user {user_id} completed!")
    except Exception as e:
        logger.error(f"Clone task error for {user_id}: {e}", exc_info=True)
        await status_msg.edit(f"❌ Clone failed for user {user_id}.")
    finally:
        active_clones.pop(user_id, None)


# 🔹 Stop clone manually
@Client.on_message(filters.command("stopclone") & filters.user(ADMINS))
async def stop_clone(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply("<b>Usage: /stopclone user_id</b>")

    try:
        user_id = int(message.command[1])
        if user_id in active_clones:
            active_clones[user_id].cancel()
            active_clones.pop(user_id, None)
            await message.reply(f"🛑 Clone for user {user_id} stopped.")
        else:
            await message.reply(f"⚠️ No active clone for user {user_id}.")
    except Exception as e:
        logger.error(f"Stop clone error: {e}", exc_info=True)
        await message.reply("❌ Failed to stop clone.")


# 🔹 List all active clones
@Client.on_message(filters.command("clones") & filters.user(ADMINS))
async def list_clones(client: Client, message: Message):
    if not active_clones:
        return await message.reply("⚠️ No active clones found.")
    clone_text = "<b>📋 Active Clones:</b>\n"
    for idx, user_id in enumerate(active_clones.keys(), start=1):
        clone_text += f"{idx}. {user_id}\n"
    await message.reply(clone_text)


# 🔹 Inline stop button
def clone_keyboard(user_id: int):
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🛑 Stop Clone", callback_data=f"stop_{user_id}")]]
    )


# 🔹 Callback query handler for inline stop
@Client.on_callback_query(filters.regex(r"^stop_\d+$") & filters.user(ADMINS))
async def stop_clone_callback(client: Client, callback_query):
    try:
        user_id = int(callback_query.data.split("_")[1])
        if user_id in active_clones:
            active_clones[user_id].cancel()
            active_clones.pop(user_id, None)
            await callback_query.answer(f"🛑 Clone for {user_id} stopped!", show_alert=True)
        else:
            await callback_query.answer("⚠️ No active clone found.", show_alert=True)
    except Exception as e:
        logger.error(f"Callback stop clone error: {e}", exc_info=True)
        await callback_query.answer("❌ Failed to stop clone.", show_alert=True)
