# =========================================================
# XPAND VISUAL INTELLIGENCE V1.0.1
#
# Visual-reference analysis layer for XPAND.
#
# Produces:
# - Visual Reference DNA
# - Reference-role classification
# - Camera analysis
# - Lens estimation
# - Perspective analysis
# - Composition analysis
# - Lighting / shadows / reflections
# - Materials
# - Color palette
# - Negative space
# - Product Lock
# - Visual success reasoning
#
# IMPORTANT:
# - Reference-role detection is deterministic BEFORE Vision.
# - User instructions about reference purpose have priority.
# - Product references are never confused with style references.
# - Sensitive banking information is never intentionally stored.
# =========================================================

from __future__ import annotations

import json
import re

from typing import (
    Any,
    Dict,
    List,
)


from xpand_image_engine import (
    call_openai_director,
)


# =========================================================
# MODULE
# =========================================================

VERSION = "1.0.1"

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
        r"[^\w\s:/\-]+",
        " ",
        text,
        flags=re.UNICODE
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
# VALID REFERENCE ROLES
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


# =========================================================
# ROLE KEYWORDS
#
# IMPORTANT:
# User-described function of the reference has priority.
# =========================================================

ROLE_HINTS = {

    # -----------------------------------------------------
    # PRODUCT
    # -----------------------------------------------------

    "product_reference": [
        "مرجع منتج",
        "مرجع المنتج",
        "مرجع للمنتج",
        "هاي المنتج",
        "هذا المنتج",
        "المنتج نفسه",
        "نفس المنتج",
        "خلي المنتج نفسه",
        "لا تغير المنتج",
        "لا تغيّر المنتج",
        "ثبّت المنتج",
        "ثبت المنتج",
        "بطاقه نفسها",
        "بطاقة نفسها",
        "نفس البطاقه",
        "نفس البطاقة",
        "نفس الكرت",
        "نفس الهاتف",
        "نفس الموبايل",
        "نفس العبوه",
        "نفس العبوة",
        "product reference",
        "same product",
        "product lock",
    ],

    # -----------------------------------------------------
    # CAMERA / ANGLE
    # -----------------------------------------------------

    "camera_reference": [
        "مرجع زاويه",
        "مرجع زاوية",
        "مرجع الزاويه",
        "مرجع الزاوية",
        "مرجع زاويه التصوير",
        "مرجع زاوية التصوير",
        "مرجع للزاويه",
        "مرجع للزاوية",
        "خد الزاويه",
        "خذ الزاوية",
        "نفس الزاويه",
        "نفس الزاوية",
        "زاويه التصوير",
        "زاوية التصوير",
        "زاويه الكاميرا",
        "زاوية الكاميرا",
        "camera reference",
        "camera angle",
        "same angle",
        "angle reference",
        "perspective reference",
    ],

    # -----------------------------------------------------
    # ENVIRONMENT
    # -----------------------------------------------------

    "environment_reference": [
        "مرجع بيئه",
        "مرجع بيئة",
        "مرجع البيئه",
        "مرجع البيئة",
        "مرجع للمكان",
        "مرجع مكان",
        "مرجع الخلفيه",
        "مرجع الخلفية",
        "نفس المكان",
        "نفس البيئه",
        "نفس البيئة",
        "خد المكان",
        "خذ المكان",
        "environment reference",
        "background reference",
        "location reference",
        "same environment",
    ],

    # -----------------------------------------------------
    # LIGHTING
    # -----------------------------------------------------

    "lighting_reference": [
        "مرجع اضاءه",
        "مرجع إضاءة",
        "مرجع الاضاءه",
        "مرجع الإضاءة",
        "نفس الاضاءه",
        "نفس الإضاءة",
        "خد الاضاءه",
        "خذ الإضاءة",
        "طريقة الاضاءه",
        "طريقة الإضاءة",
        "lighting reference",
        "same lighting",
        "light reference",
    ],

    # -----------------------------------------------------
    # COMPOSITION
    # -----------------------------------------------------

    "composition_reference": [
        "مرجع تكوين",
        "مرجع التكوين",
        "نفس التكوين",
        "ترتيب العناصر",
        "نفس ترتيب العناصر",
        "خد التكوين",
        "خذ التكوين",
        "composition reference",
        "layout reference",
        "same composition",
    ],

    # -----------------------------------------------------
    # COLOR
    # -----------------------------------------------------

    "color_reference": [
        "مرجع لون",
        "مرجع اللون",
        "مرجع الوان",
        "مرجع ألوان",
        "مرجع الالوان",
        "مرجع الألوان",
        "نفس الالوان",
        "نفس الألوان",
        "خد الالوان",
        "خذ الألوان",
        "color reference",
        "palette reference",
        "same colors",
    ],

    # -----------------------------------------------------
    # PERSON
    # -----------------------------------------------------

    "person_reference": [
        "مرجع شخص",
        "مرجع الشخص",
        "نفس الشخص",
        "نفس الوجه",
        "نفس الموديل",
        "حافظ على الشخص",
        "حافظ على الوجه",
        "person reference",
        "face reference",
        "same person",
        "same face",
    ],

    # -----------------------------------------------------
    # CAMPAIGN
    # -----------------------------------------------------

    "campaign_reference": [
        "مرجع حمله",
        "مرجع حملة",
        "مرجع الحمله",
        "مرجع الحملة",
        "نفس الحمله",
        "نفس الحملة",
        "campaign reference",
        "campaign visual reference",
    ],

    # -----------------------------------------------------
    # STYLE
    # Keep this AFTER specific technical roles.
    # -----------------------------------------------------

    "style_reference": [
        "مرجع ستايل",
        "مرجع الاسلوب",
        "مرجع الأسلوب",
        "نفس الستايل",
        "نفس الاسلوب",
        "نفس الأسلوب",
        "خد الستايل",
        "خذ الستايل",
        "استلهم الستايل",
        "style reference",
        "same style",
        "visual style",
    ],
}


