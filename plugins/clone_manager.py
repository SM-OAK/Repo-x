# In plugins/clone_manager.py

import re
import os
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import CLONE_MODE, API_ID, API_HASH, ADMINS
from database.clone_db import clone_db

logger = logging.getLogger(__name__)

# This dictionary will hold all active clone clients.
active_clones = {}

# --- NEW, SIMPLIFIED WORKFLOW ---

# 1. The user forwards a message. This handler checks if it's the token from BotFather.
@Client.on_message(filters.private & filters.forwarded)
async def handle_clone_token(client, message: Message):
    if not CLONE_MODE:
        return

    # Check if the forwarded message is from BotFather
    if not (message.forward_from and message.forward_from.id == 93372553):
        return await message.reply('To create a clone, please forward the token message you get from @BotFather.')

    # Extract the token from the message text
    try:
        bot_token = re.findall(r'(\d[0-9]{8,10}:[0-9A-Za-z_-]{35})', message.text)[0]
    except IndexError:
        return await message.reply('This does not look like a valid bot token message. Please try again.')

    # Check if this token is already in our database
    if await clone_db.get_clone_by_token(bot_token):
        return await message.reply('⚠️ This bot has already been cloned.')
    
    # Show a "Creating..." message
    msg = await message.reply_text("⏳ Creating your clone bot, please wait...")

    try:
        # Define the session name for the new clone
        session_name = f"clone_sessions/clone_{bot_token[:10]}"
        
        # Create a new Pyrogram client for the clone
        clone_bot = Client(
            name=session_name,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=bot_token,
            plugins={"root": "clone_plugins"}
        )

        # Start the clone bot
        await clone_bot.start()
        bot_info = await clone_bot.get_me()

        # Add the clone's details to the database
        await clone_db.add_clone(
            bot_id=bot_info.id,
            user_id=message.from_user.id,
            bot_token=bot_token,
            username=bot_info.username,
            name=bot_info.first_name
        )

        # Keep the new client running in our active clones dictionary
        active_clones[bot_info.id] = clone_bot

        # Send a success message
        await msg.edit_text(
            f"<b>✅ Successfully Cloned!</b>\n\n"
            f"<b>🤖 Bot:</b> @{bot_info.username}\n"
            f"<b>📝 Name:</b> {bot_info.first_name}\n\n"
            "You can now customize your bot using the main bot's interface.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton('⚙️ Customize Your Clone', callback_data=f'customize_{bot_info.id}')]]
            )
        )

    except Exception as e:
        logger.error(f"Clone creation error: {e}", exc_info=True)
        await msg.edit_text(f"⚠️ **An error occurred:**\n\n`{e}`\n\nPlease check your logs or contact support.")

# 2. Update the /start and help messages to give the new instructions
@Client.on_callback_query(filters.regex("^clone$"))
async def clone_callback(client, query: CallbackQuery):
    if not CLONE_MODE:
        return await query.answer("Clone feature is disabled!", show_alert=True)
    
    # New text to guide the user
    clone_instructions = (
        "<b>🤖 Create Your Own Clone Bot</b>\n\n"
        "1. Go to @BotFather and use the `/newbot` command.\n"
        "2. Follow the steps to create your new bot.\n"
        "3. @BotFather will give you a token. **Forward that entire message to me here.**\n\n"
        "I will automatically create your clone."
    )
    
    await query.message.edit_text(
        clone_instructions,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton('🔙 Back', callback_data='start')]]
        )
    )

# --- The restart function remains the same ---
async def restart_bots():
    if not CLONE_MODE:
        logger.info("Clone mode is disabled.")
        return
    
    try:
        os.makedirs("clone_sessions", exist_ok=True)
        clones = await clone_db.get_all_clones()
        if not clones:
            logger.info("No clones found in the database to restart.")
            return

        logger.info(f"🔄 Found {len(clones)} clones in database to restart.")
        
        for clone in clones:
            try:
                bot_id = clone['bot_id']
                bot_token = clone['bot_token']
                
                logger.info(f"Starting clone @{clone.get('username', bot_id)}...")
                
                client = Client(
                    f"clone_sessions/clone_{bot_token[:10]}",
                    API_ID, 
                    API_HASH,
                    bot_token=bot_token,
                    plugins={"root": "clone_plugins"}
                )
                
                await client.start()
                active_clones[bot_id] = client
                logger.info(f"✅ Restarted: @{clone['username']}")
                
            except Exception as e:
                logger.error(f"❌ Failed to restart clone @{clone.get('username', 'unknown')}: {e}")
                continue
        
        logger.info(f"✅ Successfully restarted {len(active_clones)} clones.")
        
    except Exception as e:
        logger.error(f"Error in restart_bots: {e}", exc_info=True)

