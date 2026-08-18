# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

import asyncio
import logging
import time
from typing import Optional

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

from pyrogram import Client
from pyrogram.errors import (
    ChatAdminRequired,
    ChatIdInvalid,
    ChannelInvalid,
    FloodWait,
    PeerIdInvalid,
    UserNotParticipant,
)

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

logger = logging.getLogger(__name__)

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

# ============================================================
# CONFIGURATION
# ============================================================

# Your force-sub channel username.
#
# Examples:
#
# FSUB_CHANNEL = "@Aero_Unity"
#
# or for a private channel:
#
# FSUB_CHANNEL = -1001234567890
#
FSUB_CHANNEL = "@Aero_Unity"


# Channel invite link.
#
# For a public channel:
# https://t.me/Anime_UpdatesAU
#
# For a private channel:
# https://t.me/+xxxxxxxxxxxx
#
FSUB_INVITE_LINK = "https://t.me/Aero_Unity"

# Replace this with your actual Telegram ID.
#
OWNER_ID = 7284759394

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

# How long a successful membership check
# should remain cached.
# 300 = 5 minutes
CACHE_TIME = 300

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

# ============================================================
# CACHE
# ============================================================

_JOIN_CACHE = {}

_CACHE_LOCK = asyncio.Lock()

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

def _cache_key(
    user_id: int,
    chat_id: str,
):
    return (
        int(user_id),
        str(chat_id),
    )

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

async def _get_cached(
    user_id: int,
    chat_id: str,
):
    key = _cache_key(
        user_id,
        chat_id,
    )

    async with _CACHE_LOCK:

        item = _JOIN_CACHE.get(key)

        if not item:
            return None

        expires_at = item.get(
            "expires_at",
            0,
        )

        if time.time() >= expires_at:
            _JOIN_CACHE.pop(
                key,
                None,
            )
            return None

        return item.get(
            "joined",
            False,
        )

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

async def _set_cache(
    user_id: int,
    chat_id: str,
    joined: bool,
):
    key = _cache_key(
        user_id,
        chat_id,
    )

    async with _CACHE_LOCK:

        _JOIN_CACHE[key] = {
            "joined": bool(joined),
            "expires_at": (
                time.time()
                + CACHE_TIME
            ),
        }
      
# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

def clear_user_cache(
    user_id: int,
):
    """
    Remove all cached membership
    results for one user.
    """

    user_id = int(user_id)

    keys = [
        key
        for key in _JOIN_CACHE
        if key[0] == user_id
    ]

    for key in keys:
        _JOIN_CACHE.pop(
            key,
            None,
        )

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #
# ============================================================
# OWNER CHECK
# ============================================================

def is_owner(
    user_id: Optional[int],
) -> bool:

    if not user_id:
        return False

    return int(user_id) == int(
        OWNER_ID
    )
  
# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

# ============================================================
# CHANNEL NAME
# ============================================================

def get_channel_name():
    """
    Returns a display name for the
    force-sub channel.
    """

    if isinstance(
        FSUB_CHANNEL,
        str,
    ):
        if FSUB_CHANNEL.startswith("@"):
            return FSUB_CHANNEL

    return "our channel"

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #
# ============================================================
# CHECK MEMBERSHIP
# ============================================================

