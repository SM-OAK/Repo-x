# plugins/clone_manager.py
import re
import os
import glob
import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.raw.functions.bots import SetBotCommands
from pyrogram.raw.types import BotCommand, BotCommandScopeDefault

try:
    from pyrogram.errors import ListenerTimeout
except ImportError:
    class ListenerTimeout(Exception):
        pass

from config import CLONE_MODE, API_ID, API_HASH, ADMINS
from database.clone_db import clone_db
from Script import script

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Active clones
active_clones = {}

# ==================== AUTO SETUP BOT COMMANDS ====================
async def setup_bot_commands(client):
    """Automatically configure bot commands via Telegram API."""
    commands = [
        ("start", "🚀 Start the bot"),
        ("help", "❓ Get help information"),
        ("about", "ℹ️ About the bot"),
        ("batch", "📦 Manual batch (collect files)"),
        ("genbatch", "⚡ Quick batch (from channel range)"),
        ("done", "✅ Finish batch and get link"),
        ("cancel", "❌ Cancel current batch")
    ]
    
    try:
        bot_commands = [BotCommand(command=cmd, description=desc) for cmd, desc in commands]
        
        await client.invoke(
            SetBotCommands(
                scope=BotCommandScopeDefault(),
                lang_code="en",
                commands=bot_commands
            )
        )
        logger.info(f"✅ Commands set for @{client.me.username}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to set commands for {client.me.username}: {e}")
        return False

# ==================== CLONE MENU ====================
@Client.on_callback_query(filters.regex("^clone$"))
async def clone_management_menu(client, query: CallbackQuery):
    if not CLONE_MODE:
        return await query.answer("Clone feature is disabled!", show_alert=True)

    user_id = query.from_user.id
    buttons = []
    
    clones = await clone_db.get_clones_by_user(user_id)
    if user_id in ADMINS:
        clones = await clone_db.get_all_clones()

    if not clones:
        reply_text = "✨ **No Clones Found**\n\nCreate your first clone bot now!"
    else:
        reply_text = "✨ **Manage Your Clones**\n\nSelect a bot to customize or create a new one."
        for clone in clones:
            status = "🟢" if clone.get('is_active', True) else "🔴"
            buttons.append(
                [InlineKeyboardButton(f"{status} {clone['name']}", callback_data=f"customize_{clone['bot_id']}")]
            )

    buttons.append([InlineKeyboardButton('➕ Create New Clone', callback_data='add_clone')])
    buttons.append([InlineKeyboardButton('🔙 Back', callback_data='start')])

    await query.message.edit_text(reply_text, reply_markup=InlineKeyboardMarkup(buttons))

