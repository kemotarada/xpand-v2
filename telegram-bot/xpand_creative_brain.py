# =========================================================
# XPAND CREATIVE BRAIN V2.0
# VERSION 4.1
#
# QUALITY-FIRST ADAPTIVE CREATIVE INTELLIGENCE
#
# FIXES:
# - robust model-response JSON parsing
# - dict/list/provider-wrapper support
# - explicit ideation parse/shape/count failures
# - real compact recovery context
# - recovery evaluation ID matching
# - merchant payments semantic routing
# - technical failure != creative quality failure
# - technical fallback metadata for integration layer
# - detailed ideation telemetry
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
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
)

from xpand_stc_bank_skill import (
    STC_BANK_VISUAL_SKILL,
    is_stc_bank_request,
)

from xpand_image_engine import (
    call_openai_director,
)


# =========================================================
# IDENTITY
# =========================================================

VERSION = "4.1"

MODULE_NAME = "XPAND Creative Brain"


# =========================================================
# MODES
# =========================================================

MODE_FAST = "fast"
MODE_MASTERPIECE = "masterpiece"


# =========================================================
# QUALITY TARGETS
# =========================================================

MASTERPIECE_MIN_SCORE = max(
    70.0,
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
    65.0,
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
    40.0,
    min(
        90.0,
        float(
            os.environ.get(
                "XPAND_FAST_CREATIVE_MIN_SCORE",
                "65",
            )
            or 65
        ),
    ),
)


# =========================================================
# COST / CALL POLICY
# =========================================================

MASTERPIECE_MAX_IDEATION_ROUNDS = max(
    1,
    min(
        3,
        int(
            os.environ.get(
                "XPAND_MASTERPIECE_IDEATION_ROUNDS",
                "2",
            )
            or 2
        ),
    ),
)

MASTERPIECE_REVISION_CANDIDATES = max(
    0,
    min(
        1,
        int(
            os.environ.get(
                "XPAND_MASTERPIECE_REVISION_CANDIDATES",
                "1",
            )
            or 1
        ),
    ),
)

MASTERPIECE_REVISION_FLOOR = max(
    55.0,
    min(
        MASTERPIECE_MIN_SCORE,
        float(
            os.environ.get(
                "XPAND_MASTERPIECE_REVISION_FLOOR",
                "72",
            )
            or 72
        ),
    ),
)

MASTERPIECE_SHORTLIST_SIZE = max(
    5,
    min(
        10,
        int(
            os.environ.get(
                "XPAND_CREATIVE_SHORTLIST_SIZE",
                "10",
            )
            or 10
        ),
    ),
)

EVALUATION_BATCH_SIZE = MASTERPIECE_SHORTLIST_SIZE

EVALUATION_RETRIES = max(
    1,
    min(
        2,
        int(
            os.environ.get(
                "XPAND_CREATIVE_EVALUATION_RETRIES",
                "2",
            )
            or 2
        ),
    ),
)

MASTERPIECE_TARGET_DIRECTOR_CALLS = 4


# =========================================================
# QUALITY SUBSCORES
# =========================================================

MASTERPIECE_MIN_SUBSCORES = {
    "message_clarity": 82,
    "originality": 85,
    "brand_fit": 85,
    "visual_power": 85,
    "feasibility": 70,
    "perspective_integrity": 75,
    "campaign_potential": 78,
}

MASTERPIECE_RELEASE_MIN_SUBSCORES = {
    "message_clarity": 68,
    "originality": 70,
    "brand_fit": 72,
    "visual_power": 70,
    "feasibility": 60,
    "perspective_integrity": 60,
    "campaign_potential": 60,
}

SCORE_WEIGHTS = {
    "message_clarity": 20,
    "originality": 20,
    "brand_fit": 20,
    "visual_power": 15,
    "feasibility": 10,
    "perspective_integrity": 5,
    "campaign_potential": 10,
}


# =========================================================
# CONCEPT DISTRIBUTIONS
# =========================================================

MASTERPIECE_DISTRIBUTION = {
    "simple_intelligent": 5,
    "realistic_cinematic": 5,
    "conceptual_photorealism": 5,
    "scale_manipulation": 3,
    "bold_experimental": 2,
}

RECOVERY_DISTRIBUTION = {
    "strategic_rebuild": 1,
    "visual_metaphor_rebuild": 1,
    "bold_challenger": 1,
}

CHALLENGER_DISTRIBUTION = {
    "simple_intelligent": 1,
    "conceptual_photorealism": 1,
    "bold_experimental": 1,
}

FAST_DISTRIBUTION = {
    "simple_intelligent": 2,
    "realistic_cinematic": 2,
    "conceptual_photorealism": 1,
    "bold_experimental": 1,
}


# =========================================================
# CAMERA / LENS
# =========================================================

CAMERA_LIBRARY = {
    "eye_level": {
        "name": "Eye-Level Shot",
        "use_for": [
            "trust",
            "natural interaction",
            "balanced lifestyle scenes",
        ],
    },
    "low_angle": {
        "name": "Low-Angle Shot",
        "use_for": [
            "authority",
            "premium status",
            "heroic presence",
        ],
    },
    "extreme_low_angle": {
        "name": "Extreme Low-Angle Shot",
        "use_for": [
            "monumental scale",
            "architectural drama",
        ],
    },
    "worms_eye": {
        "name": "Worm’s-Eye View",
        "use_for": [
            "scale transformation",
            "unexpected perspective",
        ],
    },
    "high_angle": {
        "name": "High-Angle Shot",
        "use_for": [
            "overview",
            "relationship between elements",
        ],
    },
    "birds_eye": {
        "name": "Bird’s-Eye View",
        "use_for": [
            "systems",
            "routes",
            "connections",
            "spatial relationships",
        ],
    },
    "top_down": {
        "name": "Top-Down Shot",
        "use_for": [
            "graphic organization",
            "structured layouts",
        ],
    },
    "three_quarter": {
        "name": "Three-Quarter Hero Shot",
        "use_for": [
            "bank cards",
            "phones",
            "premium products",
        ],
    },
    "over_shoulder": {
        "name": "Over-the-Shoulder Shot",
        "use_for": [
            "digital experience",
            "banking interaction",
        ],
    },
    "pov": {
        "name": "Point-of-View Shot",
        "use_for": [
            "immersive experience",
            "travel",
            "payment moments",
        ],
    },
    "ground_level": {
        "name": "Ground-Level Shot",
        "use_for": [
            "movement",
            "speed",
            "foreground depth",
        ],
    },
    "macro": {
        "name": "Macro Shot",
        "use_for": [
            "product detail",
            "luxury textures",
        ],
    },
    "extreme_closeup": {
        "name": "Extreme Close-Up",
        "use_for": [
            "material detail",
            "micro-interaction",
        ],
    },
    "wide": {
        "name": "Wide Environmental Shot",
        "use_for": [
            "lifestyle",
            "brand worlds",
            "commercial environments",
        ],
    },
    "extreme_wide": {
        "name": "Extreme Wide Shot",
        "use_for": [
            "freedom",
            "scale",
            "possibility",
        ],
    },
    "forced_perspective": {
        "name": "Forced-Perspective Shot",
        "use_for": [
            "visual metaphor",
            "scale manipulation",
        ],
    },
    "central_one_point": {
        "name": "Central One-Point Perspective",
        "use_for": [
            "precision",
            "leading lines",
            "structured environments",
        ],
    },
    "frame_within_frame": {
        "name": "Frame-within-a-Frame Composition",
        "use_for": [
            "focus",
            "architecture",
            "cinematic storytelling",
        ],
    },
    "foreground_obstruction": {
        "name": "Foreground-Obstruction Composition",
        "use_for": [
            "cinematic realism",
            "depth",
            "premium photography",
        ],
    },
}

LENS_LIBRARY = {
    "14-20mm":
        "Extreme environmental drama with intentional perspective.",
    "24mm":
        "Wide premium environmental advertising.",
    "28mm":
        "Dynamic commercial environment with controlled perspective.",
    "35mm":
        "Cinematic environmental storytelling.",
    "50mm":
        "Balanced natural perspective.",
    "85mm":
        "Premium portrait compression.",
    "105mm":
        "Luxury portrait/product compression.",
    "macro":
        "Fine product and material detail.",
    "tilt_shift":
        "Architectural perspective control.",
}


# =========================================================
# ANTI-CLICHE
# =========================================================

ANTI_CLICHE_LIBRARY = [
    {
        "id": "flying_money",
        "markers": [
            "عملات طائرة",
            "فلوس طايره",
            "فلوس طائرة",
            "flying money",
            "flying coins",
            "money floating",
        ],
        "reason": "Overused financial advertising symbol.",
    },
    {
        "id": "phone_icons",
        "markers": [
            "هاتف محاط بايقونات",
            "هاتف محاط بأيقونات",
            "phone surrounded by icons",
            "floating app icons",
            "floating banking icons",
        ],
        "reason": "Generic fintech visualization.",
    },
    {
        "id": "security_shield",
        "markers": [
            "درع الامان",
            "درع الأمان",
            "security shield",
            "digital shield",
        ],
        "reason": "Common security cliché.",
    },
    {
        "id": "growth_arrow",
        "markers": [
            "سهم صاعد",
            "اسهم صاعده",
            "أسهم صاعدة",
            "upward arrow",
            "rising graph",
        ],
        "reason": "Generic business-growth symbolism.",
    },
    {
        "id": "generic_globe",
        "markers": [
            "كره ارضيه",
            "كرة أرضية",
            "globe",
            "world globe",
            "planet earth",
        ],
        "reason": "Overused international metaphor.",
    },
    {
        "id": "travel_gate",
        "markers": [
            "بوابه سفر",
            "بوابة سفر",
            "travel gate",
            "airport gate as portal",
            "magic portal",
            "magical portal",
        ],
        "reason": "Common travel-campaign visual device.",
    },
    {
        "id": "smiling_businessman",
        "markers": [
            "رجل اعمال يبتسم",
            "رجل أعمال يبتسم",
            "smiling businessman",
            "businessman smiling",
        ],
        "reason": "Generic corporate stock-photo cliché.",
    },
    {
        "id": "floating_card",
        "markers": [
            "بطاقه تطفو",
            "بطاقة تطفو",
            "floating bank card",
            "floating card",
        ],
        "reason": "Weak product presentation unless physically justified.",
    },
    {
        "id": "random_mini_city",
        "markers": [
            "مدينه مصغره",
            "مدينة مصغرة",
            "miniature city",
            "tiny city",
        ],
        "reason": "Common AI advertising visual without relevance.",
    },
    {
        "id": "random_purple_elements",
        "markers": [
            "عناصر بنفسجيه عشوائيه",
            "عناصر بنفسجية عشوائية",
            "random purple objects",
            "purple decorative elements",
        ],
        "reason": "Brand color used as decoration instead of concept.",
    },
    {
        "id": "handshake",
        "markers": [
            "مصافحه",
            "مصافحة",
            "handshake",
            "business handshake",
        ],
        "reason": "Overused trust/business cliché.",
    },
    {
        "id": "piggy_bank",
        "markers": [
            "حصاله",
            "حصالة",
            "piggy bank",
        ],
        "reason": "Overused savings metaphor.",
    },
    {
        "id": "calculator_money",
        "markers": [
            "اله حاسبه",
            "آلة حاسبة",
            "calculator and money",
        ],
        "reason": "Generic financial-services imagery.",
    },
    {
        "id": "random_hud",
        "markers": [
            "hud",
            "digital interface around",
            "floating interface",
            "دوائر تقنيه",
            "دوائر تقنية",
        ],
        "reason": "Generic futuristic banking treatment.",
    },
]


# =========================================================
# VISUAL METAPHORS
# =========================================================

METAPHOR_FAMILIES = {
    "merchant_payments": [
        "one real commercial ecosystem seamlessly serving in-store and online sales",
        "a physical retail action continuing naturally into digital commerce",
        "merchant activity flowing through one coherent real-world environment",
        "online and point-of-sale commerce expressed as one unified business operation",
    ],
    "speed": [
        "distance compression",
        "instant spatial transformation",
        "single uninterrupted motion",
        "time collapsed into physical distance",
    ],
    "international_transfer": [
        "two distant environments physically becoming one",
        "distance folded into a single real space",
        "two cultural spaces sharing one physical architecture",
        "real material transition eliminating perceived distance",
    ],
    "travel": [
        "home and destination existing in one continuous physical world",
        "destination changing around a constant traveler",
        "movement represented through environmental transformation",
        "travel utility integrated naturally into real human behavior",
    ],
    "security": [
        "calm protected space inside a chaotic environment",
        "precise architectural containment",
        "fragile value protected by physical structure rather than symbols",
    ],
    "control": [
        "complex environment resolving around one deliberate action",
        "many paths becoming one precise system",
    ],
    "cashback": [
        "value returning physically to its origin",
        "one action producing a visible secondary benefit",
    ],
    "flexibility": [
        "environment adapting around a stable user",
        "one object changing function without changing identity",
    ],
    "rewards": [
        "ordinary action revealing a premium secondary layer",
        "small interaction producing disproportionate value",
    ],
    "digital_banking": [
        "physical world behaving with digital simplicity",
        "complex banking represented by one seamless physical gesture",
    ],
    "premium": [
        "controlled simplicity",
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

    scores: Dict[str, float] = field(
        default_factory=dict
    )
    weighted_score: float = 0.0
    cliche_hits: List[Dict[str, str]] = field(
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
    concepts: List[CreativeConcept]
    top_concepts: List[CreativeConcept]
    winner: Optional[CreativeConcept]
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )
    errors: List[str] = field(
        default_factory=list
    )


# =========================================================
# EXCEPTIONS
# =========================================================

class CreativeBrainError(RuntimeError):
    pass


class IdeationParseError(CreativeBrainError):
    pass


class IdeationShapeError(CreativeBrainError):
    pass


class IdeationCountError(CreativeBrainError):
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
        .replace("\x00", "")
        .strip()[:limit]
    )


def normalize_text(
    value: Any,
) -> str:
    text = clean_text(
        value,
        30000,
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
    text: str,
    markers: Sequence[str],
) -> bool:
    source = normalize_text(text)

    return any(
        normalize_text(marker) in source
        for marker in markers
    )


def safe_list(
    value: Any,
) -> List[Any]:
    return value if isinstance(value, list) else []


def safe_dict(
    value: Any,
) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _short_type(
    value: Any,
) -> str:
    return type(value).__name__


# =========================================================
# ROBUST MODEL RESPONSE / JSON HELPERS
# =========================================================

def _object_to_plain_python(
    value: Any,
) -> Any:
    """
    Convert common SDK/provider response objects into plain
    Python objects without turning dicts into invalid JSON
    strings.
    """

    if value is None:
        return None

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
            dict,
            list,
            tuple,
        ),
    ):
        return value

    if isinstance(value, bytes):
        try:
            return value.decode(
                "utf-8",
                errors="replace",
            )
        except Exception:
            return str(value)

    for method_name in (
        "model_dump",
        "to_dict",
        "dict",
    ):
        method = getattr(
            value,
            method_name,
            None,
        )

        if callable(method):
            try:
                dumped = method()
                if dumped is not value:
                    return dumped
            except Exception:
                pass

    for attribute in (
        "output_text",
        "text",
        "content",
    ):
        try:
            candidate = getattr(
                value,
                attribute,
            )
        except Exception:
            candidate = None

        if candidate is not None:
            return candidate

    return value


def _looks_like_concept(
    item: Any,
) -> bool:
    if not isinstance(item, dict):
        return False

    markers = {
        "concept_id",
        "title",
        "core_idea",
        "visual_metaphor",
        "hero_element",
        "marketing_message",
    }

    return len(
        markers.intersection(
            item.keys()
        )
    ) >= 2


def _looks_like_evaluation(
    item: Any,
) -> bool:
    if not isinstance(item, dict):
        return False

    return (
        "concept_id" in item
        and
        (
            "scores" in item
            or
            "creative_director" in item
        )
    )


def _try_parse_json_text(
    text: str,
) -> Any:
    text = clean_text(
        text,
        250000,
    )

    if not text:
        raise IdeationParseError(
            "Model returned an empty response."
        )

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

    direct_error: Optional[Exception] = None

    try:
        return json.loads(text)

    except Exception as error:
        direct_error = error

    # Safe support for a Python-literal string representation
    # of an already structured provider response.
    try:
        literal = ast.literal_eval(text)

        if isinstance(
            literal,
            (
                dict,
                list,
            ),
        ):
            return literal

    except Exception:
        pass

    decoder = json.JSONDecoder()

    start_positions = [
        position
        for position in (
            text.find("{"),
            text.find("["),
        )
        if position >= 0
    ]

    for start in sorted(
        start_positions
    ):
        try:
            parsed, _ = decoder.raw_decode(
                text[start:]
            )

            if isinstance(
                parsed,
                (
                    dict,
                    list,
                ),
            ):
                return parsed

        except Exception:
            pass

    raise IdeationParseError(
        "Model response is not parseable JSON"
        + " | chars="
        + str(len(text))
        + " | error="
        + clean_text(
            direct_error,
            500,
        )
        + " | preview="
        + clean_text(
            text[:1200],
            1200,
        )
    )


def _extract_nested_payload(
    value: Any,
    depth: int = 0,
) -> Optional[
    Dict[str, Any]
]:
    if depth > 8:
        return None

    value = _object_to_plain_python(
        value
    )

    if isinstance(value, str):
        try:
            parsed = _try_parse_json_text(
                value
            )
        except Exception:
            return None

        return _extract_nested_payload(
            parsed,
            depth + 1,
        )

    if isinstance(value, tuple):
        value = list(value)

    if isinstance(value, list):
        if (
            value
            and
            all(
                _looks_like_concept(item)
                for item in value
            )
        ):
            return {
                "concepts": value
            }

        if (
            value
            and
            all(
                _looks_like_evaluation(item)
                for item in value
            )
        ):
            return {
                "evaluations": value
            }

        text_parts = []

        for item in value:
            if isinstance(item, str):
                text_parts.append(item)

            elif isinstance(item, dict):
                candidate = (
                    item.get("text")
                    or
                    item.get("content")
                    or
                    item.get("output_text")
                )

                if isinstance(candidate, str):
                    text_parts.append(candidate)

        if text_parts:
            try:
                return _extract_nested_payload(
                    "\n".join(text_parts),
                    depth + 1,
                )
            except Exception:
                pass

        for item in value:
            nested = _extract_nested_payload(
                item,
                depth + 1,
            )

            if nested:
                return nested

        return None

    if not isinstance(value, dict):
        return None

    direct_payload_keys = {
        "concepts",
        "evaluations",
        "camera_director",
        "production_blueprint",
        "feasibility",
        "scores",
    }

    if direct_payload_keys.intersection(
        value.keys()
    ):
        return value

    # OpenAI / Gemini / generic provider wrappers.
    preferred_keys = (
        "output_text",
        "text",
        "content",
        "response",
        "result",
        "data",
        "json",
        "message",
        "choices",
        "output",
        "candidate",
        "candidates",
    )

    for key in preferred_keys:
        if key not in value:
            continue

        nested = _extract_nested_payload(
            value.get(key),
            depth + 1,
        )

        if nested:
            return nested

    for nested_value in value.values():
        nested = _extract_nested_payload(
            nested_value,
            depth + 1,
        )

        if nested:
            return nested

    # A plain object may itself be the expected payload.
    return value


def extract_json_object(
    value: Any,
) -> Dict[str, Any]:
    """
    Robust JSON extraction.

    IMPORTANT:
    Previous implementation converted dict responses to str(),
    producing single-quoted Python representations that json.loads()
    could not parse. That path silently returned {}, which then became
    0 concepts.

    This implementation preserves native dict/list responses first.
    """

    original_type = _short_type(value)

    value = _object_to_plain_python(
        value
    )

    if isinstance(value, dict):
        nested = _extract_nested_payload(
            value
        )

        if isinstance(nested, dict):
            return nested

        return value

    if isinstance(value, tuple):
        value = list(value)

    if isinstance(value, list):
        nested = _extract_nested_payload(
            value
        )

        if isinstance(nested, dict):
            return nested

        raise IdeationParseError(
            "Model returned an unsupported list structure"
            + " | raw_type="
            + original_type
        )

    if not isinstance(value, str):
        value = clean_text(
            value,
            250000,
        )

    parsed = _try_parse_json_text(
        value
    )

    nested = _extract_nested_payload(
        parsed
    )

    if isinstance(nested, dict):
        return nested

    if isinstance(parsed, dict):
        return parsed

    if isinstance(parsed, list):
        if all(
            _looks_like_concept(item)
            for item in parsed
        ):
            return {
                "concepts": parsed
            }

        if all(
            _looks_like_evaluation(item)
            for item in parsed
        ):
            return {
                "evaluations": parsed
            }

    raise IdeationParseError(
        "Parsed model response has unsupported root shape"
        + " | raw_type="
        + original_type
        + " | parsed_type="
        + _short_type(parsed)
    )


def _find_list_under_keys(
    payload: Any,
    keys: Sequence[str],
    *,
    validator=None,
    depth: int = 0,
) -> List[Dict[str, Any]]:
    if depth > 8:
        return []

    if isinstance(payload, dict):
        for key in keys:
            value = payload.get(key)

            if isinstance(value, list):
                items = [
                    item
                    for item in value
                    if isinstance(item, dict)
                ]

                if (
                    not validator
                    or
                    not items
                    or
                    any(
                        validator(item)
                        for item in items
                    )
                ):
                    return items

            if isinstance(value, dict):
                values = [
                    item
                    for item in value.values()
                    if isinstance(item, dict)
                ]

                if (
                    values
                    and
                    (
                        not validator
                        or
                        any(
                            validator(item)
                            for item in values
                        )
                    )
                ):
                    return values

        for value in payload.values():
            found = _find_list_under_keys(
                value,
                keys,
                validator=validator,
                depth=depth + 1,
            )

            if found:
                return found

    elif isinstance(payload, list):
        items = [
            item
            for item in payload
            if isinstance(item, dict)
        ]

        if (
            items
            and
            (
                not validator
                or
                any(
                    validator(item)
                    for item in items
                )
            )
        ):
            return items

        for value in payload:
            found = _find_list_under_keys(
                value,
                keys,
                validator=validator,
                depth=depth + 1,
            )

            if found:
                return found

    return []


def compact_json_for_prompt(
    value: Any,
    limit: int,
) -> str:
    if not value:
        return "{}"

    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )

    except Exception:
        text = clean_text(
            value,
            limit,
        )

    if len(text) <= limit:
        return text

    front = int(
        limit * 0.72
    )

    back = max(
        0,
        limit - front - 80,
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
# SCORES
# =========================================================

def clamp_score(
    value: Any,
) -> float:
    try:
        number = float(value)

    except Exception:
        number = 0.0

    return max(
        0.0,
        min(
            100.0,
            number,
        ),
    )


def calculate_weighted_score(
    scores: Dict[str, Any],
) -> float:
    total = 0.0

    for key, weight in SCORE_WEIGHTS.items():
        score = clamp_score(
            scores.get(
                key,
                0,
            )
        )

        total += (
            score
            *
            (
                float(weight)
                /
                100.0
            )
        )

    return round(
        total,
        2,
    )


# =========================================================
# ANTI-CLICHE
# =========================================================

def detect_cliches(
    concept_text: str,
) -> List[Dict[str, str]]:
    hits: List[
        Dict[str, str]
    ] = []

    source = normalize_text(
        concept_text
    )

    for item in ANTI_CLICHE_LIBRARY:
        matched = any(
            normalize_text(marker)
            in source
            for marker in item["markers"]
        )

        if matched:
            hits.append(
                {
                    "id": item["id"],
                    "reason": item["reason"],
                }
            )

    return hits


def apply_cliche_penalty(
    weighted_score: float,
    cliche_hits: List[Dict[str, str]],
) -> float:
    if not cliche_hits:
        return weighted_score

    penalty = min(
        35.0,
        len(cliche_hits) * 10.0,
    )

    return round(
        max(
            0.0,
            weighted_score - penalty,
        ),
        2,
    )


# =========================================================
# BENEFIT / SEMANTIC ROUTING
# =========================================================

def infer_benefit_family(
    request: str,
) -> str:
    # MUST be checked before "points/rewards".
    # "نقاط البيع" contains "نقاط" but means POS, not rewards.
    if contains_any(
        request,
        [
            "التجارة الالكترونية",
            "التجارة الإلكترونية",
            "تجاره الكترونيه",
            "تجارة إلكترونية",
            "ecommerce",
            "e-commerce",
            "e commerce",
            "نقاط البيع",
            "نقطة البيع",
            "نقط البيع",
            "point of sale",
            "points of sale",
            "pos terminal",
            "pos terminals",
            "pos service",
            "merchant payment",
            "merchant payments",
            "مدفوعات التجار",
            "خدمات التجار",
            "بوابة دفع",
            "بوابه دفع",
            "payment gateway",
        ],
    ):
        return "merchant_payments"

    if contains_any(
        request,
        [
            "تحويل دولي",
            "تحويل مالي دولي",
            "تحويلات مالية دولية",
            "حوالة مالية دولية",
            "حواله ماليه دوليه",
            "international transfer",
            "international money transfer",
            "حول دولي",
            "حواله دوليه",
            "حوالة دولية",
        ],
    ):
        return "international_transfer"

    if contains_any(
        request,
        [
            "شريحتك",
            "شريحة",
            "roaming",
            "تجوال",
            "وجهة",
            "وجهات",
            "سفر",
            "travel",
            "مطارات",
            "دفع دولي",
            "الدفع الدولي",
        ],
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
        ],
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
        ],
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
        ],
    ):
        return "control"

    if contains_any(
        request,
        [
            "كاش باك",
            "cashback",
            "استرداد",
        ],
    ):
        return "cashback"

    if contains_any(
        request,
        [
            "مرونه",
            "مرونة",
            "flexibility",
            "flexible",
        ],
    ):
        return "flexibility"

    if contains_any(
        request,
        [
            "مكافات",
            "مكافآت",
            "rewards",
            "reward points",
            "نقاط مكافآت",
            "نقاط المكافآت",
        ],
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
        ],
    ):
        return "digital_banking"

    return "premium"


def get_metaphor_seed(
    request: str,
) -> Dict[str, Any]:
    family = infer_benefit_family(
        request
    )

    return {
        "family": family,
        "directions": METAPHOR_FAMILIES.get(
            family,
            METAPHOR_FAMILIES[
                "premium"
            ],
        ),
    }


# =========================================================
# STC BANK EXECUTION RULES
# =========================================================

STC_FORBIDDEN_CONCEPT_MARKERS = (
    "floating card",
    "floating phone",
    "levitating",
    "unsupported product",
    "hologram",
    "holographic",
    "wireframe",
    "futuristic interface",
    "connection line",
    "network line",
    "route line",
    "dotted path",
    "laser beam",
    "transfer path",
    "particle",
    "sparkle",
    "hud",
    "ui overlay",
    "بطاقة طافية",
    "هاتف طائر",
    "هاتف يطفو",
    "يطفو",
    "تطفو",
    "هولوغرام",
    "مسار تحويل ضوئي",
    "خط اتصال",
    "خطوط اتصال",
)


def stc_concept_violations(
    concept: CreativeConcept,
) -> List[str]:
    source = normalize_text(
        "\n".join(
            [
                concept.title,
                concept.core_idea,
                concept.marketing_message,
                concept.visual_metaphor,
                concept.environment,
                concept.hero_element,
                " ".join(
                    concept.supporting_elements
                ),
                concept.campaign_extension,
            ]
        )
    )

    return [
        marker
        for marker in STC_FORBIDDEN_CONCEPT_MARKERS
        if normalize_text(marker)
        in source
    ]


# =========================================================
# CONTEXT
# =========================================================

def compact_brand_context(
    brand_context: Any,
    limit: int = 4500,
) -> str:
    if not brand_context:
        return (
            "No structured brand context supplied."
        )

    if isinstance(
        brand_context,
        str,
    ):
        return clean_text(
            brand_context,
            limit,
        )

    return compact_json_for_prompt(
        brand_context,
        limit,
    )


def compact_visual_references(
    visual_references: Any,
    limit: int = 3500,
) -> str:
    if not visual_references:
        return (
            "No Visual Reference DNA supplied."
        )

    if isinstance(
        visual_references,
        str,
    ):
        return clean_text(
            visual_references,
            limit,
        )

    return compact_json_for_prompt(
        visual_references,
        limit,
    )


def distribution_text(
    distribution: Dict[str, int],
) -> str:
    return "\n".join(
        f"- {category}: {count} concepts"
        for category, count
        in distribution.items()
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
    distribution = (
        FAST_DISTRIBUTION
        if mode == MODE_FAST
        else MASTERPIECE_DISTRIBUTION
    )

    requested_count = sum(
        distribution.values()
    )

    stc_request = is_stc_bank_request(
        user_request
    )

    metaphor_seed = (
        {
            "family":
                "STC Bank dedicated visual system",
            "directions":
                [],
        }
        if stc_request
        else
        get_metaphor_seed(
            user_request
        )
    )

    stc_skill = (
        STC_BANK_VISUAL_SKILL
        if stc_request
        else ""
    )

    recovery_context = clean_text(
        failure_context,
        2600,
    )

    return f"""
{stc_skill}

You are XPAND Creative Brain V2.

Act as a top international advertising concept team.

Do NOT generate an image.
Do NOT expose chain-of-thought.
Return strict JSON only.

==================================================
USER REQUEST
==================================================

{clean_text(user_request, 6000)}

==================================================
BRAND EXECUTION CONTEXT
==================================================

{compact_brand_context(brand_context, 3600)}

==================================================
VISUAL REFERENCE DNA
==================================================

{compact_visual_references(visual_references, 2800)}

==================================================
STYLE HINT
==================================================

{clean_text(style_hint, 1000) or "Choose the strongest appropriate style."}

==================================================
BENEFIT FAMILY
==================================================

{metaphor_seed["family"]}

Metaphor seeds:

{compact_json_for_prompt(metaphor_seed["directions"], 1700)}

For STC Bank, the empty seed list is intentional.
Never replace it with generic fintech imagery.

==================================================
ROUND / RECOVERY CONTEXT
==================================================

round_number = {round_number}
challenger = {"true" if challenger else "false"}

{recovery_context or "No previous ideation failure."}

If this is a recovery attempt because a previous answer was
malformed, incomplete, truncated or could not be parsed:

- prioritize VALID JSON over verbosity
- keep every string concise
- do not wrap JSON in Markdown
- do not put commentary before JSON
- do not put commentary after JSON
- return every required field
- return EXACTLY {requested_count} concept objects

If challenger=true:
- create materially different visual mechanisms
- do not repeat the previous visual grammar
- preserve the same commercial message

==================================================
REQUIRED DISTRIBUTION
==================================================

{distribution_text(distribution)}

==================================================
MASTERPIECE STANDARD
==================================================

Generate EXACTLY {requested_count} concepts.

Every concept must:
- have one dominant visual mechanism
- communicate the commercial benefit visually
- be materially different from the others
- use a coherent camera/lens/perspective
- be photographically believable
- be production-ready
- preserve useful negative space
- avoid generic AI decoration

==================================================
HARD ANTI-CLICHE
==================================================

Avoid unless transformed beyond recognition:

- flying money
- flying coins
- generic globe
- connection lines around the world
- phone surrounded by icons
- floating SIM card
- floating bank card
- security shield
- growth arrows
- magic portal
- generic airport gate
- smiling businessman
- handshake
- random miniature city
- decorative purple objects
- random HUD graphics
- generic neon fintech imagery

Brand color is not a concept.

==================================================
PRODUCTION
==================================================

Allowed production_method values:

- single_generation
- composite
- inpainting
- controlled_edit
- multi_pass

==================================================
OUTPUT
==================================================

Return JSON only:

{{
  "concepts": [
    {{
      "concept_id": "C01",
      "category": "",
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
  ]
}}

Do NOT score concepts.
Do NOT choose a winner.

==================================================
ACTIVE BRAND SKILL
==================================================

{stc_skill or "No dedicated brand skill activated."}
""".strip()


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
    supporting = safe_list(
        item.get(
            "supporting_elements"
        )
    )

    risks = safe_list(
        item.get(
            "risks"
        )
    )

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
            100,
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
            1400,
        ),
        visual_metaphor=clean_text(
            item.get(
                "visual_metaphor"
            ),
            1600,
        ),
        environment=clean_text(
            item.get(
                "environment"
            ),
            1700,
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
            for value in supporting[:8]
            if clean_text(
                value,
                600,
            )
        ],
        camera_angle=clean_text(
            item.get(
                "camera_angle"
            ),
            500,
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
            700,
        ),
        lighting=clean_text(
            item.get(
                "lighting"
            ),
            900,
        ),
        negative_space=clean_text(
            item.get(
                "negative_space"
            ),
            700,
        ),
        brand_logic=clean_text(
            item.get(
                "brand_logic"
            ),
            1200,
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
            900,
        ),
        risks=[
            clean_text(
                value,
                600,
            )
            for value in risks[:8]
            if clean_text(
                value,
                600,
            )
        ],
        generation_round=generation_round,
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
            concept.environment,
            concept.hero_element,
            " ".join(
                concept.supporting_elements
            ),
        ]
    )

    concept.cliche_hits = detect_cliches(
        concept_text
    )

    return concept


def _extract_concept_items(
    payload: Dict[str, Any],
) -> List[Dict[str, Any]]:
    return _find_list_under_keys(
        payload,
        (
            "concepts",
            "ideas",
            "directions",
            "creative_concepts",
            "items",
            "results",
        ),
        validator=_looks_like_concept,
    )


def parse_concepts(
    payload: Dict[str, Any],
    *,
    generation_round: int = 1,
) -> List[CreativeConcept]:
    raw_concepts = _extract_concept_items(
        payload
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
            continue

        concepts.append(
            concept_from_dict(
                item,
                fallback_id=(
                    "C"
                    +
                    str(index).zfill(2)
                ),
                generation_round=(
                    generation_round
                ),
            )
        )

    return concepts


# =========================================================
# DUPLICATE SUPPRESSION
# =========================================================

def concept_fingerprint(
    concept: CreativeConcept,
) -> str:
    value = (
        concept.title
        + " "
        + concept.core_idea
        + " "
        + concept.visual_metaphor
        + " "
        + concept.hero_element
    )

    value = normalize_text(
        value
    )

    value = re.sub(
        r"[^a-z0-9\u0600-\u06FF ]+",
        " ",
        value,
    )

    words = [
        word
        for word in value.split()
        if len(word) > 2
    ]

    return " ".join(
        words[:35]
    )


def deduplicate_concepts(
    concepts: List[CreativeConcept],
    existing: Sequence[CreativeConcept] = (),
) -> List[CreativeConcept]:
    seen = {
        concept_fingerprint(item)
        for item in existing
        if concept_fingerprint(item)
    }

    output: List[
        CreativeConcept
    ] = []

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


def assign_round_ids(
    concepts: List[CreativeConcept],
    round_number: int,
) -> None:
    used = set()

    for index, concept in enumerate(
        concepts,
        start=1,
    ):
        base = (
            clean_text(
                concept.concept_id,
                80,
            )
            or
            (
                "C"
                +
                str(index).zfill(2)
            )
        )

        if round_number > 1:
            base = (
                "R"
                +
                str(round_number)
                +
                "-"
                +
                base
            )

        candidate = base
        suffix = 2

        while candidate in used:
            candidate = (
                base
                +
                "-"
                +
                str(suffix)
            )

            suffix += 1

        used.add(
            candidate
        )

        concept.concept_id = candidate
        concept.generation_round = (
            round_number
        )


# =========================================================
# TELEMETRY
# =========================================================

def register_model_call(
    telemetry: Optional[Dict[str, Any]],
    label: str,
) -> None:
    if telemetry is None:
        return

    telemetry["director_calls"] = (
        int(
            telemetry.get(
                "director_calls",
                0,
            )
        )
        +
        1
    )

    history = telemetry.setdefault(
        "director_call_history",
        [],
    )

    history.append(label)


def _record_ideation_debug(
    telemetry: Optional[Dict[str, Any]],
    *,
    raw: Any,
    payload: Optional[Dict[str, Any]],
    parsed_count: int,
    expected: int,
    stage: str,
) -> None:
    if telemetry is None:
        return

    history = telemetry.setdefault(
        "ideation_debug",
        [],
    )

    payload_keys = (
        list(payload.keys())[:20]
        if isinstance(payload, dict)
        else []
    )

    history.append(
        {
            "stage": stage,
            "raw_type": _short_type(raw),
            "payload_keys": payload_keys,
            "parsed_concepts": parsed_count,
            "expected_concepts": expected,
        }
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
    challenger: bool = False,
    telemetry: Optional[Dict[str, Any]] = None,
) -> List[CreativeConcept]:
    distribution = (
        FAST_DISTRIBUTION
        if mode == MODE_FAST
        else MASTERPIECE_DISTRIBUTION
    )

    expected = sum(
        distribution.values()
    )

    prompt = build_concept_generation_prompt(
        user_request=user_request,
        brand_context=brand_context,
        visual_references=visual_references,
        style_hint=style_hint,
        mode=mode,
        round_number=round_number,
        failure_context=failure_context,
        challenger=challenger,
    )

    prompt += """

XPAND BANKING CREATIVE INTELLIGENCE
===================================

For bank, fintech, merchant, card, POS, ecommerce, transfer,
cashback, travel, payment or digital banking work:

- prioritize commercial communication
- prioritize real photography / premium photorealism
- use natural human behavior when useful
- use motivated lighting
- preserve correct contact shadows
- preserve believable scale
- preserve material realism
- preserve one coherent perspective
- avoid generic AI-fintech decoration

For merchant payments / ecommerce / POS:
show the merchant benefit rather than abstract financial symbolism.
The image should naturally communicate accepting and managing commerce
across real point-of-sale and online contexts without literal connection
lines, floating icons, glowing payment routes or random interfaces.
""".strip()

    register_model_call(
        telemetry,
        (
            "challenger_ideation"
            if challenger
            else
            (
                "compact_ideation_recovery"
                if failure_context
                else
                "ideation"
            )
        ),
    )

    raw = call_openai_director(
        prompt,
        json_mode=True,
    )

    try:
        payload = extract_json_object(
            raw
        )

    except Exception as error:
        _record_ideation_debug(
            telemetry,
            raw=raw,
            payload=None,
            parsed_count=0,
            expected=expected,
            stage="parse_failed",
        )

        raise IdeationParseError(
            "Creative Brain ideation JSON parse failed"
            + " | raw_type="
            + _short_type(raw)
            + " | "
            + clean_text(
                error,
                2200,
            )
        ) from error

    raw_items = _extract_concept_items(
        payload
    )

    if not raw_items:
        _record_ideation_debug(
            telemetry,
            raw=raw,
            payload=payload,
            parsed_count=0,
            expected=expected,
            stage="shape_failed",
        )

        raise IdeationShapeError(
            "Creative Brain JSON contains no concept collection"
            + " | top_level_keys="
            + ",".join(
                str(key)
                for key in list(
                    payload.keys()
                )[:20]
            )
        )

    concepts = parse_concepts(
        payload,
        generation_round=round_number,
    )

    _record_ideation_debug(
        telemetry,
        raw=raw,
        payload=payload,
        parsed_count=len(concepts),
        expected=expected,
        stage="parsed",
    )

    print(
        "🧪 Ideation parse"
        + " | raw_type="
        + _short_type(raw)
        + " | keys="
        + ",".join(
            list(payload.keys())[:10]
        )
        + " | raw_concepts="
        + str(len(raw_items))
        + " | parsed_concepts="
        + str(len(concepts))
        + " | expected="
        + str(expected)
    )

    if is_stc_bank_request(
        user_request
    ):
        for concept in concepts:
            violations = stc_concept_violations(
                concept
            )

            if violations:
                concept.debate[
                    "stc_hard_rejection"
                ] = violations

                concept.cliche_hits.extend(
                    {
                        "id":
                            "stc_visual_violation",
                        "reason":
                            "STC visual rule: "
                            + marker,
                    }
                    for marker in violations
                )

    minimum_usable = (
        3
        if is_stc_bank_request(
            user_request
        )
        else
        max(
            3,
            int(
                expected * 0.60
            ),
        )
    )

    if len(concepts) < minimum_usable:
        raise IdeationCountError(
            "Creative Brain returned too few parsed concepts: "
            + str(len(concepts))
            + "/"
            + str(expected)
            + " | minimum_required="
            + str(minimum_usable)
        )

    assign_round_ids(
        concepts,
        round_number,
    )

    return concepts


# =========================================================
# FREE LOCAL PREFLIGHT
# =========================================================

def local_preflight_score(
    concept: CreativeConcept,
) -> float:
    score = 50.0

    required_text = [
        concept.core_idea,
        concept.marketing_message,
        concept.visual_metaphor,
        concept.environment,
        concept.hero_element,
        concept.camera_angle,
        concept.lens,
        concept.perspective,
        concept.lighting,
        concept.negative_space,
        concept.brand_logic,
    ]

    completion = sum(
        1
        for value in required_text
        if clean_text(
            value,
            20,
        )
    )

    score += (
        completion
        /
        len(required_text)
        *
        24.0
    )

    if concept.visual_metaphor:
        score += 5.0

    if concept.camera_angle:
        score += 3.0

    if concept.lens:
        score += 2.0

    if concept.negative_space:
        score += 2.0

    if concept.brand_logic:
        score += 4.0

    if concept.production_method in {
        "single_generation",
        "composite",
        "inpainting",
        "controlled_edit",
        "multi_pass",
    }:
        score += 2.0

    score -= min(
        6.0,
        len(concept.risks) * 1.0,
    )

    score -= (
        len(
            concept.cliche_hits
        )
        *
        18.0
    )

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


def shortlist_concepts(
    concepts: Sequence[CreativeConcept],
    *,
    limit: int,
) -> List[CreativeConcept]:
    scored = list(concepts)

    for concept in scored:
        concept.debate[
            "local_preflight"
        ] = {
            "score":
                local_preflight_score(
                    concept
                ),
            "model_evaluation":
                False,
            "purpose":
                "free_shortlist_only",
        }

    clean_pool = [
        concept
        for concept in scored
        if not concept.cliche_hits
    ]

    dirty_pool = [
        concept
        for concept in scored
        if concept.cliche_hits
    ]

    def score_of(
        item: CreativeConcept,
    ) -> float:
        return float(
            safe_dict(
                item.debate.get(
                    "local_preflight"
                )
            ).get(
                "score",
                0,
            )
        )

    clean_pool.sort(
        key=score_of,
        reverse=True,
    )

    dirty_pool.sort(
        key=score_of,
        reverse=True,
    )

    selected: List[
        CreativeConcept
    ] = []

    used_categories = set()

    for concept in clean_pool:
        if len(selected) >= limit:
            break

        category = (
            concept.category
            or "uncategorized"
        )

        if category in used_categories:
            continue

        selected.append(
            concept
        )

        used_categories.add(
            category
        )

    selected_ids = {
        item.concept_id
        for item in selected
    }

    for concept in clean_pool:
        if len(selected) >= limit:
            break

        if concept.concept_id in selected_ids:
            continue

        selected.append(concept)
        selected_ids.add(
            concept.concept_id
        )

    for concept in dirty_pool:
        if len(selected) >= limit:
            break

        if concept.concept_id in selected_ids:
            continue

        selected.append(concept)
        selected_ids.add(
            concept.concept_id
        )

    return selected[:limit]


# =========================================================
# EVALUATION PAYLOAD
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
# REVIEW BOARD
# =========================================================

def build_evaluation_prompt(
    *,
    user_request: str,
    concepts: List[CreativeConcept],
    brand_context: Any = None,
    visual_references: Any = None,
) -> str:
    concepts_json = compact_json_for_prompt(
        [
            concept_payload_for_evaluation(
                concept
            )
            for concept in concepts
        ],
        10000,
    )

    stc_skill = (
        STC_BANK_VISUAL_SKILL
        if is_stc_bank_request(
            user_request
        )
        else ""
    )

    return f"""
{stc_skill}

You are XPAND Masterpiece Creative Review Board.

Do NOT generate an image.
Do NOT expose chain-of-thought.
Return strict JSON only.

ORIGINAL REQUEST:
{clean_text(user_request, 4200)}

BRAND:
{compact_brand_context(brand_context, 2600)}

VISUAL REFERENCES:
{compact_visual_references(visual_references, 2200)}

SHORTLIST:
{concepts_json}

Score every supplied concept 0-100:

- message_clarity
- originality
- brand_fit
- visual_power
- feasibility
- perspective_integrity
- campaign_potential

Calibration:

50 = ordinary
60 = acceptable
70 = good
75 = strong
82 = campaign-level
88 = exceptional
92+ = rare

Do not inflate scores.

Act as:
- Creative Director
- Brand Guardian
- Production Expert
- Harsh Critic

Return exactly one evaluation for every supplied concept.

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
        "approved": true,
        "verdict": ""
      }},
      "brand_guardian": {{
        "approved": true,
        "verdict": ""
      }},
      "production_expert": {{
        "approved": true,
        "verdict": ""
      }},
      "harsh_critic": {{
        "approved": true,
        "verdict": ""
      }},
      "camera_review": {{
        "current_camera_valid": true,
        "recommended_camera_angle": "",
        "recommended_lens": "",
        "perspective": "",
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
""".strip()


def apply_evaluation(
    concept: CreativeConcept,
    evaluation: Dict[str, Any],
) -> None:
    scores = safe_dict(
        evaluation.get(
            "scores"
        )
    )

    required = set(
        SCORE_WEIGHTS.keys()
    )

    supplied = {
        key
        for key in scores.keys()
        if key in required
    }

    evaluation_valid = (
        supplied == required
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

    weighted = calculate_weighted_score(
        normalized_scores
    )

    weighted = apply_cliche_penalty(
        weighted,
        concept.cliche_hits,
    )

    local_preflight = safe_dict(
        concept.debate.get(
            "local_preflight"
        )
    )

    concept.scores = normalized_scores
    concept.weighted_score = weighted
    concept.evaluation_valid = (
        evaluation_valid
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
        "camera_review":
            safe_dict(
                evaluation.get(
                    "camera_review"
                )
            ),
        "revision_required":
            bool(
                evaluation.get(
                    "revision_required",
                    False,
                )
            ),
        "revision_instruction":
            clean_text(
                evaluation.get(
                    "revision_instruction",
                    "",
                ),
                1800,
            ),
    }

    concept.feasibility = safe_dict(
        evaluation.get(
            "feasibility"
        )
    )


def _evaluation_items(
    payload: Any,
) -> List[Dict[str, Any]]:
    return _find_list_under_keys(
        payload,
        (
            "evaluations",
            "reviews",
            "results",
            "items",
        ),
        validator=_looks_like_evaluation,
    )


def evaluate_concept_batch(
    *,
    user_request: str,
    concepts: List[CreativeConcept],
    brand_context: Any = None,
    visual_references: Any = None,
    telemetry: Optional[Dict[str, Any]] = None,
) -> Dict[str, Dict[str, Any]]:
    expected_ids = {
        concept.concept_id
        for concept in concepts
    }

    best_map: Dict[
        str,
        Dict[str, Any]
    ] = {}

    last_error: Optional[
        Exception
    ] = None

    chunks = [
        concepts[
            index:
            index + 5
        ]
        for index in range(
            0,
            len(concepts),
            5,
        )
    ]

    for chunk_index, chunk in enumerate(
        chunks,
        start=1,
    ):
        chunk_ids = {
            item.concept_id
            for item in chunk
        }

        for attempt in range(
            1,
            EVALUATION_RETRIES + 1,
        ):
            pending = [
                item
                for item in chunk
                if item.concept_id
                not in best_map
            ]

            if not pending:
                break

            prompt = build_evaluation_prompt(
                user_request=user_request,
                concepts=pending,
                brand_context=brand_context,
                visual_references=visual_references,
            )

            if attempt > 1:
                prompt += (
                    "\n\nRETRY CONTRACT:\n"
                    "Return evaluations ONLY for these IDs: "
                    +
                    ", ".join(
                        item.concept_id
                        for item in pending
                    )
                    +
                    ". Do not rename IDs."
                )

            try:
                register_model_call(
                    telemetry,
                    (
                        "creative_review_chunk_"
                        + str(chunk_index)
                        + (
                            ""
                            if attempt == 1
                            else "_retry"
                        )
                    ),
                )

                raw = call_openai_director(
                    prompt,
                    json_mode=True,
                )

                payload = extract_json_object(
                    raw
                )

                parsed_items = _evaluation_items(
                    payload
                )

                # Support keyed payload:
                # {"C01": {...}, "C02": {...}}
                if not parsed_items:
                    for key, value in payload.items():
                        if (
                            key in chunk_ids
                            and
                            isinstance(
                                value,
                                dict,
                            )
                        ):
                            item = dict(value)
                            item.setdefault(
                                "concept_id",
                                key,
                            )
                            parsed_items.append(
                                item
                            )

                for item in parsed_items:
                    concept_id = clean_text(
                        item.get(
                            "concept_id"
                        ),
                        100,
                    )

                    if concept_id in chunk_ids:
                        best_map[
                            concept_id
                        ] = item

                missing = (
                    chunk_ids
                    -
                    set(
                        best_map.keys()
                    )
                )

                if not missing:
                    break

                last_error = RuntimeError(
                    "Creative review missing IDs: "
                    +
                    ", ".join(
                        sorted(missing)
                    )
                )

                print(
                    "⚠️ Review Board chunk incomplete"
                    + " | chunk="
                    + str(chunk_index)
                    + " | missing="
                    + str(len(missing))
                )

            except Exception as error:
                last_error = error

                print(
                    "⚠️ Review Board chunk failed"
                    + " | chunk="
                    + str(chunk_index)
                    + " | "
                    + clean_text(
                        error,
                        1400,
                    )
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

    if best_map:
        return best_map

    raise RuntimeError(
        "Creative Review Board failed"
        + (
            ": "
            + clean_text(
                last_error,
                1800,
            )
            if last_error
            else ""
        )
    )


def evaluate_concept_pool(
    *,
    user_request: str,
    concepts: List[CreativeConcept],
    brand_context: Any = None,
    visual_references: Any = None,
    mode: str = MODE_MASTERPIECE,
    telemetry: Optional[Dict[str, Any]] = None,
) -> List[CreativeConcept]:
    if not concepts:
        return []

    try:
        evaluation_map = evaluate_concept_batch(
            user_request=user_request,
            concepts=concepts,
            brand_context=brand_context,
            visual_references=visual_references,
            telemetry=telemetry,
        )

    except Exception as error:
        print(
            "❌ Creative review unavailable: "
            +
            clean_text(
                error,
                1600,
            )
        )

        evaluation_map = {}

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

        elif mode == MODE_FAST:
            apply_fast_fallback_score(
                concept
            )

        else:
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
# FAST FALLBACK SCORE
# =========================================================

def apply_fast_fallback_score(
    concept: CreativeConcept,
) -> None:
    fallback_scores = {
        "message_clarity": 60,
        "originality": (
            35
            if concept.cliche_hits
            else 60
        ),
        "brand_fit": 60,
        "visual_power": 60,
        "feasibility": 55,
        "perspective_integrity": 55,
        "campaign_potential": 55,
    }

    concept.scores = fallback_scores

    concept.weighted_score = (
        apply_cliche_penalty(
            calculate_weighted_score(
                fallback_scores
            ),
            concept.cliche_hits,
        )
    )

    concept.evaluation_valid = False

    concept.debate[
        "fallback_scoring"
    ] = True


# =========================================================
# QUALITY GATES
# =========================================================

def role_approved(
    value: Any,
) -> bool:
    return (
        isinstance(value, dict)
        and
        bool(
            value.get(
                "approved",
                False,
            )
        )
    )


def target_gate_failures(
    concept: CreativeConcept,
) -> List[str]:
    failures: List[str] = []

    if not concept.evaluation_valid:
        failures.append(
            "no_valid_model_evaluation"
        )

    if (
        concept.weighted_score
        <
        MASTERPIECE_MIN_SCORE
    ):
        failures.append(
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

    for key, minimum in (
        MASTERPIECE_MIN_SUBSCORES.items()
    ):
        value = clamp_score(
            concept.scores.get(
                key,
                0,
            )
        )

        if value < minimum:
            failures.append(
                key
                +
                "_"
                +
                str(value)
                +
                "_below_"
                +
                str(minimum)
            )

    if concept.cliche_hits:
        failures.append(
            "anti_cliche_hits:"
            +
            ",".join(
                item.get(
                    "id",
                    "",
                )
                for item
                in concept.cliche_hits
                if item.get("id")
            )
        )

    for role in (
        "creative_director",
        "brand_guardian",
        "production_expert",
        "harsh_critic",
    ):
        if not role_approved(
            concept.debate.get(
                role
            )
        ):
            failures.append(
                role
                +
                "_rejected"
            )

    if concept.debate.get(
        "revision_required",
        False,
    ):
        failures.append(
            "revision_required"
        )

    return failures


def adaptive_release_failures(
    concept: CreativeConcept,
) -> List[str]:
    failures: List[str] = []

    if not concept.evaluation_valid:
        failures.append(
            "no_valid_model_evaluation"
        )

    if (
        concept.weighted_score
        <
        MASTERPIECE_RELEASE_FLOOR
    ):
        failures.append(
            "weighted_score_below_release_floor_"
            +
            str(
                MASTERPIECE_RELEASE_FLOOR
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
                key
                +
                "_below_release_"
                +
                str(minimum)
            )

    if concept.cliche_hits:
        failures.append(
            "anti_cliche_hard_block"
        )

    for role in (
        "creative_director",
        "brand_guardian",
        "production_expert",
        "harsh_critic",
    ):
        if not role_approved(
            concept.debate.get(
                role
            )
        ):
            failures.append(
                role
                +
                "_rejected"
            )

    return failures


def evaluate_quality_gate(
    concept: CreativeConcept,
    *,
    mode: str,
) -> Tuple[bool, List[str]]:
    if mode == MODE_FAST:
        failures = []

        if (
            concept.weighted_score
            <
            FAST_MIN_SCORE
        ):
            failures.append(
                "weighted_score_below_"
                +
                str(
                    FAST_MIN_SCORE
                )
            )

        return (
            not failures,
            failures,
        )

    strict_failures = target_gate_failures(
        concept
    )

    if not strict_failures:
        concept.debate[
            "quality_release_level"
        ] = "target_82_plus"

        return True, []

    release_failures = (
        adaptive_release_failures(
            concept
        )
    )

    if not release_failures:
        concept.debate[
            "quality_release_level"
        ] = "adaptive_release"

        concept.debate[
            "target_gate_failures"
        ] = strict_failures

        return True, []

    concept.debate[
        "target_gate_failures"
    ] = strict_failures

    concept.debate[
        "adaptive_release_failures"
    ] = release_failures

    return (
        False,
        release_failures,
    )


def refresh_quality_gates(
    concepts: Sequence[CreativeConcept],
    *,
    mode: str,
) -> None:
    for concept in concepts:
        passed, failures = (
            evaluate_quality_gate(
                concept,
                mode=mode,
            )
        )

        concept.quality_gate_passed = passed
        concept.quality_gate_failures = (
            failures
        )


def concept_passes_review(
    concept: CreativeConcept,
    mode: str = MODE_MASTERPIECE,
) -> bool:
    passed, failures = evaluate_quality_gate(
        concept,
        mode=mode,
    )

    concept.quality_gate_passed = passed
    concept.quality_gate_failures = (
        failures
    )

    return passed


# =========================================================
# RANKING
# =========================================================

def rank_concepts(
    concepts: Sequence[CreativeConcept],
) -> List[CreativeConcept]:
    return sorted(
        list(concepts),
        key=lambda item: (
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
    concepts: List[CreativeConcept],
    limit: int = 3,
    mode: str = MODE_MASTERPIECE,
    qualified_only: bool = True,
) -> List[CreativeConcept]:
    refresh_quality_gates(
        concepts,
        mode=mode,
    )

    pool = (
        [
            concept
            for concept in concepts
            if concept.quality_gate_passed
        ]
        if qualified_only
        else
        list(concepts)
    )

    ordered = rank_concepts(
        pool
    )

    selected: List[
        CreativeConcept
    ] = []

    used_categories = set()

    for concept in ordered:
        if len(selected) >= limit:
            break

        category = (
            concept.category
            or "uncategorized"
        )

        if category in used_categories:
            continue

        selected.append(
            concept
        )

        used_categories.add(
            category
        )

    selected_ids = {
        item.concept_id
        for item in selected
    }

    for concept in ordered:
        if len(selected) >= limit:
            break

        if concept.concept_id in selected_ids:
            continue

        selected.append(concept)
        selected_ids.add(
            concept.concept_id
        )

    return selected


# =========================================================
# FAILURE CONTEXT
# =========================================================

def build_failure_context(
    concepts: Sequence[CreativeConcept],
    limit: int = 4,
) -> str:
    ranked = rank_concepts(
        concepts
    )

    payload = []

    for concept in ranked[:limit]:
        payload.append(
            {
                "id":
                    concept.concept_id,
                "title":
                    concept.title,
                "idea":
                    clean_text(
                        concept.core_idea,
                        500,
                    ),
                "metaphor":
                    clean_text(
                        concept.visual_metaphor,
                        400,
                    ),
                "score":
                    concept.weighted_score,
                "scores":
                    concept.scores,
                "target_failures":
                    concept.debate.get(
                        "target_gate_failures",
                        [],
                    ),
                "release_failures":
                    concept.debate.get(
                        "adaptive_release_failures",
                        [],
                    ),
                "revision_instruction":
                    clean_text(
                        concept.debate.get(
                            "revision_instruction",
                            "",
                        ),
                        500,
                    ),
            }
        )

    return compact_json_for_prompt(
        payload,
        4800,
    )


# =========================================================
# RECOVERY BOARD
# =========================================================

def build_recovery_prompt(
    *,
    user_request: str,
    failed_concepts: Sequence[CreativeConcept],
    brand_context: Any,
    visual_references: Any,
) -> str:
    failure_context = build_failure_context(
        failed_concepts,
        limit=4,
    )

    stc_request = is_stc_bank_request(
        user_request
    )

    metaphor_seed = (
        {
            "family":
                "STC Bank dedicated visual system",
            "directions":
                [],
        }
        if stc_request
        else
        get_metaphor_seed(
            user_request
        )
    )

    stc_skill = (
        STC_BANK_VISUAL_SKILL
        if stc_request
        else ""
    )

    return f"""
{stc_skill}

You are XPAND Masterpiece Recovery Board.

The first professionally reviewed shortlist did not pass
the desired Masterpiece target.

This is the ONLY automatic quality-recovery round.

Do not expose chain-of-thought.
Do not make cosmetic rewrites.
Change the visual mechanism materially.

ORIGINAL REQUEST:
{clean_text(user_request, 4500)}

FAILED DIRECTIONS:
{failure_context}

BRAND:
{compact_brand_context(brand_context, 2600)}

VISUAL REFERENCES:
{compact_visual_references(visual_references, 2200)}

BENEFIT FAMILY:
{metaphor_seed["family"]}

Create exactly THREE stronger concepts.

Return exactly THREE concepts and exactly THREE evaluations.

Return JSON only:

{{
  "concepts": [
    {{
      "concept_id": "RC01",
      "category": "",
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
  ],

  "evaluations": [
    {{
      "concept_id": "RC01",

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
        "approved": true,
        "verdict": ""
      }},

      "brand_guardian": {{
        "approved": true,
        "verdict": ""
      }},

      "production_expert": {{
        "approved": true,
        "verdict": ""
      }},

      "harsh_critic": {{
        "approved": true,
        "verdict": ""
      }},

      "camera_review": {{
        "current_camera_valid": true,
        "recommended_camera_angle": "",
        "recommended_lens": "",
        "perspective": "",
        "reason": ""
      }},

      "feasibility": {{
        "feasible_in_single_image": true,
        "complexity_level": "",
        "recommended_production": "",
        "split_required": false,
        "recommended_passes": [],
        "feasibility_notes": ""
      }},

      "revision_required": false,
      "revision_instruction": ""
    }}
  ]
}}
""".strip()


def run_recovery_board(
    *,
    user_request: str,
    failed_concepts: Sequence[CreativeConcept],
    brand_context: Any,
    visual_references: Any,
    telemetry: Optional[Dict[str, Any]] = None,
) -> List[CreativeConcept]:
    prompt = build_recovery_prompt(
        user_request=user_request,
        failed_concepts=failed_concepts,
        brand_context=brand_context,
        visual_references=visual_references,
    )

    register_model_call(
        telemetry,
        "masterpiece_recovery",
    )

    raw = call_openai_director(
        prompt,
        json_mode=True,
    )

    payload = extract_json_object(
        raw
    )

    concepts = parse_concepts(
        payload,
        generation_round=2,
    )[:3]

    if not concepts:
        return []

    # Preserve original model IDs BEFORE adding R2 prefix.
    original_ids = [
        concept.concept_id
        for concept in concepts
    ]

    if is_stc_bank_request(
        user_request
    ):
        for concept in concepts:
            violations = stc_concept_violations(
                concept
            )

            if violations:
                concept.debate[
                    "stc_hard_rejection"
                ] = violations

                concept.cliche_hits.extend(
                    {
                        "id":
                            "stc_visual_violation",
                        "reason":
                            "STC visual rule: "
                            + marker,
                    }
                    for marker in violations
                )

    evaluations = _evaluation_items(
        payload
    )

    evaluation_map: Dict[
        str,
        Dict[str, Any]
    ] = {}

    for item in evaluations:
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

    for index, concept in enumerate(
        concepts
    ):
        original_id = (
            original_ids[index]
            if index < len(
                original_ids
            )
            else ""
        )

        evaluation = (
            evaluation_map.get(
                original_id
            )
        )

        if (
            evaluation is None
            and
            index < len(evaluations)
            and
            isinstance(
                evaluations[index],
                dict,
            )
        ):
            evaluation = evaluations[index]

        if isinstance(
            evaluation,
            dict,
        ):
            apply_evaluation(
                concept,
                evaluation,
            )

            camera_review = safe_dict(
                concept.debate.get(
                    "camera_review"
                )
            )

            if camera_review:
                concept.debate[
                    "camera_director"
                ] = {
                    "camera_angle":
                        camera_review.get(
                            "recommended_camera_angle",
                            concept.camera_angle,
                        ),
                    "lens":
                        camera_review.get(
                            "recommended_lens",
                            concept.lens,
                        ),
                    "perspective_type":
                        camera_review.get(
                            "perspective",
                            concept.perspective,
                        ),
                    "creative_reason":
                        camera_review.get(
                            "reason",
                            "",
                        ),
                    "camera_lock_instruction":
                        (
                            "Preserve this camera "
                            "strategy during production."
                        ),
                }

    assign_round_ids(
        concepts,
        2,
    )

    return concepts


# =========================================================
# WINNER FINALIZATION
# =========================================================

def build_winner_finalization_prompt(
    *,
    user_request: str,
    winner: CreativeConcept,
    brand_context: Any,
    visual_references: Any,
) -> str:
    stc_skill = (
        STC_BANK_VISUAL_SKILL
        if is_stc_bank_request(
            user_request
        )
        else ""
    )

    return f"""
{stc_skill}

You are XPAND Final Creative Production Director.

The concept below is already selected.
Do not invent a new campaign idea.
Do not expose chain-of-thought.

REQUEST:
{clean_text(user_request, 4000)}

WINNER:
{compact_json_for_prompt(
    concept_payload_for_evaluation(winner),
    5500
)}

MODEL REVIEW:
{compact_json_for_prompt(
    winner.debate,
    3000
)}

BRAND:
{compact_brand_context(
    brand_context,
    2200
)}

VISUAL REFERENCES:
{compact_visual_references(
    visual_references,
    1800
)}

Lock:
- camera
- lens
- camera distance
- horizon
- perspective
- depth
- composition hierarchy
- negative space
- lighting
- material logic
- brand color behavior
- production feasibility

Return JSON only:

{{
  "camera_director": {{
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
  }},

  "feasibility": {{
    "feasible": true,
    "complexity_level": "",
    "recommended_strategy": "",
    "passes": [],
    "single_image_risks": [],
    "product_lock_risks": [],
    "final_recommendation": ""
  }},

  "production_blueprint": {{
    "composition": "",
    "negative_space": "",
    "lighting": "",
    "materials": "",
    "brand_execution": "",
    "human_direction": "",
    "do_not_change": []
  }}
}}
""".strip()


def finalize_winner(
    *,
    user_request: str,
    winner: CreativeConcept,
    brand_context: Any,
    visual_references: Any,
    telemetry: Optional[Dict[str, Any]] = None,
) -> None:
    register_model_call(
        telemetry,
        "winner_finalizer",
    )

    raw = call_openai_director(
        build_winner_finalization_prompt(
            user_request=user_request,
            winner=winner,
            brand_context=brand_context,
            visual_references=visual_references,
        ),
        json_mode=True,
    )

    payload = extract_json_object(
        raw
    )

    camera = safe_dict(
        payload.get(
            "camera_director"
        )
    )

    feasibility = safe_dict(
        payload.get(
            "feasibility"
        )
    )

    blueprint = safe_dict(
        payload.get(
            "production_blueprint"
        )
    )

    if camera:
        winner.debate[
            "camera_director"
        ] = camera

        camera_angle = clean_text(
            camera.get(
                "camera_angle"
            ),
            500,
        )

        lens = clean_text(
            camera.get(
                "lens"
            ),
            200,
        )

        perspective = clean_text(
            camera.get(
                "perspective_type"
            ),
            700,
        )

        if camera_angle:
            winner.camera_angle = camera_angle

        if lens:
            winner.lens = lens

        if perspective:
            winner.perspective = (
                perspective
            )

    if feasibility:
        winner.feasibility.update(
            feasibility
        )

    if blueprint:
        winner.debate[
            "production_blueprint"
        ] = blueprint


# =========================================================
# CAMERA COMPATIBILITY
# =========================================================

def build_camera_director_prompt(
    *,
    user_request: str,
    concept: CreativeConcept,
    visual_references: Any = None,
) -> str:
    return f"""
You are XPAND Camera Angle Director.

Do not redesign the approved concept.

REQUEST:
{clean_text(user_request, 4000)}

CONCEPT:
{compact_json_for_prompt(
    concept_payload_for_evaluation(concept),
    5000
)}

REFERENCES:
{compact_visual_references(
    visual_references,
    2000
)}

CAMERAS:
{compact_json_for_prompt(
    CAMERA_LIBRARY,
    3500
)}

LENSES:
{compact_json_for_prompt(
    LENS_LIBRARY,
    1600
)}

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
    visual_references: Any = None,
) -> Dict[str, Any]:
    raw = call_openai_director(
        build_camera_director_prompt(
            user_request=user_request,
            concept=concept,
            visual_references=visual_references,
        ),
        json_mode=True,
    )

    return extract_json_object(
        raw
    )


# =========================================================
# FEASIBILITY COMPATIBILITY
# =========================================================

def build_feasibility_prompt(
    *,
    user_request: str,
    concept: CreativeConcept,
    visual_references: Any = None,
) -> str:
    return f"""
You are XPAND Production Feasibility Expert.

Do not redesign the concept unless technically necessary.

REQUEST:
{clean_text(user_request, 4000)}

CONCEPT:
{compact_json_for_prompt(
    concept_payload_for_evaluation(concept),
    5200
)}

REFERENCES:
{compact_visual_references(
    visual_references,
    2200
)}

Return JSON only:

{{
  "feasible": true,
  "complexity_level": "",
  "recommended_strategy": "",
  "passes": [],
  "single_image_risks": [],
  "product_lock_risks": [],
  "final_recommendation": ""
}}
""".strip()


def check_scene_feasibility(
    *,
    user_request: str,
    concept: CreativeConcept,
    visual_references: Any = None,
) -> Dict[str, Any]:
    raw = call_openai_director(
        build_feasibility_prompt(
            user_request=user_request,
            concept=concept,
            visual_references=visual_references,
        ),
        json_mode=True,
    )

    return extract_json_object(
        raw
    )


# =========================================================
# LEGACY REVISION COMPATIBILITY
# =========================================================

def build_revision_prompt(
    *,
    user_request: str,
    concept: CreativeConcept,
    brand_context: Any = None,
    visual_references: Any = None,
) -> str:
    return f"""
You are XPAND Senior Creative Director.

Improve this concept materially.

REQUEST:
{clean_text(user_request, 4000)}

CURRENT CONCEPT:
{compact_json_for_prompt(
    concept_payload_for_evaluation(concept),
    5000
)}

BRAND:
{compact_brand_context(
    brand_context,
    2200
)}

REFERENCES:
{compact_visual_references(
    visual_references,
    1800
)}

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
    visual_references: Any = None,
) -> Optional[CreativeConcept]:
    raw = call_openai_director(
        build_revision_prompt(
            user_request=user_request,
            concept=concept,
            brand_context=brand_context,
            visual_references=visual_references,
        ),
        json_mode=True,
    )

    payload = extract_json_object(
        raw
    )

    # Support a bare revised concept or {"concept": {...}}
    item = payload

    if isinstance(
        payload.get(
            "concept"
        ),
        dict,
    ):
        item = payload["concept"]

    revised = concept_from_dict(
        item,
        fallback_id=(
            concept.concept_id
            +
            "-REV"
        ),
        generation_round=(
            concept.generation_round
        ),
        revised_from=(
            concept.concept_id
        ),
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


def select_revision_candidates(
    concepts: Sequence[CreativeConcept],
) -> List[CreativeConcept]:
    candidates = [
        item
        for item in concepts
        if (
            item.evaluation_valid
            and
            item.weighted_score
            >=
            MASTERPIECE_REVISION_FLOOR
        )
    ]

    return rank_concepts(
        candidates
    )[
        :MASTERPIECE_REVISION_CANDIDATES
    ]


# =========================================================
# BEST AVAILABLE RELEASE
# =========================================================

def best_real_evaluated_concept(
    concepts: Sequence[CreativeConcept],
) -> Optional[CreativeConcept]:
    clean_valid = [
        item
        for item in concepts
        if (
            item.evaluation_valid
            and
            not item.cliche_hits
        )
    ]

    if clean_valid:
        return rank_concepts(
            clean_valid
        )[0]

    valid = [
        item
        for item in concepts
        if item.evaluation_valid
    ]

    if valid:
        return rank_concepts(
            valid
        )[0]

    return None


def release_best_available(
    concept: CreativeConcept,
) -> None:
    concept.quality_gate_passed = True

    concept.debate[
        "quality_release_level"
    ] = "best_available_release"

    concept.debate[
        "target_gate_passed"
    ] = False

    concept.debate[
        "best_available_policy"
    ] = (
        "Real model evaluation preserved. "
        "Masterpiece target was not reached after recovery, "
        "but production may continue with the strongest "
        "real-evaluated concept."
    )

    concept.quality_gate_failures = []


# =========================================================
# ROUND SUMMARY
# =========================================================

def build_round_summary(
    *,
    round_number: int,
    concepts: Sequence[CreativeConcept],
    qualified: Sequence[CreativeConcept],
    revisions: int,
) -> Dict[str, Any]:
    valid = [
        item
        for item in concepts
        if item.evaluation_valid
    ]

    best = (
        rank_concepts(valid)[0]
        if valid
        else None
    )

    return {
        "round":
            round_number,
        "concepts":
            len(concepts),
        "valid_evaluations":
            len(valid),
        "qualified":
            len(qualified),
        "best_score":
            (
                best.weighted_score
                if best
                else None
            ),
        "best_id":
            (
                best.concept_id
                if best
                else ""
            ),
        "revisions_generated":
            revisions,
    }


def enrich_winner(
    *,
    user_request: str,
    winner: CreativeConcept,
    visual_references: Any,
    errors: List[str],
    brand_context: Any = None,
    telemetry: Optional[Dict[str, Any]] = None,
) -> None:
    try:
        finalize_winner(
            user_request=user_request,
            winner=winner,
            brand_context=brand_context,
            visual_references=visual_references,
            telemetry=telemetry,
        )

    except Exception as error:
        errors.append(
            "winner_finalizer: "
            +
            clean_text(
                error,
                2500,
            )
        )


# =========================================================
# TECHNICAL FAILURE RESPONSE
# =========================================================

def _technical_failure_response(
    *,
    mode: str,
    user_request: str,
    errors: List[str],
    telemetry: Dict[str, Any],
    stage: str,
    reason: str,
) -> CreativeBrainResponse:
    """
    IMPORTANT:

    A parser/model/transport failure is NOT a creative-quality
    failure because no quality evaluation happened.

    Integration code can use:
      technical_failure
      quality_gate_evaluated
      allow_smart_engine_fallback
      fallback_blocked
    """

    return CreativeBrainResponse(
        ok=False,
        mode=mode,
        request=user_request,
        total_concepts=0,
        concepts=[],
        top_concepts=[],
        winner=None,
        metadata={
            "version":
                VERSION,

            "architecture":
                "quality_first_adaptive",

            "technical_failure":
                True,

            "failure_stage":
                stage,

            "failure_reason":
                reason,

            "quality_gate_evaluated":
                False,

            "quality_gate_passed":
                False,

            "creative_score_available":
                False,

            "masterpiece_min_score":
                MASTERPIECE_MIN_SCORE,

            "masterpiece_target_score":
                MASTERPIECE_MIN_SCORE,

            "masterpiece_release_floor":
                MASTERPIECE_RELEASE_FLOOR,

            # Integration must NOT interpret this technical
            # state as "creative quality failed".
            "quality_target_blocks_production":
                False,

            "allow_smart_engine_fallback":
                True,

            "fallback_recommended":
                True,

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

            "ideation_debug":
                telemetry.get(
                    "ideation_debug",
                    [],
                ),
        },
        errors=errors,
    )


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
        mode = MODE_MASTERPIECE

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

    errors: List[str] = []

    telemetry: Dict[str, Any] = {
        "director_calls":
            0,

        "director_call_history":
            [],

        "initial_concepts":
            0,

        "challenger_concepts":
            0,

        "shortlisted_concepts":
            0,

        "recovery_used":
            False,

        "compact_ideation_recovery_used":
            False,

        "ideation_debug":
            [],
    }

    all_concepts: List[
        CreativeConcept
    ] = []

    round_summaries: List[
        Dict[str, Any]
    ] = []

    winner: Optional[
        CreativeConcept
    ] = None

    release_level = ""

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND CREATIVE BRAIN V2.0"
    )
    print(
        " QUALITY-FIRST ADAPTIVE"
    )
    print(
        " VERSION",
        VERSION,
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
            sum(
                MASTERPIECE_DISTRIBUTION.values()
            )
            if mode == MODE_MASTERPIECE
            else
            sum(
                FAST_DISTRIBUTION.values()
            )
        ),
    )
    print(
        "Paid review shortlist:",
        MASTERPIECE_SHORTLIST_SIZE,
    )
    print(
        "Target Director calls:",
        MASTERPIECE_TARGET_DIRECTOR_CALLS,
    )
    print(
        "Benefit family:",
        infer_benefit_family(
            user_request
        ),
    )
    print("")

    # =====================================================
    # INITIAL IDEATION
    # =====================================================

    try:
        concepts = generate_concept_pool(
            user_request=user_request,
            brand_context=brand_context,
            visual_references=visual_references,
            style_hint=style_hint,
            mode=mode,
            round_number=1,
            telemetry=telemetry,
        )

    except Exception as error:
        primary_error = clean_text(
            error,
            3500,
        )

        errors.append(
            "concept_generation: "
            +
            primary_error
        )

        print(
            "⚠️ Primary ideation unavailable:",
            primary_error,
        )

        print(
            "🔁 Running REAL compact ideation recovery..."
        )

        telemetry[
            "compact_ideation_recovery_used"
        ] = True

        try:
            concepts = generate_concept_pool(
                user_request=user_request,
                brand_context=brand_context,
                visual_references=visual_references,
                style_hint=style_hint,
                mode=MODE_FAST,
                round_number=1,
                failure_context=(
                    "The previous full ideation response failed. "
                    "Failure detail: "
                    +
                    clean_text(
                        primary_error,
                        1200,
                    )
                    +
                    ". Generate a compact strict-JSON batch. "
                    "Prioritize valid JSON syntax and complete "
                    "objects over long prose."
                ),
                telemetry=telemetry,
            )

            print(
                "✅ Compact ideation recovery:",
                len(concepts),
            )

        except Exception as recovery_error:
            recovery_text = clean_text(
                recovery_error,
                3500,
            )

            errors.append(
                "compact_ideation_recovery: "
                +
                recovery_text
            )

            print(
                "❌ Compact ideation recovery failed:",
                recovery_text,
            )

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
            print("")

            return _technical_failure_response(
                mode=mode,
                user_request=user_request,
                errors=errors,
                telemetry=telemetry,
                stage="ideation",
                reason=(
                    "ideation_unavailable_after_compact_recovery"
                ),
            )

    concepts = deduplicate_concepts(
        concepts
    )

    all_concepts.extend(
        concepts
    )

    telemetry[
        "initial_concepts"
    ] = len(concepts)

    print(
        "✅ Initial concepts:",
        len(concepts),
    )

    # =====================================================
    # CHALLENGER POOL
    # =====================================================

    if (
        mode == MODE_MASTERPIECE
        and
        MASTERPIECE_MAX_IDEATION_ROUNDS >= 2
    ):
        print("")
        print(
            "⚔️ Running independent Challenger ideation board..."
        )

        try:
            challenger_concepts = generate_concept_pool(
                user_request=user_request,
                brand_context=brand_context,
                visual_references=visual_references,
                style_hint=style_hint,
                mode=mode,
                round_number=2,
                failure_context=(
                    "Create a radically different independent pool. "
                    "Do not repeat the first pool's likely visual grammar. "
                    "Prioritize premium photographic realism, "
                    "clear commercial communication, one dominant hero, "
                    "natural brand behavior and unusual but defensible camera."
                ),
                challenger=True,
                telemetry=telemetry,
            )

            challenger_concepts = (
                deduplicate_concepts(
                    challenger_concepts,
                    all_concepts,
                )
            )

            telemetry[
                "challenger_concepts"
            ] = len(
                challenger_concepts
            )

            concepts.extend(
                challenger_concepts
            )

            all_concepts.extend(
                challenger_concepts
            )

            print(
                "✅ Challenger concepts:",
                len(challenger_concepts),
                "| combined pool:",
                len(concepts),
            )

        except Exception as error:
            errors.append(
                "challenger_ideation: "
                +
                clean_text(
                    error,
                    3000,
                )
            )

            print(
                "⚠️ Challenger ideation unavailable; "
                "continuing with primary pool."
            )

    # =====================================================
    # LOCAL SHORTLIST
    # =====================================================

    shortlist_limit = (
        MASTERPIECE_SHORTLIST_SIZE
        if mode == MODE_MASTERPIECE
        else
        min(
            6,
            len(concepts),
        )
    )

    shortlist = shortlist_concepts(
        concepts,
        limit=shortlist_limit,
    )

    telemetry[
        "shortlisted_concepts"
    ] = len(shortlist)

    print(
        "✅ FREE local shortlist:",
        str(len(shortlist))
        +
        "/"
        +
        str(len(concepts)),
    )

    # =====================================================
    # REVIEW
    # =====================================================

    evaluate_concept_pool(
        user_request=user_request,
        concepts=shortlist,
        brand_context=brand_context,
        visual_references=visual_references,
        mode=mode,
        telemetry=telemetry,
    )

    valid_review_count = sum(
        1
        for concept in shortlist
        if concept.evaluation_valid
    )

    if (
        mode == MODE_MASTERPIECE
        and
        valid_review_count == 0
    ):
        errors.append(
            "creative_review: no valid model evaluations received"
        )

        print(
            "⚠️ No valid Review Board evaluations received."
        )

    refresh_quality_gates(
        shortlist,
        mode=mode,
    )

    released = select_top_concepts(
        shortlist,
        limit=top_count,
        mode=mode,
        qualified_only=True,
    )

    if released:
        winner = released[0]

        release_level = clean_text(
            winner.debate.get(
                "quality_release_level",
                "target_82_plus",
            ),
            100,
        )

        print(
            "🏆 CREATIVE RELEASE"
            + " | "
            + winner.concept_id
            + " | score="
            + str(
                winner.weighted_score
            )
            + " | level="
            + release_level
        )

        round_summaries.append(
            build_round_summary(
                round_number=1,
                concepts=shortlist,
                qualified=released,
                revisions=0,
            )
        )

    # =====================================================
    # QUALITY RECOVERY
    # =====================================================

    recovery_concepts: List[
        CreativeConcept
    ] = []

    if (
        mode == MODE_MASTERPIECE
        and
        winner is None
        and
        valid_review_count > 0
    ):
        telemetry[
            "recovery_used"
        ] = True

        print("")
        print(
            "🧠 Masterpiece target/release gate not reached."
        )
        print(
            "🔁 Running ONE consolidated Recovery Board..."
        )

        try:
            recovery_concepts = run_recovery_board(
                user_request=user_request,
                failed_concepts=shortlist,
                brand_context=brand_context,
                visual_references=visual_references,
                telemetry=telemetry,
            )

        except Exception as error:
            errors.append(
                "masterpiece_recovery: "
                +
                clean_text(
                    error,
                    3000,
                )
            )

            recovery_concepts = []

        recovery_concepts = deduplicate_concepts(
            recovery_concepts,
            all_concepts,
        )

        all_concepts.extend(
            recovery_concepts
        )

        refresh_quality_gates(
            recovery_concepts,
            mode=MODE_MASTERPIECE,
        )

        recovery_released = select_top_concepts(
            recovery_concepts,
            limit=top_count,
            mode=MODE_MASTERPIECE,
            qualified_only=True,
        )

        if recovery_released:
            winner = recovery_released[0]
            released = recovery_released

            release_level = clean_text(
                winner.debate.get(
                    "quality_release_level",
                    "adaptive_release",
                ),
                100,
            )

            print(
                "🏆 RECOVERY WINNER"
                + " | "
                + winner.concept_id
                + " | score="
                + str(
                    winner.weighted_score
                )
                + " | level="
                + release_level
            )

        round_summaries.append(
            build_round_summary(
                round_number=2,
                concepts=recovery_concepts,
                qualified=recovery_released,
                revisions=len(
                    recovery_concepts
                ),
            )
        )

    # =====================================================
    # BEST REAL-EVALUATED RELEASE
    # =====================================================

    if (
        mode == MODE_MASTERPIECE
        and
        winner is None
    ):
        best_available = (
            best_real_evaluated_concept(
                all_concepts
            )
        )

        if best_available is not None:
            winner = best_available

            release_best_available(
                winner
            )

            released = [
                winner
            ]

            release_level = (
                "best_available_release"
            )

            print(
                "⚠️ Masterpiece target "
                +
                str(
                    MASTERPIECE_MIN_SCORE
                )
                +
                " not reached."
            )

            print(
                "✅ Continuing with strongest REAL-EVALUATED concept"
                + " | "
                + winner.concept_id
                + " | score="
                + str(
                    winner.weighted_score
                )
            )

    # =====================================================
    # FAST BEST AVAILABLE
    # =====================================================

    if (
        mode == MODE_FAST
        and
        winner is None
    ):
        ranked = rank_concepts(
            shortlist
        )

        if ranked:
            winner = ranked[0]

            winner.quality_gate_passed = (
                True
            )

            winner.quality_gate_failures = []

            winner.debate[
                "quality_release_level"
            ] = "fast_best_available"

            released = [
                winner
            ]

            release_level = (
                "fast_best_available"
            )

    # =====================================================
    # FINALIZER
    # =====================================================

    if (
        winner is not None
        and
        not telemetry[
            "recovery_used"
        ]
    ):
        try:
            finalize_winner(
                user_request=user_request,
                winner=winner,
                brand_context=brand_context,
                visual_references=visual_references,
                telemetry=telemetry,
            )

        except Exception as error:
            errors.append(
                "winner_finalizer: "
                +
                clean_text(
                    error,
                    3000,
                )
            )

            # Winner already has Review Board camera data.
            camera_review = safe_dict(
                winner.debate.get(
                    "camera_review"
                )
            )

            if camera_review:
                winner.debate[
                    "camera_director"
                ] = {
                    "camera_angle":
                        camera_review.get(
                            "recommended_camera_angle",
                            winner.camera_angle,
                        ),
                    "lens":
                        camera_review.get(
                            "recommended_lens",
                            winner.lens,
                        ),
                    "perspective_type":
                        camera_review.get(
                            "perspective",
                            winner.perspective,
                        ),
                    "creative_reason":
                        camera_review.get(
                            "reason",
                            "",
                        ),
                }

    # =====================================================
    # FINAL TOP CONCEPTS
    # =====================================================

    if winner is not None:
        winner.quality_gate_passed = True

    qualified_top = [
        item
        for item in rank_concepts(
            all_concepts
        )
        if item.quality_gate_passed
    ]

    if winner is not None:
        top_concepts = [
            winner
        ]

        for concept in qualified_top:
            if len(
                top_concepts
            ) >= top_count:
                break

            if (
                concept.concept_id
                ==
                winner.concept_id
            ):
                continue

            top_concepts.append(
                concept
            )

    else:
        top_concepts = select_top_concepts(
            all_concepts,
            limit=top_count,
            mode=mode,
            qualified_only=False,
        )

    quality_gate_passed = bool(
        winner
    )

    # =====================================================
    # NO WINNER / TECHNICAL REVIEW FAILURE
    # =====================================================

    if (
        winner is None
        and
        valid_review_count == 0
    ):
        print("")
        print(
            "=========================================="
        )
        print(
            " REVIEW TECHNICAL FAILURE"
        )
        print(
            "=========================================="
        )
        print(
            "No real evaluation was obtained."
        )
        print(
            "This is NOT classified as creative-quality failure."
        )

        return CreativeBrainResponse(
            ok=False,
            mode=mode,
            request=user_request,
            total_concepts=len(
                all_concepts
            ),
            concepts=all_concepts,
            top_concepts=top_concepts,
            winner=None,
            metadata={
                "version":
                    VERSION,

                "architecture":
                    "quality_first_adaptive",

                "technical_failure":
                    True,

                "failure_stage":
                    "creative_review",

                "failure_reason":
                    "no_valid_model_evaluation",

                "quality_gate_evaluated":
                    False,

                "quality_gate_passed":
                    False,

                "quality_target_blocks_production":
                    False,

                "allow_smart_engine_fallback":
                    True,

                "fallback_recommended":
                    True,

                "fallback_blocked":
                    False,

                "masterpiece_min_score":
                    MASTERPIECE_MIN_SCORE,

                "masterpiece_target_score":
                    MASTERPIECE_MIN_SCORE,

                "director_calls":
                    telemetry[
                        "director_calls"
                    ],

                "director_call_history":
                    telemetry[
                        "director_call_history"
                    ],

                "ideation_debug":
                    telemetry[
                        "ideation_debug"
                    ],
            },
            errors=errors,
        )

    # =====================================================
    # EFFECTIVE INTEGRATION FLOOR
    # =====================================================

    effective_integration_floor = (
        MASTERPIECE_MIN_SCORE
    )

    if winner is not None:
        if (
            release_level
            ==
            "adaptive_release"
        ):
            effective_integration_floor = min(
                MASTERPIECE_RELEASE_FLOOR,
                winner.weighted_score,
            )

        elif (
            release_level
            ==
            "best_available_release"
        ):
            effective_integration_floor = (
                winner.weighted_score
            )

        elif mode == MODE_FAST:
            effective_integration_floor = min(
                FAST_MIN_SCORE,
                winner.weighted_score,
            )

    # =====================================================
    # FINAL LOG
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
            "Score:",
            winner.weighted_score,
        )
        print(
            "Masterpiece target reached:",
            (
                winner.weighted_score
                >=
                MASTERPIECE_MIN_SCORE
            ),
        )
        print(
            "Release level:",
            release_level,
        )
        print(
            "Director calls:",
            telemetry[
                "director_calls"
            ],
        )
        print(
            "Call path:",
            " → ".join(
                telemetry[
                    "director_call_history"
                ]
            ),
        )

    print("")

    return CreativeBrainResponse(
        ok=quality_gate_passed,
        mode=mode,
        request=user_request,
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
                "quality_first_adaptive",

            "distribution":
                (
                    FAST_DISTRIBUTION
                    if mode == MODE_FAST
                    else
                    MASTERPIECE_DISTRIBUTION
                ),

            "challenger_distribution":
                CHALLENGER_DISTRIBUTION,

            "recovery_distribution":
                RECOVERY_DISTRIBUTION,

            "benefit_family":
                infer_benefit_family(
                    user_request
                ),

            "score_weights":
                SCORE_WEIGHTS,

            "masterpiece_min_score":
                effective_integration_floor,

            "masterpiece_target_score":
                MASTERPIECE_MIN_SCORE,

            "masterpiece_release_floor":
                MASTERPIECE_RELEASE_FLOOR,

            "masterpiece_min_subscores":
                MASTERPIECE_MIN_SUBSCORES,

            "masterpiece_release_min_subscores":
                MASTERPIECE_RELEASE_MIN_SUBSCORES,

            "masterpiece_max_rounds":
                MASTERPIECE_MAX_IDEATION_ROUNDS,

            "evaluation_batch_size":
                EVALUATION_BATCH_SIZE,

            "evaluation_retries":
                EVALUATION_RETRIES,

            "initial_concepts":
                telemetry[
                    "initial_concepts"
                ],

            "challenger_concepts":
                telemetry[
                    "challenger_concepts"
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

            "recovery_used":
                telemetry[
                    "recovery_used"
                ],

            "compact_ideation_recovery_used":
                telemetry[
                    "compact_ideation_recovery_used"
                ],

            "release_level":
                release_level,

            "target_quality_gate_passed":
                bool(
                    winner
                    and
                    winner.weighted_score
                    >=
                    MASTERPIECE_MIN_SCORE
                ),

            "quality_gate_enabled":
                (
                    mode
                    ==
                    MODE_MASTERPIECE
                ),

            "quality_gate_evaluated":
                True,

            "quality_gate_passed":
                quality_gate_passed,

            "technical_failure":
                False,

            "quality_target_blocks_production":
                False,

            "allow_smart_engine_fallback":
                False,

            "fallback_recommended":
                False,

            "fallback_blocked":
                False,

            "fake_fallback_winner_allowed":
                False,

            "real_model_evaluation_required":
                True,

            "anti_cliche_enabled":
                True,

            "visual_metaphor_enabled":
                True,

            "creative_debate_enabled":
                True,

            "brand_guardian_enabled":
                True,

            "production_expert_enabled":
                True,

            "harsh_critic_enabled":
                True,

            "camera_director_enabled":
                True,

            "scene_feasibility_enabled":
                True,

            "local_shortlist_enabled":
                True,

            "automatic_revision_enabled":
                False,

            "automatic_reideation_enabled":
                (
                    mode
                    ==
                    MODE_MASTERPIECE
                ),

            "single_recovery_policy":
                True,

            "ideation_debug":
                telemetry[
                    "ideation_debug"
                ],

            "rounds":
                round_summaries,
        },
        errors=errors,
    )


# =========================================================
# SERIALIZERS
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
            concept_to_dict(item)
            for item in response.concepts
        ],

        "top_concepts": [
            concept_to_dict(item)
            for item in response.top_concepts
        ],

        "winner":
            (
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
# HUMAN SUMMARY
# =========================================================

def build_top_concepts_summary(
    response: CreativeBrainResponse,
) -> str:
    if not response.top_concepts:
        failure_reason = clean_text(
            response.metadata.get(
                "failure_reason",
                "",
            ),
            300,
        )

        if response.metadata.get(
            "technical_failure"
        ):
            return (
                "تعذر الحصول على مخرجات إبداعية بسبب "
                "مشكلة تقنية في مسار النموذج"
                +
                (
                    ": "
                    + failure_reason
                    if failure_reason
                    else "."
                )
            )

        return (
            "ما طلعت اتجاهات إبداعية كافية."
        )

    lines: List[str] = []

    lines.append(
        "XPAND Creative Brain | "
        +
        response.mode.upper()
    )

    lines.append(
        "تم تطوير "
        +
        str(
            response.total_concepts
        )
        +
        " اتجاه إبداعي."
    )

    if (
        response.mode
        ==
        MODE_MASTERPIECE
    ):
        lines.append(
            "Creative target: "
            +
            str(
                response.metadata.get(
                    "masterpiece_target_score",
                    MASTERPIECE_MIN_SCORE,
                )
            )
            +
            "+"
        )

        lines.append(
            "Release: "
            +
            clean_text(
                response.metadata.get(
                    "release_level",
                    "",
                ),
                100,
            )
        )

    lines.append("")

    for index, concept in enumerate(
        response.top_concepts,
        start=1,
    ):
        lines.append(
            str(index)
            +
            ") "
            +
            concept.title
        )

        lines.append(
            "الفكرة: "
            +
            concept.core_idea
        )

        lines.append(
            "الزاوية: "
            +
            concept.camera_angle
            +
            (
                " | "
                +
                concept.lens
                if concept.lens
                else ""
            )
        )

        lines.append(
            "التقييم: "
            +
            str(
                concept.weighted_score
            )
            +
            "/100"
        )

        lines.append("")

    return "\n".join(
        lines
    ).strip()


# =========================================================
# ZERO-API SELF TEST
# =========================================================

if __name__ == "__main__":
    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND CREATIVE BRAIN SELF TEST"
    )
    print(
        " VERSION",
        VERSION,
    )
    print(
        "=========================================="
    )

    # -----------------------------------------------------
    # 1. Score weights
    # -----------------------------------------------------

    weights_ok = (
        sum(
            SCORE_WEIGHTS.values()
        )
        ==
        100
    )

    print(
        "✅"
        if weights_ok
        else "❌",
        "Score weights",
    )

    # -----------------------------------------------------
    # 2. Merchant routing
    # -----------------------------------------------------

    merchant_family = infer_benefit_family(
        "خدمات التجارة الإلكترونية ونقاط البيع"
    )

    merchant_ok = (
        merchant_family
        ==
        "merchant_payments"
    )

    print(
        "✅"
        if merchant_ok
        else "❌",
        "Merchant payments routing:",
        merchant_family,
    )

    # -----------------------------------------------------
    # 3. Native dict parser
    # -----------------------------------------------------

    dict_payload = {
        "concepts": [
            {
                "concept_id": "C01",
                "title": "Test",
                "core_idea": "Test idea",
            }
        ]
    }

    dict_parsed = extract_json_object(
        dict_payload
    )

    dict_ok = (
        isinstance(
            dict_parsed,
            dict,
        )
        and
        len(
            _extract_concept_items(
                dict_parsed
            )
        )
        ==
        1
    )

    print(
        "✅"
        if dict_ok
        else "❌",
        "Native dict model-response parsing",
    )

    # -----------------------------------------------------
    # 4. Bare list parser
    # -----------------------------------------------------

    list_payload = [
        {
            "concept_id": "C01",
            "title": "Test",
            "core_idea": "Test idea",
        }
    ]

    list_parsed = extract_json_object(
        list_payload
    )

    list_ok = (
        len(
            _extract_concept_items(
                list_parsed
            )
        )
        ==
        1
    )

    print(
        "✅"
        if list_ok
        else "❌",
        "Bare list model-response parsing",
    )

    # -----------------------------------------------------
    # 5. Fenced JSON parser
    # -----------------------------------------------------

    fenced = """```json
{
  "concepts": [
    {
      "concept_id": "C01",
      "title": "Test",
      "core_idea": "Test idea"
    }
  ]
}
```"""

    fenced_parsed = extract_json_object(
        fenced
    )

    fenced_ok = (
        len(
            _extract_concept_items(
                fenced_parsed
            )
        )
        ==
        1
    )

    print(
        "✅"
        if fenced_ok
        else "❌",
        "Fenced JSON parsing",
    )

    # -----------------------------------------------------
    # 6. Python literal parser
    # -----------------------------------------------------

    python_literal = (
        "{'concepts':["
        "{'concept_id':'C01',"
        "'title':'Test',"
        "'core_idea':'Test idea'}"
        "]}"
    )

    literal_parsed = extract_json_object(
        python_literal
    )

    literal_ok = (
        len(
            _extract_concept_items(
                literal_parsed
            )
        )
        ==
        1
    )

    print(
        "✅"
        if literal_ok
        else "❌",
        "Python-literal wrapper parsing",
    )

    # -----------------------------------------------------
    # 7. Anti cliché
    # -----------------------------------------------------

    cliche_hits = detect_cliches(
        "A floating bank card with flying coins and a globe."
    )

    cliche_ok = (
        len(cliche_hits)
        >= 3
    )

    print(
        "✅"
        if cliche_ok
        else "❌",
        "Anti-cliche detection:",
        len(cliche_hits),
    )

    # -----------------------------------------------------
    # Final
    # -----------------------------------------------------

    all_ok = all(
        [
            weights_ok,
            merchant_ok,
            dict_ok,
            list_ok,
            fenced_ok,
            literal_ok,
            cliche_ok,
        ]
    )

    print("")
    print(
        (
            "XPAND Creative Brain self-test: PASS ✅"
            if all_ok
            else
            "XPAND Creative Brain self-test: FAIL ❌"
        )
    )
    print(
        "🚫 No API calls were made"
    )
    print("")
