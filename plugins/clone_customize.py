# plugins/clone_customize.py
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.clone_db import clone_db
from Script import script
import logging

logger = logging.getLogger(__name__)

# Store user states for multi-step processes
user_states = {}

# Main customize clone menu
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
        [
            InlineKeyboardButton('START TEXT', callback_data=f'set_start_text_{bot_id}'),
            InlineKeyboardButton('START PICTURE', callback_data=f'set_start_pic_{bot_id}')
        ],
        [
            InlineKeyboardButton('START BUTTON', callback_data=f'set_start_btn_{bot_id}'),
            InlineKeyboardButton('FORCE SUBSCRIBE', callback_data=f'set_fsub_{bot_id}')
        ],
        [
            InlineKeyboardButton('MONGO DB', callback_data=f'set_mongo_{bot_id}'),
            InlineKeyboardButton('LOG CHANNEL', callback_data=f'set_log_{bot_id}')
        ],
        [
            InlineKeyboardButton('ADMINS', callback_data=f'set_admins_{bot_id}'),
            InlineKeyboardButton('BOT STATUS', callback_data=f'bot_status_{bot_id}')
        ],
        [
            InlineKeyboardButton('DATABASE CHANNEL', callback_data=f'set_db_channel_{bot_id}'),
            InlineKeyboardButton('RESTART BOT', callback_data=f'restart_{bot_id}')
        ],
        [
            InlineKeyboardButton(f"🔒 PUBLIC USE - {'✅' if settings.get('public_use', True) else '❌'}", 
                               callback_data=f'toggle_public_{bot_id}')
        ],
        [
            InlineKeyboardButton('AUTO DELETE', callback_data=f'auto_delete_menu_{bot_id}')
        ],
        [
            InlineKeyboardButton('DEACTIVATE BOT', callback_data=f'deactivate_{bot_id}'),
            InlineKeyboardButton('DELETE BOT', callback_data=f'delete_{bot_id}')
        ],
        [InlineKeyboardButton('⬅️ BACK', callback_data='clone')]
    ]
    
    settings_text = (
        f"<b>🤖 YOUR CLONE BOT - @{clone['username']}</b>\n\n"
        f"📝 <b>IF YOU WANT TO MODIFY YOUR CLONE BOT THEN DO IT FROM HERE.</b>\n\n"
        f"⚠️ <b>NOTE - IF CLONE BOT NOT USING ALONG ONE WEEK THEN AUTOMATICALLY CLONE BOT DEACTIVATE.</b>\n\n"
        f"⏰ <b>LAST USED -</b> {clone.get('last_used', 'Never')}\n"
    )
    
    await query.message.edit_text(settings_text, reply_markup=InlineKeyboardMarkup(buttons))

# Auto Delete Menu
@Client.on_callback_query(filters.regex("^auto_delete_menu_"))
async def auto_delete_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    
    auto_del_enabled = settings.get('auto_delete', False)
    auto_del_time = settings.get('auto_delete_time', 300)
    
    minutes = auto_del_time // 60
    seconds = auto_del_time % 60
    time_display = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
    
    buttons = [
        [
            InlineKeyboardButton(
                f"{'✅ ENABLE' if not auto_del_enabled else '❌ DISABLE'}", 
                callback_data=f'toggle_autodel_{bot_id}'
            )
        ],
        [
            InlineKeyboardButton('CUSTOM TIME', callback_data=f'custom_del_time_{bot_id}')
        ],
        [InlineKeyboardButton('⬅️ BACK', callback_data=f'customize_{bot_id}')]
    ]
    
    status = "ENABLED ✅" if auto_del_enabled else "DISABLED ❌"
    
    text = (
        f"<b>🗑️ AUTO DELETE SETTINGS</b>\n\n"
        f"<b>Status:</b> {status}\n"
        f"<b>Delete Time:</b> {time_display} ({auto_del_time}s)\n\n"
        f"<i>When enabled, files will be automatically deleted after the specified time.</i>"
    )
    
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# Toggle Auto Delete
@Client.on_callback_query(filters.regex("^toggle_autodel_"))
async def toggle_auto_delete(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('auto_delete', False)
    
    new_status = not current
    await clone_db.update_clone_setting(bot_id, 'auto_delete', new_status)
    
    await query.answer(f"Auto Delete: {'✅ Enabled' if new_status else '❌ Disabled'}", show_alert=True)
    await auto_delete_menu(client, query)

# Custom Delete Time
@Client.on_callback_query(filters.regex("^custom_del_time_"))
async def custom_delete_time(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_states[query.from_user.id] = {'action': 'custom_del_time', 'bot_id': bot_id}
    
    await query.message.edit_text(
        "<b>⏰ ENTER CUSTOM DELETE TIME</b>\n\n"
        "Send time in seconds (minimum 20 seconds)\n"
        "Examples:\n"
        "• <code>60</code> - 1 minute\n"
        "• <code>300</code> - 5 minutes\n"
        "• <code>600</code> - 10 minutes\n\n"
        "Send /cancel to cancel this operation.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('❌ CANCEL', callback_data=f'auto_delete_menu_{bot_id}')
        ]])
    )
    await query.answer()

# Force Subscribe Menu
@Client.on_callback_query(filters.regex("^set_fsub_"))
async def force_sub_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    fsub_channels = settings.get('force_sub_channels', [])
    
    buttons = []
    
    # Display current channels with remove buttons
    if fsub_channels:
        for idx, channel in enumerate(fsub_channels[:6], 1):
            buttons.append([
                InlineKeyboardButton(
                    f"📢 {channel}", 
                    callback_data=f'fsub_info_{bot_id}'
                ),
                InlineKeyboardButton(
                    f"❌ REMOVE", 
                    callback_data=f'remove_fsub_{bot_id}_{idx-1}'
                )
            ])
    else:
        buttons.append([InlineKeyboardButton('No channels added yet', callback_data='none')])
    
    # Add channel button (only if less than 6)
    if len(fsub_channels) < 6:
        buttons.append([InlineKeyboardButton('➕ ADD CHANNEL', callback_data=f'add_fsub_{bot_id}')])
    
    buttons.append([InlineKeyboardButton('⬅️ BACK', callback_data=f'customize_{bot_id}')])
    
    text = (
        f"<b>🔒 FORCE SUBSCRIBE CHANNELS</b>\n\n"
        f"<b>Total Channels:</b> {len(fsub_channels)}/6\n\n"
        f"<i>Users must join these channels to use your bot.</i>"
    )
    
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# Add Force Sub Channel
@Client.on_callback_query(filters.regex("^add_fsub_"))
async def add_force_sub(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    fsub_channels = settings.get('force_sub_channels', [])
    
    if len(fsub_channels) >= 6:
        return await query.answer("Maximum 6 channels allowed!", show_alert=True)
    
    user_states[query.from_user.id] = {'action': 'add_fsub', 'bot_id': bot_id}
    
    await query.message.edit_text(
        "<b>📢 ADD FORCE SUBSCRIBE CHANNEL</b>\n\n"
        "Send channel username or ID:\n\n"
        "Examples:\n"
        "• <code>@your_channel</code>\n"
        "• <code>-1001234567890</code>\n\n"
        "Send /cancel to cancel this operation.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('❌ CANCEL', callback_data=f'set_fsub_{bot_id}')
        ]])
    )
    await query.answer()

# Remove Force Sub Channel
@Client.on_callback_query(filters.regex("^remove_fsub_"))
async def remove_force_sub(client, query: CallbackQuery):
    parts = query.data.split("_")
    bot_id = int(parts[2])
    channel_idx = int(parts[3])
    
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    fsub_channels = settings.get('force_sub_channels', [])
    
    if channel_idx < len(fsub_channels):
        removed_channel = fsub_channels.pop(channel_idx)
        await clone_db.update_clone_setting(bot_id, 'force_sub_channels', fsub_channels)
        await query.answer(f"Removed: {removed_channel}", show_alert=True)
    
    await force_sub_menu(client, query)

# Start Text Setting
@Client.on_callback_query(filters.regex("^set_start_text_"))
async def set_start_text(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_states[query.from_user.id] = {'action': 'start_text', 'bot_id': bot_id}
    
    await query.message.edit_text(
        "<b>📝 SET START TEXT</b>\n\n"
        "Send your custom start message.\n"
        "You can use HTML formatting.\n\n"
        "Send /cancel to cancel this operation.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('❌ CANCEL', callback_data=f'customize_{bot_id}')
        ]])
    )
    await query.answer()

# Start Picture Setting
@Client.on_callback_query(filters.regex("^set_start_pic_"))
async def set_start_picture(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_states[query.from_user.id] = {'action': 'start_pic', 'bot_id': bot_id}
    
    await query.message.edit_text(
        "<b>🖼️ SET START PICTURE</b>\n\n"
        "Send a photo or photo URL.\n"
        "Send /remove to remove current photo.\n\n"
        "Send /cancel to cancel this operation.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('❌ CANCEL', callback_data=f'customize_{bot_id}')
        ]])
    )
    await query.answer()

# Toggle Public Use
@Client.on_callback_query(filters.regex("^toggle_public_"))
async def toggle_public_use(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    current = clone.get('settings', {}).get('public_use', True)
    
    new_status = not current
    await clone_db.update_clone_setting(bot_id, 'public_use', new_status)
    
    await query.answer(
        f"Public Use: {'✅ Enabled' if new_status else '❌ Disabled'}", 
        show_alert=True
    )
    await customize_clone(client, query)

# MongoDB Setting
@Client.on_callback_query(filters.regex("^set_mongo_"))
async def set_mongo_db(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    current_mongo = settings.get('mongo_db')
    
    buttons = []
    
    if current_mongo:
        status_text = f"<b>✅ Custom MongoDB Connected</b>\n\n<code>{current_mongo[:50]}...</code>"
        buttons.append([
            InlineKeyboardButton('🗑️ REMOVE (Use Default)', callback_data=f'remove_mongo_{bot_id}')
        ])
    else:
        status_text = "<b>📊 Using Default MongoDB</b>\n\n<i>Clone is using parent bot's database.</i>"
    
    buttons.append([InlineKeyboardButton('➕ SET CUSTOM MONGODB', callback_data=f'add_mongo_{bot_id}')])
    buttons.append([InlineKeyboardButton('⬅️ BACK', callback_data=f'customize_{bot_id}')])
    
    text = (
        f"<b>🗄️ MONGODB SETTINGS</b>\n\n"
        f"{status_text}\n\n"
        f"<i>Custom MongoDB allows clone to use separate database.</i>"
    )
    
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# Add MongoDB
@Client.on_callback_query(filters.regex("^add_mongo_"))
async def add_mongo_db(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'add_mongo', 'bot_id': bot_id}
    
    await query.message.edit_text(
        "<b>🗄️ SET CUSTOM MONGODB</b>\n\n"
        "Send your MongoDB connection URI:\n\n"
        "Example:\n"
        "<code>mongodb+srv://username:password@cluster.mongodb.net</code>\n\n"
        "Send /cancel to cancel this operation.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('❌ CANCEL', callback_data=f'set_mongo_{bot_id}')
        ]])
    )
    await query.answer()

# Remove MongoDB
@Client.on_callback_query(filters.regex("^remove_mongo_"))
async def remove_mongo_db(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    
    await clone_db.update_clone_setting(bot_id, 'mongo_db', None)
    await query.answer("✅ Switched to default MongoDB!", show_alert=True)
    await set_mongo_db(client, query)

# Log Channel Setting
@Client.on_callback_query(filters.regex("^set_log_"))
async def set_log_channel(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    log_channel = settings.get('log_channel')
    
    buttons = []
    
    if log_channel:
        buttons.append([
            InlineKeyboardButton(f'📢 {log_channel}', callback_data='log_info'),
            InlineKeyboardButton('❌ REMOVE', callback_data=f'remove_log_{bot_id}')
        ])
    else:
        buttons.append([InlineKeyboardButton('No log channel set', callback_data='none')])
    
    buttons.append([InlineKeyboardButton('➕ SET LOG CHANNEL', callback_data=f'add_log_{bot_id}')])
    buttons.append([InlineKeyboardButton('⬅️ BACK', callback_data=f'customize_{bot_id}')])
    
    text = (
        f"<b>📝 LOG CHANNEL</b>\n\n"
        f"<i>All bot activities will be logged here.</i>"
    )
    
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# Add Log Channel
@Client.on_callback_query(filters.regex("^add_log_"))
async def add_log_channel(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'add_log', 'bot_id': bot_id}
    
    await query.message.edit_text(
        "<b>📝 SET LOG CHANNEL</b>\n\n"
        "Send channel username or ID:\n\n"
        "Examples:\n"
        "• <code>@your_log_channel</code>\n"
        "• <code>-1001234567890</code>\n\n"
        "Send /cancel to cancel this operation.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('❌ CANCEL', callback_data=f'set_log_{bot_id}')
        ]])
    )
    await query.answer()

# Remove Log Channel
@Client.on_callback_query(filters.regex("^remove_log_"))
async def remove_log_channel(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    
    await clone_db.update_clone_setting(bot_id, 'log_channel', None)
    await query.answer("✅ Log channel removed!", show_alert=True)
    await set_log_channel(client, query)

# Database Channel Setting
@Client.on_callback_query(filters.regex("^set_db_channel_"))
async def set_database_channel(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    db_channel = settings.get('db_channel')
    
    buttons = []
    
    if db_channel:
        buttons.append([
            InlineKeyboardButton(f'📢 {db_channel}', callback_data='db_info'),
            InlineKeyboardButton('❌ REMOVE', callback_data=f'remove_db_ch_{bot_id}')
        ])
    else:
        buttons.append([InlineKeyboardButton('No database channel set', callback_data='none')])
    
    buttons.append([InlineKeyboardButton('➕ SET DATABASE CHANNEL', callback_data=f'add_db_ch_{bot_id}')])
    buttons.append([InlineKeyboardButton('⬅️ BACK', callback_data=f'customize_{bot_id}')])
    
    text = (
        f"<b>🗄️ DATABASE CHANNEL</b>\n\n"
        f"<i>Files will be stored in this channel.</i>"
    )
    
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# Add Database Channel
@Client.on_callback_query(filters.regex("^add_db_ch_"))
async def add_database_channel(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_states[query.from_user.id] = {'action': 'add_db_channel', 'bot_id': bot_id}
    
    await query.message.edit_text(
        "<b>🗄️ SET DATABASE CHANNEL</b>\n\n"
        "Send channel username or ID:\n\n"
        "Examples:\n"
        "• <code>@your_db_channel</code>\n"
        "• <code>-1001234567890</code>\n\n"
        "Send /cancel to cancel this operation.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('❌ CANCEL', callback_data=f'set_db_channel_{bot_id}')
        ]])
    )
    await query.answer()

# Remove Database Channel
@Client.on_callback_query(filters.regex("^remove_db_ch_"))
async def remove_database_channel(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    
    await clone_db.update_clone_setting(bot_id, 'db_channel', None)
    await query.answer("✅ Database channel removed!", show_alert=True)
    await set_database_channel(client, query)

# Start Button Setting
@Client.on_callback_query(filters.regex("^set_start_btn_"))
async def set_start_button(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_states[query.from_user.id] = {'action': 'start_button', 'bot_id': bot_id}
    
    await query.message.edit_text(
        "<b>🔘 SET START BUTTON</b>\n\n"
        "Send button text and URL in this format:\n\n"
        "<code>Button Text - https://example.com</code>\n\n"
        "Example:\n"
        "<code>Join Channel - https://t.me/yourchannel</code>\n\n"
        "Send /remove to remove button.\n"
        "Send /cancel to cancel this operation.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('❌ CANCEL', callback_data=f'customize_{bot_id}')
        ]])
    )
    await query.answer()

