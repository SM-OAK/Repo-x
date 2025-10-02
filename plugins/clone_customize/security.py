# plugins/clone_customize/security.py
import logging
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import MessageNotModified, PeerIdInvalid, ChannelInvalid
from database.clone_db import clone_db
from .input_handler import user_states  # Manages user states for multi-step actions

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Helper Function ---
async def safe_edit_message(query: CallbackQuery, text: str, reply_markup=None):
    """Safely edits a message, handling common errors like MessageNotModified."""
    try:
        await query.message.edit_text(text, reply_markup=reply_markup)
    except MessageNotModified:
        pass  # Ignore if the message content is the same
    except Exception as e:
        logger.error(f"Error editing message for user {query.from_user.id}: {e}")
        try:
            # Notify the user of the error
            await query.answer("An error occurred. Please try again later.", show_alert=True)
        except Exception:
            pass

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
    auto_del = "✅" if settings.get('auto_delete') else "❌"
    protect = "✅" if settings.get('protect_mode') else "❌"
    verify = "✅" if settings.get('verification') else "❌"
    
    buttons = [
        [InlineKeyboardButton(f'Force Subscribe ({fsub_count}/6)', callback_data=f'fsub_manage_{bot_id}')],
        [InlineKeyboardButton(f'{auto_del} Auto Delete', callback_data=f'auto_delete_{bot_id}')],
        [InlineKeyboardButton(f'{protect} Protect Content', callback_data=f'protect_mode_{bot_id}')],
        [InlineKeyboardButton(f'{verify} Verification', callback_data=f'verification_{bot_id}')],
        [InlineKeyboardButton('« Back', callback_data=f'customize_{bot_id}')]
    ]
    text = "<b>🔒 Security Settings</b>\n\nManage access control and content protection for your bot."
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
        
    settings = clone.get('settings', {})
    channels = settings.get('force_sub_channels', [])
    buttons = []
    
    for idx, channel_id in enumerate(channels):
        channel_name = "Fetching Info..."
        try:
            chat = await client.get_chat(channel_id)
            channel_name = chat.title
        except (PeerIdInvalid, ChannelInvalid, ValueError):
            channel_name = f"⚠️ Invalid Channel"
        except Exception as e:
            logger.error(f"Could not get chat for {channel_id}: {e}")
            channel_name = f"❓ Error Fetching Name"

        buttons.append([
            InlineKeyboardButton(f'📢 {channel_name}', callback_data=f'info_{channel_id}'),
            InlineKeyboardButton('❌ Remove', callback_data=f'remove_fsub_{bot_id}_{idx}')
        ])
    
    if len(channels) < 6:
        buttons.append([InlineKeyboardButton('➕ Add Channel', callback_data=f'add_fsub_prompt_{bot_id}')])
    
    buttons.append([InlineKeyboardButton('« Back', callback_data=f'security_{bot_id}')])
    
    text = f"<b>📢 Force Subscribe Settings</b>\nChannels Added: {len(channels)}/6\n\nUsers must join these channels to use your bot."
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^add_fsub_prompt_"))
async def add_fsub_prompt(client, query: CallbackQuery):
    try:
        bot_id = int(query.data.split("_")[3])
    except (IndexError, ValueError):
        return await query.answer("Invalid request.", show_alert=True)
    
    user_states[query.from_user.id] = {'action': 'add_fsub_channel', 'bot_id': bot_id}
    
    text = ("<b>➕ Add Force Subscribe Channel</b>\n\n"
            "Please send the channel's username (e.g., <code>@mychannel</code>) or its ID (e.g., <code>-100123...</code>).\n\n"
            "⚠️ <b>Important:</b> Your bot must be an administrator in the channel for this to work.")
    buttons = [[InlineKeyboardButton('« Cancel', callback_data=f'fsub_manage_{bot_id}')]]
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^remove_fsub_"))
async def remove_fsub(client, query: CallbackQuery):
    try:
        parts = query.data.split("_")
        bot_id = int(parts[2])
        idx_to_remove = int(parts[3])
    except (IndexError, ValueError):
        return await query.answer("Invalid request.", show_alert=True)
    
    clone = await clone_db.get_clone(bot_id)
    if not clone:
        return await query.answer("Bot not found.", show_alert=True)
        
    channels = clone.get('settings', {}).get('force_sub_channels', [])
    
    if 0 <= idx_to_remove < len(channels):
        removed_channel = channels.pop(idx_to_remove)
        await clone_db.update_clone_setting(bot_id, 'force_sub_channels', channels)
        await query.answer(f"✅ Channel removed.", show_alert=False)
    else:
        await query.answer("Channel not found or already removed.", show_alert=True)

    # Refresh the menu to show the change
    query.data = f"fsub_manage_{bot_id}"
    await fsub_manage(client, query)

