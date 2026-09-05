# =========================================================
# XPAND SMART IMAGE ENGINE V2.1
#
# FULL DROP-IN REPLACEMENT
#
# PRIMARY GOALS
# ---------------------------------------------------------
# - Nano Banana 2 is the default image-production route.
# - Nano Banana Pro is explicit / deliberate, not automatic.
# - Structured Creative Brain JSON uses GPT-5.6 Sol first.
# - Cheap free-text direction uses Gemini Flash-Lite first.
# - Real OpenAI fallback exists when Gemini image generation fails.
# - STC Bank receives deterministic visual production direction.
# - No automatic expensive critique/edit loops.
# - Backwards-compatible API for XPAND Production / Telegram.
#
# IMPORTANT
# ---------------------------------------------------------
# Running this file directly makes ZERO API calls.
#
# Dependencies:
#   requests>=2.32.0,<3
#   Pillow
# =========================================================

from __future__ import annotations

import base64
import io
import json
import os
import re
import time
import uuid

from dataclasses import dataclass, field

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
)

import requests

from PIL import Image

from xpand_stc_bank_skill import (
    STC_BANK_IMAGE_GUARD,
    is_stc_bank_request,
)


# =========================================================
# ENGINE
# =========================================================

ENGINE_NAME = (
    "XPAND Smart Image Engine"
)

ENGINE_VERSION = "2.1.0"


# =========================================================
# ENV HELPERS
# =========================================================

def env_bool(
    name: str,
    default: bool,
) -> bool:

    fallback = (
        "true"
        if default
        else "false"
    )

    value = str(
        os.environ.get(
            name,
            fallback,
        )
    ).strip().lower()

    return value in {
        "1",
        "true",
        "yes",
        "on",
    }


def env_int(
    name: str,
    default: int,
    *,
    minimum: int,
    maximum: int,
) -> int:

    try:

        value = int(
            os.environ.get(
                name,
                str(default),
            )
            or default
        )

    except Exception:

        value = default

    return max(
        minimum,
        min(
            maximum,
            value,
        ),
    )


# =========================================================
# API KEYS
# =========================================================

OPENAI_API_KEY = str(
    os.environ.get(
        "OPENAI_API_KEY",
        "",
    )
).strip()


GEMINI_API_KEY = str(
    os.environ.get(
        "GEMINI_API_KEY",
        "",
    )
).strip()


# =========================================================
# MODELS
# =========================================================

OPENAI_IMAGE_MODEL = str(
    os.environ.get(
        "XPAND_OPENAI_IMAGE_MODEL",
        "gpt-image-2",
    )
).strip()


OPENAI_DIRECTOR_MODEL = str(
    os.environ.get(
        "XPAND_OPENAI_DIRECTOR_MODEL",
        "gpt-5.6-sol",
    )
).strip()


GOOGLE_IMAGE_FAST_MODEL = str(
    os.environ.get(
        "XPAND_GOOGLE_IMAGE_MODEL",
        "gemini-3.1-flash-image",
    )
).strip()


GOOGLE_IMAGE_PRO_MODEL = str(
    os.environ.get(
        "XPAND_GOOGLE_IMAGE_PRO_MODEL",
        "gemini-3-pro-image",
    )
).strip()


GEMINI_DIRECTOR_MODEL = str(
    os.environ.get(
        "XPAND_GEMINI_DIRECTOR_MODEL",
        "gemini-3.5-flash-lite",
    )
).strip()


GEMINI_DIRECTOR_RUNTIME_MODEL = (
    GEMINI_DIRECTOR_MODEL
)


GEMINI_DIRECTOR_FALLBACK_MODELS = [
    item.strip()
    for item in str(
        os.environ.get(
            "XPAND_GEMINI_DIRECTOR_FALLBACK_MODELS",
            (
                "gemini-3.5-flash-lite,"
                "gemini-3.5-flash"
            ),
        )
    ).split(",")
    if item.strip()
]


# =========================================================
# DEFAULT ROUTING
# =========================================================

#
# AUTO still resolves to Nano Banana 2.
#
# Keeping the default as AUTO means explicit language such
# as "Nano Banana Pro" or "best" can still be respected.
#

DEFAULT_MODE = str(
    os.environ.get(
        "XPAND_IMAGE_MODE",
        "auto",
    )
).strip().lower()


DEFAULT_QUALITY = str(
    os.environ.get(
        "XPAND_IMAGE_QUALITY",
        "medium",
    )
).strip().lower()


DEFAULT_IMAGE_SIZE = str(
    os.environ.get(
        "XPAND_IMAGE_SIZE",
        "1K",
    )
).strip()


#
# BEST does NOT mean Pro by default.
#
# BEST = strongest normal XPAND prompt sent to Nano Banana 2.
#
# Pro is used only when this env variable is explicitly true.
#

BEST_USE_PRO = env_bool(
    "XPAND_BEST_USE_PRO",
    False,
)


#
# If Gemini image generation fails, OpenAI may finish
# the request when the caller permits fallback.
#

OPENAI_IMAGE_FALLBACK_ENABLED = env_bool(
    "XPAND_OPENAI_IMAGE_FALLBACK",
    True,
)


# =========================================================
# DIRECTOR COST POLICY
# =========================================================

#
# Structured JSON is important to Creative Brain correctness.
# GPT-5.6 Sol therefore handles structured work first.
#
# Free text / simple art direction goes to cheap Gemini Lite.
#

STRUCTURED_DIRECTOR_PREFER_OPENAI = env_bool(
    "XPAND_STRUCTURED_DIRECTOR_PREFER_OPENAI",
    True,
)


FREE_TEXT_DIRECTOR_PREFER_GEMINI = env_bool(
    "XPAND_FREE_TEXT_DIRECTOR_PREFER_GEMINI",
    True,
)


OPENAI_DIRECTOR_REASONING = str(
    os.environ.get(
        "XPAND_OPENAI_DIRECTOR_REASONING",
        "low",
    )
).strip().lower()


OPENAI_STRUCTURED_REASONING = str(
    os.environ.get(
        "XPAND_OPENAI_STRUCTURED_REASONING",
        "low",
    )
).strip().lower()


OPENAI_DIRECTOR_MAX_OUTPUT_TOKENS = env_int(
    "XPAND_OPENAI_DIRECTOR_MAX_OUTPUT_TOKENS",
    1800,
    minimum=300,
    maximum=20000,
)


#
# Creative Brain can return large structured concept arrays.
#
# Do not squeeze them into 1-2K output tokens.
#

OPENAI_STRUCTURED_MAX_OUTPUT_TOKENS = env_int(
    "XPAND_OPENAI_STRUCTURED_MAX_OUTPUT_TOKENS",
    9000,
    minimum=2000,
    maximum=32000,
)


OPENAI_STRUCTURED_RETRY_MAX_OUTPUT_TOKENS = env_int(
    "XPAND_OPENAI_STRUCTURED_RETRY_MAX_OUTPUT_TOKENS",
    12000,
    minimum=3000,
    maximum=40000,
)


OPENAI_STRUCTURED_RETRIES = env_int(
    "XPAND_OPENAI_STRUCTURED_RETRIES",
    2,
    minimum=1,
    maximum=2,
)


OPENAI_USAGE_LOGGING = env_bool(
    "XPAND_OPENAI_USAGE_LOGGING",
    True,
)


OPENAI_VISION_DETAIL = str(
    os.environ.get(
        "XPAND_OPENAI_VISION_DETAIL",
        "high",
    )
).strip().lower()


if OPENAI_VISION_DETAIL not in {
    "low",
    "high",
    "auto",
}:

    OPENAI_VISION_DETAIL = "high"


#
# Modern Responses API prompt cache controls.
#
# prompt_cache_key helps stable prefixes get grouped.
# No extended 24h retention is enabled by default.
#

OPENAI_PROMPT_CACHE_KEY = str(
    os.environ.get(
        "XPAND_OPENAI_PROMPT_CACHE_KEY",
        "xpand-director-v2",
    )
).strip()


OPENAI_PROMPT_CACHE_RETENTION = str(
    os.environ.get(
        "XPAND_OPENAI_PROMPT_CACHE_RETENTION",
        "",
    )
).strip()


#
# Compatibility field retained for status / older code.
#

OPENAI_PROMPT_CACHE_MODE = (
    "automatic"
    if OPENAI_PROMPT_CACHE_KEY
    else "off"
)


# =========================================================
# GEMINI COST POLICY
# =========================================================

GEMINI_SEARCH_GROUNDING = env_bool(
    "XPAND_GEMINI_SEARCH_GROUNDING",
    True,
)


#
# Image reasoning still happens inside Gemini image models.
# These values keep normal Nano Banana 2 economical while
# allowing deliberate Pro jobs to use stronger reasoning.
#

GEMINI_FAST_IMAGE_THINKING = str(
    os.environ.get(
        "XPAND_GEMINI_FAST_IMAGE_THINKING",
        "low",
    )
).strip().lower()


GEMINI_PRO_IMAGE_THINKING = str(
    os.environ.get(
        "XPAND_GEMINI_PRO_IMAGE_THINKING",
        "high",
    )
).strip().lower()


# =========================================================
# TIMEOUT
# =========================================================

REQUEST_TIMEOUT = max(
    30,
    int(
        os.environ.get(
            "XPAND_IMAGE_TIMEOUT_SECONDS",
            "300",
        )
        or 300
    ),
)


# =========================================================
# ENDPOINTS
# =========================================================

OPENAI_IMAGE_GENERATION_URL = (
    "https://api.openai.com/v1/images/generations"
)


OPENAI_IMAGE_EDITS_URL = (
    "https://api.openai.com/v1/images/edits"
)


OPENAI_RESPONSES_URL = (
    "https://api.openai.com/v1/responses"
)


GEMINI_INTERACTIONS_URL = (
    "https://generativelanguage.googleapis.com/"
    "v1beta/interactions"
)


# =========================================================
# MODES
# =========================================================

MODE_AUTO = "auto"

MODE_FAST = "fast"

MODE_OPENAI = "openai"

MODE_GOOGLE_FAST = "google_fast"

MODE_GOOGLE_PRO = "google_pro"

MODE_PRO = "pro"

MODE_BEST = "best"

MODE_COMPARE = "compare"


# =========================================================
# PROVIDERS
# =========================================================

PROVIDER_OPENAI = "openai"

PROVIDER_GOOGLE_FAST = "google_fast"

PROVIDER_GOOGLE_PRO = "google_pro"

PROVIDER_FUSION_PRO = "fusion_pro"

PROVIDER_FUSION_BEST = "fusion_best"

PROVIDER_OPENAI_FUSION = "openai_fusion"


# =========================================================
# SUPPORTED SETTINGS
# =========================================================

SUPPORTED_ASPECT_RATIOS = {
    "1:1",
    "2:3",
    "3:2",
    "3:4",
    "4:3",
    "4:5",
    "5:4",
    "9:16",
    "16:9",
    "21:9",
    "1:4",
    "4:1",
    "1:8",
    "8:1",
}


SUPPORTED_GOOGLE_IMAGE_SIZES = {
    "512",
    "1K",
    "2K",
    "4K",
}


SUPPORTED_OPENAI_QUALITIES = {
    "low",
    "medium",
    "high",
    "auto",
}


SUPPORTED_REASONING_LEVELS = {
    "none",
    "minimal",
    "low",
    "medium",
    "high",
    "xhigh",
    "max",
}


# =========================================================
# EXCEPTIONS
# =========================================================

class XPANDImageError(
    Exception
):
    pass


class XPANDImageConfigurationError(
    XPANDImageError
):
    pass


class XPANDImageProviderError(
    XPANDImageError
):
    pass


class XPANDStructuredOutputError(
    XPANDImageProviderError
):
    pass


# =========================================================
# DATA MODELS
# =========================================================

@dataclass
class ImageRoute:

    provider: str

    model: str

    reason: str

    aspect_ratio: str

    image_size: str

    quality: str


@dataclass
class GeneratedImage:

    image_bytes: bytes

    mime_type: str

    provider: str

    model: str

    prompt: str

    original_prompt: str

    aspect_ratio: str

    image_size: str

    quality: str

    route_reason: str

    request_id: str = ""

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def extension(
        self,
    ) -> str:

        mapping = {
            "image/png":
                ".png",

            "image/jpeg":
                ".jpg",

            "image/jpg":
                ".jpg",

            "image/webp":
                ".webp",
        }

        return mapping.get(
            str(
                self.mime_type
            ).lower(),
            ".png",
        )

    @property
    def filename(
        self,
    ) -> str:

        provider_name = (
            str(
                self.provider
            )
            .replace(
                "_",
                "-",
            )
        )

        unique = (
            self.request_id
            or
            uuid.uuid4().hex[:10]
        )

        return (
            f"XPAND-{provider_name}-{unique}"
            f"{self.extension}"
        )


@dataclass
class ImageGenerationResponse:

    ok: bool

    images: List[
        GeneratedImage
    ]

    selected_route: str

    routes: List[
        ImageRoute
    ]

    original_prompt: str

    enhanced_prompt: str

    elapsed_seconds: float

    errors: List[str] = field(
        default_factory=list
    )


# =========================================================
# BASIC HELPERS
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
        50000,
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
    text: str,
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


def extract_quoted_text(
    prompt: str,
) -> List[str]:

    patterns = [
        r'"([^"]+)"',
        r"'([^']+)'",
        r"“([^”]+)”",
        r"«([^»]+)»",
    ]

    results: List[str] = []

    for pattern in patterns:

        for match in re.findall(
            pattern,
            prompt,
        ):

            value = clean_text(
                match,
                1000,
            )

            if (
                value
                and
                value not in results
            ):

                results.append(
                    value
                )

    return results


def _normalize_digits_and_colon(
    value: Any,
) -> str:

    text = clean_text(
        value,
        50000,
    )

    text = text.translate(
        str.maketrans(
            "٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹",
            "01234567890123456789",
        )
    )

    text = re.sub(
        r"\s*[：﹕︓:]\s*",
        ":",
        text,
    )

    return text


# =========================================================
# ASPECT RATIO
# =========================================================

