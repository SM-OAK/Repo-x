import re
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import CLONE_MODE, API_ID, API_HASH, CLONE_DB_URI, CDB_NAME
from database.clone_db import clone_db
import logging

logger = logging.getLogger(__name__)

async def restart_bots(client):
    """Restart all existing clone bots from database and track their sessions."""
    logger.info("Restarting clone bots...")
    try:
        from pymongo import MongoClient
        mongo_client = MongoClient(CLONE_DB_URI)
        mongo_db = mongo_client[CDB_NAME]
        bots = list(mongo_db.bots.find())
        
        for bot in bots:
            bot_token = bot.get('token')
            bot_id = bot.get('bot_id')
            if not bot_token or not bot_id: continue
            
            try:
                clone_client = Client(f"clone_{bot_id}", API_ID, API_HASH, bot_token=bot_token, plugins={"root": "clone_plugins"})
                await clone_client.start()
                client.ACTIVE_CLONES[bot_id] = clone_client
                logger.info(f"Successfully restarted clone: {bot_id}")
            except Exception as e:
                logger.error(f"Failed to restart clone {bot_id}: {e}")
        logger.info("Clone restart process completed.")
    except Exception as e:
        logger.error(f"Error in restart_bots: {e}")

@Client.on_callback_query(filters.regex("^clone$"))
async def clone_callback(client, query: CallbackQuery):
    user_clones = await clone_db.get_user_clones(query.from_user.id)
    buttons = [[InlineKeyboardButton(f"🤖 {clone['name']}", callback_data=f"customize_{clone['bot_id']}")] for clone in user_clones]
    buttons.append([InlineKeyboardButton('➕ ᴀᴅᴅ ɴᴇᴡ ᴄʟᴏɴᴇ', callback_data='add_clone')])
    buttons.append([InlineKeyboardButton('🔙 ʙᴀᴄᴋ', callback_data='start')])
    text = "✨ **Mᴀɴᴀɢᴇ Yᴏᴜʀ Cʟᴏɴᴇs**" if user_clones else "✨ **Nᴏ Cʟᴏɴᴇs Fᴏᴜɴᴅ**"
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex("^add_clone$"))
async def add_clone_callback(client, query: CallbackQuery):
    try:
        back_button = InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data='clone')]])
        await query.message.edit_text("Fᴏʀᴡᴀʀᴅ ᴛʜᴇ ᴍᴇssᴀɢᴇ ғʀᴏᴍ @BotFather ᴛʜᴀᴛ ᴄᴏɴᴛᴀɪɴs ʏᴏᴜʀ ᴛᴏᴋᴇɴ.", reply_markup=back_button)
        
        token_msg = await client.ask(chat_id=query.from_user.id, filters=filters.forwarded, timeout=300)
        
        if not (token_msg.forward_from and token_msg.forward_from.id == 93372553):
            return await query.message.edit_text('Nᴏᴛ ғᴏʀᴡᴀʀᴅᴇᴅ ғʀᴏᴍ @BotFather!', reply_markup=back_button)

        bot_token = re.findall(r"\b(\d+:[A-Za-z0-9_-]+)\b", token_msg.text)[0]
        msg = await query.message.edit_text("⏳ Cʀᴇᴀᴛɪɴɢ ʏᴏᴜʀ ᴄʟᴏɴᴇ ʙᴏᴛ...")
        
        clone_bot = Client(f"clone_{bot_token[:8]}", API_ID, API_HASH, bot_token=bot_token, plugins={"root": "clone_plugins"})
        await clone_bot.start()
        bot_info = await clone_bot.get_me()
        client.ACTIVE_CLONES[bot_info.id] = clone_bot # Track session
        
        await clone_db.add_clone(
            bot_id=bot_info.id, user_id=query.from_user.id, bot_token=bot_token,
            username=bot_info.username, name=bot_info.first_name
        )
        await msg.edit_text(f"✅ Sᴜᴄᴄᴇssғᴜʟʟʏ ᴄʟᴏɴᴇᴅ @{bot_info.username}!")
    except asyncio.TimeoutError:
        await query.message.edit_text("Tɪᴍᴇᴏᴜᴛ! Pʀᴏᴄᴇss Cᴀɴᴄᴇʟʟᴇᴅ.", reply_markup=back_button)
    except Exception as e:
        logger.error(f"Clone creation error: {e}")
        await query.message.edit_text(f"⚠️ <b>Eʀʀᴏʀ:</b> <code>{e}</code>", reply_markup=back_button)
    
    await asyncio.sleep(2)
    await clone_callback(client, query) # Refresh menu
