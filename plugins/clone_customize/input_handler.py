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
    
    if message.text == '/cancel':
        del user_states[user_id]
        return await message.reply("❌ Cancelled!", reply_markup=types.InlineKeyboardMarkup([[
            types.InlineKeyboardButton('« Back to Main Menu', callback_data=f'customize_{bot_id}')
        ]]))
    
    try:
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

        if action in action_map:
            setting_key, back_callback = action_map[action]
            await clone_db.update_clone_setting(bot_id, setting_key, message.text)
            del user_states[user_id]
            await message.reply(f"✅ Setting for `{action}` updated!", reply_markup=types.InlineKeyboardMarkup([[
                types.InlineKeyboardButton('« Back', callback_data=back_callback)
            ]]))

        elif action == 'start_photo':
            if message.text == '/remove':
                await clone_db.update_clone_setting(bot_id, 'start_photo', None)
                del user_states[user_id]
                return await message.reply("✅ Removed!", reply_markup=types.InlineKeyboardMarkup([[
                    types.InlineKeyboardButton('« Back', callback_data=f'start_photo_{bot_id}')
                ]]))
            
            if message.text.startswith('http'):
                await clone_db.update_clone_setting(bot_id, 'start_photo', message.text)
                del user_states[user_id]
                await message.reply("✅ Photo updated!", reply_markup=types.InlineKeyboardMarkup([[
                    types.InlineKeyboardButton('« Back', callback_data=f'start_photo_{bot_id}')
                ]]))
            else:
                await message.reply("❌ Invalid URL!")

        elif action == 'add_fsub_channel':  # FIXED: Changed from 'add_fsub' to match security.py
            clone = await clone_db.get_clone(bot_id)
            channels = clone.get('settings', {}).get('force_sub_channels', [])
            
            if len(channels) >= 6:
                return await message.reply("❌ Maximum 6 channels allowed!", reply_markup=types.InlineKeyboardMarkup([[
                    types.InlineKeyboardButton('« Back', callback_data=f'fsub_manage_{bot_id}')
                ]]))
            
            channel_input = message.text.strip()
            
            # Validate channel
            try:
                # Try to get channel info to validate
                if channel_input.startswith('@'):
                    chat = await client.get_chat(channel_input)
                elif channel_input.startswith('-100') or channel_input.lstrip('-').isdigit():
                    chat = await client.get_chat(int(channel_input))
                else:
                    return await message.reply(
                        "❌ Invalid format!\n\n"
                        "Send either:\n"
                        "• Channel username: <code>@channelname</code>\n"
                        "• Channel ID: <code>-100123456789</code>",
                        reply_markup=types.InlineKeyboardMarkup([[
                            types.InlineKeyboardButton('« Back', callback_data=f'fsub_manage_{bot_id}')
                        ]])
                    )
                
                # Check if channel is already added
                channel_identifier = str(chat.id)
                if channel_identifier in channels or chat.username in [c.replace('@', '') for c in channels if c.startswith('@')]:
                    return await message.reply(
                        "❌ This channel is already added!",
                        reply_markup=types.InlineKeyboardMarkup([[
                            types.InlineKeyboardButton('« Back', callback_data=f'fsub_manage_{bot_id}')
                        ]])
                    )
                
                # Check if bot is admin in the channel
                try:
                    bot_member = await client.get_chat_member(chat.id, (await client.get_me()).id)
                    if bot_member.status not in ['administrator', 'creator']:
                        return await message.reply(
                            f"❌ I'm not an admin in <b>{chat.title}</b>!\n\n"
                            "Please add me as administrator first.",
                            reply_markup=types.InlineKeyboardMarkup([[
                                types.InlineKeyboardButton('« Back', callback_data=f'fsub_manage_{bot_id}')
                            ]])
                        )
                except Exception as e:
                    return await message.reply(
                        f"❌ Cannot verify admin status!\n\n"
                        f"Error: {str(e)}",
                        reply_markup=types.InlineKeyboardMarkup([[
                            types.InlineKeyboardButton('« Back', callback_data=f'fsub_manage_{bot_id}')
                        ]])
                    )
                
                # Add channel ID (not username) for consistency
                channels.append(channel_identifier)
                await clone_db.update_clone_setting(bot_id, 'force_sub_channels', channels)
                del user_states[user_id]
                
                await message.reply(
                    f"✅ Successfully added!\n\n"
                    f"<b>Channel:</b> {chat.title}\n"
                    f"<b>ID:</b> <code>{chat.id}</code>",
                    reply_markup=types.InlineKeyboardMarkup([[
                        types.InlineKeyboardButton('« Back to Channels', callback_data=f'fsub_manage_{bot_id}')
                    ]])
                )
                
            except (PeerIdInvalid, ChannelInvalid, UsernameInvalid):
                await message.reply(
                    "❌ Invalid channel!\n\n"
                    "Make sure:\n"
                    "• The channel exists\n"
                    "• I have access to it\n"
                    "• The format is correct",
                    reply_markup=types.InlineKeyboardMarkup([[
                        types.InlineKeyboardButton('« Back', callback_data=f'fsub_manage_{bot_id}')
                    ]])
                )
            except ValueError:
                await message.reply(
                    "❌ Invalid channel ID format!",
                    reply_markup=types.InlineKeyboardMarkup([[
                        types.InlineKeyboardButton('« Back', callback_data=f'fsub_manage_{bot_id}')
                    ]])
                )
            except Exception as e:
                logger.error(f"Error adding force sub channel: {e}")
                await message.reply(
                    f"❌ Error: {str(e)}",
                    reply_markup=types.InlineKeyboardMarkup([[
                        types.InlineKeyboardButton('« Back', callback_data=f'fsub_manage_{bot_id}')
                    ]])
                )

        elif action == 'autodel_time':
            try:
                time_minutes = int(message.text)
                if time_minutes < 1:
                    return await message.reply("❌ Minimum 1 minute!")
                if time_minutes > 100:
                    return await message.reply("❌ Maximum 100 minutes!")
                
                time_sec = time_minutes * 60
                await clone_db.update_clone_setting(bot_id, 'auto_delete_time', time_sec)
                del user_states[user_id]
                await message.reply(
                    f"✅ Auto-delete time set to {time_minutes} minute(s)!",
                    reply_markup=types.InlineKeyboardMarkup([[
                        types.InlineKeyboardButton('« Back', callback_data=f'auto_delete_{bot_id}')
                    ]])
                )
            except ValueError:
                await message.reply("❌ Please send a valid number!")

        elif action == 'add_admin':
            try:
                admin_id = int(message.text)
                clone = await clone_db.get_clone(bot_id)
                admins = clone.get('settings', {}).get('admins', [])
                
                if admin_id in admins:
                    return await message.reply("❌ Already an admin!")
                
                admins.append(admin_id)
                await clone_db.update_clone_setting(bot_id, 'admins', admins)
                del user_states[user_id]
                
                await message.reply(
                    f"✅ Admin added successfully!\n\n"
                    f"<b>User ID:</b> <code>{admin_id}</code>",
                    reply_markup=types.InlineKeyboardMarkup([[
                        types.InlineKeyboardButton('« Back', callback_data=f'admins_{bot_id}')
                    ]])
                )
            except ValueError:
                await message.reply("❌ Invalid user ID! Please send a numeric ID.")
        
        elif action == 'file_limit':
            try:
                limit = int(message.text)
                if limit < 1:
                    return await message.reply("❌ Minimum 1MB!")
                if limit > 2000:
                    return await message.reply("❌ Maximum 2000MB!")
                
                await clone_db.update_clone_setting(bot_id, 'file_size_limit', limit)
                del user_states[user_id]
                await message.reply(
                    f"✅ File size limit set to {limit}MB!",
                    reply_markup=types.InlineKeyboardMarkup([[
                        types.InlineKeyboardButton('« Back', callback_data=f'files_{bot_id}')
                    ]])
                )
            except ValueError:
                await message.reply("❌ Please send a valid number!")

    except ValueError:
        await message.reply("❌ Invalid input! Please try again.")
    except Exception as e:
        logger.error(f"Error handling input: {e}")
        await message.reply(f"❌ Error: {str(e)}")


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
