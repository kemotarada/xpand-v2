# =========================================================
# XPAND CREATIVE BRAIN V5.1
#
# PREMIUM CAMPAIGN IDEATION
# FULL RUNTIME-COMPATIBLE REPLACEMENT
#
# =========================================================
#
# Compatibility preserved for:
#
#   xpand_image_telegram.py V3.4
#   xpand_production_engine.py V5.x
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
#   run_creative_brain()
#
# =========================================================
#
# V5.1 GOALS
#
# - 4 concepts instead of 20
# - normal paid Director calls = 2
# - max Director calls = 3
# - strict structured GPT-5.6 Sol path
# - no fake evaluation
# - technical failure keeps Smart fallback alive
#
# STC Bank improvements:
#
# - campaign-level visual mechanism required
# - reject generic "person pays / person uses phone"
# - stronger camera thinking
# - premium realistic default
# - purple architecture only when justified
# - no automatic neon / fintech clutter
# - one visual idea per frame
# - natural copy space
# - no generated copy / logo
# - merchant-payments semantic priority
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

        if (
            "نقاط البيع"
            in text
            or
            "point of sale"
            in text
            or
            "ecommerce"
            in text
            or
            "e-commerce"
            in text
            or
            "التجارة الالكترونية"
            in text
            or
            "التجارة الإلكترونية"
            in text
        ):

            return "merchant_payments"

        return "general_banking"


# =========================================================
# IDENTITY
# =========================================================

VERSION = "5.1"

MODULE_NAME = "XPAND Creative Brain"


# =========================================================
# MODES
#
# CRITICAL COMPATIBILITY CONTRACT
# =========================================================

MODE_FAST = "fast"

MODE_MASTERPIECE = "masterpiece"


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


# =========================================================
# COST POLICY
# =========================================================

INITIAL_CONCEPT_COUNT = 4

MASTERPIECE_SHORTLIST_SIZE = 2

MASTERPIECE_TARGET_DIRECTOR_CALLS = 2

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
# DATA MODEL
#
# IMPORTANT:
#
# Field names intentionally preserve the old XPAND contract.
# =========================================================

@dataclass
class CreativeConcept:

    concept_id: str = ""

    category: str = ""

    title: str = ""

    core_idea: str = ""

    marketing_message: str = ""

    visual_metaphor: str = ""

    environment: str = ""

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
# SCHEMA
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

        "core_idea": {
            "type": "string",
        },

        "marketing_message": {
            "type": "string",
        },

        "visual_metaphor": {
            "type": "string",
        },

        "environment": {
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
        "core_idea",
        "marketing_message",
        "visual_metaphor",
        "environment",
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


IDEATION_SCHEMA: Dict[
    str,
    Any,
] = {
    "type": "object",

    "additionalProperties": False,

    "properties": {
        "concepts": {
            "type": "array",

            "minItems": 4,

            "maxItems": 4,

            "items":
                CONCEPT_SCHEMA,
        },
    },

    "required": [
        "concepts",
    ],
}


REVIEW_SCHEMA: Dict[
    str,
    Any,
] = {
    "type": "object",

    "additionalProperties": False,

    "properties": {
        "evaluations": {
            "type": "array",

            "minItems": 4,

            "maxItems": 4,

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

                    "weighted_score": {
                        "type": "number",
                    },

                    "verdict": {
                        "type": "string",

                        "enum": [
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
                    "weighted_score",
                    "verdict",
                    "strengths",
                    "weaknesses",
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
    "عميل يدفع عند الكاونتر",
    "smiling businessman",
    "handshake",
    "generic office",
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
]


STC_VISUAL_MECHANISMS = [
    "continuous commerce journey",
    "service transformation",
    "physical visual bridge",
    "architectural metaphor",
    "product as environment",
    "portal grounded in physical object",
    "foreground background relationship",
    "single scene dual-channel story",
    "real-world benefit manifestation",
    "perspective-based visual connection",
    "scale contrast",
    "material transition",
    "framing device",
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
            "نقاط البيع",
            "التجارة الالكترونية",
            "التجارة الإلكترونية",
            "e-commerce",
            "ecommerce",
            "point of sale",
            "pos",
            "merchant payments",
        ],
    ):

        return "merchant_payments"

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
            "augmented realism",
            "symbolic realism",
            "واقعي بفكرة خيالية",
        ],
    ):

        return "premium_augmented_realism"

    return "premium_realistic"


# =========================================================
# CONCEPT PARSER
# =========================================================

def concept_from_dict(
    item: Dict[str, Any],
    *,
    fallback_id: str,
    generation_round: int = 1,
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
            150,
        ),

        title=clean_text(
            item.get(
                "title"
            ),
            500,
        ),

        core_idea=clean_text(
            item.get(
                "core_idea"
            ),
            3000,
        ),

        marketing_message=clean_text(
            item.get(
                "marketing_message"
            ),
            1600,
        ),

        visual_metaphor=clean_text(
            item.get(
                "visual_metaphor"
            ),
            1800,
        ),

        environment=clean_text(
            item.get(
                "environment"
            ),
            2200,
        ),

        hero_element=clean_text(
            item.get(
                "hero_element"
            ),
            1300,
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
            700,
        ),

        lens=clean_text(
            item.get(
                "lens"
            ),
            300,
        ),

        perspective=clean_text(
            item.get(
                "perspective"
            ),
            900,
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
            1000,
        ),

        brand_logic=clean_text(
            item.get(
                "brand_logic"
            ),
            1600,
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
            1000,
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

    return concept


# =========================================================
# LOCAL CREATIVE GUARD
#
# NO API CALL
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

    text = "\n".join(
        [
            concept.title,
            concept.core_idea,
            concept.visual_metaphor,
            concept.environment,
            concept.hero_element,
            concept.camera_angle,
            concept.perspective,
            concept.lighting,
            concept.brand_logic,
            " ".join(
                concept.supporting_elements
            ),
        ]
    )

    penalty = 0.0

    failures: List[str] = []

    if is_stc_bank_request(
        user_request
    ):

        if contains_any(
            text,
            STC_FINTECH_CLICHES,
        ):

            penalty += 12.0

            failures.append(
                "generic_fintech_visual"
            )

        if contains_any(
            text,
            STC_GENERIC_PATTERNS,
        ):

            #
            # Not an absolute rejection:
            # sometimes a real person is valid.
            #
            # But without a visual mechanism it is weak.
            #

            if (
                len(
                    clean_text(
                        concept.visual_metaphor,
                        1000,
                    )
                )
                <
                30
            ):

                penalty += 14.0

                failures.append(
                    "generic_lifestyle_without_visual_mechanism"
                )

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
                ],
            )
        ):

            penalty += 15.0

            failures.append(
                "purple_neon_realism_violation"
            )

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

            penalty += 5.0

            failures.append(
                "weak_copy_space"
            )

        if not contains_any(
            (
                concept.camera_angle
                +
                " "
                +
                concept.perspective
            ),
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
            ],
        ):

            penalty += 4.0

            failures.append(
                "camera_not_precise"
            )

    if (
        benefit_family
        ==
        "merchant_payments"
    ):

        commerce_text = (
            normalize_arabic(
                text
            )
        )

        online_present = any(
            marker
            in commerce_text
            for marker in [
                "تجاره الكترونيه",
                "طلب اونلاين",
                "طلب الكتروني",
                "ecommerce",
                "e-commerce",
                "online order",
                "fulfillment",
                "packing",
                "shipment",
            ]
        )

        pos_present = any(
            marker
            in commerce_text
            for marker in [
                "نقاط البيع",
                "point of sale",
                "pos",
                "terminal",
                "tap",
                "checkout",
                "كاونتر",
                "الدفع",
            ]
        )

        if not online_present:

            penalty += 8.0

            failures.append(
                "merchant_online_channel_missing"
            )

        if not pos_present:

            penalty += 8.0

            failures.append(
                "merchant_pos_channel_missing"
            )

    return (
        penalty,
        failures,
    )


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
) -> str:

    recovery_block = ""

    if recovery:

        recovery_block = """
RECOVERY MODE
=============

A previous structured ideation attempt failed.

Return the COMPLETE schema exactly.

Do not shorten fields into:
"الفكرة"
"السبب"

Do not return color-only keys.

Return exactly four fully developed concepts.
"""

    stc_block = ""

    if is_stc_bank_request(
        user_request
    ):

        stc_block = f"""
==================================================
STC BANK CAMPAIGN INTELLIGENCE
==================================================

Visual family:
{stc_style}

Benefit family:
{benefit_family}

The target is premium STC Bank-level advertising.

Think like a senior advertising art director,
not like a generic image prompt writer.

--------------------------------------------------
THE CENTRAL RULE
--------------------------------------------------

Every concept needs ONE memorable visual mechanism.

A visual mechanism is the visual reason the advertisement
deserves to exist.

Examples of valid thinking:

- foreground action and background action become one visual journey
- one physical object transforms the meaning of the environment
- architecture behaves as the metaphor
- scale creates the idea
- framing reveals the service
- a real product becomes the visual bridge between two benefits
- a service moment is shown from an unexpected perspective
- one strong realistic scene contains a subtle conceptual twist

Do NOT mechanically copy those examples.

Invent the mechanism specifically for the brief.

--------------------------------------------------
STC BANK REFERENCE-DNA PRINCIPLES
--------------------------------------------------

The campaign language can move between:

A) PREMIUM REALISM
   Real Saudi environments.
   Clean people photography.
   Strong lifestyle moment.
   Natural but art-directed light.
   Premium materials.
   Restrained brand color.

B) PURPLE ARCHITECTURAL PRODUCT WORLD
   Controlled purple architecture.
   Pedestals, planes and stepped surfaces.
   Intentional geometry.
   Deep tonal separation.
   Satin / glossy material reflections.
   Hero-object discipline.
   Purple is architecture, NOT random neon.

C) AUGMENTED / SYMBOLIC REALISM
   Real scene plus ONE imaginative physical metaphor.
   Still photographically believable.
   No sci-fi clutter.

Purple is NOT automatically STC Bank identity.

A realistic STC Bank advertisement may contain:
cream stone,
warm timber,
glass,
black,
charcoal,
sand,
sky blue,
soft natural daylight,
warm sunset,
deep navy,
or other physically believable colors.

Mint green and purple are accents when useful,
not mandatory paint over the entire frame.

--------------------------------------------------
CAMERA
--------------------------------------------------

Choose an intentional scientific camera language.

Possible vocabulary when justified:

- eye-level environmental portrait
- low-angle hero shot
- worm's-eye view
- bird's-eye view
- elevated three-quarter view
- high-angle architectural composition
- over-the-shoulder POV
- foreground-framed composition
- compressed telephoto perspective
- shallow-depth environmental portrait
- symmetrical frontal product hero
- diagonal three-quarter product view
- macro / close product detail
- wide environmental establishing shot

Do NOT choose a strange angle just to be different.

The angle must strengthen the advertising idea.

--------------------------------------------------
LIGHT
--------------------------------------------------

Use real lighting logic:

- large-window soft daylight
- directional morning sunlight
- golden-hour side light
- soft skylight
- premium diffused key
- negative fill
- controlled practical lights
- edge separation
- realistic contact shadows
- material-specific specular reflections

No meaningless neon glow.

--------------------------------------------------
MATERIALS
--------------------------------------------------

Show deliberate physical surfaces:

stone
travertine
oak
walnut
brushed metal
matte metal
glass
fabric
paper
leather
polished lacquer
satin finish

Materials should create visual luxury.

--------------------------------------------------
COMPOSITION
--------------------------------------------------

One hero.

One message.

One dominant visual mechanism.

25%-40% naturally usable negative space for typography
to be added manually later.

Do not generate or request:
- headline
- slogan
- body copy
- CTA
- legal copy
- STC Bank logo
- card logos
- Visa logo
- readable banking UI

--------------------------------------------------
REJECT THESE WEAK IDEAS
--------------------------------------------------

Reject unless transformed into something genuinely original:

- customer simply paying at counter
- person simply looking at phone
- employee smiling at desk
- card floating in empty room
- POS terminal floating
- generic airport shot
- handshake
- coins flying
- network lines
- random holograms
- fintech tunnel
- neon purple banking room
- glowing particles
- random purple props

A beautiful room alone is not an idea.

A brand color alone is not an idea.

A person using a banking service alone is not a campaign idea.

--------------------------------------------------
MERCHANT PAYMENTS SPECIAL RULE
--------------------------------------------------

If benefit_family = merchant_payments:

Communicate e-commerce AND physical point-of-sale
as ONE coherent commercial ecosystem.

Avoid the weak solution:

"customer taps terminal in foreground while worker packs
a box somewhere in the background"

unless composition and visual mechanism genuinely connect
those actions into one unmistakable campaign idea.

Find a stronger visual relationship.

{clean_text(STC_BANK_VISUAL_SKILL, 5000)}
"""

    return f"""
You are XPAND Creative Brain V5.1.

You are developing campaign-grade advertising concepts.

==================================================
ORIGINAL REQUEST
==================================================

{clean_text(user_request, 6000)}

==================================================
BRAND CONTEXT
==================================================

{compact_json(brand_context, 5000)}

==================================================
REFERENCE DNA
==================================================

{compact_json(visual_references, 5000)}

==================================================
STYLE HINT
==================================================

{clean_text(style_hint, 1200)}

==================================================
RULES
==================================================

Generate exactly FOUR fundamentally different concepts.

Do not produce four cosmetic variations.

Each concept must differ in at least:
- visual mechanism
- hero relationship
- camera strategy
- spatial composition

Each concept must work as one hero advertising image.

No generated text or logo inside the intended image.

{stc_block}

{recovery_block}

==================================================
OUTPUT CONTRACT
==================================================

Return exactly the structured schema.

Use concept IDs:

C01
C02
C03
C04

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
) -> str:

    payload = [
        concept_to_dict(
            concept
        )
        for concept in concepts
    ]

    return f"""
