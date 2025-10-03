# plugins/clone_customize/database.py
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.clone_db import clone_db
from .input_handler import user_states

# ==================== DATABASE ====================
@Client.on_callback_query(filters.regex("^database_"))
async def database_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    
    has_mongo = "✅ Set" if settings.get('mongo_db') else "❌ Not Set"
    
    buttons = [
        [InlineKeyboardButton(f'🗄️ MongoDB URI • {has_mongo}', callback_data=f'mongo_db_{bot_id}')],
        [InlineKeyboardButton('« Back to Customize', callback_data=f'customize_{bot_id}')]
    ]
    
    text = (
        "<b>📊 Database Settings</b>\n\n"
        "Configure your bot's primary database connection (MongoDB).\n\n"
        "<i>If no custom URI is provided, the bot will use the default database.</i>"
    )
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# MongoDB
@Client.on_callback_query(filters.regex("^mongo_db_"))
async def mongo_db_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('mongo_db')
    
    buttons = []
    text = "<b>🗄️ MongoDB URI Management</b>\n\n"

    if current:
        text += "A custom MongoDB URI is currently set for your bot. You can remove it to revert to the default database."
        buttons.append([InlineKeyboardButton('🗑️ Remove Custom URI', callback_data=f'remove_mongo_{bot_id}')])
    else:
        text += "Your bot is currently using the default database. You can add a custom MongoDB URI for dedicated data storage."
        buttons.append([InlineKeyboardButton('➕ Add Custom URI', callback_data=f'input_mongo_{bot_id}')])
    
    buttons.append([InlineKeyboardButton('« Back', callback_data=f'database_{bot_id}')])
    
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^input_mongo_"))
async def input_mongo(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'mongo_db', 'bot_id': bot_id}
    
    await query.message.edit_text(
        "<b>Enter your MongoDB URI:</b>\n\n"
        "Please send the full connection string for your MongoDB database.\n\n"
        "<b>Example Format:</b>\n"
        "<code>mongodb+srv://user:pass@cluster.mongodb.net/database_name</code>\n\n"
        "Send /cancel to abort.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('« Cancel', callback_data=f'mongo_db_{bot_id}')
        ]])
    )

@Client.on_callback_query(filters.regex("^remove_mongo_"))
async def remove_mongo(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    await clone_db.update_clone_setting(bot_id, 'mongo_db', None)
    await query.answer("✅ Removed! Your bot will now use the default database.", show_alert=True)
    
    # Refresh the mongo_db menu
    query.data = f"mongo_db_{bot_id}"
    await mongo_db_menu(client, query)

