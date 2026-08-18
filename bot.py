# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

import asyncio
import logging
import threading
import time
import io
import requests

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

from flask import Flask

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
)
# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

from telegram.constants import ParseMode

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

from config import (
    BOT_TOKEN,
    BOT_NAME,
    PORT,
    OWNER_ID,
    UPDATES_URL,
)

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

from database import (
    init_database,
    save_user,
    save_chat,
    get_user_count,
    get_chat_count,
    authorize_user,
    unauthorize_user,
    is_authorized_user,
    authorize_chat,
    unauthorize_chat,
    is_authorized_chat,
    ban_user,
    unban_user,
    is_banned,
    get_all_user_ids,
)

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

from platforms import (
    detect_platform,
    get_platforms_text,
)

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

from poster import (
    search_media,
    extract_title_from_url,
    build_navigation_items,
    build_caption,
    create_thumbnail,
)

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

from mohammed.forcesub import (
    force_sub,
    force_sub_callback,
    get_pending_request,
)
# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

logging.basicConfig(
    format=(
        "%(asctime)s - "
        "%(name)s - "
        "%(levelname)s - "
        "%(message)s"
    ),
    level=logging.INFO,
)

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

logger = logging.getLogger(
    "mohammed-poster-zone"
)

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

app = Flask(__name__)

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

@app.route("/")
def home():
    return {
        "status": "online",
        "bot": BOT_NAME,
        "service": "Mohammed Poster Zone",
    }

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

@app.route("/health")
def health():
    return {
        "status": "healthy",
        "service": "Mohammed Poster Zone",
    }

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

def run_web_server():
    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False,
        use_reloader=False,
    )
  
# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

def is_group(update: Update):
    if not update.effective_chat:
        return False

    return update.effective_chat.type in (
        "group",
        "supergroup",
    )

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

def is_owner(
    update: Update,
):

    user = update.effective_user

    if not user:
        return False

    return user.id == OWNER_ID
    
# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

# --------------------------------------------------
# Force Subscribe Callback Wrapper
# --------------------------------------------------

