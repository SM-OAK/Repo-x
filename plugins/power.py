# plugins/power.py - Complete Enhanced Admin Panel
import config
import asyncio
import logging
import psutil
import sys
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from pymongo import MongoClient
from datetime import datetime, timedelta

# Initialize MongoDB
try:
    mongo_client = MongoClient(config.DB_URI)
    mongo_db = mongo_client["cloned_vjbotz"]
    bots_collection = mongo_db["bots"]
    settings_collection = mongo_db["settings"]
    users_collection = mongo_db["users"]
    logging.info("MongoDB connected successfully in power.py")
except Exception as e:
    logging.error(f"MongoDB connection failed in power.py: {e}")

# Global settings with defaults
GLOBAL_SETTINGS = {
    'link_generation': getattr(config, 'LINK_GENERATION_MODE', True),
    'public_file_store': getattr(config, 'PUBLIC_FILE_STORE', True),
    'auto_delete_enabled': getattr(config, 'AUTO_DELETE_ENABLED', False),
    'auto_delete_time': getattr(config, 'AUTO_DELETE_TIME', 300),
    'maintenance_mode': getattr(config, 'MAINTENANCE_MODE', False),
    'clone_mode': getattr(config, 'CLONE_MODE', True),
    'broadcast_enabled': getattr(config, 'BROADCAST_ENABLED', True),
    'welcome_enabled': getattr(config, 'WELCOME_ENABLED', True)
}

async def load_global_settings():
    """Load settings from database or use defaults"""
    global GLOBAL_SETTINGS
    try:
        saved_settings = settings_collection.find_one({"type": "global"})
        if saved_settings:
            GLOBAL_SETTINGS.update(saved_settings.get('data', {}))
    except Exception as e:
        logging.error(f"Error loading settings: {e}")

async def save_global_settings():
    """Save current settings to database"""
    try:
        settings_collection.update_one(
            {"type": "global"},
            {"$set": {"data": GLOBAL_SETTINGS, "updated_at": datetime.now()}},
            upsert=True
        )
    except Exception as e:
        logging.error(f"Error saving settings: {e}")

async def ask_for_input(client, chat_id, text, timeout=300):
    """Enhanced input handler with better error handling"""
    question = await client.send_message(chat_id, text)
    try:
        response = await client.listen(chat_id=chat_id, user_id=chat_id, timeout=timeout)
        if response and (response.text or response.caption):
            if response.text and response.text.lower() in ["/cancel", "cancel"]:
                await client.send_message(chat_id, "❌ **Process cancelled.**")
                return None
            return response
        return None
    except asyncio.TimeoutError:
        await client.send_message(chat_id, "⏱️ **Request timed out.** Please try again.")
        return None
    except Exception as e:
        await client.send_message(chat_id, f"❌ **Error:** {str(e)}")
        return None
    finally:
        try:
            await question.delete()
        except:
            pass

async def build_main_panel():
    """Build the main admin panel with all features"""
    await load_global_settings()
    
    buttons = [
        [InlineKeyboardButton(f"🔗 Link Generation: {'🟢 ON' if GLOBAL_SETTINGS['link_generation'] else '🔴 OFF'}", callback_data="toggle_admin_links")],
        [InlineKeyboardButton(f"📂 Bot Mode: {'🌍 Public' if GLOBAL_SETTINGS['public_file_store'] else '🔒 Private'}", callback_data="toggle_public")],
        [InlineKeyboardButton(f"🗑️ Auto Delete: {'🟢 ON' if GLOBAL_SETTINGS['auto_delete_enabled'] else '🔴 OFF'}", callback_data="toggle_auto_delete")],
        [InlineKeyboardButton(f"⚙️ Maintenance: {'🟢 ON' if GLOBAL_SETTINGS['maintenance_mode'] else '🔴 OFF'}", callback_data="toggle_maintenance")],
        [InlineKeyboardButton(f"🤖 Clone Mode: {'🟢 ON' if GLOBAL_SETTINGS['clone_mode'] else '🔴 OFF'}", callback_data="toggle_admin_clone_mode")],
        [InlineKeyboardButton("📊 Bot Statistics", callback_data="bot_stats"), InlineKeyboardButton("👥 User Stats", callback_data="user_stats")],
        [InlineKeyboardButton("🤖 Manage Clones", callback_data="manage_clones_menu"), InlineKeyboardButton("📢 Broadcast", callback_data="broadcast_menu")],
        [InlineKeyboardButton("⚙️ Advanced Settings", callback_data="advanced_settings"), InlineKeyboardButton("🧹 Cleanup Tools", callback_data="cleanup_tools")],
        [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="start")]
    ]
    return InlineKeyboardMarkup(buttons)

async def build_broadcast_menu():
    buttons = [[InlineKeyboardButton("📢 Broadcast to All Users", callback_data="broadcast_all")], [InlineKeyboardButton("⬅️ Back", callback_data="admin_panel")]]
    return InlineKeyboardMarkup(buttons)

async def build_advanced_settings_menu():
    await load_global_settings()
    buttons = [
        [InlineKeyboardButton(f"🎯 Auto Delete Time: {GLOBAL_SETTINGS['auto_delete_time']}s", callback_data="set_global_auto_delete_time")],
        [InlineKeyboardButton(f"📢 Broadcast: {'🟢 ON' if GLOBAL_SETTINGS['broadcast_enabled'] else '🔴 OFF'}", callback_data="toggle_broadcast")],
        [InlineKeyboardButton(f"👋 Welcome: {'🟢 ON' if GLOBAL_SETTINGS['welcome_enabled'] else '🔴 OFF'}", callback_data="toggle_welcome")],
        [InlineKeyboardButton("📊 System Info", callback_data="system_info")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(buttons)

async def build_cleanup_tools_menu():
    buttons = [
        [InlineKeyboardButton("🧹 Clean Invalid Tokens", callback_data="cleanup_invalid_tokens")],
        [InlineKeyboardButton("⚠️ Reset All Settings", callback_data="reset_all_settings")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(buttons)

@Client.on_callback_query(filters.regex(r"^(admin_panel|toggle_admin|manage_|clone_settings_|set_|broadcast_|advanced_|cleanup_|bot_stats|user_stats|system_info|reset_all_settings)") & filters.user(config.ADMINS))
async def enhanced_admin_callbacks(client: Client, query: CallbackQuery):
    """Enhanced callback handler for all admin functions"""
    data = query.data
    admin_id = query.from_user.id
    
    try:
        await query.answer()
        await load_global_settings()
        
        if data == "admin_panel":
            await query.message.edit_text("**⚙️ Enhanced Admin Power Panel**", reply_markup=await build_main_panel())
            
        elif data.startswith("toggle_admin_"):
            key = data.replace("toggle_admin_", "")
            GLOBAL_SETTINGS[key] = not GLOBAL_SETTINGS[key]
            await save_global_settings()
            await query.message.edit_reply_markup(await build_main_panel())

        elif data == "bot_stats":
            total_clones = bots_collection.count_documents({})
            active_clones = bots_collection.count_documents({"active": True})
            unique_owners = len(bots_collection.distinct("user_id"))
            stats = f"**📊 Bot Statistics**\n\n🤖 **Total Clones:** `{total_clones}`\n🟢 **Active Clones:** `{active_clones}`\n👥 **Unique Owners:** `{unique_owners}`"
            await query.message.edit_text(stats, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh", callback_data="bot_stats")], [InlineKeyboardButton("⬅️ Back", callback_data="admin_panel")]]))

        elif data == "user_stats":
            total_users = users_collection.count_documents({})
            today = datetime.now().replace(hour=0, minute=0, second=0)
            today_users = users_collection.count_documents({"last_seen": {"$gte": today}})
            stats = f"**👥 User Statistics**\n\n👤 **Total Users:** `{total_users}`\n☀️ **Active Today:** `{today_users}`"
            await query.message.edit_text(stats, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh", callback_data="user_stats")], [InlineKeyboardButton("⬅️ Back", callback_data="admin_panel")]]))
            
        elif data == "broadcast_menu":
            await query.message.edit_text("**📢 Broadcast System**", reply_markup=await build_broadcast_menu())

        elif data == "broadcast_all":
            await query.message.delete()
            ask = await ask_for_input(client, admin_id, "**📢 Broadcast Mode**\n\nPlease send the message you want to broadcast. To cancel, send `/cancel`.")
            if ask:
                await client.send_message(admin_id, "⏳ Broadcasting... This may take a while.")
                
                async def do_broadcast():
                    success, failed = 0, 0
                    users = users_collection.find({}, {"user_id": 1})
                    for user in users:
                        try:
                            await ask.copy(user["user_id"])
                            success += 1
                        except Exception:
                            failed += 1
                        await asyncio.sleep(0.05) # 20 messages per second limit
                    await client.send_message(admin_id, f"✅ **Broadcast Complete!**\n\n- Sent to: `{success}` users\n- Failed for: `{failed}` users")
                
                asyncio.create_task(do_broadcast())

        elif data == "advanced_settings":
            await query.message.edit_text("**⚙️ Advanced Settings**", reply_markup=await build_advanced_settings_menu())

        elif data == "cleanup_tools":
            await query.message.edit_text("**🧹 Cleanup Tools**\n\n⚠️ **Warning:** These actions are irreversible.", reply_markup=await build_cleanup_tools_menu())
            
        elif data == "cleanup_invalid_tokens":
            msg = await query.message.edit_text("🧹 *Scanning for invalid tokens...*")
            cleaned_count = 0
            all_bots = list(bots_collection.find({}, {"bot_id": 1, "token": 1, "username": 1}))
            for bot in all_bots:
                try:
                    temp_client = Client(name=f"test_{bot['bot_id']}", api_id=config.API_ID, api_hash=config.API_HASH, bot_token=bot['token'], in_memory=True)
                    await temp_client.start()
                    await temp_client.stop()
                except Exception:
                    bots_collection.delete_one({"bot_id": bot['bot_id']})
                    cleaned_count += 1
            await msg.edit_text(f"✅ **Cleanup complete!** Removed `{cleaned_count}` invalid clones.")

        elif data == "reset_all_settings":
            await query.message.edit_text("⚠️ **Are you sure?**\n\nThis will reset all global settings to their default values. This action cannot be undone.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Yes, Reset Now", callback_data="confirm_reset_settings")], [InlineKeyboardButton("❌ Cancel", callback_data="cleanup_tools")]]))
        
        elif data == "confirm_reset_settings":
            settings_collection.delete_one({"type": "global"})
            # Re-initialize defaults
            GLOBAL_SETTINGS.clear()
            GLOBAL_SETTINGS.update({k: getattr(config, k.upper(), v) for k, v in {
                'link_generation': True, 'public_file_store': True, 'auto_delete_enabled': False,
                'auto_delete_time': 300, 'maintenance_mode': False, 'clone_mode': True,
                'broadcast_enabled': True, 'welcome_enabled': True
            }.items()})
            await save_global_settings()
            await query.message.edit_text("✅ **All settings have been reset to default.**", reply_markup=await build_cleanup_tools_menu())

        elif data == "system_info":
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                info = (
                    f"**🖥️ System Information**\n\n"
                    f"**CPU:** `{cpu_percent}%`\n"
                    f"**Memory:** `{memory.percent}%` (`{memory.used//1024**2}MB / {memory.total//1024**2}MB`)\n"
                    f"**Disk:** `{disk.percent}%` (`{disk.used//1024**3}GB / {disk.total//1024**3}GB`)\n\n"
                    f"**Python Version:** `{sys.version.split()[0]}`\n\n"
                    f"**Database Stats:**\n"
                    f"• Users: `{users_collection.count_documents({})}`\n"
                    f"• Cloned Bots: `{bots_collection.count_documents({})}`"
                )
                await query.message.edit_text(info, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh", callback_data="system_info")], [InlineKeyboardButton("⬅️ Back", callback_data="advanced_settings")]]))
            except Exception as e:
                logging.error(f"System info error: {e}")
                await query.message.edit_text("❌ Could not retrieve system info.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="advanced_settings")]]))

        else:
            await query.answer("This feature is under development.", show_alert=True)

    except Exception as e:
        logging.error(f"Error in admin callback ({query.data}): {e}")
        await query.answer("❌ An unexpected error occurred. Please check the logs.", show_alert=True)