def detect_aspect_ratio(
    prompt: str,
    requested_aspect_ratio: str = "",
) -> str:

    explicit = _normalize_digits_and_colon(
        requested_aspect_ratio
    ).strip()

    if explicit in (
        SUPPORTED_ASPECT_RATIOS
    ):

        return explicit

    source = _normalize_digits_and_colon(
        prompt
    ).lower()

    for ratio in (
        "1:1",
        "2:3",
        "3:2",
        "3:4",
        "4:3",
        "4:5",
        "5:4",
        "9:16",
        "16:9",
        "21:9",
        "1:4",
        "4:1",
        "1:8",
        "8:1",
    ):

        if re.search(
            (
                r"(?<!\d)"
                +
                re.escape(
                    ratio
                )
                +
                r"(?!\d)"
            ),
            source,
        ):

            return ratio

    if contains_any(
        source,
        [
            "ستوري",
            "story",
            "ريل",
            "reel",
            "vertical story",
        ],
    ):

        return "9:16"

    if contains_any(
        source,
        [
            "بوستر",
            "poster",
            "بوست",
            "post",
            "social ad",
            "اعلان سوشال",
            "اعلان للسوشال",
        ],
    ):

        return "4:5"

    if contains_any(
        source,
        [
            "banner",
            "بانر",
            "landscape",
            "افقي",
            "أفقي",
        ],
    ):

        return "16:9"

    return "1:1"


# =========================================================
# IMAGE SIZE
# =========================================================

def normalize_image_size(
    value: Any,
) -> str:

    source = (
        clean_text(
            value,
            100,
        )
        .strip()
        .upper()
        .replace(
            " ",
            "",
        )
    )

    aliases = {
        "512":
            "512",

        "512PX":
            "512",

        "0.5K":
            "512",

        ".5K":
            "512",

        "HD":
            "HD",

        "720":
            "HD",

        "720P":
            "HD",

        "1K":
            "1K",

        "1024":
            "1K",

        "FHD":
            "2K",

        "FULLHD":
            "2K",

        "1080":
            "2K",

        "1080P":
            "2K",

        "2K":
            "2K",

        "4K":
            "4K",
    }

    return aliases.get(
        source,
        "",
    )


def detect_image_size(
    prompt: str,
    requested_image_size: str = "",
) -> str:

    explicit = normalize_image_size(
        requested_image_size
    )

    if explicit:

        return explicit

    source = clean_text(
        prompt,
        50000,
    ).lower()

    if re.search(
        r"(?<!\d)4\s*k(?!\w)",
        source,
        flags=re.IGNORECASE,
    ):

        return "4K"

    if (
        re.search(
            r"(?<!\d)2\s*k(?!\w)",
            source,
            flags=re.IGNORECASE,
        )
        or
        contains_any(
            source,
            [
                "1080p",
                "1080 p",
                "full hd",
                "fhd",
            ],
        )
    ):

        return "2K"

    if contains_any(
        source,
        [
            "720p",
            "720 p",
            " hd ",
            "دقه hd",
            "دقة hd",
        ],
    ):

        return "HD"

    if re.search(
        r"(?<!\d)1\s*k(?!\w)",
        source,
        flags=re.IGNORECASE,
    ):

        return "1K"

    if contains_any(
        source,
        [
            "512px",
            "512 px",
            "512 بيكسل",
            "512 بكسل",
        ],
    ):

        return "512"

    fallback = normalize_image_size(
        DEFAULT_IMAGE_SIZE
    )

    return (
        fallback
        or "1K"
    )


def google_provider_image_size(
    requested_size: str,
) -> str:

    value = normalize_image_size(
        requested_size
    )

    if value in (
        SUPPORTED_GOOGLE_IMAGE_SIZES
    ):

        return value

    #
    # HD is delivered by downscaling a normal 1K output.
    #

    if value == "HD":

        return "1K"

    return "1K"


# =========================================================
# QUALITY
# =========================================================

def detect_quality(
    prompt: str,
    requested_quality: str = "",
) -> str:

    explicit = clean_text(
        requested_quality,
        50,
    ).lower()

    if explicit in (
        SUPPORTED_OPENAI_QUALITIES
    ):

        return explicit

    source = normalize_arabic(
        prompt
    )

    if contains_any(
        source,
        [
            "high quality",
            "high-quality",
            "اعلى جوده",
            "أعلى جودة",
            "اقصى جوده",
            "أقصى جودة",
            "maximum quality",
        ],
    ):

        return "high"

    if contains_any(
        source,
        [
            "draft",
            "preview",
            "low quality",
            "مسوده",
            "مسودة",
        ],
    ):

        return "low"

    fallback = clean_text(
        DEFAULT_QUALITY,
        50,
    ).lower()

    if fallback in (
        SUPPORTED_OPENAI_QUALITIES
    ):

        return fallback

    return "medium"


# =========================================================
# STC BANK DETECTION
# =========================================================

def _is_stc_request(
    prompt: str,
) -> bool:

    try:

        if is_stc_bank_request(
            prompt
        ):

            return True

    except Exception:

        pass

    return contains_any(
        prompt,
        [
            "stc bank",
            "stc بنك",
            "بنك stc",
            "اس تي سي بنك",
            "stc_bank",
        ],
    )


# =========================================================
# STC BENEFIT FAMILY
# =========================================================

def _stc_benefit_family(
    prompt: str,
) -> str:

    source = normalize_arabic(
        prompt
    )

    #
    # Merchant payments first.
    #
    # Prevent words such as card/reward from hijacking the
    # actual merchant-payment benefit.
    #

    if contains_any(
        source,
        [
            "merchant payment",
            "merchant payments",
            "merchant",
            "pos",
            "point of sale",
            "points of sale",
            "نقاط البيع",
            "نقطه البيع",
            "نقطة البيع",
            "مدفوعات المتاجر",
            "مدفوعات التجار",
            "الدفع عند التاجر",
            "دفع عند التاجر",
            "دفع المتاجر",
            "جهاز الدفع",
            "جهاز نقاط البيع",
            "tap to pay",
            "contactless payment",
        ],
    ):

        return "merchant_payments"

    if contains_any(
        source,
        [
            "international transfer",
            "international money transfer",
            "cross border transfer",
            "تحويل دولي",
            "تحويل مالي دولي",
            "تحويل الاموال دوليا",
            "تحويل الأموال دوليا",
            "حواله دوليه",
            "حوالة دولية",
        ],
    ):

        return "international_transfer"

    if contains_any(
        source,
        [
            "travel",
            "travelling",
            "سفر",
            "السفر",
            "مسافر",
            "مطار",
            "airport",
            "trip",
        ],
    ):

        return "travel"

    if contains_any(
        source,
        [
            "cashback",
            "cash back",
            "كاش باك",
            "استرداد نقدي",
            "استرداد",
        ],
    ):

        return "cashback"

    if contains_any(
        source,
        [
            "security",
            "secure",
            "safe banking",
            "امان",
            "أمان",
            "حمايه",
            "حماية",
        ],
    ):

        return "security"

    if contains_any(
        source,
        [
            "reward",
            "rewards",
            "points",
            "loyalty",
            "مكافات",
            "مكافآت",
            "نقاط",
        ],
    ):

        return "rewards"

    if contains_any(
        source,
        [
            "app",
            "application",
            "digital banking",
            "تطبيق",
            "بنك رقمي",
            "الخدمات الرقميه",
            "الخدمات الرقمية",
        ],
    ):

        return "digital_banking"

    return "premium_banking"


# =========================================================
# STC STYLE FAMILY
# =========================================================

def _stc_style_family(
    prompt: str,
    benefit_family: str = "",
) -> str:

    source = normalize_arabic(
        prompt
    )

    #
    # Explicit user art direction always wins.
    #

    if contains_any(
        source,
        [
            "geometric studio",
            "architectural studio",
            "purple architecture",
            "purple geometric",
            "استوديو هندسي",
            "هندسي بنفسجي",
            "معماري بنفسجي",
            "منصات هندسيه",
            "منصات هندسية",
        ],
    ):

        return "purple_architectural"

    if contains_any(
        source,
        [
            "surreal",
            "conceptual",
            "augmented realism",
            "metaphor",
            "visual metaphor",
            "سريالي",
            "مجاز بصري",
            "واقعيه معززه",
            "واقعية معززة",
            "كونسبت",
            "concept art",
        ],
    ):

        return "augmented_realism"

    if contains_any(
        source,
        [
            "still life",
            "product shot",
            "product photography",
            "card hero",
            "app hero",
            "تصوير منتج",
            "لقطه منتج",
            "لقطة منتج",
            "بطاقه فقط",
            "بطاقة فقط",
            "الهاتف فقط",
        ],
    ):

        return "product_still_life"

    if contains_any(
        source,
        [
            "lifestyle",
            "realistic photography",
            "commercial photography",
            "cinematic photography",
            "تصوير واقعي",
            "تصوير تجاري",
            "لايف ستايل",
            "سينمائي واقعي",
        ],
    ):

        return "premium_realistic"

    #
    # Merchant payments must default to believable commerce.
    #

    if benefit_family == (
        "merchant_payments"
    ):

        return "premium_realistic"

    return "premium_realistic"


# =========================================================
# STC CAMERA DIRECTION
# =========================================================

STC_CAMERA_LIBRARY = {
    "eye_level": (
        "Eye-level commercial camera. Natural human scale, "
        "credible behavior and balanced perspective."
    ),

    "low_angle": (
        "Low-angle hero camera. Use restraint; preserve believable "
        "verticals and product scale."
    ),

    "extreme_low_angle": (
        "Extreme low-angle only when monumental architectural scale "
        "materially improves the concept."
    ),

    "worms_eye": (
        "Worm's-eye viewpoint for deliberate scale transformation, "
        "with physically consistent perspective."
    ),

    "high_angle": (
        "High-angle camera for clear spatial relationships without "
        "flattening the scene."
    ),

    "birds_eye": (
        "Bird's-eye view for spatial organization and real-world "
        "patterns, never for glowing network diagrams."
    ),

    "top_down": (
        "Top-down graphic composition with real objects, contact "
        "shadows and disciplined spacing."
    ),

    "three_quarter": (
        "Three-quarter commercial hero angle, especially suitable "
        "for cards, phones and premium physical products."
    ),

    "over_shoulder": (
        "Over-the-shoulder viewpoint for believable digital banking "
        "interaction and contextual human behavior."
    ),

    "pov": (
        "First-person POV for immersive payment, travel or app use."
    ),

    "ground_level": (
        "Ground-level viewpoint for movement and strong foreground "
        "depth while maintaining real scale."
    ),

    "macro": (
        "Macro product detail with convincing material texture, "
        "edge quality and shallow optical depth."
    ),

    "extreme_close_up": (
        "Extreme close-up only for meaningful product/material detail."
    ),

    "wide": (
        "Wide commercial composition with strong environmental context "
        "and intentional negative space."
    ),

    "extreme_wide": (
        "Extreme wide environmental composition for architecture "
        "or lifestyle storytelling."
    ),

    "forced_perspective": (
        "Controlled forced perspective using real spatial cues, "
        "not impossible floating-object collage."
    ),

    "one_point": (
        "One-point perspective with a clear vanishing point and "
        "disciplined architectural geometry."
    ),

    "frame_within_frame": (
        "Frame-within-frame composition using doors, windows, shelves "
        "or architecture to create hierarchy."
    ),

    "foreground_obstruction": (
        "Use a subtle foreground object for depth and realism without "
        "obscuring the benefit."
    ),
}


def _stc_camera_direction(
    prompt: str,
    benefit_family: str,
    style_family: str,
) -> str:

    source = normalize_arabic(
        prompt
    )

    marker_map = [
        (
            [
                "worm's eye",
                "worms eye",
                "worm eye",
                "عين الدوده",
                "عين الدودة",
            ],
            "worms_eye",
        ),

        (
            [
                "extreme low angle",
                "زاويه منخفضه جدا",
                "زاوية منخفضة جدا",
            ],
            "extreme_low_angle",
        ),

        (
            [
                "low angle",
                "زاويه منخفضه",
                "زاوية منخفضة",
            ],
            "low_angle",
        ),

        (
            [
                "bird's eye",
                "birds eye",
                "bird eye",
                "منظر جوي",
                "عين الطائر",
            ],
            "birds_eye",
        ),

        (
            [
                "top down",
                "top-down",
                "من الاعلى مباشره",
                "من الأعلى مباشرة",
            ],
            "top_down",
        ),

        (
            [
                "high angle",
                "زاويه مرتفعه",
                "زاوية مرتفعة",
            ],
            "high_angle",
        ),

        (
            [
                "over the shoulder",
                "over-the-shoulder",
                "من خلف الكتف",
            ],
            "over_shoulder",
        ),

        (
            [
                "pov",
                "point of view",
                "منظور الشخص",
            ],
            "pov",
        ),

        (
            [
                "macro",
                "ماكرو",
            ],
            "macro",
        ),

        (
            [
                "extreme close up",
                "extreme close-up",
                "لقطه قريبه جدا",
                "لقطة قريبة جدا",
            ],
            "extreme_close_up",
        ),

        (
            [
                "three quarter",
                "three-quarter",
                "3/4 angle",
                "ثلاثه ارباع",
                "ثلاثة أرباع",
            ],
            "three_quarter",
        ),

        (
            [
                "forced perspective",
                "منظور قسري",
            ],
            "forced_perspective",
        ),

        (
            [
                "one point perspective",
                "one-point perspective",
                "منظور نقطه واحده",
                "منظور نقطة واحدة",
            ],
            "one_point",
        ),

        (
            [
                "frame within frame",
                "frame-within-frame",
                "اطار داخل اطار",
                "إطار داخل إطار",
            ],
            "frame_within_frame",
        ),

        (
            [
                "foreground obstruction",
                "foreground element",
                "عنصر امامي",
                "عنصر أمامي",
            ],
            "foreground_obstruction",
        ),

        (
            [
                "extreme wide",
                "extreme-wide",
                "واسعه جدا",
                "واسعة جدا",
            ],
            "extreme_wide",
        ),

        (
            [
                "wide angle",
                "wide shot",
                "لقطه واسعه",
                "لقطة واسعة",
            ],
            "wide",
        ),

        (
            [
                "eye level",
                "eye-level",
                "مستوى العين",
            ],
            "eye_level",
        ),
    ]

    for markers, key in marker_map:

        if contains_any(
            source,
            markers,
        ):

            return (
                key
                +
                ": "
                +
                STC_CAMERA_LIBRARY[
                    key
                ]
            )

    if style_family == (
        "product_still_life"
    ):

        key = "three_quarter"

    elif style_family == (
        "purple_architectural"
    ):

        key = "one_point"

    elif benefit_family in {
        "digital_banking",
        "merchant_payments",
    }:

        key = "eye_level"

    elif benefit_family == "travel":

        key = "wide"

    else:

        key = "eye_level"

    return (
        key
        +
        ": "
        +
        STC_CAMERA_LIBRARY[
            key
        ]
    )


# =========================================================
# STC PRODUCTION DIRECTION
# =========================================================

