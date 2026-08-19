# ============================================================
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ============================================================

import asyncio
import logging
import threading
import time

from flask import Flask

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
)

from telegram.constants import (
    ParseMode,
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from config import (
    BOT_TOKEN,
    BOT_NAME,
    PORT,
    OWNER_ID,
    UPDATES_URL,
)

from database import (
    init_database,
    save_user,
    save_chat,
    get_user_count,
    get_chat_count,
    authorize_user,
    unauthorize_user,
    authorize_chat,
    unauthorize_chat,
    ban_user,
    unban_user,
    is_banned,
    get_all_user_ids,
)

from platforms import (
    detect_platform,
    get_platforms_text,
)

from poster import (
    search_media,
    extract_title_from_url,
    build_navigation_items,
    build_caption,
    create_thumbnail,
)

from mohammed.forcesub import (
    force_sub,
    force_sub_callback,
)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    format=(
        "%(asctime)s - "
        "%(name)s - "
        "%(levelname)s - "
        "%(message)s"
    ),
    level=logging.INFO,
)

logger = logging.getLogger(
    "mohammed-poster-zone"
)


# ============================================================
# FLASK
# ============================================================

app = Flask(
    __name__
)


@app.route("/")
def home():

    return {
        "status": "online",
        "bot": BOT_NAME,
        "service": "Mohammed Poster Zone",
    }


@app.route("/health")
def health():

    return {
        "status": "healthy",
        "service": "Mohammed Poster Zone",
    }


def run_web_server():

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False,
        use_reloader=False,
    )


# ============================================================
# HELPERS
# ============================================================

def is_group(
    update: Update,
):

    if not update.effective_chat:
        return False

    return update.effective_chat.type in (
        "group",
        "supergroup",
    )


def is_owner(
    update: Update,
):

    user = update.effective_user

    if not user:
        return False

    return user.id == OWNER_ID


# ============================================================
# NAVIGATION STORAGE
# ============================================================

NAVIGATION = {}

NAVIGATION_TTL = (
    60 * 60
)


def cleanup_navigation():

    now = time.time()

    expired = []

    for (
        key,
        value,
    ) in list(
        NAVIGATION.items()
    ):

        try:

            created_at = value.get(
                "created_at",
                now,
            )

            if (
                now - created_at
                > NAVIGATION_TTL
            ):

                expired.append(
                    key
                )

        except Exception:

            expired.append(
                key
            )

    for key in expired:

        NAVIGATION.pop(
            key,
            None,
        )


# ============================================================
# NAVIGATION BUTTONS
# ============================================================

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


# ============================================================
# FORCE SUB CALLBACK
# ============================================================

async def handle_force_sub_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    pending = await force_sub_callback(
        update,
        context,
    )

    if not pending:
        return

    user = update.effective_user
    chat = update.effective_chat

    if not user or not chat:
        return

    command = str(
        pending.get(
            "command",
            "",
        )
    ).lower().strip()

    args = pending.get(
        "args",
        [],
    )

    logger.info(
        "Executing pending command | "
        "user=%s | command=%s | args=%s",
        user.id,
        command,
        args,
    )

    # ========================================================
    # PENDING /poster
    # ========================================================

    if command == "poster":

        if not args:

            await context.bot.send_message(
                chat_id=chat.id,
                text=(
                    "❌ Nᴏ ᴘᴏsᴛᴇʀ ᴛɪᴛʟᴇ "
                    "ᴡᴀs sᴀᴠᴇᴅ."
                ),
            )

            return

        title = " ".join(
            args
        ).strip()

        processing = (
            await context.bot.send_message(
                chat_id=chat.id,
                text=(
                    "🔎 Sᴇᴀʀᴄʜɪɴɢ "
                    "ғᴏʀ ᴀʀᴛᴡᴏʀᴋ..."
                ),
            )
        )

        try:

            media = await asyncio.to_thread(
                search_media,
                title,
            )

            if not media:

                await processing.edit_text(
                    "‼️ Nᴏ Mᴀᴛᴄʜɪɴɢ "
                    "Mᴏᴠɪᴇs ᴏʀ Sᴇʀɪᴇs "
                    "ᴏʀ Aɴɪᴍᴇ ᴏʀ Sᴇʀɪᴀʟ "
                    "ᴏʀ Dʀᴀᴍᴀ ᴡᴀs ғᴏᴜɴᴅ."
                )

                return

            await processing.delete()

            await send_poster_result(
                update,
                media,
                None,
            )

        except Exception:

            logger.exception(
                "Pending poster execution failed"
            )

            try:

                await processing.edit_text(
                    "⚠️ Aɴ ᴇʀʀᴏʀ "
                    "ᴏᴄᴄᴜʀʀᴇᴅ ᴡʜɪʟᴇ "
                    "sᴇᴀʀᴄʜɪɴɢ."
                )

            except Exception:
                pass

        return

    # ========================================================
    # PENDING /ott
    # ========================================================

    if command == "ott":

        if not args:

            await context.bot.send_message(
                chat_id=chat.id,
                text=(
                    "❌ Nᴏ OTT URL "
                    "ᴡᴀs sᴀᴠᴇᴅ."
                ),
            )

            return

        url = str(
            args[0]
        ).strip()

        if not url.startswith(
            (
                "http://",
                "https://",
            )
        ):

            await context.bot.send_message(
                chat_id=chat.id,
                text=(
                    "‼️ Iɴᴠᴀʟɪᴅ OTT URL."
                ),
            )

            return

        platform = detect_platform(
            url
        )

        processing = (
            await context.bot.send_message(
                chat_id=chat.id,
                text=(
                    "🌐 Rᴇᴀᴅɪɴɢ "
                    "Tʜᴇ OTT Pᴀɢᴇ..."
                ),
            )
        )

        try:

            title = await asyncio.to_thread(
                extract_title_from_url,
                url,
            )

            if not title:

                await processing.edit_text(
                    "❌ I ᴄᴏᴜʟᴅɴ'ᴛ "
                    "ᴇxᴛʀᴀᴄᴛ ᴀ ᴛɪᴛʟᴇ "
                    "ғʀᴏᴍ ᴛʜɪs ᴘᴀɢᴇ."
                )

                return

            media = await asyncio.to_thread(
                search_media,
                title,
            )

            if not media:

                await processing.edit_text(
                    "❌ I ᴄᴏᴜʟᴅɴ'ᴛ ғɪɴᴅ "
                    "ᴍᴀᴛᴄʜɪɴɢ ᴀʀᴛᴡᴏʀᴋ."
                )

                return

            await processing.delete()

            await send_poster_result(
                update,
                media,
                platform,
            )

        except Exception:

            logger.exception(
                "Pending OTT execution failed"
            )

            try:

                await processing.edit_text(
                    "⚠️ Tʜᴇ OTT ᴘᴀɢᴇ "
                    "ᴄᴏᴜʟᴅ ɴᴏᴛ "
                    "ʙᴇ ᴘʀᴏᴄᴇssᴇᴅ."
                )

            except Exception:
                pass

        return


