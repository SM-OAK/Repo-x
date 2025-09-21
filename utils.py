#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import string
import random
import asyncio
import logging
import requests
import re
from datetime import datetime, timedelta
from typing import Union, Optional, Tuple, Dict
from pyrogram.types import Message
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from config import Config

logger = logging.getLogger(__name__)

def encode_file_id(file_id: str) -> str:
    """Encode file_id to base64 URL-safe string"""
    try:
        encoded = base64.urlsafe_b64encode(file_id.encode("ascii")).decode("ascii")
        return encoded.strip("=")
    except Exception as e:
        logger.error(f"Error encoding file_id: {e}")
        return ""

def decode_file_id(encoded_id: str) -> str:
    """Decode base64 encoded file_id"""
    try:
        # Add padding if needed
        encoded_id += "=" * (4 - len(encoded_id) % 4)
        return base64.urlsafe_b64decode(encoded_id).decode("ascii")
    except Exception as e:
        logger.error(f"Error decoding file_id: {e}")
        return ""

def generate_random_id(length: int = 10) -> str:
    """Generate a random alphanumeric ID"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_batch_id() -> str:
    """Generate a unique batch ID"""
    timestamp = str(int(datetime.now().timestamp()))
    random_part = generate_random_id(6)
    return f"batch_{timestamp}_{random_part}"

def format_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    if i == 0:
        return f"{int(size_bytes)} {size_names[i]}"
    else:
        return f"{size_bytes:.1f} {size_names[i]}"

def format_duration(seconds: int) -> str:
    """Format duration in human readable format"""
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minutes"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if minutes > 0:
            return f"{hours}h {minutes}m"
        return f"{hours} hours"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        if hours > 0:
            return f"{days}d {hours}h"
        return f"{days} days"

def get_file_type(message: Message) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[int]]:
    """Extract file information from message"""
    try:
        if message.document:
            return (
                "document",
                message.document.file_id,
                message.document.file_name or "Unknown Document",
                message.document.file_size or 0
            )
        elif message.video:
            return (
                "video",
                message.video.file_id,
                message.video.file_name or f"Video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                message.video.file_size or 0
            )
        elif message.audio:
            return (
                "audio",
                message.audio.file_id,
                message.audio.file_name or f"{message.audio.performer or 'Unknown'} - {message.audio.title or 'Audio'}.mp3",
                message.audio.file_size or 0
            )
        elif message.photo:
            return (
                "photo",
                message.photo.file_id,
                f"Photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
                message.photo.file_size or 0
            )
        elif message.animation:
            return (
                "animation",
                message.animation.file_id,
                message.animation.file_name or f"Animation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.gif",
                message.animation.file_size or 0
            )
        elif message.voice:
            return (
                "voice",
                message.voice.file_id,
                f"Voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ogg",
                message.voice.file_size or 0
            )
        elif message.video_note:
            return (
                "video_note",
                message.video_note.file_id,
                f"VideoNote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                message.video_note.file_size or 0
            )
        elif message.sticker:
            file_ext = "webp"
            if message.sticker.file_name and "." in message.sticker.file_name:
                file_ext = message.sticker.file_name.split(".")[-1]
            
            return (
                "sticker",
                message.sticker.file_id,
                f"Sticker_{message.sticker.set_name or 'Unknown'}_{datetime.now().strftime('%H%M%S')}.{file_ext}",
                message.sticker.file_size or 0
            )
        else:
            return None, None, None, None
            
    except Exception as e:
        logger.error(f"Error getting file type: {e}")
        return None, None, None, None

def get_file_emoji(file_type: str) -> str:
    """Get emoji for file type"""
    emojis = {
        "document": "📄",
        "video": "🎥",
        "audio": "🎵",
        "photo": "🖼️",
        "animation": "🎬",
        "voice": "🎤",
        "video_note": "📹",
        "sticker": "🎪",
        "archive": "📁",
        "text": "📝",
        "image": "🖼️",
        "unknown": "📎"
    }
    return emojis.get(file_type, "📎")

def detect_file_category(file_name: str) -> str:
    """Detect file category based on extension"""
    if not file_name or "." not in file_name:
        return "unknown"
    
    extension = file_name.lower().split(".")[-1]
    
    categories = {
        "video": ["mp4", "avi", "mkv", "mov", "wmv", "flv", "webm", "m4v", "3gp"],
        "audio": ["mp3", "wav", "flac", "aac", "ogg", "wma", "m4a"],
        "image": ["jpg", "jpeg", "png", "gif", "bmp", "svg", "webp", "ico"],
        "document": ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "rtf"],
        "archive": ["zip", "rar", "7z", "tar", "gz", "bz2", "xz"],
        "code": ["py", "js", "html", "css", "cpp", "java", "php", "rb", "go"],
        "data": ["json", "xml", "csv", "sql", "db"]
    }
    
    for category, extensions in categories.items():
        if extension in extensions:
            return category
    
    return "unknown"

async def shorten_url(long_url: str) -> str:
    """Shorten URL using configured shortener"""
    if not Config.USE_SHORTENER or not Config.SHORTENER_API or not Config.SHORTENER_URL:
        return long_url
    
    try:
        # Generic URL shortener implementation
        # You can customize this based on your preferred service
        response = requests.post(
            Config.SHORTENER_URL,
            json={
                "url": long_url,
                "api_key": Config.SHORTENER_API
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("short_url", long_url)
        else:
            logger.warning(f"URL shortener returned status {response.status_code}")
            return long_url
            
    except Exception as e:
        logger.error(f"Error shortening URL: {e}")
        return long_url

def validate_url(url: str) -> bool:
    """Validate URL format"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None

def extract_message_id_from_link(link: str) -> Optional[int]:
    """Extract message ID from Telegram link"""
    try:
        # Pattern for t.me/c/channelid/messageid or t.me/username/messageid
        patterns = [
            r't\.me/c/[-\d]+/(\d+)',
            r't\.me/\w+/(\d+)',
            r'telegram\.me/c/[-\d]+/(\d+)',
            r'telegram\.me/\w+/(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, link)
            if match:
                return int(match.group(1))
        
        # Direct message ID if just numbers
        if link.isdigit():
            return int(link)
        
        return None
    except Exception as e:
        logger.error(f"Error extracting message ID from link: {e}")
        return None

async def safe_send_message(client, chat_id: int, text: str, **kwargs):
    """Safely send message with flood wait handling"""
    try:
        return await client.send_message(chat_id, text, **kwargs)
    except FloodWait as e:
        logger.warning(f"FloodWait: Sleeping for {e.value} seconds")
        await asyncio.sleep(e.value + 1)
        return await client.send_message(chat_id, text, **kwargs)
    except (UserIsBlocked, InputUserDeactivated):
        logger.info(f"User {chat_id} has blocked the bot or deactivated account")
        return None
    except Exception as e:
        logger.error(f"Error sending message to {chat_id}: {e}")
        return None

async def safe_edit_message(client, chat_id: int, message_id: int, text: str, **kwargs):
    """Safely edit message with flood wait handling"""
    try:
        return await client.edit_message_text(chat_id, message_id, text, **kwargs)
    except FloodWait as e:
        logger.warning(f"FloodWait: Sleeping for {e.value} seconds")
        await asyncio.sleep(e.value + 1)
        return await client.edit_message_text(chat_id, message_id, text, **kwargs)
    except Exception as e:
        logger.error(f"Error editing message {message_id} in {chat_id}: {e}")
        return None

def generate_progress_bar(percentage: float, length: int = 20) -> str:
    """Generate progress bar string"""
    filled_length = int(length * percentage // 100)
    bar = '█' * filled_length + '░' * (length - filled_length)
    return f"[{bar}] {percentage:.1f}%"

def clean_filename(filename: str) -> str:
    """Clean filename by removing invalid characters"""
    # Remove invalid characters for most file systems
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        max_name_length = 250 - len(ext)
        filename = name[:max_name_length] + ('.' + ext if ext else '')
    
    return filename or "untitled"

def parse_time_string(time_str: str) -> int:
    """Parse time string like '5m', '2h', '1d' to seconds"""
    time_str = time_str.lower().strip()
    
    if time_str.endswith('s'):
        return int(time_str[:-1])
    elif time_str.endswith('m'):
        return int(time_str[:-1]) * 60
    elif time_str.endswith('h'):
        return int(time_str[:-1]) * 3600
    elif time_str.endswith('d'):
        return int(time_str[:-1]) * 86400
    else:
        # Assume seconds if no unit
        return int(time_str)

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in Config.ADMINS or user_id == Config.OWNER_ID

def get_readable_time() -> str:
    """Get current time in readable format"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def calculate_eta(start_time: float, current: int, total: int) -> str:
    """Calculate estimated time of arrival"""
    if current == 0:
        return "Calculating..."
    
    elapsed = datetime.now().timestamp() - start_time
    rate = current / elapsed
    remaining = (total - current) / rate if rate > 0 else 0
    
    return format_duration(int(remaining))

class FileTypeDetector:
    """Advanced file type detection"""
    
    MIME_TYPES = {
        # Videos
        'video/mp4': 'video',
        'video/avi': 'video',
        'video/quicktime': 'video',
        'video/x-msvideo': 'video',
        'video/x-ms-wmv': 'video',
        
        # Audio
        'audio/mpeg': 'audio',
        'audio/wav': 'audio',
        'audio/ogg': 'audio',
        'audio/aac': 'audio',
        
        # Images
        'image/jpeg': 'image',
        'image/png': 'image',
        'image/gif': 'image',
        'image/webp': 'image',
        
        # Documents
        'application/pdf': 'document',
        'application/msword': 'document',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'document',
        
        # Archives
        'application/zip': 'archive',
        'application/x-rar-compressed': 'archive',
        'application/x-7z-compressed': 'archive',
        'application/x-tar': 'archive',
        'application/gzip': 'archive'
    }
    
    @classmethod
    def detect_by_extension(cls, filename: str) -> str:
        """Detect file type by extension"""
        return detect_file_category(filename)
    
    @classmethod
    def detect_by_mime(cls, mime_type: str) -> str:
        """Detect file type by MIME type"""
        return cls.MIME_TYPES.get(mime_type, 'unknown')

def create_share_text(file_name: str, file_size: int, file_type: str, share_link: str) -> str:
    """Create formatted share text"""
    emoji = get_file_emoji(file_type)
    size_text = format_size(file_size)
    
    return f"""
{emoji} **File Shared Successfully!**

📄 **Name:** `{file_name}`
📊 **Size:** `{size_text}`
📂 **Type:** `{file_type.title()}`

🔗 **Share Link:**
{share_link}

💡 **Tip:** This link works permanently and can be shared with anyone!
    """

def create_batch_share_text(file_count: int, total_size: int, share_link: str) -> str:
    """Create formatted batch share text"""
    size_text = format_size(total_size)
    
    return f"""
📦 **Batch Created Successfully!**

📊 **Files Count:** {file_count}
📈 **Total Size:** {size_text}

🔗 **Batch Link:**
{share_link}

💡 **Note:** Anyone with this link can access all {file_count} files!
    """
