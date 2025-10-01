# plugins/clone_customize.py
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.clone_db import clone_db
import logging

logger = logging.getLogger(__name__)

# ------------------------
# USER STATES FOR MULTI-STEP INPUTS
# ------------------------
user_states = {}

# ------------------------
# HELPER FUNCTION TO CREATE BACK BUTTON
# ------------------------
def back_button(bot_id):
    return [[InlineKeyboardButton("⬅️ BACK", callback_data=f"customize_{bot_id}")]]


# ------------------------
# MAIN CUSTOMIZE MENU
# ------------------------
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
        [InlineKeyboardButton('START TEXT', callback_data=f'set_start_text_{bot_id}'),
         InlineKeyboardButton('START PICTURE', callback_data=f'set_start_pic_{bot_id}')],
        [InlineKeyboardButton('START BUTTON', callback_data=f'set_start_btn_{bot_id}'),
         InlineKeyboardButton('FORCE SUBSCRIBE', callback_data=f'set_fsub_{bot_id}')],
        [InlineKeyboardButton('MONGO DB', callback_data=f'set_mongo_{bot_id}'),
         InlineKeyboardButton('LOG CHANNEL', callback_data=f'set_log_{bot_id}')],
        [InlineKeyboardButton('ADMINS', callback_data=f'set_admins_{bot_id}'),
         InlineKeyboardButton('BOT STATUS', callback_data=f'bot_status_{bot_id}')],
        [InlineKeyboardButton('DATABASE CHANNEL', callback_data=f'set_db_channel_{bot_id}'),
         InlineKeyboardButton('RESTART BOT', callback_data=f'restart_{bot_id}')],
        [InlineKeyboardButton(f"🔒 PUBLIC USE - {'✅' if settings.get('public_use', True) else '❌'}",
                               callback_data=f'toggle_public_{bot_id}')],
        [InlineKeyboardButton('AUTO DELETE', callback_data=f'auto_delete_menu_{bot_id}')],
        [InlineKeyboardButton('DEACTIVATE BOT', callback_data=f'deactivate_{bot_id}'),
         InlineKeyboardButton('DELETE BOT', callback_data=f'delete_{bot_id}')],
        [InlineKeyboardButton('⬅️ BACK', callback_data='clone')]
    ]

    text = (
        f"<b>🤖 CLONE BOT - @{clone['username']}</b>\n\n"
        f"📝 Customize your clone bot below.\n"
        f"⚠️ Note: Inactive clones for 1 week are auto-deactivated.\n\n"
        f"⏰ Last used: {clone.get('last_used', 'Never')}"
    )
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))


# ------------------------
# START TEXT
# ------------------------
@Client.on_callback_query(filters.regex("^set_start_text_"))
async def set_start_text(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_states[query.from_user.id] = {'action': 'start_text', 'bot_id': bot_id}
    await query.message.edit_text(
        "<b>📝 SET START TEXT</b>\nSend your custom start message.\nYou can use HTML formatting.\n\nSend /cancel to cancel.",
        reply_markup=InlineKeyboardMarkup(back_button(bot_id))
    )
    await query.answer()


# ------------------------
# START PICTURE
# ------------------------
@Client.on_callback_query(filters.regex("^set_start_pic_"))
async def set_start_picture(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_states[query.from_user.id] = {'action': 'start_pic', 'bot_id': bot_id}
    await query.message.edit_text(
        "<b>🖼️ SET START PICTURE</b>\nSend photo or photo URL.\nSend /remove to remove current photo.\n\nSend /cancel to cancel.",
        reply_markup=InlineKeyboardMarkup(back_button(bot_id))
    )
    await query.answer()


# ------------------------
# START BUTTON
# ------------------------
@Client.on_callback_query(filters.regex("^set_start_btn_"))
async def set_start_button(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_states[query.from_user.id] = {'action': 'start_button', 'bot_id': bot_id}
    await query.message.edit_text(
        "<b>🔘 SET START BUTTON</b>\nSend in format:\n<code>Button Text - https://example.com</code>\nSend /remove to remove.\nSend /cancel to cancel.",
        reply_markup=InlineKeyboardMarkup(back_button(bot_id))
    )
    await query.answer()


# ------------------------
# FORCE SUBSCRIBE CHANNELS
# ------------------------
@Client.on_callback_query(filters.regex("^set_fsub_"))
async def force_sub_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    fsub = clone.get('settings', {}).get('force_sub_channels', [])
    buttons = [[InlineKeyboardButton(f"📢 {c}", callback_data='fsub_info'),
                InlineKeyboardButton("❌ REMOVE", callback_data=f'remove_fsub_{bot_id}_{i}')] for i, c in enumerate(fsub)]
    if len(fsub) < 6:
        buttons.append([InlineKeyboardButton('➕ ADD CHANNEL', callback_data=f'add_fsub_{bot_id}')])
    if not fsub:
        buttons = [[InlineKeyboardButton('No channels added', callback_data='none')],
                   [InlineKeyboardButton('➕ ADD CHANNEL', callback_data=f'add_fsub_{bot_id}')]]
    buttons.append([InlineKeyboardButton('⬅️ BACK', callback_data=f'customize_{bot_id}')])
    text = f"<b>🔒 FORCE SUBSCRIBE CHANNELS</b>\nTotal Channels: {len(fsub)}/6\nUsers must join these."
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))


# ------------------------
# ADMINS MANAGEMENT
# ------------------------
@Client.on_callback_query(filters.regex("^set_admins_"))
async def set_admins(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    admins = clone.get('settings', {}).get('admins', [])
    buttons = [[InlineKeyboardButton(f"👤 {a}", callback_data='admin_info'),
                InlineKeyboardButton("❌", callback_data=f'remove_admin_{bot_id}_{i}')] for i, a in enumerate(admins)]
    if not admins:
        buttons = [[InlineKeyboardButton('No admins', callback_data='none')]]
    buttons.append([InlineKeyboardButton('➕ ADD ADMIN', callback_data=f'add_admin_{bot_id}')])
    buttons.append([InlineKeyboardButton('⬅️ BACK', callback_data=f'customize_{bot_id}')])
    text = f"<b>👥 ADMINS MANAGEMENT</b>\nTotal Admins: {len(admins)}"
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))


