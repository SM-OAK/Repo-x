# plugins/clone_customize/database.py
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.clone_db import clone_db

# Hum user_states ko appearance.py se import kar rahe hain.
# Baad mein hum ise ek central file mein rakhenge.
from .appearance import input_handler.py

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

￼Enter
