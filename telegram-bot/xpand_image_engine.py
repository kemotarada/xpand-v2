# =========================================================
# XPAND SMART IMAGE ENGINE V1.1
#
# Professional multi-model image generation for XPAND.
#
# Providers:
# - OpenAI GPT-Image-2
# - Google Gemini 3 Pro Image / Nano Banana Pro
# - Google Gemini 3.1 Flash Image / Nano Banana 2
#
# BEST MODE:
# - Uses ALL available top image models.
# - If user requests 3 images:
#     1 x GPT-Image-2
#     1 x Nano Banana Pro
#     1 x Nano Banana 2
#
# FIX V1.1:
# - Removed unsupported Gemini "delivery" parameter.
# - Gemini generation now loops correctly for >1 image.
# - BEST mode genuinely uses all 3 models.
# - Requested count is distributed across providers.
# - More robust Gemini image extraction.
#
# No extra SDK required.
#
# Existing requirement:
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
# IDENTITY
# =========================================================

ENGINE_NAME = (
    "XPAND Smart Image Engine"
)

ENGINE_VERSION = (
    "1.1"
)


# =========================================================
# ENVIRONMENT
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


OPENAI_IMAGE_MODEL = str(
    os.environ.get(
        "XPAND_OPENAI_IMAGE_MODEL",
        "gpt-image-2"
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


GEMINI_INTERACTIONS_URL = (
    "https://generativelanguage.googleapis.com/"
    "v1beta/interactions"
)


# =========================================================
# ROUTE NAMES
# =========================================================

ROUTE_OPENAI = (
    "openai"
)

ROUTE_GOOGLE_FAST = (
    "google_fast"
)

ROUTE_GOOGLE_PRO = (
    "google_pro"
)

ROUTE_BEST = (
    "best"
)


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


# =========================================================
# EXCEPTIONS
# =========================================================

class XPANDImageError(
    Exception
):
    """Base XPAND image error."""


class XPANDImageConfigurationError(
    XPANDImageError
):
    """Missing API configuration."""


class XPANDImageProviderError(
    XPANDImageError
):
    """Image provider API failure."""


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


    text = (
        text
        .replace(
            "أ",
            "ا"
        )
        .replace(
            "إ",
            "ا"
        )
        .replace(
            "آ",
            "ا"
        )
        .replace(
            "ة",
            "ه"
        )
        .replace(
            "ى",
            "ي"
        )
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

    normalized = (
        normalize_arabic(
            text
        )
    )


    return any(
        normalize_arabic(
            marker
        )
        in normalized
        for marker in markers
    )


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


    normalized = (
        normalize_arabic(
            prompt
        )
    )


    ratios = [
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
    ]


    for ratio in ratios:

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
            "profile",
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
            "print quality",
            "للطباعه",
            "للطباعة",
            "high resolution",
            "ultra high resolution",
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


    if explicit in {
        "low",
        "medium",
        "high",
        "auto",
    }:

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
            "تجريبي",
        ]
    ):

        return "medium"


    return DEFAULT_QUALITY


# =========================================================
# PROFESSIONAL PROMPT ENHANCER
# =========================================================

def extract_quoted_text(
    prompt: str
) -> List[str]:

    patterns = [
        r'"([^"]+)"',
        r"'([^']+)'",
        r"“([^”]+)”",
        r"«([^»]+)»",
    ]


    results: List[
        str
    ] = []


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


    directives: List[
        str
    ] = [
        (
            "Create a premium professional image based "
            "strictly on the user's requested concept."
        ),

        (
            "Preserve the user's subject, intent, requested "
            "objects, colors, environment, composition, "
            "and constraints."
        ),

        (
            "Use strong visual hierarchy, intentional "
            "composition, realistic lighting behavior, "
            "high-quality materials and textures, clean "
            "edges, coherent perspective, and "
            "commercial-grade finishing."
        ),

        (
            "Avoid accidental extra objects, malformed "
            "details, duplicated subjects, broken anatomy, "
            "visual clutter, random text, fake watermarks, "
            "and unnecessary logos."
        ),
    ]


    if contains_any(
        user_prompt,
        [
            "واقعي",
            "واقعيه",
            "واقعية",
            "realistic",
            "photorealistic",
            "صوره حقيقيه",
            "صورة حقيقية",
            "تصوير",
        ]
    ):

        directives.extend(
            [
                (
                    "Photorealistic commercial photography, "
                    "physically plausible illumination, "
                    "natural material detail, realistic "
                    "lens behavior and refined color grading."
                ),

                (
                    "Avoid CGI-looking surfaces unless the "
                    "user explicitly requests a 3D render."
                ),
            ]
        )


    if contains_any(
        user_prompt,
        [
            "منتج",
            "product",
            "عطر",
            "perfume",
            "عبوه",
            "عبوة",
            "package",
            "packaging",
            "ساعه",
            "ساعة",
            "watch",
        ]
    ):

        directives.extend(
            [
                (
                    "Treat this as premium product "
                    "advertising photography."
                ),

                (
                    "Keep the product visually dominant, "
                    "well separated from the background, "
                    "with polished reflections and "
                    "controlled studio-grade lighting."
                ),
            ]
        )


    if contains_any(
        user_prompt,
        [
            "اعلان",
            "إعلان",
            "advertisement",
            "ad campaign",
            "campaign",
            "براند",
            "brand",
            "branding",
        ]
    ):

        directives.extend(
            [
                (
                    "Art direction should feel like a "
                    "high-budget international advertising "
                    "campaign."
                ),

                (
                    "Leave intentional negative space where "
                    "useful for marketing copy without "
                    "inventing copy that was not requested."
                ),
            ]
        )


    if contains_any(
        user_prompt,
        [
            "سينمائي",
            "cinematic",
            "فيلم",
            "movie",
        ]
    ):

        directives.append(
            (
                "Use cinematic composition, controlled "
                "contrast, motivated lighting, depth, "
                "atmospheric separation and filmic "
                "color grading."
            )
        )


    if contains_any(
        user_prompt,
        [
            "فاخر",
            "فخم",
            "luxury",
            "premium",
            "راقي",
            "high-end",
        ]
    ):

        directives.append(
            (
                "Luxury art direction: restrained, elegant, "
                "premium materials, deliberate lighting "
                "and sophisticated color relationships."
            )
        )


    if contains_any(
        user_prompt,
        [
            "3d",
            "3d render",
            "رندر",
            "render",
        ]
    ):

        directives.append(
            (
                "Produce a top-tier physically based 3D "
                "render with premium materials, accurate "
                "reflections, realistic shadows and "
                "professional rendering."
            )
        )


    quoted_texts = (
        extract_quoted_text(
            user_prompt
        )
    )


    if quoted_texts:

        exact_text = "\n".join(
            (
                f'- "{item}"'
            )
            for item in quoted_texts
        )


        directives.append(
            (
                "The following quoted text must be rendered "
                "exactly as written, without translation, "
                "rewriting or spelling changes:\n"
                +
                exact_text
            )
        )


    directives.append(
        (
            f"Target aspect ratio: "
            f"{aspect_ratio}."
        )
    )


    if image_size in {
        "2K",
        "4K",
    }:

        directives.append(
            (
                "Prioritize fine detail that remains clean "
                "at high output resolution."
            )
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
            (
                f"- {item}"
            )
            for item in directives
        )
    )


