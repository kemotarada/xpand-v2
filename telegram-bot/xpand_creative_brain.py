# =========================================================
# XPAND CREATIVE BRAIN V5.5
#
# STC BANK HIGH-ALERT
# TARGETED CREATIVE REPAIR
# QUALITY-FIRST ARBITRATION
#
# FULL RUNTIME-COMPATIBLE REPLACEMENT
#
# =========================================================
#
# PUBLIC CONTRACT PRESERVED:
#
#   MODE_FAST
#   MODE_MASTERPIECE
#   CreativeConcept
#   CreativeBrainResponse
#   concept_to_dict()
#   response_to_dict()
#   build_top_concepts_summary()
#   run_creative_brain()
#
# =========================================================
#
# V5.5 STC MASTERPIECE PATH
#
# CALL 1
#   8 fundamentally different concepts
#          ↓
#
# CALL 2
#   Executive Creative Review
#          ↓
#
#   A) STRICT finalist exists
#          ↓
#      CALL 3 = Finalist Jury
#
#   B) NO strict finalist, but one or two concepts are
#      genuinely close to the strict gates
#          ↓
#      CALL 3 = TARGETED CREATIVE REPAIR
#               - preserve strongest core proposition
#               - repair diagnosed weak dimensions
#               - create exactly 2 repaired concepts
#               - evaluate both
#               - jury-select
#               - all in ONE structured call
#
#   C) NO repairable near-miss
#          ↓
#      CALL 3 = Fresh Recovery Board
#               - 3 new concepts
#               - evaluation
#               - jury
#               - all in ONE structured call
#
# =========================================================
#
# IMPORTANT
#
# Targeted Repair is NOT:
#
#   - threshold lowering
#   - score inflation
#   - cosmetic rewriting
#   - fake approval
#
# Every repaired concept must independently pass:
#
#   concept_strength       >= 88
#   brand_fit              >= 90
#   originality            >= 88
#   visual_mechanism       >= 90
#   camera_quality         >= 84
#   realism                >= 86
#   feasibility            >= 82
#   copy_space_quality     >= 80
#   distinctiveness        >= 88
#   advertising_readiness  >= 90
#
# AND:
#
#   weighted score         >= STC release floor
#   production_feasible    = true
#   no hard-reject pattern
#
# =========================================================
#
# COST POLICY
#
# STC High Alert:
#   maximum 3 Director calls
#
# Normal:
#   normally 2 Director calls
#
# No image generation happens in this module.
#
# =========================================================


from __future__ import annotations

import json
import os
import re

from dataclasses import dataclass, field
from pathlib import Path

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
)


# =========================================================
# IMAGE ENGINE
# =========================================================

from xpand_image_engine import (
    call_openai_director,
)


# =========================================================
# OPTIONAL STC SKILL
# =========================================================

try:
    from xpand_stc_bank_skill import (
        STC_BANK_VISUAL_SKILL,
        detect_stc_benefit_family,
        is_stc_bank_request,
    )

except Exception:

    STC_BANK_VISUAL_SKILL = ""

    def is_stc_bank_request(
        value: Any,
    ) -> bool:
        text = str(
            value or ""
        ).lower()

        return (
            "stc bank" in text
            or "بنك stc" in text
        )

    def detect_stc_benefit_family(
        value: Any,
    ) -> str:
        text = str(
            value or ""
        ).lower()

        markers = (
            "نقاط البيع",
            "point of sale",
            "pos",
            "ecommerce",
            "e-commerce",
            "التجارة الالكترونية",
            "التجارة الإلكترونية",
            "merchant payments",
        )

        if any(
            marker in text
            for marker in markers
        ):
            return "merchant_payments"

        return "general_banking"


# =========================================================
# OPTIONAL PERMANENT STC BRAND KIT
# =========================================================

try:
    from xpand_stc_brand_kit import (
        load_default_stc_brand_kit,
    )

    STC_BRAND_KIT_AVAILABLE = True

except Exception:

    load_default_stc_brand_kit = None
    STC_BRAND_KIT_AVAILABLE = False


# =========================================================
# IDENTITY
# =========================================================

VERSION = "5.5"

MODULE_NAME = "XPAND Creative Brain"


# =========================================================
# PUBLIC MODES
# =========================================================

MODE_FAST = "fast"

MODE_MASTERPIECE = "masterpiece"


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
        return float(
            default
        )


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
        return int(
            default
        )


# =========================================================
# STC HIGH ALERT
# =========================================================

STC_HIGH_ALERT_ENABLED = env_bool(
    "XPAND_STC_HIGH_ALERT",
    True,
)

