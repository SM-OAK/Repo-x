# plugins/clone.py - Enhanced clone system with advanced features
import re
import asyncio
import logging
import random
from pymongo import MongoClient
from Script import script
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import AccessTokenExpired, AccessTokenInvalid, UserDeactivated, UserIsBlocked
import config
from plugins.power import ask_for_input
from datetime import datetime, timedelta

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Initialize MongoDB
try:
    mongo_client = MongoClient(config.DB_URI)
    mongo_db = mongo_client["cloned_vjbotz"]
    bots_collection = mongo_db["bots"]
    users_collection = mongo_db["users"]
    analytics_collection = mongo_db["analytics"]
    logging.info("MongoDB initialized in clone.py")
except Exception as e:
    logging.error(f"MongoDB initialization failed in clone.py: {e}")
    mongo_client = None

# Active clone clients storage
active_clones = {}

class CloneBot:
    """Enhanced clone bot class with advanced features"""
    
    def __init__(self, bot_data):
        self.bot_data = bot_data
        self.client = None
        self.is_active = False
        # Load stats from DB or initialize
        self.stats = bot_data.get('stats', {
            'messages_sent': 0,
            'files_shared': 0,
            'users_served': 0,
            'last_activity': datetime.now()
        })

    async def start_clone(self):
        """Start the clone bot"""
        try:
            self.client = Client(
                name=f"clone_{self.bot_data['bot_id']}",
                api_id=config.API_ID,
                api_hash=config.API_HASH,
                bot_token=self.bot_data['token'],
                in_memory=True
            )
            
            await self.client.start()
            self.is_active = True
            
            # Set up clone bot handlers
            self.setup_handlers()
            
            # Update database status
            bots_collection.update_one(
                {"bot_id": self.bot_data['bot_id']},
                {"$set": {"active": True, "last_started": datetime.now()}}
            )
            
            logging.info(f"Clone bot @{self.bot_data['username']} started successfully")
            return True
            
        except (AccessTokenExpired, AccessTokenInvalid, UserDeactivated) as token_err:
            logging.error(f"Token invalid for @{self.bot_data['username']}: {token_err}. Deactivating.")
            await self.stop_clone(deactivated=True)
            return False
        except Exception as e:
            logging.error(f"Failed to start clone @{self.bot_data['username']}: {e}")
            self.is_active = False
            return False

    async def stop_clone(self, deactivated=False):
        """Stop the clone bot and save stats"""
        try:
            if self.client and self.is_active:
                await self.client.stop()
            
            self.is_active = False
                
            update_fields = {
                "active": False,
                "last_stopped": datetime.now(),
                "stats": self.stats
            }
            if deactivated:
                update_fields["deactivated"] = True

            bots_collection.update_one(
                {"bot_id": self.bot_data['bot_id']},
                {"$set": update_fields}
            )
            
            logging.info(f"Clone bot @{self.bot_data['username']} stopped")
            
        except Exception as e:
            logging.error(f"Error stopping clone @{self.bot_data['username']}: {e}")

    def setup_handlers(self):
        """Set up message handlers for the clone bot"""
        
        @self.client.on_message(filters.command("start") & filters.private)
        async def clone_start(client, message):
            try:
                # Update user stats for the clone
                users_collection.update_one(
                    {"user_id": message.from_user.id, "bot_id": client.me.id},
                    {
                        "$set": {
                            "first_name": message.from_user.first_name,
                            "username": message.from_user.username,
                            "last_seen": datetime.now()
                        },
                        "$inc": {"interactions": 1}
                    },
                    upsert=True
                )
                
                # Update clone stats
                self.stats['users_served'] = users_collection.count_documents({"bot_id": client.me.id})
                self.stats['last_activity'] = datetime.now()
                
                # Get custom start message or use default
                custom_msg = self.bot_data.get('custom_start_message')
                start_text = (custom_msg or script.START_TXT).format(
                    mention=message.from_user.mention,
                    first_name=message.from_user.first_name,
                    bot_mention=f"@{client.me.username}"
                )
                
                buttons = [
                    [InlineKeyboardButton('💝 Subscribe YouTube', url='https://youtube.com/@Tech_VJ')],
                    [
                        InlineKeyboardButton('🔍 Support', url='https://t.me/vj_bot_disscussion'),
                        InlineKeyboardButton('🤖 Updates', url='https://t.me/vj_botz')
                    ],
                    [
                        InlineKeyboardButton('💁‍♀️ Help', callback_data='help'),
                        InlineKeyboardButton('😊 About', callback_data='about')
                    ],
                    [InlineKeyboardButton('📊 Bot Stats', callback_data='clone_stats')]
                ]
                
                await message.reply_photo(
                    photo=random.choice(getattr(config, 'PICS', ['https://telegra.ph/file/f4b8ba5d5c0d0ca4b3a3e.jpg'])),
                    caption=start_text,
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
                
                self.stats['messages_sent'] += 1
                
            except UserIsBlocked:
                logging.warning(f"User {message.from_user.id} has blocked @{client.me.username}")
            except Exception as e:
                logging.error(f"Clone start handler error for @{client.me.username}: {e}")
        
        @self.client.on_callback_query()
        async def clone_callbacks(client, query):
            try:
                data = query.data
                
                if data == "help":
                    await query.message.edit_text(
                        script.HELP_TXT.format(bot_name=client.me.first_name),
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('⬅️ Back', callback_data='back_to_start')]])
                    )
                elif data == "about":
                    created_date = self.bot_data.get('created_at')
                    created_str = created_date.strftime('%Y-%m-%d') if created_date else 'Unknown'
                    await query.message.edit_text(
                        script.ABOUT_TXT.format(
                            bot_name=client.me.first_name,
                            bot_username=client.me.username,
                            bot_id=client.me.id,
                            created=created_str,
                            owner_id=self.bot_data['user_id'],
                            messages=self.stats['messages_sent'],
                            files=self.stats['files_shared'],
                            users=self.stats['users_served']
                        ),
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('⬅️ Back', callback_data='back_to_start')]])
                    )
                elif data == "clone_stats":
                    await self.show_clone_stats(client, query)
                elif data == "back_to_start":
                    custom_msg = self.bot_data.get('custom_start_message')
                    start_text = (custom_msg or script.START_TXT).format(
                        mention=query.from_user.mention,
                        first_name=query.from_user.first_name,
                        bot_mention=f"@{client.me.username}"
                    )
                    buttons = [
                        [InlineKeyboardButton('💝 Subscribe YouTube', url='https://youtube.com/@Tech_VJ')],
                        [InlineKeyboardButton('🔍 Support', url='https://t.me/vj_bot_disscussion'), InlineKeyboardButton('🤖 Updates', url='https://t.me/vj_botz')],
                        [InlineKeyboardButton('💁‍♀️ Help', callback_data='help'), InlineKeyboardButton('😊 About', callback_data='about')],
                        [InlineKeyboardButton('📊 Bot Stats', callback_data='clone_stats')]
                    ]
                    await query.message.edit_caption(
                        caption=start_text,
                        reply_markup=InlineKeyboardMarkup(buttons)
                    )
                await query.answer()
            except Exception as e:
                logging.error(f"Clone callback error for @{client.me.username}: {e}")
        
        @self.client.on_message(filters.private & (filters.document | filters.video | filters.audio | filters.photo))
        async def handle_files(client, message):
            try:
                # Placeholder for file handling logic. For now, just acknowledge.
                await message.reply_text("Thanks for the file! File sharing logic will be implemented here.")

                self.stats['files_shared'] += 1
                self.stats['messages_sent'] += 1
                self.stats['last_activity'] = datetime.now()
            except Exception as e:
                logging.error(f"File handler error for @{client.me.username}: {e}")

    async def show_clone_stats(self, client, query):
        """Show detailed clone statistics"""
        try:
            last_started = self.bot_data.get('last_started', datetime.now())
            uptime = datetime.now() - last_started
            uptime_str = str(timedelta(seconds=int(uptime.total_seconds())))
            
            stats_text = (
                f"📊 **@{client.me.username} Statistics**\n\n"
                f"**Performance:**\n"
                f"📤 Messages Sent: `{self.stats['messages_sent']}`\n"
                f"📁 Files Shared: `{self.stats['files_shared']}`\n"
                f"👥 Total Users: `{self.stats['users_served']}`\n"
                f"🕐 Uptime: `{uptime_str}`\n\n"
                f"**Status:** {'🟢 Online' if self.is_active else '🔴 Offline'}\n"
                f"**Last Activity:** `{self.stats['last_activity'].strftime('%Y-%m-%d %H:%M:%S')}`"
            )
            
            await query.message.edit_text(
                stats_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton('🔄 Refresh', callback_data='clone_stats')],
                    [InlineKeyboardButton('⬅️ Back', callback_data='back_to_start')]
                ])
            )
        except Exception as e:
            logging.error(f"Clone stats error: {e}")
            await query.answer("❌ Error loading stats!", show_alert=True)

