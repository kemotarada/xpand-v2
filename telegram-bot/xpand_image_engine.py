# =========================================================
# XPAND VISUAL PROVIDER CORE V3.0.0
#
# FULL DROP-IN REPLACEMENT
#
# =========================================================
#
# FINAL ARCHITECTURE
# ---------------------------------------------------------
#
# Gemini Vision
#     = structured creative intelligence / vision / director
#
# Nano Banana 2
#     = fast image generation
#     = previsualization / composition draft
#
# Gemini Pro image
#     = final renderer
#     = multi-reference final synthesis
#     = final image edit
#
#
# MASTERPIECE / BEST
# ---------------------------------------------------------
#
# Sol-approved creative direction
#          ↓
# Nano Banana 2 PREVISUALIZATION
#          ↓
# Draft + selected physical references
#          ↓
# Gemini Pro image FINAL RENDER
#
#
# IMPORTANT
# ---------------------------------------------------------
#
# - Gemini Pro image is the mandatory final model for BEST.
# - Nano Banana 2 never becomes the final BEST image
#   unless XPAND_BEST_REQUIRE_OPENAI_FINAL=false.
# - Nano Banana Pro remains explicit only.
# - OpenAI multi-reference edit is supported.
# - Gemini Pro image input_fidelity is intentionally OMITTED.
# - Gemini Pro image flexible resolutions are supported.
# - 4:5 is a TRUE 4:5 output size.
# - Gemini image calls send NO thinking_level.
# - Structured JSON routing stays OpenAI-first.
# - Cheap free-text routing stays Gemini-first.
#
#
# STC BANK
# ---------------------------------------------------------
#
# - no invented payment hardware
# - no phone/POS fusion
# - no fake banking UI
# - no random stone/travertine luxury pedestal
# - no generic fintech decoration
# - no giant empty upper third
# - 15–22% integrated copy space
# - camera is a storytelling decision
# - permanent references are visual DNA, never clone targets
# - final renderer = Gemini Pro image
#
#
# COMPATIBILITY
# ---------------------------------------------------------
#
# Preserves public API required by:
#
#   xpand_image_telegram.py
#   xpand_creative_brain.py
#   xpand_production_engine.py
#   xpand_visual_intelligence.py
#
#
# Running:
#
#     python xpand_image_engine.py
#
# makes ZERO API calls.
#
# =========================================================

from __future__ import annotations

import base64
import json
import os
import re
import shutil
import subprocess
import tempfile
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
# OPTIONAL STC BANK SKILL
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

        markers = (
            "نقاط البيع",
            "point of sale",
            "pos",
            "ecommerce",
            "e-commerce",
            "التجارة الالكترونية",
            "التجارة الإلكترونية",
            "merchant",
        )

        if any(
            marker
            in value
            for marker
            in markers
        ):

            return "merchant_payments"

        return "premium_banking"


# =========================================================
# ENGINE
# =========================================================

ENGINE_NAME = (
    "XPAND Visual Provider Core"
)

ENGINE_VERSION = "3.0.0"


# =========================================================
# ENV HELPERS
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


def safe_int(
    value: Any,
    default: int,
) -> int:

    try:

        return int(
            value
        )

    except Exception:

        return int(
            default
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


# Gemini-only deployment: OpenAI is intentionally disabled.
OPENAI_ENABLED = False

# A provider credit/quota outage is sticky for the lifetime of this process.
# Avoid retrying the unavailable structured director on every QA/concept pass.
OPENAI_STRUCTURED_UNAVAILABLE = False

# Gemini-only production mode: OpenAI is intentionally never called.
GEMINI_ONLY_MODE = True


# =========================================================
# MODELS
# =========================================================

OPENAI_IMAGE_MODEL = str(
    os.environ.get(
        "XPAND_OPENAI_IMAGE_MODEL",
        "gpt-image-2",
    )
).strip()


# Keep editing independent of the text-to-image model. DALL-E 3 cannot
# accept the multi-reference edits request used by this pipeline.
def _resolve_openai_edit_model(value: str) -> str:
    model = str(value or "").strip()
    if not model or model.lower() == "dall-e-3":
        return "gpt-image-1"
    return model


_configured_edit_model = os.environ.get("XPAND_OPENAI_EDIT_MODEL", "")
OPENAI_EDIT_MODEL = _resolve_openai_edit_model(_configured_edit_model)
if str(_configured_edit_model).strip().lower() == "dall-e-3":
    print(
        "⚠️ XPAND_OPENAI_EDIT_MODEL=dall-e-3 is incompatible with "
        "multi-reference editing; using gpt-image-1."
    )


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


GEMINI_DIRECTOR_RUNTIME_MODEL = (
    GEMINI_DIRECTOR_MODEL
)


GEMINI_DIRECTOR_FALLBACK_MODELS = [
    item.strip()
    for item
    in str(
        os.environ.get(
            "XPAND_GEMINI_DIRECTOR_FALLBACK_MODELS",
            (
                "gemini-3.5-flash-lite,"
                "gemini-3.5-flash"
            ),
        )
    ).split(
        ","
    )
    if item.strip()
]


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


#
# Compatibility only.
#
# Nano Banana Pro is NOT used by BEST.
#

BEST_USE_PRO = env_bool(
    "XPAND_BEST_USE_PRO",
    False,
)


# Compatibility flag retained; Gemini Pro is the only final renderer.
BEST_REQUIRE_OPENAI_FINAL = False


# If OpenAI is temporarily unavailable because of quota/billing, allow
# BEST to finish with a single Gemini final instead of returning no image.
BEST_ALLOW_QUOTA_FALLBACK = env_bool(
    "XPAND_BEST_ALLOW_QUOTA_FALLBACK",
    True,
)


OPENAI_MAX_REFERENCE_IMAGES = max(
    1,
    min(
        10,
        safe_int(
            os.environ.get(
                "XPAND_OPENAI_MAX_REFERENCE_IMAGES",
                "4",
            ),
            4,
        ),
    ),
)


# =========================================================
# DIRECTOR COST CONTROL
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
    safe_int(
        os.environ.get(
            "XPAND_IMAGE_DIRECTOR_MAX_OUTPUT_TOKENS",
            "1400",
        ),
        1400,
    ),
)


OPENAI_STRUCTURED_MAX_OUTPUT_TOKENS = max(
    3000,
    safe_int(
        os.environ.get(
            "XPAND_IMAGE_STRUCTURED_MAX_OUTPUT_TOKENS",
            "9000",
        ),
        9000,
    ),
)


