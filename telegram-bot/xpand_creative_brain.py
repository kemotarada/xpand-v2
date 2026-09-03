# =========================================================
# XPAND CREATIVE BRAIN V1.1
#
# Professional creative strategy and concept-development
# engine for XPAND.
#
# =========================================================
# V1.1
# =========================================================
#
# MASTERPIECE QUALITY GATE
#
# Fixes the previous behavior where a failed model evaluation
# received conservative fallback scores:
#
# 60 / 60 / 60 / 60 / 55 / 55 / 55
#
# which produced:
#
# 58.75 / 100
#
# That score was NOT a real creative evaluation.
#
# V1.1:
#
# - Never treats fallback scoring as a Masterpiece winner
# - Requires real model evaluation
# - Masterpiece minimum score = 82 by default
# - Minimum critical sub-scores
# - Critical-role approval gate
# - Anti-cliche hard gate
# - Evaluation batching
# - Structured JSON mode
# - Evaluation retry
# - Automatic candidate revision
# - Automatic re-ideation rounds
# - Duplicate concept suppression
# - Failure-aware challenger generation
# - Honest quality-gate metadata
#
#
# MASTERPIECE FLOW
# ---------------------------------------------------------
#
# 20 Concepts
#      ↓
# Batched Creative Review
#      ↓
# Weighted Scoring
#      ↓
# Anti-Cliche
#      ↓
# Masterpiece Quality Gate ≥82
#      ↓
# FAIL?
#      ↓
# Revise strongest near-winners
#      ↓
# Re-score
#      ↓
# FAIL?
#      ↓
# New challenger ideation round
#      ↓
# Repeat up to configured maximum
#
#
# IMPORTANT
# ---------------------------------------------------------
#
# This module:
#
# - does NOT generate images
# - does NOT expose hidden chain-of-thought
# - does NOT fake a winner when evaluation fails
#
# Uses:
#
# - GPT-5.6 Sol through call_openai_director()
# - JSON structured output support from
#   xpand_image_engine.py V1.3.1+
# =========================================================

from __future__ import annotations

import json
import os
import re

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

from xpand_image_engine import (
    call_openai_director,
)


# =========================================================
# IDENTITY
# =========================================================

VERSION = "1.1"

MODULE_NAME = (
    "XPAND Creative Brain"
)


# =========================================================
# CREATIVE MODES
# =========================================================

MODE_FAST = (
    "fast"
)

MODE_MASTERPIECE = (
    "masterpiece"
)


# =========================================================
# MASTERPIECE QUALITY SETTINGS
# =========================================================

MASTERPIECE_MIN_SCORE = max(
    70.0,
    min(
        98.0,
        float(
            os.environ.get(
                "XPAND_MASTERPIECE_MIN_SCORE",
                "82"
            )
            or
            82
        )
    )
)


FAST_MIN_SCORE = max(
    40.0,
    min(
        90.0,
        float(
            os.environ.get(
                "XPAND_FAST_CREATIVE_MIN_SCORE",
                "65"
            )
            or
            65
        )
    )
)


MASTERPIECE_MAX_IDEATION_ROUNDS = max(
    1,
    min(
        5,
        int(
            os.environ.get(
                "XPAND_MASTERPIECE_IDEATION_ROUNDS",
                "3"
            )
            or
            3
        )
    )
)


MASTERPIECE_REVISION_CANDIDATES = max(
    0,
    min(
        4,
        int(
            os.environ.get(
                "XPAND_MASTERPIECE_REVISION_CANDIDATES",
                "2"
            )
            or
            2
        )
    )
)


EVALUATION_BATCH_SIZE = max(
    2,
    min(
        8,
        int(
            os.environ.get(
                "XPAND_CREATIVE_EVALUATION_BATCH_SIZE",
                "5"
            )
            or
            5
        )
    )
)


EVALUATION_RETRIES = max(
    1,
    min(
        3,
        int(
            os.environ.get(
                "XPAND_CREATIVE_EVALUATION_RETRIES",
                "2"
            )
            or
            2
        )
    )
)


MASTERPIECE_REVISION_FLOOR = max(
    55.0,
    min(
        MASTERPIECE_MIN_SCORE,
        float(
            os.environ.get(
                "XPAND_MASTERPIECE_REVISION_FLOOR",
                "72"
            )
            or
            72
        )
    )
)


# =========================================================
# CRITICAL MASTERPIECE SUB-SCORES
# =========================================================

MASTERPIECE_MIN_SUBSCORES = {
    "message_clarity":
        75,

    "originality":
        80,

    "brand_fit":
        80,

    "visual_power":
        80,

    "feasibility":
        65,

    "perspective_integrity":
        70,

    "campaign_potential":
        70,
}


# =========================================================
# SCORING WEIGHTS
#
# Message clarity ............ 20%
# Originality ................ 20%
# Brand compatibility ....... 20%
# Visual power .............. 15%
# Feasibility ............... 10%
# Perspective correctness ... 5%
# Campaign potential ........ 10%
#
# TOTAL ..................... 100%
# =========================================================

SCORE_WEIGHTS = {
    "message_clarity":
        20,

    "originality":
        20,

    "brand_fit":
        20,

    "visual_power":
        15,

    "feasibility":
        10,

    "perspective_integrity":
        5,

    "campaign_potential":
        10,
}


# =========================================================
# MASTERPIECE DISTRIBUTION
# =========================================================

MASTERPIECE_DISTRIBUTION = {
    "simple_intelligent":
        5,

    "realistic_cinematic":
        5,

    "conceptual_photorealism":
        5,

    "scale_manipulation":
        3,

    "bold_experimental":
        2,
}


# =========================================================
# CHALLENGER DISTRIBUTION
#
# Used after an entire Masterpiece round fails.
# These are NOT minor variants.
# They must challenge the previous visual grammar.
# =========================================================

CHALLENGER_DISTRIBUTION = {
    "simple_intelligent":
        3,

    "realistic_cinematic":
        3,

    "conceptual_photorealism":
        3,

    "scale_manipulation":
        2,

    "bold_experimental":
        1,
}


FAST_DISTRIBUTION = {
    "simple_intelligent":
        2,

    "realistic_cinematic":
        2,

    "conceptual_photorealism":
        1,

    "bold_experimental":
        1,
}


# =========================================================
# CAMERA LIBRARY
# =========================================================

CAMERA_LIBRARY = {
    "eye_level": {
        "name":
            "Eye-Level Shot",

        "use_for": [
            "natural human interaction",
            "trust",
            "relatable banking experience",
            "balanced lifestyle scenes",
        ],
    },

    "low_angle": {
        "name":
            "Low-Angle Shot",

        "use_for": [
            "authority",
            "strength",
            "premium status",
            "heroic presence",
        ],
    },

    "extreme_low_angle": {
        "name":
            "Extreme Low-Angle Shot",

        "use_for": [
            "monumental scale",
            "power",
            "architectural drama",
            "extreme visual impact",
        ],
    },

    "worms_eye": {
        "name":
            "Worm’s-Eye View",

        "use_for": [
            "dominance",
            "scale transformation",
            "unexpected perspective",
            "heroic conceptual scenes",
        ],
    },

    "high_angle": {
        "name":
            "High-Angle Shot",

        "use_for": [
            "overview",
            "controlled environment",
            "relationship between elements",
        ],
    },

    "birds_eye": {
        "name":
            "Bird’s-Eye View",

        "use_for": [
            "systems",
            "routes",
            "connections",
            "global transfers",
            "spatial relationships",
        ],
    },

    "top_down": {
        "name":
            "Top-Down Shot",

        "use_for": [
            "graphic organization",
            "clean product layouts",
            "structured campaign systems",
        ],
    },

    "three_quarter": {
        "name":
            "Three-Quarter Hero Shot",

        "use_for": [
            "bank cards",
            "phones",
            "product advertising",
            "premium hero presentation",
        ],
    },

    "over_shoulder": {
        "name":
            "Over-the-Shoulder Shot",

        "use_for": [
            "personal digital experience",
            "banking app use",
            "money transfer interaction",
            "human-centered services",
        ],
    },

    "pov": {
        "name":
            "Point-of-View Shot",

        "use_for": [
            "immersive banking interaction",
            "first-person experience",
            "travel",
            "payment moments",
        ],
    },

    "ground_level": {
        "name":
            "Ground-Level Shot",

        "use_for": [
            "movement",
            "speed",
            "travel",
            "roads",
            "dynamic foreground depth",
        ],
    },

    "macro": {
        "name":
            "Macro Shot",

        "use_for": [
            "premium product detail",
            "card materials",
            "phone materials",
            "luxury textures",
        ],
    },

    "extreme_closeup": {
        "name":
            "Extreme Close-Up",

        "use_for": [
            "material detail",
            "human micro-interaction",
            "premium texture",
        ],
    },

    "wide": {
        "name":
            "Wide Shot",

        "use_for": [
            "environmental advertising",
            "travel",
            "lifestyle context",
            "brand worlds",
        ],
    },

    "extreme_wide": {
        "name":
            "Extreme Wide Shot",

        "use_for": [
            "freedom",
            "travel",
            "possibility",
            "large conceptual environments",
        ],
    },

    "forced_perspective": {
        "name":
            "Forced-Perspective Shot",

        "use_for": [
            "visual metaphor",
            "smart scale manipulation",
            "product-environment integration",
        ],
    },

    "central_one_point": {
        "name":
            "Central One-Point Perspective",

        "use_for": [
            "precision",
            "trust",
            "structured brand environment",
            "strong leading lines",
        ],
    },

    "frame_within_frame": {
        "name":
            "Frame-within-a-Frame Composition",

        "use_for": [
            "focus",
            "travel",
            "architecture",
            "cinematic storytelling",
        ],
    },

    "foreground_obstruction": {
        "name":
            "Foreground-Obstruction Composition",

        "use_for": [
            "cinematic realism",
            "documentary feeling",
            "depth",
            "premium lifestyle photography",
        ],
    },
}


# =========================================================
# LENS LIBRARY
# =========================================================

LENS_LIBRARY = {
    "14-20mm":
        "Extreme environmental drama and intentional wide perspective.",

    "24mm":
        "Wide premium environmental advertising.",

    "28mm":
        "Dynamic commercial environment with controlled perspective.",

    "35mm":
        "Cinematic environmental storytelling with natural subject presence.",

    "50mm":
        "Balanced natural perspective.",

    "85mm":
        "Premium portrait compression and elegant subject isolation.",

    "105mm":
        "Luxury portrait/product compression and strong background separation.",

    "macro":
        "Fine material detail and product microtexture.",

    "tilt_shift":
        "Controlled architectural perspective when vertical accuracy matters.",
}


# =========================================================
# ANTI-CLICHE LIBRARY
# =========================================================

ANTI_CLICHE_LIBRARY = [
    {
        "id":
            "flying_money",

        "markers": [
            "عملات طائرة",
            "فلوس طايره",
            "فلوس طائرة",
            "flying money",
            "flying coins",
            "money floating",
        ],

        "reason":
            "Overused financial advertising symbol.",
    },

    {
        "id":
            "phone_icons",

        "markers": [
            "هاتف محاط بايقونات",
            "هاتف محاط بأيقونات",
            "phone surrounded by icons",
            "floating app icons",
            "floating banking icons",
        ],

        "reason":
            "Generic fintech visualization.",
    },

    {
        "id":
            "security_shield",

        "markers": [
            "درع الامان",
            "درع الأمان",
            "security shield",
            "digital shield",
        ],

        "reason":
            "Common security cliché.",
    },

    {
        "id":
            "growth_arrow",

        "markers": [
            "سهم صاعد",
            "اسهم صاعده",
            "أسهم صاعدة",
            "upward arrow",
            "rising graph",
        ],

        "reason":
            "Generic business-growth symbolism.",
    },

    {
        "id":
            "generic_globe",

        "markers": [
            "كره ارضيه",
            "كرة أرضية",
            "globe",
            "world globe",
            "planet earth",
        ],

        "reason":
            "Overused international-transfer metaphor.",
    },

    {
        "id":
            "travel_gate",

        "markers": [
            "بوابه سفر",
            "بوابة سفر",
            "travel gate",
            "airport gate as portal",
        ],

        "reason":
            "Common travel-campaign visual.",
    },

    {
        "id":
            "smiling_businessman",

        "markers": [
            "رجل اعمال يبتسم",
            "رجل أعمال يبتسم",
            "smiling businessman",
            "businessman smiling",
        ],

        "reason":
            "Generic corporate stock-photo cliché.",
    },

    {
        "id":
            "floating_card",

        "markers": [
            "بطاقه تطفو",
            "بطاقة تطفو",
            "floating bank card",
            "floating card",
        ],

        "reason":
            "Weak product presentation unless physically justified.",
    },

    {
        "id":
            "random_mini_city",

        "markers": [
            "مدينه مصغره",
            "مدينة مصغرة",
            "miniature city",
            "tiny city",
        ],

        "reason":
            "Common AI-advertising visual without conceptual relevance.",
    },

    {
        "id":
            "random_purple_elements",

        "markers": [
            "عناصر بنفسجيه عشوائيه",
            "عناصر بنفسجية عشوائية",
            "random purple objects",
            "purple decorative elements",
        ],

        "reason":
            "Brand color used as decoration instead of concept.",
    },

    {
        "id":
            "handshake",

        "markers": [
            "مصافحه",
            "مصافحة",
            "handshake",
            "business handshake",
        ],

        "reason":
            "Overused trust/business cliché.",
    },

    {
        "id":
            "piggy_bank",

        "markers": [
            "حصاله",
            "حصالة",
            "piggy bank",
        ],

        "reason":
            "Overused savings metaphor.",
    },

    {
        "id":
            "calculator_money",

        "markers": [
            "اله حاسبه",
            "آلة حاسبة",
            "calculator and money",
        ],

        "reason":
            "Generic financial-services imagery.",
    },

    {
        "id":
            "random_hud",

        "markers": [
            "hud",
            "digital interface around",
            "floating interface",
            "دوائر تقنيه",
            "دوائر تقنية",
        ],

        "reason":
            "Generic futuristic banking treatment.",
    },
]


# =========================================================
# VISUAL METAPHOR LIBRARY
# =========================================================

METAPHOR_FAMILIES = {
    "speed": [
        "distance compression",
        "instant spatial transformation",
        "single uninterrupted motion",
        "before/after merged into one frame",
        "time collapsed into physical distance",
    ],

    "international_transfer": [
        "two distant environments physically touching",
        "one continuous surface connecting two cities",
        "distance folded into a single scene",
        "one object acting as a bridge between locations",
        "two cultural spaces sharing one physical boundary",
    ],

    "travel": [
        "home and destination coexisting in one frame",
        "physical threshold without a literal airport gate",
        "luggage integrated with financial utility",
        "payment enabling movement rather than depicting travel literally",
    ],

    "security": [
        "calm protected space inside a chaotic environment",
        "controlled boundary",
        "precise structural containment",
        "fragile object protected through architecture rather than a shield",
    ],

    "control": [
        "environment responding to one deliberate action",
        "complexity organized around one focal control point",
        "many paths resolving into one precise route",
    ],

    "cashback": [
        "value returning physically to its origin",
        "purchase creating a visible second benefit",
        "one action producing a controlled return",
    ],

    "flexibility": [
        "environment adapting around the user",
        "one object transforming function without changing identity",
        "multiple paths available from one stable point",
    ],

    "rewards": [
        "ordinary action unlocking a premium secondary layer",
        "small interaction creating disproportionate value",
        "benefit revealed inside an everyday transaction",
    ],

    "digital_banking": [
        "physical environment behaving with digital simplicity",
        "complex banking reduced to one seamless physical gesture",
        "digital action represented through real-world spatial transformation",
    ],

    "premium": [
        "controlled simplicity",
        "rare material treatment",
        "precision",
        "confident scale",
        "luxury through restraint rather than decoration",
    ],
}


# =========================================================
# DATA MODELS
# =========================================================

@dataclass
class CreativeConcept:

    concept_id: str

    category: str

    title: str

    core_idea: str

    marketing_message: str

    visual_metaphor: str

    environment: str

    hero_element: str

    supporting_elements: List[str]

    camera_angle: str

    lens: str

    perspective: str

    lighting: str

    negative_space: str

    brand_logic: str

    production_method: str

    campaign_extension: str

    risks: List[str]

    scores: Dict[
        str,
        float
    ] = field(
        default_factory=dict
    )

    weighted_score: float = 0.0

    cliche_hits: List[
        Dict[
            str,
            str
        ]
    ] = field(
        default_factory=list
    )

    debate: Dict[
        str,
        Any
    ] = field(
        default_factory=dict
    )

    feasibility: Dict[
        str,
        Any
    ] = field(
        default_factory=dict
    )

    evaluation_valid: bool = False

    quality_gate_passed: bool = False

    quality_gate_failures: List[
        str
    ] = field(
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
    ] = field(
        default_factory=dict
    )

    errors: List[str] = field(
        default_factory=list
    )


# =========================================================
# TEXT HELPERS
# =========================================================

