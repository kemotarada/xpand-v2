# =========================================================
# XPAND SMART IMAGE ENGINE V1.3
#
# Production image engine for XPAND.
#
# IMAGE MODEL:
# - OpenAI GPT-Image-2
#
# VISUAL DIRECTOR / CRITIC:
# - OpenAI GPT-5.6 Sol
#
# OPTIONAL GOOGLE IMAGE MODELS:
# - Gemini 3 Pro Image / Nano Banana Pro
# - Gemini 3.1 Flash Image / Nano Banana 2
#
# IMPORTANT ARCHITECTURE:
#
# AUTO:
#   Smart single-model routing.
#
# FAST:
#   Nano Banana 2
#   -> fallback GPT-Image-2
#
# PRO:
#   Nano Banana Pro
#   -> GPT-Image-2 refinement
#
#   If Google fails:
#   GPT-Image-2 generation
#   -> GPT-Image-2 refinement
#
# BEST:
#   GPT-5.6 Sol art direction
#   -> Nano Banana Pro base generation
#   -> GPT-5.6 Sol visual critique
#   -> GPT-Image-2 final refinement
#
#   If Google quota/billing/rate-limit fails:
#
#   GPT-5.6 Sol art direction
#   -> GPT-Image-2 base generation
#   -> GPT-5.6 Sol visual critique
#   -> GPT-Image-2 final refinement
#
# COMPARE:
#   Separate generations from all available providers.
#
# Google is OPTIONAL.
# Google failure must NEVER stop XPAND if OpenAI works.
#
# No extra Python SDK required.
#
# Existing dependency:
# requests>=2.32.0,<3
# =========================================================

from __future__ import annotations

import base64
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


# =========================================================
# ENGINE
# =========================================================

ENGINE_NAME = "XPAND Smart Image Engine"

ENGINE_VERSION = "1.3"


# =========================================================
# API KEYS
# =========================================================

OPENAI_API_KEY = str(
    os.environ.get(
        "OPENAI_API_KEY",
        ""
    )
).strip()


GEMINI_API_KEY = str(
    os.environ.get(
        "GEMINI_API_KEY",
        ""
    )
).strip()


# =========================================================
# MODELS
# =========================================================

OPENAI_IMAGE_MODEL = str(
    os.environ.get(
        "XPAND_OPENAI_IMAGE_MODEL",
        "gpt-image-2"
    )
).strip()


OPENAI_DIRECTOR_MODEL = str(
    os.environ.get(
        "XPAND_OPENAI_DIRECTOR_MODEL",
        "gpt-5.6-sol"
    )
).strip()


GOOGLE_IMAGE_FAST_MODEL = str(
    os.environ.get(
        "XPAND_GOOGLE_IMAGE_MODEL",
        "gemini-3.1-flash-image"
    )
).strip()


GOOGLE_IMAGE_PRO_MODEL = str(
    os.environ.get(
        "XPAND_GOOGLE_IMAGE_PRO_MODEL",
        "gemini-3-pro-image"
    )
).strip()


# =========================================================
# DEFAULT SETTINGS
# =========================================================

DEFAULT_MODE = str(
    os.environ.get(
        "XPAND_IMAGE_MODE",
        "auto"
    )
).strip().lower()


DEFAULT_QUALITY = str(
    os.environ.get(
        "XPAND_IMAGE_DEFAULT_QUALITY",
        "high"
    )
).strip().lower()


OPENAI_DIRECTOR_REASONING = str(
    os.environ.get(
        "XPAND_IMAGE_DIRECTOR_REASONING",
        "high"
    )
).strip().lower()


REQUEST_TIMEOUT = max(
    30,
    int(
        os.environ.get(
            "XPAND_IMAGE_TIMEOUT_SECONDS",
            "300"
        )
        or
        300
    )
)


# =========================================================
# API ENDPOINTS
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
# SUPPORTED IMAGE SETTINGS
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
        Any
    ] = field(
        default_factory=dict
    )


    @property
    def extension(
        self
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
            self.mime_type.lower(),
            ".png"
        )


    @property
    def filename(
        self
    ) -> str:

        provider_name = (
            self.provider
            .replace(
                "_",
                "-"
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

    errors: List[
        str
    ] = field(
        default_factory=list
    )


# =========================================================
# TEXT HELPERS
# =========================================================

def clean_text(
    value: Any,
    max_length: int = 12000
) -> str:

    return (
        str(
            value
            if value is not None
            else ""
        )
        .replace(
            "\x00",
            ""
        )
        .strip()[:max_length]
    )


def normalize_arabic(
    value: Any
) -> str:

    text = clean_text(
        value,
        20000
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
            new
        )


    text = re.sub(
        r"[\u064B-\u065F]",
        "",
        text
    )


    text = re.sub(
        r"\s+",
        " ",
        text
    )


    return text.strip()


def contains_any(
    text: str,
    markers: Sequence[str]
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
    prompt: str
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
            prompt
        ):

            value = clean_text(
                match,
                1000
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


# =========================================================
# REQUEST UNDERSTANDING
# =========================================================

def detect_aspect_ratio(
    prompt: str,
    requested_aspect_ratio: str = ""
) -> str:

    explicit = clean_text(
        requested_aspect_ratio,
        20
    )


    if (
        explicit
        in
        SUPPORTED_ASPECT_RATIOS
    ):

        return explicit


    normalized = normalize_arabic(
        prompt
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

        if ratio in normalized:

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
            "phone wallpaper",
        ]
    ):

        return "9:16"


    if contains_any(
        prompt,
        [
            "بوست انستغرام",
            "instagram post",
            "مربع",
            "square",
        ]
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
        ]
    ):

        return "4:5"


    if contains_any(
        prompt,
        [
            "بانر",
            "banner",
            "يوتيوب",
            "youtube",
            "thumbnail",
            "ثامبنيل",
            "سينمائي عريض",
            "widescreen",
            "landscape",
            "افقي",
            "أفقي",
        ]
    ):

        return "16:9"


    if contains_any(
        prompt,
        [
            "بوستر",
            "poster",
            "portrait",
            "ملصق",
        ]
    ):

        return "2:3"


    return "1:1"


def detect_image_size(
    prompt: str,
    requested_size: str = ""
) -> str:

    explicit = clean_text(
        requested_size,
        20
    ).upper()


    aliases = {
        "0.5K":
            "512",

        "512PX":
            "512",

        "512":
            "512",

        "1K":
            "1K",

        "2K":
            "2K",

        "4K":
            "4K",
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
            "اعلى دقة",
            "أعلى دقة",
            "اعلى جوده",
            "أعلى جودة",
            "ultra high resolution",
            "print quality",
            "للطباعه",
            "للطباعة",
        ]
    ):

        return "4K"


    if contains_any(
        prompt,
        [
            "2k",
            "2 k",
            "تو كي",
            "دقه عاليه",
            "دقة عالية",
            "high quality",
        ]
    ):

        return "2K"


    return "1K"


def detect_quality(
    prompt: str,
    requested_quality: str = ""
) -> str:

    explicit = clean_text(
        requested_quality,
        20
    ).lower()


    if (
        explicit
        in
        SUPPORTED_OPENAI_QUALITIES
    ):

        return explicit


    if contains_any(
        prompt,
        [
            "سريع",
            "بسرعه",
            "بسرعة",
            "draft",
            "quick",
            "fast",
            "preview",
            "تجريبي",
        ]
    ):

        return "medium"


    return DEFAULT_QUALITY


# =========================================================
# PROMPT ENHANCEMENT
# =========================================================

