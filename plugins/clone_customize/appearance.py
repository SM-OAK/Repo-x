# plugins/clone_customize/appearance.py
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.clone_db import clone_db
from .input_handler import user_states  # <-- YEH LINE BADLI GAYI HAI

import logging
logger = logging.getLogger(__name__)

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

# ... (baaki saara code waisa hi rahega)
# Start Message handlers...
# Start Photo handlers...
# Start Button handlers...
# File Caption handlers...
# (Poora code daalne se response lamba ho jayega, lekin aapke paas yeh code pehle se hai. Bas upar ki import line badalni hai)
