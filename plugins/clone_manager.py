import re
import os
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import CLONE_MODE, API_ID, API_HASH, ADMINS
from database.clone_db import clone_db
from Script import script

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Active clone clients {bot_id: Client}
active_clones = {}

# -----------------------------
# Main Clone Menu (callback: "clone")
# -----------------------------
@Client.on_callback_query(filters.regex("^clone$"))
async def clone_management_menu(client, query: CallbackQuery):
    if not CLONE_MODE:
        return await query.answer("Clone feature is disabled!", show_alert=True)

    user_id = query.from_user.id
    buttons = []
    
    try:
        # Get clones from DB (Admins see all, users see their own)
        if user_id in ADMINS:
            clones = await clone_db.get_all_clones()
        else:
            clones = await clone_db.get_user_clones(user_id)

        if not clones or len(clones) == 0:
            reply_text = "✨ **No Clones Found**\n\nYou haven't created any clone bots yet. Use the button below to get started."
        else:
            reply_text = "✨ **Manage Clone's**\n\nYou can now manage and create your very own identical clone bot, mirroring all my awesome features, using the given buttons."
            # Create a button for each clone
            for clone in clones:
                status = "🟢" if clone.get('is_active', True) else "🔴"
                buttons.append(
                    [InlineKeyboardButton(
                        f"{status} {clone['name']}", 
                        callback_data=f"customize_{clone['bot_id']}"
                    )]
                )

        # Add 'Add Clone' and 'Back' buttons
        buttons.append([InlineKeyboardButton('➕ Add Clone', callback_data='add_clone')])
        buttons.append([InlineKeyboardButton('🔙 Back', callback_data='start')])

        await query.message.edit_text(
            reply_text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        logger.error(f"Error in clone menu: {e}")
        await query.answer("Error loading clones!", show_alert=True)

# -----------------------------
# Add Clone Instructions
# -----------------------------
@Client.on_callback_query(filters.regex("^add_clone$"))
async def add_clone_callback(client, query: CallbackQuery):
    await query.message.edit_text(
        "<b>📝 To create a new clone, please use the /clone command.</b>\n\n"
        "After typing the command, forward the message you receive from @BotFather.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Back", callback_data="clone")]]
        )
    )

# -----------------------------
# Clone Creation Command
# -----------------------------
@Client.on_message(filters.command("clone") & filters.private)
async def clone_command(client, message):
    if not CLONE_MODE:
        return await message.reply("Clone feature is disabled!")

    try:
        os.makedirs("clone_sessions", exist_ok=True)

        token_msg = await client.ask(
            message.chat.id,
            "<b>Please forward the message from @BotFather that contains your bot token.</b>\n\nUse /cancel to stop this process.",
            timeout=300
        )

        if token_msg.text and token_msg.text == '/cancel':
            return await message.reply("Process canceled!")

        if not (token_msg.forward_from and token_msg.forward_from.id == 93372553):
            return await message.reply("❌ **Error:** This message was not forwarded from @BotFather. Please try again.")

        try:
            bot_token = re.findall(r'\d[0-9]{8,10}:[0-9A-Za-z_-]{35}', token_msg.text)[0]
        except:
            return await message.reply("❌ **Invalid Token:** The token format is incorrect.")

        # Check if clone already exists
        try:
            existing_clone = await clone_db.get_clone_by_token(bot_token)
            if existing_clone:
                return await message.reply("⚠️ **Already Cloned:** This bot has already been cloned.")
        except Exception as e:
            logger.error(f"Error checking existing clone: {e}")

        msg = await message.reply_text("⏳ Please wait, creating your clone bot...")

        try:
            session_name = f"clone_sessions/clone_{message.from_user.id}_{bot_token[:8]}"
            clone_bot = Client(
                session_name, 
                API_ID, 
                API_HASH, 
                bot_token=bot_token, 
                plugins={"root": "clone_plugins"}
            )
            await clone_bot.start()
            bot_info = await clone_bot.get_me()

            # Add to database
            await clone_db.add_clone(
                user_id=message.from_user.id,
                bot_id=bot_info.id,
                bot_token=bot_token,
                name=bot_info.first_name,
                username=bot_info.username or "unknown"
            )

            active_clones[bot_info.id] = clone_bot

            buttons = [
                [InlineKeyboardButton('🛠️ Customize Your Clone', callback_data=f'customize_{bot_info.id}')],
                [InlineKeyboardButton('🔙 Back to Clones', callback_data='clone')]
            ]
            await msg.edit_text(
                f"<b>✅ Clone Created Successfully!</b>\n\n"
                f"<b>🤖 Bot:</b> @{bot_info.username}\n"
                f"<b>📝 Name:</b> {bot_info.first_name}\n"
                f"<b>🆔 Bot ID:</b> <code>{bot_info.id}</code>",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        except Exception as e:
            logger.error(f"Clone creation error: {e}", exc_info=True)
            await msg.edit_text(f"⚠️ **An error occurred:**\n\n<code>{str(e)}</code>")

    except Exception as e:
        logger.error(f"Clone process error: {e}", exc_info=True)
        await message.reply(f"❌ Error: {str(e)}")

# -----------------------------
# Restart all clones on startup
# -----------------------------
async def restart_bots():
    if not CLONE_MODE:
        logger.info("Clone mode disabled")
        return

    os.makedirs("clone_sessions", exist_ok=True)
    
    try:
        clones = await clone_db.get_all_clones()
        logger.info(f"🔄 Found {len(clones)} clones in DB")

        for clone in clones:
            if not clone.get('is_active', True):
                logger.info(f"⏭️ Skipping inactive clone: @{clone.get('username', 'unknown')}")
                continue
                
            bot_id = clone['bot_id']
            bot_token = clone['bot_token']
            
            try:
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
                logger.info(f"✅ Restarted: @{clone.get('username', 'unknown')}")
            except Exception as e:
                logger.error(f"Failed to restart @{clone.get('username', 'unknown')}: {e}")

        logger.info(f"✅ Successfully restarted {len(active_clones)} clones")
    except Exception as e:
        logger.error(f"Error in restart_bots: {e}")

logger.info("✅ Clone manager module loaded")
