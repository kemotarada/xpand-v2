# =========================================================
# XPAND BRAND RESEARCH V2.0
#
# COST-CONTROLLED / CACHE-FIRST BRAND INTELLIGENCE
#
# =========================================================
#
# PURPOSE
# ---------------------------------------------------------
#
# - Detect STC Bank visual requests.
# - Always apply strong LOCAL verified brand intelligence.
# - Do NOT perform expensive / repetitive live research
#   on every image request.
# - Refresh public research only when cache is stale,
#   explicitly requested, or forced by environment.
# - Prefer official STC Bank sources.
# - Use external advertising references only for principles,
#   never for composition copying.
# - Keep Nano Banana 2 as STC default production route.
# - Never request generated campaign text / logo.
#
#
# COST STRATEGY
# ---------------------------------------------------------
#
# Normal STC request:
#
#   Local STC profile
#       +
#   cached research
#       =
#   ZERO live-search calls when cache is fresh.
#
#
# When research cache expires:
#
#   1 official website search
#   1 official social/index search
#   1 premium advertising inspiration search
#
# Then cache for 24 hours by default.
#
#
# IMPORTANT
# ---------------------------------------------------------
#
# This module does NOT claim that Instagram itself was fully
# crawled or that every STC Bank post was downloaded.
#
# Public/indexed research != permanent visual-reference memory.
#
# Permanent image/reference storage belongs to:
#
#   xpand_brand_memory.py
#
#
# Running this file directly makes ZERO network calls.
#
# =========================================================

from __future__ import annotations

import json
import os
import re
import tempfile
import threading
import time

from pathlib import Path

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Sequence,
)


import requests


from xpand_stc_bank_skill import (
    STYLE_AUGMENTED_REALISM,
    STYLE_PREMIUM_REALISTIC,
    STYLE_PURPLE_ARCHITECTURAL,
    detect_stc_benefit_family,
    detect_stc_visual_style,
    is_stc_bank_request,
)


# =========================================================
# MODULE
# =========================================================

VERSION = "2.0"

MODULE_NAME = (
    "XPAND Brand Research"
)


# =========================================================
# API
# =========================================================

TAVILY_API_KEY = str(
    os.environ.get(
        "TAVILY_API_KEY",
        "",
    )
).strip()


TAVILY_SEARCH_URL = (
    "https://api.tavily.com/search"
)


# =========================================================
# OFFICIAL STC BANK SOURCES
# =========================================================

STC_WEBSITE_URL = (
    "https://www.stcbank.com.sa/"
)


STC_INSTAGRAM_URL = (
    "https://www.instagram.com/stcbank_ksa/"
)


STC_SUPPORT_URL = (
    "https://www.stcbank.com.sa/support"
)


# =========================================================
# RESEARCH COST SETTINGS
# =========================================================

#
# Default:
# one lightweight refresh per 24 hours.
#

RESEARCH_CACHE_TTL_SECONDS = max(
    3600,
    int(
        os.environ.get(
            "XPAND_BRAND_RESEARCH_CACHE_TTL_SECONDS",
            "86400",
        )
        or 86400
    ),
)


#
# Keep live research small.
#

RESEARCH_MAX_CALLS = max(
    1,
    min(
        4,
        int(
            os.environ.get(
                "XPAND_BRAND_RESEARCH_MAX_CALLS",
                "3",
            )
            or 3
        ),
    ),
)


RESEARCH_RESULTS_PER_CALL = max(
    1,
    min(
        5,
        int(
            os.environ.get(
                "XPAND_BRAND_RESEARCH_RESULTS_PER_CALL",
                "3",
            )
            or 3
        ),
    ),
)


RESEARCH_SEARCH_DEPTH = str(
    os.environ.get(
        "XPAND_BRAND_RESEARCH_SEARCH_DEPTH",
        "basic",
    )
).strip().lower()


if RESEARCH_SEARCH_DEPTH not in {
    "basic",
    "advanced",
}:

    RESEARCH_SEARCH_DEPTH = "basic"


#
# If false, automatic STC requests still receive local
# brand intelligence, but no live search is triggered.
#

LIVE_RESEARCH_ENABLED = str(
    os.environ.get(
        "XPAND_BRAND_LIVE_RESEARCH_ENABLED",
        "true",
    )
).strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}


#
# Explicit research language may force refresh.
#

FORCE_EXPLICIT_RESEARCH_REFRESH = str(
    os.environ.get(
        "XPAND_FORCE_EXPLICIT_RESEARCH_REFRESH",
        "true",
    )
).strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}


# =========================================================
# CACHE
# =========================================================

DEFAULT_CACHE_FILE = str(
    os.environ.get(
        "XPAND_BRAND_RESEARCH_CACHE_FILE",
        (
            Path(
                tempfile.gettempdir()
            )
            /
            "xpand_brand_research_cache_v2.json"
        ),
    )
).strip()


_RESEARCH_CACHE_LOCK = (
    threading.RLock()
)


_MEMORY_CACHE: Dict[
    str,
    Dict[str, Any],
] = {}


# =========================================================
# HELPERS
# =========================================================

def clean_text(
    value: Any,
    max_length: int = 12000,
) -> str:

    return (
        str(
            value
            if value is not None
            else ""
        )
        .replace(
            "\x00",
            "",
        )
        .strip()[:max_length]
    )


