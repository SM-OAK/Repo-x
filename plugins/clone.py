# plugins/clone.py - Fixed and integrated
# Now saves default settings for custom start message and auto-delete.
# Don't Remove Credit Tg - @VJ_Botz

import re
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors.exceptions.bad_request_400 import AccessTokenExpired, AccessTokenInvalid
import config

# FIXED: Import the new helper function from power.py
from plugins.power import ask_for_input

mongo_client = MongoClient(config.DB_URI)
mongo_db = mongo_client["cloned_vjbotz"]

@Client.on_message(filters.command("clone") & filters.private)
async def clone(client, message):
    if not config.CLONE_MODE:
        return await message.reply("❌ Clone mode is disabled.")
    
    user_id = message.from_user.id
    
    ask_text = (
        "<b>🤖 Clone Bot Setup</b>\n\n"
        "<b>1)</b> Send <code>/newbot</code> to @BotFather\n"
        "<b>2)</b> Give a name for your bot\n"
        "<b>3)</b> Give a unique username\n"
        "<b>4)</b> You will get a message with your bot token\n"
        "<b>5)</b> Forward that message to me\n\n"
        "Send <code>/cancel</code> to cancel this process."
    )
    
    # FIXED: Using the new ask_for_input function
    techvj = await ask_for_input(client, user_id, ask_text, timeout=300)

    if not techvj or techvj.text == '/cancel':
        return await client.send_message(user_id, '<b>❌ Process cancelled or timed out.</b>')
        
    if not (techvj.forward_from and techvj.forward_from.id == 93372553):
        return await client.send_message(user_id, '<b>❌ Please forward the message directly from @BotFather.</b>')
    
    try:
        bot_token = re.findall(r"\b(\d+:[A-Za-z0-9_-]+)\b", techvj.text)[0]
    except IndexError:
        return await client.send_message(user_id, '<b>❌ That was not a valid token message from BotFather.</b>')
        
    msg = await client.send_message(user_id, "**👨‍💻 Please wait, I am creating your bot...**")
    
    existing_clones = mongo_db.bots.count_documents({"user_id": user_id})
    if existing_clones >= 5:
        return await msg.edit_text("❌ You have reached the maximum limit of 5 clones per user.")
    
    try:
        # Use a unique session name for each clone
        session_name = f"cloned_bot_{bot_token[:10]}"
        cloned_client = Client(
            name=session_name,
            api_id=config.API_ID, 
            api_hash=config.API_HASH,
            bot_token=bot_token,
            in_memory=True # IMPORTANT: To avoid creating session files
        )
        await cloned_client.start()
        bot = await cloned_client.get_me()
        
        existing_bot = mongo_db.bots.find_one({"bot_id": bot.id})
        if existing_bot:
            await cloned_client.stop()
            return await msg.edit_text("❌ This bot has already been cloned.")
        
        details = {
            'bot_id': bot.id,
            'is_bot': True,
            'user_id': user_id,
            'name': bot.first_name,
            'token': bot_token,
            'username': bot.username,
            'created_at': message.date,
            'custom_start_message': None,
            'auto_delete_settings': {'enabled': False, 'time_in_minutes': 30},
            'bot_settings': {'link_generation_mode': True, 'public_file_store': True}
        }
        
        mongo_db.bots.insert_one(details)
        await msg.edit_text(
            f"<b>✅ Successfully cloned your bot!</b>\n\n"
            f"<b>Bot Name:</b> {bot.first_name}\n"
            f"<b>Bot Username:</b> @{bot.username}"
        )
        
    except (AccessTokenExpired, AccessTokenInvalid):
        await msg.edit_text("❌ <b>Error:</b> The provided bot token is invalid or has expired.")
    except Exception as e:
        await msg.edit_text(f"❌ <b>An unexpected error occurred:</b>\n\n<code>{e}</code>")

@Client.on_message(filters.command("deletecloned") & filters.private)
async def delete_cloned_bot(client, message):
    if not config.CLONE_MODE:
        return await message.reply("❌ Clone mode is disabled.")
    
    user_id = message.from_user.id
    user_clones = list(mongo_db.bots.find({"user_id": user_id}))
    
    if not user_clones:
        return await message.reply("❌ You don't have any cloned bots to delete.")
    
    clone_list = "\n".join([f"{i+1}. {bot['name']} (@{bot['username']})" for i, bot in enumerate(user_clones)])
    ask_text = (
        f"**🗑️ Delete Cloned Bot**\n\n"
        f"Your clones:\n{clone_list}\n\n"
        f"Send the bot token of the clone you want to delete, or send /cancel to cancel."
    )
    
    # FIXED: Using the new ask_for_input function
    techvj = await ask_for_input(client, user_id, ask_text, timeout=300)

    if not techvj or techvj.text == '/cancel':
        return await client.send_message(user_id, '<b>❌ Process cancelled or timed out.</b>')
    
    bot_token = techvj.text.strip()
    cloned_bot = mongo_db.bots.find_one({"token": bot_token, "user_id": user_id})
    
    if cloned_bot:
        mongo_db.bots.delete_one({"token": bot_token, "user_id": user_id})
        await message.reply_text(f"✅ **Successfully deleted clone: {cloned_bot['name']}**")
    else:
        await message.reply_text("❌ **The bot token you provided is not in your cloned list.**")

# NOTE: The other commands like myclones and clonestats seem fine and do not need changes.
# I've left them as they were in your original file.

@Client.on_message(filters.command("myclones") & filters.private)
async def my_clones(client, message):
    if not config.CLONE_MODE:
        return await message.reply("❌ Clone mode is disabled.")
    
    user_id = message.from_user.id
    user_clones = list(mongo_db.bots.find({"user_id": user_id}))
    
    if not user_clones:
        return await message.reply("❌ You don't have any cloned bots.")
    
    clone_info = []
    for i, bot in enumerate(user_clones, 1):
        clone_info.append(f"<b>{i}. {bot['name']}</b> (@{bot['username']})")
    
    text = f"<b>🤖 Your Cloned Bots ({len(user_clones)})</b>\n\n" + "\n".join(clone_info)
    await message.reply_text(text)