async def restart_all_clones():
    """Function to start all active clones from the database on main bot startup."""
    if mongo_client:
        logging.info("Restarting all active clones...")
        active_bots_cursor = bots_collection.find({"active": True, "deactivated": {"$ne": True}})
        active_bots_list = list(active_bots_cursor)
        count = 0
        for bot_data in active_bots_list:
            clone_bot = CloneBot(bot_data)
            success = await clone_bot.start_clone()
            if success:
                active_clones[bot_data['bot_id']] = clone_bot
                count += 1
        logging.info(f"Successfully restarted {count}/{len(active_bots_list)} active clones.")
    else:
        logging.warning("Cannot restart clones: No MongoDB connection.")

@Client.on_message(filters.command("clone") & filters.private)
async def enhanced_clone_creation(client: Client, message: Message):
    """Enhanced clone creation with better validation and features"""
    user_id = message.from_user.id
    
    # Check user's clone limit
    user_clone_count = bots_collection.count_documents({"user_id": user_id})
    max_clones = 5 if user_id not in getattr(config, 'ADMINS', []) else 50
    
    if user_clone_count >= max_clones:
        return await message.reply_text(
            f"❌ **Clone Limit Reached!**\n\nYou have reached the maximum limit of **{max_clones}** clones.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 My Clones", callback_data="my_clones")]])
        )
    
    ask_text = "🤖 **Forward Bot Token**\nPlease forward the message from @BotFather that contains your new bot's token."
    bot_token_msg = await ask_for_input(client, user_id, ask_text, timeout=300)
    
    if not bot_token_msg:
        return
    
    if not (bot_token_msg.forward_from and bot_token_msg.forward_from.id == 93372553):
        return await bot_token_msg.reply_text(
            '❌ **Invalid Message**\nPlease forward the message directly from @BotFather.',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Try Again", callback_data="clone")]])
        )
    
    try:
        token_pattern = r'(\d{8,10}:[a-zA-Z0-9_-]{35})'
        bot_token = re.search(token_pattern, bot_token_msg.text).group(1)
    except (AttributeError, IndexError):
        return await bot_token_msg.reply_text(
            '❌ **Invalid Token Format**\nCould not find a valid bot token.',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Try Again", callback_data="clone")]])
        )
    
    progress_msg = await bot_token_msg.reply_text("🔄 *Validating token and creating your bot...*")
    
    if bots_collection.find_one({"token": bot_token}):
        return await progress_msg.edit_text("❌ **Bot Already Cloned**\nThis bot token is already in use.")

    try:
        cloned_client = Client(name=f"temp_clone_{user_id}", api_id=config.API_ID, api_hash=config.API_HASH, bot_token=bot_token, in_memory=True)
        await cloned_client.start()
        bot_info = await cloned_client.get_me()
        await cloned_client.stop()
        
        if bots_collection.find_one({"bot_id": bot_info.id}):
            return await progress_msg.edit_text("❌ **Duplicate Bot Detected**\nThis bot has already been cloned.")
        
        bot_details = {
            'bot_id': bot_info.id, 'user_id': user_id, 'name': bot_info.first_name,
            'token': bot_token, 'username': bot_info.username, 'created_at': datetime.now(),
            'last_started': datetime.now(), 'active': True,
            'stats': {'messages_sent': 0, 'files_shared': 0, 'users_served': 0, 'last_activity': datetime.now()}
        }
        bots_collection.insert_one(bot_details)
        
        clone_bot = CloneBot(bot_details)
        if await clone_bot.start_clone():
            active_clones[bot_info.id] = clone_bot
            await progress_msg.edit_text(
                f"✅ **Clone Bot @{bot_info.username} Created Successfully!**",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"🚀 Open Bot", url=f"https://t.me/{bot_info.username}")],
                    [InlineKeyboardButton("📋 My Clones", callback_data="my_clones")]
                ])
            )
        else:
            bots_collection.delete_one({"bot_id": bot_info.id})
            await progress_msg.edit_text("❌ **Failed to Start Clone Bot**\nThe token might be invalid or revoked.")
            
    except (AccessTokenExpired, AccessTokenInvalid):
        await progress_msg.edit_text("❌ **Invalid or Expired Token**\nPlease get a new token from @BotFather.")
    except Exception as e:
        logging.error(f"Clone creation error: {e}")
        await progress_msg.edit_text(f"❌ **An Unexpected Error Occurred**\n`{e}`")

