# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

import os


# ------------------------- #
# Bot
# ------------------------- #

BOT_TOKEN = os.getenv(
    "BOT_TOKEN",
    "",
).strip()


TMDB_API_KEY = os.getenv(
    "TMDB_API_KEY",
    "",
).strip()


# ------------------------- #
# MongoDB
# ------------------------- #

MONGO_URI = os.getenv(
    "MONGO_URI",
    "",
).strip()


MONGO_DB = os.getenv(
    "MONGO_DB",
    "mohammed_poster_zone",
).strip()


# ------------------------- #
# Owner
# ------------------------- #

OWNER_ID = int(
    os.getenv(
        "OWNER_ID",
        "7284759394",
    ).strip()
)


# ------------------------- #
# Updates
# ------------------------- #

UPDATES_URL = os.getenv(
    "UPDATES_URL",
    "https://t.me/Aero_Unity",
).strip()


# ------------------------- #
# Render Port
# ------------------------- #

PORT = int(
    os.getenv(
        "PORT",
        "10000",
    )
)


# ------------------------- #
# Bot Name
# ------------------------- #

BOT_NAME = os.getenv(
    "BOT_NAME",
    "Mohammed Poster Zone",
).strip()


# ------------------------- #
# TMDB Language
# ------------------------- #

TMDB_LANGUAGE = os.getenv(
    "TMDB_LANGUAGE",
    "en-US",
).strip()


# ------------------------- #
# Request Timeout
# ------------------------- #

REQUEST_TIMEOUT = int(
    os.getenv(
        "REQUEST_TIMEOUT",
        "20",
    )
)


# ------------------------- #
# Validation
# ------------------------- #

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN environment variable is missing."
    )


if not TMDB_API_KEY:
    raise RuntimeError(
        "TMDB_API_KEY environment variable is missing."
    )


# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #
