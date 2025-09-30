from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.clone_db import clone_db
from bot import ACTIVE_CLONES # For robust delete
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
    
    settings_text = (
        f"<b>🛠️ Cᴜsᴛᴏᴍɪᴢᴇ Cʟᴏɴᴇ</b>\n\n"
        f"➜ <b>Nᴀᴍᴇ:</b> {clone['name']}\n"
        f"➜ <b>Usᴇʀɴᴀᴍᴇ:</b> @{clone['username']}</b>"
    )
    
    await query.message.edit_text(settings_text, reply_markup=InlineKeyboardMarkup(buttons))


# --- 1. START MESSAGE ---

@Client.on_callback_query(filters.regex("^set_start_"))
async def set_start_msg(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    buttons = [
        [
            InlineKeyboardButton('✏️ Sᴇᴛ Tᴇxᴛ', callback_data=f'start_text_{bot_id}'),
            InlineKeyboardButton('🖼️ Sᴇᴛ Pʜᴏᴛᴏ', callback_data=f'start_photo_{bot_id}')
        ],
        [InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]
    ]
    await query.message.edit_text("<b>🖼️ Sᴛᴀʀᴛ Mᴇssᴀɢᴇ Oᴘᴛɪᴏɴs</b>", reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^start_text_"))
async def set_start_text_msg(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    # ... (code from previous step)

@Client.on_callback_query(filters.regex("^start_photo_"))
async def set_start_photo_msg(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    # ... (code from previous step)


# --- 2. FORCE SUB ---

@Client.on_callback_query(filters.regex("^set_fsub_"))
async def set_force_sub(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    # ... (code from previous step)

@Client.on_callback_query(filters.regex("^add_fsub_"))
async def add_fsub_channel_handler(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    # ... (code from previous step)

@Client.on_callback_query(filters.regex("^rm_fsub_"))
async def remove_fsub_channel_handler(client, query: CallbackQuery):
    _, _, bot_id, channel_id = query.data.split("_")
    # ... (code from previous step)


# --- 3. AUTO DELETE ---

@Client.on_callback_query(filters.regex("^set_autodel_"))
async def set_auto_delete(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    status = "Eɴᴀʙʟᴇᴅ ✅" if settings.get('auto_delete') else "Dɪsᴀʙʟᴇᴅ ❌"
    time = settings.get('auto_delete_time', 1800) // 60 # Show in minutes
    
    buttons = [
        [InlineKeyboardButton('⏱️ Cʜᴀɴɢᴇ Tɪᴍᴇ', callback_data=f'autodel_time_{bot_id}')],
        [
            InlineKeyboardButton('✅ Eɴᴀʙʟᴇ', callback_data=f'toggle_autodel_{bot_id}_true'),
            InlineKeyboardButton('❌ Dɪsᴀʙʟᴇ', callback_data=f'toggle_autodel_{bot_id}_false')
        ],
        [InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]
    ]
    
    text = f"<b>⏱️ Aᴜᴛᴏ Dᴇʟᴇᴛᴇ Sᴇᴛᴛɪɴɢs</b>\n\nCᴜʀʀᴇɴᴛ Sᴛᴀᴛᴜs: <b>{status}</b>\nDᴇʟᴇᴛᴇ Aғᴛᴇʀ: <b>{time} ᴍɪɴᴜᴛᴇs</b>"
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^toggle_autodel_"))
async def toggle_auto_delete(client, query: CallbackQuery):
    _, _, bot_id, status_str = query.data.split("_")
    status = status_str == 'true'
    await clone_db.update_clone_setting(int(bot_id), 'auto_delete', status)
    await query.answer(f"Auto Delete {'Enabled' if status else 'Disabled'}!", show_alert=True)
    await set_auto_delete(client, query) # Refresh menu

@Client.on_callback_query(filters.regex("^autodel_time_"))
async def change_autodel_time(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    back_button = InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'set_autodel_{bot_id}')]])
    try:
        msg = await client.ask(
            chat_id=query.from_user.id,
            text="Sᴇɴᴅ ᴛʜᴇ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇ ɪɴ **ᴍɪɴᴜᴛᴇs**.",
            filters=filters.text, timeout=300
        )
        time_in_minutes = int(msg.text)
        time_in_seconds = time_in_minutes * 60
        await clone_db.update_clone_setting(bot_id, 'auto_delete_time', time_in_seconds)
        await query.answer("Time updated successfully!", show_alert=True)
    except:
        await query.answer("Invalid input or timeout.", show_alert=True)
    await set_auto_delete(client, query) # Refresh menu


# --- 4. OTHER UTILITIES ---

@Client.on_callback_query(filters.regex("^clone_stats_"))
async def clone_stats(client, query: CallbackQuery):
    # ... (code is the same)

@Client.on_callback_query(filters.regex("^restart_"))
async def restart_clone(client, query: CallbackQuery):
    # ... (code is the same)

@Client.on_callback_query(filters.regex("^delete_"))
async def delete_clone_confirm(client, query: CallbackQuery):
    # ... (code is the same)

@Client.on_callback_query(filters.regex("^confirm_delete_"))
async def confirm_delete_clone(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    # ... (Robust delete code from previous step)
    if bot_id in ACTIVE_CLONES:
        await ACTIVE_CLONES[bot_id].stop()
        del ACTIVE_CLONES[bot_id]
    await clone_db.delete_clone_by_id(bot_id)
    await query.answer("Clone stopped and deleted successfully!", show_alert=True)
    # Refresh the main clone list
    from plugins.clone_manager import clone_callback # Import here to avoid circular dependency
    await clone_callback(client, query)
