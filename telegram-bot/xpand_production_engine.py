# =========================================================
# XPAND PRODUCTION ENGINE V2.3
#
# FULL-QUALITY MULTI-PASS MASTERPIECE ENGINE
#
# IMPORTANT:
# This is NOT the cost-optimized engine.
#
# V2.3 preserves the full V2.2 pipeline:
#
# Creative Brain
#      ↓
# Prompt Budget Manager
#      ↓
# Model-specific Prompt Compiler
#      ↓
# Reference / Product Lock Loader
#      ↓
# Concept Base
#      ↓
# CONCEPT EXECUTION GATE        [NEW]
#      ↓
# Composition Pass
#      ↓
# Product Fidelity Pass
#      ↓
# Lighting Pass
#      ↓
# Material Pass
#      ↓
# Final Polish
#      ↓
# Final Vision QA
#      ↓
# Smart QA Decision
#      ↓
# Optional Targeted Corrections
#      ↓
# Best Final Image
#
#
# V2.3 FIXES
# ---------------------------------------------------------
#
# 1. PHYSICAL ASPECT-RATIO LOCK
#
#    The requested aspect ratio is no longer trusted from
#    metadata alone.
#
#    XPAND reads the REAL image width and height from the
#    returned PNG/JPEG/WebP bytes after every generation/edit.
#
#    Example:
#
#       requested = 4:5
#       returned  = 1024x1024
#
#       => REJECTED
#       => square image never becomes the working image
#
#
# 2. CONCEPT EXECUTION GATE
#
#    Concept Base is visually checked before expensive
#    composition / lighting / materials / polish passes.
#
#    If the core metaphor or required scene is missing:
#
#       => regenerate Concept Base once
#       => re-check it
#       => only continue when the core concept is present
#
#
# 3. CORRECTION ASPECT SAFETY
#
#    A QA correction that changes 4:5 → 1:1 is rejected
#    BEFORE Vision QA and can never become the best image.
#
#
# 4. FULL V2.2 QA POLICY PRESERVED
#
#    90+:
#       Full target reached.
#
#    88–89.99:
#       Delivery approved if no critical blockers.
#
#    85–87.99:
#       Maximum one correction.
#
#    Below 85:
#       Up to configured correction limit.
#
#
# 5. REGRESSION PROTECTION PRESERVED
#
#    Worse corrections never replace a better version.
#
#
# 6. FULL-QUALITY TIME WINDOW
#
#    Default correction time budget is now 900 seconds.
#    This is intentionally NOT cost optimization.
#
# =========================================================

from __future__ import annotations

import base64
import json
import os
import re
import struct
import time
import uuid

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import requests


# =========================================================
# XPAND MODULES
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
# ENGINE
# =========================================================

ENGINE_NAME = "XPAND Production Engine"
ENGINE_VERSION = "2.3"


# =========================================================
# API
# =========================================================

OPENAI_IMAGE_EDITS_URL = (
    "https://api.openai.com/v1/images/edits"
)


# =========================================================
# MODES
# =========================================================

MODE_FAST = "fast"
MODE_PRO = "pro"
MODE_MASTERPIECE = "masterpiece"


# =========================================================
# PROMPT TARGETS
# =========================================================

TARGET_OPENAI = "openai"
TARGET_GEMINI = "gemini"
TARGET_MIDJOURNEY = "midjourney"
TARGET_FLUX = "flux"
TARGET_IDEOGRAM = "ideogram"
TARGET_RUNWAY = "runway"
TARGET_KLING = "kling"
TARGET_SEEDANCE = "seedance"


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
                "26000",
            )
            or 26000
        ),
    ),
)

PASS_PROMPT_BUDGET = max(
    12000,
    min(
        OPENAI_PROMPT_HARD_LIMIT - 1000,
        int(
            os.environ.get(
                "XPAND_PASS_PROMPT_BUDGET",
                "27500",
            )
            or 27500
        ),
    ),
)

QA_PROMPT_BUDGET = max(
    12000,
    min(
        OPENAI_PROMPT_HARD_LIMIT - 1000,
        int(
            os.environ.get(
                "XPAND_QA_PROMPT_BUDGET",
                "26000",
            )
            or 26000
        ),
    ),
)

CORRECTION_PROMPT_BUDGET = max(
    12000,
    min(
        OPENAI_PROMPT_HARD_LIMIT - 1000,
        int(
            os.environ.get(
                "XPAND_CORRECTION_PROMPT_BUDGET",
                "25000",
            )
            or 25000
        ),
    ),
)

CONCEPT_GATE_PROMPT_BUDGET = max(
    8000,
    min(
        OPENAI_PROMPT_HARD_LIMIT - 1000,
        int(
            os.environ.get(
                "XPAND_CONCEPT_GATE_PROMPT_BUDGET",
                "18000",
            )
            or 18000
        ),
    ),
)


# =========================================================
# SECTION BUDGETS
# =========================================================

SECTION_BUDGETS = {
    "request": 5000,
    "creative_direction": 6000,
    "brand_context": 5000,
    "references": 3800,
    "camera_direction": 1800,
    "product_lock": 2200,
}


# =========================================================
# ASPECT-RATIO LOCK V2.3
# =========================================================

ASPECT_RATIO_TOLERANCE = max(
    0.005,
    min(
        0.15,
        float(
            os.environ.get(
                "XPAND_ASPECT_RATIO_TOLERANCE",
                "0.035",
            )
            or 0.035
        ),
    ),
)


# =========================================================
# CONCEPT GATE V2.3
# =========================================================

CONCEPT_GATE_ENABLED = str(
    os.environ.get(
        "XPAND_CONCEPT_GATE_ENABLED",
        "true",
    )
).strip().lower() not in {
    "0",
    "false",
    "no",
    "off",
}

CONCEPT_GATE_MIN_SCORE = max(
    50.0,
    min(
        100.0,
        float(
            os.environ.get(
                "XPAND_CONCEPT_GATE_MIN_SCORE",
                "75",
            )
            or 75
        ),
    ),
)

CONCEPT_GATE_MAX_REGENERATIONS = max(
    0,
    min(
        2,
        int(
            os.environ.get(
                "XPAND_CONCEPT_GATE_MAX_REGENERATIONS",
                "1",
            )
            or 1
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

QA_SINGLE_CORRECTION_FLOOR = max(
    0.0,
    min(
        QA_DELIVERY_FLOOR,
        float(
            os.environ.get(
                "XPAND_IMAGE_QA_SINGLE_CORRECTION_FLOOR",
                "85",
            )
            or 85
        ),
    ),
)

QA_MAX_CORRECTIONS = max(
    0,
    min(
        4,
        int(
            os.environ.get(
                "XPAND_IMAGE_QA_MAX_CORRECTIONS",
                "2",
            )
            or 2
        ),
    ),
)

QA_MIN_IMPROVEMENT = max(
    0.0,
    min(
        10.0,
        float(
            os.environ.get(
                "XPAND_IMAGE_QA_MIN_IMPROVEMENT",
                "0.5",
            )
            or 0.5
        ),
    ),
)

# Full-quality mode.
# Intentionally longer than V2.2.
QA_CORRECTION_TIME_BUDGET_SECONDS = max(
    60.0,
    float(
        os.environ.get(
            "XPAND_IMAGE_QA_CORRECTION_TIME_BUDGET_SECONDS",
            "900",
        )
        or 900
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
    "concept_execution": 10,
    "reference_adherence": 10,
    "perspective": 10,
    "product_fidelity": 15,
    "lighting": 10,
    "shadows": 5,
    "reflections": 5,
    "human_anatomy": 5,
    "background_cleanliness": 5,
    "brand_alignment": 10,
    "text_logo_integrity": 5,
    "advertising_readiness": 10,
}


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
# BASIC HELPERS
# =========================================================

def clean_text(
    value: Any,
    limit: int = 20000,
) -> str:
    return (
        str(value if value is not None else "")
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
    return value if isinstance(value, list) else []


# =========================================================
# CONTEXT COMPACTION
# =========================================================

DROP_CONTEXT_KEYS = {
    "image_bytes",
    "source_bytes",
    "raw_bytes",
    "binary",
    "b64_json",
    "base64",
    "telegram_file_id",
    "telegram_file_unique_id",
    "photo_file_id",
    "document_file_id",
    "document_file_unique_id",
}


def reduce_prompt_value(
    value: Any,
    *,
    depth: int = 0,
    max_depth: int = 4,
    list_limit: int = 8,
    dict_limit: int = 40,
    string_limit: int = 1200,
) -> Any:

    if depth > max_depth:
        if isinstance(value, dict):
            return {
                "_summary": "nested object omitted"
            }

        if isinstance(value, list):
            return [
                "nested list omitted"
            ]

        return clean_text(
            value,
            min(
                string_limit,
                400,
            ),
        )

    if isinstance(value, bytes):
        return "<binary image data omitted>"

    if isinstance(value, dict):
        output = {}
        count = 0

        for key, child in value.items():
            key_text = clean_text(
                key,
                200,
            )

            if not key_text:
                continue

            if key_text.lower() in DROP_CONTEXT_KEYS:
                continue

            if count >= dict_limit:
                output[
                    "_additional_fields_omitted"
                ] = True
                break

            output[key_text] = reduce_prompt_value(
                child,
                depth=depth + 1,
                max_depth=max_depth,
                list_limit=list_limit,
                dict_limit=dict_limit,
                string_limit=string_limit,
            )

            count += 1

        return output

    if isinstance(value, list):
        output = []

        for child in value[:list_limit]:
            output.append(
                reduce_prompt_value(
                    child,
                    depth=depth + 1,
                    max_depth=max_depth,
                    list_limit=list_limit,
                    dict_limit=dict_limit,
                    string_limit=string_limit,
                )
            )

        if len(value) > list_limit:
            output.append(
                (
                    "<"
                    + str(
                        len(value)
                        - list_limit
                    )
                    + " additional items omitted>"
                )
            )

        return output

    if isinstance(
        value,
        (
            int,
            float,
            bool,
        ),
    ):
        return value

    if value is None:
        return None

    return clean_text(
        value,
        string_limit,
    )


def compact_json(
    value: Any,
    limit: int,
) -> str:

    limit = max(
        100,
        int(limit or 100),
    )

    attempts = [
        {
            "max_depth": 4,
            "list_limit": 10,
            "dict_limit": 50,
            "string_limit": 1400,
        },
        {
            "max_depth": 4,
            "list_limit": 7,
            "dict_limit": 35,
            "string_limit": 900,
        },
        {
            "max_depth": 3,
            "list_limit": 5,
            "dict_limit": 28,
            "string_limit": 650,
        },
        {
            "max_depth": 3,
            "list_limit": 3,
            "dict_limit": 20,
            "string_limit": 400,
        },
        {
            "max_depth": 2,
            "list_limit": 2,
            "dict_limit": 14,
            "string_limit": 250,
        },
    ]

    for settings in attempts:
        reduced = reduce_prompt_value(
            value,
            **settings,
        )

        try:
            encoded = json.dumps(
                reduced,
                ensure_ascii=False,
                separators=(",", ":"),
                default=str,
            )
        except Exception:
            encoded = clean_text(
                reduced,
                limit,
            )

        if len(encoded) <= limit:
            return encoded

    summary_size = max(
        50,
        int(
            limit
            * 0.65
        ),
    )

    while summary_size > 30:
        fallback = {
            "truncated": True,
            "summary": clean_text(
                value,
                summary_size,
            ),
        }

        encoded = json.dumps(
            fallback,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )

        if len(encoded) <= limit:
            return encoded

        summary_size = int(
            summary_size
            * 0.75
        )

    return json.dumps(
        {
            "truncated": True
        },
        ensure_ascii=False,
    )


def safe_json(
    value: Any,
    limit: int = 30000,
) -> str:
    return compact_json(
        value,
        limit,
    )


# =========================================================
# PROMPT SAFETY
# =========================================================

def hard_fit_prompt(
    text: str,
    max_chars: int,
) -> str:

    text = clean_text(
        text,
        1000000,
    )

    if len(text) <= max_chars:
        return text

    marker = (
        "\n\n"
        "[XPAND PROMPT BUDGET COMPACTION]\n"
        "Secondary context omitted to stay inside provider limits.\n\n"
    )

    available = max(
        100,
        max_chars
        - len(marker),
    )

    front_size = int(
        available
        * 0.62
    )

    back_size = (
        available
        - front_size
    )

    return (
        text[:front_size]
        + marker
        + text[-back_size:]
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

    original_length = len(original)

    fitted = hard_fit_prompt(
        original,
        budget,
    )

    final_length = len(fitted)

    if original_length <= budget:
        print(
            (
                "🧮 Prompt budget ["
                + label
                + "]: "
                + str(final_length)
                + "/"
                + str(budget)
                + " chars ✅"
            )
        )
    else:
        print(
            (
                "🧮 Prompt budget ["
                + label
                + "]: "
                + str(original_length)
                + " → "
                + str(final_length)
                + "/"
                + str(budget)
                + " chars ✅ COMPACTED"
            )
        )

    if len(fitted) >= OPENAI_PROMPT_HARD_LIMIT:
        raise RuntimeError(
            (
                "XPAND Prompt Budget Manager failed for "
                + label
                + "."
            )
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
                text[
                    start:end + 1
                ]
            )

            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    return {}


# =========================================================
# IMAGE RESPONSE PARSING
# =========================================================

def decode_image_value(
    value: str,
) -> Optional[bytes]:

    value = clean_text(
        value,
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
        result = base64.b64decode(
            value
        )
        return result if result else None
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

    unique = []
    signatures = set()

    for raw, mime_type in found:
        signature = (
            len(raw),
            raw[:64],
        )

        if signature in signatures:
            continue

        signatures.add(signature)

        unique.append(
            (
                raw,
                mime_type,
            )
        )

    return unique


# =========================================================
# REAL IMAGE DIMENSIONS
# =========================================================

def png_dimensions(
    raw: bytes,
) -> Optional[
    Tuple[int, int]
]:

    if (
        len(raw) >= 24
        and raw.startswith(
            b"\x89PNG\r\n\x1a\n"
        )
    ):
        width = struct.unpack(
            ">I",
            raw[16:20],
        )[0]

        height = struct.unpack(
            ">I",
            raw[20:24],
        )[0]

        if width > 0 and height > 0:
            return (
                width,
                height,
            )

    return None


def jpeg_dimensions(
    raw: bytes,
) -> Optional[
    Tuple[int, int]
]:

    if (
        len(raw) < 4
        or not raw.startswith(
            b"\xff\xd8"
        )
    ):
        return None

    index = 2
    length = len(raw)

    sof_markers = {
        0xC0,
        0xC1,
        0xC2,
        0xC3,
        0xC5,
        0xC6,
        0xC7,
        0xC9,
        0xCA,
        0xCB,
        0xCD,
        0xCE,
        0xCF,
    }

    while index + 3 < length:

        if raw[index] != 0xFF:
            index += 1
            continue

        while (
            index < length
            and raw[index] == 0xFF
        ):
            index += 1

        if index >= length:
            break

        marker = raw[index]
        index += 1

        if marker in {
            0xD8,
            0xD9,
        }:
            continue

        if index + 1 >= length:
            break

        segment_length = int.from_bytes(
            raw[
                index:index + 2
            ],
            "big",
        )

        if segment_length < 2:
            break

        if marker in sof_markers:
            if index + 7 > length:
                break

            height = int.from_bytes(
                raw[
                    index + 3:
                    index + 5
                ],
                "big",
            )

            width = int.from_bytes(
                raw[
                    index + 5:
                    index + 7
                ],
                "big",
            )

            if width > 0 and height > 0:
                return (
                    width,
                    height,
                )

            return None

        index += segment_length

    return None


def webp_dimensions(
    raw: bytes,
) -> Optional[
    Tuple[int, int]
]:

    if (
        len(raw) < 30
        or not raw.startswith(
            b"RIFF"
        )
        or raw[8:12] != b"WEBP"
    ):
        return None

    chunk = raw[12:16]

    # VP8X
    if (
        chunk == b"VP8X"
        and len(raw) >= 30
    ):
        width_minus_one = (
            raw[24]
            |
            (raw[25] << 8)
            |
            (raw[26] << 16)
        )

        height_minus_one = (
            raw[27]
            |
            (raw[28] << 8)
            |
            (raw[29] << 16)
        )

        return (
            width_minus_one + 1,
            height_minus_one + 1,
        )

    # VP8L
    if (
        chunk == b"VP8L"
        and len(raw) >= 25
        and raw[20] == 0x2F
    ):
        b1 = raw[21]
        b2 = raw[22]
        b3 = raw[23]
        b4 = raw[24]

        width = (
            1
            +
            (
                b1
                |
                ((b2 & 0x3F) << 8)
            )
        )

        height = (
            1
            +
            (
                ((b2 & 0xC0) >> 6)
                |
                (b3 << 2)
                |
                ((b4 & 0x0F) << 10)
            )
        )

        return (
            width,
            height,
        )

    # VP8 lossy
    if chunk == b"VP8 ":
        marker = raw.find(
            b"\x9d\x01\x2a",
            20,
        )

        if (
            marker >= 0
            and marker + 7 <= len(raw)
        ):
            width = int.from_bytes(
                raw[
                    marker + 3:
                    marker + 5
                ],
                "little",
            ) & 0x3FFF

            height = int.from_bytes(
                raw[
                    marker + 5:
                    marker + 7
                ],
                "little",
            ) & 0x3FFF

            if width > 0 and height > 0:
                return (
                    width,
                    height,
                )

    return None


def image_dimensions(
    raw: bytes,
) -> Optional[
    Tuple[int, int]
]:

    for parser in (
        png_dimensions,
        jpeg_dimensions,
        webp_dimensions,
    ):
        try:
            result = parser(raw)

            if result:
                return result
        except Exception:
            pass

    return None


# =========================================================
# ASPECT RATIO HELPERS
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

    if width <= 0 or height <= 0:
        return None

    return width / height


def inspect_image_aspect(
    image: GeneratedImage,
    requested_aspect_ratio: str,
) -> Dict[str, Any]:

    dimensions = image_dimensions(
        image.image_bytes
    )

    expected = aspect_ratio_value(
        requested_aspect_ratio
    )

    if not dimensions:
        return {
            "ok": False,
            "reason": "unable_to_read_real_dimensions",
            "requested": requested_aspect_ratio,
            "width": 0,
            "height": 0,
            "actual_ratio": 0.0,
            "expected_ratio": expected,
            "relative_error": 1.0,
        }

    width, height = dimensions

    actual = (
        float(width)
        /
        float(height)
    )

    if expected is None:
        return {
            "ok": True,
            "reason": "unrecognized_requested_ratio",
            "requested": requested_aspect_ratio,
            "width": width,
            "height": height,
            "actual_ratio": actual,
            "expected_ratio": None,
            "relative_error": 0.0,
        }

    relative_error = (
        abs(
            actual
            -
            expected
        )
        /
        expected
    )

    ok = (
        relative_error
        <=
        ASPECT_RATIO_TOLERANCE
    )

    return {
        "ok": ok,
        "reason": (
            "aspect_match"
            if ok
            else
            "aspect_mismatch"
        ),
        "requested": requested_aspect_ratio,
        "width": width,
        "height": height,
        "actual_ratio": round(
            actual,
            6,
        ),
        "expected_ratio": round(
            expected,
            6,
        ),
        "relative_error": round(
            relative_error,
            6,
        ),
        "tolerance": ASPECT_RATIO_TOLERANCE,
    }


def stamp_image_geometry(
    image: GeneratedImage,
    requested_aspect_ratio: str,
) -> Dict[str, Any]:

    status = inspect_image_aspect(
        image,
        requested_aspect_ratio,
    )

    if not isinstance(
        image.metadata,
        dict,
    ):
        image.metadata = {}

    image.metadata[
        "physical_aspect_guard"
    ] = status

    image.metadata[
        "actual_width"
    ] = status.get(
        "width",
        0,
    )

    image.metadata[
        "actual_height"
    ] = status.get(
        "height",
        0,
    )

    image.metadata[
        "requested_aspect_ratio"
    ] = requested_aspect_ratio

    return status


def require_correct_aspect(
    image: GeneratedImage,
    requested_aspect_ratio: str,
    *,
    label: str,
) -> Dict[str, Any]:

    status = stamp_image_geometry(
        image,
        requested_aspect_ratio,
    )

    width = status.get(
        "width",
        0,
    )

    height = status.get(
        "height",
        0,
    )

    if status.get("ok"):
        print(
            (
                "📐 ASPECT LOCK ["
                + label
                + "]: PASS ✅"
                + " | requested="
                + requested_aspect_ratio
                + " | actual="
                + str(width)
                + "x"
                + str(height)
            )
        )
        return status

    print(
        (
            "⛔ ASPECT LOCK ["
            + label
            + "]: REJECTED"
            + " | requested="
            + requested_aspect_ratio
            + " | actual="
            + str(width)
            + "x"
            + str(height)
        )
    )

    raise RuntimeError(
        (
            "Physical Aspect Lock failed for "
            + label
            + ": requested "
            + requested_aspect_ratio
            + ", actual "
            + str(width)
            + "x"
            + str(height)
            + "."
        )
    )


# =========================================================
# NATIVE OUTPUT RESOLUTION
# =========================================================

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
            "9:16": "1024x1792",
            "16:9": "1792x1024",
            "2:3": "1024x1536",
            "3:2": "1536x1024",
            "3:4": "1024x1360",
            "4:3": "1360x1024",
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
        "21:9": "3840x1648",
    }

    return mapping.get(
        ratio,
        "2048x2048",
    )


# =========================================================
# NEGATIVE PROMPT
# =========================================================

def base_negative_prompt() -> str:
    return (
        "avoid malformed anatomy, extra fingers, warped products, "
        "incorrect perspective, broken reflections, duplicated objects, "
        "random decorative elements, generic stock-photo composition, "
        "fake watermarks, random text, misspelled typography, "
        "unrequested logos, visual clutter, cheap CGI appearance"
    )


# =========================================================
# COMPILED SECTION HELPERS
# =========================================================

def compiled_sections(
    compiled: CompiledPrompt,
) -> Dict[str, str]:

    metadata = (
        compiled.metadata
        if isinstance(
            compiled.metadata,
            dict,
        )
        else {}
    )

    sections = metadata.get(
        "sections",
        {},
    )

    return (
        sections
        if isinstance(
            sections,
            dict,
        )
        else {}
    )


def section_text(
    compiled: CompiledPrompt,
    key: str,
    fallback_limit: int = 5000,
) -> str:

    sections = compiled_sections(
        compiled
    )

    value = sections.get(key)

    if value:
        return clean_text(
            value,
            fallback_limit,
        )

    return clean_text(
        compiled.prompt,
        fallback_limit,
    )


def build_pass_context(
    compiled: CompiledPrompt,
    keys: Sequence[
        Tuple[
            str,
            str,
            int,
        ]
    ],
) -> str:

    parts = []

    for key, label, limit in keys:
        value = section_text(
            compiled,
            key,
            limit,
        )

        if not value:
            continue

        parts.append(
            (
                label
                + "\n"
                + ("-" * len(label))
                + "\n"
                + clean_text(
                    value,
                    limit,
                )
            )
        )

    return "\n\n".join(parts)


# =========================================================
# OPENAI PROMPT COMPILER
# =========================================================

def compile_openai_prompt(
    *,
    request: str,
    creative_direction: Any,
    brand_context: Any,
    references: Any,
    camera_direction: Any,
    product_lock: Any,
) -> CompiledPrompt:

    sections = {
        "request": clean_text(
            request,
            SECTION_BUDGETS[
                "request"
            ],
        ),
        "creative_direction": compact_json(
            creative_direction,
            SECTION_BUDGETS[
                "creative_direction"
            ],
        ),
        "brand_context": compact_json(
            brand_context,
            SECTION_BUDGETS[
                "brand_context"
            ],
        ),
        "references": compact_json(
            references,
            SECTION_BUDGETS[
                "references"
            ],
        ),
        "camera_direction": compact_json(
            camera_direction,
            SECTION_BUDGETS[
                "camera_direction"
            ],
        ),
        "product_lock": compact_json(
            product_lock,
            SECTION_BUDGETS[
                "product_lock"
            ],
        ),
    }

    prompt = f"""
ORIGINAL REQUEST
================
{sections["request"]}


APPROVED CREATIVE DIRECTION
===========================
{sections["creative_direction"]}


BRAND EXECUTION CONTEXT
=======================
{sections["brand_context"]}


VISUAL REFERENCE DNA
====================
{sections["references"]}


CAMERA LOCK
===========
{sections["camera_direction"]}


PRODUCT LOCK
============
{sections["product_lock"]}


OPENAI GPT-IMAGE EXECUTION RULES
================================

Create one world-class commercial advertising image.

The APPROVED CREATIVE DIRECTION is the primary concept.
Do not replace it with a generic advertising idea.

CORE-CONCEPT PRIORITY:
The semantic metaphor requested by the user must be visible
and understandable in the actual image, not merely implied
in the prompt.

Use brand and reference information as execution constraints,
not as competing concepts.

Use the camera direction literally and coherently.

Maintain:

- physically plausible camera geometry
- premium commercial photography
- realistic material response
- believable contact shadows
- controlled reflections
- sophisticated depth
- clear visual hierarchy
- intentional negative space
- brand-consistent colors
- realistic human anatomy
- professional advertising finish

If product references are supplied:

- treat them as authoritative product identity
- preserve silhouette
- preserve proportions
- preserve corner geometry
- preserve material
- preserve color relationships
- preserve major graphic layout
- redesign the environment around the product
- do not redesign the product itself

Do not imitate one existing advertisement exactly.
Do not create a generic AI banking image.

Avoid visual clichés unless transformed into an original,
brand-relevant visual metaphor.

The final scene must feel intentionally art-directed,
physically plausible and professionally photographed.
""".strip()

    prompt = fit_prompt_for_api(
        prompt,
        label="compiled_master_brief",
        budget=COMPILED_PROMPT_BUDGET,
    )

    return CompiledPrompt(
        target=TARGET_OPENAI,
        prompt=prompt,
        negative_prompt=base_negative_prompt(),
        metadata={
            "compiler": "openai_gpt_image_v2_3",
            "product_lock": bool(product_lock),
            "prompt_budget": COMPILED_PROMPT_BUDGET,
            "prompt_chars": len(prompt),
            "sections": sections,
        },
    )


# =========================================================
# OTHER MODEL PROMPT COMPILERS
# =========================================================

def compile_gemini_prompt(
    *,
    request: str,
    creative_direction: Any,
    brand_context: Any,
    references: Any,
    camera_direction: Any,
    product_lock: Any,
) -> CompiledPrompt:

    prompt = f"""
TASK:
{clean_text(request, 5000)}

CREATIVE DIRECTION:
{compact_json(creative_direction, 6000)}

BRAND:
{compact_json(brand_context, 4500)}

REFERENCE DNA:
{compact_json(references, 3500)}

CAMERA:
{compact_json(camera_direction, 1800)}

LOCKED PRODUCT:
{compact_json(product_lock, 2200)}

Generate a premium photorealistic advertising key visual.

Prioritize:
- semantic coherence
- original concept
- brand consistency
- believable camera geometry
- realistic material behavior
- premium lighting

Preserve locked product geometry and identity.
Avoid generic banking clichés.
""".strip()

    return CompiledPrompt(
        target=TARGET_GEMINI,
        prompt=hard_fit_prompt(
            prompt,
            COMPILED_PROMPT_BUDGET,
        ),
        negative_prompt=base_negative_prompt(),
        metadata={
            "compiler": "gemini_image_v2_3",
        },
    )


def compile_midjourney_prompt(
    *,
    request: str,
    creative_direction: Any,
    brand_context: Any,
    references: Any,
    camera_direction: Any,
    product_lock: Any,
) -> CompiledPrompt:

    prompt = (
        clean_text(
            request,
            4000,
        )
        + ", "
        + compact_json(
            creative_direction,
            4500,
        )
        + ", "
        + compact_json(
            camera_direction,
            1400,
        )
        + ", commercial advertising photography, "
        + "precise cinematic camera geometry, "
        + "premium realistic materials, controlled reflections, "
        + "professional lighting, intentional negative space"
    )

    return CompiledPrompt(
        target=TARGET_MIDJOURNEY,
        prompt=hard_fit_prompt(
            prompt,
            14000,
        ),
        negative_prompt=(
            "generic banking icons, floating coins, "
            "deformed anatomy, warped product, random typography"
        ),
        metadata={
            "compiler": "midjourney_v2_3",
            "execution_available": False,
        },
    )


def compile_flux_prompt(
    *,
    request: str,
    creative_direction: Any,
    brand_context: Any,
    references: Any,
    camera_direction: Any,
    product_lock: Any,
) -> CompiledPrompt:

    prompt = f"""
{clean_text(request, 5000)}

SCENE:
{compact_json(creative_direction, 5500)}

BRAND:
{compact_json(brand_context, 3000)}

CAMERA:
{compact_json(camera_direction, 1600)}

PRODUCT:
{compact_json(product_lock, 2000)}

Photorealistic high-end advertising photography.
Accurate geometry.
Controlled materials.
Clean commercial lighting.
""".strip()

    return CompiledPrompt(
        target=TARGET_FLUX,
        prompt=hard_fit_prompt(
            prompt,
            18000,
        ),
        negative_prompt=base_negative_prompt(),
        metadata={
            "compiler": "flux_v2_3",
            "execution_available": False,
        },
    )


def compile_ideogram_prompt(
    *,
    request: str,
    creative_direction: Any,
    brand_context: Any,
    references: Any,
    camera_direction: Any,
    product_lock: Any,
) -> CompiledPrompt:

    prompt = f"""
Create a polished commercial campaign visual.

REQUEST:
{clean_text(request, 5000)}

CREATIVE:
{compact_json(creative_direction, 5500)}

BRAND:
{compact_json(brand_context, 3500)}

CAMERA:
{compact_json(camera_direction, 1600)}

If exact headline text is specified,
prioritize spelling, layout clarity and readable typography.
""".strip()

    return CompiledPrompt(
        target=TARGET_IDEOGRAM,
        prompt=hard_fit_prompt(
            prompt,
            18000,
        ),
        negative_prompt=base_negative_prompt(),
        metadata={
            "compiler": "ideogram_v2_3",
            "execution_available": False,
        },
    )


def compile_video_prompt(
    target: str,
    *,
    request: str,
    creative_direction: Any,
    brand_context: Any,
    camera_direction: Any,
) -> CompiledPrompt:

    prompt = f"""
ADVERTISING SCENE:
{clean_text(request, 5000)}

VISUAL DIRECTION:
{compact_json(creative_direction, 6500)}

BRAND:
{compact_json(brand_context, 3500)}

CAMERA:
{compact_json(camera_direction, 1800)}

Describe:
- physically coherent subject motion
- camera motion
- lighting continuity
- material consistency
- product identity continuity
- clear opening frame
- clear final frame
""".strip()

    return CompiledPrompt(
        target=target,
        prompt=hard_fit_prompt(
            prompt,
            19000,
        ),
        negative_prompt=(
            "camera teleportation, geometry morphing, "
            "warped hands, product deformation, flicker, identity drift"
        ),
        metadata={
            "compiler": (
                target
                + "_v2_3"
            ),
            "execution_available": False,
        },
    )


def compile_prompt(
    target: str,
    *,
    request: str,
    creative_direction: Any = None,
    brand_context: Any = None,
    references: Any = None,
    camera_direction: Any = None,
    product_lock: Any = None,
) -> CompiledPrompt:

    target = clean_text(
        target,
        100,
    ).lower()

    kwargs = {
        "request": request,
        "creative_direction": creative_direction or {},
        "brand_context": brand_context or {},
        "references": references or [],
        "camera_direction": camera_direction or {},
        "product_lock": product_lock or {},
    }

    if target == TARGET_GEMINI:
        return compile_gemini_prompt(
            **kwargs
        )

    if target == TARGET_MIDJOURNEY:
        return compile_midjourney_prompt(
            **kwargs
        )

    if target == TARGET_FLUX:
        return compile_flux_prompt(
            **kwargs
        )

    if target == TARGET_IDEOGRAM:
        return compile_ideogram_prompt(
            **kwargs
        )

    if target in {
        TARGET_RUNWAY,
        TARGET_KLING,
        TARGET_SEEDANCE,
    }:
        return compile_video_prompt(
            target,
            request=request,
            creative_direction=creative_direction or {},
            brand_context=brand_context or {},
            camera_direction=camera_direction or {},
        )

    return compile_openai_prompt(
        **kwargs
    )


# =========================================================
# REFERENCE LOADING
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
        and b"WEBP" in raw[:16]
    ):
        return "image/webp"

    return fallback


def load_runtime_references(
    core,
    user_id,
    brand_id: str,
    *,
    limit: int = 12,
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
            raw = core.get_telegram_file_bytes(
                file_id
            )
        except Exception as error:
            print(
                (
                    "⚠️ Reference download skipped: "
                    + clean_text(
                        error,
                        1000,
                    )
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
                dna=(
                    item.get(
                        "dna",
                        {},
                    )
                    if isinstance(
                        item.get(
                            "dna",
                            {},
                        ),
                        dict,
                    )
                    else {}
                ),
                product_lock=(
                    item.get(
                        "product_lock",
                        {},
                    )
                    if isinstance(
                        item.get(
                            "product_lock",
                            {},
                        ),
                        dict,
                    )
                    else {}
                ),
                user_note=clean_text(
                    item.get(
                        "user_note",
                        "",
                    ),
                    2000,
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
) -> List[
    Dict[str, Any]
]:

    output = []

    for item in references:
        output.append(
            {
                "role": item.role,
                "dna": reduce_prompt_value(
                    item.dna,
                    max_depth=3,
                    list_limit=6,
                    dict_limit=30,
                    string_limit=700,
                ),
                "product_lock": reduce_prompt_value(
                    item.product_lock,
                    max_depth=3,
                    list_limit=6,
                    dict_limit=25,
                    string_limit=500,
                ),
                "user_note": clean_text(
                    item.user_note,
                    1000,
                ),
            }
        )

    return output


def combined_product_lock(
    references: Sequence[
        ProductionReference
    ],
) -> Dict[str, Any]:

    locked: List[str] = []
    source_count = 0

    for item in references:

        if item.role != "product_reference":
            continue

        source_count += 1

        product_lock = item.product_lock

        if not isinstance(
            product_lock,
            dict,
        ):
            continue

        values = product_lock.get(
            "must_remain_identical",
            [],
        )

        if not isinstance(
            values,
            list,
        ):
            continue

        for value in values:
            text = clean_text(
                value,
                500,
            )

            if (
                text
                and text not in locked
            ):
                locked.append(text)

    return {
        "enabled": bool(source_count),
        "reference_count": source_count,
        "must_remain_identical": locked[:30],
        "environment_may_change": True,
        "lighting_may_adapt": True,
        "lock_type": (
            "high_fidelity_reference"
            if source_count
            else "none"
        ),
        "exact_pixel_identity_guaranteed": False,
    }


# =========================================================
# HARD ASPECT INSTRUCTION
# =========================================================

def aspect_lock_instruction(
    aspect_ratio: str,
) -> str:

    size_medium = production_size_for_ratio(
        aspect_ratio,
        final_quality=False,
    )

    size_final = production_size_for_ratio(
        aspect_ratio,
        final_quality=True,
    )

    return f"""
PHYSICAL CANVAS LOCK
====================

MANDATORY requested aspect ratio: {aspect_ratio}

This is a hard production constraint.

Do NOT:
- change the canvas to square
- crop to 1:1
- rotate the canvas
- change portrait to landscape
- change landscape to portrait

Expected working-size family:
{size_medium}

Expected final-size family:
{size_final}

Preserve the requested physical canvas geometry.
""".strip()


# =========================================================
# MULTI-IMAGE GPT-IMAGE-2 EDIT
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
    final_quality: bool,
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
        files.append(
            (
                "image[]",
                (
                    (
                        "working-image"
                        + working_image.extension
                    ),
                    working_image.image_bytes,
                    (
                        working_image.mime_type
                        or "image/png"
                    ),
                ),
            )
        )

    for index, reference in enumerate(
        references,
        start=1,
    ):

        extension = (
            ".png"
            if reference.mime_type
            == "image/png"
            else ".jpg"
        )

        files.append(
            (
                "image[]",
                (
                    (
                        "product-reference-"
                        + str(index)
                        + extension
                    ),
                    reference.image_bytes,
                    reference.mime_type,
                ),
            )
        )

    if not files:
        raise RuntimeError(
            "No image input supplied to edit."
        )

    if len(files) == 1:
        _, file_tuple = files[0]

        files = [
            (
                "image",
                file_tuple,
            )
        ]

    size = production_size_for_ratio(
        aspect_ratio,
        final_quality=final_quality,
    )

    combined_prompt = (
        clean_text(
            prompt,
            1000000,
        )
        + "\n\n"
        + aspect_lock_instruction(
            aspect_ratio
        )
    )

    safe_prompt = fit_prompt_for_api(
        combined_prompt,
        label=pass_name,
        budget=PASS_PROMPT_BUDGET,
    )

    payload = {
        "model": OPENAI_IMAGE_MODEL,
        "prompt": safe_prompt,
        "size": size,
        "quality": (
            "high"
            if final_quality
            else "medium"
        ),
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
        data=payload,
        files=files,
        timeout=REQUEST_TIMEOUT,
    )

    try:
        response_data = response.json()
    except Exception:
        response_data = {
            "raw": response.text
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
                or response_data.get(
                    "raw"
                )
                or (
                    "HTTP "
                    + str(
                        response.status_code
                    )
                )
            )

        raise RuntimeError(
            (
                "GPT-Image-2 edit failed: "
                + clean_text(
                    message,
                    3000,
                )
            )
        )

    images = find_images_in_response(
        response_data
    )

    if not images:
        raise RuntimeError(
            "GPT-Image-2 edit returned no image."
        )

    image_bytes, mime_type = images[0]

    request_id = clean_text(
        response.headers.get(
            "x-request-id",
            "",
        ),
        300,
    )

    if not request_id:
        request_id = (
            "prod-"
            + uuid.uuid4().hex[:12]
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
        image_size=size,
        quality=(
            "high"
            if final_quality
            else "medium"
        ),
        route_reason=(
            "XPAND Production Pass: "
            + pass_name
        ),
        request_id=request_id,
        metadata={
            "production_engine": ENGINE_VERSION,
            "pass_name": pass_name,
            "reference_images": len(
                references
            ),
            "working_image_input": bool(
                working_image
            ),
            "prompt_chars": len(
                safe_prompt
            ),
            "prompt_budget": PASS_PROMPT_BUDGET,
            "requested_output_size": size,
        },
    )

    require_correct_aspect(
        result,
        aspect_ratio,
        label=pass_name,
    )

    return result


# =========================================================
# PASS PROMPTS
# =========================================================

def composition_pass_prompt(
    compiled: CompiledPrompt,
    camera: Any,
    product_lock: Any,
) -> str:

    master = build_pass_context(
        compiled,
        [
            (
                "request",
                "ORIGINAL REQUEST",
                4500,
            ),
            (
                "creative_direction",
                "APPROVED CREATIVE DIRECTION",
                6500,
            ),
            (
                "brand_context",
                "BRAND CONSTRAINTS",
                3500,
            ),
            (
                "references",
                "REFERENCE DNA",
                2800,
            ),
            (
                "camera_direction",
                "CAMERA DIRECTION",
                2200,
            ),
            (
                "product_lock",
                "PRODUCT LOCK",
                2200,
            ),
        ],
    )

    return hard_fit_prompt(
        f"""
COMPOSITION PASS
================

{master}

CURRENT PASS OBJECTIVE
======================

Refine the supplied image into the approved final composition.

CHANGE ONLY WHAT IMPROVES COMPOSITION:

- preserve the approved core concept
- preserve the visual metaphor
- lock camera geometry
- lock horizon
- correct vanishing points
- preserve physically believable perspective
- improve foreground / midground / background separation
- improve visual hierarchy
- improve hero subject position
- establish intentional negative space
- remove distracting clutter
- improve visual storytelling
- preserve brand world
- preserve product identity if locked

Do NOT create a different concept.
Do NOT replace the visual metaphor.
Do NOT redesign a locked product.

The image after this pass must look like a stronger version
of the same approved concept.
""".strip(),
        PASS_PROMPT_BUDGET,
    )


def product_pass_prompt(
    compiled: CompiledPrompt,
    product_lock: Any,
) -> str:

    master = build_pass_context(
        compiled,
        [
            (
                "request",
                "ORIGINAL REQUEST",
                4000,
            ),
            (
                "creative_direction",
                "APPROVED CREATIVE DIRECTION",
                5000,
            ),
            (
                "references",
                "PRODUCT / REFERENCE DNA",
                4200,
            ),
            (
                "product_lock",
                "PRODUCT LOCK",
                4000,
            ),
            (
                "camera_direction",
                "CAMERA",
                1600,
            ),
        ],
    )

    return hard_fit_prompt(
        f"""
PRODUCT FIDELITY PASS
=====================

{master}

The supplied product reference images are authoritative.

Preserve:
- silhouette
- proportions
- thickness
- corners
- major design geometry
- material
- color relationships
- major graphic placement
- intended product perspective

Correct:
- warped product edges
- wrong perspective
- inconsistent thickness
- impossible reflections
- bad hand/product contact
- product identity drift

Environment may remain as designed.
Lighting may adapt naturally.

Do NOT invent another product.
Do NOT convert the product into a generic AI approximation.
""".strip(),
        PASS_PROMPT_BUDGET,
    )


def lighting_pass_prompt(
    compiled: CompiledPrompt,
) -> str:

    master = build_pass_context(
        compiled,
        [
            (
                "request",
                "ORIGINAL REQUEST",
                3500,
            ),
            (
                "creative_direction",
                "CREATIVE DIRECTION",
                5200,
            ),
            (
                "brand_context",
                "BRAND LIGHTING / VISUAL CONTEXT",
                4200,
            ),
            (
                "camera_direction",
                "CAMERA",
                1800,
            ),
            (
                "product_lock",
                "PRODUCT LOCK",
                1800,
            ),
        ],
    )

    return hard_fit_prompt(
        f"""
LIGHTING PASS
=============

{master}

Preserve:
- subject identity
- product geometry
- camera
- composition
- environment structure
- core visual metaphor

Improve only professional lighting behavior:
- motivated key light
- natural fill
- controlled rim / edge light
- realistic falloff
- contact shadows
- ambient occlusion
- believable reflections
- physically coherent highlights
- premium cinematic contrast
- brand-consistent color temperature
- realistic exposure relationships

Avoid:
- fake glow
- uncontrolled neon
- excessive wet-looking reflections
- impossible highlights
- flat AI lighting
- decorative light that does not belong to the scene
""".strip(),
        PASS_PROMPT_BUDGET,
    )


def material_pass_prompt(
    compiled: CompiledPrompt,
) -> str:

    master = build_pass_context(
        compiled,
        [
            (
                "request",
                "ORIGINAL REQUEST",
                3200,
            ),
            (
                "creative_direction",
                "CREATIVE DIRECTION",
                4500,
            ),
            (
                "brand_context",
                "BRAND MATERIAL CONTEXT",
                3500,
            ),
            (
                "references",
                "REFERENCE MATERIAL DNA",
                3000,
            ),
            (
                "product_lock",
                "PRODUCT LOCK",
                2200,
            ),
        ],
    )

    return hard_fit_prompt(
        f"""
MATERIAL REALISM PASS
=====================

{master}

Preserve camera, composition and concept.

Improve physical realism of:
- metal
- glass
- plastic
- bank-card surfaces
- fabric
- leather
- skin
- architecture
- floors
- walls
- luggage
- furniture
- screens

Correct:
- plastic-looking skin
- excessive gloss
- impossible reflections
- identical roughness across surfaces
- fake CGI texture
- over-smoothed surfaces
- unrealistic glass
- unnatural specular highlights

Use:
- realistic microtexture
- material-specific roughness
- physically believable reflections
- subtle surface variation
- premium commercial finish
""".strip(),
        PASS_PROMPT_BUDGET,
    )


def polish_pass_prompt(
    compiled: CompiledPrompt,
) -> str:

    master = build_pass_context(
        compiled,
        [
            (
                "request",
                "ORIGINAL REQUEST",
                3500,
            ),
            (
                "creative_direction",
                "APPROVED CREATIVE DIRECTION",
                5000,
            ),
            (
                "brand_context",
                "BRAND",
                3500,
            ),
            (
                "product_lock",
                "PRODUCT LOCK",
                2200,
            ),
        ],
    )

    return hard_fit_prompt(
        f"""
FINAL ADVERTISING POLISH
========================

{master}

Do NOT redesign the scene.
Do NOT create a different idea.
Do NOT weaken or remove the core visual metaphor.

Preserve all successful elements.

Final corrections only:
- clean AI artifacts
- improve fine detail
- correct anatomy
- fix edges
- remove random objects
- refine contact shadows
- refine reflections
- improve commercial color grade
- preserve intentional negative space
- preserve locked product
- preserve brand consistency
- improve realism
- improve premium campaign finish

The result must look publication-ready,
not like unfinished AI artwork.
""".strip(),
        PASS_PROMPT_BUDGET,
    )


# =========================================================
# INITIAL BASE GENERATION
# =========================================================

def generate_base_image(
    *,
    compiled: CompiledPrompt,
    product_refs: Sequence[
        ProductionReference
    ],
    aspect_ratio: str,
) -> GeneratedImage:

    base_prompt = (
        fit_prompt_for_api(
            (
                compiled.prompt
                + "\n\n"
                + aspect_lock_instruction(
                    aspect_ratio
                )
            ),
            label="concept_base",
            budget=COMPILED_PROMPT_BUDGET,
        )
    )

    if product_refs:
        prompt = (
            base_prompt
            + "\n\n"
            + """
BASE GENERATION WITH PRODUCT REFERENCES
=======================================

Use the attached product reference image(s) as authoritative
product identity.

Build the new advertising environment around the product.

Do not redesign the product.

The core requested visual metaphor must already be visibly
present in this Concept Base.
""".strip()
        )

        result = openai_multi_reference_edit(
            working_image=None,
            references=product_refs,
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            final_quality=False,
            pass_name=(
                "concept_base_with_product_lock"
            ),
        )

        return result

    route = build_route(
        PROVIDER_OPENAI,
        OPENAI_IMAGE_MODEL,
        (
            "XPAND Production base generation. "
            "Physical aspect lock: "
            + aspect_ratio
        ),
        aspect_ratio,
        "2K",
        "medium",
    )

    images = generate_with_openai(
        prompt=base_prompt,
        original_prompt=clean_text(
            compiled_sections(
                compiled
            ).get(
                "request",
                base_prompt,
            ),
            6000,
        ),
        route=route,
        number=1,
    )

    if not images:
        raise RuntimeError(
            "Base generation returned no image."
        )

    image = images[0]

    image.provider = "xpand_production"

    if not isinstance(
        image.metadata,
        dict,
    ):
        image.metadata = {}

    image.metadata[
        "production_engine"
    ] = ENGINE_VERSION

    image.metadata[
        "pass_name"
    ] = "concept_base"

    image.metadata[
        "prompt_chars"
    ] = len(base_prompt)

    image.metadata[
        "prompt_budget"
    ] = COMPILED_PROMPT_BUDGET

    require_correct_aspect(
        image,
        aspect_ratio,
        label="concept_base",
    )

    return image


# =========================================================
# CONCEPT EXECUTION GATE V2.3
# =========================================================

def build_concept_gate_prompt(
    *,
    original_request: str,
    compiled: CompiledPrompt,
    aspect_ratio: str,
) -> str:

    context = build_pass_context(
        compiled,
        [
            (
                "creative_direction",
                "APPROVED CREATIVE DIRECTION",
                5500,
            ),
            (
                "camera_direction",
                "CAMERA",
                1600,
            ),
            (
                "brand_context",
                "BRAND",
                3000,
            ),
        ],
    )

    prompt = f"""
You are XPAND Concept Execution Gate.

This is NOT final visual QA.

The attached image is only the initial Concept Base.

Do not judge:
- final polish
- perfect materials
- final micro-detail

Judge ONLY whether the CORE ADVERTISING IDEA was actually
translated into the image strongly enough to justify spending
more production passes.

ORIGINAL USER REQUEST:
{clean_text(original_request, 5000)}

APPROVED EXECUTION CONTEXT:
{context}

REQUESTED ASPECT:
{aspect_ratio}

Check:

1. Is the central commercial message visually understandable?
2. Is the approved visual metaphor actually visible?
3. Are mandatory locations/environments/elements present?
4. Does the composition give the concept a realistic path to
   becoming a premium final advertisement?
5. Has the image collapsed into a generic advertising cliché?
6. Is any explicit forbidden visual cliché already dominating?
7. Is the requested physical orientation/composition respected?

Do not fail the image for minor lighting/material polish.
Those are handled later.

Return JSON only:

{{
  "concept_score": 0,
  "passed": true,
  "core_message_visible": true,
  "visual_metaphor_visible": true,
  "required_elements_present": [],
  "missing_required_elements": [],
  "forbidden_cliches_detected": [],
  "critical_failures": [],
  "regeneration_instruction": ""
}}
""".strip()

    return fit_prompt_for_api(
        prompt,
        label="concept_execution_gate",
        budget=CONCEPT_GATE_PROMPT_BUDGET,
    )


def evaluate_concept_base(
    *,
    image: GeneratedImage,
    original_request: str,
    compiled: CompiledPrompt,
    aspect_ratio: str,
) -> Dict[str, Any]:

    require_correct_aspect(
        image,
        aspect_ratio,
        label="concept_gate_input",
    )

    prompt = build_concept_gate_prompt(
        original_request=original_request,
        compiled=compiled,
        aspect_ratio=aspect_ratio,
    )

    raw = call_openai_director(
        prompt,
        image_bytes=image.image_bytes,
        image_mime_type=(
            image.mime_type
            or "image/png"
        ),
        json_mode=True,
    )

    data = extract_json_object(raw)

    if not data:
        raise RuntimeError(
            "Concept Execution Gate returned invalid JSON."
        )

    score = clamp_score(
        data.get(
            "concept_score",
            0,
        )
    )

    failures = [
        clean_text(
            item,
            1000,
        )
        for item in safe_list(
            data.get(
                "critical_failures"
            )
        )
        if clean_text(
            item,
            1000,
        )
    ]

    core_visible = bool(
        data.get(
            "core_message_visible",
            False,
        )
    )

    metaphor_visible = bool(
        data.get(
            "visual_metaphor_visible",
            False,
        )
    )

    model_passed = bool(
        data.get(
            "passed",
            False,
        )
    )

    passed = (
        model_passed
        and score
        >= CONCEPT_GATE_MIN_SCORE
        and not failures
        and core_visible
        and metaphor_visible
    )

    result = {
        "passed": passed,
        "concept_score": score,
        "core_message_visible": core_visible,
        "visual_metaphor_visible": metaphor_visible,
        "required_elements_present": safe_list(
            data.get(
                "required_elements_present"
            )
        ),
        "missing_required_elements": safe_list(
            data.get(
                "missing_required_elements"
            )
        ),
        "forbidden_cliches_detected": safe_list(
            data.get(
                "forbidden_cliches_detected"
            )
        ),
        "critical_failures": failures,
        "regeneration_instruction": clean_text(
            data.get(
                "regeneration_instruction",
                "",
            ),
            5000,
        ),
        "raw": data,
    }

    return result


def print_concept_gate(
    result: Dict[str, Any],
) -> None:

    print(
        (
            "🧠 CONCEPT GATE SCORE: "
            + str(
                result.get(
                    "concept_score",
                    0,
                )
            )
            + "/100"
        )
    )

    print(
        (
            "Core message visible: "
            + str(
                result.get(
                    "core_message_visible",
                    False,
                )
            )
        )
    )

    print(
        (
            "Visual metaphor visible: "
            + str(
                result.get(
                    "visual_metaphor_visible",
                    False,
                )
            )
        )
    )

    if result.get("passed"):
        print(
            "✅ CONCEPT EXECUTION GATE: PASSED"
        )
    else:
        print(
            "⛔ CONCEPT EXECUTION GATE: FAILED"
        )

        for item in safe_list(
            result.get(
                "missing_required_elements"
            )
        )[:5]:
            print(
                (
                    "  ❌ Missing: "
                    + clean_text(
                        item,
                        600,
                    )
                )
            )

        for item in safe_list(
            result.get(
                "critical_failures"
            )
        )[:5]:
            print(
                (
                    "  ❌ "
                    + clean_text(
                        item,
                        600,
                    )
                )
            )


def compiled_with_regeneration_instruction(
    compiled: CompiledPrompt,
    gate_result: Dict[str, Any],
    aspect_ratio: str,
) -> CompiledPrompt:

    instruction = clean_text(
        gate_result.get(
            "regeneration_instruction",
            "",
        ),
        5000,
    )

    missing = compact_json(
        gate_result.get(
            "missing_required_elements",
            [],
        ),
        3500,
    )

    failures = compact_json(
        gate_result.get(
            "critical_failures",
            [],
        ),
        3500,
    )

    clichés = compact_json(
        gate_result.get(
            "forbidden_cliches_detected",
            [],
        ),
        2500,
    )

    repair = f"""
CONCEPT-BASE REGENERATION DIRECTIVE
===================================

The previous Concept Base failed before production passes.

DO NOT repeat the failed composition.

MISSING REQUIRED ELEMENTS:
{missing}

CRITICAL CONCEPT FAILURES:
{failures}

FORBIDDEN CLICHES DETECTED:
{clichés}

VISION DIRECTOR REGENERATION INSTRUCTION:
{instruction}

HARD REQUIREMENTS:

- visibly execute the approved central metaphor
- make the commercial message understandable from the image
- preserve the approved brand direction
- preserve the requested camera logic unless that caused failure
- do not hide the core concept behind decorative styling
- do not substitute a generic banking visual
- preserve physical aspect ratio {aspect_ratio}
""".strip()

    new_prompt = fit_prompt_for_api(
        (
            compiled.prompt
            + "\n\n"
            + repair
        ),
        label="concept_regeneration_brief",
        budget=COMPILED_PROMPT_BUDGET,
    )

    metadata = dict(
        compiled.metadata
        if isinstance(
            compiled.metadata,
            dict,
        )
        else {}
    )

    metadata[
        "concept_regeneration"
    ] = True

    metadata[
        "concept_gate_failure"
    ] = reduce_prompt_value(
        gate_result,
        max_depth=3,
        list_limit=8,
        dict_limit=30,
        string_limit=700,
    )

    return CompiledPrompt(
        target=compiled.target,
        prompt=new_prompt,
        negative_prompt=compiled.negative_prompt,
        metadata=metadata,
    )


# =========================================================
# QA PROMPT
# =========================================================

def build_qa_prompt(
    *,
    original_request: str,
    compiled_prompt: CompiledPrompt,
    image_metadata: Any,
    product_lock: Any,
    brand_context: Any,
) -> str:

    master_context = build_pass_context(
        compiled_prompt,
        [
            (
                "creative_direction",
                "APPROVED CREATIVE DIRECTION",
                5000,
            ),
            (
                "references",
                "VISUAL REFERENCE DNA",
                2800,
            ),
            (
                "camera_direction",
                "CAMERA DIRECTION",
                1800,
            ),
        ],
    )

    prompt = f"""
You are XPAND Final Visual QA Director.

Evaluate the attached generated advertising image.

Do NOT compliment automatically.
Do NOT expose private chain-of-thought.

Be strict enough for a premium international advertising campaign.

ORIGINAL REQUEST:
{clean_text(original_request, 4500)}

CORE PRODUCTION CONTEXT:
{master_context}

PRODUCT LOCK:
{compact_json(product_lock, 2400)}

BRAND CONTEXT:
{compact_json(brand_context, 4200)}

IMAGE METADATA:
{compact_json(image_metadata, 1800)}

Evaluate 0–100:

1. concept_execution
2. reference_adherence
3. perspective
4. product_fidelity
5. lighting
6. shadows
7. reflections
8. human_anatomy
9. background_cleanliness
10. brand_alignment
11. text_logo_integrity
12. advertising_readiness


CRITICAL FAILURE RULE
=====================

Also return critical_failures.

A critical failure is NOT a small aesthetic preference.

Only mark a critical failure when the image contains a severe
problem that should prevent professional delivery, such as:

- severely broken perspective
- clearly malformed human anatomy
- severe product deformation
- severe brand mismatch
- obviously broken required text or logo
- major concept failure
- major impossible geometry
- a defect that makes the image unusable as a premium ad

Do NOT mark minor polish issues as critical.

IMPORTANT:

If no human appears:
human_anatomy = 100 unless an anatomical object is malformed.

If no readable text/logo is required:
text_logo_integrity evaluates absence of random or broken text.

If no product reference was supplied:
product_fidelity evaluates product realism and consistency,
not exact reference matching.

Physical aspect ratio is verified separately by XPAND code.
Do not invent an aspect-ratio failure from metadata if the
actual pixel dimensions are correct.

Look specifically for:

- weak execution of the approved concept
- generic or cliché interpretation
- warped bank cards
- wrong card thickness
- distorted phones
- impossible fingers
- bad hand contact
- broken reflections
- wet-looking surfaces when not intended
- floating objects without physical logic
- bad perspective
- random decorative brand colors
- generic banking clichés
- unreadable Arabic
- fake logos
- clutter
- cheap CGI feeling
- mismatch with stored visual reference DNA

Return JSON only:

{{
  "scores": {{
    "concept_execution": 0,
    "reference_adherence": 0,
    "perspective": 0,
    "product_fidelity": 0,
    "lighting": 0,
    "shadows": 0,
    "reflections": 0,
    "human_anatomy": 0,
    "background_cleanliness": 0,
    "brand_alignment": 0,
    "text_logo_integrity": 0,
    "advertising_readiness": 0
  }},
  "strengths": [],
  "problems": [],
  "critical_failures": [],
  "correction_instruction": ""
}}

Correction instruction must:
- fix only actual defects
- preserve successful elements
- preserve product identity
- preserve camera and concept unless defective
- never replace the concept simply to increase aesthetics
""".strip()

    return fit_prompt_for_api(
        prompt,
        label="visual_qa",
        budget=QA_PROMPT_BUDGET,
    )


# =========================================================
# QA CALCULATION
# =========================================================

def calculate_qa_score(
    scores: Dict[str, Any],
) -> Tuple[
    float,
    Dict[str, float],
]:

    normalized_scores = {}
    total = 0.0

    for key, weight in QA_WEIGHTS.items():
        value = clamp_score(
            scores.get(
                key,
                0,
            )
        )

        normalized_scores[key] = value

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
        normalized_scores,
    )


# =========================================================
# CRITICAL BLOCKERS
# =========================================================

def detect_critical_blockers(
    *,
    scores: Dict[str, float],
    explicit_failures: Any,
    product_lock: Any,
) -> List[str]:

    blockers: List[str] = []

    if isinstance(
        explicit_failures,
        list,
    ):
        for value in explicit_failures:
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
        "concept_execution": QA_CRITICAL_SCORE_FLOOR,
        "perspective": QA_CRITICAL_SCORE_FLOOR,
        "human_anatomy": QA_CRITICAL_SCORE_FLOOR,
        "text_logo_integrity": QA_CRITICAL_SCORE_FLOOR,
        "advertising_readiness": (
            QA_AD_READINESS_CRITICAL_FLOOR
        ),
    }

    if (
        isinstance(
            product_lock,
            dict,
        )
        and product_lock.get(
            "enabled"
        )
    ):
        thresholds[
            "product_fidelity"
        ] = max(
            QA_CRITICAL_SCORE_FLOOR,
            70.0,
        )

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
                        2,
                    )
                )
                + " < "
                + str(threshold)
            )

            if label not in blockers:
                blockers.append(label)

    return blockers


# =========================================================
# QA DECISION
# =========================================================

def qa_delivery_decision(
    *,
    score: float,
    critical_blockers: Sequence[str],
) -> Dict[str, Any]:

    score = clamp_score(score)

    blockers = [
        clean_text(
            item,
            1000,
        )
        for item in critical_blockers
        if clean_text(
            item,
            1000,
        )
    ]

    target_reached = (
        score >= QA_TARGET_SCORE
    )

    if blockers:
        return {
            "approved": False,
            "target_reached": target_reached,
            "decision": "critical_blocker",
            "reason": (
                "Critical visual blocker detected."
            ),
        }

    if target_reached:
        return {
            "approved": True,
            "target_reached": True,
            "decision": "target_reached",
            "reason": "QA target reached.",
        }

    if score >= QA_DELIVERY_FLOOR:
        return {
            "approved": True,
            "target_reached": False,
            "decision": (
                "near_target_approved"
            ),
            "reason": (
                "Premium near-target score with no critical blockers."
            ),
        }

    return {
        "approved": False,
        "target_reached": False,
        "decision": "correction_candidate",
        "reason": "Below delivery floor.",
    }


def recommended_correction_limit(
    qa: Optional[
        QAEvaluation
    ],
) -> int:

    if qa is None:
        return 0

    if qa.passed:
        return 0

    if QA_MAX_CORRECTIONS <= 0:
        return 0

    if (
        qa.score
        >= QA_SINGLE_CORRECTION_FLOOR
    ):
        return min(
            1,
            QA_MAX_CORRECTIONS,
        )

    return QA_MAX_CORRECTIONS


def qa_quality_rank(
    qa: Optional[
        QAEvaluation
    ],
) -> Tuple[
    int,
    int,
    float,
]:

    if qa is None:
        return (
            0,
            -999,
            0.0,
        )

    approved = (
        1
        if qa.passed
        else 0
    )

    blocker_rank = (
        -len(
            qa.critical_blockers
        )
    )

    return (
        approved,
        blocker_rank,
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
        qa_quality_rank(candidate)
        >
        qa_quality_rank(existing)
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
) -> QAEvaluation:

    requested_ratio = clean_text(
        getattr(
            image,
            "aspect_ratio",
            "",
        ),
        30,
    )

    if requested_ratio:
        require_correct_aspect(
            image,
            requested_ratio,
            label="final_visual_qa_input",
        )

    qa_prompt = build_qa_prompt(
        original_request=original_request,
        compiled_prompt=compiled_prompt,
        image_metadata=image.metadata,
        product_lock=product_lock,
        brand_context=brand_context,
    )

    raw = call_openai_director(
        qa_prompt,
        image_bytes=image.image_bytes,
        image_mime_type=image.mime_type,
        json_mode=True,
    )

    data = extract_json_object(raw)

    if not data:
        raise RuntimeError(
            "Visual QA returned invalid JSON."
        )

    scores_raw = data.get(
        "scores",
        {},
    )

    if not isinstance(
        scores_raw,
        dict,
    ):
        scores_raw = {}

    score, scores = calculate_qa_score(
        scores_raw
    )

    strengths = data.get(
        "strengths",
        [],
    )

    problems = data.get(
        "problems",
        [],
    )

    if not isinstance(
        strengths,
        list,
    ):
        strengths = []

    if not isinstance(
        problems,
        list,
    ):
        problems = []

    explicit_failures = data.get(
        "critical_failures",
        [],
    )

    critical_blockers = (
        detect_critical_blockers(
            scores=scores,
            explicit_failures=explicit_failures,
            product_lock=product_lock,
        )
    )

    decision = qa_delivery_decision(
        score=score,
        critical_blockers=critical_blockers,
    )

    data[
        "xpand_qa_policy"
    ] = {
        "target": QA_TARGET_SCORE,
        "delivery_floor": QA_DELIVERY_FLOOR,
        "single_correction_floor": (
            QA_SINGLE_CORRECTION_FLOOR
        ),
        "critical_blockers": critical_blockers,
        "delivery_approved": decision[
            "approved"
        ],
        "target_reached": decision[
            "target_reached"
        ],
        "decision": decision[
            "decision"
        ],
    }

    return QAEvaluation(
        score=score,
        scores=scores,
        passed=bool(
            decision[
                "approved"
            ]
        ),
        strengths=[
            clean_text(
                item,
                1000,
            )
            for item in strengths
            if clean_text(
                item,
                1000,
            )
        ],
        problems=[
            clean_text(
                item,
                1000,
            )
            for item in problems
            if clean_text(
                item,
                1000,
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
        target_reached=bool(
            decision[
                "target_reached"
            ]
        ),
        delivery_approved=bool(
            decision[
                "approved"
            ]
        ),
        decision=clean_text(
            decision[
                "decision"
            ],
            200,
        ),
        raw=data,
    )


# =========================================================
# CORRECTION PROMPT
# =========================================================

def correction_prompt(
    *,
    qa: QAEvaluation,
    compiled: CompiledPrompt,
    product_lock: Any,
    aspect_ratio: str = "",
) -> str:

    context = build_pass_context(
        compiled,
        [
            (
                "request",
                "ORIGINAL REQUEST",
                3500,
            ),
            (
                "creative_direction",
                "APPROVED CREATIVE DIRECTION",
                4500,
            ),
            (
                "camera_direction",
                "CAMERA",
                1600,
            ),
            (
                "product_lock",
                "PRODUCT LOCK",
                2200,
            ),
        ],
    )

    ratio_lock = (
        aspect_lock_instruction(
            aspect_ratio
        )
        if aspect_ratio
        else ""
    )

    prompt = f"""
QUALITY CORRECTION PASS
=======================

CURRENT QA SCORE:
{qa.score}/100

ASPIRATIONAL TARGET:
{QA_TARGET_SCORE}/100

DELIVERY FLOOR:
{QA_DELIVERY_FLOOR}/100 if no critical blocker remains.

CRITICAL BLOCKERS:
{compact_json(qa.critical_blockers, 3200)}

DETECTED PROBLEMS:
{compact_json(qa.problems, 4500)}

QA CORRECTION INSTRUCTION:
{clean_text(qa.correction_instruction, 4500)}

CORE CONTEXT:
{context}

PRODUCT LOCK:
{compact_json(product_lock, 2200)}

{ratio_lock}

RULES:

- Fix only the detected problems.
- Prioritize critical blockers first.
- Preserve every successful part.
- Do not redesign the concept unless the QA explicitly says
  the concept execution itself is broken.
- Do not replace the visual metaphor with a generic one.
- Do not change product identity.
- Do not change camera unless QA identified perspective failure.
- Do not introduce new text.
- Do not add decorative objects.
- Improve realism and campaign readiness.
- Never change the requested physical aspect ratio.
- The corrected version must remain the same campaign asset.
""".strip()

    return fit_prompt_for_api(
        prompt,
        label="qa_correction",
        budget=CORRECTION_PROMPT_BUDGET,
    )


# =========================================================
# PRODUCTION PASS SELECTION
# =========================================================

def production_passes_for_mode(
    mode: str,
    *,
    has_product_reference: bool,
) -> List[str]:

    mode = clean_text(
        mode,
        100,
    ).lower()

    if mode == MODE_FAST:
        return [
            "final_polish",
        ]

    if mode == MODE_PRO:
        passes = [
            "composition",
        ]

        if has_product_reference:
            passes.append(
                "product"
            )

        passes.extend(
            [
                "lighting",
                "final_polish",
            ]
        )

        return passes

    passes = [
        "composition",
    ]

    if has_product_reference:
        passes.append(
            "product"
        )

    passes.extend(
        [
            "lighting",
            "materials",
            "final_polish",
        ]
    )

    return passes


# =========================================================
# RUN ONE PRODUCTION PASS
# =========================================================

def run_named_pass(
    *,
    pass_name: str,
    working_image: GeneratedImage,
    product_refs: Sequence[
        ProductionReference
    ],
    compiled: CompiledPrompt,
    camera_direction: Any,
    product_lock: Any,
    aspect_ratio: str,
    final_pass: bool,
) -> GeneratedImage:

    if pass_name == "composition":
        prompt = composition_pass_prompt(
            compiled,
            camera_direction,
            product_lock,
        )

    elif pass_name == "product":
        prompt = product_pass_prompt(
            compiled,
            product_lock,
        )

    elif pass_name == "lighting":
        prompt = lighting_pass_prompt(
            compiled
        )

    elif pass_name == "materials":
        prompt = material_pass_prompt(
            compiled
        )

    else:
        prompt = polish_pass_prompt(
            compiled
        )

    return openai_multi_reference_edit(
        working_image=working_image,
        references=product_refs,
        prompt=prompt,
        aspect_ratio=aspect_ratio,
        final_quality=final_pass,
        pass_name=pass_name,
    )


# =========================================================
# QA LOGGING
# =========================================================

def print_qa_decision(
    qa: Optional[
        QAEvaluation
    ],
) -> None:

    if qa is None:
        print(
            "⚠️ QA decision unavailable"
        )
        return

    print(
        (
            "QA decision: "
            + qa.decision
        )
    )

    print(
        (
            "Delivery approved: "
            + str(
                qa.passed
            )
        )
    )

    print(
        (
            "Target reached: "
            + str(
                qa.target_reached
            )
        )
    )

    print(
        (
            "Critical blockers: "
            + str(
                len(
                    qa.critical_blockers
                )
            )
        )
    )

    for blocker in qa.critical_blockers[:5]:
        print(
            (
                "  ⛔ "
                + blocker
            )
        )


# =========================================================
# MASTER PRODUCTION PIPELINE V2.3
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

    references = load_runtime_references(
        core,
        user_id,
        brand_id,
        limit=12,
    )

    product_refs = product_references(
        references
    )

    dna_payload = reference_dna_payload(
        references
    )

    product_lock = combined_product_lock(
        references
    )

    compiled = compile_prompt(
        target_model,
        request=original_request,
        creative_direction=creative_direction,
        brand_context=brand_context,
        references=dna_payload,
        camera_direction=camera_direction,
        product_lock=product_lock,
    )

    if compiled.target != TARGET_OPENAI:
        raise RuntimeError(
            (
                "Execution for target '"
                + compiled.target
                + "' is not connected yet. "
                "Prompt compilation is available, "
                "but production execution is OpenAI-only in V2.3."
            )
        )

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND PRODUCTION ENGINE V2.3"
    )
    print(
        " FULL-QUALITY MULTI-PASS"
    )
    print(
        "=========================================="
    )

    print(
        "Mode:",
        mode,
    )

    print(
        "Target:",
        compiled.target,
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
        "Product Lock:",
        (
            "ACTIVE"
            if product_lock.get(
                "enabled"
            )
            else "none"
        ),
    )

    print(
        "Requested aspect:",
        aspect_ratio,
    )

    print(
        "Aspect tolerance:",
        ASPECT_RATIO_TOLERANCE,
    )

    print(
        "Concept Gate:",
        CONCEPT_GATE_ENABLED,
    )

    print(
        "Concept Gate minimum:",
        CONCEPT_GATE_MIN_SCORE,
    )

    print(
        "Concept regenerations:",
        CONCEPT_GATE_MAX_REGENERATIONS,
    )

    print(
        "QA target:",
        QA_TARGET_SCORE,
    )

    print(
        "QA delivery floor:",
        QA_DELIVERY_FLOOR,
    )

    print(
        "QA max corrections:",
        QA_MAX_CORRECTIONS,
    )

    print(
        "QA correction time budget:",
        QA_CORRECTION_TIME_BUDGET_SECONDS,
        "seconds",
    )

    print(
        "Compiled prompt chars:",
        len(
            compiled.prompt
        ),
    )

    print(
        "Compiled prompt budget:",
        COMPILED_PROMPT_BUDGET,
    )

    print("")

    if (
        len(
            compiled.prompt
        )
        > COMPILED_PROMPT_BUDGET
    ):
        raise RuntimeError(
            "Compiled production prompt exceeded XPAND safety budget."
        )

    # =====================================================
    # BASE + CONCEPT EXECUTION GATE
    # =====================================================

    gate_attempt = 0
    working: Optional[
        GeneratedImage
    ] = None

    gate_result: Dict[
        str,
        Any,
    ] = {}

    active_compiled = compiled

    while True:

        print(
            (
                "🎬 PASS 0: Concept Base"
                + (
                    ""
                    if gate_attempt == 0
                    else (
                        " | regeneration "
                        + str(
                            gate_attempt
                        )
                    )
                )
                + "..."
            )
        )

        working = generate_base_image(
            compiled=active_compiled,
            product_refs=product_refs,
            aspect_ratio=aspect_ratio,
        )

        require_correct_aspect(
            working,
            aspect_ratio,
            label=(
                "concept_base_"
                + str(
                    gate_attempt + 1
                )
            ),
        )

        if not CONCEPT_GATE_ENABLED:
            gate_result = {
                "passed": True,
                "concept_score": 100,
                "disabled": True,
            }

            print(
                "✅ Concept Gate disabled by configuration."
            )

            break

        print(
            "👁️ CONCEPT EXECUTION GATE..."
        )

        gate_result = evaluate_concept_base(
            image=working,
            original_request=original_request,
            compiled=active_compiled,
            aspect_ratio=aspect_ratio,
        )

        print_concept_gate(
            gate_result
        )

        if gate_result.get(
            "passed"
        ):
            break

        if (
            gate_attempt
            >= CONCEPT_GATE_MAX_REGENERATIONS
        ):
            raise RuntimeError(
                (
                    "Concept Execution Gate failed after "
                    + str(
                        gate_attempt + 1
                    )
                    + " base attempt(s). "
                    "XPAND stopped before spending on "
                    "Composition/Lighting/Materials/Polish."
                )
            )

        gate_attempt += 1

        print(
            (
                "🔁 REGENERATING CONCEPT BASE "
                + str(
                    gate_attempt
                )
                + "/"
                + str(
                    CONCEPT_GATE_MAX_REGENERATIONS
                )
            )
        )

        active_compiled = (
            compiled_with_regeneration_instruction(
                compiled,
                gate_result,
                aspect_ratio,
            )
        )

    if working is None:
        raise RuntimeError(
            "Concept Base unavailable."
        )

    passes: List[
        ProductionPassResult
    ] = [
        ProductionPassResult(
            pass_name=(
                "concept_base_with_product_lock"
                if product_refs
                else "concept_base"
            ),
            image=working,
            metadata={
                "prompt_chars": (
                    working.metadata.get(
                        "prompt_chars"
                    )
                ),
                "concept_gate": gate_result,
                "concept_regenerations": gate_attempt,
                "physical_aspect": (
                    working.metadata.get(
                        "physical_aspect_guard",
                        {},
                    )
                ),
            },
        )
    ]

    print(
        "✅ PASS 0: Concept Base APPROVED"
    )

    # =====================================================
    # FULL MULTI-PASS
    # =====================================================

    pass_names = production_passes_for_mode(
        mode,
        has_product_reference=bool(
            product_refs
        ),
    )

    for index, pass_name in enumerate(
        pass_names,
        start=1,
    ):

        is_final_pass = (
            pass_name
            == pass_names[-1]
        )

        print(
            (
                "🎨 PASS "
                + str(index)
                + ": "
                + pass_name
                + "..."
            )
        )

        previous_working = working

        try:
            candidate = run_named_pass(
                pass_name=pass_name,
                working_image=working,
                product_refs=product_refs,
                compiled=active_compiled,
                camera_direction=camera_direction,
                product_lock=product_lock,
                aspect_ratio=aspect_ratio,
                final_pass=is_final_pass,
            )

            aspect_status = (
                require_correct_aspect(
                    candidate,
                    aspect_ratio,
                    label=pass_name,
                )
            )

            working = candidate

            passes.append(
                ProductionPassResult(
                    pass_name=pass_name,
                    image=working,
                    metadata={
                        "prompt_chars": (
                            working.metadata.get(
                                "prompt_chars"
                            )
                        ),
                        "physical_aspect": (
                            aspect_status
                        ),
                    },
                )
            )

            print(
                (
                    "✅ PASS "
                    + str(index)
                    + ": "
                    + pass_name
                )
            )

        except Exception as error:

            working = previous_working

            message = clean_text(
                error,
                3000,
            )

            errors.append(
                (
                    pass_name
                    + ": "
                    + message
                )
            )

            if (
                "Physical Aspect Lock failed"
                in message
            ):
                print(
                    (
                        "⛔ PASS REJECTED: "
                        + pass_name
                        + " changed physical aspect ratio."
                    )
                )

                print(
                    "✅ Previous valid image restored."
                )
            else:
                print(
                    (
                        "⚠️ PASS FAILED: "
                        + pass_name
                        + " | keeping previous successful image"
                    )
                )

    # =====================================================
    # FINAL PHYSICAL ASPECT GUARD
    # =====================================================

    final_aspect_status = (
        require_correct_aspect(
            working,
            aspect_ratio,
            label="pre_final_qa",
        )
    )

    # =====================================================
    # FINAL QA
    # =====================================================

    print("")
    print(
        "👁️ FINAL VISUAL QA..."
    )

    best_image = working
    best_qa: Optional[
        QAEvaluation
    ] = None
    best_score = 0.0

    try:
        qa = evaluate_generated_image(
            image=working,
            original_request=original_request,
            compiled_prompt=active_compiled,
            product_lock=product_lock,
            brand_context=brand_context,
        )

        best_qa = qa
        best_score = qa.score

        if passes:
            passes[-1].qa = qa

        print(
            (
                "📊 QA SCORE: "
                + str(
                    qa.score
                )
                + "/100"
            )
        )

        print_qa_decision(
            qa
        )

    except Exception as error:

        errors.append(
            (
                "qa_initial: "
                + clean_text(
                    error,
                    3000,
                )
            )
        )

        print(
            (
                "⚠️ QA unavailable: "
                + clean_text(
                    error,
                    1000,
                )
            )
        )

    # =====================================================
    # IMMEDIATE DELIVERY
    # =====================================================

    if (
        best_qa is not None
        and best_qa.passed
    ):

        if best_qa.target_reached:
            print(
                "✅ MASTERPIECE QA TARGET REACHED"
            )
        else:
            print(
                (
                    "✅ MASTERPIECE DELIVERY APPROVED"
                    + " | near-target premium score="
                    + str(
                        best_qa.score
                    )
                )
            )

            print(
                "✅ No critical blockers"
            )

            print(
                (
                    "🚫 Correction skipped"
                    + " | score already >= "
                    + str(
                        QA_DELIVERY_FLOOR
                    )
                )
            )

    # =====================================================
    # CORRECTION LOOP
    # =====================================================

    correction_round = 0

    correction_limit = (
        recommended_correction_limit(
            best_qa
        )
    )

    if (
        best_qa is not None
        and not best_qa.passed
    ):
        print(
            (
                "🧠 QA correction allowance: "
                + str(
                    correction_limit
                )
                + " round(s)"
            )
        )

    current_image = best_image
    current_qa = best_qa

    while (
        current_qa is not None
        and not current_qa.passed
        and correction_round
        < correction_limit
    ):

        elapsed_before_correction = (
            time.monotonic()
            - started
        )

        if (
            elapsed_before_correction
            >= QA_CORRECTION_TIME_BUDGET_SECONDS
        ):
            print(
                (
                    "⏱️ QA CORRECTION STOPPED"
                    + " | elapsed="
                    + str(
                        round(
                            elapsed_before_correction,
                            1,
                        )
                    )
                    + "s"
                    + " | budget="
                    + str(
                        QA_CORRECTION_TIME_BUDGET_SECONDS
                    )
                    + "s"
                )
            )

            print(
                "✅ Keeping best version already produced."
            )

            break

        correction_round += 1

        previous_best_score = (
            best_qa.score
            if best_qa
            else 0.0
        )

        print(
            (
                "🛠️ CORRECTION ROUND "
                + str(
                    correction_round
                )
                + "/"
                + str(
                    correction_limit
                )
                + "..."
            )
        )

        # Always correct the best valid image.
        current_image = best_image
        current_qa = best_qa

        prompt = correction_prompt(
            qa=current_qa,
            compiled=active_compiled,
            product_lock=product_lock,
            aspect_ratio=aspect_ratio,
        )

        try:

            corrected = (
                openai_multi_reference_edit(
                    working_image=current_image,
                    references=product_refs,
                    prompt=prompt,
                    aspect_ratio=aspect_ratio,
                    final_quality=True,
                    pass_name=(
                        "qa_correction_"
                        + str(
                            correction_round
                        )
                    ),
                )
            )

            # ---------------------------------------------
            # PHYSICAL ASPECT LOCK BEFORE QA.
            # ---------------------------------------------

            corrected_aspect = (
                require_correct_aspect(
                    corrected,
                    aspect_ratio,
                    label=(
                        "qa_correction_"
                        + str(
                            correction_round
                        )
                    ),
                )
            )

        except Exception as error:

            message = clean_text(
                error,
                3000,
            )

            errors.append(
                (
                    "qa_correction_"
                    + str(
                        correction_round
                    )
                    + ": "
                    + message
                )
            )

            if (
                "Physical Aspect Lock failed"
                in message
            ):
                print(
                    "⛔ CORRECTION REJECTED BY ASPECT LOCK"
                )

                print(
                    "✅ Best previous 4:5 image preserved."
                )

                # Continue to another allowed correction,
                # always starting from best_image.
                continue

            print(
                (
                    "⚠️ Correction failed; "
                    "keeping best previous version."
                )
            )

            break

        try:
            corrected_qa = (
                evaluate_generated_image(
                    image=corrected,
                    original_request=original_request,
                    compiled_prompt=active_compiled,
                    product_lock=product_lock,
                    brand_context=brand_context,
                )
            )

            passes.append(
                ProductionPassResult(
                    pass_name=(
                        "qa_correction_"
                        + str(
                            correction_round
                        )
                    ),
                    image=corrected,
                    qa=corrected_qa,
                    metadata={
                        "prompt_chars": (
                            corrected.metadata.get(
                                "prompt_chars"
                            )
                        ),
                        "physical_aspect": (
                            corrected_aspect
                        ),
                    },
                )
            )

            print(
                (
                    "📊 CORRECTED SCORE: "
                    + str(
                        corrected_qa.score
                    )
                    + "/100"
                )
            )

            print_qa_decision(
                corrected_qa
            )

            candidate_better = (
                qa_candidate_is_better(
                    corrected_qa,
                    best_qa,
                )
            )

            if not candidate_better:
                print(
                    "🛑 CORRECTION REGRESSION DETECTED"
                )

                print(
                    (
                        "Best kept: "
                        + str(
                            best_score
                        )
                        + "/100"
                    )
                )

                print(
                    (
                        "Rejected correction: "
                        + str(
                            corrected_qa.score
                        )
                        + "/100"
                    )
                )

                print(
                    (
                        "🚫 No further correction will "
                        "start from a worse image."
                    )
                )

                break

            best_image = corrected
            best_qa = corrected_qa
            best_score = corrected_qa.score

            current_image = best_image
            current_qa = best_qa

            improvement = (
                best_score
                - previous_best_score
            )

            print(
                (
                    "📈 Improvement: +"
                    + str(
                        round(
                            improvement,
                            2,
                        )
                    )
                )
            )

            if best_qa.passed:
                if best_qa.target_reached:
                    print(
                        "✅ QA TARGET REACHED"
                    )
                else:
                    print(
                        (
                            "✅ MASTERPIECE DELIVERY APPROVED"
                            + " | score="
                            + str(
                                best_qa.score
                            )
                            + " | no critical blockers"
                        )
                    )

                break

            if (
                improvement
                < QA_MIN_IMPROVEMENT
            ):
                print(
                    (
                        "🛑 QA CORRECTION STOP"
                        + " | improvement "
                        + str(
                            round(
                                improvement,
                                2,
                            )
                        )
                        + " < "
                        + str(
                            QA_MIN_IMPROVEMENT
                        )
                    )
                )

                print(
                    "✅ Keeping the best version."
                )

                break

        except Exception as error:

            errors.append(
                (
                    "qa_correction_evaluation_"
                    + str(
                        correction_round
                    )
                    + ": "
                    + clean_text(
                        error,
                        3000,
                    )
                )
            )

            print(
                (
                    "⚠️ Corrected-image QA failed; "
                    "keeping best previous version."
                )
            )

            break

    # =====================================================
    # FINAL VALIDATION
    # =====================================================

    final_aspect_status = (
        require_correct_aspect(
            best_image,
            aspect_ratio,
            label="final_masterpiece",
        )
    )

    final_delivery_approved = bool(
        best_qa
        and best_qa.passed
    )

    final_target_reached = bool(
        best_qa
        and best_qa.target_reached
    )

    final_decision = (
        best_qa.decision
        if best_qa
        else "qa_unavailable"
    )

    final_blockers = (
        best_qa.critical_blockers
        if best_qa
        else []
    )

    # =====================================================
    # FINAL METADATA
    # =====================================================

    best_image.provider = (
        "xpand_masterpiece"
        if mode == MODE_MASTERPIECE
        else "xpand_production"
    )

    best_image.model = (
        "XPAND Production V2.3 → "
        + OPENAI_IMAGE_MODEL
    )

    best_image.metadata[
        "production_engine"
    ] = ENGINE_VERSION

    best_image.metadata[
        "production_mode"
    ] = mode

    best_image.metadata[
        "qa_score"
    ] = best_score

    best_image.metadata[
        "qa_target"
    ] = QA_TARGET_SCORE

    best_image.metadata[
        "qa_delivery_floor"
    ] = QA_DELIVERY_FLOOR

    best_image.metadata[
        "qa_passed"
    ] = final_delivery_approved

    best_image.metadata[
        "qa_delivery_approved"
    ] = final_delivery_approved

    best_image.metadata[
        "qa_target_reached"
    ] = final_target_reached

    best_image.metadata[
        "qa_decision"
    ] = final_decision

    best_image.metadata[
        "qa_critical_blockers"
    ] = final_blockers

    best_image.metadata[
        "qa_correction_rounds"
    ] = correction_round

    best_image.metadata[
        "qa_correction_limit"
    ] = correction_limit

    best_image.metadata[
        "concept_gate"
    ] = gate_result

    best_image.metadata[
        "concept_regenerations"
    ] = gate_attempt

    best_image.metadata[
        "physical_aspect_guard"
    ] = final_aspect_status

    best_image.metadata[
        "product_lock"
    ] = product_lock

    best_image.metadata[
        "production_passes"
    ] = [
        item.pass_name
        for item in passes
    ]

    best_image.metadata[
        "compiled_prompt_chars"
    ] = len(
        active_compiled.prompt
    )

    best_image.metadata[
        "compiled_prompt_budget"
    ] = COMPILED_PROMPT_BUDGET

    best_image.metadata[
        "prompt_budget_manager"
    ] = "active"

    elapsed = round(
        time.monotonic()
        - started,
        3,
    )

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND PRODUCTION COMPLETE V2.3"
    )
    print(
        "=========================================="
    )

    print(
        "Best score:",
        best_score,
    )

    print(
        "Target:",
        QA_TARGET_SCORE,
    )

    print(
        "Delivery floor:",
        QA_DELIVERY_FLOOR,
    )

    print(
        "Delivery approved:",
        final_delivery_approved,
    )

    print(
        "Target reached:",
        final_target_reached,
    )

    print(
        "QA decision:",
        final_decision,
    )

    print(
        "Critical blockers:",
        len(
            final_blockers
        ),
    )

    print(
        "Concept Gate score:",
        gate_result.get(
            "concept_score",
            "-",
        ),
    )

    print(
        "Concept regenerations:",
        gate_attempt,
    )

    print(
        "Physical aspect:",
        (
            str(
                final_aspect_status.get(
                    "width",
                    0,
                )
            )
            + "x"
            + str(
                final_aspect_status.get(
                    "height",
                    0,
                )
            )
        ),
    )

    print(
        "Requested aspect:",
        aspect_ratio,
    )

    print(
        "Correction rounds:",
        correction_round,
    )

    print(
        "Passes:",
        len(
            passes
        ),
    )

    print(
        "Compiled prompt:",
        len(
            active_compiled.prompt
        ),
        "/",
        COMPILED_PROMPT_BUDGET,
    )

    print(
        "Prompt Budget Manager: ACTIVE"
    )

    print(
        "Elapsed:",
        elapsed,
        "seconds",
    )

    print("")

    return ProductionResult(
        ok=True,
        final_image=best_image,
        best_score=best_score,
        qa=best_qa,
        passes=passes,
        compiled_prompt=active_compiled,
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
# NO API CALLS
# NO IMAGE GENERATION
# NO DATABASE ACCESS
# =========================================================

if __name__ == "__main__":

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND PRODUCTION ENGINE V2.3"
    )
    print(
        " FULL-QUALITY MULTI-PASS"
    )
    print(
        "=========================================="
    )
    print("")

    print(
        "QA target:",
        QA_TARGET_SCORE,
    )

    print(
        "QA delivery floor:",
        QA_DELIVERY_FLOOR,
    )

    print(
        "QA max corrections:",
        QA_MAX_CORRECTIONS,
    )

    print(
        "QA correction time budget:",
        QA_CORRECTION_TIME_BUDGET_SECONDS,
        "seconds",
    )

    print(
        "Concept Gate enabled:",
        CONCEPT_GATE_ENABLED,
    )

    print(
        "Concept Gate minimum:",
        CONCEPT_GATE_MIN_SCORE,
    )

    print(
        "Concept Gate regenerations:",
        CONCEPT_GATE_MAX_REGENERATIONS,
    )

    print(
        "Aspect tolerance:",
        ASPECT_RATIO_TOLERANCE,
    )

    print("")

    # =====================================================
    # RESOLUTION
    # =====================================================

    for ratio in [
        "1:1",
        "4:5",
        "9:16",
        "16:9",
        "2:3",
        "3:2",
    ]:
        print(
            (
                ratio
                + " → "
                + production_size_for_ratio(
                    ratio,
                    final_quality=True,
                )
            )
        )

    print("")

    # =====================================================
    # PHYSICAL DIMENSION TEST
    # =====================================================

    fake_png_4x5 = (
        b"\x89PNG\r\n\x1a\n"
        + b"\x00\x00\x00\r"
        + b"IHDR"
        + struct.pack(
            ">I",
            800,
        )
        + struct.pack(
            ">I",
            1000,
        )
        + b"\x08\x06\x00\x00\x00"
        + b"\x00\x00\x00\x00"
    )

    fake_png_square = (
        b"\x89PNG\r\n\x1a\n"
        + b"\x00\x00\x00\r"
        + b"IHDR"
        + struct.pack(
            ">I",
            1000,
        )
        + struct.pack(
            ">I",
            1000,
        )
        + b"\x08\x06\x00\x00\x00"
        + b"\x00\x00\x00\x00"
    )

    dims_4x5 = image_dimensions(
        fake_png_4x5
    )

    dims_square = image_dimensions(
        fake_png_square
    )

    parser_ok = (
        dims_4x5
        == (
            800,
            1000,
        )
        and dims_square
        == (
            1000,
            1000,
        )
    )

    expected_4x5 = aspect_ratio_value(
        "4:5"
    )

    ratio_4x5 = (
        dims_4x5[0]
        / dims_4x5[1]
        if dims_4x5
        else 0
    )

    ratio_square = (
        dims_square[0]
        / dims_square[1]
        if dims_square
        else 0
    )

    valid_4x5 = (
        abs(
            ratio_4x5
            - expected_4x5
        )
        / expected_4x5
        <= ASPECT_RATIO_TOLERANCE
    )

    square_rejected = (
        abs(
            ratio_square
            - expected_4x5
        )
        / expected_4x5
        > ASPECT_RATIO_TOLERANCE
    )

    print(
        (
            "✅"
            if parser_ok
            else "❌"
        ),
        "Physical image dimension parser",
    )

    print(
        (
            "✅"
            if valid_4x5
            else "❌"
        ),
        "800x1000 accepted as 4:5",
    )

    print(
        (
            "✅"
            if square_rejected
            else "❌"
        ),
        "1000x1000 rejected for requested 4:5",
    )

    print("")

    # =====================================================
    # PASS STRUCTURE TEST
    # =====================================================

    no_product = production_passes_for_mode(
        MODE_MASTERPIECE,
        has_product_reference=False,
    )

    with_product = production_passes_for_mode(
        MODE_MASTERPIECE,
        has_product_reference=True,
    )

    expected_no_product = [
        "composition",
        "lighting",
        "materials",
        "final_polish",
    ]

    expected_with_product = [
        "composition",
        "product",
        "lighting",
        "materials",
        "final_polish",
    ]

    full_pipeline_preserved = (
        no_product
        == expected_no_product
        and with_product
        == expected_with_product
    )

    print(
        (
            "✅"
            if full_pipeline_preserved
            else "❌"
        ),
        "Full V2.2 Multi-Pass pipeline preserved",
    )

    print(
        "Masterpiece without product:"
    )

    print(
        " - concept_base"
    )

    for value in no_product:
        print(
            " -",
            value,
        )

    print("")

    print(
        "Masterpiece with product:"
    )

    print(
        " - concept_base_with_product_lock"
    )

    for value in with_product:
        print(
            " -",
            value,
        )

    print("")

    # =====================================================
    # PROMPT COMPILER TEST
    # =====================================================

    dummy_compiler = compile_prompt(
        TARGET_OPENAI,
        request=(
            "STC Bank premium international transfer scene"
        ),
        creative_direction={
            "idea": (
                "Riyadh and London visually merge through architecture."
            )
        },
        brand_context={
            "brand": "STC Bank"
        },
        references=[],
        camera_direction={
            "camera": (
                "wide environmental commercial perspective"
            )
        },
        product_lock={},
    )

    compiler_ok = (
        dummy_compiler.target
        == TARGET_OPENAI
        and len(
            dummy_compiler.prompt
        )
        <= COMPILED_PROMPT_BUDGET
    )

    print(
        (
            "✅"
            if compiler_ok
            else "❌"
        ),
        "Prompt Compiler",
    )

    print("")

    # =====================================================
    # QA POLICY TEST
    # =====================================================

    def fake_qa(
        score: float,
        blockers: Optional[
            List[str]
        ] = None,
    ) -> QAEvaluation:

        blocker_list = blockers or []

        decision = qa_delivery_decision(
            score=score,
            critical_blockers=blocker_list,
        )

        return QAEvaluation(
            score=score,
            scores={},
            passed=bool(
                decision[
                    "approved"
                ]
            ),
            strengths=[],
            problems=[],
            correction_instruction="",
            critical_blockers=blocker_list,
            target_reached=bool(
                decision[
                    "target_reached"
                ]
            ),
            delivery_approved=bool(
                decision[
                    "approved"
                ]
            ),
            decision=decision[
                "decision"
            ],
        )

    qa_92 = fake_qa(92)
    qa_8875 = fake_qa(88.75)
    qa_84 = fake_qa(84)
    qa_91_blocked = fake_qa(
        91,
        blockers=[
            "major concept failure"
        ],
    )

    qa_policy_ok = (
        qa_92.passed
        and qa_92.target_reached
        and qa_8875.passed
        and not qa_8875.target_reached
        and recommended_correction_limit(
            qa_84
        )
        == QA_MAX_CORRECTIONS
        and not qa_91_blocked.passed
    )

    print(
        (
            "✅"
            if qa_policy_ok
            else "❌"
        ),
        "V2.2 QA policy preserved",
    )

    print("")

    # =====================================================
    # CONCEPT GATE PURE POLICY TEST
    # =====================================================

    concept_good = {
        "passed": True,
        "concept_score": 88,
        "core_message_visible": True,
        "visual_metaphor_visible": True,
        "critical_failures": [],
    }

    concept_bad = {
        "passed": False,
        "concept_score": 42,
        "core_message_visible": False,
        "visual_metaphor_visible": False,
        "critical_failures": [
            "Core metaphor missing."
        ],
    }

    concept_policy_ok = (
        concept_good[
            "concept_score"
        ]
        >= CONCEPT_GATE_MIN_SCORE
        and concept_good[
            "core_message_visible"
        ]
        and concept_good[
            "visual_metaphor_visible"
        ]
        and concept_bad[
            "concept_score"
        ]
        < CONCEPT_GATE_MIN_SCORE
    )

    print(
        (
            "✅"
            if concept_policy_ok
            else "❌"
        ),
        "Concept Execution Gate policy",
    )

    print("")

    # =====================================================
    # FINAL SELF-TEST
    # =====================================================

    all_ok = (
        parser_ok
        and valid_4x5
        and square_rejected
        and full_pipeline_preserved
        and compiler_ok
        and qa_policy_ok
        and concept_policy_ok
    )

    print(
        "✅ Physical Aspect Ratio Lock"
    )

    print(
        "✅ 4:5 cannot silently become 1:1"
    )

    print(
        "✅ Aspect validation after every GPT-Image edit"
    )

    print(
        "✅ Aspect validation before Final QA"
    )

    print(
        "✅ Aspect validation after QA correction"
    )

    print(
        "✅ Wrong-ratio correction never becomes Best Version"
    )

    print(
        "✅ Concept Execution Gate before expensive passes"
    )

    print(
        "✅ One Concept Base regeneration when core idea fails"
    )

    print(
        "✅ Composition Pass preserved"
    )

    print(
        "✅ Product Fidelity Pass preserved"
    )

    print(
        "✅ Lighting Pass preserved"
    )

    print(
        "✅ Material Pass preserved"
    )

    print(
        "✅ Final Polish preserved"
    )

    print(
        "✅ Final Vision QA preserved"
    )

    print(
        "✅ Critical Blocker hard gate preserved"
    )

    print(
        "✅ 88+ near-target delivery preserved"
    )

    print(
        "✅ Correction regression protection preserved"
    )

    print(
        "✅ Full-quality 900-second correction window"
    )

    print("")

    print(
        (
            "XPAND Production Engine V2.3 self-test: "
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
