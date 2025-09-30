import re
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.clone_db import clone_db
from shared import ACTIVE_CLONES
import logging

logger = logging.getLogger(__name__)

# --- Main Customization Menu ---
@Client.on_callback_query(filters.regex("^customize_"))
async def customize_clone(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    clone = await clone_db.get_clone(bot_id)
    
    if not clone or clone['user_id'] != query.from_user.id:
        return await query.answer("This is not your clone!", show_alert=True)
    
    buttons = [
        [
            InlineKeyboardButton('📝 sᴛᴀʀᴛ ᴍsɢ', callback_data=f'set_start_{bot_id}'),
            InlineKeyboardButton('🔒 ғᴏʀᴄᴇ sᴜʙ', callback_data=f'set_fsub_{bot_id}')
        ],
        [
            InlineKeyboardButton('👥 ᴍᴏᴅᴇʀᴀᴛᴏʀs', callback_data=f'set_mods_{bot_id}'),
            InlineKeyboardButton('⏱️ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ', callback_data=f'set_autodel_{bot_id}')
        ],
        [
            InlineKeyboardButton('🚫 ɴᴏ ғᴏʀᴡᴀʀᴅ', callback_data=f'set_nofw_{bot_id}'),
            InlineKeyboardButton('🔑 ᴀᴄᴄᴇss ᴛᴏᴋᴇн', callback_data=f'view_token_{bot_id}')
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
    settings_text = f"<b>🛠️ Cᴜsᴛᴏᴍɪᴢᴇ Cʟᴏɴᴇ</b>\n\n➜ <b>Nᴀᴍᴇ:</b> {clone['name']}\n➜ <b>Usᴇʀɴᴀᴍᴇ:</b> @{clone['username']}</b>"
    await query.message.edit_text(settings_text, reply_markup=InlineKeyboardMarkup(buttons))

# --- 1. START MESSAGE ---
@Client.on_callback_query(filters.regex("^set_start_"))
async def set_start_msg_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    buttons = [
        [InlineKeyboardButton('✏️ Sᴇᴛ Tᴇxᴛ', callback_data=f'start_text_{bot_id}')],
        [InlineKeyboardButton('🖼️ Sᴇᴛ Pʜᴏᴛᴏ', callback_data=f'start_photo_{bot_id}')],
        [InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]
    ]
    await query.message.edit_text("<b>🖼️ Sᴛᴀʀᴛ Mᴇssᴀɢᴇ Oᴘᴛɪᴏɴs</b>", reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^start_text_"))
async def set_start_text_handler(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    try:
        msg_req = await client.ask(chat_id=query.from_user.id, text="Sᴇɴᴅ ʏᴏᴜʀ ᴄᴜsᴛᴏᴍ sᴛᴀʀᴛ ᴍᴇssᴀɢᴇ.", filters=filters.text, timeout=300)
        await clone_db.update_clone_setting(bot_id, 'start_message', msg_req.text)
        await clone_db.update_clone_setting(bot_id, 'start_photo', None) # Clear photo
        await query.message.edit_text("✅ Sᴛᴀʀᴛ ᴍᴇssᴀɢᴇ ᴜᴘᴅᴀᴛᴇᴅ!")
    except:
        await query.message.edit_text("Tɪᴍᴇᴏᴜᴛ!")
    await asyncio.sleep(2)
    await set_start_msg_menu(client, query) # Go back to menu

@Client.on_callback_query(filters.regex("^start_photo_"))
async def set_start_photo_handler(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    try:
        msg_req = await client.ask(chat_id=query.from_user.id, text="Sᴇɴᴅ ᴀ ᴘʜᴏᴛᴏ. Tʜᴇ ᴄᴀᴘᴛɪᴏɴ ᴡɪʟʟ ʙᴇ ᴛʜᴇ sᴛᴀʀᴛ ᴛᴇxᴛ.", filters=filters.photo, timeout=300)
        await clone_db.update_clone_setting(bot_id, 'start_photo', msg_req.photo.file_id)
        await clone_db.update_clone_setting(bot_id, 'start_message', msg_req.caption.html if msg_req.caption else "")
        await query.message.edit_text("✅ Sᴛᴀʀᴛ ᴘʜᴏᴛᴏ ᴜᴘᴅᴀᴛᴇᴅ!")
    except:
        await query.message.edit_text("Tɪᴍᴇᴏᴜᴛ!")
    await asyncio.sleep(2)
    await set_start_msg_menu(client, query) # Go back to menu

# --- 2. FORCE SUB (and other features) ---
# ... (Include the full code for Force Sub, Auto Delete, and other features here as previously provided) ...


# --- DELETE CLONE (FIXED) ---
@Client.on_callback_query(filters.regex("^delete_"))
async def delete_clone_confirm(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    buttons = [
        [
            InlineKeyboardButton('✅ Yᴇs, Dᴇʟᴇᴛᴇ Iᴛ', callback_data=f'confirm_delete_{bot_id}'),
            InlineKeyboardButton('❌ Nᴏ, Cᴀɴᴄᴇʟ', callback_data=f'customize_{bot_id}')
        ]
    ]
    await query.message.edit_text("⚠️ <b>Aʀᴇ ʏᴏᴜ sᴜʀᴇ?</b>\n\nTʜɪs ᴡɪʟʟ ᴘᴇʀᴍᴀɴᴇɴᴛʟʏ sᴛᴏᴘ ᴀɴᴅ ᴅᴇʟᴇᴛᴇ ʏᴏᴜʀ ᴄʟᴏɴᴇ!", reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^confirm_delete_"))
async def confirm_delete_clone(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    
    # Stop the live session if it's running
    if bot_id in ACTIVE_CLONES:
        try:
            await ACTIVE_CLONES[bot_id].stop()
            del ACTIVE_CLONES[bot_id]
            logger.info(f"Successfully stopped session for bot {bot_id}")
        except Exception as e:
            logger.error(f"Error stopping bot {bot_id}: {e}")
            
    # Delete from the database
    await clone_db.delete_clone_by_id(bot_id)
    await query.answer("Clone stopped and deleted successfully!", show_alert=True)
    
    # Refresh the main clone list menu
    try:
        from plugins.clone_manager import clone_callback
        await clone_callback(client, query)
    except Exception as e:
        logger.error(f"Error refreshing clone list after delete: {e}")
        await query.message.edit_text("Clone deleted. Please go back to the main menu.")