# Restart Bot
@Client.on_callback_query(filters.regex("^restart_"))
async def restart_clone(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    
    # Here you would implement restart logic
    await query.answer("🔄 Clone bot restart initiated!", show_alert=True)
    # Add actual restart code here
    
    await customize_clone(client, query)

# Deactivate Bot
@Client.on_callback_query(filters.regex("^deactivate_"))
async def deactivate_clone(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    
    buttons = [
        [
            InlineKeyboardButton('✅ YES, DEACTIVATE', callback_data=f'confirm_deactivate_{bot_id}'),
            InlineKeyboardButton('❌ NO', callback_data=f'customize_{bot_id}')
        ]
    ]
    
    await query.message.edit_text(
        "⚠️ <b>DEACTIVATE CLONE?</b>\n\n"
        "This will stop your clone bot temporarily.\n"
        "You can reactivate it anytime.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    await query.answer()

@Client.on_callback_query(filters.regex("^confirm_deactivate_"))
async def confirm_deactivate(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    
    await clone_db.deactivate_clone(bot_id)
    await query.answer("✅ Clone deactivated!", show_alert=True)
    await customize_clone(client, query)

# Admins Setting
@Client.on_callback_query(filters.regex("^set_admins_"))
async def set_admins(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    admins = settings.get('admins', [])
    
    buttons = []
    
    if admins:
        for idx, admin_id in enumerate(admins, 1):
            buttons.append([
                InlineKeyboardButton(f"👤 {admin_id}", callback_data='admin_info'),
                InlineKeyboardButton("❌", callback_data=f'remove_admin_{bot_id}_{idx-1}')
            ])
    else:
        buttons.append([InlineKeyboardButton('No admins added yet', callback_data='none')])
    
    buttons.append([InlineKeyboardButton('➕ ADD ADMIN', callback_data=f'add_admin_{bot_id}')])
    buttons.append([InlineKeyboardButton('⬅️ BACK', callback_data=f'customize_{bot_id}')])
    
    text = (
        f"<b>👥 ADMINS MANAGEMENT</b>\n\n"
        f"<b>Total Admins:</b> {len(admins)}\n\n"
        f"<i>Admins can manage files and settings.</i>"
    )
    
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# Add Admin
@Client.on_callback_query(filters.regex("^add_admin_"))
async def add_admin(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'add_admin', 'bot_id': bot_id}
    
    await query.message.edit_text(
        "<b>👤 ADD ADMIN</b>\n\n"
        "Send user ID to add as admin:\n\n"
        "Example: <code>123456789</code>\n\n"
        "Send /cancel to cancel this operation.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('❌ CANCEL', callback_data=f'set_admins_{bot_id}')
        ]])
    )
    await query.answer()

# Remove Admin
@Client.on_callback_query(filters.regex("^remove_admin_"))
async def remove_admin(client, query: CallbackQuery):
    parts = query.data.split("_")
    bot_id = int(parts[2])
    admin_idx = int(parts[3])
    
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    admins = settings.get('admins', [])
    
    if admin_idx < len(admins):
        removed_admin = admins.pop(admin_idx)
        await clone_db.update_clone_setting(bot_id, 'admins', admins)
        await query.answer(f"Removed Admin: {removed_admin}", show_alert=True)
    
    await set_admins(client, query)

# Bot Status
@Client.on_callback_query(filters.regex("^bot_status_"))
async def bot_status(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    users_count = await clone_db.get_clone_users_count(bot_id)
    settings = clone.get('settings', {})
    
    status_text = (
        f"<b>📊 BOT STATUS</b>\n\n"
        f"<b>🤖 Bot:</b> @{clone['username']}\n"
        f"<b>📝 Name:</b> {clone['name']}\n"
        f"<b>👥 Users:</b> {users_count}\n"
        f"<b>📅 Created:</b> {clone.get('created_at', 'N/A')}\n"
        f"<b>⏰ Last Used:</b> {clone.get('last_used', 'Never')}\n\n"
        f"<b>⚙️ SETTINGS:</b>\n"
        f"• Auto Delete: {'✅' if settings.get('auto_delete') else '❌'}\n"
        f"• Public Use: {'✅' if settings.get('public_use', True) else '❌'}\n"
        f"• Force Sub Channels: {len(settings.get('force_sub_channels', []))}\n"
        f"• Admins: {len(settings.get('admins', []))}"
    )
    
    await query.message.edit_text(
        status_text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('⬅️ BACK', callback_data=f'customize_{bot_id}')
        ]])
    )
    await query.answer()

