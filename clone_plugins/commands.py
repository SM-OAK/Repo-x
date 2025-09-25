# clone_plugins/commands.py - Final Fixed Version for Pyrofork

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# NO problematic imports - completely clean
import asyncio

# Database import (optional)
try:
    from database.database import db
    DATABASE_AVAILABLE = True
except:
    DATABASE_AVAILABLE = False

# Welcome message exactly like your screenshot
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

def get_settings_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 PREMIUM PLAN", callback_data="premium_plan")],
        [InlineKeyboardButton("🔗 LINK SHORTNER", callback_data="link_shortner")],
        [InlineKeyboardButton("🎯 TOKEN VERIFICATION", callback_data="token_verification")],
        [InlineKeyboardButton("🍿 CUSTOM CAPTION", callback_data="custom_caption")],
        [InlineKeyboardButton("📢 CUSTOM FORCE SUBSCRIBE", callback_data="custom_force_sub")],
        [InlineKeyboardButton("⚪ CUSTOM BUTTON", callback_data="custom_button")],
        [InlineKeyboardButton("♻️ AUTO DELETE", callback_data="auto_delete")],
        [InlineKeyboardButton("∞ PERMANENT LINK", callback_data="permanent_link")],
        [InlineKeyboardButton("🔒 PROTECT CONTENT - ❌", callback_data="protect_content")],
        [InlineKeyboardButton("📱 STREAM/DOWNLOAD - ❌", callback_data="stream_download")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="back_to_main")]
    ])

def get_help_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 How to Generate Links", callback_data="help_genlink")],
        [InlineKeyboardButton("📤 How to Share Files", callback_data="help_share")],
        [InlineKeyboardButton("⚙️ Bot Commands", callback_data="help_commands")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="back_to_main")]
    ])

def get_about_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 Developer", callback_data="about_dev")],
        [InlineKeyboardButton("📊 Bot Stats", callback_data="bot_stats")],
        [InlineKeyboardButton("🔄 Version Info", callback_data="version_info")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="back_to_main")]
    ])

@Client.on_message(filters.command("start") & filters.private)
async def clone_start_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Skip if it's a file access request (handled by genlink)
    if len(message.command) > 1 and message.command[1].startswith("file_"):
        return
    
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

@Client.on_callback_query()
async def clone_callback_handler(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    
    try:
        if data == "help_menu":
            await callback_query.edit_message_text(
                "**📚 HELP MENU**\n\nChoose what you need help with:",
                reply_markup=get_help_keyboard()
            )
        
        elif data == "about_menu":
            about_text = """**📋 ABOUT THIS BOT**

🤖 **MY NAME** - File Extra Bot
👤 **MY BOSS** - .
♻️ **CLONED FROM** - FILE STORE BOT
📝 **LANGUAGE** - PYTHON
📚 **LIBRARY** - PYROFORK
🗃️ **DATABASE** - MONGO DB"""
            
            await callback_query.edit_message_text(
                about_text,
                reply_markup=get_about_keyboard()
            )
        
        elif data == "settings_menu":
            settings_text = """**HERE IS THE SETTINGS MENU**

**CUSTOMIZE YOUR SETTINGS AS PER YOUR NEED**"""
            
            await callback_query.edit_message_text(
                settings_text,
                reply_markup=get_settings_keyboard()
            )
        
        elif data == "back_to_main":
            await callback_query.edit_message_text(
                START_MESSAGE,
                reply_markup=get_start_keyboard()
            )
        
        # Settings callbacks with popup alerts
        elif data == "premium_plan":
            await callback_query.answer("💎 Premium Plan - Coming Soon!", show_alert=True)
        elif data == "link_shortner":
            await callback_query.answer("🔗 Link Shortner - Feature Available!", show_alert=True)
        elif data == "token_verification":
            await callback_query.answer("🎯 Token Verification - Configure in Admin Panel", show_alert=True)
        elif data == "custom_caption":
            await callback_query.answer("🍿 Custom Caption - Set your custom captions!", show_alert=True)
        elif data == "custom_force_sub":
            await callback_query.answer("📢 Force Subscribe - Add your channel!", show_alert=True)
        elif data == "custom_button":
            await callback_query.answer("⚪ Custom Button - Create custom buttons!", show_alert=True)
        elif data == "auto_delete":
            await callback_query.answer("♻️ Auto Delete - Configure auto deletion timer!", show_alert=True)
        elif data == "permanent_link":
            await callback_query.answer("∞ Permanent Link - Links never expire!", show_alert=True)
        elif data == "protect_content":
            await callback_query.answer("🔒 Protect Content - Currently Disabled", show_alert=True)
        elif data == "stream_download":
            await callback_query.answer("📱 Stream/Download - Currently Disabled", show_alert=True)
        
        # Help callbacks
        elif data == "help_genlink":
            help_text = """**🔗 HOW TO GENERATE LINKS**

1. Forward any file to this bot
2. Bot will generate a shareable link
3. Share the link with others
4. Others can download using the link

**Simple and Easy!**"""
            await callback_query.edit_message_text(help_text, reply_markup=get_help_keyboard())
        
        elif data == "help_share":
            help_text = """**📤 HOW TO SHARE FILES**

1. Send any media file to the bot
2. Get the generated link
3. Copy and share the link
4. Recipients can access the file anytime

**No File Size Limits!**"""
            await callback_query.edit_message_text(help_text, reply_markup=get_help_keyboard())
        
        elif data == "help_commands":
            help_text = """**⚙️ BOT COMMANDS**

/start - Start the bot
/help - Get help
/about - About this bot
/stats - Bot statistics (Admin only)
/broadcast - Send broadcast (Admin only)

**More commands coming soon!**"""
            await callback_query.edit_message_text(help_text, reply_markup=get_help_keyboard())
        
        # About callbacks
        elif data == "about_dev":
            await callback_query.answer("👤 Developer Info - Contact admin for details", show_alert=True)
        
        elif data == "bot_stats":
            if DATABASE_AVAILABLE:
                try:
                    total_users = await db.total_users_count()
                except:
                    total_users = "Error loading"
            else:
                total_users = "N/A"
            
            stats_text = f"""**📊 BOT STATISTICS**

👥 **Total Users:** {total_users}
🔗 **Links Generated:** Loading...
📤 **Files Shared:** Loading...
⏰ **Uptime:** 24/7

**Bot is running perfectly!**"""
            await callback_query.edit_message_text(stats_text, reply_markup=get_about_keyboard())
        
        elif data == "version_info":
            version_text = """**🔄 VERSION INFORMATION**

**Bot Version:** v2.1.0
**Last Updated:** Recent
**Python Version:** 3.9+
**Pyrofork Version:** 2.3.45

**All systems running smoothly!**"""
            await callback_query.edit_message_text(version_text, reply_markup=get_about_keyboard())
        
    except Exception as e:
        print(f"Callback error: {e}")
        try:
            await callback_query.answer("Error occurred. Please try again.")
        except:
            pass

@Client.on_message(filters.command("help") & filters.private)
async def clone_help_command(client: Client, message: Message):
    await message.reply_text(
        "**📚 HELP MENU**\n\nChoose what you need help with:",
        reply_markup=get_help_keyboard()
    )

@Client.on_message(filters.command("about") & filters.private) 
async def clone_about_command(client: Client, message: Message):
    about_text = """**📋 ABOUT THIS BOT**

🤖 **MY NAME** - File Extra Bot  
👤 **MY BOSS** - .
♻️ **CLONED FROM** - FILE STORE BOT
📝 **LANGUAGE** - PYTHON
📚 **LIBRARY** - PYROFORK
🗃️ **DATABASE** - MONGO DB"""
    
    await message.reply_text(about_text, reply_markup=get_about_keyboard())

print("✅ Clone commands loaded successfully!")