def build_stc_production_direction(
    prompt: str,
) -> str:

    benefit_family = (
        _stc_benefit_family(
            prompt
        )
    )

    style_family = (
        _stc_style_family(
            prompt,
            benefit_family,
        )
    )

    camera_direction = (
        _stc_camera_direction(
            prompt,
            benefit_family,
            style_family,
        )
    )

    family_direction = {
        "premium_realistic": (
            "Use premium realistic Saudi commercial photography. "
            "Human behavior must feel natural and observed rather than posed. "
            "Use credible environments, real-scale products, polished but "
            "restrained art direction and believable optical depth."
        ),

        "purple_architectural": (
            "Build a controlled architectural/studio composition with real "
            "platforms, planes, depth and perspective. Purple may appear as "
            "an identity accent or architectural material, never as a blanket "
            "purple wash. Surfaces must have physically plausible shadows, "
            "reflections and roughness."
        ),

        "augmented_realism": (
            "Use refined augmented realism: one intelligent conceptual "
            "mechanism integrated physically into an otherwise photoreal "
            "scene. The concept must not become childish fantasy, random CGI "
            "or generic fintech decoration."
        ),

        "product_still_life": (
            "Use premium product still-life discipline. Give the card, phone "
            "or banking product a physically grounded hero presentation with "
            "realistic material behavior, controlled reflections, elegant "
            "negative space and no fake floating UI."
        ),
    }.get(
        style_family,
        "",
    )

    benefit_direction = {
        "merchant_payments": (
            "MERCHANT PAYMENTS: show a believable premium Saudi commerce "
            "moment such as boutique, cafe, restaurant or quality retail. "
            "The payment interaction must be natural: customer, merchant, "
            "phone/card and POS should relate correctly in space. Never stage "
            "a person simply pointing a payment terminal at the camera."
        ),

        "international_transfer": (
            "INTERNATIONAL TRANSFER: communicate ease, reach or confidence "
            "through people, place, travel, relationship or a tangible real "
            "world metaphor. Do not use maps with glowing transfer routes, "
            "laser paths, network lines or floating country icons."
        ),

        "travel": (
            "TRAVEL: use credible Saudi traveler behavior, airport, hotel, "
            "destination or premium journey cues. Keep the banking benefit "
            "clear through situation and product use rather than travel-icon "
            "collage."
        ),

        "cashback": (
            "CASHBACK: communicate tangible value or rewarding everyday "
            "behavior using a refined real-world metaphor. Avoid floating "
            "coins, exploding particles and generic reward icons."
        ),

        "security": (
            "SECURITY: communicate control, calm and confidence through "
            "composition, behavior and environment. Avoid shields, locks, "
            "digital grids and glowing cyber effects unless explicitly asked."
        ),

        "rewards": (
            "REWARDS: represent benefit through premium experiences or "
            "tangible value. Avoid generic points clouds, coins and floating "
            "gift icons."
        ),

        "digital_banking": (
            "DIGITAL BANKING: show credible use of the app or phone in a "
            "real human context. Do not invent readable UI screens, floating "
            "interfaces or fake banking dashboards."
        ),

        "premium_banking": (
            "PREMIUM BANKING: prioritize confidence, restraint, modern Saudi "
            "lifestyle and polished commercial production rather than visual "
            "effects."
        ),
    }.get(
        benefit_family,
        "",
    )

    return (
        "\n\n"
        "========================================\n"
        "XPAND STC BANK PRODUCTION DIRECTOR\n"
        "========================================\n"
        f"Benefit family: {benefit_family}\n"
        f"Visual family: {style_family}\n"
        f"Camera: {camera_direction}\n\n"
        "NON-NEGOTIABLE OUTPUT RULES:\n"
        "- Generate NO visible advertising copy.\n"
        "- Generate NO headline, subtitle, CTA or legal text.\n"
        "- Generate NO STC wordmark or STC Bank logo.\n"
        "- Generate NO Visa/Mastercard/network logo unless an exact supplied "
        "physical reference makes it unavoidable and fidelity is explicitly "
        "required.\n"
        "- Do not invent readable app UI or financial numbers.\n"
        "- Do not add watermarks or signatures.\n"
        "- Reserve intentional clean negative space so final Arabic/English "
        "copy and official logo can be added manually later.\n"
        "- Purple is an accent, NOT a mandatory full-scene color wash.\n"
        "- Green may be used as a controlled secondary identity accent.\n"
        "- Prefer warm neutral, off-white, stone, beige, walnut, leather, "
        "glass and brushed-metal material families where suitable.\n"
        "- Use motivated light sources, realistic contact shadows, natural "
        "reflections and physically correct object grounding.\n"
        "- Preserve one coherent perspective and believable scale.\n"
        "- Avoid generic blue technology color unless the concept genuinely "
        "requires it.\n"
        "- No blue laser beams.\n"
        "- No neon transfer routes.\n"
        "- No connection/network lines.\n"
        "- No glowing arrows.\n"
        "- No random particles or sparkles.\n"
        "- No HUD or futuristic interface overlays.\n"
        "- No floating generic banking icons.\n"
        "- No unsupported floating cards or phones.\n"
        "- No generic globe metaphor.\n"
        "- No visual-effect clutter used merely to make the scene look "
        "technological.\n\n"
        "VISUAL FAMILY EXECUTION:\n"
        f"{family_direction}\n\n"
        "BENEFIT-SPECIFIC EXECUTION:\n"
        f"{benefit_direction}\n\n"
        "FINAL STANDARD:\n"
        "The result must feel like a photographable, premium campaign frame "
        "created by a senior Saudi advertising art director. Strong concept, "
        "clear focal hierarchy, real materials, disciplined color, useful "
        "negative space and no obvious AI decoration."
    )


# =========================================================
# PROFESSIONAL PROMPT
# =========================================================

def build_professional_prompt(
    user_prompt: str,
    aspect_ratio: str,
    image_size: str,
) -> str:

    user_prompt = clean_text(
        user_prompt,
        30000,
    )

    directives = [
        (
            "Preserve the user's exact commercial intent and main subject."
        ),

        (
            "Build one coherent, physically believable scene instead of "
            "a collage of unrelated visual ideas."
        ),

        (
            "Use a deliberate camera angle, clear focal hierarchy and "
            "professional negative space."
        ),

        (
            "Use realistic light direction, contact shadows, material "
            "roughness, reflections, perspective and depth."
        ),

        (
            "Keep hands, faces, products, edges and geometry commercially "
            "usable and free from obvious generation artifacts."
        ),

        (
            "Avoid unnecessary decorative effects and generic AI visual noise."
        ),

        (
            f"Target aspect ratio: {aspect_ratio}."
        ),

        (
            f"Target resolution intent: {image_size}."
        ),
    ]

    stc_request = _is_stc_request(
        user_prompt
    )

    #
    # Non-STC jobs retain intentional quoted-text support.
    #
    # STC jobs intentionally generate no advertising copy
    # because the user adds final copy/logo manually.
    #

    if not stc_request:

        quoted = extract_quoted_text(
            user_prompt
        )

        if quoted:

            exact = "\n".join(
                f'- "{item}"'
                for item in quoted
            )

            directives.append(
                (
                    "If the user intentionally requested typography, render "
                    "these quoted text elements exactly:\n"
                    +
                    exact
                )
            )

    output = (
        "USER REQUEST:\n"
        +
        user_prompt
        +
        "\n\n"
        "XPAND PROFESSIONAL ART DIRECTION:\n"
        +
        "\n".join(
            f"- {item}"
            for item in directives
        )
    )

    if stc_request:

        if STC_BANK_IMAGE_GUARD:

            output += (
                "\n\n"
                "========================================\n"
                "STC BANK SAVED IMAGE GUARD\n"
                "========================================\n"
                +
                clean_text(
                    STC_BANK_IMAGE_GUARD,
                    16000,
                )
            )

        #
        # Append deterministic local production rules LAST.
        # These are the final execution authority.
        #

        output += (
            build_stc_production_direction(
                user_prompt
            )
        )

    return clean_text(
        output,
        50000,
    )


# =========================================================
# REFINEMENT PROMPT
# =========================================================

def build_refinement_prompt(
    original_user_prompt: str,
    *,
    stronger: bool = False,
    critique: str = "",
) -> str:

    directives = [
        (
            "Edit the provided image into a stronger final professional "
            "version while preserving the approved concept."
        ),

        (
            "Preserve the main subject, identity, composition logic and "
            "all areas that already work."
        ),

        (
            "Improve realism, lighting, materials, edge quality, hierarchy, "
            "balance and premium finish."
        ),

        (
            "Fix visible artifacts without adding unrelated objects."
        ),

        (
            "Do not add fake logos, random typography or watermarks."
        ),
    ]

    if stronger:

        directives.append(
            (
                "Push production polish toward world-class campaign quality "
                "without adding clutter."
            )
        )

    if critique:

        directives.append(
            (
                "Senior visual review corrections:\n"
                +
                clean_text(
                    critique,
                    7000,
                )
            )
        )

    if _is_stc_request(
        original_user_prompt
    ):

        directives.append(
            (
                "For STC Bank keep all advertising text and logos absent; "
                "they will be added manually after generation."
            )
        )

    return (
        "ORIGINAL USER REQUEST:\n"
        +
        clean_text(
            original_user_prompt,
            20000,
        )
        +
        "\n\nFINAL REFINEMENT INSTRUCTIONS:\n"
        +
        "\n".join(
            f"- {item}"
            for item in directives
        )
    )


# =========================================================
# MODE NORMALIZATION
# =========================================================

def normalize_mode(
    mode: str,
) -> str:

    value = (
        clean_text(
            mode,
            100,
        )
        .lower()
        .strip()
    )

    aliases = {
        "auto":
            MODE_AUTO,

        "smart":
            MODE_AUTO,

        "default":
            MODE_AUTO,

        "fast":
            MODE_FAST,

        "openai":
            MODE_OPENAI,

        "gpt":
            MODE_OPENAI,

        "gpt-image-2":
            MODE_OPENAI,

        "google_fast":
            MODE_GOOGLE_FAST,

        "google-fast":
            MODE_GOOGLE_FAST,

        "google fast":
            MODE_GOOGLE_FAST,

        "nano banana 2":
            MODE_GOOGLE_FAST,

        "nano-banana-2":
            MODE_GOOGLE_FAST,

        "nanobanana2":
            MODE_GOOGLE_FAST,

        "google_pro":
            MODE_GOOGLE_PRO,

        "google-pro":
            MODE_GOOGLE_PRO,

        "google pro":
            MODE_GOOGLE_PRO,

        "nano banana pro":
            MODE_GOOGLE_PRO,

        "nano-banana-pro":
            MODE_GOOGLE_PRO,

        "pro":
            MODE_PRO,

        "fusion":
            MODE_PRO,

        "best":
            MODE_BEST,

        "max":
            MODE_BEST,

        "ultimate":
            MODE_BEST,

        "compare":
            MODE_COMPARE,

        "multi":
            MODE_COMPARE,
    }

    return aliases.get(
        value,
        MODE_AUTO,
    )


def resolve_effective_mode(
    prompt: str,
    mode: str = "",
    reference_count: int = 0,
) -> str:

    requested = (
        mode
        if clean_text(
            mode,
            100,
        )
        else DEFAULT_MODE
    )

    chosen = normalize_mode(
        requested
    )

    if chosen != MODE_AUTO:

        return chosen

    #
    # Explicit Pro request only.
    #

    if contains_any(
        prompt,
        [
            "nano banana pro",
            "nano-banana-pro",
            "google pro",
            "google_pro",
            "استخدم برو",
            "استخدم pro",
            "موديل برو",
        ],
    ):

        return MODE_GOOGLE_PRO

    #
    # BEST keeps Nano Banana 2 unless BEST_USE_PRO=true.
    #

    if contains_any(
        prompt,
        [
            "أفضل نتيجة ممكنة",
            "افضل نتيجه ممكنه",
            "أقوى نتيجة",
            "اقوى نتيجه",
            "كل قواك",
            "best mode",
            "ultimate",
            "max quality",
            "best quality",
        ],
    ):

        return MODE_BEST

    if contains_any(
        prompt,
        [
            "سريع",
            "بسرعة",
            "بسرعه",
            "fast",
            "quick",
            "draft",
            "preview",
        ],
    ):

        return MODE_FAST

    #
    # IMPORTANT V2.1:
    #
    # premium / campaign / commercial and references do NOT
    # silently trigger Nano Banana Pro anymore.
    #
    # Nano Banana 2 is intentionally the high-volume default.
    #

    return MODE_GOOGLE_FAST


# =========================================================
# ROUTE
# =========================================================

def build_route(
    provider: str,
    model: str,
    reason: str,
    aspect_ratio: str,
    image_size: str,
    quality: str,
) -> ImageRoute:

    return ImageRoute(
        provider=provider,
        model=model,
        reason=reason,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        quality=quality,
    )


def openai_size_for_ratio(
    aspect_ratio: str,
) -> str:

    if aspect_ratio in {
        "9:16",
        "2:3",
        "3:4",
        "4:5",
        "1:4",
        "1:8",
    }:

        return "1024x1536"

    if aspect_ratio in {
        "16:9",
        "3:2",
        "4:3",
        "5:4",
        "21:9",
        "4:1",
        "8:1",
    }:

        return "1536x1024"

    return "1024x1024"


# =========================================================
# HTTP HELPERS
# =========================================================

def _safe_json(
    response: requests.Response,
) -> Dict[str, Any]:

    try:

        value = response.json()

        if isinstance(
            value,
            dict,
        ):

            return value

        return {
            "data":
                value,
        }

    except Exception:

        return {
            "raw":
                clean_text(
                    response.text,
                    12000,
                ),
        }


def _provider_error_message(
    provider: str,
    response: requests.Response,
) -> str:

    data = _safe_json(
        response
    )

    error = data.get(
        "error"
    )

    if isinstance(
        error,
        dict,
    ):

        message = (
            error.get(
                "message"
            )
            or
            error.get(
                "status"
            )
            or
            error.get(
                "code"
            )
            or
            str(
                error
            )
        )

    else:

        message = (
            error
            or
            data.get(
                "message"
            )
            or
            data.get(
                "detail"
            )
            or
            data.get(
                "raw"
            )
            or
            (
                "HTTP "
                +
                str(
                    response.status_code
                )
            )
        )

    return (
        provider
        +
        ": "
        +
        clean_text(
            message,
            6000,
        )
    )


# =========================================================
# IMAGE DOWNLOAD / BASE64
# =========================================================

def _download_image_url(
    url: str,
) -> Tuple[
    bytes,
    str,
]:

    response = requests.get(
        url,
        timeout=REQUEST_TIMEOUT,
    )

    if not response.ok:

        raise XPANDImageProviderError(
            (
                "فشل تنزيل الصورة: "
                +
                str(
                    response.status_code
                )
            )
        )

    mime_type = clean_text(
        response.headers.get(
            "Content-Type",
            "",
        ),
        100,
    ).split(";")[0]

    if not mime_type.startswith(
        "image/"
    ):

        mime_type = "image/png"

    return (
        response.content,
        mime_type,
    )


def _decode_base64_image(
    data: str,
) -> Optional[bytes]:

    value = clean_text(
        data,
        100000000,
    )

    if not value:

        return None

    if value.startswith(
        "data:image/"
    ):

        try:

            value = value.split(
                ",",
                1,
            )[1]

        except Exception:

            return None

    try:

        decoded = base64.b64decode(
            value
        )

        return (
            decoded
            or None
        )

    except Exception:

        return None


def image_data_uri(
    image_bytes: bytes,
    mime_type: str = "image/png",
) -> str:

    final_mime = clean_text(
        mime_type,
        100,
    ).lower()

    if not final_mime.startswith(
        "image/"
    ):

        final_mime = "image/png"

    encoded = base64.b64encode(
        image_bytes
    ).decode(
        "ascii"
    )

    return (
        "data:"
        +
        final_mime
        +
        ";base64,"
        +
        encoded
    )


# =========================================================
# IMAGE EXTRACTION
# =========================================================

def _find_inline_images(
    value: Any,
) -> List[
    Tuple[
        bytes,
        str,
    ]
]:

    found: List[
        Tuple[
            bytes,
            str,
        ]
    ] = []

    seen = set()

    def add_image(
        raw: Optional[bytes],
        mime_type: str,
    ) -> None:

        if not raw:

            return

        fingerprint = (
            len(
                raw
            ),
            raw[:32],
        )

        if fingerprint in seen:

            return

        seen.add(
            fingerprint
        )

        final_mime = clean_text(
            mime_type,
            100,
        ).lower()

        if not final_mime.startswith(
            "image/"
        ):

            final_mime = "image/png"

        found.append(
            (
                raw,
                final_mime,
            )
        )

    def walk(
        item: Any,
    ) -> None:

        if isinstance(
            item,
            dict,
        ):

            item_type = clean_text(
                item.get(
                    "type",
                    "",
                ),
                100,
            ).lower()

            mime_type = clean_text(
                (
                    item.get(
                        "mime_type"
                    )
                    or
                    item.get(
                        "mimeType"
                    )
                    or
                    "image/png"
                ),
                100,
            ).lower()

            b64_json = item.get(
                "b64_json"
            )

            if isinstance(
                b64_json,
                str,
            ):

                add_image(
                    _decode_base64_image(
                        b64_json
                    ),
                    mime_type,
                )

            base64_value = item.get(
                "base64"
            )

            if isinstance(
                base64_value,
                str,
            ):

                add_image(
                    _decode_base64_image(
                        base64_value
                    ),
                    mime_type,
                )

            data_value = item.get(
                "data"
            )

            if (
                isinstance(
                    data_value,
                    str,
                )
                and
                (
                    item_type
                    in {
                        "image",
                        "output_image",
                        "input_image",
                    }
                    or
                    mime_type.startswith(
                        "image/"
                    )
                )
            ):

                add_image(
                    _decode_base64_image(
                        data_value
                    ),
                    mime_type,
                )

            url = item.get(
                "url"
            )

            if (
                isinstance(
                    url,
                    str,
                )
                and
                url.startswith(
                    (
                        "http://",
                        "https://",
                    )
                )
                and
                (
                    item_type
                    in {
                        "image",
                        "output_image",
                    }
                    or
                    "image"
                    in item_type
                )
            ):

                try:

                    raw, downloaded_mime = (
                        _download_image_url(
                            url
                        )
                    )

                    add_image(
                        raw,
                        downloaded_mime,
                    )

                except Exception:

                    pass

            for nested in (
                item.values()
            ):

                if nested is (
                    b64_json
                ):

                    continue

                walk(
                    nested
                )

        elif isinstance(
            item,
            list,
        ):

            for nested in item:

                walk(
                    nested
                )

    walk(
        value
    )

    return found


# =========================================================
# RESOLUTION FINALIZER
# =========================================================

def _finalize_requested_resolution(
    image_bytes: bytes,
    mime_type: str,
    requested_size: str,
) -> Tuple[
    bytes,
    str,
]:

    final_size = normalize_image_size(
        requested_size
    )

    #
    # Native 1K/2K/4K/512 are already produced by Gemini.
    #

    if final_size != "HD":

        return (
            image_bytes,
            mime_type,
        )

    try:

        image = Image.open(
            io.BytesIO(
                image_bytes
            )
        )

        image.load()

        width, height = (
            image.size
        )

        short_side = min(
            width,
            height,
        )

        if short_side <= 720:

            return (
                image_bytes,
                mime_type,
            )

        scale = (
            720.0
            /
            float(
                short_side
            )
        )

        final_width = max(
            1,
            int(
                round(
                    width
                    *
                    scale
                )
            ),
        )

        final_height = max(
            1,
            int(
                round(
                    height
                    *
                    scale
                )
            ),
        )

        image = image.resize(
            (
                final_width,
                final_height,
            ),
            Image.Resampling.LANCZOS,
        )

        output = io.BytesIO()

        source_mime = clean_text(
            mime_type,
            100,
        ).lower()

        if (
            source_mime
            in {
                "image/jpeg",
                "image/jpg",
            }
            and
            image.mode
            in {
                "RGB",
                "L",
            }
        ):

            image.save(
                output,
                format="JPEG",
                quality=95,
                optimize=True,
            )

            return (
                output.getvalue(),
                "image/jpeg",
            )

        if image.mode not in {
            "RGB",
            "RGBA",
        }:

            image = image.convert(
                "RGBA"
            )

        image.save(
            output,
            format="PNG",
            optimize=True,
        )

        return (
            output.getvalue(),
            "image/png",
        )

    except Exception:

        return (
            image_bytes,
            mime_type,
        )


# =========================================================
# JSON / STRUCTURED HELPERS
# =========================================================

def looks_like_json_request(
    prompt: str,
) -> bool:

    source = clean_text(
        prompt,
        50000,
    ).lower()

    return any(
        marker
        in source
        for marker in [
            "return json only",
            "return valid json",
            "json only",
            "output json",
            "json schema",
            "return exactly one complete valid json object",
            "respond with json",
        ]
    )


def _strip_json_fences(
    value: str,
) -> str:

    text = clean_text(
        value,
        200000,
    ).strip()

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
    )

    return text.strip()


def normalize_json_text(
    value: str,
) -> str:

    text = _strip_json_fences(
        value
    )

    try:

        parsed = json.loads(
            text
        )

        if not isinstance(
            parsed,
            dict,
        ):

            raise ValueError(
                "Structured output is not a JSON object."
            )

        return json.dumps(
            parsed,
            ensure_ascii=False,
            separators=(
                ",",
                ":",
            ),
        )

    except Exception:

        pass

    start = text.find(
        "{"
    )

    end = text.rfind(
        "}"
    )

    if (
        start >= 0
        and
        end > start
    ):

        candidate = text[
            start:
            end + 1
        ]

        try:

            parsed = json.loads(
                candidate
            )

            if not isinstance(
                parsed,
                dict,
            ):

                raise ValueError(
                    "Structured output is not a JSON object."
                )

            return json.dumps(
                parsed,
                ensure_ascii=False,
                separators=(
                    ",",
                    ":",
                ),
            )

        except Exception:

            pass

    raise XPANDStructuredOutputError(
        "Structured output is not valid JSON."
    )


def json_text_is_valid(
    value: str,
) -> bool:

    try:

        parsed = json.loads(
            _strip_json_fences(
                value
            )
        )

        return isinstance(
            parsed,
            dict,
        )

    except Exception:

        return False


# =========================================================
# OPENAI RESPONSE TEXT EXTRACTION
# =========================================================

def _extract_openai_response_text(
    value: Any,
) -> str:

    if isinstance(
        value,
        dict,
    ):

        direct = value.get(
            "output_text"
        )

        if (
            isinstance(
                direct,
                str,
            )
            and
            direct.strip()
        ):

            return direct.strip()

        if (
            value.get(
                "type"
            )
            ==
            "output_text"
        ):

            text = value.get(
                "text"
            )

            if (
                isinstance(
                    text,
                    str,
                )
                and
                text.strip()
            ):

                return text.strip()

        for key in [
            "output",
            "content",
            "message",
            "messages",
            "result",
            "response",
        ]:

            if key in value:

                found = (
                    _extract_openai_response_text(
                        value.get(
                            key
                        )
                    )
                )

                if found:

                    return found

    elif isinstance(
        value,
        list,
    ):

        for item in value:

            found = (
                _extract_openai_response_text(
                    item
                )
            )

            if found:

                return found

    return ""


def _extract_openai_refusal(
    value: Any,
) -> str:

    if isinstance(
        value,
        dict,
    ):

        if (
            value.get(
                "type"
            )
            ==
            "refusal"
        ):

            refusal = (
                value.get(
                    "refusal"
                )
                or
                value.get(
                    "text"
                )
            )

            if refusal:

                return clean_text(
                    refusal,
                    3000,
                )

        for nested in (
            value.values()
        ):

            found = (
                _extract_openai_refusal(
                    nested
                )
            )

            if found:

                return found

    elif isinstance(
        value,
        list,
    ):

        for nested in value:

            found = (
                _extract_openai_refusal(
                    nested
                )
            )

            if found:

                return found

    return ""


def response_status_error(
    data: Dict[str, Any],
) -> str:

    status = clean_text(
        data.get(
            "status",
            "",
        ),
        100,
    ).lower()

    if status in {
        "",
        "completed",
        "success",
        "succeeded",
    }:

        return ""

    error = data.get(
        "error"
    )

    if isinstance(
        error,
        dict,
    ):

        message = clean_text(
            (
                error.get(
                    "message"
                )
                or
                error.get(
                    "code"
                )
                or
                error
            ),
            3000,
        )

        if message:

            return (
                status
                +
                ": "
                +
                message
            )

    incomplete = data.get(
        "incomplete_details"
    )

    if isinstance(
        incomplete,
        dict,
    ):

        reason = clean_text(
            incomplete.get(
                "reason",
                "",
            ),
            1000,
        )

        if reason:

            return (
                status
                +
                ": "
                +
                reason
            )

    return status


# =========================================================
# REASONING
# =========================================================

def normalize_reasoning_effort(
    value: str,
    fallback: str,
) -> str:

    current = clean_text(
        value,
        50,
    ).lower()

    if current in (
        SUPPORTED_REASONING_LEVELS
    ):

        return current

    backup = clean_text(
        fallback,
        50,
    ).lower()

    if backup in (
        SUPPORTED_REASONING_LEVELS
    ):

        return backup

    return "low"


# =========================================================
# OPENAI USAGE TELEMETRY
# =========================================================

def _log_openai_usage(
    data: Dict[str, Any],
) -> None:

    if not OPENAI_USAGE_LOGGING:

        return

    usage = (
        data.get(
            "usage"
        )
        or
        {}
    )

    if not isinstance(
        usage,
        dict,
    ):

        return

    input_details = (
        usage.get(
            "input_tokens_details"
        )
        or
        {}
    )

    output_details = (
        usage.get(
            "output_tokens_details"
        )
        or
        {}
    )

    if not isinstance(
        input_details,
        dict,
    ):

        input_details = {}

    if not isinstance(
        output_details,
        dict,
    ):

        output_details = {}

    input_tokens = int(
        usage.get(
            "input_tokens",
            0,
        )
        or 0
    )

    cached_tokens = int(
        input_details.get(
            "cached_tokens",
            0,
        )
        or 0
    )

    output_tokens = int(
        usage.get(
            "output_tokens",
            0,
        )
        or 0
    )

    reasoning_tokens = int(
        output_details.get(
            "reasoning_tokens",
            0,
        )
        or 0
    )

    total_tokens = int(
        usage.get(
            "total_tokens",
            0,
        )
        or 0
    )

    print(
        "💰 XPAND SOL USAGE"
        +
        f" | input={input_tokens}"
        +
        f" | cached={cached_tokens}"
        +
        f" | output={output_tokens}"
        +
        f" | reasoning={reasoning_tokens}"
        +
        f" | total={total_tokens}"
    )


# =========================================================
# ONE OPENAI RESPONSES CALL
# =========================================================

def _call_openai_response_once(
    prompt: str,
    *,
    image_bytes: Optional[bytes],
    image_mime_type: str,
    json_mode: bool,
    json_schema: Optional[
        Dict[str, Any]
    ],
    json_schema_name: str,
    reasoning_effort: str,
    max_output_tokens: int,
) -> Dict[str, Any]:

    if not OPENAI_API_KEY:

        raise XPANDImageConfigurationError(
            "OPENAI_API_KEY مش موجود."
        )

    content: List[
        Dict[str, Any]
    ] = [
        {
            "type":
                "input_text",

            "text":
                clean_text(
                    prompt,
                    50000,
                ),
        }
    ]

    if image_bytes:

        content.append(
            {
                "type":
                    "input_image",

                "image_url":
                    image_data_uri(
                        image_bytes,
                        image_mime_type,
                    ),

                "detail":
                    OPENAI_VISION_DETAIL,
            }
        )

    payload: Dict[
        str,
        Any
    ] = {
        "model":
            OPENAI_DIRECTOR_MODEL,

        "input": [
            {
                "role":
                    "user",

                "content":
                    content,
            }
        ],

        "reasoning": {
            "effort":
                normalize_reasoning_effort(
                    reasoning_effort,
                    "low",
                ),
        },

        "max_output_tokens":
            int(
                max_output_tokens
            ),

        "store":
            False,
    }

    if OPENAI_PROMPT_CACHE_KEY:

        payload[
            "prompt_cache_key"
        ] = (
            OPENAI_PROMPT_CACHE_KEY
        )

    if OPENAI_PROMPT_CACHE_RETENTION:

        payload[
            "prompt_cache_retention"
        ] = (
            OPENAI_PROMPT_CACHE_RETENTION
        )

    if json_schema:

        schema_name = re.sub(
            r"[^a-zA-Z0-9_\-]",
            "_",
            (
                clean_text(
                    json_schema_name,
                    64,
                )
                or
                "xpand_structured_output"
            ),
        )[:64]

        payload[
            "text"
        ] = {
            "format": {
                "type":
                    "json_schema",

                "name":
                    schema_name,

                "schema":
                    json_schema,

                "strict":
                    True,
            },

            "verbosity":
                "low",
        }

    elif json_mode:

        payload[
            "text"
        ] = {
            "format": {
                "type":
                    "json_object",
            },

            "verbosity":
                "low",
        }

    response = requests.post(
        OPENAI_RESPONSES_URL,
        headers={
            "Authorization":
                (
                    "Bearer "
                    +
                    OPENAI_API_KEY
                ),

            "Content-Type":
                "application/json",
        },
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )

    if not response.ok:

        raise XPANDImageProviderError(
            _provider_error_message(
                "GPT-5.6 Sol",
                response,
            )
        )

    data = _safe_json(
        response
    )

    if not isinstance(
        data,
        dict,
    ):

        raise XPANDImageProviderError(
            (
                "GPT-5.6 Sol returned "
                "an invalid response object."
            )
        )

    _log_openai_usage(
        data
    )

    return data


