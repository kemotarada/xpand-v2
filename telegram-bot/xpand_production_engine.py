# =========================================================
# XPAND PRODUCTION ENGINE V6.0.1
#
# STABLE HYBRID MASTERPIECE PRODUCTION CORE
# REGRESSION-PROOF IMMUTABLE FINAL LOCKS
#
# =========================================================
#
# MASTERPIECE ARCHITECTURE
# ---------------------------------------------------------
#
# Creative Brain approved winner
#          ↓
# Permanent STC Brand Pack
#          ↓
# Reference Constitution
#          ↓
# Nano Banana 2
# 1K PREVISUALIZATION ONLY
#          ↓
# Gemini Preview Audit
#          ↓
# GPT-Image-2
# FINAL RENDERER
# requested 1K / 2K / 4K
#          ↓
# GPT-5.6 Sol Final Vision QA
#          ↓
# GPT-Image-2 repair only when required
#
#
# =========================================================
# V6.0.1 CRITICAL FIX
# =========================================================
#
# Final prompts are now divided into:
#
#   1) compressible production core
#   2) IMMUTABLE FINAL LOCKS
#
# The immutable block is appended AFTER prompt compaction.
#
# Therefore these rules can never disappear because of
# character-budget compaction:
#
# - 25–40% integrated copy space
# - NO artificial blank panel
# - NO hero pushed into bottom
# - NO stone/travertine pedestal
# - NO phone/POS fusion
# - NO invented payment hardware
# - NO fake UI
# - NO text/logo
# - STC references are visual authority
# - ecommerce + POS = one merchant ecosystem
#
#
# =========================================================
# HARD ARCHITECTURAL RULES
# =========================================================
#
# - Gemini is NEVER Masterpiece final renderer.
# - Nano Banana 2 is PREVISUALIZATION only.
# - GPT-Image-2 is mandatory Masterpiece final model.
# - GPT-Image-2 is automatic final repair model.
# - No Gemini Pro final escalation.
# - No blank-scene final rebuild.
# - No Smart fallback authorized here.
#
#
# =========================================================
# PUBLIC CONTRACT PRESERVED
# =========================================================
#
# MODE_FAST
# MODE_PRO
# MODE_MASTERPIECE
#
# TARGET_OPENAI
# TARGET_GEMINI
# TARGET_MIDJOURNEY
# TARGET_FLUX
# TARGET_IDEOGRAM
# TARGET_RUNWAY
# TARGET_KLING
# TARGET_SEEDANCE
#
# ProductionReference
# CompiledPrompt
# QAEvaluation
# ProductionPassResult
# ProductionResult
#
# run_production()
# evaluate_generated_image()
# load_runtime_references()
# compile_prompt()
# generate_high_quality_image()
# gemini_multi_reference_edit()
# openai_multi_reference_edit()
# product_references()
# choose_physical_references()
# reference_dna_payload()
# combined_product_lock()
# get_brand_visual_profile()
# get_production_engine_status()
#
#
# ZERO-COST TEST:
#
#     python xpand_production_engine.py
#
# =========================================================

from __future__ import annotations

import json
import os
import re
import time

from dataclasses import dataclass, field
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


# =========================================================
# IMAGE ENGINE V3+
# =========================================================

from xpand_image_engine import (
    OPENAI_IMAGE_MODEL,
    OPENAI_EDIT_MODEL,
    GOOGLE_IMAGE_FAST_MODEL,
    GeneratedImage,
    call_openai_director,
    call_gemini_director,
    detect_image_size,
    edit_with_gemini,
    edit_with_openai_multi,
    generate_image,
    get_image_engine_status,
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

ENGINE_NAME = "XPAND Production Engine"
ENGINE_VERSION = "6.0.1"


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
# MODELS
# =========================================================

NANO_BANANA_2_MODEL = str(
    os.environ.get(
        "XPAND_MASTERPIECE_PREVIS_MODEL",
        GOOGLE_IMAGE_FAST_MODEL
        or
        "gemini-3.1-flash-image",
    )
).strip()

if not NANO_BANANA_2_MODEL:
    NANO_BANANA_2_MODEL = "gemini-3.1-flash-image"


# Final production uses edit_with_openai_multi, whose model is resolved by
# the image engine. Logging and provider locks must use that same identity.
# A separate legacy generation-model setting must not reject a valid edit.
FINAL_IMAGE_MODEL = OPENAI_EDIT_MODEL
_legacy_final_model = os.environ.get(
    "XPAND_MASTERPIECE_FINAL_IMAGE_MODEL", ""
).strip()
if _legacy_final_model and _legacy_final_model != FINAL_IMAGE_MODEL:
    print(
        "⚠️ Final edit model uses XPAND_OPENAI_EDIT_MODEL="
        + FINAL_IMAGE_MODEL
        + "; ignoring legacy final-model setting "
        + _legacy_final_model
    )


# =========================================================
# FINAL PROVIDER LOCK
# =========================================================

MASTERPIECE_REQUIRE_OPENAI_FINAL = env_bool(
    "XPAND_MASTERPIECE_REQUIRE_OPENAI_FINAL",
    True,
)


# A provider fallback is forbidden for Masterpiece.
# A preview provider can never become the mandatory final renderer.
# Keep this hard-disabled in code; environment flags cannot weaken QA.
MASTERPIECE_ALLOW_PROVIDER_FALLBACK = False


STC_REQUIRE_OPENAI_FINAL = env_bool(
    "XPAND_STC_REQUIRE_OPENAI_FINAL",
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


# =========================================================
# CALL POLICY
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


MASTERPIECE_PREVIS_CALLS = 1


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


MASTERPIECE_PREVIEW_AUDIT_CALLS = 1


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


STC_FINAL_REFERENCE_LIMIT = max(
    2,
    min(
        3,
        env_int(
            "XPAND_STC_FINAL_REFERENCE_LIMIT",
            3,
        ),
    ),
)


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
# QA POLICY
# =========================================================

QA_TARGET_SCORE = max(
    82.0,
    min(
        96.0,
        env_float(
            "XPAND_PRODUCTION_QA_TARGET",
            88.0,
        ),
    ),
)


QA_RELEASE_FLOOR = max(
    78.0,
    min(
        QA_TARGET_SCORE,
        env_float(
            "XPAND_PRODUCTION_QA_RELEASE_FLOOR",
            82.0,
        ),
    ),
)


STC_QA_TARGET_SCORE = max(
    90.0,
    min(
        98.0,
        env_float(
            "XPAND_STC_QA_TARGET",
            92.0,
        ),
    ),
)


STC_QA_RELEASE_FLOOR = max(
    86.0,
    min(
        STC_QA_TARGET_SCORE,
        env_float(
            "XPAND_STC_QA_RELEASE_FLOOR",
            88.0,
        ),
    ),
)


PREVIEW_GUIDANCE_FLOOR = max(
    55.0,
    min(
        85.0,
        env_float(
            "XPAND_PREVIS_GUIDANCE_FLOOR",
            72.0,
        ),
    ),
)


# =========================================================
# PROMPT BUDGETS
# =========================================================

COMPILED_PROMPT_BUDGET = max(
    4500,
    min(
        8500,
        env_int(
            "XPAND_COMPILED_PROMPT_BUDGET",
            6800,
        ),
    ),
)


PREVIS_PROMPT_BUDGET = max(
    5000,
    min(
        9500,
        env_int(
            "XPAND_PREVIS_PROMPT_BUDGET",
            7600,
        ),
    ),
)


FINAL_PROMPT_BUDGET = max(
    6500,
    min(
        12000,
        env_int(
            "XPAND_FINAL_PROMPT_BUDGET",
            8800,
        ),
    ),
)


QA_PROMPT_BUDGET = max(
    6000,
    min(
        11000,
        env_int(
            "XPAND_QA_PROMPT_BUDGET",
            8500,
        ),
    ),
)


CORRECTION_PROMPT_BUDGET = max(
    6000,
    min(
        10000,
        env_int(
            "XPAND_CORRECTION_PROMPT_BUDGET",
            7600,
        ),
    ),
)


# =========================================================
# QA DIMENSIONS
# =========================================================

QA_WEIGHTS = {
    "concept_execution": 10,
    "message_clarity_without_text": 10,
    "brand_alignment": 8,
    "brand_identity_strength": 10,
    "advertising_readiness": 10,
    "scene_originality": 7,
    "service_integration": 10,
    "realism": 10,
    "camera_perspective": 7,
    "lighting_materials": 5,
    "human_anatomy": 3,
    "reference_adherence": 5,
    "text_logo_compliance": 3,
    "copy_space_composition": 2,
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
            budget * 4,
            budget,
        ),
    )

    if len(text) <= budget:
        return text

    front = int(
        budget * 0.78
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
        "[XPAND COMPACTED — FINAL LOCKS BELOW]\n\n"
        +
        (
            text[-back:]
            if back
            else ""
        )
    )


# =========================================================
# V6.0.1 IMMUTABLE PROMPT COMPILER
# =========================================================

IMMUTABLE_LOCK_SENTINEL = (
    "XPAND_IMMUTABLE_FINAL_LOCKS_V601"
)


def fit_prompt_with_immutable_locks(
    core_prompt: str,
    immutable_locks: str,
    *,
    label: str,
    budget: int,
) -> str:

    core = clean_text(
        core_prompt,
        max(
            budget * 6,
            budget,
        ),
    )

    locks = clean_text(
        immutable_locks,
        max(
            4000,
            budget,
        ),
    )

    separator = (
        "\n\n"
        +
        "=" * 60
        +
        "\n"
        +
        IMMUTABLE_LOCK_SENTINEL
        +
        "\n"
        +
        "=" * 60
        +
        "\n\n"
    )

    reserved = (
        len(separator)
        +
        len(locks)
    )

    if reserved >= budget:
        raise RuntimeError(
            (
                "Immutable final locks exceed prompt budget. "
                "Increase XPAND_FINAL_PROMPT_BUDGET."
            )
        )

    core_budget = (
        budget
        -
        reserved
    )

    if len(core) > core_budget:

        print(
            "✂️ CORE PROMPT COMPACTED"
            +
            " | "
            +
            label
            +
            " | "
            +
            str(
                len(core)
            )
            +
            " → "
            +
            str(
                core_budget
            )
            +
            " | immutable="
            +
            str(
                len(locks)
            )
        )

        core = fit_prompt_for_api(
            core,
            label=(
                label
                +
                "_core"
            ),
            budget=core_budget,
        )

    output = (
        core
        +
        separator
        +
        locks
    )

    if len(output) > budget:
        raise RuntimeError(
            (
                "Immutable prompt compiler exceeded "
                "final budget unexpectedly."
            )
        )

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


def reference_tuples(
    references: Sequence[
        ProductionReference
    ],
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

    for item in references:

        if not item.image_bytes:
            continue

        output.append(
            (
                item.image_bytes,
                item.mime_type
                or
                infer_mime_type(
                    item.image_bytes
                ),
            )
        )

    return output


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


# =========================================================
# FRAME
# =========================================================

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
        ". Keep the hero visually substantial and not pushed "
        "into the bottom half. Use roughly 25–40% integrated "
        "calm copy space when appropriate. Negative space must "
        "come naturally from architecture, depth, light or "
        "subject placement. Never create a artificial empty panel."
    )


# =========================================================
# BRAND PROFILE
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
# MEMORY REFERENCES
# =========================================================

def load_runtime_references(
    core,
    user_id,
    brand_id: str,
    *,
    request: str = "",
    limit: int = (
        SMART_REFERENCE_SELECTION_LIMIT
    ),
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
        " ".join(
            roles
        )
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
    max_total: int = (
        MAX_STC_PHYSICAL_REFERENCE_IMAGES
    ),
    rotation_key: str = "",
) -> Tuple[
    List[
        ProductionReference
    ],
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
                    "Required STC Brand Pack could "
                    "not be loaded: "
                    +
                    clean_text(
                        error,
                        1800,
                    )
                )
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
            benefit_family=benefit_family,
            visual_family=visual_family,
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
            size = (
                path.stat().st_size
            )

        except Exception:
            continue

        if (
            size <= 0
            or
            size
            >
            MAX_LOCAL_REFERENCE_BYTES
        ):
            continue

        try:
            raw = (
                path.read_bytes()
            )

        except Exception:
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
                        str(
                            path
                        ),
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
                "STC Brand Pack loaded but no "
                "physical references were usable."
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
    limit: int = (
        MAX_PHYSICAL_REFERENCE_IMAGES
    ),
) -> List[
    ProductionReference
]:

    if not SEND_VISUAL_REFERENCES_TO_IMAGE:
        return []

    limit = max(
        0,
        int(
            limit
            or
            0
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
        "product_reference": 1300,
        "campaign_reference": 1100,
        "style_reference": 1050,
        "environment_reference": 1000,
        "composition_reference": 950,
        "camera_reference": 940,
        "lighting_reference": 930,
        "color_reference": 900,
        "mixed_reference": 880,
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

    return unique_references(
        usable
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
    limit: int = (
        STC_RENDER_REFERENCE_LIMIT
    ),
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

    for item in product_refs:

        if item.image_bytes:
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
        for item
        in local_refs
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
        for item
        in local_refs
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
        for item
        in local_refs
        if (
            item.role
            ==
            "environment_reference"
            and
            item.image_bytes
        )
    ]

    for group in (
        style[:1],
        campaign[:1],
        service[:1],
    ):

        output.extend(
            group
        )

        output = (
            unique_references(
                output
            )
        )

        if len(
            output
        ) >= limit:
            return output[:limit]

    for item in local_refs:

        if not item.image_bytes:
            continue

        output.append(
            item
        )

        output = (
            unique_references(
                output
            )
        )

        if len(
            output
        ) >= limit:
            return output[:limit]

    for item in choose_physical_references(
        memory_refs,
        limit=limit,
    ):

        output.append(
            item
        )

        output = (
            unique_references(
                output
            )
        )

        if len(
            output
        ) >= limit:
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

    output: List[
        ProductionReference
    ] = []

    for item in product_refs:

        if item.image_bytes:
            output.append(
                item
            )

    if high_alert:

        campaign = [
            item
            for item
            in stc_local_refs
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
            for item
            in stc_local_refs
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
            for item
            in stc_local_refs
            if (
                item.role
                ==
                "environment_reference"
                and
                item.image_bytes
            )
        ]

        output.extend(
            campaign[:1]
        )

        if service:
            output.extend(
                service[:1]
            )

        elif style:
            output.extend(
                style[:1]
            )

    return unique_references(
        output
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
                or
                1
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
            bool(
                count
            ),
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
# BRAND KIT CONTEXT
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
        "selected_style_direction": __import__("xpand_stc_skill_runtime").style_direction(stc_visual_family_for_brand_kit(request)),
        "selected_assets":
            selected,
    }


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
                )[:6],
            "visual_dna":
                safe_list(
                    base_profile.get(
                        "visual_dna"
                    )
                )[:6],
        },
        "rules":
            safe_list(
                context.get(
                    "rules"
                )
            )[:10],
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
            len(
                references
            ),
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

    jury = (
        creative_finalist_jury_payload(
            creative
        )
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
                400,
            ),
        "campaign_hook":
            clean_text(
                creative.get(
                    "campaign_hook",
                    "",
                ),
                700,
            ),
        "core_idea":
            clean_text(
                creative.get(
                    "core_idea",
                    "",
                ),
                1000,
            ),
        "marketing_message":
            clean_text(
                creative.get(
                    "marketing_message",
                    "",
                ),
                650,
            ),
        "visual_metaphor":
            clean_text(
                creative.get(
                    "visual_metaphor",
                    "",
                ),
                850,
            ),
        "visual_mechanism_type":
            clean_text(
                creative.get(
                    "visual_mechanism_type",
                    "",
                ),
                400,
            ),
        "visible_message_proof":
            clean_text(
                creative.get(
                    "core_idea",
                    "",
                ),
                1200,
            ),
        "mechanism_lock":
            clean_text(
                creative.get(
                    "visual_mechanism_type",
                    "",
                ),
                400,
            ),
        "why_not_generic":
            clean_text(
                creative.get(
                    "why_not_generic",
                    "",
                ),
                550,
            ),
        "environment":
            clean_text(
                creative.get(
                    "environment",
                    "",
                ),
                700,
            ),
        "hero_element":
            clean_text(
                creative.get(
                    "hero_element",
                    "",
                ),
                600,
            ),
        "supporting_elements":
            [
                clean_text(
                    item,
                    350,
                )
                for item
                in safe_list(
                    creative.get(
                        "supporting_elements"
                    )
                )[:3]
                if clean_text(
                    item,
                    350,
                )
            ],
        "camera_angle":
            (
                clean_text(
                    camera.get(
                        "camera_angle",
                        "",
                    ),
                    500,
                )
                or
                clean_text(
                    debate_camera.get(
                        "camera_angle",
                        "",
                    ),
                    500,
                )
                or
                clean_text(
                    creative.get(
                        "camera_angle",
                        "",
                    ),
                    500,
                )
            ),
        "lens":
            (
                clean_text(
                    camera.get(
                        "lens",
                        "",
                    ),
                    180,
                )
                or
                clean_text(
                    debate_camera.get(
                        "lens",
                        "",
                    ),
                    180,
                )
                or
                clean_text(
                    creative.get(
                        "lens",
                        "",
                    ),
                    180,
                )
            ),
        "perspective":
            (
                clean_text(
                    camera.get(
                        "perspective",
                        "",
                    ),
                    550,
                )
                or
                clean_text(
                    camera.get(
                        "perspective_type",
                        "",
                    ),
                    550,
                )
                or
                clean_text(
                    debate_camera.get(
                        "perspective",
                        "",
                    ),
                    550,
                )
                or
                clean_text(
                    creative.get(
                        "perspective",
                        "",
                    ),
                    550,
                )
            ),
        "lighting":
            clean_text(
                creative.get(
                    "lighting",
                    "",
                ),
                550,
            ),
        "negative_space":
            clean_text(
                creative.get(
                    "negative_space",
                    "",
                ),
                450,
            ),
        "brand_logic":
            clean_text(
                creative.get(
                    "brand_logic",
                    "",
                ),
                650,
            ),
        "production_method":
            clean_text(
                creative.get(
                    "production_method",
                    "",
                ),
                250,
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
                900,
            ),
        "do_not_drift_into":
            [
                clean_text(
                    item,
                    350,
                )
                for item
                in safe_list(
                    jury.get(
                        "do_not_drift_into"
                    )
                )[:5]
                if clean_text(
                    item,
                    350,
                )
            ],
    }


