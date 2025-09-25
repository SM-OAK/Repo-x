# clone_plugins/commands.py - Fixed for Pyrogram compatibility

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Fix for Pyrogram version compatibility - handle StopPropagation import
try:
    from pyrogram.errors import StopPropagation
except ImportError:
    try:
        from pyrogram import StopPropagation
    except ImportError:
        # Create dummy StopPropagation if not available
        class StopPropagation(Exception):
            pass

import asyncio

# Database import (optional - will work without database)
try:
    from database.database import db
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("⚠️ Database module not found. Bot will work without database features.")

# Welcome message like in your screenshot
START_MESSAGE = """😊 **HEY** ,

**I AM A PERMANENT FILE STORE BOT AND USERS CAN ACCESS STORED MESSAGES BY USING A SHAREABLE LINK GIVEN BY ME**

**TO KNOW MORE CLICK HELP BUTTON.**"""

# Main menu buttons
def get_start_keyboard():
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👑 HELP", callback_data="help_menu"),
            InlineKeyboardButton("📋 ABOUT", callback_data="about_menu")
        ],
        [
            InlineKeyboardButton("⚙️ SETTINGS ⚙️", callback_data="settings_menu")
        ]
    ])
    return keyboard

# Settings menu with customizable options
def get_settings_keyboard():
    keyboard = InlineKeyboardMarkup([
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
    return keyboard

# Help menu
def get_help_keyboard():
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 How to Generate Links", callback_data="help_genlink")],
        [InlineKeyboardButton("📤 How to Share Files", callback_data="help_share")],
        [InlineKeyboardButton("⚙️ Bot Commands", callback_data="help_commands")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="back_to_main")]
    ])
    return keyboard

# About menu
def get_about_keyboard():
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 Developer", callback_data="about_dev")],
        [InlineKeyboardButton("📊 Bot Stats", callback_data="bot_stats")],
        [InlineKeyboardButton("🔄 Version Info", callback_data="version_info")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="back_to_main")]
    ])
    return keyboard

@Client.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check if it's a file access request first
    if len(message.command) > 1 and message.command[1].startswith("file_"):
        # This will be handled by genlink.py, so we skip it here
        return
    
    # Add user to database (optional)
    if DATABASE_AVAILABLE:
        try:
            await db.add_user(user_id)
        except Exception as e:
            print(f"Database error: {e}")
            pass
    
    # Send welcome message with buttons
    try:
        await message.reply_text(
            text=START_MESSAGE,
            reply_markup=get_start_keyboard(),
            disable_web_page_preview=True
        )
    except Exception as e:
        print(f"Error sending start message: {e}")
        # Fallback message without buttons
        await message.reply_text(START_MESSAGE)

# Callback handlers for all buttons
@Client.on_callback_query()
async def callback_handler(client: Client, callback_query: CallbackQuery):
    try:
        data = callback_query.data
        user_id = callback_query.from_user.id
        
        # Main menu callbacks
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
📚 **LIBRARY** - PYROGRAM
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
        
        # Settings callbacks
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
            try:
                if DATABASE_AVAILABLE:
                    total_users = await db.total_users_count()
                else:
                    total_users = "N/A (Database disabled)"
                
                stats_text = f"""**📊 BOT STATISTICS**

👥 **Total Users:** {total_users}
🔗 **Links Generated:** Loading...
📤 **Files Shared:** Loading...
⏰ **Uptime:** 24/7

**Bot is running perfectly!**"""
                await callback_query.edit_message_text(stats_text, reply_markup=get_about_keyboard())
            except Exception as e:
                await callback_query.answer(f"📊 Error loading statistics: {str(e)}", show_alert=True)
        
        elif data == "version_info":
            version_text = """**🔄 VERSION INFORMATION**

**Bot Version:** v2.1.0
**Last Updated:** Recent
**Python Version:** 3.9+
**Pyrogram Version:** Compatible

**All systems running smoothly!**"""
            
            await callback_query.edit_message_text(version_text, reply_markup=get_about_keyboard())
        
        # Answer the callback to remove loading state
        if not callback_query.data.startswith(('premium_plan', 'link_shortner', 'token_verification', 'custom_caption', 
                                               'custom_force_sub', 'custom_button', 'auto_delete', 'permanent_link', 
                                               'protect_content', 'stream_download', 'about_dev')):
            try:
                await callback_query.answer()
            except:
                pass
                
    except Exception as e:
        print(f"Callback error: {e}")
        try:
            await callback_query.answer("❌ An error occurred. Please try again.", show_alert=True)
        except:
            pass

# Additional commands
@Client.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message: Message):
    try:
        await message.reply_text(
            "**📚 HELP MENU**\n\nChoose what you need help with:",
            reply_markup=get_help_keyboard()
        )
    except Exception as e:
        print(f"Help command error: {e}")
        await message.reply_text("**📚 HELP MENU**\n\nSend files to generate shareable links!")

@Client.on_message(filters.command("about") & filters.private)
async def about_command(client: Client, message: Message):
    about_text = """**📋 ABOUT THIS BOT**

🤖 **MY NAME** - File Extra Bot  
👤 **MY BOSS** - .
♻️ **CLONED FROM** - FILE STORE BOT
📝 **LANGUAGE** - PYTHON
📚 **LIBRARY** - PYROGRAM
🗃️ **DATABASE** - MONGO DB"""
    
    try:
        await message.reply_text(about_text, reply_markup=get_about_keyboard())
    except Exception as e:
        print(f"About command error: {e}")
        await message.reply_text(about_text)

# Simple stats command for testing
@Client.on_message(filters.command("stats") & filters.private)
async def stats_command(client: Client, message: Message):
    try:
        if DATABASE_AVAILABLE:
            total_users = await db.total_users_count()
        else:
            total_users = "Database not connected"
        
        stats_text = f"""**📊 BOT STATISTICS**

👥 **Total Users:** {total_users}
🤖 **Bot Status:** Running
⚙️ **Version:** v2.1.0

**Bot is working perfectly!**"""
        
        await message.reply_text(stats_text)
    except Exception as e:
        await message.reply_text(f"**📊 Stats Error:** {str(e)}")

print("✅ Commands module loaded successfully!")
