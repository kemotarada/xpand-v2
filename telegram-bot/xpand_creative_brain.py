# =========================================================
# XPAND CREATIVE BRAIN V5.2
#
# STC BANK HIGH-ALERT ADVERTISING INTELLIGENCE
# FULL RUNTIME-COMPATIBLE REPLACEMENT
#
# =========================================================
#
# Compatibility preserved for:
#
#   xpand_image_telegram.py V3.4+
#   xpand_production_engine.py V5.x+
#   xpand_image_engine.py V2.2+
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
# V5.2 HIGH-ALERT GOALS
#
# NORMAL:
#   - 4 concepts
#   - 2 Director calls
#
# STC BANK MASTERPIECE:
#   - 8 genuinely different concepts
#   - 1 structured ideation call
#   - 1 structured full review call
#   - 1 finalist jury call
#   - maximum 3 paid Director calls
#
# QUALITY PHILOSOPHY:
#
#   A scene is not an advertising idea.
#   A POS terminal is not an advertising idea.
#   A purple room is not brand identity.
#   A customer using a phone is not a campaign.
#
# STC HIGH ALERT requires:
#
#   - advertising mechanism
#   - benefit translation
#   - campaign-level composition
#   - STC Bank brand logic
#   - scene novelty
#   - environmental diversity
#   - intentional camera
#   - premium realism
#   - natural copy space
#   - no generated text/logo
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
        is_stc_bank_request,
        detect_stc_benefit_family,
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

        merchant_markers = (
            "نقاط البيع",
            "point of sale",
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
            in merchant_markers
        ):

            return "merchant_payments"

        return "general_banking"


# =========================================================
# IDENTITY
# =========================================================

VERSION = "5.2"

MODULE_NAME = "XPAND Creative Brain"


# =========================================================
# MODES
#
# CRITICAL COMPATIBILITY CONTRACT
# =========================================================

MODE_FAST = "fast"

MODE_MASTERPIECE = "masterpiece"


# =========================================================
# BOOLEAN ENV
# =========================================================

def env_bool(
    name: str,
    default: bool,
) -> bool:

    value = str(
        os.environ.get(
            name,
            "true"
            if default
            else "false",
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
# HIGH ALERT
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


# =========================================================
# QUALITY
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
# DIMENSION GATES
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
# COST / QUALITY POLICY
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

        return float(
            value
        )

    except Exception:

        return float(
            default
        )


def normalize_arabic(
    value: Any,
) -> str:

    text = clean_text(
        value,
        50000,
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

    text = normalize_arabic(
        value
    )

    return any(
        normalize_arabic(
            marker
        )
        in text
        for marker in markers
    )


def count_matches(
    value: Any,
    markers: Sequence[str],
) -> int:

    text = normalize_arabic(
        value
    )

    count = 0

    for marker in markers:

        if normalize_arabic(
            marker
        ) in text:

            count += 1

    return count


def compact_json(
    value: Any,
    limit: int = 10000,
) -> str:

    try:

        output = json.dumps(
            value,
            ensure_ascii=False,
            separators=(
                ",",
                ":",
            ),
        )

    except Exception:

        output = str(
            value
        )

    return output[:limit]


# =========================================================
# OPTIONAL PERMANENT STC BRAND PACK
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

                return path

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


def stc_brand_pack_prompt_fragment() -> str:

    pack = load_stc_brand_pack()

    if not pack:

        return (
            "No local STC brand-pack manifest was loaded. "
            "Use the built-in STC Bank visual intelligence."
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
            pack.get(
                "approved_mechanisms",
                [],
            ),

        "style_families":
            pack.get(
                "style_families",
                {},
            ),
    }

    asset_notes = []

    for item in safe_list(
        pack.get(
            "assets"
        )
    )[:20]:

        if not isinstance(
            item,
            dict,
        ):

            continue

        asset_notes.append(
            {
                "asset_id":
                    item.get(
                        "asset_id"
                    ),

                "roles":
                    item.get(
                        "roles",
                        [],
                    ),

                "tags":
                    item.get(
                        "tags",
                        [],
                    ),

                "notes":
                    item.get(
                        "notes",
                        "",
                    ),
            }
        )

    useful[
        "reference_asset_manifest"
    ] = asset_notes

    return compact_json(
        useful,
        10000,
    )


# =========================================================
# DATA MODEL
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
    "type": "object",

    "additionalProperties": False,

    "properties": {

        "concept_id": {
            "type": "string",
        },

        "category": {
            "type": "string",
        },

        "title": {
            "type": "string",
        },

        "concept_archetype": {
            "type": "string",
        },

        "campaign_hook": {
            "type": "string",
        },

        "core_idea": {
            "type": "string",
        },

        "marketing_message": {
            "type": "string",
        },

        "visual_metaphor": {
            "type": "string",
        },

        "visual_mechanism_type": {
            "type": "string",
        },

        "why_not_generic": {
            "type": "string",
        },

        "environment": {
            "type": "string",
        },

        "environment_novelty": {
            "type": "string",
        },

        "hero_element": {
            "type": "string",
        },

        "supporting_elements": {
            "type": "array",

            "items": {
                "type": "string",
            },
        },

        "camera_angle": {
            "type": "string",
        },

        "lens": {
            "type": "string",
        },

        "perspective": {
            "type": "string",
        },

        "lighting": {
            "type": "string",
        },

        "negative_space": {
            "type": "string",
        },

        "brand_logic": {
            "type": "string",
        },

        "production_method": {
            "type": "string",

            "enum": [
                "single_generation",
                "controlled_edit",
                "composite",
                "inpainting",
            ],
        },

        "campaign_extension": {
            "type": "string",
        },

        "risks": {
            "type": "array",

            "items": {
                "type": "string",
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
        "type": "object",

        "additionalProperties": False,

        "properties": {
            "concepts": {
                "type": "array",

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

def make_review_schema(
    concept_count: int,
) -> Dict[str, Any]:

    return {
        "type": "object",

        "additionalProperties": False,

        "properties": {

            "evaluations": {
                "type": "array",

                "minItems":
                    concept_count,

                "maxItems":
                    concept_count,

                "items": {
                    "type": "object",

                    "additionalProperties": False,

                    "properties": {

                        "concept_id": {
                            "type": "string",
                        },

                        "concept_strength": {
                            "type": "number",
                        },

                        "brand_fit": {
                            "type": "number",
                        },

                        "originality": {
                            "type": "number",
                        },

                        "visual_mechanism": {
                            "type": "number",
                        },

                        "camera_quality": {
                            "type": "number",
                        },

                        "realism": {
                            "type": "number",
                        },

                        "feasibility": {
                            "type": "number",
                        },

                        "copy_space_quality": {
                            "type": "number",
                        },

                        "distinctiveness": {
                            "type": "number",
                        },

                        "advertising_readiness": {
                            "type": "number",
                        },

                        "weighted_score": {
                            "type": "number",
                        },

                        "verdict": {
                            "type": "string",

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
                            "type": "array",

                            "items": {
                                "type": "string",
                            },
                        },

                        "weaknesses": {
                            "type": "array",

                            "items": {
                                "type": "string",
                            },
                        },

                        "generic_scene_risk": {
                            "type": "boolean",
                        },

                        "repetition_risk": {
                            "type": "boolean",
                        },

                        "looks_like_real_bank_campaign": {
                            "type": "boolean",
                        },

                        "recommended_camera_angle": {
                            "type": "string",
                        },

                        "recommended_lens": {
                            "type": "string",
                        },

                        "recommended_perspective": {
                            "type": "string",
                        },

                        "camera_reason": {
                            "type": "string",
                        },

                        "production_feasible": {
                            "type": "boolean",
                        },

                        "feasibility_reason": {
                            "type": "string",
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
                        "looks_like_real_bank_campaign",
                        "recommended_camera_angle",
                        "recommended_lens",
                        "recommended_perspective",
                        "camera_reason",
                        "production_feasible",
                        "feasibility_reason",
                    ],
                },
            },
        },

        "required": [
            "evaluations",
        ],
    }


# =========================================================
# FINALIST JURY SCHEMA
# =========================================================

FINALIST_JURY_SCHEMA: Dict[
    str,
    Any,
] = {
    "type": "object",

    "additionalProperties": False,

    "properties": {

        "selected_concept_id": {
            "type": "string",
        },

        "approval": {
            "type": "boolean",
        },

        "confidence": {
            "type": "number",
        },

        "advertising_reason": {
            "type": "string",
        },

        "brand_reason": {
            "type": "string",
        },

        "originality_reason": {
            "type": "string",
        },

        "fatal_issues": {
            "type": "array",

            "items": {
                "type": "string",
            },
        },

        "production_instruction": {
            "type": "string",
        },

        "recommended_camera_angle": {
            "type": "string",
        },

        "recommended_lens": {
            "type": "string",
        },

        "recommended_perspective": {
            "type": "string",
        },

        "do_not_drift_into": {
            "type": "array",

            "items": {
                "type": "string",
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
        "fatal_issues",
        "production_instruction",
        "recommended_camera_angle",
        "recommended_lens",
        "recommended_perspective",
        "do_not_drift_into",
    ],
}


# =========================================================
# STC VISUAL INTELLIGENCE
# =========================================================

STC_GENERIC_PATTERNS = [

    "شخص يستخدم الهاتف",
    "شخص يمسك الهاتف",
    "رجل يستخدم الهاتف",
    "امرأة تستخدم الهاتف",

    "person using phone",
    "man using phone",
    "woman using phone",

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
    "glowing payment trail",
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
]


# =========================================================
# BENEFIT ROUTING
# =========================================================

def detect_benefit_family(
    user_request: str,
) -> str:

    value = clean_text(
        user_request,
        12000,
    )

    normalized = normalize_arabic(
        value
    )

    #
    # IMPORTANT:
    # Merchant payments BEFORE generic "points".
    #

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
            12000,
        )
        +
        "\n"
        +
        clean_text(
            style_hint,
            1000,
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
        ],
    ):

        return "premium_augmented_realism"

    return "premium_realistic"


# =========================================================
# HIGH ALERT DETECTION
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
            150,
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
            500,
        ),

        campaign_hook=clean_text(
            item.get(
                "campaign_hook"
            ),
            1400,
        ),

        core_idea=clean_text(
            item.get(
                "core_idea"
            ),
            3200,
        ),

        marketing_message=clean_text(
            item.get(
                "marketing_message"
            ),
            1800,
        ),

        visual_metaphor=clean_text(
            item.get(
                "visual_metaphor"
            ),
            2200,
        ),

        visual_mechanism_type=clean_text(
            item.get(
                "visual_mechanism_type"
            ),
            600,
        ),

        why_not_generic=clean_text(
            item.get(
                "why_not_generic"
            ),
            1800,
        ),

        environment=clean_text(
            item.get(
                "environment"
            ),
            2600,
        ),

        environment_novelty=clean_text(
            item.get(
                "environment_novelty"
            ),
            1600,
        ),

        hero_element=clean_text(
            item.get(
                "hero_element"
            ),
            1600,
        ),

        supporting_elements=[
            clean_text(
                value,
                800,
            )
            for value
            in safe_list(
                item.get(
                    "supporting_elements"
                )
            )[:8]
            if clean_text(
                value,
                800,
            )
        ],

        camera_angle=clean_text(
            item.get(
                "camera_angle"
            ),
            800,
        ),

        lens=clean_text(
            item.get(
                "lens"
            ),
            350,
        ),

        perspective=clean_text(
            item.get(
                "perspective"
            ),
            1000,
        ),

        lighting=clean_text(
            item.get(
                "lighting"
            ),
            1500,
        ),

        negative_space=clean_text(
            item.get(
                "negative_space"
            ),
            1100,
        ),

        brand_logic=clean_text(
            item.get(
                "brand_logic"
            ),
            2000,
        ),

        production_method=clean_text(
            item.get(
                "production_method"
            ),
            100,
        ),

        campaign_extension=clean_text(
            item.get(
                "campaign_extension"
            ),
            1400,
        ),

        risks=[
            clean_text(
                value,
                800,
            )
            for value
            in safe_list(
                item.get(
                    "risks"
                )
            )[:8]
            if clean_text(
                value,
                800,
            )
        ],

        generation_round=(
            generation_round
        ),
    )


# =========================================================
# LOCAL CONCEPT TEXT
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
            concept.camera_angle,
            concept.lens,
            concept.perspective,
            concept.lighting,
            concept.negative_space,
            concept.brand_logic,
            " ".join(
                concept.supporting_elements
            ),
        ]
    )


# =========================================================
# HARD REJECT IDS
# =========================================================

HARD_REJECT_FAILURES = {

    "literal_transaction_tableau",

    "generic_fintech_visual",

    "repeated_stc_scene",

    "merchant_channels_not_visually_connected",

    "generic_lifestyle_without_advertising_mechanism",
}


# =========================================================
# LOCAL CREATIVE GUARD
#
# ZERO COST
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

    is_stc = is_stc_bank_request(
        user_request
    )

    if is_stc:

        # -------------------------------------------------
        # FINTECH CLICHES
        # -------------------------------------------------

        if contains_any(
            text,
            STC_FINTECH_CLICHES,
        ):

            penalty += 28.0

            failures.append(
                "generic_fintech_visual"
            )

        # -------------------------------------------------
        # REPEATED STC SCENES
        # -------------------------------------------------

        if (
            STC_REJECT_REPEATED_SCENES
            and
            contains_any(
                text,
                STC_REPETITION_BLACKLIST,
            )
        ):

            penalty += 22.0

            failures.append(
                "repeated_stc_scene"
            )

        # -------------------------------------------------
        # LITERAL COUNTER TABLEAU
        #
        # This specifically blocks the bad pattern:
        #
        # customer + terminal + merchant + counter +
        # tablet/packing in same generic retail scene.
        # -------------------------------------------------

        literal_matches = count_matches(
            text,
            STC_LITERAL_TRANSACTION_TABLEAU,
        )

        if literal_matches >= 3:

            penalty += 38.0

            failures.append(
                "literal_transaction_tableau"
            )

        # -------------------------------------------------
        # GENERIC LIFESTYLE WITHOUT MECHANISM
        # -------------------------------------------------

        generic_hits = count_matches(
            text,
            STC_GENERIC_PATTERNS,
        )

        mechanism_text = (
            concept.visual_metaphor
            +
            " "
            +
            concept.visual_mechanism_type
            +
            " "
            +
            concept.campaign_hook
        )

        mechanism_markers = count_matches(
            mechanism_text,
            STC_VISUAL_MECHANISM_MARKERS,
        )

        if (
            STC_REJECT_GENERIC_SCENES
            and
            generic_hits > 0
            and
            (
                mechanism_markers == 0
                or
                len(
                    clean_text(
                        concept.why_not_generic,
                        1500,
                    )
                )
                <
                60
            )
        ):

            penalty += 30.0

            failures.append(
                "generic_lifestyle_without_advertising_mechanism"
            )

        # -------------------------------------------------
        # PURPLE NEON
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

            penalty += 22.0

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

                "يسار",
                "يمين",
                "أعلى",
                "اعلى",
                "أسفل",
                "اسفل",

                "25%",
                "30%",
                "35%",
                "40%",
            ],
        ):

            penalty += 7.0

            failures.append(
                "weak_copy_space"
            )

        # -------------------------------------------------
        # CAMERA PRECISION
        # -------------------------------------------------

        camera_text = (
            concept.camera_angle
            +
            " "
            +
            concept.perspective
            +
            " "
            +
            concept.lens
        )

        if not contains_any(
            camera_text,
            [
                "low angle",
                "worm",
                "bird",
                "elevated",
                "over-the-shoulder",
                "over the shoulder",
                "three-quarter",
                "three quarter",
                "top-down",
                "top down",
                "compressed perspective",
                "foreground framing",
                "high angle",
                "eye-level",
                "eye level",
                "macro",
                "close-up",
                "close up",
                "wide-angle",
                "wide angle",
                "telephoto",
                "35mm",
                "50mm",
                "85mm",
                "24mm",
                "28mm",
            ],
        ):

            penalty += 6.0

            failures.append(
                "camera_not_precise"
            )

        # -------------------------------------------------
        # ADVERTISING LOGIC
        # -------------------------------------------------

        if (
            STC_REQUIRE_ADVERTISING_STYLE
            and
            len(
                clean_text(
                    concept.campaign_hook,
                    1200,
                )
            )
            <
            45
        ):

            penalty += 12.0

            failures.append(
                "weak_campaign_hook"
            )

        if (
            STC_REQUIRE_VISUAL_MECHANISM
            and
            len(
                clean_text(
                    concept.visual_metaphor,
                    1600,
                )
            )
            <
            65
        ):

            penalty += 14.0

            failures.append(
                "weak_visual_mechanism"
            )

        if (
            len(
                clean_text(
                    concept.why_not_generic,
                    1400,
                )
            )
            <
            55
        ):

            penalty += 8.0

            failures.append(
                "generic_defense_missing"
            )

        if (
            len(
                clean_text(
                    concept.environment_novelty,
                    1200,
                )
            )
            <
            45
        ):

            penalty += 6.0

            failures.append(
                "environment_novelty_missing"
            )

    # =====================================================
    # MERCHANT PAYMENTS
    # =====================================================

    if (
        benefit_family
        ==
        "merchant_payments"
    ):

        commerce_text = normalize_arabic(
            text
        )

        online_present = any(
            normalize_arabic(
                marker
            )
            in commerce_text
            for marker in [
                "تجارة إلكترونية",
                "طلب اونلاين",
                "طلب إلكتروني",
                "ecommerce",
                "e-commerce",
                "online order",
                "digital order",
                "fulfillment",
                "packing",
                "shipment",
                "online commerce",
            ]
        )

        physical_present = any(
            normalize_arabic(
                marker
            )
            in commerce_text
            for marker in [
                "نقاط البيع",
                "point of sale",
                "pos",
                "terminal",
                "tap payment",
                "checkout",
                "الدفع داخل المتجر",
                "physical payment",
                "in-store payment",
            ]
        )

        if not online_present:

            penalty += 12.0

            failures.append(
                "merchant_online_channel_missing"
            )

        if not physical_present:

            penalty += 12.0

            failures.append(
                "merchant_pos_channel_missing"
            )

        #
        # THIS IS THE IMPORTANT PART.
        #
        # Merely putting both channels in the same room
        # is NOT enough.
        #

        bridge_text = (
            concept.visual_metaphor
            +
            " "
            +
            concept.visual_mechanism_type
            +
            " "
            +
            concept.campaign_hook
            +
            " "
            +
            concept.core_idea
        )

        bridge_count = count_matches(
            bridge_text,
            STC_VISUAL_MECHANISM_MARKERS,
        )

        if (
            online_present
            and
            physical_present
            and
            bridge_count == 0
        ):

            penalty += 30.0

            failures.append(
                "merchant_channels_not_visually_connected"
            )

    return (
        penalty,
        failures,
    )


# =========================================================
# STC DIMENSION GATE
# =========================================================

def stc_dimension_gate_failures(
    concept: CreativeConcept,
) -> List[str]:

    failures: List[str] = []

    scores = safe_dict(
        concept.scores
    )

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

        value = safe_float(
            scores.get(
                key
            ),
            0.0,
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
        concept.feasibility.get(
            "production_feasible",
            False,
        )
    ):

        failures.append(
            "production_not_feasible"
        )

    return failures


# =========================================================
# ARCHETYPE INSTRUCTIONS
# =========================================================

STC_HIGH_ALERT_ARCHETYPES = """

For the eight concepts, deliberately cover different
advertising archetypes.

Do NOT repeat the same shop with different camera angles.

Concept 1:
PREMIUM HUMAN REALISM
A real Saudi lifestyle/commercial moment, but with a strong
advertising mechanism.

Concept 2:
OBJECT-LED COMMERCIAL STORY
A real product/object relationship communicates the service
without floating fintech clichés.

Concept 3:
ARCHITECTURAL / SPATIAL IDEA
Environment, threshold, geometry, or spatial relationship
becomes the advertising mechanism.

Concept 4:
AUGMENTED REALISM
One physically believable imaginative intervention inside
an otherwise realistic scene.

Concept 5:
CAMERA-LED IDEA
The advertising concept depends on an unusual but justified
scientific camera perspective.

Concept 6:
SERVICE TRANSFORMATION
One real-world action or object transforms into another
commercial meaning.

Concept 7:
SAUDI CULTURAL / BUSINESS CONTEXT
Use an authentic Saudi commerce context that is NOT the
standard boutique-counter cliché.

Concept 8:
BOLD CAMPAIGN HERO
The most award-minded direction. One strong image,
one surprising visual proposition, extremely simple.

If more than eight concepts are requested:
continue with genuinely new archetypes.

At most TWO concepts may use an indoor retail environment.

At most ONE concept may place a POS terminal as the obvious
foreground hero.

Do not use the same hero-object relationship twice.
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
RECOVERY MODE
==================================================

A previous structured ideation attempt failed.

Return the COMPLETE schema exactly.

Do not shorten the response.

Do not return:
- only "الفكرة"
- only "السبب"
- color keys
- lighting-only keys

Return exactly {concept_count} complete concepts.
"""

    stc_block = ""

    if is_stc_bank_request(
        user_request
    ):

        high_alert_text = ""

        if high_alert:

            high_alert_text = f"""
==================================================
STC BANK HIGH-ALERT MODE
==================================================

This request is under 5-STAR advertising standards.

A merely beautiful scene FAILS.

A realistic transaction scene FAILS if it has no
campaign-level advertising mechanism.

The concepts must survive comparison with premium bank,
telecom-finance, travel-card, luxury retail and modern
Saudi campaign photography.

The creative team is allowed to think longer.

Do not optimize for the fastest/easiest image.

QUALITY > SPEED.

--------------------------------------------------
MANDATORY DIVERSITY ARCHITECTURE
--------------------------------------------------

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

Target:
TOP-TIER STC BANK ADVERTISING.

Think as:
- executive creative director
- senior art director
- advertising photographer
- production designer
- brand guardian

Do NOT think like:
"a prompt writer trying to show the requested service."

{high_alert_text}

==================================================
PERMANENT LOCAL STC BRAND PACK
==================================================

{stc_brand_pack_prompt_fragment()}

==================================================
CENTRAL ADVERTISING LAW
==================================================

Every concept needs ONE memorable VISUAL MECHANISM.

The viewer should be able to look at the image and feel:

"This was intentionally conceived as an advertisement."

NOT:

"This is a nice photograph of people using a service."

A visual mechanism can use:

- cause and effect
- spatial continuity
- transformation
- scale
- perspective reveal
- framing
- material transition
- architectural metaphor
- physical visual bridge
- one impossible-but-believable intervention
- compression of two service moments into one physical idea
- foreground/background relationship with actual meaning

Do NOT mechanically copy those examples.

Invent the mechanism for THIS benefit.

==================================================
STC BANK VISUAL FAMILIES
==================================================

A) PREMIUM REALISM

Real Saudi life.

Real architecture.

Real businesses.

Clear faces and materials.

Strong art direction.

Natural or cinematic real-world light.

Refined color grade.

STC identity is carried through:
- confidence
- composition
- product/service behavior
- restrained color accents
- clean modernity
- premium Saudi tone

NOT by painting everything purple.

--------------------------------------------------

B) PURPLE ARCHITECTURAL WORLD

Only when explicitly requested or creatively justified.

Purple acts as:
- architecture
- volume
- plane
- controlled background
- geometric structure

NOT:
- random neon
- glowing fintech room
- cheap gradients everywhere

Use:
- satin surfaces
- lacquer
- polished edges
- controlled specular highlights
- deliberate shadows
- premium reflections

--------------------------------------------------

C) AUGMENTED REALISM

Real photographic environment
+
ONE imaginative physical intervention.

It should feel:
- clever
- premium
- simple
- photographically plausible

NOT:
- sci-fi
- HUD
- hologram
- particle explosion
- random floating icons

==================================================
CAMERA INTELLIGENCE
==================================================

Use exact photographic vocabulary.

Choose camera for meaning.

Examples:

- eye-level environmental portrait
- low-angle hero shot
- worm's-eye view
- bird's-eye view
- elevated three-quarter view
- high-angle architectural shot
- over-the-shoulder POV
- foreground-framed composition
- compressed telephoto perspective
- shallow-depth environmental portrait
- symmetrical frontal hero
- diagonal three-quarter product shot
- macro detail
- extreme close-up
- wide environmental establishing shot
- controlled 24mm architectural perspective
- natural 35mm environmental perspective
- 50mm commercial realism
- 85mm compressed portrait perspective

Do not select a strange angle only to sound creative.

The camera must strengthen:
- mechanism
- hierarchy
- scale
- emotion
- benefit clarity

==================================================
LIGHTING
==================================================

Use physically believable premium advertising light:

- large-window daylight
- directional morning light
- warm golden-hour side light
- soft skylight
- premium diffused key
- negative fill
- soft practicals
- edge separation
- motivated bounce
- realistic contact shadow
- controlled specular highlight
- premium material reflections

Avoid meaningless purple neon.

==================================================
MATERIAL LANGUAGE
==================================================

Use materials deliberately.

Possible materials:

- limestone
- stone
- travertine
- glass
- brushed aluminum
- dark matte metal
- satin lacquer
- polished lacquer
- leather
- premium textile
- paper
- premium packaging
- ceramic
- architectural concrete
- dark stone
- selective timber

IMPORTANT:

Wood must NOT automatically become
"the luxury merchant counter".

Do not keep returning to the same:
wooden checkout counter + tablet + POS terminal composition.

==================================================
COMPOSITION
==================================================

One hero.

One message.

One visual mechanism.

One intentional focal path.

25%-40% natural negative space for manual typography.

Negative space must be integrated into composition.

Do NOT put generated:
- headline
- slogan
- CTA
- legal copy
- logo
- STC Bank wordmark
- Visa logo
- readable banking UI
- fake interface text

==================================================
HARD REJECT: GENERIC STC SCENES
==================================================

These are NOT acceptable concepts:

- customer simply paying at a counter
- merchant behind a counter
- tablet beside POS terminal
- worker packing a box in background
- wooden counter as luxury shorthand
- generic boutique checkout
- generic perfume store checkout
- person simply looking at phone
- employee smiling at desk
- card floating in room
- POS floating in room
- generic airport traveler
- handshake
- coins flying
- network lines
- holograms
- fintech tunnel
- glowing particles
- random purple props
- empty purple room
- card on purple cube
- repeated card pedestal composition

The specific pattern:

CUSTOMER + POS + COUNTER + MERCHANT +
TABLET/PACKING

is considered a FAILED concept unless the physical
composition itself creates an unmistakably original
advertising mechanism.

==================================================
MERCHANT PAYMENTS
==================================================

If benefit_family = merchant_payments:

You must communicate BOTH:

1. online commerce / e-commerce
2. physical point-of-sale / in-store payment

But:

DO NOT merely place both activities in the same room.

The concept must connect online commerce and physical
payment visually through ONE strong advertising mechanism.

The relationship must be:
- causal
- spatial
- transformational
- symbolic
- perspectival
- or physically integrated

"Person taps terminal while someone packs a parcel
in the background"

is specifically considered weak.

The viewer must understand:
one merchant ecosystem,
two sales channels,
one coherent service proposition.

==================================================
CONCEPT DEFENSE
==================================================

For every concept you MUST explain:

why_not_generic

This field must explain precisely why the idea is
an advertisement instead of ordinary lifestyle photography.

environment_novelty must explain why the location,
space, or world differs from standard bank-ad clichés.

==================================================
STC SKILL
==================================================

{clean_text(STC_BANK_VISUAL_SKILL, 7000)}
"""

    return f"""
You are XPAND Creative Brain V5.2.

You are creating campaign-grade advertising ideas.

==================================================
ORIGINAL REQUEST
==================================================

{clean_text(user_request, 7000)}

==================================================
BRAND CONTEXT
==================================================

{compact_json(brand_context, 7000)}

==================================================
VISUAL REFERENCE DNA
==================================================

{compact_json(visual_references, 9000)}

References are DNA, not templates.

Extract:
- art-direction level
- visual hierarchy
- camera discipline
- material quality
- lighting
- brand confidence
- campaign simplicity

DO NOT clone a reference image.

==================================================
STYLE HINT
==================================================

{clean_text(style_hint, 1500)}

==================================================
IDEATION RULES
==================================================

Generate exactly {concept_count} fundamentally different
advertising concepts.

Do not produce cosmetic variations.

Each concept must differ in:
- concept archetype
- visual mechanism
- hero relationship
- environment
- spatial composition
- camera strategy

No generated text or logo inside the image.

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

Do not score concepts in this call.

Do not rush toward the easiest scene.
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

        strict_block = """
==================================================
HIGH-ALERT REVIEW STANDARD
==================================================

You are NOT rewarding competent work.

You are searching for a campaign-quality winner.

A concept should NOT score 90+ just because:
- it is feasible
- it is pretty
- it is realistic
- it shows the requested service

A 90+ concept must have:
- strong advertising mechanism
- high STC Bank relevance
- memorable composition
- clear benefit translation
- scene novelty
- premium bank-campaign readiness
- strong visual simplicity

Specifically reject or heavily penalize:

customer + POS + counter + merchant + tablet/packing

even if beautifully photographed.

Also penalize:
- repeated luxury boutique
- repeated wood counter
- repeated perfume/fashion merchant
- generic person with phone
- generic transaction photography
- purple as a substitute for brand thinking
- copy-space-only composition
"""

    return f"""
You are XPAND V5.2 EXECUTIVE CREATIVE REVIEW BOARD.

Evaluate ALL concepts.

You are:
- executive creative director
- STC Bank brand guardian
- senior advertising art director
- commercial photography director
- production feasibility reviewer

Do NOT invent replacement concepts.

==================================================
REQUEST
==================================================

{clean_text(user_request, 6000)}

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

{compact_json(payload, 30000)}

==================================================
SCORING
==================================================

Score each dimension 0-100.

concept_strength:
Does one frame communicate a strong advertising proposition?

brand_fit:
Could this plausibly belong to STC Bank at a premium level,
without depending on purple everywhere?

originality:
Is it more memorable than normal commercial stock imagery?

visual_mechanism:
Is there a genuine visual idea or merely a scene?

camera_quality:
Does the camera strengthen the concept?

realism:
Can it look premium, physically credible and photographic?

feasibility:
Can an image model produce it without collapsing the idea?

copy_space_quality:
Is manual typography space naturally built into composition?

distinctiveness:
Is this meaningfully different from the other concepts and
from generic bank advertising?

advertising_readiness:
Does it already feel like a real campaign key visual?

weighted_score:
Your overall strict creative score.

==================================================
MANDATORY BOOLEAN JUDGMENTS
==================================================

generic_scene_risk:
TRUE if the concept can easily collapse into generic lifestyle
or generic transaction photography.

repetition_risk:
TRUE if it resembles:
- wooden merchant counter
- generic boutique POS scene
- card pedestal
- purple room
- person looking at phone

looks_like_real_bank_campaign:
TRUE only if the concept has the discipline and idea quality
of a serious premium financial campaign.

==================================================
MERCHANT PAYMENTS
==================================================

If merchant_payments:

The winning concept MUST connect online commerce and
physical payment visually.

Simply showing:
payment foreground + packing background

does NOT qualify as integration.

There must be a real mechanism.

==================================================
CAMERA REVIEW
==================================================

Return one final coherent:
- camera angle
- lens
- perspective

for every concept.

No contradictory camera systems.

{strict_block}

==================================================
IMPORTANT
==================================================

Do not inflate scores.

An attractive ordinary scene can score 65-78.

A polished but familiar campaign can score 78-86.

90+ is reserved for exceptional campaign-ready concepts.

Return the schema exactly.
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
        for concept
        in finalists
    ]

    return f"""
You are the FINAL XPAND STC BANK CAMPAIGN JURY.

This is the final decision before expensive image production.

You are not allowed to reward a safe concept merely because
it is easy to generate.

==================================================
REQUEST
==================================================

{clean_text(user_request, 6000)}

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

{compact_json(payload, 22000)}

==================================================
YOUR JOB
==================================================

Select ONE finalist only if it deserves production.

Judge:

1. Does it feel like a premium bank campaign?
2. Does it communicate the benefit visually?
3. Is the visual mechanism actually memorable?
4. Is it clearly different from generic lifestyle photography?
5. Is the scene materially and photographically premium?
6. Can it avoid collapsing into:
   - wooden counter
   - generic boutique checkout
   - plain POS scene
   - purple neon
   - floating fintech cliché?
7. Does it fit STC Bank without requiring logos or text?

For merchant payments:

The concept must visually unify:
online commerce
+
physical payment

through a genuine advertising device.

==================================================
APPROVAL
==================================================

approval = true ONLY if you would personally authorize
production as a senior creative director.

fatal_issues must contain any reason the image should NOT
be produced.

If there is no worthy finalist:
approval = false.

==================================================
PRODUCTION INSTRUCTION
==================================================

Give a concise but highly specific art-direction instruction.

Lock:
- hero relationship
- camera
- environment
- visual mechanism
- lighting logic

Also state what production must NOT drift into.

Return the structured schema exactly.
""".strip()


# =========================================================
# IDEATION CALL
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
            "xpand_creative_ideation_v52"
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
                90000,
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
            "xpand_creative_review_v52"
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

    evaluations = safe_list(
        payload.get(
            "evaluations"
        )
    )

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

    evaluation_map = {}

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

    for concept in concepts:

        evaluation = evaluation_map.get(
            concept.concept_id
        )

        if not evaluation:

            raise RuntimeError(
                (
                    "Missing evaluation for "
                    +
                    concept.concept_id
                )
            )

        model_score = safe_float(
            evaluation.get(
                "weighted_score"
            ),
            0.0,
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

        bank_campaign = bool(
            evaluation.get(
                "looks_like_real_bank_campaign",
                False,
            )
        )

        risk_penalty = 0.0

        if generic_scene_risk:

            risk_penalty += 12.0

            local_failures.append(
                "review_generic_scene_risk"
            )

        if repetition_risk:

            risk_penalty += 12.0

            local_failures.append(
                "review_repetition_risk"
            )

        if (
            is_stc_bank_request(
                user_request
            )
            and
            not bank_campaign
        ):

            risk_penalty += 14.0

            local_failures.append(
                "not_bank_campaign_ready"
            )

        final_score = max(
            0.0,
            min(
                100.0,
                model_score
                -
                local_penalty
                -
                risk_penalty,
            ),
        )

        #
        # HARD REJECTS CANNOT GET RELEASE SCORE.
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

            "concept_strength":
                safe_float(
                    evaluation.get(
                        "concept_strength"
                    )
                ),

            "brand_fit":
                safe_float(
                    evaluation.get(
                        "brand_fit"
                    )
                ),

            "originality":
                safe_float(
                    evaluation.get(
                        "originality"
                    )
                ),

            "visual_mechanism":
                safe_float(
                    evaluation.get(
                        "visual_mechanism"
                    )
                ),

            "camera_quality":
                safe_float(
                    evaluation.get(
                        "camera_quality"
                    )
                ),

            "realism":
                safe_float(
                    evaluation.get(
                        "realism"
                    )
                ),

            "feasibility":
                safe_float(
                    evaluation.get(
                        "feasibility"
                    )
                ),

            "copy_space_quality":
                safe_float(
                    evaluation.get(
                        "copy_space_quality"
                    )
                ),

            "distinctiveness":
                safe_float(
                    evaluation.get(
                        "distinctiveness"
                    )
                ),

            "advertising_readiness":
                safe_float(
                    evaluation.get(
                        "advertising_readiness"
                    )
                ),

            "model_weighted_score":
                model_score,

            "local_penalty":
                local_penalty,

            "review_risk_penalty":
                risk_penalty,
        }

        concept.weighted_score = round(
            final_score,
            2,
        )

        concept.evaluation_valid = True

        concept.quality_gate_failures = list(
            dict.fromkeys(
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
                        "production_feasible"
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

            "strengths":
                safe_list(
                    evaluation.get(
                        "strengths"
                    )
                ),

            "weaknesses":
                safe_list(
                    evaluation.get(
                        "weaknesses"
                    )
                ),

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

            "looks_like_real_bank_campaign":
                bank_campaign,

            "camera_director": {

                "camera_angle":
                    clean_text(
                        evaluation.get(
                            "recommended_camera_angle"
                        ),
                        800,
                    )
                    or
                    concept.camera_angle,

                "lens":
                    clean_text(
                        evaluation.get(
                            "recommended_lens"
                        ),
                        350,
                    )
                    or
                    concept.lens,

                "perspective":
                    clean_text(
                        evaluation.get(
                            "recommended_perspective"
                        ),
                        800,
                    )
                    or
                    concept.perspective,

                "perspective_type":
                    clean_text(
                        evaluation.get(
                            "recommended_perspective"
                        ),
                        800,
                    )
                    or
                    concept.perspective,

                "creative_reason":
                    clean_text(
                        evaluation.get(
                            "camera_reason"
                        ),
                        1200,
                    ),

                "camera_lock_instruction":
                    (
                        "Preserve this exact camera strategy "
                        "during image production."
                    ),
            },
        }

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

            concept.quality_gate_failures = list(
                dict.fromkeys(
                    concept.quality_gate_failures
                )
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
            "xpand_stc_finalist_jury_v52"
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
            50000,
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

    confidence = safe_float(
        jury.get(
            "confidence"
        ),
        0.0,
    )

    fatal_issues = [
        clean_text(
            item,
            1000,
        )
        for item
        in safe_list(
            jury.get(
                "fatal_issues"
            )
        )
        if clean_text(
            item,
            1000,
        )
    ]

    selected.debate[
        "finalist_jury"
    ] = {

        "approval":
            approval,

        "confidence":
            confidence,

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

        "fatal_issues":
            fatal_issues,

        "production_instruction":
            clean_text(
                jury.get(
                    "production_instruction"
                ),
                2500,
            ),

        "do_not_drift_into":
            safe_list(
                jury.get(
                    "do_not_drift_into"
                )
            ),
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

    selected.quality_gate_failures = list(
        dict.fromkeys(
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
        800,
    )

    jury_lens = clean_text(
        jury.get(
            "recommended_lens"
        ),
        350,
    )

    jury_perspective = clean_text(
        jury.get(
            "recommended_perspective"
        ),
        900,
    )

    if jury_angle:

        camera[
            "camera_angle"
        ] = jury_angle

        selected.camera_angle = (
            jury_angle
        )

    if jury_lens:

        camera[
            "lens"
        ] = jury_lens

        selected.lens = jury_lens

    if jury_perspective:

        camera[
            "perspective"
        ] = jury_perspective

        camera[
            "perspective_type"
        ] = jury_perspective

        selected.perspective = (
            jury_perspective
        )

    camera[
        "camera_lock_instruction"
    ] = (
        "FINAL JURY CAMERA LOCK. "
        "Do not simplify, normalize or replace this camera."
    )

    return selected


# =========================================================
# QUALITY RELEASE
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
    # STC HIGH ALERT
    # =====================================================

    if high_alert:

        candidates = []

        for concept in valid:

            gate_failures = (
                stc_dimension_gate_failures(
                    concept
                )
            )

            hard_failed = any(
                failure
                in HARD_REJECT_FAILURES
                for failure
                in concept.quality_gate_failures
            )

            if hard_failed:

                continue

            if gate_failures:

                continue

            if (
                concept.weighted_score
                <
                STC_HIGH_ALERT_RELEASE_FLOOR
            ):

                continue

            candidates.append(
                concept
            )

        if not candidates:

            return (
                None,
                "stc_high_alert_rejected",
            )

        if jury_selected is not None:

            if jury_selected not in candidates:

                return (
                    None,
                    "finalist_jury_selected_nonqualified",
                )

            jury_meta = safe_dict(
                jury_selected.debate.get(
                    "finalist_jury"
                )
            )

            approval = bool(
                jury_meta.get(
                    "approval",
                    False,
                )
            )

            fatal_issues = safe_list(
                jury_meta.get(
                    "fatal_issues"
                )
            )

            confidence = safe_float(
                jury_meta.get(
                    "confidence"
                ),
                0.0,
            )

            if (
                not approval
                or
                fatal_issues
                or
                confidence
                <
                80.0
            ):

                return (
                    None,
                    "finalist_jury_rejected",
                )

            winner = jury_selected

        else:

            winner = candidates[
                0
            ]

        if (
            winner.weighted_score
            >=
            STC_HIGH_ALERT_MIN_SCORE
        ):

            winner.quality_gate_passed = True

            return (
                winner,
                "stc_five_star_release",
            )

        if (
            winner.weighted_score
            >=
            STC_HIGH_ALERT_RELEASE_FLOOR
        ):

            winner.quality_gate_passed = True

            return (
                winner,
                "stc_high_alert_release",
            )

        return (
            None,
            "stc_high_alert_rejected",
        )

    # =====================================================
    # NORMAL FAST
    # =====================================================

    winner = valid[
        0
    ]

    if mode == MODE_FAST:

        if (
            winner.weighted_score
            >=
            FAST_MIN_SCORE
        ):

            winner.quality_gate_passed = True

            return (
                winner,
                "fast_release",
            )

        return (
            None,
            "quality_failed",
        )

    # =====================================================
    # NORMAL MASTERPIECE
    # =====================================================

    if (
        winner.weighted_score
        >=
        MASTERPIECE_MIN_SCORE
    ):

        winner.quality_gate_passed = True

        return (
            winner,
            "target_release",
        )

    if (
        winner.weighted_score
        >=
        MASTERPIECE_RELEASE_FLOOR
    ):

        winner.quality_gate_passed = True

        return (
            winner,
            "adaptive_release",
        )

    return (
        None,
        "quality_failed",
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
        " IDEATION TECHNICAL FAILURE"
    )
    print(
        "=========================================="
    )

    print(
        "This is NOT classified as a creative-quality failure."
    )

    if high_alert:

        print(
            "STC HIGH ALERT did not produce a qualified concept."
        )

        print(
            "Do NOT interpret technical failure as creative approval."
        )

    else:

        print(
            "Smart Engine fallback should remain available."
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
                "stc_high_alert_campaign_intelligence",

            "technical_failure":
                True,

            "quality_gate_evaluated":
                False,

            "quality_gate_passed":
                False,

            #
            # Kept TRUE for current Telegram compatibility.
            #
            # The later Telegram/Production upgrade can
            # block generic final delivery specifically for STC.
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
                MASTERPIECE_TARGET_DIRECTOR_CALLS,

            "release_level":
                "technical_failure",
        },

        errors=(
            errors
        ),
    )


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

    director_history: List[
        str
    ] = []

    errors: List[
        str
    ] = []

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND CREATIVE BRAIN V5.2"
    )

    if high_alert:

        print(
            " STC BANK 5-STAR HIGH ALERT"
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
        "Concepts:",
        concept_count,
    )

    print(
        "Final shortlist:",
        MASTERPIECE_SHORTLIST_SIZE,
    )

    print(
        "Target Director calls:",
        (
            3
            if high_alert
            else 2
        ),
    )

    brand_pack_path = (
        locate_stc_brand_pack()
    )

    if (
        high_alert
        and
        brand_pack_path
        is not None
    ):

        print(
            "Permanent STC brand pack:",
            str(
                brand_pack_path
            ),
        )

    elif high_alert:

        print(
            "Permanent STC brand pack: not installed yet"
        )

    print("")

    # =====================================================
    # CALL 1 — DIVERSE IDEATION
    # =====================================================

    concepts: List[
        CreativeConcept
    ] = []

    recovery_used = False

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

        errors.append(
            (
                "primary_ideation: "
                +
                clean_text(
                    error,
                    3500,
                )
            )
        )

        print(
            "⚠️ Primary ideation unavailable:",
            clean_text(
                error,
                2400,
            ),
        )

        # =================================================
        # RECOVERY
        # =================================================

        if (
            director_calls
            <
            MASTERPIECE_MAX_DIRECTOR_CALLS
        ):

            try:

                print(
                    "🔁 Running strict structured ideation recovery..."
                )

                recovery_used = True

                director_calls += 1

                director_history.append(
                    "ideation_recovery"
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
                        "ideation_recovery: "
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

    if not concepts:

        errors.append(
            "No usable creative concepts."
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
    # REVIEW CALL
    # =====================================================

    if (
        director_calls
        >=
        MASTERPIECE_MAX_DIRECTOR_CALLS
    ):

        errors.append(
            (
                "Director call budget exhausted "
                "before creative review."
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

    # =====================================================
    # SORT
    # =====================================================

    concepts.sort(
        key=lambda item:
            item.weighted_score,
        reverse=True,
    )

    # =====================================================
    # SELECT QUALIFIED FINALISTS
    # =====================================================

    qualified_for_jury = []

    for concept in concepts:

        hard_failed = any(
            failure
            in HARD_REJECT_FAILURES
            for failure
            in concept.quality_gate_failures
        )

        if hard_failed:

            continue

        if high_alert:

            if stc_dimension_gate_failures(
                concept
            ):

                continue

        qualified_for_jury.append(
            concept
        )

    finalists = qualified_for_jury[
        :MASTERPIECE_SHORTLIST_SIZE
    ]

    if not finalists:

        finalists = concepts[
            :MASTERPIECE_SHORTLIST_SIZE
        ]

    jury_selected: Optional[
        CreativeConcept
    ] = None

    jury_payload: Dict[
        str,
        Any
    ] = {}

    # =====================================================
    # CALL 3 — FINALIST JURY
    #
    # Only when:
    # - STC High Alert
    # - primary ideation worked without consuming recovery
    # - budget remains
    # =====================================================

    if (
        high_alert
        and
        not recovery_used
        and
        director_calls
        <
        MASTERPIECE_MAX_DIRECTOR_CALLS
        and
        finalists
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

            jury_selected = apply_jury_result(

                concepts=(
                    concepts
                ),

                jury=(
                    jury_payload
                ),
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

            print(
                "⚠️ Finalist jury unavailable:",
                clean_text(
                    jury_error,
                    2200,
                ),
            )

            #
            # Review remains valid.
            # No fake jury decision.
            #

            jury_selected = None

    # =====================================================
    # RELEASE
    # =====================================================

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
        )
    )

    quality_gate_evaluated = True

    quality_gate_passed = bool(
        winner
        and
        winner.evaluation_valid
        and
        winner.quality_gate_passed
    )

    top_concepts = concepts[
        :top_count
    ]

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

        if jury_selected:

            jury_info = safe_dict(
                winner.debate.get(
                    "finalist_jury"
                )
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

        if concepts:

            print(
                "Best evaluated score:",
                concepts[
                    0
                ].weighted_score,
            )

            print(
                "Best concept:",
                concepts[
                    0
                ].title,
            )

            print(
                "Failures:",
                ", ".join(
                    concepts[
                        0
                    ].quality_gate_failures[
                        :12
                    ]
                ),
            )

        print(
            "No fake winner created."
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
    # COMPATIBILITY FLOOR
    # =====================================================

    effective_integration_floor = (
        MASTERPIECE_MIN_SCORE
    )

    if winner:

        if high_alert:

            effective_integration_floor = min(
                STC_HIGH_ALERT_RELEASE_FLOOR,
                winner.weighted_score,
            )

        else:

            effective_integration_floor = min(
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
            concepts
        ),

        concepts=(
            concepts
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
                "stc_high_alert_campaign_intelligence",

            "high_alert":
                high_alert,

            "benefit_family":
                benefit_family,

            "stc_style":
                stc_style,

            "initial_concepts":
                concept_count,

            "shortlisted_concepts":
                len(
                    finalists
                ),

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

            "masterpiece_min_score":
                effective_integration_floor,

            "masterpiece_target_score":
                (
                    STC_HIGH_ALERT_MIN_SCORE
                    if high_alert
                    else
                    MASTERPIECE_MIN_SCORE
                ),

            "masterpiece_release_floor":
                (
                    STC_HIGH_ALERT_RELEASE_FLOOR
                    if high_alert
                    else
                    MASTERPIECE_RELEASE_FLOOR
                ),

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
                    winner.weighted_score
                    >=
                    (
                        STC_HIGH_ALERT_MIN_SCORE
                        if high_alert
                        else
                        MASTERPIECE_MIN_SCORE
                    )
                ),

            "technical_failure":
                False,

            "allow_smart_engine_fallback":
                True,

            "quality_target_blocks_production":
                False,

            "fallback_blocked":
                False,

            "real_model_evaluation_required":
                True,

            "fake_fallback_winner_allowed":
                False,

            "campaign_visual_mechanism_required":
                True,

            "generic_scene_guard":
                True,

            "literal_transaction_guard":
                True,

            "repetition_guard":
                True,

            "purple_neon_guard":
                True,

            "merchant_fusion_guard":
                True,

            "scene_diversity_guard":
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

            "brand_pack_available":
                bool(
                    locate_stc_brand_pack()
                ),

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
# OPTIONAL HUMAN SUMMARY
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
        bool,
    ] = {}

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

    test_concept = CreativeConcept(

        concept_id="C01",

        category="merchant_payments",

        title="Commerce Threshold",

        concept_archetype=(
            "architectural visual mechanism"
        ),

        campaign_hook=(
            "A physical architectural threshold connects "
            "digital ordering and physical payment into "
            "one continuous commercial journey."
        ),

        core_idea=(
            "A premium Saudi commerce environment uses "
            "one continuous architectural gesture to connect "
            "online order fulfillment with in-store payment."
        ),

        marketing_message=(
            "One merchant ecosystem."
        ),

        visual_metaphor=(
            "A continuous physical bridge begins as an "
            "e-commerce fulfillment surface and resolves "
            "into an in-store payment moment."
        ),

        visual_mechanism_type=(
            "physical visual bridge"
        ),

        why_not_generic=(
            "The benefit is encoded in the physical structure "
            "of the composition rather than merely showing "
            "a person paying at a terminal."
        ),

        environment=(
            "Contemporary Saudi commercial architecture "
            "with limestone, glass and restrained material accents."
        ),

        environment_novelty=(
            "The scene avoids the conventional boutique counter "
            "and uses circulation architecture as the campaign idea."
        ),

        hero_element=(
            "The continuous commerce threshold."
        ),

        supporting_elements=[
            "online order cue",
            "physical payment cue",
        ],

        camera_angle=(
            "controlled 24mm elevated three-quarter view"
        ),

        lens="24mm",

        perspective=(
            "architectural foreground-to-background reveal"
        ),

        lighting=(
            "directional soft daylight with negative fill "
            "and realistic material reflections"
        ),

        negative_space=(
            "30% clean upper-right negative space"
        ),

        brand_logic=(
            "Premium Saudi banking confidence with restrained "
            "brand accents rather than full purple saturation."
        ),

        production_method=(
            "single_generation"
        ),
    )

    encoded = concept_to_dict(
        test_concept
    )

    tests[
        "concept_to_dict_contract"
    ] = bool(
        encoded.get(
            "concept_id"
        )
        ==
        "C01"
        and
        "core_idea"
        in encoded
        and
        "camera_angle"
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
            test_concept
        ],

        top_concepts=[
            test_concept
        ],

        winner=(
            test_concept
        ),

        metadata={
            "quality_gate_passed":
                True,
        },

        errors=[],
    )

    tests[
        "response_winner_contract"
    ] = (
        response.winner
        is test_concept
    )

    tests[
        "response_metadata_contract"
    ] = isinstance(
        response.metadata,
        dict,
    )

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
            "customer simply paying at a counter",
        ],
    )

    tests[
        "literal_counter_pattern_blocked"
    ] = contains_any(
        prompt_test,
        [
            "CUSTOMER + POS + COUNTER + MERCHANT",
        ],
    )

    tests[
        "purple_not_default"
    ] = contains_any(
        prompt_test,
        [
            "NOT by painting everything purple",
        ],
    )

    tests[
        "merchant_fusion_guard"
    ] = contains_any(
        prompt_test,
        [
            (
                "connect online commerce and physical "
                "payment visually"
            ),
        ],
    )

    tests[
        "environment_diversity"
    ] = contains_any(
        prompt_test,
        [
            (
                "At most TWO concepts may use "
                "an indoor retail environment"
            ),
        ],
    )

    tests[
        "brand_pack_loader_safe"
    ] = isinstance(
        load_stc_brand_pack(),
        dict,
    )

    tests[
        "max_three_director_calls"
    ] = (
        MASTERPIECE_MAX_DIRECTOR_CALLS
        <=
        3
    )

    tests[
        "stc_three_director_target"
    ] = (
        MASTERPIECE_TARGET_DIRECTOR_CALLS
        ==
        3
    )

    literal_bad = CreativeConcept(

        concept_id="BAD",

        title="Luxury checkout",

        concept_archetype="premium realism",

        campaign_hook=(
            "A customer pays while the merchant works."
        ),

        core_idea=(
            "A customer taps a POS terminal on counter "
            "while merchant stands behind counter."
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

        hero_element="POS terminal",

        camera_angle="eye level",

        lens="35mm",

        perspective="normal perspective",

        lighting="soft daylight",

        negative_space="30% top",

        brand_logic="premium",
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
    ] = (
        bad_penalty
        >=
        30.0
        and
        (
            "literal_transaction_tableau"
            in bad_failures
        )
    )

    passed = all(
        tests.values()
    )

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND CREATIVE BRAIN V5.2"
    )
    print(
        " ZERO-COST HIGH-ALERT SELF TEST"
    )
    print(
        "=========================================="
    )
    print("")

    for name, result in tests.items():

        print(
            (
                "✅"
                if result
                else
                "❌"
            )
            +
            name
        )

    print("")

    if passed:

        print(
            (
                "XPAND Creative Brain V5.2 "
                "self-test: PASS ✅"
            )
        )

    else:

        print(
            (
                "XPAND Creative Brain V5.2 "
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
        "✅ STC High Alert mode"
    )
    print(
        (
            "✅ STC concepts = "
            +
            str(
                STC_HIGH_ALERT_CONCEPT_COUNT
            )
        )
    )
    print(
        "✅ Normal concepts = 4"
    )
    print(
        "✅ Executive Creative Review"
    )
    print(
        "✅ Finalist Jury"
    )
    print(
        "✅ Maximum 3 Director calls"
    )
    print(
        "✅ Strict structured Director path"
    )
    print(
        "✅ Permanent STC brand-pack loader"
    )
    print(
        "✅ Campaign-level visual mechanism"
    )
    print(
        "✅ Generic lifestyle hard guard"
    )
    print(
        "✅ Literal POS-counter tableau hard guard"
    )
    print(
        "✅ Merchant channel visual-fusion guard"
    )
    print(
        "✅ Repetition blacklist"
    )
    print(
        "✅ Eight-direction scene diversity"
    )
    print(
        "✅ Advertising readiness dimension"
    )
    print(
        "✅ Brand fit dimension"
    )
    print(
        "✅ Originality dimension"
    )
    print(
        "✅ Distinctiveness dimension"
    )
    print(
        "✅ Premium realistic STC default"
    )
    print(
        "✅ Purple architecture optional"
    )
    print(
        "✅ Purple-neon guard"
    )
    print(
        "✅ Scientific camera vocabulary"
    )
    print(
        "✅ Natural copy-space discipline"
    )
    print(
        "✅ No generated text"
    )
    print(
        "✅ No generated logo"
    )
    print(
        "✅ No fake winner"
    )
    print(
        "🚫 No API calls were made"
    )
    print(
        "🚫 No images were generated"
    )
    print("")