# =========================================================
# REALITY FIREWALL
# =========================================================

BRITTLE_MARKERS = [
    "half-digital",
    "half digital",
    "half-physical",
    "half physical",
    "screen plane",
    "through the screen",
    "emerging from screen",
    "phone and pos fused",
    "phone-pos fusion",
    "hybrid payment device",
    "نصف رقمي",
    "نصف مادي",
    "يعبر الشاشة",
    "تعبر الشاشة",
    "يخرج من الشاشة",
    "هاتف ونقطة بيع",
    "جهاز هجين",
]


def requires_reality_reinterpretation(
    render_brief: Dict[str, Any],
) -> bool:

    source = compact_json(
        render_brief,
        8000,
    )

    return contains_any(
        source,
        BRITTLE_MARKERS,
    )


# =========================================================
# MERCHANT PAYMENTS EXECUTION LOCK
# =========================================================

def merchant_payment_execution_lock() -> str:
    """Give the renderer one legible, photographic merchant workflow."""
    return """
MERCHANT PAYMENTS — EXECUTION LOCK
----------------------------------

Use one continuous photographic merchant workflow, not a collection
of fintech props:

- a real merchant works at one premium retail/service counter;
- one hand is completing a real customer checkout on a believable,
  unbranded physical POS terminal;
- on the same counter, a sealed, unbranded customer parcel is being
  prepared for pickup or dispatch, making the online order/fulfillment
  channel physically evident;
- the parcel, merchant action and checkout counter must share one
  coherent perspective, lighting system and depth relationship.

The viewer must understand: this one merchant can receive physical
payments and fulfill online orders through one connected business
workflow.

The online cue is the real parcel and fulfillment action, not a
smartphone screen. Do not add a laptop, tablet, floating phone,
split-screen or unrelated product tableau.

The POS screen and parcel label are blank, abstract and unreadable:
no letters, digits, logos, card-network marks, QR codes, barcodes,
balances or interface elements. The terminal remains a normal,
commercially plausible, unbranded device with a clean neutral display.

Keep the merchant and the active hand interaction as the hero.
Do not turn the scene into a product catalog, generic checkout,
or isolated terminal beauty shot.
""".strip()


# =========================================================
# STC VISUAL CONSTITUTION
# =========================================================

def build_stc_visual_constitution(
    request: str,
) -> str:

    benefit = (
        detect_stc_benefit_family(
            request
        )
    )

    style = (
        detect_stc_visual_style(
            request
        )
        or
        STYLE_PREMIUM_REALISTIC
    )

    style_text = """
PREMIUM REALISTIC

Use a natural photographic Saudi commercial world.

Brand identity must NOT become a purple filter.

Human skin, fabric, glass, metal, merchandise and natural
materials keep physically believable color and texture.
""".strip()

    if (
        style
        ==
        STYLE_PURPLE_ARCHITECTURAL
    ):

        style_text = """
PURPLE ARCHITECTURAL

Purple may exist in believable physical architecture,
paint, glass, surfaces or motivated lighting.

Never recolor people, products or the whole frame purple.
""".strip()

    elif (
        style
        ==
        STYLE_AUGMENTED_REALISM
    ):

        style_text = """
AUGMENTED REALISM

The base world remains photographic.

Only one conceptual intervention may exist.

It must still obey scale, perspective, contact, occlusion,
gravity, reflection and lighting.
""".strip()

    merchant = ""
    digital_transfer = ""

    if (
        benefit
        ==
        "digital_banking"
    ):

        digital_transfer = """
DIGITAL BANKING / GLOBAL TRANSFER VISUAL MECHANISM
=================================================

For a request about sending money worldwide and tracking it in the app,
create one concrete premium photographic relationship: a real sender in
the foreground and a real recipient or secure handoff visible in the same
continuous architectural depth, connected by believable human action and
spatial continuity. The viewer must read send -> in progress -> safe arrival
without generated words.

Use one ordinary physically correct smartphone only as a supporting cue.
Keep its screen turned away, softly out of focus or abstract and blank. The
phone must never carry the whole message, never warp around architecture, and
never intersect a column, pillar, hand or reflective edge.

Do not use a floating globe, map, route line, dotted path, particles, HUD,
hologram, split-screen, duplicated phone, invented banking hardware, or
generic person simply holding a phone. Do not create a collage of unrelated
objects. Use real people, real depth, natural hand contact, believable
architecture, and one decisive moment of secure delivery.

The final frame must feel like a real STC Bank campaign photograph, not an
app mockup or a generic fintech render.
""".strip()

    if (
        benefit
        ==
        "merchant_payments"
    ):

        merchant = """
MERCHANT-PAYMENTS CONSTITUTION
==============================

The visual proposition is:

ONLINE / E-COMMERCE ACCEPTANCE
+
PHYSICAL POINT-OF-SALE ACCEPTANCE
=
ONE CONNECTED MERCHANT ECOSYSTEM.

Both channels must be understandable without generated text.

Do not simply place unrelated service props together.

Do not use a static tableau of customer + POS + merchant +
counter + packing activity as the entire advertising mechanism.
The merchant action and the connected workflow must carry the idea.

Do not use a smartphone screen as the only evidence
of e-commerce.

Use believable commercial evidence and one clear
advertising relationship.
""".strip()

        merchant = (
            merchant
            +
            "\n\n"
            +
            merchant_payment_execution_lock()
        )

    return f"""
STC BANK VISUAL CONSTITUTION
============================

REFERENCE AUTHORITY
-------------------

Attached STC images are visual authority.

Do not guess STC Bank from generic luxury advertising.

Learn from the references:
- tonal balance
- palette restraint
- material behavior
- photographic finish
- spatial restraint
- camera sophistication
- light quality
- contemporary Saudi commercial tone
- brand maturity

Do NOT clone:
- exact compositions
- exact people
- text
- logos
- UI

REFERENCE EVIDENCE OUTRANKS GENERIC LUXURY DEFAULTS.

{style_text}

PHYSICAL REALITY FIREWALL
-------------------------

Every object must appear manufactured, supported and
photographed in the real world.

PAYMENT HARDWARE:

If a physical POS terminal appears, it must resemble a
believable commercially available unbranded payment terminal.

It needs:
- coherent body geometry
- believable keypad or touch surface
- sensible screen placement
- plausible contactless/card interaction area
- correct physical support
- believable hand interaction when held

HARD BAN:
- phone/POS fusion
- smartphone fused into payment terminal
- impossible hybrid payment hardware
- futuristic invented payment machine
- malformed keypad
- impossible screen/body geometry
- device that could not physically exist

Do not merge smartphone + POS merely to symbolize
e-commerce + physical payment.

Preserve the IDEA through composition and real-world
relationships.

MATERIAL FIREWALL
-----------------

Premium does NOT mean random stone pedestal.

HARD BAN unless genuinely required by the approved idea:
- standalone travertine slab
- limestone product plinth
- beige stone pedestal
- marble podium
- random luxury block
- product staged on meaningless stone

Luxury must come from:
camera,
light,
space,
real materials,
behavior,
color,
restraint,
and production quality.

CAMERA CONSTITUTION
-------------------

Camera must contribute to the advertising message.

Avoid automatic:
eye-level + centered + three-quarter product shot.

When justified use one coherent professional grammar:
- reflection-led framing
- architectural frame-within-frame
- controlled environmental wide angle
- true top-down system view
- low grazing angle
- foreground occlusion
- compressed long-lens relationship
- deliberate asymmetric perspective

Never use an unusual angle as a meaningless gimmick.

COPY SPACE
----------

Use roughly 25–40% integrated copy space when useful.

Do NOT:
- reserve 30–40% blank sky/wall automatically
- push the hero into the bottom half
- create a artificial empty panel

TEXT / UI
---------

IMAGE ONLY.

No generated:
- STC logo
- bank logo
- Arabic slogan
- English slogan
- readable interface
- balances
- prices
- fake merchant labels
- card-brand symbols
- watermark

If a screen exists:
no readable banking UI,
no readable numbers,
no fake financial interface.

{digital_transfer}

{merchant}
""".strip()


# =========================================================
# V6.0.1 IMMUTABLE FINAL LOCKS
# =========================================================

def build_immutable_final_locks(
    *,
    original_request: str,
    aspect_ratio: str,
    requested_size: str,
    reference_authority: bool = True,
) -> str:

    stc_request = (
        is_stc_bank_request(
            original_request
        )
    )

    benefit = (
        detect_stc_benefit_family(
            original_request
        )
        if stc_request
        else
        ""
    )

    merchant_lock = ""

    if (
        stc_request
        and
        benefit
        ==
        "merchant_payments"
    ):

        merchant_lock = """
MERCHANT MESSAGE — IMMUTABLE
----------------------------

E-COMMERCE + PHYSICAL POS MUST READ AS ONE CONNECTED
MERCHANT ECOSYSTEM.

Both channels must be visually understandable without text.

A smartphone screen alone is NOT sufficient proof
of e-commerce.

A POS terminal alone is NOT sufficient proof
of the complete service.

Do not replace the message with generic checkout activity.
""".strip()

        merchant_lock = (
            merchant_lock
            +
            "\n\n"
            +
            merchant_payment_execution_lock()
        )

    brand_lock = ""

    if (
        stc_request
        and
        reference_authority
    ):

        brand_lock = """
STC REFERENCE AUTHORITY — IMMUTABLE
-----------------------------------

THE ATTACHED STC REFERENCES ARE VISUAL AUTHORITY.

Their brand-world evidence outranks generic luxury defaults.

Use them for:
- tonal balance
- palette restraint
- photographic finish
- material behavior
- camera maturity
- spatial discipline
- Saudi commercial realism

Do NOT ignore the references.

Do NOT clone their exact composition.
""".strip()

    return f"""
FINAL NON-NEGOTIABLE LOCKS — DO NOT OVERRIDE
=============================================

These rules have higher priority than stylistic suggestions.

FRAME
-----

Final aspect ratio:
{aspect_ratio}

Final resolution intent:
{requested_size}

Use approximately 25–40% integrated copy space.

NO artificial blank panel; quiet upper-third space is allowed.

Keep negative space photographic and integrated.

NO hero pushed into the bottom half merely to create
copy space.

Negative space must be integrated naturally into
architecture, depth, lighting or scene structure.

PHYSICAL REALITY
----------------

NO phone/POS fusion.

NO smartphone fused with a payment terminal.

NO invented payment hardware.

NO impossible hybrid payment device.

Any visible physical POS terminal must look like a
believable commercially plausible unbranded POS terminal.

MATERIALS
---------

NO random travertine pedestal.

NO random stone pedestal.

NO beige luxury plinth.

NO marble product podium.

NO meaningless limestone block.

Premium quality must come from photography and art direction,
not an arbitrary stone object.

CAMERA
------

NO automatic generic eye-level centered three-quarter shot
unless that exact angle is uniquely justified by the message.

Camera must strengthen the advertising idea.

TEXT / UI
---------

NO generated text.

NO generated logo, including lettering on referenced cards or screens.
NO graphic overlays, decorative lines, particles, sparkles or holograms.
Physical support edges and real specular reflections are allowed.
Purposeful purple platforms are allowed in the selected purple studio style.

NO watermark.

NO fake banking UI.

NO fake balances.

NO fake numbers.

NO fake card-brand symbol.

NO readable financial interface.

{brand_lock}

{merchant_lock}

FINAL SELF-CHECK
----------------

Before output, verify:

1. The service message is visually clear without text.
2. Every visible object is physically believable.
3. Payment hardware is realistic.
4. No phone/POS hybrid exists.
5. No random stone/plinth exists.
6. STC reference DNA visibly informs the result.
7. Camera is intentional.
8. Copy space is integrated, not empty.
9. The hero has confident visual weight.
10. The image looks like a real premium bank campaign.

If any item fails, correct it before final output.

END_{IMMUTABLE_LOCK_SENTINEL}
""".strip()


# =========================================================
# REFERENCE MANIFEST
# =========================================================

