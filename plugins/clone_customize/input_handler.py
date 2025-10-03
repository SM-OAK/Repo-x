# plugins/clone_customize/input_handler.py
from pyrogram import Client, filters, types
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
        await message.reply("❌ Operation Cancelled.")
        return
    
    try:
        # --- FORCE SUBSCRIBE CHANNEL ADD LOGIC ---
        if action == 'add_fsub_channel':
            clone = await clone_db.get_clone(bot_id)
            channels = clone.get('settings', {}).get('force_sub_channels', [])

            if len(channels) >= 6:
                await message.reply("❌ Maximum 6 channels allowed.")
                del user_states[user_id]
                return

            channel_input = message.text.strip()
            
            # Simple format validation
            try:
                # If it's a numeric ID, store it as an integer
                channel_id = int(channel_input)
            except ValueError:
                # Otherwise, assume it's a username and store as a string
                if not channel_input.startswith('@'):
                    await message.reply("❌ Invalid format. Username must start with '@'.")
                    return
                channel_id = channel_input

            # Check if channel is already in the list
            if channel_id in channels:
                await message.reply("❌ This channel has already been added.")
                del user_states[user_id]
                return

            channels.append(channel_id)
            await clone_db.update_clone_setting(bot_id, 'force_sub_channels', channels)
            del user_states[user_id]

            await message.reply(
                f"✅ Successfully saved channel: <code>{channel_id}</code>\n\n"
                f"⚠️ **IMPORTANT:** I did not check this channel. You MUST ensure the ID/username is correct and that your **clone bot** is an admin there.",
                reply_markup=types.InlineKeyboardMarkup([[
                    types.InlineKeyboardButton('« Back to Channels', callback_data=f'fsub_manage_{bot_id}')
                ]])
            )
            return
            
        # --- OTHER SETTINGS ---
        # (The rest of your input handling logic)
        
        action_map = {
            'start_text': ('start_message', f'start_text_{bot_id}'),
            # ... add other actions here if needed
        }

        if action in action_map:
            setting_key, back_callback = action_map[action]
            await clone_db.update_clone_setting(bot_id, setting_key, message.text.strip())
            del user_states[user_id]
            await message.reply(
                f"✅ Setting updated!",
                reply_markup=types.InlineKeyboardMarkup([[
                    types.InlineKeyboardButton('« Back', callback_data=back_callback)
                ]])
            )

    except Exception as e:
        logger.error(f"Input handler error: {e}", exc_info=True)
        await message.reply("❌ A critical error occurred.")
        if user_id in user_states:
            del user_states[user_id]

# (Keep the handle_photo_input function if you use it)