# =========================================================
# SMART MODEL ROUTER
# =========================================================

def normalize_mode(
    mode: str
) -> str:

    value = clean_text(
        mode,
        40
    ).lower()


    aliases = {
        "auto":
            "auto",

        "smart":
            "auto",

        "openai":
            ROUTE_OPENAI,

        "gpt":
            ROUTE_OPENAI,

        "gpt-image-2":
            ROUTE_OPENAI,

        "google_fast":
            ROUTE_GOOGLE_FAST,

        "google-fast":
            ROUTE_GOOGLE_FAST,

        "nano banana 2":
            ROUTE_GOOGLE_FAST,

        "nano-banana-2":
            ROUTE_GOOGLE_FAST,

        "flash":
            ROUTE_GOOGLE_FAST,

        "google_pro":
            ROUTE_GOOGLE_PRO,

        "google-pro":
            ROUTE_GOOGLE_PRO,

        "nano banana pro":
            ROUTE_GOOGLE_PRO,

        "nano-banana-pro":
            ROUTE_GOOGLE_PRO,

        "pro":
            ROUTE_GOOGLE_PRO,

        "best":
            ROUTE_BEST,

        "max":
            ROUTE_BEST,

        "premium":
            ROUTE_BEST,
    }


    return aliases.get(
        value,
        "auto"
    )


