from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.clone_db import clone_db
from Script import script
import logging

# If you want to use client.ask, you MUST install pyromod
# pip install pyromod
from pyromod.listen import Client as PyroClient  

logger = logging.getLogger(__name__)

# --- Customize clone menu ---
@Client.on_callback_query(filters.regex(r"^customize_(\d+)$"))
async def customize_clone(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    clone = await clone_db.get_clone(bot_id)

    if not clone:
        return await query.answer("Clone not found!", show_alert=True)

    if clone["user_id"] != query.from_user.id:
        return await query.answer("This is not your clone!", show_alert=True)

    buttons = [
        [
            InlineKeyboardButton("📝 Start Msg", callback_data=f"set_start_{bot_id}"),
            InlineKeyboardButton("🔒 Force Sub", callback_data=f"set_fsub_{bot_id}")
        ],
        [
            InlineKeyboardButton("👥 Moderators", callback_data=f"set_mods_{bot_id}"),
            InlineKeyboardButton("⏱️ Auto Delete", callback_data=f"set_autodel_{bot_id}")
        ],
        [
            InlineKeyboardButton("🚫 No Forward", callback_data=f"set_nofw_{bot_id}"),
            InlineKeyboardButton("🔑 Access Token", callback_data=f"view_token_{bot_id}")
        ],
        [
            InlineKeyboardButton("🔄 Mode", callback_data=f"set_mode_{bot_id}"),
            InlineKeyboardButton("❌ Deactivate", callback_data=f"deactivate_{bot_id}")
        ],
        [
            InlineKeyboardButton("📊 Stats", callback_data=f"clone_stats_{bot_id}"),
            InlineKeyboardButton("🔄 Restart", callback_data=f"restart_{bot_id}")
        ],
        [
            InlineKeyboardButton("🔙 Back", callback_data="clone"),
            InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_{bot_id}")
        ]
    ]

    text = (
        f"<b>🛠️ Customize Clone</b>\n\n"
        f"➜ <b>Name:</b> {clone['name']}\n"
        f"➜ <b>Username:</b> @{clone['username']}\n\n"
        f"Configure your clone settings below:"
    )
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))


# --- Start message setting ---
@Client.on_callback_query(filters.regex(r"^set_start_(\d+)$"))
async def set_start_msg(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    await query.message.edit_text(
        "<b>📝 Send your custom start message:</b>\n\nUse /cancel to cancel."
    )

    try:
        msg = await client.ask(query.message.chat.id, timeout=300)
        if msg.text == "/cancel":
            return await query.message.edit_text("❌ Cancelled!")

        await clone_db.update_clone_setting(bot_id, "start_message", msg.text)
        await query.message.edit_text(
            "✅ Start message updated!",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Back", callback_data=f"customize_{bot_id}")]]
            )
        )
    except asyncio.TimeoutError:
        await query.message.edit_text("⏳ Timeout! Please try again.")


# --- Force sub setting ---
@Client.on_callback_query(filters.regex(r"^set_fsub_(\d+)$"))
async def set_force_sub(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    await query.message.edit_text(
        "<b>🔒 Send channel ID:</b>\nExample: <code>-100123456789</code>\n\nUse /cancel to cancel."
    )

    try:
        msg = await client.ask(query.message.chat.id, timeout=300)
        if msg.text == "/cancel":
            return await query.message.edit_text("❌ Cancelled!")

        await clone_db.update_clone_setting(bot_id, "force_sub_channel", int(msg.text))
        await query.message.edit_text(
            "✅ Force subscription updated!",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Back", callback_data=f"customize_{bot_id}")]]
            )
        )
    except (ValueError, asyncio.TimeoutError):
        await query.message.edit_text("⚠️ Invalid ID or Timeout!")


# --- Auto delete toggle ---
@Client.on_callback_query(filters.regex(r"^set_autodel_(\d+)$"))
async def set_auto_delete(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get("settings", {}).get("auto_delete", False)

    buttons = [
        [
            InlineKeyboardButton(
                "✅ Enable" if not current else "✅ Enabled",
                callback_data=f"toggle_autodel_{bot_id}_true",
            ),
            InlineKeyboardButton(
                "❌ Disable" if current else "❌ Disabled",
                callback_data=f"toggle_autodel_{bot_id}_false",
            ),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data=f"customize_{bot_id}")],
    ]

    await query.message.edit_text(
        f"<b>⏱️ Auto Delete</b>\n\nCurrent: {'Enabled' if current else 'Disabled'}",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


@Client.on_callback_query(filters.regex(r"^toggle_autodel_(\d+)_(true|false)$"))
async def toggle_auto_delete(client, query: CallbackQuery):
    _, _, bot_id, status = query.data.split("_")
    bot_id = int(bot_id)
    status = status == "true"

    await clone_db.update_clone_setting(bot_id, "auto_delete", status)
    await query.answer(f"{'Enabled' if status else 'Disabled'}!")
    await set_auto_delete(client, query)


# --- Clone stats ---
@Client.on_callback_query(filters.regex(r"^clone_stats_(\d+)$"))
async def clone_stats(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    users = await clone_db.get_clone_users_count(bot_id)

    await query.message.edit_text(
        f"<b>📊 Clone Stats</b>\n\n"
        f"🤖 Bot: @{clone['username']}\n"
        f"👥 Users: {users}\n"
        f"📅 Created: {clone.get('created_at', 'N/A')}",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Back", callback_data=f"customize_{bot_id}")]]
        ),
    )


# --- Restart clone ---
@Client.on_callback_query(filters.regex(r"^restart_(\d+)$"))
async def restart_clone(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    await query.answer("🔄 Restarting clone...", show_alert=True)
    # TODO: Add actual restart logic


# --- Delete clone confirm ---
@Client.on_callback_query(filters.regex(r"^delete_(\d+)$"))
async def delete_clone_confirm(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])

    buttons = [
        [
            InlineKeyboardButton("✅ Yes", callback_data=f"confirm_delete_{bot_id}"),
            InlineKeyboardButton("❌ No", callback_data=f"customize_{bot_id}"),
        ]
    ]

    await query.message.edit_text(
        "⚠️ <b>Are you sure?</b>\n\nThis will permanently delete your clone!",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


@Client.on_callback_query(filters.regex(r"^confirm_delete_(\d+)$"))
async def confirm_delete_clone(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)

    if clone["user_id"] != query.from_user.id:
        return await query.answer("🚫 Access denied!", show_alert=True)

    await clone_db.delete_clone_by_id(bot_id)
    await query.message.edit_text("✅ Clone deleted successfully!")
