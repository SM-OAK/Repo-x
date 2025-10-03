# plugins/clone_customize/input_handler.py
from pyrogram import Client, filters, types
from pyrogram.errors import PeerIdInvalid, ChannelInvalid, UsernameInvalid
from database.clone_db import clone_db
import logging

logger = logging.getLogger(__name__)

# User states dictionary
user_states = {}

# ==================== USER INPUT HANDLER ====================
@Client.on_message(filters.private & filters.text, group=2)
async def handle_setting_input(client, message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return
    
    state = user_states[user_id]
    action = state['action']
    bot_id = state['bot_id']

    # Cancel
    if message.text == '/cancel':
        del user_states[user_id]
        # We need to determine which menu to go back to. For now, a generic back is okay.
        # A more advanced implementation would store the 'back_callback' in the state.
        return await message.reply("❌ Action cancelled.")
    
    try:
        # --- REFACTORED ACTION MAP ---
        # Stores: (database_key, back_callback_prefix)
        action_map = {
            'start_text': ('start_message', f'start_text_'),
            'start_button': ('start_button', f'start_button_'),
            'file_caption': ('file_caption', f'file_caption_'),
            'shortlink_api': ('shortlink_api', f'verification_'),
            'shortlink_url': ('shortlink_url', f'verification_'),
            'tutorial_link': ('tutorial_link', f'verification_'),
            'mongo_db': ('mongo_db', f'mongo_db_'),
            # Corrected prefixes to match bot_settings.py
            'log_channel': ('log_channel', f'log_channel_manage_'),
            'db_channel': ('db_channel', f'db_channel_manage_'),
        }

        # Simple text input handling
        if action in action_map:
            setting_key, back_callback_prefix = action_map[action]
            
            # Build the full callback data now that we have bot_id
            back_callback = back_callback_prefix + str(bot_id)

            await clone_db.update_clone_setting(bot_id, setting_key, message.text.strip())
            del user_states[user_id]
            return await message.reply(
                f"✅ Setting for **{setting_key}** updated successfully!",
                reply_markup=types.InlineKeyboardMarkup([[
                    types.InlineKeyboardButton('« Back', callback_data=back_callback)
                ]])
            )

        # Start photo via URL
        elif action == 'start_photo':
            if message.text == '/remove':
                await clone_db.update_clone_setting(bot_id, 'start_photo', None)
                del user_states[user_id]
                return await message.reply(
                    "✅ Removed!",
                    reply_markup=types.InlineKeyboardMarkup([[
                        types.InlineKeyboardButton('« Back', callback_data=f'start_photo_{bot_id}')
                    ]])
                )
            if message.text.startswith('http'):
                await clone_db.update_clone_setting(bot_id, 'start_photo', message.text.strip())
                del user_states[user_id]
                return await message.reply(
                    "✅ Photo updated!",
                    reply_markup=types.InlineKeyboardMarkup([[
                        types.InlineKeyboardButton('« Back', callback_data=f'start_photo_{bot_id}')
                    ]])
                )
            return await message.reply("❌ Invalid URL! Send a valid http(s) link.")

        # Force Subscribe channels
        elif action == 'add_fsub_channel':
            channel_input = message.text.strip()
            
            # Using the new efficient function from clone_db.py
            await clone_db.add_to_list_setting(bot_id, 'force_sub_channels', channel_input)
            del user_states[user_id]

            return await message.reply(
                f"✅ Channel ` {channel_input} ` added to Force Subscribe list!\n\n⚠️ Make sure your clone bot is an admin there.",
                reply_markup=types.InlineKeyboardMarkup([[
                    types.InlineKeyboardButton('« Back to Channels', callback_data=f'fsub_manage_{bot_id}')
                ]])
            )

        # Auto Delete Time (1–720 minutes)
        elif action == 'autodel_time':
            try:
                time_minutes = int(message.text.strip())
                if time_minutes < 1:
                    return await message.reply("❌ Minimum 1 minute!")
                if time_minutes > 720:
                    return await message.reply("❌ Maximum 720 minutes (12 hours)!")
                await clone_db.update_clone_setting(bot_id, 'auto_delete_time', time_minutes * 60)
                del user_states[user_id]
                return await message.reply(
                    f"✅ Auto-delete time set to {time_minutes} minute(s)!",
                    reply_markup=types.InlineKeyboardMarkup([[
                        types.InlineKeyboardButton('« Back', callback_data=f'auto_delete_{bot_id}')
                    ]])
                )
            except ValueError:
                return await message.reply("❌ Please send a valid number!")

        # Add Admin (ID only for simplicity and reliability)
        elif action == 'add_admin':
            try:
                admin_id = int(message.text.strip())
                # Using the new efficient function
                await clone_db.add_to_list_setting(bot_id, 'admins', admin_id)
                del user_states[user_id]

                return await message.reply(
                    f"✅ Admin added successfully!\n<b>User ID:</b> <code>{admin_id}</code>",
                    reply_markup=types.InlineKeyboardMarkup([[
                        types.InlineKeyboardButton('« Back', callback_data=f'admins_{bot_id}')
                    ]])
                )
            except ValueError:
                return await message.reply("❌ Please send a valid User ID (number only).")
            except Exception as e:
                logger.error(f"Add admin error: {e}", exc_info=True)
                return await message.reply("❌ Failed to add admin! Make sure the ID is valid.")

        # File Size Limit (1–4096 MB)
        elif action == 'file_limit':
            try:
                limit = int(message.text.strip())
                if limit < 1:
                    return await message.reply("❌ Minimum 1MB!")
                if limit > 4096:
                    return await message.reply("❌ Maximum 4096MB (4GB)!")
                await clone_db.update_clone_setting(bot_id, 'file_size_limit', limit)
                del user_states[user_id]
                return await message.reply(
                    f"✅ File size limit set to {limit}MB!",
                    reply_markup=types.InlineKeyboardMarkup([[
                        types.InlineKeyboardButton('« Back', callback_data=f'files_{bot_id}')
                    ]])
                )
            except ValueError:
                return await message.reply("❌ Please send a valid number!")

    except Exception as e:
        logger.error(f"Input handler error: {e}", exc_info=True)
        if user_id in user_states:
            del user_states[user_id] # Clear state on error to prevent getting stuck
        await message.reply("❌ An unexpected error occurred! The action has been cancelled. Please try again.")


# Handle Photo Input
@Client.on_message(filters.private & filters.photo, group=2)
async def handle_photo_input(client, message: types.Message):
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
        "✅ Start photo updated successfully!",
        reply_markup=types.InlineKeyboardMarkup([[
            types.InlineKeyboardButton('« Back', callback_data=f'start_photo_{bot_id}')
        ]])
    )
