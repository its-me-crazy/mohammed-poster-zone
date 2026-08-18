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

# ------------------------- #
# TMDB request
# ------------------------- #

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
            f"TMDB API returned "
            f"HTTP {response.status_code}"
        )

    return response.json()

# ------------------------- #
# Clean title
# ------------------------- #

def clean_title(
    title: str
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
    ]

    for pattern in suffixes:

        title = re.sub(
            pattern,
            "",
            title,
            flags=re.IGNORECASE,
        )

    return title.strip()

# ------------------------- #
# Extract title from OTT URL
# ------------------------- #

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

        # OpenGraph title
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

        # Twitter title
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

# ------------------------- #
# Search movie
# ------------------------- #

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

# ------------------------- #
# Search TV
# ------------------------- #

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

# ------------------------- #
# Candidate
# ------------------------- #

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

        "original_title": original,

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
    }

# ------------------------- #
# Search media
# ------------------------- #

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

    # Exact match first
    for candidate in candidates:

        candidate_title = (
            candidate["title"]
            or ""
        ).lower().strip()

        original_title = (
            candidate["original_title"]
            or ""
        ).lower().strip()

        if (
            candidate_title
            == normalized
            or original_title
            == normalized
        ):

            return candidate

    return candidates[0]

# ------------------------- #
# Image URL
# ------------------------- #

def image_url(
    path: Optional[str],
):

    if not path:
        return None

    return IMAGE_BASE + path

# ------------------------- #
# Get media images
# ------------------------- #

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

    posters = data.get(
        "posters",
        [],
    )

    backdrops = data.get(
        "backdrops",
        [],
    )

    logos = data.get(
        "logos",
        [],
    )

    # Portrait
    for item in posters:

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

    # Cover
    for item in backdrops:

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

    # Logo
    for item in logos:

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

# ------------------------- #
# Sort artwork
# ------------------------- #

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

# ------------------------- #
# Best artwork
# ------------------------- #

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

        grouped[
            item["type"]
        ].append(item)

    result = []

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

# ------------------------- #
# TV details
# ------------------------- #

def get_tv_details(
    media,
):

    if media["media_type"] != "tv":
        return None

    return tmdb_get(
        f"/tv/{media['id']}"
    )

# ------------------------- #
# Seasons
# ------------------------- #

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

# ------------------------- #
# Season poster
# ------------------------- #

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

    path = data.get(
        "poster_path"
    )

    return image_url(
        path
    )

# ------------------------- #
# Navigation items
# ------------------------- #

def build_navigation_items(
    media,
):

    items = []

    artwork = get_best_artwork(
        media
    )

    for item in artwork:

        items.append({
            "type": item["type"],
            "url": item["url"],
            "season": None,
        })

    if media["media_type"] == "tv":

        seasons = get_seasons(
            media
        )

        for season in seasons:

            poster = get_season_poster(
                media["id"],
                season["number"],
            )

            if not poster:
                continue

            items.append({
                "type": (
                    f"Season "
                    f"{season['number']} "
                    f"Portrait"
                ),

                "url": poster,

                "season": season,
            })

    return items

# ------------------------- #
# Media title
# ------------------------- #

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
        title
    )

    if year:

        result += (
            f" - ({html.escape(year)})"
        )

    if season:

        result += (
            f" "
            f"{html.escape(season['name'])}"
        )

    return result

# ==================================================
# CREATE RELEASE-STYLE THUMBNAIL
# ==================================================

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

        # ------------------------------------------
        # 16:9 output
        # ------------------------------------------

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

        # ------------------------------------------
        # Center crop
        # ------------------------------------------

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

        # ------------------------------------------
        # Dark bottom gradient
        # ------------------------------------------

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

        gradient_height = 280

        for y in range(
            target_height
            - gradient_height,
            target_height,
        ):

            alpha = int(
                210
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

        # ------------------------------------------
        # Title
        # ------------------------------------------

        draw = ImageDraw.Draw(
            source
        )

        font_paths = [

            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",

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

        # ------------------------------------------
        # Clean title
        # ------------------------------------------

        clean = re.sub(
            r"\s+",
            " ",
            title,
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

        # ------------------------------------------
        # Maximum 2 lines
        # ------------------------------------------

        if len(lines) > 2:

            middle = len(words) // 2

            lines = [
                " ".join(
                    words[:middle]
                ),
                " ".join(
                    words[middle:]
                ),
            ]

        # ------------------------------------------
        # Draw title
        # ------------------------------------------

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

            # Main title
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

        # ------------------------------------------
        # Compress JPEG
        # ------------------------------------------

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

# ==================================================
# CAPTION
# ==================================================

def build_caption(
    media,
    platform,
    artwork,
):

    # ------------------------------------------
    # Current artwork
    # ------------------------------------------

    current_type = artwork.get(
        "type",
        "Poster",
    )

    # ------------------------------------------
    # Platform
    # ------------------------------------------

    platform = (
        platform
        or "Poster"
    )

    platform = html.escape(
        platform
    )

    # ------------------------------------------
    # Current artwork URL
    # ------------------------------------------

    current_url = artwork.get(
        "url"
    )

    if current_url:

        current_url = html.escape(
            current_url,
            quote=True,
        )

        platform_line = (
            f"<b>{platform} Poster:</b> "
            f"{current_url}"
        )

    else:

        platform_line = (
            f"<b>{platform} Poster:</b>"
        )

    # ------------------------------------------
    # Get all artwork
    # ------------------------------------------

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

    # ------------------------------------------
    # Find best link for each category
    # ------------------------------------------

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
            item_type
            in artwork_links
            and item_url
            and not artwork_links[item_type]
        ):

            artwork_links[item_type] = (
                item_url
            )

    # ------------------------------------------
    # If current artwork belongs to a category,
    # use it as the category link.
    # ------------------------------------------

    if (
        current_type
        in artwork_links
        and current_url
    ):

        artwork_links[current_type] = (
            artwork.get("url")
        )

    # ------------------------------------------
    # Build clickable links
    # ------------------------------------------

    lines = []

    for category in (
        "Portrait",
        "Cover",
        "Logo",
    ):

        url = artwork_links.get(
            category
        )

        if url:

            safe_url = html.escape(
                url,
                quote=True,
            )

            lines.append(
                f'{category}: '
                f'<a href="{safe_url}">'
                f'Click Here'
                f'</a>'
            )

        else:

            lines.append(
                f"{category}: "
                f"Not Available"
            )

    # ------------------------------------------
    # Title
    # ------------------------------------------

    title = media_title(
        media,
        artwork.get("season"),
    )

    # ------------------------------------------
    # Final caption
    # ------------------------------------------

    return (
        f"{platform_line}\n\n"
        f"{lines[0]}\n\n"
        f"{lines[1]}\n\n"
        f"{lines[2]}\n\n"
        f"<b>{title}</b>\n\n"
        "Powered by @Aero_Unity."
    )

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #
