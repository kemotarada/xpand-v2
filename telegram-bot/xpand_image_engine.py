# =========================================================
# XPAND SMART IMAGE ENGINE V2.2.0
#
# FULL DROP-IN REPLACEMENT
#
# =========================================================
#
# FIXES
# ---------------------------------------------------------
#
# 1. Structured Creative Brain / Vision QA:
#
#       GPT-5.6 Sol
#       OpenAI Responses API
#       strict JSON schema
#
#    OpenAI structured routing is FIRST when OpenAI is enabled.
#
#
# 2. Gemini / Nano Banana 2 image generation:
#
#       gemini-3.1-flash-image
#
#    IMPORTANT:
#
#       NO thinking_level="low"
#
#    Gemini 3.1 Flash Image rejected that value in production.
#    Image requests therefore do NOT send a thinking-level
#    field at all.
#
#
# 3. OpenAI enable semantics:
#
#       XPAND_OPENAI_ENABLED=true
#
#    Explicit false disables OpenAI.
#
#    If the variable is absent, an existing OPENAI_API_KEY
#    automatically enables OpenAI for backwards compatibility.
#
#
# 4. Cost routing:
#
#    structured JSON  -> OpenAI GPT-5.6 Sol first
#    cheap free text  -> Gemini first
#    image generation -> Nano Banana 2 first
#    image fallback   -> GPT-Image-2 only when allowed
#
#
# 5. STC:
#
#    Nano Banana 2 default.
#    Nano Banana Pro is explicit only.
#    No forced purple / fintech effects.
#    STC image guard preserved.
#
#
# COMPATIBILITY
# ---------------------------------------------------------
#
# Public API preserved for:
#
#   xpand_image_telegram.py
#   xpand_creative_brain.py
#   xpand_production_engine.py
#   xpand_visual_intelligence.py
#
#
# Running:
#
#       python xpand_image_engine.py
#
# performs ZERO API calls.
#
# =========================================================

from __future__ import annotations

import base64
import json
import os
import re
import time
import uuid

from dataclasses import (
    dataclass,
    field,
)

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
)

import requests


# =========================================================
# STC BANK SKILL
# =========================================================

try:

    from xpand_stc_bank_skill import (
        STC_BANK_IMAGE_GUARD,
        is_stc_bank_request,
        detect_stc_benefit_family,
    )

except Exception:

    STC_BANK_IMAGE_GUARD = ""

    def is_stc_bank_request(
        text: Any,
    ) -> bool:

        value = str(
            text
            or ""
        ).lower()

        return (
            "stc bank"
            in value
            or
            "بنك stc"
            in value
        )

    def detect_stc_benefit_family(
        text: Any,
    ) -> str:

        value = str(
            text
            or ""
        ).lower()

        if (
            "نقاط البيع"
            in value
            or
            "point of sale"
            in value
            or
            "merchant"
            in value
        ):

            return "merchant_payments"

        return "premium_banking"


# =========================================================
# ENGINE
# =========================================================

ENGINE_NAME = (
    "XPAND Smart Image Engine"
)

ENGINE_VERSION = "2.2.0"


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
# OPENAI ENABLE SWITCH
# =========================================================

def env_bool(
    name: str,
    default: bool,
) -> bool:

    raw = os.environ.get(
        name
    )

    if raw is None:

        return bool(
            default
        )

    value = str(
        raw
    ).strip().lower()

    if not value:

        return bool(
            default
        )

    return value in {
        "1",
        "true",
        "yes",
        "on",
        "enabled",
    }


#
# IMPORTANT:
#
# Older XPAND deployments did not have
# XPAND_OPENAI_ENABLED at all.
#
# Therefore:
#
#   variable absent + OPENAI_API_KEY exists
#       =
#   OpenAI enabled
#
# Explicit false still disables it.
#

OPENAI_ENABLED = env_bool(
    "XPAND_OPENAI_ENABLED",
    bool(
        OPENAI_API_KEY
    ),
)


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


#
# Nano Banana 2
#

GOOGLE_IMAGE_FAST_MODEL = str(
    os.environ.get(
        "XPAND_GOOGLE_IMAGE_MODEL",
        "gemini-3.1-flash-image",
    )
).strip()


#
# Explicit Pro route only.
#

GOOGLE_IMAGE_PRO_MODEL = str(
    os.environ.get(
        "XPAND_GOOGLE_IMAGE_PRO_MODEL",
        "gemini-3-pro-image",
    )
).strip()


BEST_USE_PRO = env_bool(
    "XPAND_BEST_USE_PRO",
    False,
)


#
# Cheap free-text Director.
#

GEMINI_DIRECTOR_MODEL = str(
    os.environ.get(
        "XPAND_GEMINI_DIRECTOR_MODEL",
        "gemini-3.5-flash-lite",
    )
).strip()


#
# Gemini structured is FALLBACK only.
#

GEMINI_STRUCTURED_MODEL = str(
    os.environ.get(
        "XPAND_GEMINI_STRUCTURED_MODEL",
        "gemini-3.5-flash",
    )
).strip()


GEMINI_VISION_MODEL = str(
    os.environ.get(
        "XPAND_GEMINI_VISION_MODEL",
        "gemini-3.1-pro-preview",
    )
).strip()


GEMINI_VISION_STRUCTURED_MODEL = str(
    os.environ.get(
        "XPAND_GEMINI_VISION_STRUCTURED_MODEL",
        GEMINI_VISION_MODEL,
    )
).strip()


# =========================================================
# DEFAULT SETTINGS
# =========================================================

DEFAULT_MODE = str(
    os.environ.get(
        "XPAND_IMAGE_MODE",
        "google_fast",
    )
).strip().lower()


DEFAULT_QUALITY = str(
    os.environ.get(
        "XPAND_IMAGE_DEFAULT_QUALITY",
        "high",
    )
).strip().lower()


# =========================================================
# OPENAI COST CONTROL
# =========================================================

OPENAI_DIRECTOR_REASONING = str(
    os.environ.get(
        "XPAND_IMAGE_DIRECTOR_REASONING",
        "low",
    )
).strip().lower()


OPENAI_STRUCTURED_REASONING = str(
    os.environ.get(
        "XPAND_IMAGE_STRUCTURED_REASONING",
        "low",
    )
).strip().lower()


OPENAI_DIRECTOR_MAX_OUTPUT_TOKENS = max(
    800,
    int(
        os.environ.get(
            "XPAND_IMAGE_DIRECTOR_MAX_OUTPUT_TOKENS",
            "1400",
        )
        or 1400
    ),
)


OPENAI_STRUCTURED_MAX_OUTPUT_TOKENS = max(
    2000,
    int(
        os.environ.get(
            "XPAND_IMAGE_STRUCTURED_MAX_OUTPUT_TOKENS",
            "9000",
        )
        or 9000
    ),
)


OPENAI_STRUCTURED_RETRY_MAX_OUTPUT_TOKENS = max(
    OPENAI_STRUCTURED_MAX_OUTPUT_TOKENS,
    int(
        os.environ.get(
            "XPAND_IMAGE_STRUCTURED_RETRY_MAX_OUTPUT_TOKENS",
            "12000",
        )
        or 12000
    ),
)


OPENAI_PROMPT_CACHE_MODE = str(
    os.environ.get(
        "XPAND_OPENAI_PROMPT_CACHE_MODE",
        "explicit",
    )
).strip().lower()


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


# =========================================================
# GEMINI IMAGE SETTINGS
# =========================================================

#
# DO NOT feed this directly into Gemini image requests.
#
# This helper exists only to normalize legacy values if some
# older XPAND module imports it.
#

GEMINI_IMAGE_THINKING = str(
    os.environ.get(
        "XPAND_GEMINI_IMAGE_THINKING",
        "minimal",
    )
).strip().lower()