def build_professional_prompt(
    user_prompt: str,
    aspect_ratio: str,
    image_size: str
) -> str:

    user_prompt = clean_text(
        user_prompt,
        10000
    )


    if not user_prompt:

        raise XPANDImageError(
            "وصف الصورة فاضي."
        )


    directives: List[str] = [
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


    if contains_any(
        user_prompt,
        [
            "واقعي",
            "واقعية",
            "realistic",
            "photorealistic",
            "تصوير",
            "product photography",
        ]
    ):

        directives.append(
            (
                "Use photorealistic commercial photography quality "
                "with realistic optical behavior and controlled "
                "professional lighting."
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
            "mockup",
        ]
    ):

        directives.extend(
            [
                (
                    "Treat the visual as premium product advertising."
                ),

                (
                    "Make the product the hero subject with clean "
                    "separation, refined reflections and premium "
                    "studio-grade materials."
                ),
            ]
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
            "فاخر",
            "فخم",
            "luxury",
            "premium",
            "high-end",
            "agency",
            "بوستر",
            "poster",
        ]
    ):

        directives.extend(
            [
                (
                    "Art direction should feel like a high-budget "
                    "international creative-agency campaign."
                ),

                (
                    "Use polished spacing and a deliberate hierarchy "
                    "appropriate for real advertising output."
                ),
            ]
        )


    if contains_any(
        user_prompt,
        [
            "سينمائي",
            "cinematic",
            "movie",
            "فيلم",
        ]
    ):

        directives.append(
            (
                "Use cinematic motivated lighting, controlled "
                "contrast, atmospheric depth and refined filmic "
                "color grading."
            )
        )


    quoted_texts = extract_quoted_text(
        user_prompt
    )


    if quoted_texts:

        exact_lines = "\n".join(
            f'- "{item}"'
            for item in quoted_texts
        )


        directives.append(
            (
                "Render the following quoted text exactly as written, "
                "without translation, rewriting or spelling changes:\n"
                +
                exact_lines
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
        +
        user_prompt
        +
        "\n\n"
        +
        "XPAND PROFESSIONAL ART DIRECTION:\n"
        +
        "\n".join(
            f"- {item}"
            for item in directives
        )
    )


# =========================================================
# GENERIC REFINEMENT PROMPT
# =========================================================

def build_refinement_prompt(
    original_user_prompt: str,
    *,
    stronger: bool = False,
    critique: str = ""
) -> str:

    directives = [
        (
            "Edit the provided image into a stronger final "
            "professional version."
        ),

        (
            "Preserve the core subject, concept, identity, "
            "composition intent and visual message."
        ),

        (
            "Do not replace the main product or subject with "
            "a different one."
        ),

        (
            "Improve realism, lighting, materials, edge quality, "
            "micro-detail, hierarchy, balance and premium finish."
        ),

        (
            "Fix visible artifacts and weak areas while preserving "
            "what already works."
        ),

        (
            "Do not add random objects, fake logos or watermarks."
        ),
    ]


    if stronger:

        directives.extend(
            [
                (
                    "Push the visual toward world-class campaign "
                    "quality suitable for a top creative agency."
                ),

                (
                    "Increase visual impact without making the image "
                    "busy or artificial."
                ),

                (
                    "Make typography cleaner and more legible if "
                    "the design contains requested text."
                ),
            ]
        )


    quoted_texts = extract_quoted_text(
        original_user_prompt
    )


    if quoted_texts:

        exact_lines = "\n".join(
            f'- "{item}"'
            for item in quoted_texts
        )


        directives.append(
            (
                "Preserve these requested text elements exactly:\n"
                +
                exact_lines
            )
        )


    if critique:

        directives.append(
            (
                "A senior visual director reviewed the current "
                "image. Apply these improvements where useful:\n"
                +
                clean_text(
                    critique,
                    5000
                )
            )
        )


    return (
        "ORIGINAL USER REQUEST:\n"
        +
        clean_text(
            original_user_prompt,
            10000
        )
        +
        "\n\n"
        +
        "FINAL REFINEMENT INSTRUCTIONS:\n"
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
    mode: str
) -> str:

    value = clean_text(
        mode,
        50
    ).lower()


    aliases = {
        "auto":
            MODE_AUTO,

        "smart":
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

        "nano banana 2":
            MODE_GOOGLE_FAST,

        "nano-banana-2":
            MODE_GOOGLE_FAST,

        "google_pro":
            MODE_GOOGLE_PRO,

        "google-pro":
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
        MODE_AUTO
    )


# =========================================================
# SMART MODE SELECTION
# =========================================================

def resolve_effective_mode(
    prompt: str,
    mode: str = "",
    reference_count: int = 0
) -> str:

    chosen = normalize_mode(
        mode
        or
        DEFAULT_MODE
    )


    if chosen != MODE_AUTO:

        return chosen


    if contains_any(
        prompt,
        [
            "افضل نتيجه ممكنه",
            "أفضل نتيجة ممكنة",
            "اقوى نتيجه",
            "أقوى نتيجة",
            "كل قواك",
            "all your power",
            "best mode",
            "ultimate",
            "max quality",
            "اعلى مستوى ممكن",
            "أعلى مستوى ممكن",
        ]
    ):

        return MODE_BEST


    if contains_any(
        prompt,
        [
            "سريع",
            "بسرعه",
            "بسرعة",
            "quick",
            "fast",
            "draft",
            "preview",
        ]
    ):

        return MODE_FAST


    professional = contains_any(
        prompt,
        [
            "احترافي جدا",
            "احترافي جداً",
            "احترافي",
            "premium",
            "luxury",
            "فاخر",
            "فخم",
            "agency",
            "campaign",
            "اعلان عالمي",
            "إعلان عالمي",
            "high-end",
            "commercial",
        ]
    )


    product_brand = contains_any(
        prompt,
        [
            "منتج",
            "product",
            "عطر",
            "perfume",
            "ساعة",
            "watch",
            "عبوة",
            "عبوه",
            "packaging",
            "branding",
            "brand",
            "بوستر",
            "poster",
            "اعلان",
            "إعلان",
        ]
    )


    precision = contains_any(
        prompt,
        [
            "اكتب",
            "النص التالي",
            "typography",
            "headline",
            "exact",
            "high fidelity",
            "حافظ على",
            "بدقة",
            "دقيق",
        ]
    )


    if (
        professional
        and
        product_brand
    ):

        return MODE_PRO


    if precision:

        return MODE_OPENAI


    if (
        reference_count >= 2
        and
        product_brand
    ):

        return MODE_PRO


    if professional:

        return MODE_GOOGLE_PRO


    return MODE_OPENAI


# =========================================================
# ROUTE BUILDER
# =========================================================

def build_route(
    provider: str,
    model: str,
    reason: str,
    aspect_ratio: str,
    image_size: str,
    quality: str
) -> ImageRoute:

    return ImageRoute(
        provider=
            provider,

        model=
            model,

        reason=
            reason,

        aspect_ratio=
            aspect_ratio,

        image_size=
            image_size,

        quality=
            quality,
    )


# =========================================================
# OPENAI SIZE MAPPING
# =========================================================

def openai_size_for_ratio(
    aspect_ratio: str
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
    response: requests.Response
) -> Dict[
    str,
    Any
]:

    try:

        value = response.json()


        if isinstance(
            value,
            dict
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
                    response.text,
                    5000
                )
        }


def _provider_error_message(
    provider: str,
    response: requests.Response
) -> str:

    data = _safe_json(
        response
    )


    error = data.get(
        "error"
    )


    if isinstance(
        error,
        dict
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
                f"HTTP "
                f"{response.status_code}"
            )
        )


    return (
        f"{provider}: "
        +
        clean_text(
            message,
            4000
        )
    )


# =========================================================
# GOOGLE ERROR CLASSIFICATION
# =========================================================

def looks_like_google_quota_error(
    error: Any
) -> bool:

    text = normalize_arabic(
        str(
            error
        )
    )


    markers = [
        "quota",
        "rate limit",
        "rate_limit",
        "billing",
        "free tier",
        "free_tier",
        "resource exhausted",
        "resource_exhausted",
        "429",
        "exceeded",
    ]


    return any(
        normalize_arabic(
            item
        )
        in text
        for item in markers
    )


# =========================================================
# IMAGE RESPONSE EXTRACTION
# =========================================================

def _download_image_url(
    url: str
) -> Tuple[
    bytes,
    str
]:

    response = requests.get(
        url,
        timeout=
            REQUEST_TIMEOUT
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
            ""
        ),
        100
    ).split(
        ";"
    )[0]


    if not mime_type.startswith(
        "image/"
    ):

        mime_type = "image/png"


    return (
        response.content,
        mime_type
    )


def _decode_base64_image(
    data: str
) -> Optional[bytes]:

    value = clean_text(
        data,
        100000000
    )


    if not value:

        return None


    if value.startswith(
        "data:image/"
    ):

        try:

            value = value.split(
                ",",
                1
            )[1]


        except Exception:

            return None


    try:

        raw = base64.b64decode(
            value
        )


        if not raw:

            return None


        return raw


    except Exception:

        return None


def _find_inline_images(
    value: Any
) -> List[
    Tuple[
        bytes,
        str
    ]
]:

    found: List[
        Tuple[
            bytes,
            str
        ]
    ] = []


    def walk(
        item: Any
    ) -> None:

        if isinstance(
            item,
            dict
        ):

            item_type = clean_text(
                item.get(
                    "type"
                ),
                100
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
                    ""
                ),
                100
            ).lower()


            possible_data = [
                item.get(
                    "data"
                ),

                item.get(
                    "b64_json"
                ),

                item.get(
                    "base64"
                ),
            ]


            looks_like_image = (
                item_type
                ==
                "image"
                or
                mime_type.startswith(
                    "image/"
                )
                or
                (
                    "b64_json"
                    in item
                )
            )


            if looks_like_image:

                for possible in possible_data:

                    if isinstance(
                        possible,
                        str
                    ):

                        raw = _decode_base64_image(
                            possible
                        )


                        if raw:

                            found.append(
                                (
                                    raw,
                                    (
                                        mime_type
                                        or
                                        "image/png"
                                    )
                                )
                            )


                            break


                uri = (
                    item.get(
                        "uri"
                    )
                    or
                    item.get(
                        "url"
                    )
                )


                if (
                    isinstance(
                        uri,
                        str
                    )
                    and
                    uri.startswith(
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
            list
        ):

            for child in item:

                walk(
                    child
                )


    walk(
        value
    )


    unique: List[
        Tuple[
            bytes,
            str
        ]
    ] = []


    signatures = set()


    for image_bytes, mime_type in found:

        signature = (
            len(
                image_bytes
            ),
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
                mime_type
            )
        )


    return unique


# =========================================================
# OPENAI RESPONSE TEXT EXTRACTION
# =========================================================

def _extract_openai_response_text(
    data: Dict[
        str,
        Any
    ]
) -> str:

    top_level = data.get(
        "output_text"
    )


    if isinstance(
        top_level,
        str
    ):

        return clean_text(
            top_level,
            12000
        )


    collected: List[str] = []


    output = data.get(
        "output",
        []
    )


    if isinstance(
        output,
        list
    ):

        for item in output:

            if not isinstance(
                item,
                dict
            ):

                continue


            content = item.get(
                "content",
                []
            )


            if not isinstance(
                content,
                list
            ):

                continue


            for part in content:

                if not isinstance(
                    part,
                    dict
                ):

                    continue


                if (
                    part.get(
                        "type"
                    )
                    ==
                    "output_text"
                    and
                    isinstance(
                        part.get(
                            "text"
                        ),
                        str
                    )
                ):

                    collected.append(
                        part[
                            "text"
                        ]
                    )


    return clean_text(
        "\n".join(
            collected
        ),
        12000
    )


# =========================================================
# IMAGE -> DATA URI
# =========================================================

def image_data_uri(
    image_bytes: bytes,
    mime_type: str
) -> str:

    mime = clean_text(
        mime_type,
        100
    ).lower()


    if mime not in {
        "image/png",
        "image/jpeg",
        "image/jpg",
    }:

        mime = "image/png"


    encoded = base64.b64encode(
        image_bytes
    ).decode(
        "ascii"
    )


    return (
        "data:"
        +
        mime
        +
        ";base64,"
        +
        encoded
    )


# =========================================================
# GPT-5.6 SOL TEXT / VISION
# =========================================================

def call_openai_director(
    prompt: str,
    *,
    image_bytes: Optional[bytes] = None,
    image_mime_type: str = "image/png"
) -> str:

    if not OPENAI_API_KEY:

        raise XPANDImageConfigurationError(
            "OPENAI_API_KEY مش موجود."
        )


    content: List[
        Dict[
            str,
            Any
        ]
    ] = [
        {
            "type":
                "input_text",

            "text":
                clean_text(
                    prompt,
                    16000
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
                        image_mime_type
                    ),

                "detail":
                    "high",
            }
        )


    payload = {
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
                OPENAI_DIRECTOR_REASONING,
        },

        "max_output_tokens":
            2200,
    }


    response = requests.post(
        OPENAI_RESPONSES_URL,

        headers={
            "Authorization":
                f"Bearer {OPENAI_API_KEY}",

            "Content-Type":
                "application/json",
        },

        json=
            payload,

        timeout=
            REQUEST_TIMEOUT
    )


    if not response.ok:

        raise XPANDImageProviderError(
            _provider_error_message(
                "GPT-5.6 Sol",
                response
            )
        )


    data = _safe_json(
        response
    )


    text = _extract_openai_response_text(
        data
    )


    if not text:

        raise XPANDImageProviderError(
            "GPT-5.6 Sol رجع بدون نص."
        )


    return text


# =========================================================
# GPT-5.6 SOL ART DIRECTOR
# =========================================================

def build_sol_art_direction(
    original_prompt: str,
    aspect_ratio: str,
    image_size: str
) -> str:

    request = f"""
You are the senior visual art director for XPAND Creative Agency.

Your task is NOT to generate the image.

Create a concise but highly professional visual direction that will be
passed to an image-generation model.

Original user request:

{original_prompt}

Target aspect ratio:
{aspect_ratio}

Requested resolution intent:
{image_size}

Analyze and improve:

- composition
- camera angle
- focal hierarchy
- lighting
- material realism
- color palette
- depth
- product presentation
- typography placement if applicable
- negative space
- commercial impact
- premium finish

Important:

Preserve the user's exact intent.
Do not invent unrelated products or brands.
If quoted text exists, preserve it exactly.
Do not change the requested aspect ratio.
Keep your output useful as an image-generation instruction.
Do not explain your reasoning.
Return only the final art-direction brief.
""".strip()


    return call_openai_director(
        request
    )


# =========================================================
# GPT-5.6 SOL VISUAL CRITIC
# =========================================================

def build_sol_visual_critique(
    original_prompt: str,
    image_bytes: bytes,
    mime_type: str
) -> str:

    request = f"""
You are the final senior visual reviewer for XPAND Creative Agency.

Review the attached generated image against the ORIGINAL request below.

ORIGINAL REQUEST:

{original_prompt}

Your job is to identify only meaningful improvements for a FINAL image edit.

Evaluate:

- whether the main subject/product matches the request
- composition and hierarchy
- professional advertising quality
- lighting realism
- material realism
- reflections and shadows
- typography accuracy and legibility
- unwanted artifacts
- unnecessary objects
- premium brand feel
- visual balance
- commercial readiness

Important:

Do NOT request a complete redesign if the current image is already strong.
Preserve strong parts.
Preserve the main product identity.
Do not invent a different product.
Do not add random text.
Be precise and actionable.
Return only a concise final-edit instruction list.
""".strip()


    return call_openai_director(
        request,
        image_bytes=
            image_bytes,
        image_mime_type=
            mime_type
    )


# =========================================================
# OPENAI GPT-IMAGE-2 GENERATION
# =========================================================

def generate_with_openai(
    prompt: str,
    original_prompt: str,
    route: ImageRoute,
    number: int = 1
) -> List[
    GeneratedImage
]:

    if not OPENAI_API_KEY:

        raise XPANDImageConfigurationError(
            "OPENAI_API_KEY مش موجود على Railway."
        )


    number = max(
        1,
        min(
            int(
                number
                or
                1
            ),
            4
        )
    )


    provider_size = openai_size_for_ratio(
        route.aspect_ratio
    )


    quality = (
        route.quality
        if
        route.quality
        in
        SUPPORTED_OPENAI_QUALITIES
        else
        "high"
    )


    payload: Dict[
        str,
        Any
    ] = {
        "model":
            route.model,

        "prompt":
            prompt,

        "n":
            number,

        "size":
            provider_size,

        "quality":
            quality,
    }


    response = requests.post(
        OPENAI_IMAGE_GENERATION_URL,

        headers={
            "Authorization":
                f"Bearer {OPENAI_API_KEY}",

            "Content-Type":
                "application/json",
        },

        json=
            payload,

        timeout=
            REQUEST_TIMEOUT
    )


    if not response.ok:

        raise XPANDImageProviderError(
            _provider_error_message(
                "GPT-Image-2",
                response
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
                "GPT-Image-2 رجع استجابة ناجحة "
                "لكن ما لقيت صورة."
            )
        )


    request_id = clean_text(
        response.headers.get(
            "x-request-id",
            ""
        ),
        200
    )


    results: List[
        GeneratedImage
    ] = []


    for index, (
        image_bytes,
        mime_type
    ) in enumerate(
        images[:number]
    ):

        unique_request_id = (
            request_id
            or
            (
                "oa-"
                +
                uuid.uuid4().hex[:12]
            )
        )


        if number > 1:

            unique_request_id += (
                "-"
                +
                str(
                    index + 1
                )
            )


        results.append(
            GeneratedImage(
                image_bytes=
                    image_bytes,

                mime_type=
                    mime_type
                    or
                    "image/png",

                provider=
                    PROVIDER_OPENAI,

                model=
                    route.model,

                prompt=
                    prompt,

                original_prompt=
                    original_prompt,

                aspect_ratio=
                    route.aspect_ratio,

                image_size=
                    provider_size,

                quality=
                    quality,

                route_reason=
                    route.reason,

                request_id=
                    unique_request_id,

                metadata={
                    "generation_type":
                        "openai_generation",

                    "requested_image_size":
                        route.image_size,

                    "provider_size":
                        provider_size,
                },
            )
        )


    return results


# =========================================================
# OPENAI GPT-IMAGE-2 EDIT
#
# IMPORTANT:
# Single-image edit uses multipart field:
#
# image
#
# NOT image[]
# =========================================================

def edit_with_openai(
    input_image_bytes: bytes,
    input_mime_type: str,
    prompt: str,
    original_prompt: str,
    route: ImageRoute,
    *,
    final_provider: str,
    final_model_label: str,
    metadata: Optional[
        Dict[
            str,
            Any
        ]
    ] = None
) -> GeneratedImage:

    if not OPENAI_API_KEY:

        raise XPANDImageConfigurationError(
            "OPENAI_API_KEY مش موجود."
        )


    provider_size = openai_size_for_ratio(
        route.aspect_ratio
    )


    quality = (
        route.quality
        if
        route.quality
        in
        SUPPORTED_OPENAI_QUALITIES
        else
        "high"
    )


    mime_type = clean_text(
        input_mime_type,
        100
    )


    if not mime_type.startswith(
        "image/"
    ):

        mime_type = "image/png"


    extension = (
        ".jpg"
        if
        mime_type
        in {
            "image/jpeg",
            "image/jpg",
        }
        else
        ".png"
    )


    files = {
        "image": (
            "xpand-input"
            +
            extension,

            input_image_bytes,

            mime_type,
        )
    }


    data = {
        "model":
            route.model,

        "prompt":
            prompt,

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
                f"Bearer {OPENAI_API_KEY}",
        },

        data=
            data,

        files=
            files,

        timeout=
            REQUEST_TIMEOUT
    )


    if not response.ok:

        raise XPANDImageProviderError(
            _provider_error_message(
                "GPT-Image-2 Edit",
                response
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
                "GPT-Image-2 Edit نجح كطلب "
                "لكن ما رجعت صورة."
            )
        )


    image_bytes, output_mime_type = (
        images[0]
    )


    request_id = clean_text(
        response.headers.get(
            "x-request-id",
            ""
        ),
        200
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
        "final_edit_model"
    ] = OPENAI_IMAGE_MODEL


    final_metadata[
        "final_edit_provider_size"
    ] = provider_size


    final_metadata[
        "generation_type"
    ] = "final_refinement"


    return GeneratedImage(
        image_bytes=
            image_bytes,

        mime_type=
            output_mime_type
            or
            "image/png",

        provider=
            final_provider,

        model=
            final_model_label,

        prompt=
            prompt,

        original_prompt=
            original_prompt,

        aspect_ratio=
            route.aspect_ratio,

        image_size=
            provider_size,

        quality=
            quality,

        route_reason=
            (
                "Final image refinement completed "
                "with GPT-Image-2."
            ),

        request_id=
            request_id,

        metadata=
            final_metadata,
    )


# =========================================================
# GEMINI IMAGE GENERATION
# =========================================================

def _generate_one_with_gemini(
    prompt: str,
    original_prompt: str,
    route: ImageRoute,
    index: int = 0
) -> GeneratedImage:

    if not GEMINI_API_KEY:

        raise XPANDImageConfigurationError(
            "GEMINI_API_KEY مش موجود."
        )


    image_size = (
        route.image_size
        if
        route.image_size
        in
        SUPPORTED_GOOGLE_IMAGE_SIZES
        else
        "1K"
    )


    payload = {
        "model":
            route.model,

        "input":
            prompt,

        "response_format": {
            "type":
                "image",

            "aspect_ratio":
                route.aspect_ratio,

            "image_size":
                image_size,

            "mime_type":
                "image/jpeg",
        },
    }


    response = requests.post(
        GEMINI_INTERACTIONS_URL,

        headers={
            "x-goog-api-key":
                GEMINI_API_KEY,

            "Content-Type":
                "application/json",
        },

        json=
            payload,

        timeout=
            REQUEST_TIMEOUT
    )


    if not response.ok:

        raise XPANDImageProviderError(
            _provider_error_message(
                "Gemini",
                response
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
                "لكن ما لقيت output image."
            )
        )


    image_bytes, mime_type = (
        images[0]
    )


    request_id = clean_text(
        data.get(
            "id"
        ),
        200
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
        image_bytes=
            image_bytes,

        mime_type=
            mime_type
            or
            "image/jpeg",

        provider=
            route.provider,

        model=
            route.model,

        prompt=
            prompt,

        original_prompt=
            original_prompt,

        aspect_ratio=
            route.aspect_ratio,

        image_size=
            image_size,

        quality=
            route.quality,

        route_reason=
            route.reason,

        request_id=
            request_id,

        metadata={
            "generation_type":
                "gemini_generation",

            "google_model":
                route.model,

            "google_image_size":
                image_size,
        },
    )


