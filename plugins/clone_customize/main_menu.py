# plugins/clone_customize/main_menu.py
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.clone_db import clone_db

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
