# plugins/clone_customize.py
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.clone_db import clone_db
from Script import script
import logging

logger = logging.getLogger(__name__)

# Store user states for multi-step processes
user_states = {}

# -----------------------------
# Main Customize Menu
# -----------------------------
@Client.on_callback_query(filters.regex("^customize_"))
async def customize_clone(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    clone = await clone_db.get_clone(bot_id)
    if not clone:
        return await query.answer("Clone not found!", show_alert=True)
    if clone['user_id'] != query.from_user.id:
        return await query.answer("This is not your clone!", show_alert=True)

    settings = clone.get('settings', {})
    buttons = [
        [InlineKeyboardButton('START TEXT', callback_data=f'set_start_text_{bot_id}'),
         InlineKeyboardButton('START PICTURE', callback_data=f'set_start_pic_{bot_id}')],
        [InlineKeyboardButton('START BUTTON', callback_data=f'set_start_btn_{bot_id}'),
         InlineKeyboardButton('FORCE SUBSCRIBE', callback_data=f'set_fsub_{bot_id}')],
        [InlineKeyboardButton('MONGO DB', callback_data=f'set_mongo_{bot_id}'),
         InlineKeyboardButton('LOG CHANNEL', callback_data=f'set_log_{bot_id}')],
        [InlineKeyboardButton('ADMINS', callback_data=f'set_admins_{bot_id}'),
         InlineKeyboardButton('BOT STATUS', callback_data=f'bot_status_{bot_id}')],
        [InlineKeyboardButton('DATABASE CHANNEL', callback_data=f'set_db_channel_{bot_id}'),
         InlineKeyboardButton('RESTART BOT', callback_data=f'restart_{bot_id}')],
        [InlineKeyboardButton(f"🔒 PUBLIC USE - {'✅' if settings.get('public_use', True) else '❌'}",
                               callback_data=f'toggle_public_{bot_id}')],
        [InlineKeyboardButton('AUTO DELETE', callback_data=f'auto_delete_menu_{bot_id}')],
        [InlineKeyboardButton('DEACTIVATE BOT', callback_data=f'deactivate_{bot_id}'),
         InlineKeyboardButton('DELETE BOT', callback_data=f'delete_clone_{bot_id}')],
        [InlineKeyboardButton('⬅️ BACK', callback_data='clone')]
    ]

    await query.message.edit_text(
        f"<b>🤖 YOUR CLONE BOT - @{clone['username']}</b>\n\n"
        f"📝 Configure your clone from here.\n"
        f"⏰ Last used: {clone.get('last_used', 'Never')}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# -----------------------------
# Auto Delete Menu
# -----------------------------
@Client.on_callback_query(filters.regex("^auto_delete_menu_"))
async def auto_delete_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[-1])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    auto_del_enabled = settings.get('auto_delete', False)
    auto_del_time = settings.get('auto_delete_time', 300)
    time_display = f"{auto_del_time//60}m {auto_del_time%60}s" if auto_del_time >= 60 else f"{auto_del_time}s"

    buttons = [
        [InlineKeyboardButton('✅ ENABLE' if not auto_del_enabled else '❌ DISABLE', callback_data=f'toggle_autodel_{bot_id}')],
        [InlineKeyboardButton('CUSTOM TIME', callback_data=f'custom_del_time_{bot_id}')],
        [InlineKeyboardButton('⬅️ BACK', callback_data=f'customize_{bot_id}')]
    ]
    status_text = f"<b>🗑️ AUTO DELETE SETTINGS</b>\n\nStatus: {'ENABLED ✅' if auto_del_enabled else 'DISABLED ❌'}\nDelete Time: {time_display}"
    await query.message.edit_text(status_text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^toggle_autodel_"))
async def toggle_auto_delete(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[-1])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('auto_delete', False)
    new_status = not current
    await clone_db.update_clone_setting(bot_id, 'auto_delete', new_status)
    await query.answer(f"Auto Delete: {'✅ Enabled' if new_status else '❌ Disabled'}", show_alert=True)
    await auto_delete_menu(client, query)

@Client.on_callback_query(filters.regex("^custom_del_time_"))
async def custom_delete_time(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[-1])
    user_states[query.from_user.id] = {'action': 'custom_del_time', 'bot_id': bot_id}
    await query.message.edit_text(
        "<b>⏰ ENTER CUSTOM DELETE TIME</b>\n\nSend time in seconds (min 20)\nSend /cancel to stop.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ CANCEL', callback_data=f'auto_delete_menu_{bot_id}')]])
    )
    await query.answer()

# -----------------------------
# Toggle Public Use
# -----------------------------
@Client.on_callback_query(filters.regex("^toggle_public_"))
async def toggle_public_use(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[-1])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('public_use', True)
    new_status = not current
    await clone_db.update_clone_setting(bot_id, 'public_use', new_status)
    await query.answer(f"Public Use: {'✅ Enabled' if new_status else '❌ Disabled'}", show_alert=True)
    await customize_clone(client, query)

# -----------------------------
# Start Text, Picture, Button
# -----------------------------
@Client.on_callback_query(filters.regex("^set_start_text_"))
async def set_start_text(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[-1])
    user_states[query.from_user.id] = {'action': 'start_text', 'bot_id': bot_id}
    await query.message.edit_text("📝 Send your custom start text\nSend /cancel to stop.", 
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ CANCEL', callback_data=f'customize_{bot_id}')]]))
    await query.answer()

@Client.on_callback_query(filters.regex("^set_start_pic_"))
async def set_start_picture(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[-1])
    user_states[query.from_user.id] = {'action': 'start_pic', 'bot_id': bot_id}
    await query.message.edit_text("🖼️ Send photo or URL\nSend /remove to delete\nSend /cancel to stop.",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ CANCEL', callback_data=f'customize_{bot_id}')]]))
    await query.answer()

@Client.on_callback_query(filters.regex("^set_start_btn_"))
async def set_start_button(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[-1])
    user_states[query.from_user.id] = {'action': 'start_button', 'bot_id': bot_id}
    await query.message.edit_text("🔘 Send button text and URL as:\nButton Text - https://example.com\nSend /remove to remove\n/cancel to stop.",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ CANCEL', callback_data=f'customize_{bot_id}')]]))
    await query.answer()

# -----------------------------
# Force Sub
# -----------------------------
@Client.on_callback_query(filters.regex("^set_fsub_"))
async def force_sub_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[-1])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    fsub_channels = settings.get('force_sub_channels', [])

    buttons = [[InlineKeyboardButton(c, callback_data='none')] for c in fsub_channels[:6]] or [[InlineKeyboardButton('No channels', callback_data='none')]]
    if len(fsub_channels) < 6:
        buttons.append([InlineKeyboardButton('➕ ADD CHANNEL', callback_data=f'add_fsub_{bot_id}')])
    buttons.append([InlineKeyboardButton('⬅️ BACK', callback_data=f'customize_{bot_id}')])
    await query.message.edit_text(f"🔒 FORCE SUBSCRIBE CHANNELS\nTotal: {len(fsub_channels)}/6", reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^add_fsub_"))
async def add_force_sub(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[-1])
    user_states[query.from_user.id] = {'action': 'add_fsub', 'bot_id': bot_id}
    await query.message.edit_text("📢 Send channel username or ID\n/cancel to stop.",
                                  reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ CANCEL', callback_data=f'set_fsub_{bot_id}')]]))
    await query.answer()

# -----------------------------
# Handle User Input
# -----------------------------
@Client.on_message(filters.private & filters.text)
async def handle_setting_input(client, message):
    user_id = message.from_user.id
    if user_id not in user_states: return
    state = user_states[user_id]
    bot_id = state['bot_id']
    action = state['action']

    if message.text == '/cancel':
        del user_states[user_id]
        await message.reply("❌ Cancelled!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('⬅️ BACK', callback_data=f'customize_{bot_id}')]]))
        return

    if action == 'start_text':
        await clone_db.update_clone_setting(bot_id, 'start_message', message.text)
    elif action == 'start_pic':
        await clone_db.update_clone_setting(bot_id, 'start_photo', message.text if message.text.startswith('http') else None)
    elif action == 'start_button':
        await clone_db.update_clone_setting(bot_id, 'start_button', message.text)
    elif action == 'add_fsub':
        clone = await clone_db.get_clone(bot_id)
        fsub_channels = clone.get('settings', {}).get('force_sub_channels', [])
        if message.text not in fsub_channels: fsub_channels.append(message.text)
        await clone_db.update_clone_setting(bot_id, 'force_sub_channels', fsub_channels)
    elif action == 'custom_del_time':
        time_sec = max(20, int(message.text))
        await clone_db.update_clone_setting(bot_id, 'auto_delete_time', time_sec)

    del user_states[user_id]
    await message.reply("✅ Updated!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('⬅️ BACK', callback_data=f'customize_{bot_id}')]]))

logger.info("✅ Clone customization module loaded")
