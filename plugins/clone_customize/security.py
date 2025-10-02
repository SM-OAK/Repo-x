# plugins/clone_customize/security.py

import logging
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import MessageNotModified, PeerIdInvalid, ChannelInvalid
from database.clone_db import clone_db

# input_handler se user_states import karna, taaki alag-alag steps wale commands kaam kar sakein
from .input_handler import user_states

# Debugging ke liye logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def safe_edit_message(query: CallbackQuery, text: str, reply_markup=None):
    """
    Message ko safely edit karne ke liye helper function. 
    Yeh 'MessageNotModified' jaise errors ko handle karta hai.
    """
    try:
        await query.message.edit_text(text, reply_markup=reply_markup)
    except MessageNotModified:
        # Agar message pehle se hi same hai to error aata hai, ise ignore karna safe hai.
        pass
    except Exception as e:
        logger.error(f"Message edit karne mein error (user: {query.from_user.id}): {e}")
        try:
            # User ko error ke baare mein batana
            await query.answer("Ek error aa gaya hai. Kripya dobara koshish karein.", show_alert=True)
        except Exception as alert_e:
            logger.error(f"User ko error alert bhejne mein fail hua: {alert_e}")

# ==================== SECURITY (Main Menu) ====================
@Client.on_callback_query(filters.regex("^security_"))
async def security_menu(client, query: CallbackQuery):
    try:
        bot_id = int(query.data.split("_")[1])
    except (IndexError, ValueError):
        await query.answer("Invalid request. Kripya shuru se koshish karein.", show_alert=True)
        return

    clone = await clone_db.get_clone(bot_id)
    if not clone:
        await query.answer("Yeh bot ab uplabdh nahi hai.", show_alert=True)
        return
        
    settings = clone.get('settings', {})
    
    fsub_count = len(settings.get('force_sub_channels', []))
    auto_del_status = "✅" if settings.get('auto_delete') else "❌"
    protect_status = "✅" if settings.get('protect_mode') else "❌"
    verify_status = "✅" if settings.get('verification') else "❌"
    
    buttons = [
        [InlineKeyboardButton(f'Force Sub ({fsub_count}/6)', callback_data=f'fsub_manage_{bot_id}')],
        [InlineKeyboardButton(f'{auto_del_status} Auto Delete', callback_data=f'auto_delete_{bot_id}')],
        [InlineKeyboardButton(f'{protect_status} Protect Mode', callback_data=f'protect_mode_{bot_id}')],
        [InlineKeyboardButton(f'{verify_status} Verification', callback_data=f'verification_{bot_id}')],
        [InlineKeyboardButton('« Back', callback_data=f'customize_{bot_id}')]
    ]
    
    text = "<b>🔒 Security Settings</b>\n\n<i>Yahan se aap apne bot ke liye suraksha se judi settings badal sakte hain.</i>"
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

