# ============================================================
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ============================================================
# poster.py
# ============================================================

import io
import re
import html
import logging
from urllib.parse import quote_plus, urlparse

import requests
from PIL import Image

from config import TMDB_API_KEY


logger = logging.getLogger(
    "mohammed-poster-zone.poster"
)


# ============================================================
# CONSTANTS
# ============================================================

TMDB_API_URL = "https://api.themoviedb.org/3"

TMDB_IMAGE_URL = (
    "https://image.tmdb.org/t/p/original"
)

# ============================================================
# IMPORTANT
#
# Final Telegram thumbnail = EXACTLY 5:4
#
# 1000 x 800 = 5:4
# ============================================================

THUMB_WIDTH = 1000
THUMB_HEIGHT = 800


# ============================================================
# HTTP SESSION
# ============================================================

SESSION = requests.Session()

SESSION.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/120 Safari/537.36"
        )
    }
)


# ============================================================
# TMDB REQUEST
# ============================================================

def tmdb_get(endpoint, params=None):

    if not TMDB_API_KEY:
        raise RuntimeError(
            "TMDB_API_KEY is missing."
        )

    params = dict(params or {})
    params["api_key"] = TMDB_API_KEY

    response = SESSION.get(
        f"{TMDB_API_URL}{endpoint}",
        params=params,
        timeout=20,
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# SEARCH MEDIA
# ============================================================

def search_media(query):

    query = str(query).strip()

    if not query:
        return None

    try:

        result = tmdb_get(
            "/search/multi",
            {
                "query": query,
                "language": "en-US",
                "include_adult": "false",
                "page": 1,
            },
        )

    except Exception:

        logger.exception(
            "TMDB search failed"
        )

        return None

    results = result.get(
        "results",
        [],
    )

    results = [
        item
        for item in results
        if item.get("media_type")
        in ("movie", "tv")
    ]

    if not results:
        return None

    results.sort(
        key=lambda item: (
            bool(item.get("poster_path")),
            bool(item.get("backdrop_path")),
            float(
                item.get(
                    "popularity",
                    0,
                )
                or 0
            ),
        ),
        reverse=True,
    )

    item = results[0]

    media_type = item.get(
        "media_type"
    )

    media = dict(item)

    media["media_type"] = media_type

    # ========================================================
    # FULL DETAILS
    # ========================================================

    try:

        details = tmdb_get(
            f"/{media_type}/{item['id']}",
            {
                "language": "en-US",
            },
        )

        media.update(details)

    except Exception:

        logger.warning(
            "Could not load TMDB details",
            exc_info=True,
        )

    # ========================================================
    # WATCH PROVIDERS
    # ========================================================

    try:

        providers = tmdb_get(
            f"/{media_type}/{item['id']}/watch/providers"
        )

        media["watch_providers"] = (
            providers.get(
                "results",
                {},
            )
        )

    except Exception:

        logger.warning(
            "Could not load watch providers",
            exc_info=True,
        )

        media["watch_providers"] = {}

    return media


# ============================================================
# EXTRACT TITLE FROM OTT URL
# ============================================================

def extract_title_from_url(url):

    try:

        response = SESSION.get(
            url,
            timeout=20,
        )

        response.raise_for_status()

        source = response.text

        patterns = [
            r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:title["\']',
            r'<meta[^>]+name=["\']twitter:title["\'][^>]+content=["\']([^"\']+)["\']',
            r"<title[^>]*>(.*?)</title>",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                source,
                re.IGNORECASE | re.DOTALL,
            )

            if not match:
                continue

            title = html.unescape(
                match.group(1)
            )

            title = re.sub(
                r"\s+",
                " ",
                title,
            ).strip()

            if not title:
                continue

            title = re.sub(
                r"\s*[\|\-–—]\s*"
                r"(Netflix|Prime Video|"
                r"Amazon Prime Video|"
                r"JioHotstar|Hotstar|"
                r"YouTube|"
                r"Google Play Movies|"
                r"Disney\+|"
                r"Apple TV\+?)\s*$",
                "",
                title,
                flags=re.IGNORECASE,
            ).strip()

            if title:
                return title

    except Exception:

        logger.exception(
            "Failed to extract title from URL"
        )

    # ========================================================
    # URL FALLBACK
    # ========================================================

    try:

        parsed = urlparse(url)

        path = parsed.path.strip("/")

        if path:

            last = path.split("/")[-1]

            last = re.sub(
                r"\.(html?|php)$",
                "",
                last,
                flags=re.IGNORECASE,
            )

            last = re.sub(
                r"[-_]+",
                " ",
                last,
            )

            last = re.sub(
                r"\s+",
                " ",
                last,
            ).strip()

            if last:
                return last.title()

    except Exception:
        pass

    return None


# ============================================================
# PLATFORM NORMALIZATION
# ============================================================

def normalize_platform_name(name):

    if not name:
        return None

    value = str(
        name
    ).lower().strip()

    mappings = {

        "amazon prime video":
            "Prime Video",

        "prime video":
            "Prime Video",

        "amazon":
            "Prime Video",

        "netflix":
            "Netflix",

        "jiohotstar":
            "JioHotstar",

        "hotstar":
            "JioHotstar",

        "youtube":
            "YouTube",

        "google play movies":
            "Google Play Movies",

        "google play":
            "Google Play Movies",

        "disney plus":
            "Disney+",

        "disney+":
            "Disney+",

        "apple tv":
            "Apple TV+",

        "apple tv+":
            "Apple TV+",

        "zee5":
            "ZEE5",

        "sonyliv":
            "SonyLIV",

        "aha":
            "aha",

        "mx player":
            "MX Player",

        "mubi":
            "MUBI",
    }

    return mappings.get(
        value,
        str(name),
    )


# ============================================================
# AVAILABLE PLATFORM
#
# IMPORTANT:
# This selects ONE platform only.
#
# Priority:
# Prime Video
# Netflix
# JioHotstar
# Disney+
# YouTube
# Google Play Movies
# etc.
# ============================================================

def get_available_platform(media):

    providers = media.get(
        "watch_providers",
        {},
    )

    if not isinstance(
        providers,
        dict,
    ):
        return None

    country_data = (
        providers.get("IN")
        or providers.get("US")
        or {}
    )

    if not isinstance(
        country_data,
        dict,
    ):
        return None

    groups = [
        country_data.get(
            "flatrate",
            [],
        ),
        country_data.get(
            "free",
            [],
        ),
        country_data.get(
            "ads",
            [],
        ),
        country_data.get(
            "rent",
            [],
        ),
        country_data.get(
            "buy",
            [],
        ),
    ]

    preferred = [
        "Prime Video",
        "Netflix",
        "JioHotstar",
        "Disney+",
        "YouTube",
        "Google Play Movies",
        "Apple TV+",
        "ZEE5",
        "SonyLIV",
        "aha",
        "MX Player",
        "MUBI",
    ]

    found = []

    for group in groups:

        for provider in group or []:

            provider_name = (
                provider.get(
                    "provider_name"
                )
            )

            name = normalize_platform_name(
                provider_name
            )

            if (
                name
                and name not in found
            ):
                found.append(name)

    for preferred_name in preferred:

        if preferred_name in found:
            return preferred_name

    if found:
        return found[0]

    return None


# ============================================================
# PLATFORM SEARCH URL
# ============================================================

def build_platform_url(
    platform,
    title,
):

    if not platform or not title:
        return None

    encoded = quote_plus(
        title
    )

    platform_lower = (
        platform.lower()
    )

    if platform_lower == "prime video":

        return (
            "https://www.primevideo.com/"
            "search/ref=atv_nb_sr?phrase="
            + encoded
        )

    if platform_lower == "netflix":

        return (
            "https://www.netflix.com/search?q="
            + encoded
        )

    if platform_lower == "jiohotstar":

        return (
            "https://www.hotstar.com/in/search?q="
            + encoded
        )

    if platform_lower == "youtube":

        return (
            "https://www.youtube.com/results"
            "?search_query="
            + encoded
        )

    if platform_lower == "google play movies":

        return (
            "https://play.google.com/store/search"
            "?q="
            + encoded
            + "&c=movies"
        )

    if platform_lower == "disney+":

        return (
            "https://www.disneyplus.com/search/"
            + encoded
        )

    if platform_lower == "apple tv+":

        return (
            "https://tv.apple.com/search?term="
            + encoded
        )

    if platform_lower == "zee5":

        return (
            "https://www.zee5.com/search?q="
            + encoded
        )

    if platform_lower == "sonyliv":

        return (
            "https://www.sonyliv.com/search/"
            + encoded
        )

    return (
        "https://www.google.com/search?q="
        + quote_plus(
            f"{platform} {title}"
        )
    )


# ============================================================
# ARTWORK TYPE
# ============================================================

def artwork_type_label(
    item_type
):

    mapping = {

        "poster":
            "Poster",

        "cover":
            "Cover",

        "portrait":
            "Portrait",

        "season":
            "Portrait",

    }

    return mapping.get(
        item_type,
        "Poster",
    )


# ============================================================
# BUILD NAVIGATION ITEMS
#
# The navigation now contains:
#
# 1. Poster
# 2. Cover
# 3. Portrait / Season
#
# Each item contains:
#
# type
# artwork_type
# url
# label
# ============================================================

def build_navigation_items(media):

    items = []

    if not media:
        return items

    # ========================================================
    # MAIN POSTER
    # ========================================================

    poster_path = media.get(
        "poster_path"
    )

    if poster_path:

        items.append(
            {
                "type": "poster",
                "artwork_type": "Poster",
                "url": (
                    TMDB_IMAGE_URL
                    + poster_path
                ),
                "label": "Poster",
                "source": "TMDB",
            }
        )

    # ========================================================
    # BACKDROP / COVER
    # ========================================================

    backdrop_path = media.get(
        "backdrop_path"
    )

    if backdrop_path:

        items.append(
            {
                "type": "cover",
                "artwork_type": "Cover",
                "url": (
                    TMDB_IMAGE_URL
                    + backdrop_path
                ),
                "label": "Cover",
                "source": "TMDB",
            }
        )

    # ========================================================
    # TV SEASON POSTERS
    # ========================================================

    if media.get(
        "media_type"
    ) == "tv":

        seasons = media.get(
            "seasons",
            [],
        )

        for season in seasons:

            season_number = season.get(
                "season_number"
            )

            if season_number == 0:
                continue

            season_poster = season.get(
                "poster_path"
            )

            if not season_poster:
                continue

            season_name = season.get(
                "name",
                f"Season {season_number}",
            )

            items.append(
                {
                    "type": "season",
                    "artwork_type": "Portrait",
                    "url": (
                        TMDB_IMAGE_URL
                        + season_poster
                    ),
                    "label": season_name,
                    "source": "TMDB",
                    "season": season,
                }
            )

    return items


# ============================================================
# CREATE 5:4 THUMBNAIL
#
# IMPORTANT:
#
# The original poster is NOT stretched.
#
# It is center-cropped into EXACTLY:
#
# 1000 x 800
#
# = 5:4
#
# No 16:9.
# No long thumbnail.
# ============================================================

def create_thumbnail(
    image_url,
    title,
):

    try:

        response = SESSION.get(
            image_url,
            timeout=30,
        )

        response.raise_for_status()

        source = Image.open(
            io.BytesIO(
                response.content
            )
        ).convert("RGB")

        source_width, source_height = (
            source.size
        )

        target_ratio = (
            THUMB_WIDTH
            / THUMB_HEIGHT
        )

        source_ratio = (
            source_width
            / source_height
        )

        # ====================================================
        # CROP WIDTH
        # ====================================================

        if source_ratio > target_ratio:

            new_width = int(
                source_height
                * target_ratio
            )

            left = (
                source_width
                - new_width
            ) // 2

            source = source.crop(
                (
                    left,
                    0,
                    left + new_width,
                    source_height,
                )
            )

        # ====================================================
        # CROP HEIGHT
        # ====================================================

        elif source_ratio < target_ratio:

            new_height = int(
                source_width
                / target_ratio
            )

            top = (
                source_height
                - new_height
            ) // 2

            source = source.crop(
                (
                    0,
                    top,
                    source_width,
                    top + new_height,
                )
            )

        # ====================================================
        # EXACT 5:4
        # ====================================================

        source = source.resize(
            (
                THUMB_WIDTH,
                THUMB_HEIGHT,
            ),
            Image.Resampling.LANCZOS,
        )

        output = io.BytesIO()

        source.save(
            output,
            format="JPEG",
            quality=94,
            optimize=True,
        )

        output.seek(0)

        return output

    except Exception:

        logger.exception(
            "Thumbnail creation failed"
        )

        return None


# ============================================================
# BUILD CAPTION
#
# Example:
#
# 🎬 Prime Video Poster: Click Here
#
# 🖼 Artwork: Poster
#
# Iron Man - (2008)
#
# Powered by @Aero_Unity.
#
# ONLY ONE PLATFORM IS SHOWN.
# ============================================================

def build_caption(
    media,
    platform,
    item,
):

    title = (
        media.get("title")
        or media.get("name")
        or media.get("original_title")
        or media.get("original_name")
        or "Unknown"
    )

    release_date = (
        media.get("release_date")
        or media.get("first_air_date")
        or ""
    )

    year = ""

    if release_date:
        year = str(
            release_date
        )[:4]

    season = item.get(
        "season"
    )

    display_title = title

    if season:

        season_name = season.get(
            "name",
            "",
        )

        if season_name:

            display_title = (
                f"{title} - {season_name}"
            )

    if year:

        display_title = (
            f"{display_title} - ({year})"
        )

    # ========================================================
    # SELECT ONLY ONE PLATFORM
    # ========================================================

    selected_platform = None

    if platform:

        selected_platform = (
            normalize_platform_name(
                platform
            )
        )

    if not selected_platform:

        selected_platform = (
            get_available_platform(
                media
            )
        )

    # ========================================================
    # ARTWORK TYPE
    # ========================================================

    artwork_type = (
        item.get(
            "artwork_type"
        )
        or artwork_type_label(
            item.get("type")
        )
    )

    lines = []

    # ========================================================
    # PLATFORM
    # ========================================================

    if selected_platform:

        platform_url = (
            build_platform_url(
                selected_platform,
                title,
            )
        )

        if platform_url:

            safe_platform = html.escape(
                selected_platform
            )

            lines.append(
                f"🎬 <b>{safe_platform} Poster:</b> "
                f'<a href="{html.escape(platform_url)}">'
                f"Click Here</a>"
            )

    # ========================================================
    # ARTWORK TYPE
    # ========================================================

    lines.append(
        f"🖼 <b>Artwork:</b> "
        f"{html.escape(artwork_type)}"
    )

    lines.append("")

    # ========================================================
    # TITLE
    # ========================================================

    lines.append(
        f"<b>{html.escape(display_title)}</b>"
    )

    # ========================================================
    # FOOTER
    # ========================================================

    lines.append("")

    lines.append(
        "Powered by @Aero_Unity."
    )

    return "\n".join(
        lines
    )


# ============================================================
# END poster.py
# ============================================================
