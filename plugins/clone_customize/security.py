# plugins/clone_customize/security.py
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
        # Convert to int if it's a numeric string
        if isinstance(channel_id, str) and channel_id.lstrip('-').isdigit():
            channel_id = int(channel_id)
        
        chat = await client.get_chat(channel_id)
        
        # Create display text and link
        if chat.username:
            link = f"https://t.me/{chat.username}"
            display_text = f"{chat.title}"
        else:
            # Handle private channels
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
        return {
            'title': '⚠️ Invalid Channel',
            'link': None,
            'display': '⚠️ Invalid/Deleted',
            'id': channel_id,
            'username': None
        }
    except Exception as e:
        logger.error(f"Error fetching channel {channel_id}: {e}")
        return {
            'title': '❓ Error',
            'link': None,
            'display': '❓ Error Loading',
            'id': channel_id,
            'username': None
        }

async def verify_clone_bot_admin(clone_bot_token, channel_id, api_id, api_hash):
    """Verify if clone bot is admin in the channel."""
    try:
        from pyrogram import Client as TempClient
        temp_bot = TempClient(
            f"temp_verify_{channel_id}",
            api_id=api_id,
            api_hash=api_hash,
            bot_token=clone_bot_token,
            in_memory=True
        )
        
        await temp_bot.start()
        bot_member = await temp_bot.get_chat_member(channel_id, temp_bot.me.id)
        is_admin = bot_member.status in ['administrator', 'creator']
        await temp_bot.stop()
        
        return is_admin
    except Exception as e:
        logger.error(f"Error verifying clone bot admin: {e}")
        return False

# ==================== MAIN SECURITY MENU ====================
@Client.on_callback_query(filters.regex("^security_"))
async def security_menu(client, query: CallbackQuery):
    try:
        bot_id = int(query.data.split("_")[1])
    except (IndexError, ValueError):
        return await query.answer("Invalid request. Please start over.", show_alert=True)
    
    clone = await clone_db.get_clone(bot_id)
    if not clone:
        return await query.answer("This bot is no longer available.", show_alert=True)
        
    settings = clone.get('settings', {})
    fsub_count = len(settings.get('force_sub_channels', []))
    auto_del = settings.get('auto_delete', False)
    protect = settings.get('protect_mode', False)
    verify = settings.get('verification', False)
    
    # Status emojis
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
        f"   └ Users must join channels to access bot\n\n"
        f"🗑️ <b>Auto Delete:</b> {auto_del_status}\n"
        f"   └ Automatically delete sent files\n\n"
        f"🛡️ <b>Protect Content:</b> {protect_status}\n"
        f"   └ Prevent forwarding & screenshots\n\n"
        f"🔐 <b>Verification:</b> {verify_status}\n"
        f"   └ Shortlink verification system"
    )
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

