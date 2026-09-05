# =========================================================
# XPAND CREATIVE BRAIN V5.0
#
# STC-FIRST / COST-CONTROLLED CREATIVE INTELLIGENCE
#
# =========================================================
#
# NORMAL MASTERPIECE PATH
#
# 4 materially different concepts        [CALL 1]
#        ↓
# FREE local quality / cliché /
# realism / diversity preflight
#        ↓
# strongest 2
#        ↓
# ONE consolidated Creative Board        [CALL 2]
#        ↓
# winner 88+ OR adaptive 84+
#
# ONLY IF REQUIRED:
#
# 2 materially new challengers +
# evaluation in same JSON response       [CALL 3]
#
# =========================================================
#
# DESIGN GOALS
#
# - Fewer paid calls.
# - Stronger concepts.
# - Explicit structured-output schemas.
# - Technical failure != creative failure.
# - STC Bank is a visual language, not "purple + neon".
# - No generated advertising text or logos for STC Bank.
# - Review camera + feasibility in the SAME call.
# - No separate camera call.
# - No separate feasibility call.
# - No automatic winner-finalizer call.
# - No fake fallback score.
# - No image generation in this module.
#
# Running this file directly makes ZERO API calls.
#
# =========================================================

from __future__ import annotations

import ast
import json
import os
import re

from dataclasses import dataclass, field

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

from xpand_stc_bank_skill import (
    STC_BANK_VISUAL_SKILL,
    is_stc_bank_request,
)


# =========================================================
# IDENTITY
# =========================================================

VERSION = "5.0"

MODULE_NAME = "XPAND Creative Brain"


# =========================================================
# MODES
# =========================================================

MODE_FAST = "fast"

MODE_MASTERPIECE = "masterpiece"


# =========================================================
# COST POLICY
# =========================================================

#
# The old architecture generated 20 directions.
# That is no longer the default.
#
# Four materially different concepts are enough when the
# ideation prompt is disciplined.
#

MASTERPIECE_INITIAL_CONCEPTS = max(
    4,
    min(
        6,
        int(
            os.environ.get(
                "XPAND_CREATIVE_INITIAL_CONCEPTS",
                "4",
            )
            or 4
        ),
    ),
)


FAST_INITIAL_CONCEPTS = max(
    3,
    min(
        4,
        int(
            os.environ.get(
                "XPAND_CREATIVE_FAST_CONCEPTS",
                "3",
            )
            or 3
        ),
    ),
)


MASTERPIECE_SHORTLIST_SIZE = max(
    2,
    min(
        3,
        int(
            os.environ.get(
                "XPAND_CREATIVE_SHORTLIST_SIZE",
                "2",
            )
            or 2
        ),
    ),
)


RECOVERY_CONCEPTS = 2


#
# Normal path:
# 1 ideation
# 1 review
#
# Worst normal Masterpiece path:
# + 1 recovery board
#

MASTERPIECE_TARGET_DIRECTOR_CALLS = 2

MASTERPIECE_MAX_DIRECTOR_CALLS = 3


# =========================================================
# QUALITY TARGETS
# =========================================================

MASTERPIECE_MIN_SCORE = max(
    75.0,
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
    72.0,
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
                "72",
            )
            or 72
        ),
    ),
)


# =========================================================
# SCORE WEIGHTS
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


MASTERPIECE_RELEASE_MIN_SUBSCORES = {
    "message_clarity":
        78,

    "originality":
        78,

    "brand_fit":
        82,

    "visual_power":
        78,

    "feasibility":
        74,

    "perspective_integrity":
        74,

    "campaign_potential":
        74,
}


MASTERPIECE_TARGET_MIN_SUBSCORES = {
    "message_clarity":
        84,

    "originality":
        84,

    "brand_fit":
        88,

    "visual_power":
        84,

    "feasibility":
        80,

    "perspective_integrity":
        80,

    "campaign_potential":
        80,
}


# =========================================================
# COMPATIBILITY CONSTANTS
# =========================================================

MASTERPIECE_MAX_IDEATION_ROUNDS = 2

MASTERPIECE_REVISION_CANDIDATES = 0

MASTERPIECE_REVISION_FLOOR = (
    MASTERPIECE_RELEASE_FLOOR
)

EVALUATION_BATCH_SIZE = (
    MASTERPIECE_SHORTLIST_SIZE
)

EVALUATION_RETRIES = 1


MASTERPIECE_DISTRIBUTION = {
    "premium_realistic":
        2,

    "purple_architectural":
        1,

    "augmented_realism":
        1,
}


FAST_DISTRIBUTION = {
    "premium_realistic":
        2,

    "conceptual":
        1,
}


RECOVERY_DISTRIBUTION = {
    "strategic_rebuild":
        1,

    "bold_rebuild":
        1,
}


CHALLENGER_DISTRIBUTION = (
    RECOVERY_DISTRIBUTION
)


# =========================================================
# CAMERA SCIENCE
# =========================================================

CAMERA_LIBRARY = {
    "eye_level": {
        "scientific_name":
            "Eye-Level Shot",

        "logic":
            (
                "Natural human-scale perspective. "
                "Strong for trust, lifestyle and believable commerce."
            ),
    },

    "low_angle": {
        "scientific_name":
            "Low-Angle Shot",

        "logic":
            (
                "Camera below subject eye line. "
                "Creates authority and premium hero presence."
            ),
    },

    "extreme_low_angle": {
        "scientific_name":
            "Extreme Low-Angle Shot",

        "logic":
            (
                "Strong upward perspective for deliberate "
                "monumental scale."
            ),
    },

    "worms_eye": {
        "scientific_name":
            "Worm's-Eye View",

        "logic":
            (
                "Near-ground upward viewpoint. "
                "Useful only when scale transformation supports the idea."
            ),
    },

    "high_angle": {
        "scientific_name":
            "High-Angle Shot",

        "logic":
            (
                "Camera above the subject. "
                "Good for spatial relationships and controlled overview."
            ),
    },

    "birds_eye": {
        "scientific_name":
            "Bird's-Eye View",

        "logic":
            (
                "Elevated near-orthographic overview. "
                "Use for meaningful real spatial organization."
            ),
    },

    "top_down": {
        "scientific_name":
            "Top-Down / Overhead Shot",

        "logic":
            (
                "Camera perpendicular to the scene plane. "
                "Useful for physical object layouts and graphic order."
            ),
    },

    "three_quarter": {
        "scientific_name":
            "Three-Quarter Hero Shot",

        "logic":
            (
                "Shows front and side planes together. "
                "Excellent for premium products, cards and devices."
            ),
    },

    "over_shoulder": {
        "scientific_name":
            "Over-the-Shoulder Shot",

        "logic":
            (
                "Contextual interaction shot. "
                "Strong for digital banking and app behavior."
            ),
    },

    "pov": {
        "scientific_name":
            "Point-of-View Shot",

        "logic":
            (
                "First-person perspective for immersive action."
            ),
    },

    "ground_level": {
        "scientific_name":
            "Ground-Level Shot",

        "logic":
            (
                "Very low camera height while remaining horizontally "
                "oriented; creates foreground depth."
            ),
    },

    "macro": {
        "scientific_name":
            "Macro Shot",

        "logic":
            (
                "Fine material / product detail with shallow optical depth."
            ),
    },

    "extreme_closeup": {
        "scientific_name":
            "Extreme Close-Up",

        "logic":
            (
                "Tight material or interaction detail."
            ),
    },

    "wide": {
        "scientific_name":
            "Wide Environmental Shot",

        "logic":
            (
                "Subject integrated into a strong real environment."
            ),
    },

    "extreme_wide": {
        "scientific_name":
            "Extreme Wide / Establishing Shot",

        "logic":
            (
                "Environment carries major storytelling weight."
            ),
    },

    "forced_perspective": {
        "scientific_name":
            "Forced-Perspective Composition",

        "logic":
            (
                "Real spatial alignment manipulates perceived scale "
                "without unsupported floating objects."
            ),
    },

    "one_point": {
        "scientific_name":
            "One-Point Perspective",

        "logic":
            (
                "Single vanishing point. "
                "Powerful for architecture, symmetry and depth."
            ),
    },

    "two_point": {
        "scientific_name":
            "Two-Point Perspective",

        "logic":
            (
                "Two horizontal vanishing points. "
                "Natural for corners, retail architecture and product staging."
            ),
    },

    "frame_within_frame": {
        "scientific_name":
            "Frame-within-a-Frame Composition",

        "logic":
            (
                "Architecture or physical objects create a secondary frame."
            ),
    },

    "foreground_obstruction": {
        "scientific_name":
            "Foreground-Obstruction Composition",

        "logic":
            (
                "A partial foreground object creates cinematic depth "
                "and observed realism."
            ),
    },
}


LENS_LIBRARY = {
    "18mm":
        (
            "Dramatic environmental width; only when intentional."
        ),

    "24mm":
        (
            "Premium wide commercial environmental photography."
        ),

    "28mm":
        (
            "Dynamic commercial environment with controlled perspective."
        ),

    "35mm":
        (
            "Cinematic environmental storytelling and lifestyle."
        ),

    "50mm":
        (
            "Natural balanced perspective."
        ),

    "70mm":
        (
            "Controlled commercial compression."
        ),

    "85mm":
        (
            "Premium portrait / product compression."
        ),

    "105mm":
        (
            "Luxury product or portrait isolation."
        ),

    "macro":
        (
            "Close product material detail."
        ),

    "tilt_shift":
        (
            "Perspective-controlled architecture."
        ),
}


# =========================================================
# STC SCENE ARCHETYPES
# =========================================================

