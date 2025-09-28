# plugins/commands.py - Fixed start menu integration
import random
import asyncio
import logging
from datetime import datetime, timedelta
from Script import script
from pyrogram import Client, filters
from pyrogram.types import *
from pymongo import MongoClient
import config

# Initialize MongoDB
try:
    mongo_client = MongoClient(config.DB_URI)
    mongo_db = mongo_client["cloned_vjbotz"]
    bots_collection = mongo_db["bots"]
    users_collection = mongo_db["users"]
    settings_collection = mongo_db["settings"]
    messages_collection = mongo_db["messages"]
    logging.info("MongoDB initialized in commands.py")
except Exception as e:
    logging.error(f"MongoDB initialization failed: {e}")

# Auto-delete message tracker
auto_delete_tasks = {}

async def get_global_settings():
    """Get global settings from database"""
    try:
        settings = settings_collection.find_one({"type": "global"})
        if settings:
            return settings.get('data', {})
    except Exception:
        pass
    
    return {
        'link_generation': getattr(config, 'LINK_GENERATION_MODE', True),
        'public_file_store': getattr(config, 'PUBLIC_FILE_STORE', True),
        'auto_delete_enabled': getattr(config, 'AUTO_DELETE_ENABLED', False),
        'auto_delete_time': getattr(config, 'AUTO_DELETE_TIME', 300),
        'maintenance_mode': getattr(config, 'MAINTENANCE_MODE', False),
        'clone_mode': getattr(config, 'CLONE_MODE', True),
        'welcome_enabled': getattr(config, 'WELCOME_ENABLED', True)
    }

async def schedule_auto_delete(client: Client, message: Message, delete_after_seconds: int):
    """Schedule a message for auto-deletion"""
    async def delete_message():
        try:
            await asyncio.sleep(delete_after_seconds)
            await message.delete()
            task_key = f"{message.chat.id}_{message.id}"
            if task_key in auto_delete_tasks:
                del auto_delete_tasks[task_key]
        except Exception as e:
            logging.error(f"Auto-delete error: {e}")
    
    task_key = f"{message.chat.id}_{message.id}"
    task = asyncio.create_task(delete_message())
    auto_delete_tasks[task_key] = task

def get_start_buttons(user_id, settings=None):
    """Get start menu buttons with proper admin integration"""
    if settings is None:
        settings = {}
    
    buttons = [
        [InlineKeyboardButton('💝 Subscribe My YouTube Channel', url='https://youtube.com/@Tech_VJ')],
        [
            InlineKeyboardButton('🔍 Support Group', url='https://t.me/vj_bot_disscussion'),
            InlineKeyboardButton('🤖 Update Channel', url='https://t.me/vj_botz')
        ],
        [
            InlineKeyboardButton('💁‍♀️ Help', callback_data='help'),
            InlineKeyboardButton('😊 About', callback_data='about')
        ]
    ]
    
    # Add clone button if clone mode is enabled
    if settings.get('clone_mode', getattr(config, 'CLONE_MODE', True)):
        buttons.append([InlineKeyboardButton('🤖 Create Your Own Clone Bot', callback_data='clone')])
    
    # Add admin controls for admins
    if user_id in config.ADMINS:
        # Link generation toggle
        link_status = "🟢 ON" if settings.get('link_generation', True) else "🔴 OFF"
        buttons.append([
            InlineKeyboardButton(f"Toggle Links: {link_status}", callback_data="toggle_links")
        ])
        
        # Admin panel button
        buttons.append([
            InlineKeyboardButton("⚙️ Admin Power Panel", callback_data="admin_panel")
        ])
    
    # Add extra features button for all users
    buttons.append([InlineKeyboardButton("🌟 Extra Features", callback_data="extra_features")])
    
    return InlineKeyboardMarkup(buttons)