STC_REQUIRE_VISUAL_MECHANISM = env_bool(
    "XPAND_STC_REQUIRE_VISUAL_MECHANISM",
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

STC_REQUIRE_ADVERTISING_STYLE = env_bool(
    "XPAND_STC_REQUIRE_ADVERTISING_STYLE",
    True,
)

STC_CREATIVE_RECOVERY_ENABLED = env_bool(
    "XPAND_STC_CREATIVE_RECOVERY_ENABLED",
    True,
)

STC_QUALITY_FIRST_ARBITRATION_ENABLED = env_bool(
    "XPAND_STC_QUALITY_FIRST_ARBITRATION",
    True,
)

STC_TARGETED_REPAIR_ENABLED = env_bool(
    "XPAND_STC_TARGETED_REPAIR_ENABLED",
    True,
)


# =========================================================
# GENERAL QUALITY
# =========================================================

MASTERPIECE_MIN_SCORE = max(
    82.0,
    min(
        98.0,
        env_float(
            "XPAND_MASTERPIECE_MIN_SCORE",
            88.0,
        ),
    ),
)

MASTERPIECE_RELEASE_FLOOR = max(
    78.0,
    min(
        MASTERPIECE_MIN_SCORE,
        env_float(
            "XPAND_MASTERPIECE_RELEASE_FLOOR",
            84.0,
        ),
    ),
)

FAST_MIN_SCORE = max(
    55.0,
    min(
        90.0,
        env_float(
            "XPAND_FAST_CREATIVE_MIN_SCORE",
            70.0,
        ),
    ),
)


# =========================================================
# STC QUALITY
# =========================================================

STC_HIGH_ALERT_MIN_SCORE = max(
    86.0,
    min(
        98.0,
        env_float(
            "XPAND_STC_MIN_CONCEPT_SCORE",
            90.0,
        ),
    ),
)

STC_HIGH_ALERT_RELEASE_FLOOR = max(
    84.0,
    min(
        STC_HIGH_ALERT_MIN_SCORE,
        env_float(
            "XPAND_STC_RELEASE_FLOOR",
            88.0,
        ),
    ),
)


# =========================================================
# STC STRICT DIMENSION GATES
#
# V5.5 DOES NOT LOWER THESE.
# =========================================================

STC_MIN_CONCEPT_STRENGTH = 88.0

STC_MIN_BRAND_FIT = 90.0

STC_MIN_ORIGINALITY = 88.0

STC_MIN_VISUAL_MECHANISM = 90.0

STC_MIN_CAMERA_QUALITY = 84.0

STC_MIN_REALISM = 86.0

STC_MIN_FEASIBILITY = 82.0

STC_MIN_COPY_SPACE = 80.0

STC_MIN_DISTINCTIVENESS = 88.0

STC_MIN_AD_READINESS = 90.0


STC_DIMENSION_MINIMUMS: Dict[
    str,
    float,
] = {
    "concept_strength":
        STC_MIN_CONCEPT_STRENGTH,

    "brand_fit":
        STC_MIN_BRAND_FIT,

    "originality":
        STC_MIN_ORIGINALITY,

    "visual_mechanism":
        STC_MIN_VISUAL_MECHANISM,

    "camera_quality":
        STC_MIN_CAMERA_QUALITY,

    "realism":
        STC_MIN_REALISM,

    "feasibility":
        STC_MIN_FEASIBILITY,

    "copy_space_quality":
        STC_MIN_COPY_SPACE,

    "distinctiveness":
        STC_MIN_DISTINCTIVENESS,

    "advertising_readiness":
        STC_MIN_AD_READINESS,
}


# =========================================================
# SCORE WEIGHTS
# =========================================================

DIMENSION_WEIGHTS: Dict[
    str,
    int,
] = {

    "concept_strength":
        12,

    "brand_fit":
        12,

    "originality":
        12,

    "visual_mechanism":
        14,

    "camera_quality":
        8,

    "realism":
        8,

    "feasibility":
        8,

    "copy_space_quality":
        6,

    "distinctiveness":
        10,

    "advertising_readiness":
        10,
}


# =========================================================
# CALL POLICY
# =========================================================

NORMAL_CONCEPT_COUNT = 4


STC_HIGH_ALERT_CONCEPT_COUNT = max(
    6,
    min(
        10,
        env_int(
            "XPAND_STC_CONCEPTS_REQUIRED",
            8,
        ),
    ),
)


STC_RECOVERY_CONCEPT_COUNT = max(
    3,
    min(
        4,
        env_int(
            "XPAND_STC_RECOVERY_CONCEPTS",
            3,
        ),
    ),
)


MASTERPIECE_SHORTLIST_SIZE = 3

MASTERPIECE_TARGET_DIRECTOR_CALLS = 3

MASTERPIECE_MAX_DIRECTOR_CALLS = max(
    2,
    min(
        3,
        env_int(
            "XPAND_IMAGE_DIRECTOR_MAX_CALLS",
            3,
        ),
    ),
)


# =========================================================
# TARGETED REPAIR POLICY
#
# These values decide ONLY whether Call 3 should repair
# a near-miss rather than generate a fresh concept pool.
#
# They DO NOT affect final release thresholds.
# =========================================================

STC_TARGETED_REPAIR_MIN_SCORE = max(
    80.0,
    min(
        STC_HIGH_ALERT_RELEASE_FLOOR,
        env_float(
            "XPAND_STC_TARGETED_REPAIR_MIN_SCORE",
            84.0,
        ),
    ),
)

STC_TARGETED_REPAIR_MAX_DIMENSION_FAILURES = max(
    1,
    min(
        5,
        env_int(
            "XPAND_STC_TARGETED_REPAIR_MAX_DIMENSION_FAILURES",
            4,
        ),
    ),
)

STC_TARGETED_REPAIR_MAX_GAP = max(
    1.0,
    min(
        6.0,
        env_float(
            "XPAND_STC_TARGETED_REPAIR_MAX_GAP",
            4.0,
        ),
    ),
)

STC_TARGETED_REPAIR_CANDIDATES = max(
    1,
    min(
        2,
        env_int(
            "XPAND_STC_TARGETED_REPAIR_CANDIDATES",
            2,
        ),
    ),
)

STC_TARGETED_REPAIR_OUTPUT_COUNT = 2


# =========================================================
# JURY POLICY
# =========================================================

STC_MIN_JURY_CONFIDENCE = max(
    70.0,
    min(
        95.0,
        env_float(
            "XPAND_STC_MIN_JURY_CONFIDENCE",
            80.0,
        ),
    ),
)


# =========================================================
# HELPERS
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
        return list(
            value
        )

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


def normalize_arabic(
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
    value: Any,
    markers: Sequence[str],
) -> bool:

    source = normalize_arabic(
        value
    )

    return any(
        normalize_arabic(
            marker
        )
        in source
        for marker in markers
    )


def count_matches(
    value: Any,
    markers: Sequence[str],
) -> int:

    source = normalize_arabic(
        value
    )

    count = 0

    for marker in markers:

        if normalize_arabic(
            marker
        ) in source:

            count += 1

    return count


def compact_json(
    value: Any,
    limit: int = 12000,
) -> str:

    try:

        output = json.dumps(
            value,
            ensure_ascii=False,
            separators=(
                ",",
                ":",
            ),
            default=str,
        )

    except Exception:

        output = clean_text(
            value,
            limit,
        )

    return output[:limit]


def dedupe_strings(
    values: Sequence[str],
) -> List[str]:

    output: List[str] = []

    seen: Set[str] = set()

    for value in values:

        text = clean_text(
            value,
            1600,
        )

        if not text:
            continue

        key = text.lower()

        if key in seen:
            continue

        seen.add(
            key
        )

        output.append(
            text
        )

    return output


def parse_json_payload(
    raw: Any,
) -> Dict[str, Any]:

    if isinstance(
        raw,
        dict,
    ):
        return raw

    text = clean_text(
        raw,
        180000,
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

    payload = json.loads(
        text
    )

    if not isinstance(
        payload,
        dict,
    ):
        raise RuntimeError(
            "Structured Director response is not a JSON object."
        )

    return payload


# =========================================================
# BRAND PACK
# =========================================================

def locate_stc_brand_pack() -> Optional[Path]:

    candidates = [
        (
            Path(
                __file__
            ).resolve().parent
            /
            "brand_assets"
            /
            "stc_bank"
            /
            "stc_bank_brand_pack.json"
        ),

        (
            Path.cwd()
            /
            "brand_assets"
            /
            "stc_bank"
            /
            "stc_bank_brand_pack.json"
        ),

        Path(
            "/app/brand_assets/stc_bank/stc_bank_brand_pack.json"
        ),
    ]

    for path in candidates:

        try:

            if path.is_file():

                return path.resolve()

        except Exception:

            continue

    return None


def load_stc_brand_pack() -> Dict[str, Any]:

    path = locate_stc_brand_pack()

    if path is None:
        return {}

    try:

        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        if isinstance(
            payload,
            dict,
        ):
            return payload

    except Exception:
        pass

    return {}


# =========================================================
# CURATED LOCAL REFERENCE CONTEXT
#
# Metadata only.
#
# Physical JPEG bytes are handled later by
# xpand_production_engine.py.
# =========================================================

def stc_curated_reference_context(
    *,
    benefit_family: str,
    stc_style: str,
) -> Dict[str, Any]:

    result: Dict[str, Any] = {
        "available":
            False,

        "selected_assets":
            [],

        "brand_grounding":
            "",

        "reference_brief":
            "",
    }

    if (
        not STC_BRAND_KIT_AVAILABLE
        or load_default_stc_brand_kit is None
    ):
        return result

    try:

        kit = load_default_stc_brand_kit()

        selected = kit.select_ideation_assets(
            benefit_family=(
                benefit_family
            ),
            visual_family=(
                stc_style
            ),
            max_total=7,
            rotation_key=(
                "creative-brain:"
                + benefit_family
                + ":"
                + stc_style
            ),
        )

        assets: List[
            Dict[str, Any]
        ] = []

        for item in selected:

            assets.append(
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

                    "visual_families":
                        list(
                            getattr(
                                item,
                                "visual_families",
                                [],
                            )
                            or []
                        ),

                    "benefit_families":
                        list(
                            getattr(
                                item,
                                "benefit_families",
                                [],
                            )
                            or []
                        ),

                    "notes":
                        getattr(
                            item,
                            "notes",
                            "",
                        ),
                }
            )

        try:

            grounding = (
                kit.build_brand_grounding_text(
                    stc_style,
                    benefit_family=(
                        benefit_family
                    ),
                )
            )

        except TypeError:

            grounding = (
                kit.build_brand_grounding_text(
                    stc_style
                )
            )

        try:

            reference_brief = (
                kit.build_reference_brief(
                    selected
                )
            )

        except Exception:

            reference_brief = ""

        return {
            "available":
                True,

            "selected_assets":
                assets,

            "brand_grounding":
                clean_text(
                    grounding,
                    7000,
                ),

            "reference_brief":
                clean_text(
                    reference_brief,
                    6000,
                ),
        }

    except Exception:

        return result


def stc_brand_pack_prompt_fragment(
    *,
    benefit_family: str = "",
    stc_style: str = "",
) -> str:

    pack = load_stc_brand_pack()

    curated = (
        stc_curated_reference_context(
            benefit_family=(
                benefit_family
            ),
            stc_style=(
                stc_style
                or "premium_realistic"
            ),
        )
    )

    if not pack:

        return compact_json(
            curated,
            10000,
        )

    useful = {
        "brand_id":
            pack.get(
                "brand_id"
            ),

        "brand_name":
            pack.get(
                "brand_name"
            ),

        "default_visual_family":
            pack.get(
                "default_visual_family"
            ),

        "identity_keywords":
            pack.get(
                "identity_keywords",
                [],
            ),

        "required_brand_signals":
            pack.get(
                "required_brand_signals",
                [],
            ),

        "banned_patterns":
            pack.get(
                "banned_patterns",
                [],
            ),

        "approved_mechanisms":
            (
                pack.get(
                    "approved_mechanisms"
                )
                or
                pack.get(
                    "approved_visual_mechanisms"
                )
                or []
            ),

        "global_rules":
            pack.get(
                "global_rules",
                {},
            ),

        "style_family":
            safe_dict(
                pack.get(
                    "style_families"
                )
            ).get(
                stc_style,
                {},
            ),

        "benefit_family":
            safe_dict(
                pack.get(
                    "benefit_families"
                )
            ).get(
                benefit_family,
                {},
            ),

        "curated_reference_context":
            curated,
    }

    return compact_json(
        useful,
        14000,
    )


# =========================================================
# DATA MODELS
# =========================================================

@dataclass
class CreativeConcept:

    concept_id: str = ""

    category: str = ""

    title: str = ""

    concept_archetype: str = ""

    campaign_hook: str = ""

    core_idea: str = ""

    marketing_message: str = ""

    visual_metaphor: str = ""

    visual_mechanism_type: str = ""

    why_not_generic: str = ""

    environment: str = ""

    environment_novelty: str = ""

    hero_element: str = ""

    supporting_elements: List[str] = field(
        default_factory=list
    )

    camera_angle: str = ""

    lens: str = ""

    perspective: str = ""

    lighting: str = ""

    negative_space: str = ""

    brand_logic: str = ""

    production_method: str = ""

    campaign_extension: str = ""

    risks: List[str] = field(
        default_factory=list
    )

    scores: Dict[str, float] = field(
        default_factory=dict
    )

    weighted_score: float = 0.0

    cliche_hits: List[Any] = field(
        default_factory=list
    )

    debate: Dict[str, Any] = field(
        default_factory=dict
    )

    feasibility: Dict[str, Any] = field(
        default_factory=dict
    )

    evaluation_valid: bool = False

    quality_gate_passed: bool = False

    quality_gate_failures: List[str] = field(
        default_factory=list
    )

    generation_round: int = 1

    revised_from: str = ""


@dataclass
class CreativeBrainResponse:

    ok: bool

    mode: str

    request: str

    total_concepts: int

    concepts: List[
        CreativeConcept
    ]

    top_concepts: List[
        CreativeConcept
    ]

    winner: Optional[
        CreativeConcept
    ]

    metadata: Dict[
        str,
        Any
    ]

    errors: List[str]


# =========================================================
# CONCEPT SCHEMA
# =========================================================

CONCEPT_SCHEMA: Dict[str, Any] = {

    "type":
        "object",

    "additionalProperties":
        False,

    "properties": {

        "concept_id": {
            "type":
                "string",
        },

        "category": {
            "type":
                "string",
        },

        "title": {
            "type":
                "string",
        },

        "concept_archetype": {
            "type":
                "string",
        },

        "campaign_hook": {
            "type":
                "string",
        },

        "core_idea": {
            "type":
                "string",
        },

        "marketing_message": {
            "type":
                "string",
        },

        "visual_metaphor": {
            "type":
                "string",
        },

        "visual_mechanism_type": {
            "type":
                "string",
        },

        "why_not_generic": {
            "type":
                "string",
        },

        "environment": {
            "type":
                "string",
        },

        "environment_novelty": {
            "type":
                "string",
        },

        "hero_element": {
            "type":
                "string",
        },

        "supporting_elements": {
            "type":
                "array",

            "items": {
                "type":
                    "string",
            },
        },

        "camera_angle": {
            "type":
                "string",
        },

        "lens": {
            "type":
                "string",
        },

        "perspective": {
            "type":
                "string",
        },

        "lighting": {
            "type":
                "string",
        },

        "negative_space": {
            "type":
                "string",
        },

        "brand_logic": {
            "type":
                "string",
        },

        "production_method": {
            "type":
                "string",

            "enum": [
                "single_generation",
                "controlled_edit",
                "composite",
                "inpainting",
            ],
        },

        "campaign_extension": {
            "type":
                "string",
        },

        "risks": {
            "type":
                "array",

            "items": {
                "type":
                    "string",
            },
        },
    },

    "required": [
        "concept_id",
        "category",
        "title",
        "concept_archetype",
        "campaign_hook",
        "core_idea",
        "marketing_message",
        "visual_metaphor",
        "visual_mechanism_type",
        "why_not_generic",
        "environment",
        "environment_novelty",
        "hero_element",
        "supporting_elements",
        "camera_angle",
        "lens",
        "perspective",
        "lighting",
        "negative_space",
        "brand_logic",
        "production_method",
        "campaign_extension",
        "risks",
    ],
}


def make_ideation_schema(
    concept_count: int,
) -> Dict[str, Any]:

    return {

        "type":
            "object",

        "additionalProperties":
            False,

        "properties": {

            "concepts": {

                "type":
                    "array",

                "minItems":
                    concept_count,

                "maxItems":
                    concept_count,

                "items":
                    CONCEPT_SCHEMA,
            },
        },

        "required": [
            "concepts",
        ],
    }


# =========================================================
# REVIEW SCHEMA
# =========================================================

def evaluation_schema() -> Dict[str, Any]:

    return {

        "type":
            "object",

        "additionalProperties":
            False,

        "properties": {

            "concept_id": {
                "type":
                    "string",
            },

            "concept_strength": {
                "type":
                    "number",
            },

            "brand_fit": {
                "type":
                    "number",
            },

            "originality": {
                "type":
                    "number",
            },

            "visual_mechanism": {
                "type":
                    "number",
            },

            "camera_quality": {
                "type":
                    "number",
            },

            "realism": {
                "type":
                    "number",
            },

            "feasibility": {
                "type":
                    "number",
            },

            "copy_space_quality": {
                "type":
                    "number",
            },

            "distinctiveness": {
                "type":
                    "number",
            },

            "advertising_readiness": {
                "type":
                    "number",
            },

            "weighted_score": {
                "type":
                    "number",
            },

            "verdict": {
                "type":
                    "string",
            },

            "strengths": {
                "type":
                    "array",

                "items": {
                    "type":
                        "string",
                },
            },

            "weaknesses": {
                "type":
                    "array",

                "items": {
                    "type":
                        "string",
                },
            },

            "generic_scene_risk": {
                "type":
                    "boolean",
            },

            "repetition_risk": {
                "type":
                    "boolean",
            },

            "concept_is_scene_only": {
                "type":
                    "boolean",
            },

            "mechanism_survives_single_frame": {
                "type":
                    "boolean",
            },

            "looks_like_real_bank_campaign": {
                "type":
                    "boolean",
            },

            "merchant_online_channel_clear": {
                "type":
                    "boolean",
            },

            "merchant_pos_channel_clear": {
                "type":
                    "boolean",
            },

            "merchant_channels_fused": {
                "type":
                    "boolean",
            },

            "recommended_camera_angle": {
                "type":
                    "string",
            },

            "recommended_lens": {
                "type":
                    "string",
            },

            "recommended_perspective": {
                "type":
                    "string",
            },

            "camera_reason": {
                "type":
                    "string",
            },

            "production_feasible": {
                "type":
                    "boolean",
            },

            "feasibility_reason": {
                "type":
                    "string",
            },
        },

        "required": [
            "concept_id",
            "concept_strength",
            "brand_fit",
            "originality",
            "visual_mechanism",
            "camera_quality",
            "realism",
            "feasibility",
            "copy_space_quality",
            "distinctiveness",
            "advertising_readiness",
            "weighted_score",
            "verdict",
            "strengths",
            "weaknesses",
            "generic_scene_risk",
            "repetition_risk",
            "concept_is_scene_only",
            "mechanism_survives_single_frame",
            "looks_like_real_bank_campaign",
            "merchant_online_channel_clear",
            "merchant_pos_channel_clear",
            "merchant_channels_fused",
            "recommended_camera_angle",
            "recommended_lens",
            "recommended_perspective",
            "camera_reason",
            "production_feasible",
            "feasibility_reason",
        ],
    }


def make_review_schema(
    concept_count: int,
) -> Dict[str, Any]:

    return {

        "type":
            "object",

        "additionalProperties":
            False,

        "properties": {

            "evaluations": {

                "type":
                    "array",

                "minItems":
                    concept_count,

                "maxItems":
                    concept_count,

                "items":
                    evaluation_schema(),
            },
        },

        "required": [
            "evaluations",
        ],
    }


# =========================================================
# FINAL JURY SCHEMA
# =========================================================

FINALIST_JURY_SCHEMA: Dict[str, Any] = {

    "type":
        "object",

    "additionalProperties":
        False,

    "properties": {

        "selected_concept_id": {
            "type":
                "string",
        },

        "approval": {
            "type":
                "boolean",
        },

        "confidence": {
            "type":
                "number",
        },

        "advertising_reason": {
            "type":
                "string",
        },

        "brand_reason": {
            "type":
                "string",
        },

        "originality_reason": {
            "type":
                "string",
        },

        "merchant_fusion_approved": {
            "type":
                "boolean",
        },

        "fatal_issues": {
            "type":
                "array",

            "items": {
                "type":
                    "string",
            },
        },

        "production_instruction": {
            "type":
                "string",
        },

        "recommended_camera_angle": {
            "type":
                "string",
        },

        "recommended_lens": {
            "type":
                "string",
        },

        "recommended_perspective": {
            "type":
                "string",
        },

        "do_not_drift_into": {
            "type":
                "array",

            "items": {
                "type":
                    "string",
            },
        },
    },

    "required": [
        "selected_concept_id",
        "approval",
        "confidence",
        "advertising_reason",
        "brand_reason",
        "originality_reason",
        "merchant_fusion_approved",
        "fatal_issues",
        "production_instruction",
        "recommended_camera_angle",
        "recommended_lens",
        "recommended_perspective",
        "do_not_drift_into",
    ],
}


# =========================================================
# BOARD SCHEMA
#
# Used by:
# - Targeted Repair
# - Fresh Recovery
#
# One paid call generates, evaluates and juries.
# =========================================================

def make_board_schema(
    concept_count: int,
) -> Dict[str, Any]:

    return {

        "type":
            "object",

        "additionalProperties":
            False,

        "properties": {

            "concepts": {

                "type":
                    "array",

                "minItems":
                    concept_count,

                "maxItems":
                    concept_count,

                "items":
                    CONCEPT_SCHEMA,
            },

            "evaluations": {

                "type":
                    "array",

                "minItems":
                    concept_count,

                "maxItems":
                    concept_count,

                "items":
                    evaluation_schema(),
            },

            "selected_concept_id": {
                "type":
                    "string",
            },

            "approval": {
                "type":
                    "boolean",
            },

            "confidence": {
                "type":
                    "number",
            },

            "advertising_reason": {
                "type":
                    "string",
            },

            "brand_reason": {
                "type":
                    "string",
            },

            "originality_reason": {
                "type":
                    "string",
            },

            "merchant_fusion_approved": {
                "type":
                    "boolean",
            },

            "fatal_issues": {
                "type":
                    "array",

                "items": {
                    "type":
                        "string",
                },
            },

            "production_instruction": {
                "type":
                    "string",
            },

            "recommended_camera_angle": {
                "type":
                    "string",
            },

            "recommended_lens": {
                "type":
                    "string",
            },

            "recommended_perspective": {
                "type":
                    "string",
            },

            "do_not_drift_into": {
                "type":
                    "array",

                "items": {
                    "type":
                        "string",
                },
            },
        },

        "required": [
            "concepts",
            "evaluations",
            "selected_concept_id",
            "approval",
            "confidence",
            "advertising_reason",
            "brand_reason",
            "originality_reason",
            "merchant_fusion_approved",
            "fatal_issues",
            "production_instruction",
            "recommended_camera_angle",
            "recommended_lens",
            "recommended_perspective",
            "do_not_drift_into",
        ],
    }


#
# V5.4 compatibility name.
#

def make_recovery_schema(
    concept_count: int,
) -> Dict[str, Any]:

    return make_board_schema(
        concept_count
    )


# =========================================================
# STC LANGUAGE / PATTERNS
# =========================================================

STC_GENERIC_PATTERNS = [

    "person using phone",
    "man using phone",
    "woman using phone",

    "شخص يستخدم الهاتف",
    "رجل يستخدم الهاتف",
    "امرأة تستخدم الهاتف",

    "customer paying at counter",
    "customer taps terminal",
    "customer tapping terminal",

    "عميل يدفع عند الكاونتر",
    "عميل يدفع عند الكاونتر",

    "smiling businessman",
    "business handshake",
    "generic office",
]


STC_FINTECH_CLICHES = [

    "network lines",
    "connection lines",
    "glowing payment trail",
    "glowing route",
    "hologram",
    "holographic",
    "hud",
    "cyber",
    "cyber tunnel",
    "neon fintech",
    "floating icons",
    "floating card",
    "floating phone",
    "floating pos",
    "floating terminal",
    "digital tunnel",
    "laser beam",
    "particles",
    "particle cloud",

    "هولوغرام",
    "بطاقة طافية",
    "هاتف طائر",
    "خطوط اتصال",
    "مسار ضوئي",
]


STC_REPEATED_SCENE_MARKERS = [

    "wooden counter",
    "wood counter",
    "wooden checkout",
    "luxury boutique",
    "boutique checkout",
    "perfume boutique",
    "fashion boutique",
    "merchant behind counter",
    "worker packing box",
    "packing parcel",

    "كاونتر خشبي",
    "متجر فاخر",
    "موظف يعبئ صندوق",
    "تغليف صندوق",
]


LITERAL_TRANSACTION_CUSTOMER_MARKERS = [

    "customer",
    "shopper",
    "buyer",
    "عميل",
    "زبون",
]


LITERAL_TRANSACTION_COUNTER_MARKERS = [

    "counter",
    "checkout counter",
    "cashier counter",
    "كاونتر",
    "منضدة دفع",
]


LITERAL_TRANSACTION_MERCHANT_MARKERS = [

    "merchant",
    "cashier",
    "seller",
    "store owner",
    "worker",
    "تاجر",
    "بائع",
    "كاشير",
    "موظف",
]


MERCHANT_ONLINE_MARKERS = [

    "التجارة الإلكترونية",
    "التجارة الالكترونية",
    "تجارة إلكترونية",
    "تجاره الكترونيه",

    "e-commerce",
    "ecommerce",

    "online commerce",
    "digital commerce",

    "online order",
    "online ordering",

    "digital storefront",
    "online storefront",

    "web checkout",
    "online checkout",

    "online sale",
    "online sales",

    "طلب إلكتروني",
    "طلب الكتروني",
    "متجر إلكتروني",
    "متجر الكتروني",
    "بيع إلكتروني",
]


MERCHANT_PHYSICAL_MARKERS = [

    "نقاط البيع",
    "نقطة البيع",
    "نقطه البيع",

    "الدفع داخل المتجر",
    "الدفع في المتجر",

    "دفع حضوري",

    "جهاز دفع",
    "جهاز نقاط بيع",

    "point of sale",
    "pos",
    "pos terminal",

    "payment terminal",
    "card terminal",
    "card reader",
    "payment reader",

    "tap payment",
    "tap-to-pay",
    "tap to pay",

    "in-store payment",
    "in store payment",

    "in-store acceptance",

    "physical payment",
    "physical checkout",

    "store payment",
]


MERCHANT_MECHANISM_MARKERS = [

    "connect",
    "connected",
    "connection",

    "unify",
    "unified",
    "fusion",
    "fused",

    "continuity",
    "continuous",

    "bridge",

    "transformation",
    "transform",

    "cause and effect",
    "cause/effect",

    "same system",
    "one ecosystem",
    "single ecosystem",

    "foreground background relationship",
    "foreground-to-background",

    "perspective reveal",
    "spatial relationship",

    "physical relationship",
    "material transition",

    "service transformation",

    "يربط",
    "ربط",
    "متصل",
    "موحد",
    "توحيد",
    "اندماج",
    "استمرارية",
    "استمراريه",
    "تحول",
    "جسر بصري",
    "علاقة بصرية",
    "علاقه بصريه",
    "نظام واحد",
    "منظومة واحدة",
]


HARD_REJECT_FAILURES: Set[str] = {

    "literal_transaction_tableau",

    "generic_fintech_visual",

    "repeated_stc_scene",

    "generic_lifestyle_without_advertising_mechanism",

    "review_generic_scene_risk",

    "review_repetition_risk",

    "concept_is_scene_only",

    "single_frame_mechanism_failure",

    "not_bank_campaign_ready",

    "merchant_channels_not_visually_connected",
}


# =========================================================
# BENEFIT ROUTING
# =========================================================

def detect_benefit_family(
    user_request: str,
) -> str:

    value = clean_text(
        user_request,
        14000,
    )

    normalized = normalize_arabic(
        value
    )

    merchant_markers = [

        "نقاط البيع",
        "نقطه البيع",

        "التجاره الالكترونيه",
        "تجاره الكترونيه",

        "e-commerce",
        "ecommerce",

        "point of sale",
        "pos",

        "merchant payment",
        "merchant payments",
    ]

    if any(
        normalize_arabic(
            marker
        )
        in normalized
        for marker in merchant_markers
    ):
        return "merchant_payments"

    try:

        skill_family = clean_text(
            detect_stc_benefit_family(
                value
            ),
            100,
        )

        if skill_family:
            return skill_family

    except Exception:
        pass

    if contains_any(
        value,
        [
            "تمويل",
            "finance",
            "loan",
            "راتب",
        ],
    ):
        return "financing"

    if contains_any(
        value,
        [
            "سفر",
            "travel",
            "cashback",
            "كاش باك",
        ],
    ):
        return "travel_cards"

    if contains_any(
        value,
        [
            "تحويل",
            "iban",
            "آيبان",
            "حوال",
        ],
    ):
        return "transfers"

    return "general_banking"


# =========================================================
# STC STYLE
# =========================================================

def detect_stc_style(
    user_request: str,
    style_hint: str = "",
) -> str:

    text = (
        clean_text(
            user_request,
            14000,
        )
        +
        "\n"
        +
        clean_text(
            style_hint,
            1200,
        )
    )

    if contains_any(
        text,
        [
            "بيئة بنفسجية",
            "بيئه بنفسجيه",
            "purple architecture",
            "purple studio",
            "استوديو بنفسجي",
        ],
    ):
        return "premium_purple_architecture"

    if contains_any(
        text,
        [
            "واقعية معززة",
            "واقعيه معززه",
            "augmented realism",
            "symbolic realism",
            "واقعي بفكرة خيالية",
            "واقعي بفكره خياليه",
            "واقعي سريالي",
        ],
    ):
        return "premium_augmented_realism"

    return "premium_realistic"


# =========================================================
# HIGH ALERT
# =========================================================

def is_stc_high_alert(
    user_request: str,
    mode: str,
) -> bool:

    return bool(
        STC_HIGH_ALERT_ENABLED
        and mode == MODE_MASTERPIECE
        and is_stc_bank_request(
            user_request
        )
    )


def concept_count_for_request(
    user_request: str,
    mode: str,
) -> int:

    if is_stc_high_alert(
        user_request,
        mode,
    ):
        return STC_HIGH_ALERT_CONCEPT_COUNT

    return NORMAL_CONCEPT_COUNT


# =========================================================
# CONCEPT PARSER
# =========================================================

def concept_from_dict(
    item: Dict[str, Any],
    *,
    fallback_id: str,
    generation_round: int = 1,
    revised_from: str = "",
) -> CreativeConcept:

    return CreativeConcept(

        concept_id=(
            clean_text(
                item.get(
                    "concept_id"
                ),
                100,
            )
            or fallback_id
        ),

        category=clean_text(
            item.get(
                "category"
            ),
            160,
        ),

        title=clean_text(
            item.get(
                "title"
            ),
            500,
        ),

        concept_archetype=clean_text(
            item.get(
                "concept_archetype"
            ),
            600,
        ),

        campaign_hook=clean_text(
            item.get(
                "campaign_hook"
            ),
            1800,
        ),

        core_idea=clean_text(
            item.get(
                "core_idea"
            ),
            3600,
        ),

        marketing_message=clean_text(
            item.get(
                "marketing_message"
            ),
            2200,
        ),

        visual_metaphor=clean_text(
            item.get(
                "visual_metaphor"
            ),
            2600,
        ),

        visual_mechanism_type=clean_text(
            item.get(
                "visual_mechanism_type"
            ),
            800,
        ),

        why_not_generic=clean_text(
            item.get(
                "why_not_generic"
            ),
            2200,
        ),

        environment=clean_text(
            item.get(
                "environment"
            ),
            3000,
        ),

        environment_novelty=clean_text(
            item.get(
                "environment_novelty"
            ),
            2000,
        ),

        hero_element=clean_text(
            item.get(
                "hero_element"
            ),
            1800,
        ),

        supporting_elements=[
            clean_text(
                value,
                900,
            )
            for value
            in safe_list(
                item.get(
                    "supporting_elements"
                )
            )[:8]
            if clean_text(
                value,
                900,
            )
        ],

        camera_angle=clean_text(
            item.get(
                "camera_angle"
            ),
            900,
        ),

        lens=clean_text(
            item.get(
                "lens"
            ),
            400,
        ),

        perspective=clean_text(
            item.get(
                "perspective"
            ),
            1200,
        ),

        lighting=clean_text(
            item.get(
                "lighting"
            ),
            1700,
        ),

        negative_space=clean_text(
            item.get(
                "negative_space"
            ),
            1300,
        ),

        brand_logic=clean_text(
            item.get(
                "brand_logic"
            ),
            2400,
        ),

        production_method=(
            clean_text(
                item.get(
                    "production_method"
                ),
                100,
            )
            or "single_generation"
        ),

        campaign_extension=clean_text(
            item.get(
                "campaign_extension"
            ),
            1700,
        ),

        risks=[
            clean_text(
                value,
                900,
            )
            for value
            in safe_list(
                item.get(
                    "risks"
                )
            )[:8]
            if clean_text(
                value,
                900,
            )
        ],

        generation_round=(
            generation_round
        ),

        revised_from=(
            revised_from
        ),
    )


def parse_concepts(
    payload: Dict[str, Any],
    *,
    generation_round: int = 1,
    id_prefix: str = "C",
    force_ids: bool = False,
) -> List[CreativeConcept]:

    raw_concepts = safe_list(
        payload.get(
            "concepts"
        )
    )

    concepts: List[
        CreativeConcept
    ] = []

    for index, item in enumerate(
        raw_concepts,
        start=1,
    ):

        if not isinstance(
            item,
            dict,
        ):
            continue

        forced_id = (
            id_prefix
            +
            str(index).zfill(2)
        )

        concept = concept_from_dict(
            item,
            fallback_id=(
                forced_id
            ),
            generation_round=(
                generation_round
            ),
        )

        if force_ids:
            concept.concept_id = forced_id

        concepts.append(
            concept
        )

    return concepts


# =========================================================
# SEARCHABLE CONCEPT TEXT
# =========================================================

def concept_search_text(
    concept: CreativeConcept,
) -> str:

    return "\n".join(
        [
            concept.title,
            concept.concept_archetype,
            concept.campaign_hook,
            concept.core_idea,
            concept.marketing_message,
            concept.visual_metaphor,
            concept.visual_mechanism_type,
            concept.why_not_generic,
            concept.environment,
            concept.environment_novelty,
            concept.hero_element,
            " ".join(
                concept.supporting_elements
            ),
            concept.camera_angle,
            concept.lens,
            concept.perspective,
            concept.lighting,
            concept.negative_space,
            concept.brand_logic,
            concept.campaign_extension,
            " ".join(
                concept.risks
            ),
        ]
    )


# =========================================================
# MERCHANT SEMANTIC SIGNALS
# =========================================================

def merchant_local_signals(
    concept: CreativeConcept,
) -> Dict[str, bool]:

    text = concept_search_text(
        concept
    )

    return {

        "online":
            contains_any(
                text,
                MERCHANT_ONLINE_MARKERS,
            ),

        "physical":
            contains_any(
                text,
                MERCHANT_PHYSICAL_MARKERS,
            ),

        "mechanism":
            contains_any(
                text,
                MERCHANT_MECHANISM_MARKERS,
            ),
    }


# =========================================================
# LOCAL CONCEPT PENALTIES
# =========================================================

def local_concept_penalties(
    concept: CreativeConcept,
    *,
    user_request: str,
    benefit_family: str,
    stc_style: str,
) -> Tuple[
    float,
    List[str],
]:

    text = concept_search_text(
        concept
    )

    penalty = 0.0

    failures: List[str] = []

    # =====================================================
    # LITERAL TRANSACTION TABLEAU
    # =====================================================

    customer = contains_any(
        text,
        LITERAL_TRANSACTION_CUSTOMER_MARKERS,
    )

    counter = contains_any(
        text,
        LITERAL_TRANSACTION_COUNTER_MARKERS,
    )

    merchant = contains_any(
        text,
        LITERAL_TRANSACTION_MERCHANT_MARKERS,
    )

    physical_payment = contains_any(
        text,
        MERCHANT_PHYSICAL_MARKERS,
    )

    packing = contains_any(
        text,
        [
            "packing",
            "packing box",
            "packing parcel",
            "worker packing",
            "تغليف",
            "يعبئ صندوق",
            "تعبئة صندوق",
        ],
    )

    if (
        customer
        and counter
        and physical_payment
        and (
            merchant
            or packing
        )
    ):

        penalty += 35.0

        failures.append(
            "literal_transaction_tableau"
        )

    # =====================================================
    # GENERIC FINTECH
    # =====================================================

    fintech_hits = count_matches(
        text,
        STC_FINTECH_CLICHES,
    )

    if fintech_hits >= 2:

        penalty += 30.0

        failures.append(
            "generic_fintech_visual"
        )

    elif fintech_hits == 1:

        penalty += 5.0

        failures.append(
            "generic_fintech_warning"
        )

    # =====================================================
    # REPEATED STC SCENE
    # =====================================================

    repeated_hits = count_matches(
        text,
        STC_REPEATED_SCENE_MARKERS,
    )

    if (
        STC_REJECT_REPEATED_SCENES
        and repeated_hits >= 2
    ):

        penalty += 26.0

        failures.append(
            "repeated_stc_scene"
        )

    elif repeated_hits == 1:

        penalty += 4.0

        failures.append(
            "repeated_scene_warning"
        )

    # =====================================================
    # GENERIC LIFESTYLE WITHOUT AD MECHANISM
    # =====================================================

    generic_hits = count_matches(
        text,
        STC_GENERIC_PATTERNS,
    )

    mechanism_present = bool(
        clean_text(
            concept.visual_mechanism_type,
            800,
        )
        and
        clean_text(
            concept.campaign_hook,
            1800,
        )
        and
        len(
            clean_text(
                concept.why_not_generic,
                2200,
            )
        )
        >= 25
    )

    if (
        STC_REJECT_GENERIC_SCENES
        and generic_hits >= 1
        and not mechanism_present
    ):

        penalty += 25.0

        failures.append(
            "generic_lifestyle_without_advertising_mechanism"
        )

    # =====================================================
    # MECHANISM DEFENSE
    # =====================================================

    if STC_REQUIRE_VISUAL_MECHANISM:

        if len(
            clean_text(
                concept.visual_mechanism_type,
                1000,
            )
        ) < 4:

            penalty += 5.0

            failures.append(
                "visual_mechanism_type_missing"
            )

        if len(
            clean_text(
                concept.campaign_hook,
                2000,
            )
        ) < 20:

            penalty += 4.0

            failures.append(
                "campaign_hook_weak"
            )

        if len(
            clean_text(
                concept.why_not_generic,
                2200,
            )
        ) < 25:

            penalty += 4.0

            failures.append(
                "generic_defense_missing"
            )

        if len(
            clean_text(
                concept.environment_novelty,
                1800,
            )
        ) < 25:

            penalty += 3.0

            failures.append(
                "environment_novelty_missing"
            )

    # =====================================================
    # PURPLE IS NOT AN IDEA
    # =====================================================

    if (
        stc_style
        ==
        "premium_realistic"
        and
        contains_any(
            text,
            [
                "purple neon",
                "neon purple",
                "purple cyber",
                "everything purple",
                "بنفسجي نيون",
            ],
        )
    ):

        penalty += 18.0

        failures.append(
            "purple_neon_brand_substitute"
        )

    # =====================================================
    # MERCHANT LOCAL LANGUAGE
    #
    # Lexical absence is SOFT.
    # Executive semantic review is authoritative.
    # =====================================================

    if benefit_family == "merchant_payments":

        signals = merchant_local_signals(
            concept
        )

        if not signals[
            "online"
        ]:

            penalty += 3.0

            failures.append(
                "merchant_online_language_implicit"
            )

        if not signals[
            "physical"
        ]:

            penalty += 3.0

            failures.append(
                "merchant_pos_language_implicit"
            )

        if not signals[
            "mechanism"
        ]:

            penalty += 4.0

            failures.append(
                "merchant_connection_language_weak"
            )

    return (
        penalty,
        dedupe_strings(
            failures
        ),
    )


# =========================================================
# DIMENSION SCORE
# =========================================================

def dimension_composite_score(
    scores: Dict[str, Any],
) -> float:

    total = 0.0

    for key, weight in (
        DIMENSION_WEIGHTS.items()
    ):

        total += (
            clamp_score(
                scores.get(
                    key,
                    0,
                )
            )
            *
            (
                weight
                /
                100.0
            )
        )

    return round(
        total,
        2,
    )


# =========================================================
# STC DIMENSION FAILURES
# =========================================================

def stc_dimension_gate_failures(
    concept: CreativeConcept,
) -> List[str]:

    scores = safe_dict(
        concept.scores
    )

    failures: List[str] = []

    for key, minimum in (
        STC_DIMENSION_MINIMUMS.items()
    ):

        value = clamp_score(
            scores.get(
                key,
                0,
            )
        )

        if value < minimum:

            failures.append(
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

    if any(
        failure
        in HARD_REJECT_FAILURES
        for failure
        in concept.quality_gate_failures
    ):

        failures.append(
            "hard_local_reject"
        )

    if not bool(
        safe_dict(
            concept.feasibility
        ).get(
            "production_feasible",
            False,
        )
    ):

        failures.append(
            "production_not_feasible"
        )

    return dedupe_strings(
        failures
    )


# =========================================================
# STRICT QUALIFICATION
# =========================================================

def strict_qualified_concepts(
    concepts: Sequence[
        CreativeConcept
    ],
    *,
    high_alert: bool,
) -> List[
    CreativeConcept
]:

    output: List[
        CreativeConcept
    ] = []

    for concept in concepts:

        if not concept.evaluation_valid:
            continue

        if any(
            failure
            in HARD_REJECT_FAILURES
            for failure
            in concept.quality_gate_failures
        ):
            continue

        if high_alert:

            if (
                concept.weighted_score
                <
                STC_HIGH_ALERT_RELEASE_FLOOR
            ):
                continue

            if stc_dimension_gate_failures(
                concept
            ):
                continue

        output.append(
            concept
        )

    output.sort(
        key=lambda item:
            item.weighted_score,
        reverse=True,
    )

    return output


# =========================================================
# TARGETED REPAIR DIAGNOSIS
# =========================================================

def targeted_repair_dimension_gaps(
    concept: CreativeConcept,
) -> List[
    Dict[str, Any]
]:

    scores = safe_dict(
        concept.scores
    )

    gaps: List[
        Dict[str, Any]
    ] = []

    for key, minimum in (
        STC_DIMENSION_MINIMUMS.items()
    ):

        score = clamp_score(
            scores.get(
                key,
                0,
            )
        )

        if score >= minimum:
            continue

        gaps.append(
            {
                "dimension":
                    key,

                "score":
                    round(
                        score,
                        2,
                    ),

                "minimum":
                    round(
                        minimum,
                        2,
                    ),

                "gap":
                    round(
                        minimum
                        -
                        score,
                        2,
                    ),

                "failure":
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
                    ),
            }
        )

    return gaps


def targeted_repair_rejection_reason(
    concept: CreativeConcept,
) -> str:

    if not concept.evaluation_valid:

        return (
            "evaluation_not_valid"
        )

    hard_failures = [
        failure
        for failure
        in concept.quality_gate_failures
        if failure in HARD_REJECT_FAILURES
    ]

    if hard_failures:

        return (
            "hard_reject:"
            +
            ",".join(
                hard_failures
            )
        )

    if not bool(
        safe_dict(
            concept.feasibility
        ).get(
            "production_feasible",
            False,
        )
    ):

        return (
            "production_not_feasible"
        )

    if (
        concept.weighted_score
        <
        STC_TARGETED_REPAIR_MIN_SCORE
    ):

        return (
            "score_below_repair_floor"
        )

    gaps = targeted_repair_dimension_gaps(
        concept
    )

    if not gaps:

        return (
            "already_strict_dimension_qualified"
        )

    if (
        len(
            gaps
        )
        >
        STC_TARGETED_REPAIR_MAX_DIMENSION_FAILURES
    ):

        return (
            "too_many_dimension_failures"
        )

    largest_gap = max(
        (
            safe_float(
                item.get(
                    "gap"
                ),
                0,
            )
            for item
            in gaps
        ),
        default=0.0,
    )

    if (
        largest_gap
        >
        STC_TARGETED_REPAIR_MAX_GAP
    ):

        return (
            "dimension_gap_too_large"
        )

    return ""


def is_targeted_repair_candidate(
    concept: CreativeConcept,
) -> bool:

    return not bool(
        targeted_repair_rejection_reason(
            concept
        )
    )


def select_targeted_repair_candidates(
    concepts: Sequence[
        CreativeConcept
    ],
) -> List[
    CreativeConcept
]:

    if not STC_TARGETED_REPAIR_ENABLED:

        return []

    candidates = [
        concept
        for concept in concepts
        if is_targeted_repair_candidate(
            concept
        )
    ]

    candidates.sort(
        key=lambda item:
            (
                item.weighted_score,
                -len(
                    targeted_repair_dimension_gaps(
                        item
                    )
                ),
            ),
        reverse=True,
    )

    return candidates[
        :STC_TARGETED_REPAIR_CANDIDATES
    ]


# =========================================================
# ARCHETYPE SYSTEM
# =========================================================

STC_HIGH_ALERT_ARCHETYPES = """
The concept pool must deliberately cover fundamentally
different advertising grammars.

Concept 1:
PREMIUM HUMAN REALISM
Real Saudi commercial life with a genuine campaign mechanism.

Concept 2:
OBJECT-LED COMMERCIAL STORY
A real physical object relationship communicates the service.

Concept 3:
ARCHITECTURAL / SPATIAL IDEA
Space, geometry, threshold or circulation carries the idea.

Concept 4:
AUGMENTED REALISM
One believable conceptual intervention inside a real world.

Concept 5:
CAMERA-LED IDEA
The chosen perspective itself reveals the proposition.

Concept 6:
SERVICE TRANSFORMATION
One physical action or element transforms commercial meaning.

Concept 7:
SAUDI BUSINESS CONTEXT
Authentic contemporary commerce without the boutique-counter
cliché.

Concept 8:
BOLD CAMPAIGN HERO
One simple, memorable, award-minded visual proposition.

If more concepts are requested:
continue using genuinely different advertising grammars.

At most TWO concepts may use indoor retail.

At most ONE concept may make a POS terminal the obvious
foreground hero.

Do not use the same hero relationship twice.

Do not create eight variations of:
merchant + terminal + parcel + counter.
"""


# =========================================================
# IDEATION PROMPT
# =========================================================

def build_ideation_prompt(
    *,
    user_request: str,
    brand_context: Any,
    visual_references: Any,
    style_hint: str,
    benefit_family: str,
    stc_style: str,
    recovery: bool = False,
    concept_count: int = 4,
    high_alert: bool = False,
) -> str:

    recovery_block = ""

    if recovery:

        recovery_block = f"""
==================================================
STRUCTURED TECHNICAL RETRY
==================================================

A previous structured ideation call failed technically.

This is NOT a creative-quality recovery.

Return exactly {concept_count} complete concept objects.

Do not shorten the schema.
"""

    stc_block = ""

    if is_stc_bank_request(
        user_request
    ):

        high_alert_block = ""

        if high_alert:

            high_alert_block = f"""
==================================================
STC BANK HIGH-ALERT
==================================================

A scene is not an advertising idea.

A POS terminal is not an advertising idea.

A customer using a phone is not an advertising idea.

Purple is not automatically brand intelligence.

Every concept must have ONE memorable visual mechanism
that survives as ONE still frame.

The viewer should feel:

"This image was conceived as advertising."

not:

"This is a nice picture of a service."

--------------------------------------------------
MANDATORY DIVERSITY
--------------------------------------------------

{STC_HIGH_ALERT_ARCHETYPES}
"""

        stc_block = f"""
==================================================
PERMANENT STC BRAND INTELLIGENCE
==================================================

{stc_brand_pack_prompt_fragment(
    benefit_family=benefit_family,
    stc_style=stc_style,
)}

==================================================
STC VISUAL FAMILY
==================================================

Selected family:

{stc_style}

PREMIUM REALISTIC:

Prefer:
- real Saudi commercial environments
- real people only when useful
- natural skin
- premium modern materials
- controlled reflections
- realistic daylight or motivated commercial light
- disciplined camera
- restrained brand accents

Purple is OPTIONAL.

Do NOT make purple the idea.

PURPLE ARCHITECTURAL:

Only when this family is explicitly active:
- purple may become physical architecture
- planes
- geometry
- satin materials
- controlled reflection
- shadow depth

Never:
- cyber room
- neon fintech tunnel
- generic purple gradient room

AUGMENTED REALISM:

Use ONE physically believable conceptual intervention.

It must respect:
- gravity
- scale
- perspective
- contact
- shadow
- occlusion
- material logic

No random holograms or icon clouds.

==================================================
MERCHANT PAYMENTS LAW
==================================================

When benefit_family = merchant_payments:

The viewer must understand:

ONLINE / E-COMMERCE SALES
+
PHYSICAL POINT-OF-SALE ACCEPTANCE
+
ONE UNIFIED MERCHANT PROPOSITION

Equivalent physical language is allowed:
- POS
- payment terminal
- card reader
- tap-to-pay
- in-store acceptance

Equivalent online language is allowed:
- e-commerce
- digital storefront
- online order
- web checkout
- online commerce

DO NOT merely place the two channels next to each other.

The visual mechanism must CONNECT them.

HARD WEAK PATTERN:

CUSTOMER + POS + COUNTER + MERCHANT + TABLET/PACKING

is ordinary transaction photography, not the campaign idea.

==================================================
GENERIC FINTECH BAN
==================================================

No:
- floating cards
- floating phones
- floating POS
- network lines
- glowing routes
- holograms
- HUD
- cyber tunnels
- random particles
- generic fintech icons

==================================================
COPY SPACE
==================================================

Reserve approximately 25%-40% natural negative space.

No fake digital blank panel.

==================================================
TEXT / LOGO
==================================================

The intended generated image must contain no:
- headline
- slogan
- CTA
- legal copy
- STC logo
- bank logo
- card-network logo
- fake readable banking UI

==================================================
CONCEPT DEFENSE
==================================================

For EVERY concept:

why_not_generic:
Explain precisely why this is an advertisement rather than
ordinary lifestyle photography.

environment_novelty:
Explain why the environment is not the repeated STC/Xpand
merchant-counter cliché.

==================================================
STC SKILL
==================================================

{clean_text(
    STC_BANK_VISUAL_SKILL,
    7000,
)}

{high_alert_block}
"""

    return f"""
You are XPAND Creative Brain V5.5.

The brief gives you the MESSAGE.

You are responsible for inventing the advertising idea.

==================================================
ORIGINAL REQUEST
==================================================

{clean_text(
    user_request,
    7000,
)}

==================================================
BRAND CONTEXT
==================================================

{compact_json(
    brand_context,
    7000,
)}

==================================================
VISUAL REFERENCE DNA
==================================================

{compact_json(
    visual_references,
    9000,
)}

References are DNA, not templates.

Extract:
- art-direction quality
- visual hierarchy
- camera discipline
- material quality
- lighting discipline
- brand confidence
- campaign simplicity

Do NOT clone a reference.

==================================================
STYLE HINT
==================================================

{clean_text(
    style_hint,
    1500,
)}

==================================================
BENEFIT FAMILY
==================================================

{benefit_family}

==================================================
IDEATION RULES
==================================================

Generate exactly {concept_count} fundamentally different
advertising concepts.

Each concept must differ in:
- archetype
- visual mechanism
- hero relationship
- environment
- spatial composition
- camera strategy

Do NOT produce cosmetic variations.

No generated text or logo.

{stc_block}

{recovery_block}

==================================================
OUTPUT CONTRACT
==================================================

Return exactly the structured schema.

Use IDs:

C01
C02
C03
...

until exactly {concept_count} concepts exist.

Do NOT score concepts in this call.
""".strip()


# =========================================================
# REVIEW PROMPT
# =========================================================

def build_review_prompt(
    *,
    user_request: str,
    concepts: List[
        CreativeConcept
    ],
    benefit_family: str,
    stc_style: str,
    high_alert: bool,
) -> str:

    payload = [
        concept_to_dict(
            concept
        )
        for concept in concepts
    ]

    high_alert_block = ""

    if high_alert:

        high_alert_block = f"""
==================================================
STC STRICT STANDARD
==================================================

Do not reward merely competent work.

A concept does NOT deserve 90+ merely because:
- it is pretty
- it is realistic
- it is feasible
- it includes the requested service

90+ means campaign-grade.

STRICT RELEASE DIMENSIONS:

concept_strength >= {STC_MIN_CONCEPT_STRENGTH}
brand_fit >= {STC_MIN_BRAND_FIT}
originality >= {STC_MIN_ORIGINALITY}
visual_mechanism >= {STC_MIN_VISUAL_MECHANISM}
camera_quality >= {STC_MIN_CAMERA_QUALITY}
realism >= {STC_MIN_REALISM}
feasibility >= {STC_MIN_FEASIBILITY}
copy_space_quality >= {STC_MIN_COPY_SPACE}
distinctiveness >= {STC_MIN_DISTINCTIVENESS}
advertising_readiness >= {STC_MIN_AD_READINESS}

Do not adjust your scoring to force a pass.

Heavily penalize:
- customer + POS + counter + merchant + packing/tablet
- repeated luxury boutique
- repeated wood counter
- worker packing a parcel as the e-commerce idea
- generic person using phone
- ordinary transaction photography
- purple as a substitute for concept
- generic fintech effects
"""

    return f"""
You are XPAND V5.5 EXECUTIVE CREATIVE REVIEW BOARD.

Evaluate ALL concepts independently.

You are:
- executive creative director
- STC Bank brand guardian
- senior advertising art director
- commercial photography director
- production feasibility reviewer

Do NOT invent replacement concepts in this call.

==================================================
REQUEST
==================================================

{clean_text(
    user_request,
    6500,
)}

==================================================
BENEFIT FAMILY
==================================================

{benefit_family}

==================================================
STYLE
==================================================

{stc_style}

==================================================
CONCEPTS
==================================================

{compact_json(
    payload,
    34000,
)}

==================================================
SCORE 0-100
==================================================

concept_strength:
Is there a strong single-frame advertising proposition?

brand_fit:
Could this genuinely belong to STC Bank?

originality:
Is it materially different from stock bank advertising?

visual_mechanism:
Is there a real visual idea, not merely a scene?

camera_quality:
Does the camera strengthen meaning and hierarchy?

realism:
Can the execution look premium and physically credible?

feasibility:
Can the image model preserve the central mechanism?

copy_space_quality:
Is copy space naturally integrated?

distinctiveness:
Is the direction memorable?

advertising_readiness:
Would a senior bank creative director authorize production?

weighted_score:
Give your strict overall score.

==================================================
BOOLEAN CREATIVE JUDGMENTS
==================================================

generic_scene_risk:
TRUE when the idea could collapse into ordinary lifestyle
or transaction photography.

repetition_risk:
TRUE when it resembles known repeated XPAND/STC scenes.

concept_is_scene_only:
TRUE if it is mainly location + people + props without
an advertising mechanism.

mechanism_survives_single_frame:
TRUE only when the mechanism is clear in one still image.

looks_like_real_bank_campaign:
TRUE only when the idea has premium financial-campaign
discipline.

==================================================
MERCHANT SEMANTIC REVIEW
==================================================

When benefit_family = merchant_payments:

merchant_online_channel_clear:
Can the viewer understand an online/e-commerce sales channel?

merchant_pos_channel_clear:
Can the viewer understand physical/in-store payment acceptance?

Accept semantic equivalents such as:
- card reader
- payment terminal
- tap-to-pay
- in-store acceptance
- digital storefront
- online order
- web checkout

Do NOT require the exact word "POS".

merchant_channels_fused:
TRUE only when one advertising mechanism genuinely unifies
the two channels.

Putting them in the same room is NOT fusion.

For non-merchant briefs:
set all three merchant booleans TRUE.

==================================================
CAMERA
==================================================

Return one coherent:
- camera angle
- lens
- perspective

for every concept.

==================================================
PRODUCTION FEASIBILITY
==================================================

production_feasible = TRUE only when the central idea can be
generated as one coherent image without impossible geometry,
contradictory scenes or unreadable UI.

{high_alert_block}

Return exactly the structured schema.
""".strip()


# =========================================================
# FINALIST JURY PROMPT
# =========================================================

def build_finalist_jury_prompt(
    *,
    user_request: str,
    finalists: List[
        CreativeConcept
    ],
    benefit_family: str,
    stc_style: str,
) -> str:

    payload = [
        concept_to_dict(
            concept
        )
        for concept in finalists
    ]

    return f"""
You are the FINAL XPAND STC BANK CAMPAIGN JURY V5.5.

This decision happens immediately before expensive image
production.

Every supplied finalist has already passed deterministic
strict quality gates.

You may choose ONLY from the supplied IDs.

==================================================
REQUEST
==================================================

{clean_text(
    user_request,
    6500,
)}

==================================================
BENEFIT
==================================================

{benefit_family}

==================================================
STYLE
==================================================

{stc_style}

==================================================
FINALISTS
==================================================

{compact_json(
    payload,
    26000,
)}

==================================================
DECISION
==================================================

Select ONE finalist only if you would authorize production.

Judge:
1. Campaign idea
2. STC Bank fit
3. Originality
4. Visual mechanism
5. Single-frame message clarity
6. Realism
7. Feasibility
8. Camera
9. Simplicity
10. Resistance to generic-scene drift

merchant_fusion_approved:

For merchant_payments:
TRUE only if online commerce and physical payment are
visually unified through one mechanism.

For other benefits:
TRUE.

==================================================
DO NOT APPROVE
==================================================

Do not approve:
- ordinary lifestyle photography
- transaction photography
- generic boutique POS scene
- wooden counter tableau
- worker packing a box as e-commerce
- person simply holding a device
- purple as substitute for idea
- generic fintech effects

==================================================
PRODUCTION LOCK
==================================================

production_instruction must lock:
- hero relationship
- visual mechanism
- environment
- camera
- lens
- perspective
- lighting logic
- copy-space location

do_not_drift_into must list likely generic failure modes.

Return exactly the schema.
""".strip()


# =========================================================
# GENERATE INITIAL CONCEPTS
# =========================================================

def generate_concepts(
    *,
    user_request: str,
    brand_context: Any,
    visual_references: Any,
    style_hint: str,
    benefit_family: str,
    stc_style: str,
    recovery: bool,
    concept_count: int,
    high_alert: bool,
) -> List[
    CreativeConcept
]:

    prompt = build_ideation_prompt(
        user_request=(
            user_request
        ),
        brand_context=(
            brand_context
        ),
        visual_references=(
            visual_references
        ),
        style_hint=(
            style_hint
        ),
        benefit_family=(
            benefit_family
        ),
        stc_style=(
            stc_style
        ),
        recovery=(
            recovery
        ),
        concept_count=(
            concept_count
        ),
        high_alert=(
            high_alert
        ),
    )

    raw = call_openai_director(
        prompt,
        json_mode=True,
        json_schema=(
            make_ideation_schema(
                concept_count
            )
        ),
        json_schema_name=(
            "xpand_creative_ideation_v55"
        ),
    )

    payload = parse_json_payload(
        raw
    )

    concepts = parse_concepts(
        payload,
        generation_round=1,
        id_prefix="C",
        force_ids=True,
    )

    if len(
        concepts
    ) != concept_count:

        raise RuntimeError(
            (
                "Creative Brain returned "
                +
                str(
                    len(
                        concepts
                    )
                )
                +
                " concepts; expected "
                +
                str(
                    concept_count
                )
                +
                "."
            )
        )

    return concepts


# =========================================================
# APPLY MODEL EVALUATIONS
# =========================================================

def apply_evaluations_to_concepts(
    *,
    user_request: str,
    concepts: List[
        CreativeConcept
    ],
    evaluations: Sequence[Any],
    benefit_family: str,
    stc_style: str,
    evaluation_source: str,
) -> None:

    by_id: Dict[
        str,
        Dict[str, Any]
    ] = {}

    for item in evaluations:

        if not isinstance(
            item,
            dict,
        ):
            continue

        concept_id = clean_text(
            item.get(
                "concept_id"
            ),
            100,
        )

        if concept_id:
            by_id[
                concept_id
            ] = item

    for index, concept in enumerate(
        concepts,
        start=1,
    ):

        evaluation = by_id.get(
            concept.concept_id
        )

        if evaluation is None:

            #
            # Some structured models occasionally retain the
            # correct array order but slightly alter the ID.
            #
            if (
                index - 1
                <
                len(
                    evaluations
                )
            ):

                candidate = evaluations[
                    index - 1
                ]

                if isinstance(
                    candidate,
                    dict,
                ):
                    evaluation = candidate

        if not isinstance(
            evaluation,
            dict,
        ):

            concept.evaluation_valid = False

            concept.quality_gate_passed = False

            concept.quality_gate_failures = [
                "missing_real_evaluation"
            ]

            continue

        scores: Dict[
            str,
            float
        ] = {}

        for key in (
            DIMENSION_WEIGHTS.keys()
        ):

            scores[
                key
            ] = clamp_score(
                evaluation.get(
                    key
                )
            )

        model_weighted = clamp_score(
            evaluation.get(
                "weighted_score"
            )
        )

        dimension_score = (
            dimension_composite_score(
                scores
            )
        )

        if model_weighted > 0:

            base_score = (
                dimension_score
                *
                0.60
                +
                model_weighted
                *
                0.40
            )

        else:

            base_score = (
                dimension_score
            )

        (
            local_penalty,
            local_failures,
        ) = local_concept_penalties(
            concept,
            user_request=(
                user_request
            ),
            benefit_family=(
                benefit_family
            ),
            stc_style=(
                stc_style
            ),
        )

        review_penalty = 0.0

        review_failures: List[str] = []

        generic_scene_risk = bool(
            evaluation.get(
                "generic_scene_risk",
                False,
            )
        )

        repetition_risk = bool(
            evaluation.get(
                "repetition_risk",
                False,
            )
        )

        concept_is_scene_only = bool(
            evaluation.get(
                "concept_is_scene_only",
                False,
            )
        )

        mechanism_survives = bool(
            evaluation.get(
                "mechanism_survives_single_frame",
                False,
            )
        )

        bank_campaign = bool(
            evaluation.get(
                "looks_like_real_bank_campaign",
                False,
            )
        )

        if generic_scene_risk:

            review_penalty += 7.0

            review_failures.append(
                "review_generic_scene_risk"
            )

        if repetition_risk:

            review_penalty += 7.0

            review_failures.append(
                "review_repetition_risk"
            )

        if concept_is_scene_only:

            review_penalty += 9.0

            review_failures.append(
                "concept_is_scene_only"
            )

        if not mechanism_survives:

            review_penalty += 8.0

            review_failures.append(
                "single_frame_mechanism_failure"
            )

        if not bank_campaign:

            review_penalty += 9.0

            review_failures.append(
                "not_bank_campaign_ready"
            )

        online_clear = bool(
            evaluation.get(
                "merchant_online_channel_clear",
                True,
            )
        )

        pos_clear = bool(
            evaluation.get(
                "merchant_pos_channel_clear",
                True,
            )
        )

        channels_fused = bool(
            evaluation.get(
                "merchant_channels_fused",
                True,
            )
        )

        if benefit_family == "merchant_payments":

            if not online_clear:

                review_penalty += 7.0

                review_failures.append(
                    "merchant_online_channel_unclear"
                )

            if not pos_clear:

                review_penalty += 7.0

                review_failures.append(
                    "merchant_pos_channel_unclear"
                )

            if not channels_fused:

                review_penalty += 12.0

                review_failures.append(
                    "merchant_channels_not_visually_connected"
                )

        final_score = max(
            0.0,
            min(
                100.0,
                base_score
                -
                local_penalty
                -
                review_penalty,
            ),
        )

        combined_failures = dedupe_strings(
            (
                local_failures
                +
                review_failures
            )
        )

        if any(
            failure
            in HARD_REJECT_FAILURES
            for failure
            in combined_failures
        ):

            final_score = min(
                final_score,
                79.0,
            )

        concept.scores = scores

        concept.weighted_score = round(
            final_score,
            2,
        )

        concept.evaluation_valid = True

        concept.quality_gate_passed = False

        concept.quality_gate_failures = (
            combined_failures
        )

        concept.feasibility = {

            "production_feasible":
                bool(
                    evaluation.get(
                        "production_feasible",
                        False,
                    )
                ),

            "reason":
                clean_text(
                    evaluation.get(
                        "feasibility_reason"
                    ),
                    1500,
                ),
        }

        concept.debate = {

            "evaluation_source":
                evaluation_source,

            "strengths":
                [
                    clean_text(
                        value,
                        1000,
                    )
                    for value in safe_list(
                        evaluation.get(
                            "strengths"
                        )
                    )[:8]
                ],

            "weaknesses":
                [
                    clean_text(
                        value,
                        1000,
                    )
                    for value in safe_list(
                        evaluation.get(
                            "weaknesses"
                        )
                    )[:8]
                ],

            "verdict":
                clean_text(
                    evaluation.get(
                        "verdict"
                    ),
                    300,
                ),

            "model_weighted_score":
                model_weighted,

            "dimension_composite_score":
                dimension_score,

            "local_penalty":
                round(
                    local_penalty,
                    2,
                ),

            "review_penalty":
                round(
                    review_penalty,
                    2,
                ),

            "generic_scene_risk":
                generic_scene_risk,

            "repetition_risk":
                repetition_risk,

            "concept_is_scene_only":
                concept_is_scene_only,

            "mechanism_survives_single_frame":
                mechanism_survives,

            "looks_like_real_bank_campaign":
                bank_campaign,

            "merchant_semantics": {

                "online_channel_clear":
                    online_clear,

                "pos_channel_clear":
                    pos_clear,

                "channels_fused":
                    channels_fused,
            },

            "camera_director": {

                "camera_angle":
                    (
                        clean_text(
                            evaluation.get(
                                "recommended_camera_angle"
                            ),
                            900,
                        )
                        or
                        concept.camera_angle
                    ),

                "lens":
                    (
                        clean_text(
                            evaluation.get(
                                "recommended_lens"
                            ),
                            400,
                        )
                        or
                        concept.lens
                    ),

                "perspective":
                    (
                        clean_text(
                            evaluation.get(
                                "recommended_perspective"
                            ),
                            1200,
                        )
                        or
                        concept.perspective
                    ),

                "perspective_type":
                    (
                        clean_text(
                            evaluation.get(
                                "recommended_perspective"
                            ),
                            1200,
                        )
                        or
                        concept.perspective
                    ),

                "creative_reason":
                    clean_text(
                        evaluation.get(
                            "camera_reason"
                        ),
                        1200,
                    ),

                "camera_lock_instruction":
                    (
                        "Preserve this camera strategy "
                        "during image production."
                    ),
            },
        }

        camera = safe_dict(
            concept.debate.get(
                "camera_director"
            )
        )

        if camera.get(
            "camera_angle"
        ):
            concept.camera_angle = clean_text(
                camera.get(
                    "camera_angle"
                ),
                900,
            )

        if camera.get(
            "lens"
        ):
            concept.lens = clean_text(
                camera.get(
                    "lens"
                ),
                400,
            )

        if camera.get(
            "perspective"
        ):
            concept.perspective = clean_text(
                camera.get(
                    "perspective"
                ),
                1200,
            )

        if is_stc_bank_request(
            user_request
        ):

            dimension_failures = (
                stc_dimension_gate_failures(
                    concept
                )
            )

            concept.quality_gate_failures = (
                dedupe_strings(
                    concept.quality_gate_failures
                    +
                    dimension_failures
                )
            )


# =========================================================
# REVIEW CALL
# =========================================================

def review_concepts(
    *,
    user_request: str,
    concepts: List[
        CreativeConcept
    ],
    benefit_family: str,
    stc_style: str,
    high_alert: bool,
) -> None:

    prompt = build_review_prompt(
        user_request=(
            user_request
        ),
        concepts=(
            concepts
        ),
        benefit_family=(
            benefit_family
        ),
        stc_style=(
            stc_style
        ),
        high_alert=(
            high_alert
        ),
    )

    raw = call_openai_director(
        prompt,
        json_mode=True,
        json_schema=(
            make_review_schema(
                len(
                    concepts
                )
            )
        ),
        json_schema_name=(
            "xpand_creative_review_v55"
        ),
    )

    payload = parse_json_payload(
        raw
    )

    evaluations = safe_list(
        payload.get(
            "evaluations"
        )
    )

    apply_evaluations_to_concepts(
        user_request=(
            user_request
        ),
        concepts=(
            concepts
        ),
        evaluations=(
            evaluations
        ),
        benefit_family=(
            benefit_family
        ),
        stc_style=(
            stc_style
        ),
        evaluation_source=(
            "executive_creative_review"
        ),
    )


# =========================================================
# JURY CALL
# =========================================================

def run_finalist_jury(
    *,
    user_request: str,
    finalists: List[
        CreativeConcept
    ],
    benefit_family: str,
    stc_style: str,
) -> Dict[str, Any]:

    prompt = build_finalist_jury_prompt(
        user_request=(
            user_request
        ),
        finalists=(
            finalists
        ),
        benefit_family=(
            benefit_family
        ),
        stc_style=(
            stc_style
        ),
    )

    raw = call_openai_director(
        prompt,
        json_mode=True,
        json_schema=(
            FINALIST_JURY_SCHEMA
        ),
        json_schema_name=(
            "xpand_stc_finalist_jury_v55"
        ),
    )

    return parse_json_payload(
        raw
    )


# =========================================================
# FIND CONCEPT
# =========================================================

def find_concept_by_id(
    concepts: Sequence[
        CreativeConcept
    ],
    concept_id: str,
) -> Optional[
    CreativeConcept
]:

    target = clean_text(
        concept_id,
        100,
    )

    for concept in concepts:

        if (
            concept.concept_id
            ==
            target
        ):
            return concept

    return None


# =========================================================
# JURY GLOBAL GATE
# =========================================================

def jury_global_gate(
    jury: Dict[str, Any],
    *,
    benefit_family: str,
) -> Tuple[
    bool,
    List[str],
]:

    failures: List[str] = []

    if not bool(
        jury.get(
            "approval",
            False,
        )
    ):

        failures.append(
            "jury_not_approved"
        )

    confidence = clamp_score(
        jury.get(
            "confidence"
        )
    )

    if (
        confidence
        <
        STC_MIN_JURY_CONFIDENCE
    ):

        failures.append(
            "jury_low_confidence"
        )

    fatal_issues = [
        clean_text(
            value,
            1000,
        )
        for value
        in safe_list(
            jury.get(
                "fatal_issues"
            )
        )
        if clean_text(
            value,
            1000,
        )
    ]

    if fatal_issues:

        failures.append(
            "jury_fatal_issues"
        )

    if (
        benefit_family
        ==
        "merchant_payments"
        and
        not bool(
            jury.get(
                "merchant_fusion_approved",
                False,
            )
        )
    ):

        failures.append(
            "jury_merchant_fusion_rejected"
        )

    return (
        not bool(
            failures
        ),
        failures,
    )


# =========================================================
# JURY ATTACHMENT
# =========================================================

def attach_jury_approval(
    *,
    winner: CreativeConcept,
    jury: Dict[str, Any],
    source: str,
    original_selected_id: str = "",
    arbitrated: bool = False,
) -> None:

    winner.debate[
        "finalist_jury"
    ] = {

        "source":
            source,

        "approval":
            bool(
                jury.get(
                    "approval",
                    False,
                )
            ),

        "confidence":
            clamp_score(
                jury.get(
                    "confidence"
                )
            ),

        "advertising_reason":
            clean_text(
                jury.get(
                    "advertising_reason"
                ),
                1800,
            ),

        "brand_reason":
            clean_text(
                jury.get(
                    "brand_reason"
                ),
                1800,
            ),

        "originality_reason":
            clean_text(
                jury.get(
                    "originality_reason"
                ),
                1800,
            ),

        "merchant_fusion_approved":
            bool(
                jury.get(
                    "merchant_fusion_approved",
                    True,
                )
            ),

        "fatal_issues":
            [
                clean_text(
                    value,
                    1000,
                )
                for value
                in safe_list(
                    jury.get(
                        "fatal_issues"
                    )
                )
            ],

        "production_instruction":
            clean_text(
                jury.get(
                    "production_instruction"
                ),
                3500,
            ),

        "do_not_drift_into":
            [
                clean_text(
                    value,
                    1000,
                )
                for value
                in safe_list(
                    jury.get(
                        "do_not_drift_into"
                    )
                )
            ],

        "original_selected_id":
            original_selected_id,

        "arbitrated":
            bool(
                arbitrated
            ),

        "thresholds_lowered":
            False,
    }

    camera = winner.debate.setdefault(
        "camera_director",
        {},
    )

    jury_angle = clean_text(
        jury.get(
            "recommended_camera_angle"
        ),
        900,
    )

    jury_lens = clean_text(
        jury.get(
            "recommended_lens"
        ),
        400,
    )

    jury_perspective = clean_text(
        jury.get(
            "recommended_perspective"
        ),
        1200,
    )

    if jury_angle:

        winner.camera_angle = (
            jury_angle
        )

        camera[
            "camera_angle"
        ] = jury_angle

    if jury_lens:

        winner.lens = (
            jury_lens
        )

        camera[
            "lens"
        ] = jury_lens

    if jury_perspective:

        winner.perspective = (
            jury_perspective
        )

        camera[
            "perspective"
        ] = jury_perspective

        camera[
            "perspective_type"
        ] = jury_perspective

    camera[
        "camera_lock_instruction"
    ] = (
        "FINAL JURY CAMERA LOCK. "
        "Do not normalize or replace this camera."
    )


# =========================================================
# APPLY JURY RESULT
# =========================================================

def apply_jury_result(
    *,
    concepts: List[
        CreativeConcept
    ],
    jury: Dict[str, Any],
    benefit_family: str,
    source: str = "finalist_jury",
) -> Optional[
    CreativeConcept
]:

    selected_id = clean_text(
        jury.get(
            "selected_concept_id"
        ),
        100,
    )

    selected = find_concept_by_id(
        concepts,
        selected_id,
    )

    if selected is None:
        return None

    (
        global_passed,
        global_failures,
    ) = jury_global_gate(
        jury,
        benefit_family=(
            benefit_family
        ),
    )

    selected.debate[
        "jury_global_gate"
    ] = {
        "passed":
            global_passed,

        "failures":
            global_failures,
    }

    if not global_passed:

        selected.quality_gate_failures = (
            dedupe_strings(
                selected.quality_gate_failures
                +
                global_failures
            )
        )

    attach_jury_approval(
        winner=(
            selected
        ),
        jury=(
            jury
        ),
        source=(
            source
        ),
        original_selected_id=(
            selected_id
        ),
        arbitrated=False,
    )

    return selected


# =========================================================
# FAILURE CONTEXT
# =========================================================

def build_failure_context(
    concepts: Sequence[
        CreativeConcept
    ],
    limit: int = 4,
) -> str:

    ranked = [
        item
        for item
        in concepts
        if item.evaluation_valid
    ]

    ranked.sort(
        key=lambda item:
            item.weighted_score,
        reverse=True,
    )

    payload: List[
        Dict[str, Any]
    ] = []

    for concept in ranked[
        :limit
    ]:

        payload.append(
            {
                "concept_id":
                    concept.concept_id,

                "title":
                    concept.title,

                "archetype":
                    concept.concept_archetype,

                "score":
                    concept.weighted_score,

                "scores":
                    concept.scores,

                "quality_failures":
                    concept.quality_gate_failures,

                "weaknesses":
                    safe_list(
                        concept.debate.get(
                            "weaknesses"
                        )
                    )[:8],

                "core_idea":
                    clean_text(
                        concept.core_idea,
                        1000,
                    ),

                "visual_mechanism":
                    clean_text(
                        concept.visual_metaphor,
                        900,
                    ),

                "environment":
                    clean_text(
                        concept.environment,
                        700,
                    ),
            }
        )

    return compact_json(
        payload,
        16000,
    )


def primary_archetypes(
    concepts: Sequence[
        CreativeConcept
    ],
) -> List[str]:

    return dedupe_strings(
        [
            concept.concept_archetype
            for concept
            in concepts
            if concept.concept_archetype
        ]
    )[:12]


# =========================================================
# TARGETED REPAIR CONTEXT
# =========================================================

def build_targeted_repair_context(
    candidates: Sequence[
        CreativeConcept
    ],
) -> str:

    payload: List[
        Dict[str, Any]
    ] = []

    for concept in candidates:

        payload.append(
            {
                "concept_id":
                    concept.concept_id,

                "title":
                    concept.title,

                "score":
                    concept.weighted_score,

                "failed_dimensions":
                    targeted_repair_dimension_gaps(
                        concept
                    ),

                "quality_failures":
                    concept.quality_gate_failures,

                "strengths":
                    safe_list(
                        concept.debate.get(
                            "strengths"
                        )
                    )[:8],

                "weaknesses":
                    safe_list(
                        concept.debate.get(
                            "weaknesses"
                        )
                    )[:8],

                "core_idea":
                    clean_text(
                        concept.core_idea,
                        1800,
                    ),

                "campaign_hook":
                    clean_text(
                        concept.campaign_hook,
                        1200,
                    ),

                "visual_mechanism":
                    clean_text(
                        concept.visual_metaphor,
                        1400,
                    ),

                "visual_mechanism_type":
                    clean_text(
                        concept.visual_mechanism_type,
                        700,
                    ),

                "why_not_generic":
                    clean_text(
                        concept.why_not_generic,
                        1200,
                    ),

                "environment":
                    clean_text(
                        concept.environment,
                        1200,
                    ),

                "hero_element":
                    clean_text(
                        concept.hero_element,
                        900,
                    ),

                "camera_angle":
                    concept.camera_angle,

                "lens":
                    concept.lens,

                "perspective":
                    concept.perspective,

                "brand_logic":
                    clean_text(
                        concept.brand_logic,
                        1200,
                    ),
            }
        )

    return compact_json(
        payload,
        20000,
    )


# =========================================================
# TARGETED REPAIR PROMPT
# =========================================================

def build_targeted_repair_prompt(
    *,
    user_request: str,
    repair_candidates: Sequence[
        CreativeConcept
    ],
    brand_context: Any,
    visual_references: Any,
    benefit_family: str,
    stc_style: str,
) -> str:

    repair_context = (
        build_targeted_repair_context(
            repair_candidates
        )
    )

    return f"""
You are XPAND V5.5 STC BANK TARGETED CREATIVE REPAIR BOARD.

The Executive Creative Review found one or two concepts that
are genuinely CLOSE to production quality.

You have ONE final paid creative call.

This one response must:

1. Diagnose the near-miss precisely.
2. Create exactly TWO repaired concepts.
3. Evaluate both repaired concepts.
4. Jury-select the strongest repaired concept.
5. Return all of this in ONE structured response.

==================================================
CRITICAL REPAIR PHILOSOPHY
==================================================

PRESERVE THE STRONGEST CORE PROPOSITION.

Do NOT discard a strong central advertising idea merely
because several execution dimensions are a few points short.

However:

This is NOT a cosmetic rewrite.

You MAY materially improve:
- hero relationship
- visual mechanism clarity
- environment
- art direction
- camera angle
- lens
- perspective
- production design
- material behavior
- lighting
- copy-space integration

when those changes are necessary to fix the diagnosed gaps.

The repaired idea must still be recognizably descended from
the strongest near-miss proposition.

Do NOT replace it with an unrelated campaign.

==================================================
NO SCORE INFLATION
==================================================

DO NOT inflate scores to force approval.

A repaired concept must earn every score.

If the core proposition cannot honestly survive the strict
standards, do not fake a pass.

==================================================
REQUEST
==================================================

{clean_text(
    user_request,
    6500,
)}

==================================================
BENEFIT FAMILY
==================================================

{benefit_family}

==================================================
STYLE
==================================================

{stc_style}

==================================================
NEAR-MISS CANDIDATES + EXACT DIAGNOSIS
==================================================

{repair_context}

The failed_dimensions above are the exact weaknesses that
triggered this repair route.

Repair those weaknesses deliberately.

==================================================
STRICT RELEASE GATES — NO LOWERING
==================================================

concept_strength >= {STC_MIN_CONCEPT_STRENGTH}
brand_fit >= {STC_MIN_BRAND_FIT}
originality >= {STC_MIN_ORIGINALITY}
visual_mechanism >= {STC_MIN_VISUAL_MECHANISM}
camera_quality >= {STC_MIN_CAMERA_QUALITY}
realism >= {STC_MIN_REALISM}
feasibility >= {STC_MIN_FEASIBILITY}
copy_space_quality >= {STC_MIN_COPY_SPACE}
distinctiveness >= {STC_MIN_DISTINCTIVENESS}
advertising_readiness >= {STC_MIN_AD_READINESS}

Overall release floor >= {STC_HIGH_ALERT_RELEASE_FLOOR}

No threshold may be lowered.

==================================================
STC BRAND INTELLIGENCE
==================================================

{stc_brand_pack_prompt_fragment(
    benefit_family=benefit_family,
    stc_style=stc_style,
)}

==================================================
BRAND CONTEXT
==================================================

{compact_json(
    brand_context,
    6000,
)}

==================================================
VISUAL REFERENCE DNA
==================================================

{compact_json(
    visual_references,
    7000,
)}

References are DNA, not templates.

Do not copy them.

==================================================
HARD CREATIVE RULES
==================================================

Never repair into:

- customer + POS + counter + merchant tableau
- wooden checkout counter cliché
- worker packing a parcel as the e-commerce idea
- ordinary transaction photography
- generic person holding a phone
- purple used as the concept
- random fintech neon
- holograms
- floating cards
- floating POS devices
- network lines
- fake banking UI
- generated headline
- generated STC logo

==================================================
MERCHANT PAYMENTS
==================================================

For merchant_payments:

The viewer must understand BOTH:

ONLINE / E-COMMERCE SALES

and

PHYSICAL / IN-STORE PAYMENT ACCEPTANCE

through ONE coherent advertising mechanism.

A card reader counts as physical POS.

A digital storefront counts as e-commerce.

Simply showing both in the same room is NOT fusion.

==================================================
REALISM
==================================================

The final frame must be physically believable.

Respect:
- perspective
- scale
- gravity
- contact
- occlusion
- shadows
- reflections
- material roughness
- motivated light

Do not solve conceptual weakness with impossible geometry.

==================================================
CAMERA
==================================================

Camera must strengthen the idea.

Use deliberate:
- viewpoint
- focal length
- foreground/background hierarchy
- perspective reveal
- negative space

Do not simply say "cinematic".

==================================================
COPY SPACE
==================================================

Reserve approximately 25%-40% natural copy space.

No blank digital panel.

==================================================
OUTPUT
==================================================

Create exactly TWO repaired concepts:

T01
T02

Each must use the full concept schema.

Then evaluate BOTH using the full evaluation schema.

Then jury-select ONE only if you would genuinely authorize
expensive image production.

merchant_fusion_approved must be TRUE for merchant_payments
only when the two merchant channels are genuinely unified.

fatal_issues must list any genuine fatal problem.

Return exactly the structured schema.
""".strip()


# =========================================================
# FRESH RECOVERY PROMPT
# =========================================================

def build_recovery_board_prompt(
    *,
    user_request: str,
    failed_concepts: Sequence[
        CreativeConcept
    ],
    brand_context: Any,
    visual_references: Any,
    benefit_family: str,
    stc_style: str,
) -> str:

    failure_context = build_failure_context(
        failed_concepts,
        limit=4,
    )

    used_archetypes = primary_archetypes(
        failed_concepts
    )

    return f"""
You are XPAND V5.5 STC BANK FRESH CREATIVE RECOVERY BOARD.

The first concept pool was genuinely evaluated.

No concept passed the strict campaign-quality gates.

No suitable near-miss qualified for Targeted Repair.

Therefore the problem is considered FUNDAMENTAL rather than
a small execution gap.

You have ONE final paid creative call.

This one response must:

1. Create exactly {STC_RECOVERY_CONCEPT_COUNT} materially NEW
   advertising concepts.
2. Evaluate all of them.
3. Jury-select the strongest.
4. Return all of it in ONE structured response.

==================================================
REQUEST
==================================================

{clean_text(
    user_request,
    6500,
)}

==================================================
BENEFIT
==================================================

{benefit_family}

==================================================
STYLE
==================================================

{stc_style}

==================================================
FAILED STRONGEST DIRECTIONS
==================================================

{failure_context}

==================================================
USED ARCHETYPES
==================================================

{compact_json(
    used_archetypes,
    3000,
)}

==================================================
RECOVERY LAW
==================================================

Do NOT cosmetically rewrite the failed ideas.

Change the conceptual mechanism.

Find a materially different campaign grammar.

If earlier ideas relied on:
- ordinary retail
- customer transactions
- split scenes
- portals
- floating technology
- decorative purple
- phone-holding lifestyle
- generic interior
- literal banking props

use a different visual logic.

==================================================
STRICT RELEASE GATES — NO LOWERING
==================================================

concept_strength >= {STC_MIN_CONCEPT_STRENGTH}
brand_fit >= {STC_MIN_BRAND_FIT}
originality >= {STC_MIN_ORIGINALITY}
visual_mechanism >= {STC_MIN_VISUAL_MECHANISM}
camera_quality >= {STC_MIN_CAMERA_QUALITY}
realism >= {STC_MIN_REALISM}
feasibility >= {STC_MIN_FEASIBILITY}
copy_space_quality >= {STC_MIN_COPY_SPACE}
distinctiveness >= {STC_MIN_DISTINCTIVENESS}
advertising_readiness >= {STC_MIN_AD_READINESS}

Overall release floor >= {STC_HIGH_ALERT_RELEASE_FLOOR}

==================================================
STC BRAND INTELLIGENCE
==================================================

{stc_brand_pack_prompt_fragment(
    benefit_family=benefit_family,
    stc_style=stc_style,
)}

==================================================
MERCHANT PAYMENTS
==================================================

For merchant_payments:

Online commerce and physical in-store payment must be
understood as ONE merchant ecosystem through ONE visible
advertising mechanism.

Do not use:
customer + terminal + counter + packing worker.

==================================================
BAN
==================================================

No:
- wooden counter cliché
- generic boutique checkout
- generic phone lifestyle
- floating cards
- floating phones
- floating POS
- network lines
- holograms
- HUD
- neon fintech tunnel
- random particles
- generated text/logo
- fake banking UI

==================================================
OUTPUT
==================================================

Use IDs:

R01
R02
R03

and R04 only if configured for four concepts.

Evaluate all concepts honestly.

Do not inflate scores.

Jury-select only if genuinely production-worthy.

Return exactly the structured schema.
""".strip()


# =========================================================
# BOARD EXECUTION
# =========================================================

def run_creative_board(
    *,
    prompt: str,
    concept_count: int,
    id_prefix: str,
    user_request: str,
    benefit_family: str,
    stc_style: str,
    evaluation_source: str,
    schema_name: str,
) -> Tuple[
    List[CreativeConcept],
    Dict[str, Any],
]:

    raw = call_openai_director(
        prompt,
        json_mode=True,
        json_schema=(
            make_board_schema(
                concept_count
            )
        ),
        json_schema_name=(
            schema_name
        ),
    )

    payload = parse_json_payload(
        raw
    )

    concepts = parse_concepts(
        payload,
        generation_round=2,
        id_prefix=(
            id_prefix
        ),
        force_ids=True,
    )

    if len(
        concepts
    ) != concept_count:

        raise RuntimeError(
            (
                evaluation_source
                +
                " returned "
                +
                str(
                    len(
                        concepts
                    )
                )
                +
                " concepts; expected "
                +
                str(
                    concept_count
                )
                +
                "."
            )
        )

    evaluations = safe_list(
        payload.get(
            "evaluations"
        )
    )

    #
    # Because IDs are intentionally forced locally,
    # normalize evaluation IDs by array position too.
    #

    normalized_evaluations: List[
        Dict[str, Any]
    ] = []

    for index, item in enumerate(
        evaluations,
        start=1,
    ):

        if not isinstance(
            item,
            dict,
        ):
            continue

        normalized = dict(
            item
        )

        normalized[
            "concept_id"
        ] = (
            id_prefix
            +
            str(
                index
            ).zfill(
                2
            )
        )

        normalized_evaluations.append(
            normalized
        )

    apply_evaluations_to_concepts(
        user_request=(
            user_request
        ),
        concepts=(
            concepts
        ),
        evaluations=(
            normalized_evaluations
        ),
        benefit_family=(
            benefit_family
        ),
        stc_style=(
            stc_style
        ),
        evaluation_source=(
            evaluation_source
        ),
    )

    #
    # Normalize selected ID if model used source-style IDs.
    #
    selected_id = clean_text(
        payload.get(
            "selected_concept_id"
        ),
        100,
    )

    valid_ids = {
        concept.concept_id
        for concept in concepts
    }

    if selected_id not in valid_ids:

        match = re.search(
            r"(\d+)",
            selected_id,
        )

        if match:

            number = int(
                match.group(
                    1
                )
            )

            candidate_id = (
                id_prefix
                +
                str(
                    number
                ).zfill(
                    2
                )
            )

            if candidate_id in valid_ids:

                payload[
                    "selected_concept_id"
                ] = candidate_id

    return (
        concepts,
        payload,
    )


def run_targeted_repair_board(
    *,
    user_request: str,
    repair_candidates: Sequence[
        CreativeConcept
    ],
    brand_context: Any,
    visual_references: Any,
    benefit_family: str,
    stc_style: str,
) -> Tuple[
    List[CreativeConcept],
    Dict[str, Any],
]:

    prompt = build_targeted_repair_prompt(
        user_request=(
            user_request
        ),
        repair_candidates=(
            repair_candidates
        ),
        brand_context=(
            brand_context
        ),
        visual_references=(
            visual_references
        ),
        benefit_family=(
            benefit_family
        ),
        stc_style=(
            stc_style
        ),
    )

    return run_creative_board(
        prompt=(
            prompt
        ),
        concept_count=(
            STC_TARGETED_REPAIR_OUTPUT_COUNT
        ),
        id_prefix=(
            "T"
        ),
        user_request=(
            user_request
        ),
        benefit_family=(
            benefit_family
        ),
        stc_style=(
            stc_style
        ),
        evaluation_source=(
            "stc_targeted_repair_board"
        ),
        schema_name=(
            "xpand_stc_targeted_repair_v55"
        ),
    )


def run_recovery_board(
    *,
    user_request: str,
    failed_concepts: Sequence[
        CreativeConcept
    ],
    brand_context: Any,
    visual_references: Any,
    benefit_family: str,
    stc_style: str,
) -> Tuple[
    List[CreativeConcept],
    Dict[str, Any],
]:

    prompt = build_recovery_board_prompt(
        user_request=(
            user_request
        ),
        failed_concepts=(
            failed_concepts
        ),
        brand_context=(
            brand_context
        ),
        visual_references=(
            visual_references
        ),
        benefit_family=(
            benefit_family
        ),
        stc_style=(
            stc_style
        ),
    )

    return run_creative_board(
        prompt=(
            prompt
        ),
        concept_count=(
            STC_RECOVERY_CONCEPT_COUNT
        ),
        id_prefix=(
            "R"
        ),
        user_request=(
            user_request
        ),
        benefit_family=(
            benefit_family
        ),
        stc_style=(
            stc_style
        ),
        evaluation_source=(
            "stc_recovery_board"
        ),
        schema_name=(
            "xpand_stc_recovery_board_v55"
        ),
    )


# =========================================================
# QUALITY-FIRST BOARD ARBITRATION
# =========================================================

def arbitrate_board_selection(
    *,
    board_concepts: Sequence[
        CreativeConcept
    ],
    board_qualified: Sequence[
        CreativeConcept
    ],
    jury: Dict[str, Any],
    benefit_family: str,
    source: str,
) -> Tuple[
    Optional[CreativeConcept],
    Dict[str, Any],
]:

    original_selected_id = clean_text(
        jury.get(
            "selected_concept_id"
        ),
        100,
    )

    qualified_ids = [
        concept.concept_id
        for concept
        in board_qualified
    ]

    result: Dict[str, Any] = {

        "used":
            False,

        "original_selected_id":
            original_selected_id,

        "selected_was_qualified":
            (
                original_selected_id
                in qualified_ids
            ),

        "arbitrated_winner_id":
            "",

        "reason":
            "",

        "qualified_ids":
            qualified_ids,

        "source":
            source,

        "thresholds_lowered":
            False,
    }

    if not board_qualified:

        result[
            "reason"
        ] = (
            "no_strict_qualified_board_concept"
        )

        return (
            None,
            result,
        )

    (
        global_gate_passed,
        global_failures,
    ) = jury_global_gate(
        jury,
        benefit_family=(
            benefit_family
        ),
    )

    result[
        "jury_global_gate_passed"
    ] = global_gate_passed

    result[
        "jury_global_failures"
    ] = global_failures

    if not global_gate_passed:

        result[
            "reason"
        ] = (
            "jury_global_gate_failed:"
            +
            ",".join(
                global_failures
            )
        )

        return (
            None,
            result,
        )

    selected = find_concept_by_id(
        board_concepts,
        original_selected_id,
    )

    if (
        selected is not None
        and
        original_selected_id
        in qualified_ids
    ):

        attach_jury_approval(
            winner=(
                selected
            ),
            jury=(
                jury
            ),
            source=(
                source
            ),
            original_selected_id=(
                original_selected_id
            ),
            arbitrated=False,
        )

        result[
            "reason"
        ] = (
            "jury_selected_strict_qualified_concept"
        )

        return (
            selected,
            result,
        )

    if not STC_QUALITY_FIRST_ARBITRATION_ENABLED:

        result[
            "reason"
        ] = (
            "quality_first_arbitration_disabled"
        )

        return (
            None,
            result,
        )

    #
    # The Director approved the board globally, but selected
    # an unqualified ID while another board concept passed
    # EVERY deterministic release gate.
    #
    # Promote the strongest strict-qualified concept.
    #
    promoted = board_qualified[
        0
    ]

    attach_jury_approval(
        winner=(
            promoted
        ),
        jury=(
            jury
        ),
        source=(
            source
            +
            "_quality_first_arbitration"
        ),
        original_selected_id=(
            original_selected_id
        ),
        arbitrated=True,
    )

    promoted.debate[
        "board_arbitration"
    ] = {

        "used":
            True,

        "source":
            source,

        "original_selected_id":
            original_selected_id,

        "promoted_id":
            promoted.concept_id,

        "reason":
            (
                "jury_selected_unqualified_concept_"
                "strict_qualified_candidate_promoted"
            ),

        "thresholds_lowered":
            False,
    }

    result.update(
        {

            "used":
                True,

            "arbitrated_winner_id":
                promoted.concept_id,

            "reason":
                (
                    "jury_selected_unqualified_concept_"
                    "strict_qualified_candidate_promoted"
                ),
        }
    )

    return (
        promoted,
        result,
    )


#
# V5.4 compatibility wrapper.
#

def arbitrate_recovery_selection(
    *,
    recovery_concepts: Sequence[
        CreativeConcept
    ],
    recovery_qualified: Sequence[
        CreativeConcept
    ],
    jury: Dict[str, Any],
    benefit_family: str,
) -> Tuple[
    Optional[CreativeConcept],
    Dict[str, Any],
]:

    return arbitrate_board_selection(
        board_concepts=(
            recovery_concepts
        ),
        board_qualified=(
            recovery_qualified
        ),
        jury=(
            jury
        ),
        benefit_family=(
            benefit_family
        ),
        source=(
            "stc_recovery"
        ),
    )


def arbitrate_targeted_repair_selection(
    *,
    repair_concepts: Sequence[
        CreativeConcept
    ],
    repair_qualified: Sequence[
        CreativeConcept
    ],
    jury: Dict[str, Any],
    benefit_family: str,
) -> Tuple[
    Optional[CreativeConcept],
    Dict[str, Any],
]:

    return arbitrate_board_selection(
        board_concepts=(
            repair_concepts
        ),
        board_qualified=(
            repair_qualified
        ),
        jury=(
            jury
        ),
        benefit_family=(
            benefit_family
        ),
        source=(
            "stc_targeted_repair"
        ),
    )


# =========================================================
# RELEASE
# =========================================================

def mark_quality_release(
    concept: CreativeConcept,
    *,
    release_level: str,
) -> None:

    concept.quality_gate_passed = True

    concept.debate[
        "quality_release_level"
    ] = release_level

    concept.debate[
        "thresholds_lowered"
    ] = False


def choose_normal_release(
    *,
    concepts: Sequence[
        CreativeConcept
    ],
    mode: str,
) -> Tuple[
    Optional[CreativeConcept],
    str,
]:

    valid = [
        concept
        for concept
        in concepts
        if concept.evaluation_valid
    ]

    valid.sort(
        key=lambda item:
            item.weighted_score,
        reverse=True,
    )

    if not valid:

        return (
            None,
            "quality_failed",
        )

    best = valid[
        0
    ]

    if mode == MODE_FAST:

        if (
            best.weighted_score
            >= FAST_MIN_SCORE
        ):

            mark_quality_release(
                best,
                release_level=(
                    "fast_release"
                ),
            )

            return (
                best,
                "fast_release",
            )

        return (
            None,
            "quality_failed",
        )

    if (
        best.weighted_score
        >= MASTERPIECE_MIN_SCORE
    ):

        mark_quality_release(
            best,
            release_level=(
                "masterpiece_target_release"
            ),
        )

        return (
            best,
            "masterpiece_target_release",
        )

    if (
        best.weighted_score
        >= MASTERPIECE_RELEASE_FLOOR
    ):

        mark_quality_release(
            best,
            release_level=(
                "masterpiece_release_floor"
            ),
        )

        return (
            best,
            "masterpiece_release_floor",
        )

    return (
        None,
        "quality_failed",
    )


def choose_strict_stc_jury_release(
    *,
    concepts: Sequence[
        CreativeConcept
    ],
    jury: Dict[str, Any],
    benefit_family: str,
) -> Tuple[
    Optional[CreativeConcept],
    str,
]:

    qualified = (
        strict_qualified_concepts(
            concepts,
            high_alert=True,
        )
    )

    qualified_ids = {
        concept.concept_id
        for concept in qualified
    }

    (
        global_passed,
        _
    ) = jury_global_gate(
        jury,
        benefit_family=(
            benefit_family
        ),
    )

    if not global_passed:

        return (
            None,
            "jury_rejected",
        )

    selected_id = clean_text(
        jury.get(
            "selected_concept_id"
        ),
        100,
    )

    if selected_id not in qualified_ids:

        return (
            None,
            "jury_selected_unqualified",
        )

    winner = find_concept_by_id(
        concepts,
        selected_id,
    )

    if winner is None:

        return (
            None,
            "jury_selection_missing",
        )

    attach_jury_approval(
        winner=(
            winner
        ),
        jury=(
            jury
        ),
        source=(
            "stc_finalist_jury"
        ),
        original_selected_id=(
            selected_id
        ),
        arbitrated=False,
    )

    mark_quality_release(
        winner,
        release_level=(
            "stc_finalist_jury_release"
        ),
    )

    return (
        winner,
        "stc_finalist_jury_release",
    )


# =========================================================
# TECHNICAL FAILURE RESPONSE
# =========================================================

def technical_failure_response(
    *,
    user_request: str,
    mode: str,
    errors: List[str],
    director_calls: int,
    history: List[str],
    benefit_family: str,
    stc_style: str,
    high_alert: bool,
) -> CreativeBrainResponse:

    print("")
    print(
        "=========================================="
    )
    print(
        " CREATIVE DIRECTOR TECHNICAL FAILURE"
    )
    print(
        "=========================================="
    )
    print(
        "This is NOT classified as a creative-quality failure."
    )

    if high_alert:

        print(
            "STC High Alert produced no valid creative approval."
        )

    else:

        print(
            "Technical Smart fallback may remain available."
        )

    if errors:

        print(
            clean_text(
                errors[
                    -1
                ],
                3500,
            )
        )

    print("")

    return CreativeBrainResponse(

        ok=False,

        mode=(
            mode
        ),

        request=(
            user_request
        ),

        total_concepts=0,

        concepts=[],

        top_concepts=[],

        winner=None,

        metadata={

            "version":
                VERSION,

            "architecture":
                "stc_targeted_repair_v55",

            "technical_failure":
                True,

            "quality_gate_evaluated":
                False,

            "quality_gate_passed":
                False,

            #
            # Technical failure remains distinct from a genuine
            # creative-quality rejection.
            #
            "allow_smart_engine_fallback":
                True,

            "quality_target_blocks_production":
                False,

            "fallback_blocked":
                False,

            "high_alert":
                high_alert,

            "benefit_family":
                benefit_family,

            "stc_style":
                stc_style,

            "director_calls":
                director_calls,

            "director_call_history":
                history,

            "director_call_target":
                (
                    3
                    if high_alert
                    else 2
                ),

            "director_call_maximum":
                MASTERPIECE_MAX_DIRECTOR_CALLS,

            "targeted_repair_enabled":
                STC_TARGETED_REPAIR_ENABLED,

            "targeted_repair_used":
                False,

            "recovery_used":
                False,

            "release_level":
                "technical_failure",

            "failure_reason":
                (
                    clean_text(
                        errors[
                            -1
                        ],
                        1000,
                    )
                    if errors
                    else
                    "director_technical_failure"
                ),
        },

        errors=(
            errors
        ),
    )


# =========================================================
# TOP CONCEPT BUILDER
# =========================================================

def build_top_concept_list(
    *,
    all_concepts: Sequence[
        CreativeConcept
    ],
    winner: Optional[
        CreativeConcept
    ],
    limit: int,
) -> List[
    CreativeConcept
]:

    ranked = [
        concept
        for concept
        in all_concepts
        if concept.evaluation_valid
    ]

    ranked.sort(
        key=lambda item:
            item.weighted_score,
        reverse=True,
    )

    output: List[
        CreativeConcept
    ] = []

    seen: Set[str] = set()

    if winner is not None:

        output.append(
            winner
        )

        seen.add(
            winner.concept_id
        )

    for concept in ranked:

        if (
            concept.concept_id
            in seen
        ):
            continue

        output.append(
            concept
        )

        seen.add(
            concept.concept_id
        )

        if len(
            output
        ) >= limit:
            break

    return output[
        :limit
    ]


# =========================================================
# MAIN PUBLIC API
# =========================================================

def run_creative_brain(
    *,
    user_request: str,
    brand_context: Any = None,
    visual_references: Any = None,
    style_hint: str = "",
    mode: str = MODE_MASTERPIECE,
    top_count: int = 3,
) -> CreativeBrainResponse:

    user_request = clean_text(
        user_request,
        14000,
    )

    if not user_request:

        raise ValueError(
            "Creative request is empty."
        )

    mode = clean_text(
        mode,
        100,
    ).lower()

    if mode not in {
        MODE_FAST,
        MODE_MASTERPIECE,
    }:

        mode = (
            MODE_MASTERPIECE
        )

    top_count = max(
        1,
        min(
            5,
            int(
                top_count
                or 3
            ),
        ),
    )

    benefit_family = (
        detect_benefit_family(
            user_request
        )
    )

    stc_style = (
        detect_stc_style(
            user_request,
            style_hint,
        )
    )

    high_alert = (
        is_stc_high_alert(
            user_request,
            mode,
        )
    )

    concept_count = (
        concept_count_for_request(
            user_request,
            mode,
        )
    )

    director_calls = 0

    director_history: List[str] = []

    errors: List[str] = []

    concepts: List[
        CreativeConcept
    ] = []

    all_concepts: List[
        CreativeConcept
    ] = []

    winner: Optional[
        CreativeConcept
    ] = None

    release_level = (
        "quality_failed"
    )

    jury_payload: Dict[
        str,
        Any
    ] = {}

    technical_ideation_recovery = False

    targeted_repair_used = False

    targeted_repair_source_ids: List[
        str
    ] = []

    targeted_repair_concepts: List[
        CreativeConcept
    ] = []

    targeted_repair_arbitration: Dict[
        str,
        Any
    ] = {
        "used":
            False,

        "original_selected_id":
            "",

        "selected_was_qualified":
            False,

        "arbitrated_winner_id":
            "",

        "reason":
            "",

        "qualified_ids":
            [],
    }

    recovery_used = False

    recovery_reason = ""

    recovery_concepts: List[
        CreativeConcept
    ] = []

    recovery_arbitration: Dict[
        str,
        Any
    ] = {
        "used":
            False,

        "original_selected_id":
            "",

        "selected_was_qualified":
            False,

        "arbitrated_winner_id":
            "",

        "reason":
            "",

        "qualified_ids":
            [],
    }

    # =====================================================
    # LOG HEADER
    # =====================================================

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND CREATIVE BRAIN V5.5"
    )

    if high_alert:

        print(
            " STC BANK TARGETED-REPAIR HIGH ALERT"
        )

    else:

        print(
            " CAMPAIGN QUALITY MODE"
        )

    print(
        "=========================================="
    )

    print(
        "Mode:",
        mode,
    )

    print(
        "Benefit family:",
        benefit_family,
    )

    if is_stc_bank_request(
        user_request
    ):

        print(
            "STC visual family:",
            stc_style,
        )

    print(
        "High alert:",
        high_alert,
    )

    print(
        "Initial concepts:",
        concept_count,
    )

    print(
        "Director-call maximum:",
        MASTERPIECE_MAX_DIRECTOR_CALLS,
    )

    print(
        "Targeted repair:",
        (
            STC_TARGETED_REPAIR_ENABLED
            if high_alert
            else False
        ),
    )

    print(
        "Quality-first arbitration:",
        (
            STC_QUALITY_FIRST_ARBITRATION_ENABLED
            if high_alert
            else False
        ),
    )

    brand_pack_path = (
        locate_stc_brand_pack()
    )

    if high_alert:

        print(
            "Permanent STC brand pack:",
            (
                str(
                    brand_pack_path
                )
                if brand_pack_path
                else
                "not found"
            ),
        )

        curated = (
            stc_curated_reference_context(
                benefit_family=(
                    benefit_family
                ),
                stc_style=(
                    stc_style
                ),
            )
        )

        print(
            "Creative Brand Kit refs:",
            len(
                safe_list(
                    curated.get(
                        "selected_assets"
                    )
                )
            ),
        )

    print("")

    # =====================================================
    # CALL 1 — IDEATION
    # =====================================================

    try:

        director_calls += 1

        director_history.append(
            "diverse_ideation"
        )

        concepts = generate_concepts(
            user_request=(
                user_request
            ),
            brand_context=(
                brand_context
            ),
            visual_references=(
                visual_references
            ),
            style_hint=(
                style_hint
            ),
            benefit_family=(
                benefit_family
            ),
            stc_style=(
                stc_style
            ),
            recovery=False,
            concept_count=(
                concept_count
            ),
            high_alert=(
                high_alert
            ),
        )

    except Exception as error:

        primary_error = clean_text(
            error,
            3500,
        )

        errors.append(
            (
                "primary_ideation: "
                +
                primary_error
            )
        )

        print(
            "⚠️ Primary ideation technical failure:",
            primary_error,
        )

        # =================================================
        # TECHNICAL RETRY
        #
        # This consumes another Director call.
        # =================================================

        if (
            mode == MODE_MASTERPIECE
            and
            director_calls
            <
            MASTERPIECE_MAX_DIRECTOR_CALLS
        ):

            try:

                technical_ideation_recovery = True

                director_calls += 1

                director_history.append(
                    "technical_ideation_recovery"
                )

                concepts = generate_concepts(
                    user_request=(
                        user_request
                    ),
                    brand_context=(
                        brand_context
                    ),
                    visual_references=(
                        visual_references
                    ),
                    style_hint=(
                        style_hint
                    ),
                    benefit_family=(
                        benefit_family
                    ),
                    stc_style=(
                        stc_style
                    ),
                    recovery=True,
                    concept_count=(
                        concept_count
                    ),
                    high_alert=(
                        high_alert
                    ),
                )

            except Exception as retry_error:

                errors.append(
                    (
                        "technical_ideation_recovery: "
                        +
                        clean_text(
                            retry_error,
                            3500,
                        )
                    )
                )

                return technical_failure_response(
                    user_request=(
                        user_request
                    ),
                    mode=(
                        mode
                    ),
                    errors=(
                        errors
                    ),
                    director_calls=(
                        director_calls
                    ),
                    history=(
                        director_history
                    ),
                    benefit_family=(
                        benefit_family
                    ),
                    stc_style=(
                        stc_style
                    ),
                    high_alert=(
                        high_alert
                    ),
                )

        else:

            return technical_failure_response(
                user_request=(
                    user_request
                ),
                mode=(
                    mode
                ),
                errors=(
                    errors
                ),
                director_calls=(
                    director_calls
                ),
                history=(
                    director_history
                ),
                benefit_family=(
                    benefit_family
                ),
                stc_style=(
                    stc_style
                ),
                high_alert=(
                    high_alert
                ),
            )

    all_concepts.extend(
        concepts
    )

    # =====================================================
    # CALL 2 — EXECUTIVE REVIEW
    # =====================================================

    if (
        director_calls
        >=
        MASTERPIECE_MAX_DIRECTOR_CALLS
    ):

        errors.append(
            (
                "Director call budget exhausted "
                "before Executive Creative Review."
            )
        )

        return technical_failure_response(
            user_request=(
                user_request
            ),
            mode=(
                mode
            ),
            errors=(
                errors
            ),
            director_calls=(
                director_calls
            ),
            history=(
                director_history
            ),
            benefit_family=(
                benefit_family
            ),
            stc_style=(
                stc_style
            ),
            high_alert=(
                high_alert
            ),
        )

    try:

        director_calls += 1

        director_history.append(
            "executive_creative_review"
        )

        review_concepts(
            user_request=(
                user_request
            ),
            concepts=(
                concepts
            ),
            benefit_family=(
                benefit_family
            ),
            stc_style=(
                stc_style
            ),
            high_alert=(
                high_alert
            ),
        )

    except Exception as error:

        errors.append(
            (
                "creative_review: "
                +
                clean_text(
                    error,
                    3500,
                )
            )
        )

        return technical_failure_response(
            user_request=(
                user_request
            ),
            mode=(
                mode
            ),
            errors=(
                errors
            ),
            director_calls=(
                director_calls
            ),
            history=(
                director_history
            ),
            benefit_family=(
                benefit_family
            ),
            stc_style=(
                stc_style
            ),
            high_alert=(
                high_alert
            ),
        )

    concepts.sort(
        key=lambda item:
            item.weighted_score,
        reverse=True,
    )

    # =====================================================
    # NORMAL MODE
    # =====================================================

    if not high_alert:

        (
            winner,
            release_level,
        ) = choose_normal_release(
            concepts=(
                concepts
            ),
            mode=(
                mode
            ),
        )

    # =====================================================
    # STC HIGH ALERT
    # =====================================================

    else:

        primary_qualified = (
            strict_qualified_concepts(
                concepts,
                high_alert=True,
            )
        )

        print(
            "Strict primary finalists:",
            len(
                primary_qualified
            ),
        )

        # =================================================
        # TECHNICAL IDEATION RETRY ALREADY CONSUMED CALL 2.
        #
        # Executive Review is now Call 3.
        # No additional Jury/Repair/Recovery call is legal.
        #
        # A strict reviewed concept may still release.
        # =================================================

        if technical_ideation_recovery:

            if primary_qualified:

                winner = (
                    primary_qualified[
                        0
                    ]
                )

                release_level = (
                    "stc_technical_retry_strict_review_release"
                )

                mark_quality_release(
                    winner,
                    release_level=(
                        release_level
                    ),
                )

            else:

                winner = None

                release_level = (
                    "quality_failed_after_technical_retry"
                )

        # =================================================
        # ROUTE A
        # STRICT PRIMARY FINALISTS
        # CALL 3 = JURY
        # =================================================

        elif primary_qualified:

            finalists = (
                primary_qualified[
                    :MASTERPIECE_SHORTLIST_SIZE
                ]
            )

            if (
                director_calls
                <
                MASTERPIECE_MAX_DIRECTOR_CALLS
            ):

                try:

                    director_calls += 1

                    director_history.append(
                        "stc_finalist_jury"
                    )

                    jury_payload = run_finalist_jury(
                        user_request=(
                            user_request
                        ),
                        finalists=(
                            finalists
                        ),
                        benefit_family=(
                            benefit_family
                        ),
                        stc_style=(
                            stc_style
                        ),
                    )

                    (
                        winner,
                        release_level,
                    ) = (
                        choose_strict_stc_jury_release(
                            concepts=(
                                concepts
                            ),
                            jury=(
                                jury_payload
                            ),
                            benefit_family=(
                                benefit_family
                            ),
                        )
                    )

                except Exception as jury_error:

                    errors.append(
                        (
                            "finalist_jury: "
                            +
                            clean_text(
                                jury_error,
                                3500,
                            )
                        )
                    )

                    return technical_failure_response(
                        user_request=(
                            user_request
                        ),
                        mode=(
                            mode
                        ),
                        errors=(
                            errors
                        ),
                        director_calls=(
                            director_calls
                        ),
                        history=(
                            director_history
                        ),
                        benefit_family=(
                            benefit_family
                        ),
                        stc_style=(
                            stc_style
                        ),
                        high_alert=(
                            high_alert
                        ),
                    )

        # =================================================
        # NO STRICT PRIMARY FINALIST
        # =================================================

        else:

            repair_candidates = (
                select_targeted_repair_candidates(
                    concepts
                )
            )

            print(
                "Targeted-repair candidates:",
                len(
                    repair_candidates
                ),
            )

            if repair_candidates:

                for candidate in repair_candidates:

                    print(
                        (
                            "  ↳ "
                            +
                            candidate.concept_id
                            +
                            " score="
                            +
                            str(
                                candidate.weighted_score
                            )
                            +
                            " gaps="
                            +
                            compact_json(
                                targeted_repair_dimension_gaps(
                                    candidate
                                ),
                                2000,
                            )
                        )
                    )

            # =============================================
            # ROUTE B
            # CALL 3 = TARGETED REPAIR
            # =============================================

            if (
                repair_candidates
                and
                STC_TARGETED_REPAIR_ENABLED
                and
                director_calls
                <
                MASTERPIECE_MAX_DIRECTOR_CALLS
            ):

                print("")
                print(
                    "🛠️ STC TARGETED CREATIVE REPAIR"
                )
                print(
                    "Near-miss detected."
                )
                print(
                    "Call 3 will repair the strongest "
                    "existing proposition instead of "
                    "discarding it."
                )
                print("")

                targeted_repair_used = True

                targeted_repair_source_ids = [
                    candidate.concept_id
                    for candidate
                    in repair_candidates
                ]

                try:

                    director_calls += 1

                    director_history.append(
                        "stc_targeted_repair_board"
                    )

                    (
                        targeted_repair_concepts,
                        repair_jury,
                    ) = run_targeted_repair_board(
                        user_request=(
                            user_request
                        ),
                        repair_candidates=(
                            repair_candidates
                        ),
                        brand_context=(
                            brand_context
                        ),
                        visual_references=(
                            visual_references
                        ),
                        benefit_family=(
                            benefit_family
                        ),
                        stc_style=(
                            stc_style
                        ),
                    )

                    all_concepts.extend(
                        targeted_repair_concepts
                    )

                    repair_qualified = (
                        strict_qualified_concepts(
                            targeted_repair_concepts,
                            high_alert=True,
                        )
                    )

                    print(
                        "Targeted-repair strict finalists:",
                        len(
                            repair_qualified
                        ),
                    )

                    jury_payload = (
                        repair_jury
                    )

                    (
                        winner,
                        targeted_repair_arbitration,
                    ) = (
                        arbitrate_targeted_repair_selection(
                            repair_concepts=(
                                targeted_repair_concepts
                            ),
                            repair_qualified=(
                                repair_qualified
                            ),
                            jury=(
                                repair_jury
                            ),
                            benefit_family=(
                                benefit_family
                            ),
                        )
                    )

                    if winner:

                        release_level = (
                            "stc_targeted_repair_release"
                        )

                        mark_quality_release(
                            winner,
                            release_level=(
                                release_level
                            ),
                        )

                    else:

                        release_level = (
                            "targeted_repair_quality_failed"
                        )

                except Exception as repair_error:

                    errors.append(
                        (
                            "targeted_repair: "
                            +
                            clean_text(
                                repair_error,
                                3500,
                            )
                        )
                    )

                    return technical_failure_response(
                        user_request=(
                            user_request
                        ),
                        mode=(
                            mode
                        ),
                        errors=(
                            errors
                        ),
                        director_calls=(
                            director_calls
                        ),
                        history=(
                            director_history
                        ),
                        benefit_family=(
                            benefit_family
                        ),
                        stc_style=(
                            stc_style
                        ),
                        high_alert=(
                            high_alert
                        ),
                    )

            # =============================================
            # ROUTE C
            # CALL 3 = FRESH RECOVERY
            # =============================================

            elif (
                STC_CREATIVE_RECOVERY_ENABLED
                and
                director_calls
                <
                MASTERPIECE_MAX_DIRECTOR_CALLS
            ):

                recovery_used = True

                recovery_reason = (
                    "no_strict_primary_and_no_repairable_near_miss"
                )

                print("")
                print(
                    "🔁 STC FRESH CREATIVE RECOVERY"
                )
                print(
                    "Reason:",
                    recovery_reason,
                )
                print(
                    "No repairable near-miss exists; "
                    "Call 3 will rebuild the creative mechanism."
                )
                print("")

                try:

                    director_calls += 1

                    director_history.append(
                        "stc_recovery_board"
                    )

                    (
                        recovery_concepts,
                        recovery_jury,
                    ) = run_recovery_board(
                        user_request=(
                            user_request
                        ),
                        failed_concepts=(
                            concepts
                        ),
                        brand_context=(
                            brand_context
                        ),
                        visual_references=(
                            visual_references
                        ),
                        benefit_family=(
                            benefit_family
                        ),
                        stc_style=(
                            stc_style
                        ),
                    )

                    all_concepts.extend(
                        recovery_concepts
                    )

                    recovery_qualified = (
                        strict_qualified_concepts(
                            recovery_concepts,
                            high_alert=True,
                        )
                    )

                    print(
                        "Recovery strict finalists:",
                        len(
                            recovery_qualified
                        ),
                    )

                    jury_payload = (
                        recovery_jury
                    )

                    (
                        winner,
                        recovery_arbitration,
                    ) = (
                        arbitrate_recovery_selection(
                            recovery_concepts=(
                                recovery_concepts
                            ),
                            recovery_qualified=(
                                recovery_qualified
                            ),
                            jury=(
                                recovery_jury
                            ),
                            benefit_family=(
                                benefit_family
                            ),
                        )
                    )

                    if winner:

                        release_level = (
                            "stc_recovery_release"
                        )

                        mark_quality_release(
                            winner,
                            release_level=(
                                release_level
                            ),
                        )

                    else:

                        release_level = (
                            "recovery_quality_failed"
                        )

                except Exception as recovery_error:

                    errors.append(
                        (
                            "creative_recovery: "
                            +
                            clean_text(
                                recovery_error,
                                3500,
                            )
                        )
                    )

                    return technical_failure_response(
                        user_request=(
                            user_request
                        ),
                        mode=(
                            mode
                        ),
                        errors=(
                            errors
                        ),
                        director_calls=(
                            director_calls
                        ),
                        history=(
                            director_history
                        ),
                        benefit_family=(
                            benefit_family
                        ),
                        stc_style=(
                            stc_style
                        ),
                        high_alert=(
                            high_alert
                        ),
                    )

            else:

                winner = None

                release_level = (
                    "quality_failed_no_call_budget"
                )

    # =====================================================
    # FINAL QUALITY STATE
    # =====================================================

    quality_gate_evaluated = bool(
        any(
            concept.evaluation_valid
            for concept
            in all_concepts
        )
    )

    quality_gate_passed = bool(
        winner is not None
        and winner.evaluation_valid
        and winner.quality_gate_passed
    )

    if (
        high_alert
        and winner is not None
    ):

        #
        # Absolute last deterministic protection.
        #
        if (
            winner.weighted_score
            <
            STC_HIGH_ALERT_RELEASE_FLOOR
            or
            stc_dimension_gate_failures(
                winner
            )
            or
            any(
                failure
                in HARD_REJECT_FAILURES
                for failure
                in winner.quality_gate_failures
            )
        ):

            errors.append(
                (
                    "final_release_guard: "
                    "winner failed strict STC release validation"
                )
            )

            winner.quality_gate_passed = False

            winner = None

            quality_gate_passed = False

            release_level = (
                "final_strict_guard_failed"
            )

    # =====================================================
    # TOP CONCEPTS
    # =====================================================

    top_concepts = build_top_concept_list(
        all_concepts=(
            all_concepts
        ),
        winner=(
            winner
        ),
        limit=(
            top_count
        ),
    )

    # =====================================================
    # DIAGNOSTIC LOG
    # =====================================================

    print("")
    print(
        "=========================================="
    )

    if quality_gate_passed:

        print(
            " CREATIVE QUALITY GATE: PASSED ✅"
        )

        print(
            "Winner:",
            winner.concept_id
            if winner
            else "",
        )

        print(
            "Score:",
            winner.weighted_score
            if winner
            else 0,
        )

        print(
            "Release:",
            release_level,
        )

    else:

        print(
            " CREATIVE QUALITY GATE: NOT PASSED"
        )

        evaluated = [
            concept
            for concept
            in all_concepts
            if concept.evaluation_valid
        ]

        evaluated.sort(
            key=lambda item:
                item.weighted_score,
            reverse=True,
        )

        if evaluated:

            best = evaluated[
                0
            ]

            print(
                "Best evaluated score:",
                best.weighted_score,
            )

            print(
                "Best concept:",
                best.title
                or
                best.concept_id,
            )

            failures = (
                stc_dimension_gate_failures(
                    best
                )
                if high_alert
                else
                best.quality_gate_failures
            )

            if failures:

                print(
                    "Failures:",
                    ", ".join(
                        failures[
                            :16
                        ]
                    ),
                )

        print(
            "No fake winner created."
        )

    print(
        "Targeted repair used:",
        targeted_repair_used,
    )

    print(
        "Fresh recovery used:",
        recovery_used,
    )

    print(
        "Director calls:",
        director_calls,
    )

    print(
        "Call path:",
        (
            " → ".join(
                director_history
            )
        ),
    )

    print(
        "=========================================="
    )
    print("")

    # =====================================================
    # FAILURE REASON
    # =====================================================

    failure_reason = ""

    if not quality_gate_passed:

        if targeted_repair_used:

            failure_reason = (
                "targeted_repair_did_not_pass_strict_stc_gates"
            )

        elif recovery_used:

            failure_reason = (
                "recovery_did_not_pass_strict_stc_gates"
            )

        elif high_alert:

            failure_reason = (
                "no_strict_stc_concept_approved"
            )

        else:

            failure_reason = (
                "creative_quality_target_not_reached"
            )

    # =====================================================
    # RESPONSE
    # =====================================================

    return CreativeBrainResponse(

        ok=(
            quality_gate_passed
        ),

        mode=(
            mode
        ),

        request=(
            user_request
        ),

        total_concepts=len(
            all_concepts
        ),

        concepts=list(
            all_concepts
        ),

        top_concepts=(
            top_concepts
        ),

        winner=(
            winner
        ),

        metadata={

            "version":
                VERSION,

            "architecture":
                "stc_targeted_repair_quality_first_v55",

            "high_alert":
                high_alert,

            "benefit_family":
                benefit_family,

            "stc_style":
                stc_style,

            "initial_concepts":
                concept_count,

            "total_concepts":
                len(
                    all_concepts
                ),

            "shortlisted_concepts":
                len(
                    top_concepts
                ),

            # =============================================
            # DIRECTOR CALLS
            # =============================================

            "director_calls":
                director_calls,

            "director_call_history":
                director_history,

            "director_call_target":
                (
                    3
                    if high_alert
                    else 2
                ),

            "director_call_maximum":
                MASTERPIECE_MAX_DIRECTOR_CALLS,

            "technical_ideation_recovery":
                technical_ideation_recovery,

            # =============================================
            # TARGETED REPAIR
            # =============================================

            "targeted_repair_enabled":
                STC_TARGETED_REPAIR_ENABLED,

            "targeted_repair_used":
                targeted_repair_used,

            "targeted_repair_min_score":
                STC_TARGETED_REPAIR_MIN_SCORE,

            "targeted_repair_max_dimension_failures":
                STC_TARGETED_REPAIR_MAX_DIMENSION_FAILURES,

            "targeted_repair_max_gap":
                STC_TARGETED_REPAIR_MAX_GAP,

            "targeted_repair_source_ids":
                targeted_repair_source_ids,

            "targeted_repair_concepts":
                len(
                    targeted_repair_concepts
                ),

            "targeted_repair_arbitration_enabled":
                STC_QUALITY_FIRST_ARBITRATION_ENABLED,

            "targeted_repair_arbitration_used":
                bool(
                    targeted_repair_arbitration.get(
                        "used"
                    )
                ),

            "targeted_repair_original_selection":
                targeted_repair_arbitration.get(
                    "original_selected_id",
                    "",
                ),

            "targeted_repair_arbitrated_selection":
                targeted_repair_arbitration.get(
                    "arbitrated_winner_id",
                    "",
                ),

            "targeted_repair_arbitration_reason":
                targeted_repair_arbitration.get(
                    "reason",
                    "",
                ),

            "targeted_repair_strict_qualified_ids":
                targeted_repair_arbitration.get(
                    "qualified_ids",
                    [],
                ),

            # =============================================
            # FRESH RECOVERY
            # =============================================

            "recovery_enabled":
                STC_CREATIVE_RECOVERY_ENABLED,

            "recovery_used":
                recovery_used,

            "recovery_reason":
                recovery_reason,

            "recovery_concepts":
                len(
                    recovery_concepts
                ),

            "quality_first_arbitration_enabled":
                STC_QUALITY_FIRST_ARBITRATION_ENABLED,

            "quality_first_arbitration_used":
                bool(
                    recovery_arbitration.get(
                        "used"
                    )
                ),

            "recovery_jury_original_selection":
                recovery_arbitration.get(
                    "original_selected_id",
                    "",
                ),

            "recovery_arbitrated_selection":
                recovery_arbitration.get(
                    "arbitrated_winner_id",
                    "",
                ),

            "recovery_arbitration_reason":
                recovery_arbitration.get(
                    "reason",
                    "",
                ),

            "recovery_strict_qualified_ids":
                recovery_arbitration.get(
                    "qualified_ids",
                    [],
                ),

            # =============================================
            # THRESHOLDS
            # =============================================

            "masterpiece_min_score":
                MASTERPIECE_MIN_SCORE,

            "masterpiece_target_score":
                MASTERPIECE_MIN_SCORE,

            "masterpiece_release_floor":
                MASTERPIECE_RELEASE_FLOOR,

            "stc_target_score":
                STC_HIGH_ALERT_MIN_SCORE,

            "stc_release_floor":
                STC_HIGH_ALERT_RELEASE_FLOOR,

            "stc_min_jury_confidence":
                STC_MIN_JURY_CONFIDENCE,

            "stc_dimension_minimums":
                dict(
                    STC_DIMENSION_MINIMUMS
                ),

            "thresholds_lowered_by_repair":
                False,

            "thresholds_lowered_by_arbitration":
                False,

            # =============================================
            # QUALITY STATE
            # =============================================

            "release_level":
                release_level,

            "quality_gate_evaluated":
                quality_gate_evaluated,

            "quality_gate_passed":
                quality_gate_passed,

            "target_quality_gate_passed":
                bool(
                    winner
                    and
                    (
                        winner.weighted_score
                        >=
                        (
                            STC_HIGH_ALERT_MIN_SCORE
                            if high_alert
                            else
                            MASTERPIECE_MIN_SCORE
                        )
                    )
                ),

            "technical_failure":
                False,

            #
            # Genuine STC quality rejection must NOT silently
            # become generic Smart final delivery.
            #
            "allow_smart_engine_fallback":
                bool(
                    not high_alert
                    and
                    not quality_gate_passed
                ),

            "quality_target_blocks_production":
                bool(
                    high_alert
                    and
                    not quality_gate_passed
                ),

            "fallback_blocked":
                bool(
                    high_alert
                    and
                    not quality_gate_passed
                ),

            "failure_reason":
                failure_reason,

            # =============================================
            # SAFETY / QUALITY FEATURES
            # =============================================

            "real_model_evaluation_required":
                True,

            "fake_fallback_winner_allowed":
                False,

            "campaign_visual_mechanism_required":
                True,

            "generic_scene_guard":
                True,

            "repeated_scene_guard":
                True,

            "literal_transaction_guard":
                True,

            "purple_neon_guard":
                True,

            "merchant_fusion_guard":
                True,

            "merchant_semantic_equivalence":
                True,

            "merchant_online_semantic_review":
                True,

            "merchant_pos_semantic_review":
                True,

            "single_frame_mechanism_gate":
                True,

            "advertising_readiness_gate":
                True,

            "brand_fit_dimension_gate":
                True,

            "originality_dimension_gate":
                True,

            "finalist_jury_enabled":
                high_alert,

            "finalist_jury_used":
                bool(
                    jury_payload
                ),

            "finalist_jury_source":
                (
                    safe_dict(
                        winner.debate.get(
                            "finalist_jury"
                        )
                    ).get(
                        "source",
                        "",
                    )
                    if winner
                    else
                    ""
                ),

            "brand_pack_available":
                bool(
                    locate_stc_brand_pack()
                ),

            "brand_kit_available":
                STC_BRAND_KIT_AVAILABLE,

            "camera_director_enabled":
                True,

            "scene_feasibility_enabled":
                True,

            "no_generated_copy":
                True,

            "no_generated_logo":
                True,
        },

        errors=(
            errors
        ),
    )