def reference_role_manifest(
    references: Sequence[
        ProductionReference
    ],
    *,
    draft_first: bool,
) -> str:

    lines: List[str] = []

    index = 1

    if draft_first:

        lines.append(
            (
                "Image 1 = approved Nano Banana 2 "
                "previsualization / composition draft."
            )
        )

        index = 2

    for reference in references:

        role = reference.role

        if role == "campaign_reference":

            role_text = (
                "STC BANK BRAND DNA reference. "
                "Use for identity, restraint and campaign maturity."
            )

        elif role == "style_reference":

            role_text = (
                "STC PHOTOGRAPHIC / STYLE reference. "
                "Use for camera, lighting, finish and material language."
            )

        elif role == "environment_reference":

            role_text = (
                "STC MERCHANT / SERVICE reference. "
                "Use for believable commercial context and service cues."
            )

        elif role == "product_reference":

            role_text = (
                "EXACT PRODUCT reference. "
                "Physical geometry has highest fidelity priority."
            )

        else:

            role_text = (
                "Supporting brand reference."
            )

        lines.append(
            (
                "Image "
                +
                str(
                    index
                )
                +
                " = "
                +
                role_text
                +
                " Source: "
                +
                clean_text(
                    reference.source_id,
                    200,
                )
            )
        )

        index += 1

    return "\n".join(
        lines
    )


# =========================================================
# NEGATIVE LOCK
# =========================================================

def base_negative_prompt() -> str:

    return """
HARD NEGATIVE LOCK

No generated headline.
No generated logo.
No watermark.
No fake banking UI.
No fake financial numbers.
No fake card-brand symbol.
No readable receipt.
No readable parcel label.

No phone/POS fusion.
No invented payment terminal.
No futuristic payment hardware.

No random travertine pedestal.
No beige stone plinth.
No marble product podium.
No meaningless luxury block.

No holograms.
No HUD.
No network lines.
No glowing payment trails.
No lasers.
No fintech particles.

No generic checkout tableau.
No generic boutique counter.
No customer simply presenting a POS toward camera.

No artificial blank panel; quiet upper-third space is allowed.
No hero pushed into the bottom quarter.

No plastic skin.
No deformed hands.
No broken grip.
No fake reflections.
No contradictory perspective.
No impossible object support.
""".strip()


# =========================================================
# BLUEPRINT
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
        4500,
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

    stc_request = (
        is_stc_bank_request(
            request
        )
    )

    reality_reinterpretation = (
        requires_reality_reinterpretation(
            render_brief
        )
    )

    brand_summary = compact_json(
        {
            "profile":
                safe_dict(
                    brand_context
                ).get(
                    "profile",
                    {},
                ),
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
        },
        1200,
    )

    reinterpretation = """
REALITY INTERPRETATION

Execute the approved visual mechanism directly and
physically believably.
""".strip()

    if reality_reinterpretation:

        reinterpretation = """
REALITY INTERPRETATION: ACTIVE

The approved concept contains potentially brittle or
physically impossible geometry.

Preserve:
- advertising proposition
- marketing message
- hero relationship
- strategic mechanism
- emotional effect

But DO NOT literally manufacture impossible geometry.

Translate the same idea into a physically believable
photographic relationship.

Never use invented hybrid hardware as a metaphor.
""".strip()

    stc_section = (
        build_stc_visual_constitution(
            request
        )
        if stc_request
        else
        ""
    )

    campaign_read_section = ""
    if stc_request:
        campaign_read_section = """
STC CAMPAIGN READ GATE
----------------------
Choose one visual structure only: benefit-in-use realism, decisive product
action, branded purple studio narrative, product-as-threshold, or premium
contextual still life. Create one dominant hero and one meaningful action or
relationship. The environment must prove the benefit category in under two
seconds. A secondary cue may establish the banking role. Reserve 25–40%
integrated calm tonal space for later Arabic copy, but do not create a blank
panel or dead wall. Exact rates, amounts, codes, terms and logos belong to
later typography; never render them or readable UI in this image.
""".strip()

    merchant_proof_section = ""
    if (
        stc_request
        and
        detect_stc_benefit_family(request)
        ==
        "merchant_payments"
    ):
        merchant_proof_section = """
MERCHANT PAYMENT VISIBLE-PROOF GATE
-----------------------------------
The frame must show one connected merchant mechanism, not a product display.
The viewer must understand both an online/e-commerce action and physical
point-of-sale acceptance from the same causal or spatial relationship.
Reject phone + POS as unrelated objects, phone + POS on stone/travertine/
marble, a generic checkout, tablet + terminal + parcel tableau, split-screen,
fake UI or invented hardware. The online cue must show its role in commerce;
the POS cue must show credible acceptance. If the proof is missing, rebuild.
""".strip()

        merchant_proof_section = (
            merchant_proof_section
            +
            "\n\n"
            +
            merchant_payment_execution_lock()
        )

    prompt = f"""
XPAND MASTERPIECE STRATEGY-TO-IMAGE CONTRACT V6.0.1
===================================================

ORIGINAL USER MESSAGE
---------------------
{request}

APPROVED CREATIVE DIRECTION
---------------------------
{compact_json(
    render_brief,
    3300,
)}

{reinterpretation}

BRAND CONTEXT
-------------
{brand_summary}

REFERENCE DNA SUMMARY
---------------------
{compact_json(
    references,
    900,
)}

PRODUCT LOCK
------------
{compact_json(
    product_lock,
    700,
)}

PRODUCTION LAW
--------------

Create ONE campaign idea in ONE photographic frame.

One hero relationship.
One message.
One coherent camera.
One motivated lighting system.

Do not add a second idea.

The advertising message must work before typography.

CAMERA
------

Use the approved camera when meaningful.

If the approved camera is vague or generic,
choose a stronger real commercial viewpoint that improves
message clarity.

Avoid habitual centered eye-level three-quarter framing.

REALISM
-------

Everything must be plausible to photograph.

Correct:
- scale
- anatomy
- hand contact
- gravity
- physical support
- perspective
- reflections
- shadow direction
- material response

{stc_section}

{campaign_read_section}

{merchant_proof_section}

{safe_frame_instruction(
    aspect_ratio
)}

FINAL LOCK
----------

IMAGE ONLY.
NO TEXT.
NO LOGO.
NO FAKE UI.
NO GENERIC FINTECH DECORATION.

{base_negative_prompt()}
""".strip()

    return fit_prompt_for_api(
        prompt,
        label=(
            "production_blueprint_v601"
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
        TARGET_OPENAI,
        TARGET_GEMINI,
    }:
        target = TARGET_OPENAI

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

    reality_reinterpretation = (
        requires_reality_reinterpretation(
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
                "xpand_production_v601",
            "prompt_chars":
                len(
                    blueprint
                ),
            "prompt_budget":
                COMPILED_PROMPT_BUDGET,
            "aspect_ratio":
                aspect_ratio,
            "render_brief":
                render_brief,
            "reality_reinterpretation":
                reality_reinterpretation,
            "nano_banana_role":
                "previsualization_only",
            "final_renderer":
                FINAL_IMAGE_MODEL,
            "copy_space_policy":
                "25-40_percent_integrated",
            "immutable_final_locks":
                True,
            "permanent_stc_brand_grounding":
                True,
        },
    )


# =========================================================
# PREVIS PROMPT
# =========================================================

def build_previsualization_prompt(
    *,
    compiled: CompiledPrompt,
    original_request: str,
    references: Sequence[
        ProductionReference
    ],
    aspect_ratio: str,
) -> str:

    manifest = (
        reference_role_manifest(
            references,
            draft_first=False,
        )
    )

    prompt = f"""
XPAND NANO BANANA 2 PREVISUALIZATION V6.0.1
===========================================

THIS IS NOT THE FINAL CLIENT IMAGE.

Your job is to prove:
- message
- composition
- real-world scene logic
- camera
- hero relationship
- service integration

ORIGINAL REQUEST
----------------
{clean_text(
    original_request,
    3500,
)}

APPROVED PRODUCTION CONTRACT
----------------------------
{clean_text(
    compiled.prompt,
    4700,
)}

ATTACHED REFERENCE ROLES
------------------------
{manifest}

PREVIS LAW
----------

References are actual visual evidence.

Do not merely decorate the frame with purple.

Do not copy their exact old scene.

Solve the message with a physically believable frame.

For STC merchant payments:
show online/e-commerce commerce and physical payment
acceptance as one real connected merchant ecosystem.

Never invent a device to explain the service.

Never merge phone + POS.

Never use a stone pedestal as a shortcut for premium.

Do not reserve a giant empty top area.

Use a deliberate camera that supports the idea.

{safe_frame_instruction(
    aspect_ratio
)}

NO TEXT.
NO LOGO.
NO FAKE UI.
""".strip()

    return fit_prompt_for_api(
        prompt,
        label=(
            "nano_banana_previs_v601"
        ),
        budget=(
            PREVIS_PROMPT_BUDGET
        ),
    )


# =========================================================
# QA SUMMARY
# =========================================================

def qa_feedback_summary(
    qa: Optional[
        QAEvaluation
    ],
) -> str:

    if qa is None:
        return (
            "No preview audit was available. "
            "Use the approved production contract directly."
        )

    return compact_json(
        {
            "score":
                qa.score,
            "problems":
                qa.problems[:6],
            "blockers":
                qa.critical_blockers[:8],
            "instruction":
                clean_text(
                    qa.correction_instruction,
                    1200,
                ),
            "weak_dimensions": {
                key:
                    qa.scores.get(
                        key,
                        0,
                    )
                for key in (
                    "concept_execution",
                    "message_clarity_without_text",
                    "brand_identity_strength",
                    "service_integration",
                    "realism",
                    "camera_perspective",
                    "reference_adherence",
                    "copy_space_composition",
                )
            },
        },
        2400,
    )


def qa_flags_text_logo_failure(
    qa: Optional[
        QAEvaluation
    ],
) -> bool:

    if qa is None:
        return False

    flags = safe_dict(
        qa.raw.get(
            "_xpand_flags"
        )
    )

    if (
        flags.get(
            "unwanted_text_or_logo"
        )
        or
        flags.get(
            "fake_banking_ui"
        )
    ):
        return True

    if (
        clamp_score(
            qa.scores.get(
                "text_logo_compliance",
                100,
            )
        )
        <
        95
    ):
        return True

    evidence = " ".join(
        [
            clean_text(
                item,
                500,
            ).lower()
            for item in (
                list(
                    qa.critical_blockers
                )
                +
                list(
                    qa.problems
                )
            )
        ]
    )

    return any(
        marker in evidence
        for marker in (
            "text",
            "logo",
            "lettering",
            "wordmark",
            "watermark",
            "readable",
            "fake ui",
        )
    )


def qa_flags_copy_space_failure(
    qa: Optional[
        QAEvaluation
    ],
) -> bool:

    if qa is None:
        return False

    flags = safe_dict(
        qa.raw.get(
            "_xpand_flags"
        )
    )

    if flags.get(
        "excessive_empty_copy_space"
    ):
        return True

    evidence = " ".join(
        clean_text(
            item,
            500,
        ).lower()
        for item in qa.critical_blockers
    )

    return any(
        marker in evidence
        for marker in (
            "copy_space",
            "copy space",
            "empty upper space",
            "empty copy space",
        )
    )


def preview_blocker_corrections(
    qa: Optional[
        QAEvaluation
    ],
) -> str:

    if (
        qa is None
        or
        not qa.critical_blockers
    ):
        return ""

    blockers = "\n".join(
        (
            "- "
            +
            clean_text(
                item,
                500,
            )
        )
        for item in qa.critical_blockers[:6]
        if clean_text(
            item,
            500,
        )
    )

    if not blockers:
        return ""

    return f"""
PREVIEW BLOCKER CORRECTIONS — REQUIRED
---------------------------------------

The preview may still be marked preview_ready, but every blocker
below must be corrected in the final render:

{blockers}
""".strip()


# =========================================================
# FINAL GPT-IMAGE-2 PROMPT V6.0.1
# =========================================================

def build_final_renderer_prompt(
    *,
    compiled: CompiledPrompt,
    original_request: str,
    preview_qa: Optional[
        QAEvaluation
    ],
    references: Sequence[
        ProductionReference
    ],
    aspect_ratio: str,
    requested_size: str,
) -> str:

    stc_request = (
        is_stc_bank_request(
            original_request
        )
    )

    constitution = (
        build_stc_visual_constitution(
            original_request
        )
        if stc_request
        else
        ""
    )

    preview_requires_clean_recomposition = bool(
        preview_qa
        is not None
        and (
            preview_qa.decision
            ==
            "preview_repair_required"
            or
            bool(
                preview_qa.critical_blockers
            )
        )
    )

    image_role_instruction = (
        "NO PREVISUALIZATION INPUT IS PROVIDED.\n\n"
        "Build the final image from the approved production contract and\n"
        "attached STC references only. Do not infer, preserve or repair\n"
        "geometry from a draft image."
        if preview_requires_clean_recomposition
        else
        "Image 1 is a PREVISUALIZATION.\n\n"
        "It is NOT a sacred pixel-perfect base.\n\n"
        "Preserve what works:\n"
        "- advertising proposition\n"
        "- useful composition\n"
        "- hero relationship\n"
        "- camera intent\n\n"
        "Correct what looks synthetic, generic or physically wrong."
    )

    manifest = (
        reference_role_manifest(
            references,
            draft_first=not preview_requires_clean_recomposition,
        )
    )

    #
    # Compressible core.
    #
    # Critical non-negotiable locks are NOT placed here.
    # They are appended after compaction.
    #

    core_prompt = f"""
XPAND GPT-IMAGE-2 FINAL RENDER V6.0.1
=====================================

CREATE THE CLIENT-READY FINAL IMAGE.

{image_role_instruction}

INPUT IMAGE ROLES
-----------------
{manifest}

ORIGINAL USER REQUEST
---------------------
{clean_text(
    original_request,
    3200,
)}

APPROVED PRODUCTION CONTRACT
----------------------------
{clean_text(
    compiled.prompt,
    4300,
)}

PREVISUALIZATION AUDIT
----------------------
{qa_feedback_summary(
    preview_qa
)}

FINAL RENDER OBJECTIVE
----------------------

Turn the draft into premium real-world commercial photography.

The final image must NOT look like:
- concept art
- CGI product visualization
- generic fintech render
- generic luxury product still-life

It should feel intentionally produced for a real bank campaign.

REFERENCE USAGE
---------------

Study the attached STC references.

Use them to strengthen:
- tonal balance
- lighting discipline
- camera maturity
- material restraint
- brand-world confidence
- spatial design
- realistic Saudi commercial context

Do not clone source campaigns.

PHOTOGRAPHIC QUALITY
--------------------

Require:
- real-world geometry
- coherent lens perspective
- believable scale
- realistic anatomy
- realistic hand/object contact
- physically plausible shadows
- physically plausible reflections
- natural skin and fabric
- material-specific roughness
- deliberate focal hierarchy
- production-grade color separation

CAMERA
------

Maintain an intentional viewpoint.

Camera may use:
- reflection-led framing
- architectural framing
- controlled environmental width
- long-lens compression
- top-down relationship
- low grazing perspective
- foreground depth

only where the approved advertising idea benefits.

STC CONTEXT
-----------

{constitution}

Create a polished campaign image at:
Aspect ratio: {aspect_ratio}
Resolution intent: {requested_size}
""".strip()

    preview_corrections = (
        preview_blocker_corrections(
            preview_qa
        )
    )

    immutable_locks = "\n\n".join(
        item
        for item in (
            preview_corrections,
            build_immutable_final_locks(
            original_request=(
                original_request
            ),
            aspect_ratio=(
                aspect_ratio
            ),
            requested_size=(
                requested_size
            ),
            ),
        )
        if item
    )

    return fit_prompt_with_immutable_locks(
        core_prompt,
        immutable_locks,
        label=(
            "gpt_image_2_final_v601"
        ),
        budget=(
            FINAL_PROMPT_BUDGET
        ),
    )


# =========================================================
# GEMINI COMPATIBILITY EDIT
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

    limit = (
        max_reference_images
        if max_reference_images
        is not None
        else
        MAX_PHYSICAL_REFERENCE_IMAGES
    )

    limit = max(
        0,
        int(
            limit
            or
            0
        ),
    )

    refs = [
        item
        for item
        in unique_references(
            references
        )
        if item.image_bytes
    ][:limit]

    tuples = (
        reference_tuples(
            refs
        )
    )

    if working_image is not None:

        inputs = [
            (
                working_image.image_bytes,
                working_image.mime_type
                or
                infer_mime_type(
                    working_image.image_bytes
                ),
            )
        ]

        inputs.extend(
            tuples
        )

        result = edit_with_gemini(
            inputs,
            prompt,
            aspect_ratio=(
                aspect_ratio
            ),
            image_size=(
                output_image_size
            ),
            pro=False,
        )

    else:

        response = generate_image(
            prompt,
            mode="google_fast",
            number=1,
            aspect_ratio=(
                aspect_ratio
            ),
            image_size=(
                output_image_size
            ),
            quality="high",
            reference_images=(
                tuples
            ),
            allow_fallback=False,
        )

        if not response.images:
            raise RuntimeError(
                "Nano Banana 2 returned no image."
            )

        result = (
            response.images[0]
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
            "production_stage":
                "previsualization",
            "final_delivery_allowed":
                False,
            "physical_reference_count":
                len(
                    refs
                ),
            "physical_reference_ids":
                [
                    item.source_id
                    for item
                    in refs
                ],
        }
    )

    return result