# ==================== CUSTOMIZE MENU ====================
@Client.on_callback_query(filters.regex("^customize_"))
async def customize_clone(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    clone = await clone_db.get_clone(bot_id)

    if not clone:
        return await query.answer("Clone not found!", show_alert=True)
        
    if clone['user_id'] != query.from_user.id and query.from_user.id not in ADMINS:
        return await query.answer("This is not your bot!", show_alert=True)

    status = "🟢 Active" if clone.get('is_active', True) else "🔴 Inactive"
    
    buttons = [
        [
            InlineKeyboardButton('🎨 Appearance', callback_data=f'appearance_{bot_id}'),
            InlineKeyboardButton('🔒 Security', callback_data=f'security_{bot_id}')
        ],
        [
            InlineKeyboardButton('📁 Files', callback_data=f'files_{bot_id}'),
            InlineKeyboardButton('📊 Database', callback_data=f'database_{bot_id}')
        ],
        [
            InlineKeyboardButton('👥 Admins', callback_data=f'admins_{bot_id}'),
            InlineKeyboardButton('⚙️ Settings', callback_data=f'bot_settings_{bot_id}')
        ],
        [
            InlineKeyboardButton('🔄 Restart Bot', callback_data=f'restart_{bot_id}'),
            InlineKeyboardButton('🗑️ Delete', callback_data=f'delete_clone_{bot_id}')
        ],
        [InlineKeyboardButton('🔙 Back to Clones', callback_data='clone')]
    ]

    await query.message.edit_text(
        f"<b>🤖 {clone['name']}</b>\n"
        f"<b>Username:</b> @{clone['username']}\n"
        f"<b>Status:</b> {status}\n\n"
        f"<i>Select category to customize:</i>",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ==================== CORE CLONE CREATION ====================
async def start_clone_process(client, chat_id, user_id, message_to_edit=None):
    """Core clone creation with auto command setup."""
    if not CLONE_MODE:
        text = "❌ Clone feature is disabled!"
        if message_to_edit:
            return await message_to_edit.edit_text(text)
        return await client.send_message(chat_id, text)

    try:
        os.makedirs("clone_sessions", exist_ok=True)

        # Ask for token
        try:
            token_msg = await client.ask(
                chat_id,
                "<b>📝 Forward the message from @BotFather containing your bot token.</b>\n\n"
                "💡 <i>The token looks like: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz</i>\n\n"
                "Use /cancel to stop.",
                timeout=300
            )
        except (ListenerTimeout, TimeoutError, asyncio.TimeoutError):
            text = "⏱️ **Timeout!** Please try again."
            if message_to_edit:
                return await message_to_edit.edit_text(text)
            return await client.send_message(chat_id, text)

        # Check cancel
        if token_msg.text and token_msg.text.lower() == '/cancel':
            text = "❌ Process cancelled!"
            if message_to_edit:
                return await message_to_edit.edit_text(text)
            return await client.send_message(chat_id, text)

        # Validate BotFather forward
        if not (token_msg.forward_from and token_msg.forward_from.id == 93372553):
            text = "❌ **Error:** Please forward from @BotFather only!"
            if message_to_edit:
                return await message_to_edit.edit_text(text)
            return await client.send_message(chat_id, text)

        # Extract token
        tokens = re.findall(r'\d[0-9]{8,10}:[0-9A-Za-z_-]{35}', token_msg.text)
        if not tokens:
            text = "❌ **Invalid Token:** No valid token found!"
            if message_to_edit:
                return await message_to_edit.edit_text(text)
            return await client.send_message(chat_id, text)
        
        bot_token = tokens[0]

        # Check duplicate
        if await clone_db.get_clone_by_token(bot_token):
            text = "⚠️ **Already Cloned:** This bot already exists!"
            if message_to_edit:
                return await message_to_edit.edit_text(text)
            return await client.send_message(chat_id, text)

        # Show progress
        if message_to_edit:
            msg = message_to_edit
            await msg.edit_text("⏳ Creating your clone bot...\n\n<i>Step 1/3: Verifying token...</i>")
        else:
            msg = await client.send_message(chat_id, "⏳ Creating your clone bot...\n\n<i>Step 1/3: Verifying token...</i>")

        try:
            # Get bot info
            temp_session = f"clone_sessions/temp_{user_id}"
            temp_client = Client(temp_session, API_ID, API_HASH, bot_token=bot_token)
            
            await msg.edit_text("⏳ Creating your clone bot...\n\n<i>Step 2/3: Connecting to Telegram...</i>")
            await temp_client.start()
            bot_info = await temp_client.get_me()
            
            # Auto-setup commands
            await msg.edit_text("⏳ Creating your clone bot...\n\n<i>Step 3/3: Setting up commands...</i>")
            commands_set = await setup_bot_commands(temp_client)
            
            await temp_client.stop()
            
            # Clean temp files
            for file in glob.glob(f"{temp_session}*"):
                try:
                    os.remove(file)
                except:
                    pass

            # Start permanent clone
            session_name = f"clone_sessions/{bot_info.id}"
            clone_bot = Client(
                session_name, 
                API_ID, 
                API_HASH, 
                bot_token=bot_token, 
                plugins={"root": "clone_plugins"}
            )
            await clone_bot.start()

            # Save to database
            await clone_db.add_clone(
                bot_id=bot_info.id,
                user_id=user_id,
                bot_token=bot_token,
                username=bot_info.username,
                name=bot_info.first_name
            )

            active_clones[bot_info.id] = clone_bot

            # Success message
            cmd_status = "✅ Commands configured automatically!" if commands_set else "⚠️ Commands setup failed (manual setup required)"
            
            buttons = [
                [InlineKeyboardButton('🛠️ Customize Your Clone', callback_data=f'customize_{bot_info.id}')],
                [InlineKeyboardButton('📋 View Commands', callback_data=f'view_commands_{bot_info.id}')],
                [InlineKeyboardButton('🔙 Back to Clones', callback_data='clone')]
            ]
            
            await msg.edit_text(
                f"<b>✅ Clone Created Successfully!</b>\n\n"
                f"<b>🤖 Bot:</b> @{bot_info.username}\n"
                f"<b>📝 Name:</b> {bot_info.first_name}\n"
                f"<b>🆔 ID:</b> <code>{bot_info.id}</code>\n\n"
                f"<b>Commands:</b> {cmd_status}\n\n"
                f"<i>Your bot is ready to use! Start customizing now.</i>",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        except Exception as e:
            logger.error(f"Clone creation error: {e}", exc_info=True)
            await msg.edit_text(
                f"❌ <b>Error creating clone:</b>\n\n<code>{str(e)}</code>\n\n"
                f"<i>Please check your token and try again.</i>"
            )

    except Exception as e:
        logger.error(f"Clone process error: {e}", exc_info=True)
        text = f"❌ <b>Unexpected Error:</b>\n\n<code>{str(e)}</code>"
        if message_to_edit:
            return await message_to_edit.edit_text(text)
        return await client.send_message(chat_id, text)

# ==================== ADD CLONE BUTTON ====================
@Client.on_callback_query(filters.regex("^add_clone$"))
async def add_clone_callback(client, query: CallbackQuery):
    await query.answer()
    try:
        await query.message.delete()
    except:
        pass
    await start_clone_process(client, query.message.chat.id, query.from_user.id)

# ==================== CLONE COMMAND ====================
@Client.on_message(filters.command("clone") & filters.private)
async def clone_command(client, message):
    await start_clone_process(client, message.chat.id, message.from_user.id)

# ==================== VIEW COMMANDS ====================
@Client.on_callback_query(filters.regex("^view_commands_"))
async def view_commands(client, query: CallbackQuery):
    await query.answer()
    
    commands_text = """<b>📋 Bot Commands List:</b>

<b>Basic Commands:</b>
• <b>/start</b> - 🚀 Start bot & access files
• <b>/help</b> - ❓ Get help instructions  
• <b>/about</b> - ℹ️ Learn about the bot

<b>📦 Batch Commands:</b>
• <b>/batch</b> - Manual batch (collect files one by one)
• <b>/genbatch</b> - ⚡ Quick batch (from channel range - FAST!)
• <b>/done</b> - Finish batch and generate link
• <b>/cancel</b> - Cancel current batch

<b>💡 Batch Types:</b>

<b>1️⃣ Manual Batch (/batch):</b>
└ Collect files one by one
└ Send /done when finished
└ Good for selective files

<b>2️⃣ Quick Batch (/genbatch):</b>
└ Forward first & last message from channel
└ Instant batch creation - SUPER FAST!
└ Good for bulk files (100s of files in seconds!)

<i>✅ All commands are pre-configured!</i>"""

    buttons = [[InlineKeyboardButton('🔙 Back', callback_data=f'customize_{query.data.split("_")[2]}')]]
    
    await query.message.edit_text(commands_text, reply_markup=InlineKeyboardMarkup(buttons))

# ==================== RESTART CLONE ====================
@Client.on_callback_query(filters.regex("^restart_"))
async def restart_clone(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    clone = await clone_db.get_clone(bot_id)
    
    if not clone:
        return await query.answer("Clone not found!", show_alert=True)
    
    if clone['user_id'] != query.from_user.id and query.from_user.id not in ADMINS:
        return await query.answer("Not your clone!", show_alert=True)
    
    await query.answer("🔄 Restarting...", show_alert=False)
    
    try:
        # Stop if running
        if bot_id in active_clones:
            await active_clones[bot_id].stop()
            await asyncio.sleep(0.5)
            active_clones.pop(bot_id, None)
        
        # Restart
        session_name = f"clone_sessions/{bot_id}"
        clone_bot = Client(
            session_name,
            API_ID,
            API_HASH,
            bot_token=clone['bot_token'],
            plugins={"root": "clone_plugins"}
        )
        await clone_bot.start()
        
        # Re-setup commands
        await setup_bot_commands(clone_bot)
        
        active_clones[bot_id] = clone_bot
        
        await query.message.edit_text(
            f"<b>✅ Restarted Successfully!</b>\n\n"
            f"<b>🤖 Bot:</b> @{clone['username']}\n"
            f"<i>Your bot is now online with updated commands.</i>",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton('🔙 Back', callback_data=f'customize_{bot_id}')
            ]])
        )
        
    except Exception as e:
        logger.error(f"Restart error: {e}")
        await query.message.edit_text(
            f"❌ <b>Restart Failed:</b>\n\n<code>{e}</code>",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton('🔙 Back', callback_data=f'customize_{bot_id}')
            ]])
        )