# ==================== OTHER SETTINGS (Auto Delete, Protect, etc.) ====================
# These functions are now also improved with better error handling and menu refreshing.

@Client.on_callback_query(filters.regex("^auto_delete_"))
async def auto_delete_menu(client, query: CallbackQuery):
    try: bot_id = int(query.data.split("_")[2])
    except (IndexError, ValueError): return await query.answer("Error!", show_alert=True)
    clone = await clone_db.get_clone(bot_id)
    if not clone: return await query.answer("Bot not found!", show_alert=True)
    settings = clone.get('settings', {})
    enabled = settings.get('auto_delete', False)
    minutes = settings.get('auto_delete_time', 1800) // 60
    buttons = [
        [InlineKeyboardButton(f"Status: {'✅ Enabled' if enabled else '❌ Disabled'}", callback_data=f'toggle_autodel_{bot_id}')],
        [InlineKeyboardButton('⏱️ Set Deletion Time', callback_data=f'set_autodel_time_{bot_id}')],
        [InlineKeyboardButton('« Back', callback_data=f'security_{bot_id}')]
    ]
    text = f"<b>🗑️ Auto Delete Settings</b>\n\nAutomatically delete files sent by the bot after a set time.\n\n<b>Status:</b> {'ON' if enabled else 'OFF'}\n<b>Deletion Time:</b> {minutes} minutes"
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^toggle_autodel_"))
async def toggle_autodel(client, query: CallbackQuery):
    try: bot_id = int(query.data.split("_")[2])
    except (IndexError, ValueError): return await query.answer("Error!", show_alert=True)
    clone = await clone_db.get_clone(bot_id)
    if not clone: return await query.answer("Bot not found!", show_alert=True)
    new_status = not clone.get('settings', {}).get('auto_delete', False)
    await clone_db.update_clone_setting(bot_id, 'auto_delete', new_status)
    await query.answer(f"Auto Delete is now {'ENABLED' if new_status else 'DISABLED'}", show_alert=True)
    query.data = f"auto_delete_{bot_id}"
    await auto_delete_menu(client, query)

@Client.on_callback_query(filters.regex("^set_autodel_time_"))
async def set_autodel_time_prompt(client, query: CallbackQuery):
    try: bot_id = int(query.data.split("_")[3])
    except (IndexError, ValueError): return await query.answer("Error!", show_alert=True)
    user_states[query.from_user.id] = {'action': 'autodel_time', 'bot_id': bot_id}
    text = ("<b>⏱️ Set Auto-Deletion Time</b>\n\nPlease send the time in <b>minutes</b>.\n\n"
            "🔹 Minimum: 1\n🔹 Maximum: 100\nExample: <code>30</code>")
    buttons = [[InlineKeyboardButton('« Cancel', callback_data=f'auto_delete_{bot_id}')]]
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^protect_mode_"))
async def protect_mode_menu(client, query: CallbackQuery):
    try: bot_id = int(query.data.split("_")[2])
    except (IndexError, ValueError): return await query.answer("Error!", show_alert=True)
    clone = await clone_db.get_clone(bot_id)
    if not clone: return await query.answer("Bot not found!", show_alert=True)
    enabled = clone.get('settings', {}).get('protect_mode', False)
    buttons = [
        [InlineKeyboardButton(f"Status: {'✅ Enabled' if enabled else '❌ Disabled'}", callback_data=f'toggle_protect_{bot_id}')],
        [InlineKeyboardButton('« Back', callback_data=f'security_{bot_id}')]
    ]
    text = f"<b>🛡️ Protect Content</b>\n\nPrevents users from forwarding or saving files sent by your bot.\n\n<b>Status:</b> {'ON' if enabled else 'OFF'}"
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^toggle_protect_"))
async def toggle_protect(client, query: CallbackQuery):
    try: bot_id = int(query.data.split("_")[2])
    except (IndexError, ValueError): return await query.answer("Error!", show_alert=True)
    clone = await clone_db.get_clone(bot_id)
    if not clone: return await query.answer("Bot not found!", show_alert=True)
    new_status = not clone.get('settings', {}).get('protect_mode', False)
    await clone_db.update_clone_setting(bot_id, 'protect_mode', new_status)
    await query.answer(f"Protect Content is now {'ENABLED' if new_status else 'DISABLED'}", show_alert=True)
    query.data = f"protect_mode_{bot_id}"
    await protect_mode_menu(client, query)

@Client.on_callback_query(filters.regex("^verification_"))
async def verification_menu(client, query: CallbackQuery):
    try: bot_id = int(query.data.split("_")[1])
    except (IndexError, ValueError): return await query.answer("Error!", show_alert=True)
    clone = await clone_db.get_clone(bot_id)
    if not clone: return await query.answer("Bot not found!", show_alert=True)
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
    text = f"<b>🔐 Shortlink Verification</b>\n\nForce users to go through a shortlink to get files.\n\n<b>Status:</b> {'ON' if enabled else 'OFF'}"
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^toggle_verify_"))
async def toggle_verify(client, query: CallbackQuery):
    try: bot_id = int(query.data.split("_")[2])
    except (IndexError, ValueError): return await query.answer("Error!", show_alert=True)
    clone = await clone_db.get_clone(bot_id)
    if not clone: return await query.answer("Bot not found!", show_alert=True)
    new_status = not clone.get('settings', {}).get('verification', False)
    await clone_db.update_clone_setting(bot_id, 'verification', new_status)
    await query.answer(f"Verification is now {'ENABLED' if new_status else 'DISABLED'}", show_alert=True)
    query.data = f"verification_{bot_id}"
    await verification_menu(client, query)

@Client.on_callback_query(filters.regex("^set_api_"))
async def set_shortlink_api_prompt(client, query: CallbackQuery):
    try: bot_id = int(query.data.split("_")[2])
    except (IndexError, ValueError): return await query.answer("Error!", show_alert=True)
    user_states[query.from_user.id] = {'action': 'shortlink_api', 'bot_id': bot_id}
    text = "<b>🔑 Set Shortlink API Key</b>\n\nPlease send your API key from your shortlink provider."
    buttons = [[InlineKeyboardButton('« Cancel', callback_data=f'verification_{bot_id}')]]
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^set_url_"))
async def set_shortlink_url_prompt(client, query: CallbackQuery):
    try: bot_id = int(query.data.split("_")[2])
    except (IndexError, ValueError): return await query.answer("Error!", show_alert=True)
    user_states[query.from_user.id] = {'action': 'shortlink_url', 'bot_id': bot_id}
    text = "<b>🔗 Set Shortlink URL</b>\n\nPlease send the main URL of your shortlink website.\nExample: <code>droplink.co</code>"
    buttons = [[InlineKeyboardButton('« Cancel', callback_data=f'verification_{bot_id}')]]
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^set_tutorial_"))
async def set_tutorial_prompt(client, query: CallbackQuery):
    try: bot_id = int(query.data.split("_")[2])
    except (IndexError, ValueError): return await query.answer("Error!", show_alert=True)
    user_states[query.from_user.id] = {'action': 'tutorial_link', 'bot_id': bot_id}
    text = "<b>📖 Set Tutorial Link</b>\n\nSend a YouTube or any other URL to help users open your shortlinks."
    buttons = [[InlineKeyboardButton('« Cancel', callback_data=f'verification_{bot_id}')]]
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))
