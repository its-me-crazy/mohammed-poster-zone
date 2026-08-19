# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

import html
import re
import io
import logging

from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from PIL import Image, ImageDraw, ImageFont

from config import (
    TMDB_API_KEY,
    TMDB_LANGUAGE,
    REQUEST_TIMEOUT,
)

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

logger = logging.getLogger(
    "mohammed-poster"
)

# ------------------------- #
# TMDB
# ------------------------- #

TMDB_BASE = "https://api.themoviedb.org/3"

IMAGE_BASE = (
    "https://image.tmdb.org/t/p/w780"
)

# ------------------------- #
# Requests session
# ------------------------- #

session = requests.Session()

session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
})


# =========================================================
# TMDB REQUEST
# =========================================================

def tmdb_get(
    endpoint: str,
    params: Optional[dict] = None,
):

    params = dict(params or {})

    if not TMDB_API_KEY:
        raise RuntimeError(
            "TMDB_API_KEY is missing."
        )

    params["api_key"] = TMDB_API_KEY

    if TMDB_LANGUAGE:
        params["language"] = TMDB_LANGUAGE

    response = session.get(
        TMDB_BASE + endpoint,
        params=params,
        timeout=REQUEST_TIMEOUT,
    )

    if response.status_code != 200:

        logger.error(
            "TMDB API error | status=%s | endpoint=%s | response=%s",
            response.status_code,
            endpoint,
            response.text[:500],
        )

        raise RuntimeError(
            f"TMDB API returned HTTP "
            f"{response.status_code}"
        )

    return response.json()


# =========================================================
# CLEAN TITLE
# =========================================================

def clean_title(
    title: str,
) -> str:

    if not title:
        return ""

    title = re.sub(
        r"\s+",
        " ",
        title,
    ).strip()

    suffixes = [

        r"\s*\|\s*Netflix$",
        r"\s*-\s*Netflix$",

        r"\s*\|\s*Prime Video$",
        r"\s*-\s*Prime Video$",

        r"\s*\|\s*Amazon Prime Video$",
        r"\s*-\s*Amazon Prime Video$",

        r"\s*\|\s*JioHotstar$",
        r"\s*-\s*JioHotstar$",

        r"\s*\|\s*Hotstar$",
        r"\s*-\s*Hotstar$",

        r"\s*\|\s*Disney\+ Hotstar$",
        r"\s*-\s*Disney\+ Hotstar$",

        r"\s*\|\s*JioStar$",
        r"\s*-\s*JioStar$",

        r"\s*\|\s*SonyLIV$",
        r"\s*-\s*SonyLIV$",

        r"\s*\|\s*ZEE5$",
        r"\s*-\s*ZEE5$",

        r"\s*\|\s*Crunchyroll$",
        r"\s*-\s*Crunchyroll$",

        r"\s*\|\s*Hulu$",
        r"\s*-\s*Hulu$",

        r"\s*\|\s*YouTube$",
        r"\s*-\s*YouTube$",

        r"\s*\|\s*MX Player$",
        r"\s*-\s*MX Player$",

        r"\s*\|\s*Discovery\+$",
        r"\s*-\s*Discovery\+$",

        r"\s*\|\s*Chorki$",
        r"\s*-\s*Chorki$",

        r"\s*\|\s*District$",
        r"\s*-\s*District$",

        r"\s*\|\s*JustWatch$",
        r"\s*-\s*JustWatch$",

        r"\s*\|\s*Ultra Play$",
        r"\s*-\s*Ultra Play$",
    ]

    for pattern in suffixes:

        title = re.sub(
            pattern,
            "",
            title,
            flags=re.IGNORECASE,
        )

    return title.strip()


# =========================================================
# EXTRACT TITLE FROM OTT URL
# =========================================================

