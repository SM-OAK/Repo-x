import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import CLONE_MODE, API_ID, API_HASH, ADMINS
from database.clone_db import clone_db
from Script import script
import logging

logger = logging.getLogger(__name__)

# Clone callback handler - Shows user's clones
@Client.on_callback_query(filters.regex("^clone$"))
async def clone_callback(client, query: CallbackQuery):
    if not CLONE_MODE:
        return await query.answer("Clone feature is disabled!", show_alert=True)

    user_clones = await clone_db.get_user_clones(query.from_user.id)

    buttons = []
    if user_clones:
        for clone in user_clones:
            buttons.append([
                InlineKeyboardButton(
                    f"🤖 {clone['name']} (@{clone['username']})",
                    callback_data=f"customize_{clone['bot_id']}"
                )
            ])

    buttons.append([InlineKeyboardButton('➕ ᴀᴅᴅ ɴᴇᴡ ᴄʟᴏɴᴇ', callback_data='add_clone')])
    buttons.append([InlineKeyboardButton('🔙 ʙᴀᴄᴋ', callback_data='start')])

    if user_clones:
        reply_text = "✨ **Mᴀɴᴀɢᴇ Yᴏᴜʀ Cʟᴏɴᴇs**\n\nSelect a bot from the list below to customize its settings, or add a new one."
    else:
        reply_text = "✨ **Nᴏ Cʟᴏɴᴇs Fᴏᴜɴᴅ**\n\nYou have not created any clone bots yet. Use the button below to get started."

    await query.message.edit_text(
        reply_text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# Add clone handler - FIXED
@Client.on_callback_query(filters.regex("^add_clone$"))
async def add_clone_callback(client, query: CallbackQuery):
    try:
        # Ask for bot token
        await query.message.edit_text(
            "<b>1) Sᴇɴᴅ <code>/newbot</code> ᴛᴏ @BotFather\n"
            "2) Gɪᴠᴇ ᴀ ɴᴀᴍᴇ ғᴏʀ ʏᴏᴜʀ ʙᴏᴛ\n"
            "3) Gɪᴠᴇ ᴀ ᴜɴɪǫᴜᴇ ᴜsᴇʀɴᴀᴍᴇ\n"
            "4) Fᴏʀᴡᴀʀᴅ ᴛʜᴇ ᴛᴏᴋᴇɴ ᴍᴇssᴀɢᴇ ᴛᴏ ᴍᴇ\n\n"
            "/cancel - Cᴀɴᴄᴇʟ ᴛʜɪs ᴘʀᴏᴄᴇss</b>"
        )
        
        token_msg = await client.ask(
            chat_id=query.from_user.id,
            text="Please forward the message from BotFather now...",
            timeout=300
        )

        if token_msg.text and token_msg.text == '/cancel':
            return await query.message.edit_text('Cᴀɴᴄᴇʟᴇᴅ! 🚫', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data='clone')]]))

        # Validate token
        if not (token_msg.forward_from and token_msg.forward_from.id == 93372553):
            return await query.message.edit_text('Nᴏᴛ ғᴏʀᴡᴀʀᴅᴇᴅ ғʀᴏᴍ @BotFather! 😑', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data='clone')]]))

        try:
            bot_token = re.findall(r"\b(\d+:[A-Za-z0-9_-]+)\b", token_msg.text)[0]
        except:
            return await query.message.edit_text('Iɴᴠᴀʟɪᴅ ᴛᴏᴋᴇɴ ғᴏʀᴍᴀᴛ! 😕', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data='clone')]]))

        # Create clone
        msg = await query.message.edit_text("⏳ Cʀᴇᴀᴛɪɴɢ ʏᴏᴜʀ ᴄʟᴏɴᴇ ʙᴏᴛ...")

        try:
            clone_bot = Client(
                f"clone_{query.from_user.id}_{bot_token[:8]}",
                API_ID,
                API_HASH,
                bot_token=bot_token,
                plugins={"root": "clone_plugins"}
            )

            await clone_bot.start()
            bot_info = await clone_bot.get_me()

            await clone_db.add_clone(
                bot_id=bot_info.id, user_id=query.from_user.id, bot_token=bot_token,
                username=bot_info.username, name=bot_info.first_name
            )

            buttons = [
                [InlineKeyboardButton('📝 Cᴜsᴛᴏᴍɪᴢᴇ Cʟᴏɴᴇ', callback_data=f'customize_{bot_info.id}')],
                [InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data='clone')]
            ]

            await msg.edit_text(
                f"<b>✅ Sᴜᴄᴄᴇssғᴜʟʟʏ ᴄʟᴏɴᴇᴅ!\n\n🤖 Bᴏᴛ: @{bot_info.username}</b>",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        except Exception as e:
            logger.error(f"Clone creation error: {e}")
            await msg.edit_text(f"⚠️ <b>Eʀʀᴏʀ:</b>\n\n<code>{e}</code>")

    except Exception as e:
        logger.error(f"Clone process error: {e}")

# (This command is now redundant but kept to preserve structure)
@Client.on_message(filters.command("clone") & filters.private)
async def clone_command(client, message):
    await message.reply(
        "Please use the buttons to create a clone.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('🤖 ᴄʀᴇᴀᴛᴇ ʏᴏᴜʀ ᴏᴡɴ ᴄʟᴏɴᴇ ʙᴏᴛ', callback_data='clone')
        ]])
    )

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
            "Sᴇɴᴅ ᴛʜᴇ ʙᴏᴛ ᴛᴏᴋᴇɴ ᴛᴏ ᴅᴇʟᴇᴛᴇ:",
            timeout=300
        )

        bot_token = re.findall(r'\d[0-9]{8,10}:[0-9A-Za-z_-]{35}', token_msg.text)
        if not bot_token:
            return await message.reply("Iɴᴠᴀʟɪᴅ ᴛᴏᴋᴇɴ!")

        clone = await clone_db.get_clone_by_token(bot_token[0])
        if not clone:
            return await message.reply("Cʟᴏɴᴇ ɴᴏᴛ ғᴏᴜɴᴅ!")

        await clone_db.delete_clone(bot_token[0])
        await message.reply("✅ Cʟᴏɴᴇ ᴅᴇʟᴇᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!")

    except Exception as e:
        logger.error(f"Delete clone error: {e}")
        await message.reply(f"Eʀʀᴏʀ: {str(e)}")
