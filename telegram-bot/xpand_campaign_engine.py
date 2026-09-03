# =========================================================
# XPAND CAMPAIGN CONSISTENCY ENGINE V1.1
#
# Creates and maintains a Campaign Visual Bible.
#
# =========================================================
# V1.1
# =========================================================
#
# FIXES:
#
# - Prevents Campaign Bible max_output_tokens failures
# - Splits Bible generation into:
#
#       Core Visual Bible
#               ↓
#       Batched Asset Planning
#
# - Uses explicit Structured JSON mode
# - Uses compact prompt contexts
# - Uses safe prompt budgets
# - Never truncates JSON blindly inside prompts
# - Validates model output
# - Supports strict Masterpiece mode
# - Truthful fallback metadata
# - Batched asset planning for campaigns up to 30 assets
# - Keeps source-confidence system
# - Keeps 6–12 month freshness policy
#
#
# IMPORTANT
# ---------------------------------------------------------
#
# This module DOES NOT generate images.
#
# In normal compatibility mode:
#
#     allow_fallback=True
#
# If model creation fails, a clearly marked deterministic
# fallback Bible may be returned.
#
# In Masterpiece mode the orchestrator should call:
#
#     allow_fallback=False
#
# Then Campaign Bible failure stops production instead of
# pretending that an AI-created Bible succeeded.
#
#
# Self-test:
#
#     python xpand_campaign_engine.py
#
# Makes NO API calls.
# =========================================================

from __future__ import annotations

import hashlib
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
)


# =========================================================
# XPAND MODULES
# =========================================================

from xpand_image_engine import (
    call_openai_director,
)

from xpand_brand_memory import (
    load_campaign_bible,
    save_campaign_bible,
    safe_brand_id,
)


# =========================================================
# MODULE
# =========================================================

VERSION = "1.1"

MODULE_NAME = (
    "XPAND Campaign Consistency Engine"
)


# =========================================================
# DEFAULT POLICY
# =========================================================

DEFAULT_CAMPAIGN_ASSET_COUNT = 5


FRESHNESS_POLICY = {
    "preferred_recent_window_months":
        12,

    "strong_recent_window_months":
        6,

    "official_sources_priority":
        True,

    "recent_campaigns_priority":
        True,

    "evergreen_brand_identity_preserved":
        True,
}


SOURCE_CONFIDENCE_LEVELS = {
    "official_brand_source":
        100,

    "official_campaign_source":
        100,

    "agency_case_study":
        90,

    "verified_brand_partner":
        85,

    "recent_industry_reference":
        75,

    "creative_reference":
        60,

    "competitor_reference":
        55,

    "search_snippet":
        45,

    "inference":
        35,
}


# =========================================================
# PROMPT BUDGETS
# =========================================================

CAMPAIGN_PROMPT_HARD_LIMIT = max(
    12000,
    min(
        30000,
        int(
            os.environ.get(
                "XPAND_CAMPAIGN_PROMPT_HARD_LIMIT",
                "26000"
            )
            or
            26000
        )
    )
)


CORE_PROMPT_BUDGET = max(
    12000,
    min(
        CAMPAIGN_PROMPT_HARD_LIMIT,
        int(
            os.environ.get(
                "XPAND_CAMPAIGN_CORE_PROMPT_BUDGET",
                "24000"
            )
            or
            24000
        )
    )
)


ASSET_PLAN_PROMPT_BUDGET = max(
    10000,
    min(
        CAMPAIGN_PROMPT_HARD_LIMIT,
        int(
            os.environ.get(
                "XPAND_CAMPAIGN_ASSET_PROMPT_BUDGET",
                "21000"
            )
            or
            21000
        )
    )
)


EXECUTION_CONTEXT_BUDGET = max(
    6000,
    min(
        20000,
        int(
            os.environ.get(
                "XPAND_CAMPAIGN_EXECUTION_CONTEXT_BUDGET",
                "14000"
            )
            or
            14000
        )
    )
)


ASSET_PLAN_BATCH_SIZE = max(
    1,
    min(
        8,
        int(
            os.environ.get(
                "XPAND_CAMPAIGN_ASSET_BATCH_SIZE",
                "5"
            )
            or
            5
        )
    )
)


# =========================================================
# CAMERA ROTATION LIBRARY
# =========================================================

CAMERA_ROTATION_LIBRARY = [
    {
        "name":
            "Three-Quarter Hero Shot",

        "best_for":
            "product hero / card / phone / package",
    },

    {
        "name":
            "Over-the-Shoulder",

        "best_for":
            "human interaction / banking app / transaction",
    },

    {
        "name":
            "Wide Environmental Shot",

        "best_for":
            "lifestyle / travel / brand world",
    },

    {
        "name":
            "Low-Angle Hero Shot",

        "best_for":
            "premium status / authority / scale",
    },

    {
        "name":
            "Bird’s-Eye View",

        "best_for":
            "systems / routes / relationships",
    },

    {
        "name":
            "Macro Product Detail",

        "best_for":
            "materials / product craftsmanship",
    },

    {
        "name":
            "Forced Perspective",

        "best_for":
            "visual metaphor / conceptual advertising",
    },

    {
        "name":
            "Ground-Level Shot",

        "best_for":
            "motion / travel / road / dynamic foreground",
    },

    {
        "name":
            "Central One-Point Perspective",

        "best_for":
            "precision / trust / clean architectural scene",
    },

    {
        "name":
            "Frame-within-a-Frame",

        "best_for":
            "cinematic storytelling / architecture / travel",
    },
]


# =========================================================
# DATA MODEL
# =========================================================

@dataclass
class CampaignBible:

    campaign_key: str

    brand_id: str

    title: str

    campaign_goal: str

    asset_count: int

    visual_world: Dict[str, Any]

    color_system: Dict[str, Any]

    lighting_system: Dict[str, Any]

    material_system: Dict[str, Any]

    camera_system: Dict[str, Any]

    composition_system: Dict[str, Any]

    typography_system: Dict[str, Any]

    product_system: Dict[str, Any]

    character_system: Dict[str, Any]

    environment_system: Dict[str, Any]

    metaphor_system: Dict[str, Any]

    consistency_rules: List[str]

    variation_rules: List[str]

    forbidden_drift: List[str]

    asset_plan: List[Dict[str, Any]]

    research_policy: Dict[str, Any]

    source_confidence: List[Dict[str, Any]]

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


# =========================================================
# BASIC HELPERS
# =========================================================