# =========================================================
# OPENAI DIRECTOR INTERNAL
# =========================================================

def _call_openai_director_impl(
    prompt: str,
    *,
    image_bytes: Optional[
        bytes
    ] = None,
    image_mime_type: str = "image/png",
    json_mode: Optional[
        bool
    ] = None,
    json_schema: Optional[
        Dict[str, Any]
    ] = None,
    json_schema_name: str = (
        "xpand_structured_output"
    ),
) -> str:

    structured = bool(
        json_mode
        or
        json_schema
        or
        looks_like_json_request(
            prompt
        )
    )

    attempts = (
        OPENAI_STRUCTURED_RETRIES
        if structured
        else 1
    )

    last_error: Optional[
        Exception
    ] = None

    for attempt in range(
        1,
        attempts + 1,
    ):

        current_prompt = clean_text(
            prompt,
            50000,
        )

        current_reasoning = (
            OPENAI_STRUCTURED_REASONING
            if structured
            else
            OPENAI_DIRECTOR_REASONING
        )

        current_max_tokens = (
            OPENAI_STRUCTURED_MAX_OUTPUT_TOKENS
            if structured
            else
            OPENAI_DIRECTOR_MAX_OUTPUT_TOKENS
        )

        if (
            structured
            and
            attempt > 1
        ):

            current_max_tokens = (
                OPENAI_STRUCTURED_RETRY_MAX_OUTPUT_TOKENS
            )

            current_prompt += (
                "\n\n"
                "STRUCTURED RETRY CONTRACT:\n"
                "Return exactly ONE complete JSON object.\n"
                "Do not use Markdown.\n"
                "Do not add commentary before or after the JSON.\n"
                "Do not truncate arrays.\n"
                "Preserve all IDs requested by the original contract."
            )

        try:

            data = (
                _call_openai_response_once(
                    current_prompt,
                    image_bytes=image_bytes,
                    image_mime_type=(
                        image_mime_type
                    ),
                    json_mode=bool(
                        structured
                        and
                        not json_schema
                    ),
                    json_schema=json_schema,
                    json_schema_name=(
                        json_schema_name
                    ),
                    reasoning_effort=(
                        current_reasoning
                    ),
                    max_output_tokens=(
                        current_max_tokens
                    ),
                )
            )

            refusal = (
                _extract_openai_refusal(
                    data
                )
            )

            if refusal:

                raise XPANDImageProviderError(
                    (
                        "GPT-5.6 Sol refused "
                        "the request: "
                        +
                        refusal
                    )
                )

            status_problem = (
                response_status_error(
                    data
                )
            )

            text = (
                _extract_openai_response_text(
                    data
                )
            )

            if status_problem:

                raise XPANDImageProviderError(
                    (
                        "GPT-5.6 Sol response "
                        "status: "
                        +
                        status_problem
                    )
                )

            if not text:

                raise XPANDImageProviderError(
                    (
                        "GPT-5.6 Sol رجع "
                        "بدون نص."
                    )
                )

            if structured:

                normalized = (
                    normalize_json_text(
                        text
                    )
                )

                if attempt > 1:

                    print(
                        "✅ Structured Sol retry succeeded"
                    )

                return normalized

            return text

        except Exception as error:

            last_error = error

            if (
                structured
                and
                attempt < attempts
            ):

                print(
                    (
                        "⚠️ Structured Sol attempt "
                        +
                        str(
                            attempt
                        )
                        +
                        ": "
                        +
                        clean_text(
                            error,
                            1800,
                        )
                    )
                )

                continue

            raise

    raise XPANDImageProviderError(
        (
            "GPT-5.6 Sol failed: "
            +
            clean_text(
                last_error,
                3000,
            )
        )
    )


# =========================================================
# GEMINI TEXT EXTRACTION
# =========================================================

def _find_gemini_text(
    value: Any,
) -> str:

    if isinstance(
        value,
        dict,
    ):

        for key in [
            "output_text",
            "text",
        ]:

            item = value.get(
                key
            )

            if (
                isinstance(
                    item,
                    str,
                )
                and
                item.strip()
            ):

                return item.strip()

        for key in [
            "output",
            "outputs",
            "steps",
            "content",
            "parts",
            "result",
        ]:

            if key in value:

                found = (
                    _find_gemini_text(
                        value.get(
                            key
                        )
                    )
                )

                if found:

                    return found

    elif isinstance(
        value,
        list,
    ):

        for item in value:

            found = (
                _find_gemini_text(
                    item
                )
            )

            if found:

                return found

    return ""


# =========================================================
# GEMINI DIRECTOR
# =========================================================

def call_gemini_director(
    prompt: str,
    *,
    image_bytes: Optional[
        bytes
    ] = None,
    image_mime_type: str = "image/png",
    json_mode: Optional[
        bool
    ] = None,
    json_schema: Optional[
        Dict[str, Any]
    ] = None,
    json_schema_name: str = (
        "xpand_structured_output"
    ),
) -> str:

    global GEMINI_DIRECTOR_RUNTIME_MODEL

    if not GEMINI_API_KEY:

        raise XPANDImageConfigurationError(
            "GEMINI_API_KEY مش موجود."
        )

    final_prompt = clean_text(
        prompt,
        50000,
    )

    structured = bool(
        json_mode
        or
        json_schema
        or
        looks_like_json_request(
            final_prompt
        )
    )

    if structured:

        final_prompt += (
            "\n\n"
            "STRICT OUTPUT CONTRACT:\n"
            "Return exactly one COMPLETE valid JSON object.\n"
            "No Markdown.\n"
            "No prose before or after JSON.\n"
            "Do not rename required IDs.\n"
            "Do not truncate arrays."
        )

        if json_schema:

            final_prompt += (
                "\n\nJSON SCHEMA:\n"
                +
                json.dumps(
                    json_schema,
                    ensure_ascii=False,
                )
            )

    inputs: List[
        Dict[str, Any]
    ] = [
        {
            "type":
                "text",

            "text":
                final_prompt,
        }
    ]

    if image_bytes:

        inputs.append(
            {
                "type":
                    "image",

                "mime_type":
                    (
                        clean_text(
                            image_mime_type,
                            100,
                        )
                        or
                        "image/png"
                    ),

                "data":
                    base64.b64encode(
                        image_bytes
                    ).decode(
                        "ascii"
                    ),
            }
        )

    #
    # Search grounding is deliberately restricted to
    # explicit research jobs.
    #
    # A normal STC image-art-direction call should NOT spend
    # a grounded search merely because the word "bank" exists.
    #

    research_intent = contains_any(
        final_prompt,
        [
            "deep research",
            "بحث عميق",
            "competitor research",
            "بحث المنافسين",
            "latest campaign research",
            "current competitor",
            "research current",
            "ground with google search",
        ],
    )

    use_search = bool(
        GEMINI_SEARCH_GROUNDING
        and
        not structured
        and
        research_intent
    )

    candidates: List[str] = []

    def add_candidate(
        value: Any,
    ) -> None:

        model = clean_text(
            value,
            200,
        ).strip()

        if (
            model
            and
            model not in candidates
        ):

            candidates.append(
                model
            )

    add_candidate(
        GEMINI_DIRECTOR_RUNTIME_MODEL
    )

    for fallback_model in (
        GEMINI_DIRECTOR_FALLBACK_MODELS
    ):

        add_candidate(
            fallback_model
        )

    last_error = ""

    index = 0

    while (
        index < len(
            candidates
        )
        and
        index < 5
    ):

        model = candidates[
            index
        ]

        index += 1

        payload: Dict[
            str,
            Any
        ] = {
            "model":
                model,

            "input":
                inputs,
        }

        if use_search:

            payload[
                "tools"
            ] = [
                {
                    "type":
                        "google_search",
                }
            ]

        response = requests.post(
            GEMINI_INTERACTIONS_URL,
            headers={
                "x-goog-api-key":
                    GEMINI_API_KEY,

                "Content-Type":
                    "application/json",
            },
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )

        if response.ok:

            data = _safe_json(
                response
            )

            text = _find_gemini_text(
                data
            )

            if not text:

                raise XPANDImageProviderError(
                    (
                        "Gemini Director "
                        "رجع بدون نص."
                    )
                )

            if (
                model
                !=
                GEMINI_DIRECTOR_RUNTIME_MODEL
            ):

                print(
                    (
                        "✅ GEMINI DIRECTOR MODEL RECOVERED | "
                        +
                        model
                    )
                )

            GEMINI_DIRECTOR_RUNTIME_MODEL = (
                model
            )

            if structured:

                return normalize_json_text(
                    text
                )

            return text

        last_error = (
            _provider_error_message(
                "Gemini Director",
                response,
            )
        )

        model_problem = bool(
            re.search(
                (
                    r"model.+"
                    r"(?:not found|unsupported|invalid|"
                    r"does not exist|unavailable)"
                ),
                last_error,
                flags=(
                    re.IGNORECASE
                    |
                    re.DOTALL
                ),
            )
        )

        if not model_problem:

            raise XPANDImageProviderError(
                last_error
            )

        #
        # Use Google's suggested replacement when present.
        #

        suggestion = re.search(
            (
                r"Did you mean\s+"
                r"['\"]([^'\"]+)['\"]"
            ),
            last_error,
            flags=re.IGNORECASE,
        )

        if suggestion:

            suggested_model = (
                suggestion.group(
                    1
                ).strip()
            )

            if (
                suggested_model
                and
                suggested_model
                not in candidates
            ):

                candidates.insert(
                    index,
                    suggested_model,
                )

        if index < min(
            len(
                candidates
            ),
            5,
        ):

            print(
                (
                    "🔁 GEMINI DIRECTOR MODEL FALLBACK | "
                    +
                    model
                    +
                    " unavailable"
                )
            )

    raise XPANDImageProviderError(
        (
            last_error
            or
            (
                "Gemini Director: "
                "no usable Director model was found."
            )
        )
    )


# =========================================================
# PUBLIC DIRECTOR ROUTER
# =========================================================

def call_openai_director(
    prompt: str,
    *,
    image_bytes: Optional[
        bytes
    ] = None,
    image_mime_type: str = "image/png",
    json_mode: Optional[
        bool
    ] = None,
    json_schema: Optional[
        Dict[str, Any]
    ] = None,
    json_schema_name: str = (
        "xpand_structured_output"
    ),
) -> str:

    """
    Backwards-compatible public name.

    V2.1 routing:
    - Structured JSON -> GPT-5.6 Sol first.
    - Free-text work -> Gemini Flash-Lite first.
    - The other provider is a technical fallback.

    Creative Brain imports this exact function name, so
    backwards compatibility is mandatory.
    """

    structured = bool(
        json_mode
        or
        json_schema
        or
        looks_like_json_request(
            prompt
        )
    )

    errors: List[str] = []

    # =====================================================
    # STRUCTURED -> OPENAI FIRST
    # =====================================================

    if structured:

        if (
            STRUCTURED_DIRECTOR_PREFER_OPENAI
            and
            OPENAI_API_KEY
        ):

            try:

                return (
                    _call_openai_director_impl(
                        prompt,
                        image_bytes=image_bytes,
                        image_mime_type=(
                            image_mime_type
                        ),
                        json_mode=True,
                        json_schema=json_schema,
                        json_schema_name=(
                            json_schema_name
                        ),
                    )
                )

            except Exception as error:

                errors.append(
                    (
                        "openai_structured: "
                        +
                        clean_text(
                            error,
                            2500,
                        )
                    )
                )

                print(
                    (
                        "⚠️ OPENAI STRUCTURED DIRECTOR: "
                        +
                        clean_text(
                            error,
                            1200,
                        )
                    )
                )

        if GEMINI_API_KEY:

            try:

                return (
                    call_gemini_director(
                        prompt,
                        image_bytes=image_bytes,
                        image_mime_type=(
                            image_mime_type
                        ),
                        json_mode=True,
                        json_schema=json_schema,
                        json_schema_name=(
                            json_schema_name
                        ),
                    )
                )

            except Exception as error:

                errors.append(
                    (
                        "gemini_structured: "
                        +
                        clean_text(
                            error,
                            2500,
                        )
                    )
                )

        #
        # If preference was changed to Gemini-first and Gemini
        # failed, OpenAI still gets a final chance.
        #

        if (
            OPENAI_API_KEY
            and
            not STRUCTURED_DIRECTOR_PREFER_OPENAI
        ):

            try:

                return (
                    _call_openai_director_impl(
                        prompt,
                        image_bytes=image_bytes,
                        image_mime_type=(
                            image_mime_type
                        ),
                        json_mode=True,
                        json_schema=json_schema,
                        json_schema_name=(
                            json_schema_name
                        ),
                    )
                )

            except Exception as error:

                errors.append(
                    (
                        "openai_structured_fallback: "
                        +
                        clean_text(
                            error,
                            2500,
                        )
                    )
                )

        raise XPANDImageProviderError(
            (
                "Structured Director failed. "
                +
                " | ".join(
                    errors
                )
            )
        )

    # =====================================================
    # FREE TEXT -> GEMINI FIRST
    # =====================================================

    if (
        FREE_TEXT_DIRECTOR_PREFER_GEMINI
        and
        GEMINI_API_KEY
    ):

        try:

            return call_gemini_director(
                prompt,
                image_bytes=image_bytes,
                image_mime_type=(
                    image_mime_type
                ),
                json_mode=False,
                json_schema=None,
                json_schema_name=(
                    json_schema_name
                ),
            )

        except Exception as error:

            errors.append(
                (
                    "gemini_text: "
                    +
                    clean_text(
                        error,
                        2500,
                    )
                )
            )

            print(
                (
                    "⚠️ GEMINI TEXT DIRECTOR: "
                    +
                    clean_text(
                        error,
                        1200,
                    )
                )
            )

    if OPENAI_API_KEY:

        try:

            return (
                _call_openai_director_impl(
                    prompt,
                    image_bytes=image_bytes,
                    image_mime_type=(
                        image_mime_type
                    ),
                    json_mode=False,
                    json_schema=None,
                    json_schema_name=(
                        json_schema_name
                    ),
                )
            )

        except Exception as error:

            errors.append(
                (
                    "openai_text: "
                    +
                    clean_text(
                        error,
                        2500,
                    )
                )
            )

    if (
        GEMINI_API_KEY
        and
        not FREE_TEXT_DIRECTOR_PREFER_GEMINI
    ):

        try:

            return call_gemini_director(
                prompt,
                image_bytes=image_bytes,
                image_mime_type=(
                    image_mime_type
                ),
                json_mode=False,
            )

        except Exception as error:

            errors.append(
                (
                    "gemini_text_fallback: "
                    +
                    clean_text(
                        error,
                        2500,
                    )
                )
            )

    if not (
        OPENAI_API_KEY
        or
        GEMINI_API_KEY
    ):

        raise XPANDImageConfigurationError(
            (
                "لا يوجد OPENAI_API_KEY "
                "ولا GEMINI_API_KEY."
            )
        )

    raise XPANDImageProviderError(
        (
            "Director failed. "
            +
            " | ".join(
                errors
            )
        )
    )


