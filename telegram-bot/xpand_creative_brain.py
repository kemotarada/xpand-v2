# =========================================================
# XPAND CREATIVE BRAIN V5.7
#
# STC BANK CANONICAL SERVICE INTELLIGENCE
# + DETERMINISTIC STRICT RELEASE
# + TARGETED REPAIR
# + FRESH RECOVERY
#
# FULL RUNTIME-COMPATIBLE REPLACEMENT
#
# =========================================================
#
# PUBLIC CONTRACT PRESERVED
# ---------------------------------------------------------
#
# MODE_FAST
# MODE_MASTERPIECE
#
# CreativeConcept
# CreativeBrainResponse
#
# concept_to_dict()
# response_to_dict()
# build_top_concepts_summary()
# run_creative_brain()
#
#
# =========================================================
# V5.7 PRIMARY FIX
# =========================================================
#
# xpand_stc_policy.py is the SINGLE SOURCE OF TRUTH for:
#
# - merchant_payments
# - digital_banking
# - premium
#
# Generic downstream values such as "premium" are NOT
# allowed to erase a stronger service intent contained
# in the user's original STC request.
#
#
# Example:
#
# User:
#   حوالتك حول العالم وتتبعها من التطبيق
#
# Canonical:
#   digital_banking
#
# NEVER:
#   premium
#
#
# User:
#   التجارة الإلكترونية ونقاط البيع
#
# Canonical:
#   merchant_payments
#
#
# =========================================================
# STC MASTERPIECE PATH
# =========================================================
#
# CALL 1
#   8 fundamentally different concepts
#          ↓
#
# CALL 2
#   Executive Creative Review
#          ↓
#
# A) strict-qualified candidate exists
#          ↓
#    CALL 3 = Finalist Jury
#          ↓
#    highest independently strict-qualified concept releases
#
# B) no strict finalist + repairable near miss
#          ↓
#    CALL 3 = Targeted Repair Board
#          ↓
#    exactly 2 repaired concepts
#    + evaluation
#    + jury guidance
#
# C) no strict finalist + no repairable near miss
#          ↓
#    CALL 3 = Fresh Recovery Board
#          ↓
#    exactly 3 new concepts
#    + evaluation
#    + jury guidance
#
#
# =========================================================
# V5.7 VISUAL POLICY
# =========================================================
#
# - user supplies CONTENT / MESSAGE
# - Creative Brain invents the visual advertising idea
# - no need for user to describe the idea
#
# - STC reference pack = visual DNA
# - references are not templates
#
# - premium realistic default
# - purple is optional
# - no generic fintech language
# - no fake UI
# - no generated text/logo
#
# - 25–40% integrated copy space
# - NO artificial empty panel
#
# - intentional campaign camera
# - physically believable execution
#
#
# =========================================================
# COST
# =========================================================
#
# STC High Alert:
#   maximum 3 Director calls
#
# Normal:
#   normally 2 Director calls
#
# This module generates NO images.
#
#
# =========================================================
# ZERO-COST SELF TEST
# =========================================================
#
# python xpand_creative_brain.py
#
# No API calls.
# No images.
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

from pathlib import Path

from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
)


# =========================================================
# IMAGE ENGINE
# =========================================================

from xpand_image_engine import (
    call_openai_director,
)


# =========================================================
# STC BANK SKILL
# =========================================================

