# plugins/clone.py - Fixed and integrated by Claude
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
        return await message.reply("❌ Clone mode is disabled.")
    
    try:
        techvj = await client.ask(
            message.chat.id, 
            "<b>🤖 Clone Bot Setup</b>\n\n"
            "<b>1)</b> Send <code>/newbot</code> to @BotFather\n"
            "<b>2)</b> Give a name for your bot\n"
            "<b>3)</b> Give a unique username\n"
            "<b>4)</b> You will get a message with your bot token\n"
            "<b>5)</b> Forward that message to me\n\n"
            "Send <code>/cancel</code> to cancel this process.",
            timeout=300
        )
    except:
        return await message.reply("❌ Request timed out. Please try again.")
    
    if techvj.text == '/cancel':
        return await message.reply('<b>❌ Process cancelled</b>')
        
    # Validate token from BotFather
    if not (techvj.forward_from and techvj.forward_from.id == 93372553):
        return await message.reply('<b>❌ Please forward the message directly from @BotFather.</b>')
    
    try:
        bot_token = re.findall(r"\b(\d+:[A-Za-z0-9_-]+)\b", techvj.text)[0]
    except IndexError:
        return await message.reply('<b>❌ That was not a valid token message from BotFather.</b>')
        
    user_id = message.from_user.id
    msg = await message.reply_text("**👨‍💻 Please wait, I am creating your bot...**")
    
    # Check if user already has too many clones (optional limit)
    existing_clones = mongo_db.bots.count_documents({"user_id": user_id})
    if existing_clones >= 5:  # Limit to 5 clones per user
        return await msg.edit_text("❌ You have reached the maximum limit of 5 clones per user.")
    
    try:
        cloned_client = Client(
            name=f"cloned_bot_{user_id}_{bot_token[:10]}",  # Make name unique
            api_id=config.API_ID, 
            api_hash=config.API_HASH,
            bot_token=bot_token, 
            plugins={"root": "clone_plugins"},
            in_memory=True
        )
        await cloned_client.start()
        bot = await cloned_client.get_me()
        
        # Check if this bot is already cloned
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
            # Default settings
            'custom_start_message': None,  # None means use default
            'auto_delete_settings': {
                'enabled': False,
                'time_in_minutes': 30
            },
            'bot_settings': {
                'link_generation_mode': True,
                'public_file_store': True
            }
        }
        
        mongo_db.bots.insert_one(details)
        await msg.edit_text(
            f"<b>✅ Successfully cloned your bot!</b>\n\n"
            f"<b>Bot Name:</b> {bot.first_name}\n"
            f"<b>Bot Username:</b> @{bot.username}\n"
            f"<b>Bot ID:</b> <code>{bot.id}</code>\n\n"
            f"Your bot is now active and ready to use!"
        )
        
        # Keep the cloned client running (in a real scenario, you'd manage this differently)
        # await cloned_client.stop()  # Don't stop it immediately
        
    except (AccessTokenExpired, AccessTokenInvalid):
        await msg.edit_text("❌ <b>Error:</b> The provided bot token is invalid or has expired.")
    except Exception as e:
        print(f"Clone error: {e}")
        await msg.edit_text(f"❌ <b>An unexpected error occurred:</b>\n\n<code>{str(e)[:200]}</code>")

@Client.on_message(filters.command("deletecloned") & filters.private)
async def delete_cloned_bot(client, message):
    if not config.CLONE_MODE:
        return await message.reply("❌ Clone mode is disabled.")
    
    user_id = message.from_user.id
    user_clones = list(mongo_db.bots.find({"user_id": user_id}))
    
    if not user_clones:
        return await message.reply("❌ You don't have any cloned bots to delete.")
    
    try:
        # Show user their clones
        clone_list = "\n".join([f"{i+1}. {bot['name']} (@{bot['username']})" for i, bot in enumerate(user_clones)])
        techvj = await client.ask(
            message.chat.id, 
            f"**🗑️ Delete Cloned Bot**\n\n"
            f"Your clones:\n{clone_list}\n\n"
            f"Send the bot token of the clone you want to delete, or send /cancel to cancel.",
            timeout=300
        )
    except:
        return await message.reply("❌ Request timed out. Please try again.")
    
    if techvj.text == '/cancel':
        return await message.reply('❌ Process cancelled')
    
    bot_token = techvj.text.strip()
    cloned_bot = mongo_db.bots.find_one({"token": bot_token, "user_id": user_id})
    
    if cloned_bot:
        mongo_db.bots.delete_one({"token": bot_token, "user_id": user_id})
        await message.reply_text(f"✅ **Successfully deleted clone: {cloned_bot['name']} (@{cloned_bot['username']})**")
    else:
        await message.reply_text("❌ **The bot token you provided is not in your cloned list or doesn't exist.**")

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
        auto_del = bot.get('auto_delete_settings', {})
        custom_msg = "✅" if bot.get('custom_start_message') else "❌"
        auto_del_status = "✅" if auto_del.get('enabled') else "❌"
        
        clone_info.append(
            f"<b>{i}. {bot['name']}</b>\n"
            f"   • Username: @{bot['username']}\n"
            f"   • Custom Start Msg: {custom_msg}\n"
            f"   • Auto Delete: {auto_del_status}"
        )
    
    text = f"<b>🤖 Your Cloned Bots ({len(user_clones)})</b>\n\n" + "\n\n".join(clone_info)
    await message.reply_text(text)

@Client.on_message(filters.command("clonestats") & filters.user(config.ADMINS))
async def clone_stats(client, message):
    """Admin command to see clone statistics"""
    if not config.CLONE_MODE:
        return await message.reply("❌ Clone mode is disabled.")
    
    total_clones = mongo_db.bots.count_documents({})
    active_users = mongo_db.bots.distinct("user_id")
    
    # Get top users by clone count
    pipeline = [
        {"$group": {"_id": "$user_id", "clone_count": {"$sum": 1}}},
        {"$sort": {"clone_count": -1}},
        {"$limit": 5}
    ]
    top_users = list(mongo_db.bots.aggregate(pipeline))
    
    # Recent clones (last 24 hours)
    from datetime import datetime, timedelta
    yesterday = datetime.now() - timedelta(days=1)
    recent_clones = mongo_db.bots.count_documents({"created_at": {"$gte": yesterday}})
    
    stats_text = f"""
<b>📊 Clone Bot Statistics</b>

<b>Total Clones:</b> {total_clones}
<b>Active Users:</b> {len(active_users)}
<b>Recent Clones (24h):</b> {recent_clones}

<b>Top Users:</b>
"""
    
    for i, user in enumerate(top_users, 1):
        stats_text += f"{i}. User ID: <code>{user['_id']}</code> - {user['clone_count']} clones\n"
    
    await message.reply_text(stats_text)

async def restart_bots():
    """Function to restart all cloned bots on server restart."""
    bots = list(mongo_db.bots.find())
    if not bots:
        print("No cloned bots found to restart.")
        return
        
    print(f"Found {len(bots)} cloned bots to restart...")
    successful = 0
    failed = 0
    
    for bot in bots:
        bot_token = bot['token']
        try:
            cloned_client = Client(
                name=f"restarted_bot_{bot['bot_id']}",
                api_id=config.API_ID, 
                api_hash=config.API_HASH,
                bot_token=bot_token, 
                plugins={"root": "clone_plugins"},
                in_memory=True
            )
            await cloned_client.start()
            successful += 1
            print(f"Successfully restarted @{bot['username']}")
        except Exception as e:
            failed += 1
            print(f"Failed to restart @{bot['username']}. Error: {e}")
            # Optionally remove failed bots from database
            # mongo_db.bots.delete_one({"bot_id": bot['bot_id']})
    
    print(f"Restart complete: {successful} successful, {failed} failed")

async def cleanup_invalid_clones():
    """Function to clean up clones with invalid tokens"""
    bots = list(mongo_db.bots.find())
    cleaned = 0
    
    for bot in bots:
        try:
            test_client = Client(
                name=f"test_bot_{bot['bot_id']}",
                api_id=config.API_ID,
                api_hash=config.API_HASH,
                bot_token=bot['token'],
                in_memory=True
            )
            await test_client.start()
            await test_client.stop()
        except (AccessTokenExpired, AccessTokenInvalid):
            # Remove invalid bot from database
            mongo_db.bots.delete_one({"bot_id": bot['bot_id']})
            cleaned += 1
            print(f"Cleaned up invalid clone: @{bot['username']}")
        except Exception as e:
            print(f"Error checking @{bot['username']}: {e}")
    
    print(f"Cleanup complete: {cleaned} invalid clones removed")

# Export important functions
__all__ = ['restart_bots', 'cleanup_invalid_clones']