# =========================================================
# EXPLICIT JSON HELPER
# =========================================================

def call_openai_director_json(
    prompt: str,
    *,
    image_bytes: Optional[
        bytes
    ] = None,
    image_mime_type: str = "image/png",
    json_schema: Optional[
        Dict[str, Any]
    ] = None,
    json_schema_name: str = (
        "xpand_structured_output"
    ),
) -> Dict[str, Any]:

    raw = call_openai_director(
        prompt,
        image_bytes=image_bytes,
        image_mime_type=(
            image_mime_type
        ),
        json_mode=True,
        json_schema=json_schema,
        json_schema_name=(
            json_schema_name
        ),
    )

    try:

        value = json.loads(
            raw
        )

    except Exception as error:

        raise XPANDStructuredOutputError(
            (
                "Structured response could "
                "not be decoded: "
                +
                clean_text(
                    error,
                    1000,
                )
            )
        )

    if not isinstance(
        value,
        dict,
    ):

        raise XPANDStructuredOutputError(
            (
                "Structured response "
                "is not a JSON object."
            )
        )

    return value


# =========================================================
# LEGACY SOL ART DIRECTION
# =========================================================

def build_sol_art_direction(
    original_prompt: str,
    aspect_ratio: str,
    image_size: str,
) -> str:

    request = f"""
You are the senior visual art director for XPAND Creative Agency.

Your task is NOT to generate the image.

Create a concise professional visual direction for an image-generation model.

ORIGINAL USER REQUEST:
{clean_text(original_prompt, 16000)}

TARGET ASPECT RATIO:
{aspect_ratio}

RESOLUTION INTENT:
{image_size}

Improve:
- composition
- camera
- focal hierarchy
- lighting
- materials
- palette
- depth
- negative space
- commercial impact
- premium finish

Preserve the exact user intent.
Do not invent unrelated brands or products.
Do not expose chain-of-thought.
Return only the final concise art-direction brief.
""".strip()

    return call_openai_director(
        request,
        json_mode=False,
    )


# =========================================================
# LEGACY SOL VISUAL CRITIC
# =========================================================

def build_sol_visual_critique(
    original_prompt: str,
    image_bytes: bytes,
    mime_type: str,
) -> str:

    request = f"""
You are the final senior visual reviewer for XPAND Creative Agency.

Review the attached generated image against this request:

{clean_text(original_prompt, 12000)}

Identify only meaningful improvements.

Evaluate:
- request accuracy
- composition
- hierarchy
- advertising quality
- lighting
- materials
- reflections
- shadows
- artifacts
- brand feel
- commercial readiness

Do not request a full redesign if the image is already strong.
Preserve the main product or subject.
Do not expose chain-of-thought.
Return only concise actionable corrections.
""".strip()

    return call_openai_director(
        request,
        image_bytes=image_bytes,
        image_mime_type=mime_type,
        json_mode=False,
    )


# =========================================================
# OPENAI GPT-IMAGE-2 GENERATION
# =========================================================

def generate_with_openai(
    prompt: str,
    original_prompt: str,
    route: ImageRoute,
    number: int = 1,
) -> List[
    GeneratedImage
]:

    if not OPENAI_API_KEY:

        raise XPANDImageConfigurationError(
            (
                "OPENAI_API_KEY مش موجود "
                "على Railway."
            )
        )

    number = max(
        1,
        min(
            int(
                number
                or 1
            ),
            4,
        ),
    )

    provider_size = (
        openai_size_for_ratio(
            route.aspect_ratio
        )
    )

    quality = (
        route.quality
        if route.quality
        in SUPPORTED_OPENAI_QUALITIES
        else "high"
    )

    payload: Dict[
        str,
        Any
    ] = {
        "model":
            route.model,

        "prompt":
            clean_text(
                prompt,
                32000,
            ),

        "n":
            number,

        "size":
            provider_size,

        "quality":
            quality,
    }

    started = time.monotonic()

    response = requests.post(
        OPENAI_IMAGE_GENERATION_URL,
        headers={
            "Authorization":
                (
                    "Bearer "
                    +
                    OPENAI_API_KEY
                ),

            "Content-Type":
                "application/json",
        },
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )

    elapsed = round(
        time.monotonic()
        -
        started,
        3,
    )

    if not response.ok:

        raise XPANDImageProviderError(
            _provider_error_message(
                "GPT-Image-2",
                response,
            )
        )

    data = _safe_json(
        response
    )

    images = _find_inline_images(
        data
    )

    if not images:

        raise XPANDImageProviderError(
            (
                "GPT-Image-2 نجح "
                "لكن ما رجعت صورة."
            )
        )

    request_id = clean_text(
        response.headers.get(
            "x-request-id",
            "",
        ),
        200,
    )

    results: List[
        GeneratedImage
    ] = []

    for index, (
        image_bytes,
        mime_type,
    ) in enumerate(
        images[:number],
        start=1,
    ):

        current_id = (
            request_id
            or
            (
                "og-"
                +
                uuid.uuid4().hex[:12]
            )
        )

        if number > 1:

            current_id += (
                "-"
                +
                str(
                    index
                )
            )

        results.append(
            GeneratedImage(
                image_bytes=(
                    image_bytes
                ),
                mime_type=(
                    mime_type
                    or
                    "image/png"
                ),
                provider=(
                    route.provider
                ),
                model=(
                    route.model
                ),
                prompt=prompt,
                original_prompt=(
                    original_prompt
                ),
                aspect_ratio=(
                    route.aspect_ratio
                ),
                image_size=(
                    route.image_size
                ),
                quality=quality,
                route_reason=(
                    route.reason
                ),
                request_id=(
                    current_id
                ),
                metadata={
                    "generation_type":
                        "openai_generation",

                    "provider_size":
                        provider_size,

                    "requested_image_size":
                        route.image_size,

                    "elapsed_seconds":
                        elapsed,
                },
            )
        )

    return results


# =========================================================
# OPENAI EDIT
# =========================================================

def edit_with_openai(
    input_image_bytes: bytes,
    input_mime_type: str,
    prompt: str,
    original_prompt: str,
    route: ImageRoute,
    *,
    final_provider: str = (
        PROVIDER_OPENAI
    ),
    final_model_label: str = (
        OPENAI_IMAGE_MODEL
    ),
    metadata: Optional[
        Dict[str, Any]
    ] = None,
) -> GeneratedImage:

    if not OPENAI_API_KEY:

        raise XPANDImageConfigurationError(
            "OPENAI_API_KEY مش موجود."
        )

    provider_size = (
        openai_size_for_ratio(
            route.aspect_ratio
        )
    )

    quality = (
        route.quality
        if route.quality
        in SUPPORTED_OPENAI_QUALITIES
        else "high"
    )

    mime_type = clean_text(
        input_mime_type,
        100,
    ).lower()

    if not mime_type.startswith(
        "image/"
    ):

        mime_type = "image/png"

    extension = (
        ".jpg"
        if mime_type
        in {
            "image/jpeg",
            "image/jpg",
        }
        else
        ".png"
    )

    files = {
        "image": (
            (
                "xpand-input"
                +
                extension
            ),
            input_image_bytes,
            mime_type,
        )
    }

    form_data = {
        "model":
            route.model,

        "prompt":
            clean_text(
                prompt,
                32000,
            ),

        "size":
            provider_size,

        "quality":
            quality,

        "n":
            "1",
    }

    response = requests.post(
        OPENAI_IMAGE_EDITS_URL,
        headers={
            "Authorization":
                (
                    "Bearer "
                    +
                    OPENAI_API_KEY
                ),
        },
        data=form_data,
        files=files,
        timeout=REQUEST_TIMEOUT,
    )

    if not response.ok:

        raise XPANDImageProviderError(
            _provider_error_message(
                "GPT-Image-2 Edit",
                response,
            )
        )

    payload = _safe_json(
        response
    )

    images = _find_inline_images(
        payload
    )

    if not images:

        raise XPANDImageProviderError(
            (
                "GPT-Image-2 Edit نجح "
                "لكن ما رجعت صورة."
            )
        )

    image_bytes, output_mime = (
        images[0]
    )

    request_id = clean_text(
        response.headers.get(
            "x-request-id",
            "",
        ),
        200,
    )

    if not request_id:

        request_id = (
            "oe-"
            +
            uuid.uuid4().hex[:12]
        )

    final_metadata = dict(
        metadata
        or
        {}
    )

    final_metadata[
        "generation_type"
    ] = (
        "final_refinement"
    )

    final_metadata[
        "final_edit_model"
    ] = (
        OPENAI_IMAGE_MODEL
    )

    return GeneratedImage(
        image_bytes=image_bytes,
        mime_type=(
            output_mime
            or
            "image/png"
        ),
        provider=final_provider,
        model=final_model_label,
        prompt=prompt,
        original_prompt=(
            original_prompt
        ),
        aspect_ratio=(
            route.aspect_ratio
        ),
        image_size=(
            route.image_size
        ),
        quality=quality,
        route_reason=(
            "Final image refinement "
            "completed with GPT-Image-2."
        ),
        request_id=request_id,
        metadata=final_metadata,
    )


# =========================================================
# GOOGLE ERROR
# =========================================================

def looks_like_google_quota_error(
    error: Any,
) -> bool:

    text = normalize_arabic(
        error
    )

    markers = [
        "quota",
        "rate limit",
        "billing",
        "free tier",
        "resource exhausted",
        "429",
        "exceeded",
        "too many requests",
    ]

    return any(
        normalize_arabic(
            marker
        )
        in text
        for marker in markers
    )


# =========================================================
# GEMINI IMAGE GENERATION
# =========================================================

def _generate_one_with_gemini(
    prompt: str,
    original_prompt: str,
    route: ImageRoute,
    index: int = 0,
) -> GeneratedImage:

    if not GEMINI_API_KEY:

        raise XPANDImageConfigurationError(
            "GEMINI_API_KEY مش موجود."
        )

    requested_size = (
        route.image_size
    )

    provider_size = (
        google_provider_image_size(
            requested_size
        )
    )

    thinking_level = (
        GEMINI_PRO_IMAGE_THINKING
        if route.model
        ==
        GOOGLE_IMAGE_PRO_MODEL
        else
        GEMINI_FAST_IMAGE_THINKING
    )

    payload: Dict[
        str,
        Any
    ] = {
        "model":
            route.model,

        "input":
            clean_text(
                prompt,
                50000,
            ),

        "response_format": {
            "type":
                "image",

            "aspect_ratio":
                route.aspect_ratio,

            "image_size":
                provider_size,

            "mime_type":
                "image/jpeg",
        },
    }

    if thinking_level:

        payload[
            "generation_config"
        ] = {
            "thinking_level":
                thinking_level,
        }

    response = requests.post(
        GEMINI_INTERACTIONS_URL,
        headers={
            "x-goog-api-key":
                GEMINI_API_KEY,

            "Content-Type":
                "application/json",
        },
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )

    if not response.ok:

        raise XPANDImageProviderError(
            _provider_error_message(
                "Gemini Image",
                response,
            )
        )

    data = _safe_json(
        response
    )

    images = _find_inline_images(
        data
    )

    if not images:

        raise XPANDImageProviderError(
            (
                "Gemini رجع استجابة ناجحة "
                "لكن ما لقيت صورة."
            )
        )

    image_bytes, mime_type = (
        images[0]
    )

    image_bytes, mime_type = (
        _finalize_requested_resolution(
            image_bytes,
            mime_type,
            requested_size,
        )
    )

    request_id = clean_text(
        data.get(
            "id",
            "",
        ),
        200,
    )

    if not request_id:

        request_id = (
            "gg-"
            +
            uuid.uuid4().hex[:12]
        )

    if index > 0:

        request_id += (
            "-"
            +
            str(
                index + 1
            )
        )

    return GeneratedImage(
        image_bytes=image_bytes,
        mime_type=(
            mime_type
            or
            "image/jpeg"
        ),
        provider=(
            route.provider
        ),
        model=(
            route.model
        ),
        prompt=prompt,
        original_prompt=(
            original_prompt
        ),
        aspect_ratio=(
            route.aspect_ratio
        ),
        image_size=(
            requested_size
        ),
        quality=(
            route.quality
        ),
        route_reason=(
            route.reason
        ),
        request_id=request_id,
        metadata={
            "generation_type":
                "gemini_generation",

            "google_model":
                route.model,

            "google_image_size":
                provider_size,

            "delivered_image_size":
                requested_size,

            "thinking_level":
                thinking_level,
        },
    )


def generate_with_gemini(
    prompt: str,
    original_prompt: str,
    route: ImageRoute,
    number: int = 1,
) -> List[
    GeneratedImage
]:

    number = max(
        1,
        min(
            int(
                number
                or 1
            ),
            4,
        ),
    )

    results: List[
        GeneratedImage
    ] = []

    errors: List[str] = []

    for index in range(
        number
    ):

        try:

            result = (
                _generate_one_with_gemini(
                    prompt=prompt,
                    original_prompt=(
                        original_prompt
                    ),
                    route=route,
                    index=index,
                )
            )

            results.append(
                result
            )

        except Exception as error:

            errors.append(
                clean_text(
                    error,
                    3000,
                )
            )

    if not results:

        raise XPANDImageProviderError(
            (
                "Gemini generation failed.\n"
                +
                "\n".join(
                    errors
                )
            )
        )

    return results


