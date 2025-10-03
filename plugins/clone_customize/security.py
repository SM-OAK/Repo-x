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
    """Safely edit message with error handling and disabled web page preview."""
    try:
        await query.message.edit_text(
            text, 
            reply_markup=reply_markup, 
            disable_web_page_preview=True
        )
    except MessageNotModified:
        pass
    except Exception as e:
        logger.error(f"Error editing message for user {query.from_user.id}: {e}")
        try:
            await query.answer("An error occurred. Please try again later.", show_alert=True)
        except Exception:
            pass

async def get_channel_info(client: Client, channel_id):
    """Get channel title and invite link with proper error handling."""
    try:
        if isinstance(channel_id, str) and channel_id.lstrip('-').isdigit():
            channel_id = int(channel_id)
        
        chat = await client.get_chat(channel_id)
        
        if chat.username:
            link = f"https://t.me/{chat.username}"
            display_text = f"{chat.title}"
        else:
            try:
                link = await client.export_chat_invite_link(chat.id)
                display_text = f"{chat.title} 🔒"
            except Exception:
                link = None
                display_text = f"{chat.title} 🔒"
        
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

async def verify_clone_bot_admin(clone_bot_token, channel_id, api_id, api_hash):
    """Verify if clone bot is admin in the channel."""
    if not clone_bot_token: return False
    try:
        from pyrogram import Client as TempClient
        temp_bot = TempClient(
            name=f"temp_verify_{channel_id}",
            api_id=api_id,
            api_hash=api_hash,
            bot_token=clone_bot_token,
            in_memory=True
        )
        async with temp_bot:
            bot_member = await temp_bot.get_chat_member(channel_id, "me")
            return bot_member.status in ('administrator', 'creator')
    except Exception as e:
        logger.error(f"Error verifying clone bot admin in {channel_id}: {e}")
        return False

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
    auto_del = settings.get('auto_delete', False)
    protect = settings.get('protect_mode', False)
    verify = settings.get('verification', False)
    
    auto_del_status = "🟢 ON" if auto_del else "🔴 OFF"
    protect_status = "🟢 ON" if protect else "🔴 OFF"
    verify_status = "🟢 ON" if verify else "🔴 OFF"
    
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

