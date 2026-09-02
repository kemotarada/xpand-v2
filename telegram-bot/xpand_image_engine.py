# =========================================================
# XPAND SMART IMAGE ENGINE V1.2
#
# Professional multi-model image generation for XPAND.
#
# Providers:
# - OpenAI GPT-Image-2
# - Google Gemini 3 Pro Image / Nano Banana Pro
# - Google Gemini 3.1 Flash Image / Nano Banana 2
#
# Modes:
# - auto
# - fast
# - openai
# - google_fast
# - google_pro
# - pro       -> Fusion Pipeline
# - best      -> Stronger Fusion Pipeline
# - compare   -> Separate outputs from multiple models
#
# FUSION PIPELINE:
# - Stage 1: Nano Banana Pro builds the base image
# - Stage 2: GPT-Image-2 refines the SAME image
#
# BEST:
# - same fusion idea, but with stronger direction
# - can generate multiple fused final images
#
# COMPARE:
# - returns separate images from different models
#
# Existing requirement:
# requests>=2.32.0,<3
# =========================================================

from __future__ import annotations

import base64
import io
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
ENGINE_VERSION = "1.2"


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

OPENAI_IMAGE_EDITS_URL = (
    "https://api.openai.com/v1/images/edits"
)

GEMINI_INTERACTIONS_URL = (
    "https://generativelanguage.googleapis.com/"
    "v1beta/interactions"
)


# =========================================================
# MODE NAMES
# =========================================================

MODE_AUTO = "auto"
MODE_FAST = "fast"
MODE_OPENAI = "openai"
MODE_GOOGLE_FAST = "google_fast"
MODE_GOOGLE_PRO = "google_pro"
MODE_PRO = "pro"
MODE_BEST = "best"
MODE_COMPARE = "compare"

PROVIDER_OPENAI = "openai"
PROVIDER_GOOGLE_FAST = "google_fast"
PROVIDER_GOOGLE_PRO = "google_pro"

PROVIDER_FUSION_PRO = "fusion_pro"
PROVIDER_FUSION_BEST = "fusion_best"


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
    """Base XPAND image error."""


class XPANDImageConfigurationError(XPANDImageError):
    """Missing configuration."""


class XPANDImageProviderError(XPANDImageError):
    """Provider failure."""


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
    metadata: Dict[str, Any] = field(default_factory=dict)

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
        provider_name = self.provider.replace("_", "-")
        unique = self.request_id or uuid.uuid4().hex[:10]
        return f"XPAND-{provider_name}-{unique}{self.extension}"


@dataclass
class ImageGenerationResponse:
    ok: bool
    images: List[GeneratedImage]
    selected_route: str
    routes: List[ImageRoute]
    original_prompt: str
    enhanced_prompt: str
    elapsed_seconds: float
    errors: List[str] = field(default_factory=list)


# =========================================================
# TEXT HELPERS
# =========================================================

def clean_text(
    value: Any,
    max_length: int = 12000
) -> str:
    return (
        str(value if value is not None else "")
        .replace("\x00", "")
        .strip()[:max_length]
    )