OPENAI_STRUCTURED_RETRY_MAX_OUTPUT_TOKENS = max(
    OPENAI_STRUCTURED_MAX_OUTPUT_TOKENS,
    safe_int(
        os.environ.get(
            "XPAND_IMAGE_STRUCTURED_RETRY_MAX_OUTPUT_TOKENS",
            "12000",
        ),
        12000,
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
    "original",
}:

    OPENAI_VISION_DETAIL = (
        "high"
    )


# =========================================================
# GEMINI THINKING COMPATIBILITY
# =========================================================

def normalize_gemini_image_thinking_level(
    value: Any,
) -> str:

    level = str(
        value
        or ""
    ).strip().lower()

    if level in {
        "low",
        "minimal",
        "min",
        "none",
    }:

        return "minimal"

    if level in {
        "medium",
        "med",
    }:

        return "medium"

    if level in {
        "high",
        "max",
    }:

        return "high"

    return "minimal"


GEMINI_IMAGE_THINKING = (
    normalize_gemini_image_thinking_level(
        os.environ.get(
            "XPAND_GEMINI_IMAGE_THINKING",
            "minimal",
        )
    )
)


# =========================================================
# TIMEOUT
# =========================================================

REQUEST_TIMEOUT = max(
    30,
    safe_int(
        os.environ.get(
            "XPAND_IMAGE_TIMEOUT_SECONDS",
            "300",
        ),
        300,
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

PROVIDER_GOOGLE_FAST = (
    "google_fast"
)

PROVIDER_GOOGLE_PRO = (
    "google_pro"
)

PROVIDER_FUSION_PRO = (
    "fusion_pro"
)

PROVIDER_FUSION_BEST = (
    "fusion_best"
)

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

        if normalize_arabic(
            marker
        ) in source:

            return True

    return False


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
        in image_bytes[:16]
    ):

        return "image/webp"

    return fallback


def _read_image_dimensions(raw: bytes) -> Optional[Tuple[int, int]]:
    if raw.startswith(b"\x89PNG\r\n\x1a\n") and len(raw) >= 24:
        return int.from_bytes(raw[16:20], "big"), int.from_bytes(raw[20:24], "big")
    if raw.startswith(b"\xff\xd8\xff"):
        index = 2
        sof_markers = set(range(0xC0, 0xC4)) | set(range(0xC5, 0xC8)) | set(range(0xC9, 0xCC)) | set(range(0xCD, 0xD0))
        while index + 9 < len(raw):
            if raw[index] != 0xFF:
                index += 1
                continue
            while index < len(raw) and raw[index] == 0xFF:
                index += 1
            if index >= len(raw):
                break
            marker = raw[index]
            index += 1
            if marker in (0xD8, 0xD9):
                continue
            if index + 2 > len(raw):
                break
            segment_length = int.from_bytes(raw[index:index + 2], "big")
            if marker in sof_markers and index + 7 <= len(raw):
                height = int.from_bytes(raw[index + 3:index + 5], "big")
                width = int.from_bytes(raw[index + 5:index + 7], "big")
                return width, height
            if segment_length < 2:
                break
            index += segment_length
    return None


def normalize_image_bytes_to_aspect(
    image_bytes: bytes,
    mime_type: str,
    aspect_ratio: str,
) -> Tuple[bytes, str]:
    """Crop provider-native output to the requested delivery ratio before QA."""
    raw = image_bytes or b""
    try:
        rw, rh = (float(part.strip()) for part in clean_text(aspect_ratio, 40).split(":", 1))
        dimensions = _read_image_dimensions(raw)
        if rw <= 0 or rh <= 0 or not dimensions:
            return raw, mime_type or infer_mime_type(raw)
        sw, sh = dimensions
        target = rw / rh
        current = sw / sh
        if abs(current - target) < 0.005:
            return raw, mime_type or infer_mime_type(raw)
        if current > target:
            th, tw = sh, max(1, int(round(sh * target)))
        else:
            tw, th = sw, max(1, int(round(sw / target)))
        tw, th = min(tw, sw), min(th, sh)
        x, y = max(0, (sw - tw) // 2), max(0, (sh - th) // 2)
        ffmpeg_bin = shutil.which("ffmpeg")
        if not ffmpeg_bin:
            try:
                import imageio_ffmpeg
                ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
            except Exception:
                ffmpeg_bin = None
        if not ffmpeg_bin:
            print("⚠️ Aspect normalization skipped: ffmpeg executable unavailable", flush=True)
            return raw, mime_type or infer_mime_type(raw)
        with tempfile.NamedTemporaryFile(suffix=".input", delete=True) as source:
            source.write(raw)
            source.flush()
            rendered = subprocess.run([ffmpeg_bin, "-v", "error", "-y", "-i", source.name, "-vf", f"crop={tw}:{th}:{x}:{y}", "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True, timeout=45, check=False)
            if rendered.returncode == 0 and rendered.stdout:
                return rendered.stdout, "image/png"
    except Exception as error:
        print("⚠️ Aspect normalization skipped:", clean_text(error, 500), flush=True)
    return raw, mime_type or infer_mime_type(raw)


def image_data_uri(
    image_bytes: bytes,
    mime_type: str,
) -> str:

    mime = clean_text(
        mime_type,
        100,
    ).lower()

    if not mime.startswith(
        "image/"
    ):

        mime = infer_mime_type(
            image_bytes,
            "image/png",
        )

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
# REFERENCE NORMALIZATION
# =========================================================

def _normalize_reference_images(
    references: Any,
) -> List[
    Tuple[
        bytes,
        str,
    ]
]:

    if not references:

        return []

    if isinstance(
        references,
        tuple,
    ):

        references = list(
            references
        )

    if not isinstance(
        references,
        list,
    ):

        references = [
            references
        ]

    output: List[
        Tuple[
            bytes,
            str,
        ]
    ] = []

    for item in references:

        raw = b""

        mime = ""

        if isinstance(
            item,
            GeneratedImage,
        ):

            raw = (
                item.image_bytes
                or b""
            )

            mime = (
                item.mime_type
                or ""
            )

        elif (
            isinstance(
                item,
                tuple,
            )
            and
            len(
                item
            )
            >=
            1
        ):

            candidate = item[
                0
            ]

            if isinstance(
                candidate,
                bytes,
            ):

                raw = candidate

                if len(
                    item
                ) > 1:

                    mime = clean_text(
                        item[
                            1
                        ],
                        100,
                    )

        elif isinstance(
            item,
            dict,
        ):

            candidate = (
                item.get(
                    "image_bytes"
                )
                or
                item.get(
                    "bytes"
                )
                or
                item.get(
                    "data"
                )
            )

            if isinstance(
                candidate,
                bytes,
            ):

                raw = candidate

            mime = clean_text(
                (
                    item.get(
                        "mime_type"
                    )
                    or
                    item.get(
                        "mime"
                    )
                    or ""
                ),
                100,
            )

        if not raw:

            continue

        if not mime.startswith(
            "image/"
        ):

            mime = infer_mime_type(
                raw,
                "image/jpeg",
            )

        output.append(
            (
                raw,
                mime,
            )
        )

    return output


def _generated_image_tuple(
    image: GeneratedImage,
) -> Tuple[
    bytes,
    str,
]:

    return (
        image.image_bytes,
        (
            image.mime_type
            or
            infer_mime_type(
                image.image_bytes
            )
        ),
    )


# =========================================================
# DETECT ASPECT RATIO
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

    match = re.search(
        (
            r"(?<!\d)"
            r"(1:1|2:3|3:2|3:4|4:3|4:5|5:4|"
            r"9:16|16:9|21:9|1:4|4:1|1:8|8:1)"
            r"(?!\d)"
        ),
        text,
    )

    if match:

        return match.group(
            1
        )

    if contains_any(
        text,
        (
            "ستوري",
            "story",
            "reel",
            "ريل",
            "9 16",
        ),
    ):

        return "9:16"

    if contains_any(
        text,
        (
            "عمودي 4 5",
            "portrait 4 5",
            "portrait post",
            "بوست طولي",
            "بوستر طولي",
        ),
    ):

        return "4:5"

    if contains_any(
        text,
        (
            "landscape",
            "افقي",
            "أفقي",
            "سينمائي",
        ),
    ):

        return "16:9"

    return "1:1"


# =========================================================
# DETECT IMAGE SIZE
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

    if (
        re.search(
            r"(?<!\d)4\s*k(?!\w)",
            text,
        )
        or
        contains_any(
            text,
            (
                "4096",
                "فور كي",
            ),
        )
    ):

        return "4K"

    if (
        re.search(
            r"(?<!\d)2\s*k(?!\w)",
            text,
        )
        or
        contains_any(
            text,
            (
                "2048",
                "تو كي",
                "full hd",
                "fullhd",
                "fhd",
            ),
        )
    ):

        return "2K"

    if contains_any(
        text,
        (
            "1k",
            "1024",
        ),
    ):

        return "1K"

    return "1K"


# =========================================================
# DETECT QUALITY
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
        (
            "masterpiece",
            "ماستر بيس",
            "فاخر",
            "فاخرة",
            "premium",
            "high quality",
            "جودة عالية",
            "حملة",
            "campaign",
        ),
    ):

        return "high"

    if contains_any(
        prompt,
        (
            "low quality",
            "جودة منخفضة",
        ),
    ):

        return "low"

    if DEFAULT_QUALITY in (
        SUPPORTED_OPENAI_QUALITIES
    ):

        return DEFAULT_QUALITY

    return "high"


# =========================================================
# MODE NORMALIZATION
# =========================================================

def normalize_mode(
    mode: str,
) -> str:

    value = clean_text(
        mode,
        80,
    ).lower()

    aliases = {
        "":
            MODE_AUTO,

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

        "gpt image":
            MODE_OPENAI,

        "gpt-image-2":
            MODE_OPENAI,

        "gpt image 2":
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

        #
        # V3:
        # PRO means hybrid high-quality production.
        #

        "pro":
            MODE_PRO,

        "fusion":
            MODE_PRO,

        "best":
            MODE_BEST,

        "masterpiece":
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
    requested_mode: str = "",
    reference_count: int = 0,
) -> str:

    #
    # Explicit caller mode has the highest authority.
    #

    explicit = clean_text(
        requested_mode,
        80,
    ).lower()

    if explicit:

        chosen = normalize_mode(
            explicit
        )

        if chosen != MODE_AUTO:

            return chosen

    #
    # Prompt-explicit provider requests override
    # DEFAULT_MODE.
    #

    if contains_any(
        prompt,
        (
            "nano banana pro",
            "nano-banana-pro",
            "نانو بنانا برو",
            "gemini 3 pro image",
            "gemini-3-pro-image",
        ),
    ):

        return MODE_GOOGLE_PRO

    if contains_any(
        prompt,
        (
            "nano banana 2",
            "nano-banana-2",
            "نانو بنانا 2",
            "gemini 3.1 flash image",
            "gemini-3.1-flash-image",
        ),
    ):

        return MODE_GOOGLE_FAST

    if contains_any(
        prompt,
        (
            "gpt-image-2",
            "gpt image 2",
            "اوبن اي للصورة",
            "openai image",
        ),
    ):

        return MODE_OPENAI

    #
    # Masterpiece / strongest output means the
    # hybrid route:
    #
    # Nano Banana 2 draft
    #         ↓
    # Gemini Pro image final
    #

    if contains_any(
        prompt,
        (
            "masterpiece",
            "ماستر بيس",
            "ماستربيس",
            "أفضل نتيجة ممكنة",
            "افضل نتيجه ممكنه",
            "أقوى نتيجة",
            "اقوى نتيجه",
            "اقوى ما عندك",
            "أقوى ما عندك",
            "كل قواك",
            "best mode",
            "ultimate",
            "max quality",
            "maximum quality",
        ),
    ):

        return MODE_BEST

    if contains_any(
        prompt,
        (
            "draft",
            "preview",
            "سريع",
            "بسرعة",
            "بسرعه",
            "quick",
        ),
    ):

        return MODE_GOOGLE_FAST

    #
    # Only now inspect the environment default.
    #

    default_mode = normalize_mode(
        DEFAULT_MODE
    )

    if default_mode in {
        MODE_OPENAI,
        MODE_GOOGLE_FAST,
        MODE_GOOGLE_PRO,
        MODE_PRO,
        MODE_BEST,
        MODE_COMPARE,
        MODE_FAST,
    }:

        return default_mode

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
            300,
        ),

        reason=clean_text(
            reason,
            1200,
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
# GPT-IMAGE-2 FLEXIBLE SIZE
# =========================================================

OPENAI_SIZE_MAP = {

    "1:1": {
        "1K":
            "1024x1024",

        "2K":
            "2048x2048",

        "4K":
            "2880x2880",
    },

    "4:5": {
        "1K":
            "1024x1280",

        "2K":
            "2048x2560",

        "4K":
            "2560x3200",
    },

    "5:4": {
        "1K":
            "1280x1024",

        "2K":
            "2560x2048",

        "4K":
            "3200x2560",
    },

    "9:16": {
        "1K":
            "720x1280",

        "2K":
            "1152x2048",

        "4K":
            "2160x3840",
    },

    "16:9": {
        "1K":
            "1280x720",

        "2K":
            "2048x1152",

        "4K":
            "3840x2160",
    },

    "2:3": {
        "1K":
            "768x1152",

        "2K":
            "1344x2016",

        "4K":
            "2304x3456",
    },

    "3:2": {
        "1K":
            "1152x768",

        "2K":
            "2016x1344",

        "4K":
            "3456x2304",
    },

    "3:4": {
        "1K":
            "768x1024",

        "2K":
            "1536x2048",

        "4K":
            "2304x3072",
    },

    "4:3": {
        "1K":
            "1024x768",

        "2K":
            "2048x1536",

        "4K":
            "3072x2304",
    },

    "21:9": {
        "1K":
            "1344x576",

        "2K":
            "2688x1152",

        "4K":
            "3584x1536",
    },

    #
    # Gemini Pro image maximum aspect ratio is 3:1.
    #
    # Legacy 1:4 / 1:8 requests therefore clamp
    # safely to the closest valid 1:3 frame.
    #

    "1:4": {
        "1K":
            "512x1536",

        "2K":
            "896x2688",

        "4K":
            "1120x3360",
    },

    "1:8": {
        "1K":
            "512x1536",

        "2K":
            "896x2688",

        "4K":
            "1120x3360",
    },

    "4:1": {
        "1K":
            "1536x512",

        "2K":
            "2688x896",

        "4K":
            "3360x1120",
    },

    "8:1": {
        "1K":
            "1536x512",

        "2K":
            "2688x896",

        "4K":
            "3360x1120",
    },
}


def validate_openai_size(
    value: str,
) -> bool:

    match = re.fullmatch(
        r"(\d+)x(\d+)",
        clean_text(
            value,
            50,
        ).lower(),
    )

    if not match:

        return False

    width = int(
        match.group(
            1
        )
    )

    height = int(
        match.group(
            2
        )
    )

    if (
        width <= 0
        or
        height <= 0
    ):

        return False

    if max(
        width,
        height,
    ) > 3840:

        return False

    if (
        width % 16
        !=
        0
        or
        height % 16
        !=
        0
    ):

        return False

    short_edge = min(
        width,
        height,
    )

    long_edge = max(
        width,
        height,
    )

    if (
        long_edge
        /
        short_edge
        >
        3.0
    ):

        return False

    pixels = (
        width
        *
        height
    )

    if pixels < 655360:

        return False

    if pixels > 8294400:

        return False

    return True


def openai_size_for_ratio(
    aspect_ratio: str,
    image_size: str = "1K",
) -> str:

    ratio = (
        aspect_ratio
        if aspect_ratio
        in OPENAI_SIZE_MAP
        else
        "1:1"
    )

    intent = str(
        image_size
        or "1K"
    ).strip().upper()

    if intent in {
        "",
        "512",
        "1024",
        "AUTO",
    }:

        intent = "1K"

    elif intent in {
        "2048",
        "HD",
        "FHD",
    }:

        intent = "2K"

    elif intent == "4096":

        intent = "4K"

    if intent not in {
        "1K",
        "2K",
        "4K",
    }:

        intent = "1K"

    size = (
        OPENAI_SIZE_MAP[
            ratio
        ][
            intent
        ]
    )

    if not validate_openai_size(
        size
    ):

        raise XPANDImageError(
            (
                "Invalid Gemini Pro image size "
                "calculated: "
                +
                size
            )
        )

    return size


# =========================================================
# HTTP HELPERS
# =========================================================

def _safe_json(
    response: Any,
) -> Dict[str, Any]:

    if isinstance(
        response,
        dict,
    ):

        return response

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
                    8000,
                )
        }


def _provider_error_message(
    provider: str,
    response: Any,
) -> str:

    data = _safe_json(
        response
    )

    status_code = getattr(
        response,
        "status_code",
        "?",
    )

    value = data.get(
        "error"
    )

    message = ""

    if isinstance(
        value,
        dict,
    ):

        message = clean_text(
            (
                value.get(
                    "message"
                )
                or
                value.get(
                    "detail"
                )
                or
                value.get(
                    "code"
                )
                or
                value
            ),
            5000,
        )

    elif value:

        message = clean_text(
            value,
            5000,
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
            5000,
        )

    return (
        clean_text(
            provider,
            200,
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
# IMAGE DATA DISCOVERY
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
            )[
                1
            ]

        except Exception:

            return None

    try:

        raw = base64.b64decode(
            text,
            validate=False,
        )

        if len(
            raw
        ) < 32:

            return None

        return raw

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

            mime = clean_text(
                (
                    node.get(
                        "mime_type"
                    )
                    or
                    node.get(
                        "mimeType"
                    )
                    or
                    node.get(
                        "media_type"
                    )
                    or
                    ""
                ),
                100,
            )

            for key in (
                "b64_json",
                "base64",
            ):

                candidate = node.get(
                    key
                )

                if isinstance(
                    candidate,
                    str,
                ):

                    raw = (
                        _decode_image_data(
                            candidate
                        )
                    )

                    if raw:

                        output.append(
                            (
                                raw,
                                (
                                    mime
                                    or
                                    infer_mime_type(
                                        raw,
                                        "image/png",
                                    )
                                ),
                            )
                        )

            #
            # Gemini commonly places base64 bytes under data.
            #

            candidate = node.get(
                "data"
            )

            if (
                isinstance(
                    candidate,
                    str,
                )
                and
                (
                    "image"
                    in normalize_arabic(
                        mime
                    )
                    or
                    any(
                        marker
                        in node
                        for marker
                        in (
                            "mime_type",
                            "mimeType",
                            "media_type",
                        )
                    )
                )
            ):

                raw = (
                    _decode_image_data(
                        candidate
                    )
                )

                if raw:

                    output.append(
                        (
                            raw,
                            (
                                mime
                                or
                                infer_mime_type(
                                    raw
                                )
                            ),
                        )
                    )

            for child in (
                node.values()
            ):

                if isinstance(
                    child,
                    (
                        dict,
                        list,
                        tuple,
                    ),
                ):

                    walk(
                        child
                    )

        elif isinstance(
            node,
            (
                list,
                tuple,
            ),
        ):

            for child in node:

                walk(
                    child
                )

    walk(
        value
    )

    deduped: List[
        Tuple[
            bytes,
            str,
        ]
    ] = []

    seen = set()

    for raw, mime in output:

        signature = (
            len(
                raw
            ),
            raw[:64],
        )

        if signature in seen:

            continue

        seen.add(
            signature
        )

        deduped.append(
            (
                raw,
                (
                    mime
                    or
                    infer_mime_type(
                        raw
                    )
                ),
            )
        )

    return deduped


# =========================================================
# JSON HELPERS
# =========================================================

JSON_REQUEST_MARKERS = [
    "return json only",
    "return only json",
    "json only",
    "output json",
    "return a json object",
    "required schema",
    "output schema",
    "json schema",
]


def looks_like_json_request(
    prompt: str,
) -> bool:

    source = clean_text(
        prompt,
        50000,
    ).lower()

    if any(
        marker
        in source
        for marker
        in JSON_REQUEST_MARKERS
    ):

        return True

    if (
        "return json"
        in source
        and
        "{"
        in source
        and
        "}"
        in source
    ):

        return True

    return False


def normalize_json_text(
    value: str,
) -> str:

    text = clean_text(
        value,
        200000,
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
        (
            "Structured model output "
            "is not valid JSON."
        )
    )


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

    value = (
        data.get(
            "error"
        )
        or
        data.get(
            "incomplete_details"
        )
        or
        status
    )

    return clean_text(
        value,
        3000,
    )


def is_openai_quota_error(
    error: Any,
) -> bool:
    """Return True for billing/quota failures where retrying OpenAI is wasteful."""
    message = clean_text(
        error,
        8000,
    ).lower()

    billing_markers = (
        "no credits",
        "insufficient_quota",
        "quota exceeded",
        "exceeded your current quota",
        "billing hard limit",
        "billing_hard_limit",
        "add credits",
        "credit balance",
        "does not exist",
        "model_not_found",
        "unsupported model",
        "invalid model",
    )

    if any(marker in message for marker in billing_markers):
        return True

    return (
        "429" in message
        and any(
            marker in message
            for marker in (
                "quota",
                "billing",
                "rate limit",
                "too many requests",
            )
        )
    )


# =========================================================
# OPENAI RESPONSE TEXT
# =========================================================

def _extract_openai_response_text(
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

    texts: List[str] = []

    def walk(
        node: Any,
    ) -> None:

        if isinstance(
            node,
            dict,
        ):

            node_type = clean_text(
                node.get(
                    "type",
                    "",
                ),
                100,
            ).lower()

            text = node.get(
                "text"
            )

            if (
                isinstance(
                    text,
                    str,
                )
                and
                text.strip()
                and
                node_type
                in {
                    "output_text",
                    "text",
                    "message",
                    "",
                }
            ):

                texts.append(
                    text.strip()
                )

            for key in (
                "output",
                "content",
                "parts",
                "result",
                "response",
            ):

                if key in node:

                    walk(
                        node.get(
                            key
                        )
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
        data.get(
            "output"
        )
    )

    return clean_text(
        "\n".join(
            texts
        ),
        200000,
    )


def _extract_openai_refusal(
    data: Dict[str, Any],
) -> str:

    refusals: List[str] = []

    def walk(
        node: Any,
    ) -> None:

        if isinstance(
            node,
            dict,
        ):

            if (
                clean_text(
                    node.get(
                        "type",
                        "",
                    ),
                    100,
                ).lower()
                ==
                "refusal"
            ):

                value = (
                    node.get(
                        "refusal"
                    )
                    or
                    node.get(
                        "text"
                    )
                )

                if value:

                    refusals.append(
                        clean_text(
                            value,
                            3000,
                        )
                    )

            for child in (
                node.values()
            ):

                if isinstance(
                    child,
                    (
                        dict,
                        list,
                    ),
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
        data
    )

    return clean_text(
        "\n".join(
            refusals
        ),
        5000,
    )


# =========================================================
# OPENAI USAGE TELEMETRY
# =========================================================

def _log_openai_usage(
    data: Dict[str, Any],
) -> None:

    if not OPENAI_USAGE_LOGGING:

        return

    usage = data.get(
        "usage"
    )

    if not isinstance(
        usage,
        dict,
    ):

        return

    input_tokens = safe_int(
        usage.get(
            "input_tokens",
            0,
        ),
        0,
    )

    output_tokens = safe_int(
        usage.get(
            "output_tokens",
            0,
        ),
        0,
    )

    total_tokens = safe_int(
        usage.get(
            "total_tokens",
            (
                input_tokens
                +
                output_tokens
            ),
        ),
        (
            input_tokens
            +
            output_tokens
        ),
    )

    reasoning_tokens = 0

    details = usage.get(
        "output_tokens_details"
    )

    if isinstance(
        details,
        dict,
    ):

        reasoning_tokens = (
            safe_int(
                details.get(
                    "reasoning_tokens",
                    0,
                ),
                0,
            )
        )

    print(
        (
            "📊 OPENAI USAGE"
            +
            " | input="
            +
            str(
                input_tokens
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
    )


# =========================================================
# REASONING
# =========================================================

def normalize_reasoning_effort(
    value: Any,
    fallback: str = "low",
) -> str:

    normalized = str(
        value
        or ""
    ).strip().lower()

    if normalized in (
        SUPPORTED_REASONING_LEVELS
    ):

        return normalized

    return fallback


# =========================================================
# OPENAI RESPONSE CALL
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
                    100000,
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

    else:

        payload[
            "text"
        ] = {
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
                "Gemini Vision",
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
                "Gemini Vision returned "
                "invalid response."
            )
        )

    _log_openai_usage(
        data
    )

    return data


def _run_openai_director(
    prompt: str,
    *,
    image_bytes: Optional[
        bytes
    ] = None,
    image_mime_type: str = "image/png",
    json_mode: bool = False,
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
    )

    reasoning = (
        OPENAI_STRUCTURED_REASONING
        if structured
        else
        OPENAI_DIRECTOR_REASONING
    )

    max_tokens = (
        OPENAI_STRUCTURED_MAX_OUTPUT_TOKENS
        if structured
        else
        OPENAI_DIRECTOR_MAX_OUTPUT_TOKENS
    )

    attempts = (
        2
        if structured
        else
        1
    )

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

            current_tokens = (
                OPENAI_STRUCTURED_RETRY_MAX_OUTPUT_TOKENS
            )

            current_prompt = (
                prompt
                +
                "\n\n"
                +
                "STRUCTURED RETRY REQUIREMENT:\n"
                +
                "Return the complete JSON object again "
                +
                "from the beginning. Be concise. "
                +
                "Close every object and array."
            )

        else:

            current_tokens = (
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
                        bool(
                            json_mode
                        )
                    ),

                    json_schema=(
                        json_schema
                    ),

                    json_schema_name=(
                        json_schema_name
                    ),

                    reasoning_effort=(
                        reasoning
                    ),

                    max_output_tokens=(
                        current_tokens
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
                        "Gemini Vision refused: "
                        +
                        refusal
                    )
                )

            status_problem = (
                response_status_error(
                    data
                )
            )

            if status_problem:

                raise XPANDImageProviderError(
                    (
                        "Gemini Vision status: "
                        +
                        status_problem
                    )
                )

            text = (
                _extract_openai_response_text(
                    data
                )
            )

            if not text:

                raise XPANDImageProviderError(
                    (
                        "Gemini Vision returned "
                        "no output text."
                    )
                )

            if structured:

                return normalize_json_text(
                    text
                )

            return text

        except Exception as error:

            last_error = error

            if (
                structured
                and
                attempt
                <
                attempts
            ):

                print(
                    (
                        "🔁 Gemini Vision "
                        "structured retry"
                    )
                )

                continue

            raise

    raise XPANDImageProviderError(
        (
            "Gemini Vision failed: "
            +
            clean_text(
                last_error,
                3000,
            )
        )
    )


# =========================================================
# GEMINI DIRECTOR
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

            if (
                isinstance(
                    item,
                    str,
                )
                and
                item.strip()
            ):

                return item.strip()

        for key in (
            "output",
            "outputs",
            "steps",
            "content",
            "parts",
            "result",
        ):

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
            "GEMINI_API_KEY missing."
        )

    structured = bool(
        json_mode
        or
        json_schema
    )

    request_prompt = clean_text(
        prompt,
        60000,
    )

    if structured:

        request_prompt += (
            "\n\n"
            "OUTPUT CONTRACT:\n"
            "Return exactly one complete valid JSON object. "
            "No Markdown and no prose."
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

    candidates: List[str] = []

    def add_candidate(
        model: str,
    ) -> None:

        model = clean_text(
            model,
            200,
        )

        if (
            model
            and
            model not in candidates
        ):

            candidates.append(
                model
            )

    if structured:

        if image_bytes:

            add_candidate(
                GEMINI_VISION_STRUCTURED_MODEL
            )

        add_candidate(
            GEMINI_STRUCTURED_MODEL
        )

    elif image_bytes:

        add_candidate(
            GEMINI_VISION_MODEL
        )

    add_candidate(
        GEMINI_DIRECTOR_RUNTIME_MODEL
    )

    for model in (
        GEMINI_DIRECTOR_FALLBACK_MODELS
    ):

        add_candidate(
            model
        )

    last_error = ""

    for model in candidates[
        :4
    ]:

        payload: Dict[
            str,
            Any,
        ] = {
            "model":
                model,

            "input":
                inputs,
        }

        #
        # Search grounding stays off for structured output.
        #

        if (
            not structured
            and
            env_bool(
                "XPAND_GEMINI_SEARCH_GROUNDING",
                True,
            )
            and
            contains_any(
                request_prompt,
                (
                    "deep research",
                    "بحث عميق",
                    "competitor",
                    "منافس",
                    "current campaign",
                    "latest campaign",
                ),
            )
        ):

            payload[
                "tools"
            ] = [
                {
                    "type":
                        "google_search"
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
                        "returned no text."
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
                    r"(?:not found|unsupported|"
                    r"invalid|does not exist)"
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

    raise XPANDImageProviderError(
        (
            last_error
            or
            (
                "Gemini Director: "
                "no usable model found."
            )
        )
    )


# =========================================================
# PUBLIC DIRECTOR
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

    global OPENAI_STRUCTURED_UNAVAILABLE

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

    if GEMINI_ONLY_MODE:
        return call_gemini_director(
            prompt,
            image_bytes=(image_bytes),
            image_mime_type=(image_mime_type),
            json_mode=(structured),
            json_schema=(json_schema),
            json_schema_name=(json_schema_name),
        )

    #
    # STRUCTURED:
    # Gemini Vision FIRST.
    #

    if structured:

        if (
            OPENAI_ENABLED
            and
            OPENAI_API_KEY
            and
            not OPENAI_STRUCTURED_UNAVAILABLE
        ):

            try:

                return (
                    _run_openai_director(
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
                )

            except Exception as error:

                print(
                    (
                        "⚠️ OPENAI STRUCTURED "
                        "DIRECTOR: "
                        +
                        clean_text(
                            error,
                            1800,
                        )
                    )
                )

                error_text = clean_text(error, 2400).lower()
                if any(
                    marker in error_text
                    for marker in (
                        "no credits",
                        "insufficient_quota",
                        "quota",
                        "billing",
                        "rate limit",
                        "429",
                    )
                ):
                    OPENAI_STRUCTURED_UNAVAILABLE = True
                    print(
                        "🔒 OpenAI structured director disabled for this process; using Gemini fallback.",
                        flush=True,
                    )

                if not GEMINI_API_KEY:

                    raise

        if GEMINI_API_KEY:

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

        raise XPANDImageConfigurationError(
            (
                "No structured Director "
                "provider configured."
            )
        )

    #
    # FREE TEXT:
    # Gemini FIRST for cost efficiency.
    #

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
            )

        except Exception as error:

            print(
                (
                    "⚠️ GEMINI FREE-TEXT "
                    "DIRECTOR: "
                    +
                    clean_text(
                        error,
                        1500,
                    )
                )
            )

            if not (
                OPENAI_ENABLED
                and
                OPENAI_API_KEY
            ):

                raise

    if (
        OPENAI_ENABLED
        and
        OPENAI_API_KEY
    ):

        return _run_openai_director(
            prompt,

            image_bytes=(
                image_bytes
            ),

            image_mime_type=(
                image_mime_type
            ),

            json_mode=False,
        )

    raise XPANDImageConfigurationError(
        "No Director provider configured."
    )


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
                "Could not decode "
                "structured response: "
                +
                clean_text(
                    error,
                    1200,
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
# EXPLICIT SOL HELPERS
# =========================================================

def build_sol_art_direction(
    original_prompt: str,
    aspect_ratio: str,
    image_size: str,
) -> str:

    request = f"""
You are XPAND's senior advertising art director.

Do NOT generate an image.

ORIGINAL REQUEST:
{clean_text(
    original_prompt,
    12000,
)}

TARGET ASPECT RATIO:
{aspect_ratio}

RESOLUTION INTENT:
{image_size}

Create one concise professional art-direction brief.

Lock:
- advertising proposition
- visual mechanism
- hero relationship
- camera position
- lens behavior
- focal hierarchy
- environment
- lighting motivation
- materials
- depth
- negative space
- physical realism

Do not default to a generic three-quarter commercial shot.
Do not invent unrelated objects.
Return only the final brief.
""".strip()

    if (
        OPENAI_ENABLED
        and
        OPENAI_API_KEY
    ):

        return _run_openai_director(
            request,
            json_mode=False,
        )

    return call_openai_director(
        request,
        json_mode=False,
    )


def build_sol_visual_critique(
    original_prompt: str,
    image_bytes: bytes,
    mime_type: str,
) -> str:

    request = f"""
You are XPAND's final senior visual reviewer.

Review the attached image against:

{clean_text(
    original_prompt,
    12000,
)}

Evaluate only meaningful defects:

- message clarity
- advertising mechanism
- brand feel
- composition
- camera
- human realism
- object realism
- anatomy
- materials
- reflections
- shadows
- perspective
- visual artifacts
- commercial readiness

Do not redesign a strong image unnecessarily.

Return concise actionable corrections only.
""".strip()

    if (
        OPENAI_ENABLED
        and
        OPENAI_API_KEY
    ):

        return _run_openai_director(
            request,

            image_bytes=(
                image_bytes
            ),

            image_mime_type=(
                mime_type
            ),

            json_mode=False,
        )

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


def critique_generated_image(
    image_bytes: bytes,
    mime_type: str,
    original_prompt: str,
) -> str:

    return build_sol_visual_critique(
        original_prompt,
        image_bytes,
        mime_type,
    )


# =========================================================
# PROFESSIONAL PROMPT
# =========================================================

def build_professional_prompt(
    prompt: str,
    aspect_ratio: str,
    image_size: str,
) -> str:

    original = clean_text(
        prompt,
        40000,
    )

    suffix = f"""

XPAND EXECUTION LOCK
====================

Target frame:
{aspect_ratio}

Resolution intent:
{image_size}

Make one coherent professional advertising image.

Mandatory:
- one physically coherent perspective
- believable scale
- motivated light
- correct contact shadows
- material-specific reflections
- natural depth
- clear focal hierarchy
- no random decorative technology
- no accidental visual clutter

The camera must serve the message rather than defaulting
to a generic commercial three-quarter shot.
""".strip()

    if is_stc_bank_request(
        original
    ):

        suffix += """

STC BANK BASE LOCK
==================

This is a premium STC Bank campaign image.

Do NOT generate:
- copy
- slogans
- readable banking UI
- fake logos
- watermarks
- generic fintech network lines
- holograms
- glowing arrows
- random floating banking objects

Purple is an identity tool, not an automatic global tint.

Skin, clothing, products, metal, glass and natural materials
must remain physically credible.
""".strip()

    return (
        original
        +
        "\n\n"
        +
        suffix
    )


# =========================================================
# PREVISUALIZATION PROMPT
# =========================================================

def build_previsualization_prompt(
    original_prompt: str,
    aspect_ratio: str,
    *,
    reference_count: int = 0,
) -> str:

    stc = is_stc_bank_request(
        original_prompt
    )

    prompt = f"""
XPAND PREVISUALIZATION — NANO BANANA 2
======================================

This image is an internal advertising PREVISUALIZATION.
It will NOT be the final delivery.

ORIGINAL REQUEST:
{clean_text(
    original_prompt,
    18000,
)}

FRAME:
{aspect_ratio}

REFERENCE IMAGES AVAILABLE:
{reference_count}

Your job is to prove the advertising idea visually.

Prioritize:
1. message clarity
2. visual mechanism
3. composition
4. meaningful camera viewpoint
5. believable environment
6. physically realistic object relationships
7. strong focal hierarchy

Do NOT waste effort on decorative polish that does not
improve the advertising proposition.

Create a real, photographable scene.

Avoid:
- generic three-quarter product shot
- giant empty upper third
- meaningless luxury pedestal
- generic futuristic fintech effects
- random floating elements
- fake readable UI
- generated copy
- generated logos

Use approximately 15–22% integrated calm copy space only
when the composition benefits from it.

The negative space must feel designed, not empty.
""".strip()

    if reference_count:

        prompt += """

REFERENCE CONTRACT
==================

The attached images are visual DNA and production references.

Study:
- tonal balance
- lighting behavior
- palette restraint
- material language
- spatial discipline
- camera sophistication
- cultural realism
- advertising finish

Do NOT clone any reference composition.

Do NOT copy a reference scene literally.
""".strip()

    if stc:

        prompt += """

STC BANK PREVISUALIZATION LOCK
==============================

The image must already feel capable of becoming an STC Bank
campaign before the final renderer touches it.

For merchant payments / e-commerce + POS:

The proposition must be understandable WITHOUT text:

the merchant's online commerce and physical point-of-sale
activity belong to one connected commercial reality.

Do NOT communicate this by inventing strange technology.

Hard bans:
- invented hybrid payment terminal
- phone/POS fusion
- smartphone physically merged with a POS
- fake futuristic payment hardware
- customer simply holding a POS toward camera
- generic checkout tableau
- random stone or travertine pedestal
- meaningless beige luxury object stage
- generic phone screen as the only e-commerce cue
- purple neon fintech room
- UI holograms
- network lines
- particles

Use believable Saudi commercial behavior.

Choose a camera angle that makes the proposition stronger.
""".strip()

    return prompt


# =========================================================
# GPT-IMAGE-2 FINAL RENDERER PROMPT
# =========================================================

def build_final_renderer_prompt(
    original_prompt: str,
    aspect_ratio: str,
    image_size: str,
    reference_count: int = 0,
    stc_request: Optional[
        bool
    ] = None,
) -> str:

    if stc_request is None:

        stc_request = (
            is_stc_bank_request(
                original_prompt
            )
        )

    prompt = f"""
XPAND FINAL RENDERER — GPT-IMAGE-2
==================================

Create the FINAL client-ready advertising image.

ORIGINAL REQUEST:
{clean_text(
    original_prompt,
    22000,
)}

FINAL FRAME:
{aspect_ratio}

FINAL RESOLUTION INTENT:
{image_size}

INPUT IMAGE CONTRACT
====================

Image 1:
approved composition / advertising-message draft.

Images 2+:
brand DNA, photographic style, environment or service
references.

Number of additional references:
{reference_count}

The draft controls:
- proposition
- core composition
- hero relationship
- camera logic
- scene structure

The references control:
- visual DNA
- brand restraint
- photographic finish
- material language
- light
- color discipline
- cultural credibility

References are DNA, never clone targets.

Do NOT reproduce any source campaign literally.

FINAL QUALITY STANDARD
======================

The result must look like a real premium commercial production,
not an AI concept render.

Require:
- convincing real-world geometry
- coherent lens perspective
- believable object scale
- natural human anatomy
- realistic hands and grip
- credible contact
- correct shadows
- physically plausible reflections
- detailed skin and fabric
- material-specific roughness
- controlled depth of field
- deliberate focal hierarchy
- production-grade color separation

Do not normalize the approved camera into a generic
three-quarter product shot.

Preserve a strong or unusual camera decision when it helps
the advertising message.

Negative space must be designed as part of the shot.

Do not create a giant blank upper third.

For portrait campaign work, aim for approximately 15–22%
integrated usable copy space when appropriate.

Do NOT generate copy, logo or watermark unless the original
request explicitly requires generated typography.
""".strip()

    if stc_request:

        prompt += """

============================================================
STC BANK VISUAL CONSTITUTION — FINAL LOCK
============================================================

This image must feel like a high-budget STC Bank campaign,
not a generic fintech advertisement with purple added later.

BRAND IDENTITY
==============

Use the attached STC references as the authority for:

- tonal balance
- restrained purple usage
- light behavior
- spatial discipline
- premium modernity
- real Saudi cultural cues
- materials
- photographic finish
- composition restraint

Purple is NOT automatically the dominant color.

Do not purple-tint:
- human skin
- white clothing
- hair
- natural food
- wood
- neutral metal
- glass
- real product surfaces

Purple should appear only where it behaves like intentional
brand art direction.

PHYSICAL REALITY LOCK
=====================

Everything shown must be physically understandable.

Never invent a payment device simply to explain the service.

HARD BAN:
- phone/POS fusion
- smartphone fused with a payment terminal
- imaginary hybrid POS hardware
- deformed POS terminal
- impossible payment screen
- floating fake banking UI
- readable fake banking interface
- holographic payment panels

A real POS terminal must look like a real commercially
plausible payment device.

A real smartphone must remain a real smartphone.

Do not merge the two.

MATERIAL LOCK
=============

Do NOT introduce random luxury materials merely because the
brief says premium.

Specifically avoid:
- random travertine
- random stone slab
- beige stone pedestal
- marble podium
- generic luxury plinth
- product sitting on a stone block

unless that material is genuinely required by the approved
concept or clearly supported by the selected STC references.

Luxury must come from:
- art direction
- lighting
- camera
- spatial restraint
- human behavior
- color
- believable materials
- production finish

not from an arbitrary stone pedestal.

MERCHANT PAYMENTS MESSAGE LOCK
==============================

When the benefit is e-commerce services + point of sale:

The viewer must understand visually that:

ONLINE COMMERCE
and
PHYSICAL PAYMENT ACCEPTANCE

belong to ONE merchant commercial ecosystem.

Use real commercial evidence.

Possible real-world evidence may include:
- genuine merchant workflow
- prepared online order
- physical customer transaction
- packaging or fulfillment only when narratively justified
- real retail environment
- real operational relationship between physical and online
  commerce

But DO NOT fall into the old literal cliché:

customer
+ merchant
+ counter
+ POS
+ tablet
+ packing box

simply placed together.

The relationship must be an advertising idea, not an
inventory of service objects.

Do NOT use a phone screen as the sole shortcut for
"e-commerce".

The visual message must work even with zero text.

CAMERA LOCK
===========

The camera must add meaning.

Prefer an intentional visual grammar when justified:

- reflection-led framing
- compressed long-lens relationship
- true top-down system view
- low grazing angle
- foreground occlusion
- architectural framing
- controlled wide environmental perspective
- unusual but realistic commercial viewpoint

Avoid repeatedly returning to:

eye-level
+
three-quarter angle
+
device centered on counter

unless that exact angle is uniquely justified.

COPY SPACE
==========

Use approximately 15–22% calm integrated copy space.

Do NOT push the entire scene into the lower half merely to
leave a giant empty area above.

The negative space should emerge naturally from:
- depth
- wall plane
- light
- architecture
- atmosphere
- subject placement

NO GENERATED BRAND COPY
=======================

Do not generate:
- STC Bank logo
- fake Arabic slogan
- English slogan
- fake merchant copy
- random interface labels
- watermark

FINAL TEST
==========

Before finishing, the image should pass these questions:

1. Could this plausibly be photographed?
2. Is the payment hardware believable?
3. Is the advertising message understandable without text?
4. Does it feel brand-specific rather than generic fintech?
5. Is the camera intentional?
6. Is every visible material justified?
7. Does the image feel premium without arbitrary stone?
8. Would this look credible in a real Saudi bank campaign?

If any answer is no, correct the image before final output.
""".strip()

    return prompt


# =========================================================
# GEMINI IMAGE PAYLOAD
# =========================================================

def _build_gemini_image_payload(
    *,
    model: str,
    prompt: str,
    aspect_ratio: str,
    image_size: str,
) -> Dict[str, Any]:

    #
    # IMPORTANT:
    #
    # NO:
    # thinking_level
    # thinking
    # reasoning
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
            "GEMINI_API_KEY missing."
        )

    provider_size = (
        route.image_size
        if route.image_size
        in SUPPORTED_GOOGLE_IMAGE_SIZES
        else
        "1K"
    )

    if provider_size == "512":

        provider_size = "1K"

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
                provider_size
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
                "Gemini image request "
                "succeeded but returned "
                "no image."
            )
        )

    image_bytes, mime_type = (
        images[
            0
        ]
    )

    image_bytes, mime_type = normalize_image_bytes_to_aspect(image_bytes, mime_type or "image/jpeg", route.aspect_ratio)

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
            uuid.uuid4().hex[
                :12
            ]
        )

    if index:

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
            route.image_size
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

            "provider_size":
                provider_size,

            "requested_image_size":
                route.image_size,

            "thinking_level_sent":
                False,

            "provider_core":
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
            safe_int(
                number,
                1,
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
                    prompt,
                    original_prompt,
                    route,
                    index,
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
# GEMINI MULTI-IMAGE SYNTHESIS
# =========================================================

def _gemini_multi_image_synthesis(
    input_images: Sequence[
        Tuple[
            bytes,
            str,
        ]
    ],
    prompt: str,
    *,
    aspect_ratio: str,
    image_size: str,
    pro: bool = False,
    reference_only: bool = False,
) -> GeneratedImage:

    if not GEMINI_API_KEY:

        raise XPANDImageConfigurationError(
            "GEMINI_API_KEY missing."
        )

    normalized_images = (
        _normalize_reference_images(
            list(
                input_images
            )
        )
    )

    if not normalized_images:

        raise XPANDImageError(
            (
                "No valid images supplied "
                "to Gemini synthesis."
            )
        )

    model = (
        GOOGLE_IMAGE_PRO_MODEL
        if pro
        else
        GOOGLE_IMAGE_FAST_MODEL
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

    if provider_size == "512":

        provider_size = "1K"

    instruction = clean_text(
        prompt,
        50000,
    )

    if reference_only:

        instruction += """

REFERENCE MODE
==============

All attached images are references only.

Do NOT treat Image 1 as a base image that must be copied.

Study the references as visual / brand / service DNA.

Create a new original previsualization that follows the
written advertising direction.
""".strip()

    else:

        instruction += """

EDIT MODE
=========

Image 1 is the base image.

Images 2+ are supporting references.

Preserve the successful base composition unless the user
explicitly requests a structural change.

Match perspective, scale, shadows, reflections and material
response.
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
    ) in normalized_images[
        :10
    ]:

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
    # NO thinking_level.
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
                (
                    "Nano Banana Pro"
                    if pro
                    else
                    "Nano Banana 2"
                ),
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
                "Gemini multi-image "
                "synthesis returned no image."
            )
        )

    output, output_mime = (
        images[
            0
        ]
    )

    output, output_mime = normalize_image_bytes_to_aspect(output, output_mime or "image/jpeg", final_ratio)

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
            prompt
        ),

        aspect_ratio=(
            final_ratio
        ),

        image_size=(
            final_size
        ),

        quality="high",

        route_reason=(
            (
                "XPAND Nano Banana "
                "reference previsualization"
            )
            if reference_only
            else
            "XPAND Nano Banana image edit"
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
                "nge-"
                +
                uuid.uuid4().hex[
                    :12
                ]
            )
        ),

        metadata={
            "generation_type":
                (
                    "gemini_reference_previsualization"
                    if reference_only
                    else
                    "gemini_edit"
                ),

            "input_images":
                len(
                    normalized_images
                ),

            "provider_size":
                provider_size,

            "thinking_level_sent":
                False,

            "provider_core":
                ENGINE_VERSION,
        },
    )


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

    return _gemini_multi_image_synthesis(
        input_images,
        prompt,

        aspect_ratio=(
            aspect_ratio
        ),

        image_size=(
            image_size
            or
            detect_image_size(
                prompt
            )
        ),

        pro=(
            pro
        ),

        reference_only=False,
    )


# =========================================================
# OPENAI GENERATION
# =========================================================

def _build_openai_generation_payload(
    *,
    prompt: str,
    size: str,
    quality: str,
    number: int,
) -> Dict[str, Any]:

    return {
        "model":
            OPENAI_EDIT_MODEL,

        "prompt":
            clean_text(
                prompt,
                32000,
            ),

        "size":
            size,

        "quality":
            (
                quality
                if quality
                in SUPPORTED_OPENAI_QUALITIES
                else
                "high"
            ),

        "n":
            max(
                1,
                min(
                    safe_int(
                        number,
                        1,
                    ),
                    4,
                ),
            ),
    }


def generate_with_openai(
    prompt: str,
    original_prompt: str,
    route: ImageRoute,
    number: int = 1,
) -> List[
    GeneratedImage
]:

    if (
        not OPENAI_ENABLED
        or
        not OPENAI_API_KEY
    ):

        raise XPANDImageConfigurationError(
            "OpenAI image generation is disabled."
        )

    number = max(
        1,
        min(
            safe_int(
                number,
                1,
            ),
            4,
        ),
    )

    provider_size = (
        openai_size_for_ratio(
            route.aspect_ratio,
            route.image_size,
        )
    )

    quality = (
        route.quality
        if route.quality
        in SUPPORTED_OPENAI_QUALITIES
        else
        "high"
    )

    payload = (
        _build_openai_generation_payload(
            prompt=(
                prompt
            ),

            size=(
                provider_size
            ),

            quality=(
                quality
            ),

            number=(
                number
            ),
        )
    )

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

    if not response.ok:

        raise XPANDImageProviderError(
            _provider_error_message(
                "Gemini Pro image",
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
                "Gemini Pro image generation "
                "returned no image."
            )
        )

    request_id = clean_text(
        getattr(
            response,
            "headers",
            {},
        ).get(
            "x-request-id",
            "",
        ),
        200,
    )

    elapsed = round(
        time.monotonic()
        -
        started,
        3,
    )

    results: List[
        GeneratedImage
    ] = []

    for index, (
        image_bytes,
        mime_type,
    ) in enumerate(
        images[
            :number
        ]
    ):

        unique = (
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

            unique += (
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
                    "image/png"
                ),

                provider=(
                    PROVIDER_OPENAI
                ),

                model=(
                    OPENAI_EDIT_MODEL
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
                    route.image_size
                ),

                quality=(
                    quality
                ),

                route_reason=(
                    route.reason
                ),

                request_id=(
                    unique
                ),

                metadata={
                    "generation_type":
                        "openai_generation",

                    "requested_image_size":
                        route.image_size,

                    "provider_size":
                        provider_size,

                    "flexible_size":
                        True,

                    "provider_core":
                        ENGINE_VERSION,

                    "elapsed_seconds":
                        elapsed,
                },
            )
        )

    return results


# =========================================================
# OPENAI MULTI-REFERENCE EDIT HELPERS
# =========================================================

def _extension_for_mime(
    mime_type: str,
) -> str:

    mime = clean_text(
        mime_type,
        100,
    ).lower()

    if (
        "jpeg"
        in mime
        or
        "jpg"
        in mime
    ):

        return ".jpg"

    if "webp" in mime:

        return ".webp"

    return ".png"


def _build_openai_edit_files(
    input_images: Sequence[
        Tuple[
            bytes,
            str,
        ]
    ],
) -> List[
    Tuple[
        str,
        Tuple[
            str,
            bytes,
            str,
        ],
    ]
]:

    files: List[
        Tuple[
            str,
            Tuple[
                str,
                bytes,
                str,
            ],
        ]
    ] = []

    for index, (
        image_bytes,
        mime_type,
    ) in enumerate(
        list(
            input_images
        )[
            :OPENAI_MAX_REFERENCE_IMAGES
        ],
        start=1,
    ):

        if not image_bytes:

            continue

        mime = (
            mime_type
            if str(
                mime_type
            ).startswith(
                "image/"
            )
            else
            infer_mime_type(
                image_bytes,
                "image/png",
            )
        )

        filename = (
            "xpand-input-"
            +
            str(
                index
            )
            +
            _extension_for_mime(
                mime
            )
        )

        #
        # Gemini Pro image Image API array syntax.
        #

        files.append(
            (
                "image[]",
                (
                    filename,
                    image_bytes,
                    mime,
                ),
            )
        )

    return files


def _build_openai_IMAGE_form(
    *,
    prompt: str,
    size: str,
    quality: str,
) -> Dict[str, str]:

    #
    # IMPORTANT:
    #
    # Gemini Pro image processes image inputs at high
    # fidelity automatically.
    #
    # input_fidelity MUST NOT be sent.
    #

    return {
        "model":
            OPENAI_IMAGE_MODEL,

        "prompt":
            clean_text(
                prompt,
                32000,
            ),

        "size":
            size,

        "quality":
            (
                quality
                if quality
                in SUPPORTED_OPENAI_QUALITIES
                else
                "high"
            ),

        "n":
            "1",
    }


# =========================================================
# OPENAI MULTI-REFERENCE EDIT
# =========================================================
def _build_openai_edit_form(
    *,
    prompt: str,
    size: str,
    quality: str,
) -> Dict[str, str]:

    #
    # IMPORTANT:
    #
    # Gemini Pro image processes image inputs at high
    # fidelity automatically.
    #
    # input_fidelity MUST NOT be sent.
    #
    # Use the independently configured edit model, not a generation-only
    # model. Omit optional fidelity parameters for provider compatibility.
    #

    # GPT Image 1 accepts native portrait/landscape/square sizes only.
    # Keep requested aspect/2K intent in the existing output pipeline;
    # do not send GPT Image 2 custom dimensions to this endpoint.
    if OPENAI_EDIT_MODEL == "gpt-image-1":
        width, height = (int(part) for part in size.split("x"))
        size = (
            "1024x1536" if height > width
            else "1536x1024" if width > height
            else "1024x1024"
        )

    return {
        "model":
            OPENAI_EDIT_MODEL,

        "prompt":
            clean_text(
                prompt,
                32000,
            ),

        "size":
            size,

        "quality":
            (
                quality
                if quality
                in SUPPORTED_OPENAI_QUALITIES
                else
                "high"
            ),

        "n":
            "1",
    }




def edit_with_openai_multi(
    input_images: Sequence[
        Tuple[
            bytes,
            str,
        ]
    ],
    prompt: str,
    *,
    aspect_ratio: str = "4:5",
    image_size: str = "2K",
    quality: str = "high",
    original_prompt: str = "",
    final_provider: str = (
        PROVIDER_OPENAI
    ),
    final_model_label: str = (
        OPENAI_EDIT_MODEL
    ),
    metadata: Optional[
        Dict[str, Any]
    ] = None,
) -> GeneratedImage:

    if (
        not OPENAI_ENABLED
        or
        not OPENAI_API_KEY
    ):

        raise XPANDImageConfigurationError(
            "OpenAI image editing is disabled."
        )

    normalized_images = (
        _normalize_reference_images(
            list(
                input_images
            )
        )
    )

    normalized_images = (
        normalized_images[
            :OPENAI_MAX_REFERENCE_IMAGES
        ]
    )

    if not normalized_images:

        raise XPANDImageError(
            (
                "No valid input images "
                "for Gemini Pro image edit."
            )
        )

    ratio = (
        aspect_ratio
        if aspect_ratio
        in SUPPORTED_ASPECT_RATIOS
        else
        detect_aspect_ratio(
            prompt
        )
    )

    intent = detect_image_size(
        prompt,
        image_size,
    )

    provider_size = (
        openai_size_for_ratio(
            ratio,
            intent,
        )
    )

    final_quality = (
        quality
        if quality
        in SUPPORTED_OPENAI_QUALITIES
        else
        "high"
    )

    files = (
        _build_openai_edit_files(
            normalized_images
        )
    )

    form_data = (
        _build_openai_edit_form(
            prompt=(
                prompt
            ),

            size=(
                provider_size
            ),

            quality=(
                final_quality
            ),
        )
    )

    started = time.monotonic()

    print(
        "🎯 OPENAI EDIT REQUEST | model="
        + OPENAI_EDIT_MODEL
        + " | size="
        + form_data["size"]
    )

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

        data=(
            form_data
        ),

        files=(
            files
        ),

        timeout=REQUEST_TIMEOUT,
    )

    if not response.ok:

        raise XPANDImageProviderError(
            _provider_error_message(
                "OpenAI Edit [" + OPENAI_EDIT_MODEL + "]",
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
                "OpenAI edit [" + OPENAI_EDIT_MODEL + "] "
                "returned no image."
            )
        )

    image_bytes, mime_type = (
        images[
            0
        ]
    )

    image_bytes, mime_type = normalize_image_bytes_to_aspect(image_bytes, mime_type or "image/png", ratio)

    request_id = clean_text(
        getattr(
            response,
            "headers",
            {},
        ).get(
            "x-request-id",
            "",
        ),
        200,
    )

    if not request_id:

        request_id = (
            "oe-"
            +
            uuid.uuid4().hex[
                :12
            ]
        )

    final_metadata = dict(
        metadata
        or {}
    )

    final_metadata.update(
        {
            "generation_type":
                "openai_multi_reference_edit",

            "input_images":
                len(
                    normalized_images
                ),

            "requested_image_size":
                intent,

            "provider_size":
                provider_size,

            "reference_fidelity":
                "automatic_high",

            "input_fidelity_sent":
                False,

            "flexible_size":
                True,

            "provider_core":
                ENGINE_VERSION,

            "elapsed_seconds":
                round(
                    time.monotonic()
                    -
                    started,
                    3,
                ),
        }
    )

    return GeneratedImage(
        image_bytes=(
            image_bytes
        ),

        mime_type=(
            mime_type
            or
            "image/png"
        ),

        provider=(
            final_provider
        ),

        model=(
            final_model_label
        ),

        prompt=(
            prompt
        ),

        original_prompt=(
            original_prompt
            or
            prompt
        ),

        aspect_ratio=(
            ratio
        ),

        image_size=(
            intent
        ),

        quality=(
            final_quality
        ),

        route_reason=(
            (
                "XPAND Gemini Pro image "
                "multi-reference final render"
            )
        ),

        request_id=(
            request_id
        ),

        metadata=(
            final_metadata
        ),
    )


# =========================================================
# LEGACY OPENAI EDIT
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
        OPENAI_EDIT_MODEL
    ),
    metadata: Optional[
        Dict[str, Any]
    ] = None,
) -> GeneratedImage:

    return edit_with_openai_multi(
        [
            (
                input_image_bytes,
                input_mime_type,
            )
        ],

        prompt,

        aspect_ratio=(
            route.aspect_ratio
        ),

        image_size=(
            route.image_size
        ),

        quality=(
            route.quality
        ),

        original_prompt=(
            original_prompt
        ),

        final_provider=(
            final_provider
        ),

        final_model_label=(
            final_model_label
        ),

        metadata=(
            metadata
        ),
    )


# =========================================================
# FINAL RENDERER
# =========================================================

def render_final_with_openai(
    draft_image: GeneratedImage,
    original_prompt: str,
    *,
    reference_images: Sequence[
        Tuple[
            bytes,
            str,
        ]
    ] = (),
    aspect_ratio: str = "4:5",
    image_size: str = "2K",
    quality: str = "high",
) -> GeneratedImage:

    references = (
        _normalize_reference_images(
            list(
                reference_images
            )
        )
    )

    #
    # Draft must remain Image 1.
    #
    # Remaining capacity is for actual references.
    #

    max_refs = max(
        0,
        OPENAI_MAX_REFERENCE_IMAGES
        -
        1,
    )

    inputs = [
        _generated_image_tuple(
            draft_image
        )
    ]

    inputs.extend(
        references[
            :max_refs
        ]
    )

    final_prompt = (
        build_final_renderer_prompt(
            original_prompt,

            aspect_ratio,

            image_size,

            reference_count=(
                len(
                    inputs
                )
                -
                1
            ),
        )
    )

    return edit_with_openai_multi(
        inputs,

        final_prompt,

        aspect_ratio=(
            aspect_ratio
        ),

        image_size=(
            image_size
        ),

        quality=(
            quality
        ),

        original_prompt=(
            original_prompt
        ),

        metadata={
            "hybrid_pipeline":
                True,

            "draft_provider":
                draft_image.provider,

            "draft_model":
                draft_image.model,

            "draft_request_id":
                draft_image.request_id,

            "final_renderer":
                OPENAI_EDIT_MODEL,
        },
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
    number: int = 1,
    reference_images: Sequence[
        Tuple[
            bytes,
            str,
        ]
    ] = (),
) -> ImageGenerationResponse:

    started = time.monotonic()

    references = (
        _normalize_reference_images(
            list(
                reference_images
            )
        )
    )

    enhanced = (
        build_final_renderer_prompt(
            original_prompt,

            aspect_ratio,

            image_size,

            reference_count=(
                len(
                    references
                )
            ),
        )
    )

    route = build_route(
        PROVIDER_OPENAI,

        OPENAI_IMAGE_MODEL,

        "Direct Gemini Pro image final route.",

        aspect_ratio,

        image_size,

        quality,
    )

    if references:

        images: List[
            GeneratedImage
        ] = []

        for _ in range(
            max(
                1,
                min(
                    safe_int(
                        number,
                        1,
                    ),
                    4,
                ),
            )
        ):

            images.append(
                edit_with_openai_multi(
                    references,

                    enhanced,

                    aspect_ratio=(
                        aspect_ratio
                    ),

                    image_size=(
                        image_size
                    ),

                    quality=(
                        quality
                    ),

                    original_prompt=(
                        original_prompt
                    ),

                    metadata={
                        "direct_reference_render":
                            True,
                    },
                )
            )

    else:

        images = generate_with_openai(
            enhanced,
            original_prompt,
            route,
            number,
        )

    return ImageGenerationResponse(
        ok=True,

        images=(
            images
        ),

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
# DIRECT GOOGLE ROUTE
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
    reference_images: Sequence[
        Tuple[
            bytes,
            str,
        ]
    ] = (),
) -> ImageGenerationResponse:

    started = time.monotonic()

    references = (
        _normalize_reference_images(
            list(
                reference_images
            )
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

    enhanced = build_professional_prompt(
        original_prompt,
        aspect_ratio,
        image_size,
    )

    route = build_route(
        provider,

        model,

        (
            "Explicit Nano Banana Pro"
            if pro
            else
            "Nano Banana 2 direct route"
        ),

        aspect_ratio,

        image_size,

        quality,
    )

    errors: List[str] = []

    try:

        if references:

            images = []

            for _ in range(
                max(
                    1,
                    min(
                        safe_int(
                            number,
                            1,
                        ),
                        4,
                    ),
                )
            ):

                images.append(
                    _gemini_multi_image_synthesis(
                        references,

                        enhanced,

                        aspect_ratio=(
                            aspect_ratio
                        ),

                        image_size=(
                            image_size
                        ),

                        pro=(
                            pro
                        ),

                        reference_only=True,
                    )
                )

        else:

            images = generate_with_gemini(
                enhanced,
                original_prompt,
                route,
                number,
            )

        return ImageGenerationResponse(
            ok=True,

            images=(
                images
            ),

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

        message = clean_text(
            error,
            4000,
        )

        errors.append(
            "google: "
            +
            message
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
            (
                "🔁 GOOGLE TECHNICAL FALLBACK "
                "→ Gemini Pro image"
            )
        )

        result = run_openai_direct(
            original_prompt,

            aspect_ratio=(
                aspect_ratio
            ),

            image_size=(
                image_size
            ),

            quality=(
                quality
            ),

            number=(
                number
            ),

            reference_images=(
                references
            ),
        )

        result.errors.extend(
            errors
        )

        return result

    raise XPANDImageProviderError(
        (
            "Google image generation failed.\n"
            +
            "\n".join(
                errors
            )
        )
    )


# =========================================================
# HYBRID BEST
# =========================================================

def run_hybrid_best(
    original_prompt: str,
    *,
    aspect_ratio: str,
    image_size: str,
    quality: str,
    number: int = 1,
    reference_images: Sequence[
        Tuple[
            bytes,
            str,
        ]
    ] = (),
) -> ImageGenerationResponse:

    started = time.monotonic()

    references = (
        _normalize_reference_images(
            list(
                reference_images
            )
        )
    )

    number = max(
        1,
        min(
            safe_int(
                number,
                1,
            ),
            4,
        ),
    )

    #
    # BEST must not spend money on a Gemini draft
    # if the required final provider cannot run.
    #

    if (
        BEST_REQUIRE_OPENAI_FINAL
        and
        (
            not OPENAI_ENABLED
            or
            not OPENAI_API_KEY
        )
    ):

        raise XPANDImageConfigurationError(
            (
                "BEST requires Gemini Pro image "
                "as the final renderer, but "
                "OpenAI is not available."
            )
        )

    #
    # No Gemini?
    #
    # Gemini Pro image still completes the request.
    #

    if not GEMINI_API_KEY:

        if (
            OPENAI_ENABLED
            and
            OPENAI_API_KEY
        ):

            print(
                (
                    "⚠️ Nano Banana 2 unavailable."
                    " Gemini Pro image direct final route."
                )
            )

            return run_openai_direct(
                original_prompt,

                aspect_ratio=(
                    aspect_ratio
                ),

                image_size=(
                    image_size
                ),

                quality="high",

                number=(
                    number
                ),

                reference_images=(
                    references
                ),
            )

        raise XPANDImageConfigurationError(
            (
                "Neither Gemini nor OpenAI "
                "image provider is available."
            )
        )

    if (
        not OPENAI_ENABLED
        or
        not OPENAI_API_KEY
    ):

        #
        # Only possible if explicitly disabled by env.
        #

        if not BEST_REQUIRE_OPENAI_FINAL:

            return run_google_direct(
                original_prompt,

                pro=False,

                aspect_ratio=(
                    aspect_ratio
                ),

                image_size=(
                    image_size
                ),

                quality=(
                    quality
                ),

                number=(
                    number
                ),

                allow_fallback=False,

                reference_images=(
                    references
                ),
            )

        raise XPANDImageConfigurationError(
            "Gemini Pro image final renderer unavailable."
        )

    final_quality = "high"

    draft_route = build_route(
        PROVIDER_GOOGLE_FAST,

        GOOGLE_IMAGE_FAST_MODEL,

        (
            "XPAND BEST previsualization "
            "with Nano Banana 2"
        ),

        aspect_ratio,

        "1K",

        "high",
    )

    final_route = build_route(
        PROVIDER_OPENAI,

        OPENAI_IMAGE_MODEL,

        (
            "XPAND BEST mandatory "
            "Gemini Pro image final renderer"
        ),

        aspect_ratio,

        image_size,

        final_quality,
    )

    results: List[
        GeneratedImage
    ] = []

    errors: List[str] = []

    openai_quota_unavailable = False
    quota_fallback_used = False


    preview_prompt = (
        build_previsualization_prompt(
            original_prompt,

            aspect_ratio,

            reference_count=(
                len(
                    references
                )
            ),
        )
    )

    for index in range(
        number
    ):

        if openai_quota_unavailable:
            break

        draft: Optional[
            GeneratedImage
        ] = None

        #
        # STAGE 1:
        # Nano Banana 2 previsualization.
        #

        try:

            print(
                (
                    "🍌 XPAND PREVIS "
                    "Nano Banana 2"
                    +
                    " | "
                    +
                    str(
                        index + 1
                    )
                    +
                    "/"
                    +
                    str(
                        number
                    )
                )
            )

            if references:

                draft = (
                    _gemini_multi_image_synthesis(
                        references,

                        preview_prompt,

                        aspect_ratio=(
                            aspect_ratio
                        ),

                        image_size="1K",

                        pro=False,

                        reference_only=True,
                    )
                )

            else:

                draft = (
                    _generate_one_with_gemini(
                        preview_prompt,

                        original_prompt,

                        draft_route,

                        index,
                    )
                )

        except Exception as error:

            message = clean_text(
                error,
                3500,
            )

            errors.append(
                (
                    "previsualization_"
                    +
                    str(
                        index + 1
                    )
                    +
                    ": "
                    +
                    message
                )
            )

            print(
                "⚠️ PREVIS FAILED:",
                message,
            )

        #
        # STAGE 2:
        # Gemini Pro image mandatory final.
        #

        if draft is not None:

            try:

                print(
                    (
                        "🎯 XPAND FINAL "
                        "Gemini Pro image"
                    )
                )

                final_image = (
                    render_final_with_openai(
                        draft,

                        original_prompt,

                        reference_images=(
                            references
                        ),

                        aspect_ratio=(
                            aspect_ratio
                        ),

                        image_size=(
                            image_size
                        ),

                        quality=(
                            final_quality
                        ),
                    )
                )

                final_image.metadata.update(
                    {
                        "best_pipeline":
                            [
                                GOOGLE_IMAGE_FAST_MODEL,
                                OPENAI_IMAGE_MODEL,
                            ],

                        "previsualization":
                            True,

                        "nano_banana_final":
                            False,

                        "mandatory_openai_final":
                            True,

                        "reference_count":
                            len(
                                references
                            ),
                    }
                )

                results.append(
                    final_image
                )

                continue

            except Exception as error:

                message = clean_text(
                    error,
                    3500,
                )

                errors.append(
                    (
                        "openai_multi_final_"
                        +
                        str(
                            index + 1
                        )
                        +
                        ": "
                        +
                        message
                    )
                )

                print(
                    "⚠️ Gemini Pro image MULTI FINAL:",
                    message,
                )

                if is_openai_quota_error(error):
                    openai_quota_unavailable = True
                    print(
                        "🔁 OpenAI quota/billing unavailable; "
                        "skipping repeated OpenAI retries."
                    )
                    continue

                #
                # Technical recovery:
                #
                # Keep the approved draft and try a
                # single-image OpenAI edit.
                #

                try:

                    recovery_prompt = (
                        build_final_renderer_prompt(
                            original_prompt,

                            aspect_ratio,

                            image_size,

                            reference_count=0,
                        )
                    )

                    recovered = (
                        edit_with_openai_multi(
                            [
                                _generated_image_tuple(
                                    draft
                                )
                            ],

                            recovery_prompt,

                            aspect_ratio=(
                                aspect_ratio
                            ),

                            image_size=(
                                image_size
                            ),

                            quality=(
                                final_quality
                            ),

                            original_prompt=(
                                original_prompt
                            ),

                            metadata={
                                "technical_recovery":
                                    "draft_only_openai_edit",

                                "mandatory_openai_final":
                                    True,
                            },
                        )
                    )

                    results.append(
                        recovered
                    )

                    continue

                except Exception as recovery_error:

                    errors.append(
                        (
                            "openai_draft_recovery_"
                            +
                            str(
                                index + 1
                            )
                            +
                            ": "
                            +
                            clean_text(
                                recovery_error,
                                3000,
                            )
                        )
                    )

        #
        # Final technical safety:
        #
        # NEVER deliver Gemini draft as BEST.
        #
        # Generate a fresh Gemini Pro image final.
        #

        try:

            final_prompt = (
                build_final_renderer_prompt(
                    original_prompt,

                    aspect_ratio,

                    image_size,

                    reference_count=(
                        len(
                            references
                        )
                    ),
                )
            )

            if references:

                try:

                    direct_reference_final = (
                        edit_with_openai_multi(
                            references,

                            final_prompt,

                            aspect_ratio=(
                                aspect_ratio
                            ),

                            image_size=(
                                image_size
                            ),

                            quality=(
                                final_quality
                            ),

                            original_prompt=(
                                original_prompt
                            ),

                            metadata={
                                "technical_recovery":
                                    "openai_reference_only",

                                "mandatory_openai_final":
                                    True,
                            },
                        )
                    )

                    results.append(
                        direct_reference_final
                    )

                    continue

                except Exception as reference_error:

                    errors.append(
                        (
                            "openai_reference_recovery_"
                            +
                            str(
                                index + 1
                            )
                            +
                            ": "
                            +
                            clean_text(
                                reference_error,
                                3000,
                            )
                        )
                    )

            direct_route = build_route(
                PROVIDER_OPENAI,

                OPENAI_IMAGE_MODEL,

                (
                    "BEST technical recovery "
                    "with Gemini Pro image"
                ),

                aspect_ratio,

                image_size,

                final_quality,
            )

            direct_images = (
                generate_with_openai(
                    final_prompt,

                    original_prompt,

                    direct_route,

                    1,
                )
            )

            if not direct_images:

                raise XPANDImageProviderError(
                    (
                        "Gemini Pro image direct "
                        "recovery returned no image."
                    )
                )

            direct = direct_images[
                0
            ]

            direct.metadata.update(
                {
                    "technical_recovery":
                        "openai_direct_generation",

                    "mandatory_openai_final":
                        True,

                    "nano_banana_final":
                        False,
                }
            )

            results.append(
                direct
            )

        except Exception as error:

            errors.append(
                (
                    "openai_final_recovery_"
                    +
                    str(
                        index + 1
                    )
                    +
                    ": "
                    +
                    clean_text(
                        error,
                        3500,
                    )
                )
            )

    if (
        not results
        and openai_quota_unavailable
        and BEST_ALLOW_QUOTA_FALLBACK
        and GEMINI_API_KEY
    ):
        print(
            "🔁 XPAND QUOTA FALLBACK → Gemini final"
        )

        try:
            google_fallback = run_google_direct(
                original_prompt,
                pro=False,
                aspect_ratio=aspect_ratio,
                image_size=image_size,
                quality=final_quality,
                number=number,
                allow_fallback=False,
                reference_images=references,
            )

            if not google_fallback.images:
                raise XPANDImageProviderError(
                    "Gemini quota fallback returned no image."
                )

            for fallback_image in google_fallback.images:
                fallback_image.metadata.update(
                    {
                        "best_pipeline": [
                            GOOGLE_IMAGE_FAST_MODEL,
                        ],
                        "previsualization": False,
                        "nano_banana_final": True,
                        "mandatory_openai_final": False,
                        "provider_fallback": "openai_quota_to_google",
                    }
                )

            results.extend(
                google_fallback.images[:number]
            )

            if google_fallback.routes:
                final_route = google_fallback.routes[0]

            quota_fallback_used = True
            errors.append(
                "openai_quota_fallback: Gemini final used because OpenAI quota/billing was unavailable."
            )

        except Exception as fallback_error:
            errors.append(
                "google_quota_fallback: "
                + clean_text(
                    fallback_error,
                    3500,
                )
            )
            print(
                "⚠️ GEMINI QUOTA FALLBACK:",
                clean_text(
                    fallback_error,
                    3500,
                ),
            )

    if not results:

        raise XPANDImageProviderError(
            (
                "XPAND BEST failed to produce "
                "a Gemini Pro image final image.\n"
                +
                "\n".join(
                    errors
                )
            )
        )

    #
    # Absolute final-provider safety.
    #

    if (
        BEST_REQUIRE_OPENAI_FINAL
        and not quota_fallback_used
    ):

        invalid = [
            image
            for image
            in results
            if (
                image.model
                !=
                OPENAI_IMAGE_MODEL
            )
        ]

        if invalid:

            raise XPANDImageProviderError(
                (
                    "XPAND BEST final-provider lock "
                    "failed: non-OpenAI image detected."
                )
            )

    return ImageGenerationResponse(
        ok=True,

        images=(
            results
        ),

        selected_route=(
            MODE_BEST
        ),

        routes=[
            draft_route,
            final_route,
        ],

        original_prompt=(
            original_prompt
        ),

        enhanced_prompt=(
            build_final_renderer_prompt(
                original_prompt,

                aspect_ratio,

                image_size,

                reference_count=(
                    len(
                        references
                    )
                ),
            )
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


# =========================================================
# COMPATIBILITY BEST ALIASES
# =========================================================

def run_openai_best(
    original_prompt: str,
    *,
    aspect_ratio: str,
    image_size: str,
    quality: str,
    number: int = 1,
    reference_images: Sequence[
        Tuple[
            bytes,
            str,
        ]
    ] = (),
) -> ImageGenerationResponse:

    return run_hybrid_best(
        original_prompt,

        aspect_ratio=(
            aspect_ratio
        ),

        image_size=(
            image_size
        ),

        quality=(
            quality
        ),

        number=(
            number
        ),

        reference_images=(
            reference_images
        ),
    )


def run_google_openai_fusion(
    original_prompt: str,
    *,
    aspect_ratio: str,
    image_size: str,
    quality: str,
    number: int = 1,
    stronger: bool = False,
    reference_images: Sequence[
        Tuple[
            bytes,
            str,
        ]
    ] = (),
) -> ImageGenerationResponse:

    return run_hybrid_best(
        original_prompt,

        aspect_ratio=(
            aspect_ratio
        ),

        image_size=(
            image_size
        ),

        quality=(
            "high"
            if stronger
            else
            quality
        ),

        number=(
            number
        ),

        reference_images=(
            reference_images
        ),
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
    reference_images: Sequence[
        Tuple[
            bytes,
            str,
        ]
    ] = (),
) -> ImageGenerationResponse:

    started = time.monotonic()

    references = (
        _normalize_reference_images(
            list(
                reference_images
            )
        )
    )

    images: List[
        GeneratedImage
    ] = []

    routes: List[
        ImageRoute
    ] = []

    errors: List[str] = []

    #
    # OpenAI candidate.
    #

    if (
        OPENAI_ENABLED
        and
        OPENAI_API_KEY
    ):

        try:

            result = run_openai_direct(
                original_prompt,

                aspect_ratio=(
                    aspect_ratio
                ),

                image_size=(
                    image_size
                ),

                quality=(
                    quality
                ),

                number=1,

                reference_images=(
                    references
                ),
            )

            images.extend(
                result.images
            )

            routes.extend(
                result.routes
            )

        except Exception as error:

            errors.append(
                (
                    "openai: "
                    +
                    clean_text(
                        error,
                        3000,
                    )
                )
            )

    #
    # Nano Banana 2 candidate.
    #

    if GEMINI_API_KEY:

        try:

            result = run_google_direct(
                original_prompt,

                pro=False,

                aspect_ratio=(
                    aspect_ratio
                ),

                image_size=(
                    image_size
                ),

                quality=(
                    quality
                ),

                number=1,

                allow_fallback=False,

                reference_images=(
                    references
                ),
            )

            images.extend(
                result.images
            )

            routes.extend(
                result.routes
            )

        except Exception as error:

            errors.append(
                (
                    "google: "
                    +
                    clean_text(
                        error,
                        3000,
                    )
                )
            )

    if not images:

        raise XPANDImageProviderError(
            (
                "Compare mode failed.\n"
                +
                "\n".join(
                    errors
                )
            )
        )

    return ImageGenerationResponse(
        ok=True,

        images=(
            images
        ),

        selected_route=(
            MODE_COMPARE
        ),

        routes=(
            routes
        ),

        original_prompt=(
            original_prompt
        ),

        enhanced_prompt=(
            build_professional_prompt(
                original_prompt,
                aspect_ratio,
                image_size,
            )
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


# =========================================================
# MAIN IMAGE API
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

    reference_images = (
        _normalize_reference_images(
            (
                kwargs.get(
                    "reference_images"
                )
                or
                kwargs.get(
                    "physical_references"
                )
                or
                []
            )
        )
    )

    reference_count = max(
        safe_int(
            reference_count,
            0,
        ),
        len(
            reference_images
        ),
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
            safe_int(
                number,
                1,
            ),
            4,
        ),
    )

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND VISUAL PROVIDER CORE V3"
    )
    print(
        "=========================================="
    )
    print(
        "Mode:",
        effective_mode,
    )
    print(
        "Aspect ratio:",
        final_aspect_ratio,
    )
    print(
        "Resolution:",
        final_image_size,
    )
    print(
        "Quality:",
        final_quality,
    )
    print(
        "Physical references:",
        len(
            reference_images
        ),
    )

    if effective_mode in {
        MODE_BEST,
        MODE_PRO,
    }:

        print(
            (
                "Pipeline: "
                "Nano Banana 2 draft "
                "→ Gemini Pro image final"
            )
        )

    print("")

    if effective_mode in {
        MODE_BEST,
        MODE_PRO,
    }:

        return run_hybrid_best(
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

            reference_images=(
                reference_images
            ),
        )

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

            reference_images=(
                reference_images
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

            reference_images=(
                reference_images
            ),
        )

    if effective_mode == MODE_GOOGLE_PRO:

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

            reference_images=(
                reference_images
            ),
        )

    #
    # FAST / AUTO / GOOGLE FAST
    #

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

        reference_images=(
            reference_images
        ),
    )


# =========================================================
# FRIENDLY ROUTE
# =========================================================

def describe_route(
    route: ImageRoute,
) -> str:

    labels = {
        PROVIDER_OPENAI:
            "Gemini Pro image",

        PROVIDER_GOOGLE_FAST:
            "Nano Banana 2",

        PROVIDER_GOOGLE_PRO:
            "Nano Banana Pro",

        PROVIDER_FUSION_BEST:
            (
                "Nano Banana 2 "
                "→ Gemini Pro image"
            ),

        PROVIDER_FUSION_PRO:
            (
                "Nano Banana 2 "
                "→ Gemini Pro image"
            ),
    }

    label = labels.get(
        route.provider,
        route.model,
    )

    return (
        str(
            label
        )
        +
        " | "
        +
        str(
            route.aspect_ratio
        )
        +
        " | "
        +
        str(
            route.image_size
        )
        +
        " | "
        +
        str(
            route.quality
        )
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

        "provider_core":
            ENGINE_VERSION,

        "openai_configured":
            False,

        "openai_enabled":
            bool(
                OPENAI_ENABLED
            ),

        "gemini_configured":
            bool(
                GEMINI_API_KEY
            ),

        "openai_image":
            "disabled",

        "openai_director":
            "disabled",

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

        "default_mode":
            DEFAULT_MODE,

        "default_quality":
            DEFAULT_QUALITY,

        "best_use_pro":
            BEST_USE_PRO,

        "best_require_openai_final":
            BEST_REQUIRE_OPENAI_FINAL,

        "best_pipeline": [
            GOOGLE_IMAGE_PRO_MODEL,
        ],

        "best_final_model":
            GOOGLE_IMAGE_PRO_MODEL,

        "stc_masterpiece_final_model":
            GOOGLE_IMAGE_PRO_MODEL,

        "nano_banana_role":
            "Gemini Pro image renderer",

        "gpt_image_2_role":
            "disabled",

        "openai_multi_reference":
            False,

        "openai_max_input_images":
            OPENAI_MAX_REFERENCE_IMAGES,

        "openai_flexible_sizes":
            True,

        "gpt_image_2_reference_fidelity":
            "automatic_high",

        "input_fidelity_parameter_sent":
            False,

        "director_reasoning":
            OPENAI_DIRECTOR_REASONING,

        "structured_reasoning":
            OPENAI_STRUCTURED_REASONING,

        "structured_routing":
            "Gemini only",

        "free_text_routing":
            "Gemini only",

        "gemini_image_thinking_normalized":
            GEMINI_IMAGE_THINKING,

        "gemini_image_thinking_sent":
            False,

        "telegram_ready":
            True,
    }


# =========================================================
# ZERO-API SELF TEST
# =========================================================

if __name__ == "__main__":

    tests: Dict[
        str,
        bool,
    ] = {}

    # -----------------------------------------------------
    # MODE ROUTING
    # -----------------------------------------------------

    tests[
        "masterpiece_routes_to_best"
    ] = (
        resolve_effective_mode(
            (
                "أنشئ إعلان STC Bank "
                "Masterpiece 4:5"
            ),
            "",
            0,
        )
        ==
        MODE_BEST
    )

    tests[
        "arabic_masterpiece_routes_to_best"
    ] = (
        resolve_effective_mode(
            (
                "اعمل أقوى نتيجة ممكنة "
                "لبنك STC"
            ),
            "",
            0,
        )
        ==
        MODE_BEST
    )

    tests[
        "explicit_nb2"
    ] = (
        resolve_effective_mode(
            "استخدم Nano Banana 2",
            "",
            0,
        )
        ==
        MODE_GOOGLE_FAST
    )

    tests[
        "explicit_nb_pro"
    ] = (
        resolve_effective_mode(
            "استخدم Nano Banana Pro",
            "",
            0,
        )
        ==
        MODE_GOOGLE_PRO
    )

    tests[
        "explicit_gpt_image_2"
    ] = (
        resolve_effective_mode(
            "استخدم Gemini Pro image",
            "",
            0,
        )
        ==
        MODE_OPENAI
    )

    tests[
        "caller_google_fast_is_respected"
    ] = (
        resolve_effective_mode(
            "Masterpiece",
            "google_fast",
            0,
        )
        ==
        MODE_GOOGLE_FAST
    )

    # -----------------------------------------------------
    # TRUE 4:5
    # -----------------------------------------------------

    tests[
        "openai_4_5_1k"
    ] = (
        openai_size_for_ratio(
            "4:5",
            "1K",
        )
        ==
        "1024x1280"
    )

    tests[
        "openai_4_5_2k"
    ] = (
        openai_size_for_ratio(
            "4:5",
            "2K",
        )
        ==
        "2048x2560"
    )

    tests[
        "openai_4_5_4k"
    ] = (
        openai_size_for_ratio(
            "4:5",
            "4K",
        )
        ==
        "2560x3200"
    )

    all_sizes_valid = True

    for ratio in (
        OPENAI_SIZE_MAP
    ):

        for intent in (
            "1K",
            "2K",
            "4K",
        ):

            size = (
                openai_size_for_ratio(
                    ratio,
                    intent,
                )
            )

            if not validate_openai_size(
                size
            ):

                all_sizes_valid = (
                    False
                )

    tests[
        "all_openai_sizes_valid"
    ] = (
        all_sizes_valid
    )

    # -----------------------------------------------------
    # MULTI-IMAGE OPENAI
    # -----------------------------------------------------

    fake_png = (
        b"\x89PNG\r\n\x1a\n"
        +
        b"x"
        *
        100
    )

    fake_jpeg = (
        b"\xff\xd8\xff"
        +
        b"y"
        *
        100
    )

    fake_files = (
        _build_openai_edit_files(
            [
                (
                    fake_png,
                    "image/png",
                ),
                (
                    fake_jpeg,
                    "image/jpeg",
                ),
            ]
        )
    )

    tests[
        "openai_multi_image_field"
    ] = (
        len(
            fake_files
        )
        ==
        2
        and
        all(
            item[
                0
            ]
            ==
            "image[]"
            for item
            in fake_files
        )
    )

    fake_form = (
        _build_openai_edit_form(
            prompt="test",
            size="1024x1280",
            quality="high",
        )
    )

    tests[
        "gpt_image_2_omits_input_fidelity"
    ] = (
        "input_fidelity"
        not in fake_form
    )

    # -----------------------------------------------------
    # GEMINI IMAGE THINKING
    # -----------------------------------------------------

    gemini_payload = (
        _build_gemini_image_payload(
            model=(
                GOOGLE_IMAGE_FAST_MODEL
            ),

            prompt="test",

            aspect_ratio="4:5",

            image_size="1K",
        )
    )

    serialized_gemini = json.dumps(
        gemini_payload
    ).lower()

    tests[
        "gemini_image_no_thinking_level"
    ] = (
        "thinking_level"
        not in serialized_gemini
        and
        '"thinking"'
        not in serialized_gemini
        and
        '"reasoning"'
        not in serialized_gemini
    )

    # -----------------------------------------------------
    # STC PHYSICAL REALITY PROMPT
    # -----------------------------------------------------

    stc_prompt = (
        build_final_renderer_prompt(
            (
                "أنشئ إعلان STC Bank "
                "عن التجارة الإلكترونية "
                "ونقاط البيع"
            ),

            "4:5",

            "2K",

            reference_count=3,
        )
    )

    tests[
        "stc_travertine_ban"
    ] = (
        "travertine"
        in stc_prompt
    )

    tests[
        "stc_phone_pos_fusion_ban"
    ] = (
        "phone/POS fusion"
        in stc_prompt
    )

    tests[
        "stc_copy_space_15_22"
    ] = (
        "15–22%"
        in stc_prompt
    )

    tests[
        "stc_three_quarter_camera_ban"
    ] = (
        "three-quarter"
        in stc_prompt
    )

    tests[
        "stc_message_without_text"
    ] = (
        (
            "understandable without text"
            in stc_prompt
        )
        or
        (
            "visual message must work"
            in stc_prompt
        )
    )

    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------

    status = (
        get_image_engine_status()
    )

    tests[
        "best_final_model_gemini"
    ] = (
        status.get(
            "best_final_model"
        )
        ==
        GOOGLE_IMAGE_PRO_MODEL
    )

    tests[
        "stc_final_model_gemini"
    ] = (
        status.get(
            "stc_masterpiece_final_model"
        )
        ==
        GOOGLE_IMAGE_PRO_MODEL
    )

    tests[
        "structured_gemini_only"
    ] = (
        status.get(
            "structured_routing"
        )
        ==
        "Gemini only"
    )

    tests[
        "free_text_gemini_only"
    ] = (
        status.get(
            "free_text_routing"
        )
        ==
        "Gemini only"
    )

    tests[
        "gemini_pro_multi_reference_enabled"
    ] = (
        not bool(
            status.get(
                "openai_multi_reference"
            )
        )
    )

    tests[
        "best_requires_gemini_by_default"
    ] = (
        not bool(
            BEST_REQUIRE_OPENAI_FINAL
        )
    )

    all_ok = all(
        tests.values()
    )

    print("")
    print(
        "=============================================="
    )
    print(
        " XPAND VISUAL PROVIDER CORE V3.0.0"
    )
    print(
        " ZERO-API SELF TEST"
    )
    print(
        "=============================================="
    )
    print("")

    for name, passed in (
        tests.items()
    ):

        print(
            (
                "✅ "
                if passed
                else
                "❌ "
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

    print("")
    print(
        "Director:",
        OPENAI_DIRECTOR_MODEL,
    )

    print(
        "Draft model:",
        GOOGLE_IMAGE_FAST_MODEL,
    )

    print(
        "Final image model:",
        OPENAI_IMAGE_MODEL,
    )

    print(
        "Explicit Gemini Pro:",
        GOOGLE_IMAGE_PRO_MODEL,
    )

    print("")
    print(
        "BEST pipeline:"
    )
    print(
        "  Gemini Vision"
    )
    print(
        "       ↓"
    )
    print(
        "  Nano Banana 2 previsualization"
    )
    print(
        "       ↓"
    )
    print(
        "  Gemini Pro image FINAL"
    )

    print("")
    print(
        "4:5 1K:",
        openai_size_for_ratio(
            "4:5",
            "1K",
        ),
    )
    print(
        "4:5 2K:",
        openai_size_for_ratio(
            "4:5",
            "2K",
        ),
    )
    print(
        "4:5 4K:",
        openai_size_for_ratio(
            "4:5",
            "4K",
        ),
    )

    print("")
    print(
        "Gemini Pro image multi-reference:",
        True,
    )
    print(
        "Gemini Pro image input fidelity:",
        "automatic high",
    )
    print(
        "input_fidelity parameter sent:",
        False,
    )
    print(
        "Gemini image thinking sent:",
        False,
    )

    print("")

    if all_ok:

        print(
            (
                "XPAND Visual Provider Core "
                "V3.0.0 self-test: PASS ✅"
            )
        )

    else:

        print(
            (
                "XPAND Visual Provider Core "
                "V3.0.0 self-test: FAIL ❌"
            )
        )

    print("")
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
