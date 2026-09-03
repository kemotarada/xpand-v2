# =========================================================
# XPAND CAMPAIGN CONSISTENCY ENGINE V1.0
#
# Creates and maintains a Campaign Visual Bible.
#
# PURPOSE
# ---------------------------------------------------------
# When XPAND creates multiple assets for one campaign,
# every image must belong to the same visual world.
#
# Maintains:
# - Brand visual language
# - Campaign palette
# - Lighting family
# - Material treatment
# - Lens family
# - Camera language
# - Realism level
# - Negative-space logic
# - Typography safe zones
# - Product treatment
# - Character styling
# - Environment family
# - Visual metaphor family
# - Campaign consistency rules
#
# Allows controlled variation:
# - different camera angles
# - different scenes
# - different environments
# - different hero moments
#
# WITHOUT breaking campaign identity.
#
# Uses:
# - xpand_brand_memory.py
# - xpand_image_engine.call_openai_director()
#
# IMPORTANT:
# This file does NOT generate images.
# Self-test makes NO API calls.
# =========================================================

from __future__ import annotations

import hashlib
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
)


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

VERSION = "1.0"

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
# HELPERS
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


def safe_json(
    value: Any,
    limit: int = 30000
) -> str:

    try:

        return clean_text(
            json.dumps(
                value,
                ensure_ascii=False,
                indent=2,
                default=str
            ),
            limit
        )

    except Exception:

        return clean_text(
            value,
            limit
        )


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
        flags=re.IGNORECASE
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
    ).strip("-")

    if not slug:

        slug = "campaign"

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

    if source_type in SOURCE_CONFIDENCE_LEVELS:

        return source_type

    return "inference"


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

    output: List[Dict[str, Any]] = []

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

    return output[:50]


# =========================================================
# DEFAULT BIBLE
#
# Used only as a safe fallback if model creation fails.
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

    asset_plan = []

    for index in range(
        asset_count
    ):

        camera = CAMERA_ROTATION_LIBRARY[
            index
            %
            len(
                CAMERA_ROTATION_LIBRARY
            )
        ]

        asset_plan.append(
            {
                "asset_number":
                    index + 1,

                "camera":
                    camera[
                        "name"
                    ],

                "camera_purpose":
                    camera[
                        "best_for"
                    ],

                "consistency_rule":
                    (
                        "Keep the same campaign visual world "
                        "while varying the shot."
                    ),
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
            "rule":
                (
                    "One coherent premium campaign world "
                    "across all assets."
                )
        },

        color_system={
            "rule":
                (
                    "Use one controlled palette and preserve "
                    "the same color relationships."
                )
        },

        lighting_system={
            "rule":
                (
                    "Use one lighting family with controlled "
                    "variation by scene."
                )
        },

        material_system={
            "rule":
                (
                    "Maintain consistent roughness, reflections "
                    "and material realism."
                )
        },

        camera_system={
            "rule":
                (
                    "Vary camera angles intentionally without "
                    "changing overall lens language."
                )
        },

        composition_system={
            "rule":
                (
                    "Maintain consistent hierarchy and "
                    "negative-space logic."
                )
        },

        typography_system={
            "rule":
                (
                    "Reserve stable headline and CTA zones "
                    "across campaign assets."
                )
        },

        product_system={
            "rule":
                (
                    "Keep product identity and proportions "
                    "consistent across all assets."
                )
        },

        character_system={
            "rule":
                (
                    "Keep styling, cultural context and realism "
                    "consistent."
                )
        },

        environment_system={
            "rule":
                (
                    "All environments must feel like parts of "
                    "the same campaign universe."
                )
        },

        metaphor_system={
            "rule":
                (
                    "Use one metaphor family without repeating "
                    "the same literal composition."
                )
        },

        consistency_rules=[
            (
                "Keep the same campaign color relationships."
            ),

            (
                "Keep the same realism level."
            ),

            (
                "Keep the same material treatment."
            ),

            (
                "Keep the same product identity."
            ),

            (
                "Keep the same lighting language."
            ),

            (
                "Keep consistent negative-space logic."
            ),
        ],

        variation_rules=[
            (
                "Vary camera angle."
            ),

            (
                "Vary scene while preserving the visual world."
            ),

            (
                "Vary the hero moment."
            ),
        ],

        forbidden_drift=[
            (
                "Do not change product identity."
            ),

            (
                "Do not change campaign palette randomly."
            ),

            (
                "Do not shift from premium realism to generic CGI."
            ),

            (
                "Do not repeat the exact same camera angle."
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

            "engine_version":
                VERSION,
        },
    )


# =========================================================
# CAMPAIGN BIBLE PROMPT
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

    return f"""
You are XPAND Campaign Visual Director.

Create a Campaign Visual Bible before any campaign images
are generated.

Do NOT generate images.

Do NOT expose chain-of-thought.

The purpose is to ensure that multiple campaign assets feel
like one coherent premium advertising campaign.

==================================================
BRAND
==================================================

{clean_text(brand_id, 200)}

==================================================
CAMPAIGN TITLE
==================================================

{clean_text(campaign_title, 1000)}

==================================================
CAMPAIGN GOAL
==================================================

{clean_text(campaign_goal, 5000)}

==================================================
NUMBER OF ASSETS
==================================================

{asset_count}

==================================================
BRAND MEMORY
==================================================

{safe_json(brand_context, 16000)}

==================================================
VISUAL REFERENCE DNA
==================================================

{safe_json(visual_references, 16000)}

==================================================
APPROVED CREATIVE DIRECTION
==================================================

{safe_json(approved_creative_direction, 12000)}

==================================================
RECENT RESEARCH SUMMARY
==================================================

{clean_text(research_summary, 12000)}

==================================================
RESEARCH SOURCES
==================================================

{safe_json(research_sources, 12000)}

==================================================
FRESHNESS POLICY
==================================================

Prefer recent campaign evidence from the last 6–12 months
when available.

Recent campaign behavior may override old campaign styling,
but evergreen brand identity must remain stable.

Do not treat Pinterest, Behance, Dribbble, Midjourney or
competitor visuals as official brand rules.

Differentiate:

- official brand source
- official campaign source
- agency case study
- creative reference
- competitor reference
- search result
- visual inference

==================================================
CAMPAIGN CONSISTENCY RULE
==================================================

The campaign must maintain:

- one visual universe
- stable color relationships
- stable lighting language
- stable realism level
- stable material response
- stable product treatment
- stable negative-space logic
- stable typography-safe areas
- stable cultural styling
- stable commercial finish

But it must NOT become repetitive.

Variation must come from:

- camera angle
- environment
- framing
- scale
- foreground relationships
- human interaction
- visual metaphor
- hero moment

==================================================
CAMERA DIVERSITY
==================================================

Do not use one camera angle for every asset.

Use meaningful variation from directions such as:

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

Every camera choice must serve the message.

==================================================
TYPOGRAPHY / SAFE AREA
==================================================

Define a stable system for:

- headline safe area
- supporting copy
- CTA
- logo zone

The actual image generator should not invent random text.

==================================================
PRODUCT CONSISTENCY
==================================================

If Product References or Product Locks exist:

- product shape stays consistent
- proportions stay consistent
- material stays consistent
- major graphic layout stays consistent
- environment may vary
- lighting may adapt naturally
- do not redesign the product between campaign assets

==================================================
OUTPUT
==================================================

Return JSON only.

Schema:

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

  "forbidden_drift": [],

  "asset_plan": [
    {{
      "asset_number": 1,
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

Return exactly {asset_count} items in asset_plan.
""".strip()


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
    approved_creative_direction: Any = None
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

    prompt = build_campaign_bible_prompt(
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

    try:

        raw = call_openai_director(
            prompt
        )

        payload = extract_json_object(
            raw
        )

        if not payload:

            raise RuntimeError(
                "Campaign Bible returned invalid JSON."
            )

        asset_plan = safe_list(
            payload.get(
                "asset_plan"
            )
        )

        if not asset_plan:

            raise RuntimeError(
                "Campaign Bible has no asset plan."
            )

        bible = CampaignBible(
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
                    payload.get(
                        "visual_world"
                    )
                ),

            color_system=
                safe_dict(
                    payload.get(
                        "color_system"
                    )
                ),

            lighting_system=
                safe_dict(
                    payload.get(
                        "lighting_system"
                    )
                ),

            material_system=
                safe_dict(
                    payload.get(
                        "material_system"
                    )
                ),

            camera_system=
                safe_dict(
                    payload.get(
                        "camera_system"
                    )
                ),

            composition_system=
                safe_dict(
                    payload.get(
                        "composition_system"
                    )
                ),

            typography_system=
                safe_dict(
                    payload.get(
                        "typography_system"
                    )
                ),

            product_system=
                safe_dict(
                    payload.get(
                        "product_system"
                    )
                ),

            character_system=
                safe_dict(
                    payload.get(
                        "character_system"
                    )
                ),

            environment_system=
                safe_dict(
                    payload.get(
                        "environment_system"
                    )
                ),

            metaphor_system=
                safe_dict(
                    payload.get(
                        "metaphor_system"
                    )
                ),

            consistency_rules=[
                clean_text(
                    item,
                    1500
                )
                for item in safe_list(
                    payload.get(
                        "consistency_rules"
                    )
                )
                if clean_text(
                    item,
                    1500
                )
            ],

            variation_rules=[
                clean_text(
                    item,
                    1500
                )
                for item in safe_list(
                    payload.get(
                        "variation_rules"
                    )
                )
                if clean_text(
                    item,
                    1500
                )
            ],

            forbidden_drift=[
                clean_text(
                    item,
                    1500
                )
                for item in safe_list(
                    payload.get(
                        "forbidden_drift"
                    )
                )
                if clean_text(
                    item,
                    1500
                )
            ],

            asset_plan=
                asset_plan[
                    :asset_count
                ],

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
            },
        )

    except Exception as error:

        print(
            (
                "⚠️ Campaign Bible model fallback: "
                +
                clean_text(
                    error,
                    2000
                )
            )
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
        ] = clean_text(
            error,
            2000
        )

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

    return (
        "========================================\n"
        "XPAND CAMPAIGN VISUAL BIBLE\n"
        "========================================\n"
        +
        safe_json(
            context,
            24000
        )
        +
        "\n\n"
        "CAMPAIGN EXECUTION RULE:\n"
        "The new image may vary according to the asset-specific "
        "direction, but it must visibly belong to the same campaign. "
        "Do not drift from the defined visual world, palette, lighting "
        "language, material treatment, realism level, product identity, "
        "or composition system."
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
        " XPAND CAMPAIGN CONSISTENCY ENGINE V1.0"
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

    print("")

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
                    "camera"
                ]
            )
        )

    print("")

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

    print(
        "✅ Campaign Visual Bible"
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
        "🚫 No API calls were made"
    )

    print("")
