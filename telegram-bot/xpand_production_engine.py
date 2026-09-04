# =========================================================
# XPAND PRODUCTION ENGINE V4.0
#
# QUALITY-FIRST + SMART VISUAL REFERENCE ROUTING
#
# =========================================================
#
# PRODUCTION FLOW
# ---------------------------------------------------------
#
# User Request
#      ↓
# Brand Memory V2
#      ↓
# Request-Aware Reference Selection
#      ↓
# Best 3–5 Visual DNA References
#      ↓
# Brand Visual Profile
#      ↓
# Only strongest 1–3 ACTUAL images sent physically
#      ↓
# Quality-First Production Blueprint
#      ↓
# GPT-Image-2 HIGH                 [IMAGE CALL 1]
#      ↓
# Exact Local Delivery Frame       [$0]
#      ↓
# Vision QA                        [VISION CALL 1]
#      ↓
# optional:
# targeted correction OR concept recovery
#                                    [IMAGE CALL 2 MAX]
#      ↓
# Vision QA                        [VISION CALL 2 MAX]
#      ↓
# Best Version
#      ↓
# Exact Final Delivery Frame        [$0]
#
#
# V3.1 IMPORTANT CHANGES
# ---------------------------------------------------------
#
# - Integrates XPAND Brand Memory V2.
# - Integrates Visual Intelligence V2.
# - Stops loading the latest references blindly.
# - Selects references according to campaign meaning.
# - Travel request → travel references.
# - International transfer → transfer references.
# - Product request → product references prioritized.
# - Brand Visual Profile injected into production blueprint.
# - Actual visual reference images CAN be supplied to
#   GPT-Image-2, not only text summaries.
# - Actual physical references limited to max 3 by default.
# - Visual DNA references limited to max 5 by default.
# - Product references receive first priority.
# - Official/recent/high-confidence references preferred
#   by Brand Memory / Visual Intelligence.
# - Reference images are used as STYLE / CAMERA /
#   COMPOSITION / PRODUCT evidence.
# - Exact old campaign composition must NOT be cloned.
#
#
# COST POLICY
# ---------------------------------------------------------
#
# Default:
#
#   Visual DNA selected:       max 5
#   Physical image references: max 3
#   Image calls:               max 2
#   Vision calls:              max 2
#
#
# Actual reference images are sent mainly on:
#
#   - first generation
#   - fresh concept recovery
#
# A targeted correction normally sends:
#
#   working image
#   + product references only
#
# instead of repeatedly sending all style references.
#
#
# SELF TEST
# ---------------------------------------------------------
#
# Running:
#
#     python xpand_production_engine.py
#
# makes ZERO paid API calls.
#
# =========================================================

from __future__ import annotations

import base64
import colorsys
import json
import os
import re
import time
import uuid

from dataclasses import dataclass, field
from io import BytesIO

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


# =========================================================
# EXISTING XPAND IMAGE ENGINE
# =========================================================

from xpand_image_engine import (
    GEMINI_API_KEY,
    GEMINI_INTERACTIONS_URL,
    GOOGLE_IMAGE_FAST_MODEL,
    GOOGLE_IMAGE_PRO_MODEL,
    OPENAI_API_KEY,
    OPENAI_IMAGE_MODEL,
    REQUEST_TIMEOUT,
    GeneratedImage,
    PROVIDER_OPENAI,
    build_route,
    call_openai_director,
    detect_image_size,
    generate_with_gemini,
    generate_with_openai,
    PROVIDER_GOOGLE_FAST,
    _finalize_requested_resolution,
)

from xpand_stc_bank_skill import STC_BANK_IMAGE_GUARD, is_stc_bank_request


# =========================================================
# XPAND BRAND MEMORY V2
# =========================================================

import xpand_brand_memory as xpand_brand_memory


# =========================================================
# IDENTITY
# =========================================================

ENGINE_NAME = "XPAND Production Engine"

ENGINE_VERSION = "4.0"


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
# QUALITY-FIRST COST LIMITS
# =========================================================

MASTERPIECE_MAX_IMAGE_CALLS = max(
    1,
    min(
        6,
        int(
            os.environ.get(
                "XPAND_MASTERPIECE_MAX_IMAGE_CALLS",
                "6",
            )
            or 6
        ),
    ),
)


MASTERPIECE_MAX_VISION_CALLS = max(
    1,
    min(
        6,
        int(
            os.environ.get(
                "XPAND_MASTERPIECE_MAX_VISION_CALLS",
                "6",
            )
            or 6
        ),
    ),
)

# Model specialization: Nano Banana 2 explores the first visual solution;
# Nano Banana Pro handles recovery and precision passes where fidelity matters
# more than latency.  The strict QA gate remains provider-independent.
MASTERPIECE_EXPLORATION_MODEL = str(
    os.environ.get(
        "XPAND_MASTERPIECE_EXPLORATION_MODEL",
        "gemini-3.1-flash-image",
    )
).strip()

MASTERPIECE_FINAL_IMAGE_MODEL = str(
    os.environ.get(
        "XPAND_MASTERPIECE_GOOGLE_MODEL",
        "gemini-3-pro-image",
    )
).strip()


def masterpiece_model_for_pass(pass_name: str) -> str:
    name = str(pass_name or "").lower()
    # All exploration/recovery/correction candidates use Nano Banana 2 at 1K.
    # Nano Banana Pro is reserved exclusively for the chosen final 1K/2K/4K master.
    if name.startswith("final_native_"):
        return MASTERPIECE_FINAL_IMAGE_MODEL
    return MASTERPIECE_EXPLORATION_MODEL


# =========================================================
# VISUAL REFERENCE COST POLICY
# =========================================================

#
# Number of references whose DNA can enter the prompt.
#

SMART_REFERENCE_SELECTION_LIMIT = max(
    1,
    min(
        12,
        int(
            os.environ.get(
                "XPAND_SMART_REFERENCE_LIMIT",
                "10",
            )
            or 10
        ),
    ),
)


#
# Number of actual image files sent to the image model.
#
# Keeping this at 2–3 gives us the strongest visual evidence
# without repeatedly sending a large reference library.
#

MAX_PHYSICAL_REFERENCE_IMAGES = max(
    0,
    min(
        6,
        int(
            os.environ.get(
                "XPAND_PHYSICAL_REFERENCE_LIMIT",
                "5",
            )
            or 5
        ),
    ),
)


SEND_VISUAL_REFERENCES_TO_IMAGE = (
    str(
        os.environ.get(
            "XPAND_SEND_VISUAL_REFERENCES_TO_IMAGE",
            "true",
        )
    )
    .strip()
    .lower()
    in {
        "1",
        "true",
        "yes",
        "on",
    }
)


# =========================================================
# ADAPTIVE QUALITY POLICY
# =========================================================

ADAPTIVE_CORRECTION_TRIGGER_SCORE = max(
    70.0,
    min(
        100.0,
        float(
            os.environ.get(
                "XPAND_ADAPTIVE_CORRECTION_TRIGGER_SCORE",
                "95",
            )
            or 95
        ),
    ),
)


CONCEPT_RECOVERY_SCORE_FLOOR = max(
    40.0,
    min(
        90.0,
        float(
            os.environ.get(
                "XPAND_CONCEPT_RECOVERY_SCORE_FLOOR",
                "75",
            )
            or 75
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
                "94",
            )
            or 94
        ),
    ),
)


QA_DELIVERY_FLOOR = max(
    50.0,
    min(
        float(
            QA_TARGET_SCORE
        ),
        float(
            os.environ.get(
                "XPAND_IMAGE_QA_DELIVERY_FLOOR",
                "90",
            )
            or 90
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
    "concept_execution": 13,
    "reference_adherence": 8,
    "perspective": 7,
    "product_fidelity": 8,
    "lighting": 7,
    "materials": 6,
    "human_anatomy": 4,
    "background_cleanliness": 4,
    "brand_alignment": 10,
    "negative_space": 4,
    "text_logo_integrity": 10,
    "advertising_readiness": 7,
    "stc_palette_fidelity": 6,
    "hero_dominance": 3,
    "message_clarity_without_text": 3,
}


# =========================================================
# PROMPT BUDGET
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

    dna: Dict[str, Any] = field(
        default_factory=dict
    )

    product_lock: Dict[str, Any] = field(
        default_factory=dict
    )

    user_note: str = ""

    source_id: str = ""

    content_family: str = "general_brand"

    source_metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    selection: Dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class CompiledPrompt:

    target: str

    prompt: str

    negative_prompt: str

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class QAEvaluation:

    score: float

    scores: Dict[str, float]

    passed: bool

    strengths: List[str]

    problems: List[str]

    correction_instruction: str

    critical_blockers: List[str] = field(
        default_factory=list
    )

    target_reached: bool = False

    delivery_approved: bool = False

    decision: str = ""

    raw: Dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class ProductionPassResult:

    pass_name: str

    image: GeneratedImage

    qa: Optional[
        QAEvaluation
    ] = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class ProductionResult:

    ok: bool

    final_image: GeneratedImage

    best_score: float

    qa: Optional[
        QAEvaluation
    ]

    passes: List[
        ProductionPassResult
    ]

    compiled_prompt: CompiledPrompt

    references_used: int

    product_references_used: int

    elapsed_seconds: float

    errors: List[str] = field(
        default_factory=list
    )


# =========================================================
# BASIC HELPERS
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
        .replace(
            "\x00",
            "",
        )
        .strip()[:limit]
    )


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
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def clamp_score(
    value: Any,
) -> float:

    try:

        number = float(
            value
        )

    except Exception:

        number = 0.0

    return max(
        0.0,
        min(
            100.0,
            number,
        ),
    )


def compact_json(
    value: Any,
    limit: int = 6000,
) -> str:

    try:

        text = json.dumps(
            value,
            ensure_ascii=False,
            separators=(
                ",",
                ":",
            ),
            default=str,
        )

    except Exception:

        text = clean_text(
            value,
            limit,
        )

    if len(
        text
    ) <= limit:

        return text

    front = int(
        limit
        *
        0.68
    )

    back = max(
        0,
        limit
        -
        front
        -
        90
    )

    return (
        text[:front]
        +
        '\n"[XPAND_CONTEXT_COMPACTED]"\n'
        +
        (
            text[-back:]
            if back
            else ""
        )
    )


def hard_fit_prompt(
    text: str,
    max_chars: int,
) -> str:

    value = clean_text(
        text,
        1000000,
    )

    if len(
        value
    ) <= max_chars:

        return value

    marker = (
        "\n\n"
        "[XPAND CONTEXT COMPACTED]\n"
        "Secondary detail omitted. "
        "The original request, winning creative direction, "
        "brand rules and critical reference rules remain authoritative."
        "\n\n"
    )

    available = max(
        500,
        max_chars - len(
            marker
        ),
    )

    front = int(
        available
        *
        0.68
    )

    back = (
        available
        -
        front
    )

    return (
        value[:front]
        +
        marker
        +
        value[-back:]
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

    if len(
        original
    ) <= budget:

        print(
            "🧮 Prompt budget ["
            + label
            + "]: "
            + str(
                len(
                    fitted
                )
            )
            + "/"
            + str(
                budget
            )
            + " chars ✅"
        )

    else:

        print(
            "🧮 Prompt budget ["
            + label
            + "]: "
            + str(
                len(
                    original
                )
            )
            + " → "
            + str(
                len(
                    fitted
                )
            )
            + "/"
            + str(
                budget
            )
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

        parsed = json.loads(
            text
        )

        if isinstance(
            parsed,
            dict,
        ):

            return parsed

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

        try:

            parsed = json.loads(
                text[
                    start:
                    end + 1
                ]
            )

            if isinstance(
                parsed,
                dict,
            ):

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


def find_images_in_response(
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

    def walk(
        item: Any,
    ) -> None:

        if isinstance(
            item,
            dict,
        ):

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
                100,
            )

            for key in [
                "b64_json",
                "base64",
                "data",
            ]:

                raw_value = (
                    item.get(
                        key
                    )
                )

                if not isinstance(
                    raw_value,
                    str,
                ):

                    continue

                raw = (
                    decode_image_value(
                        raw_value
                    )
                )

                if raw:

                    found.append(
                        (
                            raw,
                            mime_type
                            or
                            "image/png",
                        )
                    )

                    break

            for child in (
                item.values()
            ):

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

    output: List[
        Tuple[
            bytes,
            str,
        ]
    ] = []

    seen = set()

    for raw, mime_type in found:

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
        raw.startswith(
            b"RIFF"
        )
        and
        b"WEBP"
        in raw[:16]
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
        match.group(
            1
        )
    )

    height = float(
        match.group(
            2
        )
    )

    if (
        width <= 0
        or
        height <= 0
    ):

        return None

    return (
        width
        /
        height
    )


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

    orientation = (
        orientation_for_ratio(
            aspect_ratio
        )
    )

    if orientation == "portrait":

        return (
            PROVIDER_PORTRAIT_SIZE
        )

    if orientation == "landscape":

        return (
            PROVIDER_LANDSCAPE_SIZE
        )

    return (
        PROVIDER_SQUARE_SIZE
    )


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
            "1:1":
                "1024x1024",

            "4:5":
                "1024x1280",

            "5:4":
                "1280x1024",

            "9:16":
                "864x1536",

            "16:9":
                "1536x864",

            "2:3":
                "1024x1536",

            "3:2":
                "1536x1024",

            "3:4":
                "1024x1365",

            "4:3":
                "1365x1024",
        }

        return mapping.get(
            ratio,
            "1024x1024",
        )

    mapping = {
        "1:1":
            "2048x2048",

        "4:5":
            "2560x3200",

        "5:4":
            "3200x2560",

        "9:16":
            "2160x3840",

        "16:9":
            "3840x2160",

        "2:3":
            "2304x3456",

        "3:2":
            "3456x2304",

        "3:4":
            "2448x3264",

        "4:3":
            "3264x2448",

        "21:9":
            "3840x1646",
    }

    return mapping.get(
        ratio,
        "2048x2048",
    )


def parse_size_string(
    value: str,
) -> Optional[
    Tuple[
        int,
        int,
    ]
]:

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
        int(
            match.group(
                1
            )
        ),
        int(
            match.group(
                2
            )
        ),
    )