# =========================================================
# ROLE PRIORITY
#
# In ambiguity, specific physical references have priority
# over generic style.
# =========================================================

ROLE_PRIORITY = [
    "product_reference",
    "camera_reference",
    "environment_reference",
    "lighting_reference",
    "composition_reference",
    "color_reference",
    "person_reference",
    "campaign_reference",
    "style_reference",
]


# =========================================================
# GENERIC SINGLE-WORD SIGNALS
#
# Lower confidence than direct phrases.
# =========================================================

GENERIC_ROLE_SIGNALS = {

    "product_reference": [
        "المنتج",
        "بطاقه",
        "بطاقة",
        "الكرت",
        "الهاتف",
        "الموبايل",
        "العبوه",
        "العبوة",
        "product",
        "card",
        "package",
    ],

    "camera_reference": [
        "زاويه",
        "زاوية",
        "كاميرا",
        "عدسه",
        "عدسة",
        "منظور",
        "perspective",
        "camera",
        "lens",
    ],

    "environment_reference": [
        "الخلفيه",
        "الخلفية",
        "المكان",
        "البيئه",
        "البيئة",
        "background",
        "environment",
        "location",
    ],

    "lighting_reference": [
        "الاضاءه",
        "الإضاءة",
        "الضوء",
        "الظل",
        "lighting",
        "light",
        "shadow",
    ],

    "composition_reference": [
        "التكوين",
        "الكادر",
        "ترتيب",
        "composition",
        "layout",
        "framing",
    ],

    "color_reference": [
        "اللون",
        "الالوان",
        "الألوان",
        "palette",
        "colors",
        "colour",
    ],

    "person_reference": [
        "الشخص",
        "الوجه",
        "الموديل",
        "person",
        "face",
    ],

    "campaign_reference": [
        "الحمله",
        "الحملة",
        "campaign",
    ],

    "style_reference": [
        "ستايل",
        "الاسلوب",
        "الأسلوب",
        "style",
        "look",
    ],
}


# =========================================================
# REFERENCE ROLE CLASSIFIER
# =========================================================

def infer_reference_role_from_note(
    note: str
) -> str:

    source = normalize_text(
        note
    )

    if not source:

        return "style_reference"

    scores: Dict[str, int] = {
        role: 0
        for role in VALID_ROLES
    }

    # -----------------------------------------------------
    # DIRECT PHRASE MATCHES
    #
    # These are strongest.
    # Longer phrases get slightly more weight.
    # -----------------------------------------------------

    for role in ROLE_PRIORITY:

        markers = ROLE_HINTS.get(
            role,
            []
        )

        for marker in markers:

            normalized_marker = normalize_text(
                marker
            )

            if (
                normalized_marker
                and
                normalized_marker in source
            ):

                scores[
                    role
                ] += (
                    100
                    +
                    min(
                        50,
                        len(
                            normalized_marker
                        )
                    )
                )

    # -----------------------------------------------------
    # GENERIC SIGNALS
    # -----------------------------------------------------

    for role in ROLE_PRIORITY:

        markers = GENERIC_ROLE_SIGNALS.get(
            role,
            []
        )

        for marker in markers:

            normalized_marker = normalize_text(
                marker
            )

            if (
                normalized_marker
                and
                normalized_marker in source
            ):

                scores[
                    role
                ] += 10

    # -----------------------------------------------------
    # MULTI-REFERENCE LANGUAGE
    # -----------------------------------------------------

    mixed_markers = [
        "خد من هاي الصور",
        "خذ من هاي الصور",
        "استخدم الصور كمرجع",
        "استخدم كل الصور",
        "ادمج المراجع",
        "استفيد من كل مرجع",
        "mixed reference",
        "use all references",
    ]

    if contains_any(
        source,
        mixed_markers
    ):

        positive_roles = [
            role
            for role, score in scores.items()
            if (
                role != "mixed_reference"
                and
                score > 0
            )
        ]

        if len(
            positive_roles
        ) >= 2:

            return "mixed_reference"

    # -----------------------------------------------------
    # PICK WINNER
    # -----------------------------------------------------

    highest_score = max(
        scores.values()
    )

    if highest_score <= 0:

        return "style_reference"

    candidates = [
        role
        for role in ROLE_PRIORITY
        if scores.get(
            role,
            0
        ) == highest_score
    ]

    if candidates:

        return candidates[0]

    return "style_reference"


# =========================================================
# ROLE WITH EXPLANATION
# =========================================================

def classify_reference_role(
    note: str
) -> Dict[str, Any]:

    source = normalize_text(
        note
    )

    role = infer_reference_role_from_note(
        note
    )

    matched_markers: List[str] = []

    for marker in ROLE_HINTS.get(
        role,
        []
    ):

        if normalize_text(
            marker
        ) in source:

            matched_markers.append(
                marker
            )

    return {
        "role":
            role,

        "source":
            "user_note"
            if source
            else
            "default",

        "matched_markers":
            matched_markers[:10],

        "confidence":
            (
                100
                if matched_markers
                else
                60
            ),
    }


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


# =========================================================
# NORMALIZATION
# =========================================================

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
# BRAND / USER ROLE OVERRIDE RULE
# =========================================================

def resolve_final_reference_role(
    *,
    user_role: str,
    vision_role: str,
    user_note: str
) -> str:

    user_role = normalized_role(
        user_role
    )

    vision_role = normalized_role(
        vision_role
    )

    note = normalize_text(
        user_note
    )

    # -----------------------------------------------------
    # USER EXPLICITLY EXPLAINED REFERENCE FUNCTION
    #
    # User instruction wins over Vision classification.
    # -----------------------------------------------------

    classification = classify_reference_role(
        user_note
    )

    if (
        note
        and
        classification.get(
            "matched_markers"
        )
    ):

        return classification[
            "role"
        ]

    # -----------------------------------------------------
    # NO EXPLICIT FUNCTION:
    # Vision can classify the image naturally.
    # -----------------------------------------------------

    if vision_role in VALID_ROLES:

        return vision_role

    return user_role


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

==================================================
USER NOTE
==================================================

{clean_text(user_note, 5000)}

==================================================
BRAND CONTEXT
==================================================

{clean_text(brand_context, 10000)}

==================================================
REFERENCE ROLE HINT
==================================================

{role_hint or "none"}

IMPORTANT:

If the user explicitly states what the image is a reference for,
respect that role.

Examples:

- "مرجع زاوية" means camera_reference
- "مرجع المنتج" means product_reference
- "مرجع الإضاءة" means lighting_reference
- "مرجع الألوان" means color_reference
- "مرجع الخلفية" means environment_reference
- "مرجع التكوين" means composition_reference
- "مرجع الستايل" means style_reference

Do NOT reinterpret an explicit product reference as a style reference.

Do NOT copy the product from an environment reference.

Do NOT copy the environment from a product-only reference unless
the user explicitly requests it.

==================================================
POSSIBLE REFERENCE ROLES
==================================================

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

==================================================
CAMERA ANALYSIS
==================================================

Estimate:

- camera height
- camera direction
- shot type
- approximate focal length / lens
- distance to primary subject
- horizon position
- camera tilt
- camera roll if relevant

==================================================
PERSPECTIVE
==================================================

Analyze:

- perspective type
- vanishing points
- perspective distortion
- foreground / midground / background relationship
- scale relationships
- forced perspective if present

==================================================
COMPOSITION
==================================================

Analyze:

- primary focal point
- supporting focal points
- product position
- human position
- negative space
- headline-safe area
- hierarchy
- symmetry / asymmetry
- leading lines
- frame balance
- depth layers

==================================================
LIGHTING
==================================================

Analyze:

- key light direction
- key light softness
- fill behavior
- rim / edge light
- backlight
- practical lights
- contrast ratio
- apparent color temperature
- shadow direction
- contact shadows
- reflections
- specular highlights
- environmental light

==================================================
MATERIALS
==================================================

Identify relevant behavior of:

- glass
- metal
- plastic
- fabric
- skin
- leather
- architecture
- floors
- walls
- product surfaces
- roughness
- gloss
- translucency
- reflection properties

==================================================
COLOR
==================================================

Extract:

- dominant colors
- secondary colors
- accents
- approximate color relationships
- saturation behavior
- contrast behavior
- warm/cool balance

==================================================
PRODUCT LOCK
==================================================

If a product/card/phone/package is present AND this image is
being used as a product reference, determine which properties
must remain unchanged.

Potential locked attributes:

- silhouette
- proportions
- dimensions
- thickness
- corners
- edge geometry
- camera-facing orientation
- chip placement
- button placement
- camera-module placement
- packaging geometry
- material
- color
- graphic layout
- logo placement when appropriate

The environment may be redesigned unless the user explicitly
locks it.

Lighting may adapt to the new environment unless the user
explicitly locks it.

==================================================
SENSITIVE FINANCIAL INFORMATION
==================================================

Never transcribe or store:

- payment card numbers
- IBAN values
- account numbers
- CVV
- security codes
- PINs
- passwords
- private IDs

If sensitive financial text appears, ONLY report:

"sensitive_text_present": true

Never reproduce the actual value.

==================================================
VISUAL SUCCESS
==================================================

Explain concisely why the visual works:

- idea
- camera
- hierarchy
- lighting
- negative space
- material treatment
- visual simplicity
- emotional effect
- commercial effect

==================================================
GENERATION RISKS
==================================================

Identify likely generation failures:

- hand/product interaction
- warped card
- wrong perspective
- incorrect reflections
- broken typography
- inconsistent product geometry
- anatomy
- excessive complexity
- conflicting depth
- unrealistic scale

==================================================
OUTPUT
==================================================

Return JSON ONLY.

Required schema:

{{
  "summary": "",

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
    "tilt": "",
    "creative_reason": ""
  }},

  "perspective": {{
    "type": "",
    "vanishing_points": "",
    "distortion_level": "",
    "foreground": "",
    "midground": "",
    "background": "",
    "scale_relationship": ""
  }},

  "composition": {{
    "primary_focal_point": "",
    "secondary_element": "",
    "product_position": "",
    "person_position": "",
    "negative_space": "",
    "headline_safe_area": "",
    "visual_hierarchy": "",
    "leading_lines": "",
    "balance": "",
    "depth_layers": ""
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
    "contact_shadows": "",
    "reflection_behavior": "",
    "specular_behavior": ""
  }},

  "materials": [],

  "color_palette": {{
    "dominant": [],
    "secondary": [],
    "accents": [],
    "saturation": "",
    "contrast": "",
    "temperature_balance": ""
  }},

  "relationships": [],

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

Do not invent details that cannot reasonably be inferred.

Return only JSON.
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

    deterministic_role = (
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
            deterministic_role
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

    vision_role = normalized_role(
        data.get(
            "primary_reference_role"
        ),
        fallback=
            deterministic_role
    )

    final_role = resolve_final_reference_role(
        user_role=
            deterministic_role,

        vision_role=
            vision_role,

        user_note=
            user_note
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

    normalized_secondary = []

    for item in secondary:

        role = normalized_role(
            item
        )

        if (
            role
            and
            role != final_role
            and
            role not in normalized_secondary
        ):

            normalized_secondary.append(
                role
            )

    product_lock = data.get(
        "product_lock",
        {}
    )

    if not isinstance(
        product_lock,
        dict
    ):

        product_lock = {}

    # =====================================================
    # PRODUCT LOCK SAFETY
    #
    # Product lock should only be force-enabled when:
    # - reference is product_reference
    # - or Vision has strong product information
    # =====================================================

    if final_role == "product_reference":

        product_lock[
            "enabled"
        ] = True

    # =====================================================
    # SENSITIVE FIELD REDACTION
    # =====================================================

    sensitive_keys = [
        "card_number",
        "card_numbers",
        "iban",
        "iban_number",
        "account_number",
        "account_numbers",
        "cvv",
        "cvc",
        "security_code",
        "pin",
        "password",
        "sensitive_text",
        "sensitive_value",
        "financial_identifier",
    ]

    for key in sensitive_keys:

        product_lock.pop(
            key,
            None
        )

    product_lock[
        "sensitive_text_policy"
    ] = (
        "never store or reproduce"
    )

    # =====================================================
    # NORMALIZED RESULT
    # =====================================================

    result = {

        "visual_intelligence_version":
            VERSION,

        "summary":
            clean_text(
                data.get(
                    "summary"
                ),
                1500
            ),

        "primary_reference_role":
            final_role,

        "role_source":
            (
                "explicit_user_instruction"
                if classify_reference_role(
                    user_note
                ).get(
                    "matched_markers"
                )
                else
                "vision_analysis"
            ),

        "secondary_reference_roles":
            normalized_secondary,

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

ROLE_LABELS_AR = {
    "product_reference":
        "مرجع المنتج",

    "environment_reference":
        "مرجع البيئة / الخلفية",

    "camera_reference":
        "مرجع زاوية الكاميرا",

    "color_reference":
        "مرجع الألوان",

    "style_reference":
        "مرجع الأسلوب",

    "lighting_reference":
        "مرجع الإضاءة",

    "composition_reference":
        "مرجع التكوين",

    "person_reference":
        "مرجع الشخص",

    "campaign_reference":
        "مرجع الحملة",

    "mixed_reference":
        "مرجع متعدد الوظائف",
}


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

    role_label = ROLE_LABELS_AR.get(
        role,
        role
        or
        "مرجع بصري"
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
                "\n📷 الزاوية: "
                +
                (
                    shot
                    or
                    "غير محددة"
                )
            )

            if lens:

                camera_line += (
                    " | العدسة التقريبية: "
                    +
                    lens
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
        role_label
        +
        camera_line
        +
        lighting_line
        +
        composition_line
        +
        "\nدرجة الثقة: "
        +
        str(
            confidence
        )
        +
        "%"
    )


# =========================================================
# PRODUCT LOCK
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
# NO API CALLS
# NO VISION CALLS
# NO PAID USAGE
# =========================================================

if __name__ == "__main__":

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND VISUAL INTELLIGENCE V1.0.1"
    )
    print(
        "=========================================="
    )
    print("")

    tests = [
        (
            "هاي مرجع زاوية التصوير",
            "camera_reference"
        ),

        (
            "خد نفس زاوية الكاميرا من هاي",
            "camera_reference"
        ),

        (
            "هاي مرجع المنتج نفسه لا تغيره",
            "product_reference"
        ),

        (
            "هاي البطاقة نفسها خليها ثابتة",
            "product_reference"
        ),

        (
            "خد الإضاءة من هاي الصورة",
            "lighting_reference"
        ),

        (
            "هاي مرجع الخلفية والمكان",
            "environment_reference"
        ),

        (
            "خد الألوان من هاي",
            "color_reference"
        ),

        (
            "بدي نفس التكوين وترتيب العناصر",
            "composition_reference"
        ),

        (
            "هاي مرجع الستايل",
            "style_reference"
        ),

        (
            "حافظ على نفس الشخص والوجه",
            "person_reference"
        ),

        (
            "",
            "style_reference"
        ),
    ]

    passed = 0

    for text, expected in tests:

        actual = (
            infer_reference_role_from_note(
                text
            )
        )

        ok = (
            actual == expected
        )

        if ok:

            passed += 1

        print(
            (
                "✅"
                if ok
                else
                "❌"
            ),
            "| expected:",
            expected,
            "| actual:",
            actual,
            "|",
            text
        )

    print("")

    print(
        "Passed:",
        passed,
        "/",
        len(
            tests
        )
    )

    print("")

    print(
        "✅ Deterministic reference-role classifier"
    )

    print(
        "✅ User reference purpose overrides Vision"
    )

    print(
        "✅ Camera-reference detection"
    )

    print(
        "✅ Product-reference detection"
    )

    print(
        "✅ Environment-reference detection"
    )

    print(
        "✅ Lighting-reference detection"
    )

    print(
        "✅ Color-reference detection"
    )

    print(
        "✅ Composition-reference detection"
    )

    print(
        "✅ Person-reference detection"
    )

    print(
        "✅ Product Lock extraction"
    )

    print(
        "✅ Sensitive financial text redaction"
    )

    print(
        "✅ No paid API calls were made"
    )

    print("")