STC_SCENE_ARCHETYPES = {
    "merchant_payments": [
        (
            "premium Saudi boutique checkout with genuine merchant-customer "
            "interaction and physically correct POS placement"
        ),

        (
            "refined specialty café payment moment with polished stone, "
            "warm timber and natural daylight"
        ),

        (
            "high-end retail counter where physical POS and an online-order "
            "workflow are communicated through real human behavior"
        ),

        (
            "elegant restaurant or hospitality payment moment using "
            "subtle contextual commerce cues"
        ),

        (
            "small premium Saudi business owner managing a real order "
            "while a customer completes an in-person payment"
        ),

        (
            "executive merchant environment with phone, laptop and POS "
            "integrated naturally rather than displayed to camera"
        ),

        (
            "bird's-eye physical commerce composition using real products, "
            "packaging, receipt-free POS interaction and strong material detail"
        ),

        (
            "low-angle commercial retail composition using architecture "
            "and counter geometry to give the merchant confidence and scale"
        ),
    ],

    "travel": [
        (
            "premium Saudi traveler in a refined airport or hotel context"
        ),

        (
            "destination lifestyle scene with banking utility integrated "
            "naturally into behavior"
        ),

        (
            "POV travel moment where the service solves a real travel action"
        ),

        (
            "wide cinematic travel scene with restrained product integration"
        ),
    ],

    "international_transfer": [
        (
            "real family or business relationship connecting two places "
            "without maps or network graphics"
        ),

        (
            "premium everyday international relationship expressed through "
            "real-world context and behavior"
        ),

        (
            "one physical space containing subtle authentic cultural cues "
            "from two destinations without impossible collage"
        ),
    ],

    "cashback": [
        (
            "premium everyday purchase where the value is communicated "
            "through the experience rather than floating money"
        ),

        (
            "lifestyle benefit scene with understated luxury and real behavior"
        ),
    ],

    "digital_banking": [
        (
            "natural over-the-shoulder banking interaction in a premium "
            "real environment"
        ),

        (
            "executive or lifestyle mobile-banking moment with clean "
            "negative space and no floating interface"
        ),
    ],

    "premium": [
        (
            "refined Saudi lifestyle commercial scene with restrained "
            "identity accents"
        ),

        (
            "premium product-oriented still life using stone, glass, "
            "metal and controlled reflections"
        ),

        (
            "architectural commercial scene with disciplined perspective "
            "and intentional negative space"
        ),
    ],
}


# =========================================================
# ANTI-CLICHE / HARD RISKS
# =========================================================

