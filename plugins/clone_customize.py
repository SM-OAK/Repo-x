import re
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.clone_db import clone_db
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
    back_button = InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'set_start_{bot_id}')]])
    try:
        msg_req = await client.ask(
            chat_id=query.from_user.id,
            text="Sᴇɴᴅ ʏᴏᴜʀ ᴄᴜsᴛᴏᴍ sᴛᴀʀᴛ ᴍᴇssᴀɢᴇ ɴᴏᴡ.",
            filters=filters.text, timeout=300
        )
        await clone_db.update_clone_setting(bot_id, 'start_message', msg_req.text)
        await clone_db.update_clone_setting(bot_id, 'start_photo', None)
        await query.message.edit_text("✅ Sᴛᴀʀᴛ ᴍᴇssᴀɢᴇ ᴜᴘᴅᴀᴛᴇᴅ!", reply_markup=back_button)
    except:
        await query.message.edit_text("Tɪᴍᴇᴏᴜᴛ!", reply_markup=back_button)

@Client.on_callback_query(filters.regex("^start_photo_"))
async def set_start_photo_msg(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    back_button = InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'set_start_{bot_id}')]])
    try:
        msg_req = await client.ask(
            chat_id=query.from_user.id,
            text="Sᴇɴᴅ ᴀ ᴘʜᴏᴛᴏ. Tʜᴇ ᴄᴀᴘᴛɪᴏɴ ᴡɪʟʟ ʙᴇ ᴜsᴇᴅ ᴀs ᴛʜᴇ sᴛᴀʀᴛ ᴛᴇxᴛ.",
            filters=filters.photo, timeout=300
        )
        await clone_db.update_clone_setting(bot_id, 'start_photo', msg_req.photo.file_id)
        await clone_db.update_clone_setting(bot_id, 'start_message', msg_req.caption.html if msg_req.caption else None)
        await query.message.edit_text("✅ Sᴛᴀʀᴛ ᴘʜᴏᴛᴏ ᴜᴘᴅᴀᴛᴇᴅ!", reply_markup=back_button)
    except:
        await query.message.edit_text("Tɪᴍᴇᴏᴜᴛ!", reply_markup=back_button)


# --- 2. FORCE SUB ---

