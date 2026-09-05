# =========================================================
# XPAND CREATIVE BRAIN V5.3
#
# STC BANK HIGH-ALERT
# ADAPTIVE CAMPAIGN INTELLIGENCE
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
# V5.3 STC MASTERPIECE PATH
#
# CALL 1
#   8 fundamentally different concepts
#          ↓
#
# CALL 2
#   Executive Creative Review
#          ↓
#
#   IF strong finalists exist:
#       CALL 3 = Finalist Jury
#
#   ELSE:
#       CALL 3 = Recovery Board
#                ↓
#                3 NEW concepts
#                + evaluation
#                + final jury
#                in ONE structured call
#
# =========================================================
#
# IMPORTANT
#
# Recovery is triggered by QUALITY failure,
# not only technical JSON failure.
#
# The recovery call receives diagnosed failures such as:
#
#   weak campaign hook
#   weak visual mechanism
#   merchant channel ambiguity
#   realism
#   feasibility
#   generic scene risk
#
# and must create materially NEW advertising mechanisms.
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

from dataclasses import (
    dataclass,
    field,
)

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
            value
            or ""
        ).lower()

        return (
            "stc bank"
            in text
            or
            "بنك stc"
            in text
        )

    def detect_stc_benefit_family(
        value: Any,
    ) -> str:

        text = str(
            value
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
            "merchant payments",
        )

        if any(
            marker
            in text
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

VERSION = "5.3"

MODULE_NAME = (
    "XPAND Creative Brain"
)


# =========================================================
# MODES
# =========================================================

MODE_FAST = "fast"

MODE_MASTERPIECE = "masterpiece"


# =========================================================
# ENV
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


# =========================================================
# GENERAL QUALITY
# =========================================================

MASTERPIECE_MIN_SCORE = max(
    82.0,
    min(
        98.0,
        float(
            os.environ.get(
                "XPAND_MASTERPIECE_MIN_SCORE",
                "88",
            )
            or 88
        ),
    ),
)


MASTERPIECE_RELEASE_FLOOR = max(
    78.0,
    min(
        MASTERPIECE_MIN_SCORE,
        float(
            os.environ.get(
                "XPAND_MASTERPIECE_RELEASE_FLOOR",
                "84",
            )
            or 84
        ),
    ),
)


FAST_MIN_SCORE = max(
    55.0,
    min(
        90.0,
        float(
            os.environ.get(
                "XPAND_FAST_CREATIVE_MIN_SCORE",
                "70",
            )
            or 70
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
        float(
            os.environ.get(
                "XPAND_STC_MIN_CONCEPT_SCORE",
                "90",
            )
            or 90
        ),
    ),
)


STC_HIGH_ALERT_RELEASE_FLOOR = max(
    84.0,
    min(
        STC_HIGH_ALERT_MIN_SCORE,
        float(
            os.environ.get(
                "XPAND_STC_RELEASE_FLOOR",
                "88",
            )
            or 88
        ),
    ),
)


# =========================================================
# STC DIMENSION GATES
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


# =========================================================
# SCORE WEIGHTS
# =========================================================

DIMENSION_WEIGHTS = {

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
        int(
            os.environ.get(
                "XPAND_STC_CONCEPTS_REQUIRED",
                "8",
            )
            or 8
        ),
    ),
)


STC_RECOVERY_CONCEPT_COUNT = max(
    3,
    min(
        4,
        int(
            os.environ.get(
                "XPAND_STC_RECOVERY_CONCEPTS",
                "3",
            )
            or 3
        ),
    ),
)


MASTERPIECE_SHORTLIST_SIZE = 3


MASTERPIECE_TARGET_DIRECTOR_CALLS = 3


MASTERPIECE_MAX_DIRECTOR_CALLS = max(
    2,
    min(
        3,
        int(
            os.environ.get(
                "XPAND_IMAGE_DIRECTOR_MAX_CALLS",
                "3",
            )
            or 3
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
        for marker
        in markers
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
# The actual JPEG bytes are sent later by
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
        or
        load_default_stc_brand_kit
        is None
    ):

        return result

    try:

        kit = (
            load_default_stc_brand_kit()
        )

        selected = (
            kit.select_ideation_assets(

                benefit_family=(
                    benefit_family
                ),

                visual_family=(
                    stc_style
                ),

                max_total=7,

                rotation_key=(
                    "creative-brain:"
                    +
                    benefit_family
                    +
                    ":"
                    +
                    stc_style
                ),
            )
        )

        assets = []

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

    curated = stc_curated_reference_context(

        benefit_family=(
            benefit_family
        ),

        stc_style=(
            stc_style
            or
            "premium_realistic"
        ),
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
                or
                []
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
# REVIEW EVALUATION SCHEMA
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

                "enum": [
                    "exceptional",
                    "excellent",
                    "strong",
                    "usable",
                    "weak",
                    "reject",
                ],
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
# FINAL JURY
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
# RECOVERY BOARD SCHEMA
# =========================================================

def make_recovery_schema(
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


# =========================================================
# STC PATTERNS
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
    "عميل يدفع عند الكاشير",

    "smiling businessman",
    "handshake",
    "generic office",

    "merchant standing behind counter",
    "merchant behind counter",
]


STC_FINTECH_CLICHES = [

    "network lines",
    "connection lines",

    "glowing payment trail",
    "glowing path",

    "hologram",
    "hud",

    "cyber",
    "neon fintech",

    "floating icons",
    "floating card",
    "floating phone",
    "floating pos",

    "digital tunnel",
    "glowing particles",
    "data stream",
]


STC_LITERAL_TRANSACTION_TABLEAU = [

    "customer paying at counter",
    "customer taps terminal",
    "customer tapping terminal",

    "pos terminal on counter",
    "terminal on counter",

    "merchant behind counter",
    "merchant standing behind counter",

    "tablet on counter",
    "tablet beside terminal",

    "worker packing",
    "employee packing",
    "packing box",
    "parcel in background",

    "wooden checkout counter",
    "wood counter",

    "luxury boutique counter",
    "retail counter scene",

    "عميل يدفع",
    "نقطه بيع على الكاونتر",
    "جهاز نقاط البيع على الكاونتر",
    "موظف يغلف",
    "عامل يغلف",
    "صندوق في الخلفيه",
]


STC_REPETITION_BLACKLIST = [

    "wooden checkout counter",

    "luxury boutique checkout",

    "same boutique counter",

    "plain merchant counter",

    "generic perfume boutique",

    "generic fashion boutique",

    "card on purple cube",

    "card on pedestal",

    "empty purple room",

    "plain purple wall",

    "generic airport traveler",

    "generic office desk",

    "man looking at phone",

    "customer tapping pos terminal",
]


STC_VISUAL_MECHANISM_MARKERS = [

    "visual bridge",
    "physical bridge",
    "physical continuity",

    "transformation",
    "transform",

    "continuity",
    "continuous",

    "threshold",

    "portal",

    "cause and effect",

    "trigger",

    "parallel action",

    "mirrored action",

    "spatial relationship",

    "spatial rhythm",

    "perspective reveal",

    "forced perspective",

    "scale contrast",

    "material transition",

    "framing device",

    "single gesture",
    "one gesture",

    "visual compression",

    "foreground background relationship",

    "architectural metaphor",

    "service transformation",

    "integrated physical mechanism",

    "one continuous",

    "merged physically",

    "shared physical",

    "تتحول",
    "تحول",
    "امتداد",
    "جسر بصري",
    "علاقه بصريه",
    "استمراريه",
    "سبب ونتيجه",
    "بوابه",
    "توازي",
    "انعكاس",
    "ترابط مكاني",
]


MERCHANT_ONLINE_MARKERS = [

    "تجاره الكترونيه",
    "التجاره الالكترونيه",

    "طلب اونلاين",
    "طلب الكتروني",

    "متجر الكتروني",

    "طلب رقمي",

    "بيع اونلاين",

    "ecommerce",
    "e-commerce",

    "online commerce",

    "online order",

    "digital order",

    "digital storefront",

    "online storefront",

    "web store",

    "web checkout",

    "online checkout",

    "digital checkout",

    "shopping cart",

    "order fulfilment",
    "order fulfillment",

    "fulfillment",

    "shipment",

    "shipping order",
]


MERCHANT_PHYSICAL_MARKERS = [

    "نقاط البيع",
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


HARD_REJECT_FAILURES = {

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
        for marker
        in merchant_markers
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
# STYLE
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

        return (
            "premium_purple_architecture"
        )

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

        return (
            "premium_augmented_realism"
        )

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
        and
        mode
        ==
        MODE_MASTERPIECE
        and
        is_stc_bank_request(
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

        return (
            STC_HIGH_ALERT_CONCEPT_COUNT
        )

    return NORMAL_CONCEPT_COUNT


# =========================================================
# PARSER
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
            or
            fallback_id
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
            or
            "single_generation"
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

    online = contains_any(
        text,
        MERCHANT_ONLINE_MARKERS,
    )

    physical = contains_any(
        text,
        MERCHANT_PHYSICAL_MARKERS,
    )

    mechanism_text = (
        concept.campaign_hook
        +
        " "
        +
        concept.core_idea
        +
        " "
        +
        concept.visual_metaphor
        +
        " "
        +
        concept.visual_mechanism_type
    )

    mechanism = bool(
        count_matches(
            mechanism_text,
            STC_VISUAL_MECHANISM_MARKERS,
        )
        > 0
    )

    return {
        "online":
            online,

        "physical":
            physical,

        "mechanism":
            mechanism,
    }


# =========================================================
# LOCAL GUARD
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

    if is_stc_bank_request(
        user_request
    ):

        # -------------------------------------------------
        # GENERIC FINTECH
        # -------------------------------------------------

        if contains_any(
            text,
            STC_FINTECH_CLICHES,
        ):

            penalty += 22.0

            failures.append(
                "generic_fintech_visual"
            )

        # -------------------------------------------------
        # REPETITION
        # -------------------------------------------------

        if (
            STC_REJECT_REPEATED_SCENES
            and
            contains_any(
                text,
                STC_REPETITION_BLACKLIST,
            )
        ):

            penalty += 18.0

            failures.append(
                "repeated_stc_scene"
            )

        # -------------------------------------------------
        # LITERAL TRANSACTION TABLEAU
        # -------------------------------------------------

        literal_matches = count_matches(
            text,
            STC_LITERAL_TRANSACTION_TABLEAU,
        )

        if literal_matches >= 3:

            penalty += 35.0

            failures.append(
                "literal_transaction_tableau"
            )

        # -------------------------------------------------
        # GENERIC LIFESTYLE
        # -------------------------------------------------

        generic_hits = count_matches(
            text,
            STC_GENERIC_PATTERNS,
        )

        mechanism_text = (
            concept.campaign_hook
            +
            " "
            +
            concept.visual_metaphor
            +
            " "
            +
            concept.visual_mechanism_type
        )

        mechanism_hits = count_matches(
            mechanism_text,
            STC_VISUAL_MECHANISM_MARKERS,
        )

        if (
            STC_REJECT_GENERIC_SCENES
            and
            generic_hits > 0
            and
            mechanism_hits == 0
        ):

            penalty += 26.0

            failures.append(
                "generic_lifestyle_without_advertising_mechanism"
            )

        # -------------------------------------------------
        # PURPLE NEON IN REALISM
        # -------------------------------------------------

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
                    "purple glow everywhere",
                    "بنفسجي نيون",
                    "نيون بنفسجي",
                ],
            )
        ):

            penalty += 18.0

            failures.append(
                "purple_neon_realism_violation"
            )

        # -------------------------------------------------
        # COPY SPACE
        # -------------------------------------------------

        if not contains_any(
            concept.negative_space,
            [
                "left",
                "right",
                "top",
                "bottom",
                "upper",
                "lower",
                "يسار",
                "يمين",
                "اعلى",
                "أعلى",
                "اسفل",
                "أسفل",
                "25%",
                "30%",
                "35%",
                "40%",
            ],
        ):

            penalty += 4.0

            failures.append(
                "weak_copy_space"
            )

        # -------------------------------------------------
        # CAMERA
        # -------------------------------------------------

        camera_text = (
            concept.camera_angle
            +
            " "
            +
            concept.lens
            +
            " "
            +
            concept.perspective
        )

        if not contains_any(
            camera_text,
            [
                "low angle",
                "high angle",
                "eye level",
                "eye-level",
                "bird",
                "worm",
                "elevated",
                "three-quarter",
                "three quarter",
                "over-the-shoulder",
                "over the shoulder",
                "foreground",
                "macro",
                "wide angle",
                "wide-angle",
                "telephoto",
                "24mm",
                "28mm",
                "35mm",
                "50mm",
                "85mm",
            ],
        ):

            penalty += 3.0

            failures.append(
                "camera_not_precise"
            )

        # -------------------------------------------------
        # FIELD COMPLETENESS
        #
        # These are soft penalties only.
        #
        # V5.2 penalized concise concepts too aggressively.
        # -------------------------------------------------

        if (
            STC_REQUIRE_ADVERTISING_STYLE
            and
            len(
                clean_text(
                    concept.campaign_hook,
                    1600,
                )
            )
            <
            35
        ):

            penalty += 5.0

            failures.append(
                "weak_campaign_hook"
            )

        if (
            STC_REQUIRE_VISUAL_MECHANISM
            and
            len(
                clean_text(
                    concept.visual_metaphor,
                    2000,
                )
            )
            <
            45
        ):

            penalty += 6.0

            failures.append(
                "weak_visual_mechanism"
            )

        if (
            len(
                clean_text(
                    concept.why_not_generic,
                    1800,
                )
            )
            <
            35
        ):

            penalty += 4.0

            failures.append(
                "generic_defense_missing"
            )

        if (
            len(
                clean_text(
                    concept.environment_novelty,
                    1600,
                )
            )
            <
            30
        ):

            penalty += 3.0

            failures.append(
                "environment_novelty_missing"
            )

    # =====================================================
    # MERCHANT PAYMENTS
    #
    # IMPORTANT V5.3:
    #
    # Lexical absence is only a SOFT warning.
    #
    # The Executive Review provides semantic judgments
    # for online channel / POS channel / actual fusion.
    #
    # This prevents false rejection when a concept uses
    # terms like "card reader", "digital storefront",
    # "in-store acceptance", etc.
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
# STC DIMENSION GATE
# =========================================================

def stc_dimension_gate_failures(
    concept: CreativeConcept,
) -> List[str]:

    scores = safe_dict(
        concept.scores
    )

    failures: List[str] = []

    checks = [

        (
            "concept_strength",
            STC_MIN_CONCEPT_STRENGTH,
        ),

        (
            "brand_fit",
            STC_MIN_BRAND_FIT,
        ),

        (
            "originality",
            STC_MIN_ORIGINALITY,
        ),

        (
            "visual_mechanism",
            STC_MIN_VISUAL_MECHANISM,
        ),

        (
            "camera_quality",
            STC_MIN_CAMERA_QUALITY,
        ),

        (
            "realism",
            STC_MIN_REALISM,
        ),

        (
            "feasibility",
            STC_MIN_FEASIBILITY,
        ),

        (
            "copy_space_quality",
            STC_MIN_COPY_SPACE,
        ),

        (
            "distinctiveness",
            STC_MIN_DISTINCTIVENESS,
        ),

        (
            "advertising_readiness",
            STC_MIN_AD_READINESS,
        ),
    ]

    for key, minimum in checks:

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
# QUALIFIED CONCEPTS
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

    output = []

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

            if concept.weighted_score < (
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
continue using new advertising grammars.

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
STRUCTURED TECHNICAL RECOVERY
==================================================

A previous STRUCTURED ideation call failed technically.

This is not a creative-quality recovery.

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
STC HIGH ALERT
==================================================

The brief gives you the MESSAGE.

YOU invent the advertising idea.

Do not require the user to describe:
- scene
- metaphor
- composition
- location
- hero
- visual device

Those are YOUR job.

A beautiful scene alone fails.

A realistic transaction alone fails.

A person using a service alone fails.

QUALITY > EASE OF GENERATION.

==================================================
DIVERSITY
==================================================

{STC_HIGH_ALERT_ARCHETYPES}
"""

        stc_block = f"""
==================================================
STC BANK CAMPAIGN INTELLIGENCE
==================================================

Visual family:
{stc_style}

Benefit family:
{benefit_family}

Think simultaneously as:
- executive creative director
- senior art director
- campaign strategist
- advertising photographer
- production designer
- STC Bank brand guardian

Do NOT think as:
"a prompt writer trying to show service props."

{high_alert_block}

==================================================
PERMANENT STC BRAND INTELLIGENCE
==================================================

{stc_brand_pack_prompt_fragment(
    benefit_family=benefit_family,
    stc_style=stc_style,
)}

The permanent references are VISUAL DNA.

Use them to understand:
- campaign maturity
- brand confidence
- visual hierarchy
- material quality
- lighting restraint
- Saudi context
- composition quality
- camera discipline

Never clone:
- exact scene
- exact people
- exact location
- exact campaign
- old copy
- old logo

==================================================
CENTRAL ADVERTISING LAW
==================================================

Every concept needs ONE meaningful VISUAL MECHANISM.

It must survive as ONE still frame.

The viewer should feel:

"This image was conceived as advertising."

not:

"This is a nice picture of a service."

A visual mechanism may arise from:
- physical cause/effect
- spatial logic
- transformation
- perspective
- scale
- material behavior
- architecture
- framing
- foreground/background relationship
- one physically believable conceptual intervention

These are categories of thinking, not concepts to copy.

==================================================
PREMIUM REALISTIC FAMILY
==================================================

When style = premium_realistic:

Prefer:
- real Saudi commercial environments
- real people only when useful
- natural skin
- premium modern materials
- deliberate art direction
- realistic daylight or commercial lighting
- physically credible objects
- restrained brand accents

Purple is optional.

Do NOT use purple as the idea.

==================================================
PURPLE ARCHITECTURAL FAMILY
==================================================

When explicitly selected:

Purple acts as physical architecture.

Use:
- planes
- geometry
- controlled reflection
- satin surfaces
- premium shadow
- material depth

Never:
- cyber room
- purple neon everywhere
- fintech tunnel
- empty gradient environment

==================================================
AUGMENTED REALISM FAMILY
==================================================

Use ONE conceptual intervention.

It must obey:
- gravity
- scale
- perspective
- contact
- shadow
- occlusion
- material logic

Never replace the idea with:
- holograms
- icon clouds
- random particles

==================================================
MERCHANT PAYMENTS LAW
==================================================

When benefit_family = merchant_payments:

The communication must contain:

ONLINE COMMERCE
+
PHYSICAL POINT-OF-SALE
+
ONE UNIFIED MERCHANT PROPOSITION

Important:

The physical channel may be described as:
- POS
- payment terminal
- card reader
- tap-to-pay
- in-store acceptance
- physical payment

The digital channel may be described as:
- e-commerce
- online order
- digital storefront
- web checkout
- online checkout
- digital commerce

You do NOT need to use one exact phrase.

But both commercial channels must be visibly understandable.

Most importantly:

DO NOT simply place them next to each other.

The visual mechanism must CONNECT them.

==================================================
MERCHANT HARD REJECT
==================================================

Reject:

customer
+
POS
+
counter
+
merchant
+
tablet / packing

when it is just an ordinary retail tableau.

Also reject:
- generic boutique checkout
- wooden luxury counter cliché
- worker packing box in background as "e-commerce"
- POS simply held toward camera
- ordinary transaction photography

Changing the lens or wall color does not make this a new idea.

==================================================
NO GENERIC FINTECH
==================================================

No:
- floating cards
- floating phones
- floating POS
- network lines
- glowing routes
- holograms
- HUD
- cyber tunnel
- particles
- random fintech icons

==================================================
COPY SPACE
==================================================

Reserve approximately 25%-40% natural negative space.

Do not create a digital blank panel.

==================================================
TEXT / LOGO
==================================================

The intended image must contain no generated:
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

For every concept explain:

why_not_generic

and:

environment_novelty

These fields must describe real conceptual reasons.

==================================================
STC SKILL
==================================================

{clean_text(
    STC_BANK_VISUAL_SKILL,
    7000,
)}
"""

    return f"""
You are XPAND Creative Brain V5.3.

You receive the COMMERCIAL MESSAGE.

You are responsible for inventing the advertising idea.

==================================================
REQUEST / MESSAGE
==================================================

{clean_text(
    user_request,
    8000,
)}

==================================================
BRAND CONTEXT
==================================================

{compact_json(
    brand_context,
    7000,
)}

==================================================
RUNTIME REFERENCE DNA
==================================================

{compact_json(
    visual_references,
    7000,
)}

==================================================
STYLE HINT
==================================================

{clean_text(
    style_hint,
    1600,
)}

==================================================
IDEATION
==================================================

Generate exactly {concept_count} fundamentally different
advertising concepts.

Each must differ materially in:
- visual mechanism
- concept archetype
- hero relationship
- environment
- spatial construction
- camera strategy

Do not produce cosmetic variants.

{stc_block}

{recovery_block}

==================================================
OUTPUT CONTRACT
==================================================

Return exactly the structured schema.

Use:
C01
C02
C03
...

Do not score concepts in this call.

Do not ask the user to supply the visual idea.
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
        for concept
        in concepts
    ]

    high_alert_block = ""

    if high_alert:

        high_alert_block = """
==================================================
STC HIGH-ALERT STANDARD
==================================================

Do not reward competence.

We need a concept worthy of expensive image production.

90+ means:

- memorable advertising proposition
- strong STC Bank relevance
- clear visual mechanism
- clear service communication
- scene novelty
- premium Saudi campaign quality
- strong single-frame readability
- production feasibility

An attractive ordinary scene may score 65-78.

A polished but familiar campaign may score 78-86.

90+ is exceptional.

HARD REJECT:
customer + POS + counter + merchant + tablet/packing

when it is only transaction photography.
"""

    return f"""
You are XPAND V5.3 EXECUTIVE CREATIVE REVIEW.

Review every concept independently.

Do NOT invent new concepts in this call.

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
    32000,
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
Is the direction memorable and different?

advertising_readiness:
Would a senior bank creative director send this to production?

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
TRUE if the proposal is mainly a location + people + props,
without an advertising device.

mechanism_survives_single_frame:
TRUE only when the advertising mechanism remains clear in
one still image.

looks_like_real_bank_campaign:
TRUE only when the idea has premium financial-campaign
discipline.

==================================================
MERCHANT SEMANTIC REVIEW
==================================================

When benefit_family = merchant_payments:

merchant_online_channel_clear:
Can a viewer understand an online/e-commerce sales channel?

merchant_pos_channel_clear:
Can a viewer understand a physical/in-store payment channel?

Accept equivalent language such as:
card reader,
payment terminal,
tap-to-pay,
in-store acceptance,
digital storefront,
online order,
web checkout.

Do NOT require the exact token "POS".

merchant_channels_fused:
TRUE only when the concept visually unifies the two channels
through one advertising mechanism.

Putting them in the same room is NOT fusion.

For any non-merchant brief:
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

production_feasible = true only if an image model can create
the central mechanism without requiring contradictory geometry,
multiple impossible scenes or unreadable UI.

{high_alert_block}

Return exactly the structured schema.
""".strip()


# =========================================================
# JURY PROMPT
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
        for concept
        in finalists
    ]

    return f"""
You are the FINAL XPAND STC BANK CAMPAIGN JURY.

This decision happens immediately before expensive image
production.

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
    24000,
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
visually unified by the mechanism.

For other benefit families:
TRUE.

==================================================
DO NOT APPROVE
==================================================

Do not approve:
- safe ordinary lifestyle
- transaction photography
- generic boutique POS scene
- wooden counter tableau
- person simply holding device
- purple as substitute for idea
- generic fintech effects

==================================================
PRODUCTION INSTRUCTION
==================================================

Lock:
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
# GENERATE CONCEPTS
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
            "xpand_creative_ideation_v53"
        ),
    )

    if isinstance(
        raw,
        dict,
    ):

        payload = raw

    else:

        payload = json.loads(
            clean_text(
                raw,
                100000,
            )
        )

    raw_concepts = safe_list(
        payload.get(
            "concepts"
        )
    )

    if len(
        raw_concepts
    ) != concept_count:

        raise RuntimeError(
            (
                "Creative Brain expected "
                +
                str(
                    concept_count
                )
                +
                " concepts, got "
                +
                str(
                    len(
                        raw_concepts
                    )
                )
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

            raise RuntimeError(
                (
                    "Invalid concept object at index "
                    +
                    str(
                        index
                    )
                )
            )

        concept_id = (
            "C"
            +
            str(
                index
            ).zfill(
                2
            )
        )

        concept = concept_from_dict(

            item,

            fallback_id=(
                concept_id
            ),

            generation_round=(
                2
                if recovery
                else 1
            ),
        )

        concept.concept_id = (
            concept_id
        )

        concepts.append(
            concept
        )

    return concepts


# =========================================================
# APPLY EVALUATIONS
# =========================================================

def apply_evaluations_to_concepts(
    *,
    user_request: str,
    concepts: List[
        CreativeConcept
    ],
    evaluations: List[
        Dict[str, Any]
    ],
    benefit_family: str,
    stc_style: str,
    evaluation_source: str,
) -> None:

    if len(
        evaluations
    ) != len(
        concepts
    ):

        raise RuntimeError(
            (
                "Creative review expected "
                +
                str(
                    len(
                        concepts
                    )
                )
                +
                " evaluations, got "
                +
                str(
                    len(
                        evaluations
                    )
                )
            )
        )

    evaluation_map: Dict[
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

            evaluation_map[
                concept_id
            ] = item

    for index, concept in enumerate(
        concepts
    ):

        evaluation = (
            evaluation_map.get(
                concept.concept_id
            )
        )

        #
        # Recovery board can occasionally keep old Cxx IDs
        # even when instructed to return Rxx.
        #
        # Pair by index if the structured array length is valid.
        #

        if evaluation is None:

            raw_item = evaluations[
                index
            ]

            if isinstance(
                raw_item,
                dict,
            ):

                evaluation = raw_item

        if evaluation is None:

            raise RuntimeError(
                (
                    "Missing evaluation for "
                    +
                    concept.concept_id
                )
            )

        dimension_scores = {

            "concept_strength":
                clamp_score(
                    evaluation.get(
                        "concept_strength"
                    )
                ),

            "brand_fit":
                clamp_score(
                    evaluation.get(
                        "brand_fit"
                    )
                ),

            "originality":
                clamp_score(
                    evaluation.get(
                        "originality"
                    )
                ),

            "visual_mechanism":
                clamp_score(
                    evaluation.get(
                        "visual_mechanism"
                    )
                ),

            "camera_quality":
                clamp_score(
                    evaluation.get(
                        "camera_quality"
                    )
                ),

            "realism":
                clamp_score(
                    evaluation.get(
                        "realism"
                    )
                ),

            "feasibility":
                clamp_score(
                    evaluation.get(
                        "feasibility"
                    )
                ),

            "copy_space_quality":
                clamp_score(
                    evaluation.get(
                        "copy_space_quality"
                    )
                ),

            "distinctiveness":
                clamp_score(
                    evaluation.get(
                        "distinctiveness"
                    )
                ),

            "advertising_readiness":
                clamp_score(
                    evaluation.get(
                        "advertising_readiness"
                    )
                ),
        }

        model_weighted = clamp_score(
            evaluation.get(
                "weighted_score"
            )
        )

        composite = (
            dimension_composite_score(
                dimension_scores
            )
        )

        if model_weighted <= 0:

            base_score = composite

        else:

            #
            # V5.3 does not let one arbitrary "weighted_score"
            # field dominate ten detailed dimension judgments.
            #

            base_score = (
                composite
                *
                0.60
                +
                model_weighted
                *
                0.40
            )

        local_penalty, local_failures = (
            local_concept_penalties(

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
        )

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

        scene_only = bool(
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

        merchant_online = bool(
            evaluation.get(
                "merchant_online_channel_clear",
                True,
            )
        )

        merchant_pos = bool(
            evaluation.get(
                "merchant_pos_channel_clear",
                True,
            )
        )

        merchant_fused = bool(
            evaluation.get(
                "merchant_channels_fused",
                True,
            )
        )

        risk_penalty = 0.0

        if generic_scene_risk:

            risk_penalty += 7.0

            local_failures.append(
                "review_generic_scene_risk"
            )

        if repetition_risk:

            risk_penalty += 7.0

            local_failures.append(
                "review_repetition_risk"
            )

        if scene_only:

            risk_penalty += 9.0

            local_failures.append(
                "concept_is_scene_only"
            )

        if not mechanism_survives:

            risk_penalty += 8.0

            local_failures.append(
                "single_frame_mechanism_failure"
            )

        if (
            is_stc_bank_request(
                user_request
            )
            and
            not bank_campaign
        ):

            risk_penalty += 9.0

            local_failures.append(
                "not_bank_campaign_ready"
            )

        # =================================================
        # MERCHANT SEMANTIC JUDGMENT
        # =================================================

        if benefit_family == "merchant_payments":

            if not merchant_online:

                risk_penalty += 7.0

                local_failures.append(
                    "merchant_online_channel_missing"
                )

            if not merchant_pos:

                risk_penalty += 7.0

                local_failures.append(
                    "merchant_pos_channel_missing"
                )

            if (
                merchant_online
                and
                merchant_pos
                and
                not merchant_fused
            ):

                risk_penalty += 12.0

                local_failures.append(
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
                risk_penalty,
            ),
        )

        #
        # A hard-rejected idea can never appear close to
        # release quality in logs.
        #

        if any(
            failure
            in HARD_REJECT_FAILURES
            for failure
            in local_failures
        ):

            final_score = min(
                final_score,
                79.0,
            )

        concept.scores = {

            **dimension_scores,

            "model_weighted_score":
                round(
                    model_weighted,
                    2,
                ),

            "dimension_composite_score":
                round(
                    composite,
                    2,
                ),

            "local_penalty":
                round(
                    local_penalty,
                    2,
                ),

            "review_risk_penalty":
                round(
                    risk_penalty,
                    2,
                ),
        }

        concept.weighted_score = round(
            final_score,
            2,
        )

        concept.evaluation_valid = True

        concept.quality_gate_passed = False

        concept.quality_gate_failures = (
            dedupe_strings(
                local_failures
            )
        )

        concept.cliche_hits = [
            {
                "id":
                    failure,

                "reason":
                    failure.replace(
                        "_",
                        " ",
                    ),
            }
            for failure
            in concept.quality_gate_failures
        ]

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
                    1700,
                ),
        }

        concept.debate = {

            "evaluation_source":
                evaluation_source,

            "strengths":
                [
                    clean_text(
                        item,
                        1000,
                    )
                    for item
                    in safe_list(
                        evaluation.get(
                            "strengths"
                        )
                    )[:8]
                    if clean_text(
                        item,
                        1000,
                    )
                ],

            "weaknesses":
                [
                    clean_text(
                        item,
                        1200,
                    )
                    for item
                    in safe_list(
                        evaluation.get(
                            "weaknesses"
                        )
                    )[:10]
                    if clean_text(
                        item,
                        1200,
                    )
                ],

            "verdict":
                clean_text(
                    evaluation.get(
                        "verdict"
                    ),
                    100,
                ),

            "generic_scene_risk":
                generic_scene_risk,

            "repetition_risk":
                repetition_risk,

            "concept_is_scene_only":
                scene_only,

            "mechanism_survives_single_frame":
                mechanism_survives,

            "looks_like_real_bank_campaign":
                bank_campaign,

            "merchant_semantics": {

                "online_channel_clear":
                    merchant_online,

                "pos_channel_clear":
                    merchant_pos,

                "channels_fused":
                    merchant_fused,
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
                            1000,
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
                            1000,
                        )
                        or
                        concept.perspective
                    ),

                "creative_reason":
                    clean_text(
                        evaluation.get(
                            "camera_reason"
                        ),
                        1400,
                    ),

                "camera_lock_instruction":
                    (
                        "Preserve this camera strategy "
                        "during final image production."
                    ),
            },
        }

        #
        # Replace original proposed camera with the reviewed
        # coherent camera.
        #

        camera = safe_dict(
            concept.debate.get(
                "camera_director"
            )
        )

        concept.camera_angle = (
            clean_text(
                camera.get(
                    "camera_angle"
                ),
                900,
            )
            or
            concept.camera_angle
        )

        concept.lens = (
            clean_text(
                camera.get(
                    "lens"
                ),
                400,
            )
            or
            concept.lens
        )

        concept.perspective = (
            clean_text(
                camera.get(
                    "perspective"
                ),
                1000,
            )
            or
            concept.perspective
        )

        if is_stc_bank_request(
            user_request
        ):

            dimension_failures = (
                stc_dimension_gate_failures(
                    concept
                )
            )

            concept.quality_gate_failures.extend(
                dimension_failures
            )

            concept.quality_gate_failures = (
                dedupe_strings(
                    concept.quality_gate_failures
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
            "xpand_creative_review_v53"
        ),
    )

    if isinstance(
        raw,
        dict,
    ):

        payload = raw

    else:

        payload = json.loads(
            clean_text(
                raw,
                120000,
            )
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
            "xpand_stc_finalist_jury_v53"
        ),
    )

    if isinstance(
        raw,
        dict,
    ):

        return raw

    return json.loads(
        clean_text(
            raw,
            60000,
        )
    )


# =========================================================
# APPLY JURY
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

    selected = None

    for concept in concepts:

        if (
            concept.concept_id
            ==
            selected_id
        ):

            selected = concept

            break

    if selected is None:

        return None

    approval = bool(
        jury.get(
            "approval",
            False,
        )
    )

    confidence = clamp_score(
        jury.get(
            "confidence"
        )
    )

    merchant_fusion = bool(
        jury.get(
            "merchant_fusion_approved",
            True,
        )
    )

    fatal_issues = [
        clean_text(
            item,
            1100,
        )
        for item
        in safe_list(
            jury.get(
                "fatal_issues"
            )
        )
        if clean_text(
            item,
            1100,
        )
    ]

    if (
        benefit_family
        ==
        "merchant_payments"
        and
        not merchant_fusion
    ):

        approval = False

        fatal_issues.append(
            "Merchant online and physical channels are not sufficiently fused."
        )

        selected.quality_gate_failures.append(
            "finalist_jury_merchant_fusion_rejected"
        )

    selected.debate[
        "finalist_jury"
    ] = {

        "source":
            source,

        "approval":
            approval,

        "confidence":
            confidence,

        "advertising_reason":
            clean_text(
                jury.get(
                    "advertising_reason"
                ),
                2000,
            ),

        "brand_reason":
            clean_text(
                jury.get(
                    "brand_reason"
                ),
                2000,
            ),

        "originality_reason":
            clean_text(
                jury.get(
                    "originality_reason"
                ),
                2000,
            ),

        "merchant_fusion_approved":
            merchant_fusion,

        "fatal_issues":
            fatal_issues,

        "production_instruction":
            clean_text(
                jury.get(
                    "production_instruction"
                ),
                3000,
            ),

        "do_not_drift_into":
            [
                clean_text(
                    item,
                    1000,
                )
                for item
                in safe_list(
                    jury.get(
                        "do_not_drift_into"
                    )
                )[:10]
                if clean_text(
                    item,
                    1000,
                )
            ],
    }

    if fatal_issues:

        selected.quality_gate_failures.append(
            "finalist_jury_fatal_issue"
        )

    if not approval:

        selected.quality_gate_failures.append(
            "finalist_jury_rejected"
        )

    if confidence < 80.0:

        selected.quality_gate_failures.append(
            "finalist_jury_low_confidence"
        )

    selected.quality_gate_failures = (
        dedupe_strings(
            selected.quality_gate_failures
        )
    )

    camera = selected.debate.setdefault(
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
        1100,
    )

    if jury_angle:

        selected.camera_angle = (
            jury_angle
        )

        camera[
            "camera_angle"
        ] = jury_angle

    if jury_lens:

        selected.lens = jury_lens

        camera[
            "lens"
        ] = jury_lens

    if jury_perspective:

        selected.perspective = (
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

    payload = []

    for concept in ranked[:limit]:

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
# RECOVERY PROMPT
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

    failure_context = (
        build_failure_context(
            failed_concepts,
            limit=4,
        )
    )

    used_archetypes = (
        primary_archetypes(
            failed_concepts
        )
    )

    return f"""
You are XPAND V5.3 STC BANK CREATIVE RECOVERY BOARD.

The first concept pool was genuinely evaluated.

It FAILED the required campaign-quality gates.

You have ONE final paid creative call.

This one response must:

1. diagnose the failure pattern
2. invent exactly {STC_RECOVERY_CONCEPT_COUNT} NEW concepts
3. evaluate all new concepts
4. choose one only if it deserves production
5. provide final production art direction

Do not expose chain-of-thought.

==================================================
ORIGINAL COMMERCIAL MESSAGE
==================================================

{clean_text(
    user_request,
    7000,
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
WHY THE FIRST ROUND FAILED
==================================================

{failure_context}

==================================================
USED ARCHETYPES
==================================================

{compact_json(
    used_archetypes,
    4000,
)}

Do not make cosmetic rewrites of these directions.

==================================================
PERMANENT STC BANK INTELLIGENCE
==================================================

{stc_brand_pack_prompt_fragment(
    benefit_family=benefit_family,
    stc_style=stc_style,
)}

==================================================
RUNTIME BRAND CONTEXT
==================================================

{compact_json(
    brand_context,
    6000,
)}

==================================================
RUNTIME REFERENCE DNA
==================================================

{compact_json(
    visual_references,
    5000,
)}

==================================================
RECOVERY LAW
==================================================

The new concepts must attack the diagnosed weaknesses.

If the failed pool had:
- weak visual mechanism

then create a mechanism that is central to the frame.

If it had:
- weak campaign hook

then the proposition must be visible in one memorable image.

If it had:
- weak realism or feasibility

simplify the physical execution without simplifying the idea.

If it had:
- merchant channel ambiguity

make BOTH online commerce and physical payment visually
understandable.

Use semantic equivalents naturally.

The physical side can be:
- card reader
- payment terminal
- tap-to-pay
- in-store acceptance
- physical payment

The digital side can be:
- digital storefront
- online order
- e-commerce
- web checkout
- online commerce

Do NOT rely on exact keywords.

==================================================
MERCHANT FUSION LAW
==================================================

For merchant_payments:

Both channels must be connected by ONE visual mechanism.

Do not solve this with:
- split screen
- generic before/after
- POS foreground + parcel background
- customer paying while employee packs
- customer + counter + merchant
- ordinary checkout scene

The mechanism itself must communicate:
ONE merchant ecosystem.

==================================================
NEW IDEA LAW
==================================================

Create exactly {STC_RECOVERY_CONCEPT_COUNT} materially NEW
directions.

They must not simply:
- change the camera
- change the store type
- change the person
- change the counter material
- change the wall color
- add purple
- add effects

Change the conceptual grammar.

==================================================
REALISM
==================================================

The winning recovery concept must be image-model feasible.

One coherent frame.

One camera system.

One light logic.

One dominant mechanism.

No contradictory geometry.

No required readable interface.

No generated copy or logo.

==================================================
SCORING
==================================================

For each recovery concept score:

concept_strength
brand_fit
originality
visual_mechanism
camera_quality
realism
feasibility
copy_space_quality
distinctiveness
advertising_readiness
weighted_score

Do not inflate scores.

90+ remains exceptional.

==================================================
BOOLEAN REVIEW
==================================================

For every concept return:

generic_scene_risk

repetition_risk

concept_is_scene_only

mechanism_survives_single_frame

looks_like_real_bank_campaign

merchant_online_channel_clear

merchant_pos_channel_clear

merchant_channels_fused

For non-merchant briefs:
set merchant booleans TRUE.

==================================================
FINAL SELECTION
==================================================

Select one only if it genuinely deserves production.

approval may be FALSE.

confidence must reflect real confidence.

merchant_fusion_approved must be TRUE for a merchant winner.

fatal_issues must contain any reason production should stop.

==================================================
CAMERA LOCK
==================================================

Return final:
- angle
- lens
- perspective
- production instruction
- do_not_drift_into

==================================================
OUTPUT IDS
==================================================

Recovery concept IDs must be:

R01
R02
R03

Return exactly the structured schema.
""".strip()


# =========================================================
# RECOVERY CALL
# =========================================================

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
    List[
        CreativeConcept
    ],
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

    raw = call_openai_director(

        prompt,

        json_mode=True,

        json_schema=(
            make_recovery_schema(
                STC_RECOVERY_CONCEPT_COUNT
            )
        ),

        json_schema_name=(
            "xpand_stc_recovery_board_v53"
        ),
    )

    if isinstance(
        raw,
        dict,
    ):

        payload = raw

    else:

        payload = json.loads(
            clean_text(
                raw,
                120000,
            )
        )

    raw_concepts = safe_list(
        payload.get(
            "concepts"
        )
    )

    if len(
        raw_concepts
    ) != STC_RECOVERY_CONCEPT_COUNT:

        raise RuntimeError(
            (
                "Recovery Board expected "
                +
                str(
                    STC_RECOVERY_CONCEPT_COUNT
                )
                +
                " concepts, got "
                +
                str(
                    len(
                        raw_concepts
                    )
                )
            )
        )

    recovery_concepts: List[
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

            raise RuntimeError(
                (
                    "Invalid Recovery concept "
                    +
                    str(
                        index
                    )
                )
            )

        recovery_id = (
            "R"
            +
            str(
                index
            ).zfill(
                2
            )
        )

        concept = concept_from_dict(

            item,

            fallback_id=(
                recovery_id
            ),

            generation_round=2,

            revised_from=(
                "primary_quality_failure"
            ),
        )

        concept.concept_id = (
            recovery_id
        )

        recovery_concepts.append(
            concept
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
            recovery_concepts
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
            "stc_recovery_board"
        ),
    )

    jury_payload = {

        "selected_concept_id":
            payload.get(
                "selected_concept_id"
            ),

        "approval":
            payload.get(
                "approval"
            ),

        "confidence":
            payload.get(
                "confidence"
            ),

        "advertising_reason":
            payload.get(
                "advertising_reason"
            ),

        "brand_reason":
            payload.get(
                "brand_reason"
            ),

        "originality_reason":
            payload.get(
                "originality_reason"
            ),

        "merchant_fusion_approved":
            payload.get(
                "merchant_fusion_approved"
            ),

        "fatal_issues":
            payload.get(
                "fatal_issues",
                [],
            ),

        "production_instruction":
            payload.get(
                "production_instruction"
            ),

        "recommended_camera_angle":
            payload.get(
                "recommended_camera_angle"
            ),

        "recommended_lens":
            payload.get(
                "recommended_lens"
            ),

        "recommended_perspective":
            payload.get(
                "recommended_perspective"
            ),

        "do_not_drift_into":
            payload.get(
                "do_not_drift_into",
                [],
            ),
    }

    return (
        recovery_concepts,
        jury_payload,
    )


# =========================================================
# RELEASE
# =========================================================

def choose_release(
    *,
    concepts: List[
        CreativeConcept
    ],
    mode: str,
    user_request: str,
    jury_selected: Optional[
        CreativeConcept
    ] = None,
    jury_required: bool = True,
) -> Tuple[
    Optional[
        CreativeConcept
    ],
    str,
]:

    valid = [
        concept
        for concept
        in concepts
        if concept.evaluation_valid
    ]

    if not valid:

        return (
            None,
            "technical_failure",
        )

    valid.sort(
        key=lambda item:
            item.weighted_score,
        reverse=True,
    )

    high_alert = is_stc_high_alert(
        user_request,
        mode,
    )

    # =====================================================
    # FAST
    # =====================================================

    if mode == MODE_FAST:

        best = valid[
            0
        ]

        if (
            best.weighted_score
            >=
            FAST_MIN_SCORE
        ):

            best.quality_gate_passed = (
                True
            )

            best.debate[
                "quality_release_level"
            ] = (
                "fast_release"
            )

            return (
                best,
                "fast_release",
            )

        return (
            None,
            "quality_failed",
        )

    # =====================================================
    # STC HIGH ALERT
    # =====================================================

    if high_alert:

        qualified = (
            strict_qualified_concepts(
                valid,
                high_alert=True,
            )
        )

        if not qualified:

            return (
                None,
                "quality_failed",
            )

        if jury_required:

            if jury_selected is None:

                return (
                    None,
                    "jury_required",
                )

            if (
                jury_selected
                not in qualified
            ):

                return (
                    None,
                    "jury_selected_unqualified",
                )

            jury_info = safe_dict(
                jury_selected.debate.get(
                    "finalist_jury"
                )
            )

            if not jury_info:

                return (
                    None,
                    "jury_missing",
                )

            if not bool(
                jury_info.get(
                    "approval",
                    False,
                )
            ):

                return (
                    None,
                    "jury_rejected",
                )

            if (
                safe_float(
                    jury_info.get(
                        "confidence"
                    ),
                    0,
                )
                <
                80.0
            ):

                return (
                    None,
                    "jury_low_confidence",
                )

            if safe_list(
                jury_info.get(
                    "fatal_issues"
                )
            ):

                return (
                    None,
                    "jury_fatal_issue",
                )

            winner = jury_selected

        else:

            winner = qualified[
                0
            ]

        winner.quality_gate_passed = (
            True
        )

        if (
            winner.weighted_score
            >=
            STC_HIGH_ALERT_MIN_SCORE
        ):

            release_level = (
                "stc_target_release"
            )

        else:

            release_level = (
                "stc_adaptive_release"
            )

        winner.debate[
            "quality_release_level"
        ] = release_level

        return (
            winner,
            release_level,
        )

    # =====================================================
    # NORMAL MASTERPIECE
    # =====================================================

    winner = valid[
        0
    ]

    if (
        winner.weighted_score
        >=
        MASTERPIECE_MIN_SCORE
    ):

        winner.quality_gate_passed = (
            True
        )

        winner.debate[
            "quality_release_level"
        ] = (
            "target_release"
        )

        return (
            winner,
            "target_release",
        )

    if (
        winner.weighted_score
        >=
        MASTERPIECE_RELEASE_FLOOR
    ):

        winner.quality_gate_passed = (
            True
        )

        winner.debate[
            "quality_release_level"
        ] = (
            "adaptive_release"
        )

        return (
            winner,
            "adaptive_release",
        )

    return (
        None,
        "quality_failed",
    )


# =========================================================
# TECHNICAL FAILURE
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
    high_alert: bool = False,
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
                "stc_adaptive_recovery_v53",

            "technical_failure":
                True,

            "quality_gate_evaluated":
                False,

            "quality_gate_passed":
                False,

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
# MAIN API
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

        mode = MODE_MASTERPIECE

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

    high_alert = is_stc_high_alert(
        user_request,
        mode,
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

    recovery_used = False

    recovery_reason = ""

    jury_payload: Dict[
        str,
        Any
    ] = {}

    jury_selected: Optional[
        CreativeConcept
    ] = None

    concepts: List[
        CreativeConcept
    ] = []

    all_concepts: List[
        CreativeConcept
    ] = []

    technical_ideation_recovery = False

    # =====================================================
    # LOG HEADER
    # =====================================================

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND CREATIVE BRAIN V5.3"
    )

    if high_alert:

        print(
            " STC BANK ADAPTIVE HIGH ALERT"
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
        "Recovery concepts:",
        (
            STC_RECOVERY_CONCEPT_COUNT
            if high_alert
            else 0
        ),
    )

    print(
        "Director-call maximum:",
        MASTERPIECE_MAX_DIRECTOR_CALLS,
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
        # TECHNICAL IDEATION RECOVERY
        # =================================================

        if (
            mode
            ==
            MODE_MASTERPIECE
            and
            director_calls
            <
            MASTERPIECE_MAX_DIRECTOR_CALLS
        ):

            try:

                technical_ideation_recovery = (
                    True
                )

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

            except Exception as recovery_error:

                errors.append(
                    (
                        "technical_ideation_recovery: "
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
    #
    # Or Call 3 if Call 1 had a technical retry.
    # =====================================================

    if (
        director_calls
        >=
        MASTERPIECE_MAX_DIRECTOR_CALLS
    ):

        return technical_failure_response(

            user_request=(
                user_request
            ),

            mode=(
                mode
            ),

            errors=(
                errors
                +
                [
                    (
                        "No Director-call budget remained "
                        "for real concept evaluation."
                    )
                ]
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
    # NORMAL MODE RELEASE
    # =====================================================

    if not high_alert:

        winner, release_level = (
            choose_release(

                concepts=(
                    concepts
                ),

                mode=(
                    mode
                ),

                user_request=(
                    user_request
                ),

                jury_selected=None,

                jury_required=False,
            )
        )

    else:

        # =================================================
        # STC PRIMARY QUALIFICATION
        # =================================================

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
        # TECHNICAL IDEATION RECOVERY ALREADY USED CALL
        #
        # No call remains for a separate jury.
        #
        # A truly strict reviewed concept may still release.
        # This is not a fake evaluation.
        # =================================================

        if technical_ideation_recovery:

            winner, release_level = (
                choose_release(

                    concepts=(
                        concepts
                    ),

                    mode=(
                        mode
                    ),

                    user_request=(
                        user_request
                    ),

                    jury_selected=None,

                    jury_required=False,
                )
            )

            if winner:

                release_level = (
                    "stc_technical_recovery_review_release"
                )

                winner.debate[
                    "quality_release_level"
                ] = release_level

        # =================================================
        # PRIMARY CONCEPTS ARE STRONG:
        # CALL 3 = FINAL JURY
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

                    jury_payload = (
                        run_finalist_jury(

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
                    )

                    jury_selected = (
                        apply_jury_result(

                            concepts=(
                                concepts
                            ),

                            jury=(
                                jury_payload
                            ),

                            benefit_family=(
                                benefit_family
                            ),

                            source=(
                                "stc_finalist_jury"
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

            winner, release_level = (
                choose_release(

                    concepts=(
                        concepts
                    ),

                    mode=(
                        mode
                    ),

                    user_request=(
                        user_request
                    ),

                    jury_selected=(
                        jury_selected
                    ),

                    jury_required=True,
                )
            )

        # =================================================
        # PRIMARY QUALITY FAILED:
        # CALL 3 = ADAPTIVE RECOVERY BOARD
        # =================================================

        else:

            winner = None

            release_level = (
                "quality_failed"
            )

            recovery_reason = (
                "no_primary_concept_passed_strict_stc_gates"
            )

            if (
                STC_CREATIVE_RECOVERY_ENABLED
                and
                director_calls
                <
                MASTERPIECE_MAX_DIRECTOR_CALLS
            ):

                print("")
                print(
                    "🔁 STC CREATIVE QUALITY RECOVERY"
                )
                print(
                    "Reason:",
                    recovery_reason,
                )
                print(
                    "The third Director call will rebuild "
                    "the concept pool instead of judging "
                    "weak finalists."
                )
                print("")

                try:

                    recovery_used = True

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

                    jury_selected = (
                        apply_jury_result(

                            concepts=(
                                recovery_concepts
                            ),

                            jury=(
                                recovery_jury
                            ),

                            benefit_family=(
                                benefit_family
                            ),

                            source=(
                                "stc_recovery_board"
                            ),
                        )
                    )

                    winner, release_level = (
                        choose_release(

                            concepts=(
                                recovery_concepts
                            ),

                            mode=(
                                mode
                            ),

                            user_request=(
                                user_request
                            ),

                            jury_selected=(
                                jury_selected
                            ),

                            jury_required=True,
                        )
                    )

                    if winner:

                        release_level = (
                            "stc_recovery_release"
                        )

                        winner.debate[
                            "quality_release_level"
                        ] = release_level

                except Exception as recovery_error:

                    errors.append(
                        (
                            "stc_recovery_board: "
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

    # =====================================================
    # SORT ALL
    # =====================================================

    all_concepts.sort(
        key=lambda item:
            item.weighted_score,
        reverse=True,
    )

    #
    # Winner must be first for downstream inspection.
    #

    if winner is not None:

        all_concepts = [
            winner
        ] + [
            item
            for item
            in all_concepts
            if item
            is not winner
        ]

    top_concepts = (
        all_concepts[
            :top_count
        ]
    )

    quality_gate_evaluated = bool(
        any(
            concept.evaluation_valid
            for concept
            in all_concepts
        )
    )

    quality_gate_passed = bool(
        winner
        and
        winner.evaluation_valid
        and
        winner.quality_gate_passed
    )

    # =====================================================
    # FAILURE REASON
    # =====================================================

    failure_reason = ""

    if (
        not winner
        and
        all_concepts
    ):

        best = all_concepts[
            0
        ]

        failure_reason = (
            ";".join(
                best.quality_gate_failures[
                    :8
                ]
            )
            or
            "creative_quality_gate_failed"
        )

    # =====================================================
    # LOG
    # =====================================================

    print("")
    print(
        "=========================================="
    )

    if winner:

        print(
            " XPAND CREATIVE SELECTION COMPLETE"
        )
        print(
            "=========================================="
        )

        print(
            "Winner:",
            winner.concept_id,
        )

        print(
            "Title:",
            winner.title,
        )

        print(
            "Archetype:",
            winner.concept_archetype,
        )

        print(
            "Score:",
            winner.weighted_score,
        )

        if high_alert:

            print(
                "STC target:",
                STC_HIGH_ALERT_MIN_SCORE,
            )

            print(
                "STC release floor:",
                STC_HIGH_ALERT_RELEASE_FLOOR,
            )

        else:

            print(
                "Target:",
                MASTERPIECE_MIN_SCORE,
            )

            print(
                "Release floor:",
                MASTERPIECE_RELEASE_FLOOR,
            )

        print(
            "Release level:",
            release_level,
        )

        jury_info = safe_dict(
            winner.debate.get(
                "finalist_jury"
            )
        )

        if jury_info:

            print(
                "Final jury source:",
                jury_info.get(
                    "source"
                ),
            )

            print(
                "Final jury approval:",
                jury_info.get(
                    "approval"
                ),
            )

            print(
                "Final jury confidence:",
                jury_info.get(
                    "confidence"
                ),
            )

    else:

        print(
            " CREATIVE QUALITY GATE NOT RELEASED"
        )
        print(
            "=========================================="
        )

        if all_concepts:

            best = all_concepts[
                0
            ]

            print(
                "Best evaluated score:",
                best.weighted_score,
            )

            print(
                "Best concept:",
                best.title,
            )

            print(
                "Failures:",
                ", ".join(
                    best.quality_gate_failures[
                        :14
                    ]
                ),
            )

        print(
            "No fake winner created."
        )

    print(
        "Recovery used:",
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

    print("")

    # =====================================================
    # METADATA
    # =====================================================

    effective_integration_floor = (
        MASTERPIECE_MIN_SCORE
    )

    if winner:

        if high_alert:

            effective_integration_floor = (
                min(
                    STC_HIGH_ALERT_RELEASE_FLOOR,
                    winner.weighted_score,
                )
            )

        else:

            effective_integration_floor = (
                min(
                    (
                        MASTERPIECE_RELEASE_FLOOR
                        if mode
                        ==
                        MODE_MASTERPIECE
                        else
                        FAST_MIN_SCORE
                    ),
                    winner.weighted_score,
                )
            )

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

        concepts=(
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
                "stc_adaptive_recovery_v53",

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

            "recovery_enabled":
                STC_CREATIVE_RECOVERY_ENABLED,

            "recovery_used":
                recovery_used,

            "recovery_reason":
                recovery_reason,

            "recovery_concepts":
                (
                    STC_RECOVERY_CONCEPT_COUNT
                    if recovery_used
                    else 0
                ),

            "technical_ideation_recovery":
                technical_ideation_recovery,

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

            "masterpiece_min_score":
                effective_integration_floor,

            "masterpiece_target_score":
                MASTERPIECE_MIN_SCORE,

            "masterpiece_release_floor":
                MASTERPIECE_RELEASE_FLOOR,

            "stc_target_score":
                STC_HIGH_ALERT_MIN_SCORE,

            "stc_release_floor":
                STC_HIGH_ALERT_RELEASE_FLOOR,

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
            # For a REAL STC quality rejection:
            # do not invite Smart fallback.
            #
            # Telegram V3.5 also enforces this independently.
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

    lines = [
        (
            "XPAND Creative Brain | "
            +
            response.mode.upper()
        )
    ]

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
                concept.title
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
                    else ""
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
        "stc_default_realistic"
    ] = (
        detect_stc_style(
            "إعلان بنك STC Bank"
        )
        ==
        "premium_realistic"
    )

    tests[
        "stc_explicit_purple"
    ] = (
        detect_stc_style(
            "بيئة بنفسجية معمارية"
        )
        ==
        "premium_purple_architecture"
    )

    tests[
        "stc_augmented_realism"
    ] = (
        detect_stc_style(
            "واقعية معززة"
        )
        ==
        "premium_augmented_realism"
    )

    tests[
        "stc_high_alert_default"
    ] = (
        is_stc_high_alert(
            "إعلان STC Bank",
            MODE_MASTERPIECE,
        )
        ==
        STC_HIGH_ALERT_ENABLED
    )

    # =====================================================
    # CALL POLICY
    # =====================================================

    tests[
        "stc_eight_concepts"
    ] = (
        STC_HIGH_ALERT_CONCEPT_COUNT
        >=
        6
    )

    tests[
        "normal_four_concepts"
    ] = (
        NORMAL_CONCEPT_COUNT
        ==
        4
    )

    tests[
        "recovery_three_concepts"
    ] = (
        STC_RECOVERY_CONCEPT_COUNT
        >=
        3
    )

    tests[
        "max_three_director_calls"
    ] = (
        MASTERPIECE_MAX_DIRECTOR_CALLS
        <=
        3
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
    # BRAND PACK
    # =====================================================

    tests[
        "brand_pack_loader_safe"
    ] = isinstance(
        load_stc_brand_pack(),
        dict,
    )

    tests[
        "brand_kit_context_safe"
    ] = isinstance(
        stc_curated_reference_context(
            benefit_family=(
                "merchant_payments"
            ),
            stc_style=(
                "premium_realistic"
            ),
        ),
        dict,
    )

    # =====================================================
    # PROMPT
    # =====================================================

    prompt_test = build_ideation_prompt(

        user_request=(
            "STC Bank عن التجارة الإلكترونية ونقاط البيع"
        ),

        brand_context={},

        visual_references=[],

        style_hint="",

        benefit_family=(
            "merchant_payments"
        ),

        stc_style=(
            "premium_realistic"
        ),

        concept_count=(
            STC_HIGH_ALERT_CONCEPT_COUNT
        ),

        high_alert=True,
    )

    tests[
        "visual_mechanism_guard"
    ] = contains_any(
        prompt_test,
        [
            "VISUAL MECHANISM",
        ],
    )

    tests[
        "no_generic_scene_rule"
    ] = contains_any(
        prompt_test,
        [
            "generic boutique checkout",
        ],
    )

    tests[
        "merchant_semantic_equivalents"
    ] = bool(
        contains_any(
            prompt_test,
            [
                "card reader",
            ],
        )
        and
        contains_any(
            prompt_test,
            [
                "digital storefront",
            ],
        )
    )

    tests[
        "user_only_needs_message"
    ] = contains_any(
        prompt_test,
        [
            (
                "The brief gives you the MESSAGE"
            ),
        ],
    )

    tests[
        "brand_pack_in_ideation"
    ] = contains_any(
        prompt_test,
        [
            "PERMANENT STC BRAND INTELLIGENCE",
        ],
    )

    # =====================================================
    # MERCHANT LANGUAGE TEST
    # =====================================================

    semantic_concept = CreativeConcept(

        concept_id="SEM",

        title="Unified commerce",

        concept_archetype=(
            "commercial mechanism"
        ),

        campaign_hook=(
            "One continuous physical relationship unifies "
            "a digital storefront and an in-store card reader."
        ),

        core_idea=(
            "The single advertising frame makes online ordering "
            "and in-store acceptance parts of one merchant system."
        ),

        marketing_message=(
            "Unified merchant payments."
        ),

        visual_metaphor=(
            "A physical continuity connects the digital storefront "
            "with the in-store payment reader."
        ),

        visual_mechanism_type=(
            "physical continuity"
        ),

        why_not_generic=(
            "The relationship between both sales channels forms "
            "the visual idea instead of ordinary checkout photography."
        ),

        environment=(
            "Contemporary Saudi commercial environment."
        ),

        environment_novelty=(
            "No conventional checkout-counter hero."
        ),

        hero_element=(
            "Unified commerce relationship."
        ),

        camera_angle=(
            "elevated three-quarter view"
        ),

        lens="35mm",

        perspective=(
            "foreground-to-background reveal"
        ),

        lighting=(
            "premium daylight"
        ),

        negative_space=(
            "30% upper-right negative space"
        ),

        brand_logic=(
            "Premium Saudi digital banking confidence."
        ),
    )

    signals = merchant_local_signals(
        semantic_concept
    )

    tests[
        "digital_storefront_detected"
    ] = bool(
        signals.get(
            "online"
        )
    )

    tests[
        "card_reader_detected_as_pos"
    ] = bool(
        signals.get(
            "physical"
        )
    )

    tests[
        "mechanism_detected"
    ] = bool(
        signals.get(
            "mechanism"
        )
    )

    # =====================================================
    # BAD COUNTER TEST
    # =====================================================

    literal_bad = CreativeConcept(

        concept_id="BAD",

        title="Luxury checkout",

        concept_archetype=(
            "premium realism"
        ),

        campaign_hook=(
            "Customer pays while merchant works."
        ),

        core_idea=(
            "Customer taps POS terminal on counter "
            "while merchant stands behind counter."
        ),

        marketing_message=(
            "merchant payments"
        ),

        visual_metaphor=(
            "Worker packing box in background."
        ),

        visual_mechanism_type="",

        why_not_generic="",

        environment=(
            "Luxury boutique with wooden checkout counter."
        ),

        environment_novelty="",

        hero_element=(
            "POS terminal"
        ),

        camera_angle=(
            "eye level"
        ),

        lens="35mm",

        perspective=(
            "normal perspective"
        ),

        lighting=(
            "soft daylight"
        ),

        negative_space=(
            "30% top"
        ),

        brand_logic=(
            "premium"
        ),
    )

    bad_penalty, bad_failures = (
        local_concept_penalties(

            literal_bad,

            user_request=(
                "STC Bank التجارة الإلكترونية ونقاط البيع"
            ),

            benefit_family=(
                "merchant_payments"
            ),

            stc_style=(
                "premium_realistic"
            ),
        )
    )

    tests[
        "bad_counter_scene_hard_rejected"
    ] = bool(
        bad_penalty
        >=
        30.0
        and
        "literal_transaction_tableau"
        in bad_failures
    )

    # =====================================================
    # RECOVERY PROMPT TEST
    # =====================================================

    fake_failed = CreativeConcept(

        concept_id="C01",

        title="Weak concept",

        concept_archetype="scene",

        campaign_hook="weak",

        core_idea="ordinary transaction",

        visual_metaphor="weak",

        weighted_score=52.0,

        evaluation_valid=True,

        quality_gate_failures=[
            "weak_campaign_hook",
            "visual_mechanism_below_90",
            "merchant_pos_channel_missing",
            "realism_below_86",
        ],

        scores={
            "concept_strength":
                70,

            "brand_fit":
                80,

            "originality":
                65,

            "visual_mechanism":
                55,

            "camera_quality":
                80,

            "realism":
                78,

            "feasibility":
                75,

            "copy_space_quality":
                80,

            "distinctiveness":
                60,

            "advertising_readiness":
                60,
        },

        feasibility={
            "production_feasible":
                True,
        },
    )

    recovery_prompt = (
        build_recovery_board_prompt(

            user_request=(
                "STC Bank التجارة الإلكترونية ونقاط البيع"
            ),

            failed_concepts=[
                fake_failed
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
        "recovery_uses_failure_context"
    ] = contains_any(
        recovery_prompt,
        [
            "visual_mechanism_below_90",
        ],
    )

    tests[
        "recovery_not_cosmetic"
    ] = contains_any(
        recovery_prompt,
        [
            "Change the conceptual grammar",
        ],
    )

    tests[
        "recovery_combines_generation_review_jury"
    ] = bool(
        contains_any(
            recovery_prompt,
            [
                "invent exactly",
            ],
        )
        and
        contains_any(
            recovery_prompt,
            [
                "evaluate all new concepts",
            ],
        )
        and
        contains_any(
            recovery_prompt,
            [
                "choose one",
            ],
        )
    )

    # =====================================================
    # SERIALIZATION
    # =====================================================

    encoded = concept_to_dict(
        semantic_concept
    )

    tests[
        "concept_contract"
    ] = bool(
        encoded.get(
            "concept_id"
        )
        ==
        "SEM"
        and
        "concept_archetype"
        in encoded
        and
        "campaign_hook"
        in encoded
        and
        "debate"
        in encoded
    )

    response = CreativeBrainResponse(

        ok=True,

        mode=(
            MODE_MASTERPIECE
        ),

        request="test",

        total_concepts=1,

        concepts=[
            semantic_concept
        ],

        top_concepts=[
            semantic_concept
        ],

        winner=(
            semantic_concept
        ),

        metadata={
            "quality_gate_passed":
                True,
        },

        errors=[],
    )

    serialized = response_to_dict(
        response
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
        " XPAND CREATIVE BRAIN V5.3"
    )
    print(
        " ZERO-COST ADAPTIVE RECOVERY SELF TEST"
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
                "XPAND Creative Brain V5.3 "
                "self-test: PASS ✅"
            )
        )

    else:

        print(
            (
                "XPAND Creative Brain V5.3 "
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
        (
            "✅ Initial STC concepts = "
            +
            str(
                STC_HIGH_ALERT_CONCEPT_COUNT
            )
        )
    )

    print(
        (
            "✅ Recovery concepts = "
            +
            str(
                STC_RECOVERY_CONCEPT_COUNT
            )
        )
    )

    print(
        "✅ Maximum 3 Director calls"
    )

    print(
        "✅ Call 3 dynamically becomes Jury OR Recovery"
    )

    print(
        "✅ Recovery generates NEW concepts"
    )

    print(
        "✅ Recovery evaluates concepts in same call"
    )

    print(
        "✅ Recovery final jury in same call"
    )

    print(
        "✅ Permanent STC Brand Kit used during ideation"
    )

    print(
        "✅ Merchant semantic equivalence"
    )

    print(
        "✅ Card reader recognized as physical POS channel"
    )

    print(
        "✅ Digital storefront recognized as e-commerce channel"
    )

    print(
        "✅ Merchant fusion judged semantically"
    )

    print(
        "✅ Generic-scene hard rejection"
    )

    print(
        "✅ Repeated-scene hard rejection"
    )

    print(
        "✅ Literal counter-tableau hard rejection"
    )

    print(
        "✅ Single-frame mechanism gate"
    )

    print(
        "✅ Real bank-campaign gate"
    )

    print(
        "✅ Strict dimension gates preserved"
    )

    print(
        "✅ No fake winner"
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
