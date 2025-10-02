# plugins/clone_customize/bot_settings.py
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.clone_db import clone_db

# ==================== CHANNELS ====================
@Client.on_callback_query(filters.regex("^channels_"))
async def channels_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    
    fsub = len(settings.get('force_sub_channels', []))
    log = settings.get('log_channel', 'Not set')
    db = settings.get('db_channel', 'Not set')
    
    buttons = [
        [InlineKeyboardButton(f'Force Sub ({fsub})', callback_data=f'fsub_manage_{bot_id}')],
        [InlineKeyboardButton('📝 Log Channel', callback_data=f'log_channel_{bot_id}')],
        [InlineKeyboardButton('🗄️ DB Channel', callback_data=f'db_channel_{bot_id}')],
        [InlineKeyboardButton('« Back', callback_data=f'customize_{bot_id}')]
    ]
    
    text = (
        f"<b>📢 Channels</b>\n\n"
        f"<b>Force Sub:</b> {fsub}\n"
        f"<b>Log:</b> {log}\n"
        f"<b>DB:</b> {db}"
    )
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# ==================== BOT SETTINGS ====================
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
    await bot_settings_menu(client, query)

@Client.on_callback_query(filters.regex("^toggle_maintenance_"))
async def toggle_maintenance(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('maintenance', False)
    
    await clone_db.update_clone_setting(bot_id, 'maintenance', not current)
    await query.answer(f"✅ Maintenance: {'ON' if not current else 'OFF'}!", show_alert=True)
    await bot_settings_menu(client, query)

# ==================== TOGGLE PUBLIC ====================
@Client.on_callback_query(filters.regex("^toggle_public_"))
async def toggle_public_use(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('public_use', True)
    
    await clone_db.update_clone_setting(bot_id, 'public_use', not current)
    await query.answer(f"✅ Mode: {'Private' if current else 'Public'}!", show_alert=True)
    # This function needs access to customize_clone, which is in another file.
    # For now, let's just send a simple confirmation. We can fix this later if needed.
    from .main_menu import customize_clone
    await customize_clone(client, query)


# ==================== RESTART BOT ====================
@Client.on_callback_query(filters.regex("^restart_"))
async def restart_clone(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    await query.answer("🔄 Restart feature coming soon!", show_alert=True)

# ==================== DEACTIVATE ====================
@Client.on_callback_query(filters.regex("^deactivate_"))
async def deactivate_clone(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    
    buttons = [
        [
            InlineKeyboardButton('✅ Yes', callback_data=f'confirm_deactivate_{bot_id}'),
            InlineKeyboardButton('❌ No', callback_data=f'customize_{bot_id}')
        ]
    ]
    
    await query.message.edit_text(
        "<b>⚠️ Deactivate Clone?</b>\n\nBot will stop temporarily",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex("^confirm_deactivate_"))
async def confirm_deactivate(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    await clone_db.update_clone_setting(bot_id, 'is_active', False)
    await query.answer("✅ Deactivated!", show_alert=True)
    from .main_menu import customize_clone
    await customize_clone(client, query)

# ==================== DELETE ====================
@Client.on_callback_query(filters.regex("^delete_(?!clone)"))
async def delete_clone_confirm(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    
    buttons = [
        [
            InlineKeyboardButton('✅ Yes, Delete', callback_data=f'confirm_delete_{bot_id}'),
            InlineKeyboardButton('❌ No', callback_data=f'customize_{bot_id}')
        ]
    ]
    
    await query.message.edit_text(
        "<b>⚠️ DELETE CLONE?</b>\n\nThis action cannot be undone!",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex("^confirm_delete_"))
async def confirm_delete_clone(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    
    if clone['user_id'] != query.from_user.id:
        return await query.answer("Access denied!", show_alert=True)
    
    await clone_db.delete_clone_by_id(bot_id)
    await query.message.edit_text(
        "<b>✅ Clone Deleted!</b>",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('« Back', callback_data='clone')
        ]])
    )
