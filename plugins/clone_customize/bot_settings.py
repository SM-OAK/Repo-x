# plugins/clone_customize/bot_settings.py
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.clone_db import clone_db
from .input_handler import user_states # Added import for input handling

# ==================== CHANNELS MENU (ENHANCED) ====================
@Client.on_callback_query(filters.regex("^channels_"))
async def channels_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    
    fsub_count = len(settings.get('force_sub_channels', []))
    log_status = "✅ Set" if settings.get('log_channel') else "❌ Not Set"
    db_status = "✅ Set" if settings.get('db_channel') else "❌ Not Set"
    
    buttons = [
        [InlineKeyboardButton(f'📢 Force Subscribe ({fsub_count}/6)', callback_data=f'fsub_manage_{bot_id}')],
        [InlineKeyboardButton(f'📝 Log Channel • {log_status}', callback_data=f'log_channel_manage_{bot_id}')],
        [InlineKeyboardButton(f'🗄️ DB Channel • {db_status}', callback_data=f'db_channel_manage_{bot_id}')],
        [InlineKeyboardButton('« Back to Customize', callback_data=f'customize_{bot_id}')]
    ]
    
    text = (
        "<b>📢 Channel Management</b>\n\n"
        "Configure all channel-related settings for your bot here.\n\n"
        "• <b>Force Subscribe:</b> Require users to join channels.\n"
        "• <b>Log Channel:</b> Record bot activity and errors.\n"
        "• <b>DB Channel:</b> Store files sent through the bot."
    )
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# ==================== LOG CHANNEL (MOVED & ENHANCED) ====================
@Client.on_callback_query(filters.regex("^log_channel_manage_"))
async def log_channel_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('log_channel')
    
    buttons = []
    text = "<b>📝 Log Channel Settings</b>\n\nLogs, such as new user alerts and error reports, will be sent to this channel.\n\n"

    if current:
        text += f"<b>Current Channel:</b> <code>{current}</code>"
        buttons.append([InlineKeyboardButton('🔄 Change Channel', callback_data=f'input_log_{bot_id}')])
        buttons.append([InlineKeyboardButton('🗑️ Remove Channel', callback_data=f'remove_log_{bot_id}')])
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
        "<b>Send the Log Channel ID or Username:</b>\n\n"
        "Make sure your clone bot is an administrator in this channel.\n\n"
        "<b>Format:</b> <code>@username</code> or <code>-100...</code>\n\n"
        "Send /cancel to abort.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('« Cancel', callback_data=f'log_channel_manage_{bot_id}')
        ]])
    )

@Client.on_callback_query(filters.regex("^remove_log_"))
async def remove_log(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    await clone_db.update_clone_setting(bot_id, 'log_channel', None)
    await query.answer("✅ Log Channel removed!", show_alert=True)
    query.data = f"log_channel_manage_{bot_id}"
    await log_channel_menu(client, query)

# ==================== DB CHANNEL (MOVED & ENHANCED) ====================
@Client.on_callback_query(filters.regex("^db_channel_manage_"))
async def db_channel_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('db_channel')
    
    buttons = []
    text = "<b>🗄️ DB Channel Settings</b>\n\nThis channel is used to store files. It must be private.\n\n"
    
    if current:
        text += f"<b>Current Channel:</b> <code>{current}</code>"
        buttons.append([InlineKeyboardButton('🔄 Change Channel', callback_data=f'input_db_{bot_id}')])
        buttons.append([InlineKeyboardButton('🗑️ Remove Channel', callback_data=f'remove_db_{bot_id}')])
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
        "<b>Send the DB Channel ID:</b>\n\n"
        "Your clone bot must be an admin here. For security, using a private channel is required.\n\n"
        "<b>Format:</b> <code>-100...</code>\n\n"
        "Send /cancel to abort.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('« Cancel', callback_data=f'db_channel_manage_{bot_id}')
        ]])
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

# ... (rest of your original bot_settings.py code remains the same) ...

@Client.on_callback_query(filters.regex("^toggle_mode_"))
async def toggle_mode(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('public_use', True)
    
    await clone_db.update_clone_setting(bot_id, 'public_use', not current)
    await query.answer(f"✅ Mode: {'Private' if current else 'Public'}!", show_alert=True)
    query.data = f"bot_settings_{bot_id}"
    await bot_settings_menu(client, query)

@Client.on_callback_query(filters.regex("^toggle_maintenance_"))
async def toggle_maintenance(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('maintenance', False)
    
    await clone_db.update_clone_setting(bot_id, 'maintenance', not current)
    await query.answer(f"✅ Maintenance: {'ON' if not current else 'OFF'}!", show_alert=True)
    query.data = f"bot_settings_{bot_id}"
    await bot_settings_menu(client, query)
