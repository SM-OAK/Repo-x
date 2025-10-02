# plugins/clone_customize/files.py
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.clone_db import clone_db

# Hum user_states ko appearance.py se import kar rahe hain.
# Baad mein hum ise ek central file mein rakhenge.
from .appearance import user_states

# ==================== FILES ====================
@Client.on_callback_query(filters.regex("^files_"))
async def files_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    
    # Note: The original code had a 'file_caption' button here, 
    # but that function is already in appearance.py. 
    # So, I'm keeping the menu clean by not duplicating it.
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
￼Enter
