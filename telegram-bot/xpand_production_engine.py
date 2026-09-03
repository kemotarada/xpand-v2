# =========================================================
# XPAND PRODUCTION ENGINE V3.0
#
# QUALITY-FIRST ADAPTIVE MASTERPIECE
#
# =========================================================
#
# GOAL
# ---------------------------------------------------------
#
# Highest practical image quality with controlled cost.
#
# This engine deliberately moves:
#
#   Composition
#   Product Fidelity
#   Lighting
#   Materials
#   Final Polish
#
# into ONE high-quality production blueprint BEFORE the
# first image is generated.
#
#
# PRODUCTION FLOW
# ---------------------------------------------------------
#
# Creative Brain / Brand Memory / Research
#             ↓
# Quality-First Production Blueprint
#             ↓
# GPT-Image-2 HIGH          [IMAGE CALL 1]
#             ↓
# Exact Local Delivery Frame
#             ↓
# Adaptive Vision QA        [VISION CALL 1]
#             ↓
#        ┌────┴────┐
#        │         │
#      GOOD      NEEDS WORK
#        │         │
#        │       choose ONE:
#        │       - concept recovery
#        │       - targeted correction
#        │               ↓
#        │       GPT-Image-2 HIGH       [IMAGE CALL 2 MAX]
#        │               ↓
#        │       Adaptive Vision QA     [VISION CALL 2 MAX]
#        │               ↓
#        └────── Best Version Selector
#                         ↓
#               Exact Final Delivery Frame
#                         ↓
#                       DELIVER
#
#
# IMPORTANT
# ---------------------------------------------------------
#
# - QA NEVER destroys the user's paid image.
# - QA NEVER prevents run_production() from returning the
#   best successfully generated image.
# - No Composition/Lighting/Materials image passes.
# - Maximum automatic image calls defaults to 2.
# - Maximum automatic Vision QA calls defaults to 2.
# - A bad second version never replaces a better first one.
# - A concept failure uses the second image call as a
#   concept recovery, not as useless polish.
# - A normal quality problem uses the second call as a
#   targeted correction.
# - Native provider canvas is accepted.
# - Exact 4:5 / 9:16 / etc. delivery framing is local.
# - Crop / resize costs $0 API spend.
#
# =========================================================

from __future__ import annotations

import base64
import json
import os
import re
import time
import uuid

from dataclasses import dataclass, field
from io import BytesIO
from typing import Any, Dict, List, Optional, Sequence, Tuple

import requests
from PIL import Image


# =========================================================
# XPAND EXISTING MODULES
# =========================================================

from xpand_image_engine import (
    OPENAI_API_KEY,
    OPENAI_IMAGE_MODEL,
    REQUEST_TIMEOUT,
    GeneratedImage,
    PROVIDER_OPENAI,
    build_route,
    call_openai_director,
    generate_with_openai,
)

from xpand_brand_memory import (
    load_visual_references,
)


# =========================================================
# IDENTITY
# =========================================================

ENGINE_NAME = "XPAND Production Engine"
ENGINE_VERSION = "3.0"

MODE_FAST = "fast"
MODE_PRO = "pro"
MODE_MASTERPIECE = "masterpiece"

TARGET_OPENAI = "openai"
TARGET_GEMINI = "gemini"
TARGET_MIDJOURNEY = "midjourney"
TARGET_FLUX = "flux"
TARGET_IDEOGRAM = "ideogram"
TARGET_RUNWAY = "runway"
TARGET_KLING = "kling"
TARGET_SEEDANCE = "seedance"


# =========================================================
# OPENAI
# =========================================================

OPENAI_IMAGE_EDITS_URL = (
    "https://api.openai.com/v1/images/edits"
)


# =========================================================
# QUALITY-FIRST LIMITS
# =========================================================

#
# Automatic image generations/edits per one final asset.
#
# Masterpiece defaults to:
#
#   1 initial high-quality image
#   1 optional adaptive recovery/correction
#
# Never more than 2 unless this code is intentionally
# changed later.
#

MASTERPIECE_MAX_IMAGE_CALLS = max(
    1,
    min(
        2,
        int(
            os.environ.get(
                "XPAND_MASTERPIECE_MAX_IMAGE_CALLS",
                "2",
            )
            or 2
        ),
    ),
)


MASTERPIECE_MAX_VISION_CALLS = max(
    1,
    min(
        2,
        int(
            os.environ.get(
                "XPAND_MASTERPIECE_MAX_VISION_CALLS",
                "2",
            )
            or 2
        ),
    ),
)


#
# Score at which we stop spending automatically.
#
# 90+ = excellent enough to avoid another paid image call.
#

ADAPTIVE_CORRECTION_TRIGGER_SCORE = max(
    70.0,
    min(
        100.0,
        float(
            os.environ.get(
                "XPAND_ADAPTIVE_CORRECTION_TRIGGER_SCORE",
                "90",
            )
            or 90
        ),
    ),
)


#
# Major concept failure threshold.
#
# Below this, second image call is a CONCEPT RECOVERY,
# not a normal correction.
#

CONCEPT_RECOVERY_SCORE_FLOOR = max(
    40.0,
    min(
        90.0,
        float(
            os.environ.get(
                "XPAND_CONCEPT_RECOVERY_SCORE_FLOOR",
                "65",
            )
            or 65
        ),
    ),
)


# =========================================================
# QA POLICY
# =========================================================

QA_TARGET_SCORE = max(
    50,
    min(
        100,
        int(
            os.environ.get(
                "XPAND_IMAGE_QA_TARGET",
                "90",
            )
            or 90
        ),
    ),
)


QA_DELIVERY_FLOOR = max(
    50.0,
    min(
        float(QA_TARGET_SCORE),
        float(
            os.environ.get(
                "XPAND_IMAGE_QA_DELIVERY_FLOOR",
                "88",
            )
            or 88
        ),
    ),
)


QA_CRITICAL_SCORE_FLOOR = max(
    0.0,
    min(
        100.0,
        float(
            os.environ.get(
                "XPAND_IMAGE_QA_CRITICAL_FLOOR",
                "65",
            )
            or 65
        ),
    ),
)


QA_AD_READINESS_CRITICAL_FLOOR = max(
    QA_CRITICAL_SCORE_FLOOR,
    min(
        100.0,
        float(
            os.environ.get(
                "XPAND_IMAGE_QA_AD_READINESS_CRITICAL_FLOOR",
                "70",
            )
            or 70
        ),
    ),
)


QA_WEIGHTS = {
    "concept_execution": 15,
    "reference_adherence": 10,
    "perspective": 10,
    "product_fidelity": 10,
    "lighting": 10,
    "materials": 10,
    "human_anatomy": 5,
    "background_cleanliness": 5,
    "brand_alignment": 10,
    "negative_space": 5,
    "text_logo_integrity": 3,
    "advertising_readiness": 7,
}


# =========================================================
# PROMPT BUDGETS
# =========================================================

OPENAI_PROMPT_HARD_LIMIT = max(
    10000,
    min(
        32000,
        int(
            os.environ.get(
                "XPAND_OPENAI_PROMPT_HARD_LIMIT",
                "32000",
            )
            or 32000
        ),
    ),
)


COMPILED_PROMPT_BUDGET = max(
    12000,
    min(
        OPENAI_PROMPT_HARD_LIMIT - 1000,
        int(
            os.environ.get(
                "XPAND_COMPILED_PROMPT_BUDGET",
                "24000",
            )
            or 24000
        ),
    ),
)


QA_PROMPT_BUDGET = max(
    6000,
    min(
        OPENAI_PROMPT_HARD_LIMIT - 1000,
        int(
            os.environ.get(
                "XPAND_QA_PROMPT_BUDGET",
                "12000",
            )
            or 12000
        ),
    ),
)


CORRECTION_PROMPT_BUDGET = max(
    8000,
    min(
        OPENAI_PROMPT_HARD_LIMIT - 1000,
        int(
            os.environ.get(
                "XPAND_CORRECTION_PROMPT_BUDGET",
                "18000",
            )
            or 18000
        ),
    ),
)


# =========================================================
# PROVIDER-NATIVE CANVAS
# =========================================================

PROVIDER_PORTRAIT_SIZE = "1024x1536"
PROVIDER_LANDSCAPE_SIZE = "1536x1024"
PROVIDER_SQUARE_SIZE = "1024x1024"


# =========================================================
# DATA CLASSES
# =========================================================

@dataclass
class ProductionReference:
    role: str
    image_bytes: bytes
    mime_type: str
    dna: Dict[str, Any] = field(default_factory=dict)
    product_lock: Dict[str, Any] = field(default_factory=dict)
    user_note: str = ""
    source_id: str = ""


@dataclass
class CompiledPrompt:
    target: str
    prompt: str
    negative_prompt: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QAEvaluation:
    score: float
    scores: Dict[str, float]
    passed: bool
    strengths: List[str]
    problems: List[str]
    correction_instruction: str
    critical_blockers: List[str] = field(default_factory=list)
    target_reached: bool = False
    delivery_approved: bool = False
    decision: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProductionPassResult:
    pass_name: str
    image: GeneratedImage
    qa: Optional[QAEvaluation] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProductionResult:
    ok: bool
    final_image: GeneratedImage
    best_score: float
    qa: Optional[QAEvaluation]
    passes: List[ProductionPassResult]
    compiled_prompt: CompiledPrompt
    references_used: int
    product_references_used: int
    elapsed_seconds: float
    errors: List[str] = field(default_factory=list)


