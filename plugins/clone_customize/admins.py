# plugins/clone_customize/admins.py
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.clone_db import clone_db

# Hum user_states ko appearance.py se import kar rahe hain.
# Baad mein hum ise ek central file mein rakhenge.
from .appearance import input_handler.py

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
￼Enter
