# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

import logging

from motor.motor_asyncio import (
    AsyncIOMotorClient,
)

from config import (
    MONGO_URI,
    MONGO_DB,
)

# ------------------------- #

logger = logging.getLogger(
    "mohammed-poster-database"
)

# ------------------------- #

client = None
db = None

users = None
chats = None
authorized_users = None
authorized_chats = None
banned_users = None

# ------------------------- #


def init_database():

    global client
    global db
    global users
    global chats
    global authorized_users
    global authorized_chats
    global banned_users

    if not MONGO_URI:

        raise RuntimeError(
            "MONGO_URI is missing."
        )

    client = AsyncIOMotorClient(
        MONGO_URI
    )

    db = client[MONGO_DB]

    users = db["users"]

    chats = db["chats"]

    authorized_users = db[
        "authorized_users"
    ]

    authorized_chats = db[
        "authorized_chats"
    ]

    banned_users = db[
        "banned_users"
    ]

    logger.info(
        "MongoDB initialized: %s",
        MONGO_DB,
    )


# ------------------------- #
# Users
# ------------------------- #


async def save_user(user):

    if not user:
        return

    await users.update_one(
        {
            "_id": user.id,
        },
        {
            "$set": {
                "user_id": user.id,
                "first_name": (
                    user.first_name
                    or ""
                ),
                "last_name": (
                    user.last_name
                    or ""
                ),
                "username": (
                    user.username
                    or ""
                ),
            },
            "$setOnInsert": {
                "started": True,
            },
        },
        upsert=True,
    )


# ------------------------- #
# Chats
# ------------------------- #


async def save_chat(chat):

    if not chat:
        return

    await chats.update_one(
        {
            "_id": chat.id,
        },
        {
            "$set": {
                "chat_id": chat.id,
                "title": (
                    getattr(
                        chat,
                        "title",
                        "",
                    )
                    or ""
                ),
                "type": str(
                    chat.type
                ),
            }
        },
        upsert=True,
    )


# ------------------------- #
# Statistics
# ------------------------- #


async def get_user_count():

    return await users.count_documents({})


async def get_chat_count():

    return await chats.count_documents({})


# ------------------------- #
# Authorization
# ------------------------- #


async def authorize_user(
    user_id: int,
):

    await authorized_users.update_one(
        {
            "_id": user_id,
        },
        {
            "$set": {
                "user_id": user_id,
            }
        },
        upsert=True,
    )


async def unauthorize_user(
    user_id: int,
):

    await authorized_users.delete_one(
        {
            "_id": user_id,
        }
    )


async def is_authorized_user(
    user_id: int,
):

    result = await authorized_users.find_one(
        {
            "_id": user_id,
        }
    )

    return result is not None


# ------------------------- #


async def authorize_chat(
    chat_id: int,
):

    await authorized_chats.update_one(
        {
            "_id": chat_id,
        },
        {
            "$set": {
                "chat_id": chat_id,
            }
        },
        upsert=True,
    )


async def unauthorize_chat(
    chat_id: int,
):

    await authorized_chats.delete_one(
        {
            "_id": chat_id,
        }
    )


async def is_authorized_chat(
    chat_id: int,
):

    result = await authorized_chats.find_one(
        {
            "_id": chat_id,
        }
    )

    return result is not None


# ------------------------- #
# Ban
# ------------------------- #


async def ban_user(
    user_id: int,
):

    await banned_users.update_one(
        {
            "_id": user_id,
        },
        {
            "$set": {
                "user_id": user_id,
            }
        },
        upsert=True,
    )


async def unban_user(
    user_id: int,
):

    await banned_users.delete_one(
        {
            "_id": user_id,
        }
    )


async def is_banned(
    user_id: int,
):

    result = await banned_users.find_one(
        {
            "_id": user_id,
        }
    )

    return result is not None


# ------------------------- #
# Broadcast users
# ------------------------- #


async def get_all_user_ids():

    cursor = users.find(
        {},
        {
            "_id": 1,
        },
    )

    result = []

    async for item in cursor:

        result.append(
            item["_id"]
        )

    return result