# ==================== FORCE SUBSCRIBE SECTION ====================
@Client.on_callback_query(filters.regex("^fsub_manage_"))
async def fsub_manage(client: Client, query: CallbackQuery):
    try:
        bot_id = int(query.data.split("_")[2])
    except (IndexError, ValueError):
        return await query.answer("Invalid request.", show_alert=True)

    clone = await clone_db.get_clone(bot_id)
    if not clone:
        return await query.answer("Bot not found.", show_alert=True)
        
    channels = clone.get('settings', {}).get('force_sub_channels', [])
    
    # Show loading if there are channels
    if channels:
        await query.answer("⏳ Loading channels...", show_alert=False)
    
    buttons = []
    
    # List all channels with better formatting
    if channels:
        for idx, channel_id in enumerate(channels):
            info = await get_channel_info(client, channel_id)
            # Show channel number and title
            buttons.append([
                InlineKeyboardButton(
                    f"{idx + 1}. {info['display'][:30]}",
                    callback_data=f'info_fsub_{idx}_{bot_id}'
                ),
                InlineKeyboardButton('🗑️', callback_data=f'remove_fsub_{bot_id}_{idx}')
            ])
    
    # Add/Max channels button
    if len(channels) < 6:
        buttons.append([
            InlineKeyboardButton('➕ Add New Channel', callback_data=f'add_fsub_prompt_{bot_id}')
        ])
    else:
        buttons.append([
            InlineKeyboardButton('⚠️ Maximum Channels Reached (6/6)', callback_data='noop')
        ])
    
    # Test and manage buttons
    if channels:
        buttons.append([
            InlineKeyboardButton('🧪 Test All Channels', callback_data=f'test_fsub_{bot_id}'),
            InlineKeyboardButton('🔄 Verify Setup', callback_data=f'verify_all_fsub_{bot_id}')
        ])
        buttons.append([
            InlineKeyboardButton('🗑️ Clear All Channels', callback_data=f'clear_all_fsub_{bot_id}')
        ])
    
    buttons.append([InlineKeyboardButton('« Back to Security', callback_data=f'security_{bot_id}')])
    
    if channels:
        text = (
            "📢 <b>Force Subscribe Management</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>Active Channels:</b> {len(channels)}/6\n\n"
            "<b>ℹ️ What is Force Subscribe?</b>\n"
            "Users must join all listed channels before they can access your bot's content.\n\n"
            "<b>⚠️ Important:</b>\n"
            "• Your <b>clone bot</b> must be admin in all channels\n"
            "• Bot needs 'Add Members' permission\n"
            "• Click on channel to view details\n"
            "• Click 🗑️ to remove a channel"
        )
    else:
        text = (
            "📢 <b>Force Subscribe Management</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "<b>No channels configured</b>\n\n"
            "<b>ℹ️ What is Force Subscribe?</b>\n"
            "Force users to join your channels before accessing the bot. This helps grow your community!\n\n"
            "<b>How it works:</b>\n"
            "1. Add up to 6 channels\n"
            "2. Users must join all channels\n"
            "3. Bot verifies membership automatically\n\n"
            "<b>Requirements:</b>\n"
            "• Your clone bot must be admin\n"
            "• Bot needs 'Add Members' permission\n\n"
            "Click <b>Add New Channel</b> to get started!"
        )
    
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^info_fsub_"))
async def show_channel_info(client, query: CallbackQuery):
    try:
        parts = query.data.split("_")
        idx, bot_id = int(parts[2]), int(parts[3])
    except (IndexError, ValueError):
        return await query.answer("Invalid request.", show_alert=True)
    
    clone = await clone_db.get_clone(bot_id)
    channels = clone.get('settings', {}).get('force_sub_channels', [])
    
    if not (0 <= idx < len(channels)):
        return await query.answer("❌ Channel not found or removed.", show_alert=True)
    
    channel_id = channels[idx]
    info = await get_channel_info(client, channel_id)
    
    # Check clone bot admin status
    clone_bot_token = clone.get('bot_token')
    is_admin = False
    
    if clone_bot_token:
        is_admin = await verify_clone_bot_admin(
            clone_bot_token,
            info['id'],
            client.api_id,
            client.api_hash
        )
    
    admin_status = "✅ Clone bot is Admin" if is_admin else "❌ Clone bot is NOT Admin!"
    
    link_text = f"🔗 {info['link']}" if info['link'] else "🔒 Private Channel"
    username_text = f"@{info['username']}" if info['username'] else "No username"
    
    info_text = (
        f"📢 <b>Channel Details</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"<b>Name:</b> {info['title']}\n"
        f"<b>Username:</b> {username_text}\n"
        f"<b>ID:</b> <code>{info['id']}</code>\n"
        f"<b>Link:</b> {link_text}\n\n"
        f"<b>Status:</b> {admin_status}\n\n"
        f"{'✅ Everything looks good!' if is_admin else '⚠️ Please make your clone bot admin in this channel!'}"
    )
    await query.answer(info_text, show_alert=True)

