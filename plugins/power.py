# plugins/power.py - Corrected by Gemini
# This is your dedicated admin control panel.

import config
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pymongo import MongoClient

# Connect to the database that stores clone information
mongo_client = MongoClient(config.DB_URI)
mongo_db = mongo_client["cloned_vjbotz"]
bots_collection = mongo_db["bots"]


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
    cloned_bots = bots_collection.find({"user_id": admin_id})
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
@Client.on_callback_query(filters.regex(r"^(toggle_|admin_panel|manage_clones_menu|clone_settings_|set_)") & filters.user(config.ADMINS))
async def power_panel_callbacks(client, query: CallbackQuery):
    data = query.data
    admin_id = query.from_user.id

    if data == "admin_panel":
        await query.answer()
        await query.message.edit_text(
            "**⚙️ Admin Power Panel**\n\nHere you can manage your bot's live settings.",
            reply_markup=await build_main_panel()
        )
    
    elif data == "toggle_links":
        config.LINK_GENERATION_MODE = not config.LINK_GENERATION_MODE
        await query.answer(f"Link Sharing is now {'ENABLED' if config.LINK_GENERATION_MODE else 'DISABLED'}")
        await query.message.edit_reply_markup(await build_main_panel())

    elif data == "toggle_public":
        config.PUBLIC_FILE_STORE = not config.PUBLIC_FILE_STORE
        await query.answer(f"Bot Mode is now {'PUBLIC' if config.PUBLIC_FILE_STORE else 'PRIVATE'}")
        await query.message.edit_reply_markup(await build_main_panel())

    elif data == "manage_clones_menu":
        await query.answer()
        await query.message.edit_text(
            "**🤖 Manage Your Cloned Bots**\n\nSelect a bot from the list below to configure its settings.",
            reply_markup=await build_clones_list_menu(admin_id)
        )
    
    elif data.startswith("clone_settings_"):
        bot_id = int(data.split("_")[2])
        bot_details = bots_collection.find_one({"bot_id": bot_id})
        await query.answer()
        await query.message.edit_text(
            f"**🛠️ Configuring: {bot_details['name']}**\n\nSelect a setting to modify for this bot.",
            reply_markup=await build_clone_settings_menu(bot_id)
        )
    
    elif data.startswith("set_start_msg_"):
        bot_id = int(data.split("_")[2])
        await query.message.delete()
        try:
            ask = await client.ask(admin_id, "Please send me the new start message for this bot.\n\nTo cancel, send /cancel", timeout=300)
            if ask.text == "/cancel":
                await client.send_message(admin_id, "Cancelled.")
            else:
                bots_collection.update_one({"bot_id": bot_id}, {"$set": {"custom_start_message": ask.text}})
                await client.send_message(admin_id, "✅ Successfully updated the start message for this clone!")
        except asyncio.TimeoutError:
            await client.send_message(admin_id, "Request timed out. Please try again.")

    elif data.startswith("set_auto_del_"):
        bot_id = int(data.split("_")[3])
        await query.answer()
        await query.message.edit_text(
            "**🗑️ Auto-Delete Settings**\n\nConfigure the auto-delete behavior for this clone.",
            reply_markup=await build_auto_delete_menu(bot_id)
        )

    elif data.startswith("toggle_auto_del_"):
        bot_id = int(data.split("_")[3])
        bot_settings = bots_collection.find_one({"bot_id": bot_id})
        current_status = bot_settings.get("auto_delete_settings", {}).get("enabled", False)
        
        new_status = not current_status
        bots_collection.update_one(
            {"bot_id": bot_id},
            {"$set": {"auto_delete_settings.enabled": new_status}}
        )
        await query.answer(f"Auto-delete is now {'ENABLED' if new_status else 'DISABLED'}")
        await query.message.edit_reply_markup(await build_auto_delete_menu(bot_id))
        
    elif data.startswith("set_del_time_"):
        bot_id = int(data.split("_")[3])
        await query.message.delete()
        try:
            ask = await client.ask(admin_id, "Please send the new auto-delete time in **minutes** (e.g., `30`).\n\nTo cancel, send /cancel", timeout=120)
            if ask.text == "/cancel":
                await client.send_message(admin_id, "Cancelled.")
                return
            
            new_time = int(ask.text)
            bots_collection.update_one(
                {"bot_id": bot_id},
                {"$set": {"auto_delete_settings.time_in_minutes": new_time}}
            )
            await client.send_message(admin_id, f"✅ Auto-delete time successfully set to **{new_time} minutes**.")

        except asyncio.TimeoutError:
            await client.send_message(admin_id, "Request timed out.")
        except ValueError:
            await client.send_message(admin_id, "❌ Invalid input. Please send only a number.")
