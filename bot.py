# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

import asyncio
import logging
import threading
import time

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
                "⬅️ Back",
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
                "Next ➡️",
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

# --------------------------------------------------
# /start
# --------------------------------------------------

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_group(update):
        return

    await update.message.reply_text(
        "🎬 <b>Mohammed Poster Zone</b>\n\n"
        "Your movie, series, drama, anime, "
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
        "❓ <b>Mohammed Poster Zone Help</b>\n\n"
        "<b>Search by title:</b>\n"
        "<code>/poster Reacher</code>\n\n"
        "<b>Search by OTT URL:</b>\n"
        "<code>/ott https://example.com/...</code>\n\n"
        "<b>Supported platforms:</b>\n"
        "<code>/platforms</code>\n\n"
        "<b>Artwork navigation:</b>\n"
        "⬅️ Back\n"
        "Next ➡️\n\n"
        "The bot works only in groups and "
        "supergroups.",
        parse_mode=ParseMode.HTML,
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
        "ℹ️ <b>Mohammed Poster Zone</b>\n\n"
        "Searches movie and TV metadata and "
        "available artwork through TMDB.\n\n"
        "Supports movies, TV series, dramas, "
        "anime, cartoons and serials when "
        "matching metadata is available.\n\n"
        "This bot is not affiliated with "
        "Netflix, Prime Video, Disney+, Hulu "
        "or the other listed platforms.\n\n"
        "TMDB API is used for metadata and "
        "artwork.",
        parse_mode=ParseMode.HTML,
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
        "🌐 <b>SUPPORTED PLATFORMS</b>\n\n"
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
            "❌ No artwork was found for "
            "this title."
        )
        return

    cleanup_navigation()

    first = items[0]

    sent = await update.message.reply_photo(
        photo=first["url"],
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

    if not context.args:
        await update.message.reply_text(
            "❌ Enter a title.\n\n"
            "Example:\n"
            "<code>/poster Reacher</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    title = " ".join(
        context.args
    ).strip()

    processing = await update.message.reply_text(
        "🔎 Searching for artwork..."
    )

    try:
        media = await asyncio.to_thread(
            search_media,
            title,
        )

        if not media:
            await processing.edit_text(
                "❌ No matching movie or series "
                "was found."
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
                "⚠️ An error occurred while "
                "searching. Please try again."
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
                "⚠️ The OTT page could not be "
                "processed."
            )
        except Exception:
            pass

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

    await query.answer()

    try:
        parts = query.data.split(":")

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

        # Only the person who requested
        # the poster can control buttons.
        if query.from_user.id != user_id:
            await query.answer(
                "These buttons belong to "
                "another user.",
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

        keyboard = make_navigation_buttons(
            key,
            index,
            len(data["items"]),
        )

        media = InputMediaPhoto(
            media=item["url"],
            caption=build_caption(
                data["media"],
                data["platform"],
                item,
            ),
            parse_mode=ParseMode.HTML,
        )

        await query.message.edit_media(
            media=media,
            reply_markup=keyboard,
        )

    except Exception:
        logger.exception(
            "Navigation callback failed"
        )

        try:
            await query.answer(
                "Unable to change artwork.",
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

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #
# --------------------------------------------------
# Main
# --------------------------------------------------

def main():

    logger.info(
        "Starting %s...",
        BOT_NAME,
    )

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
            filters=group_filter,
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

    application.add_error_handler(
        error_handler
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