# Delete Clone
@Client.on_callback_query(filters.regex("^delete_(?!clone)"))
async def delete_clone_confirm(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    
    buttons = [
        [
            InlineKeyboardButton('✅ YES, DELETE', callback_data=f'confirm_delete_{bot_id}'),
            InlineKeyboardButton('❌ NO', callback_data=f'customize_{bot_id}')
        ]
    ]
    
    await query.message.edit_text(
        "⚠️ <b>ARE YOU SURE?</b>\n\n"
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
        "✅ <b>CLONE DELETED!</b>\n\n"
        "Your clone bot has been successfully deleted.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('⬅️ BACK', callback_data='clone')
        ]])
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
        buttons = [[InlineKeyboardButton('⬅️ BACK', callback_data=f'customize_{bot_id}')]]
        return await message.reply(
            "❌ Operation cancelled!", 
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    try:
        # Start text
        if action == 'start_text':
            await clone_db.update_clone_setting(bot_id, 'start_message', message.text)
            del user_states[user_id]
            await message.reply(
                "✅ Start text updated successfully!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton('⬅️ BACK', callback_data=f'customize_{bot_id}')
                ]])
            )
        
        # Start picture
        elif action == 'start_pic':
            if message.text == '/remove':
                await clone_db.update_clone_setting(bot_id, 'start_photo', None)
                del user_states[user_id]
                return await message.reply(
                    "✅ Start photo removed!",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton('⬅️ BACK', callback_data=f'customize_{bot_id}')
                    ]])
                )
            
            photo_url = message.text if message.text.startswith('http') else None
            if photo_url:
                await clone_db.update_clone_setting(bot_id, 'start_photo', photo_url)
                del user_states[user_id]
                await message.reply(
                    "✅ Start photo updated!",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton('⬅️ BACK', callback_data=f'customize_{bot_id}')
                    ]])
                )
            else:
                await message.reply("❌ Invalid photo URL! Please send a valid URL.")
        
        # Add Force Sub
        elif action == 'add_fsub':
            clone = await clone_db.get_clone(bot_id)
            settings = clone.get('settings', {})
            fsub_channels = settings.get('force_sub_channels', [])
            
            if len(fsub_channels) >= 6:
                return await message.reply("❌ Maximum 6 channels allowed!")
            
            channel = message.text.strip()
            if channel not in fsub_channels:
                fsub_channels.append(channel)
                await clone_db.update_clone_setting(bot_id, 'force_sub_channels', fsub_channels)
                del user_states[user_id]
                await message.reply(
                    f"✅ Channel added: {channel}",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton('⬅️ BACK', callback_data=f'set_fsub_{bot_id}')
                    ]])
                )
            else:
                await message.reply("❌ Channel already exists!")
        
        # Add Admin
        elif action == 'add_admin':
            try:
                admin_id = int(message.text)
                clone = await clone_db.get_clone(bot_id)
                settings = clone.get('settings', {})
                admins = settings.get('admins', [])
                
                if admin_id not in admins:
                    admins.append(admin_id)
                    await clone_db.update_clone_setting(bot_id, 'admins', admins)
                    del user_states[user_id]
                    await message.reply(
                        f"✅ Admin added: {admin_id}",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton('⬅️ BACK', callback_data=f'set_admins_{bot_id}')
                        ]])
                    )
                else:
                    await message.reply("❌ Admin already exists!")
            except ValueError:
                await message.reply("❌ Invalid user ID! Please send a valid number.")
        
        # Custom Delete Time
        elif action == 'custom_del_time':
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
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton('⬅️ BACK', callback_data=f'auto_delete_menu_{bot_id}')
                    ]])
                )
            except ValueError:
                await message.reply("❌ Invalid number! Please send a valid number of seconds.")
    
    except Exception as e:
        logger.error(f"Error handling input: {e}")
        await message.reply(
            f"❌ Error: {str(e)}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton('⬅️ BACK', callback_data=f'customize_{bot_id}')
            ]])
        )

# Handle photo input
@Client.on_message(filters.private & filters.photo, group=2)
async def handle_photo_input(client, message):
    user_id = message.from_user.id
    
    if user_id not in user_states:
        return
    
    state = user_states[user_id]
    if state['action'] != 'start_pic':
        return
    
    bot_id = state['bot_id']
    photo_id = message.photo.file_id
    
    await clone_db.update_clone_setting(bot_id, 'start_photo', photo_id)
    del user_states[user_id]
    await message.reply(
        "✅ Start photo updated successfully!",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('⬅️ BACK', callback_data=f'customize_{bot_id}')
        ]])
    )

logger.info("✅ Clone customization module loaded")