def generate_with_gemini(
    prompt: str,
    original_prompt: str,
    route: ImageRoute,
    number: int = 1
) -> List[
    GeneratedImage
]:

    number = max(
        1,
        min(
            int(
                number
                or
                1
            ),
            4
        )
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
                    prompt=
                        prompt,

                    original_prompt=
                        original_prompt,

                    route=
                        route,

                    index=
                        index
                )
            )


        except Exception as error:

            errors.append(
                clean_text(
                    error,
                    4000
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
# OPENAI-ONLY BEST FALLBACK
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
    ] = None
) -> ImageGenerationResponse:

    started = time.monotonic()


    errors = list(
        inherited_errors
        or
        []
    )


    print(
        "🔁 XPAND FALLBACK: OPENAI FUSION"
    )


    # -----------------------------------------------------
    # STAGE 1
    # GPT-5.6 SOL ART DIRECTOR
    # -----------------------------------------------------

    art_direction = clean_text(
        initial_art_direction,
        12000
    )


    if not art_direction:

        try:

            print(
                "🎨 Stage 1: GPT-5.6 Sol Art Director..."
            )


            art_direction = (
                build_sol_art_direction(
                    original_prompt,
                    aspect_ratio,
                    image_size
                )
            )


            print(
                "✅ Stage 1: GPT-5.6 Sol Art Director"
            )


        except Exception as error:

            errors.append(
                (
                    "GPT-5.6 Sol art director: "
                    +
                    clean_text(
                        error,
                        4000
                    )
                )
            )


            art_direction = (
                build_professional_prompt(
                    original_prompt,
                    aspect_ratio,
                    image_size
                )
            )


            print(
                "⚠️ Art Director unavailable; using XPAND prompt enhancer"
            )


    else:

        print(
            "✅ Stage 1: Existing GPT-5.6 Sol art direction"
        )


    # -----------------------------------------------------
    # STAGE 2
    # GPT-IMAGE-2 BASE GENERATION
    # -----------------------------------------------------

    print(
        "🖼️ Stage 2: GPT-Image-2 base generation..."
    )


    generation_route = build_route(
        PROVIDER_OPENAI,
        OPENAI_IMAGE_MODEL,
        (
            "OpenAI Fusion base generation."
        ),
        aspect_ratio,
        image_size,
        quality
    )


    base_prompt = (
        "ORIGINAL REQUEST:\n"
        +
        original_prompt
        +
        "\n\n"
        +
        "SENIOR ART DIRECTION:\n"
        +
        art_direction
    )


    base_images = generate_with_openai(
        prompt=
            base_prompt,

        original_prompt=
            original_prompt,

        route=
            generation_route,

        number=
            number
    )


    print(
        "✅ Stage 2: GPT-Image-2 base generation"
    )


    final_images: List[
        GeneratedImage
    ] = []


    # -----------------------------------------------------
    # STAGE 3 + 4 PER IMAGE
    # -----------------------------------------------------

    for index, base_image in enumerate(
        base_images,
        start=1
    ):

        critique = ""


        try:

            print(
                (
                    "👁️ Stage 3: GPT-5.6 Sol visual critique "
                    +
                    str(
                        index
                    )
                    +
                    "/"
                    +
                    str(
                        len(
                            base_images
                        )
                    )
                    +
                    "..."
                )
            )


            critique = (
                build_sol_visual_critique(
                    original_prompt,
                    base_image.image_bytes,
                    base_image.mime_type
                )
            )


            print(
                "✅ Stage 3: GPT-5.6 Sol visual critique"
            )


        except Exception as error:

            errors.append(
                (
                    "GPT-5.6 Sol visual critique: "
                    +
                    clean_text(
                        error,
                        4000
                    )
                )
            )


            print(
                "⚠️ Visual critic unavailable; using generic refinement"
            )


        refine_prompt = build_refinement_prompt(
            original_prompt,
            stronger=
                stronger,
            critique=
                critique
        )


        try:

            print(
                (
                    "✨ Stage 4: GPT-Image-2 final refinement "
                    +
                    str(
                        index
                    )
                    +
                    "/"
                    +
                    str(
                        len(
                            base_images
                        )
                    )
                    +
                    "..."
                )
            )


            final_image = edit_with_openai(
                input_image_bytes=
                    base_image.image_bytes,

                input_mime_type=
                    base_image.mime_type,

                prompt=
                    refine_prompt,

                original_prompt=
                    original_prompt,

                route=
                    generation_route,

                final_provider=
                    PROVIDER_OPENAI_FUSION,

                final_model_label=
                    (
                        "GPT-5.6 Sol → GPT-Image-2 → "
                        "GPT-5.6 Sol → GPT-Image-2"
                    ),

                metadata={
                    "pipeline":
                        "openai_fusion",

                    "art_director_model":
                        OPENAI_DIRECTOR_MODEL,

                    "base_model":
                        OPENAI_IMAGE_MODEL,

                    "critic_model":
                        OPENAI_DIRECTOR_MODEL,

                    "final_model":
                        OPENAI_IMAGE_MODEL,

                    "base_request_id":
                        base_image.request_id,

                    "google_used":
                        False,
                }
            )


            final_images.append(
                final_image
            )


            print(
                "✅ Stage 4: GPT-Image-2 final refinement"
            )


        except Exception as error:

            errors.append(
                (
                    "GPT-Image-2 final refinement: "
                    +
                    clean_text(
                        error,
                        4000
                    )
                )
            )


            #
            # Never lose a successful base image.
            #
            base_image.provider = (
                PROVIDER_OPENAI_FUSION
            )


            base_image.model = (
                "GPT-5.6 Sol → GPT-Image-2"
            )


            base_image.route_reason = (
                "OpenAI Fusion base image returned because "
                "final refinement failed."
            )


            base_image.metadata[
                "pipeline"
            ] = "openai_fusion_partial"


            base_image.metadata[
                "final_refinement_failed"
            ] = True


            final_images.append(
                base_image
            )


            print(
                "⚠️ Final edit failed; returning successful base image"
            )


    elapsed = round(
        time.monotonic()
        -
        started,
        3
    )


    if not final_images:

        raise XPANDImageProviderError(
            "OpenAI Fusion لم يرجع أي صورة."
        )


    print(
        "✅ OPENAI FUSION COMPLETE"
    )


    return ImageGenerationResponse(
        ok=
            True,

        images=
            final_images,

        selected_route=
            MODE_BEST
            if stronger
            else
            MODE_PRO,

        routes=[
            generation_route
        ],

        original_prompt=
            original_prompt,

        enhanced_prompt=
            art_direction,

        elapsed_seconds=
            elapsed,

        errors=
            errors,
    )


# =========================================================
# GOOGLE + OPENAI FUSION
# =========================================================

