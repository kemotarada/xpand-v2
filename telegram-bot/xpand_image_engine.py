# =========================================================
# XPAND SMART IMAGE ENGINE V1.0
#
# Professional multi-model image generation for XPAND.
#
# Providers:
# - OpenAI GPT-Image-2
# - Google Gemini 3 Pro Image / Nano Banana Pro
# - Google Gemini 3.1 Flash Image / Nano Banana 2
#
# Goals:
# - Natural Arabic requests
# - Smart automatic model routing
# - Professional prompt enhancement
# - 4K routing where supported
# - BEST mode using multiple premium models
# - No extra Python SDK dependencies
#
# Existing requirement:
# requests>=2.32.0,<3
# =========================================================

from __future__ import annotations

import base64
import mimetypes
import os
import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import requests


# =========================================================
# IDENTITY
# =========================================================

ENGINE_NAME = "XPAND Smart Image Engine"
ENGINE_VERSION = "1.0"


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
# PROVIDER ENDPOINTS
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

ROUTE_OPENAI = "openai"

ROUTE_GOOGLE_FAST = "google_fast"

ROUTE_GOOGLE_PRO = "google_pro"

ROUTE_BEST = "best"


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

class XPANDImageError(Exception):
    """Base XPAND image-generation error."""


class XPANDImageConfigurationError(
    XPANDImageError
):
    """Missing API key or invalid configuration."""


class XPANDImageProviderError(
    XPANDImageError
):
    """Provider API returned an error."""


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
            self.mime_type.lower(),
            ".png"
        )

    @property
    def filename(self) -> str:

        provider_name = (
            self.provider
            .replace("_", "-")
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
        .replace("\x00", "")
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
        .replace("أ", "ا")
        .replace("إ", "ا")
        .replace("آ", "ا")
        .replace("ة", "ه")
        .replace("ى", "ي")
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

    normalized = normalize_arabic(
        text
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
        in SUPPORTED_ASPECT_RATIOS
    ):
        return explicit


    normalized = normalize_arabic(
        prompt
    )


    ratio_patterns = [
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


    for ratio in ratio_patterns:

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

    explicit = (
        clean_text(
            requested_size,
            20
        )
        .upper()
    )


    aliases = {
        "0.5K": "512",
        "512PX": "512",
        "512": "512",
        "1K": "1K",
        "2K": "2K",
        "4K": "4K",
    }


    if explicit in aliases:
        return aliases[explicit]


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
            "high-quality materials and textures, "
            "clean edges, coherent perspective, and "
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
                    "natural skin/material detail, realistic "
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
                    "with polished reflections and controlled "
                    "studio-grade lighting."
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

        directives.extend(
            [
                (
                    "Use cinematic composition, controlled "
                    "contrast, motivated lighting, depth, "
                    "atmospheric separation and filmic "
                    "color grading."
                ),
            ]
        )


    if contains_any(
        user_prompt,
        [
            "فاخر",
            "فخم",
            "luxury",
            "premium",
            "راقي",
        ]
    ):

        directives.extend(
            [
                (
                    "Luxury art direction: restrained, "
                    "elegant, premium materials, deliberate "
                    "lighting and sophisticated color "
                    "relationships."
                ),
            ]
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

        directives.extend(
            [
                (
                    "Produce a top-tier physically based "
                    "3D render with premium materials, "
                    "accurate reflections, realistic "
                    "shadows and professional rendering."
                ),
            ]
        )


    quoted_texts = extract_quoted_text(
        user_prompt
    )


    if quoted_texts:

        exact_text = "\n".join(
            f'- "{item}"'
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
            f"Target aspect ratio: {aspect_ratio}."
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
            f"- {item}"
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
        "auto": "auto",
        "smart": "auto",

        "openai": ROUTE_OPENAI,
        "gpt": ROUTE_OPENAI,
        "gpt-image-2": ROUTE_OPENAI,

        "google_fast": ROUTE_GOOGLE_FAST,
        "google-fast": ROUTE_GOOGLE_FAST,
        "nano banana 2": ROUTE_GOOGLE_FAST,
        "nano-banana-2": ROUTE_GOOGLE_FAST,
        "flash": ROUTE_GOOGLE_FAST,

        "google_pro": ROUTE_GOOGLE_PRO,
        "google-pro": ROUTE_GOOGLE_PRO,
        "nano banana pro": ROUTE_GOOGLE_PRO,
        "nano-banana-pro": ROUTE_GOOGLE_PRO,
        "pro": ROUTE_GOOGLE_PRO,

        "best": ROUTE_BEST,
        "max": ROUTE_BEST,
        "premium": ROUTE_BEST,
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
) -> List[ImageRoute]:

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
            provider=provider,
            model=model,
            reason=reason,
            aspect_ratio=final_aspect_ratio,
            image_size=final_image_size,
            quality=final_quality
        )


    # -----------------------------------------------------
    # EXPLICIT MODES
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
                "OpenAI requested explicitly."
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
                "Nano Banana 2 requested explicitly."
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
                "Nano Banana Pro requested explicitly."
            )
        ]


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
                    "BEST mode: premium OpenAI "
                    "generation."
                )
            ),

            route(
                ROUTE_GOOGLE_PRO,
                GOOGLE_IMAGE_PRO_MODEL,
                (
                    "BEST mode: premium Google "
                    "generation."
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
            "بوستر",
            "poster",
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


    # Fast/high-volume request:
    if fast_request:

        return [
            route(
                ROUTE_GOOGLE_FAST,
                GOOGLE_IMAGE_FAST_MODEL,
                (
                    "Fast request: Nano Banana 2 "
                    "selected for speed and quality."
                )
            )
        ]


    # Explicit 4K:
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
                    "4K request: Nano Banana 2 "
                    "selected for native 4K output."
                )
            )
        ]


    # Complex brand / many references:
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


    # Text-heavy / precision instruction:
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


    # Premium visual request:
    if complex_professional:

        return [
            route(
                ROUTE_GOOGLE_PRO,
                GOOGLE_IMAGE_PRO_MODEL,
                (
                    "Premium professional art direction: "
                    "Nano Banana Pro selected."
                )
            )
        ]


    # General high-quality default:
    return [
        route(
            ROUTE_OPENAI,
            OPENAI_IMAGE_MODEL,
            (
                "General high-quality request: "
                "GPT-Image-2 selected as default."
            )
        )
    ]


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
) -> Dict[str, Any]:

    try:

        value = response.json()

        if isinstance(
            value,
            dict
        ):
            return value

        return {
            "data": value
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
            error.get("message")
            or
            error.get("status")
            or
            str(error)
        )

    else:

        message = (
            error
            or
            data.get("message")
            or
            data.get("detail")
            or
            data.get("raw")
            or
            f"HTTP {response.status_code}"
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
) -> Tuple[bytes, str]:

    response = requests.get(
        url,
        timeout=REQUEST_TIMEOUT
    )


    if not response.ok:

        raise XPANDImageProviderError(
            (
                "فشل تنزيل الصورة من الرابط: "
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
    ).split(";")[0]


    if not mime_type.startswith(
        "image/"
    ):

        mime_type = "image/png"


    return (
        response.content,
        mime_type
    )


def _find_inline_images(
    value: Any
) -> List[Tuple[bytes, str]]:

    found: List[
        Tuple[bytes, str]
    ] = []


    def walk(
        item: Any
    ) -> None:

        if isinstance(
            item,
            dict
        ):

            item_type = clean_text(
                item.get("type"),
                100
            ).lower()


            mime_type = clean_text(
                item.get("mime_type")
                or
                item.get("mimeType")
                or
                "",
                100
            ).lower()


            data = (
                item.get("data")
                or
                item.get("b64_json")
                or
                item.get("base64")
            )


            uri = (
                item.get("uri")
                or
                item.get("url")
            )


            looks_like_image = (
                item_type == "image"
                or
                mime_type.startswith(
                    "image/"
                )
                or
                "b64_json" in item
            )


            if (
                looks_like_image
                and
                isinstance(
                    data,
                    str
                )
                and
                data.strip()
            ):

                try:

                    raw = base64.b64decode(
                        data
                    )

                    if raw:

                        found.append(
                            (
                                raw,
                                mime_type
                                or
                                "image/png"
                            )
                        )

                except Exception:

                    pass


            elif (
                looks_like_image
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
        Tuple[bytes, str]
    ] = []


    hashes = set()


    for image_bytes, mime_type in found:

        signature = (
            len(image_bytes),
            image_bytes[:64]
        )


        if signature in hashes:
            continue


        hashes.add(
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
            int(number or 1),
            4
        )
    )


    payload: Dict[str, Any] = {
        "model":
            route.model,

        "prompt":
            prompt,

        "n":
            number,

        "size":
            openai_size_for_ratio(
                route.aspect_ratio
            ),

        "quality":
            (
                route.quality
                if route.quality
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
                f"Bearer {OPENAI_API_KEY}",

            "Content-Type":
                "application/json",
        },
        json=payload,
        timeout=REQUEST_TIMEOUT
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

        results.append(
            GeneratedImage(
                image_bytes=image_bytes,
                mime_type=(
                    mime_type
                    or
                    "image/png"
                ),
                provider=ROUTE_OPENAI,
                model=route.model,
                prompt=prompt,
                original_prompt=(
                    original_prompt
                ),
                aspect_ratio=(
                    route.aspect_ratio
                ),
                image_size=(
                    payload["size"]
                ),
                quality=(
                    route.quality
                ),
                route_reason=(
                    route.reason
                ),
                request_id=(
                    request_id
                    or
                    (
                        "oa-"
                        +
                        uuid
                        .uuid4()
                        .hex[:10]
                    )
                ),
                metadata={
                    "index":
                        index,

                    "provider_size":
                        payload["size"],

                    "requested_image_size":
                        route.image_size,
                }
            )
        )


    return results


# =========================================================
# GEMINI GENERATION
# =========================================================

def generate_with_gemini(
    prompt: str,
    original_prompt: str,
    route: ImageRoute,
    number: int = 1
) -> List[GeneratedImage]:

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
            int(number or 1),
            4
        )
    )


    image_size = (
        route.image_size
        if route.image_size
        in SUPPORTED_GOOGLE_IMAGE_SIZES
        else
        "1K"
    )


    #
    # Current Gemini Interactions API.
    #
    # We request inline JPEG so the Telegram bot can
    # immediately send the bytes without temporary hosting.
    #
    payload: Dict[str, Any] = {
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

            "delivery":
                "inline",
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
        json=payload,
        timeout=REQUEST_TIMEOUT
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
                "لكن ما لقيت صورة بالنتيجة."
            )
        )


    interaction_id = clean_text(
        data.get("id"),
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

        results.append(
            GeneratedImage(
                image_bytes=image_bytes,
                mime_type=(
                    mime_type
                    or
                    "image/jpeg"
                ),
                provider=route.provider,
                model=route.model,
                prompt=prompt,
                original_prompt=(
                    original_prompt
                ),
                aspect_ratio=(
                    route.aspect_ratio
                ),
                image_size=(
                    image_size
                ),
                quality=(
                    route.quality
                ),
                route_reason=(
                    route.reason
                ),
                request_id=(
                    interaction_id
                    or
                    (
                        "gg-"
                        +
                        uuid
                        .uuid4()
                        .hex[:10]
                    )
                ),
                metadata={
                    "index":
                        index,

                    "interaction_id":
                        interaction_id,
                }
            )
        )


    return results


# =========================================================
# FALLBACK LOGIC
# =========================================================

def fallback_route_for(
    failed_route: ImageRoute
) -> Optional[ImageRoute]:

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
                    "OpenAI generation failure."
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
                    "Gemini generation failure."
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
) -> List[GeneratedImage]:

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
                number
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
                number
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
    """
    Main XPAND image-generation entry point.

    Examples:

        generate_image(
            "اعمللي إعلان عطر فاخر على خلفية سودا"
        )

        generate_image(
            "اعملها 4K سينمائية",
            mode="auto",
            aspect_ratio="16:9"
        )

        generate_image(
            "بوستر إعلاني عالمي",
            mode="best"
        )
    """

    started = time.monotonic()


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
            reference_count
    )


    primary_route = routes[0]


    enhanced_prompt = (
        build_professional_prompt(
            original_prompt,
            primary_route.aspect_ratio,
            primary_route.image_size
        )
    )


    results: List[
        GeneratedImage
    ] = []


    errors: List[str] = []


    executed_provider_models = set()


    for route in routes:

        key = (
            route.provider,
            route.model
        )


        if key in executed_provider_models:
            continue


        executed_provider_models.add(
            key
        )


        try:

            generated = _run_route(
                route,
                enhanced_prompt,
                original_prompt,
                number
            )


            results.extend(
                generated
            )


        except Exception as error:

            errors.append(
                (
                    f"{route.provider}/"
                    f"{route.model}: "
                    f"{clean_text(error, 3000)}"
                )
            )


            #
            # BEST mode already has another premium route.
            # Don't introduce extra fallback requests here.
            #
            if (
                len(routes) > 1
                or
                not allow_fallback
            ):
                continue


            fallback = fallback_route_for(
                route
            )


            if fallback is None:
                continue


            fallback_key = (
                fallback.provider,
                fallback.model
            )


            if (
                fallback_key
                in executed_provider_models
            ):
                continue


            executed_provider_models.add(
                fallback_key
            )


            try:

                fallback_images = (
                    _run_route(
                        fallback,
                        enhanced_prompt,
                        original_prompt,
                        number
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
        time.monotonic()
        -
        started,
        3
    )


    if not results:

        readable_errors = (
            "\n".join(
                errors
            )
            or
            "Unknown generation failure."
        )


        raise XPANDImageProviderError(
            (
                "فشل توليد الصورة من كل "
                "المحركات المتاحة.\n"
                +
                readable_errors
            )
        )


    return ImageGenerationResponse(
        ok=True,
        images=results,
        selected_route=(
            routes[0].provider
            if routes
            else
            ""
        ),
        routes=routes,
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

def get_image_engine_status() -> Dict[str, Any]:

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
        " XPAND SMART IMAGE ENGINE V1.0"
    )
    print(
        "======================================"
    )
    print("")

    print(
        "OpenAI:",
        (
            "READY"
            if status[
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
            if status[
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
            if status[
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
            if status[
                "supports_best_mode"
            ]
            else
            "needs both API keys"
        )
    )

    print("")