def clean_text(
    value: Any,
    limit: int = 20000
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


def safe_list(
    value: Any
) -> List[Any]:

    return (
        value
        if isinstance(
            value,
            list
        )
        else
        []
    )


def safe_dict(
    value: Any
) -> Dict[str, Any]:

    return (
        value
        if isinstance(
            value,
            dict
        )
        else
        {}
    )


# =========================================================
# CONTEXT COMPACTION
# =========================================================

DROP_CONTEXT_KEYS = {
    "image_bytes",
    "raw_bytes",
    "source_bytes",
    "binary",
    "base64",
    "b64_json",
    "telegram_file_id",
    "telegram_file_unique_id",
    "photo_file_id",
    "document_file_id",
    "document_file_unique_id",
}


def reduce_prompt_value(
    value: Any,
    *,
    depth: int = 0,
    max_depth: int = 4,
    list_limit: int = 8,
    dict_limit: int = 40,
    string_limit: int = 1000
) -> Any:

    if depth > max_depth:

        if isinstance(
            value,
            dict
        ):

            return {
                "_summary":
                    "nested object omitted"
            }

        if isinstance(
            value,
            list
        ):

            return [
                "nested list omitted"
            ]

        return clean_text(
            value,
            min(
                string_limit,
                300
            )
        )

    if isinstance(
        value,
        bytes
    ):

        return (
            "<binary data omitted>"
        )

    if isinstance(
        value,
        dict
    ):

        output: Dict[str, Any] = {}

        count = 0

        for key, child in value.items():

            key_text = clean_text(
                key,
                200
            )

            if not key_text:

                continue

            if (
                key_text.lower()
                in
                DROP_CONTEXT_KEYS
            ):

                continue

            if count >= dict_limit:

                output[
                    "_additional_fields_omitted"
                ] = True

                break

            output[
                key_text
            ] = reduce_prompt_value(
                child,

                depth=
                    depth + 1,

                max_depth=
                    max_depth,

                list_limit=
                    list_limit,

                dict_limit=
                    dict_limit,

                string_limit=
                    string_limit
            )

            count += 1

        return output

    if isinstance(
        value,
        list
    ):

        output = []

        for child in value[
            :list_limit
        ]:

            output.append(
                reduce_prompt_value(
                    child,

                    depth=
                        depth + 1,

                    max_depth=
                        max_depth,

                    list_limit=
                        list_limit,

                    dict_limit=
                        dict_limit,

                    string_limit=
                        string_limit
                )
            )

        if len(
            value
        ) > list_limit:

            output.append(
                (
                    "<"
                    +
                    str(
                        len(
                            value
                        )
                        -
                        list_limit
                    )
                    +
                    " additional items omitted>"
                )
            )

        return output

    if isinstance(
        value,
        (
            int,
            float,
            bool,
        )
    ):

        return value

    if value is None:

        return None

    return clean_text(
        value,
        string_limit
    )


def compact_json(
    value: Any,
    limit: int
) -> str:

    limit = max(
        100,
        int(
            limit
            or
            100
        )
    )

    attempts = [
        {
            "max_depth":
                4,

            "list_limit":
                10,

            "dict_limit":
                50,

            "string_limit":
                1200,
        },

        {
            "max_depth":
                4,

            "list_limit":
                7,

            "dict_limit":
                36,

            "string_limit":
                850,
        },

        {
            "max_depth":
                3,

            "list_limit":
                5,

            "dict_limit":
                28,

            "string_limit":
                600,
        },

        {
            "max_depth":
                3,

            "list_limit":
                3,

            "dict_limit":
                20,

            "string_limit":
                400,
        },

        {
            "max_depth":
                2,

            "list_limit":
                2,

            "dict_limit":
                14,

            "string_limit":
                250,
        },
    ]

    for settings in attempts:

        reduced = reduce_prompt_value(
            value,
            **settings
        )

        try:

            encoded = json.dumps(
                reduced,
                ensure_ascii=False,
                separators=(
                    ",",
                    ":"
                ),
                default=str
            )

        except Exception:

            encoded = clean_text(
                reduced,
                limit
            )

        if len(
            encoded
        ) <= limit:

            return encoded

    fallback = {
        "compacted":
            True,

        "summary":
            clean_text(
                value,
                max(
                    100,
                    int(
                        limit
                        *
                        0.60
                    )
                )
            ),
    }

    encoded = json.dumps(
        fallback,
        ensure_ascii=False,
        separators=(
            ",",
            ":"
        ),
        default=str
    )

    if len(
        encoded
    ) <= limit:

        return encoded

    return json.dumps(
        {
            "compacted":
                True
        },
        ensure_ascii=False
    )


def safe_json(
    value: Any,
    limit: int = 30000
) -> str:

    return compact_json(
        value,
        limit
    )


# =========================================================
# PROMPT SAFETY
# =========================================================

def hard_fit_prompt(
    prompt: str,
    budget: int
) -> str:

    prompt = clean_text(
        prompt,
        1000000
    )

    if len(
        prompt
    ) <= budget:

        return prompt

    marker = (
        "\n\n"
        "[XPAND CAMPAIGN CONTEXT COMPACTED]\n"
        "Secondary context omitted to remain within "
        "the provider prompt budget.\n\n"
    )

    available = max(
        500,
        budget
        -
        len(
            marker
        )
    )

    front = int(
        available
        *
        0.68
    )

    back = (
        available
        -
        front
    )

    return (
        prompt[
            :front
        ]
        +
        marker
        +
        prompt[
            -back:
        ]
    )


def fit_prompt_for_api(
    prompt: str,
    *,
    label: str,
    budget: int
) -> str:

    original = clean_text(
        prompt,
        1000000
    )

    original_length = len(
        original
    )

    fitted = hard_fit_prompt(
        original,
        budget
    )

    final_length = len(
        fitted
    )

    if original_length <= budget:

        print(
            (
                "🧮 Campaign prompt ["
                +
                label
                +
                "]: "
                +
                str(
                    final_length
                )
                +
                "/"
                +
                str(
                    budget
                )
                +
                " chars ✅"
            )
        )

    else:

        print(
            (
                "🧮 Campaign prompt ["
                +
                label
                +
                "]: "
                +
                str(
                    original_length
                )
                +
                " → "
                +
                str(
                    final_length
                )
                +
                "/"
                +
                str(
                    budget
                )
                +
                " chars ✅ COMPACTED"
            )
        )

    return fitted


# =========================================================
# JSON EXTRACTION
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
# CAMPAIGN KEY
# =========================================================

def build_campaign_key(
    brand_id: str,
    campaign_title: str
) -> str:

    brand_id = safe_brand_id(
        brand_id
    )

    title = clean_text(
        campaign_title,
        500
    ).lower()

    raw = (
        brand_id
        +
        "|"
        +
        title
    )

    digest = hashlib.sha256(
        raw.encode(
            "utf-8"
        )
    ).hexdigest()[:12]

    slug = re.sub(
        r"[^a-z0-9]+",
        "-",
        brand_id.lower()
    ).strip(
        "-"
    )

    if not slug:

        slug = (
            "campaign"
        )

    return (
        slug
        +
        "-"
        +
        digest
    )


# =========================================================
# SOURCE CONFIDENCE
# =========================================================

def normalize_source_type(
    value: str
) -> str:

    source_type = clean_text(
        value,
        100
    ).lower()

    if (
        source_type
        in
        SOURCE_CONFIDENCE_LEVELS
    ):

        return source_type

    return (
        "inference"
    )


def score_source(
    source_type: str,
    *,
    recent: bool = False,
    official: bool = False
) -> int:

    source_type = normalize_source_type(
        source_type
    )

    score = int(
        SOURCE_CONFIDENCE_LEVELS.get(
            source_type,
            35
        )
    )

    if official:

        score = max(
            score,
            95
        )

    if recent:

        score = min(
            100,
            score + 5
        )

    return score


def build_source_confidence_records(
    sources: Any
) -> List[Dict[str, Any]]:

    if not isinstance(
        sources,
        list
    ):

        return []

    output: List[
        Dict[str, Any]
    ] = []

    for source in sources:

        if isinstance(
            source,
            str
        ):

            output.append(
                {
                    "source":
                        clean_text(
                            source,
                            1000
                        ),

                    "source_type":
                        "search_snippet",

                    "confidence":
                        score_source(
                            "search_snippet"
                        ),

                    "official":
                        False,

                    "recent":
                        False,
                }
            )

            continue

        if not isinstance(
            source,
            dict
        ):

            continue

        source_type = normalize_source_type(
            source.get(
                "source_type",
                "inference"
            )
        )

        official = bool(
            source.get(
                "official",
                False
            )
        )

        recent = bool(
            source.get(
                "recent",
                False
            )
        )

        output.append(
            {
                "source":
                    clean_text(
                        (
                            source.get(
                                "url"
                            )
                            or
                            source.get(
                                "source"
                            )
                            or
                            source.get(
                                "title"
                            )
                            or
                            ""
                        ),
                        1000
                    ),

                "source_type":
                    source_type,

                "confidence":
                    score_source(
                        source_type,
                        recent=
                            recent,
                        official=
                            official
                    ),

                "official":
                    official,

                "recent":
                    recent,
            }
        )

    output.sort(
        key=
            lambda item:
                int(
                    item.get(
                        "confidence",
                        0
                    )
                ),
        reverse=
            True
    )

    return output[
        :50
    ]


# =========================================================
# DEFAULT BIBLE
#
# Compatibility fallback only.
#
# In Masterpiece mode the orchestrator should use:
#
# allow_fallback=False
# =========================================================

def build_default_bible(
    *,
    brand_id: str,
    campaign_title: str,
    campaign_goal: str,
    asset_count: int
) -> CampaignBible:

    campaign_key = build_campaign_key(
        brand_id,
        campaign_title
    )

    asset_plan: List[
        Dict[str, Any]
    ] = []

    for index in range(
        asset_count
    ):

        camera = (
            CAMERA_ROTATION_LIBRARY[
                index
                %
                len(
                    CAMERA_ROTATION_LIBRARY
                )
            ]
        )

        asset_plan.append(
            {
                "asset_number":
                    index + 1,

                "purpose":
                    (
                        "Campaign asset "
                        +
                        str(
                            index + 1
                        )
                    ),

                "hero_moment":
                    (
                        "Deliver one clear campaign benefit."
                    ),

                "environment":
                    (
                        "Use an environment consistent with "
                        "the campaign visual world."
                    ),

                "camera_angle":
                    camera[
                        "name"
                    ],

                "lens":
                    (
                        "Choose a coherent lens for the shot."
                    ),

                "composition_note":
                    (
                        "Keep stable hierarchy and intentional "
                        "negative space."
                    ),

                "lighting_note":
                    (
                        "Preserve the campaign lighting family."
                    ),

                "metaphor_note":
                    (
                        "Remain inside the approved campaign "
                        "metaphor family."
                    ),

                "what_must_match_campaign": [
                    "visual world",
                    "palette relationships",
                    "lighting language",
                    "material treatment",
                    "realism level",
                    "product identity",
                ],

                "what_may_vary": [
                    "camera angle",
                    "environment",
                    "hero moment",
                    "foreground relationship",
                ],
            }
        )

    return CampaignBible(
        campaign_key=
            campaign_key,

        brand_id=
            safe_brand_id(
                brand_id
            ),

        title=
            clean_text(
                campaign_title,
                500
            ),

        campaign_goal=
            clean_text(
                campaign_goal,
                3000
            ),

        asset_count=
            asset_count,

        visual_world={
            "core_description":
                (
                    "One coherent premium campaign world "
                    "across all assets."
                ),

            "realism_level":
                "premium photorealistic",

            "mood":
                "controlled and confident",

            "commercial_tone":
                "premium",

            "depth_style":
                "professional layered depth",
        },

        color_system={
            "primary_colors":
                [],

            "secondary_colors":
                [],

            "accent_colors":
                [],

            "background_behavior":
                (
                    "Use one controlled campaign palette."
                ),

            "contrast_behavior":
                (
                    "Keep stable visual contrast."
                ),

            "forbidden_color_drift":
                [
                    "random unrelated color shifts"
                ],
        },

        lighting_system={
            "key_light_family":
                "controlled commercial key light",

            "fill_behavior":
                "natural controlled fill",

            "edge_light_behavior":
                "subtle when useful",

            "shadow_behavior":
                "physically plausible",

            "reflection_behavior":
                "controlled and realistic",

            "temperature_behavior":
                "campaign-consistent",
        },

        material_system={
            "roughness_behavior":
                "material-specific",

            "metal_behavior":
                "realistic",

            "glass_behavior":
                "realistic",

            "plastic_behavior":
                "premium and controlled",

            "fabric_behavior":
                "natural",

            "skin_behavior":
                "realistic",

            "floor_behavior":
                "avoid unnecessary wet mirror reflections",
        },

        camera_system={
            "lens_family":
                [
                    "24mm",
                    "35mm",
                    "50mm",
                    "85mm",
                ],

            "perspective_style":
                "physically coherent",

            "camera_rules":
                [
                    (
                        "Choose camera angle according "
                        "to the message."
                    )
                ],

            "angles_to_avoid_repeating":
                [],
        },

        composition_system={
            "hero_position_logic":
                "clear single visual hierarchy",

            "negative_space_logic":
                "intentional",

            "depth_layers":
                "foreground / midground / background",

            "headline_safe_area":
                "stable campaign-safe zone",

            "cta_safe_area":
                "stable campaign-safe zone",

            "logo_safe_area":
                "stable campaign-safe zone",
        },

        typography_system={
            "headline_behavior":
                "clean and controlled",

            "supporting_copy_behavior":
                "secondary hierarchy",

            "cta_behavior":
                "clear dedicated zone",

            "text_density":
                "low to moderate",

            "image_generation_rule":
                (
                    "Do not invent random text."
                ),
        },

        product_system={
            "identity_lock":
                (
                    "Preserve product identity when reference exists."
                ),

            "geometry_lock":
                "preserve proportions",

            "material_lock":
                "preserve product materials",

            "allowed_environment_change":
                "yes",

            "allowed_lighting_change":
                "yes, naturally",
        },

        character_system={
            "casting_style":
                "campaign appropriate",

            "wardrobe":
                "brand and cultural context appropriate",

            "expression":
                "natural",

            "pose_style":
                "credible commercial photography",

            "cultural_context":
                "brand relevant",
        },

        environment_system={
            "environment_family":
                [],

            "architectural_language":
                "campaign-consistent",

            "background_complexity":
                "controlled",

            "allowed_variation":
                "scene may vary without breaking identity",
        },

        metaphor_system={
            "core_metaphor_family":
                "single coherent campaign metaphor family",

            "allowed_variations":
                [],

            "cliches_to_avoid":
                [
                    "generic banking clichés"
                ],
        },

        consistency_rules=[
            "Keep the same campaign color relationships.",
            "Keep the same realism level.",
            "Keep the same material treatment.",
            "Keep the same product identity.",
            "Keep the same lighting language.",
            "Keep consistent negative-space logic.",
        ],

        variation_rules=[
            "Vary camera angle.",
            (
                "Vary scene while preserving "
                "the visual world."
            ),
            "Vary the hero moment.",
        ],

        forbidden_drift=[
            "Do not change product identity.",
            (
                "Do not change campaign palette randomly."
            ),
            (
                "Do not shift from premium realism "
                "to generic CGI."
            ),
            (
                "Do not repeat the exact same "
                "camera angle."
            ),
        ],

        asset_plan=
            asset_plan,

        research_policy=
            dict(
                FRESHNESS_POLICY
            ),

        source_confidence=[],

        metadata={
            "fallback":
                True,

            "model_generated":
                False,

            "quality_status":
                "fallback",

            "engine_version":
                VERSION,
        },
    )


# =========================================================
# CORE BIBLE REQUIRED FIELDS
# =========================================================

CORE_DICT_FIELDS = [
    "visual_world",
    "color_system",
    "lighting_system",
    "material_system",
    "camera_system",
    "composition_system",
    "typography_system",
    "product_system",
    "character_system",
    "environment_system",
    "metaphor_system",
]


CORE_LIST_FIELDS = [
    "consistency_rules",
    "variation_rules",
    "forbidden_drift",
]


# =========================================================
# CORE CAMPAIGN BIBLE PROMPT
# =========================================================

def build_campaign_bible_core_prompt(
    *,
    brand_id: str,
    campaign_title: str,
    campaign_goal: str,
    asset_count: int,
    brand_context: Any,
    visual_references: Any,
    research_summary: str,
    research_sources: Any,
    approved_creative_direction: Any
) -> str:

    prompt = f"""
You are XPAND Campaign Visual Director.

Create the CORE Campaign Visual Bible.

Do NOT generate images.

Do NOT generate the individual asset plan yet.

Do NOT expose chain-of-thought.

This Bible must be concise, practical and directly usable
by an image-production engine.

==================================================
BRAND
==================================================

{clean_text(brand_id, 300)}

==================================================
CAMPAIGN
==================================================

Title:
{clean_text(campaign_title, 800)}

Goal:
{clean_text(campaign_goal, 3500)}

Planned asset count:
{asset_count}

==================================================
BRAND MEMORY
==================================================

{compact_json(
    brand_context,
    5200
)}

==================================================
VISUAL REFERENCE DNA
==================================================

{compact_json(
    visual_references,
    4200
)}

==================================================
APPROVED CREATIVE DIRECTION
==================================================

{compact_json(
    approved_creative_direction,
    5200
)}

==================================================
RECENT RESEARCH
==================================================

{clean_text(
    research_summary,
    4200
)}

==================================================
SOURCE CONFIDENCE
==================================================

{compact_json(
    research_sources,
    2800
)}

==================================================
SOURCE POLICY
==================================================

Use official sources as brand truth.

Give recent official campaign evidence from the last
6–12 months priority when available.

Pinterest, Behance, Dribbble, Midjourney galleries,
competitor campaigns and creative references may inspire
creative thinking but must NOT be treated as official
brand identity rules.

==================================================
CAMPAIGN CONSISTENCY
==================================================

The campaign must preserve:

- one visual universe
- stable color relationships
- stable lighting language
- stable realism level
- stable material response
- stable product treatment
- stable negative-space logic
- stable typography safe zones
- stable cultural styling
- stable commercial finish

Variation is allowed through:

- camera
- environment
- framing
- scale
- human interaction
- foreground relationships
- hero moment
- visual metaphor execution

==================================================
OUTPUT COMPRESSION RULES
==================================================

Be concise.

Each string should normally remain below 180 characters.

Keep arrays focused.

Do not repeat the same rule in multiple sections.

Do not include explanations outside the JSON.

==================================================
OUTPUT
==================================================

Return JSON only.

{{
  "visual_world": {{
    "core_description": "",
    "realism_level": "",
    "mood": "",
    "commercial_tone": "",
    "depth_style": ""
  }},

  "color_system": {{
    "primary_colors": [],
    "secondary_colors": [],
    "accent_colors": [],
    "background_behavior": "",
    "contrast_behavior": "",
    "forbidden_color_drift": []
  }},

  "lighting_system": {{
    "key_light_family": "",
    "fill_behavior": "",
    "edge_light_behavior": "",
    "shadow_behavior": "",
    "reflection_behavior": "",
    "temperature_behavior": ""
  }},

  "material_system": {{
    "roughness_behavior": "",
    "metal_behavior": "",
    "glass_behavior": "",
    "plastic_behavior": "",
    "fabric_behavior": "",
    "skin_behavior": "",
    "floor_behavior": ""
  }},

  "camera_system": {{
    "lens_family": [],
    "perspective_style": "",
    "camera_rules": [],
    "angles_to_avoid_repeating": []
  }},

  "composition_system": {{
    "hero_position_logic": "",
    "negative_space_logic": "",
    "depth_layers": "",
    "headline_safe_area": "",
    "cta_safe_area": "",
    "logo_safe_area": ""
  }},

  "typography_system": {{
    "headline_behavior": "",
    "supporting_copy_behavior": "",
    "cta_behavior": "",
    "text_density": "",
    "image_generation_rule": ""
  }},

  "product_system": {{
    "identity_lock": "",
    "geometry_lock": "",
    "material_lock": "",
    "allowed_environment_change": "",
    "allowed_lighting_change": ""
  }},

  "character_system": {{
    "casting_style": "",
    "wardrobe": "",
    "expression": "",
    "pose_style": "",
    "cultural_context": ""
  }},

  "environment_system": {{
    "environment_family": [],
    "architectural_language": "",
    "background_complexity": "",
    "allowed_variation": ""
  }},

  "metaphor_system": {{
    "core_metaphor_family": "",
    "allowed_variations": [],
    "cliches_to_avoid": []
  }},

  "consistency_rules": [],

  "variation_rules": [],

  "forbidden_drift": []
}}
""".strip()

    return fit_prompt_for_api(
        prompt,

        label=
            "campaign_core",

        budget=
            CORE_PROMPT_BUDGET
    )


# =========================================================
# BACKWARDS-COMPATIBLE PROMPT FUNCTION
# =========================================================

def build_campaign_bible_prompt(
    *,
    brand_id: str,
    campaign_title: str,
    campaign_goal: str,
    asset_count: int,
    brand_context: Any,
    visual_references: Any,
    research_summary: str,
    research_sources: Any,
    approved_creative_direction: Any
) -> str:

    return build_campaign_bible_core_prompt(
        brand_id=
            brand_id,

        campaign_title=
            campaign_title,

        campaign_goal=
            campaign_goal,

        asset_count=
            asset_count,

        brand_context=
            brand_context,

        visual_references=
            visual_references,

        research_summary=
            research_summary,

        research_sources=
            research_sources,

        approved_creative_direction=
            approved_creative_direction
    )


# =========================================================
# CORE VALIDATION
# =========================================================

def validate_core_payload(
    payload: Dict[str, Any]
) -> None:

    if not isinstance(
        payload,
        dict
    ):

        raise RuntimeError(
            "Campaign Bible core is not an object."
        )

    missing = []

    for field_name in CORE_DICT_FIELDS:

        if not isinstance(
            payload.get(
                field_name
            ),
            dict
        ):

            missing.append(
                field_name
            )

    for field_name in CORE_LIST_FIELDS:

        if not isinstance(
            payload.get(
                field_name
            ),
            list
        ):

            missing.append(
                field_name
            )

    if missing:

        raise RuntimeError(
            (
                "Campaign Bible core missing required fields: "
                +
                ", ".join(
                    missing
                )
            )
        )


# =========================================================
# CREATE CORE BIBLE
# =========================================================

def generate_campaign_core(
    *,
    brand_id: str,
    campaign_title: str,
    campaign_goal: str,
    asset_count: int,
    brand_context: Any,
    visual_references: Any,
    research_summary: str,
    research_sources: Any,
    approved_creative_direction: Any
) -> Dict[str, Any]:

    prompt = build_campaign_bible_core_prompt(
        brand_id=
            brand_id,

        campaign_title=
            campaign_title,

        campaign_goal=
            campaign_goal,

        asset_count=
            asset_count,

        brand_context=
            brand_context,

        visual_references=
            visual_references,

        research_summary=
            research_summary,

        research_sources=
            research_sources,

        approved_creative_direction=
            approved_creative_direction
    )

    raw = call_openai_director(
        prompt,

        json_mode=
            True
    )

    payload = extract_json_object(
        raw
    )

    if not payload:

        raise RuntimeError(
            (
                "Campaign Bible core returned "
                "invalid JSON."
            )
        )

    validate_core_payload(
        payload
    )

    return payload


# =========================================================
# ASSET PLAN PROMPT
# =========================================================

def build_asset_plan_prompt(
    *,
    brand_id: str,
    campaign_title: str,
    campaign_goal: str,
    asset_start: int,
    asset_end: int,
    total_asset_count: int,
    core_bible: Dict[str, Any],
    approved_creative_direction: Any,
    existing_asset_plan: Sequence[
        Dict[str, Any]
    ]
) -> str:

    previous_cameras = []

    previous_hero_moments = []

    for item in existing_asset_plan:

        if not isinstance(
            item,
            dict
        ):

            continue

        camera = clean_text(
            item.get(
                "camera_angle",
                ""
            ),
            300
        )

        hero = clean_text(
            item.get(
                "hero_moment",
                ""
            ),
            500
        )

        if camera:

            previous_cameras.append(
                camera
            )

        if hero:

            previous_hero_moments.append(
                hero
            )

    required_count = (
        asset_end
        -
        asset_start
        +
        1
    )

    prompt = f"""
You are XPAND Campaign Asset Director.

Create only the requested campaign asset-plan entries.

Do NOT generate images.

Do NOT redesign the approved campaign concept.

Do NOT expose chain-of-thought.

==================================================
BRAND
==================================================

{clean_text(brand_id, 300)}

==================================================
CAMPAIGN
==================================================

Title:
{clean_text(campaign_title, 800)}

Goal:
{clean_text(campaign_goal, 3200)}

Total campaign assets:
{total_asset_count}

Create assets:

{asset_start} through {asset_end}

Required entries:

{required_count}

==================================================
CORE CAMPAIGN VISUAL BIBLE
==================================================

{compact_json(
    core_bible,
    9000
)}

==================================================
APPROVED CREATIVE DIRECTION
==================================================

{compact_json(
    approved_creative_direction,
    4500
)}

==================================================
ALREADY USED CAMERAS
==================================================

{compact_json(
    previous_cameras,
    1800
)}

==================================================
ALREADY USED HERO MOMENTS
==================================================

{compact_json(
    previous_hero_moments,
    2200
)}

==================================================
CAMERA DIVERSITY
==================================================

Use meaningful variation such as:

- Three-Quarter Hero Shot
- Over-the-Shoulder
- Wide Environmental Shot
- Low-Angle Hero Shot
- Bird’s-Eye View
- Macro Product Detail
- Forced Perspective
- Ground-Level Shot
- Central One-Point Perspective
- Frame-within-a-Frame

Do not vary camera randomly.

Each camera must strengthen that asset's message.

Do not repeat the exact same hero moment.

==================================================
CONSISTENCY
==================================================

Every asset must visibly belong to the same campaign.

Preserve:

- visual world
- color relationships
- lighting language
- material treatment
- realism level
- product identity
- typography-safe logic
- commercial finish

==================================================
OUTPUT COMPRESSION RULE
==================================================

Keep every field concise.

Normally keep each string under 160 characters.

Use short arrays.

Return no prose outside JSON.

==================================================
OUTPUT
==================================================

Return JSON only:

{{
  "assets": [
    {{
      "asset_number": {asset_start},
      "purpose": "",
      "hero_moment": "",
      "environment": "",
      "camera_angle": "",
      "lens": "",
      "composition_note": "",
      "lighting_note": "",
      "metaphor_note": "",
      "what_must_match_campaign": [],
      "what_may_vary": []
    }}
  ]
}}

Return exactly {required_count} asset entries.

Asset numbers must be exactly:

{asset_start} through {asset_end}
""".strip()

    return fit_prompt_for_api(
        prompt,

        label=
            (
                "asset_plan_"
                +
                str(
                    asset_start
                )
                +
                "_"
                +
                str(
                    asset_end
                )
            ),

        budget=
            ASSET_PLAN_PROMPT_BUDGET
    )


# =========================================================
# ASSET PLAN NORMALIZATION
# =========================================================

ASSET_REQUIRED_FIELDS = [
    "asset_number",
    "purpose",
    "hero_moment",
    "environment",
    "camera_angle",
    "lens",
    "composition_note",
    "lighting_note",
    "metaphor_note",
    "what_must_match_campaign",
    "what_may_vary",
]


def normalize_asset_entry(
    item: Dict[str, Any],
    expected_number: int
) -> Dict[str, Any]:

    if not isinstance(
        item,
        dict
    ):

        raise RuntimeError(
            "Campaign asset entry is not an object."
        )

    try:

        asset_number = int(
            item.get(
                "asset_number",
                expected_number
            )
        )

    except Exception:

        asset_number = (
            expected_number
        )

    if asset_number != expected_number:

        asset_number = (
            expected_number
        )

    return {
        "asset_number":
            asset_number,

        "purpose":
            clean_text(
                item.get(
                    "purpose",
                    ""
                ),
                700
            ),

        "hero_moment":
            clean_text(
                item.get(
                    "hero_moment",
                    ""
                ),
                800
            ),

        "environment":
            clean_text(
                item.get(
                    "environment",
                    ""
                ),
                800
            ),

        "camera_angle":
            clean_text(
                item.get(
                    "camera_angle",
                    ""
                ),
                400
            ),

        "lens":
            clean_text(
                item.get(
                    "lens",
                    ""
                ),
                300
            ),

        "composition_note":
            clean_text(
                item.get(
                    "composition_note",
                    ""
                ),
                800
            ),

        "lighting_note":
            clean_text(
                item.get(
                    "lighting_note",
                    ""
                ),
                800
            ),

        "metaphor_note":
            clean_text(
                item.get(
                    "metaphor_note",
                    ""
                ),
                800
            ),

        "what_must_match_campaign": [
            clean_text(
                value,
                500
            )
            for value in safe_list(
                item.get(
                    "what_must_match_campaign"
                )
            )[
                :8
            ]
            if clean_text(
                value,
                500
            )
        ],

        "what_may_vary": [
            clean_text(
                value,
                500
            )
            for value in safe_list(
                item.get(
                    "what_may_vary"
                )
            )[
                :8
            ]
            if clean_text(
                value,
                500
            )
        ],
    }


# =========================================================
# GENERATE ONE ASSET BATCH
# =========================================================

def generate_asset_plan_batch(
    *,
    brand_id: str,
    campaign_title: str,
    campaign_goal: str,
    asset_start: int,
    asset_end: int,
    total_asset_count: int,
    core_bible: Dict[str, Any],
    approved_creative_direction: Any,
    existing_asset_plan: Sequence[
        Dict[str, Any]
    ]
) -> List[Dict[str, Any]]:

    prompt = build_asset_plan_prompt(
        brand_id=
            brand_id,

        campaign_title=
            campaign_title,

        campaign_goal=
            campaign_goal,

        asset_start=
            asset_start,

        asset_end=
            asset_end,

        total_asset_count=
            total_asset_count,

        core_bible=
            core_bible,

        approved_creative_direction=
            approved_creative_direction,

        existing_asset_plan=
            existing_asset_plan
    )

    raw = call_openai_director(
        prompt,

        json_mode=
            True
    )

    payload = extract_json_object(
        raw
    )

    if not payload:

        raise RuntimeError(
            (
                "Campaign asset-plan batch returned "
                "invalid JSON."
            )
        )

    assets = safe_list(
        payload.get(
            "assets"
        )
    )

    expected_count = (
        asset_end
        -
        asset_start
        +
        1
    )

    if len(
        assets
    ) != expected_count:

        raise RuntimeError(
            (
                "Campaign asset-plan batch returned "
                +
                str(
                    len(
                        assets
                    )
                )
                +
                " assets; expected "
                +
                str(
                    expected_count
                )
                +
                "."
            )
        )

    normalized: List[
        Dict[str, Any]
    ] = []

    for offset, item in enumerate(
        assets
    ):

        expected_number = (
            asset_start
            +
            offset
        )

        normalized.append(
            normalize_asset_entry(
                item,
                expected_number
            )
        )

    return normalized


# =========================================================
# GENERATE COMPLETE ASSET PLAN
# =========================================================

def generate_complete_asset_plan(
    *,
    brand_id: str,
    campaign_title: str,
    campaign_goal: str,
    asset_count: int,
    core_bible: Dict[str, Any],
    approved_creative_direction: Any
) -> List[Dict[str, Any]]:

    output: List[
        Dict[str, Any]
    ] = []

    start = 1

    while start <= asset_count:

        end = min(
            asset_count,
            start
            +
            ASSET_PLAN_BATCH_SIZE
            -
            1
        )

        print(
            (
                "🗂️ Campaign asset batch: "
                +
                str(
                    start
                )
                +
                "-"
                +
                str(
                    end
                )
            )
        )

        batch = generate_asset_plan_batch(
            brand_id=
                brand_id,

            campaign_title=
                campaign_title,

            campaign_goal=
                campaign_goal,

            asset_start=
                start,

            asset_end=
                end,

            total_asset_count=
                asset_count,

            core_bible=
                core_bible,

            approved_creative_direction=
                approved_creative_direction,

            existing_asset_plan=
                output
        )

        output.extend(
            batch
        )

        print(
            (
                "✅ Campaign asset batch: "
                +
                str(
                    start
                )
                +
                "-"
                +
                str(
                    end
                )
            )
        )

        start = (
            end + 1
        )

    if len(
        output
    ) != asset_count:

        raise RuntimeError(
            (
                "Final Campaign asset plan count mismatch: "
                +
                str(
                    len(
                        output
                    )
                )
                +
                "/"
                +
                str(
                    asset_count
                )
            )
        )

    return output


# =========================================================
# CORE -> CAMPAIGN BIBLE
# =========================================================

def campaign_bible_from_core(
    *,
    campaign_key: str,
    brand_id: str,
    campaign_title: str,
    campaign_goal: str,
    asset_count: int,
    core_payload: Dict[str, Any],
    asset_plan: List[Dict[str, Any]],
    source_confidence: List[Dict[str, Any]]
) -> CampaignBible:

    validate_core_payload(
        core_payload
    )

    return CampaignBible(
        campaign_key=
            campaign_key,

        brand_id=
            brand_id,

        title=
            clean_text(
                campaign_title,
                500
            ),

        campaign_goal=
            clean_text(
                campaign_goal,
                5000
            ),

        asset_count=
            asset_count,

        visual_world=
            safe_dict(
                core_payload.get(
                    "visual_world"
                )
            ),

        color_system=
            safe_dict(
                core_payload.get(
                    "color_system"
                )
            ),

        lighting_system=
            safe_dict(
                core_payload.get(
                    "lighting_system"
                )
            ),

        material_system=
            safe_dict(
                core_payload.get(
                    "material_system"
                )
            ),

        camera_system=
            safe_dict(
                core_payload.get(
                    "camera_system"
                )
            ),

        composition_system=
            safe_dict(
                core_payload.get(
                    "composition_system"
                )
            ),

        typography_system=
            safe_dict(
                core_payload.get(
                    "typography_system"
                )
            ),

        product_system=
            safe_dict(
                core_payload.get(
                    "product_system"
                )
            ),

        character_system=
            safe_dict(
                core_payload.get(
                    "character_system"
                )
            ),

        environment_system=
            safe_dict(
                core_payload.get(
                    "environment_system"
                )
            ),

        metaphor_system=
            safe_dict(
                core_payload.get(
                    "metaphor_system"
                )
            ),

        consistency_rules=[
            clean_text(
                item,
                1200
            )
            for item in safe_list(
                core_payload.get(
                    "consistency_rules"
                )
            )[
                :20
            ]
            if clean_text(
                item,
                1200
            )
        ],

        variation_rules=[
            clean_text(
                item,
                1200
            )
            for item in safe_list(
                core_payload.get(
                    "variation_rules"
                )
            )[
                :20
            ]
            if clean_text(
                item,
                1200
            )
        ],

        forbidden_drift=[
            clean_text(
                item,
                1200
            )
            for item in safe_list(
                core_payload.get(
                    "forbidden_drift"
                )
            )[
                :20
            ]
            if clean_text(
                item,
                1200
            )
        ],

        asset_plan=
            asset_plan,

        research_policy=
            dict(
                FRESHNESS_POLICY
            ),

        source_confidence=
            source_confidence,

        metadata={
            "engine_version":
                VERSION,

            "fallback":
                False,

            "model_generated":
                True,

            "quality_status":
                "validated",

            "generation_strategy":
                (
                    "core_plus_batched_asset_plan"
                ),

            "asset_plan_batch_size":
                ASSET_PLAN_BATCH_SIZE,
        },
    )


# =========================================================
# CREATE BIBLE
# =========================================================

def create_campaign_bible(
    *,
    core,
    user_id,
    brand_id: str,
    campaign_title: str,
    campaign_goal: str,
    asset_count: int = DEFAULT_CAMPAIGN_ASSET_COUNT,
    brand_context: Any = None,
    visual_references: Any = None,
    research_summary: str = "",
    research_sources: Any = None,
    approved_creative_direction: Any = None,
    allow_fallback: bool = True
) -> CampaignBible:

    brand_id = safe_brand_id(
        brand_id
    )

    asset_count = max(
        1,
        min(
            30,
            int(
                asset_count
                or
                DEFAULT_CAMPAIGN_ASSET_COUNT
            )
        )
    )

    if not brand_id:

        raise ValueError(
            "brand_id is required."
        )

    if not clean_text(
        campaign_title,
        500
    ):

        raise ValueError(
            "campaign_title is required."
        )

    campaign_key = build_campaign_key(
        brand_id,
        campaign_title
    )

    source_confidence = (
        build_source_confidence_records(
            research_sources
        )
    )

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND CAMPAIGN CONSISTENCY ENGINE V1.1"
    )
    print(
        "=========================================="
    )
    print(
        "Brand:",
        brand_id
    )
    print(
        "Assets:",
        asset_count
    )
    print(
        "Fallback allowed:",
        allow_fallback
    )
    print("")

    try:

        # =================================================
        # STAGE 1
        # CORE VISUAL BIBLE
        # =================================================

        print(
            "📘 STAGE 1: Campaign Core Bible..."
        )

        core_payload = (
            generate_campaign_core(
                brand_id=
                    brand_id,

                campaign_title=
                    campaign_title,

                campaign_goal=
                    campaign_goal,

                asset_count=
                    asset_count,

                brand_context=
                    brand_context
                    or
                    {},

                visual_references=
                    visual_references
                    or
                    [],

                research_summary=
                    research_summary,

                research_sources=
                    source_confidence,

                approved_creative_direction=
                    approved_creative_direction
                    or
                    {}
            )
        )

        print(
            "✅ STAGE 1: Campaign Core Bible"
        )

        # =================================================
        # STAGE 2
        # BATCHED ASSET PLAN
        # =================================================

        print(
            "🗂️ STAGE 2: Campaign Asset Plan..."
        )

        asset_plan = (
            generate_complete_asset_plan(
                brand_id=
                    brand_id,

                campaign_title=
                    campaign_title,

                campaign_goal=
                    campaign_goal,

                asset_count=
                    asset_count,

                core_bible=
                    core_payload,

                approved_creative_direction=
                    approved_creative_direction
                    or
                    {}
            )
        )

        print(
            "✅ STAGE 2: Campaign Asset Plan"
        )

        bible = campaign_bible_from_core(
            campaign_key=
                campaign_key,

            brand_id=
                brand_id,

            campaign_title=
                campaign_title,

            campaign_goal=
                campaign_goal,

            asset_count=
                asset_count,

            core_payload=
                core_payload,

            asset_plan=
                asset_plan,

            source_confidence=
                source_confidence
        )

        print(
            "✅ CAMPAIGN BIBLE VALIDATED"
        )

    except Exception as error:

        error_text = clean_text(
            error,
            3000
        )

        print(
            (
                "❌ Campaign Bible generation failed: "
                +
                error_text
            )
        )

        # =================================================
        # STRICT MODE
        # =================================================

        if not allow_fallback:

            print(
                "🛑 Campaign fallback BLOCKED"
            )

            raise RuntimeError(
                (
                    "Campaign Bible quality gate failed. "
                    "No fallback Bible was accepted. "
                    +
                    error_text
                )
            ) from error

        # =================================================
        # COMPATIBILITY FALLBACK
        # =================================================

        print(
            "⚠️ Using clearly-marked deterministic fallback."
        )

        bible = build_default_bible(
            brand_id=
                brand_id,

            campaign_title=
                campaign_title,

            campaign_goal=
                campaign_goal,

            asset_count=
                asset_count
        )

        bible.source_confidence = (
            source_confidence
        )

        bible.metadata[
            "creation_error"
        ] = (
            error_text
        )

        bible.metadata[
            "fallback_reason"
        ] = (
            "model_generation_failed"
        )

        bible.metadata[
            "fallback"
        ] = True

        bible.metadata[
            "model_generated"
        ] = False

        bible.metadata[
            "quality_status"
        ] = "fallback"

    # =====================================================
    # SAVE ONLY WHAT WE ACTUALLY HAVE
    # =====================================================

    save_campaign_bible(
        core,
        user_id,
        brand_id,
        campaign_key,
        clean_text(
            campaign_title,
            500
        ),
        campaign_bible_to_dict(
            bible
        )
    )

    print(
        (
            "✅ CAMPAIGN BIBLE SAVED"
            +
            " | key="
            +
            campaign_key
            +
            " | fallback="
            +
            str(
                bool(
                    bible.metadata.get(
                        "fallback",
                        False
                    )
                )
            )
        )
    )

    print("")

    return bible


