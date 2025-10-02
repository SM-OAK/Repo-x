# plugins/clone_customize/input_handler.py
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import UserNotParticipant
from database.clone_db import clone_db

# This dictionary stores what action we are expecting from a user.
# It should be imported by other files that need to set a state.
user_states = {}

@Client.on_message(filters.private & ~filters.command(["start", "cancel"]) & filters.text)
async def handle_user_input(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return  # Not waiting for any input from this user.

    state = user_states.pop(user_id)  # Get state and remove it to prevent re-triggering
    action = state.get('action')
    bot_id = state.get('bot_id')
    
    # --- Handler for adding Force Subscribe channel ---
    if action == 'add_fsub_channel':
        channel_input = message.text.strip()
        
        try:
            # Try to convert to int for ID check, otherwise treat as username
            channel_identifier = int(channel_input) if channel_input.startswith('-100') else channel_input
        except ValueError:
            await message.reply_text("❌ **Invalid ID Format**\nChannel IDs must be numbers starting with -100.")
            return

        try:
            # Check if the channel is accessible
            chat = await client.get_chat(channel_identifier)
            
            # Check if the bot is an admin in the channel
            member = await chat.get_member(client.me.id)
            if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                 await message.reply_text(f"❌ **Bot is Not Admin**\nI am not an administrator in '{chat.title}'. Please make me an admin and try again.")
                 return

        except Exception as e:
            await message.reply_text(f"❌ **Error Accessing Channel**\nCould not access `{channel_input}`.\n\n"
                                     f"Please ensure the username/ID is correct and that I am a member of the channel.\n`Error: {e}`")
            return

        clone = await clone_db.get_clone(bot_id)
        channels = clone.get('settings', {}).get('force_sub_channels', [])
        
        if len(channels) >= 6:
            await message.reply_text("❌ **Limit Reached**\nYou have already added the maximum of 6 channels.")
            return
        
        if chat.id in channels:
            await message.reply_text(f"⚠️ **Already Added**\nThe channel '{chat.title}' is already in your list.")
            return

        channels.append(chat.id)  # Store the integer ID for reliability
        await clone_db.update_clone_setting(bot_id, 'force_sub_channels', channels)
        await message.reply_text(f"✅ **Channel Added!**\nSuccessfully added '{chat.title}'.\n\nYou can go back to the menu to see the change or add another channel.")

    # --- Handler for setting auto-delete time ---
    elif action == 'autodel_time':
        try:
            minutes = int(message.text.strip())
            if not (1 <= minutes <= 100): raise ValueError
            seconds = minutes * 60
            await clone_db.update_clone_setting(bot_id, 'auto_delete_time', seconds)
            await message.reply_text(f"✅ **Time Set**\nAuto-delete time has been set to {minutes} minutes.")
        except ValueError:
            await message.reply_text("❌ **Invalid Input**\nPlease send a number between 1 and 100.")
    
    # --- Handlers for verification settings ---
    elif action == 'shortlink_api':
        await clone_db.update_clone_setting(bot_id, 'shortlink_api', message.text.strip())
        await message.reply_text("✅ **API Key Set**")
        
    elif action == 'shortlink_url':
        url = message.text.strip()
        if not url.startswith("http"): url = "https://" + url
        await clone_db.update_clone_setting(bot_id, 'shortlink_url', url)
        await message.reply_text("✅ **URL Set**")
        
    elif action == 'tutorial_link':
        await clone_db.update_clone_setting(bot_id, 'tutorial_link', message.text.strip())
        await message.reply_text("✅ **Tutorial Link Set**")
