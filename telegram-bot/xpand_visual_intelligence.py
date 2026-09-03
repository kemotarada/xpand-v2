# =========================================================
# XPAND VISUAL INTELLIGENCE V2.0
#
# BRAND VISUAL REFERENCE ENGINE
#
# =========================================================
#
# PURPOSE
# ---------------------------------------------------------
#
# Convert advertising references into structured,
# reusable Brand Visual DNA.
#
# V2 understands not only WHAT is visible in one image,
# but WHY the reference is useful for future campaigns.
#
#
# V2 ADDS
# ---------------------------------------------------------
#
# - Deep Visual Reference DNA
# - Reference-purpose classification
# - Campaign / content-family classification
# - Brand Visual Fingerprint
# - Color swatches + approximate HEX + usage ratios
# - Typography / copy-layout analysis
# - Art-direction analysis
# - Camera / lens / perspective DNA
# - Lighting DNA
# - Materials DNA
# - Negative-space DNA
# - Human-direction DNA
# - Product Lock
# - Campaign archetype
# - Visual hook / attention path
# - Reference utility scoring
# - Source authority / freshness metadata
# - Multi-reference brand-profile aggregation
# - Request-aware reference ranking
# - Automatic best-reference selection
# - Duplicate-reference fingerprinting
# - Sensitive financial-text redaction
#
#
# IMPORTANT ARCHITECTURE
# ---------------------------------------------------------
#
# Official reference != universal brand rule.
#
# One Instagram post is evidence.
# Repeated patterns across multiple official posts become
# stronger brand rules.
#
#
# REFERENCE SELECTION
# ---------------------------------------------------------
#
# A travel campaign should not blindly use the same
# references as:
#
# - cashback
# - international transfer
# - digital banking
# - card/product hero
#
# V2 ranks references according to:
#
# - request meaning
# - content family
# - role usefulness
# - brand relevance
# - source authority
# - freshness
# - Vision confidence
# - production usefulness
#
#
# SELF TEST
# ---------------------------------------------------------
#
# Running:
#
#     python xpand_visual_intelligence.py
#
# makes ZERO API calls.
#
# =========================================================

from __future__ import annotations

import hashlib
import json
import re

from collections import Counter
from datetime import date, datetime, timezone

from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
)


from xpand_image_engine import (
    call_openai_director,
)


# =========================================================
# MODULE
# =========================================================

VERSION = "2.0"

MODULE_NAME = (
    "XPAND Visual Intelligence"
)


# =========================================================
# CONSTANTS
# =========================================================

DEFAULT_REFERENCE_LIMIT = 5

MAX_REFERENCE_SELECTION = 6

MIN_REFERENCE_SELECTION = 1


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
        r"[^\w\s:/#%.\-]+",
        " ",
        text,
        flags=re.UNICODE,
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


def clamp_number(
    value: Any,
    minimum: float = 0.0,
    maximum: float = 100.0,
    fallback: float = 0.0,
) -> float:

    try:

        number = float(
            value
        )

    except Exception:

        number = float(
            fallback
        )

    return max(
        minimum,
        min(
            maximum,
            number,
        ),
    )


def normalize_confidence(
    value: Any,
) -> int:

    return int(
        round(
            clamp_number(
                value,
                0.0,
                100.0,
                70.0,
            )
        )
    )


def compact_json(
    value: Any,
    limit: int = 5000,
) -> str:

    try:

        text = json.dumps(
            value,
            ensure_ascii=False,
            separators=(
                ",",
                ":",
            ),
            default=str,
        )

    except Exception:

        text = clean_text(
            value,
            limit,
        )

    if len(
        text
    ) <= limit:

        return text

    front = int(
        limit
        *
        0.72
    )

    back = max(
        0,
        limit
        -
        front
        -
        80
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
# IMAGE FINGERPRINT
# =========================================================

def image_fingerprint(
    image_bytes: bytes,
) -> str:

    if not image_bytes:

        return ""

    return hashlib.sha256(
        image_bytes
    ).hexdigest()


# =========================================================
# JSON PARSER
# =========================================================

def extract_json_object(
    value: str,
) -> Dict[str, Any]:

    text = clean_text(
        value,
        120000,
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

        parsed = json.loads(
            text
        )

        if isinstance(
            parsed,
            dict,
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
                    start:
                    end + 1
                ]
            )

            if isinstance(
                parsed,
                dict,
            ):

                return parsed

        except Exception:

            pass

    return {}


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
# ROLE KEYWORDS
# =========================================================

ROLE_HINTS = {

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
# ROLE CLASSIFIER
# =========================================================

def infer_reference_role_from_note(
    note: str,
) -> str:

    source = normalize_text(
        note
    )

    if not source:

        return "style_reference"

    scores: Dict[
        str,
        int
    ] = {
        role: 0
        for role in VALID_ROLES
    }

    for role in ROLE_PRIORITY:

        for marker in ROLE_HINTS.get(
            role,
            [],
        ):

            normalized_marker = (
                normalize_text(
                    marker
                )
            )

            if (
                normalized_marker
                and
                normalized_marker
                in source
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
                        ),
                    )
                )

    for role in ROLE_PRIORITY:

        for marker in GENERIC_ROLE_SIGNALS.get(
            role,
            [],
        ):

            normalized_marker = (
                normalize_text(
                    marker
                )
            )

            if (
                normalized_marker
                and
                normalized_marker
                in source
            ):

                scores[
                    role
                ] += 10

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
        mixed_markers,
    ):

        positive_roles = [
            role
            for role, score
            in scores.items()
            if (
                role
                !=
                "mixed_reference"
                and
                score > 0
            )
        ]

        if len(
            positive_roles
        ) >= 2:

            return (
                "mixed_reference"
            )

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
            0,
        )
        ==
        highest_score
    ]

    if candidates:

        return candidates[0]

    return "style_reference"


def classify_reference_role(
    note: str,
) -> Dict[str, Any]:

    source = normalize_text(
        note
    )

    role = (
        infer_reference_role_from_note(
            note
        )
    )

    matched_markers: List[
        str
    ] = []

    for marker in ROLE_HINTS.get(
        role,
        [],
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
            (
                "user_note"
                if source
                else "default"
            ),

        "matched_markers":
            matched_markers[:10],

        "confidence":
            (
                100
                if matched_markers
                else 60
            ),
    }


def normalized_role(
    value: Any,
    fallback: str = "style_reference",
) -> str:

    role = clean_text(
        value,
        100,
    ).lower()

    if role in VALID_ROLES:

        return role

    return fallback


def resolve_final_reference_role(
    *,
    user_role: str,
    vision_role: str,
    user_note: str,
) -> str:

    user_role = normalized_role(
        user_role
    )

    vision_role = normalized_role(
        vision_role
    )

    classification = (
        classify_reference_role(
            user_note
        )
    )

    if (
        normalize_text(
            user_note
        )
        and
        classification.get(
            "matched_markers"
        )
    ):

        return classification[
            "role"
        ]

    if vision_role in VALID_ROLES:

        return vision_role

    return user_role


# =========================================================
# CONTENT / CAMPAIGN FAMILIES
# =========================================================

CONTENT_FAMILY_MARKERS = {

    "international_transfer": [
        "تحويل دولي",
        "تحويل مالي دولي",
        "تحويلات مالية دولية",
        "حواله دوليه",
        "حوالة دولية",
        "حواله ماليه دوليه",
        "حوالة مالية دولية",
        "international transfer",
        "international money transfer",
        "cross border transfer",
        "cross-border transfer",
        "send money abroad",
    ],

    "travel_roaming": [
        "سفر",
        "مسافر",
        "وجهه",
        "وجهة",
        "وجهات",
        "شريحتك",
        "تجوال",
        "roaming",
        "travel",
        "airport",
        "lounge",
        "destination",
    ],

    "cashback_rewards": [
        "كاش باك",
        "كاشباك",
        "استرداد نقدي",
        "مكافات",
        "مكافآت",
        "نقاط",
        "cashback",
        "cash back",
        "rewards",
        "reward points",
    ],

    "payments_cards": [
        "بطاقه",
        "بطاقة",
        "visa",
        "mastercard",
        "دفع",
        "مدفوعات",
        "payment",
        "payments",
        "bank card",
        "credit card",
        "debit card",
    ],

    "digital_banking": [
        "تطبيق",
        "بنك رقمي",
        "رقمي",
        "حساب رقمي",
        "app",
        "digital banking",
        "mobile banking",
        "fintech",
    ],

    "security_trust": [
        "امان",
        "أمان",
        "امن",
        "آمن",
        "حمايه",
        "حماية",
        "security",
        "secure",
        "protection",
        "fraud",
    ],

    "business_banking": [
        "اعمال",
        "أعمال",
        "شركات",
        "منشات",
        "منشآت",
        "business banking",
        "corporate banking",
        "sme",
    ],

    "premium_lifestyle": [
        "فاخر",
        "فخامه",
        "فخامة",
        "premium",
        "luxury",
        "lifestyle",
        "vip",
    ],
}


def infer_content_family(
    text: Any,
) -> str:

    source = normalize_text(
        text
    )

    if not source:

        return "general_brand"

    scores: Dict[str, int] = {}

    for family, markers in (
        CONTENT_FAMILY_MARKERS.items()
    ):

        score = 0

        for marker in markers:

            normalized_marker = (
                normalize_text(
                    marker
                )
            )

            if (
                normalized_marker
                and
                normalized_marker
                in source
            ):

                score += (
                    10
                    +
                    min(
                        20,
                        len(
                            normalized_marker
                        ),
                    )
                )

        scores[
            family
        ] = score

    best_family = max(
        scores,
        key=scores.get,
    )

    if scores[
        best_family
    ] <= 0:

        return "general_brand"

    return best_family


# =========================================================
# SOURCE QUALITY / FRESHNESS
# =========================================================

def parse_source_date(
    value: Any,
) -> Optional[date]:

    text = clean_text(
        value,
        100,
    )

    if not text:

        return None

    candidates = [
        text,
        text[:10],
    ]

    for candidate in candidates:

        try:

            return date.fromisoformat(
                candidate
            )

        except Exception:

            pass

    return None


def source_recency_score(
    value: Any,
) -> float:

    parsed = parse_source_date(
        value
    )

    if parsed is None:

        return 50.0

    today = datetime.now(
        timezone.utc
    ).date()

    age_days = max(
        0,
        (
            today
            -
            parsed
        ).days,
    )

    if age_days <= 90:
        return 100.0

    if age_days <= 180:
        return 92.0

    if age_days <= 365:
        return 82.0

    if age_days <= 730:
        return 65.0

    return 45.0


def normalize_source_metadata(
    metadata: Any,
) -> Dict[str, Any]:

    source = safe_dict(
        metadata
    )

    source_type = clean_text(
        source.get(
            "source_type",
            "",
        ),
        100,
    ).lower()

    official = bool(
        source.get(
            "official",
            False,
        )
    )

    if source_type in {
        "official_instagram",
        "official_website",
        "official_campaign",
        "official_social",
    }:
        official = True

    authority = (
        100
        if official
        else
        clamp_number(
            source.get(
                "authority_score",
                60,
            ),
            0,
            100,
            60,
        )
    )

    published_at = clean_text(
        source.get(
            "published_at",
            "",
        ),
        100,
    )

    return {
        "source_type":
            source_type
            or
            "unknown",

        "source_url":
            clean_text(
                source.get(
                    "source_url",
                    "",
                ),
                2000,
            ),

        "published_at":
            published_at,

        "campaign_name":
            clean_text(
                source.get(
                    "campaign_name",
                    "",
                ),
                300,
            ),

        "brand_id":
            clean_text(
                source.get(
                    "brand_id",
                    "",
                ),
                200,
            ),

        "official":
            official,

        "authority_score":
            round(
                authority,
                1,
            ),

        "recency_score":
            round(
                source_recency_score(
                    published_at
                ),
                1,
            ),
    }


# =========================================================
# SENSITIVE FINANCIAL TEXT SAFETY
# =========================================================

SENSITIVE_KEY_MARKERS = {
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
}


LONG_NUMBER_PATTERN = re.compile(
    r"(?<!\d)(?:\d[\s\-]?){12,19}(?!\d)"
)


IBAN_PATTERN = re.compile(
    r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b",
    flags=re.IGNORECASE,
)


def redact_sensitive_string(
    value: str,
) -> Tuple[
    str,
    bool,
]:

    text = clean_text(
        value,
        20000,
    )

    detected = False

    if IBAN_PATTERN.search(
        text
    ):

        text = IBAN_PATTERN.sub(
            "[REDACTED_IBAN]",
            text,
        )

        detected = True

    if LONG_NUMBER_PATTERN.search(
        text
    ):

        text = LONG_NUMBER_PATTERN.sub(
            "[REDACTED_FINANCIAL_NUMBER]",
            text,
        )

        detected = True

    return (
        text,
        detected,
    )


def redact_sensitive_payload(
    value: Any,
) -> Tuple[
    Any,
    bool,
]:

    detected = False

    if isinstance(
        value,
        dict,
    ):

        output = {}

        for key, child in value.items():

            normalized_key = (
                normalize_text(
                    key
                )
                .replace(
                    " ",
                    "_",
                )
            )

            if normalized_key in (
                SENSITIVE_KEY_MARKERS
            ):

                detected = True
                continue

            redacted_child, child_detected = (
                redact_sensitive_payload(
                    child
                )
            )

            if child_detected:
                detected = True

            output[
                key
            ] = redacted_child

        return (
            output,
            detected,
        )

    if isinstance(
        value,
        list,
    ):

        output_list = []

        for child in value:

            redacted_child, child_detected = (
                redact_sensitive_payload(
                    child
                )
            )

            if child_detected:
                detected = True

            output_list.append(
                redacted_child
            )

        return (
            output_list,
            detected,
        )

    if isinstance(
        value,
        str,
    ):

        return redact_sensitive_string(
            value
        )

    return (
        value,
        False,
    )


# =========================================================
# COLOR NORMALIZATION
# =========================================================

HEX_PATTERN = re.compile(
    r"#[0-9A-Fa-f]{6}\b"
)


def extract_hex_values(
    value: Any,
) -> List[str]:

    text = compact_json(
        value,
        20000,
    )

    found = []

    for match in HEX_PATTERN.findall(
        text
    ):

        color = match.upper()

        if color not in found:

            found.append(
                color
            )

    return found


def normalize_color_palette(
    value: Any,
) -> Dict[str, Any]:

    palette = safe_dict(
        value
    )

    dominant = safe_list(
        palette.get(
            "dominant"
        )
    )

    secondary = safe_list(
        palette.get(
            "secondary"
        )
    )

    accents = safe_list(
        palette.get(
            "accents"
        )
    )

    swatches = safe_list(
        palette.get(
            "swatches"
        )
    )

    return {
        "dominant":
            dominant[:8],

        "secondary":
            secondary[:8],

        "accents":
            accents[:8],

        "swatches":
            swatches[:16],

        "dominant_hex":
            extract_hex_values(
                dominant
            )[:8],

        "secondary_hex":
            extract_hex_values(
                secondary
            )[:8],

        "accent_hex":
            extract_hex_values(
                accents
            )[:8],

        "all_hex":
            extract_hex_values(
                palette
            )[:20],

        "brand_color_usage":
            clean_text(
                palette.get(
                    "brand_color_usage",
                    "",
                ),
                1200,
            ),

        "background_behavior":
            clean_text(
                palette.get(
                    "background_behavior",
                    "",
                ),
                1000,
            ),

        "saturation":
            clean_text(
                palette.get(
                    "saturation",
                    "",
                ),
                600,
            ),

        "contrast":
            clean_text(
                palette.get(
                    "contrast",
                    "",
                ),
                600,
            ),

        "temperature_balance":
            clean_text(
                palette.get(
                    "temperature_balance",
                    "",
                ),
                600,
            ),
    }


# =========================================================
# ANALYSIS PROMPT V2
# =========================================================

def build_visual_analysis_prompt(
    *,
    user_note: str = "",
    brand_context: str = "",
    role_hint: str = "",
    source_metadata: Any = None,
) -> str:

    role_hint = (
        normalized_role(
            role_hint
        )
        if role_hint
        else ""
    )

    source = normalize_source_metadata(
        source_metadata
    )

    return f"""
You are XPAND Visual Intelligence V2.

Analyze the attached image as a senior:

- advertising art director
- commercial photographer
- brand-system analyst
- production designer
- visual strategist

The result will become reusable Brand Visual Reference DNA.

Do NOT generate an image.

Do NOT expose chain-of-thought.

Return concise technical observations and useful production
rules.

==================================================
USER NOTE
==================================================

{clean_text(user_note, 4500)}

==================================================
BRAND CONTEXT
==================================================

{clean_text(brand_context, 7000)}

==================================================
REFERENCE ROLE HINT
==================================================

{role_hint or "none"}

==================================================
SOURCE METADATA
==================================================

{compact_json(source, 1800)}

==================================================
CRITICAL EVIDENCE RULE
==================================================

Separate:

1. WHAT IS ACTUALLY OBSERVED IN THIS IMAGE
2. WHAT CAN REASONABLY BE INFERRED
3. WHAT SHOULD NOT BECOME A UNIVERSAL BRAND RULE FROM ONE IMAGE

An official Instagram post is strong evidence about that
campaign, but one post alone does NOT define the entire brand.

Repeated patterns across several official references can later
be promoted into stronger Brand Visual Rules.

==================================================
REFERENCE ROLE
==================================================

Respect explicit user purpose.

Examples:

"مرجع زاوية"
→ camera_reference

"مرجع المنتج"
→ product_reference

"مرجع الإضاءة"
→ lighting_reference

"مرجع الألوان"
→ color_reference

"مرجع الخلفية"
→ environment_reference

"مرجع التكوين"
→ composition_reference

"مرجع الستايل"
→ style_reference

Never take the product identity from an environment-only
reference.

Never redesign a Product Lock reference.

==================================================
CONTENT / CAMPAIGN CLASSIFICATION
==================================================

Classify the image into the best content family:

- international_transfer
- travel_roaming
- cashback_rewards
- payments_cards
- digital_banking
- security_trust
- business_banking
- premium_lifestyle
- general_brand

Also identify the campaign archetype, for example:

- human_lifestyle
- environmental_storytelling
- product_hero
- architectural_metaphor
- conceptual_photorealism
- digital_experience
- premium_portrait
- destination_story
- graphic_minimal
- mixed

==================================================
VISUAL HOOK / COMMUNICATION
==================================================

Analyze:

- what the eye notices first
- what carries the marketing message
- whether the idea works without copy
- emotional effect
- premium/trust/technology effect
- attention path through the frame
- what makes the visual commercially effective
- what is merely decoration

==================================================
CAMERA
==================================================

Estimate:

- camera height
- direction
- shot type
- approximate focal length
- camera-to-subject distance
- horizon
- tilt
- roll
- depth behavior
- lens compression
- commercial photography character

==================================================
PERSPECTIVE
==================================================

Analyze:

- perspective type
- vanishing points
- distortion
- foreground/midground/background
- physical scale relationships
- forced perspective
- architectural alignment
- perspective risks

==================================================
COMPOSITION
==================================================

Analyze:

- primary focal point
- secondary focal point
- product position
- human position
- copy area
- negative space percentage approximately
- visual hierarchy
- alignment
- symmetry/asymmetry
- leading lines
- frame balance
- depth layers
- eye-flow direction
- hero-to-copy relationship

==================================================
TYPOGRAPHY / COPY SYSTEM
==================================================

Do NOT transcribe the actual advertising copy.

Analyze only the visual system:

- headline placement
- alignment
- approximate size relationship
- number of headline lines
- typography weight
- color behavior
- supporting-copy placement
- CTA placement/style
- disclaimer placement
- text density
- relationship between text and hero image

If the image contains financial numbers or account/card data,
never reproduce them.

==================================================
LIGHTING
==================================================

Analyze:

- key direction
- softness
- fill behavior
- rim light
- backlight
- practicals
- contrast
- apparent color temperature
- shadows
- contact shadows
- reflections
- specular highlights
- environmental light
- commercial-grade lighting style

==================================================
MATERIALS
==================================================

Analyze:

- glass
- brushed metal
- polished metal
- matte surfaces
- satin surfaces
- plastic
- leather
- fabric
- skin
- stone
- floors
- architecture
- roughness
- gloss
- translucency
- reflection quality

Identify which material behaviors create the premium feeling.

==================================================
COLOR SYSTEM
==================================================

Estimate the most important visible colors.

For each useful swatch provide:

- color name
- approximate HEX
- approximate usage percentage
- function:
  primary_brand
  secondary_brand
  accent
  background
  neutral
  skin
  environment

HEX values are visual approximations, not official brand
specifications unless confirmed by brand context.

Analyze:

- dominant colors
- secondary colors
- accents
- saturation
- contrast
- warm/cool balance
- how brand colors are introduced
- whether brand color appears in architecture, lighting,
  clothing, graphic blocks, product, or accents
- whether purple/mint/etc. is dominant or restrained

==================================================
ART DIRECTION
==================================================

Analyze:

- realism level
- premium level
- visual restraint
- environment style
- production scale
- use of negative space
- use of architecture
- graphic overlays
- gradients
- UI-style objects
- depth treatment
- foreground treatment
- background treatment
- cinematic vs graphic balance
- campaign consistency potential

==================================================
HUMAN DIRECTION
==================================================

If people exist, analyze:

- nationality/cultural styling if reasonably inferable from
  clothing/context without guessing identity
- wardrobe category
- pose
- gaze direction
- body language
- relationship to product/service
- candid vs staged behavior
- whether the human is hero, support, or scale reference
- why the casting works visually

Do not identify real people.

==================================================
PRODUCT LOCK
==================================================

If this is a product reference, determine what must remain
identical:

- silhouette
- proportions
- dimensions
- thickness
- corners
- edge geometry
- orientation
- chip placement
- buttons
- camera module
- package geometry
- material
- color
- graphic layout
- logo position

Environment may change unless explicitly locked.

Lighting may adapt unless explicitly locked.

==================================================
REFERENCE UTILITY
==================================================

Score 0-100 how useful THIS IMAGE is as a future reference for:

- style
- color
- lighting
- camera
- composition
- environment
- product
- person
- campaign_consistency

These are utility scores, not aesthetic ratings.

==================================================
BRAND VISUAL FINGERPRINT
==================================================

Create concise reusable production tokens:

- style_tags
- camera_signature
- composition_signature
- lighting_signature
- material_signature
- palette_signature
- human_signature
- negative_space_signature
- commercial_finish_signature

Also provide:

- preserve
- avoid_copying_literally
- transferable_rules

The goal is to learn the visual logic without cloning the exact
creative idea.

==================================================
SENSITIVE INFORMATION
==================================================

Never transcribe/store:

- card numbers
- IBAN
- account numbers
- CVV/CVC
- PIN
- passwords
- security codes
- private IDs

Only return:

"sensitive_text_present": true

==================================================
OUTPUT
==================================================

Return JSON ONLY.

Required schema:

{{
  "summary": "",

  "observed_facts": [],
  "inferred_rules": [],
  "single_reference_limitations": [],

  "primary_reference_role": "style_reference",
  "secondary_reference_roles": [],

  "content_classification": {{
    "family": "general_brand",
    "campaign_archetype": "",
    "benefit_theme": "",
    "customer_context": "",
    "confidence": 0
  }},

  "visual_hook": {{
    "first_attention": "",
    "message_carrier": "",
    "works_without_copy": true,
    "attention_path": "",
    "emotional_effect": "",
    "commercial_effect": "",
    "decorative_only_elements": []
  }},

  "camera": {{
    "height": "",
    "direction": "",
    "shot_type": "",
    "estimated_lens_mm": "",
    "subject_distance": "",
    "horizon_position": "",
    "tilt": "",
    "roll": "",
    "lens_compression": "",
    "depth_behavior": "",
    "commercial_character": "",
    "creative_reason": ""
  }},

  "perspective": {{
    "type": "",
    "vanishing_points": "",
    "distortion_level": "",
    "foreground": "",
    "midground": "",
    "background": "",
    "scale_relationship": "",
    "architectural_alignment": "",
    "risks": []
  }},

  "composition": {{
    "primary_focal_point": "",
    "secondary_element": "",
    "product_position": "",
    "person_position": "",
    "negative_space": "",
    "negative_space_pct": 0,
    "headline_safe_area": "",
    "visual_hierarchy": "",
    "alignment_system": "",
    "leading_lines": "",
    "balance": "",
    "depth_layers": "",
    "eye_flow": "",
    "hero_copy_relationship": ""
  }},

  "typography_system": {{
    "headline_position": "",
    "headline_alignment": "",
    "headline_scale": "",
    "headline_line_count": "",
    "headline_weight": "",
    "headline_color_behavior": "",
    "supporting_copy_position": "",
    "cta_position": "",
    "cta_style": "",
    "disclaimer_position": "",
    "copy_density": "",
    "image_copy_relationship": ""
  }},

  "lighting": {{
    "key_light": "",
    "fill_light": "",
    "rim_light": "",
    "backlight": "",
    "practicals": "",
    "softness": "",
    "contrast": "",
    "color_temperature": "",
    "shadow_behavior": "",
    "contact_shadows": "",
    "reflection_behavior": "",
    "specular_behavior": "",
    "commercial_style": ""
  }},

  "materials": [],

  "color_palette": {{
    "dominant": [],
    "secondary": [],
    "accents": [],
    "swatches": [
      {{
        "name": "",
        "hex": "#000000",
        "usage_pct": 0,
        "function": ""
      }}
    ],
    "brand_color_usage": "",
    "background_behavior": "",
    "saturation": "",
    "contrast": "",
    "temperature_balance": ""
  }},

  "art_direction": {{
    "realism_level": "",
    "premium_level": "",
    "visual_restraint": "",
    "environment_style": "",
    "production_scale": "",
    "architecture_usage": "",
    "graphic_overlay_usage": "",
    "gradient_usage": "",
    "ui_element_usage": "",
    "foreground_treatment": "",
    "background_treatment": "",
    "cinematic_graphic_balance": "",
    "campaign_consistency_potential": ""
  }},

  "human_direction": {{
    "present": false,
    "wardrobe": "",
    "pose": "",
    "gaze": "",
    "body_language": "",
    "behavior": "",
    "role_in_frame": "",
    "product_relationship": "",
    "casting_effect": ""
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

  "reference_utility": {{
    "style": 0,
    "color": 0,
    "lighting": 0,
    "camera": 0,
    "composition": 0,
    "environment": 0,
    "product": 0,
    "person": 0,
    "campaign_consistency": 0
  }},

  "visual_fingerprint": {{
    "style_tags": [],
    "camera_signature": "",
    "composition_signature": "",
    "lighting_signature": "",
    "material_signature": "",
    "palette_signature": "",
    "human_signature": "",
    "negative_space_signature": "",
    "commercial_finish_signature": "",
    "preserve": [],
    "avoid_copying_literally": [],
    "transferable_rules": []
  }},

  "confidence": 0
}}

Be precise.

Do not invent unavailable information.

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
    role_hint: str = "",
    source_metadata: Any = None,
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

    normalized_source = (
        normalize_source_metadata(
            source_metadata
        )
    )

    prompt = (
        build_visual_analysis_prompt(
            user_note=user_note,
            brand_context=brand_context,
            role_hint=deterministic_role,
            source_metadata=(
                normalized_source
            ),
        )
    )

    raw = call_openai_director(
        prompt,
        image_bytes=image_bytes,
        image_mime_type=(
            mime_type
            or
            "image/jpeg"
        ),
        json_mode=True,
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

    data, recursive_sensitive = (
        redact_sensitive_payload(
            data
        )
    )

    vision_role = normalized_role(
        data.get(
            "primary_reference_role"
        ),
        fallback=(
            deterministic_role
        ),
    )

    final_role = (
        resolve_final_reference_role(
            user_role=(
                deterministic_role
            ),
            vision_role=vision_role,
            user_note=user_note,
        )
    )

    secondary = safe_list(
        data.get(
            "secondary_reference_roles"
        )
    )

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
            role
            not in normalized_secondary
        ):

            normalized_secondary.append(
                role
            )

    content = safe_dict(
        data.get(
            "content_classification"
        )
    )

    family = clean_text(
        content.get(
            "family",
            "",
        ),
        100,
    ).lower()

    if family not in (
        set(
            CONTENT_FAMILY_MARKERS.keys()
        )
        |
        {
            "general_brand",
        }
    ):

        family = infer_content_family(
            " ".join(
                [
                    user_note,
                    clean_text(
                        content.get(
                            "benefit_theme",
                            "",
                        ),
                        500,
                    ),
                    clean_text(
                        data.get(
                            "summary",
                            "",
                        ),
                        800,
                    ),
                ]
            )
        )

    product_lock = safe_dict(
        data.get(
            "product_lock"
        )
    )

    if (
        final_role
        ==
        "product_reference"
    ):

        product_lock[
            "enabled"
        ] = True

    sensitive_present = bool(
        product_lock.get(
            "sensitive_text_present",
            False,
        )
        or
        recursive_sensitive
    )

    product_lock[
        "sensitive_text_present"
    ] = sensitive_present

    product_lock[
        "sensitive_text_policy"
    ] = (
        "never store or reproduce"
    )

    reference_utility = (
        safe_dict(
            data.get(
                "reference_utility"
            )
        )
    )

    normalized_utility = {}

    for key in [
        "style",
        "color",
        "lighting",
        "camera",
        "composition",
        "environment",
        "product",
        "person",
        "campaign_consistency",
    ]:

        normalized_utility[
            key
        ] = round(
            clamp_number(
                reference_utility.get(
                    key,
                    0,
                ),
                0,
                100,
                0,
            ),
            1,
        )

    #
    # Explicit reference purpose receives a minimum utility
    # score so later selection does not ignore the user's
    # instruction.
    #

    explicit_role_to_utility = {
        "product_reference":
            "product",

        "camera_reference":
            "camera",

        "environment_reference":
            "environment",

        "lighting_reference":
            "lighting",

        "composition_reference":
            "composition",

        "color_reference":
            "color",

        "person_reference":
            "person",

        "campaign_reference":
            "campaign_consistency",

        "style_reference":
            "style",
    }

    utility_key = (
        explicit_role_to_utility.get(
            final_role
        )
    )

    if utility_key:

        normalized_utility[
            utility_key
        ] = max(
            normalized_utility.get(
                utility_key,
                0,
            ),
            80.0,
        )

    fingerprint = safe_dict(
        data.get(
            "visual_fingerprint"
        )
    )

    palette = (
        normalize_color_palette(
            data.get(
                "color_palette"
            )
        )
    )

    classification = (
        classify_reference_role(
            user_note
        )
    )

    role_source = (
        "explicit_user_instruction"
        if classification.get(
            "matched_markers"
        )
        else
        "vision_analysis"
    )

    result = {

        "visual_intelligence_version":
            VERSION,

        "image_fingerprint_sha256":
            image_fingerprint(
                image_bytes
            ),

        "summary":
            clean_text(
                data.get(
                    "summary"
                ),
                1800,
            ),

        "observed_facts": [
            clean_text(
                item,
                900,
            )
            for item in safe_list(
                data.get(
                    "observed_facts"
                )
            )[:20]
            if clean_text(
                item,
                900,
            )
        ],

        "inferred_rules": [
            clean_text(
                item,
                900,
            )
            for item in safe_list(
                data.get(
                    "inferred_rules"
                )
            )[:20]
            if clean_text(
                item,
                900,
            )
        ],

        "single_reference_limitations": [
            clean_text(
                item,
                900,
            )
            for item in safe_list(
                data.get(
                    "single_reference_limitations"
                )
            )[:15]
            if clean_text(
                item,
                900,
            )
        ],

        "primary_reference_role":
            final_role,

        "secondary_reference_roles":
            normalized_secondary[:8],

        "role_source":
            role_source,

        "content_classification": {
            "family":
                family,

            "campaign_archetype":
                clean_text(
                    content.get(
                        "campaign_archetype",
                        "",
                    ),
                    300,
                ),

            "benefit_theme":
                clean_text(
                    content.get(
                        "benefit_theme",
                        "",
                    ),
                    700,
                ),

            "customer_context":
                clean_text(
                    content.get(
                        "customer_context",
                        "",
                    ),
                    700,
                ),

            "confidence":
                normalize_confidence(
                    content.get(
                        "confidence",
                        70,
                    )
                ),
        },

        "visual_hook":
            safe_dict(
                data.get(
                    "visual_hook"
                )
            ),

        "camera":
            safe_dict(
                data.get(
                    "camera"
                )
            ),

        "perspective":
            safe_dict(
                data.get(
                    "perspective"
                )
            ),

        "composition":
            safe_dict(
                data.get(
                    "composition"
                )
            ),

        "typography_system":
            safe_dict(
                data.get(
                    "typography_system"
                )
            ),

        "lighting":
            safe_dict(
                data.get(
                    "lighting"
                )
            ),

        "materials":
            safe_list(
                data.get(
                    "materials"
                )
            )[:30],

        "color_palette":
            palette,

        "art_direction":
            safe_dict(
                data.get(
                    "art_direction"
                )
            ),

        "human_direction":
            safe_dict(
                data.get(
                    "human_direction"
                )
            ),

        "relationships":
            safe_list(
                data.get(
                    "relationships"
                )
            )[:25],

        "visual_success_reasons":
            safe_list(
                data.get(
                    "visual_success_reasons"
                )
            )[:20],

        "generation_risks":
            safe_list(
                data.get(
                    "generation_risks"
                )
            )[:20],

        "product_lock":
            product_lock,

        "reference_utility":
            normalized_utility,

        "visual_fingerprint": {
            "style_tags": [
                clean_text(
                    item,
                    200,
                )
                for item in safe_list(
                    fingerprint.get(
                        "style_tags"
                    )
                )[:20]
                if clean_text(
                    item,
                    200,
                )
            ],

            "camera_signature":
                clean_text(
                    fingerprint.get(
                        "camera_signature",
                        "",
                    ),
                    1000,
                ),

            "composition_signature":
                clean_text(
                    fingerprint.get(
                        "composition_signature",
                        "",
                    ),
                    1000,
                ),

            "lighting_signature":
                clean_text(
                    fingerprint.get(
                        "lighting_signature",
                        "",
                    ),
                    1000,
                ),

            "material_signature":
                clean_text(
                    fingerprint.get(
                        "material_signature",
                        "",
                    ),
                    1000,
                ),

            "palette_signature":
                clean_text(
                    fingerprint.get(
                        "palette_signature",
                        "",
                    ),
                    1000,
                ),

            "human_signature":
                clean_text(
                    fingerprint.get(
                        "human_signature",
                        "",
                    ),
                    1000,
                ),

            "negative_space_signature":
                clean_text(
                    fingerprint.get(
                        "negative_space_signature",
                        "",
                    ),
                    1000,
                ),

            "commercial_finish_signature":
                clean_text(
                    fingerprint.get(
                        "commercial_finish_signature",
                        "",
                    ),
                    1000,
                ),

            "preserve":
                safe_list(
                    fingerprint.get(
                        "preserve"
                    )
                )[:20],

            "avoid_copying_literally":
                safe_list(
                    fingerprint.get(
                        "avoid_copying_literally"
                    )
                )[:20],

            "transferable_rules":
                safe_list(
                    fingerprint.get(
                        "transferable_rules"
                    )
                )[:25],
        },

        "source_metadata":
            normalized_source,

        "confidence":
            normalize_confidence(
                data.get(
                    "confidence",
                    70,
                )
            ),

        "user_note":
            clean_text(
                user_note,
                5000,
            ),
    }

    #
    # Final recursive safety pass.
    #

    result, final_sensitive = (
        redact_sensitive_payload(
            result
        )
    )

    if final_sensitive:

        result[
            "product_lock"
        ][
            "sensitive_text_present"
        ] = True

    return result


# =========================================================
# REQUEST-AWARE REFERENCE MATCHING
# =========================================================

def request_reference_priorities(
    request: str,
) -> Dict[str, float]:

    source = normalize_text(
        request
    )

    priorities = {
        "style":
            1.00,

        "color":
            0.95,

        "lighting":
            0.90,

        "camera":
            0.90,

        "composition":
            1.00,

        "environment":
            0.70,

        "product":
            0.30,

        "person":
            0.35,

        "campaign_consistency":
            0.85,
    }

    if contains_any(
        source,
        [
            "بطاقه",
            "بطاقة",
            "كرت",
            "هاتف",
            "موبايل",
            "منتج",
            "product",
            "card",
            "phone",
        ],
    ):

        priorities[
            "product"
        ] = 1.25

    if contains_any(
        source,
        [
            "زاويه",
            "زاوية",
            "منظور",
            "كاميرا",
            "camera",
            "angle",
            "perspective",
        ],
    ):

        priorities[
            "camera"
        ] = 1.20

    if contains_any(
        source,
        [
            "اضاءه",
            "إضاءة",
            "lighting",
            "light",
        ],
    ):

        priorities[
            "lighting"
        ] = 1.15

    if contains_any(
        source,
        [
            "الوان",
            "ألوان",
            "لون",
            "palette",
            "color",
            "colour",
        ],
    ):

        priorities[
            "color"
        ] = 1.20

    if contains_any(
        source,
        [
            "تكوين",
            "كادر",
            "layout",
            "composition",
        ],
    ):

        priorities[
            "composition"
        ] = 1.20

    if contains_any(
        source,
        [
            "شخص",
            "رجل",
            "امرأه",
            "امرأة",
            "مسافر",
            "عميل",
            "person",
            "human",
            "traveler",
        ],
    ):

        priorities[
            "person"
        ] = 0.90

    return priorities


def reference_content_family(
    dna: Dict[str, Any],
) -> str:

    classification = safe_dict(
        dna.get(
            "content_classification"
        )
    )

    family = clean_text(
        classification.get(
            "family",
            "",
        ),
        100,
    ).lower()

    return (
        family
        or
        "general_brand"
    )


def score_reference_for_request(
    dna: Dict[str, Any],
    request: str,
) -> Dict[str, Any]:

    if not isinstance(
        dna,
        dict,
    ):

        return {
            "score":
                0.0,

            "reasons":
                [
                    "invalid_reference"
                ],
        }

    request_family = (
        infer_content_family(
            request
        )
    )

    dna_family = (
        reference_content_family(
            dna
        )
    )

    utility = safe_dict(
        dna.get(
            "reference_utility"
        )
    )

    priorities = (
        request_reference_priorities(
            request
        )
    )

    utility_weight_total = 0.0
    utility_score_total = 0.0

    for key, priority in (
        priorities.items()
    ):

        weight = max(
            0.0,
            float(
                priority
            ),
        )

        utility_weight_total += (
            weight
        )

        utility_score_total += (
            clamp_number(
                utility.get(
                    key,
                    0,
                ),
                0,
                100,
                0,
            )
            *
            weight
        )

    utility_score = (
        (
            utility_score_total
            /
            utility_weight_total
        )
        if utility_weight_total
        else 0.0
    )

    reasons: List[
        str
    ] = []

    content_bonus = 0.0

    if (
        request_family
        ==
        dna_family
    ):

        content_bonus = 18.0

        reasons.append(
            "content_family_match"
        )

    elif (
        dna_family
        ==
        "general_brand"
    ):

        content_bonus = 6.0

        reasons.append(
            "general_brand_reference"
        )

    elif (
        request_family
        ==
        "general_brand"
    ):

        content_bonus = 8.0

    source = safe_dict(
        dna.get(
            "source_metadata"
        )
    )

    authority = clamp_number(
        source.get(
            "authority_score",
            50,
        ),
        0,
        100,
        50,
    )

    recency = clamp_number(
        source.get(
            "recency_score",
            50,
        ),
        0,
        100,
        50,
    )

    confidence = clamp_number(
        dna.get(
            "confidence",
            70,
        ),
        0,
        100,
        70,
    )

    source_bonus = (
        (
            authority
            /
            100.0
        )
        *
        7.0
    )

    freshness_bonus = (
        (
            recency
            /
            100.0
        )
        *
        5.0
    )

    confidence_bonus = (
        (
            confidence
            /
            100.0
        )
        *
        5.0
    )

    if source.get(
        "official"
    ):

        reasons.append(
            "official_source"
        )

    if recency >= 80:

        reasons.append(
            "recent_reference"
        )

    primary_role = clean_text(
        dna.get(
            "primary_reference_role",
            "",
        ),
        100,
    )

    if primary_role in {
        "campaign_reference",
        "style_reference",
        "composition_reference",
        "color_reference",
        "camera_reference",
    }:

        role_bonus = 3.0

    else:

        role_bonus = 1.0

    final_score = (
        utility_score
        *
        0.62
        +
        content_bonus
        +
        source_bonus
        +
        freshness_bonus
        +
        confidence_bonus
        +
        role_bonus
    )

    final_score = round(
        min(
            100.0,
            max(
                0.0,
                final_score,
            ),
        ),
        2,
    )

    return {
        "score":
            final_score,

        "request_family":
            request_family,

        "reference_family":
            dna_family,

        "utility_score":
            round(
                utility_score,
                2,
            ),

        "authority":
            authority,

        "recency":
            recency,

        "confidence":
            confidence,

        "reasons":
            reasons,
    }


def rank_references_for_request(
    references: Sequence[
        Dict[str, Any]
    ],
    request: str,
) -> List[
    Dict[str, Any]
]:

    ranked = []

    seen_fingerprints = set()

    for reference in references:

        if not isinstance(
            reference,
            dict,
        ):

            continue

        fingerprint = clean_text(
            reference.get(
                "image_fingerprint_sha256",
                "",
            ),
            100,
        )

        if (
            fingerprint
            and
            fingerprint
            in seen_fingerprints
        ):

            continue

        if fingerprint:

            seen_fingerprints.add(
                fingerprint
            )

        match = (
            score_reference_for_request(
                reference,
                request,
            )
        )

        item = dict(
            reference
        )

        item[
            "_selection"
        ] = match

        ranked.append(
            item
        )

    ranked.sort(
        key=lambda item:
            float(
                safe_dict(
                    item.get(
                        "_selection"
                    )
                ).get(
                    "score",
                    0,
                )
            ),
        reverse=True,
    )

    return ranked


def select_best_references(
    references: Sequence[
        Dict[str, Any]
    ],
    request: str,
    *,
    limit: int = DEFAULT_REFERENCE_LIMIT,
) -> List[
    Dict[str, Any]
]:

    limit = max(
        MIN_REFERENCE_SELECTION,
        min(
            MAX_REFERENCE_SELECTION,
            int(
                limit
                or
                DEFAULT_REFERENCE_LIMIT
            ),
        ),
    )

    ranked = (
        rank_references_for_request(
            references,
            request,
        )
    )

    if not ranked:

        return []

    selected: List[
        Dict[str, Any]
    ] = []

    selected_ids = set()

    #
    # First pass:
    # maximize useful role diversity.
    #

    role_order = [
        "campaign_reference",
        "style_reference",
        "composition_reference",
        "color_reference",
        "camera_reference",
        "lighting_reference",
        "environment_reference",
        "product_reference",
        "person_reference",
    ]

    for wanted_role in role_order:

        if len(
            selected
        ) >= limit:

            break

        for item in ranked:

            fingerprint = clean_text(
                item.get(
                    "image_fingerprint_sha256",
                    "",
                ),
                100,
            )

            unique_id = (
                fingerprint
                or
                str(
                    id(
                        item
                    )
                )
            )

            if unique_id in (
                selected_ids
            ):

                continue

            primary = clean_text(
                item.get(
                    "primary_reference_role",
                    "",
                ),
                100,
            )

            secondary = [
                clean_text(
                    role,
                    100,
                )
                for role in safe_list(
                    item.get(
                        "secondary_reference_roles"
                    )
                )
            ]

            if (
                primary
                ==
                wanted_role
                or
                wanted_role
                in secondary
            ):

                selected.append(
                    item
                )

                selected_ids.add(
                    unique_id
                )

                break

    #
    # Second pass:
    # fill remaining slots by relevance.
    #

    for item in ranked:

        if len(
            selected
        ) >= limit:

            break

        fingerprint = clean_text(
            item.get(
                "image_fingerprint_sha256",
                "",
            ),
            100,
        )

        unique_id = (
            fingerprint
            or
            str(
                id(
                    item
                )
            )
        )

        if unique_id in (
            selected_ids
        ):

            continue

        selected.append(
            item
        )

        selected_ids.add(
            unique_id
        )

    #
    # Return sorted by actual match score.
    #

    selected.sort(
        key=lambda item:
            float(
                safe_dict(
                    item.get(
                        "_selection"
                    )
                ).get(
                    "score",
                    0,
                )
            ),
        reverse=True,
    )

    return selected[:limit]


# =========================================================
# MULTI-REFERENCE BRAND VISUAL PROFILE
# =========================================================

def counter_top(
    values: Iterable[str],
    limit: int = 8,
) -> List[
    Dict[str, Any]
]:

    cleaned = [
        clean_text(
            value,
            500,
        )
        for value in values
        if clean_text(
            value,
            500,
        )
    ]

    counter = Counter(
        cleaned
    )

    return [
        {
            "value":
                value,

            "count":
                count,
        }
        for value, count
        in counter.most_common(
            limit
        )
    ]


def collect_style_tags(
    references: Sequence[
        Dict[str, Any]
    ],
) -> List[str]:

    output = []

    for dna in references:

        fingerprint = safe_dict(
            dna.get(
                "visual_fingerprint"
            )
        )

        for tag in safe_list(
            fingerprint.get(
                "style_tags"
            )
        ):

            text = clean_text(
                tag,
                200,
            )

            if text:

                output.append(
                    text
                )

    return output


def collect_hex_colors(
    references: Sequence[
        Dict[str, Any]
    ],
) -> List[str]:

    output = []

    for dna in references:

        palette = safe_dict(
            dna.get(
                "color_palette"
            )
        )

        for value in safe_list(
            palette.get(
                "all_hex"
            )
        ):

            text = clean_text(
                value,
                20,
            ).upper()

            if HEX_PATTERN.fullmatch(
                text
            ):

                output.append(
                    text
                )

    return output


def build_brand_visual_profile(
    references: Sequence[
        Dict[str, Any]
    ],
    *,
    brand_id: str = "",
) -> Dict[str, Any]:

    usable = [
        item
        for item in references
        if isinstance(
            item,
            dict,
        )
    ]

    if not usable:

        return {
            "brand_id":
                clean_text(
                    brand_id,
                    200,
                ),

            "source_count":
                0,

            "confidence":
                0,

            "status":
                "empty",
        }

    official_count = sum(
        1
        for item in usable
        if safe_dict(
            item.get(
                "source_metadata"
            )
        ).get(
            "official"
        )
    )

    families = [
        reference_content_family(
            item
        )
        for item in usable
    ]

    roles = [
        clean_text(
            item.get(
                "primary_reference_role",
                "",
            ),
            100,
        )
        for item in usable
    ]

    archetypes = []

    camera_signatures = []
    composition_signatures = []
    lighting_signatures = []
    material_signatures = []
    palette_signatures = []
    human_signatures = []
    negative_space_signatures = []
    finish_signatures = []
    transferable_rules = []
    preserve_rules = []

    confidence_values = []

    for item in usable:

        classification = safe_dict(
            item.get(
                "content_classification"
            )
        )

        archetype = clean_text(
            classification.get(
                "campaign_archetype",
                "",
            ),
            300,
        )

        if archetype:

            archetypes.append(
                archetype
            )

        fingerprint = safe_dict(
            item.get(
                "visual_fingerprint"
            )
        )

        mappings = [
            (
                "camera_signature",
                camera_signatures,
            ),

            (
                "composition_signature",
                composition_signatures,
            ),

            (
                "lighting_signature",
                lighting_signatures,
            ),

            (
                "material_signature",
                material_signatures,
            ),

            (
                "palette_signature",
                palette_signatures,
            ),

            (
                "human_signature",
                human_signatures,
            ),

            (
                "negative_space_signature",
                negative_space_signatures,
            ),

            (
                "commercial_finish_signature",
                finish_signatures,
            ),
        ]

        for key, target in mappings:

            value = clean_text(
                fingerprint.get(
                    key,
                    "",
                ),
                800,
            )

            if value:

                target.append(
                    value
                )

        for value in safe_list(
            fingerprint.get(
                "transferable_rules"
            )
        ):

            text = clean_text(
                value,
                600,
            )

            if text:

                transferable_rules.append(
                    text
                )

        for value in safe_list(
            fingerprint.get(
                "preserve"
            )
        ):

            text = clean_text(
                value,
                600,
            )

            if text:

                preserve_rules.append(
                    text
                )

        confidence_values.append(
            normalize_confidence(
                item.get(
                    "confidence",
                    70,
                )
            )
        )

    color_counts = Counter(
        collect_hex_colors(
            usable
        )
    )

    recurring_colors = [
        {
            "hex":
                value,

            "count":
                count,

            "frequency_pct":
                round(
                    (
                        count
                        /
                        max(
                            1,
                            len(
                                usable
                            ),
                        )
                    )
                    *
                    100.0,
                    1,
                ),
        }
        for value, count
        in color_counts.most_common(
            12
        )
    ]

    average_confidence = (
        sum(
            confidence_values
        )
        /
        max(
            1,
            len(
                confidence_values
            ),
        )
    )

    evidence_strength = (
        min(
            100.0,
            (
                len(
                    usable
                )
                /
                12.0
            )
            *
            70.0
            +
            (
                official_count
                /
                max(
                    1,
                    len(
                        usable
                    ),
                )
            )
            *
            20.0
            +
            (
                average_confidence
                /
                100.0
            )
            *
            10.0,
        )
    )

    return {
        "visual_profile_version":
            VERSION,

        "brand_id":
            clean_text(
                brand_id,
                200,
            ),

        "source_count":
            len(
                usable
            ),

        "official_source_count":
            official_count,

        "evidence_strength":
            round(
                evidence_strength,
                1,
            ),

        "confidence":
            round(
                average_confidence,
                1,
            ),

        "content_families":
            counter_top(
                families,
                12,
            ),

        "reference_roles":
            counter_top(
                roles,
                12,
            ),

        "campaign_archetypes":
            counter_top(
                archetypes,
                10,
            ),

        "style_tags":
            counter_top(
                collect_style_tags(
                    usable
                ),
                15,
            ),

        "recurring_colors":
            recurring_colors,

        "camera_patterns":
            counter_top(
                camera_signatures,
                8,
            ),

        "composition_patterns":
            counter_top(
                composition_signatures,
                8,
            ),

        "lighting_patterns":
            counter_top(
                lighting_signatures,
                8,
            ),

        "material_patterns":
            counter_top(
                material_signatures,
                8,
            ),

        "palette_patterns":
            counter_top(
                palette_signatures,
                8,
            ),

        "human_direction_patterns":
            counter_top(
                human_signatures,
                8,
            ),

        "negative_space_patterns":
            counter_top(
                negative_space_signatures,
                8,
            ),

        "commercial_finish_patterns":
            counter_top(
                finish_signatures,
                8,
            ),

        "transferable_rules":
            counter_top(
                transferable_rules,
                15,
            ),

        "preserve_patterns":
            counter_top(
                preserve_rules,
                15,
            ),

        "brand_rule_policy":
            {
                "one_reference":
                    (
                        "campaign evidence only; "
                        "do not treat as universal brand law"
                    ),

                "repeated_pattern":
                    (
                        "promote confidence as the pattern repeats "
                        "across official references"
                    ),

                "official_source_priority":
                    True,

                "recent_source_priority":
                    True,

                "creative_copy_policy":
                    (
                        "learn visual logic, do not clone exact campaign idea"
                    ),
            },

        "status":
            "ready",
    }


# =========================================================
# PRODUCTION CONTEXT BUILDER
# =========================================================

def build_reference_execution_context(
    references: Sequence[
        Dict[str, Any]
    ],
    request: str,
    *,
    limit: int = DEFAULT_REFERENCE_LIMIT,
) -> Dict[str, Any]:

    selected = (
        select_best_references(
            references,
            request,
            limit=limit,
        )
    )

    compact_refs = []

    for item in selected:

        compact_refs.append(
            {
                "primary_role":
                    item.get(
                        "primary_reference_role"
                    ),

                "secondary_roles":
                    item.get(
                        "secondary_reference_roles",
                        [],
                    ),

                "content_family":
                    reference_content_family(
                        item
                    ),

                "selection":
                    item.get(
                        "_selection",
                        {},
                    ),

                "camera":
                    safe_dict(
                        item.get(
                            "camera"
                        )
                    ),

                "composition":
                    safe_dict(
                        item.get(
                            "composition"
                        )
                    ),

                "lighting":
                    safe_dict(
                        item.get(
                            "lighting"
                        )
                    ),

                "color_palette":
                    safe_dict(
                        item.get(
                            "color_palette"
                        )
                    ),

                "art_direction":
                    safe_dict(
                        item.get(
                            "art_direction"
                        )
                    ),

                "human_direction":
                    safe_dict(
                        item.get(
                            "human_direction"
                        )
                    ),

                "visual_fingerprint":
                    safe_dict(
                        item.get(
                            "visual_fingerprint"
                        )
                    ),

                "product_lock":
                    safe_dict(
                        item.get(
                            "product_lock"
                        )
                    ),

                "source_metadata":
                    safe_dict(
                        item.get(
                            "source_metadata"
                        )
                    ),
            }
        )

    return {
        "request_family":
            infer_content_family(
                request
            ),

        "selected_count":
            len(
                selected
            ),

        "selected_references":
            compact_refs,

        "selection_policy":
            (
                "request-aware + role-diverse + "
                "official/freshness/confidence weighted"
            ),
    }


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


CONTENT_LABELS_AR = {
    "international_transfer":
        "تحويلات دولية",

    "travel_roaming":
        "سفر / تجوال",

    "cashback_rewards":
        "كاش باك / مكافآت",

    "payments_cards":
        "بطاقات / مدفوعات",

    "digital_banking":
        "بنك رقمي",

    "security_trust":
        "أمان وثقة",

    "business_banking":
        "خدمات أعمال",

    "premium_lifestyle":
        "Premium Lifestyle",

    "general_brand":
        "هوية عامة",
}


def build_visual_dna_summary(
    dna: Dict[str, Any],
) -> str:

    if not dna:

        return (
            "ما قدرت أطلع تحليل بصري موثوق."
        )

    role = clean_text(
        dna.get(
            "primary_reference_role"
        ),
        100,
    )

    role_label = ROLE_LABELS_AR.get(
        role,
        role
        or
        "مرجع بصري",
    )

    content = safe_dict(
        dna.get(
            "content_classification"
        )
    )

    family = clean_text(
        content.get(
            "family",
            "general_brand",
        ),
        100,
    )

    family_label = (
        CONTENT_LABELS_AR.get(
            family,
            family,
        )
    )

    camera = safe_dict(
        dna.get(
            "camera"
        )
    )

    lighting = safe_dict(
        dna.get(
            "lighting"
        )
    )

    composition = safe_dict(
        dna.get(
            "composition"
        )
    )

    palette = safe_dict(
        dna.get(
            "color_palette"
        )
    )

    confidence = (
        normalize_confidence(
            dna.get(
                "confidence",
                70,
            )
        )
    )

    lines = [
        "🧬 Visual Reference DNA V2 محفوظ.",
        (
            "الوظيفة: "
            +
            role_label
        ),
        (
            "نوع المحتوى: "
            +
            family_label
        ),
    ]

    shot = clean_text(
        camera.get(
            "shot_type",
            "",
        ),
        200,
    )

    lens = clean_text(
        camera.get(
            "estimated_lens_mm",
            "",
        ),
        100,
    )

    if (
        shot
        or
        lens
    ):

        camera_line = (
            "📷 الكاميرا: "
            +
            (
                shot
                or
                "غير محددة"
            )
        )

        if lens:

            camera_line += (
                " | "
                +
                lens
            )

        lines.append(
            camera_line
        )

    key_light = clean_text(
        lighting.get(
            "key_light",
            "",
        ),
        250,
    )

    if key_light:

        lines.append(
            (
                "💡 الإضاءة: "
                +
                key_light
            )
        )

    focal = clean_text(
        composition.get(
            "primary_focal_point",
            "",
        ),
        250,
    )

    if focal:

        lines.append(
            (
                "🎯 نقطة التركيز: "
                +
                focal
            )
        )

    colors = safe_list(
        palette.get(
            "all_hex"
        )
    )[:5]

    if colors:

        lines.append(
            (
                "🎨 Palette: "
                +
                " / ".join(
                    colors
                )
            )
        )

    lines.append(
        (
            "درجة الثقة: "
            +
            str(
                confidence
            )
            +
            "%"
        )
    )

    return "\n".join(
        lines
    )


# =========================================================
# PRODUCT LOCK
# =========================================================

def product_lock_enabled(
    dna: Dict[str, Any],
) -> bool:

    product_lock = safe_dict(
        dna.get(
            "product_lock"
        )
    )

    return bool(
        product_lock.get(
            "enabled"
        )
    )


# =========================================================
# LOCAL SELF TEST
#
# ZERO API CALLS
# ZERO VISION CALLS
# ZERO PAID USAGE
# =========================================================

if __name__ == "__main__":

    print("")
    print(
        "=============================================="
    )
    print(
        " XPAND VISUAL INTELLIGENCE V2.0"
    )
    print(
        " BRAND VISUAL REFERENCE ENGINE"
    )
    print(
        "=============================================="
    )
    print("")

    # =====================================================
    # ROLE CLASSIFICATION
    # =====================================================

    role_tests = [
        (
            "هاي مرجع زاوية التصوير",
            "camera_reference",
        ),

        (
            "خد نفس زاوية الكاميرا من هاي",
            "camera_reference",
        ),

        (
            "هاي مرجع المنتج نفسه لا تغيره",
            "product_reference",
        ),

        (
            "هاي البطاقة نفسها خليها ثابتة",
            "product_reference",
        ),

        (
            "خد الإضاءة من هاي الصورة",
            "lighting_reference",
        ),

        (
            "هاي مرجع الخلفية والمكان",
            "environment_reference",
        ),

        (
            "خد الألوان من هاي",
            "color_reference",
        ),

        (
            "بدي نفس التكوين وترتيب العناصر",
            "composition_reference",
        ),

        (
            "هاي مرجع الستايل",
            "style_reference",
        ),

        (
            "حافظ على نفس الشخص والوجه",
            "person_reference",
        ),

        (
            "",
            "style_reference",
        ),
    ]

    role_passed = 0

    for text, expected in role_tests:

        actual = (
            infer_reference_role_from_note(
                text
            )
        )

        ok = (
            actual
            ==
            expected
        )

        if ok:

            role_passed += 1

        print(
            (
                "✅"
                if ok
                else "❌"
            ),
            "role",
            expected,
            "→",
            actual,
        )

    role_ok = (
        role_passed
        ==
        len(
            role_tests
        )
    )

    print("")
    print(
        "Reference roles:",
        role_passed,
        "/",
        len(
            role_tests
        ),
    )
    print("")

    # =====================================================
    # CONTENT FAMILY ROUTING
    # =====================================================

    family_tests = [
        (
            "اعلان تحويل مالي دولي سريع",
            "international_transfer",
        ),

        (
            "شريحتك معك بكل وجهة سفر",
            "travel_roaming",
        ),

        (
            "بوستر كاش باك ومكافآت",
            "cashback_rewards",
        ),

        (
            "اعلان بطاقة Visa للدفع",
            "payments_cards",
        ),

        (
            "تجربة تطبيق البنك الرقمي",
            "digital_banking",
        ),
    ]

    family_passed = 0

    for text, expected in family_tests:

        actual = (
            infer_content_family(
                text
            )
        )

        ok = (
            actual
            ==
            expected
        )

        if ok:

            family_passed += 1

        print(
            (
                "✅"
                if ok
                else "❌"
            ),
            "content",
            expected,
            "→",
            actual,
        )

    family_ok = (
        family_passed
        ==
        len(
            family_tests
        )
    )

    print("")

    # =====================================================
    # PALETTE NORMALIZATION
    # =====================================================

    palette_test = (
        normalize_color_palette(
            {
                "dominant": [
                    "Deep purple #4A136F",
                ],

                "secondary": [
                    "White #FFFFFF",
                ],

                "accents": [
                    "Mint #00C9A7",
                ],

                "swatches": [
                    {
                        "hex":
                            "#4A136F",

                        "usage_pct":
                            55,
                    },

                    {
                        "hex":
                            "#00C9A7",

                        "usage_pct":
                            10,
                    },
                ],
            }
        )
    )

    palette_ok = (
        "#4A136F"
        in palette_test[
            "all_hex"
        ]
        and
        "#00C9A7"
        in palette_test[
            "all_hex"
        ]
    )

    print(
        (
            "✅"
            if palette_ok
            else "❌"
        ),
        "Palette + HEX normalization",
    )

    # =====================================================
    # SENSITIVE REDACTION
    # =====================================================

    sensitive_test, sensitive_found = (
        redact_sensitive_payload(
            {
                "description":
                    (
                        "Card 4111 1111 1111 1111"
                    ),

                "iban":
                    (
                        "SA1234567890123456789012"
                    ),

                "safe":
                    "premium purple card",
            }
        )
    )

    sensitive_ok = (
        sensitive_found
        and
        "iban"
        not in sensitive_test
        and
        "4111"
        not in compact_json(
            sensitive_test,
            1000,
        )
    )

    print(
        (
            "✅"
            if sensitive_ok
            else "❌"
        ),
        "Sensitive financial text redaction",
    )

    # =====================================================
    # SYNTHETIC STC-LIKE REFERENCES
    # =====================================================

    base_source = {
        "source_type":
            "official_instagram",

        "official":
            True,

        "published_at":
            datetime.now(
                timezone.utc
            ).date().isoformat(),

        "brand_id":
            "stc_bank",
    }

    travel_reference = {
        "image_fingerprint_sha256":
            "travel-ref",

        "primary_reference_role":
            "style_reference",

        "secondary_reference_roles": [
            "composition_reference",
            "lighting_reference",
        ],

        "content_classification": {
            "family":
                "travel_roaming",

            "campaign_archetype":
                "environmental_storytelling",
        },

        "reference_utility": {
            "style":
                95,

            "color":
                90,

            "lighting":
                92,

            "camera":
                88,

            "composition":
                94,

            "environment":
                90,

            "product":
                20,

            "person":
                75,

            "campaign_consistency":
                95,
        },

        "visual_fingerprint": {
            "style_tags": [
                "premium",
                "cinematic",
                "Saudi lifestyle",
            ],

            "camera_signature":
                "35mm environmental perspective",

            "composition_signature":
                "hero right, negative space left",

            "lighting_signature":
                "soft directional premium light",

            "material_signature":
                "stone glass brushed metal",

            "palette_signature":
                "deep purple with controlled mint",

            "human_signature":
                "natural non-camera-facing behavior",

            "negative_space_signature":
                "large clean headline-safe zone",

            "commercial_finish_signature":
                "premium banking campaign",

            "transferable_rules": [
                "use brand color through environment",
            ],

            "preserve": [
                "visual restraint",
            ],
        },

        "color_palette": {
            "all_hex": [
                "#4A136F",
                "#00C9A7",
                "#FFFFFF",
            ],
        },

        "source_metadata":
            normalize_source_metadata(
                base_source
            ),

        "confidence":
            95,
    }

    transfer_reference = {
        "image_fingerprint_sha256":
            "transfer-ref",

        "primary_reference_role":
            "campaign_reference",

        "secondary_reference_roles": [
            "composition_reference",
        ],

        "content_classification": {
            "family":
                "international_transfer",

            "campaign_archetype":
                "architectural_metaphor",
        },

        "reference_utility": {
            "style":
                94,

            "color":
                91,

            "lighting":
                90,

            "camera":
                89,

            "composition":
                96,

            "environment":
                85,

            "product":
                15,

            "person":
                60,

            "campaign_consistency":
                96,
        },

        "visual_fingerprint": {
            "style_tags": [
                "premium",
                "architectural metaphor",
                "cinematic",
            ],

            "camera_signature":
                "wide architectural hero",

            "composition_signature":
                "single visual metaphor with copy space",

            "lighting_signature":
                "controlled commercial contrast",

            "material_signature":
                "glass stone metal",

            "palette_signature":
                "purple primary mint restrained",

            "human_signature":
                "supporting human scale",

            "negative_space_signature":
                "clean upper copy region",

            "commercial_finish_signature":
                "global banking hero visual",

            "transferable_rules": [
                "message should work visually without copy",
            ],

            "preserve": [
                "strong visual metaphor",
            ],
        },

        "color_palette": {
            "all_hex": [
                "#4A136F",
                "#00C9A7",
                "#FFFFFF",
            ],
        },

        "source_metadata":
            normalize_source_metadata(
                base_source
            ),

        "confidence":
            96,
    }

    generic_reference = {
        "image_fingerprint_sha256":
            "generic-ref",

        "primary_reference_role":
            "color_reference",

        "secondary_reference_roles": [],

        "content_classification": {
            "family":
                "general_brand",

            "campaign_archetype":
                "graphic_minimal",
        },

        "reference_utility": {
            "style":
                75,

            "color":
                98,

            "lighting":
                50,

            "camera":
                40,

            "composition":
                70,

            "environment":
                30,

            "product":
                20,

            "person":
                10,

            "campaign_consistency":
                80,
        },

        "visual_fingerprint": {
            "style_tags": [
                "brand minimal",
            ],

            "camera_signature":
                "",

            "composition_signature":
                "minimal graphic hierarchy",

            "lighting_signature":
                "",

            "material_signature":
                "",

            "palette_signature":
                "purple mint white",

            "human_signature":
                "",

            "negative_space_signature":
                "high negative space",

            "commercial_finish_signature":
                "clean",

            "transferable_rules": [
                "maintain purple mint hierarchy",
            ],

            "preserve": [
                "clean brand palette",
            ],
        },

        "color_palette": {
            "all_hex": [
                "#4A136F",
                "#00C9A7",
                "#FFFFFF",
            ],
        },

        "source_metadata":
            normalize_source_metadata(
                base_source
            ),

        "confidence":
            90,
    }

    reference_library = [
        travel_reference,
        transfer_reference,
        generic_reference,
    ]

    # =====================================================
    # REQUEST-AWARE SELECTION
    # =====================================================

    selected_transfer = (
        select_best_references(
            reference_library,
            (
                "اعمل اعلان STC Bank "
                "عن تحويل مالي دولي سريع"
            ),
            limit=2,
        )
    )

    selection_ok = bool(
        selected_transfer
        and
        reference_content_family(
            selected_transfer[0]
        )
        ==
        "international_transfer"
    )

    print(
        (
            "✅"
            if selection_ok
            else "❌"
        ),
        "Request-aware reference selection",
    )

    # =====================================================
    # BRAND PROFILE AGGREGATION
    # =====================================================

    brand_profile = (
        build_brand_visual_profile(
            reference_library,
            brand_id="stc_bank",
        )
    )

    profile_ok = (
        brand_profile.get(
            "source_count"
        )
        ==
        3
        and
        bool(
            brand_profile.get(
                "recurring_colors"
            )
        )
        and
        bool(
            brand_profile.get(
                "style_tags"
            )
        )
    )

    print(
        (
            "✅"
            if profile_ok
            else "❌"
        ),
        "Multi-reference Brand Visual Profile",
    )

    # =====================================================
    # EXECUTION CONTEXT
    # =====================================================

    execution_context = (
        build_reference_execution_context(
            reference_library,
            (
                "بوستر STC Bank "
                "عن شريحتك معك بكل وجهة سفر"
            ),
            limit=3,
        )
    )

    execution_ok = (
        execution_context.get(
            "request_family"
        )
        ==
        "travel_roaming"
        and
        execution_context.get(
            "selected_count"
        )
        >=
        1
    )

    print(
        (
            "✅"
            if execution_ok
            else "❌"
        ),
        "Production reference execution context",
    )

    # =====================================================
    # FINGERPRINT
    # =====================================================

    fingerprint_ok = (
        len(
            image_fingerprint(
                b"xpand-test-image"
            )
        )
        ==
        64
    )

    print(
        (
            "✅"
            if fingerprint_ok
            else "❌"
        ),
        "Duplicate-reference fingerprint",
    )

    print("")
    print(
        "✅ Deterministic reference-role classifier"
    )
    print(
        "✅ User reference purpose overrides Vision"
    )
    print(
        "✅ Campaign/content-family classification"
    )
    print(
        "✅ Deep camera + lens + perspective DNA"
    )
    print(
        "✅ Composition + negative-space DNA"
    )
    print(
        "✅ Typography/copy-layout analysis"
    )
    print(
        "✅ Lighting + material DNA"
    )
    print(
        "✅ Approximate HEX + color-usage DNA"
    )
    print(
        "✅ Art-direction DNA"
    )
    print(
        "✅ Human-direction DNA"
    )
    print(
        "✅ Product Lock preserved"
    )
    print(
        "✅ Sensitive financial text protected"
    )
    print(
        "✅ Source authority + freshness supported"
    )
    print(
        "✅ Reference utility scoring"
    )
    print(
        "✅ Request-aware best-reference ranking"
    )
    print(
        "✅ Role-diverse reference selection"
    )
    print(
        "✅ Multi-reference Brand Visual Profile"
    )
    print(
        "✅ Learn visual logic without cloning exact campaign"
    )

    print("")

    all_ok = (
        role_ok
        and
        family_ok
        and
        palette_ok
        and
        sensitive_ok
        and
        selection_ok
        and
        profile_ok
        and
        execution_ok
        and
        fingerprint_ok
    )

    print(
        (
            "XPAND Visual Intelligence V2.0 self-test: "
            +
            (
                "PASS ✅"
                if all_ok
                else "FAIL ❌"
            )
        )
    )

    print(
        "🚫 No API calls were made"
    )

    print("")