# =========================================================
# LOAD EXISTING BIBLE
# =========================================================

def get_campaign_bible(
    *,
    core,
    user_id,
    brand_id: str,
    campaign_key: str = ""
) -> Dict[str, Any]:

    return load_campaign_bible(
        core,
        user_id,
        safe_brand_id(
            brand_id
        ),
        campaign_key=
            clean_text(
                campaign_key,
                200
            )
    )


# =========================================================
# ASSET-SPECIFIC CONTEXT
# =========================================================

def get_asset_direction(
    bible: CampaignBible,
    asset_number: int
) -> Dict[str, Any]:

    asset_number = max(
        1,
        int(
            asset_number
            or
            1
        )
    )

    selected = {}

    for item in bible.asset_plan:

        if not isinstance(
            item,
            dict
        ):

            continue

        try:

            current = int(
                item.get(
                    "asset_number",
                    0
                )
            )

        except Exception:

            current = 0

        if current == asset_number:

            selected = item
            break

    if not selected:

        index = (
            asset_number - 1
        )

        if (
            0
            <=
            index
            <
            len(
                bible.asset_plan
            )
        ):

            selected = (
                bible.asset_plan[
                    index
                ]
            )

    return {
        "campaign_key":
            bible.campaign_key,

        "campaign_title":
            bible.title,

        "asset_number":
            asset_number,

        "asset_direction":
            selected,

        "visual_world":
            bible.visual_world,

        "color_system":
            bible.color_system,

        "lighting_system":
            bible.lighting_system,

        "material_system":
            bible.material_system,

        "camera_system":
            bible.camera_system,

        "composition_system":
            bible.composition_system,

        "typography_system":
            bible.typography_system,

        "product_system":
            bible.product_system,

        "character_system":
            bible.character_system,

        "environment_system":
            bible.environment_system,

        "metaphor_system":
            bible.metaphor_system,

        "consistency_rules":
            bible.consistency_rules,

        "variation_rules":
            bible.variation_rules,

        "forbidden_drift":
            bible.forbidden_drift,

        "campaign_metadata": {
            "fallback":
                bool(
                    bible.metadata.get(
                        "fallback",
                        False
                    )
                ),

            "quality_status":
                bible.metadata.get(
                    "quality_status",
                    ""
                ),
        },
    }


