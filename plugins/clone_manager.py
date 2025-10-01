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
# This now shows the "Manage Clone's" screen directly, as per your screenshot.
# -----------------------------
@Client.on_callback_query(filters.regex("^clone$"))
async def clone_management_menu(client, query: CallbackQuery):
    if not CLONE_MODE:
        return await query.answer("Clone feature is disabled!", show_alert=True)

    user_id = query.from_user.id
    buttons = []
    
    # Get clones from DB (Admins see all, users see their own)
    clones = await clone_db.get_clones_by_user(user_id)
    if user_id in ADMINS:
        clones = await clone_db.get_all_clones()

    if not clones:
        reply_text = "✨ **No Clones Found**\n\nYou haven't created any clone bots yet. Use the button below to get started."
    else:
        reply_text = "✨ **Manage Clone's**\n\nYou can now manage and create your very own identical clone bot, mirroring all my awesome features, using the given buttons."
        # Create a single button for each clone that links to the customize menu
        for clone in clones:
            buttons.append(
                [InlineKeyboardButton(f"🤖 {clone['name']}", callback_data=f"customize_{clone['bot_id']}")]
            )

    # Add 'Add Clone' and 'Back' buttons at the bottom
    buttons.append([InlineKeyboardButton('➕ Add Clone', callback_data='add_clone')])
    buttons.append([InlineKeyboardButton('🔙 Back', callback_data='start')])

    await query.message.edit_text(
        reply_text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# -----------------------------
# NEW! Customize Clone Menu
# This function is called when a user clicks on their clone's name.
# -----------------------------
@Client.on_callback_query(filters.regex("^customize_"))
async def customize_clone(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[1])
    clone = await clone_db.get_clone(bot_id)

    if not clone:
        return await query.answer("Clone not found!", show_alert=True)
        
    if clone['user_id'] != query.from_user.id and query.from_user.id not in ADMINS:
        return await query.answer("This is not your bot!", show_alert=True)

    # You can add all your customization buttons here
    buttons = [
        [
            InlineKeyboardButton('📝 START MSG', callback_data=f'set_start_{bot_id}'),
            InlineKeyboardButton('🔒 FORCE SUB', callback_data=f'set_fsub_{bot_id}')
        ],
        [
            InlineKeyboardButton('🗑️ DELETE CLONE', callback_data=f'delete_clone_{bot_id}')
        ],
        [
            InlineKeyboardButton('🔙 Back to Clones', callback_data='clone')
        ]
    ]

    await query.message.edit_text(
        f"🛠️ **Customize Clone: {clone['name']}**\n\n"
        f"Configure your bot's settings using the buttons below.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# -----------------------------
# Add Clone Instructions (callback: "add_clone")
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
# Clone Creation Command (/clone)
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

        if await clone_db.get_clone_by_token(bot_token):
            return await message.reply("⚠️ **Already Cloned:** This bot has already been cloned.")

        msg = await message.reply_text("⏳ Please wait, creating your clone bot...")

        try:
            session_name = f"clone_sessions/clone_{message.from_user.id}_{bot_token[:8]}"
            clone_bot = Client(session_name, API_ID, API_HASH, bot_token=bot_token, plugins={"root": "clone_plugins"})
            await clone_bot.start()
            bot_info = await clone_bot.get_me()

            await clone_db.add_clone(
                bot_id=bot_info.id,
                user_id=message.from_user.id,
                bot_token=bot_token,
                username=bot_info.username,
                name=bot_info.first_name
            )

            active_clones[bot_info.id] = clone_bot

            buttons = [
                [InlineKeyboardButton('🛠️ Customize Your Clone', callback_data=f'customize_{bot_info.id}')],
                [InlineKeyboardButton('🔙 Back to Clones', callback_data='clone')]
            ]
            await msg.edit_text(
                f"<b>✅ Clone Created Successfully!</b>\n\n"
                f"<b>🤖 Bot:</b> @{bot_info.username}\n",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        except Exception as e:
            logger.error(f"Clone creation error: {e}", exc_info=True)
            await msg.edit_text(f"⚠️ **An error occurred:**\n\n<code>{e}</code>")

    except Exception as e:
        logger.error(f"Clone process error: {e}", exc_info=True)


# -----------------------------
# Delete Clone
# -----------------------------
@Client.on_callback_query(filters.regex("^delete_clone_"))
async def delete_clone_button_callback(client, query: CallbackQuery):
    bot_id = int(query.data.split("_")[2])
    clone = await clone_db.get_clone(bot_id)
    if not clone:
        return await query.answer("Clone not found!", show_alert=True)

    user_id = query.from_user.id
    if clone['user_id'] != user_id and user_id not in ADMINS:
        return await query.answer("❌ This is not your clone!", show_alert=True)

    # Stop bot if running
    if bot_id in active_clones:
        try:
            await active_clones[bot_id].stop()
            del active_clones[bot_id]
        except:
            pass

    # Delete from DB
    await clone_db.delete_clone_by_id(bot_id)
    await query.answer("✅ Clone deleted successfully!", show_alert=True)
    # Go back to the main clone menu
    await clone_management_menu(client, query)


# -----------------------------
# Restart all clones (on bot startup)
# -----------------------------
async def restart_bots():
    if not CLONE_MODE:
        logger.info("Clone mode disabled")
        return

    os.makedirs("clone_sessions", exist_ok=True)
    clones = await clone_db.get_all_clones()
    logger.info(f"🔄 Found {len(clones)} clones in DB")

    for clone in clones:
        bot_id = clone['bot_id']
        bot_token = clone['bot_token']
        try:
            session_name = f"clone_sessions/clone_{bot_id}"
            client = Client(session_name, API_ID, API_HASH, bot_token=bot_token, plugins={"root": "clone_plugins"})
            await client.start()
            active_clones[bot_id] = client
            logger.info(f"✅ Restarted: @{clone['username']}")
        except Exception as e:
            logger.error(f"Failed to restart @{clone['username']}: {e}")

    logger.info(f"✅ Successfully restarted {len(active_clones)} clones")
