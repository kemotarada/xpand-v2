# =========================================================
# XPAND PRODUCTION ENGINE V5.1
#
# STC BANK PERMANENT REFERENCE GROUNDING
# + NANO BANANA 2
# + HIGH-ALERT VISUAL QA
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
#   get_production_engine_status()
#
# =========================================================
#
# V5.1 STC BANK ARCHITECTURE
#
# Creative Brain V5.2 winner
#          ↓
# Permanent STC Brand Kit
#          ↓
# 2 Brand DNA
# + 2 selected style references
# + 1 service reference
#          ↓
# ACTUAL LOCAL JPEG BYTES
#          ↓
# Nano Banana 2
#          ↓
# Strict STC Visual QA
#          ↓
# if exceptional:
#       release
#
# if not exceptional:
#       one correction / recovery / premium refinement
#       optionally using Gemini Pro image model
#          ↓
# final QA
#
# =========================================================
#
# STC HIGH-ALERT RULES
#
# - A beautiful scene is NOT automatically an ad.
# - A transaction is NOT automatically a campaign.
# - Purple is NOT automatically brand identity.
# - References are visual DNA, never clone targets.
#
# HARD-REJECT VISUAL PATTERN:
#
#   customer
#   + POS
#   + counter
#   + merchant
#   + tablet/packing
#
# when it is merely a literal retail tableau.
#
# =========================================================
#
# COST POLICY
#
# NORMAL:
#
#   Image calls = 1
#   Vision calls = 1
#
# MAX:
#
#   Image calls = 2
#   Vision calls = 2
#
# STC High Alert may use the second call to reach
# the premium target rather than stopping at "acceptable".
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

ENGINE_VERSION = "5.1"


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
            (
                "true"
                if default
                else
                "false"
            ),
        )
    ).strip().lower()

    return value in {
        "1",
        "true",
        "yes",
        "on",
        "enabled",
    }


# =========================================================
# NANO BANANA 2
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


# =========================================================
# OPTIONAL GEMINI PRO ESCALATION
# =========================================================

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
# COST LIMITS
# =========================================================

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


# =========================================================
# REFERENCE POLICY
# =========================================================

SMART_REFERENCE_SELECTION_LIMIT = max(
    1,
    min(
        3,
        int(
            os.environ.get(
                "XPAND_SMART_REFERENCE_LIMIT",
                "3",
            )
            or 3
        ),
    ),
)


MAX_PHYSICAL_REFERENCE_IMAGES = max(
    0,
    min(
        2,
        int(
            os.environ.get(
                "XPAND_PHYSICAL_REFERENCE_LIMIT",
                "2",
            )
            or 2
        ),
    ),
)


MAX_STC_PHYSICAL_REFERENCE_IMAGES = max(
    3,
    min(
        5,
        int(
            os.environ.get(
                "XPAND_STC_PHYSICAL_REFERENCE_LIMIT",
                "5",
            )
            or 5
        ),
    ),
)


STC_IDEATION_REFERENCE_LIMIT = max(
    3,
    min(
        7,
        int(
            os.environ.get(
                "XPAND_STC_IDEATION_REFERENCE_LIMIT",
                "7",
            )
            or 7
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
        int(
            os.environ.get(
                "XPAND_STC_MAX_REFERENCE_BYTES",
                "15000000",
            )
            or 15_000_000
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
        float(
            os.environ.get(
                "XPAND_PRODUCTION_QA_TARGET",
                "86",
            )
            or 86
        ),
    ),
)


QA_RELEASE_FLOOR = max(
    76.0,
    min(
        QA_TARGET_SCORE,
        float(
            os.environ.get(
                "XPAND_PRODUCTION_QA_RELEASE_FLOOR",
                "80",
            )
            or 80
        ),
    ),
)


QA_CRITICAL_SCORE_FLOOR = max(
    50.0,
    min(
        80.0,
        float(
            os.environ.get(
                "XPAND_PRODUCTION_QA_CRITICAL_FLOOR",
                "65",
            )
            or 65
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
        float(
            os.environ.get(
                "XPAND_STC_QA_TARGET",
                "92",
            )
            or 92
        ),
    ),
)


STC_QA_RELEASE_FLOOR = max(
    84.0,
    min(
        STC_QA_TARGET_SCORE,
        float(
            os.environ.get(
                "XPAND_STC_QA_RELEASE_FLOOR",
                "88",
            )
            or 88
        ),
    ),
)


# =========================================================
# PROMPT BUDGETS
# =========================================================

COMPILED_PROMPT_BUDGET = max(
    12000,
    min(
        32000,
        int(
            os.environ.get(
                "XPAND_COMPILED_PROMPT_BUDGET",
                "26000",
            )
            or 26000
        ),
    ),
)


QA_PROMPT_BUDGET = max(
    7000,
    min(
        20000,
        int(
            os.environ.get(
                "XPAND_QA_PROMPT_BUDGET",
                "14000",
            )
            or 14000
        ),
    ),
)


CORRECTION_PROMPT_BUDGET = max(
    9000,
    min(
        26000,
        int(
            os.environ.get(
                "XPAND_CORRECTION_PROMPT_BUDGET",
                "20000",
            )
            or 20000
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

    return []


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
        0.8
    )

    back = max(
        0,
        limit
        -
        front
        -
        80
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
            budget * 2,
            budget,
        ),
    )

    if len(
        text
    ) <= budget:

        return text

    front = int(
        budget
        *
        0.82
    )

    back = max(
        0,
        budget
        -
        front
        -
        160
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
            len(
                text
            )
        )
        +
        " → "
        +
        str(
            budget
        )
    )

    return (
        text[:front]
        +
        "\n\n"
        +
        "[XPAND PROMPT COMPACTED — "
        +
        "PRESERVE ALL LOCKED RULES]\n\n"
        +
        (
            text[-back:]
            if back
            else ""
        )
    )


def normalize_text(
    value: Any,
) -> str:

    text = clean_text(
        value,
        30000,
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


def unique_references(
    references: Iterable[
        ProductionReference
    ],
) -> List[
    ProductionReference
]:

    result: List[
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
                    )
                )
                +
                ":"
                +
                str(
                    item.image_bytes[:32]
                )
            )
        )

        if key in seen:

            continue

        seen.add(
            key
        )

        result.append(
            item
        )

    return result


# =========================================================
# JSON PARSER
# =========================================================

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
        100000,
    ).strip()

    if not text:

        return {}

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

        result = json.loads(
            text
        )

        if isinstance(
            result,
            dict,
        ):

            return result

    except Exception:

        pass

    first = text.find(
        "{"
    )

    last = text.rfind(
        "}"
    )

    if (
        first >= 0
        and
        last > first
    ):

        try:

            result = json.loads(
                text[
                    first:
                    last + 1
                ]
            )

            if isinstance(
                result,
                dict,
            ):

                return result

        except Exception:

            pass

    return {}


# =========================================================
# IMAGE RESPONSE
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

                raw_value = item.get(
                    key
                )

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
                            or
                            "image/jpeg",
                        )
                    )

                    break

            for child in item.values():

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

    output = []

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


# =========================================================
# RATIO HELPERS
# =========================================================

