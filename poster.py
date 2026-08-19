# ============================================================
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ============================================================

# ============================================================
# poster.py
# Mohammed Poster Zone
# ============================================================

import io
import re
import html
import logging
from urllib.parse import quote_plus, urlparse

import requests
from PIL import Image

from config import (
    TMDB_API_KEY,
    TMDB_LANGUAGE,
    REQUEST_TIMEOUT,
)


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


# ============================================================
# EXACT THUMBNAIL SIZE
#
# 1000 x 800
#
# 1000 / 800 = 1.25
# 5 / 4 = 1.25
#
# Therefore:
# 1000 x 800 = EXACTLY 5:4
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

def tmdb_get(
    endpoint,
    params=None,
):
    """
    Make a request to TMDB.
    """

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
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# SEARCH MEDIA
# ============================================================

def search_media(
    query,
):
    """
    Search TMDB for a movie or TV series.
    """

    query = str(query).strip()

    if not query:
        return None

    try:

        result = tmdb_get(
            "/search/multi",
            {
                "query": query,
                "language": TMDB_LANGUAGE,
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

    # --------------------------------------------------------
    # Prefer:
    # 1. Poster
    # 2. Backdrop
    # 3. Popularity
    # --------------------------------------------------------

    results.sort(
        key=lambda item: (
            bool(
                item.get(
                    "poster_path"
                )
            ),
            bool(
                item.get(
                    "backdrop_path"
                )
            ),
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
    # COMPLETE DETAILS
    # ========================================================

    try:

        details = tmdb_get(
            f"/{media_type}/{item['id']}",
            {
                "language": TMDB_LANGUAGE,
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
                {}
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

def extract_title_from_url(
    url,
):
    """
    Extract movie/series title from an OTT page.
    """

    try:

        response = SESSION.get(
            url,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        source = response.text

        patterns = [

            # OpenGraph
            r'<meta[^>]+property=["\']og:title["\']'
            r'[^>]+content=["\']([^"\']+)["\']',

            r'<meta[^>]+content=["\']([^"\']+)["\']'
            r'[^>]+property=["\']og:title["\']',

            # Twitter
            r'<meta[^>]+name=["\']twitter:title["\']'
            r'[^>]+content=["\']([^"\']+)["\']',

            # HTML title
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

            # ------------------------------------------------
            # Remove common platform suffixes
            # ------------------------------------------------

            title = re.sub(
                r"\s*[\|\-–—]\s*"
                r"(Netflix|"
                r"Prime Video|"
                r"Amazon Prime Video|"
                r"JioHotstar|"
                r"Hotstar|"
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
    # FALLBACK: URL SLUG
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

def normalize_platform_name(
    name,
):
    """
    Convert TMDB provider names to clean names.
    """

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

        "jio hotstar":
            "JioHotstar",

        "hotstar":
            "JioHotstar",

        "youtube":
            "YouTube",

        "youtube premium":
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

        "sony liv":
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
        str(name).strip(),
    )


# ============================================================
# PROVIDER PRIORITY
# ============================================================

PLATFORM_PRIORITY = [

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


# ============================================================
# GET AVAILABLE PLATFORM
# ============================================================

def get_available_platform(
    media,
):
    """
    Get exactly ONE platform from TMDB.

    India is preferred.
    US is used as fallback.
    """

    providers = media.get(
        "watch_providers",
        {},
    )

    if not isinstance(
        providers,
        dict,
    ):
        return None

    # --------------------------------------------------------
    # Prefer India
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Provider groups
    # --------------------------------------------------------

    provider_groups = [

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

    found = []

    for group in provider_groups:

        if not isinstance(
            group,
            list,
        ):
            continue

        for provider in group:

            if not isinstance(
                provider,
                dict,
            ):
                continue

            name = normalize_platform_name(
                provider.get(
                    "provider_name"
                )
            )

            if (
                name
                and name not in found
            ):
                found.append(
                    name
                )

    # --------------------------------------------------------
    # Select ONE according to priority
    # --------------------------------------------------------

    for preferred in PLATFORM_PRIORITY:

        if preferred in found:
            return preferred

    # --------------------------------------------------------
    # Fallback to first provider
    # --------------------------------------------------------

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
    """
    Build a platform search URL.
    """

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
# GET DISPLAY TITLE
# ============================================================

def get_media_title(
    media,
):
    """
    Get the best available title.
    """

    return (
        media.get("title")
        or media.get("name")
        or media.get("original_title")
        or media.get("original_name")
        or "Unknown"
    )


# ============================================================
# GET YEAR
# ============================================================

def get_media_year(
    media,
):
    """
    Get release / first-air year.
    """

    release_date = (
        media.get("release_date")
        or media.get("first_air_date")
        or ""
    )

    if release_date:
        return str(
            release_date
        )[:4]

    return ""


# ============================================================
# GET ARTWORK LABEL
# ============================================================

def get_item_label(
    item,
):
    """
    Return:
      Poster
      Cover
      Season 1
      Season 2
      etc.
    """

    item_type = (
        item.get("type")
        or ""
    ).lower()

    # --------------------------------------------------------
    # Main poster
    # --------------------------------------------------------

    if item_type == "poster":
        return "Poster"

    # --------------------------------------------------------
    # Cover
    # --------------------------------------------------------

    if item_type == "cover":
        return "Cover"

    # --------------------------------------------------------
    # Season
    # --------------------------------------------------------

    if item_type == "season":

        season = item.get(
            "season",
            {},
        )

        if isinstance(
            season,
            dict,
        ):

            season_number = (
                season.get(
                    "season_number"
                )
            )

            if (
                season_number is not None
                and season_number > 0
            ):

                return (
                    f"Season {season_number}"
                )

            season_name = (
                season.get(
                    "name"
                )
            )

            if season_name:
                return str(
                    season_name
                )

        label = item.get(
            "label"
        )

        if label:
            return str(
                label
            )

        return "Season"

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    label = item.get(
        "label"
    )

    if label:
        return str(
            label
        )

    return "Poster"


# ============================================================
# BUILD NAVIGATION ITEMS
# ============================================================

def build_navigation_items(
    media,
):
    """
    Build all artwork that the user can browse.

    Order:
      1. Poster
      2. Cover
      3. Season 1
      4. Season 2
      5. Season 3...
    """

    items = []

    if not media:
        return items

    media_type = media.get(
        "media_type"
    )

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

                "url": (
                    TMDB_IMAGE_URL
                    + poster_path
                ),

                "label": "Poster",
            }
        )

    # ========================================================
    # COVER
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

        if isinstance(
            seasons,
            list,
        ):

            # Sort by season number.
            seasons = sorted(
                seasons,
                key=lambda season: (
                    season.get(
                        "season_number",
                        0,
                    )
                    or 0
                ),
            )

            for season in seasons:

                if not isinstance(
                    season,
                    dict,
                ):
                    continue

                season_number = (
                    season.get(
                        "season_number"
                    )
                )

                # Skip specials.
                if season_number == 0:
                    continue

                season_poster = (
                    season.get(
                        "poster_path"
                    )
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
# CREATE EXACT 5:4 THUMBNAIL
#
# Output:
#
# 1000 x 800
#
# EXACT 5:4
#
# IMPORTANT:
#
# We DO NOT use a center crop.
#
# The complete source artwork is fitted
# inside the 1000x800 canvas.
#
# This prevents:
# - Faces being cut
# - Poster text being cut
# - Character heads being cut
# - Important artwork being lost
#
# The image is NEVER stretched.
# ============================================================

def create_thumbnail(
    image_url,
    title=None,
):
    """
    Download artwork and create
    an exact 1000x800 thumbnail.
    """

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

        if (
            source_width <= 0
            or source_height <= 0
        ):
            return None

        # ====================================================
        # TARGET 5:4
        # ====================================================

        target_width = (
            THUMB_WIDTH
        )

        target_height = (
            THUMB_HEIGHT
        )

        # ====================================================
        # FIT IMAGE INSIDE 1000x800
        #
        # Complete image remains visible.
        # ====================================================

        scale = min(
            target_width
            / source_width,

            target_height
            / source_height,
        )

        new_width = max(
            1,
            int(
                source_width
                * scale
            ),
        )

        new_height = max(
            1,
            int(
                source_height
                * scale
            ),
        )

        resized = source.resize(
            (
                new_width,
                new_height,
            ),
            Image.Resampling.LANCZOS,
        )

        # ====================================================
        # BACKGROUND
        #
        # Use average dark background from
        # the source artwork.
        # ====================================================

        try:

            small = source.resize(
                (
                    1,
                    1,
                ),
                Image.Resampling.BILINEAR,
            )

            background_color = (
                small.getpixel(
                    (
                        0,
                        0,
                    )
                )
            )

            # Darken the average color.
            background_color = tuple(
                max(
                    0,
                    int(
                        value
                        * 0.45
                    ),
                )
                for value in background_color
            )

        except Exception:

            background_color = (
                25,
                25,
                25,
            )

        # ====================================================
        # CREATE EXACT 1000x800 CANVAS
        # ====================================================

        canvas = Image.new(
            "RGB",
            (
                target_width,
                target_height,
            ),
            background_color,
        )

        # ====================================================
        # CENTER IMAGE
        # ====================================================

        x = (
            target_width
            - new_width
        ) // 2

        y = (
            target_height
            - new_height
        ) // 2

        canvas.paste(
            resized,
            (
                x,
                y,
            ),
        )

        # ====================================================
        # JPEG OUTPUT
        # ====================================================

        output = io.BytesIO()

        canvas.save(
            output,
            format="JPEG",
            quality=94,
            optimize=True,
            progressive=True,
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
# Iron Man - (2008)
#
# Powered by @Aero_Unity.
#
#
# Only ONE platform is displayed.
# ============================================================

def build_caption(
    media,
    platform,
    item,
):
    """
    Build final Telegram caption.
    """

    # ========================================================
    # TITLE
    # ========================================================

    title = get_media_title(
        media
    )

    year = get_media_year(
        media
    )

    # ========================================================
    # ARTWORK TYPE
    # ========================================================

    artwork_label = get_item_label(
        item
    )

    # ========================================================
    # DISPLAY TITLE
    # ========================================================

    display_title = title

    if artwork_label.lower().startswith(
        "season "
    ):

        display_title = (
            f"{title} - {artwork_label}"
        )

    elif year:

        display_title = (
            f"{title} - ({year})"
        )

    # For season, add year after season title.
    if (
        artwork_label.lower().startswith(
            "season "
        )
        and year
    ):

        display_title = (
            f"{title} - "
            f"{artwork_label} "
            f"- ({year})"
        )

    # ========================================================
    # SELECT ONLY ONE PLATFORM
    # ========================================================

    selected_platform = None

    # --------------------------------------------------------
    # 1. Platform explicitly supplied
    #
    # Example:
    # /ott Netflix URL
    # --------------------------------------------------------

    if platform:

        selected_platform = (
            normalize_platform_name(
                platform
            )
        )

    # --------------------------------------------------------
    # 2. Otherwise TMDB provider
    # --------------------------------------------------------

    if not selected_platform:

        selected_platform = (
            get_available_platform(
                media
            )
        )

    # ========================================================
    # CAPTION
    # ========================================================

    lines = []

    # ========================================================
    # ONE PLATFORM
    # ========================================================

    if selected_platform:

        platform_url = (
            build_platform_url(
                selected_platform,
                title,
            )
        )

        if platform_url:

            safe_platform = (
                html.escape(
                    selected_platform
                )
            )

            safe_artwork = (
                html.escape(
                    artwork_label
                )
            )

            safe_url = (
                html.escape(
                    platform_url,
                    quote=True,
                )
            )

            lines.append(
                f'🎬 <b>{safe_platform} '
                f'{safe_artwork}:</b> '
                f'<a href="{safe_url}">'
                f'Click Here</a>'
            )

    # ========================================================
    # EMPTY LINE
    # ========================================================

    if lines:

        lines.append("")

    # ========================================================
    # TITLE
    # ========================================================

    lines.append(
        html.escape(
            display_title
        )
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
# END OF poster.py
# ============================================================
