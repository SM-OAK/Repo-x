# plugins/clone_manager.py
import re
import os
import glob
import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# FIX: Handle ListenerTimeout import for different Pyrogram versions
try:
    from pyrogram.errors import ListenerTimeout
except ImportError:
    # Fallback for older versions or when pyrogramx is used
    class ListenerTimeout(Exception):
        """Custom timeout exception for compatibility"""
        pass

from config import CLONE_MODE, API_ID, API_HASH, ADMINS
from database.clone_db import clone_db
from Script import script

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Active clone clients {bot_id: Client}
active_clones = {}

# -----------------------------
# Main Clone Menu (callback: "clone")
# -----------------------------
@Client.on_callback_query(filters.regex("^clone$"))
async def clone_management_menu(client, query: CallbackQuery):
    if not CLONE_MODE:
        return await query.answer("Clone feature is disabled!", show_alert=True)

    user_id = query.from_user.id
    buttons = []
    
    # Get clones from DB (Admins see all, users see their own)
    clones = await clone_db.get_clones_by_user(user_id)
    if user_id in ADMINS:
        clones = await clone_db.get_all_clones()

    if not clones:
        reply_text = "✨ **No Clones Found**\n\nYou haven't created any clone bots yet. Use the button below to get started."
    else:
        reply_text = "✨ **Manage Clone's**\n\nYou can now manage and create your very own identical clone bot, mirroring all my awesome features, using the given buttons."
        for clone in clones:
            buttons.append(
                [InlineKeyboardButton(f"🤖 {clone['name']}", callback_data=f"customize_{clone['bot_id']}")]
            )

    buttons.append([InlineKeyboardButton('➕ Add Clone', callback_data='add_clone')])
    buttons.append([InlineKeyboardButton('🔙 Back', callback_data='start')])

    await query.message.edit_text(
        reply_text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# -----------------------------
# Customize Clone Menu
# -----------------------------
@Client.on_callback_query(filters.regex("^customize_"))
async def customize_clone(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    clone = await clone_db.get_clone(bot_id)

    if not clone:
        return await query.answer("Clone not found!", show_alert=True)
        
    if clone['user_id'] != query.from_user.id and query.from_user.id not in ADMINS:
        return await query.answer("This is not your bot!", show_alert=True)

    buttons = [
        [
            InlineKeyboardButton('📝 START MSG', callback_data=f'set_start_{bot_id}'),
            InlineKeyboardButton('🔒 FORCE SUB', callback_data=f'set_fsub_{bot_id}')
        ],
        [
            InlineKeyboardButton('🗑️ DELETE CLONE', callback_data=f'delete_clone_{bot_id}')
        ],
        [
            InlineKeyboardButton('🔙 Back to Clones', callback_data='clone')
        ]
    ]

    await query.message.edit_text(
        f"🛠️ **Customize Clone: {clone['name']}**\n\n"
        f"Configure your bot's settings using the buttons below.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# -----------------------------
# Core Clone Creation Logic (Reusable Function)
# -----------------------------
async def start_clone_process(client, chat_id, user_id, message_to_edit=None):
    """
    Core clone creation logic that can be called from both command and callback
    
    FIXED ISSUES:
    - ✅ Session naming now uses bot_id instead of bot_token (filesystem safe)
    - ✅ Timeout handling added for user input
    - ✅ Better token validation
    - ✅ Proper error handling
    """
    if not CLONE_MODE:
        text = "Clone feature is disabled!"
        if message_to_edit:
            return await message_to_edit.edit_text(text)
        return await client.send_message(chat_id, text)

    try:
        os.makedirs("clone_sessions", exist_ok=True)

        # Ask for token with timeout handling
        try:
            token_msg = await client.ask(
                chat_id,
                "<b>📝 Please forward the message from @BotFather that contains your bot token.</b>\n\n"
                "Use /cancel to stop this process.",
                timeout=300
            )
        except (ListenerTimeout, TimeoutError, asyncio.TimeoutError) as e:
            logger.info(f"User timeout: {e}")
            text = "⏱️ **Timeout!** You took too long to respond. Please try again."
            if message_to_edit:
                return await message_to_edit.edit_text(text)
            return await client.send_message(chat_id, text)
        except Exception as e:
            logger.error(f"Ask error: {e}")
            text = f"⚠️ **Error:** Unable to receive your message.\n\n<code>{e}</code>"
            if message_to_edit:
                return await message_to_edit.edit_text(text)
            return await client.send_message(chat_id, text)

        # Check for cancel
        if token_msg.text and token_msg.text.lower() == '/cancel':
            text = "❌ Process canceled!"
            if message_to_edit:
                return await message_to_edit.edit_text(text)
            return await client.send_message(chat_id, text)

        # Validate BotFather forward
        if not (token_msg.forward_from and token_msg.forward_from.id == 93372553):
            text = "❌ **Error:** This message was not forwarded from @BotFather.\n\nPlease forward the message containing your bot token and try again."
            if message_to_edit:
                return await message_to_edit.edit_text(text)
            return await client.send_message(chat_id, text)

        # Extract token with better validation
        try:
            tokens = re.findall(r'\d[0-9]{8,10}:[0-9A-Za-z_-]{35}', token_msg.text)
            if not tokens:
                text = "❌ **Invalid Token:** No valid bot token found in the message."
                if message_to_edit:
                    return await message_to_edit.edit_text(text)
                return await client.send_message(chat_id, text)
            bot_token = tokens[0]
        except Exception as e:
            logger.error(f"Token extraction error: {e}")
            text = f"❌ **Error:** Unable to extract token.\n\n<code>{e}</code>"
            if message_to_edit:
                return await message_to_edit.edit_text(text)
            return await client.send_message(chat_id, text)

        # Check if already cloned
        if await clone_db.get_clone_by_token(bot_token):
            text = "⚠️ **Already Cloned:** This bot has already been added as a clone."
            if message_to_edit:
                return await message_to_edit.edit_text(text)
            return await client.send_message(chat_id, text)

        # Show processing message
        if message_to_edit:
            msg = message_to_edit
            await msg.edit_text("⏳ Please wait, creating your clone bot...")
        else:
            msg = await client.send_message(chat_id, "⏳ Please wait, creating your clone bot...")

        try:
            # Create temporary client to get bot info
            temp_session = f"clone_sessions/temp_{user_id}"
            temp_client = Client(temp_session, API_ID, API_HASH, bot_token=bot_token)
            await temp_client.start()
            bot_info = await temp_client.get_me()
            await temp_client.stop()
            
            # Clean up temp session files
            temp_files = glob.glob(f"{temp_session}*")
            for file in temp_files:
                try:
                    os.remove(file)
                except:
                    pass

            # FIX: Use bot_id as session name (filesystem safe)
            session_name = f"clone_sessions/{bot_info.id}"
            clone_bot = Client(
                session_name, 
                API_ID, 
                API_HASH, 
                bot_token=bot_token, 
                plugins={"root": "clone_plugins"}
            )
            await clone_bot.start()

            # Add to database
            await clone_db.add_clone(
                bot_id=bot_info.id,
                user_id=user_id,
                bot_token=bot_token,
                username=bot_info.username,
                name=bot_info.first_name
            )

            # Add to active clones
            active_clones[bot_info.id] = clone_bot

            buttons = [
                [InlineKeyboardButton('🛠️ Customize Your Clone', callback_data=f'customize_{bot_info.id}')],
                [InlineKeyboardButton('🔙 Back to Clones', callback_data='clone')]
            ]
            await msg.edit_text(
                f"<b>✅ Clone Created Successfully!</b>\n\n"
                f"<b>🤖 Bot:</b> @{bot_info.username}\n"
                f"<b>📝 Name:</b> {bot_info.first_name}\n"
                f"<b>🆔 Bot ID:</b> <code>{bot_info.id}</code>",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        except Exception as e:
            logger.error(f"Clone creation error: {e}", exc_info=True)
            await msg.edit_text(f"⚠️ **An error occurred while creating the clone:**\n\n<code>{e}</code>")

    except Exception as e:
        logger.error(f"Clone process error: {e}", exc_info=True)
        text = f"⚠️ **Unexpected Error:**\n\n<code>{e}</code>"
        if message_to_edit:
            return await message_to_edit.edit_text(text)
        return await client.send_message(chat_id, text)

# -----------------------------
# Add Clone Button - Direct Process Start
# -----------------------------
@Client.on_callback_query(filters.regex("^add_clone$"))
async def add_clone_callback(client, query: CallbackQuery):
    """
    FIX: Seedha clone process start hota hai, manual command ki zarurat nahi
    
    FIXED: Direct clone creation process starts when button is clicked
    """
    await query.answer()
    
    # Delete old menu message
    try:
        await query.message.delete()
    except:
        pass
    
    # Start clone process directly
    await start_clone_process(client, query.message.chat.id, query.from_user.id)

# -----------------------------
# Clone Creation Command (/clone)
# -----------------------------
@Client.on_message(filters.command("clone") & filters.private)
async def clone_command(client, message):
    """
    FIX: Now uses the same core function as button callback
    """
    await start_clone_process(client, message.chat.id, message.from_user.id)

# -----------------------------
# Delete Clone
# -----------------------------
@Client.on_callback_query(filters.regex("^delete_clone_"))
async def delete_clone_button_callback(client, query: CallbackQuery):
    """
    FIXED ISSUES:
    - ✅ Proper error handling when stopping bot
    - ✅ Session files are now deleted from filesystem
    - ✅ Menu refreshes before showing alert
    """
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    
    if not clone:
        return await query.answer("Clone not found!", show_alert=True)

    user_id = query.from_user.id
    if clone['user_id'] != user_id and user_id not in ADMINS:
        return await query.answer("❌ This is not your clone!", show_alert=True)

    # Stop bot if running
    if bot_id in active_clones:
        try:
            await active_clones[bot_id].stop()
            logger.info(f"Stopped clone bot {bot_id}")
        except Exception as e:
            logger.error(f"Error stopping clone {bot_id}: {e}")
        finally:
            # FIX: Always remove from active_clones dict
            active_clones.pop(bot_id, None)

    # FIX: Delete session files from filesystem
    try:
        session_files = glob.glob(f"clone_sessions/{bot_id}*")
        for file in session_files:
            try:
                os.remove(file)
                logger.info(f"Deleted session file: {file}")
            except Exception as e:
                logger.error(f"Failed to delete session file {file}: {e}")
    except Exception as e:
        logger.error(f"Error cleaning up session files for bot {bot_id}: {e}")

    # Delete from database
    await clone_db.delete_clone_by_id(bot_id)
    
    # FIX: Refresh menu first, then show alert
    await clone_management_menu(client, query)
    await query.answer("✅ Clone deleted successfully!", show_alert=True)

# -----------------------------
# Restart all clones (on bot startup)
# -----------------------------
async def restart_bots():
    """
    FIXED ISSUES:
    - ✅ Session naming now consistent (uses bot_id)
    - ✅ Better error handling per clone
    - ✅ Continues even if one clone fails
    """
    if not CLONE_MODE:
        logger.info("Clone mode disabled")
        return

    os.makedirs("clone_sessions", exist_ok=True)
    clones = await clone_db.get_all_clones()
    logger.info(f"🔄 Found {len(clones)} clones in database")

    success_count = 0
    for clone in clones:
        bot_id = clone['bot_id']
        bot_token = clone['bot_token']
        username = clone.get('username', 'unknown')
        
        try:
            # FIX: Use bot_id as session name (consistent with creation)
            session_name = f"clone_sessions/{bot_id}"
            client = Client(
                session_name, 
                API_ID, 
                API_HASH, 
                bot_token=bot_token, 
                plugins={"root": "clone_plugins"}
            )
            await client.start()
            active_clones[bot_id] = client
            success_count += 1
            logger.info(f"✅ Restarted: @{username} (ID: {bot_id})")
        except Exception as e:
            logger.error(f"❌ Failed to restart @{username} (ID: {bot_id}): {e}")
            # Continue with next clone even if one fails

    logger.info(f"✅ Successfully restarted {success_count}/{len(clones)} clones")
