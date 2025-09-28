# clone_plugins/commands.py - Smart routing system

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import base64
import asyncio

# Database import (optional)
try:
    from database.database import db
    DATABASE_AVAILABLE = True
except:
    DATABASE_AVAILABLE = False

# Import config to check if this is main bot or clone
try:
    from config import BOT_USERNAME, LOG_CHANNEL, ADMINS
    MAIN_BOT_CONFIG = True
except:
    MAIN_BOT_CONFIG = False

START_MESSAGE = """😊 **HEY** ,

**I AM A PERMANENT FILE STORE BOT AND USERS CAN ACCESS STORED MESSAGES BY USING A SHAREABLE LINK GIVEN BY ME**

**TO KNOW MORE CLICK HELP BUTTON.**"""

def get_start_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👑 HELP", callback_data="help_menu"),
            InlineKeyboardButton("📋 ABOUT", callback_data="about_menu")
        ],
        [
            InlineKeyboardButton("⚙️ SETTINGS ⚙️", callback_data="settings_menu")
        ]
    ])

def get_help_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 How to Generate Links", callback_data="help_genlink")],
        [InlineKeyboardButton("📤 How to Share Files", callback_data="help_share")],
        [InlineKeyboardButton("⚙️ Bot Commands", callback_data="help_commands")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="back_to_main")]
    ])

def is_file_access_request(parameter):
    """Check if this is a file access request"""
    if not parameter:
        return False
    
    # Direct file_ prefix
    if parameter.startswith("file_"):
        return True
    
    # Base64 encoded file access
    try:
        # Try to decode as base64
        decoded = base64.urlsafe_b64decode(parameter + "=" * (-len(parameter) % 4)).decode("ascii")
        if "file_" in decoded or "_" in decoded:
            return True
    except:
        pass
    
    # Other known non-file patterns
    if (parameter.startswith("BATCH-") or 
        parameter.startswith("verify-") or
        parameter in ["help", "about", "settings"]):
        return False
    
    # If it's long and encoded, likely a file
    if len(parameter) > 15:
        return True
    
    return False

async def handle_file_access_clone(client: Client, message: Message, parameter: str):
    """Handle file access for clone bots"""
    try:
        # Try to decode the file ID
        if parameter.startswith("file_"):
            encoded_id = parameter.replace("file_", "")
        else:
            # Handle base64 encoded format
            decoded_data = base64.urlsafe_b64decode(parameter + "=" * (-len(parameter) % 4)).decode("ascii")
            if "_" in decoded_data:
                pre, file_id = decoded_data.split("_", 1)
                encoded_id = base64.urlsafe_b64encode(f"file_{file_id}".encode("ascii")).decode().strip("=")
            else:
                encoded_id = parameter
        
        # Decode the file ID
        decoded_string = base64.urlsafe_b64decode(encoded_id + "=" * (-len(encoded_id) % 4)).decode("ascii")
        
        if decoded_string.startswith("file_"):
            file_id = int(decoded_string[5:])
        else:
            file_id = int(decoded_string)
        
        print(f"Clone: Trying to access file ID {file_id}")
        
        # Send loading message
        loading_msg = await message.reply_text("🔄 **Fetching your file...**")
        
        try:
            # For clone bots, try to get from LOG_CHANNEL (if available)
            if MAIN_BOT_CONFIG and LOG_CHANNEL:
                file_msg = await client.get_messages(LOG_CHANNEL, file_id)
                
                if file_msg and file_msg.media:
                    await file_msg.copy(chat_id=message.from_user.id, protect_content=False)
                    await loading_msg.delete()
                    await message.reply_text("✅ **File delivered successfully!**")
                    print(f"Clone: File {file_id} delivered to user {message.from_user.id}")
                    return True
                else:
                    await loading_msg.edit_text("❌ **File not found in storage**")
                    return False
            else:
                await loading_msg.edit_text("❌ **File storage not configured for clone bot**")
                return False
                
        except Exception as e:
            await loading_msg.edit_text(f"❌ **Cannot access file**\n\n**Error:** `{str(e)}`")
            print(f"Clone: Error accessing file {file_id}: {str(e)}")
            return False
            
    except Exception as e:
        await message.reply_text(f"❌ **Invalid link format**\n\n**Error:** `{str(e)}`")
        print(f"Clone: Link decode error: {str(e)}")
        return False

@Client.on_message(filters.command("start") & filters.private)
async def smart_start_handler(client: Client, message: Message):
    """Smart start command handler that routes properly"""
    
    # Get bot info to determine if this is main bot or clone
    bot_info = await client.get_me()
    is_main_bot = MAIN_BOT_CONFIG and bot_info.username == BOT_USERNAME.replace("@", "") if MAIN_BOT_CONFIG else False
    
    # Check if there's a parameter
    if len(message.command) > 1:
        parameter = message.command[1]
        
        print(f"Start command received - Bot: {bot_info.username}, Parameter: {parameter}")
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
    
    # Send start message
    await message.reply_text(
        text=START_MESSAGE,
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
            await callback_query.edit_message_text(
                START_MESSAGE,
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
        await callback_query.answer("Error occurred. Please try again.")

@Client.on_message(filters.command(["help", "about"]) & filters.private)
async def clone_help_about(client: Client, message: Message):
    """Handle help and about commands for clone bots"""
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

print("✅ Smart clone commands loaded - conflict-free routing system!")
