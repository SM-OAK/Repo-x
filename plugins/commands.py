# plugins/commands.py - Enhanced with better integration and auto-delete
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
    messages_collection = mongo_db["messages"]  # For auto-delete tracking
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
        'auto_delete_enabled': getattr(config, 'AUTO_DELETE_ENABLED', False),
        'auto_delete_time': getattr(config, 'AUTO_DELETE_TIME', 300),
        'maintenance_mode': getattr(config, 'MAINTENANCE_MODE', False),
        'welcome_enabled': getattr(config, 'WELCOME_ENABLED', True)
    }

async def schedule_auto_delete(client: Client, message: Message, delete_after_seconds: int):
    """Schedule a message for auto-deletion"""
    async def delete_message():
        try:
            await asyncio.sleep(delete_after_seconds)
            await message.delete()
            # Remove from tracking
            task_key = f"{message.chat.id}_{message.id}"
            if task_key in auto_delete_tasks:
                del auto_delete_tasks[task_key]
        except Exception as e:
            logging.error(f"Auto-delete error: {e}")
    
    # Create task and store reference
    task_key = f"{message.chat.id}_{message.id}"
    task = asyncio.create_task(delete_message())
    auto_delete_tasks[task_key] = task
    
    # Store in database for persistence
    try:
        messages_collection.insert_one({
            "chat_id": message.chat.id,
            "message_id": message.id,
            "delete_at": datetime.now() + timedelta(seconds=delete_after_seconds),
            "created_at": datetime.now()
        })
    except Exception as e:
        logging.error(f"Error storing auto-delete info: {e}")

def get_start_buttons(message):
    """Enhanced start buttons with dynamic features"""
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
    if getattr(config, 'CLONE_MODE', True):
        buttons.append([InlineKeyboardButton('🤖 Create Your Own Clone Bot', callback_data='clone')])
    
    # Add admin panel for admins
    if message.from_user.id in config.ADMINS:
        buttons.append([InlineKeyboardButton("⚙️ Admin Power Panel", callback_data="admin_panel")])
    
    # Add extra features button
    buttons.append([InlineKeyboardButton("🌟 Extra Features", callback_data="extra_features")])
    
    return InlineKeyboardMarkup(buttons)

@Client.on_message(filters.command("start") & filters.private)
async def enhanced_start(client: Client, message: Message):
    """Enhanced start command with auto-delete and user tracking"""
    try:
        # Check maintenance mode
        settings = await get_global_settings()
        if settings.get('maintenance_mode', False) and message.from_user.id not in config.ADMINS:
            maintenance_msg = await message.reply_text(
                "🚧 **Bot is under maintenance!**\n\n"
                "Please try again later.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Retry", callback_data="start")]
                ])
            )
            # Auto-delete maintenance message
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
            if deep_link.startswith("file_"):
                # Handle file requests
                file_id = deep_link.replace("file_", "")
                await handle_file_request(client, message, file_id)
                return
            elif deep_link == "help":
                await show_help(client, message)
                return

        # Send start message
        pics = getattr(config, 'PICS', ['https://telegra.ph/file/f4b8ba5d5c0d0ca4b3a3e.jpg'])
        start_msg = await message.reply_photo(
            photo=random.choice(pics),
            caption=script.START_TXT.format(message.from_user.mention, client.me.mention),
            reply_markup=get_start_buttons(message)
        )

        # Schedule auto-delete if enabled
        if settings.get('auto_delete_enabled', False):
            await schedule_auto_delete(client, start_msg, settings.get('auto_delete_time', 300))

    except Exception as e:
        logging.error(f"Start command error: {e}")
        error_msg = await message.reply_text("❌ An error occurred. Please try again later.")
        await schedule_auto_delete(client, error_msg, 30)

async def handle_file_request(client: Client, message: Message, file_id: str):
    """Handle file requests with auto-delete"""
    try:
        # Get file info from database (assuming you have a files collection)
        # This is a placeholder - implement according to your file storage system
        file_msg = await message.reply_text(
            f"📁 **File Request: {file_id}**\n\n"
            "Processing your request...",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Back to Start", callback_data="start")]
            ])
        )
        
        settings = await get_global_settings()
        if settings.get('auto_delete_enabled', False):
            await schedule_auto_delete(client, file_msg, settings.get('auto_delete_time', 300))
            
    except Exception as e:
        logging.error(f"File request error: {e}")

