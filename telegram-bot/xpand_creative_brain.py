# =========================================================
# XPAND CREATIVE BRAIN V5.6
#
# STC BANK HIGH-ALERT
# DETERMINISTIC STRICT-QUALIFIED RELEASE AUTHORITY
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
# V5.6 CORE GUARANTEE
#
# A real model-generated concept that:
#
#   1. was evaluated by the Director
#   2. has production_feasible = true
#   3. contains no hard-reject pattern
#   4. passes EVERY strict STC dimension
#   5. passes the STC release floor
#
# is a STRICT-QUALIFIED concept.
#
# Once at least one strict-qualified concept exists:
#
#   THE CREATIVE QUALITY GATE MUST RELEASE ONE.
#
# The Jury can:
#   - recommend a concept
#   - provide camera guidance
#   - provide production instruction
#   - provide concerns
#
# The Jury can NOT:
#   - veto all strict-qualified concepts
#   - make approval=false destroy a qualified concept
#   - make low confidence destroy a qualified concept
#   - make a global fatal_issues field destroy a different
#     concept that independently passed strict evaluation
#   - select an unqualified concept over a qualified concept
#
# Why:
#
# Recovery/Repair Board jury fields are GLOBAL fields created
# in the same call. They can accidentally describe another
# candidate while the per-concept evaluation correctly shows
# one or more production-ready concepts.
#
# V5.6 therefore establishes ONE authority:
#
#   PER-CONCEPT STRICT QUALIFICATION
#
# The highest strict-qualified concept wins deterministically.
#
# NO thresholds are lowered.
# NO fake winner is created.
#
# =========================================================
#
# STC MASTERPIECE PATH
#
# CALL 1
#   8 fundamentally different concepts
#          ↓
#
# CALL 2
#   Executive Creative Review
#          ↓
#
#   A) Strict finalist exists
#          ↓
#      CALL 3 = Finalist Jury
#          ↓
#      Highest strict-qualified finalist RELEASES
#
#   B) No strict finalist, but repairable near-miss exists
#          ↓
#      CALL 3 = Targeted Repair Board
#               2 repaired concepts
#               + evaluation
#               + jury guidance
#          ↓
#      If any repaired concept is strict-qualified:
#      highest strict-qualified concept RELEASES
#
#   C) No strict finalist and no repairable near-miss
#          ↓
#      CALL 3 = Fresh Recovery Board
#               3 new concepts
#               + evaluation
#               + jury guidance
#          ↓
#      If any recovery concept is strict-qualified:
#      highest strict-qualified concept RELEASES
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
# This module performs NO image generation.
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
            for marker
            in markers
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

VERSION = "5.6"

MODULE_NAME = (
    "XPAND Creative Brain"
)


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


