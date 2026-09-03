# =========================================================
# EXPLICIT REFERENCE CONTENT FAMILY V3.2.1
# =========================================================
#
# User caption wins over Vision classification when the
# requested family is explicit.
#
# Example:
#
# مرجع STC رسمي | تحويل مالي دولي
# -> international_transfer
#
# The original Vision classification is preserved as
# vision_family for audit/debugging.
# =========================================================

EXPLICIT_REFERENCE_FAMILIES = [
    (
        "international_transfer",
        [
            "تحويل دولي",
            "تحويل مالي دولي",
            "تحويلات مالية دولية",
            "حوالة مالية دولية",
            "حواله ماليه دوليه",
            "حوالة دولية",
            "حواله دوليه",
            "international transfer",
            "international money transfer",
            "cross border transfer",
            "cross-border transfer",
        ],
    ),

    (
        "travel_roaming",
        [
            "سفر",
            "السفر",
            "مسافر",
            "سياحة",
            "مطار",
            "طيران",
            "تجوال",
            "روامينج",
            "روaming",
            "roaming",
            "travel",
            "airport",
        ],
    ),

    (
        "cashback_rewards",
        [
            "كاش باك",
            "كاشباك",
            "استرداد نقدي",
            "cashback",
            "مكافآت",
            "مكافات",
            "rewards",
        ],
    ),

    (
        "payments_cards",
        [
            "بطاقة",
            "بطاقه",
            "بطاقات",
            "بطاقة بنكية",
            "بطاقه بنكيه",
            "card",
            "cards",
            "bank card",
            "payment card",
        ],
    ),

    (
        "security_trust",
        [
            "أمان",
            "امان",
            "حماية",
            "حمايه",
            "أمن",
            "امن",
            "security",
            "secure",
            "protection",
            "trust",
        ],
    ),

    (
        "business_banking",
        [
            "أعمال",
            "اعمال",
            "شركات",
            "منشآت",
            "منشات",
            "business banking",
            "business",
            "corporate",
        ],
    ),

    (
        "digital_banking",
        [
            "بنك رقمي",
            "البنك الرقمي",
            "خدمات رقمية",
            "خدمات رقميه",
            "تطبيق البنك",
            "digital banking",
            "mobile banking",
            "banking app",
        ],
    ),

    (
        "premium_lifestyle",
        [
            "بريميوم",
            "فاخر",
            "فخامة",
            "فخامه",
            "premium",
            "luxury",
            "lifestyle",
        ],
    ),
]


def infer_explicit_reference_family(
    text: str
) -> str:

    value = clean_text(
        text,
        5000
    )

    if not value:

        return ""

    for family, markers in EXPLICIT_REFERENCE_FAMILIES:

        if contains_any(
            value,
            markers
        ):

            return family

    return ""