@Client.on_message(filters.command("start") & filters.private)
async def enhanced_start(client: Client, message: Message):
    """Enhanced start command with proper integration"""
    try:
        # Get current settings
        settings = await get_global_settings()
        
        # Check maintenance mode
        if settings.get('maintenance_mode', False) and message.from_user.id not in config.ADMINS:
            maintenance_msg = await message.reply_text(
                "🚧 **Bot is under maintenance!**\n\n"
                "Please try again later.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Retry", callback_data="start")]
                ])
            )
            if settings.get('auto_delete_enabled', False):
                await schedule_auto_delete(client, maintenance_msg, settings.get('auto_delete_time', 300))
            return

        # Track user
        try:
            users_collection.update_one(
                {"user_id": message.from_user.id},
                {
                    "$set": {
                        "first_name": message.from_user.first_name,
                        "username": message.from_user.username,
                        "last_seen": datetime.now()
                    },
                    "$inc": {"start_count": 1}
                },
                upsert=True
            )
        except Exception as e:
            logging.error(f"User tracking error: {e}")

        # Handle deep links
        if len(message.command) > 1:
            deep_link = message.command[1]
            
            # File access link
            if deep_link.startswith("file_"):
                file_id = deep_link.replace("file_", "")
                
                # Check if link generation is enabled for main bot
                if not settings.get('link_generation', True):
                    bot_id = (await client.get_me()).id
                    if bot_id == getattr(config, 'OWNER_BOT_ID', 0):
                        await message.reply_text(
                            "❌ **File access is currently disabled on the main bot.**\n\n"
                            "Please contact admin or try again later.",
                            reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton("⬅️ Back to Start", callback_data="start")]
                            ])
                        )
                        return
                
                await handle_file_request(client, message, file_id, settings)
                return
                
            elif deep_link == "help":
                await show_help(client, message, settings)
                return

        # Send main start message
        pics = getattr(config, 'PICS', ['https://telegra.ph/file/f4b8ba5d5c0d0ca4b3a3e.jpg'])
        start_msg = await message.reply_photo(
            photo=random.choice(pics),
            caption=script.START_TXT.format(message.from_user.mention, client.me.mention),
            reply_markup=get_start_buttons(message.from_user.id, settings)
        )

        # Schedule auto-delete if enabled
        if settings.get('auto_delete_enabled', False):
            await schedule_auto_delete(client, start_msg, settings.get('auto_delete_time', 300))

    except Exception as e:
        logging.error(f"Start command error: {e}")
        error_msg = await message.reply_text(
            "❌ **An error occurred while starting the bot.**\n\n"
            "Please try again with /start",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Retry", callback_data="start")]
            ])
        )
        await schedule_auto_delete(client, error_msg, 30)

async def handle_file_request(client: Client, message: Message, file_id: str, settings: dict):
    """Handle file requests with proper error handling"""
    try:
        # This is a placeholder for your file handling logic
        file_msg = await message.reply_text(
            f"📁 **Processing File Request**\n\n"
            f"File ID: `{file_id}`\n"
            "Please wait while we retrieve your file...",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Back to Start", callback_data="start")]
            ])
        )
        
        if settings.get('auto_delete_enabled', False):
            await schedule_auto_delete(client, file_msg, settings.get('auto_delete_time', 300))
            
    except Exception as e:
        logging.error(f"File request error: {e}")
        await message.reply_text(
            "❌ **Error accessing file.**\n\n"
            "Please try again later or contact support.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Back to Start", callback_data="start")]
            ])
        )

async def show_help(client: Client, message: Message, settings: dict):
    """Show help with proper formatting"""
    try:
        help_msg = await message.reply_text(
            script.HELP_TXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('⬅️ Back', callback_data='start')],
                [InlineKeyboardButton('🔒 Close', callback_data='close_data')]
            ])
        )
        
        if settings.get('auto_delete_enabled', False):
            await schedule_auto_delete(client, help_msg, settings.get('auto_delete_time', 300))
            
    except Exception as e:
        logging.error(f"Help command error: {e}")

