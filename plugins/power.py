# plugins/power.py - Updated by Gemini
# Added full logic for Auto-Delete settings.

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
    # ... (This function remains the same) ...

async def build_clones_list_menu(admin_id):
    # ... (This function remains the same) ...

async def build_clone_settings_menu(bot_id):
    # ... (This function remains the same) ...

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

    # ... (admin_panel, toggle_links, toggle_public, manage_clones_menu, clone_settings_ handlers remain the same) ...
    
    if data.startswith("set_start_msg_"):
        # ... (This handler remains the same) ...

    # --- New & Updated Auto-Delete Handlers ---
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
        
        # Flip the status
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

