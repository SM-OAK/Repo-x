# In clone_plugins/customize.py

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.clone_db import clone_db
import logging

logger = logging.getLogger(__name__)

# Main customize menu
@Client.on_callback_query(filters.regex("^customize_"))
async def customize_clone(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    clone = await clone_db.get_clone(bot_id)
    
    if not clone:
        return await query.answer("Clone not found!", show_alert=True)
    
    if clone['user_id'] != query.from_user.id:
        return await query.answer("This is not your clone!", show_alert=True)
    
    buttons = [
        [
            InlineKeyboardButton('📝 sᴛᴀʀᴛ ᴍsɢ', callback_data=f'set_start_{bot_id}'),
            InlineKeyboardButton('📢 ʟᴏɢ ᴄʜᴀɴɴᴇʟ', callback_data=f'set_log_{bot_id}') # <-- ADDED THIS
        ],
        [
            InlineKeyboardButton('🔒 ғᴏʀᴄᴇ sᴜʙ', callback_data=f'set_fsub_{bot_id}'),
            InlineKeyboardButton('⏱️ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ', callback_data=f'set_autodel_{bot_id}')
        ],
        [
            InlineKeyboardButton('📊 sᴛᴀᴛs', callback_data=f'clone_stats_{bot_id}'),
            InlineKeyboardButton('🔄 ʀᴇsᴛᴀʀᴛ', callback_data=f'restart_{bot_id}')
        ],
        [
            InlineKeyboardButton('🔙 ʙᴀᴄᴋ', callback_data='clone'),
            InlineKeyboardButton('🗑️ ᴅᴇʟᴇᴛᴇ', callback_data=f'delete_{bot_id}')
        ]
    ]
    
    settings_text = (
        f"<b>🛠️ Cᴜsᴛᴏᴍɪᴢᴇ Cʟᴏɴᴇ</b>\n\n"
        f"➜ <b>Nᴀᴍᴇ:</b> {clone['name']}\n"
        f"➜ <b>Usᴇʀɴᴀᴍᴇ:</b> @{clone['username']}\n\n"
        f"Cᴏɴғɪɢᴜʀᴇ ʏᴏᴜʀ ᴄʟᴏɴᴇ sᴇᴛᴛɪɴɢs ᴜsɪɴɢ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ:"
    )
    
    await query.message.edit_text(settings_text, reply_markup=InlineKeyboardMarkup(buttons))

# Start message setting
@Client.on_callback_query(filters.regex("^set_start_"))
async def set_start_msg(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    await query.message.edit_text("<b>📝 Sᴇɴᴅ ʏᴏᴜʀ ᴄᴜsᴛᴏᴍ sᴛᴀʀᴛ ᴍᴇssᴀɢᴇ:</b>\n\nUsᴇ /cancel ᴛᴏ ᴄᴀɴᴄᴇʟ")
    try:
        msg = await client.ask(query.message.chat.id, timeout=300)
        if msg.text == '/cancel':
            return await query.message.edit_text("Cᴀɴᴄᴇʟᴇᴅ!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]]))
        await clone_db.update_clone_setting(bot_id, 'start_message', msg.text)
        await query.message.edit_text("✅ Sᴛᴀʀᴛ ᴍᴇssᴀɢᴇ ᴜᴘᴅᴀᴛᴇᴅ!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]]))
    except:
        await query.message.edit_text("Tɪᴍᴇᴏᴜᴛ!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]]))

# Force sub setting
@Client.on_callback_query(filters.regex("^set_fsub_"))
async def set_force_sub(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    await query.message.edit_text("<b>🔒 Sᴇɴᴅ ᴄʜᴀɴɴᴇʟ ID:</b>\n\nExᴀᴍᴘʟᴇ: <code>-100123456789</code>\n\nUsᴇ /cancel ᴛᴏ ᴄᴀɴᴄᴇʟ")
    try:
        msg = await client.ask(query.message.chat.id, timeout=300)
        if msg.text == '/cancel':
            return await query.message.edit_text("Cᴀɴᴄᴇʟᴇᴅ!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]]))
        await clone_db.update_clone_setting(bot_id, 'force_sub_channel', int(msg.text))
        await query.message.edit_text("✅ Fᴏʀᴄᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴜᴘᴅᴀᴛᴇᴅ!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]]))
    except:
        await query.message.edit_text("Iɴᴠᴀʟɪᴅ ID!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]]))

# NEW: Log channel setting
@Client.on_callback_query(filters.regex("^set_log_"))
async def set_log_channel(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    await query.message.edit_text("<b>📢 Sᴇɴᴅ ʏᴏᴜʀ Lᴏɢ Cʜᴀɴɴᴇʟ ID:</b>\n\nMake sure your clone bot is an admin there.\nExᴀᴍᴘʟᴇ: <code>-100123456789</code>\n\nUsᴇ /cancel ᴛᴏ ᴄᴀɴᴄᴇʟ")
    try:
        msg = await client.ask(query.message.chat.id, timeout=300)
        if msg.text == '/cancel':
            return await query.message.edit_text("Cᴀɴᴄᴇʟᴇᴅ!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]]))
        await clone_db.update_clone_setting(bot_id, 'log_channel', int(msg.text))
        await query.message.edit_text("✅ Lᴏɢ Cʜᴀɴɴᴇʟ ᴜᴘᴅᴀᴛᴇᴅ!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]]))
    except:
        await query.message.edit_text("Iɴᴠᴀʟɪᴅ ID!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]]))

# Auto delete toggle and other functions remain the same...
# (You can paste the rest of your original `clone_customize-5.py` file content here)