@Client.on_callback_query()
async def unified_callback_handler(client: Client, query: CallbackQuery):
    """Unified callback handler for all bot functions"""
    data = query.data
    user_id = query.from_user.id
    
    try:
        # Get current settings
        settings = await get_global_settings()
        
        # Handle admin-only callbacks first
        if data in ["admin_panel", "toggle_links", "toggle_public", "toggle_auto_delete", 
                   "toggle_maintenance", "toggle_clone_mode", "manage_clones_menu", 
                   "broadcast_menu", "advanced_settings", "cleanup_tools"] and user_id not in config.ADMINS:
            await query.answer("❌ This feature is only available for admins!", show_alert=True)
            return
        
        await query.answer()
        
        # Main menu callbacks
        if data == "start":
            pics = getattr(config, 'PICS', ['https://telegra.ph/file/f4b8ba5d5c0d0ca4b3a3e.jpg'])
            await query.message.edit_media(
                InputMediaPhoto(
                    media=random.choice(pics),
                    caption=script.START_TXT.format(query.from_user.mention, client.me.mention)
                ),
                reply_markup=get_start_buttons(user_id, settings)
            )
            
        elif data == "toggle_links" and user_id in config.ADMINS:
            # Toggle link generation setting
            settings['link_generation'] = not settings.get('link_generation', True)
            config.LINK_GENERATION_MODE = settings['link_generation']
            
            # Save to database
            try:
                settings_collection.update_one(
                    {"type": "global"},
                    {"$set": {"data": settings, "updated_at": datetime.now()}},
                    upsert=True
                )
            except Exception as e:
                logging.error(f"Error saving settings: {e}")
            
            # Update the menu
            await query.message.edit_reply_markup(get_start_buttons(user_id, settings))
            
        elif data == "help":
            await query.message.edit_text(
                script.HELP_TXT,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('⬅️ Back', callback_data='start')],
                    [InlineKeyboardButton('🔒 Close', callback_data='close_data')]
                ])
            )
            
        elif data == "about":
            await query.message.edit_text(
                script.ABOUT_TXT.format(client.me.mention),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('⬅️ Back', callback_data='start')],
                    [InlineKeyboardButton('🔒 Close', callback_data='close_data')]
                ])
            )
            
        elif data == "clone":
            if not settings.get('clone_mode', True):
                await query.answer("🚫 Clone feature is currently disabled!", show_alert=True)
                return
                
            await query.message.edit_text(
                script.CLONE_TXT.format(query.from_user.mention),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('🤖 Create Clone Now', callback_data='create_clone')],
                    [InlineKeyboardButton('📋 My Clones', callback_data='my_clones')],
                    [InlineKeyboardButton('⬅️ Back', callback_data='start')],
                    [InlineKeyboardButton('🔒 Close', callback_data='close_data')]
                ])
            )
            
        elif data == "extra_features":
            try:
                total_users = users_collection.count_documents({})
                total_clones = bots_collection.count_documents({})
            except:
                total_users = "N/A"
                total_clones = "N/A"
            
            features_text = (
                "🌟 **Extra Features**\n\n"
                "🔥 **Available Features:**\n"
                "• 🤖 Clone Bot Creation\n"
                "• 🗑️ Auto Message Delete\n"
                "• 📊 Real-time Statistics\n"
                "• 🔗 Smart Link Generation\n"
                "• 📢 Broadcast System\n"
                "• 🛡️ Advanced Security\n\n"
                f"📈 **Live Stats:**\n"
                f"👥 Total Users: {total_users}\n"
                f"🤖 Total Clones: {total_clones}"
            )
            
            await query.message.edit_text(
                features_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('📊 Detailed Stats', callback_data='detailed_stats')],
                    [InlineKeyboardButton('🤖 Create Clone', callback_data='clone')],
                    [InlineKeyboardButton('⬅️ Back', callback_data='start')],
                    [InlineKeyboardButton('🔒 Close', callback_data='close_data')]
                ])
            )
            
        elif data == "create_clone":
            await query.answer("Use /clone command to create a new clone bot!", show_alert=True)
            
        elif data == "my_clones":
            try:
                user_clones = list(bots_collection.find({"user_id": user_id}))
                if not user_clones:
                    await query.answer("You don't have any cloned bots yet! Use /clone to create one.", show_alert=True)
                    return
                    
                clones_text = f"🤖 **Your Cloned Bots ({len(user_clones)})**\n\n"
                for i, bot in enumerate(user_clones, 1):
                    status = "🟢 Active" if bot.get('active', True) else "🔴 Inactive"
                    clones_text += f"{i}. **{bot['name']}** (@{bot['username']}) - {status}\n"
                
                await query.message.edit_text(
                    clones_text,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton('🛠️ Manage Clones', callback_data='manage_my_clones')],
                        [InlineKeyboardButton('⬅️ Back', callback_data='extra_features')],
                        [InlineKeyboardButton('🔒 Close', callback_data='close_data')]
                    ])
                )
            except Exception as e:
                logging.error(f"My clones error: {e}")
                await query.answer("Error loading your clones!", show_alert=True)
                
        elif data == "close_data":
            await query.message.delete()
            
        # Admin panel integration
        elif data == "admin_panel" and user_id in config.ADMINS:
            # Import and call the admin panel from power.py
            from plugins.power import enhanced_admin_callbacks
            await enhanced_admin_callbacks(client, query)
            return
            
        # Handle other admin callbacks by delegating to power.py
        elif (data.startswith(("toggle_", "manage_", "clone_", "set_", "broadcast_", 
                            "advanced_", "cleanup_", "bot_", "user_")) and user_id in config.ADMINS):
            from plugins.power import enhanced_admin_callbacks
            await enhanced_admin_callbacks(client, query)
            return
            
        else:
            await query.answer("🔄 Feature under development!", show_alert=True)
            
        # Schedule auto-delete for callback responses if enabled
        if settings.get('auto_delete_enabled', False) and data not in ["close_data"]:
            await schedule_auto_delete(client, query.message, settings.get('auto_delete_time', 300))
            
    except Exception as e:
        logging.error(f"Callback handler error: {e}")
        await query.answer("❌ An error occurred!", show_alert=True)