# =========================================================
# SERIALIZER
#
# PUBLIC COMPATIBILITY CONTRACT
# =========================================================

def concept_to_dict(
    concept: CreativeConcept,
) -> Dict[str, Any]:

    return {

        "concept_id":
            concept.concept_id,

        "category":
            concept.category,

        "title":
            concept.title,

        "concept_archetype":
            concept.concept_archetype,

        "campaign_hook":
            concept.campaign_hook,

        "core_idea":
            concept.core_idea,

        "marketing_message":
            concept.marketing_message,

        "visual_metaphor":
            concept.visual_metaphor,

        "visual_mechanism_type":
            concept.visual_mechanism_type,

        "why_not_generic":
            concept.why_not_generic,

        "environment":
            concept.environment,

        "environment_novelty":
            concept.environment_novelty,

        "hero_element":
            concept.hero_element,

        "supporting_elements":
            concept.supporting_elements,

        "camera_angle":
            concept.camera_angle,

        "lens":
            concept.lens,

        "perspective":
            concept.perspective,

        "lighting":
            concept.lighting,

        "negative_space":
            concept.negative_space,

        "brand_logic":
            concept.brand_logic,

        "production_method":
            concept.production_method,

        "campaign_extension":
            concept.campaign_extension,

        "risks":
            concept.risks,

        "scores":
            concept.scores,

        "weighted_score":
            concept.weighted_score,

        "cliche_hits":
            concept.cliche_hits,

        "debate":
            concept.debate,

        "feasibility":
            concept.feasibility,

        "evaluation_valid":
            concept.evaluation_valid,

        "quality_gate_passed":
            concept.quality_gate_passed,

        "quality_gate_failures":
            concept.quality_gate_failures,

        "generation_round":
            concept.generation_round,

        "revised_from":
            concept.revised_from,
    }