def run_google_openai_fusion(
    original_prompt: str,
    *,
    aspect_ratio: str,
    image_size: str,
    quality: str,
    number: int = 1,
    stronger: bool = False
) -> ImageGenerationResponse:

    started = time.monotonic()


    errors: List[str] = []


    art_direction = ""


    # -----------------------------------------------------
    # BEST ONLY:
    # SOL PRE-DIRECTS THE GOOGLE GENERATION
    # -----------------------------------------------------

    if stronger:

        try:

            print(
                "🎨 Stage 1: GPT-5.6 Sol Art Director..."
            )


            art_direction = (
                build_sol_art_direction(
                    original_prompt,
                    aspect_ratio,
                    image_size
                )
            )


            print(
                "✅ Stage 1: GPT-5.6 Sol Art Director"
            )


        except Exception as error:

            errors.append(
                (
                    "GPT-5.6 Sol art director: "
                    +
                    clean_text(
                        error,
                        4000
                    )
                )
            )


    if not art_direction:

        art_direction = (
            build_professional_prompt(
                original_prompt,
                aspect_ratio,
                image_size
            )
        )


    # -----------------------------------------------------
    # GOOGLE STAGE
    # -----------------------------------------------------

    google_route = build_route(
        PROVIDER_GOOGLE_PRO,
        GOOGLE_IMAGE_PRO_MODEL,
        (
            "Fusion base: Nano Banana Pro."
        ),
        aspect_ratio,
        image_size,
        quality
    )


    google_prompt = (
        "ORIGINAL REQUEST:\n"
        +
        original_prompt
        +
        "\n\n"
        +
        "XPAND ART DIRECTION:\n"
        +
        art_direction
    )


    try:

        print(
            "🍌 Stage 2: Nano Banana Pro base generation..."
        )


        base_images = generate_with_gemini(
            prompt=
                google_prompt,

            original_prompt=
                original_prompt,

            route=
                google_route,

            number=
                number
        )


        print(
            "✅ Stage 2: Nano Banana Pro"
        )


    except Exception as google_error:

        google_error_text = clean_text(
            google_error,
            5000
        )


        errors.append(
            (
                "Nano Banana Pro: "
                +
                google_error_text
            )
        )


        if looks_like_google_quota_error(
            google_error
        ):

            print(
                "⚠️ Google quota/billing unavailable"
            )


        else:

            print(
                "⚠️ Google image generation unavailable"
            )


        print(
            "➡️ Switching automatically to OpenAI Fusion"
        )


        return run_openai_fusion(
            original_prompt,
            aspect_ratio=
                aspect_ratio,
            image_size=
                image_size,
            quality=
                quality,
            number=
                number,
            stronger=
                stronger,
            initial_art_direction=
                art_direction,
            inherited_errors=
                errors
        )


    # -----------------------------------------------------
    # CRITIQUE + OPENAI FINAL EDIT
    # -----------------------------------------------------

    final_images: List[
        GeneratedImage
    ] = []


    openai_route = build_route(
        PROVIDER_OPENAI,
        OPENAI_IMAGE_MODEL,
        (
            "Fusion final refinement."
        ),
        aspect_ratio,
        image_size,
        quality
    )


    for index, base_image in enumerate(
        base_images,
        start=1
    ):

        critique = ""


        if stronger:

            try:

                print(
                    (
                        "👁️ Stage 3: GPT-5.6 Sol critique "
                        +
                        str(
                            index
                        )
                        +
                        "/"
                        +
                        str(
                            len(
                                base_images
                            )
                        )
                        +
                        "..."
                    )
                )


                critique = (
                    build_sol_visual_critique(
                        original_prompt,
                        base_image.image_bytes,
                        base_image.mime_type
                    )
                )


                print(
                    "✅ Stage 3: GPT-5.6 Sol visual critique"
                )


            except Exception as error:

                errors.append(
                    (
                        "GPT-5.6 Sol critique: "
                        +
                        clean_text(
                            error,
                            4000
                        )
                    )
                )


        refine_prompt = build_refinement_prompt(
            original_prompt,
            stronger=
                stronger,
            critique=
                critique
        )


        try:

            print(
                (
                    "✨ Final Stage: GPT-Image-2 refinement "
                    +
                    str(
                        index
                    )
                    +
                    "/"
                    +
                    str(
                        len(
                            base_images
                        )
                    )
                    +
                    "..."
                )
            )


            final_image = edit_with_openai(
                input_image_bytes=
                    base_image.image_bytes,

                input_mime_type=
                    base_image.mime_type,

                prompt=
                    refine_prompt,

                original_prompt=
                    original_prompt,

                route=
                    openai_route,

                final_provider=
                    (
                        PROVIDER_FUSION_BEST
                        if stronger
                        else
                        PROVIDER_FUSION_PRO
                    ),

                final_model_label=
                    (
                        "GPT-5.6 Sol → Nano Banana Pro → "
                        "GPT-5.6 Sol → GPT-Image-2"
                        if stronger
                        else
                        "Nano Banana Pro → GPT-Image-2"
                    ),

                metadata={
                    "pipeline":
                        (
                            "google_openai_best_fusion"
                            if stronger
                            else
                            "google_openai_pro_fusion"
                        ),

                    "art_director_model":
                        (
                            OPENAI_DIRECTOR_MODEL
                            if stronger
                            else
                            None
                        ),

                    "base_model":
                        GOOGLE_IMAGE_PRO_MODEL,

                    "critic_model":
                        (
                            OPENAI_DIRECTOR_MODEL
                            if stronger
                            else
                            None
                        ),

                    "final_model":
                        OPENAI_IMAGE_MODEL,

                    "google_used":
                        True,

                    "google_base_request_id":
                        base_image.request_id,
                }
            )


            final_images.append(
                final_image
            )


            print(
                "✅ Final Stage: GPT-Image-2 refinement"
            )


        except Exception as error:

            errors.append(
                (
                    "GPT-Image-2 final refinement: "
                    +
                    clean_text(
                        error,
                        4000
                    )
                )
            )


            #
            # Return the successful Google image
            # instead of failing the whole request.
            #
            base_image.provider = (
                PROVIDER_FUSION_BEST
                if stronger
                else
                PROVIDER_FUSION_PRO
            )


            base_image.model = (
                (
                    "GPT-5.6 Sol → Nano Banana Pro"
                    if stronger
                    else
                    "Nano Banana Pro"
                )
            )


            base_image.metadata[
                "final_refinement_failed"
            ] = True


            final_images.append(
                base_image
            )


    elapsed = round(
        time.monotonic()
        -
        started,
        3
    )


    if not final_images:

        raise XPANDImageProviderError(
            "Fusion pipeline لم يرجع صورة."
        )


    print(
        (
            "✅ FUSION BEST COMPLETE"
            if stronger
            else
            "✅ FUSION PRO COMPLETE"
        )
    )


    return ImageGenerationResponse(
        ok=
            True,

        images=
            final_images,

        selected_route=
            (
                MODE_BEST
                if stronger
                else
                MODE_PRO
            ),

        routes=[
            google_route,
            openai_route,
        ],

        original_prompt=
            original_prompt,

        enhanced_prompt=
            art_direction,

        elapsed_seconds=
            elapsed,

        errors=
            errors,
    )


# =========================================================
# DIRECT OPENAI ROUTE
# =========================================================

def run_openai_direct(
    original_prompt: str,
    *,
    aspect_ratio: str,
    image_size: str,
    quality: str,
    number: int = 1
) -> ImageGenerationResponse:

    started = time.monotonic()


    route = build_route(
        PROVIDER_OPENAI,
        OPENAI_IMAGE_MODEL,
        (
            "Direct GPT-Image-2 generation."
        ),
        aspect_ratio,
        image_size,
        quality
    )


    enhanced = build_professional_prompt(
        original_prompt,
        aspect_ratio,
        image_size
    )


    images = generate_with_openai(
        prompt=
            enhanced,

        original_prompt=
            original_prompt,

        route=
            route,

        number=
            number
    )


    return ImageGenerationResponse(
        ok=
            True,

        images=
            images,

        selected_route=
            MODE_OPENAI,

        routes=[
            route
        ],

        original_prompt=
            original_prompt,

        enhanced_prompt=
            enhanced,

        elapsed_seconds=
            round(
                time.monotonic()
                -
                started,
                3
            ),

        errors=[],
    )


