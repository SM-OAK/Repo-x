# plugins/power.py - Created by Gemini
# This is your new, dedicated admin control panel.

import config
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# Helper function to build the dynamic settings panel
async def build_settings_panel():
    """Creates the settings menu with the current status of each toggle."""
    buttons = []
    
    # Toggle for Link Generation Mode
    links_status = "🟢 ON" if config.LINK_GENERATION_MODE else "🔴 OFF"
    buttons.append(
        [InlineKeyboardButton(f"Main Bot Link Sharing: {links_status}", callback_data="toggle_links")]
    )
    
    # Toggle for Public Mode
    public_status = "🌍 Public" if config.PUBLIC_FILE_STORE else "🔒 Private"
    buttons.append(
        [InlineKeyboardButton(f"Bot Public Mode: {public_status}", callback_data="toggle_public")]
    )
    
    # Back button to return to the main start menu
    buttons.append([InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="start")])
    return InlineKeyboardMarkup(buttons)


# This handler opens the Admin Panel
@Client.on_message(filters.command("settings") & filters.user(config.ADMINS))
async def settings_command(client, message):
    await message.reply_text(
        "**⚙️ Admin Power Panel**\n\nHere you can manage your bot's live settings.",
        reply_markup=await build_settings_panel()
    )


# This handler manages all button clicks within the Admin Panel
@Client.on_callback_query(filters.regex(r"^(toggle_|admin_panel)") & filters.user(config.ADMINS))
async def power_panel_callbacks(client, query: CallbackQuery):
    data = query.data

    if data == "admin_panel":
        await query.answer()
        await query.message.edit_text(
            "**⚙️ Admin Power Panel**\n\nHere you can manage your bot's live settings.",
            reply_markup=await build_settings_panel()
        )
    
    elif data == "toggle_links":
        config.LINK_GENERATION_MODE = not config.LINK_GENERATION_MODE
        await query.answer(f"Link Sharing is now {'ENABLED' if config.LINK_GENERATION_MODE else 'DISABLED'}")
        await query.message.edit_reply_markup(await build_settings_panel())

    elif data == "toggle_public":
        config.PUBLIC_FILE_STORE = not config.PUBLIC_FILE_STORE
        await query.answer(f"Bot Mode is now {'PUBLIC' if config.PUBLIC_FILE_STORE else 'PRIVATE'}")
        await query.message.edit_reply_markup(await build_settings_panel())