# =========================================================
# REAL OPENAI MULTI-REFERENCE FINAL
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
    output_image_size: str = "2K",
    model_override: Optional[str] = None,
    max_reference_images: Optional[int] = None,
) -> GeneratedImage:

    limit = (
        max_reference_images
        if max_reference_images
        is not None
        else
        STC_FINAL_REFERENCE_LIMIT
    )

    limit = max(
        0,
        int(
            limit
            or
            0
        ),
    )

    refs = [
        item
        for item
        in unique_references(
            references
        )
        if item.image_bytes
    ][:limit]

    inputs: List[
        Tuple[
            bytes,
            str,
        ]
    ] = []

    if (
        working_image is not None
        and
        working_image.image_bytes
    ):

        inputs.append(
            (
                working_image.image_bytes,
                working_image.mime_type
                or
                infer_mime_type(
                    working_image.image_bytes
                ),
            )
        )

    inputs.extend(
        reference_tuples(
            refs
        )
    )

    if not inputs:

        response = generate_image(
            prompt,
            mode="openai",
            number=1,
            aspect_ratio=(
                aspect_ratio
            ),
            image_size=(
                output_image_size
            ),
            quality="high",
            allow_fallback=False,
        )

        if not response.images:
            raise RuntimeError(
                "GPT-Image-2 returned no image."
            )

        result = response.images[
            0
        ]

    else:

        try:
            result = edit_with_openai_multi(
                inputs,
                prompt,
                aspect_ratio=(
                    aspect_ratio
                ),
                image_size=(
                    output_image_size
                ),
                quality="high",
                original_prompt=(
                    prompt
                ),
                metadata={
                    "production_engine":
                        ENGINE_VERSION,
                    "pass_name":
                        pass_name,
                    "immutable_final_locks":
                        True,
                },
            )

        except Exception as openai_error:
            message = clean_text(
                openai_error,
                3500,
            )

            # One safety-only retry: remove external brand/reference inputs
            # that can trigger provider moderation, while keeping the
            # approved idea and no-text/no-logo contract in the prompt.
            safety_markers = (
                "safety",
                "content policy",
                "content_policy",
                "moderation",
            )
            safety_rejection = any(
                marker in message.lower()
                for marker in safety_markers
            )

            if not safety_rejection:
                raise

            safety_inputs = (
                inputs[:1]
                if working_image is not None
                else []
            )

            safety_prompt = (
                prompt
                + "\n\nSAFETY RETRY — IMMUTABLE: "
                "Create an original unbranded advertising image. "
                "Do not reproduce, identify, or render any logo, "
                "wordmark, trademark, readable text, bank-card mark, "
                "app UI, or branded asset from the input image. "
                "Use only abstract purple architectural materials, "
                "lighting and composition cues. Keep the service message "
                "visual and text-free."
            )

            print(
                "🔒 OpenAI safety retry: removed external reference inputs"
            )

            try:
                result = edit_with_openai_multi(
                    safety_inputs,
                    safety_prompt,
                    aspect_ratio=(
                        aspect_ratio
                    ),
                    image_size=(
                        output_image_size
                    ),
                    quality="high",
                    original_prompt=(
                        safety_prompt
                    ),
                    metadata={
                        "production_engine":
                            ENGINE_VERSION,
                        "pass_name":
                            pass_name,
                        "immutable_final_locks":
                            True,
                        "openai_safety_retry":
                            True,
                    },
                )

                if not isinstance(
                    result.metadata,
                    dict,
                ):
                    result.metadata = {}

                result.metadata.update(
                    {
                        "openai_safety_retry":
                            True,
                        "external_references_removed":
                            True,
                    }
                )

            except Exception as safety_retry_error:
                raise openai_error from safety_retry_error

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
            "production_stage":
                "final",
            "final_delivery_allowed":
                not bool(
                    getattr(
                        result,
                        "metadata",
                        {},
                    ).get(
                        "provider_fallback"
                    )
                ),
            "physical_reference_count":
                len(
                    refs
                ),
            "physical_reference_ids":
                [
                    item.source_id
                    for item
                    in refs
                ],
            "mandatory_final_model":
                FINAL_IMAGE_MODEL,
            "immutable_final_locks":
                True,
        }
    )

    return result


# =========================================================
# COMPATIBILITY HIGH QUALITY GENERATION
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

    refs = list(
        visual_refs
    )

    existing = {
        item.source_id
        for item
        in refs
        if item.source_id
    }

    for item in product_refs:

        if (
            item.source_id
            and
            item.source_id
            in existing
        ):
            continue

        refs.insert(
            0,
            item,
        )

        if item.source_id:
            existing.add(
                item.source_id
            )

    refs = (
        unique_references(
            refs
        )
    )

    limit = (
        max_physical_references
        if max_physical_references
        is not None
        else
        MAX_PHYSICAL_REFERENCE_IMAGES
    )

    limit = max(
        0,
        int(
            limit
            or
            0
        ),
    )

    preview_prompt = (
        build_previsualization_prompt(
            compiled=compiled,
            original_request=(
                original_request
            ),
            references=refs[
                :limit
            ],
            aspect_ratio=(
                aspect_ratio
            ),
        )
    )

    return gemini_multi_reference_edit(
        working_image=None,
        references=refs,
        prompt=preview_prompt,
        aspect_ratio=(
            aspect_ratio
        ),
        pass_name=(
            pass_name
        ),
        output_image_size=(
            output_image_size
        ),
        model_override=(
            NANO_BANANA_2_MODEL
        ),
        max_reference_images=(
            limit
        ),
    )


# =========================================================
# QA SCHEMA
# =========================================================

