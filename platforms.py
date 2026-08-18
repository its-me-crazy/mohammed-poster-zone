# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

from urllib.parse import urlparse

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

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

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

def normalize_domain(domain: str) -> str:
    domain = domain.lower().strip()

    if domain.startswith("www."):
        domain = domain[4:]

    return domain

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

def detect_platform(url: str) -> str:
    try:
        hostname = urlparse(url).hostname

        if not hostname:
            return "Unknown Platform"

        hostname = normalize_domain(hostname)

        for platform, domains in SUPPORTED_PLATFORMS.items():
            for domain in domains:
                domain = normalize_domain(domain)

                if (
                    hostname == domain
                    or hostname.endswith("." + domain)
                ):
                    return platform

    except Exception:
        pass

    return "Unknown Platform"

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #

def get_platforms_text() -> str:
    return "\n".join(
        f"{index:02d}. {name}"
        for index, name in enumerate(
            SUPPORTED_PLATFORMS.keys(),
            start=1,
        )
    )

# ------------------------- #
# Don't Remove Credit
# Owner @Mr_Mohammed_29
# ------------------------- #