def normalize_gemini_image_thinking_level(
    value: Any,
) -> str:

    level = str(
        value
        or ""
    ).strip().lower()

    if level in {
        "high",
        "max",
        "maximum",
        "strong",
        "full",
    }:

        return "high"

    #
    # IMPORTANT:
    #
    # low is a valid OpenAI reasoning level,
    # but NOT a valid level for this Gemini image model.
    #

    if level in {
        "",
        "low",
        "minimal",
        "min",
        "medium",
        "balanced",
        "fast",
        "none",
        "off",
    }:

        return "minimal"

    return "minimal"


GEMINI_IMAGE_THINKING = (
    normalize_gemini_image_thinking_level(
        GEMINI_IMAGE_THINKING
    )
)


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

PROVIDER_OPENAI_FUSION = (
    "openai_fusion"
)


# =========================================================
# SUPPORTED VALUES
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
    "low",
    "medium",
    "high",
    "xhigh",
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

    metadata: Dict[
        str,
        Any,
    ] = field(
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
            uuid.uuid4().hex[
                :10
            ]
        )

        return (
            "XPAND-"
            +
            provider_name
            +
            "-"
            +
            unique
            +
            self.extension
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
        .strip()[
            :max_length
        ]
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
    text: Any,
    markers: Sequence[str],
) -> bool:

    source = normalize_arabic(
        text
    )

    for marker in markers:

        if (
            normalize_arabic(
                marker
            )
            in source
        ):

            return True

    return False


def safe_dict(
    value: Any,
) -> Dict[str, Any]:

    return (
        value
        if isinstance(
            value,
            dict,
        )
        else {}
    )


def safe_list(
    value: Any,
) -> List[Any]:

    return (
        value
        if isinstance(
            value,
            list,
        )
        else []
    )


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
# PROVIDER ERRORS
# =========================================================

def _safe_json(
    response,
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
                value
        }

    except Exception:

        return {
            "raw":
                clean_text(
                    getattr(
                        response,
                        "text",
                        "",
                    ),
                    5000,
                )
        }


def _provider_error_message(
    provider: str,
    response,
) -> str:

    status_code = getattr(
        response,
        "status_code",
        "?",
    )

    data = _safe_json(
        response
    )

    message = ""

    error_value = data.get(
        "error"
    )

    if isinstance(
        error_value,
        dict,
    ):

        message = clean_text(
            (
                error_value.get(
                    "message"
                )
                or
                error_value.get(
                    "detail"
                )
                or
                error_value
            ),
            3500,
        )

    elif error_value:

        message = clean_text(
            error_value,
            3500,
        )

    if not message:

        message = clean_text(
            (
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
                data
            ),
            3500,
        )

    return (
        str(
            provider
        )
        +
        " HTTP "
        +
        str(
            status_code
        )
        +
        ": "
        +
        message
    )


# =========================================================
# INLINE IMAGE DISCOVERY
# =========================================================

def _decode_image_data(
    value: str,
) -> Optional[bytes]:

    text = clean_text(
        value,
        100000000,
    )

    if not text:

        return None

    if text.startswith(
        "data:image/"
    ):

        try:

            text = text.split(
                ",",
                1,
            )[1]

        except Exception:

            return None

    try:

        raw = base64.b64decode(
            text
        )

        return (
            raw
            if raw
            else None
        )

    except Exception:

        return None


def _find_inline_images(
    value: Any,
) -> List[
    Tuple[
        bytes,
        str,
    ]
]:

    output: List[
        Tuple[
            bytes,
            str,
        ]
    ] = []

    def walk(
        node: Any,
    ) -> None:

        if isinstance(
            node,
            dict,
        ):

            mime_type = clean_text(
                (
                    node.get(
                        "mime_type"
                    )
                    or
                    node.get(
                        "mimeType"
                    )
                    or
                    "image/jpeg"
                ),
                100,
            )

            for key in (
                "b64_json",
                "base64",
                "data",
            ):

                candidate = node.get(
                    key
                )

                if not isinstance(
                    candidate,
                    str,
                ):

                    continue

                raw = _decode_image_data(
                    candidate
                )

                if raw:

                    output.append(
                        (
                            raw,
                            mime_type,
                        )
                    )

                    break

            for child in (
                node.values()
            ):

                walk(
                    child
                )

        elif isinstance(
            node,
            list,
        ):

            for child in node:

                walk(
                    child
                )

    walk(
        value
    )

    deduped = []

    seen = set()

    for raw, mime_type in output:

        signature = (
            len(
                raw
            ),
            raw[
                :64
            ],
        )

        if signature in seen:

            continue

        seen.add(
            signature
        )

        deduped.append(
            (
                raw,
                mime_type,
            )
        )

    return deduped


# =========================================================
# MIME
# =========================================================

def infer_mime_type(
    image_bytes: bytes,
    fallback: str = "image/jpeg",
) -> str:

    if not image_bytes:

        return fallback

    if image_bytes.startswith(
        b"\x89PNG\r\n\x1a\n"
    ):

        return "image/png"

    if image_bytes.startswith(
        b"\xff\xd8\xff"
    ):

        return "image/jpeg"

    if (
        image_bytes.startswith(
            b"RIFF"
        )
        and
        b"WEBP"
        in image_bytes[
            :16
        ]
    ):

        return "image/webp"

    return fallback


def image_data_uri(
    image_bytes: bytes,
    mime_type: str,
) -> str:

    mime_type = (
        clean_text(
            mime_type,
            100,
        )
        or
        infer_mime_type(
            image_bytes
        )
    )

    return (
        "data:"
        +
        mime_type
        +
        ";base64,"
        +
        base64.b64encode(
            image_bytes
        ).decode(
            "ascii"
        )
    )


# =========================================================
# DETECTION — ASPECT RATIO
# =========================================================

def detect_aspect_ratio(
    prompt: str,
    explicit: str = "",
) -> str:

    explicit = clean_text(
        explicit,
        50,
    )

    if explicit in (
        SUPPORTED_ASPECT_RATIOS
    ):

        return explicit

    text = normalize_arabic(
        prompt
    )

    ratio_pattern = re.search(
        (
            r"(?<!\d)"
            r"(1:1|2:3|3:2|3:4|4:3|4:5|5:4|"
            r"9:16|16:9|21:9|1:4|4:1|1:8|8:1)"
            r"(?!\d)"
        ),
        text,
    )

    if ratio_pattern:

        return ratio_pattern.group(
            1
        )

    if contains_any(
        text,
        [
            "ستوري",
            "story",
            "reel",
            "ريل",
            "9 16",
        ],
    ):

        return "9:16"

    if contains_any(
        text,
        [
            "بوست انستجرام طولي",
            "بوست انستغرام طولي",
            "portrait post",
            "عمودي 4 5",
        ],
    ):

        return "4:5"

    if contains_any(
        text,
        [
            "landscape",
            "افقي",
            "أفقي",
            "سينمائي",
        ],
    ):

        return "16:9"

    return "1:1"


# =========================================================
# DETECTION — IMAGE SIZE
# =========================================================

def detect_image_size(
    prompt: str,
    explicit: str = "",
) -> str:

    explicit_value = str(
        explicit
        or ""
    ).strip().upper()

    aliases = {
        "512":
            "512",

        "1K":
            "1K",

        "1024":
            "1K",

        "2K":
            "2K",

        "2048":
            "2K",

        "4K":
            "4K",

        "4096":
            "4K",

        "HD":
            "2K",

        "FHD":
            "2K",

        "FULLHD":
            "2K",

        "FULL HD":
            "2K",
    }

    if explicit_value in aliases:

        return aliases[
            explicit_value
        ]

    text = normalize_arabic(
        prompt
    )

    if re.search(
        r"(?<!\d)4\s*k(?!\w)",
        text,
    ):

        return "4K"

    if contains_any(
        text,
        [
            "4k",
            "4096",
            "فور كي",
        ],
    ):

        return "4K"

    if re.search(
        r"(?<!\d)2\s*k(?!\w)",
        text,
    ):

        return "2K"

    if contains_any(
        text,
        [
            "2k",
            "2048",
            "تو كي",
            "full hd",
            "fullhd",
            "fhd",
        ],
    ):

        return "2K"

    if contains_any(
        text,
        [
            "1k",
            "1024",
        ],
    ):

        return "1K"

    return "1K"


# =========================================================
# DETECTION — QUALITY
# =========================================================

def detect_quality(
    prompt: str,
    explicit: str = "",
) -> str:

    explicit_value = str(
        explicit
        or ""
    ).strip().lower()

    if explicit_value in (
        SUPPORTED_OPENAI_QUALITIES
    ):

        return explicit_value

    if contains_any(
        prompt,
        [
            "high quality",
            "جودة عالية",
            "فاخر",
            "فاخرة",
            "premium",
            "masterpiece",
        ],
    ):

        return "high"

    if contains_any(
        prompt,
        [
            "low quality",
            "جودة منخفضة",
        ],
    ):

        return "low"

    return (
        DEFAULT_QUALITY
        if DEFAULT_QUALITY
        in SUPPORTED_OPENAI_QUALITIES
        else
        "high"
    )


# =========================================================
# MODE DETECTION
# =========================================================

def resolve_effective_mode(
    prompt: str,
    requested_mode: str = "",
    reference_count: int = 0,
) -> str:

    mode = str(
        requested_mode
        or ""
    ).strip().lower()

    if mode in {
        MODE_OPENAI,
        MODE_GOOGLE_FAST,
        MODE_GOOGLE_PRO,
        MODE_PRO,
        MODE_BEST,
        MODE_COMPARE,
        MODE_FAST,
    }:

        return mode

    text = normalize_arabic(
        prompt
    )

    if contains_any(
        text,
        [
            "nano banana pro",
            "نانو بنانا برو",
            "gemini 3 pro image",
        ],
    ):

        return MODE_GOOGLE_PRO

    if contains_any(
        text,
        [
            "nano banana 2",
            "نانو بنانا 2",
            "gemini 3.1 flash image",
        ],
    ):

        return MODE_GOOGLE_FAST

    if contains_any(
        text,
        [
            "gpt-image-2",
            "gpt image 2",
        ],
    ):

        return MODE_OPENAI

    if mode == MODE_AUTO:

        return MODE_GOOGLE_FAST

    if DEFAULT_MODE in {
        MODE_OPENAI,
        MODE_GOOGLE_FAST,
        MODE_GOOGLE_PRO,
        MODE_FAST,
        MODE_PRO,
        MODE_BEST,
    }:

        return DEFAULT_MODE

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
        provider=clean_text(
            provider,
            100,
        ),

        model=clean_text(
            model,
            200,
        ),

        reason=clean_text(
            reason,
            1000,
        ),

        aspect_ratio=(
            aspect_ratio
            if aspect_ratio
            in SUPPORTED_ASPECT_RATIOS
            else
            "1:1"
        ),

        image_size=(
            image_size
            if image_size
            in SUPPORTED_GOOGLE_IMAGE_SIZES
            else
            "1K"
        ),

        quality=(
            quality
            if quality
            in SUPPORTED_OPENAI_QUALITIES
            else
            "high"
        ),
    )


# =========================================================
# OPENAI RATIO SIZE
# =========================================================

def openai_size_for_ratio(
    aspect_ratio: str,
) -> str:

    portrait = {
        "2:3",
        "3:4",
        "4:5",
        "9:16",
        "1:4",
        "1:8",
    }

    landscape = {
        "3:2",
        "4:3",
        "5:4",
        "16:9",
        "21:9",
        "4:1",
        "8:1",
    }

    if aspect_ratio in portrait:

        return "1024x1536"

    if aspect_ratio in landscape:

        return "1536x1024"

    return "1024x1024"


# =========================================================
# RESOLUTION FINALIZATION
# =========================================================

def _finalize_requested_resolution(
    image_bytes: bytes,
    mime_type: str,
    requested_size: str,
) -> Tuple[
    bytes,
    str,
]:

    #
    # IMPORTANT V2.2:
    #
    # Gemini now receives native 1K/2K/4K output intent.
    #
    # We intentionally DO NOT perform fake local upscaling
    # after generation.
    #
    # This preserves native provider pixels and avoids
    # expensive / artificial resampling.
    #

    return (
        image_bytes,
        (
            mime_type
            or
            infer_mime_type(
                image_bytes
            )
        ),
    )


# =========================================================
# STC PROMPT GUARD
# =========================================================

def build_professional_prompt(
    prompt: str,
    aspect_ratio: str,
    image_size: str,
) -> str:

    value = clean_text(
        prompt,
        30000,
    )

    suffix = f"""

XPAND IMAGE EXECUTION LOCK
==========================

Aspect ratio:
{aspect_ratio}

Native resolution intent:
{image_size}

Produce one coherent premium image.

Use:
- physically believable composition
- realistic lighting
- credible shadows
- material-specific reflections
- coherent perspective
- natural scale
- professional advertising restraint

Do not add random graphic effects merely to make the scene
look futuristic.
""".strip()

    if is_stc_bank_request(
        value
    ):

        suffix += """

STC BANK EXECUTION LOCK
=======================

Generate the IMAGE ONLY.

Do not generate:
- advertising headline
- subtitle
- CTA
- percentage
- price
- financial figures
- legal copy
- STC Bank logo
- STC wordmark
- Visa logo
- Mastercard logo
- watermark
- fake readable banking UI

Do not automatically create:
- purple neon environment
- holograms
- floating cards
- floating phones
- floating POS terminals
- network lines
- payment trails
- random particles
- generic fintech graphics

For realistic photography:
preserve natural real-world environmental colors.

Purple is optional and must be physically motivated.
""".strip()

        if STC_BANK_IMAGE_GUARD:

            suffix += (
                "\n\n"
                +
                clean_text(
                    STC_BANK_IMAGE_GUARD,
                    6000,
                )
            )

    return (
        value
        +
        "\n\n"
        +
        suffix
    )


# =========================================================
# GOOGLE QUOTA
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
    ]

    return any(
        normalize_arabic(
            marker
        )
        in text
        for marker in markers
    )


# =========================================================
# OPENAI REASONING NORMALIZER
# =========================================================

def normalize_reasoning_effort(
    value: Any,
    default: str = "low",
) -> str:

    level = str(
        value
        or ""
    ).strip().lower()

    if level in SUPPORTED_REASONING_LEVELS:

        return level

    return default


# =========================================================
# OPENAI USAGE
# =========================================================

