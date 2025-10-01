# clone_plugins/forcesub.py
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from config import FORCE_SUB_CHANNEL

# ───────────────────────────────
# 📌 FORCE SUBSCRIBE CHECK
# ───────────────────────────────
async def check_force_sub(client, user_id):
    """Check if user joined the force-sub channel"""
    try:
        member = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
    except UserNotParticipant:
        return False
    except Exception as e:
        print(f"ForceSub Error: {e}")
        return True  # Fallback → don’t block
    return False


# ───────────────────────────────
# 📌 START HANDLER WITH FORCE-SUB
# ───────────────────────────────
@Client.on_message(filters.command("start"))
async def start_handler(client, message):
    user_id = message.from_user.id

    # Check force-subscribe
    is_joined = await check_force_sub(client, user_id)
    if not is_joined:
        invite_link = (await client.get_chat(FORCE_SUB_CHANNEL)).invite_link
        return await message.reply(
            "🚨 <b>You must join our channel to use the bot!</b>",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("📢 Join Channel", url=invite_link)],
                    [InlineKeyboardButton("✅ Refresh", callback_data="refresh_fsub")]
                ]
            )
        )

    # If passed → normal start message
    await message.reply("✅ Welcome! You have access to the bot.")


# ───────────────────────────────
# 📌 REFRESH BUTTON HANDLER
# ───────────────────────────────
@Client.on_callback_query(filters.regex("^refresh_fsub$"))
async def refresh_fsub(client, query):
    user_id = query.from_user.id
    is_joined = await check_force_sub(client, user_id)

    if is_joined:
        await query.message.edit_text("✅ Access granted! You can now use the bot.")
    else:
        await query.answer("🚨 You haven’t joined yet!", show_alert=True)