# =========================================================
# GEMINI MULTI-IMAGE EDIT
# =========================================================

def edit_with_gemini(
    input_images: Sequence[
        Tuple[
            bytes,
            str,
        ]
    ],
    prompt: str,
    *,
    aspect_ratio: str = "4:5",
    image_size: str = "",
    pro: bool = False,
) -> GeneratedImage:

    if not GEMINI_API_KEY:

        raise XPANDImageConfigurationError(
            "GEMINI_API_KEY مش موجود."
        )

    if not input_images:

        raise XPANDImageError(
            "لا توجد صور للتعديل."
        )

    final_aspect_ratio = (
        detect_aspect_ratio(
            prompt,
            aspect_ratio,
        )
    )

    final_size = detect_image_size(
        prompt,
        image_size,
    )

    provider_size = (
        google_provider_image_size(
            final_size
        )
    )

    model = (
        GOOGLE_IMAGE_PRO_MODEL
        if pro
        else
        GOOGLE_IMAGE_FAST_MODEL
    )

    provider = (
        PROVIDER_GOOGLE_PRO
        if pro
        else
        PROVIDER_GOOGLE_FAST
    )

    instruction = (
        build_professional_prompt(
            prompt,
            final_aspect_ratio,
            final_size,
        )
    )

    instruction += (
        "\n\n"
        "========================================\n"
        "REFERENCE ORDER CONTRACT\n"
        "========================================\n"
        "Image 1 is the BASE image unless the user explicitly says otherwise.\n"
        "Images 2+ are references or source images.\n"
        "Preserve untouched areas of the base image.\n"
        "Transfer only what the user requested from each reference.\n"
        "Match perspective, scale, camera, light direction, contact shadows, "
        "reflections, color temperature and depth so the final result feels "
        "like one coherent photograph.\n"
        "Never add generic fintech effects, laser beams, neon routes or "
        "floating interface decorations unless explicitly requested."
    )

    inputs: List[
        Dict[str, Any]
    ] = [
        {
            "type":
                "text",

            "text":
                instruction,
        }
    ]

    #
    # Nano Banana 2 supports several reference images.
    # Keep a hard practical cap of 10 here for compatibility.
    #

    for (
        image_bytes,
        mime_type,
    ) in list(
        input_images
    )[:10]:

        inputs.append(
            {
                "type":
                    "image",

                "mime_type":
                    (
                        clean_text(
                            mime_type,
                            100,
                        )
                        or
                        "image/png"
                    ),

                "data":
                    base64.b64encode(
                        image_bytes
                    ).decode(
                        "ascii"
                    ),
            }
        )

    thinking_level = (
        GEMINI_PRO_IMAGE_THINKING
        if pro
        else
        GEMINI_FAST_IMAGE_THINKING
    )

    payload: Dict[
        str,
        Any
    ] = {
        "model":
            model,

        "input":
            inputs,

        "response_format": {
            "type":
                "image",

            "aspect_ratio":
                final_aspect_ratio,

            "image_size":
                provider_size,

            "mime_type":
                "image/jpeg",
        },
    }

    if thinking_level:

        payload[
            "generation_config"
        ] = {
            "thinking_level":
                thinking_level,
        }

    response = requests.post(
        GEMINI_INTERACTIONS_URL,
        headers={
            "x-goog-api-key":
                GEMINI_API_KEY,

            "Content-Type":
                "application/json",
        },
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )

    if not response.ok:

        raise XPANDImageProviderError(
            _provider_error_message(
                "Nano Banana Edit",
                response,
            )
        )

    data = _safe_json(
        response
    )

    images = _find_inline_images(
        data
    )

    if not images:

        raise XPANDImageProviderError(
            (
                "Nano Banana Edit نجح "
                "لكن لم يرجع صورة."
            )
        )

    output, output_mime = (
        images[0]
    )

    output, output_mime = (
        _finalize_requested_resolution(
            output,
            output_mime,
            final_size,
        )
    )

    return GeneratedImage(
        image_bytes=output,
        mime_type=(
            output_mime
            or
            "image/jpeg"
        ),
        provider=provider,
        model=model,
        prompt=instruction,
        original_prompt=prompt,
        aspect_ratio=(
            final_aspect_ratio
        ),
        image_size=(
            final_size
        ),
        quality=(
            "high"
            if pro
            else
            "medium"
        ),
        route_reason=(
            "Gemini multi-image edit."
        ),
        request_id=(
            clean_text(
                data.get(
                    "id",
                    "",
                ),
                200,
            )
            or
            (
                "ge-"
                +
                uuid.uuid4().hex[:12]
            )
        ),
        metadata={
            "generation_type":
                "gemini_multi_image_edit",

            "input_images":
                len(
                    input_images
                ),

            "google_image_size":
                provider_size,

            "delivered_image_size":
                final_size,

            "thinking_level":
                thinking_level,
        },
    )


# =========================================================
# OPENAI DIRECT ROUTE
# =========================================================

def run_openai_direct(
    original_prompt: str,
    *,
    aspect_ratio: str,
    image_size: str,
    quality: str,
    number: int = 1,
) -> ImageGenerationResponse:

    started = time.monotonic()

    enhanced = (
        build_professional_prompt(
            original_prompt,
            aspect_ratio,
            image_size,
        )
    )

    route = build_route(
        PROVIDER_OPENAI,
        OPENAI_IMAGE_MODEL,
        "Direct GPT-Image-2 generation.",
        aspect_ratio,
        image_size,
        quality,
    )

    images = generate_with_openai(
        enhanced,
        original_prompt,
        route,
        number,
    )

    return ImageGenerationResponse(
        ok=True,
        images=images,
        selected_route=(
            MODE_OPENAI
        ),
        routes=[
            route
        ],
        original_prompt=(
            original_prompt
        ),
        enhanced_prompt=(
            enhanced
        ),
        elapsed_seconds=round(
            time.monotonic()
            -
            started,
            3,
        ),
        errors=[],
    )


# =========================================================
# GOOGLE DIRECT ROUTE
# =========================================================

def run_google_direct(
    original_prompt: str,
    *,
    pro: bool,
    aspect_ratio: str,
    image_size: str,
    quality: str,
    number: int = 1,
    allow_fallback: bool = False,
) -> ImageGenerationResponse:

    started = time.monotonic()

    enhanced = (
        build_professional_prompt(
            original_prompt,
            aspect_ratio,
            image_size,
        )
    )

    provider = (
        PROVIDER_GOOGLE_PRO
        if pro
        else
        PROVIDER_GOOGLE_FAST
    )

    model = (
        GOOGLE_IMAGE_PRO_MODEL
        if pro
        else
        GOOGLE_IMAGE_FAST_MODEL
    )

    route = build_route(
        provider,
        model,
        (
            "Nano Banana Pro image generation."
            if pro
            else
            "Nano Banana 2 image generation."
        ),
        aspect_ratio,
        image_size,
        quality,
    )

    errors: List[str] = []

    try:

        images = generate_with_gemini(
            enhanced,
            original_prompt,
            route,
            number,
        )

        return ImageGenerationResponse(
            ok=True,
            images=images,
            selected_route=(
                MODE_GOOGLE_PRO
                if pro
                else
                MODE_GOOGLE_FAST
            ),
            routes=[
                route
            ],
            original_prompt=(
                original_prompt
            ),
            enhanced_prompt=(
                enhanced
            ),
            elapsed_seconds=round(
                time.monotonic()
                -
                started,
                3,
            ),
            errors=[],
        )

    except Exception as error:

        google_error = clean_text(
            error,
            4000,
        )

        errors.append(
            (
                "google: "
                +
                google_error
            )
        )

        print(
            (
                "⚠️ GOOGLE IMAGE ROUTE: "
                +
                google_error
            )
        )

        if not allow_fallback:

            raise

    # =====================================================
    # ACTUAL OPENAI FALLBACK
    # =====================================================

    if (
        allow_fallback
        and
        OPENAI_IMAGE_FALLBACK_ENABLED
        and
        OPENAI_API_KEY
    ):

        print(
            (
                "🔁 GOOGLE -> OPENAI IMAGE FALLBACK"
                +
                " | GPT-Image-2"
            )
        )

        openai_route = build_route(
            PROVIDER_OPENAI,
            OPENAI_IMAGE_MODEL,
            (
                "GPT-Image-2 fallback after "
                "Gemini image-generation failure."
            ),
            aspect_ratio,
            image_size,
            quality,
        )

        try:

            images = generate_with_openai(
                enhanced,
                original_prompt,
                openai_route,
                number,
            )

            return ImageGenerationResponse(
                ok=True,
                images=images,
                selected_route=(
                    MODE_OPENAI
                ),
                routes=[
                    route,
                    openai_route,
                ],
                original_prompt=(
                    original_prompt
                ),
                enhanced_prompt=(
                    enhanced
                ),
                elapsed_seconds=round(
                    time.monotonic()
                    -
                    started,
                    3,
                ),
                errors=errors,
            )

        except Exception as error:

            errors.append(
                (
                    "openai_fallback: "
                    +
                    clean_text(
                        error,
                        4000,
                    )
                )
            )

    raise XPANDImageProviderError(
        (
            "Image generation failed.\n"
            +
            "\n".join(
                errors
            )
        )
    )


# =========================================================
# COST-CONTROLLED OPENAI BEST
# =========================================================

OPENAI_BEST_USE_DIRECTOR = env_bool(
    "XPAND_OPENAI_BEST_USE_DIRECTOR",
    False,
)


def run_openai_best(
    original_prompt: str,
    *,
    aspect_ratio: str,
    image_size: str,
    quality: str,
    number: int = 1,
) -> ImageGenerationResponse:

    started = time.monotonic()

    errors: List[str] = []

    base_direction = (
        build_professional_prompt(
            original_prompt,
            aspect_ratio,
            image_size,
        )
    )

    #
    # No extra Director call by default.
    #
    # This keeps explicit OpenAI fallback predictable in cost.
    #

    if OPENAI_BEST_USE_DIRECTOR:

        try:

            art_direction = (
                build_sol_art_direction(
                    original_prompt,
                    aspect_ratio,
                    image_size,
                )
            )

            final_prompt = (
                "ORIGINAL REQUEST:\n"
                +
                clean_text(
                    original_prompt,
                    16000,
                )
                +
                "\n\n"
                "XPAND BASE DIRECTION:\n"
                +
                base_direction
                +
                "\n\n"
                "SENIOR ART DIRECTION:\n"
                +
                art_direction
            )

        except Exception as error:

            errors.append(
                (
                    "director: "
                    +
                    clean_text(
                        error,
                        2500,
                    )
                )
            )

            final_prompt = (
                base_direction
            )

    else:

        final_prompt = (
            base_direction
        )

    route = build_route(
        PROVIDER_OPENAI,
        OPENAI_IMAGE_MODEL,
        (
            "Cost-controlled OpenAI BEST "
            "with GPT-Image-2."
        ),
        aspect_ratio,
        image_size,
        quality,
    )

    images = generate_with_openai(
        final_prompt,
        original_prompt,
        route,
        number,
    )

    return ImageGenerationResponse(
        ok=True,
        images=images,
        selected_route=(
            MODE_BEST
        ),
        routes=[
            route
        ],
        original_prompt=(
            original_prompt
        ),
        enhanced_prompt=(
            final_prompt
        ),
        elapsed_seconds=round(
            time.monotonic()
            -
            started,
            3,
        ),
        errors=errors,
    )


# =========================================================
# BACKWARDS-COMPATIBLE FUSION WRAPPERS
# =========================================================

def run_openai_fusion(
    original_prompt: str,
    *,
    aspect_ratio: str,
    image_size: str,
    quality: str,
    number: int = 1,
    stronger: bool = True,
    initial_art_direction: str = "",
    inherited_errors: Optional[
        List[str]
    ] = None,
) -> ImageGenerationResponse:

    result = run_openai_best(
        original_prompt,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        quality=quality,
        number=number,
    )

    result.errors.extend(
        inherited_errors
        or
        []
    )

    return result


def run_google_openai_fusion(
    original_prompt: str,
    *,
    aspect_ratio: str,
    image_size: str,
    quality: str,
    number: int = 1,
    stronger: bool = False,
) -> ImageGenerationResponse:

    #
    # Compatibility wrapper.
    #
    # Prefer Nano Banana 2 and allow GPT-Image-2 only as
    # technical fallback.
    #

    return run_google_direct(
        original_prompt,
        pro=False,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        quality=quality,
        number=number,
        allow_fallback=True,
    )


# =========================================================
# COMPARE
# =========================================================

def run_compare(
    original_prompt: str,
    *,
    aspect_ratio: str,
    image_size: str,
    quality: str,
    number: int = 1,
) -> ImageGenerationResponse:

    started = time.monotonic()

    results: List[
        GeneratedImage
    ] = []

    routes: List[
        ImageRoute
    ] = []

    errors: List[str] = []

    prompt = (
        build_professional_prompt(
            original_prompt,
            aspect_ratio,
            image_size,
        )
    )

    if OPENAI_API_KEY:

        openai_route = build_route(
            PROVIDER_OPENAI,
            OPENAI_IMAGE_MODEL,
            "Compare: GPT-Image-2.",
            aspect_ratio,
            image_size,
            quality,
        )

        try:

            openai_images = (
                generate_with_openai(
                    prompt,
                    original_prompt,
                    openai_route,
                    1,
                )
            )

            results.extend(
                openai_images
            )

            routes.append(
                openai_route
            )

        except Exception as error:

            errors.append(
                (
                    "openai_compare: "
                    +
                    clean_text(
                        error,
                        3000,
                    )
                )
            )

    if GEMINI_API_KEY:

        google_route = build_route(
            PROVIDER_GOOGLE_FAST,
            GOOGLE_IMAGE_FAST_MODEL,
            "Compare: Nano Banana 2.",
            aspect_ratio,
            image_size,
            quality,
        )

        try:

            google_images = (
                generate_with_gemini(
                    prompt,
                    original_prompt,
                    google_route,
                    1,
                )
            )

            results.extend(
                google_images
            )

            routes.append(
                google_route
            )

        except Exception as error:

            errors.append(
                (
                    "google_compare: "
                    +
                    clean_text(
                        error,
                        3000,
                    )
                )
            )

    if not results:

        raise XPANDImageProviderError(
            (
                "Compare mode failed: "
                +
                " | ".join(
                    errors
                )
            )
        )

    requested = max(
        1,
        min(
            int(
                number
                or 1
            ),
            len(
                results
            ),
        ),
    )

    return ImageGenerationResponse(
        ok=True,
        images=results[
            :requested
        ],
        selected_route=(
            MODE_COMPARE
        ),
        routes=routes,
        original_prompt=(
            original_prompt
        ),
        enhanced_prompt=prompt,
        elapsed_seconds=round(
            time.monotonic()
            -
            started,
            3,
        ),
        errors=errors,
    )


