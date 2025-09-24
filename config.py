#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from typing import List

class Config:
    # Telegram API Credentials
    API_ID: int = int(os.environ.get("API_ID", "22321078"))
    API_HASH: str = os.environ.get("API_HASH", "9960806d290cf4170e43355fcc3687ac")
    BOT_TOKEN: str = os.environ.get("BOT_TOKEN", "8251719855:AAH8O0OeEoAjNrtQ9IOOBYfblS4xvT2Dksw")
    BOT_USERNAME: str = os.environ.get("BOT_USERNAME", "Svadvance2_bot")
    
    # Database Configuration
    DB_URI: str = os.environ.get("DB_URI", "mongodb+srv://mysimplestats:simplestats@cluster0.uelokbe.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    DB_NAME: str = os.environ.get("DB_NAME", "FileStore")
    
    # Channel Configuration
    DB_CHANNEL: int = int(os.environ.get("DB_CHANNEL", "100209196669"))  # Channel to store files
    LOG_CHANNEL: int = int(os.environ.get("LOG_CHANNEL", "100291358571"))  # Channel for activity logs
    
    # Admin Configuration
    ADMINS: List[int] = list(set(int(x) for x in os.environ.get("ADMINS", "").split() if x))
    OWNER_ID: int = int(os.environ.get("OWNER_ID", "6226520145"))
    
    # Server Configuration
    URL: str = os.environ.get("URL", "")
    PORT: int = int(os.environ.get("PORT", "8080"))
    
    # Auto Delete Configuration
    AUTO_DELETE: bool = bool(int(os.environ.get("AUTO_DELETE", "0")))
    AUTO_DELETE_TIME: int = int(os.environ.get("AUTO_DELETE_TIME", "600"))  # seconds
    
    # File Size Limits
    MAX_FILE_SIZE: int = int(os.environ.get("MAX_FILE_SIZE", "2147483648"))  # 2GB in bytes
    
    # URL Shortener Configuration
    USE_SHORTENER: bool = bool(int(os.environ.get("USE_SHORTENER", "0")))
    SHORTENER_API: str = os.environ.get("SHORTENER_API", "")
    SHORTENER_URL: str = os.environ.get("SHORTENER_URL", "")
    
    # Feature Toggles
    FORCE_SUB_CHANNEL: int = int(os.environ.get("FORCE_SUB_CHANNEL", "0"))
    TOKEN_VERIFICATION: bool = bool(int(os.environ.get("TOKEN_VERIFICATION", "0")))
    
    # Messages Configuration
    START_MESSAGE: str = os.environ.get("START_MESSAGE", """
👋 **Hello {first_name}!**

🤖 **I'm a File Store Bot that can store all types of files!**

**📂 Supported File Types:**
• 📄 Documents (PDF, DOCX, TXT, etc.)
• 🎥 Videos (MP4, AVI, MKV, etc.)
• 🎵 Audio (MP3, WAV, FLAC, etc.)
• 🖼️ Images (JPG, PNG, GIF, etc.)
• 📁 Archives (ZIP, RAR, 7Z, etc.)
• 🎬 Animations & GIFs
• 🎤 Voice messages
• 🎪 Stickers
• And much more!

Send me a file to get started! 🚀
    """)
    
    FORCE_SUB_MESSAGE: str = os.environ.get("FORCE_SUB_MESSAGE", """
❌ **Access Denied!**

🔐 You must join our channel first to use this bot.

**Please join the channel and try again:**
    """)
    
    # Validation
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        required_vars = [
            cls.API_ID,
            cls.API_HASH,
            cls.BOT_TOKEN,
            cls.BOT_USERNAME,
            cls.DB_URI
        ]
        
        if not all(required_vars):
            missing = []
            if not cls.API_ID: missing.append("API_ID")
            if not cls.API_HASH: missing.append("API_HASH")
            if not cls.BOT_TOKEN: missing.append("BOT_TOKEN")
            if not cls.BOT_USERNAME: missing.append("BOT_USERNAME")
            if not cls.DB_URI: missing.append("DB_URI")
            
            print(f"❌ Missing required environment variables: {', '.join(missing)}")
            return False
        
        if cls.DB_CHANNEL == 0:
            print("⚠️ Warning: DB_CHANNEL not set. Files will be stored using message IDs only.")
        
        if cls.LOG_CHANNEL == 0:
            print("⚠️ Warning: LOG_CHANNEL not set. Activity logging disabled.")
        
        if not cls.ADMINS:
            print("⚠️ Warning: No ADMINS set. Broadcast feature disabled.")
        
        return True
    
    @classmethod
    def print_config(cls):
        """Print configuration summary"""
        print("\n" + "="*50)
        print("🤖 FILE STORE BOT CONFIGURATION")
        print("="*50)
        print(f"📱 Bot Username: @{cls.BOT_USERNAME}")
        print(f"🗄️  Database: {'✅ Connected' if cls.DB_URI else '❌ Not configured'}")
        print(f"📁 DB Channel: {'✅ Set' if cls.DB_CHANNEL else '❌ Not set'}")
        print(f"📋 Log Channel: {'✅ Set' if cls.LOG_CHANNEL else '❌ Not set'}")
        print(f"👥 Admins: {len(cls.ADMINS)} configured")
        print(f"🗑️  Auto Delete: {'✅ Enabled' if cls.AUTO_DELETE else '❌ Disabled'}")
        print(f"📊 Max File Size: {cls.format_size(cls.MAX_FILE_SIZE)}")
        print(f"🔗 URL Shortener: {'✅ Enabled' if cls.USE_SHORTENER else '❌ Disabled'}")
        print("="*50 + "\n")
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Format file size"""
        if size_bytes == 0:
            return "0B"
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024
            i += 1
        return f"{size_bytes:.1f} {size_names[i]}"

# Environment variables template for easy setup
ENV_TEMPLATE = """
# Telegram API Configuration (Get from my.telegram.org)
API_ID=your_api_id
API_HASH=your_api_hash

# Bot Configuration (Get from @BotFather)
BOT_TOKEN=your_bot_token
BOT_USERNAME=your_bot_username_without_@

# Database Configuration (MongoDB URI)
DB_URI=mongodb://username:password@host:port/database
DB_NAME=FileStore

# Channel Configuration
DB_CHANNEL=-100xxxxxxxxx  # Channel where files are stored (must be channel ID)
LOG_CHANNEL=-100xxxxxxxxx  # Channel for activity logs (optional)

# Admin Configuration
ADMINS=user_id1 user_id2 user_id3  # Space separated user IDs
OWNER_ID=your_user_id

# Server Configuration (for deployment)
URL=https://your-app-name.herokuapp.com/
PORT=8080

# Auto Delete Configuration
AUTO_DELETE=0  # 1 to enable, 0 to disable
AUTO_DELETE_TIME=600  # Time in seconds before auto delete

# File Size Configuration
MAX_FILE_SIZE=2147483648  # Maximum file size in bytes (2GB)

# URL Shortener Configuration (Optional)
USE_SHORTENER=0  # 1 to enable, 0 to disable
SHORTENER_API=your_shortener_api_key
SHORTENER_URL=https://your-shortener-domain.com

# Feature Configuration
FORCE_SUB_CHANNEL=0  # Channel ID for force subscription (optional)
TOKEN_VERIFICATION=0  # 1 to enable token verification, 0 to disable

# Custom Messages (Optional)
START_MESSAGE="Custom start message here"
FORCE_SUB_MESSAGE="Custom force subscription message here"
"""