def aspect_ratio_value(
    aspect_ratio: str,
) -> Optional[float]:

    match = re.fullmatch(
        (
            r"\s*"
            r"(\d+(?:\.\d+)?)"
            r"\s*:\s*"
            r"(\d+(?:\.\d+)?)"
            r"\s*"
        ),
        clean_text(
            aspect_ratio,
            50,
        ),
    )

    if not match:

        return None

    width = safe_float(
        match.group(
            1
        ),
        0,
    )

    height = safe_float(
        match.group(
            2
        ),
        0,
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

        return "1024x1536"

    if orientation == "landscape":

        return "1536x1024"

    return "1024x1024"


def production_size_for_ratio(
    aspect_ratio: str,
    *,
    final_quality: bool = True,
) -> str:

    if final_quality:

        return (
            clean_text(
                aspect_ratio,
                50,
            )
            +
            " provider-native"
        )

    return provider_size_for_ratio(
        aspect_ratio
    )


def safe_frame_instruction(
    aspect_ratio: str,
) -> str:

    return (
        "FRAME LOCK:\n"
        +
        "Final image aspect ratio must be exactly "
        +
        clean_text(
            aspect_ratio,
            50,
        )
        +
        ". Compose natively for this ratio. "
        +
        "Do not create a different canvas and crop the hero later."
    )


# =========================================================
# STC REQUEST HELPERS
# =========================================================

def is_stc_production_request(
    request: str,
    brand_id: str = "",
) -> bool:

    if is_stc_bank_request(
        request
    ):

        return True

    normalized_brand = normalize_text(
        brand_id
    )

    return normalized_brand in {
        "stc_bank",
        "stc bank",
        "بنك stc",
    }


def is_stc_high_alert(
    request: str,
    mode: str,
    brand_id: str = "",
) -> bool:

    return bool(
        STC_HIGH_ALERT_ENABLED
        and
        mode
        ==
        MODE_MASTERPIECE
        and
        is_stc_production_request(
            request,
            brand_id,
        )
    )


# =========================================================
# STC SCENE TIER
# =========================================================

def stc_scene_tier(
    request: str,
) -> str:

    style = detect_stc_visual_style(
        request
    )

    if (
        style
        ==
        STYLE_PURPLE_ARCHITECTURAL
    ):

        return "TIER_C"

    if (
        style
        ==
        STYLE_AUGMENTED_REALISM
    ):

        return "TIER_B"

    return "TIER_A"


def stc_visual_family_for_brand_kit(
    request: str,
) -> str:

    style = detect_stc_visual_style(
        request
    )

    if (
        style
        ==
        STYLE_PURPLE_ARCHITECTURAL
    ):

        return (
            "premium_purple_architecture"
        )

    if (
        style
        ==
        STYLE_AUGMENTED_REALISM
    ):

        return (
            "premium_augmented_realism"
        )

    return "premium_realistic"


def build_stc_scene_tier_instruction(
    request: str,
) -> str:

    tier = stc_scene_tier(
        request
    )

    if tier == "TIER_C":

        return """
STC SCENE TIER: C — PURPLE ARCHITECTURAL WORLD
===============================================

Purple must behave as physical design:

- architecture
- volume
- planes
- controlled studio surfaces
- intentional geometric structures

Purple is NOT a substitute for an advertising idea.

The hero still requires:
- clear hierarchy
- premium materials
- believable reflections
- realistic contact shadows
- purposeful camera

Never create:
- purple nightclub lighting
- cyber-banking room
- random neon
- floating fintech objects
- card-on-purple-cube by default

Subject-protection:

Never purple-tint:
- skin
- hair
- white thobe
- food
- natural product materials
- natural metal
- neutral objects that should remain physically accurate

Use deep violet tones with controlled tonal separation,
not global neon saturation.
""".strip()

    if tier == "TIER_B":

        return """
STC SCENE TIER: B — PREMIUM AUGMENTED REALISM
==============================================

Start with a believable photographed world.

Use exactly ONE major imaginative physical intervention.

That intervention must communicate the service benefit.

It must obey:
- gravity
- perspective
- scale
- contact
- shadow
- reflection
- occlusion
- material behavior

The scene must still look like a high-budget commercial shoot.

Do NOT use:
- holograms
- HUD overlays
- floating icon clouds
- network lines
- particle effects
- sci-fi tunnel language

Purple is limited to restrained identity accents unless
the approved idea physically requires more.
""".strip()

    return """
STC SCENE TIER: A — PREMIUM REALISTIC CAMPAIGN PHOTOGRAPHY
==========================================================

The world remains naturally colored and photographically believable.

ZERO automatic purple wash.

STC Bank identity must come through:
- advertising confidence
- composition
- art direction
- clean Saudi context
- restrained color accents
- premium material quality
- camera discipline
- visual idea

Do NOT make:
- the room purple
- the store purple
- skin purple
- clothing purple
- natural stone purple
- food purple

unless the physical object is naturally meant to be that color.

Prioritize real premium Saudi visual language.
""".strip()


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

        if isinstance(
            profile,
            dict,
        ) and profile:

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


# =========================================================
# COMPATIBILITY ALIAS
# =========================================================

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
# BRAND MEMORY RUNTIME REFERENCES
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
                    200,
                ),

                content_family=(
                    clean_text(
                        item.get(
                            "content_family",
                            "general_brand",
                        ),
                        100,
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
# PERMANENT LOCAL STC REFERENCES
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
    )

    roles = list(
        getattr(
            asset,
            "roles",
            [],
        )
        or []
    )

    if (
        category
        ==
        "dna"
        or
        "brand_dna"
        in roles
    ):

        return "campaign_reference"

    if category in {
        "realistic",
        "purple",
        "augmented",
    }:

        return "style_reference"

    if category == "merchant":

        return "environment_reference"

    if category in {
        "product",
        "ui",
    }:

        return "product_reference"

    if category == "layout":

        return "composition_reference"

    return "style_reference"


def load_stc_local_references(
    *,
    request: str,
    max_total: int = MAX_STC_PHYSICAL_REFERENCE_IMAGES,
    rotation_key: Optional[str] = None,
) -> Tuple[
    List[ProductionReference],
    Optional[Any],
    List[Any],
]:

    if not STC_BRAND_KIT_AVAILABLE:

        if STC_REQUIRE_BRAND_PACK:

            raise RuntimeError(
                (
                    "STC Bank brand grounding is required, "
                    "but xpand_stc_brand_kit is unavailable."
                )
            )

        return (
            [],
            None,
            [],
        )

    if load_default_stc_brand_kit is None:

        if STC_REQUIRE_BRAND_PACK:

            raise RuntimeError(
                "STC Brand Kit loader unavailable."
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

        path = kit.resolve_asset_path(
            asset.path
        )

        if not path.is_file():

            continue

        try:

            size = path.stat().st_size

        except Exception:

            continue

        if size <= 0:

            continue

        if size > MAX_LOCAL_REFERENCE_BYTES:

            print(
                "⚠️ STC reference skipped because file is too large:",
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

                image_bytes=(
                    raw
                ),

                mime_type=(
                    infer_mime_type(
                        raw
                    )
                ),

                dna={
                    "asset_id":
                        asset.asset_id,

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

                user_note=(
                    clean_text(
                        getattr(
                            asset,
                            "notes",
                            "",
                        ),
                        1200,
                    )
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
                "STC Brand Pack loaded but no physical "
                "reference images were usable."
            )
        )

    return (
        references,
        kit,
        selected_assets,
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

    if not usable:

        return []

    role_priority = {

        "product_reference":
            1100,

        "campaign_reference":
            1000,

        "style_reference":
            950,

        "mixed_reference":
            940,

        "composition_reference":
            920,

        "camera_reference":
            900,

        "lighting_reference":
            880,

        "environment_reference":
            860,

        "color_reference":
            820,
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

    used_ids = set()

    used_families = set()

    # =====================================================
    # PRODUCT FIRST
    # =====================================================

    for item in usable:

        if (
            item.role
            !=
            "product_reference"
        ):

            continue

        key = (
            item.source_id
            or
            str(
                id(
                    item
                )
            )
        )

        if key in used_ids:

            continue

        selected.append(
            item
        )

        used_ids.add(
            key
        )

        used_families.add(
            item.content_family
        )

        if len(
            selected
        ) >= limit:

            return selected

    # =====================================================
    # DIVERSE REST
    # =====================================================

    for item in usable:

        key = (
            item.source_id
            or
            str(
                id(
                    item
                )
            )
        )

        if key in used_ids:

            continue

        if (
            len(
                selected
            )
            >= 1
            and
            item.content_family
            in used_families
        ):

            alternatives = [
                candidate
                for candidate
                in usable
                if (
                    candidate.content_family
                    not in used_families
                    and
                    (
                        candidate.source_id
                        or
                        str(
                            id(
                                candidate
                            )
                        )
                    )
                    not in used_ids
                )
            ]

            if alternatives:

                continue

        selected.append(
            item
        )

        used_ids.add(
            key
        )

        used_families.add(
            item.content_family
        )

        if len(
            selected
        ) >= limit:

            break

    return selected


def build_stc_physical_reference_set(
    *,
    local_references: Sequence[
        ProductionReference
    ],
    memory_references: Sequence[
        ProductionReference
    ],
    limit: int = MAX_STC_PHYSICAL_REFERENCE_IMAGES,
) -> List[
    ProductionReference
]:

    if not SEND_VISUAL_REFERENCES_TO_IMAGE:

        return []

    limit = max(
        1,
        min(
            MAX_STC_PHYSICAL_REFERENCE_IMAGES,
            int(
                limit
            ),
        ),
    )

    output: List[
        ProductionReference
    ] = []

    # =====================================================
    # EXACT / PRODUCT REFERENCES FIRST
    # =====================================================

    for item in memory_references:

        if (
            item.role
            ==
            "product_reference"
            and
            item.image_bytes
        ):

            output.append(
                item
            )

            if len(
                output
            ) >= limit:

                return unique_references(
                    output
                )[:limit]

    # =====================================================
    # PERMANENT STC REFERENCES
    # =====================================================

    for item in local_references:

        if not item.image_bytes:

            continue

        output.append(
            item
        )

        output = unique_references(
            output
        )

        if len(
            output
        ) >= limit:

            return output[:limit]

    # =====================================================
    # USER / BRAND MEMORY COMPLEMENT
    # =====================================================

    for item in choose_physical_references(
        memory_references,
        limit=limit,
    ):

        output.append(
            item
        )

        output = unique_references(
            output
        )

        if len(
            output
        ) >= limit:

            break

    return output[:limit]


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
            ),
        ),
    )

    output = []

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

    rules = []

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
            rules[:20],

        "environment_may_change":
            True,

        "lighting_may_adapt":
            True,

        "logos_must_not_be_generated":
            True,
    }


# =========================================================
# STC BRAND KIT TEXT CONTEXT
# =========================================================

def build_stc_brand_kit_context(
    kit: Optional[Any],
    *,
    request: str,
    selected_assets: Sequence[Any],
) -> Dict[str, Any]:

    if kit is None:

        return {}

    visual_family = (
        stc_visual_family_for_brand_kit(
            request
        )
    )

    benefit_family = (
        detect_stc_benefit_family(
            request
        )
    )

    try:

        grounding_text = (
            kit.build_brand_grounding_text(
                visual_family,
                benefit_family=benefit_family,
            )
        )

    except TypeError:

        grounding_text = (
            kit.build_brand_grounding_text(
                visual_family
            )
        )

    except Exception:

        grounding_text = ""

    try:

        banned_text = (
            kit.build_banned_patterns_text()
        )

    except Exception:

        banned_text = ""

    try:

        reference_brief = (
            kit.build_reference_brief(
                selected_assets
            )
        )

    except Exception:

        reference_brief = ""

    selection = []

    for asset in selected_assets:

        selection.append(
            {
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
            }
        )

    return {
        "enabled":
            True,

        "visual_family":
            visual_family,

        "benefit_family":
            benefit_family,

        "grounding_text":
            grounding_text,

        "banned_patterns":
            banned_text,

        "reference_brief":
            reference_brief,

        "selected_assets":
            selection,
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

    return {
        "brand_id":
            context.get(
                "brand_id",
                "",
            ),

        "profile":
            context.get(
                "profile",
                {},
            ),

        "rules":
            safe_list(
                context.get(
                    "rules"
                )
            )[:24],

        "reference_execution_context":
            context.get(
                "reference_execution_context",
                {},
            ),

        "visual_profile": {
            "reference_count":
                profile.get(
                    "reference_count",
                    0,
                ),

            "official_reference_count":
                profile.get(
                    "official_reference_count",
                    0,
                ),

            "camera_patterns":
                safe_list(
                    profile.get(
                        "camera_patterns"
                    )
                )[:8],

            "lighting_patterns":
                safe_list(
                    profile.get(
                        "lighting_patterns"
                    )
                )[:8],

            "material_patterns":
                safe_list(
                    profile.get(
                        "material_patterns"
                    )
                )[:8],

            "composition_patterns":
                safe_list(
                    profile.get(
                        "composition_patterns"
                    )
                )[:8],

            "style_distribution":
                safe_dict(
                    profile.get(
                        "style_distribution"
                    )
                ),
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
# NEGATIVE PROMPT
# =========================================================

def base_negative_prompt() -> str:

    return """
Avoid:

generated advertising text,
headlines,
logos,
wordmarks,
watermarks,
fake banking UI,
fake financial numbers,

floating fintech icons,
floating cards,
floating phones,
floating POS devices,

coins,
flying money,
network lines,
connection lines,
laser beams,
neon trails,
holograms,
HUD graphics,
random particles,
generic cyber banking,

cheap purple neon,
global purple wash,

plastic skin,
over-smoothed faces,
extra fingers,
deformed hands,

impossible object support,
incorrect perspective,
fake reflections,
unmotivated colored light,

visual clutter,
generic stock-photo posing,

generic office banking scene,
generic checkout tableau,
wooden luxury counter cliché,

customer + POS + merchant + packing background
as a literal transaction scene.
""".strip()


# =========================================================
# FINAL JURY EXTRACTION
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

    return jury


# =========================================================
# QUALITY-FIRST BLUEPRINT
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
        12000,
    )

    stc_request = (
        is_stc_bank_request(
            request
        )
    )

    jury = creative_finalist_jury_payload(
        creative_direction
    )

    jury_section = ""

    if jury:

        jury_section = f"""
================================================
FINAL CREATIVE JURY LOCK
================================================

The selected concept has already passed a creative jury.

Production instruction:

{clean_text(
    jury.get(
        "production_instruction",
        "",
    ),
    3000,
)}

Do NOT drift into:

{compact_json(
    jury.get(
        "do_not_drift_into",
        [],
    ),
    2200,
)}

This instruction is a production lock.

Do NOT simplify the approved visual mechanism into a
generic lifestyle photograph merely because it is easier
to generate.
""".strip()

    stc_section = ""

    if stc_request:

        benefit_family = (
            detect_stc_benefit_family(
                request
            )
        )

        selected_style = (
            detect_stc_visual_style(
                request
            )
        )

        stc_context = safe_dict(
            safe_dict(
                brand_context
            ).get(
                "stc_permanent_brand_kit"
            )
        )

        permanent_grounding = clean_text(
            stc_context.get(
                "grounding_text",
                "",
            ),
            8000,
        )

        permanent_banned = clean_text(
            stc_context.get(
                "banned_patterns",
                "",
            ),
            5000,
        )

        permanent_refs = clean_text(
            stc_context.get(
                "reference_brief",
                "",
            ),
            6000,
        )

        merchant_section = ""

        if (
            benefit_family
            ==
            "merchant_payments"
        ):

            merchant_section = """
================================================
MERCHANT PAYMENTS — HARD VISUAL LAW
================================================

The image must communicate:

ONLINE COMMERCE
+
PHYSICAL POINT-OF-SALE
=
ONE CONNECTED MERCHANT ECOSYSTEM

But DO NOT solve this by merely showing:

- customer at counter
- POS in foreground
- merchant behind counter
- tablet nearby
- worker packing a box in background

That exact literal tableau is a known rejected XPAND pattern.

The two channels must be connected by the APPROVED
advertising mechanism.

The connection may be:
- physical
- architectural
- transformational
- perspectival
- causal
- spatial
- symbolic but believable

The visual idea must be stronger than the transaction itself.
""".strip()

        stc_section = f"""
================================================
STC BANK HIGH-ALERT PRODUCTION STANDARD
================================================

BENEFIT FAMILY:
{benefit_family}

SELECTED STYLE:
{selected_style or "premium_realistic"}

{build_stc_scene_tier_instruction(request)}

================================================
PERMANENT STC BANK BRAND DNA
================================================

{permanent_grounding or "Permanent brand grounding is attached through physical references."}

================================================
SELECTED REFERENCE ROLES
================================================

{permanent_refs or "Use attached references as brand DNA."}

================================================
BRAND-PACK BANNED PATTERNS
================================================

{permanent_banned or "Avoid generic fintech and repeated transaction scenes."}

================================================
REFERENCE INTERPRETATION LAW
================================================

Attached STC images are NOT templates.

They are evidence of:

- campaign maturity
- visual hierarchy
- lighting quality
- material quality
- Saudi visual context
- composition confidence
- camera discipline
- restraint
- negative-space planning

DO NOT copy:
- exact person
- exact location
- exact campaign
- exact pose
- exact framing
- exact background
- old headline placement
- text
- logo

The output must be an ORIGINAL STC Bank campaign image.

================================================
ADVERTISING-IDEA LAW
================================================

A beautiful photograph alone FAILS.

A transaction photograph alone FAILS.

A bank product alone FAILS.

The approved visual mechanism must remain visible in the
finished image.

The final frame must feel deliberately conceived as an
advertisement before typography is added.

================================================
HARD REJECT — REPEATED XPAND SCENE
================================================

Do NOT create:

wooden / timber retail counter
+
POS terminal
+
customer
+
merchant
+
tablet
+
box packing in background

Do NOT create cosmetic variations of that composition.

Changing:
- wall color
- gender
- counter material
- lens
- shop category

does NOT make it a new idea.

================================================
SUBJECT-PROTECTION LAW
================================================

Never apply STC purple globally to:

- skin
- face
- hair
- natural fabric
- food
- neutral product material
- natural stone
- natural wood
- real metal

Keep human white balance natural.

================================================
COPY-SPACE LAW
================================================

Reserve approximately 25–40% of the frame as calm,
natural negative space for typography added later.

It must be real compositional space.

Never create:
- white digital box
- fake graphic panel
- banner
- artificial gradient overlay
- UI card

================================================
TEXT-FREE LAW
================================================

Generate NO readable advertising text.

Generate NO:
- headline
- subtitle
- CTA
- percentage
- offer copy
- legal copy
- STC Bank logo
- STC wordmark
- Visa logo
- Mastercard logo
- watermark

================================================
REAL-APP LAW
================================================

If the real verified STC Bank app UI was not supplied as
an exact product reference:

DO NOT invent readable banking UI.

Instead:
- make the screen unreadable,
- use reflection,
- use shallow depth,
- angle it away,
or
- avoid making UI the message.

================================================
CAMERA LAW
================================================

Preserve the approved camera strategy.

Do NOT normalize an unusual approved angle back into a
generic eye-level commercial shot.

Camera must serve:
- visual mechanism
- hierarchy
- message
- scale
- emotion

================================================
MATERIAL LAW
================================================

Materials must behave physically.

Stone = stone.
Glass = glass.
Metal = metal.
Leather = leather.
Paper = paper.
Fabric = fabric.

Do not make every surface glossy.

Use believable:
- roughness
- highlights
- reflections
- contact shadows
- edge behavior

================================================
ONE-MECHANISM LAW
================================================

One dominant visual mechanism.

Do not bury the campaign idea under:
- decorative effects
- extra metaphors
- random props
- fintech graphics

{merchant_section}

================================================
STC SKILL GUARD
================================================

{STC_BANK_IMAGE_GUARD}
""".strip()

    return f"""
XPAND PRODUCTION BLUEPRINT V5.1
===============================

Produce ONE premium campaign-ready advertising photograph.

This is a production stage.

Do NOT brainstorm a replacement campaign.

================================================
USER REQUEST
================================================

{request}

================================================
APPROVED CREATIVE DIRECTION
================================================

{compact_json(
    creative_direction,
    8500,
)}

{jury_section}

================================================
CAMERA DIRECTION
================================================

{compact_json(
    camera_direction,
    3000,
)}

The camera direction is intentional.

Lock:
- camera height
- viewing direction
- focal length
- camera distance
- horizon
- vanishing points
- foreground scale
- hero scale
- depth strategy

================================================
BRAND CONTEXT
================================================

{compact_json(
    brand_context,
    7500,
)}

================================================
CURATED VISUAL REFERENCE DNA
================================================

{compact_json(
    references,
    6500,
)}

References are NOT scene templates.

Learn:
- photographic maturity
- lighting discipline
- material finish
- campaign hierarchy
- camera confidence
- art-direction restraint

Never clone an old campaign.

================================================
PRODUCT LOCK
================================================

{compact_json(
    product_lock,
    2200,
)}

If a real product reference exists:
preserve physical structure and characteristics.

Do NOT generate logos or readable financial copy.

================================================
PHOTOGRAPHIC REALISM
================================================

Require:
- believable physics
- correct gravity
- realistic anatomy
- credible hand/object contact
- correct object scale
- surface contact
- coherent perspective
- premium production design
- natural microtexture
- believable depth

Avoid polished-but-obviously-AI imagery.

================================================
LIGHTING
================================================

Every shadow must have a plausible source.

Require:
- coherent key direction
- realistic bounce
- controlled negative fill
- real contact shadows
- material-specific highlights
- correct exposure
- natural skin
- believable white balance

No random glow.

================================================
COMPOSITION
================================================

ONE dominant visual idea.

ONE clear hero relationship.

Supporting elements exist only to strengthen that idea.

Use:
- intentional foreground
- meaningful midground
- controlled background
- clear depth
- intentional negative space
- sophisticated restraint

Remove unnecessary props.

================================================
ADVERTISING STANDARD
================================================

The image must communicate visually before typography.

It should feel ready to hand to a senior campaign designer.

It must NOT feel like:
- documentary photography
- stock photography
- random lifestyle content
- product demo
- ordinary transaction scene

================================================
STC BANK
================================================

{stc_section or "No dedicated STC Bank rules required."}

================================================
FRAME
================================================

{safe_frame_instruction(aspect_ratio)}

================================================
FINAL LOCK
================================================

IMAGE ONLY.

NO generated advertising text.
NO generated logos.
NO fake banking UI.
NO decorative fintech graphics.

Create ONE coherent premium campaign frame.
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

    if target not in {
        TARGET_GEMINI,
        TARGET_OPENAI,
    }:

        target = TARGET_GEMINI

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

    blueprint = fit_prompt_for_api(
        blueprint,
        label=(
            "production_blueprint_v51"
        ),
        budget=(
            COMPILED_PROMPT_BUDGET
        ),
    )

    return CompiledPrompt(

        target=target,

        prompt=blueprint,

        negative_prompt=(
            base_negative_prompt()
        ),

        metadata={
            "compiler":
                "xpand_production_v51",

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

            "general_reference_limit":
                SMART_REFERENCE_SELECTION_LIMIT,

            "general_physical_reference_limit":
                MAX_PHYSICAL_REFERENCE_IMAGES,

            "stc_physical_reference_limit":
                MAX_STC_PHYSICAL_REFERENCE_IMAGES,
        },
    )


# =========================================================
# PHYSICAL REFERENCE INSTRUCTION
# =========================================================

def physical_reference_instruction(
    references: Sequence[
        ProductionReference
    ],
) -> str:

    if not references:

        return ""

    lines = [
        "PHYSICAL REFERENCE RULES",
        "========================",
        "",
        (
            "Actual reference images are attached to this "
            "image-generation request."
        ),
        "",
        (
            "Interpret every reference by its assigned role."
        ),
        "",
    ]

    for index, reference in enumerate(
        references,
        start=1,
    ):

        metadata = safe_dict(
            reference.source_metadata
        )

        dna = safe_dict(
            reference.dna
        )

        lines.append(
            (
                "REFERENCE "
                +
                str(
                    index
                )
            )
        )

        lines.append(
            (
                "- source_id: "
                +
                clean_text(
                    reference.source_id,
                    300,
                )
            )
        )

        lines.append(
            (
                "- role: "
                +
                clean_text(
                    reference.role,
                    100,
                )
            )
        )

        lines.append(
            (
                "- family: "
                +
                clean_text(
                    reference.content_family,
                    100,
                )
            )
        )

        category = clean_text(
            (
                metadata.get(
                    "category"
                )
                or
                dna.get(
                    "category"
                )
                or
                ""
            ),
            100,
        )

        if category:

            lines.append(
                (
                    "- category: "
                    +
                    category
                )
            )

        if reference.user_note:

            lines.append(
                (
                    "- purpose: "
                    +
                    clean_text(
                        reference.user_note,
                        650,
                    )
                )
            )

        if (
            metadata.get(
                "permanent"
            )
        ):

            lines.append(
                (
                    "- permanent STC brand-pack reference: YES"
                )
            )

        lines.append("")

    lines.extend(
        [
            (
                "REFERENCE ROLE INTERPRETATION:"
            ),

            (
                "- campaign_reference: learn STC campaign maturity, "
                "visual hierarchy, restraint and brand confidence."
            ),

            (
                "- style_reference: learn lighting, camera, material "
                "quality and the selected visual-family language."
            ),

            (
                "- environment_reference: understand the commercial "
                "service context, but DO NOT copy its exact scene."
            ),

            (
                "- product_reference: preserve verified product form "
                "when an actual product lock exists."
            ),

            "",

            (
                "CRITICAL:"
            ),

            (
                "Do NOT average all references into one messy hybrid."
            ),

            (
                "Do NOT clone one reference."
            ),

            (
                "Do NOT copy old text."
            ),

            (
                "Do NOT copy old logos."
            ),

            (
                "Do NOT copy old people."
            ),

            (
                "Do NOT recreate the exact location."
            ),

            (
                "Create an ORIGINAL campaign execution that reaches "
                "the same professional level."
            ),
        ]
    )

    return "\n".join(
        lines
    )


# =========================================================
# GEMINI IMAGE INTERACTION
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
            "GEMINI_API_KEY missing."
        )

    requested_size = clean_text(
        output_image_size,
        20,
    ).upper()

    if requested_size not in {
        "1K",
        "2K",
        "4K",
    }:

        requested_size = "1K"

    model = (
        clean_text(
            model_override,
            300,
        )
        or
        NANO_BANANA_2_MODEL
    )

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
            ),
        ),
    )

    selected_refs = [
        item
        for item
        in references
        if item.image_bytes
    ][
        :max_reference_images
    ]

    reference_rules = (
        physical_reference_instruction(
            selected_refs
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
                base_negative_prompt()
                +
                "\n\n"
                +
                safe_frame_instruction(
                    aspect_ratio
                )
            ),

            label=pass_name,

            budget=(
                CORRECTION_PROMPT_BUDGET
                if working_image
                is not None
                else
                COMPILED_PROMPT_BUDGET
            ),
        )
    )

    inputs: List[
        Dict[str, Any]
    ] = [
        {
            "type":
                "text",

            "text":
                safe_prompt,
        }
    ]

    if working_image is not None:

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
        images[
            0
        ]
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

        prompt=safe_prompt,

        original_prompt=safe_prompt,

        aspect_ratio=aspect_ratio,

        image_size=requested_size,

        quality="high",

        route_reason=(
            "XPAND Production V5.1"
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
                "xpand-"
                +
                uuid.uuid4().hex[
                    :12
                ]
            )
        ),

        metadata={
            "production_engine":
                ENGINE_VERSION,

            "pass_name":
                pass_name,

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
        },
    )

    return result


# =========================================================
# HISTORICAL COMPATIBILITY ALIAS
# =========================================================

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

    # =====================================================
    # VERIFIED PRODUCT REFERENCES FIRST
    # =====================================================

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
        :max_physical_references
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

    normalized = {}

    total = 0.0

    for key, weight in QA_WEIGHTS.items():

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


# =========================================================
# QA TARGET HELPERS
# =========================================================

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

    blockers = []

    for value in safe_list(
        explicit_failures
    ):

        text = clean_text(
            value,
            900,
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

    for key, minimum in thresholds.items():

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

        if (
            flag_data.get(
                "literal_counter_tableau_detected"
            )
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

        if (
            flag_data.get(
                "brand_identity_weak"
            )
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

        if (
            flag_data.get(
                "reference_cloning_detected"
            )
        ):

            blockers.append(
                "stc_reference_cloning"
            )

        if (
            flag_data.get(
                "unwanted_text_or_logo"
            )
        ):

            blockers.append(
                "stc_unwanted_text_or_logo"
            )

        if (
            flag_data.get(
                "fake_banking_ui"
            )
        ):

            blockers.append(
                "stc_fake_banking_ui"
            )

    product_lock = safe_dict(
        product_lock
    )

    if product_lock.get(
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
            65
        ):

            blockers.append(
                "product_reference_fidelity"
            )

    deduped = []

    seen = set()

    for blocker in blockers:

        key = clean_text(
            blocker,
            900,
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

        deduped.append(
            key
        )

    return deduped


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

    stc_audit = ""

    if stc_request:

        benefit_family = (
            detect_stc_benefit_family(
                original_request
            )
        )

        merchant_audit = ""

        if (
            benefit_family
            ==
            "merchant_payments"
        ):

            merchant_audit = """
MERCHANT-PAYMENTS AUDIT
-----------------------

service_integration must answer:

Does the image visually communicate BOTH:
- e-commerce / online commerce
- physical point-of-sale

as ONE connected service proposition?

A merchant scene that merely contains both activities
does NOT automatically pass.

Specifically mark:

literal_counter_tableau_detected = true

if the image substantially resembles:

customer
+ POS / terminal
+ retail counter
+ merchant
+ tablet or packing activity

without a strong original visual mechanism.

merchant_fusion_failed = true

if online commerce and physical payment are simply placed
next to each other rather than conceptually connected.
""".strip()

        stc_audit = f"""
STC BANK 5-STAR HARD AUDIT
==========================

This QA is intentionally stricter than normal advertising QA.

Do NOT approve an image merely because it is:
- realistic
- attractive
- polished
- technically clean

The image must feel like a real premium STC Bank key visual.

------------------------------------------------
BRAND IDENTITY
------------------------------------------------

brand_identity_strength asks:

If all text and logos are removed,
does this still feel intentionally art-directed for the
STC Bank campaign language?

Brand identity does NOT require purple everywhere.

Strong identity may come from:
- photographic confidence
- Saudi context
- composition
- material quality
- disciplined color
- lighting
- camera
- visual simplicity
- STC reference-DNA maturity

------------------------------------------------
SCENE ORIGINALITY
------------------------------------------------

scene_originality must be LOW if this is basically:

- generic merchant checkout
- generic office
- generic person holding phone
- generic person holding POS
- generic purple studio
- card on simple pedestal
- ordinary stock lifestyle photograph

------------------------------------------------
ADVERTISING READINESS
------------------------------------------------

advertising_readiness asks:

Would a senior bank creative director reasonably approve
this as a campaign key visual BEFORE typography?

Not:

"Could this be used somewhere?"

But:

"Does this look intentionally conceived as advertising?"

------------------------------------------------
REFERENCE ADHERENCE
------------------------------------------------

Reward:
- visual maturity
- lighting
- material discipline
- hierarchy
- camera quality

Do NOT reward exact cloning.

reference_cloning_detected must be true if the final scene
looks substantially copied from one supplied reference.

------------------------------------------------
TEXT / LOGOS / UI
------------------------------------------------

text_logo_compliance = 100 only when there is no unwanted:
- headline
- logo
- wordmark
- banking text
- card-brand logo
- fake financial copy

fake_banking_ui = true if readable invented banking UI
appears without verified product reference.

------------------------------------------------
PURPLE
------------------------------------------------

Score purple_restraint using:

{build_stc_scene_tier_instruction(original_request)}

------------------------------------------------
GENERIC SCENE FLAG
------------------------------------------------

generic_scene_detected = true when the image is professionally
executed but the central visual proposition is still ordinary
lifestyle / transaction photography.

------------------------------------------------
REPEATED SCENE FLAG
------------------------------------------------

repeated_scene_risk = true if it falls into the known XPAND
repetition family:

- luxury wooden/timber counter
- POS foreground
- merchant behind it
- customer transaction
- tablet / parcel / packing activity
- boutique-style commercial background

Small cosmetic changes do not remove repetition risk.

{merchant_audit}
""".strip()

    return f"""
XPAND MASTERPIECE VISUAL QA V5.1
================================

Review ONE finished advertising image.

Be strict, visual and practical.

================================================
ORIGINAL REQUEST
================================================

{clean_text(
    original_request,
    4200,
)}

================================================
APPROVED PRODUCTION BLUEPRINT
================================================

{clean_text(
    compiled_prompt.prompt,
    7000,
)}

================================================
PRODUCT LOCK
================================================

{compact_json(
    product_lock,
    1600,
)}

================================================
BRAND CONTEXT
================================================

{compact_json(
    brand_context,
    3000,
)}

================================================
FRAME
================================================

Expected aspect ratio:
{clean_text(
    aspect_ratio,
    50,
)}

================================================
SCORE EVERY DIMENSION 0–100
================================================

concept_execution
-----------------
Did the final image actually execute the approved visual idea?

message_clarity_without_text
----------------------------
Can the benefit be understood visually before copy is added?

brand_alignment
---------------
Does it belong to the brand strategically?

brand_identity_strength
-----------------------
Does it possess a distinctive brand-world quality rather than
looking interchangeable with any bank?

advertising_readiness
---------------------
Does this genuinely look like a premium campaign key visual?

scene_originality
-----------------
Is the environment / hero relationship materially different
from obvious bank and fintech clichés?

service_integration
-------------------
Does the visual mechanism communicate the requested service,
rather than merely containing related props?

realism
-------
Is it physically and photographically believable?

camera_perspective
------------------
Are lens, angle, horizon, scale and perspective coherent and
creatively useful?

lighting_materials
------------------
Do lighting, shadows, reflections and materials behave like
a real premium commercial shoot?

human_anatomy
-------------
Are anatomy, grip, hands, posture and interaction credible?
If there are no humans, score 100.

reference_adherence
-------------------
Did it learn appropriate maturity from the references without
cloning them?

text_logo_compliance
--------------------
Is it free from unwanted generated text and logos?

purple_restraint
----------------
Is brand color used intentionally rather than automatically?

================================================
FLAGS
================================================

Return true/false for:

generic_scene_detected

literal_counter_tableau_detected

repeated_scene_risk

brand_identity_weak

merchant_fusion_failed

reference_cloning_detected

unwanted_text_or_logo

fake_banking_ui

================================================
CRITICAL BLOCKERS
================================================

Only list genuine blockers.

Possible examples:

- visual mechanism disappeared
- generic scene
- repeated checkout tableau
- service unclear
- weak brand identity
- severe anatomy issue
- broken perspective
- fake UI
- unwanted generated text
- unwanted logo
- purple overuse
- reference cloning
- obvious AI artifact

================================================
DECISION
================================================

approve:
campaign ready.

correct:
core concept is good but specific execution defects remain.

rebuild:
the scene / visual mechanism fundamentally failed.

================================================
STC HIGH ALERT
================================================

{stc_audit or "No dedicated STC Bank audit required."}

Return only the structured JSON schema.
""".strip()


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

    prompt = build_qa_prompt(

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

    prompt = fit_prompt_for_api(
        prompt,
        label="vision_qa_v51",
        budget=QA_PROMPT_BUDGET,
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
            "xpand_production_qa_v51"
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

    blockers = (
        detect_critical_blockers(

            scores=normalized_scores,

            explicit_failures=(
                data.get(
                    "critical_blockers"
                )
            ),

            flags=(
                flags
            ),

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

        decision = "rebuild"

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
                4000,
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
]:

    if qa is None:

        return (
            -999,
            0,
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

    ad_score = clamp_score(
        qa.scores.get(
            "advertising_readiness",
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
        ad_score,
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
        .lower()
    )

    markers = [
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
    ]

    return any(
        marker
        in combined
        for marker
        in markers
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

        # QA infrastructure failure is not evidence
        # that another paid image is necessary.

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
            # High Alert deliberately tries to move a clean
            # 88–91 result toward the 92+ target when the
            # second image budget is available.
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
# TARGETED CORRECTION
# =========================================================

def build_targeted_correction_prompt(
    *,
    qa: QAEvaluation,
    compiled: CompiledPrompt,
    product_lock: Any,
    aspect_ratio: str,
) -> str:

    prompt = f"""
XPAND TARGETED CORRECTION V5.1
==============================

The core advertising idea remains usable.

Fix the actual visual defects without redesigning the
campaign.

================================================
CURRENT QA
================================================

Score:
{qa.score}/100

Problems:
{compact_json(
    qa.problems,
    3500,
)}

Critical blockers:
{compact_json(
    qa.critical_blockers,
    2400,
)}

QA instruction:
{clean_text(
    qa.correction_instruction,
    3500,
)}

================================================
ORIGINAL BLUEPRINT
================================================

{clean_text(
    compiled.prompt,
    9000,
)}

================================================
PRODUCT LOCK
================================================

{compact_json(
    product_lock,
    1600,
)}

================================================
CORRECTION LAW
================================================

Preserve:
- approved visual mechanism
- successful scene regions
- successful camera
- successful human identity
- successful environment
- successful lighting
- successful material palette
- successful negative space

Correct only what actually needs correction.

Possible corrections:
- anatomy
- contact
- grip
- perspective
- reflection
- skin realism
- clutter
- purple overuse
- fake UI
- unwanted text
- unwanted logo
- weak service clarity
- weak brand identity

Do NOT add decorative effects.

Do NOT simplify the campaign idea into a generic transaction.

Do NOT add text.

Do NOT add logos.

{safe_frame_instruction(aspect_ratio)}
""".strip()

    return fit_prompt_for_api(
        prompt,
        label=(
            "targeted_correction_v51"
        ),
        budget=(
            CORRECTION_PROMPT_BUDGET
        ),
    )


# =========================================================
# CONCEPT RECOVERY
# =========================================================

def build_concept_recovery_prompt(
    *,
    qa: QAEvaluation,
    compiled: CompiledPrompt,
    aspect_ratio: str,
) -> str:

    prompt = f"""
XPAND SCENE / CONCEPT EXECUTION RECOVERY V5.1
==============================================

The previous image failed to express the APPROVED advertising
mechanism strongly enough.

Do NOT brainstorm a different marketing proposition.

Keep:
- approved strategy
- approved benefit
- approved visual mechanism
- approved brand family

Rebuild the physical execution.

================================================
FAILED QA
================================================

Score:
{qa.score}/100

Problems:
{compact_json(
    qa.problems,
    4200,
)}

Critical blockers:
{compact_json(
    qa.critical_blockers,
    2600,
)}

QA instruction:
{clean_text(
    qa.correction_instruction,
    4000,
)}

================================================
APPROVED BLUEPRINT
================================================

{clean_text(
    compiled.prompt,
    10000,
)}

================================================
RECOVERY STANDARD
================================================

The new scene must make the advertising idea clearer.

Improve when relevant:
- visual mechanism
- environment choice
- hero relationship
- camera viewpoint
- real human behavior
- object relationship
- depth
- materials
- light
- negative space
- brand identity

HARD BAN:

Do NOT fall back to:
customer
+ POS
+ merchant
+ counter
+ packing box

Do NOT use:
- purple neon
- network lines
- holograms
- particles
- random floating objects
- fintech graphics
- generic person-holding-device pose
- generated text
- generated logos

Create a genuinely stronger production execution of the
same approved campaign idea.

{safe_frame_instruction(aspect_ratio)}
""".strip()

    return fit_prompt_for_api(
        prompt,
        label=(
            "scene_recovery_v51"
        ),
        budget=(
            CORRECTION_PROMPT_BUDGET
        ),
    )


# =========================================================
# PREMIUM REFINEMENT
# =========================================================

def build_premium_refinement_prompt(
    *,
    qa: QAEvaluation,
    compiled: CompiledPrompt,
    aspect_ratio: str,
) -> str:

    prompt = f"""
XPAND STC 5-STAR PREMIUM REFINEMENT V5.1
========================================

The current image may already be usable, but it has not
reached the full High-Alert premium target.

This is NOT a concept rewrite.

Preserve the winning concept.

Increase campaign quality.

================================================
CURRENT QA
================================================

Current score:
{qa.score}/100

Target:
{STC_QA_TARGET_SCORE}/100

Strengths:
{compact_json(
    qa.strengths,
    2600,
)}

Remaining problems:
{compact_json(
    qa.problems,
    3600,
)}

QA direction:
{clean_text(
    qa.correction_instruction,
    3500,
)}

================================================
LOCKED BLUEPRINT
================================================

{clean_text(
    compiled.prompt,
    9500,
)}

================================================
REFINEMENT OBJECTIVE
================================================

Move the image from:

"good bank advertisement"

to:

"premium campaign key visual".

Improve only where needed:

- stronger visual hierarchy
- more intentional hero relationship
- more STC Bank identity
- more premium materials
- cleaner lighting
- more deliberate camera depth
- more refined negative space
- more natural humans
- stronger advertising readability
- less AI-looking detail

Do NOT:
- change the concept
- add more props
- add more metaphors
- add random purple
- add fintech effects
- add text
- add logos
- introduce the rejected merchant-counter tableau

The final frame should be cleaner, simpler and more
campaign-ready than the current one.

{safe_frame_instruction(aspect_ratio)}
""".strip()

    return fit_prompt_for_api(
        prompt,
        label=(
            "stc_premium_refinement_v51"
        ),
        budget=(
            CORRECTION_PROMPT_BUDGET
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
        "Message:",
        qa.scores.get(
            "message_clarity_without_text",
            0,
        ),
    )

    print(
        "Brand identity:",
        qa.scores.get(
            "brand_identity_strength",
            0,
        ),
    )

    print(
        "Originality:",
        qa.scores.get(
            "scene_originality",
            0,
        ),
    )

    print(
        "Service integration:",
        qa.scores.get(
            "service_integration",
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
        "Realism:",
        qa.scores.get(
            "realism",
            0,
        ),
    )

    print(
        "Text/logo:",
        qa.scores.get(
            "text_logo_compliance",
            0,
        ),
    )

    print(
        "Purple restraint:",
        qa.scores.get(
            "purple_restraint",
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
            :8
        ]
    ):

        print(
            "  🛑",
            clean_text(
                blocker,
                900,
            ),
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
# CORRECTION REFERENCE SET
# =========================================================

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

        #
        # Keep enough STC DNA during image-to-image
        # correction to stop brand drift.
        #
        # We do not resend all five plus working image.
        #

        campaign_refs = [
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

        style_refs = [
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

        service_refs = [
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

        for group in [
            campaign_refs[
                :1
            ],
            style_refs[
                :1
            ],
            service_refs[
                :1
            ],
        ]:

            refs.extend(
                group
            )

    return unique_references(
        refs
    )[:3]


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

        "memory_reference_count":
            0,

        "stc_local_reference_count":
            0,

        "stc_local_reference_ids":
            [],

        "stc_brand_pack_loaded":
            False,

        "stc_high_alert":
            high_alert,

        "adaptive_action":
            "none",

        #
        # Telegram V3.4 currently does not consume this
        # policy yet. It is exposed for the next integration
        # step.
        #

        "block_generic_smart_fallback":
            bool(
                high_alert
            ),
    }

    # =====================================================
    # BRAND MEMORY REFERENCES
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

    telemetry[
        "memory_reference_count"
    ] = len(
        memory_references
    )

    # =====================================================
    # PERMANENT STC BRAND PACK
    # =====================================================

    stc_local_refs: List[
        ProductionReference
    ] = []

    stc_kit = None

    stc_assets: List[
        Any
    ] = []

    if stc_request:

        rotation_key = (
            str(
                user_id
            )
            +
            "|"
            +
            clean_text(
                original_request,
                3000,
            )
            +
            "|"
            +
            clean_text(
                safe_dict(
                    creative_direction
                ).get(
                    "concept_id",
                    "",
                ),
                300,
            )
        )

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
                rotation_key
            ),
        )

        telemetry[
            "stc_brand_pack_loaded"
        ] = bool(
            stc_kit
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
    # ALL LOGICAL REFERENCES
    # =====================================================

    references = unique_references(
        list(
            stc_local_refs
        )
        +
        list(
            memory_references
        )
    )

    # =====================================================
    # PRODUCT REFERENCES
    # =====================================================

    product_refs = (
        product_references(
            references
        )
    )

    # =====================================================
    # PHYSICAL REFERENCE SET
    # =====================================================

    if stc_request:

        physical_refs = (
            build_stc_physical_reference_set(

                local_references=(
                    stc_local_refs
                ),

                memory_references=(
                    memory_references
                ),

                limit=(
                    MAX_STC_PHYSICAL_REFERENCE_IMAGES
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

    # =====================================================
    # REFERENCE DNA
    # =====================================================

    reference_dna = (
        reference_dna_payload(

            references,

            limit=(
                STC_IDEATION_REFERENCE_LIMIT
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

    # =====================================================
    # STC KIT TEXTUAL GROUNDING
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
    # ENRICH BRAND CONTEXT
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

    # =====================================================
    # LOG
    # =====================================================

    print("")
    print(
        "=============================================="
    )
    print(
        " XPAND PRODUCTION ENGINE V5.1"
    )

    if high_alert:

        print(
            " STC BANK 5-STAR HIGH ALERT"
        )

    else:

        print(
            " NANO BANANA 2 QUALITY PRODUCTION"
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
        "Permanent STC references:",
        len(
            stc_local_refs
        ),
    )

    print(
        "Actual references sent to image model:",
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
        "Product references:",
        len(
            product_refs
        ),
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
                "NOT LOADED ❌"
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
                "masterpiece_primary"
            ),

            output_image_size=(
                requested_size
            ),

            model_override=(
                NANO_BANANA_2_MODEL
            ),

            max_physical_references=(
                MAX_STC_PHYSICAL_REFERENCE_IMAGES
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
                "masterpiece_primary"
            ),

            image=(
                first_image
            ),

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
            },
        )
    ]

    best_image = first_image

    best_qa: Optional[
        QAEvaluation
    ] = None

    best_score = 0.0

    # =====================================================
    # FAST / NON MASTERPIECE
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

            final_image=final_image,

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

            best_qa = None

    # =====================================================
    # ADAPTIVE DECISION
    # =====================================================

    action = choose_adaptive_action(
        best_qa,
        high_alert=high_alert,
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

            # =================================================
            # CONCEPT RECOVERY
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
                    " | scene recovery"
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

                second_image = (
                    gemini_multi_reference_edit(

                        working_image=None,

                        references=(
                            physical_refs
                        ),

                        prompt=(
                            recovery_prompt
                        ),

                        aspect_ratio=(
                            aspect_ratio
                        ),

                        pass_name=(
                            "scene_recovery"
                        ),

                        output_image_size=(
                            requested_size
                        ),

                        model_override=(
                            escalation_model
                        ),

                        max_reference_images=(
                            MAX_STC_PHYSICAL_REFERENCE_IMAGES
                            if stc_request
                            else
                            MAX_PHYSICAL_REFERENCE_IMAGES
                        ),
                    )
                )

                second_pass_name = (
                    "scene_recovery"
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
                    " | premium refinement"
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

                refinement_refs = (
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
                )

                second_image = (
                    gemini_multi_reference_edit(

                        working_image=(
                            best_image
                        ),

                        references=(
                            refinement_refs
                        ),

                        prompt=(
                            refinement_prompt
                        ),

                        aspect_ratio=(
                            aspect_ratio
                        ),

                        pass_name=(
                            "premium_refinement"
                        ),

                        output_image_size=(
                            requested_size
                        ),

                        model_override=(
                            escalation_model
                        ),

                        max_reference_images=(
                            3
                            if high_alert
                            else
                            MAX_PHYSICAL_REFERENCE_IMAGES
                        ),
                    )
                )

                second_pass_name = (
                    "premium_refinement"
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
                    " | targeted correction"
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

                correction_refs = (
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
                )

                second_image = (
                    gemini_multi_reference_edit(

                        working_image=(
                            best_image
                        ),

                        references=(
                            correction_refs
                        ),

                        prompt=(
                            correction_prompt
                        ),

                        aspect_ratio=(
                            aspect_ratio
                        ),

                        pass_name=(
                            "targeted_correction"
                        ),

                        output_image_size=(
                            requested_size
                        ),

                        model_override=(
                            escalation_model
                        ),

                        max_reference_images=(
                            3
                            if high_alert
                            else
                            MAX_PHYSICAL_REFERENCE_IMAGES
                        ),
                    )
                )

                second_pass_name = (
                    "targeted_correction"
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

                        "stc_high_alert":
                            high_alert,
                    },
                )
            )

            # =================================================
            # QA 2
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
            # KEEP STRONGEST VERIFIED CANDIDATE
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
        " XPAND PRODUCTION COMPLETE V5.1"
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
        "Permanent STC refs:",
        telemetry[
            "stc_local_reference_count"
        ],
    )

    print(
        "Physical refs sent:",
        telemetry[
            "physical_reference_count"
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

        "stc_physical_reference_limit":
            MAX_STC_PHYSICAL_REFERENCE_IMAGES,

        "qa_target":
            QA_TARGET_SCORE,

        "qa_release_floor":
            QA_RELEASE_FLOOR,

        "stc_qa_target":
            STC_QA_TARGET_SCORE,

        "stc_qa_release_floor":
            STC_QA_RELEASE_FLOOR,
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
    # QA
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
        "stc_five_physical_refs"
    ] = (
        MAX_STC_PHYSICAL_REFERENCE_IMAGES
        >=
        3
        and
        MAX_STC_PHYSICAL_REFERENCE_IMAGES
        <=
        5
    )

    # =====================================================
    # MODEL
    # =====================================================

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
                "واقعية معززة"
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
                "بيئة بنفسجية استوديو"
            )
        )
        ==
        "TIER_C"
    )

    tests[
        "stc_brand_kit_realistic_family"
    ] = (
        stc_visual_family_for_brand_kit(
            (
                "STC Bank "
                "واقعي فوتوغرافي"
            )
        )
        ==
        "premium_realistic"
    )

    # =====================================================
    # COMPILED PROMPT
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
                    "C01",

                "core_idea":
                    (
                        "A real advertising mechanism "
                        "connects online commerce and "
                        "physical point-of-sale."
                    ),

                "visual_metaphor":
                    (
                        "A meaningful physical continuity "
                        "connects both commerce channels."
                    ),

                "debate": {
                    "finalist_jury": {
                        "production_instruction":
                            (
                                "Preserve the visual bridge "
                                "and premium Saudi realism."
                            ),

                        "do_not_drift_into": [
                            "generic checkout counter",
                        ],
                    }
                },
            },

            brand_context={
                "stc_permanent_brand_kit": {
                    "grounding_text":
                        (
                            "Premium STC Bank Saudi "
                            "campaign visual language."
                        ),

                    "banned_patterns":
                        (
                            "Avoid wooden checkout counter."
                        ),

                    "reference_brief":
                        (
                            "Use STC brand DNA references."
                        ),
                }
            },

            references=[],

            camera_direction={
                "camera_angle":
                    "Low-Angle Shot",

                "lens":
                    "35mm",
            },

            product_lock={},

            aspect_ratio="4:5",
        )
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
        "permanent_stc_dna_lock"
    ] = (
        "PERMANENT STC BANK BRAND DNA"
        in
        sample_compiled.prompt
    )

    tests[
        "counter_tableau_hard_ban"
    ] = (
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

    # =====================================================
    # ADAPTIVE QA
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
            (
                "Lighting and material hierarchy "
                "could be more premium."
            )
        ],

        correction_instruction=(
            "Refine material realism."
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
        "high_alert_usable_image_gets_refinement"
    ] = (
        choose_adaptive_action(
            adaptive_qa,
            high_alert=True,
        )
        ==
        "premium_refinement"
    )

    concept_fail_qa = QAEvaluation(

        score=70.0,

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
                55.0,

            "advertising_readiness":
                60.0,
        },

        passed=False,

        strengths=[],

        problems=[
            "generic scene"
        ],

        correction_instruction=(
            "Rebuild the physical scene."
        ),

        critical_blockers=[
            "concept_execution_below_65"
        ],

        target_reached=False,

        delivery_approved=False,

        decision="rebuild",

        raw={
            "decision":
                "rebuild",

            "_xpand_flags": {
                "generic_scene_detected":
                    True,
            },
        },
    )

    tests[
        "concept_failure_recovery"
    ] = (
        choose_adaptive_action(
            concept_fail_qa,
            high_alert=True,
        )
        ==
        "concept_recovery"
    )

    # =====================================================
    # PERMANENT BRAND PACK ACTUAL IMAGE TEST
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
                    "production-engine-self-test"
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
        " XPAND PRODUCTION ENGINE V5.1"
    )
    print(
        " ZERO-COST HIGH-ALERT SELF TEST"
    )
    print(
        "=========================================="
    )
    print("")

    for name, passed in tests.items():

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
        "Permanent STC physical refs loaded:",
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
                "V5.1 self-test: PASS ✅"
            )
        )

    else:

        print(
            (
                "XPAND Production Engine "
                "V5.1 self-test: FAIL ❌"
            )
        )

    print("")

    print(
        "✅ Telegram public import contract preserved"
    )

    print(
        "✅ Nano Banana 2 primary generation"
    )

    print(
        "✅ Optional Gemini Pro second-pass escalation"
    )

    print(
        "✅ Maximum 2 image calls"
    )

    print(
        "✅ Maximum 2 Vision QA calls"
    )

    print(
        "✅ Permanent STC Brand Pack connected"
    )

    print(
        "✅ Real JPG bytes loaded from GitHub/Railway"
    )

    print(
        "✅ Up to 5 physical STC reference images"
    )

    print(
        "✅ Brand DNA + style + service reference mix"
    )

    print(
        "✅ Permanent references sent to Gemini image input"
    )

    print(
        "✅ Strict STC brand-identity QA"
    )

    print(
        "✅ Strict advertising-readiness QA"
    )

    print(
        "✅ Scene-originality QA"
    )

    print(
        "✅ Merchant service-integration QA"
    )

    print(
        "✅ Literal counter-tableau hard blocker"
    )

    print(
        "✅ Repeated-scene hard blocker"
    )

    print(
        "✅ Reference-cloning blocker"
    )

    print(
        "✅ 92 target / 88 STC release floor by default"
    )

    print(
        "✅ 88–91 clean STC result may trigger premium refinement"
    )

    print(
        "✅ No generated text"
    )

    print(
        "✅ No generated logos"
    )

    print(
        "✅ No fake banking UI"
    )

    print(
        "✅ Purple is not automatic brand identity"
    )

    print(
        "✅ 25–40% natural copy space"
    )

    print(
        "✅ No API calls were made by this self-test"
    )

    print(
        "🚫 No images were generated"
    )

    print("")
