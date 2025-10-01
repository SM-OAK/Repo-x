# plugins/clone_customize.py
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.clone_db import clone_db
from Script import script
import logging

logger = logging.getLogger(__name__)

# Store user states for multi-step processes
user_states = {}

# Customize clone callback
@Client.on_callback_query(filters.regex("^customize_"))
async def customize_clone(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    clone = await clone_db.get_clone(bot_id)
    
    if not clone:
        return await query.answer("Clone not found!", show_alert=True)
    
    if clone['user_id'] != query.from_user.id:
        return await query.answer("This is not your clone!", show_alert=True)
    
    settings = clone.get('settings', {})
    auto_del_status = "✅ ON" if settings.get('auto_delete', False) else "❌ OFF"
    auto_del_time = settings.get('auto_delete_time', 300)
    no_fw_status = "✅ ON" if settings.get('no_forward', False) else "❌ OFF"
    
    buttons = [
        [
            InlineKeyboardButton('📝 sᴛᴀʀᴛ ᴍsɢ', callback_data=f'set_start_{bot_id}'),
            InlineKeyboardButton('🖼️ sᴛᴀʀᴛ ᴘʜᴏᴛᴏ', callback_data=f'set_photo_{bot_id}')
        ],
        [
            InlineKeyboardButton('🔒 ғᴏʀᴄᴇ sᴜʙ', callback_data=f'set_fsub_{bot_id}'),
            InlineKeyboardButton('👥 ᴍᴏᴅᴇʀᴀᴛᴏʀs', callback_data=f'set_mods_{bot_id}')
        ],
        [
            InlineKeyboardButton(f'⏱️ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ {auto_del_status}', callback_data=f'set_autodel_{bot_id}'),
            InlineKeyboardButton(f'🕒 ᴛɪᴍᴇ: {auto_del_time}s', callback_data=f'set_time_{bot_id}')
        ],
        [
            InlineKeyboardButton(f'🚫 ɴᴏ ғᴏʀᴡᴀʀᴅ {no_fw_status}', callback_data=f'set_nofw_{bot_id}'),
            InlineKeyboardButton('🔑 ᴛᴏᴋᴇɴ', callback_data=f'view_token_{bot_id}')
        ],
        [
            InlineKeyboardButton('🔄 ᴍᴏᴅᴇ', callback_data=f'set_mode_{bot_id}'),
            InlineKeyboardButton('📊 sᴛᴀᴛs', callback_data=f'clone_stats_{bot_id}')
        ],
        [
            InlineKeyboardButton('🔙 ʙᴀᴄᴋ', callback_data='clone'),
            InlineKeyboardButton('🗑️ ᴅᴇʟᴇᴛᴇ', callback_data=f'delete_{bot_id}')
        ]
    ]
    
    settings_text = (
        f"<b>🛠️ Cᴜsᴛᴏᴍɪᴢᴇ Cʟᴏɴᴇ</b>\n\n"
        f"➜ <b>Nᴀᴍᴇ:</b> {clone['name']}\n"
        f"➜ <b>Usᴇʀɴᴀᴍᴇ:</b> @{clone['username']}\n"
        f"➜ <b>Sᴛᴀᴛᴜs:</b> {'🟢 Active' if clone.get('is_active') else '🔴 Inactive'}\n\n"
        f"Cᴏɴғɪɢᴜʀᴇ ʏᴏᴜʀ ᴄʟᴏɴᴇ sᴇᴛᴛɪɴɢs ᴜsɪɴɢ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ:"
    )
    
    await query.message.edit_text(settings_text, reply_markup=InlineKeyboardMarkup(buttons))

# Start message setting
@Client.on_callback_query(filters.regex("^set_start_"))
async def set_start_msg(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'start_msg', 'bot_id': bot_id}
    
    await query.message.edit_text(
        "<b>📝 Sᴇɴᴅ ʏᴏᴜʀ ᴄᴜsᴛᴏᴍ sᴛᴀʀᴛ ᴍᴇssᴀɢᴇ:</b>\n\n"
        "You can use HTML formatting.\n"
        "Use /cancel to cancel this operation.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ Cᴀɴᴄᴇʟ', callback_data=f'customize_{bot_id}')]])
    )
    await query.answer()

# Start photo setting
@Client.on_callback_query(filters.regex("^set_photo_"))
async def set_start_photo(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'start_photo', 'bot_id': bot_id}
    
    await query.message.edit_text(
        "<b>🖼️ Sᴇɴᴅ ʏᴏᴜʀ sᴛᴀʀᴛ ᴘʜᴏᴛᴏ:</b>\n\n"
        "Send a photo or photo URL.\n"
        "Send /remove to remove current photo.\n"
        "Use /cancel to cancel.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ Cᴀɴᴄᴇʟ', callback_data=f'customize_{bot_id}')]])
    )
    await query.answer()

# Force sub setting
@Client.on_callback_query(filters.regex("^set_fsub_"))
async def set_force_sub(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'force_sub', 'bot_id': bot_id}
    
    await query.message.edit_text(
        "<b>🔒 Sᴇɴᴅ ᴄʜᴀɴɴᴇʟ ID ᴏʀ Usᴇʀɴᴀᴍᴇ:</b>\n\n"
        "Examples:\n"
        "<code>-100123456789</code>\n"
        "<code>@your_channel</code>\n\n"
        "Send /remove to disable force sub.\n"
        "Use /cancel to cancel.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ Cᴀɴᴄᴇʟ', callback_data=f'customize_{bot_id}')]])
    )
    await query.answer()

# Moderators setting
@Client.on_callback_query(filters.regex("^set_mods_"))
async def set_moderators(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    mods = clone.get('settings', {}).get('moderators', [])
    
    user_states[query.from_user.id] = {'action': 'moderators', 'bot_id': bot_id}
    
    mods_text = "\n".join([f"• <code>{mod}</code>" for mod in mods]) if mods else "No moderators added."
    
    await query.message.edit_text(
        f"<b>👥 Mᴀɴᴀɢᴇ Mᴏᴅᴇʀᴀᴛᴏʀs</b>\n\n"
        f"<b>Cᴜʀʀᴇɴᴛ Mᴏᴅᴇʀᴀᴛᴏʀs:</b>\n{mods_text}\n\n"
        f"<b>Tᴏ Aᴅᴅ:</b> Send user ID\n"
        f"<b>Tᴏ Rᴇᴍᴏᴠᴇ:</b> Send <code>/remove user_id</code>\n"
        f"Use /cancel to cancel.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]])
    )
    await query.answer()

# Auto delete toggle
@Client.on_callback_query(filters.regex("^set_autodel_"))
async def set_auto_delete(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('auto_delete', False)
    
    # Toggle the status
    new_status = not current
    await clone_db.update_clone_setting(bot_id, 'auto_delete', new_status)
    
    await query.answer(f"Auto Delete: {'✅ Enabled' if new_status else '❌ Disabled'}", show_alert=True)
    await customize_clone(client, query)

# Auto delete time setting
@Client.on_callback_query(filters.regex("^set_time_"))
async def set_delete_time(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    current_time = clone.get('settings', {}).get('auto_delete_time', 300)
    
    buttons = [
        [
            InlineKeyboardButton('20s', callback_data=f'time_{bot_id}_20'),
            InlineKeyboardButton('1m', callback_data=f'time_{bot_id}_60'),
            InlineKeyboardButton('5m', callback_data=f'time_{bot_id}_300')
        ],
        [
            InlineKeyboardButton('10m', callback_data=f'time_{bot_id}_600'),
            InlineKeyboardButton('30m', callback_data=f'time_{bot_id}_1800'),
            InlineKeyboardButton('1h', callback_data=f'time_{bot_id}_3600')
        ],
        [InlineKeyboardButton('✏️ Cᴜsᴛᴏᴍ', callback_data=f'time_custom_{bot_id}')],
        [InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]
    ]
    
    await query.message.edit_text(
        f"<b>🕒 Aᴜᴛᴏ Dᴇʟᴇᴛᴇ Tɪᴍᴇ</b>\n\n"
        f"Cᴜʀʀᴇɴᴛ: <b>{current_time}s</b> ({current_time // 60}m {current_time % 60}s)\n\n"
        f"Select a preset or choose custom:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    await query.answer()

@Client.on_callback_query(filters.regex("^time_\\d+_\\d+$"))
async def update_delete_time(client, query: CallbackQuery):
    parts = query.data.split("_")
    bot_id = int(parts[1])
    time_seconds = int(parts[2])
    
    await clone_db.update_clone_setting(bot_id, 'auto_delete_time', time_seconds)
    await query.answer(f"Time updated to {time_seconds}s!", show_alert=True)
    await customize_clone(client, query)

@Client.on_callback_query(filters.regex("^time_custom_"))
async def custom_delete_time(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'custom_time', 'bot_id': bot_id}
    
    await query.message.edit_text(
        "<b>✏️ Eɴᴛᴇʀ Cᴜsᴛᴏᴍ Tɪᴍᴇ</b>\n\n"
        "Send time in seconds (minimum 20).\n"
        "Example: <code>120</code> for 2 minutes\n\n"
        "Use /cancel to cancel.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ Cᴀɴᴄᴇʟ', callback_data=f'customize_{bot_id}')]])
    )
    await query.answer()

# No forward toggle
@Client.on_callback_query(filters.regex("^set_nofw_"))
async def toggle_no_forward(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('no_forward', False)
    
    new_status = not current
    await clone_db.update_clone_setting(bot_id, 'no_forward', new_status)
    
    await query.answer(f"No Forward: {'✅ Enabled' if new_status else '❌ Disabled'}", show_alert=True)
    await customize_clone(client, query)

# Mode setting
@Client.on_callback_query(filters.regex("^set_mode_"))
async def set_mode(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    current_mode = clone.get('settings', {}).get('mode', 'public')
    
    buttons = [
        [
            InlineKeyboardButton('🌍 Pᴜʙʟɪᴄ' if current_mode != 'public' else '✅ Pᴜʙʟɪᴄ', callback_data=f'mode_{bot_id}_public'),
            InlineKeyboardButton('🔒 Pʀɪᴠᴀᴛᴇ' if current_mode != 'private' else '✅ Pʀɪᴠᴀᴛᴇ', callback_data=f'mode_{bot_id}_private')
        ],
        [InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]
    ]
    
    await query.message.edit_text(
        f"<b>🔄 Bᴏᴛ Mᴏᴅᴇ</b>\n\n"
        f"Cᴜʀʀᴇɴᴛ: <b>{current_mode.title()}</b>\n\n"
        f"<b>🌍 Public:</b> Anyone can upload files\n"
        f"<b>🔒 Private:</b> Only owner and moderators can upload",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    await query.answer()

@Client.on_callback_query(filters.regex("^mode_"))
async def update_mode(client, query: CallbackQuery):
    parts = query.data.split("_")
    bot_id = int(parts[1])
    mode = parts[2]
    
    await clone_db.update_clone_setting(bot_id, 'mode', mode)
    await query.answer(f"Mode updated to {mode.title()}!", show_alert=True)
    await customize_clone(client, query)

# View token
@Client.on_callback_query(filters.regex("^view_token_"))
async def view_token(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    
    if clone['user_id'] != query.from_user.id:
        return await query.answer("Access denied!", show_alert=True)
    
    token = clone['bot_token']
    await query.answer(f"Token: {token[:10]}...{token[-5:]}", show_alert=True)

# Clone stats
@Client.on_callback_query(filters.regex("^clone_stats_"))
async def clone_stats(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    users = await clone_db.get_clone_users_count(bot_id)
    settings = clone.get('settings', {})
    
    stats_text = (
        f"<b>📊 Cʟᴏɴᴇ Sᴛᴀᴛɪsᴛɪᴄs</b>\n\n"
        f"🤖 <b>Bᴏᴛ:</b> @{clone['username']}\n"
        f"📝 <b>Nᴀᴍᴇ:</b> {clone['name']}\n"
        f"👥 <b>Usᴇʀs:</b> {users}\n"
        f"📅 <b>Cʀᴇᴀᴛᴇᴅ:</b> {clone.get('created_at', 'N/A')}\n\n"
        f"<b>⚙️ Sᴇᴛᴛɪɴɢs:</b>\n"
        f"• Auto Delete: {'✅' if settings.get('auto_delete') else '❌'}\n"
        f"• Delete Time: {settings.get('auto_delete_time', 300)}s\n"
        f"• No Forward: {'✅' if settings.get('no_forward') else '❌'}\n"
        f"• Mode: {settings.get('mode', 'public').title()}\n"
        f"• Moderators: {len(settings.get('moderators', []))}"
    )
    
    await query.message.edit_text(
        stats_text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]])
    )
    await query.answer()

# Delete clone
@Client.on_callback_query(filters.regex("^delete_(?!clone)"))
async def delete_clone_confirm(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    
    buttons = [
        [
            InlineKeyboardButton('✅ Yᴇs, Dᴇʟᴇᴛᴇ', callback_data=f'confirm_delete_{bot_id}'),
            InlineKeyboardButton('❌ Nᴏ', callback_data=f'customize_{bot_id}')
        ]
    ]
    
    await query.message.edit_text(
        "⚠️ <b>Aʀᴇ ʏᴏᴜ sᴜʀᴇ?</b>\n\n"
        "This will permanently delete your clone bot!\n"
        "This action cannot be undone.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    await query.answer()

@Client.on_callback_query(filters.regex("^confirm_delete_"))
async def confirm_delete_clone(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    
    if clone['user_id'] != query.from_user.id:
        return await query.answer("Access denied!", show_alert=True)
    
    await clone_db.delete_clone_by_id(bot_id)
    await query.message.edit_text(
        "✅ <b>Cʟᴏɴᴇ Dᴇʟᴇᴛᴇᴅ!</b>\n\n"
        "Your clone bot has been successfully deleted.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data='clone')]])
    )
    await query.answer()

# Handle user input for settings
@Client.on_message(filters.private & filters.text, group=2)
async def handle_setting_input(client, message):
    user_id = message.from_user.id
    
    if user_id not in user_states:
        return
    
    state = user_states[user_id]
    action = state['action']
    bot_id = state['bot_id']
    
    # Cancel operation
    if message.text == '/cancel':
        del user_states[user_id]
        buttons = [[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]]
        return await message.reply("❌ Operation cancelled!", reply_markup=InlineKeyboardMarkup(buttons))
    
    try:
        # Start message
        if action == 'start_msg':
            await clone_db.update_clone_setting(bot_id, 'start_message', message.text)
            del user_states[user_id]
            await message.reply(
                "✅ Start message updated!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]])
            )
        
        # Start photo
        elif action == 'start_photo':
            if message.text == '/remove':
                await clone_db.update_clone_setting(bot_id, 'start_photo', None)
                del user_states[user_id]
                return await message.reply(
                    "✅ Start photo removed!",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]])
                )
            
            photo_url = message.text if message.text.startswith('http') else None
            if photo_url:
                await clone_db.update_clone_setting(bot_id, 'start_photo', photo_url)
                del user_states[user_id]
                await message.reply(
                    "✅ Start photo updated!",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]])
                )
            else:
                await message.reply("❌ Invalid photo URL! Send a valid URL or send a photo directly.")
        
        # Force sub
        elif action == 'force_sub':
            if message.text == '/remove':
                await clone_db.update_clone_setting(bot_id, 'force_sub_channel', None)
                del user_states[user_id]
                return await message.reply(
                    "✅ Force subscription disabled!",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]])
                )
            
            channel = message.text
            await clone_db.update_clone_setting(bot_id, 'force_sub_channel', channel)
            del user_states[user_id]
            await message.reply(
                "✅ Force subscription updated!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]])
            )
        
        # Moderators
        elif action == 'moderators':
            if message.text.startswith('/remove'):
                try:
                    mod_id = int(message.text.split()[1])
                    await clone_db.remove_moderator(bot_id, mod_id)
                    del user_states[user_id]
                    await message.reply(
                        f"✅ Moderator {mod_id} removed!",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]])
                    )
                except:
                    await message.reply("❌ Invalid format! Use: /remove user_id")
            else:
                try:
                    mod_id = int(message.text)
                    await clone_db.add_moderator(bot_id, mod_id)
                    del user_states[user_id]
                    await message.reply(
                        f"✅ Moderator {mod_id} added!",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]])
                    )
                except:
                    await message.reply("❌ Invalid user ID! Send a valid number.")
        
        # Custom time
        elif action == 'custom_time':
            try:
                time_sec = int(message.text)
                if time_sec < 20:
                    return await message.reply("❌ Minimum time is 20 seconds!")
                
                await clone_db.update_clone_setting(bot_id, 'auto_delete_time', time_sec)
                del user_states[user_id]
                minutes = time_sec // 60
                seconds = time_sec % 60
                time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
                await message.reply(
                    f"✅ Auto delete time set to {time_sec}s ({time_str})!",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]])
                )
            except:
                await message.reply("❌ Invalid number! Send a valid number of seconds.")
    
    except Exception as e:
        logger.error(f"Error handling input: {e}")
        await message.reply(
            f"❌ Error: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]])
        )

# Handle photo input
@Client.on_message(filters.private & filters.photo, group=2)
async def handle_photo_input(client, message):
    user_id = message.from_user.id
    
    if user_id not in user_states:
        return
    
    state = user_states[user_id]
    if state['action'] != 'start_photo':
        return
    
    bot_id = state['bot_id']
    photo_id = message.photo.file_id
    
    await clone_db.update_clone_setting(bot_id, 'start_photo', photo_id)
    del user_states[user_id]
    await message.reply(
        "✅ Start photo updated!",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]])
    )

logger.info("✅ Clone customization module loaded")
