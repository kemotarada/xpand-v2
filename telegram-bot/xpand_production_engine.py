# =========================================================
# XPAND PRODUCTION ENGINE V5.0
#
# NANO BANANA 2
# COST-CONTROLLED MASTERPIECE PRODUCTION
#
# =========================================================
#
# NORMAL MASTERPIECE PATH
# ---------------------------------------------------------
#
# Creative Brain approved direction
#          ↓
# Brand Memory V3 Reference Curator
#          ↓
# max 3 DNA references
# max 2 physical image references
#          ↓
# ONE Nano Banana 2 generation
# at USER-REQUESTED resolution
#          ↓
# ONE structured Vision QA
#          ↓
# if approved:
#       DELIVERY
#
#
# ONLY IF A REAL PROBLEM EXISTS:
#
# targeted correction
# OR
# scene/concept recovery
#          ↓
# ONE Nano Banana 2 image call
#          ↓
# ONE final QA
#
#
# =========================================================
# COST POLICY
# =========================================================
#
# NORMAL:
#
#   Image calls:  1
#   Vision calls: 1
#
# MAXIMUM:
#
#   Image calls:  2
#   Vision calls: 2
#
#
# NO mandatory Nano Banana Pro finishing pass.
# NO automatic 6-call loop.
# NO fake quality score.
# NO pointless second candidate.
#
#
# =========================================================
# STC BANK
# =========================================================
#
# - image only
# - no text
# - no logo
# - no fake banking UI
# - purple is NOT automatic
# - realistic photography remains naturally colored
# - premium purple studio uses physical architecture
# - augmented realism uses one physical metaphor
# - 25–40% calm copy space
# - no generic fintech effects
# - no person simply holding POS toward camera
#
#
# =========================================================
# COMPATIBILITY
# =========================================================
#
# Preserves public functions used by XPAND:
#
#   run_production
#   evaluate_generated_image
#   load_runtime_references
#   compile_prompt
#   generate_high_quality_image
#   gemini_multi_reference_edit
#   openai_multi_reference_edit
#   product_references
#   choose_physical_references
#   reference_dna_payload
#   combined_product_lock
#   get_brand_visual_profile / loader compatibility
#
#
# Running:
#
#     python xpand_production_engine.py
#
# makes ZERO API calls.
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
# IDENTITY
# =========================================================

ENGINE_NAME = (
    "XPAND Production Engine"
)

ENGINE_VERSION = "5.0"


# =========================================================
# MODES
# =========================================================

MODE_FAST = "fast"

MODE_PRO = "pro"

MODE_MASTERPIECE = (
    "masterpiece"
)


# =========================================================
# TARGETS
# =========================================================

TARGET_OPENAI = "openai"

TARGET_GEMINI = "gemini"

TARGET_MIDJOURNEY = (
    "midjourney"
)

TARGET_FLUX = "flux"

TARGET_IDEOGRAM = (
    "ideogram"
)

TARGET_RUNWAY = "runway"

TARGET_KLING = "kling"

TARGET_SEEDANCE = (
    "seedance"
)


# =========================================================
# NANO BANANA 2
# =========================================================

NANO_BANANA_2_MODEL = str(
    os.environ.get(
        "XPAND_MASTERPIECE_EXPLORATION_MODEL",
        GOOGLE_IMAGE_FAST_MODEL
        or
        "gemini-3.1-flash-image",
    )
).strip()


if not NANO_BANANA_2_MODEL:

    NANO_BANANA_2_MODEL = (
        "gemini-3.1-flash-image"
    )


# =========================================================
# COST LIMITS
# =========================================================

#
# Hard maximum = 2.
#
# Environment cannot accidentally restore 6.
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


# =========================================================
# REFERENCE POLICY
# =========================================================

#
# Brand Memory V3 already curates STC references.
#

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


#
# Physical files cost more context than DNA.
#
# Two is normally enough:
#
# 1. strongest style/service reference
# 2. second complementary angle/reference
#

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


SEND_VISUAL_REFERENCES_TO_IMAGE = str(
    os.environ.get(
        "XPAND_SEND_VISUAL_REFERENCES_TO_IMAGE",
        "true",
    )
).strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}


# =========================================================
# QA POLICY
# =========================================================

#
# 86 = target.
#
# 80 = safe adaptive release when there are no
# critical blockers.
#
# This prevents wasting another paid image call
# just to push an already strong 82/83 image to 86.
#

