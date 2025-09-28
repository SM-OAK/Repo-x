# plugins/power.py - Enhanced and fully integrated admin panel
import config
import asyncio
import logging
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
    logging.info("MongoDB connected successfully")
except Exception as e:
    logging.error(f"MongoDB connection failed: {e}")

# Global settings with defaults
GLOBAL_SETTINGS = {
    'link_generation': getattr(config, 'LINK_GENERATION_MODE', True),
    'public_file_store': getattr(config, 'PUBLIC_FILE_STORE', True),
    'auto_delete_enabled': getattr(config, 'AUTO_DELETE_ENABLED', False),
    'auto_delete_time': getattr(config, 'AUTO_DELETE_TIME', 300),  # 5 minutes default
    'maintenance_mode': getattr(config, 'MAINTENANCE_MODE', False),
    'clone_mode': getattr(config, 'CLONE_MODE', True),
    'broadcast_enabled': getattr(config, 'BROADCAST_ENABLED', True),
    'welcome_enabled': getattr(config, 'WELCOME_ENABLED', True)
}

async def load_global_settings():
    """Load settings from database or use defaults"""
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
        if response and response.text:
            if response.text.lower() in ["/cancel", "cancel"]:
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
    buttons = [
        [
            InlineKeyboardButton(
                f"🔗 Link Generation: {'🟢 ON' if GLOBAL_SETTINGS['link_generation'] else '🔴 OFF'}",
                callback_data="toggle_links"
            )
        ],
        [
            InlineKeyboardButton(
                f"📂 Bot Mode: {'🌍 Public' if GLOBAL_SETTINGS['public_file_store'] else '🔒 Private'}",
                callback_data="toggle_public"
            )
        ],
        [
            InlineKeyboardButton(
                f"🗑️ Auto Delete: {'🟢 ON' if GLOBAL_SETTINGS['auto_delete_enabled'] else '🔴 OFF'}",
                callback_data="toggle_auto_delete"
            )
        ],
        [
            InlineKeyboardButton(
                f"⚙️ Maintenance: {'🟢 ON' if GLOBAL_SETTINGS['maintenance_mode'] else '🔴 OFF'}",
                callback_data="toggle_maintenance"
            )
        ],
        [
            InlineKeyboardButton(
                f"🤖 Clone Mode: {'🟢 ON' if GLOBAL_SETTINGS['clone_mode'] else '🔴 OFF'}",
                callback_data="toggle_clone_mode"
            )
        ],
        [
            InlineKeyboardButton("📊 Bot Statistics", callback_data="bot_stats"),
            InlineKeyboardButton("👥 User Stats", callback_data="user_stats")
        ],
        [
            InlineKeyboardButton("🤖 Manage Clones", callback_data="manage_clones_menu"),
            InlineKeyboardButton("📢 Broadcast", callback_data="broadcast_menu")
        ],
        [
            InlineKeyboardButton("⚙️ Advanced Settings", callback_data="advanced_settings"),
            InlineKeyboardButton("🧹 Cleanup Tools", callback_data="cleanup_tools")
        ],
        [
            InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="start")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

async def build_clones_list_menu(admin_id):
    """Build clones management menu"""
    buttons = []
    try:
        cloned_bots = list(bots_collection.find({"user_id": admin_id}).sort("name", 1))
        
        if not cloned_bots:
            buttons.append([InlineKeyboardButton("❌ No Clones Found", callback_data="no_action")])
        else:
            for bot in cloned_bots:
                status = "🟢" if bot.get('active', True) else "🔴"
                buttons.append([
                    InlineKeyboardButton(
                        f"{status} {bot['name']} (@{bot['username']})",
                        callback_data=f"clone_settings_{bot['bot_id']}"
                    )
                ])
        
        buttons.extend([
            [InlineKeyboardButton("📊 Clone Statistics", callback_data="clone_statistics")],
            [InlineKeyboardButton("🧹 Cleanup Invalid Clones", callback_data="cleanup_clones")],
            [InlineKeyboardButton("⬅️ Back", callback_data="admin_panel")]
        ])
    except Exception as e:
        logging.error(f"Error building clones menu: {e}")
        buttons = [[InlineKeyboardButton("❌ Error Loading Clones", callback_data="admin_panel")]]
    
    return InlineKeyboardMarkup(buttons)

async def build_clone_settings_menu(bot_id):
    """Build individual clone settings menu"""
    try:
        bot_details = bots_collection.find_one({"bot_id": bot_id})
        if not bot_details:
            return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Bot Not Found", callback_data="manage_clones_menu")]])
        
        auto_del_settings = bot_details.get("auto_delete_settings", {'enabled': False, 'time_in_minutes': 30})
        
        buttons = [
            [InlineKeyboardButton("✏️ Edit Start Message", callback_data=f"set_start_msg_{bot_id}")],
            [InlineKeyboardButton("🖼️ Set Bot Picture", callback_data=f"set_bot_pic_{bot_id}")],
            [
                InlineKeyboardButton(
                    f"🗑️ Auto Delete: {'🟢 ON' if auto_del_settings['enabled'] else '🔴 OFF'}",
                    callback_data=f"toggle_clone_auto_del_{bot_id}"
                )
            ],
            [InlineKeyboardButton(f"⏱️ Delete Time: {auto_del_settings['time_in_minutes']}min", callback_data=f"set_del_time_{bot_id}")],
            [
                InlineKeyboardButton("📊 Bot Analytics", callback_data=f"bot_analytics_{bot_id}"),
                InlineKeyboardButton("🔄 Restart Bot", callback_data=f"restart_bot_{bot_id}")
            ],
            [
                InlineKeyboardButton("⏸️ Pause Bot", callback_data=f"pause_bot_{bot_id}"),
                InlineKeyboardButton("🗑️ Delete Bot", callback_data=f"delete_bot_{bot_id}")
            ],
            [InlineKeyboardButton("⬅️ Back to Clones", callback_data="manage_clones_menu")]
        ]
        
        return InlineKeyboardMarkup(buttons)
    except Exception as e:
        logging.error(f"Error building clone settings: {e}")
        return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Error", callback_data="manage_clones_menu")]])

async def build_broadcast_menu():
    """Build broadcast menu"""
    buttons = [
        [InlineKeyboardButton("📢 Broadcast to All Users", callback_data="broadcast_all")],
        [InlineKeyboardButton("👥 Broadcast to Clone Owners", callback_data="broadcast_clone_owners")],
        [InlineKeyboardButton("🤖 Broadcast via Clone Bots", callback_data="broadcast_via_clones")],
        [InlineKeyboardButton("📊 Broadcast Statistics", callback_data="broadcast_stats")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(buttons)

async def build_advanced_settings_menu():
    """Build advanced settings menu"""
    buttons = [
        [
            InlineKeyboardButton(
                f"🎯 Auto Delete Time: {GLOBAL_SETTINGS['auto_delete_time']}s",
                callback_data="set_global_auto_delete_time"
            )
        ],
        [
            InlineKeyboardButton(
                f"📢 Broadcast: {'🟢 ON' if GLOBAL_SETTINGS['broadcast_enabled'] else '🔴 OFF'}",
                callback_data="toggle_broadcast"
            )
        ],
        [
            InlineKeyboardButton(
                f"👋 Welcome: {'🟢 ON' if GLOBAL_SETTINGS['welcome_enabled'] else '🔴 OFF'}",
                callback_data="toggle_welcome"
            )
        ],
        [InlineKeyboardButton("📝 Edit Welcome Message", callback_data="edit_welcome_msg")],
        [InlineKeyboardButton("🔧 Database Settings", callback_data="database_settings")],
        [InlineKeyboardButton("📊 System Info", callback_data="system_info")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(buttons)

async def build_cleanup_tools_menu():
    """Build cleanup tools menu"""
    buttons = [
        [InlineKeyboardButton("🧹 Clean Invalid Tokens", callback_data="cleanup_invalid_tokens")],
        [InlineKeyboardButton("🗑️ Clean Old Messages", callback_data="cleanup_old_messages")],
        [InlineKeyboardButton("📊 Database Cleanup", callback_data="cleanup_database")],
        [InlineKeyboardButton("🔄 Restart All Clones", callback_data="restart_all_clones")],
        [InlineKeyboardButton("⚠️ Reset All Settings", callback_data="reset_all_settings")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(buttons)

@Client.on_callback_query(filters.regex(r"^(admin_panel|toggle_|manage_|clone_|set_|broadcast_|advanced_|cleanup_|bot_|user_)") & filters.user(config.ADMINS))
async def enhanced_admin_callbacks(client: Client, query: CallbackQuery):
    """Enhanced callback handler for all admin functions"""
    data = query.data
    admin_id = query.from_user.id
    
    try:
        await query.answer()
        
        # Load current settings
        await load_global_settings()
        
        if data == "admin_panel":
            await query.message.edit_text(
                "**⚙️ Enhanced Admin Power Panel**\n\n"
                "🎛️ **Control Panel Features:**\n"
                "• Link Generation Control\n"
                "• Bot Mode Management\n"
                "• Auto Delete System\n"
                "• Clone Bot Management\n"
                "• Broadcast System\n"
                "• Advanced Settings\n"
                "• Cleanup Tools\n\n"
                f"👤 **Admin:** {query.from_user.mention}\n"
                f"🕐 **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                reply_markup=await build_main_panel()
            )
            
        elif data == "toggle_links":
            GLOBAL_SETTINGS['link_generation'] = not GLOBAL_SETTINGS['link_generation']
            config.LINK_GENERATION_MODE = GLOBAL_SETTINGS['link_generation']
            await save_global_settings()
            await query.message.edit_reply_markup(await build_main_panel())
            
        elif data == "toggle_public":
            GLOBAL_SETTINGS['public_file_store'] = not GLOBAL_SETTINGS['public_file_store']
            config.PUBLIC_FILE_STORE = GLOBAL_SETTINGS['public_file_store']
            await save_global_settings()
            await query.message.edit_reply_markup(await build_main_panel())
            
        elif data == "toggle_auto_delete":
            GLOBAL_SETTINGS['auto_delete_enabled'] = not GLOBAL_SETTINGS['auto_delete_enabled']
            await save_global_settings()
            await query.message.edit_reply_markup(await build_main_panel())
            
        elif data == "toggle_maintenance":
            GLOBAL_SETTINGS['maintenance_mode'] = not GLOBAL_SETTINGS['maintenance_mode']
            await save_global_settings()
            await query.message.edit_reply_markup(await build_main_panel())
            
        elif data == "toggle_clone_mode":
            GLOBAL_SETTINGS['clone_mode'] = not GLOBAL_SETTINGS['clone_mode']
            config.CLONE_MODE = GLOBAL_SETTINGS['clone_mode']
            await save_global_settings()
            await query.message.edit_reply_markup(await build_main_panel())
            
        elif data == "manage_clones_menu":
            total_clones = bots_collection.count_documents({"user_id": admin_id})
            if total_clones == 0:
                await query.message.edit_text(
                    "**🤖 No Cloned Bots Found**\n\n"
                    "You haven't created any clone bots yet.\n"
                    "Use /clone command to create your first bot!",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ Back", callback_data="admin_panel")]
                    ])
                )
            else:
                await query.message.edit_text(
                    f"**🤖 Manage Your Cloned Bots ({total_clones})**\n\n"
                    "Select a bot to configure its settings:",
                    reply_markup=await build_clones_list_menu(admin_id)
                )
                
        elif data.startswith("clone_settings_"):
            bot_id = int(data.split("_")[2])
            bot_details = bots_collection.find_one({"bot_id": bot_id})
            if bot_details:
                await query.message.edit_text(
                    f"**🛠️ Configuring: {bot_details['name']}**\n\n"
                    f"**Bot Info:**\n"
                    f"• Username: @{bot_details['username']}\n"
                    f"• Bot ID: `{bot_details['bot_id']}`\n"
                    f"• Created: {bot_details.get('created_at', 'Unknown')}\n"
                    f"• Status: {'🟢 Active' if bot_details.get('active', True) else '🔴 Inactive'}",
                    reply_markup=await build_clone_settings_menu(bot_id)
                )
                
        elif data.startswith("set_start_msg_"):
            bot_id = int(data.split("_")[3])
            await query.message.delete()
            ask = await ask_for_input(
                client, admin_id,
                "**✏️ Set Custom Start Message**\n\n"
                "Send me the new start message for this bot.\n"
                "You can use HTML formatting.\n\n"
                "**Variables available:**\n"
                "• `{mention}` - User mention\n"
                "• `{first_name}` - User first name\n"
                "• `{bot_mention}` - Bot mention\n\n"
                "Send /cancel to cancel.",
                timeout=300
            )
            if ask and ask.text:
                bots_collection.update_one(
                    {"bot_id": bot_id},
                    {"$set": {"custom_start_message": ask.text, "updated_at": datetime.now()}}
                )
                await client.send_message(admin_id, "✅ **Start message updated successfully!**")
                
        elif data.startswith("toggle_clone_auto_del_"):
            bot_id = int(data.split("_")[4])
            bot_settings = bots_collection.find_one({"bot_id": bot_id})
            current_settings = bot_settings.get("auto_delete_settings", {'enabled': False, 'time_in_minutes': 30})
            current_settings['enabled'] = not current_settings['enabled']
            
            bots_collection.update_one(
                {"bot_id": bot_id},
                {"$set": {"auto_delete_settings": current_settings, "updated_at": datetime.now()}}
            )
            await query.message.edit_reply_markup(await build_clone_settings_menu(bot_id))
            
        elif data.startswith("set_del_time_"):
            bot_id = int(data.split("_")[3])
            await query.message.delete()
            ask = await ask_for_input(
                client, admin_id,
                "**⏱️ Set Auto-Delete Time**\n\n"
                "Enter the time in minutes after which messages should be deleted.\n"
                "Minimum: 1 minute, Maximum: 10080 minutes (1 week)\n\n"
                "Send /cancel to cancel.",
                timeout=120
            )
            if ask and ask.text:
                try:
                    new_time = int(ask.text)
                    if 1 <= new_time <= 10080:
                        bots_collection.update_one(
                            {"bot_id": bot_id},
                            {"$set": {"auto_delete_settings.time_in_minutes": new_time, "updated_at": datetime.now()}}
                        )
                        await client.send_message(
                            admin_id,
                            f"✅ **Auto-delete time set to {new_time} minutes.**"
                        )
                    else:
                        await client.send_message(
                            admin_id,
                            "❌ **Invalid time range.** Please enter between 1-10080 minutes."
                        )
                except ValueError:
                    await client.send_message(admin_id, "❌ **Invalid input.** Please enter a valid number.")
                    
        elif data == "bot_stats":
            total_clones = bots_collection.count_documents({})
            active_clones = bots_collection.count_documents({"active": {"$ne": False}})
            unique_users = len(bots_collection.distinct("user_id"))
            recent_clones = bots_collection.count_documents({
                "created_at": {"$gte": datetime.now() - timedelta(days=1)}
            })
            
            stats_text = (
                f"**📊 Bot Statistics**\n\n"
                f"🤖 **Total Clones:** {total_clones}\n"
                f"🟢 **Active Clones:** {active_clones}\n"
                f"👥 **Unique Users:** {unique_users}\n"
                f"📅 **Today's Clones:** {recent_clones}\n\n"
                f"📈 **Success Rate:** {(active_clones/total_clones*100):.1f}%" if total_clones > 0 else "N/A"
            )
            
            await query.message.edit_text(
                stats_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Refresh", callback_data="bot_stats")],
                    [InlineKeyboardButton("⬅️ Back", callback_data="admin_panel")]
                ])
            )
            
        elif data == "broadcast_menu":
            await query.message.edit_text(
                "**📢 Broadcast System**\n\n"
                "Choose broadcast type:",
                reply_markup=await build_broadcast_menu()
            )
            
        elif data == "advanced_settings":
            await query.message.edit_text(
                "**⚙️ Advanced Settings**\n\n"
                "Configure advanced bot features:",
                reply_markup=await build_advanced_settings_menu()
            )
            
        elif data == "cleanup_tools":
            await query.message.edit_text(
                "**🧹 Cleanup Tools**\n\n"
                "⚠️ **Warning:** These tools can affect bot performance.\n"
                "Use with caution!",
                reply_markup=await build_cleanup_tools_menu()
            )
            
        elif data == "cleanup_invalid_tokens":
            await query.message.edit_text("🧹 **Cleaning up invalid tokens...**")
            cleaned = await cleanup_invalid_clones()
            await query.message.edit_text(
                f"✅ **Cleanup completed!**\n\n"
                f"🗑️ Removed {cleaned} invalid clones.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Back", callback_data="cleanup_tools")]
                ])
            )
            
        else:
            await query.answer("🔄 Feature under development!", show_alert=True)
            
    except Exception as e:
        logging.error(f"Error in admin callback: {e}")
        await query.answer("❌ An error occurred. Check logs.", show_alert=True)

async def cleanup_invalid_clones():
    """Clean up clones with invalid tokens"""
    cleaned_count = 0
    try:
        bots = list(bots_collection.find())
        for bot in bots:
            try:
                test_client = Client(
                    name=f"test_{bot['bot_id']}",
                    api_id=config.API_ID,
                    api_hash=config.API_HASH,
                    bot_token=bot['token'],
                    in_memory=True
                )
                await test_client.start()
                await test_client.stop()
            except Exception:
                bots_collection.delete_one({"bot_id": bot['bot_id']})
                cleaned_count += 1
                logging.info(f"Cleaned up invalid clone: @{bot['username']}")
    except Exception as e:
        logging.error(f"Error during cleanup: {e}")
    
    return cleaned_count

# Initialize settings on import
asyncio.create_task(load_global_settings())
