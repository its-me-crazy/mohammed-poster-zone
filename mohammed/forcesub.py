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

OWNER_ID = 7284759394


# ============================================================
# PENDING REQUEST STORAGE
# ============================================================

# Stores commands blocked by Force Subscribe.
#
# Example:
#
# user_id:
# {
#     "command": "poster",
#     "args": ["Reacher"],
#     "created_at": 123456789
# }
#
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
# CLEANUP PENDING REQUESTS
# ============================================================

def cleanup_pending_requests():

    now = time.time()

    expired = []

    for user_id, data in PENDING_REQUESTS.items():

        if (
            now - data["created_at"]
            > PENDING_TTL
        ):
            expired.append(user_id)

    for user_id in expired:
        PENDING_REQUESTS.pop(
            user_id,
            None,
        )


# ============================================================
# SAVE PENDING REQUEST
# ============================================================

def save_pending_request(
    user_id: int,
    command: str,
    args: list,
):

    cleanup_pending_requests()

    PENDING_REQUESTS[int(user_id)] = {
        "command": command,
        "args": list(args),
        "created_at": time.time(),
    }

    logger.info(
        "Saved pending request | "
        "user=%s | command=%s | args=%s",
        user_id,
        command,
        args,
    )


# ============================================================
# GET PENDING REQUEST
# ============================================================

def get_pending_request(
    user_id: int,
):

    cleanup_pending_requests()

    return PENDING_REQUESTS.get(
        int(user_id)
    )


# ============================================================
# CLEAR PENDING REQUEST
# ============================================================

def clear_pending_request(
    user_id: int,
):

    PENDING_REQUESTS.pop(
        int(user_id),
        None,
    )


# ============================================================
# MEMBER STATUS CHECK
# ============================================================

def member_is_joined(member) -> bool:

    status = member.status

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

        return True

    try:

        member = await context.bot.get_chat_member(
            chat_id=FSUB_CHANNEL,
            user_id=user_id,
        )

        joined = member_is_joined(
            member
        )

        logger.info(
            "Force-sub check | "
            "user=%s | status=%s | joined=%s",
            user_id,
            member.status,
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
    # USER CHECK
    # --------------------------------------------------------

    user = update.effective_user

    if not user:

        return True

    user_id = user.id

    # --------------------------------------------------------
    # OWNER BYPASS
    # --------------------------------------------------------

    if int(user_id) == int(OWNER_ID):

        return True

    # --------------------------------------------------------
    # CHECK MEMBERSHIP
    # --------------------------------------------------------

    joined = await check_membership(
        context,
        user_id,
    )

    if joined:

        # If already joined, remove
        # any old pending request.

        clear_pending_request(
            user_id
        )

        return True

    # --------------------------------------------------------
    # SAVE CURRENT COMMAND
    # --------------------------------------------------------

    command = ""

    args = []

    if update.message:

        if update.message.text:

            text = update.message.text.strip()

            if text.startswith("/"):

                parts = text.split()

                command = (
                    parts[0]
                    .split("@")[0]
                    .lstrip("/")
                    .lower()
                )

                args = parts[1:]

    if command:

        save_pending_request(
            user_id=user_id,
            command=command,
            args=args,
        )

    # --------------------------------------------------------
    # SEND FORCE SUB MESSAGE
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

        return False

    user = query.from_user

    if not user:

        return False

    user_id = user.id

    # --------------------------------------------------------
    # CHECK MEMBERSHIP
    # --------------------------------------------------------

    joined = await check_membership(
        context,
        user_id,
    )

    if not joined:

        await query.answer(
            "❌ You have not joined the channel yet.",
            show_alert=True,
        )

        return False

    # --------------------------------------------------------
    # GET PENDING REQUEST
    # --------------------------------------------------------

    pending = get_pending_request(
        user_id
    )

    # --------------------------------------------------------
    # VERIFIED
    # --------------------------------------------------------

    await query.answer(
        "✅ Subscription verified!",
        show_alert=True,
    )

    # --------------------------------------------------------
    # DELETE FORCE SUB MESSAGE
    # --------------------------------------------------------

    try:

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

        return None

    clear_pending_request(
        user_id
    )

    logger.info(
        "Force-sub verified | "
        "user=%s | pending=%s",
        user_id,
        pending,
    )

    return pending
