import re
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.clone_db import clone_db

# Auto delete settings with presets, custom time, enable/disable
@Client.on_callback_query(filters.regex("^set_autodel_"))
async def set_auto_delete(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('auto_delete_seconds', 0)

    # Convert seconds to readable text
    if current == 0:
        current_text = "Disabled"
    elif current < 60:
        current_text = f"{current} sec"
    elif current < 3600:
        current_text = f"{current // 60} min"
    else:
        current_text = f"{current // 3600} hrs"

    buttons = [
        [
            InlineKeyboardButton('20 sec', callback_data=f'toggle_autodel_{bot_id}_20'),
            InlineKeyboardButton('5 min', callback_data=f'toggle_autodel_{bot_id}_300')
        ],
        [
            InlineKeyboardButton('1 hr', callback_data=f'toggle_autodel_{bot_id}_3600'),
            InlineKeyboardButton('6 hrs', callback_data=f'toggle_autodel_{bot_id}_21600')
        ],
        [
            InlineKeyboardButton('⌨️ Custom Time', callback_data=f'custom_autodel_{bot_id}'),
            InlineKeyboardButton('❌ Disable', callback_data=f'toggle_autodel_{bot_id}_0')
        ],
        [InlineKeyboardButton('✅ Enable', callback_data=f'toggle_autodel_{bot_id}_enable')],
        [InlineKeyboardButton('🔙 Back', callback_data=f'customize_{bot_id}')]
    ]

    await query.message.edit_text(
        f"<b>⏱️ Auto Delete</b>\n\nCurrent: {current_text}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# Handle preset times, Enable/Disable
@Client.on_callback_query(filters.regex("^toggle_autodel_"))
async def toggle_auto_delete(client, query: CallbackQuery):
    data = query.data.split("_")
    bot_id = int(data[2])
    value = data[3]

    if value == "enable":
        seconds = 60  # default 1 minute if enabling
        await query.answer("Auto Delete Enabled!")
    else:
        seconds = int(value)
        if seconds == 0:
            await query.answer("Auto Delete Disabled!")
        else:
            await query.answer(f"Auto Delete set to {seconds} seconds!")

    await clone_db.update_clone_setting(bot_id, 'auto_delete_seconds', seconds)
    await set_auto_delete(client, query)

# Handle custom time input
@Client.on_callback_query(filters.regex("^custom_autodel_"))
async def custom_auto_delete(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    await query.message.edit_text(
        "<b>⌨️ Send custom time for Auto Delete</b>\n\n"
        "Examples: 30 sec, 5 min, 2 hrs\n"
        "Use /cancel to cancel."
    )

    try:
        msg = await client.ask(query.message.chat.id, timeout=300)
        if msg.text.lower() == "/cancel":
            return await query.message.edit_text("Cancelled!")

        # Parse input
        match = re.match(r"(\d+)\s*(sec|s|min|m|hr|h)", msg.text.lower())
        if not match:
            return await query.message.edit_text("Invalid format! Use e.g., 30 sec, 5 min, 2 hrs.")

        number, unit = match.groups()
        number = int(number)
        if unit in ["sec", "s"]:
            seconds = number
        elif unit in ["min", "m"]:
            seconds = number * 60
        elif unit in ["hr", "h"]:
            seconds = number * 3600
        else:
            seconds = 0

        await clone_db.update_clone_setting(bot_id, 'auto_delete_seconds', seconds)
        await query.message.edit_text(
            f"✅ Auto Delete set to {msg.text}!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Back', callback_data=f'customize_{bot_id}')]])
        )
    except:
        await query.message.edit_text("⏰ Timeout!")
