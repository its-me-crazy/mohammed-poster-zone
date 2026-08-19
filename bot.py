# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

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
    is_authorized_user,
    authorize_chat,
    unauthorize_chat,
    is_authorized_chat,
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
    get_pending_request,
)


# ------------------------- #
# Logging
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

logger = logging.getLogger(
    "mohammed-poster-zone"
)


# ------------------------- #
# Flask Web Server
# ------------------------- #

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


# ------------------------- #
# Helpers
# ------------------------- #

def is_group(update: Update):
    if not update.effective_chat:
        return False

    return update.effective_chat.type in (
        "group",
        "supergroup",
    )


def is_owner(update: Update):
    user = update.effective_user

    if not user:
        return False

    return user.id == OWNER_ID


# ------------------------- #
# Navigation Storage
# ------------------------- #

NAVIGATION = {}

NAVIGATION_TTL = 60 * 60


def cleanup_navigation():
    now = time.time()

    expired = []

    for key, value in list(NAVIGATION.items()):
        try:
            created_at = value.get(
                "created_at",
                now,
            )

            if (
                now - created_at
                > NAVIGATION_TTL
            ):
                expired.append(key)

        except Exception:
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


# ------------------------- #
# Execute Pending Force-Sub
# ------------------------- #

async def handle_force_sub_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    try:
        pending = await force_sub_callback(
            update,
            context,
        )
    except Exception:
        logger.exception(
            "Force-sub callback failed"
        )
        return

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
    ).lower()

    args = pending.get(
        "args",
        [],
    )

    if not isinstance(args, list):
        args = [str(args)]

    logger.info(
        "Executing pending command after "
        "force-sub verification | "
        "user=%s | command=%s | args=%s",
        user.id,
        command,
        args,
    )

    # ------------------------- #
    # Pending /poster
    # ------------------------- #

    if command == "poster":

        if not args:
            await context.bot.send_message(
                chat_id=chat.id,
                text=(
                    "❌ Nᴏ ᴘᴏsᴛᴇʀ ᴛɪᴛʟᴇ ᴡᴀs sᴀᴠᴇᴅ."
                ),
            )
            return

        title = " ".join(
            args
        ).strip()

        processing = await context.bot.send_message(
            chat_id=chat.id,
            text=(
                "🔎 Sᴇᴀʀᴄʜɪɴɢ ғᴏʀ ᴀʀᴛᴡᴏʀᴋ..."
            ),
        )

        try:
            media = await asyncio.to_thread(
                search_media,
                title,
            )

            if not media:
                await processing.edit_text(
                    "Nᴏ Mᴀᴛᴄʜɪɴɢ 𝗠𝗼𝘃𝗶𝗲𝘀 ᴏʀ "
                    "𝗦𝗲𝗿𝗶𝗲𝘀 ᴏʀ 𝗔𝗻𝗶𝗺𝗲 ᴏʀ "
                    "𝗦𝗲𝗿𝗶𝗮𝗹 ᴏʀ 𝗗𝗿𝗮𝗺𝗮 ᴡᴀs ғᴏᴜɴᴅ"
                )
                return

            items = await asyncio.to_thread(
                build_navigation_items,
                media,
            )

            if not items:
                await processing.edit_text(
                    "‼️ Nᴏ Aʀᴛᴡᴏʀᴋ Wᴀs Fᴏᴜɴᴅ "
                    "Fᴏʀ Tʜɪs Tɪᴛʟᴇ.."
                )
                return

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
                await processing.edit_text(
                    "❌ Failed to create thumbnail."
                )
                return

            thumbnail.seek(0)

            sent = await context.bot.send_photo(
                chat_id=chat.id,
                photo=thumbnail,
                caption=build_caption(
                    media,
                    "Unknown platform",
                    first,
                ),
                parse_mode=ParseMode.HTML,
            )

            try:
                await processing.delete()
            except Exception:
                pass

            cleanup_navigation()

            key = (
                chat.id,
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
                    "⚠️ 𝗔𝗻 𝗲𝗿𝗿𝗼𝗿 𝗼𝗰𝗰𝘂𝗿𝗿𝗲𝗱 𝘄𝗵𝗶𝗹𝗲 "
                    "𝘀𝗲𝗮𝗿𝗰𝗵𝗶𝗻𝗴. 𝗣𝗹𝗲𝗮𝘀𝗲 𝘁𝗿𝘆 𝗮𝗴𝗮𝗶𝗻"
                )
            except Exception:
                pass

        return

    # ------------------------- #
    # Pending /ott
    # ------------------------- #

    if command == "ott":

        if not args:
            await context.bot.send_message(
                chat_id=chat.id,
                text=(
                    "❌ Nᴏ 𝗢𝗧𝗧 URL Wᴀs Sᴀᴠᴇᴅ."
                ),
            )
            return

        url = str(
            args[0]
        ).strip()

        if not (
            url.startswith("http://")
            or url.startswith("https://")
        ):
            await context.bot.send_message(
                chat_id=chat.id,
                text="‼️ Iɴᴠᴀʟɪᴅ 𝗢𝗧𝗧 URL..",
            )
            return

        platform = detect_platform(
            url
        )

        processing = await context.bot.send_message(
            chat_id=chat.id,
            text=(
                "🌐 Rᴇᴀᴅɪɴɢ Tʜᴇ 𝗢𝗧𝗧 Pᴀɢᴇ..."
            ),
        )

        try:
            title = await asyncio.to_thread(
                extract_title_from_url,
                url,
            )

            if not title:
                await processing.edit_text(
                    "❌ I ᴄᴏᴜʟᴅɴ'ᴛ ᴇxᴛʀᴀᴄᴛ ᴀ "
                    "ᴛɪᴛʟᴇ ғʀᴏᴍ ᴛʜɪs ᴘᴀɢᴇ."
                )
                return

            media = await asyncio.to_thread(
                search_media,
                title,
            )

            if not media:
                await processing.edit_text(
                    "❌ I ᴄᴏᴜʟᴅɴ'ᴛ ғɪɴᴅ ᴍᴀᴛᴄʜɪɴɢ "
                    "ᴀʀᴛᴡᴏʀᴋ ғᴏʀ ᴛʜɪs ᴛɪᴛʟᴇ.."
                )
                return

            items = await asyncio.to_thread(
                build_navigation_items,
                media,
            )

            if not items:
                await processing.edit_text(
                    "🔎 ɴᴏ ᴀʀᴛᴡᴏʀᴋ ᴡᴀs ғᴏᴜɴᴅ"
                )
                return

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
                await processing.edit_text(
                    "❌ Failed to create thumbnail."
                )
                return

            thumbnail.seek(0)

            sent = await context.bot.send_photo(
                chat_id=chat.id,
                photo=thumbnail,
                caption=build_caption(
                    media,
                    platform,
                    first,
                ),
                parse_mode=ParseMode.HTML,
            )

            try:
                await processing.delete()
            except Exception:
                pass

            cleanup_navigation()

            key = (
                chat.id,
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

            try:
                await processing.edit_text(
                    "⚠️ ᴛʜᴇ 𝗢𝗧𝗧 ᴘᴀɢᴇ ᴄᴏᴜʟᴅ ɴᴏᴛ ʙᴇ "
                    "ᴘʀᴏᴄᴇssᴇᴅ.."
                )
            except Exception:
                pass

        return


# ------------------------- #
# /start
# ------------------------- #

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
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
            "Failed to save start user/chat"
        )

    # ------------------------- #
    # Private
    # ------------------------- #

    if chat.type == "private":

        if await is_banned(user.id):
            await update.message.reply_text(
                "🚫 <b>Yᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ ғʀᴏᴍ "
                "ᴜsɪɴɢ ᴛʜɪs ʙᴏᴛ..</b>\n"
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
            "Please Use This Bot In Our Poster Group.",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )

        return

    # ------------------------- #
    # Group
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
# /help
# ------------------------- #

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
# /about
# ------------------------- #

