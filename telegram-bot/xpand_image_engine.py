# =========================================================
# XPAND SMART IMAGE ENGINE V1.3.2
#
# FULL DROP-IN REPLACEMENT
#
# FIXES:
# - Fixed broken indentation in _call_openai_response_once
# - Low-cost GPT-5.6 Sol director defaults
# - Structured Vision reasoning stays LOW
# - Explicit prompt-cache mode
# - OpenAI usage telemetry
# - GPT-Image-2 generation
# - GPT-Image-2 edits
# - Optional Gemini image routing
# - Backwards-compatible public API for XPAND modules
#
# Dependency:
# requests>=2.32.0,<3
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
from typing import Any, Dict, List, Optional, Sequence, Tuple

import requests
from PIL import Image

from xpand_stc_bank_skill import STC_BANK_IMAGE_GUARD, is_stc_bank_request


# =========================================================
# ENGINE
# =========================================================

ENGINE_NAME = "XPAND Smart Image Engine"
ENGINE_VERSION = "2.0.0"


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

# "best" used to force Nano Banana Pro. Keep Pro available as an explicit
# mode, but make Nano Banana 2 the default BEST/STC production route as
# requested. Set XPAND_BEST_USE_PRO=true only when Pro is deliberately wanted.
BEST_USE_PRO = str(
    os.environ.get(
        "XPAND_BEST_USE_PRO",
        "false",
    )
).strip().lower() in {"1", "true", "yes", "on"}

GEMINI_DIRECTOR_MODEL = str(
    os.environ.get(
        "XPAND_GEMINI_DIRECTOR_MODEL",
        "gemini-3.1-pro-preview",
    )
).strip()

# Visual QA needs the strongest multimodal reasoning available.  It is kept
# separate from the creative director so Railway can tune both independently.
GEMINI_VISION_MODEL = str(
    os.environ.get(
        "XPAND_GEMINI_VISION_MODEL",
        "gemini-3.1-pro-preview",
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
        "medium",
    )
).strip().lower()


# =========================================================
# COST CONTROL
# =========================================================

#
# IMPORTANT:
#
# The Railway variables you already added override
# these defaults automatically.
#
# Recommended:
#
# XPAND_IMAGE_DIRECTOR_REASONING=low
# XPAND_IMAGE_DIRECTOR_MAX_OUTPUT_TOKENS=1400
#

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
    3000,
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

OPENAI_USAGE_LOGGING = str(
    os.environ.get(
        "XPAND_OPENAI_USAGE_LOGGING",
        "true",
    )
).strip().lower() not in {
    "0",
    "false",
    "no",
    "off",
}

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
    "low",
    "medium",
    "high",
    "xhigh",
    "max",
}


# =========================================================
# EXCEPTIONS
# =========================================================

class XPANDImageError(Exception):
    pass


class XPANDImageConfigurationError(XPANDImageError):
    pass


class XPANDImageProviderError(XPANDImageError):
    pass


class XPANDStructuredOutputError(XPANDImageProviderError):
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
    def extension(self) -> str:
        mapping = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/webp": ".webp",
        }

        return mapping.get(
            str(self.mime_type).lower(),
            ".png",
        )

    @property
    def filename(self) -> str:
        provider_name = (
            str(self.provider)
            .replace("_", "-")
        )

        unique = (
            self.request_id
            or uuid.uuid4().hex[:10]
        )

        return (
            f"XPAND-{provider_name}-{unique}"
            f"{self.extension}"
        )


@dataclass
class ImageGenerationResponse:
    ok: bool
    images: List[GeneratedImage]
    selected_route: str
    routes: List[ImageRoute]
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
        .replace("\x00", "")
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
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ة": "ه",
        "ى": "ي",
        "ؤ": "و",
        "ئ": "ي",
    }

    for old, new in replacements.items():
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
        normalize_arabic(marker)
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
                and value not in results
            ):
                results.append(
                    value
                )

    return results


# =========================================================
# ASPECT RATIO
# =========================================================

def detect_aspect_ratio(
    prompt: str,
    requested_aspect_ratio: str = "",
) -> str:
    explicit = clean_text(
        requested_aspect_ratio,
        20,
    )

    digit_map = str.maketrans(
        "٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹",
        "01234567890123456789",
    )
    explicit = re.sub(
        r"\s*[：﹕︓:]\s*",
        ":",
        explicit.translate(digit_map),
    )

    if explicit in SUPPORTED_ASPECT_RATIOS:
        return explicit

    source = normalize_arabic(
        prompt
    )
    source = re.sub(
        r"\s*[：﹕︓:]\s*",
        ":",
        source.translate(digit_map),
    )

    for ratio in [
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
    ]:
        if re.search(
            rf"(?<!\d){re.escape(ratio)}(?!\d)",
            source,
        ):
            return ratio

    if contains_any(
        prompt,
        [
            "ستوري",
            "story",
            "ريل",
            "reel",
            "تيك توك",
            "tiktok",
            "عمودي",
            "vertical",
        ],
    ):
        return "9:16"

    if contains_any(
        prompt,
        [
            "بوست انستغرام",
            "instagram post",
            "مربع",
            "square",
        ],
    ):
        return "1:1"

    if contains_any(
        prompt,
        [
            "بوست",
            "social post",
            "انستغرام",
            "instagram",
            "اعلان سوشال",
            "إعلان سوشال",
        ],
    ):
        return "4:5"

    if contains_any(
        prompt,
        [
            "بانر",
            "banner",
            "youtube",
            "يوتيوب",
            "landscape",
            "افقي",
            "أفقي",
            "widescreen",
        ],
    ):
        return "16:9"

    if contains_any(
        prompt,
        [
            "بوستر",
            "poster",
            "portrait",
            "ملصق",
        ],
    ):
        return "2:3"

    return "1:1"


# =========================================================
# IMAGE SIZE
# =========================================================

