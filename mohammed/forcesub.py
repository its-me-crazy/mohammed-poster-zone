# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,
)

import logging


logger = logging.getLogger(
    "mohammed-force-sub"
)


# ============================================================
# FORCE SUB CONFIG
# ============================================================

# Your force-sub channel
FSUB_CHANNEL = "@Aero_Unity"

# Public channel:
# https://t.me/Anime_UpdatesAU
#
# Private channel:
# Put your private invite link here.
FSUB_INVITE_LINK = "https://t.me/Aero_Unity"

# Your Telegram user ID
OWNER_ID = 7284759394


# ============================================================
# CHECK GROUP
# ============================================================

def is_group(update: Update):

    if not update.effective_chat:
        return False

    return update.effective_chat.type in (
        "group",
        "supergroup",
    )


# ============================================================
# CHECK FORCE SUB
# ============================================================

async def check_membership(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
) -> bool:

    # Owner bypass
    if int(user_id) == int(OWNER_ID):
        return True

    try:

        member = await context.bot.get_chat_member(
            chat_id=FSUB_CHANNEL,
            user_id=user_id,
        )

        status = member.status

        if status in (
            "creator",
            "administrator",
            "member",
            "restricted",
        ):
            return True

        return False

    except Exception as e:

        logger.error(
            "Force-sub check failed: %s",
            e,
        )

        return False


# ============================================================
# FORCE SUB BUTTONS
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
# FORCE SUB MESSAGE
# ============================================================

async def send_force_sub(
    update: Update,
):

    if not update.message:
        return

    await update.message.reply_text(
        "🔒 <b>Join Required</b>\n\n"
        "You must join our channel before "
        "using Mohammed Poster Zone.\n\n"
        "📢 <b>Required Channel:</b>\n"
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

    # Only groups
    if not is_group(update):
        return False

    if not update.effective_user:
        return False

    user_id = update.effective_user.id

    # Owner bypass
    if int(user_id) == int(OWNER_ID):
        return True

    joined = await check_membership(
        context,
        user_id,
    )

    if joined:
        return True

    await send_force_sub(
        update,
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

    user_id = user.id

    # Only the person who pressed
    # the button gets checked.
    joined = await check_membership(
        context,
        user_id,
    )

    if joined:

        await query.answer(
            "✅ Subscription verified!",
            show_alert=True,
        )

        try:
            await query.message.delete()
        except Exception:
            pass

        return

    await query.answer(
        "❌ You have not joined the channel yet.",
        show_alert=True,
    )
