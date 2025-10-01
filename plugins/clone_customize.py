# plugins/clone_customize.py
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.clone_db import clone_db
import logging

logger = logging.getLogger(__name__)
user_states = {}

# ==================== MAIN CUSTOMIZE MENU ====================
@Client.on_callback_query(filters.regex("^customize_"))
async def customize_clone(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    clone = await clone_db.get_clone(bot_id)
    
    if not clone:
        return await query.answer("Clone not found!", show_alert=True)
    
    if clone['user_id'] != query.from_user.id:
        return await query.answer("Not your clone!", show_alert=True)
    
    settings = clone.get('settings', {})
    status = "🟢" if clone.get('is_active', True) else "🔴"
    mode = "🔓" if settings.get('public_use', True) else "🔒"
    
    buttons = [
        [
            InlineKeyboardButton('🎨 Appearance', callback_data=f'appearance_{bot_id}'),
            InlineKeyboardButton('🔒 Security', callback_data=f'security_{bot_id}')
        ],
        [
            InlineKeyboardButton('📁 Files', callback_data=f'files_{bot_id}'),
            InlineKeyboardButton('📊 Database', callback_data=f'database_{bot_id}')
        ],
        [
            InlineKeyboardButton('👥 Admins', callback_data=f'admins_{bot_id}'),
            InlineKeyboardButton('📢 Channels', callback_data=f'channels_{bot_id}')
        ],
        [
            InlineKeyboardButton('📈 Statistics', callback_data=f'stats_{bot_id}'),
            InlineKeyboardButton('⚙️ Settings', callback_data=f'bot_settings_{bot_id}')
        ],
        [
            InlineKeyboardButton(f'{mode} Toggle Mode', callback_data=f'toggle_public_{bot_id}'),
            InlineKeyboardButton('🔄 Restart', callback_data=f'restart_{bot_id}')
        ],
        [
            InlineKeyboardButton('⚠️ Deactivate', callback_data=f'deactivate_{bot_id}'),
            InlineKeyboardButton('🗑️ Delete', callback_data=f'delete_{bot_id}')
        ],
        [InlineKeyboardButton('« Back', callback_data='clone')]
    ]
    
    text = f"<b>{status} @{clone['username']}</b>\n<i>Select category:</i>"
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# ==================== APPEARANCE ====================
@Client.on_callback_query(filters.regex("^appearance_"))
async def appearance_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    
    has_text = "✅" if settings.get('start_message') else "➕"
    has_pic = "✅" if settings.get('start_photo') else "➕"
    has_btn = "✅" if settings.get('start_button') else "➕"
    has_caption = "✅" if settings.get('file_caption') else "➕"
    
    buttons = [
        [InlineKeyboardButton(f'{has_text} Start Message', callback_data=f'start_text_{bot_id}')],
        [InlineKeyboardButton(f'{has_pic} Start Photo', callback_data=f'start_photo_{bot_id}')],
        [InlineKeyboardButton(f'{has_btn} Start Button', callback_data=f'start_button_{bot_id}')],
        [InlineKeyboardButton(f'{has_caption} File Caption', callback_data=f'file_caption_{bot_id}')],
        [InlineKeyboardButton('« Back', callback_data=f'customize_{bot_id}')]
    ]
    
    text = "<b>🎨 Appearance Settings</b>\n<i>Customize bot interface</i>"
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# Start Message
@Client.on_callback_query(filters.regex("^start_text_"))
async def start_text_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('start_message')
    
    buttons = []
    if current:
        buttons.append([InlineKeyboardButton('👁️ Preview', callback_data=f'preview_start_{bot_id}')])
        buttons.append([InlineKeyboardButton('🗑️ Remove', callback_data=f'remove_start_text_{bot_id}')])
    
    buttons.append([InlineKeyboardButton('✏️ Set New', callback_data=f'input_start_text_{bot_id}')])
    buttons.append([InlineKeyboardButton('« Back', callback_data=f'appearance_{bot_id}')])
    
    status = "Custom" if current else "Default"
    text = f"<b>📝 Start Message</b>\n<b>Status:</b> {status}"
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^input_start_text_"))
async def input_start_text(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_states[query.from_user.id] = {'action': 'start_text', 'bot_id': bot_id}
    
    await query.message.edit_text(
        "<b>Send start message:</b>\n\n"
        "Variables: <code>{mention}</code>\n"
        "Format: HTML\n\n"
        "/cancel to abort",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('« Cancel', callback_data=f'start_text_{bot_id}')
        ]])
    )

@Client.on_callback_query(filters.regex("^remove_start_text_"))
async def remove_start_text(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    await clone_db.update_clone_setting(bot_id, 'start_message', None)
    await query.answer("✅ Removed!", show_alert=True)
    await start_text_menu(client, query)

@Client.on_callback_query(filters.regex("^preview_start_"))
async def preview_start(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    msg = clone.get('settings', {}).get('start_message', 'No message set')
    
    await query.answer(f"Preview:\n{msg[:150]}...", show_alert=True)

# Start Photo
@Client.on_callback_query(filters.regex("^start_photo_"))
async def start_photo_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('start_photo')
    
    buttons = []
    if current:
        buttons.append([InlineKeyboardButton('🗑️ Remove', callback_data=f'remove_start_photo_{bot_id}')])
    
    buttons.append([InlineKeyboardButton('📤 Upload New', callback_data=f'input_start_photo_{bot_id}')])
    buttons.append([InlineKeyboardButton('« Back', callback_data=f'appearance_{bot_id}')])
    
    status = "Custom" if current else "Default"
    text = f"<b>🖼️ Start Photo</b>\n<b>Status:</b> {status}"
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^input_start_photo_"))
async def input_start_photo(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_states[query.from_user.id] = {'action': 'start_photo', 'bot_id': bot_id}
    
    await query.message.edit_text(
        "<b>Send photo or URL:</b>\n\n"
        "/remove to delete\n"
        "/cancel to abort",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('« Cancel', callback_data=f'start_photo_{bot_id}')
        ]])
    )

@Client.on_callback_query(filters.regex("^remove_start_photo_"))
async def remove_start_photo(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    await clone_db.update_clone_setting(bot_id, 'start_photo', None)
    await query.answer("✅ Removed!", show_alert=True)
    await start_photo_menu(client, query)

# Start Button
@Client.on_callback_query(filters.regex("^start_button_"))
async def start_button_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('start_button')
    
    buttons = []
    if current:
        buttons.append([InlineKeyboardButton('👁️ Preview', callback_data=f'preview_button_{bot_id}')])
        buttons.append([InlineKeyboardButton('🗑️ Remove', callback_data=f'remove_start_button_{bot_id}')])
    
    buttons.append([InlineKeyboardButton('✏️ Set New', callback_data=f'input_start_button_{bot_id}')])
    buttons.append([InlineKeyboardButton('« Back', callback_data=f'appearance_{bot_id}')])
    
    status = "Custom" if current else "Default"
    text = f"<b>🔘 Start Button</b>\n<b>Status:</b> {status}"
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^input_start_button_"))
async def input_start_button(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_states[query.from_user.id] = {'action': 'start_button', 'bot_id': bot_id}
    
    await query.message.edit_text(
        "<b>Send button:</b>\n\n"
        "Format: <code>Text - URL</code>\n"
        "Example: <code>Join - https://t.me/channel</code>\n\n"
        "/cancel to abort",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('« Cancel', callback_data=f'start_button_{bot_id}')
        ]])
    )