async def show_help(client: Client, message: Message):
    """Show help with auto-delete"""
    try:
        help_msg = await message.reply_text(
            script.HELP_TXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('⬅️ Back', callback_data='start')],
                [InlineKeyboardButton('🔒 Close', callback_data='close_data')]
            ])
        )
        
        settings = await get_global_settings()
        if settings.get('auto_delete_enabled', False):
            await schedule_auto_delete(client, help_msg, settings.get('auto_delete_time', 300))
            
    except Exception as e:
        logging.error(f"Help command error: {e}")

@Client.on_callback_query(~filters.regex(r"^(toggle_|admin_panel|manage_clones_menu|clone_settings_|set_|broadcast_|advanced_|cleanup_|bot_|user_)"))
async def enhanced_callback_handler(client: Client, query: CallbackQuery):
    """Enhanced callback handler with auto-delete support"""
    data = query.data
    settings = await get_global_settings()
    
    try:
        await query.answer()
        
        if data == "start":
            await query.message.edit_media(
                InputMediaPhoto(
                    media=random.choice(getattr(config, 'PICS', ['https://telegra.ph/file/f4b8ba5d5c0d0ca4b3a3e.jpg'])),
                    caption=script.START_TXT.format(query.from_user.mention, client.me.mention)
                ),
                reply_markup=get_start_buttons(query)
            )
            
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
            if not getattr(config, 'CLONE_MODE', True):
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
            total_users = users_collection.count_documents({})
            total_clones = bots_collection.count_documents({})
            
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
                f"🤖 Total Clones: {total_clones}\n"
                f"⚡ Uptime: {get_uptime()}"
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
            
        elif data == "detailed_stats":
            await show_detailed_stats(client, query)
            
        elif data == "create_clone":
            await query.answer("Use /clone command to create a new clone bot!", show_alert=True)
            
        elif data == "my_clones":
            user_clones = list(bots_collection.find({"user_id": query.from_user.id}))
            if not user_clones:
                await query.answer("You don't have any cloned bots yet!", show_alert=True)
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
            
        elif data == "close_data":
            await query.message.delete()
            
        elif data == "no_action":
            await query.answer("No action available", show_alert=False)
            
        else:
            await query.answer("🔄 Feature coming soon!", show_alert=True)
            
        # Schedule auto-delete for callback responses if enabled
        if settings.get('auto_delete_enabled', False) and data not in ["close_data"]:
            await schedule_auto_delete(client, query.message, settings.get('auto_delete_time', 300))
            
    except Exception as e:
        logging.error(f"Callback handler error: {e}")
        await query.answer("❌ An error occurred!", show_alert=True)

async def show_detailed_stats(client: Client, query: CallbackQuery):
    """Show detailed bot statistics"""
    try:
        # Gather comprehensive stats
        total_users = users_collection.count_documents({})
        total_clones = bots_collection.count_documents({})
        active_clones = bots_collection.count_documents({"active": {"$ne": False}})
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_users = users_collection.count_documents({"last_seen": {"$gte": today}})
        today_clones = bots_collection.count_documents({"created_at": {"$gte": today}})
        
        # Top users by clone count
        pipeline = [
            {"$group": {"_id": "$user_id", "clone_count": {"$sum": 1}}},
            {"$sort": {"clone_count": -1}},
            {"$limit": 5}
        ]
        top_clone_creators = list(bots_collection.aggregate(pipeline))
        
        stats_text = (
            "📊 **Detailed Bot Statistics**\n\n"
            f"👥 **Users:**\n"
            f"• Total: {total_users}\n"
            f"• Active Today: {today_users}\n\n"
            f"🤖 **Clone Bots:**\n"
            f"• Total: {total_clones}\n"
            f"• Active: {active_clones}\n"
            f"• Created Today: {today_clones}\n"
            f"• Success Rate: {(active_clones/total_clones*100):.1f}%\n\n" if total_clones > 0 else ""
            f"🏆 **Top Clone Creators:**\n"
        )
        
        for i, creator in enumerate(top_clone_creators, 1):
            try:
                user = await client.get_users(creator['_id'])
                stats_text += f"{i}. {user.first_name} - {creator['clone_count']} clones\n"
            except:
                stats_text += f"{i}. User {creator['_id']} - {creator['clone_count']} clones\n"
        
        stats_text += f"\n🕐 **Last Updated:** {datetime.now().strftime('%H:%M:%S')}"
        
        await query.message.edit_text(
            stats_text,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('🔄 Refresh', callback_data='detailed_stats')],
                [InlineKeyboardButton('⬅️ Back', callback_data='extra_features')],
                [InlineKeyboardButton('🔒 Close', callback_data='close_data')]
            ])
        )
        
    except Exception as e:
        logging.error(f"Detailed stats error: {e}")
        await query.answer("❌ Error loading stats!", show_alert=True)

