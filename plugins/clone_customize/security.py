import logging
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import MessageNotModified, PeerIdInvalid, ChannelInvalid, UserNotParticipant
from database.clone_db import clone_db
from .input_handler import user_states

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== HELPER FUNCTIONS ====================
async def safe_edit_message(query: CallbackQuery, text: str, reply_markup=None):
    """Safely edit message with error handling."""
    try:
        await query.message.edit_text(
            text, 
            reply_markup=reply_markup, 
            disable_web_page_preview=True
        )
    except MessageNotModified:
        pass
    except Exception as e:
        logger.error(f"Error editing message: {e}")

async def get_channel_info(client: Client, channel_id):
    """Get channel title and link."""
    try:
        if isinstance(channel_id, str) and channel_id.lstrip('-').isdigit():
            channel_id = int(channel_id)
        
        chat = await client.get_chat(channel_id)
        
        link = f"https://t.me/{chat.username}" if chat.username else None
        display_text = f"{chat.title}" if link else f"{chat.title} 🔒"
        
        return {
            'title': chat.title,
            'link': link,
            'display': display_text,
            'id': chat.id,
            'username': chat.username
        }
    except (PeerIdInvalid, ChannelInvalid, ValueError):
        return {'title': 'Invalid Channel', 'link': None, 'display': '⚠️ Invalid/Deleted', 'id': channel_id, 'username': None}
    except Exception as e:
        logger.error(f"Error fetching channel {channel_id}: {e}")
        return {'title': 'Error', 'link': None, 'display': '❓ Error Loading', 'id': channel_id, 'username': None}

# ==================== MAIN SECURITY MENU ====================
@Client.on_callback_query(filters.regex("^security_"))
async def security_menu(client, query: CallbackQuery):
    try:
        bot_id = int(query.data.split("_")[1])
    except (IndexError, ValueError):
        return await query.answer("Invalid request.", show_alert=True)
    
    clone = await clone_db.get_clone(bot_id)
    if not clone:
        return await query.answer("This bot is no longer available.", show_alert=True)
        
    settings = clone.get('settings', {})
    fsub_count = len(settings.get('force_sub_channels', []))
    auto_del_status = "🟢 ON" if settings.get('auto_delete', False) else "🔴 OFF"
    protect_status = "🟢 ON" if settings.get('protect_mode', False) else "🔴 OFF"
    verify_status = "🟢 ON" if settings.get('verification', False) else "🔴 OFF"
    
    buttons = [
        [InlineKeyboardButton(f'📢 Force Subscribe ({fsub_count}/6)', callback_data=f'fsub_manage_{bot_id}')],
        [InlineKeyboardButton(f'🗑️ Auto Delete • {auto_del_status}', callback_data=f'auto_delete_{bot_id}')],
        [InlineKeyboardButton(f'🛡️ Protect Content • {protect_status}', callback_data=f'protect_mode_{bot_id}')],
        [InlineKeyboardButton(f'🔐 Verification • {verify_status}', callback_data=f'verification_{bot_id}')],
        [InlineKeyboardButton('« Back to Customize', callback_data=f'customize_{bot_id}')]
    ]
    
    text = (
        "🔒 <b>Security & Access Control</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📢 <b>Force Subscribe:</b> {fsub_count}/6 channels\n"
        "   └ Users must join channels to access bot\n\n"
        f"🗑️ <b>Auto Delete:</b> {auto_del_status}\n"
        "   └ Automatically delete sent files\n\n"
        f"🛡️ <b>Protect Content:</b> {protect_status}\n"
        "   └ Prevent forwarding & screenshots\n\n"
        f"🔐 <b>Verification:</b> {verify_status}\n"
        "   └ Shortlink verification system"
    )
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

# ==================== FORCE SUBSCRIBE SECTION (SIMPLE) ====================
@Client.on_callback_query(filters.regex("^fsub_manage_"))
async def fsub_manage(client: Client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    if not clone: return await query.answer("Bot not found.", show_alert=True)
        
    channels = clone.get('settings', {}).get('force_sub_channels', [])
    
    buttons = []
    if channels:
        await query.answer("⏳ Loading channels...", show_alert=False)
        for idx, channel_id in enumerate(channels):
            info = await get_channel_info(client, channel_id)
            buttons.append([
                InlineKeyboardButton(f"{idx + 1}. {info['display'][:30]}", callback_data=f'info_fsub_{idx}_{bot_id}'),
                InlineKeyboardButton('🗑️', callback_data=f'remove_fsub_{bot_id}_{idx}')
            ])
    
    if len(channels) < 6:
        buttons.append([InlineKeyboardButton('➕ Add New Channel', callback_data=f'add_fsub_prompt_{bot_id}')])
    else:
        buttons.append([InlineKeyboardButton('⚠️ Maximum Channels Reached (6/6)', callback_data='noop')])
    
    if channels:
        buttons.append([InlineKeyboardButton('🗑️ Clear All Channels', callback_data=f'clear_all_fsub_{bot_id}')])
    
    buttons.append([InlineKeyboardButton('« Back to Security', callback_data=f'security_{bot_id}')])
    
    text = "📢 <b>Force Subscribe Management</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
    if channels:
        text += (
            f"<b>Active Channels:</b> {len(channels)}/6\n\n"
            "<b>⚠️ Important:</b>\nFor this to work, your clone bot MUST be an admin in all listed channels with the 'Add Members' permission."
        )
    else:
        text += (
            "<b>No channels configured.</b>\n\n"
            "This feature forces users to join your channels before they can get files.\n\n"
            "Click <b>Add New Channel</b> to get started."
        )
    
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^info_fsub_"))
async def show_channel_info(client, query: CallbackQuery):
    parts = query.data.split("_"); idx, bot_id = int(parts[2]), int(parts[3])
    clone = await clone_db.get_clone(bot_id)
    channels = clone.get('settings', {}).get('force_sub_channels', [])
    
    if not (0 <= idx < len(channels)):
        return await query.answer("❌ Channel not found.", show_alert=True)
    
    info = await get_channel_info(client, channels[idx])
    
    username_text = f"@{info['username']}" if info['username'] else "None"
    
    info_text = (
        f"📢 <b>Channel Details</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>Name:</b> {info['title']}\n"
        f"<b>Username:</b> {username_text}\n"
        f"<b>ID:</b> <code>{info['id']}</code>\n"
    )
    await query.answer(info_text, show_alert=True, cache_time=10)

@Client.on_callback_query(filters.regex("^add_fsub_prompt_"))
async def add_fsub_prompt(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_states[query.from_user.id] = {'action': 'add_fsub_channel', 'bot_id': bot_id}
    text = (
        "<b>➕ Add Force Subscribe Channel</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Please send the channel's <b>username</b> (e.g., <code>@channelname</code>) or <b>ID</b> (e.g., <code>-100123456789</code>).\n\n"
        "💡 To get a private channel's ID, forward a message from it to @userinfobot."
    )
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(
        [[InlineKeyboardButton('❌ Cancel', callback_data=f'fsub_manage_{bot_id}')]]
    ))

@Client.on_callback_query(filters.regex("^remove_fsub_"))
async def remove_fsub(client, query: CallbackQuery):
    parts = query.data.split("_"); bot_id, idx_to_remove = int(parts[2]), int(parts[3])
    clone = await clone_db.get_clone(bot_id)
    channels = clone.get('settings', {}).get('force_sub_channels', [])
    
    if 0 <= idx_to_remove < len(channels):
        channels.pop(idx_to_remove)
        await clone_db.update_clone_setting(bot_id, 'force_sub_channels', channels)
        await query.answer("✅ Channel removed.", show_alert=False)
    else:
        await query.answer("❌ Channel already removed.", show_alert=True)

    query.data = f"fsub_manage_{bot_id}"
    await fsub_manage(client, query)

@Client.on_callback_query(filters.regex("^clear_all_fsub_"))
async def clear_all_fsub(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    text = "⚠️ Are you sure you want to remove ALL force subscribe channels? This cannot be undone."
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton('✅ Yes, Clear All', callback_data=f'confirm_clear_fsub_{bot_id}')],
        [InlineKeyboardButton('❌ No, Cancel', callback_data=f'fsub_manage_{bot_id}')]
    ]))