@Client.on_callback_query(filters.regex("^set_fsub_"))
async def set_force_sub(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    channels = clone.get('settings', {}).get('force_sub_channels', [])
    buttons = []
    for channel in channels:
        buttons.append([InlineKeyboardButton(f'❌ {channel}', callback_data=f'rm_fsub_{bot_id}_{channel}')])
    if len(channels) < 4:
        buttons.append([InlineKeyboardButton('➕ Aᴅᴅ Cʜᴀɴɴᴇʟ', callback_data=f'add_fsub_{bot_id}')])
    buttons.append([InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')])
    text = f"<b>🔒 Fᴏʀᴄᴇ Sᴜʙ Sᴇᴛᴛɪɴɢs</b>\n\nYou have added {len(channels)} of 4 channels."
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^add_fsub_"))
async def add_fsub_channel_handler(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    try:
        msg = await client.ask(
            chat_id=query.from_user.id,
            text="Sᴇɴᴅ ᴛʜᴇ ID ᴏғ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴀᴅᴅ.",
            filters=filters.text, timeout=300
        )
        channel_id = int(msg.text)
        await clone_db.add_fsub_channel(bot_id, channel_id)
        await query.answer("Channel added successfully!", show_alert=True)
    except:
        await query.answer("Invalid ID or timeout.", show_alert=True)
    await set_force_sub(client, query)

@Client.on_callback_query(filters.regex("^rm_fsub_"))
async def remove_fsub_channel_handler(client, query: CallbackQuery):
    _, _, bot_id, channel_id = query.data.split("_")
    await clone_db.remove_fsub_channel(int(bot_id), int(channel_id))
    await query.answer("Channel removed successfully!", show_alert=True)
    await set_force_sub(client, query)


# --- 3. AUTO DELETE ---

@Client.on_callback_query(filters.regex("^set_autodel_"))
async def set_auto_delete(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    status = "Eɴᴀʙʟᴇᴅ ✅" if settings.get('auto_delete') else "Dɪsᴀʙʟᴇᴅ ❌"
    time = settings.get('auto_delete_time', 1800) // 60
    buttons = [
        [InlineKeyboardButton('⏱️ Cʜᴀɴɢᴇ Tɪᴍᴇ', callback_data=f'autodel_time_{bot_id}')],
        [
            InlineKeyboardButton('✅ Eɴᴀʙʟᴇ', callback_data=f'toggle_autodel_{bot_id}_true'),
            InlineKeyboardButton('❌ Dɪsᴀʙʟᴇ', callback_data=f'toggle_autodel_{bot_id}_false')
        ],
        [InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]
    ]
    text = f"<b>⏱️ Aᴜᴛᴏ Dᴇʟᴇᴛᴇ Sᴇᴛᴛɪɴɢs</b>\n\nSᴛᴀᴛᴜs: <b>{status}</b>\nDᴇʟᴇᴛᴇ Aғᴛᴇʀ: <b>{time} ᴍɪɴᴜᴛᴇs</b>"
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^toggle_autodel_"))
async def toggle_auto_delete(client, query: CallbackQuery):
    _, _, bot_id, status_str = query.data.split("_")
    status = status_str == 'true'
    await clone_db.update_clone_setting(int(bot_id), 'auto_delete', status)
    await query.answer(f"Auto Delete {'Enabled' if status else 'Disabled'}!", show_alert=True)
    await set_auto_delete(client, query)

@Client.on_callback_query(filters.regex("^autodel_time_"))
async def change_autodel_time(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    try:
        msg = await client.ask(
            chat_id=query.from_user.id,
            text="Sᴇɴᴅ ᴛʜᴇ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ ᴛɪᴍᴇ ɪɴ **ᴍɪɴᴜᴛᴇs**.",
            filters=filters.text, timeout=300
        )
        time_in_seconds = int(msg.text) * 60
        await clone_db.update_clone_setting(bot_id, 'auto_delete_time', time_in_seconds)
        await query.answer("Time updated successfully!", show_alert=True)
    except:
        await query.answer("Invalid input or timeout.", show_alert=True)
    await set_auto_delete(client, query)


# --- 4. OTHER UTILITIES ---

@Client.on_callback_query(filters.regex("^clone_stats_"))
async def clone_stats(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    users = await clone_db.get_clone_users_count(bot_id)
    await query.message.edit_text(
        f"<b>📊 Cʟᴏɴᴇ Sᴛᴀᴛs</b>\n\nBᴏᴛ: @{clone['username']}\nUsᴇʀs: {users}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]])
    )

@Client.on_callback_query(filters.regex("^restart_"))
async def restart_clone(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    await query.answer("This feature is not implemented yet.", show_alert=True)

@Client.on_callback_query(filters.regex("^delete_"))
async def delete_clone_confirm(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    buttons = [
        [
            InlineKeyboardButton('✅ Yᴇs', callback_data=f'confirm_delete_{bot_id}'),
            InlineKeyboardButton('❌ Nᴏ', callback_data=f'customize_{bot_id}')
        ]
    ]
    await query.message.edit_text("⚠️ <b>Aʀᴇ ʏᴏᴜ sᴜʀᴇ?</b>", reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^confirm_delete_"))
async def confirm_delete_clone(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    if bot_id in ACTIVE_CLONES:
        try:
            await ACTIVE_CLONES[bot_id].stop()
        except: pass
        del ACTIVE_CLONES[bot_id]
    await clone_db.delete_clone_by_id(bot_id)
    await query.answer("Clone stopped and deleted successfully!", show_alert=True)
    try:
        from plugins.clone_manager import clone_callback
        await clone_callback(client, query)
    except:
        await query.message.edit_text("Clone deleted. Please go back to the main menu.")

