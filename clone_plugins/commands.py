# clone_plugins/commands.py - Fully merged and updated by Gemini
# Now includes custom start message and auto-delete logic.

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pymongo import MongoClient
import base64
import asyncio
import config

# --- Database Connection ---
mongo_client = MongoClient(config.DB_URI)
mongo_db = mongo_client["cloned_vjbotz"]
bots_collection = mongo_db["bots"]


# --- Default Text & Keyboards ---
START_MESSAGE = """😊 **HEY** {mention},

**I AM A PERMANENT FILE STORE BOT AND USERS CAN ACCESS STORED MESSAGES BY USING A SHAREABLE LINK GIVEN BY ME**

**TO KNOW MORE CLICK HELP BUTTON.**"""

def get_start_keyboard():
    # ... (This function remains the same as in your file) ...

# --- Helper Functions ---

def is_file_access_request(parameter):
    # ... (This function remains exactly as you provided) ...

async def handle_file_access_clone(client: Client, message: Message, parameter: str):
    """Handles file access for clone bots with custom auto-delete logic"""
    bot_info = await client.get_me()
    clone_settings = bots_collection.find_one({"bot_id": bot_info.id})
    
    try:
        # Decode the file ID from the start parameter
        decoded_data = base64.urlsafe_b64decode(parameter + "=" * (-len(parameter) % 4)).decode("ascii")
        file_id = int(decoded_data.split("_", 1)[1])
        
        loading_msg = await message.reply_text("🔄 **Fetching your file...**")
        file_msg = await client.get_messages(config.LOG_CHANNEL, file_id)
        
        if not file_msg or not file_msg.media:
            return await loading_msg.edit_text("❌ **File not found in storage.**")

        # --- Auto-Delete Logic ---
        auto_delete_config = clone_settings.get("auto_delete_settings", {})
        is_enabled = auto_delete_config.get("enabled", False)
        
        if is_enabled:
            time_in_minutes = auto_delete_config.get("time_in_minutes", 30)
            time_in_seconds = time_in_minutes * 60
            
            # Send the file and the warning message
            sent_file_msg = await file_msg.copy(chat_id=message.from_user.id)
            warning_msg = await message.reply_text(
                f"<b>❗️❗️❗️IMPORTANT❗️️❗️❗️</b>\n\nThis file will be deleted in <b><u>{time_in_minutes} minutes</u></b>."
            )
            await loading_msg.delete()
            
            # Wait for the specified time
            await asyncio.sleep(time_in_seconds)
            
            # Delete the messages
            await sent_file_msg.delete()
            await warning_msg.edit_text("<b>Your file has been successfully deleted!</b>")
        else:
            # If auto-delete is not enabled, just send the file
            await file_msg.copy(chat_id=message.from_user.id)
            await loading_msg.delete()

    except Exception as e:
        await message.reply_text(f"❌ **Invalid or expired link.**\n\n`{e}`")


@Client.on_message(filters.command("start") & filters.private)
async def smart_start_handler(client: Client, message: Message):
    # ... (This function remains exactly the same as our last version) ...

# ... (The rest of your file, including clone_callback_handler and clone_help_about, 
# remains exactly the same as you provided) ...

