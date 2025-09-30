import re
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import CLONE_MODE, API_ID, API_HASH, ADMINS
from database.clone_db import clone_db
from Script import script
import logging
import os

logger = logging.getLogger(__name__)

# Store active clone clients
active_clones = {}

# Clone callback handler
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
        script.CLONE_TEXT if hasattr(script, 'CLONE_TEXT') else 
        "<b>🤖 Clone Bot Manager</b>\n\nCreate your own file store bot!",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# Add clone handler
@Client.on_callback_query(filters.regex("^add_clone$"))
async def add_clone_callback(client, query: CallbackQuery):
    await query.message.edit_text(
        "<b>📝 Cʟᴏɴᴇ Cʀᴇᴀᴛɪᴏɴ Sᴛᴇᴘs:\n\n"
        "1) Sᴇɴᴅ <code>/newbot</code> ᴛᴏ @BotFather\n"
        "2) Gɪᴠᴇ ᴀ ɴᴀᴍᴇ ғᴏʀ ʏᴏᴜʀ ʙᴏᴛ\n"
        "3) Gɪᴠᴇ ᴀ ᴜɴɪǫᴜᴇ ᴜsᴇʀɴᴀᴍᴇ\n"
        "4) Fᴏʀᴡᴀʀᴅ ᴛʜᴇ ᴛᴏᴋᴇɴ ᴍᴇssᴀɢᴇ ᴛᴏ ᴍᴇ\n\n"
        "Use /clone command to start.</b>"
    )

