# =========================================================
# XPAND STC POLICY V1.0
#
# CANONICAL STC BENEFIT FAMILY + SERVICE CONSTITUTION
#
# =========================================================
#
# PURPOSE
# ---------------------------------------------------------
#
# One permanent source of truth for:
#
# - STC benefit-family detection
# - Creative Brain service meaning
# - Production service meaning
# - Final render locks
# - QA / runtime consistency
#
#
# CRITICAL RULE
# ---------------------------------------------------------
#
# A generic downstream value such as:
#
#     premium
#
# MUST NOT override a stronger semantic signal from the
# original user message such as:
#
#     international transfer
#     track transfer
#     حول العالم
#     تتبع الحوالة
#     e-commerce
#     POS
#
#
# CANONICAL FAMILIES
# ---------------------------------------------------------
#
# merchant_payments
# digital_banking
# premium
#
#
# ZERO-COST SELF TEST
# ---------------------------------------------------------
#
# python xpand_stc_policy.py
#
# No API calls.
#
# =========================================================

from __future__ import annotations

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


# =========================================================
# IDENTITY
# =========================================================

MODULE_NAME = "XPAND STC Policy"
VERSION = "1.0"


# =========================================================
# CANONICAL FAMILY IDS
# =========================================================

FAMILY_MERCHANT_PAYMENTS = (
    "merchant_payments"
)

FAMILY_DIGITAL_BANKING = (
    "digital_banking"
)

FAMILY_PREMIUM = (
    "premium"
)


CANONICAL_FAMILIES = {
    FAMILY_MERCHANT_PAYMENTS,
    FAMILY_DIGITAL_BANKING,
    FAMILY_PREMIUM,
}


# =========================================================
# DATA MODEL
# =========================================================

@dataclass(frozen=True)
class STCBenefitPolicy:

    family_id: str

    aliases: Tuple[str, ...] = field(
        default_factory=tuple
    )

    creative_constitution: Tuple[
        str,
        ...
    ] = field(
        default_factory=tuple
    )

    final_render_locks: Tuple[
        str,
        ...
    ] = field(
        default_factory=tuple
    )


# =========================================================
# TEXT NORMALIZATION
# =========================================================

