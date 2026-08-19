# ============================================================
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ============================================================

from urllib.parse import urlparse

SUPPORTED_PLATFORMS = {

    "AaoNXT": [
        "aaonxt.com",
    ],

    "Addatimes": [
        "addatimes.com",
    ],

    "Aha": [
        "aha.video",
        "aha.com",
    ],

    "Airtel Xstream": [
        "airtelxstream.in",
        "xstreamplay.com",
    ],

    "Prime Video": [
        "primevideo.com",
        "amazon.com",
        "amazon.in",
    ],

    "Apple TV+": [
        "tv.apple.com",
    ],

    "Atrangii": [
        "atrangii.com",
    ],

    "BookMyShow Stream": [
        "bookmyshow.com",
    ],

    "BongoBD": [
        "bongobd.com",
    ],

    "Chaupal": [
        "chaupal.tv",
    ],

    "Chorki": [
        "chorki.com",
    ],

    "Crunchyroll": [
        "crunchyroll.com",
    ],

    "Dangal Play": [
        "dangalplay.com",
    ],

    "Discovery+": [
        "discoveryplus.com",
    ],

    "District": [
        "district.in",
    ],

    "Eros Now": [
        "erosnow.com",
    ],

    "Hoichoi": [
        "hoichoi.tv",
    ],

    "Disney+ Hotstar": [
        "hotstar.com",
        "disneyplus.com",
    ],

    "Hulu": [
        "hulu.com",
    ],

    "Hungama Play": [
        "hungama.com",
        "hungama.org",
    ],

    "iQIYI": [
        "iq.com",
        "iqiyi.com",
    ],

    "Iscreen": [
        "iscreen.com.pk",
    ],

    "JioCinema": [
        "jiocinema.com",
    ],

    "JioStar": [
        "jiostar.com",
    ],

    "Klikk": [
        "klikk.tv",
    ],

    "Lionsgate Play": [
        "lionsgateplay.com",
    ],

    "MUBI": [
        "mubi.com",
    ],

    "MX Player": [
        "mxplayer.in",
    ],

    "Netflix": [
        "netflix.com",
    ],

    "Playflix": [
        "playflix.com",
    ],

    "Saina Play": [
        "sainaplay.com",
    ],

    "ShemarooMe": [
        "shemaroome.com",
    ],

    "SonyLIV": [
        "sonyliv.com",
    ],

    "Sun NXT": [
        "sunnxt.com",
    ],

    "Tata Play Binge": [
        "tataplaybinge.com",
    ],

    "Ultra Play": [
        "ultraplay.in",
    ],

    "Viki": [
        "viki.com",
    ],

    "Viu": [
        "viu.com",
    ],

    "Vivamax": [
        "vivamax.net",
    ],

    "WeTV": [
        "wetv.vip",
    ],

    "YouTube": [
        "youtube.com",
        "youtu.be",
    ],

    "ZEE5": [
        "zee5.com",
    ],
}


# ============================================================
# NORMALIZE DOMAIN
# ============================================================

def normalize_domain(
    domain: str,
) -> str:
    """
    Normalize a hostname.

    Example:

        WWW.Netflix.com
        ->
        netflix.com
    """

    if not domain:
        return ""

    domain = (
        str(domain)
        .lower()
        .strip()
        .rstrip(".")
    )

    if domain.startswith(
        "www."
    ):
        domain = domain[4:]

    return domain


# ============================================================
# DETECT PLATFORM
# ============================================================

def detect_platform(
    url: str,
) -> str:
    """
    Detect the OTT/platform name from a URL.

    Example:

        https://www.netflix.com/title/123
        -> Netflix

        https://www.primevideo.com/detail/...
        -> Prime Video
    """

    try:

        if not url:
            return "Unknown Platform"

        url = str(
            url
        ).strip()

        # ----------------------------------------------------
        # Make sure URL has a scheme.
        # ----------------------------------------------------

        if not url.startswith(
            (
                "http://",
                "https://",
            )
        ):
            url = (
                "https://"
                + url
            )

        parsed = urlparse(
            url
        )

        hostname = parsed.hostname

        if not hostname:
            return "Unknown Platform"

        hostname = normalize_domain(
            hostname
        )

        # ----------------------------------------------------
        # Check every supported platform.
        # ----------------------------------------------------

        for (
            platform,
            domains,
        ) in SUPPORTED_PLATFORMS.items():

            for domain in domains:

                domain = normalize_domain(
                    domain
                )

                if not domain:
                    continue

                # Exact domain
                if hostname == domain:
                    return platform

                # Subdomain
                #
                # Example:
                # www.netflix.com
                # -> netflix.com
                #
                # Example:
                # help.netflix.com
                # -> netflix.com
                if hostname.endswith(
                    "." + domain
                ):
                    return platform

    except Exception:
        pass

    return "Unknown Platform"


# ============================================================
# GET PLATFORM DOMAINS
# ============================================================

def get_platform_domains(
    platform: str,
):
    """
    Return domains belonging to a platform.
    """

    if not platform:
        return []

    for (
        name,
        domains,
    ) in SUPPORTED_PLATFORMS.items():

        if name.lower() == str(
            platform
        ).lower().strip():

            return list(
                domains
            )

    return []


# ============================================================
# IS SUPPORTED URL
# ============================================================

def is_supported_url(
    url: str,
) -> bool:
    """
    Return True when URL belongs
    to a supported platform.
    """

    return (
        detect_platform(url)
        != "Unknown Platform"
    )


# ============================================================
# GET ALL PLATFORM NAMES
# ============================================================

def get_platform_names():
    """
    Return all supported platform names.
    """

    return list(
        SUPPORTED_PLATFORMS.keys()
    )


# ============================================================
# PLATFORMS TEXT
# ============================================================

def get_platforms_text() -> str:
    """
    Generate /platforms output.
    """

    lines = []

    for (
        index,
        name,
    ) in enumerate(
        SUPPORTED_PLATFORMS.keys(),
        start=1,
    ):

        lines.append(
            f"{index:02d}. {name}"
        )

    return "\n".join(
        lines
    )