# ============================================================
# START
# ============================================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user
    chat = update.effective_chat

    if not user or not chat:
        return

    try:

        await save_user(
            user
        )

        await save_chat(
            chat
        )

    except Exception:

        logger.exception(
            "Failed to save user/chat"
        )

    # ========================================================
    # PRIVATE
    # ========================================================

    if chat.type == "private":

        if await is_banned(
            user.id
        ):

            await update.message.reply_text(
                (
                    "🚫 <b>Yᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ "
                    "ғʀᴏᴍ ᴜsɪɴɢ ᴛʜɪs ʙᴏᴛ.</b>\n\n"
                    "Contact @Mr_Mohammed_29"
                ),
                parse_mode=ParseMode.HTML,
            )

            return

        keyboard = InlineKeyboardMarkup(
            [

                [
                    InlineKeyboardButton(
                        "• ᴘᴏsᴛᴇʀ ɢʀᴏᴜᴘ •",
                        url=(
                            "https://t.me/"
                            "+hxfpcrzX0YFjNmRl"
                        ),
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
            (
                "🎬 <b>Mohammed Poster Zone</b>\n\n"
                "Welcome to Mohammed Poster Bot! 👋\n\n"
                "Please use this bot "
                "in our Poster Group."
            ),
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )

        return

    # ========================================================
    # GROUP
    # ========================================================

    if is_group(update):

        await update.message.reply_text(
            (
                "🎬 <b>Mohammed Poster Zone</b>\n\n"

                "Your movies, series, drama, anime, "
                "cartoon and serial poster finder.\n\n"

                "🎞 <code>/poster Reacher</code>\n"
                "🌐 <code>/ott https://example.com</code>\n"
                "📚 <code>/platforms</code>\n"
                "❓ <code>/help</code>\n"
                "ℹ️ <code>/about</code>\n\n"

                "Use Back and Next to browse "
                "available artwork."
            ),
            parse_mode=ParseMode.HTML,
        )


# ============================================================
# HELP
# ============================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_group(update):
        return

    await update.message.reply_text(
        (
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
            "┃ <b>Back</b> — Previous artwork\n"
            "┃ <b>Next</b> — Next artwork\n"
            "┃\n"
            "┃ ℹ️ <b>About Bot</b>\n"
            "┃ <code>/about</code>\n"
            "┃\n"
            "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"
            "⚡ <i>Powered by @Aero_Unity</i>"
        ),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


# ============================================================
# ABOUT
# ============================================================

async def about_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_group(update):
        return

    await update.message.reply_text(
        (
            "⍟───[ MY ᴅᴇᴛᴀɪʟꜱ ]───⍟\n\n"

            "‣ ᴍʏ ɴᴀᴍᴇ : "
            '<a href="https://t.me/Mohammed_Poster_bot">'
            "Mohammed Poster Zone</a>\n"

            "‣ ᴅᴇᴠᴇʟᴏᴘᴇʀ : "
            '<a href="https://t.me/Mr_Mohammed_29">'
            "Mohammed</a>\n"

            "‣ ʟɪʙʀᴀʀʏ : "
            '<a href="https://pypi.org/project/python-telegram-bot/">'
            "python-telegram-bot</a>\n"

            "‣ ʟᴀɴɢᴜᴀɢᴇ : "
            '<a href="https://www.python.org/">'
            "Python 3</a>\n"

            "‣ ᴅᴀᴛᴀʙᴀsᴇ : "
            '<a href="https://www.mongodb.com/">'
            "MongoDB</a>\n"

            "‣ ʙᴏᴛ sᴇʀᴠᴇʀ : "
            '<a href="https://render.com/">'
            "Render</a>\n'

            "‣ ᴜᴘᴅᴀᴛᴇs : "
            '<a href="https://t.me/Aero_Unity">'
            "Aero Unity</a>\n"

            "‣ ʙᴜɪʟᴅ sᴛᴀᴛᴜs : "
            "V3.0 Stable"
        ),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


# ============================================================
# PLATFORMS
# ============================================================

async def platforms_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_group(update):
        return

    await update.message.reply_text(
        (
            "🌐 <b>SUPPORTED PLATFORMS</b>\n\n"
            + get_platforms_text()
        ),
        parse_mode=ParseMode.HTML,
    )

async def send_poster_result(
    update: Update,
    media: dict,
    platform: str = None,
):

    if not update.effective_chat:
        return

    if not update.effective_user:
        return

    items = await asyncio.to_thread(
        build_navigation_items,
        media,
    )

    if not items:

        await context_send_message(
            update,
            (
                "❌ <b>ɴᴏ ᴀʀᴛᴡᴏʀᴋ "
                "ᴡᴀs ғᴏᴜɴᴅ.</b>"
            ),
        )

        return

    cleanup_navigation()

    first = items[0]

    # --------------------------------------------------------
    # Create EXACT 1000x800 thumbnail
    # --------------------------------------------------------

    thumbnail = await asyncio.to_thread(
        create_thumbnail,
        first.get("url"),
        (
            media.get("title")
            or media.get("name")
            or "Unknown"
        ),
    )

    if not thumbnail:

        await context_send_message(
            update,
            "❌ Failed to create 5:4 thumbnail.",
        )

        return

    thumbnail.seek(0)

    # --------------------------------------------------------
    # Caption
    # --------------------------------------------------------

    caption = build_caption(
        media,
        platform,
        first,
    )

    # --------------------------------------------------------
    # SEND 1000x800 IMAGE
    # --------------------------------------------------------

    sent = await update.effective_chat.send_photo(
        photo=thumbnail,
        caption=caption,
        parse_mode=ParseMode.HTML,
    )

    # --------------------------------------------------------
    # Navigation key
    # --------------------------------------------------------

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


# ============================================================
# SMALL SEND HELPER
# ============================================================

async def context_send_message(
    update,
    text,
):

    if update.effective_chat:

        await update.effective_chat.send_message(
            text=text,
            parse_mode=ParseMode.HTML,
        )


# ============================================================
# /poster
# ============================================================

async def poster_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_group(update):
        return

    # --------------------------------------------------------
    # Force subscribe
    # --------------------------------------------------------

    if not await force_sub(
        update,
        context,
    ):
        return

    # --------------------------------------------------------
    # No title
    # --------------------------------------------------------

    if not context.args:

        await update.message.reply_text(
            (
                "❌ <b>Enter a title.</b>\n\n"
                "Example:\n"
                "<code>/poster Reacher</code>"
            ),
            parse_mode=ParseMode.HTML,
        )

        return

    title = " ".join(
        context.args
    ).strip()

    processing = (
        await update.message.reply_text(
            "🔎 Sᴇᴀʀᴄʜɪɴɢ ғᴏʀ ᴀʀᴛᴡᴏʀᴋ..."
        )
    )

    try:

        media = await asyncio.to_thread(
            search_media,
            title,
        )

        if not media:

            await processing.edit_text(
                (
                    "‼️ Nᴏ Mᴀᴛᴄʜɪɴɢ "
                    "Mᴏᴠɪᴇs ᴏʀ Sᴇʀɪᴇs "
                    "ᴏʀ Aɴɪᴍᴇ ᴏʀ Sᴇʀɪᴀʟ "
                    "ᴏʀ Dʀᴀᴍᴀ ᴡᴀs ғᴏᴜɴᴅ."
                )
            )

            return

        await processing.delete()

        await send_poster_result(
            update,
            media,
            None,
        )

    except Exception:

        logger.exception(
            "Poster search failed"
        )

        try:

            await processing.edit_text(
                (
                    "⚠️ Aɴ ᴇʀʀᴏʀ "
                    "ᴏᴄᴄᴜʀʀᴇᴅ ᴡʜɪʟᴇ "
                    "sᴇᴀʀᴄʜɪɴɢ."
                )
            )

        except Exception:
            pass


# ============================================================
# /ott
# ============================================================

async def ott_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_group(update):
        return

    # --------------------------------------------------------
    # Force subscribe
    # --------------------------------------------------------

    if not await force_sub(
        update,
        context,
    ):
        return

    # --------------------------------------------------------
    # URL
    # --------------------------------------------------------

    if not context.args:

        await update.message.reply_text(
            (
                "❌ <b>Enter an OTT URL.</b>\n\n"
                "Example:\n"
                "<code>/ott https://example.com/...</code>"
            ),
            parse_mode=ParseMode.HTML,
        )

        return

    url = str(
        context.args[0]
    ).strip()

    if not url.startswith(
        (
            "http://",
            "https://",
        )
    ):

        await update.message.reply_text(
            "❌ Only HTTP/HTTPS URLs are accepted."
        )

        return

    # --------------------------------------------------------
    # Detect platform
    # --------------------------------------------------------

    platform = detect_platform(
        url
    )

    processing = (
        await update.message.reply_text(
            "🌐 Rᴇᴀᴅɪɴɢ Tʜᴇ OTT Pᴀɢᴇ..."
        )
    )

    try:

        title = await asyncio.to_thread(
            extract_title_from_url,
            url,
        )

        if not title:

            await processing.edit_text(
                (
                    "❌ I couldn't extract "
                    "a title from this page.\n\n"
                    "Try:\n"
                    "<code>/poster Movie Name</code>"
                ),
                parse_mode=ParseMode.HTML,
            )

            return

        logger.info(
            "OTT title=%s | platform=%s",
            title,
            platform,
        )

        media = await asyncio.to_thread(
            search_media,
            title,
        )

        if not media:

            await processing.edit_text(
                (
                    "❌ I couldn't find "
                    "matching artwork for:\n\n"
                    f"{html_escape(title)}"
                ),
                parse_mode=ParseMode.HTML,
            )

            return

        await processing.delete()

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # send_poster_result creates the 1000x800
        # thumbnail itself.
        #
        # Do NOT send first["url"] directly.
        # ----------------------------------------------------

        await send_poster_result(
            update,
            media,
            platform,
        )

    except Exception:

        logger.exception(
            "OTT processing failed"
        )

        try:

            await processing.edit_text(
                (
                    "⚠️ The OTT page "
                    "could not be processed."
                )
            )

        except Exception:
            pass


# ============================================================
# HTML ESCAPE
# ============================================================

def html_escape(
    text,
):

    import html

    return html.escape(
        str(text)
    )


# ============================================================
# BACK / NEXT
# ============================================================

async def navigation_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    try:

        await query.answer()

        data_string = (
            query.data or ""
        )

        parts = data_string.split(
            ":"
        )

        if len(parts) != 4:
            return

        action = parts[0]

        chat_id = int(
            parts[1]
        )

        user_id = int(
            parts[2]
        )

        message_id = int(
            parts[3]
        )

        key = (
            chat_id,
            user_id,
            message_id,
        )

        data = NAVIGATION.get(
            key
        )

        if not data:

            await query.answer(
                "This navigation session expired.",
                show_alert=True,
            )

            return

        # ----------------------------------------------------
        # Only requester can control buttons
        # ----------------------------------------------------

        if (
            not query.from_user
            or query.from_user.id
            != user_id
        ):

            await query.answer(
                "These buttons belong to another user.",
                show_alert=True,
            )

            return

        index = int(
            data.get(
                "index",
                0,
            )
        )

        # ----------------------------------------------------
        # Change index
        # ----------------------------------------------------

        if action == "poster_next":

            index += 1

        elif action == "poster_prev":

            index -= 1

        index = max(
            0,
            min(
                index,
                len(
                    data["items"]
                ) - 1,
            ),
        )

        data["index"] = index

        item = data["items"][index]

        image_url = item.get(
            "url"
        )

        if not image_url:

            await query.answer(
                "❌ Image URL is missing.",
                show_alert=True,
            )

            return

        # ----------------------------------------------------
        # Create EXACT 1000x800 thumbnail
        # ----------------------------------------------------

        thumbnail = await asyncio.to_thread(
            create_thumbnail,
            image_url,
            (
                data["media"].get(
                    "title"
                )
                or data["media"].get(
                    "name"
                )
                or "Unknown"
            ),
        )

        if not thumbnail:

            await query.answer(
                "❌ Failed to create thumbnail.",
                show_alert=True,
            )

            return

        thumbnail.seek(0)

        # ----------------------------------------------------
        # Caption
        # ----------------------------------------------------

        caption = build_caption(
            data["media"],
            data.get(
                "platform"
            ),
            item,
        )

        # ----------------------------------------------------
        # Edit photo
        # ----------------------------------------------------

        media = InputMediaPhoto(
            media=thumbnail,
            caption=caption,
            parse_mode=ParseMode.HTML,
        )

        keyboard = make_navigation_buttons(
            key,
            index,
            len(
                data["items"]
            ),
        )

        await query.message.edit_media(
            media=media,
            reply_markup=keyboard,
        )

        # ----------------------------------------------------
        # Refresh timestamp
        # ----------------------------------------------------

        data["created_at"] = (
            time.time()
        )

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


# ============================================================
# ERROR HANDLER
# ============================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):

    logger.error(
        "Telegram error: %s",
        context.error,
        exc_info=context.error,
    )


# ============================================================
# /stats
# ============================================================

async def stats_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if not is_owner(update):

        await update.message.reply_text(
            "🚫 Owner only command."
        )

        return

    total_users = (
        await get_user_count()
    )

    total_chats = (
        await get_chat_count()
    )

    await update.message.reply_text(
        (
            "📊 <b>BOT STATISTICS</b>\n\n"

            "👤 <b>Total Users:</b> "
            f"<code>{total_users}</code>\n"

            "👥 <b>Total Groups:</b> "
            f"<code>{total_chats}</code>\n\n"

            "⚡ <b>Mohammed Poster Zone</b>"
        ),
        parse_mode=ParseMode.HTML,
    )


# ============================================================
# /broadcast
# ============================================================

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
            (
                "❌ Reply to a message "
                "with <code>/broadcast</code>."
            ),
            parse_mode=ParseMode.HTML,
        )

        return

    users = await get_all_user_ids()

    if not users:

        await update.message.reply_text(
            "❌ No users found."
        )

        return

    processing = (
        await update.message.reply_text(
            (
                "📢 <b>Broadcast started...</b>\n\n"
                f"👤 Users: <code>{len(users)}</code>"
            ),
            parse_mode=ParseMode.HTML,
        )
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
                "Broadcast failed | "
                "user=%s | error=%s",
                user_id,
                error,
            )

        await asyncio.sleep(
            0.05
        )

    await processing.edit_text(
        (
            "📢 <b>BROADCAST COMPLETED</b>\n\n"

            f"👥 <b>Total:</b> "
            f"<code>{len(users)}</code>\n"

            f"✅ <b>Success:</b> "
            f"<code>{success}</code>\n"

            f"❌ <b>Failed:</b> "
            f"<code>{failed}</code>"
        ),
        parse_mode=ParseMode.HTML,
    )


# ============================================================
# /authuser
# ============================================================

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
            (
                "Usage:\n"
                "<code>/authuser USER_ID</code>"
            ),
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
        (
            "✅ <b>User Authorized</b>\n\n"
            f"👤 User ID: <code>{user_id}</code>"
        ),
        parse_mode=ParseMode.HTML,
    )


# ============================================================
# /unauthuser
# ============================================================

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
            (
                "Usage:\n"
                "<code>/unauthuser USER_ID</code>"
            ),
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
        (
            "✅ <b>User Unauthorized</b>\n\n"
            f"👤 User ID: <code>{user_id}</code>"
        ),
        parse_mode=ParseMode.HTML,
    )


# ============================================================
# /authchat
# ============================================================

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
            (
                "Usage:\n"
                "<code>/authchat CHAT_ID</code>"
            ),
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
        (
            "✅ <b>Chat Authorized</b>\n\n"
            f"💬 Chat ID: <code>{chat_id}</code>"
        ),
        parse_mode=ParseMode.HTML,
    )


# ============================================================
# /unauthchat
# ============================================================

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
            (
                "Usage:\n"
                "<code>/unauthchat CHAT_ID</code>"
            ),
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
        (
            "✅ <b>Chat Unauthorized</b>\n\n"
            f"💬 Chat ID: <code>{chat_id}</code>"
        ),
        parse_mode=ParseMode.HTML,
    )


# ============================================================
# /ban
# ============================================================

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
            (
                "Usage:\n"
                "<code>/ban USER_ID</code>"
            ),
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
        (
            "🚫 <b>User Banned</b>\n\n"
            f"👤 User ID: <code>{user_id}</code>"
        ),
        parse_mode=ParseMode.HTML,
    )


# ============================================================
# /unban
# ============================================================

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
            (
                "Usage:\n"
                "<code>/unban USER_ID</code>"
            ),
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
        (
            "✅ <b>User Unbanned</b>\n\n"
            f"👤 User ID: <code>{user_id}</code>"
        ),
        parse_mode=ParseMode.HTML,
    )


# ============================================================
# MAIN
# ============================================================

def main():

    logger.info(
        "Starting %s...",
        BOT_NAME,
    )

    # --------------------------------------------------------
    # Database
    # --------------------------------------------------------

    init_database()

    # --------------------------------------------------------
    # Flask server
    # --------------------------------------------------------

    threading.Thread(
        target=run_web_server,
        daemon=True,
    ).start()

    # --------------------------------------------------------
    # Telegram application
    # --------------------------------------------------------

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    group_filter = (
        filters.ChatType.GROUPS
    )

    # --------------------------------------------------------
    # Start
    # --------------------------------------------------------

    application.add_handler(
        CommandHandler(
            "start",
            start_command,
        )
    )

    # --------------------------------------------------------
    # Help
    # --------------------------------------------------------

    application.add_handler(
        CommandHandler(
            "help",
            help_command,
            filters=group_filter,
        )
    )

    # --------------------------------------------------------
    # About
    # --------------------------------------------------------

    application.add_handler(
        CommandHandler(
            "about",
            about_command,
            filters=group_filter,
        )
    )

    # --------------------------------------------------------
    # Platforms
    # --------------------------------------------------------

    application.add_handler(
        CommandHandler(
            "platforms",
            platforms_command,
            filters=group_filter,
        )
    )

    # --------------------------------------------------------
    # Poster
    # --------------------------------------------------------

    application.add_handler(
        CommandHandler(
            "poster",
            poster_command,
            filters=group_filter,
        )
    )

    # --------------------------------------------------------
    # OTT
    # --------------------------------------------------------

    application.add_handler(
        CommandHandler(
            "ott",
            ott_command,
            filters=group_filter,
        )
    )

    # --------------------------------------------------------
    # Poster navigation
    # --------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            navigation_callback,
            pattern=r"^poster_(prev|next):",
        )
    )

    # --------------------------------------------------------
    # Force subscribe
    # --------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            handle_force_sub_callback,
            pattern=r"^force_sub_check$",
        )
    )

    # --------------------------------------------------------
    # Owner commands
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Error handler
    # --------------------------------------------------------

    application.add_error_handler(
        error_handler
    )

    logger.info(
        "Mohammed Poster Zone is online."
    )

    # --------------------------------------------------------
    # Polling
    # --------------------------------------------------------

    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )

if __name__ == "__main__":
    main()
