# plugins/power.py - Corrected and integrated
# This is your dedicated admin control panel.

import config
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import TimeoutError as PyrogramTimeoutError # Renamed to avoid conflict
from pymongo import MongoClient

# Connect to the database that stores clone information
mongo_client = MongoClient(config.DB_URI)
mongo_db = mongo_client["cloned_vjbotz"]
bots_collection = mongo_db["bots"]

# --- NEW HELPER FUNCTION to replace client.ask ---
# This function safely waits for a user's response.
async def ask_for_input(client, chat_id, text, timeout=300):
    message = await client.send_message(chat_id, text)
    try:
        response = await client.listen(chat_id=chat_id, user_id=chat_id, timeout=timeout)
        if response:
            await response.delete() # Clean up user's response message
            return response
    except PyrogramTimeoutError:
        return None
    finally:
        await message.delete() # Clean up the bot's question message


# --- Helper functions to build the different menus ---

async def build_main_panel():
    """Builds the main admin panel menu."""
    buttons = [
        [InlineKeyboardButton(f"Main Bot Link Sharing: {'🟢 ON' if config.LINK_GENERATION_MODE else '🔴 OFF'}", callback_data="toggle_links")],
        [InlineKeyboardButton(f"Bot Public Mode: {'🌍 Public' if config.PUBLIC_FILE_STORE else '🔒 Private'}", callback_data="toggle_public")],
        [InlineKeyboardButton("🤖 Manage Clones", callback_data="manage_clones_menu")],
        [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="start")]
    ]
    return InlineKeyboardMarkup(buttons)

async def build_clones_list_menu(admin_id):
    """Builds the menu that lists all cloned bots."""
    buttons = []
    # Use sort to ensure consistent order
    cloned_bots = bots_collection.find({"user_id": admin_id}).sort("name", 1)
    for bot in cloned_bots:
        buttons.append([InlineKeyboardButton(f"{bot['name']} (@{bot['username']})", callback_data=f"clone_settings_{bot['bot_id']}")])
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="admin_panel")])
    return InlineKeyboardMarkup(buttons)

async def build_clone_settings_menu(bot_id):
    """Builds the settings menu for a specific clone."""
    buttons = [
        [InlineKeyboardButton("✏️ Set Start Msg", callback_data=f"set_start_msg_{bot_id}")],
        [InlineKeyboardButton("🗑️ Auto-Delete Settings", callback_data=f"set_auto_del_{bot_id}")],
        [InlineKeyboardButton("⬅️ Back to Clones List", callback_data="manage_clones_menu")]
    ]
    return InlineKeyboardMarkup(buttons)

async def build_auto_delete_menu(bot_id):
    """Builds the menu to manage auto-delete settings for a specific clone."""
    bot_settings = bots_collection.find_one({"bot_id": bot_id})
    settings = bot_settings.get("auto_delete_settings", {'enabled': False, 'time_in_minutes': 30})
    
    status = "🟢 Enabled" if settings['enabled'] else "🔴 Disabled"
    time = settings['time_in_minutes']

    buttons = [
        [InlineKeyboardButton(f"Status: {status}", callback_data=f"toggle_auto_del_{bot_id}")],
        [InlineKeyboardButton(f"Time: {time} minutes", callback_data=f"set_del_time_{bot_id}")],
        [InlineKeyboardButton("⬅️ Back", callback_data=f"clone_settings_{bot_id}")]
    ]
    return InlineKeyboardMarkup(buttons)


