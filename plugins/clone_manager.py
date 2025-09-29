import re
import logging
from pyrofork import Client, filters   # ✅ switched to pyrofork
from pyrofork.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import CLONE_MODE, API_ID, API_HASH, ADMINS
from database.clone_db import clone_db
from Script import script

logger = logging.getLogger(__name__)

# Clone menu callback
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
        script.CLONE_TEXT,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# Add clone handler
@Client.on_callback_query(filters.regex("^add_clone$"))
async def add_clone_callback(client, query: CallbackQuery):
    await query.message.edit_text(
        "<b>📝 Clone Creation Steps:\n\n"
        "1) Send <code>/newbot</code> to @BotFather\n"
        "2) Give a name for your bot\n"
        "3) Choose a unique username\n"
        "4) Forward the token message here\n\n"
        "Use /cancel to stop this process.</b>"
    )

# Clone command (manual creation)
@Client.on_message(filters.command("clone") & filters.private)
async def clone_command(client, message):
    if not CLONE_MODE:
        return await message.reply("Clone feature is disabled!")

    try:
        # Ask for bot token
        token_msg = await client.ask(
            message.chat.id,
            "<b>1) Send <code>/newbot</code> to @BotFather\n"
            "2) Give a name for your bot\n"
            "3) Choose a unique username\n"
            "4) Forward the token message here\n\n"
            "/cancel - Cancel this process</b>",
            timeout=300
        )

        if token_msg.text == '/cancel':
            return await message.reply("❌ Cancelled!")

        # Check token forwarded from BotFather
        if not (token_msg.forward_from and token_msg.forward_from.id == 93372553):
            return await message.reply("❌ Not forwarded from @BotFather!")

        # Extract token
        try:
            bot_token = re.findall(r"\b(\d+:[A-Za-z0-9_-]+)\b", token_msg.text)[0]
        except:
            return await message.reply("❌ Invalid token format!")

        msg = await message.reply_text("⏳ Creating your clone bot...")

        try:
            # Start new clone bot client
            clone_bot = Client(
                f"clone_{message.from_user.id}_{bot_token[:8]}",
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
            logger.error(f"Clone creation error: {e}")
            await msg.edit_text(
                f"⚠️ <b>Error:</b>\n\n<code>{e}</code>\n\n"
                "Contact support for help."
            )

    except Exception as e:
        logger.error(f"Clone process error: {e}")
        await message.reply(f"❌ Error: {str(e)}")

# Manage clones (Admin only)
@Client.on_callback_query(filters.regex("^manage_clones$"))
async def manage_clones_callback(client, query: CallbackQuery):
    if query.from_user.id not in ADMINS:
        return await query.answer("Admin only!", show_alert=True)

    clones = await clone_db.get_all_clones()
    if not clones:
        return await query.answer("No clones created yet!", show_alert=True)

    buttons = []
    for clone in clones[:10]:  # Show first 10 only
        buttons.append([
            InlineKeyboardButton(
                f"🤖 {clone['name']} (@{clone['username']})",
                callback_data=f"view_clone_{clone['bot_id']}"
            )
        ])

    buttons.append([InlineKeyboardButton('🔙 Back', callback_data='start')])

    await query.message.edit_text(
        f"<b>📊 Total Clones: {len(clones)}</b>\n\nSelect a clone to view details:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# Delete clone by token
@Client.on_message(filters.command("deleteclone") & filters.private)
async def delete_clone_command(client, message):
    if not CLONE_MODE:
        return await message.reply("Clone feature is disabled!")

    try:
        token_msg = await client.ask(
            message.chat.id,
            "Send the bot token to delete:",
            timeout=300
        )

        bot_token = re.findall(r'\d+:[0-9A-Za-z_-]{35}', token_msg.text)
        if not bot_token:
            return await message.reply("❌ Invalid token!")

        clone = await clone_db.get_clone_by_token(bot_token[0])
        if not clone:
            return await message.reply("❌ Clone not found!")

        await clone_db.delete_clone(bot_token[0])
        await message.reply("✅ Clone deleted successfully!")

    except Exception as e:
        logger.error(f"Delete clone error: {e}")
        await message.reply(f"❌ Error: {str(e)}")

# Restart all clones
async def restart_bots():
    """Restart all clone bots from database"""
    clones = await clone_db.get_all_clones()

    for clone in clones:
        try:
            client = Client(
                f"clone_{clone['bot_id']}",
                API_ID,
                API_HASH,
                bot_token=clone['token'],
                plugins={"root": "clone_plugins"}
            )
            await client.start()
            print(f"✅ Restarted: @{clone['username']}")
        except Exception as e:
            print(f"❌ Failed to restart clone @{clone.get('username')} - {e}")
