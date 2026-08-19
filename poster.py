# ============================================================
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ============================================================

import io
import re
import html
import logging
from urllib.parse import quote_plus, urlparse

import requests
from PIL import Image, ImageOps

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

    query = str(
        query or ""
    ).strip()

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

    results = [
        item
        for item in results
        if item.get("media_type")
        in (
            "movie",
            "tv",
        )
    ]

    if not results:
        return None

    # --------------------------------------------------------
    # Prefer artwork + popularity
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

    media = dict(
        item
    )

    media["media_type"] = (
        media_type
    )

    # --------------------------------------------------------
    # Complete details
    # --------------------------------------------------------

    try:

        details = tmdb_get(
            f"/{media_type}/{item['id']}",
            {
                "language": TMDB_LANGUAGE,
            },
        )

        media.update(
            details
        )

    except Exception:

        logger.warning(
            "Could not load TMDB details",
            exc_info=True,
        )

    # --------------------------------------------------------
    # Watch providers
    # --------------------------------------------------------

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

def extract_title_from_url(
    url,
):

    try:

        response = SESSION.get(
            url,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        source = response.text

        patterns = [

            r'<meta[^>]+property=["\']og:title["\']'
            r'[^>]+content=["\']([^"\']+)["\']',

            r'<meta[^>]+content=["\']([^"\']+)["\']'
            r'[^>]+property=["\']og:title["\']',

            r'<meta[^>]+name=["\']twitter:title["\']'
            r'[^>]+content=["\']([^"\']+)["\']',

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
            # Remove common site suffixes
            # ------------------------------------------------

            title = re.sub(
                r"\s*[\|\-–—]\s*"
                r"(Netflix|Prime Video|"
                r"Amazon Prime Video|"
                r"JioHotstar|Hotstar|"
                r"Disney\+ Hotstar|"
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

    # --------------------------------------------------------
    # URL slug fallback
    # --------------------------------------------------------

    try:

        parsed = urlparse(
            url
        )

        path = parsed.path.strip(
            "/"
        )

        if path:

            last = path.split(
                "/"
            )[-1]

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

        "jiostar":
            "JioStar",

        "hotstar":
            "Disney+ Hotstar",

        "disney+ hotstar":
            "Disney+ Hotstar",

        "disney plus hotstar":
            "Disney+ Hotstar",

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
            "Aha",

        "mx player":
            "MX Player",

        "mubi":
            "MUBI",

        "iqiyi":
            "iQIYI",

    }

    return mappings.get(
        value,
        str(name).strip(),
    )


# ============================================================
# GET ONE AVAILABLE PLATFORM
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

    # --------------------------------------------------------
    # India first
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

    preferred = [

        "Prime Video",

        "Netflix",

        "JioHotstar",

        "Disney+ Hotstar",

        "JioStar",

        "YouTube",

        "Google Play Movies",

        "Apple TV+",

        "ZEE5",

        "SonyLIV",

        "Aha",

        "MX Player",

        "MUBI",

        "iQIYI",
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
    # Preferred provider
    # --------------------------------------------------------

    for name in preferred:

        if name in found:
            return name

    # --------------------------------------------------------
    # Any available provider
    # --------------------------------------------------------

    if found:
        return found[0]

    return None

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

    if platform_lower in (
        "jiohotstar",
        "disney+ hotstar",
    ):

        return (
            "https://www.hotstar.com/in/search?q="
            + encoded
        )

    if platform_lower == "youtube":

        return (
            "https://www.youtube.com/results?search_query="
            + encoded
        )

    if platform_lower == "google play movies":

        return (
            "https://play.google.com/store/search?q="
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

            season_name = (
                season.get(
                    "name"
                )
                or f"Season {season_number}"
            )

            items.append(
                {
                    "type": "season",

                    "url": (
                        TMDB_IMAGE_URL
                        + season_poster
                    ),

                    "label": season_name,

                    "season": season,
                }
            )

    return items

def create_thumbnail(
    image_url,
    title=None,
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
        )

        # ----------------------------------------------------
        # Handle EXIF orientation
        # ----------------------------------------------------

        source = ImageOps.exif_transpose(
            source
        )

        # ----------------------------------------------------
        # Convert to RGB
        # ----------------------------------------------------

        if source.mode != "RGB":

            if (
                source.mode
                in (
                    "RGBA",
                    "LA",
                )
            ):

                background = Image.new(
                    "RGB",
                    source.size,
                    "white",
                )

                if source.mode == "RGBA":

                    background.paste(
                        source,
                        mask=source.getchannel(
                            "A"
                        ),
                    )

                else:

                    background.paste(
                        source,
                        mask=source.getchannel(
                            "A"
                        ),
                    )

                source = background

            else:

                source = source.convert(
                    "RGB"
                )

        thumbnail = ImageOps.fit(
            source,
            (
                THUMB_WIDTH,
                THUMB_HEIGHT,
            ),
            method=Image.Resampling.LANCZOS,
            centering=(
                0.5,
                0.5,
            ),
        )

        # ----------------------------------------------------
        # Final safety resize
        # ----------------------------------------------------

        thumbnail = thumbnail.resize(
            (
                1000,
                800,
            ),
            Image.Resampling.LANCZOS,
        )

        # ----------------------------------------------------
        # JPEG output
        # ----------------------------------------------------

        output = io.BytesIO()

        output.name = (
            "poster_1000x800.jpg"
        )

        thumbnail.save(
            output,
            format="JPEG",
            quality=95,
            optimize=True,
            progressive=False,
        )

        output.seek(0)

        # ----------------------------------------------------
        # Verify dimensions
        # ----------------------------------------------------

        check = Image.open(
            output
        )

        if check.size != (
            1000,
            800,
        ):

            logger.error(
                "Thumbnail size incorrect: %s",
                check.size,
            )

            return None

        output.seek(0)

        logger.info(
            "Created thumbnail: %sx%s",
            1000,
            800,
        )

        return output

    except Exception:

        logger.exception(
            "Thumbnail creation failed"
        )

        return None

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

    # --------------------------------------------------------
    # Season
    # --------------------------------------------------------

    season = item.get(
        "season"
    )

    display_title = title

    if season:

        season_name = (
            season.get(
                "name",
                "",
            )
            or ""
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
    # Artwork type
    # --------------------------------------------------------

    artwork_type = (
        item.get(
            "type"
        )
        or "poster"
    )

    if artwork_type == "poster":

        artwork_name = "Poster"

    elif artwork_type == "cover":

        artwork_name = "Cover"

    elif artwork_type == "season":

        artwork_name = (
            item.get(
                "label"
            )
            or "Season"
        )

    else:

        artwork_name = (
            item.get(
                "label"
            )
            or "Artwork"
        )

    # --------------------------------------------------------
    # Platform
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
    # IMAGE URL
    #
    # This is what "Click Here" opens.
    # --------------------------------------------------------

    image_url = (
        item.get(
            "url"
        )
        or ""
    )

    # --------------------------------------------------------
    # Build caption
    # --------------------------------------------------------

    lines = []

    # --------------------------------------------------------
    # ONE PLATFORM ONLY
    # --------------------------------------------------------

    if selected_platform:

        safe_platform = html.escape(
            selected_platform
        )

        if image_url:

            safe_image_url = html.escape(
                image_url,
                quote=True,
            )

            lines.append(
                f'🎬 <b>{safe_platform} '
                f'{artwork_name}:</b> '
                f'<a href="{safe_image_url}">'
                f'Click Here</a>'
            )

        else:

            lines.append(
                f"🎬 <b>{safe_platform} "
                f"{artwork_name}</b>"
            )

    # --------------------------------------------------------
    # ARTWORK TYPE WHEN PLATFORM IS UNKNOWN
    # --------------------------------------------------------

    else:

        if image_url:

            safe_image_url = html.escape(
                image_url,
                quote=True,
            )

            lines.append(
                f'🖼 <b>{artwork_name}:</b> '
                f'<a href="{safe_image_url}">'
                f'Click Here</a>'
            )

        else:

            lines.append(
                f"🖼 <b>{artwork_name}</b>"
            )

    # --------------------------------------------------------
    # Space
    # --------------------------------------------------------

    lines.append("")

    # --------------------------------------------------------
    # TITLE
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