@Client.on_callback_query(filters.regex("^remove_start_button_"))
async def remove_start_button(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    await clone_db.update_clone_setting(bot_id, 'start_button', None)
    await query.answer("✅ Removed!", show_alert=True)
    await start_button_menu(client, query)

# File Caption
@Client.on_callback_query(filters.regex("^file_caption_"))
async def file_caption_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('file_caption')
    
    buttons = []
    if current:
        buttons.append([InlineKeyboardButton('👁️ Preview', callback_data=f'preview_caption_{bot_id}')])
        buttons.append([InlineKeyboardButton('🗑️ Remove', callback_data=f'remove_caption_{bot_id}')])
    
    buttons.append([InlineKeyboardButton('✏️ Set New', callback_data=f'input_caption_{bot_id}')])
    buttons.append([InlineKeyboardButton('« Back', callback_data=f'appearance_{bot_id}')])
    
    status = "Custom" if current else "Default"
    text = f"<b>📝 File Caption</b>\n<b>Status:</b> {status}"
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^input_caption_"))
async def input_caption(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'file_caption', 'bot_id': bot_id}
    
    await query.message.edit_text(
        "<b>Send caption template:</b>\n\n"
        "Variables:\n"
        "<code>{filename}</code> - File name\n"
        "<code>{size}</code> - File size\n"
        "<code>{caption}</code> - Original caption\n\n"
        "/cancel to abort",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('« Cancel', callback_data=f'file_caption_{bot_id}')
        ]])
    )

@Client.on_callback_query(filters.regex("^remove_caption_"))
async def remove_caption(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    await clone_db.update_clone_setting(bot_id, 'file_caption', None)
    await query.answer("✅ Removed!", show_alert=True)
    await file_caption_menu(client, query)

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

@Client.on_callback_query(filters.regex("^add_fsub_"))
async def add_fsub(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'add_fsub', 'bot_id': bot_id}
    
    await query.message.edit_text(
        "<b>Send channel:</b>\n\n"
        "Format: <code>@username</code> or <code>-100xxx</code>\n\n"
        "/cancel to abort",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('« Cancel', callback_data=f'fsub_manage_{bot_id}')
        ]])
    )

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

# ==================== FILES ====================
@Client.on_callback_query(filters.regex("^files_"))
async def files_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    
    protect = "✅" if settings.get('protect_forward') else "❌"
    
    buttons = [
        [InlineKeyboardButton('📝 Caption Template', callback_data=f'file_caption_{bot_id}')],
        [InlineKeyboardButton(f'{protect} Protect Forward', callback_data=f'toggle_forward_{bot_id}')],
        [InlineKeyboardButton('📏 File Size Limit', callback_data=f'file_limit_{bot_id}')],
        [InlineKeyboardButton('📂 Allowed Types', callback_data=f'file_types_{bot_id}')],
        [InlineKeyboardButton('« Back', callback_data=f'customize_{bot_id}')]
    ]
    
    text = "<b>📁 File Settings</b>\n<i>Manage file behavior</i>"
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^toggle_forward_"))
async def toggle_forward(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('protect_forward', False)
    
    await clone_db.update_clone_setting(bot_id, 'protect_forward', not current)
    await query.answer(f"✅ {'Enabled' if not current else 'Disabled'}!", show_alert=True)
    await files_menu(client, query)

@Client.on_callback_query(filters.regex("^file_limit_"))
async def file_limit_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'file_limit', 'bot_id': bot_id}
    
    await query.message.edit_text(
        "<b>Set file size limit (MB):</b>\n\n"
        "Example: <code>500</code> for 500MB\n"
        "Send <code>0</code> for no limit\n\n"
        "/cancel to abort",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('« Cancel', callback_data=f'files_{bot_id}')
        ]])
    )

@Client.on_callback_query(filters.regex("^file_types_"))
async def file_types_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    allowed = settings.get('allowed_types', ['all'])
    
    types = ['video', 'audio', 'document', 'photo', 'all']
    buttons = []
    
    for t in types:
        check = "✅" if t in allowed else "☐"
        buttons.append([InlineKeyboardButton(f'{check} {t.title()}', callback_data=f'toggle_type_{bot_id}_{t}')])
    
    buttons.append([InlineKeyboardButton('« Back', callback_data=f'files_{bot_id}')])
    
    text = f"<b>📂 Allowed File Types</b>\n<b>Selected:</b> {', '.join(allowed)}"
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^toggle_type_"))
async def toggle_file_type(client, query: CallbackQuery):
    parts = query.data.split("_")
    bot_id = int(parts[2])
    file_type = parts[3]
    
    clone = await clone_db.get_clone(bot_id)
    allowed = clone.get('settings', {}).get('allowed_types', ['all'])
    
    if file_type == 'all':
        allowed = ['all']
    else:
        if 'all' in allowed:
            allowed.remove('all')
        
        if file_type in allowed:
            allowed.remove(file_type)
        else:
            allowed.append(file_type)
        
        if not allowed:
            allowed = ['all']
    
    await clone_db.update_clone_setting(bot_id, 'allowed_types', allowed)
    await file_types_menu(client, query)

# ==================== DATABASE ====================
@Client.on_callback_query(filters.regex("^database_"))
async def database_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    
    has_mongo = "✅" if settings.get('mongo_db') else "❌"
    has_log = "✅" if settings.get('log_channel') else "❌"
    has_db = "✅" if settings.get('db_channel') else "❌"
    
    buttons = [
        [InlineKeyboardButton(f'{has_mongo} MongoDB URI', callback_data=f'mongo_db_{bot_id}')],
        [InlineKeyboardButton(f'{has_log} Log Channel', callback_data=f'log_channel_{bot_id}')],
        [InlineKeyboardButton(f'{has_db} DB Channel', callback_data=f'db_channel_{bot_id}')],
        [InlineKeyboardButton('« Back', callback_data=f'customize_{bot_id}')]
    ]
    
    text = "<b>📊 Database Settings</b>\n<i>Storage & logging config</i>"
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# MongoDB
@Client.on_callback_query(filters.regex("^mongo_db_"))
async def mongo_db_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('mongo_db')
    
    buttons = []
    if current:
        buttons.append([InlineKeyboardButton('🗑️ Remove', callback_data=f'remove_mongo_{bot_id}')])
    else:
        buttons.append([InlineKeyboardButton('➕ Add Custom', callback_data=f'input_mongo_{bot_id}')])
    
    buttons.append([InlineKeyboardButton('« Back', callback_data=f'database_{bot_id}')])
    
    status = "Custom DB" if current else "Default DB"
    text = f"<b>🗄️ MongoDB</b>\n<b>Status:</b> {status}"
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^input_mongo_"))
async def input_mongo(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'mongo_db', 'bot_id': bot_id}
    
    await query.message.edit_text(
        "<b>Send MongoDB URI:</b>\n\n"
        "Format: <code>mongodb+srv://user:pass@cluster.mongodb.net</code>\n\n"
        "/cancel to abort",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('« Cancel', callback_data=f'mongo_db_{bot_id}')
        ]])
    )

@Client.on_callback_query(filters.regex("^remove_mongo_"))
async def remove_mongo(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    await clone_db.update_clone_setting(bot_id, 'mongo_db', None)
    await query.answer("✅ Removed! Using default", show_alert=True)
    await mongo_db_menu(client, query)

# Log Channel
@Client.on_callback_query(filters.regex("^log_channel_"))
async def log_channel_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('log_channel')
    
    buttons = []
    if current:
        buttons.append([InlineKeyboardButton(f'📢 {current}', callback_data='channel_info')])
        buttons.append([InlineKeyboardButton('🗑️ Remove', callback_data=f'remove_log_{bot_id}')])
    
    buttons.append([InlineKeyboardButton('➕ Set Channel', callback_data=f'input_log_{bot_id}')])
    buttons.append([InlineKeyboardButton('« Back', callback_data=f'database_{bot_id}')])
    
    status = current if current else "Not set"
    text = f"<b>📝 Log Channel</b>\n<b>Channel:</b> {status}\n\n<i>Activity logs stored here</i>"
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^input_log_"))
async def input_log(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'log_channel', 'bot_id': bot_id}
    
    await query.message.edit_text(
        "<b>Send channel:</b>\n\n"
        "Format: <code>@username</code> or <code>-100xxx</code>\n\n"
        "/cancel to abort",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('« Cancel', callback_data=f'log_channel_{bot_id}')
        ]])
    )

