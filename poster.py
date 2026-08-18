# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

import html
import re
from typing import Optional
from urllib.parse import urlparse

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

import requests
from bs4 import BeautifulSoup

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

from config import (
    TMDB_API_KEY,
    TMDB_LANGUAGE,
    REQUEST_TIMEOUT,
)

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

TMDB_BASE = "https://api.themoviedb.org/3"

IMAGE_BASE = (
    "https://image.tmdb.org/t/p/original"
)

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
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
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

def tmdb_get(
    endpoint: str,
    params: Optional[dict] = None,
):
    params = dict(params or {})

    params["api_key"] = TMDB_API_KEY
    params["language"] = TMDB_LANGUAGE

    response = session.get(
        TMDB_BASE + endpoint,
        params=params,
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    return response.json()

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

def clean_title(title: str) -> str:
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
# Don't Remove Credit
# Owner @Mr_Mohammed_29
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
            content = meta.get("content")

            if content:
                return clean_title(content)

        # Twitter title
        meta = soup.find(
            "meta",
            attrs={
                "name": "twitter:title",
            },
        )

        if meta:
            content = meta.get("content")

            if content:
                return clean_title(content)

        # Normal page title
        if soup.title:
            title = soup.title.get_text(
                " ",
                strip=True,
            )

            if title:
                return clean_title(title)

    except Exception:
        return None

    return None

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

def search_movie(title: str):
    return tmdb_get(
        "/search/movie",
        {
            "query": title,
            "include_adult": "false",
        },
    ).get("results", [])

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

def search_tv(title: str):
    return tmdb_get(
        "/search/tv",
        {
            "query": title,
            "include_adult": "false",
        },
    ).get("results", [])

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

def make_candidate(
    item: dict,
    media_type: str,
):
    if not item.get("poster_path"):
        return None

    if media_type == "movie":
        name = item.get("title")
        original = item.get(
            "original_title"
        )
        date = item.get(
            "release_date",
            "",
        )
    else:
        name = item.get("name")
        original = item.get(
            "original_name"
        )
        date = item.get(
            "first_air_date",
            "",
        )

    return {
        "media_type": media_type,
        "id": item.get("id"),
        "title": name,
        "original_title": original,
        "year": date[:4] if date else "",
        "poster_path": item.get(
            "poster_path"
        ),
        "overview": item.get(
            "overview",
            "",
        ),
    }

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

def search_media(title: str):
    title = clean_title(title)

    if not title:
        return None

    movies = search_movie(title)
    tvs = search_tv(title)

    candidates = []

    for item in movies:
        candidate = make_candidate(
            item,
            "movie",
        )

        if candidate:
            candidates.append(candidate)

    for item in tvs:
        candidate = make_candidate(
            item,
            "tv",
        )

        if candidate:
            candidates.append(candidate)

    if not candidates:
        return None

    # Prefer exact title matches.
    normalized = title.lower().strip()

    for candidate in candidates:
        candidate_title = (
            candidate["title"] or ""
        ).lower().strip()

        original_title = (
            candidate["original_title"]
            or ""
        ).lower().strip()

        if (
            candidate_title == normalized
            or original_title == normalized
        ):
            return candidate

    return candidates[0]

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

def image_url(path: Optional[str]):
    if not path:
        return None

    return IMAGE_BASE + path

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

def get_media_images(media: dict):
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
            item.get("file_path")
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
            item.get("file_path")
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
            item.get("file_path")
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
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

def sort_artwork(items):
    return sorted(
        items,
        key=lambda item: (
            item.get("width", 0)
            * item.get("height", 0)
        ),
        reverse=True,
    )

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

def get_best_artwork(media):
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

    # One best image from each category.
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
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

def get_tv_details(media):
    if media["media_type"] != "tv":
        return None

    return tmdb_get(
        f"/tv/{media['id']}"
    )

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

def get_seasons(media):
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

        # Skip specials.
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
# Don't Remove Credit
# Owner @Mr_Mohammed_29
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
            return image_url(path)

    # Fallback to season poster_path.
    path = data.get(
        "poster_path"
    )

    return image_url(path)

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
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
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

def media_title(
    media,
    season=None,
):
    title = (
        media.get("title")
        or media.get("original_title")
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

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

def build_caption(
    media,
    platform,
    artwork,
):
    current_type = html.escape(
        artwork["type"]
    )

    title = media_title(
        media,
        artwork.get("season"),
    )

    platform = html.escape(
        platform
    )

    return (
        f"<b>{platform} Poster:</b>\n\n"
        f"<b>Current:</b> "
        f"{current_type}\n\n"
        f"<b>{title}</b>\n\n"
        "Powered by TMDB."
    )

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #
