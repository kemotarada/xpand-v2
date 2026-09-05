# =========================================================
# XPAND UNIFIED VISUAL RUNTIME V3.3
#
# STABLE TELEGRAM IMAGE RUNTIME
#
# Telegram Text / Voice
#        ↓
# Brand Detection
#        ↓
# Brand Research / Memory
#        ↓
# Semantic Benefit Director
#        ↓
# Creative Brain
#        ↓
# Runtime State Classifier
#        ↓
# Masterpiece Production
#        ↓
# Smart Engine Fallback
#        ↓
# Telegram Delivery
#
# IMPORTANT
# ---------------------------------------------------------
# - technical Creative Brain failure != quality failure
# - technical failure NEVER blocks normal image generation
# - Smart Engine fallback remains available
# - install(core) is always available
# - no shell commands belong in this file
# =========================================================

from __future__ import annotations

import io
import json
import os
import re

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
)

import requests


# =========================================================
# COST GUARD
# =========================================================

try:
    from xpand_cost_guard import budget_status
except Exception:

    def budget_status() -> Dict[str, Any]:
        return {
            "enabled": False,
            "limit_usd": 0.0,
            "reserved_usd": 0.0,
            "remaining_usd": 0.0,
        }


# =========================================================
# BASE IMAGE ENGINE
# =========================================================

from xpand_image_engine import (
    ENGINE_VERSION as SMART_ENGINE_VERSION,
    detect_image_size,
    generate_image,
    get_image_engine_status,
)


# =========================================================
# BRAND RESEARCH
# =========================================================

from xpand_brand_research import (
    BRAND_PROFILES,
    build_researched_prompt,
    detect_brand,
    should_apply_deep_research,
)


# =========================================================
# BRAND MEMORY
# =========================================================

from xpand_brand_memory import (
    build_brand_memory_context,
    get_active_brand,
    safe_brand_id,
    set_active_brand,
    upsert_brand_profile,
)


# =========================================================
# CREATIVE BRAIN
# =========================================================

from xpand_creative_brain import (
    MODE_FAST as CREATIVE_MODE_FAST,
    MODE_MASTERPIECE as CREATIVE_MODE_MASTERPIECE,
    concept_to_dict,
    run_creative_brain,
)


# =========================================================
# PRODUCTION ENGINE
# =========================================================

from xpand_production_engine import (
    MODE_MASTERPIECE as PRODUCTION_MODE_MASTERPIECE,
    TARGET_GEMINI,
    run_production,
)


# =========================================================
# CAMPAIGN ENGINE
# =========================================================

try:
    from xpand_campaign_engine import (
        create_campaign_bible,
        get_asset_direction,
    )

    CAMPAIGN_ENGINE_AVAILABLE = True

except Exception:

    create_campaign_bible = None
    get_asset_direction = None

    CAMPAIGN_ENGINE_AVAILABLE = False


# =========================================================
# MODULE
# =========================================================

VERSION = "3.3"

MODULE_NAME = "XPAND Unified Visual Runtime"


# =========================================================
# SETTINGS
# =========================================================

SEND_PREVIEW = str(
    os.environ.get(
        "XPAND_IMAGE_SEND_PREVIEW",
        "true",
    )
).strip().lower() not in {
    "0",
    "false",
    "no",
    "off",
}


SEND_ORIGINAL = str(
    os.environ.get(
        "XPAND_IMAGE_SEND_ORIGINAL",
        "true",
    )
).strip().lower() not in {
    "0",
    "false",
    "no",
    "off",
}


MAX_GENERATED_IMAGES = max(
    1,
    min(
        4,
        int(
            os.environ.get(
                "XPAND_IMAGE_MAX_IMAGES",
                "4",
            )
            or 4
        ),
    ),
)


MASTERPIECE_MAX_IMAGES = max(
    1,
    min(
        3,
        int(
            os.environ.get(
                "XPAND_MASTERPIECE_MAX_IMAGES",
                "3",
            )
            or 3
        ),
    ),
)


TELEGRAM_TIMEOUT = max(
    60,
    int(
        os.environ.get(
            "XPAND_IMAGE_TELEGRAM_TIMEOUT",
            "300",
        )
        or 300
    ),
)


MASTERPIECE_REQUIRE_QA = str(
    os.environ.get(
        "XPAND_MASTERPIECE_REQUIRE_QA",
        "true",
    )
).strip().lower() not in {
    "0",
    "false",
    "no",
    "off",
}


MASTERPIECE_ALLOW_SMART_FALLBACK = str(
    os.environ.get(
        "XPAND_MASTERPIECE_ALLOW_SMART_FALLBACK",
        "true",
    )
).strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}


# =========================================================
# ERROR
# =========================================================

class MasterpieceGuardError(
    RuntimeError
):
    pass


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


def normalized(
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
    markers,
) -> bool:

    source = normalized(
        text
    )

    return any(
        normalized(
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


def safe_json_string(
    value: Any,
    limit: int = 16000,
) -> str:

    try:

        result = json.dumps(
            value,
            ensure_ascii=False,
            separators=(
                ",",
                ":",
            ),
            default=str,
        )

    except Exception:

        result = "{}"

    return result[:limit]


# =========================================================
# IMAGE INTENT
# =========================================================

IMAGE_ACTION_MARKERS = [
    "اعمللي",
    "اعمل لي",
    "اعمل",
    "صمملي",
    "صمم لي",
    "صمم",
    "انشئ",
    "أنشئ",
    "سويلي",
    "سوي لي",
    "سوي",
    "ولد",
    "ولّد",
    "generate",
    "create",
    "design",
    "make",
]


IMAGE_ASSET_MARKERS = [
    "صوره",
    "صورة",
    "صور",
    "بوستر",
    "poster",
    "بوست",
    "بوستات",
    "post",
    "posts",
    "اعلان",
    "إعلان",
    "اعلانات",
    "إعلانات",
    "ad",
    "ads",
    "visual",
    "key visual",
    "campaign",
    "حمله",
    "حملة",
]


IMAGE_QUESTION_MARKERS = [
    "اشرحلي",
    "اشرح لي",
    "شو افضل موديل",
    "شو أفضل موديل",
    "ايش افضل موديل",
    "أي موديل",
    "كيف بتشتغل",
    "كيف تعمل",
    "شو يعني",
    "ما معنى",
]


MASTERPIECE_MARKERS = [
    "xpand masterpiece",
    "masterpiece",
    "ماستر بيس",
    "ماستربيس",
    "اقصى قوتك",
    "أقصى قوتك",
    "كل قواك",
    "افضل نتيجه ممكنه",
    "أفضل نتيجة ممكنة",
    "اقوى نتيجه",
    "أقوى نتيجة",
    "اعلى مستوى ممكن",
    "أعلى مستوى ممكن",
    "اقوى شغل",
    "أقوى شغل",
    "ultimate",
    "max quality",
]


def is_campaign_request(
    text: str,
) -> bool:

    source = normalized(
        text
    )

    if contains_any(
        source,
        [
            "سلسله بوستات",
            "سلسلة بوستات",
            "سلسله اعلانات",
            "سلسلة اعلانات",
            "سلسلة إعلانات",
            "series of posts",
            "series of ads",
            "ad series",
            "post series",
        ],
    ):

        return True

    if re.search(
        r"(?:^|\s)(?:حمله|campaign)(?=\s|$)",
        source,
        flags=re.IGNORECASE,
    ):

        # "campaign quality" alone is not campaign creation.
        if contains_any(
            source,
            [
                "campaign quality",
                "campaign-level",
                "campaign level",
                "بمستوى حملة",
                "جودة حملة",
            ],
        ):

            return False

        return True

    return False


def looks_like_image_generation_request(
    text: str,
) -> bool:

    value = clean_text(
        text,
        12000,
    )

    if not value:

        return False

    source = normalized(
        value
    )

    if source.startswith(
        "/image"
    ):

        return True

    if contains_any(
        value,
        IMAGE_QUESTION_MARKERS,
    ):

        return False

    if is_campaign_request(
        value
    ):

        return True

    return bool(
        contains_any(
            value,
            IMAGE_ACTION_MARKERS,
        )
        and
        contains_any(
            value,
            IMAGE_ASSET_MARKERS,
        )
    )


def is_masterpiece_request(
    text: str,
) -> bool:

    return contains_any(
        text,
        MASTERPIECE_MARKERS,
    )


# =========================================================
# IMAGE COUNT
# =========================================================

def detect_requested_image_count(
    text: str,
) -> int:

    source = normalized(
        text
    )

    patterns = [
        (
            r"\b([1-4])\s*"
            r"(?:صور|صوره|صورة|نسخ|خيارات|بوستات)\b"
        ),

        (
            r"\b(?:صور|نسخ|خيارات|بوستات)\s*"
            r"([1-4])\b"
        ),
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            source,
        )

        if match:

            return max(
                1,
                min(
                    MAX_GENERATED_IMAGES,
                    int(
                        match.group(
                            1
                        )
                    ),
                ),
            )

    return 1


# =========================================================
# ASPECT RATIO
# =========================================================

def detect_aspect_ratio(
    text: str,
) -> str:

    source = normalized(
        text
    )

    source = source.translate(
        str.maketrans(
            "٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹",
            "01234567890123456789",
        )
    )

    source = re.sub(
        r"\s*[：﹕︓:]\s*",
        ":",
        source,
    )

    ratios = [
        "1:1",
        "4:5",
        "5:4",
        "9:16",
        "16:9",
        "2:3",
        "3:2",
        "3:4",
        "4:3",
        "21:9",
    ]

    for ratio in ratios:

        if re.search(
            rf"(?<!\d){re.escape(ratio)}(?!\d)",
            source,
        ):

            return ratio

    if contains_any(
        source,
        [
            "ستوري",
            "story",
            "ريل",
            "reel",
        ],
    ):

        return "9:16"

    if contains_any(
        source,
        [
            "بوستر",
            "poster",
            "بوست",
            "post",
            "اعلان",
            "إعلان",
        ],
    ):

        return "4:5"

    return "1:1"


# =========================================================
# GENERATION MODE
# =========================================================

def detect_generation_mode(
    text: str,
) -> str:

    if contains_any(
        text,
        [
            "compare",
            "قارن الموديلات",
            "كل موديل لحاله",
        ],
    ):

        return "compare"

    if is_masterpiece_request(
        text
    ):

        return "best"

    if contains_any(
        text,
        [
            "nano banana pro",
            "نانو بنانا برو",
            "gemini 3 pro image",
            "google pro",
        ],
    ):

        return "google_pro"

    if contains_any(
        text,
        [
            "nano banana 2",
            "نانو بنانا 2",
            "google fast",
            "gemini fast",
        ],
    ):

        return "google_fast"

    if contains_any(
        text,
        [
            "سريع",
            "fast mode",
            "وضع سريع",
        ],
    ):

        return "fast"

    return "auto"


# =========================================================
# PROMPT
# =========================================================

def extract_image_prompt(
    text: str,
) -> str:

    value = clean_text(
        text,
        12000,
    )

    if value.lower().startswith(
        "/image"
    ):

        value = value[
            len(
                "/image"
            ):
        ].strip()

    return value


# =========================================================
# BRAND
# =========================================================

def detect_runtime_brand(
    core,
    user_id,
    text: str,
) -> str:

    try:

        detected = clean_text(
            detect_brand(
                text
            ),
            100,
        )

    except Exception:

        detected = ""

    if detected:

        return safe_brand_id(
            detected
        )

    if contains_any(
        text,
        [
            "stc bank",
            "stc بنك",
            "بنك stc",
            "اس تي سي بنك",
        ],
    ):

        return "stc_bank"

    try:

        active = get_active_brand(
            core,
            user_id,
        )

        return safe_brand_id(
            active
        )

    except Exception:

        return ""


def ensure_known_brand_profile(
    core,
    user_id,
    brand_id: str,
) -> None:

    if not brand_id:

        return

    if brand_id == "stc_bank":

        try:

            profile = BRAND_PROFILES.get(
                "stc_bank",
                {},
            )

            if profile:

                upsert_brand_profile(
                    core,
                    user_id,
                    "stc_bank",
                    "STC Bank KSA",
                    profile,
                )

        except Exception as error:

            print(
                "⚠️ STC brand profile:",
                clean_text(
                    error,
                    1000,
                ),
            )


def build_brand_context_for_request(
    core,
    user_id,
    brand_id: str,
    request: str,
) -> Dict[str, Any]:

    if not brand_id:

        return {}

    try:

        result = build_brand_memory_context(
            core,
            user_id,
            brand_id,
            request=request,
            max_rules=70,
            max_references=5,
        )

        return safe_dict(
            result
        )

    except TypeError:

        try:

            result = build_brand_memory_context(
                core,
                user_id,
                brand_id,
                max_rules=70,
                max_references=5,
            )

            return safe_dict(
                result
            )

        except Exception as error:

            print(
                "⚠️ Brand Memory fallback:",
                clean_text(
                    error,
                    1200,
                ),
            )

            return {}

    except Exception as error:

        print(
            "⚠️ Brand Memory:",
            clean_text(
                error,
                1200,
            ),
        )

        return {}


def safe_brand_context_for_model(
    context: Any,
) -> Dict[str, Any]:

    context = safe_dict(
        context
    )

    references = safe_list(
        context.get(
            "references"
        )
    )

    return {
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
            )[:70],

        "references":
            [
                item
                for item in references[:5]
                if isinstance(
                    item,
                    dict,
                )
            ],

        "reference_execution_context":
            context.get(
                "reference_execution_context",
                {},
            ),

        "campaign":
            context.get(
                "campaign",
                {},
            ),
    }


# =========================================================
# BENEFIT FAMILY
# =========================================================

INTERNATIONAL_TRANSFER_MARKERS = [
    "تحويل دولي",
    "تحويل مالي دولي",
    "تحويلات مالية دولية",
    "حوالة مالية دولية",
    "international transfer",
    "international money transfer",
]


MERCHANT_PAYMENTS_MARKERS = [
    "نقاط البيع",
    "نقطة البيع",
    "اجهزة نقاط البيع",
    "أجهزة نقاط البيع",
    "خدمات التجارة الالكترونية",
    "خدمات التجارة الإلكترونية",
    "التجارة الالكترونية",
    "التجارة الإلكترونية",
    "e-commerce",
    "ecommerce",
    "point of sale",
    "points of sale",
    "pos terminal",
    "merchant payments",
    "merchant services",
    "payment gateway",
    "بوابة الدفع",
]


CASHBACK_MARKERS = [
    "كاش باك",
    "cashback",
    "استرداد نقدي",
]


SECURITY_MARKERS = [
    "امان",
    "أمان",
    "امن",
    "آمن",
    "security",
    "secure",
]


TRAVEL_MARKERS = [
    "سفر",
    "السفر",
    "مسافر",
    "رحلة",
    "مطار",
    "travel",
    "airport",
]


REWARDS_MARKERS = [
    "مكافآت",
    "مكافات",
    "نقاط مكافآت",
    "reward points",
    "rewards",
]


SPEED_MARKERS = [
    "سرعة",
    "سرعه",
    "فوري",
    "سريع",
    "instant",
    "fast",
]


def detect_runtime_benefit_family(
    text: str,
) -> str:

    if contains_any(
        text,
        INTERNATIONAL_TRANSFER_MARKERS,
    ):

        return "international_transfer"

    # IMPORTANT:
    # merchant must run before rewards because
    # "نقاط البيع" contains "نقاط".
    if contains_any(
        text,
        MERCHANT_PAYMENTS_MARKERS,
    ):

        return "merchant_payments"

    if contains_any(
        text,
        CASHBACK_MARKERS,
    ):

        return "cashback"

    if contains_any(
        text,
        SECURITY_MARKERS,
    ):

        return "security"

    if contains_any(
        text,
        TRAVEL_MARKERS,
    ):

        return "travel"

    if contains_any(
        text,
        REWARDS_MARKERS,
    ):

        return "rewards"

    if contains_any(
        text,
        SPEED_MARKERS,
    ):

        return "speed"

    return "premium"


def build_creative_request(
    original_request: str,
) -> Tuple[
    str,
    str,
]:

    family = detect_runtime_benefit_family(
        original_request
    )

    if family == "merchant_payments":

        semantic = """
XPAND SEMANTIC PRIORITY:
The primary commercial benefit is merchant payments:
e-commerce services and point-of-sale acceptance.

Arabic "نقاط البيع" means Point of Sale / POS,
NOT loyalty points and NOT rewards.

The advertising idea must communicate a believable
merchant commerce experience across physical POS and
e-commerce without generic fintech decoration.

Avoid:
- reward points
- cashback coins
- floating money
- floating banking icons
- network lines
- laser payment paths
- generic HUD interfaces
""".strip()

    elif family == "international_transfer":

        semantic = """
XPAND SEMANTIC PRIORITY:
The primary commercial benefit is international transfer.
If speed is mentioned, speed is only a supporting attribute.
""".strip()

    elif family == "travel":

        semantic = """
XPAND SEMANTIC PRIORITY:
The primary commercial benefit is travel.
""".strip()

    elif family == "cashback":

        semantic = """
XPAND SEMANTIC PRIORITY:
The primary commercial benefit is cashback.
""".strip()

    elif family == "security":

        semantic = """
XPAND SEMANTIC PRIORITY:
The primary commercial benefit is security.
""".strip()

    elif family == "rewards":

        semantic = """
XPAND SEMANTIC PRIORITY:
The primary commercial benefit is rewards.
""".strip()

    elif family == "speed":

        semantic = """
XPAND SEMANTIC PRIORITY:
The primary commercial benefit is speed.
""".strip()

    else:

        semantic = """
XPAND SEMANTIC PRIORITY:
Visualize the real commercial benefit.
Do not default to generic banking imagery.
""".strip()

    return (
        clean_text(
            original_request,
            12000,
        )
        +
        "\n\n"
        +
        semantic,
        family,
    )


# =========================================================
# WINNER PROMPT
# =========================================================

def build_winner_instruction(
    creative_response,
) -> str:

    if creative_response is None:

        return ""

    winner = getattr(
        creative_response,
        "winner",
        None,
    )

    if winner is None:

        return ""

    try:

        direction = concept_to_dict(
            winner
        )

    except Exception:

        return ""

    return (
        "\n\n"
        "========================================\n"
        "XPAND APPROVED CREATIVE DIRECTION\n"
        "========================================\n"
        +
        safe_json_string(
            direction,
            18000,
        )
        +
        "\n\n"
        "Execute this direction faithfully. "
        "Do not replace it with generic advertising imagery."
    )


# =========================================================
# CREATIVE STATE
# =========================================================

def creative_quality_metadata(
    response,
) -> Dict[str, Any]:

    if response is None:

        return {}

    return safe_dict(
        getattr(
            response,
            "metadata",
            {},
        )
    )


def creative_quality_passed(
    response,
) -> bool:

    if response is None:

        return False

    winner = getattr(
        response,
        "winner",
        None,
    )

    if winner is None:

        return False

    metadata = creative_quality_metadata(
        response
    )

    metadata_passed = bool(
        metadata.get(
            "quality_gate_passed",
            getattr(
                response,
                "ok",
                False,
            ),
        )
    )

    winner_passed = bool(
        getattr(
            winner,
            "quality_gate_passed",
            metadata_passed,
        )
    )

    evaluation_valid = bool(
        getattr(
            winner,
            "evaluation_valid",
            True,
        )
    )

    return bool(
        metadata_passed
        and
        winner_passed
        and
        evaluation_valid
    )


def creative_runtime_state(
    response,
) -> Dict[str, Any]:

    if response is None:

        return {
            "state":
                "technical_failure",

            "technical_failure":
                True,

            "quality_gate_evaluated":
                False,

            "quality_gate_passed":
                False,

            "allow_smart_engine_fallback":
                True,

            "failure_reason":
                "creative_response_missing",

            "winner":
                None,

            "metadata":
                {},
        }

    metadata = creative_quality_metadata(
        response
    )

    winner = getattr(
        response,
        "winner",
        None,
    )

    technical_failure = bool(
        metadata.get(
            "technical_failure",
            False,
        )
    )

    quality_gate_evaluated = bool(
        metadata.get(
            "quality_gate_evaluated",
            winner is not None,
        )
    )

    quality_gate_passed = bool(
        metadata.get(
            "quality_gate_passed",
            False,
        )
    )

    allow_fallback = bool(
        metadata.get(
            "allow_smart_engine_fallback",
            False,
        )
    )

    failure_reason = clean_text(
        metadata.get(
            "failure_reason",
            "",
        ),
        1000,
    )

    if technical_failure:

        state = "technical_failure"
        allow_fallback = True

    elif not quality_gate_evaluated:

        state = "technical_failure"
        allow_fallback = True

    elif creative_quality_passed(
        response
    ):

        state = "approved"

    else:

        state = "quality_failed"

        if not bool(
            metadata.get(
                "quality_target_blocks_production",
                False,
            )
        ):

            allow_fallback = True

    return {
        "state":
            state,

        "technical_failure":
            technical_failure,

        "quality_gate_evaluated":
            quality_gate_evaluated,

        "quality_gate_passed":
            quality_gate_passed,

        "allow_smart_engine_fallback":
            allow_fallback,

        "failure_reason":
            failure_reason,

        "winner":
            winner,

        "metadata":
            metadata,
    }


# =========================================================
# MASTERPIECE GUARD
# =========================================================

def masterpiece_guard_status(
    prepared: Dict[str, Any],
) -> Dict[str, Any]:

    creative_mode = clean_text(
        prepared.get(
            "creative_mode",
            "",
        ),
        100,
    )

    if creative_mode != CREATIVE_MODE_MASTERPIECE:

        return {
            "allowed":
                True,

            "route":
                "normal",

            "code":
                "not_masterpiece",

            "message":
                "Normal image route.",
        }

    if (
        prepared.get(
            "campaign_required"
        )
        and
        not prepared.get(
            "campaign_validated"
        )
    ):

        return {
            "allowed":
                False,

            "route":
                "blocked",

            "code":
                "campaign_quality_gate_failed",

            "message":
                "Campaign validation did not pass.",
        }

    runtime = creative_runtime_state(
        prepared.get(
            "creative_response"
        )
    )

    state = runtime.get(
        "state"
    )

    if state == "approved":

        return {
            "allowed":
                True,

            "route":
                "masterpiece",

            "code":
                "passed",

            "message":
                "Masterpiece creative direction approved.",
        }

    if state == "technical_failure":

        return {
            "allowed":
                True,

            "route":
                "smart_fallback",

            "code":
                "creative_brain_technical_fallback",

            "message":
                (
                    "Creative Brain technical failure. "
                    "Continue through Smart Engine."
                ),

            "failure_reason":
                runtime.get(
                    "failure_reason",
                    "",
                ),
        }

    if (
        runtime.get(
            "allow_smart_engine_fallback"
        )
        or
        MASTERPIECE_ALLOW_SMART_FALLBACK
    ):

        return {
            "allowed":
                True,

            "route":
                "smart_fallback",

            "code":
                "creative_quality_fallback",

            "message":
                (
                    "Creative quality target not reached. "
                    "Continue through Smart Engine."
                ),
        }

    return {
        "allowed":
            False,

        "route":
            "blocked",

        "code":
            "creative_quality_gate_failed",

        "message":
            (
                "Creative Quality Gate did not pass "
                "and fallback is disabled."
            ),
    }


def enforce_masterpiece_guard(
    prepared: Dict[str, Any],
) -> Dict[str, Any]:

    status = masterpiece_guard_status(
        prepared
    )

    route = status.get(
        "route"
    )

    if not status.get(
        "allowed"
    ):

        print("")
        print(
            "=========================================="
        )
        print(
            " MASTERPIECE INTEGRATION GUARD: BLOCKED"
        )
        print(
            "=========================================="
        )
        print(
            "Reason:",
            status.get(
                "code"
            )
        )
        print(
            status.get(
                "message"
            )
        )
        print("")

        raise MasterpieceGuardError(
            status.get(
                "message"
            )
            or
            "Masterpiece guard blocked production."
        )

    if route == "masterpiece":

        print(
            "✅ MASTERPIECE INTEGRATION GUARD: PASSED"
        )

    elif route == "smart_fallback":

        print("")
        print(
            "=========================================="
        )
        print(
            " MASTERPIECE INTEGRATION GUARD: FALLBACK"
        )
        print(
            "=========================================="
        )
        print(
            "Reason:",
            status.get(
                "code"
            )
        )
        print(
            status.get(
                "message"
            )
        )
        print(
            "✅ Smart Engine fallback is allowed."
        )
        print("")

    return status


# =========================================================
# RESEARCH
# =========================================================

def apply_brand_research(
    prompt: str,
) -> Dict[str, Any]:

    result = {
        "applied":
            False,

        "final_prompt":
            prompt,

        "research_summary":
            "",

        "sources_used":
            [],

        "mode_override":
            "",

        "brand_id":
            "",
    }

    try:

        if not should_apply_deep_research(
            prompt
        ):

            return result

        research = build_researched_prompt(
            prompt
        )

        if not isinstance(
            research,
            dict,
        ):

            return result

        if research.get(
            "applied"
        ):

            result.update(
                {
                    "applied":
                        True,

                    "final_prompt":
                        clean_text(
                            research.get(
                                "final_prompt",
                                prompt,
                            ),
                            32000,
                        ),

                    "research_summary":
                        clean_text(
                            research.get(
                                "research_summary",
                                "",
                            ),
                            7000,
                        ),

                    "sources_used":
                        safe_list(
                            research.get(
                                "sources_used"
                            )
                        )[:20],

                    "mode_override":
                        clean_text(
                            research.get(
                                "mode_override",
                                "",
                            ),
                            100,
                        ),

                    "brand_id":
                        clean_text(
                            research.get(
                                "brand_id",
                                "",
                            ),
                            100,
                        ),
                }
            )

    except Exception as error:

        print(
            "⚠️ Brand research:",
            clean_text(
                error,
                1600,
            ),
        )

    return result


# =========================================================
# CAMPAIGN
# =========================================================

def campaign_title_from_request(
    text: str,
    brand_id: str,
) -> str:

    source = clean_text(
        text,
        500,
    )

    if source:

        return source[:120]

    return (
        brand_id
        +
        " Campaign"
    )


def detect_campaign_asset_count(
    text: str,
) -> int:

    source = normalized(
        text
    )

    match = re.search(
        (
            r"\b([2-9]|1[0-9]|20)\b"
            r".{0,50}?"
            r"(?:بوستات|اعلانات|إعلانات|assets|posts|ads)"
        ),
        source,
    )

    if match:

        return max(
            2,
            min(
                20,
                int(
                    match.group(
                        1
                    )
                ),
            ),
        )

    return 3


def try_build_campaign(
    *,
    core,
    user_id,
    brand_id: str,
    original_prompt: str,
    creative_response,
    brand_context: Dict[str, Any],
    references: List[Any],
    research_summary: str,
    research_sources: List[Any],
) -> Dict[str, Any]:

    if not is_campaign_request(
        original_prompt
    ):

        return {
            "required":
                False,

            "validated":
                False,

            "bible":
                None,

            "execution":
                {},
        }

    if not CAMPAIGN_ENGINE_AVAILABLE:

        return {
            "required":
                True,

            "validated":
                False,

            "bible":
                None,

            "execution":
                {},

            "error":
                "campaign_engine_unavailable",
        }

    if not creative_quality_passed(
        creative_response
    ):

        return {
            "required":
                True,

            "validated":
                False,

            "bible":
                None,

            "execution":
                {},

            "error":
                "creative_direction_not_approved",
        }

    approved_direction = {}

    try:

        winner = getattr(
            creative_response,
            "winner",
            None,
        )

        if winner:

            approved_direction = concept_to_dict(
                winner
            )

    except Exception:

        approved_direction = {}

    try:

        bible = create_campaign_bible(
            core=core,
            user_id=user_id,
            brand_id=brand_id,
            campaign_title=campaign_title_from_request(
                original_prompt,
                brand_id,
            ),
            campaign_goal=original_prompt,
            asset_count=detect_campaign_asset_count(
                original_prompt
            ),
            brand_context=brand_context,
            visual_references=references,
            research_summary=research_summary,
            research_sources=research_sources,
            approved_creative_direction=approved_direction,
            allow_fallback=True,
        )

        metadata = safe_dict(
            getattr(
                bible,
                "metadata",
                {},
            )
        )

        validated = bool(
            not metadata.get(
                "fallback",
                False,
            )
            and
            metadata.get(
                "quality_status",
                "validated",
            )
            ==
            "validated"
        )

        execution = {}

        if callable(
            get_asset_direction
        ):

            try:

                execution = safe_dict(
                    get_asset_direction(
                        bible,
                        1,
                    )
                )

            except Exception:

                execution = {}

        return {
            "required":
                True,

            "validated":
                validated,

            "bible":
                bible,

            "execution":
                execution,
        }

    except Exception as error:

        print(
            "⚠️ Campaign Bible:",
            clean_text(
                error,
                2000,
            ),
        )

        return {
            "required":
                True,

            "validated":
                False,

            "bible":
                None,

            "execution":
                {},

            "error":
                clean_text(
                    error,
                    2000,
                ),
        }


# =========================================================
# PREPARE REQUEST
# =========================================================

def prepare_generation_input(
    core,
    user_id,
    prompt: str,
) -> Dict[str, Any]:

    original_prompt = clean_text(
        prompt,
        12000,
    )

    brand_id = detect_runtime_brand(
        core,
        user_id,
        original_prompt,
    )

    if brand_id:

        try:

            set_active_brand(
                core,
                user_id,
                brand_id,
            )

        except Exception:

            pass

        ensure_known_brand_profile(
            core,
            user_id,
            brand_id,
        )

    research = apply_brand_research(
        original_prompt
    )

    research_prompt = clean_text(
        research.get(
            "final_prompt",
            original_prompt,
        ),
        32000,
    )

    research_brand = safe_brand_id(
        research.get(
            "brand_id",
            "",
        )
    )

    if research_brand:

        brand_id = research_brand

    brand_context = build_brand_context_for_request(
        core,
        user_id,
        brand_id,
        original_prompt,
    )

    model_brand_context = safe_brand_context_for_model(
        brand_context
    )

    references = safe_list(
        brand_context.get(
            "references"
        )
    )[:5]

    strict_masterpiece = bool(
        is_masterpiece_request(
            original_prompt
        )
        or
        brand_id
        ==
        "stc_bank"
    )

    creative_mode = (
        CREATIVE_MODE_MASTERPIECE
        if strict_masterpiece
        else
        CREATIVE_MODE_FAST
    )

    creative_request, benefit_family = (
        build_creative_request(
            original_prompt
        )
    )

    creative_response = None
    creative_error = ""

    try:

        creative_response = run_creative_brain(
            user_request=creative_request,
            brand_context=model_brand_context,
            visual_references=references,
            mode=creative_mode,
            top_count=3,
        )

    except Exception as error:

        creative_error = clean_text(
            error,
            4000,
        )

        print(
            "⚠️ Creative Brain exception:",
            creative_error,
        )

    runtime_state = creative_runtime_state(
        creative_response
    )

    campaign = try_build_campaign(
        core=core,
        user_id=user_id,
        brand_id=brand_id,
        original_prompt=original_prompt,
        creative_response=creative_response,
        brand_context=model_brand_context,
        references=references,
        research_summary=research.get(
            "research_summary",
            "",
        ),
        research_sources=safe_list(
            research.get(
                "sources_used"
            )
        ),
    )

    final_prompt = research_prompt

    final_prompt += (
        "\n\n"
        "========================================\n"
        "XPAND COMMERCIAL INTENT\n"
        "========================================\n"
        +
        creative_request
    )

    if model_brand_context:

        final_prompt += (
            "\n\n"
            "========================================\n"
            "BRAND MEMORY CONTEXT\n"
            "========================================\n"
            +
            safe_json_string(
                model_brand_context,
                12000,
            )
        )

    winner_instruction = build_winner_instruction(
        creative_response
    )

    if winner_instruction:

        final_prompt += winner_instruction

    campaign_execution = safe_dict(
        campaign.get(
            "execution"
        )
    )

    if campaign_execution:

        final_prompt += (
            "\n\n"
            "========================================\n"
            "CAMPAIGN VISUAL BIBLE\n"
            "========================================\n"
            +
            safe_json_string(
                campaign_execution,
                12000,
            )
        )

    if brand_id == "stc_bank":

        final_prompt += """

========================================
STC BANK PRODUCTION LOCK
========================================

Create premium, realistic Saudi commercial advertising.

Use STC Bank brand identity with restraint.
Do not turn brand purple into random decoration.

For merchant payments / e-commerce / POS:
show a believable premium merchant/customer commerce moment.

Do NOT use:
- floating coins
- reward points
- magic portals
- random HUD
- network lines
- blue laser beams
- floating banking cards
- floating payment icons
- generic fintech neon

The final image must look photographically believable,
commercially usable and premium.
""".rstrip()

    mode_override = clean_text(
        research.get(
            "mode_override",
            "",
        ),
        100,
    )

    if (
        brand_id == "stc_bank"
        and
        not mode_override
    ):

        mode_override = "best"

    return {
        "original_prompt":
            original_prompt,

        "final_prompt":
            clean_text(
                final_prompt,
                50000,
            ),

        "brand_id":
            brand_id,

        "benefit_family":
            benefit_family,

        "research_applied":
            bool(
                research.get(
                    "applied"
                )
            ),

        "research_summary":
            research.get(
                "research_summary",
                "",
            ),

        "research_sources":
            safe_list(
                research.get(
                    "sources_used"
                )
            ),

        "mode_override":
            mode_override,

        "brand_context":
            brand_context,

        "model_brand_context":
            model_brand_context,

        "references":
            references,

        "creative_mode":
            creative_mode,

        "strict_masterpiece":
            strict_masterpiece,

        "creative_response":
            creative_response,

        "creative_error":
            creative_error,

        "creative_runtime_state":
            runtime_state,

        "campaign_required":
            bool(
                campaign.get(
                    "required"
                )
            ),

        "campaign_validated":
            bool(
                campaign.get(
                    "validated"
                )
            ),

        "campaign_bible":
            campaign.get(
                "bible"
            ),

        "campaign_execution":
            campaign_execution,
    }


# =========================================================
# CREATIVE DIRECTION
# =========================================================

def creative_direction_for_index(
    creative_response,
    index: int,
) -> Tuple[
    Dict[str, Any],
    Dict[str, Any],
]:

    if creative_response is None:

        return (
            {},
            {},
        )

    concepts = safe_list(
        getattr(
            creative_response,
            "top_concepts",
            [],
        )
    )

    concept = None

    if concepts:

        concept = concepts[
            min(
                index,
                len(
                    concepts
                )
                -
                1,
            )
        ]

    if concept is None:

        concept = getattr(
            creative_response,
            "winner",
            None,
        )

    if concept is None:

        return (
            {},
            {},
        )

    try:

        direction = concept_to_dict(
            concept
        )

    except Exception:

        return (
            {},
            {},
        )

    debate = safe_dict(
        getattr(
            concept,
            "debate",
            {},
        )
    )

    camera = safe_dict(
        debate.get(
            "camera_director"
        )
    )

    if not camera:

        camera = {
            "camera_angle":
                getattr(
                    concept,
                    "camera_angle",
                    "",
                ),

            "lens":
                getattr(
                    concept,
                    "lens",
                    "",
                ),

            "perspective":
                getattr(
                    concept,
                    "perspective",
                    "",
                ),
        }

    return (
        direction,
        camera,
    )


# =========================================================
# MASTERPIECE PRODUCTION
# =========================================================

def generate_masterpiece_images(
    *,
    core,
    user_id,
    request_text: str,
    prepared: Dict[str, Any],
    number: int,
    aspect_ratio: str,
) -> Tuple[
    List[Any],
    List[Dict[str, Any]],
    List[str],
]:

    status = enforce_masterpiece_guard(
        prepared
    )

    if status.get(
        "route"
    ) != "masterpiece":

        return (
            [],
            [],
            [
                (
                    "masterpiece_skipped: "
                    +
                    clean_text(
                        status.get(
                            "code",
                            "smart_fallback",
                        ),
                        500,
                    )
                )
            ],
        )

    creative_response = prepared.get(
        "creative_response"
    )

    brand_id = prepared.get(
        "brand_id",
        "",
    )

    brand_context = safe_dict(
        prepared.get(
            "model_brand_context"
        )
    )

    number = max(
        1,
        min(
            MASTERPIECE_MAX_IMAGES,
            int(
                number
                or 1
            ),
        ),
    )

    images: List[Any] = []
    metadata: List[Dict[str, Any]] = []
    errors: List[str] = []

    for index in range(
        number
    ):

        direction, camera = (
            creative_direction_for_index(
                creative_response,
                index,
            )
        )

        if not direction:

            errors.append(
                "masterpiece_direction_missing"
            )

            break

        try:

            print("")
            print(
                "🎬 MASTERPIECE PRODUCTION",
                str(
                    index + 1
                )
                +
                "/"
                +
                str(
                    number
                ),
            )

            production = run_production(
                core=core,
                user_id=user_id,
                brand_id=brand_id,
                original_request=request_text,
                creative_direction=direction,
                brand_context=brand_context,
                camera_direction=camera,
                aspect_ratio=aspect_ratio,
                mode=PRODUCTION_MODE_MASTERPIECE,
                target_model=TARGET_GEMINI,
            )

            final_image = getattr(
                production,
                "final_image",
                None,
            )

            qa = getattr(
                production,
                "qa",
                None,
            )

            qa_passed = bool(
                qa
                and
                getattr(
                    qa,
                    "passed",
                    False,
                )
            )

            best_score = safe_float(
                getattr(
                    production,
                    "best_score",
                    0,
                ),
                0,
            )

            metadata.append(
                {
                    "best_score":
                        best_score,

                    "qa_passed":
                        qa_passed,

                    "errors":
                        safe_list(
                            getattr(
                                production,
                                "errors",
                                [],
                            )
                        ),
                }
            )

            if final_image is None:

                errors.append(
                    "masterpiece_final_image_missing"
                )

                continue

            if (
                MASTERPIECE_REQUIRE_QA
                and
                not qa_passed
            ):

                errors.append(
                    (
                        "masterpiece_qa_failed:"
                        +
                        str(
                            best_score
                        )
                    )
                )

                print(
                    "⚠️ Masterpiece QA failed. "
                    "Smart Engine fallback will be used."
                )

                continue

            images.append(
                final_image
            )

        except Exception as error:

            message = clean_text(
                error,
                4000,
            )

            errors.append(
                (
                    "masterpiece_"
                    +
                    str(
                        index + 1
                    )
                    +
                    ": "
                    +
                    message
                )
            )

            print(
                "⚠️ MASTERPIECE FAILED:",
                message,
            )

    return (
        images,
        metadata,
        errors,
    )


# =========================================================
# TELEGRAM API
# =========================================================

def telegram_api_url(
    core,
    method: str,
) -> str:

    token = clean_text(
        getattr(
            core,
            "TELEGRAM_BOT_TOKEN",
            "",
        )
        or
        os.environ.get(
            "TELEGRAM_BOT_TOKEN",
            "",
        ),
        2000,
    )

    if not token:

        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN missing"
        )

    return (
        "https://api.telegram.org/bot"
        +
        token
        +
        "/"
        +
        method
    )


def send_photo_bytes(
    core,
    chat_id,
    image_bytes: bytes,
    filename: str,
    mime_type: str,
    caption: str,
) -> Dict[str, Any]:

    buffer = io.BytesIO(
        image_bytes
    )

    buffer.name = filename

    response = requests.post(
        telegram_api_url(
            core,
            "sendPhoto",
        ),

        data={
            "chat_id":
                str(
                    chat_id
                ),

            "caption":
                clean_text(
                    caption,
                    1000,
                ),
        },

        files={
            "photo": (
                filename,
                buffer,
                mime_type
                or
                "image/png",
            )
        },

        timeout=TELEGRAM_TIMEOUT,
    )

    try:

        payload = response.json()

    except Exception:

        payload = {
            "ok":
                False,

            "description":
                response.text,
        }

    if (
        not response.ok
        or
        not payload.get(
            "ok"
        )
    ):

        raise RuntimeError(
            "Telegram sendPhoto failed: "
            +
            clean_text(
                payload,
                2000,
            )
        )

    return payload


def send_document_bytes(
    core,
    chat_id,
    image_bytes: bytes,
    filename: str,
    mime_type: str,
    caption: str,
) -> Dict[str, Any]:

    buffer = io.BytesIO(
        image_bytes
    )

    buffer.name = filename

    response = requests.post(
        telegram_api_url(
            core,
            "sendDocument",
        ),

        data={
            "chat_id":
                str(
                    chat_id
                ),

            "caption":
                clean_text(
                    caption,
                    1000,
                ),
        },

        files={
            "document": (
                filename,
                buffer,
                mime_type
                or
                "application/octet-stream",
            )
        },

        timeout=TELEGRAM_TIMEOUT,
    )

    try:

        payload = response.json()

    except Exception:

        payload = {
            "ok":
                False,

            "description":
                response.text,
        }

    if (
        not response.ok
        or
        not payload.get(
            "ok"
        )
    ):

        raise RuntimeError(
            "Telegram sendDocument failed: "
            +
            clean_text(
                payload,
                2000,
            )
        )

    return payload


# =========================================================
# DELIVERY
# =========================================================

def deliver_generated_image(
    core,
    *,
    chat_id,
    image,
    index: int,
    total: int,
) -> Dict[str, Any]:

    image_bytes = getattr(
        image,
        "image_bytes",
        b"",
    )

    if not image_bytes:

        raise RuntimeError(
            "Generated image contains no bytes."
        )

    filename = clean_text(
        getattr(
            image,
            "filename",
            "",
        ),
        500,
    )

    if not filename:

        filename = (
            "xpand-"
            +
            str(
                index
            )
            +
            ".png"
        )

    mime_type = clean_text(
        getattr(
            image,
            "mime_type",
            "",
        ),
        100,
    )

    if not mime_type:

        mime_type = "image/png"

    model = clean_text(
        getattr(
            image,
            "model",
            "",
        ),
        300,
    )

    preview_result = {}

    original_result = {}

    if SEND_PREVIEW:

        preview_result = send_photo_bytes(
            core,
            chat_id,
            image_bytes,
            filename,
            mime_type,
            (
                "XPAND "
                +
                str(
                    index
                )
                +
                "/"
                +
                str(
                    total
                )
                +
                (
                    "\n"
                    +
                    model
                    if model
                    else ""
                )
            ),
        )

    if SEND_ORIGINAL:

        original_result = send_document_bytes(
            core,
            chat_id,
            image_bytes,
            filename,
            mime_type,
            (
                "النسخة الأصلية"
                +
                (
                    " | "
                    +
                    model
                    if model
                    else ""
                )
            ),
        )

    return {
        "model":
            model,

        "provider":
            clean_text(
                getattr(
                    image,
                    "provider",
                    "",
                ),
                200,
            ),

        "filename":
            filename,

        "mime_type":
            mime_type,

        "byte_size":
            len(
                image_bytes
            ),

        "preview_sent":
            bool(
                preview_result
            ),

        "original_sent":
            bool(
                original_result
            ),
    }


# =========================================================
# GENERATE + DELIVER
# =========================================================

def generate_and_deliver(
    core,
    chat_id,
    user_id,
    text,
    source_channel: str = "telegram_text",
) -> Dict[str, Any]:

    prompt = extract_image_prompt(
        text
    )

    if not prompt:

        raise RuntimeError(
            "اكتبلي وصف الصورة اللي بدك إياها."
        )

    number = detect_requested_image_count(
        prompt
    )

    aspect_ratio = detect_aspect_ratio(
        prompt
    )

    image_size = detect_image_size(
        prompt
    )

    prepared = prepare_generation_input(
        core,
        user_id,
        prompt,
    )

    final_prompt = prepared.get(
        "final_prompt",
        prompt,
    )

    brand_id = prepared.get(
        "brand_id",
        "",
    )

    benefit_family = prepared.get(
        "benefit_family",
        "",
    )

    creative_mode = prepared.get(
        "creative_mode",
        CREATIVE_MODE_FAST,
    )

    creative_response = prepared.get(
        "creative_response"
    )

    runtime = creative_runtime_state(
        creative_response
    )

    creative_score = None

    winner = getattr(
        creative_response,
        "winner",
        None,
    ) if creative_response else None

    if winner is not None:

        creative_score = safe_float(
            getattr(
                winner,
                "weighted_score",
                0,
            ),
            0,
        )

    try:

        core.send_action(
            chat_id,
            "upload_photo",
        )

    except Exception:

        pass

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND UNIFIED VISUAL REQUEST V3.3"
    )
    print(
        "=========================================="
    )
    print(
        "brand =",
        brand_id
        or
        "-",
    )
    print(
        "benefit_family =",
        benefit_family,
    )
    print(
        "research =",
        prepared.get(
            "research_applied"
        ),
    )
    print(
        "creative_mode =",
        creative_mode,
    )
    print(
        "creative_state =",
        runtime.get(
            "state"
        ),
    )
    print(
        "creative_score =",
        (
            creative_score
            if creative_score is not None
            else "n/a"
        ),
    )
    print(
        "technical_failure =",
        runtime.get(
            "technical_failure"
        ),
    )
    print(
        "quality_gate_evaluated =",
        runtime.get(
            "quality_gate_evaluated"
        ),
    )
    print(
        "quality_gate_passed =",
        runtime.get(
            "quality_gate_passed"
        ),
    )
    print(
        "allow_smart_engine_fallback =",
        runtime.get(
            "allow_smart_engine_fallback"
        ),
    )
    print(
        "aspect_ratio =",
        aspect_ratio,
    )
    print(
        "image_size =",
        image_size,
    )
    print(
        "requested_images =",
        number,
    )
    print(
        "selected_references =",
        len(
            prepared.get(
                "references",
                [],
            )
        ),
    )
    print(
        "campaign_required =",
        prepared.get(
            "campaign_required"
        ),
    )
    print(
        "campaign_validated =",
        prepared.get(
            "campaign_validated"
        ),
    )
    print("")

    images: List[Any] = []

    production_metadata: List[
        Dict[str, Any]
    ] = []

    pipeline_errors: List[str] = []

    use_masterpiece = (
        creative_mode
        ==
        CREATIVE_MODE_MASTERPIECE
    )

    guard_status = {
        "allowed":
            True,

        "route":
            "normal",

        "code":
            "not_masterpiece",
    }

    # =====================================================
    # MASTERPIECE ROUTE
    # =====================================================

    if use_masterpiece:

        guard_status = enforce_masterpiece_guard(
            prepared
        )

        if guard_status.get(
            "route"
        ) == "masterpiece":

            try:

                core.send_message(
                    chat_id,
                    (
                        "تمام، الاتجاه الإبداعي اجتاز "
                        "Masterpiece Gate. ببدأ الإنتاج."
                    ),
                )

            except Exception:

                pass

            (
                images,
                production_metadata,
                masterpiece_errors,
            ) = generate_masterpiece_images(
                core=core,
                user_id=user_id,
                request_text=prompt,
                prepared=prepared,
                number=number,
                aspect_ratio=aspect_ratio,
            )

            pipeline_errors.extend(
                masterpiece_errors
            )

            if not images:

                print(
                    "⚠️ Masterpiece produced no qualified image."
                )
                print(
                    "⚡ Continuing with Smart Engine fallback."
                )

        else:

            print(
                "⚡ Masterpiece skipped"
                +
                " | route="
                +
                clean_text(
                    guard_status.get(
                        "route",
                        "",
                    ),
                    100,
                )
                +
                " | reason="
                +
                clean_text(
                    guard_status.get(
                        "code",
                        "",
                    ),
                    300,
                )
            )

    # =====================================================
    # SMART ENGINE FALLBACK
    # =====================================================

    smart_fallback_allowed = bool(
        not use_masterpiece
        or
        guard_status.get(
            "route"
        )
        ==
        "smart_fallback"
        or
        MASTERPIECE_ALLOW_SMART_FALLBACK
    )

    if (
        not images
        and
        smart_fallback_allowed
    ):

        mode = (
            clean_text(
                prepared.get(
                    "mode_override",
                    "",
                ),
                100,
            )
            or
            detect_generation_mode(
                prompt
            )
        )

        # On a technical Creative Brain failure the image
        # engine must be able to finish the user's request.
        if (
            runtime.get(
                "state"
            )
            ==
            "technical_failure"
            and
            mode
            ==
            "auto"
        ):

            mode = "best"

        print(
            "⚡ SMART IMAGE ENGINE"
            +
            " | mode="
            +
            mode
        )

        try:

            result = generate_image(
                final_prompt,
                mode=mode,
                number=number,
                aspect_ratio=aspect_ratio,
                image_size=image_size,
                reference_count=len(
                    prepared.get(
                        "references",
                        [],
                    )
                ),
                allow_fallback=True,
            )

            if (
                not getattr(
                    result,
                    "ok",
                    False,
                )
                or
                not safe_list(
                    getattr(
                        result,
                        "images",
                        [],
                    )
                )
            ):

                raise RuntimeError(
                    "Smart image engine returned no image."
                )

            images = safe_list(
                result.images
            )

            pipeline_errors.extend(
                safe_list(
                    getattr(
                        result,
                        "errors",
                        [],
                    )
                )
            )

        except Exception as error:

            message = clean_text(
                error,
                4000,
            )

            pipeline_errors.append(
                "smart_engine: "
                +
                message
            )

            print(
                "❌ SMART IMAGE ENGINE:",
                message,
            )

            raise

    if not images:

        raise RuntimeError(
            (
                "لم يتم تسليم صورة لأن Masterpiece "
                "وSmart Engine لم يرجعا نتيجة صالحة."
            )
        )

    # =====================================================
    # DELIVERY
    # =====================================================

    delivered = []

    for index, image in enumerate(
        images,
        start=1,
    ):

        delivered.append(
            deliver_generated_image(
                core,
                chat_id=chat_id,
                image=image,
                index=index,
                total=len(
                    images
                ),
            )
        )

    qa_scores = [
        safe_float(
            item.get(
                "best_score",
                0,
            ),
            0,
        )
        for item in production_metadata
        if safe_float(
            item.get(
                "best_score",
                0,
            ),
            0,
        )
        >
        0
    ]

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND IMAGE DELIVERY COMPLETE"
    )
    print(
        "=========================================="
    )
    print(
        "images =",
        len(
            delivered
        ),
    )
    print(
        "creative_route =",
        guard_status.get(
            "route"
        ),
    )
    print(
        "errors =",
        len(
            pipeline_errors
        ),
    )
    print("")

    return {
        "ok":
            True,

        "runtime_version":
            VERSION,

        "source_channel":
            source_channel,

        "brand_id":
            brand_id,

        "benefit_family":
            benefit_family,

        "creative_mode":
            creative_mode,

        "creative_state":
            runtime.get(
                "state"
            ),

        "creative_score":
            creative_score,

        "guard_route":
            guard_status.get(
                "route"
            ),

        "images":
            delivered,

        "qa_scores":
            qa_scores,

        "production_metadata":
            production_metadata,

        "errors":
            pipeline_errors,
    }


# =========================================================
# TEXT HANDLER
# =========================================================

def handle_text_image_request(
    core,
    chat_id,
    user_id,
    text,
) -> bool:

    source = normalized(
        text
    )

    if source in {
        "/xpand_budget",
        "ميزانية اوبن اي",
        "ميزانيه اوبن اي",
        "openai budget",
    }:

        status = budget_status()

        core.send_message(
            chat_id,
            (
                "💰 حد OpenAI اليومي\n"
                +
                "الحالة: "
                +
                (
                    "مفعّل"
                    if status.get(
                        "enabled"
                    )
                    else
                    "مغلق"
                )
                +
                "\nالحد: $"
                +
                f"{safe_float(status.get('limit_usd'), 0):.2f}"
                +
                "\nالمحجوز: $"
                +
                f"{safe_float(status.get('reserved_usd'), 0):.2f}"
                +
                "\nالمتبقي: $"
                +
                f"{safe_float(status.get('remaining_usd'), 0):.2f}"
            ),
        )

        return True

    if not looks_like_image_generation_request(
        text
    ):

        return False

    try:

        result = generate_and_deliver(
            core,
            chat_id,
            user_id,
            text,
            source_channel="telegram_text",
        )

        if result.get(
            "errors"
        ):

            print(
                "⚠️ XPAND VISUAL PIPELINE INFO:",
                result.get(
                    "errors"
                ),
            )

    except MasterpieceGuardError as error:

        message = clean_text(
            error,
            1800,
        )

        print(
            "🛑 XPAND MASTERPIECE GUARD:",
            message,
        )

        try:

            core.send_message(
                chat_id,
                message,
            )

        except Exception:

            pass

    except Exception as error:

        message = clean_text(
            error,
            2000,
        )

        print(
            "❌ XPAND VISUAL TEXT:",
            message,
        )

        try:

            core.send_message(
                chat_id,
                (
                    "صار خلل بالإنتاج البصري.\n"
                    "الخطأ: "
                    +
                    message
                ),
            )

        except Exception:

            pass

    return True


# =========================================================
# STATUS
# =========================================================

def provider_ready(
    status: Dict[str, Any],
    provider_name: str,
) -> bool:

    providers = safe_dict(
        status.get(
            "providers"
        )
    )

    provider = safe_dict(
        providers.get(
            provider_name
        )
    )

    return bool(
        provider.get(
            "configured"
        )
    )


# =========================================================
# INSTALL
# =========================================================

def install(
    core,
) -> Dict[str, Any]:

    if getattr(
        core,
        "_XPAND_IMAGE_TELEGRAM_INSTALLED",
        False,
    ):

        return {
            "ok":
                True,

            "already_installed":
                True,

            "runtime_version":
                VERSION,
        }

    # =====================================================
    # COMMAND ROUTER
    # =====================================================

    original_handle_command = getattr(
        core,
        "handle_command",
        None,
    )

    if callable(
        original_handle_command
    ):

        def xpand_visual_handle_command(
            chat_id,
            user_id,
            text,
        ):

            if handle_text_image_request(
                core,
                chat_id,
                user_id,
                text,
            ):

                return True

            return original_handle_command(
                chat_id,
                user_id,
                text,
            )

        core.handle_command = (
            xpand_visual_handle_command
        )

    # =====================================================
    # VOICE / NORMAL ASK ROUTER
    # =====================================================

    original_ask = getattr(
        core,
        "ask_kemo",
        None,
    )

    if callable(
        original_ask
    ):

        def xpand_visual_ask(
            chat_id,
            user_id,
            user_message,
        ):

            if not looks_like_image_generation_request(
                user_message
            ):

                return original_ask(
                    chat_id,
                    user_id,
                    user_message,
                )

            try:

                result = generate_and_deliver(
                    core,
                    chat_id,
                    user_id,
                    user_message,
                    source_channel="telegram_voice",
                )

                if result.get(
                    "guard_route"
                ) == "smart_fallback":

                    return (
                        "تم. Creative Brain تعرّض لمشكلة، "
                        "فكملت الطلب تلقائيًا عبر Smart Engine "
                        "وبعثتلك الصورة."
                    )

                return (
                    "تم، ولّدتلك الصورة وبعثتلك "
                    "المعاينة والنسخة الأصلية."
                )

            except Exception as error:

                message = clean_text(
                    error,
                    1500,
                )

                print(
                    "❌ XPAND IMAGE VOICE:",
                    message,
                )

                return (
                    "صار خلل بالإنتاج البصري: "
                    +
                    message
                )

        core.ask_kemo = (
            xpand_visual_ask
        )

    # =====================================================
    # INSTALL COMPLETE
    # =====================================================

    core._XPAND_IMAGE_TELEGRAM_INSTALLED = (
        True
    )

    try:

        status = get_image_engine_status()

    except Exception as error:

        status = {
            "ok":
                False,

            "error":
                clean_text(
                    error,
                    1000,
                ),
        }

    print("")
    print(
        "=================================================="
    )
    print(
        " XPAND UNIFIED VISUAL RUNTIME V3.3"
    )
    print(
        "=================================================="
    )
    print(
        "✅ install(core): READY"
    )
    print(
        "✅ Telegram Text Image Routing"
    )
    print(
        "✅ Voice Image Routing"
    )
    print(
        "✅ STC Bank Masterpiece Mode"
    )
    print(
        "✅ Merchant Payments Semantic Priority"
    )
    print(
        "✅ Creative Brain Runtime State Classifier"
    )
    print(
        "✅ Technical Failure != Quality Failure"
    )
    print(
        "✅ Masterpiece Production"
    )
    print(
        "✅ Smart Engine Automatic Fallback"
    )
    print(
        "✅ 4:5 / explicit ratio support"
    )
    print(
        "✅ 1K / 2K / 4K resolution intent support"
    )
    print(
        "✅ Telegram Preview + Original"
    )
    print(
        "✅ Smart Engine version:",
        SMART_ENGINE_VERSION,
    )
    print(
        "✅ Image Engine status:",
        status.get(
            "ok"
        ),
    )
    print("")

    return {
        "ok":
            True,

        "already_installed":
            False,

        "runtime_version":
            VERSION,

        "status":
            status,

        "creative_brain":
            True,

        "masterpiece":
            True,

        "smart_fallback":
            True,

        "merchant_payments":
            True,
    }


# =========================================================
# ZERO-API SELF TEST
# =========================================================

if __name__ == "__main__":

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND IMAGE TELEGRAM SELF TEST"
    )
    print(
        " VERSION",
        VERSION,
    )
    print(
        "=========================================="
    )

    failures = []

    if not callable(
        install
    ):

        failures.append(
            "install"
        )

    merchant = detect_runtime_benefit_family(
        "خدمات التجارة الإلكترونية ونقاط البيع"
    )

    if merchant != "merchant_payments":

        failures.append(
            "merchant_payments"
        )

    ratio = detect_aspect_ratio(
        "اعلان 2k 4:5"
    )

    if ratio != "4:5":

        failures.append(
            "aspect_ratio"
        )

    image_request = (
        looks_like_image_generation_request(
            "أنشئ صورة إعلانية لبنك STC Bank"
        )
    )

    if not image_request:

        failures.append(
            "image_request"
        )

    if failures:

        print(
            "❌ SELF TEST FAILED:",
            failures,
        )

        raise RuntimeError(
            "XPAND image telegram self-test failed."
        )

    print(
        "✅ install(): PASS"
    )
    print(
        "✅ merchant_payments: PASS"
    )
    print(
        "✅ 4:5 detection: PASS"
    )
    print(
        "✅ image request detection: PASS"
    )
    print(
        "✅ SELF TEST: PASS"
    )
    print(
        "🚫 No API calls were made"
    )
    print("")