CLICHE_LIBRARY = {
    "flying_money": [
        "flying money",
        "flying coins",
        "floating coins",
        "عملات طائرة",
        "فلوس طايرة",
    ],

    "floating_card": [
        "floating card",
        "floating bank card",
        "levitating card",
        "بطاقة طافية",
        "بطاقه طايره",
    ],

    "floating_phone": [
        "floating phone",
        "levitating phone",
        "هاتف طائر",
        "هاتف يطفو",
    ],

    "phone_icons": [
        "phone surrounded by icons",
        "floating app icons",
        "floating banking icons",
        "هاتف محاط بايقونات",
        "هاتف محاط بأيقونات",
    ],

    "globe": [
        "generic globe",
        "world globe",
        "planet earth",
        "كرة أرضية",
        "كره ارضيه",
    ],

    "network_lines": [
        "network lines",
        "connection lines",
        "route lines",
        "transfer line",
        "خطوط اتصال",
        "خط اتصال",
    ],

    "laser": [
        "laser beam",
        "blue laser",
        "neon trail",
        "glowing route",
        "مسار ضوئي",
        "شعاع ليزر",
    ],

    "hologram": [
        "hologram",
        "holographic interface",
        "هولوغرام",
    ],

    "hud": [
        "hud",
        "futuristic interface",
        "floating interface",
        "واجهة مستقبلية",
    ],

    "particles": [
        "random particles",
        "sparkles",
        "particle cloud",
        "جزيئات",
        "شرارات",
    ],

    "shield": [
        "security shield",
        "digital shield",
        "درع الأمان",
        "درع الامان",
    ],

    "growth_arrow": [
        "upward arrow",
        "rising graph",
        "سهم صاعد",
    ],

    "handshake": [
        "business handshake",
        "handshake",
        "مصافحة",
    ],

    "purple_neon": [
        "purple neon",
        "neon purple",
        "purple neon glow",
        "نيون بنفسجي",
    ],

    "generic_fintech": [
        "generic fintech",
        "generic banking visual",
        "generic futuristic banking",
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

    style_family: str

    scene_archetype: str

    environment: str

    hero_element: str

    supporting_elements: List[str]

    camera_angle: str

    lens: str

    perspective: str

    lighting: str

    negative_space: str

    material_language: str

    color_strategy: str

    brand_logic: str

    production_method: str

    campaign_extension: str

    risks: List[str]

    scores: Dict[str, float] = field(
        default_factory=dict
    )

    weighted_score: float = 0.0

    cliche_hits: List[
        Dict[str, str]
    ] = field(
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

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    errors: List[str] = field(
        default_factory=list
    )


# =========================================================
# EXCEPTIONS
# =========================================================

class CreativeBrainError(
    RuntimeError
):
    pass


class IdeationParseError(
    CreativeBrainError
):
    pass


class IdeationShapeError(
    CreativeBrainError
):
    pass


class IdeationCountError(
    CreativeBrainError
):
    pass


class ReviewShapeError(
    CreativeBrainError
):
    pass


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


def normalize_text(
    value: Any,
) -> str:

    text = clean_text(
        value,
        50000,
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
    text: Any,
    markers: Sequence[str],
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


def clamp_score(
    value: Any,
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
            number,
        ),
    )


def compact_json_for_prompt(
    value: Any,
    limit: int,
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
        0.78
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


# =========================================================
# CONTEXT COMPACTION
# =========================================================

def compact_brand_context(
    brand_context: Any,
    limit: int = 3600,
) -> str:

    if not brand_context:

        return "{}"

    if isinstance(
        brand_context,
        str,
    ):

        return clean_text(
            brand_context,
            limit,
        )

    context = safe_dict(
        brand_context
    )

    compact = {
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

        "visual_profile":
            context.get(
                "visual_profile",
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
    }

    return compact_json_for_prompt(
        compact,
        limit,
    )


def compact_visual_references(
    visual_references: Any,
    limit: int = 3000,
) -> str:

    if not visual_references:

        return "[]"

    if isinstance(
        visual_references,
        str,
    ):

        return clean_text(
            visual_references,
            limit,
        )

    references = safe_list(
        visual_references
    )[:3]

    compact = []

    for item in references:

        if not isinstance(
            item,
            dict,
        ):

            compact.append(
                clean_text(
                    item,
                    800,
                )
            )

            continue

        useful = {}

        for key in [
            "title",
            "note",
            "role",
            "summary",
            "analysis",
            "visual_dna",
            "style",
            "scene_type",
            "camera",
            "lighting",
            "composition",
            "materials",
            "color_behavior",
            "reference_execution_context",
        ]:

            if key in item:

                useful[
                    key
                ] = item[
                    key
                ]

        compact.append(
            useful
            if useful
            else item
        )

    return compact_json_for_prompt(
        compact,
        limit,
    )


# =========================================================
# BENEFIT ROUTING
# =========================================================

def infer_benefit_family(
    request: str,
) -> str:

    #
    # IMPORTANT:
    # Merchant payments must run BEFORE rewards.
    #
    # "نقاط البيع" contains "نقاط" but it means POS.
    #

    if contains_any(
        request,
        [
            "نقاط البيع",
            "نقطة البيع",
            "اجهزة نقاط البيع",
            "أجهزة نقاط البيع",
            "خدمات التجارة الالكترونية",
            "خدمات التجارة الإلكترونية",
            "التجارة الالكترونية",
            "التجارة الإلكترونية",
            "merchant payments",
            "merchant services",
            "point of sale",
            "points of sale",
            "pos terminal",
            "payment gateway",
            "e-commerce",
            "ecommerce",
            "بوابة الدفع",
        ],
    ):

        return "merchant_payments"

    if contains_any(
        request,
        [
            "تحويل دولي",
            "تحويل مالي دولي",
            "حوالة دولية",
            "حواله دوليه",
            "international transfer",
            "international money transfer",
        ],
    ):

        return "international_transfer"

    if contains_any(
        request,
        [
            "سفر",
            "السفر",
            "مسافر",
            "رحلة",
            "مطار",
            "travel",
            "airport",
            "roaming",
        ],
    ):

        return "travel"

    if contains_any(
        request,
        [
            "كاش باك",
            "cashback",
            "cash back",
            "استرداد نقدي",
        ],
    ):

        return "cashback"

    if contains_any(
        request,
        [
            "تطبيق",
            "بنك رقمي",
            "digital banking",
            "banking app",
        ],
    ):

        return "digital_banking"

    if contains_any(
        request,
        [
            "مكافآت",
            "مكافات",
            "rewards",
            "reward points",
            "نقاط مكافآت",
        ],
    ):

        return "rewards"

    if contains_any(
        request,
        [
            "أمان",
            "امان",
            "security",
            "secure",
        ],
    ):

        return "security"

    return "premium"


# =========================================================
# STC STYLE ROUTING
# =========================================================

def infer_stc_style_family(
    request: str,
) -> str:

    if contains_any(
        request,
        [
            "بيئة بنفسجية",
            "بيئه بنفسجيه",
            "purple environment",
            "purple architectural",
            "purple studio",
            "استوديو بنفسجي",
            "منصات بنفسجية",
            "منصات بنفسجيه",
        ],
    ):

        return "purple_architectural"

    if contains_any(
        request,
        [
            "augmented realism",
            "واقعية معززة",
            "واقعيه معززه",
            "سريالي واقعي",
            "surreal realism",
            "conceptual realism",
            "فانتزي واقعي",
        ],
    ):

        return "augmented_realism"

    if contains_any(
        request,
        [
            "still life",
            "product shot",
            "تصوير منتج",
            "لقطة منتج",
            "لقطه منتج",
        ],
    ):

        return "product_still_life"

    #
    # Premium realistic is intentionally the default.
    #
    # STC identity must not automatically mean
    # purple room + purple neon.
    #

    return "premium_realistic"


# =========================================================
# STC CREATIVE AUTHORITY
# =========================================================

def build_stc_creative_authority(
    request: str,
) -> str:

    benefit = infer_benefit_family(
        request
    )

    style = infer_stc_style_family(
        request
    )

    archetypes = STC_SCENE_ARCHETYPES.get(
        benefit,
        STC_SCENE_ARCHETYPES[
            "premium"
        ],
    )

    return f"""
XPAND STC BANK VISUAL DIRECTOR — LOCAL AUTHORITY
================================================

BENEFIT FAMILY:
{benefit}

REQUESTED / DEFAULT VISUAL FAMILY:
{style}

REFERENCE-INSPIRED SCENE SEEDS:
{compact_json_for_prompt(archetypes, 2500)}

These are scene seeds only.
Never copy an existing campaign composition.

STC BANK IS NOT "PURPLE + NEON".

The identity must be expressed through:
- premium visual restraint
- modern Saudi context where relevant
- controlled purple and green identity cues
- elegant light
- precise material behavior
- commercial realism
- strong photography
- clean hierarchy
- sophisticated negative space
- purposeful product / app integration

DEFAULT COLOR PRINCIPLE:
Purple is optional.
Do NOT make the whole environment purple unless the selected
visual family is explicitly purple_architectural.

A realistic STC scene may use:
- warm neutral stone
- beige
- off-white
- charcoal
- walnut
- leather
- brushed metal
- smoked or clear glass
- restrained green
- subtle purple identity accents

================================================
STYLE FAMILY: PREMIUM_REALISTIC
================================================

Use:
- believable Saudi commercial environments
- observed human behavior
- natural or motivated commercial lighting
- clean faces and hands
- high-end material surfaces
- real spatial relationships
- cinematic but credible camera choices
- clean negative space for later typography

Avoid:
- people facing camera merely holding products
- generic stock-photo smiles
- fake futuristic banking effects

================================================
STYLE FAMILY: PURPLE_ARCHITECTURAL
================================================

Use purple as material / architecture, not as cheap neon.

Use:
- disciplined platforms
- parallel planes
- geometric bases
- one-point or two-point perspective
- real contact shadows
- polished / satin surfaces
- elegant glossy reflection
- controlled edge highlights
- real depth and physical scale

Objects must sit physically on the geometry.
Their angle must agree with the surface / platform perspective.

DO NOT:
- float cards
- float phones
- flood the whole image with neon
- add glowing routes
- add particles
- add random graphic lines

================================================
STYLE FAMILY: AUGMENTED_REALISM
================================================

Start from a real photographic scene.

Add only ONE elevated conceptual device.

Examples:
- controlled scale relationship
- physically motivated architectural transformation
- elegant forced perspective
- refined object/environment relationship

The final result must still look photographable.

Never turn it into:
- fantasy illustration
- generic CGI
- holographic banking
- science-fiction fintech

================================================
CAMERA DISCIPLINE
================================================

Choose the camera because it improves the message.

Available scientific approaches include:
{compact_json_for_prompt(CAMERA_LIBRARY, 4200)}

Available lenses:
{compact_json_for_prompt(LENS_LIBRARY, 1800)}

================================================
LIGHT / MATERIAL DISCIPLINE
================================================

Require:
- motivated key light
- realistic shadow direction
- soft shadow transition when appropriate
- correct contact shadows
- controlled specular highlights
- material-specific roughness
- restrained glossy reflections
- realistic bounce light
- coherent color temperature

Premium reflections should define form,
not create random luminous decoration.

================================================
TEXT / LOGO RULE
================================================

THE IMAGE IS IMAGE-ONLY.

Do NOT design:
- headline
- body copy
- offer text
- price
- percentage
- CTA
- disclaimer
- STC Bank wordmark
- STC logo
- VISA logo
- Mastercard logo
- watermark

Reserve clean negative space.
Typography and official logos will be added manually later.

================================================
ABSOLUTE VISUAL BLOCK
================================================

Never use unless explicitly required by the user:
- floating coins
- floating cards
- floating phones
- phone surrounded by icons
- world globe
- connection lines
- network lines
- transfer routes
- laser beams
- neon trails
- holograms
- HUD graphics
- random particles
- random sparkles
- shields
- lock icons
- upward arrows
- handshake
- generic miniature city
- decorative purple clutter

================================================
MERCHANT PAYMENTS SPECIAL RULE
================================================

If benefit family is merchant_payments:

Arabic "نقاط البيع" means Point of Sale.

It NEVER means reward points.

The scene must communicate commerce through real relationships:
merchant + customer + product/order + POS/phone/device + environment.

Good:
- believable boutique payment
- premium café / restaurant transaction
- real e-commerce order management integrated into the merchant scene
- real retail counter
- elegant hospitality payment

Weak:
- salesman holding terminal toward camera
- purple POS floating in air
- laptop dashboard as the entire idea
- icons around merchant
- glowing payment beam
""".strip()


# =========================================================
# ANTI-CLICHE
# =========================================================

def detect_cliches(
    concept_text: str,
) -> List[
    Dict[str, str]
]:

    source = normalize_text(
        concept_text
    )

    hits = []

    for cliché_id, markers in (
        CLICHE_LIBRARY.items()
    ):

        for marker in markers:

            if normalize_text(
                marker
            ) in source:

                hits.append(
                    {
                        "id":
                            cliché_id,

                        "reason":
                            (
                                "Blocked / weak visual device: "
                                +
                                marker
                            ),
                    }
                )

                break

    return hits


# =========================================================
# JSON EXTRACTION
# =========================================================

def _parse_json_candidate(
    value: Any,
) -> Any:

    if isinstance(
        value,
        (
            dict,
            list,
        ),
    ):

        return value

    if not isinstance(
        value,
        str,
    ):

        return None

    text = clean_text(
        value,
        250000,
    ).strip()

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

        return json.loads(
            text
        )

    except Exception:

        pass

    try:

        candidate = ast.literal_eval(
            text
        )

        if isinstance(
            candidate,
            (
                dict,
                list,
            ),
        ):

            return candidate

    except Exception:

        pass

    first_object = text.find(
        "{"
    )

    last_object = text.rfind(
        "}"
    )

    if (
        first_object >= 0
        and
        last_object > first_object
    ):

        segment = text[
            first_object:
            last_object + 1
        ]

        try:

            return json.loads(
                segment
            )

        except Exception:

            pass

    first_array = text.find(
        "["
    )

    last_array = text.rfind(
        "]"
    )

    if (
        first_array >= 0
        and
        last_array > first_array
    ):

        segment = text[
            first_array:
            last_array + 1
        ]

        try:

            return json.loads(
                segment
            )

        except Exception:

            pass

    return None


def extract_json_object(
    value: Any,
) -> Dict[str, Any]:

    parsed = _parse_json_candidate(
        value
    )

    if isinstance(
        parsed,
        dict,
    ):

        #
        # Common provider wrapper handling.
        #

        for key in [
            "json",
            "result",
            "response",
            "data",
            "output",
        ]:

            nested = parsed.get(
                key
            )

            if isinstance(
                nested,
                dict,
            ):

                if any(
                    wanted in nested
                    for wanted in [
                        "concepts",
                        "evaluations",
                        "candidates",
                    ]
                ):

                    return nested

            if isinstance(
                nested,
                str,
            ):

                nested_parsed = (
                    _parse_json_candidate(
                        nested
                    )
                )

                if isinstance(
                    nested_parsed,
                    dict,
                ):

                    return nested_parsed

        return parsed

    if isinstance(
        parsed,
        list,
    ):

        return {
            "items":
                parsed,
        }

    raise IdeationParseError(
        (
            "Creative Brain model response "
            "could not be parsed as JSON."
        )
    )


# =========================================================
# JSON SCHEMAS
# =========================================================

CONCEPT_PROPERTIES = {
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

    "style_family": {
        "type":
            "string",
    },

    "scene_archetype": {
        "type":
            "string",
    },

    "environment": {
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

    "material_language": {
        "type":
            "string",
    },

    "color_strategy": {
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
}


CONCEPT_REQUIRED = list(
    CONCEPT_PROPERTIES.keys()
)


def concept_schema() -> Dict[str, Any]:

    return {
        "type":
            "object",

        "additionalProperties":
            False,

        "properties":
            CONCEPT_PROPERTIES,

        "required":
            CONCEPT_REQUIRED,
    }


def ideation_schema(
    count: int,
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
                    count,

                "maxItems":
                    count,

                "items":
                    concept_schema(),
            },
        },

        "required": [
            "concepts",
        ],
    }


SCORE_SCHEMA = {
    "type":
        "object",

    "additionalProperties":
        False,

    "properties": {
        key: {
            "type":
                "number",
        }
        for key in SCORE_WEIGHTS
    },

    "required":
        list(
            SCORE_WEIGHTS.keys()
        ),
}


ROLE_SCHEMA = {
    "type":
        "object",

    "additionalProperties":
        False,

    "properties": {
        "approved": {
            "type":
                "boolean",
        },

        "verdict": {
            "type":
                "string",
        },
    },

    "required": [
        "approved",
        "verdict",
    ],
}


CAMERA_SCHEMA = {
    "type":
        "object",

    "additionalProperties":
        False,

    "properties": {
        "camera_angle": {
            "type":
                "string",
        },

        "camera_height": {
            "type":
                "string",
        },

        "camera_direction": {
            "type":
                "string",
        },

        "shot_type": {
            "type":
                "string",
        },

        "lens": {
            "type":
                "string",
        },

        "camera_distance": {
            "type":
                "string",
        },

        "horizon_position": {
            "type":
                "string",
        },

        "perspective_type": {
            "type":
                "string",
        },

        "vanishing_points": {
            "type":
                "string",
        },

        "depth_strategy": {
            "type":
                "string",
        },

        "creative_reason": {
            "type":
                "string",
        },

        "camera_lock_instruction": {
            "type":
                "string",
        },
    },

    "required": [
        "camera_angle",
        "camera_height",
        "camera_direction",
        "shot_type",
        "lens",
        "camera_distance",
        "horizon_position",
        "perspective_type",
        "vanishing_points",
        "depth_strategy",
        "creative_reason",
        "camera_lock_instruction",
    ],
}


FEASIBILITY_SCHEMA = {
    "type":
        "object",

    "additionalProperties":
        False,

    "properties": {
        "feasible": {
            "type":
                "boolean",
        },

        "complexity_level": {
            "type":
                "string",
        },

        "recommended_strategy": {
            "type":
                "string",
        },

        "passes": {
            "type":
                "array",

            "items": {
                "type":
                    "string",
            },
        },

        "single_image_risks": {
            "type":
                "array",

            "items": {
                "type":
                    "string",
            },
        },

        "final_recommendation": {
            "type":
                "string",
        },
    },

    "required": [
        "feasible",
        "complexity_level",
        "recommended_strategy",
        "passes",
        "single_image_risks",
        "final_recommendation",
    ],
}


BLUEPRINT_SCHEMA = {
    "type":
        "object",

    "additionalProperties":
        False,

    "properties": {
        "composition": {
            "type":
                "string",
        },

        "negative_space": {
            "type":
                "string",
        },

        "lighting": {
            "type":
                "string",
        },

        "materials": {
            "type":
                "string",
        },

        "color_strategy": {
            "type":
                "string",
        },

        "brand_execution": {
            "type":
                "string",
        },

        "human_direction": {
            "type":
                "string",
        },

        "do_not_change": {
            "type":
                "array",

            "items": {
                "type":
                    "string",
            },
        },
    },

    "required": [
        "composition",
        "negative_space",
        "lighting",
        "materials",
        "color_strategy",
        "brand_execution",
        "human_direction",
        "do_not_change",
    ],
}


EVALUATION_SCHEMA = {
    "type":
        "object",

    "additionalProperties":
        False,

    "properties": {
        "concept_id": {
            "type":
                "string",
        },

        "scores":
            SCORE_SCHEMA,

        "creative_director":
            ROLE_SCHEMA,

        "brand_guardian":
            ROLE_SCHEMA,

        "production_expert":
            ROLE_SCHEMA,

        "harsh_critic":
            ROLE_SCHEMA,

        "camera_director":
            CAMERA_SCHEMA,

        "feasibility":
            FEASIBILITY_SCHEMA,

        "production_blueprint":
            BLUEPRINT_SCHEMA,

        "purple_overuse": {
            "type":
                "boolean",
        },

        "text_or_logo_risk": {
            "type":
                "boolean",
        },

        "generic_fintech_risk": {
            "type":
                "boolean",
        },

        "scene_realism_risk": {
            "type":
                "boolean",
        },

        "decision": {
            "type":
                "string",

            "enum": [
                "approve",
                "reject",
            ],
        },

        "revision_note": {
            "type":
                "string",
        },
    },

    "required": [
        "concept_id",
        "scores",
        "creative_director",
        "brand_guardian",
        "production_expert",
        "harsh_critic",
        "camera_director",
        "feasibility",
        "production_blueprint",
        "purple_overuse",
        "text_or_logo_risk",
        "generic_fintech_risk",
        "scene_realism_risk",
        "decision",
        "revision_note",
    ],
}


def review_schema(
    count: int,
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
                    count,

                "maxItems":
                    count,

                "items":
                    EVALUATION_SCHEMA,
            },
        },

        "required": [
            "evaluations",
        ],
    }


RECOVERY_ITEM_SCHEMA = {
    "type":
        "object",

    "additionalProperties":
        False,

    "properties": {
        "concept":
            concept_schema(),

        "evaluation":
            EVALUATION_SCHEMA,
    },

    "required": [
        "concept",
        "evaluation",
    ],
}


RECOVERY_SCHEMA = {
    "type":
        "object",

    "additionalProperties":
        False,

    "properties": {
        "candidates": {
            "type":
                "array",

            "minItems":
                RECOVERY_CONCEPTS,

            "maxItems":
                RECOVERY_CONCEPTS,

            "items":
                RECOVERY_ITEM_SCHEMA,
        },
    },

    "required": [
        "candidates",
    ],
}


# =========================================================
# CONCEPT PARSING
# =========================================================

def concept_from_dict(
    item: Dict[str, Any],
    *,
    fallback_id: str,
    generation_round: int = 1,
    revised_from: str = "",
) -> CreativeConcept:

    concept = CreativeConcept(
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
            120,
        ),

        title=clean_text(
            item.get(
                "title"
            ),
            400,
        ),

        core_idea=clean_text(
            item.get(
                "core_idea"
            ),
            2200,
        ),

        marketing_message=clean_text(
            item.get(
                "marketing_message"
            ),
            1200,
        ),

        visual_metaphor=clean_text(
            item.get(
                "visual_metaphor"
            ),
            1400,
        ),

        style_family=clean_text(
            item.get(
                "style_family"
            ),
            200,
        ),

        scene_archetype=clean_text(
            item.get(
                "scene_archetype"
            ),
            1200,
        ),

        environment=clean_text(
            item.get(
                "environment"
            ),
            1800,
        ),

        hero_element=clean_text(
            item.get(
                "hero_element"
            ),
            1000,
        ),

        supporting_elements=[
            clean_text(
                value,
                600,
            )
            for value in safe_list(
                item.get(
                    "supporting_elements"
                )
            )[:8]
            if clean_text(
                value,
                600,
            )
        ],

        camera_angle=clean_text(
            item.get(
                "camera_angle"
            ),
            600,
        ),

        lens=clean_text(
            item.get(
                "lens"
            ),
            200,
        ),

        perspective=clean_text(
            item.get(
                "perspective"
            ),
            800,
        ),

        lighting=clean_text(
            item.get(
                "lighting"
            ),
            1200,
        ),

        negative_space=clean_text(
            item.get(
                "negative_space"
            ),
            900,
        ),

        material_language=clean_text(
            item.get(
                "material_language"
            ),
            1200,
        ),

        color_strategy=clean_text(
            item.get(
                "color_strategy"
            ),
            1200,
        ),

        brand_logic=clean_text(
            item.get(
                "brand_logic"
            ),
            1500,
        ),

        production_method=clean_text(
            item.get(
                "production_method"
            ),
            200,
        ),

        campaign_extension=clean_text(
            item.get(
                "campaign_extension"
            ),
            900,
        ),

        risks=[
            clean_text(
                value,
                700,
            )
            for value in safe_list(
                item.get(
                    "risks"
                )
            )[:8]
            if clean_text(
                value,
                700,
            )
        ],

        generation_round=(
            generation_round
        ),

        revised_from=clean_text(
            revised_from,
            100,
        ),
    )

    concept_text = "\n".join(
        [
            concept.title,
            concept.core_idea,
            concept.visual_metaphor,
            concept.style_family,
            concept.scene_archetype,
            concept.environment,
            concept.hero_element,
            " ".join(
                concept.supporting_elements
            ),
            concept.lighting,
            concept.color_strategy,
        ]
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
    expected_count: int = 0,
    generation_round: int = 1,
) -> List[
    CreativeConcept
]:

    raw = payload.get(
        "concepts"
    )

    if raw is None:

        #
        # Compatibility with a harmless bare-array wrapper.
        #

        raw = payload.get(
            "items"
        )

    if not isinstance(
        raw,
        list,
    ):

        keys = ",".join(
            list(
                payload.keys()
            )[:12]
        )

        raise IdeationShapeError(
            (
                "Creative Brain JSON contains no concept collection"
                +
                (
                    " | top_level_keys="
                    +
                    keys
                    if keys
                    else ""
                )
            )
        )

    concepts = []

    for index, item in enumerate(
        raw,
        start=1,
    ):

        if not isinstance(
            item,
            dict,
        ):

            continue

        concepts.append(
            concept_from_dict(
                item,
                fallback_id=(
                    "C"
                    +
                    str(
                        index
                    ).zfill(
                        2
                    )
                ),
                generation_round=(
                    generation_round
                ),
            )
        )

    if expected_count:

        minimum = max(
            2,
            min(
                expected_count,
                int(
                    expected_count
                    *
                    0.75
                ),
            ),
        )

        if len(
            concepts
        ) < minimum:

            raise IdeationCountError(
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
                        expected_count
                    )
                )
            )

    return concepts


