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
        # Ignore if the message content is the same
        pass
    except Exception as e:
        logger.error(f"Error editing message for user {query.from_user.id}: {e}")
        try:
            # Notify the user of the error
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
            display_text = f"{chat.title} (@{chat.username})"
        else:
            # Handle private channels
            try:
                link = await client.export_chat_invite_link(chat.id)
            except Exception:
                link = None # Cannot create link
            display_text = f"{chat.title} (Private)"
        
        return {
            'title': chat.title,
            'link': link,
            'display': display_text,
            'id': chat.id
        }
            
    except (PeerIdInvalid, ChannelInvalid, ValueError):
        return {'title': '⚠️ Invalid Channel', 'link': None, 'display': '⚠️ Invalid/Deleted Channel', 'id': channel_id}
    except Exception as e:
        logger.error(f"Error fetching channel {channel_id}: {e}")
        return {'title': '❓ Error', 'link': None, 'display': '❓ Error Fetching Info', 'id': channel_id}

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
    auto_del = "✅ Enabled" if settings.get('auto_delete') else "❌ Disabled"
    protect = "✅ Enabled" if settings.get('protect_mode') else "❌ Disabled"
    verify = "✅ Enabled" if settings.get('verification') else "❌ Disabled"
    
    buttons = [
        [InlineKeyboardButton(f'📢 Force Subscribe ({fsub_count}/6)', callback_data=f'fsub_manage_{bot_id}')],
        [InlineKeyboardButton(f'🗑️ Auto Delete: {auto_del.split()[0]}', callback_data=f'auto_delete_{bot_id}')],
        [InlineKeyboardButton(f'🛡️ Protect Content: {protect.split()[0]}', callback_data=f'protect_mode_{bot_id}')],
        [InlineKeyboardButton(f'🔐 Verification: {verify.split()[0]}', callback_data=f'verification_{bot_id}')],
        [InlineKeyboardButton('« Back to Customize', callback_data=f'customize_{bot_id}')]
    ]
    text = (
        "<b>🔒 Security Settings</b>\n\n"
        "Manage access control and content protection for your bot.\n\n"
        f"• <b>Force Subscribe:</b> {fsub_count}/6 channels\n"
        f"• <b>Auto Delete:</b> {auto_del}\n"
        f"• <b>Protect Content:</b> {protect}\n"
        f"• <b>Verification:</b> {verify}"
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
    if channels:
        await query.answer("Loading channel details...", show_alert=False)
    
    buttons = []
    for idx, channel_id in enumerate(channels):
        info = await get_channel_info(client, channel_id)
        buttons.append([
            InlineKeyboardButton(f"📢 {info['display']}", callback_data=f'info_fsub_{idx}_{bot_id}'),
            InlineKeyboardButton('❌', callback_data=f'remove_fsub_{bot_id}_{idx}')
        ])
    
    if len(channels) < 6:
        buttons.append([InlineKeyboardButton('➕ Add Channel', callback_data=f'add_fsub_prompt_{bot_id}')])
    else:
        buttons.append([InlineKeyboardButton('⚠️ Max Channels (6/6)', callback_data='noop')])
    
    if channels:
        buttons.append([InlineKeyboardButton('🧪 Test Setup', callback_data=f'test_fsub_{bot_id}')])
    
    buttons.append([InlineKeyboardButton('« Back', callback_data=f'security_{bot_id}')])
    
    text = (
        f"<b>📢 Force Subscribe Management</b>\n<b>Channels:</b> {len(channels)}/6\n\n"
        "Users must join these channels to use your bot. "
        "Make sure the bot is an admin in all channels."
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
        return await query.answer("Channel not found or removed.", show_alert=True)
    
    channel_id = channels[idx]
    info = await get_channel_info(client, channel_id)
    
    try:
        bot_member = await client.get_chat_member(info['id'], (await client.get_me()).id)
        is_admin = bot_member.status in ('administrator', 'creator')
        admin_status = "✅ Bot is Admin" if is_admin else "❌ Bot is NOT an Admin!"
    except Exception:
        admin_status = "❓ Unable to check status."
    
    info_text = (
        f"<b>📢 Channel Info</b>\n\n"
        f"<b>Display:</b> {info['display']}\n"
        f"<b>ID:</b> <code>{info['id']}</code>\n"
        f"<b>Link:</b> {info['link'] or 'N/A'}\n\n"
        f"<b>Status:</b> {admin_status}"
    )
    await query.answer(info_text, show_alert=True)

@Client.on_callback_query(filters.regex("^test_fsub_"))
async def test_force_sub(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    channels = clone.get('settings', {}).get('force_sub_channels', [])
    if not channels:
        return await query.answer("No channels configured to test.", show_alert=True)
    
    not_joined = []
    for channel_id in channels:
        try:
            await client.get_chat_member(channel_id, query.from_user.id)
        except UserNotParticipant:
            info = await get_channel_info(client, channel_id)
            not_joined.append(info['title'])
        except Exception as e:
            logger.error(f"Error checking membership for {channel_id}: {e}")
            not_joined.append(f"❓ Error with channel ID {channel_id}")
    
    if not_joined:
        result = "❌ Test Failed!\nYou have not joined:\n" + "\n".join([f"• {ch}" for ch in not_joined])
    else:
        result = "✅ Test Passed!\nYou are subscribed to all required channels."
    await query.answer(result, show_alert=True)

@Client.on_callback_query(filters.regex("^add_fsub_prompt_"))
async def add_fsub_prompt(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_states[query.from_user.id] = {'action': 'add_fsub_channel', 'bot_id': bot_id}
    text = (
        "<b>➕ Add Channel</b>\n\n"
        "Send the channel's username (e.g., `@channelname`) or ID (e.g., `-100123...`).\n\n"
        "💡 <b>Tip:</b> Forward a message from the target channel to @userinfobot to get its ID.\n\n"
        "⚠️ Your bot must be an <b>administrator</b> in the channel."
    )
    buttons = [[InlineKeyboardButton('« Cancel', callback_data=f'fsub_manage_{bot_id}')]]
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
        await query.answer("Channel already removed.", show_alert=True)

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
    minutes = settings.get('auto_delete_time', 30) // 60
    
    buttons = [
        [InlineKeyboardButton(f"Status: {'✅ Enabled' if enabled else '❌ Disabled'}", callback_data=f'toggle_autodel_{bot_id}')],
        [InlineKeyboardButton(f'⏱️ Set Time ({minutes} min)', callback_data=f'set_autodel_time_{bot_id}')],
        [InlineKeyboardButton('« Back', callback_data=f'security_{bot_id}')]
    ]
    text = f"<b>🗑️ Auto Delete Files</b>\n\nAutomatically delete files sent by the bot after a set duration.\n\n<b>Status: {'ON' if enabled else 'OFF'}</b>"
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^toggle_autodel_"))
async def toggle_autodel(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    new_status = not clone.get('settings', {}).get('auto_delete', False)
    await clone_db.update_clone_setting(bot_id, 'auto_delete', new_status)
    await query.answer(f"Auto Delete is now {'ENABLED' if new_status else 'DISABLED'}", show_alert=True)
    query.data = f"auto_delete_{bot_id}"
    await auto_delete_menu(client, query)

@Client.on_callback_query(filters.regex("^set_autodel_time_"))
async def set_autodel_time_prompt(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_states[query.from_user.id] = {'action': 'autodel_time', 'bot_id': bot_id}
    text = (
        "<b>⏱️ Set Deletion Time</b>\n\nPlease send the auto-deletion time in <b>minutes</b>.\n\n"
        "• Minimum: `1`\n• Maximum: `120`\n\nExample: `30` for 30 minutes."
    )
    buttons = [[InlineKeyboardButton('« Cancel', callback_data=f'auto_delete_{bot_id}')]]
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

# ==================== PROTECT CONTENT SECTION ====================
@Client.on_callback_query(filters.regex("^protect_mode_"))
async def protect_mode_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    enabled = clone.get('settings', {}).get('protect_mode', False)
    buttons = [
        [InlineKeyboardButton(f"Status: {'✅ Enabled' if enabled else '❌ Disabled'}", callback_data=f'toggle_protect_{bot_id}')],
        [InlineKeyboardButton('« Back', callback_data=f'security_{bot_id}')]
    ]
    text = (
        "<b>🛡️ Protect Content</b>\n\n"
        "Prevents users from forwarding, saving, or taking screenshots of content sent by your bot.\n\n"
        "<b>Status: {'ON' if enabled else 'OFF'}</b>"
    )
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^toggle_protect_"))
async def toggle_protect(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    new_status = not clone.get('settings', {}).get('protect_mode', False)
    await clone_db.update_clone_setting(bot_id, 'protect_mode', new_status)
    await query.answer(f"Protect Content is now {'ENABLED' if new_status else 'DISABLED'}", show_alert=True)
    query.data = f"protect_mode_{bot_id}"
    await protect_mode_menu(client, query)
    
# ==================== VERIFICATION SECTION ====================
@Client.on_callback_query(filters.regex("^verification_"))
async def verification_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    enabled = settings.get('verification', False)
    has_api = "✅ Set" if settings.get('shortlink_api') else "❌ Not Set"
    has_url = "✅ Set" if settings.get('shortlink_url') else "❌ Not Set"
    has_tutorial = "✅ Set" if settings.get('tutorial_link') else "❌ Not Set"
    buttons = [
        [InlineKeyboardButton(f"Status: {'✅ Enabled' if enabled else '❌ Disabled'}", callback_data=f'toggle_verify_{bot_id}')],
        [InlineKeyboardButton(f'API Key: {has_api}', callback_data=f'set_api_{bot_id}')],
        [InlineKeyboardButton(f'Shortlink URL: {has_url}', callback_data=f'set_url_{bot_id}')],
        [InlineKeyboardButton(f'Tutorial Link: {has_tutorial}', callback_data=f'set_tutorial_{bot_id}')],
        [InlineKeyboardButton('« Back', callback_data=f'security_{bot_id}')]
    ]
    text = f"<b>🔐 Shortlink Verification</b>\n\nForce users to complete a shortlink before receiving files.\n\n<b>Status: {'ON' if enabled else 'OFF'}</b>"
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^toggle_verify_"))
async def toggle_verify(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    new_status = not clone.get('settings', {}).get('verification', False)
    await clone_db.update_clone_setting(bot_id, 'verification', new_status)
    await query.answer(f"Verification is now {'ENABLED' if new_status else 'DISABLED'}", show_alert=True)
    query.data = f"verification_{bot_id}"
    await verification_menu(client, query)

@Client.on_callback_query(filters.regex("^set_api_"))
async def set_shortlink_api_prompt(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'shortlink_api', 'bot_id': bot_id}
    text = "<b>🔑 Set Shortlink API Key</b>\n\nPlease send the API key from your shortlink provider."
    buttons = [[InlineKeyboardButton('« Cancel', callback_data=f'verification_{bot_id}')]]
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^set_url_"))
async def set_shortlink_url_prompt(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'shortlink_url', 'bot_id': bot_id}
    text = "<b>🔗 Set Shortlink URL</b>\n\nPlease send the main URL of your shortlink site.\nExample: `droplink.co` or `mdisk.me`"
    buttons = [[InlineKeyboardButton('« Cancel', callback_data=f'verification_{bot_id}')]]
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^set_tutorial_"))
async def set_tutorial_prompt(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'tutorial_link', 'bot_id': bot_id}
    text = "<b>📖 Set Tutorial Link</b>\n\nSend a link (e.g., YouTube, Telegraph) that shows users how to open your shortlinks."
    buttons = [[InlineKeyboardButton('« Cancel', callback_data=f'verification_{bot_id}')]]
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))