# ==================== Force Subscribe Management ====================
@Client.on_callback_query(filters.regex("^fsub_manage_"))
async def fsub_manage(client, query: CallbackQuery):
    try:
        bot_id = int(query.data.split("_")[2])
    except (IndexError, ValueError):
        return await query.answer("Anurodh mein galti hai.", show_alert=True)

    clone = await clone_db.get_clone(bot_id)
    if not clone:
        return await query.answer("Yeh bot ab uplabdh nahi hai.", show_alert=True)
        
    settings = clone.get('settings', {})
    channels = settings.get('force_sub_channels', [])
    
    buttons = []
    
    # Har channel ke liye uski details nikalenge
    for idx, ch_identifier in enumerate(channels):
        channel_name = f"..." 
        try:
            chat = await client.get_chat(ch_identifier)
            channel_name = chat.title
        except (PeerIdInvalid, ChannelInvalid, ValueError):
            logger.warning(f"Chat nahi mila: {ch_identifier}. Invalid ID ya bot member nahi hai.")
            channel_name = f"⚠️ Invalid ID/Username"
        except Exception as e:
            logger.error(f"Chat fetch karne mein error ({ch_identifier}): {e}")
            channel_name = f"❓ Error"

        buttons.append([
            InlineKeyboardButton(f'📢 {channel_name}', url=f"https://t.me/{str(ch_identifier).replace('@', '')}" if isinstance(ch_identifier, str) and ch_identifier.startswith('@') else f"tg://resolve?domain=c&chat_id={str(ch_identifier).replace('-100', '')}"),
            InlineKeyboardButton('❌ Hataein', callback_data=f'remove_fsub_{bot_id}_{idx}')
        ])
    
    if len(channels) < 6:
        buttons.append([InlineKeyboardButton('➕ Channel Jodein', callback_data=f'add_fsub_{bot_id}')])
    
    buttons.append([InlineKeyboardButton('« Back', callback_data=f'security_{bot_id}')])
    
    text = f"<b>🔒 Force Subscribe</b>\n<b>Channels:</b> {len(channels)}/6\n\n<i>Aapke bot ka upyog karne ke liye users ko in channels ko join karna hoga. Public channel ka username (@username) ya private channel ki ID jodein.</i>"
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_callback_query(filters.regex("^add_fsub_"))
async def add_fsub_prompt(client, query: CallbackQuery):
    try:
        bot_id = int(query.data.split("_")[2])
    except (IndexError, ValueError):
        return await query.answer("Anurodh mein galti hai.", show_alert=True)
    
    user_states[query.from_user.id] = {'action': 'add_fsub_channel', 'bot_id': bot_id}
    
    text = (
        "<b>➕ Force Subscribe Channel Jodein</b>\n\n"
        "Kripya channel ka username (jaise <code>@TechVJ</code>) ya uski ID bhejein.\n\n"
        "<i>Private channel ke liye, channel se koi message @userinfobot ko forward karke ID prapt karein.</i>\n\n"
        "⚠️ <b>Zaroori:</b> Is feature ke kaam karne ke liye aapka bot us channel mein ek administrator hona chahiye."
    )
    
    buttons = [[InlineKeyboardButton('« Cancel', callback_data=f'fsub_manage_{bot_id}')]]
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^remove_fsub_"))
async def remove_fsub(client, query: CallbackQuery):
    try:
        parts = query.data.split("_")
        bot_id = int(parts[2])
        idx_to_remove = int(parts[3])
    except (IndexError, ValueError):
        return await query.answer("Anurodh mein galti hai.", show_alert=True)
    
    clone = await clone_db.get_clone(bot_id)
    if not clone:
        return await query.answer("Yeh bot ab uplabdh nahi hai.", show_alert=True)
        
    channels = clone.get('settings', {}).get('force_sub_channels', [])
    
    if 0 <= idx_to_remove < len(channels):
        removed_channel = channels.pop(idx_to_remove)
        await clone_db.update_clone_setting(bot_id, 'force_sub_channels', channels)
        await query.answer(f"✅ Channel '{removed_channel}' hata diya gaya hai.", show_alert=False)
    else:
        await query.answer("Channel nahi mila. Shayad ise pehle hi hata diya gaya hai.", show_alert=True)

    # Menu ko refresh karne ke liye, fsub_manage ko sahi data ke sath call karein
    query.data = f"fsub_manage_{bot_id}"
    await fsub_manage(client, query)

# ==================== Auto Delete & other toggles ====================
# Note: Baaki ke functions (Auto Delete, Protect Mode, Verification) aapke original code mein aam taur par theek the.
# Maine un sabhi mein crash protection aur behtar menu refresh logic joda hai.

# ... Auto Delete ...
@Client.on_callback_query(filters.regex("^auto_delete_"))
async def auto_delete_menu(client, query: CallbackQuery):
    try: bot_id = int(query.data.split("_")[2])
    except (IndexError, ValueError): return await query.answer("Error!", show_alert=True)
    
    clone = await clone_db.get_clone(bot_id)
    if not clone: return await query.answer("Bot not found!", show_alert=True)
    settings = clone.get('settings', {})
    
    enabled = settings.get('auto_delete', False)
    time_sec = settings.get('auto_delete_time', 1800)
    minutes = time_sec // 60
    
    buttons = [
        [InlineKeyboardButton(f"Status: {'✅ Enabled' if enabled else '❌ Disabled'}", callback_data=f'toggle_autodel_{bot_id}')],
        [InlineKeyboardButton('⏱️ Deletion Time Set Karein', callback_data=f'set_autodel_time_{bot_id}')],
        [InlineKeyboardButton('« Back', callback_data=f'security_{bot_id}')]
    ]
    status = "ON" if enabled else "OFF"
    text = f"<b>🗑️ Auto Delete Settings</b>\n\nYeh feature bot dwara bheji gayi files ko ek nishchit samay ke baad delete kar deta hai.\n\n<b>Current Status:</b> {status}\n<b>Deletion Time:</b> {minutes} minutes"
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^toggle_autodel_"))
async def toggle_autodel(client, query: CallbackQuery):
    try: bot_id = int(query.data.split("_")[2])
    except (IndexError, ValueError): return await query.answer("Error!", show_alert=True)
    clone = await clone_db.get_clone(bot_id)
    if not clone: return await query.answer("Bot not found!", show_alert=True)
    current = clone.get('settings', {}).get('auto_delete', False)
    new_status = not current
    await clone_db.update_clone_setting(bot_id, 'auto_delete', new_status)
    await query.answer(f"Auto Delete ab {'ENABLED' if new_status else 'DISABLED'} hai", show_alert=True)
    query.data = f"auto_delete_{bot_id}"
    await auto_delete_menu(client, query)

@Client.on_callback_query(filters.regex("^set_autodel_time_"))
async def set_autodel_time(client, query: CallbackQuery):
    try: bot_id = int(query.data.split("_")[3])
    except (IndexError, ValueError): return await query.answer("Error!", show_alert=True)
    user_states[query.from_user.id] = {'action': 'autodel_time', 'bot_id': bot_id}
    text = ("<b>⏱️ Auto-Deletion Time Set Karein</b>\n\nKripya <b>minutes</b> mein samay bhejein jiske baad files delete ho jaani chahiye.\n\n"
            "🔹 Kam se kam: 1 minute\n🔹 Adhiktam: 100 minutes\n"
            "Udhaaran: <code>5</code>, <code>30</code>, <code>60</code>\n\n"
            "Cancel karne ke liye, neeche button dabayein ya /cancel type karein.")
    buttons = [[InlineKeyboardButton('« Cancel', callback_data=f'auto_delete_{bot_id}')]]
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

# ... Protect Mode ...
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
    status = "ON" if enabled else "OFF"
    text = f"<b>🛡️ Protect Content Mode</b>\n\nJab yeh chalu hota hai, to users aapke bot se bheji gayi files ko forward ya save nahi kar paate.\n\n<b>Current Status:</b> {status}"
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^toggle_protect_"))
async def toggle_protect(client, query: CallbackQuery):
    try: bot_id = int(query.data.split("_")[2])
    except (IndexError, ValueError): return await query.answer("Error!", show_alert=True)
    clone = await clone_db.get_clone(bot_id)
    if not clone: return await query.answer("Bot not found!", show_alert=True)
    current = clone.get('settings', {}).get('protect_mode', False)
    new_status = not current
    await clone_db.update_clone_setting(bot_id, 'protect_mode', new_status)
    await query.answer(f"Protect Mode ab {'ENABLED' if new_status else 'DISABLED'} hai", show_alert=True)
    query.data = f"protect_mode_{bot_id}"
    await protect_mode_menu(client, query)

# ... Verification ...
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
    status = "ON" if enabled else "OFF"
    text = f"<b>🔐 Shortlink Verification</b>\n\nUsers ko file prapt karne ke liye ek shortlink se guzarne ke liye majboor karein.\n\n<b>Current Status:</b> {status}"
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^toggle_verify_"))
async def toggle_verify(client, query: CallbackQuery):
    try: bot_id = int(query.data.split("_")[2])
    except (IndexError, ValueError): return await query.answer("Error!", show_alert=True)
    clone = await clone_db.get_clone(bot_id)
    if not clone: return await query.answer("Bot not found!", show_alert=True)
    current = clone.get('settings', {}).get('verification', False)
    new_status = not current
    await clone_db.update_clone_setting(bot_id, 'verification', new_status)
    await query.answer(f"Verification ab {'ENABLED' if new_status else 'DISABLED'} hai", show_alert=True)
    query.data = f"verification_{bot_id}"
    await verification_menu(client, query)

@Client.on_callback_query(filters.regex("^set_api_"))
async def set_shortlink_api(client, query: CallbackQuery):
    try: bot_id = int(query.data.split("_")[2])
    except (IndexError, ValueError): return await query.answer("Error!", show_alert=True)
    user_states[query.from_user.id] = {'action': 'shortlink_api', 'bot_id': bot_id}
    text = ("<b>🔑 Shortlink API Key Set Karein</b>\n\nKripya apne shortlink provider se prapt API key bhejein.\n\nCancel karne ke liye /cancel type karein.")
    buttons = [[InlineKeyboardButton('« Cancel', callback_data=f'verification_{bot_id}')]]
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^set_url_"))
async def set_shortlink_url(client, query: CallbackQuery):
    try: bot_id = int(query.data.split("_")[2])
    except (IndexError, ValueError): return await query.answer("Error!", show_alert=True)
    user_states[query.from_user.id] = {'action': 'shortlink_url', 'bot_id': bot_id}
    text = ("<b>🔗 Shortlink URL Set Karein</b>\n\nApni shortlink website ka mukhya URL bhejein.\nUdhaaran: <code>droplink.co</code> ya <code>https://za.gl</code>\n\nCancel karne ke liye /cancel type karein.")
    buttons = [[InlineKeyboardButton('« Cancel', callback_data=f'verification_{bot_id}')]]
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^set_tutorial_"))
async def set_tutorial(client, query: CallbackQuery):
    try: bot_id = int(query.data.split("_")[2])
    except (IndexError, ValueError): return await query.answer("Error!", show_alert=True)
    user_states[query.from_user.id] = {'action': 'tutorial_link', 'bot_id': bot_id}
    text = ("<b> TUTORIAL LINK </b>\n\nApna YouTube ya koi aur tutorial URL bhejein taaki users ko shortlink kholne mein madad mile.\n\nCancel karne ke liye /cancel type karein.")
    buttons = [[InlineKeyboardButton('« Cancel', callback_data=f'verification_{bot_id}')]]
    await safe_edit_message(query, text, reply_markup=InlineKeyboardMarkup(buttons))