def get_uptime():
    """Calculate bot uptime (placeholder)"""
    # You can implement actual uptime calculation here
    return "24h 15m"

# Auto-delete cleanup task
@Client.on_message(filters.command("cleanup_auto_delete") & filters.user(config.ADMINS))
async def cleanup_expired_messages(client: Client, message: Message):
    """Clean up expired auto-delete messages"""
    try:
        now = datetime.now()
        expired_messages = messages_collection.find({"delete_at": {"$lt": now}})
        
        cleaned_count = 0
        for msg_doc in expired_messages:
            try:
                await client.delete_messages(msg_doc['chat_id'], msg_doc['message_id'])
                cleaned_count += 1
            except:
                pass
            messages_collection.delete_one({"_id": msg_doc['_id']})
        
        await message.reply_text(f"✅ Cleaned up {cleaned_count} expired messages.")
        
    except Exception as e:
        logging.error(f"Cleanup error: {e}")
        await message.reply_text("❌ Cleanup failed!")

# User statistics command
@Client.on_message(filters.command("stats") & filters.user(config.ADMINS))
async def user_stats(client: Client, message: Message):
    """Show user statistics"""
    try:
        total_users = users_collection.count_documents({})
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_users = users_collection.count_documents({"last_seen": {"$gte": today}})
        week_ago = datetime.now() - timedelta(days=7)
        week_users = users_collection.count_documents({"last_seen": {"$gte": week_ago}})
        
        stats_msg = await message.reply_text(
            f"📊 **User Statistics**\n\n"
            f"👥 Total Users: {total_users}\n"
            f"📅 Today: {today_users}\n"
            f"📅 This Week: {week_users}\n"
            f"📈 Weekly Growth: {((week_users/total_users)*100):.1f}%" if total_users > 0 else "0%"
        )
        
        settings = await get_global_settings()
        if settings.get('auto_delete_enabled', False):
            await schedule_auto_delete(client, stats_msg, 60)
            
    except Exception as e:
        logging.error(f"Stats error: {e}")
        await message.reply_text("❌ Error getting stats!")

# Broadcast command
@Client.on_message(filters.command("broadcast") & filters.user(config.ADMINS))
async def broadcast_message(client: Client, message: Message):
    """Broadcast message to all users"""
    try:
        if not message.reply_to_message:
            return await message.reply_text("❌ Reply to a message to broadcast it!")
        
        users = users_collection.find({}, {"user_id": 1})
        total_users = users_collection.count_documents({})
        
        broadcast_msg = await message.reply_text(
            f"📢 **Broadcasting to {total_users} users...**\n\n"
            "⏳ Please wait..."
        )
        
        success_count = 0
        failed_count = 0
        
        for user in users:
            try:
                await message.reply_to_message.copy(user['user_id'])
                success_count += 1
            except Exception:
                failed_count += 1
            
            # Update progress every 50 users
            if (success_count + failed_count) % 50 == 0:
                await broadcast_msg.edit_text(
                    f"📢 **Broadcasting...**\n\n"
                    f"✅ Success: {success_count}\n"
                    f"❌ Failed: {failed_count}\n"
                    f"📊 Progress: {((success_count + failed_count)/total_users)*100:.1f}%"
                )
        
        await broadcast_msg.edit_text(
            f"📢 **Broadcast Complete!**\n\n"
            f"✅ Success: {success_count}\n"
            f"❌ Failed: {failed_count}\n"
            f"📊 Success Rate: {(success_count/total_users)*100:.1f}%"
        )
        
    except Exception as e:
        logging.error(f"Broadcast error: {e}")
        await message.reply_text("❌ Broadcast failed!")

# Initialize auto-delete cleanup on startup
async def init_auto_delete_cleanup():
    """Initialize auto-delete cleanup on bot startup"""
    while True:
        try:
            now = datetime.now()
            expired_messages = messages_collection.find({"delete_at": {"$lt": now}})
            
            for msg_doc in expired_messages:
                task_key = f"{msg_doc['chat_id']}_{msg_doc['message_id']}"
                if task_key in auto_delete_tasks:
                    auto_delete_tasks[task_key].cancel()
                    del auto_delete_tasks[task_key]
                
                messages_collection.delete_one({"_id": msg_doc['_id']})
            
            await asyncio.sleep(300)  # Check every 5 minutes
            
        except Exception as e:
            logging.error(f"Auto-delete cleanup error: {e}")
            await asyncio.sleep(300)

# Start cleanup task
asyncio.create_task(init_auto_delete_cleanup())