def select_image_route(
    prompt: str,
    mode: str = "",
    aspect_ratio: str = "",
    image_size: str = "",
    quality: str = "",
    reference_count: int = 0
) -> List[
    ImageRoute
]:

    chosen_mode = normalize_mode(
        mode
        or
        DEFAULT_MODE
    )


    final_aspect_ratio = (
        detect_aspect_ratio(
            prompt,
            aspect_ratio
        )
    )


    final_image_size = (
        detect_image_size(
            prompt,
            image_size
        )
    )


    final_quality = (
        detect_quality(
            prompt,
            quality
        )
    )


    def route(
        provider: str,
        model: str,
        reason: str
    ) -> ImageRoute:

        return ImageRoute(
            provider=
                provider,

            model=
                model,

            reason=
                reason,

            aspect_ratio=
                final_aspect_ratio,

            image_size=
                final_image_size,

            quality=
                final_quality,
        )


    # -----------------------------------------------------
    # EXPLICIT ROUTES
    # -----------------------------------------------------

    if (
        chosen_mode
        ==
        ROUTE_OPENAI
    ):

        return [
            route(
                ROUTE_OPENAI,
                OPENAI_IMAGE_MODEL,
                (
                    "OpenAI requested explicitly."
                )
            )
        ]


    if (
        chosen_mode
        ==
        ROUTE_GOOGLE_FAST
    ):

        return [
            route(
                ROUTE_GOOGLE_FAST,
                GOOGLE_IMAGE_FAST_MODEL,
                (
                    "Nano Banana 2 requested explicitly."
                )
            )
        ]


    if (
        chosen_mode
        ==
        ROUTE_GOOGLE_PRO
    ):

        return [
            route(
                ROUTE_GOOGLE_PRO,
                GOOGLE_IMAGE_PRO_MODEL,
                (
                    "Nano Banana Pro requested explicitly."
                )
            )
        ]


    # -----------------------------------------------------
    # TRUE BEST MODE
    #
    # ALL THREE MODELS.
    # -----------------------------------------------------

    if (
        chosen_mode
        ==
        ROUTE_BEST
    ):

        return [
            route(
                ROUTE_OPENAI,
                OPENAI_IMAGE_MODEL,
                (
                    "BEST mode: GPT-Image-2."
                )
            ),

            route(
                ROUTE_GOOGLE_PRO,
                GOOGLE_IMAGE_PRO_MODEL,
                (
                    "BEST mode: Nano Banana Pro."
                )
            ),

            route(
                ROUTE_GOOGLE_FAST,
                GOOGLE_IMAGE_FAST_MODEL,
                (
                    "BEST mode: Nano Banana 2."
                )
            ),
        ]


    # -----------------------------------------------------
    # AUTO ROUTING
    # -----------------------------------------------------

    fast_request = contains_any(
        prompt,
        [
            "سريع",
            "بسرعه",
            "بسرعة",
            "quick",
            "fast",
            "draft",
            "تجريبي",
            "preview",
        ]
    )


    needs_4k = (
        final_image_size
        ==
        "4K"
    )


    brand_heavy = contains_any(
        prompt,
        [
            "براند",
            "brand",
            "branding",
            "brand identity",
            "campaign",
            "حمله",
            "حملة",
            "اعلان احترافي",
            "إعلان احترافي",
            "key visual",
            "art direction",
            "هوية بصريه",
            "هوية بصرية",
            "packaging",
            "عبوه",
            "عبوة",
        ]
    )


    complex_professional = contains_any(
        prompt,
        [
            "احترافي جدا",
            "احترافي جداً",
            "professional",
            "premium",
            "فاخر",
            "luxury",
            "high-end",
            "commercial",
            "اعلان عالمي",
            "إعلان عالمي",
        ]
    )


    precision_text = contains_any(
        prompt,
        [
            "اكتب",
            "اكتب النص",
            "النص التالي",
            "text",
            "typography",
            "تايبوجرافي",
            "headline",
            "عنوان",
        ]
    )


    precision_edit_style = contains_any(
        prompt,
        [
            "حافظ على",
            "نفس الشخص",
            "نفس المنتج",
            "نفس الوجه",
            "preserve",
            "exact",
            "high fidelity",
            "دقيق",
            "بدقه",
            "بدقة",
        ]
    )


    if fast_request:

        return [
            route(
                ROUTE_GOOGLE_FAST,
                GOOGLE_IMAGE_FAST_MODEL,
                (
                    "Fast request: Nano Banana 2 selected."
                )
            )
        ]


    if needs_4k:

        if (
            brand_heavy
            or
            complex_professional
            or
            reference_count >= 2
        ):

            return [
                route(
                    ROUTE_GOOGLE_PRO,
                    GOOGLE_IMAGE_PRO_MODEL,
                    (
                        "Professional 4K request: "
                        "Nano Banana Pro selected."
                    )
                )
            ]


        return [
            route(
                ROUTE_GOOGLE_FAST,
                GOOGLE_IMAGE_FAST_MODEL,
                (
                    "4K request: Nano Banana 2 selected."
                )
            )
        ]


    if (
        brand_heavy
        or
        reference_count >= 2
    ):

        return [
            route(
                ROUTE_GOOGLE_PRO,
                GOOGLE_IMAGE_PRO_MODEL,
                (
                    "Brand/reference-heavy request: "
                    "Nano Banana Pro selected."
                )
            )
        ]


    if (
        precision_text
        or
        precision_edit_style
    ):

        return [
            route(
                ROUTE_OPENAI,
                OPENAI_IMAGE_MODEL,
                (
                    "Precision/text-heavy request: "
                    "GPT-Image-2 selected."
                )
            )
        ]


    if complex_professional:

        return [
            route(
                ROUTE_GOOGLE_PRO,
                GOOGLE_IMAGE_PRO_MODEL,
                (
                    "Premium professional request: "
                    "Nano Banana Pro selected."
                )
            )
        ]


    return [
        route(
            ROUTE_OPENAI,
            OPENAI_IMAGE_MODEL,
            (
                "General high-quality request: "
                "GPT-Image-2 selected."
            )
        )
    ]


