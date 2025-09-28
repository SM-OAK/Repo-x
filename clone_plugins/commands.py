# clone_plugins/commands.py - Final version by Gemini
# Merges smart routing with custom start message and auto-delete features.

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

# --- Helper Functions ---

def is_file_access_request(parameter):
    if not parameter: return False
    if parameter.startswith("file_"): return True
    try:
        decoded = base64.urlsafe_b64decode(parameter + "=" * (-len(parameter) % 4)).decode("ascii")
        if "file_" in decoded or "_" in decoded: return True
    except:
        pass
    if (parameter.startswith("BATCH-") or parameter.startswith("verify-")): return False
    if len(parameter) > 15: return True
    return False

async def handle_file_access_clone(client: Client, message: Message, parameter: str):
    bot_info = await client.get_me()
    clone_settings = bots_collection.find_one({"bot_id": bot_info.id})
    
    try:
        decoded_data = base64.urlsafe_b64decode(parameter + "=" * (-len(parameter) % 4)).decode("ascii")
        file_id = int(decoded_data.split("_", 1)[1])
        
        loading_msg = await message.reply_text("🔄 **Fetching your file...**")
        file_msg = await client.get_messages(config.LOG_CHANNEL, file_id)
        
        if not file_msg or not file_msg.media:
            return await loading_msg.edit_text("❌ **File not found in storage.**")

        auto_delete_config = clone_settings.get("auto_delete_settings", {})
        is_enabled = auto_delete_config.get("enabled", False)
        
        if is_enabled:
            time_in_minutes = auto_delete_config.get("time_in_minutes", 30)
            sent_file = await file_msg.copy(chat_id=message.from_user.id)
            warning_msg = await message.reply_text(f"<b>❗️IMPORTANT❗️</b>\n\nThis file will be deleted in <b><u>{time_in_minutes} minutes</u></b>.")
            await loading_msg.delete()
            await asyncio.sleep(time_in_minutes * 60)
            await sent_file.delete()
            await warning_msg.edit_text("<b>Your file has been successfully deleted!</b>")
        else:
            await file_msg.copy(chat_id=message.from_user.id)
            await loading_msg.delete()
        return True
    except Exception as e:
        await message.reply_text(f"❌ **Invalid or expired link.**\n\n`{e}`")
        return False

# --- Message and Callback Handlers ---

@Client.on_message(filters.command("start") & filters.private)
async def smart_start_handler(client: Client, message: Message):
    bot_info = await client.get_me()
    is_main_bot = bot_info.username == config.BOT_USERNAME.replace("@", "")

    if len(message.command) > 1:
        parameter = message.command[1]
        if is_file_access_request(parameter):
            if is_main_bot: return
            else:
                await handle_file_access_clone(client, message, parameter)
                return
        else:
            if is_main_bot: return

    clone_settings = bots_collection.find_one({"bot_id": bot_info.id})
    start_text = clone_settings.get("custom_start_message") or START_MESSAGE.format(mention=message.from_user.mention)
        
    await message.reply_text(text=start_text, reply_markup=get_start_keyboard())

@Client.on_callback_query()
async def clone_callback_handler(client: Client, query: CallbackQuery):
    data = query.data
    
    if data == "back_to_main":
        bot_info = await client.get_me()
        clone_settings = bots_collection.find_one({"bot_id": bot_info.id})
        start_text = clone_settings.get("custom_start_message") or START_MESSAGE.format(mention=query.from_user.mention)
        await query.message.edit_text(start_text, reply_markup=get_start_keyboard())
    
    elif data == "help_menu":
        await query.message.edit_text("**📚 HELP MENU**...", reply_markup=get_help_keyboard())
        
    # Add other help/about logic from your file here if needed

print("✅ Smart clone commands loaded - with full custom feature support!")

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