async def about_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_group(update):
        return

    await update.message.reply_text(
        "⍟───[ MY ᴅᴇᴛᴀɪʟꜱ ]───⍟\n\n"
        "‣ ᴍʏ ɴᴀᴍᴇ : "
        "[ᴍᴏʜᴀᴍᴍᴇᴅ ᴘᴏsᴛᴇʀ ᴢᴏɴᴇ]"
        "(https://t.me/Mohammed_Poster_bot)\n"
        "‣ ᴅᴇᴠᴇʟᴏᴘᴇʀ : "
        "[ᴍᴏʜᴀᴍᴍᴇᴅ]"
        "(https://t.me/Mr_Mohammed_29)\n"
        "‣ ʟɪʙʀᴀʀʏ : "
        "[ᴘʏᴛʜᴏɴ-ᴛᴇʟᴇɢʀᴀᴍ-ʙᴏᴛ]"
        "(https://pypi.org/project/"
        "python-telegram-bot/)\n"
        "‣ ʟᴀɴɢᴜᴀɢᴇ : "
        "[ᴘʏᴛʜᴏɴ 𝟹]"
        "(https://www.python.org/downloads/)\n"
        "‣ ᴅᴀᴛᴀ ʙᴀsᴇ : "
        "[ᴍᴏɴɢᴏ ᴅʙ]"
        "(https://www.mongodb.com/)\n"
        "‣ ʙᴏᴛ sᴇʀᴠᴇʀ : "
        "[ʙᴏᴛ sᴇʀᴠᴇʀ]"
        "(https://render.com)\n"
        "‣ ᴜᴘᴅᴀᴛᴇs : "
        "[Aᴇʀᴏ Uɴɪᴛʏ]"
        "(https://t.me/Aero_Unity)\n"
        "‣ ʙᴜɪʟᴅ sᴛᴀᴛᴜs : "
        "ᴠ3.𝟶 [sᴛᴀʙʟᴇ]"
        "(https://t.me/Aero_Unity)",
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )


# ------------------------- #
# /platforms
# ------------------------- #

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
# Send Poster Result
# ------------------------- #

async def send_poster_result(
    update: Update,
    media: dict,
    platform: str,
):
    if not update.message:
        return

    items = await asyncio.to_thread(
        build_navigation_items,
        media,
    )

    if not items:
        await update.message.reply_text(
            "❌ <b>ɴᴏ ᴀʀᴛᴡᴏʀᴋ ᴡᴀs ғᴏᴜɴᴅ "
            "ғᴏʀ ᴛʜɪs ᴛɪᴛʟᴇ.</b>",
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
            platform or "Unknown platform",
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
        "platform": platform or "Unknown platform",
        "created_at": time.time(),
    }

    keyboard = make_navigation_buttons(
        key,
        0,
        len(items),
    )

    if keyboard:
        await sent.edit_reply_markup(
            reply_markup=keyboard,
        )


# ------------------------- #
# /poster
# ------------------------- #

async def poster_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_group(update):
        return

    if await is_banned(
        update.effective_user.id
    ):
        await update.message.reply_text(
            "🚫 You are banned from using this bot."
        )
        return

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
                "‼️ Nᴏ Mᴀᴛᴄʜɪɴɢ 𝗠𝗼𝘃𝗶𝗲𝘀 ᴏʀ "
                "𝗦𝗲𝗿𝗶𝗲𝘀 ᴏʀ 𝗔𝗻𝗶𝗺ᴇ ᴏʀ "
                "𝗦𝗲𝗿𝗶𝗮𝗹 ᴏʀ 𝗗𝗿ᴀᴍᴀ ᴡᴀs ғᴏᴜɴᴅ"
            )
            return

        try:
            await processing.delete()
        except Exception:
            pass

        await send_poster_result(
            update,
            media,
            "Unknown platform",
        )

    except Exception:
        logger.exception(
            "Poster search failed"
        )

        try:
            await processing.edit_text(
                "⚠️ 𝗔𝗻 𝗲𝗿𝗿𝗼𝗿 ᴏᴄᴄᴜʀʀᴇᴅ 𝘄𝗵𝗶𝗹𝗲 "
                "𝘀𝗲𝗮𝗿𝗰𝗵𝗶𝗻𝗴. 𝗣𝗹𝗲𝗮𝘀𝗲 𝘁𝗿𝘆 𝗮𝗴𝗮𝗶𝗻"
            )
        except Exception:
            pass


# ------------------------- #
# /ott
# ------------------------- #

async def ott_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_group(update):
        return

    if await is_banned(
        update.effective_user.id
    ):
        await update.message.reply_text(
            "🚫 You are banned from using this bot."
        )
        return

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

        try:
            await processing.delete()
        except Exception:
            pass

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
# Back / Next
# ------------------------- #

async def navigation_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if not query:
        return

    try:
        parts = query.data.split(":")

        if len(parts) != 4:
            await query.answer()
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

        else:
            await query.answer()
            return

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

        title = (
            data["media"].get("title")
            or data["media"].get("name")
            or data["media"].get("original_title")
            or data["media"].get("original_name")
            or "Unknown"
        )

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
            data["media"],
            data["platform"],
            item,
        )

        media = InputMediaPhoto(
            media=thumbnail,
            caption=caption,
            parse_mode=ParseMode.HTML,
        )

        keyboard = make_navigation_buttons(
            key,
            index,
            len(data["items"]),
        )

        try:
            await query.message.edit_media(
                media=media,
                reply_markup=keyboard,
            )

            await query.answer()

        except Exception:
            logger.exception(
                "Telegram edit_media failed"
            )

            await query.answer(
                "❌ Telegram could not update this artwork.",
                show_alert=True,
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


# ------------------------- #
# Error Handler
# ------------------------- #

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
# /stats
# ------------------------- #

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
# /broadcast
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
                from_chat_id=source_message.chat_id,
                message_id=source_message.message_id,
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
# /authuser
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
# /unauthuser
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
# /authchat
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
# /unauthchat
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
# /ban
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

    if user_id == OWNER_ID:
        await update.message.reply_text(
            "❌ You cannot ban the owner."
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
# /unban
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


# ------------------------- #
# Main
# ------------------------- #

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

    group_filter = filters.ChatType.GROUPS

    # ------------------------- #
    # User Commands
    # ------------------------- #

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

    # ------------------------- #
    # Navigation
    # ------------------------- #

    application.add_handler(
        CallbackQueryHandler(
            navigation_callback,
            pattern=r"^poster_(prev|next):",
        )
    )

    # ------------------------- #
    # Force Subscribe
    # ------------------------- #

    application.add_handler(
        CallbackQueryHandler(
            handle_force_sub_callback,
            pattern=r"^force_sub_check$",
        )
    )

    # ------------------------- #
    # Owner Commands
    # ------------------------- #

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

    # ------------------------- #
    # Error Handler
    # ------------------------- #

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
# Entry Point
# ------------------------- #

if __name__ == "__main__":
    main()


# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #
