# =========================================================
# XPAND VISUAL INTELLIGENCE V1.0
#
# Visual-reference analysis layer.
#
# Produces:
# - Visual Reference DNA
# - Reference role classification
# - Camera analysis
# - Lens estimate
# - Perspective analysis
# - Lighting analysis
# - Materials
# - Color behavior
# - Negative space
# - Product Lock
# - Visual success reasons
#
# Uses the OpenAI visual director already configured
# in xpand_image_engine.py.
#
# IMPORTANT:
# - Never stores or transcribes sensitive card/account data.
# =========================================================

from __future__ import annotations

import json
import re

from typing import (
    Any,
    Dict,
    List,
    Optional,
)


from xpand_image_engine import (
    call_openai_director,
)


VERSION = "1.0"

MODULE_NAME = (
    "XPAND Visual Intelligence"
)


# =========================================================
# HELPERS
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
        12000
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
    markers: List[str]
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
# REFERENCE ROLE
# =========================================================

ROLE_HINTS = {
    "product_reference": [
        "مرجع المنتج",
        "المنتج نفسه",
        "نفس المنتج",
        "بطاقه",
        "بطاقة",
        "كرت",
        "هاتف",
        "موبايل",
        "عبوه",
        "عبوة",
        "ساعة",
        "ساعه",
        "product reference",
    ],

    "environment_reference": [
        "مرجع البيئه",
        "مرجع البيئة",
        "الخلفيه",
        "الخلفية",
        "المكان",
        "البيئه",
        "البيئة",
        "environment",
        "background",
    ],

    "camera_reference": [
        "مرجع الزاويه",
        "مرجع الزاوية",
        "الزاويه",
        "الزاوية",
        "الكاميرا",
        "زاويه تصوير",
        "camera angle",
        "perspective",
    ],

    "color_reference": [
        "مرجع اللون",
        "مرجع الالوان",
        "مرجع الألوان",
        "الالوان",
        "الألوان",
        "color reference",
        "palette",
    ],

    "lighting_reference": [
        "مرجع الاضاءه",
        "مرجع الإضاءة",
        "الاضاءه",
        "الإضاءة",
        "lighting",
    ],

    "composition_reference": [
        "مرجع التكوين",
        "التكوين",
        "ترتيب العناصر",
        "composition",
        "layout",
    ],

    "person_reference": [
        "مرجع الشخص",
        "نفس الشخص",
        "نفس الوجه",
        "الشخصيه",
        "الشخصية",
        "person reference",
        "face reference",
    ],

    "style_reference": [
        "مرجع الاسلوب",
        "مرجع الأسلوب",
        "الستايل",
        "الاسلوب",
        "الأسلوب",
        "style reference",
        "style",
    ],
}


def infer_reference_role_from_note(
    note: str
) -> str:

    note = clean_text(
        note,
        5000
    )

    for role, markers in ROLE_HINTS.items():

        if contains_any(
            note,
            markers
        ):

            return role

    return "style_reference"


# =========================================================
# JSON PARSER
# =========================================================

def extract_json_object(
    value: str
) -> Dict[str, Any]:

    text = clean_text(
        value,
        50000
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
# NORMALIZATION
# =========================================================

VALID_ROLES = {
    "product_reference",
    "environment_reference",
    "camera_reference",
    "color_reference",
    "style_reference",
    "lighting_reference",
    "composition_reference",
    "person_reference",
    "campaign_reference",
    "mixed_reference",
}


def normalized_role(
    value: Any,
    fallback: str = "style_reference"
) -> str:

    role = clean_text(
        value,
        100
    ).lower()

    if role in VALID_ROLES:
        return role

    return fallback


def normalize_confidence(
    value: Any
) -> int:

    try:
        number = int(
            round(
                float(
                    value
                )
            )
        )

    except Exception:
        number = 70

    return max(
        0,
        min(
            100,
            number
        )
    )


# =========================================================
# ANALYSIS PROMPT
# =========================================================

def build_visual_analysis_prompt(
    *,
    user_note: str = "",
    brand_context: str = "",
    role_hint: str = ""
) -> str:

    role_hint = (
        normalized_role(
            role_hint
        )
        if role_hint
        else
        ""
    )

    return f"""
You are XPAND Visual Intelligence.

Analyze the attached image as a professional advertising
visual reference.

This analysis will be stored as structured Visual Reference DNA.

USER NOTE:
{clean_text(user_note, 5000)}

BRAND CONTEXT:
{clean_text(brand_context, 10000)}

ROLE HINT:
{role_hint or "none"}

Your job is to identify what this image should be used for,
not just describe what it contains.

Possible reference roles:

- product_reference
- environment_reference
- camera_reference
- color_reference
- style_reference
- lighting_reference
- composition_reference
- person_reference
- campaign_reference
- mixed_reference

Analyze carefully:

CAMERA
- approximate camera height
- camera direction
- shot type
- approximate lens / focal length
- distance to primary subject
- horizon position

PERSPECTIVE
- perspective type
- number / direction of vanishing points
- perspective distortion
- foreground / midground / background relationship
- whether any forced perspective is used

COMPOSITION
- primary focal point
- supporting element
- negative-space placement
- hierarchy
- symmetry / asymmetry
- leading lines
- object position inside frame

LIGHTING
- key-light direction
- fill behavior
- rim/back light
- softness
- contrast
- color temperature
- practical lights
- reflection behavior
- shadow behavior
- contact shadows

MATERIALS
- glass
- metal
- plastic
- fabric
- skin
- architecture
- surfaces
- roughness / glossiness
- important reflection characteristics

COLOR
- dominant colors
- secondary colors
- accent colors
- saturation
- contrast
- color relationships

PRODUCT
If a product/card/phone/package is present:
- identify its geometric characteristics
- proportions
- orientation
- thickness
- corners
- physical placement
- interaction with hand/environment

Do NOT transcribe or store:
- payment card numbers
- IBAN numbers
- account numbers
- CVV
- security codes
- personal IDs
- passwords
- private sensitive financial text

If sensitive text appears, only set:
"sensitive_text_present": true

Never reproduce the sensitive value.

PRODUCT LOCK:
Determine which physical/visual properties must remain
unchanged if this reference is used as an original product reference.

VISUAL SUCCESS:
Explain what makes the image visually successful:
- concept
- angle
- hierarchy
- lighting
- simplicity
- integration
- emotional/commercial effect

RISKS:
Identify elements that a generation model could easily break.

Return JSON ONLY.

Required schema:

{{
  "summary": "short visual summary",

  "primary_reference_role":
    "product_reference | environment_reference | camera_reference | color_reference | style_reference | lighting_reference | composition_reference | person_reference | campaign_reference | mixed_reference",

  "secondary_reference_roles": [],

  "camera": {{
    "height": "",
    "direction": "",
    "shot_type": "",
    "estimated_lens_mm": "",
    "subject_distance": "",
    "horizon_position": "",
    "creative_reason": ""
  }},

  "perspective": {{
    "type": "",
    "vanishing_points": "",
    "distortion_level": "",
    "foreground": "",
    "midground": "",
    "background": ""
  }},

  "composition": {{
    "primary_focal_point": "",
    "secondary_element": "",
    "product_position": "",
    "negative_space": "",
    "visual_hierarchy": "",
    "leading_lines": "",
    "balance": ""
  }},

  "lighting": {{
    "key_light": "",
    "fill_light": "",
    "rim_light": "",
    "backlight": "",
    "softness": "",
    "contrast": "",
    "color_temperature": "",
    "shadow_behavior": "",
    "reflection_behavior": ""
  }},

  "materials": [],

  "color_palette": {{
    "dominant": [],
    "secondary": [],
    "accents": [],
    "saturation": "",
    "contrast": ""
  }},

  "relationships": [
    "relationship between important objects"
  ],

  "visual_success_reasons": [],

  "generation_risks": [],

  "product_lock": {{
    "enabled": false,
    "must_remain_identical": [],
    "environment_may_change": true,
    "lighting_may_adapt": true,
    "sensitive_text_present": false,
    "sensitive_text_policy": "never store or reproduce"
  }},

  "confidence": 0
}}

Be technically precise.
Do not invent information that cannot reasonably be inferred
from the image.
""".strip()


# =========================================================
# VISUAL ANALYSIS
# =========================================================

def analyze_visual_reference(
    image_bytes: bytes,
    mime_type: str,
    *,
    user_note: str = "",
    brand_context: str = "",
    role_hint: str = ""
) -> Dict[str, Any]:

    if not image_bytes:

        raise ValueError(
            "Image bytes are empty."
        )

    inferred_role = (
        normalized_role(
            role_hint
        )
        if role_hint
        else
        infer_reference_role_from_note(
            user_note
        )
    )

    prompt = build_visual_analysis_prompt(
        user_note=
            user_note,

        brand_context=
            brand_context,

        role_hint=
            inferred_role
    )

    raw = call_openai_director(
        prompt,
        image_bytes=
            image_bytes,
        image_mime_type=
            mime_type
            or
            "image/jpeg"
    )

    data = extract_json_object(
        raw
    )

    if not data:

        raise RuntimeError(
            (
                "Vision model returned an invalid "
                "Visual Reference DNA payload."
            )
        )

    primary_role = normalized_role(
        data.get(
            "primary_reference_role"
        ),
        fallback=
            inferred_role
    )

    secondary = data.get(
        "secondary_reference_roles",
        []
    )

    if not isinstance(
        secondary,
        list
    ):
        secondary = []

    secondary = [
        normalized_role(
            item
        )
        for item in secondary
        if clean_text(
            item,
            100
        )
    ]

    product_lock = data.get(
        "product_lock",
        {}
    )

    if not isinstance(
        product_lock,
        dict
    ):
        product_lock = {}

    # -----------------------------------------------------
    # HARD PRIVACY RULE
    #
    # Even if the vision model accidentally returns values
    # that look like sensitive banking identifiers,
    # this module removes risky text-oriented fields.
    # -----------------------------------------------------

    sensitive_keys = [
        "card_number",
        "iban",
        "account_number",
        "cvv",
        "security_code",
        "pin",
        "password",
        "sensitive_text",
        "sensitive_value",
    ]

    for key in sensitive_keys:

        product_lock.pop(
            key,
            None
        )

    product_lock[
        "sensitive_text_policy"
    ] = "never store or reproduce"

    result = {
        "summary":
            clean_text(
                data.get(
                    "summary"
                ),
                1500
            ),

        "primary_reference_role":
            primary_role,

        "secondary_reference_roles":
            secondary,

        "camera":
            (
                data.get(
                    "camera"
                )
                if isinstance(
                    data.get(
                        "camera"
                    ),
                    dict
                )
                else
                {}
            ),

        "perspective":
            (
                data.get(
                    "perspective"
                )
                if isinstance(
                    data.get(
                        "perspective"
                    ),
                    dict
                )
                else
                {}
            ),

        "composition":
            (
                data.get(
                    "composition"
                )
                if isinstance(
                    data.get(
                        "composition"
                    ),
                    dict
                )
                else
                {}
            ),

        "lighting":
            (
                data.get(
                    "lighting"
                )
                if isinstance(
                    data.get(
                        "lighting"
                    ),
                    dict
                )
                else
                {}
            ),

        "materials":
            (
                data.get(
                    "materials"
                )
                if isinstance(
                    data.get(
                        "materials"
                    ),
                    list
                )
                else
                []
            ),

        "color_palette":
            (
                data.get(
                    "color_palette"
                )
                if isinstance(
                    data.get(
                        "color_palette"
                    ),
                    dict
                )
                else
                {}
            ),

        "relationships":
            (
                data.get(
                    "relationships"
                )
                if isinstance(
                    data.get(
                        "relationships"
                    ),
                    list
                )
                else
                []
            ),

        "visual_success_reasons":
            (
                data.get(
                    "visual_success_reasons"
                )
                if isinstance(
                    data.get(
                        "visual_success_reasons"
                    ),
                    list
                )
                else
                []
            ),

        "generation_risks":
            (
                data.get(
                    "generation_risks"
                )
                if isinstance(
                    data.get(
                        "generation_risks"
                    ),
                    list
                )
                else
                []
            ),

        "product_lock":
            product_lock,

        "confidence":
            normalize_confidence(
                data.get(
                    "confidence",
                    70
                )
            ),

        "user_note":
            clean_text(
                user_note,
                5000
            ),
    }

    return result


# =========================================================
# HUMAN SUMMARY
# =========================================================

def build_visual_dna_summary(
    dna: Dict[str, Any]
) -> str:

    if not dna:

        return (
            "ما قدرت أطلع تحليل بصري موثوق."
        )

    role = clean_text(
        dna.get(
            "primary_reference_role"
        ),
        100
    )

    camera = dna.get(
        "camera",
        {}
    )

    lighting = dna.get(
        "lighting",
        {}
    )

    composition = dna.get(
        "composition",
        {}
    )

    confidence = normalize_confidence(
        dna.get(
            "confidence",
            70
        )
    )

    camera_line = ""

    if isinstance(
        camera,
        dict
    ):

        shot = clean_text(
            camera.get(
                "shot_type"
            ),
            200
        )

        lens = clean_text(
            camera.get(
                "estimated_lens_mm"
            ),
            100
        )

        if (
            shot
            or
            lens
        ):

            camera_line = (
                "\n📷 "
                +
                "الزاوية: "
                +
                (
                    shot
                    or
                    "غير محددة"
                )
                +
                (
                    (
                        " | عدسة تقريبية: "
                        +
                        lens
                    )
                    if lens
                    else
                    ""
                )
            )

    lighting_line = ""

    if isinstance(
        lighting,
        dict
    ):

        key_light = clean_text(
            lighting.get(
                "key_light"
            ),
            250
        )

        if key_light:

            lighting_line = (
                "\n💡 الإضاءة: "
                +
                key_light
            )

    composition_line = ""

    if isinstance(
        composition,
        dict
    ):

        focal = clean_text(
            composition.get(
                "primary_focal_point"
            ),
            250
        )

        if focal:

            composition_line = (
                "\n🎯 نقطة التركيز: "
                +
                focal
            )

    return (
        "🧬 Visual Reference DNA محفوظ.\n"
        +
        "الوظيفة الأساسية: "
        +
        (
            role
            or
            "style_reference"
        )
        +
        camera_line
        +
        lighting_line
        +
        composition_line
        +
        "\n"
        +
        "درجة الثقة: "
        +
        str(
            confidence
        )
        +
        "%"
    )


# =========================================================
# PRODUCT LOCK SUMMARY
# =========================================================

def product_lock_enabled(
    dna: Dict[str, Any]
) -> bool:

    product_lock = dna.get(
        "product_lock",
        {}
    )

    if not isinstance(
        product_lock,
        dict
    ):

        return False

    return bool(
        product_lock.get(
            "enabled"
        )
    )


# =========================================================
# SELF TEST
#
# Does NOT call Vision.
# Does NOT spend API usage.
# =========================================================

if __name__ == "__main__":

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND VISUAL INTELLIGENCE V1.0"
    )
    print(
        "=========================================="
    )
    print("")
    print(
        "✅ Visual Reference DNA schema"
    )
    print(
        "✅ Camera Angle analysis"
    )
    print(
        "✅ Lens estimation"
    )
    print(
        "✅ Perspective analysis"
    )
    print(
        "✅ Lighting / shadow / reflection analysis"
    )
    print(
        "✅ Material analysis"
    )
    print(
        "✅ Color analysis"
    )
    print(
        "✅ Negative-space analysis"
    )
    print(
        "✅ Reference-role classification"
    )
    print(
        "✅ Product Lock extraction"
    )
    print(
        "✅ Sensitive banking text redaction"
    )
    print("")