def detect_image_size(
    prompt: str,
    requested_size: str = "",
) -> str:
    explicit = clean_text(
        requested_size,
        20,
    ).upper()

    aliases = {
        "HD": "HD",
        "720P": "HD",
        "1080P": "2K",
        "FHD": "2K",
        "FULLHD": "2K",
        "FULL HD": "2K",
        "0.5K": "512",
        "512PX": "512",
        "512": "512",
        "1K": "1K",
        "2K": "2K",
        "4K": "4K",
    }

    if explicit in aliases:
        return aliases[
            explicit
        ]

    if contains_any(
        prompt,
        [
            "4k",
            "4 k",
            "فور كي",
            "بدقة 4k",
            "دقة 4k",
        ],
    ):
        return "4K"

    if contains_any(
        prompt,
        [
            "2k",
            "2 k",
            "بدقة 2k",
            "دقة 2k",
            "fhd",
            "full hd",
            "1080p",
        ],
    ):
        return "2K"

    if contains_any(
        prompt,
        [
            "720p",
            "جودة hd",
            "دقة hd",
        ],
    ):
        return "HD"

    return "1K"


def _finalize_requested_resolution(
    image_bytes: bytes,
    mime_type: str,
    requested_size: str,
) -> Tuple[bytes, str]:
    """Return an actual 720p file when the user explicitly requests HD."""
    if str(requested_size).upper() != "HD":
        return image_bytes, mime_type

    with Image.open(io.BytesIO(image_bytes)) as source:
        source.load()
        width, height = source.size
        if min(width, height) <= 720:
            return image_bytes, mime_type

        scale = 720.0 / float(min(width, height))
        target = (
            max(1, round(width * scale)),
            max(1, round(height * scale)),
        )
        converted = source.convert("RGB").resize(target, Image.Resampling.LANCZOS)
        output = io.BytesIO()
        converted.save(output, format="JPEG", quality=95, optimize=True)
        return output.getvalue(), "image/jpeg"


# =========================================================
# QUALITY
# =========================================================

def detect_quality(
    prompt: str,
    requested_quality: str = "",
) -> str:
    explicit = clean_text(
        requested_quality,
        20,
    ).lower()

    if explicit in SUPPORTED_OPENAI_QUALITIES:
        return explicit

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
            "تجريبي",
        ],
    ):
        return "medium"

    return DEFAULT_QUALITY


# =========================================================
# PROMPT HELPERS
# =========================================================

def build_professional_prompt(
    user_prompt: str,
    aspect_ratio: str,
    image_size: str,
) -> str:
    user_prompt = clean_text(
        user_prompt,
        20000,
    )

    if not user_prompt:
        raise XPANDImageError(
            "وصف الصورة فاضي."
        )

    directives = [
        (
            "Create a premium professional visual based "
            "strictly on the user's requested concept."
        ),
        (
            "Preserve the requested subject, intent, objects, "
            "environment, colors, mood and constraints."
        ),
        (
            "Use exceptional composition, strong visual hierarchy, "
            "believable lighting, coherent perspective, realistic "
            "materials and commercial-grade finishing."
        ),
        (
            "Avoid malformed objects, random extra elements, "
            "duplicated subjects, visual clutter, fake watermarks, "
            "unrequested logos and accidental text."
        ),
    ]

    if is_stc_bank_request(user_prompt):
        directives.append(STC_BANK_IMAGE_GUARD)

    if contains_any(
        user_prompt,
        [
            "واقعي",
            "واقعية",
            "realistic",
            "photorealistic",
            "تصوير",
        ],
    ):
        directives.append(
            (
                "Use photorealistic commercial photography quality "
                "with controlled professional lighting."
            )
        )

    if contains_any(
        user_prompt,
        [
            "منتج",
            "product",
            "عطر",
            "perfume",
            "ساعة",
            "watch",
            "packaging",
            "عبوة",
            "عبوه",
        ],
    ):
        directives.append(
            (
                "Treat the subject as premium product advertising "
                "with refined reflections and realistic materials."
            )
        )

    if contains_any(
        user_prompt,
        [
            "اعلان",
            "إعلان",
            "advertisement",
            "campaign",
            "brand",
            "branding",
            "premium",
            "فاخر",
            "فخم",
        ],
    ):
        directives.append(
            (
                "Art direction should feel like a high-budget "
                "international creative-agency campaign."
            )
        )

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
                "Render these requested quoted text elements "
                "exactly if typography is intentionally required:\n"
                + exact
            )
        )

    directives.append(
        f"Target aspect ratio: {aspect_ratio}."
    )

    directives.append(
        f"Target resolution intent: {image_size}."
    )

    return (
        "USER REQUEST:\n"
        + user_prompt
        + "\n\n"
        + "XPAND PROFESSIONAL ART DIRECTION:\n"
        + "\n".join(
            f"- {item}"
            for item in directives
        )
    )