# =========================================================
# BEST COUNT DISTRIBUTION
# =========================================================

def distribute_image_count(
    routes: List[
        ImageRoute
    ],
    requested_number: int
) -> List[int]:

    if not routes:

        return []


    requested_number = max(
        1,
        min(
            int(
                requested_number
                or
                1
            ),
            12
        )
    )


    if len(
        routes
    ) == 1:

        return [
            requested_number
        ]


    #
    # BEST mode guarantees every selected model
    # gets at least one generation.
    #
    total_target = max(
        requested_number,
        len(
            routes
        )
    )


    counts = [
        1
        for _ in routes
    ]


    remaining = (
        total_target
        -
        len(
            routes
        )
    )


    index = 0


    while remaining > 0:

        counts[
            index % len(
                counts
            )
        ] += 1


        remaining -= 1

        index += 1


    return counts


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

        value = (
            response.json()
        )


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
            3000
        )
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

        mime_type = (
            "image/png"
        )


    return (
        response.content,
        mime_type
    )


def _decode_base64_image(
    data: str
) -> Optional[
    bytes
]:

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

                for data in possible_data:

                    if isinstance(
                        data,
                        str
                    ):

                        raw = (
                            _decode_base64_image(
                                data
                            )
                        )


                        if raw:

                            found.append(
                                (
                                    raw,
                                    (
                                        mime_type
                                        or
                                        "image/jpeg"
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
                    not possible_data[0]
                    and
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


    for (
        image_bytes,
        mime_type
    ) in found:

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
# OPENAI GENERATION
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
                or
                1
            ),
            4
        )
    )


    provider_size = (
        openai_size_for_ratio(
            route.aspect_ratio
        )
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
            (
                route.quality
                if
                route.quality
                in {
                    "low",
                    "medium",
                    "high",
                    "auto",
                }
                else
                "high"
            ),
    }


    response = requests.post(
        OPENAI_IMAGE_GENERATION_URL,

        headers={
            "Authorization":
                (
                    f"Bearer "
                    f"{OPENAI_API_KEY}"
                ),

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
                "OpenAI",
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
                "OpenAI رجع استجابة ناجحة "
                "لكن ما لقيت صورة بالنتيجة."
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
                uuid.uuid4().hex[:10]
            )
        )


        if number > 1:

            unique_request_id = (
                unique_request_id
                +
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
                    (
                        mime_type
                        or
                        "image/png"
                    ),

                provider=
                    ROUTE_OPENAI,

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
                    route.quality,

                route_reason=
                    route.reason,

                request_id=
                    unique_request_id,

                metadata={
                    "index":
                        index,

                    "provider_size":
                        provider_size,

                    "requested_image_size":
                        route.image_size,
                }
            )
        )


    return results