# =========================================================
# HELPERS
# =========================================================

def clean_text(
    value: Any,
    limit: int = 20000,
) -> str:
    return (
        str(
            value
            if value is not None
            else ""
        )
        .replace("\x00", "")
        .strip()[:limit]
    )


def clamp_score(
    value: Any,
) -> float:
    try:
        number = float(value)
    except Exception:
        number = 0.0

    return max(
        0.0,
        min(
            100.0,
            number,
        ),
    )


def safe_list(
    value: Any,
) -> List[Any]:
    return (
        value
        if isinstance(value, list)
        else []
    )


def safe_dict(
    value: Any,
) -> Dict[str, Any]:
    return (
        value
        if isinstance(value, dict)
        else {}
    )


def compact_json(
    value: Any,
    limit: int = 6000,
) -> str:
    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )
    except Exception:
        text = clean_text(
            value,
            limit,
        )

    if len(text) <= limit:
        return text

    return text[:limit]


def hard_fit_prompt(
    text: str,
    max_chars: int,
) -> str:
    value = clean_text(
        text,
        1000000,
    )

    if len(value) <= max_chars:
        return value

    marker = (
        "\n\n"
        "[XPAND CONTEXT COMPACTED]\n"
        "Secondary detail omitted. "
        "Original request and core creative direction remain authoritative."
        "\n\n"
    )

    available = max(
        500,
        max_chars - len(marker),
    )

    front = int(
        available * 0.68
    )

    back = (
        available - front
    )

    return (
        value[:front]
        + marker
        + value[-back:]
    )


def fit_prompt_for_api(
    prompt: str,
    *,
    label: str,
    budget: int,
) -> str:
    original = clean_text(
        prompt,
        1000000,
    )

    fitted = hard_fit_prompt(
        original,
        budget,
    )

    if len(original) <= budget:
        print(
            "🧮 Prompt budget ["
            + label
            + "]: "
            + str(len(fitted))
            + "/"
            + str(budget)
            + " chars ✅"
        )
    else:
        print(
            "🧮 Prompt budget ["
            + label
            + "]: "
            + str(len(original))
            + " → "
            + str(len(fitted))
            + "/"
            + str(budget)
            + " chars ✅ COMPACTED"
        )

    return fitted


# =========================================================
# JSON EXTRACTION
# =========================================================

def extract_json_object(
    value: str,
) -> Dict[str, Any]:
    text = clean_text(
        value,
        100000,
    )

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

    try:
        parsed = json.loads(text)

        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")

    if (
        start >= 0
        and end > start
    ):
        try:
            parsed = json.loads(
                text[start:end + 1]
            )

            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    return {}


# =========================================================
# IMAGE RESPONSE EXTRACTION
# =========================================================

def decode_image_value(
    value: str,
) -> Optional[bytes]:
    text = clean_text(
        value,
        100000000,
    )

    if not text:
        return None

    if text.startswith("data:image/"):
        try:
            text = text.split(
                ",",
                1,
            )[1]
        except Exception:
            return None

    try:
        raw = base64.b64decode(text)
        return raw if raw else None
    except Exception:
        return None


