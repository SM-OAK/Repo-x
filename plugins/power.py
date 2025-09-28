# plugins/power.py - Corrected and integrated
import config
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pymongo import MongoClient

mongo_client = MongoClient(config.DB_URI)
mongo_db = mongo_client["cloned_vjbotz"]
bots_collection = mongo_db["bots"]

async def ask_for_input(client, chat_id, text, timeout=300):
    """Safely asks for and waits for a user's text response."""
    question = await client.send_message(chat_id, text)
    try:
        response = await client.listen(chat_id=chat_id, user_id=chat_id, timeout=timeout)
        if response and response.text and response.text.lower() == "/cancel":
            await client.send_message(chat_id, "Process cancelled.")
            return None
        return response
    except asyncio.TimeoutError:
        await client.send_message(chat_id, "Request timed out. Please try again.")
        return None
    finally:
        await question.delete()

async def build_main_panel():
    buttons = [
        [InlineKeyboardButton(f"Link Sharing: {'🟢 ON' if config.LINK_GENERATION_MODE else '🔴 OFF'}", callback_data="toggle_links")],
        [InlineKeyboardButton(f"Bot Mode: {'🌍 Public' if config.PUBLIC_FILE_STORE else '🔒 Private'}", callback_data="toggle_public")],
        [InlineKeyboardButton("🤖 Manage Clones", callback_data="manage_clones_menu")],
        [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="start")]
    ]
    return InlineKeyboardMarkup(buttons)

async def build_clones_list_menu(admin_id):
    buttons = []
    cloned_bots = bots_collection.find({"user_id": admin_id}).sort("name", 1)
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

async def build_auto_delete_menu(bot_id):
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

@Client.on_callback_query(filters.regex(r"^(toggle_|admin_panel|manage_clones_menu|clone_settings_|set_auto_del_|toggle_auto_del_|set_del_time_|set_start_msg_)") & filters.user(config.ADMINS))
async def power_panel_callbacks(client, query: CallbackQuery):
    data = query.data
    admin_id = query.from_user.id
    await query.answer()

    if data == "admin_panel":
        await query.message.edit_text("**⚙️ Admin Power Panel**", reply_markup=await build_main_panel())
    elif data == "toggle_links":
        config.LINK_GENERATION_MODE = not config.LINK_GENERATION_MODE
        await query.message.edit_reply_markup(await build_main_panel())
    elif data == "toggle_public":
        config.PUBLIC_FILE_STORE = not config.PUBLIC_FILE_STORE
        await query.message.edit_reply_markup(await build_main_panel())
    elif data == "manage_clones_menu":
        if bots_collection.count_documents({"user_id": admin_id}) == 0:
            await query.message.edit_text("**🤖 No Cloned Bots Found**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="admin_panel")]]))
        else:
            await query.message.edit_text("**🤖 Manage Your Cloned Bots**", reply_markup=await build_clones_list_menu(admin_id))
    elif data.startswith("clone_settings_"):
        bot_id = int(data.split("_")[2])
        bot_details = bots_collection.find_one({"bot_id": bot_id})
        await query.message.edit_text(f"**🛠️ Configuring: {bot_details['name']}**", reply_markup=await build_clone_settings_menu(bot_id))
    elif data.startswith("set_start_msg_"):
        bot_id = int(data.split("_")[3])
        await query.message.delete()
        ask = await ask_for_input(client, admin_id, "Please send me the new start message for this bot.\n\nTo cancel, send /cancel")
        if ask and ask.text:
            bots_collection.update_one({"bot_id": bot_id}, {"$set": {"custom_start_message": ask.text}})
            await client.send_message(admin_id, "✅ Start message updated!")
    elif data.startswith("set_auto_del_"):
        bot_id = int(data.split("_")[3])
        await query.message.edit_text("**🗑️ Auto-Delete Settings**", reply_markup=await build_auto_delete_menu(bot_id))
    elif data.startswith("toggle_auto_del_"):
        bot_id = int(data.split("_")[3])
        bot_settings = bots_collection.find_one({"bot_id": bot_id})
        current_status = bot_settings.get("auto_delete_settings", {}).get("enabled", False)
        bots_collection.update_one({"bot_id": bot_id}, {"$set": {"auto_delete_settings.enabled": not current_status}})
        await query.message.edit_reply_markup(await build_auto_delete_menu(bot_id))
    elif data.startswith("set_del_time_"):
        bot_id = int(data.split("_")[3])
        await query.message.delete()
        ask = await ask_for_input(client, admin_id, "Please send the new auto-delete time in **minutes**.", timeout=120)
        if ask and ask.text:
            try:
                new_time = int(ask.text)
                if new_time < 1:
                    await client.send_message(admin_id, "❌ Time must be at least 1 minute.")
                else:
                    bots_collection.update_one({"bot_id": bot_id}, {"$set": {"auto_delete_settings.time_in_minutes": new_time}})
                    await client.send_message(admin_id, f"✅ Auto-delete time set to {new_time} minutes.")
            except ValueError:
                await client.send_message(admin_id, "❌ Invalid input. Please send only a number.")