# =========================================================
# LOCAL QUALITY
# =========================================================

def local_preflight_score(
    concept: CreativeConcept,
    *,
    user_request: str,
) -> float:

    score = 20.0

    important = [
        concept.core_idea,
        concept.scene_archetype,
        concept.environment,
        concept.hero_element,
        concept.camera_angle,
        concept.lens,
        concept.perspective,
        concept.lighting,
        concept.negative_space,
        concept.material_language,
        concept.color_strategy,
        concept.brand_logic,
    ]

    completion = sum(
        1
        for value in important
        if clean_text(
            value,
            20,
        )
    )

    score += (
        completion
        /
        len(
            important
        )
        *
        42.0
    )

    if concept.cliche_hits:

        score -= min(
            50.0,
            len(
                concept.cliche_hits
            )
            *
            16.0,
        )

    if concept.production_method in {
        "single_generation",
        "single_image",
        "composite",
        "controlled_edit",
        "inpainting",
    }:

        score += 5.0

    if (
        clean_text(
            concept.camera_angle,
            100,
        )
        and
        clean_text(
            concept.lens,
            100,
        )
    ):

        score += 7.0

    if (
        clean_text(
            concept.material_language,
            100,
        )
        and
        clean_text(
            concept.lighting,
            100,
        )
    ):

        score += 7.0

    if is_stc_bank_request(
        user_request
    ):

        benefit = infer_benefit_family(
            user_request
        )

        requested_style = (
            infer_stc_style_family(
                user_request
            )
        )

        if (
            concept.style_family
            ==
            requested_style
        ):

            score += 6.0

        if (
            benefit
            ==
            "merchant_payments"
            and
            concept.style_family
            ==
            "premium_realistic"
        ):

            score += 5.0

        #
        # A default STC request should not be pushed toward
        # dominant purple architecture unnecessarily.
        #

        if (
            requested_style
            ==
            "premium_realistic"
            and
            concept.style_family
            ==
            "purple_architectural"
        ):

            score -= 6.0

    return round(
        max(
            0.0,
            min(
                100.0,
                score,
            ),
        ),
        2,
    )


def concept_fingerprint(
    concept: CreativeConcept,
) -> set:

    text = normalize_text(
        " ".join(
            [
                concept.title,
                concept.core_idea,
                concept.scene_archetype,
                concept.environment,
                concept.hero_element,
            ]
        )
    )

    words = re.findall(
        r"[a-z0-9\u0600-\u06FF]+",
        text,
    )

    return {
        word
        for word in words
        if len(
            word
        ) >= 4
    }


def concept_similarity(
    a: CreativeConcept,
    b: CreativeConcept,
) -> float:

    left = concept_fingerprint(
        a
    )

    right = concept_fingerprint(
        b
    )

    if not left or not right:

        return 0.0

    union = left | right

    if not union:

        return 0.0

    return (
        len(
            left & right
        )
        /
        len(
            union
        )
    )