# =========================================================
# DIRECT GOOGLE ROUTE WITH OPENAI FALLBACK
# =========================================================

def run_google_direct(
    original_prompt: str,
    *,
    pro: bool,
    aspect_ratio: str,
    image_size: str,
    quality: str,
    number: int = 1
) -> ImageGenerationResponse:

    started = time.monotonic()


    route = build_route(
        (
            PROVIDER_GOOGLE_PRO
            if pro
            else
            PROVIDER_GOOGLE_FAST
        ),
        (
            GOOGLE_IMAGE_PRO_MODEL
            if pro
            else
            GOOGLE_IMAGE_FAST_MODEL
        ),
        (
            "Direct Nano Banana Pro generation."
            if pro
            else
            "Direct Nano Banana 2 generation."
        ),
        aspect_ratio,
        image_size,
        quality
    )


    enhanced = build_professional_prompt(
        original_prompt,
        aspect_ratio,
        image_size
    )


    try:

        images = generate_with_gemini(
            prompt=
                enhanced,

            original_prompt=
                original_prompt,

            route=
                route,

            number=
                number
        )


        return ImageGenerationResponse(
            ok=
                True,

            images=
                images,

            selected_route=
                (
                    MODE_GOOGLE_PRO
                    if pro
                    else
                    MODE_GOOGLE_FAST
                ),

            routes=[
                route
            ],

            original_prompt=
                original_prompt,

            enhanced_prompt=
                enhanced,

            elapsed_seconds=
                round(
                    time.monotonic()
                    -
                    started,
                    3
                ),

            errors=[],
        )


    except Exception as google_error:

        print(
            "⚠️ Google direct route failed → GPT-Image-2 fallback"
        )


        result = run_openai_direct(
            original_prompt,
            aspect_ratio=
                aspect_ratio,
            image_size=
                image_size,
            quality=
                quality,
            number=
                number
        )


        result.errors.append(
            (
                "Google fallback: "
                +
                clean_text(
                    google_error,
                    4000
                )
            )
        )


        return result


# =========================================================
# COMPARE MODE
# =========================================================

def run_compare(
    original_prompt: str,
    *,
    aspect_ratio: str,
    image_size: str,
    quality: str,
    number: int = 3
) -> ImageGenerationResponse:

    started = time.monotonic()


    enhanced = build_professional_prompt(
        original_prompt,
        aspect_ratio,
        image_size
    )


    routes = [
        build_route(
            PROVIDER_OPENAI,
            OPENAI_IMAGE_MODEL,
            "COMPARE: GPT-Image-2",
            aspect_ratio,
            image_size,
            quality
        ),

        build_route(
            PROVIDER_GOOGLE_PRO,
            GOOGLE_IMAGE_PRO_MODEL,
            "COMPARE: Nano Banana Pro",
            aspect_ratio,
            image_size,
            quality
        ),

        build_route(
            PROVIDER_GOOGLE_FAST,
            GOOGLE_IMAGE_FAST_MODEL,
            "COMPARE: Nano Banana 2",
            aspect_ratio,
            image_size,
            quality
        ),
    ]


    target = max(
        3,
        int(
            number
            or
            3
        )
    )


    counts = [
        1,
        1,
        1,
    ]


    remaining = (
        target
        -
        3
    )


    index = 0


    while remaining > 0:

        counts[
            index % 3
        ] += 1


        remaining -= 1

        index += 1


    images: List[
        GeneratedImage
    ] = []


    errors: List[str] = []


    # -----------------------------------------------------
    # OPENAI
    # -----------------------------------------------------

    try:

        images.extend(
            generate_with_openai(
                prompt=
                    enhanced,

                original_prompt=
                    original_prompt,

                route=
                    routes[0],

                number=
                    counts[0]
            )
        )


    except Exception as error:

        errors.append(
            (
                "GPT-Image-2: "
                +
                clean_text(
                    error,
                    4000
                )
            )
        )


    # -----------------------------------------------------
    # GOOGLE PRO
    # -----------------------------------------------------

    if GEMINI_API_KEY:

        try:

            images.extend(
                generate_with_gemini(
                    prompt=
                        enhanced,

                    original_prompt=
                        original_prompt,

                    route=
                        routes[1],

                    number=
                        counts[1]
                )
            )


        except Exception as error:

            errors.append(
                (
                    "Nano Banana Pro: "
                    +
                    clean_text(
                        error,
                        4000
                    )
                )
            )


        # -------------------------------------------------
        # GOOGLE FAST
        # -------------------------------------------------

        try:

            images.extend(
                generate_with_gemini(
                    prompt=
                        enhanced,

                    original_prompt=
                        original_prompt,

                    route=
                        routes[2],

                    number=
                        counts[2]
                )
            )


        except Exception as error:

            errors.append(
                (
                    "Nano Banana 2: "
                    +
                    clean_text(
                        error,
                        4000
                    )
                )
            )


    if not images:

        raise XPANDImageProviderError(
            (
                "COMPARE فشل من كل المحركات.\n"
                +
                "\n".join(
                    errors
                )
            )
        )


    return ImageGenerationResponse(
        ok=
            True,

        images=
            images,

        selected_route=
            MODE_COMPARE,

        routes=
            routes,

        original_prompt=
            original_prompt,

        enhanced_prompt=
            enhanced,

        elapsed_seconds=
            round(
                time.monotonic()
                -
                started,
                3
            ),

        errors=
            errors,
    )


# =========================================================
# MAIN PUBLIC FUNCTION
# =========================================================

def generate_image(
    user_prompt: str,
    *,
    mode: str = "",
    aspect_ratio: str = "",
    image_size: str = "",
    quality: str = "",
    number: int = 1,
    reference_count: int = 0,
    allow_fallback: bool = True
) -> ImageGenerationResponse:

    original_prompt = clean_text(
        user_prompt,
        10000
    )


    if not original_prompt:

        raise XPANDImageError(
            "لازم يكون في وصف للصورة."
        )


    final_aspect_ratio = detect_aspect_ratio(
        original_prompt,
        aspect_ratio
    )


    final_image_size = detect_image_size(
        original_prompt,
        image_size
    )


    final_quality = detect_quality(
        original_prompt,
        quality
    )


    effective_mode = resolve_effective_mode(
        original_prompt,
        mode=
            mode,
        reference_count=
            reference_count
    )


    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND IMAGE REQUEST V1.3"
    )
    print(
        "=========================================="
    )
    print(
        (
            "🎯 Effective mode: "
            +
            effective_mode
        )
    )
    print(
        (
            "📐 Aspect ratio: "
            +
            final_aspect_ratio
        )
    )
    print(
        (
            "🖼️ Resolution intent: "
            +
            final_image_size
        )
    )
    print(
        (
            "💎 Quality: "
            +
            final_quality
        )
    )
    print("")


    # -----------------------------------------------------
    # BEST
    # -----------------------------------------------------

    if effective_mode == MODE_BEST:

        return run_google_openai_fusion(
            original_prompt,
            aspect_ratio=
                final_aspect_ratio,
            image_size=
                final_image_size,
            quality=
                final_quality,
            number=
                number,
            stronger=
                True
        )


    # -----------------------------------------------------
    # PRO
    # -----------------------------------------------------

    if effective_mode == MODE_PRO:

        return run_google_openai_fusion(
            original_prompt,
            aspect_ratio=
                final_aspect_ratio,
            image_size=
                final_image_size,
            quality=
                final_quality,
            number=
                number,
            stronger=
                False
        )


    # -----------------------------------------------------
    # COMPARE
    # -----------------------------------------------------

    if effective_mode == MODE_COMPARE:

        return run_compare(
            original_prompt,
            aspect_ratio=
                final_aspect_ratio,
            image_size=
                final_image_size,
            quality=
                final_quality,
            number=
                number
        )


    # -----------------------------------------------------
    # GOOGLE PRO
    # -----------------------------------------------------

    if effective_mode == MODE_GOOGLE_PRO:

        return run_google_direct(
            original_prompt,
            pro=
                True,
            aspect_ratio=
                final_aspect_ratio,
            image_size=
                final_image_size,
            quality=
                final_quality,
            number=
                number
        )


    # -----------------------------------------------------
    # GOOGLE FAST / FAST
    # -----------------------------------------------------

    if effective_mode in {
        MODE_GOOGLE_FAST,
        MODE_FAST,
    }:

        return run_google_direct(
            original_prompt,
            pro=
                False,
            aspect_ratio=
                final_aspect_ratio,
            image_size=
                final_image_size,
            quality=
                final_quality,
            number=
                number
        )


    # -----------------------------------------------------
    # OPENAI DEFAULT
    # -----------------------------------------------------

    return run_openai_direct(
        original_prompt,
        aspect_ratio=
            final_aspect_ratio,
        image_size=
            final_image_size,
        quality=
            final_quality,
        number=
            number
    )


# =========================================================
# ENGINE STATUS
# =========================================================

def get_image_engine_status() -> Dict[
    str,
    Any
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
            },

            "google_fast": {
                "configured":
                    bool(
                        GEMINI_API_KEY
                    ),

                "model":
                    GOOGLE_IMAGE_FAST_MODEL,
            },

            "google_pro": {
                "configured":
                    bool(
                        GEMINI_API_KEY
                    ),

                "model":
                    GOOGLE_IMAGE_PRO_MODEL,
            },
        },

        "default_mode":
            DEFAULT_MODE,

        "default_quality":
            DEFAULT_QUALITY,

        "supports_openai_fusion":
            bool(
                OPENAI_API_KEY
            ),

        "supports_google_openai_fusion":
            bool(
                OPENAI_API_KEY
                and
                GEMINI_API_KEY
            ),

        "google_optional":
            True,

        "google_failure_fallback":
            "openai_fusion",

        "openai_fusion_pipeline": [
            OPENAI_DIRECTOR_MODEL,
            OPENAI_IMAGE_MODEL,
            OPENAI_DIRECTOR_MODEL,
            OPENAI_IMAGE_MODEL,
        ],

        "best_google_pipeline": [
            OPENAI_DIRECTOR_MODEL,
            GOOGLE_IMAGE_PRO_MODEL,
            OPENAI_DIRECTOR_MODEL,
            OPENAI_IMAGE_MODEL,
        ],

        "telegram_ready":
            True,
    }


# =========================================================
# FRIENDLY ROUTE DESCRIPTION
# =========================================================

def describe_route(
    route: ImageRoute
) -> str:

    labels = {
        PROVIDER_OPENAI:
            "GPT-Image-2",

        PROVIDER_GOOGLE_FAST:
            "Nano Banana 2",

        PROVIDER_GOOGLE_PRO:
            "Nano Banana Pro",
    }


    label = labels.get(
        route.provider,
        route.model
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
# IMPORTANT:
# This does NOT generate an image.
# This does NOT call paid APIs.
# =========================================================

if __name__ == "__main__":

    status = get_image_engine_status()


    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND SMART IMAGE ENGINE V1.3"
    )
    print(
        "=========================================="
    )
    print("")


    print(
        "OpenAI Image:",
        (
            "READY"
            if
            status[
                "providers"
            ][
                "openai"
            ][
                "configured"
            ]
            else
            "missing key"
        ),
        "|",
        OPENAI_IMAGE_MODEL
    )


    print(
        "GPT-5.6 Sol Director:",
        (
            "READY"
            if
            status[
                "providers"
            ][
                "openai"
            ][
                "configured"
            ]
            else
            "missing key"
        ),
        "|",
        OPENAI_DIRECTOR_MODEL
    )


    print(
        "Nano Banana 2:",
        (
            "CONFIGURED"
            if
            status[
                "providers"
            ][
                "google_fast"
            ][
                "configured"
            ]
            else
            "missing key"
        ),
        "|",
        GOOGLE_IMAGE_FAST_MODEL
    )


    print(
        "Nano Banana Pro:",
        (
            "CONFIGURED"
            if
            status[
                "providers"
            ][
                "google_pro"
            ][
                "configured"
            ]
            else
            "missing key"
        ),
        "|",
        GOOGLE_IMAGE_PRO_MODEL
    )


    print("")


    print(
        "OpenAI Fusion:",
        (
            "READY"
            if
            status[
                "supports_openai_fusion"
            ]
            else
            "NOT READY"
        )
    )


    print(
        "Google + OpenAI Fusion:",
        (
            "CONFIGURED"
            if
            status[
                "supports_google_openai_fusion"
            ]
            else
            "Google unavailable"
        )
    )


    print("")


    print(
        "BEST PRIMARY PIPELINE:"
    )

    print(
        (
            " - Stage 1: "
            +
            OPENAI_DIRECTOR_MODEL
            +
            " | Art Director"
        )
    )

    print(
        (
            " - Stage 2: "
            +
            GOOGLE_IMAGE_PRO_MODEL
            +
            " | Base image if Google quota works"
        )
    )

    print(
        (
            " - Stage 3: "
            +
            OPENAI_DIRECTOR_MODEL
            +
            " | Visual Critic"
        )
    )

    print(
        (
            " - Stage 4: "
            +
            OPENAI_IMAGE_MODEL
            +
            " | Final image refinement"
        )
    )


    print("")


    print(
        "BEST GOOGLE FALLBACK:"
    )

    print(
        (
            " - Stage 1: "
            +
            OPENAI_DIRECTOR_MODEL
            +
            " | Art Director"
        )
    )

    print(
        (
            " - Stage 2: "
            +
            OPENAI_IMAGE_MODEL
            +
            " | Base image"
        )
    )

    print(
        (
            " - Stage 3: "
            +
            OPENAI_DIRECTOR_MODEL
            +
            " | Visual Critic"
        )
    )

    print(
        (
            " - Stage 4: "
            +
            OPENAI_IMAGE_MODEL
            +
            " | Final image refinement"
        )
    )


    print("")


    test_prompt = (
        "اعمللي بوستر منتج فاخر بأفضل نتيجة ممكنة"
    )


    print(
        "Test request effective mode:"
    )

    print(
        " -",
        resolve_effective_mode(
            test_prompt
        )
    )


    print("")

    print(
        "Expected:"
    )

    print(
        " - best"
    )

    print("")

    print(
        "✅ Google is now OPTIONAL"
    )

    print(
        "✅ Google quota failure will NOT stop XPAND"
    )

    print(
        "✅ GPT-5.6 Sol visual direction enabled"
    )

    print(
        "✅ GPT-5.6 Sol image critique enabled"
    )

    print(
        "✅ GPT-Image-2 generation enabled"
    )

    print(
        "✅ GPT-Image-2 image edit enabled"
    )

    print("")
