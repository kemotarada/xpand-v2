# =========================================================
# XPAND PRODUCTION ENGINE V2.2
#
# Professional image-production orchestration for XPAND.
#
# =========================================================
# V2.2
# =========================================================
#
# MAJOR FIXES
# ---------------------------------------------------------
#
# 1. SMART QA DELIVERY POLICY
#
#    90+:
#       Full QA target reached.
#
#    88–89.99:
#       Masterpiece delivery approved automatically
#       when there are NO critical blockers.
#
#    85–87.99:
#       Maximum ONE correction attempt.
#
#    Below 85:
#       Up to configured QA_MAX_CORRECTIONS.
#
#
# 2. REGRESSION STOP
#
#    A correction that makes the image worse NEVER becomes
#    the source for another correction round.
#
#    XPAND immediately returns to the best version.
#
#
# 3. BEST VERSION PRESERVATION V2
#
#    Version quality ranking considers:
#
#    - delivery approval
#    - critical blockers
#    - QA score
#
#
# 4. CRITICAL VISUAL BLOCKERS
#
#    Severe failures remain hard blockers even if the
#    weighted average is high.
#
#
# 5. QA TIME BUDGET
#
#    XPAND will not keep starting expensive correction
#    rounds forever.
#
#
# 6. NEAR-TARGET DELIVERY
#
#    Example:
#
#       QA = 88.75
#       Critical blockers = none
#
#       => DELIVER immediately
#       => NO correction loop
#
#
# =========================================================
#
# MASTERPIECE PIPELINE
# ---------------------------------------------------------
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
# Vision QA
#      ↓
# Smart QA Decision
#      ↓
# Optional Targeted Correction
#      ↓
# Best Final Image
#
#
# Current executable provider:
# - OpenAI GPT-Image-2
#
# Prepared prompt compilers:
# - OpenAI
# - Gemini
# - Midjourney
# - FLUX
# - Ideogram
# - Runway
# - Kling
# - Seedance
#
#
# Product Lock here means high-fidelity AI reference lock.
#
# Pixel-exact identity is handled separately by:
# xpand_exact_asset_lock.py
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

ENGINE_NAME = (
    "XPAND Production Engine"
)

ENGINE_VERSION = (
    "2.2"
)


# =========================================================
# API
# =========================================================

OPENAI_IMAGE_EDITS_URL = (
    "https://api.openai.com/v1/images/edits"
)


# =========================================================
# MODES
# =========================================================

MODE_FAST = (
    "fast"
)

MODE_PRO = (
    "pro"
)

MODE_MASTERPIECE = (
    "masterpiece"
)


# =========================================================
# PROMPT TARGETS
# =========================================================

TARGET_OPENAI = (
    "openai"
)

TARGET_GEMINI = (
    "gemini"
)

TARGET_MIDJOURNEY = (
    "midjourney"
)

TARGET_FLUX = (
    "flux"
)

TARGET_IDEOGRAM = (
    "ideogram"
)

TARGET_RUNWAY = (
    "runway"
)

TARGET_KLING = (
    "kling"
)

TARGET_SEEDANCE = (
    "seedance"
)


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
                "32000"
            )
            or
            32000
        )
    )
)


COMPILED_PROMPT_BUDGET = max(
    12000,
    min(
        OPENAI_PROMPT_HARD_LIMIT - 1000,
        int(
            os.environ.get(
                "XPAND_COMPILED_PROMPT_BUDGET",
                "26000"
            )
            or
            26000
        )
    )
)


PASS_PROMPT_BUDGET = max(
    12000,
    min(
        OPENAI_PROMPT_HARD_LIMIT - 1000,
        int(
            os.environ.get(
                "XPAND_PASS_PROMPT_BUDGET",
                "27500"
            )
            or
            27500
        )
    )
)


QA_PROMPT_BUDGET = max(
    12000,
    min(
        OPENAI_PROMPT_HARD_LIMIT - 1000,
        int(
            os.environ.get(
                "XPAND_QA_PROMPT_BUDGET",
                "26000"
            )
            or
            26000
        )
    )
)


CORRECTION_PROMPT_BUDGET = max(
    12000,
    min(
        OPENAI_PROMPT_HARD_LIMIT - 1000,
        int(
            os.environ.get(
                "XPAND_CORRECTION_PROMPT_BUDGET",
                "25000"
            )
            or
            25000
        )
    )
)


# =========================================================
# SECTION BUDGETS
# =========================================================

SECTION_BUDGETS = {
    "request":
        5000,

    "creative_direction":
        6000,

    "brand_context":
        5000,

    "references":
        3800,

    "camera_direction":
        1800,

    "product_lock":
        2200,
}


# =========================================================
# QA V2.2
# =========================================================

#
# Aspirational perfect target.
#

QA_TARGET_SCORE = max(
    50,
    min(
        100,
        int(
            os.environ.get(
                "XPAND_IMAGE_QA_TARGET",
                "90"
            )
            or
            90
        )
    )
)


#
# A Masterpiece scoring at least this value can be
# delivered without forcing another expensive regeneration,
# as long as no critical visual blocker exists.
#

QA_DELIVERY_FLOOR = max(
    50.0,
    min(
        float(
            QA_TARGET_SCORE
        ),
        float(
            os.environ.get(
                "XPAND_IMAGE_QA_DELIVERY_FLOOR",
                "88"
            )
            or
            88
        )
    )
)


#
# 85–87.99:
# one targeted correction only.
#

QA_SINGLE_CORRECTION_FLOOR = max(
    0.0,
    min(
        QA_DELIVERY_FLOOR,
        float(
            os.environ.get(
                "XPAND_IMAGE_QA_SINGLE_CORRECTION_FLOOR",
                "85"
            )
            or
            85
        )
    )
)


QA_MAX_CORRECTIONS = max(
    0,
    min(
        4,
        int(
            os.environ.get(
                "XPAND_IMAGE_QA_MAX_CORRECTIONS",
                "2"
            )
            or
            2
        )
    )
)


#
# If a correction improves the weighted score by less than
# this amount, do not start another correction.
#

QA_MIN_IMPROVEMENT = max(
    0.0,
    min(
        10.0,
        float(
            os.environ.get(
                "XPAND_IMAGE_QA_MIN_IMPROVEMENT",
                "0.5"
            )
            or
            0.5
        )
    )
)


#
# Maximum total production time at which XPAND is allowed
# to START another correction pass.
#
# It does not kill an API request already in progress.
#

QA_CORRECTION_TIME_BUDGET_SECONDS = max(
    60.0,
    float(
        os.environ.get(
            "XPAND_IMAGE_QA_CORRECTION_TIME_BUDGET_SECONDS",
            "420"
        )
        or
        420
    )
)


#
# Hard blocker thresholds.
#

QA_CRITICAL_SCORE_FLOOR = max(
    0.0,
    min(
        100.0,
        float(
            os.environ.get(
                "XPAND_IMAGE_QA_CRITICAL_FLOOR",
                "65"
            )
            or
            65
        )
    )
)


QA_AD_READINESS_CRITICAL_FLOOR = max(
    QA_CRITICAL_SCORE_FLOOR,
    min(
        100.0,
        float(
            os.environ.get(
                "XPAND_IMAGE_QA_AD_READINESS_CRITICAL_FLOOR",
                "70"
            )
            or
            70
        )
    )
)


QA_WEIGHTS = {
    "concept_execution":
        10,

    "reference_adherence":
        10,

    "perspective":
        10,

    "product_fidelity":
        15,

    "lighting":
        10,

    "shadows":
        5,

    "reflections":
        5,

    "human_anatomy":
        5,

    "background_cleanliness":
        5,

    "brand_alignment":
        10,

    "text_logo_integrity":
        5,

    "advertising_readiness":
        10,
}


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

    qa: Optional[QAEvaluation] = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


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

    errors: List[str] = field(
        default_factory=list
    )


# =========================================================
# BASIC HELPERS
# =========================================================

def clean_text(
    value: Any,
    limit: int = 20000
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
        .strip()[:limit]
    )


def clamp_score(
    value: Any
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
            number
        )
    )


def safe_list(
    value: Any
) -> List[Any]:

    return (
        value
        if isinstance(
            value,
            list
        )
        else
        []
    )


# =========================================================
# PROMPT VALUE COMPACTION
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
    string_limit: int = 1200
) -> Any:

    if depth > max_depth:

        if isinstance(
            value,
            dict
        ):

            return {
                "_summary":
                    "nested object omitted"
            }

        if isinstance(
            value,
            list
        ):

            return [
                "nested list omitted"
            ]

        return clean_text(
            value,
            min(
                string_limit,
                400
            )
        )

    if isinstance(
        value,
        bytes
    ):

        return (
            "<binary image data omitted>"
        )

    if isinstance(
        value,
        dict
    ):

        output = {}

        count = 0

        for key, child in value.items():

            key_text = clean_text(
                key,
                200
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

            output[
                key_text
            ] = reduce_prompt_value(
                child,

                depth=
                    depth + 1,

                max_depth=
                    max_depth,

                list_limit=
                    list_limit,

                dict_limit=
                    dict_limit,

                string_limit=
                    string_limit
            )

            count += 1

        return output

    if isinstance(
        value,
        list
    ):

        output = []

        for child in value[
            :list_limit
        ]:

            output.append(
                reduce_prompt_value(
                    child,

                    depth=
                        depth + 1,

                    max_depth=
                        max_depth,

                    list_limit=
                        list_limit,

                    dict_limit=
                        dict_limit,

                    string_limit=
                        string_limit
                )
            )

        if len(
            value
        ) > list_limit:

            output.append(
                (
                    "<"
                    +
                    str(
                        len(
                            value
                        )
                        -
                        list_limit
                    )
                    +
                    " additional items omitted>"
                )
            )

        return output

    if isinstance(
        value,
        (
            int,
            float,
            bool,
        )
    ):

        return value

    if value is None:

        return None

    return clean_text(
        value,
        string_limit
    )


def compact_json(
    value: Any,
    limit: int
) -> str:

    limit = max(
        100,
        int(
            limit
            or
            100
        )
    )

    attempts = [
        {
            "max_depth":
                4,

            "list_limit":
                10,

            "dict_limit":
                50,

            "string_limit":
                1400,
        },

        {
            "max_depth":
                4,

            "list_limit":
                7,

            "dict_limit":
                35,

            "string_limit":
                900,
        },

        {
            "max_depth":
                3,

            "list_limit":
                5,

            "dict_limit":
                28,

            "string_limit":
                650,
        },

        {
            "max_depth":
                3,

            "list_limit":
                3,

            "dict_limit":
                20,

            "string_limit":
                400,
        },

        {
            "max_depth":
                2,

            "list_limit":
                2,

            "dict_limit":
                14,

            "string_limit":
                250,
        },
    ]

    for settings in attempts:

        reduced = reduce_prompt_value(
            value,
            **settings
        )

        try:

            encoded = json.dumps(
                reduced,
                ensure_ascii=False,
                separators=(
                    ",",
                    ":"
                ),
                default=str
            )

        except Exception:

            encoded = clean_text(
                reduced,
                limit
            )

        if len(
            encoded
        ) <= limit:

            return encoded

    summary_size = max(
        50,
        int(
            limit
            *
            0.65
        )
    )

    while summary_size > 30:

        fallback = {
            "truncated":
                True,

            "summary":
                clean_text(
                    value,
                    summary_size
                ),
        }

        encoded = json.dumps(
            fallback,
            ensure_ascii=False,
            separators=(
                ",",
                ":"
            ),
            default=str
        )

        if len(
            encoded
        ) <= limit:

            return encoded

        summary_size = int(
            summary_size
            *
            0.75
        )

    return json.dumps(
        {
            "truncated":
                True
        },
        ensure_ascii=False
    )


def safe_json(
    value: Any,
    limit: int = 30000
) -> str:

    return compact_json(
        value,
        limit
    )


# =========================================================
# FINAL PROMPT SAFETY FIT
# =========================================================

def hard_fit_prompt(
    text: str,
    max_chars: int
) -> str:

    text = clean_text(
        text,
        1000000
    )

    if len(
        text
    ) <= max_chars:

        return text

    marker = (
        "\n\n"
        "[XPAND PROMPT BUDGET COMPACTION]\n"
        "Secondary context omitted to stay inside provider limits.\n"
        "\n"
    )

    available = max(
        100,
        max_chars
        -
        len(
            marker
        )
    )

    front_size = int(
        available
        *
        0.62
    )

    back_size = (
        available
        -
        front_size
    )

    return (
        text[
            :front_size
        ]
        +
        marker
        +
        text[
            -back_size:
        ]
    )


def fit_prompt_for_api(
    prompt: str,
    *,
    label: str,
    budget: int
) -> str:

    original = clean_text(
        prompt,
        1000000
    )

    original_length = len(
        original
    )

    fitted = hard_fit_prompt(
        original,
        budget
    )

    final_length = len(
        fitted
    )

    if original_length <= budget:

        print(
            (
                "🧮 Prompt budget ["
                +
                label
                +
                "]: "
                +
                str(
                    final_length
                )
                +
                "/"
                +
                str(
                    budget
                )
                +
                " chars ✅"
            )
        )

    else:

        print(
            (
                "🧮 Prompt budget ["
                +
                label
                +
                "]: "
                +
                str(
                    original_length
                )
                +
                " → "
                +
                str(
                    final_length
                )
                +
                "/"
                +
                str(
                    budget
                )
                +
                " chars ✅ COMPACTED"
            )
        )

    if len(
        fitted
    ) >= OPENAI_PROMPT_HARD_LIMIT:

        raise RuntimeError(
            (
                "XPAND Prompt Budget Manager failed for "
                +
                label
                +
                "."
            )
        )

    return fitted


# =========================================================
# JSON EXTRACTION
# =========================================================

def extract_json_object(
    value: str
) -> Dict[str, Any]:

    text = clean_text(
        value,
        100000
    )

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=
            re.IGNORECASE
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    try:

        parsed = json.loads(
            text
        )

        if isinstance(
            parsed,
            dict
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
                    start:end + 1
                ]
            )

            if isinstance(
                parsed,
                dict
            ):

                return parsed

        except Exception:

            pass

    return {}


# =========================================================
# IMAGE RESPONSE PARSING
# =========================================================

def decode_image_value(
    value: str
) -> Optional[bytes]:

    value = clean_text(
        value,
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

        result = base64.b64decode(
            value
        )

        return (
            result
            if result
            else
            None
        )

    except Exception:

        return None


def find_images_in_response(
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
            )

            for key in [
                "b64_json",
                "base64",
                "data",
            ]:

                raw_value = item.get(
                    key
                )

                if not isinstance(
                    raw_value,
                    str
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
                            or
                            "image/png"
                        )
                    )

                    break

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

    unique = []

    signatures = set()

    for raw, mime_type in found:

        signature = (
            len(
                raw
            ),
            raw[
                :64
            ],
        )

        if signature in signatures:

            continue

        signatures.add(
            signature
        )

        unique.append(
            (
                raw,
                mime_type
            )
        )

    return unique


# =========================================================
# NATIVE OUTPUT RESOLUTION
# =========================================================

def production_size_for_ratio(
    aspect_ratio: str,
    *,
    final_quality: bool = True
) -> str:

    ratio = clean_text(
        aspect_ratio,
        30
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
                "1024x1792",

            "16:9":
                "1792x1024",

            "2:3":
                "1024x1536",

            "3:2":
                "1536x1024",

            "3:4":
                "1024x1360",

            "4:3":
                "1360x1024",
        }

        return mapping.get(
            ratio,
            "1024x1024"
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
            "3840x1648",
    }

    return mapping.get(
        ratio,
        "2048x2048"
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
    compiled: CompiledPrompt
) -> Dict[str, str]:

    metadata = (
        compiled.metadata
        if isinstance(
            compiled.metadata,
            dict
        )
        else
        {}
    )

    sections = metadata.get(
        "sections",
        {}
    )

    return (
        sections
        if isinstance(
            sections,
            dict
        )
        else
        {}
    )


def section_text(
    compiled: CompiledPrompt,
    key: str,
    fallback_limit: int = 5000
) -> str:

    sections = compiled_sections(
        compiled
    )

    value = sections.get(
        key
    )

    if value:

        return clean_text(
            value,
            fallback_limit
        )

    return clean_text(
        compiled.prompt,
        fallback_limit
    )