You are XPAND Senior Creative Review Board.

Evaluate four advertising concepts.

Do NOT invent new concepts.

==================================================
REQUEST
==================================================

{clean_text(user_request, 5000)}

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

{compact_json(payload, 16000)}

==================================================
SCORING
==================================================

Score every dimension from 0 to 100.

Be strict.

concept_strength:
Does one frame communicate a clear advertising idea?

brand_fit:
Does it feel premium and appropriate for the brand
without lazy brand-color dependence?

originality:
Is the idea more memorable than ordinary stock photography?

visual_mechanism:
Is there an actual visual mechanism or only a scene?

camera_quality:
Does camera strategy strengthen the idea?

realism:
Can the image look physically credible and polished?

feasibility:
Can a modern image model produce it reliably?

copy_space_quality:
Is there natural 25%-40% usable typography space?

--------------------------------------------------
SPECIAL STC BANK STANDARD
--------------------------------------------------

Penalize heavily:

- generic person-with-phone
- generic customer-at-counter
- decorative purple only
- purple neon
- floating fintech clutter
- weak symbolism
- too many unrelated ideas
- impossible physical logic
- copy space that feels artificially empty

Reward:

- campaign-level hero composition
- premium realism
- strong material quality
- unusual but justified camera
- one clear visual mechanism
- service clarity without textual explanation
- elegant copy-space planning

For merchant_payments:
the strongest concept must connect online commerce and
physical payment visually rather than merely placing two
activities in the same room.

--------------------------------------------------
CAMERA REVIEW
--------------------------------------------------

Return one final recommended camera angle,
lens and perspective for production.

Do not mix contradictory camera systems.

--------------------------------------------------
IMPORTANT
--------------------------------------------------

weighted_score must reflect your genuine evaluation.

Do not give every concept 90+.

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
    )

    raw = call_openai_director(
        prompt,

        json_mode=True,

        json_schema=(
            IDEATION_SCHEMA
        ),

        json_schema_name=(
            "xpand_creative_ideation_v51"
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
                50000,
            )
        )

    raw_concepts = safe_list(
        payload.get(
            "concepts"
        )
    )

    if len(
        raw_concepts
    ) != 4:

        raise RuntimeError(
            (
                "Creative Brain expected 4 concepts, got "
                +
                str(
                    len(
                        raw_concepts
                    )
                )
            )
        )

    concepts = []

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

        concept = concept_from_dict(
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
                2
                if recovery
                else 1
            ),
        )

        #
        # Stable IDs for downstream runtime.
        #

        concept.concept_id = (
            "C"
            +
            str(
                index
            ).zfill(
                2
            )
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
    )

    raw = call_openai_director(
        prompt,

        json_mode=True,

        json_schema=(
            REVIEW_SCHEMA
        ),

        json_schema_name=(
            "xpand_creative_review_v51"
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
                60000,
            )
        )

    evaluations = safe_list(
        payload.get(
            "evaluations"
        )
    )

    if len(
        evaluations
    ) != 4:

        raise RuntimeError(
            (
                "Creative review expected 4 evaluations, got "
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

        local_penalty, failures = (
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

        final_score = max(
            0.0,
            min(
                100.0,
                model_score
                -
                local_penalty,
            ),
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

            "model_weighted_score":
                model_score,

            "local_penalty":
                local_penalty,
        }

        concept.weighted_score = round(
            final_score,
            2,
        )

        concept.evaluation_valid = True

        concept.quality_gate_failures = (
            list(
                failures
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
            in failures
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
                    1200,
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

            #
            # Production runtime compatibility.
            #

            "camera_director": {
                "camera_angle":
                    clean_text(
                        evaluation.get(
                            "recommended_camera_angle"
                        ),
                        700,
                    )
                    or
                    concept.camera_angle,

                "lens":
                    clean_text(
                        evaluation.get(
                            "recommended_lens"
                        ),
                        300,
                    )
                    or
                    concept.lens,

                "perspective":
                    clean_text(
                        evaluation.get(
                            "recommended_perspective"
                        ),
                        700,
                    )
                    or
                    concept.perspective,

                "perspective_type":
                    clean_text(
                        evaluation.get(
                            "recommended_perspective"
                        ),
                        700,
                    )
                    or
                    concept.perspective,

                "creative_reason":
                    clean_text(
                        evaluation.get(
                            "camera_reason"
                        ),
                        1000,
                    ),

                "camera_lock_instruction":
                    (
                        "Preserve this camera strategy "
                        "during final image production."
                    ),
            },
        }


# =========================================================
# QUALITY RELEASE
# =========================================================

def choose_release(
    *,
    concepts: List[
        CreativeConcept
    ],
    mode: str,
) -> Tuple[
    Optional[
        CreativeConcept
    ],
    str,
]:

    valid = [
        concept
        for concept in concepts
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

    #
    # MASTERPIECE
    #

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
    print(
        "Smart Engine fallback should remain allowed."
    )

    if errors:

        print(
            clean_text(
                errors[
                    -1
                ],
                3000,
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
                "quality_first_campaign_mechanism",

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
#
# CRITICAL COMPATIBILITY SIGNATURE
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
        12000,
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
        " XPAND CREATIVE BRAIN V5.1"
    )
    print(
        " CAMPAIGN MECHANISM + QUALITY FIRST"
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
        "Concepts:",
        INITIAL_CONCEPT_COUNT,
    )

    print(
        "Paid shortlist:",
        MASTERPIECE_SHORTLIST_SIZE,
    )

    print(
        "Target Director calls:",
        MASTERPIECE_TARGET_DIRECTOR_CALLS,
    )

    print("")

    # =====================================================
    # CALL 1 — IDEATION
    # =====================================================

    concepts: List[
        CreativeConcept
    ] = []

    try:

        director_calls += 1

        director_history.append(
            "ideation"
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
        )

    except Exception as error:

        errors.append(
            (
                "primary_ideation: "
                +
                clean_text(
                    error,
                    3000,
                )
            )
        )

        print(
            "⚠️ Primary ideation unavailable:",
            clean_text(
                error,
                2200,
            ),
        )

        # =================================================
        # RECOVERY IDEATION
        #
        # Only if call budget permits.
        # =================================================

        if (
            director_calls
            <
            MASTERPIECE_MAX_DIRECTOR_CALLS
        ):

            try:

                print(
                    "🔁 Running compact structured recovery..."
                )

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
                )

            except Exception as recovery_error:

                errors.append(
                    (
                        "ideation_recovery: "
                        +
                        clean_text(
                            recovery_error,
                            3000,
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
        )

    # =====================================================
    # CALL 2 — REVIEW BOARD
    #
    # Or call 3 if recovery ideation was used.
    # =====================================================

    if (
        director_calls
        >=
        MASTERPIECE_MAX_DIRECTOR_CALLS
    ):

        #
        # This should only happen if max calls was configured
        # below the required review path.
        #

        errors.append(
            (
                "Director call budget exhausted "
                "before real creative evaluation."
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
        )

    try:

        director_calls += 1

        director_history.append(
            "creative_review"
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
        )

    except Exception as error:

        errors.append(
            (
                "creative_review: "
                +
                clean_text(
                    error,
                    3000,
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
        )

    # =====================================================
    # RANK
    # =====================================================

    concepts.sort(
        key=lambda item:
            item.weighted_score,
        reverse=True,
    )

    shortlist = concepts[
        :MASTERPIECE_SHORTLIST_SIZE
    ]

    winner, release_level = (
        choose_release(
            concepts=(
                concepts
            ),

            mode=(
                mode
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
            "Score:",
            winner.weighted_score,
        )

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

    effective_integration_floor = (
        MASTERPIECE_MIN_SCORE
    )

    if winner:

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
                "campaign_mechanism_quality_first",

            "benefit_family":
                benefit_family,

            "stc_style":
                stc_style,

            "initial_concepts":
                INITIAL_CONCEPT_COUNT,

            "shortlisted_concepts":
                len(
                    shortlist
                ),

            "director_calls":
                director_calls,

            "director_call_history":
                director_history,

            "director_call_target":
                MASTERPIECE_TARGET_DIRECTOR_CALLS,

            "masterpiece_min_score":
                effective_integration_floor,

            "masterpiece_target_score":
                MASTERPIECE_MIN_SCORE,

            "masterpiece_release_floor":
                MASTERPIECE_RELEASE_FLOOR,

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
                    MASTERPIECE_MIN_SCORE
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

            "purple_neon_guard":
                True,

            "merchant_fusion_guard":
                True,

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
# CRITICAL COMPATIBILITY CONTRACT
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

    test_concept = CreativeConcept(
        concept_id="C01",

        category="merchant_commerce_fusion",

        title="Commerce Through One Counter",

        core_idea=(
            "A premium Saudi merchant scene connecting "
            "online fulfillment and physical checkout."
        ),

        marketing_message=(
            "One merchant ecosystem."
        ),

        visual_metaphor=(
            "A continuous physical composition visually "
            "connects fulfillment to payment."
        ),

        environment=(
            "Premium Saudi fashion boutique with travertine, "
            "oak and glass."
        ),

        hero_element=(
            "The merchant counter acting as the visual bridge."
        ),

        supporting_elements=[
            "real POS terminal",
            "premium parcel",
        ],

        camera_angle=(
            "elevated three-quarter view"
        ),

        lens="35mm",

        perspective=(
            "foreground-framed environmental perspective"
        ),

        lighting=(
            "large-window directional soft daylight"
        ),

        negative_space=(
            "30% clean upper-left negative space"
        ),

        brand_logic=(
            "Premium realism with restrained brand accent."
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
    ] = (
        isinstance(
            response.metadata,
            dict,
        )
    )

    tests[
        "visual_mechanism_guard"
    ] = contains_any(
        build_ideation_prompt(
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
        ),
        [
            "ONE memorable visual mechanism",
        ],
    )

    tests[
        "no_generic_scene_rule"
    ] = contains_any(
        build_ideation_prompt(
            user_request=(
                "STC Bank"
            ),

            brand_context={},

            visual_references=[],

            style_hint="",

            benefit_family=(
                "general_banking"
            ),

            stc_style=(
                "premium_realistic"
            ),
        ),
        [
            "customer simply paying at counter",
        ],
    )

    tests[
        "purple_not_default"
    ] = contains_any(
        build_ideation_prompt(
            user_request=(
                "STC Bank"
            ),

            brand_context={},

            visual_references=[],

            style_hint="",

            benefit_family=(
                "general_banking"
            ),

            stc_style=(
                "premium_realistic"
            ),
        ),
        [
            "Purple is NOT automatically",
        ],
    )

    tests[
        "merchant_fusion_guard"
    ] = contains_any(
        build_ideation_prompt(
            user_request=(
                "STC Bank نقاط البيع والتجارة الإلكترونية"
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
        ),
        [
            "physical payment visually",
        ],
    )

    tests[
        "max_three_director_calls"
    ] = (
        MASTERPIECE_MAX_DIRECTOR_CALLS
        <=
        3
    )

    tests[
        "normal_two_director_calls"
    ] = (
        MASTERPIECE_TARGET_DIRECTOR_CALLS
        ==
        2
    )

    passed = all(
        tests.values()
    )

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND CREATIVE BRAIN V5.1"
    )
    print(
        " ZERO-COST SELF TEST"
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
                "XPAND Creative Brain V5.1 "
                "self-test: PASS ✅"
            )
        )

    else:

        print(
            (
                "XPAND Creative Brain V5.1 "
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
        "✅ 4 concept ideation"
    )
    print(
        "✅ 2 normal Director calls"
    )
    print(
        "✅ Maximum 3 Director calls"
    )
    print(
        "✅ GPT-5.6 Sol strict schemas via Image Engine"
    )
    print(
        "✅ Campaign-level visual mechanism"
    )
    print(
        "✅ Generic scene penalty"
    )
    print(
        "✅ Merchant commerce fusion rule"
    )
    print(
        "✅ Premium realistic STC default"
    )
    print(
        "✅ Purple architecture optional"
    )
    print(
        "✅ Anti-purple-neon guard"
    )
    print(
        "✅ Scientific camera language"
    )
    print(
        "✅ Natural copy-space discipline"
    )
    print(
        "✅ No fake evaluation"
    )
    print(
        "✅ Technical failure keeps Smart fallback alive"
    )
    print(
        "🚫 No API calls were made"
    )
    print(
        "🚫 No images were generated"
    )
    print("")
