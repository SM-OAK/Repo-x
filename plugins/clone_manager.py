import re
import os
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import CLONE_MODE, API_ID, API_HASH, ADMINS
from database.clone_db import clone_db
from Script import script

logger = logging.getLogger(__name__)

# Store active clone clients
active_clones = {}

# -----------------------------
# Clone callback
# -----------------------------
@Client.on_callback_query(filters.regex("^clone$"))
async def clone_callback(client, query: CallbackQuery):
    if not CLONE_MODE:
        return await query.answer("Clone feature is disabled!", show_alert=True)
    
    buttons = [
        [InlineKeyboardButton('➕ Add Clone', callback_data='add_clone')],
        [InlineKeyboardButton('❌ Delete Clone', callback_data='delete_clone')],
        [InlineKeyboardButton('🔙 Back', callback_data='start')]
    ]
    
    await query.message.edit_text(
        getattr(script, 'CLONE_TEXT', "<b>🤖 Clone Bot Manager</b>\n\nCreate your own file store bot!"),
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# -----------------------------
# Add Clone
# -----------------------------
@Client.on_callback_query(filters.regex("^add_clone$"))
async def add_clone_callback(client, query: CallbackQuery):
    await query.message.edit_text(
        "<b>📝 Clone Creation Steps:</b>\n\n"
        "1) Send <code>/newbot</code> to @BotFather\n"
        "2) Give a name for your bot\n"
        "3) Give a unique username\n"
        "4) Forward the token message here\n\n"
        "Use /clone command to start."
    )

@Client.on_message(filters.command("clone") & filters.private)
async def clone_command(client, message):
    if not CLONE_MODE:
        return await message.reply("Clone feature is disabled!")

    try:
        os.makedirs("clone_sessions", exist_ok=True)

        token_msg = await client.ask(
            message.chat.id,
            "<b>Forward your BotFather message or paste the token here.\n\n/cancel to stop</b>",
            timeout=300
        )

        if token_msg.text == '/cancel':
            return await message.reply("Canceled!")

        # Validate forwarded from BotFather
        if not (token_msg.forward_from and token_msg.forward_from.id == 93372553):
            return await message.reply("❌ Not forwarded from @BotFather!")

        # Extract bot token
        try:
            bot_token = re.findall(r'\d[0-9]{8,10}:[0-9A-Za-z_-]{35}', token_msg.text)[0]
        except:
            return await message.reply("❌ Invalid token format!")

        # Check if already exists
        existing = await clone_db.get_clone_by_token(bot_token)
        if existing:
            return await message.reply("⚠️ This bot is already cloned!")

        # Create clone
        msg = await message.reply_text("⏳ Creating your clone bot...")

        try:
            session_name = f"clone_sessions/clone_{message.from_user.id}_{bot_token[:8]}"
            clone_bot = Client(session_name, API_ID, API_HASH, bot_token=bot_token, plugins={"root": "clone_plugins"})
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

            # Store active clone
            active_clones[bot_info.id] = clone_bot

            buttons = [
                [InlineKeyboardButton('📝 Customize Clone', callback_data=f'customize_{bot_info.id}')],
                [InlineKeyboardButton('🔙 Back', callback_data='clone')]
            ]

            await msg.edit_text(
                f"<b>✅ Successfully cloned!\n\n"
                f"🤖 Bot: @{bot_info.username}\n"
                f"📝 Name: {bot_info.first_name}</b>",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        except Exception as e:
            logger.error(f"Clone creation error: {e}", exc_info=True)
            await msg.edit_text(f"⚠️ Error:\n<code>{e}</code>\nPlease contact support.")

    except Exception as e:
        logger.error(f"Clone process error: {e}", exc_info=True)
        await message.reply(f"An error occurred: {str(e)}")

# -----------------------------
# Manage clones
# -----------------------------
@Client.on_callback_query(filters.regex("^manage_clones$"))
async def manage_clones_callback(client, query: CallbackQuery):
    user_id = query.from_user.id

    # Admin sees all clones, user sees own clones
    if user_id in ADMINS:
        clones = await clone_db.get_all_clones()
    else:
        clones = await clone_db.get_clones_by_user(user_id)

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
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data='start')])

    await query.message.edit_text(
        f"<b>📊 Total Clones: {len(clones)}</b>\n\nSelect a clone to view details:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# -----------------------------
# Delete clone
# -----------------------------
@Client.on_message(filters.command("deleteclone") & filters.private)
async def delete_clone_command(client, message):
    if not CLONE_MODE:
        return await message.reply("Clone feature is disabled!")

    try:
        token_msg = await client.ask(
            message.chat.id,
            "<b>Forward the token message or paste manually.\n/cancel to stop</b>",
            timeout=300
        )
        if token_msg.text == '/cancel':
            return await message.reply("Canceled!")

        bot_token = re.findall(r'\d[0-9]{8,10}:[0-9A-Za-z_-]{35}', token_msg.text)
        if not bot_token:
            return await message.reply("❌ Invalid token!")
        bot_token = bot_token[0]

        clone = await clone_db.get_clone_by_token(bot_token)
        if not clone:
            return await message.reply("❌ Clone not found in database!")

        # Ownership check
        if clone['user_id'] != message.from_user.id and message.from_user.id not in ADMINS:
            return await message.reply("❌ This is not your clone!")

        # Stop if running
        bot_id = clone['bot_id']
        if bot_id in active_clones:
            try:
                await active_clones[bot_id].stop()
                del active_clones[bot_id]
            except:
                pass

        # Delete from DB
        await clone_db.delete_clone(bot_token)
        await message.reply("✅ Clone deleted successfully!")

    except Exception as e:
        logger.error(f"Delete clone error: {e}", exc_info=True)
        await message.reply(f"Error: {str(e)}")

# -----------------------------
# Restart all clones
# -----------------------------
async def restart_bots():
    """Restart all clones from DB"""
    if not CLONE_MODE:
        logger.info("Clone mode is disabled")
        return

    os.makedirs("clone_sessions", exist_ok=True)
    clones = await clone_db.get_all_clones()
    logger.info(f"🔄 Found {len(clones)} clones in DB")

    for clone in clones:
        try:
            bot_id = clone['bot_id']
            bot_token = clone['bot_token']

            try:
                # Try new session name
                session_name = f"clone_sessions/clone_{bot_id}"
                client = Client(session_name, API_ID, API_HASH, bot_token=bot_token, plugins={"root": "clone_plugins"})
                await client.start()
            except:
                # Backward compatible: old session name
                old_session_name = f"clone_sessions/clone_{clone['user_id']}_{bot_token[:8]}"
                client = Client(old_session_name, API_ID, API_HASH, bot_token=bot_token, plugins={"root": "clone_plugins"})
                await client.start()

            active_clones[bot_id] = client
            logger.info(f"✅ Restarted: @{clone['username']}")

        except Exception as e:
            logger.error(f"❌ Failed to restart clone {clone.get('username', 'unknown')}: {e}")
            continue

    logger.info(f"✅ Successfully restarted {len(active_clones)} clones")