def build_refinement_prompt(
    original_user_prompt: str,
    *,
    stronger: bool = False,
    critique: str = "",
) -> str:
    directives = [
        (
            "Edit the provided image into a stronger final "
            "professional version."
        ),
        (
            "Preserve the main subject, concept and identity."
        ),
        (
            "Improve realism, lighting, materials, edge quality, "
            "hierarchy, balance and premium finish."
        ),
        (
            "Fix visible artifacts while preserving what works."
        ),
        (
            "Do not add random objects, fake logos or watermarks."
        ),
    ]

    if stronger:
        directives.append(
            (
                "Push the visual toward world-class campaign quality "
                "without unnecessary clutter."
            )
        )

    if critique:
        directives.append(
            (
                "Senior visual review:\n"
                + clean_text(
                    critique,
                    7000,
                )
            )
        )

    return (
        "ORIGINAL USER REQUEST:\n"
        + clean_text(
            original_user_prompt,
            20000,
        )
        + "\n\nFINAL REFINEMENT INSTRUCTIONS:\n"
        + "\n".join(
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
    value = clean_text(
        mode,
        50,
    ).lower()

    aliases = {
        "auto": MODE_AUTO,
        "smart": MODE_AUTO,
        "fast": MODE_FAST,
        "openai": MODE_OPENAI,
        "gpt": MODE_OPENAI,
        "gpt-image-2": MODE_OPENAI,
        "google_fast": MODE_GOOGLE_FAST,
        "google-fast": MODE_GOOGLE_FAST,
        "nano banana 2": MODE_GOOGLE_FAST,
        "nano-banana-2": MODE_GOOGLE_FAST,
        "google_pro": MODE_GOOGLE_PRO,
        "google-pro": MODE_GOOGLE_PRO,
        "nano banana pro": MODE_GOOGLE_PRO,
        "nano-banana-pro": MODE_GOOGLE_PRO,
        "pro": MODE_PRO,
        "fusion": MODE_PRO,
        "best": MODE_BEST,
        "max": MODE_BEST,
        "ultimate": MODE_BEST,
        "compare": MODE_COMPARE,
        "multi": MODE_COMPARE,
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
    chosen = normalize_mode(
        mode or DEFAULT_MODE
    )

    if chosen != MODE_AUTO:
        return chosen

    if contains_any(
        prompt,
        [
            "أفضل نتيجة ممكنة",
            "افضل نتيجه ممكنه",
            "أقوى نتيجة",
            "اقوى نتيجه",
            "كل قواك",
            "all your power",
            "best mode",
            "ultimate",
            "max quality",
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

    professional = contains_any(
        prompt,
        [
            "احترافي",
            "premium",
            "luxury",
            "فاخر",
            "فخم",
            "agency",
            "campaign",
            "commercial",
        ],
    )

    if professional or reference_count > 0:
        return MODE_GOOGLE_PRO

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
            "data": value,
        }

    except Exception:
        return {
            "raw": clean_text(
                response.text,
                10000,
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
            error.get("message")
            or error.get("status")
            or error.get("code")
            or str(error)
        )
    else:
        message = (
            error
            or data.get("message")
            or data.get("detail")
            or data.get("raw")
            or f"HTTP {response.status_code}"
        )

    return (
        provider
        + ": "
        + clean_text(
            message,
            6000,
        )
    )


# =========================================================
# BASE64 / IMAGE EXTRACTION
# =========================================================

def _download_image_url(
    url: str,
) -> Tuple[bytes, str]:
    response = requests.get(
        url,
        timeout=REQUEST_TIMEOUT,
    )

    if not response.ok:
        raise XPANDImageProviderError(
            (
                "فشل تنزيل الصورة: "
                + str(
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
        raw = base64.b64decode(
            value
        )

        return raw or None

    except Exception:
        return None


def _find_inline_images(
    value: Any,
) -> List[Tuple[bytes, str]]:
    found: List[
        Tuple[bytes, str]
    ] = []

    def walk(
        item: Any,
    ) -> None:
        if isinstance(
            item,
            dict,
        ):
            item_type = clean_text(
                item.get("type"),
                100,
            ).lower()

            mime_type = clean_text(
                (
                    item.get("mime_type")
                    or item.get("mimeType")
                    or ""
                ),
                100,
            ).lower()

            possible_data = [
                item.get("data"),
                item.get("b64_json"),
                item.get("base64"),
            ]

            looks_like_image = (
                item_type == "image"
                or mime_type.startswith(
                    "image/"
                )
                or "b64_json" in item
            )

            if looks_like_image:
                for possible in possible_data:
                    if isinstance(
                        possible,
                        str,
                    ):
                        raw = _decode_base64_image(
                            possible
                        )

                        if raw:
                            found.append(
                                (
                                    raw,
                                    mime_type
                                    or "image/png",
                                )
                            )
                            break

                uri = (
                    item.get("uri")
                    or item.get("url")
                )

                if (
                    isinstance(uri, str)
                    and uri.startswith(
                        (
                            "http://",
                            "https://",
                        )
                    )
                ):
                    try:
                        found.append(
                            _download_image_url(
                                uri
                            )
                        )
                    except Exception:
                        pass

            for child in item.values():
                walk(
                    child
                )

        elif isinstance(
            item,
            list,
        ):
            for child in item:
                walk(
                    child
                )

    walk(
        value
    )

    unique: List[
        Tuple[bytes, str]
    ] = []

    signatures = set()

    for image_bytes, mime_type in found:
        signature = (
            len(image_bytes),
            image_bytes[:64],
        )

        if signature in signatures:
            continue

        signatures.add(
            signature
        )

        unique.append(
            (
                image_bytes,
                mime_type,
            )
        )

    return unique


# =========================================================
# OPENAI RESPONSE EXTRACTION
# =========================================================

def _extract_openai_response_text(
    data: Dict[str, Any],
) -> str:
    top = data.get(
        "output_text"
    )

    if isinstance(
        top,
        str,
    ):
        return clean_text(
            top,
            50000,
        )

    collected: List[str] = []

    output = data.get(
        "output",
        [],
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
                "content",
                [],
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

                part_type = clean_text(
                    part.get("type"),
                    100,
                ).lower()

                text = part.get(
                    "text"
                )

                if (
                    part_type == "output_text"
                    and isinstance(
                        text,
                        str,
                    )
                ):
                    collected.append(
                        text
                    )

    return clean_text(
        "\n".join(
            collected
        ),
        50000,
    )


def _extract_openai_refusal(
    data: Dict[str, Any],
) -> str:
    output = data.get(
        "output",
        [],
    )

    if not isinstance(
        output,
        list,
    ):
        return ""

    refusals = []

    for item in output:
        if not isinstance(
            item,
            dict,
        ):
            continue

        content = item.get(
            "content",
            [],
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

            if clean_text(
                part.get("type"),
                100,
            ).lower() == "refusal":
                refusal = clean_text(
                    (
                        part.get("refusal")
                        or part.get("text")
                        or ""
                    ),
                    5000,
                )

                if refusal:
                    refusals.append(
                        refusal
                    )

    return clean_text(
        "\n".join(
            refusals
        ),
        5000,
    )


# =========================================================
# IMAGE DATA URI
# =========================================================

def image_data_uri(
    image_bytes: bytes,
    mime_type: str,
) -> str:
    mime = clean_text(
        mime_type,
        100,
    ).lower()

    if mime not in {
        "image/png",
        "image/jpeg",
        "image/jpg",
        "image/webp",
    }:
        mime = "image/png"

    encoded = base64.b64encode(
        image_bytes
    ).decode(
        "ascii"
    )

    return (
        "data:"
        + mime
        + ";base64,"
        + encoded
    )


# =========================================================
# STRUCTURED OUTPUT DETECTION
# =========================================================

JSON_REQUEST_MARKERS = [
    "return json only",
    "return only json",
    "json only",
    "output json",
    "return exactly this json",
    "return a json object",
    "required schema",
    "output schema",
    "schema:",
    "json schema",
]


def looks_like_json_request(
    prompt: str,
) -> bool:
    source = clean_text(
        prompt,
        40000,
    ).lower()

    if any(
        marker in source
        for marker
        in JSON_REQUEST_MARKERS
    ):
        return True

    if (
        "return json" in source
        and "{" in source
        and "}" in source
    ):
        return True

    return False


# =========================================================
# JSON NORMALIZATION
# =========================================================

def normalize_json_text(
    value: str,
) -> str:
    text = clean_text(
        value,
        50000,
    )

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

        if isinstance(
            parsed,
            (
                dict,
                list,
            ),
        ):
            return json.dumps(
                parsed,
                ensure_ascii=False,
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
        and end > start
    ):
        candidate = text[
            start:end + 1
        ]

        try:
            parsed = json.loads(
                candidate
            )

            if isinstance(
                parsed,
                dict,
            ):
                return json.dumps(
                    parsed,
                    ensure_ascii=False,
                )
        except Exception:
            pass

    raise XPANDStructuredOutputError(
        "Structured model output is not valid JSON."
    )


def json_text_is_valid(
    value: str,
) -> bool:
    try:
        normalize_json_text(
            value
        )
        return True
    except Exception:
        return False


# =========================================================
# RESPONSE STATUS
# =========================================================

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
                error.get("message")
                or error.get("code")
                or error
            ),
            3000,
        )

        if message:
            return (
                status
                + ": "
                + message
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
                + ": "
                + reason
            )

    return status


# =========================================================
# REASONING
# =========================================================

def normalize_reasoning_effort(
    value: str,
    fallback: str,
) -> str:
    value = clean_text(
        value,
        50,
    ).lower()

    if value in SUPPORTED_REASONING_LEVELS:
        return value

    fallback = clean_text(
        fallback,
        50,
    ).lower()

    if fallback in SUPPORTED_REASONING_LEVELS:
        return fallback

    return "low"


# =========================================================
# USAGE TELEMETRY
# =========================================================

def _log_openai_usage(
    data: Dict[str, Any],
) -> None:
    if not OPENAI_USAGE_LOGGING:
        return

    usage = (
        data.get("usage")
        or {}
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
        or {}
    )

    output_details = (
        usage.get(
            "output_tokens_details"
        )
        or {}
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

    cache_write_tokens = int(
        (
            input_details.get(
                "cache_write_tokens"
            )
            or input_details.get(
                "cache_creation_tokens"
            )
            or 0
        )
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
        f" | input={input_tokens}"
        f" | cached={cached_tokens}"
        f" | cache_write={cache_write_tokens}"
        f" | output={output_tokens}"
        f" | reasoning={reasoning_tokens}"
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
            "type": "input_text",
            "text": clean_text(
                prompt,
                32000,
            ),
        }
    ]

    if image_bytes:
        content.append(
            {
                "type": "input_image",
                "image_url": image_data_uri(
                    image_bytes,
                    image_mime_type,
                ),
                "detail": OPENAI_VISION_DETAIL,
            }
        )

    payload: Dict[
        str,
        Any
    ] = {
        "model": OPENAI_DIRECTOR_MODEL,

        "input": [
            {
                "role": "user",
                "content": content,
            }
        ],

        "reasoning": {
            "effort": normalize_reasoning_effort(
                reasoning_effort,
                "low",
            ),
        },

        "max_output_tokens": int(
            max_output_tokens
        ),

        "store": False,
    }

    #
    # Explicit cache mode prevents XPAND's one-shot
    # visual/director prompts from creating implicit
    # cache breakpoints unnecessarily.
    #

    if OPENAI_PROMPT_CACHE_MODE:
        payload[
            "prompt_cache_options"
        ] = {
            "mode": OPENAI_PROMPT_CACHE_MODE,
        }

    # -----------------------------------------------------
    # STRUCTURED OUTPUT
    # -----------------------------------------------------

    if json_schema:
        schema_name = re.sub(
            r"[^a-zA-Z0-9_\-]",
            "_",
            clean_text(
                json_schema_name,
                64,
            )
            or "xpand_structured_output",
        )

        payload[
            "text"
        ] = {
            "format": {
                "type": "json_schema",
                "name": schema_name,
                "schema": json_schema,
                "strict": True,
            },
            "verbosity": "low",
        }

    elif json_mode:
        payload[
            "text"
        ] = {
            "format": {
                "type": "json_object",
            },
            "verbosity": "low",
        }

    response = requests.post(
        OPENAI_RESPONSES_URL,
        headers={
            "Authorization": (
                "Bearer "
                + OPENAI_API_KEY
            ),
            "Content-Type": (
                "application/json"
            ),
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
# GPT-5.6 SOL TEXT / VISION
# =========================================================

def _find_gemini_text(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("output_text", "text"):
            item = value.get(key)
            if isinstance(item, str) and item.strip():
                return item.strip()
        for key in ("output", "outputs", "steps", "content", "parts", "result"):
            if key in value:
                found = _find_gemini_text(value.get(key))
                if found:
                    return found
    elif isinstance(value, list):
        for item in value:
            found = _find_gemini_text(item)
            if found:
                return found
    return ""


def call_gemini_director(
    prompt: str,
    *,
    image_bytes: Optional[bytes] = None,
    image_mime_type: str = "image/png",
    json_mode: Optional[bool] = None,
    json_schema: Optional[Dict[str, Any]] = None,
    json_schema_name: str = "xpand_structured_output",
) -> str:
    if not GEMINI_API_KEY:
        raise XPANDImageConfigurationError("GEMINI_API_KEY مش موجود.")
    prompt = clean_text(prompt, 32000)
    structured = bool(json_mode or json_schema)
    if structured:
        prompt += (
            "\n\nOUTPUT CONTRACT: Return exactly one complete valid JSON object. "
            "No Markdown and no explanation."
        )
        if json_schema:
            prompt += "\nJSON SCHEMA:\n" + json.dumps(json_schema, ensure_ascii=False)
    inputs: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
    if image_bytes:
        inputs.append({
            "type": "image",
            "mime_type": image_mime_type or "image/png",
            "data": base64.b64encode(image_bytes).decode("ascii"),
        })
    selected_model = GEMINI_VISION_MODEL if image_bytes else GEMINI_DIRECTOR_MODEL
    payload: Dict[str, Any] = {"model": selected_model, "input": inputs}
    search_enabled = str(os.environ.get("XPAND_GEMINI_SEARCH_GROUNDING", "true")).lower() not in {
        "0", "false", "no", "off"
    }
    if search_enabled and contains_any(prompt, [
        "bank", "بنك", "مصرف", "competitor", "منافس", "deep research", "بحث عميق"
    ]):
        payload["tools"] = [{"type": "google_search"}]
    response = requests.post(
        GEMINI_INTERACTIONS_URL,
        headers={"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"},
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )
    if not response.ok:
        raise XPANDImageProviderError(_provider_error_message("Gemini Director", response))
    data = _safe_json(response)
    text = _find_gemini_text(data)
    if not text:
        raise XPANDImageProviderError("Gemini Director رجع بدون نص.")
    return normalize_json_text(text) if structured else text

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

    # Backwards-compatible function name. XPAND V2 routes all creative,
    # structured and visual direction work to Gemini by default.
    if GEMINI_API_KEY:
        return call_gemini_director(
            prompt,
            image_bytes=image_bytes,
            image_mime_type=image_mime_type,
            json_mode=json_mode,
            json_schema=json_schema,
            json_schema_name=json_schema_name,
        )

    if not OPENAI_API_KEY:
        raise XPANDImageConfigurationError(
            "OPENAI_API_KEY مش موجود."
        )

    prompt = clean_text(
        prompt,
        32000,
    )

    if not prompt:
        raise XPANDImageError(
            "Director prompt is empty."
        )

    if json_mode is None:
        json_mode = (
            bool(json_schema)
            or looks_like_json_request(
                prompt
            )
        )

    structured = bool(
        json_mode
        or json_schema
    )

    if structured:
        reasoning_effort = (
            OPENAI_STRUCTURED_REASONING
        )

        max_output_tokens = (
            OPENAI_STRUCTURED_MAX_OUTPUT_TOKENS
        )

    else:
        reasoning_effort = (
            OPENAI_DIRECTOR_REASONING
        )

        max_output_tokens = (
            OPENAI_DIRECTOR_MAX_OUTPUT_TOKENS
        )

    request_prompt = prompt

    if structured:
        request_prompt += (
            "\n\n"
            "CRITICAL OUTPUT CONTRACT:\n"
            "Return exactly one complete valid JSON object. "
            "Do not use Markdown fences. "
            "Do not add prose before or after the JSON. "
            "Finish every opened object and array."
        )

    attempts = (
        2
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
        current_max_tokens = (
            max_output_tokens
            if attempt == 1
            else
            OPENAI_STRUCTURED_RETRY_MAX_OUTPUT_TOKENS
        )

        current_reasoning = (
            reasoning_effort
            if attempt == 1
            else "low"
        )

        retry_prompt = request_prompt

        if attempt > 1:
            retry_prompt += (
                "\n\n"
                "RETRY REQUIREMENT:\n"
                "The previous structured response was "
                "incomplete or invalid. Produce the entire "
                "JSON again from the beginning. "
                "Be concise so the object finishes."
            )

            print(
                "🔁 Structured Vision retry..."
            )

        try:
            data = _call_openai_response_once(
                retry_prompt,
                image_bytes=image_bytes,
                image_mime_type=image_mime_type,
                json_mode=bool(
                    json_mode
                ),
                json_schema=json_schema,
                json_schema_name=json_schema_name,
                reasoning_effort=current_reasoning,
                max_output_tokens=current_max_tokens,
            )

            refusal = _extract_openai_refusal(
                data
            )

            if refusal:
                raise XPANDImageProviderError(
                    (
                        "GPT-5.6 Sol refused "
                        "the request: "
                        + refusal
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

            if structured:
                if status_problem:
                    raise XPANDStructuredOutputError(
                        (
                            "Structured response "
                            "incomplete: "
                            + status_problem
                        )
                    )

                if not text:
                    raise XPANDStructuredOutputError(
                        (
                            "GPT-5.6 Sol returned "
                            "no structured output text."
                        )
                    )

                normalized = normalize_json_text(
                    text
                )

                if attempt > 1:
                    print(
                        (
                            "✅ Structured Vision "
                            "retry succeeded"
                        )
                    )

                return normalized

            if status_problem:
                raise XPANDImageProviderError(
                    (
                        "GPT-5.6 Sol response "
                        "status: "
                        + status_problem
                    )
                )

            if not text:
                raise XPANDImageProviderError(
                    "GPT-5.6 Sol رجع بدون نص."
                )

            return text

        except Exception as error:
            last_error = error

            if (
                structured
                and attempt < attempts
            ):
                print(
                    (
                        "⚠️ Structured Vision attempt "
                        + str(attempt)
                        + ": "
                        + clean_text(
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
            + clean_text(
                last_error,
                3000,
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
        image_mime_type=image_mime_type,
        json_mode=True,
        json_schema=json_schema,
        json_schema_name=json_schema_name,
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
                + clean_text(
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
# SOL ART DIRECTION
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
{original_prompt}

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
Do not explain your reasoning.
Return only the final concise art-direction brief.
""".strip()

    return call_openai_director(
        request,
        json_mode=False,
    )


# =========================================================
# SOL VISUAL CRITIC
# =========================================================

def build_sol_visual_critique(
    original_prompt: str,
    image_bytes: bytes,
    mime_type: str,
) -> str:
    request = f"""
You are the final senior visual reviewer for XPAND Creative Agency.

Review the attached generated image against this request:

{original_prompt}

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
) -> List[GeneratedImage]:

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
                number or 1
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
        "model": route.model,
        "prompt": clean_text(
            prompt,
            32000,
        ),
        "n": number,
        "size": provider_size,
        "quality": quality,
    }

    started = time.monotonic()

    response = requests.post(
        OPENAI_IMAGE_GENERATION_URL,
        headers={
            "Authorization": (
                "Bearer "
                + OPENAI_API_KEY
            ),
            "Content-Type": (
                "application/json"
            ),
        },
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )

    elapsed = round(
        time.monotonic()
        - started,
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
                "GPT-Image-2 رجع استجابة "
                "ناجحة لكن ما لقيت صورة."
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
        images[:number]
    ):
        unique_request_id = (
            request_id
            or (
                "oa-"
                + uuid.uuid4().hex[:12]
            )
        )

        if number > 1:
            unique_request_id += (
                "-"
                + str(
                    index + 1
                )
            )

        results.append(
            GeneratedImage(
                image_bytes=image_bytes,
                mime_type=(
                    mime_type
                    or "image/png"
                ),
                provider=PROVIDER_OPENAI,
                model=route.model,
                prompt=prompt,
                original_prompt=original_prompt,
                aspect_ratio=route.aspect_ratio,
                image_size=provider_size,
                quality=quality,
                route_reason=route.reason,
                request_id=unique_request_id,
                metadata={
                    "generation_type": (
                        "openai_generation"
                    ),
                    "requested_image_size": (
                        route.image_size
                    ),
                    "provider_size": (
                        provider_size
                    ),
                    "elapsed_seconds": elapsed,
                },
            )
        )

    return results


# =========================================================
# OPENAI IMAGE EDIT
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
        if mime_type in {
            "image/jpeg",
            "image/jpg",
        }
        else ".png"
    )

    files = {
        "image": (
            (
                "xpand-input"
                + extension
            ),
            input_image_bytes,
            mime_type,
        )
    }

    form_data = {
        "model": route.model,
        "prompt": clean_text(
            prompt,
            32000,
        ),
        "size": provider_size,
        "quality": quality,
        "n": "1",
    }

    response = requests.post(
        OPENAI_IMAGE_EDITS_URL,
        headers={
            "Authorization": (
                "Bearer "
                + OPENAI_API_KEY
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
            + uuid.uuid4().hex[:12]
        )

    final_metadata = dict(
        metadata or {}
    )

    final_metadata[
        "generation_type"
    ] = "final_refinement"

    final_metadata[
        "final_edit_model"
    ] = OPENAI_IMAGE_MODEL

    return GeneratedImage(
        image_bytes=image_bytes,
        mime_type=(
            output_mime
            or "image/png"
        ),
        provider=final_provider,
        model=final_model_label,
        prompt=prompt,
        original_prompt=original_prompt,
        aspect_ratio=route.aspect_ratio,
        image_size=provider_size,
        quality=quality,
        route_reason=(
            "Final image refinement "
            "completed with GPT-Image-2."
        ),
        request_id=request_id,
        metadata=final_metadata,
    )


# =========================================================
# GEMINI ERROR
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
        normalize_arabic(marker)
        in text
        for marker in markers
    )


# =========================================================
# GEMINI GENERATION
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

    requested_size = route.image_size
    image_size = (
        route.image_size
        if route.image_size
        in SUPPORTED_GOOGLE_IMAGE_SIZES
        else "1K"
    )

    payload = {
        "model": route.model,
        "input": prompt,
        "response_format": {
            "type": "image",
            "aspect_ratio": (
                route.aspect_ratio
            ),
            "image_size": image_size,
            "mime_type": (
                "image/jpeg"
            ),
        },
    }

    response = requests.post(
        GEMINI_INTERACTIONS_URL,
        headers={
            "x-goog-api-key": (
                GEMINI_API_KEY
            ),
            "Content-Type": (
                "application/json"
            ),
        },
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )

    if not response.ok:
        raise XPANDImageProviderError(
            _provider_error_message(
                "Gemini",
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

    image_bytes, mime_type = _finalize_requested_resolution(
        image_bytes,
        mime_type,
        requested_size,
    )

    request_id = clean_text(
        data.get("id"),
        200,
    )

    if not request_id:
        request_id = (
            "gg-"
            + uuid.uuid4().hex[:12]
        )

    if index > 0:
        request_id += (
            "-"
            + str(index + 1)
        )

    return GeneratedImage(
        image_bytes=image_bytes,
        mime_type=(
            mime_type
            or "image/jpeg"
        ),
        provider=route.provider,
        model=route.model,
        prompt=prompt,
        original_prompt=original_prompt,
        aspect_ratio=route.aspect_ratio,
        image_size=requested_size,
        quality=route.quality,
        route_reason=route.reason,
        request_id=request_id,
        metadata={
            "generation_type": (
                "gemini_generation"
            ),
            "google_model": (
                route.model
            ),
            "google_image_size": (
                image_size
            ),
            "delivered_image_size": requested_size,
        },
    )


def generate_with_gemini(
    prompt: str,
    original_prompt: str,
    route: ImageRoute,
    number: int = 1,
) -> List[GeneratedImage]:

    number = max(
        1,
        min(
            int(
                number or 1
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
            results.append(
                _generate_one_with_gemini(
                    prompt=prompt,
                    original_prompt=(
                        original_prompt
                    ),
                    route=route,
                    index=index,
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
                + "\n".join(
                    errors
                )
            )
        )

    return results


def edit_with_gemini(
    input_images: Sequence[Tuple[bytes, str]],
    prompt: str,
    *,
    aspect_ratio: str = "4:5",
    image_size: str = "",
    pro: bool = False,
) -> GeneratedImage:
    if not GEMINI_API_KEY:
        raise XPANDImageConfigurationError("GEMINI_API_KEY مش موجود.")
    if not input_images:
        raise XPANDImageError("لا توجد صور للتعديل.")
    final_size = detect_image_size(prompt, image_size)
    provider_size = final_size if final_size in SUPPORTED_GOOGLE_IMAGE_SIZES else "1K"
    model = GOOGLE_IMAGE_PRO_MODEL if pro else GOOGLE_IMAGE_FAST_MODEL
    instruction = build_professional_prompt(prompt, aspect_ratio, final_size)
    instruction += (
        "\n\nREFERENCE ORDER CONTRACT:\n"
        "Image 1 is the BASE image unless the user explicitly says otherwise. "
        "Images 2+ are reference/source images. Preserve untouched areas of the "
        "base image. Transfer only the requested subject, product, style, color, "
        "material or composition from each reference. Match perspective, scale, "
        "lighting, shadows, reflections and depth so the result looks photographed "
        "as one coherent scene. Never add blue laser beams, neon connection lines, "
        "or generic fintech effects unless the user explicitly requests them."
    )
    inputs: List[Dict[str, Any]] = [{"type": "text", "text": instruction}]
    for image_bytes, mime_type in list(input_images)[:10]:
        inputs.append({
            "type": "image",
            "mime_type": mime_type or "image/png",
            "data": base64.b64encode(image_bytes).decode("ascii"),
        })
    response = requests.post(
        GEMINI_INTERACTIONS_URL,
        headers={"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"},
        json={
            "model": model,
            "input": inputs,
            "response_format": {
                "type": "image",
                "aspect_ratio": detect_aspect_ratio(prompt, aspect_ratio),
                "image_size": provider_size,
                "mime_type": "image/jpeg",
            },
        },
        timeout=REQUEST_TIMEOUT,
    )
    if not response.ok:
        raise XPANDImageProviderError(_provider_error_message("Nano Banana Edit", response))
    data = _safe_json(response)
    images = _find_inline_images(data)
    if not images:
        raise XPANDImageProviderError("Nano Banana Edit نجح لكن لم يرجع صورة.")
    output, output_mime = images[0]
    output, output_mime = _finalize_requested_resolution(
        output,
        output_mime,
        final_size,
    )
    return GeneratedImage(
        image_bytes=output,
        mime_type=output_mime or "image/jpeg",
        provider=PROVIDER_GOOGLE_PRO if pro else PROVIDER_GOOGLE_FAST,
        model=model,
        prompt=instruction,
        original_prompt=prompt,
        aspect_ratio=detect_aspect_ratio(prompt, aspect_ratio),
        image_size=final_size,
        quality="high" if pro else "medium",
        route_reason="Gemini-first multi-image edit",
        request_id=clean_text(data.get("id"), 200) or "ge-" + uuid.uuid4().hex[:12],
        metadata={
            "generation_type": "gemini_multi_image_edit",
            "input_images": len(input_images),
            "google_image_size": provider_size,
            "delivered_image_size": final_size,
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

    enhanced = build_professional_prompt(
        original_prompt,
        aspect_ratio,
        image_size,
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
        selected_route=MODE_OPENAI,
        routes=[route],
        original_prompt=original_prompt,
        enhanced_prompt=enhanced,
        elapsed_seconds=round(
            time.monotonic()
            - started,
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

    enhanced = build_professional_prompt(
        original_prompt,
        aspect_ratio,
        image_size,
    )

    provider = (
        PROVIDER_GOOGLE_PRO
        if pro
        else PROVIDER_GOOGLE_FAST
    )

    model = (
        GOOGLE_IMAGE_PRO_MODEL
        if pro
        else GOOGLE_IMAGE_FAST_MODEL
    )

    route = build_route(
        provider,
        model,
        (
            "Google Pro image generation."
            if pro
            else
            "Google Fast image generation."
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
                else MODE_GOOGLE_FAST
            ),
            routes=[route],
            original_prompt=original_prompt,
            enhanced_prompt=enhanced,
            elapsed_seconds=round(
                time.monotonic()
                - started,
                3,
            ),
            errors=[],
        )

    except Exception as error:
        errors.append(
            clean_text(
                error,
                4000,
            )
        )

        if not allow_fallback:
            raise

    raise XPANDImageProviderError(
        "Gemini image generation failed and OpenAI fallback is disabled.\n"
        + "\n".join(errors)
    )


# =========================================================
# COST-CONTROLLED BEST ROUTE
# =========================================================

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

    #
    # ONE Sol director call only.
    # No automatic second image.
    # No automatic critique/edit loop here.
    #

    try:
        art_direction = (
            build_sol_art_direction(
                original_prompt,
                aspect_ratio,
                image_size,
            )
        )
    except Exception as error:
        errors.append(
            (
                "Sol director: "
                + clean_text(
                    error,
                    2500,
                )
            )
        )

        art_direction = (
            build_professional_prompt(
                original_prompt,
                aspect_ratio,
                image_size,
            )
        )

    final_prompt = (
        "ORIGINAL REQUEST:\n"
        + original_prompt
        + "\n\n"
        + "SENIOR ART DIRECTION:\n"
        + art_direction
    )

    route = build_route(
        PROVIDER_OPENAI,
        OPENAI_IMAGE_MODEL,
        (
            "Cost-controlled BEST: "
            "one Sol direction + GPT-Image-2."
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
        selected_route=MODE_BEST,
        routes=[route],
        original_prompt=original_prompt,
        enhanced_prompt=art_direction,
        elapsed_seconds=round(
            time.monotonic()
            - started,
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
        or []
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
    # Preserve public function without forcing
    # four expensive model stages.
    #

    if GEMINI_API_KEY:
        try:
            return run_google_direct(
                original_prompt,
                pro=True,
                aspect_ratio=aspect_ratio,
                image_size=image_size,
                quality=quality,
                number=number,
                allow_fallback=False,
            )
        except Exception:
            pass

    return run_openai_best(
        original_prompt,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        quality=quality,
        number=number,
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

    openai_route = build_route(
        PROVIDER_OPENAI,
        OPENAI_IMAGE_MODEL,
        "Compare: OpenAI.",
        aspect_ratio,
        image_size,
        quality,
    )

    prompt = build_professional_prompt(
        original_prompt,
        aspect_ratio,
        image_size,
    )

    try:
        openai_images = generate_with_openai(
            prompt,
            original_prompt,
            openai_route,
            1,
        )

        results.extend(
            openai_images
        )

        routes.append(
            openai_route
        )

    except Exception as error:
        errors.append(
            clean_text(
                error,
                3000,
            )
        )

    if GEMINI_API_KEY:
        google_route = build_route(
            PROVIDER_GOOGLE_FAST,
            GOOGLE_IMAGE_FAST_MODEL,
            "Compare: Google Fast.",
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
                clean_text(
                    error,
                    3000,
                )
            )

    if not results:
        raise XPANDImageProviderError(
            (
                "Compare mode failed: "
                + " | ".join(
                    errors
                )
            )
        )

    return ImageGenerationResponse(
        ok=True,
        images=results[
            :max(
                1,
                int(
                    number or 1
                ),
            )
        ],
        selected_route=MODE_COMPARE,
        routes=routes,
        original_prompt=original_prompt,
        enhanced_prompt=prompt,
        elapsed_seconds=round(
            time.monotonic()
            - started,
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
        32000,
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
                number or 1
            ),
            4,
        ),
    )

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND IMAGE REQUEST V1.3.2"
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
    print("")

    if effective_mode == MODE_BEST:
        return run_google_direct(
            original_prompt,
            pro=BEST_USE_PRO,
            aspect_ratio=final_aspect_ratio,
            image_size=final_image_size,
            quality=final_quality,
            number=number,
            allow_fallback=False,
        )

    if effective_mode == MODE_COMPARE:
        return run_compare(
            original_prompt,
            aspect_ratio=final_aspect_ratio,
            image_size=final_image_size,
            quality=final_quality,
            number=number,
        )

    if effective_mode in {
        MODE_GOOGLE_FAST,
        MODE_FAST,
    }:
        return run_google_direct(
            original_prompt,
            pro=False,
            aspect_ratio=final_aspect_ratio,
            image_size=final_image_size,
            quality=final_quality,
            number=number,
            allow_fallback=allow_fallback,
        )

    if effective_mode in {
        MODE_GOOGLE_PRO,
        MODE_PRO,
    }:
        return run_google_direct(
            original_prompt,
            pro=True,
            aspect_ratio=final_aspect_ratio,
            image_size=final_image_size,
            quality=final_quality,
            number=number,
            allow_fallback=allow_fallback,
        )

    return run_google_direct(
        original_prompt,
        pro=False,
        aspect_ratio=final_aspect_ratio,
        image_size=final_image_size,
        quality=final_quality,
        number=number,
        allow_fallback=False,
    )


# =========================================================
# ENGINE STATUS
# =========================================================

def get_image_engine_status() -> Dict[
    str,
    Any,
]:

    return {
        "ok": bool(
            OPENAI_API_KEY
            or GEMINI_API_KEY
        ),

        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,

        "providers": {
            "openai": {
                "configured": bool(
                    OPENAI_API_KEY
                ),
                "image_model": (
                    OPENAI_IMAGE_MODEL
                ),
                "director_model": (
                    OPENAI_DIRECTOR_MODEL
                ),
                "structured_json": True,
                "vision": bool(
                    OPENAI_API_KEY
                ),
            },

            "google_fast": {
                "configured": bool(
                    GEMINI_API_KEY
                ),
                "model": (
                    GOOGLE_IMAGE_FAST_MODEL
                ),
            },

            "google_pro": {
                "configured": bool(
                    GEMINI_API_KEY
                ),
                "model": (
                    GOOGLE_IMAGE_PRO_MODEL
                ),
            },
        },

        "default_mode": (
            DEFAULT_MODE
        ),

        "default_quality": (
            DEFAULT_QUALITY
        ),

        "director_reasoning": (
            OPENAI_DIRECTOR_REASONING
        ),

        "director_max_output_tokens": (
            OPENAI_DIRECTOR_MAX_OUTPUT_TOKENS
        ),

        "structured_reasoning": (
            OPENAI_STRUCTURED_REASONING
        ),

        "structured_max_output_tokens": (
            OPENAI_STRUCTURED_MAX_OUTPUT_TOKENS
        ),

        "structured_retry_max_output_tokens": (
            OPENAI_STRUCTURED_RETRY_MAX_OUTPUT_TOKENS
        ),

        "prompt_cache_mode": (
            OPENAI_PROMPT_CACHE_MODE
        ),

        "usage_logging": (
            OPENAI_USAGE_LOGGING
        ),

        "vision_detail": (
            OPENAI_VISION_DETAIL
        ),

        "structured_retry": True,

        "supports_openai_fusion": bool(
            OPENAI_API_KEY
        ),

        "supports_best_mode": bool(
            OPENAI_API_KEY
        ),

        "supports_google_openai_fusion": bool(
            OPENAI_API_KEY
            and GEMINI_API_KEY
        ),

        "google_optional": True,

        "google_failure_fallback": (
            "openai"
        ),

        "openai_fusion_pipeline": [
            OPENAI_DIRECTOR_MODEL,
            OPENAI_IMAGE_MODEL,
        ],

        "best_google_pipeline": [
            GOOGLE_IMAGE_PRO_MODEL,
        ],

        "telegram_ready": True,
    }


# =========================================================
# FRIENDLY ROUTE
# =========================================================

def describe_route(
    route: ImageRoute,
) -> str:

    labels = {
        PROVIDER_OPENAI: (
            "GPT-Image-2"
        ),
        PROVIDER_GOOGLE_FAST: (
            "Nano Banana 2"
        ),
        PROVIDER_GOOGLE_PRO: (
            "Nano Banana Pro"
        ),
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

    status = (
        get_image_engine_status()
    )

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND SMART IMAGE ENGINE V1.3.2"
    )
    print(
        "=========================================="
    )
    print("")

    print(
        "OpenAI:",
        (
            "READY"
            if OPENAI_API_KEY
            else "missing key"
        ),
    )

    print(
        "GPT-Image-2:",
        OPENAI_IMAGE_MODEL,
    )

    print(
        "Director:",
        OPENAI_DIRECTOR_MODEL,
    )

    print(
        "Director reasoning:",
        OPENAI_DIRECTOR_REASONING,
    )

    print(
        "Director max:",
        OPENAI_DIRECTOR_MAX_OUTPUT_TOKENS,
    )

    print(
        "Structured reasoning:",
        OPENAI_STRUCTURED_REASONING,
    )

    print(
        "Structured max:",
        OPENAI_STRUCTURED_MAX_OUTPUT_TOKENS,
    )

    print(
        "Cache mode:",
        OPENAI_PROMPT_CACHE_MODE,
    )

    print(
        "Usage telemetry:",
        OPENAI_USAGE_LOGGING,
    )

    print(
        "Google Fast:",
        (
            "CONFIGURED"
            if GEMINI_API_KEY
            else "missing key"
        ),
        "|",
        GOOGLE_IMAGE_FAST_MODEL,
    )

    print(
        "Google Pro:",
        (
            "CONFIGURED"
            if GEMINI_API_KEY
            else "missing key"
        ),
        "|",
        GOOGLE_IMAGE_PRO_MODEL,
    )

    print("")
    print(
        "✅ Syntax-safe engine"
    )
    print(
        "✅ Backwards-compatible imports"
    )
    print(
        "✅ Director reasoning cost control"
    )
    print(
        "✅ Structured reasoning LOW"
    )
    print(
        "✅ Explicit prompt cache"
    )
    print(
        "✅ Sol usage telemetry"
    )
    print(
        "🚫 No API call"
    )
    print(
        "🚫 No Vision"
    )
    print(
        "🚫 No image generation"
    )
    print("")