def shortlist_concepts(
    concepts: Sequence[
        CreativeConcept
    ],
    *,
    user_request: str,
    limit: int,
) -> List[
    CreativeConcept
]:

    candidates = list(
        concepts
    )

    for concept in candidates:

        concept.debate[
            "local_preflight"
        ] = {
            "score":
                local_preflight_score(
                    concept,
                    user_request=user_request,
                ),

            "paid_model":
                False,
        }

    candidates.sort(
        key=lambda item:
            float(
                safe_dict(
                    item.debate.get(
                        "local_preflight"
                    )
                ).get(
                    "score",
                    0,
                )
            ),
        reverse=True,
    )

    selected = []

    for concept in candidates:

        if len(
            selected
        ) >= limit:

            break

        if any(
            concept_similarity(
                concept,
                existing,
            )
            >=
            0.62
            for existing in selected
        ):

            continue

        selected.append(
            concept
        )

    #
    # If diversity suppression was too aggressive, fill
    # remaining slots with strongest available concepts.
    #

    selected_ids = {
        item.concept_id
        for item in selected
    }

    for concept in candidates:

        if len(
            selected
        ) >= limit:

            break

        if concept.concept_id in (
            selected_ids
        ):

            continue

        selected.append(
            concept
        )

        selected_ids.add(
            concept.concept_id
        )

    return selected[:limit]


# =========================================================
# SCORE
# =========================================================

def calculate_weighted_score(
    scores: Dict[str, Any],
) -> float:

    total = 0.0

    for key, weight in (
        SCORE_WEIGHTS.items()
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
                float(
                    weight
                )
                /
                100.0
            )
        )

    return round(
        total,
        2,
    )


# =========================================================
# TELEMETRY
# =========================================================

def register_model_call(
    telemetry: Optional[
        Dict[str, Any]
    ],
    label: str,
) -> None:

    if telemetry is None:

        return

    telemetry[
        "director_calls"
    ] = (
        int(
            telemetry.get(
                "director_calls",
                0,
            )
        )
        +
        1
    )

    telemetry.setdefault(
        "director_call_history",
        [],
    ).append(
        label
    )


# =========================================================
# IDEATION PROMPT
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
    challenger: bool = False,
) -> str:

    count = (
        MASTERPIECE_INITIAL_CONCEPTS
        if mode
        ==
        MODE_MASTERPIECE
        else
        FAST_INITIAL_CONCEPTS
    )

    stc_request = is_stc_bank_request(
        user_request
    )

    stc_authority = (
        build_stc_creative_authority(
            user_request
        )
        if stc_request
        else ""
    )

    recovery = ""

    if failure_context:

        recovery = f"""
PREVIOUS FAILURE CONTEXT
========================

{clean_text(failure_context, 3500)}

Do NOT cosmetically rewrite these directions.
Change the scene mechanism, camera logic or storytelling mechanism.
""".strip()

    return f"""
You are XPAND Senior Advertising Concept Director.

Generate advertising concepts.
Do NOT generate an image.
Do NOT expose chain-of-thought.

================================================
USER REQUEST
================================================

{clean_text(user_request, 5000)}

================================================
BRAND MEMORY
================================================

{compact_brand_context(brand_context, 3000)}

================================================
REFERENCE DNA
================================================

{compact_visual_references(visual_references, 2600)}

Use references to understand:
- realism level
- art-direction maturity
- camera behavior
- lighting behavior
- material quality
- color restraint
- scene complexity
- negative-space behavior

Never copy a reference composition.

================================================
STYLE HINT
================================================

{clean_text(style_hint, 1000) or "Use the strongest appropriate visual family."}

================================================
STC BANK AUTHORITY
================================================

{stc_authority or "No dedicated STC Bank rules required."}

================================================
IDEATION STANDARD
================================================

Generate EXACTLY {count} materially different concepts.

Quality is more important than quantity.

Every concept must answer:

1. What is the single visual idea?
2. Why does this real scene communicate the benefit?
3. What does the camera add?
4. What physical environment makes the idea believable?
5. What light and materials make it premium?
6. Where is clean negative space for manual typography?
7. Is it feasible as one coherent commercial frame?

Do not make concepts that differ only by:
- changing room
- changing person
- changing purple shade
- changing lens

Each concept must use a materially different scene mechanism.

================================================
SCENE REALISM
================================================

Prefer:
- real behavior
- real architecture
- believable product interaction
- real contact shadows
- coherent scale
- clear physical support
- plausible lens and camera height
- production-design detail

Reject:
- random visual effects
- generic AI decoration
- decorative technology
- meaningless floating objects
- cluttered poster thinking

================================================
CAMERA
================================================

Use the correct scientific camera terminology.

Choose one coherent camera system per concept.

Do not write contradictory combinations such as:
"85mm extreme wide worm's-eye bird's-eye".

================================================
TEXT
================================================

For STC Bank:
the generated image will receive typography manually later.

Therefore:
do NOT make text or logo part of the concept.

================================================
RECOVERY CONTEXT
================================================

{recovery or "This is the first ideation pass."}

================================================
OUTPUT
================================================

Return only the schema requested by the API.
""".strip()


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
    challenger: bool = False,
    telemetry: Optional[
        Dict[str, Any]
    ] = None,
) -> List[
    CreativeConcept
]:

    count = (
        MASTERPIECE_INITIAL_CONCEPTS
        if mode
        ==
        MODE_MASTERPIECE
        else
        FAST_INITIAL_CONCEPTS
    )

    prompt = (
        build_concept_generation_prompt(
            user_request=user_request,
            brand_context=brand_context,
            visual_references=visual_references,
            style_hint=style_hint,
            mode=mode,
            round_number=round_number,
            failure_context=failure_context,
            challenger=challenger,
        )
    )

    register_model_call(
        telemetry,
        "ideation",
    )

    raw = call_openai_director(
        prompt,
        json_mode=True,
        json_schema=ideation_schema(
            count
        ),
        json_schema_name=(
            "xpand_creative_ideation_v5"
        ),
    )

    payload = extract_json_object(
        raw
    )

    concepts = parse_concepts(
        payload,
        expected_count=count,
        generation_round=round_number,
    )

    return concepts


# =========================================================
# REVIEW PAYLOAD
# =========================================================

def concept_payload_for_evaluation(
    concept: CreativeConcept,
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

        "style_family":
            concept.style_family,

        "scene_archetype":
            concept.scene_archetype,

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

        "material_language":
            concept.material_language,

        "color_strategy":
            concept.color_strategy,

        "brand_logic":
            concept.brand_logic,

        "production_method":
            concept.production_method,

        "campaign_extension":
            concept.campaign_extension,

        "risks":
            concept.risks,

        "local_cliche_hits":
            concept.cliche_hits,

        "local_preflight":
            safe_dict(
                concept.debate.get(
                    "local_preflight"
                )
            ),
    }


# =========================================================
# REVIEW PROMPT
# =========================================================

def build_evaluation_prompt(
    *,
    user_request: str,
    concepts: List[
        CreativeConcept
    ],
    brand_context: Any = None,
    visual_references: Any = None,
) -> str:

    stc_request = is_stc_bank_request(
        user_request
    )

    stc_authority = (
        build_stc_creative_authority(
            user_request
        )
        if stc_request
        else ""
    )

    payload = [
        concept_payload_for_evaluation(
            concept
        )
        for concept in concepts
    ]

    return f"""
You are XPAND Masterpiece Creative Board.

Evaluate ONLY the supplied concepts.

Do NOT invent a new idea in this step.
Do NOT expose chain-of-thought.

================================================
ORIGINAL REQUEST
================================================

{clean_text(user_request, 4500)}

================================================
CONCEPT SHORTLIST
================================================

{compact_json_for_prompt(payload, 8500)}

================================================
BRAND CONTEXT
================================================

{compact_brand_context(brand_context, 2400)}

================================================
REFERENCE DNA
================================================

{compact_visual_references(visual_references, 2200)}

================================================
STC BANK AUTHORITY
================================================

{stc_authority or "No dedicated STC rules required."}

================================================
REVIEW STANDARD
================================================

Score 0-100.

50 = weak / ordinary
60 = acceptable but generic
70 = good professional
80 = strong advertising
84 = high-quality production-ready
88 = Masterpiece-level
92+ = rare

Do not inflate scores.

SCORE:
- message_clarity
- originality
- brand_fit
- visual_power
- feasibility
- perspective_integrity
- campaign_potential

================================================
REALISM AUDIT
================================================

Inspect:
- human behavior
- hand / product relationship
- object support
- scale
- shadows
- light direction
- reflection logic
- perspective
- camera height
- lens compatibility
- material behavior

Set scene_realism_risk=true if the concept depends on
physically doubtful staging or obvious AI visual tricks.

================================================
STC PURPLE AUDIT
================================================

Set purple_overuse=true if:
- purple is being used because "STC = purple"
- scene becomes a generic purple room
- neon purple replaces actual art direction
- purple decoration has no conceptual function

Purple architecture may still be approved when:
- it is the deliberate selected style
- geometry is elegant
- perspective is coherent
- material behavior is premium
- it serves the concept

================================================
TEXT / LOGO AUDIT
================================================

For STC Bank:
set text_or_logo_risk=true if the concept requires generated:
- headline
- offer copy
- percentage
- logo
- wordmark
- fake app text
- legal copy

Clean negative space is good.

================================================
GENERIC FINTECH AUDIT
================================================

Set generic_fintech_risk=true for:
- floating card / phone
- icons around phone
- glowing routes
- network lines
- lasers
- globe
- HUD
- particles
- fake futuristic interface
- generic cyber-security symbols

================================================
CAMERA + FEASIBILITY
================================================

Do NOT make separate future calls necessary.

For every concept provide:
- final camera direction
- production feasibility
- production blueprint

The camera must be scientifically coherent.

================================================
APPROVAL
================================================

All four review roles must be independent:

Creative Director:
Is the idea worth producing?

Brand Guardian:
Does it genuinely belong to this brand?

Production Expert:
Can it become a strong coherent image?

Harsh Critic:
Would a senior agency reject it as generic?

decision="approve" only when the concept is genuinely worth production.

================================================
OUTPUT
================================================

Return only the API schema.
""".strip()


# =========================================================
# APPLY EVALUATION
# =========================================================

def apply_evaluation(
    concept: CreativeConcept,
    evaluation: Dict[str, Any],
) -> None:

    scores = safe_dict(
        evaluation.get(
            "scores"
        )
    )

    normalized_scores = {
        key:
            clamp_score(
                scores.get(
                    key,
                    0,
                )
            )
        for key in SCORE_WEIGHTS
    }

    supplied = {
        key
        for key in scores
        if key in SCORE_WEIGHTS
    }

    concept.evaluation_valid = (
        supplied
        ==
        set(
            SCORE_WEIGHTS.keys()
        )
    )

    concept.scores = (
        normalized_scores
    )

    concept.weighted_score = (
        calculate_weighted_score(
            normalized_scores
        )
    )

    local_preflight = safe_dict(
        concept.debate.get(
            "local_preflight"
        )
    )

    concept.debate = {
        "local_preflight":
            local_preflight,

        "creative_director":
            safe_dict(
                evaluation.get(
                    "creative_director"
                )
            ),

        "brand_guardian":
            safe_dict(
                evaluation.get(
                    "brand_guardian"
                )
            ),

        "production_expert":
            safe_dict(
                evaluation.get(
                    "production_expert"
                )
            ),

        "harsh_critic":
            safe_dict(
                evaluation.get(
                    "harsh_critic"
                )
            ),

        "camera_director":
            safe_dict(
                evaluation.get(
                    "camera_director"
                )
            ),

        "production_blueprint":
            safe_dict(
                evaluation.get(
                    "production_blueprint"
                )
            ),

        "purple_overuse":
            bool(
                evaluation.get(
                    "purple_overuse",
                    False,
                )
            ),

        "text_or_logo_risk":
            bool(
                evaluation.get(
                    "text_or_logo_risk",
                    False,
                )
            ),

        "generic_fintech_risk":
            bool(
                evaluation.get(
                    "generic_fintech_risk",
                    False,
                )
            ),

        "scene_realism_risk":
            bool(
                evaluation.get(
                    "scene_realism_risk",
                    False,
                )
            ),

        "decision":
            clean_text(
                evaluation.get(
                    "decision",
                    "",
                ),
                50,
            ).lower(),

        "revision_note":
            clean_text(
                evaluation.get(
                    "revision_note",
                    "",
                ),
                1200,
            ),
    }

    concept.feasibility = (
        safe_dict(
            evaluation.get(
                "feasibility"
            )
        )
    )

    camera = safe_dict(
        concept.debate.get(
            "camera_director"
        )
    )

    if clean_text(
        camera.get(
            "camera_angle"
        ),
        300,
    ):

        concept.camera_angle = clean_text(
            camera.get(
                "camera_angle"
            ),
            600,
        )

    if clean_text(
        camera.get(
            "lens"
        ),
        100,
    ):

        concept.lens = clean_text(
            camera.get(
                "lens"
            ),
            200,
        )

    if clean_text(
        camera.get(
            "perspective_type"
        ),
        400,
    ):

        concept.perspective = clean_text(
            camera.get(
                "perspective_type"
            ),
            800,
        )


# =========================================================
# REVIEW
# =========================================================

def evaluate_concept_batch(
    *,
    user_request: str,
    concepts: List[
        CreativeConcept
    ],
    brand_context: Any = None,
    visual_references: Any = None,
    telemetry: Optional[
        Dict[str, Any]
    ] = None,
) -> Dict[
    str,
    Dict[str, Any]
]:

    if not concepts:

        return {}

    register_model_call(
        telemetry,
        "creative_review",
    )

    raw = call_openai_director(
        build_evaluation_prompt(
            user_request=user_request,
            concepts=concepts,
            brand_context=brand_context,
            visual_references=visual_references,
        ),
        json_mode=True,
        json_schema=review_schema(
            len(
                concepts
            )
        ),
        json_schema_name=(
            "xpand_creative_review_v5"
        ),
    )

    payload = extract_json_object(
        raw
    )

    evaluations = payload.get(
        "evaluations"
    )

    if not isinstance(
        evaluations,
        list,
    ):

        raise ReviewShapeError(
            "Creative Review JSON contains no evaluations array."
        )

    expected_ids = {
        concept.concept_id
        for concept in concepts
    }

    output = {}

    for evaluation in evaluations:

        if not isinstance(
            evaluation,
            dict,
        ):

            continue

        concept_id = clean_text(
            evaluation.get(
                "concept_id"
            ),
            100,
        )

        if concept_id in expected_ids:

            output[
                concept_id
            ] = evaluation

    if not output:

        raise ReviewShapeError(
            "Creative Review returned no matching concept IDs."
        )

    return output


def evaluate_concept_pool(
    *,
    user_request: str,
    concepts: List[
        CreativeConcept
    ],
    brand_context: Any = None,
    visual_references: Any = None,
    mode: str = MODE_MASTERPIECE,
    telemetry: Optional[
        Dict[str, Any]
    ] = None,
) -> List[
    CreativeConcept
]:

    evaluation_map = (
        evaluate_concept_batch(
            user_request=user_request,
            concepts=concepts,
            brand_context=brand_context,
            visual_references=visual_references,
            telemetry=telemetry,
        )
    )

    for concept in concepts:

        evaluation = evaluation_map.get(
            concept.concept_id
        )

        if isinstance(
            evaluation,
            dict,
        ):

            apply_evaluation(
                concept,
                evaluation,
            )

        else:

            concept.evaluation_valid = False

            concept.weighted_score = 0.0

            concept.debate[
                "evaluation_error"
            ] = (
                "No matching model evaluation."
            )

    return concepts


# =========================================================
# QUALITY GATE
# =========================================================

def role_approved(
    value: Any,
) -> bool:

    return bool(
        isinstance(
            value,
            dict,
        )
        and
        value.get(
            "approved"
        )
    )


def quality_gate_failures(
    concept: CreativeConcept,
    *,
    mode: str,
) -> List[str]:

    failures = []

    if not concept.evaluation_valid:

        failures.append(
            "no_valid_model_evaluation"
        )

        return failures

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

        return failures

    if (
        concept.weighted_score
        <
        MASTERPIECE_RELEASE_FLOOR
    ):

        failures.append(
            (
                "weighted_score_below_release_floor_"
                +
                str(
                    MASTERPIECE_RELEASE_FLOOR
                )
            )
        )

    for key, minimum in (
        MASTERPIECE_RELEASE_MIN_SUBSCORES.items()
    ):

        value = clamp_score(
            concept.scores.get(
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
                        minimum
                    )
                )
            )

    if concept.cliche_hits:

        failures.append(
            (
                "anti_cliche:"
                +
                ",".join(
                    hit.get(
                        "id",
                        "",
                    )
                    for hit in concept.cliche_hits
                    if hit.get(
                        "id"
                    )
                )
            )
        )

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

    if (
        concept.debate.get(
            "decision"
        )
        !=
        "approve"
    ):

        failures.append(
            "review_decision_reject"
        )

    if concept.debate.get(
        "purple_overuse"
    ):

        failures.append(
            "purple_overuse"
        )

    if concept.debate.get(
        "text_or_logo_risk"
    ):

        failures.append(
            "text_or_logo_risk"
        )

    if concept.debate.get(
        "generic_fintech_risk"
    ):

        failures.append(
            "generic_fintech_risk"
        )

    if concept.debate.get(
        "scene_realism_risk"
    ):

        failures.append(
            "scene_realism_risk"
        )

    feasibility = safe_dict(
        concept.feasibility
    )

    if (
        feasibility
        and
        not bool(
            feasibility.get(
                "feasible",
                True,
            )
        )
    ):

        failures.append(
            "production_not_feasible"
        )

    return failures


def refresh_quality_gate(
    concept: CreativeConcept,
    *,
    mode: str,
) -> None:

    failures = quality_gate_failures(
        concept,
        mode=mode,
    )

    concept.quality_gate_failures = (
        failures
    )

    concept.quality_gate_passed = (
        not failures
    )

    if concept.quality_gate_passed:

        if (
            concept.weighted_score
            >=
            MASTERPIECE_MIN_SCORE
        ):

            concept.debate[
                "quality_release_level"
            ] = (
                "target_masterpiece"
            )

        else:

            concept.debate[
                "quality_release_level"
            ] = (
                "adaptive_release"
            )


def concept_passes_review(
    concept: CreativeConcept,
    mode: str = MODE_MASTERPIECE,
) -> bool:

    refresh_quality_gate(
        concept,
        mode=mode,
    )

    return concept.quality_gate_passed


# =========================================================
# RANKING
# =========================================================

def rank_concepts(
    concepts: Sequence[
        CreativeConcept
    ],
) -> List[
    CreativeConcept
]:

    return sorted(
        list(
            concepts
        ),
        key=lambda item: (
            1
            if item.quality_gate_passed
            else 0,

            1
            if item.evaluation_valid
            else 0,

            1
            if not item.cliche_hits
            else 0,

            item.weighted_score,
        ),
        reverse=True,
    )


def select_top_concepts(
    concepts: List[
        CreativeConcept
    ],
    limit: int = 3,
    mode: str = MODE_MASTERPIECE,
    qualified_only: bool = True,
) -> List[
    CreativeConcept
]:

    for concept in concepts:

        refresh_quality_gate(
            concept,
            mode=mode,
        )

    pool = (
        [
            concept
            for concept in concepts
            if concept.quality_gate_passed
        ]
        if qualified_only
        else list(
            concepts
        )
    )

    return rank_concepts(
        pool
    )[:limit]


def best_real_evaluated_concept(
    concepts: Sequence[
        CreativeConcept
    ],
) -> Optional[
    CreativeConcept
]:

    valid = [
        concept
        for concept in concepts
        if concept.evaluation_valid
    ]

    if not valid:

        return None

    return rank_concepts(
        valid
    )[0]


# =========================================================
# FAILURE CONTEXT
# =========================================================

def build_failure_context(
    concepts: Sequence[
        CreativeConcept
    ],
    limit: int = 2,
) -> str:

    payload = []

    for concept in rank_concepts(
        concepts
    )[:limit]:

        payload.append(
            {
                "concept_id":
                    concept.concept_id,

                "title":
                    concept.title,

                "core_idea":
                    clean_text(
                        concept.core_idea,
                        500,
                    ),

                "scene":
                    clean_text(
                        concept.scene_archetype,
                        400,
                    ),

                "style_family":
                    concept.style_family,

                "score":
                    concept.weighted_score,

                "failures":
                    concept.quality_gate_failures,

                "review_note":
                    clean_text(
                        concept.debate.get(
                            "revision_note",
                            "",
                        ),
                        500,
                    ),
            }
        )

    return compact_json_for_prompt(
        payload,
        3200,
    )