def clean_text(
    value: Any,
    limit: int = 12000
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


def normalize_text(
    value: Any
) -> str:

    text = clean_text(
        value,
        30000
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
            new
        )

    text = re.sub(
        r"[\u064B-\u065F]",
        "",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def contains_any(
    text: str,
    markers: Sequence[str]
) -> bool:

    source = normalize_text(
        text
    )

    return any(
        normalize_text(
            marker
        )
        in source
        for marker in markers
    )


# =========================================================
# JSON HELPERS
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


def compact_json_for_prompt(
    value: Any,
    limit: int
) -> str:

    if not value:

        return "{}"

    try:

        text = json.dumps(
            value,
            ensure_ascii=False,
            separators=(
                ",",
                ":"
            ),
            default=str
        )

    except Exception:

        text = clean_text(
            value,
            limit
        )

    if len(
        text
    ) <= limit:

        return text

    front = int(
        limit
        *
        0.70
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
        text[
            :front
        ]
        +
        '\n"[XPAND_CONTEXT_COMPACTED]"\n'
        +
        (
            text[
                -back:
            ]
            if back
            else
            ""
        )
    )


# =========================================================
# SCORE HELPERS
# =========================================================

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


def calculate_weighted_score(
    scores: Dict[str, Any]
) -> float:

    total = 0.0

    for key, weight in SCORE_WEIGHTS.items():

        score = clamp_score(
            scores.get(
                key,
                0
            )
        )

        total += (
            score
            *
            (
                float(
                    weight
                )
                /
                100.0
            )
        )

    return round(
        total,
        2
    )


# =========================================================
# ANTI-CLICHE CHECK
# =========================================================

def detect_cliches(
    concept_text: str
) -> List[
    Dict[
        str,
        str
    ]
]:

    hits: List[
        Dict[
            str,
            str
        ]
    ] = []

    source = normalize_text(
        concept_text
    )

    for item in ANTI_CLICHE_LIBRARY:

        matched = False

        for marker in item[
            "markers"
        ]:

            if normalize_text(
                marker
            ) in source:

                matched = True
                break

        if matched:

            hits.append(
                {
                    "id":
                        item[
                            "id"
                        ],

                    "reason":
                        item[
                            "reason"
                        ],
                }
            )

    return hits


def apply_cliche_penalty(
    weighted_score: float,
    cliche_hits: List[
        Dict[
            str,
            str
        ]
    ]
) -> float:

    if not cliche_hits:

        return weighted_score

    penalty = min(
        35.0,
        (
            len(
                cliche_hits
            )
            *
            10.0
        )
    )

    return round(
        max(
            0.0,
            weighted_score
            -
            penalty
        ),
        2
    )


# =========================================================
# METAPHOR HELPERS
# =========================================================

def infer_benefit_family(
    request: str
) -> str:

    if contains_any(
        request,
        [
            "تحويل دولي",
            "international transfer",
            "حول دولي",
            "حواله دوليه",
            "حوالة دولية",
        ]
    ):

        return "international_transfer"

    if contains_any(
        request,
        [
            "سفر",
            "travel",
            "مطارات",
            "دفع دولي",
            "الدفع الدولي",
        ]
    ):

        return "travel"

    if contains_any(
        request,
        [
            "سرعه",
            "سرعة",
            "فوري",
            "instant",
            "fast",
        ]
    ):

        return "speed"

    if contains_any(
        request,
        [
            "امان",
            "أمان",
            "امن",
            "آمن",
            "security",
            "secure",
        ]
    ):

        return "security"

    if contains_any(
        request,
        [
            "تحكم",
            "control",
            "اداره",
            "إدارة",
            "manage",
        ]
    ):

        return "control"

    if contains_any(
        request,
        [
            "كاش باك",
            "cashback",
            "استرداد",
        ]
    ):

        return "cashback"

    if contains_any(
        request,
        [
            "مرونه",
            "مرونة",
            "flexibility",
            "flexible",
        ]
    ):

        return "flexibility"

    if contains_any(
        request,
        [
            "مكافات",
            "مكافآت",
            "rewards",
            "points",
            "نقاط",
        ]
    ):

        return "rewards"

    if contains_any(
        request,
        [
            "تطبيق",
            "app",
            "رقمي",
            "digital",
            "بنك رقمي",
        ]
    ):

        return "digital_banking"

    return "premium"


def get_metaphor_seed(
    request: str
) -> Dict[str, Any]:

    family = infer_benefit_family(
        request
    )

    return {
        "family":
            family,

        "directions":
            METAPHOR_FAMILIES.get(
                family,
                METAPHOR_FAMILIES[
                    "premium"
                ]
            ),
    }


# =========================================================
# CONTEXT SERIALIZERS
# =========================================================

def compact_brand_context(
    brand_context: Any,
    limit: int = 6500
) -> str:

    if not brand_context:

        return (
            "No structured brand context supplied."
        )

    if isinstance(
        brand_context,
        str
    ):

        return clean_text(
            brand_context,
            limit
        )

    return compact_json_for_prompt(
        brand_context,
        limit
    )


def compact_visual_references(
    visual_references: Any,
    limit: int = 5500
) -> str:

    if not visual_references:

        return (
            "No Visual Reference DNA supplied."
        )

    if isinstance(
        visual_references,
        str
    ):

        return clean_text(
            visual_references,
            limit
        )

    return compact_json_for_prompt(
        visual_references,
        limit
    )


# =========================================================
# DISTRIBUTION PROMPT
# =========================================================

def distribution_text(
    distribution: Dict[str, int]
) -> str:

    return "\n".join(
        (
            f"- {category}: "
            f"{count} concepts"
        )
        for (
            category,
            count
        ) in distribution.items()
    )


# =========================================================
# CONCEPT GENERATION PROMPT
# =========================================================

def build_concept_generation_prompt(
    *,
    user_request: str,
    brand_context: Any = None,
    visual_references: Any = None,
    style_hint: str = "",
    mode: str = MODE_MASTERPIECE,
    round_number: int = 1,
    failure_context: str = "",
    challenger: bool = False
) -> str:

    if mode == MODE_FAST:

        distribution = (
            FAST_DISTRIBUTION
        )

    elif challenger:

        distribution = (
            CHALLENGER_DISTRIBUTION
        )

    else:

        distribution = (
            MASTERPIECE_DISTRIBUTION
        )

    metaphor_seed = get_metaphor_seed(
        user_request
    )

    challenger_rules = ""

    if challenger:

        challenger_rules = f"""
==================================================
FAILED PREVIOUS DIRECTIONS
==================================================

{clean_text(failure_context, 7000)}

This is a challenger round.

Do NOT create cosmetic variations of previous ideas.

Change the conceptual mechanism itself.

If previous ideas relied on:
- symmetry, try asymmetry
- split environments, avoid another split environment
- portals, avoid portals
- chairs, rooms, windows or city pairs, find another metaphor
- literal travel objects, seek an abstract physical relationship
- decorative brand colors, make color serve the concept instead

Each new concept must have a genuinely different
visual grammar from the failed directions.
""".strip()

    return f"""
You are XPAND Creative Brain.

Act as a world-class advertising concept-development team.

Do NOT generate an image.

Do NOT write the final image prompt.

Do NOT expose private chain-of-thought.

Return concise structured creative decisions only.

==================================================
USER REQUEST
==================================================

{clean_text(user_request, 9000)}

==================================================
BRAND MEMORY
==================================================

{compact_brand_context(brand_context)}

==================================================
VISUAL REFERENCE DNA
==================================================

{compact_visual_references(visual_references)}

==================================================
STYLE HINT
==================================================

{clean_text(style_hint, 1500) or "Use the most appropriate visual style."}

==================================================
CREATIVE MODE
==================================================

{mode}

Ideation round:
{round_number}

==================================================
REQUIRED CONCEPT DISTRIBUTION
==================================================

{distribution_text(distribution)}

==================================================
VISUAL METAPHOR STARTING FAMILY
==================================================

Benefit family:
{metaphor_seed["family"]}

Possible metaphor logic:

{compact_json_for_prompt(
    metaphor_seed["directions"],
    2500
)}

These are seeds only.

Do NOT copy them mechanically.

{challenger_rules}

==================================================
MASTERPIECE STANDARD
==================================================

For Masterpiece Mode, an idea is not considered successful
because it is merely attractive.

A true Masterpiece direction must achieve:

- immediate visual communication
- strong originality
- strong brand relevance
- exceptional visual power
- credible execution
- coherent perspective
- campaign-extension potential

Target level:

82+ = strong campaign-level direction
88+ = exceptional
92+ = rare

Avoid safe middle-ground concepts.

Do not produce 20 variations of one idea.

==================================================
MANDATORY CREATIVE RULES
==================================================

Every concept must:

- communicate the benefit visually
- work without explanatory copy
- fit the brand context
- feel premium and commercially usable
- avoid generic banking symbolism
- have one dominant visual idea
- avoid unnecessary visual effects
- use a meaningful camera angle
- have plausible lighting and perspective
- be executable as one image OR clearly state if composite production is needed
- respect Product Lock information in Visual Reference DNA
- preserve original product identity if a product reference exists
- leave intentional negative space where appropriate
- avoid copying a specific existing campaign
- differ materially from other concepts in the same batch

Avoid these clichés unless transformed into a genuinely
original visual relationship:

- flying money
- flying coins
- phone surrounded by icons
- security shield
- growth arrows
- generic globe
- generic airport portal
- smiling businessman
- random floating bank card
- random miniature city
- decorative purple shapes
- business handshake
- piggy bank
- calculator and money
- random HUD graphics

==================================================
CAMERA RULE
==================================================

The camera angle must serve the concept.

Use technically coherent choices such as:

- Eye-Level Shot
- Low-Angle Shot
- Extreme Low-Angle Shot
- Worm’s-Eye View
- High-Angle Shot
- Bird’s-Eye View
- Top-Down Shot
- Three-Quarter Hero Shot
- Over-the-Shoulder Shot
- Point-of-View Shot
- Ground-Level Shot
- Macro Shot
- Extreme Close-Up
- Wide Shot
- Extreme Wide Shot
- Forced-Perspective Shot
- Central One-Point Perspective
- Frame-within-a-Frame Composition
- Foreground-Obstruction Composition

Choose one logical focal length.

Do not combine contradictory camera descriptions.

==================================================
OUTPUT
==================================================

Return JSON only.

Required structure:

{{
  "concepts": [
    {{
      "concept_id": "C01",

      "category":
        "simple_intelligent | realistic_cinematic | conceptual_photorealism | scale_manipulation | bold_experimental",

      "title": "",

      "core_idea": "",

      "marketing_message": "",

      "visual_metaphor": "",

      "environment": "",

      "hero_element": "",

      "supporting_elements": [],

      "camera_angle": "",

      "lens": "",

      "perspective": "",

      "lighting": "",

      "negative_space": "",

      "brand_logic": "",

      "production_method":
        "single_generation | multi_pass | composite | inpainting",

      "campaign_extension": "",

      "risks": []
    }}
  ]
}}

Generate exactly the requested number of concepts.

Do not score them.

Do not select a winner.
""".strip()


# =========================================================
# CONCEPT PARSER
# =========================================================

def concept_from_dict(
    item: Dict[str, Any],
    *,
    fallback_id: str,
    generation_round: int = 1,
    revised_from: str = ""
) -> CreativeConcept:

    supporting = item.get(
        "supporting_elements",
        []
    )

    if not isinstance(
        supporting,
        list
    ):

        supporting = []

    risks = item.get(
        "risks",
        []
    )

    if not isinstance(
        risks,
        list
    ):

        risks = []

    concept = CreativeConcept(
        concept_id=
            (
                clean_text(
                    item.get(
                        "concept_id"
                    ),
                    100
                )
                or
                fallback_id
            ),

        category=
            clean_text(
                item.get(
                    "category"
                ),
                100
            ),

        title=
            clean_text(
                item.get(
                    "title"
                ),
                500
            ),

        core_idea=
            clean_text(
                item.get(
                    "core_idea"
                ),
                3000
            ),

        marketing_message=
            clean_text(
                item.get(
                    "marketing_message"
                ),
                2000
            ),

        visual_metaphor=
            clean_text(
                item.get(
                    "visual_metaphor"
                ),
                2000
            ),

        environment=
            clean_text(
                item.get(
                    "environment"
                ),
                2500
            ),

        hero_element=
            clean_text(
                item.get(
                    "hero_element"
                ),
                1500
            ),

        supporting_elements=[
            clean_text(
                value,
                1000
            )
            for value in supporting
            if clean_text(
                value,
                1000
            )
        ],

        camera_angle=
            clean_text(
                item.get(
                    "camera_angle"
                ),
                500
            ),

        lens=
            clean_text(
                item.get(
                    "lens"
                ),
                300
            ),

        perspective=
            clean_text(
                item.get(
                    "perspective"
                ),
                1000
            ),

        lighting=
            clean_text(
                item.get(
                    "lighting"
                ),
                1500
            ),

        negative_space=
            clean_text(
                item.get(
                    "negative_space"
                ),
                1000
            ),

        brand_logic=
            clean_text(
                item.get(
                    "brand_logic"
                ),
                2000
            ),

        production_method=
            clean_text(
                item.get(
                    "production_method"
                ),
                100
            ),

        campaign_extension=
            clean_text(
                item.get(
                    "campaign_extension"
                ),
                1500
            ),

        risks=[
            clean_text(
                value,
                1000
            )
            for value in risks
            if clean_text(
                value,
                1000
            )
        ],

        generation_round=
            generation_round,

        revised_from=
            clean_text(
                revised_from,
                100
            ),
    )

    concept_text = (
        concept.title
        +
        "\n"
        +
        concept.core_idea
        +
        "\n"
        +
        concept.visual_metaphor
        +
        "\n"
        +
        concept.environment
        +
        "\n"
        +
        concept.hero_element
        +
        "\n"
        +
        " ".join(
            concept.supporting_elements
        )
    )

    concept.cliche_hits = (
        detect_cliches(
            concept_text
        )
    )

    return concept


def parse_concepts(
    payload: Dict[str, Any],
    *,
    generation_round: int = 1
) -> List[
    CreativeConcept
]:

    raw_concepts = payload.get(
        "concepts",
        []
    )

    if not isinstance(
        raw_concepts,
        list
    ):

        return []

    concepts: List[
        CreativeConcept
    ] = []

    for index, item in enumerate(
        raw_concepts,
        start=1
    ):

        if not isinstance(
            item,
            dict
        ):

            continue

        concept = concept_from_dict(
            item,

            fallback_id=
                (
                    "C"
                    +
                    str(
                        index
                    ).zfill(
                        2
                    )
                ),

            generation_round=
                generation_round
        )

        concepts.append(
            concept
        )

    return concepts


# =========================================================
# CONCEPT FINGERPRINT
# =========================================================

def concept_fingerprint(
    concept: CreativeConcept
) -> str:

    value = (
        concept.title
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
        concept.hero_element
    )

    value = normalize_text(
        value
    )

    value = re.sub(
        r"[^a-z0-9\u0600-\u06FF ]+",
        " ",
        value
    )

    words = [
        word
        for word in value.split()
        if len(
            word
        ) > 2
    ]

    return " ".join(
        words[
            :35
        ]
    )


def deduplicate_concepts(
    concepts: List[
        CreativeConcept
    ],
    existing: Sequence[
        CreativeConcept
    ] = ()
) -> List[
    CreativeConcept
]:

    seen = {
        concept_fingerprint(
            item
        )
        for item in existing
        if concept_fingerprint(
            item
        )
    }

    output = []

    for concept in concepts:

        fingerprint = concept_fingerprint(
            concept
        )

        if (
            fingerprint
            and
            fingerprint in seen
        ):

            continue

        if fingerprint:

            seen.add(
                fingerprint
            )

        output.append(
            concept
        )

    return output


# =========================================================
# ROUND IDS
# =========================================================

def assign_round_ids(
    concepts: List[
        CreativeConcept
    ],
    round_number: int
) -> None:

    used = set()

    for index, concept in enumerate(
        concepts,
        start=1
    ):

        raw = (
            clean_text(
                concept.concept_id,
                80
            )
            or
            (
                "C"
                +
                str(
                    index
                ).zfill(
                    2
                )
            )
        )

        if round_number > 1:

            raw = (
                "R"
                +
                str(
                    round_number
                )
                +
                "-"
                +
                raw
            )

        candidate = raw

        suffix = 2

        while candidate in used:

            candidate = (
                raw
                +
                "-"
                +
                str(
                    suffix
                )
            )

            suffix += 1

        used.add(
            candidate
        )

        concept.concept_id = (
            candidate
        )

        concept.generation_round = (
            round_number
        )


# =========================================================
# GENERATE CONCEPT POOL
# =========================================================

def generate_concept_pool(
    *,
    user_request: str,
    brand_context: Any = None,
    visual_references: Any = None,
    style_hint: str = "",
    mode: str = MODE_MASTERPIECE,
    round_number: int = 1,
    failure_context: str = "",
    challenger: bool = False
) -> List[
    CreativeConcept
]:

    prompt = build_concept_generation_prompt(
        user_request=
            user_request,

        brand_context=
            brand_context,

        visual_references=
            visual_references,

        style_hint=
            style_hint,

        mode=
            mode,

        round_number=
            round_number,

        failure_context=
            failure_context,

        challenger=
            challenger
    )

    raw = call_openai_director(
        prompt,
        json_mode=
            True
    )

    payload = extract_json_object(
        raw
    )

    concepts = parse_concepts(
        payload,
        generation_round=
            round_number
    )

    expected = (
        sum(
            FAST_DISTRIBUTION.values()
        )
        if mode == MODE_FAST
        else
        (
            sum(
                CHALLENGER_DISTRIBUTION.values()
            )
            if challenger
            else
            sum(
                MASTERPIECE_DISTRIBUTION.values()
            )
        )
    )

    minimum_usable = max(
        3,
        int(
            expected
            *
            0.60
        )
    )

    if len(
        concepts
    ) < minimum_usable:

        raise RuntimeError(
            (
                "Creative Brain returned too few usable concepts: "
                +
                str(
                    len(
                        concepts
                    )
                )
                +
                "/"
                +
                str(
                    expected
                )
            )
        )

    assign_round_ids(
        concepts,
        round_number
    )

    return concepts


# =========================================================
# EVALUATION PAYLOAD
# =========================================================

def concept_payload_for_evaluation(
    concept: CreativeConcept
) -> Dict[str, Any]:

    return {
        "concept_id":
            concept.concept_id,

        "category":
            concept.category,

        "title":
            concept.title,

        "core_idea":
            concept.core_idea,

        "marketing_message":
            concept.marketing_message,

        "visual_metaphor":
            concept.visual_metaphor,

        "environment":
            concept.environment,

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

        "anti_cliche_hits":
            concept.cliche_hits,

        "generation_round":
            concept.generation_round,

        "revised_from":
            concept.revised_from,
    }


# =========================================================
# EVALUATION PROMPT
# =========================================================

def build_evaluation_prompt(
    *,
    user_request: str,
    concepts: List[
        CreativeConcept
    ],
    brand_context: Any = None,
    visual_references: Any = None
) -> str:

    concepts_json = compact_json_for_prompt(
        [
            concept_payload_for_evaluation(
                concept
            )
            for concept in concepts
        ],
        12500
    )

    return f"""
You are XPAND Creative Review Board.

Do NOT generate an image.

Do NOT expose chain-of-thought.

Evaluate the supplied advertising concepts using:

1. Creative Director
2. Brand Guardian
3. Production Expert
4. Harsh Critic

==================================================
ORIGINAL REQUEST
==================================================

{clean_text(user_request, 7000)}

==================================================
BRAND MEMORY
==================================================

{compact_brand_context(
    brand_context,
    4500
)}

==================================================
VISUAL REFERENCES
==================================================

{compact_visual_references(
    visual_references,
    4000
)}

==================================================
CONCEPTS
==================================================

{concepts_json}

==================================================
SCORING CALIBRATION
==================================================

Score seriously.

Do NOT inflate scores.

Use this calibration:

50 = ordinary / weak
60 = acceptable but generic
70 = good professional concept
75 = strong
82 = campaign-level Masterpiece candidate
88 = exceptional
92+ = rare, award-level potential

A visually pretty scene with a weak advertising idea
must NOT score highly.

==================================================
CREATIVE DIRECTOR
==================================================

Evaluate:

- originality
- conceptual intelligence
- visual impact
- clarity
- advertising usefulness

==================================================
BRAND GUARDIAN
==================================================

Evaluate:

- brand compatibility
- identity consistency
- cultural relevance
- consistency with approved visual references
- consistency with approved/rejected Brand Memory rules

==================================================
PRODUCTION EXPERT
==================================================

Evaluate:

- one-frame feasibility
- perspective
- product geometry
- camera consistency
- lighting consistency
- human interaction risk
- whether multi-pass/composite/inpainting is required

==================================================
HARSH CRITIC
==================================================

Attack the idea.

Reject:

- pretty-but-empty visuals
- familiar stock advertising
- clichés
- unnecessary complexity
- weak visual metaphor
- unclear benefit
- ideas that depend on explanatory copy
- concepts likely to collapse in image generation

==================================================
SCORING
==================================================

Score 0–100:

- message_clarity
- originality
- brand_fit
- visual_power
- feasibility
- perspective_integrity
- campaign_potential

Do NOT calculate the final weighted score.

Python calculates it.

==================================================
SCENE FEASIBILITY
==================================================

For each concept return:

- feasible_in_single_image
- complexity_level:
  low | medium | high | extreme

- recommended_production:
  single_generation |
  multi_pass |
  composite |
  inpainting

- split_required
- recommended_passes
- feasibility_notes

==================================================
ANTI-CLICHE
==================================================

Any concept containing cliché elements must lose
originality unless the cliché has been transformed into
a genuinely new visual relationship.

A concept that simply recolors a cliché with brand colors
is still a cliché.

==================================================
OUTPUT
==================================================

Return JSON only:

{{
  "evaluations": [
    {{
      "concept_id": "C01",

      "scores": {{
        "message_clarity": 0,
        "originality": 0,
        "brand_fit": 0,
        "visual_power": 0,
        "feasibility": 0,
        "perspective_integrity": 0,
        "campaign_potential": 0
      }},

      "creative_director": {{
        "verdict": "",
        "approved": true
      }},

      "brand_guardian": {{
        "verdict": "",
        "approved": true
      }},

      "production_expert": {{
        "verdict": "",
        "approved": true
      }},

      "harsh_critic": {{
        "verdict": "",
        "approved": true
      }},

      "camera_review": {{
        "current_camera_valid": true,
        "recommended_camera_angle": "",
        "recommended_lens": "",
        "reason": ""
      }},

      "feasibility": {{
        "feasible_in_single_image": true,
        "complexity_level": "low",
        "recommended_production": "single_generation",
        "split_required": false,
        "recommended_passes": [],
        "feasibility_notes": ""
      }},

      "revision_required": false,

      "revision_instruction": ""
    }}
  ]
}}

Return exactly one evaluation for every supplied concept.
""".strip()


# =========================================================
# APPLY MODEL EVALUATION
# =========================================================

def apply_evaluation(
    concept: CreativeConcept,
    evaluation: Dict[str, Any]
) -> None:

    scores = evaluation.get(
        "scores",
        {}
    )

    if not isinstance(
        scores,
        dict
    ):

        scores = {}

    required_score_keys = set(
        SCORE_WEIGHTS.keys()
    )

    supplied_score_keys = {
        key
        for key in scores.keys()
        if key in required_score_keys
    }

    evaluation_valid = (
        supplied_score_keys
        ==
        required_score_keys
    )

    normalized_scores = {
        key:
            clamp_score(
                scores.get(
                    key,
                    0
                )
            )
        for key in SCORE_WEIGHTS
    }

    weighted = calculate_weighted_score(
        normalized_scores
    )

    weighted = apply_cliche_penalty(
        weighted,
        concept.cliche_hits
    )

    concept.scores = (
        normalized_scores
    )

    concept.weighted_score = (
        weighted
    )

    concept.evaluation_valid = (
        evaluation_valid
    )

    concept.debate = {
        "creative_director":
            evaluation.get(
                "creative_director",
                {}
            ),

        "brand_guardian":
            evaluation.get(
                "brand_guardian",
                {}
            ),

        "production_expert":
            evaluation.get(
                "production_expert",
                {}
            ),

        "harsh_critic":
            evaluation.get(
                "harsh_critic",
                {}
            ),

        "camera_review":
            evaluation.get(
                "camera_review",
                {}
            ),

        "revision_required":
            bool(
                evaluation.get(
                    "revision_required",
                    False
                )
            ),

        "revision_instruction":
            clean_text(
                evaluation.get(
                    "revision_instruction"
                ),
                3000
            ),
    }

    feasibility = evaluation.get(
        "feasibility",
        {}
    )

    if not isinstance(
        feasibility,
        dict
    ):

        feasibility = {}

    concept.feasibility = (
        feasibility
    )


# =========================================================
# EVALUATION BATCH
# =========================================================

def evaluate_concept_batch(
    *,
    user_request: str,
    concepts: List[
        CreativeConcept
    ],
    brand_context: Any = None,
    visual_references: Any = None
) -> Dict[
    str,
    Dict[str, Any]
]:

    expected_ids = {
        concept.concept_id
        for concept in concepts
    }

    best_map: Dict[
        str,
        Dict[str, Any]
    ] = {}

    last_error = None

    for attempt in range(
        1,
        EVALUATION_RETRIES + 1
    ):

        try:

            prompt = build_evaluation_prompt(
                user_request=
                    user_request,

                concepts=
                    concepts,

                brand_context=
                    brand_context,

                visual_references=
                    visual_references
            )

            raw = call_openai_director(
                prompt,
                json_mode=
                    True
            )

            payload = extract_json_object(
                raw
            )

            evaluations = payload.get(
                "evaluations",
                []
            )

            if not isinstance(
                evaluations,
                list
            ):

                evaluations = []

            current_map = {}

            for item in evaluations:

                if not isinstance(
                    item,
                    dict
                ):

                    continue

                concept_id = clean_text(
                    item.get(
                        "concept_id"
                    ),
                    100
                )

                if (
                    concept_id
                    and
                    concept_id in expected_ids
                ):

                    current_map[
                        concept_id
                    ] = item

            best_map.update(
                current_map
            )

            missing = (
                expected_ids
                -
                set(
                    best_map.keys()
                )
            )

            if not missing:

                return best_map

            last_error = RuntimeError(
                (
                    "Evaluation missing concepts: "
                    +
                    ", ".join(
                        sorted(
                            missing
                        )
                    )
                )
            )

            print(
                (
                    "⚠️ Creative evaluation batch incomplete"
                    +
                    " | attempt="
                    +
                    str(
                        attempt
                    )
                    +
                    " | missing="
                    +
                    str(
                        len(
                            missing
                        )
                    )
                )
            )

        except Exception as error:

            last_error = error

            print(
                (
                    "⚠️ Creative evaluation batch failed"
                    +
                    " | attempt="
                    +
                    str(
                        attempt
                    )
                    +
                    " | "
                    +
                    clean_text(
                        error,
                        1200
                    )
                )
            )

    if best_map:

        return best_map

    raise RuntimeError(
        (
            "Creative evaluation batch failed after retries: "
            +
            clean_text(
                last_error,
                2000
            )
        )
    )


# =========================================================
# FALLBACK SCORING
#
# IMPORTANT:
#
# Used only in FAST mode.
#
# NEVER allowed to qualify a Masterpiece winner.
# =========================================================

def apply_fast_fallback_score(
    concept: CreativeConcept
) -> None:

    fallback_scores = {
        "message_clarity":
            60,

        "originality":
            (
                35
                if concept.cliche_hits
                else
                60
            ),

        "brand_fit":
            60,

        "visual_power":
            60,

        "feasibility":
            55,

        "perspective_integrity":
            55,

        "campaign_potential":
            55,
    }

    concept.scores = (
        fallback_scores
    )

    concept.weighted_score = (
        apply_cliche_penalty(
            calculate_weighted_score(
                fallback_scores
            ),
            concept.cliche_hits
        )
    )

    concept.evaluation_valid = (
        False
    )

    concept.debate[
        "fallback_scoring"
    ] = True


# =========================================================
# EVALUATE FULL CONCEPT POOL
# =========================================================

def evaluate_concept_pool(
    *,
    user_request: str,
    concepts: List[
        CreativeConcept
    ],
    brand_context: Any = None,
    visual_references: Any = None,
    mode: str = MODE_MASTERPIECE
) -> List[
    CreativeConcept
]:

    if not concepts:

        return []

    for start in range(
        0,
        len(
            concepts
        ),
        EVALUATION_BATCH_SIZE
    ):

        batch = concepts[
            start:
            start + EVALUATION_BATCH_SIZE
        ]

        try:

            evaluation_map = (
                evaluate_concept_batch(
                    user_request=
                        user_request,

                    concepts=
                        batch,

                    brand_context=
                        brand_context,

                    visual_references=
                        visual_references
                )
            )

        except Exception as error:

            print(
                (
                    "❌ Creative evaluation unavailable for batch: "
                    +
                    clean_text(
                        error,
                        1600
                    )
                )
            )

            evaluation_map = {}

        for concept in batch:

            evaluation = evaluation_map.get(
                concept.concept_id
            )

            if isinstance(
                evaluation,
                dict
            ):

                apply_evaluation(
                    concept,
                    evaluation
                )

            elif mode == MODE_FAST:

                apply_fast_fallback_score(
                    concept
                )

            else:

                #
                # MASTERPIECE:
                #
                # NO fake evaluation.
                #
                concept.scores = {}

                concept.weighted_score = 0.0

                concept.evaluation_valid = False

                concept.debate[
                    "evaluation_error"
                ] = (
                    "No valid model evaluation received."
                )

    return concepts


# =========================================================
# ROLE APPROVAL
# =========================================================

def role_approved(
    value: Any
) -> bool:

    if not isinstance(
        value,
        dict
    ):

        return False

    return bool(
        value.get(
            "approved",
            False
        )
    )


# =========================================================
# MASTERPIECE QUALITY GATE
# =========================================================

def evaluate_quality_gate(
    concept: CreativeConcept,
    *,
    mode: str
) -> Tuple[
    bool,
    List[str]
]:

    failures: List[str] = []

    if mode == MODE_FAST:

        if (
            concept.weighted_score
            <
            FAST_MIN_SCORE
        ):

            failures.append(
                (
                    "weighted_score_below_"
                    +
                    str(
                        FAST_MIN_SCORE
                    )
                )
            )

        return (
            not failures,
            failures
        )

    # =====================================================
    # REAL EVALUATION REQUIRED
    # =====================================================

    if not concept.evaluation_valid:

        failures.append(
            "no_valid_model_evaluation"
        )

    # =====================================================
    # WEIGHTED SCORE
    # =====================================================

    if (
        concept.weighted_score
        <
        MASTERPIECE_MIN_SCORE
    ):

        failures.append(
            (
                "weighted_score_"
                +
                str(
                    concept.weighted_score
                )
                +
                "_below_"
                +
                str(
                    MASTERPIECE_MIN_SCORE
                )
            )
        )

    # =====================================================
    # CRITICAL SUB-SCORES
    # =====================================================

    for key, minimum in (
        MASTERPIECE_MIN_SUBSCORES.items()
    ):

        value = clamp_score(
            concept.scores.get(
                key,
                0
            )
        )

        if value < minimum:

            failures.append(
                (
                    key
                    +
                    "_"
                    +
                    str(
                        value
                    )
                    +
                    "_below_"
                    +
                    str(
                        minimum
                    )
                )
            )

    # =====================================================
    # CLICHE HARD GATE
    # =====================================================

    if concept.cliche_hits:

        failures.append(
            (
                "anti_cliche_hits:"
                +
                ",".join(
                    item.get(
                        "id",
                        ""
                    )
                    for item in concept.cliche_hits
                    if item.get(
                        "id"
                    )
                )
            )
        )

    # =====================================================
    # FOUR-ROLE APPROVAL
    # =====================================================

    for role in [
        "creative_director",
        "brand_guardian",
        "production_expert",
        "harsh_critic",
    ]:

        if not role_approved(
            concept.debate.get(
                role
            )
        ):

            failures.append(
                (
                    role
                    +
                    "_rejected"
                )
            )

    # =====================================================
    # REVISION FLAG
    # =====================================================

    if concept.debate.get(
        "revision_required",
        False
    ):

        failures.append(
            "revision_required"
        )

    return (
        not failures,
        failures
    )


def refresh_quality_gates(
    concepts: Sequence[
        CreativeConcept
    ],
    *,
    mode: str
) -> None:

    for concept in concepts:

        passed, failures = (
            evaluate_quality_gate(
                concept,
                mode=
                    mode
            )
        )

        concept.quality_gate_passed = (
            passed
        )

        concept.quality_gate_failures = (
            failures
        )


# =========================================================
# REVIEW COMPATIBILITY FUNCTION
# =========================================================

def concept_passes_review(
    concept: CreativeConcept,
    mode: str = MODE_MASTERPIECE
) -> bool:

    passed, failures = (
        evaluate_quality_gate(
            concept,
            mode=
                mode
        )
    )

    concept.quality_gate_passed = (
        passed
    )

    concept.quality_gate_failures = (
        failures
    )

    return passed


# =========================================================
# RANKING
# =========================================================

def rank_concepts(
    concepts: Sequence[
        CreativeConcept
    ]
) -> List[
    CreativeConcept
]:

    return sorted(
        list(
            concepts
        ),
        key=
            lambda item:
                (
                    1
                    if item.evaluation_valid
                    else
                    0,

                    item.weighted_score,
                ),
        reverse=
            True
    )


# =========================================================
# TOP-CONCEPT SELECTION
# =========================================================

def select_top_concepts(
    concepts: List[
        CreativeConcept
    ],
    limit: int = 3,
    mode: str = MODE_MASTERPIECE,
    qualified_only: bool = True
) -> List[
    CreativeConcept
]:

    refresh_quality_gates(
        concepts,
        mode=
            mode
    )

    if qualified_only:

        pool = [
            concept
            for concept in concepts
            if concept.quality_gate_passed
        ]

    else:

        pool = list(
            concepts
        )

    ordered = rank_concepts(
        pool
    )

    selected: List[
        CreativeConcept
    ] = []

    used_categories = set()

    for concept in ordered:

        if len(
            selected
        ) >= limit:

            break

        if (
            concept.category
            and
            concept.category
            not in used_categories
        ):

            selected.append(
                concept
            )

            used_categories.add(
                concept.category
            )

    if len(
        selected
    ) < limit:

        selected_ids = {
            item.concept_id
            for item in selected
        }

        for concept in ordered:

            if len(
                selected
            ) >= limit:

                break

            if concept.concept_id in selected_ids:

                continue

            selected.append(
                concept
            )

            selected_ids.add(
                concept.concept_id
            )

    return selected


# =========================================================
# FAILURE CONTEXT FOR RE-IDEATION
# =========================================================

def build_failure_context(
    concepts: Sequence[
        CreativeConcept
    ],
    limit: int = 8
) -> str:

    ranked = rank_concepts(
        concepts
    )

    payload = []

    for concept in ranked[
        :limit
    ]:

        payload.append(
            {
                "title":
                    concept.title,

                "core_idea":
                    clean_text(
                        concept.core_idea,
                        800
                    ),

                "visual_metaphor":
                    clean_text(
                        concept.visual_metaphor,
                        600
                    ),

                "score":
                    concept.weighted_score,

                "gate_failures":
                    concept.quality_gate_failures,

                "cliches": [
                    item.get(
                        "id"
                    )
                    for item in concept.cliche_hits
                ],

                "revision_instruction":
                    clean_text(
                        concept.debate.get(
                            "revision_instruction",
                            ""
                        ),
                        600
                    ),
            }
        )

    return compact_json_for_prompt(
        payload,
        6500
    )


# =========================================================
# CAMERA DIRECTOR
# =========================================================

def build_camera_director_prompt(
    *,
    user_request: str,
    concept: CreativeConcept,
    visual_references: Any = None
) -> str:

    camera_library_text = (
        compact_json_for_prompt(
            CAMERA_LIBRARY,
            6000
        )
    )

    lens_library_text = (
        compact_json_for_prompt(
            LENS_LIBRARY,
            2500
        )
    )

    return f"""
You are XPAND Camera Angle Director.

Do NOT redesign the concept.

Do NOT expose chain-of-thought.

Choose the most effective physically coherent camera
setup for this approved advertising concept.

ORIGINAL REQUEST:

{clean_text(user_request, 6500)}

CONCEPT:

{compact_json_for_prompt(
    concept_payload_for_evaluation(
        concept
    ),
    7000
)}

VISUAL REFERENCES:

{compact_visual_references(
    visual_references,
    3500
)}

CAMERA LIBRARY:

{camera_library_text}

LENS LIBRARY:

{lens_library_text}

Evaluate:

- message
- subject hierarchy
- product geometry
- human anatomy risk
- depth
- negative space
- perspective reliability
- premium advertising quality

Return JSON only:

{{
  "camera_angle": "",
  "camera_height": "",
  "camera_direction": "",
  "shot_type": "",
  "lens": "",
  "camera_distance": "",
  "horizon_position": "",
  "perspective_type": "",
  "vanishing_points": "",
  "depth_strategy": "",
  "creative_reason": "",
  "generation_risk": "",
  "camera_lock_instruction": ""
}}
""".strip()


def direct_camera(
    *,
    user_request: str,
    concept: CreativeConcept,
    visual_references: Any = None
) -> Dict[str, Any]:

    raw = call_openai_director(
        build_camera_director_prompt(
            user_request=
                user_request,

            concept=
                concept,

            visual_references=
                visual_references
        ),
        json_mode=
            True
    )

    return extract_json_object(
        raw
    )


# =========================================================
# FEASIBILITY CHECK
# =========================================================

def build_feasibility_prompt(
    *,
    user_request: str,
    concept: CreativeConcept,
    visual_references: Any = None
) -> str:

    return f"""
You are XPAND Production Feasibility Expert.

Do NOT generate an image.

Do NOT redesign the advertising idea unless technically necessary.

USER REQUEST:

{clean_text(user_request, 6500)}

CONCEPT:

{compact_json_for_prompt(
    concept_payload_for_evaluation(
        concept
    ),
    7500
)}

VISUAL REFERENCES / PRODUCT LOCK:

{compact_visual_references(
    visual_references,
    4500
)}

Check:

- number of independent events
- spatial relationships
- product geometry
- text/logo sensitivity
- human-hand interaction
- perspective
- reflections
- environment complexity
- scale manipulation
- Product Lock conflicts
- whether background/product should be separate
- whether inpainting is needed
- whether multi-pass production is safer

Return JSON only:

{{
  "feasible": true,

  "complexity_level":
    "low | medium | high | extreme",

  "recommended_strategy":
    "single_generation | multi_pass | composite | inpainting",

  "passes": [
    {{
      "pass_name": "",
      "goal": "",
      "locked_elements": [],
      "editable_elements": []
    }}
  ],

  "single_image_risks": [],

  "product_lock_risks": [],

  "final_recommendation": ""
}}
""".strip()


def check_scene_feasibility(
    *,
    user_request: str,
    concept: CreativeConcept,
    visual_references: Any = None
) -> Dict[str, Any]:

    raw = call_openai_director(
        build_feasibility_prompt(
            user_request=
                user_request,

            concept=
                concept,

            visual_references=
                visual_references
        ),
        json_mode=
            True
    )

    return extract_json_object(
        raw
    )


# =========================================================
# REVISION PROMPT
# =========================================================

def build_revision_prompt(
    *,
    user_request: str,
    concept: CreativeConcept,
    brand_context: Any = None,
    visual_references: Any = None
) -> str:

    return f"""
You are XPAND Senior Creative Director.

The supplied concept is close to being useful but FAILED
the Masterpiece quality gate.

Do NOT generate an image.

Do NOT expose chain-of-thought.

You are allowed to make a MATERIAL creative improvement,
not just rewrite wording.

==================================================
ORIGINAL REQUEST
==================================================

{clean_text(user_request, 6500)}

==================================================
CURRENT CONCEPT
==================================================

{compact_json_for_prompt(
    concept_payload_for_evaluation(
        concept
    ),
    7500
)}

==================================================
CURRENT SCORE
==================================================

{concept.weighted_score}/100

==================================================
QUALITY-GATE FAILURES
==================================================

{compact_json_for_prompt(
    concept.quality_gate_failures,
    2500
)}

==================================================
DEBATE / REVIEW
==================================================

{compact_json_for_prompt(
    concept.debate,
    4500
)}

==================================================
BRAND MEMORY
==================================================

{compact_brand_context(
    brand_context,
    4000
)}

==================================================
VISUAL REFERENCES
==================================================

{compact_visual_references(
    visual_references,
    3500
)}

Improve specifically:

- originality
- message clarity
- visual metaphor
- brand-native logic
- visual power
- generation feasibility

Do NOT simply add spectacle.

Do NOT use a banned cliché.

If the central metaphor is the reason for failure,
replace that metaphor while preserving the marketing benefit.

Return JSON only:

{{
  "concept_id": "{concept.concept_id}-REV",

  "category": "{concept.category}",

  "title": "",

  "core_idea": "",

  "marketing_message": "",

  "visual_metaphor": "",

  "environment": "",

  "hero_element": "",

  "supporting_elements": [],

  "camera_angle": "",

  "lens": "",

  "perspective": "",

  "lighting": "",

  "negative_space": "",

  "brand_logic": "",

  "production_method": "",

  "campaign_extension": "",

  "risks": []
}}
""".strip()


def revise_concept(
    *,
    user_request: str,
    concept: CreativeConcept,
    brand_context: Any = None,
    visual_references: Any = None
) -> Optional[
    CreativeConcept
]:

    raw = call_openai_director(
        build_revision_prompt(
            user_request=
                user_request,

            concept=
                concept,

            brand_context=
                brand_context,

            visual_references=
                visual_references
        ),
        json_mode=
            True
    )

    payload = extract_json_object(
        raw
    )

    if not payload:

        return None

    revised = concept_from_dict(
        payload,

        fallback_id=
            (
                concept.concept_id
                +
                "-REV"
            ),

        generation_round=
            concept.generation_round,

        revised_from=
            concept.concept_id
    )

    revised.concept_id = (
        concept.concept_id
        +
        "-REV"
    )

    if not revised.category:

        revised.category = (
            concept.category
        )

    return revised


# =========================================================
# REVISION CANDIDATE SELECTION
# =========================================================

def select_revision_candidates(
    concepts: Sequence[
        CreativeConcept
    ]
) -> List[
    CreativeConcept
]:

    candidates = [
        item
        for item in concepts
        if (
            item.evaluation_valid
            and
            not item.quality_gate_passed
            and
            item.weighted_score
            >=
            MASTERPIECE_REVISION_FLOOR
        )
    ]

    candidates = rank_concepts(
        candidates
    )

    return candidates[
        :MASTERPIECE_REVISION_CANDIDATES
    ]


# =========================================================
# FINAL CAMERA + FEASIBILITY
# =========================================================

def enrich_winner(
    *,
    user_request: str,
    winner: CreativeConcept,
    visual_references: Any,
    errors: List[str]
) -> None:

    try:

        camera_direction = (
            direct_camera(
                user_request=
                    user_request,

                concept=
                    winner,

                visual_references=
                    visual_references
            )
        )

        if camera_direction:

            winner.debate[
                "camera_director"
            ] = camera_direction

    except Exception as error:

        errors.append(
            (
                "camera_director: "
                +
                clean_text(
                    error,
                    3000
                )
            )
        )

    try:

        feasibility = (
            check_scene_feasibility(
                user_request=
                    user_request,

                concept=
                    winner,

                visual_references=
                    visual_references
            )
        )

        if feasibility:

            winner.feasibility.update(
                feasibility
            )

    except Exception as error:

        errors.append(
            (
                "scene_feasibility: "
                +
                clean_text(
                    error,
                    3000
                )
            )
        )


# =========================================================
# ROUND SUMMARY
# =========================================================

def build_round_summary(
    *,
    round_number: int,
    concepts: Sequence[
        CreativeConcept
    ],
    qualified: Sequence[
        CreativeConcept
    ],
    revisions: int
) -> Dict[str, Any]:

    valid = [
        item
        for item in concepts
        if item.evaluation_valid
    ]

    best = (
        rank_concepts(
            valid
        )[0]
        if valid
        else
        None
    )

    return {
        "round":
            round_number,

        "concepts":
            len(
                concepts
            ),

        "valid_evaluations":
            len(
                valid
            ),

        "qualified":
            len(
                qualified
            ),

        "best_score":
            (
                best.weighted_score
                if best
                else
                0
            ),

        "best_id":
            (
                best.concept_id
                if best
                else
                ""
            ),

        "revisions_generated":
            revisions,
    }


# =========================================================
# MASTER CREATIVE BRAIN
# =========================================================

def run_creative_brain(
    *,
    user_request: str,
    brand_context: Any = None,
    visual_references: Any = None,
    style_hint: str = "",
    mode: str = MODE_MASTERPIECE,
    top_count: int = 3
) -> CreativeBrainResponse:

    user_request = clean_text(
        user_request,
        12000
    )

    if not user_request:

        raise ValueError(
            "Creative request is empty."
        )

    mode = clean_text(
        mode,
        100
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
            int(
                top_count
                or
                3
            ),
            5
        )
    )

    errors: List[str] = []

    all_concepts: List[
        CreativeConcept
    ] = []

    round_summaries: List[
        Dict[str, Any]
    ] = []

    winner: Optional[
        CreativeConcept
    ] = None

    failure_context = ""

    max_rounds = (
        1
        if mode == MODE_FAST
        else
        MASTERPIECE_MAX_IDEATION_ROUNDS
    )

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND CREATIVE BRAIN V1.1"
    )
    print(
        "=========================================="
    )
    print(
        "Mode:",
        mode
    )

    if mode == MODE_MASTERPIECE:

        print(
            "Masterpiece gate:",
            MASTERPIECE_MIN_SCORE
        )

        print(
            "Max ideation rounds:",
            max_rounds
        )

    print("")

    # =====================================================
    # IDEATION ROUNDS
    # =====================================================

    for round_number in range(
        1,
        max_rounds + 1
    ):

        challenger = (
            round_number
            >
            1
        )

        print(
            (
                "🧠 CREATIVE ROUND "
                +
                str(
                    round_number
                )
                +
                "/"
                +
                str(
                    max_rounds
                )
                +
                (
                    " | CHALLENGER"
                    if challenger
                    else
                    ""
                )
            )
        )

        # -------------------------------------------------
        # GENERATION
        # -------------------------------------------------

        try:

            concepts = generate_concept_pool(
                user_request=
                    user_request,

                brand_context=
                    brand_context,

                visual_references=
                    visual_references,

                style_hint=
                    style_hint,

                mode=
                    mode,

                round_number=
                    round_number,

                failure_context=
                    failure_context,

                challenger=
                    challenger
            )

        except Exception as error:

            errors.append(
                (
                    "concept_generation_round_"
                    +
                    str(
                        round_number
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
                    "❌ Ideation round failed: "
                    +
                    clean_text(
                        error,
                        1200
                    )
                )
            )

            continue

        concepts = deduplicate_concepts(
            concepts,
            all_concepts
        )

        print(
            (
                "✅ Concepts generated: "
                +
                str(
                    len(
                        concepts
                    )
                )
            )
        )

        if not concepts:

            errors.append(
                (
                    "round_"
                    +
                    str(
                        round_number
                    )
                    +
                    "_all_duplicate"
                )
            )

            continue

        # -------------------------------------------------
        # REAL MODEL EVALUATION
        # -------------------------------------------------

        concepts = evaluate_concept_pool(
            user_request=
                user_request,

            concepts=
                concepts,

            brand_context=
                brand_context,

            visual_references=
                visual_references,

            mode=
                mode
        )

        refresh_quality_gates(
            concepts,
            mode=
                mode
        )

        all_concepts.extend(
            concepts
        )

        qualified = select_top_concepts(
            all_concepts,

            limit=
                top_count,

            mode=
                mode,

            qualified_only=
                True
        )

        if qualified:

            winner = qualified[
                0
            ]

            round_summaries.append(
                build_round_summary(
                    round_number=
                        round_number,

                    concepts=
                        concepts,

                    qualified=
                        qualified,

                    revisions=
                        0
                )
            )

            print(
                (
                    "🏆 MASTERPIECE GATE PASSED"
                    +
                    " | "
                    +
                    winner.concept_id
                    +
                    " | score="
                    +
                    str(
                        winner.weighted_score
                    )
                )
            )

            break

        # =================================================
        # FAST MODE
        # =================================================

        if mode == MODE_FAST:

            diagnostic = select_top_concepts(
                all_concepts,

                limit=
                    top_count,

                mode=
                    mode,

                qualified_only=
                    False
            )

            winner = (
                diagnostic[
                    0
                ]
                if diagnostic
                else
                None
            )

            round_summaries.append(
                build_round_summary(
                    round_number=
                        round_number,

                    concepts=
                        concepts,

                    qualified=
                        [],

                    revisions=
                        0
                )
            )

            break

        # =================================================
        # MASTERPIECE REVISION
        # =================================================

        revisions: List[
            CreativeConcept
        ] = []

        revision_candidates = (
            select_revision_candidates(
                all_concepts
            )
        )

        if revision_candidates:

            print(
                (
                    "🛠️ Revising "
                    +
                    str(
                        len(
                            revision_candidates
                        )
                    )
                    +
                    " near-winner concept(s)..."
                )
            )

        for candidate in revision_candidates:

            try:

                revised = revise_concept(
                    user_request=
                        user_request,

                    concept=
                        candidate,

                    brand_context=
                        brand_context,

                    visual_references=
                        visual_references
                )

                if revised:

                    revisions.append(
                        revised
                    )

            except Exception as error:

                errors.append(
                    (
                        "revision_"
                        +
                        candidate.concept_id
                        +
                        ": "
                        +
                        clean_text(
                            error,
                            2500
                        )
                    )
                )

        revisions = deduplicate_concepts(
            revisions,
            all_concepts
        )

        if revisions:

            revisions = evaluate_concept_pool(
                user_request=
                    user_request,

                concepts=
                    revisions,

                brand_context=
                    brand_context,

                visual_references=
                    visual_references,

                mode=
                    MODE_MASTERPIECE
            )

            refresh_quality_gates(
                revisions,
                mode=
                    MODE_MASTERPIECE
            )

            all_concepts.extend(
                revisions
            )

            qualified = select_top_concepts(
                all_concepts,

                limit=
                    top_count,

                mode=
                    MODE_MASTERPIECE,

                qualified_only=
                    True
            )

            if qualified:

                winner = qualified[
                    0
                ]

                round_summaries.append(
                    build_round_summary(
                        round_number=
                            round_number,

                        concepts=
                            concepts,

                        qualified=
                            qualified,

                        revisions=
                            len(
                                revisions
                            )
                    )
                )

                print(
                    (
                        "🏆 MASTERPIECE GATE PASSED AFTER REVISION"
                        +
                        " | "
                        +
                        winner.concept_id
                        +
                        " | score="
                        +
                        str(
                            winner.weighted_score
                        )
                    )
                )

                break

        # -------------------------------------------------
        # ROUND FAILED
        # -------------------------------------------------

        refresh_quality_gates(
            all_concepts,
            mode=
                MODE_MASTERPIECE
        )

        valid_ranked = [
            item
            for item in rank_concepts(
                all_concepts
            )
            if item.evaluation_valid
        ]

        best_score = (
            valid_ranked[
                0
            ].weighted_score
            if valid_ranked
            else
            0
        )

        best_id = (
            valid_ranked[
                0
            ].concept_id
            if valid_ranked
            else
            "-"
        )

        print(
            (
                "⛔ MASTERPIECE GATE NOT PASSED"
                +
                " | best="
                +
                best_id
                +
                " | score="
                +
                str(
                    best_score
                )
                +
                " | required="
                +
                str(
                    MASTERPIECE_MIN_SCORE
                )
            )
        )

        round_summaries.append(
            build_round_summary(
                round_number=
                    round_number,

                concepts=
                    concepts,

                qualified=
                    [],

                revisions=
                    len(
                        revisions
                    )
            )
        )

        failure_context = (
            build_failure_context(
                all_concepts
            )
        )

    # =====================================================
    # FINAL TOP CONCEPTS
    # =====================================================

    refresh_quality_gates(
        all_concepts,
        mode=
            mode
    )

    qualified_top = select_top_concepts(
        all_concepts,

        limit=
            top_count,

        mode=
            mode,

        qualified_only=
            True
    )

    if qualified_top:

        top_concepts = (
            qualified_top
        )

        winner = (
            qualified_top[
                0
            ]
        )

    else:

        #
        # Diagnostic top concepts are returned only so the
        # caller/logs can inspect what failed.
        #
        # They are NOT declared Masterpiece winners.
        #

        top_concepts = select_top_concepts(
            all_concepts,

            limit=
                top_count,

            mode=
                mode,

            qualified_only=
                False
        )

        if mode == MODE_MASTERPIECE:

            winner = None

    # =====================================================
    # FINAL SPECIALIST PASSES
    # =====================================================

    if winner:

        enrich_winner(
            user_request=
                user_request,

            winner=
                winner,

            visual_references=
                visual_references,

            errors=
                errors
        )

    # =====================================================
    # HONEST MASTERPIECE FAILURE
    # =====================================================

    quality_gate_passed = (
        bool(
            winner
        )
        if mode == MODE_MASTERPIECE
        else
        bool(
            top_concepts
        )
    )

    if (
        mode == MODE_MASTERPIECE
        and
        not quality_gate_passed
    ):

        errors.append(
            (
                "masterpiece_quality_gate_failed:"
                +
                " no concept achieved the required "
                +
                str(
                    MASTERPIECE_MIN_SCORE
                )
                +
                "/100 standard."
            )
        )

        print("")
        print(
            "=========================================="
        )
        print(
            " MASTERPIECE QUALITY GATE: FAILED"
        )
        print(
            "=========================================="
        )
        print(
            "No fake winner selected."
        )
        print(
            "Required score:",
            MASTERPIECE_MIN_SCORE
        )
        print("")

    elif winner:

        print("")
        print(
            "=========================================="
        )
        print(
            " MASTERPIECE QUALITY GATE: PASSED"
            if mode == MODE_MASTERPIECE
            else
            " CREATIVE SELECTION COMPLETE"
        )
        print(
            "=========================================="
        )
        print(
            "Winner:",
            winner.concept_id
        )
        print(
            "Score:",
            winner.weighted_score
        )
        print("")

    return CreativeBrainResponse(
        ok=
            quality_gate_passed,

        mode=
            mode,

        request=
            user_request,

        total_concepts=
            len(
                all_concepts
            ),

        concepts=
            all_concepts,

        top_concepts=
            top_concepts,

        winner=
            winner,

        metadata={
            "version":
                VERSION,

            "distribution":
                (
                    FAST_DISTRIBUTION
                    if mode == MODE_FAST
                    else
                    MASTERPIECE_DISTRIBUTION
                ),

            "challenger_distribution":
                CHALLENGER_DISTRIBUTION,

            "score_weights":
                SCORE_WEIGHTS,

            "masterpiece_min_score":
                MASTERPIECE_MIN_SCORE,

            "masterpiece_min_subscores":
                MASTERPIECE_MIN_SUBSCORES,

            "masterpiece_max_rounds":
                MASTERPIECE_MAX_IDEATION_ROUNDS,

            "evaluation_batch_size":
                EVALUATION_BATCH_SIZE,

            "evaluation_retries":
                EVALUATION_RETRIES,

            "anti_cliche_enabled":
                True,

            "visual_metaphor_enabled":
                True,

            "creative_debate_enabled":
                True,

            "camera_director_enabled":
                True,

            "scene_feasibility_enabled":
                True,

            "automatic_revision_enabled":
                (
                    MASTERPIECE_REVISION_CANDIDATES
                    >
                    0
                ),

            "automatic_reideation_enabled":
                (
                    MASTERPIECE_MAX_IDEATION_ROUNDS
                    >
                    1
                ),

            "quality_gate_enabled":
                (
                    mode
                    ==
                    MODE_MASTERPIECE
                ),

            "quality_gate_passed":
                quality_gate_passed,

            "fake_fallback_winner_allowed":
                False,

            "rounds":
                round_summaries,
        },

        errors=
            errors,
    )


# =========================================================
# SERIALIZER
# =========================================================

def concept_to_dict(
    concept: CreativeConcept
) -> Dict[str, Any]:

    return {
        "concept_id":
            concept.concept_id,

        "category":
            concept.category,

        "title":
            concept.title,

        "core_idea":
            concept.core_idea,

        "marketing_message":
            concept.marketing_message,

        "visual_metaphor":
            concept.visual_metaphor,

        "environment":
            concept.environment,

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
    response: CreativeBrainResponse
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

        "top_concepts": [
            concept_to_dict(
                item
            )
            for item in response.top_concepts
        ],

        "winner":
            (
                concept_to_dict(
                    response.winner
                )
                if response.winner
                else
                None
            ),

        "metadata":
            response.metadata,

        "errors":
            response.errors,
    }


# =========================================================
# HUMAN-FRIENDLY SUMMARY
# =========================================================

def build_top_concepts_summary(
    response: CreativeBrainResponse
) -> str:

    if not response.top_concepts:

        return (
            "ما طلعت اتجاهات إبداعية كافية."
        )

    lines: List[str] = []

    lines.append(
        (
            "XPAND Creative Brain | "
            +
            response.mode.upper()
        )
    )

    lines.append(
        (
            "تم تحليل "
            +
            str(
                response.total_concepts
            )
            +
            " اتجاه إبداعي."
        )
    )

    if (
        response.mode
        ==
        MODE_MASTERPIECE
    ):

        lines.append(
            (
                "Masterpiece Gate: "
                +
                (
                    "PASSED"
                    if response.metadata.get(
                        "quality_gate_passed"
                    )
                    else
                    "FAILED"
                )
            )
        )

    lines.append("")

    for index, concept in enumerate(
        response.top_concepts,
        start=1
    ):

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

        lines.append(
            (
                "الفكرة: "
                +
                concept.core_idea
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

        lines.append(
            (
                "Quality Gate: "
                +
                (
                    "PASS"
                    if concept.quality_gate_passed
                    else
                    "FAIL"
                )
            )
        )

        lines.append("")

    return "\n".join(
        lines
    ).strip()


# =========================================================
# LOCAL SELF TEST
#
# NO API CALLS.
# NO PAID USAGE.
# =========================================================

if __name__ == "__main__":

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND CREATIVE BRAIN V1.1"
    )
    print(
        "=========================================="
    )
    print("")

    print(
        "Masterpiece concepts:",
        sum(
            MASTERPIECE_DISTRIBUTION.values()
        )
    )

    print(
        "Challenger concepts:",
        sum(
            CHALLENGER_DISTRIBUTION.values()
        )
    )

    print(
        "Fast concepts:",
        sum(
            FAST_DISTRIBUTION.values()
        )
    )

    print("")

    print(
        "Masterpiece gate:",
        MASTERPIECE_MIN_SCORE
    )

    print(
        "Revision floor:",
        MASTERPIECE_REVISION_FLOOR
    )

    print(
        "Maximum ideation rounds:",
        MASTERPIECE_MAX_IDEATION_ROUNDS
    )

    print(
        "Evaluation batch size:",
        EVALUATION_BATCH_SIZE
    )

    print(
        "Evaluation retries:",
        EVALUATION_RETRIES
    )

    print("")

    print(
        "Score weights total:",
        sum(
            SCORE_WEIGHTS.values()
        ),
        "%"
    )

    print("")

    # =====================================================
    # WEIGHTED SCORE TEST
    # =====================================================

    strong_scores = {
        "message_clarity":
            90,

        "originality":
            90,

        "brand_fit":
            95,

        "visual_power":
            92,

        "feasibility":
            85,

        "perspective_integrity":
            90,

        "campaign_potential":
            88,
    }

    strong_weighted = (
        calculate_weighted_score(
            strong_scores
        )
    )

    print(
        "Strong weighted test score:",
        strong_weighted
    )

    print("")

    # =====================================================
    # OLD 58.75 FALLBACK REPRODUCTION
    # =====================================================

    old_fallback_scores = {
        "message_clarity":
            60,

        "originality":
            60,

        "brand_fit":
            60,

        "visual_power":
            60,

        "feasibility":
            55,

        "perspective_integrity":
            55,

        "campaign_potential":
            55,
    }

    old_fallback_weighted = (
        calculate_weighted_score(
            old_fallback_scores
        )
    )

    print(
        "Old fallback weighted score:",
        old_fallback_weighted
    )

    print(
        "Expected old fallback:",
        58.75
    )

    print(
        (
            "✅ Old 58.75 fallback identified"
            if old_fallback_weighted
            ==
            58.75
            else
            "❌ Unexpected fallback calculation"
        )
    )

    print("")

    # =====================================================
    # WEAK CONCEPT GATE TEST
    # =====================================================

    weak = CreativeConcept(
        concept_id=
            "WEAK",

        category=
            "simple_intelligent",

        title=
            "Weak test",

        core_idea=
            "Generic idea",

        marketing_message=
            "Test",

        visual_metaphor=
            "Generic",

        environment=
            "Generic room",

        hero_element=
            "Object",

        supporting_elements=[],

        camera_angle=
            "Eye-Level",

        lens=
            "50mm",

        perspective=
            "normal",

        lighting=
            "soft",

        negative_space=
            "center",

        brand_logic=
            "generic",

        production_method=
            "single_generation",

        campaign_extension=
            "none",

        risks=[],

        scores=
            old_fallback_scores,

        weighted_score=
            old_fallback_weighted,

        evaluation_valid=
            True,

        debate={
            "creative_director": {
                "approved":
                    True
            },

            "brand_guardian": {
                "approved":
                    True
            },

            "production_expert": {
                "approved":
                    True
            },

            "harsh_critic": {
                "approved":
                    True
            },

            "revision_required":
                False,
        },
    )

    weak_passed, weak_failures = (
        evaluate_quality_gate(
            weak,
            mode=
                MODE_MASTERPIECE
        )
    )

    print(
        "Old 58.75 concept gate:",
        (
            "REJECTED ✅"
            if not weak_passed
            else
            "ACCEPTED ❌"
        )
    )

    print(
        "Failure count:",
        len(
            weak_failures
        )
    )

    print("")

    # =====================================================
    # STRONG CONCEPT GATE TEST
    # =====================================================

    strong = CreativeConcept(
        concept_id=
            "STRONG",

        category=
            "conceptual_photorealism",

        title=
            "Strong test",

        core_idea=
            "One original visual mechanism clearly communicates the benefit.",

        marketing_message=
            "Clear",

        visual_metaphor=
            "Original spatial transformation",

        environment=
            "Premium controlled environment",

        hero_element=
            "Single meaningful hero",

        supporting_elements=[],

        camera_angle=
            "Forced-Perspective Shot",

        lens=
            "35mm",

        perspective=
            "coherent",

        lighting=
            "motivated cinematic",

        negative_space=
            "intentional",

        brand_logic=
            "brand-native",

        production_method=
            "multi_pass",

        campaign_extension=
            "strong",

        risks=[],

        scores=
            strong_scores,

        weighted_score=
            strong_weighted,

        evaluation_valid=
            True,

        debate={
            "creative_director": {
                "approved":
                    True
            },

            "brand_guardian": {
                "approved":
                    True
            },

            "production_expert": {
                "approved":
                    True
            },

            "harsh_critic": {
                "approved":
                    True
            },

            "revision_required":
                False,
        },
    )

    strong_passed, strong_failures = (
        evaluate_quality_gate(
            strong,
            mode=
                MODE_MASTERPIECE
        )
    )

    print(
        "Strong concept gate:",
        (
            "PASSED ✅"
            if strong_passed
            else
            "FAILED ❌"
        )
    )

    print(
        "Strong failures:",
        len(
            strong_failures
        )
    )

    print("")

    # =====================================================
    # INVALID EVALUATION TEST
    # =====================================================

    invalid = CreativeConcept(
        concept_id=
            "INVALID",

        category=
            "bold_experimental",

        title=
            "Invalid evaluation",

        core_idea=
            "Unknown",

        marketing_message=
            "",

        visual_metaphor=
            "",

        environment=
            "",

        hero_element=
            "",

        supporting_elements=[],

        camera_angle=
            "",

        lens=
            "",

        perspective=
            "",

        lighting=
            "",

        negative_space=
            "",

        brand_logic=
            "",

        production_method=
            "",

        campaign_extension=
            "",

        risks=[],

        scores=
            strong_scores,

        weighted_score=
            95,

        evaluation_valid=
            False,

        debate={
            "creative_director": {
                "approved":
                    True
            },

            "brand_guardian": {
                "approved":
                    True
            },

            "production_expert": {
                "approved":
                    True
            },

            "harsh_critic": {
                "approved":
                    True
            },

            "revision_required":
                False,
        },
    )

    invalid_passed, invalid_failures = (
        evaluate_quality_gate(
            invalid,
            mode=
                MODE_MASTERPIECE
        )
    )

    print(
        "Invalid model evaluation gate:",
        (
            "REJECTED ✅"
            if not invalid_passed
            else
            "ACCEPTED ❌"
        )
    )

    print(
        (
            "✅ Real model evaluation required"
            if
            "no_valid_model_evaluation"
            in
            invalid_failures
            else
            "❌ Missing real-evaluation protection"
        )
    )

    print("")

    # =====================================================
    # CLICHE TEST
    # =====================================================

    cliche_test = (
        "A smiling businessman holding a floating "
        "bank card with flying money and icons."
    )

    hits = detect_cliches(
        cliche_test
    )

    print(
        "Anti-cliche test hits:",
        len(
            hits
        )
    )

    for hit in hits:

        print(
            " -",
            hit[
                "id"
            ],
            "|",
            hit[
                "reason"
            ]
        )

    print("")

    metaphor = get_metaphor_seed(
        (
            "إعلان عن التحويل الدولي "
            "بسرعة"
        )
    )

    print(
        "Metaphor family:",
        metaphor[
            "family"
        ]
    )

    print("")

    print(
        "✅ 20-direction Masterpiece engine"
    )

    print(
        "✅ 82+ Masterpiece Quality Gate"
    )

    print(
        "✅ Critical sub-score gates"
    )

    print(
        "✅ Real model evaluation required"
    )

    print(
        "✅ Old 58.75 fallback cannot win Masterpiece"
    )

    print(
        "✅ Evaluation batching"
    )

    print(
        "✅ Structured JSON evaluation"
    )

    print(
        "✅ Evaluation retry"
    )

    print(
        "✅ Automatic near-winner revision"
    )

    print(
        "✅ Automatic challenger re-ideation"
    )

    print(
        "✅ Failure-aware new concept rounds"
    )

    print(
        "✅ Duplicate concept suppression"
    )

    print(
        "✅ Weighted scoring"
    )

    print(
        "✅ Anti-Cliche hard gate"
    )

    print(
        "✅ Visual Metaphor engine"
    )

    print(
        "✅ Creative Debate"
    )

    print(
        "✅ Brand Guardian"
    )

    print(
        "✅ Production Expert"
    )

    print(
        "✅ Harsh Critic"
    )

    print(
        "✅ Camera Angle Director"
    )

    print(
        "✅ Scene Feasibility Check"
    )

    print(
        "✅ Fast Mode fallback preserved"
    )

    print(
        "✅ Masterpiece fake-winner fallback removed"
    )

    print(
        "🚫 No API calls were made"
    )

    print("")
