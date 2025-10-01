# plugins/clone_customize.py
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.clone_db import clone_db
import logging

logger = logging.getLogger(__name__)

# Store user states for multi-step input
user_states = {}

# -----------------------------
# Main customize clone menu
# -----------------------------
@Client.on_callback_query(filters.regex("^customize_"))
async def customize_clone(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    clone = await clone_db.get_clone(bot_id)
    
    if not clone:
        return await query.answer("Clone not found!", show_alert=True)
    
    if clone['user_id'] != query.from_user.id:
        return await query.answer("This is not your clone!", show_alert=True)
    
    settings = clone.get('settings', {})
    
    buttons = [
        [InlineKeyboardButton('📝 START TEXT', callback_data=f'set_start_text_{bot_id}'),
         InlineKeyboardButton('🖼️ START PICTURE', callback_data=f'set_start_pic_{bot_id}')],
        [InlineKeyboardButton('🔘 START BUTTON', callback_data=f'set_start_btn_{bot_id}'),
         InlineKeyboardButton('🔒 FORCE SUBSCRIBE', callback_data=f'set_fsub_{bot_id}')],
        [InlineKeyboardButton('🗄️ MONGO DB', callback_data=f'set_mongo_{bot_id}'),
         InlineKeyboardButton('📢 LOG CHANNEL', callback_data=f'set_log_{bot_id}')],
        [InlineKeyboardButton('🗂️ DATABASE CHANNEL', callback_data=f'set_db_channel_{bot_id}'),
         InlineKeyboardButton('👥 ADMINS', callback_data=f'set_admins_{bot_id}')],
        [InlineKeyboardButton('📊 BOT STATUS', callback_data=f'bot_status_{bot_id}'),
         InlineKeyboardButton('🔄 RESTART BOT', callback_data=f'restart_{bot_id}')],
        [InlineKeyboardButton(f"🔒 PUBLIC USE - {'✅' if settings.get('public_use', True) else '❌'}",
                               callback_data=f'toggle_public_{bot_id}')],
        [InlineKeyboardButton('🗑️ AUTO DELETE', callback_data=f'auto_delete_menu_{bot_id}')],
        [InlineKeyboardButton('⛔ DEACTIVATE BOT', callback_data=f'deactivate_{bot_id}'),
         InlineKeyboardButton('❌ DELETE BOT', callback_data=f'delete_{bot_id}')],
        [InlineKeyboardButton('⬅️ BACK', callback_data='clone')]
    ]
    
    settings_text = (
        f"<b>🤖 YOUR CLONE BOT - @{clone['username']}</b>\n\n"
        f"📝 Modify your clone bot settings using the buttons below.\n\n"
        f"⚠️ Clone inactive for a week will be auto deactivated.\n"
        f"⏰ Last Used: {clone.get('last_used', 'Never')}"
    )
    
    await query.message.edit_text(settings_text, reply_markup=InlineKeyboardMarkup(buttons))

# -----------------------------
# AUTO DELETE MENU
# -----------------------------
@Client.on_callback_query(filters.regex("^auto_delete_menu_"))
async def auto_delete_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    
    auto_del_enabled = settings.get('auto_delete', False)
    auto_del_time = settings.get('auto_delete_time', 300)
    
    minutes = auto_del_time // 60
    seconds = auto_del_time % 60
    time_display = f"{minutes}m {seconds}s" if minutes else f"{seconds}s"
    
    buttons = [
        [InlineKeyboardButton(f"{'✅ ENABLE' if not auto_del_enabled else '❌ DISABLE'}",
                              callback_data=f'toggle_autodel_{bot_id}')],
        [InlineKeyboardButton('CUSTOM TIME', callback_data=f'custom_del_time_{bot_id}')],
        [InlineKeyboardButton('⬅️ BACK', callback_data=f'customize_{bot_id}')]
    ]
    
    status = "ENABLED ✅" if auto_del_enabled else "DISABLED ❌"
    text = (
        f"<b>🗑️ AUTO DELETE SETTINGS</b>\n\n"
        f"<b>Status:</b> {status}\n"
        f"<b>Delete Time:</b> {time_display} ({auto_del_time}s)\n\n"
        f"<i>Files auto delete after specified time.</i>"
    )
    
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^toggle_autodel_"))
async def toggle_auto_delete(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('auto_delete', False)
    new_status = not current
    await clone_db.update_clone_setting(bot_id, 'auto_delete', new_status)
    await query.answer(f"Auto Delete {'✅ Enabled' if new_status else '❌ Disabled'}", show_alert=True)
    await auto_delete_menu(client, query)

@Client.on_callback_query(filters.regex("^custom_del_time_"))
async def custom_delete_time(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_states[query.from_user.id] = {'action': 'custom_del_time', 'bot_id': bot_id}
    await query.message.edit_text(
        "<b>⏰ ENTER CUSTOM DELETE TIME</b>\nSend time in seconds (min 20s)\nSend /cancel to cancel.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ CANCEL', callback_data=f'auto_delete_menu_{bot_id}')]])
    )
    await query.answer()

# -----------------------------
# FORCE SUBSCRIBE MENU
# -----------------------------
@Client.on_callback_query(filters.regex("^set_fsub_"))
async def force_sub_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    fsub_channels = settings.get('force_sub_channels', [])
    
    buttons = []
    for idx, channel in enumerate(fsub_channels[:6]):
        buttons.append([
            InlineKeyboardButton(f"📢 {channel}", callback_data=f'fsub_info_{bot_id}'),
            InlineKeyboardButton("❌ REMOVE", callback_data=f'remove_fsub_{bot_id}_{idx}')
        ])
    if len(fsub_channels) < 6:
        buttons.append([InlineKeyboardButton('➕ ADD CHANNEL', callback_data=f'add_fsub_{bot_id}')])
    if not fsub_channels:
        buttons.append([InlineKeyboardButton('No channels added', callback_data='none')])
    
    buttons.append([InlineKeyboardButton('⬅️ BACK', callback_data=f'customize_{bot_id}')])
    text = f"<b>🔒 FORCE SUBSCRIBE CHANNELS</b>\nTotal Channels: {len(fsub_channels)}/6"
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^add_fsub_"))
async def add_force_sub(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'add_fsub', 'bot_id': bot_id}
    await query.message.edit_text(
        "<b>📢 ADD FORCE SUBSCRIBE CHANNEL</b>\nSend channel username or ID.\nSend /cancel to cancel.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ CANCEL', callback_data=f'set_fsub_{bot_id}')]])
    )
    await query.answer()

@Client.on_callback_query(filters.regex("^remove_fsub_"))
async def remove_force_sub(client, query: CallbackQuery):
    parts = query.data.split("_")
    bot_id = int(parts[2])
    idx = int(parts[3])
    clone = await clone_db.get_clone(bot_id)
    fsub_channels = clone.get('settings', {}).get('force_sub_channels', [])
    if idx < len(fsub_channels):
        removed = fsub_channels.pop(idx)
        await clone_db.update_clone_setting(bot_id, 'force_sub_channels', fsub_channels)
        await query.answer(f"Removed: {removed}", show_alert=True)
    await force_sub_menu(client, query)

# -----------------------------
# START TEXT / PIC / BUTTON HANDLERS
# -----------------------------
@Client.on_callback_query(filters.regex("^set_start_text_"))
async def set_start_text(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_states[query.from_user.id] = {'action': 'start_text', 'bot_id': bot_id}
    await query.message.edit_text(
        "<b>📝 SET START TEXT</b>\nSend your start message.\nSend /cancel to cancel.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ CANCEL', callback_data=f'customize_{bot_id}')]])
    )
    await query.answer()

@Client.on_callback_query(filters.regex("^set_start_pic_"))
async def set_start_pic(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_states[query.from_user.id] = {'action': 'start_pic', 'bot_id': bot_id}
    await query.message.edit_text(
        "<b>🖼️ SET START PICTURE</b>\nSend photo URL or file.\nSend /remove to remove.\nSend /cancel to cancel.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ CANCEL', callback_data=f'customize_{bot_id}')]])
    )
    await query.answer()

@Client.on_callback_query(filters.regex("^set_start_btn_"))
async def set_start_button(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_states[query.from_user.id] = {'action': 'start_button', 'bot_id': bot_id}
    await query.message.edit_text(
        "<b>🔘 SET START BUTTON</b>\nSend: Button Text - URL\nSend /remove to remove.\nSend /cancel to cancel.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ CANCEL', callback_data=f'customize_{bot_id}')]])
    )
    await query.answer()

# -----------------------------
# TOGGLE PUBLIC USE
# -----------------------------
@Client.on_callback_query(filters.regex("^toggle_public_"))
async def toggle_public(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('public_use', True)
    new_status = not current
    await clone_db.update_clone_setting(bot_id, 'public_use', new_status)
    await query.answer(f"Public Use: {'✅ Enabled' if new_status else '❌ Disabled'}", show_alert=True)
    await customize_clone(client, query)

logger.info("✅ Clone customization module loaded with full features")