# =========================================================
# MAIN IMAGE GENERATION API
# =========================================================

def generate_image(
    prompt: str,
    *,
    mode: str = "",
    number: int = 1,
    aspect_ratio: str = "",
    image_size: str = "",
    quality: str = "",
    reference_count: int = 0,
    allow_fallback: bool = True,
    **kwargs: Any,
) -> ImageGenerationResponse:

    original_prompt = clean_text(
        prompt,
        50000,
    )

    if not original_prompt:

        raise XPANDImageError(
            "وصف الصورة فاضي."
        )

    final_aspect_ratio = (
        detect_aspect_ratio(
            original_prompt,
            aspect_ratio,
        )
    )

    final_image_size = (
        detect_image_size(
            original_prompt,
            image_size,
        )
    )

    final_quality = (
        detect_quality(
            original_prompt,
            quality,
        )
    )

    effective_mode = (
        resolve_effective_mode(
            original_prompt,
            mode,
            reference_count,
        )
    )

    number = max(
        1,
        min(
            int(
                number
                or 1
            ),
            4,
        ),
    )

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND IMAGE REQUEST V2.1"
    )
    print(
        "=========================================="
    )
    print(
        "🎯 Effective mode:",
        effective_mode,
    )
    print(
        "📐 Aspect ratio:",
        final_aspect_ratio,
    )
    print(
        "🖼️ Resolution intent:",
        final_image_size,
    )
    print(
        "💎 Quality:",
        final_quality,
    )
    print(
        "🧠 References:",
        int(
            reference_count
            or 0
        ),
    )
    print("")

    # =====================================================
    # OPENAI EXPLICIT
    # =====================================================

    if effective_mode == (
        MODE_OPENAI
    ):

        return run_openai_direct(
            original_prompt,
            aspect_ratio=(
                final_aspect_ratio
            ),
            image_size=(
                final_image_size
            ),
            quality=(
                final_quality
            ),
            number=number,
        )

    # =====================================================
    # BEST
    #
    # Nano Banana 2 remains default.
    # =====================================================

    if effective_mode == (
        MODE_BEST
    ):

        if GEMINI_API_KEY:

            return run_google_direct(
                original_prompt,
                pro=BEST_USE_PRO,
                aspect_ratio=(
                    final_aspect_ratio
                ),
                image_size=(
                    final_image_size
                ),
                quality=(
                    final_quality
                ),
                number=number,
                allow_fallback=(
                    allow_fallback
                ),
            )

        if (
            OPENAI_API_KEY
            and
            allow_fallback
        ):

            return run_openai_best(
                original_prompt,
                aspect_ratio=(
                    final_aspect_ratio
                ),
                image_size=(
                    final_image_size
                ),
                quality=(
                    final_quality
                ),
                number=number,
            )

        raise XPANDImageConfigurationError(
            (
                "BEST mode يحتاج GEMINI_API_KEY "
                "أو OpenAI fallback متاح."
            )
        )

    # =====================================================
    # COMPARE
    # =====================================================

    if effective_mode == (
        MODE_COMPARE
    ):

        return run_compare(
            original_prompt,
            aspect_ratio=(
                final_aspect_ratio
            ),
            image_size=(
                final_image_size
            ),
            quality=(
                final_quality
            ),
            number=number,
        )

    # =====================================================
    # NANO BANANA 2
    # =====================================================

    if effective_mode in {
        MODE_GOOGLE_FAST,
        MODE_FAST,
    }:

        return run_google_direct(
            original_prompt,
            pro=False,
            aspect_ratio=(
                final_aspect_ratio
            ),
            image_size=(
                final_image_size
            ),
            quality=(
                final_quality
            ),
            number=number,
            allow_fallback=(
                allow_fallback
            ),
        )

    # =====================================================
    # NANO BANANA PRO EXPLICIT
    # =====================================================

    if effective_mode in {
        MODE_GOOGLE_PRO,
        MODE_PRO,
    }:

        return run_google_direct(
            original_prompt,
            pro=True,
            aspect_ratio=(
                final_aspect_ratio
            ),
            image_size=(
                final_image_size
            ),
            quality=(
                final_quality
            ),
            number=number,
            allow_fallback=(
                allow_fallback
            ),
        )

    # =====================================================
    # FINAL SAFE DEFAULT
    # =====================================================

    return run_google_direct(
        original_prompt,
        pro=False,
        aspect_ratio=(
            final_aspect_ratio
        ),
        image_size=(
            final_image_size
        ),
        quality=(
            final_quality
        ),
        number=number,
        allow_fallback=(
            allow_fallback
        ),
    )


# =========================================================
# ENGINE STATUS
# =========================================================

def get_image_engine_status() -> Dict[
    str,
    Any,
]:

    return {
        "ok":
            bool(
                OPENAI_API_KEY
                or
                GEMINI_API_KEY
            ),

        "engine":
            ENGINE_NAME,

        "version":
            ENGINE_VERSION,

        "providers": {
            "openai": {
                "configured":
                    bool(
                        OPENAI_API_KEY
                    ),

                "image_model":
                    OPENAI_IMAGE_MODEL,

                "director_model":
                    OPENAI_DIRECTOR_MODEL,

                "structured_json":
                    True,

                "vision":
                    bool(
                        OPENAI_API_KEY
                    ),
            },

            "google_fast": {
                "configured":
                    bool(
                        GEMINI_API_KEY
                    ),

                "label":
                    "Nano Banana 2",

                "model":
                    GOOGLE_IMAGE_FAST_MODEL,

                "primary":
                    True,
            },

            "google_pro": {
                "configured":
                    bool(
                        GEMINI_API_KEY
                    ),

                "label":
                    "Nano Banana Pro",

                "model":
                    GOOGLE_IMAGE_PRO_MODEL,

                "automatic":
                    False,
            },

            "gemini_director": {
                "configured":
                    bool(
                        GEMINI_API_KEY
                    ),

                "model":
                    GEMINI_DIRECTOR_RUNTIME_MODEL,

                "role":
                    (
                        "free_text_first"
                    ),
            },
        },

        "default_mode":
            DEFAULT_MODE,

        "default_effective_provider":
            "google_fast",

        "default_quality":
            DEFAULT_QUALITY,

        "best_use_pro":
            BEST_USE_PRO,

        "director_routing": {
            "structured":
                (
                    "openai_first"
                    if
                    STRUCTURED_DIRECTOR_PREFER_OPENAI
                    else
                    "gemini_first"
                ),

            "free_text":
                (
                    "gemini_first"
                    if
                    FREE_TEXT_DIRECTOR_PREFER_GEMINI
                    else
                    "openai_first"
                ),
        },

        "director_reasoning":
            OPENAI_DIRECTOR_REASONING,

        "director_max_output_tokens":
            OPENAI_DIRECTOR_MAX_OUTPUT_TOKENS,

        "structured_reasoning":
            OPENAI_STRUCTURED_REASONING,

        "structured_max_output_tokens":
            OPENAI_STRUCTURED_MAX_OUTPUT_TOKENS,

        "structured_retry_max_output_tokens":
            OPENAI_STRUCTURED_RETRY_MAX_OUTPUT_TOKENS,

        "prompt_cache_mode":
            OPENAI_PROMPT_CACHE_MODE,

        "prompt_cache_key":
            bool(
                OPENAI_PROMPT_CACHE_KEY
            ),

        "usage_logging":
            OPENAI_USAGE_LOGGING,

        "vision_detail":
            OPENAI_VISION_DETAIL,

        "structured_retry":
            True,

        "supports_openai_fusion":
            bool(
                OPENAI_API_KEY
            ),

        "supports_best_mode":
            bool(
                GEMINI_API_KEY
                or
                OPENAI_API_KEY
            ),

        "supports_google_openai_fusion":
            bool(
                GEMINI_API_KEY
                and
                OPENAI_API_KEY
            ),

        "google_optional":
            True,

        "google_failure_fallback":
            (
                "openai"
                if
                OPENAI_IMAGE_FALLBACK_ENABLED
                else
                "disabled"
            ),

        "supports_image_edit":
            bool(
                GEMINI_API_KEY
                or
                OPENAI_API_KEY
            ),

        "supported_google_sizes":
            sorted(
                SUPPORTED_GOOGLE_IMAGE_SIZES
            ),

        "telegram_ready":
            True,
    }


# =========================================================
# FRIENDLY ROUTE
# =========================================================

def describe_route(
    route: ImageRoute,
) -> str:

    labels = {
        PROVIDER_OPENAI:
            "GPT-Image-2",

        PROVIDER_GOOGLE_FAST:
            "Nano Banana 2",

        PROVIDER_GOOGLE_PRO:
            "Nano Banana Pro",

        PROVIDER_FUSION_PRO:
            "PRO Fusion",

        PROVIDER_FUSION_BEST:
            "BEST Fusion",

        PROVIDER_OPENAI_FUSION:
            "OpenAI Fusion",
    }

    label = labels.get(
        route.provider,
        route.model,
    )

    return (
        f"{label} | "
        f"{route.aspect_ratio} | "
        f"{route.image_size} | "
        f"{route.quality}"
    )


# =========================================================
# SELF TEST
#
# ZERO API CALLS
# ZERO IMAGE GENERATION
# =========================================================

if __name__ == "__main__":

    tests: Dict[
        str,
        bool
    ] = {}

    tests[
        "nano_banana_alias"
    ] = (
        normalize_mode(
            "Nano Banana 2"
        )
        ==
        MODE_GOOGLE_FAST
    )

    tests[
        "explicit_pro"
    ] = (
        normalize_mode(
            "Nano Banana Pro"
        )
        ==
        MODE_GOOGLE_PRO
    )

    tests[
        "auto_default_fast"
    ] = (
        resolve_effective_mode(
            "premium commercial STC Bank campaign",
            mode="auto",
            reference_count=3,
        )
        ==
        MODE_GOOGLE_FAST
    )

    tests[
        "references_do_not_force_pro"
    ] = (
        resolve_effective_mode(
            "professional campaign image",
            mode="auto",
            reference_count=5,
        )
        ==
        MODE_GOOGLE_FAST
    )

    tests[
        "explicit_pro_prompt"
    ] = (
        resolve_effective_mode(
            "استخدم Nano Banana Pro لهذا التصميم",
            mode="auto",
            reference_count=0,
        )
        ==
        MODE_GOOGLE_PRO
    )

    tests[
        "ratio_4_5"
    ] = (
        detect_aspect_ratio(
            "اعمل بوست بنسبة 4:5"
        )
        ==
        "4:5"
    )

    tests[
        "arabic_ratio_4_5"
    ] = (
        detect_aspect_ratio(
            "اعمل التصميم ٤ : ٥"
        )
        ==
        "4:5"
    )

    tests[
        "size_2k"
    ] = (
        detect_image_size(
            "أعطيني الصورة 2K"
        )
        ==
        "2K"
    )

    tests[
        "fhd_maps_2k"
    ] = (
        detect_image_size(
            "بدي FHD"
        )
        ==
        "2K"
    )

    stc_direction_test = (
        build_stc_production_direction(
            (
                "STC Bank merchant payments "
                "premium Saudi cafe advertisement"
            )
        )
    )

    tests[
        "merchant_priority"
    ] = (
        "Benefit family: merchant_payments"
        in
        stc_direction_test
    )

    tests[
        "stc_no_text_rule"
    ] = (
        "Generate NO visible advertising copy"
        in
        stc_direction_test
    )

    tests[
        "stc_no_logo_rule"
    ] = (
        "Generate NO STC wordmark or STC Bank logo"
        in
        stc_direction_test
    )

    tests[
        "stc_no_network_lines"
    ] = (
        "No connection/network lines"
        in
        stc_direction_test
    )

    tests[
        "structured_detection"
    ] = looks_like_json_request(
        "Return JSON only."
    )

    all_ok = all(
        tests.values()
    )

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND SMART IMAGE ENGINE V2.1"
    )
    print(
        " ZERO-COST SELF TEST"
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
    print(
        "OpenAI configured:",
        bool(
            OPENAI_API_KEY
        ),
    )
    print(
        "Gemini configured:",
        bool(
            GEMINI_API_KEY
        ),
    )
    print(
        "OpenAI image:",
        OPENAI_IMAGE_MODEL,
    )
    print(
        "Structured Director:",
        OPENAI_DIRECTOR_MODEL,
    )
    print(
        "Cheap text Director:",
        GEMINI_DIRECTOR_MODEL,
    )
    print(
        "Nano Banana 2:",
        GOOGLE_IMAGE_FAST_MODEL,
    )
    print(
        "Nano Banana Pro:",
        GOOGLE_IMAGE_PRO_MODEL,
    )
    print(
        "BEST uses Pro:",
        BEST_USE_PRO,
    )
    print("")

    print(
        "Structured routing:",
        (
            "OpenAI first"
            if
            STRUCTURED_DIRECTOR_PREFER_OPENAI
            else
            "Gemini first"
        ),
    )

    print(
        "Free-text routing:",
        (
            "Gemini first"
            if
            FREE_TEXT_DIRECTOR_PREFER_GEMINI
            else
            "OpenAI first"
        ),
    )

    print("")

    if all_ok:

        print(
            "XPAND Image Engine V2.1 self-test: PASS ✅"
        )

    else:

        print(
            "XPAND Image Engine V2.1 self-test: FAIL ❌"
        )

    print("")
    print(
        "✅ Nano Banana 2 primary"
    )
    print(
        "✅ Pro no longer triggered by references"
    )
    print(
        "✅ Structured JSON -> Sol first"
    )
    print(
        "✅ Gemini free-text cost route"
    )
    print(
        "✅ Real OpenAI image fallback"
    )
    print(
        "✅ STC merchant-payment priority"
    )
    print(
        "✅ STC no generated copy/logo"
    )
    print(
        "✅ STC anti-fintech-clutter rules"
    )
    print(
        "✅ Production Engine imports preserved"
    )
    print(
        "🚫 No API calls were made"
    )
    print(
        "🚫 No Vision calls were made"
    )
    print(
        "🚫 No images were generated"
    )
    print("")
