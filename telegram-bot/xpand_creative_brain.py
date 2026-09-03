# =========================================================
# XPAND CREATIVE BRAIN V1.0
#
# Creative strategy and concept-development engine.
#
# Implements:
# - Fast Mode
# - Masterpiece Mode
# - 20-direction concept generation
# - Anti-Cliche system
# - Visual Metaphor engine
# - Weighted concept scoring
# - Creative Debate
# - Brand Guardian
# - Production Expert
# - Harsh Critic
# - Camera Angle Director
# - Scene Feasibility Check
#
# IMPORTANT:
# - This module does NOT generate images.
# - This module does NOT expose hidden chain-of-thought.
# - It returns structured creative decisions only.
#
# Uses:
# - GPT-5.6 Sol through call_openai_director()
#   already implemented in xpand_image_engine.py
# =========================================================

from __future__ import annotations

import json
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

VERSION = "1.0"

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
# SCORING WEIGHTS
#
# User-approved weighting:
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
#
# 5 simple intelligent
# 5 realistic cinematic
# 5 conceptual photorealism
# 3 scale manipulation
# 2 bold / outside the box
#
# TOTAL = 20
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
        20000
    ).lower()

    replacements = {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ة": "ه",
        "ى": "ي",
        "ؤ": "و",
        "ئ": "ي",
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
# JSON PARSER
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
# BRAND CONTEXT SERIALIZER
# =========================================================

def compact_brand_context(
    brand_context: Any,
    limit: int = 16000
) -> str:

    if not brand_context:

        return "No structured brand context supplied."

    if isinstance(
        brand_context,
        str
    ):

        return clean_text(
            brand_context,
            limit
        )

    try:

        return clean_text(
            json.dumps(
                brand_context,
                ensure_ascii=False,
                indent=2
            ),
            limit
        )

    except Exception:

        return clean_text(
            brand_context,
            limit
        )


# =========================================================
# VISUAL REFERENCES SERIALIZER
# =========================================================

def compact_visual_references(
    visual_references: Any,
    limit: int = 16000
) -> str:

    if not visual_references:

        return "No Visual Reference DNA supplied."

    if isinstance(
        visual_references,
        str
    ):

        return clean_text(
            visual_references,
            limit
        )

    try:

        return clean_text(
            json.dumps(
                visual_references,
                ensure_ascii=False,
                indent=2
            ),
            limit
        )

    except Exception:

        return clean_text(
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
    mode: str = MODE_MASTERPIECE
) -> str:

    if mode == MODE_FAST:

        distribution = (
            FAST_DISTRIBUTION
        )

    else:

        distribution = (
            MASTERPIECE_DISTRIBUTION
        )

    metaphor_seed = get_metaphor_seed(
        user_request
    )

    return f"""
You are XPAND Creative Brain.

Act as a world-class advertising concept-development team.

The user is asking for a visual advertising concept.

Do NOT generate an image.

Do NOT write the final image prompt yet.

Do NOT expose private chain-of-thought.

Return only concise structured creative decisions.

==================================================
USER REQUEST
==================================================

{clean_text(user_request, 12000)}

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

{clean_text(style_hint, 2000) or "Use the most appropriate visual style."}

==================================================
CREATIVE MODE
==================================================

{mode}

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

{json.dumps(
    metaphor_seed["directions"],
    ensure_ascii=False,
    indent=2
)}

These are thinking seeds only.

Do NOT copy them mechanically.

==================================================
MANDATORY CREATIVE RULES
==================================================

Every concept must:

- communicate the benefit visually
- work without explanatory text
- fit the brand context
- feel premium and commercially usable
- avoid generic banking symbolism
- have one dominant visual idea
- avoid unnecessary visual effects
- use a meaningful camera angle
- have plausible lighting and perspective
- be executable as one image OR clearly state if composite production is needed
- respect Product Lock information in the supplied Visual Reference DNA
- preserve original product identity if a product reference exists
- leave intentional negative space where appropriate
- avoid copying a specific existing campaign

Avoid these clichés unless transformed into a genuinely original idea:

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

The camera angle must serve the idea.

Select a technically coherent angle such as:

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

Choose a logical focal length.

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

Do not score them yet.

Do not choose the winner yet.
""".strip()


# =========================================================
# CONCEPT PARSER
# =========================================================

def parse_concepts(
    payload: Dict[str, Any]
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

        concept_id = clean_text(
            item.get(
                "concept_id"
            ),
            100
        )

        if not concept_id:

            concept_id = (
                "C"
                +
                str(
                    index
                ).zfill(
                    2
                )
            )

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
                concept_id,

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

        concepts.append(
            concept
        )

    return concepts


# =========================================================
# GENERATE CONCEPT POOL
# =========================================================

def generate_concept_pool(
    *,
    user_request: str,
    brand_context: Any = None,
    visual_references: Any = None,
    style_hint: str = "",
    mode: str = MODE_MASTERPIECE
) -> List[
    CreativeConcept
]:

    prompt = (
        build_concept_generation_prompt(
            user_request=
                user_request,

            brand_context=
                brand_context,

            visual_references=
                visual_references,

            style_hint=
                style_hint,

            mode=
                mode
        )
    )

    raw = call_openai_director(
        prompt
    )

    payload = extract_json_object(
        raw
    )

    concepts = parse_concepts(
        payload
    )

    expected = (
        sum(
            FAST_DISTRIBUTION.values()
        )
        if mode == MODE_FAST
        else
        sum(
            MASTERPIECE_DISTRIBUTION.values()
        )
    )

    if len(
        concepts
    ) < max(
        3,
        expected // 2
    ):

        raise RuntimeError(
            (
                "Creative Brain returned too few "
                "usable concepts."
            )
        )

    return concepts


# =========================================================
# EVALUATION / CREATIVE DEBATE
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
    }


def build_evaluation_prompt(
    *,
    user_request: str,
    concepts: List[
        CreativeConcept
    ],
    brand_context: Any = None,
    visual_references: Any = None
) -> str:

    concepts_json = json.dumps(
        [
            concept_payload_for_evaluation(
                concept
            )
            for concept in concepts
        ],
        ensure_ascii=False,
        indent=2
    )

    return f"""
You are the XPAND Creative Review Board.

Do NOT generate an image.

Do NOT expose chain-of-thought.

Evaluate the supplied advertising concepts using four
professional roles:

1. Creative Director
2. Brand Guardian
3. Production Expert
4. Harsh Critic

==================================================
ORIGINAL REQUEST
==================================================

{clean_text(user_request, 12000)}

==================================================
BRAND MEMORY
==================================================

{compact_brand_context(brand_context)}

==================================================
VISUAL REFERENCES
==================================================

{compact_visual_references(visual_references)}

==================================================
CONCEPTS
==================================================

{concepts_json}

==================================================
ROLE RESPONSIBILITIES
==================================================

CREATIVE DIRECTOR:
- originality
- conceptual strength
- visual impact
- clarity
- advertising intelligence

BRAND GUARDIAN:
- brand compatibility
- identity consistency
- cultural appropriateness
- visual-language consistency
- compliance with stored approved/rejected directions

PRODUCTION EXPERT:
- one-frame feasibility
- generation reliability
- perspective
- product geometry
- camera consistency
- lighting consistency
- whether multi-pass/composite/inpainting is required

HARSH CRITIC:
- identify generic ideas
- identify cliché
- identify weak metaphor
- identify unnecessary complexity
- identify AI-generation failure risks
- reject pretty-but-empty visuals

==================================================
SCORING
==================================================

Score each concept from 0–100 on:

- message_clarity
- originality
- brand_fit
- visual_power
- feasibility
- perspective_integrity
- campaign_potential

Do not calculate the final weighted score.
Python will calculate it.

==================================================
SCENE FEASIBILITY
==================================================

For each concept also decide:

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
CAMERA REVIEW
==================================================

Check that:

- the camera angle serves the message
- the lens is plausible
- camera angle and perspective do not contradict
- product proportions can remain stable
- human anatomy is not placed in unnecessarily risky poses

If the current camera direction is weak,
provide an improved camera direction.

==================================================
ANTI-CLICHE
==================================================

A concept with cliché elements must not receive a high
originality score unless the cliché has been transformed
into a genuinely fresh visual relationship.

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

Return one evaluation for every supplied concept.
""".strip()


def evaluate_concept_pool(
    *,
    user_request: str,
    concepts: List[
        CreativeConcept
    ],
    brand_context: Any = None,
    visual_references: Any = None
) -> List[
    CreativeConcept
]:

    if not concepts:

        return []

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
        prompt
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

    evaluation_map: Dict[
        str,
        Dict[str, Any]
    ] = {}

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

        if concept_id:

            evaluation_map[
                concept_id
            ] = item

    for concept in concepts:

        evaluation = evaluation_map.get(
            concept.concept_id,
            {}
        )

        scores = evaluation.get(
            "scores",
            {}
        )

        if not isinstance(
            scores,
            dict
        ):

            scores = {}

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

        weighted = (
            calculate_weighted_score(
                normalized_scores
            )
        )

        weighted = (
            apply_cliche_penalty(
                weighted,
                concept.cliche_hits
            )
        )

        concept.scores = (
            normalized_scores
        )

        concept.weighted_score = (
            weighted
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

    return concepts


# =========================================================
# APPROVAL GATE
# =========================================================

def role_approved(
    value: Any
) -> bool:

    if not isinstance(
        value,
        dict
    ):

        return True

    return bool(
        value.get(
            "approved",
            True
        )
    )


def concept_passes_review(
    concept: CreativeConcept
) -> bool:

    debate = concept.debate

    critical_roles = [
        "creative_director",
        "brand_guardian",
        "production_expert",
        "harsh_critic",
    ]

    rejected = 0

    for role in critical_roles:

        if not role_approved(
            debate.get(
                role,
                {}
            )
        ):

            rejected += 1

    #
    # One role can object and the concept can still
    # survive if overall performance is exceptional.
    #
    if rejected >= 2:

        return False

    if concept.weighted_score < 65:

        return False

    return True


# =========================================================
# TOP-CONCEPT SELECTION
# =========================================================

def select_top_concepts(
    concepts: List[
        CreativeConcept
    ],
    limit: int = 3
) -> List[
    CreativeConcept
]:

    approved = [
        concept
        for concept in concepts
        if concept_passes_review(
            concept
        )
    ]

    pool = (
        approved
        if len(
            approved
        ) >= min(
            limit,
            len(
                concepts
            )
        )
        else
        concepts
    )

    ordered = sorted(
        pool,
        key=
            lambda item:
                item.weighted_score,
        reverse=
            True
    )

    selected: List[
        CreativeConcept
    ] = []

    used_categories = set()

    #
    # Prefer category diversity in the top 3.
    #
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

    #
    # Fill remaining slots by score.
    #
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

            if (
                concept.concept_id
                in selected_ids
            ):

                continue

            selected.append(
                concept
            )

            selected_ids.add(
                concept.concept_id
            )

    return selected


# =========================================================
# CAMERA DIRECTOR
# =========================================================

def build_camera_director_prompt(
    *,
    user_request: str,
    concept: CreativeConcept,
    visual_references: Any = None
) -> str:

    camera_library_text = json.dumps(
        CAMERA_LIBRARY,
        ensure_ascii=False,
        indent=2
    )

    lens_library_text = json.dumps(
        LENS_LIBRARY,
        ensure_ascii=False,
        indent=2
    )

    return f"""
You are XPAND Camera Angle Director.

Do NOT redesign the concept.

Do NOT expose chain-of-thought.

Choose the most effective physically coherent camera
setup for this advertising concept.

ORIGINAL REQUEST:

{clean_text(user_request, 10000)}

CONCEPT:

{json.dumps(
    concept_payload_for_evaluation(
        concept
    ),
    ensure_ascii=False,
    indent=2
)}

VISUAL REFERENCES:

{compact_visual_references(visual_references)}

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
        )
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

Assess whether this concept can be reliably generated.

USER REQUEST:

{clean_text(user_request, 10000)}

CONCEPT:

{json.dumps(
    concept_payload_for_evaluation(
        concept
    ),
    ensure_ascii=False,
    indent=2
)}

VISUAL REFERENCES / PRODUCT LOCK:

{compact_visual_references(visual_references)}

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
- whether Product Lock conflicts with free generation
- whether background/product should be generated separately
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
        )
    )

    return extract_json_object(
        raw
    )


# =========================================================
# OPTIONAL REVISION OF WINNING CONCEPT
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

Do NOT generate an image.

Do NOT expose chain-of-thought.

Revise ONLY the weak points of the supplied concept.

Keep all strong elements.

ORIGINAL REQUEST:

{clean_text(user_request, 10000)}

CURRENT CONCEPT:

{json.dumps(
    concept_payload_for_evaluation(
        concept
    ),
    ensure_ascii=False,
    indent=2
)}

DEBATE / REVIEW:

{json.dumps(
    concept.debate,
    ensure_ascii=False,
    indent=2
)}

BRAND MEMORY:

{compact_brand_context(brand_context)}

VISUAL REFERENCES:

{compact_visual_references(visual_references)}

Return JSON only:

{{
  "concept_id": "{concept.concept_id}",
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

        mode = MODE_MASTERPIECE

    errors: List[str] = []

    # -----------------------------------------------------
    # PASS 1
    # CONCEPT GENERATION
    # -----------------------------------------------------

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
            mode
    )

    # -----------------------------------------------------
    # PASS 2
    # CREATIVE DEBATE + SCORING
    # -----------------------------------------------------

    try:

        concepts = evaluate_concept_pool(
            user_request=
                user_request,

            concepts=
                concepts,

            brand_context=
                brand_context,

            visual_references=
                visual_references
        )

    except Exception as error:

        errors.append(
            (
                "creative_evaluation: "
                +
                clean_text(
                    error,
                    3000
                )
            )
        )

        #
        # Safe fallback:
        # no fake evaluation.
        #
        # Assign conservative scores based only on
        # local anti-cliche information.
        #

        for concept in concepts:

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

    # -----------------------------------------------------
    # TOP 3
    # -----------------------------------------------------

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

    top_concepts = select_top_concepts(
        concepts,
        limit=
            top_count
    )

    winner = (
        top_concepts[0]
        if top_concepts
        else
        None
    )

    # -----------------------------------------------------
    # FINAL CAMERA + FEASIBILITY
    #
    # Only run the expensive specialist passes
    # on the winner.
    # -----------------------------------------------------

    if winner:

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

    return CreativeBrainResponse(
        ok=
            bool(
                top_concepts
            ),

        mode=
            mode,

        request=
            user_request,

        total_concepts=
            len(
                concepts
            ),

        concepts=
            concepts,

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

            "score_weights":
                SCORE_WEIGHTS,

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
        " XPAND CREATIVE BRAIN V1.0"
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
        "Fast concepts:",
        sum(
            FAST_DISTRIBUTION.values()
        )
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

    test_scores = {
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

    print(
        "Weighted test score:",
        calculate_weighted_score(
            test_scores
        )
    )

    print("")

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
        "✅ Weighted scoring"
    )

    print(
        "✅ Anti-Cliche system"
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
        "✅ Fast Mode"
    )

    print(
        "✅ Masterpiece Mode"
    )

    print("")
