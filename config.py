# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import re
import os
from os import environ
from Script import script

id_pattern = re.compile(r'^.\d+$')

def is_enabled(value, default):
    if str(value).lower() in ["true", "yes", "1", "enable", "y"]:
        return True
    elif str(value).lower() in ["false", "no", "0", "disable", "n"]:
        return False
    else:
        return default

# Bot Information
API_ID = int(environ.get("API_ID", "22321078"))
API_HASH = environ.get("API_HASH", "9960806d290cf4170e43355fcc3687ac")
BOT_TOKEN = environ.get("BOT_TOKEN", "8470211855:AAFEGZcprBnVYPPj9VuAKXRPBlnorDvtY8M")

PICS = (environ.get('PICS', 'https://graph.org/file/ce1723991756e48c35aa1.jpg')).split()
ADMINS = [int(admin) if id_pattern.search(admin) else admin for admin in environ.get('ADMINS', '6226520145').split()]
BOT_USERNAME = environ.get("BOT_USERNAME", "Svadvance2_bot")
PORT = environ.get("PORT", "8080")

# Clone Info
CLONE_MODE = is_enabled(environ.get('CLONE_MODE', "True"), True)
CLONE_DB_URI = environ.get("CLONE_DB_URI", "mongodb+srv://clone:clone@cluster0.e5uszpi.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
CDB_NAME = environ.get("CDB_NAME", "clonetechvj")

# Database Information
DB_URI = environ.get("DB_URI", "mongodb+srv://mysimplestats:simplestats@cluster0.uelokbe.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = environ.get("DB_NAME", "techvjbotz")

# Auto Delete
AUTO_DELETE_MODE = is_enabled(environ.get('AUTO_DELETE_MODE', "True"), True)
AUTO_DELETE = int(environ.get("AUTO_DELETE", "30")) 
AUTO_DELETE_TIME = int(environ.get("AUTO_DELETE_TIME", "1800"))

# Channels
LOG_CHANNEL = int(environ.get("LOG_CHANNEL", "-1002091966691"))
CHANNEL_ID = int(environ.get("CHANNEL_ID", "-1002091966691"))
FORCE_SUB_CHANNEL = int(environ.get("FORCE_SUB_CHANNEL", "0"))

# Captions
CUSTOM_FILE_CAPTION = environ.get("CUSTOM_FILE_CAPTION", f"{script.CAPTION}")
BATCH_FILE_CAPTION = environ.get("BATCH_FILE_CAPTION", CUSTOM_FILE_CAPTION)

# Enable / Disable
PUBLIC_FILE_STORE = is_enabled(environ.get('PUBLIC_FILE_STORE', "True"), True)

# Verify
VERIFY_MODE = is_enabled(environ.get('VERIFY_MODE', "False"), False)
SHORTLINK_URL = environ.get("SHORTLINK_URL", "")
SHORTLINK_API = environ.get("SHORTLINK_API", "")
VERIFY_TUTORIAL = environ.get("VERIFY_TUTORIAL", "")

# Website
WEBSITE_URL_MODE = is_enabled(environ.get('WEBSITE_URL_MODE', "False"), False)
WEBSITE_URL = environ.get("WEBSITE_URL", "")

# Streaming
STREAM_MODE = is_enabled(environ.get('STREAM_MODE', "True"), True)
MULTI_CLIENT = False
SLEEP_THRESHOLD = int(environ.get('SLEEP_THRESHOLD', '60'))
PING_INTERVAL = int(environ.get("PING_INTERVAL", "1200"))

ON_HEROKU = 'DYNO' in environ
URL = environ.get("URL", "https://testofvjfilter-1fa60b1b8498.herokuapp.com/")