# =========================================================
# GEMINI SINGLE GENERATION
# =========================================================

def _generate_one_with_gemini(
    prompt: str,
    original_prompt: str,
    route: ImageRoute,
    index: int = 0
) -> GeneratedImage:

    image_size = (
        route.image_size
        if
        route.image_size
        in
        SUPPORTED_GOOGLE_IMAGE_SIZES
        else
        "1K"
    )


    #
    # IMPORTANT:
    #
    # Do NOT send:
    #
    # "delivery": "inline"
    #
    # The live API/model returned:
    # "Image delivery mode is not supported."
    #
    # Google image-generation examples work with:
    #
    # type
    # aspect_ratio
    # image_size
    #
    payload: Dict[
        str,
        Any
    ] = {
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


    interaction_id = clean_text(
        data.get(
            "id"
        ),
        200
    )


    unique_request_id = (
        interaction_id
        or
        (
            "gg-"
            +
            uuid.uuid4().hex[:10]
        )
    )


    if index > 0:

        unique_request_id = (
            unique_request_id
            +
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
            (
                mime_type
                or
                "image/jpeg"
            ),

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
            unique_request_id,

        metadata={
            "index":
                index,

            "interaction_id":
                interaction_id,

            "google_response_format": {
                "type":
                    "image",

                "aspect_ratio":
                    route.aspect_ratio,

                "image_size":
                    image_size,
            },
        }
    )


# =========================================================
# GEMINI GENERATION
#
# Gemini Interactions image generation naturally returns
# one final image per interaction.
#
# For number > 1 we intentionally perform multiple
# generations.
# =========================================================

def generate_with_gemini(
    prompt: str,
    original_prompt: str,
    route: ImageRoute,
    number: int = 1
) -> List[
    GeneratedImage
]:

    if not GEMINI_API_KEY:

        raise XPANDImageConfigurationError(
            (
                "GEMINI_API_KEY مش موجود "
                "على Railway."
            )
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


    results: List[
        GeneratedImage
    ] = []


    errors: List[
        str
    ] = []


    for index in range(
        number
    ):

        try:

            image = (
                _generate_one_with_gemini(
                    prompt=
                        prompt,

                    original_prompt=
                        original_prompt,

                    route=
                        route,

                    index=
                        index,
                )
            )


            results.append(
                image
            )


        except Exception as error:

            errors.append(
                clean_text(
                    error,
                    3000
                )
            )


    if not results:

        raise XPANDImageProviderError(
            (
                f"Gemini {route.model} فشل.\n"
                +
                "\n".join(
                    errors
                )
            )
        )


    return results


# =========================================================
# FALLBACK LOGIC
# =========================================================

def fallback_route_for(
    failed_route: ImageRoute
) -> Optional[
    ImageRoute
]:

    if (
        failed_route.provider
        ==
        ROUTE_OPENAI
        and
        GEMINI_API_KEY
    ):

        return ImageRoute(
            provider=
                ROUTE_GOOGLE_PRO,

            model=
                GOOGLE_IMAGE_PRO_MODEL,

            reason=
                (
                    "Automatic fallback after "
                    "OpenAI failure."
                ),

            aspect_ratio=
                failed_route.aspect_ratio,

            image_size=
                failed_route.image_size,

            quality=
                failed_route.quality,
        )


    if (
        failed_route.provider
        in {
            ROUTE_GOOGLE_FAST,
            ROUTE_GOOGLE_PRO,
        }
        and
        OPENAI_API_KEY
    ):

        return ImageRoute(
            provider=
                ROUTE_OPENAI,

            model=
                OPENAI_IMAGE_MODEL,

            reason=
                (
                    "Automatic fallback after "
                    "Gemini failure."
                ),

            aspect_ratio=
                failed_route.aspect_ratio,

            image_size=
                failed_route.image_size,

            quality=
                failed_route.quality,
        )


    return None


# =========================================================
# PROVIDER DISPATCH
# =========================================================

def _run_route(
    route: ImageRoute,
    enhanced_prompt: str,
    original_prompt: str,
    number: int
) -> List[
    GeneratedImage
]:

    if (
        route.provider
        ==
        ROUTE_OPENAI
    ):

        return generate_with_openai(
            prompt=
                enhanced_prompt,

            original_prompt=
                original_prompt,

            route=
                route,

            number=
                number,
        )


    if route.provider in {
        ROUTE_GOOGLE_FAST,
        ROUTE_GOOGLE_PRO,
    }:

        return generate_with_gemini(
            prompt=
                enhanced_prompt,

            original_prompt=
                original_prompt,

            route=
                route,

            number=
                number,
        )


    raise XPANDImageError(
        (
            "مسار توليد غير معروف: "
            +
            str(
                route.provider
            )
        )
    )


# =========================================================
# MAIN GENERATION FUNCTION
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

    started = (
        time.monotonic()
    )


    original_prompt = clean_text(
        user_prompt,
        10000
    )


    if not original_prompt:

        raise XPANDImageError(
            "لازم يكون في وصف للصورة."
        )


    routes = select_image_route(
        prompt=
            original_prompt,

        mode=
            mode,

        aspect_ratio=
            aspect_ratio,

        image_size=
            image_size,

        quality=
            quality,

        reference_count=
            reference_count,
    )


    if not routes:

        raise XPANDImageError(
            "ما تم اختيار موديل للصورة."
        )


    primary_route = (
        routes[0]
    )


    enhanced_prompt = (
        build_professional_prompt(
            original_prompt,
            primary_route.aspect_ratio,
            primary_route.image_size
        )
    )


    route_counts = (
        distribute_image_count(
            routes,
            number
        )
    )


    print(
        (
            "🧠 XPAND IMAGE ROUTES | "
            +
            " | ".join(
                (
                    f"{route.provider}"
                    f"/{route.model}"
                    f" x{count}"
                )
                for (
                    route,
                    count
                ) in zip(
                    routes,
                    route_counts
                )
            )
        )
    )


    results: List[
        GeneratedImage
    ] = []


    errors: List[
        str
    ] = []


    executed_provider_models = (
        set()
    )


    for (
        route,
        route_count
    ) in zip(
        routes,
        route_counts
    ):

        key = (
            route.provider,
            route.model,
        )


        if key in executed_provider_models:

            continue


        executed_provider_models.add(
            key
        )


        try:

            generated = _run_route(
                route=
                    route,

                enhanced_prompt=
                    enhanced_prompt,

                original_prompt=
                    original_prompt,

                number=
                    route_count,
            )


            results.extend(
                generated
            )


        except Exception as error:

            errors.append(
                (
                    f"{route.provider}/"
                    f"{route.model}: "
                    f"{clean_text(
                        error,
                        3000
                    )}"
                )
            )


            #
            # Multi-model BEST already has other providers.
            #
            # We do not introduce a fourth duplicate fallback
            # because another model is already being tried.
            #
            if (
                len(
                    routes
                ) > 1
                or
                not allow_fallback
            ):

                continue


            fallback = (
                fallback_route_for(
                    route
                )
            )


            if fallback is None:

                continue


            fallback_key = (
                fallback.provider,
                fallback.model,
            )


            if (
                fallback_key
                in
                executed_provider_models
            ):

                continue


            executed_provider_models.add(
                fallback_key
            )


            try:

                fallback_images = (
                    _run_route(
                        route=
                            fallback,

                        enhanced_prompt=
                            enhanced_prompt,

                        original_prompt=
                            original_prompt,

                        number=
                            route_count,
                    )
                )


                results.extend(
                    fallback_images
                )


                routes.append(
                    fallback
                )


            except Exception as fallback_error:

                errors.append(
                    (
                        f"{fallback.provider}/"
                        f"{fallback.model}: "
                        f"{clean_text(
                            fallback_error,
                            3000
                        )}"
                    )
                )


    elapsed = round(
        (
            time.monotonic()
            -
            started
        ),
        3
    )


    if not results:

        readable_errors = (
            "\n".join(
                errors
            )
            or
            "Unknown image-generation failure."
        )


        raise XPANDImageProviderError(
            (
                "فشل توليد الصورة من كل "
                "المحركات المتاحة.\n"
                +
                readable_errors
            )
        )


    selected_route = (
        ROUTE_BEST
        if len(
            route_counts
        ) > 1
        else
        routes[0].provider
    )


    return ImageGenerationResponse(
        ok=
            True,

        images=
            results,

        selected_route=
            selected_route,

        routes=
            routes,

        original_prompt=
            original_prompt,

        enhanced_prompt=
            enhanced_prompt,

        elapsed_seconds=
            elapsed,

        errors=
            errors,
    )