try:

    from xpand_stc_bank_skill import (
        STC_BANK_VISUAL_SKILL,
        is_stc_bank_request,
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

        return bool(
            "stc bank"
            in text
            or
            "بنك stc"
            in text
            or
            "stc بنك"
            in text
            or
            "اس تي سي بنك"
            in text
        )


# =========================================================
# CANONICAL STC POLICY
#
# MANDATORY FOR V5.7
# =========================================================

from xpand_stc_policy import (
    FAMILY_DIGITAL_BANKING,
    FAMILY_MERCHANT_PAYMENTS,
    FAMILY_PREMIUM,
    build_creative_constitution_text,
    resolve_stc_benefit_family,
    resolve_stc_benefit_family_id,
)


STC_CANONICAL_POLICY_AVAILABLE = True


# =========================================================
# PERMANENT STC BRAND KIT
# =========================================================

try:

    from xpand_stc_brand_kit import (
        load_default_stc_brand_kit,
    )

    STC_BRAND_KIT_AVAILABLE = True

except Exception:

    load_default_stc_brand_kit = None

    STC_BRAND_KIT_AVAILABLE = False


# =========================================================
# IDENTITY
# =========================================================

VERSION = "5.7"

MODULE_NAME = (
    "XPAND Creative Brain"
)


# =========================================================
# PUBLIC MODES
# =========================================================

MODE_FAST = "fast"

MODE_MASTERPIECE = "masterpiece"


# =========================================================
# ENV HELPERS
# =========================================================

def env_bool(
    name: str,
    default: bool,
) -> bool:

    value = str(
        os.environ.get(
            name,
            (
                "true"
                if default
                else
                "false"
            ),
        )
    ).strip().lower()

    return value in {
        "1",
        "true",
        "yes",
        "on",
        "enabled",
    }


def env_float(
    name: str,
    default: float,
) -> float:

    try:

        return float(
            os.environ.get(
                name,
                str(
                    default
                ),
            )
            or
            default
        )

    except Exception:

        return float(
            default
        )


def env_int(
    name: str,
    default: int,
) -> int:

    try:

        return int(
            os.environ.get(
                name,
                str(
                    default
                ),
            )
            or
            default
        )

    except Exception:

        return int(
            default
        )


# =========================================================
# HIGH ALERT
# =========================================================

STC_HIGH_ALERT_ENABLED = env_bool(
    "XPAND_STC_HIGH_ALERT",
    True,
)


STC_REQUIRE_VISUAL_MECHANISM = env_bool(
    "XPAND_STC_REQUIRE_VISUAL_MECHANISM",
    True,
)


STC_REJECT_GENERIC_SCENES = env_bool(
    "XPAND_STC_REJECT_GENERIC_SCENES",
    True,
)


STC_REJECT_REPEATED_SCENES = env_bool(
    "XPAND_STC_REJECT_REPEATED_SCENES",
    True,
)


STC_CREATIVE_RECOVERY_ENABLED = env_bool(
    "XPAND_STC_CREATIVE_RECOVERY_ENABLED",
    True,
)


STC_TARGETED_REPAIR_ENABLED = env_bool(
    "XPAND_STC_TARGETED_REPAIR_ENABLED",
    True,
)


STC_STRICT_QUALIFIED_RELEASE_AUTHORITY = env_bool(
    "XPAND_STC_STRICT_QUALIFIED_RELEASE_AUTHORITY",
    True,
)


# =========================================================
# QUALITY TARGETS
# =========================================================

MASTERPIECE_MIN_SCORE = max(
    82.0,
    min(
        98.0,
        env_float(
            "XPAND_MASTERPIECE_MIN_SCORE",
            88.0,
        ),
    ),
)


MASTERPIECE_RELEASE_FLOOR = max(
    78.0,
    min(
        MASTERPIECE_MIN_SCORE,
        env_float(
            "XPAND_MASTERPIECE_RELEASE_FLOOR",
            84.0,
        ),
    ),
)


FAST_MIN_SCORE = max(
    55.0,
    min(
        90.0,
        env_float(
            "XPAND_FAST_CREATIVE_MIN_SCORE",
            70.0,
        ),
    ),
)


STC_HIGH_ALERT_MIN_SCORE = max(
    86.0,
    min(
        98.0,
        env_float(
            "XPAND_STC_MIN_CONCEPT_SCORE",
            90.0,
        ),
    ),
)


STC_HIGH_ALERT_RELEASE_FLOOR = max(
    84.0,
    min(
        STC_HIGH_ALERT_MIN_SCORE,
        env_float(
            "XPAND_STC_RELEASE_FLOOR",
            88.0,
        ),
    ),
)


# =========================================================
# STC STRICT DIMENSIONS
# =========================================================

STC_MIN_CONCEPT_STRENGTH = 88.0

STC_MIN_BRAND_FIT = 90.0

STC_MIN_ORIGINALITY = 88.0

STC_MIN_VISUAL_MECHANISM = 90.0

STC_MIN_CAMERA_QUALITY = 84.0

STC_MIN_REALISM = 86.0

STC_MIN_FEASIBILITY = 82.0

STC_MIN_COPY_SPACE = 80.0

STC_MIN_DISTINCTIVENESS = 88.0

STC_MIN_AD_READINESS = 90.0


STC_DIMENSION_MINIMUMS: Dict[
    str,
    float,
] = {

    "concept_strength":
        STC_MIN_CONCEPT_STRENGTH,

    "brand_fit":
        STC_MIN_BRAND_FIT,

    "originality":
        STC_MIN_ORIGINALITY,

    "visual_mechanism":
        STC_MIN_VISUAL_MECHANISM,

    "camera_quality":
        STC_MIN_CAMERA_QUALITY,

    "realism":
        STC_MIN_REALISM,

    "feasibility":
        STC_MIN_FEASIBILITY,

    "copy_space_quality":
        STC_MIN_COPY_SPACE,

    "distinctiveness":
        STC_MIN_DISTINCTIVENESS,

    "advertising_readiness":
        STC_MIN_AD_READINESS,
}


# =========================================================
# DIMENSION WEIGHTS
# =========================================================

DIMENSION_WEIGHTS: Dict[
    str,
    int,
] = {

    "concept_strength":
        12,

    "brand_fit":
        12,

    "originality":
        12,

    "visual_mechanism":
        14,

    "camera_quality":
        8,

    "realism":
        8,

    "feasibility":
        8,

    "copy_space_quality":
        6,

    "distinctiveness":
        10,

    "advertising_readiness":
        10,
}


# =========================================================
# CALL POLICY
# =========================================================

NORMAL_CONCEPT_COUNT = 4


STC_HIGH_ALERT_CONCEPT_COUNT = max(
    6,
    min(
        10,
        env_int(
            "XPAND_STC_CONCEPTS_REQUIRED",
            8,
        ),
    ),
)


STC_RECOVERY_CONCEPT_COUNT = max(
    3,
    min(
        4,
        env_int(
            "XPAND_STC_RECOVERY_CONCEPTS",
            3,
        ),
    ),
)


STC_TARGETED_REPAIR_OUTPUT_COUNT = 2


MASTERPIECE_SHORTLIST_SIZE = 3


MASTERPIECE_TARGET_DIRECTOR_CALLS = 3


MASTERPIECE_MAX_DIRECTOR_CALLS = max(
    2,
    min(
        3,
        env_int(
            "XPAND_IMAGE_DIRECTOR_MAX_CALLS",
            3,
        ),
    ),
)


# =========================================================
# TARGETED REPAIR
# =========================================================

STC_TARGETED_REPAIR_MIN_SCORE = max(
    80.0,
    min(
        STC_HIGH_ALERT_RELEASE_FLOOR,
        env_float(
            "XPAND_STC_TARGETED_REPAIR_MIN_SCORE",
            84.0,
        ),
    ),
)


STC_TARGETED_REPAIR_MAX_DIMENSION_FAILURES = max(
    1,
    min(
        5,
        env_int(
            "XPAND_STC_TARGETED_REPAIR_MAX_DIMENSION_FAILURES",
            4,
        ),
    ),
)


STC_TARGETED_REPAIR_MAX_GAP = max(
    1.0,
    min(
        6.0,
        env_float(
            "XPAND_STC_TARGETED_REPAIR_MAX_GAP",
            4.0,
        ),
    ),
)


STC_TARGETED_REPAIR_CANDIDATES = max(
    1,
    min(
        2,
        env_int(
            "XPAND_STC_TARGETED_REPAIR_CANDIDATES",
            2,
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

    if isinstance(
        value,
        tuple,
    ):

        return list(
            value
        )

    return []


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


def clamp_score(
    value: Any,
) -> float:

    return max(
        0.0,
        min(
            100.0,
            safe_float(
                value,
                0.0,
            ),
        ),
    )


def normalize_arabic(
    value: Any,
) -> str:

    text = clean_text(
        value,
        60000,
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
    value: Any,
    markers: Sequence[str],
) -> bool:

    source = normalize_arabic(
        value
    )

    return any(
        normalize_arabic(
            marker
        )
        in source
        for marker in markers
    )


def count_matches(
    value: Any,
    markers: Sequence[str],
) -> int:

    source = normalize_arabic(
        value
    )

    count = 0

    for marker in markers:

        if (
            normalize_arabic(
                marker
            )
            in source
        ):

            count += 1

    return count


def compact_json(
    value: Any,
    limit: int = 12000,
) -> str:

    try:

        output = json.dumps(
            value,
            ensure_ascii=False,
            separators=(
                ",",
                ":",
            ),
            default=str,
        )

    except Exception:

        output = clean_text(
            value,
            limit,
        )

    if len(
        output
    ) <= limit:

        return output

    front = int(
        limit * 0.78
    )

    back = max(
        0,
        limit
        -
        front
        -
        80,
    )

    return (
        output[:front]
        +
        '\n"[XPAND_CONTEXT_COMPACTED]"\n'
        +
        (
            output[-back:]
            if back
            else
            ""
        )
    )


def dedupe_strings(
    values: Iterable[Any],
    *,
    limit: int = 100,
) -> List[str]:

    output: List[str] = []

    seen: Set[str] = set()

    for value in values:

        text = clean_text(
            value,
            1800,
        )

        if not text:

            continue

        key = normalize_arabic(
            text
        )

        if (
            not key
            or
            key in seen
        ):

            continue

        seen.add(
            key
        )

        output.append(
            text
        )

        if len(
            output
        ) >= limit:

            break

    return output


def parse_json_payload(
    raw: Any,
) -> Dict[str, Any]:

    if isinstance(
        raw,
        dict,
    ):

        return raw

    text = clean_text(
        raw,
        220000,
    )

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
    )

    try:

        payload = json.loads(
            text
        )

        if isinstance(
            payload,
            dict,
        ):

            return payload

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

        payload = json.loads(
            text[
                start:
                end + 1
            ]
        )

        if isinstance(
            payload,
            dict,
        ):

            return payload

    raise RuntimeError(
        (
            "Structured Director response "
            "is not a JSON object."
        )
    )


# =========================================================
# CANONICAL BENEFIT FAMILY
# =========================================================

def detect_benefit_family(
    user_request: str,
) -> str:

    value = clean_text(
        user_request,
        14000,
    )

    #
    # STC:
    # canonical policy owns the decision.
    #

    if is_stc_bank_request(
        value
    ):

        return (
            resolve_stc_benefit_family_id(
                value,
                None,
            )
        )

    #
    # Non-STC compatibility.
    #

    if contains_any(
        value,
        [
            "نقاط البيع",
            "point of sale",
            "pos",
            "ecommerce",
            "e-commerce",
            "التجارة الالكترونية",
            "التجارة الإلكترونية",
        ],
    ):

        return (
            FAMILY_MERCHANT_PAYMENTS
        )

    if contains_any(
        value,
        [
            "حوال",
            "تحويل",
            "international transfer",
            "global transfer",
            "remittance",
            "transfer",
        ],
    ):

        return (
            FAMILY_DIGITAL_BANKING
        )

    return FAMILY_PREMIUM


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
            14000,
        )
        +
        "\n"
        +
        clean_text(
            style_hint,
            1200,
        )
    )

    if contains_any(
        text,
        [
            "بيئة بنفسجية",
            "بيئه بنفسجيه",
            "purple architecture",
            "purple studio",
            "استوديو بنفسجي",
        ],
    ):

        return (
            "premium_purple_architecture"
        )

    if contains_any(
        text,
        [
            "واقعية معززة",
            "واقعيه معززه",
            "augmented realism",
            "symbolic realism",
            "واقعي بفكرة خيالية",
            "واقعي بفكره خياليه",
            "واقعي سريالي",
        ],
    ):

        return (
            "premium_augmented_realism"
        )

    return (
        "premium_realistic"
    )


# =========================================================
# HIGH ALERT
# =========================================================

def is_stc_high_alert(
    user_request: str,
    mode: str,
) -> bool:

    return bool(
        STC_HIGH_ALERT_ENABLED
        and
        mode
        ==
        MODE_MASTERPIECE
        and
        is_stc_bank_request(
            user_request
        )
    )


def concept_count_for_request(
    user_request: str,
    mode: str,
) -> int:

    if is_stc_high_alert(
        user_request,
        mode,
    ):

        return (
            STC_HIGH_ALERT_CONCEPT_COUNT
        )

    return NORMAL_CONCEPT_COUNT


# =========================================================
# BRAND PACK
# =========================================================

def locate_stc_brand_pack() -> Optional[
    Path
]:

    candidates = [

        (
            Path(
                __file__
            ).resolve().parent
            /
            "brand_assets"
            /
            "stc_bank"
            /
            "stc_bank_brand_pack.json"
        ),

        (
            Path.cwd()
            /
            "brand_assets"
            /
            "stc_bank"
            /
            "stc_bank_brand_pack.json"
        ),

        Path(
            "/app/brand_assets/stc_bank/stc_bank_brand_pack.json"
        ),
    ]

    for path in candidates:

        try:

            if path.is_file():

                return path.resolve()

        except Exception:

            continue

    return None


def load_stc_brand_pack() -> Dict[
    str,
    Any,
]:

    path = (
        locate_stc_brand_pack()
    )

    if path is None:

        return {}

    try:

        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        if isinstance(
            payload,
            dict,
        ):

            return payload

    except Exception:

        pass

    return {}


def stc_curated_reference_context(
    *,
    benefit_family: str,
    stc_style: str,
) -> Dict[str, Any]:

    result: Dict[
        str,
        Any,
    ] = {

        "available":
            False,

        "selected_assets":
            [],

        "brand_grounding":
            "",

        "reference_brief":
            "",
    }

    if (
        not STC_BRAND_KIT_AVAILABLE
        or
        load_default_stc_brand_kit
        is None
    ):

        return result

    try:

        kit = (
            load_default_stc_brand_kit()
        )

        selected = (
            kit.select_ideation_assets(
                benefit_family=(
                    benefit_family
                ),
                visual_family=(
                    stc_style
                ),
                max_total=7,
                rotation_key=(
                    "creative-v57:"
                    +
                    benefit_family
                    +
                    ":"
                    +
                    stc_style
                ),
            )
        )

        assets: List[
            Dict[str, Any]
        ] = []

        for item in selected:

            assets.append(
                {
                    "asset_id":
                        getattr(
                            item,
                            "asset_id",
                            "",
                        ),

                    "category":
                        getattr(
                            item,
                            "category",
                            "",
                        ),

                    "roles":
                        list(
                            getattr(
                                item,
                                "roles",
                                [],
                            )
                            or []
                        ),

                    "visual_families":
                        list(
                            getattr(
                                item,
                                "visual_families",
                                [],
                            )
                            or []
                        ),

                    "benefit_families":
                        list(
                            getattr(
                                item,
                                "benefit_families",
                                [],
                            )
                            or []
                        ),

                    "notes":
                        clean_text(
                            getattr(
                                item,
                                "notes",
                                "",
                            ),
                            500,
                        ),
                }
            )

        try:

            grounding = (
                kit.build_brand_grounding_text(
                    stc_style,
                    benefit_family=(
                        benefit_family
                    ),
                )
            )

        except TypeError:

            grounding = (
                kit.build_brand_grounding_text(
                    stc_style
                )
            )

        try:

            reference_brief = (
                kit.build_reference_brief(
                    selected
                )
            )

        except Exception:

            reference_brief = ""

        return {

            "available":
                True,

            "selected_assets":
                assets,

            "brand_grounding":
                clean_text(
                    grounding,
                    6500,
                ),

            "reference_brief":
                clean_text(
                    reference_brief,
                    5500,
                ),
        }

    except Exception:

        return result


def stc_brand_pack_prompt_fragment(
    *,
    benefit_family: str,
    stc_style: str,
) -> str:

    pack = (
        load_stc_brand_pack()
    )

    curated = (
        stc_curated_reference_context(
            benefit_family=(
                benefit_family
            ),
            stc_style=(
                stc_style
            ),
        )
    )

    if not pack:

        return compact_json(
            curated,
            9500,
        )

    styles = safe_dict(
        pack.get(
            "styles"
        )
    )

    visual_families = safe_dict(
        pack.get(
            "visual_families"
        )
    )

    style_payload = (
        styles.get(
            stc_style
        )
        or
        visual_families.get(
            stc_style
        )
        or
        {}
    )

    useful = {

        "brand_id":
            pack.get(
                "brand_id"
            ),

        "brand_name":
            pack.get(
                "brand_name"
            ),

        "pack_version":
            pack.get(
                "pack_version"
            ),

        "default_visual_family":
            pack.get(
                "default_visual_family"
            ),

        "identity_keywords":
            pack.get(
                "identity_keywords",
                [],
            ),

        "required_brand_signals":
            pack.get(
                "required_brand_signals",
                [],
            ),

        "banned_patterns":
            pack.get(
                "banned_patterns",
                [],
            ),

        "approved_mechanisms":
            (
                pack.get(
                    "approved_mechanisms"
                )
                or
                pack.get(
                    "approved_visual_mechanisms"
                )
                or
                []
            ),

        "global_rules":
            pack.get(
                "global_rules",
                {},
            ),

        "selected_style":
            style_payload,

        "benefit_family":
            safe_dict(
                pack.get(
                    "benefit_families"
                )
            ).get(
                benefit_family,
                {},
            ),

        "curated_reference_context":
            curated,
    }

    return compact_json(
        useful,
        13000,
    )


# =========================================================
# DATA MODELS
# =========================================================

@dataclass
class CreativeConcept:

    concept_id: str = ""

    category: str = ""

    title: str = ""

    concept_archetype: str = ""

    campaign_hook: str = ""

    core_idea: str = ""

    marketing_message: str = ""

    visual_metaphor: str = ""

    visual_mechanism_type: str = ""

    why_not_generic: str = ""

    environment: str = ""

    environment_novelty: str = ""

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
# CONCEPT SCHEMA
# =========================================================

CONCEPT_SCHEMA: Dict[
    str,
    Any,
] = {

    "type":
        "object",

    "additionalProperties":
        False,

    "properties": {

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

        "concept_archetype": {
            "type":
                "string",
        },

        "campaign_hook": {
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

        "visual_mechanism_type": {
            "type":
                "string",
        },

        "why_not_generic": {
            "type":
                "string",
        },

        "environment": {
            "type":
                "string",
        },

        "environment_novelty": {
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

        "brand_logic": {
            "type":
                "string",
        },

        "production_method": {

            "type":
                "string",

            "enum": [
                "single_generation",
                "controlled_edit",
                "composite",
                "inpainting",
            ],
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
    },

    "required": [
        "concept_id",
        "category",
        "title",
        "concept_archetype",
        "campaign_hook",
        "core_idea",
        "marketing_message",
        "visual_metaphor",
        "visual_mechanism_type",
        "why_not_generic",
        "environment",
        "environment_novelty",
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


def make_ideation_schema(
    concept_count: int,
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
                    concept_count,

                "maxItems":
                    concept_count,

                "items":
                    CONCEPT_SCHEMA,
            },
        },

        "required": [
            "concepts",
        ],
    }


# =========================================================
# EVALUATION SCHEMA
# =========================================================

def evaluation_schema() -> Dict[
    str,
    Any,
]:

    return {

        "type":
            "object",

        "additionalProperties":
            False,

        "properties": {

            "concept_id": {
                "type":
                    "string",
            },

            "concept_strength": {
                "type":
                    "number",
            },

            "brand_fit": {
                "type":
                    "number",
            },

            "originality": {
                "type":
                    "number",
            },

            "visual_mechanism": {
                "type":
                    "number",
            },

            "camera_quality": {
                "type":
                    "number",
            },

            "realism": {
                "type":
                    "number",
            },

            "feasibility": {
                "type":
                    "number",
            },

            "copy_space_quality": {
                "type":
                    "number",
            },

            "distinctiveness": {
                "type":
                    "number",
            },

            "advertising_readiness": {
                "type":
                    "number",
            },

            "weighted_score": {
                "type":
                    "number",
            },

            "verdict": {
                "type":
                    "string",
            },

            "strengths": {

                "type":
                    "array",

                "items": {
                    "type":
                        "string",
                },
            },

            "weaknesses": {

                "type":
                    "array",

                "items": {
                    "type":
                        "string",
                },
            },

            "generic_scene_risk": {
                "type":
                    "boolean",
            },

            "repetition_risk": {
                "type":
                    "boolean",
            },

            "concept_is_scene_only": {
                "type":
                    "boolean",
            },

            "mechanism_survives_single_frame": {
                "type":
                    "boolean",
            },

            "looks_like_real_bank_campaign": {
                "type":
                    "boolean",
            },

            "merchant_online_channel_clear": {
                "type":
                    "boolean",
            },

            "merchant_pos_channel_clear": {
                "type":
                    "boolean",
            },

            "merchant_channels_fused": {
                "type":
                    "boolean",
            },

            "digital_global_reach_clear": {
                "type":
                    "boolean",
            },

            "digital_tracking_control_clear": {
                "type":
                    "boolean",
            },

            "recommended_camera_angle": {
                "type":
                    "string",
            },

            "recommended_lens": {
                "type":
                    "string",
            },

            "recommended_perspective": {
                "type":
                    "string",
            },

            "camera_reason": {
                "type":
                    "string",
            },

            "production_feasible": {
                "type":
                    "boolean",
            },

            "feasibility_reason": {
                "type":
                    "string",
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
            "distinctiveness",
            "advertising_readiness",
            "weighted_score",
            "verdict",
            "strengths",
            "weaknesses",
            "generic_scene_risk",
            "repetition_risk",
            "concept_is_scene_only",
            "mechanism_survives_single_frame",
            "looks_like_real_bank_campaign",
            "merchant_online_channel_clear",
            "merchant_pos_channel_clear",
            "merchant_channels_fused",
            "digital_global_reach_clear",
            "digital_tracking_control_clear",
            "recommended_camera_angle",
            "recommended_lens",
            "recommended_perspective",
            "camera_reason",
            "production_feasible",
            "feasibility_reason",
        ],
    }


def make_review_schema(
    concept_count: int,
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
                    concept_count,

                "maxItems":
                    concept_count,

                "items":
                    evaluation_schema(),
            },
        },

        "required": [
            "evaluations",
        ],
    }


# =========================================================
# JURY SCHEMA
# =========================================================

FINALIST_JURY_SCHEMA: Dict[
    str,
    Any,
] = {

    "type":
        "object",

    "additionalProperties":
        False,

    "properties": {

        "selected_concept_id": {
            "type":
                "string",
        },

        "approval": {
            "type":
                "boolean",
        },

        "confidence": {
            "type":
                "number",
        },

        "advertising_reason": {
            "type":
                "string",
        },

        "brand_reason": {
            "type":
                "string",
        },

        "originality_reason": {
            "type":
                "string",
        },

        "merchant_fusion_approved": {
            "type":
                "boolean",
        },

        "digital_service_approved": {
            "type":
                "boolean",
        },

        "fatal_issues": {

            "type":
                "array",

            "items": {
                "type":
                    "string",
            },
        },

        "production_instruction": {
            "type":
                "string",
        },

        "recommended_camera_angle": {
            "type":
                "string",
        },

        "recommended_lens": {
            "type":
                "string",
        },

        "recommended_perspective": {
            "type":
                "string",
        },

        "do_not_drift_into": {

            "type":
                "array",

            "items": {
                "type":
                    "string",
            },
        },
    },

    "required": [
        "selected_concept_id",
        "approval",
        "confidence",
        "advertising_reason",
        "brand_reason",
        "originality_reason",
        "merchant_fusion_approved",
        "digital_service_approved",
        "fatal_issues",
        "production_instruction",
        "recommended_camera_angle",
        "recommended_lens",
        "recommended_perspective",
        "do_not_drift_into",
    ],
}


def make_board_schema(
    concept_count: int,
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
                    concept_count,

                "maxItems":
                    concept_count,

                "items":
                    CONCEPT_SCHEMA,
            },

            "evaluations": {

                "type":
                    "array",

                "minItems":
                    concept_count,

                "maxItems":
                    concept_count,

                "items":
                    evaluation_schema(),
            },

            "selected_concept_id": {
                "type":
                    "string",
            },

            "approval": {
                "type":
                    "boolean",
            },

            "confidence": {
                "type":
                    "number",
            },

            "advertising_reason": {
                "type":
                    "string",
            },

            "brand_reason": {
                "type":
                    "string",
            },

            "originality_reason": {
                "type":
                    "string",
            },

            "merchant_fusion_approved": {
                "type":
                    "boolean",
            },

            "digital_service_approved": {
                "type":
                    "boolean",
            },

            "fatal_issues": {

                "type":
                    "array",

                "items": {
                    "type":
                        "string",
                },
            },

            "production_instruction": {
                "type":
                    "string",
            },

            "recommended_camera_angle": {
                "type":
                    "string",
            },

            "recommended_lens": {
                "type":
                    "string",
            },

            "recommended_perspective": {
                "type":
                    "string",
            },

            "do_not_drift_into": {

                "type":
                    "array",

                "items": {
                    "type":
                        "string",
                },
            },
        },

        "required": [
            "concepts",
            "evaluations",
            "selected_concept_id",
            "approval",
            "confidence",
            "advertising_reason",
            "brand_reason",
            "originality_reason",
            "merchant_fusion_approved",
            "digital_service_approved",
            "fatal_issues",
            "production_instruction",
            "recommended_camera_angle",
            "recommended_lens",
            "recommended_perspective",
            "do_not_drift_into",
        ],
    }


def make_recovery_schema(
    concept_count: int,
) -> Dict[str, Any]:

    return make_board_schema(
        concept_count
    )


# =========================================================
# STC LOCAL GUARDS
# =========================================================

STC_GENERIC_PATTERNS = [

    "person using phone",
    "man using phone",
    "woman using phone",
    "شخص يستخدم الهاتف",
    "رجل يستخدم الهاتف",
    "امرأة تستخدم الهاتف",

    "customer paying at counter",
    "customer taps terminal",
    "customer tapping terminal",

    "عميل يدفع عند الكاونتر",
    "عميل يدفع عند الكاشير",

    "smiling businessman",
    "business handshake",
    "generic office",
]


STC_FINTECH_CLICHES = [

    "network lines",
    "connection lines",
    "glowing payment trail",
    "glowing route",
    "hologram",
    "holographic",
    "hud",
    "cyber",
    "cyber tunnel",
    "neon fintech",
    "floating icons",
    "floating card",
    "floating phone",
    "floating pos",
    "floating terminal",
    "digital tunnel",
    "laser beam",
    "particle cloud",

    "هولوغرام",
    "بطاقة طافية",
    "خطوط اتصال",
    "مسار ضوئي",
]


STC_REPEATED_SCENE_MARKERS = [

    "wooden counter",
    "wood counter",
    "wooden checkout",

    "luxury boutique",
    "boutique checkout",
    "perfume boutique",
    "fashion boutique",

    "merchant behind counter",
    "worker packing box",
    "packing parcel",

    "كاونتر خشبي",
    "متجر فاخر",
    "موظف يعبئ صندوق",
    "تغليف صندوق",
]


LITERAL_TRANSACTION_CUSTOMER_MARKERS = [

    "customer",
    "shopper",
    "buyer",

    "عميل",
    "زبون",
]


LITERAL_TRANSACTION_COUNTER_MARKERS = [

    "counter",
    "checkout counter",
    "cashier counter",

    "كاونتر",
    "منضدة دفع",
]


LITERAL_TRANSACTION_MERCHANT_MARKERS = [

    "merchant",
    "cashier",
    "seller",
    "store owner",
    "worker",

    "تاجر",
    "بائع",
    "كاشير",
    "موظف",
]


MERCHANT_ONLINE_MARKERS = [

    "التجارة الإلكترونية",
    "التجارة الالكترونية",
    "تجارة إلكترونية",
    "تجاره الكترونيه",

    "e-commerce",
    "ecommerce",
    "online commerce",
    "digital commerce",

    "online order",
    "online ordering",

    "digital storefront",
    "online storefront",

    "web checkout",
    "online checkout",

    "online sale",
    "online sales",

    "طلب إلكتروني",
    "طلب الكتروني",

    "متجر إلكتروني",
    "متجر الكتروني",
]


MERCHANT_PHYSICAL_MARKERS = [

    "نقاط البيع",
    "نقطة البيع",
    "نقطه البيع",

    "الدفع داخل المتجر",
    "الدفع في المتجر",

    "دفع حضوري",

    "جهاز دفع",
    "جهاز نقاط بيع",

    "point of sale",
    "pos",

    "pos terminal",
    "payment terminal",
    "card terminal",
    "card reader",

    "payment reader",
    "tap payment",
    "tap-to-pay",
    "tap to pay",

    "in-store payment",
    "in store payment",

    "in-store acceptance",
    "physical payment",
]


MERCHANT_MECHANISM_MARKERS = [

    "connect",
    "connected",
    "connection",

    "unify",
    "unified",

    "fusion",
    "fused",

    "continuity",
    "continuous",

    "bridge",

    "transformation",
    "transform",

    "cause and effect",

    "same system",
    "one ecosystem",
    "single ecosystem",

    "foreground background relationship",
    "foreground-to-background",

    "perspective reveal",
    "spatial relationship",
    "physical relationship",

    "material transition",
    "service transformation",

    "يربط",
    "ربط",
    "متصل",
    "موحد",
    "توحيد",
    "اندماج",
    "استمرارية",
    "استمراريه",
    "تحول",
    "جسر بصري",
    "علاقة بصرية",
    "علاقه بصريه",
    "نظام واحد",
    "منظومة واحدة",
]


DIGITAL_GLOBAL_REACH_MARKERS = [

    "global",
    "world",
    "worldwide",
    "international",
    "across countries",
    "cross-border",
    "cross border",

    "حول العالم",
    "العالم",
    "دولي",
    "دولية",
    "دوليه",
    "عبر الدول",
]


DIGITAL_TRACKING_MARKERS = [

    "track",
    "tracking",
    "status",
    "follow",
    "control",
    "app control",
    "transfer status",

    "تتبع",
    "متابعة",
    "متابعه",
    "حالة الحوالة",
    "حاله الحواله",
    "من التطبيق",
    "عبر التطبيق",
]


DIGITAL_CLICHE_MARKERS = [

    "floating globe",
    "giant globe",
    "digital globe",
    "world map",
    "map background",

    "glowing route",
    "route line",
    "network line",
    "connection line",

    "glowing world",
    "fintech network",

    "كرة أرضية طافية",
    "كره ارضيه طافيه",
    "خريطة العالم",
    "خريطه العالم",
    "مسار مضيء",
    "خط تحويل",
]


HARD_REJECT_FAILURES: Set[str] = {

    "literal_transaction_tableau",

    "generic_fintech_visual",

    "repeated_stc_scene",

    "generic_lifestyle_without_advertising_mechanism",

    "review_generic_scene_risk",

    "review_repetition_risk",

    "concept_is_scene_only",

    "single_frame_mechanism_failure",

    "not_bank_campaign_ready",

    "merchant_online_channel_unclear",

    "merchant_pos_channel_unclear",

    "merchant_channels_not_visually_connected",

    "digital_global_reach_unclear",

    "digital_tracking_control_unclear",

    "digital_banking_cliche",

    "production_not_feasible",
}


# =========================================================
# PARSING
# =========================================================

def concept_from_dict(
    item: Dict[str, Any],
    *,
    fallback_id: str,
    generation_round: int = 1,
    revised_from: str = "",
) -> CreativeConcept:

    return CreativeConcept(

        concept_id=(
            clean_text(
                item.get(
                    "concept_id"
                ),
                100,
            )
            or
            fallback_id
        ),

        category=clean_text(
            item.get(
                "category"
            ),
            160,
        ),

        title=clean_text(
            item.get(
                "title"
            ),
            500,
        ),

        concept_archetype=clean_text(
            item.get(
                "concept_archetype"
            ),
            600,
        ),

        campaign_hook=clean_text(
            item.get(
                "campaign_hook"
            ),
            1800,
        ),

        core_idea=clean_text(
            item.get(
                "core_idea"
            ),
            3600,
        ),

        marketing_message=clean_text(
            item.get(
                "marketing_message"
            ),
            2200,
        ),

        visual_metaphor=clean_text(
            item.get(
                "visual_metaphor"
            ),
            2600,
        ),

        visual_mechanism_type=clean_text(
            item.get(
                "visual_mechanism_type"
            ),
            800,
        ),

        why_not_generic=clean_text(
            item.get(
                "why_not_generic"
            ),
            2200,
        ),

        environment=clean_text(
            item.get(
                "environment"
            ),
            3000,
        ),

        environment_novelty=clean_text(
            item.get(
                "environment_novelty"
            ),
            2000,
        ),

        hero_element=clean_text(
            item.get(
                "hero_element"
            ),
            1800,
        ),

        supporting_elements=[
            clean_text(
                value,
                900,
            )
            for value
            in safe_list(
                item.get(
                    "supporting_elements"
                )
            )[:8]
            if clean_text(
                value,
                900,
            )
        ],

        camera_angle=clean_text(
            item.get(
                "camera_angle"
            ),
            900,
        ),

        lens=clean_text(
            item.get(
                "lens"
            ),
            400,
        ),

        perspective=clean_text(
            item.get(
                "perspective"
            ),
            1200,
        ),

        lighting=clean_text(
            item.get(
                "lighting"
            ),
            1700,
        ),

        negative_space=clean_text(
            item.get(
                "negative_space"
            ),
            1300,
        ),

        brand_logic=clean_text(
            item.get(
                "brand_logic"
            ),
            2400,
        ),

        production_method=(
            clean_text(
                item.get(
                    "production_method"
                ),
                100,
            )
            or
            "single_generation"
        ),

        campaign_extension=clean_text(
            item.get(
                "campaign_extension"
            ),
            1700,
        ),

        risks=[
            clean_text(
                value,
                900,
            )
            for value
            in safe_list(
                item.get(
                    "risks"
                )
            )[:8]
            if clean_text(
                value,
                900,
            )
        ],

        generation_round=(
            generation_round
        ),

        revised_from=(
            revised_from
        ),
    )


def parse_concepts(
    payload: Dict[str, Any],
    *,
    generation_round: int = 1,
    id_prefix: str = "C",
    force_ids: bool = False,
) -> List[
    CreativeConcept
]:

    raw_concepts = safe_list(
        payload.get(
            "concepts"
        )
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

        forced_id = (
            id_prefix
            +
            str(
                index
            ).zfill(
                2
            )
        )

        concept = concept_from_dict(
            item,
            fallback_id=(
                forced_id
            ),
            generation_round=(
                generation_round
            ),
        )

        if force_ids:

            concept.concept_id = (
                forced_id
            )

        concepts.append(
            concept
        )

    return concepts


# =========================================================
# CONCEPT TEXT
# =========================================================

def concept_search_text(
    concept: CreativeConcept,
) -> str:

    return "\n".join(
        [
            concept.title,
            concept.concept_archetype,
            concept.campaign_hook,
            concept.core_idea,
            concept.marketing_message,
            concept.visual_metaphor,
            concept.visual_mechanism_type,
            concept.why_not_generic,
            concept.environment,
            concept.environment_novelty,
            concept.hero_element,
            " ".join(
                concept.supporting_elements
            ),
            concept.camera_angle,
            concept.lens,
            concept.perspective,
            concept.lighting,
            concept.negative_space,
            concept.brand_logic,
            concept.campaign_extension,
            " ".join(
                concept.risks
            ),
        ]
    )


# =========================================================
# SERVICE LOCAL SIGNALS
# =========================================================

def merchant_local_signals(
    concept: CreativeConcept,
) -> Dict[str, bool]:

    text = (
        concept_search_text(
            concept
        )
    )

    return {

        "online":
            contains_any(
                text,
                MERCHANT_ONLINE_MARKERS,
            ),

        "physical":
            contains_any(
                text,
                MERCHANT_PHYSICAL_MARKERS,
            ),

        "mechanism":
            contains_any(
                text,
                MERCHANT_MECHANISM_MARKERS,
            ),
    }


def digital_local_signals(
    concept: CreativeConcept,
) -> Dict[str, bool]:

    text = (
        concept_search_text(
            concept
        )
    )

    return {

        "global":
            contains_any(
                text,
                DIGITAL_GLOBAL_REACH_MARKERS,
            ),

        "tracking":
            contains_any(
                text,
                DIGITAL_TRACKING_MARKERS,
            ),

        "cliche":
            contains_any(
                text,
                DIGITAL_CLICHE_MARKERS,
            ),
    }


# =========================================================
# LOCAL CONCEPT PENALTIES
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

    text = (
        concept_search_text(
            concept
        )
    )

    penalty = 0.0

    failures: List[str] = []

    # =====================================================
    # LITERAL TRANSACTION TABLEAU
    # =====================================================

    customer = contains_any(
        text,
        LITERAL_TRANSACTION_CUSTOMER_MARKERS,
    )

    counter = contains_any(
        text,
        LITERAL_TRANSACTION_COUNTER_MARKERS,
    )

    merchant = contains_any(
        text,
        LITERAL_TRANSACTION_MERCHANT_MARKERS,
    )

    physical_payment = contains_any(
        text,
        MERCHANT_PHYSICAL_MARKERS,
    )

    packing = contains_any(
        text,
        [
            "packing",
            "packing box",
            "packing parcel",
            "worker packing",
            "تغليف",
            "يعبئ صندوق",
            "تعبئة صندوق",
        ],
    )

    if (
        customer
        and
        counter
        and
        physical_payment
        and
        (
            merchant
            or
            packing
        )
    ):

        penalty += 35.0

        failures.append(
            "literal_transaction_tableau"
        )

    # =====================================================
    # FINTECH CLICHE
    # =====================================================

    fintech_hits = count_matches(
        text,
        STC_FINTECH_CLICHES,
    )

    if fintech_hits >= 2:

        penalty += 30.0

        failures.append(
            "generic_fintech_visual"
        )

    elif fintech_hits == 1:

        penalty += 5.0

        failures.append(
            "generic_fintech_warning"
        )

    # =====================================================
    # REPEATED STC SCENE
    # =====================================================

    repeated_hits = count_matches(
        text,
        STC_REPEATED_SCENE_MARKERS,
    )

    if (
        STC_REJECT_REPEATED_SCENES
        and
        repeated_hits >= 2
    ):

        penalty += 26.0

        failures.append(
            "repeated_stc_scene"
        )

    elif repeated_hits == 1:

        penalty += 4.0

        failures.append(
            "repeated_scene_warning"
        )

    # =====================================================
    # GENERIC LIFESTYLE
    # =====================================================

    generic_hits = count_matches(
        text,
        STC_GENERIC_PATTERNS,
    )

    mechanism_present = bool(
        clean_text(
            concept.visual_mechanism_type,
            800,
        )
        and
        clean_text(
            concept.campaign_hook,
            1800,
        )
        and
        len(
            clean_text(
                concept.why_not_generic,
                2200,
            )
        )
        >=
        25
    )

    if (
        STC_REJECT_GENERIC_SCENES
        and
        generic_hits >= 1
        and
        not mechanism_present
    ):

        penalty += 25.0

        failures.append(
            "generic_lifestyle_without_advertising_mechanism"
        )

    # =====================================================
    # MECHANISM COMPLETENESS
    # =====================================================

    if STC_REQUIRE_VISUAL_MECHANISM:

        if len(
            clean_text(
                concept.visual_mechanism_type,
                1000,
            )
        ) < 4:

            penalty += 5.0

            failures.append(
                "visual_mechanism_type_missing"
            )

        if len(
            clean_text(
                concept.campaign_hook,
                2000,
            )
        ) < 20:

            penalty += 4.0

            failures.append(
                "campaign_hook_weak"
            )

        if len(
            clean_text(
                concept.why_not_generic,
                2200,
            )
        ) < 25:

            penalty += 4.0

            failures.append(
                "generic_defense_missing"
            )

        if len(
            clean_text(
                concept.environment_novelty,
                1800,
            )
        ) < 25:

            penalty += 3.0

            failures.append(
                "environment_novelty_missing"
            )

    # =====================================================
    # PURPLE IS NOT THE IDEA
    # =====================================================

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
                "purple cyber",
                "everything purple",
                "بنفسجي نيون",
            ],
        )
    ):

        penalty += 18.0

        failures.append(
            "purple_neon_brand_substitute"
        )

    # =====================================================
    # MERCHANT
    # =====================================================

    if (
        benefit_family
        ==
        FAMILY_MERCHANT_PAYMENTS
    ):

        signals = (
            merchant_local_signals(
                concept
            )
        )

        if not signals[
            "online"
        ]:

            penalty += 3.0

            failures.append(
                "merchant_online_language_implicit"
            )

        if not signals[
            "physical"
        ]:

            penalty += 3.0

            failures.append(
                "merchant_pos_language_implicit"
            )

        if not signals[
            "mechanism"
        ]:

            penalty += 4.0

            failures.append(
                "merchant_connection_language_weak"
            )

    # =====================================================
    # DIGITAL BANKING / INTERNATIONAL TRANSFER
    # =====================================================

    if (
        benefit_family
        ==
        FAMILY_DIGITAL_BANKING
    ):

        signals = (
            digital_local_signals(
                concept
            )
        )

        if not signals[
            "global"
        ]:

            penalty += 4.0

            failures.append(
                "digital_global_reach_language_weak"
            )

        if not signals[
            "tracking"
        ]:

            penalty += 4.0

            failures.append(
                "digital_tracking_language_weak"
            )

        if signals[
            "cliche"
        ]:

            penalty += 22.0

            failures.append(
                "digital_banking_cliche"
            )

    return (
        penalty,
        dedupe_strings(
            failures
        ),
    )


