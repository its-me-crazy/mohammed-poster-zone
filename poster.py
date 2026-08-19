# ============================================================
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ============================================================

# ============================================================
# poster.py
# ============================================================

import io
import re
import html
import logging
from urllib.parse import quote_plus, urlparse

import requests
from PIL import Image, ImageDraw, ImageFont

from config import TMDB_API_KEY


logger = logging.getLogger(
    "mohammed-poster-zone.poster"
)


# ============================================================
# CONSTANTS
# ============================================================

TMDB_API_URL = (
    "https://api.themoviedb.org/3"
)

TMDB_IMAGE_URL = (
    "https://image.tmdb.org/t/p/original"
)

# Thumbnail ratio:
#
# 5:4
#
# This prevents the thumbnail from becoming
# a long 16:9 image.
#
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

def tmdb_get(
    endpoint,
    params=None,
):

    if not TMDB_API_KEY:
        raise RuntimeError(
            "TMDB_API_KEY is missing."
        )

    if params is None:
        params = {}

    params = dict(params)

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

def search_media(
    query,
):

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

    allowed = {
        "movie",
        "tv",
    }

    results = [
        item
        for item in results
        if item.get("media_type") in allowed
    ]

    if not results:
        return None

    # Prefer results that have artwork.
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

    # --------------------------------------------------------
    # Get complete movie / TV information
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Providers
    # --------------------------------------------------------

    try:

        providers = tmdb_get(
            f"/{media_type}/{item['id']}/watch/providers"
        )

        media["watch_providers"] = (
            providers.get(
                "results",
                {}
            )
        )

    except Exception:

        media["watch_providers"] = {}

    return media


# ============================================================
# EXTRACT TITLE FROM OTT URL
# ============================================================

def extract_title_from_url(
    url,
):

    try:

        response = SESSION.get(
            url,
            timeout=20,
        )

        response.raise_for_status()

        source = response.text

        # ----------------------------------------------------
        # OpenGraph title
        # ----------------------------------------------------

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

            if match:

                title = html.unescape(
                    match.group(1)
                )

                title = re.sub(
                    r"\s+",
                    " ",
                    title,
                ).strip()

                if title:

                    # Remove common site suffixes.
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

                    return title

    except Exception:

        logger.exception(
            "Failed to extract title from URL"
        )

    # --------------------------------------------------------
    # Fallback: URL slug
    # --------------------------------------------------------

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

def normalize_platform_name(
    name,
):

    if not name:
        return None

    value = str(name).lower().strip()

    mappings = {
        "amazon prime video": "Prime Video",
        "prime video": "Prime Video",
        "amazon": "Prime Video",

        "netflix": "Netflix",

        "jiohotstar": "JioHotstar",
        "hotstar": "JioHotstar",

        "youtube": "YouTube",

        "google play movies": (
            "Google Play Movies"
        ),
        "google play": (
            "Google Play Movies"
        ),

        "disney plus": "Disney+",
        "disney+": "Disney+",

        "apple tv": "Apple TV+",
        "apple tv+": "Apple TV+",

        "zee5": "ZEE5",

        "sonyliv": "SonyLIV",

        "aha": "aha",

        "mx player": "MX Player",

        "mubi": "MUBI",
    }

    return mappings.get(
        value,
        name,
    )


# ============================================================
# PROVIDER NAME
# ============================================================

