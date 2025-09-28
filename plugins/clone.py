# plugins/clone.py - Updated by Gemini
# Now saves default settings for custom start message and auto-delete.
# Don't Remove Credit Tg - @VJ_Botz

import re
from pymongo import MongoClient
from Script import script
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors.exceptions.bad_request_400 import AccessTokenExpired, AccessTokenInvalid
import config

mongo_client = MongoClient(config.DB_URI)
mongo_db = mongo_client["cloned_vjbotz"]

@Client.on_message(filters.command("clone") & filters.private)
async def clone(client, message):
    if not config.CLONE_MODE:
        return 
    
    techvj = await client.ask(message.chat.id, "<b>1) sᴇɴᴅ <code>/newbot</code> ᴛᴏ @BotFather\n2) ɢɪᴠᴇ ᴀ ɴᴀᴍᴇ ꜰᴏʀ ʏᴏᴜʀ ʙᴏᴛ.\n3) ɢɪᴠᴇ ᴀ ᴜɴɪǫᴜᴇ ᴜsᴇʀɴᴀᴍᴇ.\n4) ᴛʜᴇɴ ʏᴏᴜ ᴡɪʟʟ ɢᴇᴛ ᴀ ᴍᴇssᴀɢᴇ ᴡɪᴛʜ ʏᴏᴜʀ ʙᴏᴛ ᴛᴏᴋᴇн.\n5) ꜰᴏʀᴡᴀʀᴅ ᴛʜᴀᴛ ᴍᴇssᴀɢᴇ ᴛᴏ ᴍᴇ.\n\n/cancel - ᴄᴀɴᴄᴇʟ ᴛʜɪs ᴘʀᴏᴄᴇss.</b>", timeout=300)
    
    if techvj.text == '/cancel':
        return await message.reply('<b>ᴄᴀɴᴄᴇʟᴇᴅ ᴛʜɪs ᴘʀᴏᴄᴇss 🚫</b>')
        
    if techvj.forward_from and techvj.forward_from.id == 93372553:
        try:
            bot_token = re.findall(r"\b(\d+:[A-Za-z0-9_-]+)\b", techvj.text)[0]
        except IndexError:
            return await message.reply('<b>That was not a valid token message from BotFather.</b>')
    else:
        return await message.reply('<b>Please forward the message directly from @BotFather.</b>')
        
    user_id = message.from_user.id
    msg = await message.reply_text("**👨‍💻 Please wait, I am creating your bot...**")
    
    try:
        cloned_client = Client(
            name=f"cloned_bot_{user_id}",
            api_id=config.API_ID, api_hash=config.API_HASH,
            bot_token=bot_token, plugins={"root": "clone_plugins"},
            in_memory=True
        )
        await cloned_client.start()
        bot = await cloned_client.get_me()
        
        details = {
            'bot_id': bot.id,
            'is_bot': True,
            'user_id': user_id,
            'name': bot.first_name,
            'token': bot_token,
            'username': bot.username,
            # --- New Settings Added by Gemini ---
            'custom_start_message': None,  # None means use default
            'auto_delete_settings': {
                'enabled': False,
                'time_in_minutes': 30
            }
        }
        mongo_db.bots.insert_one(details)
        await msg.edit_text(f"<b>sᴜᴄᴄᴇssғᴜʟʟʏ ᴄʟᴏɴᴇᴅ ʏᴏᴜʀ ʙᴏᴛ: @{bot.username}.</b>")
        
    except (AccessTokenExpired, AccessTokenInvalid):
        await msg.edit_text("<b>Error:</b> The provided bot token is invalid or has expired.")
    except Exception as e:
        await msg.edit_text(f"⚠️ <b>An unexpected error occurred:</b>\n\n<code>{e}</code>")

@Client.on_message(filters.command("deletecloned") & filters.private)
async def delete_cloned_bot(client, message):
    if not config.CLONE_MODE:
        return 
        
    techvj = await client.ask(message.chat.id, "**Please send me the Bot Token of the clone you want to delete.**", timeout=300)
    bot_token = techvj.text
    
    cloned_bot = mongo_db.bots.find_one({"token": bot_token})
    
    if cloned_bot:
        mongo_db.bots.delete_one({"token": bot_token})
        await message.reply_text("**🤖 The cloned bot's details have been successfully removed from the database.**")
    else:
        await message.reply_text("**⚠️ The bot token you provided is not in the cloned list.**")

async def restart_bots():
    bots = list(mongo_db.bots.find())
    if not bots:
        print("No cloned bots found to restart.")
        return
        
    print(f"Found {len(bots)} cloned bots to restart...")
    for bot in bots:
        bot_token = bot['token']
        try:
            cloned_client = Client(
                name=f"restarted_bot_{bot['bot_id']}",
                api_id=config.API_ID, api_hash=config.API_HASH,
                bot_token=bot_token, plugins={"root": "clone_plugins"},
                in_memory=True
            )
            await cloned_client.start()
            print(f"Successfully restarted @{bot['username']}")
        except Exception as e:
            print(f"Failed to restart @{bot['username']}. Error: {e}")
