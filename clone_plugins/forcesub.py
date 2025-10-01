# clone_plugins/forcesub.py
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from database.clone_db import clone_db

# ───────────────────────────────
# 📌 FORCE SUBSCRIBE CHECK
# ───────────────────────────────
async def check_force_sub(client, user_id):
    """Check if user joined the clone's force-sub channel"""
    # Get clone bot ID from current client
    bot_id = client.me.id  
    clone = await clone_db.get_clone(bot_id)
    
    force_channel = clone.get("force_sub_channel")  # stored in DB
    if not force_channel:
        return True  # No force-sub set → allow

    try:
        member = await client.get_chat_member(force_channel, user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
    except UserNotParticipant:
        return False
    except Exception as e:
        print(f"ForceSub Error ({bot_id}): {e}")
        return True  # fallback: don’t block
    return False


# ───────────────────────────────
# 📌 START HANDLER WITH FORCE-SUB
# ───────────────────────────────
@Client.on_message(filters.command("start"))
async def start_handler(client, message):
    user_id = message.from_user.id
    bot_id = client.me.id
    clone = await clone_db.get_clone(bot_id)

    is_joined = await check_force_sub(client, user_id)
    if not is_joined:
        try:
            invite_link = (await client.get_chat(clone["force_sub_channel"])).invite_link
        except Exception:
            invite_link = f"https://t.me/{clone['force_sub_channel'].strip('@')}"

        return await message.reply(
            f"🚨 <b>You must join our channel to use {clone['name']}!</b>",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("📢 Join Channel", url=invite_link)],
                    [InlineKeyboardButton("✅ Refresh", callback_data="refresh_fsub")]
                ]
            )
        )

    # If passed → normal start message
    await message.reply(f"✅ Welcome! You have access to <b>{clone['name']}</b>.")


# ───────────────────────────────
# 📌 REFRESH BUTTON HANDLER
# ───────────────────────────────
@Client.on_callback_query(filters.regex("^refresh_fsub$"))
async def refresh_fsub(client, query):
    user_id = query.from_user.id
    bot_id = client.me.id
    clone = await clone_db.get_clone(bot_id)

    is_joined = await check_force_sub(client, user_id)
    if is_joined:
        await query.message.edit_text(f"✅ Access granted! You can now use <b>{clone['name']}</b>.")
    else:
        await query.answer("🚨 You haven’t joined yet!", show_alert=True)
