# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

import logging

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

logger = logging.getLogger("mohammed-force-sub")


# ============================================================
# FORCE SUB CONFIG
# ============================================================

# ------------------------------------------------------------
# IMPORTANT:
#
# You can use either:
#
# 1. Public username:
#    FSUB_CHANNEL = "@Aero_Unity"
#
# OR
#
# 2. Numeric Telegram channel ID:
#    FSUB_CHANNEL = -1001234567890
#
# Numeric channel ID is recommended.
# ------------------------------------------------------------

FSUB_CHANNEL = "-1004471112743"


# Button URL
#
# Public channel:
# https://t.me/Aero_Unity
#
# Private channel:
# Put the actual private invite link here.
#
FSUB_INVITE_LINK = "https://t.me/Aero_Unity"


# Your Telegram user ID
OWNER_ID = 7284759394


# ============================================================
# CHECK IF CHAT IS GROUP
# ============================================================

def is_group(update: Update) -> bool:

    chat = update.effective_chat

    if not chat:
        return False

    return chat.type in (
        "group",
        "supergroup",
    )


# ============================================================
# CHECK IF MEMBER IS ACTUALLY JOINED
# ============================================================

def member_is_joined(member) -> bool:
    """
    Check Telegram ChatMember status safely.

    Accepted:
        creator
        administrator
        member
        restricted (only when is_member=True)

    Rejected:
        left
        kicked
        anything unknown
    """

    status = member.status

    # Owner/admin/member
    if status in (
        "creator",
        "administrator",
        "member",
    ):
        return True

    # Restricted users can still be members.
    # We must check is_member.
    if status == "restricted":
        return bool(
            getattr(member, "is_member", False)
        )

    return False


# ============================================================
# CHECK FORCE SUB MEMBERSHIP
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
            "Force-sub bypass for owner: %s",
            user_id,
        )
        return True

    try:

        # ----------------------------------------------------
        # GET TELEGRAM MEMBER INFORMATION
        # ----------------------------------------------------

        member = await context.bot.get_chat_member(
            chat_id=FSUB_CHANNEL,
            user_id=user_id,
        )

        # ----------------------------------------------------
        # CHECK STATUS
        # ----------------------------------------------------

        joined = member_is_joined(member)

        logger.info(
            "Force-sub check | user=%s | status=%s | joined=%s",
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
# FORCE SUB KEYBOARD
# ============================================================

def force_sub_keyboard() -> InlineKeyboardMarkup:

    keyboard = [
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

    return InlineKeyboardMarkup(keyboard)


# ============================================================
# SEND FORCE SUB MESSAGE
# ============================================================

async def send_force_sub(
    update: Update,
) -> None:

    # --------------------------------------------------------
    # MESSAGE UPDATE
    # --------------------------------------------------------

    if update.message:

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
# MAIN FORCE SUB FUNCTION
# ============================================================

async def force_sub(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> bool:

    # --------------------------------------------------------
    # ONLY WORK IN GROUPS / SUPERGROUPS
    # --------------------------------------------------------

    if not is_group(update):
        return True

    # --------------------------------------------------------
    # CHECK USER
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
        context=context,
        user_id=user_id,
    )

    # --------------------------------------------------------
    # USER JOINED
    # --------------------------------------------------------

    if joined:
        return True

    # --------------------------------------------------------
    # USER NOT JOINED
    # --------------------------------------------------------

    await send_force_sub(update)

    return False


# ============================================================
# TRY AGAIN CALLBACK
# ============================================================

async def force_sub_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:

    query = update.callback_query

    if not query:
        return

    # --------------------------------------------------------
    # ANSWER CALLBACK IMMEDIATELY
    # --------------------------------------------------------

    try:
        await query.answer()
    except Exception:
        pass

    # --------------------------------------------------------
    # GET USER
    # --------------------------------------------------------

    user = query.from_user

    if not user:
        return

    user_id = user.id

    # --------------------------------------------------------
    # OWNER BYPASS
    # --------------------------------------------------------

    if int(user_id) == int(OWNER_ID):

        try:
            await query.answer(
                "✅ Subscription verified!",
                show_alert=True,
            )
        except Exception:
            pass

        try:
            await query.message.delete()
        except Exception:
            pass

        return

    # --------------------------------------------------------
    # CHECK MEMBERSHIP
    # --------------------------------------------------------

    joined = await check_membership(
        context=context,
        user_id=user_id,
    )

    # --------------------------------------------------------
    # JOINED
    # --------------------------------------------------------

    if joined:

        try:
            await query.answer(
                "✅ Subscription verified!",
                show_alert=True,
            )
        except Exception:
            pass

        # Delete force-sub message
        try:
            await query.message.delete()
        except Exception:
            pass

        return

    # --------------------------------------------------------
    # NOT JOINED
    # --------------------------------------------------------

    try:
        await query.answer(
            "❌ You have not joined the channel yet.",
            show_alert=True,
        )
    except Exception:
        pass


# ============================================================
# OPTIONAL: TEST FORCE SUB
# ============================================================

async def test_membership(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
) -> bool:

    """
    Optional helper.

    Can be used from another part of your bot
    if you want to test a user's subscription.
    """

    return await check_membership(
        context=context,
        user_id=user_id,
    )