@Client.on_callback_query(filters.regex("^remove_log_"))
async def remove_log(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    await clone_db.update_clone_setting(bot_id, 'log_channel', None)
    await query.answer("✅ Removed!", show_alert=True)
    await log_channel_menu(client, query)

# DB Channel (File Storage)
@Client.on_callback_query(filters.regex("^db_channel_"))
async def db_channel_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('db_channel')
    
    buttons = []
    if current:
        buttons.append([InlineKeyboardButton(f'📢 {current}', callback_data='channel_info')])
        buttons.append([InlineKeyboardButton('🗑️ Remove', callback_data=f'remove_db_{bot_id}')])
    
    buttons.append([InlineKeyboardButton('➕ Set Channel', callback_data=f'input_db_{bot_id}')])
    buttons.append([InlineKeyboardButton('« Back', callback_data=f'database_{bot_id}')])
    
    status = current if current else "Not set"
    text = f"<b>🗄️ DB Channel</b>\n<b>Channel:</b> {status}\n\n<i>Files stored here</i>"
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^input_db_"))
async def input_db_channel(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'db_channel', 'bot_id': bot_id}
    
    await query.message.edit_text(
        "<b>Send channel:</b>\n\n"
        "Format: <code>@username</code> or <code>-100xxx</code>\n\n"
        "/cancel to abort",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('« Cancel', callback_data=f'db_channel_{bot_id}')
        ]])
    )

@Client.on_callback_query(filters.regex("^remove_db_"))
async def remove_db_channel(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    await clone_db.update_clone_setting(bot_id, 'db_channel', None)
    await query.answer("✅ Removed!", show_alert=True)
    await db_channel_menu(client, query)

# ==================== ADMINS ====================
@Client.on_callback_query(filters.regex("^admins_"))
async def admins_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    admins = settings.get('admins', [])
    
    buttons = []
    for idx, admin_id in enumerate(admins[:10]):
        buttons.append([
            InlineKeyboardButton(f'👤 {admin_id}', callback_data='admin_info'),
            InlineKeyboardButton('❌', callback_data=f'remove_admin_{bot_id}_{idx}')
        ])
    
    if len(admins) < 10:
        buttons.append([InlineKeyboardButton('➕ Add Admin', callback_data=f'add_admin_{bot_id}')])
    
    buttons.append([InlineKeyboardButton('« Back', callback_data=f'customize_{bot_id}')])
    
    text = f"<b>👥 Admins</b>\n<b>Total:</b> {len(admins)}/10"
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^add_admin_"))
async def add_admin(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'add_admin', 'bot_id': bot_id}
    
    await query.message.edit_text(
        "<b>Send user ID:</b>\n\n"
        "Example: <code>123456789</code>\n\n"
        "/cancel to abort",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('« Cancel', callback_data=f'admins_{bot_id}')
        ]])
    )

@Client.on_callback_query(filters.regex("^remove_admin_"))
async def remove_admin(client, query: CallbackQuery):
    parts = query.data.split("_")
    bot_id = int(parts[2])
    idx = int(parts[3])
    
    clone = await clone_db.get_clone(bot_id)
    admins = clone.get('settings', {}).get('admins', [])
    
    if idx < len(admins):
        removed = admins.pop(idx)
        await clone_db.update_clone_setting(bot_id, 'admins', admins)
        await query.answer(f"✅ Removed: {removed}", show_alert=True)
    
    await admins_menu(client, query)

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

# ==================== STATISTICS ====================
@Client.on_callback_query(filters.regex("^stats_"))
async def stats_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    clone = await clone_db.get_clone(bot_id)
    users_count = await clone_db.get_clone_users_count(bot_id)
    
    buttons = [[InlineKeyboardButton('« Back', callback_data=f'customize_{bot_id}')]]
    
    text = (
        f"<b>📈 Statistics</b>\n\n"
        f"<b>Bot:</b> @{clone['username']}\n"
        f"<b>Users:</b> {users_count}\n"
        f"<b>Created:</b> {clone.get('created_at', 'N/A')}\n"
        f"<b>Last Used:</b> {clone.get('last_used', 'Never')}"
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

# ==================== USER INPUT HANDLER ====================
@Client.on_message(filters.private & filters.text, group=2)
async def handle_setting_input(client, message):
    user_id = message.from_user.id
    
    if user_id not in user_states:
        return
    
    state = user_states[user_id]
    action = state['action']
    bot_id = state['bot_id']
    
    if message.text == '/cancel':
        del user_states[user_id]
        return await message.reply("❌ Cancelled!", reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('« Back', callback_data=f'customize_{bot_id}')
        ]]))
    
    try:
        # Start Text
        if action == 'start_text':
            await clone_db.update_clone_setting(bot_id, 'start_message', message.text)
            del user_states[user_id]
            await message.reply("✅ Start message updated!", reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton('« Back', callback_data=f'start_text_{bot_id}')
            ]]))
        
        # Start Photo URL
        elif action == 'start_photo':
            if message.text == '/remove':
                await clone_db.update_clone_setting(bot_id, 'start_photo', None)
                del user_states[user_id]
                return await message.reply("✅ Removed!", reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton('« Back', callback_data=f'start_photo_{bot_id}')
                ]]))
            
            if message.text.startswith('http'):
                await clone_db.update_clone_setting(bot_id, 'start_photo', message.text)
                del user_states[user_id]
                await message.reply("✅ Photo updated!", reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton('« Back', callback_data=f'start_photo_{bot_id}')
                ]]))
            else:
                await message.reply("❌ Invalid URL!")
        
        # Start Button
        elif action == 'start_button':
            if ' - ' in message.text:
                await clone_db.update_clone_setting(bot_id, 'start_button', message.text)
                del user_states[user_id]
                await message.reply("✅ Button updated!", reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton('« Back', callback_data=f'start_button_{bot_id}')
                ]]))
            else:
                await message.reply("❌ Invalid format! Use: Text - URL")
        
        # File Caption
        elif action == 'file_caption':
            await clone_db.update_clone_setting(bot_id, 'file_caption', message.text)
            del user_states[user_id]
            await message.reply("✅ Caption template updated!", reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton('« Back', callback_data=f'file_caption_{bot_id}')
            ]]))
        
        # Force Sub Channel
        elif action == 'add_fsub':
            clone = await clone_db.get_clone(bot_id)
            channels = clone.get('settings', {}).get('force_sub_channels', [])
            
            if len(channels) >= 6:
                return await message.reply("❌ Max 6 channels!")
            
            channel = message.text.strip()
            if channel not in channels:
                channels.append(channel)
                await clone_db.update_clone_setting(bot_id, 'force_sub_channels', channels)
                del user_states[user_id]
                await message.reply(f"✅ Added: {channel}", reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton('« Back', callback_data=f'fsub_manage_{bot_id}')
                ]]))
            else:
                await message.reply("❌ Already exists!")
        
        # Auto Delete Time
        elif action == 'autodel_time':
            time_sec = int(message.text)
            if time_sec < 20:
                return await message.reply("❌ Min 20 seconds!")
            
            await clone_db.update_clone_setting(bot_id, 'auto_delete_time', time_sec)
            del user_states[user_id]
            await message.reply(f"✅ Time set to {time_sec}s!", reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton('« Back', callback_data=f'auto_delete_{bot_id}')
            ]]))
        
        # Shortlink API
        elif action == 'shortlink_api':
            await clone_db.update_clone_setting(bot_id, 'shortlink_api', message.text)
            del user_states[user_id]
            await message.reply("✅ API updated!", reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton('« Back', callback_data=f'verification_{bot_id}')
            ]]))
        
        # Shortlink URL
        elif action == 'shortlink_url':
            await clone_db.update_clone_setting(bot_id, 'shortlink_url', message.text)
            del user_states[user_id]
            await message.reply("✅ URL updated!", reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton('« Back', callback_data=f'verification_{bot_id}')
            ]]))
        
        # Tutorial Link
        elif action == 'tutorial_link':
            await clone_db.update_clone_setting(bot_id, 'tutorial_link', message.text)
            del user_states[user_id]
            await message.reply("✅ Tutorial link updated!", reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton('« Back', callback_data=f'verification_{bot_id}')
            ]]))
        
        # MongoDB URI
        elif action == 'mongo_db':
            await clone_db.update_clone_setting(bot_id, 'mongo_db', message.text)
            del user_states[user_id]
            await message.reply("✅ MongoDB updated!", reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton('« Back', callback_data=f'mongo_db_{bot_id}')
            ]]))
        
        # Log Channel
        elif action == 'log_channel':
            await clone_db.update_clone_setting(bot_id, 'log_channel', message.text)
            del user_states[user_id]
            await message.reply("✅ Log channel updated!", reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton('« Back', callback_data=f'log_channel_{bot_id}')
            ]]))
        
        # DB Channel
        elif action == 'db_channel':
            await clone_db.update_clone_setting(bot_id, 'db_channel', message.text)
            del user_states[user_id]
            await message.reply("✅ DB channel updated!", reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton('« Back', callback_data=f'db_channel_{bot_id}')
            ]]))
        
        # Admin
        elif action == 'add_admin':
            admin_id = int(message.text)
            clone = await clone_db.get_clone(bot_id)
            admins = clone.get('settings', {}).get('admins', [])
            
            if admin_id not in admins:
                admins.append(admin_id)
                await clone_db.update_clone_setting(bot_id, 'admins', admins)
                del user_states[user_id]
                await message.reply(f"✅ Admin added: {admin_id}", reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton('« Back', callback_data=f'admins_{bot_id}')
                ]]))
            else:
                await message.reply("❌ Already admin!")
        
        # File Size Limit
        elif action == 'file_limit':
            limit = int(message.text)
            await clone_db.update_clone_setting(bot_id, 'file_size_limit', limit)
            del user_states[user_id]
            await message.reply(f"✅ Limit set to {limit}MB!", reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton('« Back', callback_data=f'files_{bot_id}')
            ]]))
    
    except ValueError:
        await message.reply("❌ Invalid input!")
    except Exception as e:
        logger.error(f"Error handling input: {e}")
        await message.reply(f"❌ Error: {str(e)}")

# Handle Photo Input
@Client.on_message(filters.private & filters.photo, group=2)
async def handle_photo_input(client, message):
    user_id = message.from_user.id
    
    if user_id not in user_states:
        return
    
    state = user_states[user_id]
    if state['action'] != 'start_photo':
        return
    
    bot_id = state['bot_id']
    photo_id = message.photo.file_id
    
    await clone_db.update_clone_setting(bot_id, 'start_photo', photo_id)
    del user_states[user_id]
    await message.reply("✅ Photo updated!", reply_markup=InlineKeyboardMarkup([[
        InlineKeyboardButton('« Back', callback_data=f'start_photo_{bot_id}')
    ]]))

logger.info("✅ Clone customization loaded - Compact UI with all features!")