async def handle_force_sub_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    pending = await force_sub_callback(
        update,
        context,
    )

    # User has not joined yet
    if not pending:
        return

    user = update.effective_user

    if not user:
        return

    command = pending.get(
        "command",
        "",
    ).lower()

    args = pending.get(
        "args",
        [],
    )

    logger.info(
        "Executing pending command after "
        "force-sub verification | "
        "user=%s | command=%s | args=%s",
        user.id,
        command,
        args,
    )

    # --------------------------------------------------
    # POSTER
    # --------------------------------------------------

    if command == "poster":

        # Re-create the original command
        update.message = update.message

        # We cannot directly modify
        # Telegram's original message.
        #
        # Instead, search the saved title
        # and send the result directly.

        if not args:

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=(
                    "❌ Nᴏ ᴘᴏsᴛᴇʀ ᴛɪᴛʟᴇ ᴡᴀs sᴀᴠᴇᴅ."
                ),
            )

            return

        title = " ".join(args).strip()

        processing = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🔎 Sᴇᴀʀᴄʜɪɴɢ ғᴏʀ ᴀʀᴛᴡᴏʀᴋ...",
        )

        try:

            media = await asyncio.to_thread(
                search_media,
                title,
            )

            if not media:

                await processing.edit_text(
                    "Nᴏ Mᴀᴛᴄʜɪɴɢ 𝗠𝗼𝘃𝗶𝗲𝘀 ᴏʀ 𝗦𝗲𝗿𝗶𝗲𝘀 ᴏʀ 𝗔𝗻𝗶𝗺𝗲 ᴏʀ 𝗦𝗲𝗿𝗶𝗮𝗹 ᴏʀ 𝗗𝗿𝗮𝗺𝗮 ᴡᴀs ғᴏᴜɴᴅ"
                )

                return

            await processing.delete()

            items = await asyncio.to_thread(
                build_navigation_items,
                media,
            )

            if not items:

                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=(
                        "‼️ Nᴏ Aʀᴛᴡᴏʀᴋ Wᴀs Fᴏᴜɴᴅ Fᴏʀ Tʜɪs Tɪᴛʟᴇ.. "
                    ),
                )

                return

            first = items[0]

            sent = await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=first["url"],
                caption=build_caption(
                    media,
                    "Unknown Platform",
                    first,
                ),
                parse_mode=ParseMode.HTML,
            )

            cleanup_navigation()

            key = (
                update.effective_chat.id,
                user.id,
                sent.message_id,
            )

            NAVIGATION[key] = {
                "items": items,
                "index": 0,
                "media": media,
                "platform": "Unknown Platform",
                "created_at": time.time(),
            }

            keyboard = make_navigation_buttons(
                key,
                0,
                len(items),
            )

            if keyboard:

                await sent.edit_reply_markup(
                    reply_markup=keyboard
                )

        except Exception:

            logger.exception(
                "Pending poster execution failed"
            )

            try:

                await processing.edit_text(
                    "⚠️ 𝗔𝗻 𝗲𝗿𝗿𝗼𝗿 𝗼𝗰𝗰𝘂𝗿𝗿𝗲𝗱 𝘄𝗵𝗶𝗹𝗲 𝘀𝗲𝗮𝗿𝗰𝗵𝗶𝗻𝗴. 𝗣𝗹𝗲𝗮𝘀𝗲 𝘁𝗿𝘆 𝗮𝗴𝗮𝗶𝗻"
                )

            except Exception:

                pass

        return

    # --------------------------------------------------
    # OTT
    # --------------------------------------------------

    if command == "ott":

        if not args:

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=(
                    "❌ Nᴏ 𝗢𝗧𝗧 URL Wᴀs Sᴀᴠᴇᴅ."
                ),
            )

            return

        url = args[0].strip()

        if not (
            url.startswith("http://")
            or url.startswith("https://")
        ):

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=(
                    "‼️ Iɴᴠᴀʟɪᴅ 𝗢𝗧𝗧 URL.."
                ),
            )

            return

        platform = detect_platform(
            url
        )

        processing = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🌐 Rᴇᴀᴅɪɴɢ Tʜᴇ 𝗢𝗧𝗧 Pᴀɢᴇ...",
        )

        try:

            title = await asyncio.to_thread(
                extract_title_from_url,
                url,
            )

            if not title:

                await processing.edit_text(
                    "❌ I ᴄᴏᴜʟᴅɴ'ᴛ ᴇxᴛʀᴀᴄᴛ ᴀ ᴛɪᴛʟᴇ ғʀᴏᴍ ᴛʜɪs ᴘᴀɢᴇ."
                )

                return

            media = await asyncio.to_thread(
                search_media,
                title,
            )

            if not media:

                await processing.edit_text(
                    "❌ I ᴄᴏᴜʟᴅɴ'ᴛ ғɪɴᴅ ᴍᴀᴛᴄʜɪɴɢ ᴀʀᴛᴡᴏʀᴋ ғᴏʀ ᴛʜɪs ᴛɪᴛʟᴇ.."
                )

                return

            await processing.delete()

            items = await asyncio.to_thread(
                build_navigation_items,
                media,
            )

            if not items:

                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=(
                        "🔎 ɴᴏ ᴀʀᴛᴡᴏʀᴋ ᴡᴀs ғᴏᴜɴᴅ"
                    ),
                )

                return

            first = items[0]

            sent = await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=first["url"],
                caption=build_caption(
                    media,
                    platform,
                    first,
                ),
                parse_mode=ParseMode.HTML,
            )

            cleanup_navigation()

            key = (
                update.effective_chat.id,
                user.id,
                sent.message_id,
            )

            NAVIGATION[key] = {
                "items": items,
                "index": 0,
                "media": media,
                "platform": platform,
                "created_at": time.time(),
            }

            keyboard = make_navigation_buttons(
                key,
                0,
                len(items),
            )

            if keyboard:

                await sent.edit_reply_markup(
                    reply_markup=keyboard
                )

        except Exception:

            logger.exception(
                "‼️ ᴘᴇɴᴅɪɴɢ 𝗢𝗧𝗧 ᴇxᴇᴄᴜᴛɪᴏɴ ғᴀɪʟᴇᴅ"
            )

            try:

                await processing.edit_text(
                    "⚠️ ᴛʜᴇ 𝗢𝗧𝗧 ᴘᴀɢᴇ ᴄᴏᴜʟᴅ ɴᴏᴛ ʙᴇ ᴘʀᴏᴄᴇssᴇᴅ.."
                )

            except Exception:

                pass

        return