def normalize_arabic(value: Any) -> str:
    text = clean_text(value, 20000).lower()

    text = (
        text.replace("أ", "ا")
        .replace("إ", "ا")
        .replace("آ", "ا")
        .replace("ة", "ه")
        .replace("ى", "ي")
        .replace("ؤ", "و")
        .replace("ئ", "ي")
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
    source = normalize_arabic(text)
    return any(
        normalize_arabic(marker) in source
        for marker in markers
    )


def extract_quoted_text(prompt: str) -> List[str]:
    patterns = [
        r'"([^"]+)"',
        r"'([^']+)'",
        r"“([^”]+)”",
        r"«([^»]+)»",
    ]

    results: List[str] = []

    for pattern in patterns:
        for match in re.findall(pattern, prompt):
            value = clean_text(match, 1000)
            if value and value not in results:
                results.append(value)

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

    if explicit in SUPPORTED_ASPECT_RATIOS:
        return explicit

    normalized = normalize_arabic(prompt)

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
            "اعلى دقه",
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
        raise XPANDImageError("وصف الصورة فاضي.")

    directives: List[str] = [
        (
            "Create a premium professional image based strictly "
            "on the user's requested concept."
        ),
        (
            "Preserve the user's subject, intent, requested objects, "
            "environment, mood, and constraints."
        ),
        (
            "Use high-quality composition, believable lighting, "
            "clean perspective, refined textures, polished finishing, "
            "and commercial-grade output."
        ),
        (
            "Avoid accidental extra objects, malformed details, "
            "duplicate subjects, visual clutter, broken anatomy, "
            "random text, fake watermarks, and unnecessary logos."
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
            "Use photorealistic commercial photography quality."
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
                "Treat this as premium product advertising.",
                (
                    "Keep the product dominant, cleanly separated "
                    "from the background, with studio-grade reflections."
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
                    "international advertising campaign."
                ),
                (
                    "Use a polished visual hierarchy and leave clean space "
                    "for copy when useful."
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
                "Use cinematic lighting, controlled contrast, atmospheric "
                "depth, and refined filmic color grading."
            )
        )

    quoted_texts = extract_quoted_text(user_prompt)
    if quoted_texts:
        lines = "\n".join(
            f'- "{item}"'
            for item in quoted_texts
        )
        directives.append(
            (
                "The following quoted text must be rendered exactly as written, "
                "without translation, rewriting, or spelling changes:\n"
                + lines
            )
        )

    directives.append(f"Target aspect ratio: {aspect_ratio}.")
    directives.append(f"Target output size intent: {image_size}.")

    return (
        "USER REQUEST:\n"
        + user_prompt
        + "\n\n"
        + "XPAND PROFESSIONAL ART DIRECTION:\n"
        + "\n".join(f"- {item}" for item in directives)
    )


def build_refinement_prompt(
    original_user_prompt: str,
    *,
    stronger: bool = False
) -> str:
    original_user_prompt = clean_text(
        original_user_prompt,
        10000
    )

    directives: List[str] = [
        "Edit the provided image and refine it into a stronger final version.",
        "Preserve the same core subject, same concept, and same main composition.",
        "Do not replace the product or main subject with a different one.",
        "Improve cleanliness, realism, lighting, sharpness, textures, hierarchy, and finish.",
        "Fix minor visual issues if present.",
        "Keep the result premium, coherent, and professional.",
        "Do not add random watermarks, fake logos, or unrelated objects.",
    ]

    if contains_any(
        original_user_prompt,
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
        ]
    ):
        directives.extend(
            [
                "Preserve the same product identity and hero-shot intent.",
                "Improve edge definition, reflections, product materials, and premium advertising finish.",
            ]
        )

    quoted_texts = extract_quoted_text(original_user_prompt)
    if quoted_texts:
        lines = "\n".join(
            f'- "{item}"'
            for item in quoted_texts
        )
        directives.append(
            (
                "If these text elements appear in the design, keep them exact:\n"
                + lines
            )
        )

    if stronger:
        directives.extend(
            [
                "Push the result to a more premium, agency-level final look.",
                "Increase polish, depth, luxury feel, and commercial impact.",
                "Improve typography clarity if text exists.",
                "Make the output feel like a final campaign-quality key visual.",
            ]
        )

    return (
        "ORIGINAL USER REQUEST:\n"
        + original_user_prompt
        + "\n\n"
        + "XPAND REFINEMENT INSTRUCTIONS:\n"
        + "\n".join(f"- {item}" for item in directives)
    )


# =========================================================
# MODE RESOLUTION
# =========================================================

def normalize_mode(mode: str) -> str:
    value = clean_text(
        mode,
        40
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
        "flash": MODE_GOOGLE_FAST,

        "google_pro": MODE_GOOGLE_PRO,
        "google-pro": MODE_GOOGLE_PRO,
        "nano banana pro": MODE_GOOGLE_PRO,
        "nano-banana-pro": MODE_GOOGLE_PRO,

        "pro": MODE_PRO,
        "fusion": MODE_PRO,
        "fusion_pro": MODE_PRO,
        "fusion-pro": MODE_PRO,

        "best": MODE_BEST,
        "max": MODE_BEST,
        "ultimate": MODE_BEST,
        "fusion_best": MODE_BEST,
        "fusion-best": MODE_BEST,

        "compare": MODE_COMPARE,
        "multi": MODE_COMPARE,
    }

    return aliases.get(
        value,
        MODE_AUTO
    )


def resolve_effective_mode(
    prompt: str,
    mode: str = "",
    reference_count: int = 0
) -> str:
    chosen = normalize_mode(
        mode or DEFAULT_MODE
    )

    if chosen != MODE_AUTO:
        return chosen

    fast_request = contains_any(
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
    )

    strongest_request = contains_any(
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
    )

    professional_request = contains_any(
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

    product_or_branding = contains_any(
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

    precision_request = contains_any(
        prompt,
        [
            "اكتب",
            "اكتب النص",
            "النص التالي",
            "text",
            "headline",
            "title",
            "typography",
            "preserve",
            "exact",
            "high fidelity",
            "حافظ على",
            "بدقة",
            "دقيق",
        ]
    )

    needs_4k = contains_any(
        prompt,
        [
            "4k",
            "4 k",
            "فور كي",
            "اعلى دقه",
            "أعلى دقة",
            "للطباعة",
            "print quality",
        ]
    )

    if fast_request:
        return MODE_FAST

    if strongest_request:
        return MODE_BEST

    if professional_request and product_or_branding:
        return MODE_PRO

    if needs_4k and professional_request:
        return MODE_PRO

    if precision_request:
        return MODE_OPENAI

    if product_or_branding and reference_count >= 2:
        return MODE_PRO

    if professional_request:
        return MODE_GOOGLE_PRO

    return MODE_OPENAI


def build_route(
    provider: str,
    model: str,
    reason: str,
    aspect_ratio: str,
    image_size: str,
    quality: str
) -> ImageRoute:
    return ImageRoute(
        provider=provider,
        model=model,
        reason=reason,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        quality=quality,
    )


def select_routes_for_mode(
    effective_mode: str,
    prompt: str,
    aspect_ratio: str,
    image_size: str,
    quality: str
) -> List[ImageRoute]:
    if effective_mode == MODE_FAST:
        return [
            build_route(
                PROVIDER_GOOGLE_FAST,
                GOOGLE_IMAGE_FAST_MODEL,
                "FAST mode: Nano Banana 2 selected.",
                aspect_ratio,
                image_size,
                quality,
            )
        ]

    if effective_mode == MODE_OPENAI:
        return [
            build_route(
                PROVIDER_OPENAI,
                OPENAI_IMAGE_MODEL,
                "OpenAI selected.",
                aspect_ratio,
                image_size,
                quality,
            )
        ]

    if effective_mode == MODE_GOOGLE_FAST:
        return [
            build_route(
                PROVIDER_GOOGLE_FAST,
                GOOGLE_IMAGE_FAST_MODEL,
                "Nano Banana 2 selected.",
                aspect_ratio,
                image_size,
                quality,
            )
        ]

    if effective_mode == MODE_GOOGLE_PRO:
        return [
            build_route(
                PROVIDER_GOOGLE_PRO,
                GOOGLE_IMAGE_PRO_MODEL,
                "Nano Banana Pro selected.",
                aspect_ratio,
                image_size,
                quality,
            )
        ]

    if effective_mode == MODE_COMPARE:
        return [
            build_route(
                PROVIDER_OPENAI,
                OPENAI_IMAGE_MODEL,
                "COMPARE mode: GPT-Image-2 selected.",
                aspect_ratio,
                image_size,
                quality,
            ),
            build_route(
                PROVIDER_GOOGLE_PRO,
                GOOGLE_IMAGE_PRO_MODEL,
                "COMPARE mode: Nano Banana Pro selected.",
                aspect_ratio,
                image_size,
                quality,
            ),
            build_route(
                PROVIDER_GOOGLE_FAST,
                GOOGLE_IMAGE_FAST_MODEL,
                "COMPARE mode: Nano Banana 2 selected.",
                aspect_ratio,
                image_size,
                quality,
            ),
        ]

    return [
        build_route(
            PROVIDER_OPENAI,
            OPENAI_IMAGE_MODEL,
            "Default OpenAI route.",
            aspect_ratio,
            image_size,
            quality,
        )
    ]


def distribute_image_count(
    routes: List[ImageRoute],
    requested_number: int
) -> List[int]:
    if not routes:
        return []

    requested_number = max(
        1,
        min(int(requested_number or 1), 12)
    )

    if len(routes) == 1:
        return [requested_number]

    total_target = max(
        requested_number,
        len(routes)
    )

    counts = [1 for _ in routes]
    remaining = total_target - len(routes)
    index = 0

    while remaining > 0:
        counts[index % len(counts)] += 1
        remaining -= 1
        index += 1

    return counts


# =========================================================
# SIZE MAPPING
# =========================================================

def openai_size_for_ratio(aspect_ratio: str) -> str:
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

def _safe_json(response: requests.Response) -> Dict[str, Any]:
    try:
        value = response.json()
        if isinstance(value, dict):
            return value
        return {"data": value}
    except Exception:
        return {"raw": clean_text(response.text, 5000)}


def _provider_error_message(
    provider: str,
    response: requests.Response
) -> str:
    data = _safe_json(response)
    error = data.get("error")

    if isinstance(error, dict):
        message = (
            error.get("message")
            or error.get("status")
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

    return f"{provider}: {clean_text(message, 3000)}"


# =========================================================
# IMAGE EXTRACTION HELPERS
# =========================================================

def _download_image_url(url: str) -> Tuple[bytes, str]:
    response = requests.get(
        url,
        timeout=REQUEST_TIMEOUT
    )

    if not response.ok:
        raise XPANDImageProviderError(
            f"فشل تنزيل الصورة: {response.status_code}"
        )

    mime_type = clean_text(
        response.headers.get("Content-Type", ""),
        100
    ).split(";")[0]

    if not mime_type.startswith("image/"):
        mime_type = "image/png"

    return response.content, mime_type


def _decode_base64_image(data: str) -> Optional[bytes]:
    value = clean_text(
        data,
        100000000
    )

    if not value:
        return None

    if value.startswith("data:image/"):
        try:
            value = value.split(",", 1)[1]
        except Exception:
            return None

    try:
        raw = base64.b64decode(value)
        if not raw:
            return None
        return raw
    except Exception:
        return None


def _find_inline_images(value: Any) -> List[Tuple[bytes, str]]:
    found: List[Tuple[bytes, str]] = []

    def walk(item: Any) -> None:
        if isinstance(item, dict):
            item_type = clean_text(
                item.get("type"),
                100
            ).lower()

            mime_type = clean_text(
                item.get("mime_type")
                or item.get("mimeType")
                or "",
                100
            ).lower()

            possible_data = [
                item.get("data"),
                item.get("b64_json"),
                item.get("base64"),
            ]

            looks_like_image = (
                item_type == "image"
                or mime_type.startswith("image/")
                or "b64_json" in item
            )

            if looks_like_image:
                for data in possible_data:
                    if isinstance(data, str):
                        raw = _decode_base64_image(data)
                        if raw:
                            found.append(
                                (
                                    raw,
                                    mime_type or "image/png"
                                )
                            )
                            break

                uri = item.get("uri") or item.get("url")
                if (
                    isinstance(uri, str)
                    and uri.startswith(("http://", "https://"))
                ):
                    try:
                        found.append(_download_image_url(uri))
                    except Exception:
                        pass

            for child in item.values():
                walk(child)

        elif isinstance(item, list):
            for child in item:
                walk(child)

    walk(value)

    unique: List[Tuple[bytes, str]] = []
    signatures = set()

    for image_bytes, mime_type in found:
        signature = (
            len(image_bytes),
            image_bytes[:64],
        )
        if signature in signatures:
            continue
        signatures.add(signature)
        unique.append((image_bytes, mime_type))

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
            "OPENAI_API_KEY مش موجود على Railway."
        )

    number = max(
        1,
        min(int(number or 1), 4)
    )

    provider_size = openai_size_for_ratio(
        route.aspect_ratio
    )

    payload: Dict[str, Any] = {
        "model": route.model,
        "prompt": prompt,
        "n": number,
        "size": provider_size,
        "quality": (
            route.quality
            if route.quality in {
                "low",
                "medium",
                "high",
                "auto",
            }
            else "high"
        ),
    }

    response = requests.post(
        OPENAI_IMAGE_GENERATION_URL,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )

    if not response.ok:
        raise XPANDImageProviderError(
            _provider_error_message("OpenAI", response)
        )

    data = _safe_json(response)
    images = _find_inline_images(data)

    if not images:
        raise XPANDImageProviderError(
            "OpenAI رجع استجابة ناجحة لكن ما لقيت صورة."
        )

    request_id = clean_text(
        response.headers.get("x-request-id", ""),
        200
    )

    results: List[GeneratedImage] = []

    for index, (image_bytes, mime_type) in enumerate(images[:number]):
        unique_request_id = (
            request_id
            or ("oa-" + uuid.uuid4().hex[:10])
        )

        if number > 1:
            unique_request_id = f"{unique_request_id}-{index + 1}"

        results.append(
            GeneratedImage(
                image_bytes=image_bytes,
                mime_type=mime_type or "image/png",
                provider=PROVIDER_OPENAI,
                model=route.model,
                prompt=prompt,
                original_prompt=original_prompt,
                aspect_ratio=route.aspect_ratio,
                image_size=provider_size,
                quality=route.quality,
                route_reason=route.reason,
                request_id=unique_request_id,
                metadata={
                    "provider_size": provider_size,
                    "requested_image_size": route.image_size,
                    "generation_type": "direct_generation",
                },
            )
        )

    return results


# =========================================================
# OPENAI EDIT / REFINEMENT
# =========================================================

def edit_with_openai(
    input_image_bytes: bytes,
    input_mime_type: str,
    prompt: str,
    original_prompt: str,
    route: ImageRoute,
    *,
    fusion_provider: str,
    fusion_model_label: str,
    stage1_metadata: Optional[Dict[str, Any]] = None,
    stage1_request_id: str = "",
    stage1_route_reason: str = "",
) -> GeneratedImage:
    if not OPENAI_API_KEY:
        raise XPANDImageConfigurationError(
            "OPENAI_API_KEY مش موجود على Railway."
        )

    provider_size = openai_size_for_ratio(
        route.aspect_ratio
    )

    files = [
        (
            "image[]",
            (
                "input.png",
                input_image_bytes,
                input_mime_type or "image/png",
            ),
        )
    ]

    data = {
        "model": route.model,
        "prompt": prompt,
        "size": provider_size,
        "quality": (
            route.quality
            if route.quality in {
                "low",
                "medium",
                "high",
                "auto",
            }
            else "high"
        ),
        "n": "1",
    }

    response = requests.post(
        OPENAI_IMAGE_EDITS_URL,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        },
        data=data,
        files=files,
        timeout=REQUEST_TIMEOUT,
    )

    if not response.ok:
        raise XPANDImageProviderError(
            _provider_error_message("OpenAI Edit", response)
        )

    payload = _safe_json(response)
    images = _find_inline_images(payload)

    if not images:
        raise XPANDImageProviderError(
            "OpenAI edit رجع استجابة ناجحة لكن ما لقيت صورة."
        )

    image_bytes, mime_type = images[0]

    request_id = clean_text(
        response.headers.get("x-request-id", ""),
        200
    ) or ("oe-" + uuid.uuid4().hex[:10])

    return GeneratedImage(
        image_bytes=image_bytes,
        mime_type=mime_type or "image/png",
        provider=fusion_provider,
        model=fusion_model_label,
        prompt=prompt,
        original_prompt=original_prompt,
        aspect_ratio=route.aspect_ratio,
        image_size=provider_size,
        quality=route.quality,
        route_reason=(
            "Fusion refinement complete. "
            + stage1_route_reason
            + " -> OpenAI GPT-Image-2 refinement."
        ),
        request_id=request_id,
        metadata={
            "generation_type": "fusion_refinement",
            "stage1": stage1_metadata or {},
            "stage1_request_id": stage1_request_id,
            "stage2_model": route.model,
            "stage2_provider": PROVIDER_OPENAI,
            "requested_image_size": route.image_size,
            "final_provider_size": provider_size,
        },
    )


# =========================================================
# GEMINI GENERATION
# =========================================================

def _generate_one_with_gemini(
    prompt: str,
    original_prompt: str,
    route: ImageRoute,
    index: int = 0
) -> GeneratedImage:
    if not GEMINI_API_KEY:
        raise XPANDImageConfigurationError(
            "GEMINI_API_KEY مش موجود على Railway."
        )

    image_size = (
        route.image_size
        if route.image_size in SUPPORTED_GOOGLE_IMAGE_SIZES
        else "1K"
    )

    payload: Dict[str, Any] = {
        "model": route.model,
        "input": prompt,
        "response_format": {
            "type": "image",
            "aspect_ratio": route.aspect_ratio,
            "image_size": image_size,
        },
    }

    response = requests.post(
        GEMINI_INTERACTIONS_URL,
        headers={
            "x-goog-api-key": GEMINI_API_KEY,
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )

    if not response.ok:
        raise XPANDImageProviderError(
            _provider_error_message("Gemini", response)
        )

    data = _safe_json(response)
    images = _find_inline_images(data)

    if not images:
        raise XPANDImageProviderError(
            "Gemini رجع استجابة ناجحة لكن ما لقيت output image."
        )

    image_bytes, mime_type = images[0]

    interaction_id = clean_text(
        data.get("id"),
        200
    ) or ("gg-" + uuid.uuid4().hex[:10])

    if index > 0:
        interaction_id = f"{interaction_id}-{index + 1}"

    return GeneratedImage(
        image_bytes=image_bytes,
        mime_type=mime_type or "image/jpeg",
        provider=route.provider,
        model=route.model,
        prompt=prompt,
        original_prompt=original_prompt,
        aspect_ratio=route.aspect_ratio,
        image_size=image_size,
        quality=route.quality,
        route_reason=route.reason,
        request_id=interaction_id,
        metadata={
            "generation_type": "direct_generation",
            "google_response_format": {
                "type": "image",
                "aspect_ratio": route.aspect_ratio,
                "image_size": image_size,
            },
        },
    )


def generate_with_gemini(
    prompt: str,
    original_prompt: str,
    route: ImageRoute,
    number: int = 1
) -> List[GeneratedImage]:
    number = max(
        1,
        min(int(number or 1), 4)
    )

    results: List[GeneratedImage] = []
    errors: List[str] = []

    for index in range(number):
        try:
            image = _generate_one_with_gemini(
                prompt=prompt,
                original_prompt=original_prompt,
                route=route,
                index=index,
            )
            results.append(image)
        except Exception as error:
            errors.append(clean_text(error, 3000))

    if not results:
        raise XPANDImageProviderError(
            f"Gemini {route.model} فشل.\n" + "\n".join(errors)
        )

    return results


# =========================================================
# GENERIC ROUTE RUNNER
# =========================================================

def _run_direct_route(
    route: ImageRoute,
    enhanced_prompt: str,
    original_prompt: str,
    number: int
) -> List[GeneratedImage]:
    if route.provider == PROVIDER_OPENAI:
        return generate_with_openai(
            prompt=enhanced_prompt,
            original_prompt=original_prompt,
            route=route,
            number=number,
        )

    if route.provider in {
        PROVIDER_GOOGLE_FAST,
        PROVIDER_GOOGLE_PRO,
    }:
        return generate_with_gemini(
            prompt=enhanced_prompt,
            original_prompt=original_prompt,
            route=route,
            number=number,
        )

    raise XPANDImageError(
        f"مزود غير معروف: {route.provider}"
    )


# =========================================================
# FALLBACK FOR SINGLE DIRECT ROUTES
# =========================================================

def fallback_route_for(
    failed_route: ImageRoute
) -> Optional[ImageRoute]:
    if (
        failed_route.provider == PROVIDER_OPENAI
        and GEMINI_API_KEY
    ):
        return build_route(
            PROVIDER_GOOGLE_PRO,
            GOOGLE_IMAGE_PRO_MODEL,
            "Fallback after OpenAI failure.",
            failed_route.aspect_ratio,
            failed_route.image_size,
            failed_route.quality,
        )

    if (
        failed_route.provider in {
            PROVIDER_GOOGLE_FAST,
            PROVIDER_GOOGLE_PRO,
        }
        and OPENAI_API_KEY
    ):
        return build_route(
            PROVIDER_OPENAI,
            OPENAI_IMAGE_MODEL,
            "Fallback after Gemini failure.",
            failed_route.aspect_ratio,
            failed_route.image_size,
            failed_route.quality,
        )

    return None


# =========================================================
# FUSION PIPELINE
# =========================================================

def run_fusion_pipeline(
    original_prompt: str,
    *,
    aspect_ratio: str,
    image_size: str,
    quality: str,
    number: int = 1,
    stronger: bool = False,
) -> ImageGenerationResponse:
    started = time.monotonic()

    if not GEMINI_API_KEY:
        raise XPANDImageConfigurationError(
            "Fusion mode يحتاج GEMINI_API_KEY."
        )

    if not OPENAI_API_KEY:
        raise XPANDImageConfigurationError(
            "Fusion mode يحتاج OPENAI_API_KEY."
        )

    number = max(
        1,
        min(int(number or 1), 4)
    )

    base_route = build_route(
        PROVIDER_GOOGLE_PRO,
        GOOGLE_IMAGE_PRO_MODEL,
        (
            "Fusion stage 1: Nano Banana Pro creates "
            "the base image."
        ),
        aspect_ratio,
        image_size,
        quality,
    )

    refine_route = build_route(
        PROVIDER_OPENAI,
        OPENAI_IMAGE_MODEL,
        (
            "Fusion stage 2: GPT-Image-2 refines "
            "the same image."
        ),
        aspect_ratio,
        image_size,
        quality,
    )

    enhanced_prompt = build_professional_prompt(
        original_prompt,
        aspect_ratio,
        image_size,
    )

    refinement_prompt = build_refinement_prompt(
        original_prompt,
        stronger=stronger,
    )

    fusion_provider = (
        PROVIDER_FUSION_BEST
        if stronger
        else PROVIDER_FUSION_PRO
    )

    fusion_model_label = (
        "Nano Banana Pro -> GPT-Image-2 (BEST Fusion)"
        if stronger
        else "Nano Banana Pro -> GPT-Image-2 (Fusion)"
    )

    base_images = generate_with_gemini(
        prompt=enhanced_prompt,
        original_prompt=original_prompt,
        route=base_route,
        number=number,
    )

    final_images: List[GeneratedImage] = []
    errors: List[str] = []

    for base_image in base_images:
        try:
            refined = edit_with_openai(
                input_image_bytes=base_image.image_bytes,
                input_mime_type=base_image.mime_type,
                prompt=refinement_prompt,
                original_prompt=original_prompt,
                route=refine_route,
                fusion_provider=fusion_provider,
                fusion_model_label=fusion_model_label,
                stage1_metadata=base_image.metadata,
                stage1_request_id=base_image.request_id,
                stage1_route_reason=base_route.reason,
            )

            refined.metadata["fusion_mode"] = (
                "best" if stronger else "pro"
            )
            refined.metadata["stage1_model"] = GOOGLE_IMAGE_PRO_MODEL
            refined.metadata["stage2_model"] = OPENAI_IMAGE_MODEL

            final_images.append(refined)

        except Exception as error:
            errors.append(
                f"Fusion refine fallback: {clean_text(error, 3000)}"
            )

            fallback_image = GeneratedImage(
                image_bytes=base_image.image_bytes,
                mime_type=base_image.mime_type,
                provider=fusion_provider,
                model=(
                    "Nano Banana Pro (Fusion fallback: "
                    "OpenAI refine failed)"
                ),
                prompt=base_image.prompt,
                original_prompt=original_prompt,
                aspect_ratio=base_image.aspect_ratio,
                image_size=base_image.image_size,
                quality=base_image.quality,
                route_reason=(
                    "Fusion fallback: returned stage 1 image because "
                    "OpenAI refinement failed."
                ),
                request_id=base_image.request_id,
                metadata={
                    "generation_type": "fusion_stage1_fallback",
                    "fusion_mode": "best" if stronger else "pro",
                    "stage1_model": GOOGLE_IMAGE_PRO_MODEL,
                    "stage2_model": OPENAI_IMAGE_MODEL,
                    "stage2_failed": True,
                },
            )

            final_images.append(fallback_image)

    elapsed = round(
        time.monotonic() - started,
        3
    )

    return ImageGenerationResponse(
        ok=True,
        images=final_images,
        selected_route=MODE_BEST if stronger else MODE_PRO,
        routes=[base_route, refine_route],
        original_prompt=original_prompt,
        enhanced_prompt=enhanced_prompt,
        elapsed_seconds=elapsed,
        errors=errors,
    )


# =========================================================
# DIRECT / COMPARE EXECUTION
# =========================================================

def run_direct_or_compare(
    original_prompt: str,
    *,
    effective_mode: str,
    aspect_ratio: str,
    image_size: str,
    quality: str,
    number: int = 1,
    allow_fallback: bool = True,
) -> ImageGenerationResponse:
    started = time.monotonic()

    routes = select_routes_for_mode(
        effective_mode,
        original_prompt,
        aspect_ratio,
        image_size,
        quality,
    )

    enhanced_prompt = build_professional_prompt(
        original_prompt,
        aspect_ratio,
        image_size,
    )

    route_counts = distribute_image_count(
        routes,
        number
    )

    print(
        "🧠 XPAND IMAGE ROUTES | "
        + " | ".join(
            f"{route.provider}/{route.model} x{count}"
            for route, count in zip(routes, route_counts)
        )
    )

    results: List[GeneratedImage] = []
    errors: List[str] = []
    executed = set()

    for route, route_count in zip(routes, route_counts):
        key = (route.provider, route.model)
        if key in executed:
            continue
        executed.add(key)

        try:
            route_images = _run_direct_route(
                route=route,
                enhanced_prompt=enhanced_prompt,
                original_prompt=original_prompt,
                number=route_count,
            )
            results.extend(route_images)

        except Exception as error:
            errors.append(
                f"{route.provider}/{route.model}: {clean_text(error, 3000)}"
            )

            if len(routes) > 1 or not allow_fallback:
                continue

            fallback = fallback_route_for(route)
            if fallback is None:
                continue

            fallback_key = (fallback.provider, fallback.model)
            if fallback_key in executed:
                continue

            executed.add(fallback_key)

            try:
                fallback_images = _run_direct_route(
                    route=fallback,
                    enhanced_prompt=enhanced_prompt,
                    original_prompt=original_prompt,
                    number=route_count,
                )
                results.extend(fallback_images)
            except Exception as fallback_error:
                errors.append(
                    f"{fallback.provider}/{fallback.model}: "
                    f"{clean_text(fallback_error, 3000)}"
                )

    elapsed = round(
        time.monotonic() - started,
        3
    )

    if not results:
        raise XPANDImageProviderError(
            "فشل توليد الصورة من كل المحركات المتاحة.\n"
            + ("\n".join(errors) or "Unknown image-generation failure.")
        )

    return ImageGenerationResponse(
        ok=True,
        images=results,
        selected_route=effective_mode,
        routes=routes,
        original_prompt=original_prompt,
        enhanced_prompt=enhanced_prompt,
        elapsed_seconds=elapsed,
        errors=errors,
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
    original_prompt = clean_text(
        user_prompt,
        10000
    )

    if not original_prompt:
        raise XPANDImageError("لازم يكون في وصف للصورة.")

    final_aspect_ratio = detect_aspect_ratio(
        original_prompt,
        aspect_ratio,
    )

    final_image_size = detect_image_size(
        original_prompt,
        image_size,
    )

    final_quality = detect_quality(
        original_prompt,
        quality,
    )

    effective_mode = resolve_effective_mode(
        original_prompt,
        mode=mode,
        reference_count=reference_count,
    )

    print(
        f"🎯 XPAND EFFECTIVE MODE: {effective_mode}"
    )

    if effective_mode == MODE_PRO:
        return run_fusion_pipeline(
            original_prompt,
            aspect_ratio=final_aspect_ratio,
            image_size=final_image_size,
            quality=final_quality,
            number=number,
            stronger=False,
        )

    if effective_mode == MODE_BEST:
        return run_fusion_pipeline(
            original_prompt,
            aspect_ratio=final_aspect_ratio,
            image_size=final_image_size,
            quality=final_quality,
            number=number,
            stronger=True,
        )

    return run_direct_or_compare(
        original_prompt,
        effective_mode=effective_mode,
        aspect_ratio=final_aspect_ratio,
        image_size=final_image_size,
        quality=final_quality,
        number=number,
        allow_fallback=allow_fallback,
    )


# =========================================================
# STATUS
# =========================================================

def get_image_engine_status() -> Dict[str, Any]:
    return {
        "ok": bool(OPENAI_API_KEY or GEMINI_API_KEY),
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "providers": {
            "openai": {
                "configured": bool(OPENAI_API_KEY),
                "model": OPENAI_IMAGE_MODEL,
            },
            "google_fast": {
                "configured": bool(GEMINI_API_KEY),
                "model": GOOGLE_IMAGE_FAST_MODEL,
            },
            "google_pro": {
                "configured": bool(GEMINI_API_KEY),
                "model": GOOGLE_IMAGE_PRO_MODEL,
            },
        },
        "default_mode": DEFAULT_MODE,
        "default_quality": DEFAULT_QUALITY,
        "supports_best_mode": bool(OPENAI_API_KEY and GEMINI_API_KEY),
        "supports_fusion_mode": bool(OPENAI_API_KEY and GEMINI_API_KEY),
        "fusion_pipeline": [
            GOOGLE_IMAGE_PRO_MODEL,
            OPENAI_IMAGE_MODEL,
        ],
        "compare_mode_models": [
            OPENAI_IMAGE_MODEL,
            GOOGLE_IMAGE_PRO_MODEL,
            GOOGLE_IMAGE_FAST_MODEL,
        ],
        "telegram_ready": True,
    }


# =========================================================
# ROUTE DESCRIPTION
# =========================================================

def describe_route(route: ImageRoute) -> str:
    labels = {
        PROVIDER_OPENAI: "GPT-Image-2",
        PROVIDER_GOOGLE_FAST: "Nano Banana 2",
        PROVIDER_GOOGLE_PRO: "Nano Banana Pro",
    }

    label = labels.get(route.provider, route.model)

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
    status = get_image_engine_status()

    print("")
    print("======================================")
    print(" XPAND SMART IMAGE ENGINE V1.2")
    print("======================================")
    print("")

    print(
        "OpenAI:",
        "READY" if status["providers"]["openai"]["configured"] else "missing key",
        "|",
        OPENAI_IMAGE_MODEL
    )

    print(
        "Nano Banana 2:",
        "READY" if status["providers"]["google_fast"]["configured"] else "missing key",
        "|",
        GOOGLE_IMAGE_FAST_MODEL
    )

    print(
        "Nano Banana Pro:",
        "READY" if status["providers"]["google_pro"]["configured"] else "missing key",
        "|",
        GOOGLE_IMAGE_PRO_MODEL
    )

    print(
        "Fusion mode:",
        "READY" if status["supports_fusion_mode"] else "needs both API keys"
    )

    print("")

    test_prompt = (
        "اعمللي بوستر منتج فاخر جدا بأفضل نتيجة ممكنة "
        "لعبوة عطر سوداء فخمة بإضاءة سينمائية"
    )

    print("Auto effective mode:")
    print(" -", resolve_effective_mode(test_prompt))

    print("")
    print("Expected for the above prompt:")
    print(" - best")
    print("")

    print("COMPARE routes for 3 images:")
    compare_routes = select_routes_for_mode(
        MODE_COMPARE,
        test_prompt,
        "4:5",
        "2K",
        "high",
    )
    compare_counts = distribute_image_count(
        compare_routes,
        3
    )
    for route, count in zip(compare_routes, compare_counts):
        print(f" - {route.model} x{count}")

    print("")
    print("Fusion pipeline:")
    print(f" - Stage 1: {GOOGLE_IMAGE_PRO_MODEL}")
    print(f" - Stage 2: {OPENAI_IMAGE_MODEL}")
    print("")