# --- Main Callback Handler for the Power Panel ---
# This handler will ONLY manage callbacks starting with admin-related prefixes
@Client.on_callback_query(filters.regex(r"^(toggle_|admin_panel|manage_clones_menu|clone_settings_|set_auto_del_|toggle_auto_del_|set_del_time_|set_start_msg_)"))
async def power_panel_callbacks(client, query: CallbackQuery):
    data = query.data
    admin_id = query.from_user.id
    
    # Check if user is admin
    if not admin_id in config.ADMINS:
        await query.answer("❌ You are not authorized to use this feature.", show_alert=True)
        return

    # To prevent "CallbackQueryExpired" error
    await query.answer()

    if data == "admin_panel":
        await query.message.edit_text(
            "**⚙️ Admin Power Panel**\n\nHere you can manage your bot's live settings.",
            reply_markup=await build_main_panel()
        )
    
    elif data == "toggle_links":
        config.LINK_GENERATION_MODE = not config.LINK_GENERATION_MODE
        await query.message.edit_reply_markup(await build_main_panel())

    elif data == "toggle_public":
        config.PUBLIC_FILE_STORE = not config.PUBLIC_FILE_STORE
        await query.message.edit_reply_markup(await build_main_panel())

    elif data == "manage_clones_menu":
        clones_count = bots_collection.count_documents({"user_id": admin_id})
        if clones_count == 0:
            await query.message.edit_text(
                "**🤖 No Cloned Bots Found**\n\nYou haven't created any clone bots yet. Use /clone to create one.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_panel")]])
            )
        else:
            await query.message.edit_text(
                f"**🤖 Manage Your Cloned Bots ({clones_count})**\n\nSelect a bot from the list below to configure its settings.",
                reply_markup=await build_clones_list_menu(admin_id)
            )
    
    elif data.startswith("clone_settings_"):
        bot_id = int(data.split("_")[2])
        bot_details = bots_collection.find_one({"bot_id": bot_id, "user_id": admin_id})
        if not bot_details:
            await query.message.edit_text("❌ Bot not found or you don't have permission to manage it.")
            return
        await query.message.edit_text(
            f"**🛠️ Configuring: {bot_details['name']}**\n\nSelect a setting to modify for this bot.",
            reply_markup=await build_clone_settings_menu(bot_id)
        )
    
    elif data.startswith("set_start_msg_"):
        bot_id = int(data.split("_")[3])
        if not bots_collection.find_one({"bot_id": bot_id, "user_id": admin_id}):
             return await client.send_message(admin_id, "❌ Bot not found or you don't have permission to manage it.")
        
        await query.message.delete()
        ask = await ask_for_input(client, admin_id, "Please send me the new start message for this bot.\n\nTo cancel, send /cancel")
        if not ask or ask.text == "/cancel":
            return await client.send_message(admin_id, "Cancelled or timed out.")
        
        bots_collection.update_one({"bot_id": bot_id}, {"$set": {"custom_start_message": ask.text}})
        await client.send_message(admin_id, "✅ Successfully updated the start message for this clone!")

    elif data.startswith("set_auto_del_"):
        bot_id = int(data.split("_")[3])
        if not bots_collection.find_one({"bot_id": bot_id, "user_id": admin_id}):
            return
        await query.message.edit_text(
            "**🗑️ Auto-Delete Settings**\n\nConfigure the auto-delete behavior for this clone.",
            reply_markup=await build_auto_delete_menu(bot_id)
        )

    elif data.startswith("toggle_auto_del_"):
        bot_id = int(data.split("_")[3])
        bot_settings = bots_collection.find_one({"bot_id": bot_id, "user_id": admin_id})
        if not bot_settings: return
        
        current_status = bot_settings.get("auto_delete_settings", {}).get("enabled", False)
        new_status = not current_status
        bots_collection.update_one(
            {"bot_id": bot_id},
            {"$set": {"auto_delete_settings.enabled": new_status}}
        )
        await query.message.edit_reply_markup(await build_auto_delete_menu(bot_id))
        
    elif data.startswith("set_del_time_"):
        bot_id = int(data.split("_")[3])
        if not bots_collection.find_one({"bot_id": bot_id, "user_id": admin_id}):
            return
        
        await query.message.delete()
        ask = await ask_for_input(client, admin_id, "Please send the new auto-delete time in **minutes** (e.g., `30`).\n\nTo cancel, send /cancel", timeout=120)
        if not ask or ask.text == "/cancel":
            return await client.send_message(admin_id, "Cancelled or timed out.")
        
        try:
            new_time = int(ask.text)
            if new_time < 1:
                return await client.send_message(admin_id, "❌ Time must be at least 1 minute.")
                
            bots_collection.update_one(
                {"bot_id": bot_id},
                {"$set": {"auto_delete_settings.time_in_minutes": new_time}}
            )
            await client.send_message(admin_id, f"✅ Auto-delete time successfully set to **{new_time} minutes**.")
        except ValueError:
            await client.send_message(admin_id, "❌ Invalid input. Please send only a number.")

