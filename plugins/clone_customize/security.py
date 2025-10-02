# plugins/clone_customize/security.py
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.clone_db import clone_db

# Hum user_states ko appearance.py se import kar rahe hain taaki state share ho sake.
# Baad mein hum ise ek central file mein rakhenge.
# Yeh sahi line hai
from .input_handler import user_states

# ==================== SECURITY ====================
@Client.on_callback_query(filters.regex("^security_"))
async def security_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    
    fsub_count = len(settings.get('force_sub_channels', []))
    auto_del = "✅" if settings.get('auto_delete') else "❌"
    protect = "✅" if settings.get('protect_mode') else "❌"
    verify = "✅" if settings.get('verification') else "❌"
    
    buttons = [
        [InlineKeyboardButton(f'Force Sub ({fsub_count}/6)', callback_data=f'fsub_manage_{bot_id}')],
        [InlineKeyboardButton(f'{auto_del} Auto Delete', callback_data=f'auto_delete_{bot_id}')],
        [InlineKeyboardButton(f'{protect} Protect Mode', callback_data=f'protect_mode_{bot_id}')],
        [InlineKeyboardButton(f'{verify} Verification', callback_data=f'verification_{bot_id}')],
        [InlineKeyboardButton('« Back', callback_data=f'customize_{bot_id}')]
    ]
    
    text = "<b>🔒 Security Settings</b>\n<i>Manage access & protection</i>"
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# Force Subscribe
@Client.on_callback_query(filters.regex("^fsub_manage_"))
async def fsub_manage(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    channels = settings.get('force_sub_channels', [])
    
    buttons = []
    for idx, ch in enumerate(channels):
        buttons.append([
            InlineKeyboardButton(f'📢 {ch}', callback_data='fsub_info'),
            InlineKeyboardButton('❌', callback_data=f'remove_fsub_{bot_id}_{idx}')
        ])
    
    if len(channels) < 6:
        buttons.append([InlineKeyboardButton('➕ Add Channel', callback_data=f'add_fsub_{bot_id}')])
    
    buttons.append([InlineKeyboardButton('« Back', callback_data=f'security_{bot_id}')])
    
    text = f"<b>🔒 Force Subscribe</b>\n<b>Channels:</b> {len(channels)}/6"
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# Yeh naya aur improved fsub_manage function hai
@Client.on_callback_query(filters.regex("^fsub_manage_"))
async def fsub_manage(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    channels = settings.get('force_sub_channels', [])
    
    buttons = []
    
    # Har channel ke liye uski details nikalenge
    for idx, ch_identifier in enumerate(channels):
        channel_name = f"⚠️ Invalid: {ch_identifier}" # Default text agar error aaye
        try:
            # client.get_chat() se channel ka naam nikalenge
            chat = await client.get_chat(ch_identifier)
            channel_name = chat.title # Channel ka asli naam
        except Exception as e:
            print(f"Could not get chat for {ch_identifier}: {e}")

        # Ab button mein ID ki jagah channel ka asli naam dikhega
        buttons.append([
            InlineKeyboardButton(f'📢 {channel_name}', callback_data=f'info_{ch_identifier}'), # Button par ab naam aayega
            InlineKeyboardButton('❌', callback_data=f'remove_fsub_{bot_id}_{idx}')
        ])
    
    if len(channels) < 6:
        buttons.append([InlineKeyboardButton('➕ Add Channel', callback_data=f'add_fsub_{bot_id}')])
    
    buttons.append([InlineKeyboardButton('« Back', callback_data=f'security_{bot_id}')])
    
    text = f"<b>🔒 Force Subscribe</b>\n<b>Channels:</b> {len(channels)}/6\n\n<i>Yahan aapke jode gaye channels dikhenge.</i>"
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^remove_fsub_"))
async def remove_fsub(client, query: CallbackQuery):
    parts = query.data.split("_")
    bot_id = int(parts[2])
    idx = int(parts[3])
    
    clone = await clone_db.get_clone(bot_id)
    channels = clone.get('settings', {}).get('force_sub_channels', [])
    
    if idx < len(channels):
        removed = channels.pop(idx)
        await clone_db.update_clone_setting(bot_id, 'force_sub_channels', channels)
        await query.answer(f"✅ Removed: {removed}", show_alert=True)
    
    await fsub_manage(client, query)

# Auto Delete
@Client.on_callback_query(filters.regex("^auto_delete_"))
async def auto_delete_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    
    enabled = settings.get('auto_delete', False)
    time_sec = settings.get('auto_delete_time', 1800)
    minutes = time_sec // 60
    
    buttons = [
        [InlineKeyboardButton(
            f"{'✅ Enabled' if enabled else '❌ Disabled'}", 
            callback_data=f'toggle_autodel_{bot_id}'
        )],
        [InlineKeyboardButton('⏱️ Set Time', callback_data=f'set_autodel_time_{bot_id}')],
        [InlineKeyboardButton('« Back', callback_data=f'security_{bot_id}')]
    ]
    
    status = "ON" if enabled else "OFF"
    text = f"<b>🗑️ Auto Delete</b>\n<b>Status:</b> {status}\n<b>Time:</b> {minutes} min"
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^toggle_autodel_"))
async def toggle_autodel(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('auto_delete', False)
    
    await clone_db.update_clone_setting(bot_id, 'auto_delete', not current)
    await query.answer(f"✅ {'Enabled' if not current else 'Disabled'}!", show_alert=True)
    await auto_delete_menu(client, query)

@Client.on_callback_query(filters.regex("^set_autodel_time_"))
async def set_autodel_time(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_states[query.from_user.id] = {'action': 'autodel_time', 'bot_id': bot_id}
    
    await query.message.edit_text(
        "<b>Send time in seconds:</b>\n\n"
        "Min: 20 seconds\n"
        "Examples: <code>60</code>, <code>300</code>, <code>600</code>\n\n"
        "/cancel to abort",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('« Cancel', callback_data=f'auto_delete_{bot_id}')
        ]])
    )

# Protect Mode
@Client.on_callback_query(filters.regex("^protect_mode_"))
async def protect_mode_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    enabled = settings.get('protect_mode', False)
    
    buttons = [
        [InlineKeyboardButton(
            f"{'✅ Enabled' if enabled else '❌ Disabled'}", 
            callback_data=f'toggle_protect_{bot_id}'
        )],
        [InlineKeyboardButton('« Back', callback_data=f'security_{bot_id}')]
    ]
    
    status = "ON" if enabled else "OFF"
    text = f"<b>🛡️ Protect Mode</b>\n<b>Status:</b> {status}\n\n<i>Disable forward/save</i>"
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^toggle_protect_"))
async def toggle_protect(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('protect_mode', False)
    
    await clone_db.update_clone_setting(bot_id, 'protect_mode', not current)
    await query.answer(f"✅ {'Enabled' if not current else 'Disabled'}!", show_alert=True)
    await protect_mode_menu(client, query)

# Verification
@Client.on_callback_query(filters.regex("^verification_"))
async def verification_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    
    enabled = settings.get('verification', False)
    has_api = "✅" if settings.get('shortlink_api') else "❌"
    has_url = "✅" if settings.get('shortlink_url') else "❌"
    
    buttons = [
        [InlineKeyboardButton(
            f"{'✅ Enabled' if enabled else '❌ Disabled'}", 
            callback_data=f'toggle_verify_{bot_id}'
        )],
        [InlineKeyboardButton(f'{has_api} Shortlink API', callback_data=f'set_api_{bot_id}')],
        [InlineKeyboardButton(f'{has_url} Shortlink URL', callback_data=f'set_url_{bot_id}')],
        [InlineKeyboardButton('Tutorial Link', callback_data=f'set_tutorial_{bot_id}')],
        [InlineKeyboardButton('« Back', callback_data=f'security_{bot_id}')]
    ]
    
    status = "ON" if enabled else "OFF"
    text = f"<b>🔐 Verification</b>\n<b>Status:</b> {status}"
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^toggle_verify_"))
async def toggle_verify(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('verification', False)
    
    await clone_db.update_clone_setting(bot_id, 'verification', not current)
    await query.answer(f"✅ {'Enabled' if not current else 'Disabled'}!", show_alert=True)
    await verification_menu(client, query)

@Client.on_callback_query(filters.regex("^set_api_"))
async def set_shortlink_api(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'shortlink_api', 'bot_id': bot_id}
    
    await query.message.edit_text(
        "<b>Send Shortlink API:</b>\n\n"
        "Get from your shortlink provider\n\n"
        "/cancel to abort",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('« Cancel', callback_data=f'verification_{bot_id}')
        ]])
    )

@Client.on_callback_query(filters.regex("^set_url_"))
async def set_shortlink_url(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'shortlink_url', 'bot_id': bot_id}
    
    await query.message.edit_text(
        "<b>Send Shortlink URL:</b>\n\n"
        "Example: <code>https://droplink.co</code>\n\n"
        "/cancel to abort",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('« Cancel', callback_data=f'verification_{bot_id}')
        ]])
    )

@Client.on_callback_query(filters.regex("^set_tutorial_"))
async def set_tutorial(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'tutorial_link', 'bot_id': bot_id}
    
    await query.message.edit_text(
        "<b>Send Tutorial Link:</b>\n\n"
        "YouTube or any tutorial URL\n\n"
        "/cancel to abort",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('« Cancel', callback_data=f'verification_{bot_id}')
        ]])
    )
