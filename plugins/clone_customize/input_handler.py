# plugins/clone_customize/input_handler.py
from pyrogram import Client, filters, types
from database.clone_db import clone_db
import logging

logger = logging.getLogger(__name__)

# Yeh user_states dictionary ab yahan centrally manage hogi.
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

        elif action == 'add_fsub':
            clone = await clone_db.get_clone(bot_id)
            channels = clone.get('settings', {}).get('force_sub_channels', [])
            if len(channels) >= 6: return await message.reply("❌ Max 6 channels!")
            channel = message.text.strip()
            if channel not in channels:
                channels.append(channel)
                await clone_db.update_clone_setting(bot_id, 'force_sub_channels', channels)
                del user_states[user_id]
                await message.reply(f"✅ Added: {channel}", reply_markup=types.InlineKeyboardMarkup([[
                    types.InlineKeyboardButton('« Back', callback_data=f'fsub_manage_{bot_id}')
                ]]))
            else:
                await message.reply("❌ Already exists!")

        elif action == 'autodel_time':
            time_sec = int(message.text)
            if time_sec < 20: return await message.reply("❌ Min 20 seconds!")
            await clone_db.update_clone_setting(bot_id, 'auto_delete_time', time_sec)
            del user_states[user_id]
            await message.reply(f"✅ Time set to {time_sec}s!", reply_markup=types.InlineKeyboardMarkup([[
                types.InlineKeyboardButton('« Back', callback_data=f'auto_delete_{bot_id}')
            ]]))

        elif action == 'add_admin':
            admin_id = int(message.text)
            clone = await clone_db.get_clone(bot_id)
            admins = clone.get('settings', {}).get('admins', [])
            if admin_id not in admins:
                admins.append(admin_id)
                await clone_db.update_clone_setting(bot_id, 'admins', admins)
                del user_states[user_id]
                await message.reply(f"✅ Admin added: {admin_id}", reply_markup=types.InlineKeyboardMarkup([[
                    types.InlineKeyboardButton('« Back', callback_data=f'admins_{bot_id}')
                ]]))
            else:
                await message.reply("❌ Already admin!")
        
        elif action == 'file_limit':
            limit = int(message.text)
            await clone_db.update_clone_setting(bot_id, 'file_size_limit', limit)
            del user_states[user_id]
            await message.reply(f"✅ Limit set to {limit}MB!", reply_markup=types.InlineKeyboardMarkup([[
                types.InlineKeyboardButton('« Back', callback_data=f'files_{bot_id}')
            ]]))

    except ValueError:
        await message.reply("❌ Invalid input!")
    except Exception as e:
        logger.error(f"Error handling input: {e}")
        await message.reply(f"❌ Error: {str(e)}")


@Client.on_message(filters.private & filters.photo, group=2)
async def handle_photo_input(client, message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_states: return
    state = user_states[user_id]
    if state['action'] != 'start_photo': return
    
    bot_id = state['bot_id']
    photo_id = message.photo.file_id
    
    await clone_db.update_clone_setting(bot_id, 'start_photo', photo_id)
    del user_states[user_id]
    await message.reply("✅ Photo updated!", reply_markup=types.InlineKeyboardMarkup([[
        types.InlineKeyboardButton('« Back', callback_data=f'start_photo_{bot_id}')
    ]]))