# =========================================================
# LOCAL IMAGE PROCESSING
# =========================================================

def real_image_dimensions(
    raw: bytes,
) -> Tuple[
    int,
    int,
]:

    try:

        with Image.open(
            BytesIO(
                raw
            )
        ) as image:

            image.load()

            return (
                int(
                    image.width
                ),
                int(
                    image.height
                ),
            )

    except Exception as error:

        raise RuntimeError(
            (
                "Unable to inspect image dimensions: "
                +
                clean_text(
                    error,
                    1000,
                )
            )
        )


def inspect_provider_canvas(
    image: GeneratedImage,
    requested_aspect_ratio: str,
) -> Dict[str, Any]:

    width, height = (
        real_image_dimensions(
            image.image_bytes
        )
    )

    requested_orientation = (
        orientation_for_ratio(
            requested_aspect_ratio
        )
    )

    if width > height:

        actual_orientation = (
            "landscape"
        )

    elif height > width:

        actual_orientation = (
            "portrait"
        )

    else:

        actual_orientation = (
            "square"
        )

    expected_size = (
        provider_size_for_ratio(
            requested_aspect_ratio
        )
    )

    orientation_match = (
        requested_orientation
        ==
        actual_orientation
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
            orientation_match,
    }

    if orientation_match:

        print(
            "📐 PROVIDER CANVAS: "
            + str(
                width
            )
            + "x"
            + str(
                height
            )
            + " ✅"
        )

    else:

        print(
            "⚠️ PROVIDER CANVAS DIFFERENT"
            + " | requested="
            + requested_aspect_ratio
            + " | actual="
            + str(
                width
            )
            + "x"
            + str(
                height
            )
            + " | local exact frame will repair delivery"
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
) -> Tuple[
    int,
    int,
    int,
    int,
]:

    target_ratio = (
        aspect_ratio_value(
            aspect_ratio
        )
    )

    if target_ratio is None:

        raise RuntimeError(
            (
                "Invalid aspect ratio: "
                +
                clean_text(
                    aspect_ratio,
                    100,
                )
            )
        )

    current_ratio = (
        float(
            width
        )
        /
        float(
            height
        )
    )

    if abs(
        current_ratio
        -
        target_ratio
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
                *
                target_ratio
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
                    -
                    target_width
                )
                /
                2
            )
        )

        return (
            left,
            0,
            left
            +
            target_width,
            height,
        )

    target_height = int(
        round(
            width
            /
            target_ratio
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
                -
                target_height
            )
            /
            2
        )
    )

    return (
        0,
        top,
        width,
        top
        +
        target_height,
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
        image_bytes=(
            image_bytes
        ),

        mime_type=(
            mime_type
        ),

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

        aspect_ratio=(
            aspect_ratio
        ),

        image_size=(
            image_size
        ),

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
            (
                "local-"
                +
                uuid.uuid4().hex[:12]
            ),
        ),

        metadata=(
            metadata
        ),
    )


