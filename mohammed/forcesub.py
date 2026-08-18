# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

import logging
import time

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from config import OWNER_ID

# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger(
    "mohammed-force-sub"
)


# ============================================================
# CONFIG
# ============================================================

FSUB_CHANNEL = "@Aero_Unity"

FSUB_INVITE_LINK = "https://t.me/Aero_Unity"


# ============================================================
# PENDING REQUESTS
# ============================================================

PENDING_REQUESTS = {}

PENDING_TTL = 10 * 60


# ============================================================
# GROUP CHECK
# ============================================================

def is_group(update: Update) -> bool:

    if not update.effective_chat:
        return False

    return update.effective_chat.type in (
        "group",
        "supergroup",
    )


# ============================================================
# CLEANUP
# ============================================================

def cleanup_pending_requests():

    now = time.time()

    expired = []

    for user_id, data in list(
        PENDING_REQUESTS.items()
    ):

        created_at = data.get(
            "created_at",
            now,
        )

        if now - created_at > PENDING_TTL:

            expired.append(user_id)

    for user_id in expired:

        PENDING_REQUESTS.pop(
            user_id,
            None,
        )

        logger.info(
            "Expired pending request | user=%s",
            user_id,
        )


# ============================================================
# SAVE
# ============================================================

def save_pending_request(
    user_id: int,
    command: str,
    args: list,
    chat_id: int,
):

    cleanup_pending_requests()

    PENDING_REQUESTS[int(user_id)] = {

        "command": command,

        "args": list(args),

        "chat_id": int(chat_id),

        "created_at": time.time(),
    }

    logger.info(
        "Saved pending request | "
        "user=%s | command=%s | args=%s | chat=%s",
        user_id,
        command,
        args,
        chat_id,
    )


# ============================================================
# GET
# ============================================================

def get_pending_request(
    user_id: int,
):

    cleanup_pending_requests()

    return PENDING_REQUESTS.get(
        int(user_id)
    )


# ============================================================
# CLEAR
# ============================================================

def clear_pending_request(
    user_id: int,
):

    PENDING_REQUESTS.pop(
        int(user_id),
        None,
    )


# ============================================================
# MEMBER STATUS
# ============================================================

def member_is_joined(member) -> bool:

    status = str(
        member.status
    ).lower()

    # Telegram constants can be strings
    # such as member/administrator/creator.

    if status in (
        "creator",
        "administrator",
        "member",
    ):
        return True

    if status == "restricted":

        return bool(
            getattr(
                member,
                "is_member",
                False,
            )
        )

    return False


# ============================================================
# CHECK MEMBERSHIP
# ============================================================

async def check_membership(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
) -> bool:

    # --------------------------------------------------------
    # OWNER BYPASS
    # --------------------------------------------------------

    if int(user_id) == int(OWNER_ID):

        logger.info(
            "Force-sub owner bypass | user=%s",
            user_id,
        )

        return True

    try:

        member = await context.bot.get_chat_member(
            chat_id=FSUB_CHANNEL,
            user_id=int(user_id),
        )

        status = str(
            member.status
        ).lower()

        joined = member_is_joined(
            member
        )

        logger.info(
            "Force-sub check | "
            "user=%s | status=%s | joined=%s",
            user_id,
            status,
            joined,
        )

        return joined

    except Exception as e:

        logger.error(
            "Force-sub check failed | "
            "channel=%s | user=%s | error=%s",
            FSUB_CHANNEL,
            user_id,
            e,
        )

        return False


# ============================================================
# KEYBOARD
# ============================================================

def force_sub_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📢 Join Channel",
                    url=FSUB_INVITE_LINK,
                )
            ],
            [
                InlineKeyboardButton(
                    "🔄 Try Again",
                    callback_data="force_sub_check",
                )
            ],
        ]
    )


# ============================================================
# SEND FORCE SUB
# ============================================================

