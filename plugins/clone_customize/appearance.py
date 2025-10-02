# plugins/clone_customize/appearance.py
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.clone_db import clone_db
from .input_handler import user_states # <-- Yeh final import hai

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