@Client.on_callback_query(filters.regex("^confirm_clear_fsub_"))
async def confirm_clear_fsub(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    await clone_db.update_clone_setting(bot_id, 'force_sub_channels', [])
    await query.answer("✅ All channels have been cleared!", show_alert=True)
    query.data = f"fsub_manage_{bot_id}"
    await fsub_manage(client, query)

# ==================== AUTO DELETE, PROTECT, VERIFICATION SECTIONS (UNCHANGED) ====================

# (The rest of the code for Auto Delete, Protect Content, and Verification remains here...)
# (I am omitting it for brevity, but you should keep it in your file if you need those features)
# ==================== AUTO DELETE SECTION ====================
@Client.on_callback_query(filters.regex("^auto_delete_"))
async def auto_delete_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    if not clone:
        return await query.answer("Bot not found!", show_alert=True)
    
    settings = clone.get('settings', {})
    enabled = settings.get('auto_delete', False)
    minutes = settings.get('auto_delete_time', 300) // 60
    
    status_emoji = "🟢" if enabled else "🔴"
    status_text = "ENABLED" if enabled else "DISABLED"
    
    buttons = [
        [InlineKeyboardButton(
            f"{status_emoji} Status: {status_text}",
            callback_data=f'toggle_autodel_{bot_id}'
        )],
        [InlineKeyboardButton(
            f'⏱️ Set Time ({minutes} minutes)',
            callback_data=f'set_autodel_time_{bot_id}'
        )],
        [InlineKeyboardButton('« Back to Security', callback_data=f'security_{bot_id}')]
    ]
    
    text = (
        "🗑️ <b>Auto Delete Settings</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>Status:</b> {status_emoji} {status_text}\n"
        f"<b>Delete After:</b> {minutes} minute(s)\n\n"
        "<b>ℹ️ What is Auto Delete?</b>\n"
        "Automatically delete files sent by your bot after a set time period. "
        "This helps protect content and save storage space.\n\n"
        f"<b>Current Setting:</b> Files will be deleted after <b>{minutes} minutes</b>"
    )
    
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^toggle_autodel_"))
async def toggle_autodel(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    new_status = not clone.get('settings', {}).get('auto_delete', False)
    await clone_db.update_clone_setting(bot_id, 'auto_delete', new_status)
    
    status_text = "ENABLED ✅" if new_status else "DISABLED ❌"
    await query.answer(f"Auto Delete is now {status_text}", show_alert=True)
    
    query.data = f"auto_delete_{bot_id}"
    await auto_delete_menu(client, query)

@Client.on_callback_query(filters.regex("^set_autodel_time_"))
async def set_autodel_time_prompt(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_states[query.from_user.id] = {'action': 'autodel_time', 'bot_id': bot_id}
    
    text = (
        "⏱️ <b>Set Auto-Delete Time</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Please send the time in <b>minutes</b> after which files should be deleted.\n\n"
        "• Minimum: <code>1</code>\n"
        "• Maximum: <code>100</code>"
    )
    buttons = [[InlineKeyboardButton('❌ Cancel', callback_data=f'auto_delete_{bot_id}')]]
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

# ==================== PROTECT CONTENT SECTION ====================
@Client.on_callback_query(filters.regex("^protect_mode_"))
async def protect_mode_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    enabled = clone.get('settings', {}).get('protect_mode', False)
    
    status_emoji = "🟢" if enabled else "🔴"
    status_text = "ENABLED" if enabled else "DISABLED"
    
    buttons = [
        [InlineKeyboardButton(
            f"{status_emoji} Status: {status_text}",
            callback_data=f'toggle_protect_{bot_id}'
        )],
        [InlineKeyboardButton('« Back to Security', callback_data=f'security_{bot_id}')]
    ]
    
    text = (
        "🛡️ <b>Protect Content Settings</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>Status:</b> {status_emoji} {status_text}\n\n"
        "Prevents users from forwarding, saving, or taking screenshots of content sent by your bot."
    )
    
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^toggle_protect_"))
async def toggle_protect(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    new_status = not clone.get('settings', {}).get('protect_mode', False)
    await clone_db.update_clone_setting(bot_id, 'protect_mode', new_status)
    
    status_text = "ENABLED ✅" if new_status else "DISABLED ❌"
    await query.answer(f"Protect Content is now {status_text}", show_alert=True)
    
    query.data = f"protect_mode_{bot_id}"
    await protect_mode_menu(client, query)
    
# ==================== VERIFICATION SECTION ====================
@Client.on_callback_query(filters.regex("^verification_"))
async def verification_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    
    enabled = settings.get('verification', False)
    status_emoji = "🟢" if enabled else "🔴"; status_text = "ENABLED" if enabled else "DISABLED"
    
    api_status = "✅ Set" if settings.get('shortlink_api') else "❌ Not Set"
    url_status = "✅ Set" if settings.get('shortlink_url') else "❌ Not Set"
    
    buttons = [
        [InlineKeyboardButton(f"{status_emoji} Status: {status_text}", callback_data=f'toggle_verify_{bot_id}')],
        [InlineKeyboardButton(f'🔑 API Key • {api_status}', callback_data=f'set_api_{bot_id}')],
        [InlineKeyboardButton(f'🔗 Shortlink URL • {url_status}', callback_data=f'set_url_{bot_id}')],
        [InlineKeyboardButton('« Back to Security', callback_data=f'security_{bot_id}')]
    ]
    
    text = (
        "🔐 <b>Shortlink Verification</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Force users to solve a shortlink to access the bot.\n\n"
        "<b>Required:</b>\n"
        "• <code>API Key</code>: Your shortener service API key.\n"
        "• <code>Shortlink URL</code>: The base URL of your shortener."
    )
    
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))
