# plugins/clone.py - Fixed and integrated

import re
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import AccessTokenExpired, AccessTokenInvalid
import config
from plugins.power import ask_for_input

mongo_client = MongoClient(config.DB_URI)
mongo_db = mongo_client["cloned_vjbotz"]
bots_collection = mongo_db["bots"]

@Client.on_message(filters.command("clone") & filters.private)
async def clone(client, message):
    if not config.CLONE_MODE:
        return await message.reply("❌ Clone mode is disabled.")
    
    user_id = message.from_user.id
    ask_text = (
        "<b>🤖 Clone Bot Setup</b>\n\n"
        "Please forward the message from @BotFather that contains your new bot's token.\n\n"
        "Send <code>/cancel</code> to cancel this process."
    )
    
    techvj = await ask_for_input(client, user_id, ask_text, timeout=300)

    if not techvj: return
        
    if not (techvj.forward_from and techvj.forward_from.id == 93372553):
        return await client.send_message(user_id, '<b>❌ Please forward the message directly from @BotFather.</b>')
    
    try:
        bot_token = re.findall(r"\b(\d+:[A-Za-z0-9_-]+)\b", techvj.text)[0]
    except IndexError:
        return await client.send_message(user_id, '<b>❌ That was not a valid token message.</b>')
        
    msg = await client.send_message(user_id, "**👨‍💻 Please wait, creating your bot...**")
    
    if bots_collection.count_documents({"user_id": user_id}) >= 5:
        return await msg.edit_text("❌ You have reached the maximum limit of 5 clones.")
    
    try:
        cloned_client = Client(name=f"cloned_bot_{bot_token[:10]}", api_id=config.API_ID, api_hash=config.API_HASH, bot_token=bot_token, in_memory=True)
        await cloned_client.start()
        bot = await cloned_client.get_me()
        
        if bots_collection.find_one({"bot_id": bot.id}):
            await cloned_client.stop()
            return await msg.edit_text("❌ This bot has already been cloned.")
        
        details = {
            'bot_id': bot.id, 'user_id': user_id, 'name': bot.first_name, 'token': bot_token,
            'username': bot.username, 'created_at': message.date, 'custom_start_message': None,
            'auto_delete_settings': {'enabled': False, 'time_in_minutes': 30}
        }
        bots_collection.insert_one(details)
        await msg.edit_text(f"<b>✅ Successfully cloned @{bot.username}!</b>")
        
    except (AccessTokenExpired, AccessTokenInvalid):
        await msg.edit_text("❌ <b>Error:</b> The provided bot token is invalid or has expired.")
    except Exception as e:
        await msg.edit_text(f"❌ <b>An unexpected error occurred:</b>\n\n<code>{e}</code>")

@Client.on_message(filters.command("deletecloned") & filters.private)
async def delete_cloned_bot(client, message):
    user_id = message.from_user.id
    user_clones = list(bots_collection.find({"user_id": user_id}))
    
    if not user_clones:
        return await message.reply("❌ You don't have any cloned bots to delete.")
    
    clone_list = "\n".join([f"{i+1}. {bot['name']} (@{bot['username']})" for i, bot in enumerate(user_clones)])
    ask_text = f"**🗑️ Your clones:**\n{clone_list}\n\nSend the token of the clone you want to delete."
    
    techvj = await ask_for_input(client, user_id, ask_text, timeout=300)
    if not techvj or not techvj.text: return
    
    bot_token = techvj.text.strip()
    cloned_bot = bots_collection.find_one_and_delete({"token": bot_token, "user_id": user_id})
    
    if cloned_bot:
        await message.reply_text(f"✅ **Successfully deleted clone: {cloned_bot['name']}**")
    else:
        await message.reply_text("❌ **Bot token not found in your cloned list.**")