async def check_membership(
    app: Client,
    user_id: int,
) -> bool:
    """
    Check whether a Telegram user has
    joined the force-sub channel.

    Returns:
        True  -> joined
        False -> not joined / unavailable
    """

    # Owner bypass.
    if is_owner(user_id):
        return True

    cached = await _get_cached(
        user_id,
        str(FSUB_CHANNEL),
    )

    if cached is not None:
        return bool(cached)

    try:

        member = await app.get_chat_member(
            FSUB_CHANNEL,
            user_id,
        )

        status = getattr(
            member,
            "status",
            None,
        )

        status_name = str(
            status
        ).lower()

        # Telegram membership statuses:
        #
        # owner
        # administrator
        # member
        # restricted
        #
        # Left / kicked are not accepted.
        if status_name in (
            "owner",
            "administrator",
            "member",
            "restricted",
        ):
            await _set_cache(
                user_id,
                str(FSUB_CHANNEL),
                True,
            )

            return True

        await _set_cache(
            user_id,
            str(FSUB_CHANNEL),
            False,
        )

        return False

    except UserNotParticipant:

        await _set_cache(
            user_id,
            str(FSUB_CHANNEL),
            False,
        )

        return False

    except (
        ChatIdInvalid,
        ChannelInvalid,
        PeerIdInvalid,
    ):

        logger.exception(
            "Invalid force-sub channel: %s",
            FSUB_CHANNEL,
        )

        # Don't accidentally let users
        # through when force-sub itself
        # is incorrectly configured.
        return False

    except ChatAdminRequired:

        logger.error(
            "Bot must be an administrator "
            "in the force-sub channel."
        )

        return False

    except FloodWait as error:

        logger.warning(
            "FloodWait while checking "
            "force-sub: %s seconds",
            error.value,
        )

        return False

    except Exception:

        logger.exception(
            "Unexpected force-sub error."
        )

        return False

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #
# ============================================================
# FORCE-SUB BUTTONS
# ============================================================

def force_sub_buttons():
    """
    Creates:
      Join Channel
      Try Again
    """

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

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

# ============================================================
# FORCE-SUB MESSAGE
# ============================================================

def force_sub_text():
    channel = get_channel_name()

    return (
        "🔒 <b>Join Required</b>\n\n"
        "You must join our channel before "
        "using this bot.\n\n"
        f"📢 Channel: <b>{channel}</b>\n\n"
        "1️⃣ Tap <b>Join Channel</b>\n"
        "2️⃣ Join the channel\n"
        "3️⃣ Return here\n"
        "4️⃣ Tap <b>Try Again</b>"
    )
  
# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

# ============================================================
# SEND FORCE-SUB MESSAGE
# ============================================================

async def send_force_sub(
    message,
):
    """
    Send the force-sub message to
    the user.
    """

    return await message.reply_text(
        force_sub_text(),
        reply_markup=force_sub_buttons(),
        disable_web_page_preview=True,
    )
  
# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

# ============================================================
# MAIN FORCE-SUB FUNCTION
# ============================================================

async def force_sub(
    app: Client,
    message,
) -> bool:
    """
    Main function to use before a
    command that requires subscription.

    Example:

        if not await force_sub(
            app,
            message
        ):
            return

    Returns:
        True  -> user can continue
        False -> stop command
    """

    # Make sure we have a sender.
    if not message.from_user:
        return False

    user_id = message.from_user.id

    # Owner bypass.
    if is_owner(user_id):
        return True

    joined = await check_membership(
        app,
        user_id,
    )

    if joined:
        return True

    await send_force_sub(
        message
    )

    return False

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #
# ============================================================
# CALLBACK HANDLER
# ============================================================

async def force_sub_callback(
    client: Client,
    callback_query,
):
    """
    Handler for the "Try Again" button.
    """

    user = callback_query.from_user

    if not user:
        await callback_query.answer(
            "Unable to identify user.",
            show_alert=True,
        )
        return

    user_id = user.id

    # Owner bypass.
    if is_owner(user_id):

        await callback_query.answer(
            "✅ Verified!",
            show_alert=True,
        )

        try:
            await callback_query.message.delete()
        except Exception:
            pass

        return

    # Clear cached False result so
    # Telegram is checked again.
    clear_user_cache(
        user_id
    )

    joined = await check_membership(
        client,
        user_id,
    )

    if joined:

        await callback_query.answer(
            "✅ Subscription verified!",
            show_alert=True,
        )

        try:
            await callback_query.message.delete()
        except Exception:
            pass

        return

    await callback_query.answer(
        "❌ You haven't joined the channel yet.",
        show_alert=True,
    )

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #
# ============================================================
# REGISTER CALLBACK HANDLER
# ============================================================

def register_force_sub_handler(
    app: Client,
):
    """
    Register the Try Again callback.

    Call this once when creating your
    Pyrogram Client.
    """

    from pyrogram import filters

    app.add_callback_query_handler(
        force_sub_callback,
        filters.regex(
            r"^force_sub_check$"
        ),
  )

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #
