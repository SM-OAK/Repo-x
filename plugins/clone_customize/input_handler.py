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
        return await message.reply(
            "❌ Cancelled!",
            reply_markup=types.InlineKeyboardMarkup([[
                types.InlineKeyboardButton('« Back to Main Menu', callback_data=f'customize_{bot_id}')
            ]])
        )
    
    try:
        # Map simple text actions
        action_map = {
            'start_text': ('start_message', f'start_text_{bot_id}'),
            'start_button': ('start_button', f'start_button_{bot_id}'),
            'file_caption': ('file_caption', f'file_caption_{bot_id}'),
            'shortlink_api': ('shortlink_api', f'verification_{bot_id}'),
            'shortlink_url': ('shortlink_url', f'verification_{bot_id}'),
            'tutorial_link': ('tutorial_link', f'verification_{bot_id}'),
            'mongo_db': ('mongo_db', f'mongo_db_{bot_id}'),
            'log_channel': ('log_channel', f'log_channel_{bot_id}'),
            'db_channel': ('db_channel', f'db_channel_{bot_id}'),
        }

        # Simple text input handling
        if action in action_map:
            setting_key, back_callback = action_map[action]
            await clone_db.update_clone_setting(bot_id, setting_key, message.text.strip())
            del user_states[user_id]
            return await message.reply(
                f"✅ Setting for `{action}` updated!",
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
            del user_states[user_id]
            return await message.reply("❌ Invalid URL! Send a valid http(s) link.")

        # Force Subscribe channels
        elif action == 'add_fsub_channel':
            # FIX: Moved the import here to prevent a circular dependency
            from .security import verify_clone_bot_admin

            clone = await clone_db.get_clone(bot_id)
            channels = clone.get('settings', {}).get('force_sub_channels', [])

            if len(channels) >= 6:
                del user_states[user_id]
                return await message.reply(
                    "❌ Maximum 6 channels allowed!",
                    reply_markup=types.InlineKeyboardMarkup([[
                        types.InlineKeyboardButton('« Back', callback_data=f'fsub_manage_{bot_id}')
                    ]])
                )

            channel_input = message.text.strip()
            try:
                chat = await client.get_chat(channel_input)

                if chat.id in channels:
                    del user_states[user_id]
                    return await message.reply(
                        "❌ This channel is already added!",
                        reply_markup=types.InlineKeyboardMarkup([[
                            types.InlineKeyboardButton('« Back', callback_data=f'fsub_manage_{bot_id}')
                        ]])
                    )
                
                clone_bot_token = clone.get('bot_token')
                if not clone_bot_token:
                    del user_states[user_id]
                    return await message.reply("❌ Clone Bot Token not found. Cannot verify permissions.")

                is_admin = await verify_clone_bot_admin(
                    clone_bot_token,
                    chat.id,
                    client.api_id,
                    client.api_hash
                )

                if not is_admin:
                    del user_states[user_id]
                    return await message.reply(
                        f"❌ The **clone bot** is not an admin in <b>{chat.title}</b>!\n\nPlease add the clone bot as an administrator with 'Add Members' permission first.",
                        reply_markup=types.InlineKeyboardMarkup([[
                            types.InlineKeyboardButton('« Back', callback_data=f'fsub_manage_{bot_id}')
                        ]])
                    )

                channels.append(chat.id)
                await clone_db.update_clone_setting(bot_id, 'force_sub_channels', channels)
                del user_states[user_id]

                return await message.reply(
                    f"✅ Successfully added!\n\n<b>Channel:</b> {chat.title}\n<b>ID:</b> <code>{chat.id}</code>",
                    reply_markup=types.InlineKeyboardMarkup([[
                        types.InlineKeyboardButton('« Back to Channels', callback_data=f'fsub_manage_{bot_id}')
                    ]])
                )

            except (PeerIdInvalid, ChannelInvalid, UsernameInvalid):
                del user_states[user_id]
                return await message.reply(
                    "❌ Invalid channel!! Please check the username/ID and make sure the **main bot** (Repo Bot) has been added to the channel (it doesn't need admin rights, it just needs to be a member to see the channel's info).",
                    reply_markup=types.InlineKeyboardMarkup([[
                        types.InlineKeyboardButton('« Back', callback_data=f'fsub_manage_{bot_id}')
                    ]])
                )
            except Exception as e:
                del user_states[user_id]
                logger.error(f"ForceSub add error: {e}", exc_info=True)
                return await message.reply("❌ An unexpected error occurred while adding the channel.")

        # Auto Delete Time
        elif action == 'autodel_time':
            try:
                time_minutes = int(message.text.strip())
                if not 1 <= time_minutes <= 100:
                    del user_states[user_id]
                    return await message.reply("❌ Time must be between 1 and 100 minutes!")
                
                await clone_db.update_clone_setting(bot_id, 'auto_delete_time', time_minutes * 60)
                del user_states[user_id]
                return await message.reply(
                    f"✅ Auto-delete time set to {time_minutes} minute(s)!",
                    reply_markup=types.InlineKeyboardMarkup([[
                        types.InlineKeyboardButton('« Back', callback_data=f'auto_delete_{bot_id}')
                    ]])
                )
            except ValueError:
                del user_states[user_id]
                return await message.reply("❌ Please send a valid number!")

        # Add Admin (ID or @username)
        elif action == 'add_admin':
            try:
                if message.text.strip().startswith("@"):
                    user = await client.get_users(message.text.strip())
                    admin_id = user.id
                else:
                    admin_id = int(message.text.strip())

                clone = await clone_db.get_clone(bot_id)
                admins = clone.get('settings', {}).get('admins', [])

                if admin_id in admins:
                    del user_states[user_id]
                    return await message.reply("❌ Already an admin!")

                admins.append(admin_id)
                await clone_db.update_clone_setting(bot_id, 'admins', admins)
                del user_states[user_id]

                return await message.reply(
                    f"✅ Admin added successfully!\n<b>User ID:</b> <code>{admin_id}</code>",
                    reply_markup=types.InlineKeyboardMarkup([[
                        types.InlineKeyboardButton('« Back', callback_data=f'admins_{bot_id}')
                    ]])
                )
            except Exception as e:
                del user_states[user_id]
                logger.error(f"Add admin error: {e}", exc_info=True)
                return await message.reply("❌ Failed to add admin! Make sure the ID/username is valid.")
        
    except Exception as e:
        logger.error(f"Input handler error: {e}", exc_info=True)
        if user_id in user_states:
            del user_states[user_id]
        await message.reply("❌ A critical error occurred. The operation has been cancelled.")


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
