# =========================================================
# XPAND PRODUCTION ENGINE V5.2
#
# PRODUCTION-SAFE MASTERPIECE RENDERER
#
# STC BANK:
# - Permanent Brand Pack grounding
# - Short render contract
# - 5 local references may be loaded
# - max 3 references are sent on primary render
# - max 2 references are sent during working-image repair
# - brittle concepts may receive a production-safe
#   reinterpretation without changing the commercial idea
# - second pass edits the first image instead of blindly
#   rebuilding an unrelated scene
# - strict Vision QA remains active
# - STC target = 92
# - STC release floor = 88
#
# FULL RUNTIME-COMPATIBLE REPLACEMENT
#
# =========================================================
#
# PUBLIC CONTRACT PRESERVED:
#
#   MODE_FAST
#   MODE_PRO
#   MODE_MASTERPIECE
#
#   TARGET_OPENAI
#   TARGET_GEMINI
#   TARGET_MIDJOURNEY
#   TARGET_FLUX
#   TARGET_IDEOGRAM
#   TARGET_RUNWAY
#   TARGET_KLING
#   TARGET_SEEDANCE
#
#   ProductionReference
#   CompiledPrompt
#   QAEvaluation
#   ProductionPassResult
#   ProductionResult
#
#   run_production()
#   evaluate_generated_image()
#   load_runtime_references()
#   compile_prompt()
#   generate_high_quality_image()
#   gemini_multi_reference_edit()
#   openai_multi_reference_edit
#   product_references()
#   choose_physical_references()
#   reference_dna_payload()
#   combined_product_lock()
#   get_brand_visual_profile()
#   get_production_engine_status()
#
# =========================================================
#
# ZERO-COST SELF TEST:
#
#     python xpand_production_engine.py
#
# No API calls are made by the self-test.
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

from pathlib import Path

from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
)

import requests


# =========================================================
# XPAND IMAGE ENGINE
# =========================================================

from xpand_image_engine import (
    GEMINI_API_KEY,
    GEMINI_INTERACTIONS_URL,
    GOOGLE_IMAGE_FAST_MODEL,
    REQUEST_TIMEOUT,
    GeneratedImage,
    call_openai_director,
    detect_image_size,
)


# =========================================================
# STC BANK SKILL
# =========================================================

from xpand_stc_bank_skill import (
    STC_BANK_IMAGE_GUARD,
    STYLE_AUGMENTED_REALISM,
    STYLE_PREMIUM_REALISTIC,
    STYLE_PURPLE_ARCHITECTURAL,
    detect_stc_benefit_family,
    detect_stc_visual_style,
    is_stc_bank_request,
)


# =========================================================
# BRAND MEMORY
# =========================================================

import xpand_brand_memory as xpand_brand_memory


# =========================================================
# PERMANENT STC BRAND KIT
# =========================================================

try:

    from xpand_stc_brand_kit import (
        BrandKit,
        ReferenceAsset,
        load_default_stc_brand_kit,
    )

    STC_BRAND_KIT_AVAILABLE = True

except Exception:

    BrandKit = Any
    ReferenceAsset = Any

    load_default_stc_brand_kit = None

    STC_BRAND_KIT_AVAILABLE = False


# =========================================================
# IDENTITY
# =========================================================

ENGINE_NAME = (
    "XPAND Production Engine"
)

ENGINE_VERSION = "5.2"


# =========================================================
# MODES
# =========================================================

MODE_FAST = "fast"

MODE_PRO = "pro"

MODE_MASTERPIECE = "masterpiece"


# =========================================================
# TARGETS
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
# ENV HELPERS
# =========================================================

def env_bool(
    name: str,
    default: bool,
) -> bool:

    value = str(
        os.environ.get(
            name,
            "true" if default else "false",
        )
    ).strip().lower()

    return value in {
        "1",
        "true",
        "yes",
        "on",
        "enabled",
    }


def env_int(
    name: str,
    default: int,
) -> int:

    try:

        return int(
            os.environ.get(
                name,
                str(default),
            )
            or default
        )

    except Exception:

        return int(default)


def env_float(
    name: str,
    default: float,
) -> float:

    try:

        return float(
            os.environ.get(
                name,
                str(default),
            )
            or default
        )

    except Exception:

        return float(default)


# =========================================================
# IMAGE MODELS
# =========================================================

NANO_BANANA_2_MODEL = str(
    os.environ.get(
        "XPAND_MASTERPIECE_EXPLORATION_MODEL",
        (
            GOOGLE_IMAGE_FAST_MODEL
            or
            "gemini-3.1-flash-image"
        ),
    )
).strip()


if not NANO_BANANA_2_MODEL:

    NANO_BANANA_2_MODEL = (
        "gemini-3.1-flash-image"
    )


NANO_BANANA_PRO_MODEL = str(
    os.environ.get(
        "XPAND_STC_PRO_IMAGE_MODEL",
        "gemini-3-pro-image",
    )
).strip()


if not NANO_BANANA_PRO_MODEL:

    NANO_BANANA_PRO_MODEL = (
        "gemini-3-pro-image"
    )


STC_ALLOW_GEMINI_PRO_UPGRADE = env_bool(
    "XPAND_STC_ALLOW_GEMINI_PRO_UPGRADE",
    True,
)


# =========================================================
# STC HIGH ALERT
# =========================================================

STC_HIGH_ALERT_ENABLED = env_bool(
    "XPAND_STC_HIGH_ALERT",
    True,
)


STC_REQUIRE_BRAND_PACK = env_bool(
    "XPAND_STC_REQUIRE_BRAND_PACK",
    True,
)


STC_FORCE_BRAND_GROUNDING = env_bool(
    "XPAND_STC_FORCE_BRAND_GROUNDING",
    True,
)


STC_REJECT_GENERIC_SCENES = env_bool(
    "XPAND_STC_REJECT_GENERIC_SCENES",
    True,
)


STC_REJECT_REPEATED_SCENES = env_bool(
    "XPAND_STC_REJECT_REPEATED_SCENES",
    True,
)


# =========================================================
# CALL LIMITS
# =========================================================

MASTERPIECE_MAX_IMAGE_CALLS = max(
    1,
    min(
        2,
        env_int(
            "XPAND_MASTERPIECE_MAX_IMAGE_CALLS",
            2,
        ),
    ),
)


MASTERPIECE_MAX_VISION_CALLS = max(
    1,
    min(
        2,
        env_int(
            "XPAND_MASTERPIECE_MAX_VISION_CALLS",
            2,
        ),
    ),
)


# =========================================================
# REFERENCE POLICY
# =========================================================

SMART_REFERENCE_SELECTION_LIMIT = max(
    1,
    min(
        3,
        env_int(
            "XPAND_SMART_REFERENCE_LIMIT",
            3,
        ),
    ),
)


MAX_PHYSICAL_REFERENCE_IMAGES = max(
    0,
    min(
        2,
        env_int(
            "XPAND_PHYSICAL_REFERENCE_LIMIT",
            2,
        ),
    ),
)


#
# IMPORTANT:
#
# Up to five permanent STC references may still be LOADED
# and inspected.
#
# V5.2 deliberately does NOT send all five to the image
# generator at once.
#

MAX_STC_PHYSICAL_REFERENCE_IMAGES = max(
    3,
    min(
        5,
        env_int(
            "XPAND_STC_PHYSICAL_REFERENCE_LIMIT",
            5,
        ),
    ),
)


#
# Primary STC render:
#
# 1 campaign / DNA
# 1 style
# 1 service / merchant
#

STC_RENDER_REFERENCE_LIMIT = max(
    2,
    min(
        3,
        env_int(
            "XPAND_STC_RENDER_REFERENCE_LIMIT",
            3,
        ),
    ),
)


#
# Working-image correction:
#
# Current rendered image itself is already one image input.
# Add no more than two STC references.
#

STC_EDIT_REFERENCE_LIMIT = max(
    1,
    min(
        2,
        env_int(
            "XPAND_STC_EDIT_REFERENCE_LIMIT",
            2,
        ),
    ),
)


STC_IDEATION_REFERENCE_LIMIT = max(
    3,
    min(
        7,
        env_int(
            "XPAND_STC_IDEATION_REFERENCE_LIMIT",
            7,
        ),
    ),
)


SEND_VISUAL_REFERENCES_TO_IMAGE = env_bool(
    "XPAND_SEND_VISUAL_REFERENCES_TO_IMAGE",
    True,
)


MAX_LOCAL_REFERENCE_BYTES = max(
    2_000_000,
    min(
        30_000_000,
        env_int(
            "XPAND_STC_MAX_REFERENCE_BYTES",
            15_000_000,
        ),
    ),
)


# =========================================================
# QA POLICY — GENERAL
# =========================================================

QA_TARGET_SCORE = max(
    82.0,
    min(
        96.0,
        env_float(
            "XPAND_PRODUCTION_QA_TARGET",
            86.0,
        ),
    ),
)


QA_RELEASE_FLOOR = max(
    76.0,
    min(
        QA_TARGET_SCORE,
        env_float(
            "XPAND_PRODUCTION_QA_RELEASE_FLOOR",
            80.0,
        ),
    ),
)


QA_CRITICAL_SCORE_FLOOR = max(
    50.0,
    min(
        80.0,
        env_float(
            "XPAND_PRODUCTION_QA_CRITICAL_FLOOR",
            65.0,
        ),
    ),
)


# =========================================================
# QA POLICY — STC HIGH ALERT
# =========================================================

STC_QA_TARGET_SCORE = max(
    88.0,
    min(
        98.0,
        env_float(
            "XPAND_STC_QA_TARGET",
            92.0,
        ),
    ),
)


STC_QA_RELEASE_FLOOR = max(
    84.0,
    min(
        STC_QA_TARGET_SCORE,
        env_float(
            "XPAND_STC_QA_RELEASE_FLOOR",
            88.0,
        ),
    ),
)


# =========================================================
# PROMPT BUDGETS V5.2
# =========================================================
#
# V5.1 could allow a 26K production blueprint.
#
# V5.2 intentionally caps the actual render contract.
#
# The image generator should receive production decisions,
# not the entire history of the creative process.
#

COMPILED_PROMPT_BUDGET = max(
    6000,
    min(
        10_000,
        env_int(
            "XPAND_COMPILED_PROMPT_BUDGET",
            8500,
        ),
    ),
)


IMAGE_CALL_PROMPT_BUDGET = max(
    7500,
    min(
        12_000,
        env_int(
            "XPAND_IMAGE_CALL_PROMPT_BUDGET",
            10_500,
        ),
    ),
)


QA_PROMPT_BUDGET = max(
    7500,
    min(
        13_000,
        env_int(
            "XPAND_QA_PROMPT_BUDGET",
            10_500,
        ),
    ),
)


CORRECTION_PROMPT_BUDGET = max(
    5500,
    min(
        9000,
        env_int(
            "XPAND_CORRECTION_PROMPT_BUDGET",
            7200,
        ),
    ),
)


# =========================================================
# QA WEIGHTS
# =========================================================

QA_WEIGHTS = {

    "concept_execution":
        12,

    "message_clarity_without_text":
        10,

    "brand_alignment":
        8,

    "brand_identity_strength":
        8,

    "advertising_readiness":
        10,

    "scene_originality":
        8,

    "service_integration":
        8,

    "realism":
        8,

    "camera_perspective":
        6,

    "lighting_materials":
        6,

    "human_anatomy":
        4,

    "reference_adherence":
        4,

    "text_logo_compliance":
        4,

    "purple_restraint":
        4,
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

    content_family: str = (
        "general_brand"
    )

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

    telemetry: Dict[str, Any] = field(
        default_factory=dict
    )


# =========================================================
# BASIC HELPERS
# =========================================================

def clean_text(
    value: Any,
    limit: int = 12000,
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

    if isinstance(
        value,
        dict,
    ):

        return value

    return {}


def safe_list(
    value: Any,
) -> List[Any]:

    if isinstance(
        value,
        list,
    ):

        return value

    if isinstance(
        value,
        tuple,
    ):

        return list(value)

    return []


def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:

    try:

        return float(value)

    except Exception:

        return float(default)


def clamp_score(
    value: Any,
) -> float:

    return max(
        0.0,
        min(
            100.0,
            safe_float(
                value,
                0.0,
            ),
        ),
    )


def normalize_text(
    value: Any,
) -> str:

    text = clean_text(
        value,
        60000,
    ).lower()

    replacements = {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ة": "ه",
        "ى": "ي",
        "ؤ": "و",
        "ئ": "ي",
        "ـ": "",
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
    value: Any,
    markers: Sequence[str],
) -> bool:

    source = normalize_text(
        value
    )

    return any(
        normalize_text(
            marker
        )
        in source
        for marker in markers
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

    if len(text) <= limit:

        return text

    front = int(
        limit * 0.78
    )

    back = max(
        0,
        limit
        -
        front
        -
        90,
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


def fit_prompt_for_api(
    prompt: str,
    *,
    label: str,
    budget: int,
) -> str:

    text = clean_text(
        prompt,
        max(
            budget * 3,
            budget,
        ),
    )

    if len(text) <= budget:

        return text

    front = int(
        budget * 0.80
    )

    back = max(
        0,
        budget
        -
        front
        -
        180,
    )

    print(
        "✂️ PROMPT COMPACTED"
        +
        " | "
        +
        label
        +
        " | "
        +
        str(
            len(text)
        )
        +
        " → "
        +
        str(budget)
    )

    return (
        text[:front]
        +
        "\n\n"
        +
        "[XPAND COMPACTED — KEEP THE FINAL LOCKS BELOW]\n\n"
        +
        (
            text[-back:]
            if back
            else ""
        )
    )


def dedupe_strings(
    values: Iterable[Any],
    *,
    limit: int = 100,
) -> List[str]:

    output: List[str] = []

    seen: Set[str] = set()

    for item in values:

        text = clean_text(
            item,
            1600,
        )

        if not text:

            continue

        key = normalize_text(
            text
        )

        if (
            not key
            or
            key in seen
        ):

            continue

        seen.add(
            key
        )

        output.append(
            text
        )

        if len(output) >= limit:

            break

    return output


def parse_json_object(
    value: Any,
) -> Dict[str, Any]:

    if isinstance(
        value,
        dict,
    ):

        return value

    text = clean_text(
        value,
        200000,
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
# IMAGE RESPONSE HELPERS
# =========================================================

def decode_image_value(
    value: Any,
) -> Optional[bytes]:

    if not isinstance(
        value,
        str,
    ):

        return None

    source = value.strip()

    if not source:

        return None

    if source.startswith(
        "data:"
    ):

        if "," not in source:

            return None

        source = source.split(
            ",",
            1,
        )[1]

    try:

        raw = base64.b64decode(
            source,
            validate=False,
        )

    except Exception:

        return None

    if len(raw) < 100:

        return None

    return raw


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

            for key in (
                "b64_json",
                "base64",
                "data",
            ):

                raw = decode_image_value(
                    item.get(key)
                )

                if raw:

                    found.append(
                        (
                            raw,
                            mime_type
                            or
                            "image/jpeg",
                        )
                    )

                    break

            for child in item.values():

                walk(child)

        elif isinstance(
            item,
            list,
        ):

            for child in item:

                walk(child)

    walk(value)

    output: List[
        Tuple[
            bytes,
            str,
        ]
    ] = []

    seen = set()

    for raw, mime_type in found:

        signature = (
            len(raw),
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


# =========================================================
# REQUEST HELPERS
# =========================================================

def is_stc_production_request(
    original_request: str,
    brand_id: str,
) -> bool:

    if (
        clean_text(
            brand_id,
            100,
        ).lower()
        ==
        "stc_bank"
    ):

        return True

    return bool(
        is_stc_bank_request(
            original_request
        )
    )


def is_stc_high_alert(
    original_request: str,
    mode: str,
    brand_id: str,
) -> bool:

    return bool(
        STC_HIGH_ALERT_ENABLED
        and
        mode
        ==
        MODE_MASTERPIECE
        and
        is_stc_production_request(
            original_request,
            brand_id,
        )
    )


def stc_scene_tier(
    request: str,
) -> str:

    style = (
        detect_stc_visual_style(
            request
        )
        or
        STYLE_PREMIUM_REALISTIC
    )

    if style == STYLE_PURPLE_ARCHITECTURAL:

        return "TIER_C"

    if style == STYLE_AUGMENTED_REALISM:

        return "TIER_B"

    return "TIER_A"


def stc_visual_family_for_brand_kit(
    request: str,
) -> str:

    style = (
        detect_stc_visual_style(
            request
        )
        or
        STYLE_PREMIUM_REALISTIC
    )

    if style == STYLE_PURPLE_ARCHITECTURAL:

        return "premium_purple_architecture"

    if style == STYLE_AUGMENTED_REALISM:

        return "premium_augmented_realism"

    return "premium_realistic"


def build_stc_scene_tier_instruction(
    request: str,
) -> str:

    tier = stc_scene_tier(
        request
    )

    if tier == "TIER_C":

        return """
TIER C — PURPLE ARCHITECTURAL
Purple may live in real architectural planes and materials.
Human skin, natural objects, food, white clothing and neutral
products stay naturally colored.
No cyber neon. No nightclub look. No fintech CGI clutter.
""".strip()

    if tier == "TIER_B":

        return """
TIER B — AUGMENTED REALISM
Base world stays photographic.
Use only one believable conceptual intervention.
It must obey perspective, gravity, scale, occlusion, contact
shadow and real material behavior.
Purple stays restrained.
""".strip()

    return """
TIER A — PREMIUM REALISTIC
Natural photographic Saudi environment.
No global purple wash.
Brand identity comes from art direction, material quality,
composition, camera, confidence and restrained accents.
""".strip()


def safe_frame_instruction(
    aspect_ratio: str,
) -> str:

    return (
        "FRAME LOCK: final image must be "
        +
        clean_text(
            aspect_ratio,
            40,
        )
        +
        ". Preserve all important subjects inside safe margins. "
        "Build 25–40% calm natural copy space without placing "
        "generated typography inside it."
    )


# =========================================================
# BRAND VISUAL PROFILE
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
            xpand_brand_memory
            .get_brand_visual_profile(
                core,
                user_id,
                brand_id,
            )
        )

        if (
            isinstance(
                profile,
                dict,
            )
            and
            profile
        ):

            return profile

    except Exception as error:

        print(
            "⚠️ Brand Visual Profile load:",
            clean_text(
                error,
                800,
            ),
        )

    try:

        profile = (
            xpand_brand_memory
            .refresh_brand_visual_profile(
                core,
                user_id,
                brand_id,
            )
        )

        if isinstance(
            profile,
            dict,
        ):

            return profile

    except Exception as error:

        print(
            "⚠️ Brand Visual Profile refresh:",
            clean_text(
                error,
                800,
            ),
        )

    return {}


def get_brand_visual_profile(
    core,
    user_id,
    brand_id: str,
) -> Dict[str, Any]:

    return load_brand_visual_profile_safe(
        core,
        user_id,
        brand_id,
    )


# =========================================================
# BRAND MEMORY REFERENCES
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

    stored: List[Any] = []

    if request:

        try:

            stored = (
                xpand_brand_memory
                .load_relevant_visual_references(
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
                "⚠️ Reference Curator:",
                clean_text(
                    error,
                    1000,
                ),
            )

    if not stored:

        try:

            stored = (
                xpand_brand_memory
                .load_visual_references(
                    core,
                    user_id,
                    brand_id=brand_id,
                    limit=limit,
                )
            )

        except Exception as error:

            print(
                "⚠️ Reference fallback:",
                clean_text(
                    error,
                    1000,
                ),
            )

            stored = []

    references: List[
        ProductionReference
    ] = []

    for item in safe_list(
        stored
    ):

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

        raw = b""

        if (
            file_id
            and
            hasattr(
                core,
                "get_telegram_file_bytes",
            )
        ):

            try:

                raw = (
                    core.get_telegram_file_bytes(
                        file_id
                    )
                    or
                    b""
                )

            except Exception as error:

                print(
                    "⚠️ Reference image unavailable:",
                    clean_text(
                        error,
                        700,
                    ),
                )

        references.append(
            ProductionReference(

                role=(
                    clean_text(
                        item.get(
                            "reference_role",
                            "style_reference",
                        ),
                        100,
                    )
                    or
                    "style_reference"
                ),

                image_bytes=raw,

                mime_type=(
                    infer_mime_type(
                        raw
                    )
                    if raw
                    else
                    "image/jpeg"
                ),

                dna=safe_dict(
                    item.get(
                        "dna"
                    )
                ),

                product_lock=safe_dict(
                    item.get(
                        "product_lock"
                    )
                ),

                user_note=clean_text(
                    item.get(
                        "user_note",
                        "",
                    ),
                    1200,
                ),

                source_id=clean_text(
                    item.get(
                        "id",
                        "",
                    ),
                    300,
                ),

                content_family=(
                    clean_text(
                        item.get(
                            "content_family",
                            "general_brand",
                        ),
                        120,
                    )
                    or
                    "general_brand"
                ),

                source_metadata=safe_dict(
                    item.get(
                        "source_metadata"
                    )
                ),

                selection=safe_dict(
                    item.get(
                        "selection"
                    )
                ),
            )
        )

    return references


# =========================================================
# STC LOCAL REFERENCES
# =========================================================

def role_for_stc_asset(
    asset: Any,
) -> str:

    category = clean_text(
        getattr(
            asset,
            "category",
            "",
        ),
        100,
    ).lower()

    roles = [
        clean_text(
            item,
            100,
        ).lower()
        for item
        in (
            getattr(
                asset,
                "roles",
                [],
            )
            or []
        )
    ]

    joined = (
        category
        +
        " "
        +
        " ".join(roles)
    )

    if (
        "dna"
        in joined
        or
        "brand_dna"
        in joined
    ):

        return "campaign_reference"

    if (
        "merchant"
        in joined
        or
        "service"
        in joined
    ):

        return "environment_reference"

    if (
        "realistic"
        in joined
        or
        "purple"
        in joined
        or
        "augmented"
        in joined
        or
        "style"
        in joined
    ):

        return "style_reference"

    return "style_reference"


def load_stc_local_references(
    *,
    request: str,
    max_total: int = MAX_STC_PHYSICAL_REFERENCE_IMAGES,
    rotation_key: str = "",
) -> Tuple[
    List[ProductionReference],
    Optional[Any],
    List[Any],
]:

    if (
        not STC_BRAND_KIT_AVAILABLE
        or
        load_default_stc_brand_kit
        is None
    ):

        if STC_REQUIRE_BRAND_PACK:

            raise RuntimeError(
                "Required STC Brand Kit is unavailable."
            )

        return (
            [],
            None,
            [],
        )

    try:

        kit = (
            load_default_stc_brand_kit()
        )

    except Exception as error:

        if STC_REQUIRE_BRAND_PACK:

            raise RuntimeError(
                (
                    "Required STC Brand Pack could not be loaded: "
                    +
                    clean_text(
                        error,
                        1800,
                    )
                )
            )

        print(
            "⚠️ STC Brand Pack unavailable:",
            clean_text(
                error,
                1000,
            ),
        )

        return (
            [],
            None,
            [],
        )

    benefit_family = (
        detect_stc_benefit_family(
            request
        )
    )

    visual_family = (
        stc_visual_family_for_brand_kit(
            request
        )
    )

    selected_assets = (
        kit.select_generation_assets(

            benefit_family=(
                benefit_family
            ),

            visual_family=(
                visual_family
            ),

            max_total=max(
                1,
                min(
                    MAX_STC_PHYSICAL_REFERENCE_IMAGES,
                    int(
                        max_total
                        or
                        MAX_STC_PHYSICAL_REFERENCE_IMAGES
                    ),
                ),
            ),

            rotation_key=(
                rotation_key
                or
                request
            ),
        )
    )

    references: List[
        ProductionReference
    ] = []

    for asset in selected_assets:

        try:

            path = kit.resolve_asset_path(
                asset.path
            )

        except Exception:

            continue

        if not path.is_file():

            continue

        try:

            size = path.stat().st_size

        except Exception:

            continue

        if (
            size <= 0
            or
            size > MAX_LOCAL_REFERENCE_BYTES
        ):

            print(
                "⚠️ STC reference skipped:",
                path.name,
                size,
            )

            continue

        try:

            raw = path.read_bytes()

        except Exception as error:

            print(
                "⚠️ STC local reference read failed:",
                clean_text(
                    error,
                    1000,
                ),
            )

            continue

        if not raw:

            continue

        references.append(
            ProductionReference(

                role=(
                    role_for_stc_asset(
                        asset
                    )
                ),

                image_bytes=raw,

                mime_type=(
                    infer_mime_type(
                        raw
                    )
                ),

                dna={
                    "asset_id":
                        getattr(
                            asset,
                            "asset_id",
                            "",
                        ),

                    "category":
                        getattr(
                            asset,
                            "category",
                            "",
                        ),

                    "roles":
                        list(
                            getattr(
                                asset,
                                "roles",
                                [],
                            )
                            or []
                        ),

                    "visual_families":
                        list(
                            getattr(
                                asset,
                                "visual_families",
                                [],
                            )
                            or []
                        ),

                    "benefit_families":
                        list(
                            getattr(
                                asset,
                                "benefit_families",
                                [],
                            )
                            or []
                        ),

                    "notes":
                        getattr(
                            asset,
                            "notes",
                            "",
                        ),
                },

                product_lock={},

                user_note=clean_text(
                    getattr(
                        asset,
                        "notes",
                        "",
                    ),
                    1200,
                ),

                source_id=(
                    "local_stc:"
                    +
                    clean_text(
                        getattr(
                            asset,
                            "asset_id",
                            "",
                        ),
                        300,
                    )
                ),

                content_family=(
                    "stc_"
                    +
                    (
                        clean_text(
                            getattr(
                                asset,
                                "category",
                                "",
                            ),
                            100,
                        )
                        or
                        "reference"
                    )
                ),

                source_metadata={
                    "source_type":
                        "local_brand_pack",

                    "permanent":
                        True,

                    "brand_id":
                        "stc_bank",

                    "asset_id":
                        getattr(
                            asset,
                            "asset_id",
                            "",
                        ),

                    "category":
                        getattr(
                            asset,
                            "category",
                            "",
                        ),

                    "resolved_path":
                        str(path),

                    "official":
                        False,
                },

                selection={
                    "final_score":
                        float(
                            getattr(
                                asset,
                                "priority",
                                50,
                            )
                        ),

                    "priority":
                        getattr(
                            asset,
                            "priority",
                            50,
                        ),

                    "selector":
                        "stc_brand_kit_v2",
                },
            )
        )

    if (
        STC_REQUIRE_BRAND_PACK
        and
        STC_FORCE_BRAND_GROUNDING
        and
        not references
    ):

        raise RuntimeError(
            (
                "STC Brand Pack loaded but no physical "
                "reference images were usable."
            )
        )

    return (
        references,
        kit,
        list(
            selected_assets
        ),
    )


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
        for item
        in references
        if item.role
        ==
        "product_reference"
    ]


def reference_score(
    reference: ProductionReference,
) -> float:

    selection = safe_dict(
        reference.selection
    )

    return max(
        safe_float(
            selection.get(
                "final_score"
            ),
            0,
        ),

        safe_float(
            selection.get(
                "base_score"
            ),
            0,
        ),

        safe_float(
            selection.get(
                "score"
            ),
            0,
        ),

        safe_float(
            selection.get(
                "priority"
            ),
            0,
        ),
    )


def unique_references(
    references: Sequence[
        ProductionReference
    ],
) -> List[
    ProductionReference
]:

    output: List[
        ProductionReference
    ] = []

    seen: Set[str] = set()

    for item in references:

        key = (
            clean_text(
                item.source_id,
                500,
            )
            or
            (
                str(
                    len(
                        item.image_bytes
                        or
                        b""
                    )
                )
                +
                ":"
                +
                str(
                    hash(
                        (
                            item.image_bytes
                            or
                            b""
                        )[:128]
                    )
                )
            )
        )

        if key in seen:

            continue

        seen.add(
            key
        )

        output.append(
            item
        )

    return output


def choose_physical_references(
    references: Sequence[
        ProductionReference
    ],
    *,
    limit: int = MAX_PHYSICAL_REFERENCE_IMAGES,
) -> List[
    ProductionReference
]:

    if not SEND_VISUAL_REFERENCES_TO_IMAGE:

        return []

    limit = max(
        0,
        int(
            limit
            or 0
        ),
    )

    if limit <= 0:

        return []

    usable = [
        item
        for item
        in references
        if item.image_bytes
    ]

    role_priority = {

        "product_reference":
            1200,

        "campaign_reference":
            1050,

        "style_reference":
            1000,

        "mixed_reference":
            980,

        "composition_reference":
            950,

        "camera_reference":
            930,

        "lighting_reference":
            910,

        "environment_reference":
            900,

        "color_reference":
            850,
    }

    usable.sort(
        key=lambda item: (
            role_priority.get(
                item.role,
                800,
            )
            +
            reference_score(
                item
            )
        ),
        reverse=True,
    )

    selected: List[
        ProductionReference
    ] = []

    used_families: Set[str] = set()

    #
    # Product references first.
    #

    for item in usable:

        if item.role != "product_reference":

            continue

        selected.append(
            item
        )

        if len(selected) >= limit:

            return unique_references(
                selected
            )[:limit]

    #
    # Then encourage family diversity.
    #

    for item in usable:

        if item in selected:

            continue

        family = clean_text(
            item.content_family,
            200,
        )

        if (
            family
            and
            family in used_families
            and
            len(
                usable
            )
            >
            limit
        ):

            continue

        selected.append(
            item
        )

        if family:

            used_families.add(
                family
            )

        if len(selected) >= limit:

            break

    #
    # Fill if diversity skipped too much.
    #

    if len(selected) < limit:

        for item in usable:

            if item in selected:

                continue

            selected.append(
                item
            )

            if len(selected) >= limit:

                break

    return unique_references(
        selected
    )[:limit]


def build_stc_primary_reference_set(
    *,
    product_refs: Sequence[
        ProductionReference
    ],
    local_refs: Sequence[
        ProductionReference
    ],
    memory_refs: Sequence[
        ProductionReference
    ],
    limit: int = STC_RENDER_REFERENCE_LIMIT,
) -> List[
    ProductionReference
]:

    if not SEND_VISUAL_REFERENCES_TO_IMAGE:

        return []

    limit = max(
        1,
        min(
            STC_RENDER_REFERENCE_LIMIT,
            int(
                limit
                or
                STC_RENDER_REFERENCE_LIMIT
            ),
        ),
    )

    output: List[
        ProductionReference
    ] = []

    #
    # Exact user product has authority when present.
    #

    for item in product_refs:

        if not item.image_bytes:

            continue

        output.append(
            item
        )

        if len(
            unique_references(
                output
            )
        ) >= limit:

            return unique_references(
                output
            )[:limit]

    campaign = [
        item
        for item in local_refs
        if (
            item.role
            ==
            "campaign_reference"
            and
            item.image_bytes
        )
    ]

    style = [
        item
        for item in local_refs
        if (
            item.role
            ==
            "style_reference"
            and
            item.image_bytes
        )
    ]

    service = [
        item
        for item in local_refs
        if (
            item.role
            ==
            "environment_reference"
            and
            item.image_bytes
        )
    ]

    #
    # V5.2 core mix:
    # one DNA + one style + one service.
    #

    for group in (
        campaign[:1],
        style[:1],
        service[:1],
    ):

        output.extend(
            group
        )

        output = unique_references(
            output
        )

        if len(output) >= limit:

            return output[:limit]

    #
    # Fill from remaining permanent assets.
    #

    for item in local_refs:

        if not item.image_bytes:

            continue

        output.append(
            item
        )

        output = unique_references(
            output
        )

        if len(output) >= limit:

            return output[:limit]

    #
    # Last fallback from Brand Memory.
    #

    for item in choose_physical_references(
        memory_refs,
        limit=limit,
    ):

        output.append(
            item
        )

        output = unique_references(
            output
        )

        if len(output) >= limit:

            break

    return output[:limit]


def correction_reference_set(
    *,
    product_refs: Sequence[
        ProductionReference
    ],
    stc_local_refs: Sequence[
        ProductionReference
    ],
    high_alert: bool,
) -> List[
    ProductionReference
]:

    refs: List[
        ProductionReference
    ] = []

    for item in product_refs:

        if item.image_bytes:

            refs.append(
                item
            )

    if high_alert:

        campaign = [
            item
            for item in stc_local_refs
            if (
                item.role
                ==
                "campaign_reference"
                and
                item.image_bytes
            )
        ]

        style = [
            item
            for item in stc_local_refs
            if (
                item.role
                ==
                "style_reference"
                and
                item.image_bytes
            )
        ]

        service = [
            item
            for item in stc_local_refs
            if (
                item.role
                ==
                "environment_reference"
                and
                item.image_bytes
            )
        ]

        #
        # Working image is already present.
        # Favor identity plus execution reference.
        #

        refs.extend(
            campaign[:1]
        )

        if service:

            refs.extend(
                service[:1]
            )

        elif style:

            refs.extend(
                style[:1]
            )

    return unique_references(
        refs
    )[
        :STC_EDIT_REFERENCE_LIMIT
    ]


def reference_dna_payload(
    references: Sequence[
        ProductionReference
    ],
    limit: Optional[int] = None,
) -> List[
    Dict[str, Any]
]:

    if limit is None:

        limit = (
            SMART_REFERENCE_SELECTION_LIMIT
        )

    limit = max(
        1,
        min(
            10,
            int(
                limit
                or 1
            ),
        ),
    )

    output: List[
        Dict[str, Any]
    ] = []

    for item in list(
        references
    )[:limit]:

        output.append(
            {
                "reference_id":
                    item.source_id,

                "role":
                    item.role,

                "content_family":
                    item.content_family,

                "selection_score":
                    reference_score(
                        item
                    ),

                "official_source":
                    bool(
                        safe_dict(
                            item.source_metadata
                        ).get(
                            "official",
                            False,
                        )
                    ),

                "permanent_local_reference":
                    bool(
                        safe_dict(
                            item.source_metadata
                        ).get(
                            "permanent",
                            False,
                        )
                    ),

                "dna":
                    safe_dict(
                        item.dna
                    ),

                "note":
                    clean_text(
                        item.user_note,
                        500,
                    ),
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

        for value in safe_list(
            item.product_lock.get(
                "must_remain_identical"
            )
        ):

            text = clean_text(
                value,
                500,
            )

            if (
                text
                and
                text not in rules
            ):

                rules.append(
                    text
                )

    return {
        "enabled":
            bool(count),

        "reference_count":
            count,

        "must_remain_identical":
            rules[:20],

        "environment_may_change":
            True,

        "lighting_may_adapt":
            True,

        "logos_must_not_be_generated":
            True,
    }


# =========================================================
# STC KIT TEXT CONTEXT
# =========================================================

def build_stc_brand_kit_context(
    kit: Optional[Any],
    *,
    request: str,
    selected_assets: Sequence[Any],
) -> Dict[str, Any]:

    if kit is None:

        return {}

    selected = []

    for item in list(
        selected_assets
    )[:7]:

        selected.append(
            {
                "asset_id":
                    getattr(
                        item,
                        "asset_id",
                        "",
                    ),

                "category":
                    getattr(
                        item,
                        "category",
                        "",
                    ),

                "roles":
                    list(
                        getattr(
                            item,
                            "roles",
                            [],
                        )
                        or []
                    ),

                "notes":
                    clean_text(
                        getattr(
                            item,
                            "notes",
                            "",
                        ),
                        350,
                    ),
            }
        )

    return {
        "brand_id":
            "stc_bank",

        "benefit_family":
            detect_stc_benefit_family(
                request
            ),

        "visual_family":
            stc_visual_family_for_brand_kit(
                request
            ),

        "selected_assets":
            selected,
    }


# =========================================================
# BRAND CONTEXT COMPACTION
# =========================================================

def build_enriched_brand_context(
    *,
    brand_context: Any,
    brand_visual_profile: Any,
    references: Sequence[
        ProductionReference
    ],
    stc_brand_kit_context: Optional[
        Dict[str, Any]
    ] = None,
) -> Dict[str, Any]:

    context = safe_dict(
        brand_context
    )

    profile = safe_dict(
        brand_visual_profile
    )

    base_profile = safe_dict(
        context.get(
            "profile"
        )
    )

    return {
        "brand_id":
            context.get(
                "brand_id",
                "",
            ),

        "profile": {
            "brand_label":
                base_profile.get(
                    "brand_label",
                    "",
                ),

            "creative_positioning":
                safe_list(
                    base_profile.get(
                        "creative_positioning"
                    )
                )[:8],

            "visual_dna":
                safe_list(
                    base_profile.get(
                        "visual_dna"
                    )
                )[:8],
        },

        "rules":
            safe_list(
                context.get(
                    "rules"
                )
            )[:12],

        "visual_profile": {
            "camera_patterns":
                safe_list(
                    profile.get(
                        "camera_patterns"
                    )
                )[:4],

            "lighting_patterns":
                safe_list(
                    profile.get(
                        "lighting_patterns"
                    )
                )[:4],

            "material_patterns":
                safe_list(
                    profile.get(
                        "material_patterns"
                    )
                )[:4],

            "composition_patterns":
                safe_list(
                    profile.get(
                        "composition_patterns"
                    )
                )[:4],
        },

        "runtime_reference_count":
            len(references),

        "stc_permanent_brand_kit":
            (
                stc_brand_kit_context
                or
                {}
            ),
    }


# =========================================================
# CREATIVE RENDER BRIEF
# =========================================================

def creative_finalist_jury_payload(
    creative_direction: Any,
) -> Dict[str, Any]:

    creative = safe_dict(
        creative_direction
    )

    debate = safe_dict(
        creative.get(
            "debate"
        )
    )

    jury = safe_dict(
        debate.get(
            "finalist_jury"
        )
    )

    if jury:

        return jury

    return safe_dict(
        creative.get(
            "finalist_jury"
        )
    )


def build_render_brief(
    *,
    creative_direction: Any,
    camera_direction: Any,
) -> Dict[str, Any]:

    creative = safe_dict(
        creative_direction
    )

    camera = safe_dict(
        camera_direction
    )

    jury = creative_finalist_jury_payload(
        creative
    )

    debate = safe_dict(
        creative.get(
            "debate"
        )
    )

    debate_camera = safe_dict(
        debate.get(
            "camera_director"
        )
    )

    supporting = [
        clean_text(
            item,
            450,
        )
        for item
        in safe_list(
            creative.get(
                "supporting_elements"
            )
        )[:3]
        if clean_text(
            item,
            450,
        )
    ]

    risks = [
        clean_text(
            item,
            450,
        )
        for item
        in safe_list(
            creative.get(
                "risks"
            )
        )[:4]
        if clean_text(
            item,
            450,
        )
    ]

    drift = [
        clean_text(
            item,
            450,
        )
        for item
        in safe_list(
            jury.get(
                "do_not_drift_into"
            )
        )[:5]
        if clean_text(
            item,
            450,
        )
    ]

    return {
        "concept_id":
            clean_text(
                creative.get(
                    "concept_id",
                    "",
                ),
                100,
            ),

        "title":
            clean_text(
                creative.get(
                    "title",
                    "",
                ),
                500,
            ),

        "campaign_hook":
            clean_text(
                creative.get(
                    "campaign_hook",
                    "",
                ),
                900,
            ),

        "core_idea":
            clean_text(
                creative.get(
                    "core_idea",
                    "",
                ),
                1200,
            ),

        "marketing_message":
            clean_text(
                creative.get(
                    "marketing_message",
                    "",
                ),
                700,
            ),

        "visual_metaphor":
            clean_text(
                creative.get(
                    "visual_metaphor",
                    "",
                ),
                1000,
            ),

        "visual_mechanism_type":
            clean_text(
                creative.get(
                    "visual_mechanism_type",
                    "",
                ),
                500,
            ),

        "why_not_generic":
            clean_text(
                creative.get(
                    "why_not_generic",
                    "",
                ),
                700,
            ),

        "environment":
            clean_text(
                creative.get(
                    "environment",
                    "",
                ),
                900,
            ),

        "hero_element":
            clean_text(
                creative.get(
                    "hero_element",
                    "",
                ),
                700,
            ),

        "supporting_elements":
            supporting,

        "camera_angle":
            (
                clean_text(
                    camera.get(
                        "camera_angle",
                        "",
                    ),
                    600,
                )
                or
                clean_text(
                    debate_camera.get(
                        "camera_angle",
                        "",
                    ),
                    600,
                )
                or
                clean_text(
                    creative.get(
                        "camera_angle",
                        "",
                    ),
                    600,
                )
            ),

        "lens":
            (
                clean_text(
                    camera.get(
                        "lens",
                        "",
                    ),
                    200,
                )
                or
                clean_text(
                    debate_camera.get(
                        "lens",
                        "",
                    ),
                    200,
                )
                or
                clean_text(
                    creative.get(
                        "lens",
                        "",
                    ),
                    200,
                )
            ),

        "perspective":
            (
                clean_text(
                    camera.get(
                        "perspective",
                        "",
                    ),
                    700,
                )
                or
                clean_text(
                    camera.get(
                        "perspective_type",
                        "",
                    ),
                    700,
                )
                or
                clean_text(
                    debate_camera.get(
                        "perspective",
                        "",
                    ),
                    700,
                )
                or
                clean_text(
                    debate_camera.get(
                        "perspective_type",
                        "",
                    ),
                    700,
                )
                or
                clean_text(
                    creative.get(
                        "perspective",
                        "",
                    ),
                    700,
                )
            ),

        "lighting":
            clean_text(
                creative.get(
                    "lighting",
                    "",
                ),
                700,
            ),

        "negative_space":
            clean_text(
                creative.get(
                    "negative_space",
                    "",
                ),
                600,
            ),

        "brand_logic":
            clean_text(
                creative.get(
                    "brand_logic",
                    "",
                ),
                800,
            ),

        "production_method":
            clean_text(
                creative.get(
                    "production_method",
                    "",
                ),
                300,
            ),

        "production_instruction":
            clean_text(
                (
                    jury.get(
                        "production_instruction"
                    )
                    or
                    jury.get(
                        "production_direction"
                    )
                    or
                    ""
                ),
                1200,
            ),

        "do_not_drift_into":
            drift,

        "risks":
            risks,
    }


# =========================================================
# BRITTLE MECHANISM DETECTION
# =========================================================

BRITTLE_MECHANISM_MARKERS = [

    "half-digital",
    "half digital",
    "half-physical",
    "half physical",
    "screen plane",
    "crossing the screen",
    "crosses the screen",
    "through the screen",
    "emerges from screen",
    "emerging from screen",
    "comes out of the screen",
    "digital half",
    "physical half",
    "crossing glass",
    "through the glass",

    "نصف رقمي",
    "نصف رقمية",
    "نصف مادي",
    "نصف مادية",
    "يعبر الشاشة",
    "تعبر الشاشة",
    "عبر الشاشة",
    "يخرج من الشاشة",
    "تخرج من الشاشة",
    "اختراق الشاشة",
    "تعبر الزجاج",
    "يعبر الزجاج",
    "عبر الزجاج",
]


def render_brief_text(
    render_brief: Any,
) -> str:

    brief = safe_dict(
        render_brief
    )

    fields = [
        brief.get(
            "title",
            "",
        ),
        brief.get(
            "campaign_hook",
            "",
        ),
        brief.get(
            "core_idea",
            "",
        ),
        brief.get(
            "visual_metaphor",
            "",
        ),
        brief.get(
            "visual_mechanism_type",
            "",
        ),
        brief.get(
            "hero_element",
            "",
        ),
        brief.get(
            "production_instruction",
            "",
        ),
        " ".join(
            safe_list(
                brief.get(
                    "supporting_elements"
                )
            )
        ),
    ]

    return "\n".join(
        clean_text(
            item,
            3000,
        )
        for item in fields
        if clean_text(
            item,
            3000,
        )
    )


def requires_production_safe_reinterpretation(
    render_brief: Any,
) -> bool:

    source = render_brief_text(
        render_brief
    )

    return contains_any(
        source,
        BRITTLE_MECHANISM_MARKERS,
    )


def production_safe_reinterpretation_instruction(
    *,
    original_request: str,
    active: bool,
) -> str:

    if not active:

        return """
PRODUCTION INTERPRETATION
-------------------------
Execute the approved visual mechanism directly and cleanly.
Do not add extra concepts.
""".strip()

    benefit = (
        detect_stc_benefit_family(
            original_request
        )
        if
        is_stc_bank_request(
            original_request
        )
        else
        ""
    )

    merchant = ""

    if benefit == "merchant_payments":

        merchant = """
For merchant payments:
- BOTH online/e-commerce and physical payment acceptance
  must remain visually understandable.
- They must feel like parts of ONE merchant ecosystem.
- Do not solve this with an ordinary checkout tableau.
- Do not solve this with POS foreground + worker packing
  in the background.
""".strip()

    return f"""
PRODUCTION-SAFE REINTERPRETATION: ACTIVE
----------------------------------------

The approved concept contains a visually fragile geometry.

Preserve:
- the commercial proposition
- the campaign hook
- the hero relationship
- the intended visual meaning
- the camera hierarchy
- the brand world

BUT:

Do NOT force impossible or brittle geometry merely because
the concept text described it literally.

A phrase such as:
half-digital / half-physical,
crossing a screen plane,
object emerging perfectly through glass,
or seamless impossible digital-to-real continuity

may be translated into a simpler PHYSICALLY BELIEVABLE
single-frame equivalent.

The replacement must remain:
- one dominant visual mechanism
- immediately legible
- premium
- photographic
- campaign-level
- faithful to the same commercial meaning

Do NOT turn simplification into a generic lifestyle scene.

{merchant}
""".strip()


# =========================================================
# NEGATIVE PROMPT
# =========================================================

def base_negative_prompt() -> str:

    return """
HARD NEGATIVE LOCK:

No generated headline.
No readable advertising copy.
No generated STC logo.
No generated bank logo.
No wordmark.
No watermark.
No fake card-brand symbol.
No fake banking UI.
No fake account balance.
No financial numbers.
No readable receipt.
No readable parcel label.
No readable storefront signage.

If a screen exists:
no letters,
no numbers,
no brand marks,
no banking interface,
no readable buttons.
Use clean visual content, reflections or icon-free imagery only.

No floating phone.
No floating card.
No floating POS.
No hologram.
No HUD.
No network line.
No glowing payment line.
No laser path.
No random particles.
No generic fintech graphics.

No global purple wash unless the chosen STC tier explicitly
requires physical purple architecture.

No plastic skin.
No broken fingers.
No impossible grip.
No broken scale.
No bad contact shadow.
No fake reflection.
No contradictory perspective.

No generic boutique checkout tableau.
No luxury wooden counter cliché.
No customer + POS + merchant + counter + packing scene.
""".strip()


# =========================================================
# PHYSICAL REFERENCE INSTRUCTION
# =========================================================

def physical_reference_instruction(
    references: Sequence[
        ProductionReference
    ],
) -> str:

    if not references:

        return """
REFERENCE POLICY:
No physical reference images supplied.
""".strip()

    roles = []

    for item in references:

        roles.append(
            (
                clean_text(
                    item.source_id,
                    250,
                )
                +
                " | "
                +
                clean_text(
                    item.role,
                    100,
                )
            )
        )

    return """
REFERENCE POLICY:

The attached images are visual references, not scene templates.

Learn:
- brand maturity
- lighting discipline
- material quality
- camera restraint
- composition quality
- Saudi commercial tone

Do NOT:
- clone their exact scene
- copy their exact people
- copy their exact layout
- copy any logo
- copy any text
- copy any UI

A product_reference is the only reference whose physical
product geometry may be treated as authoritative.

References:
""" + "\n".join(
        "- " + item
        for item in roles
    )


# =========================================================
# QUALITY-FIRST SHORT BLUEPRINT V5.2
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

    request = clean_text(
        request,
        5000,
    )

    render_brief = (
        build_render_brief(
            creative_direction=(
                creative_direction
            ),
            camera_direction=(
                camera_direction
            ),
        )
    )

    safe_reinterpretation = (
        requires_production_safe_reinterpretation(
            render_brief
        )
    )

    stc_request = (
        is_stc_bank_request(
            request
        )
    )

    benefit_family = (
        detect_stc_benefit_family(
            request
        )
        if stc_request
        else ""
    )

    stc_section = ""

    if stc_request:

        merchant_lock = ""

        if benefit_family == "merchant_payments":

            merchant_lock = """
ONE CONNECTED MERCHANT ECOSYSTEM
--------------------------------
The frame must communicate online/e-commerce commerce and
physical point-of-sale acceptance as one connected commercial
proposition.

Do not merely place two related props in the same room.

Do not use:
customer + POS + counter + merchant + packing activity

as the campaign mechanism.
""".strip()

        stc_section = f"""
PERMANENT STC BANK BRAND DNA
----------------------------
Use the attached STC references as visual DNA.
Synthesize their maturity; never clone a reference.

STC brand identity without generated logo should come from:
- premium Saudi commercial art direction
- disciplined composition
- intentional color restraint
- material quality
- confident photography
- sophisticated negative space
- subtle STC-coded accents where physically motivated

{build_stc_scene_tier_instruction(request)}

SUBJECT-PROTECTION LAW
----------------------
Skin, clothing, product materials and natural objects retain
realistic color and texture.

TEXT-FREE LAW
-------------
IMAGE ONLY.
No generated copy.
No generated logo.
No wordmark.
No readable signage.

REAL-APP LAW
------------
Never invent readable banking UI.
Never invent balances, numbers, buttons or financial data.
If a screen is needed, make its visual content non-readable
and non-banking.

ANTI-REPETITION LAW
-------------------
Do not return the known generic:
luxury counter + POS + merchant + customer + packing/tablet.

NO-CLONE LAW
------------
References teach visual DNA only.
Never recreate an old STC scene.

FINAL CREATIVE JURY LOCK
------------------------
The approved creative direction is authoritative at the
STRATEGY level. Production may simplify fragile geometry,
but may not replace the commercial proposition.

{merchant_lock}
""".strip()

    brief_json = compact_json(
        render_brief,
        4400,
    )

    brand_rules = compact_json(
        {
            "rules":
                safe_list(
                    safe_dict(
                        brand_context
                    ).get(
                        "rules"
                    )
                )[:8],

            "visual_profile":
                safe_dict(
                    safe_dict(
                        brand_context
                    ).get(
                        "visual_profile"
                    )
                ),

            "stc_brand_kit":
                safe_dict(
                    safe_dict(
                        brand_context
                    ).get(
                        "stc_permanent_brand_kit"
                    )
                ),
        },
        1400,
    )

    ref_dna = compact_json(
        references,
        1200,
    )

    product = compact_json(
        product_lock,
        900,
    )

    reinterpretation = (
        production_safe_reinterpretation_instruction(
            original_request=request,
            active=safe_reinterpretation,
        )
    )

    prompt = f"""
XPAND MASTERPIECE RENDER CONTRACT V5.2
======================================

GOAL
----
Create ONE premium campaign key visual.

Do not brainstorm.
Do not add a second concept.
Do not narrate.
Render the approved commercial idea with the simplest
physically convincing execution.

ORIGINAL REQUEST
----------------
{request}

APPROVED RENDER BRIEF
---------------------
{brief_json}

{reinterpretation}

CAMERA LOCK
-----------
Use the camera, lens and perspective from the render brief.
If one field is empty, choose one coherent professional
camera system only.
Never mix contradictory lens or perspective logic.

COMPOSITION LOCK
----------------
ONE dominant hero relationship.
ONE advertising mechanism.
Remove non-essential props.
Foreground, midground and background must support the same idea.
Maintain believable scale, depth, occlusion and contact.

PHOTOGRAPHIC REALISM
--------------------
High-budget commercial photography.
Correct anatomy.
Correct hands.
Correct scale.
Correct object support.
Real material roughness.
Natural skin.
Real contact shadows.
Coherent reflections.
Coherent light direction.
No polished AI-plastic look.

LIGHTING
--------
One motivated lighting logic.
Natural or premium commercial directional light.
Controlled negative fill.
Believable bounce.
Material-specific highlights.
No random glow.

ADVERTISING STANDARD
--------------------
The image must communicate before typography is added.
It must feel intentionally conceived as a bank campaign,
not documentary photography and not a stock-photo transaction.

BRAND CONTEXT
-------------
{brand_rules}

REFERENCE DNA SUMMARY
---------------------
{ref_dna}

PRODUCT LOCK
------------
{product}

{stc_section}

{safe_frame_instruction(aspect_ratio)}

FINAL IMAGE LAW
---------------
IMAGE ONLY.
NO TEXT.
NO LOGO.
NO FAKE UI.
NO DECORATIVE FINTECH GRAPHICS.
NO GENERIC FALLBACK SCENE.

Create one coherent premium finished frame.
""".strip()

    return fit_prompt_for_api(
        prompt,
        label=(
            "production_blueprint_v52"
        ),
        budget=(
            COMPILED_PROMPT_BUDGET
        ),
    )


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

    if target not in {
        TARGET_GEMINI,
        TARGET_OPENAI,
    }:

        target = TARGET_GEMINI

    creative_direction = (
        creative_direction
        or
        {}
    )

    camera_direction = (
        camera_direction
        or
        {}
    )

    render_brief = (
        build_render_brief(
            creative_direction=(
                creative_direction
            ),
            camera_direction=(
                camera_direction
            ),
        )
    )

    safe_reinterpretation = (
        requires_production_safe_reinterpretation(
            render_brief
        )
    )

    blueprint = (
        build_quality_first_blueprint(

            request=request,

            creative_direction=(
                creative_direction
            ),

            brand_context=(
                brand_context
                or
                {}
            ),

            references=(
                references
                or
                []
            ),

            camera_direction=(
                camera_direction
            ),

            product_lock=(
                product_lock
                or
                {}
            ),

            aspect_ratio=(
                aspect_ratio
            ),
        )
    )

    return CompiledPrompt(

        target=target,

        prompt=blueprint,

        negative_prompt=(
            base_negative_prompt()
        ),

        metadata={
            "compiler":
                "xpand_production_v52",

            "prompt_chars":
                len(
                    blueprint
                ),

            "prompt_budget":
                COMPILED_PROMPT_BUDGET,

            "aspect_ratio":
                aspect_ratio,

            "nano_banana_2":
                True,

            "permanent_stc_brand_grounding":
                True,

            "render_brief":
                render_brief,

            "production_safe_reinterpretation":
                safe_reinterpretation,

            "general_reference_limit":
                SMART_REFERENCE_SELECTION_LIMIT,

            "general_physical_reference_limit":
                MAX_PHYSICAL_REFERENCE_IMAGES,

            "stc_brand_pack_load_limit":
                MAX_STC_PHYSICAL_REFERENCE_IMAGES,

            "stc_render_reference_limit":
                STC_RENDER_REFERENCE_LIMIT,

            "stc_edit_reference_limit":
                STC_EDIT_REFERENCE_LIMIT,
        },
    )


# =========================================================
# GEMINI IMAGE API
# =========================================================

def gemini_multi_reference_edit(
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
    output_image_size: str = "1K",
    model_override: Optional[str] = None,
    max_reference_images: Optional[int] = None,
) -> GeneratedImage:

    if not GEMINI_API_KEY:

        raise RuntimeError(
            "GEMINI_API_KEY missing"
        )

    model = clean_text(
        (
            model_override
            or
            NANO_BANANA_2_MODEL
        ),
        300,
    )

    if not model:

        model = (
            NANO_BANANA_2_MODEL
        )

    requested_size = clean_text(
        output_image_size,
        50,
    ).upper()

    if requested_size not in {
        "1K",
        "2K",
        "4K",
    }:

        requested_size = "1K"

    if max_reference_images is None:

        max_reference_images = (
            MAX_PHYSICAL_REFERENCE_IMAGES
        )

    max_reference_images = max(
        0,
        min(
            8,
            int(
                max_reference_images
                or 0
            ),
        ),
    )

    selected_refs = [
        item
        for item
        in unique_references(
            references
        )
        if item.image_bytes
    ][
        :max_reference_images
    ]

    full_prompt = (
        clean_text(
            prompt,
            20000,
        )
        +
        "\n\n"
        +
        physical_reference_instruction(
            selected_refs
        )
        +
        "\n\n"
        +
        base_negative_prompt()
        +
        "\n\n"
        +
        safe_frame_instruction(
            aspect_ratio
        )
    )

    full_prompt = fit_prompt_for_api(
        full_prompt,
        label=pass_name,
        budget=(
            IMAGE_CALL_PROMPT_BUDGET
        ),
    )

    inputs: List[
        Dict[str, Any]
    ] = [
        {
            "type":
                "text",

            "text":
                full_prompt,
        }
    ]

    if (
        working_image is not None
        and
        working_image.image_bytes
    ):

        inputs.append(
            {
                "type":
                    "image",

                "mime_type":
                    (
                        working_image.mime_type
                        or
                        "image/jpeg"
                    ),

                "data":
                    base64.b64encode(
                        working_image.image_bytes
                    ).decode(
                        "ascii"
                    ),
            }
        )

    for reference in selected_refs:

        inputs.append(
            {
                "type":
                    "image",

                "mime_type":
                    (
                        reference.mime_type
                        or
                        "image/jpeg"
                    ),

                "data":
                    base64.b64encode(
                        reference.image_bytes
                    ).decode(
                        "ascii"
                    ),
            }
        )

    response = requests.post(

        GEMINI_INTERACTIONS_URL,

        headers={
            "x-goog-api-key":
                GEMINI_API_KEY,

            "Content-Type":
                "application/json",
        },

        json={
            "model":
                model,

            "input":
                inputs,

            "response_format": {
                "type":
                    "image",

                "aspect_ratio":
                    aspect_ratio,

                "image_size":
                    requested_size,

                "mime_type":
                    "image/jpeg",
            },
        },

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

        raise RuntimeError(
            (
                "Gemini image call failed"
                +
                " | model="
                +
                model
                +
                " | response="
                +
                clean_text(
                    response_data,
                    3200,
                )
            )
        )

    images = find_images_in_response(
        response_data
    )

    if not images:

        raise RuntimeError(
            (
                "Gemini returned no image"
                +
                " | model="
                +
                model
                +
                " | response="
                +
                clean_text(
                    response_data,
                    2600,
                )
            )
        )

    image_bytes, mime_type = (
        images[0]
    )

    is_pro_model = bool(
        model
        ==
        NANO_BANANA_PRO_MODEL
    )

    result = GeneratedImage(

        image_bytes=image_bytes,

        mime_type=(
            mime_type
            or
            "image/jpeg"
        ),

        provider="google",

        model=model,

        prompt=full_prompt,

        original_prompt=full_prompt,

        aspect_ratio=aspect_ratio,

        image_size=requested_size,

        quality="high",

        route_reason=(
            "XPAND Production V5.2"
            +
            " | "
            +
            pass_name
            +
            " | "
            +
            model
        ),

        request_id=(
            clean_text(
                response_data.get(
                    "id",
                    "",
                ),
                300,
            )
            or
            (
                "xpand-v52-"
                +
                uuid.uuid4().hex[:12]
            )
        ),

        metadata={
            "production_engine":
                ENGINE_VERSION,

            "pass_name":
                pass_name,

            "working_image_used":
                bool(
                    working_image
                    is not None
                ),

            "physical_reference_count":
                len(
                    selected_refs
                ),

            "physical_reference_ids": [
                item.source_id
                for item
                in selected_refs
            ],

            "nano_banana_2":
                not is_pro_model,

            "nano_banana_pro":
                is_pro_model,

            "provider_native_resolution":
                requested_size,

            "aspect_ratio":
                aspect_ratio,

            "model":
                model,

            "prompt_chars":
                len(
                    full_prompt
                ),
        },
    )

    return result


#
# Historical compatibility alias.
#

openai_multi_reference_edit = (
    gemini_multi_reference_edit
)


# =========================================================
# HIGH QUALITY GENERATION
# =========================================================

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
    pass_name: str = (
        "quality_first_generation"
    ),
    output_image_size: str = "1K",
    model_override: Optional[str] = None,
    max_physical_references: Optional[int] = None,
) -> GeneratedImage:

    physical_refs = list(
        visual_refs
    )

    existing_ids = {
        item.source_id
        for item
        in physical_refs
        if item.source_id
    }

    for product_ref in product_refs:

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

    physical_refs = unique_references(
        physical_refs
    )

    if max_physical_references is None:

        max_physical_references = (
            MAX_PHYSICAL_REFERENCE_IMAGES
        )

    physical_refs = physical_refs[
        :max(
            0,
            int(
                max_physical_references
                or 0
            ),
        )
    ]

    return gemini_multi_reference_edit(

        working_image=None,

        references=physical_refs,

        prompt=compiled.prompt,

        aspect_ratio=aspect_ratio,

        pass_name=pass_name,

        output_image_size=(
            output_image_size
        ),

        model_override=(
            model_override
        ),

        max_reference_images=(
            max_physical_references
        ),
    )


# =========================================================
# QA SCHEMA
# =========================================================

QA_SCORE_PROPERTIES = {
    key: {
        "type":
            "number",
    }
    for key
    in QA_WEIGHTS
}


QA_FLAGS_SCHEMA = {

    "type":
        "object",

    "additionalProperties":
        False,

    "properties": {

        "generic_scene_detected": {
            "type":
                "boolean",
        },

        "literal_counter_tableau_detected": {
            "type":
                "boolean",
        },

        "repeated_scene_risk": {
            "type":
                "boolean",
        },

        "brand_identity_weak": {
            "type":
                "boolean",
        },

        "merchant_fusion_failed": {
            "type":
                "boolean",
        },

        "reference_cloning_detected": {
            "type":
                "boolean",
        },

        "unwanted_text_or_logo": {
            "type":
                "boolean",
        },

        "fake_banking_ui": {
            "type":
                "boolean",
        },
    },

    "required": [
        "generic_scene_detected",
        "literal_counter_tableau_detected",
        "repeated_scene_risk",
        "brand_identity_weak",
        "merchant_fusion_failed",
        "reference_cloning_detected",
        "unwanted_text_or_logo",
        "fake_banking_ui",
    ],
}


QA_SCHEMA = {

    "type":
        "object",

    "additionalProperties":
        False,

    "properties": {

        "scores": {
            "type":
                "object",

            "additionalProperties":
                False,

            "properties":
                QA_SCORE_PROPERTIES,

            "required":
                list(
                    QA_WEIGHTS.keys()
                ),
        },

        "flags":
            QA_FLAGS_SCHEMA,

        "strengths": {
            "type":
                "array",

            "items": {
                "type":
                    "string",
            },
        },

        "problems": {
            "type":
                "array",

            "items": {
                "type":
                    "string",
            },
        },

        "critical_blockers": {
            "type":
                "array",

            "items": {
                "type":
                    "string",
            },
        },

        "correction_instruction": {
            "type":
                "string",
        },

        "decision": {
            "type":
                "string",

            "enum": [
                "approve",
                "correct",
                "rebuild",
            ],
        },
    },

    "required": [
        "scores",
        "flags",
        "strengths",
        "problems",
        "critical_blockers",
        "correction_instruction",
        "decision",
    ],
}


# =========================================================
# QA SCORE
# =========================================================

def calculate_qa_score(
    scores: Dict[str, Any],
) -> Tuple[
    float,
    Dict[str, float],
]:

    normalized: Dict[
        str,
        float
    ] = {}

    total = 0.0

    for key, weight in (
        QA_WEIGHTS.items()
    ):

        value = clamp_score(
            scores.get(
                key,
                0,
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


def qa_target_for_request(
    original_request: str,
) -> float:

    if (
        STC_HIGH_ALERT_ENABLED
        and
        is_stc_bank_request(
            original_request
        )
    ):

        return STC_QA_TARGET_SCORE

    return QA_TARGET_SCORE


def qa_release_floor_for_request(
    original_request: str,
) -> float:

    if (
        STC_HIGH_ALERT_ENABLED
        and
        is_stc_bank_request(
            original_request
        )
    ):

        return STC_QA_RELEASE_FLOOR

    return QA_RELEASE_FLOOR


# =========================================================
# QA BLOCKER SANITIZER
# =========================================================
#
# When V5.2 explicitly activated a production-safe
# reinterpretation, QA may not reject the result ONLY
# because a brittle literal geometry disappeared.
#
# This does not remove:
# - service failure
# - merchant fusion failure
# - generic scene
# - text/logo
# - brand failure
# - realism failure
#
# It only prevents "you did not literally cross the exact
# screen plane" from becoming a false blocker.
#

def sanitize_explicit_qa_blockers(
    blockers: Any,
    *,
    compiled_prompt: CompiledPrompt,
) -> List[str]:

    values = [
        clean_text(
            item,
            1000,
        )
        for item
        in safe_list(
            blockers
        )
        if clean_text(
            item,
            1000,
        )
    ]

    safe_reinterpretation = bool(
        safe_dict(
            compiled_prompt.metadata
        ).get(
            "production_safe_reinterpretation",
            False,
        )
    )

    if not safe_reinterpretation:

        return values

    literal_only_markers = [
        "half-digital",
        "half digital",
        "half-physical",
        "half physical",
        "screen plane",
        "crossing the screen",
        "crossing screen",
        "through the screen",
        "crossing the glass",
        "through the glass",
        "تعبر الزجاج",
        "يعبر الزجاج",
        "نصف رقمي",
        "نصف مادي",
    ]

    protected: List[str] = []

    for item in values:

        lower = normalize_text(
            item
        )

        literal_only = any(
            normalize_text(
                marker
            )
            in lower
            for marker
            in literal_only_markers
        )

        #
        # Never remove a blocker that also says the
        # service/message/fusion itself failed.
        #

        semantic_failure = contains_any(
            item,
            [
                "merchant fusion",
                "service",
                "message",
                "e-commerce",
                "ecommerce",
                "point of sale",
                "pos",
                "generic",
                "brand",
                "text",
                "logo",
                "ui",
                "realism",
                "anatomy",
                "perspective",
                "التجارة",
                "نقاط البيع",
                "المعنى",
                "الخدمة",
            ],
        )

        if (
            literal_only
            and
            not semantic_failure
        ):

            continue

        protected.append(
            item
        )

    return protected


# =========================================================
# QA BLOCKERS
# =========================================================

def detect_critical_blockers(
    *,
    scores: Dict[str, float],
    explicit_failures: Any,
    flags: Any,
    product_lock: Any,
    original_request: str = "",
) -> List[str]:

    blockers: List[str] = []

    for value in safe_list(
        explicit_failures
    ):

        text = clean_text(
            value,
            900,
        )

        if text:

            blockers.append(
                text
            )

    thresholds = {

        "concept_execution":
            QA_CRITICAL_SCORE_FLOOR,

        "message_clarity_without_text":
            max(
                QA_CRITICAL_SCORE_FLOOR,
                68.0,
            ),

        "realism":
            max(
                QA_CRITICAL_SCORE_FLOOR,
                68.0,
            ),

        "camera_perspective":
            QA_CRITICAL_SCORE_FLOOR,

        "advertising_readiness":
            max(
                QA_CRITICAL_SCORE_FLOOR,
                70.0,
            ),
    }

    for key, minimum in (
        thresholds.items()
    ):

        if (
            clamp_score(
                scores.get(
                    key,
                    0,
                )
            )
            <
            minimum
        ):

            blockers.append(
                (
                    key
                    +
                    "_below_"
                    +
                    str(
                        int(
                            minimum
                        )
                    )
                )
            )

    stc_request = (
        is_stc_bank_request(
            original_request
        )
    )

    flag_data = safe_dict(
        flags
    )

    if stc_request:

        stc_thresholds = {

            "brand_alignment":
                78.0,

            "brand_identity_strength":
                80.0,

            "scene_originality":
                80.0,

            "advertising_readiness":
                82.0,

            "concept_execution":
                80.0,

            "text_logo_compliance":
                95.0,
        }

        for key, minimum in (
            stc_thresholds.items()
        ):

            if (
                clamp_score(
                    scores.get(
                        key,
                        0,
                    )
                )
                <
                minimum
            ):

                blockers.append(
                    (
                        "stc_"
                        +
                        key
                        +
                        "_below_"
                        +
                        str(
                            int(
                                minimum
                            )
                        )
                    )
                )

        if (
            clamp_score(
                scores.get(
                    "purple_restraint",
                    0,
                )
            )
            <
            75.0
        ):

            blockers.append(
                "stc_purple_overuse"
            )

        benefit_family = (
            detect_stc_benefit_family(
                original_request
            )
        )

        if (
            benefit_family
            ==
            "merchant_payments"
            and
            clamp_score(
                scores.get(
                    "service_integration",
                    0,
                )
            )
            <
            82.0
        ):

            blockers.append(
                "stc_merchant_service_integration_weak"
            )

        if (
            STC_REJECT_GENERIC_SCENES
            and
            flag_data.get(
                "generic_scene_detected"
            )
        ):

            blockers.append(
                "stc_generic_scene_detected"
            )

        if flag_data.get(
            "literal_counter_tableau_detected"
        ):

            blockers.append(
                "stc_literal_counter_tableau"
            )

        if (
            STC_REJECT_REPEATED_SCENES
            and
            flag_data.get(
                "repeated_scene_risk"
            )
        ):

            blockers.append(
                "stc_repeated_scene_risk"
            )

        if flag_data.get(
            "brand_identity_weak"
        ):

            blockers.append(
                "stc_brand_identity_weak"
            )

        if (
            benefit_family
            ==
            "merchant_payments"
            and
            flag_data.get(
                "merchant_fusion_failed"
            )
        ):

            blockers.append(
                "stc_merchant_fusion_failed"
            )

        if flag_data.get(
            "reference_cloning_detected"
        ):

            blockers.append(
                "stc_reference_cloning"
            )

        if flag_data.get(
            "unwanted_text_or_logo"
        ):

            blockers.append(
                "stc_unwanted_text_or_logo"
            )

        if flag_data.get(
            "fake_banking_ui"
        ):

            blockers.append(
                "stc_fake_banking_ui"
            )

    lock = safe_dict(
        product_lock
    )

    if lock.get(
        "enabled"
    ):

        if (
            clamp_score(
                scores.get(
                    "reference_adherence",
                    0,
                )
            )
            <
            65.0
        ):

            blockers.append(
                "product_reference_fidelity"
            )

    return dedupe_strings(
        blockers,
        limit=50,
    )


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
) -> str:

    stc_request = (
        is_stc_bank_request(
            original_request
        )
    )

    safe_reinterpretation = bool(
        safe_dict(
            compiled_prompt.metadata
        ).get(
            "production_safe_reinterpretation",
            False,
        )
    )

    render_brief = safe_dict(
        safe_dict(
            compiled_prompt.metadata
        ).get(
            "render_brief"
        )
    )

    reinterpretation_audit = ""

    if safe_reinterpretation:

        reinterpretation_audit = """
PRODUCTION-SAFE INTERPRETATION AUDIT
------------------------------------

The renderer intentionally simplified a brittle literal
geometry while preserving the approved campaign proposition.

IMPORTANT:

Do NOT require literal impossible geometry such as:
- exact half-digital / half-physical object
- exact object crossing a screen plane
- exact seamless object emerging through glass

Judge SEMANTIC FIDELITY instead.

A physically credible equivalent may score highly when:
- the same commercial idea survives
- the same service benefit survives
- the visual mechanism remains strong
- the result is not generic
- the result is campaign-ready

Do NOT forgive:
- merchant fusion failure
- service ambiguity
- generic scene
- weak brand identity
- unwanted text/logo
- fake UI
- poor realism

Production-safe reinterpretation is not permission to
replace the concept with a random scene.
""".strip()

    stc_audit = ""

    if stc_request:

        benefit_family = (
            detect_stc_benefit_family(
                original_request
            )
        )

        merchant_audit = ""

        if benefit_family == "merchant_payments":

            merchant_audit = """
MERCHANT-PAYMENTS AUDIT
-----------------------

The image must make BOTH visually understandable:

1. online / e-commerce commerce
2. physical payment / point-of-sale acceptance

They must feel connected by ONE advertising mechanism.

Do not demand readable UI or readable text as proof.

Semantic visual equivalents are valid.

Set merchant_fusion_failed = TRUE when the two channels are
merely placed beside each other with no meaningful connection.

Set literal_counter_tableau_detected = TRUE when the result
substantially becomes:

customer
+ POS
+ counter
+ merchant
+ tablet / packing background

without a strong original campaign mechanism.
""".strip()

        stc_audit = f"""
STC BANK 5-STAR HARD AUDIT
--------------------------

A technically attractive image is not enough.

Strong STC Bank identity without logo may come from:
- premium Saudi art direction
- disciplined composition
- material quality
- restrained color
- photography
- lighting
- confident negative space
- maturity learned from references

Do NOT require purple everywhere.

Reject:
- generic boutique checkout
- generic bank office
- generic person holding device
- POS toward camera as the whole idea
- generic purple room
- generic fintech effects
- reference cloning

TEXT / LOGO:
No generated advertising text.
No generated logos.
No card-brand-style symbol.
No fake readable banking UI.

PURPLE:
{build_stc_scene_tier_instruction(original_request)}

{merchant_audit}
""".strip()

    prompt = f"""
XPAND MASTERPIECE VISUAL QA V5.2
================================

Review ONE finished advertising image.

Be strict.
Do not reward beauty alone.
Judge campaign effectiveness and physical execution.

ORIGINAL REQUEST
----------------
{clean_text(
    original_request,
    3000,
)}

APPROVED RENDER BRIEF
---------------------
{compact_json(
    render_brief,
    3200,
)}

ACTUAL RENDER CONTRACT
----------------------
{clean_text(
    compiled_prompt.prompt,
    4200,
)}

PRODUCT LOCK
------------
{compact_json(
    product_lock,
    900,
)}

BRAND CONTEXT
-------------
{compact_json(
    brand_context,
    1200,
)}

EXPECTED FRAME
--------------
{clean_text(
    aspect_ratio,
    50,
)}

{reinterpretation_audit}

SCORE EVERY DIMENSION 0–100
---------------------------

concept_execution:
Did the image execute the approved advertising proposition?

message_clarity_without_text:
Can the central commercial benefit be understood before copy?

brand_alignment:
Does the result belong strategically to the brand?

brand_identity_strength:
Does it feel intentionally art-directed for this bank rather
than interchangeable with another brand?

advertising_readiness:
Could this genuinely function as a premium campaign key visual?

scene_originality:
Is the scene/hero relationship meaningfully different from
stock banking and generic fintech imagery?

service_integration:
Does the visual mechanism actually communicate the requested
service rather than just showing related props?

realism:
Is physics, anatomy, object support and photography believable?

camera_perspective:
Are lens, horizon, scale, perspective and viewpoint coherent?

lighting_materials:
Do light, shadow, reflection, texture and materials feel real?

human_anatomy:
If humans are present, are body, hands, grip and posture correct?
If no humans are present, score 100.

reference_adherence:
Did it learn visual maturity without copying a reference?

text_logo_compliance:
Is the image free from unwanted text, logos and fake UI?

purple_restraint:
Is brand color used deliberately and appropriately?

FLAGS
-----
Return true/false for:

generic_scene_detected
literal_counter_tableau_detected
repeated_scene_risk
brand_identity_weak
merchant_fusion_failed
reference_cloning_detected
unwanted_text_or_logo
fake_banking_ui

CRITICAL BLOCKERS
-----------------
List only genuine blockers.

DECISION
--------
approve:
campaign-ready.

correct:
the concept is good and specific defects can be repaired.

rebuild:
the visual execution fundamentally failed.

{stc_audit}

Return only the requested structured JSON schema.
""".strip()

    return fit_prompt_for_api(
        prompt,
        label=(
            "vision_qa_v52"
        ),
        budget=(
            QA_PROMPT_BUDGET
        ),
    )


# =========================================================
# IMAGE QA
# =========================================================

def evaluate_generated_image(
    *,
    image: GeneratedImage,
    original_request: str,
    compiled_prompt: CompiledPrompt,
    product_lock: Any,
    brand_context: Any,
    aspect_ratio: str,
    telemetry: Optional[
        Dict[str, Any]
    ] = None,
) -> QAEvaluation:

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
                aspect_ratio
            ),
        )
    )

    raw = call_openai_director(

        prompt,

        image_bytes=(
            image.image_bytes
        ),

        image_mime_type=(
            image.mime_type
            or
            "image/jpeg"
        ),

        json_mode=True,

        json_schema=(
            QA_SCHEMA
        ),

        json_schema_name=(
            "xpand_production_qa_v52"
        ),
    )

    data = parse_json_object(
        raw
    )

    if not data:

        raise RuntimeError(
            "Production QA returned invalid JSON."
        )

    score, normalized_scores = (
        calculate_qa_score(
            safe_dict(
                data.get(
                    "scores"
                )
            )
        )
    )

    flags = safe_dict(
        data.get(
            "flags"
        )
    )

    sanitized_explicit = (
        sanitize_explicit_qa_blockers(

            data.get(
                "critical_blockers"
            ),

            compiled_prompt=(
                compiled_prompt
            ),
        )
    )

    blockers = (
        detect_critical_blockers(

            scores=normalized_scores,

            explicit_failures=(
                sanitized_explicit
            ),

            flags=flags,

            product_lock=(
                product_lock
            ),

            original_request=(
                original_request
            ),
        )
    )

    model_decision = clean_text(
        data.get(
            "decision",
            "",
        ),
        50,
    ).lower()

    target_score = (
        qa_target_for_request(
            original_request
        )
    )

    release_floor = (
        qa_release_floor_for_request(
            original_request
        )
    )

    target_reached = bool(
        score
        >=
        target_score
        and
        not blockers
        and
        model_decision
        !=
        "rebuild"
    )

    delivery_approved = bool(
        score
        >=
        release_floor
        and
        not blockers
        and
        model_decision
        !=
        "rebuild"
    )

    if target_reached:

        decision = (
            "target_reached"
        )

    elif delivery_approved:

        decision = (
            "adaptive_release"
        )

    elif model_decision == "rebuild":

        decision = (
            "rebuild"
        )

    else:

        decision = (
            "correction_required"
        )

    return QAEvaluation(

        score=score,

        scores=normalized_scores,

        passed=delivery_approved,

        strengths=[
            clean_text(
                item,
                900,
            )
            for item
            in safe_list(
                data.get(
                    "strengths"
                )
            )[:8]
            if clean_text(
                item,
                900,
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
            )[:10]
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
                3000,
            )
        ),

        critical_blockers=blockers,

        target_reached=target_reached,

        delivery_approved=(
            delivery_approved
        ),

        decision=decision,

        raw={
            **data,

            "_xpand_target_score":
                target_score,

            "_xpand_release_floor":
                release_floor,

            "_xpand_flags":
                flags,

            "_xpand_production_safe_reinterpretation":
                bool(
                    safe_dict(
                        compiled_prompt.metadata
                    ).get(
                        "production_safe_reinterpretation",
                        False,
                    )
                ),
        },
    )


# =========================================================
# QA COMPARISON
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
    float,
    float,
    float,
]:

    if qa is None:

        return (
            -999,
            0,
            0.0,
            0.0,
            0.0,
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

    service_score = clamp_score(
        qa.scores.get(
            "service_integration",
            0,
        )
    )

    ad_score = clamp_score(
        qa.scores.get(
            "advertising_readiness",
            0,
        )
    )

    identity_score = clamp_score(
        qa.scores.get(
            "brand_identity_strength",
            0,
        )
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
        service_score,
        ad_score,
        identity_score,
        concept_score,
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
# CONCEPT FAILURE
# =========================================================

def has_concept_failure(
    qa: QAEvaluation,
) -> bool:

    if (
        clamp_score(
            qa.scores.get(
                "concept_execution",
                0,
            )
        )
        <
        72
    ):

        return True

    if (
        clamp_score(
            qa.scores.get(
                "message_clarity_without_text",
                0,
            )
        )
        <
        72
    ):

        return True

    if (
        clamp_score(
            qa.scores.get(
                "advertising_readiness",
                0,
            )
        )
        <
        72
    ):

        return True

    if (
        qa.raw.get(
            "decision"
        )
        ==
        "rebuild"
    ):

        return True

    flags = safe_dict(
        qa.raw.get(
            "_xpand_flags"
        )
    )

    if (
        flags.get(
            "generic_scene_detected"
        )
        or
        flags.get(
            "literal_counter_tableau_detected"
        )
        or
        flags.get(
            "merchant_fusion_failed"
        )
    ):

        return True

    combined = (
        " ".join(
            qa.critical_blockers
            +
            qa.problems
        )
    )

    return contains_any(
        combined,
        [
            "concept failure",
            "core concept",
            "message unclear",
            "visual idea missing",
            "generic scene",
            "generic banking",
            "literal counter",
            "merchant fusion",
            "الفكرة",
            "المعنى غير واضح",
        ],
    )


# =========================================================
# ADAPTIVE ACTION
# =========================================================

def choose_adaptive_action(
    qa: Optional[
        QAEvaluation
    ],
    *,
    high_alert: bool = False,
) -> str:

    if qa is None:

        #
        # QA infrastructure failure is not evidence that
        # another paid image should be generated.
        #

        return "none"

    if high_alert:

        if qa.target_reached:

            return "none"

        if has_concept_failure(
            qa
        ):

            return "concept_recovery"

        if qa.passed:

            #
            # Clean 88–91 can use the second call to try
            # to reach the 92 premium target.
            #

            return "premium_refinement"

        return "targeted_correction"

    if qa.passed:

        return "none"

    if has_concept_failure(
        qa
    ):

        return "concept_recovery"

    return "targeted_correction"


# =========================================================
# REPAIR PROMPT HELPERS
# =========================================================

def qa_failure_summary(
    qa: QAEvaluation,
) -> str:

    return compact_json(
        {
            "score":
                qa.score,

            "problems":
                qa.problems[:6],

            "critical_blockers":
                qa.critical_blockers[:8],

            "instruction":
                clean_text(
                    qa.correction_instruction,
                    1600,
                ),

            "scores": {
                key:
                    qa.scores.get(
                        key,
                        0,
                    )
                for key in (
                    "concept_execution",
                    "message_clarity_without_text",
                    "brand_alignment",
                    "brand_identity_strength",
                    "advertising_readiness",
                    "scene_originality",
                    "service_integration",
                    "realism",
                    "text_logo_compliance",
                )
            },
        },
        3200,
    )


def build_targeted_correction_prompt(
    *,
    qa: QAEvaluation,
    compiled: CompiledPrompt,
    product_lock: Any,
    aspect_ratio: str,
) -> str:

    brief = safe_dict(
        safe_dict(
            compiled.metadata
        ).get(
            "render_brief"
        )
    )

    prompt = f"""
XPAND WORKING-IMAGE TARGETED REPAIR V5.2
========================================

You are EDITING the supplied working image.

Do not invent a different campaign.

PRESERVE:
- successful composition
- successful people
- successful environment
- successful lighting
- successful camera
- successful materials
- successful copy space

FIX:
{qa_failure_summary(qa)}

APPROVED RENDER BRIEF:
{compact_json(
    brief,
    2800,
)}

PRODUCT LOCK:
{compact_json(
    product_lock,
    900,
)}

REPAIR LAW:
- remove every unwanted glyph, logo and fake symbol
- remove fake banking UI
- correct anatomy/contact/perspective if needed
- strengthen STC visual maturity without purple wash
- strengthen service clarity
- preserve one advertising mechanism
- never become a generic transaction scene

SCREEN LAW:
Any retained screen must contain no readable text, number,
logo, banking UI or fake financial information.

{safe_frame_instruction(aspect_ratio)}

Return one corrected premium campaign image.
""".strip()

    return fit_prompt_for_api(
        prompt,
        label=(
            "targeted_repair_v52"
        ),
        budget=(
            CORRECTION_PROMPT_BUDGET
        ),
    )


def build_concept_recovery_prompt(
    *,
    qa: QAEvaluation,
    compiled: CompiledPrompt,
    aspect_ratio: str,
) -> str:

    metadata = safe_dict(
        compiled.metadata
    )

    brief = safe_dict(
        metadata.get(
            "render_brief"
        )
    )

    safe_reinterpretation = bool(
        metadata.get(
            "production_safe_reinterpretation",
            False,
        )
    )

    reinterpretation = (
        production_safe_reinterpretation_instruction(
            original_request=(
                compiled.prompt
            ),
            active=(
                safe_reinterpretation
            ),
        )
    )

    prompt = f"""
XPAND WORKING-IMAGE CONCEPT EXECUTION RECOVERY V5.2
====================================================

IMPORTANT:
The supplied image is the WORKING IMAGE.

Do NOT start from an unrelated blank concept.

Use the current image as source material, but you may
RECOMPOSE IT AGGRESSIVELY when necessary.

The marketing proposition stays locked.
The failed geometry does not.

FAILED QA:
{qa_failure_summary(qa)}

APPROVED RENDER BRIEF:
{compact_json(
    brief,
    3200,
)}

{reinterpretation}

RECOVERY PRIORITIES:
1. Make the campaign mechanism visually clear.
2. Preserve the commercial proposition.
3. Preserve a premium STC Bank feel.
4. Fix service integration.
5. Remove generic-scene drift.
6. Remove all text, logos, fake symbols and fake UI.
7. Improve physical realism.
8. Keep one camera system and one light logic.

FOR MERCHANT PAYMENTS:
Online commerce and physical payment must be visually
understandable as ONE ecosystem.

Do NOT solve this with:
- customer + terminal + counter
- POS foreground + worker packing
- ordinary boutique checkout
- generic person holding POS
- generic split screen
- floating fintech graphics

If the previous literal visual trick was too fragile,
replace only that physical trick with a simpler,
believable equivalent carrying the SAME idea.

{safe_frame_instruction(aspect_ratio)}

Produce one stronger edited campaign frame.
""".strip()

    return fit_prompt_for_api(
        prompt,
        label=(
            "concept_recovery_edit_v52"
        ),
        budget=(
            CORRECTION_PROMPT_BUDGET
        ),
    )


def build_premium_refinement_prompt(
    *,
    qa: QAEvaluation,
    compiled: CompiledPrompt,
    aspect_ratio: str,
) -> str:

    brief = safe_dict(
        safe_dict(
            compiled.metadata
        ).get(
            "render_brief"
        )
    )

    prompt = f"""
XPAND STC PREMIUM WORKING-IMAGE REFINEMENT V5.2
================================================

The supplied image already reached the safe release floor.

Do NOT redesign the concept.

Preserve:
- scene
- hero relationship
- camera
- human identity
- service meaning
- negative space

Improve only premium execution.

CURRENT QA:
{qa_failure_summary(qa)}

APPROVED BRIEF:
{compact_json(
    brief,
    2600,
)}

Refine:
- material realism
- natural skin
- reflections
- contact shadows
- hierarchy
- lighting separation
- visual polish
- STC brand-world confidence
- restrained color
- campaign readiness

Remove any accidental text/logo/UI artifacts.

Do not add:
- new props
- new fintech effects
- new concept
- new purple wash

{safe_frame_instruction(aspect_ratio)}

Produce one refined version of the working image.
""".strip()

    return fit_prompt_for_api(
        prompt,
        label=(
            "premium_refinement_v52"
        ),
        budget=(
            CORRECTION_PROMPT_BUDGET
        ),
    )


# =========================================================
# QA LOG
# =========================================================

def print_qa(
    label: str,
    qa: QAEvaluation,
) -> None:

    print("")
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

    labels = [
        (
            "Concept",
            "concept_execution",
        ),
        (
            "Message",
            "message_clarity_without_text",
        ),
        (
            "Brand",
            "brand_alignment",
        ),
        (
            "Brand identity",
            "brand_identity_strength",
        ),
        (
            "Originality",
            "scene_originality",
        ),
        (
            "Service integration",
            "service_integration",
        ),
        (
            "Advertising readiness",
            "advertising_readiness",
        ),
        (
            "Realism",
            "realism",
        ),
        (
            "Text/logo",
            "text_logo_compliance",
        ),
        (
            "Purple restraint",
            "purple_restraint",
        ),
    ]

    for display, key in labels:

        print(
            display
            +
            ":",
            qa.scores.get(
                key,
                0,
            ),
        )

    print(
        "Critical blockers:",
        len(
            qa.critical_blockers
        ),
    )

    for blocker in (
        qa.critical_blockers[:10]
    ):

        print(
            "  🛑",
            blocker,
        )

    print(
        "Decision:",
        qa.decision,
    )


# =========================================================
# DELIVERY FRAME
# =========================================================

def create_exact_delivery_frame(
    image: GeneratedImage,
    aspect_ratio: str,
    *,
    upscale_final: bool = False,
    label: str = "delivery",
) -> GeneratedImage:

    if not isinstance(
        image.metadata,
        dict,
    ):

        image.metadata = {}

    image.metadata.update(
        {
            "delivery_frame":
                label,

            "requested_aspect_ratio":
                aspect_ratio,

            "native_delivery":
                True,

            "local_upscale":
                False,
        }
    )

    image.aspect_ratio = (
        aspect_ratio
    )

    return image


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

    started = time.monotonic()

    errors: List[str] = []

    requested_size = (
        detect_image_size(
            original_request
        )
    )

    if requested_size not in {
        "1K",
        "2K",
        "4K",
    }:

        requested_size = "1K"

    stc_request = (
        is_stc_production_request(
            original_request,
            brand_id,
        )
    )

    high_alert = (
        is_stc_high_alert(
            original_request,
            mode,
            brand_id,
        )
    )

    telemetry: Dict[
        str,
        Any,
    ] = {

        "image_calls":
            0,

        "vision_calls":
            0,

        "max_image_calls":
            MASTERPIECE_MAX_IMAGE_CALLS,

        "max_vision_calls":
            MASTERPIECE_MAX_VISION_CALLS,

        "normal_expected_image_calls":
            1,

        "normal_expected_vision_calls":
            (
                1
                if
                mode
                ==
                MODE_MASTERPIECE
                else
                0
            ),

        "nano_banana_2":
            True,

        "nano_banana_pro":
            False,

        "nano_banana_pro_calls":
            0,

        "requested_image_size":
            requested_size,

        "selected_reference_count":
            0,

        "physical_reference_count":
            0,

        "physical_reference_ids":
            [],

        "stc_local_reference_count":
            0,

        "stc_local_reference_ids":
            [],

        "stc_render_reference_limit":
            STC_RENDER_REFERENCE_LIMIT,

        "stc_edit_reference_limit":
            STC_EDIT_REFERENCE_LIMIT,

        "adaptive_action":
            "none",

        "production_safe_reinterpretation":
            False,

        "working_image_recovery":
            False,

        "block_generic_smart_fallback":
            bool(
                high_alert
            ),
    }

    # =====================================================
    # MEMORY REFERENCES
    # =====================================================

    memory_references = (
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

    # =====================================================
    # PERMANENT STC REFERENCES
    # =====================================================

    stc_local_refs: List[
        ProductionReference
    ] = []

    stc_kit: Optional[Any] = None

    stc_assets: List[Any] = []

    if stc_request:

        (
            stc_local_refs,
            stc_kit,
            stc_assets,
        ) = load_stc_local_references(

            request=(
                original_request
            ),

            max_total=(
                MAX_STC_PHYSICAL_REFERENCE_IMAGES
            ),

            rotation_key=(
                clean_text(
                    user_id,
                    200,
                )
                +
                ":"
                +
                clean_text(
                    original_request,
                    1500,
                )
            ),
        )

    telemetry[
        "stc_local_reference_count"
    ] = len(
        stc_local_refs
    )

    telemetry[
        "stc_local_reference_ids"
    ] = [
        item.source_id
        for item
        in stc_local_refs
    ]

    # =====================================================
    # ALL REFERENCE INTELLIGENCE
    # =====================================================

    references = unique_references(
        list(
            memory_references
        )
        +
        list(
            stc_local_refs
        )
    )

    product_refs = (
        product_references(
            memory_references
        )
    )

    # =====================================================
    # PHYSICAL RENDER SET
    # =====================================================

    if stc_request:

        physical_refs = (
            build_stc_primary_reference_set(

                product_refs=(
                    product_refs
                ),

                local_refs=(
                    stc_local_refs
                ),

                memory_refs=(
                    memory_references
                ),

                limit=(
                    STC_RENDER_REFERENCE_LIMIT
                ),
            )
        )

    else:

        physical_refs = (
            choose_physical_references(

                memory_references,

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

    telemetry[
        "physical_reference_ids"
    ] = [
        item.source_id
        for item
        in physical_refs
    ]

    # =====================================================
    # REFERENCE DNA
    # =====================================================

    reference_dna = (
        reference_dna_payload(

            references,

            limit=(
                5
                if stc_request
                else
                SMART_REFERENCE_SELECTION_LIMIT
            ),
        )
    )

    # =====================================================
    # PRODUCT LOCK
    # =====================================================

    product_lock = (
        combined_product_lock(
            memory_references
        )
    )

    # =====================================================
    # VISUAL PROFILE
    # =====================================================

    brand_visual_profile = (
        load_brand_visual_profile_safe(
            core,
            user_id,
            brand_id,
        )
    )

    # =====================================================
    # BRAND KIT TEXT CONTEXT
    # =====================================================

    stc_kit_context = {}

    if stc_request:

        stc_kit_context = (
            build_stc_brand_kit_context(

                stc_kit,

                request=(
                    original_request
                ),

                selected_assets=(
                    stc_assets
                ),
            )
        )

    # =====================================================
    # ENRICHED BRAND CONTEXT
    # =====================================================

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

            stc_brand_kit_context=(
                stc_kit_context
            ),
        )
    )

    # =====================================================
    # COMPILE SHORT RENDER CONTRACT
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

    telemetry[
        "production_safe_reinterpretation"
    ] = bool(
        safe_dict(
            compiled.metadata
        ).get(
            "production_safe_reinterpretation",
            False,
        )
    )

    telemetry[
        "render_prompt_chars"
    ] = len(
        compiled.prompt
    )

    # =====================================================
    # LOG HEADER
    # =====================================================

    print("")
    print(
        "=============================================="
    )
    print(
        " XPAND PRODUCTION ENGINE V5.2"
    )

    if high_alert:

        print(
            " STC BANK PRODUCTION-SAFE HIGH ALERT"
        )

    else:

        print(
            " NANO BANANA QUALITY PRODUCTION"
        )

    print(
        "=============================================="
    )

    print(
        "Mode:",
        mode,
    )

    print(
        "Primary model:",
        NANO_BANANA_2_MODEL,
    )

    if high_alert:

        print(
            "Escalation model:",
            (
                NANO_BANANA_PRO_MODEL
                if
                STC_ALLOW_GEMINI_PRO_UPGRADE
                else
                "disabled"
            ),
        )

    print(
        "Brand:",
        brand_id,
    )

    print(
        "Aspect ratio:",
        aspect_ratio,
    )

    print(
        "Native image size:",
        requested_size,
    )

    print(
        "Memory references:",
        len(
            memory_references
        ),
    )

    print(
        "Permanent STC references loaded:",
        len(
            stc_local_refs
        ),
    )

    print(
        "Actual references sent to primary:",
        len(
            physical_refs
        ),
    )

    for item in physical_refs:

        print(
            "  🖼️",
            item.source_id,
            "|",
            item.role,
            "|",
            item.content_family,
        )

    print(
        "Render prompt chars:",
        len(
            compiled.prompt
        ),
    )

    print(
        "Production-safe reinterpretation:",
        telemetry[
            "production_safe_reinterpretation"
        ],
    )

    print(
        "Normal image calls:",
        1,
    )

    print(
        "Max image calls:",
        MASTERPIECE_MAX_IMAGE_CALLS,
    )

    print(
        "Max Vision calls:",
        MASTERPIECE_MAX_VISION_CALLS,
    )

    if stc_request:

        print(
            "STC scene tier:",
            stc_scene_tier(
                original_request
            ),
        )

        print(
            "STC visual family:",
            stc_visual_family_for_brand_kit(
                original_request
            ),
        )

        print(
            "STC benefit:",
            detect_stc_benefit_family(
                original_request
            ),
        )

        print(
            "STC Brand Pack:",
            (
                "LOADED ✅"
                if stc_kit
                else
                "NOT LOADED"
            ),
        )

    print("")

    # =====================================================
    # IMAGE CALL 1
    # =====================================================

    print(
        "🍌 IMAGE CALL 1/"
        +
        str(
            MASTERPIECE_MAX_IMAGE_CALLS
        )
        +
        " | "
        +
        NANO_BANANA_2_MODEL
    )

    first_image = (
        generate_high_quality_image(

            compiled=(
                compiled
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
                "masterpiece_primary_v52"
            ),

            output_image_size=(
                requested_size
            ),

            model_override=(
                NANO_BANANA_2_MODEL
            ),

            max_physical_references=(
                STC_RENDER_REFERENCE_LIMIT
                if stc_request
                else
                MAX_PHYSICAL_REFERENCE_IMAGES
            ),
        )
    )

    telemetry[
        "image_calls"
    ] += 1

    passes: List[
        ProductionPassResult
    ] = [
        ProductionPassResult(

            pass_name=(
                "masterpiece_primary_v52"
            ),

            image=first_image,

            metadata={
                "image_call":
                    1,

                "model":
                    NANO_BANANA_2_MODEL,

                "image_size":
                    requested_size,

                "physical_reference_count":
                    len(
                        physical_refs
                    ),

                "physical_reference_ids": [
                    item.source_id
                    for item
                    in physical_refs
                ],

                "stc_brand_pack":
                    bool(
                        stc_kit
                    ),

                "stc_high_alert":
                    high_alert,

                "production_safe_reinterpretation":
                    telemetry[
                        "production_safe_reinterpretation"
                    ],
            },
        )
    ]

    best_image = (
        first_image
    )

    best_qa: Optional[
        QAEvaluation
    ] = None

    best_score = 0.0

    # =====================================================
    # FAST / NON-MASTERPIECE
    # =====================================================

    if mode != MODE_MASTERPIECE:

        final_image = (
            create_exact_delivery_frame(

                best_image,
                aspect_ratio,

                upscale_final=False,

                label=(
                    "fast_delivery"
                ),
            )
        )

        final_image.provider = (
            "xpand_production"
        )

        return ProductionResult(

            ok=True,

            final_image=(
                final_image
            ),

            best_score=0.0,

            qa=None,

            passes=passes,

            compiled_prompt=compiled,

            references_used=len(
                references
            ),

            product_references_used=len(
                product_refs
            ),

            elapsed_seconds=round(
                time.monotonic()
                -
                started,
                3,
            ),

            errors=errors,

            telemetry=telemetry,
        )

    # =====================================================
    # VISION QA 1
    # =====================================================

    if (
        telemetry[
            "vision_calls"
        ]
        <
        MASTERPIECE_MAX_VISION_CALLS
    ):

        print("")
        print(
            "👁️ VISION QA 1/"
            +
            str(
                MASTERPIECE_MAX_VISION_CALLS
            )
        )

        try:

            best_qa = (
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
                best_qa
            )

            best_score = (
                best_qa.score
            )

            print_qa(
                "Primary QA",
                best_qa,
            )

        except Exception as error:

            message = clean_text(
                error,
                3000,
            )

            errors.append(
                (
                    "qa_primary: "
                    +
                    message
                )
            )

            print(
                "⚠️ Primary QA unavailable:",
                message,
            )

            #
            # Do not spend a second image call because
            # evaluator infrastructure failed.
            #

            best_qa = None

    # =====================================================
    # ADAPTIVE DECISION
    # =====================================================

    action = (
        choose_adaptive_action(

            best_qa,

            high_alert=(
                high_alert
            ),
        )
    )

    telemetry[
        "adaptive_action"
    ] = action

    print("")
    print(
        "🧠 ADAPTIVE DECISION:",
        action,
    )

    # =====================================================
    # SECOND IMAGE CALL
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
        MASTERPIECE_MAX_IMAGE_CALLS
    ):

        second_image: Optional[
            GeneratedImage
        ] = None

        second_qa: Optional[
            QAEvaluation
        ] = None

        try:

            escalation_model = (
                NANO_BANANA_PRO_MODEL
                if (
                    high_alert
                    and
                    STC_ALLOW_GEMINI_PRO_UPGRADE
                )
                else
                NANO_BANANA_2_MODEL
            )

            if (
                escalation_model
                ==
                NANO_BANANA_PRO_MODEL
            ):

                telemetry[
                    "nano_banana_pro"
                ] = True

                telemetry[
                    "nano_banana_pro_calls"
                ] += 1

            if high_alert:

                edit_refs = (
                    correction_reference_set(

                        product_refs=(
                            product_refs
                        ),

                        stc_local_refs=(
                            stc_local_refs
                        ),

                        high_alert=True,
                    )
                )

                edit_limit = (
                    STC_EDIT_REFERENCE_LIMIT
                )

            else:

                edit_refs = (
                    choose_physical_references(

                        memory_references,

                        limit=(
                            MAX_PHYSICAL_REFERENCE_IMAGES
                        ),
                    )
                )

                edit_limit = (
                    MAX_PHYSICAL_REFERENCE_IMAGES
                )

            # =================================================
            # CONCEPT EXECUTION RECOVERY
            # =================================================

            if action == "concept_recovery":

                print("")
                print(
                    "🍌 IMAGE CALL 2/"
                    +
                    str(
                        MASTERPIECE_MAX_IMAGE_CALLS
                    )
                    +
                    " | "
                    +
                    escalation_model
                    +
                    " | WORKING-IMAGE CONCEPT RECOVERY"
                )

                recovery_prompt = (
                    build_concept_recovery_prompt(

                        qa=best_qa,

                        compiled=compiled,

                        aspect_ratio=(
                            aspect_ratio
                        ),
                    )
                )

                #
                # V5.2 CRITICAL CHANGE:
                #
                # Do NOT generate from blank.
                #
                # The existing image becomes working material.
                #

                second_image = (
                    gemini_multi_reference_edit(

                        working_image=(
                            best_image
                        ),

                        references=(
                            edit_refs
                        ),

                        prompt=(
                            recovery_prompt
                        ),

                        aspect_ratio=(
                            aspect_ratio
                        ),

                        pass_name=(
                            "working_image_concept_recovery_v52"
                        ),

                        output_image_size=(
                            requested_size
                        ),

                        model_override=(
                            escalation_model
                        ),

                        max_reference_images=(
                            edit_limit
                        ),
                    )
                )

                telemetry[
                    "working_image_recovery"
                ] = True

                second_pass_name = (
                    "working_image_concept_recovery_v52"
                )

            # =================================================
            # PREMIUM REFINEMENT
            # =================================================

            elif action == "premium_refinement":

                print("")
                print(
                    "🍌 IMAGE CALL 2/"
                    +
                    str(
                        MASTERPIECE_MAX_IMAGE_CALLS
                    )
                    +
                    " | "
                    +
                    escalation_model
                    +
                    " | premium working-image refinement"
                )

                refinement_prompt = (
                    build_premium_refinement_prompt(

                        qa=best_qa,

                        compiled=compiled,

                        aspect_ratio=(
                            aspect_ratio
                        ),
                    )
                )

                second_image = (
                    gemini_multi_reference_edit(

                        working_image=(
                            best_image
                        ),

                        references=(
                            edit_refs
                        ),

                        prompt=(
                            refinement_prompt
                        ),

                        aspect_ratio=(
                            aspect_ratio
                        ),

                        pass_name=(
                            "premium_refinement_v52"
                        ),

                        output_image_size=(
                            requested_size
                        ),

                        model_override=(
                            escalation_model
                        ),

                        max_reference_images=(
                            edit_limit
                        ),
                    )
                )

                second_pass_name = (
                    "premium_refinement_v52"
                )

            # =================================================
            # TARGETED CORRECTION
            # =================================================

            else:

                print("")
                print(
                    "🍌 IMAGE CALL 2/"
                    +
                    str(
                        MASTERPIECE_MAX_IMAGE_CALLS
                    )
                    +
                    " | "
                    +
                    escalation_model
                    +
                    " | targeted working-image repair"
                )

                correction_prompt = (
                    build_targeted_correction_prompt(

                        qa=best_qa,

                        compiled=compiled,

                        product_lock=(
                            product_lock
                        ),

                        aspect_ratio=(
                            aspect_ratio
                        ),
                    )
                )

                second_image = (
                    gemini_multi_reference_edit(

                        working_image=(
                            best_image
                        ),

                        references=(
                            edit_refs
                        ),

                        prompt=(
                            correction_prompt
                        ),

                        aspect_ratio=(
                            aspect_ratio
                        ),

                        pass_name=(
                            "targeted_repair_v52"
                        ),

                        output_image_size=(
                            requested_size
                        ),

                        model_override=(
                            escalation_model
                        ),

                        max_reference_images=(
                            edit_limit
                        ),
                    )
                )

                second_pass_name = (
                    "targeted_repair_v52"
                )

            telemetry[
                "image_calls"
            ] += 1

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

                        "model":
                            escalation_model,

                        "adaptive_action":
                            action,

                        "image_size":
                            requested_size,

                        "working_image_used":
                            True,

                        "physical_reference_count":
                            len(
                                edit_refs
                            ),

                        "physical_reference_ids": [
                            item.source_id
                            for item
                            in edit_refs
                        ],
                    },
                )
            )

            # =================================================
            # VISION QA 2
            # =================================================

            if (
                telemetry[
                    "vision_calls"
                ]
                <
                MASTERPIECE_MAX_VISION_CALLS
            ):

                print("")
                print(
                    "👁️ VISION QA 2/"
                    +
                    str(
                        MASTERPIECE_MAX_VISION_CALLS
                    )
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
                        "Second QA",
                        second_qa,
                    )

                except Exception as error:

                    message = clean_text(
                        error,
                        3000,
                    )

                    errors.append(
                        (
                            "qa_second: "
                            +
                            message
                        )
                    )

                    print(
                        "⚠️ Second QA unavailable:",
                        message,
                    )

            # =================================================
            # KEEP STRONGEST CANDIDATE
            # =================================================

            if (
                second_qa is not None
                and
                qa_candidate_is_better(
                    second_qa,
                    best_qa,
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
                    "🏆 Second candidate selected."
                )

            else:

                print(
                    "🏆 Primary candidate preserved."
                )

        except Exception as error:

            message = clean_text(
                error,
                3500,
            )

            errors.append(
                (
                    action
                    +
                    ": "
                    +
                    message
                )
            )

            print(
                "⚠️ Adaptive image pass failed:",
                message,
            )

            print(
                "✅ Existing candidate preserved."
            )

    else:

        if best_qa is not None:

            if best_qa.target_reached:

                print(
                    "✅ QA premium target reached."
                )

            elif best_qa.passed:

                print(
                    "✅ QA release floor reached."
                )

        print(
            "💰 No second image call needed."
        )

    # =====================================================
    # FINAL DELIVERY FRAME
    # =====================================================

    print("")
    print(
        "📦 Preparing native final delivery..."
    )

    final_image = (
        create_exact_delivery_frame(

            best_image,
            aspect_ratio,

            upscale_final=False,

            label=(
                "final_delivery"
            ),
        )
    )

    final_image.provider = (
        "xpand_masterpiece"
    )

    if not isinstance(
        final_image.metadata,
        dict,
    ):

        final_image.metadata = {}

    final_image.metadata.update(
        {
            "production_engine":
                ENGINE_VERSION,

            "primary_model":
                NANO_BANANA_2_MODEL,

            "final_model":
                getattr(
                    best_image,
                    "model",
                    NANO_BANANA_2_MODEL,
                ),

            "nano_banana_2":
                True,

            "nano_banana_pro_used":
                bool(
                    telemetry.get(
                        "nano_banana_pro_calls",
                        0,
                    )
                ),

            "image_calls":
                telemetry[
                    "image_calls"
                ],

            "vision_calls":
                telemetry[
                    "vision_calls"
                ],

            "requested_image_size":
                requested_size,

            "selected_reference_count":
                len(
                    references
                ),

            "physical_reference_count":
                len(
                    physical_refs
                ),

            "physical_reference_ids": [
                item.source_id
                for item
                in physical_refs
            ],

            "stc_brand_pack_loaded":
                bool(
                    stc_kit
                ),

            "stc_high_alert":
                high_alert,

            "stc_local_reference_ids":
                telemetry.get(
                    "stc_local_reference_ids",
                    [],
                ),

            "production_safe_reinterpretation":
                telemetry.get(
                    "production_safe_reinterpretation",
                    False,
                ),

            "working_image_recovery":
                telemetry.get(
                    "working_image_recovery",
                    False,
                ),

            "render_prompt_chars":
                telemetry.get(
                    "render_prompt_chars",
                    0,
                ),

            "block_generic_smart_fallback":
                bool(
                    high_alert
                ),
        }
    )

    # =====================================================
    # FINAL QA STATUS
    # =====================================================

    if best_qa is not None:

        final_ok = bool(
            best_qa.passed
        )

        best_score = (
            best_qa.score
        )

    else:

        #
        # No fake QA approval.
        #

        final_ok = False

        best_score = 0.0

    elapsed = round(
        time.monotonic()
        -
        started,
        3,
    )

    print("")
    print(
        "=============================================="
    )
    print(
        " XPAND PRODUCTION COMPLETE V5.2"
    )
    print(
        "=============================================="
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
        "Permanent STC refs loaded:",
        telemetry[
            "stc_local_reference_count"
        ],
    )

    print(
        "Primary physical refs sent:",
        telemetry[
            "physical_reference_count"
        ],
    )

    print(
        "Working-image recovery:",
        telemetry[
            "working_image_recovery"
        ],
    )

    print(
        "Production-safe reinterpretation:",
        telemetry[
            "production_safe_reinterpretation"
        ],
    )

    print(
        "Nano Banana Pro calls:",
        telemetry[
            "nano_banana_pro_calls"
        ],
    )

    print(
        "Final model:",
        getattr(
            best_image,
            "model",
            NANO_BANANA_2_MODEL,
        ),
    )

    print(
        "Final size:",
        requested_size,
    )

    print(
        "QA target:",
        qa_target_for_request(
            original_request
        ),
    )

    print(
        "QA release floor:",
        qa_release_floor_for_request(
            original_request
        ),
    )

    print(
        "QA score:",
        (
            best_score
            if best_qa
            else
            "unavailable"
        ),
    )

    print(
        "QA passed:",
        (
            best_qa.passed
            if best_qa
            else
            False
        ),
    )

    print(
        "STC High Alert:",
        high_alert,
    )

    print(
        "Elapsed:",
        elapsed,
        "sec",
    )

    print("")

    return ProductionResult(

        ok=final_ok,

        final_image=final_image,

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

        telemetry=telemetry,
    )


# =========================================================
# STATUS
# =========================================================

def get_production_engine_status() -> Dict[
    str,
    Any,
]:

    return {
        "engine":
            ENGINE_NAME,

        "version":
            ENGINE_VERSION,

        "nano_banana_2_model":
            NANO_BANANA_2_MODEL,

        "nano_banana_pro_model":
            NANO_BANANA_PRO_MODEL,

        "nano_banana_pro_required":
            False,

        "stc_pro_upgrade_enabled":
            STC_ALLOW_GEMINI_PRO_UPGRADE,

        "stc_high_alert_enabled":
            STC_HIGH_ALERT_ENABLED,

        "stc_brand_kit_available":
            STC_BRAND_KIT_AVAILABLE,

        "stc_brand_pack_required":
            STC_REQUIRE_BRAND_PACK,

        "max_image_calls":
            MASTERPIECE_MAX_IMAGE_CALLS,

        "max_vision_calls":
            MASTERPIECE_MAX_VISION_CALLS,

        "normal_image_calls":
            1,

        "normal_vision_calls":
            1,

        "smart_reference_limit":
            SMART_REFERENCE_SELECTION_LIMIT,

        "physical_reference_limit":
            MAX_PHYSICAL_REFERENCE_IMAGES,

        #
        # Keep old compatibility value:
        # how many STC refs can be loaded/curated.
        #

        "stc_physical_reference_limit":
            MAX_STC_PHYSICAL_REFERENCE_IMAGES,

        #
        # New V5.2 actual generation limits.
        #

        "stc_render_reference_limit":
            STC_RENDER_REFERENCE_LIMIT,

        "stc_edit_reference_limit":
            STC_EDIT_REFERENCE_LIMIT,

        "render_prompt_budget":
            COMPILED_PROMPT_BUDGET,

        "image_call_prompt_budget":
            IMAGE_CALL_PROMPT_BUDGET,

        "qa_prompt_budget":
            QA_PROMPT_BUDGET,

        "correction_prompt_budget":
            CORRECTION_PROMPT_BUDGET,

        "qa_target":
            QA_TARGET_SCORE,

        "qa_release_floor":
            QA_RELEASE_FLOOR,

        "stc_qa_target":
            STC_QA_TARGET_SCORE,

        "stc_qa_release_floor":
            STC_QA_RELEASE_FLOOR,

        "production_safe_reinterpretation":
            True,

        "working_image_concept_recovery":
            True,
    }


# =========================================================
# ZERO-COST SELF TEST
# =========================================================

if __name__ == "__main__":

    tests: Dict[
        str,
        bool,
    ] = {}

    # =====================================================
    # CONTRACT / QA
    # =====================================================

    tests[
        "qa_weights_sum_100"
    ] = (
        sum(
            QA_WEIGHTS.values()
        )
        ==
        100
    )

    tests[
        "max_two_image_calls"
    ] = (
        MASTERPIECE_MAX_IMAGE_CALLS
        <=
        2
    )

    tests[
        "max_two_vision_calls"
    ] = (
        MASTERPIECE_MAX_VISION_CALLS
        <=
        2
    )

    tests[
        "general_three_memory_refs"
    ] = (
        SMART_REFERENCE_SELECTION_LIMIT
        <=
        3
    )

    tests[
        "general_two_physical_refs"
    ] = (
        MAX_PHYSICAL_REFERENCE_IMAGES
        <=
        2
    )

    tests[
        "stc_pack_can_load_five"
    ] = (
        MAX_STC_PHYSICAL_REFERENCE_IMAGES
        >=
        3
        and
        MAX_STC_PHYSICAL_REFERENCE_IMAGES
        <=
        5
    )

    tests[
        "stc_primary_max_three_refs"
    ] = (
        STC_RENDER_REFERENCE_LIMIT
        <=
        3
    )

    tests[
        "stc_edit_max_two_refs"
    ] = (
        STC_EDIT_REFERENCE_LIMIT
        <=
        2
    )

    tests[
        "nano_banana_2"
    ] = bool(
        NANO_BANANA_2_MODEL
    )

    tests[
        "pro_model_defined"
    ] = bool(
        NANO_BANANA_PRO_MODEL
    )

    tests[
        "no_mandatory_pro"
    ] = (
        get_production_engine_status()[
            "nano_banana_pro_required"
        ]
        is False
    )

    # =====================================================
    # STC QA THRESHOLDS
    # =====================================================

    tests[
        "stc_target_not_lowered"
    ] = (
        STC_QA_TARGET_SCORE
        >=
        92.0
    )

    tests[
        "stc_release_floor_not_lowered"
    ] = (
        STC_QA_RELEASE_FLOOR
        >=
        88.0
    )

    # =====================================================
    # STC STYLE
    # =====================================================

    tests[
        "stc_realistic_tier_a"
    ] = (
        stc_scene_tier(
            (
                "STC Bank "
                "واقعي فوتوغرافي"
            )
        )
        ==
        "TIER_A"
    )

    tests[
        "stc_augmented_tier_b"
    ] = (
        stc_scene_tier(
            (
                "STC Bank "
                "واقعي سريالي راقٍ"
            )
        )
        ==
        "TIER_B"
    )

    tests[
        "stc_purple_tier_c"
    ] = (
        stc_scene_tier(
            (
                "STC Bank "
                "بيئة بنفسجية معمارية"
            )
        )
        ==
        "TIER_C"
    )

    # =====================================================
    # BRITTLE MECHANISM REGRESSION
    # =====================================================

    brittle_brief = {
        "title":
            "الواجهة التي تعبر الزجاج",

        "core_idea":
            (
                "A half-digital half-physical product "
                "crosses the screen plane into the real world."
            ),

        "campaign_hook":
            "One merchant ecosystem.",
    }

    tests[
        "brittle_screen_crossing_detected"
    ] = (
        requires_production_safe_reinterpretation(
            brittle_brief
        )
    )

    safe_brief = {
        "title":
            "Physical commerce threshold",

        "core_idea":
            (
                "One believable physical structure connects "
                "online commerce and physical payment."
            ),
    }

    tests[
        "normal_physical_mechanism_not_rewritten"
    ] = (
        not
        requires_production_safe_reinterpretation(
            safe_brief
        )
    )

    # =====================================================
    # REFERENCE MIX REGRESSION
    # =====================================================

    fake_refs = [
        ProductionReference(
            role="campaign_reference",
            image_bytes=b"a" * 200,
            mime_type="image/jpeg",
            source_id="dna_1",
            content_family="stc_dna",
        ),
        ProductionReference(
            role="campaign_reference",
            image_bytes=b"b" * 200,
            mime_type="image/jpeg",
            source_id="dna_2",
            content_family="stc_dna",
        ),
        ProductionReference(
            role="style_reference",
            image_bytes=b"c" * 200,
            mime_type="image/jpeg",
            source_id="style_1",
            content_family="stc_realistic",
        ),
        ProductionReference(
            role="style_reference",
            image_bytes=b"d" * 200,
            mime_type="image/jpeg",
            source_id="style_2",
            content_family="stc_realistic",
        ),
        ProductionReference(
            role="environment_reference",
            image_bytes=b"e" * 200,
            mime_type="image/jpeg",
            source_id="merchant_1",
            content_family="stc_merchant",
        ),
    ]

    fake_primary = (
        build_stc_primary_reference_set(
            product_refs=[],
            local_refs=fake_refs,
            memory_refs=[],
            limit=(
                STC_RENDER_REFERENCE_LIMIT
            ),
        )
    )

    tests[
        "five_loaded_three_sent"
    ] = (
        len(
            fake_refs
        )
        ==
        5
        and
        len(
            fake_primary
        )
        <=
        3
    )

    tests[
        "primary_contains_dna"
    ] = any(
        item.role
        ==
        "campaign_reference"
        for item
        in fake_primary
    )

    tests[
        "primary_contains_style"
    ] = any(
        item.role
        ==
        "style_reference"
        for item
        in fake_primary
    )

    tests[
        "primary_contains_service"
    ] = any(
        item.role
        ==
        "environment_reference"
        for item
        in fake_primary
    )

    fake_edit = (
        correction_reference_set(
            product_refs=[],
            stc_local_refs=fake_refs,
            high_alert=True,
        )
    )

    tests[
        "working_edit_refs_max_two"
    ] = (
        len(
            fake_edit
        )
        <=
        2
    )

    # =====================================================
    # PROMPT REGRESSION
    # =====================================================

    sample_compiled = (
        compile_prompt(

            TARGET_GEMINI,

            request=(
                "أنشئ إعلان STC Bank "
                "عن خدمات التجارة الإلكترونية "
                "ونقاط البيع "
                "واقعي فوتوغرافي"
            ),

            creative_direction={
                "concept_id":
                    "C04",

                "title":
                    "Commerce Continuity",

                "campaign_hook":
                    "One connected merchant ecosystem.",

                "core_idea":
                    (
                        "A physical commercial relationship "
                        "connects online commerce with "
                        "in-store payment."
                    ),

                "visual_metaphor":
                    (
                        "One continuous believable physical "
                        "gesture communicates both channels."
                    ),

                "visual_mechanism_type":
                    "physical continuity",

                "environment":
                    (
                        "Contemporary premium Saudi "
                        "commercial architecture."
                    ),

                "hero_element":
                    "The unified commerce relationship.",

                "supporting_elements": [
                    "online commerce cue",
                    "physical payment cue",
                ],

                "lighting":
                    "Soft directional commercial daylight.",

                "negative_space":
                    "30% upper-right copy space.",

                "brand_logic":
                    (
                        "Premium Saudi banking confidence "
                        "with restrained identity accents."
                    ),
            },

            brand_context={},

            references=[],

            camera_direction={
                "camera_angle":
                    "elevated three-quarter",

                "lens":
                    "35mm",

                "perspective":
                    "controlled architectural perspective",
            },

            product_lock={},

            aspect_ratio="4:5",
        )
    )

    tests[
        "short_render_contract"
    ] = (
        len(
            sample_compiled.prompt
        )
        <=
        COMPILED_PROMPT_BUDGET
    )

    tests[
        "copy_space_lock"
    ] = (
        "25–40%"
        in
        sample_compiled.prompt
    )

    tests[
        "subject_protection"
    ] = (
        "SUBJECT-PROTECTION LAW"
        in
        sample_compiled.prompt
    )

    tests[
        "no_text_lock"
    ] = (
        "TEXT-FREE LAW"
        in
        sample_compiled.prompt
    )

    tests[
        "real_app_lock"
    ] = (
        "REAL-APP LAW"
        in
        sample_compiled.prompt
    )

    tests[
        "anti_repetition"
    ] = (
        "ANTI-REPETITION LAW"
        in
        sample_compiled.prompt
    )

    tests[
        "no_clone"
    ] = (
        "NO-CLONE LAW"
        in
        sample_compiled.prompt
    )

    tests[
        "permanent_stc_dna_lock"
    ] = (
        "PERMANENT STC BANK BRAND DNA"
        in
        sample_compiled.prompt
    )

    tests[
        "counter_tableau_hard_ban"
    ] = bool(
        "customer"
        in
        sample_compiled.prompt.lower()
        and
        "packing"
        in
        sample_compiled.prompt.lower()
        and
        "counter"
        in
        sample_compiled.prompt.lower()
    )

    tests[
        "merchant_integration_lock"
    ] = (
        "ONE CONNECTED MERCHANT ECOSYSTEM"
        in
        sample_compiled.prompt
    )

    tests[
        "final_jury_lock"
    ] = (
        "FINAL CREATIVE JURY LOCK"
        in
        sample_compiled.prompt
    )

    tests[
        "screen_text_hard_ban"
    ] = bool(
        "No generated headline"
        in
        base_negative_prompt()
        and
        "No fake banking UI"
        in
        base_negative_prompt()
    )

    # =====================================================
    # QA REINTERPRETATION POLICY
    # =====================================================

    brittle_compiled = (
        compile_prompt(

            TARGET_GEMINI,

            request=(
                "STC Bank التجارة الإلكترونية "
                "ونقاط البيع واقعي فوتوغرافي"
            ),

            creative_direction={
                "title":
                    "الواجهة التي تعبر الزجاج",

                "core_idea":
                    (
                        "A half-digital half-physical object "
                        "crosses the screen plane."
                    ),

                "campaign_hook":
                    "One merchant ecosystem.",
            },

            brand_context={},

            references=[],

            camera_direction={
                "lens":
                    "35mm",
            },

            product_lock={},

            aspect_ratio="4:5",
        )
    )

    tests[
        "safe_reinterpretation_metadata"
    ] = bool(
        brittle_compiled.metadata.get(
            "production_safe_reinterpretation"
        )
    )

    qa_test_prompt = (
        build_qa_prompt(

            original_request=(
                "STC Bank التجارة الإلكترونية ونقاط البيع"
            ),

            compiled_prompt=(
                brittle_compiled
            ),

            product_lock={},

            brand_context={},

            aspect_ratio="4:5",
        )
    )

    tests[
        "qa_does_not_require_literal_brittle_geometry"
    ] = (
        "Do NOT require literal impossible geometry"
        in
        qa_test_prompt
    )

    sanitized = (
        sanitize_explicit_qa_blockers(

            [
                (
                    "Missing continuous half-digital, "
                    "half-physical product crossing the screen plane."
                ),
                (
                    "Merchant channel fusion fails."
                ),
            ],

            compiled_prompt=(
                brittle_compiled
            ),
        )
    )

    tests[
        "literal_geometry_false_blocker_removed"
    ] = not any(
        "screen plane"
        in
        item.lower()
        for item
        in sanitized
    )

    tests[
        "semantic_failure_still_preserved"
    ] = any(
        "merchant"
        in
        item.lower()
        for item
        in sanitized
    )

    # =====================================================
    # WORKING-IMAGE RECOVERY PROMPT
    # =====================================================

    fake_qa = QAEvaluation(

        score=59.0,

        scores={
            key:
                70.0
            for key
            in QA_WEIGHTS
        },

        passed=False,

        strengths=[],

        problems=[
            "Merchant fusion failed."
        ],

        correction_instruction=(
            "Strengthen service integration."
        ),

        critical_blockers=[
            "stc_merchant_fusion_failed"
        ],

        target_reached=False,

        delivery_approved=False,

        decision="rebuild",

        raw={
            "decision":
                "rebuild",

            "_xpand_flags": {
                "merchant_fusion_failed":
                    True,
            },
        },
    )

    recovery_prompt = (
        build_concept_recovery_prompt(

            qa=(
                fake_qa
            ),

            compiled=(
                brittle_compiled
            ),

            aspect_ratio="4:5",
        )
    )

    tests[
        "recovery_uses_working_image_language"
    ] = (
        "WORKING IMAGE"
        in
        recovery_prompt
    )

    tests[
        "recovery_allows_safe_geometry_change"
    ] = (
        "failed geometry does not"
        in
        recovery_prompt.lower()
    )

    # =====================================================
    # ADAPTIVE POLICY
    # =====================================================

    good_qa = QAEvaluation(

        score=94.0,

        scores={
            key:
                94.0
            for key
            in QA_WEIGHTS
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

        raw={
            "_xpand_flags": {}
        },
    )

    tests[
        "excellent_high_alert_no_second_call"
    ] = (
        choose_adaptive_action(
            good_qa,
            high_alert=True,
        )
        ==
        "none"
    )

    adaptive_qa = QAEvaluation(

        score=89.0,

        scores={
            key:
                89.0
            for key
            in QA_WEIGHTS
        },

        passed=True,

        strengths=[],

        problems=[
            "Material hierarchy can improve."
        ],

        correction_instruction=(
            "Refine materials."
        ),

        critical_blockers=[],

        target_reached=False,

        delivery_approved=True,

        decision=(
            "adaptive_release"
        ),

        raw={
            "_xpand_flags": {}
        },
    )

    tests[
        "high_alert_release_gets_refinement"
    ] = (
        choose_adaptive_action(
            adaptive_qa,
            high_alert=True,
        )
        ==
        "premium_refinement"
    )

    concept_fail_qa = QAEvaluation(

        score=60.0,

        scores={
            **{
                key:
                    80.0
                for key
                in QA_WEIGHTS
            },

            "concept_execution":
                55.0,

            "message_clarity_without_text":
                60.0,

            "advertising_readiness":
                60.0,
        },

        passed=False,

        strengths=[],

        problems=[
            "merchant fusion failed"
        ],

        correction_instruction=(
            "Recover the service mechanism."
        ),

        critical_blockers=[
            "stc_merchant_fusion_failed"
        ],

        target_reached=False,

        delivery_approved=False,

        decision="rebuild",

        raw={
            "decision":
                "rebuild",

            "_xpand_flags": {
                "merchant_fusion_failed":
                    True,
            },
        },
    )

    tests[
        "concept_failure_routes_to_recovery"
    ] = (
        choose_adaptive_action(
            concept_fail_qa,
            high_alert=True,
        )
        ==
        "concept_recovery"
    )

    # =====================================================
    # LOCAL STC BRAND PACK ACTUAL BYTES TEST
    # =====================================================

    local_reference_test_ok = False

    local_reference_count = 0

    local_reference_ids: List[str] = []

    if STC_BRAND_KIT_AVAILABLE:

        try:

            (
                selftest_refs,
                selftest_kit,
                selftest_assets,
            ) = load_stc_local_references(

                request=(
                    "STC Bank "
                    "التجارة الإلكترونية ونقاط البيع "
                    "واقعي فوتوغرافي"
                ),

                max_total=(
                    MAX_STC_PHYSICAL_REFERENCE_IMAGES
                ),

                rotation_key=(
                    "production-engine-v52-self-test"
                ),
            )

            local_reference_count = len(
                selftest_refs
            )

            local_reference_ids = [
                item.source_id
                for item
                in selftest_refs
            ]

            local_reference_test_ok = bool(
                selftest_kit
                and
                len(
                    selftest_refs
                )
                >=
                3
                and
                all(
                    item.image_bytes
                    for item
                    in selftest_refs
                )
            )

        except Exception as error:

            print(
                "⚠️ STC physical-reference self test:",
                clean_text(
                    error,
                    1500,
                ),
            )

    tests[
        "permanent_stc_actual_image_bytes"
    ] = (
        local_reference_test_ok
    )

    # =====================================================
    # RESULT
    # =====================================================

    all_ok = all(
        tests.values()
    )

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND PRODUCTION ENGINE V5.2"
    )
    print(
        " ZERO-COST PRODUCTION-SAFE SELF TEST"
    )
    print(
        "=========================================="
    )
    print("")

    for name, passed in tests.items():

        print(
            (
                "✅"
                if passed
                else
                "❌"
            ),
            name,
        )

    print("")
    print(
        "Local STC refs found:",
        local_reference_count,
    )

    for item in local_reference_ids:

        print(
            "  🖼️",
            item,
        )

    print("")

    if all_ok:

        print(
            (
                "XPAND Production Engine "
                "V5.2 self-test: PASS ✅"
            )
        )

    else:

        print(
            (
                "XPAND Production Engine "
                "V5.2 self-test: FAIL ❌"
            )
        )

        failures = [
            name
            for name, passed
            in tests.items()
            if not passed
        ]

        print(
            "Failed tests:",
            failures,
        )

        raise RuntimeError(
            (
                "XPAND Production Engine "
                "V5.2 self-test failed."
            )
        )

    print("")
    print(
        "✅ 5 STC refs may be loaded; max 3 sent to primary"
    )
    print(
        "✅ Working-image recovery instead of blank rebuild"
    )
    print(
        "✅ Max 2 refs during edit/recovery"
    )
    print(
        "✅ Short production render contract"
    )
    print(
        "✅ Brittle geometry can be safely reinterpreted"
    )
    print(
        "✅ QA evaluates semantic fidelity after reinterpretation"
    )
    print(
        "✅ Merchant fusion remains a hard quality requirement"
    )
    print(
        "✅ STC QA target remains 92"
    )
    print(
        "✅ STC release floor remains 88"
    )
    print(
        "✅ No generated text / logo / fake banking UI"
    )
    print(
        "✅ No Smart fallback policy changed here"
    )
    print(
        "🚫 No API calls were made"
    )
    print(
        "🚫 No images were generated"
    )
    print("")