def get_available_platform(
    media,
):

    providers = media.get(
        "watch_providers",
        {},
    )

    if not isinstance(
        providers,
        dict,
    ):
        return None

    # India first.
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

    # TMDB normally gives flatrate,
    # free, ads and rent/buy.
    provider_groups = [
        country_data.get("flatrate", []),
        country_data.get("free", []),
        country_data.get("ads", []),
        country_data.get("rent", []),
        country_data.get("buy", []),
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

    for group in provider_groups:

        for provider in group or []:

            name = normalize_platform_name(
                provider.get(
                    "provider_name"
                )
            )

            if name and name not in found:
                found.append(name)

    # Preferred provider.
    for preferred_name in preferred:

        if preferred_name in found:
            return preferred_name

    # Any available provider.
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

    # --------------------------------------------------------
    # Prime Video
    # --------------------------------------------------------

    if platform_lower == "prime video":

        return (
            "https://www.primevideo.com/"
            "search/ref=atv_nb_sr?phrase="
            + encoded
        )

    # --------------------------------------------------------
    # Netflix
    # --------------------------------------------------------

    if platform_lower == "netflix":

        return (
            "https://www.netflix.com/search?q="
            + encoded
        )

    # --------------------------------------------------------
    # JioHotstar
    # --------------------------------------------------------

    if platform_lower == "jiohotstar":

        return (
            "https://www.hotstar.com/in/search?q="
            + encoded
        )

    # --------------------------------------------------------
    # YouTube
    # --------------------------------------------------------

    if platform_lower == "youtube":

        return (
            "https://www.youtube.com/results?search_query="
            + encoded
        )

    # --------------------------------------------------------
    # Google Play Movies
    # --------------------------------------------------------

    if platform_lower == "google play movies":

        return (
            "https://play.google.com/store/search?q="
            + encoded
            + "&c=movies"
        )

    # --------------------------------------------------------
    # Disney+
    # --------------------------------------------------------

    if platform_lower == "disney+":

        return (
            "https://www.disneyplus.com/search/"
            + encoded
        )

    # --------------------------------------------------------
    # Apple TV+
    # --------------------------------------------------------

    if platform_lower == "apple tv+":

        return (
            "https://tv.apple.com/search?term="
            + encoded
        )

    # --------------------------------------------------------
    # ZEE5
    # --------------------------------------------------------

    if platform_lower == "zee5":

        return (
            "https://www.zee5.com/search?q="
            + encoded
        )

    # --------------------------------------------------------
    # SonyLIV
    # --------------------------------------------------------

    if platform_lower == "sonyliv":

        return (
            "https://www.sonyliv.com/search/"
            + encoded
        )

    # --------------------------------------------------------
    # Generic fallback
    # --------------------------------------------------------

    return (
        "https://www.google.com/search?q="
        + quote_plus(
            f"{platform} {title}"
        )
    )


# ============================================================
# BUILD NAVIGATION ITEMS
# ============================================================

def build_navigation_items(
    media,
):

    items = []

    if not media:
        return items

    media_type = media.get(
        "media_type"
    )

    # ========================================================
    # Main poster
    # ========================================================

    poster_path = media.get(
        "poster_path"
    )

    if poster_path:

        items.append(
            {
                "type": "poster",
                "url": (
                    TMDB_IMAGE_URL
                    + poster_path
                ),
                "label": "Poster",
            }
        )

    # ========================================================
    # Backdrop / cover
    # ========================================================

    backdrop_path = media.get(
        "backdrop_path"
    )

    if backdrop_path:

        items.append(
            {
                "type": "cover",
                "url": (
                    TMDB_IMAGE_URL
                    + backdrop_path
                ),
                "label": "Cover",
            }
        )

    # ========================================================
    # TV SEASONS
    # ========================================================

    if media_type == "tv":

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

            items.append(
                {
                    "type": "season",
                    "url": (
                        TMDB_IMAGE_URL
                        + season_poster
                    ),
                    "label": season.get(
                        "name",
                        f"Season {season_number}",
                    ),
                    "season": season,
                }
            )

    return items


# ============================================================
# CREATE 5:4 THUMBNAIL
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

        # ----------------------------------------------------
        # Target = 5:4
        # ----------------------------------------------------

        target_ratio = (
            THUMB_WIDTH
            / THUMB_HEIGHT
        )

        source_width, source_height = (
            source.size
        )

        source_ratio = (
            source_width
            / source_height
        )

        # ----------------------------------------------------
        # Center crop
        # ----------------------------------------------------

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

        source = source.resize(
            (
                THUMB_WIDTH,
                THUMB_HEIGHT,
            ),
            Image.Resampling.LANCZOS,
        )

        # ----------------------------------------------------
        # Create output
        # ----------------------------------------------------

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
# IMPORTANT:
# Only ONE platform button is generated.
#
# Priority:
# 1. OTT platform passed to function
# 2. TMDB available provider
# 3. No platform button
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

        year = release_date[:4]

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

    # --------------------------------------------------------
    # Determine ONLY ONE platform
    # --------------------------------------------------------

    selected_platform = (
        normalize_platform_name(
            platform
        )
        if platform
        else None
    )

    if not selected_platform:

        selected_platform = (
            get_available_platform(
                media
            )
        )

    # --------------------------------------------------------
    # Build caption
    # --------------------------------------------------------

    lines = []

    # --------------------------------------------------------
    # ONE platform only
    # --------------------------------------------------------

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
                f'🎬 <b>{safe_platform} Poster:</b> '
                f'<a href="{html.escape(platform_url)}">'
                f'Click Here</a>'
            )

    # --------------------------------------------------------
    # Empty line
    # --------------------------------------------------------

    if lines:
        lines.append("")

    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    lines.append(
        html.escape(
            display_title
        )
    )

    # --------------------------------------------------------
    # Footer
    # --------------------------------------------------------

    lines.append("")

    lines.append(
        "Powered by @Aero_Unity."
    )

    return "\n".join(
        lines
    )


# ============================================================
# END
# ============================================================
