import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from config import CLONE_MODE, API_ID, API_HASH, ADMINS
from database.clone_db import clone_db
from Script import script
import logging

logger = logging.getLogger(__name__)

# Dictionary to store user's current conversation step
user_steps = {}

# Main clone menu
@Client.on_callback_query(filters.regex("^clone$"))
async def clone_callback(client, query: CallbackQuery):
    if not CLONE_MODE:
        return await query.answer("Clone feature is disabled!", show_alert=True)
    
    # Clear any previous steps
    if query.from_user.id in user_steps:
        del user_steps[query.from_user.id]
        
    buttons = [
        [InlineKeyboardButton('➕ ᴀᴅᴅ ᴄʟᴏɴᴇ', callback_data='add_clone')],
        [InlineKeyboardButton('❌ ᴅᴇʟᴇᴛᴇ ᴄʟᴏɴᴇ', callback_data='delete_clone')],
        [InlineKeyboardButton('🔙 ʙᴀᴄᴋ', callback_data='start')]
    ]
    
    await query.message.edit_text(
        script.CLONE_TEXT,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# --- Conversation Handlers ---

@Client.on_callback_query(filters.regex("^(add|delete)_clone$"))
async def start_conversation_callback(client, query: CallbackQuery):
    action = query.data.split("_")[0] # 'add' or 'delete'
    user_id = query.from_user.id

    if action == 'add':
        await query.message.edit_text(
            "<b>Fᴏʀᴡᴀʀᴅ Tʜᴇ Mᴇssᴀɢᴇ Fʀᴏᴍ @BotFather\n\n"
            "Tʜɪs ᴍᴇssᴀGᴇ ᴍᴜsᴛ ᴄᴏɴᴛᴀɪɴ ʏᴏᴜʀ ʙᴏᴛ ᴛᴏᴋᴇɴ.\n\n"
            "Usᴇ /cancel ᴛᴏ sᴛᴏᴘ ᴛʜɪs ᴘʀᴏᴄᴇss.</b>"
        )
        user_steps[user_id] = "awaiting_add_token"
    elif action == 'delete':
        await query.message.edit_text(
            "<b>Sᴇɴᴅ ᴛʜᴇ Bᴏᴛ Tᴏᴋᴇɴ ᴏғ ᴛʜᴇ ᴄʟᴏɴᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴇʟᴇᴛᴇ.\n\n"
            "Usᴇ /cancel ᴛᴏ sᴛᴏᴘ ᴛʜɪs ᴘʀᴏᴄᴇss.</b>"
        )
        user_steps[user_id] = "awaiting_delete_token"

# Cancel command to exit conversation
@Client.on_message(filters.command("cancel") & filters.private)
async def cancel_conversation(client, message: Message):
    user_id = message.from_user.id
    if user_id in user_steps:
        del user_steps[user_id]
        await message.reply_text("Cᴀɴᴄᴇʟᴇᴅ! 🚫", reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('🔙 Bᴀᴄᴋ ᴛᴏ Cʟᴏɴᴇ Mᴇɴᴜ', callback_data='clone')
        ]]))

# Handler for receiving the token message
@Client.on_message(filters.private & ~filters.command("cancel"))
async def conversation_handler(client, message: Message):
    user_id = message.from_user.id
    step = user_steps.get(user_id)

    if not step:
        return # Not in a conversation

    # --- ADD CLONE LOGIC ---
    if step == "awaiting_add_token":
        # Clear step immediately
        del user_steps[user_id]

        if not (message.forward_from and message.forward_from.id == 93372553):
            return await message.reply('Nᴏᴛ ғᴏʀᴡᴀʀᴅᴇᴅ ғʀᴏᴍ @BotFather! 😑', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data='clone')]]))

        try:
            bot_token = re.findall(r"\b(\d+:[A-Za-z0-9_-]+)\b", message.text)[0]
        except IndexError:
            return await message.reply('Iɴᴠᴀʟɪᴅ ᴛᴏᴋᴇɴ ғᴏʀᴍᴀᴛ! 😕', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data='clone')]]))

        msg = await message.reply_text("⏳ Cʀᴇᴀᴛɪɴɢ ʏᴏᴜʀ ᴄʟᴏɴᴇ ʙᴏᴛ...")
        try:
            clone_bot = Client(
                f"clone_{user_id}_{bot_token[:8]}", API_ID, API_HASH,
                bot_token=bot_token, plugins={"root": "clone_plugins"}
            )
            await clone_bot.start()
            bot_info = await clone_bot.get_me()
            await clone_db.add_clone(bot_info.id, user_id, bot_token, bot_info.username, bot_info.first_name)
            await msg.edit_text(f"<b>✅ Sᴜᴄᴄᴇssғᴜʟʟʏ ᴄʟᴏɴᴇᴅ!\n\n🤖 Bᴏᴛ: @{bot_info.username}</b>",
                                reply_markup=InlineKeyboardMarkup([
                                    [InlineKeyboardButton('🔙 Bᴀᴄᴋ ᴛᴏ Cʟᴏɴᴇ Mᴇɴᴜ', callback_data='clone')]
                                ]))
        except Exception as e:
            logger.error(f"Clone creation error: {e}")
            await msg.edit_text(f"⚠️ <b>Eʀʀᴏʀ:</b>\n\n<code>{e}</code>")

    # --- DELETE CLONE LOGIC ---
    elif step == "awaiting_delete_token":
        # Clear step immediately
        del user_steps[user_id]

        bot_token_match = re.search(r'(\d+:[A-Za-z0-9_-]+)', message.text)
        if not bot_token_match:
            return await message.reply("Iɴᴠᴀʟɪᴅ ᴛᴏᴋᴇɴ ғᴏʀᴍᴀᴛ!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data='clone')]]))

        bot_token = bot_token_match.group(1)
        clone = await clone_db.get_clone_by_token(bot_token)
        
        if not clone or clone['user_id'] != user_id:
            return await message.reply("Cʟᴏɴᴇ ɴᴏᴛ ғᴏᴜɴᴅ ɪɴ ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data='clone')]]))
        
        await clone_db.delete_clone(bot_token)
        await message.reply("✅ Cʟᴏɴᴇ ᴅᴇʟᴇᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data='clone')]]))

# --- Admin Handlers (Unchanged) ---
@Client.on_callback_query(filters.regex("^manage_clones$"))
async def manage_clones_callback(client, query: CallbackQuery):
    # This function remains the same
    if query.from_user.id not in ADMINS:
        return await query.answer("Admin only!", show_alert=True)
    clones = await clone_db.get_all_clones()
    if not clones:
        return await query.answer("No clones created yet!", show_alert=True)
    buttons = [[InlineKeyboardButton(f"🤖 {clone['name']} (@{clone['username']})", callback_data=f"view_clone_{clone['bot_id']}")] for clone in clones[:10]]
    buttons.append([InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data='start')])
    await query.message.edit_text(
        f"<b>📊 Tᴏᴛᴀʟ Cʟᴏɴᴇs: {len(clones)}</b>\n\nSᴇʟᴇᴄᴛ ᴀ ᴄʟᴏɴᴇ ᴛᴏ ᴠɪᴇᴡ ᴅᴇᴛᴀɪʟs:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