# --------------------------------------------------
# Navigation storage
# --------------------------------------------------

NAVIGATION = {}

NAVIGATION_TTL = 60 * 60

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

def cleanup_navigation():
    now = time.time()

    expired = []

    for key, value in NAVIGATION.items():

        if (
            now - value["created_at"]
            > NAVIGATION_TTL
        ):
            expired.append(key)

    for key in expired:
        NAVIGATION.pop(
            key,
            None,
        )
      
# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

def make_navigation_buttons(
    key,
    index,
    total,
):
    row = []

    if index > 0:
        row.append(
            InlineKeyboardButton(
                "• ʙᴀᴄᴋ •",
                callback_data=(
                    f"poster_prev:"
                    f"{key[0]}:"
                    f"{key[1]}:"
                    f"{key[2]}"
                ),
            )
        )

    if index < total - 1:
        row.append(
            InlineKeyboardButton(
                "• ɴᴇxᴛ •",
                callback_data=(
                    f"poster_next:"
                    f"{key[0]}:"
                    f"{key[1]}:"
                    f"{key[2]}"
                ),
            )
        )

    if not row:
        return None

    return InlineKeyboardMarkup(
        [row]
    )

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user
    chat = update.effective_chat

    if not user or not chat:
        return

    # ------------------------- #
    # Save user
    # ------------------------- #

    try:
        await save_user(user)
        await save_chat(chat)
    except Exception:
        logger.exception(
            "‼️ 𝖥𝖺𝗂𝗅𝖾𝖽 𝗍𝗈 𝗌𝖺𝗏𝖾 𝗌𝗍𝖺𝗋𝗍 𝗎𝗌𝖾𝗋/𝖼𝗁𝖺𝗍"
        )

    # ------------------------- #
    # Private start
    # ------------------------- #

    if chat.type == "private":

        if await is_banned(user.id):

            await update.message.reply_text(
                "🚫 <b>Yᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ ғʀᴏᴍ ᴜsɪɴɢ ᴛʜɪs ʙᴏᴛ..contact @Mr_Mohammed_29</b>",
                parse_mode=ParseMode.HTML,
            )

            return

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "• ᴘᴏsᴛᴇʀ ɢʀᴏᴜᴘ •",
                        url="https://t.me/+hxfpcrzX0YFjNmRl",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "• ᴜᴘᴅᴀᴛᴇs •",
                        url=UPDATES_URL,
                    )
                ],
            ]
        )

        await update.message.reply_text(
            "🎬 <b>Mohammed Poster Zone</b>\n\n"
            "Welcome to Mohammed Poster bot! 👋\n\n"
            "Please Use This Bot In Our Poster Group.", 
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )

        return

    # ------------------------- #
    # Group start
    # ------------------------- #

    if chat.type in (
        "group",
        "supergroup",
    ):

        await update.message.reply_text(
            "🎬 <b>Mohammed Poster Zone</b>\n\n"
            "Your movies, series, drama, anime, "
            "cartoon and serial poster finder.\n\n"
            "🎞 <code>/poster Reacher</code>\n"
            "🌐 <code>/ott URL</code>\n"
            "📚 <code>/platforms</code>\n"
            "❓ <code>/help</code>\n"
            "ℹ️ <code>/about</code>\n\n"
            "Use the Back and Next buttons to "
            "browse available artwork.",
            parse_mode=ParseMode.HTML,
        )

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

