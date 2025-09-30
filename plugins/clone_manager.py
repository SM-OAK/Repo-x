import re
import os
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from config import CLONE_MODE, API_ID, API_HASH, ADMINS
from database.clone_db import clone_db
from Script import script

logger = logging.getLogger(__name__)
active_clones = {}

@Client.on_callback_query(filters.regex("^clone$"))
async def clone_callback(client, query: CallbackQuery):
    if not CLONE_MODE:
        return await query.answer("Clone feature is disabled!", show_alert=True)
    
    buttons = [
        [InlineKeyboardButton('➕ ᴀᴅᴅ ᴄʟᴏɴᴇ', callback_data='add_clone')],
        [InlineKeyboardButton('❌ ᴅᴇʟᴇᴛᴇ ᴄʟᴏɴᴇ', callback_data='delete_clone')],
        [InlineKeyboardButton('🔙 ʙᴀᴄᴋ', callback_data='start')]
    ]
    await query.message.edit_text(
        script.CLONE_TEXT if hasattr(script, 'CLONE_TEXT') else "<b>🤖 Manage your Clone Bots</b>",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex("^add_clone$"))
async def add_clone_callback(client: Client, query: CallbackQuery):
    try:
        os.makedirs("clone_sessions", exist_ok=True)
        
        ask_msg = await query.message.edit_text(
            "<b>Please forward the message from @BotFather that contains your bot token.\n\n/cancel to stop the process.</b>"
        )

        token_msg = await client.ask(chat_id=query.from_user.id, timeout=300)

        if token_msg.text == '/cancel':
            return await ask_msg.edit_text('Cᴀɴᴄᴇʟᴇᴅ! 🚫', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Back', callback_data='clone')]]))

        if not (token_msg.forward_from and token_msg.forward_from.id == 93372553):
            return await ask_msg.edit_text('❌ Not a forwarded message from @BotFather.', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Retry', callback_data='add_clone')]]))

        try:
            bot_token = re.findall(r'(\d+:[A-Za-z0-9_-]+)', token_msg.text)[0]
        except IndexError:
            return await ask_msg.edit_text('❌ Invalid token format.', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Retry', callback_data='add_clone')]]))

        if await clone_db.get_clone_by_token(bot_token):
            return await ask_msg.edit_text('⚠️ This bot is already cloned!', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Back', callback_data='clone')]]))

        processing_msg = await ask_msg.edit_text("⏳ Creating your clone bot...")
        
        try:
            clone_bot = Client(
                f"clone_sessions/clone_{query.from_user.id}_{bot_token[:8]}",
                API_ID, API_HASH, bot_token=bot_token, plugins={"root": "clone_plugins"}
            )
            await clone_bot.start()
            bot_info = await clone_bot.get_me()
            
            await clone_db.add_clone(
                bot_id=bot_info.id, user_id=query.from_user.id, bot_token=bot_token,
                username=bot_info.username, name=bot_info.first_name
            )
            active_clones[bot_info.id] = clone_bot
            
            await processing_msg.edit_text(
                f"<b>✅ Successfully cloned!\n\n🤖 Bot: @{bot_info.username}</b>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Back to Clones', callback_data='clone')]])
            )
        except Exception as e:
            logger.error(f"Clone creation error: {e}", exc_info=True)
            await processing_msg.edit_text(f"⚠️ <b>Error:</b> <code>{e}</code>")

    except Exception as e:
        logger.error(f"Clone process error: {e}", exc_info=True)
        await query.message.reply_text("An error occurred or the process timed out.")

@Client.on_callback_query(filters.regex("^delete_clone$"))
async def delete_clone_callback(client: Client, query: CallbackQuery):
    try:
        ask_msg = await query.message.edit_text(
            "<b>Please send the token of the bot you wish to delete.\n\n/cancel to stop.</b>"
        )
        token_msg = await client.ask(chat_id=query.from_user.id, timeout=300)

        if token_msg.text == '/cancel':
            return await ask_msg.edit_text('Canceled!', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Back', callback_data='clone')]]))
        
        try:
            bot_token = re.findall(r'(\d+:[A-Za-z0-9_-]+)', token_msg.text)[0]
        except IndexError:
            return await ask_msg.edit_text('❌ Invalid token format.', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Retry', callback_data='delete_clone')]]))

        clone = await clone_db.get_clone_by_token(bot_token)
        if not clone or (clone['user_id'] != query.from_user.id and query.from_user.id not in ADMINS):
            return await ask_msg.edit_text("❌ This clone was not found in your account.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Back', callback_data='clone')]]))

        bot_id = clone['bot_id']
        if bot_id in active_clones:
            await active_clones[bot_id].stop()
            del active_clones[bot_id]

        await clone_db.delete_clone(bot_token)
        await ask_msg.edit_text("✅ Clone deleted successfully!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Back', callback_data='clone')]]))

    except Exception as e:
        logger.error(f"Delete clone error: {e}", exc_info=True)
        await query.message.reply_text("An error occurred or the process timed out.")