@Client.on_callback_query(filters.regex("^test_fsub_"))
async def test_force_sub(client, query: CallbackQuery):
    """Test if user has joined all force sub channels."""
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    channels = clone.get('settings', {}).get('force_sub_channels', [])
    
    if not channels:
        return await query.answer("❌ No channels configured to test.", show_alert=True)
    
    not_joined = []
    errors = []
    
    for channel_id in channels:
        try:
            await client.get_chat_member(channel_id, query.from_user.id)
        except UserNotParticipant:
            info = await get_channel_info(client, channel_id)
            not_joined.append(f"• {info['title']}")
        except Exception as e:
            logger.error(f"Error checking membership for {channel_id}: {e}")
            info = await get_channel_info(client, channel_id)
            errors.append(f"• {info['title']} (Error checking)")
    
    if not_joined:
        result = (
            "❌ <b>Test Failed!</b>\n\n"
            "<b>You haven't joined:</b>\n" + 
            "\n".join(not_joined)
        )
    elif errors:
        result = (
            "⚠️ <b>Test Partial</b>\n\n"
            "<b>Errors occurred:</b>\n" + 
            "\n".join(errors)
        )
    else:
        result = "✅ <b>Test Passed!</b>\n\nYou are subscribed to all required channels."
    
    await query.answer(result, show_alert=True)

@Client.on_callback_query(filters.regex("^verify_all_fsub_"))
async def verify_all_fsub(client, query: CallbackQuery):
    """Verify clone bot is admin in all channels."""
    bot_id = int(query.data.split("_")[3])
    clone = await clone_db.get_clone(bot_id)
    channels = clone.get('settings', {}).get('force_sub_channels', [])
    clone_bot_token = clone.get('bot_token')
    
    if not channels:
        return await query.answer("❌ No channels to verify.", show_alert=True)
    
    if not clone_bot_token:
        return await query.answer("❌ Clone bot token not found!", show_alert=True)
    
    await query.answer("⏳ Verifying all channels...", show_alert=False)
    
    not_admin = []
    verified = []
    
    for channel_id in channels:
        info = await get_channel_info(client, channel_id)
        is_admin = await verify_clone_bot_admin(
            clone_bot_token,
            channel_id,
            client.api_id,
            client.api_hash
        )
        
        if is_admin:
            verified.append(f"✅ {info['title']}")
        else:
            not_admin.append(f"❌ {info['title']}")
    
    result = "<b>🔄 Verification Results</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
    
    if verified:
        result += "<b>Verified Channels:</b>\n" + "\n".join(verified) + "\n\n"
    
    if not_admin:
        result += "<b>Issues Found:</b>\n" + "\n".join(not_admin) + "\n\n"
        result += "⚠️ Make your clone bot admin in the channels above!"
    else:
        result += "✅ All channels verified successfully!"
    
    await query.answer(result, show_alert=True)

@Client.on_callback_query(filters.regex("^add_fsub_prompt_"))
async def add_fsub_prompt(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_states[query.from_user.id] = {'action': 'add_fsub_channel', 'bot_id': bot_id}
    
    text = (
        "<b>➕ Add Force Subscribe Channel</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Send the channel information:</b>\n\n"
        "<b>Option 1:</b> Channel Username\n"
        "Example: <code>@channelname</code>\n\n"
        "<b>Option 2:</b> Channel ID\n"
        "Example: <code>-100123456789</code>\n\n"
        "💡 <b>How to get Channel ID:</b>\n"
        "1. Forward a message from the channel to @userinfobot\n"
        "2. Copy the channel ID it gives you\n"
        "3. Send it here\n\n"
        "⚠️ <b>Requirements:</b>\n"
        "• Your <b>clone bot</b> must be admin in the channel\n"
        "• Bot needs <b>'Add Members'</b> permission\n\n"
        "Send /cancel to cancel."
    )
    buttons = [[InlineKeyboardButton('❌ Cancel', callback_data=f'fsub_manage_{bot_id}')]]
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^remove_fsub_"))
async def remove_fsub(client, query: CallbackQuery):
    parts = query.data.split("_")
    bot_id, idx_to_remove = int(parts[2]), int(parts[3])
    clone = await clone_db.get_clone(bot_id)
    channels = clone.get('settings', {}).get('force_sub_channels', [])
    
    if 0 <= idx_to_remove < len(channels):
        removed_channel_id = channels.pop(idx_to_remove)
        await clone_db.update_clone_setting(bot_id, 'force_sub_channels', channels)
        info = await get_channel_info(client, removed_channel_id)
        await query.answer(f"✅ Removed: {info['title']}", show_alert=False)
    else:
        await query.answer("❌ Channel already removed.", show_alert=True)

    query.data = f"fsub_manage_{bot_id}"
    await fsub_manage(client, query)

@Client.on_callback_query(filters.regex("^clear_all_fsub_"))
async def clear_all_fsub(client, query: CallbackQuery):
    """Clear all force subscribe channels with confirmation."""
    bot_id = int(query.data.split("_")[3])
    
    buttons = [
        [
            InlineKeyboardButton('✅ Yes, Clear All', callback_data=f'confirm_clear_fsub_{bot_id}'),
            InlineKeyboardButton('❌ No, Cancel', callback_data=f'fsub_manage_{bot_id}')
        ]
    ]
    
    text = (
        "⚠️ <b>Confirm Clear All Channels</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Are you sure you want to remove <b>ALL</b> force subscribe channels?\n\n"
        "This action cannot be undone!"
    )
    
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^confirm_clear_fsub_"))
async def confirm_clear_fsub(client, query: CallbackQuery):
    """Confirm and clear all channels."""
    bot_id = int(query.data.split("_")[3])
    clone = await clone_db.get_clone(bot_id)
    channels_count = len(clone.get('settings', {}).get('force_sub_channels', []))
    
    await clone_db.update_clone_setting(bot_id, 'force_sub_channels', [])
    await query.answer(f"✅ Cleared {channels_count} channel(s)!", show_alert=True)
    
    query.data = f"fsub_manage_{bot_id}"
    await fsub_manage(client, query)

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
        "<b>How it works:</b>\n"
        "• Bot sends file to user\n"
        "• After set time, file is deleted\n"
        "• User receives notification\n\n"
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
        "<b>Limits:</b>\n"
        "• Minimum: <code>1</code> minute\n"
        "• Maximum: <code>100</code> minutes\n\n"
        "<b>Examples:</b>\n"
        "• <code>5</code> - Delete after 5 minutes\n"
        "• <code>30</code> - Delete after 30 minutes\n"
        "• <code>60</code> - Delete after 1 hour\n\n"
        "Send /cancel to cancel."
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
        "<b>ℹ️ What is Protect Content?</b>\n"
        "Prevents users from forwarding, saving, or taking screenshots of content sent by your bot.\n\n"
        "<b>Protection includes:</b>\n"
        "• ❌ No forwarding messages\n"
        "• ❌ No saving media files\n"
        "• ❌ No screenshots (on supported devices)\n"
        "• ❌ No copying text\n\n"
        "<b>Note:</b> This feature uses Telegram's built-in content protection. "
        "While effective, determined users may still find ways to capture content using external tools."
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
    has_api = bool(settings.get('shortlink_api'))
    has_url = bool(settings.get('shortlink_url'))
    has_tutorial = bool(settings.get('tutorial_link'))
    
    status_emoji = "🟢" if enabled else "🔴"
    status_text = "ENABLED" if enabled else "DISABLED"
    
    api_status = "✅ Set" if has_api else "❌ Not Set"
    url_status = "✅ Set" if has_url else "❌ Not Set"
    tutorial_status = "✅ Set" if has_tutorial else "❌ Not Set"
    
    # Check if all required settings are configured
    all_configured = has_api and has_url
    
    buttons = [
        [InlineKeyboardButton(
            f"{status_emoji} Status: {status_text}",
            callback_data=f'toggle_verify_{bot_id}'
        )],
        [InlineKeyboardButton(
            f'🔑 API Key • {api_status}',
            callback_data=f'set_api_{bot_id}'
        )],
        [InlineKeyboardButton(
            f'🔗 Shortlink URL • {url_status}',
            callback_data=f'set_url_{bot_id}'
        )],
        [InlineKeyboardButton(
            f'📖 Tutorial Link • {tutorial_status}',
            callback_data=f'set_tutorial_{bot_id}'
        )],
        [InlineKeyboardButton('« Back to Security', callback_data=f'security_{bot_id}')]
    ]
    
    warning = ""
    if enabled and not all_configured:
        warning = "\n\n⚠️ <b>Warning:</b> Verification is enabled but not fully configured! Set the API Key and Shortlink URL for it to work."
    
    text = (
        "🔐 <b>Shortlink Verification</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Force users to solve a shortlink to get verified and access the bot. This is a powerful way to monetize your bot.\n\n"
        "<b>How it works:</b>\n"
        "1. User starts your bot.\n"
        "2. Bot sends them a verification link (your shortlink).\n"
        "3. User completes the shortlink.\n"
        "4. Bot grants them access.\n\n"
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
    
    current_status = settings.get('verification', False)
    new_status = not current_status
    
    # Prevent enabling if not configured
    if new_status and not (settings.get('shortlink_api') and settings.get('shortlink_url')):
        await query.answer(
            "❌ Cannot enable! Please set both an API Key and a Shortlink URL first.",
            show_alert=True
        )
        return
        
    await clone_db.update_clone_setting(bot_id, 'verification', new_status)
    
    status_text = "ENABLED ✅" if new_status else "DISABLED ❌"
    await query.answer(f"Verification is now {status_text}", show_alert=True)
    
    query.data = f"verification_{bot_id}"
    await verification_menu(client, query)

@Client.on_callback_query(filters.regex("^set_api_"))
async def set_shortlink_api_prompt(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'set_shortlink_api', 'bot_id': bot_id}
    
    text = (
        "🔑 <b>Set Shortlink API Key</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Please send your shortlink provider's API key.\n\n"
        "This is a secret key used by the bot to create verification links. Keep it safe!\n\n"
        "Send /cancel to return to the menu."
    )
    buttons = [[InlineKeyboardButton('❌ Cancel', callback_data=f'verification_{bot_id}')]]
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^set_url_"))
async def set_shortlink_url_prompt(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'set_shortlink_url', 'bot_id': bot_id}
    
    text = (
        "🔗 <b>Set Shortlink URL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Please send the base URL of your shortlink provider.\n\n"
        "<b>Examples:</b>\n"
        "• <code>droplink.co</code>\n"
        "• <code>linksfly.me</code>\n\n"
        "Do not include <code>https://</code> or <code>www.</code> at the beginning.\n\n"
        "Send /cancel to return to the menu."
    )
    buttons = [[InlineKeyboardButton('❌ Cancel', callback_data=f'verification_{bot_id}')]]
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^set_tutorial_"))
async def set_tutorial_link_prompt(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'set_tutorial_link', 'bot_id': bot_id}
    
    text = (
        "📖 <b>Set Tutorial Link</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Optionally, you can provide a link to a tutorial (e.g., a YouTube video or Telegraph page) that shows users how to solve the shortlink.\n\n"
        "This link will be shown to users who need help.\n\n"
        "➡️ <b>To add/update:</b> Send the full URL.\n"
        "➡️ <b>To remove:</b> Send /clear\n\n"
        "Send /cancel to return to the menu."
    )
    buttons = [[InlineKeyboardButton('❌ Cancel', callback_data=f'verification_{bot_id}')]]
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))