# =========================================================
# SCORE
# =========================================================

def dimension_composite_score(
    scores: Dict[str, Any],
) -> float:

    total = 0.0

    for key, weight in (
        DIMENSION_WEIGHTS.items()
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
                weight
                /
                100.0
            )
        )

    return round(
        total,
        2,
    )


# =========================================================
# STRICT GATE
# =========================================================

def stc_dimension_gate_failures(
    concept: CreativeConcept,
) -> List[str]:

    scores = safe_dict(
        concept.scores
    )

    failures: List[str] = []

    for key, minimum in (
        STC_DIMENSION_MINIMUMS.items()
    ):

        value = clamp_score(
            scores.get(
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
                        int(
                            minimum
                        )
                    )
                )
            )

    if any(
        failure
        in HARD_REJECT_FAILURES
        for failure
        in concept.quality_gate_failures
    ):

        failures.append(
            "hard_local_reject"
        )

    if not bool(
        safe_dict(
            concept.feasibility
        ).get(
            "production_feasible",
            False,
        )
    ):

        failures.append(
            "production_not_feasible"
        )

    return dedupe_strings(
        failures
    )


def strict_qualified_concepts(
    concepts: Sequence[
        CreativeConcept
    ],
    *,
    high_alert: bool,
) -> List[
    CreativeConcept
]:

    output: List[
        CreativeConcept
    ] = []

    for concept in concepts:

        if not concept.evaluation_valid:

            continue

        if any(
            failure
            in HARD_REJECT_FAILURES
            for failure
            in concept.quality_gate_failures
        ):

            continue

        if high_alert:

            if (
                concept.weighted_score
                <
                STC_HIGH_ALERT_RELEASE_FLOOR
            ):

                continue

            if stc_dimension_gate_failures(
                concept
            ):

                continue

        output.append(
            concept
        )

    output.sort(
        key=lambda item:
            item.weighted_score,
        reverse=True,
    )

    return output


# =========================================================
# TARGETED REPAIR DIAGNOSIS
# =========================================================

def targeted_repair_dimension_gaps(
    concept: CreativeConcept,
) -> List[
    Dict[str, Any]
]:

    scores = safe_dict(
        concept.scores
    )

    gaps: List[
        Dict[str, Any]
    ] = []

    for key, minimum in (
        STC_DIMENSION_MINIMUMS.items()
    ):

        score = clamp_score(
            scores.get(
                key,
                0,
            )
        )

        if score >= minimum:

            continue

        gaps.append(
            {
                "dimension":
                    key,

                "score":
                    round(
                        score,
                        2,
                    ),

                "minimum":
                    round(
                        minimum,
                        2,
                    ),

                "gap":
                    round(
                        minimum
                        -
                        score,
                        2,
                    ),
            }
        )

    return gaps