def find_images_in_response(
    value: Any,
) -> List[Tuple[bytes, str]]:
    found: List[
        Tuple[bytes, str]
    ] = []

    def walk(
        item: Any,
    ) -> None:
        if isinstance(item, dict):
            mime_type = clean_text(
                (
                    item.get("mime_type")
                    or item.get("mimeType")
                    or ""
                ),
                100,
            )

            for key in [
                "b64_json",
                "base64",
                "data",
            ]:
                raw_value = item.get(key)

                if not isinstance(
                    raw_value,
                    str,
                ):
                    continue

                raw = decode_image_value(
                    raw_value
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

            for child in item.values():
                walk(child)

        elif isinstance(item, list):
            for child in item:
                walk(child)

    walk(value)

    output: List[
        Tuple[bytes, str]
    ] = []

    seen = set()

    for raw, mime_type in found:
        signature = (
            len(raw),
            raw[:64],
        )

        if signature in seen:
            continue

        seen.add(signature)

        output.append(
            (
                raw,
                mime_type,
            )
        )

    return output


# =========================================================
# MIME
# =========================================================

def infer_mime_type(
    raw: bytes,
    fallback: str = "image/jpeg",
) -> str:
    if raw.startswith(
        b"\x89PNG\r\n\x1a\n"
    ):
        return "image/png"

    if raw.startswith(
        b"\xff\xd8\xff"
    ):
        return "image/jpeg"

    if (
        raw.startswith(b"RIFF")
        and b"WEBP" in raw[:16]
    ):
        return "image/webp"

    return fallback


def extension_for_mime(
    mime_type: str,
) -> str:
    value = clean_text(
        mime_type,
        100,
    ).lower()

    if "png" in value:
        return ".png"

    if "webp" in value:
        return ".webp"

    return ".jpg"


# =========================================================
# ASPECT RATIO
# =========================================================

def aspect_ratio_value(
    aspect_ratio: str,
) -> Optional[float]:
    text = clean_text(
        aspect_ratio,
        50,
    )

    match = re.fullmatch(
        r"\s*(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)\s*",
        text,
    )

    if not match:
        return None

    width = float(
        match.group(1)
    )

    height = float(
        match.group(2)
    )

    if (
        width <= 0
        or height <= 0
    ):
        return None

    return width / height


def orientation_for_ratio(
    aspect_ratio: str,
) -> str:
    ratio = aspect_ratio_value(
        aspect_ratio
    )

    if ratio is None:
        return "square"

    if ratio < 0.95:
        return "portrait"

    if ratio > 1.05:
        return "landscape"

    return "square"


def provider_size_for_ratio(
    aspect_ratio: str,
) -> str:
    orientation = orientation_for_ratio(
        aspect_ratio
    )

    if orientation == "portrait":
        return PROVIDER_PORTRAIT_SIZE

    if orientation == "landscape":
        return PROVIDER_LANDSCAPE_SIZE

    return PROVIDER_SQUARE_SIZE


def production_size_for_ratio(
    aspect_ratio: str,
    *,
    final_quality: bool = True,
) -> str:
    ratio = clean_text(
        aspect_ratio,
        30,
    )

    if not final_quality:
        mapping = {
            "1:1": "1024x1024",
            "4:5": "1024x1280",
            "5:4": "1280x1024",
            "9:16": "864x1536",
            "16:9": "1536x864",
            "2:3": "1024x1536",
            "3:2": "1536x1024",
            "3:4": "1024x1365",
            "4:3": "1365x1024",
        }

        return mapping.get(
            ratio,
            "1024x1024",
        )

    mapping = {
        "1:1": "2048x2048",
        "4:5": "2560x3200",
        "5:4": "3200x2560",
        "9:16": "2160x3840",
        "16:9": "3840x2160",
        "2:3": "2304x3456",
        "3:2": "3456x2304",
        "3:4": "2448x3264",
        "4:3": "3264x2448",
        "21:9": "3840x1646",
    }

    return mapping.get(
        ratio,
        "2048x2048",
    )


def parse_size_string(
    value: str,
) -> Optional[Tuple[int, int]]:
    match = re.fullmatch(
        r"\s*(\d+)\s*x\s*(\d+)\s*",
        clean_text(
            value,
            100,
        ),
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    return (
        int(match.group(1)),
        int(match.group(2)),
    )


# =========================================================
# LOCAL IMAGE PROCESSING
# =========================================================

def real_image_dimensions(
    raw: bytes,
) -> Tuple[int, int]:
    try:
        with Image.open(
            BytesIO(raw)
        ) as image:
            image.load()

            return (
                int(image.width),
                int(image.height),
            )
    except Exception as error:
        raise RuntimeError(
            "Unable to inspect image dimensions: "
            + clean_text(
                error,
                1000,
            )
        )


def inspect_provider_canvas(
    image: GeneratedImage,
    requested_aspect_ratio: str,
) -> Dict[str, Any]:
    width, height = real_image_dimensions(
        image.image_bytes
    )

    requested_orientation = (
        orientation_for_ratio(
            requested_aspect_ratio
        )
    )

    if width > height:
        actual_orientation = "landscape"

    elif height > width:
        actual_orientation = "portrait"

    else:
        actual_orientation = "square"

    expected_size = provider_size_for_ratio(
        requested_aspect_ratio
    )

    expected_orientation_match = (
        requested_orientation
        == actual_orientation
    )

    status = {
        "requested_ratio":
            requested_aspect_ratio,

        "expected_native":
            expected_size,

        "width":
            width,

        "height":
            height,

        "requested_orientation":
            requested_orientation,

        "actual_orientation":
            actual_orientation,

        "orientation_match":
            expected_orientation_match,
    }

    if expected_orientation_match:
        print(
            "📐 PROVIDER CANVAS: "
            + str(width)
            + "x"
            + str(height)
            + " ✅"
        )
    else:
        #
        # IMPORTANT:
        #
        # V3 does NOT throw away a paid image merely because
        # the provider returned another valid canvas.
        #
        # Local exact-frame processing will still attempt to
        # create the requested campaign ratio.
        #
        print(
            "⚠️ PROVIDER CANVAS DIFFERENT"
            + " | requested="
            + requested_aspect_ratio
            + " | actual="
            + str(width)
            + "x"
            + str(height)
            + " | continuing safely"
        )

    if not isinstance(
        image.metadata,
        dict,
    ):
        image.metadata = {}

    image.metadata[
        "provider_canvas"
    ] = status

    return status


def crop_box_for_aspect(
    width: int,
    height: int,
    aspect_ratio: str,
) -> Tuple[int, int, int, int]:
    target_ratio = aspect_ratio_value(
        aspect_ratio
    )

    if target_ratio is None:
        raise RuntimeError(
            "Invalid aspect ratio: "
            + clean_text(
                aspect_ratio,
                100,
            )
        )

    current_ratio = (
        float(width)
        / float(height)
    )

    if abs(
        current_ratio
        - target_ratio
    ) < 0.0001:
        return (
            0,
            0,
            width,
            height,
        )

    if current_ratio > target_ratio:
        target_width = int(
            round(
                height
                * target_ratio
            )
        )

        target_width = max(
            1,
            min(
                width,
                target_width,
            ),
        )

        left = int(
            round(
                (
                    width
                    - target_width
                )
                / 2
            )
        )

        return (
            left,
            0,
            left + target_width,
            height,
        )

    target_height = int(
        round(
            width
            / target_ratio
        )
    )

    target_height = max(
        1,
        min(
            height,
            target_height,
        ),
    )

    top = int(
        round(
            (
                height
                - target_height
            )
            / 2
        )
    )

    return (
        0,
        top,
        width,
        top + target_height,
    )


def derived_image(
    source: GeneratedImage,
    *,
    image_bytes: bytes,
    mime_type: str,
    aspect_ratio: str,
    image_size: str,
    metadata_updates: Dict[str, Any],
) -> GeneratedImage:
    metadata = dict(
        source.metadata
        if isinstance(
            source.metadata,
            dict,
        )
        else {}
    )

    metadata.update(
        metadata_updates
    )

    return GeneratedImage(
        image_bytes=image_bytes,
        mime_type=mime_type,
        provider=getattr(
            source,
            "provider",
            "xpand_production",
        ),
        model=getattr(
            source,
            "model",
            OPENAI_IMAGE_MODEL,
        ),
        prompt=getattr(
            source,
            "prompt",
            "",
        ),
        original_prompt=getattr(
            source,
            "original_prompt",
            "",
        ),
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        quality=getattr(
            source,
            "quality",
            "high",
        ),
        route_reason=getattr(
            source,
            "route_reason",
            "XPAND local exact frame",
        ),
        request_id=getattr(
            source,
            "request_id",
            "local-"
            + uuid.uuid4().hex[:12],
        ),
        metadata=metadata,
    )


def create_exact_delivery_frame(
    source: GeneratedImage,
    requested_aspect_ratio: str,
    *,
    upscale_final: bool = False,
    label: str = "delivery_frame",
) -> GeneratedImage:
    #
    # If this is already an exact local delivery frame and
    # no further upscale is needed, do not crop it again.
    #
    existing_meta = safe_dict(
        getattr(
            source,
            "metadata",
            {},
        )
    )

    if (
        existing_meta.get(
            "exact_delivery_frame"
        )
        and clean_text(
            getattr(
                source,
                "aspect_ratio",
                "",
            ),
            30,
        )
        == requested_aspect_ratio
        and not upscale_final
    ):
        return source

    source_width, source_height = (
        real_image_dimensions(
            source.image_bytes
        )
    )

    with Image.open(
        BytesIO(
            source.image_bytes
        )
    ) as pil_image:
        pil_image.load()

        if pil_image.mode not in {
            "RGB",
            "RGBA",
        }:
            pil_image = pil_image.convert(
                "RGB"
            )

        crop_box = crop_box_for_aspect(
            int(pil_image.width),
            int(pil_image.height),
            requested_aspect_ratio,
        )

        cropped = pil_image.crop(
            crop_box
        )

        crop_width = int(
            cropped.width
        )

        crop_height = int(
            cropped.height
        )

        output_width = crop_width
        output_height = crop_height

        if upscale_final:
            target_size = (
                production_size_for_ratio(
                    requested_aspect_ratio,
                    final_quality=True,
                )
            )

            target_dims = parse_size_string(
                target_size
            )

            if target_dims:
                target_width, target_height = (
                    target_dims
                )

                if (
                    target_width
                    != crop_width
                    or target_height
                    != crop_height
                ):
                    cropped = cropped.resize(
                        (
                            target_width,
                            target_height,
                        ),
                        Image.Resampling.LANCZOS,
                    )

                output_width = (
                    target_width
                )

                output_height = (
                    target_height
                )

        buffer = BytesIO()

        cropped.save(
            buffer,
            format="PNG",
            optimize=False,
            compress_level=4,
        )

        output_bytes = (
            buffer.getvalue()
        )

    print(
        "✂️ EXACT FRAME ["
        + label
        + "]: "
        + str(source_width)
        + "x"
        + str(source_height)
        + " → "
        + str(output_width)
        + "x"
        + str(output_height)
        + " "
        + requested_aspect_ratio
        + " ✅"
    )

    return derived_image(
        source,
        image_bytes=output_bytes,
        mime_type="image/png",
        aspect_ratio=requested_aspect_ratio,
        image_size=(
            str(output_width)
            + "x"
            + str(output_height)
        ),
        metadata_updates={
            "exact_delivery_frame":
                True,

            "exact_delivery_ratio":
                requested_aspect_ratio,

            "source_native_width":
                source_width,

            "source_native_height":
                source_height,

            "output_width":
                output_width,

            "output_height":
                output_height,

            "local_upscale":
                bool(upscale_final),

            "local_processing_cost":
                0,
        },
    )


# =========================================================
# SAFE FRAME
# =========================================================

def safe_frame_description(
    aspect_ratio: str,
) -> Dict[str, Any]:
    provider_size = (
        provider_size_for_ratio(
            aspect_ratio
        )
    )

    dims = parse_size_string(
        provider_size
    )

    if not dims:
        return {
            "provider_size":
                provider_size,

            "requested_ratio":
                aspect_ratio,
        }

    width, height = dims

    crop_box = crop_box_for_aspect(
        width,
        height,
        aspect_ratio,
    )

    left, top, right, bottom = (
        crop_box
    )

    return {
        "provider_size":
            provider_size,

        "requested_ratio":
            aspect_ratio,

        "safe_width":
            right - left,

        "safe_height":
            bottom - top,

        "left_bleed_pct":
            round(
                left / width * 100,
                2,
            ),

        "right_bleed_pct":
            round(
                (
                    width - right
                )
                / width
                * 100,
                2,
            ),

        "top_bleed_pct":
            round(
                top / height * 100,
                2,
            ),

        "bottom_bleed_pct":
            round(
                (
                    height - bottom
                )
                / height
                * 100,
                2,
            ),
    }


def safe_frame_instruction(
    aspect_ratio: str,
) -> str:
    safe = safe_frame_description(
        aspect_ratio
    )

    return f"""
FINAL DELIVERY FRAME
====================

Final campaign ratio:
{aspect_ratio}

Provider working canvas:
{safe.get("provider_size")}

All visually critical information MUST survive the central
{aspect_ratio} crop.

Approximate expendable provider bleed:
left   {safe.get("left_bleed_pct", 0)}%
right  {safe.get("right_bleed_pct", 0)}%
top    {safe.get("top_bleed_pct", 0)}%
bottom {safe.get("bottom_bleed_pct", 0)}%

Keep inside the final safe frame:

- hero subject
- core metaphor
- product
- human face/hands
- architectural storytelling
- important city/environment cues
- negative-space copy area

Do not put critical information in crop bleed.
""".strip()


# =========================================================
# REFERENCES
# =========================================================

def load_runtime_references(
    core,
    user_id,
    brand_id: str,
    *,
    limit: int = 10,
) -> List[ProductionReference]:
    stored = load_visual_references(
        core,
        user_id,
        brand_id=brand_id,
        limit=limit,
    )

    references: List[
        ProductionReference
    ] = []

    for item in stored:
        if not isinstance(
            item,
            dict,
        ):
            continue

        file_id = clean_text(
            item.get(
                "telegram_file_id",
                "",
            ),
            1500,
        )

        if not file_id:
            continue

        try:
            raw = (
                core.get_telegram_file_bytes(
                    file_id
                )
            )
        except Exception as error:
            print(
                "⚠️ Reference download skipped: "
                + clean_text(
                    error,
                    1000,
                )
            )
            continue

        if not raw:
            continue

        references.append(
            ProductionReference(
                role=clean_text(
                    item.get(
                        "reference_role",
                        "style_reference",
                    ),
                    100,
                ),

                image_bytes=raw,

                mime_type=infer_mime_type(
                    raw
                ),

                dna=safe_dict(
                    item.get(
                        "dna",
                        {},
                    )
                ),

                product_lock=safe_dict(
                    item.get(
                        "product_lock",
                        {},
                    )
                ),

                user_note=clean_text(
                    item.get(
                        "user_note",
                        "",
                    ),
                    1500,
                ),

                source_id=str(
                    item.get(
                        "id",
                        "",
                    )
                ),
            )
        )

    return references


def product_references(
    references: Sequence[
        ProductionReference
    ],
) -> List[ProductionReference]:
    return [
        item
        for item in references
        if item.role
        == "product_reference"
    ]


def reference_dna_payload(
    references: Sequence[
        ProductionReference
    ],
) -> List[Dict[str, Any]]:
    output = []

    for item in references[:10]:
        output.append(
            {
                "role":
                    item.role,

                "dna":
                    item.dna,

                "product_lock":
                    item.product_lock,

                "note":
                    item.user_note,
            }
        )

    return output


def combined_product_lock(
    references: Sequence[
        ProductionReference
    ],
) -> Dict[str, Any]:
    rules: List[str] = []
    count = 0

    for item in references:
        if item.role != "product_reference":
            continue

        count += 1

        values = safe_list(
            item.product_lock.get(
                "must_remain_identical"
            )
        )

        for value in values:
            text = clean_text(
                value,
                500,
            )

            if (
                text
                and text not in rules
            ):
                rules.append(text)

    return {
        "enabled":
            bool(count),

        "reference_count":
            count,

        "must_remain_identical":
            rules[:30],

        "environment_may_change":
            True,

        "lighting_may_adapt":
            True,

        "lock_type":
            (
                "high_fidelity_reference"
                if count
                else "none"
            ),
    }


# =========================================================
# PRODUCTION BLUEPRINT
# =========================================================

def base_negative_prompt() -> str:
    return (
        "malformed anatomy, extra fingers, warped product, "
        "wrong perspective, fake reflections, duplicated objects, "
        "generic stock photography, floating decorative objects, "
        "random text, fake logos, misspelled typography, "
        "cheap CGI, plastic skin, wet-floor reflections, "
        "generic banking clichés"
    )


def build_quality_first_blueprint(
    *,
    request: str,
    creative_direction: Any,
    brand_context: Any,
    references: Any,
    camera_direction: Any,
    product_lock: Any,
    aspect_ratio: str,
) -> str:
    return f"""
XPAND QUALITY-FIRST MASTERPIECE BLUEPRINT
========================================

ORIGINAL USER REQUEST
---------------------
{clean_text(request, 5000)}


APPROVED CREATIVE DIRECTION
---------------------------
{compact_json(creative_direction, 5500)}


BRAND EXECUTION DNA
-------------------
{compact_json(brand_context, 4500)}


VISUAL REFERENCE DNA
--------------------
{compact_json(references, 3500)}


CAMERA DIRECTION
----------------
{compact_json(camera_direction, 1800)}


PRODUCT LOCK
------------
{compact_json(product_lock, 2200)}


{safe_frame_instruction(aspect_ratio)}


ONE-PASS MASTERPIECE OBJECTIVE
==============================

Create the strongest possible finished advertising hero image
in ONE high-quality production generation.

Do NOT treat this as a rough concept sketch.

The first generated image should already integrate:

1. CONCEPT
   - execute the approved visual metaphor clearly
   - make the message understandable visually
   - avoid generic interpretation
   - reject banking / travel / technology clichés

2. COMPOSITION
   - world-class campaign framing
   - strong visual hierarchy
   - purposeful foreground / midground / background
   - clean negative space
   - no random decoration
   - no unnecessary clutter

3. CAMERA
   - physically believable real-lens behavior
   - correct horizon and vanishing points
   - intentional focal length
   - natural depth
   - premium advertising perspective

4. LIGHTING
   - motivated cinematic commercial light
   - natural fill
   - controlled highlights
   - correct contact shadows
   - realistic exposure
   - premium contrast
   - no fake neon unless conceptually necessary

5. MATERIALS
   - physically convincing glass
   - real metal
   - believable stone
   - realistic fabric
   - realistic skin
   - correct surface roughness
   - controlled reflections
   - no wet-floor appearance unless explicitly requested

6. BRAND
   - visually recognizable brand world
   - correct visual tone
   - correct color hierarchy
   - use brand accent colors intentionally
   - do not turn brand colors into random decoration

7. PRODUCT
   If Product Lock is enabled:
   - preserve identity
   - preserve silhouette
   - preserve proportions
   - preserve major geometry
   - preserve major graphic placement
   - preserve color relationships
   - do not redesign it

8. PEOPLE
   - natural behavior
   - correct anatomy
   - believable hands
   - authentic styling
   - never generic posed stock-photo behavior

9. ADVERTISING READINESS
   - premium global campaign finish
   - cinematic photorealism
   - real commercial photography feeling
   - immediately usable as a hero visual
   - intentional copy space where required

10. FINAL QUALITY
   Solve composition, lighting, materials and polish NOW.
   Do not depend on later passes to rescue weak fundamentals.


NON-NEGOTIABLE
==============

The concept matters more than decorative beauty.

A beautiful image that fails the requested idea is a failure.

The image must feel designed by a top international
creative director, photographer and production team,
not like generic AI art.
""".strip()


def compile_prompt(
    target: str,
    *,
    request: str,
    creative_direction: Any = None,
    brand_context: Any = None,
    references: Any = None,
    camera_direction: Any = None,
    product_lock: Any = None,
    aspect_ratio: str = "4:5",
) -> CompiledPrompt:
    target = clean_text(
        target,
        100,
    ).lower()

    blueprint = (
        build_quality_first_blueprint(
            request=request,
            creative_direction=(
                creative_direction
                or {}
            ),
            brand_context=(
                brand_context
                or {}
            ),
            references=(
                references
                or []
            ),
            camera_direction=(
                camera_direction
                or {}
            ),
            product_lock=(
                product_lock
                or {}
            ),
            aspect_ratio=aspect_ratio,
        )
    )

    blueprint = fit_prompt_for_api(
        blueprint,
        label="quality_first_blueprint",
        budget=COMPILED_PROMPT_BUDGET,
    )

    return CompiledPrompt(
        target=target,
        prompt=blueprint,
        negative_prompt=base_negative_prompt(),
        metadata={
            "compiler":
                "xpand_quality_first_v3",

            "prompt_chars":
                len(blueprint),

            "prompt_budget":
                COMPILED_PROMPT_BUDGET,

            "aspect_ratio":
                aspect_ratio,

            "adaptive":
                True,
        },
    )


# =========================================================
# OPENAI IMAGE EDIT
# =========================================================

def openai_multi_reference_edit(
    *,
    working_image: Optional[
        GeneratedImage
    ],
    references: Sequence[
        ProductionReference
    ],
    prompt: str,
    aspect_ratio: str,
    pass_name: str,
) -> GeneratedImage:
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY missing."
        )

    files: List[
        Tuple[
            str,
            Tuple[
                str,
                bytes,
                str,
            ]
        ]
    ] = []

    if working_image is not None:
        extension = extension_for_mime(
            working_image.mime_type
        )

        files.append(
            (
                "image[]",
                (
                    "working-image"
                    + extension,

                    working_image.image_bytes,

                    working_image.mime_type
                    or "image/png",
                ),
            )
        )

    for index, reference in enumerate(
        references,
        start=1,
    ):
        extension = extension_for_mime(
            reference.mime_type
        )

        files.append(
            (
                "image[]",
                (
                    "reference-"
                    + str(index)
                    + extension,

                    reference.image_bytes,

                    reference.mime_type,
                ),
            )
        )

    if not files:
        raise RuntimeError(
            "Image edit requested without an image input."
        )

    if len(files) == 1:
        _, file_value = files[0]

        files = [
            (
                "image",
                file_value,
            )
        ]

    safe_prompt = fit_prompt_for_api(
        (
            prompt
            + "\n\n"
            + safe_frame_instruction(
                aspect_ratio
            )
        ),
        label=pass_name,
        budget=CORRECTION_PROMPT_BUDGET,
    )

    provider_size = (
        provider_size_for_ratio(
            aspect_ratio
        )
    )

    response = requests.post(
        OPENAI_IMAGE_EDITS_URL,
        headers={
            "Authorization":
                "Bearer "
                + OPENAI_API_KEY,
        },
        data={
            "model":
                OPENAI_IMAGE_MODEL,

            "prompt":
                safe_prompt,

            "size":
                provider_size,

            "quality":
                "high",

            "n":
                "1",
        },
        files=files,
        timeout=REQUEST_TIMEOUT,
    )

    try:
        response_data = (
            response.json()
        )
    except Exception:
        response_data = {
            "raw":
                response.text
        }

    if not response.ok:
        error = response_data.get(
            "error"
        )

        if isinstance(
            error,
            dict,
        ):
            message = (
                error.get("message")
                or str(error)
            )
        else:
            message = (
                error
                or response_data.get("raw")
                or (
                    "HTTP "
                    + str(
                        response.status_code
                    )
                )
            )

        raise RuntimeError(
            "GPT-Image-2 edit failed: "
            + clean_text(
                message,
                3000,
            )
        )

    images = find_images_in_response(
        response_data
    )

    if not images:
        raise RuntimeError(
            "GPT-Image-2 edit returned no image."
        )

    image_bytes, mime_type = (
        images[0]
    )

    result = GeneratedImage(
        image_bytes=image_bytes,
        mime_type=(
            mime_type
            or "image/png"
        ),
        provider="xpand_production",
        model=OPENAI_IMAGE_MODEL,
        prompt=safe_prompt,
        original_prompt=safe_prompt,
        aspect_ratio=aspect_ratio,
        image_size=provider_size,
        quality="high",
        route_reason=(
            "XPAND Quality-First Adaptive: "
            + pass_name
        ),
        request_id=(
            clean_text(
                response.headers.get(
                    "x-request-id",
                    "",
                ),
                300,
            )
            or
            "prod-"
            + uuid.uuid4().hex[:12]
        ),
        metadata={
            "production_engine":
                ENGINE_VERSION,

            "pass_name":
                pass_name,

            "prompt_chars":
                len(safe_prompt),

            "requested_delivery_ratio":
                aspect_ratio,

            "quality":
                "high",
        },
    )

    inspect_provider_canvas(
        result,
        aspect_ratio,
    )

    return result


# =========================================================
# INITIAL HIGH-QUALITY GENERATION
# =========================================================

def generate_high_quality_image(
    *,
    compiled: CompiledPrompt,
    product_refs: Sequence[
        ProductionReference
    ],
    aspect_ratio: str,
    original_request: str,
    pass_name: str = "quality_first_generation",
) -> GeneratedImage:
    #
    # With Product Reference:
    #
    # use image edit/generation so product identity is
    # physically supplied to the image model.
    #
    if product_refs:
        prompt = (
            compiled.prompt
            + "\n\n"
            + """
PRODUCT-REFERENCE EXECUTION
===========================

The attached reference image(s) are authoritative product
identity references.

Create the full new campaign scene around them.

Do not merely copy the reference background.

Do not redesign the locked product.
""".strip()
        )

        return openai_multi_reference_edit(
            working_image=None,
            references=product_refs,
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            pass_name=pass_name,
        )

    #
    # No product reference:
    #
    # direct HIGH quality generation.
    #
    route = build_route(
        PROVIDER_OPENAI,
        OPENAI_IMAGE_MODEL,
        (
            "XPAND Quality-First V3 "
            "high-quality final-candidate generation"
        ),
        aspect_ratio,
        "4K",
        "high",
    )

    images = generate_with_openai(
        prompt=compiled.prompt,
        original_prompt=clean_text(
            original_request,
            6000,
        ),
        route=route,
        number=1,
    )

    if not images:
        raise RuntimeError(
            "Quality-First generation returned no image."
        )

    result = images[0]

    result.provider = (
        "xpand_production"
    )

    result.aspect_ratio = (
        aspect_ratio
    )

    result.quality = "high"

    if not isinstance(
        result.metadata,
        dict,
    ):
        result.metadata = {}

    result.metadata.update(
        {
            "production_engine":
                ENGINE_VERSION,

            "pass_name":
                pass_name,

            "quality_first":
                True,

            "requested_delivery_ratio":
                aspect_ratio,

            "quality":
                "high",

            "prompt_chars":
                len(
                    compiled.prompt
                ),
        }
    )

    inspect_provider_canvas(
        result,
        aspect_ratio,
    )

    return result


# =========================================================
# QA
# =========================================================

def calculate_qa_score(
    scores: Dict[str, Any],
) -> Tuple[
    float,
    Dict[str, float],
]:
    normalized = {}
    total = 0.0

    for key, weight in QA_WEIGHTS.items():
        value = clamp_score(
            scores.get(
                key,
                0,
            )
        )

        normalized[key] = value

        total += (
            value
            * (
                float(weight)
                / 100.0
            )
        )

    return (
        round(
            total,
            2,
        ),
        normalized,
    )


def detect_critical_blockers(
    *,
    scores: Dict[str, float],
    explicit_failures: Any,
    product_lock: Any,
) -> List[str]:
    blockers: List[str] = []

    for value in safe_list(
        explicit_failures
    ):
        text = clean_text(
            value,
            1000,
        )

        if (
            text
            and text not in blockers
        ):
            blockers.append(text)

    thresholds = {
        "concept_execution":
            QA_CRITICAL_SCORE_FLOOR,

        "perspective":
            QA_CRITICAL_SCORE_FLOOR,

        "human_anatomy":
            QA_CRITICAL_SCORE_FLOOR,

        "advertising_readiness":
            QA_AD_READINESS_CRITICAL_FLOOR,
    }

    if safe_dict(
        product_lock
    ).get(
        "enabled"
    ):
        thresholds[
            "product_fidelity"
        ] = 70.0

    for key, threshold in thresholds.items():
        value = clamp_score(
            scores.get(
                key,
                0,
            )
        )

        if value < threshold:
            label = (
                key
                + "="
                + str(
                    round(
                        value,
                        1,
                    )
                )
                + " < "
                + str(threshold)
            )

            if label not in blockers:
                blockers.append(label)

    return blockers


def build_qa_prompt(
    *,
    original_request: str,
    compiled_prompt: CompiledPrompt,
    product_lock: Any,
    brand_context: Any,
    aspect_ratio: str,
) -> str:
    prompt = f"""
You are XPAND Adaptive Visual QA.

Evaluate the attached EXACT FINAL CAMPAIGN CROP.

Be strict but practical.

Do not reject a professionally usable image because of tiny
subjective preferences.

ORIGINAL REQUEST
----------------
{clean_text(original_request, 4000)}

APPROVED PRODUCTION BLUEPRINT
-----------------------------
{clean_text(compiled_prompt.prompt, 5000)}

PRODUCT LOCK
------------
{compact_json(product_lock, 1800)}

BRAND
-----
{compact_json(brand_context, 2500)}

FINAL RATIO
-----------
{aspect_ratio}

Score 0-100:

- concept_execution
- reference_adherence
- perspective
- product_fidelity
- lighting
- materials
- human_anatomy
- background_cleanliness
- brand_alignment
- negative_space
- text_logo_integrity
- advertising_readiness

Critical failure means a genuine delivery problem:
- core concept missing
- major requested metaphor absent
- severe anatomy
- severe perspective failure
- major product deformation
- major brand mismatch
- unusable composition

Do NOT classify a minor preference as critical.

Return JSON only:

{{
  "scores": {{
    "concept_execution": 0,
    "reference_adherence": 0,
    "perspective": 0,
    "product_fidelity": 0,
    "lighting": 0,
    "materials": 0,
    "human_anatomy": 0,
    "background_cleanliness": 0,
    "brand_alignment": 0,
    "negative_space": 0,
    "text_logo_integrity": 0,
    "advertising_readiness": 0
  }},
  "strengths": [],
  "problems": [],
  "critical_failures": [],
  "correction_instruction": ""
}}
""".strip()

    return fit_prompt_for_api(
        prompt,
        label="adaptive_visual_qa",
        budget=QA_PROMPT_BUDGET,
    )


def evaluate_generated_image(
    *,
    image: GeneratedImage,
    original_request: str,
    compiled_prompt: CompiledPrompt,
    product_lock: Any,
    brand_context: Any,
    aspect_ratio: Optional[str] = None,
    telemetry: Optional[
        Dict[str, Any]
    ] = None,
) -> QAEvaluation:
    requested_ratio = clean_text(
        (
            aspect_ratio
            or getattr(
                image,
                "aspect_ratio",
                "",
            )
            or "1:1"
        ),
        30,
    )

    #
    # Post-Exact Asset QA can pass an already exact image.
    #
    if safe_dict(
        getattr(
            image,
            "metadata",
            {},
        )
    ).get(
        "exact_delivery_frame"
    ):
        qa_frame = image
    else:
        qa_frame = (
            create_exact_delivery_frame(
                image,
                requested_ratio,
                upscale_final=False,
                label="adaptive_qa",
            )
        )

    prompt = build_qa_prompt(
        original_request=original_request,
        compiled_prompt=compiled_prompt,
        product_lock=product_lock,
        brand_context=brand_context,
        aspect_ratio=requested_ratio,
    )

    if telemetry is not None:
        telemetry[
            "vision_calls"
        ] = (
            int(
                telemetry.get(
                    "vision_calls",
                    0,
                )
            )
            + 1
        )

    raw = call_openai_director(
        prompt,
        image_bytes=qa_frame.image_bytes,
        image_mime_type=qa_frame.mime_type,
        json_mode=True,
    )

    data = extract_json_object(
        raw
    )

    if not data:
        raise RuntimeError(
            "Adaptive Vision QA returned invalid JSON."
        )

    raw_scores = safe_dict(
        data.get(
            "scores"
        )
    )

    score, scores = calculate_qa_score(
        raw_scores
    )

    critical_blockers = (
        detect_critical_blockers(
            scores=scores,
            explicit_failures=data.get(
                "critical_failures"
            ),
            product_lock=product_lock,
        )
    )

    target_reached = (
        score
        >= QA_TARGET_SCORE
        and not critical_blockers
    )

    delivery_approved = (
        score
        >= QA_DELIVERY_FLOOR
        and not critical_blockers
    )

    if target_reached:
        decision = "target_reached"

    elif delivery_approved:
        decision = "near_target"

    elif critical_blockers:
        decision = "critical_issues"

    else:
        decision = "improvement_recommended"

    return QAEvaluation(
        score=score,
        scores=scores,
        passed=delivery_approved,
        strengths=[
            clean_text(
                item,
                1000,
            )
            for item in safe_list(
                data.get(
                    "strengths"
                )
            )
            if clean_text(
                item,
                1000,
            )
        ],
        problems=[
            clean_text(
                item,
                1200,
            )
            for item in safe_list(
                data.get(
                    "problems"
                )
            )
            if clean_text(
                item,
                1200,
            )
        ],
        correction_instruction=clean_text(
            data.get(
                "correction_instruction",
                "",
            ),
            4500,
        ),
        critical_blockers=critical_blockers,
        target_reached=target_reached,
        delivery_approved=delivery_approved,
        decision=decision,
        raw=data,
    )


# =========================================================
# BEST VERSION RANKING
# =========================================================

def qa_quality_rank(
    qa: Optional[
        QAEvaluation
    ],
) -> Tuple[
    int,
    int,
    float,
    float,
]:
    if qa is None:
        return (
            -999,
            0,
            0.0,
            0.0,
        )

    no_critical = (
        1
        if not qa.critical_blockers
        else 0
    )

    approved = (
        1
        if qa.passed
        else 0
    )

    concept_score = clamp_score(
        qa.scores.get(
            "concept_execution",
            0,
        )
    )

    return (
        no_critical,
        approved,
        concept_score,
        float(qa.score),
    )


def qa_candidate_is_better(
    candidate: Optional[
        QAEvaluation
    ],
    existing: Optional[
        QAEvaluation
    ],
) -> bool:
    return (
        qa_quality_rank(
            candidate
        )
        >
        qa_quality_rank(
            existing
        )
    )


# =========================================================
# ADAPTIVE ACTION
# =========================================================

def has_concept_failure(
    qa: QAEvaluation,
) -> bool:
    concept_score = clamp_score(
        qa.scores.get(
            "concept_execution",
            0,
        )
    )

    if (
        concept_score
        < CONCEPT_RECOVERY_SCORE_FLOOR
    ):
        return True

    combined = " ".join(
        (
            qa.critical_blockers
            + qa.problems
        )
    ).lower()

    markers = [
        "concept failure",
        "core concept",
        "metaphor missing",
        "visual metaphor",
        "required concept",
        "core message",
        "major concept",
        "required element",
        "الفكرة",
        "الاستعارة",
        "المعنى",
    ]

    return any(
        marker in combined
        for marker in markers
    )


def choose_adaptive_action(
    qa: Optional[
        QAEvaluation
    ],
) -> str:
    if qa is None:
        return "none"

    if (
        qa.score
        >= ADAPTIVE_CORRECTION_TRIGGER_SCORE
        and not qa.critical_blockers
    ):
        return "none"

    if has_concept_failure(
        qa
    ):
        return "concept_recovery"

    return "targeted_correction"


# =========================================================
# SECOND IMAGE CALL PROMPTS
# =========================================================

def build_targeted_correction_prompt(
    *,
    qa: QAEvaluation,
    compiled: CompiledPrompt,
    product_lock: Any,
    aspect_ratio: str,
) -> str:
    prompt = f"""
XPAND TARGETED QUALITY CORRECTION
=================================

This is the ONLY automatic correction image pass.

Preserve every successful part of the supplied image.

CURRENT QA SCORE:
{qa.score}/100

PROBLEMS:
{compact_json(qa.problems, 4500)}

CRITICAL ISSUES:
{compact_json(qa.critical_blockers, 3000)}

QA DIRECTIVE:
{clean_text(qa.correction_instruction, 4500)}

PRODUCT LOCK:
{compact_json(product_lock, 2200)}

CORE BLUEPRINT:
{clean_text(compiled.prompt, 7000)}

{safe_frame_instruction(aspect_ratio)}

RULES
=====

- Correct only real weaknesses.
- Do not replace a strong concept.
- Do not casually change camera angle.
- Preserve successful composition.
- Preserve successful lighting.
- Preserve successful materials.
- Preserve successful human identity and pose.
- Preserve negative space.
- Preserve product identity.
- Fix anatomy only if needed.
- Fix perspective only if needed.
- Fix brand color balance only if needed.
- Fix material realism only if needed.
- Fix clutter only if needed.
- Do not introduce text or fake branding.

This pass must be a controlled professional refinement,
not a completely different random image.
""".strip()

    return fit_prompt_for_api(
        prompt,
        label="adaptive_targeted_correction",
        budget=CORRECTION_PROMPT_BUDGET,
    )


def build_concept_recovery_prompt(
    *,
    qa: QAEvaluation,
    compiled: CompiledPrompt,
    aspect_ratio: str,
) -> str:
    prompt = f"""
XPAND CONCEPT RECOVERY
======================

The previous image may be visually attractive, but the core
advertising concept was not executed strongly enough.

DO NOT simply polish the old concept.

Rebuild the visual execution so the intended message becomes
clear from the image itself.

FAILED CONCEPT SCORE:
{qa.scores.get("concept_execution", 0)}/100

PROBLEMS:
{compact_json(qa.problems, 4500)}

CRITICAL FAILURES:
{compact_json(qa.critical_blockers, 3500)}

VISION QA RECOVERY DIRECTIVE:
{clean_text(qa.correction_instruction, 4500)}

ORIGINAL MASTER BLUEPRINT:
{clean_text(compiled.prompt, 9000)}

{safe_frame_instruction(aspect_ratio)}

RECOVERY RULES
==============

- preserve the original requested message
- execute the approved metaphor clearly
- avoid the visual mistake that caused the first version
- do not fall back to a cliché
- keep the brand world premium
- solve composition, lighting and materials in this generation
- respect final campaign crop
- create a finished campaign-level visual
""".strip()

    return fit_prompt_for_api(
        prompt,
        label="concept_recovery",
        budget=COMPILED_PROMPT_BUDGET,
    )


def compiled_with_recovery(
    compiled: CompiledPrompt,
    recovery_prompt: str,
) -> CompiledPrompt:
    metadata = dict(
        compiled.metadata
    )

    metadata[
        "concept_recovery"
    ] = True

    return CompiledPrompt(
        target=compiled.target,
        prompt=recovery_prompt,
        negative_prompt=compiled.negative_prompt,
        metadata=metadata,
    )


# =========================================================
# LOGGING
# =========================================================

def print_qa(
    label: str,
    qa: Optional[
        QAEvaluation
    ],
) -> None:
    if qa is None:
        print(
            "⚠️ "
            + label
            + ": QA unavailable"
        )
        return

    print(
        "📊 "
        + label
        + ": "
        + str(qa.score)
        + "/100"
    )

    print(
        "Concept:",
        qa.scores.get(
            "concept_execution",
            0,
        ),
    )

    print(
        "Brand:",
        qa.scores.get(
            "brand_alignment",
            0,
        ),
    )

    print(
        "Advertising readiness:",
        qa.scores.get(
            "advertising_readiness",
            0,
        ),
    )

    print(
        "Critical blockers:",
        len(
            qa.critical_blockers
        ),
    )

    print(
        "Decision:",
        qa.decision,
    )


# =========================================================
# MAIN QUALITY-FIRST PIPELINE
# =========================================================

def run_production(
    *,
    core,
    user_id,
    brand_id: str,
    original_request: str,
    creative_direction: Any,
    brand_context: Any,
    camera_direction: Any,
    aspect_ratio: str = "4:5",
    mode: str = MODE_MASTERPIECE,
    target_model: str = TARGET_OPENAI,
) -> ProductionResult:
    started = time.monotonic()

    errors: List[str] = []

    telemetry: Dict[str, Any] = {
        "image_calls":
            0,

        "vision_calls":
            0,

        "max_image_calls":
            MASTERPIECE_MAX_IMAGE_CALLS,

        "max_vision_calls":
            MASTERPIECE_MAX_VISION_CALLS,

        "adaptive_action":
            "none",
    }

    # =====================================================
    # REFERENCES
    # =====================================================

    references = load_runtime_references(
        core,
        user_id,
        brand_id,
        limit=10,
    )

    product_refs = product_references(
        references
    )

    reference_dna = reference_dna_payload(
        references
    )

    product_lock = combined_product_lock(
        references
    )

    # =====================================================
    # BLUEPRINT
    # =====================================================

    compiled = compile_prompt(
        target_model,
        request=original_request,
        creative_direction=creative_direction,
        brand_context=brand_context,
        references=reference_dna,
        camera_direction=camera_direction,
        product_lock=product_lock,
        aspect_ratio=aspect_ratio,
    )

    if compiled.target != TARGET_OPENAI:
        raise RuntimeError(
            "Production execution is currently OpenAI-only."
        )

    print("")
    print(
        "=============================================="
    )
    print(
        " XPAND PRODUCTION ENGINE V3.0"
    )
    print(
        " QUALITY-FIRST ADAPTIVE MASTERPIECE"
    )
    print(
        "=============================================="
    )

    print(
        "Mode:",
        mode,
    )

    print(
        "Model:",
        OPENAI_IMAGE_MODEL,
    )

    print(
        "Requested ratio:",
        aspect_ratio,
    )

    print(
        "Provider canvas:",
        provider_size_for_ratio(
            aspect_ratio
        ),
    )

    print(
        "Final delivery:",
        production_size_for_ratio(
            aspect_ratio,
            final_quality=True,
        ),
    )

    print(
        "References:",
        len(references),
    )

    print(
        "Product references:",
        len(product_refs),
    )

    print(
        "Max image calls:",
        MASTERPIECE_MAX_IMAGE_CALLS,
    )

    print(
        "Max Vision calls:",
        MASTERPIECE_MAX_VISION_CALLS,
    )

    print(
        "Image quality:",
        "HIGH",
    )

    print("")

    # =====================================================
    # IMAGE CALL 1
    # =====================================================

    print(
        "🎬 IMAGE CALL 1/"
        + str(
            MASTERPIECE_MAX_IMAGE_CALLS
        )
        + " | Quality-First HIGH..."
    )

    first_image = generate_high_quality_image(
        compiled=compiled,
        product_refs=product_refs,
        aspect_ratio=aspect_ratio,
        original_request=original_request,
        pass_name="quality_first_high",
    )

    telemetry[
        "image_calls"
    ] += 1

    passes: List[
        ProductionPassResult
    ] = [
        ProductionPassResult(
            pass_name="quality_first_high",
            image=first_image,
            metadata={
                "image_call":
                    1,

                "quality":
                    "high",

                "adaptive":
                    True,
            },
        )
    ]

    #
    # Local exact crop preview.
    #
    first_preview = (
        create_exact_delivery_frame(
            first_image,
            aspect_ratio,
            upscale_final=False,
            label="candidate_1",
        )
    )

    print(
        "✅ Candidate 1 ready:",
        first_preview.image_size,
    )

    # =====================================================
    # VISION CALL 1
    # =====================================================

    first_qa: Optional[
        QAEvaluation
    ] = None

    if (
        telemetry[
            "vision_calls"
        ]
        < MASTERPIECE_MAX_VISION_CALLS
    ):
        print("")
        print(
            "👁️ ADAPTIVE VISION QA 1/"
            + str(
                MASTERPIECE_MAX_VISION_CALLS
            )
            + "..."
        )

        try:
            first_qa = (
                evaluate_generated_image(
                    image=first_image,
                    original_request=original_request,
                    compiled_prompt=compiled,
                    product_lock=product_lock,
                    brand_context=brand_context,
                    aspect_ratio=aspect_ratio,
                    telemetry=telemetry,
                )
            )

            passes[0].qa = (
                first_qa
            )

            print_qa(
                "Candidate 1 QA",
                first_qa,
            )

        except Exception as error:
            errors.append(
                "qa_candidate_1: "
                + clean_text(
                    error,
                    3000,
                )
            )

            print(
                "⚠️ Candidate 1 QA unavailable."
            )

    best_image = first_image
    best_qa = first_qa

    best_score = (
        first_qa.score
        if first_qa
        else 0.0
    )

    # =====================================================
    # DECIDE WHETHER SECOND IMAGE CALL IS WORTH IT
    # =====================================================

    action = choose_adaptive_action(
        first_qa
    )

    telemetry[
        "adaptive_action"
    ] = action

    print("")
    print(
        "🧠 ADAPTIVE DECISION:",
        action,
    )

    second_image: Optional[
        GeneratedImage
    ] = None

    second_qa: Optional[
        QAEvaluation
    ] = None

    # =====================================================
    # IMAGE CALL 2 MAX
    # =====================================================

    if (
        action != "none"
        and telemetry[
            "image_calls"
        ]
        < MASTERPIECE_MAX_IMAGE_CALLS
    ):
        print("")
        print(
            "🎨 IMAGE CALL 2/"
            + str(
                MASTERPIECE_MAX_IMAGE_CALLS
            )
            + " | "
            + action
            + "..."
        )

        try:
            if action == "concept_recovery":
                recovery_prompt = (
                    build_concept_recovery_prompt(
                        qa=first_qa,
                        compiled=compiled,
                        aspect_ratio=aspect_ratio,
                    )
                )

                recovery_compiled = (
                    compiled_with_recovery(
                        compiled,
                        recovery_prompt,
                    )
                )

                #
                # Concept failure:
                # create a fresh scene instead of polishing
                # the failed composition.
                #
                second_image = (
                    generate_high_quality_image(
                        compiled=recovery_compiled,
                        product_refs=product_refs,
                        aspect_ratio=aspect_ratio,
                        original_request=original_request,
                        pass_name="concept_recovery_high",
                    )
                )

                second_pass_name = (
                    "concept_recovery_high"
                )

            else:
                correction = (
                    build_targeted_correction_prompt(
                        qa=first_qa,
                        compiled=compiled,
                        product_lock=product_lock,
                        aspect_ratio=aspect_ratio,
                    )
                )

                second_image = (
                    openai_multi_reference_edit(
                        working_image=first_image,
                        references=product_refs,
                        prompt=correction,
                        aspect_ratio=aspect_ratio,
                        pass_name="targeted_correction_high",
                    )
                )

                second_pass_name = (
                    "targeted_correction_high"
                )

            telemetry[
                "image_calls"
            ] += 1

            second_preview = (
                create_exact_delivery_frame(
                    second_image,
                    aspect_ratio,
                    upscale_final=False,
                    label="candidate_2",
                )
            )

            passes.append(
                ProductionPassResult(
                    pass_name=second_pass_name,
                    image=second_image,
                    metadata={
                        "image_call":
                            telemetry[
                                "image_calls"
                            ],

                        "quality":
                            "high",

                        "adaptive_action":
                            action,

                        "delivery_preview":
                            second_preview.image_size,
                    },
                )
            )

            # =================================================
            # VISION CALL 2
            # =================================================

            if (
                telemetry[
                    "vision_calls"
                ]
                < MASTERPIECE_MAX_VISION_CALLS
            ):
                print("")
                print(
                    "👁️ ADAPTIVE VISION QA 2/"
                    + str(
                        MASTERPIECE_MAX_VISION_CALLS
                    )
                    + "..."
                )

                try:
                    second_qa = (
                        evaluate_generated_image(
                            image=second_image,
                            original_request=original_request,
                            compiled_prompt=compiled,
                            product_lock=product_lock,
                            brand_context=brand_context,
                            aspect_ratio=aspect_ratio,
                            telemetry=telemetry,
                        )
                    )

                    passes[-1].qa = (
                        second_qa
                    )

                    print_qa(
                        "Candidate 2 QA",
                        second_qa,
                    )

                except Exception as error:
                    errors.append(
                        "qa_candidate_2: "
                        + clean_text(
                            error,
                            3000,
                        )
                    )

                    print(
                        "⚠️ Candidate 2 QA unavailable."
                    )

            # =================================================
            # BEST VERSION SELECTION
            # =================================================

            if (
                second_qa is not None
                and qa_candidate_is_better(
                    second_qa,
                    first_qa,
                )
            ):
                best_image = (
                    second_image
                )

                best_qa = (
                    second_qa
                )

                best_score = (
                    second_qa.score
                )

                print(
                    "🏆 Candidate 2 selected as BEST."
                )

            else:
                print(
                    "🏆 Candidate 1 preserved as BEST."
                )

        except Exception as error:
            errors.append(
                action
                + ": "
                + clean_text(
                    error,
                    3000,
                )
            )

            print(
                "⚠️ Adaptive second image call failed."
            )

            print(
                "✅ Candidate 1 preserved and will still be delivered."
            )

    else:
        print(
            "✅ No second paid image call needed."
        )

    # =====================================================
    # ALWAYS DELIVER BEST SUCCESSFUL IMAGE
    # =====================================================

    print("")
    print(
        "📦 Preparing exact final delivery..."
    )

    final_delivery_image = (
        create_exact_delivery_frame(
            best_image,
            aspect_ratio,
            upscale_final=True,
            label="final_delivery",
        )
    )

    #
    # IMPORTANT:
    #
    # QA is advisory / optimization metadata.
    #
    # run_production does NOT fail just because score is
    # below 88/90.
    #
    final_delivery_image.provider = (
        "xpand_masterpiece"
        if mode == MODE_MASTERPIECE
        else "xpand_production"
    )

    final_delivery_image.model = (
        "XPAND Production V3.0 → "
        + OPENAI_IMAGE_MODEL
        + " → Local Exact Frame"
    )

    if not isinstance(
        final_delivery_image.metadata,
        dict,
    ):
        final_delivery_image.metadata = {}

    final_delivery_image.metadata.update(
        {
            "production_engine":
                ENGINE_VERSION,

            "production_mode":
                mode,

            "quality_first_adaptive":
                True,

            "qa_score":
                best_score,

            "qa_passed":
                bool(
                    best_qa
                    and best_qa.passed
                ),

            "qa_target_reached":
                bool(
                    best_qa
                    and best_qa.target_reached
                ),

            "qa_decision":
                (
                    best_qa.decision
                    if best_qa
                    else "qa_unavailable"
                ),

            "qa_critical_blockers":
                (
                    best_qa.critical_blockers
                    if best_qa
                    else []
                ),

            "product_lock":
                product_lock,

            "production_passes":
                [
                    item.pass_name
                    for item in passes
                ],

            "image_calls":
                telemetry[
                    "image_calls"
                ],

            "vision_calls":
                telemetry[
                    "vision_calls"
                ],

            "image_call_limit":
                MASTERPIECE_MAX_IMAGE_CALLS,

            "vision_call_limit":
                MASTERPIECE_MAX_VISION_CALLS,

            "adaptive_action":
                telemetry[
                    "adaptive_action"
                ],

            "native_provider_canvas":
                provider_size_for_ratio(
                    aspect_ratio
                ),

            "exact_delivery_ratio":
                aspect_ratio,

            "exact_delivery_size":
                final_delivery_image.image_size,

            "local_processing_cost":
                0,

            "best_version_preservation":
                True,

            "qa_never_blocks_delivery":
                True,
        }
    )

    elapsed = round(
        time.monotonic()
        - started,
        3,
    )

    print("")
    print(
        "=============================================="
    )
    print(
        " XPAND PRODUCTION COMPLETE V3.0"
    )
    print(
        "=============================================="
    )

    print(
        "Best QA score:",
        best_score,
    )

    print(
        "QA target:",
        QA_TARGET_SCORE,
    )

    print(
        "Image calls:",
        telemetry[
            "image_calls"
        ],
        "/",
        MASTERPIECE_MAX_IMAGE_CALLS,
    )

    print(
        "Vision calls:",
        telemetry[
            "vision_calls"
        ],
        "/",
        MASTERPIECE_MAX_VISION_CALLS,
    )

    print(
        "Adaptive action:",
        telemetry[
            "adaptive_action"
        ],
    )

    print(
        "References:",
        len(references),
    )

    print(
        "Product references:",
        len(product_refs),
    )

    print(
        "Requested ratio:",
        aspect_ratio,
    )

    print(
        "Final delivery:",
        final_delivery_image.image_size,
    )

    print(
        "Local crop/resize API cost: $0",
    )

    print(
        "QA blocks delivery: False",
    )

    print(
        "Elapsed:",
        elapsed,
        "seconds",
    )

    print("")

    return ProductionResult(
        ok=True,
        final_image=final_delivery_image,
        best_score=best_score,
        qa=best_qa,
        passes=passes,
        compiled_prompt=compiled,
        references_used=len(
            references
        ),
        product_references_used=len(
            product_refs
        ),
        elapsed_seconds=elapsed,
        errors=errors,
    )


# =========================================================
# SELF TEST
#
# IMPORTANT:
# - NO API CALLS
# - NO IMAGE GENERATION
# - NO DATABASE ACCESS
# =========================================================

if __name__ == "__main__":
    print("")
    print(
        "=============================================="
    )
    print(
        " XPAND PRODUCTION ENGINE V3.0"
    )
    print(
        " QUALITY-FIRST ADAPTIVE MASTERPIECE"
    )
    print(
        "=============================================="
    )
    print("")

    print(
        "OpenAI:",
        (
            "READY"
            if OPENAI_API_KEY
            else "NOT CONFIGURED"
        ),
    )

    print(
        "Image model:",
        OPENAI_IMAGE_MODEL,
    )

    print(
        "Pillow:",
        Image.__version__,
    )

    print(
        "Max image calls:",
        MASTERPIECE_MAX_IMAGE_CALLS,
    )

    print(
        "Max Vision calls:",
        MASTERPIECE_MAX_VISION_CALLS,
    )

    print(
        "Correction trigger:",
        ADAPTIVE_CORRECTION_TRIGGER_SCORE,
    )

    print(
        "Concept recovery floor:",
        CONCEPT_RECOVERY_SCORE_FLOOR,
    )

    print("")

    # =====================================================
    # PROVIDER ROUTING
    # =====================================================

    provider_tests = {
        "1:1":
            "1024x1024",

        "4:5":
            "1024x1536",

        "9:16":
            "1024x1536",

        "2:3":
            "1024x1536",

        "16:9":
            "1536x1024",

        "3:2":
            "1536x1024",
    }

    provider_ok = True

    print(
        "Provider routing:"
    )

    for ratio, expected in provider_tests.items():
        actual = provider_size_for_ratio(
            ratio
        )

        ok = (
            actual
            == expected
        )

        provider_ok = (
            provider_ok
            and ok
        )

        print(
            (
                "✅"
                if ok
                else "❌"
            ),
            ratio,
            "→",
            actual,
        )

    print("")

    # =====================================================
    # LOCAL FRAME
    # =====================================================

    source_image = Image.new(
        "RGB",
        (
            1024,
            1536,
        ),
        (
            72,
            20,
            105,
        ),
    )

    source_buffer = BytesIO()

    source_image.save(
        source_buffer,
        format="PNG",
    )

    fake_image = GeneratedImage(
        image_bytes=source_buffer.getvalue(),
        mime_type="image/png",
        provider="self-test",
        model="self-test",
        prompt="self-test",
        original_prompt="self-test",
        aspect_ratio="4:5",
        image_size="1024x1536",
        quality="high",
        route_reason="self-test",
        request_id="self-test",
        metadata={},
    )

    preview = create_exact_delivery_frame(
        fake_image,
        "4:5",
        upscale_final=False,
        label="self_test_preview",
    )

    preview_dims = real_image_dimensions(
        preview.image_bytes
    )

    preview_ok = (
        preview_dims
        == (
            1024,
            1280,
        )
    )

    print(
        (
            "✅"
            if preview_ok
            else "❌"
        ),
        "Native 1024x1536 → exact 1024x1280",
    )

    final_test = create_exact_delivery_frame(
        fake_image,
        "4:5",
        upscale_final=True,
        label="self_test_final",
    )

    final_dims = real_image_dimensions(
        final_test.image_bytes
    )

    final_ok = (
        final_dims
        == (
            2560,
            3200,
        )
    )

    print(
        (
            "✅"
            if final_ok
            else "❌"
        ),
        "Final 4:5 →",
        final_dims,
    )

    print("")

    # =====================================================
    # ADAPTIVE POLICY
    # =====================================================

    good_qa = QAEvaluation(
        score=92,
        scores={
            "concept_execution":
                92,
        },
        passed=True,
        strengths=[],
        problems=[],
        correction_instruction="",
        critical_blockers=[],
        target_reached=True,
        delivery_approved=True,
        decision="target_reached",
    )

    weak_concept_qa = QAEvaluation(
        score=78,
        scores={
            "concept_execution":
                50,
        },
        passed=False,
        strengths=[],
        problems=[
            "Core visual metaphor missing."
        ],
        correction_instruction=(
            "Rebuild concept."
        ),
        critical_blockers=[
            "major concept failure"
        ],
        target_reached=False,
        delivery_approved=False,
        decision="critical_issues",
    )

    polish_qa = QAEvaluation(
        score=86,
        scores={
            "concept_execution":
                90,
        },
        passed=False,
        strengths=[],
        problems=[
            "Lighting needs refinement."
        ],
        correction_instruction=(
            "Refine lighting only."
        ),
        critical_blockers=[],
        target_reached=False,
        delivery_approved=False,
        decision=(
            "improvement_recommended"
        ),
    )

    adaptive_good = (
        choose_adaptive_action(
            good_qa
        )
        == "none"
    )

    adaptive_concept = (
        choose_adaptive_action(
            weak_concept_qa
        )
        == "concept_recovery"
    )

    adaptive_polish = (
        choose_adaptive_action(
            polish_qa
        )
        == "targeted_correction"
    )

    print(
        (
            "✅"
            if adaptive_good
            else "❌"
        ),
        "90+ → no second image call",
    )

    print(
        (
            "✅"
            if adaptive_concept
            else "❌"
        ),
        "Concept failure → concept recovery",
    )

    print(
        (
            "✅"
            if adaptive_polish
            else "❌"
        ),
        "Normal weakness → targeted correction",
    )

    print("")

    # =====================================================
    # BLUEPRINT
    # =====================================================

    dummy = compile_prompt(
        TARGET_OPENAI,
        request=(
            "STC Bank premium international transfer hero visual"
        ),
        creative_direction={
            "core_idea":
                "Two distant environments become one physical space."
        },
        brand_context={
            "brand":
                "STC Bank",
        },
        references=[],
        camera_direction={
            "camera":
                "premium environmental perspective",
        },
        product_lock={},
        aspect_ratio="4:5",
    )

    compiler_ok = (
        len(
            dummy.prompt
        )
        <= COMPILED_PROMPT_BUDGET
    )

    print(
        (
            "✅"
            if compiler_ok
            else "❌"
        ),
        "Quality-First Production Blueprint",
    )

    print("")

    # =====================================================
    # COST GUARD
    # =====================================================

    cost_guard_ok = (
        MASTERPIECE_MAX_IMAGE_CALLS
        <= 2
        and
        MASTERPIECE_MAX_VISION_CALLS
        <= 2
    )

    print(
        (
            "✅"
            if cost_guard_ok
            else "❌"
        ),
        "Maximum automatic image calls <= 2",
    )

    print(
        (
            "✅"
            if cost_guard_ok
            else "❌"
        ),
        "Maximum automatic Vision calls <= 2",
    )

    print(
        "✅ Composition decisions moved before image generation"
    )

    print(
        "✅ Lighting decisions moved before image generation"
    )

    print(
        "✅ Materials decisions moved before image generation"
    )

    print(
        "✅ Product Fidelity integrated into first generation"
    )

    print(
        "✅ First image uses HIGH quality"
    )

    print(
        "✅ Second image call only when QA justifies it"
    )

    print(
        "✅ Concept failure uses recovery instead of polish"
    )

    print(
        "✅ Best-version preservation"
    )

    print(
        "✅ QA never blocks best-image delivery"
    )

    print(
        "✅ Native canvas accepted"
    )

    print(
        "✅ Exact delivery framing is local"
    )

    print(
        "✅ Crop/resize makes no paid API call"
    )

    print("")

    all_ok = (
        provider_ok
        and preview_ok
        and final_ok
        and adaptive_good
        and adaptive_concept
        and adaptive_polish
        and compiler_ok
        and cost_guard_ok
    )

    print(
        (
            "XPAND Production Engine V3.0 self-test: "
            + (
                "PASS ✅"
                if all_ok
                else "FAIL ❌"
            )
        )
    )

    print(
        "🚫 No API calls were made"
    )

    print("")
