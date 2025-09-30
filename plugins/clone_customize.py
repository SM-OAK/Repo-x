# clone_customize.py

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.clone_db import clone_db
import logging
import asyncio

logger = logging.getLogger(__name__)

# Main Customize Menu
@Client.on_callback_query(filters.regex(r"^customize_(\d+)$"))
async def customize_clone_menu(client, query: CallbackQuery):
    bot_id = int(query.matches[0].group(1))
    clone = await clone_db.get_clone(bot_id)
    
    if not clone:
        return await query.answer("Clone not found!", show_alert=True)
    
    if clone['user_id'] != query.from_user.id:
        return await query.answer("This is not your clone!", show_alert=True)
    
    buttons = [
        [
            InlineKeyboardButton('📝 sᴛᴀʀᴛ ᴍsɢ', callback_data=f'set_start_{bot_id}'),
            InlineKeyboardButton('🔒 ғᴏʀᴄᴇ sᴜʙ', callback_data=f'set_fsub_{bot_id}')
        ],
        [
            InlineKeyboardButton('⏱️ ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ', callback_data=f'autodel_menu_{bot_id}')
        ],
        [
            InlineKeyboardButton('📊 sᴛᴀᴛs', callback_data=f'clone_stats_{bot_id}'),
            InlineKeyboardButton('🔄 ʀᴇsᴛᴀʀᴛ', callback_data=f'restart_clone_{bot_id}')
        ],
        [
            InlineKeyboardButton('🔙 ʙᴀᴄᴋ', callback_data='clone'),
            InlineKeyboardButton('🗑️ ᴅᴇʟᴇᴛᴇ', callback_data=f'delete_clone_{bot_id}')
        ]
    ]
    
    settings_text = (
        f"<b>🛠️ Cᴜsᴛᴏᴍɪᴢᴇ Cʟᴏɴᴇ</b>\n\n"
        f"➜ <b>Nᴀᴍᴇ:</b> {clone['name']}\n"
        f"➜ <b>Usᴇʀɴᴀᴍᴇ:</b> @{clone['username']}\n\n"
        f"Cᴏɴғɪɢᴜʀᴇ ʏᴏᴜʀ ᴄʟᴏɴᴇ sᴇᴛᴛɪngs ᴜsɪɴɢ ᴛʜᴇ ʙᴜᴛᴛᴏɴs ʙᴇʟᴏᴡ:"
    )
    
    await query.message.edit_text(settings_text, reply_markup=InlineKeyboardMarkup(buttons))


# --- Auto Delete Section ---

# Auto Delete Main Menu
@Client.on_callback_query(filters.regex(r"^autodel_menu_"))
async def auto_delete_menu(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    settings = clone.get('settings', {})
    
    status = settings.get('auto_delete', False)
    delete_time_seconds = settings.get('auto_delete_time', 300)
    delete_time_minutes = delete_time_seconds // 60
    
    text = (
        f"**Auto Delete**\n\n"
        f"Automatically delete all messages sent to clone users after {delete_time_minutes} minutes.\n\n"
        f"**Status:** {'Enabled ✅' if status else 'Disabled ❌'}"
    )
    
    buttons = [
        [
            InlineKeyboardButton('⏰ Change Time', callback_data=f'autodel_time_{bot_id}'),
            InlineKeyboardButton('💬 Message', callback_data=f'autodel_msg_{bot_id}')
        ],
        [
            InlineKeyboardButton('✅ Enable' if not status else '❌ Disable', callback_data=f'autodel_toggle_{bot_id}')
        ],
        [
            InlineKeyboardButton('🔙 Back', callback_data=f'customize_{bot_id}')
        ]
    ]
    
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

# Toggle Enable/Disable
@Client.on_callback_query(filters.regex(r"^autodel_toggle_"))
async def toggle_auto_delete(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    current_status = clone.get('settings', {}).get('auto_delete', False)
    new_status = not current_status
    
    await clone_db.update_clone_setting(bot_id, 'auto_delete', new_status)
    await query.answer(f"Auto Delete has been {'Enabled' if new_status else 'Disabled'}.")
    
    query.data = f"autodel_menu_{bot_id}"
    await auto_delete_menu(client, query)

# Set Auto Delete Time
@Client.on_callback_query(filters.regex(r"^autodel_time_"))
async def set_autodel_time(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    
    try:
        ask_msg = await query.message.edit_text(
            "**Enter the auto-delete time in minutes.**\n\n"
            "Example: `5` for 5 minutes.\n\n"
            "Use /cancel to go back."
        )
        
        response = await client.ask(query.from_user.id, timeout=120)
        
        if response.text:
            if response.text == "/cancel":
                await response.delete()
                await query.answer("Canceled.")
            elif response.text.isdigit():
                minutes = int(response.text)
                seconds = minutes * 60
                await clone_db.update_clone_setting(bot_id, 'auto_delete_time', seconds)
                await query.answer(f"Time set to {minutes} minutes.", show_alert=True)
                await response.delete()
            else:
                await query.answer("Invalid input. Please send a number.", show_alert=True)
                await response.delete()
        
    except asyncio.TimeoutError:
        await query.answer("Timeout! Process canceled.", show_alert=True)
    finally:
        await ask_msg.delete()
        query.data = f"autodel_menu_{bot_id}"
        await auto_delete_menu(client, query)

# Set Auto Delete Message
@Client.on_callback_query(filters.regex(r"^autodel_msg_"))
async def set_autodel_msg(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    
    try:
        ask_msg = await query.message.edit_text(
            "**Send the new auto-delete warning message.**\n\n"
            "You can use the placeholder `{time}` which will be replaced with the deletion time (e.g., '5 minutes').\n\n"
            "Use /cancel to go back."
        )

        response = await client.ask(query.from_user.id, timeout=300)
        
        if response.text:
            if response.text == "/cancel":
                 await response.delete()
                 await query.answer("Canceled.")
            else:
                await clone_db.update_clone_setting(bot_id, 'auto_delete_message', response.text)
                await query.answer("Message updated successfully.", show_alert=True)
                await response.delete()
        
    except asyncio.TimeoutError:
        await query.answer("Timeout! Process canceled.", show_alert=True)
    finally:
        await ask_msg.delete()
        query.data = f"autodel_menu_{bot_id}"
        await auto_delete_menu(client, query)


# --- Other Settings ---

# Start message setting
@Client.on_callback_query(filters.regex("^set_start_"))
async def set_start_msg(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    await query.message.edit_text("<b>📝 Sᴇɴᴅ ʏᴏᴜʀ ᴄᴜsᴛᴏᴍ sᴛᴀʀᴛ ᴍᴇssᴀɢᴇ:</b>\n\nUsᴇ /cancel ᴛᴏ ᴄᴀɴᴄᴇʟ")
    
    try:
        msg = await client.ask(query.message.chat.id, timeout=300)
        if msg.text == '/cancel':
            return await query.message.edit_text("Cᴀɴᴄᴇʟᴇᴅ!")
        
        await clone_db.update_clone_setting(bot_id, 'start_message', msg.text)
        await query.message.edit_text(
            "✅ Sᴛᴀʀᴛ ᴍᴇssᴀɢᴇ ᴜᴘᴅᴀᴛᴇᴅ!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]])
        )
    except:
        await query.message.edit_text("Tɪᴍᴇᴏᴜᴛ!")

# Force sub setting
@Client.on_callback_query(filters.regex("^set_fsub_"))
async def set_force_sub(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    await query.message.edit_text("<b>🔒 Sᴇɴᴅ ᴄʜᴀɴɴᴇʟ ID:</b>\n\nExᴀᴍᴘʟᴇ: <code>-100123456789</code>\n\nUsᴇ /cancel ᴛᴏ ᴄᴀɴᴄᴇʟ")
    
    try:
        msg = await client.ask(query.message.chat.id, timeout=300)
        if msg.text == '/cancel':
            return await query.message.edit_text("Cᴀɴᴄᴇʟᴇᴅ!")
        
        await clone_db.update_clone_setting(bot_id, 'force_sub_channel', int(msg.text))
        await query.message.edit_text(
            "✅ Fᴏʀᴄᴇ sᴜʙsᴄʀɪᴘᴛɪᴏɴ ᴜᴘᴅᴀᴛᴇᴅ!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]])
        )
    except:
        await query.message.edit_text("Iɴᴠᴀʟɪᴅ ID!")

# Clone stats
@Client.on_callback_query(filters.regex("^clone_stats_"))
async def clone_stats(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    users = await clone_db.get_clone_users_count(bot_id)
    
    await query.message.edit_text(
        f"<b>📊 Cʟᴏɴᴇ Sᴛᴀᴛs</b>\n\n"
        f"🤖 Bᴏᴛ: @{clone['username']}\n"
        f"👥 Usᴇʀs: {users}\n"
        f"📅 Cʀᴇᴀᴛᴇᴅ: {clone.get('created_at', 'N/A')}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data=f'customize_{bot_id}')]])
    )

# Restart clone
@Client.on_callback_query(filters.regex("^restart_"))
async def restart_clone(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    await query.answer("Rᴇsᴛᴀʀᴛɪɴɢ ᴄʟᴏɴᴇ...", show_alert=True)
    # Add restart logic here

# Delete clone
@Client.on_callback_query(filters.regex("^delete_(?!clone)"))
async def delete_clone_confirm(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    
    buttons = [
        [
            InlineKeyboardButton('✅ Yᴇs', callback_data=f'confirm_delete_{bot_id}'),
            InlineKeyboardButton('❌ Nᴏ', callback_data=f'customize_{bot_id}')
        ]
    ]
    
    await query.message.edit_text(
        "⚠️ <b>Aʀᴇ ʏᴏᴜ sᴜʀᴇ?</b>\n\nTʜɪs ᴡɪʟʟ ᴘᴇʀᴍᴀɴᴇɴᴛʟʏ ᴅᴇʟᴇᴛᴇ ʏᴏᴜʀ ᴄʟᴏɴᴇ!",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex("^confirm_delete_"))
async def confirm_delete_clone(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    
    if clone['user_id'] != query.from_user.id:
        return await query.answer("Access denied!", show_alert=True)
    
    await clone_db.delete_clone_by_id(bot_id)
    await query.message.edit_text("✅ Cʟᴏɴᴇ ᴅᴇʟᴇᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!")