@Client.on_message(filters.command("clone") & filters.private)
async def clone_command(client, message):
    if not CLONE_MODE:
        return await message.reply("Clone feature is disabled!")
    
    try:
        os.makedirs("clone_sessions", exist_ok=True)
        
        # Ask for bot token
        token_msg = await client.ask(
            message.chat.id,
            "<b>1) Sᴇɴᴅ <code>/newbot</code> ᴛᴏ @BotFather\n"
            "2) Gɪᴠᴇ ᴀ ɴᴀᴍᴇ ғᴏʀ ʏᴏᴜʀ ʙᴏᴛ\n"
            "3) Gɪᴠᴇ ᴀ ᴜɴɪǫᴜᴇ ᴜsᴇʀɴᴀᴍᴇ\n"
            "4) Fᴏʀᴡᴀʀᴅ ᴛʜᴇ ᴛᴏᴋᴇɴ ᴍᴇssᴀɢᴇ ᴛᴏ ᴍᴇ\n\n"
            "/cancel - Cᴀɴᴄᴇʟ ᴛʜɪs ᴘʀᴏᴄᴇss</b>",
            timeout=300
        )
        
        if token_msg.text == '/cancel':
            return await message.reply('Cᴀɴᴄᴇʟᴇᴅ! 🚫')
        
        # Validate token - must be forwarded from BotFather
        if not (token_msg.forward_from and token_msg.forward_from.id == 93372553):
            return await message.reply('❌ Nᴏᴛ ғᴏʀᴡᴀʀᴅᴇᴅ ғʀᴏᴍ @BotFather! Please forward the message.')
        
        # Extract token (flexible regex)
        try:
            bot_token = re.findall(r"\d{8,10}:[A-Za-z0-9_-]{30,}", token_msg.text)[0]
        except:
            return await message.reply('❌ Iɴᴠᴀʟɪᴅ ᴛᴏᴋᴇɴ ғᴏʀᴍᴀᴛ! Please try again.')
        
        # Check if token already exists
        existing = await clone_db.get_clone_by_token(bot_token)
        if existing:
            return await message.reply('⚠️ Tʜɪs ʙᴏᴛ ɪs ᴀʟʀᴇᴀᴅʏ ᴄʟᴏɴᴇᴅ!')
        
        msg = await message.reply_text("⏳ Cʀᴇᴀᴛɪɴɢ ʏᴏᴜʀ ᴄʟᴏɴᴇ ʙᴏᴛ...")
        
        try:
            # Use bot_id based session name
            clone_bot = Client(
                f"clone_sessions/clone_{message.from_user.id}",
                API_ID,
                API_HASH,
                bot_token=bot_token,
                plugins={"root": "clone_plugins"}
            )
            
            await clone_bot.start()
            bot_info = await clone_bot.get_me()
            
            # Save to database
            await clone_db.add_clone(
                bot_id=bot_info.id,
                user_id=message.from_user.id,
                bot_token=bot_token,
                username=bot_info.username,
                name=bot_info.first_name
            )
            
            # Store in active clones
            active_clones[bot_info.id] = clone_bot
            
            buttons = [
                [InlineKeyboardButton('📝 Cᴜsᴛᴏᴍɪᴢᴇ Cʟᴏɴᴇ', callback_data=f'customize_{bot_info.id}')],
                [InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data='clone')]
            ]
            
            await msg.edit_text(
                f"<b>✅ Sᴜᴄᴄᴇssғᴜʟʟʏ ᴄʟᴏɴᴇᴅ!\n\n"
                f"🤖 Bᴏᴛ: @{bot_info.username}\n"
                f"📝 Nᴀᴍᴇ: {bot_info.first_name}\n\n"
                f"Your bot is now running and ready to use!</b>",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            
        except Exception as e:
            logger.error(f"Clone creation error: {e}", exc_info=True)
            await msg.edit_text("⚠️ An error occurred while creating your clone. Please try again or contact support.")
            
    except Exception as e:
        logger.error(f"Clone process error: {e}", exc_info=True)
        await message.reply("⚠️ An unexpected error occurred. Please try again.")

# Manage clones (Admin only)
@Client.on_callback_query(filters.regex("^manage_clones$"))
async def manage_clones_callback(client, query: CallbackQuery):
    if query.from_user.id not in ADMINS:
        return await query.answer("Admin only!", show_alert=True)
    
    clones = await clone_db.get_all_clones()
    
    if not clones:
        return await query.answer("No clones created yet!", show_alert=True)
    
    buttons = []
    for clone in clones[:10]:
        buttons.append([
            InlineKeyboardButton(
                f"🤖 {clone['name']} (@{clone['username']})",
                callback_data=f"view_clone_{clone['bot_id']}"
            )
        ])
    
    buttons.append([InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data='start')])
    
    await query.message.edit_text(
        f"<b>📊 Tᴏᴛᴀʟ Cʟᴏɴᴇs: {len(clones)}</b>\n\nSᴇʟᴇᴄᴛ ᴀ ᴄʟᴏɴᴇ ᴛᴏ ᴠɪᴇᴡ ᴅᴇᴛᴀɪʟs:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# Delete clone
@Client.on_message(filters.command("deleteclone") & filters.private)
async def delete_clone_command(client, message):
    if not CLONE_MODE:
        return await message.reply("Clone feature is disabled!")
    
    try:
        token_msg = await client.ask(
            message.chat.id,
            "<b>Fᴏʀᴡᴀʀᴅ ᴛʜᴇ ᴛᴏᴋᴇɴ ᴍᴇssᴀɢᴇ ғʀᴏᴍ @BotFather\n\n"
            "Or paste the token manually\n\n"
            "/cancel to stop</b>",
            timeout=300
        )
        
        if token_msg.text == '/cancel':
            return await message.reply('Cᴀɴᴄᴇʟᴇᴅ!')
        
        bot_token = re.findall(r"\d{8,10}:[A-Za-z0-9_-]{30,}", token_msg.text)
        
        if not bot_token:
            return await message.reply("❌ Iɴᴠᴀʟɪᴅ ᴛᴏᴋᴇɴ!")
        
        bot_token = bot_token[0]
        
        # Get clone from database
        clone = await clone_db.get_clone_by_token(bot_token)
        
        if not clone:
            return await message.reply("❌ Cʟᴏɴᴇ ɴᴏᴛ ғᴏᴜɴᴅ in database!")
        
        if clone['user_id'] != message.from_user.id and message.from_user.id not in ADMINS:
            return await message.reply("❌ Tʜɪs ɪs ɴᴏᴛ ʏᴏᴜʀ ᴄʟᴏɴᴇ!")
        
        bot_id = clone['bot_id']
        if bot_id in active_clones:
            try:
                await active_clones[bot_id].stop()
                del active_clones[bot_id]
                logger.info(f"Stopped clone {bot_id}")
            except Exception as e:
                logger.warning(f"Failed to stop clone {bot_id}: {e}")
        
        await clone_db.delete_clone(bot_token)
        
        await message.reply("✅ Cʟᴏɴᴇ ᴅᴇʟᴇᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!")
        
    except Exception as e:
        logger.error(f"Delete clone error: {e}", exc_info=True)
        await message.reply("⚠️ Error while deleting clone. Please try again.")

# Restart all clones - patched
async def restart_bots():
    """Restart all clone bots from database"""
    if not CLONE_MODE:
        logger.info("Clone mode is disabled")
        return

    try:
        os.makedirs("clone_sessions", exist_ok=True)

        clones = await clone_db.get_all_clones()
        logger.info(f"🔄 Found {len(clones)} clones in database")

        for clone in clones:
            try:
                bot_id = clone['bot_id']
                bot_token = clone['bot_token']

                if bot_id in active_clones:
                    try:
                        await active_clones[bot_id].stop()
                        del active_clones[bot_id]
                    except Exception as e:
                        logger.warning(f"Failed to stop old session for {bot_id}: {e}")

                logger.info(f"Starting clone {bot_id}...")

                session_name = f"clone_sessions/clone_{bot_id}"

                client = Client(
                    session_name,
                    API_ID,
                    API_HASH,
                    bot_token=bot_token,
                    plugins={"root": "clone_plugins"}
                )

                await client.start()
                active_clones[bot_id] = client

                logger.info(f"✅ Restarted: @{clone['username']}")

                await asyncio.sleep(1)  # throttle

            except Exception as e:
                logger.error(f"❌ Failed to restart clone {clone.get('username', 'unknown')}: {e}")
                continue

        logger.info(f"✅ Successfully restarted {len(active_clones)} clones")

    except Exception as e:
        logger.error(f"Error in restart_bots: {e}", exc_info=True)