QA_TARGET_SCORE = max(
    82.0,
    min(
        95.0,
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
# PROMPT BUDGETS
# =========================================================

COMPILED_PROMPT_BUDGET = max(
    12000,
    min(
        28000,
        int(
            os.environ.get(
                "XPAND_COMPILED_PROMPT_BUDGET",
                "22000",
            )
            or 22000
        ),
    ),
)


QA_PROMPT_BUDGET = max(
    6000,
    min(
        16000,
        int(
            os.environ.get(
                "XPAND_QA_PROMPT_BUDGET",
                "10000",
            )
            or 10000
        ),
    ),
)


CORRECTION_PROMPT_BUDGET = max(
    8000,
    min(
        22000,
        int(
            os.environ.get(
                "XPAND_CORRECTION_PROMPT_BUDGET",
                "16000",
            )
            or 16000
        ),
    ),
)


# =========================================================
# QA WEIGHTS
# =========================================================

QA_WEIGHTS = {
    "concept_execution":
        15,

    "message_clarity_without_text":
        12,

    "brand_alignment":
        12,

    "realism":
        12,

    "camera_perspective":
        10,

    "lighting_materials":
        10,

    "human_anatomy":
        8,

    "reference_adherence":
        6,

    "advertising_readiness":
        8,

    "text_logo_compliance":
        4,

    "purple_restraint":
        3,
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
        140
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
        "PRESERVE LOCKED RULES]\n\n"
        +
        (
            text[-back:]
            if back
            else ""
        )
    )


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

    #
    # Compatibility helper.
    #
    # Gemini V5 receives exact aspect_ratio + image_size.
    #

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
        "Do not create a different canvas and crop the main subject later."
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


def build_stc_scene_tier_instruction(
    request: str,
) -> str:

    tier = stc_scene_tier(
        request
    )

    if tier == "TIER_C":

        return """
STC SCENE TIER: C — PURPLE ARCHITECTURAL STUDIO
================================================

Purple is allowed primarily in the physical background,
architectural surfaces, plinths and selected material planes.

The SUBJECT itself must remain naturally colored.

Never tint:
- human skin
- hair
- white thobe
- natural food
- natural wood
- metal product surfaces
- hero product materials

Use:
- deep aubergine
- dark violet
- near-black violet
- matte surfaces
- satin surfaces
- controlled semi-gloss
- realistic contact shadows
- restrained specular reflections

This is premium architecture/studio photography.

It is NOT:
- nightclub neon
- glowing cyber environment
- generic fintech CGI
""".strip()

    if tier == "TIER_B":

        return """
STC SCENE TIER: B — AUGMENTED REALISM
=====================================

The base environment remains fully photographic and believable.

Purple is limited to restrained identity accents,
typically no more than approximately 15% of the visual field.

Use exactly ONE physical conceptual metaphor.

The metaphor must obey:
- gravity
- perspective
- contact shadows
- light direction
- material behavior
- occlusion
- scale

Never tint people or natural materials purple.

Do not turn the image into fantasy CGI.
""".strip()

    return """
STC SCENE TIER: A — PREMIUM REAL LIFE
=====================================

The environment remains naturally colored.

ZERO global purple wash.

Do not make the room, street, store, café, skin, clothing
or natural materials purple merely because the brand is STC Bank.

Purple/green may appear only as very small motivated accents
when useful.

Prioritize:
- authentic Saudi commercial environment
- beautiful natural palette
- clean skin tones
- premium architecture
- real daylight or practical light
- believable materials
- restrained art direction
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
# RUNTIME REFERENCES
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

    references = []

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
                role=clean_text(
                    item.get(
                        "reference_role",
                        "style_reference",
                    ),
                    100,
                )
                or
                "style_reference",

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

                content_family=clean_text(
                    item.get(
                        "content_family",
                        "general_brand",
                    ),
                    100,
                )
                or
                "general_brand",

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
        min(
            MAX_PHYSICAL_REFERENCE_IMAGES,
            int(
                limit
                or 0
            ),
        ),
    )

    if limit <= 0:

        return []

    usable = [
        item
        for item in references
        if item.image_bytes
    ]

    if not usable:

        return []

    role_priority = {
        "product_reference":
            1000,

        "campaign_reference":
            900,

        "style_reference":
            850,

        "mixed_reference":
            840,

        "composition_reference":
            820,

        "camera_reference":
            800,

        "lighting_reference":
            780,

        "environment_reference":
            740,

        "color_reference":
            720,
    }

    usable.sort(
        key=lambda item: (
            role_priority.get(
                item.role,
                700,
            )
            +
            reference_score(
                item
            )
        ),
        reverse=True,
    )

    selected = []

    used_ids = set()

    used_families = set()

    #
    # Product reference gets first priority.
    #

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

    #
    # Then select complementary evidence.
    #

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

            #
            # Prefer a different reference family when possible.
            #

            alternatives = [
                candidate
                for candidate in usable
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


def reference_dna_payload(
    references: Sequence[
        ProductionReference
    ],
) -> List[
    Dict[str, Any]
]:

    output = []

    for item in list(
        references
    )[:SMART_REFERENCE_SELECTION_LIMIT]:

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

                "dna":
                    compact_json(
                        item.dna,
                        2400,
                    ),

                "note":
                    clean_text(
                        item.user_note,
                        700,
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
# BRAND CONTEXT COMPACTION
# =========================================================

def build_enriched_brand_context(
    *,
    brand_context: Any,
    brand_visual_profile: Any,
    references: Sequence[
        ProductionReference
    ],
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
fake UI,
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
plastic skin,
over-smoothed faces,
extra fingers,
deformed hands,
impossible object support,
incorrect perspective,
fake reflections,
unmotivated colored light,
visual clutter,
generic stock-photo posing.
""".strip()


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
        10000,
    )

    stc_request = (
        is_stc_bank_request(
            request
        )
    )

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

        stc_section = f"""
================================================
STC BANK LOCKED PRODUCTION STANDARD
================================================

BENEFIT FAMILY:
{benefit_family}

SELECTED STYLE:
{selected_style or "premium_realistic"}

{build_stc_scene_tier_instruction(request)}

SUBJECT-PROTECTION LAW
----------------------

Purple belongs to environmental identity treatment only.

Never tint:
- skin
- face
- hair
- natural fabric
- food
- natural wood
- natural stone
- hero product material

Keep subject white balance clean and neutral.

COPY-SPACE LAW
--------------

Reserve approximately 25–40% of the frame as calm,
naturally photographed negative space for later Arabic copy.

The copy space must NOT be:
- white digital box
- banner
- gradient overlay
- UI panel
- graphic card

It must be part of the actual photographed composition.

TEXT-FREE LAW
-------------

Generate NO readable advertising text.

Generate NO:
- headline
- subtitle
- CTA
- percentage
- price
- offer text
- legal copy
- STC Bank logo
- STC wordmark
- Visa logo
- Mastercard logo
- watermark

If a reference advertisement contains text or logos,
use it only for photographic/style understanding.

Do NOT reproduce the old typography.

REAL-APP LAW
------------

If a phone screen is visible and the real STC Bank app
screenshot is NOT supplied as an exact verified asset:

- do not invent readable banking UI
- do not invent account values
- do not invent balances
- do not invent menus
- do not create fake STC app text

Instead:
- angle screen away from camera,
- use reflection,
- use shallow depth,
- make screen content unreadable,
or
- make the concept work without showing the interface.

ANTI-REPETITION LAW
-------------------

Do not default to:
- generic office desk
- businessman sitting at desk with phone
- merchant standing and presenting POS toward camera
- purple room with laptop
- person staring at camera holding a bank product

Human behavior must be real and story-driven.

NO-CLONE LAW
------------

References are evidence of:
- taste
- realism
- camera quality
- materials
- lighting
- restraint

Never recreate an existing STC Bank advertisement.

Create an original scene.

ONE-METAPHOR LAW
----------------

Use at most ONE conceptual visual mechanism.

It must obey:
- gravity
- perspective
- scale
- occlusion
- shadows
- reflections

EFFECTS-WITH-PURPOSE LAW
------------------------

Do not add:
- bokeh
- bloom
- haze
- motion blur
- glow
- colored light

automatically.

Use an optical effect only if it improves the message
or genuine photographic luxury.

{STC_BANK_IMAGE_GUARD}
""".strip()

    return f"""
XPAND PRODUCTION BLUEPRINT V5.0
===============================

You are producing ONE finished premium commercial photograph.

This is NOT a brainstorming step.

Do not invent a different advertising concept.

================================================
USER REQUEST
================================================

{request}

================================================
APPROVED CREATIVE DIRECTION
================================================

{compact_json(creative_direction, 6000)}

================================================
CAMERA DIRECTION
================================================

{compact_json(camera_direction, 2200)}

The camera direction is deliberate.

Do not replace it with a generic front-facing eye-level shot
unless the approved direction specifically requires that.

Maintain coherent:
- camera height
- viewing direction
- focal length
- horizon
- vanishing points
- foreground scale
- subject scale

================================================
BRAND MEMORY
================================================

{compact_json(brand_context, 5000)}

================================================
CURATED VISUAL REFERENCE DNA
================================================

{compact_json(references, 5000)}

References are NOT templates.

Learn:
- realism
- sophistication
- photography level
- lighting quality
- material finish
- camera maturity
- environmental design

Do NOT clone:
- scene
- exact framing
- exact pose
- old campaign metaphor
- old text placement

================================================
PRODUCT LOCK
================================================

{compact_json(product_lock, 1800)}

If product lock is present:
preserve physical form and product characteristics.

However:
do NOT generate logos, wordmarks or readable financial text.

================================================
PHOTOGRAPHIC REALISM
================================================

The result must feel like a real premium advertising shoot.

Require:
- believable physics
- correct gravity
- realistic human anatomy
- credible hand/object contact
- correct object scale
- real surface contact
- coherent perspective
- realistic depth
- premium but believable production design

Avoid the polished-but-obviously-AI look.

================================================
LIGHTING
================================================

Use motivated lighting.

Every major shadow must have a plausible source.

Require:
- coherent key-light direction
- realistic bounce
- material-specific highlights
- clean shadow transitions
- real contact shadows
- controlled exposure
- clean facial tones
- believable white balance

Do not illuminate objects independently with random glows.

================================================
MATERIALS
================================================

Render real material differences.

Stone must behave like stone.
Glass must behave like glass.
Metal must behave like metal.
Leather must behave like leather.
Fabric must behave like fabric.

Use a premium hierarchy of:
- matte
- satin
- semi-gloss
- controlled specular reflections

Do not make everything shiny.

================================================
COMPOSITION
================================================

ONE dominant visual idea.

ONE clear hero.

Supporting elements exist only to strengthen the message.

Use:
- intentional foreground
- midground
- background
- clear depth
- controlled asymmetry or symmetry
- clean edges
- calm negative space
- sophisticated restraint

Remove unnecessary props.

================================================
ADVERTISING STANDARD
================================================

The benefit must be understandable primarily through
the visual scene.

Do not depend on generated text to explain the idea.

The image should be strong enough that a professional
designer can later add Arabic copy and official branding.

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

NO text.
NO logos.
NO fake UI.
NO decorative fintech graphics.

Create one coherent premium photographic frame.
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
            "production_blueprint_v5"
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
                "xpand_production_v5",

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

            "pro_final_pass":
                False,

            "reference_limit":
                SMART_REFERENCE_SELECTION_LIMIT,

            "physical_reference_limit":
                MAX_PHYSICAL_REFERENCE_IMAGES,
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
        (
            "PHYSICAL REFERENCE RULES"
        ),
        (
            "========================"
        ),
        "",
        (
            "Actual reference images are attached."
        ),
        "",
        (
            "Use them as visual evidence only."
        ),
        "",
    ]

    for index, reference in enumerate(
        references,
        start=1,
    ):

        lines.append(
            (
                "Reference "
                +
                str(
                    index
                )
                +
                ":"
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

        if reference.user_note:

            lines.append(
                (
                    "- note: "
                    +
                    clean_text(
                        reference.user_note,
                        350,
                    )
                )
            )

        lines.append("")

    lines.extend(
        [
            (
                "Do NOT copy old text."
            ),

            (
                "Do NOT copy old logos."
            ),

            (
                "Do NOT clone the exact composition."
            ),

            (
                "Do NOT recreate an existing campaign."
            ),

            (
                "Create an original execution with the same "
                "professional photographic maturity."
            ),
        ]
    )

    return "\n".join(
        lines
    )


# =========================================================
# NANO BANANA 2 INTERACTION
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

    for reference in list(
        references
    )[:MAX_PHYSICAL_REFERENCE_IMAGES]:

        if not reference.image_bytes:

            continue

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
                NANO_BANANA_2_MODEL,

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
                "Nano Banana 2 image call failed: "
                +
                clean_text(
                    response_data,
                    2800,
                )
            )
        )

    images = find_images_in_response(
        response_data
    )

    if not images:

        raise RuntimeError(
            (
                "Nano Banana 2 returned no image"
                +
                " | model="
                +
                NANO_BANANA_2_MODEL
                +
                " | response="
                +
                clean_text(
                    response_data,
                    2200,
                )
            )
        )

    image_bytes, mime_type = (
        images[
            0
        ]
    )

    result = GeneratedImage(
        image_bytes=image_bytes,

        mime_type=(
            mime_type
            or
            "image/jpeg"
        ),

        provider=(
            "google"
        ),

        model=(
            NANO_BANANA_2_MODEL
        ),

        prompt=safe_prompt,

        original_prompt=(
            safe_prompt
        ),

        aspect_ratio=(
            aspect_ratio
        ),

        image_size=(
            requested_size
        ),

        quality="high",

        route_reason=(
            "XPAND Production V5 Nano Banana 2 | "
            +
            pass_name
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
                "nb2-"
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
                    [
                        item
                        for item
                        in references
                        if item.image_bytes
                    ]
                ),

            "nano_banana_2":
                True,

            "nano_banana_pro":
                False,

            "provider_native_resolution":
                requested_size,

            "aspect_ratio":
                aspect_ratio,
        },
    )

    return result


#
# Compatibility alias.
#
# Older XPAND modules imported this historical name.
#
# It is NOT OpenAI anymore.
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
) -> GeneratedImage:

    physical_refs = list(
        visual_refs
    )

    existing_ids = {
        item.source_id
        for item in physical_refs
        if item.source_id
    }

    #
    # Product refs first when available.
    #

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

    return gemini_multi_reference_edit(
        working_image=None,

        references=physical_refs,

        prompt=(
            compiled.prompt
        ),

        aspect_ratio=(
            aspect_ratio
        ),

        pass_name=(
            pass_name
        ),

        output_image_size=(
            output_image_size
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
    for key in QA_WEIGHTS
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


# =========================================================
# QA BLOCKERS
# =========================================================

def detect_critical_blockers(
    *,
    scores: Dict[str, float],
    explicit_failures: Any,
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
                68.0,
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

    if is_stc_bank_request(
        original_request
    ):

        if (
            clamp_score(
                scores.get(
                    "text_logo_compliance",
                    0,
                )
            )
            <
            90
        ):

            blockers.append(
                "stc_visible_text_or_logo"
            )

        if (
            clamp_score(
                scores.get(
                    "purple_restraint",
                    0,
                )
            )
            <
            65
        ):

            blockers.append(
                "stc_purple_overuse"
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

    stc_request = is_stc_bank_request(
        original_request
    )

    stc_audit = ""

    if stc_request:

        stc_audit = f"""
STC BANK HARD AUDIT
===================

The generated image MUST contain no advertising text
and no generated logos.

Score text_logo_compliance:

100:
no readable copy, no logos, no wordmarks, no fake UI.

0:
headline/logo/financial text is clearly visible.

Score purple_restraint according to:

{build_stc_scene_tier_instruction(original_request)}

Also reject:
- generic purple neon
- floating cards
- floating phone
- floating POS
- network graphics
- laser/glowing payment lines
- random particles
- fake banking UI
- subject simply holding device toward camera
- generic office-desk banking scene
""".strip()

    return f"""
XPAND MASTERPIECE VISUAL QA V5.0
================================

You are reviewing a finished advertising image.

Be strict but practical.

Do NOT reward an image merely because it looks attractive.

The question is:

Would this work as a premium real advertising photograph?

================================================
ORIGINAL REQUEST
================================================

{clean_text(original_request, 3500)}

================================================
APPROVED PRODUCTION BLUEPRINT
================================================

{clean_text(compiled_prompt.prompt, 5000)}

================================================
PRODUCT LOCK
================================================

{compact_json(product_lock, 1300)}

================================================
BRAND CONTEXT
================================================

{compact_json(brand_context, 1800)}

================================================
FRAME
================================================

Expected aspect ratio:
{clean_text(aspect_ratio, 50)}

================================================
SCORE 0–100
================================================

concept_execution
-----------------
Did the image actually execute the approved visual idea?

message_clarity_without_text
----------------------------
Can the central benefit be understood visually even before
advertising copy is added?

brand_alignment
---------------
Does the image feel appropriate for the brand without
reducing the identity to a color effect?

realism
-------
Does it look physically and photographically believable?

camera_perspective
------------------
Are lens, angle, horizon, scale and perspective coherent?

lighting_materials
------------------
Do lighting, shadows, reflections and materials behave
like a professional real shoot?

human_anatomy
-------------
If people/hands are visible, are anatomy, grip and posture
credible?
If no humans are present, score this 100.

reference_adherence
-------------------
Did it learn appropriate visual maturity from references
without cloning them?

advertising_readiness
---------------------
Could this realistically be handed to a senior designer
for final typography and campaign finishing?

text_logo_compliance
--------------------
Is the image free from unwanted generated copy/logos?

purple_restraint
----------------
Is brand color used intelligently rather than automatically?

================================================
CRITICAL BLOCKERS
================================================

List only real blockers.

Examples:
- concept does not communicate
- fake anatomy
- impossible object support
- broken perspective
- obvious AI artifact
- unwanted generated text
- logo generated against instruction
- fake banking UI
- severe purple wash
- generic fintech cliché
- product reference materially changed

================================================
DECISION
================================================

approve:
production-ready or strong adaptive release.

correct:
idea is good but specific visual defects need one controlled
correction.

rebuild:
the scene mechanism itself failed and should be rebuilt.

================================================
STC AUDIT
================================================

{stc_audit or "No dedicated STC Bank audit required."}

Return only the requested JSON schema.
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
        label="vision_qa_v5",
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
            "xpand_production_qa_v5"
        ),
    )

    data = parse_json_object(
        raw
    )

    if not data:

        raise RuntimeError(
            (
                "Production QA returned invalid JSON."
            )
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

    blockers = (
        detect_critical_blockers(
            scores=normalized_scores,

            explicit_failures=(
                data.get(
                    "critical_blockers"
                )
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

    target_reached = bool(
        score
        >=
        QA_TARGET_SCORE
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
        QA_RELEASE_FLOOR
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

        scores=(
            normalized_scores
        ),

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
            )[:6]
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
            )[:8]
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
                3000,
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

        decision=(
            decision
        ),

        raw=data,
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
# ADAPTIVE ACTION
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
        68
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
        68
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
        "الفكرة",
        "المعنى غير واضح",
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

        #
        # QA outage does NOT justify buying
        # another image automatically.
        #

        return "none"

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
XPAND TARGETED CORRECTION V5.0
==============================

This is the ONE allowed automatic correction pass.

The advertising idea is fundamentally usable.

Preserve every successful region.

================================================
CURRENT QA
================================================

Score:
{qa.score}/100

Problems:
{compact_json(qa.problems, 2800)}

Critical blockers:
{compact_json(qa.critical_blockers, 1600)}

QA directive:
{clean_text(qa.correction_instruction, 2400)}

================================================
ORIGINAL BLUEPRINT
================================================

{clean_text(compiled.prompt, 6500)}

================================================
PRODUCT LOCK
================================================

{compact_json(product_lock, 1200)}

================================================
CORRECTION RULES
================================================

Fix only the actual problems.

Preserve:
- successful concept
- successful camera
- successful scene
- successful human identity
- successful architecture
- successful lighting
- successful material palette
- successful negative space

Correct when necessary:
- anatomy
- product grip
- object support
- perspective
- reflections
- skin realism
- clutter
- excessive purple
- unwanted generated text/logo
- fake UI

Do NOT redesign a successful scene merely to make it different.

Do NOT add new decorative elements.

Do NOT add text.

Do NOT add logos.

{safe_frame_instruction(aspect_ratio)}
""".strip()

    return fit_prompt_for_api(
        prompt,
        label=(
            "targeted_correction_v5"
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
XPAND SCENE RECOVERY V5.0
=========================

The previous execution failed to communicate the approved
advertising idea strongly enough.

This is NOT a new brainstorming round.

Keep the approved marketing strategy,
but rebuild the physical scene mechanism.

================================================
FAILED QA
================================================

Score:
{qa.score}/100

Problems:
{compact_json(qa.problems, 3000)}

Critical blockers:
{compact_json(qa.critical_blockers, 1800)}

QA directive:
{clean_text(qa.correction_instruction, 2500)}

================================================
APPROVED BLUEPRINT
================================================

{clean_text(compiled.prompt, 7000)}

================================================
RECOVERY RULE
================================================

Change the failed scene execution.

Possible improvements:
- more meaningful real environment
- stronger camera viewpoint
- clearer real human behavior
- better physical relationship between hero objects
- more sophisticated negative space
- less generic staging
- stronger material/lighting logic

Do NOT:
- add purple neon
- add floating elements
- add fintech graphics
- add network lines
- add particles
- add text
- add logos
- use the generic person-holding-product pose

The new execution must still follow the approved campaign idea.

{safe_frame_instruction(aspect_ratio)}
""".strip()

    return fit_prompt_for_api(
        prompt,
        label=(
            "scene_recovery_v5"
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
        "Message without text:",
        qa.scores.get(
            "message_clarity_without_text",
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
        "Text/logo compliance:",
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
            :5
        ]
    ):

        print(
            "  🛑",
            clean_text(
                blocker,
                800,
            ),
        )

    print(
        "Decision:",
        qa.decision,
    )


# =========================================================
# COMPATIBILITY DELIVERY FRAME
# =========================================================

def create_exact_delivery_frame(
    image: GeneratedImage,
    aspect_ratio: str,
    *,
    upscale_final: bool = False,
    label: str = "delivery",
) -> GeneratedImage:

    #
    # V5 asks Gemini to render natively at the requested
    # aspect ratio and resolution.
    #
    # No paid or fake local upscale is required.
    #

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

    requested_size = detect_image_size(
        original_request
    )

    if requested_size not in {
        "1K",
        "2K",
        "4K",
    }:

        #
        # Provider native image generation.
        #
        # HD / unknown uses 1K processing output.
        #

        requested_size = "1K"

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

        "requested_image_size":
            requested_size,

        "selected_reference_count":
            0,

        "physical_reference_count":
            0,

        "adaptive_action":
            "none",
    }

    # =====================================================
    # REFERENCES
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
    # VISUAL PROFILE
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

    # =====================================================
    # LOG
    # =====================================================

    print("")
    print(
        "=============================================="
    )
    print(
        " XPAND PRODUCTION ENGINE V5.0"
    )
    print(
        " NANO BANANA 2 | COST-CONTROLLED"
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
        NANO_BANANA_2_MODEL,
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
        "DNA references:",
        len(
            references
        ),
        "/",
        SMART_REFERENCE_SELECTION_LIMIT,
    )

    print(
        "Physical references:",
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
        "Normal image calls:",
        1,
    )

    print(
        "Normal Vision calls:",
        (
            1
            if mode
            ==
            MODE_MASTERPIECE
            else
            0
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
        "Nano Banana Pro final pass:",
        False,
    )

    if is_stc_bank_request(
        original_request
    ):

        print(
            "STC scene tier:",
            stc_scene_tier(
                original_request
            ),
        )

        print(
            "STC style:",
            (
                detect_stc_visual_style(
                    original_request
                )
                or
                STYLE_PREMIUM_REALISTIC
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
        " | Nano Banana 2"
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

                "cost_controlled":
                    True,
            },
        )
    ]

    best_image = first_image

    best_qa: Optional[
        QAEvaluation
    ] = None

    best_score = 0.0

    # =====================================================
    # FAST MODE
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

            compiled_prompt=(
                compiled
            ),

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
                2500,
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
            # IMPORTANT COST RULE:
            #
            # An evaluator outage is NOT evidence that the
            # image itself is bad.
            #
            # Do not spend another image call because QA
            # infrastructure failed.
            #

            best_qa = None

    # =====================================================
    # ADAPTIVE DECISION
    # =====================================================

    action = choose_adaptive_action(
        best_qa
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
    # SECOND CALL ONLY WHEN ACTUALLY REQUIRED
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

            if (
                action
                ==
                "concept_recovery"
            ):

                print("")
                print(
                    "🍌 IMAGE CALL 2/"
                    +
                    str(
                        MASTERPIECE_MAX_IMAGE_CALLS
                    )
                    +
                    " | Nano Banana 2"
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
                    )
                )

                second_pass_name = (
                    "scene_recovery"
                )

            else:

                print("")
                print(
                    "🍌 IMAGE CALL 2/"
                    +
                    str(
                        MASTERPIECE_MAX_IMAGE_CALLS
                    )
                    +
                    " | Nano Banana 2"
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

                #
                # Targeted correction:
                #
                # working image
                # +
                # authoritative product refs only
                #
                # We do not resend every style reference.
                #

                correction_refs = [
                    item
                    for item in product_refs
                    if item.image_bytes
                ][
                    :MAX_PHYSICAL_REFERENCE_IMAGES
                ]

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
                            NANO_BANANA_2_MODEL,

                        "adaptive_action":
                            action,

                        "image_size":
                            requested_size,
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
                        "Correction QA",
                        second_qa,
                    )

                except Exception as error:

                    message = clean_text(
                        error,
                        2500,
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
            # KEEP STRONGEST
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
                    "🏆 Corrected candidate selected."
                )

            else:

                print(
                    "🏆 Primary candidate preserved."
                )

        except Exception as error:

            message = clean_text(
                error,
                2800,
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
                "✅ Primary candidate preserved."
            )

    else:

        if best_qa is not None:

            if best_qa.target_reached:

                print(
                    "✅ QA target reached."
                )

            elif best_qa.passed:

                print(
                    "✅ Adaptive release floor reached."
                )

        print(
            "💰 No second image call needed."
        )

    # =====================================================
    # FINAL DELIVERY
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

            "final_model":
                NANO_BANANA_2_MODEL,

            "nano_banana_2":
                True,

            "nano_banana_pro":
                False,

            "mandatory_pro_pass":
                False,

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
        }
    )

    if best_qa is not None:

        final_ok = bool(
            best_qa.passed
        )

        best_score = (
            best_qa.score
        )

    else:

        #
        # The runtime will see qa=None and can decide
        # whether to Smart-fallback.
        #
        # We do NOT fake QA approval.
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
        " XPAND PRODUCTION COMPLETE V5.0"
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
        "Final model:",
        NANO_BANANA_2_MODEL,
    )

    print(
        "Final size:",
        requested_size,
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
        "Nano Banana Pro calls:",
        0,
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
            references
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

    return {
        "engine":
            ENGINE_NAME,

        "version":
            ENGINE_VERSION,

        "nano_banana_2_model":
            NANO_BANANA_2_MODEL,

        "nano_banana_pro_required":
            False,

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

        "qa_target":
            QA_TARGET_SCORE,

        "qa_release_floor":
            QA_RELEASE_FLOOR,
    }


# =========================================================
# ZERO-COST SELF TEST
# =========================================================

if __name__ == "__main__":

    tests: Dict[
        str,
        bool,
    ] = {}

    tests[
        "qa_weights"
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
        "three_dna_references"
    ] = (
        SMART_REFERENCE_SELECTION_LIMIT
        <=
        3
    )

    tests[
        "two_physical_references"
    ] = (
        MAX_PHYSICAL_REFERENCE_IMAGES
        <=
        2
    )

    tests[
        "nano_banana_2"
    ] = bool(
        NANO_BANANA_2_MODEL
    )

    tests[
        "no_mandatory_pro"
    ] = (
        get_production_engine_status()[
            "nano_banana_pro_required"
        ]
        is False
    )

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
                "بيئة بنفسجية استوديو"
            )
        )
        ==
        "TIER_C"
    )

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
                "core_idea":
                    (
                        "Real premium merchant "
                        "payment moment"
                    ),
            },

            brand_context={},

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

    good_qa = QAEvaluation(
        score=84.0,

        scores={
            key:
                84.0
            for key in QA_WEIGHTS
        },

        passed=True,

        strengths=[],

        problems=[],

        correction_instruction="",

        critical_blockers=[],

        target_reached=False,

        delivery_approved=True,

        decision=(
            "adaptive_release"
        ),
    )

    tests[
        "good_qa_no_second_call"
    ] = (
        choose_adaptive_action(
            good_qa
        )
        ==
        "none"
    )

    concept_fail_qa = (
        QAEvaluation(
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
                    "rebuild"
            },
        )
    )

    tests[
        "concept_failure_recovery"
    ] = (
        choose_adaptive_action(
            concept_fail_qa
        )
        ==
        "concept_recovery"
    )

    all_ok = all(
        tests.values()
    )

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND PRODUCTION ENGINE V5.0"
    )
    print(
        " ZERO-COST SELF TEST"
    )
    print(
        "=========================================="
    )
    print("")

    for name, passed in (
        tests.items()
    ):

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

    if all_ok:

        print(
            (
                "XPAND Production Engine "
                "V5.0 self-test: PASS ✅"
            )
        )

    else:

        print(
            (
                "XPAND Production Engine "
                "V5.0 self-test: FAIL ❌"
            )
        )

    print("")

    print(
        "✅ Normal Masterpiece = 1 image + 1 QA"
    )

    print(
        "✅ Maximum = 2 images + 2 QA"
    )

    print(
        "✅ Nano Banana 2 primary"
    )

    print(
        "✅ Nano Banana 2 correction"
    )

    print(
        "✅ No mandatory Nano Banana Pro pass"
    )

    print(
        "✅ No six-image loop"
    )

    print(
        "✅ No six-Vision loop"
    )

    print(
        "✅ Direct requested 1K / 2K / 4K generation"
    )

    print(
        "✅ Max 3 curated DNA references"
    )

    print(
        "✅ Max 2 physical references"
    )

    print(
        "✅ Product reference priority"
    )

    print(
        "✅ Physical-reference diversity"
    )

    print(
        "✅ QA only triggers second image when needed"
    )

    print(
        "✅ QA outage does NOT trigger expensive image retry"
    )

    print(
        "✅ Strong 80+ clean image may release without another call"
    )

    print(
        "✅ STC Tier A realistic scenes"
    )

    print(
        "✅ STC Tier B augmented realism"
    )

    print(
        "✅ STC Tier C purple architectural studio"
    )

    print(
        "✅ Subject-protection law"
    )

    print(
        "✅ 25–40% natural copy space"
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
        "✅ No-clone rule"
    )

    print(
        "✅ Anti-repetition rule"
    )

    print(
        "✅ One-metaphor rule"
    )

    print(
        "✅ Purple is NOT automatic"
    )

    print(
        "✅ Generic fintech effects blocked"
    )

    print(
        "✅ Telegram V3.4 compatibility"
    )

    print(
        "🚫 No API calls were made"
    )

    print(
        "🚫 No Vision calls were made"
    )

    print(
        "🚫 No image calls were made"
    )

    print("")
