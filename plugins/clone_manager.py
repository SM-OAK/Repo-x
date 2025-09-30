import re
import logging
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    Message,
)
from pyrogram.errors import (
    AuthKeyUnregistered,

    UserDeactivated,
    UserDeactivatedBan
)
from config import CLONE_MODE, API_ID, API_HASH, ADMINS
from database.clone_db import clone_db

logger = logging.getLogger(__name__)

# In-memory dictionary to track user states.
# For multi-instance bots, consider using a database (e.g., Redis) for this.
user_states = {}

# --- Clone Management Callbacks ---

@Client.on_callback_query(filters.regex("^clone$"))
async def clone_callback(client: Client, query: CallbackQuery):
    """Displays the user's current clones and management options."""
    if not CLONE_MODE:
        return await query.answer("Cloning feature is currently disabled!", show_alert=True)

    user_clones = await clone_db.get_user_clones(query.from_user.id)
    buttons = []

    if user_clones:
        for clone in user_clones:
            buttons.append([
                InlineKeyboardButton(
                    f"🤖 {clone['name']} (@{clone['username']})",
                    callback_data=f"customize_{clone['bot_id']}"
                )
            ])
        reply_text = "✨ **Manage Your Clones**\n\nSelect a bot from the list below to customize its settings, or add a new one."
    else:
        reply_text = "✨ **No Clones Found**\n\nYou have not created any clone bots yet. Use the button below to get started."

    buttons.append([InlineKeyboardButton('➕ Add New Clone', callback_data='add_clone')])
    buttons.append([InlineKeyboardButton('🔙 Back', callback_data='start')])

    await query.message.edit_text(reply_text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^add_clone$"))
async def add_clone_callback(client: Client, query: CallbackQuery):
    """Initiates the process of adding a new clone."""
    user_id = query.from_user.id
    user_states[user_id] = "awaiting_token_for_add"

    await query.message.edit_text(
        "<b>➕ Add New Clone</b>\n\n"
        "1. Go to @BotFather and use <code>/newbot</code>.\n"
        "2. Give your bot a name and a unique username.\n"
        "3. **Forward the final message from BotFather containing the token to me.**\n\n"
        "Use the /cancel command to abort this process.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton('❌ Cancel', callback_data='cancel_clone_process')]]
        )
    )

# --- Token Handling for Add/Delete ---

@Client.on_message(filters.private & (filters.forwarded | filters.text))
async def token_handler(client: Client, message: Message):
    """Handles incoming messages to process tokens for adding or deleting clones."""
    user_id = message.from_user.id

    if user_id not in user_states:
        return

    state = user_states[user_id]

    if message.text and message.text.startswith("/"):
        if message.text == "/cancel":
            del user_states[user_id]
            return await message.reply(
                "✅ Process has been canceled.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton('🔙 Back to Clone Menu', callback_data='clone')
                ]])
            )
        return # Ignore other commands

    if state == "awaiting_token_for_add":
        await create_clone_from_token(client, message)
    elif state == "awaiting_token_for_delete":
        await delete_clone_from_token(client, message)

async def create_clone_from_token(client: Client, message: Message):
    """Validates a forwarded token and creates a clone."""
    user_id = message.from_user.id
    
    if not message.forward_from or message.forward_from.id != 93372553: # 93372553 is @BotFather's ID
        await message.reply("⚠️ **Invalid Forward!**\n\nPlease forward the message directly from @BotFather.",
                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ Cancel', callback_data='cancel_clone_process')]]))
        return

    bot_token_match = re.search(r"(\d{8,10}:[a-zA-Z0-9_-]{35})", message.text)
    if not bot_token_match:
        await message.reply("⚠️ **Invalid Token!**\n\nThe forwarded message does not contain a valid bot token.",
                            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('❌ Cancel', callback_data='cancel_clone_process')]]))
        return
        
    bot_token = bot_token_match.group(1)
    
    # Clear the state
    if user_id in user_states:
        del user_states[user_id]

    msg = await message.reply("⏳ Verifying token and creating your clone...")

    try:
        clone_client = Client(
            name=f"clone_{user_id}_{bot_token[:8]}", # Unique session name
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=bot_token,
            in_memory=True, # Use in-memory session to avoid creating session files
            plugins={"root": "plugins/clone_plugins"} # Assuming clone plugins are here
        )
        await clone_client.start()
        bot_info = await clone_client.get_me()
        
        # Stop the client after getting info. The main bot will manage starting/stopping.
        await clone_client.stop()

        await clone_db.add_clone(
            bot_id=bot_info.id,
            user_id=user_id,
            bot_token=bot_token,
            username=bot_info.username,
            name=bot_info.first_name
        )

        buttons = [
            [InlineKeyboardButton('📝 Customize Clone', callback_data=f'customize_{bot_info.id}')],
            [InlineKeyboardButton('🔙 Back to Clones', callback_data='clone')]
        ]
        await msg.edit_text(
            f"✅ **Successfully Cloned!**\n\n🤖 **Bot:** @{bot_info.username}",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except (AuthKeyUnregistered, UserDeactivated, UserDeactivatedBan):
        await msg.edit_text("⚠️ **Error:** The provided bot token has been revoked. Please generate a new one from @BotFather.")
    except Exception as e:
        logger.error(f"Clone creation error: {e}", exc_info=True)
        await msg.edit_text(f"⚠️ **An unexpected error occurred:**\n\n`{e}`\n\nPlease try again later.")

# --- Deletion and Cancellation ---

@Client.on_message(filters.command("deleteclone") & filters.private)
async def delete_clone_command(client: Client, message: Message):
    """Initiates the process to delete a clone."""
    if not CLONE_MODE:
        return await message.reply("Cloning feature is currently disabled!")
        
    user_id = message.from_user.id
    user_states[user_id] = "awaiting_token_for_delete"
    
    await message.reply(
        "🗑️ **Delete Clone**\n\n"
        "Please send the bot token of the clone you wish to delete.\n\n"
        "Use /cancel to abort this process.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton('❌ Cancel', callback_data='cancel_clone_process')]]
        )
    )

async def delete_clone_from_token(client: Client, message: Message):
    """Finds a clone by token and deletes it from the database."""
    user_id = message.from_user.id
    bot_token_match = re.search(r"(\d{8,10}:[a-zA-Z0-9_-]{35})", message.text)

    if not bot_token_match:
        await message.reply("That doesn't look like a valid token. Please try again or /cancel.")
        return

    bot_token = bot_token_match.group(1)

    # Clear state
    if user_id in user_states:
        del user_states[user_id]

    clone = await clone_db.get_clone_by_token(bot_token)
    
    # Ensure the user owns the clone or is an admin
    if not clone or (clone['user_id'] != user_id and user_id not in ADMINS):
        return await message.reply("❌ **Clone Not Found!**\n\nI couldn't find a clone with that token associated with your account.")

    # IMPORTANT: To fully stop a running clone, you need to manage the active
    # Client instances. This part of the logic depends on how your main bot
    # starts and stores clone sessions (e.g., in a global dictionary).
    # Example:
    # if clone['bot_id'] in running_clones:
    #     await running_clones[clone['bot_id']].stop()
    #     del running_clones[clone['bot_id']]
    
    await clone_db.delete_clone(bot_token)
    await message.reply(f"✅ **Clone Deleted!**\n\nThe bot @{clone['username']} has been successfully removed from my database.")

@Client.on_callback_query(filters.regex("^cancel_clone_process$"))
async def cancel_clone_process(client: Client, query: CallbackQuery):
    """Callback to cancel any ongoing clone operation."""
    user_id = query.from_user.id
    if user_id in user_states:
        del user_states[user_id]
    
    await query.message.edit_text(
        "✅ Process has been canceled.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('🔙 Back to Clone Menu', callback_data='clone')
        ]])
    )