def clean_text(
    value: Any,
    limit: int = 50000,
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
        r"[^\w\u0600-\u06FF]+",
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
            return True

    return False


# =========================================================
# SERVICE MARKERS
# =========================================================

MERCHANT_STRONG_MARKERS = (
    "خدمات التجارة الالكترونية ونقاط البيع",
    "التجارة الالكترونية ونقاط البيع",
    "التجاره الالكترونيه ونقاط البيع",
    "نقاط البيع والتجارة الالكترونية",
    "نقاط البيع والتجاره الالكترونيه",
    "ecommerce and pos",
    "e commerce and pos",
    "e-commerce and pos",
    "merchant payments",
    "merchant payment",
    "point of sale",
    "point-of-sale",
    "payment gateway",
)


MERCHANT_MARKERS = (
    "نقاط البيع",
    "نقطه البيع",
    "جهاز نقاط البيع",
    "جهاز الدفع",
    "التجارة الالكترونية",
    "التجاره الالكترونيه",
    "متجر الكتروني",
    "متجر إلكتروني",
    "التجارة عبر الانترنت",
    "التجاره عبر الانترنت",
    "ecommerce",
    "e commerce",
    "e-commerce",
    "pos",
    "merchant",
    "card reader",
    "online payments",
    "store payments",
)


DIGITAL_BANKING_STRONG_MARKERS = (
    "حوالتك حول العالم",
    "حواله حول العالم",
    "تحويلات حول العالم",
    "حول العالم من التطبيق",
    "تتبع الحوالة",
    "تتبع الحواله",
    "تتبع تحويلك",
    "تتبع التحويل",
    "حوالات دولية",
    "حوالات دوليه",
    "تحويل دولي",
    "تحويلات دولية",
    "تحويلات دوليه",
    "international transfer",
    "international transfers",
    "international money transfer",
    "global transfer",
    "global transfers",
    "track transfer",
    "transfer tracking",
    "remittance",
    "remittances",
)


DIGITAL_BANKING_MARKERS = (
    "حوالة",
    "حواله",
    "حوالات",
    "تحويل مالي",
    "تحويل الأموال",
    "تحويل الاموال",
    "تحويل",
    "حول العالم",
    "العالم",
    "تطبيق البنك",
    "من التطبيق",
    "عبر التطبيق",
    "التطبيق",
    "digital banking",
    "mobile banking",
    "banking app",
    "bank app",
    "app banking",
    "transfer",
    "global",
    "worldwide",
)


PREMIUM_MARKERS = (
    "premium",
    "فاخر",
    "فاخرة",
    "فخم",
    "فخامة",
    "فخامه",
    "premium banking",
)


# =========================================================
# POLICIES
# =========================================================

STC_BENEFIT_POLICIES: Dict[
    str,
    STCBenefitPolicy,
] = {

    FAMILY_MERCHANT_PAYMENTS:
        STCBenefitPolicy(

            family_id=(
                FAMILY_MERCHANT_PAYMENTS
            ),

            aliases=(
                MERCHANT_STRONG_MARKERS
                +
                MERCHANT_MARKERS
            ),

            creative_constitution=(

                (
                    "The advertising proposition is that "
                    "STC Bank gives merchants one connected "
                    "commercial payment ecosystem."
                ),

                (
                    "Online / e-commerce acceptance and "
                    "physical point-of-sale acceptance must "
                    "both be visually understood."
                ),

                (
                    "The relationship between the two channels "
                    "must be the advertising idea, not merely "
                    "a collection of banking objects."
                ),

                (
                    "The commercial message must work without "
                    "generated text, slogans or readable UI."
                ),

                (
                    "Do not default to customer + merchant + "
                    "counter + POS + parcel as the entire idea."
                ),

                (
                    "Do not use a phone screen as the only "
                    "evidence of e-commerce."
                ),

                (
                    "Do not invent futuristic payment hardware "
                    "to connect e-commerce and POS."
                ),

                (
                    "The scene must feel like a premium real "
                    "Saudi bank campaign rather than generic "
                    "fintech or ordinary checkout photography."
                ),

                (
                    "Use one memorable, physically believable "
                    "visual mechanism."
                ),

                (
                    "Camera strategy must strengthen the "
                    "commercial proposition."
                ),
            ),

            final_render_locks=(

                (
                    "Preserve the message that e-commerce and "
                    "physical POS belong to one connected "
                    "merchant ecosystem."
                ),

                (
                    "Both commercial channels must remain "
                    "visually understandable without text."
                ),

                (
                    "Do not create invented payment hardware."
                ),

                (
                    "Do not create phone/POS fusion."
                ),

                (
                    "Any visible POS terminal must look like a "
                    "believable real commercially plausible "
                    "payment terminal."
                ),

                (
                    "Do not use a random stone, travertine, "
                    "marble or luxury pedestal as a shortcut "
                    "for premium quality."
                ),

                (
                    "Do not turn the approved idea into a "
                    "generic checkout scene."
                ),

                (
                    "No generated text, logo, fake UI or "
                    "card-brand symbol."
                ),
            ),
        ),


    FAMILY_DIGITAL_BANKING:
        STCBenefitPolicy(

            family_id=(
                FAMILY_DIGITAL_BANKING
            ),

            aliases=(
                DIGITAL_BANKING_STRONG_MARKERS
                +
                DIGITAL_BANKING_MARKERS
            ),

            creative_constitution=(

                (
                    "The advertising proposition is premium "
                    "digital banking control with confident "
                    "global reach."
                ),

                (
                    "For international transfers, the viewer "
                    "must understand global money movement and "
                    "easy transfer tracking from the app."
                ),

                (
                    "The idea must visually communicate "
                    "world-connected banking without depending "
                    "on generated text."
                ),

                (
                    "Do not reduce the advertisement to a "
                    "generic person simply holding a phone."
                ),

                (
                    "Do not use a floating globe as an easy "
                    "visual cliché."
                ),

                (
                    "Do not use generic world maps, glowing "
                    "route lines, fintech network lines, "
                    "particles or holographic UI as the main "
                    "advertising mechanism."
                ),

                (
                    "Global reach should be expressed through "
                    "one elegant physical or photographic "
                    "relationship."
                ),

                (
                    "Tracking and control should feel simple "
                    "and confident, not technically cluttered."
                ),

                (
                    "The campaign must remain grounded in a "
                    "real premium photographic world."
                ),

                (
                    "Camera, environment and human behavior "
                    "must carry the campaign idea rather than "
                    "generic app-poster graphics."
                ),

                (
                    "The visual result must feel appropriate "
                    "for a contemporary Saudi bank campaign."
                ),
            ),

            final_render_locks=(

                (
                    "Preserve the core message of global "
                    "transfer reach plus simple digital "
                    "tracking and control."
                ),

                (
                    "Do not reduce the final image to a basic "
                    "hand-with-phone advertisement."
                ),

                (
                    "Do not introduce a giant floating globe "
                    "or generic map graphic as a shortcut."
                ),

                (
                    "Do not add glowing world-route lines, "
                    "network paths, fintech particles or HUD "
                    "graphics."
                ),

                (
                    "If a smartphone appears it must remain a "
                    "physically realistic smartphone."
                ),

                (
                    "Do not generate readable fake banking UI."
                ),

                (
                    "No generated text, logo, fake balances, "
                    "numbers or interface labels."
                ),

                (
                    "Preserve the successful visual mechanism "
                    "from the approved concept and previs."
                ),

                (
                    "The final scene must remain premium, "
                    "photographic, human and bank-grade."
                ),
            ),
        ),


    FAMILY_PREMIUM:
        STCBenefitPolicy(

            family_id=(
                FAMILY_PREMIUM
            ),

            aliases=(
                PREMIUM_MARKERS
            ),

            creative_constitution=(

                (
                    "Create a premium, contemporary and "
                    "campaign-grade STC Bank visual."
                ),

                (
                    "The benefit must be visually understandable "
                    "without relying on generated text."
                ),

                (
                    "Avoid generic banking stock photography."
                ),

                (
                    "Avoid purple as a substitute for actual "
                    "brand thinking."
                ),

                (
                    "Use intentional camera, realistic materials "
                    "and disciplined composition."
                ),
            ),

            final_render_locks=(

                (
                    "Preserve premium photographic realism."
                ),

                (
                    "Do not replace the approved concept with "
                    "a generic banking scene."
                ),

                (
                    "No generated text, logo or fake banking UI."
                ),
            ),
        ),
}


# =========================================================
# SIGNAL STRENGTH
# =========================================================

def detect_semantic_signal(
    user_text: Any,
) -> Tuple[
    str,
    int,
    str,
]:

    """
    Returns:
        family_id
        confidence 0..100
        reason
    """

    text = normalize_text(
        user_text
    )

    if not text:

        return (
            FAMILY_PREMIUM,
            10,
            "empty_request_fallback",
        )

    #
    # Merchant: strongest compound intent first.
    #

    if contains_any(
        text,
        MERCHANT_STRONG_MARKERS,
    ):

        return (
            FAMILY_MERCHANT_PAYMENTS,
            100,
            "merchant_strong_semantic_match",
        )

    #
    # Global transfer / tracking.
    #

    if contains_any(
        text,
        DIGITAL_BANKING_STRONG_MARKERS,
    ):

        return (
            FAMILY_DIGITAL_BANKING,
            100,
            "digital_banking_strong_semantic_match",
        )

    #
    # POS / ecommerce individual markers.
    #

    merchant_hits = sum(
        1
        for marker
        in MERCHANT_MARKERS
        if normalize_text(
            marker
        )
        in text
    )

    digital_hits = sum(
        1
        for marker
        in DIGITAL_BANKING_MARKERS
        if normalize_text(
            marker
        )
        in text
    )

    if merchant_hits >= 2:

        return (
            FAMILY_MERCHANT_PAYMENTS,
            95,
            "merchant_multiple_semantic_markers",
        )

    if digital_hits >= 2:

        return (
            FAMILY_DIGITAL_BANKING,
            95,
            "digital_multiple_semantic_markers",
        )

    if merchant_hits == 1:

        return (
            FAMILY_MERCHANT_PAYMENTS,
            88,
            "merchant_semantic_marker",
        )

    if digital_hits == 1:

        return (
            FAMILY_DIGITAL_BANKING,
            82,
            "digital_semantic_marker",
        )

    if contains_any(
        text,
        PREMIUM_MARKERS,
    ):

        return (
            FAMILY_PREMIUM,
            60,
            "premium_semantic_marker",
        )

    return (
        FAMILY_PREMIUM,
        20,
        "generic_stc_fallback",
    )


# =========================================================
# EXPLICIT FAMILY NORMALIZATION
# =========================================================

EXPLICIT_ALIASES = {

    "merchant":
        FAMILY_MERCHANT_PAYMENTS,

    "merchant_payment":
        FAMILY_MERCHANT_PAYMENTS,

    "merchant_payments":
        FAMILY_MERCHANT_PAYMENTS,

    "pos":
        FAMILY_MERCHANT_PAYMENTS,

    "ecommerce":
        FAMILY_MERCHANT_PAYMENTS,

    "e_commerce":
        FAMILY_MERCHANT_PAYMENTS,

    "digital":
        FAMILY_DIGITAL_BANKING,

    "digital_banking":
        FAMILY_DIGITAL_BANKING,

    "international_transfer":
        FAMILY_DIGITAL_BANKING,

    "international_transfers":
        FAMILY_DIGITAL_BANKING,

    "transfer":
        FAMILY_DIGITAL_BANKING,

    "transfers":
        FAMILY_DIGITAL_BANKING,

    "remittance":
        FAMILY_DIGITAL_BANKING,

    "global_transfer":
        FAMILY_DIGITAL_BANKING,

    "premium":
        FAMILY_PREMIUM,

    "general_banking":
        FAMILY_PREMIUM,

    "general":
        FAMILY_PREMIUM,
}


def normalize_explicit_family(
    value: Any,
) -> str:

    text = normalize_text(
        value
    ).replace(
        " ",
        "_",
    )

    if not text:

        return ""

    return EXPLICIT_ALIASES.get(
        text,
        (
            text
            if text
            in CANONICAL_FAMILIES
            else
            ""
        ),
    )


# =========================================================
# CANONICAL RESOLVER
# =========================================================

def resolve_stc_benefit_family(
    user_text: Any,
    explicit_benefit_family: Optional[
        str
    ] = None,
) -> STCBenefitPolicy:

    """
    Permanent single source of truth.

    Resolution law:

    1. Read original user semantics FIRST.
    2. A strong semantic service signal wins.
    3. An explicit specific service family may be respected.
    4. Generic 'premium' can NEVER erase:
       merchant_payments or digital_banking.
    5. Premium is only fallback when no stronger service
       signal exists.
    """

    (
        semantic_family,
        semantic_confidence,
        semantic_reason,
    ) = detect_semantic_signal(
        user_text
    )

    explicit_family = (
        normalize_explicit_family(
            explicit_benefit_family
        )
    )

    #
    # Strong request semantics always win.
    #

    if (
        semantic_family
        in {
            FAMILY_MERCHANT_PAYMENTS,
            FAMILY_DIGITAL_BANKING,
        }
        and
        semantic_confidence
        >=
        80
    ):

        return STC_BENEFIT_POLICIES[
            semantic_family
        ]

    #
    # A specific explicit service family may win when
    # original semantics are weak.
    #

    if explicit_family in {
        FAMILY_MERCHANT_PAYMENTS,
        FAMILY_DIGITAL_BANKING,
    }:

        return STC_BENEFIT_POLICIES[
            explicit_family
        ]

    #
    # Premium may be explicit only if no specific service
    # was detected.
    #

    if (
        explicit_family
        ==
        FAMILY_PREMIUM
        and
        semantic_family
        ==
        FAMILY_PREMIUM
    ):

        return STC_BENEFIT_POLICIES[
            FAMILY_PREMIUM
        ]

    return STC_BENEFIT_POLICIES[
        semantic_family
    ]


def resolve_stc_benefit_family_id(
    user_text: Any,
    explicit_benefit_family: Optional[
        str
    ] = None,
) -> str:

    return (
        resolve_stc_benefit_family(
            user_text,
            explicit_benefit_family,
        )
        .family_id
    )


# =========================================================
# CREATIVE CONSTITUTION
# =========================================================

def build_creative_constitution_text(
    user_text: Any,
    explicit_benefit_family: Optional[
        str
    ] = None,
    selected_stc_style: str = "",
) -> str:

    policy = (
        resolve_stc_benefit_family(
            user_text,
            explicit_benefit_family,
        )
    )

    style = (
        clean_text(
            selected_stc_style,
            200,
        )
        or
        "premium_realistic"
    )

    lines = [
        (
            "CANONICAL STC BENEFIT FAMILY: "
            +
            policy.family_id
        ),
        (
            "SELECTED STC VISUAL FAMILY: "
            +
            style
        ),
        "",
        "STC SERVICE CREATIVE CONSTITUTION:",
    ]

    for item in (
        policy.creative_constitution
    ):

        lines.append(
            "- "
            +
            item
        )

    lines.extend(
        [
            "",
            "GLOBAL STC CREATIVE LOCKS:",
            (
                "- STC references are visual DNA authority, "
                "not optional decoration."
            ),
            (
                "- Premium does not mean automatically "
                "painting the image purple."
            ),
            (
                "- Do not generate readable campaign copy, "
                "slogan or logo inside the image."
            ),
            (
                "- Do not solve a service brief with generic "
                "fintech decoration."
            ),
            (
                "- The winning visual mechanism must remain "
                "physically believable and photographable."
            ),
            (
                "- Camera choice must contribute to the "
                "advertising idea."
            ),
        ]
    )

    return "\n".join(
        lines
    ).strip()


# =========================================================
# FINAL RENDER LOCKS
# =========================================================

def build_final_render_locks_text(
    user_text: Any,
    explicit_benefit_family: Optional[
        str
    ] = None,
    selected_stc_style: str = "",
) -> str:

    policy = (
        resolve_stc_benefit_family(
            user_text,
            explicit_benefit_family,
        )
    )

    style = (
        clean_text(
            selected_stc_style,
            200,
        )
        or
        "premium_realistic"
    )

    lines = [
        (
            "FINAL CANONICAL BENEFIT FAMILY: "
            +
            policy.family_id
        ),
        (
            "FINAL STC VISUAL FAMILY: "
            +
            style
        ),
        "",
        "SERVICE-SPECIFIC FINAL LOCKS:",
    ]

    for item in (
        policy.final_render_locks
    ):

        lines.append(
            "- "
            +
            item
        )

    lines.extend(
        [
            "",
            "GLOBAL FINAL RENDER LOCKS:",
            (
                "- Preserve the successful advertising "
                "mechanism and composition skeleton from the "
                "approved concept/previsualization when they "
                "already communicate the message clearly."
            ),
            (
                "- Improve realism, materials, anatomy, "
                "lighting and finish without replacing the "
                "idea with a weaker generic scene."
            ),
            (
                "- STC reference images have authority over "
                "brand-world taste, tonal behavior, materials, "
                "lighting maturity and photographic finish."
            ),
            (
                "- Do not drift into arbitrary generic luxury "
                "styling that conflicts with the references."
            ),
            (
                "- Use approximately 15–22% integrated calm "
                "copy space when useful."
            ),
            (
                "- Do not create a giant blank upper third."
            ),
            (
                "- Do not push the main subject into the "
                "bottom half simply to manufacture copy space."
            ),
            (
                "- Camera must feel campaign-grade and "
                "intentional, not default catalog framing."
            ),
            (
                "- Every visible object must be physically "
                "possible and photographically coherent."
            ),
            (
                "- No readable generated text."
            ),
            (
                "- No generated STC logo."
            ),
            (
                "- No fake banking UI."
            ),
            (
                "- No fake financial numbers."
            ),
            (
                "- No watermark."
            ),
        ]
    )

    return "\n".join(
        lines
    ).strip()


# =========================================================
# DIAGNOSTICS
# =========================================================

def explain_resolution(
    user_text: Any,
    explicit_benefit_family: Optional[
        str
    ] = None,
) -> Dict[str, Any]:

    (
        semantic_family,
        semantic_confidence,
        semantic_reason,
    ) = detect_semantic_signal(
        user_text
    )

    explicit = (
        normalize_explicit_family(
            explicit_benefit_family
        )
    )

    resolved = (
        resolve_stc_benefit_family(
            user_text,
            explicit_benefit_family,
        )
    )

    return {
        "semantic_family":
            semantic_family,

        "semantic_confidence":
            semantic_confidence,

        "semantic_reason":
            semantic_reason,

        "explicit_family":
            explicit,

        "resolved_family":
            resolved.family_id,
    }


def get_stc_policy_status() -> Dict[
    str,
    Any,
]:

    return {
        "module":
            MODULE_NAME,

        "version":
            VERSION,

        "canonical_families":
            sorted(
                CANONICAL_FAMILIES
            ),

        "semantic_first":
            True,

        "generic_premium_cannot_override_specific_service":
            True,

        "merchant_policy":
            True,

        "digital_banking_policy":
            True,

        "creative_constitution":
            True,

        "final_render_locks":
            True,
    }


# =========================================================
# ZERO-COST SELF TEST
# =========================================================

if __name__ == "__main__":

    tests: Dict[
        str,
        bool,
    ] = {}

    # -----------------------------------------------------
    # Merchant
    # -----------------------------------------------------

    tests[
        "merchant_arabic"
    ] = (
        resolve_stc_benefit_family_id(
            (
                "أنشئ إعلان STC Bank عن خدمات "
                "التجارة الإلكترونية ونقاط البيع"
            )
        )
        ==
        FAMILY_MERCHANT_PAYMENTS
    )

    tests[
        "merchant_english"
    ] = (
        resolve_stc_benefit_family_id(
            (
                "STC Bank ecommerce and POS "
                "merchant payments campaign"
            )
        )
        ==
        FAMILY_MERCHANT_PAYMENTS
    )

    # -----------------------------------------------------
    # Digital banking / transfer
    # -----------------------------------------------------

    tests[
        "global_transfer_arabic"
    ] = (
        resolve_stc_benefit_family_id(
            (
                "STC Bank حوالتك حول العالم "
                "وتقدر تتبعها من التطبيق"
            )
        )
        ==
        FAMILY_DIGITAL_BANKING
    )

    tests[
        "international_transfer_arabic"
    ] = (
        resolve_stc_benefit_family_id(
            (
                "حوالات دولية وتتبع التحويل "
                "من تطبيق STC Bank"
            )
        )
        ==
        FAMILY_DIGITAL_BANKING
    )

    tests[
        "global_transfer_english"
    ] = (
        resolve_stc_benefit_family_id(
            (
                "STC Bank international transfer "
                "with transfer tracking in the app"
            )
        )
        ==
        FAMILY_DIGITAL_BANKING
    )

    # -----------------------------------------------------
    # Regression:
    # old runtime says premium,
    # original request says global transfer.
    # Semantics MUST win.
    # -----------------------------------------------------

    tests[
        "premium_cannot_override_global_transfer"
    ] = (
        resolve_stc_benefit_family_id(
            (
                "حوالتك حول العالم وتقدر "
                "تتبعها من التطبيق بكل سهولة"
            ),
            "premium",
        )
        ==
        FAMILY_DIGITAL_BANKING
    )

    tests[
        "premium_cannot_override_merchant"
    ] = (
        resolve_stc_benefit_family_id(
            (
                "خدمات التجارة الإلكترونية "
                "ونقاط البيع"
            ),
            "premium",
        )
        ==
        FAMILY_MERCHANT_PAYMENTS
    )

    # -----------------------------------------------------
    # Explicit specific family
    # -----------------------------------------------------

    tests[
        "specific_explicit_family_allowed"
    ] = (
        resolve_stc_benefit_family_id(
            "إعلان STC Bank",
            "digital_banking",
        )
        ==
        FAMILY_DIGITAL_BANKING
    )

    # -----------------------------------------------------
    # Generic fallback
    # -----------------------------------------------------

    tests[
        "generic_request_falls_to_premium"
    ] = (
        resolve_stc_benefit_family_id(
            "أنشئ إعلان فاخر لبنك STC Bank"
        )
        ==
        FAMILY_PREMIUM
    )

    # -----------------------------------------------------
    # Creative constitution
    # -----------------------------------------------------

    digital_creative = (
        build_creative_constitution_text(
            (
                "حوالتك حول العالم وتقدر "
                "تتبعها من التطبيق"
            ),
            "premium",
            "premium_realistic",
        )
    )

    tests[
        "digital_constitution_canonical"
    ] = (
        (
            "CANONICAL STC BENEFIT FAMILY: "
            "digital_banking"
        )
        in digital_creative
    )

    tests[
        "digital_constitution_blocks_phone_cliche"
    ] = (
        (
            "generic person simply holding a phone"
        )
        in digital_creative
    )

    tests[
        "digital_constitution_blocks_globe_cliche"
    ] = (
        "floating globe"
        in digital_creative
    )

    # -----------------------------------------------------
    # Merchant final locks
    # -----------------------------------------------------

    merchant_final = (
        build_final_render_locks_text(
            (
                "خدمات التجارة الإلكترونية "
                "ونقاط البيع"
            ),
            "premium",
            "premium_realistic",
        )
    )

    tests[
        "merchant_final_canonical"
    ] = (
        (
            "FINAL CANONICAL BENEFIT FAMILY: "
            "merchant_payments"
        )
        in merchant_final
    )

    tests[
        "merchant_final_no_phone_pos_fusion"
    ] = (
        "phone/POS fusion"
        in merchant_final
    )

    tests[
        "merchant_final_no_stone"
    ] = (
        "travertine"
        in merchant_final
    )

    # -----------------------------------------------------
    # Global final locks
    # -----------------------------------------------------

    tests[
        "final_copy_space_15_22"
    ] = (
        "15–22%"
        in merchant_final
    )

    tests[
        "final_no_giant_upper_third"
    ] = (
        "giant blank upper third"
        in merchant_final
    )

    tests[
        "final_reference_authority"
    ] = (
        "reference images have authority"
        in merchant_final
    )

    # -----------------------------------------------------
    # Result
    # -----------------------------------------------------

    passed = all(
        tests.values()
    )

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND STC POLICY V1.0"
    )
    print(
        " ZERO-COST CANONICAL BENEFIT SELF TEST"
    )
    print(
        "=========================================="
    )
    print("")

    for name, result in tests.items():

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

    transfer_demo = (
        explain_resolution(
            (
                "حوالتك حول العالم وتقدر "
                "تتبعها من التطبيق"
            ),
            "premium",
        )
    )

    print(
        "Regression demo:"
    )

    print(
        "  semantic =",
        transfer_demo[
            "semantic_family"
        ],
    )

    print(
        "  old explicit =",
        transfer_demo[
            "explicit_family"
        ],
    )

    print(
        "  canonical =",
        transfer_demo[
            "resolved_family"
        ],
    )

    print("")

    if passed:

        print(
            (
                "XPAND STC Policy V1.0 "
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
                "XPAND STC Policy V1.0 "
                "self-test: FAIL ❌"
            )
        )

        print(
            "Failures:",
            failures,
        )

        raise RuntimeError(
            (
                "XPAND STC Policy V1.0 "
                "self-test failed."
            )
        )

    print("")
    print(
        "✅ Semantic service intent is canonical"
    )
    print(
        "✅ premium cannot erase digital_banking"
    )
    print(
        "✅ premium cannot erase merchant_payments"
    )
    print(
        "✅ Global-transfer creative constitution ready"
    )
    print(
        "✅ Merchant-payments constitution ready"
    )
    print(
        "✅ Final-render service locks ready"
    )
    print(
        "🚫 No API calls were made"
    )
    print("")