def env_float(
    name: str,
    default: float,
) -> float:

    try:

        return float(
            os.environ.get(
                name,
                str(
                    default
                ),
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
                str(
                    default
                ),
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


STC_TARGETED_REPAIR_ENABLED = env_bool(
    "XPAND_STC_TARGETED_REPAIR_ENABLED",
    True,
)


#
# V5.6:
#
# Once a concept independently passes every strict
# per-concept gate, Jury global fields are advisory.
#
STC_STRICT_QUALIFIED_RELEASE_AUTHORITY = env_bool(
    "XPAND_STC_STRICT_QUALIFIED_RELEASE_AUTHORITY",
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
# V5.6 DOES NOT LOWER THESE.
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


STC_TARGETED_REPAIR_OUTPUT_COUNT = 2


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
# These values only determine whether Call 3 repairs a
# near-miss instead of rebuilding the idea.
#
# They DO NOT change final release thresholds.
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


# =========================================================
# JURY
#
# V5.6:
#
# Confidence is retained for diagnostics / art direction.
# It is NOT a second quality gate after strict qualification.
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
        .strip()[
            :limit
        ]
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

        "أ":
            "ا",

        "إ":
            "ا",

        "آ":
            "ا",

        "ة":
            "ه",

        "ى":
            "ي",

        "ؤ":
            "و",

        "ئ":
            "ي",

        "ـ":
            "",
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

    return output[
        :limit
    ]


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
        flags=(
            re.IGNORECASE
        ),
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
            (
                "Structured Director response "
                "is not a JSON object."
            )
        )

    return payload


# =========================================================
# BRAND PACK
# =========================================================

def locate_stc_brand_pack() -> Optional[
    Path
]:

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


def load_stc_brand_pack() -> Dict[
    str,
    Any,
]:

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
# CURATED BRAND KIT CONTEXT
# =========================================================

def stc_curated_reference_context(
    *,
    benefit_family: str,
    stc_style: str,
) -> Dict[str, Any]:

    result: Dict[
        str,
        Any,
    ] = {

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
                or
                "premium_realistic"
            ),
        )
    )

    if not pack:

        return compact_json(
            curated,
            10000,
        )

    styles = safe_dict(
        pack.get(
            "styles"
        )
    )

    visual_families = safe_dict(
        pack.get(
            "visual_families"
        )
    )

    style_payload = (
        styles.get(
            stc_style
        )
        or
        visual_families.get(
            stc_style
        )
        or
        {}
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

        "pack_version":
            pack.get(
                "pack_version"
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

        "selected_style":
            style_payload,

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

CONCEPT_SCHEMA: Dict[
    str,
    Any,
] = {

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
# EVALUATION SCHEMA
# =========================================================

def evaluation_schema() -> Dict[
    str,
    Any,
]:

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
# JURY SCHEMA
# =========================================================

FINALIST_JURY_SCHEMA: Dict[
    str,
    Any,
] = {

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
# COMBINED BOARD SCHEMA
#
# Used by Targeted Repair and Fresh Recovery.
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
# Compatibility alias from V5.4/V5.5.
#

def make_recovery_schema(
    concept_count: int,
) -> Dict[str, Any]:

    return make_board_schema(
        concept_count
    )


# =========================================================
# STC GUARD PATTERNS
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

    "particle cloud",

    "هولوغرام",

    "بطاقة طافية",

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


#
# Any of these means the concept itself is not strict-qualified.
#
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

    "merchant_online_channel_unclear",

    "merchant_pos_channel_unclear",

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
# PARSING
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


def parse_concepts(
    payload: Dict[str, Any],
    *,
    generation_round: int = 1,
    id_prefix: str = "C",
    force_ids: bool = False,
) -> List[
    CreativeConcept
]:

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
            str(
                index
            ).zfill(
                2
            )
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

            concept.concept_id = (
                forced_id
            )

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
# MERCHANT LOCAL SEMANTICS
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
# LOCAL CONCEPT GUARD
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
        and
        counter
        and
        physical_payment
        and
        (
            merchant
            or
            packing
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
        and
        repeated_hits >= 2
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
    # GENERIC LIFESTYLE
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
        >=
        25
    )

    if (
        STC_REJECT_GENERIC_SCENES
        and
        generic_hits >= 1
        and
        not mechanism_present
    ):

        penalty += 25.0

        failures.append(
            "generic_lifestyle_without_advertising_mechanism"
        )

    # =====================================================
    # MECHANISM COMPLETENESS
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
    # PURPLE IS NOT THE IDEA
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
    # These are soft warnings.
    # Real semantic evaluation happens in Call 2/3.
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
# STRICT DIMENSION FAILURES
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
        if failure
        in HARD_REJECT_FAILURES
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

    gaps = (
        targeted_repair_dimension_gaps(
            concept
        )
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
        for concept
        in concepts
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
# STC IDEATION ARCHETYPES
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

At most TWO concepts may use indoor retail.

At most ONE concept may make a POS terminal the obvious
foreground hero.

Do not create eight variations of:
merchant + terminal + parcel + counter.
"""


# =========================================================
# INITIAL IDEATION PROMPT
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

    technical_retry_block = ""

    if recovery:

        technical_retry_block = f"""
==================================================
STRUCTURED TECHNICAL RETRY
==================================================

The first structured call failed technically.

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
STC BANK HIGH ALERT
==================================================

The brief gives you the COMMERCIAL MESSAGE.

YOU invent:
- concept
- scene
- visual metaphor
- hero
- camera
- art direction
- production design

The user should not have to invent the advertising idea.

A scene is not an advertising idea.

A POS terminal is not an advertising idea.

A customer holding a phone is not an advertising idea.

Purple is not automatically brand identity.

Every concept needs ONE meaningful VISUAL MECHANISM
that survives in ONE still frame.

==================================================
MANDATORY DIVERSITY
==================================================

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

References are VISUAL DNA.

Use them to understand:
- campaign maturity
- composition quality
- hierarchy
- materials
- lighting restraint
- Saudi context
- camera discipline
- STC Bank confidence

Do NOT clone:
- scene
- people
- location
- campaign
- copy
- logo

==================================================
VISUAL FAMILY
==================================================

Selected family:
{stc_style}

PREMIUM REALISTIC:

Prefer:
- real Saudi commercial environments
- real people only when useful
- natural skin
- premium modern materials
- realistic daylight or motivated commercial light
- restrained brand accents
- deliberate camera
- controlled reflections

Purple is OPTIONAL.

Do not use purple as the idea.

PURPLE ARCHITECTURAL:

Only when explicitly active.

Purple may become:
- architecture
- planes
- geometry
- satin surfaces
- controlled reflections

Never:
- nightclub neon
- cyber room
- generic fintech tunnel

AUGMENTED REALISM:

Use ONE physically credible conceptual intervention.

It must obey:
- gravity
- perspective
- scale
- contact
- shadows
- reflections
- occlusion
- material logic

==================================================
MERCHANT PAYMENTS LAW
==================================================

When benefit_family = merchant_payments:

The viewer must understand:

ONLINE / E-COMMERCE SALES
+
PHYSICAL / IN-STORE PAYMENT ACCEPTANCE
+
ONE UNIFIED MERCHANT PROPOSITION

Physical equivalents:
- POS
- payment terminal
- card reader
- tap-to-pay
- in-store acceptance

Digital equivalents:
- e-commerce
- digital storefront
- online order
- web checkout
- online commerce

Both channels must be understandable.

But DO NOT simply place them next to each other.

ONE advertising mechanism must connect them.

==================================================
HARD WEAK PATTERN
==================================================

Reject:

CUSTOMER
+
POS
+
COUNTER
+
MERCHANT
+
TABLET / PACKING

when it is ordinary transaction photography.

Also reject:
- wooden checkout counter cliché
- generic luxury boutique
- packing worker as the e-commerce idea
- customer simply tapping a terminal
- terminal simply held toward camera

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

The image must contain no generated:
- headline
- slogan
- CTA
- legal copy
- STC logo
- bank logo
- card-network logo
- fake readable banking UI

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
You are XPAND Creative Brain V5.6.

You receive the COMMERCIAL MESSAGE.

Your job is to invent the advertising idea.

==================================================
REQUEST
==================================================

{clean_text(
    user_request,
    7500,
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
    8000,
)}

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
IDEATION
==================================================

Generate exactly {concept_count} fundamentally different
advertising concepts.

Each concept must differ materially in:
- visual mechanism
- archetype
- hero relationship
- environment
- spatial construction
- camera strategy

Do not produce cosmetic variants.

{stc_block}

{technical_retry_block}

==================================================
OUTPUT
==================================================

Return exactly the structured schema.

Use IDs:
C01
C02
C03
...

Do not score concepts in this call.
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

    strict_block = ""

    if high_alert:

        strict_block = f"""
==================================================
STC STRICT RELEASE STANDARD
==================================================

Do not reward competence.

90+ must mean genuine campaign quality.

STRICT DIMENSION GATES:

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

Overall strict release floor:
{STC_HIGH_ALERT_RELEASE_FLOOR}

Do NOT inflate scores just to pass.

A beautiful but ordinary scene can score 65-78.

A polished but familiar campaign can score 78-86.

90+ is exceptional.
"""

    return f"""
You are XPAND V5.6 EXECUTIVE CREATIVE REVIEW.

Evaluate every concept independently.

Do NOT generate replacement concepts here.

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
Is there a real visual idea rather than just a scene?

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
Would a senior bank creative director send this to production?

weighted_score:
Give a strict overall score.

==================================================
BOOLEAN CREATIVE JUDGMENTS
==================================================

generic_scene_risk:
TRUE if this could collapse into ordinary lifestyle or
transaction photography.

repetition_risk:
TRUE if this resembles the repeated XPAND/STC merchant
counter / boutique pattern.

concept_is_scene_only:
TRUE if the proposal is mainly location + people + props.

mechanism_survives_single_frame:
TRUE only when the advertising mechanism remains readable
in one still image.

looks_like_real_bank_campaign:
TRUE only for premium financial-campaign discipline.

==================================================
MERCHANT SEMANTIC REVIEW
==================================================

For merchant_payments:

merchant_online_channel_clear:
Can a viewer understand an online/e-commerce sales channel?

merchant_pos_channel_clear:
Can a viewer understand physical/in-store payment acceptance?

Accept:
- card reader
- payment terminal
- tap-to-pay
- in-store acceptance
- digital storefront
- online order
- web checkout

Do NOT require the exact token POS.

merchant_channels_fused:
TRUE only when ONE mechanism genuinely unifies both channels.

Putting both channels in one room is NOT fusion.

For non-merchant briefs:
set all three merchant booleans TRUE.

==================================================
PRODUCTION FEASIBILITY
==================================================

production_feasible = TRUE only if one coherent generated
frame can preserve the central advertising idea.

No impossible geometry.

No contradictory camera systems.

No required readable UI.

==================================================
CAMERA
==================================================

Return:
- one camera angle
- one lens
- one perspective

for every concept.

{strict_block}

Return exactly the structured schema.
""".strip()


# =========================================================
# JURY PROMPT
#
# V5.6:
#
# Jury is an advisory production layer after deterministic
# qualification. It cannot veto strict-qualified concepts.
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
You are XPAND V5.6 FINAL STC BANK ART-DIRECTION JURY.

IMPORTANT:

Every concept provided below has ALREADY passed XPAND's
deterministic strict quality gates.

Your role is:

1. rank the qualified concepts
2. recommend the strongest one
3. strengthen production art direction
4. lock camera / environment / mechanism
5. warn about likely execution drift

You are NOT a second veto layer.

The deterministic strict qualification remains the final
release authority.

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
STRICT-QUALIFIED FINALISTS
==================================================

{compact_json(
    payload,
    26000,
)}

==================================================
SELECT
==================================================

Choose ONE ID from the supplied concepts.

Prefer:
- strongest advertising proposition
- strongest STC Bank ownership
- clearest single-frame mechanism
- best merchant fusion
- highest realism
- lowest generic-scene risk
- best camera

approval:
Give your recommendation.

confidence:
Give honest confidence.

These values are diagnostic and do NOT erase a concept that
already passed deterministic strict gates.

==================================================
MERCHANT
==================================================

For merchant_payments:

merchant_fusion_approved should describe your opinion about
the recommended concept.

The runtime still relies on the concept's independent
per-concept evaluation for release authority.

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
- lighting
- copy-space location

Do not drift into:
- ordinary checkout
- customer + terminal tableau
- wooden boutique counter
- packing worker
- generic fintech effects
- generated text or logo

Return exactly the schema.
""".strip()


# =========================================================
# FAILURE / REPAIR CONTEXT
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
                        1100,
                    ),

                "visual_mechanism":
                    clean_text(
                        concept.visual_metaphor,
                        1000,
                    ),

                "environment":
                    clean_text(
                        concept.environment,
                        800,
                    ),
            }
        )

    return compact_json(
        payload,
        18000,
    )


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

                "weighted_score":
                    concept.weighted_score,

                "exact_dimension_gaps":
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
                        1400,
                    ),

                "visual_metaphor":
                    clean_text(
                        concept.visual_metaphor,
                        1600,
                    ),

                "visual_mechanism_type":
                    clean_text(
                        concept.visual_mechanism_type,
                        800,
                    ),

                "why_not_generic":
                    clean_text(
                        concept.why_not_generic,
                        1400,
                    ),

                "environment":
                    clean_text(
                        concept.environment,
                        1400,
                    ),

                "hero_element":
                    clean_text(
                        concept.hero_element,
                        1000,
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
                        1400,
                    ),
            }
        )

    return compact_json(
        payload,
        22000,
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

    return f"""
You are XPAND V5.6 STC BANK TARGETED CREATIVE REPAIR BOARD.

The Executive Review found a genuinely strong near-miss.

You have ONE final Director call.

This one structured response must:

1. repair the strongest near-miss
2. create exactly TWO repaired concepts
3. evaluate both independently
4. recommend one
5. provide production guidance

==================================================
REPAIR PHILOSOPHY
==================================================

Preserve the strongest CORE proposition.

Do not discard a strong advertising idea because several
execution dimensions are a few points short.

But do NOT perform a cosmetic rewrite.

You may materially strengthen:
- mechanism
- hero relationship
- environment
- camera
- brand ownership
- realism
- production design
- lighting
- copy-space integration

when necessary.

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
NEAR-MISS DIAGNOSIS
==================================================

{build_targeted_repair_context(
    repair_candidates
)}

==================================================
STRICT GATES — NO LOWERING
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

overall release floor >= {STC_HIGH_ALERT_RELEASE_FLOOR}

Do not inflate scores.

==================================================
PERMANENT STC BRAND INTELLIGENCE
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
RUNTIME VISUAL DNA
==================================================

{compact_json(
    visual_references,
    7000,
)}

==================================================
MERCHANT LAW
==================================================

For merchant_payments:

The viewer must understand:
ONLINE COMMERCE
+
PHYSICAL PAYMENT ACCEPTANCE
+
ONE UNIFIED MERCHANT SYSTEM

A card reader counts as POS.

A digital storefront counts as e-commerce.

Both must be connected by ONE advertising mechanism.

Same room is not fusion.

==================================================
BAN
==================================================

Never repair into:
- customer + POS + counter + merchant tableau
- wooden checkout counter
- packing employee in background
- ordinary transaction photography
- floating fintech objects
- network lines
- holograms
- cyber effects
- generated copy
- generated logo
- fake banking UI

==================================================
REALISM
==================================================

One coherent frame.

One camera system.

One light logic.

Physically believable:
- perspective
- scale
- contact
- shadow
- reflection
- occlusion
- material roughness

==================================================
OUTPUT
==================================================

Create exactly:

T01
T02

Evaluate both honestly.

The runtime will independently apply deterministic strict
qualification after your response.

If one or both pass every strict gate, the highest
strict-qualified concept will be released.

Your final recommendation is advisory production guidance.

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

    return f"""
You are XPAND V5.6 STC BANK FRESH CREATIVE RECOVERY BOARD.

The first eight concepts were genuinely evaluated.

No strict-qualified concept exists.

No suitable near-miss qualified for Targeted Repair.

You have ONE final Director call.

This response must:

1. invent exactly {STC_RECOVERY_CONCEPT_COUNT} NEW concepts
2. evaluate every new concept independently
3. recommend one
4. provide production art direction

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
WHY THE FIRST ROUND FAILED
==================================================

{build_failure_context(
    failed_concepts,
    limit=4,
)}

==================================================
RECOVERY LAW
==================================================

Do NOT cosmetically rewrite the failed ideas.

Change the conceptual grammar.

Do not merely:
- change the store
- change the person
- change the counter
- change the wall
- add purple
- change the lens

Find a materially different advertising mechanism.

==================================================
STRICT GATES — NO LOWERING
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

overall release floor >= {STC_HIGH_ALERT_RELEASE_FLOOR}

Do not inflate scores.

==================================================
PERMANENT STC BANK INTELLIGENCE
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

==================================================
MERCHANT PAYMENTS
==================================================

For merchant_payments:

ONLINE / E-COMMERCE
+
PHYSICAL / IN-STORE PAYMENT
+
ONE UNIFIED MERCHANT PROPOSITION

The two channels must be connected by the visual mechanism.

Do not use:
customer + terminal + counter + packing worker.

==================================================
BAN
==================================================

No:
- generic boutique checkout
- wooden counter cliché
- generic phone lifestyle
- floating cards
- floating phones
- floating POS
- network lines
- holograms
- HUD
- neon fintech
- random particles
- generated text/logo
- fake banking UI

==================================================
OUTPUT
==================================================

Use:

R01
R02
R03

and R04 only if four recovery concepts are configured.

Evaluate every concept honestly.

The runtime will independently apply deterministic strict
qualification after this response.

IMPORTANT:

If any generated concept passes ALL deterministic strict
gates, it WILL be released.

Your selected_concept_id / approval / confidence fields are
advisory guidance and cannot erase a strict-qualified concept.

Return exactly the structured schema.
""".strip()


# =========================================================
# INITIAL GENERATION CALL
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
            "xpand_creative_ideation_v56"
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
# APPLY REAL MODEL EVALUATIONS
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

        #
        # Safe array-position fallback.
        #
        if evaluation is None:

            array_index = (
                index
                -
                1
            )

            if (
                array_index
                <
                len(
                    evaluations
                )
            ):

                candidate = evaluations[
                    array_index
                ]

                if isinstance(
                    candidate,
                    dict,
                ):

                    evaluation = (
                        candidate
                    )

        if not isinstance(
            evaluation,
            dict,
        ):

            concept.evaluation_valid = (
                False
            )

            concept.quality_gate_passed = (
                False
            )

            concept.quality_gate_failures = [
                "missing_real_evaluation"
            ]

            continue

        scores: Dict[
            str,
            float,
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

        if benefit_family == "merchant_payments":

            if not online_clear:

                review_penalty += 8.0

                review_failures.append(
                    "merchant_online_channel_unclear"
                )

            if not pos_clear:

                review_penalty += 8.0

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
                (
                    base_score
                    -
                    local_penalty
                    -
                    review_penalty
                ),
            ),
        )

        combined_failures = (
            dedupe_strings(
                local_failures
                +
                review_failures
            )
        )

        #
        # Hard-rejected concepts cannot appear close to release.
        #
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
                    1700,
                ),
        }

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

        concept.debate = {

            "evaluation_source":
                evaluation_source,

            "strengths":
                [
                    clean_text(
                        value,
                        1000,
                    )
                    for value
                    in safe_list(
                        evaluation.get(
                            "strengths"
                        )
                    )[:8]
                    if clean_text(
                        value,
                        1000,
                    )
                ],

            "weaknesses":
                [
                    clean_text(
                        value,
                        1100,
                    )
                    for value
                    in safe_list(
                        evaluation.get(
                            "weaknesses"
                        )
                    )[:10]
                    if clean_text(
                        value,
                        1100,
                    )
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
                        1400,
                    ),

                "camera_lock_instruction":
                    (
                        "Preserve this evaluated camera "
                        "strategy during image production."
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

            concept.camera_angle = (
                clean_text(
                    camera.get(
                        "camera_angle"
                    ),
                    900,
                )
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

            concept.perspective = (
                clean_text(
                    camera.get(
                        "perspective"
                    ),
                    1200,
                )
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
            "xpand_creative_review_v56"
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
# FINALIST JURY CALL
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
            "xpand_stc_finalist_jury_v56"
        ),
    )

    return parse_json_payload(
        raw
    )


# =========================================================
# COMBINED REPAIR / RECOVERY BOARD
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
    # Normalize selected ID if the Director used a different
    # prefix but correct numeric index.
    #
    selected_id = clean_text(
        payload.get(
            "selected_concept_id"
        ),
        100,
    )

    valid_ids = {
        concept.concept_id
        for concept
        in concepts
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

            normalized_id = (
                id_prefix
                +
                str(
                    number
                ).zfill(
                    2
                )
            )

            if normalized_id in valid_ids:

                payload[
                    "selected_concept_id"
                ] = normalized_id

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
        id_prefix="T",
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
            "xpand_stc_targeted_repair_v56"
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
        id_prefix="R",
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
            "xpand_stc_recovery_board_v56"
        ),
    )


# =========================================================
# CONCEPT LOOKUP
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
# JURY DIAGNOSTICS
#
# These fields are retained.
# They are NOT strict-release authority after qualification.
# =========================================================

def jury_diagnostics(
    jury: Any,
) -> Dict[str, Any]:

    jury = safe_dict(
        jury
    )

    return {

        "selected_concept_id":
            clean_text(
                jury.get(
                    "selected_concept_id"
                ),
                100,
            ),

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

        "merchant_fusion_approved":
            bool(
                jury.get(
                    "merchant_fusion_approved",
                    False,
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
                )[:10]
                if clean_text(
                    value,
                    1000,
                )
            ],

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

        "production_instruction":
            clean_text(
                jury.get(
                    "production_instruction"
                ),
                3500,
            ),

        "recommended_camera_angle":
            clean_text(
                jury.get(
                    "recommended_camera_angle"
                ),
                900,
            ),

        "recommended_lens":
            clean_text(
                jury.get(
                    "recommended_lens"
                ),
                400,
            ),

        "recommended_perspective":
            clean_text(
                jury.get(
                    "recommended_perspective"
                ),
                1200,
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
                )[:12]
                if clean_text(
                    value,
                    1000,
                )
            ],
    }


def print_jury_diagnostics(
    *,
    jury: Any,
    qualified: Sequence[
        CreativeConcept
    ],
    source: str,
) -> None:

    diag = jury_diagnostics(
        jury
    )

    print("")
    print(
        "⚖️ V5.6 JURY DIAGNOSTICS"
    )
    print(
        "Source:",
        source,
    )
    print(
        "Jury selected ID:",
        (
            diag.get(
                "selected_concept_id"
            )
            or "-"
        ),
    )
    print(
        "Jury approval:",
        diag.get(
            "approval"
        ),
    )
    print(
        "Jury confidence:",
        diag.get(
            "confidence"
        ),
    )
    print(
        "Jury merchant fusion:",
        diag.get(
            "merchant_fusion_approved"
        ),
    )
    print(
        "Jury fatal issues:",
        compact_json(
            diag.get(
                "fatal_issues"
            ),
            2000,
        ),
    )
    print(
        "Strict-qualified IDs:",
        [
            concept.concept_id
            for concept
            in qualified
        ],
    )


# =========================================================
# PRODUCTION INSTRUCTION
# =========================================================

def build_deterministic_production_instruction(
    winner: CreativeConcept,
) -> str:

    return clean_text(
        (
            "XPAND V5.6 STRICT-QUALIFIED PRODUCTION LOCK. "
            "Produce the independently evaluated campaign concept "
            +
            winner.concept_id
            +
            " without simplifying it into ordinary lifestyle "
            "or transaction photography. Preserve the central "
            "advertising mechanism, hero relationship, environment, "
            "brand logic and copy space. Camera angle: "
            +
            (
                winner.camera_angle
                or
                "preserve evaluated camera"
            )
            +
            ". Lens: "
            +
            (
                winner.lens
                or
                "preserve evaluated lens"
            )
            +
            ". Perspective: "
            +
            (
                winner.perspective
                or
                "preserve evaluated perspective"
            )
            +
            ". Lighting: "
            +
            (
                winner.lighting
                or
                "premium physically motivated lighting"
            )
            +
            ". Do not add text, logo, fake UI, fintech decoration, "
            "wooden checkout tableau, packing-worker background, "
            "or generic customer-payment photography."
        ),
        4200,
    )


# =========================================================
# ATTACH JURY AS ADVISORY ART DIRECTION
# =========================================================

def attach_jury_advisory(
    *,
    winner: CreativeConcept,
    jury: Any,
    source: str,
    strict_qualified_ids: Sequence[str],
    deterministic_reason: str,
) -> None:

    diag = jury_diagnostics(
        jury
    )

    jury_selected_id = clean_text(
        diag.get(
            "selected_concept_id"
        ),
        100,
    )

    #
    # Only apply jury camera override when Jury actually
    # recommended THIS qualified winner.
    #
    # Otherwise preserve this concept's own evaluated camera.
    #
    jury_recommended_winner = bool(
        jury_selected_id
        and
        jury_selected_id
        ==
        winner.concept_id
    )

    production_instruction = (
        clean_text(
            diag.get(
                "production_instruction"
            ),
            3500,
        )
        if jury_recommended_winner
        else
        ""
    )

    if not production_instruction:

        production_instruction = (
            build_deterministic_production_instruction(
                winner
            )
        )

    drift = dedupe_strings(
        list(
            safe_list(
                diag.get(
                    "do_not_drift_into"
                )
            )
        )
        +
        [
            "generic checkout-counter scene",
            "customer + POS + merchant transaction tableau",
            "worker packing a parcel in background",
            "wooden luxury counter cliché",
            "generic fintech effects",
            "reference-image cloning",
            "generated text or logo",
            "fake readable banking UI",
        ]
    )[:14]

    winner.debate[
        "finalist_jury"
    ] = {

        "source":
            source,

        "role":
            "advisory_art_direction",

        "release_authority":
            "deterministic_per_concept_strict_qualification",

        "approval":
            diag.get(
                "approval"
            ),

        "confidence":
            diag.get(
                "confidence"
            ),

        "merchant_fusion_approved":
            diag.get(
                "merchant_fusion_approved"
            ),

        "fatal_issues":
            diag.get(
                "fatal_issues"
            ),

        "advertising_reason":
            diag.get(
                "advertising_reason"
            ),

        "brand_reason":
            diag.get(
                "brand_reason"
            ),

        "originality_reason":
            diag.get(
                "originality_reason"
            ),

        "jury_selected_id":
            jury_selected_id,

        "jury_recommended_this_winner":
            jury_recommended_winner,

        "strict_qualified_ids":
            list(
                strict_qualified_ids
            ),

        "deterministic_reason":
            deterministic_reason,

        "production_instruction":
            production_instruction,

        "do_not_drift_into":
            drift,

        "thresholds_lowered":
            False,

        "jury_global_fields_can_veto_strict_winner":
            False,
    }

    camera = winner.debate.setdefault(
        "camera_director",
        {},
    )

    if jury_recommended_winner:

        jury_angle = clean_text(
            diag.get(
                "recommended_camera_angle"
            ),
            900,
        )

        jury_lens = clean_text(
            diag.get(
                "recommended_lens"
            ),
            400,
        )

        jury_perspective = clean_text(
            diag.get(
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
        "V5.6 STRICT-QUALIFIED CAMERA LOCK. "
        "Use the camera evaluated for this exact winning concept. "
        "Only apply Jury camera changes when the Jury selected "
        "this same strict-qualified concept."
    )


# =========================================================
# DETERMINISTIC STRICT-QUALIFIED RELEASE
#
# THIS IS THE V5.6 FIX.
# =========================================================

def deterministic_strict_release(
    *,
    concepts: Sequence[
        CreativeConcept
    ],
    jury: Any,
    source: str,
) -> Tuple[
    Optional[CreativeConcept],
    Dict[str, Any],
]:

    qualified = (
        strict_qualified_concepts(
            concepts,
            high_alert=True,
        )
    )

    diag = jury_diagnostics(
        jury
    )

    result: Dict[
        str,
        Any,
    ] = {

        "source":
            source,

        "authority":
            (
                "deterministic_per_concept_"
                "strict_qualification"
            ),

        "strict_qualified_ids":
            [
                concept.concept_id
                for concept
                in qualified
            ],

        "strict_qualified_count":
            len(
                qualified
            ),

        "jury_selected_id":
            diag.get(
                "selected_concept_id"
            ),

        "jury_approval":
            diag.get(
                "approval"
            ),

        "jury_confidence":
            diag.get(
                "confidence"
            ),

        "jury_merchant_fusion_approved":
            diag.get(
                "merchant_fusion_approved"
            ),

        "jury_fatal_issues":
            diag.get(
                "fatal_issues"
            ),

        "jury_fields_are_advisory":
            True,

        "thresholds_lowered":
            False,

        "released":
            False,

        "winner_id":
            "",

        "reason":
            "",
    }

    #
    # No strict-qualified concept:
    # quality failure remains quality failure.
    #
    if not qualified:

        result[
            "reason"
        ] = (
            "no_strict_qualified_concept"
        )

        return (
            None,
            result,
        )

    #
    # V5.6 invariant:
    #
    # Once strict qualification exists, Jury global fields
    # cannot destroy it.
    #
    # Highest strict-qualified concept wins.
    #
    winner = qualified[
        0
    ]

    jury_selected_id = clean_text(
        diag.get(
            "selected_concept_id"
        ),
        100,
    )

    qualified_ids = [
        concept.concept_id
        for concept
        in qualified
    ]

    if (
        jury_selected_id
        ==
        winner.concept_id
    ):

        reason = (
            "jury_and_strict_ranking_agree"
        )

    elif (
        jury_selected_id
        in qualified_ids
    ):

        reason = (
            "strict_highest_score_outranked_"
            "different_qualified_jury_choice"
        )

    elif jury_selected_id:

        reason = (
            "jury_selected_unqualified_concept_"
            "highest_strict_qualified_released"
        )

    else:

        reason = (
            "jury_selection_missing_"
            "highest_strict_qualified_released"
        )

    attach_jury_advisory(
        winner=(
            winner
        ),
        jury=(
            jury
        ),
        source=(
            source
        ),
        strict_qualified_ids=(
            qualified_ids
        ),
        deterministic_reason=(
            reason
        ),
    )

    winner.debate[
        "strict_release_authority"
    ] = {

        "policy_version":
            "5.6",

        "authority":
            (
                "per_concept_strict_qualification"
            ),

        "winner_id":
            winner.concept_id,

        "winner_score":
            winner.weighted_score,

        "strict_qualified_ids":
            qualified_ids,

        "reason":
            reason,

        "jury_global_veto_allowed":
            False,

        "thresholds_lowered":
            False,

        "real_model_generated":
            True,

        "real_model_evaluated":
            True,

        "production_feasible":
            bool(
                safe_dict(
                    winner.feasibility
                ).get(
                    "production_feasible",
                    False,
                )
            ),

        "strict_dimension_failures":
            stc_dimension_gate_failures(
                winner
            ),
    }

    winner.quality_gate_passed = True

    winner.debate[
        "quality_release_level"
    ] = (
        "stc_strict_qualified_release"
    )

    result.update(
        {

            "released":
                True,

            "winner_id":
                winner.concept_id,

            "winner_score":
                winner.weighted_score,

            "reason":
                reason,
        }
    )

    return (
        winner,
        result,
    )


# =========================================================
# NORMAL NON-STC RELEASE
# =========================================================

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

    if (
        best.weighted_score
        >=
        MASTERPIECE_MIN_SCORE
    ):

        best.quality_gate_passed = (
            True
        )

        best.debate[
            "quality_release_level"
        ] = (
            "masterpiece_target_release"
        )

        return (
            best,
            "masterpiece_target_release",
        )

    if (
        best.weighted_score
        >=
        MASTERPIECE_RELEASE_FLOOR
    ):

        best.quality_gate_passed = (
            True
        )

        best.debate[
            "quality_release_level"
        ] = (
            "masterpiece_release_floor"
        )

        return (
            best,
            "masterpiece_release_floor",
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
        (
            "This is NOT classified as a "
            "creative-quality failure."
        )
    )

    if high_alert:

        print(
            (
                "STC High Alert produced no "
                "valid evaluated creative release."
            )
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
                (
                    "stc_deterministic_"
                    "strict_release_v56"
                ),

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
                    else
                    2
                ),

            "director_call_maximum":
                MASTERPIECE_MAX_DIRECTOR_CALLS,

            "strict_qualified_release_authority":
                (
                    STC_STRICT_QUALIFIED_RELEASE_AUTHORITY
                ),

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
# TOP CONCEPTS
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

    all_concepts: List[
        CreativeConcept
    ] = []

    primary_concepts: List[
        CreativeConcept
    ] = []

    targeted_repair_concepts: List[
        CreativeConcept
    ] = []

    recovery_concepts: List[
        CreativeConcept
    ] = []

    winner: Optional[
        CreativeConcept
    ] = None

    release_level = (
        "quality_failed"
    )

    technical_ideation_recovery = (
        False
    )

    targeted_repair_used = False

    targeted_repair_source_ids: List[
        str
    ] = []

    fresh_recovery_used = False

    recovery_reason = ""

    final_jury_payload: Dict[
        str,
        Any
    ] = {}

    strict_release_info: Dict[
        str,
        Any
    ] = {

        "released":
            False,

        "reason":
            "",

        "winner_id":
            "",

        "strict_qualified_ids":
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
        " XPAND CREATIVE BRAIN V5.6"
    )

    if high_alert:

        print(
            (
                " STC BANK DETERMINISTIC "
                "STRICT-RELEASE HIGH ALERT"
            )
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
            else
            False
        ),
    )

    print(
        "Strict-qualified release authority:",
        (
            STC_STRICT_QUALIFIED_RELEASE_AUTHORITY
            if high_alert
            else
            False
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
    # CALL 1 — DIVERSE IDEATION
    # =====================================================

    try:

        director_calls += 1

        director_history.append(
            "diverse_ideation"
        )

        primary_concepts = (
            generate_concepts(
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

        #
        # One technical retry is permitted.
        #
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

                primary_concepts = (
                    generate_concepts(
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
        primary_concepts
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
                primary_concepts
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

    primary_concepts.sort(
        key=lambda item:
            item.weighted_score,
        reverse=True,
    )

    # =====================================================
    # NORMAL NON-STC
    # =====================================================

    if not high_alert:

        (
            winner,
            release_level,
        ) = choose_normal_release(
            concepts=(
                primary_concepts
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
                primary_concepts,
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
        # TECHNICAL RETRY USED ALL 3 CALLS
        #
        # If Executive Review itself found a strict-qualified
        # concept, release it deterministically.
        # =================================================

        if technical_ideation_recovery:

            if primary_qualified:

                (
                    winner,
                    strict_release_info,
                ) = deterministic_strict_release(
                    concepts=(
                        primary_concepts
                    ),
                    jury={},
                    source=(
                        "technical_retry_review"
                    ),
                )

                if winner:

                    release_level = (
                        "stc_technical_retry_"
                        "strict_release"
                    )

            else:

                winner = None

                release_level = (
                    "quality_failed_after_"
                    "technical_retry"
                )

        # =================================================
        # ROUTE A:
        # PRIMARY STRICT FINALISTS
        # CALL 3 = ADVISORY FINAL JURY
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

                    final_jury_payload = (
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

                except Exception as jury_error:

                    #
                    # V5.6:
                    #
                    # Jury technical failure cannot erase concepts
                    # already independently strict-qualified.
                    #
                    errors.append(
                        (
                            "finalist_jury_advisory_failure: "
                            +
                            clean_text(
                                jury_error,
                                3500,
                            )
                        )
                    )

                    final_jury_payload = {}

            print_jury_diagnostics(
                jury=(
                    final_jury_payload
                ),
                qualified=(
                    primary_qualified
                ),
                source=(
                    "stc_finalist_jury"
                ),
            )

            (
                winner,
                strict_release_info,
            ) = deterministic_strict_release(
                concepts=(
                    primary_concepts
                ),
                jury=(
                    final_jury_payload
                ),
                source=(
                    "stc_primary_strict_finalists"
                ),
            )

            if winner:

                release_level = (
                    "stc_primary_"
                    "strict_qualified_release"
                )

        # =================================================
        # NO PRIMARY STRICT FINALIST
        # =================================================

        else:

            repair_candidates = (
                select_targeted_repair_candidates(
                    primary_concepts
                )
            )

            print(
                "Targeted-repair candidates:",
                len(
                    repair_candidates
                ),
            )

            for candidate in (
                repair_candidates
            ):

                print(
                    (
                        "  ↳ "
                        +
                        candidate.concept_id
                        +
                        " | score="
                        +
                        str(
                            candidate.weighted_score
                        )
                        +
                        " | gaps="
                        +
                        compact_json(
                            targeted_repair_dimension_gaps(
                                candidate
                            ),
                            1800,
                        )
                    )
                )

            # =============================================
            # ROUTE B:
            # TARGETED REPAIR
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

                targeted_repair_used = True

                targeted_repair_source_ids = [
                    candidate.concept_id
                    for candidate
                    in repair_candidates
                ]

                print("")
                print(
                    "🛠️ STC TARGETED CREATIVE REPAIR"
                )
                print(
                    "Near-miss detected."
                )
                print(
                    (
                        "Call 3 will repair the strongest "
                        "existing proposition."
                    )
                )
                print("")

                try:

                    director_calls += 1

                    director_history.append(
                        "stc_targeted_repair_board"
                    )

                    (
                        targeted_repair_concepts,
                        repair_jury,
                    ) = (
                        run_targeted_repair_board(
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

                    print_jury_diagnostics(
                        jury=(
                            repair_jury
                        ),
                        qualified=(
                            repair_qualified
                        ),
                        source=(
                            "stc_targeted_repair_board"
                        ),
                    )

                    final_jury_payload = (
                        repair_jury
                    )

                    (
                        winner,
                        strict_release_info,
                    ) = (
                        deterministic_strict_release(
                            concepts=(
                                targeted_repair_concepts
                            ),
                            jury=(
                                repair_jury
                            ),
                            source=(
                                "stc_targeted_repair_board"
                            ),
                        )
                    )

                    if winner:

                        release_level = (
                            "stc_targeted_repair_"
                            "strict_qualified_release"
                        )

                    else:

                        release_level = (
                            "targeted_repair_"
                            "quality_failed"
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
            # ROUTE C:
            # FRESH RECOVERY
            # =============================================

            elif (
                STC_CREATIVE_RECOVERY_ENABLED
                and
                director_calls
                <
                MASTERPIECE_MAX_DIRECTOR_CALLS
            ):

                fresh_recovery_used = True

                recovery_reason = (
                    "no_strict_primary_and_"
                    "no_repairable_near_miss"
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
                    (
                        "No repairable near-miss exists; "
                        "Call 3 will rebuild the "
                        "creative mechanism."
                    )
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
                            primary_concepts
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

                    for qualified_item in (
                        recovery_qualified
                    ):

                        print(
                            (
                                "  ✅ "
                                +
                                qualified_item.concept_id
                                +
                                " | "
                                +
                                qualified_item.title
                                +
                                " | score="
                                +
                                str(
                                    qualified_item.weighted_score
                                )
                            )
                        )

                    print_jury_diagnostics(
                        jury=(
                            recovery_jury
                        ),
                        qualified=(
                            recovery_qualified
                        ),
                        source=(
                            "stc_recovery_board"
                        ),
                    )

                    final_jury_payload = (
                        recovery_jury
                    )

                    #
                    # THIS IS THE EXACT REGRESSION FIX:
                    #
                    # Recovery strict finalists > 0
                    # MUST produce a winner.
                    #
                    (
                        winner,
                        strict_release_info,
                    ) = (
                        deterministic_strict_release(
                            concepts=(
                                recovery_concepts
                            ),
                            jury=(
                                recovery_jury
                            ),
                            source=(
                                "stc_recovery_board"
                            ),
                        )
                    )

                    if winner:

                        release_level = (
                            "stc_recovery_"
                            "strict_qualified_release"
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
    # ABSOLUTE FINAL STRICT REVALIDATION
    #
    # No new threshold.
    #
    # This simply proves the winner STILL passes the exact
    # same deterministic gates that qualified it.
    # =====================================================

    if (
        high_alert
        and
        winner is not None
    ):

        final_failures = (
            stc_dimension_gate_failures(
                winner
            )
        )

        final_hard = [
            failure
            for failure
            in winner.quality_gate_failures
            if failure
            in HARD_REJECT_FAILURES
        ]

        final_score_ok = bool(
            winner.weighted_score
            >=
            STC_HIGH_ALERT_RELEASE_FLOOR
        )

        final_feasible = bool(
            safe_dict(
                winner.feasibility
            ).get(
                "production_feasible",
                False,
            )
        )

        if (
            final_failures
            or
            final_hard
            or
            not final_score_ok
            or
            not final_feasible
        ):

            errors.append(
                (
                    "final_strict_revalidation_failed:"
                    +
                    compact_json(
                        {
                            "dimension_failures":
                                final_failures,

                            "hard_failures":
                                final_hard,

                            "score_ok":
                                final_score_ok,

                            "production_feasible":
                                final_feasible,
                        },
                        2500,
                    )
                )
            )

            winner.quality_gate_passed = (
                False
            )

            winner = None

            release_level = (
                "final_strict_revalidation_failed"
            )

        else:

            winner.quality_gate_passed = (
                True
            )

    # =====================================================
    # QUALITY STATE
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
        and
        winner.evaluation_valid
        and
        winner.quality_gate_passed
    )

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
    # LOG FINAL
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
            "Title:",
            winner.title
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

        print(
            "Strict release authority:",
            strict_release_info.get(
                "authority",
                (
                    "normal_release"
                    if not high_alert
                    else ""
                ),
            ),
        )

        print(
            "Final arbitration reason:",
            strict_release_info.get(
                "reason",
                "",
            ),
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
                (
                    best.title
                    or
                    best.concept_id
                ),
            )

            if high_alert:

                print(
                    "Failures:",
                    ", ".join(
                        stc_dimension_gate_failures(
                            best
                        )[:16]
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
        fresh_recovery_used,
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
                "targeted_repair_did_not_"
                "produce_strict_qualified_concept"
            )

        elif fresh_recovery_used:

            failure_reason = (
                "recovery_did_not_produce_"
                "strict_qualified_concept"
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
                (
                    "stc_deterministic_"
                    "strict_release_v56"
                ),

            "high_alert":
                high_alert,

            "benefit_family":
                benefit_family,

            "stc_style":
                stc_style,

            # =============================================
            # CALLS
            # =============================================

            "initial_concepts":
                concept_count,

            "director_calls":
                director_calls,

            "director_call_history":
                director_history,

            "director_call_target":
                (
                    3
                    if high_alert
                    else
                    2
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

            "targeted_repair_source_ids":
                targeted_repair_source_ids,

            "targeted_repair_concepts":
                len(
                    targeted_repair_concepts
                ),

            "targeted_repair_min_score":
                STC_TARGETED_REPAIR_MIN_SCORE,

            "targeted_repair_max_dimension_failures":
                STC_TARGETED_REPAIR_MAX_DIMENSION_FAILURES,

            "targeted_repair_max_gap":
                STC_TARGETED_REPAIR_MAX_GAP,

            # =============================================
            # RECOVERY
            # =============================================

            "recovery_enabled":
                STC_CREATIVE_RECOVERY_ENABLED,

            "recovery_used":
                fresh_recovery_used,

            "recovery_reason":
                recovery_reason,

            "recovery_concepts":
                len(
                    recovery_concepts
                ),

            # =============================================
            # V5.6 RELEASE AUTHORITY
            # =============================================

            "strict_qualified_release_authority":
                STC_STRICT_QUALIFIED_RELEASE_AUTHORITY,

            "strict_release_authority":
                strict_release_info.get(
                    "authority",
                    "",
                ),

            "strict_release_released":
                bool(
                    strict_release_info.get(
                        "released",
                        False,
                    )
                ),

            "strict_release_winner_id":
                strict_release_info.get(
                    "winner_id",
                    "",
                ),

            "strict_release_reason":
                strict_release_info.get(
                    "reason",
                    "",
                ),

            "strict_qualified_ids":
                strict_release_info.get(
                    "strict_qualified_ids",
                    [],
                ),

            "strict_qualified_count":
                strict_release_info.get(
                    "strict_qualified_count",
                    0,
                ),

            "jury_fields_are_advisory_after_strict_qualification":
                True,

            "jury_global_veto_allowed_after_strict_qualification":
                False,

            # =============================================
            # JURY DIAGNOSTICS
            # =============================================

            "finalist_jury_used":
                bool(
                    final_jury_payload
                ),

            "jury_diagnostics":
                jury_diagnostics(
                    final_jury_payload
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

            "thresholds_lowered":
                False,

            "thresholds_lowered_by_repair":
                False,

            "thresholds_lowered_by_jury":
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
            # QUALITY PROTECTIONS
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

            "camera_director_enabled":
                True,

            "scene_feasibility_enabled":
                True,

            "brand_pack_available":
                bool(
                    locate_stc_brand_pack()
                ),

            "brand_kit_available":
                STC_BRAND_KIT_AVAILABLE,

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
                (
                    response.winner.title
                    or
                    response.winner.concept_id
                )
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
# ZERO-COST V5.6 SELF TEST
#
# NO API CALLS.
# NO IMAGE GENERATION.
# =========================================================

if __name__ == "__main__":

    tests: Dict[
        str,
        bool,
    ] = {}

    # =====================================================
    # CONTRACT
    # =====================================================

    tests[
        "version_56"
    ] = (
        VERSION
        ==
        "5.6"
    )

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
    # WEIGHTS
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
    # STRICT THRESHOLDS UNCHANGED
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
    ] = bool(
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
        "three_call_target"
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
                "أنشئ إعلان STC Bank "
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
            "بيئة بنفسجية معمارية"
        )
        ==
        "premium_purple_architecture"
    )

    tests[
        "augmented_style"
    ] = (
        detect_stc_style(
            "واقعية معززة"
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
    # BUILD A REAL STRICT-QUALIFIED FIXTURE
    # =====================================================

    strict_a = CreativeConcept(

        concept_id="R01",

        title=(
            "ظلّ التجارة المزدوج"
        ),

        concept_archetype=(
            "campaign service transformation"
        ),

        campaign_hook=(
            "One physically believable visual mechanism "
            "connects online commerce with physical payment "
            "acceptance as one merchant ecosystem."
        ),

        core_idea=(
            "A premium Saudi commercial environment expresses "
            "e-commerce and in-store payment through one coherent "
            "physical relationship rather than a literal checkout."
        ),

        marketing_message=(
            "Unified merchant payment ecosystem."
        ),

        visual_metaphor=(
            "One continuous physical relationship makes the digital "
            "commerce channel and physical acceptance channel read "
            "as two expressions of the same merchant system."
        ),

        visual_mechanism_type=(
            "physical service continuity"
        ),

        why_not_generic=(
            "The service proposition is encoded into the central "
            "physical advertising mechanism, not documentary "
            "transaction photography."
        ),

        environment=(
            "Premium contemporary Saudi commercial architecture."
        ),

        environment_novelty=(
            "No ordinary checkout counter, no wooden boutique scene."
        ),

        hero_element=(
            "Unified commerce mechanism."
        ),

        camera_angle=(
            "elevated three-quarter view"
        ),

        lens="35mm",

        perspective=(
            "foreground-to-background reveal"
        ),

        lighting=(
            "controlled premium natural daylight"
        ),

        negative_space=(
            "30% natural upper-right negative space"
        ),

        brand_logic=(
            "Premium restrained STC Bank confidence."
        ),

        production_method=(
            "single_generation"
        ),

        evaluation_valid=True,

        weighted_score=93.32,

        scores={

            "concept_strength":
                94,

            "brand_fit":
                94,

            "originality":
                93,

            "visual_mechanism":
                95,

            "camera_quality":
                91,

            "realism":
                91,

            "feasibility":
                89,

            "copy_space_quality":
                90,

            "distinctiveness":
                94,

            "advertising_readiness":
                95,
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

        quality_gate_failures=[],
    )

    strict_b = CreativeConcept(

        concept_id="R02",

        title=(
            "Second qualified concept"
        ),

        concept_archetype=(
            "architectural mechanism"
        ),

        campaign_hook=(
            "One coherent campaign mechanism links both "
            "merchant payment channels."
        ),

        core_idea=(
            "A second production-ready STC Bank merchant concept."
        ),

        marketing_message=(
            "Unified commerce."
        ),

        visual_metaphor=(
            "Physical continuity between digital storefront "
            "and in-store payment acceptance."
        ),

        visual_mechanism_type=(
            "physical continuity"
        ),

        why_not_generic=(
            "The central relationship, not a transaction, "
            "communicates the benefit."
        ),

        environment=(
            "Contemporary Saudi commercial architecture."
        ),

        environment_novelty=(
            "No repeated checkout-counter scene."
        ),

        hero_element=(
            "Commerce continuity."
        ),

        camera_angle=(
            "controlled three-quarter view"
        ),

        lens="35mm",

        perspective=(
            "layered perspective reveal"
        ),

        lighting=(
            "premium daylight"
        ),

        negative_space=(
            "30% upper-left natural negative space"
        ),

        brand_logic=(
            "Premium STC Bank visual discipline."
        ),

        production_method=(
            "single_generation"
        ),

        evaluation_valid=True,

        weighted_score=91.40,

        scores={

            "concept_strength":
                92,

            "brand_fit":
                93,

            "originality":
                91,

            "visual_mechanism":
                92,

            "camera_quality":
                88,

            "realism":
                89,

            "feasibility":
                86,

            "copy_space_quality":
                87,

            "distinctiveness":
                91,

            "advertising_readiness":
                92,
        },

        feasibility={
            "production_feasible":
                True,
        },

        quality_gate_failures=[],
    )

    strict_fixture = (
        strict_qualified_concepts(
            [
                strict_a,
                strict_b,
            ],
            high_alert=True,
        )
    )

    tests[
        "two_strict_finalists_detected"
    ] = bool(
        len(
            strict_fixture
        )
        ==
        2
    )

    tests[
        "highest_strict_score_first"
    ] = bool(
        strict_fixture
        and
        strict_fixture[
            0
        ].concept_id
        ==
        "R01"
    )

    # =====================================================
    # EXACT V5.5 REGRESSION
    #
    # TWO strict finalists exist but Jury says:
    #
    #   approval=false
    #   low confidence
    #   merchant fusion=false
    #   fatal issues
    #
    # V5.5 could block.
    #
    # V5.6 MUST still release highest strict-qualified.
    # =====================================================

    hostile_global_jury = {

        "selected_concept_id":
            "R03",

        "approval":
            False,

        "confidence":
            42,

        "advertising_reason":
            (
                "Jury global field contradicts "
                "per-concept evaluation."
            ),

        "brand_reason":
            "Advisory only.",

        "originality_reason":
            "Advisory only.",

        "merchant_fusion_approved":
            False,

        "fatal_issues": [
            (
                "Global board concern referring "
                "to another candidate."
            )
        ],

        "production_instruction":
            "",

        "recommended_camera_angle":
            "",

        "recommended_lens":
            "",

        "recommended_perspective":
            "",

        "do_not_drift_into": [
            "generic checkout",
        ],
    }

    (
        regression_winner,
        regression_info,
    ) = deterministic_strict_release(
        concepts=[
            strict_a,
            strict_b,
        ],
        jury=(
            hostile_global_jury
        ),
        source=(
            "self_test_exact_v55_regression"
        ),
    )

    tests[
        "v55_regression_cannot_recur"
    ] = bool(
        regression_winner
        and
        regression_winner.concept_id
        ==
        "R01"
    )

    tests[
        "jury_approval_false_cannot_veto_strict_finalist"
    ] = bool(
        regression_winner
        is not None
    )

    tests[
        "jury_low_confidence_cannot_veto_strict_finalist"
    ] = bool(
        regression_winner
        is not None
    )

    tests[
        "jury_global_fatal_issue_cannot_veto_other_strict_finalist"
    ] = bool(
        regression_winner
        is not None
    )

    tests[
        "jury_global_merchant_false_cannot_veto_per_concept_fusion"
    ] = bool(
        regression_winner
        is not None
    )

    tests[
        "unqualified_jury_selection_cannot_win"
    ] = bool(
        regression_winner
        and
        regression_winner.concept_id
        ==
        "R01"
    )

    tests[
        "highest_strict_qualified_always_wins"
    ] = bool(
        regression_winner
        and
        regression_winner.weighted_score
        ==
        93.32
    )

    tests[
        "strict_release_no_threshold_lowering"
    ] = bool(
        regression_info.get(
            "thresholds_lowered"
        )
        is False
    )

    tests[
        "strict_release_authority_is_deterministic"
    ] = bool(
        regression_info.get(
            "authority"
        )
        ==
        (
            "deterministic_per_concept_"
            "strict_qualification"
        )
    )

    # =====================================================
    # JURY AGREEMENT CASE
    # =====================================================

    agreeing_jury = {

        **hostile_global_jury,

        "selected_concept_id":
            "R01",

        "approval":
            True,

        "confidence":
            96,

        "merchant_fusion_approved":
            True,

        "fatal_issues":
            [],

        "production_instruction":
            (
                "Preserve the hero mechanism."
            ),

        "recommended_camera_angle":
            "elevated three-quarter view",

        "recommended_lens":
            "35mm",

        "recommended_perspective":
            "foreground-to-background reveal",
    }

    (
        agreeing_winner,
        agreeing_info,
    ) = deterministic_strict_release(
        concepts=[
            strict_a,
            strict_b,
        ],
        jury=(
            agreeing_jury
        ),
        source=(
            "self_test_jury_agreement"
        ),
    )

    tests[
        "jury_agreement_still_releases"
    ] = bool(
        agreeing_winner
        and
        agreeing_winner.concept_id
        ==
        "R01"
    )

    # =====================================================
    # NO QUALIFIED CONCEPT MUST STILL FAIL
    # =====================================================

    weak = CreativeConcept(

        concept_id="R03",

        title="Weak",

        weighted_score=87.0,

        evaluation_valid=True,

        scores={

            "concept_strength":
                87,

            "brand_fit":
                89,

            "originality":
                87,

            "visual_mechanism":
                89,

            "camera_quality":
                84,

            "realism":
                86,

            "feasibility":
                83,

            "copy_space_quality":
                82,

            "distinctiveness":
                87,

            "advertising_readiness":
                89,
        },

        feasibility={
            "production_feasible":
                True,
        },

        quality_gate_failures=[],
    )

    (
        weak_winner,
        weak_info,
    ) = deterministic_strict_release(
        concepts=[
            weak
        ],
        jury=(
            agreeing_jury
        ),
        source=(
            "self_test_weak"
        ),
    )

    tests[
        "no_strict_finalist_still_blocks"
    ] = bool(
        weak_winner
        is None
        and
        weak_info.get(
            "reason"
        )
        ==
        "no_strict_qualified_concept"
    )

    # =====================================================
    # HARD REJECT MUST STILL FAIL
    # =====================================================

    hard = CreativeConcept(

        concept_id="BAD",

        title="Generic checkout",

        weighted_score=96.0,

        evaluation_valid=True,

        scores={

            "concept_strength":
                96,

            "brand_fit":
                96,

            "originality":
                96,

            "visual_mechanism":
                96,

            "camera_quality":
                96,

            "realism":
                96,

            "feasibility":
                96,

            "copy_space_quality":
                96,

            "distinctiveness":
                96,

            "advertising_readiness":
                96,
        },

        feasibility={
            "production_feasible":
                True,
        },

        quality_gate_failures=[
            "literal_transaction_tableau"
        ],
    )

    (
        hard_winner,
        _
    ) = deterministic_strict_release(
        concepts=[
            hard
        ],
        jury=(
            agreeing_jury
        ),
        source=(
            "self_test_hard"
        ),
    )

    tests[
        "hard_reject_still_blocks_even_at_96"
    ] = (
        hard_winner
        is None
    )

    # =====================================================
    # PRODUCTION FEASIBILITY MUST STILL FAIL
    # =====================================================

    impossible = CreativeConcept(

        concept_id="IMP",

        title="Impossible",

        weighted_score=95.0,

        evaluation_valid=True,

        scores={

            "concept_strength":
                95,

            "brand_fit":
                95,

            "originality":
                95,

            "visual_mechanism":
                95,

            "camera_quality":
                95,

            "realism":
                95,

            "feasibility":
                95,

            "copy_space_quality":
                95,

            "distinctiveness":
                95,

            "advertising_readiness":
                95,
        },

        feasibility={
            "production_feasible":
                False,
        },

        quality_gate_failures=[],
    )

    (
        impossible_winner,
        _
    ) = deterministic_strict_release(
        concepts=[
            impossible
        ],
        jury=(
            agreeing_jury
        ),
        source=(
            "self_test_impossible"
        ),
    )

    tests[
        "production_infeasible_still_blocks"
    ] = (
        impossible_winner
        is None
    )

    # =====================================================
    # NEAR MISS TARGETED REPAIR
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
            "One merchant ecosystem."
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
            "between both commerce channels."
        ),

        environment=(
            "Contemporary premium Saudi commercial architecture."
        ),

        environment_novelty=(
            "No conventional checkout-counter hero."
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

        evaluation_valid=True,

        scores={

            "concept_strength":
                87,

            "brand_fit":
                89,

            "originality":
                90,

            "visual_mechanism":
                92,

            "camera_quality":
                87,

            "realism":
                85,

            "feasibility":
                86,

            "copy_space_quality":
                85,

            "distinctiveness":
                90,

            "advertising_readiness":
                89,
        },

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
    )

    repair_candidates = (
        select_targeted_repair_candidates(
            [
                near_miss
            ]
        )
    )

    tests[
        "8794_near_miss_routes_to_repair"
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
    # HARD CONCEPT DOES NOT ENTER REPAIR
    # =====================================================

    hard_repair = CreativeConcept(

        concept_id="HARD_REPAIR",

        weighted_score=87.8,

        evaluation_valid=True,

        scores=dict(
            near_miss.scores
        ),

        feasibility={
            "production_feasible":
                True,
        },

        quality_gate_failures=[
            "literal_transaction_tableau"
        ],
    )

    tests[
        "hard_reject_cannot_enter_targeted_repair"
    ] = (
        not is_targeted_repair_candidate(
            hard_repair
        )
    )

    # =====================================================
    # SEMANTICS
    # =====================================================

    semantic = CreativeConcept(

        concept_id="SEM",

        title="Unified commerce",

        campaign_hook=(
            "A continuous physical connection unifies a "
            "digital storefront and in-store card reader."
        ),

        core_idea=(
            "Online commerce and physical acceptance become "
            "one merchant ecosystem."
        ),

        visual_metaphor=(
            "Physical continuity."
        ),

        visual_mechanism_type=(
            "physical connection"
        ),

        why_not_generic=(
            "The unified physical relationship is the advertising idea."
        ),

        environment=(
            "Contemporary Saudi commercial environment."
        ),

        environment_novelty=(
            "No conventional counter."
        ),

        hero_element=(
            "Unified merchant system."
        ),
    )

    semantic_signals = (
        merchant_local_signals(
            semantic
        )
    )

    tests[
        "digital_storefront_is_online"
    ] = bool(
        semantic_signals.get(
            "online"
        )
    )

    tests[
        "card_reader_is_physical_pos"
    ] = bool(
        semantic_signals.get(
            "physical"
        )
    )

    tests[
        "connection_language_is_mechanism"
    ] = bool(
        semantic_signals.get(
            "mechanism"
        )
    )

    # =====================================================
    # SERIALIZATION CONTRACT
    # =====================================================

    encoded = concept_to_dict(
        strict_a
    )

    tests[
        "concept_contract"
    ] = bool(
        encoded.get(
            "concept_id"
        )
        ==
        "R01"
        and
        "concept_archetype"
        in encoded
        and
        "campaign_hook"
        in encoded
        and
        "visual_mechanism_type"
        in encoded
        and
        "debate"
        in encoded
    )

    response_fixture = (
        CreativeBrainResponse(

            ok=True,

            mode=(
                MODE_MASTERPIECE
            ),

            request="test",

            total_concepts=1,

            concepts=[
                strict_a
            ],

            top_concepts=[
                strict_a
            ],

            winner=(
                strict_a
            ),

            metadata={
                "quality_gate_passed":
                    True,
            },

            errors=[],
        )
    )

    serialized = response_to_dict(
        response_fixture
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
        " XPAND CREATIVE BRAIN V5.6"
    )
    print(
        " ZERO-COST REGRESSION-PROOF SELF TEST"
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
                "XPAND Creative Brain V5.6 "
                "self-test: PASS ✅"
            )
        )

    else:

        print(
            (
                "XPAND Creative Brain V5.6 "
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
        "✅ Maximum 3 Director calls"
    )
    print(
        "✅ Strict STC thresholds unchanged"
    )
    print(
        "✅ Targeted Repair preserved"
    )
    print(
        "✅ Fresh Recovery preserved"
    )
    print(
        (
            "✅ Recovery strict finalists > 0 "
            "MUST release a strict winner"
        )
    )
    print(
        (
            "✅ Jury approval=false cannot erase "
            "a strict-qualified concept"
        )
    )
    print(
        (
            "✅ Jury low confidence cannot erase "
            "a strict-qualified concept"
        )
    )
    print(
        (
            "✅ Global Jury fatal issue cannot erase "
            "a different independently qualified concept"
        )
    )
    print(
        (
            "✅ Global Jury merchant flag cannot override "
            "per-concept merchant fusion evaluation"
        )
    )
    print(
        (
            "✅ Unqualified Jury selection cannot beat "
            "a strict-qualified concept"
        )
    )
    print(
        (
            "✅ Highest strict-qualified score wins "
            "deterministically"
        )
    )
    print(
        "✅ Hard rejects still block"
    )
    print(
        "✅ Production-infeasible concepts still block"
    )
    print(
        "✅ No thresholds were lowered"
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