# ==================== DELETE CLONE ====================
@Client.on_callback_query(filters.regex("^delete_clone_"))
async def delete_clone_button_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    
    if not clone:
        return await query.answer("Clone not found!", show_alert=True)

    user_id = query.from_user.id
    if clone['user_id'] != user_id and user_id not in ADMINS:
        return await query.answer("❌ Not your clone!", show_alert=True)

    # Stop bot
    if bot_id in active_clones:
        try:
            await active_clones[bot_id].stop()
            await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Stop error: {e}")
        finally:
            active_clones.pop(bot_id, None)

    # Delete files
    try:
        for file in glob.glob(f"clone_sessions/{bot_id}*"):
            try:
                os.remove(file)
            except Exception as e:
                logger.error(f"File delete error: {e}")
    except Exception as e:
        logger.error(f"Cleanup error: {e}")

    # Delete from DB
    await clone_db.delete_clone_by_id(bot_id)
    
    await clone_management_menu(client, query)
    await query.answer("✅ Clone deleted successfully!", show_alert=True)

# ==================== RESTART ALL CLONES ====================
async def restart_bots():
    """Restart all clones on bot startup."""
    if not CLONE_MODE:
        logger.info("Clone mode disabled")
        return

    os.makedirs("clone_sessions", exist_ok=True)
    clones = await clone_db.get_all_clones()
    logger.info(f"🔄 Found {len(clones)} clones")

    success = 0
    for clone in clones:
        bot_id = clone['bot_id']
        
        if bot_id in active_clones:
            logger.info(f"⚠️ Clone {bot_id} already running")
            success += 1
            continue
        
        try:
            session_name = f"clone_sessions/{bot_id}"
            client = Client(
                session_name, 
                API_ID, 
                API_HASH, 
                bot_token=clone['bot_token'], 
                plugins={"root": "clone_plugins"}
            )
            await client.start()
            
            # Setup commands on restart
            await setup_bot_commands(client)
            
            active_clones[bot_id] = client
            success += 1
            logger.info(f"✅ Restarted: @{clone['username']}")
        except Exception as e:
            logger.error(f"❌ Failed @{clone['username']}: {e}")

    logger.info(f"✅ Restarted {success}/{len(clones)} clones")

# ==================== STOP ALL CLONES ====================
async def stop_all_clones():
    """Stop all running clones."""
    if not active_clones:
        return
    
    logger.info(f"🛑 Stopping {len(active_clones)} clones...")
    stopped = 0
    
    for bot_id, client in list(active_clones.items()):
        try:
            await client.stop()
            stopped += 1
            logger.info(f"✅ Stopped {bot_id}")
        except Exception as e:
            logger.error(f"❌ Error stopping {bot_id}: {e}")
    
    active_clones.clear()
    logger.info(f"✅ Stopped {stopped} clones")
