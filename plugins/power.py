# plugins/power.py - Updated by Gemini
# Added logic for "Set Start Msg" button.

import config
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pymongo import MongoClient

# Connect to the database that stores clone information
mongo_client = MongoClient(config.DB_URI)
mongo_db = mongo_client["cloned_vjbotz"]
bots_collection = mongo_db["bots"]


# --- Helper functions to build the different menus ---
async def build_main_panel():
    buttons = [
        [InlineKeyboardButton(f"Main Bot Link Sharing: {'🟢 ON' if config.LINK_GENERATION_MODE else '🔴 OFF'}", callback_data="toggle_links")],
        [InlineKeyboardButton(f"Bot Public Mode: {'🌍 Public' if config.PUBLIC_FILE_STORE else '🔒 Private'}", callback_data="toggle_public")],
        [InlineKeyboardButton("🤖 Manage Clones", callback_data="manage_clones_menu")],
        [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="start")]
    ]
    return InlineKeyboardMarkup(buttons)

async def build_clones_list_menu(admin_id):
    buttons = []
    # Find all bots cloned by this admin
    cloned_bots = bots_collection.find({"user_id": admin_id})
    for bot in cloned_bots:
        buttons.append([InlineKeyboardButton(f"{bot['name']} (@{bot['username']})", callback_data=f"clone_settings_{bot['bot_id']}")])
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="admin_panel")])
    return InlineKeyboardMarkup(buttons)

async def build_clone_settings_menu(bot_id):
    buttons = [
        [InlineKeyboardButton("✏️ Set Start Msg", callback_data=f"set_start_msg_{bot_id}")],
        [InlineKeyboardButton("🗑️ Auto-Delete Settings", callback_data=f"set_auto_del_{bot_id}")],
        [InlineKeyboardButton("⬅️ Back to Clones List", callback_data="manage_clones_menu")]
    ]
    return InlineKeyboardMarkup(buttons)


# --- Main Callback Handler for the Power Panel ---
@Client.on_callback_query(filters.regex(r"^(toggle_|admin_panel|manage_clones_menu|clone_settings_|set_)") & filters.user(config.ADMINS))
async def power_panel_callbacks(client, query: CallbackQuery):
    data = query.data
    admin_id = query.from_user.id

    if data == "admin_panel":
        await query.answer()
        await query.message.edit_text("**⚙️ Admin Power Panel**...", reply_markup=await build_main_panel())
    
    # ... (toggle_links and toggle_public handlers remain the same) ...

    elif data == "manage_clones_menu":
        await query.answer()
        await query.message.edit_text("**🤖 Manage Your Cloned Bots**...", reply_markup=await build_clones_list_menu(admin_id))
    
    elif data.startswith("clone_settings_"):
        bot_id = int(data.split("_")[2])
        bot_details = bots_collection.find_one({"bot_id": bot_id})
        await query.answer()
        await query.message.edit_text(f"**🛠️ Configuring: {bot_details['name']}**...", reply_markup=await build_clone_settings_menu(bot_id))
    
    elif data.startswith("set_start_msg_"):
        bot_id = int(data.split("_")[2])
        await query.message.delete() # Delete the panel to keep chat clean
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
        await query.answer("This feature is coming soon!", show_alert=True)