@Client.on_message(filters.command("deletecloned") & filters.private)
async def enhanced_delete_clone(client: Client, message: Message):
    """Enhanced clone deletion with confirmation and cleanup"""
    user_id = message.from_user.id
    user_clones = list(bots_collection.find({"user_id": user_id}))
    
    if not user_clones:
        return await message.reply_text("❌ **No Cloned Bots Found**")
    
    clone_buttons = []
    for bot in user_clones:
        status = "🟢" if bot.get('active', False) else "🔴"
        clone_buttons.append([InlineKeyboardButton(f"{status} @{bot['username']}", callback_data=f"delete_confirm_{bot['bot_id']}")])
    
    clone_buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="start")])
    await message.reply_text("🗑️ **Select a clone bot to delete:**", reply_markup=InlineKeyboardMarkup(clone_buttons))

@Client.on_callback_query(filters.regex(r"^delete_confirm_"))
async def confirm_clone_deletion(client: Client, query):
    """Handle clone deletion confirmation"""
    bot_id = int(query.data.split("_")[2])
    bot_details = bots_collection.find_one({"bot_id": bot_id, "user_id": query.from_user.id})
    
    if not bot_details:
        return await query.answer("❌ Bot not found or you are not the owner!", show_alert=True)
    
    await query.message.edit_text(
        f"⚠️ **Confirm Deletion**\n\nAre you sure you want to delete **@{bot_details['username']}**?\nThis action cannot be undone!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Yes, Delete", callback_data=f"delete_final_{bot_id}")],
            [InlineKeyboardButton("❌ No, Cancel", callback_data="my_clones")]
        ])
    )

@Client.on_callback_query(filters.regex(r"^delete_final_"))
async def final_clone_deletion(client: Client, query):
    """Perform the final deletion of the clone bot"""
    await query.message.edit_text("🗑️ *Deleting bot...*")
    bot_id = int(query.data.split("_")[2])
    
    bot_details = bots_collection.find_one({"bot_id": bot_id, "user_id": query.from_user.id})
    if not bot_details:
        return await query.message.edit_text("❌ **Error:** Bot not found or you are not the owner.")
    
    # Stop the clone if it's running
    if bot_id in active_clones:
        await active_clones[bot_id].stop_clone()
        del active_clones[bot_id]
        logging.info(f"Stopped and removed active clone session for bot ID {bot_id}")

    # Delete from database
    result = bots_collection.delete_one({"bot_id": bot_id})
    
    if result.deleted_count > 0:
        await query.message.edit_text(f"✅ **Success!** Bot **@{bot_details['username']}** has been deleted.")
    else:
        await query.message.edit_text("❌ **Error:** Could not delete the bot from the database.")