# Command handlers
@Client.on_message(filters.command(["enable_links", "disable_links"]) & filters.user(config.ADMINS))
async def toggle_links_command(client: Client, message: Message):
    """Command to toggle link generation"""
    try:
        settings = await get_global_settings()
        command = message.command[0].lower()
        
        if command == "enable_links":
            if settings.get('link_generation', True):
                await message.reply("✅ Link generation is already enabled.")
            else:
                settings['link_generation'] = True
                config.LINK_GENERATION_MODE = True
                # Save to database
                settings_collection.update_one(
                    {"type": "global"},
                    {"$set": {"data": settings, "updated_at": datetime.now()}},
                    upsert=True
                )
                await message.reply("✅ Link generation has been **enabled** for the main bot.")
        else:  # disable_links
            if not settings.get('link_generation', True):
                await message.reply("❌ Link generation is already disabled.")
            else:
                settings['link_generation'] = False
                config.LINK_GENERATION_MODE = False
                # Save to database
                settings_collection.update_one(
                    {"type": "global"},
                    {"$set": {"data": settings, "updated_at": datetime.now()}},
                    upsert=True
                )
                await message.reply("❌ Link generation has been **disabled** for the main bot.")
                
    except Exception as e:
        logging.error(f"Toggle links command error: {e}")
        await message.reply("❌ Error updating link settings!")

# Stats command
@Client.on_message(filters.command("stats") & filters.user(config.ADMINS))
async def user_stats(client: Client, message: Message):
    """Show user statistics"""
    try:
        total_users = users_collection.count_documents({})
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_users = users_collection.count_documents({"last_seen": {"$gte": today}})
        week_ago = datetime.now() - timedelta(days=7)
        week_users = users_collection.count_documents({"last_seen": {"$gte": week_ago}})
        
        total_clones = bots_collection.count_documents({})
        active_clones = bots_collection.count_documents({"active": {"$ne": False}})
        
        settings = await get_global_settings()
        
        stats_msg = await message.reply_text(
            f"📊 **Bot Statistics**\n\n"
            f"👥 **Users:**\n"
            f"• Total: {total_users}\n"
            f"• Today: {today_users}\n"
            f"• This Week: {week_users}\n\n"
            f"🤖 **Clones:**\n"
            f"• Total: {total_clones}\n"
            f"• Active: {active_clones}\n\n"
            f"⚙️ **Settings:**\n"
            f"• Links: {'🟢 ON' if settings.get('link_generation', True) else '🔴 OFF'}\n"
            f"• Clone Mode: {'🟢 ON' if settings.get('clone_mode', True) else '🔴 OFF'}\n"
            f"• Auto Delete: {'🟢 ON' if settings.get('auto_delete_enabled', False) else '🔴 OFF'}"
        )
        
        if settings.get('auto_delete_enabled', False):
            await schedule_auto_delete(client, stats_msg, 60)
            
    except Exception as e:
        logging.error(f"Stats error: {e}")
        await message.reply_text("❌ Error getting stats!")

# Initialize settings on startup
async def initialize_settings():
    """Initialize default settings if they don't exist"""
    try:
        existing_settings = settings_collection.find_one({"type": "global"})
        if not existing_settings:
            default_settings = await get_global_settings()
            settings_collection.insert_one({
                "type": "global",
                "data": default_settings,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            })
            logging.info("Default settings initialized")
    except Exception as e:
        logging.error(f"Settings initialization error: {e}")

# Call initialization
import asyncio
asyncio.create_task(initialize_settings())