async def send_force_sub(
    update: Update,
):

    if not update.message:

        return

    await update.message.reply_text(

        "🔒 <b>Join Required</b>\n\n"

        "You must join our channel before "
        "using <b>Mohammed Poster Zone</b>.\n\n"

        f"📢 <b>Required Channel:</b>\n"
        f"{FSUB_CHANNEL}\n\n"

        "1️⃣ Tap <b>Join Channel</b>\n"
        "2️⃣ Join the channel\n"
        "3️⃣ Come back here\n"
        "4️⃣ Tap <b>Try Again</b>",

        parse_mode=ParseMode.HTML,

        reply_markup=force_sub_keyboard(),

        disable_web_page_preview=True,
    )


# ============================================================
# MAIN FORCE SUB
# ============================================================

async def force_sub(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> bool:

    # --------------------------------------------------------
    # ONLY GROUPS
    # --------------------------------------------------------

    if not is_group(update):

        return True

    # --------------------------------------------------------
    # USER
    # --------------------------------------------------------

    user = update.effective_user

    if not user:

        return True

    user_id = int(
        user.id
    )

    chat = update.effective_chat

    # --------------------------------------------------------
    # OWNER
    # --------------------------------------------------------

    if user_id == int(OWNER_ID):

        return True

    # --------------------------------------------------------
    # CHECK
    # --------------------------------------------------------

    joined = await check_membership(
        context,
        user_id,
    )

    if joined:

        return True

    # --------------------------------------------------------
    # SAVE COMMAND
    # --------------------------------------------------------

    command = ""
    args = []

    if update.message:

        text = (
            update.message.text
            or update.message.caption
            or ""
        ).strip()

        if text.startswith("/"):

            parts = text.split()

            command = (
                parts[0]
                .split("@")[0]
                .lstrip("/")
                .lower()
            )

            args = parts[1:]

    # --------------------------------------------------------
    # SAVE ONLY SUPPORTED COMMANDS
    # --------------------------------------------------------

    if command in (
        "poster",
        "ott",
    ):

        save_pending_request(

            user_id=user_id,

            command=command,

            args=args,

            chat_id=chat.id,
        )

    # --------------------------------------------------------
    # SEND MESSAGE
    # --------------------------------------------------------

    await send_force_sub(
        update
    )

    return False


# ============================================================
# TRY AGAIN CALLBACK
# ============================================================

async def force_sub_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:

        return

    user = query.from_user

    if not user:

        return

    user_id = int(
        user.id
    )

    # --------------------------------------------------------
    # CHECK MEMBERSHIP AGAIN
    # --------------------------------------------------------

    joined = await check_membership(
        context,
        user_id,
    )

    if not joined:

        await query.answer(

            "❌ You have not joined "
            "the channel yet.",

            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # GET PENDING
    # --------------------------------------------------------

    pending = get_pending_request(
        user_id
    )

    # --------------------------------------------------------
    # VERIFIED
    # --------------------------------------------------------

    await query.answer(
        "✅ Subscription verified!"
    )

    logger.info(
        "Force-sub verified | "
        "user=%s | pending=%s",
        user_id,
        pending,
    )

    # --------------------------------------------------------
    # DELETE FORCE-SUB MESSAGE
    # --------------------------------------------------------

    try:

        if query.message:

            await query.message.delete()

    except Exception as e:

        logger.warning(
            "Could not delete force-sub message: %s",
            e,
        )

    # --------------------------------------------------------
    # RETURN PENDING REQUEST
    # --------------------------------------------------------

    if not pending:

        logger.info(
            "No pending request | user=%s",
            user_id,
        )

        return

    clear_pending_request(
        user_id
    )

    # --------------------------------------------------------
    # STORE FOR MAIN CALLBACK
    # --------------------------------------------------------

    context.user_data[
        "force_sub_pending"
    ] = pending

    logger.info(
        "Pending request released | "
        "user=%s | command=%s | args=%s",
        user_id,
        pending["command"],
        pending["args"],
    )
