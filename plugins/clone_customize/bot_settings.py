# plugins/clone_customize/bot_settings.py
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.clone_db import clone_db
# This import is needed for the new input handlers
from .input_handler import user_states

# ==================== MAIN CHANNELS MENU (UPDATED) ====================
@Client.on_callback_query(filters.regex("^channels_"))
async def channels_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    
    log_status = "✅ Set" if settings.get('log_channel') else "❌ Not Set"
    db_status = "✅ Set" if settings.get('db_channel') else "❌ Not Set"
    
    buttons = [
        # Force Subscribe button removed
        [InlineKeyboardButton(f'📝 Log Channel • {log_status}', callback_data=f'log_channel_manage_{bot_id}')],
        [InlineKeyboardButton(f'🗄️ DB Channel • {db_status}', callback_data=f'db_channel_manage_{bot_id}')],
        [InlineKeyboardButton('« Back to Customize', callback_data=f'customize_{bot_id}')]
    ]
    
    text = (
        "<b>📢 Admin Channels</b>\n\n"
        "Configure administrative channels for your bot.\n\n"
        "• <b>Log Channel:</b> Record bot activity and errors.\n"
        "• <b>DB Channel:</b> Store files sent through the bot."
    )
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# ==================== LOG CHANNEL SECTION ====================
@Client.on_callback_query(filters.regex("^log_channel_manage_"))
async def log_channel_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('log_channel')
    
    buttons = []
    text = "<b>📝 Log Channel Settings</b>\n\nBot activity will be logged here.\n\n"
    if current:
        text += f"<b>Current Channel:</b> <code>{current}</code>"
        buttons.append([InlineKeyboardButton('🔄 Change', callback_data=f'input_log_{bot_id}')])
        buttons.append([InlineKeyboardButton('🗑️ Remove', callback_data=f'remove_log_{bot_id}')])
    else:
        text += "<b>Status:</b> Not set."
        buttons.append([InlineKeyboardButton('➕ Set Channel', callback_data=f'input_log_{bot_id}')])
    
    buttons.append([InlineKeyboardButton('« Back', callback_data=f'channels_{bot_id}')])
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^input_log_"))
async def input_log(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'log_channel', 'bot_id': bot_id}
    await query.message.edit_text(
        "<b>Send the Log Channel ID or Username:</b>\n\nSend /cancel to abort.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('« Cancel', callback_data=f'log_channel_manage_{bot_id}')]])
    )

@Client.on_callback_query(filters.regex("^remove_log_"))
async def remove_log(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    await clone_db.update_clone_setting(bot_id, 'log_channel', None)
    await query.answer("✅ Log Channel removed!", show_alert=True)
    query.data = f"log_channel_manage_{bot_id}"
    await log_channel_menu(client, query)


# ==================== DB CHANNEL SECTION ====================
@Client.on_callback_query(filters.regex("^db_channel_manage_"))
async def db_channel_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('db_channel')
    
    buttons = []
    text = "<b>🗄️ DB Channel Settings</b>\n\nFiles will be stored here.\n\n"
    if current:
        text += f"<b>Current Channel:</b> <code>{current}</code>"
        buttons.append([InlineKeyboardButton('🔄 Change', callback_data=f'input_db_{bot_id}')])
        buttons.append([InlineKeyboardButton('🗑️ Remove', callback_data=f'remove_db_{bot_id}')])
    else:
        text += "<b>Status:</b> Not set."
        buttons.append([InlineKeyboardButton('➕ Set Channel', callback_data=f'input_db_{bot_id}')])
    
    buttons.append([InlineKeyboardButton('« Back', callback_data=f'channels_{bot_id}')])
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^input_db_"))
async def input_db_channel(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'db_channel', 'bot_id': bot_id}
    await query.message.edit_text(
        "<b>Send the DB Channel ID:</b>\n\nSend /cancel to abort.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('« Cancel', callback_data=f'db_channel_manage_{bot_id}')]])
    )

@Client.on_callback_query(filters.regex("^remove_db_"))
async def remove_db_channel(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    await clone_db.update_clone_setting(bot_id, 'db_channel', None)
    await query.answer("✅ DB Channel removed!", show_alert=True)
    query.data = f"db_channel_manage_{bot_id}"
    await db_channel_menu(client, query)


# ==================== BOT SETTINGS (Original Code) ====================
@Client.on_callback_query(filters.regex("^bot_settings_"))
async def bot_settings_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    
    mode = "Public" if settings.get('public_use', True) else "Private"
    maintenance = "ON" if settings.get('maintenance') else "OFF"
    
    buttons = [
        [InlineKeyboardButton(f'🔓 Mode: {mode}', callback_data=f'toggle_mode_{bot_id}')],
        [InlineKeyboardButton(f'🔧 Maintenance: {maintenance}', callback_data=f'toggle_maintenance_{bot_id}')],
        [InlineKeyboardButton('🌍 Language', callback_data=f'language_{bot_id}')],
        [InlineKeyboardButton('🕐 Timezone', callback_data=f'timezone_{bot_id}')],
        [InlineKeyboardButton('« Back', callback_data=f'customize_{bot_id}')]
    ]
    
    text = "<b>⚙️ Bot Settings</b>\n<i>General configuration</i>"
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^toggle_mode_"))
async def toggle_mode(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('public_use', True)
    
    await clone_db.update_clone_setting(bot_id, 'public_use', not current)
    await query.answer(f"✅ Mode: {'Private' if current else 'Public'}!", show_alert=True)
    query.data = f"bot_settings_{bot_id}" # Manually set data to refresh the menu
    await bot_settings_menu(client, query)

@Client.on_callback_query(filters.regex("^toggle_maintenance_"))
async def toggle_maintenance(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('maintenance', False)
    
    await clone_db.update_clone_setting(bot_id, 'maintenance', not current)
    await query.answer(f"✅ Maintenance: {'ON' if not current else 'OFF'}!", show_alert=True)
    query.data = f"bot_settings_{bot_id}" # Manually set data to refresh the menu
    await bot_settings_menu(client, query)

# ==================== TOGGLE PUBLIC (Original Code) ====================
@Client.on_callback_query(filters.regex("^toggle_public_"))
async def toggle_public_use(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('public_use', True)
    
    await clone_db.update_clone_setting(bot_id, 'public_use', not current)
    await query.answer(f"✅ Mode: {'Private' if current else 'Public'}!", show_alert=True)
    from .main_menu import customize_clone
    await customize_clone(client, query)

# ==================== RESTART BOT (Original Code) ====================
@Client.on_callback_query(filters.regex("^restart_"))
async def restart_clone(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    await query.answer("🔄 Restart feature coming soon!", show_alert=True)

# ==================== DEACTIVATE (Original Code) ====================
@Client.on_callback_query(filters.regex("^deactivate_"))
async def deactivate_clone(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    buttons = [
        [InlineKeyboardButton('✅ Yes', callback_data=f'confirm_deactivate_{bot_id}')],
        [InlineKeyboardButton('❌ No', callback_data=f'customize_{bot_id}')]
    ]
    await query.message.edit_text("<b>⚠️ Deactivate Clone?</b>\n\nBot will stop temporarily", reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^confirm_deactivate_"))
async def confirm_deactivate(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    await clone_db.update_clone_setting(bot_id, 'is_active', False)
    await query.answer("✅ Deactivated!", show_alert=True)
    from .main_menu import customize_clone
    await customize_clone(client, query)

# ==================== DELETE (Original Code) ====================
@Client.on_callback_query(filters.regex("^delete_(?!clone)"))
async def delete_clone_confirm(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    buttons = [
        [InlineKeyboardButton('✅ Yes, Delete', callback_data=f'confirm_delete_{bot_id}')],
        [InlineKeyboardButton('❌ No', callback_data=f'customize_{bot_id}')]
    ]
    await query.message.edit_text("<b>⚠️ DELETE CLONE?</b>\n\nThis action cannot be undone!", reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^confirm_delete_"))
async def confirm_delete_clone(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    if clone['user_id'] != query.from_user.id:
        return await query.answer("Access denied!", show_alert=True)
    await clone_db.delete_clone_by_id(bot_id)
    await query.message.edit_text("<b>✅ Clone Deleted!</b>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('« Back', callback_data='clone')]]))