# --------------------------------------------------
# /help
# --------------------------------------------------

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_group(update):
        return

    await update.message.reply_text(
        "╭━━━「 🎬 ᴘᴏsᴛᴇʀ ʜᴇʟᴘ 」━━━╮\n"
        "┃\n"
        "┃ 🔎 <b>Search Poster</b>\n"
        "┃ <code>/poster Movie Name</code>\n"
        "┃\n"
        "┃ 🌐 <b>Search From OTT URL</b>\n"
        "┃ <code>/ott https://example.com</code>\n"
        "┃\n"
        "┃ 📺 <b>Supported Platforms</b>\n"
        "┃ <code>/platforms</code>\n"
        "┃\n"
        "┃ 🖼 <b>Artwork Navigation</b>\n"
        "┃ <b>⬅️ Back</b> — Previous artwork\n"
        "┃ <b>Next ➡️</b> — Next artwork\n"
        "┃\n"
        "┃ ℹ️ <b>About Bot</b>\n"
        "┃ <code>/about</code>\n"
        "┃\n"
        "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"
        "⚡ <i>Powered by @Aero_Unity</i>",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

# --------------------------------------------------
# /about
# --------------------------------------------------

async def about_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_group(update):
        return

    await update.message.reply_text(
        "⍟───[ MY ᴅᴇᴛᴀɪʟꜱ ]───⍟\n\n"
        "‣ ᴍʏ ɴᴀᴍᴇ : "
        "[ᴍᴏʜᴀᴍᴍᴇᴅ ᴘᴏsᴛᴇʀ ᴢᴏɴᴇ](https://t.me/Mohammed_Poster_bot)\n"
        "‣ ᴅᴇᴠᴇʟᴏᴘᴇʀ : "
        "[ᴍᴏʜᴀᴍᴍᴇᴅ](https://t.me/Mr_Mohammed_29)\n"
        "‣ ʟɪʙʀᴀʀʏ : "
        "[ᴘʏᴛʜᴏɴ-ᴛᴇʟᴇɢʀᴀᴍ-ʙᴏᴛ](https://pypi.org/project/python-telegram-bot/)\n"
        "‣ ʟᴀɴɢᴜᴀɢᴇ : "
        "[ᴘʏᴛʜᴏɴ 𝟹](https://www.python.org/downloads/)\n"
        "‣ ᴅᴀᴛᴀ ʙᴀsᴇ : "
        "[ᴍᴏɴɢᴏ ᴅʙ](https://www.mongodb.com/)\n"
        "‣ ʙᴏᴛ sᴇʀᴠᴇʀ : "
        "[ʙᴏᴛ sᴇʀᴠᴇʀ](https://render.com)\n"
        "‣ ᴜᴘᴅᴀᴛᴇs : "
        "[Aᴇʀᴏ Uɴɪᴛʏ](https://t.me/Aero_Unity)\n"
        "‣ ʙᴜɪʟᴅ sᴛᴀᴛᴜs : "
        "ᴠ3.𝟶 [sᴛᴀʙʟᴇ](https://t.me/Aero_Unity)",
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

# --------------------------------------------------
# /platforms
# --------------------------------------------------

async def platforms_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_group(update):
        return

    await update.message.reply_text(
        "🌐 <b>sᴜᴘᴘᴏʀᴛᴇᴅ ᴘʟᴀᴛғᴏʀᴍs</b>\n\n"
        + get_platforms_text(),
        parse_mode=ParseMode.HTML,
    )

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

# --------------------------------------------------
# Send poster
# --------------------------------------------------

async def send_poster_result(
    update: Update,
    media: dict,
    platform: str,
):
    items = await asyncio.to_thread(
        build_navigation_items,
        media,
    )

    if not items:
        await update.message.reply_text(
            "❌ <b>ɴᴏ ᴀʀᴛᴡᴏʀᴋ ᴡᴀs ғᴏᴜɴᴅ ғᴏʀ ᴛʜɪs ᴛɪᴛʟᴇ.</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    cleanup_navigation()

    first = items[0]

    title = (
        media.get("title")
        or media.get("name")
        or media.get("original_title")
        or media.get("original_name")
        or "Unknown"
    )

    thumbnail = await asyncio.to_thread(
        create_thumbnail,
        first["url"],
        title,
    )

    if not thumbnail:
        await update.message.reply_text(
            "❌ <b>Failed to create thumbnail.</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    # Make sure the file is at the beginning
    thumbnail.seek(0)

    sent = await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=thumbnail,
        caption=build_caption(
            media,
            platform,
            first,
        ),
        parse_mode=ParseMode.HTML,
    )

    key = (
        update.effective_chat.id,
        update.effective_user.id,
        sent.message_id,
    )

    NAVIGATION[key] = {
        "items": items,
        "index": 0,
        "media": media,
        "platform": platform,
        "created_at": time.time(),
    }

    keyboard = make_navigation_buttons(
        key,
        0,
        len(items),
    )

    if keyboard:
        await sent.edit_reply_markup(
            reply_markup=keyboard
        )
        
# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #
# --------------------------------------------------
# /poster
# --------------------------------------------------

async def poster_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_group(update):
        return

    # FORCE SUB CHECK
    if not await force_sub(
        update,
        context,
    ):
        return

    if not context.args:
        await update.message.reply_text(
            "~ ᴇɴᴛᴇʀ ᴀ ᴛɪᴛʟᴇ.\n\n"
            "Example:\n"
            "<code>/poster Reacher</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    title = " ".join(
        context.args
    ).strip()

    processing = await update.message.reply_text(
        "🔎 sᴇᴀʀᴄʜɪɴɢ ғᴏʀ ᴀʀᴛᴡᴏʀᴋ..."
    )

    try:
        media = await asyncio.to_thread(
            search_media,
            title,
        )

        if not media:
            await processing.edit_text(
                "‼️ Nᴏ Mᴀᴛᴄʜɪɴɢ 𝗠𝗼𝘃𝗶𝗲𝘀 ᴏʀ 𝗦𝗲𝗿𝗶𝗲𝘀 ᴏʀ 𝗔𝗻𝗶𝗺𝗲 ᴏʀ 𝗦𝗲𝗿𝗶𝗮𝗹 ᴏʀ 𝗗𝗿𝗮𝗺𝗮 ᴡᴀs ғᴏᴜɴᴅ"
            )
            return

        await processing.delete()

        await send_poster_result(
            update,
            media,
            "Unknown Platform",
        )

    except Exception:
        logger.exception(
            "Poster search failed"
        )

        try:
            await processing.edit_text(
                "⚠️  𝗔𝗻 𝗲𝗿𝗿𝗼𝗿 𝗼𝗰𝗰𝘂𝗿𝗿𝗲𝗱 𝘄𝗵𝗶𝗹𝗲 𝘀𝗲𝗮𝗿𝗰𝗵𝗶𝗻𝗴. 𝗣𝗹𝗲𝗮𝘀𝗲 𝘁𝗿𝘆 𝗮𝗴𝗮𝗶𝗻"
            )
        except Exception:
            pass

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

# --------------------------------------------------
# /ott
# --------------------------------------------------

async def ott_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_group(update):
        return

    # FORCE SUB CHECK
    if not await force_sub(
        update,
        context,
    ):
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Enter an OTT URL.\n\n"
            "Example:\n"
            "<code>/ott https://example.com/...</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    url = context.args[0].strip()

    if not (
        url.startswith("http://")
        or url.startswith("https://")
    ):
        await update.message.reply_text(
            "❌ Only HTTP/HTTPS URLs are accepted."
        )
        return

    platform = detect_platform(
        url
    )

    processing = await update.message.reply_text(
        "🌐 Reading the OTT page..."
    )

    try:
        title = await asyncio.to_thread(
            extract_title_from_url,
            url,
        )

        if not title:
            await processing.edit_text(
                "❌ I couldn't extract a title "
                "from this page.\n\n"
                "Try using:\n"
                "<code>/poster Movie Name</code>",
                parse_mode=ParseMode.HTML,
            )
            return

        logger.info(
            "OTT title: %s | Platform: %s",
            title,
            platform,
        )

        media = await asyncio.to_thread(
            search_media,
            title,
        )

        if not media:
            await processing.edit_text(
                "❌ I couldn't find matching "
                "artwork for:\n\n"
                f"{title}"
            )
            return

        await processing.delete()

        # ------------------------- #
        # Get Artwork
        # ------------------------- #

        items = await asyncio.to_thread(
            build_navigation_items,
            media,
        )

        if not items:
            await update.message.reply_text(
                "❌ No artwork was found for "
                "this title."
            )
            return

        cleanup_navigation()

        first = items[0]

        # ------------------------- #
        # Create Thumbnail
        # ------------------------- #

        title = (
            media.get("title")
            or media.get("name")
            or media.get("original_title")
            or media.get("original_name")
            or "Unknown"
        )

        thumbnail = await asyncio.to_thread(
            create_thumbnail,
            first["url"],
            title,
        )

        if not thumbnail:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Failed to create thumbnail.",
            )
            return

        # ------------------------- #
        # Send Thumbnail
        # ------------------------- #

        sent = await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=thumbnail,
            caption=build_caption(
                media,
                platform,
                first,
            ),
            parse_mode=ParseMode.HTML,
        )

        # ------------------------- #
        # Save Navigation
        # ------------------------- #

        key = (
            update.effective_chat.id,
            update.effective_user.id,
            sent.message_id,
        )

        NAVIGATION[key] = {
            "items": items,
            "index": 0,
            "media": media,
            "platform": platform,
            "created_at": time.time(),
        }

        keyboard = make_navigation_buttons(
            key,
            0,
            len(items),
        )

        if keyboard:
            await sent.edit_reply_markup(
                reply_markup=keyboard
            )

    except Exception:
        logger.exception(
            "OTT processing failed"
        )

        try:
            await processing.edit_text(
                "⚠️ The OTT page could not be "
                "processed."
            )
        except Exception:
            pass

            # ------------------------- #

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

# --------------------------------------------------
# Back / Next
# --------------------------------------------------

async def navigation_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    try:
        await query.answer()

        parts = query.data.split(":")

        if len(parts) != 4:
            return

        action = parts[0]

        chat_id = int(parts[1])
        user_id = int(parts[2])
        message_id = int(parts[3])

        key = (
            chat_id,
            user_id,
            message_id,
        )

        data = NAVIGATION.get(key)

        if not data:
            await query.answer(
                "This navigation session expired.",
                show_alert=True,
            )
            return

        # Only the user who requested the poster
        # can control the buttons.
        if query.from_user.id != user_id:
            await query.answer(
                "These buttons belong to another user.",
                show_alert=True,
            )
            return

        index = data["index"]

        if action == "poster_next":
            index += 1

        elif action == "poster_prev":
            index -= 1

        index = max(
            0,
            min(
                index,
                len(data["items"]) - 1,
            ),
        )

        data["index"] = index

        item = data["items"][index]

        image_url = item.get("url")

        if not image_url:
            await query.answer(
                "❌ Image URL is missing.",
                show_alert=True,
            )
            return

        logger.info(
            "Navigation | user=%s | index=%s | type=%s",
            user_id,
            index,
            item.get("type"),
        )

        # --------------------------------------------------
        # Movie / Series title
        # --------------------------------------------------

        title = (
            data["media"].get("title")
            or data["media"].get("name")
            or data["media"].get("original_title")
            or data["media"].get("original_name")
            or "Unknown"
        )

        # Add season name when browsing a season.
        season = item.get("season")

        if season:
            season_name = season.get(
                "name",
                "",
            )

            if season_name:
                title = (
                    f"{title} {season_name}"
                )

        # --------------------------------------------------
        # Create thumbnail
        # --------------------------------------------------

        thumbnail = await asyncio.to_thread(
            create_thumbnail,
            image_url,
            title,
        )

        if not thumbnail:
            await query.answer(
                "❌ Failed to create thumbnail.",
                show_alert=True,
            )
            return

        # --------------------------------------------------
        # Keyboard
        # --------------------------------------------------

        keyboard = make_navigation_buttons(
            key,
            index,
            len(data["items"]),
        )

        # --------------------------------------------------
        # Caption
        # --------------------------------------------------

        caption = build_caption(
            data["media"],
            data["platform"],
            item,
        )

        # --------------------------------------------------
        # Replace existing Telegram photo
        # --------------------------------------------------

        try:

            media = InputMediaPhoto(
                media=thumbnail,
                caption=caption,
                parse_mode=ParseMode.HTML,
            )

            await query.message.edit_media(
                media=media,
                reply_markup=keyboard,
            )

        except Exception:
            logger.exception(
                "Telegram edit_media failed"
            )

            await query.answer(
                "❌ Telegram could not update this artwork.",
                show_alert=True,
            )

            return

    except Exception:
        logger.exception(
            "Navigation callback failed"
        )

        try:
            await query.answer(
                "❌ Unable to change artwork.",
                show_alert=True,
            )
        except Exception:
            pass

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

# --------------------------------------------------
# Error handler
# --------------------------------------------------

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):
    logger.error(
        "Telegram error: %s",
        context.error,
        exc_info=context.error,
    )