# ------------------------
# HANDLE USER INPUT FOR MULTI-STEP SETTINGS
# ------------------------
@Client.on_message(filters.private & (filters.text | filters.photo))
async def handle_setting_input(client, message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return

    state = user_states[user_id]
    action = state['action']
    bot_id = state['bot_id']

    # CANCEL
    if message.text == '/cancel':
        del user_states[user_id]
        await message.reply("❌ Operation cancelled!", reply_markup=InlineKeyboardMarkup(back_button(bot_id)))
        return

    try:
        # START TEXT
        if action == 'start_text' and message.text:
            await clone_db.update_clone_setting(bot_id, 'start_message', message.text)
            del user_states[user_id]
            await message.reply("✅ Start text updated!", reply_markup=InlineKeyboardMarkup(back_button(bot_id)))

        # START PICTURE
        elif action == 'start_pic':
            if message.text == '/remove':
                await clone_db.update_clone_setting(bot_id, 'start_photo', None)
                del user_states[user_id]
                await message.reply("✅ Start photo removed!", reply_markup=InlineKeyboardMarkup(back_button(bot_id)))
            elif message.photo:
                photo_id = message.photo.file_id
                await clone_db.update_clone_setting(bot_id, 'start_photo', photo_id)
                del user_states[user_id]
                await message.reply("✅ Start photo updated!", reply_markup=InlineKeyboardMarkup(back_button(bot_id)))
            elif message.text.startswith('http'):
                await clone_db.update_clone_setting(bot_id, 'start_photo', message.text)
                del user_states[user_id]
                await message.reply("✅ Start photo URL set!", reply_markup=InlineKeyboardMarkup(back_button(bot_id)))
            else:
                await message.reply("❌ Invalid photo or URL!")

        # START BUTTON
        elif action == 'start_button' and message.text:
            if message.text == '/remove':
                await clone_db.update_clone_setting(bot_id, 'start_button', None)
            else:
                await clone_db.update_clone_setting(bot_id, 'start_button', message.text)
            del user_states[user_id]
            await message.reply("✅ Start button updated!", reply_markup=InlineKeyboardMarkup(back_button(bot_id)))

        # CUSTOM AUTO DELETE TIME
        elif action == 'custom_del_time' and message.text:
            time_sec = int(message.text)
            if time_sec < 20:
                return await message.reply("❌ Minimum 20 seconds!")
            await clone_db.update_clone_setting(bot_id, 'auto_delete_time', time_sec)
            del user_states[user_id]
            await message.reply(f"✅ Auto delete set to {time_sec}s", reply_markup=InlineKeyboardMarkup(back_button(bot_id)))

    except Exception as e:
        logger.error(f"Error handling input: {e}")
        await message.reply(f"❌ Error: {e}", reply_markup=InlineKeyboardMarkup(back_button(bot_id)))


logger.info("✅ Full clone customization module loaded")
