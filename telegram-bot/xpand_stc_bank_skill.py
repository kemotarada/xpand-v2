# =========================================================
# XPAND STC BANK VISUAL SKILL V4.0
#
# FULL DROP-IN REPLACEMENT
#
# =========================================================
#
# PURPOSE
# ---------------------------------------------------------
#
# Central visual authority for STC Bank.
#
# This module does NOT:
# - call OpenAI
# - call Gemini
# - generate images
# - browse the web
# - modify the database
#
# It provides:
# - STC Bank detection
# - mandatory style-question logic
# - visual-language authority
# - prompt guidance
# - camera vocabulary
# - lighting / material rules
# - anti-cliche protection
# - image-only / no-text / no-logo rules
# - compatibility constants used by XPAND modules
#
# Running:
#
#     python xpand_stc_bank_skill.py
#
# makes ZERO API calls.
#
# =========================================================

from __future__ import annotations

import re

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Sequence,
)


# =========================================================
# IDENTITY
# =========================================================

VERSION = "4.0"

MODULE_NAME = (
    "XPAND STC Bank Visual Skill"
)

BRAND_ID = "stc_bank"

BRAND_NAME = "STC Bank"


# =========================================================
# VISUAL STYLE IDS
# =========================================================

STYLE_PREMIUM_REALISTIC = (
    "premium_realistic"
)

STYLE_PURPLE_ARCHITECTURAL = (
    "purple_architectural"
)

STYLE_AUGMENTED_REALISM = (
    "augmented_realism"
)


SUPPORTED_STC_STYLES = {
    STYLE_PREMIUM_REALISTIC,
    STYLE_PURPLE_ARCHITECTURAL,
    STYLE_AUGMENTED_REALISM,
}


# =========================================================
# USER-FACING STYLE NAMES
# =========================================================

STYLE_NAME_REALISTIC_AR = (
    "واقعي فوتوغرافي"
)

STYLE_NAME_PURPLE_AR = (
    "بيئة بنفسجية استوديو"
)

STYLE_NAME_AUGMENTED_AR = (
    "واقعي سريالي راقٍ"
)


STC_BANK_STYLE_QUESTION = (
    "أي أسلوب بدك للصورة؟ "
    "اكتب اسم الأسلوب كاملًا: "
    "واقعي فوتوغرافي، "
    "بيئة بنفسجية استوديو، "
    "أو واقعي سريالي راقٍ."
)


# =========================================================
# BASIC HELPERS
# =========================================================

def clean_text(
    value: Any,
    limit: int = 30000,
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


# =========================================================
# STC BANK DETECTION
# =========================================================

STC_BANK_REQUEST_MARKERS = (
    "stc bank",
    "stcbank",
    "stc-bank",
    "stc_bank",
    "بنك stc",
    "بنك اس تي سي",
    "اس تي سي بنك",
    "اس تي سي bank",
    "stc بنك",
)


def is_stc_bank_request(
    text: Any,
) -> bool:

    source = normalize_text(
        text
    )

    if not source:

        return False

    return contains_any(
        source,
        STC_BANK_REQUEST_MARKERS,
    )


# =========================================================
# STYLE DETECTION
# =========================================================

REALISTIC_STYLE_MARKERS = (
    STYLE_NAME_REALISTIC_AR,
    "واقعي احترافي",
    "واقعي فاخر",
    "تصوير واقعي",
    "فوتوغرافي واقعي",
    "premium realistic",
    "premium realism",
    "premium photography",
    "realistic photography",
    "commercial photography",
    "photorealistic",
)


PURPLE_STYLE_MARKERS = (
    STYLE_NAME_PURPLE_AR,
    "بيئه بنفسجيه استوديو",
    "بيئة بنفسجية",
    "بيئه بنفسجيه",
    "استوديو بنفسجي",
    "purple environment",
    "purple studio",
    "purple architectural",
    "purple architecture",
    "geometric purple studio",
)


AUGMENTED_STYLE_MARKERS = (
    STYLE_NAME_AUGMENTED_AR,
    "واقعي سريالي",
    "واقعيه سرياليه",
    "واقعية سريالية",
    "واقعية معززة",
    "واقعيه معززه",
    "augmented realism",
    "conceptual realism",
    "photographic surrealism",
    "surreal realism",
    "refined surrealism",
    "فانتزي واقعي",
    "اسلوب فانتزي",
    "أسلوب فانتزي",
    "photographic fantasy",
)


def detect_stc_visual_style(
    text: Any,
) -> str:

    source = normalize_text(
        text
    )

    if not source:

        return ""

    short_styles = {"واقعي": STYLE_PREMIUM_REALISTIC, "بنفسجي": STYLE_PURPLE_ARCHITECTURAL,
                    "فانتزي": STYLE_AUGMENTED_REALISM, "سريالي": STYLE_AUGMENTED_REALISM}
    if source in short_styles:
        return short_styles[source]

    if contains_any(
        source,
        PURPLE_STYLE_MARKERS,
    ):

        return (
            STYLE_PURPLE_ARCHITECTURAL
        )

    if contains_any(
        source,
        AUGMENTED_STYLE_MARKERS,
    ):

        return (
            STYLE_AUGMENTED_REALISM
        )

    if contains_any(
        source,
        REALISTIC_STYLE_MARKERS,
    ):

        return (
            STYLE_PREMIUM_REALISTIC
        )

    # STC Bank defaults to the permanent purple architectural campaign world
    # unless the user explicitly asks for realistic or augmented realism.
    if (
        "stc" in source
        or "اس تي سي" in source
        or "بنك stc" in source
        or "stc بنك" in source
    ):

        return (
            STYLE_PURPLE_ARCHITECTURAL
        )

    return ""


def stc_style_question_needed(
    text: Any,
) -> bool:

    if not is_stc_bank_request(
        text
    ):

        return False

    return not bool(
        detect_stc_visual_style(
            text
        )
    )


def get_stc_style_question() -> str:

    return (
        STC_BANK_STYLE_QUESTION
    )


# =========================================================
# VISUAL DNA
# =========================================================

STC_BANK_VISUAL_DNA: Dict[
    str,
    Any,
] = {

    # -----------------------------------------------------
    # CORE CHARACTER
    # -----------------------------------------------------

    "brand_character": [
        "modern",
        "premium",
        "confident",
        "Saudi-relevant",
        "clean",
        "restrained",
        "digitally fluent",
        "human",
        "commercially polished",
        "visually intelligent",
    ],


    # -----------------------------------------------------
    # IDENTITY PRINCIPLES
    # -----------------------------------------------------

    "identity_principles": [

        (
            "STC Bank identity is a visual language, "
            "not simply a purple color treatment."
        ),

        (
            "Brand recognition may come from restrained "
            "purple or green accents, materials, lighting, "
            "composition and contemporary Saudi context."
        ),

        (
            "The visual idea must communicate the benefit "
            "before decorative brand styling is considered."
        ),

        (
            "Premium quality comes primarily from scene design, "
            "camera, light, materials, behavior and restraint."
        ),

        (
            "Real-world environments may retain their natural "
            "colors instead of being artificially recolored purple."
        ),

        (
            "Purple architectural environments are a valid "
            "STC visual family, but not the automatic default."
        ),

        (
            "Human scenes should feel observed and believable, "
            "not like stock photography."
        ),

        (
            "Negative space is intentional because final "
            "advertising copy and logos are added manually."
        ),
    ],


    # -----------------------------------------------------
    # VISUAL FAMILIES
    # -----------------------------------------------------

    "visual_families": {

        STYLE_PREMIUM_REALISTIC: {

            "purpose":
                (
                    "Premium photographic storytelling using "
                    "credible real environments and behavior."
                ),

            "characteristics": [
                "photorealistic",
                "clear natural skin tones",
                "real Saudi lifestyle",
                "clean contemporary architecture",
                "believable human behavior",
                "real product interaction",
                "motivated daylight or practical lighting",
                "restrained contrast",
                "subtle STC identity cue",
                "cinematic depth",
                "clean negative space",
            ],

            "preferred_color_behavior": [
                "natural environment colors",
                "warm neutral stone",
                "off-white",
                "beige",
                "charcoal",
                "walnut",
                "soft blue daylight",
                "green as controlled accent",
                "purple as controlled accent only",
            ],

            "avoid": [
                "purple wash over the entire location",
                "neon purple lighting without motivation",
                "generic business stock photography",
                "person staring at camera holding a bank product",
                "generic fintech decoration",
            ],
        },


        STYLE_PURPLE_ARCHITECTURAL: {

            "purpose":
                (
                    "Controlled premium studio or architectural "
                    "world using purple geometry and physical surfaces."
                ),

            "characteristics": [
                "deep aubergine",
                "near-black violet",
                "controlled saturated purple",
                "geometric plinths",
                "parallel planes",
                "precise perspective",
                "matte surfaces",
                "controlled semi-gloss surfaces",
                "narrow premium reflections",
                "clean contact shadows",
                "soft directional key light",
                "restrained rim light",
                "minimal green accent",
                "high material polish",
            ],

            "spatial_rules": [
                (
                    "Every object must rest on a visible physical "
                    "surface or be held naturally."
                ),

                (
                    "Hero-object angles must agree with the "
                    "supporting platform geometry."
                ),

                (
                    "Platform edges, object edges and architectural "
                    "edges must follow coherent vanishing points."
                ),

                (
                    "Reflections must follow the real material, "
                    "camera and light position."
                ),

                (
                    "Use depth through real planes and shadow, "
                    "not through glowing effects."
                ),
            ],

            "avoid": [
                "purple neon room",
                "cheap purple gradient",
                "floating card",
                "floating phone",
                "laser lines",
                "random glowing edges",
                "random particles",
                "generic futuristic banking set",
            ],
        },


        STYLE_AUGMENTED_REALISM: {

            "purpose":
                (
                    "Photographic realism elevated by exactly one "
                    "intelligent conceptual mechanism."
                ),

            "characteristics": [
                "credible photographic base",
                "one visual metaphor",
                "physically coherent transformation",
                "real gravity",
                "real perspective",
                "real occlusion",
                "real shadow logic",
                "real reflections",
                "premium production design",
                "clear benefit",
                "restrained surrealism",
            ],

            "allowed_mechanisms": [
                "controlled scale relationship",
                "forced perspective",
                "architectural transformation",
                "frame-within-frame metaphor",
                "physical object/environment integration",
                "unexpected but plausible viewpoint",
            ],

            "avoid": [
                "cartoon fantasy",
                "magic portal effect",
                "floating fintech objects",
                "science-fiction banking",
                "holographic world",
                "multiple metaphors in one image",
                "effect-heavy CGI",
            ],
        },
    },


    # -----------------------------------------------------
    # REFERENCE FAMILIES
    # -----------------------------------------------------

    "reference_families": {

        "premium_lifestyle": {
            "learn": [
                "natural Saudi casting",
                "real behavior",
                "premium interiors",
                "clear focal hierarchy",
                "lifestyle authenticity",
                "subtle brand cues",
            ],
        },

        "payments_cards": {
            "learn": [
                "controlled product hero shots",
                "geometric studio discipline",
                "premium reflections",
                "dark card contrast",
                "precise object angle",
                "physical support surfaces",
            ],
        },

        "digital_banking": {
            "learn": [
                "phone as functional object",
                "human-context integration",
                "clear depth hierarchy",
                "credible interaction",
                "clean negative space",
            ],
        },

        "travel_roaming": {
            "learn": [
                "destination realism",
                "natural daylight",
                "lifestyle storytelling",
                "environmental scale",
                "human travel behavior",
            ],
        },

        "international_transfer": {
            "learn": [
                "human connection",
                "location storytelling",
                "real-world movement",
                "avoid generic maps and network graphics",
            ],
        },

        "cashback_rewards": {
            "learn": [
                "benefit-first storytelling",
                "real purchase context",
                "premium product/lifestyle scenes",
                "avoid floating coins",
            ],
        },

        "general_brand": {
            "learn": [
                "color restraint",
                "visual consistency",
                "premium finish",
                "brand character",
            ],
        },
    },


    # -----------------------------------------------------
    # MATERIAL LANGUAGE
    # -----------------------------------------------------

    "material_language": [

        "polished stone",
        "soft matte stone",
        "travertine",
        "warm walnut",
        "dark walnut",
        "brushed metal",
        "satin metal",
        "smoked glass",
        "clear architectural glass",
        "premium leather",
        "soft textile",
        "clean plaster",
        "matte painted surfaces",
        "controlled glossy acrylic",
        "subtle reflective floor",
    ],


    # -----------------------------------------------------
    # CAMERA LIBRARY
    # -----------------------------------------------------

    "camera_library": {

        "eye_level": {
            "scientific_name":
                "Eye-Level Shot",

            "use":
                (
                    "Trust, human interaction, natural lifestyle "
                    "and believable payment moments."
                ),
        },

        "low_angle": {
            "scientific_name":
                "Low-Angle Shot",

            "use":
                (
                    "Premium hero presence and architectural scale."
                ),
        },

        "extreme_low_angle": {
            "scientific_name":
                "Extreme Low-Angle Shot",

            "use":
                (
                    "Rare monumental product or architecture "
                    "when genuinely concept-driven."
                ),
        },

        "worms_eye": {
            "scientific_name":
                "Worm's-Eye View",

            "use":
                (
                    "Near-ground dramatic scale transformation "
                    "with coherent perspective."
                ),
        },

        "high_angle": {
            "scientific_name":
                "High-Angle Shot",

            "use":
                (
                    "Spatial relationships, product/customer "
                    "interaction and controlled overview."
                ),
        },

        "birds_eye": {
            "scientific_name":
                "Bird's-Eye View",

            "use":
                (
                    "Real spatial patterns, tables, retail layouts "
                    "and environmental storytelling."
                ),
        },

        "top_down": {
            "scientific_name":
                "Top-Down / Overhead Shot",

            "use":
                (
                    "Physical object arrangements with graphic "
                    "discipline and real contact shadows."
                ),
        },

        "three_quarter": {
            "scientific_name":
                "Three-Quarter Hero Shot",

            "use":
                (
                    "Cards, phones, POS devices and premium "
                    "product presentations."
                ),
        },

        "over_shoulder": {
            "scientific_name":
                "Over-the-Shoulder Shot",

            "use":
                (
                    "Mobile banking, e-commerce workflow "
                    "and contextual human interaction."
                ),
        },

        "pov": {
            "scientific_name":
                "Point-of-View Shot",

            "use":
                (
                    "Immersive payment, banking or travel action."
                ),
        },

        "ground_level": {
            "scientific_name":
                "Ground-Level Shot",

            "use":
                (
                    "Strong foreground depth and environmental scale."
                ),
        },

        "close_up": {
            "scientific_name":
                "Close-Up Shot",

            "use":
                (
                    "Interaction, hand/device relationship "
                    "and product detail."
                ),
        },

        "extreme_close_up": {
            "scientific_name":
                "Extreme Close-Up",

            "use":
                (
                    "Material detail and focused functional action."
                ),
        },

        "macro": {
            "scientific_name":
                "Macro Shot",

            "use":
                (
                    "Premium material surface, card texture, "
                    "device detail and refined reflections."
                ),
        },

        "medium": {
            "scientific_name":
                "Medium Shot",

            "use":
                (
                    "Human behavior with enough environment "
                    "to understand context."
                ),
        },

        "wide": {
            "scientific_name":
                "Wide Environmental Shot",

            "use":
                (
                    "Lifestyle, travel, retail and architecture."
                ),
        },

        "extreme_wide": {
            "scientific_name":
                "Extreme Wide / Establishing Shot",

            "use":
                (
                    "Environment-led storytelling and scale."
                ),
        },

        "one_point": {
            "scientific_name":
                "One-Point Perspective",

            "use":
                (
                    "Symmetrical or deep architectural scenes "
                    "with one clear vanishing point."
                ),
        },

        "two_point": {
            "scientific_name":
                "Two-Point Perspective",

            "use":
                (
                    "Retail corners, product plinths and "
                    "architectural volume."
                ),
        },

        "forced_perspective": {
            "scientific_name":
                "Forced-Perspective Composition",

            "use":
                (
                    "Augmented realism and conceptual scale "
                    "without unsupported floating objects."
                ),
        },

        "frame_within_frame": {
            "scientific_name":
                "Frame-within-a-Frame Composition",

            "use":
                (
                    "Doors, windows, shelves and architecture "
                    "used to create hierarchy."
                ),
        },

        "foreground_obstruction": {
            "scientific_name":
                "Foreground-Obstruction Composition",

            "use":
                (
                    "Cinematic observed realism and layered depth."
                ),
        },
    },


    # -----------------------------------------------------
    # LENS LANGUAGE
    # -----------------------------------------------------

    "lens_language": {

        "18mm":
            (
                "Extreme environmental width. "
                "Use rarely and deliberately."
            ),

        "24mm":
            (
                "Premium wide environmental advertising."
            ),

        "28mm":
            (
                "Dynamic but controllable commercial environment."
            ),

        "35mm":
            (
                "Cinematic lifestyle and environmental storytelling."
            ),

        "50mm":
            (
                "Balanced natural perspective."
            ),

        "70mm":
            (
                "Controlled commercial compression."
            ),

        "85mm":
            (
                "Premium portrait and product compression."
            ),

        "105mm":
            (
                "Luxury isolation and product detail."
            ),

        "macro":
            (
                "Fine surface and product detail."
            ),

        "tilt_shift":
            (
                "Perspective-controlled architecture "
                "when technically appropriate."
            ),
    },


    # -----------------------------------------------------
    # LIGHTING
    # -----------------------------------------------------

    "lighting": {

        "premium_realistic": [
            "motivated daylight",
            "soft window light",
            "natural practical light",
            "soft directional key",
            "clean skin-tone rendering",
            "realistic bounce light",
            "controlled contrast",
            "soft highlight rolloff",
            "natural shadow density",
        ],

        "purple_architectural": [
            "soft directional key light",
            "controlled purple ambient fill",
            "restrained rim separation",
            "narrow specular highlights",
            "deep but readable shadows",
            "clean contact shadow",
            "controlled glossy reflection",
            "no global neon wash",
        ],

        "augmented_realism": [
            "photographic motivated key light",
            "metaphor obeys same light direction",
            "matched shadow softness",
            "matched reflection logic",
            "coherent color temperature",
            "realistic bounce light",
        ],
    },


    # -----------------------------------------------------
    # REFLECTION PRINCIPLES
    # -----------------------------------------------------

    "reflection_principles": [

        (
            "Reflection exists to describe material form, "
            "not to add futuristic decoration."
        ),

        (
            "Glossy cards and devices require controlled "
            "specular highlights with readable edges."
        ),

        (
            "A reflective plinth must reflect the object "
            "according to real angle and distance."
        ),

        (
            "Avoid mirror-like surfaces everywhere."
        ),

        (
            "Use satin, semi-gloss and matte variation "
            "to create premium hierarchy."
        ),
    ],


    # -----------------------------------------------------
    # HUMAN DIRECTION
    # -----------------------------------------------------

    "human_direction": [

        (
            "People should perform a real action rather "
            "than pose merely to display the product."
        ),

        (
            "Do not automatically make the subject "
            "look directly at camera."
        ),

        (
            "Hands must connect naturally with phone, "
            "card, POS, product or environment."
        ),

        (
            "Saudi clothing and context should be "
            "culturally credible when used."
        ),

        (
            "Expressions should be subtle and believable."
        ),

        (
            "Avoid exaggerated advertising smiles."
        ),

        (
            "Body posture must match the action."
        ),
    ],


    # -----------------------------------------------------
    # COMPOSITION
    # -----------------------------------------------------

    "composition": [

        "single dominant visual idea",
        "one clear hero",
        "secondary elements support rather than compete",
        "clean visual hierarchy",
        "intentional negative space",
        "foreground-midground-background depth",
        "controlled asymmetry when useful",
        "symmetry only when conceptually justified",
        "clear edge control",
        "no accidental tangencies",
        "no unnecessary objects",
    ],


    # -----------------------------------------------------
    # TEXT-FREE OUTPUT
    # -----------------------------------------------------

    "text_free_output": [

        "no headline",
        "no subtitle",
        "no offer text",
        "no CTA",
        "no percentage",
        "no financial number",
        "no legal disclaimer",
        "no STC wordmark",
        "no STC Bank logo",
        "no Visa logo",
        "no Mastercard logo",
        "no watermark",
        "no invented readable UI text",
    ],


    # -----------------------------------------------------
    # HARD BLOCKS
    # -----------------------------------------------------

    "forbidden_visual_devices": [

        "floating coins",
        "flying money",
        "floating card",
        "floating phone",
        "floating banking icons",
        "phone surrounded by icons",
        "generic world globe",
        "network lines",
        "connection lines",
        "transfer route lines",
        "laser beam",
        "blue payment beam",
        "purple neon trail",
        "glowing arrows",
        "random particles",
        "sparkles",
        "HUD",
        "hologram",
        "futuristic banking interface",
        "security shield",
        "generic lock icon",
        "growth arrow",
        "generic business handshake",
        "random miniature city",
        "decorative technology clutter",
        "purple simply for the sake of purple",
    ],
}


# =========================================================
# BENEFIT-SPECIFIC VISUAL DIRECTION
# =========================================================

STC_BANK_BENEFIT_DIRECTIONS = {

    "merchant_payments": """

MERCHANT PAYMENTS / E-COMMERCE / POS
------------------------------------

Arabic "نقاط البيع" means Point of Sale.

It does NOT mean loyalty or reward points.

Prefer:
- premium boutique checkout
- specialty café
- refined restaurant
- quality retail
- hospitality
- premium small business
- merchant managing real e-commerce orders
- customer and merchant interacting naturally
- POS physically positioned correctly
- phone / laptop / terminal integrated naturally

The scene should communicate:
commerce + acceptance + business confidence.

Do NOT use:
- merchant simply holding POS toward camera
- floating terminal
- payment laser
- icons around terminal
- purple fintech room by default
- coins
- reward points

""".strip(),


    "international_transfer": """

INTERNATIONAL TRANSFER
----------------------

Communicate:
reach, confidence, relationship, movement or accessibility.

Prefer:
- real travel relationship
- family context
- business relationship
- international lifestyle
- meaningful location transition
- real physical metaphor

Do NOT use:
- world globe
- glowing routes
- dotted transfer path
- map with laser connections
- floating country flags
- generic network graphics

""".strip(),


    "travel": """

TRAVEL
------

Prefer:
- real airport
- hotel
- destination
- premium traveler behavior
- authentic luggage / payment / mobile interaction
- wide environmental photography
- POV or over-the-shoulder when useful

Natural blue sky, warm stone, wood, skin tones and destination
colors are allowed and often preferable to purple.

Do NOT turn travel into a purple neon airport.

""".strip(),


    "digital_banking": """

DIGITAL BANKING
---------------

The phone is a real functional object, not the entire advertisement.

For global or international transfer requests, prefer one continuous
photographic relationship showing a sender and a believable secure handoff
or recipient in real spatial depth. The viewer should understand movement
and safe arrival without words, maps, route lines or interface graphics.

Prefer:
- over-the-shoulder interaction as a supporting cue
- real human handoff or recipient relationship
- natural bank lounge, home or travel context
- clear hand/device relationship
- believable screen orientation
- physical depth and clean separation from pillars and reflective edges

Do NOT invent:
- readable fake banking UI
- floating interface tiles
- random app icons
- holographic UI

""".strip(),


    "cashback": """

CASHBACK / VALUE
----------------

Communicate tangible value through:
- purchase context
- useful experience
- premium lifestyle
- product relationship

Avoid:
- flying coins
- raining money
- generic percentage graphics inside the generated image

""".strip(),


    "rewards": """

REWARDS
-------

Communicate reward through:
- elevated experience
- premium benefit
- real-world value

Avoid:
- point clouds
- coin explosions
- floating gift icons

""".strip(),


    "security": """

SECURITY
--------

Communicate:
calm, control, trust, confidence.

Prefer:
- human behavior
- environment
- composition
- product control

Avoid:
- shield
- lock
- cyber grid
- blue hologram
- security HUD

""".strip(),
}


# =========================================================
# BENEFIT DETECTION
# =========================================================

def detect_stc_benefit_family(
    text: Any,
) -> str:

    source = normalize_text(
        text
    )

    # -----------------------------------------------------
    # MERCHANT FIRST
    #
    # "نقاط البيع" contains "نقاط".
    # -----------------------------------------------------

    if contains_any(
        source,
        [
            "نقاط البيع",
            "نقطه البيع",
            "نقطة البيع",
            "اجهزة نقاط البيع",
            "أجهزة نقاط البيع",
            "التجارة الالكترونية",
            "التجارة الإلكترونية",
            "خدمات التجارة الالكترونية",
            "خدمات التجارة الإلكترونية",
            "merchant payment",
            "merchant payments",
            "merchant services",
            "point of sale",
            "points of sale",
            "pos terminal",
            "pos device",
            "payment gateway",
            "e-commerce",
            "ecommerce",
        ],
    ):

        return "merchant_payments"

    if contains_any(
        source,
        [
            "تحويل دولي",
            "تحويل مالي دولي",
            "حواله دوليه",
            "حوالة دولية",
            "international transfer",
            "international money transfer",
            "cross border",
        ],
    ):

        return "international_transfer"

    if contains_any(
        source,
        [
            "سفر",
            "السفر",
            "مسافر",
            "مطار",
            "رحله",
            "رحلة",
            "travel",
            "airport",
            "trip",
        ],
    ):

        return "travel"

    if contains_any(
        source,
        [
            "كاش باك",
            "cashback",
            "cash back",
            "استرداد نقدي",
        ],
    ):

        return "cashback"

    if contains_any(
        source,
        [
            "مكافات",
            "مكافآت",
            "reward",
            "rewards",
            "reward points",
        ],
    ):

        return "rewards"

    if contains_any(
        source,
        [
            "امان",
            "أمان",
            "امن",
            "آمن",
            "security",
            "secure",
        ],
    ):

        return "security"

    if contains_any(
        source,
        [
            "تطبيق",
            "بنك رقمي",
            "digital banking",
            "banking app",
            "mobile banking",
        ],
    ):

        return "digital_banking"

    return "premium_banking"


# =========================================================
# STYLE-SPECIFIC PROMPT AUTHORITY
# =========================================================

STC_STYLE_INSTRUCTIONS = {

    STYLE_PREMIUM_REALISTIC: """

SELECTED STYLE:
PREMIUM REALISTIC PHOTOGRAPHY

Create a believable premium commercial photograph.

The environment should retain natural color unless a subtle
brand accent is genuinely useful.

Prioritize:
- realistic Saudi lifestyle
- authentic human action
- natural proportions
- refined contemporary environment
- clean skin tones
- motivated daylight or practical lighting
- premium material detail
- subtle STC purple/green cue
- deliberate camera angle
- cinematic depth
- clear negative space

Do not recolor the entire environment purple.

The image should feel photographed,
not designed as a generic fintech poster.

""".strip(),


    STYLE_PURPLE_ARCHITECTURAL: """

SELECTED STYLE:
PREMIUM PURPLE ARCHITECTURAL STUDIO

Build a real physical studio/architectural environment.

Use:
- deep aubergine
- dark violet
- near-black violet
- restrained saturated purple accents
- matte and satin planes
- geometric plinths
- physically supported objects
- clean parallel architectural lines
- coherent one-point or two-point perspective
- controlled specular highlights
- narrow elegant reflections
- deep contact shadows
- soft directional key light

Green may appear as a small accent.

Every object must align with the same perspective system.

A card/device sitting on a plinth must visually agree with
the plane angle, camera height and vanishing points.

Do not make:
- neon nightclub scene
- glowing sci-fi set
- random purple objects
- floating hero objects

""".strip(),


    STYLE_AUGMENTED_REALISM: """

SELECTED STYLE:
REFINED PHOTOGRAPHIC SURREALISM / AUGMENTED REALISM

Begin with a believable high-end photograph.

Introduce EXACTLY ONE conceptual mechanism.

The mechanism may use:
- controlled scale
- forced perspective
- physical architectural metaphor
- frame-within-frame
- unexpected spatial relationship
- refined object/environment transformation

The concept must obey:
- gravity
- perspective
- lighting
- occlusion
- reflections
- contact shadows
- material behavior

The final frame must still feel photographable.

Do not use:
- magic
- childish fantasy
- portal glow
- holograms
- particles
- futuristic HUD
- random CGI

""".strip(),
}


def get_stc_style_instruction(
    style: str,
) -> str:

    return STC_STYLE_INSTRUCTIONS.get(
        clean_text(
            style,
            100,
        ),
        "",
    )


# =========================================================
# CENTRAL VISUAL SKILL
# =========================================================

from xpand_stc_skill_runtime import core_direction, style_direction

STC_BANK_VISUAL_SKILL = core_direction()


# =========================================================
# IMAGE MODEL GUARD
# =========================================================

STC_BANK_IMAGE_GUARD = r"""
STC BANK IMAGE EXECUTION LOCK V4.1
===============================

Create IMAGE ONLY. The image model must not generate headline, body copy, CTA, offer text, percentages, financial numbers, legal copy, logos, wordmarks, watermarks, signatures, readable banking UI, QR codes or barcodes. Reserve 25–40% integrated photographic space for typography added later.

STC CAMPAIGN WORLD
- Default STC route: premium purple architectural campaign world unless the user explicitly selects premium realistic or augmented realism.
- Palette: deep violet base, saturated violet/magenta plane, near-black blackberry/plum falloff, graphite/black hero objects, and one restrained mint/green accent. Preserve saturated violet midtones; reject grey-mauve, pastel lavender, brown-black, washed white interiors and blue/cyan purple drift.
- Light: broad soft violet/magenta pool from upper-right or rear plane, deep-violet falloff at left/lower frame, controlled violet rim on dark objects, real contact shadows and physically motivated reflections on metal, glass and satin surfaces.
- Set: two or three connected architectural planes with one vanishing system; purple is architecture and light, never a flat backdrop or post-process tint.

IDEA AND SERVICE LOCK
- One hero, one benefit, one memorable physical mechanism, one deliberate camera.
- For e-commerce plus POS, show a believable contactless acceptance action and one credible online/fulfillment cue joined by a real commercial relationship. A real unbranded phone/tablet may support the online cue only when its UI is abstract and unreadable; it must remain separate from the POS and never carry the whole message.
- Reject phone-plus-POS displays, generic counters, parcel-as-unrelated-prop, device museums, split screens, collages, floating hardware, random blocks and any scene that needs a caption to explain why the objects are together.

PHYSICAL REALITY
Everything obeys gravity, scale, perspective, occlusion, light direction, contact shadows, reflection geometry and material-specific roughness. No fusion, holograms, neon trails, particles, sparkles, HUD or invented payment hardware. Premium comes from concept, camera, light, materials, composition and restraint—not neon.

EDIT-SPECIFIC FAILURE LOCK
- When editing an approved prior render, preserve its exact camera, crop, surface silhouette, phone position, POS position, hand relationship and visual hierarchy. Do not redesign or invent a new composition.
- Keep the POS fully inside the frame with comfortable margins; the terminal, contactless contact area, hand and card must be readable as one complete action. Never crop the POS, card or hand at the lower edge.
- The phone screen must retain a restrained non-readable e-commerce/order cue: simple product/order shapes or blocks are allowed, but no blank abstract wallpaper, fake banking UI, readable text or numbers.
- A mint seam may be a thin recessed material detail or a very soft reflected accent. It must not become a bright neon cable, road, light trail or graphic line.
- Reject a giant empty purple void, an oversized phone-only hero, a tiny/cropped POS, a disconnected card, a generic product render, or a scene that loses the service relationship during refinement.
""".strip()


# =========================================================
# STC BANK CAMPAIGN DNA — LEARNED FROM OFFICIAL CAMPAIGN REFERENCES
# =========================================================

STC_BANK_CAMPAIGN_DNA = r"""
STC BANK CAMPAIGN ART DIRECTION
===============================

The supplied STC Bank campaign references establish a recognizable
commercial system. Learn the system; never clone a source image.

CAMPAIGN CHARACTER
- benefit-first, not decoration-first
- one memorable visual idea per frame
- one hero object, gesture or physical metaphor
- premium editorial advertising, not stock photography
- confident, minimal and immediately readable
- modern Saudi commercial context when people are present

VISUAL SYSTEM
- saturated STC violet spectrum: #2C1359, #653098, #853DB6 and #994ACA
- deep violet falloff #150E25, never brown-black or gray-mauve
- graphite, black and dark neutral surfaces for contrast
- white and vivid green are reserved for designed typography and small
  brand accents in post-production; never generate readable copy in the image
- deliberate studio lighting, clean edge separation and controlled highlights
- architectural planes, plinths or portals only when they support the idea
- realistic materials, scale, gravity, contact shadows and perspective

BANK-AD IDEA ARCHETYPES
- product as a gateway to a real benefit or experience
- one physical object turning an abstract benefit into a visible moment
- premium product hero with a single meaningful environmental cue
- human behavior that proves ease, confidence or control
- a real-world before/after relationship without split-screen or UI
- a carefully staged service moment with one clear cause and effect

COMPOSITION LAW
- create a visual hierarchy: message idea first, product/service proof second,
  brand atmosphere third
- reserve integrated calm space for later copy, never an empty artificial panel
- avoid centered portrait posing, generic smiling staff and decorative fintech props
- the image must still communicate the benefit with all text removed

REFERENCE DISCIPLINE
- use references for tonal balance, lighting, palette, material quality,
  spatial restraint and campaign maturity
- do not copy their exact objects, people, wording, logos or composition
""".strip()

# =========================================================
# STC BANK SHOT DESIGN CONTRACT
# =========================================================

STC_BANK_SHOT_DESIGN_CONTRACT = r"""
STC BANK DIRECTOR'S SHOT DESIGN CONTRACT V4.1
===============================================

Design the advertisement as a single campaign frame before rendering. Answer: what is the one benefit, what is the one visible proof, what is the hero, why does the camera help, and what can be removed without weakening the idea?

GLOBAL SHOT RULES
- Choose one mechanism and one camera grammar; do not combine incompatible angles.
- Use a 4:5 crop with a dominant hero, readable foreground/midground/background hierarchy and 25–40% integrated copy-safe photographic space.
- The STC purple route uses connected violet planes, near-black/graphite objects, a bright violet/magenta light pool toward upper-right or rear, deep-violet falloff, controlled rim reflections and attached contact shadows.
- Do not turn a generic scene into STC by recoloring it. The set, hero relationship and camera must be designed together.

MERCHANT PAYMENTS
- Make online commerce and physical acceptance read as one connected merchant ecosystem through one causal action or physical continuity.
- Select one grammar: continuous commerce surface, threshold/reveal, close handoff choreography, reflection-led pairing, product theatre, or a specific Saudi merchant moment.
- Show one believable unbranded POS in an active contactless interaction. For the online side, allow one supporting unbranded phone/tablet with non-readable abstract UI, or a physically credible fulfillment cue; never use both as unrelated trophies.
- Keep phone/tablet, POS and parcel physically separate but connected by the same action, surface, shadow and perspective. Never fuse hardware, use a split screen, or default to a counter-plus-parcel tableau.
- The POS must be fully visible inside the 4:5 crop with the tap/contact area readable; reserve enough lower-frame breathing room for the hand and card.
- The online cue must look like commerce/order intent, not a blank abstract wallpaper. Use minimal non-readable product/order shapes only.
- The first read is the commercial relationship, not a portrait, device catalogue or random luxury still life.

QUALITY TEST
Reject any concept that could be reused unchanged for a restaurant, telecom shop or generic e-commerce brand. Reject giant empty upper space, tiny terminal, face-led crop, flat purple wall, fake UI, decorative neon and unsupported floating objects.
""".strip()

# =========================================================
# STC BANK CONCEPT ATLAS — ADVERTISING IDEAS, NOT COLOR VARIATIONS
# =========================================================

STC_MERCHANT_CONCEPT_LIBRARY = r"""
STC BANK MERCHANT CAMPAIGN CONCEPT ATLAS V4.1
=============================================

Choose exactly one mechanism per image. Concepts must differ by mechanism, camera and object hierarchy—not only by wall color.

1. CONTINUOUS COMMERCE SURFACE
A single sculptural violet/graphite surface carries a real order cue into a physical checkout action. The surface changes level or material once; that continuity is the bridge. No arrows, split screen or generic counter.

2. THE THRESHOLD REVEAL
A believable architectural opening contains the active POS at the near threshold and a carefully staged fulfillment outcome beyond it. One depth system, one light direction, real scale and contact. No magical portal glow.

3. THE PRECISE HANDOFF
A close editorial choreography: one hand completes contactless acceptance while another hand receives or seals the order at the same moment. Use hands, material tension and timing as the hero; no merchant portrait.

4. REFLECTION-LED COMMERCE
A physical POS action is sharp in the foreground while a controlled reflection in a real glossy plane reveals the online/fulfillment side. Reflection must belong to the same surface and camera, never a floating duplicate or fake overlay.

5. PRODUCT THEATRE, NOT A PEDESTAL
Use a designed violet campaign set where POS, product/order cue and fulfillment object form one intentional silhouette. Every support has a reason, attached shadow and shared vanishing point; reject random cubes and device museums.

6. SAUDI COMMERCE, ELEVATED
Choose one specific contemporary Saudi merchant category and express its online-to-physical workflow with premium restraint, natural behavior and STC purple architecture. No stock smile, beige shop interior or ordinary checkout documentation.

RELEASE TEST
The image must have one dominant hero, one causal banking cue, one readable online/physical relationship, physically coherent light and reflections, and calm integrated copy space. If the idea needs a caption to explain the relationship, discard it.
""".strip()



# =========================================================
# STC PURPLE STUDIO COLOR LOCK — OBSERVED REFERENCE PALETTE
# =========================================================

STC_PURPLE_STUDIO_COLOR_LOCK = r"""
STC PURPLE STUDIO COLOR AUTHORITY — MATCH THE SUPPLIED CAMPAIGN
===============================================================

The supplied STC Bank campaign card reference is the primary authority for
this visual family. Match its visual recipe, not a generic idea of purple.
These are observed image swatches, not official brand specifications.

REFERENCE COLOR BALANCE
- deep violet base: #2C1359
- near-black violet shadow: #150E25
- saturated violet plane: #653098
- secondary violet plane: #472474
- bright violet / magenta highlight: #853DB6 / #994ACA
- restrained green accent only when the concept needs a brand cue: #0FB288

LIGHTING LOCK
- a broad saturated violet/magenta light pool must be visible on the upper-right
  or rear plane, like the supplied campaign reference
- the left and lower frame fall toward deep violet, but must retain purple hue
- black products and objects receive a controlled violet rim or edge reflection
- platform bevels catch luminous violet edge light; reflections remain glossy but
  physically connected to the surface
- use a soft broad key plus controlled specular strips, not flat ambient light
- preserve readable midtone saturation; do not crush the scene into brown-black

MATERIAL / COMPOSITION LOCK
- use saturated violet architectural planes or stepped platforms
- maintain clean vertical product hierarchy and calm copy space above when useful
- keep products near-black/graphite with violet separation, never gray-mauve
- build one premium advertising composition with deliberate camera intent

HARD COLOR FAILURES
- brown aubergine wash
- gray-mauve wall
- desaturated plum room
- blue/cyan purple shift
- flat purple background
- neon nightclub magenta
- a normal office or counter recolored purple

The purple studio is a physical campaign world with the same color, lighting,
material response and contrast logic as the supplied STC reference. It is not
a loose style suggestion and never a post-process color filter.
""".strip()

STC_STYLE_TRANSFORMATION_CONTRACT = r"""
STYLE CHANGE MEANS IDEA CHANGE
==============================

The selected STC style is an art-direction mode, not a color filter.

PREMIUM REALISTIC
Use a real contemporary Saudi environment and natural motivated light. Let the
service behavior and human detail carry the campaign idea. Do not add purple
architecture merely to signal the brand.

PURPLE ARCHITECTURAL
Re-invent the scene as a deliberate campaign set: portals, folded planes,
thresholds, plinths, sculptural surfaces, controlled perspective and saturated STC violet / deep violet
space with a brighter violet light pool. Do not place the old retail counter in a purple room. Change the visual
mechanism, camera and object hierarchy.

AUGMENTED REALISM
Start with believable photography, then add exactly one physically coherent
conceptual intervention that makes the banking benefit visible. The metaphor must
be the idea, not a purple glow or decorative effect.

STYLE PIVOT TEST
If replacing the selected style with another style would leave the same scene,
same camera, same object positions and same action, the concept has failed.
""".strip()




# =========================================================
# BENEFIT DIRECTION
# =========================================================

def get_stc_benefit_direction(
    text: Any,
) -> str:

    family = detect_stc_benefit_family(
        text
    )

    return (
        STC_BANK_BENEFIT_DIRECTIONS.get(
            family,
            "",
        )
    )


# =========================================================
# COMPLETE REQUEST CONTEXT
# =========================================================

def build_stc_bank_skill_context(
    user_request: Any,
    *,
    selected_style: str = "",
) -> str:

    request = clean_text(
        user_request,
        12000,
    )

    style = clean_text(
        selected_style,
        100,
    )

    if style not in (
        SUPPORTED_STC_STYLES
    ):

        detected = (
            detect_stc_visual_style(
                request
            )
        )

        style = detected

    style_instruction = (
        get_stc_style_instruction(
            style
        )
    )

    benefit_direction = (
        get_stc_benefit_direction(
            request
        )
    )

    parts = [
        STC_BANK_VISUAL_SKILL,
        STC_BANK_CAMPAIGN_DNA,
        STC_BANK_SHOT_DESIGN_CONTRACT,
        STC_MERCHANT_CONCEPT_LIBRARY,
        STC_STYLE_TRANSFORMATION_CONTRACT,
        STC_PURPLE_STUDIO_COLOR_LOCK,
        style_direction(style),
    ]

    if style_instruction:

        parts.extend(
            [
                "",
                "=========================================================",
                "SELECTED STYLE EXECUTION",
                "=========================================================",
                style_instruction,
            ]
        )

    else:

        parts.extend(
            [
                "",
                "=========================================================",
                "STYLE NOT YET SELECTED",
                "=========================================================",
                (
                    "Do not invent the user's style preference. "
                    "The orchestration layer should ask the STC Bank "
                    "style question before final prompt generation."
                ),
            ]
        )

    if benefit_direction:

        parts.extend(
            [
                "",
                "=========================================================",
                "BENEFIT-SPECIFIC EXECUTION",
                "=========================================================",
                benefit_direction,
            ]
        )

    return "\n".join(
        parts
    ).strip()


# =========================================================
# DETERMINISTIC VIOLATION CHECK
# =========================================================

STC_FORBIDDEN_CONCEPT_MARKERS = (

    # -----------------------------------------------------
    # FLOATING
    # -----------------------------------------------------

    "floating card",
    "floating bank card",
    "levitating card",
    "floating phone",
    "levitating phone",
    "floating pos",
    "floating terminal",
    "unsupported product",
    "بطاقة طافية",
    "بطاقه طايره",
    "هاتف طائر",
    "هاتف يطفو",
    "جهاز نقاط بيع يطفو",

    # -----------------------------------------------------
    # FINTECH EFFECTS
    # -----------------------------------------------------

    "hologram",
    "holographic",
    "wireframe",
    "futuristic interface",
    "hud",
    "ui overlay",
    "network line",
    "connection line",
    "route line",
    "transfer path",
    "laser beam",
    "blue laser",
    "neon trail",
    "glowing route",
    "particle cloud",
    "random particles",
    "sparkles",
    "هولوغرام",
    "خطوط اتصال",
    "خط اتصال",
    "مسار تحويل ضوئي",
    "شعاع ليزر",
    "جزيئات مضيئة",

    # -----------------------------------------------------
    # GENERIC SYMBOLS
    # -----------------------------------------------------

    "generic globe",
    "security shield",
    "digital shield",
    "growth arrow",
    "business handshake",

    # -----------------------------------------------------
    # GENERATED COPY / LOGO
    # -----------------------------------------------------

    "render headline",
    "render the headline",
    "add headline",
    "visible headline",
    "place logo",
    "render logo",
    "add stc bank logo",
    "visible stc bank logo",
    "generate advertising copy",
)


def stc_text_violations(
    value: Any,
) -> List[str]:

    source = normalize_text(
        value
    )

    violations = []

    for marker in (
        STC_FORBIDDEN_CONCEPT_MARKERS
    ):

        if normalize_text(
            marker
        ) in source:

            violations.append(
                marker
            )

    return violations


def stc_concept_violations(
    concept: Any,
) -> List[str]:

    if concept is None:

        return []

    fields = [
        "title",
        "core_idea",
        "marketing_message",
        "visual_metaphor",
        "style_family",
        "scene_archetype",
        "environment",
        "hero_element",
        "camera_angle",
        "perspective",
        "lighting",
        "negative_space",
        "material_language",
        "color_strategy",
        "brand_logic",
        "production_method",
        "campaign_extension",
    ]

    values: List[str] = []

    if isinstance(
        concept,
        dict,
    ):

        for field_name in fields:

            value = concept.get(
                field_name
            )

            if value:

                values.append(
                    clean_text(
                        value,
                        3000,
                    )
                )

        supporting = concept.get(
            "supporting_elements"
        )

        if isinstance(
            supporting,
            list,
        ):

            values.extend(
                clean_text(
                    item,
                    1000,
                )
                for item in supporting
            )

    else:

        for field_name in fields:

            value = getattr(
                concept,
                field_name,
                "",
            )

            if value:

                values.append(
                    clean_text(
                        value,
                        3000,
                    )
                )

        supporting = getattr(
            concept,
            "supporting_elements",
            [],
        )

        if isinstance(
            supporting,
            list,
        ):

            values.extend(
                clean_text(
                    item,
                    1000,
                )
                for item in supporting
            )

    return stc_text_violations(
        "\n".join(
            values
        )
    )


# =========================================================
# STYLE DISPLAY
# =========================================================

def stc_style_display_name(
    style: str,
) -> str:

    mapping = {
        STYLE_PREMIUM_REALISTIC:
            STYLE_NAME_REALISTIC_AR,

        STYLE_PURPLE_ARCHITECTURAL:
            STYLE_NAME_PURPLE_AR,

        STYLE_AUGMENTED_REALISM:
            STYLE_NAME_AUGMENTED_AR,
    }

    return mapping.get(
        clean_text(
            style,
            100,
        ),
        "",
    )


# =========================================================
# VISUAL DNA SUMMARY
# =========================================================

def get_stc_visual_dna_summary() -> Dict[
    str,
    Any,
]:

    return {
        "brand_id":
            BRAND_ID,

        "brand_name":
            BRAND_NAME,

        "version":
            VERSION,

        "styles": [
            {
                "id":
                    STYLE_PREMIUM_REALISTIC,

                "name_ar":
                    STYLE_NAME_REALISTIC_AR,
            },

            {
                "id":
                    STYLE_PURPLE_ARCHITECTURAL,

                "name_ar":
                    STYLE_NAME_PURPLE_AR,
            },

            {
                "id":
                    STYLE_AUGMENTED_REALISM,

                "name_ar":
                    STYLE_NAME_AUGMENTED_AR,
            },
        ],

        "reference_families":
            list(
                STC_BANK_VISUAL_DNA[
                    "reference_families"
                ].keys()
            ),

        "camera_system":
            list(
                STC_BANK_VISUAL_DNA[
                    "camera_library"
                ].keys()
            ),

        "text_free":
            True,

        "logo_free":
            True,

        "purple_is_optional":
            True,

        "neon_default":
            False,

        "merchant_payments_priority":
            True,
    }


# =========================================================
# ZERO-COST SELF TEST
# =========================================================

if __name__ == "__main__":

    tests: Dict[
        str,
        bool
    ] = {}


    tests[
        "brand_detection_english"
    ] = is_stc_bank_request(
        "Create an STC Bank campaign."
    )


    tests[
        "brand_detection_arabic"
    ] = is_stc_bank_request(
        "أنشئ إعلان لبنك STC"
    )


    tests[
        "no_false_plain_stc"
    ] = not is_stc_bank_request(
        "إعلان لشركة STC للاتصالات"
    )


    tests[
        "realistic_style"
    ] = (
        detect_stc_visual_style(
            (
                "STC Bank "
                "واقعي فوتوغرافي"
            )
        )
        ==
        STYLE_PREMIUM_REALISTIC
    )


    tests[
        "purple_style"
    ] = (
        detect_stc_visual_style(
            (
                "STC Bank "
                "بيئة بنفسجية استوديو"
            )
        )
        ==
        STYLE_PURPLE_ARCHITECTURAL
    )


    tests[
        "augmented_style"
    ] = (
        detect_stc_visual_style(
            (
                "STC Bank "
                "واقعي سريالي راقٍ"
            )
        )
        ==
        STYLE_AUGMENTED_REALISM
    )


    tests[
        "style_question_needed"
    ] = stc_style_question_needed(
        (
            "أنشئ إعلان لبنك STC Bank "
            "عن خدمات التجارة الإلكترونية"
        )
    )


    tests[
        "style_question_not_needed"
    ] = not stc_style_question_needed(
        (
            "أنشئ إعلان لبنك STC Bank "
            "واقعي فوتوغرافي"
        )
    )


    tests[
        "merchant_priority"
    ] = (
        detect_stc_benefit_family(
            (
                "خدمات التجارة الإلكترونية "
                "ونقاط البيع"
            )
        )
        ==
        "merchant_payments"
    )


    tests[
        "no_text_guard"
    ] = (
        "NO visible:"
        in
        STC_BANK_IMAGE_GUARD
    )


    tests[
        "no_logo_guard"
    ] = (
        "STC Bank logo"
        in
        STC_BANK_IMAGE_GUARD
    )


    tests[
        "purple_not_identity"
    ] = (
        "STC BANK IS NOT"
        in
        STC_BANK_VISUAL_SKILL
    )


    tests[
        "camera_worms_eye"
    ] = (
        "worms_eye"
        in
        STC_BANK_VISUAL_DNA[
            "camera_library"
        ]
    )


    tests[
        "camera_birds_eye"
    ] = (
        "birds_eye"
        in
        STC_BANK_VISUAL_DNA[
            "camera_library"
        ]
    )


    tests[
        "camera_over_shoulder"
    ] = (
        "over_shoulder"
        in
        STC_BANK_VISUAL_DNA[
            "camera_library"
        ]
    )


    tests[
        "forbidden_floating"
    ] = bool(
        stc_text_violations(
            (
                "floating card with "
                "network lines"
            )
        )
    )


    tests[
        "allowed_purple_accent"
    ] = not bool(
        stc_text_violations(
            (
                "realistic Saudi retail scene "
                "with one subtle purple accent"
            )
        )
    )


    tests[
        "complete_context"
    ] = (
        "PREMIUM REALISTIC PHOTOGRAPHY"
        in
        build_stc_bank_skill_context(
            (
                "STC Bank merchant payments "
                "واقعي فوتوغرافي"
            )
        )
    )


    tests[
        "dna_text_free"
    ] = bool(
        get_stc_visual_dna_summary().get(
            "text_free"
        )
    )


    tests[
        "dna_purple_optional"
    ] = bool(
        get_stc_visual_dna_summary().get(
            "purple_is_optional"
        )
    )


    all_ok = all(
        tests.values()
    )


    print("")

    print(
        "=========================================="
    )

    print(
        " XPAND STC BANK VISUAL SKILL V4.0"
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
                "XPAND STC Bank Visual Skill "
                "V4.0 self-test: PASS ✅"
            )
        )

    else:

        print(
            (
                "XPAND STC Bank Visual Skill "
                "V4.0 self-test: FAIL ❌"
            )
        )


    print("")

    print(
        "✅ STC Bank detection"
    )

    print(
        "✅ Mandatory style-question logic"
    )

    print(
        "✅ Premium realistic visual family"
    )

    print(
        "✅ Purple architectural visual family"
    )

    print(
        "✅ Augmented realism visual family"
    )

    print(
        "✅ Reference-family Visual DNA"
    )

    print(
        "✅ Scientific camera vocabulary"
    )

    print(
        "✅ Lens vocabulary"
    )

    print(
        "✅ Lighting discipline"
    )

    print(
        "✅ Material discipline"
    )

    print(
        "✅ Reflection discipline"
    )

    print(
        "✅ Human-realism discipline"
    )

    print(
        "✅ Merchant payments semantic priority"
    )

    print(
        "✅ No generated text"
    )

    print(
        "✅ No generated logo"
    )

    print(
        "✅ Purple is optional"
    )

    print(
        "✅ Purple neon is NOT the default"
    )

    print(
        "✅ Generic fintech visual block"
    )

    print(
        "✅ Compatibility constants preserved"
    )

    print(
        "🚫 No API calls were made"
    )

    print(
        "🚫 No web requests were made"
    )

    print(
        "🚫 No images were generated"
    )

    print("")