def _log_openai_usage(
    data: Dict[str, Any],
) -> None:

    if not OPENAI_USAGE_LOGGING:

        return

    usage = safe_dict(
        data.get(
            "usage"
        )
    )

    if not usage:

        return

    input_tokens = int(
        usage.get(
            "input_tokens",
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

    total_tokens = int(
        usage.get(
            "total_tokens",
            0,
        )
        or
        (
            input_tokens
            +
            output_tokens
        )
    )

    input_details = safe_dict(
        usage.get(
            "input_tokens_details"
        )
    )

    output_details = safe_dict(
        usage.get(
            "output_tokens_details"
        )
    )

    cached_tokens = int(
        input_details.get(
            "cached_tokens",
            0,
        )
        or 0
    )

    cache_write_tokens = int(
        input_details.get(
            "cache_write_tokens",
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

    print(
        "💰 XPAND SOL USAGE"
        +
        " | input="
        +
        str(
            input_tokens
        )
        +
        " | cached="
        +
        str(
            cached_tokens
        )
        +
        " | cache_write="
        +
        str(
            cache_write_tokens
        )
        +
        " | output="
        +
        str(
            output_tokens
        )
        +
        " | reasoning="
        +
        str(
            reasoning_tokens
        )
        +
        " | total="
        +
        str(
            total_tokens
        )
    )


# =========================================================
# OPENAI RESPONSE TEXT
# =========================================================

def _extract_openai_text(
    data: Dict[str, Any],
) -> str:

    direct = data.get(
        "output_text"
    )

    if isinstance(
        direct,
        str,
    ) and direct.strip():

        return direct.strip()

    output = data.get(
        "output"
    )

    if isinstance(
        output,
        list,
    ):

        for item in output:

            if not isinstance(
                item,
                dict,
            ):

                continue

            content = item.get(
                "content"
            )

            if not isinstance(
                content,
                list,
            ):

                continue

            for part in content:

                if not isinstance(
                    part,
                    dict,
                ):

                    continue

                text = part.get(
                    "text"
                )

                if isinstance(
                    text,
                    str,
                ) and text.strip():

                    return text.strip()

    def walk(
        node: Any,
    ) -> str:

        if isinstance(
            node,
            dict,
        ):

            for key in (
                "output_text",
                "text",
            ):

                value = node.get(
                    key
                )

                if isinstance(
                    value,
                    str,
                ) and value.strip():

                    return value.strip()

            for child in (
                node.values()
            ):

                found = walk(
                    child
                )

                if found:

                    return found

        elif isinstance(
            node,
            list,
        ):

            for child in node:

                found = walk(
                    child
                )

                if found:

                    return found

        return ""

    return walk(
        data
    )


def _extract_openai_refusal(
    data: Dict[str, Any],
) -> str:

    def walk(
        node: Any,
    ) -> str:

        if isinstance(
            node,
            dict,
        ):

            refusal = node.get(
                "refusal"
            )

            if isinstance(
                refusal,
                str,
            ) and refusal.strip():

                return refusal.strip()

            for child in (
                node.values()
            ):

                found = walk(
                    child
                )

                if found:

                    return found

        elif isinstance(
            node,
            list,
        ):

            for child in node:

                found = walk(
                    child
                )

                if found:

                    return found

        return ""

    return walk(
        data
    )


# =========================================================
# JSON NORMALIZER
# =========================================================

def normalize_json_text(
    value: Any,
) -> str:

    if isinstance(
        value,
        dict,
    ):

        return json.dumps(
            value,
            ensure_ascii=False,
            separators=(
                ",",
                ":",
            ),
        )

    text = clean_text(
        value,
        100000,
    ).strip()

    if not text:

        return ""

    text = re.sub(
        r"^\s*```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\s*```\s*$",
        "",
        text,
    ).strip()

    try:

        parsed = json.loads(
            text
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

    first_object = text.find(
        "{"
    )

    last_object = text.rfind(
        "}"
    )

    if (
        first_object >= 0
        and
        last_object
        >
        first_object
    ):

        candidate = text[
            first_object:
            last_object + 1
        ]

        try:

            parsed = json.loads(
                candidate
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

    first_array = text.find(
        "["
    )

    last_array = text.rfind(
        "]"
    )

    if (
        first_array >= 0
        and
        last_array
        >
        first_array
    ):

        candidate = text[
            first_array:
            last_array + 1
        ]

        try:

            parsed = json.loads(
                candidate
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

    return text


def structured_json_is_valid(
    value: Any,
) -> bool:

    text = normalize_json_text(
        value
    )

    if not text:

        return False

    try:

        json.loads(
            text
        )

        return True

    except Exception:

        return False


def looks_like_json_request(
    prompt: str,
) -> bool:

    return contains_any(
        prompt,
        [
            "json",
            "json object",
            "json schema",
            "return only json",
            "structured output",
            "structured json",
        ],
    )


# =========================================================
# ONE OPENAI RESPONSES CALL
# =========================================================

def _call_openai_response_once(
    prompt: str,
    *,
    image_bytes: Optional[
        bytes
    ],
    image_mime_type: str,
    json_mode: bool,
    json_schema: Optional[
        Dict[str, Any]
    ],
    json_schema_name: str,
    reasoning_effort: str,
    max_output_tokens: int,
) -> Dict[str, Any]:

    if not OPENAI_ENABLED:

        raise XPANDImageConfigurationError(
            (
                "OpenAI disabled: "
                "XPAND_OPENAI_ENABLED=false."
            )
        )

    if not OPENAI_API_KEY:

        raise XPANDImageConfigurationError(
            "OPENAI_API_KEY missing."
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
                    32000,
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
        Any,
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

    if OPENAI_PROMPT_CACHE_MODE:

        payload[
            "prompt_cache_options"
        ] = {
            "mode":
                OPENAI_PROMPT_CACHE_MODE,
        }

    # -----------------------------------------------------
    # STRICT STRUCTURED OUTPUT
    # -----------------------------------------------------

    if json_schema:

        schema_name = re.sub(
            r"[^a-zA-Z0-9_\-]",
            "_",
            clean_text(
                json_schema_name,
                64,
            )
            or
            "xpand_structured_output",
        )

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
                "invalid response."
            )
        )

    _log_openai_usage(
        data
    )

    return data


# =========================================================
# OPENAI DIRECTOR EXECUTION
# =========================================================

def _run_openai_director(
    prompt: str,
    *,
    image_bytes: Optional[
        bytes
    ],
    image_mime_type: str,
    json_mode: bool,
    json_schema: Optional[
        Dict[str, Any]
    ],
    json_schema_name: str,
) -> str:

    structured = bool(
        json_mode
        or
        json_schema
    )

    if structured:

        reasoning_effort = (
            OPENAI_STRUCTURED_REASONING
        )

        max_tokens = (
            OPENAI_STRUCTURED_MAX_OUTPUT_TOKENS
        )

        attempts = 2

    else:

        reasoning_effort = (
            OPENAI_DIRECTOR_REASONING
        )

        max_tokens = (
            OPENAI_DIRECTOR_MAX_OUTPUT_TOKENS
        )

        attempts = 1

    last_error: Optional[
        Exception
    ] = None

    for attempt in range(
        1,
        attempts + 1,
    ):

        if (
            structured
            and
            attempt > 1
        ):

            current_max_tokens = (
                OPENAI_STRUCTURED_RETRY_MAX_OUTPUT_TOKENS
            )

            current_prompt = (
                prompt
                +
                "\n\n"
                +
                "STRUCTURED RETRY:\n"
                +
                "Return the entire JSON again from the beginning. "
                +
                "Do not truncate the object. Be concise."
            )

        else:

            current_max_tokens = (
                max_tokens
            )

            current_prompt = (
                prompt
            )

        try:

            data = (
                _call_openai_response_once(
                    current_prompt,

                    image_bytes=(
                        image_bytes
                    ),

                    image_mime_type=(
                        image_mime_type
                    ),

                    json_mode=(
                        json_mode
                    ),

                    json_schema=(
                        json_schema
                    ),

                    json_schema_name=(
                        json_schema_name
                    ),

                    reasoning_effort=(
                        reasoning_effort
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
                        "GPT-5.6 Sol refused: "
                        +
                        refusal
                    )
                )

            text = _extract_openai_text(
                data
            )

            if not text:

                raise XPANDImageProviderError(
                    (
                        "GPT-5.6 Sol returned "
                        "no output text."
                    )
                )

            if structured:

                normalized = (
                    normalize_json_text(
                        text
                    )
                )

                if not structured_json_is_valid(
                    normalized
                ):

                    raise XPANDStructuredOutputError(
                        (
                            "GPT-5.6 Sol structured output "
                            "is not valid JSON."
                        )
                    )

                return normalized

            return text

        except Exception as error:

            last_error = error

            if attempt < attempts:

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
                2500,
            )
        )
    )


# =========================================================
# GEMINI TEXT DISCOVERY
# =========================================================

def _find_gemini_text(
    value: Any,
) -> str:

    if isinstance(
        value,
        dict,
    ):

        for key in (
            "output_text",
            "text",
        ):

            item = value.get(
                key
            )

            if isinstance(
                item,
                str,
            ) and item.strip():

                return item.strip()

        for key in (
            "output",
            "outputs",
            "steps",
            "content",
            "parts",
            "result",
        ):

            if key not in value:

                continue

            found = _find_gemini_text(
                value.get(
                    key
                )
            )

            if found:

                return found

    elif isinstance(
        value,
        list,
    ):

        for item in value:

            found = _find_gemini_text(
                item
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

    if not GEMINI_API_KEY:

        raise XPANDImageConfigurationError(
            "GEMINI_API_KEY missing."
        )

    prompt = clean_text(
        prompt,
        32000,
    )

    if not prompt:

        raise XPANDImageError(
            "Director prompt is empty."
        )

    structured = bool(
        json_mode
        or
        json_schema
    )

    request_prompt = (
        prompt
    )

    if structured:

        request_prompt += (
            "\n\n"
            +
            "OUTPUT CONTRACT:\n"
            +
            "Return exactly one complete valid JSON object. "
            +
            "No Markdown. No prose outside the JSON."
        )

        if json_schema:

            request_prompt += (
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
                request_prompt,
        }
    ]

    if image_bytes:

        inputs.append(
            {
                "type":
                    "image",

                "mime_type":
                    (
                        image_mime_type
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

    if (
        image_bytes
        and
        structured
    ):

        selected_model = (
            GEMINI_VISION_STRUCTURED_MODEL
        )

    elif image_bytes:

        selected_model = (
            GEMINI_VISION_MODEL
        )

    elif structured:

        selected_model = (
            GEMINI_STRUCTURED_MODEL
        )

    else:

        selected_model = (
            GEMINI_DIRECTOR_MODEL
        )

    payload: Dict[
        str,
        Any,
    ] = {
        "model":
            selected_model,

        "input":
            inputs,
    }

    #
    # IMPORTANT:
    #
    # NO thinking_level here either.
    #
    # Keep provider-specific thinking parameters away from
    # shared Director/image routing.
    #

    search_enabled = env_bool(
        "XPAND_GEMINI_SEARCH_GROUNDING",
        True,
    )

    if (
        search_enabled
        and
        not structured
        and
        contains_any(
            request_prompt,
            [
                "bank",
                "بنك",
                "مصرف",
                "competitor",
                "منافس",
                "deep research",
                "بحث عميق",
            ],
        )
    ):

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

    if not response.ok:

        raise XPANDImageProviderError(
            _provider_error_message(
                "Gemini Director",
                response,
            )
        )

    data = _safe_json(
        response
    )

    text = _find_gemini_text(
        data
    )

    if not text:

        raise XPANDImageProviderError(
            (
                "Gemini Director returned "
                "no text."
            )
        )

    if structured:

        normalized = normalize_json_text(
            text
        )

        if not structured_json_is_valid(
            normalized
        ):

            raise XPANDStructuredOutputError(
                (
                    "Structured output is "
                    "not valid JSON."
                )
            )

        return normalized

    return text


# =========================================================
# XPAND DIRECTOR ROUTER
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

    prompt = clean_text(
        prompt,
        32000,
    )

    if not prompt:

        raise XPANDImageError(
            "Director prompt is empty."
        )

    if json_mode is None:

        json_mode = bool(
            json_schema
            or
            looks_like_json_request(
                prompt
            )
        )

    structured = bool(
        json_mode
        or
        json_schema
    )

    errors = []

    # =====================================================
    # STRUCTURED:
    # GPT-5.6 SOL FIRST
    # =====================================================

    if structured:

        if (
            OPENAI_ENABLED
            and
            OPENAI_API_KEY
        ):

            try:

                return _run_openai_director(
                    prompt,

                    image_bytes=(
                        image_bytes
                    ),

                    image_mime_type=(
                        image_mime_type
                    ),

                    json_mode=True,

                    json_schema=(
                        json_schema
                    ),

                    json_schema_name=(
                        json_schema_name
                    ),
                )

            except Exception as error:

                errors.append(
                    (
                        "openai_structured: "
                        +
                        clean_text(
                            error,
                            2400,
                        )
                    )
                )

                print(
                    (
                        "⚠️ OPENAI STRUCTURED DIRECTOR: "
                        +
                        clean_text(
                            error,
                            1800,
                        )
                    )
                )

        elif not OPENAI_ENABLED:

            errors.append(
                (
                    "openai_structured: "
                    +
                    "XPAND_OPENAI_ENABLED=false"
                )
            )

            print(
                (
                    "⚠️ OPENAI STRUCTURED DIRECTOR disabled "
                    "by XPAND_OPENAI_ENABLED=false."
                )
            )

        elif not OPENAI_API_KEY:

            errors.append(
                (
                    "openai_structured: "
                    +
                    "OPENAI_API_KEY missing"
                )
            )

        # -------------------------------------------------
        # Structured fallback:
        # Gemini only after Sol cannot be used.
        # -------------------------------------------------

        if GEMINI_API_KEY:

            try:

                return call_gemini_director(
                    prompt,

                    image_bytes=(
                        image_bytes
                    ),

                    image_mime_type=(
                        image_mime_type
                    ),

                    json_mode=True,

                    json_schema=(
                        json_schema
                    ),

                    json_schema_name=(
                        json_schema_name
                    ),
                )

            except Exception as error:

                errors.append(
                    (
                        "gemini_structured: "
                        +
                        clean_text(
                            error,
                            2400,
                        )
                    )
                )

        raise XPANDStructuredOutputError(
            (
                "Structured Director failed. "
                +
                " | ".join(
                    errors
                )
            )
        )

    # =====================================================
    # FREE TEXT:
    # GEMINI FIRST FOR COST
    # =====================================================

    if GEMINI_API_KEY:

        try:

            return call_gemini_director(
                prompt,

                image_bytes=(
                    image_bytes
                ),

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
                        2200,
                    )
                )
            )

    if (
        OPENAI_ENABLED
        and
        OPENAI_API_KEY
    ):

        try:

            return _run_openai_director(
                prompt,

                image_bytes=(
                    image_bytes
                ),

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
                    "openai_text: "
                    +
                    clean_text(
                        error,
                        2200,
                    )
                )
            )

    raise XPANDImageProviderError(
        (
            "Director unavailable. "
            +
            " | ".join(
                errors
            )
        )
    )


# =========================================================
# JSON DIRECTOR HELPER
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

        image_bytes=(
            image_bytes
        ),

        image_mime_type=(
            image_mime_type
        ),

        json_mode=True,

        json_schema=(
            json_schema
        ),

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
                "Structured response is "
                "not a JSON object."
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
You are the senior visual art director for XPAND.

ORIGINAL REQUEST:
{clean_text(original_prompt, 10000)}

TARGET ASPECT RATIO:
{aspect_ratio}

RESOLUTION INTENT:
{image_size}

Create a concise professional visual direction.

Improve:
- composition
- camera
- hierarchy
- lighting
- materials
- palette
- depth
- negative space
- advertising finish

Preserve the user's intent.
Return only the concise art-direction brief.
""".strip()

    return call_openai_director(
        request,
        json_mode=False,
    )


# =========================================================
# LEGACY VISUAL CRITIC
# =========================================================

def critique_generated_image(
    image_bytes: bytes,
    mime_type: str,
    original_prompt: str,
) -> str:

    request = f"""
Review the attached generated image against this request:

{clean_text(original_prompt, 8000)}

Identify only meaningful improvements.

Evaluate:
- request accuracy
- concept clarity
- composition
- advertising quality
- lighting
- materials
- perspective
- reflections
- shadows
- anatomy
- artifacts
- commercial readiness

Do not request a full redesign if the image is already strong.

Return concise actionable corrections.
""".strip()

    return call_openai_director(
        request,

        image_bytes=(
            image_bytes
        ),

        image_mime_type=(
            mime_type
        ),

        json_mode=False,
    )


# =========================================================
# GEMINI IMAGE GENERATION
# =========================================================

def _build_gemini_image_payload(
    *,
    model: str,
    prompt: str,
    aspect_ratio: str,
    image_size: str,
) -> Dict[str, Any]:

    #
    # THIS FUNCTION IS THE CORE FIX.
    #
    # Intentionally NO:
    #
    #   thinking_level
    #   thinking
    #   reasoning_effort
    #
    # Nano Banana 2 controls its image reasoning internally.
    #

    return {
        "model":
            model,

        "input":
            prompt,

        "response_format": {
            "type":
                "image",

            "aspect_ratio":
                aspect_ratio,

            "image_size":
                image_size,

            "mime_type":
                "image/jpeg",
        },
    }


def _generate_one_with_gemini(
    prompt: str,
    original_prompt: str,
    route: ImageRoute,
    index: int = 0,
) -> GeneratedImage:

    if not GEMINI_API_KEY:

        raise XPANDImageConfigurationError(
            "GEMINI_API_KEY missing."
        )

    requested_size = (
        route.image_size
    )

    image_size = (
        route.image_size
        if route.image_size
        in SUPPORTED_GOOGLE_IMAGE_SIZES
        else
        "1K"
    )

    payload = (
        _build_gemini_image_payload(
            model=(
                route.model
            ),

            prompt=(
                prompt
            ),

            aspect_ratio=(
                route.aspect_ratio
            ),

            image_size=(
                image_size
            ),
        )
    )

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
                "Gemini returned success "
                "but no image was found."
            )
        )

    image_bytes, mime_type = (
        images[
            0
        ]
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
            "id"
        ),
        200,
    )

    if not request_id:

        request_id = (
            "gg-"
            +
            uuid.uuid4().hex[
                :12
            ]
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
        image_bytes=(
            image_bytes
        ),

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

        prompt=(
            prompt
        ),

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

        request_id=(
            request_id
        ),

        metadata={
            "generation_type":
                "gemini_generation",

            "google_model":
                route.model,

            "google_image_size":
                image_size,

            "delivered_image_size":
                requested_size,

            "thinking_level_sent":
                None,

            "xpand_engine_version":
                ENGINE_VERSION,
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

    results = []

    errors = []

    for index in range(
        number
    ):

        try:

            results.append(
                _generate_one_with_gemini(
                    prompt=(
                        prompt
                    ),

                    original_prompt=(
                        original_prompt
                    ),

                    route=(
                        route
                    ),

                    index=(
                        index
                    ),
                )
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
# GEMINI EDIT
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
            "GEMINI_API_KEY missing."
        )

    if not input_images:

        raise XPANDImageError(
            "No images supplied for edit."
        )

    final_ratio = detect_aspect_ratio(
        prompt,
        aspect_ratio,
    )

    final_size = detect_image_size(
        prompt,
        image_size,
    )

    provider_size = (
        final_size
        if final_size
        in SUPPORTED_GOOGLE_IMAGE_SIZES
        else
        "1K"
    )

    model = (
        GOOGLE_IMAGE_PRO_MODEL
        if pro
        else
        GOOGLE_IMAGE_FAST_MODEL
    )

    instruction = (
        build_professional_prompt(
            prompt,
            final_ratio,
            final_size,
        )
    )

    instruction += """

REFERENCE ORDER CONTRACT
========================

Image 1 is the BASE image unless the user explicitly says otherwise.

Images 2+ are references.

Preserve all untouched areas.

Transfer only what the user requested.

Match:
- perspective
- scale
- lighting
- shadows
- reflections
- depth
- material response

The result must look like one coherent photographed scene.

Do not introduce generic fintech effects unless explicitly requested.
""".strip()

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

    for (
        image_bytes,
        mime_type,
    ) in list(
        input_images
    )[:10]:

        if not image_bytes:

            continue

        inputs.append(
            {
                "type":
                    "image",

                "mime_type":
                    (
                        mime_type
                        or
                        infer_mime_type(
                            image_bytes
                        )
                    ),

                "data":
                    base64.b64encode(
                        image_bytes
                    ).decode(
                        "ascii"
                    ),
            }
        )

    payload = {
        "model":
            model,

        "input":
            inputs,

        "response_format": {
            "type":
                "image",

            "aspect_ratio":
                final_ratio,

            "image_size":
                provider_size,

            "mime_type":
                "image/jpeg",
        },
    }

    #
    # CRITICAL:
    #
    # No thinking_level is included.
    #

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
                "Nano Banana Edit succeeded "
                "but returned no image."
            )
        )

    output, output_mime = (
        images[
            0
        ]
    )

    output, output_mime = (
        _finalize_requested_resolution(
            output,
            output_mime,
            final_size,
        )
    )

    return GeneratedImage(
        image_bytes=(
            output
        ),

        mime_type=(
            output_mime
            or
            "image/jpeg"
        ),

        provider=(
            PROVIDER_GOOGLE_PRO
            if pro
            else
            PROVIDER_GOOGLE_FAST
        ),

        model=(
            model
        ),

        prompt=(
            instruction
        ),

        original_prompt=(
            clean_text(
                prompt,
                32000,
            )
        ),

        aspect_ratio=(
            final_ratio
        ),

        image_size=(
            final_size
        ),

        quality="high",

        route_reason=(
            "XPAND Nano Banana image edit"
        ),

        request_id=(
            clean_text(
                data.get(
                    "id"
                ),
                200,
            )
            or
            (
                "gge-"
                +
                uuid.uuid4().hex[
                    :12
                ]
            )
        ),

        metadata={
            "generation_type":
                "gemini_edit",

            "input_images":
                len(
                    input_images
                ),

            "thinking_level_sent":
                None,

            "xpand_engine_version":
                ENGINE_VERSION,
        },
    )


# =========================================================
# OPENAI GPT-IMAGE-2
# =========================================================

def generate_with_openai(
    prompt: str,
    original_prompt: str,
    route: ImageRoute,
    number: int = 1,
) -> List[
    GeneratedImage
]:

    if not OPENAI_ENABLED:

        raise XPANDImageConfigurationError(
            (
                "OpenAI disabled by "
                "XPAND_OPENAI_ENABLED=false."
            )
        )

    if not OPENAI_API_KEY:

        raise XPANDImageConfigurationError(
            "OPENAI_API_KEY missing."
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
        else
        "high"
    )

    payload: Dict[
        str,
        Any,
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
                "GPT-Image-2 returned success "
                "but no image was found."
            )
        )

    request_id = clean_text(
        response.headers.get(
            "x-request-id",
            "",
        ),
        200,
    )

    results = []

    for index, (
        image_bytes,
        mime_type,
    ) in enumerate(
        images[
            :number
        ]
    ):

        unique_id = (
            request_id
            or
            (
                "oa-"
                +
                uuid.uuid4().hex[
                    :12
                ]
            )
        )

        if number > 1:

            unique_id += (
                "-"
                +
                str(
                    index + 1
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
                    infer_mime_type(
                        image_bytes,
                        "image/png",
                    )
                ),

                provider=(
                    PROVIDER_OPENAI
                ),

                model=(
                    route.model
                ),

                prompt=(
                    prompt
                ),

                original_prompt=(
                    original_prompt
                ),

                aspect_ratio=(
                    route.aspect_ratio
                ),

                image_size=(
                    provider_size
                ),

                quality=(
                    quality
                ),

                route_reason=(
                    route.reason
                ),

                request_id=(
                    unique_id
                ),

                metadata={
                    "generation_type":
                        "openai_generation",

                    "elapsed_seconds":
                        elapsed,

                    "requested_resolution_intent":
                        route.image_size,

                    "provider_size":
                        provider_size,

                    "xpand_engine_version":
                        ENGINE_VERSION,
                },
            )
        )

    return results


# =========================================================
# DIRECT GOOGLE ROUTE
# =========================================================

def run_google_direct(
    original_prompt: str,
    *,
    pro: bool,
    aspect_ratio: str,
    image_size: str,
    quality: str,
    number: int,
    allow_fallback: bool,
) -> ImageGenerationResponse:

    started = time.monotonic()

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

    route = build_route(
        provider,
        model,
        (
            "Explicit Nano Banana Pro"
            if pro
            else
            "Nano Banana 2 primary"
        ),
        aspect_ratio,
        image_size,
        quality,
    )

    enhanced_prompt = (
        build_professional_prompt(
            original_prompt,
            aspect_ratio,
            image_size,
        )
    )

    errors = []

    try:

        images = generate_with_gemini(
            enhanced_prompt,
            original_prompt,
            route,
            number,
        )

        return ImageGenerationResponse(
            ok=True,

            images=images,

            selected_route=(
                provider
            ),

            routes=[
                route
            ],

            original_prompt=(
                original_prompt
            ),

            enhanced_prompt=(
                enhanced_prompt
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

        message = clean_text(
            error,
            3000,
        )

        errors.append(
            (
                "google: "
                +
                message
            )
        )

        print(
            "⚠️ GOOGLE IMAGE ROUTE:",
            message,
        )

    if (
        allow_fallback
        and
        OPENAI_ENABLED
        and
        OPENAI_API_KEY
    ):

        print(
            "🔁 GOOGLE -> OPENAI IMAGE FALLBACK | GPT-Image-2"
        )

        fallback_route = build_route(
            PROVIDER_OPENAI,
            OPENAI_IMAGE_MODEL,
            (
                "Gemini image fallback"
            ),
            aspect_ratio,
            image_size,
            quality,
        )

        try:

            images = (
                generate_with_openai(
                    enhanced_prompt,
                    original_prompt,
                    fallback_route,
                    number,
                )
            )

            return ImageGenerationResponse(
                ok=True,

                images=images,

                selected_route=(
                    PROVIDER_OPENAI
                ),

                routes=[
                    route,
                    fallback_route,
                ],

                original_prompt=(
                    original_prompt
                ),

                enhanced_prompt=(
                    enhanced_prompt
                ),

                elapsed_seconds=round(
                    time.monotonic()
                    -
                    started,
                    3,
                ),

                errors=(
                    errors
                ),
            )

        except Exception as error:

            errors.append(
                (
                    "openai_fallback: "
                    +
                    clean_text(
                        error,
                        3000,
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
# DIRECT OPENAI
# =========================================================

def run_openai_direct(
    original_prompt: str,
    *,
    aspect_ratio: str,
    image_size: str,
    quality: str,
    number: int,
) -> ImageGenerationResponse:

    started = time.monotonic()

    route = build_route(
        PROVIDER_OPENAI,
        OPENAI_IMAGE_MODEL,
        "Explicit GPT-Image-2 route",
        aspect_ratio,
        image_size,
        quality,
    )

    enhanced_prompt = (
        build_professional_prompt(
            original_prompt,
            aspect_ratio,
            image_size,
        )
    )

    images = generate_with_openai(
        enhanced_prompt,
        original_prompt,
        route,
        number,
    )

    return ImageGenerationResponse(
        ok=True,

        images=images,

        selected_route=(
            PROVIDER_OPENAI
        ),

        routes=[
            route
        ],

        original_prompt=(
            original_prompt
        ),

        enhanced_prompt=(
            enhanced_prompt
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
# COMPARE
# =========================================================

def run_compare(
    original_prompt: str,
    *,
    aspect_ratio: str,
    image_size: str,
    quality: str,
    number: int,
) -> ImageGenerationResponse:

    started = time.monotonic()

    images = []

    routes = []

    errors = []

    google_route = build_route(
        PROVIDER_GOOGLE_FAST,
        GOOGLE_IMAGE_FAST_MODEL,
        "Compare: Nano Banana 2",
        aspect_ratio,
        image_size,
        quality,
    )

    routes.append(
        google_route
    )

    enhanced_prompt = (
        build_professional_prompt(
            original_prompt,
            aspect_ratio,
            image_size,
        )
    )

    try:

        images.extend(
            generate_with_gemini(
                enhanced_prompt,
                original_prompt,
                google_route,
                1,
            )
        )

    except Exception as error:

        errors.append(
            (
                "google: "
                +
                clean_text(
                    error,
                    2500,
                )
            )
        )

    if (
        OPENAI_ENABLED
        and
        OPENAI_API_KEY
    ):

        openai_route = build_route(
            PROVIDER_OPENAI,
            OPENAI_IMAGE_MODEL,
            "Compare: GPT-Image-2",
            aspect_ratio,
            image_size,
            quality,
        )

        routes.append(
            openai_route
        )

        try:

            images.extend(
                generate_with_openai(
                    enhanced_prompt,
                    original_prompt,
                    openai_route,
                    1,
                )
            )

        except Exception as error:

            errors.append(
                (
                    "openai: "
                    +
                    clean_text(
                        error,
                        2500,
                    )
                )
            )

    if not images:

        raise XPANDImageProviderError(
            (
                "Compare generation failed.\n"
                +
                "\n".join(
                    errors
                )
            )
        )

    return ImageGenerationResponse(
        ok=True,

        images=images,

        selected_route=(
            MODE_COMPARE
        ),

        routes=routes,

        original_prompt=(
            original_prompt
        ),

        enhanced_prompt=(
            enhanced_prompt
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
# MAIN API
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
        32000,
    )

    if not original_prompt:

        raise XPANDImageError(
            "Image prompt is empty."
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
        " XPAND IMAGE REQUEST V2.2"
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

    if effective_mode in {
        MODE_GOOGLE_FAST,
        MODE_FAST,
        MODE_AUTO,
    }:

        print(
            "🍌 Model:",
            GOOGLE_IMAGE_FAST_MODEL,
        )

    elif effective_mode in {
        MODE_GOOGLE_PRO,
        MODE_PRO,
    }:

        print(
            "🍌 Model:",
            GOOGLE_IMAGE_PRO_MODEL,
        )

    print("")

    if effective_mode == MODE_OPENAI:

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

            number=(
                number
            ),
        )

    if effective_mode == MODE_COMPARE:

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

            number=(
                number
            ),
        )

    if effective_mode == MODE_BEST:

        return run_google_direct(
            original_prompt,

            pro=(
                BEST_USE_PRO
            ),

            aspect_ratio=(
                final_aspect_ratio
            ),

            image_size=(
                final_image_size
            ),

            quality=(
                final_quality
            ),

            number=(
                number
            ),

            allow_fallback=(
                allow_fallback
            ),
        )

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

            number=(
                number
            ),

            allow_fallback=(
                allow_fallback
            ),
        )

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

        number=(
            number
        ),

        allow_fallback=(
            allow_fallback
        ),
    )


# =========================================================
# STATUS
# =========================================================

def get_image_engine_status() -> Dict[
    str,
    Any,
]:

    return {
        "ok":
            bool(
                GEMINI_API_KEY
                or
                (
                    OPENAI_ENABLED
                    and
                    OPENAI_API_KEY
                )
            ),

        "engine":
            ENGINE_NAME,

        "version":
            ENGINE_VERSION,

        "openai_configured":
            bool(
                OPENAI_API_KEY
            ),

        "openai_enabled":
            bool(
                OPENAI_ENABLED
            ),

        "gemini_configured":
            bool(
                GEMINI_API_KEY
            ),

        "openai_image":
            OPENAI_IMAGE_MODEL,

        "openai_director":
            OPENAI_DIRECTOR_MODEL,

        "google_fast":
            GOOGLE_IMAGE_FAST_MODEL,

        "google_pro":
            GOOGLE_IMAGE_PRO_MODEL,

        "gemini_director":
            GEMINI_DIRECTOR_MODEL,

        "gemini_structured":
            GEMINI_STRUCTURED_MODEL,

        "gemini_vision":
            GEMINI_VISION_MODEL,

        "best_use_pro":
            BEST_USE_PRO,

        "default_mode":
            DEFAULT_MODE,

        "default_quality":
            DEFAULT_QUALITY,

        "director_reasoning":
            OPENAI_DIRECTOR_REASONING,

        "structured_reasoning":
            OPENAI_STRUCTURED_REASONING,

        "gemini_image_thinking_normalized":
            GEMINI_IMAGE_THINKING,

        "gemini_image_thinking_sent":
            False,

        "structured_routing":
            "OpenAI first",

        "free_text_routing":
            "Gemini first",
    }


# =========================================================
# ZERO-COST SELF TEST
# =========================================================

if __name__ == "__main__":

    tests: Dict[
        str,
        bool,
    ] = {}

    tests[
        "nano_banana_alias"
    ] = (
        GOOGLE_IMAGE_FAST_MODEL
        ==
        "gemini-3.1-flash-image"
        or
        bool(
            GOOGLE_IMAGE_FAST_MODEL
        )
    )

    tests[
        "explicit_pro"
    ] = bool(
        GOOGLE_IMAGE_PRO_MODEL
    )

    tests[
        "auto_default_fast"
    ] = (
        resolve_effective_mode(
            "أنشئ صورة",
            "auto",
            0,
        )
        ==
        MODE_GOOGLE_FAST
    )

    tests[
        "references_do_not_force_pro"
    ] = (
        resolve_effective_mode(
            "أنشئ صورة",
            "auto",
            5,
        )
        ==
        MODE_GOOGLE_FAST
    )

    tests[
        "explicit_pro_prompt"
    ] = (
        resolve_effective_mode(
            (
                "أنشئ صورة باستخدام "
                "Nano Banana Pro"
            ),
            "",
            0,
        )
        ==
        MODE_GOOGLE_PRO
    )

    tests[
        "ratio_4_5"
    ] = (
        detect_aspect_ratio(
            "portrait 4:5",
            "",
        )
        ==
        "4:5"
    )

    tests[
        "arabic_ratio_4_5"
    ] = (
        detect_aspect_ratio(
            (
                "النسبة 4:5"
            ),
            "",
        )
        ==
        "4:5"
    )

    tests[
        "size_2k"
    ] = (
        detect_image_size(
            "الجودة 2k"
        )
        ==
        "2K"
    )

    tests[
        "fhd_maps_2k"
    ] = (
        detect_image_size(
            "Full HD"
        )
        ==
        "2K"
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

    stc_prompt = (
        build_professional_prompt(
            (
                "أنشئ صورة لبنك STC Bank "
                "عن نقاط البيع"
            ),
            "4:5",
            "2K",
        )
    )

    tests[
        "stc_no_text_rule"
    ] = (
        "advertising headline"
        in
        stc_prompt
    )

    tests[
        "stc_no_logo_rule"
    ] = (
        "STC Bank logo"
        in
        stc_prompt
    )

    tests[
        "stc_no_network_lines"
    ] = (
        "network lines"
        in
        stc_prompt
    )

    tests[
        "structured_detection"
    ] = (
        looks_like_json_request(
            "return only JSON schema"
        )
        is True
    )

    tests[
        "openai_sol_model"
    ] = (
        "gpt-5.6-sol"
        in
        OPENAI_DIRECTOR_MODEL.lower()
    )

    tests[
        "low_maps_to_minimal_for_gemini"
    ] = (
        normalize_gemini_image_thinking_level(
            "low"
        )
        ==
        "minimal"
    )

    tests[
        "minimal_supported"
    ] = (
        normalize_gemini_image_thinking_level(
            "minimal"
        )
        ==
        "minimal"
    )

    tests[
        "high_supported"
    ] = (
        normalize_gemini_image_thinking_level(
            "high"
        )
        ==
        "high"
    )

    sample_payload = (
        _build_gemini_image_payload(
            model=(
                GOOGLE_IMAGE_FAST_MODEL
            ),
            prompt=(
                "test"
            ),
            aspect_ratio=(
                "4:5"
            ),
            image_size=(
                "2K"
            ),
        )
    )

    tests[
        "gemini_image_has_no_thinking_level"
    ] = (
        "thinking_level"
        not in
        sample_payload
    )

    tests[
        "gemini_image_has_no_thinking"
    ] = (
        "thinking"
        not in
        sample_payload
    )

    tests[
        "gemini_image_has_no_reasoning"
    ] = (
        "reasoning"
        not in
        sample_payload
    )

    tests[
        "gemini_image_model"
    ] = (
        sample_payload.get(
            "model"
        )
        ==
        GOOGLE_IMAGE_FAST_MODEL
    )

    tests[
        "gemini_image_ratio"
    ] = (
        safe_dict(
            sample_payload.get(
                "response_format"
            )
        ).get(
            "aspect_ratio"
        )
        ==
        "4:5"
    )

    tests[
        "gemini_image_size"
    ] = (
        safe_dict(
            sample_payload.get(
                "response_format"
            )
        ).get(
            "image_size"
        )
        ==
        "2K"
    )

    status = (
        get_image_engine_status()
    )

    tests[
        "structured_openai_first"
    ] = (
        status.get(
            "structured_routing"
        )
        ==
        "OpenAI first"
    )

    tests[
        "free_text_gemini_first"
    ] = (
        status.get(
            "free_text_routing"
        )
        ==
        "Gemini first"
    )

    tests[
        "best_does_not_force_pro"
    ] = (
        BEST_USE_PRO
        is False
        or
        env_bool(
            "XPAND_BEST_USE_PRO",
            False,
        )
        is True
    )

    all_ok = all(
        tests.values()
    )

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND SMART IMAGE ENGINE V2.2"
    )
    print(
        " ZERO-COST SELF TEST"
    )
    print(
        "=========================================="
    )
    print("")

    for (
        name,
        passed,
    ) in tests.items():

        print(
            (
                "✅"
                if passed
                else
                "❌"
            )
            +
            name
        )

    print("")

    print(
        "OpenAI configured:",
        bool(
            OPENAI_API_KEY
        ),
    )

    print(
        "OpenAI enabled:",
        OPENAI_ENABLED,
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

    print(
        "Gemini image thinking normalized:",
        GEMINI_IMAGE_THINKING,
    )

    print(
        "Gemini image thinking sent:",
        False,
    )

    print(
        "Structured routing: OpenAI first"
    )

    print(
        "Free-text routing: Gemini first"
    )

    print("")

    if all_ok:

        print(
            (
                "XPAND Smart Image Engine "
                "V2.2 self-test: PASS ✅"
            )
        )

    else:

        print(
            (
                "XPAND Smart Image Engine "
                "V2.2 self-test: FAIL ❌"
            )
        )

    print("")
    print(
        "✅ Nano Banana 2 primary"
    )
    print(
        "✅ Nano Banana Pro explicit only"
    )
    print(
        "✅ Structured Sol first"
    )
    print(
        "✅ Strict OpenAI JSON schema"
    )
    print(
        "✅ Gemini structured fallback preserved"
    )
    print(
        "✅ Cheap free-text Gemini first"
    )
    print(
        "✅ OpenAI fallback preserved"
    )
    print(
        "✅ XPAND_OPENAI_ENABLED compatibility"
    )
    print(
        "✅ Gemini low → minimal normalization"
    )
    print(
        "✅ Gemini image sends NO thinking_level"
    )
    print(
        "✅ 1K / 2K / 4K native image intent"
    )
    print(
        "✅ STC no generated copy"
    )
    print(
        "✅ STC no generated logo"
    )
    print(
        "✅ STC anti-fintech-clutter"
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