async def stats_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_owner(update):

        await update.message.reply_text(
            "🚫 Owner only command."
        )

        return

    total_users = await get_user_count()

    total_chats = await get_chat_count()

    await update.message.reply_text(
        "📊 <b>BOT STATISTICS</b>\n\n"
        f"👤 <b>Total Users:</b> "
        f"<code>{total_users}</code>\n"
        f"👥 <b>Total Groups:</b> "
        f"<code>{total_chats}</code>\n\n"
        "⚡ <b>Mohammed Poster Zone</b>",
        parse_mode=ParseMode.HTML,
    )

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

async def broadcast_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_owner(update):

        await update.message.reply_text(
            "🚫 Owner only command."
        )

        return

    if not update.message.reply_to_message:

        await update.message.reply_text(
            "❌ Reply to a message with "
            "<code>/broadcast</code>.",
            parse_mode=ParseMode.HTML,
        )

        return

    users = await get_all_user_ids()

    if not users:

        await update.message.reply_text(
            "❌ No users found."
        )

        return

    processing = await update.message.reply_text(
        "📢 <b>Broadcast started...</b>\n\n"
        f"👤 Users: <code>{len(users)}</code>",
        parse_mode=ParseMode.HTML,
    )

    success = 0
    failed = 0

    source_message = (
        update.message.reply_to_message
    )

    for user_id in users:

        try:

            await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=(
                    source_message.chat_id
                ),
                message_id=(
                    source_message.message_id
                ),
            )

            success += 1

        except Exception as error:

            failed += 1

            logger.warning(
                "Broadcast failed | user=%s | error=%s",
                user_id,
                error,
            )

        await asyncio.sleep(
            0.05
        )

    await processing.edit_text(
        "📢 <b>BROADCAST COMPLETED</b>\n\n"
        f"👥 <b>Total:</b> "
        f"<code>{len(users)}</code>\n"
        f"✅ <b>Success:</b> "
        f"<code>{success}</code>\n"
        f"❌ <b>Failed:</b> "
        f"<code>{failed}</code>",
        parse_mode=ParseMode.HTML,
    )

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