# =========================================================
# CAMPAIGN CONSISTENCY PROMPT
# =========================================================

def build_campaign_execution_context(
    bible: CampaignBible,
    asset_number: int
) -> str:

    context = get_asset_direction(
        bible,
        asset_number
    )

    compact_context = compact_json(
        context,
        EXECUTION_CONTEXT_BUDGET
        -
        1200
    )

    prompt = (
        "========================================\n"
        "XPAND CAMPAIGN VISUAL BIBLE\n"
        "========================================\n"
        +
        compact_context
        +
        "\n\n"
        "CAMPAIGN EXECUTION RULE:\n"
        "The new image may vary according to the "
        "asset-specific direction, but it must visibly "
        "belong to the same campaign.\n"
        "Preserve the defined visual world, palette, "
        "lighting language, material treatment, realism "
        "level, product identity and composition system.\n"
        "Do not copy another asset composition exactly.\n"
        "Do not introduce visual drift."
    )

    return fit_prompt_for_api(
        prompt,

        label=
            (
                "campaign_execution_asset_"
                +
                str(
                    asset_number
                )
            ),

        budget=
            EXECUTION_CONTEXT_BUDGET
    )


# =========================================================
# SERIALIZER
# =========================================================

def campaign_bible_to_dict(
    bible: CampaignBible
) -> Dict[str, Any]:

    return {
        "campaign_key":
            bible.campaign_key,

        "brand_id":
            bible.brand_id,

        "title":
            bible.title,

        "campaign_goal":
            bible.campaign_goal,

        "asset_count":
            bible.asset_count,

        "visual_world":
            bible.visual_world,

        "color_system":
            bible.color_system,

        "lighting_system":
            bible.lighting_system,

        "material_system":
            bible.material_system,

        "camera_system":
            bible.camera_system,

        "composition_system":
            bible.composition_system,

        "typography_system":
            bible.typography_system,

        "product_system":
            bible.product_system,

        "character_system":
            bible.character_system,

        "environment_system":
            bible.environment_system,

        "metaphor_system":
            bible.metaphor_system,

        "consistency_rules":
            bible.consistency_rules,

        "variation_rules":
            bible.variation_rules,

        "forbidden_drift":
            bible.forbidden_drift,

        "asset_plan":
            bible.asset_plan,

        "research_policy":
            bible.research_policy,

        "source_confidence":
            bible.source_confidence,

        "metadata":
            bible.metadata,
    }


# =========================================================
# SELF TEST
#
# NO DATABASE
# NO API
# NO PAID USAGE
# =========================================================

if __name__ == "__main__":

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND CAMPAIGN CONSISTENCY ENGINE V1.1"
    )
    print(
        "=========================================="
    )
    print("")

    print(
        "Recent research priority:",
        (
            str(
                FRESHNESS_POLICY[
                    "strong_recent_window_months"
                ]
            )
            +
            "–"
            +
            str(
                FRESHNESS_POLICY[
                    "preferred_recent_window_months"
                ]
            )
            +
            " months"
        )
    )

    print("")

    print(
        "Core prompt budget:",
        CORE_PROMPT_BUDGET
    )

    print(
        "Asset-plan prompt budget:",
        ASSET_PLAN_PROMPT_BUDGET
    )

    print(
        "Asset batch size:",
        ASSET_PLAN_BATCH_SIZE
    )

    print(
        "Execution context budget:",
        EXECUTION_CONTEXT_BUDGET
    )

    print("")

    # =====================================================
    # SOURCE CONFIDENCE
    # =====================================================

    print(
        "Source confidence:"
    )

    for key, value in (
        SOURCE_CONFIDENCE_LEVELS.items()
    ):

        print(
            " -",
            key,
            "=",
            value
        )

    print("")

    test_key_1 = build_campaign_key(
        "stc_bank",
        "Travel Without Fees"
    )

    test_key_2 = build_campaign_key(
        "stc_bank",
        "Travel Without Fees"
    )

    print(
        "Campaign key deterministic:",
        (
            test_key_1
            ==
            test_key_2
        )
    )

    print(
        "Campaign key:",
        test_key_1
    )

    print("")

    # =====================================================
    # DEFAULT BIBLE
    # =====================================================

    default_bible = build_default_bible(
        brand_id=
            "stc_bank",

        campaign_title=
            "Travel Without Fees",

        campaign_goal=
            "Promote international card usage.",

        asset_count=
            5
    )

    print(
        "Default asset count:",
        len(
            default_bible.asset_plan
        )
    )

    print(
        "Default fallback flag:",
        default_bible.metadata.get(
            "fallback"
        )
    )

    print(
        "Default model generated:",
        default_bible.metadata.get(
            "model_generated"
        )
    )

    print("")

    # =====================================================
    # CAMERA ROTATION
    # =====================================================

    print(
        "Camera rotation:"
    )

    for item in default_bible.asset_plan:

        print(
            (
                " - Asset "
                +
                str(
                    item[
                        "asset_number"
                    ]
                )
                +
                ": "
                +
                item[
                    "camera_angle"
                ]
            )
        )

    print("")

    # =====================================================
    # SOURCE TEST
    # =====================================================

    test_sources = [
        {
            "url":
                "https://example.com/official",

            "source_type":
                "official_campaign_source",

            "official":
                True,

            "recent":
                True,
        },

        {
            "url":
                "https://example.com/pinterest",

            "source_type":
                "creative_reference",

            "official":
                False,

            "recent":
                True,
        },
    ]

    records = build_source_confidence_records(
        test_sources
    )

    print(
        "Source confidence test:"
    )

    for item in records:

        print(
            " -",
            item[
                "source_type"
            ],
            "=",
            item[
                "confidence"
            ]
        )

    print("")

    # =====================================================
    # EXTREME CONTEXT TEST
    # =====================================================

    giant_text = (
        "STC Bank research visual reference campaign "
        "creative direction photography lighting material "
        "marketing advertising "
        *
        1500
    )

    giant_brand = {
        "brand":
            "STC Bank",

        "research":
            [
                giant_text
                for _ in range(
                    20
                )
            ],

        "visual_rules":
            {
                "lighting":
                    giant_text,

                "camera":
                    giant_text,

                "materials":
                    giant_text,
            },
    }

    giant_references = [
        {
            "role":
                "style_reference",

            "dna": {
                "camera":
                    giant_text,

                "lighting":
                    giant_text,

                "materials":
                    giant_text,

                "composition":
                    giant_text,
            },
        }
        for _ in range(
            12
        )
    ]

    giant_creative = {
        "title":
            "Masterpiece",

        "core_idea":
            giant_text,

        "visual_metaphor":
            giant_text,

        "camera":
            giant_text,
    }

    giant_sources = [
        {
            "source":
                giant_text,

            "source_type":
                "creative_reference",

            "confidence":
                60,
        }
        for _ in range(
            30
        )
    ]

    core_prompt = (
        build_campaign_bible_core_prompt(
            brand_id=
                "stc_bank",

            campaign_title=
                "Travel Without Fees",

            campaign_goal=
                giant_text,

            asset_count=
                5,

            brand_context=
                giant_brand,

            visual_references=
                giant_references,

            research_summary=
                giant_text,

            research_sources=
                giant_sources,

            approved_creative_direction=
                giant_creative
        )
    )

    core_ok = (
        len(
            core_prompt
        )
        <=
        CORE_PROMPT_BUDGET
    )

    print(
        "Extreme core prompt chars:",
        len(
            core_prompt
        ),
        "/",
        CORE_PROMPT_BUDGET
    )

    print(
        "Extreme core prompt test:",
        (
            "PASS ✅"
            if core_ok
            else
            "FAIL ❌"
        )
    )

    print("")

    # =====================================================
    # ASSET PLAN PROMPT TEST
    # =====================================================

    sample_core = {
        "visual_world": {
            "core_description":
                giant_text
        },

        "color_system": {
            "primary_colors":
                [
                    "purple",
                    "mint"
                ]
        },

        "lighting_system": {
            "key_light_family":
                giant_text
        },

        "material_system": {
            "roughness_behavior":
                giant_text
        },

        "camera_system": {
            "lens_family":
                [
                    "24mm",
                    "35mm",
                    "50mm"
                ]
        },

        "composition_system": {
            "negative_space_logic":
                giant_text
        },

        "typography_system": {
            "headline_behavior":
                giant_text
        },

        "product_system": {
            "identity_lock":
                giant_text
        },

        "character_system": {
            "casting_style":
                giant_text
        },

        "environment_system": {
            "environment_family":
                [
                    giant_text
                ]
        },

        "metaphor_system": {
            "core_metaphor_family":
                giant_text
        },

        "consistency_rules": [
            giant_text
        ],

        "variation_rules": [
            giant_text
        ],

        "forbidden_drift": [
            giant_text
        ],
    }

    asset_prompt = build_asset_plan_prompt(
        brand_id=
            "stc_bank",

        campaign_title=
            "Travel Without Fees",

        campaign_goal=
            giant_text,

        asset_start=
            1,

        asset_end=
            5,

        total_asset_count=
            5,

        core_bible=
            sample_core,

        approved_creative_direction=
            giant_creative,

        existing_asset_plan=[]
    )

    asset_ok = (
        len(
            asset_prompt
        )
        <=
        ASSET_PLAN_PROMPT_BUDGET
    )

    print(
        "Extreme asset-plan prompt chars:",
        len(
            asset_prompt
        ),
        "/",
        ASSET_PLAN_PROMPT_BUDGET
    )

    print(
        "Extreme asset-plan prompt test:",
        (
            "PASS ✅"
            if asset_ok
            else
            "FAIL ❌"
        )
    )

    print("")

    # =====================================================
    # CORE VALIDATION TEST
    # =====================================================

    validation_payload = {
        "visual_world":
            {},

        "color_system":
            {},

        "lighting_system":
            {},

        "material_system":
            {},

        "camera_system":
            {},

        "composition_system":
            {},

        "typography_system":
            {},

        "product_system":
            {},

        "character_system":
            {},

        "environment_system":
            {},

        "metaphor_system":
            {},

        "consistency_rules":
            [],

        "variation_rules":
            [],

        "forbidden_drift":
            [],
    }

    validation_ok = True

    try:

        validate_core_payload(
            validation_payload
        )

    except Exception:

        validation_ok = False

    print(
        "Core schema validation:",
        (
            "PASS ✅"
            if validation_ok
            else
            "FAIL ❌"
        )
    )

    print("")

    # =====================================================
    # COMPACTION TEST
    # =====================================================

    compacted = compact_json(
        giant_brand,
        5000
    )

    compact_ok = (
        len(
            compacted
        )
        <=
        5000
    )

    print(
        "Structured compaction:",
        (
            "PASS ✅"
            if compact_ok
            else
            "FAIL ❌"
        ),
        "|",
        len(
            compacted
        ),
        "/5000"
    )

    print("")

    # =====================================================
    # FEATURE STATUS
    # =====================================================

    print(
        "✅ Campaign Visual Bible"
    )

    print(
        "✅ Core Bible separated from Asset Plan"
    )

    print(
        "✅ Structured JSON mode"
    )

    print(
        "✅ Compact prompt contexts"
    )

    print(
        "✅ Campaign prompt budget protection"
    )

    print(
        "✅ Batched asset-plan generation"
    )

    print(
        "✅ Large campaigns up to 30 assets"
    )

    print(
        "✅ Model output validation"
    )

    print(
        "✅ Multi-asset consistency"
    )

    print(
        "✅ Camera-angle rotation"
    )

    print(
        "✅ Stable palette system"
    )

    print(
        "✅ Stable lighting system"
    )

    print(
        "✅ Stable material system"
    )

    print(
        "✅ Product consistency rules"
    )

    print(
        "✅ Typography safe-area system"
    )

    print(
        "✅ Controlled scene variation"
    )

    print(
        "✅ Forbidden visual drift"
    )

    print(
        "✅ 6–12 month freshness policy"
    )

    print(
        "✅ Research source confidence"
    )

    print(
        "✅ Official sources outrank inspiration sources"
    )

    print(
        "✅ Truthful fallback metadata"
    )

    print(
        "✅ Strict Masterpiece no-fallback mode prepared"
    )

    print("")

    print(
        (
            "Campaign prompt safety self-test: "
            +
            (
                "PASS ✅"
                if (
                    core_ok
                    and
                    asset_ok
                    and
                    validation_ok
                    and
                    compact_ok
                )
                else
                "FAIL ❌"
            )
        )
    )

    print("")

    print(
        "🚫 No API calls were made"
    )

    print("")