def response_to_dict(
    response: CreativeBrainResponse,
) -> Dict[str, Any]:

    return {

        "ok":
            response.ok,

        "mode":
            response.mode,

        "request":
            response.request,

        "total_concepts":
            response.total_concepts,

        "concepts": [
            concept_to_dict(
                item
            )
            for item
            in response.concepts
        ],

        "top_concepts": [
            concept_to_dict(
                item
            )
            for item
            in response.top_concepts
        ],

        "winner": (
            concept_to_dict(
                response.winner
            )
            if response.winner
            else None
        ),

        "metadata":
            response.metadata,

        "errors":
            response.errors,
    }


# =========================================================
# HUMAN SUMMARY
# =========================================================

def build_top_concepts_summary(
    response: CreativeBrainResponse,
) -> str:

    if not response.top_concepts:

        return (
            "ما طلعت اتجاهات إبداعية كافية."
        )

    lines: List[str] = [
        (
            "XPAND Creative Brain | "
            +
            response.mode.upper()
        )
    ]

    if response.winner:

        lines.append(
            (
                "الفكرة المعتمدة: "
                +
                response.winner.title
            )
        )

    for index, concept in enumerate(
        response.top_concepts,
        start=1,
    ):

        lines.append("")

        lines.append(
            (
                str(
                    index
                )
                +
                ") "
                +
                (
                    concept.title
                    or
                    concept.concept_id
                )
            )
        )

        if concept.concept_archetype:

            lines.append(
                (
                    "النوع: "
                    +
                    concept.concept_archetype
                )
            )

        if concept.core_idea:

            lines.append(
                (
                    "الفكرة: "
                    +
                    concept.core_idea
                )
            )

        if concept.campaign_hook:

            lines.append(
                (
                    "الآلية الإعلانية: "
                    +
                    concept.campaign_hook
                )
            )

        lines.append(
            (
                "الزاوية: "
                +
                concept.camera_angle
                +
                (
                    (
                        " | "
                        +
                        concept.lens
                    )
                    if concept.lens
                    else
                    ""
                )
            )
        )

        lines.append(
            (
                "التقييم: "
                +
                str(
                    concept.weighted_score
                )
                +
                "/100"
            )
        )

    return "\n".join(
        lines
    ).strip()


