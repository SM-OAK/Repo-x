# plugins/clone_customize/stats.py
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.clone_db import clone_db

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