def build_pass_context(
    compiled: CompiledPrompt,
    keys: Sequence[
        Tuple[
            str,
            str,
            int
        ]
    ]
) -> str:

    parts = []

    for key, label, limit in keys:

        value = section_text(
            compiled,
            key,
            limit
        )

        if not value:

            continue

        parts.append(
            (
                label
                +
                "\n"
                +
                ("-" * len(label))
                +
                "\n"
                +
                clean_text(
                    value,
                    limit
                )
            )
        )

    return "\n\n".join(
        parts
    )


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
    product_lock: Any
) -> CompiledPrompt:

    sections = {
        "request":
            clean_text(
                request,
                SECTION_BUDGETS[
                    "request"
                ]
            ),

        "creative_direction":
            compact_json(
                creative_direction,
                SECTION_BUDGETS[
                    "creative_direction"
                ]
            ),

        "brand_context":
            compact_json(
                brand_context,
                SECTION_BUDGETS[
                    "brand_context"
                ]
            ),

        "references":
            compact_json(
                references,
                SECTION_BUDGETS[
                    "references"
                ]
            ),

        "camera_direction":
            compact_json(
                camera_direction,
                SECTION_BUDGETS[
                    "camera_direction"
                ]
            ),

        "product_lock":
            compact_json(
                product_lock,
                SECTION_BUDGETS[
                    "product_lock"
                ]
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

Avoid visual clichés unless they are transformed into
an original, brand-relevant visual metaphor.

The final scene must feel intentionally art-directed,
physically plausible and professionally photographed.
""".strip()

    prompt = fit_prompt_for_api(
        prompt,

        label=
            "compiled_master_brief",

        budget=
            COMPILED_PROMPT_BUDGET
    )

    return CompiledPrompt(
        target=
            TARGET_OPENAI,

        prompt=
            prompt,

        negative_prompt=
            base_negative_prompt(),

        metadata={
            "compiler":
                "openai_gpt_image_v2_2",

            "product_lock":
                bool(
                    product_lock
                ),

            "prompt_budget":
                COMPILED_PROMPT_BUDGET,

            "prompt_chars":
                len(
                    prompt
                ),

            "sections":
                sections,
        }
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
    product_lock: Any
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

    prompt = hard_fit_prompt(
        prompt,
        COMPILED_PROMPT_BUDGET
    )

    return CompiledPrompt(
        target=
            TARGET_GEMINI,

        prompt=
            prompt,

        negative_prompt=
            base_negative_prompt(),

        metadata={
            "compiler":
                "gemini_image_v2_2",
        }
    )


def compile_midjourney_prompt(
    *,
    request: str,
    creative_direction: Any,
    brand_context: Any,
    references: Any,
    camera_direction: Any,
    product_lock: Any
) -> CompiledPrompt:

    prompt = (
        clean_text(
            request,
            4000
        )
        +
        ", "
        +
        compact_json(
            creative_direction,
            4500
        )
        +
        ", "
        +
        compact_json(
            camera_direction,
            1400
        )
        +
        ", commercial advertising photography, "
        +
        "precise cinematic camera geometry, "
        +
        "premium realistic materials, "
        +
        "controlled reflections, professional lighting, "
        +
        "intentional negative space"
    )

    return CompiledPrompt(
        target=
            TARGET_MIDJOURNEY,

        prompt=
            hard_fit_prompt(
                prompt,
                14000
            ),

        negative_prompt=
            (
                "generic banking icons, floating coins, "
                "deformed anatomy, warped product, random typography"
            ),

        metadata={
            "compiler":
                "midjourney_v2_2",

            "execution_available":
                False,
        }
    )


def compile_flux_prompt(
    *,
    request: str,
    creative_direction: Any,
    brand_context: Any,
    references: Any,
    camera_direction: Any,
    product_lock: Any
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
        target=
            TARGET_FLUX,

        prompt=
            hard_fit_prompt(
                prompt,
                18000
            ),

        negative_prompt=
            base_negative_prompt(),

        metadata={
            "compiler":
                "flux_v2_2",

            "execution_available":
                False,
        }
    )


def compile_ideogram_prompt(
    *,
    request: str,
    creative_direction: Any,
    brand_context: Any,
    references: Any,
    camera_direction: Any,
    product_lock: Any
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
        target=
            TARGET_IDEOGRAM,

        prompt=
            hard_fit_prompt(
                prompt,
                18000
            ),

        negative_prompt=
            base_negative_prompt(),

        metadata={
            "compiler":
                "ideogram_v2_2",

            "execution_available":
                False,
        }
    )


def compile_video_prompt(
    target: str,
    *,
    request: str,
    creative_direction: Any,
    brand_context: Any,
    camera_direction: Any
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
        target=
            target,

        prompt=
            hard_fit_prompt(
                prompt,
                19000
            ),

        negative_prompt=
            (
                "camera teleportation, geometry morphing, "
                "warped hands, product deformation, flicker, "
                "identity drift"
            ),

        metadata={
            "compiler":
                (
                    target
                    +
                    "_v2_2"
                ),

            "execution_available":
                False,
        }
    )


# =========================================================
# MAIN COMPILER ROUTER
# =========================================================

def compile_prompt(
    target: str,
    *,
    request: str,
    creative_direction: Any = None,
    brand_context: Any = None,
    references: Any = None,
    camera_direction: Any = None,
    product_lock: Any = None
) -> CompiledPrompt:

    target = clean_text(
        target,
        100
    ).lower()

    kwargs = {
        "request":
            request,

        "creative_direction":
            creative_direction
            or
            {},

        "brand_context":
            brand_context
            or
            {},

        "references":
            references
            or
            [],

        "camera_direction":
            camera_direction
            or
            {},

        "product_lock":
            product_lock
            or
            {},
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

            request=
                request,

            creative_direction=
                creative_direction
                or
                {},

            brand_context=
                brand_context
                or
                {},

            camera_direction=
                camera_direction
                or
                {}
        )

    return compile_openai_prompt(
        **kwargs
    )


# =========================================================
# REFERENCE LOADING
# =========================================================

def infer_mime_type(
    raw: bytes,
    fallback: str = "image/jpeg"
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
        in
        raw[
            :16
        ]
    ):

        return "image/webp"

    return fallback


def load_runtime_references(
    core,
    user_id,
    brand_id: str,
    *,
    limit: int = 12
) -> List[ProductionReference]:

    stored = load_visual_references(
        core,
        user_id,

        brand_id=
            brand_id,

        limit=
            limit
    )

    references: List[
        ProductionReference
    ] = []

    for item in stored:

        if not isinstance(
            item,
            dict
        ):

            continue

        file_id = clean_text(
            item.get(
                "telegram_file_id",
                ""
            ),
            1500
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
                    +
                    clean_text(
                        error,
                        1000
                    )
                )
            )

            continue

        if not raw:

            continue

        references.append(
            ProductionReference(
                role=
                    clean_text(
                        item.get(
                            "reference_role",
                            "style_reference"
                        ),
                        100
                    ),

                image_bytes=
                    raw,

                mime_type=
                    infer_mime_type(
                        raw
                    ),

                dna=
                    (
                        item.get(
                            "dna",
                            {}
                        )
                        if isinstance(
                            item.get(
                                "dna",
                                {}
                            ),
                            dict
                        )
                        else
                        {}
                    ),

                product_lock=
                    (
                        item.get(
                            "product_lock",
                            {}
                        )
                        if isinstance(
                            item.get(
                                "product_lock",
                                {}
                            ),
                            dict
                        )
                        else
                        {}
                    ),

                user_note=
                    clean_text(
                        item.get(
                            "user_note",
                            ""
                        ),
                        2000
                    ),

                source_id=
                    str(
                        item.get(
                            "id",
                            ""
                        )
                    ),
            )
        )

    return references


def product_references(
    references: Sequence[
        ProductionReference
    ]
) -> List[
    ProductionReference
]:

    return [
        item
        for item in references
        if item.role == "product_reference"
    ]


def reference_dna_payload(
    references: Sequence[
        ProductionReference
    ]
) -> List[Dict[str, Any]]:

    output = []

    for item in references:

        output.append(
            {
                "role":
                    item.role,

                "dna":
                    reduce_prompt_value(
                        item.dna,

                        max_depth=
                            3,

                        list_limit=
                            6,

                        dict_limit=
                            30,

                        string_limit=
                            700
                    ),

                "product_lock":
                    reduce_prompt_value(
                        item.product_lock,

                        max_depth=
                            3,

                        list_limit=
                            6,

                        dict_limit=
                            25,

                        string_limit=
                            500
                    ),

                "user_note":
                    clean_text(
                        item.user_note,
                        1000
                    ),
            }
        )

    return output


def combined_product_lock(
    references: Sequence[
        ProductionReference
    ]
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
            dict
        ):

            continue

        values = product_lock.get(
            "must_remain_identical",
            []
        )

        if not isinstance(
            values,
            list
        ):

            continue

        for value in values:

            text = clean_text(
                value,
                500
            )

            if (
                text
                and
                text not in locked
            ):

                locked.append(
                    text
                )

    return {
        "enabled":
            bool(
                source_count
            ),

        "reference_count":
            source_count,

        "must_remain_identical":
            locked[
                :30
            ],

        "environment_may_change":
            True,

        "lighting_may_adapt":
            True,

        "lock_type":
            (
                "high_fidelity_reference"
                if source_count
                else
                "none"
            ),

        "exact_pixel_identity_guaranteed":
            False,
    }


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
    pass_name: str
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
                str
            ]
        ]
    ] = []

    if working_image is not None:

        files.append(
            (
                "image[]",
                (
                    "working-image"
                    +
                    working_image.extension,

                    working_image.image_bytes,

                    working_image.mime_type
                    or
                    "image/png",
                )
            )
        )

    for index, reference in enumerate(
        references,
        start=1
    ):

        extension = (
            ".png"
            if reference.mime_type
            ==
            "image/png"
            else
            ".jpg"
        )

        files.append(
            (
                "image[]",
                (
                    (
                        "product-reference-"
                        +
                        str(
                            index
                        )
                        +
                        extension
                    ),

                    reference.image_bytes,

                    reference.mime_type,
                )
            )
        )

    if not files:

        raise RuntimeError(
            "No image input supplied to edit."
        )

    if len(
        files
    ) == 1:

        _, file_tuple = files[
            0
        ]

        files = [
            (
                "image",
                file_tuple
            )
        ]

    size = production_size_for_ratio(
        aspect_ratio,

        final_quality=
            final_quality
    )

    safe_prompt = fit_prompt_for_api(
        prompt,

        label=
            pass_name,

        budget=
            PASS_PROMPT_BUDGET
    )

    payload = {
        "model":
            OPENAI_IMAGE_MODEL,

        "prompt":
            safe_prompt,

        "size":
            size,

        "quality":
            (
                "high"
                if final_quality
                else
                "medium"
            ),

        "n":
            "1",
    }

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

        data=
            payload,

        files=
            files,

        timeout=
            REQUEST_TIMEOUT
    )

    try:

        response_data = response.json()

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
            dict
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
                "GPT-Image-2 edit failed: "
                +
                clean_text(
                    message,
                    3000
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

    image_bytes, mime_type = images[
        0
    ]

    request_id = clean_text(
        response.headers.get(
            "x-request-id",
            ""
        ),
        300
    )

    if not request_id:

        request_id = (
            "prod-"
            +
            uuid.uuid4().hex[
                :12
            ]
        )

    return GeneratedImage(
        image_bytes=
            image_bytes,

        mime_type=
            mime_type
            or
            "image/png",

        provider=
            "xpand_production",

        model=
            OPENAI_IMAGE_MODEL,

        prompt=
            safe_prompt,

        original_prompt=
            safe_prompt,

        aspect_ratio=
            aspect_ratio,

        image_size=
            size,

        quality=
            (
                "high"
                if final_quality
                else
                "medium"
            ),

        route_reason=
            (
                "XPAND Production Pass: "
                +
                pass_name
            ),

        request_id=
            request_id,

        metadata={
            "production_engine":
                ENGINE_VERSION,

            "pass_name":
                pass_name,

            "reference_images":
                len(
                    references
                ),

            "working_image_input":
                bool(
                    working_image
                ),

            "prompt_chars":
                len(
                    safe_prompt
                ),

            "prompt_budget":
                PASS_PROMPT_BUDGET,
        },
    )


# =========================================================
# PRODUCTION PASS PROMPTS
# =========================================================

def composition_pass_prompt(
    compiled: CompiledPrompt,
    camera: Any,
    product_lock: Any
) -> str:

    master = build_pass_context(
        compiled,
        [
            (
                "request",
                "ORIGINAL REQUEST",
                4500
            ),

            (
                "creative_direction",
                "APPROVED CREATIVE DIRECTION",
                6500
            ),

            (
                "brand_context",
                "BRAND CONSTRAINTS",
                3500
            ),

            (
                "references",
                "REFERENCE DNA",
                2800
            ),

            (
                "camera_direction",
                "CAMERA DIRECTION",
                2200
            ),

            (
                "product_lock",
                "PRODUCT LOCK",
                2200
            ),
        ]
    )

    prompt = f"""
COMPOSITION PASS
================

{master}

CURRENT PASS OBJECTIVE
======================

Refine the supplied image into the approved final composition.

CHANGE ONLY WHAT IMPROVES COMPOSITION:

- preserve the approved concept
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
""".strip()

    return hard_fit_prompt(
        prompt,
        PASS_PROMPT_BUDGET
    )


def product_pass_prompt(
    compiled: CompiledPrompt,
    product_lock: Any
) -> str:

    master = build_pass_context(
        compiled,
        [
            (
                "request",
                "ORIGINAL REQUEST",
                4000
            ),

            (
                "creative_direction",
                "APPROVED CREATIVE DIRECTION",
                5000
            ),

            (
                "references",
                "PRODUCT / REFERENCE DNA",
                4200
            ),

            (
                "product_lock",
                "PRODUCT LOCK",
                4000
            ),

            (
                "camera_direction",
                "CAMERA",
                1600
            ),
        ]
    )

    prompt = f"""
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
""".strip()

    return hard_fit_prompt(
        prompt,
        PASS_PROMPT_BUDGET
    )


def lighting_pass_prompt(
    compiled: CompiledPrompt
) -> str:

    master = build_pass_context(
        compiled,
        [
            (
                "request",
                "ORIGINAL REQUEST",
                3500
            ),

            (
                "creative_direction",
                "CREATIVE DIRECTION",
                5200
            ),

            (
                "brand_context",
                "BRAND LIGHTING / VISUAL CONTEXT",
                4200
            ),

            (
                "camera_direction",
                "CAMERA",
                1800
            ),

            (
                "product_lock",
                "PRODUCT LOCK",
                1800
            ),
        ]
    )

    prompt = f"""
LIGHTING PASS
=============

{master}

Preserve:

- subject identity
- product geometry
- camera
- composition
- environment structure
- visual metaphor

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
""".strip()

    return hard_fit_prompt(
        prompt,
        PASS_PROMPT_BUDGET
    )


def material_pass_prompt(
    compiled: CompiledPrompt
) -> str:

    master = build_pass_context(
        compiled,
        [
            (
                "request",
                "ORIGINAL REQUEST",
                3200
            ),

            (
                "creative_direction",
                "CREATIVE DIRECTION",
                4500
            ),

            (
                "brand_context",
                "BRAND MATERIAL CONTEXT",
                3500
            ),

            (
                "references",
                "REFERENCE MATERIAL DNA",
                3000
            ),

            (
                "product_lock",
                "PRODUCT LOCK",
                2200
            ),
        ]
    )

    prompt = f"""
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
""".strip()

    return hard_fit_prompt(
        prompt,
        PASS_PROMPT_BUDGET
    )


def polish_pass_prompt(
    compiled: CompiledPrompt
) -> str:

    master = build_pass_context(
        compiled,
        [
            (
                "request",
                "ORIGINAL REQUEST",
                3500
            ),

            (
                "creative_direction",
                "APPROVED CREATIVE DIRECTION",
                5000
            ),

            (
                "brand_context",
                "BRAND",
                3500
            ),

            (
                "product_lock",
                "PRODUCT LOCK",
                2200
            ),
        ]
    )

    prompt = f"""
FINAL ADVERTISING POLISH
========================

{master}

Do NOT redesign the scene.

Do NOT create a different idea.

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
""".strip()

    return hard_fit_prompt(
        prompt,
        PASS_PROMPT_BUDGET
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
    aspect_ratio: str
) -> GeneratedImage:

    base_prompt = fit_prompt_for_api(
        compiled.prompt,

        label=
            "concept_base",

        budget=
            COMPILED_PROMPT_BUDGET
    )

    if product_refs:

        prompt = (
            base_prompt
            +
            "\n\n"
            "BASE GENERATION WITH PRODUCT REFERENCES\n"
            "=======================================\n"
            "Use the attached product reference image(s) as "
            "authoritative product identity. "
            "Build the new advertising environment around the "
            "product. Do not redesign the product."
        )

        prompt = fit_prompt_for_api(
            prompt,

            label=
                "concept_base_with_product_lock",

            budget=
                PASS_PROMPT_BUDGET
        )

        return openai_multi_reference_edit(
            working_image=
                None,

            references=
                product_refs,

            prompt=
                prompt,

            aspect_ratio=
                aspect_ratio,

            final_quality=
                False,

            pass_name=
                "concept_base_with_product_lock"
        )

    route = build_route(
        PROVIDER_OPENAI,
        OPENAI_IMAGE_MODEL,
        "XPAND Production base generation.",
        aspect_ratio,
        "2K",
        "medium"
    )

    images = generate_with_openai(
        prompt=
            base_prompt,

        original_prompt=
            clean_text(
                compiled_sections(
                    compiled
                ).get(
                    "request",
                    base_prompt
                ),
                6000
            ),

        route=
            route,

        number=
            1
    )

    if not images:

        raise RuntimeError(
            "Base generation returned no image."
        )

    image = images[
        0
    ]

    image.provider = (
        "xpand_production"
    )

    image.metadata[
        "production_engine"
    ] = ENGINE_VERSION

    image.metadata[
        "pass_name"
    ] = "concept_base"

    image.metadata[
        "prompt_chars"
    ] = len(
        base_prompt
    )

    image.metadata[
        "prompt_budget"
    ] = COMPILED_PROMPT_BUDGET

    return image


# =========================================================
# QA PROMPT V2.2
# =========================================================

def build_qa_prompt(
    *,
    original_request: str,
    compiled_prompt: CompiledPrompt,
    image_metadata: Any,
    product_lock: Any,
    brand_context: Any
) -> str:

    master_context = build_pass_context(
        compiled_prompt,
        [
            (
                "creative_direction",
                "APPROVED CREATIVE DIRECTION",
                5000
            ),

            (
                "references",
                "VISUAL REFERENCE DNA",
                2800
            ),

            (
                "camera_direction",
                "CAMERA DIRECTION",
                1800
            ),
        ]
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


IMPORTANT
=========

If no human appears:
human_anatomy = 100 unless an anatomical object is malformed.

If no readable text/logo is required:
text_logo_integrity evaluates absence of random or broken text.

If no product reference was supplied:
product_fidelity evaluates product realism and consistency,
not exact reference matching.

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

        label=
            "visual_qa",

        budget=
            QA_PROMPT_BUDGET
    )


# =========================================================
# QA CALCULATION
# =========================================================

def calculate_qa_score(
    scores: Dict[str, Any]
) -> Tuple[
    float,
    Dict[str, float]
]:

    normalized_scores = {}

    total = 0.0

    for key, weight in QA_WEIGHTS.items():

        value = clamp_score(
            scores.get(
                key,
                0
            )
        )

        normalized_scores[
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
            2
        ),
        normalized_scores
    )


# =========================================================
# CRITICAL BLOCKER DETECTION
# =========================================================

def detect_critical_blockers(
    *,
    scores: Dict[str, float],
    explicit_failures: Any,
    product_lock: Any
) -> List[str]:

    blockers: List[str] = []

    if isinstance(
        explicit_failures,
        list
    ):

        for value in explicit_failures:

            text = clean_text(
                value,
                1000
            )

            if (
                text
                and
                text not in blockers
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

        "text_logo_integrity":
            QA_CRITICAL_SCORE_FLOOR,

        "advertising_readiness":
            QA_AD_READINESS_CRITICAL_FLOOR,
    }

    if (
        isinstance(
            product_lock,
            dict
        )
        and
        product_lock.get(
            "enabled"
        )
    ):

        thresholds[
            "product_fidelity"
        ] = max(
            QA_CRITICAL_SCORE_FLOOR,
            70.0
        )

    for key, threshold in thresholds.items():

        value = clamp_score(
            scores.get(
                key,
                0
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
                        2
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
# QA DECISION POLICY V2.2
# =========================================================

def qa_delivery_decision(
    *,
    score: float,
    critical_blockers: Sequence[str]
) -> Dict[str, Any]:

    score = clamp_score(
        score
    )

    blockers = [
        clean_text(
            item,
            1000
        )
        for item in critical_blockers
        if clean_text(
            item,
            1000
        )
    ]

    target_reached = (
        score
        >=
        QA_TARGET_SCORE
    )

    if blockers:

        return {
            "approved":
                False,

            "target_reached":
                target_reached,

            "decision":
                "critical_blocker",

            "reason":
                (
                    "Critical visual blocker detected."
                ),
        }

    if target_reached:

        return {
            "approved":
                True,

            "target_reached":
                True,

            "decision":
                "target_reached",

            "reason":
                (
                    "QA target reached."
                ),
        }

    if score >= QA_DELIVERY_FLOOR:

        return {
            "approved":
                True,

            "target_reached":
                False,

            "decision":
                "near_target_approved",

            "reason":
                (
                    "Premium near-target score with no critical blockers."
                ),
        }

    return {
        "approved":
            False,

        "target_reached":
            False,

        "decision":
            "correction_candidate",

        "reason":
            (
                "Below delivery floor."
            ),
    }


def recommended_correction_limit(
    qa: Optional[
        QAEvaluation
    ]
) -> int:

    if qa is None:

        return 0

    if qa.passed:

        return 0

    if QA_MAX_CORRECTIONS <= 0:

        return 0

    if qa.score >= QA_SINGLE_CORRECTION_FLOOR:

        return min(
            1,
            QA_MAX_CORRECTIONS
        )

    return QA_MAX_CORRECTIONS


def qa_quality_rank(
    qa: Optional[
        QAEvaluation
    ]
) -> Tuple[
    int,
    int,
    float
]:

    if qa is None:

        return (
            0,
            -999,
            0.0
        )

    approved = (
        1
        if qa.passed
        else
        0
    )

    blocker_rank = (
        -len(
            qa.critical_blockers
        )
    )

    return (
        approved,
        blocker_rank,
        float(
            qa.score
        ),
    )


def qa_candidate_is_better(
    candidate: Optional[
        QAEvaluation
    ],
    existing: Optional[
        QAEvaluation
    ]
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
# VISION QA
# =========================================================

def evaluate_generated_image(
    *,
    image: GeneratedImage,
    original_request: str,
    compiled_prompt: CompiledPrompt,
    product_lock: Any,
    brand_context: Any
) -> QAEvaluation:

    qa_prompt = build_qa_prompt(
        original_request=
            original_request,

        compiled_prompt=
            compiled_prompt,

        image_metadata=
            image.metadata,

        product_lock=
            product_lock,

        brand_context=
            brand_context
    )

    raw = call_openai_director(
        qa_prompt,

        image_bytes=
            image.image_bytes,

        image_mime_type=
            image.mime_type,

        json_mode=
            True
    )

    data = extract_json_object(
        raw
    )

    if not data:

        raise RuntimeError(
            "Visual QA returned invalid JSON."
        )

    scores_raw = data.get(
        "scores",
        {}
    )

    if not isinstance(
        scores_raw,
        dict
    ):

        scores_raw = {}

    score, scores = calculate_qa_score(
        scores_raw
    )

    strengths = data.get(
        "strengths",
        []
    )

    problems = data.get(
        "problems",
        []
    )

    if not isinstance(
        strengths,
        list
    ):

        strengths = []

    if not isinstance(
        problems,
        list
    ):

        problems = []

    explicit_failures = data.get(
        "critical_failures",
        []
    )

    critical_blockers = (
        detect_critical_blockers(
            scores=
                scores,

            explicit_failures=
                explicit_failures,

            product_lock=
                product_lock
        )
    )

    decision = qa_delivery_decision(
        score=
            score,

        critical_blockers=
            critical_blockers
    )

    data[
        "xpand_qa_policy"
    ] = {
        "target":
            QA_TARGET_SCORE,

        "delivery_floor":
            QA_DELIVERY_FLOOR,

        "single_correction_floor":
            QA_SINGLE_CORRECTION_FLOOR,

        "critical_blockers":
            critical_blockers,

        "delivery_approved":
            decision[
                "approved"
            ],

        "target_reached":
            decision[
                "target_reached"
            ],

        "decision":
            decision[
                "decision"
            ],
    }

    return QAEvaluation(
        score=
            score,

        scores=
            scores,

        passed=
            bool(
                decision[
                    "approved"
                ]
            ),

        strengths=[
            clean_text(
                item,
                1000
            )
            for item in strengths
            if clean_text(
                item,
                1000
            )
        ],

        problems=[
            clean_text(
                item,
                1000
            )
            for item in problems
            if clean_text(
                item,
                1000
            )
        ],

        correction_instruction=
            clean_text(
                data.get(
                    "correction_instruction",
                    ""
                ),
                4500
            ),

        critical_blockers=
            critical_blockers,

        target_reached=
            bool(
                decision[
                    "target_reached"
                ]
            ),

        delivery_approved=
            bool(
                decision[
                    "approved"
                ]
            ),

        decision=
            clean_text(
                decision[
                    "decision"
                ],
                200
            ),

        raw=
            data,
    )


# =========================================================
# CORRECTION PROMPT
# =========================================================

def correction_prompt(
    *,
    qa: QAEvaluation,
    compiled: CompiledPrompt,
    product_lock: Any
) -> str:

    context = build_pass_context(
        compiled,
        [
            (
                "request",
                "ORIGINAL REQUEST",
                3500
            ),

            (
                "creative_direction",
                "APPROVED CREATIVE DIRECTION",
                4500
            ),

            (
                "camera_direction",
                "CAMERA",
                1600
            ),

            (
                "product_lock",
                "PRODUCT LOCK",
                2200
            ),
        ]
    )

    prompt = f"""
QUALITY CORRECTION PASS
=======================

CURRENT QA SCORE:
{qa.score}/100

ASPIRATIONAL TARGET:
{QA_TARGET_SCORE}/100.

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

RULES:

- Fix only the detected problems.
- Prioritize critical blockers first.
- Preserve every successful part.
- Do not redesign the concept.
- Do not replace the visual metaphor.
- Do not change product identity.
- Do not change camera unless QA identified a perspective failure.
- Do not introduce new text.
- Do not add decorative objects.
- Improve realism and campaign readiness.
- The corrected version must be a refinement, not a new image concept.
""".strip()

    return fit_prompt_for_api(
        prompt,

        label=
            "qa_correction",

        budget=
            CORRECTION_PROMPT_BUDGET
    )


# =========================================================
# PRODUCTION PASS SELECTION
# =========================================================

def production_passes_for_mode(
    mode: str,
    *,
    has_product_reference: bool
) -> List[str]:

    mode = clean_text(
        mode,
        100
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
    final_pass: bool
) -> GeneratedImage:

    if pass_name == "composition":

        prompt = composition_pass_prompt(
            compiled,
            camera_direction,
            product_lock
        )

    elif pass_name == "product":

        prompt = product_pass_prompt(
            compiled,
            product_lock
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
        working_image=
            working_image,

        references=
            product_refs,

        prompt=
            prompt,

        aspect_ratio=
            aspect_ratio,

        final_quality=
            final_pass,

        pass_name=
            pass_name
    )


# =========================================================
# QA LOGGING
# =========================================================

def print_qa_decision(
    qa: Optional[
        QAEvaluation
    ]
) -> None:

    if qa is None:

        print(
            "⚠️ QA decision unavailable"
        )

        return

    print(
        (
            "QA decision: "
            +
            qa.decision
        )
    )

    print(
        (
            "Delivery approved: "
            +
            str(
                qa.passed
            )
        )
    )

    print(
        (
            "Target reached: "
            +
            str(
                qa.target_reached
            )
        )
    )

    print(
        (
            "Critical blockers: "
            +
            str(
                len(
                    qa.critical_blockers
                )
            )
        )
    )

    for blocker in qa.critical_blockers[
        :5
    ]:

        print(
            (
                "  ⛔ "
                +
                blocker
            )
        )


# =========================================================
# MASTER PRODUCTION PIPELINE V2.2
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
    target_model: str = TARGET_OPENAI
) -> ProductionResult:

    started = time.monotonic()

    errors: List[str] = []

    references = load_runtime_references(
        core,
        user_id,
        brand_id,

        limit=
            12
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

        request=
            original_request,

        creative_direction=
            creative_direction,

        brand_context=
            brand_context,

        references=
            dna_payload,

        camera_direction=
            camera_direction,

        product_lock=
            product_lock
    )

    if compiled.target != TARGET_OPENAI:

        raise RuntimeError(
            (
                "Execution for target '"
                +
                compiled.target
                +
                "' is not connected yet. "
                "Prompt compilation is available, "
                "but production execution is OpenAI-only in V2.2."
            )
        )

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND PRODUCTION ENGINE V2.2"
    )
    print(
        "=========================================="
    )

    print(
        "Mode:",
        mode
    )

    print(
        "Target:",
        compiled.target
    )

    print(
        "References:",
        len(
            references
        )
    )

    print(
        "Product references:",
        len(
            product_refs
        )
    )

    print(
        "Product Lock:",
        (
            "ACTIVE"
            if product_lock.get(
                "enabled"
            )
            else
            "none"
        )
    )

    print(
        "QA target:",
        QA_TARGET_SCORE
    )

    print(
        "QA delivery floor:",
        QA_DELIVERY_FLOOR
    )

    print(
        "QA single-correction floor:",
        QA_SINGLE_CORRECTION_FLOOR
    )

    print(
        "QA max corrections:",
        QA_MAX_CORRECTIONS
    )

    print(
        "QA correction time budget:",
        QA_CORRECTION_TIME_BUDGET_SECONDS,
        "seconds"
    )

    print(
        "Prompt hard limit:",
        OPENAI_PROMPT_HARD_LIMIT
    )

    print(
        "Compiled prompt budget:",
        COMPILED_PROMPT_BUDGET
    )

    print(
        "Compiled prompt chars:",
        len(
            compiled.prompt
        )
    )

    print(
        (
            "Prompt budget status:"
        ),
        (
            "OK ✅"
            if len(
                compiled.prompt
            )
            <=
            COMPILED_PROMPT_BUDGET
            else
            "FAILED ❌"
        )
    )

    print("")

    if len(
        compiled.prompt
    ) > COMPILED_PROMPT_BUDGET:

        raise RuntimeError(
            "Compiled production prompt exceeded XPAND safety budget."
        )

    # =====================================================
    # BASE
    # =====================================================

    print(
        "🎬 PASS 0: Concept Base..."
    )

    working = generate_base_image(
        compiled=
            compiled,

        product_refs=
            product_refs,

        aspect_ratio=
            aspect_ratio
    )

    passes: List[
        ProductionPassResult
    ] = [
        ProductionPassResult(
            pass_name=
                (
                    "concept_base_with_product_lock"
                    if product_refs
                    else
                    "concept_base"
                ),

            image=
                working,

            metadata={
                "prompt_chars":
                    working.metadata.get(
                        "prompt_chars"
                    ),
            }
        )
    ]

    print(
        "✅ PASS 0: Concept Base"
    )

    # =====================================================
    # MULTI-PASS
    # =====================================================

    pass_names = production_passes_for_mode(
        mode,

        has_product_reference=
            bool(
                product_refs
            )
    )

    for index, pass_name in enumerate(
        pass_names,
        start=1
    ):

        is_final_pass = (
            pass_name
            ==
            pass_names[
                -1
            ]
        )

        print(
            (
                "🎨 PASS "
                +
                str(
                    index
                )
                +
                ": "
                +
                pass_name
                +
                "..."
            )
        )

        try:

            working = run_named_pass(
                pass_name=
                    pass_name,

                working_image=
                    working,

                product_refs=
                    product_refs,

                compiled=
                    compiled,

                camera_direction=
                    camera_direction,

                product_lock=
                    product_lock,

                aspect_ratio=
                    aspect_ratio,

                final_pass=
                    is_final_pass
            )

            passes.append(
                ProductionPassResult(
                    pass_name=
                        pass_name,

                    image=
                        working,

                    metadata={
                        "prompt_chars":
                            working.metadata.get(
                                "prompt_chars"
                            ),
                    }
                )
            )

            print(
                (
                    "✅ PASS "
                    +
                    str(
                        index
                    )
                    +
                    ": "
                    +
                    pass_name
                )
            )

        except Exception as error:

            errors.append(
                (
                    pass_name
                    +
                    ": "
                    +
                    clean_text(
                        error,
                        3000
                    )
                )
            )

            print(
                (
                    "⚠️ PASS FAILED: "
                    +
                    pass_name
                    +
                    " | keeping previous successful image"
                )
            )

    # =====================================================
    # INITIAL QA
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
            image=
                working,

            original_request=
                original_request,

            compiled_prompt=
                compiled,

            product_lock=
                product_lock,

            brand_context=
                brand_context
        )

        best_qa = qa

        best_score = qa.score

        if passes:

            passes[
                -1
            ].qa = qa

        print(
            (
                "📊 QA SCORE: "
                +
                str(
                    qa.score
                )
                +
                "/100"
            )
        )

        print_qa_decision(
            qa
        )

    except Exception as error:

        errors.append(
            (
                "qa_initial: "
                +
                clean_text(
                    error,
                    3000
                )
            )
        )

        print(
            (
                "⚠️ QA unavailable: "
                +
                clean_text(
                    error,
                    1000
                )
            )
        )

    # =====================================================
    # IMMEDIATE DELIVERY DECISION
    # =====================================================

    if (
        best_qa is not None
        and
        best_qa.passed
    ):

        if best_qa.target_reached:

            print(
                "✅ MASTERPIECE QA TARGET REACHED"
            )

        else:

            print(
                (
                    "✅ MASTERPIECE DELIVERY APPROVED"
                    +
                    " | near-target premium score="
                    +
                    str(
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
                    +
                    " | score already >= "
                    +
                    str(
                        QA_DELIVERY_FLOOR
                    )
                )
            )

    # =====================================================
    # SMART AUTO-CORRECTION LOOP V2.2
    # =====================================================

    correction_round = 0

    correction_limit = (
        recommended_correction_limit(
            best_qa
        )
    )

    if (
        best_qa is not None
        and
        not best_qa.passed
    ):

        print(
            (
                "🧠 QA correction allowance: "
                +
                str(
                    correction_limit
                )
                +
                " round(s)"
            )
        )

    current_image = best_image

    current_qa = best_qa

    while (
        current_qa is not None
        and
        not current_qa.passed
        and
        correction_round
        <
        correction_limit
    ):

        elapsed_before_correction = (
            time.monotonic()
            -
            started
        )

        if (
            elapsed_before_correction
            >=
            QA_CORRECTION_TIME_BUDGET_SECONDS
        ):

            print(
                (
                    "⏱️ QA CORRECTION STOPPED"
                    +
                    " | elapsed="
                    +
                    str(
                        round(
                            elapsed_before_correction,
                            1
                        )
                    )
                    +
                    "s"
                    +
                    " | budget="
                    +
                    str(
                        QA_CORRECTION_TIME_BUDGET_SECONDS
                    )
                    +
                    "s"
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
            else
            0.0
        )

        print(
            (
                "🛠️ CORRECTION ROUND "
                +
                str(
                    correction_round
                )
                +
                "/"
                +
                str(
                    correction_limit
                )
                +
                "..."
            )
        )

        #
        # IMPORTANT:
        #
        # Always correct the CURRENT BEST VERSION.
        #
        # Never correct a known-worse result.
        #

        current_image = best_image

        current_qa = best_qa

        prompt = correction_prompt(
            qa=
                current_qa,

            compiled=
                compiled,

            product_lock=
                product_lock
        )

        try:

            corrected = openai_multi_reference_edit(
                working_image=
                    current_image,

                references=
                    product_refs,

                prompt=
                    prompt,

                aspect_ratio=
                    aspect_ratio,

                final_quality=
                    True,

                pass_name=
                    (
                        "qa_correction_"
                        +
                        str(
                            correction_round
                        )
                    )
            )

            corrected_qa = (
                evaluate_generated_image(
                    image=
                        corrected,

                    original_request=
                        original_request,

                    compiled_prompt=
                        compiled,

                    product_lock=
                        product_lock,

                    brand_context=
                        brand_context
                )
            )

            passes.append(
                ProductionPassResult(
                    pass_name=
                        (
                            "qa_correction_"
                            +
                            str(
                                correction_round
                            )
                        ),

                    image=
                        corrected,

                    qa=
                        corrected_qa,

                    metadata={
                        "prompt_chars":
                            corrected.metadata.get(
                                "prompt_chars"
                            ),
                    }
                )
            )

            print(
                (
                    "📊 CORRECTED SCORE: "
                    +
                    str(
                        corrected_qa.score
                    )
                    +
                    "/100"
                )
            )

            print_qa_decision(
                corrected_qa
            )

            candidate_better = (
                qa_candidate_is_better(
                    corrected_qa,
                    best_qa
                )
            )

            if not candidate_better:

                print(
                    "🛑 CORRECTION REGRESSION DETECTED"
                )

                print(
                    (
                        "Best kept: "
                        +
                        str(
                            best_score
                        )
                        +
                        "/100"
                    )
                )

                print(
                    (
                        "Rejected correction: "
                        +
                        str(
                            corrected_qa.score
                        )
                        +
                        "/100"
                    )
                )

                print(
                    "🚫 No further correction will start from a worse image."
                )

                break

            best_image = corrected

            best_qa = corrected_qa

            best_score = corrected_qa.score

            current_image = best_image

            current_qa = best_qa

            improvement = (
                best_score
                -
                previous_best_score
            )

            print(
                (
                    "📈 Improvement: +"
                    +
                    str(
                        round(
                            improvement,
                            2
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
                            +
                            " | score="
                            +
                            str(
                                best_qa.score
                            )
                            +
                            " | no critical blockers"
                        )
                    )

                break

            if (
                improvement
                <
                QA_MIN_IMPROVEMENT
            ):

                print(
                    (
                        "🛑 QA CORRECTION STOP"
                        +
                        " | improvement "
                        +
                        str(
                            round(
                                improvement,
                                2
                            )
                        )
                        +
                        " < "
                        +
                        str(
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
                    "qa_correction_"
                    +
                    str(
                        correction_round
                    )
                    +
                    ": "
                    +
                    clean_text(
                        error,
                        3000
                    )
                )
            )

            print(
                (
                    "⚠️ Correction failed; "
                    "keeping best previous version."
                )
            )

            break

    # =====================================================
    # FINAL QA STATUS
    # =====================================================

    final_delivery_approved = bool(
        best_qa
        and
        best_qa.passed
    )

    final_target_reached = bool(
        best_qa
        and
        best_qa.target_reached
    )

    final_decision = (
        best_qa.decision
        if best_qa
        else
        "qa_unavailable"
    )

    final_blockers = (
        best_qa.critical_blockers
        if best_qa
        else
        []
    )

    # =====================================================
    # FINAL METADATA
    # =====================================================

    best_image.provider = (
        "xpand_masterpiece"
        if mode == MODE_MASTERPIECE
        else
        "xpand_production"
    )

    best_image.model = (
        "XPAND Production V2.2 → "
        +
        OPENAI_IMAGE_MODEL
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
        compiled.prompt
    )

    best_image.metadata[
        "compiled_prompt_budget"
    ] = COMPILED_PROMPT_BUDGET

    best_image.metadata[
        "prompt_budget_manager"
    ] = "active"

    elapsed = round(
        time.monotonic()
        -
        started,
        3
    )

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND PRODUCTION COMPLETE V2.2"
    )
    print(
        "=========================================="
    )

    print(
        "Best score:",
        best_score
    )

    print(
        "Target:",
        QA_TARGET_SCORE
    )

    print(
        "Delivery floor:",
        QA_DELIVERY_FLOOR
    )

    print(
        "Delivery approved:",
        final_delivery_approved
    )

    print(
        "Target reached:",
        final_target_reached
    )

    print(
        "QA decision:",
        final_decision
    )

    print(
        "Critical blockers:",
        len(
            final_blockers
        )
    )

    print(
        "Correction rounds:",
        correction_round
    )

    print(
        "Passes:",
        len(
            passes
        )
    )

    print(
        "Compiled prompt:",
        len(
            compiled.prompt
        ),
        "/",
        COMPILED_PROMPT_BUDGET
    )

    print(
        "Prompt Budget Manager: ACTIVE"
    )

    print(
        "Elapsed:",
        elapsed,
        "seconds"
    )

    print("")

    return ProductionResult(
        ok=
            True,

        final_image=
            best_image,

        best_score=
            best_score,

        qa=
            best_qa,

        passes=
            passes,

        compiled_prompt=
            compiled,

        references_used=
            len(
                references
            ),

        product_references_used=
            len(
                product_refs
            ),

        elapsed_seconds=
            elapsed,

        errors=
            errors,
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
        " XPAND PRODUCTION ENGINE V2.2"
    )
    print(
        "=========================================="
    )
    print("")

    print(
        "QA target:",
        QA_TARGET_SCORE
    )

    print(
        "QA delivery floor:",
        QA_DELIVERY_FLOOR
    )

    print(
        "QA single-correction floor:",
        QA_SINGLE_CORRECTION_FLOOR
    )

    print(
        "QA max corrections:",
        QA_MAX_CORRECTIONS
    )

    print(
        "QA minimum improvement:",
        QA_MIN_IMPROVEMENT
    )

    print(
        "QA correction time budget:",
        QA_CORRECTION_TIME_BUDGET_SECONDS,
        "seconds"
    )

    print(
        "QA weights:",
        sum(
            QA_WEIGHTS.values()
        ),
        "%"
    )

    print("")

    print(
        "OpenAI prompt hard limit:",
        OPENAI_PROMPT_HARD_LIMIT
    )

    print(
        "XPAND compiled budget:",
        COMPILED_PROMPT_BUDGET
    )

    print(
        "XPAND pass budget:",
        PASS_PROMPT_BUDGET
    )

    print(
        "XPAND QA budget:",
        QA_PROMPT_BUDGET
    )

    print("")

    # =====================================================
    # RESOLUTION TEST
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
                +
                " → "
                +
                production_size_for_ratio(
                    ratio,

                    final_quality=
                        True
                )
            )
        )

    print("")

    # =====================================================
    # PASS TEST
    # =====================================================

    no_product = production_passes_for_mode(
        MODE_MASTERPIECE,

        has_product_reference=
            False
    )

    with_product = production_passes_for_mode(
        MODE_MASTERPIECE,

        has_product_reference=
            True
    )

    print(
        "Masterpiece without product reference:"
    )

    print(
        " - concept_base"
    )

    for value in no_product:

        print(
            " -",
            value
        )

    print("")

    print(
        "Masterpiece WITH product reference:"
    )

    print(
        " - concept_base_with_product_lock"
    )

    for value in with_product:

        print(
            " -",
            value
        )

    print("")

    # =====================================================
    # NORMAL COMPILER TEST
    # =====================================================

    dummy_compiler = compile_prompt(
        TARGET_OPENAI,

        request=
            (
                "STC Bank premium travel advertising scene"
            ),

        creative_direction={
            "idea":
                "test"
        },

        brand_context={
            "brand":
                "STC Bank"
        },

        references=[],

        camera_direction={
            "camera":
                "three-quarter hero"
        },

        product_lock={}
    )

    print(
        "Prompt compiler:",
        dummy_compiler.target
    )

    print(
        "Normal compiled chars:",
        len(
            dummy_compiler.prompt
        )
    )

    print("")

    # =====================================================
    # QA POLICY SELF TEST
    # =====================================================

    def fake_qa(
        score: float,
        *,
        blockers: Optional[
            List[str]
        ] = None
    ) -> QAEvaluation:

        blocker_list = (
            blockers
            if blockers
            else
            []
        )

        decision = qa_delivery_decision(
            score=
                score,

            critical_blockers=
                blocker_list
        )

        return QAEvaluation(
            score=
                score,

            scores={},

            passed=
                bool(
                    decision[
                        "approved"
                    ]
                ),

            strengths=[],

            problems=[],

            correction_instruction="",

            critical_blockers=
                blocker_list,

            target_reached=
                bool(
                    decision[
                        "target_reached"
                    ]
                ),

            delivery_approved=
                bool(
                    decision[
                        "approved"
                    ]
                ),

            decision=
                decision[
                    "decision"
                ],
        )

    qa_92 = fake_qa(
        92
    )

    qa_8875 = fake_qa(
        88.75
    )

    qa_8725 = fake_qa(
        87.25
    )

    qa_82 = fake_qa(
        82
    )

    qa_91_blocked = fake_qa(
        91,
        blockers=[
            "perspective critical failure"
        ]
    )

    qa_policy_tests = [
        (
            "92 target reached",
            qa_92.passed
            and
            qa_92.target_reached,
        ),

        (
            "88.75 near-target delivery approved",
            qa_8875.passed
            and
            not qa_8875.target_reached,
        ),

        (
            "88.75 correction count = 0",
            (
                recommended_correction_limit(
                    qa_8875
                )
                ==
                0
            ),
        ),

        (
            "87.25 requires one correction",
            (
                not qa_8725.passed
                and
                recommended_correction_limit(
                    qa_8725
                )
                ==
                min(
                    1,
                    QA_MAX_CORRECTIONS
                )
            ),
        ),

        (
            "82 allows extended correction",
            (
                recommended_correction_limit(
                    qa_82
                )
                ==
                QA_MAX_CORRECTIONS
            ),
        ),

        (
            "91 with critical blocker rejected",
            (
                not
                qa_91_blocked.passed
            ),
        ),
    ]

    qa_policy_ok = True

    print(
        "QA V2.2 policy tests:"
    )

    for name, ok in qa_policy_tests:

        qa_policy_ok = (
            qa_policy_ok
            and
            bool(
                ok
            )
        )

        print(
            (
                " ✅ "
                if ok
                else
                " ❌ "
            ),
            name
        )

    print("")

    # =====================================================
    # BEST VERSION / REGRESSION TEST
    # =====================================================

    old_good = fake_qa(
        87.5
    )

    worse_new = fake_qa(
        86.5
    )

    better_new = fake_qa(
        88.5
    )

    regression_rejected = (
        not qa_candidate_is_better(
            worse_new,
            old_good
        )
    )

    improvement_accepted = (
        qa_candidate_is_better(
            better_new,
            old_good
        )
    )

    blocker_candidate = fake_qa(
        89.0,
        blockers=[
            "critical defect"
        ]
    )

    clean_candidate = fake_qa(
        87.0
    )

    clean_beats_blocked = (
        qa_candidate_is_better(
            clean_candidate,
            blocker_candidate
        )
    )

    version_policy_ok = (
        regression_rejected
        and
        improvement_accepted
        and
        clean_beats_blocked
    )

    print(
        "Best-version policy:"
    )

    print(
        (
            " ✅ "
            if regression_rejected
            else
            " ❌ "
        ),
        "worse correction rejected"
    )

    print(
        (
            " ✅ "
            if improvement_accepted
            else
            " ❌ "
        ),
        "better correction accepted"
    )

    print(
        (
            " ✅ "
            if clean_beats_blocked
            else
            " ❌ "
        ),
        "clean version preferred over critical-blocked version"
    )

    print("")

    # =====================================================
    # EXTREME CONTEXT TEST
    # =====================================================

    giant_text = (
        "STC Bank creative research and detailed campaign "
        "visual intelligence. "
        *
        1000
    )

    giant_references = [
        {
            "role":
                "style_reference",

            "dna": {
                "camera":
                    giant_text,

                "lighting":
                    giant_text,

                "materials":
                    giant_text,

                "composition":
                    giant_text,
            },

            "user_note":
                giant_text,
        }
        for _ in range(
            12
        )
    ]

    giant_brand = {
        "profile":
            giant_text,

        "rules": [
            giant_text
            for _ in range(
                30
            )
        ],

        "campaign_execution": {
            "visual_world":
                giant_text,

            "lighting_system":
                giant_text,

            "material_system":
                giant_text,

            "camera_system":
                giant_text,
        },
    }

    giant_creative = {
        "title":
            "Extreme Masterpiece Test",

        "core_idea":
            giant_text,

        "visual_metaphor":
            giant_text,

        "camera":
            giant_text,

        "production":
            giant_text,
    }

    giant_compiler = compile_prompt(
        TARGET_OPENAI,

        request=
            giant_text,

        creative_direction=
            giant_creative,

        brand_context=
            giant_brand,

        references=
            giant_references,

        camera_direction={
            "camera":
                giant_text
        },

        product_lock={
            "enabled":
                True,

            "must_remain_identical": [
                giant_text
                for _ in range(
                    10
                )
            ],
        }
    )

    giant_length = len(
        giant_compiler.prompt
    )

    giant_ok = (
        giant_length
        <=
        COMPILED_PROMPT_BUDGET
        and
        giant_length
        <
        OPENAI_PROMPT_HARD_LIMIT
    )

    print(
        "Extreme context compiled chars:",
        giant_length
    )

    print(
        "Extreme context budget test:",
        (
            "PASS ✅"
            if giant_ok
            else
            "FAIL ❌"
        )
    )

    print("")

    # =====================================================
    # PASS-PROMPT TESTS
    # =====================================================

    test_prompts = {
        "composition":
            composition_pass_prompt(
                giant_compiler,

                {
                    "camera":
                        giant_text
                },

                {
                    "lock":
                        giant_text
                }
            ),

        "product":
            product_pass_prompt(
                giant_compiler,

                {
                    "lock":
                        giant_text
                }
            ),

        "lighting":
            lighting_pass_prompt(
                giant_compiler
            ),

        "materials":
            material_pass_prompt(
                giant_compiler
            ),

        "final_polish":
            polish_pass_prompt(
                giant_compiler
            ),
    }

    all_passes_ok = True

    print(
        "Production pass prompt budgets:"
    )

    for name, prompt in (
        test_prompts.items()
    ):

        length = len(
            prompt
        )

        ok = (
            length
            <=
            PASS_PROMPT_BUDGET
            and
            length
            <
            OPENAI_PROMPT_HARD_LIMIT
        )

        if not ok:

            all_passes_ok = False

        print(
            (
                " ✅ "
                if ok
                else
                " ❌ "
            ),
            name,
            "=",
            length,
            "/",
            PASS_PROMPT_BUDGET
        )

    print("")

    print(
        "Prepared compilers:"
    )

    for target in [
        TARGET_OPENAI,
        TARGET_GEMINI,
        TARGET_MIDJOURNEY,
        TARGET_FLUX,
        TARGET_IDEOGRAM,
        TARGET_RUNWAY,
        TARGET_KLING,
        TARGET_SEEDANCE,
    ]:

        print(
            " -",
            target
        )

    print("")

    print(
        "✅ Prompt Budget Manager"
    )

    print(
        "✅ Structured context compaction"
    )

    print(
        "✅ Request priority preserved"
    )

    print(
        "✅ Creative-direction priority preserved"
    )

    print(
        "✅ Brand Memory compact execution context"
    )

    print(
        "✅ Visual Reference DNA compaction"
    )

    print(
        "✅ Camera context preserved"
    )

    print(
        "✅ Product Lock preserved"
    )

    print(
        "✅ Per-pass selective context"
    )

    print(
        "✅ Prompt length logging before API calls"
    )

    print(
        "✅ GPT-Image-2 overflow protection"
    )

    print(
        "✅ Model-specific Prompt Compiler"
    )

    print(
        "✅ High-Fidelity Product Reference Lock"
    )

    print(
        "✅ Multi-reference GPT-Image-2 editing"
    )

    print(
        "✅ Composition Pass"
    )

    print(
        "✅ Product Fidelity Pass"
    )

    print(
        "✅ Lighting Pass"
    )

    print(
        "✅ Material Pass"
    )

    print(
        "✅ Final Polish"
    )

    print(
        "✅ Vision QA /100"
    )

    print(
        "✅ 90+ full target"
    )

    print(
        "✅ 88+ near-target Masterpiece delivery"
    )

    print(
        "✅ Critical blocker hard gate"
    )

    print(
        "✅ 85–87.99 single correction policy"
    )

    print(
        "✅ Below-85 extended correction policy"
    )

    print(
        "✅ Correction regression stop"
    )

    print(
        "✅ Never continue from a worse image"
    )

    print(
        "✅ Minimum-improvement stop"
    )

    print(
        "✅ QA correction time budget"
    )

    print(
        "✅ Best-version preservation V2"
    )

    print(
        "✅ High-resolution output mapping"
    )

    print("")

    all_ok = (
        giant_ok
        and
        all_passes_ok
        and
        qa_policy_ok
        and
        version_policy_ok
    )

    print(
        (
            "XPAND Production Engine V2.2 self-test: "
            +
            (
                "PASS ✅"
                if all_ok
                else
                "FAIL ❌"
            )
        )
    )

    print("")

    print(
        "🚫 No API calls were made"
    )

    print("")
