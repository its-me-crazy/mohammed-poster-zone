# ============================================================
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ============================================================
# bot.py
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

from telegram.constants import ParseMode

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

app = Flask(__name__)


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

def is_group(update):

    if not update.effective_chat:
        return False

    return update.effective_chat.type in (
        "group",
        "supergroup",
    )


def is_owner(update):

    user = update.effective_user

    if not user:
        return False

    return user.id == OWNER_ID


# ============================================================
# NAVIGATION
# ============================================================

NAVIGATION = {}

NAVIGATION_TTL = 60 * 60


def cleanup_navigation():

    now = time.time()

    expired = []

    for key, value in list(
        NAVIGATION.items()
    ):

        if (
            now
            - value.get(
                "created_at",
                now,
            )
            > NAVIGATION_TTL
        ):

            expired.append(key)

    for key in expired:

        NAVIGATION.pop(
            key,
            None,
        )


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
# SEND POSTER
# ============================================================

async def send_poster_result(
    update,
    media,
    platform=None,
):

    items = await asyncio.to_thread(
        build_navigation_items,
        media,
    )

    if not items:

        await update.message.reply_text(
            "❌ <b>No artwork was found "
            "for this title.</b>",
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

    thumbnail.seek(0)

    sent = await update.message.reply_photo(
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


# ============================================================
# START
# ============================================================

async def start_command(
    update,
    context,
):

    user = update.effective_user
    chat = update.effective_chat

    if not user or not chat:
        return

    try:

        await save_user(user)
        await save_chat(chat)

    except Exception:

        logger.exception(
            "Failed to save user/chat"
        )

    if chat.type == "private":

        if await is_banned(
            user.id
        ):

            await update.message.reply_text(
                "🚫 <b>You are banned from "
                "using this bot.</b>\n\n"
                "Contact @Mr_Mohammed_29",
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
            "🎬 <b>Mohammed Poster Zone</b>\n\n"
            "Welcome to Mohammed Poster bot! 👋\n\n"
            "Please use this bot in our poster group.",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )

        return

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
            "Use Back and Next to browse "
            "available artwork.",
            parse_mode=ParseMode.HTML,
        )


# ============================================================
# HELP
# ============================================================

async def help_command(
    update,
    context,
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
        "┃ 🖼 <b>Artwork</b>\n"
        "┃ Poster / Cover / Portrait\n"
        "┃\n"
        "┃ ⬅️ <b>Back</b> / <b>Next</b> ➡️\n"
        "┃ Browse available artwork\n"
        "┃\n"
        "┃ ℹ️ <b>About Bot</b>\n"
        "┃ <code>/about</code>\n"
        "┃\n"
        "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"
        "⚡ <i>Powered by @Aero_Unity</i>",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


# ============================================================
# ABOUT
# ============================================================

async def about_command(
    update,
    context,
):

    if not is_group(update):
        return

    await update.message.reply_text(
        "⍟───[ MY ᴅᴇᴛᴀɪʟꜱ ]───⍟\n\n"
        "‣ ᴍʏ ɴᴀᴍᴇ : "
        "[Mohammed Poster Zone]"
        "(https://t.me/Mohammed_Poster_bot)\n"
        "‣ ᴅᴇᴠᴇʟᴏᴘᴇʀ : "
        "[Mohammed]"
        "(https://t.me/Mr_Mohammed_29)\n"
        "‣ ʟɪʙʀᴀʀʏ : "
        "[python-telegram-bot]"
        "(https://pypi.org/project/python-telegram-bot/)\n"
        "‣ ʟᴀɴɢᴜᴀɢᴇ : "
        "[Python 3]"
        "(https://www.python.org/downloads/)\n"
        "‣ ᴅᴀᴛᴀʙᴀsᴇ : "
        "[MongoDB]"
        "(https://www.mongodb.com/)\n"
        "‣ ʙᴏᴛ sᴇʀᴠᴇʀ : "
        "[Render]"
        "(https://render.com)\n"
        "‣ ᴜᴘᴅᴀᴛᴇs : "
        "[Aero Unity]"
        "(https://t.me/Aero_Unity)\n"
        "‣ ʙᴜɪʟᴅ sᴛᴀᴛᴜs : "
        "v3.0 [stable]"
        "(https://t.me/Aero_Unity)",
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )


# ============================================================
# PLATFORMS
# ============================================================

async def platforms_command(
    update,
    context,
):

    if not is_group(update):
        return

    await update.message.reply_text(
        "🌐 <b>Supported Platforms</b>\n\n"
        + get_platforms_text(),
        parse_mode=ParseMode.HTML,
    )


# ============================================================
# POSTER
# ============================================================

async def poster_command(
    update,
    context,
):

    if not is_group(update):
        return

    if not await force_sub(
        update,
        context,
    ):
        return

    if not context.args:

        await update.message.reply_text(
            "🔎 <b>Enter a title.</b>\n\n"
            "Example:\n"
            "<code>/poster Iron Man</code>",
            parse_mode=ParseMode.HTML,
        )

        return

    title = " ".join(
        context.args
    ).strip()

    processing = (
        await update.message.reply_text(
            "🔎 Searching for artwork..."
        )
    )

    try:

        media = await asyncio.to_thread(
            search_media,
            title,
        )

        if not media:

            await processing.edit_text(
                "❌ No matching movie, series, "
                "anime, serial or drama was found."
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
                "⚠️ An error occurred while "
                "searching. Please try again."
            )

        except Exception:
            pass


# ============================================================
# OTT
# ============================================================

async def ott_command(
    update,
    context,
):

    if not is_group(update):
        return

    if not await force_sub(
        update,
        context,
    ):
        return

    if not context.args:

        await update.message.reply_text(
            "❌ <b>Enter an OTT URL.</b>\n\n"
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

    processing = (
        await update.message.reply_text(
            "🌐 Reading the OTT page..."
        )
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
                "Try:\n"
                "<code>/poster Movie Name</code>",
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
                "❌ I couldn't find matching "
                "artwork for:\n\n"
                f"{html.escape(title)}",
                parse_mode=ParseMode.HTML,
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
                "⚠️ The OTT page could not "
                "be processed."
            )

        except Exception:
            pass


# ============================================================
# NAVIGATION
# ============================================================

async def navigation_callback(
    update,
    context,
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

        if (
            query.from_user.id
            != user_id
        ):

            await query.answer(
                "These buttons belong "
                "to another user.",
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

        media_data = data["media"]

        title = (
            media_data.get("title")
            or media_data.get("name")
            or media_data.get("original_title")
            or media_data.get("original_name")
            or "Unknown"
        )

        season = item.get(
            "season"
        )

        if season:

            season_name = season.get(
                "name",
                "",
            )

            if season_name:

                title = (
                    f"{title} {season_name}"
                )

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

        thumbnail.seek(0)

        caption = build_caption(
            media_data,
            data["platform"],
            item,
        )

        media = InputMediaPhoto(
            media=thumbnail,
            caption=caption,
            parse_mode=ParseMode.HTML,
        )

        keyboard = (
            make_navigation_buttons(
                key,
                index,
                len(
                    data["items"]
                ),
            )
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
                "❌ Unable to change artwork.",
                show_alert=True,
            )

        except Exception:
            pass


# ============================================================
# FORCE SUB CALLBACK
# ============================================================

async def handle_force_sub_callback(
    update,
    context,
):

    pending = await force_sub_callback(
        update,
        context,
    )

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

    if command == "poster":

        if not args:

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ No poster title was saved.",
            )

            return

        title = " ".join(
            args
        ).strip()

        processing = (
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="🔎 Searching for artwork...",
            )
        )

        try:

            media = await asyncio.to_thread(
                search_media,
                title,
            )

            if not media:

                await processing.edit_text(
                    "❌ No matching movie, series, "
                    "anime, serial or drama was found."
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
                    text="❌ No artwork was found.",
                )

                return

            cleanup_navigation()

            first = items[0]

            main_title = (
                media.get("title")
                or media.get("name")
                or media.get("original_title")
                or media.get("original_name")
                or "Unknown"
            )

            thumbnail = await asyncio.to_thread(
                create_thumbnail,
                first["url"],
                main_title,
            )

            if not thumbnail:

                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Failed to create thumbnail.",
                )

                return

            thumbnail.seek(0)

            sent = await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=thumbnail,
                caption=build_caption(
                    media,
                    None,
                    first,
                ),
                parse_mode=ParseMode.HTML,
            )

            key = (
                update.effective_chat.id,
                user.id,
                sent.message_id,
            )

            NAVIGATION[key] = {
                "items": items,
                "index": 0,
                "media": media,
                "platform": None,
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

        return

    if command == "ott":

        if not args:

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ No OTT URL was saved.",
            )

            return

        url = args[0].strip()

        if not (
            url.startswith("http://")
            or url.startswith("https://")
        ):

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Invalid OTT URL.",
            )

            return

        platform = detect_platform(
            url
        )

        processing = (
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="🌐 Reading the OTT page...",
            )
        )

        try:

            title = await asyncio.to_thread(
                extract_title_from_url,
                url,
            )

            if not title:

                await processing.edit_text(
                    "❌ I couldn't extract a title."
                )

                return

            media = await asyncio.to_thread(
                search_media,
                title,
            )

            if not media:

                await processing.edit_text(
                    "❌ Matching artwork was not found."
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
                    text="❌ No artwork was found.",
                )

                return

            cleanup_navigation()

            first = items[0]

            main_title = (
                media.get("title")
                or media.get("name")
                or media.get("original_title")
                or media.get("original_name")
                or "Unknown"
            )

            thumbnail = await asyncio.to_thread(
                create_thumbnail,
                first["url"],
                main_title,
            )

            if not thumbnail:

                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Failed to create thumbnail.",
                )

                return

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
                "Pending OTT execution failed"
            )

        return


# ============================================================
# ERROR
# ============================================================

async def error_handler(
    update,
    context,
):

    logger.error(
        "Telegram error: %s",
        context.error,
        exc_info=context.error,
    )


# ============================================================
# STATS
# ============================================================

async def stats_command(
    update,
    context,
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


# ============================================================
# BROADCAST
# ============================================================

async def broadcast_command(
    update,
    context,
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

    processing = (
        await update.message.reply_text(
            "📢 <b>Broadcast started...</b>\n\n"
            f"👤 Users: <code>{len(users)}</code>",
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


# ============================================================
# AUTH USER
# ============================================================

async def authuser_command(
    update,
    context,
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


# ============================================================
# UNAUTH USER
# ============================================================

async def unauthuser_command(
    update,
    context,
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


# ============================================================
# AUTH CHAT
# ============================================================

async def authchat_command(
    update,
    context,
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


# ============================================================
# UNAUTH CHAT
# ============================================================

async def unauthchat_command(
    update,
    context,
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


# ============================================================
# BAN
# ============================================================

async def ban_command(
    update,
    context,
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


# ============================================================
# UNBAN
# ============================================================

async def unban_command(
    update,
    context,
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


# ============================================================
# MAIN
# ============================================================

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

    # ========================================================
    # BASIC
    # ========================================================

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

    # ========================================================
    # POSTER
    # ========================================================

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

    # ========================================================
    # NAVIGATION
    # ========================================================

    application.add_handler(
        CallbackQueryHandler(
            navigation_callback,
            pattern=r"^poster_(prev|next):",
        )
    )

    # ========================================================
    # FORCE SUB
    # ========================================================

    application.add_handler(
        CallbackQueryHandler(
            handle_force_sub_callback,
            pattern=r"^force_sub_check$",
        )
    )

    # ========================================================
    # ADMIN
    # ========================================================

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


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