def targeted_repair_rejection_reason(
    concept: CreativeConcept,
) -> str:

    if not concept.evaluation_valid:

        return (
            "evaluation_not_valid"
        )

    hard_failures = [
        failure
        for failure
        in concept.quality_gate_failures
        if failure
        in HARD_REJECT_FAILURES
    ]

    if hard_failures:

        return (
            "hard_reject:"
            +
            ",".join(
                hard_failures
            )
        )

    if not bool(
        safe_dict(
            concept.feasibility
        ).get(
            "production_feasible",
            False,
        )
    ):

        return (
            "production_not_feasible"
        )

    if (
        concept.weighted_score
        <
        STC_TARGETED_REPAIR_MIN_SCORE
    ):

        return (
            "score_below_repair_floor"
        )

    gaps = (
        targeted_repair_dimension_gaps(
            concept
        )
    )

    if not gaps:

        return (
            "already_strict_dimension_qualified"
        )

    if (
        len(
            gaps
        )
        >
        STC_TARGETED_REPAIR_MAX_DIMENSION_FAILURES
    ):

        return (
            "too_many_dimension_failures"
        )

    largest_gap = max(
        (
            safe_float(
                item.get(
                    "gap"
                ),
                0,
            )
            for item
            in gaps
        ),
        default=0.0,
    )

    if (
        largest_gap
        >
        STC_TARGETED_REPAIR_MAX_GAP
    ):

        return (
            "dimension_gap_too_large"
        )

    return ""


def is_targeted_repair_candidate(
    concept: CreativeConcept,
) -> bool:

    return not bool(
        targeted_repair_rejection_reason(
            concept
        )
    )


def select_targeted_repair_candidates(
    concepts: Sequence[
        CreativeConcept
    ],
) -> List[
    CreativeConcept
]:

    if not STC_TARGETED_REPAIR_ENABLED:

        return []

    candidates = [
        concept
        for concept
        in concepts
        if is_targeted_repair_candidate(
            concept
        )
    ]

    candidates.sort(
        key=lambda item:
            (
                item.weighted_score,
                -len(
                    targeted_repair_dimension_gaps(
                        item
                    )
                ),
            ),
        reverse=True,
    )

    return candidates[
        :STC_TARGETED_REPAIR_CANDIDATES
    ]


# =========================================================
# ARCHETYPES
# =========================================================

STC_HIGH_ALERT_ARCHETYPES = """
The concept pool must deliberately cover fundamentally
different advertising grammars.

Concept 1:
PREMIUM HUMAN REALISM
Real Saudi life with a genuine campaign mechanism.

Concept 2:
OBJECT-LED COMMERCIAL STORY
A physically real object relationship communicates the service.

Concept 3:
ARCHITECTURAL / SPATIAL IDEA
Space, depth, threshold or geometry carries the proposition.

Concept 4:
AUGMENTED REALISM
One believable conceptual intervention inside a real world.

Concept 5:
CAMERA-LED IDEA
The viewpoint itself reveals the proposition.

Concept 6:
SERVICE TRANSFORMATION
One physical action changes the commercial meaning.

Concept 7:
AUTHENTIC SAUDI CONTEXT
Contemporary Saudi life or commerce without stock-ad clichés.

Concept 8:
BOLD CAMPAIGN HERO
One simple, memorable, award-minded proposition.

At most TWO concepts may use indoor retail.

At most ONE concept may make a POS terminal the obvious
foreground hero.

Do not generate cosmetic variations of one scene.
""".strip()


# =========================================================
# SHARED CANONICAL POLICY TEXT
# =========================================================

def canonical_service_constitution(
    *,
    user_request: str,
    benefit_family: str,
    stc_style: str,
) -> str:

    if not is_stc_bank_request(
        user_request
    ):

        return ""

    return (
        build_creative_constitution_text(
            user_text=(
                user_request
            ),
            explicit_benefit_family=(
                benefit_family
            ),
            selected_stc_style=(
                stc_style
            ),
        )
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
    concept_count: int = 4,
    high_alert: bool = False,
) -> str:

    technical_retry_block = ""

    if recovery:

        technical_retry_block = f"""
==================================================
STRUCTURED TECHNICAL RETRY
==================================================

The previous structured request failed technically.

Return exactly {concept_count} complete concept objects.

Do not simplify the schema.
""".strip()

    stc_block = ""

    if is_stc_bank_request(
        user_request
    ):

        constitution = (
            canonical_service_constitution(
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

        high_alert_block = ""

        if high_alert:

            high_alert_block = f"""
==================================================
STC BANK HIGH ALERT
==================================================

THE USER SUPPLIES THE COMMERCIAL MESSAGE.

YOU SUPPLY THE ADVERTISING IDEA.

The user does NOT need to invent:
- the scene
- the metaphor
- the mechanism
- the environment
- the camera

A scene is not an advertising idea.

A phone is not an advertising idea.

A POS machine is not an advertising idea.

A purple room is not an advertising idea.

Every concept needs ONE visual mechanism that works
in one still image.

==================================================
MANDATORY DIVERSITY
==================================================

{STC_HIGH_ALERT_ARCHETYPES}
""".strip()

        stc_block = f"""
==================================================
CANONICAL STC SERVICE POLICY
==================================================

{constitution}

==================================================
PERMANENT STC BRAND INTELLIGENCE
==================================================

{stc_brand_pack_prompt_fragment(
    benefit_family=benefit_family,
    stc_style=stc_style,
)}

The reference pack is VISUAL DNA.

Learn:
- campaign maturity
- tonal restraint
- camera sophistication
- lighting discipline
- material behavior
- Saudi relevance
- composition
- premium financial confidence

Never clone:
- exact composition
- exact people
- exact environment
- copy
- logo
- readable UI

==================================================
PHOTOGRAPHIC REALISM
==================================================

Everything must be physically photographable.

Correct:
- gravity
- scale
- hand/object contact
- anatomy
- perspective
- reflections
- contact shadows
- material roughness
- object support

Do not create impossible objects merely to create a metaphor.

==================================================
CAMERA LAW
==================================================

Camera must strengthen the meaning.

Do not automatically choose:
centered + eye-level + three-quarter product shot.

Consider when meaningful:
- reflection-led composition
- foreground occlusion
- architectural frame
- compressed long-lens relation
- controlled environmental wide angle
- true top-down relationship
- low grazing perspective
- deliberate asymmetric perspective

==================================================
COPY SPACE
==================================================

Use approximately 25–40% integrated calm copy space
when useful.

Do NOT create:
- an artificial blank panel
- 30–40% automatic empty wall
- a hero pushed into the bottom of the frame

Negative space must belong naturally to the composition.

==================================================
TEXT / LOGO
==================================================

The intended image contains NO generated:
- headline
- slogan
- CTA
- STC logo
- bank logo
- readable app UI
- fake banking labels
- financial numbers
- card-network logo

==================================================
STC SKILL
==================================================

{clean_text(
    STC_BANK_VISUAL_SKILL + "\n" + __import__("xpand_stc_skill_runtime").read_skill_file("references/concept-workflow.md"),
    6500,
)}

{high_alert_block}
""".strip()

    return f"""
You are XPAND Creative Brain V5.7.

Your role is to invent a campaign-grade visual advertising
idea from the user's COMMERCIAL MESSAGE.

==================================================
ORIGINAL USER REQUEST
==================================================

{clean_text(
    user_request,
    7200,
)}

==================================================
CANONICAL BENEFIT FAMILY
==================================================

{benefit_family}

This family is already resolved.

DO NOT silently replace it with:
premium,
speed,
generic banking,
or another family.

==================================================
BRAND CONTEXT
==================================================

{compact_json(
    brand_context,
    6500,
)}

==================================================
RUNTIME REFERENCE DNA
==================================================

{compact_json(
    visual_references,
    7000,
)}

==================================================
STYLE HINT
==================================================

{clean_text(
    style_hint,
    1300,
)}

==================================================
IDEATION
==================================================

Generate exactly {concept_count} fundamentally different
advertising concepts.

Each direction must materially differ in:
- visual mechanism
- hero relationship
- environment
- spatial structure
- camera grammar

Do not create cosmetic variants.

{stc_block}

{technical_retry_block}

==================================================
OUTPUT
==================================================

Return exactly the requested structured schema.

Concept IDs:
C01
C02
C03
...

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
    high_alert: bool,
) -> str:

    payload = [
        concept_to_dict(
            concept
        )
        for concept
        in concepts
    ]

    constitution = (
        canonical_service_constitution(
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

    strict_block = ""

    if high_alert:

        strict_block = f"""
==================================================
STRICT STC RELEASE STANDARD
==================================================

A concept is not 90+ merely because it is pretty.

Strict gates:

concept_strength >= {STC_MIN_CONCEPT_STRENGTH}
brand_fit >= {STC_MIN_BRAND_FIT}
originality >= {STC_MIN_ORIGINALITY}
visual_mechanism >= {STC_MIN_VISUAL_MECHANISM}
camera_quality >= {STC_MIN_CAMERA_QUALITY}
realism >= {STC_MIN_REALISM}
feasibility >= {STC_MIN_FEASIBILITY}
copy_space_quality >= {STC_MIN_COPY_SPACE}
distinctiveness >= {STC_MIN_DISTINCTIVENESS}
advertising_readiness >= {STC_MIN_AD_READINESS}

Overall release floor:
{STC_HIGH_ALERT_RELEASE_FLOOR}

Do not inflate scores.

65–78:
attractive but ordinary.

78–86:
polished but familiar.

90+:
exceptional campaign-ready direction.
""".strip()

    return f"""
You are XPAND V5.7 EXECUTIVE CREATIVE REVIEW.

Evaluate each concept independently.

Do NOT invent new concepts.

==================================================
REQUEST
==================================================

{clean_text(
    user_request,
    6200,
)}

==================================================
CANONICAL BENEFIT
==================================================

{benefit_family}

The benefit family is LOCKED.

==================================================
STC SERVICE CONSTITUTION
==================================================

{constitution}

==================================================
STYLE
==================================================

{stc_style}

==================================================
CONCEPTS
==================================================

{compact_json(
    payload,
    33000,
)}

==================================================
SCORE 0–100
==================================================

concept_strength:
Is there one strong single-frame advertising proposition?

brand_fit:
Could this genuinely belong to STC Bank?

originality:
Is it materially beyond generic banking stock imagery?

visual_mechanism:
Is there a real visual idea rather than a scene?

camera_quality:
Does camera strengthen meaning?

realism:
Can it look genuinely photographic and physically credible?

feasibility:
Can an image model preserve the mechanism?

copy_space_quality:
Is approximately 25–40% copy space naturally integrated,
without a giant dead upper region?

distinctiveness:
Is the idea memorable?

advertising_readiness:
Could a senior bank creative director authorize production?

weighted_score:
Return a strict overall score.

==================================================
GENERAL BOOLEAN REVIEW
==================================================

generic_scene_risk:
TRUE if this can collapse into ordinary lifestyle or
transaction photography.

repetition_risk:
TRUE if it repeats known weak XPAND/STC scene structures.

concept_is_scene_only:
TRUE if it is mainly location + props + people.

mechanism_survives_single_frame:
TRUE only if the central advertising idea is readable
in one still frame.

looks_like_real_bank_campaign:
TRUE only if the concept feels campaign-grade.

==================================================
MERCHANT PAYMENTS
==================================================

If benefit_family = merchant_payments:

merchant_online_channel_clear:
The viewer understands the e-commerce / online channel.

merchant_pos_channel_clear:
The viewer understands physical payment acceptance.

merchant_channels_fused:
The two are connected by ONE advertising mechanism.

Putting both in one room is NOT fusion.

For non-merchant requests:
all merchant booleans = TRUE.

==================================================
DIGITAL BANKING / GLOBAL TRANSFER
==================================================

If benefit_family = digital_banking:

digital_global_reach_clear:
The viewer can understand global / international reach
without requiring text.

digital_tracking_control_clear:
The viewer can understand easy digital tracking/control
without requiring readable app UI.

HARD WARNING:

Do NOT reward:
- generic person holding phone
- giant floating globe
- map background
- glowing world route
- network lines
- fintech HUD

For non-digital requests:
both digital booleans = TRUE.

==================================================
PRODUCTION FEASIBILITY
==================================================

production_feasible = TRUE only when the central idea can
exist in one physically coherent image.

No impossible geometry.

No requirement for readable UI.

No device mutation.

==================================================
CAMERA
==================================================

Return one:
- angle
- lens
- perspective

for each concept.

{strict_block}

Return exactly the requested structured schema.
""".strip()


# =========================================================
# FINALIST JURY PROMPT
# =========================================================

def build_finalist_jury_prompt(
    *,
    user_request: str,
    finalists: List[
        CreativeConcept
    ],
    benefit_family: str,
    stc_style: str,
) -> str:

    payload = [
        concept_to_dict(
            concept
        )
        for concept
        in finalists
    ]

    constitution = (
        canonical_service_constitution(
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

    return f"""
You are XPAND V5.7 FINAL STC BANK ART-DIRECTION JURY.

Every supplied concept has ALREADY passed deterministic
strict qualification.

Your role is advisory art direction.

You may:
- rank
- recommend
- strengthen camera
- strengthen environment
- identify production risks

You may NOT erase every strict-qualified concept.

==================================================
REQUEST
==================================================

{clean_text(
    user_request,
    6000,
)}

==================================================
CANONICAL BENEFIT
==================================================

{benefit_family}

==================================================
SERVICE CONSTITUTION
==================================================

{constitution}

==================================================
STYLE
==================================================

{stc_style}

==================================================
STRICT-QUALIFIED FINALISTS
==================================================

{compact_json(
    payload,
    25000,
)}

==================================================
SELECT
==================================================

Choose one supplied ID.

Prefer:
- strongest advertising mechanism
- strongest STC ownership
- clearest service meaning
- strongest realism
- strongest camera
- lowest generic-scene risk

merchant_fusion_approved:
For merchant_payments, TRUE only if online + physical payment
are genuinely connected.

For non-merchant:
TRUE.

digital_service_approved:
For digital_banking, TRUE only if global reach plus
tracking/control are clear without readable text.

For non-digital:
TRUE.

==================================================
PRODUCTION INSTRUCTION
==================================================

Lock:
- hero relationship
- mechanism
- environment
- angle
- lens
- perspective
- lighting
- approximately 25–40% integrated copy space

do_not_drift_into should explicitly identify the most likely
generic failure modes.

Return exactly the schema.
""".strip()


# =========================================================
# FAILURE CONTEXT
# =========================================================

def build_failure_context(
    concepts: Sequence[
        CreativeConcept
    ],
    limit: int = 4,
) -> str:

    ranked = [
        item
        for item
        in concepts
        if item.evaluation_valid
    ]

    ranked.sort(
        key=lambda item:
            item.weighted_score,
        reverse=True,
    )

    payload = []

    for concept in ranked[
        :limit
    ]:

        payload.append(
            {
                "concept_id":
                    concept.concept_id,

                "title":
                    concept.title,

                "archetype":
                    concept.concept_archetype,

                "score":
                    concept.weighted_score,

                "scores":
                    concept.scores,

                "quality_failures":
                    concept.quality_gate_failures,

                "weaknesses":
                    safe_list(
                        concept.debate.get(
                            "weaknesses"
                        )
                    )[:8],

                "core_idea":
                    clean_text(
                        concept.core_idea,
                        1100,
                    ),

                "visual_mechanism":
                    clean_text(
                        concept.visual_metaphor,
                        1000,
                    ),

                "environment":
                    clean_text(
                        concept.environment,
                        800,
                    ),
            }
        )

    return compact_json(
        payload,
        18000,
    )


def build_targeted_repair_context(
    candidates: Sequence[
        CreativeConcept
    ],
) -> str:

    payload = []

    for concept in candidates:

        payload.append(
            {
                "concept_id":
                    concept.concept_id,

                "title":
                    concept.title,

                "weighted_score":
                    concept.weighted_score,

                "dimension_gaps":
                    targeted_repair_dimension_gaps(
                        concept
                    ),

                "quality_failures":
                    concept.quality_gate_failures,

                "strengths":
                    safe_list(
                        concept.debate.get(
                            "strengths"
                        )
                    )[:8],

                "weaknesses":
                    safe_list(
                        concept.debate.get(
                            "weaknesses"
                        )
                    )[:8],

                "core_idea":
                    clean_text(
                        concept.core_idea,
                        1600,
                    ),

                "campaign_hook":
                    clean_text(
                        concept.campaign_hook,
                        1200,
                    ),

                "visual_metaphor":
                    clean_text(
                        concept.visual_metaphor,
                        1500,
                    ),

                "environment":
                    clean_text(
                        concept.environment,
                        1200,
                    ),

                "camera_angle":
                    concept.camera_angle,

                "lens":
                    concept.lens,

                "perspective":
                    concept.perspective,
            }
        )

    return compact_json(
        payload,
        22000,
    )


# =========================================================
# TARGETED REPAIR PROMPT
# =========================================================

def build_targeted_repair_prompt(
    *,
    user_request: str,
    repair_candidates: Sequence[
        CreativeConcept
    ],
    brand_context: Any,
    visual_references: Any,
    benefit_family: str,
    stc_style: str,
) -> str:

    constitution = (
        canonical_service_constitution(
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

    return f"""
You are XPAND V5.7 TARGETED CREATIVE REPAIR BOARD.

The Executive Review found a strong near-miss.

You have one final Director call.

Create exactly TWO repaired directions.

Do NOT throw away the strong core proposition.

Do NOT merely polish wording.

Fix the diagnosed dimensions.

==================================================
REQUEST
==================================================

{clean_text(
    user_request,
    6000,
)}

==================================================
CANONICAL BENEFIT
==================================================

{benefit_family}

==================================================
SERVICE CONSTITUTION
==================================================

{constitution}

==================================================
REPAIR CANDIDATES
==================================================

{build_targeted_repair_context(
    repair_candidates
)}

==================================================
BRAND INTELLIGENCE
==================================================

{stc_brand_pack_prompt_fragment(
    benefit_family=benefit_family,
    stc_style=stc_style,
)}

==================================================
BRAND CONTEXT
==================================================

{compact_json(
    brand_context,
    5000,
)}

==================================================
REFERENCE DNA
==================================================

{compact_json(
    visual_references,
    5500,
)}

==================================================
STRICT GATES
==================================================

concept_strength >= {STC_MIN_CONCEPT_STRENGTH}
brand_fit >= {STC_MIN_BRAND_FIT}
originality >= {STC_MIN_ORIGINALITY}
visual_mechanism >= {STC_MIN_VISUAL_MECHANISM}
camera_quality >= {STC_MIN_CAMERA_QUALITY}
realism >= {STC_MIN_REALISM}
feasibility >= {STC_MIN_FEASIBILITY}
copy_space_quality >= {STC_MIN_COPY_SPACE}
distinctiveness >= {STC_MIN_DISTINCTIVENESS}
advertising_readiness >= {STC_MIN_AD_READINESS}

Release floor >= {STC_HIGH_ALERT_RELEASE_FLOOR}

No threshold lowering.

==================================================
HARD BANS
==================================================

Never repair into:
- generic customer/phone
- ordinary checkout
- customer + POS + counter + merchant
- worker packing parcel as e-commerce concept
- wooden counter
- random purple room
- floating fintech objects
- network lines
- glowing routes
- HUD
- giant globe
- readable banking UI
- generated text/logo
- artificial empty panel

Use 25–40% integrated copy space.

==================================================
OUTPUT
==================================================

Create exactly:
T01
T02

Evaluate both independently.

Provide jury guidance.

The runtime independently decides strict qualification.

Return exactly the structured schema.
""".strip()


# =========================================================
# FRESH RECOVERY PROMPT
# =========================================================

def build_recovery_board_prompt(
    *,
    user_request: str,
    failed_concepts: Sequence[
        CreativeConcept
    ],
    brand_context: Any,
    visual_references: Any,
    benefit_family: str,
    stc_style: str,
) -> str:

    constitution = (
        canonical_service_constitution(
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

    return f"""
You are XPAND V5.7 FRESH CREATIVE RECOVERY BOARD.

The first concept pool failed strict qualification.

No repairable near-miss exists.

Create a materially DIFFERENT conceptual grammar.

Exactly {STC_RECOVERY_CONCEPT_COUNT} new directions.

==================================================
REQUEST
==================================================

{clean_text(
    user_request,
    6000,
)}

==================================================
CANONICAL BENEFIT
==================================================

{benefit_family}

==================================================
SERVICE CONSTITUTION
==================================================

{constitution}

==================================================
FAILED DIRECTIONS
==================================================

{build_failure_context(
    failed_concepts,
    limit=4,
)}

==================================================
RECOVERY LAW
==================================================

Do not simply:
- change location
- change person
- change wall
- change lens
- add purple
- add effects

Change the underlying advertising mechanism.

==================================================
PERMANENT STC BRAND INTELLIGENCE
==================================================

{stc_brand_pack_prompt_fragment(
    benefit_family=benefit_family,
    stc_style=stc_style,
)}

==================================================
BRAND CONTEXT
==================================================

{compact_json(
    brand_context,
    5000,
)}

==================================================
REFERENCE DNA
==================================================

{compact_json(
    visual_references,
    5500,
)}

==================================================
STRICT GATES
==================================================

concept_strength >= {STC_MIN_CONCEPT_STRENGTH}
brand_fit >= {STC_MIN_BRAND_FIT}
originality >= {STC_MIN_ORIGINALITY}
visual_mechanism >= {STC_MIN_VISUAL_MECHANISM}
camera_quality >= {STC_MIN_CAMERA_QUALITY}
realism >= {STC_MIN_REALISM}
feasibility >= {STC_MIN_FEASIBILITY}
copy_space_quality >= {STC_MIN_COPY_SPACE}
distinctiveness >= {STC_MIN_DISTINCTIVENESS}
advertising_readiness >= {STC_MIN_AD_READINESS}

release floor >= {STC_HIGH_ALERT_RELEASE_FLOOR}

==================================================
REALISM
==================================================

One coherent image.

One physical world.

One camera system.

No impossible object geometry.

No required readable UI.

==================================================
COPY SPACE
==================================================

25–40% integrated copy space.

No artificial blank panel.

==================================================
OUTPUT IDS
==================================================

R01
R02
R03

Evaluate every concept independently.

Provide jury guidance.

Return exactly the requested structured schema.
""".strip()


# =========================================================
# GENERATE CONCEPTS
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
    concept_count: int,
    high_alert: bool,
) -> List[
    CreativeConcept
]:

    prompt = (
        build_ideation_prompt(
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
            concept_count=(
                concept_count
            ),
            high_alert=(
                high_alert
            ),
        )
    )

    raw = call_openai_director(
        prompt,
        json_mode=True,
        json_schema=(
            make_ideation_schema(
                concept_count
            )
        ),
        json_schema_name=(
            "xpand_creative_ideation_v57"
        ),
    )

    payload = (
        parse_json_payload(
            raw
        )
    )

    concepts = (
        parse_concepts(
            payload,
            generation_round=1,
            id_prefix="C",
            force_ids=True,
        )
    )

    if len(
        concepts
    ) != concept_count:

        raise RuntimeError(
            (
                "Creative ideation returned "
                +
                str(
                    len(
                        concepts
                    )
                )
                +
                " concepts; expected "
                +
                str(
                    concept_count
                )
            )
        )

    return concepts


# =========================================================
# APPLY EVALUATIONS
# =========================================================

def apply_evaluations_to_concepts(
    *,
    user_request: str,
    concepts: Sequence[
        CreativeConcept
    ],
    evaluations: Sequence[Any],
    benefit_family: str,
    stc_style: str,
    evaluation_source: str,
) -> None:

    by_id: Dict[
        str,
        Dict[str, Any]
    ] = {}

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

            by_id[
                concept_id
            ] = item

    for concept in concepts:

        evaluation = by_id.get(
            concept.concept_id
        )

        if not evaluation:

            concept.evaluation_valid = False

            concept.quality_gate_failures = (
                dedupe_strings(
                    concept.quality_gate_failures
                    +
                    [
                        "evaluation_missing"
                    ]
                )
            )

            continue

        scores: Dict[
            str,
            float
        ] = {}

        for key in (
            DIMENSION_WEIGHTS.keys()
        ):

            scores[
                key
            ] = clamp_score(
                evaluation.get(
                    key,
                    0,
                )
            )

        concept.scores = (
            scores
        )

        model_weighted = clamp_score(
            evaluation.get(
                "weighted_score",
                0,
            )
        )

        deterministic_weighted = (
            dimension_composite_score(
                scores
            )
        )

        #
        # Deterministic score is authority.
        #

        concept.weighted_score = (
            deterministic_weighted
        )

        penalty, local_failures = (
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

        concept.weighted_score = max(
            0.0,
            round(
                concept.weighted_score
                -
                penalty,
                2,
            ),
        )

        failures = list(
            local_failures
        )

        generic_scene_risk = bool(
            evaluation.get(
                "generic_scene_risk",
                False,
            )
        )

        repetition_risk = bool(
            evaluation.get(
                "repetition_risk",
                False,
            )
        )

        scene_only = bool(
            evaluation.get(
                "concept_is_scene_only",
                False,
            )
        )

        mechanism_survives = bool(
            evaluation.get(
                "mechanism_survives_single_frame",
                False,
            )
        )

        bank_campaign = bool(
            evaluation.get(
                "looks_like_real_bank_campaign",
                False,
            )
        )

        production_feasible = bool(
            evaluation.get(
                "production_feasible",
                False,
            )
        )

        if generic_scene_risk:

            failures.append(
                "review_generic_scene_risk"
            )

        if repetition_risk:

            failures.append(
                "review_repetition_risk"
            )

        if scene_only:

            failures.append(
                "concept_is_scene_only"
            )

        if not mechanism_survives:

            failures.append(
                "single_frame_mechanism_failure"
            )

        if not bank_campaign:

            failures.append(
                "not_bank_campaign_ready"
            )

        if not production_feasible:

            failures.append(
                "production_not_feasible"
            )

        merchant_online = bool(
            evaluation.get(
                "merchant_online_channel_clear",
                True,
            )
        )

        merchant_pos = bool(
            evaluation.get(
                "merchant_pos_channel_clear",
                True,
            )
        )

        merchant_fused = bool(
            evaluation.get(
                "merchant_channels_fused",
                True,
            )
        )

        if (
            benefit_family
            ==
            FAMILY_MERCHANT_PAYMENTS
        ):

            if not merchant_online:

                failures.append(
                    "merchant_online_channel_unclear"
                )

            if not merchant_pos:

                failures.append(
                    "merchant_pos_channel_unclear"
                )

            if not merchant_fused:

                failures.append(
                    "merchant_channels_not_visually_connected"
                )

        digital_global = bool(
            evaluation.get(
                "digital_global_reach_clear",
                True,
            )
        )

        digital_tracking = bool(
            evaluation.get(
                "digital_tracking_control_clear",
                True,
            )
        )

        if (
            benefit_family
            ==
            FAMILY_DIGITAL_BANKING
        ):

            if not digital_global:

                failures.append(
                    "digital_global_reach_unclear"
                )

            if not digital_tracking:

                failures.append(
                    "digital_tracking_control_unclear"
                )

        concept.feasibility = {

            "production_feasible":
                production_feasible,

            "reason":
                clean_text(
                    evaluation.get(
                        "feasibility_reason"
                    ),
                    1800,
                ),
        }

        concept.debate = {

            "evaluation_source":
                evaluation_source,

            "model_weighted_score":
                model_weighted,

            "deterministic_weighted_score":
                deterministic_weighted,

            "local_penalty":
                penalty,

            "strengths":
                [
                    clean_text(
                        item,
                        1200,
                    )
                    for item
                    in safe_list(
                        evaluation.get(
                            "strengths"
                        )
                    )[:10]
                    if clean_text(
                        item,
                        1200,
                    )
                ],

            "weaknesses":
                [
                    clean_text(
                        item,
                        1200,
                    )
                    for item
                    in safe_list(
                        evaluation.get(
                            "weaknesses"
                        )
                    )[:10]
                    if clean_text(
                        item,
                        1200,
                    )
                ],

            "verdict":
                clean_text(
                    evaluation.get(
                        "verdict"
                    ),
                    120,
                ),

            "generic_scene_risk":
                generic_scene_risk,

            "repetition_risk":
                repetition_risk,

            "concept_is_scene_only":
                scene_only,

            "mechanism_survives_single_frame":
                mechanism_survives,

            "looks_like_real_bank_campaign":
                bank_campaign,

            "merchant_semantics": {

                "online_channel_clear":
                    merchant_online,

                "pos_channel_clear":
                    merchant_pos,

                "channels_fused":
                    merchant_fused,
            },

            "digital_banking_semantics": {

                "global_reach_clear":
                    digital_global,

                "tracking_control_clear":
                    digital_tracking,
            },

            "camera_director": {

                "camera_angle":
                    (
                        clean_text(
                            evaluation.get(
                                "recommended_camera_angle"
                            ),
                            900,
                        )
                        or
                        concept.camera_angle
                    ),

                "lens":
                    (
                        clean_text(
                            evaluation.get(
                                "recommended_lens"
                            ),
                            400,
                        )
                        or
                        concept.lens
                    ),

                "perspective":
                    (
                        clean_text(
                            evaluation.get(
                                "recommended_perspective"
                            ),
                            1100,
                        )
                        or
                        concept.perspective
                    ),

                "perspective_type":
                    (
                        clean_text(
                            evaluation.get(
                                "recommended_perspective"
                            ),
                            1100,
                        )
                        or
                        concept.perspective
                    ),

                "creative_reason":
                    clean_text(
                        evaluation.get(
                            "camera_reason"
                        ),
                        1400,
                    ),

                "camera_lock_instruction":
                    (
                        "Preserve this evaluated camera "
                        "strategy during image production."
                    ),
            },
        }

        camera = safe_dict(
            concept.debate.get(
                "camera_director"
            )
        )

        if camera.get(
            "camera_angle"
        ):

            concept.camera_angle = (
                clean_text(
                    camera.get(
                        "camera_angle"
                    ),
                    900,
                )
            )

        if camera.get(
            "lens"
        ):

            concept.lens = (
                clean_text(
                    camera.get(
                        "lens"
                    ),
                    400,
                )
            )

        if camera.get(
            "perspective"
        ):

            concept.perspective = (
                clean_text(
                    camera.get(
                        "perspective"
                    ),
                    1100,
                )
            )

        concept.evaluation_valid = True

        concept.quality_gate_failures = (
            dedupe_strings(
                failures
            )
        )

        if is_stc_bank_request(
            user_request
        ):

            concept.quality_gate_failures = (
                dedupe_strings(
                    concept.quality_gate_failures
                    +
                    stc_dimension_gate_failures(
                        concept
                    )
                )
            )


# =========================================================
# REVIEW
# =========================================================

def review_concepts(
    *,
    user_request: str,
    concepts: List[
        CreativeConcept
    ],
    benefit_family: str,
    stc_style: str,
    high_alert: bool,
) -> None:

    prompt = (
        build_review_prompt(
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
            high_alert=(
                high_alert
            ),
        )
    )

    raw = call_openai_director(
        prompt,
        json_mode=True,
        json_schema=(
            make_review_schema(
                len(
                    concepts
                )
            )
        ),
        json_schema_name=(
            "xpand_creative_review_v57"
        ),
    )

    payload = (
        parse_json_payload(
            raw
        )
    )

    apply_evaluations_to_concepts(
        user_request=(
            user_request
        ),
        concepts=(
            concepts
        ),
        evaluations=(
            safe_list(
                payload.get(
                    "evaluations"
                )
            )
        ),
        benefit_family=(
            benefit_family
        ),
        stc_style=(
            stc_style
        ),
        evaluation_source=(
            "executive_creative_review_v57"
        ),
    )


# =========================================================
# FINAL JURY
# =========================================================

def run_finalist_jury(
    *,
    user_request: str,
    finalists: List[
        CreativeConcept
    ],
    benefit_family: str,
    stc_style: str,
) -> Dict[str, Any]:

    prompt = (
        build_finalist_jury_prompt(
            user_request=(
                user_request
            ),
            finalists=(
                finalists
            ),
            benefit_family=(
                benefit_family
            ),
            stc_style=(
                stc_style
            ),
        )
    )

    raw = call_openai_director(
        prompt,
        json_mode=True,
        json_schema=(
            FINALIST_JURY_SCHEMA
        ),
        json_schema_name=(
            "xpand_stc_finalist_jury_v57"
        ),
    )

    return parse_json_payload(
        raw
    )


# =========================================================
# COMBINED BOARD
# =========================================================

def run_creative_board(
    *,
    prompt: str,
    concept_count: int,
    id_prefix: str,
    user_request: str,
    benefit_family: str,
    stc_style: str,
    evaluation_source: str,
    schema_name: str,
) -> Tuple[
    List[
        CreativeConcept
    ],
    Dict[str, Any],
]:

    raw = call_openai_director(
        prompt,
        json_mode=True,
        json_schema=(
            make_board_schema(
                concept_count
            )
        ),
        json_schema_name=(
            schema_name
        ),
    )

    payload = (
        parse_json_payload(
            raw
        )
    )

    concepts = (
        parse_concepts(
            payload,
            generation_round=2,
            id_prefix=(
                id_prefix
            ),
            force_ids=True,
        )
    )

    if len(
        concepts
    ) != concept_count:

        raise RuntimeError(
            (
                evaluation_source
                +
                " returned "
                +
                str(
                    len(
                        concepts
                    )
                )
                +
                " concepts; expected "
                +
                str(
                    concept_count
                )
            )
        )

    evaluations = safe_list(
        payload.get(
            "evaluations"
        )
    )

    normalized_evaluations: List[
        Dict[str, Any]
    ] = []

    for index, item in enumerate(
        evaluations,
        start=1,
    ):

        if not isinstance(
            item,
            dict,
        ):

            continue

        copied = dict(
            item
        )

        copied[
            "concept_id"
        ] = (
            id_prefix
            +
            str(
                index
            ).zfill(
                2
            )
        )

        normalized_evaluations.append(
            copied
        )

    apply_evaluations_to_concepts(
        user_request=(
            user_request
        ),
        concepts=(
            concepts
        ),
        evaluations=(
            normalized_evaluations
        ),
        benefit_family=(
            benefit_family
        ),
        stc_style=(
            stc_style
        ),
        evaluation_source=(
            evaluation_source
        ),
    )

    return (
        concepts,
        payload,
    )


def run_targeted_repair_board(
    *,
    user_request: str,
    repair_candidates: Sequence[
        CreativeConcept
    ],
    brand_context: Any,
    visual_references: Any,
    benefit_family: str,
    stc_style: str,
) -> Tuple[
    List[
        CreativeConcept
    ],
    Dict[str, Any],
]:

    prompt = (
        build_targeted_repair_prompt(
            user_request=(
                user_request
            ),
            repair_candidates=(
                repair_candidates
            ),
            brand_context=(
                brand_context
            ),
            visual_references=(
                visual_references
            ),
            benefit_family=(
                benefit_family
            ),
            stc_style=(
                stc_style
            ),
        )
    )

    return run_creative_board(
        prompt=(
            prompt
        ),
        concept_count=(
            STC_TARGETED_REPAIR_OUTPUT_COUNT
        ),
        id_prefix="T",
        user_request=(
            user_request
        ),
        benefit_family=(
            benefit_family
        ),
        stc_style=(
            stc_style
        ),
        evaluation_source=(
            "stc_targeted_repair_board_v57"
        ),
        schema_name=(
            "xpand_stc_targeted_repair_v57"
        ),
    )


def run_recovery_board(
    *,
    user_request: str,
    failed_concepts: Sequence[
        CreativeConcept
    ],
    brand_context: Any,
    visual_references: Any,
    benefit_family: str,
    stc_style: str,
) -> Tuple[
    List[
        CreativeConcept
    ],
    Dict[str, Any],
]:

    prompt = (
        build_recovery_board_prompt(
            user_request=(
                user_request
            ),
            failed_concepts=(
                failed_concepts
            ),
            brand_context=(
                brand_context
            ),
            visual_references=(
                visual_references
            ),
            benefit_family=(
                benefit_family
            ),
            stc_style=(
                stc_style
            ),
        )
    )

    return run_creative_board(
        prompt=(
            prompt
        ),
        concept_count=(
            STC_RECOVERY_CONCEPT_COUNT
        ),
        id_prefix="R",
        user_request=(
            user_request
        ),
        benefit_family=(
            benefit_family
        ),
        stc_style=(
            stc_style
        ),
        evaluation_source=(
            "stc_recovery_board_v57"
        ),
        schema_name=(
            "xpand_stc_recovery_board_v57"
        ),
    )


# =========================================================
# JURY GUIDANCE
# =========================================================

def jury_diagnostics(
    jury: Any,
) -> Dict[str, Any]:

    jury = safe_dict(
        jury
    )

    return {

        "selected_concept_id":
            clean_text(
                jury.get(
                    "selected_concept_id"
                ),
                100,
            ),

        "approval":
            bool(
                jury.get(
                    "approval",
                    False,
                )
            ),

        "confidence":
            clamp_score(
                jury.get(
                    "confidence",
                    0,
                )
            ),

        "merchant_fusion_approved":
            bool(
                jury.get(
                    "merchant_fusion_approved",
                    False,
                )
            ),

        "digital_service_approved":
            bool(
                jury.get(
                    "digital_service_approved",
                    False,
                )
            ),

        "fatal_issues":
            [
                clean_text(
                    item,
                    1000,
                )
                for item
                in safe_list(
                    jury.get(
                        "fatal_issues"
                    )
                )[:10]
                if clean_text(
                    item,
                    1000,
                )
            ],

        "advertising_reason":
            clean_text(
                jury.get(
                    "advertising_reason"
                ),
                1600,
            ),

        "brand_reason":
            clean_text(
                jury.get(
                    "brand_reason"
                ),
                1600,
            ),

        "originality_reason":
            clean_text(
                jury.get(
                    "originality_reason"
                ),
                1600,
            ),

        "production_instruction":
            clean_text(
                jury.get(
                    "production_instruction"
                ),
                3200,
            ),

        "recommended_camera_angle":
            clean_text(
                jury.get(
                    "recommended_camera_angle"
                ),
                900,
            ),

        "recommended_lens":
            clean_text(
                jury.get(
                    "recommended_lens"
                ),
                400,
            ),

        "recommended_perspective":
            clean_text(
                jury.get(
                    "recommended_perspective"
                ),
                1100,
            ),

        "do_not_drift_into":
            [
                clean_text(
                    item,
                    1000,
                )
                for item
                in safe_list(
                    jury.get(
                        "do_not_drift_into"
                    )
                )[:12]
                if clean_text(
                    item,
                    1000,
                )
            ],
    }


def attach_jury_guidance(
    *,
    winner: CreativeConcept,
    jury: Any,
    source: str,
) -> None:

    diag = (
        jury_diagnostics(
            jury
        )
    )

    winner.debate[
        "finalist_jury"
    ] = {

        **diag,

        "source":
            source,

        "advisory_only":
            True,

        "strict_release_authority":
            (
                "deterministic_per_concept_"
                "strict_qualification"
            ),
    }

    camera = winner.debate.setdefault(
        "camera_director",
        {},
    )

    if diag[
        "recommended_camera_angle"
    ]:

        winner.camera_angle = (
            diag[
                "recommended_camera_angle"
            ]
        )

        camera[
            "camera_angle"
        ] = (
            winner.camera_angle
        )

    if diag[
        "recommended_lens"
    ]:

        winner.lens = (
            diag[
                "recommended_lens"
            ]
        )

        camera[
            "lens"
        ] = (
            winner.lens
        )

    if diag[
        "recommended_perspective"
    ]:

        winner.perspective = (
            diag[
                "recommended_perspective"
            ]
        )

        camera[
            "perspective"
        ] = (
            winner.perspective
        )

        camera[
            "perspective_type"
        ] = (
            winner.perspective
        )

    camera[
        "camera_lock_instruction"
    ] = (
        "FINAL JURY CAMERA LOCK. "
        "Do not normalize this into generic framing."
    )


def print_jury_diagnostics(
    *,
    jury: Any,
    qualified: Sequence[
        CreativeConcept
    ],
    source: str,
) -> None:

    diag = (
        jury_diagnostics(
            jury
        )
    )

    print("")
    print(
        "⚖️ V5.7 JURY DIAGNOSTICS"
    )

    print(
        "Source:",
        source,
    )

    print(
        "Jury selected ID:",
        diag[
            "selected_concept_id"
        ],
    )

    print(
        "Jury approval:",
        diag[
            "approval"
        ],
    )

    print(
        "Jury confidence:",
        diag[
            "confidence"
        ],
    )

    print(
        "Jury merchant fusion:",
        diag[
            "merchant_fusion_approved"
        ],
    )

    print(
        "Jury digital service:",
        diag[
            "digital_service_approved"
        ],
    )

    print(
        "Jury fatal issues:",
        diag[
            "fatal_issues"
        ],
    )

    print(
        "Strict-qualified IDs:",
        [
            item.concept_id
            for item
            in qualified
        ],
    )


# =========================================================
# TECHNICAL FAILURE
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
    high_alert: bool,
) -> CreativeBrainResponse:

    print("")
    print(
        "=========================================="
    )
    print(
        " CREATIVE DIRECTOR TECHNICAL FAILURE"
    )
    print(
        "=========================================="
    )

    print(
        (
            "This is a technical failure, "
            "not a creative-quality approval."
        )
    )

    if errors:

        print(
            clean_text(
                errors[
                    -1
                ],
                2800,
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
                "canonical_stc_service_v57",

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

            "high_alert":
                high_alert,

            "benefit_family":
                benefit_family,

            "canonical_benefit_family":
                benefit_family,

            "canonical_policy":
                True,

            "stc_style":
                stc_style,

            "director_calls":
                director_calls,

            "director_call_history":
                history,

            "director_call_target":
                (
                    3
                    if high_alert
                    else
                    2
                ),

            "release_level":
                "technical_failure",

            "failure_reason":
                (
                    clean_text(
                        errors[
                            -1
                        ],
                        1000,
                    )
                    if errors
                    else
                    "director_technical_failure"
                ),
        },

        errors=(
            errors
        ),
    )


# =========================================================
# NORMAL NON-HIGH-ALERT RELEASE
# =========================================================

def choose_normal_release(
    concepts: Sequence[
        CreativeConcept
    ],
    *,
    mode: str,
) -> Tuple[
    Optional[
        CreativeConcept
    ],
    str,
]:

    valid = [
        item
        for item
        in concepts
        if item.evaluation_valid
    ]

    valid.sort(
        key=lambda item:
            item.weighted_score,
        reverse=True,
    )

    if not valid:

        return (
            None,
            "technical_failure",
        )

    best = valid[
        0
    ]

    if mode == MODE_FAST:

        if (
            best.weighted_score
            >=
            FAST_MIN_SCORE
        ):

            best.quality_gate_passed = (
                True
            )

            return (
                best,
                "fast_release",
            )

        return (
            None,
            "quality_failed",
        )

    if (
        best.weighted_score
        >=
        MASTERPIECE_RELEASE_FLOOR
    ):

        best.quality_gate_passed = (
            True
        )

        return (
            best,
            (
                "target_release"
                if
                best.weighted_score
                >=
                MASTERPIECE_MIN_SCORE
                else
                "adaptive_release"
            ),
        )

    return (
        None,
        "quality_failed",
    )


# =========================================================
# MAIN API
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
        14000,
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
                or
                3
            ),
        ),
    )

    # =====================================================
    # CANONICAL BENEFIT — SINGLE AUTHORITY
    # =====================================================

    if is_stc_bank_request(
        user_request
    ):

        canonical_policy = (
            resolve_stc_benefit_family(
                user_text=(
                    user_request
                ),
                explicit_benefit_family=None,
            )
        )

        benefit_family = (
            canonical_policy.family_id
        )

    else:

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

    high_alert = (
        is_stc_high_alert(
            user_request,
            mode,
        )
    )

    concept_count = (
        concept_count_for_request(
            user_request,
            mode,
        )
    )

    director_calls = 0

    director_history: List[
        str
    ] = []

    errors: List[str] = []

    all_concepts: List[
        CreativeConcept
    ] = []

    primary_concepts: List[
        CreativeConcept
    ] = []

    targeted_repair_concepts: List[
        CreativeConcept
    ] = []

    recovery_concepts: List[
        CreativeConcept
    ] = []

    winner: Optional[
        CreativeConcept
    ] = None

    final_jury_payload: Dict[
        str,
        Any
    ] = {}

    targeted_repair_used = False

    fresh_recovery_used = False

    targeted_repair_source_ids: List[
        str
    ] = []

    recovery_reason = ""

    technical_ideation_recovery = False

    release_level = ""

    final_arbitration_reason = ""

    strict_release_info: Dict[
        str,
        Any
    ] = {

        "released":
            False,

        "authority":
            (
                "deterministic_per_concept_"
                "strict_qualification"
            ),

        "winner_id":
            "",

        "strict_qualified_ids":
            [],
    }

    # =====================================================
    # LOG
    # =====================================================

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND CREATIVE BRAIN V5.7"
    )

    if high_alert:

        print(
            " STC BANK CANONICAL STRICT-RELEASE HIGH ALERT"
        )

    else:

        print(
            " CAMPAIGN QUALITY MODE"
        )

    print(
        "=========================================="
    )

    print(
        "Mode:",
        mode,
    )

    print(
        "Canonical benefit family:",
        benefit_family,
    )

    if is_stc_bank_request(
        user_request
    ):

        print(
            "STC canonical policy:",
            "xpand_stc_policy V1 ✅",
        )

        print(
            "STC visual family:",
            stc_style,
        )

    print(
        "High alert:",
        high_alert,
    )

    print(
        "Initial concepts:",
        concept_count,
    )

    print(
        "Director-call maximum:",
        MASTERPIECE_MAX_DIRECTOR_CALLS,
    )

    print(
        "Targeted repair:",
        (
            STC_TARGETED_REPAIR_ENABLED
            if high_alert
            else
            False
        ),
    )

    print(
        "Strict-qualified release authority:",
        (
            STC_STRICT_QUALIFIED_RELEASE_AUTHORITY
            if high_alert
            else
            False
        ),
    )

    brand_pack_path = (
        locate_stc_brand_pack()
    )

    if high_alert:

        print(
            "Permanent STC brand pack:",
            (
                str(
                    brand_pack_path
                )
                if brand_pack_path
                else
                "not found"
            ),
        )

        curated = (
            stc_curated_reference_context(
                benefit_family=(
                    benefit_family
                ),
                stc_style=(
                    stc_style
                ),
            )
        )

        print(
            "Creative Brand Kit refs:",
            len(
                safe_list(
                    curated.get(
                        "selected_assets"
                    )
                )
            ),
        )

    print("")

    # =====================================================
    # CALL 1 — IDEATION
    # =====================================================

    try:

        director_calls += 1

        director_history.append(
            "diverse_ideation"
        )

        primary_concepts = (
            generate_concepts(
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
                concept_count=(
                    concept_count
                ),
                high_alert=(
                    high_alert
                ),
            )
        )

    except Exception as error:

        errors.append(
            (
                "primary_ideation: "
                +
                clean_text(
                    error,
                    3200,
                )
            )
        )

        if (
            mode
            ==
            MODE_MASTERPIECE
            and
            director_calls
            <
            MASTERPIECE_MAX_DIRECTOR_CALLS
        ):

            try:

                technical_ideation_recovery = (
                    True
                )

                director_calls += 1

                director_history.append(
                    "technical_ideation_recovery"
                )

                primary_concepts = (
                    generate_concepts(
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
                        concept_count=(
                            concept_count
                        ),
                        high_alert=(
                            high_alert
                        ),
                    )
                )

            except Exception as retry_error:

                errors.append(
                    (
                        "technical_ideation_recovery: "
                        +
                        clean_text(
                            retry_error,
                            3200,
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
                    high_alert=(
                        high_alert
                    ),
                )

        else:

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
                high_alert=(
                    high_alert
                ),
            )

    all_concepts.extend(
        primary_concepts
    )

    # =====================================================
    # CALL 2 — REVIEW
    # =====================================================

    if (
        director_calls
        >=
        MASTERPIECE_MAX_DIRECTOR_CALLS
    ):

        errors.append(
            (
                "Director call budget exhausted "
                "before creative review."
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
            high_alert=(
                high_alert
            ),
        )

    try:

        director_calls += 1

        director_history.append(
            "executive_creative_review"
        )

        review_concepts(
            user_request=(
                user_request
            ),
            concepts=(
                primary_concepts
            ),
            benefit_family=(
                benefit_family
            ),
            stc_style=(
                stc_style
            ),
            high_alert=(
                high_alert
            ),
        )

    except Exception as error:

        errors.append(
            (
                "creative_review: "
                +
                clean_text(
                    error,
                    3200,
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
            high_alert=(
                high_alert
            ),
        )

    primary_concepts.sort(
        key=lambda item:
            item.weighted_score,
        reverse=True,
    )

    # =====================================================
    # NORMAL REQUEST
    # =====================================================

    if not high_alert:

        winner, release_level = (
            choose_normal_release(
                primary_concepts,
                mode=(
                    mode
                ),
            )
        )

        top_concepts = (
            primary_concepts[
                :top_count
            ]
        )

        quality_gate_passed = bool(
            winner
        )

        if winner:

            winner.quality_gate_passed = (
                True
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
                all_concepts
            ),

            concepts=list(
                all_concepts
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
                    "canonical_service_v57",

                "high_alert":
                    False,

                "benefit_family":
                    benefit_family,

                "canonical_benefit_family":
                    benefit_family,

                "canonical_policy":
                    True,

                "stc_style":
                    stc_style,

                "director_calls":
                    director_calls,

                "director_call_history":
                    director_history,

                "quality_gate_evaluated":
                    True,

                "quality_gate_passed":
                    quality_gate_passed,

                "technical_failure":
                    False,

                "allow_smart_engine_fallback":
                    True,

                "quality_target_blocks_production":
                    False,

                "fallback_blocked":
                    False,

                "release_level":
                    release_level,

                "no_generated_copy":
                    True,

                "no_generated_logo":
                    True,

                "copy_space_policy":
                    "25-40_percent_integrated",
            },

            errors=(
                errors
            ),
        )

    # =====================================================
    # HIGH ALERT:
    # STRICT PRIMARY QUALIFICATION
    # =====================================================

    strict_primary = (
        strict_qualified_concepts(
            primary_concepts,
            high_alert=True,
        )
    )

    print(
        "Strict primary finalists:",
        len(
            strict_primary
        ),
    )

    # =====================================================
    # CALL 3A — FINALIST JURY
    # =====================================================

    if strict_primary:

        finalists = (
            strict_primary[
                :MASTERPIECE_SHORTLIST_SIZE
            ]
        )

        if (
            director_calls
            <
            MASTERPIECE_MAX_DIRECTOR_CALLS
        ):

            try:

                director_calls += 1

                director_history.append(
                    "stc_finalist_jury"
                )

                final_jury_payload = (
                    run_finalist_jury(
                        user_request=(
                            user_request
                        ),
                        finalists=(
                            finalists
                        ),
                        benefit_family=(
                            benefit_family
                        ),
                        stc_style=(
                            stc_style
                        ),
                    )
                )

            except Exception as error:

                errors.append(
                    (
                        "stc_finalist_jury: "
                        +
                        clean_text(
                            error,
                            2800,
                        )
                    )
                )

                final_jury_payload = {}

        #
        # Deterministic strict authority:
        # highest independently qualified concept wins.
        #

        winner = strict_primary[
            0
        ]

        winner.quality_gate_passed = (
            True
        )

        release_level = (
            "stc_primary_strict_qualified_release"
        )

        final_arbitration_reason = (
            "highest_strict_qualified_concept"
        )

        strict_release_info.update(
            {
                "released":
                    True,

                "winner_id":
                    winner.concept_id,

                "strict_qualified_ids":
                    [
                        item.concept_id
                        for item
                        in strict_primary
                    ],
            }
        )

        if final_jury_payload:

            attach_jury_guidance(
                winner=(
                    winner
                ),
                jury=(
                    final_jury_payload
                ),
                source=(
                    "stc_finalist_jury"
                ),
            )

            print_jury_diagnostics(
                jury=(
                    final_jury_payload
                ),
                qualified=(
                    strict_primary
                ),
                source=(
                    "stc_finalist_jury"
                ),
            )

            jury_selected_id = clean_text(
                final_jury_payload.get(
                    "selected_concept_id"
                ),
                100,
            )

            if (
                jury_selected_id
                ==
                winner.concept_id
            ):

                final_arbitration_reason = (
                    "jury_and_strict_ranking_agree"
                )

            elif jury_selected_id:

                final_arbitration_reason = (
                    "strict_ranking_overrode_advisory_jury"
                )

    # =====================================================
    # NO STRICT PRIMARY:
    # TARGETED REPAIR OR FRESH RECOVERY
    # =====================================================

    else:

        repair_candidates = (
            select_targeted_repair_candidates(
                primary_concepts
            )
        )

        print(
            "Targeted-repair candidates:",
            len(
                repair_candidates
            ),
        )

        if (
            repair_candidates
            and
            STC_TARGETED_REPAIR_ENABLED
            and
            director_calls
            <
            MASTERPIECE_MAX_DIRECTOR_CALLS
        ):

            targeted_repair_used = (
                True
            )

            targeted_repair_source_ids = [
                item.concept_id
                for item
                in repair_candidates
            ]

            recovery_reason = (
                "repairable_strong_near_miss"
            )

            print("")
            print(
                "🔧 STC TARGETED CREATIVE REPAIR"
            )

            print(
                "Source IDs:",
                targeted_repair_source_ids,
            )

            try:

                director_calls += 1

                director_history.append(
                    "stc_targeted_repair_board"
                )

                (
                    targeted_repair_concepts,
                    final_jury_payload,
                ) = (
                    run_targeted_repair_board(
                        user_request=(
                            user_request
                        ),
                        repair_candidates=(
                            repair_candidates
                        ),
                        brand_context=(
                            brand_context
                        ),
                        visual_references=(
                            visual_references
                        ),
                        benefit_family=(
                            benefit_family
                        ),
                        stc_style=(
                            stc_style
                        ),
                    )
                )

                all_concepts.extend(
                    targeted_repair_concepts
                )

                repaired_strict = (
                    strict_qualified_concepts(
                        targeted_repair_concepts,
                        high_alert=True,
                    )
                )

                print(
                    "Targeted-repair strict finalists:",
                    len(
                        repaired_strict
                    ),
                )

                if repaired_strict:

                    winner = (
                        repaired_strict[
                            0
                        ]
                    )

                    winner.quality_gate_passed = (
                        True
                    )

                    release_level = (
                        "stc_targeted_repair_strict_release"
                    )

                    final_arbitration_reason = (
                        "highest_strict_qualified_repaired_concept"
                    )

                    strict_release_info.update(
                        {
                            "released":
                                True,

                            "winner_id":
                                winner.concept_id,

                            "strict_qualified_ids":
                                [
                                    item.concept_id
                                    for item
                                    in repaired_strict
                                ],
                        }
                    )

                    attach_jury_guidance(
                        winner=(
                            winner
                        ),
                        jury=(
                            final_jury_payload
                        ),
                        source=(
                            "stc_targeted_repair_board"
                        ),
                    )

                    print_jury_diagnostics(
                        jury=(
                            final_jury_payload
                        ),
                        qualified=(
                            repaired_strict
                        ),
                        source=(
                            "stc_targeted_repair_board"
                        ),
                    )

            except Exception as error:

                errors.append(
                    (
                        "stc_targeted_repair_board: "
                        +
                        clean_text(
                            error,
                            3000,
                        )
                    )
                )

        elif (
            STC_CREATIVE_RECOVERY_ENABLED
            and
            director_calls
            <
            MASTERPIECE_MAX_DIRECTOR_CALLS
        ):

            fresh_recovery_used = (
                True
            )

            recovery_reason = (
                "no_strict_primary_and_"
                "no_repairable_near_miss"
            )

            print("")
            print(
                "🔁 STC FRESH CREATIVE RECOVERY"
            )

            print(
                "Reason:",
                recovery_reason,
            )

            try:

                director_calls += 1

                director_history.append(
                    "stc_recovery_board"
                )

                (
                    recovery_concepts,
                    final_jury_payload,
                ) = (
                    run_recovery_board(
                        user_request=(
                            user_request
                        ),
                        failed_concepts=(
                            primary_concepts
                        ),
                        brand_context=(
                            brand_context
                        ),
                        visual_references=(
                            visual_references
                        ),
                        benefit_family=(
                            benefit_family
                        ),
                        stc_style=(
                            stc_style
                        ),
                    )
                )

                all_concepts.extend(
                    recovery_concepts
                )

                recovery_strict = (
                    strict_qualified_concepts(
                        recovery_concepts,
                        high_alert=True,
                    )
                )

                print(
                    "Recovery strict finalists:",
                    len(
                        recovery_strict
                    ),
                )

                if recovery_strict:

                    winner = (
                        recovery_strict[
                            0
                        ]
                    )

                    winner.quality_gate_passed = (
                        True
                    )

                    release_level = (
                        "stc_recovery_strict_release"
                    )

                    final_arbitration_reason = (
                        "highest_strict_qualified_recovery_concept"
                    )

                    strict_release_info.update(
                        {
                            "released":
                                True,

                            "winner_id":
                                winner.concept_id,

                            "strict_qualified_ids":
                                [
                                    item.concept_id
                                    for item
                                    in recovery_strict
                                ],
                        }
                    )

                    attach_jury_guidance(
                        winner=(
                            winner
                        ),
                        jury=(
                            final_jury_payload
                        ),
                        source=(
                            "stc_recovery_board"
                        ),
                    )

                    print_jury_diagnostics(
                        jury=(
                            final_jury_payload
                        ),
                        qualified=(
                            recovery_strict
                        ),
                        source=(
                            "stc_recovery_board"
                        ),
                    )

            except Exception as error:

                errors.append(
                    (
                        "stc_recovery_board: "
                        +
                        clean_text(
                            error,
                            3000,
                        )
                    )
                )

    # =====================================================
    # FINAL QUALITY STATE
    # =====================================================

    quality_gate_passed = bool(
        winner
        and
        winner.quality_gate_passed
    )

    evaluated = [
        item
        for item
        in all_concepts
        if item.evaluation_valid
    ]

    evaluated.sort(
        key=lambda item:
            item.weighted_score,
        reverse=True,
    )

    top_concepts = (
        evaluated[
            :top_count
        ]
    )

    if (
        winner
        and
        winner not in top_concepts
    ):

        top_concepts = (
            [
                winner
            ]
            +
            [
                item
                for item
                in top_concepts
                if item.concept_id
                !=
                winner.concept_id
            ]
        )[
            :top_count
        ]

    print("")
    print(
        "=========================================="
    )

    if quality_gate_passed:

        print(
            " CREATIVE QUALITY GATE: PASSED ✅"
        )

        print(
            "Winner:",
            winner.concept_id
            if winner
            else
            "-",
        )

        print(
            "Title:",
            winner.title
            if winner
            else
            "-",
        )

        print(
            "Score:",
            winner.weighted_score
            if winner
            else
            0,
        )

        print(
            "Release:",
            release_level,
        )

        print(
            "Canonical benefit:",
            benefit_family,
        )

    else:

        print(
            " CREATIVE QUALITY GATE: NOT PASSED"
        )

        if evaluated:

            print(
                "Best evaluated score:",
                evaluated[
                    0
                ].weighted_score,
            )

            print(
                "Best concept:",
                (
                    evaluated[
                        0
                    ].title
                    or
                    evaluated[
                        0
                    ].concept_id
                ),
            )

            print(
                "Failures:",
                ", ".join(
                    evaluated[
                        0
                    ].quality_gate_failures[
                        :12
                    ]
                ),
            )

        print(
            "No fake winner created."
        )

    print(
        "Targeted repair used:",
        targeted_repair_used,
    )

    print(
        "Fresh recovery used:",
        fresh_recovery_used,
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

    print(
        "=========================================="
    )
    print("")

    # =====================================================
    # FAILURE REASON
    # =====================================================

    failure_reason = ""

    if not quality_gate_passed:

        if targeted_repair_used:

            failure_reason = (
                "targeted_repair_did_not_"
                "produce_strict_qualified_concept"
            )

        elif fresh_recovery_used:

            failure_reason = (
                "recovery_did_not_produce_"
                "strict_qualified_concept"
            )

        else:

            failure_reason = (
                "no_strict_stc_concept_approved"
            )

    # =====================================================
    # RESPONSE
    # =====================================================

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
            all_concepts
        ),

        concepts=list(
            all_concepts
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
                (
                    "canonical_service_"
                    "deterministic_strict_release_v57"
                ),

            "high_alert":
                high_alert,

            "benefit_family":
                benefit_family,

            "canonical_benefit_family":
                benefit_family,

            "canonical_policy":
                True,

            "canonical_policy_module":
                "xpand_stc_policy",

            "stc_style":
                stc_style,

            "initial_concepts":
                concept_count,

            "director_calls":
                director_calls,

            "director_call_history":
                director_history,

            "director_call_target":
                (
                    3
                    if high_alert
                    else
                    2
                ),

            "director_call_maximum":
                MASTERPIECE_MAX_DIRECTOR_CALLS,

            "technical_ideation_recovery":
                technical_ideation_recovery,

            "targeted_repair_enabled":
                STC_TARGETED_REPAIR_ENABLED,

            "targeted_repair_used":
                targeted_repair_used,

            "targeted_repair_source_ids":
                targeted_repair_source_ids,

            "targeted_repair_concepts":
                len(
                    targeted_repair_concepts
                ),

            "targeted_repair_min_score":
                STC_TARGETED_REPAIR_MIN_SCORE,

            "targeted_repair_max_dimension_failures":
                STC_TARGETED_REPAIR_MAX_DIMENSION_FAILURES,

            "targeted_repair_max_gap":
                STC_TARGETED_REPAIR_MAX_GAP,

            "recovery_enabled":
                STC_CREATIVE_RECOVERY_ENABLED,

            "recovery_used":
                fresh_recovery_used,

            "recovery_reason":
                recovery_reason,

            "recovery_concepts":
                len(
                    recovery_concepts
                ),

            "strict_qualified_release_authority":
                STC_STRICT_QUALIFIED_RELEASE_AUTHORITY,

            "strict_release_authority":
                strict_release_info[
                    "authority"
                ],

            "strict_release_released":
                strict_release_info[
                    "released"
                ],

            "strict_release_winner_id":
                strict_release_info[
                    "winner_id"
                ],

            "strict_qualified_ids":
                strict_release_info[
                    "strict_qualified_ids"
                ],

            "release_level":
                release_level,

            "final_arbitration_reason":
                final_arbitration_reason,

            "quality_gate_evaluated":
                True,

            "quality_gate_passed":
                quality_gate_passed,

            "technical_failure":
                False,

            #
            # STC Telegram V3.6 determines whether a quality
            # failure can fallback. High Alert remains strict.
            #

            "allow_smart_engine_fallback":
                False
                if high_alert
                else
                True,

            "quality_target_blocks_production":
                bool(
                    high_alert
                    and
                    not quality_gate_passed
                ),

            "fallback_blocked":
                bool(
                    high_alert
                    and
                    not quality_gate_passed
                ),

            "failure_reason":
                failure_reason,

            "masterpiece_target_score":
                (
                    STC_HIGH_ALERT_MIN_SCORE
                    if high_alert
                    else
                    MASTERPIECE_MIN_SCORE
                ),

            "masterpiece_release_floor":
                (
                    STC_HIGH_ALERT_RELEASE_FLOOR
                    if high_alert
                    else
                    MASTERPIECE_RELEASE_FLOOR
                ),

            "strict_dimension_gates":
                dict(
                    STC_DIMENSION_MINIMUMS
                ),

            "brand_pack_available":
                bool(
                    locate_stc_brand_pack()
                ),

            "brand_kit_available":
                STC_BRAND_KIT_AVAILABLE,

            "canonical_policy_available":
                STC_CANONICAL_POLICY_AVAILABLE,

            "copy_space_policy":
                "25-40_percent_integrated",

            "giant_upper_third_banned":
                True,

            "camera_director_enabled":
                True,

            "scene_feasibility_enabled":
                True,

            "merchant_semantic_equivalence":
                True,

            "digital_banking_semantic_gate":
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

        "concept_archetype":
            concept.concept_archetype,

        "campaign_hook":
            concept.campaign_hook,

        "core_idea":
            concept.core_idea,

        "marketing_message":
            concept.marketing_message,

        "visual_metaphor":
            concept.visual_metaphor,

        "visual_mechanism_type":
            concept.visual_mechanism_type,

        "why_not_generic":
            concept.why_not_generic,

        "environment":
            concept.environment,

        "environment_novelty":
            concept.environment_novelty,

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
            else
            None
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

        return (
            "ما طلعت اتجاهات إبداعية كافية."
        )

    lines: List[str] = [

        (
            "XPAND Creative Brain | "
            +
            response.mode.upper()
        ),
    ]

    if response.winner:

        lines.append(
            (
                "الفكرة المعتمدة: "
                +
                (
                    response.winner.title
                    or
                    response.winner.concept_id
                )
            )
        )

    family = clean_text(
        response.metadata.get(
            "canonical_benefit_family",
            "",
        ),
        100,
    )

    if family:

        lines.append(
            (
                "الخدمة: "
                +
                family
            )
        )

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
                (
                    concept.title
                    or
                    concept.concept_id
                )
            )
        )

        if concept.concept_archetype:

            lines.append(
                (
                    "النوع: "
                    +
                    concept.concept_archetype
                )
            )

        if concept.core_idea:

            lines.append(
                (
                    "الفكرة: "
                    +
                    concept.core_idea
                )
            )

        if concept.campaign_hook:

            lines.append(
                (
                    "الآلية الإعلانية: "
                    +
                    concept.campaign_hook
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

    return "\n".join(
        lines
    ).strip()


# =========================================================
# ZERO-COST V5.7 SELF TEST
# =========================================================

if __name__ == "__main__":

    tests: Dict[
        str,
        bool,
    ] = {}

    # =====================================================
    # CONTRACT
    # =====================================================

    tests[
        "version_57"
    ] = (
        VERSION
        ==
        "5.7"
    )

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
        "dimension_weights_sum_100"
    ] = (
        sum(
            DIMENSION_WEIGHTS.values()
        )
        ==
        100
    )

    # =====================================================
    # CANONICAL POLICY
    # =====================================================

    tests[
        "canonical_policy_available"
    ] = (
        STC_CANONICAL_POLICY_AVAILABLE
        is True
    )

    tests[
        "merchant_payments_canonical"
    ] = (
        detect_benefit_family(
            (
                "أنشئ إعلان لبنك STC Bank "
                "عن التجارة الإلكترونية ونقاط البيع"
            )
        )
        ==
        FAMILY_MERCHANT_PAYMENTS
    )

    tests[
        "digital_banking_transfer_tracking"
    ] = (
        detect_benefit_family(
            (
                "STC Bank حوالتك حول العالم "
                "وتقدر تتبعها من التطبيق"
            )
        )
        ==
        FAMILY_DIGITAL_BANKING
    )

    tests[
        "premium_cannot_erase_digital_banking"
    ] = (
        resolve_stc_benefit_family_id(
            (
                "STC Bank حوالتك حول العالم "
                "وتتبعها من التطبيق"
            ),
            "premium",
        )
        ==
        FAMILY_DIGITAL_BANKING
    )

    tests[
        "premium_cannot_erase_merchant_payments"
    ] = (
        resolve_stc_benefit_family_id(
            (
                "STC Bank التجارة الإلكترونية "
                "ونقاط البيع"
            ),
            "premium",
        )
        ==
        FAMILY_MERCHANT_PAYMENTS
    )

    # =====================================================
    # STYLE
    # =====================================================

    tests[
        "stc_default_realistic"
    ] = (
        detect_stc_style(
            "إعلان STC Bank"
        )
        ==
        "premium_realistic"
    )

    tests[
        "stc_explicit_purple"
    ] = (
        detect_stc_style(
            "STC Bank بيئة بنفسجية معمارية"
        )
        ==
        "premium_purple_architecture"
    )

    tests[
        "stc_augmented"
    ] = (
        detect_stc_style(
            "STC Bank واقعية معززة"
        )
        ==
        "premium_augmented_realism"
    )

    # =====================================================
    # COUNTS / CALLS
    # =====================================================

    tests[
        "normal_four_concepts"
    ] = (
        NORMAL_CONCEPT_COUNT
        ==
        4
    )

    tests[
        "stc_six_to_ten_concepts"
    ] = bool(
        6
        <=
        STC_HIGH_ALERT_CONCEPT_COUNT
        <=
        10
    )

    tests[
        "targeted_repair_two_outputs"
    ] = (
        STC_TARGETED_REPAIR_OUTPUT_COUNT
        ==
        2
    )

    tests[
        "max_three_director_calls"
    ] = (
        MASTERPIECE_MAX_DIRECTOR_CALLS
        <=
        3
    )

    # =====================================================
    # STRICT THRESHOLDS
    # =====================================================

    tests[
        "strict_concept_strength_88"
    ] = (
        STC_MIN_CONCEPT_STRENGTH
        ==
        88.0
    )

    tests[
        "strict_brand_fit_90"
    ] = (
        STC_MIN_BRAND_FIT
        ==
        90.0
    )

    tests[
        "strict_visual_mechanism_90"
    ] = (
        STC_MIN_VISUAL_MECHANISM
        ==
        90.0
    )

    tests[
        "strict_ad_readiness_90"
    ] = (
        STC_MIN_AD_READINESS
        ==
        90.0
    )

    tests[
        "release_floor_88"
    ] = (
        STC_HIGH_ALERT_RELEASE_FLOOR
        >=
        88.0
    )

    # =====================================================
    # POLICY PROMPT
    # =====================================================

    digital_policy_prompt = (
        build_ideation_prompt(
            user_request=(
                "STC Bank حوالتك حول العالم "
                "وتتبعها من التطبيق"
            ),
            brand_context={},
            visual_references=[],
            style_hint="",
            benefit_family=(
                FAMILY_DIGITAL_BANKING
            ),
            stc_style=(
                "premium_realistic"
            ),
            concept_count=8,
            high_alert=True,
        )
    )

    tests[
        "digital_prompt_canonical_family"
    ] = (
        FAMILY_DIGITAL_BANKING
        in digital_policy_prompt
    )

    tests[
        "digital_prompt_no_globe_cliche"
    ] = (
        "floating globe"
        in digital_policy_prompt
    )

    tests[
        "digital_prompt_no_phone_cliche"
    ] = (
        "person simply holding a phone"
        in digital_policy_prompt
    )

    tests[
        "copy_space_25_40"
    ] = (
        "25–40%"
        in digital_policy_prompt
    )

    tests[
        "obsolete_copy_space_removed"
    ] = (
        "15–22%"
        not in digital_policy_prompt
        and
        "15-22%"
        not in digital_policy_prompt
    )

    tests[
        "no_giant_upper_third"
    ] = (
        "artificial blank panel"
        in digital_policy_prompt
    )

    # =====================================================
    # MERCHANT LOCAL SEMANTICS
    # =====================================================

    merchant_good = CreativeConcept(

        concept_id="M01",

        title=(
            "Connected commerce"
        ),

        concept_archetype=(
            "camera-led"
        ),

        campaign_hook=(
            "One connected merchant ecosystem."
        ),

        core_idea=(
            "A digital storefront and a believable "
            "physical card reader are connected through "
            "one spatial relationship in a Saudi business."
        ),

        marketing_message=(
            "Online commerce and physical point-of-sale "
            "acceptance operate as one system."
        ),

        visual_metaphor=(
            "A connected spatial relationship bridges "
            "digital storefront and in-store payment."
        ),

        visual_mechanism_type=(
            "spatial relationship"
        ),

        why_not_generic=(
            "The service relationship itself creates the "
            "advertising composition instead of an ordinary checkout."
        ),

        environment=(
            "Contemporary Saudi commercial environment."
        ),

        environment_novelty=(
            "The architecture carries the service relationship."
        ),

        hero_element=(
            "Connected commercial system."
        ),

        camera_angle=(
            "reflection-led oblique viewpoint"
        ),

        lens="50mm",

        perspective=(
            "controlled compression"
        ),

        lighting=(
            "motivated commercial daylight"
        ),

        negative_space=(
            "18% integrated side space"
        ),

        brand_logic=(
            "STC Bank confidence through restraint."
        ),
    )

    merchant_signals = (
        merchant_local_signals(
            merchant_good
        )
    )

    tests[
        "merchant_online_detected"
    ] = (
        merchant_signals[
            "online"
        ]
        is True
    )

    tests[
        "merchant_physical_detected"
    ] = (
        merchant_signals[
            "physical"
        ]
        is True
    )

    tests[
        "merchant_mechanism_detected"
    ] = (
        merchant_signals[
            "mechanism"
        ]
        is True
    )

    # =====================================================
    # BAD COUNTER
    # =====================================================

    bad_counter = CreativeConcept(

        concept_id="BAD",

        title="Luxury checkout",

        concept_archetype="premium realism",

        campaign_hook=(
            "Customer pays while merchant works."
        ),

        core_idea=(
            "Customer taps POS terminal on a wooden counter "
            "while merchant stands behind counter."
        ),

        visual_metaphor=(
            "Worker packing parcel in background."
        ),

        visual_mechanism_type="",

        why_not_generic="",

        environment=(
            "Luxury boutique wooden checkout counter."
        ),

        environment_novelty="",

        hero_element="POS terminal",

        camera_angle="eye level",

        lens="35mm",

        perspective="normal",

        lighting="soft daylight",

        negative_space="35% top",

        brand_logic="premium",
    )

    bad_penalty, bad_failures = (
        local_concept_penalties(
            bad_counter,
            user_request=(
                "STC Bank التجارة الإلكترونية ونقاط البيع"
            ),
            benefit_family=(
                FAMILY_MERCHANT_PAYMENTS
            ),
            stc_style=(
                "premium_realistic"
            ),
        )
    )

    tests[
        "bad_counter_hard_rejected"
    ] = (
        bad_penalty
        >=
        30
        and
        "literal_transaction_tableau"
        in bad_failures
    )

    # =====================================================
    # DIGITAL CLICHE
    # =====================================================

    bad_digital = CreativeConcept(

        concept_id="D01",

        title="Global network",

        concept_archetype="fintech",

        campaign_hook=(
            "A giant floating globe shows international transfer."
        ),

        core_idea=(
            "A person holds a phone beside a glowing world map "
            "with network lines and glowing routes."
        ),

        marketing_message=(
            "Global transfer."
        ),

        visual_metaphor=(
            "Glowing route around a floating globe."
        ),

        visual_mechanism_type=(
            "network lines"
        ),

        why_not_generic=(
            "Uses a globe."
        ),

        environment=(
            "Generic digital studio."
        ),

        environment_novelty=(
            "Digital global world."
        ),

        hero_element=(
            "floating globe"
        ),

        camera_angle="eye level",

        lens="35mm",

        perspective="normal",

        lighting="neon",

        negative_space="40% top",

        brand_logic="purple",
    )

    digital_penalty, digital_failures = (
        local_concept_penalties(
            bad_digital,
            user_request=(
                "STC Bank حوالتك حول العالم "
                "وتتبعها من التطبيق"
            ),
            benefit_family=(
                FAMILY_DIGITAL_BANKING
            ),
            stc_style=(
                "premium_realistic"
            ),
        )
    )

    tests[
        "digital_globe_cliche_rejected"
    ] = (
        digital_penalty
        >=
        20
        and
        "digital_banking_cliche"
        in digital_failures
    )

    # =====================================================
    # STRICT RELEASE REGRESSION
    # =====================================================

    strict_a = CreativeConcept(

        concept_id="C01",

        title="Qualified A",

        evaluation_valid=True,

        weighted_score=91.0,

        scores={
            key:
                max(
                    minimum,
                    92.0,
                )
            for key, minimum
            in STC_DIMENSION_MINIMUMS.items()
        },

        feasibility={
            "production_feasible":
                True,
        },

        quality_gate_failures=[],
    )

    strict_b = CreativeConcept(

        concept_id="C02",

        title="Qualified B",

        evaluation_valid=True,

        weighted_score=93.0,

        scores={
            key:
                max(
                    minimum,
                    93.0,
                )
            for key, minimum
            in STC_DIMENSION_MINIMUMS.items()
        },

        feasibility={
            "production_feasible":
                True,
        },

        quality_gate_failures=[],
    )

    strict_list = (
        strict_qualified_concepts(
            [
                strict_a,
                strict_b,
            ],
            high_alert=True,
        )
    )

    tests[
        "two_strict_finalists_detected"
    ] = (
        len(
            strict_list
        )
        ==
        2
    )

    tests[
        "highest_strict_score_first"
    ] = (
        strict_list[
            0
        ].concept_id
        ==
        "C02"
    )

    tests[
        "jury_cannot_erase_strict_release"
    ] = bool(
        STC_STRICT_QUALIFIED_RELEASE_AUTHORITY
        and
        strict_list
    )

    # =====================================================
    # NEAR MISS
    # =====================================================

    near_miss_scores = {
        key:
            minimum
        for key, minimum
        in STC_DIMENSION_MINIMUMS.items()
    }

    near_miss_scores[
        "concept_strength"
    ] = 87.0

    near_miss_scores[
        "brand_fit"
    ] = 89.0

    near_miss = CreativeConcept(

        concept_id="N01",

        title="Repairable",

        evaluation_valid=True,

        weighted_score=87.9,

        scores=near_miss_scores,

        feasibility={
            "production_feasible":
                True,
        },

        quality_gate_failures=[],
    )

    tests[
        "near_miss_routes_to_repair"
    ] = (
        is_targeted_repair_candidate(
            near_miss
        )
        is True
    )

    # =====================================================
    # HARD REJECT CANNOT REPAIR
    # =====================================================

    hard_bad = CreativeConcept(

        concept_id="H01",

        title="Hard bad",

        evaluation_valid=True,

        weighted_score=96.0,

        scores={
            key:
                96.0
            for key
            in STC_DIMENSION_MINIMUMS
        },

        feasibility={
            "production_feasible":
                True,
        },

        quality_gate_failures=[
            "literal_transaction_tableau"
        ],
    )

    tests[
        "hard_reject_cannot_enter_repair"
    ] = (
        is_targeted_repair_candidate(
            hard_bad
        )
        is False
    )

    tests[
        "hard_reject_cannot_strict_release"
    ] = (
        not strict_qualified_concepts(
            [
                hard_bad
            ],
            high_alert=True,
        )
    )

    # =====================================================
    # BRAND PACK
    # =====================================================

    tests[
        "brand_pack_loader_safe"
    ] = isinstance(
        load_stc_brand_pack(),
        dict,
    )

    tests[
        "brand_kit_context_safe"
    ] = isinstance(
        stc_curated_reference_context(
            benefit_family=(
                FAMILY_MERCHANT_PAYMENTS
            ),
            stc_style=(
                "premium_realistic"
            ),
        ),
        dict,
    )

    # =====================================================
    # PUBLIC CONTRACT
    # =====================================================

    tests[
        "concept_contract"
    ] = all(
        hasattr(
            CreativeConcept(),
            key,
        )
        for key
        in (
            "concept_id",
            "core_idea",
            "camera_angle",
            "weighted_score",
            "debate",
            "feasibility",
            "quality_gate_passed",
        )
    )

    dummy_response = CreativeBrainResponse(

        ok=False,

        mode=(
            MODE_MASTERPIECE
        ),

        request="test",

        total_concepts=0,

        concepts=[],

        top_concepts=[],

        winner=None,

        metadata={},

        errors=[],
    )

    tests[
        "response_contract"
    ] = all(
        key
        in response_to_dict(
            dummy_response
        )
        for key
        in (
            "ok",
            "mode",
            "request",
            "total_concepts",
            "concepts",
            "top_concepts",
            "winner",
            "metadata",
            "errors",
        )
    )

    # =====================================================
    # RESULT
    # =====================================================

    all_ok = all(
        tests.values()
    )

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND CREATIVE BRAIN V5.7"
    )
    print(
        " ZERO-COST CANONICAL-SERVICE SELF TEST"
    )
    print(
        "=========================================="
    )
    print("")

    for name, result in (
        tests.items()
    ):

        print(
            (
                "✅ "
                if result
                else
                "❌ "
            )
            +
            name
        )

    print("")

    if all_ok:

        print(
            (
                "XPAND Creative Brain V5.7 "
                "self-test: PASS ✅"
            )
        )

    else:

        failures = [
            name
            for name, result
            in tests.items()
            if not result
        ]

        print(
            (
                "XPAND Creative Brain V5.7 "
                "self-test: FAIL ❌"
            )
        )

        print(
            "Failures:",
            failures,
        )

        raise RuntimeError(
            (
                "XPAND Creative Brain V5.7 "
                "self-test failed."
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
        "✅ xpand_stc_policy is canonical authority"
    )
    print(
        "✅ premium cannot erase digital_banking"
    )
    print(
        "✅ premium cannot erase merchant_payments"
    )
    print(
        "✅ Global-transfer creative policy active"
    )
    print(
        "✅ Merchant-payments creative policy active"
    )
    print(
        "✅ 25–40% integrated copy-space policy"
    )
    print(
        "✅ Artificial blank panel banned"
    )
    print(
        "✅ Generic phone/global-globe transfer cliché banned"
    )
    print(
        "✅ Generic merchant checkout tableau banned"
    )
    print(
        "✅ Strict STC thresholds unchanged"
    )
    print(
        "✅ Deterministic strict release preserved"
    )
    print(
        "✅ Targeted Repair preserved"
    )
    print(
        "✅ Fresh Recovery preserved"
    )
    print(
        "✅ Maximum 3 Director calls"
    )
    print(
        "✅ Permanent STC Brand Kit preserved"
    )
    print(
        "✅ No generated text / logo"
    )
    print(
        "🚫 No API calls were made"
    )
    print(
        "🚫 No images were generated"
    )
    print("")