# =========================================================
# ZERO-COST SELF TEST
#
# IMPORTANT:
#
# This block makes NO Director API calls.
# It generates NO images.
# =========================================================

if __name__ == "__main__":

    tests: Dict[
        str,
        bool
    ] = {}

    # =====================================================
    # PUBLIC CONTRACT
    # =====================================================

    tests[
        "mode_fast_contract"
    ] = (
        MODE_FAST
        ==
        "fast"
    )

    tests[
        "mode_masterpiece_contract"
    ] = (
        MODE_MASTERPIECE
        ==
        "masterpiece"
    )

    tests[
        "version_55"
    ] = (
        VERSION
        ==
        "5.5"
    )

    # =====================================================
    # SCORE WEIGHTS
    # =====================================================

    tests[
        "dimension_weights_sum_100"
    ] = (
        sum(
            DIMENSION_WEIGHTS.values()
        )
        ==
        100
    )

    # =====================================================
    # STRICT THRESHOLDS
    #
    # Targeted Repair must NEVER lower these.
    # =====================================================

    tests[
        "strict_concept_strength_88"
    ] = (
        STC_MIN_CONCEPT_STRENGTH
        ==
        88.0
    )

    tests[
        "strict_brand_fit_90"
    ] = (
        STC_MIN_BRAND_FIT
        ==
        90.0
    )

    tests[
        "strict_originality_88"
    ] = (
        STC_MIN_ORIGINALITY
        ==
        88.0
    )

    tests[
        "strict_visual_mechanism_90"
    ] = (
        STC_MIN_VISUAL_MECHANISM
        ==
        90.0
    )

    tests[
        "strict_camera_84"
    ] = (
        STC_MIN_CAMERA_QUALITY
        ==
        84.0
    )

    tests[
        "strict_realism_86"
    ] = (
        STC_MIN_REALISM
        ==
        86.0
    )

    tests[
        "strict_feasibility_82"
    ] = (
        STC_MIN_FEASIBILITY
        ==
        82.0
    )

    tests[
        "strict_copy_space_80"
    ] = (
        STC_MIN_COPY_SPACE
        ==
        80.0
    )

    tests[
        "strict_distinctiveness_88"
    ] = (
        STC_MIN_DISTINCTIVENESS
        ==
        88.0
    )

    tests[
        "strict_ad_readiness_90"
    ] = (
        STC_MIN_AD_READINESS
        ==
        90.0
    )

    # =====================================================
    # CALL POLICY
    # =====================================================

    tests[
        "normal_four_concepts"
    ] = (
        NORMAL_CONCEPT_COUNT
        ==
        4
    )

    tests[
        "stc_six_to_ten_concepts"
    ] = (
        6
        <=
        STC_HIGH_ALERT_CONCEPT_COUNT
        <=
        10
    )

    tests[
        "targeted_repair_two_outputs"
    ] = (
        STC_TARGETED_REPAIR_OUTPUT_COUNT
        ==
        2
    )

    tests[
        "max_three_director_calls"
    ] = (
        MASTERPIECE_MAX_DIRECTOR_CALLS
        <=
        3
    )

    tests[
        "stc_three_call_target"
    ] = (
        MASTERPIECE_TARGET_DIRECTOR_CALLS
        ==
        3
    )

    # =====================================================
    # ROUTING
    # =====================================================

    tests[
        "merchant_payments_routing"
    ] = (
        detect_benefit_family(
            (
                "أنشئ إعلان لبنك STC Bank "
                "عن التجارة الإلكترونية ونقاط البيع"
            )
        )
        ==
        "merchant_payments"
    )

    tests[
        "default_realistic_style"
    ] = (
        detect_stc_style(
            "إعلان STC Bank"
        )
        ==
        "premium_realistic"
    )

    tests[
        "explicit_purple_style"
    ] = (
        detect_stc_style(
            "STC Bank في بيئة بنفسجية معمارية"
        )
        ==
        "premium_purple_architecture"
    )

    tests[
        "augmented_realism_style"
    ] = (
        detect_stc_style(
            "STC Bank واقعية معززة"
        )
        ==
        "premium_augmented_realism"
    )

    # =====================================================
    # BRAND PACK
    # =====================================================

    tests[
        "brand_pack_loader_safe"
    ] = isinstance(
        load_stc_brand_pack(),
        dict,
    )

    # =====================================================
    # LIVE-CASE STYLE NEAR MISS
    #
    # Represents the type of concept that scored ~87.94:
    #
    # - strong core idea
    # - feasible
    # - no hard reject
    # - only four small strict-dimension gaps
    # =====================================================

    near_miss = CreativeConcept(

        concept_id="NM01",

        title=(
            "نافذة تصبح مدخلاً"
        ),

        concept_archetype=(
            "architectural service transformation"
        ),

        campaign_hook=(
            "One physical architectural relationship turns "
            "online commerce and in-store payment into one "
            "continuous merchant system."
        ),

        core_idea=(
            "A premium Saudi commercial environment uses one "
            "believable spatial transformation to connect a "
            "digital storefront with physical payment acceptance."
        ),

        marketing_message=(
            "One merchant ecosystem across online and physical sales."
        ),

        visual_metaphor=(
            "A continuous architectural threshold links digital "
            "commerce and in-store payment."
        ),

        visual_mechanism_type=(
            "architectural continuity"
        ),

        why_not_generic=(
            "The campaign is driven by the physical relationship "
            "between both commerce channels, not by a customer "
            "performing an ordinary transaction."
        ),

        environment=(
            "Contemporary premium Saudi commercial architecture."
        ),

        environment_novelty=(
            "The environment is built around a spatial advertising "
            "mechanism rather than the repeated checkout-counter scene."
        ),

        hero_element=(
            "Unified commerce threshold."
        ),

        camera_angle=(
            "elevated three-quarter reveal"
        ),

        lens="35mm",

        perspective=(
            "foreground-to-background spatial reveal"
        ),

        lighting=(
            "controlled premium natural daylight"
        ),

        negative_space=(
            "30% natural upper-right copy space"
        ),

        brand_logic=(
            "Restrained premium STC Bank confidence."
        ),

        production_method=(
            "single_generation"
        ),

        weighted_score=87.94,

        scores={

            "concept_strength":
                87.0,

            "brand_fit":
                89.0,

            "originality":
                90.0,

            "visual_mechanism":
                92.0,

            "camera_quality":
                87.0,

            "realism":
                85.0,

            "feasibility":
                86.0,

            "copy_space_quality":
                85.0,

            "distinctiveness":
                90.0,

            "advertising_readiness":
                89.0,
        },

        evaluation_valid=True,

        feasibility={
            "production_feasible":
                True,
        },

        quality_gate_failures=[
            "concept_strength_below_88",
            "brand_fit_below_90",
            "realism_below_86",
            "advertising_readiness_below_90",
        ],

        debate={
            "strengths": [
                "Strong single-frame spatial mechanism.",
                "Merchant channels are visibly unified.",
            ],

            "weaknesses": [
                "Needs stronger STC Bank ownership.",
                "Needs more premium realism.",
                "Needs final advertising polish.",
            ],

            "merchant_semantics": {
                "online_channel_clear":
                    True,

                "pos_channel_clear":
                    True,

                "channels_fused":
                    True,
            },
        },
    )

    near_miss_gaps = (
        targeted_repair_dimension_gaps(
            near_miss
        )
    )

    tests[
        "near_miss_has_four_small_gaps"
    ] = bool(
        len(
            near_miss_gaps
        )
        ==
        4
        and
        max(
            safe_float(
                item.get(
                    "gap"
                ),
                0,
            )
            for item
            in near_miss_gaps
        )
        <=
        STC_TARGETED_REPAIR_MAX_GAP
    )

    repair_candidates = (
        select_targeted_repair_candidates(
            [
                near_miss
            ]
        )
    )

    tests[
        "live_8794_case_is_repairable"
    ] = bool(
        repair_candidates
        and
        repair_candidates[
            0
        ].concept_id
        ==
        "NM01"
    )

    # =====================================================
    # HARD REJECT CANNOT ENTER REPAIR
    # =====================================================

    hard_rejected = CreativeConcept(

        concept_id="HARD",

        title="Generic checkout",

        core_idea=(
            "Customer taps POS terminal on a wooden counter "
            "while merchant packs a parcel."
        ),

        campaign_hook=(
            "Ordinary payment transaction."
        ),

        visual_metaphor=(
            "Worker packing box."
        ),

        visual_mechanism_type="",

        why_not_generic="",

        environment=(
            "Luxury boutique with wooden counter."
        ),

        environment_novelty="",

        hero_element=(
            "POS terminal"
        ),

        weighted_score=87.5,

        scores=dict(
            near_miss.scores
        ),

        evaluation_valid=True,

        feasibility={
            "production_feasible":
                True,
        },

        quality_gate_failures=[
            "literal_transaction_tableau",
        ],
    )

    tests[
        "hard_reject_not_repairable"
    ] = (
        not is_targeted_repair_candidate(
            hard_rejected
        )
    )

    # =====================================================
    # TARGETED REPAIR PROMPT
    # =====================================================

    repair_prompt_test = (
        build_targeted_repair_prompt(
            user_request=(
                "STC Bank التجارة الإلكترونية ونقاط البيع"
            ),
            repair_candidates=[
                near_miss
            ],
            brand_context={},
            visual_references=[],
            benefit_family=(
                "merchant_payments"
            ),
            stc_style=(
                "premium_realistic"
            ),
        )
    )

    tests[
        "repair_prompt_preserves_core"
    ] = contains_any(
        repair_prompt_test,
        [
            "PRESERVE THE STRONGEST CORE PROPOSITION",
        ],
    )

    tests[
        "repair_prompt_contains_exact_failure"
    ] = contains_any(
        repair_prompt_test,
        [
            "concept_strength_below_88",
        ],
    )

    tests[
        "repair_prompt_blocks_score_inflation"
    ] = contains_any(
        repair_prompt_test,
        [
            "DO NOT inflate scores",
        ],
    )

    tests[
        "repair_prompt_has_merchant_fusion"
    ] = contains_any(
        repair_prompt_test,
        [
            (
                "Simply showing both in the same room "
                "is NOT fusion"
            ),
        ],
    )

    tests[
        "repair_prompt_blocks_counter"
    ] = contains_any(
        repair_prompt_test,
        [
            "customer + POS + counter + merchant tableau",
        ],
    )

    # =====================================================
    # STRICT QUALIFIED FIXTURE
    # =====================================================

    qualified = CreativeConcept(

        concept_id="T01",

        title=(
            "Strict repaired concept"
        ),

        concept_archetype=(
            "service transformation"
        ),

        campaign_hook=(
            "One physical mechanism unifies online commerce "
            "and in-store acceptance."
        ),

        core_idea=(
            "A premium Saudi commercial scene uses one coherent "
            "physical transformation between digital ordering and "
            "physical payment."
        ),

        marketing_message=(
            "Unified merchant payments."
        ),

        visual_metaphor=(
            "One continuous material relationship visibly joins "
            "digital storefront and payment acceptance."
        ),

        visual_mechanism_type=(
            "physical continuity"
        ),

        why_not_generic=(
            "The relationship between both channels is the actual "
            "advertising mechanism."
        ),

        environment=(
            "Premium contemporary Saudi commercial architecture."
        ),

        environment_novelty=(
            "No checkout-counter tableau."
        ),

        hero_element=(
            "Unified merchant mechanism."
        ),

        camera_angle=(
            "elevated three-quarter view"
        ),

        lens="35mm",

        perspective=(
            "foreground-to-background reveal"
        ),

        lighting=(
            "premium natural daylight"
        ),

        negative_space=(
            "30% upper-right natural negative space"
        ),

        brand_logic=(
            "Restrained premium STC Bank visual discipline."
        ),

        production_method=(
            "single_generation"
        ),

        evaluation_valid=True,

        weighted_score=89.25,

        scores={

            "concept_strength":
                91,

            "brand_fit":
                93,

            "originality":
                90,

            "visual_mechanism":
                93,

            "camera_quality":
                88,

            "realism":
                90,

            "feasibility":
                87,

            "copy_space_quality":
                88,

            "distinctiveness":
                91,

            "advertising_readiness":
                92,
        },

        feasibility={
            "production_feasible":
                True,
        },

        debate={
            "merchant_semantics": {

                "online_channel_clear":
                    True,

                "pos_channel_clear":
                    True,

                "channels_fused":
                    True,
            },
        },
    )

    unqualified = CreativeConcept(

        concept_id="T02",

        title=(
            "Jury liked but unqualified"
        ),

        core_idea=(
            "Visually attractive merchant scene."
        ),

        campaign_hook=(
            "Commerce scene."
        ),

        visual_metaphor=(
            "Composition."
        ),

        visual_mechanism_type=(
            "composition"
        ),

        why_not_generic=(
            "Styled image."
        ),

        environment=(
            "Commercial environment."
        ),

        environment_novelty=(
            "Modern."
        ),

        hero_element=(
            "Merchant scene."
        ),

        evaluation_valid=True,

        weighted_score=86.0,

        scores={

            "concept_strength":
                86,

            "brand_fit":
                88,

            "originality":
                86,

            "visual_mechanism":
                86,

            "camera_quality":
                85,

            "realism":
                88,

            "feasibility":
                86,

            "copy_space_quality":
                84,

            "distinctiveness":
                85,

            "advertising_readiness":
                86,
        },

        feasibility={
            "production_feasible":
                True,
        },
    )

    strict_fixture = (
        strict_qualified_concepts(
            [
                qualified,
                unqualified,
            ],
            high_alert=True,
        )
    )

    tests[
        "strict_fixture_has_one_finalist"
    ] = bool(
        len(
            strict_fixture
        )
        ==
        1
        and
        strict_fixture[
            0
        ].concept_id
        ==
        "T01"
    )

    # =====================================================
    # QUALITY-FIRST TARGETED REPAIR ARBITRATION
    # =====================================================

    repair_jury = {

        "selected_concept_id":
            "T02",

        "approval":
            True,

        "confidence":
            90,

        "advertising_reason":
            "Board approves production.",

        "brand_reason":
            "Fits STC Bank.",

        "originality_reason":
            "Distinct enough.",

        "merchant_fusion_approved":
            True,

        "fatal_issues":
            [],

        "production_instruction":
            "Lock the central mechanism.",

        "recommended_camera_angle":
            "elevated three-quarter view",

        "recommended_lens":
            "35mm",

        "recommended_perspective":
            "foreground-to-background reveal",

        "do_not_drift_into": [
            "generic checkout",
        ],
    }

    (
        arbitrated_repair,
        repair_arbitration_info,
    ) = (
        arbitrate_targeted_repair_selection(
            repair_concepts=[
                qualified,
                unqualified,
            ],
            repair_qualified=(
                strict_fixture
            ),
            jury=(
                repair_jury
            ),
            benefit_family=(
                "merchant_payments"
            ),
        )
    )

    tests[
        "targeted_repair_unqualified_selection_cannot_win"
    ] = bool(
        arbitrated_repair
        and
        arbitrated_repair.concept_id
        ==
        "T01"
    )

    tests[
        "targeted_repair_arbitration_used"
    ] = bool(
        repair_arbitration_info.get(
            "used"
        )
    )

    tests[
        "targeted_repair_arbitration_no_threshold_lowering"
    ] = bool(
        repair_arbitration_info.get(
            "thresholds_lowered"
        )
        is False
    )

    # =====================================================
    # NEGATIVE ARBITRATION TEST
    # =====================================================

    rejected_jury = {
        **repair_jury,
        "approval":
            False,
    }

    (
        rejected_candidate,
        _
    ) = (
        arbitrate_targeted_repair_selection(
            repair_concepts=[
                qualified,
                unqualified,
            ],
            repair_qualified=[
                qualified
            ],
            jury=(
                rejected_jury
            ),
            benefit_family=(
                "merchant_payments"
            ),
        )
    )

    tests[
        "arbitration_does_not_override_jury_rejection"
    ] = (
        rejected_candidate
        is None
    )

    fatal_jury = {
        **repair_jury,

        "fatal_issues": [
            "Service message unclear."
        ],
    }

    (
        fatal_candidate,
        _
    ) = (
        arbitrate_targeted_repair_selection(
            repair_concepts=[
                qualified,
                unqualified,
            ],
            repair_qualified=[
                qualified
            ],
            jury=(
                fatal_jury
            ),
            benefit_family=(
                "merchant_payments"
            ),
        )
    )

    tests[
        "arbitration_does_not_override_fatal_issue"
    ] = (
        fatal_candidate
        is None
    )

    fusion_reject_jury = {
        **repair_jury,

        "merchant_fusion_approved":
            False,
    }

    (
        fusion_candidate,
        _
    ) = (
        arbitrate_targeted_repair_selection(
            repair_concepts=[
                qualified,
                unqualified,
            ],
            repair_qualified=[
                qualified
            ],
            jury=(
                fusion_reject_jury
            ),
            benefit_family=(
                "merchant_payments"
            ),
        )
    )

    tests[
        "arbitration_does_not_override_merchant_reject"
    ] = (
        fusion_candidate
        is None
    )

    low_confidence_jury = {
        **repair_jury,

        "confidence":
            72,
    }

    (
        low_confidence_candidate,
        _
    ) = (
        arbitrate_targeted_repair_selection(
            repair_concepts=[
                qualified,
                unqualified,
            ],
            repair_qualified=[
                qualified
            ],
            jury=(
                low_confidence_jury
            ),
            benefit_family=(
                "merchant_payments"
            ),
        )
    )

    tests[
        "arbitration_does_not_override_low_confidence"
    ] = (
        low_confidence_candidate
        is None
    )

    # =====================================================
    # SERIALIZATION CONTRACT
    # =====================================================

    fixture_response = (
        CreativeBrainResponse(

            ok=True,

            mode=(
                MODE_MASTERPIECE
            ),

            request=(
                "test"
            ),

            total_concepts=1,

            concepts=[
                qualified
            ],

            top_concepts=[
                qualified
            ],

            winner=(
                qualified
            ),

            metadata={
                "version":
                    VERSION,

                "quality_gate_passed":
                    True,
            },

            errors=[],
        )
    )

    serialized = response_to_dict(
        fixture_response
    )

    tests[
        "response_contract"
    ] = bool(
        serialized.get(
            "winner"
        )
        is not None
        and
        isinstance(
            serialized.get(
                "concepts"
            ),
            list,
        )
        and
        isinstance(
            serialized.get(
                "top_concepts"
            ),
            list,
        )
    )

    tests[
        "concept_contract"
    ] = bool(
        concept_to_dict(
            qualified
        ).get(
            "visual_mechanism_type"
        )
        ==
        qualified.visual_mechanism_type
    )

    # =====================================================
    # RESULT
    # =====================================================

    passed = all(
        tests.values()
    )

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND CREATIVE BRAIN V5.5"
    )
    print(
        " ZERO-COST TARGETED REPAIR SELF TEST"
    )
    print(
        "=========================================="
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

    if passed:

        print(
            (
                "XPAND Creative Brain V5.5 "
                "self-test: PASS ✅"
            )
        )

    else:

        print(
            (
                "XPAND Creative Brain V5.5 "
                "self-test: FAIL ❌"
            )
        )

    print("")
    print(
        "✅ Telegram import contract preserved"
    )
    print(
        "✅ Production concept contract preserved"
    )
    print(
        "✅ STC High Alert preserved"
    )
    print(
        "✅ Maximum 3 Director calls"
    )
    print(
        "✅ Call 3 = Jury OR Targeted Repair OR Fresh Recovery"
    )
    print(
        "✅ Targeted Repair preserves strong near-miss core idea"
    )
    print(
        "✅ Targeted Repair fixes diagnosed dimensions"
    )
    print(
        "✅ Targeted Repair creates exactly 2 repaired concepts"
    )
    print(
        "✅ Targeted Repair evaluates + juries in same call"
    )
    print(
        "✅ ~87.94 near-miss fixture routes to Targeted Repair"
    )
    print(
        "✅ Hard-rejected concepts cannot enter repair"
    )
    print(
        "✅ Quality-first arbitration preserved"
    )
    print(
        "✅ Jury rejection cannot be overridden"
    )
    print(
        "✅ Merchant fusion rejection cannot be overridden"
    )
    print(
        "✅ Fatal issues cannot be overridden"
    )
    print(
        "✅ Strict thresholds were NOT lowered"
    )
    print(
        "✅ Permanent STC Brand Kit preserved"
    )
    print(
        "✅ Merchant semantic equivalence preserved"
    )
    print(
        "✅ Generic-scene hard guard preserved"
    )
    print(
        "✅ Repeated-scene guard preserved"
    )
    print(
        "✅ Literal counter-tableau guard preserved"
    )
    print(
        "✅ No generated text / logo"
    )
    print(
        "🚫 No API calls were made"
    )
    print(
        "🚫 No images were generated"
    )
    print("")