# =========================================================
# CONFIGURATION STATUS
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

                "model":
                    OPENAI_IMAGE_MODEL,
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

        "supports_best_mode":
            bool(
                OPENAI_API_KEY
                and
                GEMINI_API_KEY
            ),

        "best_mode_models": [
            OPENAI_IMAGE_MODEL,
            GOOGLE_IMAGE_PRO_MODEL,
            GOOGLE_IMAGE_FAST_MODEL,
        ],

        "best_mode_provider_count":
            3,

        "google_native_4k":
            True,

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

        ROUTE_OPENAI:
            "GPT-Image-2",

        ROUTE_GOOGLE_FAST:
            "Nano Banana 2",

        ROUTE_GOOGLE_PRO:
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
# NO PAID IMAGE GENERATION.
# =========================================================

if __name__ == "__main__":

    status = (
        get_image_engine_status()
    )


    print("")

    print(
        "======================================"
    )

    print(
        " XPAND SMART IMAGE ENGINE V1.1"
    )

    print(
        "======================================"
    )

    print("")


    print(
        "OpenAI:",
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
        "Nano Banana 2:",
        (
            "READY"
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
            "READY"
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


    print(
        "BEST mode:",
        (
            "READY"
            if
            status[
                "supports_best_mode"
            ]
            else
            "needs both API keys"
        )
    )


    print("")


    print(
        "BEST models:"
    )


    for model in status[
        "best_mode_models"
    ]:

        print(
            " -",
            model
        )


    print("")


    test_routes = (
        select_image_route(
            (
                "اعمللي 3 صور بأفضل نتيجة "
                "ممكنة لبوستر منتج فاخر"
            ),
            mode=
                "best",
            aspect_ratio=
                "4:5",
        )
    )


    test_counts = (
        distribute_image_count(
            test_routes,
            3
        )
    )


    print(
        "BEST 3-image routing:"
    )


    for (
        route,
        count
    ) in zip(
        test_routes,
        test_counts
    ):

        print(
            (
                " - "
                +
                route.model
                +
                " x"
                +
                str(
                    count
                )
            )
        )


    print("")

    print(
        "Expected:"
    )

    print(
        " - gpt-image-2 x1"
    )

    print(
        " - gemini-3-pro-image x1"
    )

    print(
        " - gemini-3.1-flash-image x1"
    )

    print("")