# ==================== FORCE SUBSCRIBE SECTION ====================
@Client.on_callback_query(filters.regex("^fsub_manage_"))
async def fsub_manage(client: Client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    if not clone: return await query.answer("Bot not found.", show_alert=True)
        
    channels = clone.get('settings', {}).get('force_sub_channels', [])
    if channels: await query.answer("⏳ Loading channels...", show_alert=False)
    
    buttons = []
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
        buttons.append([
            InlineKeyboardButton('🧪 Test All Channels', callback_data=f'test_fsub_{bot_id}'),
            InlineKeyboardButton('🔄 Verify Setup', callback_data=f'verify_all_fsub_{bot_id}')
        ])
        buttons.append([InlineKeyboardButton('🗑️ Clear All Channels', callback_data=f'clear_all_fsub_{bot_id}')])
    
    buttons.append([InlineKeyboardButton('« Back to Security', callback_data=f'security_{bot_id}')])
    
    text = (
        "📢 <b>Force Subscribe Management</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    if channels:
        text += (
            f"<b>Active Channels:</b> {len(channels)}/6\n\n"
            "Users must join all listed channels to use the bot.\n\n"
            "<b>⚠️ Important:</b>\n"
            "• Your <b>clone bot</b> must be admin in all channels with 'Add Members' permission."
        )
    else:
        text += (
            "<b>No channels configured.</b>\n\n"
            "This feature forces users to join your channels before they can get files. It's a great way to grow your community!\n\n"
            "Click <b>Add New Channel</b> to get started."
        )
    
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^info_fsub_"))
async def show_channel_info(client, query: CallbackQuery):
    parts = query.data.split("_"); idx, bot_id = int(parts[2]), int(parts[3])
    clone = await clone_db.get_clone(bot_id)
    channels = clone.get('settings', {}).get('force_sub_channels', [])
    
    if not (0 <= idx < len(channels)):
        return await query.answer("❌ Channel not found or already removed.", show_alert=True)
    
    channel_id = channels[idx]
    info = await get_channel_info(client, channel_id)
    
    is_admin = await verify_clone_bot_admin(clone.get('bot_token'), info['id'], client.api_id, client.api_hash)
    admin_status = "✅ Clone bot is Admin" if is_admin else "❌ Clone bot is NOT Admin!"
    
    link_text = f"🔗 {info['link']}" if info['link'] else "🔒 Private Channel (No link available)"
    username_text = f"@{info['username']}" if info['username'] else "None"
    
    info_text = (
        f"📢 <b>Channel Details</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>Name:</b> {info['title']}\n"
        f"<b>Username:</b> {username_text}\n"
        f"<b>ID:</b> <code>{info['id']}</code>\n"
        f"<b>Link:</b> {link_text}\n\n"
        f"<b>Status:</b> {admin_status}\n\n"
        f"{'✅ Setup looks correct!' if is_admin else '⚠️ Please make your clone bot an admin in this channel!'}"
    )
    await query.answer(info_text, show_alert=True, cache_time=5)

@Client.on_callback_query(filters.regex("^test_fsub_"))
async def test_force_sub(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    channels = clone.get('settings', {}).get('force_sub_channels', [])
    if not channels: return await query.answer("❌ No channels configured to test.", show_alert=True)
    
    await query.answer("🧪 Checking your membership...", show_alert=False)
    not_joined, errors = [], []
    for channel_id in channels:
        try:
            await client.get_chat_member(channel_id, query.from_user.id)
        except UserNotParticipant:
            info = await get_channel_info(client, channel_id)
            not_joined.append(f"• {info['title']}")
        except Exception:
            info = await get_channel_info(client, channel_id)
            errors.append(f"• {info['title']} (Error)")
    
    if not_joined:
        result = "❌ <b>Test Failed!</b>\nYou haven't joined:\n" + "\n".join(not_joined)
    elif errors:
        result = "⚠️ <b>Test Incomplete.</b>\nCould not check:\n" + "\n".join(errors)
    else:
        result = "✅ <b>Test Passed!</b>\nYou are subscribed to all required channels."
    
    await query.answer(result, show_alert=True)

@Client.on_callback_query(filters.regex("^verify_all_fsub_"))
async def verify_all_fsub(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    clone = await clone_db.get_clone(bot_id)
    channels = clone.get('settings', {}).get('force_sub_channels', [])
    if not channels: return await query.answer("❌ No channels to verify.", show_alert=True)
    
    await query.answer("⏳ Verifying all channels...", show_alert=False)
    not_admin, verified = [], []
    for channel_id in channels:
        info = await get_channel_info(client, channel_id)
        is_admin = await verify_clone_bot_admin(clone.get('bot_token'), channel_id, client.api_id, client.api_hash)
        (verified if is_admin else not_admin).append(f"{'✅' if is_admin else '❌'} {info['title']}")
    
    result = "<b>🔄 Verification Results</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
    if verified: result += "<b>Verified Channels:</b>\n" + "\n".join(verified) + "\n\n"
    if not_admin:
        result += "<b>Issues Found:</b>\n" + "\n".join(not_admin) + "\n\n⚠️ Make your clone bot an admin in the channels listed above!"
    elif not verified:
        result += "No channels to check."
    else:
        result += "✅ All channels verified successfully!"
    
    await query.answer(result, show_alert=True, cache_time=5)

@Client.on_callback_query(filters.regex("^add_fsub_prompt_"))
async def add_fsub_prompt(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_states[query.from_user.id] = {'action': 'add_fsub_channel', 'bot_id': bot_id}
    text = (
        "<b>➕ Add Force Subscribe Channel</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Please send the channel's <b>username</b> (e.g., <code>@channelname</code>) or <b>ID</b> (e.g., <code>-100123456789</code>).\n\n"
        "💡 <b>Tip:</b> To get a private channel's ID, forward a message from it to @userinfobot.\n\n"
        "⚠️ Your <b>clone bot</b> must be an admin in the channel with 'Add Members' permission."
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
    text = (
        "⚠️ <b>Confirm Action</b>\n"
        "Are you sure you want to remove ALL force subscribe channels? This cannot be undone."
    )
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

# ==================== AUTO DELETE SECTION ====================
@Client.on_callback_query(filters.regex("^auto_delete_"))
async def auto_delete_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    if not clone: return await query.answer("Bot not found!", show_alert=True)
    
    settings = clone.get('settings', {})
    enabled = settings.get('auto_delete', False)
    minutes = settings.get('auto_delete_time', 300) // 60
    
    status_emoji = "🟢" if enabled else "🔴"; status_text = "ENABLED" if enabled else "DISABLED"
    
    buttons = [
        [InlineKeyboardButton(f"{status_emoji} Status: {status_text}", callback_data=f'toggle_autodel_{bot_id}')],
        [InlineKeyboardButton(f'⏱️ Set Time ({minutes} min)', callback_data=f'set_autodel_time_{bot_id}')],
        [InlineKeyboardButton('« Back to Security', callback_data=f'security_{bot_id}')]
    ]
    text = (
        "🗑️ <b>Auto Delete Settings</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>Status:</b> {status_text}\n"
        f"<b>Delete After:</b> {minutes} minute(s)\n\n"
        "This feature automatically deletes files sent by your bot after a set time. This helps protect your content."
    )
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^toggle_autodel_"))
async def toggle_autodel(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    new_status = not clone.get('settings', {}).get('auto_delete', False)
    await clone_db.update_clone_setting(bot_id, 'auto_delete', new_status)
    await query.answer(f"Auto Delete is now {'ENABLED' if new_status else 'DISABLED'}.", show_alert=True)
    query.data = f"auto_delete_{bot_id}"
    await auto_delete_menu(client, query)

@Client.on_callback_query(filters.regex("^set_autodel_time_"))
async def set_autodel_time_prompt(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_states[query.from_user.id] = {'action': 'autodel_time', 'bot_id': bot_id}
    text = (
        "⏱️ <b>Set Auto-Delete Time</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Please send the time in <b>minutes</b>.\n\n"
        "• Minimum: <code>1</code>\n"
        "• Maximum: <code>100</code>"
    )
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(
        [[InlineKeyboardButton('❌ Cancel', callback_data=f'auto_delete_{bot_id}')]]
    ))

# ==================== PROTECT CONTENT SECTION ====================
@Client.on_callback_query(filters.regex("^protect_mode_"))
async def protect_mode_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    enabled = clone.get('settings', {}).get('protect_mode', False)
    status_emoji = "🟢" if enabled else "🔴"; status_text = "ENABLED" if enabled else "DISABLED"
    
    buttons = [
        [InlineKeyboardButton(f"{status_emoji} Status: {status_text}", callback_data=f'toggle_protect_{bot_id}')],
        [InlineKeyboardButton('« Back to Security', callback_data=f'security_{bot_id}')]
    ]
    text = (
        "🛡️ <b>Protect Content Settings</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>Status:</b> {status_text}\n\n"
        "When enabled, this prevents users from forwarding, saving, or taking screenshots of content sent by your bot.\n\n"
        "<b>Note:</b> This uses Telegram's built-in protection and may not work on all devices."
    )
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^toggle_protect_"))
async def toggle_protect(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    new_status = not clone.get('settings', {}).get('protect_mode', False)
    await clone_db.update_clone_setting(bot_id, 'protect_mode', new_status)
    await query.answer(f"Protect Content is now {'ENABLED' if new_status else 'DISABLED'}.", show_alert=True)
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
    tutorial_status = "✅ Set" if settings.get('tutorial_link') else "❌ Not Set"
    
    all_configured = settings.get('shortlink_api') and settings.get('shortlink_url')
    
    buttons = [
        [InlineKeyboardButton(f"{status_emoji} Status: {status_text}", callback_data=f'toggle_verify_{bot_id}')],
        [InlineKeyboardButton(f'🔑 API Key • {api_status}', callback_data=f'set_api_{bot_id}')],
        [InlineKeyboardButton(f'🔗 Shortlink URL • {url_status}', callback_data=f'set_url_{bot_id}')],
        [InlineKeyboardButton(f'📖 Tutorial Link • {tutorial_status}', callback_data=f'set_tutorial_{bot_id}')],
        [InlineKeyboardButton('« Back to Security', callback_data=f'security_{bot_id}')]
    ]
    
    warning = "\n\n⚠️ <b>Warning:</b> Enable this only after setting your API Key and URL." if not all_configured else ""
    text = (
        "🔐 <b>Shortlink Verification</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Force users to solve a shortlink to access the bot. This can be used to monetize your service.\n\n"
        "<b>Required:</b>\n"
        "• <code>API Key</code>: Your shortener service API key.\n"
        "• <code>Shortlink URL</code>: The base URL of your shortener."
        f"{warning}"
    )
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^toggle_verify_"))
async def toggle_verification(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    new_status = not settings.get('verification', False)
    
    if new_status and not (settings.get('shortlink_api') and settings.get('shortlink_url')):
        return await query.answer("❌ Cannot enable! Set API Key and Shortlink URL first.", show_alert=True)
        
    await clone_db.update_clone_setting(bot_id, 'verification', new_status)
    await query.answer(f"Verification is now {'ENABLED' if new_status else 'DISABLED'}.", show_alert=True)
    query.data = f"verification_{bot_id}"
    await verification_menu(client, query)

@Client.on_callback_query(filters.regex("^set_api_"))
async def set_shortlink_api_prompt(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'set_shortlink_api', 'bot_id': bot_id}
    text = "🔑 <b>Set Shortlink API Key</b>\n\nPlease send your shortlink provider's API key."
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(
        [[InlineKeyboardButton('❌ Cancel', callback_data=f'verification_{bot_id}')]]
    ))

@Client.on_callback_query(filters.regex("^set_url_"))
async def set_shortlink_url_prompt(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'set_shortlink_url', 'bot_id': bot_id}
    text = (
        "🔗 <b>Set Shortlink URL</b>\n\n"
        "Please send the base URL of your shortlink provider (e.g., <code>droplink.co</code>).\n\n"
        "Do not include <code>https://</code>."
    )
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(
        [[InlineKeyboardButton('❌ Cancel', callback_data=f'verification_{bot_id}')]]
    ))

@Client.on_callback_query(filters.regex("^set_tutorial_"))
async def set_tutorial_link_prompt(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'set_tutorial_link', 'bot_id': bot_id}
    text = (
        "📖 <b>Set Tutorial Link</b>\n\n"
        "You can provide a link to a tutorial on how to solve the shortlink.\n\n"
        "➡️ <b>To add/update:</b> Send the full URL.\n"
        "➡️ <b>To remove:</b> Send /clear"
    )
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(
        [[InlineKeyboardButton('❌ Cancel', callback_data=f'verification_{bot_id}')]]
    ))