def extract_title_from_url(
    url: str,
) -> Optional[str]:

    try:

        parsed = urlparse(url)

        if parsed.scheme not in (
            "http",
            "https",
        ):
            return None

        response = session.get(
            url,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        # OpenGraph
        meta = soup.find(
            "meta",
            property="og:title",
        )

        if meta:

            content = meta.get(
                "content"
            )

            if content:

                return clean_title(
                    content
                )

        # Twitter
        meta = soup.find(
            "meta",
            attrs={
                "name": "twitter:title"
            },
        )

        if meta:

            content = meta.get(
                "content"
            )

            if content:

                return clean_title(
                    content
                )

        # Normal title
        if soup.title:

            title = soup.title.get_text(
                " ",
                strip=True,
            )

            if title:

                return clean_title(
                    title
                )

    except Exception:

        logger.exception(
            "Failed to extract title from URL"
        )

        return None

    return None


# =========================================================
# SEARCH MOVIE
# =========================================================

def search_movie(
    title: str,
):

    return tmdb_get(
        "/search/movie",
        {
            "query": title,
            "include_adult": "false",
        },
    ).get(
        "results",
        [],
    )


# =========================================================
# SEARCH TV
# =========================================================

def search_tv(
    title: str,
):

    return tmdb_get(
        "/search/tv",
        {
            "query": title,
            "include_adult": "false",
        },
    ).get(
        "results",
        [],
    )


# =========================================================
# WATCH PROVIDERS
# =========================================================

def get_watch_provider_data(
    media,
):

    try:

        media_type = media.get(
            "media_type"
        )

        media_id = media.get(
            "id"
        )

        if not media_type or not media_id:
            return {
                "providers": [],
                "provider_links": [],
                "watch_link": None,
            }

        data = tmdb_get(
            f"/{media_type}/{media_id}/watch/providers"
        )

        results = data.get(
            "results",
            {},
        )

        # India first
        region = (
            results.get("IN")
            or results.get("US")
        )

        if not region:

            return {
                "providers": [],
                "provider_links": [],
                "watch_link": None,
            }

        providers = []

        provider_links = []

        # TMDB's watch page
        watch_link = region.get(
            "link"
        )

        provider_groups = (
            region.get("flatrate", [])
            + region.get("free", [])
            + region.get("ads", [])
            + region.get("rent", [])
            + region.get("buy", [])
        )

        seen = set()

        for provider in provider_groups:

            name = provider.get(
                "provider_name"
            )

            if not name:
                continue

            normalized = name.lower().strip()

            if normalized in seen:
                continue

            seen.add(normalized)

            providers.append(name)

            logo_path = provider.get(
                "logo_path"
            )

            logo_url = None

            if logo_path:
                logo_url = image_url(
                    logo_path
                )

            provider_links.append({
                "name": name,
                "logo_url": logo_url,
                "url": watch_link,
                "provider_id": provider.get(
                    "provider_id"
                ),
            })

        return {
            "providers": providers,
            "provider_links": provider_links,
            "watch_link": watch_link,
        }

    except Exception:

        logger.exception(
            "Failed to get watch providers"
        )

        return {
            "providers": [],
            "provider_links": [],
            "watch_link": None,
        }


def get_watch_providers(
    media,
):

    data = get_watch_provider_data(
        media
    )

    return data.get(
        "providers",
        []
    )


# =========================================================
# CANDIDATE
# =========================================================

def make_candidate(
    item: dict,
    media_type: str,
):

    if not item.get(
        "poster_path"
    ):
        return None

    if media_type == "movie":

        name = item.get(
            "title"
        )

        original = item.get(
            "original_title"
        )

        date = item.get(
            "release_date",
            "",
        )

    else:

        name = item.get(
            "name"
        )

        original = item.get(
            "original_name"
        )

        date = item.get(
            "first_air_date",
            "",
        )

    return {
        "media_type": media_type,

        "id": item.get(
            "id"
        ),

        "title": name,

        "name": name,

        "original_title": original,

        "original_name": original,

        "year": (
            date[:4]
            if date
            else ""
        ),

        "poster_path": item.get(
            "poster_path"
        ),

        "overview": item.get(
            "overview",
            "",
        ),

        "providers": [],
        "provider_links": [],
        "watch_link": None,
    }


# =========================================================
# SEARCH MEDIA
# =========================================================

def search_media(
    title: str,
):

    title = clean_title(
        title
    )

    if not title:
        return None

    movies = search_movie(
        title
    )

    tvs = search_tv(
        title
    )

    candidates = []

    for item in movies:

        candidate = make_candidate(
            item,
            "movie",
        )

        if candidate:

            candidates.append(
                candidate
            )

    for item in tvs:

        candidate = make_candidate(
            item,
            "tv",
        )

        if candidate:

            candidates.append(
                candidate
            )

    if not candidates:
        return None

    normalized = (
        title.lower().strip()
    )

    selected = None

    # Exact match
    for candidate in candidates:

        candidate_title = (
            candidate.get("title")
            or ""
        ).lower().strip()

        original_title = (
            candidate.get(
                "original_title"
            )
            or ""
        ).lower().strip()

        if (
            candidate_title == normalized
            or original_title == normalized
        ):

            selected = candidate
            break

    # First best result
    if selected is None:

        selected = candidates[0]

    # --------------------------------------------------
    # GET WATCH PROVIDERS
    # --------------------------------------------------

    provider_data = (
        get_watch_provider_data(
            selected
        )
    )

    selected["providers"] = (
        provider_data.get(
            "providers",
            []
        )
    )

    selected["provider_links"] = (
        provider_data.get(
            "provider_links",
            []
        )
    )

    selected["watch_link"] = (
        provider_data.get(
            "watch_link"
        )
    )

    return selected


# =========================================================
# IMAGE URL
# =========================================================

def image_url(
    path: Optional[str],
):

    if not path:
        return None

    if path.startswith(
        "http://"
    ) or path.startswith(
        "https://"
    ):

        return path

    return IMAGE_BASE + path


# =========================================================
# GET MEDIA IMAGES
# =========================================================

def get_media_images(
    media: dict,
):

    endpoint = (
        f"/{media['media_type']}/"
        f"{media['id']}/images"
    )

    data = tmdb_get(
        endpoint,
        {
            "include_image_language": (
                "en,null"
            ),
        },
    )

    artwork = []

    # --------------------------------------------------
    # Portrait
    # --------------------------------------------------

    for item in data.get(
        "posters",
        [],
    ):

        url = image_url(
            item.get(
                "file_path"
            )
        )

        if url:

            artwork.append({
                "type": "Portrait",
                "url": url,
                "width": item.get(
                    "width",
                    0,
                ),
                "height": item.get(
                    "height",
                    0,
                ),
            })

    # --------------------------------------------------
    # Cover
    # --------------------------------------------------

    for item in data.get(
        "backdrops",
        [],
    ):

        url = image_url(
            item.get(
                "file_path"
            )
        )

        if url:

            artwork.append({
                "type": "Cover",
                "url": url,
                "width": item.get(
                    "width",
                    0,
                ),
                "height": item.get(
                    "height",
                    0,
                ),
            })

    # --------------------------------------------------
    # Logo
    # --------------------------------------------------

    for item in data.get(
        "logos",
        [],
    ):

        url = image_url(
            item.get(
                "file_path"
            )
        )

        if url:

            artwork.append({
                "type": "Logo",
                "url": url,
                "width": item.get(
                    "width",
                    0,
                ),
                "height": item.get(
                    "height",
                    0,
                ),
            })

    return artwork


# =========================================================
# SORT ARTWORK
# =========================================================

def sort_artwork(
    items,
):

    return sorted(
        items,
        key=lambda item: (
            item.get("width", 0)
            * item.get("height", 0)
        ),
        reverse=True,
    )


# =========================================================
# BEST ARTWORK
# =========================================================

def get_best_artwork(
    media,
):

    all_artwork = get_media_images(
        media
    )

    grouped = {
        "Portrait": [],
        "Cover": [],
        "Logo": [],
    }

    for item in all_artwork:

        item_type = item.get(
            "type"
        )

        if item_type in grouped:

            grouped[
                item_type
            ].append(item)

    result = []

    # EXACT ORDER
    for category in (
        "Portrait",
        "Cover",
        "Logo",
    ):

        images = sort_artwork(
            grouped[category]
        )

        if images:

            result.append(
                images[0]
            )

    return result


# =========================================================
# TV DETAILS
# =========================================================

def get_tv_details(
    media,
):

    if media.get(
        "media_type"
    ) != "tv":

        return None

    return tmdb_get(
        f"/tv/{media['id']}"
    )


# =========================================================
# SEASONS
# =========================================================

def get_seasons(
    media,
):

    details = get_tv_details(
        media
    )

    if not details:
        return []

    seasons = []

    for season in details.get(
        "seasons",
        [],
    ):

        number = season.get(
            "season_number"
        )

        if number is None:
            continue

        if number == 0:
            continue

        seasons.append({
            "number": number,

            "name": season.get(
                "name",
                f"Season {number}",
            ),

            "episode_count": season.get(
                "episode_count",
                0,
            ),

            "poster_path": season.get(
                "poster_path"
            ),
        })

    return seasons


# =========================================================
# SEASON POSTER
# =========================================================

def get_season_poster(
    series_id: int,
    season_number: int,
):

    data = tmdb_get(
        f"/tv/{series_id}/season/"
        f"{season_number}",
        {
            "append_to_response": (
                "images"
            ),
        },
    )

    images = data.get(
        "images",
        {},
    )

    posters = images.get(
        "posters",
        [],
    )

    if posters:

        posters = sort_artwork(
            posters
        )

        path = posters[0].get(
            "file_path"
        )

        if path:

            return image_url(
                path
            )

    return image_url(
        data.get(
            "poster_path"
        )
    )


# =========================================================
# NAVIGATION ITEMS
# =========================================================

def build_navigation_items(
    media,
):

    items = []

    # --------------------------------------------------
    # TMDB Portrait + Cover ONLY
    # --------------------------------------------------

    artwork = get_best_artwork(
        media
    )

    for item in artwork:

        item_type = item.get(
            "type"
        )

        # Only Portrait and Cover
        if item_type not in (
            "Portrait",
            "Cover",
        ):

            continue

        items.append({
            "type": item_type,
            "url": item["url"],
            "season": None,
            "source": "tmdb",
        })

    # --------------------------------------------------
    # Provider logos are NOT used as thumbnails.
    #
    # This keeps Next/Back as:
    #
    # Portrait -> Cover
    #
    # The title is rendered onto both thumbnails.
    # --------------------------------------------------

    return items


# =========================================================
# MEDIA TITLE
# =========================================================

def media_title(
    media,
    season=None,
):

    title = (
        media.get("title")
        or media.get("name")
        or media.get("original_title")
        or media.get("original_name")
        or "Unknown"
    )

    year = media.get(
        "year",
        "",
    )

    result = html.escape(
        str(title)
    )

    if year:

        result += (
            f" - ({html.escape(str(year))})"
        )

    if season:

        season_name = season.get(
            "name",
            "",
        )

        if season_name:

            result += (
                f" "
                f"{html.escape(str(season_name))}"
            )

    return result


# =========================================================
# CREATE RELEASE STYLE THUMBNAIL
# =========================================================

def create_thumbnail(
    image_url_value: str,
    title: str,
):

    try:

        response = session.get(
            image_url_value,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        source = Image.open(
            io.BytesIO(
                response.content
            )
        ).convert("RGB")

        target_width = 1280
        target_height = 720

        source_ratio = (
            source.width
            / source.height
        )

        target_ratio = (
            target_width
            / target_height
        )

        if source_ratio > target_ratio:

            new_height = target_height

            new_width = int(
                new_height
                * source_ratio
            )

        else:

            new_width = target_width

            new_height = int(
                new_width
                / source_ratio
            )

        source = source.resize(
            (
                new_width,
                new_height,
            ),
            Image.Resampling.LANCZOS,
        )

        # --------------------------------------------------
        # CENTER CROP
        # --------------------------------------------------

        left = (
            new_width
            - target_width
        ) // 2

        top = (
            new_height
            - target_height
        ) // 2

        source = source.crop(
            (
                left,
                top,
                left + target_width,
                top + target_height,
            )
        )

        # --------------------------------------------------
        # DARK GRADIENT
        # --------------------------------------------------

        overlay = Image.new(
            "RGBA",
            source.size,
            (
                0,
                0,
                0,
                0,
            ),
        )

        draw = ImageDraw.Draw(
            overlay
        )

        gradient_height = 300

        for y in range(
            target_height
            - gradient_height,
            target_height,
        ):

            alpha = int(
                220
                * (
                    y
                    - (
                        target_height
                        - gradient_height
                    )
                )
                / gradient_height
            )

            draw.line(
                (
                    0,
                    y,
                    target_width,
                    y,
                ),
                fill=(
                    0,
                    0,
                    0,
                    alpha,
                ),
            )

        source = Image.alpha_composite(
            source.convert("RGBA"),
            overlay,
        )

        # --------------------------------------------------
        # FONT
        # --------------------------------------------------

        draw = ImageDraw.Draw(
            source
        )

        font_paths = [

            "/usr/share/fonts/truetype/dejavu/"
            "DejaVuSans-Bold.ttf",

            "/usr/share/fonts/truetype/liberation2/"
            "LiberationSans-Bold.ttf",
        ]

        font = None

        for font_path in font_paths:

            try:

                font = ImageFont.truetype(
                    font_path,
                    58,
                )

                break

            except Exception:
                continue

        if font is None:

            font = ImageFont.load_default()

        # --------------------------------------------------
        # TITLE
        # --------------------------------------------------

        clean = re.sub(
            r"\s+",
            " ",
            str(title),
        ).strip()

        max_width = 1100

        words = clean.split()

        lines = []

        current = ""

        for word in words:

            test = (
                f"{current} {word}"
                if current
                else word
            )

            bbox = draw.textbbox(
                (0, 0),
                test,
                font=font,
            )

            width = (
                bbox[2]
                - bbox[0]
            )

            if width <= max_width:

                current = test

            else:

                if current:

                    lines.append(
                        current
                    )

                current = word

        if current:

            lines.append(
                current
            )

        # --------------------------------------------------
        # Maximum 2 lines
        # --------------------------------------------------

        if len(lines) > 2:

            middle = max(
                1,
                len(words) // 2,
            )

            lines = [
                " ".join(
                    words[:middle]
                ),
                " ".join(
                    words[middle:]
                ),
            ]

        # --------------------------------------------------
        # DRAW TITLE
        # --------------------------------------------------

        line_height = 70

        total_height = (
            len(lines)
            * line_height
        )

        start_y = (
            target_height
            - total_height
            - 55
        )

        for line in lines:

            bbox = draw.textbbox(
                (0, 0),
                line,
                font=font,
            )

            text_width = (
                bbox[2]
                - bbox[0]
            )

            x = (
                target_width
                - text_width
            ) // 2

            # Shadow
            draw.text(
                (
                    x + 4,
                    start_y + 4,
                ),
                line,
                font=font,
                fill=(
                    0,
                    0,
                    0,
                    230,
                ),
            )

            # Main
            draw.text(
                (
                    x,
                    start_y,
                ),
                line,
                font=font,
                fill="white",
            )

            start_y += line_height

        # --------------------------------------------------
        # JPEG
        # --------------------------------------------------

        output = io.BytesIO()

        source.convert(
            "RGB"
        ).save(
            output,
            format="JPEG",
            quality=82,
            optimize=True,
            progressive=True,
        )

        output.seek(0)

        output.name = (
            "mohammed_poster.jpg"
        )

        return output

    except Exception:

        logger.exception(
            "Thumbnail generation failed"
        )

        return None


# =========================================================
# CAPTION
# =========================================================

def build_caption(
    media,
    platform,
    artwork,
):

    # --------------------------------------------------
    # Current artwork
    # --------------------------------------------------

    current_type = artwork.get(
        "type",
        "Poster",
    )

    current_url = artwork.get(
        "url"
    )

    # --------------------------------------------------
    # Providers
    # --------------------------------------------------

    provider_links = media.get(
        "provider_links",
        []
    )

    providers = media.get(
        "providers",
        []
    )

    # --------------------------------------------------
    # Fallback platform
    # --------------------------------------------------

    if not provider_links and platform:

        provider_links = [{
            "name": str(platform),
            "url": None,
            "logo_url": None,
        }]

    # --------------------------------------------------
    # Platform caption
    # --------------------------------------------------

    platform_lines = []

    seen_platforms = set()

    for provider in provider_links:

        name = provider.get(
            "name"
        )

        if not name:
            continue

        normalized = (
            name.lower().strip()
        )

        if normalized in seen_platforms:
            continue

        seen_platforms.add(
            normalized
        )

        provider_url = provider.get(
            "url"
        )

        if provider_url:

            safe_url = html.escape(
                provider_url,
                quote=True,
            )

            platform_lines.append(
                f'<b>{html.escape(name)} '
                f'Poster:</b> '
                f'<a href="{safe_url}">'
                f'Click Here'
                f'</a>'
            )

        else:

            platform_lines.append(
                f"<b>{html.escape(name)} "
                f"Poster:</b> "
                f"Not Available"
            )

    # --------------------------------------------------
    # TMDB poster
    # --------------------------------------------------

    poster_path = media.get(
        "poster_path"
    )

    if poster_path:

        tmdb_poster = image_url(
            poster_path
        )

        safe_tmdb = html.escape(
            tmdb_poster,
            quote=True,
        )

        platform_lines.insert(
            0,
            f'<b>TMDB Poster:</b> '
            f'<a href="{safe_tmdb}">'
            f'Click Here'
            f'</a>'
        )

    # --------------------------------------------------
    # Artwork
    # --------------------------------------------------

    try:

        all_artwork = get_media_images(
            media
        )

    except Exception:

        logger.exception(
            "Failed to get artwork "
            "for caption"
        )

        all_artwork = []

    artwork_links = {
        "Portrait": None,
        "Cover": None,
        "Logo": None,
    }

    for item in all_artwork:

        item_type = item.get(
            "type"
        )

        item_url = item.get(
            "url"
        )

        if (
            item_type in artwork_links
            and item_url
            and artwork_links[item_type] is None
        ):

            artwork_links[item_type] = (
                item_url
            )

    # Current artwork gets priority
    if (
        current_type in artwork_links
        and current_url
    ):

        artwork_links[current_type] = (
            current_url
        )

    # --------------------------------------------------
    # Build artwork links
    # --------------------------------------------------

    artwork_lines = []

    for category in (
        "Portrait",
        "Cover",
    ):

        url = artwork_links.get(
            category
        )

        if url:

            safe_url = html.escape(
                url,
                quote=True,
            )

            artwork_lines.append(
                f'{category}: '
                f'<a href="{safe_url}">'
                f'Click Here'
                f'</a>'
            )

        else:

            artwork_lines.append(
                f"{category}: "
                f"Not Available"
            )

    # --------------------------------------------------
    # Title
    # --------------------------------------------------

    title = media_title(
        media,
        artwork.get("season"),
    )

    # --------------------------------------------------
    # FINAL CAPTION
    # --------------------------------------------------

    lines = []

    if platform_lines:

        lines.extend(
            platform_lines
        )

    lines.append("")

    lines.extend(
        artwork_lines
    )

    lines.append("")

    lines.append(
        f"<b>{title}</b>"
    )

    lines.append("")

    lines.append(
        "Powered by @Aero_Unity."
    )

    return "\n\n".join(
        lines
    )


# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #
