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
        if isinstance(channel_id, str) and channel_id.lstrip('-').isdigit():
            channel_id = int(channel_id)

        chat = await client.get_chat(channel_id)

        if chat.username:
            link = f"https://t.me/{chat.username}"
            display_text = f"{chat.title} (@{chat.username})"
        else:
            try:
                link = await client.export_chat_invite_link(chat.id)
            except Exception:
                link = None
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
        "⚠️ Make sure <b>only the clone bot</b> is an admin in these channels."
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

    # ✅ Check with CLONE BOT, not manager
    try:
        clone_bot = await Client(f"clone_{bot_id}").get_me()
        bot_member = await client.get_chat_member(info['id'], clone_bot.id)
        is_admin = bot_member.status in ('administrator', 'creator')
        admin_status = "✅ Clone Bot is Admin" if is_admin else "❌ Clone Bot is NOT an Admin!"
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

# ==================== AUTO DELETE SECTION ====================
@Client.on_callback_query(filters.regex("^auto_delete_"))
async def auto_delete_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    if not clone: return await query.answer("Bot not found!", show_alert=True)

    settings = clone.get('settings', {})
    enabled = settings.get('auto_delete', False)
    seconds = settings.get('auto_delete_time', 1200)  # default 20min
    minutes = seconds // 60

    buttons = [
        [InlineKeyboardButton(f"Status: {'✅ Enabled' if enabled else '❌ Disabled'}", callback_data=f'toggle_autodel_{bot_id}')],
        [InlineKeyboardButton(f'⏱️ Set Time ({minutes} min)', callback_data=f'set_autodel_time_{bot_id}')],
        [InlineKeyboardButton('« Back', callback_data=f'security_{bot_id}')]
    ]
    text = f"<b>🗑️ Auto Delete Files</b>\n\nAutomatically delete files sent by the bot after a set duration.\n\n<b>Status: {'ON' if enabled else 'OFF'}</b>"
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_callback_query(filters.regex("^set_autodel_time_"))
async def set_autodel_time_prompt(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[3])
    user_states[query.from_user.id] = {'action': 'autodel_time', 'bot_id': bot_id}
    text = (
        "<b>⏱️ Set Deletion Time</b>\n\nPlease send the auto-deletion time in <b>minutes</b>.\n\n"
        "• Minimum: `0.33` (20 seconds)\n• Maximum: `720` (12 hours)\n\n"
        "Example: `30` for 30 minutes."
    )
    buttons = [[InlineKeyboardButton('« Cancel', callback_data=f'auto_delete_{bot_id}')]]
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

# ==================== VERIFICATION SECTION (Fix missing bracket) ====================
@Client.on_callback_query(filters.regex("^set_tutorial_"))
async def set_tutorial_prompt(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    user_states[query.from_user.id] = {'action': 'tutorial_link', 'bot_id': bot_id}
    text = "<b>📖 Set Tutorial Link</b>\n\nSend a link (e.g., YouTube, Telegraph) that shows users how to open your shortlinks."
    buttons = [[InlineKeyboardButton('« Cancel', callback_data=f'verification_{bot_id}')]]
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))