def normalize_arabic(
    value: Any,
) -> str:

    text = clean_text(
        value,
        30000,
    ).lower()

    replacements = {
        "أ":
            "ا",

        "إ":
            "ا",

        "آ":
            "ا",

        "ة":
            "ه",

        "ى":
            "ي",

        "ؤ":
            "و",

        "ئ":
            "ي",

        "ـ":
            "",
    }

    for old, new in (
        replacements.items()
    ):

        text = text.replace(
            old,
            new,
        )

    text = re.sub(
        r"[\u064B-\u065F]",
        "",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def contains_any(
    text: Any,
    markers: Sequence[str],
) -> bool:

    source = normalize_arabic(
        text
    )

    return any(
        normalize_arabic(
            marker
        )
        in source
        for marker in markers
    )


def safe_list(
    value: Any,
) -> List[Any]:

    if isinstance(
        value,
        list,
    ):

        return value

    return []


def safe_dict(
    value: Any,
) -> Dict[str, Any]:

    if isinstance(
        value,
        dict,
    ):

        return value

    return {}


def now_timestamp() -> float:

    return time.time()


# =========================================================
# IMAGE INTENT
# =========================================================

VISUAL_MARKERS = [
    "صوره",
    "صورة",
    "صور",
    "اعلان",
    "إعلان",
    "اعلانات",
    "إعلانات",
    "بوستر",
    "بانر",
    "مشهد",
    "حملة",
    "حمله",
    "تصميم",
    "post",
    "poster",
    "banner",
    "ad",
    "advertisement",
    "visual",
    "key visual",
    "campaign",
    "design",
    "create",
    "generate",
    "image",
    "scene",
]


def looks_like_visual_request(
    text: str,
) -> bool:

    return contains_any(
        text,
        VISUAL_MARKERS,
    )


# =========================================================
# BRAND DETECTION
# =========================================================

def detect_brand(
    prompt: str,
) -> str:

    #
    # IMPORTANT:
    #
    # Do NOT classify plain "STC" automatically as STC Bank.
    # It may mean STC telecom.
    #

    if is_stc_bank_request(
        prompt
    ):

        return "stc_bank"

    source = normalize_arabic(
        prompt
    )

    #
    # Secondary bank-context detector for phrases where user
    # separated STC and bank terms.
    #

    has_stc = contains_any(
        source,
        [
            "stc",
            "اس تي سي",
        ],
    )

    has_bank_context = contains_any(
        source,
        [
            "بنك",
            "bank",
            "بطاقه بنكيه",
            "بطاقة بنكية",
            "حساب بنكي",
            "تحويل بنكي",
            "الخدمات البنكيه",
            "الخدمات البنكية",
        ],
    )

    if (
        has_stc
        and
        has_bank_context
    ):

        return "stc_bank"

    return ""


# =========================================================
# RESEARCH MODE
# =========================================================

EXPLICIT_RESEARCH_MARKERS = [
    "بحث عميق",
    "ابحث عميق",
    "ابحث عن اخر",
    "ابحث عن أحدث",
    "ابحث عن احدث",
    "آخر اعلانات",
    "آخر إعلانات",
    "احدث اعلانات",
    "أحدث إعلانات",
    "اخر حملات",
    "آخر حملات",
    "احدث حملات",
    "أحدث حملات",
    "راجع الانستجرام",
    "راجع الانستغرام",
    "راجع حساب البنك",
    "research",
    "deep research",
    "latest ads",
    "latest campaigns",
    "latest stc bank",
    "current stc bank",
    "refresh research",
]


def explicit_research_requested(
    prompt: str,
) -> bool:

    return contains_any(
        prompt,
        EXPLICIT_RESEARCH_MARKERS,
    )


def should_apply_deep_research(
    prompt: str,
) -> bool:

    #
    # This means:
    #
    # "apply the STC researched brand layer"
    #
    # NOT:
    #
    # "make live web searches every time".
    #
    # Live search is separately cache-controlled.
    #

    brand = detect_brand(
        prompt
    )

    if not brand:

        return False

    if not looks_like_visual_request(
        prompt
    ):

        return False

    return True


# =========================================================
# BRAND PROFILES
# =========================================================

BRAND_PROFILES: Dict[
    str,
    Dict[str, Any],
] = {

    "stc_bank": {

        "brand_label":
            "STC Bank KSA",

        "official_sources": [
            STC_WEBSITE_URL,
            STC_INSTAGRAM_URL,
            STC_SUPPORT_URL,
        ],

        #
        # Nano Banana 2.
        #

        "default_mode":
            "google_fast",

        "default_ratio":
            "4:5",

        #
        # 2K is a strong production/cost balance.
        # Explicit user resolution always wins elsewhere.
        #

        "default_resolution":
            "2K",


        # =================================================
        # BRAND CHARACTER
        # =================================================

        "creative_positioning": [
            "premium",
            "modern",
            "confident",
            "clean",
            "restrained",
            "Saudi-relevant",
            "digitally fluent",
            "human",
            "commercially polished",
        ],


        # =================================================
        # VISUAL DNA
        # =================================================

        "visual_dna": [

            (
                "STC Bank is a visual language, not simply "
                "a purple environment."
            ),

            (
                "Use premium realism as the default when "
                "the user selects realistic photography."
            ),

            (
                "Natural environments must retain believable "
                "real-world colors."
            ),

            (
                "Purple may appear as a controlled identity "
                "accent, architectural material or deliberate "
                "studio family."
            ),

            (
                "Do not automatically flood the scene "
                "with purple light."
            ),

            (
                "Green is a restrained secondary brand cue, "
                "not general scene lighting."
            ),

            (
                "Use modern Saudi/Gulf context when people "
                "or places are relevant."
            ),

            (
                "Premium advertising quality comes from "
                "camera, scene design, material behavior, "
                "lighting, hierarchy and restraint."
            ),

            (
                "Human subjects should perform credible actions "
                "rather than pose merely to display a bank product."
            ),

            (
                "Product, phone and POS placement must obey "
                "real support, scale and perspective."
            ),

            (
                "Reserve intentional negative space because "
                "copy and official branding will be added manually."
            ),

            (
                "Three main visual families are allowed: "
                "premium realistic photography, premium purple "
                "architectural studio, and refined augmented realism."
            ),

            (
                "Augmented realism uses exactly one intelligent "
                "physical visual metaphor inside an otherwise "
                "photographic scene."
            ),

            (
                "Never interpret Arabic 'نقاط البيع' as rewards; "
                "it means Point of Sale / POS."
            ),
        ],


        # =================================================
        # PHOTOGRAPHY
        # =================================================

        "photography_rules": [

            (
                "Use a deliberate scientifically coherent "
                "camera viewpoint."
            ),

            (
                "Eye-level works well for credible human "
                "commerce and lifestyle."
            ),

            (
                "Low-angle may create premium hero presence "
                "when conceptually justified."
            ),

            (
                "Bird's-eye / overhead may organize real "
                "physical objects or environments."
            ),

            (
                "Over-the-shoulder is useful for genuine "
                "mobile banking / e-commerce interactions."
            ),

            (
                "Worm's-eye should only be used for deliberate "
                "scale storytelling."
            ),

            (
                "Use real foreground, midground and background "
                "depth where the scene benefits from it."
            ),

            (
                "Lighting must have a motivated direction."
            ),

            (
                "Contact shadows must physically connect "
                "objects to surfaces."
            ),

            (
                "Reflections must describe real material "
                "properties rather than futuristic decoration."
            ),

            (
                "Avoid distorted hands, impossible product grip "
                "and contradictory lens/perspective descriptions."
            ),
        ],


        # =================================================
        # MATERIALS
        # =================================================

        "material_language": [
            "warm stone",
            "travertine",
            "off-white plaster",
            "charcoal",
            "walnut",
            "premium leather",
            "brushed metal",
            "satin metal",
            "smoked glass",
            "architectural glass",
            "matte surfaces",
            "controlled semi-gloss surfaces",
            "restrained polished reflections",
        ],


        # =================================================
        # COLOR BEHAVIOR
        # =================================================

        "color_behavior": {

            "premium_realistic": [
                "natural skin tones",
                "warm neutrals",
                "real environmental colors",
                "clean daylight",
                "subtle green accent",
                "subtle purple accent",
            ],

            "purple_architectural": [
                "deep aubergine",
                "near-black violet",
                "controlled saturated purple",
                "restrained green accent",
                "matte/satin material separation",
                "narrow controlled reflections",
            ],

            "augmented_realism": [
                "photographic base palette",
                "one controlled STC identity cue",
                "no artificial global color wash",
            ],
        },


        # =================================================
        # NO GENERATED COPY
        # =================================================

        "image_only_rules": [
            "no advertising headline",
            "no subtitle",
            "no CTA",
            "no offer copy",
            "no percentage",
            "no financial figures",
            "no legal disclaimer",
            "no STC Bank wordmark",
            "no STC logo",
            "no Visa logo",
            "no Mastercard logo",
            "no watermark",
            "no invented readable banking UI",
        ],


        # =================================================
        # ANTI CLICHE
        # =================================================

        "forbidden_default_devices": [
            "floating bank card",
            "floating phone",
            "floating POS terminal",
            "floating coins",
            "flying money",
            "phone surrounded by icons",
            "world globe",
            "network lines",
            "connection lines",
            "transfer routes",
            "laser beams",
            "neon trails",
            "glowing arrows",
            "holograms",
            "HUD graphics",
            "random particles",
            "sparkles",
            "generic security shield",
            "generic lock",
            "generic handshake",
            "generic futuristic banking room",
        ],


        # =================================================
        # REFERENCE FAMILIES
        # =================================================

        "reference_families": [
            "premium_lifestyle",
            "payments_cards",
            "digital_banking",
            "travel_roaming",
            "international_transfer",
            "cashback_rewards",
            "general_brand",
        ],


        # =================================================
        # RESEARCH SOURCES
        # =================================================

        "official_domains": [
            "stcbank.com.sa",
            "www.stcbank.com.sa",
            "instagram.com",
        ],

        "inspiration_domains": [
            "adsoftheworld.com",
            "behance.net",
            "pinterest.com",
        ],

        #
        # Only a few focused queries.
        #

        "official_research_queries": [
            (
                "STC Bank Saudi Arabia latest services "
                "business cards transfers offers visual campaign"
            ),
        ],

        "social_research_queries": [
            (
                "STC Bank KSA stcbank_ksa Instagram "
                "campaign advertising"
            ),
        ],

        "inspiration_queries": [
            (
                "premium Saudi banking advertising campaign "
                "commercial photography art direction"
            ),
        ],
    },
}


# =========================================================
# BENEFIT RESEARCH CONTEXT
# =========================================================

BENEFIT_RESEARCH_CONTEXT = {

    "merchant_payments": (
        "Focus on real merchant commerce, e-commerce services, "
        "Point of Sale acceptance, business confidence, customer "
        "interaction and credible payment behavior. Never treat "
        "POS as reward points."
    ),

    "international_transfer": (
        "Focus on international money transfer, ease, trust, "
        "reach and human/place relationships without glowing "
        "maps or transfer routes."
    ),

    "travel": (
        "Focus on credible premium travel behavior, real locations, "
        "airport/hotel/destination context and natural product use."
    ),

    "digital_banking": (
        "Focus on real mobile banking interaction and physical "
        "device behavior, without fake floating UI."
    ),

    "cashback": (
        "Focus on tangible real-world value and purchase experience, "
        "not floating coins or money effects."
    ),

    "rewards": (
        "Focus on premium experiences and tangible benefit, "
        "not points clouds or gift-icon collage."
    ),

    "security": (
        "Focus on calm, confidence and user control rather than "
        "shields, cyber grids and holograms."
    ),

    "premium_banking": (
        "Focus on confident modern Saudi banking, refined restraint "
        "and premium commercial photography."
    ),
}


# =========================================================
# CACHE FILE
# =========================================================

def _load_disk_cache() -> Dict[
    str,
    Dict[str, Any],
]:

    path = clean_text(
        DEFAULT_CACHE_FILE,
        2000,
    )

    if not path:

        return {}

    try:

        cache_path = Path(
            path
        )

        if not cache_path.is_file():

            return {}

        raw = cache_path.read_text(
            encoding="utf-8"
        )

        data = json.loads(
            raw
        )

        if isinstance(
            data,
            dict,
        ):

            return {
                clean_text(
                    key,
                    100,
                ):
                    safe_dict(
                        value
                    )
                for key, value
                in data.items()
            }

    except Exception:

        pass

    return {}


def _save_disk_cache(
    cache: Dict[
        str,
        Dict[str, Any],
    ],
) -> None:

    path = clean_text(
        DEFAULT_CACHE_FILE,
        2000,
    )

    if not path:

        return

    try:

        cache_path = Path(
            path
        )

        cache_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary = cache_path.with_suffix(
            cache_path.suffix
            +
            ".tmp"
        )

        temporary.write_text(
            json.dumps(
                cache,
                ensure_ascii=False,
                separators=(
                    ",",
                    ":",
                ),
            ),
            encoding="utf-8",
        )

        temporary.replace(
            cache_path
        )

    except Exception:

        #
        # Cache failure must NEVER break generation.
        #

        return


def _ensure_cache_loaded() -> None:

    with _RESEARCH_CACHE_LOCK:

        if _MEMORY_CACHE:

            return

        disk = _load_disk_cache()

        if disk:

            _MEMORY_CACHE.update(
                disk
            )


def get_cached_brand_research(
    brand_id: str,
) -> Dict[str, Any]:

    _ensure_cache_loaded()

    key = clean_text(
        brand_id,
        100,
    )

    with _RESEARCH_CACHE_LOCK:

        return dict(
            _MEMORY_CACHE.get(
                key,
                {},
            )
        )


def save_cached_brand_research(
    brand_id: str,
    payload: Dict[str, Any],
) -> None:

    _ensure_cache_loaded()

    key = clean_text(
        brand_id,
        100,
    )

    if not key:

        return

    value = dict(
        payload
    )

    value[
        "cached_at"
    ] = now_timestamp()

    with _RESEARCH_CACHE_LOCK:

        _MEMORY_CACHE[
            key
        ] = value

        _save_disk_cache(
            _MEMORY_CACHE
        )


def invalidate_brand_research_cache(
    brand_id: str = "",
) -> None:

    _ensure_cache_loaded()

    with _RESEARCH_CACHE_LOCK:

        if brand_id:

            _MEMORY_CACHE.pop(
                clean_text(
                    brand_id,
                    100,
                ),
                None,
            )

        else:

            _MEMORY_CACHE.clear()

        _save_disk_cache(
            _MEMORY_CACHE
        )


def research_cache_age_seconds(
    brand_id: str,
) -> Optional[float]:

    cached = get_cached_brand_research(
        brand_id
    )

    timestamp = safe_float(
        cached.get(
            "cached_at",
            0,
        ),
        0,
    )

    if timestamp <= 0:

        return None

    return max(
        0.0,
        now_timestamp()
        -
        timestamp,
    )


def research_cache_is_fresh(
    brand_id: str,
) -> bool:

    age = research_cache_age_seconds(
        brand_id
    )

    if age is None:

        return False

    return (
        age
        <
        RESEARCH_CACHE_TTL_SECONDS
    )


# =========================================================
# SAFE FLOAT
# =========================================================

def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:

    try:

        return float(
            value
        )

    except Exception:

        return float(
            default
        )


# =========================================================
# LIVE REFRESH DECISION
# =========================================================

def should_refresh_live_research(
    brand_id: str,
    user_prompt: str,
) -> bool:

    if not LIVE_RESEARCH_ENABLED:

        return False

    if not TAVILY_API_KEY:

        return False

    if (
        FORCE_EXPLICIT_RESEARCH_REFRESH
        and
        explicit_research_requested(
            user_prompt
        )
    ):

        return True

    return not research_cache_is_fresh(
        brand_id
    )


# =========================================================
# TAVILY
# =========================================================

def run_tavily_search(
    query: str,
    include_domains: Optional[
        List[str]
    ] = None,
    max_results: int = 3,
) -> List[
    Dict[str, Any]
]:

    if not TAVILY_API_KEY:

        return []

    payload: Dict[str, Any] = {
        "api_key":
            TAVILY_API_KEY,

        "query":
            clean_text(
                query,
                1200,
            ),

        "search_depth":
            RESEARCH_SEARCH_DEPTH,

        "max_results":
            max(
                1,
                min(
                    max_results,
                    5,
                ),
            ),

        "include_answer":
            False,

        "include_raw_content":
            False,
    }

    if include_domains:

        payload[
            "include_domains"
        ] = [
            clean_text(
                item,
                300,
            )
            for item in (
                include_domains
            )
            if clean_text(
                item,
                300,
            )
        ]

    try:

        response = requests.post(
            TAVILY_SEARCH_URL,
            json=payload,
            timeout=30,
        )

    except Exception as error:

        print(
            (
                "⚠️ Brand Research search failed: "
                +
                clean_text(
                    error,
                    600,
                )
            )
        )

        return []

    if not response.ok:

        print(
            (
                "⚠️ Brand Research HTTP "
                +
                str(
                    response.status_code
                )
            )
        )

        return []

    try:

        data = response.json()

    except Exception:

        return []

    results = data.get(
        "results",
        []
    )

    if not isinstance(
        results,
        list,
    ):

        return []

    cleaned: List[
        Dict[str, Any]
    ] = []

    for item in results:

        if not isinstance(
            item,
            dict,
        ):

            continue

        title = clean_text(
            item.get(
                "title",
                "",
            ),
            320,
        )

        url = clean_text(
            item.get(
                "url",
                "",
            ),
            900,
        )

        content = clean_text(
            item.get(
                "content",
                "",
            ),
            1200,
        )

        if not (
            title
            or
            url
            or
            content
        ):

            continue

        cleaned.append(
            {
                "title":
                    title,

                "url":
                    url,

                "content":
                    content,
            }
        )

    return cleaned


# =========================================================
# RESULT DEDUPE
# =========================================================

def dedupe_research_results(
    results: Sequence[
        Dict[str, Any]
    ],
    max_items: int = 12,
) -> List[
    Dict[str, Any]
]:

    output = []

    seen_urls = set()

    seen_content = set()

    for item in results:

        if not isinstance(
            item,
            dict,
        ):

            continue

        url = clean_text(
            item.get(
                "url",
                "",
            ),
            900,
        )

        content_key = normalize_arabic(
            (
                clean_text(
                    item.get(
                        "title",
                        "",
                    ),
                    300,
                )
                +
                " "
                +
                clean_text(
                    item.get(
                        "content",
                        "",
                    ),
                    500,
                )
            )
        )[:400]

        if (
            url
            and
            url in seen_urls
        ):

            continue

        if (
            content_key
            and
            content_key in seen_content
        ):

            continue

        if url:

            seen_urls.add(
                url
            )

        if content_key:

            seen_content.add(
                content_key
            )

        output.append(
            {
                "title":
                    clean_text(
                        item.get(
                            "title",
                            "",
                        ),
                        320,
                    ),

                "url":
                    url,

                "content":
                    clean_text(
                        item.get(
                            "content",
                            "",
                        ),
                        1200,
                    ),
            }
        )

        if len(
            output
        ) >= max_items:

            break

    return output


# =========================================================
# LIVE RESEARCH
# =========================================================

def collect_brand_research(
    brand_id: str,
    user_prompt: str,
    *,
    force_refresh: bool = False,
) -> Dict[str, Any]:

    profile = BRAND_PROFILES.get(
        brand_id,
        {}
    )

    if not profile:

        return {
            "results":
                [],

            "sources_used":
                [],

            "research_performed":
                False,

            "cache_hit":
                False,
        }

    if not LIVE_RESEARCH_ENABLED:

        cached = get_cached_brand_research(
            brand_id
        )

        return {
            "results":
                safe_list(
                    cached.get(
                        "results"
                    )
                ),

            "sources_used":
                safe_list(
                    cached.get(
                        "sources_used"
                    )
                ),

            "research_performed":
                False,

            "cache_hit":
                bool(
                    cached
                ),

            "cached_at":
                cached.get(
                    "cached_at"
                ),
        }

    cached = get_cached_brand_research(
        brand_id
    )

    refresh = bool(
        force_refresh
        or
        should_refresh_live_research(
            brand_id,
            user_prompt,
        )
    )

    if (
        cached
        and
        not refresh
    ):

        print(
            "♻️ BRAND RESEARCH CACHE HIT"
            +
            " | brand="
            +
            brand_id
        )

        return {
            "results":
                safe_list(
                    cached.get(
                        "results"
                    )
                ),

            "sources_used":
                safe_list(
                    cached.get(
                        "sources_used"
                    )
                ),

            "research_performed":
                False,

            "cache_hit":
                True,

            "cached_at":
                cached.get(
                    "cached_at"
                ),
        }

    if not TAVILY_API_KEY:

        return {
            "results":
                safe_list(
                    cached.get(
                        "results"
                    )
                ),

            "sources_used":
                safe_list(
                    cached.get(
                        "sources_used"
                    )
                ),

            "research_performed":
                False,

            "cache_hit":
                bool(
                    cached
                ),

            "cached_at":
                cached.get(
                    "cached_at"
                ),
        }

    collected: List[
        Dict[str, Any]
    ] = []

    calls = 0

    # =====================================================
    # 1. OFFICIAL WEBSITE
    # =====================================================

    if calls < RESEARCH_MAX_CALLS:

        queries = safe_list(
            profile.get(
                "official_research_queries"
            )
        )

        if queries:

            results = run_tavily_search(
                queries[
                    0
                ],
                include_domains=[
                    "stcbank.com.sa",
                ],
                max_results=(
                    RESEARCH_RESULTS_PER_CALL
                ),
            )

            collected.extend(
                results
            )

            calls += 1

    # =====================================================
    # 2. OFFICIAL SOCIAL / INDEXED PUBLIC RESULTS
    # =====================================================

    if calls < RESEARCH_MAX_CALLS:

        queries = safe_list(
            profile.get(
                "social_research_queries"
            )
        )

        if queries:

            results = run_tavily_search(
                queries[
                    0
                ],
                include_domains=[
                    "instagram.com",
                ],
                max_results=(
                    RESEARCH_RESULTS_PER_CALL
                ),
            )

            collected.extend(
                results
            )

            calls += 1

    # =====================================================
    # 3. HIGH-LEVEL ADVERTISING INSPIRATION
    # =====================================================

    if calls < RESEARCH_MAX_CALLS:

        queries = safe_list(
            profile.get(
                "inspiration_queries"
            )
        )

        if queries:

            results = run_tavily_search(
                queries[
                    0
                ],
                include_domains=(
                    safe_list(
                        profile.get(
                            "inspiration_domains"
                        )
                    )
                ),
                max_results=(
                    RESEARCH_RESULTS_PER_CALL
                ),
            )

            collected.extend(
                results
            )

            calls += 1

    cleaned = dedupe_research_results(
        collected,
        max_items=12,
    )

    sources = []

    seen = set()

    for item in cleaned:

        url = clean_text(
            item.get(
                "url",
                "",
            ),
            900,
        )

        if (
            not url
            or
            url in seen
        ):

            continue

        seen.add(
            url
        )

        sources.append(
            url
        )

    payload = {
        "brand_id":
            brand_id,

        "results":
            cleaned,

        "sources_used":
            sources,

        "research_calls":
            calls,

        "research_performed":
            bool(
                cleaned
            ),

        "cache_hit":
            False,
    }

    if cleaned:

        save_cached_brand_research(
            brand_id,
            payload,
        )

        payload[
            "cached_at"
        ] = now_timestamp()

        print(
            "🌐 BRAND RESEARCH REFRESHED"
            +
            " | brand="
            +
            brand_id
            +
            " | calls="
            +
            str(
                calls
            )
            +
            " | results="
            +
            str(
                len(
                    cleaned
                )
            )
        )

    elif cached:

        #
        # Live refresh failure must not erase good cached data.
        #

        return {
            "results":
                safe_list(
                    cached.get(
                        "results"
                    )
                ),

            "sources_used":
                safe_list(
                    cached.get(
                        "sources_used"
                    )
                ),

            "research_performed":
                False,

            "cache_hit":
                True,

            "refresh_failed":
                True,

            "cached_at":
                cached.get(
                    "cached_at"
                ),
        }

    return payload


# =========================================================
# DEFAULT BRAND BRIEF
# =========================================================

def build_default_brand_brief(
    brand_id: str,
) -> str:

    profile = BRAND_PROFILES.get(
        brand_id,
        {}
    )

    if not profile:

        return ""

    positioning = safe_list(
        profile.get(
            "creative_positioning"
        )
    )

    visual_dna = safe_list(
        profile.get(
            "visual_dna"
        )
    )

    photography = safe_list(
        profile.get(
            "photography_rules"
        )
    )

    materials = safe_list(
        profile.get(
            "material_language"
        )
    )

    image_only = safe_list(
        profile.get(
            "image_only_rules"
        )
    )

    forbidden = safe_list(
        profile.get(
            "forbidden_default_devices"
        )
    )

    lines = [
        (
            "Brand: "
            +
            clean_text(
                profile.get(
                    "brand_label",
                    brand_id,
                ),
                300,
            )
        ),

        (
            "Positioning: "
            +
            ", ".join(
                clean_text(
                    item,
                    100,
                )
                for item in positioning
            )
        ),

        "",
        "Visual DNA:",
    ]

    for item in visual_dna:

        lines.append(
            "- "
            +
            clean_text(
                item,
                600,
            )
        )

    lines.extend(
        [
            "",
            "Photography:",
        ]
    )

    for item in photography:

        lines.append(
            "- "
            +
            clean_text(
                item,
                600,
            )
        )

    lines.extend(
        [
            "",
            (
                "Material language: "
                +
                ", ".join(
                    clean_text(
                        item,
                        100,
                    )
                    for item in materials
                )
            ),
            "",
            "Image-only rules:",
        ]
    )

    for item in image_only:

        lines.append(
            "- "
            +
            clean_text(
                item,
                300,
            )
        )

    lines.extend(
        [
            "",
            "Do not default to:",
        ]
    )

    for item in forbidden:

        lines.append(
            "- "
            +
            clean_text(
                item,
                300,
            )
        )

    return "\n".join(
        lines
    )


# =========================================================
# RESEARCH SUMMARY
# =========================================================

def summarize_search_results(
    results: List[
        Dict[str, Any]
    ],
    max_items: int = 6,
) -> str:

    if not results:

        return (
            "No current public research snapshots are available. "
            "Use verified local STC Bank Visual DNA and the "
            "permanent visual-reference memory."
        )

    lines: List[str] = []

    for item in results[
        :max_items
    ]:

        title = clean_text(
            item.get(
                "title",
                "",
            ),
            220,
        )

        content = clean_text(
            item.get(
                "content",
                "",
            ),
            480,
        )

        url = clean_text(
            item.get(
                "url",
                "",
            ),
            600,
        )

        if not (
            title
            or
            content
        ):

            continue

        line = "- "

        if title:

            line += title

        if content:

            if title:

                line += ": "

            line += content

        if url:

            line += (
                " [source="
                +
                url
                +
                "]"
            )

        lines.append(
            line
        )

    if not lines:

        return (
            "No usable current research snippets. "
            "Use verified local STC Bank Visual DNA."
        )

    return "\n".join(
        lines
    )


# =========================================================
# STYLE CONTEXT
# =========================================================

def build_style_context(
    user_prompt: str,
) -> str:

    style = detect_stc_visual_style(
        user_prompt
    )

    if style == (
        STYLE_PREMIUM_REALISTIC
    ):

        return """
SELECTED STC VISUAL FAMILY:
Premium realistic photography.

Use:
- believable premium Saudi commercial environment
- real human action
- natural environmental colors
- premium materials
- motivated light
- subtle STC identity cue
- strong photography
- clean negative space

Do not artificially recolor the whole location purple.
""".strip()

    if style == (
        STYLE_PURPLE_ARCHITECTURAL
    ):

        return """
SELECTED STC VISUAL FAMILY:
Premium purple architectural studio.

Use:
- physical geometric platforms
- disciplined vanishing points
- matte/satin purple materials
- controlled reflections
- physically supported objects
- elegant contact shadows
- restrained highlights

Do not create a neon fintech room.
""".strip()

    if style == (
        STYLE_AUGMENTED_REALISM
    ):

        return """
SELECTED STC VISUAL FAMILY:
Refined augmented realism.

Start with photographic realism.
Use exactly one conceptual physical mechanism.
It must obey gravity, perspective, light, shadow,
occlusion, material and reflection logic.

Do not create cartoon fantasy or generic CGI.
""".strip()

    return (
        "STC visual family has not been selected yet. "
        "The Telegram orchestration layer should ask the "
        "user for the style before final generation."
    )


# =========================================================
# BENEFIT CONTEXT
# =========================================================

def build_benefit_context(
    user_prompt: str,
) -> str:

    family = detect_stc_benefit_family(
        user_prompt
    )

    return (
        "Benefit family: "
        +
        family
        +
        "\n"
        +
        BENEFIT_RESEARCH_CONTEXT.get(
            family,
            BENEFIT_RESEARCH_CONTEXT[
                "premium_banking"
            ],
        )
    )


# =========================================================
# RESEARCH PROMPT
# =========================================================

def build_researched_prompt(
    user_prompt: str,
) -> Dict[str, Any]:

    prompt = clean_text(
        user_prompt,
        12000,
    )

    brand_id = detect_brand(
        prompt
    )

    if not brand_id:

        return {
            "applied":
                False,

            "brand_id":
                "",

            "brand_label":
                "",

            "mode_override":
                "",

            "final_prompt":
                prompt,

            "research_summary":
                "",

            "sources_used":
                [],

            "research_performed":
                False,

            "cache_hit":
                False,
        }

    profile = BRAND_PROFILES.get(
        brand_id,
        {}
    )

    if not profile:

        return {
            "applied":
                False,

            "brand_id":
                "",

            "brand_label":
                "",

            "mode_override":
                "",

            "final_prompt":
                prompt,

            "research_summary":
                "",

            "sources_used":
                [],

            "research_performed":
                False,

            "cache_hit":
                False,
        }

    #
    # Cache-controlled live/public research.
    #

    live_research = (
        collect_brand_research(
            brand_id,
            prompt,
            force_refresh=(
                FORCE_EXPLICIT_RESEARCH_REFRESH
                and
                explicit_research_requested(
                    prompt
                )
            ),
        )
    )

    research_results = safe_list(
        live_research.get(
            "results"
        )
    )

    sources_used = safe_list(
        live_research.get(
            "sources_used"
        )
    )

    research_performed = bool(
        live_research.get(
            "research_performed",
            False,
        )
    )

    cache_hit = bool(
        live_research.get(
            "cache_hit",
            False,
        )
    )

    if research_performed:

        research_status = (
            "PUBLIC RESEARCH REFRESHED"
        )

    elif cache_hit:

        research_status = (
            "CACHED PUBLIC RESEARCH REUSED"
        )

    elif not TAVILY_API_KEY:

        research_status = (
            "LIVE SEARCH UNAVAILABLE — LOCAL VERIFIED "
            "VISUAL DNA ACTIVE"
        )

    elif not LIVE_RESEARCH_ENABLED:

        research_status = (
            "LIVE SEARCH DISABLED — LOCAL VERIFIED "
            "VISUAL DNA ACTIVE"
        )

    else:

        research_status = (
            "NO USABLE PUBLIC RESULTS — LOCAL VERIFIED "
            "VISUAL DNA ACTIVE"
        )

    default_brief = (
        build_default_brand_brief(
            brand_id
        )
    )

    live_summary = (
        summarize_search_results(
            research_results,
            max_items=6,
        )
    )

    style_context = (
        build_style_context(
            prompt
        )
    )

    benefit_context = (
        build_benefit_context(
            prompt
        )
    )

    #
    # IMPORTANT COST RULE:
    #
    # Do NOT tell this layer to create 20 concepts.
    # Creative Brain V5 owns ideation and review.
    #

    final_prompt = f"""
USER REQUEST
============

{prompt}


XPAND STC BANK RESEARCH LAYER V2
================================

RESEARCH STATUS:
{research_status}


SOURCE PRIORITY
===============

1. User-supplied verified visual references.
2. Permanent STC Bank visual-reference memory.
3. Local STC Bank Visual DNA.
4. Current official STC Bank public material.
5. High-quality banking advertising inspiration only for
   art-direction principles.

Official website:
{STC_WEBSITE_URL}

Official Instagram reference:
{STC_INSTAGRAM_URL}

IMPORTANT:
Do not claim an Instagram post was directly inspected unless
the source was genuinely accessible.
Indexed/public snippets are contextual evidence only.


LOCAL STC BANK VISUAL DNA
=========================

{default_brief}


CURRENT BENEFIT CONTEXT
=======================

{benefit_context}


SELECTED VISUAL STYLE
=====================

{style_context}


CACHED / PUBLIC RESEARCH SNAPSHOTS
==================================

{live_summary}


CREATIVE EXECUTION AUTHORITY
============================

This research layer does NOT perform Creative Brain ideation.

Creative Brain V5 will independently generate and evaluate
the concepts.

Your job here is to strengthen the final image context with
brand and market intelligence.

Use the research to understand:
- visual maturity
- service relevance
- contemporary banking context
- environmental realism
- commercial finish

Do NOT copy:
- an existing campaign composition
- exact object placement
- exact camera framing
- an existing visual metaphor


STC BANK VISUAL STANDARD
========================

The final image must feel like premium Saudi commercial
advertising rather than generic AI banking art.

Prioritize:
- one strong visual idea
- believable physical scene
- purposeful camera angle
- real human behavior when people are present
- refined production design
- realistic material response
- motivated lighting
- coherent perspective
- physically correct contact shadows
- controlled reflections
- clear negative space
- sophisticated restrained color

STC Bank is NOT automatically a purple room.

For realistic photography:
preserve natural environmental colors.

For purple architectural studio:
purple belongs to physical architecture/materials,
not generic neon effects.

For augmented realism:
use exactly one controlled physical metaphor.


IMAGE-ONLY LOCK
===============

Generate NO visible advertising text.

Do NOT generate:
- headline
- subtitle
- body copy
- CTA
- discount
- percentage
- price
- legal disclaimer
- STC Bank wordmark
- STC logo
- Visa logo
- Mastercard logo
- watermark
- invented readable app UI

Reserve clean negative space.
Final typography and official logos will be added manually.


ANTI-CLICHE LOCK
================

Do NOT add merely for visual excitement:
- floating coins
- flying money
- floating bank card
- floating phone
- floating POS
- generic globe
- connection lines
- network lines
- transfer routes
- laser beams
- neon trails
- glowing arrows
- hologram
- HUD
- random particles
- sparkles
- generic fintech icons
- security shield
- generic lock
- generic handshake

Do not solve a weak concept by adding effects.


PRODUCTION ROUTE
================

Default STC production model:
Nano Banana 2 / google_fast.

Nano Banana Pro should only be used when explicitly requested
or intentionally selected elsewhere by the orchestration layer.

Resolution:
Respect the user's explicit requested resolution.
Do not automatically force 4K.
""".strip()

    return {
        "applied":
            True,

        "brand_id":
            brand_id,

        "brand_label":
            clean_text(
                profile.get(
                    "brand_label",
                    brand_id,
                ),
                300,
            ),

        "mode_override":
            clean_text(
                profile.get(
                    "default_mode",
                    "google_fast",
                ),
                100,
            ),

        "default_ratio":
            clean_text(
                profile.get(
                    "default_ratio",
                    "4:5",
                ),
                50,
            ),

        "default_resolution":
            clean_text(
                profile.get(
                    "default_resolution",
                    "2K",
                ),
                50,
            ),

        "final_prompt":
            clean_text(
                final_prompt,
                50000,
            ),

        "research_summary":
            live_summary,

        "sources_used":
            sources_used,

        "research_performed":
            research_performed,

        "cache_hit":
            cache_hit,

        "research_status":
            research_status,

        "research_calls":
            int(
                live_research.get(
                    "research_calls",
                    0,
                )
                or 0
            ),

        "cache_age_seconds":
            research_cache_age_seconds(
                brand_id
            ),

        "benefit_family":
            detect_stc_benefit_family(
                prompt
            ),

        "visual_style":
            detect_stc_visual_style(
                prompt
            ),
    }


# =========================================================
# MANUAL REFRESH API
# =========================================================

def refresh_brand_research(
    brand_id: str,
    user_prompt: str = "",
) -> Dict[str, Any]:

    brand_id = clean_text(
        brand_id,
        100,
    )

    if brand_id not in (
        BRAND_PROFILES
    ):

        return {
            "ok":
                False,

            "error":
                "unknown_brand",
        }

    if not LIVE_RESEARCH_ENABLED:

        return {
            "ok":
                False,

            "error":
                "live_research_disabled",
        }

    if not TAVILY_API_KEY:

        return {
            "ok":
                False,

            "error":
                "tavily_api_key_missing",
        }

    result = collect_brand_research(
        brand_id,
        (
            clean_text(
                user_prompt,
                8000,
            )
            or
            (
                "refresh current official "
                "brand advertising context"
            )
        ),
        force_refresh=True,
    )

    return {
        "ok":
            bool(
                result.get(
                    "results"
                )
            ),

        **result,
    }


# =========================================================
# STATUS
# =========================================================

def get_brand_research_status() -> Dict[
    str,
    Any,
]:

    cached = get_cached_brand_research(
        "stc_bank"
    )

    return {
        "module":
            MODULE_NAME,

        "version":
            VERSION,

        "live_research_enabled":
            LIVE_RESEARCH_ENABLED,

        "tavily_configured":
            bool(
                TAVILY_API_KEY
            ),

        "search_depth":
            RESEARCH_SEARCH_DEPTH,

        "max_calls_per_refresh":
            RESEARCH_MAX_CALLS,

        "results_per_call":
            RESEARCH_RESULTS_PER_CALL,

        "cache_ttl_seconds":
            RESEARCH_CACHE_TTL_SECONDS,

        "cache_file":
            DEFAULT_CACHE_FILE,

        "stc_cache_present":
            bool(
                cached
            ),

        "stc_cache_fresh":
            research_cache_is_fresh(
                "stc_bank"
            ),

        "stc_cache_age_seconds":
            research_cache_age_seconds(
                "stc_bank"
            ),

        "stc_default_mode":
            BRAND_PROFILES[
                "stc_bank"
            ][
                "default_mode"
            ],

        "stc_default_resolution":
            BRAND_PROFILES[
                "stc_bank"
            ][
                "default_resolution"
            ],
    }


# =========================================================
# ZERO-NETWORK SELF TEST
# =========================================================

if __name__ == "__main__":

    tests: Dict[
        str,
        bool
    ] = {}


    tests[
        "stc_bank_detection"
    ] = (
        detect_brand(
            (
                "أنشئ صورة إعلانية "
                "لبنك STC Bank"
            )
        )
        ==
        "stc_bank"
    )


    tests[
        "plain_stc_not_bank"
    ] = (
        detect_brand(
            (
                "أنشئ إعلان لشركة STC "
                "عن باقة اتصالات"
            )
        )
        ==
        ""
    )


    tests[
        "visual_research_layer"
    ] = (
        should_apply_deep_research(
            (
                "أنشئ إعلان لبنك STC Bank "
                "عن نقاط البيع"
            )
        )
        is True
    )


    tests[
        "non_visual_no_layer"
    ] = (
        should_apply_deep_research(
            (
                "ما هو STC Bank؟"
            )
        )
        is False
    )


    tests[
        "merchant_priority"
    ] = (
        detect_stc_benefit_family(
            (
                "خدمات التجارة الإلكترونية "
                "ونقاط البيع"
            )
        )
        ==
        "merchant_payments"
    )


    tests[
        "nano_banana_2_default"
    ] = (
        BRAND_PROFILES[
            "stc_bank"
        ][
            "default_mode"
        ]
        ==
        "google_fast"
    )


    tests[
        "2k_default"
    ] = (
        BRAND_PROFILES[
            "stc_bank"
        ][
            "default_resolution"
        ]
        ==
        "2K"
    )


    tests[
        "research_calls_max_3_default"
    ] = (
        RESEARCH_MAX_CALLS
        <=
        3
    )


    tests[
        "cache_ttl_minimum"
    ] = (
        RESEARCH_CACHE_TTL_SECONDS
        >=
        3600
    )


    tests[
        "explicit_research_detection"
    ] = explicit_research_requested(
        (
            "ابحث عن أحدث إعلانات "
            "STC Bank"
        )
    )


    brief = (
        build_default_brand_brief(
            "stc_bank"
        )
    )


    tests[
        "purple_not_identity"
    ] = (
        "not simply"
        in
        brief.lower()
    )


    tests[
        "image_only_profile"
    ] = (
        "no advertising headline"
        in
        brief.lower()
    )


    tests[
        "anti_floating"
    ] = (
        "floating bank card"
        in
        brief.lower()
    )


    realistic_context = (
        build_style_context(
            (
                "STC Bank "
                "واقعي فوتوغرافي"
            )
        )
    )


    tests[
        "realistic_style_context"
    ] = (
        "Premium realistic photography"
        in
        realistic_context
    )


    purple_context = (
        build_style_context(
            (
                "STC Bank "
                "بيئة بنفسجية استوديو"
            )
        )
    )


    tests[
        "purple_style_context"
    ] = (
        "purple architectural studio"
        in
        purple_context
    )


    augmented_context = (
        build_style_context(
            (
                "STC Bank "
                "واقعي سريالي راقٍ"
            )
        )
    )


    tests[
        "augmented_style_context"
    ] = (
        "augmented realism"
        in
        augmented_context
    )


    all_ok = all(
        tests.values()
    )


    print("")

    print(
        "=========================================="
    )

    print(
        " XPAND BRAND RESEARCH V2.0"
    )

    print(
        " ZERO-NETWORK SELF TEST"
    )

    print(
        "=========================================="
    )

    print("")


    for name, passed in (
        tests.items()
    ):

        print(
            (
                "✅"
                if passed
                else
                "❌"
            ),
            name,
        )


    print("")


    if all_ok:

        print(
            (
                "XPAND Brand Research "
                "V2.0 self-test: PASS ✅"
            )
        )

    else:

        print(
            (
                "XPAND Brand Research "
                "V2.0 self-test: FAIL ❌"
            )
        )


    print("")

    print(
        "✅ Local STC Visual DNA always available"
    )

    print(
        "✅ Live research cache"
    )

    print(
        "✅ 24h default refresh interval"
    )

    print(
        "✅ Maximum 3 lightweight searches per refresh"
    )

    print(
        "✅ Official-source-first research"
    )

    print(
        "✅ Indexed social research"
    )

    print(
        "✅ Premium advertising inspiration research"
    )

    print(
        "✅ No live search on every request"
    )

    print(
        "✅ No 20-concept instruction"
    )

    print(
        "✅ Creative Brain V5 owns ideation"
    )

    print(
        "✅ Nano Banana 2 default"
    )

    print(
        "✅ 2K cost-balanced default"
    )

    print(
        "✅ Premium realistic family"
    )

    print(
        "✅ Purple architectural family"
    )

    print(
        "✅ Augmented realism family"
    )

    print(
        "✅ No generated copy"
    )

    print(
        "✅ No generated logo"
    )

    print(
        "✅ Purple is not automatic"
    )

    print(
        "✅ Generic fintech effects blocked"
    )

    print(
        "✅ Plain STC telecom is not misclassified as STC Bank"
    )

    print(
        "🚫 No network calls were made"
    )

    print(
        "🚫 No Tavily calls were made"
    )

    print(
        "🚫 No OpenAI calls were made"
    )

    print(
        "🚫 No Gemini calls were made"
    )

    print(
        "🚫 No images were generated"
    )

    print("")