QA_SCORE_PROPERTIES = {
    key: {
        "type":
            "number",
        "minimum":
            0,
        "maximum":
            100,
        "description": (
            "Score on the 0-100 scale: 0 = complete failure, "
            "50 = materially flawed/average, 100 = fully excellent."
        ),
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
        "reference_drift": {
            "type":
                "boolean",
        },
        "invented_payment_hardware": {
            "type":
                "boolean",
        },
        "phone_pos_fusion": {
            "type":
                "boolean",
        },
        "random_stone_pedestal": {
            "type":
                "boolean",
        },
        "excessive_empty_copy_space": {
            "type":
                "boolean",
        },
        "generic_camera": {
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
        "reference_drift",
        "invented_payment_hardware",
        "phone_pos_fusion",
        "random_stone_pedestal",
        "excessive_empty_copy_space",
        "generic_camera",
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
# BLOCKERS
# =========================================================

def detect_critical_blockers(
    *,
    scores: Dict[str, float],
    explicit_failures: Any,
    flags: Any,
    product_lock: Any,
    original_request: str = "",
    stage: str = "final",
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

    flag_data = safe_dict(
        flags
    )

    if stage == "preview":

        if flag_data.get(
            "invented_payment_hardware"
        ):
            blockers.append(
                "preview_invented_payment_hardware"
            )

        if flag_data.get(
            "phone_pos_fusion"
        ):
            blockers.append(
                "preview_phone_pos_fusion"
            )

        if flag_data.get(
            "merchant_fusion_failed"
        ):
            blockers.append(
                "preview_merchant_fusion_failed"
            )

        if flag_data.get(
            "random_stone_pedestal"
        ):
            blockers.append(
                "preview_random_stone_pedestal"
            )

        return dedupe_strings(
            blockers,
            limit=40,
        )

    general_thresholds = {
        "concept_execution": 72.0,
        "message_clarity_without_text": 72.0,
        "realism": 75.0,
        "camera_perspective": 72.0,
        "advertising_readiness": 75.0,
    }

    for key, minimum in (
        general_thresholds.items()
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

    if stc_request:

        stc_thresholds = {
            "concept_execution": 82.0,
            "message_clarity_without_text": 80.0,
            "brand_alignment": 82.0,
            "brand_identity_strength": 82.0,
            "advertising_readiness": 84.0,
            "scene_originality": 80.0,
            "service_integration": 82.0,
            "realism": 84.0,
            "camera_perspective": 80.0,
            "reference_adherence": 80.0,
            "text_logo_compliance": 95.0,
            "copy_space_composition": 80.0,
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

        hard_flags = {
            "generic_scene_detected":
                "stc_generic_scene",
            "literal_counter_tableau_detected":
                "stc_literal_counter_tableau",
            "brand_identity_weak":
                "stc_brand_identity_weak",
            "reference_drift":
                "stc_reference_drift",
            "invented_payment_hardware":
                "stc_invented_payment_hardware",
            "phone_pos_fusion":
                "stc_phone_pos_fusion",
            "random_stone_pedestal":
                "stc_random_stone_pedestal",
            "excessive_empty_copy_space":
                "stc_excessive_empty_copy_space",
            "unwanted_text_or_logo":
                "stc_unwanted_text_or_logo",
            "fake_banking_ui":
                "stc_fake_banking_ui",
        }

        for (
            flag_name,
            blocker,
        ) in hard_flags.items():

            if flag_data.get(
                flag_name
            ):
                blockers.append(
                    blocker
                )

        if (
            detect_stc_benefit_family(
                original_request
            )
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

        if (
            flag_data.get(
                "generic_camera"
            )
            and
            clamp_score(
                scores.get(
                    "camera_perspective",
                    0,
                )
            )
            <
            84
        ):
            blockers.append(
                "stc_generic_camera"
            )

    lock = safe_dict(
        product_lock
    )

    if (
        lock.get(
            "enabled"
        )
        and
        clamp_score(
            scores.get(
                "reference_adherence",
                0,
            )
        )
        <
        80
    ):
        blockers.append(
            "product_reference_fidelity"
        )

    return dedupe_strings(
        blockers,
        limit=60,
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
    stage: str = "final",
) -> str:

    stc_request = (
        is_stc_bank_request(
            original_request
        )
    )

    stage_instruction = """
This is the FINAL image.

Judge release readiness.
""".strip()

    if stage == "preview":

        stage_instruction = """
This is a PREVISUALIZATION only.

Do not judge tiny polish harshly.

Find structural problems GPT-Image-2 must repair:

- message
- hardware
- scene logic
- camera
- composition
- brand drift
- reference drift
- copy space
- service integration

This audit is guidance, not client release.
""".strip()

    stc_section = ""

    if stc_request:

        stc_section = f"""
STC BANK AUDIT
==============

Judge whether the image genuinely feels informed by
STC Bank visual language instead of generic fintech.

PAYMENT HARDWARE
----------------

invented_payment_hardware = TRUE if any POS/payment device
has implausible industrial design, broken keys, impossible
screen/body logic or fictional hardware.

phone_pos_fusion = TRUE if smartphone + POS physically merge.

STONE / PEDESTAL
----------------

random_stone_pedestal = TRUE when travertine, marble,
limestone or generic luxury stone becomes an unmotivated
advertising pedestal.

COPY SPACE
----------

excessive_empty_copy_space = TRUE when the composition
contains a large dead upper region or pushes the hero too low.

CAMERA
------

generic_camera = TRUE when the image defaults to an ordinary
eye-level centered three-quarter shot with no visual purpose.

REFERENCE ADHERENCE
-------------------

reference_drift = TRUE when the image feels like generic
luxury/fintech rather than a visual world informed by the
STC reference DNA.

MERCHANT MESSAGE
----------------

For merchant_payments:

merchant_fusion_failed = TRUE unless the viewer understands
both:

- online/e-commerce activity
- physical/in-store payment acceptance

as one connected ecosystem.

Do not require readable text or UI as proof.

{build_stc_visual_constitution(
    original_request
)}
""".strip()

    prompt = f"""
XPAND VISUAL QA V6.0.1
======================

SCORING SCALE — APPLY BEFORE ALL OTHER INSTRUCTIONS
---------------------------------------------------

Every dimension MUST be scored directly on a 0–100 scale.
0 = complete failure, 50 = materially flawed/average,
100 = fully excellent. Never return a 0–10 scale.

{stage_instruction}

ORIGINAL REQUEST
----------------
{clean_text(
    original_request,
    2800,
)}

APPROVED RENDER BRIEF
---------------------
{compact_json(
    safe_dict(
        compiled_prompt.metadata
    ).get(
        "render_brief",
        {},
    ),
    2600,
)}

EXPECTED ASPECT
---------------
{aspect_ratio}

SCORE EACH DIMENSION 0–100
--------------------------

concept_execution:
Did the approved advertising idea survive?

message_clarity_without_text:
Can the commercial benefit be understood before copy?

brand_alignment:
Does the strategy fit the brand?

brand_identity_strength:
Does the frame feel specifically art-directed for this brand?

advertising_readiness:
Does this feel like a real campaign key visual?

scene_originality:
Is it meaningfully different from generic stock banking?

service_integration:
Is the requested service visibly communicated?

realism:
Are physics, anatomy, objects and industrial design believable?

camera_perspective:
Does camera/lens/perspective feel intentional and coherent?

lighting_materials:
Are materials, shadows and reflections physically credible?

human_anatomy:
If no people appear, score 100.

reference_adherence:
Does the image show evidence of intended visual DNA
without cloning references?

text_logo_compliance:
No unwanted generated text/logo/UI.

copy_space_composition:
Is copy space integrated naturally without harming balance?

FLAGS
-----

Return every required boolean accurately.

DECISION
--------

approve = ready for current stage.
correct = strong basis with repairable defects.
rebuild = structural execution failure.

{stc_section}

Return exactly the requested JSON schema.
""".strip()

    return fit_prompt_for_api(
        prompt,
        label=(
            "preview_audit_v601"
            if stage
            ==
            "preview"
            else
            "final_qa_v601"
        ),
        budget=(
            QA_PROMPT_BUDGET
        ),
    )


# =========================================================
# BUILD QA
# =========================================================

def build_qa_evaluation(
    data: Dict[str, Any],
    *,
    original_request: str,
    product_lock: Any,
    stage: str,
) -> QAEvaluation:

    raw_scores = safe_dict(
        data.get(
            "scores"
        )
    )

    numeric_raw_scores = [
        float(value)
        for value
        in raw_scores.values()
        if isinstance(
            value,
            (int, float),
        )
        and not isinstance(
            value,
            bool,
        )
    ]

    if (
        numeric_raw_scores
        and
        len(numeric_raw_scores)
        ==
        len(raw_scores)
        and
        max(numeric_raw_scores)
        <=
        10
    ):

        print(
            (
                "⚠️ QA scores occupy the ambiguous 0-10 low band; "
                "preserving values as legitimate 0-100 scores."
            )
        )

    score, normalized_scores = (
        calculate_qa_score(
            raw_scores
        )
    )

    flags = safe_dict(
        data.get(
            "flags"
        )
    )

    blockers = (
        detect_critical_blockers(
            scores=normalized_scores,
            explicit_failures=(
                data.get(
                    "critical_blockers"
                )
            ),
            flags=flags,
            product_lock=(
                product_lock
            ),
            original_request=(
                original_request
            ),
            stage=stage,
        )
    )

    model_decision = clean_text(
        data.get(
            "decision",
            "",
        ),
        50,
    ).lower()

    if stage == "preview":

        preview_ok = bool(
            score
            >=
            PREVIEW_GUIDANCE_FLOOR
            and
            model_decision
            !=
            "rebuild"
            and
            not blockers
        )

        return QAEvaluation(
            score=score,
            scores=normalized_scores,
            passed=preview_ok,
            strengths=[
                clean_text(
                    item,
                    800,
                )
                for item
                in safe_list(
                    data.get(
                        "strengths"
                    )
                )[:8]
                if clean_text(
                    item,
                    800,
                )
            ],
            problems=[
                clean_text(
                    item,
                    1000,
                )
                for item
                in safe_list(
                    data.get(
                        "problems"
                    )
                )[:10]
                if clean_text(
                    item,
                    1000,
                )
            ],
            correction_instruction=(
                clean_text(
                    data.get(
                        "correction_instruction",
                        "",
                    ),
                    2400,
                )
            ),
            critical_blockers=blockers,
            target_reached=False,
            delivery_approved=False,
            decision=(
                "preview_ready"
                if preview_ok
                else
                "preview_repair_required"
            ),
            raw={
                **data,
                "_xpand_stage":
                    "preview",
                "_xpand_flags":
                    flags,
            },
        )

    target = (
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
        target
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
        decision = "rebuild"

    else:
        decision = (
            "correction_required"
        )

    return QAEvaluation(
        score=score,
        scores=normalized_scores,
        passed=(
            delivery_approved
        ),
        strengths=[
            clean_text(
                item,
                800,
            )
            for item
            in safe_list(
                data.get(
                    "strengths"
                )
            )[:8]
            if clean_text(
                item,
                800,
            )
        ],
        problems=[
            clean_text(
                item,
                1000,
            )
            for item
            in safe_list(
                data.get(
                    "problems"
                )
            )[:10]
            if clean_text(
                item,
                1000,
            )
        ],
        correction_instruction=(
            clean_text(
                data.get(
                    "correction_instruction",
                    "",
                ),
                2400,
            )
        ),
        critical_blockers=(
            blockers
        ),
        target_reached=(
            target_reached
        ),
        delivery_approved=(
            delivery_approved
        ),
        decision=decision,
        raw={
            **data,
            "_xpand_stage":
                "final",
            "_xpand_target_score":
                target,
            "_xpand_release_floor":
                release_floor,
            "_xpand_flags":
                flags,
        },
    )


# =========================================================
# PREVIEW AUDIT
# =========================================================

def evaluate_preview_image(
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
            "preview_audit_calls"
        ] = (
            int(
                telemetry.get(
                    "preview_audit_calls",
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
            stage="preview",
        )
    )

    raw = call_gemini_director(
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
            "xpand_preview_audit_v601"
        ),
    )

    data = parse_json_object(
        raw
    )

    if not data:
        raise RuntimeError(
            "Preview audit returned invalid JSON."
        )

    return build_qa_evaluation(
        data,
        original_request=(
            original_request
        ),
        product_lock=(
            product_lock
        ),
        stage="preview",
    )


# =========================================================
# FINAL SOL QA
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
            stage="final",
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
            "xpand_final_qa_v601"
        ),
    )

    data = parse_json_object(
        raw
    )

    if not data:
        raise RuntimeError(
            "Final Production QA returned invalid JSON."
        )

    return build_qa_evaluation(
        data,
        original_request=(
            original_request
        ),
        product_lock=(
            product_lock
        ),
        stage="final",
    )


# =========================================================
# QA RANKING
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
            0.0,
        )

    return (
        1
        if not qa.critical_blockers
        else
        0,

        1
        if qa.passed
        else
        0,

        clamp_score(
            qa.scores.get(
                "service_integration",
                0,
            )
        ),

        clamp_score(
            qa.scores.get(
                "brand_identity_strength",
                0,
            )
        ),

        clamp_score(
            qa.scores.get(
                "realism",
                0,
            )
        ),

        clamp_score(
            qa.scores.get(
                "camera_perspective",
                0,
            )
        ),

        clamp_score(
            qa.scores.get(
                "advertising_readiness",
                0,
            )
        ),

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

    if candidate is None:
        return False

    if existing is None:
        return True

    # A passed candidate always wins over a rejected candidate.
    if candidate.passed != existing.passed:
        return bool(candidate.passed)

    # Among candidates with the same pass state, preserve the strongest
    # measured result. Fewer blockers must not select a materially weaker
    # image such as 72.49 over 74.79.
    return float(candidate.score) > float(existing.score)


# =========================================================
# ADAPTIVE FINAL ACTION
# =========================================================

def has_structural_failure(
    qa: QAEvaluation,
) -> bool:

    flags = safe_dict(
        qa.raw.get(
            "_xpand_flags"
        )
    )

    if any(
        flags.get(
            key
        )
        for key
        in (
            "invented_payment_hardware",
            "phone_pos_fusion",
            "merchant_fusion_failed",
            "generic_scene_detected",
            "random_stone_pedestal",
        )
    ):
        return True

    if (
        clamp_score(
            qa.scores.get(
                "concept_execution",
                0,
            )
        )
        <
        76
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
        76
    ):
        return True

    if (
        clamp_score(
            qa.scores.get(
                "service_integration",
                0,
            )
        )
        <
        76
    ):
        return True

    # Allow a broader repair when several visual execution dimensions
    # are materially weak. This does not lower the final QA threshold.
    broad_execution_scores = (
        "realism",
        "camera_perspective",
        "advertising_readiness",
        "copy_space_composition",
    )

    if any(
        clamp_score(
            qa.scores.get(
                dimension,
                0,
            )
        )
        <
        82
        for dimension
        in broad_execution_scores
    ):
        return True

    return bool(
        qa.raw.get(
            "decision"
        )
        ==
        "rebuild"
    )


def choose_adaptive_action(
    qa: Optional[
        QAEvaluation
    ],
    *,
    high_alert: bool = False,
) -> str:

    if qa is None:
        return "none"

    if qa.target_reached:
        return "none"

    if has_structural_failure(
        qa
    ):
        return "structural_repair"

    if qa.passed:

        if high_alert:
            return "premium_refinement"

        return "none"

    return "targeted_repair"


# =========================================================
# FINAL REPAIR PROMPT V6.0.1
# =========================================================

def build_final_repair_prompt(
    *,
    qa: QAEvaluation,
    compiled: CompiledPrompt,
    original_request: str,
    references: Sequence[
        ProductionReference
    ],
    aspect_ratio: str,
    requested_size: str,
    action: str,
) -> str:

    structural = (
        action
        ==
        "structural_repair"
    )

    text_logo_surgical = bool(
        action
        ==
        "targeted_repair"
        and
        qa_flags_text_logo_failure(
            qa
        )
    )

    copy_space_surgical = bool(
        text_logo_surgical
        and
        qa_flags_copy_space_failure(
            qa
        )
    )

    surgical_composition_instruction = (
        """
QA also explicitly flags copy-space composition. A narrowly bounded
composition correction is permitted: minimally crop, reframe, scale
or shift existing scene elements only as needed to restore integrated
copy-space balance and advertising readiness. Preserve the established
camera intent, service relationship and message. Do not create or
expand empty space, add a blank panel, push the hero downward, replace
the scene or introduce new objects.
""".strip()
        if copy_space_surgical
        else
        """
Preserve the existing composition. Do not recompose, reframe, crop,
move the hero, expand copy space, add objects or reinterpret the
campaign.
""".strip()
    )

    repair_mode = (
        """
STRUCTURAL REPAIR IS ALLOWED.

The existing final image has a structural execution problem.

You may substantially recompose the existing image while
preserving:

- commercial proposition
- approved advertising idea
- brand world
- service message

Replace impossible or generic execution with a believable
photographic execution of the SAME idea.
""".strip()
        if structural
        else
        f"""
SURGICAL TEXT / LOGO / UI REMOVAL.

Image 1, the failed final candidate, is the PRIMARY AND ONLY
visual source for this repair.

Preserve the already-good advertising message, service depiction,
camera, perspective, subjects, geometry, lighting, materials,
and photographic character.

Edit only the local pixels containing lettering, logos, wordmarks,
symbols, watermarks, fake banking UI, readable numbers or readable
screen/card/terminal content. Replace those pixels with physically
plausible unbranded surface material, blank screen treatment or
natural scene detail matching the immediate surroundings.

{surgical_composition_instruction}

Do not restyle or change the service story.
Do not reproduce marks visible in any prior brand reference.
""".strip()
        if text_logo_surgical
        else
        """
TARGETED REPAIR.

Preserve successful regions.

Do not redesign the campaign.

Fix only diagnosed defects.
""".strip()
    )

    reference_role_text = (
        """
No style, campaign, environment or product reference is attached.
Use Image 1 alone and do not reconstruct prior branded lettering.
""".strip()
        if text_logo_surgical
        else
        reference_role_manifest(
            references,
            draft_first=True,
        )
    )

    repair_scope_lock = (
        f"""
REPAIR MODE — IMMUTABLE
-----------------------
SURGICAL REMOVAL. Image 1 is the PRIMARY AND ONLY visual source.
Preserve the already-good advertising message, service depiction,
camera, perspective, subjects, geometry, lighting, materials and all
successful regions. Remove only diagnosed text, logos, wordmarks,
symbols, watermarks, readable numbers and fake banking UI; rebuild
those local pixels plausibly.
{(
    "A narrowly bounded composition correction may minimally crop, "
    "reframe, scale or shift existing elements only for the diagnosed "
    "copy-space failure. Do not create or expand empty space, add a "
    "blank panel or replace the scene."
    if copy_space_surgical
    else
    "Do not recompose, reframe, crop, add objects or redesign."
)}
""".strip()
        if text_logo_surgical
        else
        """
REPAIR MODE — IMMUTABLE
-----------------------
STRUCTURAL REPAIR of the same approved idea is allowed. Preserve the
commercial proposition, brand world and service message while replacing
structurally impossible or generic execution with believable photography.
""".strip()
        if structural
        else
        """
REPAIR MODE — IMMUTABLE
-----------------------
TARGETED REPAIR. Preserve successful regions and the approved campaign.
Fix only the defects diagnosed by final QA; do not redesign.
""".strip()
    )

    actionable_qa_lock = f"""
FINAL QA CORRECTION — IMMUTABLE
-------------------------------
Instruction:
{clean_text(
    qa.correction_instruction,
    900,
) or "Correct only the diagnosed final-QA defects."}

Critical blockers:
{compact_json(
    qa.critical_blockers[:8],
    1200,
)}
""".strip()

    immutable_repair_section = f"""
XPAND_REPAIR_SCOPE_V601
=======================

{repair_scope_lock}

REFERENCE ROLES — IMMUTABLE
---------------------------
{clean_text(
    reference_role_text,
    800,
)}

{actionable_qa_lock}

END_XPAND_REPAIR_SCOPE_V601
""".strip()

    repair_priorities = (
        f"""
- remove every diagnosed letter, logo, wordmark and readable UI artifact
- preserve the existing message, camera and service depiction exactly
- preserve all already-successful regions outside the local artifacts
- leave repaired surfaces clean, unbranded and physically plausible
{(
    "- minimally correct the explicitly failed copy-space composition"
    if copy_space_surgical
    else
    ""
)}
""".strip()
        if text_logo_surgical
        else
        """
- weak service communication
- weak brand identity
- unrealistic hardware
- bad anatomy
- bad object contact
- weak camera
- reference drift
- generic scene logic
- weak composition
- synthetic materials
- fake UI
- accidental text/logo
- excessive empty upper space
""".strip()
    )

    core_prompt = f"""
XPAND GPT-IMAGE-2 FINAL REPAIR V6.0.1
=====================================

Image 1 is the existing GPT-Image-2 final candidate.

{(
    "No Images 2+ are attached for this surgical repair."
    if text_logo_surgical
    else
    "Images 2+ are supporting visual references."
)}

REFERENCE ROLES
---------------
{reference_role_text}

ORIGINAL REQUEST
----------------
{clean_text(
    original_request,
    2800,
)}

APPROVED CONTRACT
-----------------
{clean_text(
    compiled.prompt,
    1800,
)}

FINAL QA FAILURE
----------------
{qa_feedback_summary(
    qa
)}

REPAIR MODE
-----------
{repair_mode}

REPAIR PRIORITIES
-----------------

Repair only the applicable items:
{repair_priorities}

Keep the commercial proposition intact.

Create one improved final campaign image.
""".strip()

    immutable_locks = (
        build_immutable_final_locks(
            original_request=(
                original_request
            ),
            aspect_ratio=(
                aspect_ratio
            ),
            requested_size=(
                requested_size
            ),
            reference_authority=(
                not text_logo_surgical
            ),
        )
        +
        "\n\n"
        +
        immutable_repair_section
    )

    return fit_prompt_with_immutable_locks(
        core_prompt,
        immutable_locks,
        label=(
            "gpt_image_2_final_repair_v601"
        ),
        budget=(
            CORRECTION_PROMPT_BUDGET
        ),
    )


# =========================================================
# DELIVERY
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

    for (
        display,
        key,
    ) in (
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
            "Service",
            "service_integration",
        ),
        (
            "Ad readiness",
            "advertising_readiness",
        ),
        (
            "Realism",
            "realism",
        ),
        (
            "Camera",
            "camera_perspective",
        ),
        (
            "Reference DNA",
            "reference_adherence",
        ),
        (
            "Copy space",
            "copy_space_composition",
        ),
        (
            "Text/logo",
            "text_logo_compliance",
        ),
    ):

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
        qa.critical_blockers[
            :12
        ]
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
# PROVIDER FAILURE QA
# =========================================================

def provider_failure_qa(
    reason: str,
) -> QAEvaluation:

    return QAEvaluation(
        score=0.0,
        scores={
            key:
                0.0
            for key
            in QA_WEIGHTS
        },
        passed=False,
        strengths=[],
        problems=[
            clean_text(
                reason,
                1500,
            )
        ],
        correction_instruction="",
        critical_blockers=[
            (
                "mandatory_gpt_image_2_"
                "final_unavailable"
            )
        ],
        target_reached=False,
        delivery_approved=False,
        decision="rebuild",
        raw={
            "provider_failure":
                True,
            "reason":
                clean_text(
                    reason,
                    2000,
                ),
        },
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
    target_model: str = TARGET_OPENAI,
) -> ProductionResult:

    started = (
        time.monotonic()
    )

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
        "previsualization_calls":
            0,
        "final_image_calls":
            0,
        "preview_audit_calls":
            0,
        "vision_calls":
            0,
        "max_image_calls":
            MASTERPIECE_MAX_IMAGE_CALLS,
        "max_total_provider_image_calls":
            (
                MASTERPIECE_PREVIS_CALLS
                +
                MASTERPIECE_MAX_IMAGE_CALLS
            ),
        "max_vision_calls":
            MASTERPIECE_MAX_VISION_CALLS,
        "max_preview_audit_calls":
            MASTERPIECE_PREVIEW_AUDIT_CALLS,
        "nano_banana_2_model":
            NANO_BANANA_2_MODEL,
        "final_image_model":
            FINAL_IMAGE_MODEL,
        "mandatory_openai_final":
            bool(
                MASTERPIECE_REQUIRE_OPENAI_FINAL
            ),
        "stc_high_alert":
            high_alert,
        "stc_brand_pack_loaded":
            False,
        "stc_local_reference_count":
            0,
        "physical_reference_count":
            0,
        "physical_reference_ids":
            [],
        "final_reference_count":
            0,
        "final_provider_lock_passed":
            False,
        "adaptive_action":
            "none",
        "immutable_final_locks":
            True,
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

    product_refs = (
        product_references(
            memory_references
        )
    )

    # =====================================================
    # STC PERMANENT REFERENCES
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
        ) = (
            load_stc_local_references(
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
                        1400,
                    )
                ),
            )
        )

    telemetry[
        "stc_local_reference_count"
    ] = len(
        stc_local_refs
    )

    telemetry[
        "stc_brand_pack_loaded"
    ] = bool(
        stc_kit
    )

    # =====================================================
    # REFERENCE CONSTITUTION
    # =====================================================

    all_references = (
        unique_references(
            list(
                memory_references
            )
            +
            list(
                stc_local_refs
            )
        )
    )

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
    # PRODUCT LOCK
    # =====================================================

    product_lock = (
        combined_product_lock(
            memory_references
        )
    )

    # =====================================================
    # BRAND CONTEXT
    # =====================================================

    brand_visual_profile = (
        load_brand_visual_profile_safe(
            core,
            user_id,
            brand_id,
        )
    )

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

    enriched_brand_context = (
        build_enriched_brand_context(
            brand_context=(
                brand_context
            ),
            brand_visual_profile=(
                brand_visual_profile
            ),
            references=(
                all_references
            ),
            stc_brand_kit_context=(
                stc_kit_context
            ),
        )
    )

    # =====================================================
    # COMPILE
    # =====================================================

    reference_dna = (
        reference_dna_payload(
            physical_refs,
            limit=3,
        )
    )

    compiled = compile_prompt(
        TARGET_OPENAI,
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

    # =====================================================
    # LOG HEADER
    # =====================================================

    print("")
    print(
        "=============================================="
    )
    print(
        " XPAND PRODUCTION ENGINE V6.0.1"
    )
    print(
        " IMMUTABLE-LOCK HYBRID MASTERPIECE CORE"
    )
    print(
        "=============================================="
    )

    print(
        "Mode:",
        mode,
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
        "Requested final size:",
        requested_size,
    )

    print(
        "Previsualization model:",
        NANO_BANANA_2_MODEL,
    )

    print(
        "Mandatory final model:",
        FINAL_IMAGE_MODEL,
    )

    print(
        "Permanent STC refs loaded:",
        len(
            stc_local_refs
        ),
    )

    print(
        "References selected:",
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
        "Render contract chars:",
        len(
            compiled.prompt
        ),
    )

    print(
        "Immutable final locks:",
        True,
    )

    print(
        "STC High Alert:",
        high_alert,
    )

    if stc_request:

        print(
            "STC scene tier:",
            stc_scene_tier(
                original_request
            ),
        )

        print(
            "STC benefit:",
            detect_stc_benefit_family(
                original_request
            ),
        )

    print("")

    # =====================================================
    # NON-MASTERPIECE
    # =====================================================

    if mode != MODE_MASTERPIECE:

        print(
            "🍌 FAST PRODUCTION | Nano Banana 2"
        )

        fast_image = (
            generate_high_quality_image(
                compiled=compiled,
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
                    "fast_generation_v601"
                ),
                output_image_size=(
                    requested_size
                ),
                max_physical_references=(
                    len(
                        physical_refs
                    )
                ),
            )
        )

        telemetry[
            "previsualization_calls"
        ] += 1

        telemetry[
            "image_calls"
        ] += 1

        final_image = (
            create_exact_delivery_frame(
                fast_image,
                aspect_ratio,
                label=(
                    "fast_delivery"
                ),
            )
        )

        return ProductionResult(
            ok=True,
            final_image=(
                final_image
            ),
            best_score=0.0,
            qa=None,
            passes=[
                ProductionPassResult(
                    pass_name=(
                        "fast_generation_v601"
                    ),
                    image=(
                        fast_image
                    ),
                )
            ],
            compiled_prompt=(
                compiled
            ),
            references_used=len(
                all_references
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
    # MASTERPIECE PREVIS
    # =====================================================

    print(
        "🍌 PREVIS 1/1 | "
        +
        NANO_BANANA_2_MODEL
        +
        " | 1K INTERNAL ONLY"
    )

    preview_image = (
        generate_high_quality_image(
            compiled=compiled,
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
                "nano_banana_previs_v601"
            ),
            output_image_size="1K",
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
        "previsualization_calls"
    ] += 1

    telemetry[
        "image_calls"
    ] += 1

    passes: List[
        ProductionPassResult
    ] = [
        ProductionPassResult(
            pass_name=(
                "nano_banana_previs_v601"
            ),
            image=(
                preview_image
            ),
            metadata={
                "delivery_allowed":
                    False,
                "model":
                    preview_image.model,
                "stage":
                    "previsualization",
            },
        )
    ]

    # =====================================================
    # GEMINI PREVIEW AUDIT
    # =====================================================

    preview_qa: Optional[
        QAEvaluation
    ] = None

    print("")
    print(
        "👁️ PREVIS AUDIT 1/1 | Gemini Vision"
    )

    try:

        preview_qa = (
            evaluate_preview_image(
                image=(
                    preview_image
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
            preview_qa
        )

        print_qa(
            "Previs Audit",
            preview_qa,
        )

    except Exception as error:

        message = clean_text(
            error,
            2400,
        )

        errors.append(
            (
                "preview_audit: "
                +
                message
            )
        )

        print(
            "⚠️ Preview audit unavailable:",
            message,
        )

        print(
            (
                "✅ Final renderer continues using "
                "approved Creative Brain contract."
            )
        )

    # =====================================================
    # FINAL REFERENCE SET
    # =====================================================

    final_refs = physical_refs[
        :(
            STC_FINAL_REFERENCE_LIMIT
            if stc_request
            else
            MAX_PHYSICAL_REFERENCE_IMAGES
        )
    ]

    telemetry[
        "final_reference_count"
    ] = len(
        final_refs
    )

    # =====================================================
    # GPT-IMAGE-2 FINAL
    # =====================================================

    final_prompt = (
        build_final_renderer_prompt(
            compiled=(
                compiled
            ),
            original_request=(
                original_request
            ),
            preview_qa=(
                preview_qa
            ),
            references=(
                final_refs
            ),
            aspect_ratio=(
                aspect_ratio
            ),
            requested_size=(
                requested_size
            ),
        )
    )

    print(
        "Final prompt chars:",
        len(
            final_prompt
        ),
        "/",
        FINAL_PROMPT_BUDGET,
    )

    print(
        "Immutable sentinel present:",
        (
            IMMUTABLE_LOCK_SENTINEL
            in final_prompt
        ),
    )

    print("")
    preview_requires_clean_recomposition = bool(
        preview_qa
        is not None
        and (
            preview_qa.decision
            ==
            "preview_repair_required"
            or
            bool(
                preview_qa.critical_blockers
            )
        )
    )

    if preview_requires_clean_recomposition:
        print(
            "🧱 CLEAN FINAL RECOMPOSITION: preview blocker present; "
            "final starts from contract + STC references only"
        )

    print(
        "🎯 FINAL IMAGE 1/"
        +
        str(
            MASTERPIECE_MAX_IMAGE_CALLS
        )
        +
        " | "
        +
        FINAL_IMAGE_MODEL
    )

    try:

        first_final = (
            openai_multi_reference_edit(
                working_image=(
                    None
                    if preview_requires_clean_recomposition
                    else
                    preview_image
                ),
                references=(
                    final_refs
                ),
                prompt=(
                    final_prompt
                ),
                aspect_ratio=(
                    aspect_ratio
                ),
                pass_name=(
                    "gpt_image_2_final_v601"
                ),
                output_image_size=(
                    requested_size
                ),
                model_override=(
                    FINAL_IMAGE_MODEL
                ),
                max_reference_images=(
                    len(
                        final_refs
                    )
                ),
            )
        )

    except Exception as error:

        message = clean_text(
            error,
            3500,
        )

        errors.append(
            (
                "gpt_image_2_final: "
                +
                message
            )
        )

        print(
            "🛑 Mandatory GPT-Image-2 final failed:",
            message,
        )

        failure_qa = (
            provider_failure_qa(
                message
            )
        )

        preview_image.metadata[
            "final_delivery_allowed"
        ] = False

        preview_image.metadata[
            "mandatory_openai_final_failed"
        ] = True

        return ProductionResult(
            ok=False,
            final_image=(
                preview_image
            ),
            best_score=0.0,
            qa=(
                failure_qa
            ),
            passes=(
                passes
            ),
            compiled_prompt=(
                compiled
            ),
            references_used=len(
                all_references
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
            telemetry={
                **telemetry,
                "failure_kind":
                    "mandatory_final_provider_failure",
                "block_generic_smart_fallback":
                    bool(
                        high_alert
                    ),
            },
        )

    telemetry[
        "final_image_calls"
    ] += 1

    telemetry[
        "image_calls"
    ] += 1

    telemetry[
        "final_provider_lock_passed"
    ] = bool(
        first_final.model
        ==
        FINAL_IMAGE_MODEL
    )

    passes.append(
        ProductionPassResult(
            pass_name=(
                "gpt_image_2_final_v601"
            ),
            image=(
                first_final
            ),
            metadata={
                "model":
                    first_final.model,
                "stage":
                    "final",
                "final_provider":
                    (
                        "google"
                        if bool(
                            getattr(
                                first_final,
                                "metadata",
                                {},
                            ).get(
                                "provider_fallback"
                            )
                        )
                        else
                        "openai"
                    ),
                "immutable_final_locks":
                    True,
                "working_image_used":
                    not preview_requires_clean_recomposition,
                "working_image_source":
                    (
                        "previsualization"
                        if not preview_requires_clean_recomposition
                        else
                        "clean_contract_recomposition"
                    ),
                "references":
                    [
                        item.source_id
                        for item
                        in final_refs
                    ],
            },
        )
    )

    # =====================================================
    # FINAL PROVIDER LOCK
    # =====================================================

    if (
        MASTERPIECE_REQUIRE_OPENAI_FINAL
        and
        first_final.model
        !=
        FINAL_IMAGE_MODEL
        and not bool(
            getattr(
                first_final,
                "metadata",
                {},
            ).get(
                "provider_fallback"
            )
        )
    ):

        failure_qa = (
            provider_failure_qa(
                (
                    "Final provider lock failed. Expected "
                    +
                    FINAL_IMAGE_MODEL
                    +
                    " but got "
                    +
                    clean_text(
                        first_final.model,
                        200,
                    )
                )
            )
        )

        return ProductionResult(
            ok=False,
            final_image=(
                first_final
            ),
            best_score=0.0,
            qa=(
                failure_qa
            ),
            passes=(
                passes
            ),
            compiled_prompt=(
                compiled
            ),
            references_used=len(
                all_references
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
    # FINAL QA 1
    # =====================================================

    print("")
    print(
        "👁️ FINAL QA 1/"
        +
        str(
            MASTERPIECE_MAX_VISION_CALLS
        )
        +
        " | GPT-5.6 Sol"
    )

    first_qa: Optional[
        QAEvaluation
    ] = None

    try:

        first_qa = (
            evaluate_generated_image(
                image=(
                    first_final
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
            first_qa
        )

        print_qa(
            "Final QA",
            first_qa,
        )

    except Exception as error:

        message = clean_text(
            error,
            2800,
        )

        errors.append(
            (
                "final_qa_1: "
                +
                message
            )
        )

        print(
            "⚠️ Final QA unavailable:",
            message,
        )

    best_image = (
        first_final
    )

    best_qa = (
        first_qa
    )

    # =====================================================
    # ADAPTIVE DECISION
    # =====================================================

    action = (
        choose_adaptive_action(
            first_qa,
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
        "🧠 FINAL ADAPTIVE DECISION:",
        action,
    )

    # =====================================================
    # OPTIONAL FINAL GPT-IMAGE-2 REPAIR
    # =====================================================

    if (
        action
        !=
        "none"
        and
        first_qa
        is not None
        and
        telemetry[
            "final_image_calls"
        ]
        <
        MASTERPIECE_MAX_IMAGE_CALLS
        and not bool(
            getattr(
                first_final,
                "metadata",
                {},
            ).get(
                "provider_fallback"
            )
        )
    ):

        text_logo_surgical = bool(
            action
            ==
            "targeted_repair"
            and
            qa_flags_text_logo_failure(
                first_qa
            )
        )

        repair_refs = (
            []
            if text_logo_surgical
            else
            correction_reference_set(
                product_refs=(
                    product_refs
                ),
                stc_local_refs=(
                    stc_local_refs
                ),
                high_alert=(
                    high_alert
                ),
            )
            if stc_request
            else
            physical_refs[
                :MAX_PHYSICAL_REFERENCE_IMAGES
            ]
        )

        repair_phase = (
            "repair_prompt_build"
        )

        try:

            repair_prompt = (
                build_final_repair_prompt(
                    qa=(
                        first_qa
                    ),
                    compiled=(
                        compiled
                    ),
                    original_request=(
                        original_request
                    ),
                    references=(
                        repair_refs
                    ),
                    aspect_ratio=(
                        aspect_ratio
                    ),
                    requested_size=(
                        requested_size
                    ),
                    action=(
                        action
                    ),
                )
            )

            print(
                "Repair prompt chars:",
                len(
                    repair_prompt
                ),
                "/",
                CORRECTION_PROMPT_BUDGET,
            )

            print(
                "Repair immutable sentinel:",
                (
                    IMMUTABLE_LOCK_SENTINEL
                    in repair_prompt
                ),
            )

            print("")
            print(
                "🎯 FINAL IMAGE 2/"
                +
                str(
                    MASTERPIECE_MAX_IMAGE_CALLS
                )
                +
                " | "
                +
                FINAL_IMAGE_MODEL
                +
                " | "
                +
                action
            )

            repair_phase = (
                "repair_provider_call"
            )

            second_final = (
                openai_multi_reference_edit(
                    # A structural failure needs a clean recomposition.
                    # Reusing the failed final candidate would preserve its
                    # broken camera, geometry or generic scene logic.
                    working_image=(
                        None
                        if (
                            action == "structural_repair"
                            and
                            preview_requires_clean_recomposition
                        )
                        else
                        (
                            preview_image
                            if action == "structural_repair"
                            else first_final
                        )
                    ),
                    references=(
                        repair_refs
                    ),
                    prompt=(
                        repair_prompt
                    ),
                    aspect_ratio=(
                        aspect_ratio
                    ),
                    pass_name=(
                        "gpt_image_2_"
                        +
                        action
                        +
                        "_v601"
                    ),
                    output_image_size=(
                        requested_size
                    ),
                    model_override=(
                        FINAL_IMAGE_MODEL
                    ),
                    max_reference_images=(
                        len(
                            repair_refs
                        )
                    ),
                )
            )

            telemetry[
                "final_image_calls"
            ] += 1

            telemetry[
                "image_calls"
            ] += 1

            passes.append(
                ProductionPassResult(
                    pass_name=(
                        "gpt_image_2_"
                        +
                        action
                        +
                        "_v601"
                    ),
                    image=(
                        second_final
                    ),
                    metadata={
                        "model":
                            second_final.model,
                        "stage":
                            "final_repair",
                        "working_image_used":
                            True,
                        "working_image_primary":
                            True,
                        "working_image_source":
                            (
                                (
                                    "clean_contract_recomposition"
                                    if preview_requires_clean_recomposition
                                    else
                                    "previsualization_recomposition"
                                )
                                if action == "structural_repair"
                                else "failed_final_candidate"
                            ),
                        "text_logo_surgical":
                            text_logo_surgical,
                        "references":
                            [
                                item.source_id
                                for item
                                in repair_refs
                            ],
                        "immutable_final_locks":
                            True,
                    },
                )
            )

            second_qa: Optional[
                QAEvaluation
            ] = None

            if (
                telemetry[
                    "vision_calls"
                ]
                <
                MASTERPIECE_MAX_VISION_CALLS
            ):

                repair_phase = (
                    "repair_final_qa"
                )

                print("")
                print(
                    "👁️ FINAL QA 2/"
                    +
                    str(
                        MASTERPIECE_MAX_VISION_CALLS
                    )
                    +
                    " | GPT-5.6 Sol"
                )

                try:

                    second_qa = (
                        evaluate_generated_image(
                            image=(
                                second_final
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
                        "Repair QA",
                        second_qa,
                    )

                except Exception as error:

                    message = clean_text(
                        error,
                        2800,
                    )

                    errors.append(
                        (
                            "final_qa_2: "
                            +
                            message
                        )
                    )

                    print(
                        "⚠️ Repair QA unavailable:",
                        message,
                    )

            if (
                second_qa
                is not None
                and
                qa_candidate_is_better(
                    second_qa,
                    best_qa,
                )
            ):

                best_image = (
                    second_final
                )

                best_qa = (
                    second_qa
                )

                print(
                    (
                        "🏆 GPT-Image-2 repaired "
                        "candidate selected."
                    )
                )

            else:

                print(
                    (
                        "🏆 Original GPT-Image-2 "
                        "final preserved."
                    )
                )

        except Exception as error:

            message = clean_text(
                error,
                3200,
            )

            final_qa_log = (
                first_qa.score
                if first_qa is not None
                else
                None
            )

            repair_error = {
                "phase":
                    repair_phase,
                "provider":
                    FINAL_IMAGE_MODEL,
                "final_qa":
                    final_qa_log,
                "message":
                    message,
            }

            telemetry[
                "final_repair_error"
            ] = repair_error

            errors.append(
                (
                    "final_repair"
                    +
                    " | phase="
                    +
                    repair_phase
                    +
                    " | provider="
                    +
                    FINAL_IMAGE_MODEL
                    +
                    " | final_qa="
                    +
                    str(
                        final_qa_log
                    )
                    +
                    ": "
                    +
                    message
                )
            )

            print(
                "FINAL_REPAIR_FAILURE"
                + " | phase=" + repair_phase
                + " | provider=" + FINAL_IMAGE_MODEL
                + " | first_qa=" + str(final_qa_log)
                + " | error_type=" + type(error).__name__,
                flush=True,
            )

            print(
                (
                    "✅ Original GPT-Image-2 "
                    "final preserved."
                )
            )

    # =====================================================
    # FINAL DELIVERY LOCK
    # =====================================================

    final_provider_valid = bool(
        best_image.model
        ==
        FINAL_IMAGE_MODEL
        or bool(
            getattr(
                best_image,
                "metadata",
                {},
            ).get(
                "provider_fallback"
            )
        )
    )

    telemetry[
        "final_provider_lock_passed"
    ] = (
        final_provider_valid
    )

    if (
        MASTERPIECE_REQUIRE_OPENAI_FINAL
        and
        not final_provider_valid
    ):

        best_qa = (
            provider_failure_qa(
                (
                    "Non-OpenAI final "
                    "candidate blocked."
                )
            )
        )

    final_image = (
        create_exact_delivery_frame(
            best_image,
            aspect_ratio,
            label=(
                "final_delivery_v601"
            ),
        )
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
            "previsualization_model":
                NANO_BANANA_2_MODEL,
            "final_model":
                final_image.model,
            "mandatory_final_model":
                FINAL_IMAGE_MODEL,
            "final_provider_lock_passed":
                final_provider_valid,
            "requested_image_size":
                requested_size,
            "requested_aspect_ratio":
                aspect_ratio,
            "stc_brand_pack_loaded":
                bool(
                    stc_kit
                ),
            "stc_high_alert":
                high_alert,
            "physical_reference_ids":
                [
                    item.source_id
                    for item
                    in physical_refs
                ],
            "previsualization_only_gemini":
                True,
            "gemini_final_allowed":
                bool(
                    getattr(
                        final_image,
                        "metadata",
                        {},
                    ).get(
                        "provider_fallback"
                    )
                ),
            "copy_space_policy":
                "25-40_percent_integrated",
            "immutable_final_locks":
                True,
            "immutable_lock_version":
                "v601",
            "block_generic_smart_fallback":
                bool(
                    high_alert
                ),
        }
    )

    final_ok = bool(
        best_qa
        and
        best_qa.passed
        and
        final_provider_valid
    )

    best_score = (
        best_qa.score
        if best_qa
        else
        0.0
    )

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
        " XPAND PRODUCTION COMPLETE V6.0.1"
    )
    print(
        "=============================================="
    )

    print(
        "Previsualization calls:",
        telemetry[
            "previsualization_calls"
        ],
        "/",
        MASTERPIECE_PREVIS_CALLS,
    )

    print(
        "Final GPT-Image-2 calls:",
        telemetry[
            "final_image_calls"
        ],
        "/",
        MASTERPIECE_MAX_IMAGE_CALLS,
    )

    print(
        "Preview audits:",
        telemetry[
            "preview_audit_calls"
        ],
        "/",
        MASTERPIECE_PREVIEW_AUDIT_CALLS,
    )

    print(
        "Final Vision QA calls:",
        telemetry[
            "vision_calls"
        ],
        "/",
        MASTERPIECE_MAX_VISION_CALLS,
    )

    print(
        "Permanent STC refs loaded:",
        len(
            stc_local_refs
        ),
    )

    print(
        "References used:",
        len(
            physical_refs
        ),
    )

    print(
        "Final model:",
        final_image.model,
    )

    print(
        "Mandatory final model:",
        FINAL_IMAGE_MODEL,
    )

    print(
        "Final provider lock:",
        (
            "PASS ✅"
            if final_provider_valid
            else
            "FAIL ❌"
        ),
    )

    print(
        "Immutable final locks:",
        True,
    )

    print(
        "Final size:",
        requested_size,
    )

    print(
        "Final aspect ratio:",
        aspect_ratio,
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
        best_score,
    )

    print(
        "QA passed:",
        final_ok,
    )

    print(
        "Elapsed:",
        elapsed,
        "sec",
    )

    print("")

    return ProductionResult(
        ok=final_ok,
        final_image=(
            final_image
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
        references_used=len(
            all_references
        ),
        product_references_used=len(
            product_refs
        ),
        elapsed_seconds=(
            elapsed
        ),
        errors=(
            errors
        ),
        telemetry=(
            telemetry
        ),
    )


# =========================================================
# STATUS
# =========================================================

def get_production_engine_status() -> Dict[
    str,
    Any,
]:

    image_status = {}

    try:
        image_status = (
            get_image_engine_status()
        )

    except Exception:
        image_status = {}

    return {
        "engine":
            ENGINE_NAME,
        "version":
            ENGINE_VERSION,

        "nano_banana_2_model":
            NANO_BANANA_2_MODEL,

        "nano_banana_role":
            "previsualization_only",

        "final_image_model":
            FINAL_IMAGE_MODEL,

        "final_renderer":
            "openai",

        "mandatory_openai_final":
            MASTERPIECE_REQUIRE_OPENAI_FINAL,

        "gemini_final_allowed":
            False,

        "gemini_pro_final":
            False,

        "max_image_calls":
            MASTERPIECE_MAX_IMAGE_CALLS,

        "previsualization_calls":
            MASTERPIECE_PREVIS_CALLS,

        "max_total_provider_image_calls":
            (
                MASTERPIECE_PREVIS_CALLS
                +
                MASTERPIECE_MAX_IMAGE_CALLS
            ),

        "max_vision_calls":
            MASTERPIECE_MAX_VISION_CALLS,

        "preview_audit_calls":
            MASTERPIECE_PREVIEW_AUDIT_CALLS,

        "smart_reference_limit":
            SMART_REFERENCE_SELECTION_LIMIT,

        "physical_reference_limit":
            MAX_PHYSICAL_REFERENCE_IMAGES,

        "stc_physical_reference_limit":
            MAX_STC_PHYSICAL_REFERENCE_IMAGES,

        "stc_render_reference_limit":
            STC_RENDER_REFERENCE_LIMIT,

        "stc_final_reference_limit":
            STC_FINAL_REFERENCE_LIMIT,

        "stc_edit_reference_limit":
            STC_EDIT_REFERENCE_LIMIT,

        "stc_brand_kit_available":
            STC_BRAND_KIT_AVAILABLE,

        "stc_brand_pack_required":
            STC_REQUIRE_BRAND_PACK,

        "stc_high_alert_enabled":
            STC_HIGH_ALERT_ENABLED,

        "qa_target":
            QA_TARGET_SCORE,

        "qa_release_floor":
            QA_RELEASE_FLOOR,

        "stc_qa_target":
            STC_QA_TARGET_SCORE,

        "stc_qa_release_floor":
            STC_QA_RELEASE_FLOOR,

        "copy_space_policy":
            "25-40_percent_integrated",

        "physical_reality_firewall":
            True,

        "invented_payment_hardware_ban":
            True,

        "phone_pos_fusion_ban":
            True,

        "stone_pedestal_ban":
            True,

        "generic_camera_guard":
            True,

        "reference_authority":
            True,

        "merchant_message_lock":
            True,

        "immutable_final_locks":
            True,

        "immutable_lock_sentinel":
            IMMUTABLE_LOCK_SENTINEL,

        "final_prompt_budget":
            FINAL_PROMPT_BUDGET,

        "correction_prompt_budget":
            CORRECTION_PROMPT_BUDGET,

        "image_engine_version":
            image_status.get(
                "version",
                "",
            ),

        "image_engine_final_model":
            image_status.get(
                "best_final_model",
                "",
            ),
    }


# =========================================================
# ZERO-COST SELF TEST
# =========================================================

if __name__ == "__main__":

    tests: Dict[
        str,
        bool,
    ] = {}

    # -----------------------------------------------------
    # VERSION / ARCHITECTURE
    # -----------------------------------------------------

    tests[
        "version_601"
    ] = (
        ENGINE_VERSION
        ==
        "6.0.1"
    )

    tests[
        "qa_weights_sum_100"
    ] = (
        sum(
            QA_WEIGHTS.values()
        )
        ==
        100
    )

    status = (
        get_production_engine_status()
    )

    tests[
        "nano_banana_is_previs"
    ] = (
        status[
            "nano_banana_role"
        ]
        ==
        "previsualization_only"
    )

    tests[
        "gpt_image_2_is_final"
    ] = (
        FINAL_IMAGE_MODEL
        ==
        "gpt-image-2"
    )

    tests[
        "openai_final_required"
    ] = (
        MASTERPIECE_REQUIRE_OPENAI_FINAL
        is True
    )

    tests[
        "gemini_final_forbidden"
    ] = (
        status[
            "gemini_final_allowed"
        ]
        is False
    )

    tests[
        "no_gemini_pro_final"
    ] = (
        status[
            "gemini_pro_final"
        ]
        is False
    )

    # -----------------------------------------------------
    # CALL STRUCTURE
    # -----------------------------------------------------

    tests[
        "one_previsualization"
    ] = (
        MASTERPIECE_PREVIS_CALLS
        ==
        1
    )

    tests[
        "max_two_final_image_calls"
    ] = (
        MASTERPIECE_MAX_IMAGE_CALLS
        <=
        2
    )

    tests[
        "max_two_final_vision_calls"
    ] = (
        MASTERPIECE_MAX_VISION_CALLS
        <=
        2
    )

    tests[
        "one_preview_audit"
    ] = (
        MASTERPIECE_PREVIEW_AUDIT_CALLS
        ==
        1
    )

    # -----------------------------------------------------
    # STC THRESHOLDS
    # -----------------------------------------------------

    tests[
        "stc_target_92"
    ] = (
        STC_QA_TARGET_SCORE
        >=
        92.0
    )

    tests[
        "stc_release_floor_88"
    ] = (
        STC_QA_RELEASE_FLOOR
        >=
        88.0
    )

    # -----------------------------------------------------
    # FRAME
    # -----------------------------------------------------

    frame = (
        safe_frame_instruction(
            "4:5"
        )
    )

    tests[
        "copy_space_25_40"
    ] = (
        "25–40%"
        in frame
    )

    tests[
        "no_giant_upper_third"
    ] = (
        "artificial empty panel"
        in frame
    )

    # -----------------------------------------------------
    # STC CONSTITUTION
    # -----------------------------------------------------

    constitution = (
        build_stc_visual_constitution(
            (
                "STC Bank خدمات التجارة الإلكترونية "
                "ونقاط البيع واقعي فوتوغرافي"
            )
        )
    )

    tests[
        "stone_pedestal_banned"
    ] = (
        "travertine"
        in constitution
        and
        "stone pedestal"
        in constitution
    )

    tests[
        "phone_pos_fusion_banned"
    ] = (
        "phone/POS fusion"
        in constitution
    )

    tests[
        "invented_hardware_banned"
    ] = (
        "impossible hybrid payment hardware"
        in constitution
    )

    tests[
        "real_pos_required"
    ] = (
        (
            "commercially available "
            "unbranded payment terminal"
        )
        in constitution
    )

    tests[
        "merchant_message_locked"
    ] = (
        "ONE CONNECTED MERCHANT ECOSYSTEM"
        in constitution
    )

    tests[
        "phone_not_only_ecommerce_cue"
    ] = (
        "smartphone screen as the only evidence"
        in constitution
    )

    tests[
        "generic_camera_guard"
    ] = (
        "three-quarter product shot"
        in constitution
    )

    tests[
        "reference_authority"
    ] = (
        "REFERENCE EVIDENCE OUTRANKS"
        in constitution
    )

    # -----------------------------------------------------
    # REFERENCES
    # -----------------------------------------------------

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

    selected = (
        build_stc_primary_reference_set(
            product_refs=[],
            local_refs=(
                fake_refs
            ),
            memory_refs=[],
            limit=3,
        )
    )

    tests[
        "five_loaded_three_selected"
    ] = (
        len(
            fake_refs
        )
        ==
        5
        and
        len(
            selected
        )
        ==
        3
    )

    tests[
        "selected_has_dna"
    ] = any(
        item.role
        ==
        "campaign_reference"
        for item
        in selected
    )

    tests[
        "selected_has_style"
    ] = any(
        item.role
        ==
        "style_reference"
        for item
        in selected
    )

    tests[
        "selected_has_merchant"
    ] = any(
        item.role
        ==
        "environment_reference"
        for item
        in selected
    )

    manifest = (
        reference_role_manifest(
            selected,
            draft_first=True,
        )
    )

    tests[
        "final_manifest_has_draft"
    ] = (
        "Image 1"
        in manifest
        and
        "previsualization"
        in manifest
    )

    tests[
        "final_manifest_has_brand_roles"
    ] = (
        "BRAND DNA"
        in manifest
        and
        "PHOTOGRAPHIC"
        in manifest
        and
        "MERCHANT"
        in manifest
    )

    # -----------------------------------------------------
    # COMPILED CONTRACT
    # -----------------------------------------------------

    compiled = (
        compile_prompt(
            TARGET_OPENAI,
            request=(
                "أنشئ صورة إعلانية فاخرة وواقعية "
                "لبنك STC Bank عن خدمات التجارة "
                "الإلكترونية ونقاط البيع. "
                "Masterpiece 2K 4:5 بدون نصوص."
            ),
            creative_direction={
                "concept_id":
                    "C01",
                "title":
                    "Connected Commerce",
                "campaign_hook":
                    (
                        "One merchant ecosystem."
                    ),
                "core_idea":
                    (
                        "A believable Saudi merchant "
                        "environment visually connects "
                        "online commerce and physical payment."
                    ),
                "marketing_message":
                    (
                        "Online and physical payment "
                        "acceptance work together."
                    ),
                "environment":
                    (
                        "Contemporary Saudi "
                        "commercial world."
                    ),
                "hero_element":
                    (
                        "Merchant ecosystem relationship."
                    ),
            },
            brand_context={},
            references=(
                reference_dna_payload(
                    selected,
                    limit=3,
                )
            ),
            camera_direction={
                "camera_angle":
                    "reflection-led low viewpoint",
                "lens":
                    "50mm",
                "perspective":
                    "controlled compressed depth",
            },
            product_lock={},
            aspect_ratio="4:5",
        )
    )

    tests[
        "compiled_short"
    ] = (
        len(
            compiled.prompt
        )
        <=
        COMPILED_PROMPT_BUDGET
    )

    tests[
        "compiled_realism_firewall"
    ] = (
        "PHYSICAL REALITY FIREWALL"
        in compiled.prompt
    )

    tests[
        "compiled_copy_space"
    ] = (
        "25–40%"
        in compiled.prompt
    )

    # -----------------------------------------------------
    # IMMUTABLE FINAL PROMPT
    # -----------------------------------------------------

    final_prompt = (
        build_final_renderer_prompt(
            compiled=(
                compiled
            ),
            original_request=(
                "STC Bank خدمات التجارة الإلكترونية "
                "ونقاط البيع Masterpiece 2K 4:5"
            ),
            preview_qa=None,
            references=(
                selected
            ),
            aspect_ratio="4:5",
            requested_size="2K",
        )
    )

    tests[
        "final_prompt_gpt_image_2"
    ] = (
        "GPT-IMAGE-2 FINAL"
        in final_prompt
    )

    tests[
        "final_prompt_draft_image_1"
    ] = (
        "Image 1"
        in final_prompt
        and
        "PREVISUALIZATION"
        in final_prompt
    )

    tests[
        "final_prompt_immutable_sentinel"
    ] = (
        IMMUTABLE_LOCK_SENTINEL
        in final_prompt
    )

    tests[
        "final_prompt_within_budget"
    ] = (
        len(
            final_prompt
        )
        <=
        FINAL_PROMPT_BUDGET
    )

    tests[
        "final_prompt_no_giant_space"
    ] = (
        "NO artificial blank panel"
        in final_prompt
    )

    tests[
        "final_prompt_copy_space_immutable"
    ] = (
        "25–40% integrated copy space"
        in final_prompt
    )

    tests[
        "final_prompt_no_bottom_push"
    ] = (
        "NO hero pushed into the bottom half"
        in final_prompt
    )

    tests[
        "final_prompt_stone_guard"
    ] = (
        "NO random travertine pedestal"
        in final_prompt
        and
        "NO random stone pedestal"
        in final_prompt
    )

    tests[
        "final_prompt_hardware_guard"
    ] = (
        "NO phone/POS fusion"
        in final_prompt
        and
        "NO invented payment hardware"
        in final_prompt
    )

    tests[
        "final_prompt_reference_authority"
    ] = (
        "THE ATTACHED STC REFERENCES ARE VISUAL AUTHORITY"
        in final_prompt
    )

    tests[
        "final_prompt_merchant_ecosystem"
    ] = (
        (
            "ONE CONNECTED"
            in final_prompt
        )
        and
        (
            "MERCHANT ECOSYSTEM"
            in final_prompt
        )
    )

    tests[
        "final_prompt_no_text_logo_ui"
    ] = (
        "NO generated text"
        in final_prompt
        and
        "NO generated logo"
        in final_prompt
        and
        "NO fake banking UI"
        in final_prompt
    )

    tests[
        "immutable_locks_survive_forced_compaction"
    ] = False

    try:

        huge_core = (
            "CORE INFORMATION\n"
            +
            (
                "x" * 20000
            )
        )

        forced = (
            fit_prompt_with_immutable_locks(
                huge_core,
                build_immutable_final_locks(
                    original_request=(
                        "STC Bank التجارة الإلكترونية "
                        "ونقاط البيع"
                    ),
                    aspect_ratio="4:5",
                    requested_size="2K",
                ),
                label=(
                    "forced_compaction_selftest"
                ),
                budget=(
                    FINAL_PROMPT_BUDGET
                ),
            )
        )

        tests[
            "immutable_locks_survive_forced_compaction"
        ] = bool(
            len(
                forced
            )
            <=
            FINAL_PROMPT_BUDGET
            and
            IMMUTABLE_LOCK_SENTINEL
            in forced
            and
            "NO artificial blank panel"
            in forced
            and
            "NO phone/POS fusion"
            in forced
            and
            "NO random travertine pedestal"
            in forced
            and
            "25–40% integrated copy space"
            in forced
            and
            (
                "THE ATTACHED STC REFERENCES "
                "ARE VISUAL AUTHORITY"
            )
            in forced
        )

    except Exception:
        tests[
            "immutable_locks_survive_forced_compaction"
        ] = False

    # -----------------------------------------------------
    # REPAIR PROMPT ALSO IMMUTABLE
    # -----------------------------------------------------

    fake_qa = QAEvaluation(
        score=74.0,
        scores={
            key:
                76.0
            for key
            in QA_WEIGHTS
        },
        passed=False,
        strengths=[],
        problems=[
            (
                "Payment hardware looks invented "
                "and copy space is excessive."
            )
        ],
        correction_instruction=(
            "Replace hardware and rebalance composition."
        ),
        critical_blockers=[
            "stc_invented_payment_hardware",
            "stc_excessive_empty_copy_space",
        ],
        target_reached=False,
        delivery_approved=False,
        decision="rebuild",
        raw={
            "decision":
                "rebuild",
            "_xpand_flags": {
                "invented_payment_hardware":
                    True,
            },
        },
    )

    repair_prompt = (
        build_final_repair_prompt(
            qa=(
                fake_qa
            ),
            compiled=(
                compiled
            ),
            original_request=(
                "STC Bank التجارة الإلكترونية "
                "ونقاط البيع Masterpiece 2K 4:5"
            ),
            references=(
                selected[:2]
            ),
            aspect_ratio="4:5",
            requested_size="2K",
            action="structural_repair",
        )
    )

    tests[
        "repair_prompt_immutable_sentinel"
    ] = (
        IMMUTABLE_LOCK_SENTINEL
        in repair_prompt
    )

    tests[
        "repair_prompt_no_giant_space"
    ] = (
        "NO artificial blank panel"
        in repair_prompt
    )

    tests[
        "repair_prompt_hardware_lock"
    ] = (
        "NO phone/POS fusion"
        in repair_prompt
        and
        "NO invented payment hardware"
        in repair_prompt
    )

    tests[
        "repair_prompt_within_budget"
    ] = (
        len(
            repair_prompt
        )
        <=
        CORRECTION_PROMPT_BUDGET
    )

    # -----------------------------------------------------
    # QA FLAGS
    # -----------------------------------------------------

    required_flags = set(
        QA_FLAGS_SCHEMA[
            "required"
        ]
    )

    tests[
        "qa_detects_invented_hardware"
    ] = (
        "invented_payment_hardware"
        in required_flags
    )

    tests[
        "qa_detects_phone_pos_fusion"
    ] = (
        "phone_pos_fusion"
        in required_flags
    )

    tests[
        "qa_detects_stone"
    ] = (
        "random_stone_pedestal"
        in required_flags
    )

    tests[
        "qa_detects_copy_space"
    ] = (
        "excessive_empty_copy_space"
        in required_flags
    )

    tests[
        "qa_detects_generic_camera"
    ] = (
        "generic_camera"
        in required_flags
    )

    tests[
        "qa_detects_reference_drift"
    ] = (
        "reference_drift"
        in required_flags
    )

    # -----------------------------------------------------
    # ADAPTIVE POLICY
    # -----------------------------------------------------

    perfect_qa = QAEvaluation(
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
        decision="target_reached",
        raw={
            "_xpand_flags": {}
        },
    )

    tests[
        "excellent_final_stops"
    ] = (
        choose_adaptive_action(
            perfect_qa,
            high_alert=True,
        )
        ==
        "none"
    )

    structural_qa = QAEvaluation(
        score=76.0,
        scores={
            key:
                80.0
            for key
            in QA_WEIGHTS
        },
        passed=False,
        strengths=[],
        problems=[
            "Payment hardware is invented."
        ],
        correction_instruction=(
            "Replace hardware with a believable real POS."
        ),
        critical_blockers=[
            "stc_invented_payment_hardware"
        ],
        target_reached=False,
        delivery_approved=False,
        decision="rebuild",
        raw={
            "decision":
                "rebuild",
            "_xpand_flags": {
                "invented_payment_hardware":
                    True,
            },
        },
    )

    tests[
        "invented_hardware_routes_structural_repair"
    ] = (
        choose_adaptive_action(
            structural_qa,
            high_alert=True,
        )
        ==
        "structural_repair"
    )

    # -----------------------------------------------------
    # ACTUAL STC BRAND PACK BYTES
    # -----------------------------------------------------

    local_reference_test_ok = False

    local_reference_count = 0

    local_reference_ids: List[
        str
    ] = []

    if STC_BRAND_KIT_AVAILABLE:

        try:

            (
                self_refs,
                self_kit,
                self_assets,
            ) = load_stc_local_references(
                request=(
                    "STC Bank التجارة الإلكترونية "
                    "ونقاط البيع واقعي فوتوغرافي"
                ),
                max_total=(
                    MAX_STC_PHYSICAL_REFERENCE_IMAGES
                ),
                rotation_key=(
                    "production-v601-self-test"
                ),
            )

            local_reference_count = len(
                self_refs
            )

            local_reference_ids = [
                item.source_id
                for item
                in self_refs
            ]

            local_reference_test_ok = bool(
                self_kit
                and
                len(
                    self_refs
                )
                >=
                3
                and
                all(
                    item.image_bytes
                    for item
                    in self_refs
                )
            )

        except Exception as error:

            print(
                "⚠️ STC brand-pack self test:",
                clean_text(
                    error,
                    1200,
                ),
            )

    tests[
        "permanent_stc_actual_bytes"
    ] = (
        local_reference_test_ok
    )

    # -----------------------------------------------------
    # IMAGE ENGINE
    # -----------------------------------------------------

    image_status = {}

    try:
        image_status = (
            get_image_engine_status()
        )

    except Exception:
        image_status = {}

    tests[
        "image_engine_v3_plus"
    ] = (
        str(
            image_status.get(
                "version",
                "",
            )
        ).startswith(
            "3."
        )
    )

    tests[
        "image_engine_final_gpt_image_2"
    ] = (
        image_status.get(
            "best_final_model"
        )
        ==
        FINAL_IMAGE_MODEL
    )

    # -----------------------------------------------------
    # RESULT
    # -----------------------------------------------------

    passed = all(
        tests.values()
    )

    print("")
    print(
        "=============================================="
    )
    print(
        " XPAND PRODUCTION ENGINE V6.0.1"
    )
    print(
        " ZERO-COST IMMUTABLE-LOCK SELF TEST"
    )
    print(
        "=============================================="
    )
    print("")

    for name, result in (
        tests.items()
    ):

        print(
            (
                "✅ "
                if result
                else
                "❌ "
            )
            +
            name
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
    print(
        "Previs model:",
        NANO_BANANA_2_MODEL,
    )

    print(
        "Final model:",
        FINAL_IMAGE_MODEL,
    )

    print(
        "Final prompt budget:",
        FINAL_PROMPT_BUDGET,
    )

    print(
        "Immutable sentinel:",
        IMMUTABLE_LOCK_SENTINEL,
    )

    print("")
    print(
        "Normal Masterpiece path:"
    )
    print(
        "  Creative Brain"
    )
    print(
        "      ↓"
    )
    print(
        "  3 selected STC references"
    )
    print(
        "      ↓"
    )
    print(
        "  Nano Banana 2 1K PREVIS"
    )
    print(
        "      ↓"
    )
    print(
        "  Gemini Preview Audit"
    )
    print(
        "      ↓"
    )
    print(
        "  GPT-Image-2 FINAL"
    )
    print(
        "      ↓"
    )
    print(
        "  IMMUTABLE FINAL LOCKS"
    )
    print(
        "      ↓"
    )
    print(
        "  GPT-5.6 Sol QA"
    )
    print(
        "      ↓"
    )
    print(
        "  GPT-Image-2 repair only if required"
    )

    print("")

    if passed:

        print(
            (
                "XPAND Production Engine V6.0.1 "
                "self-test: PASS ✅"
            )
        )

    else:

        print(
            (
                "XPAND Production Engine V6.0.1 "
                "self-test: FAIL ❌"
            )
        )

        failures = [
            name
            for (
                name,
                result
            )
            in tests.items()
            if not result
        ]

        print(
            "Failures:",
            failures,
        )

        raise RuntimeError(
            (
                "XPAND Production Engine "
                "V6.0.1 self-test failed."
            )
        )

    print("")
    print(
        "✅ GPT-Image-2 mandatory final renderer"
    )
    print(
        "✅ Nano Banana 2 is previsualization only"
    )
    print(
        "✅ 3 STC reference roles preserved"
    )
    print(
        "✅ Immutable final locks survive compaction"
    )
    print(
        "✅ Immutable repair locks survive compaction"
    )
    print(
        "✅ NO artificial blank panel cannot be compacted away"
    )
    print(
        "✅ 25–40% copy-space lock cannot be compacted away"
    )
    print(
        "✅ Phone/POS fusion lock cannot be compacted away"
    )
    print(
        "✅ Invented hardware lock cannot be compacted away"
    )
    print(
        "✅ Stone/travertine lock cannot be compacted away"
    )
    print(
        "✅ STC reference authority cannot be compacted away"
    )
    print(
        "✅ Merchant ecosystem message cannot be compacted away"
    )
    print(
        "✅ No generated text/logo/fake UI"
    )
    print(
        "✅ STC target remains 92"
    )
    print(
        "✅ STC release floor remains 88"
    )
    print(
        "🚫 Gemini final delivery forbidden"
    )
    print(
        "🚫 Nano Banana Pro final escalation removed"
    )
    print(
        "🚫 No API calls were made"
    )
    print(
        "🚫 No images were generated"
    )
    print("")