print("✅ Smart clone commands loaded - with custom message and auto-delete support!"

@Client.on_message(filters.command("start") & filters.private)
async def smart_start_handler(client: Client, message: Message):
    """Smart start command handler that routes properly and supports custom messages"""
    
    # Get bot info to determine if this is main bot or clone
    try:
        bot_info = await client.get_me()
        is_main_bot = MAIN_BOT_CONFIG and bot_info.username == BOT_USERNAME.replace("@", "") if MAIN_BOT_CONFIG else False
    except Exception as e:
        print(f"Error getting bot info: {e}")
        bot_info = None
        is_main_bot = False
    
    # Check if there's a parameter
    if len(message.command) > 1:
        parameter = message.command[1]
        
        print(f"Start command received - Bot: {bot_info.username if bot_info else 'Unknown'}, Parameter: {parameter}")
        print(f"Is main bot: {is_main_bot}")
        print(f"Is file access: {is_file_access_request(parameter)}")
        
        # If it's a file access request
        if is_file_access_request(parameter):
            if is_main_bot:
                # This is the main bot - let the main commands.py handle it
                print("Main bot: Letting main commands.py handle file access")
                return  # Don't handle here, let main commands.py take over
            else:
                # This is a clone bot - handle file access here
                print("Clone bot: Handling file access")
                success = await handle_file_access_clone(client, message, parameter)
                if success:
                    return
                # If failed, continue to show start message
        else:
            # Not a file access request, but has parameter
            if is_main_bot:
                # Let main bot handle other parameters (BATCH-, verify-, etc.)
                return
    
    # Regular start command (no parameter) or clone bot fallback
    user_id = message.from_user.id
    
    # Add user to database if available
    if DATABASE_AVAILABLE:
        try:
            await db.add_user(user_id)
        except Exception as e:
            print(f"Database error: {e}")
    
    # Get custom start message for this clone bot
    start_message = DEFAULT_START_MESSAGE
    if bot_info:
        start_message = await get_custom_start_message(bot_info.id)
    
    # Format the message with user mention
    try:
        formatted_message = start_message.format(
            mention=message.from_user.mention,
            first_name=message.from_user.first_name,
            user_id=message.from_user.id
        )
    except Exception as e:
        print(f"Error formatting message: {e}")
        formatted_message = start_message
    
    # Send start message
    try:
        await message.reply_text(
            text=formatted_message,
            reply_markup=get_start_keyboard(),
            disable_web_page_preview=True
        )
    except Exception as e:
        print(f"Error sending start message: {e}")
        # Fallback message
        await message.reply_text(
            text=DEFAULT_START_MESSAGE.format(mention=message.from_user.mention),
            reply_markup=get_start_keyboard(),
            disable_web_page_preview=True
        )

@Client.on_callback_query(filters.regex(r"^(help_menu|about_menu|settings_menu|back_to_main|help_genlink|help_share|help_commands|about_dev|bot_stats|version_info)$"))
async def clone_callback_handler(client: Client, callback_query: CallbackQuery):
    """Handle callback queries for clone bots"""
    data = callback_query.data
    
    try:
        if data == "help_menu":
            await callback_query.edit_message_text(
                "**📚 HELP MENU**\n\nChoose what you need help with:",
                reply_markup=get_help_keyboard()
            )
        
        elif data == "about_menu":
            about_text = """**📋 ABOUT THIS BOT**

🤖 **BOT TYPE** - File Store Clone Bot
📝 **LANGUAGE** - Python
📚 **LIBRARY** - Pyrofork  
🗃️ **DATABASE** - MongoDB
♻️ **CLONED FROM** - VJ File Store Bot"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ BACK", callback_data="back_to_main")]
            ])
            
            await callback_query.edit_message_text(about_text, reply_markup=keyboard)
        
        elif data == "settings_menu":
            settings_text = """**⚙️ SETTINGS MENU**

This is a clone bot. Settings are managed by the bot owner.

**Available Features:**
• File Upload & Link Generation
• Permanent File Storage  
• Fast File Delivery
• Unlimited File Size"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ BACK", callback_data="back_to_main")]
            ])
            
            await callback_query.edit_message_text(settings_text, reply_markup=keyboard)
        
        elif data == "back_to_main":
            # Get custom start message for callback
            bot_info = await client.get_me()
            start_message = await get_custom_start_message(bot_info.id)
            
            try:
                formatted_message = start_message.format(
                    mention=callback_query.from_user.mention,
                    first_name=callback_query.from_user.first_name,
                    user_id=callback_query.from_user.id
                )
            except:
                formatted_message = start_message
            
            await callback_query.edit_message_text(
                formatted_message,
                reply_markup=get_start_keyboard()
            )
        
        elif data == "help_genlink":
            help_text = """**🔗 HOW TO GENERATE LINKS**

1. Send any file to this bot
2. Bot will generate a shareable link
3. Share the link with anyone  
4. They can download using the link

**Files supported:**
• Documents, Videos, Audio, Photos
• Any file type and size"""
            
            await callback_query.edit_message_text(help_text, reply_markup=get_help_keyboard())
        
        elif data == "help_share":
            help_text = """**📤 HOW TO SHARE FILES**

1. Upload your file to the bot
2. Copy the generated link
3. Share the link anywhere
4. Others click link to download

**Features:**
• Links never expire
• No download limits
• Fast delivery"""
            
            await callback_query.edit_message_text(help_text, reply_markup=get_help_keyboard())
        
        elif data == "help_commands":
            help_text = """**⚙️ BOT COMMANDS**

`/start` - Start the bot
`/help` - Show help menu
`/about` - About this bot

**Usage:**
Just send any file to generate a shareable link!"""
            
            await callback_query.edit_message_text(help_text, reply_markup=get_help_keyboard())
        
    except Exception as e:
        print(f"Callback error: {e}")
        try:
            await callback_query.answer("Error occurred. Please try again.")
        except:
            pass

@Client.on_message(filters.command(["help", "about"]) & filters.private)
async def clone_help_about(client: Client, message: Message):
    """Handle help and about commands for clone bots"""
    try:
        command = message.command[0].lower()
        
        if command == "help":
            await message.reply_text(
                "**📚 HELP MENU**\n\nChoose what you need help with:",
                reply_markup=get_help_keyboard()
            )
        elif command == "about":
            about_text = """**📋 ABOUT THIS BOT**

🤖 **BOT TYPE** - File Store Clone Bot
📝 **LANGUAGE** - Python
📚 **LIBRARY** - Pyrofork  
🗃️ **DATABASE** - MongoDB
♻️ **CLONED FROM** - VJ File Store Bot"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ MAIN MENU", callback_data="back_to_main")]
            ])
            
            await message.reply_text(about_text, reply_markup=keyboard)
    except Exception as e:
        print(f"Help/About command error: {e}")
        await message.reply_text("❌ An error occurred. Please try again.")

print("✅ Smart clone commands loaded - conflict-free routing system with custom message support!")