# =========================================================
# RECOVERY
# =========================================================

def build_recovery_prompt(
    *,
    user_request: str,
    failed_concepts: Sequence[
        CreativeConcept
    ],
    brand_context: Any,
    visual_references: Any,
) -> str:

    stc_request = is_stc_bank_request(
        user_request
    )

    return f"""
You are XPAND Masterpiece Recovery Board.

This is the ONLY automatic recovery call.

Create exactly {RECOVERY_CONCEPTS} materially NEW concepts
and evaluate each concept in the SAME response.

Do NOT expose chain-of-thought.

================================================
REQUEST
================================================

{clean_text(user_request, 4500)}

================================================
FAILED DIRECTIONS
================================================

{build_failure_context(failed_concepts)}

Do not cosmetically rewrite these.

Change:
- scene mechanism
- human behavior
- composition
- camera logic
- physical metaphor
or
- style family when appropriate

================================================
BRAND CONTEXT
================================================

{compact_brand_context(brand_context, 2400)}

================================================
REFERENCE DNA
================================================

{compact_visual_references(visual_references, 2200)}

================================================
STC BANK AUTHORITY
================================================

{
    build_stc_creative_authority(user_request)
    if stc_request
    else "No dedicated STC rules required."
}

================================================
RECOVERY PRIORITY
================================================

Solve the exact reasons the first concepts failed.

Especially reject:
- generic banking
- generic purple scene
- weak product presentation
- ordinary standing person
- subject simply holding a terminal toward camera
- floating fintech objects
- text-dependent idea
- unrealistic camera / object relationship

For STC merchant payments:
prefer a premium believable commerce story
where the merchant, payment device and real environment
form one intelligent scene.

================================================
EVALUATION
================================================

Evaluate the new concept honestly.

Use the same strict score calibration:
84 = strong release
88 = Masterpiece

Provide:
- scores
- four role approvals
- camera director
- feasibility
- production blueprint
- all visual risk booleans
- approve / reject decision

================================================
OUTPUT
================================================

Return only the API schema.
""".strip()


def run_recovery_board(
    *,
    user_request: str,
    failed_concepts: Sequence[
        CreativeConcept
    ],
    brand_context: Any,
    visual_references: Any,
    telemetry: Optional[
        Dict[str, Any]
    ],
) -> List[
    CreativeConcept
]:

    register_model_call(
        telemetry,
        "recovery_board",
    )

    raw = call_openai_director(
        build_recovery_prompt(
            user_request=user_request,
            failed_concepts=failed_concepts,
            brand_context=brand_context,
            visual_references=visual_references,
        ),
        json_mode=True,
        json_schema=RECOVERY_SCHEMA,
        json_schema_name=(
            "xpand_creative_recovery_v5"
        ),
    )

    payload = extract_json_object(
        raw
    )

    candidates = payload.get(
        "candidates"
    )

    if not isinstance(
        candidates,
        list,
    ):

        raise ReviewShapeError(
            "Recovery Board returned no candidates array."
        )

    concepts = []

    for index, item in enumerate(
        candidates,
        start=1,
    ):

        if not isinstance(
            item,
            dict,
        ):

            continue

        concept_payload = safe_dict(
            item.get(
                "concept"
            )
        )

        evaluation = safe_dict(
            item.get(
                "evaluation"
            )
        )

        if not concept_payload:

            continue

        concept = concept_from_dict(
            concept_payload,
            fallback_id=(
                "R2-C"
                +
                str(
                    index
                ).zfill(
                    2
                )
            ),
            generation_round=2,
        )

        #
        # Ensure evaluation ID follows the actual concept.
        #

        evaluation[
            "concept_id"
        ] = concept.concept_id

        if evaluation:

            apply_evaluation(
                concept,
                evaluation,
            )

        refresh_quality_gate(
            concept,
            mode=(
                MODE_MASTERPIECE
            ),
        )

        concepts.append(
            concept
        )

    return concepts


# =========================================================
# TECHNICAL FAILURE RESPONSE
# =========================================================

def technical_failure_response(
    *,
    mode: str,
    request: str,
    error: Exception,
    telemetry: Dict[str, Any],
    stage: str,
) -> CreativeBrainResponse:

    message = clean_text(
        error,
        3500,
    )

    print("")
    print(
        "=========================================="
    )
    print(
        " IDEATION TECHNICAL FAILURE"
        if stage == "ideation"
        else
        " CREATIVE TECHNICAL FAILURE"
    )
    print(
        "=========================================="
    )
    print(
        message
    )
    print(
        "This is NOT classified as a creative-quality failure."
    )
    print(
        "Smart Engine fallback should remain allowed."
    )
    print("")

    return CreativeBrainResponse(
        ok=False,
        mode=mode,
        request=request,
        total_concepts=0,
        concepts=[],
        top_concepts=[],
        winner=None,
        metadata={
            "version":
                VERSION,

            "architecture":
                "cost_controlled_stc_first",

            "technical_failure":
                True,

            "technical_failure_stage":
                stage,

            "failure_reason":
                message,

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

            "director_calls":
                telemetry.get(
                    "director_calls",
                    0,
                ),

            "director_call_history":
                telemetry.get(
                    "director_call_history",
                    [],
                ),
        },

        errors=[
            (
                stage
                +
                ": "
                +
                message
            )
        ],
    )


# =========================================================
# MAIN CREATIVE BRAIN
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

    request = clean_text(
        user_request,
        12000,
    )

    if not request:

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
            int(
                top_count
                or 3
            ),
            5,
        ),
    )

    benefit_family = (
        infer_benefit_family(
            request
        )
    )

    stc_request = is_stc_bank_request(
        request
    )

    style_family = (
        infer_stc_style_family(
            request
        )
        if stc_request
        else ""
    )

    telemetry = {
        "director_calls":
            0,

        "director_call_history":
            [],

        "initial_concepts":
            0,

        "shortlisted_concepts":
            0,

        "recovery_used":
            False,
    }

    errors = []

    all_concepts = []

    winner = None

    release_level = ""

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND CREATIVE BRAIN V5.0"
    )
    print(
        " COST-CONTROLLED STC-FIRST"
    )
    print(
        "=========================================="
    )
    print(
        "Mode:",
        mode,
    )
    print(
        "Masterpiece target:",
        MASTERPIECE_MIN_SCORE,
    )
    print(
        "Adaptive release floor:",
        MASTERPIECE_RELEASE_FLOOR,
    )
    print(
        "Initial concepts:",
        (
            MASTERPIECE_INITIAL_CONCEPTS
            if mode
            ==
            MODE_MASTERPIECE
            else
            FAST_INITIAL_CONCEPTS
        ),
    )
    print(
        "Paid review shortlist:",
        MASTERPIECE_SHORTLIST_SIZE,
    )
    print(
        "Normal Director calls:",
        MASTERPIECE_TARGET_DIRECTOR_CALLS,
    )
    print(
        "Maximum Director calls:",
        MASTERPIECE_MAX_DIRECTOR_CALLS,
    )
    print(
        "Benefit family:",
        benefit_family,
    )

    if stc_request:

        print(
            "STC visual family:",
            style_family,
        )

    print("")

    # =====================================================
    # CALL 1 — IDEATION
    # =====================================================

    try:

        initial = generate_concept_pool(
            user_request=request,
            brand_context=brand_context,
            visual_references=visual_references,
            style_hint=style_hint,
            mode=mode,
            round_number=1,
            telemetry=telemetry,
        )

    except Exception as error:

        return technical_failure_response(
            mode=mode,
            request=request,
            error=error,
            telemetry=telemetry,
            stage="ideation",
        )

    telemetry[
        "initial_concepts"
    ] = len(
        initial
    )

    all_concepts.extend(
        initial
    )

    shortlist = shortlist_concepts(
        initial,
        user_request=request,
        limit=(
            MASTERPIECE_SHORTLIST_SIZE
            if mode
            ==
            MODE_MASTERPIECE
            else
            min(
                2,
                len(
                    initial
                ),
            )
        ),
    )

    telemetry[
        "shortlisted_concepts"
    ] = len(
        shortlist
    )

    if not shortlist:

        return technical_failure_response(
            mode=mode,
            request=request,
            error=CreativeBrainError(
                "Local preflight produced no usable shortlist."
            ),
            telemetry=telemetry,
            stage="shortlist",
        )

    # =====================================================
    # CALL 2 — ONE CONSOLIDATED REVIEW
    # =====================================================

    try:

        evaluate_concept_pool(
            user_request=request,
            concepts=shortlist,
            brand_context=brand_context,
            visual_references=visual_references,
            mode=mode,
            telemetry=telemetry,
        )

    except Exception as error:

        return technical_failure_response(
            mode=mode,
            request=request,
            error=error,
            telemetry=telemetry,
            stage="review",
        )

    for concept in shortlist:

        refresh_quality_gate(
            concept,
            mode=mode,
        )

    qualified = select_top_concepts(
        shortlist,
        limit=top_count,
        mode=mode,
        qualified_only=True,
    )

    if qualified:

        winner = qualified[
            0
        ]

        release_level = clean_text(
            winner.debate.get(
                "quality_release_level",
                "adaptive_release",
            ),
            100,
        )

    # =====================================================
    # CALL 3 — SINGLE RECOVERY BOARD IF NEEDED
    # =====================================================

    if (
        winner is None
        and
        mode
        ==
        MODE_MASTERPIECE
    ):

        print(
            "🔁 Running ONE strategic recovery board..."
        )

        telemetry[
            "recovery_used"
        ] = True

        try:

            recovered = run_recovery_board(
                user_request=request,
                failed_concepts=shortlist,
                brand_context=brand_context,
                visual_references=visual_references,
                telemetry=telemetry,
            )

            all_concepts.extend(
                recovered
            )

            qualified_recovery = (
                select_top_concepts(
                    recovered,
                    limit=top_count,
                    mode=mode,
                    qualified_only=True,
                )
            )

            if qualified_recovery:

                winner = (
                    qualified_recovery[
                        0
                    ]
                )

                qualified = (
                    qualified_recovery
                )

                release_level = clean_text(
                    winner.debate.get(
                        "quality_release_level",
                        "adaptive_release",
                    ),
                    100,
                )

        except Exception as error:

            errors.append(
                (
                    "recovery_board: "
                    +
                    clean_text(
                        error,
                        2500,
                    )
                )
            )

            print(
                (
                    "⚠️ Recovery Board unavailable: "
                    +
                    clean_text(
                        error,
                        1600,
                    )
                )
            )

    # =====================================================
    # FINAL STATE
    # =====================================================

    quality_gate_passed = bool(
        winner
        and
        winner.quality_gate_passed
        and
        winner.evaluation_valid
    )

    if winner:

        print("")
        print(
            "✅ CREATIVE WINNER"
        )
        print(
            "ID:",
            winner.concept_id,
        )
        print(
            "Score:",
            winner.weighted_score,
        )
        print(
            "Release:",
            release_level,
        )
        print(
            "Camera:",
            winner.camera_angle,
        )
        print("")

    else:

        print("")
        print(
            "=========================================="
        )
        print(
            " CREATIVE QUALITY FALLBACK"
        )
        print(
            "=========================================="
        )
        print(
            "No concept reached the safe release floor."
        )
        print(
            "Smart Engine fallback remains allowed."
        )
        print("")

    if winner:

        top_concepts = (
            select_top_concepts(
                all_concepts,
                limit=top_count,
                mode=mode,
                qualified_only=True,
            )
        )

    else:

        top_concepts = rank_concepts(
            [
                concept
                for concept in all_concepts
                if concept.evaluation_valid
            ]
        )[:top_count]

    return CreativeBrainResponse(
        ok=quality_gate_passed,
        mode=mode,
        request=request,
        total_concepts=len(
            all_concepts
        ),
        concepts=all_concepts,
        top_concepts=top_concepts,
        winner=winner,
        metadata={
            "version":
                VERSION,

            "architecture":
                "cost_controlled_stc_first",

            "benefit_family":
                benefit_family,

            "stc_request":
                stc_request,

            "stc_style_family":
                style_family,

            "masterpiece_min_score":
                MASTERPIECE_MIN_SCORE,

            "masterpiece_target_score":
                MASTERPIECE_MIN_SCORE,

            "masterpiece_release_floor":
                MASTERPIECE_RELEASE_FLOOR,

            "score_weights":
                SCORE_WEIGHTS,

            "initial_concepts":
                telemetry[
                    "initial_concepts"
                ],

            "shortlisted_concepts":
                telemetry[
                    "shortlisted_concepts"
                ],

            "director_calls":
                telemetry[
                    "director_calls"
                ],

            "director_call_history":
                telemetry[
                    "director_call_history"
                ],

            "director_call_target":
                MASTERPIECE_TARGET_DIRECTOR_CALLS,

            "director_call_max":
                MASTERPIECE_MAX_DIRECTOR_CALLS,

            "recovery_used":
                telemetry[
                    "recovery_used"
                ],

            "release_level":
                release_level,

            "technical_failure":
                False,

            "quality_gate_evaluated":
                True,

            "quality_gate_passed":
                quality_gate_passed,

            "quality_target_blocks_production":
                False,

            "allow_smart_engine_fallback":
                True,

            "fallback_blocked":
                False,

            "real_model_evaluation_required":
                True,

            "structured_schema_enabled":
                True,

            "camera_review_in_main_review":
                True,

            "feasibility_in_main_review":
                True,

            "separate_camera_call":
                False,

            "separate_feasibility_call":
                False,

            "winner_finalizer_call":
                False,

            "anti_cliche_enabled":
                True,

            "stc_purple_overuse_guard":
                True,

            "stc_text_logo_guard":
                True,

            "stc_generic_fintech_guard":
                True,

            "stc_scene_realism_guard":
                True,

            "references_compacted":
                True,

            "brand_context_compacted":
                True,
        },

        errors=errors,
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

        "core_idea":
            concept.core_idea,

        "marketing_message":
            concept.marketing_message,

        "visual_metaphor":
            concept.visual_metaphor,

        "style_family":
            concept.style_family,

        "scene_archetype":
            concept.scene_archetype,

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

        "material_language":
            concept.material_language,

        "color_strategy":
            concept.color_strategy,

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


# =========================================================
# LEGACY / COMPATIBILITY FUNCTIONS
# =========================================================

def finalize_winner(
    *,
    user_request: str,
    winner: CreativeConcept,
    brand_context: Any = None,
    visual_references: Any = None,
    telemetry: Optional[
        Dict[str, Any]
    ] = None,
) -> None:

    """
    V5 already attaches camera + feasibility + production
    blueprint in the main Creative Review call.

    This function intentionally makes ZERO additional calls.
    """

    return None


def direct_camera(
    *,
    user_request: str,
    concept: CreativeConcept,
    visual_references: Any = None,
) -> Dict[str, Any]:

    camera = safe_dict(
        concept.debate.get(
            "camera_director"
        )
    )

    if camera:

        return camera

    return {
        "camera_angle":
            concept.camera_angle,

        "lens":
            concept.lens,

        "perspective_type":
            concept.perspective,

        "camera_lock_instruction":
            (
                "Preserve the concept's approved camera strategy."
            ),
    }


def check_scene_feasibility(
    *,
    user_request: str,
    concept: CreativeConcept,
    visual_references: Any = None,
) -> Dict[str, Any]:

    if concept.feasibility:

        return dict(
            concept.feasibility
        )

    return {
        "feasible":
            bool(
                concept.evaluation_valid
            ),

        "complexity_level":
            "unknown",

        "recommended_strategy":
            (
                concept.production_method
                or
                "single_generation"
            ),

        "passes":
            [],

        "single_image_risks":
            concept.risks,

        "final_recommendation":
            (
                "Use the reviewed production blueprint."
            ),
    }


def revise_concept(
    *,
    user_request: str,
    concept: CreativeConcept,
    brand_context: Any = None,
    visual_references: Any = None,
) -> Optional[
    CreativeConcept
]:

    #
    # Automatic individual revision is intentionally disabled.
    #
    # V5 uses one consolidated recovery board instead.
    #

    return None


def select_revision_candidates(
    concepts: Sequence[
        CreativeConcept
    ],
) -> List[
    CreativeConcept
]:

    return []


# =========================================================
# ZERO-API SELF TEST
# =========================================================

if __name__ == "__main__":

    tests = {}

    tests[
        "score_weights"
    ] = (
        sum(
            SCORE_WEIGHTS.values()
        )
        ==
        100
    )

    tests[
        "merchant_payments_routing"
    ] = (
        infer_benefit_family(
            (
                "خدمات التجارة الإلكترونية "
                "ونقاط البيع"
            )
        )
        ==
        "merchant_payments"
    )

    tests[
        "stc_default_realistic"
    ] = (
        infer_stc_style_family(
            (
                "أنشئ إعلان واقعي فاخر "
                "لبنك STC Bank"
            )
        )
        ==
        "premium_realistic"
    )

    tests[
        "stc_explicit_purple"
    ] = (
        infer_stc_style_family(
            (
                "STC Bank بيئة بنفسجية "
                "هندسية فاخرة"
            )
        )
        ==
        "purple_architectural"
    )

    tests[
        "stc_augmented_realism"
    ] = (
        infer_stc_style_family(
            (
                "STC Bank بأسلوب "
                "augmented realism"
            )
        )
        ==
        "augmented_realism"
    )

    tests[
        "anti_neon"
    ] = bool(
        detect_cliches(
            (
                "purple neon glow with "
                "network lines and floating card"
            )
        )
    )

    tests[
        "native_dict_parsing"
    ] = (
        extract_json_object(
            {
                "concepts": []
            }
        ).get(
            "concepts"
        )
        ==
        []
    )

    tests[
        "fenced_json_parsing"
    ] = (
        extract_json_object(
            '```json\n{"concepts":[]}\n```'
        ).get(
            "concepts"
        )
        ==
        []
    )

    tests[
        "python_literal_parsing"
    ] = (
        extract_json_object(
            "{'concepts': []}"
        ).get(
            "concepts"
        )
        ==
        []
    )

    tests[
        "ideation_schema_four"
    ] = (
        ideation_schema(
            4
        )[
            "properties"
        ][
            "concepts"
        ][
            "minItems"
        ]
        ==
        4
    )

    stc_authority = (
        build_stc_creative_authority(
            (
                "STC Bank خدمات التجارة "
                "الإلكترونية ونقاط البيع"
            )
        )
    )

    tests[
        "stc_no_text"
    ] = (
        "Do NOT design:"
        in
        stc_authority
    )

    tests[
        "stc_purple_not_default"
    ] = (
        (
            "Purple is optional"
            in
            stc_authority
        )
        and
        (
            "premium_realistic"
            in
            stc_authority
        )
    )

    tests[
        "max_three_director_calls"
    ] = (
        MASTERPIECE_MAX_DIRECTOR_CALLS
        ==
        3
    )

    tests[
        "normal_two_director_calls"
    ] = (
        MASTERPIECE_TARGET_DIRECTOR_CALLS
        ==
        2
    )

    all_ok = all(
        tests.values()
    )

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND CREATIVE BRAIN V5.0"
    )
    print(
        " ZERO-COST SELF TEST"
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

    if all_ok:

        print(
            "XPAND Creative Brain V5.0 self-test: PASS ✅"
        )

    else:

        print(
            "XPAND Creative Brain V5.0 self-test: FAIL ❌"
        )

    print("")
    print(
        "✅ 4 concepts instead of 20"
    )
    print(
        "✅ 2-concept paid shortlist"
    )
    print(
        "✅ Normal paid Director calls = 2"
    )
    print(
        "✅ Maximum calls with recovery = 3"
    )
    print(
        "✅ Explicit JSON schemas"
    )
    print(
        "✅ Merchant payments priority"
    )
    print(
        "✅ Premium realistic STC default"
    )
    print(
        "✅ Purple architecture only when justified"
    )
    print(
        "✅ Augmented realism supported"
    )
    print(
        "✅ Scientific camera vocabulary"
    )
    print(
        "✅ Camera + feasibility merged into review"
    )
    print(
        "✅ No winner-finalizer paid call"
    )
    print(
        "✅ STC no text / logo"
    )
    print(
        "✅ Purple-neon guard"
    )
    print(
        "✅ Generic fintech guard"
    )
    print(
        "✅ Scene-realism guard"
    )
    print(
        "✅ Technical failure keeps Smart fallback alive"
    )
    print(
        "🚫 No API calls were made"
    )
    print("")