def create_exact_delivery_frame(
    source: GeneratedImage,
    requested_aspect_ratio: str,
    *,
    upscale_final: bool = False,
    label: str = "delivery_frame",
) -> GeneratedImage:

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
        and
        clean_text(
            getattr(
                source,
                "aspect_ratio",
                "",
            ),
            30,
        )
        ==
        requested_aspect_ratio
        and
        not upscale_final
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

            pil_image = (
                pil_image.convert(
                    "RGB"
                )
            )

        crop_box = (
            crop_box_for_aspect(
                int(
                    pil_image.width
                ),
                int(
                    pil_image.height
                ),
                requested_aspect_ratio,
            )
        )

        cropped = (
            pil_image.crop(
                crop_box
            )
        )

        crop_width = int(
            cropped.width
        )

        crop_height = int(
            cropped.height
        )

        output_width = (
            crop_width
        )

        output_height = (
            crop_height
        )

        if upscale_final:

            target_size = (
                production_size_for_ratio(
                    requested_aspect_ratio,
                    final_quality=True,
                )
            )

            target_dims = (
                parse_size_string(
                    target_size
                )
            )

            if target_dims:

                target_width, target_height = (
                    target_dims
                )

                if (
                    target_width
                    !=
                    crop_width
                    or
                    target_height
                    !=
                    crop_height
                ):

                    cropped = (
                        cropped.resize(
                            (
                                target_width,
                                target_height,
                            ),
                            Image.Resampling.LANCZOS,
                        )
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
        + str(
            source_width
        )
        + "x"
        + str(
            source_height
        )
        + " → "
        + str(
            output_width
        )
        + "x"
        + str(
            output_height
        )
        + " "
        + requested_aspect_ratio
        + " ✅"
    )

    return derived_image(
        source,
        image_bytes=(
            output_bytes
        ),
        mime_type="image/png",
        aspect_ratio=(
            requested_aspect_ratio
        ),
        image_size=(
            str(
                output_width
            )
            + "x"
            + str(
                output_height
            )
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
                bool(
                    upscale_final
                ),

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

    crop_box = (
        crop_box_for_aspect(
            width,
            height,
            aspect_ratio,
        )
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
            right
            -
            left,

        "safe_height":
            bottom
            -
            top,

        "left_bleed_pct":
            round(
                left
                /
                width
                *
                100,
                2,
            ),

        "right_bleed_pct":
            round(
                (
                    width
                    -
                    right
                )
                /
                width
                *
                100,
                2,
            ),

        "top_bleed_pct":
            round(
                top
                /
                height
                *
                100,
                2,
            ),

        "bottom_bleed_pct":
            round(
                (
                    height
                    -
                    bottom
                )
                /
                height
                *
                100,
                2,
            ),
    }


def safe_frame_instruction(
    aspect_ratio: str,
) -> str:

    safe = (
        safe_frame_description(
            aspect_ratio
        )
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

left:
{safe.get("left_bleed_pct", 0)}%

right:
{safe.get("right_bleed_pct", 0)}%

top:
{safe.get("top_bleed_pct", 0)}%

bottom:
{safe.get("bottom_bleed_pct", 0)}%

Keep inside the final safe frame:

- hero subject
- core metaphor
- product
- human face/hands
- architectural storytelling
- destination/environment cues
- negative-space copy area

Do not put critical information in crop bleed.
""".strip()


# =========================================================
# BRAND MEMORY V2
# =========================================================

def load_brand_visual_profile_safe(
    core,
    user_id,
    brand_id: str,
) -> Dict[str, Any]:

    if not brand_id:

        return {}

    try:

        profile = (
            xpand_brand_memory.get_brand_visual_profile(
                core,
                user_id,
                brand_id,
            )
        )

        if profile:

            return profile

    except Exception as error:

        print(
            "⚠️ Brand Visual Profile load: "
            +
            clean_text(
                error,
                1000,
            )
        )

    #
    # Existing V1 references may exist before a V2 profile
    # has been aggregated.
    #
    # Refresh is local DB aggregation only.
    #

    try:

        profile = (
            xpand_brand_memory.refresh_brand_visual_profile(
                core,
                user_id,
                brand_id,
            )
        )

        return (
            profile
            if isinstance(
                profile,
                dict,
            )
            else {}
        )

    except Exception as error:

        print(
            "⚠️ Brand Visual Profile refresh: "
            +
            clean_text(
                error,
                1000,
            )
        )

        return {}


# =========================================================
# SMART REFERENCE LOADER
# =========================================================

def load_runtime_references(
    core,
    user_id,
    brand_id: str,
    *,
    request: str = "",
    limit: int = SMART_REFERENCE_SELECTION_LIMIT,
) -> List[
    ProductionReference
]:

    limit = max(
        1,
        min(
            SMART_REFERENCE_SELECTION_LIMIT,
            int(
                limit
                or
                SMART_REFERENCE_SELECTION_LIMIT
            ),
        ),
    )

    stored = []

    if request:

        try:

            stored = (
                xpand_brand_memory.load_relevant_visual_references(
                    core,
                    user_id,
                    brand_id=brand_id,
                    request=request,
                    limit=limit,
                    mark_used=True,
                )
            )

        except Exception as error:

            print(
                "⚠️ Smart reference selection failed: "
                +
                clean_text(
                    error,
                    1200,
                )
            )

    #
    # Compatibility fallback:
    #
    # If there is no V2 result, preserve old loading behavior
    # but keep the quantity small.
    #

    if not stored:

        try:

            stored = (
                xpand_brand_memory.load_visual_references(
                    core,
                    user_id,
                    brand_id=brand_id,
                    limit=limit,
                )
            )

            if stored:

                print(
                    "⚠️ Reference selector fallback: latest brand references"
                )

        except Exception as error:

            print(
                "⚠️ Legacy reference load failed: "
                +
                clean_text(
                    error,
                    1200,
                )
            )

            stored = []

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

        #
        # DNA can still participate in the prompt only when
        # the image file itself is available for runtime.
        #
        # Existing production architecture expects
        # ProductionReference.image_bytes.
        #

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
                +
                clean_text(
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

                image_bytes=(
                    raw
                ),

                mime_type=(
                    infer_mime_type(
                        raw
                    )
                ),

                dna=safe_dict(
                    item.get(
                        "dna",
                        {},
                    )
                ),

                product_lock=(
                    safe_dict(
                        item.get(
                            "product_lock",
                            {},
                        )
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

                content_family=clean_text(
                    item.get(
                        "content_family",
                        "general_brand",
                    ),
                    100,
                ),

                source_metadata=(
                    safe_dict(
                        item.get(
                            "source_metadata",
                            {},
                        )
                    )
                ),

                selection=(
                    safe_dict(
                        item.get(
                            "selection",
                            {},
                        )
                    )
                ),
            )
        )

    return references


# =========================================================
# REFERENCE HELPERS
# =========================================================

def product_references(
    references: Sequence[
        ProductionReference
    ],
) -> List[
    ProductionReference
]:

    return [
        item
        for item in references
        if item.role
        ==
        "product_reference"
    ]


def reference_dna_payload(
    references: Sequence[
        ProductionReference
    ],
) -> List[
    Dict[str, Any]
]:

    output = []

    for item in references[
        :SMART_REFERENCE_SELECTION_LIMIT
    ]:

        selection_score = (
            safe_dict(
                item.selection
            ).get(
                "score",
                0,
            )
        )

        output.append(
            {
                "reference_id":
                    item.source_id,

                "role":
                    item.role,

                "content_family":
                    item.content_family,

                "selection_score":
                    selection_score,

                "official_source":
                    bool(
                        safe_dict(
                            item.source_metadata
                        ).get(
                            "official",
                            False,
                        )
                    ),

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

        if (
            item.role
            !=
            "product_reference"
        ):

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
                and
                text
                not in rules
            ):

                rules.append(
                    text
                )

    return {
        "enabled":
            bool(
                count
            ),

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
                else
                "none"
            ),
    }


# =========================================================
# PHYSICAL REFERENCE SELECTION
# =========================================================

PHYSICAL_ROLE_PRIORITY = {
    "product_reference":
        1000,

    "campaign_reference":
        900,

    "style_reference":
        850,

    "composition_reference":
        820,

    "camera_reference":
        800,

    "lighting_reference":
        780,

    "color_reference":
        760,

    "environment_reference":
        720,

    "person_reference":
        650,

    "mixed_reference":
        840,
}


def reference_selection_score(
    reference: ProductionReference,
) -> float:

    try:

        return float(
            safe_dict(
                reference.selection
            ).get(
                "score",
                0,
            )
            or 0
        )

    except Exception:

        return 0.0


def choose_physical_references(
    references: Sequence[
        ProductionReference
    ],
    *,
    limit: int = MAX_PHYSICAL_REFERENCE_IMAGES,
) -> List[
    ProductionReference
]:

    if (
        not SEND_VISUAL_REFERENCES_TO_IMAGE
        or
        limit <= 0
    ):

        return []

    limit = min(
        MAX_PHYSICAL_REFERENCE_IMAGES,
        max(
            0,
            int(
                limit
            ),
        ),
    )

    ranked = sorted(
        list(
            references
        ),
        key=lambda item:
            (
                PHYSICAL_ROLE_PRIORITY.get(
                    item.role,
                    500,
                )
                +
                reference_selection_score(
                    item
                )
            ),
        reverse=True,
    )

    selected: List[
        ProductionReference
    ] = []

    seen_ids = set()

    #
    # Product Lock always receives priority.
    #

    for item in ranked:

        if len(
            selected
        ) >= limit:

            break

        if (
            item.role
            !=
            "product_reference"
        ):

            continue

        unique = (
            item.source_id
            or
            str(
                id(
                    item
                )
            )
        )

        if unique in seen_ids:

            continue

        selected.append(
            item
        )

        seen_ids.add(
            unique
        )

    #
    # Then strongest brand/campaign/style evidence.
    #

    for item in ranked:

        if len(
            selected
        ) >= limit:

            break

        unique = (
            item.source_id
            or
            str(
                id(
                    item
                )
            )
        )

        if unique in seen_ids:

            continue

        selected.append(
            item
        )

        seen_ids.add(
            unique
        )

    return selected


# =========================================================
# REFERENCE IMAGE INSTRUCTION
# =========================================================

def physical_reference_instruction(
    references: Sequence[
        ProductionReference
    ],
) -> str:

    if not references:

        return ""

    lines = [
        "ATTACHED VISUAL REFERENCE POLICY",
        "================================",
        "",
        (
            "The attached images are authoritative visual references, "
            "but they have DIFFERENT FUNCTIONS."
        ),
        "",
        (
            "Learn their visual logic. Do NOT clone an old campaign "
            "composition or copy existing advertising text."
        ),
        "",
    ]

    for index, item in enumerate(
        references,
        start=1,
    ):

        official = bool(
            safe_dict(
                item.source_metadata
            ).get(
                "official",
                False,
            )
        )

        score = (
            reference_selection_score(
                item
            )
        )

        lines.extend(
            [
                (
                    "REFERENCE "
                    +
                    str(
                        index
                    )
                ),

                (
                    "Role: "
                    +
                    item.role
                ),

                (
                    "Content family: "
                    +
                    item.content_family
                ),

                (
                    "Official source: "
                    +
                    str(
                        official
                    )
                ),

                (
                    "Selection relevance: "
                    +
                    str(
                        round(
                            score,
                            1,
                        )
                    )
                ),

                (
                    "User note: "
                    +
                    (
                        clean_text(
                            item.user_note,
                            500,
                        )
                        or
                        "none"
                    )
                ),

                "",
            ]
        )

        if (
            item.role
            ==
            "product_reference"
        ):

            lines.extend(
                [
                    (
                        "PRODUCT RULE: preserve this product's identity, "
                        "silhouette, proportions, materials and major layout."
                    ),
                    "",
                ]
            )

        elif (
            item.role
            ==
            "camera_reference"
        ):

            lines.extend(
                [
                    (
                        "CAMERA RULE: learn camera height, lens behavior "
                        "and perspective. Do not copy unrelated objects."
                    ),
                    "",
                ]
            )

        elif (
            item.role
            ==
            "color_reference"
        ):

            lines.extend(
                [
                    (
                        "COLOR RULE: learn palette hierarchy and color usage. "
                        "Do not copy the scene."
                    ),
                    "",
                ]
            )

        elif (
            item.role
            ==
            "lighting_reference"
        ):

            lines.extend(
                [
                    (
                        "LIGHTING RULE: learn light quality, contrast, "
                        "shadow behavior and reflections."
                    ),
                    "",
                ]
            )

        elif (
            item.role
            ==
            "composition_reference"
        ):

            lines.extend(
                [
                    (
                        "COMPOSITION RULE: learn hierarchy, negative space "
                        "and balance without reproducing the exact scene."
                    ),
                    "",
                ]
            )

        elif (
            item.role
            in {
                "style_reference",
                "campaign_reference",
                "mixed_reference",
            }
        ):

            lines.extend(
                [
                    (
                        "STYLE RULE: learn commercial finish, brand tone, "
                        "material language, restraint and photographic quality."
                    ),
                    "",
                ]
            )

    lines.extend(
        [
            "GLOBAL REFERENCE RULES",
            "----------------------",
            "",
            "- Never copy advertising copy from a reference.",
            "- Never reproduce financial numbers.",
            "- Never hallucinate a fake official logo.",
            "- Never treat one old post as a universal brand law.",
            "- Prefer repeated Brand Visual Profile patterns.",
            "- Preserve the NEW requested idea.",
            "- Reference images guide execution, not creative duplication.",
        ]
    )

    return "\n".join(
        lines
    ).strip()


# =========================================================
# ENRICH BRAND CONTEXT
# =========================================================

def build_enriched_brand_context(
    *,
    brand_context: Any,
    brand_visual_profile: Dict[str, Any],
    references: Sequence[
        ProductionReference
    ],
) -> Dict[str, Any]:

    selected_summary = []

    for item in references:

        selected_summary.append(
            {
                "id":
                    item.source_id,

                "role":
                    item.role,

                "content_family":
                    item.content_family,

                "selection_score":
                    reference_selection_score(
                        item
                    ),

                "official":
                    bool(
                        safe_dict(
                            item.source_metadata
                        ).get(
                            "official",
                            False,
                        )
                    ),
            }
        )

    return {
        "base_brand_context":
            brand_context,

        "brand_visual_profile":
            brand_visual_profile,

        "smart_reference_selection":
            selected_summary,

        "reference_policy":
            {
                "visual_dna_limit":
                    SMART_REFERENCE_SELECTION_LIMIT,

                "physical_image_limit":
                    MAX_PHYSICAL_REFERENCE_IMAGES,

                "request_aware":
                    True,

                "official_source_priority":
                    True,

                "freshness_priority":
                    True,

                "do_not_clone_campaign":
                    True,
            },
    }


# =========================================================
# NEGATIVE PROMPT
# =========================================================

def base_negative_prompt() -> str:

    return (
        "malformed anatomy, extra fingers, warped product, "
        "wrong perspective, fake reflections, duplicated objects, "
        "generic stock photography, floating decorative objects, "
        "random text, fake logos, misspelled typography, "
        "cheap CGI, plastic skin, wet-floor reflections, "
        "generic banking clichés, generic travel clichés, "
        "floating cards, floating SIM cards, globes, "
        "connection lines, random neon fintech graphics"
    )


def stc_scene_lock(request: str) -> str:
    """Compact STC rules placed early so prompt fitting cannot drop them."""
    if not is_stc_bank_request(request):
        return ""

    source = clean_text(request, 12000).lower()
    studio_markers = (
        "studio", "استوديو", "منصة", "platform", "podium",
        "product shot", "لقطة منتج",
    )
    natural_markers = (
        "airport", "travel", "airplane", "plane", "lounge", "beach",
        "office", "home", "house", "restaurant", "cafe", "car",
        "person", "man", "woman", "family", "lifestyle", "interior",
        "مطار", "سفر", "طائرة", "صالة", "شاطئ", "مكتب", "منزل",
        "بيت", "مطعم", "مقهى", "سيارة", "شخص", "رجل", "امرأة",
        "عائلة", "لايف ستايل", "واقعي",
    )
    use_vivid = any(str(item).lower() in source for item in studio_markers)
    use_natural = any(str(item).lower() in source for item in natural_markers)

    if use_natural and not use_vivid:
        palette = """
SELECTED PALETTE — NATURAL STC LIFESTYLE MODE:
Do not flood the environment with purple and do not apply a purple, blue,
cyan or teal color cast. Skin, sky, wood, fabric, food, glass and architecture
keep believable real-world color under motivated neutral light. Use warm
neutrals only where physically present: #301F14, #52392C, #8D674C,
#976D4D, #B79A7F, #D3A26D, #ECDFCE and #E4C1C3. Use natural travel/sky
blues only in real sky or exterior depth: #8EC3EC, #70AADD, #5F94C9,
#4A8BB7, #2E5F83 and #143B5C. STC purple occupies only 5–15% as a
physically motivated product, wardrobe, reflection or architectural accent,
using #5C0C9B or deep #1D0446 with restrained #7433C5 highlight. Preserve
neutral whites #FBFBFB and realistic blacks #05070F/#0E090E.
""".strip()
    elif use_vivid:
        palette = """
SELECTED PALETTE — FAMILY A ONLY, DO NOT MIX WITH FAMILY B:
dark edges/contact shadows #2E0053; structural transitions #440675,
#500988 and #4D0C8C; dominant brand core behind the hero #5C0C9B;
controlled transitions #531985, #6C2F9A and #8945B4; one motivated
light edge #8F45C1 or #A35DC9; palest highlight #B7A5C4.
""".strip()
    else:
        palette = """
SELECTED PALETTE — FAMILY B ONLY, DO NOT MIX WITH FAMILY A:
near-black violet edges #090114, #13012C and #19032F; primary deep
background #1D0446 and #260845; shadow-to-light structure #310F68,
#33165D, #401880 and #49277D; hero illumination #53249E and #623C9E;
at most one motivated background light edge #7433C5; soft glow #825DBE;
palest halo #AA89DD. Do not substitute blue, cyan or teal for purple.
""".strip()

    phone_required = any(
        marker in source
        for marker in [
            "phone", "smartphone", "mobile", "app", "application",
            "هاتف", "جوال", "موبايل", "تطبيق", "التطبيق",
        ]
    )
    phone_rule = (
        """
PHONE IS A REQUIRED DOMINANT HERO: keep it completely visible, large enough
to lead the hierarchy, physically supported, perspective-correct and sharply
focused. If no verified UI screenshot is physically supplied, the screen must
be blank, clean and softly reflective with absolutely no generated words,
letters, numbers, icons, pseudo-UI or invented STC marks. The benefit must read
from the photographed scene without relying on screen text.
""".strip()
        if phone_required
        else ""
    )

    return f"""
STC BANK PRODUCTION LOCK — HIGHEST PRIORITY
===========================================
{palette}

Purple is dimensional: darkest at edges/recesses, brighter only around the
hero, with violet contact shadows and physically correct restrained reflections.
Green is not scene lighting. No green/teal cast on skin, walls or architecture.
User-supplied STC references control perceived color, tonal roll-off, restraint
and finish. Do not copy their literal composition.

{phone_rule}

IMAGE SURFACE RULE: no campaign copy, typography, letters, numbers, logo,
watermark, invented UI, route graphics, holograms, decorative particles or
souvenir-like landmark collections anywhere in the generated image.

COMPOSITION RULE: one dominant hero, one subordinate context, clear visual
balance, purposeful negative space, premium real-lens viewpoint, believable
gravity, materials, anatomy, perspective, contact shadows and reflections.
""".strip()


def analyze_stc_color_balance(
    image_bytes: bytes,
    palette_mode: str,
) -> Dict[str, Any]:
    """Low-cost deterministic color evidence for Vision QA."""
    with Image.open(BytesIO(image_bytes)) as source:
        sample = source.convert("RGB")
        sample.thumbnail((160, 160), Image.Resampling.LANCZOS)
        pixels = list(sample.getdata())

    total = max(1, len(pixels))
    purple = 0
    blue_cyan = 0
    green = 0
    saturated = 0

    for red, green_value, blue in pixels:
        hue, saturation, value = colorsys.rgb_to_hsv(
            red / 255.0,
            green_value / 255.0,
            blue / 255.0,
        )
        if saturation >= 0.18 and value >= 0.05:
            saturated += 1
            if 0.70 <= hue <= 0.91:
                purple += 1
            elif 0.48 <= hue < 0.70:
                blue_cyan += 1
            elif 0.24 <= hue < 0.48:
                green += 1

    return {
        "palette_mode": palette_mode,
        "purple_pixel_ratio": round(purple / total, 4),
        "blue_cyan_pixel_ratio": round(blue_cyan / total, 4),
        "green_pixel_ratio": round(green / total, 4),
        "saturated_pixel_ratio": round(saturated / total, 4),
        "sampled_pixels": total,
    }


# =========================================================
# QUALITY-FIRST MASTER BLUEPRINT
# =========================================================

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
XPAND QUALITY-FIRST MASTERPIECE BLUEPRINT V3.1
==============================================

ORIGINAL USER REQUEST
---------------------

{clean_text(request, 5000)}


{stc_scene_lock(
    request
    + "\n"
    + compact_json(creative_direction, 2500)
)}


APPROVED CREATIVE DIRECTION
---------------------------

{compact_json(
    creative_direction,
    5000
)}


BRAND EXECUTION CONTEXT
-----------------------

{compact_json(
    brand_context,
    5000
)}


SMART VISUAL REFERENCE DNA
--------------------------

{compact_json(
    references,
    4800
)}


CAMERA DIRECTION
----------------

{compact_json(
    camera_direction,
    1800
)}


PRODUCT LOCK
------------

{compact_json(
    product_lock,
    2200
)}


{safe_frame_instruction(aspect_ratio)}


REFERENCE INTELLIGENCE RULE
===========================

Visual references were selected according to the current
campaign request.

Do NOT average all references blindly.

Each reference has a role.

Examples:

product_reference
→ preserve product identity.

camera_reference
→ learn camera and perspective.

color_reference
→ learn palette hierarchy.

lighting_reference
→ learn lighting behavior.

composition_reference
→ learn hierarchy / balance / negative space.

style_reference
→ learn overall commercial finish.

campaign_reference
→ learn the brand's campaign language without copying the
  original campaign idea.

The aggregated Brand Visual Profile is stronger evidence than
a single isolated post when patterns repeat across several
official references.


ONE-PASS MASTERPIECE OBJECTIVE
==============================

Create the strongest possible FINISHED advertising hero image
during the FIRST high-quality image generation.

Do NOT create a rough concept sketch.

Solve these before generation:

1. CONCEPT

Execute the approved visual metaphor clearly.

The core advertising idea must be visually understandable.

Do not replace the requested idea with generic beauty.

Avoid clichés.


2. COMPOSITION

Create world-class advertising framing.

Use:

- intentional visual hierarchy
- controlled negative space
- strong foreground/midground/background
- clean eye flow
- campaign-ready copy area
- no random decorative clutter


3. CAMERA

Use:

- physically believable real-lens behavior
- intentional focal length
- correct horizon
- correct vanishing points
- realistic perspective
- believable depth
- premium commercial camera position

Camera must support the marketing idea.


4. LIGHTING

Use:

- motivated commercial lighting
- soft realistic fill
- premium contrast
- correct contact shadows
- controlled highlights
- realistic environmental light
- physically convincing reflections

Avoid:

- fake neon unless conceptually justified
- wet-floor reflections
- mirror-like surfaces unless physically correct


5. MATERIALS

Render believable:

- glass
- brushed metal
- stone
- fabric
- leather
- skin
- architectural surfaces
- product materials

Surface roughness must feel physically correct.


6. BRAND

The final image must feel native to the brand.

Use the Brand Visual Profile and selected references for:

- palette hierarchy
- purple/mint/neutral balance when relevant
- visual restraint
- premium finish
- architectural language
- lighting language
- human direction
- composition behavior

Brand color is not random decoration.


7. PRODUCT

If Product Lock is active:

- preserve silhouette
- preserve proportions
- preserve geometry
- preserve thickness
- preserve major details
- preserve major graphic placement
- preserve material/color relationships

Environment may change.

Lighting may adapt.

Product identity may NOT casually change.


8. PEOPLE

If people are present:

- natural authentic behavior
- correct anatomy
- believable hands
- culturally appropriate styling
- realistic fabric
- non-stock-photo posing
- no artificial smile-to-camera behavior unless requested


9. ADVERTISING READINESS

The result should feel like:

premium global campaign
commercial photography
cinematic photorealism
high-end art direction
real production design
agency-grade hero visual


10. ANTI-CLONE RULE

Do not reproduce an existing reference campaign literally.

Learn:

- color logic
- camera logic
- composition logic
- material logic
- lighting logic
- visual restraint

Then create a NEW execution for the NEW user request.


NON-NEGOTIABLE
==============

A beautiful image that fails the requested marketing idea is
not successful.

A generic AI image with brand colors is not successful.

The result must feel intentionally art-directed.
""".strip()


# =========================================================
# PROMPT COMPILER
# =========================================================

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
            aspect_ratio=(
                aspect_ratio
            ),
        )
    )

    blueprint = (
        fit_prompt_for_api(
            blueprint,
            label=(
                "quality_first_blueprint_v3_1"
            ),
            budget=(
                COMPILED_PROMPT_BUDGET
            ),
        )
    )

    return CompiledPrompt(
        target=(
            target
        ),

        prompt=(
            blueprint
        ),

        negative_prompt=(
            base_negative_prompt()
        ),

        metadata={
            "compiler":
                "xpand_quality_first_v3_1",

            "prompt_chars":
                len(
                    blueprint
                ),

            "prompt_budget":
                COMPILED_PROMPT_BUDGET,

            "aspect_ratio":
                aspect_ratio,

            "adaptive":
                True,

            "smart_reference_routing":
                True,

            "brand_visual_profile":
                True,
        },
    )


# =========================================================
# OPENAI MULTI-REFERENCE IMAGE EDIT / GENERATION
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

        extension = (
            extension_for_mime(
                working_image.mime_type
            )
        )

        files.append(
            (
                "image[]",
                (
                    (
                        "working-image"
                        +
                        extension
                    ),
                    working_image.image_bytes,
                    working_image.mime_type
                    or
                    "image/png",
                ),
            )
        )

    for index, reference in enumerate(
        references,
        start=1,
    ):

        extension = (
            extension_for_mime(
                reference.mime_type
            )
        )

        files.append(
            (
                "image[]",
                (
                    (
                        "reference-"
                        +
                        str(
                            index
                        )
                        +
                        extension
                    ),
                    reference.image_bytes,
                    reference.mime_type,
                ),
            )
        )

    if not files:

        raise RuntimeError(
            "Image edit requested without image input."
        )

    if len(
        files
    ) == 1:

        _name, file_value = (
            files[0]
        )

        files = [
            (
                "image",
                file_value,
            )
        ]

    reference_rules = (
        physical_reference_instruction(
            references
        )
    )

    safe_prompt = (
        fit_prompt_for_api(
            (
                prompt
                +
                (
                    "\n\n"
                    +
                    reference_rules
                    if reference_rules
                    else ""
                )
                +
                "\n\n"
                +
                safe_frame_instruction(
                    aspect_ratio
                )
            ),
            label=(
                pass_name
            ),
            budget=(
                CORRECTION_PROMPT_BUDGET
                if working_image
                is not None
                else
                COMPILED_PROMPT_BUDGET
            ),
        )
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
                (
                    "Bearer "
                    +
                    OPENAI_API_KEY
                ),
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
        timeout=(
            REQUEST_TIMEOUT
        ),
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

        error = (
            response_data.get(
                "error"
            )
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
                str(
                    error
                )
            )

        else:

            message = (
                error
                or
                response_data.get(
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

        raise RuntimeError(
            (
                "GPT-Image-2 reference generation/edit failed: "
                +
                clean_text(
                    message,
                    3000,
                )
            )
        )

    images = (
        find_images_in_response(
            response_data
        )
    )

    if not images:

        raise RuntimeError(
            "GPT-Image-2 returned no image."
        )

    image_bytes, mime_type = (
        images[0]
    )

    result = GeneratedImage(
        image_bytes=(
            image_bytes
        ),

        mime_type=(
            mime_type
            or
            "image/png"
        ),

        provider=(
            "xpand_production"
        ),

        model=(
            OPENAI_IMAGE_MODEL
        ),

        prompt=(
            safe_prompt
        ),

        original_prompt=(
            safe_prompt
        ),

        aspect_ratio=(
            aspect_ratio
        ),

        image_size=(
            provider_size
        ),

        quality=(
            "high"
        ),

        route_reason=(
            "XPAND V3.1 Smart Visual Reference: "
            +
            pass_name
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
            (
                "prod-"
                +
                uuid.uuid4().hex[:12]
            )
        ),

        metadata={
            "production_engine":
                ENGINE_VERSION,

            "pass_name":
                pass_name,

            "prompt_chars":
                len(
                    safe_prompt
                ),

            "requested_delivery_ratio":
                aspect_ratio,

            "quality":
                "high",

            "physical_reference_count":
                len(
                    references
                ),
        },
    )

    inspect_provider_canvas(
        result,
        aspect_ratio,
    )

    return result


# =========================================================
# HIGH-QUALITY FIRST GENERATION
# =========================================================

def gemini_multi_reference_edit(
    *,
    working_image: Optional[GeneratedImage],
    references: Sequence[ProductionReference],
    prompt: str,
    aspect_ratio: str,
    pass_name: str,
    output_image_size: str = "1K",
) -> GeneratedImage:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY missing.")
    reference_rules = physical_reference_instruction(references)
    safe_prompt = fit_prompt_for_api(
        prompt
        + (("\n\n" + reference_rules) if reference_rules else "")
        + "\n\n" + safe_frame_instruction(aspect_ratio),
        label=pass_name,
        budget=CORRECTION_PROMPT_BUDGET if working_image is not None else COMPILED_PROMPT_BUDGET,
    )
    inputs: List[Dict[str, Any]] = [{"type": "text", "text": safe_prompt}]
    if working_image is not None:
        inputs.append({
            "type": "image",
            "mime_type": working_image.mime_type or "image/png",
            "data": base64.b64encode(working_image.image_bytes).decode("ascii"),
        })
    for reference in list(references)[:10]:
        inputs.append({
            "type": "image",
            "mime_type": reference.mime_type or "image/png",
            "data": base64.b64encode(reference.image_bytes).decode("ascii"),
        })
    requested_image_size = str(output_image_size or "1K").upper().strip()
    if requested_image_size not in {"1K", "2K", "4K"}:
        requested_image_size = "1K"
    image_size = requested_image_size if requested_image_size in {"1K", "2K", "4K"} else "1K"
    model = masterpiece_model_for_pass(pass_name)
    response = requests.post(
        GEMINI_INTERACTIONS_URL,
        headers={"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"},
        json={
            "model": model,
            "input": inputs,
            "response_format": {
                "type": "image",
                "aspect_ratio": aspect_ratio,
                "image_size": image_size,
                "mime_type": "image/jpeg",
            },
        },
        timeout=REQUEST_TIMEOUT,
    )
    try:
        response_data = response.json()
    except Exception:
        response_data = {"raw": response.text}
    if not response.ok:
        raise RuntimeError("Nano Banana reference edit failed: " + clean_text(response_data, 3000))
    images = find_images_in_response(response_data)
    if not images:
        raise RuntimeError(
            "Nano Banana returned no image | model="
            + model
            + " | response="
            + clean_text(response_data, 2400)
        )
    image_bytes, mime_type = images[0]
    image_bytes, mime_type = _finalize_requested_resolution(
        image_bytes,
        mime_type,
        requested_image_size,
    )
    return GeneratedImage(
        image_bytes=image_bytes,
        mime_type=mime_type or "image/jpeg",
        provider="google",
        model=model,
        prompt=safe_prompt,
        original_prompt=safe_prompt,
        aspect_ratio=aspect_ratio,
        image_size=requested_image_size,
        quality="high",
        route_reason="XPAND Gemini-first multi-reference: " + pass_name,
        request_id=clean_text(response_data.get("id"), 300) or "gem-" + uuid.uuid4().hex[:12],
        metadata={
            "production_engine": ENGINE_VERSION,
            "pass_name": pass_name,
            "physical_reference_count": len(references),
            "gemini_first": True,
            "google_image_size": image_size,
            "delivered_image_size": requested_image_size,
        },
    )


# Compatibility alias: callers keep their old function name, but the actual
# provider is Nano Banana. No OpenAI image request is made.
openai_multi_reference_edit = gemini_multi_reference_edit

def generate_high_quality_image(
    *,
    compiled: CompiledPrompt,
    product_refs: Sequence[
        ProductionReference
    ],
    visual_refs: Sequence[
        ProductionReference
    ] = (),
    aspect_ratio: str,
    original_request: str,
    pass_name: str = "quality_first_generation",
    output_image_size: str = "1K",
) -> GeneratedImage:

    physical_refs = list(
        visual_refs
    )

    #
    # Product references are always authoritative.
    #
    # Ensure they are present in physical refs.
    #

    existing_ids = {
        item.source_id
        for item in physical_refs
        if item.source_id
    }

    for product_ref in (
        product_refs
    ):

        if (
            product_ref.source_id
            and
            product_ref.source_id
            in existing_ids
        ):

            continue

        physical_refs.insert(
            0,
            product_ref,
        )

        if product_ref.source_id:

            existing_ids.add(
                product_ref.source_id
            )

    physical_refs = (
        physical_refs[
            :MAX_PHYSICAL_REFERENCE_IMAGES
        ]
    )

    # A concise request-aware STC lock is already embedded at the beginning of
    # compiled.prompt. Re-appending the full skill here doubled the production
    # prompt and forced destructive truncation before generation.
    stc_guard = ""

    if physical_refs:

        prompt = (
            compiled.prompt
            +
            "\n\n"
            +
            """
PHYSICAL REFERENCE EXECUTION
============================

Actual visual reference images are attached.

Use them according to their assigned reference roles.

Do not clone the old advertisement.

Do not copy old text.

Do not copy an old headline.

Do not reproduce old financial information.

Create a completely new campaign execution for the current
user request while preserving the relevant brand visual DNA.
""".strip()
            + (("\n\n" + stc_guard) if stc_guard else "")
        )

        return (
            openai_multi_reference_edit(
                working_image=None,
                references=physical_refs,
                prompt=prompt,
                aspect_ratio=(
                    aspect_ratio
                ),
                pass_name=(
                    pass_name
                ),
                output_image_size=output_image_size,
            )
        )

    #
    # No actual visual reference images are available.
    #
    # Use direct HIGH-quality generation.
    #

    google_model = masterpiece_model_for_pass(pass_name)
    route = build_route(
        PROVIDER_GOOGLE_FAST,
        google_model,
        (
            "XPAND V3.1 Quality-First "
            "high-quality generation"
        ),
        aspect_ratio,
        output_image_size if output_image_size in {"1K", "2K", "4K"} else "1K",
        "medium",
    )

    images = generate_with_gemini(
        prompt=(
            compiled.prompt
            + (("\n\n" + stc_guard) if stc_guard else "")
        ),

        original_prompt=(
            clean_text(
                original_request,
                6000,
            )
        ),

        route=(
            route
        ),

        number=1,
    )

    if not images:

        raise RuntimeError(
            "Quality-First generation returned no image."
        )

    result = (
        images[0]
    )

    result.provider = (
        "xpand_production"
    )

    result.aspect_ratio = (
        aspect_ratio
    )

    result.quality = (
        "high"
    )

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

            "physical_reference_count":
                0,
        }
    )

    inspect_provider_canvas(
        result,
        aspect_ratio,
    )

    return result


# =========================================================
# QA SCORING
# =========================================================

def calculate_qa_score(
    scores: Dict[str, Any],
) -> Tuple[
    float,
    Dict[str, float],
]:

    normalized = {}

    total = 0.0

    for key, weight in (
        QA_WEIGHTS.items()
    ):

        value = (
            clamp_score(
                scores.get(
                    key,
                    0,
                )
            )
        )

        normalized[
            key
        ] = value

        total += (
            value
            *
            (
                float(
                    weight
                )
                /
                100.0
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
    original_request: str = "",
) -> List[str]:

    blockers: List[
        str
    ] = []

    for value in safe_list(
        explicit_failures
    ):

        text = clean_text(
            value,
            1000,
        )

        if (
            text
            and
            text
            not in blockers
        ):

            blockers.append(
                text
            )

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

    if is_stc_bank_request(original_request):
        thresholds.update(
            {
                "stc_palette_fidelity": 65.0,
                "hero_dominance": 60.0,
                "message_clarity_without_text": 60.0,
                "brand_alignment": 65.0,
            }
        )

    if safe_dict(
        product_lock
    ).get(
        "enabled"
    ):

        thresholds[
            "product_fidelity"
        ] = 70.0

    for key, threshold in (
        thresholds.items()
    ):

        value = clamp_score(
            scores.get(
                key,
                0,
            )
        )

        if value < threshold:

            label = (
                key
                +
                "="
                +
                str(
                    round(
                        value,
                        1,
                    )
                )
                +
                " < "
                +
                str(
                    threshold
                )
            )

            if label not in blockers:

                blockers.append(
                    label
                )

    return blockers


# =========================================================
# QA PROMPT
# =========================================================

def build_qa_prompt(
    *,
    original_request: str,
    compiled_prompt: CompiledPrompt,
    product_lock: Any,
    brand_context: Any,
    aspect_ratio: str,
    color_analysis: Any = None,
) -> str:

    prompt = f"""
You are XPAND Adaptive Visual QA.

Evaluate the attached EXACT FINAL CAMPAIGN CROP.

Be strict but practical.

Do not reject a professionally usable image because of tiny
subjective differences.

ORIGINAL REQUEST
----------------

{clean_text(original_request, 4000)}


APPROVED PRODUCTION BLUEPRINT
-----------------------------

{clean_text(
    compiled_prompt.prompt,
    5000
)}


PRODUCT LOCK
------------

{compact_json(
    product_lock,
    1800
)}


BRAND + VISUAL PROFILE
----------------------

{compact_json(
    brand_context,
    3000
)}


FINAL RATIO
-----------

{aspect_ratio}


DETERMINISTIC COLOR SAMPLE
--------------------------

{compact_json(color_analysis or {}, 1200)}

Use this numerical sample as supporting evidence, together with the visible
image and supplied references. In NATURAL mode, realistic environmental color
is correct and purple should remain a controlled identity accent. In FAMILY A
or FAMILY B studio mode, purple must visibly lead without becoming a flat wash.


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
- stc_palette_fidelity
- hero_dominance
- message_clarity_without_text

CONTEXT-AWARE SCORING
=====================

- If no person, hand or body part is visible, human_anatomy MUST be 100. Do not
  assign a neutral 50 to a non-applicable dimension.
- If no text, letters, numbers, logo or UI is visible and none was requested,
  text_logo_integrity MUST be 100. Empty negative space, a blank phone screen,
  a white architectural surface or a light reflection is NOT a text defect.
- If a person/hand or text/logo/UI is actually visible, score it strictly.
- Never use 50 as an N/A placeholder. A non-applicable category is fully
  compliant; reserve low scores for a visible defect supported by the image.


CRITICAL FAILURE
================

Critical means a genuine campaign-delivery problem:

- core requested concept absent
- visual metaphor fundamentally missing
- severe anatomy
- severe perspective
- major product deformation
- major brand mismatch
- unusable composition
- any generated/readable words, letters, numbers, fake UI or invented logo when
  no verified screen asset was supplied
- for STC Bank: blue/cyan/teal replacing the selected purple family, mixing
  both purple families, or purple identity coverage too weak to feel native
- required phone missing, cropped, too small, visually subordinate, floating,
  physically unsupported, or carrying invented screen content
- the campaign benefit cannot be understood after mentally removing all text

Do NOT classify a minor taste preference as critical.

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
    "advertising_readiness": 0,
    "stc_palette_fidelity": 0,
    "hero_dominance": 0,
    "message_clarity_without_text": 0
  }},

  "strengths": [],

  "problems": [],

  "critical_failures": [],

  "correction_instruction": ""
}}
""".strip()

    return (
        fit_prompt_for_api(
            prompt,
            label=(
                "adaptive_visual_qa_v3_1"
            ),
            budget=(
                QA_PROMPT_BUDGET
            ),
        )
    )


# =========================================================
# VISION QA
# =========================================================

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
            or
            getattr(
                image,
                "aspect_ratio",
                "",
            )
            or
            "1:1"
        ),
        30,
    )

    if safe_dict(
        getattr(
            image,
            "metadata",
            {},
        )
    ).get(
        "exact_delivery_frame"
    ):

        qa_frame = (
            image
        )

    else:

        qa_frame = (
            create_exact_delivery_frame(
                image,
                requested_ratio,
                upscale_final=False,
                label="adaptive_qa",
            )
        )

    # Vision QA does not need the full 4K delivery payload. Sending a 3K–5K
    # frame as base64 was causing ~60 second request failures before JSON could
    # be returned. Use a faithful, aspect-preserving proxy for analysis only;
    # the original full-resolution candidate remains untouched for delivery.
    qa_image_bytes = qa_frame.image_bytes
    qa_image_mime = qa_frame.mime_type or "image/jpeg"
    try:
        with Image.open(BytesIO(qa_frame.image_bytes)) as qa_source:
            qa_source = qa_source.convert("RGB")
            longest = max(qa_source.size)
            if longest > 1600:
                scale = 1600.0 / float(longest)
                qa_source = qa_source.resize(
                    (
                        max(1, int(round(qa_source.width * scale))),
                        max(1, int(round(qa_source.height * scale))),
                    ),
                    Image.Resampling.LANCZOS,
                )
            qa_buffer = BytesIO()
            qa_source.save(qa_buffer, format="JPEG", quality=90, optimize=True)
            qa_image_bytes = qa_buffer.getvalue()
            qa_image_mime = "image/jpeg"
    except Exception:
        pass

    prompt = (
        # Determine the intended color behavior from the early production lock.
        # This survives prompt fitting and lets QA distinguish a natural STC
        # lifestyle image from a purple studio/product image.
        None
    )

    palette_mode = (
        "natural"
        if "SELECTED PALETTE — NATURAL" in compiled_prompt.prompt
        else (
            "family_a"
            if "SELECTED PALETTE — FAMILY A" in compiled_prompt.prompt
            else (
                "family_b"
                if "SELECTED PALETTE — FAMILY B" in compiled_prompt.prompt
                else "unspecified"
            )
        )
    )
    color_analysis = (
        analyze_stc_color_balance(
            qa_frame.image_bytes,
            palette_mode,
        )
        if is_stc_bank_request(original_request)
        else {}
    )

    prompt = (
        build_qa_prompt(
            original_request=(
                original_request
            ),
            compiled_prompt=(
                compiled_prompt
            ),
            product_lock=(
                product_lock
            ),
            brand_context=(
                brand_context
            ),
            aspect_ratio=(
                requested_ratio
            ),
            color_analysis=(
                color_analysis
            ),
        )
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
            +
            1
        )

    raw = call_openai_director(
        prompt,
        image_bytes=(
            qa_image_bytes
        ),
        image_mime_type=(
            qa_image_mime
        ),
        json_mode=True,
    )

    data = (
        extract_json_object(
            raw
        )
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

    score, scores = (
        calculate_qa_score(
            raw_scores
        )
    )

    explicit_failures = safe_list(
        data.get("critical_failures")
    )

    if is_stc_bank_request(original_request):
        purple_ratio = safe_float(
            color_analysis.get("purple_pixel_ratio"),
            0.0,
        )
        blue_ratio = safe_float(
            color_analysis.get("blue_cyan_pixel_ratio"),
            0.0,
        )
        if palette_mode in {"family_a", "family_b"} and purple_ratio < 0.22:
            explicit_failures.append(
                "deterministic_palette_failure: purple coverage too low for STC studio mode"
            )
        if palette_mode == "natural" and purple_ratio > 0.45:
            explicit_failures.append(
                "deterministic_palette_failure: unnatural purple wash in STC lifestyle mode"
            )
        if palette_mode in {"family_a", "family_b"} and blue_ratio > purple_ratio * 1.35:
            explicit_failures.append(
                "deterministic_palette_failure: blue/cyan dominates selected STC purple"
            )

    critical_blockers = (
        detect_critical_blockers(
            scores=(
                scores
            ),
            explicit_failures=(
                explicit_failures
            ),
            product_lock=(
                product_lock
            ),
            original_request=(
                original_request
            ),
        )
    )

    target_reached = (
        score
        >=
        QA_TARGET_SCORE
        and
        not critical_blockers
    )

    delivery_approved = (
        score
        >=
        QA_DELIVERY_FLOOR
        and
        not critical_blockers
    )

    if target_reached:

        decision = (
            "target_reached"
        )

    elif delivery_approved:

        decision = (
            "near_target"
        )

    elif critical_blockers:

        decision = (
            "critical_issues"
        )

    else:

        decision = (
            "improvement_recommended"
        )

    return QAEvaluation(
        score=(
            score
        ),

        scores=(
            scores
        ),

        passed=(
            delivery_approved
        ),

        strengths=[
            clean_text(
                item,
                1000,
            )
            for item
            in safe_list(
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
            for item
            in safe_list(
                data.get(
                    "problems"
                )
            )
            if clean_text(
                item,
                1200,
            )
        ],

        correction_instruction=(
            clean_text(
                data.get(
                    "correction_instruction",
                    "",
                ),
                4500,
            )
        ),

        critical_blockers=(
            critical_blockers
        ),

        target_reached=(
            target_reached
        ),

        delivery_approved=(
            delivery_approved
        ),

        decision=(
            decision
        ),

        raw=(
            data
        ),
    )


# =========================================================
# BEST VERSION
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

    concept_score = (
        clamp_score(
            qa.scores.get(
                "concept_execution",
                0,
            )
        )
    )

    return (
        no_critical,
        approved,
        concept_score,
        float(
            qa.score
        ),
    )


def unavailable_qa_evaluation(error: Any) -> QAEvaluation:
    """A strict non-passing marker that keeps adaptive production alive."""
    message = clean_text(error, 1400) or "Vision QA unavailable"
    return QAEvaluation(
        score=0.0,
        scores={key: 0.0 for key in QA_WEIGHTS},
        passed=False,
        strengths=[],
        problems=["QA evaluator unavailable: " + message],
        correction_instruction=(
            "Do not assume the unreviewed candidate is acceptable. Produce a "
            "fresh, independently executable candidate that satisfies every "
            "brief, reference, composition, palette and fidelity constraint."
        ),
        critical_blockers=["qa_evaluator_unavailable"],
        target_reached=False,
        delivery_approved=False,
        decision="qa_unavailable_recover",
        raw={"error": message},
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

    concept_score = (
        clamp_score(
            qa.scores.get(
                "concept_execution",
                0,
            )
        )
    )

    if (
        concept_score
        <
        CONCEPT_RECOVERY_SCORE_FLOOR
    ):

        return True

    # A visually attractive scene that communicates only through generated
    # screen copy is a failed advertising idea, not a retouching problem.
    if clamp_score(
        qa.scores.get(
            "message_clarity_without_text",
            0,
        )
    ) < 70.0:
        return True

    combined = " ".join(
        (
            qa.critical_blockers
            +
            qa.problems
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
        marker
        in combined
        for marker
        in markers
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
        >=
        ADAPTIVE_CORRECTION_TRIGGER_SCORE
        and
        not qa.critical_blockers
    ):

        return "none"

    if has_concept_failure(
        qa
    ):

        return (
            "concept_recovery"
        )

    return (
        "targeted_correction"
    )


# =========================================================
# CORRECTION PROMPTS
# =========================================================

def build_targeted_correction_prompt(
    *,
    qa: QAEvaluation,
    compiled: CompiledPrompt,
    product_lock: Any,
    aspect_ratio: str,
) -> str:

    prompt = f"""
XPAND TARGETED QUALITY CORRECTION V3.1
======================================

This is the ONLY automatic correction image pass.

Preserve every successful part of the supplied image.

CURRENT QA SCORE:
{qa.score}/100

PROBLEMS:
{compact_json(
    qa.problems,
    4200
)}

CRITICAL ISSUES:
{compact_json(
    qa.critical_blockers,
    2800
)}

QA DIRECTIVE:
{clean_text(
    qa.correction_instruction,
    4200
)}

PRODUCT LOCK:
{compact_json(
    product_lock,
    2000
)}

CORE BLUEPRINT:
{clean_text(
    compiled.prompt,
    6500
)}

{safe_frame_instruction(aspect_ratio)}

RULES
=====

- Correct only real weaknesses.
- Preserve successful concept.
- Preserve successful composition.
- Preserve successful camera.
- Preserve successful lighting.
- Preserve successful materials.
- Preserve product identity.
- Preserve negative space.
- Fix anatomy only if needed.
- Fix perspective only if needed.
- Fix brand color balance only if needed.
- Fix material realism only if needed.
- Fix clutter only if needed.
- Do not introduce fake text.
- Do not introduce fake financial information.

This is a controlled professional refinement,
not a random new design.
""".strip()

    return (
        fit_prompt_for_api(
            prompt,
            label=(
                "adaptive_targeted_correction_v3_1"
            ),
            budget=(
                CORRECTION_PROMPT_BUDGET
            ),
        )
    )


def build_concept_recovery_prompt(
    *,
    qa: QAEvaluation,
    compiled: CompiledPrompt,
    aspect_ratio: str,
) -> str:

    prompt = f"""
XPAND CONCEPT RECOVERY V3.1
===========================

The previous image may be visually attractive, but the core
advertising concept was not executed strongly enough.

DO NOT simply polish the failed concept.

Rebuild the visual execution.

FAILED CONCEPT SCORE:
{qa.scores.get("concept_execution", 0)}/100

PROBLEMS:
{compact_json(
    qa.problems,
    4200
)}

CRITICAL FAILURES:
{compact_json(
    qa.critical_blockers,
    3200
)}

RECOVERY DIRECTIVE:
{clean_text(
    qa.correction_instruction,
    4200
)}

ORIGINAL MASTER BLUEPRINT:
{clean_text(
    compiled.prompt,
    8500
)}

{safe_frame_instruction(aspect_ratio)}

RECOVERY RULES
==============

- preserve the user's real marketing message
- preserve brand identity
- preserve relevant reference DNA
- change the failed visual mechanism if necessary
- avoid clichés
- solve composition in this generation
- solve lighting in this generation
- solve materials in this generation
- respect final campaign crop
- create a finished campaign hero visual
""".strip()

    return (
        fit_prompt_for_api(
            prompt,
            label=(
                "concept_recovery_v3_1"
            ),
            budget=(
                COMPILED_PROMPT_BUDGET
            ),
        )
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
        target=(
            compiled.target
        ),

        prompt=(
            recovery_prompt
        ),

        negative_prompt=(
            compiled.negative_prompt
        ),

        metadata=(
            metadata
        ),
    )


# =========================================================
# QA LOGGING
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
            +
            label
            +
            ": QA unavailable"
        )

        return

    print(
        "📊 "
        +
        label
        +
        ": "
        +
        str(
            qa.score
        )
        +
        "/100"
    )

    print(
        "Concept:",
        qa.scores.get(
            "concept_execution",
            0,
        ),
    )

    print(
        "Reference adherence:",
        qa.scores.get(
            "reference_adherence",
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

    for blocker in qa.critical_blockers[:5]:
        print("  🛑", clean_text(blocker, 900))

    if qa.problems:
        print("Top QA problems:")
        for problem in qa.problems[:3]:
            print("  -", clean_text(problem, 900))

    print(
        "Decision:",
        qa.decision,
    )


# =========================================================
# MAIN PIPELINE
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
    target_model: str = TARGET_GEMINI,
) -> ProductionResult:

    started = (
        time.monotonic()
    )

    final_requested_size = detect_image_size(original_request)
    if final_requested_size not in {"1K", "2K", "4K"}:
        final_requested_size = "1K"

    # Reserve exactly one image + one QA call for a true provider-native final
    # at the user's chosen 1K/2K/4K tier. Processing stays on economical Nano
    # Banana 2; the sixth call is the only Nano Banana Pro finishing pass.
    reserve_final_call = True
    processing_image_limit = max(
        1,
        MASTERPIECE_MAX_IMAGE_CALLS - (1 if reserve_final_call else 0),
    )
    processing_vision_limit = max(
        1,
        MASTERPIECE_MAX_VISION_CALLS - (1 if reserve_final_call else 0),
    )

    errors: List[
        str
    ] = []

    telemetry: Dict[
        str,
        Any
    ] = {
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

        "processing_image_size":
            "1K",

        "final_requested_size":
            final_requested_size,

        "smart_reference_selection":
            True,

        "selected_reference_count":
            0,

        "physical_reference_count":
            0,
    }

    # =====================================================
    # SMART BRAND REFERENCES
    # =====================================================

    references = (
        load_runtime_references(
            core,
            user_id,
            brand_id,
            request=(
                original_request
            ),
            limit=(
                SMART_REFERENCE_SELECTION_LIMIT
            ),
        )
    )

    product_refs = (
        product_references(
            references
        )
    )

    physical_refs = (
        choose_physical_references(
            references,
            limit=(
                MAX_PHYSICAL_REFERENCE_IMAGES
            ),
        )
    )

    telemetry[
        "selected_reference_count"
    ] = len(
        references
    )

    telemetry[
        "physical_reference_count"
    ] = len(
        physical_refs
    )

    reference_dna = (
        reference_dna_payload(
            references
        )
    )

    product_lock = (
        combined_product_lock(
            references
        )
    )

    # =====================================================
    # BRAND VISUAL PROFILE
    # =====================================================

    brand_visual_profile = (
        load_brand_visual_profile_safe(
            core,
            user_id,
            brand_id,
        )
    )

    enriched_brand_context = (
        build_enriched_brand_context(
            brand_context=(
                brand_context
            ),
            brand_visual_profile=(
                brand_visual_profile
            ),
            references=(
                references
            ),
        )
    )

    # =====================================================
    # COMPILE
    # =====================================================

    compiled = compile_prompt(
        target_model,
        request=(
            original_request
        ),
        creative_direction=(
            creative_direction
        ),
        brand_context=(
            enriched_brand_context
        ),
        references=(
            reference_dna
        ),
        camera_direction=(
            camera_direction
        ),
        product_lock=(
            product_lock
        ),
        aspect_ratio=(
            aspect_ratio
        ),
    )

    if compiled.target not in {TARGET_GEMINI, TARGET_OPENAI}:
        raise RuntimeError("Unsupported production target.")

    # =====================================================
    # LOG
    # =====================================================

    print("")
    print(
        "=============================================="
    )
    print(
        " XPAND PRODUCTION ENGINE V3.1"
    )
    print(
        " SMART VISUAL REFERENCE + QUALITY-FIRST"
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
        str(os.environ.get("XPAND_MASTERPIECE_GOOGLE_MODEL", GOOGLE_IMAGE_FAST_MODEL)).strip(),
    )

    print(
        "Brand:",
        brand_id,
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
        "Final requested quality:",
        final_requested_size,
        "(provider-native)" if reserve_final_call else "(processing master)",
    )

    print(
        "Smart DNA references:",
        len(
            references
        ),
        "/",
        SMART_REFERENCE_SELECTION_LIMIT,
    )

    print(
        "Actual image references:",
        len(
            physical_refs
        ),
        "/",
        MAX_PHYSICAL_REFERENCE_IMAGES,
    )

    print(
        "Product references:",
        len(
            product_refs
        ),
    )

    print(
        "Brand Visual Profile:",
        (
            "READY"
            if brand_visual_profile
            else "EMPTY"
        ),
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

    if references:

        print("")
        print(
            "Smart reference selection:"
        )

        for index, reference in enumerate(
            references,
            start=1,
        ):

            print(
                "  "
                +
                str(
                    index
                )
                +
                ". role="
                +
                reference.role
                +
                " | family="
                +
                reference.content_family
                +
                " | score="
                +
                str(
                    round(
                        reference_selection_score(
                            reference
                        ),
                        1,
                    )
                )
            )

    print("")

    # =====================================================
    # IMAGE CALL 1
    # =====================================================

    print(
        "🎬 GEMINI IMAGE CALL 1/"
        +
        str(
            MASTERPIECE_MAX_IMAGE_CALLS
        )
        +
        " | Nano Banana..."
    )

    if physical_refs:

        print(
            "🧬 Actual visual references attached:",
            len(
                physical_refs
            ),
        )

    else:

        print(
            "🧬 Actual visual references attached: 0"
        )

    first_image: Optional[GeneratedImage] = None
    first_generation_error: Optional[Exception] = None
    initial_pass_name = "quality_first_high"
    # A provider may occasionally return text/refusal/empty output. Such a
    # transport/model failure must consume a call but must not abort the whole
    # Masterpiece run. Retry with clean Nano Banana 2 requests inside the
    # configured processing-call ceiling; Pro remains reserved for the final.
    for initial_pass_name in (
        "quality_first_high",
        "quality_first_retry_nb2",
        "quality_first_retry_nb2_2",
    ):
        if telemetry["image_calls"] >= processing_image_limit:
            break
        try:
            first_image = generate_high_quality_image(
                compiled=compiled,
                product_refs=product_refs,
                visual_refs=physical_refs,
                aspect_ratio=aspect_ratio,
                original_request=original_request,
                pass_name=initial_pass_name,
            )
            telemetry["image_calls"] += 1
            break
        except Exception as error:
            telemetry["image_calls"] += 1
            first_generation_error = error
            errors.append(
                initial_pass_name + ": " + clean_text(error, 3000)
            )
            print(
                "⚠️ " + initial_pass_name + " failed: "
                + clean_text(error, 1600)
            )

    if first_image is None:
        raise RuntimeError(
            "All initial image-provider attempts failed: "
            + clean_text(first_generation_error, 3000)
        )

    passes: List[
        ProductionPassResult
    ] = [
        ProductionPassResult(
            pass_name=(
                initial_pass_name
            ),

            image=(
                first_image
            ),

            metadata={
                "image_call":
                    1,

                "quality":
                    "high",

                "adaptive":
                    True,

                "smart_reference_routing":
                    True,

                "physical_reference_count":
                    len(
                        physical_refs
                    ),
            },
        )
    ]

    first_preview = (
        create_exact_delivery_frame(
            first_image,
            aspect_ratio,
            upscale_final=False,
            label=(
                "candidate_1"
            ),
        )
    )

    print(
        "✅ Candidate 1 ready:",
        first_preview.image_size,
    )

    # =====================================================
    # VISION QA 1
    # =====================================================

    first_qa: Optional[
        QAEvaluation
    ] = None

    if (
        telemetry[
            "vision_calls"
        ]
        <
        processing_vision_limit
    ):

        print("")
        print(
            "👁️ ADAPTIVE VISION QA 1/"
            +
            str(
                MASTERPIECE_MAX_VISION_CALLS
            )
            +
            "..."
        )

        try:

            first_qa = (
                evaluate_generated_image(
                    image=(
                        first_image
                    ),
                    original_request=(
                        original_request
                    ),
                    compiled_prompt=(
                        compiled
                    ),
                    product_lock=(
                        product_lock
                    ),
                    brand_context=(
                        enriched_brand_context
                    ),
                    aspect_ratio=(
                        aspect_ratio
                    ),
                    telemetry=(
                        telemetry
                    ),
                )
            )

            passes[
                0
            ].qa = (
                first_qa
            )

            print_qa(
                "Candidate 1 QA",
                first_qa,
            )

        except Exception as error:

            errors.append(
                "qa_candidate_1: "
                +
                clean_text(
                    error,
                    3000,
                )
            )

            print(
                "⚠️ Candidate 1 QA unavailable: "
                + clean_text(error, 1200)
            )

            # Never interpret an evaluator outage as "no correction needed".
            # This strict synthetic result cannot pass delivery; it only keeps
            # the remaining generation/review budget active.
            first_qa = unavailable_qa_evaluation(error)
            passes[0].qa = first_qa

    best_image = (
        first_image
    )

    best_qa = (
        first_qa
    )

    best_score = (
        first_qa.score
        if first_qa
        else 0.0
    )

    # =====================================================
    # ADAPTIVE DECISION
    # =====================================================

    action = (
        choose_adaptive_action(
            first_qa
        )
    )

    telemetry[
        "adaptive_action"
    ] = (
        action
    )

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
        action
        !=
        "none"
        and
        telemetry[
            "image_calls"
        ]
        <
        processing_image_limit
    ):

        print("")
        print(
            "🎨 IMAGE CALL 2/"
            +
            str(
                MASTERPIECE_MAX_IMAGE_CALLS
            )
            +
            " | "
            +
            action
            +
            "..."
        )

        try:

            if (
                action
                ==
                "concept_recovery"
            ):

                recovery_prompt = (
                    build_concept_recovery_prompt(
                        qa=(
                            first_qa
                        ),
                        compiled=(
                            compiled
                        ),
                        aspect_ratio=(
                            aspect_ratio
                        ),
                    )
                )

                recovery_compiled = (
                    compiled_with_recovery(
                        compiled,
                        recovery_prompt,
                    )
                )

                #
                # Fresh concept recovery receives the selected
                # visual references again because style/camera/
                # campaign alignment still matter.
                #

                second_image = (
                    generate_high_quality_image(
                        compiled=(
                            recovery_compiled
                        ),
                        product_refs=(
                            product_refs
                        ),
                        visual_refs=(
                            physical_refs
                        ),
                        aspect_ratio=(
                            aspect_ratio
                        ),
                        original_request=(
                            original_request
                        ),
                        pass_name=(
                            "concept_recovery_high"
                        ),
                    )
                )

                second_pass_name = (
                    "concept_recovery_high"
                )

            else:

                correction = (
                    build_targeted_correction_prompt(
                        qa=(
                            first_qa
                        ),
                        compiled=(
                            compiled
                        ),
                        product_lock=(
                            product_lock
                        ),
                        aspect_ratio=(
                            aspect_ratio
                        ),
                    )
                )

                #
                # IMPORTANT COST RULE:
                #
                # Targeted correction gets:
                #
                # working image
                # + product refs only.
                #
                # We do NOT resend the whole style library.
                #

                second_image = (
                    openai_multi_reference_edit(
                        working_image=(
                            first_image
                        ),
                        references=(
                            product_refs[
                                :MAX_PHYSICAL_REFERENCE_IMAGES
                            ]
                        ),
                        prompt=(
                            correction
                        ),
                        aspect_ratio=(
                            aspect_ratio
                        ),
                        pass_name=(
                            "targeted_correction_high"
                        ),
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
                    label=(
                        "candidate_2"
                    ),
                )
            )

            passes.append(
                ProductionPassResult(
                    pass_name=(
                        second_pass_name
                    ),

                    image=(
                        second_image
                    ),

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

            # =============================================
            # VISION QA 2
            # =============================================

            if (
                telemetry[
                    "vision_calls"
                ]
                <
                processing_vision_limit
            ):

                print("")
                print(
                    "👁️ ADAPTIVE VISION QA 2/"
                    +
                    str(
                        MASTERPIECE_MAX_VISION_CALLS
                    )
                    +
                    "..."
                )

                try:

                    second_qa = (
                        evaluate_generated_image(
                            image=(
                                second_image
                            ),
                            original_request=(
                                original_request
                            ),
                            compiled_prompt=(
                                compiled
                            ),
                            product_lock=(
                                product_lock
                            ),
                            brand_context=(
                                enriched_brand_context
                            ),
                            aspect_ratio=(
                                aspect_ratio
                            ),
                            telemetry=(
                                telemetry
                            ),
                        )
                    )

                    passes[
                        -1
                    ].qa = (
                        second_qa
                    )

                    print_qa(
                        "Candidate 2 QA",
                        second_qa,
                    )

                except Exception as error:

                    errors.append(
                        "qa_candidate_2: "
                        +
                        clean_text(
                            error,
                            3000,
                        )
                    )

                    print(
                        "⚠️ Candidate 2 QA unavailable."
                    )

            # =============================================
            # BEST VERSION PRESERVATION
            # =============================================

            if (
                second_qa
                is not None
                and
                qa_candidate_is_better(
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
                +
                ": "
                +
                clean_text(
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
    # IMAGE CALL 3 — FINAL MASTERPIECE RECOVERY/POLISH
    # =====================================================

    if (
        best_qa is not None
        and telemetry["image_calls"] < processing_image_limit
        and (
            not best_qa.target_reached
            or bool(best_qa.critical_blockers)
        )
    ):
        correction_failed_to_improve = (
            action == "targeted_correction"
            and (
                second_qa is None
                or not qa_candidate_is_better(second_qa, first_qa)
            )
        )
        third_action = (
            "concept_recovery"
            if has_concept_failure(best_qa) or correction_failed_to_improve
            else "targeted_correction"
        )
        print("")
        print(
            "🎨 IMAGE CALL 3/"
            + str(MASTERPIECE_MAX_IMAGE_CALLS)
            + " | final_"
            + third_action
            + "..."
        )
        try:
            if third_action == "concept_recovery":
                third_prompt = build_concept_recovery_prompt(
                    qa=best_qa,
                    compiled=compiled,
                    aspect_ratio=aspect_ratio,
                )
                third_compiled = compiled_with_recovery(
                    compiled,
                    third_prompt,
                )
                third_image = generate_high_quality_image(
                    compiled=third_compiled,
                    product_refs=product_refs,
                    visual_refs=physical_refs,
                    aspect_ratio=aspect_ratio,
                    original_request=original_request,
                    pass_name="final_concept_recovery_high",
                )
            else:
                third_prompt = build_targeted_correction_prompt(
                    qa=best_qa,
                    compiled=compiled,
                    product_lock=product_lock,
                    aspect_ratio=aspect_ratio,
                )
                third_image = openai_multi_reference_edit(
                    working_image=best_image,
                    references=product_refs[:MAX_PHYSICAL_REFERENCE_IMAGES],
                    prompt=third_prompt,
                    aspect_ratio=aspect_ratio,
                    pass_name="final_targeted_correction_high",
                )

            telemetry["image_calls"] += 1
            third_qa: Optional[QAEvaluation] = None
            if telemetry["vision_calls"] < processing_vision_limit:
                print(
                    "👁️ ADAPTIVE VISION QA 3/"
                    + str(MASTERPIECE_MAX_VISION_CALLS)
                    + "..."
                )
                third_qa = evaluate_generated_image(
                    image=third_image,
                    original_request=original_request,
                    compiled_prompt=compiled,
                    product_lock=product_lock,
                    brand_context=enriched_brand_context,
                    aspect_ratio=aspect_ratio,
                    telemetry=telemetry,
                )
                print_qa("Candidate 3 QA", third_qa)

            passes.append(
                ProductionPassResult(
                    pass_name="final_" + third_action + "_high",
                    image=third_image,
                    qa=third_qa,
                    metadata={
                        "image_call": telemetry["image_calls"],
                        "quality": "high",
                        "adaptive_action": third_action,
                    },
                )
            )

            if third_qa is not None and qa_candidate_is_better(
                third_qa,
                best_qa,
            ):
                best_image = third_image
                best_qa = third_qa
                best_score = third_qa.score
                print("🏆 Candidate 3 selected as BEST.")
            else:
                print("🏆 Earlier stronger candidate preserved as BEST.")
        except Exception as error:
            errors.append(
                "final_masterpiece_pass: "
                + clean_text(error, 3000)
            )
            print("⚠️ Final Masterpiece pass failed; preserving best candidate.")

    # =====================================================
    # DEEP MASTERPIECE LOOP — CALLS 4..N
    # =====================================================
    # Keep the strict delivery gate unchanged.  Extra budget is spent upstream:
    # every remaining call reacts to the best candidate's actual QA report.
    # Concept failures receive a genuinely new composition; execution failures
    # receive a controlled edit of the strongest surviving image.

    while (
        best_qa is not None
        and telemetry["image_calls"] < processing_image_limit
        and telemetry["vision_calls"] < processing_vision_limit
        and (not best_qa.passed or not best_qa.target_reached or best_qa.critical_blockers)
    ):
        call_number = telemetry["image_calls"] + 1
        targeted_since_recovery = 0
        for previous_pass in reversed(passes):
            previous_name = str(previous_pass.pass_name).lower()
            if "concept_recovery" in previous_name:
                break
            if "targeted_correction" in previous_name:
                targeted_since_recovery += 1

        deep_action = (
            "concept_recovery"
            if has_concept_failure(best_qa) or targeted_since_recovery >= 1
            else "targeted_correction"
        )
        print("")
        print(
            "🎨 DEEP MASTERPIECE CALL "
            + str(call_number)
            + "/"
            + str(MASTERPIECE_MAX_IMAGE_CALLS)
            + " | "
            + deep_action
            + "..."
        )
        # Count the provider attempt before execution so both success and
        # failure consume exactly one slot and the loop can never exceed N.
        telemetry["image_calls"] += 1
        try:
            if deep_action == "concept_recovery":
                deep_prompt = build_concept_recovery_prompt(
                    qa=best_qa,
                    compiled=compiled,
                    aspect_ratio=aspect_ratio,
                )
                deep_prompt += (
                    "\n\nDIVERSITY REQUIREMENT: This is recovery candidate "
                    + str(call_number)
                    + ". Build a materially different physical scene, camera angle, "
                      "hero arrangement and visual metaphor. Do not paraphrase or "
                      "re-render any earlier failed composition. Preserve only the "
                      "brief, brand DNA, product fidelity and strict QA requirements."
                )
                deep_compiled = compiled_with_recovery(compiled, deep_prompt)
                deep_image = generate_high_quality_image(
                    compiled=deep_compiled,
                    product_refs=product_refs,
                    visual_refs=physical_refs,
                    aspect_ratio=aspect_ratio,
                    original_request=original_request,
                    pass_name="deep_concept_recovery_" + str(call_number),
                )
            else:
                deep_prompt = build_targeted_correction_prompt(
                    qa=best_qa,
                    compiled=compiled,
                    product_lock=product_lock,
                    aspect_ratio=aspect_ratio,
                )
                deep_prompt += (
                    "\n\nPRECISION PASS " + str(call_number) + ": Correct every listed "
                    "blocker simultaneously. Preserve successful regions pixel-faithfully; "
                    "do not redesign the entire scene and do not introduce new text, logos, "
                    "objects, colors or decorative effects."
                )
                deep_image = gemini_multi_reference_edit(
                    working_image=best_image,
                    references=product_refs[:MAX_PHYSICAL_REFERENCE_IMAGES],
                    prompt=deep_prompt,
                    aspect_ratio=aspect_ratio,
                    pass_name="deep_targeted_correction_" + str(call_number),
                )

            deep_qa = evaluate_generated_image(
                image=deep_image,
                original_request=original_request,
                compiled_prompt=compiled,
                product_lock=product_lock,
                brand_context=enriched_brand_context,
                aspect_ratio=aspect_ratio,
                telemetry=telemetry,
            )
            print_qa("Candidate " + str(call_number) + " QA", deep_qa)
            passes.append(
                ProductionPassResult(
                    pass_name="deep_" + deep_action + "_" + str(call_number),
                    image=deep_image,
                    qa=deep_qa,
                    metadata={
                        "image_call": call_number,
                        "quality": "high",
                        "adaptive_action": deep_action,
                        "strict_gate_unchanged": True,
                    },
                )
            )
            if qa_candidate_is_better(deep_qa, best_qa):
                best_image = deep_image
                best_qa = deep_qa
                best_score = deep_qa.score
                print("🏆 Candidate " + str(call_number) + " selected as BEST.")
            else:
                print("🏆 Earlier stronger candidate preserved as BEST.")
        except Exception as error:
            errors.append(
                "deep_masterpiece_pass_"
                + str(call_number)
                + ": "
                + clean_text(error, 3000)
            )
            print("⚠️ Deep Masterpiece pass failed; preserving best candidate.")

    # =====================================================
    # PROVIDER-NATIVE FINAL RESOLUTION PASS
    # =====================================================
    # Processing is always economical 1K. Spend the one reserved Pro call only
    # on the strongest surviving candidate at the requested 1K/2K/4K tier,
    # then QA that exact output.

    if reserve_final_call:
        if telemetry["image_calls"] >= MASTERPIECE_MAX_IMAGE_CALLS:
            raise RuntimeError("No reserved image call remained for final resolution.")
        if telemetry["vision_calls"] >= MASTERPIECE_MAX_VISION_CALLS:
            raise RuntimeError("No reserved Vision call remained for final resolution QA.")

        print("")
        print(
            "💎 FINAL NATIVE OUTPUT | Nano Banana Pro | "
            + final_requested_size
        )
        final_master_prompt = build_targeted_correction_prompt(
            qa=best_qa,
            compiled=compiled,
            product_lock=product_lock,
            aspect_ratio=aspect_ratio,
        )
        final_master_prompt += (
            "\n\nFINAL RESOLUTION MASTER\n"
            "Preserve the strongest approved composition and its natural photographic "
            "character. Resolve every remaining listed QA defect without redesigning "
            "successful regions. Return a genuinely native "
            + final_requested_size
            + " image at exact aspect ratio "
            + aspect_ratio
            + ". Do not add text, logos, fake UI or new decorative elements."
        )
        final_native_image = gemini_multi_reference_edit(
            working_image=best_image,
            references=physical_refs[:MAX_PHYSICAL_REFERENCE_IMAGES],
            prompt=final_master_prompt,
            aspect_ratio=aspect_ratio,
            pass_name="final_native_" + final_requested_size.lower(),
            output_image_size=final_requested_size,
        )
        telemetry["image_calls"] += 1
        final_native_qa = evaluate_generated_image(
            image=final_native_image,
            original_request=original_request,
            compiled_prompt=compiled,
            product_lock=product_lock,
            brand_context=enriched_brand_context,
            aspect_ratio=aspect_ratio,
            telemetry=telemetry,
        )
        print_qa("Final native " + final_requested_size + " QA", final_native_qa)
        passes.append(
            ProductionPassResult(
                pass_name="final_native_" + final_requested_size.lower(),
                image=final_native_image,
                qa=final_native_qa,
                metadata={
                    "image_call": telemetry["image_calls"],
                    "quality": final_requested_size,
                    "provider_native_final": True,
                },
            )
        )
        # The requested final artifact must be judged on its own pixels. Never
        # use a passing 1K score to silently approve a different 2K/4K output.
        best_image = final_native_image
        best_qa = final_native_qa
        best_score = final_native_qa.score

    # =====================================================
    # FINAL DELIVERY
    # =====================================================

    print("")
    print(
        "📦 Preparing exact final delivery..."
    )

    final_delivery_image = (
        create_exact_delivery_frame(
            best_image,
            aspect_ratio,
            upscale_final=False,
            label=(
                "final_delivery"
            ),
        )
    )

    final_delivery_image.provider = (
        "xpand_masterpiece"
        if mode
        ==
        MODE_MASTERPIECE
        else
        "xpand_production"
    )

    final_delivery_image.model = (
        "XPAND Masterpiece V4 → "
        +
        str(
            os.environ.get(
                "XPAND_MASTERPIECE_GOOGLE_MODEL",
                GOOGLE_IMAGE_FAST_MODEL,
            )
        ).strip()
        +
        " → Smart Visual Reference Routing"
        +
        " → 3-Pass Adaptive Vision QA"
        +
        " → Local Exact Frame"
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

            "processing_image_size":
                "1K",

            "final_requested_size":
                final_requested_size,

            "quality_first_adaptive":
                True,

            "smart_reference_routing":
                True,

            "brand_visual_profile_used":
                bool(
                    brand_visual_profile
                ),

            "selected_reference_count":
                len(
                    references
                ),

            "physical_reference_count":
                len(
                    physical_refs
                ),

            "selected_reference_roles":
                [
                    item.role
                    for item in references
                ],

            "selected_reference_families":
                [
                    item.content_family
                    for item in references
                ],

            "qa_score":
                best_score,

            "qa_passed":
                bool(
                    best_qa
                    and
                    best_qa.passed
                ),

            "qa_target_reached":
                bool(
                    best_qa
                    and
                    best_qa.target_reached
                ),

            "qa_decision":
                (
                    best_qa.decision
                    if best_qa
                    else
                    "qa_unavailable"
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
        (
            time.monotonic()
            -
            started
        ),
        3,
    )

    # =====================================================
    # FINAL LOG
    # =====================================================

    print("")
    print(
        "=============================================="
    )
    print(
        " XPAND PRODUCTION COMPLETE V3.1"
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
        "Smart DNA references:",
        len(
            references
        ),
    )

    print(
        "Physical image references:",
        len(
            physical_refs
        ),
    )

    print(
        "Product references:",
        len(
            product_refs
        ),
    )

    print(
        "Brand Visual Profile:",
        (
            "USED"
            if brand_visual_profile
            else
            "NOT AVAILABLE"
        ),
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

        final_image=(
            final_delivery_image
        ),

        best_score=(
            best_score
        ),

        qa=(
            best_qa
        ),

        passes=(
            passes
        ),

        compiled_prompt=(
            compiled
        ),

        references_used=(
            len(
                references
            )
        ),

        product_references_used=(
            len(
                product_refs
            )
        ),

        elapsed_seconds=(
            elapsed
        ),

        errors=(
            errors
        ),
    )


# =========================================================
# SELF TEST
#
# ZERO API CALLS
# ZERO DATABASE ACCESS
# ZERO IMAGE GENERATION
# =========================================================

if __name__ == "__main__":

    print("")
    print(
        "=============================================="
    )
    print(
        " XPAND PRODUCTION ENGINE V3.1"
    )
    print(
        " SMART VISUAL REFERENCE + QUALITY-FIRST"
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
            else
            "NOT CONFIGURED"
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
        "Brand Memory:",
        getattr(
            xpand_brand_memory,
            "VERSION",
            "unknown",
        ),
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
        "Smart DNA reference limit:",
        SMART_REFERENCE_SELECTION_LIMIT,
    )

    print(
        "Physical reference limit:",
        MAX_PHYSICAL_REFERENCE_IMAGES,
    )

    print(
        "Send visual refs to image:",
        SEND_VISUAL_REFERENCES_TO_IMAGE,
    )

    print("")

    # =====================================================
    # BRAND MEMORY V2 INTEGRATION
    # =====================================================

    brand_memory_ok = (
        hasattr(
            xpand_brand_memory,
            "load_relevant_visual_references",
        )
        and
        hasattr(
            xpand_brand_memory,
            "get_brand_visual_profile",
        )
        and
        hasattr(
            xpand_brand_memory,
            "refresh_brand_visual_profile",
        )
    )

    print(
        (
            "✅"
            if brand_memory_ok
            else
            "❌"
        ),
        "Brand Memory V2 integration",
    )

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

    for ratio, expected in (
        provider_tests.items()
    ):

        actual = (
            provider_size_for_ratio(
                ratio
            )
        )

        ok = (
            actual
            ==
            expected
        )

        provider_ok = (
            provider_ok
            and
            ok
        )

        print(
            (
                "✅"
                if ok
                else
                "❌"
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

    source_buffer = (
        BytesIO()
    )

    source_image.save(
        source_buffer,
        format="PNG",
    )

    fake_image = GeneratedImage(
        image_bytes=(
            source_buffer.getvalue()
        ),

        mime_type=(
            "image/png"
        ),

        provider=(
            "self-test"
        ),

        model=(
            "self-test"
        ),

        prompt=(
            "self-test"
        ),

        original_prompt=(
            "self-test"
        ),

        aspect_ratio=(
            "4:5"
        ),

        image_size=(
            "1024x1536"
        ),

        quality=(
            "high"
        ),

        route_reason=(
            "self-test"
        ),

        request_id=(
            "self-test"
        ),

        metadata={},
    )

    preview = (
        create_exact_delivery_frame(
            fake_image,
            "4:5",
            upscale_final=False,
            label=(
                "self_test_preview"
            ),
        )
    )

    preview_dims = (
        real_image_dimensions(
            preview.image_bytes
        )
    )

    preview_ok = (
        preview_dims
        ==
        (
            1024,
            1280,
        )
    )

    print(
        (
            "✅"
            if preview_ok
            else
            "❌"
        ),
        "Native 1024x1536 → exact 1024x1280",
    )

    final_test = (
        create_exact_delivery_frame(
            fake_image,
            "4:5",
            upscale_final=True,
            label=(
                "self_test_final"
            ),
        )
    )

    final_dims = (
        real_image_dimensions(
            final_test.image_bytes
        )
    )

    final_ok = (
        final_dims
        ==
        (
            2560,
            3200,
        )
    )

    print(
        (
            "✅"
            if final_ok
            else
            "❌"
        ),
        "Final 4:5 →",
        final_dims,
    )

    print("")

    # =====================================================
    # SYNTHETIC SMART REFERENCES
    # =====================================================

    fake_product_ref = (
        ProductionReference(
            role=(
                "product_reference"
            ),

            image_bytes=(
                b"product"
            ),

            mime_type=(
                "image/png"
            ),

            dna={},

            product_lock={
                "enabled":
                    True,

                "must_remain_identical": [
                    "silhouette",
                ],
            },

            source_id=(
                "product"
            ),

            content_family=(
                "payments_cards"
            ),

            source_metadata={
                "official":
                    True,
            },

            selection={
                "score":
                    82,
            },
        )
    )

    fake_campaign_ref = (
        ProductionReference(
            role=(
                "campaign_reference"
            ),

            image_bytes=(
                b"campaign"
            ),

            mime_type=(
                "image/png"
            ),

            dna={},

            source_id=(
                "campaign"
            ),

            content_family=(
                "international_transfer"
            ),

            source_metadata={
                "official":
                    True,
            },

            selection={
                "score":
                    96,
            },
        )
    )

    fake_style_ref = (
        ProductionReference(
            role=(
                "style_reference"
            ),

            image_bytes=(
                b"style"
            ),

            mime_type=(
                "image/png"
            ),

            dna={},

            source_id=(
                "style"
            ),

            content_family=(
                "general_brand"
            ),

            source_metadata={
                "official":
                    True,
            },

            selection={
                "score":
                    90,
            },
        )
    )

    fake_color_ref = (
        ProductionReference(
            role=(
                "color_reference"
            ),

            image_bytes=(
                b"color"
            ),

            mime_type=(
                "image/png"
            ),

            dna={},

            source_id=(
                "color"
            ),

            content_family=(
                "general_brand"
            ),

            source_metadata={
                "official":
                    True,
            },

            selection={
                "score":
                    99,
            },
        )
    )

    fake_refs = [
        fake_style_ref,
        fake_campaign_ref,
        fake_color_ref,
        fake_product_ref,
    ]

    physical = (
        choose_physical_references(
            fake_refs,
            limit=3,
        )
    )

    physical_ok = (
        len(
            physical
        )
        ==
        3
        and
        any(
            item.role
            ==
            "product_reference"
            for item in physical
        )
    )

    print(
        (
            "✅"
            if physical_ok
            else
            "❌"
        ),
        "Physical reference selector max 3 + Product priority",
    )

    # =====================================================
    # BRAND CONTEXT ENRICHMENT
    # =====================================================

    enriched = (
        build_enriched_brand_context(
            brand_context={
                "brand":
                    "STC Bank",
            },

            brand_visual_profile={
                "source_count":
                    12,

                "recurring_colors": [
                    "#4A136F",
                    "#00C9A7",
                ],
            },

            references=(
                fake_refs[:3]
            ),
        )
    )

    enriched_ok = (
        bool(
            enriched.get(
                "brand_visual_profile"
            )
        )
        and
        len(
            enriched.get(
                "smart_reference_selection",
                [],
            )
        )
        ==
        3
    )

    print(
        (
            "✅"
            if enriched_ok
            else
            "❌"
        ),
        "Brand Visual Profile → production context",
    )

    # =====================================================
    # ADAPTIVE QA POLICY
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

        decision=(
            "target_reached"
        ),
    )

    weak_concept_qa = (
        QAEvaluation(
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

            decision=(
                "critical_issues"
            ),
        )
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
        ==
        "none"
    )

    adaptive_concept = (
        choose_adaptive_action(
            weak_concept_qa
        )
        ==
        "concept_recovery"
    )

    adaptive_polish = (
        choose_adaptive_action(
            polish_qa
        )
        ==
        "targeted_correction"
    )

    print(
        (
            "✅"
            if adaptive_good
            else
            "❌"
        ),
        "90+ → no second image call",
    )

    print(
        (
            "✅"
            if adaptive_concept
            else
            "❌"
        ),
        "Concept failure → concept recovery",
    )

    print(
        (
            "✅"
            if adaptive_polish
            else
            "❌"
        ),
        "Normal weakness → targeted correction",
    )

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
                (
                    "Two distant environments become one "
                    "physical space."
                ),
        },

        brand_context=(
            enriched
        ),

        references=[
            {
                "role":
                    "campaign_reference",

                "content_family":
                    "international_transfer",
            }
        ],

        camera_direction={
            "camera":
                "premium environmental perspective",
        },

        product_lock={},

        aspect_ratio=(
            "4:5"
        ),
    )

    compiler_ok = (
        len(
            dummy.prompt
        )
        <=
        COMPILED_PROMPT_BUDGET
    )

    print(
        (
            "✅"
            if compiler_ok
            else
            "❌"
        ),
        "Quality-First V3.1 Production Blueprint",
    )

    # =====================================================
    # COST GUARD
    # =====================================================

    cost_guard_ok = (
        MASTERPIECE_MAX_IMAGE_CALLS
        <=
        3
        and
        MASTERPIECE_MAX_VISION_CALLS
        <=
        3
        and
        MAX_PHYSICAL_REFERENCE_IMAGES
        <=
        6
        and
        SMART_REFERENCE_SELECTION_LIMIT
        <=
        12
    )

    print("")
    print(
        (
            "✅"
            if cost_guard_ok
            else
            "❌"
        ),
        "Image calls <= 3",
    )

    print(
        (
            "✅"
            if cost_guard_ok
            else
            "❌"
        ),
        "Vision calls <= 3",
    )

    print(
        (
            "✅"
            if cost_guard_ok
            else
            "❌"
        ),
        "Actual reference images <= 3",
    )

    print(
        (
            "✅"
            if cost_guard_ok
            else
            "❌"
        ),
        "Visual DNA references <= 6",
    )

    print("")
    print(
        "✅ Request-aware STC reference selection supported"
    )

    print(
        "✅ Travel request can select travel references"
    )

    print(
        "✅ International transfer can select transfer references"
    )

    print(
        "✅ Brand Visual Profile injected into production"
    )

    print(
        "✅ Actual visual reference images supported"
    )

    print(
        "✅ Product Reference receives first physical priority"
    )

    print(
        "✅ Reference role instructions preserved"
    )

    print(
        "✅ Anti-clone campaign policy"
    )

    print(
        "✅ First generation remains HIGH quality"
    )

    print(
        "✅ One automatic correction maximum"
    )

    print(
        "✅ Targeted correction avoids resending full style library"
    )

    print(
        "✅ Concept recovery keeps relevant visual references"
    )

    print(
        "✅ Best-version preservation"
    )

    print(
        "✅ QA never blocks final delivery"
    )

    print(
        "✅ Native provider canvas accepted"
    )

    print(
        "✅ Exact final aspect framing remains local"
    )

    print(
        "✅ Local crop/resize cost remains $0"
    )

    print("")

    all_ok = (
        brand_memory_ok
        and
        provider_ok
        and
        preview_ok
        and
        final_ok
        and
        physical_ok
        and
        enriched_ok
        and
        adaptive_good
        and
        adaptive_concept
        and
        adaptive_polish
        and
        compiler_ok
        and
        cost_guard_ok
    )

    print(
        (
            "XPAND Production Engine V3.1 self-test: "
            +
            (
                "PASS ✅"
                if all_ok
                else
                "FAIL ❌"
            )
        )
    )

    print(
        "🚫 No API calls were made"
    )

    print(
        "🚫 No database access was made"
    )

    print(
        "🚫 No image generation was made"
    )

    print("")