async def authuser_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_owner(update):

        await update.message.reply_text(
            "🚫 Owner only command."
        )
        return

    if not context.args:

        await update.message.reply_text(
            "Usage:\n"
            "<code>/authuser USER_ID</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    try:

        user_id = int(
            context.args[0]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Invalid user ID."
        )
        return

    await authorize_user(
        user_id
    )

    await update.message.reply_text(
        "✅ <b>User Authorized</b>\n\n"
        f"👤 User ID: "
        f"<code>{user_id}</code>",
        parse_mode=ParseMode.HTML,
    )

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

async def unauthuser_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_owner(update):

        await update.message.reply_text(
            "🚫 Owner only command."
        )
        return

    if not context.args:

        await update.message.reply_text(
            "Usage:\n"
            "<code>/unauthuser USER_ID</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    try:

        user_id = int(
            context.args[0]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Invalid user ID."
        )
        return

    await unauthorize_user(
        user_id
    )

    await update.message.reply_text(
        "✅ <b>User Unauthorized</b>\n\n"
        f"👤 User ID: "
        f"<code>{user_id}</code>",
        parse_mode=ParseMode.HTML,
    )

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

async def authchat_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_owner(update):

        await update.message.reply_text(
            "🚫 Owner only command."
        )
        return

    if not context.args:

        await update.message.reply_text(
            "Usage:\n"
            "<code>/authchat CHAT_ID</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    try:

        chat_id = int(
            context.args[0]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Invalid chat ID."
        )
        return

    await authorize_chat(
        chat_id
    )

    await update.message.reply_text(
        "✅ <b>Chat Authorized</b>\n\n"
        f"💬 Chat ID: "
        f"<code>{chat_id}</code>",
        parse_mode=ParseMode.HTML,
    )

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

async def unauthchat_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_owner(update):

        await update.message.reply_text(
            "🚫 Owner only command."
        )
        return

    if not context.args:

        await update.message.reply_text(
            "Usage:\n"
            "<code>/unauthchat CHAT_ID</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    try:

        chat_id = int(
            context.args[0]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Invalid chat ID."
        )
        return

    await unauthorize_chat(
        chat_id
    )

    await update.message.reply_text(
        "✅ <b>Chat Unauthorized</b>\n\n"
        f"💬 Chat ID: "
        f"<code>{chat_id}</code>",
        parse_mode=ParseMode.HTML,
    )

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

async def ban_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_owner(update):

        await update.message.reply_text(
            "🚫 Owner only command."
        )
        return

    if not context.args:

        await update.message.reply_text(
            "Usage:\n"
            "<code>/ban USER_ID</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    try:

        user_id = int(
            context.args[0]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Invalid user ID."
        )
        return

    await ban_user(
        user_id
    )

    await update.message.reply_text(
        "🚫 <b>User Banned</b>\n\n"
        f"👤 User ID: "
        f"<code>{user_id}</code>",
        parse_mode=ParseMode.HTML,
    )

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

async def unban_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_owner(update):

        await update.message.reply_text(
            "🚫 Owner only command."
        )
        return

    if not context.args:

        await update.message.reply_text(
            "Usage:\n"
            "<code>/unban USER_ID</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    try:

        user_id = int(
            context.args[0]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Invalid user ID."
        )
        return

    await unban_user(
        user_id
    )

    await update.message.reply_text(
        "✅ <b>User Unbanned</b>\n\n"
        f"👤 User ID: "
        f"<code>{user_id}</code>",
        parse_mode=ParseMode.HTML,
    )



# --------------------------------------------------
# Main
# --------------------------------------------------

def main():

    logger.info(
        "Starting %s...",
        BOT_NAME,
    )

    init_database()

    threading.Thread(
        target=run_web_server,
        daemon=True,
    ).start()

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    group_filter = (
        filters.ChatType.GROUPS
    )

    application.add_handler(
        CommandHandler(
            "start",
            start_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "help",
            help_command,
            filters=group_filter,
        )
    )

    application.add_handler(
        CommandHandler(
            "about",
            about_command,
            filters=group_filter,
        )
    )

    application.add_handler(
        CommandHandler(
            "platforms",
            platforms_command,
            filters=group_filter,
        )
    )

    application.add_handler(
        CommandHandler(
            "poster",
            poster_command,
            filters=group_filter,
        )
    )

    application.add_handler(
        CommandHandler(
            "ott",
            ott_command,
            filters=group_filter,
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            navigation_callback,
            pattern=r"^poster_(prev|next):",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            handle_force_sub_callback,
            pattern=r"^force_sub_check$",
        )
    )

    application.add_error_handler(
        error_handler
    )

    application.add_handler(
        CommandHandler(
            "stats",
            stats_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "broadcast",
            broadcast_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "authuser",
            authuser_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "unauthuser",
            unauthuser_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "authchat",
            authchat_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "unauthchat",
            unauthchat_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "ban",
            ban_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "unban",
            unban_command,
        )
    )


    logger.info(
        "Mohammed Poster Zone is online."
    )

    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

if __name__ == "__main__":
    main()

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #
