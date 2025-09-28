# In plugins/commands.py, replace the existing start function with this one.
from pyrogram import Client, filters, enums

@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        if LOG_CHANNEL:
            await client.send_message(LOG_CHANNEL, script.LOG_TEXT.format(message.from_user.id, message.from_user.mention))

    # --- FULLY IMPLEMENTED DEEP LINK & FILE ACCESS LOGIC ---
    if len(message.command) > 1:
        # 1. Handle Force Sub
        if not await handle_force_sub(client, message):
            return  # Stop if the user hasn't joined the channel

        # 2. Handle File Access
        data = message.command[1]
        try:
            # Decode the file ID from the deep link
            try:
                if data.startswith("file_"):
                    decode_file_id = data[5:]
                else:
                    decoded_data = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("ascii")
                    _, decode_file_id = decoded_data.split("_", 1)
            except Exception as decode_error:
                logger.error(f"Deep link decode error: {decode_error}")
                return await message.reply("❌ **Invalid Link**\n\nThis link may be broken or expired. Please request a new one.")

            # Get the file message from the log channel and send it
            try:
                msg = await client.get_messages(LOG_CHANNEL, int(decode_file_id))
                if msg.media:
                    media = getattr(msg, msg.media.value)
                    title = formate_file_name(getattr(media, "file_name", "File"))
                    size = get_size(media.file_size)
                    f_caption = f"<code>{title}</code>"
                    
                    # Add stream/download buttons if enabled
                    reply_markup = None
                    if STREAM_MODE and (msg.video or msg.document):
                        stream_url = f"{URL}watch/{str(msg.id)}/{quote_plus(get_name(msg))}?hash={get_hash(msg)}"
                        download_url = f"{URL}{str(msg.id)}/{quote_plus(get_name(msg))}?hash={get_hash(msg)}"
                        button = [[
                            InlineKeyboardButton("• ᴅᴏᴡɴʟᴏᴀᴅ •", url=download_url),
                            InlineKeyboardButton('• ᴡᴀᴛᴄʜ •', url=stream_url)
                        ]]
                        reply_markup = InlineKeyboardMarkup(button)
                        
                    del_msg = await msg.copy(chat_id=message.from_user.id, caption=f_caption, reply_markup=reply_markup)
                else:
                    del_msg = await msg.copy(chat_id=message.from_user.id)
                
                # Handle auto-delete if enabled
                if AUTO_DELETE_MODE:
                    k = await client.send_message(chat_id=message.from_user.id, text=f"**❗️IMPORTANT❗️**\n\nThis file will be deleted in **{AUTO_DELETE} minutes** due to copyright.\nPlease forward it to your saved messages to keep it.")
                    await asyncio.sleep(AUTO_DELETE_TIME)
                    await del_msg.delete()
                    await k.edit_text("Your file has been deleted successfully!")
                return
                
            except Exception as msg_error:
                logger.error(f"File retrieval error: {msg_error}")
                await message.reply_text("❌ **File Not Found**\n\nThe file may have been deleted from the server.")
                return
                
        except Exception as general_error:
            logger.error(f"General error in file access: {general_error}")
            await message.reply_text("An error occurred while trying to access the file.")
        return

    # --- START COMMAND FOR REGULAR & ADMIN USERS (NO DEEP LINK) ---
    if message.from_user.id in ADMINS:
        await message.reply_photo(
            photo=random.choice(PICS),
            caption="✨ **Admin Panel**\n\nWelcome, Owner! You can configure your bot's settings using the buttons below.",
            reply_markup=await build_admin_panel()
        )
        return

    # Corrected button layout for regular users
    buttons = [
        [
            InlineKeyboardButton('💁‍♀️ ʜᴇʟᴘ', callback_data='help'),
            InlineKeyboardButton('😊 ᴀʙᴏᴜᴛ', callback_data='about')
        ],
        [InlineKeyboardButton('🤖 ᴄʀᴇᴀᴛᴇ ʏᴏᴜʀ ᴏᴡɴ ᴄʟᴏɴᴇ ʙᴏᴛ', callback_data='clone')],
        [InlineKeyboardButton('📢 ᴜᴘᴅᴀᴛᴇ ᴄʜᴀɴɴᴇʟ', url=f"https://t.me/{(await client.get_chat(FORCE_SUB_CHANNEL)).username}")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    
    await message.reply_photo(
        photo=random.choice(PICS),
        caption=script.START_TXT.format(message.from_user.mention, client.me.mention),
        reply_markup=reply_markup
    )
