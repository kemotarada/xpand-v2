# =========================================================
# XPAND VISUAL STACK INTEGRATION AUDIT V1.0
#
# ZERO API / ZERO DATABASE / ZERO IMAGE TEST
#
# =========================================================
#
# This file does NOT modify XPAND.
#
# It verifies the deployed modules can work together before
# spending money on the first real STC Bank generation.
#
# =========================================================

from __future__ import annotations

import inspect
import sys
import traceback

from typing import (
    Any,
    Dict,
    List,
    Tuple,
)


# =========================================================
# RESULT HELPERS
# =========================================================

RESULTS: List[
    Tuple[
        str,
        bool,
        str,
    ]
] = []


def record(
    name: str,
    passed: bool,
    detail: str = "",
) -> None:

    RESULTS.append(
        (
            name,
            bool(
                passed
            ),
            str(
                detail
                or ""
            ),
        )
    )


def version_tuple(
    value: Any,
) -> Tuple[int, ...]:

    text = str(
        value
        or ""
    ).strip()

    parts = []

    for token in text.split(
        "."
    ):

        digits = ""

        for char in token:

            if char.isdigit():

                digits += char

            else:

                break

        if digits:

            parts.append(
                int(
                    digits
                )
            )

        else:

            parts.append(
                0
            )

    return tuple(
        parts
    )


def version_at_least(
    actual: Any,
    minimum: str,
) -> bool:

    actual_tuple = version_tuple(
        actual
    )

    minimum_tuple = version_tuple(
        minimum
    )

    length = max(
        len(
            actual_tuple
        ),
        len(
            minimum_tuple
        ),
    )

    actual_tuple += (
        0,
    ) * (
        length
        -
        len(
            actual_tuple
        )
    )

    minimum_tuple += (
        0,
    ) * (
        length
        -
        len(
            minimum_tuple
        )
    )

    return (
        actual_tuple
        >=
        minimum_tuple
    )


# =========================================================
# IMPORT MODULES
# =========================================================

IMPORT_ERRORS: Dict[
    str,
    str,
] = {}


def safe_import(
    module_name: str,
):

    try:

        module = __import__(
            module_name
        )

        record(
            (
                "import_"
                +
                module_name
            ),
            True,
        )

        return module

    except Exception as error:

        IMPORT_ERRORS[
            module_name
        ] = (
            str(
                error
            )
        )

        record(
            (
                "import_"
                +
                module_name
            ),
            False,
            str(
                error
            ),
        )

        return None


image_engine = safe_import(
    "xpand_image_engine"
)

creative_brain = safe_import(
    "xpand_creative_brain"
)

stc_skill = safe_import(
    "xpand_stc_bank_skill"
)

brand_research = safe_import(
    "xpand_brand_research"
)

brand_memory = safe_import(
    "xpand_brand_memory"
)

production = safe_import(
    "xpand_production_engine"
)

telegram_runtime = safe_import(
    "xpand_image_telegram"
)


# =========================================================
# VERSION AUDIT
# =========================================================

if image_engine:

    engine_version = getattr(
        image_engine,
        "ENGINE_VERSION",
        getattr(
            image_engine,
            "VERSION",
            "",
        ),
    )

    record(
        "image_engine_version",
        version_at_least(
            engine_version,
            "2.0",
        ),
        (
            "actual="
            +
            str(
                engine_version
            )
        ),
    )


if creative_brain:

    creative_version = getattr(
        creative_brain,
        "VERSION",
        "",
    )

    record(
        "creative_brain_v5",
        version_at_least(
            creative_version,
            "5.0",
        ),
        (
            "actual="
            +
            str(
                creative_version
            )
        ),
    )


if stc_skill:

    skill_version = getattr(
        stc_skill,
        "VERSION",
        "",
    )

    record(
        "stc_skill_v3",
        version_at_least(
            skill_version,
            "3.0",
        ),
        (
            "actual="
            +
            str(
                skill_version
            )
        ),
    )


if brand_research:

    research_version = getattr(
        brand_research,
        "VERSION",
        "",
    )

    record(
        "brand_research_v2",
        version_at_least(
            research_version,
            "2.0",
        ),
        (
            "actual="
            +
            str(
                research_version
            )
        ),
    )


if brand_memory:

    memory_version = getattr(
        brand_memory,
        "VERSION",
        "",
    )

    record(
        "brand_memory_v3",
        version_at_least(
            memory_version,
            "3.0",
        ),
        (
            "actual="
            +
            str(
                memory_version
            )
        ),
    )


if production:

    production_version = getattr(
        production,
        "ENGINE_VERSION",
        getattr(
            production,
            "VERSION",
            "",
        ),
    )

    record(
        "production_v5",
        version_at_least(
            production_version,
            "5.0",
        ),
        (
            "actual="
            +
            str(
                production_version
            )
        ),
    )


if telegram_runtime:

    telegram_version = getattr(
        telegram_runtime,
        "VERSION",
        "",
    )

    record(
        "telegram_v3_4",
        version_at_least(
            telegram_version,
            "3.4",
        ),
        (
            "actual="
            +
            str(
                telegram_version
            )
        ),
    )


# =========================================================
# TELEGRAM INSTALL CONTRACT
# =========================================================

if telegram_runtime:

    record(
        "telegram_install_exists",
        callable(
            getattr(
                telegram_runtime,
                "install",
                None,
            )
        ),
    )

    record(
        "telegram_generate_exists",
        callable(
            getattr(
                telegram_runtime,
                "generate_and_deliver",
                None,
            )
        ),
    )

    record(
        "telegram_style_gate_exists",
        callable(
            getattr(
                telegram_runtime,
                "consume_pending_stc_style_reply",
                None,
            )
        ),
    )


# =========================================================
# STC STYLE GATE
# =========================================================

if stc_skill:

    request_without_style = (
        "أنشئ صورة إعلانية لبنك STC Bank "
        "عن خدمات التجارة الإلكترونية ونقاط البيع"
    )

    request_realistic = (
        request_without_style
        +
        " واقعي فوتوغرافي"
    )

    record(
        "stc_style_question_required",
        bool(
            stc_skill
            .stc_style_question_needed(
                request_without_style
            )
        ),
    )

    record(
        "stc_explicit_style_bypass",
        not bool(
            stc_skill
            .stc_style_question_needed(
                request_realistic
            )
        ),
    )

    record(
        "stc_merchant_semantics",
        (
            stc_skill
            .detect_stc_benefit_family(
                request_without_style
            )
            ==
            "merchant_payments"
        ),
    )


# =========================================================
# RESEARCH COST CONTRACT
# =========================================================

if brand_research:

    profile = getattr(
        brand_research,
        "BRAND_PROFILES",
        {},
    ).get(
        "stc_bank",
        {},
    )

    record(
        "research_stc_default_fast",
        (
            profile.get(
                "default_mode"
            )
            ==
            "google_fast"
        ),
        (
            "actual="
            +
            str(
                profile.get(
                    "default_mode"
                )
            )
        ),
    )

    record(
        "research_max_three_calls",
        (
            int(
                getattr(
                    brand_research,
                    "RESEARCH_MAX_CALLS",
                    999,
                )
            )
            <=
            3
        ),
        (
            "actual="
            +
            str(
                getattr(
                    brand_research,
                    "RESEARCH_MAX_CALLS",
                    "?",
                )
            )
        ),
    )

    record(
        "research_cache_24h_or_more",
        (
            int(
                getattr(
                    brand_research,
                    "RESEARCH_CACHE_TTL_SECONDS",
                    0,
                )
            )
            >=
            86400
        ),
        (
            "actual="
            +
            str(
                getattr(
                    brand_research,
                    "RESEARCH_CACHE_TTL_SECONDS",
                    "?",
                )
            )
        ),
    )


# =========================================================
# BRAND MEMORY COST CONTRACT
# =========================================================

if brand_memory:

    record(
        "memory_reference_curator_exists",
        callable(
            getattr(
                brand_memory,
                "curate_references",
                None,
            )
        ),
    )

    record(
        "memory_stc_max_three_refs",
        (
            int(
                getattr(
                    brand_memory,
                    "STC_REFERENCE_LIMIT",
                    999,
                )
            )
            <=
            3
        ),
        (
            "actual="
            +
            str(
                getattr(
                    brand_memory,
                    "STC_REFERENCE_LIMIT",
                    "?",
                )
            )
        ),
    )

    record(
        "memory_relevant_loader_exists",
        callable(
            getattr(
                brand_memory,
                "load_relevant_visual_references",
                None,
            )
        ),
    )

    record(
        "memory_visual_profile_exists",
        callable(
            getattr(
                brand_memory,
                "get_brand_visual_profile",
                None,
            )
        ),
    )


# =========================================================
# PRODUCTION COST CONTRACT
# =========================================================

if production:

    record(
        "production_max_two_images",
        (
            int(
                getattr(
                    production,
                    "MASTERPIECE_MAX_IMAGE_CALLS",
                    999,
                )
            )
            <=
            2
        ),
        (
            "actual="
            +
            str(
                getattr(
                    production,
                    "MASTERPIECE_MAX_IMAGE_CALLS",
                    "?",
                )
            )
        ),
    )

    record(
        "production_max_two_vision",
        (
            int(
                getattr(
                    production,
                    "MASTERPIECE_MAX_VISION_CALLS",
                    999,
                )
            )
            <=
            2
        ),
        (
            "actual="
            +
            str(
                getattr(
                    production,
                    "MASTERPIECE_MAX_VISION_CALLS",
                    "?",
                )
            )
        ),
    )

    record(
        "production_max_three_dna_refs",
        (
            int(
                getattr(
                    production,
                    "SMART_REFERENCE_SELECTION_LIMIT",
                    999,
                )
            )
            <=
            3
        ),
        (
            "actual="
            +
            str(
                getattr(
                    production,
                    "SMART_REFERENCE_SELECTION_LIMIT",
                    "?",
                )
            )
        ),
    )

    record(
        "production_max_two_physical_refs",
        (
            int(
                getattr(
                    production,
                    "MAX_PHYSICAL_REFERENCE_IMAGES",
                    999,
                )
            )
            <=
            2
        ),
        (
            "actual="
            +
            str(
                getattr(
                    production,
                    "MAX_PHYSICAL_REFERENCE_IMAGES",
                    "?",
                )
            )
        ),
    )

    model = str(
        getattr(
            production,
            "NANO_BANANA_2_MODEL",
            "",
        )
    )

    record(
        "production_nano_banana_2",
        (
            "gemini-3.1-flash-image"
            in
            model
        ),
        (
            "actual="
            +
            model
        ),
    )

    status = (
        production
        .get_production_engine_status()
    )

    record(
        "production_no_mandatory_pro",
        (
            status.get(
                "nano_banana_pro_required"
            )
            is False
        ),
        (
            "actual="
            +
            str(
                status.get(
                    "nano_banana_pro_required"
                )
            )
        ),
    )


# =========================================================
# IMAGE ENGINE ROUTING
# =========================================================

if image_engine:

    fast_model = str(
        getattr(
            image_engine,
            "GOOGLE_IMAGE_FAST_MODEL",
            "",
        )
    )

    record(
        "image_engine_nano_banana_2",
        (
            "gemini-3.1-flash-image"
            in
            fast_model
        ),
        (
            "actual="
            +
            fast_model
        ),
    )

    best_use_pro = bool(
        getattr(
            image_engine,
            "BEST_USE_PRO",
            False,
        )
    )

    record(
        "image_engine_best_not_pro",
        (
            best_use_pro
            is False
        ),
        (
            "actual="
            +
            str(
                best_use_pro
            )
        ),
    )


# =========================================================
# CRITICAL DIRECTOR ROUTING AUDIT
# =========================================================

if image_engine:

    director = getattr(
        image_engine,
        "call_openai_director",
        None,
    )

    if callable(
        director
    ):

        try:

            source = inspect.getsource(
                director
            )

        except Exception:

            source = ""

        normalized_source = (
            source
            .replace(
                " ",
                ""
            )
            .replace(
                "\n",
                ""
            )
            .lower()
        )

        #
        # BAD HISTORICAL PATTERN:
        #
        # if GEMINI_API_KEY:
        #     return call_gemini_director(...)
        #
        # appearing before structured/json routing.
        #

        gemini_guard_position = (
            normalized_source.find(
                "ifgemini_api_key:"
            )
        )

        gemini_return_position = (
            normalized_source.find(
                "returncall_gemini_director("
            )
        )

        structured_position = min(
            [
                position
                for position
                in [
                    normalized_source.find(
                        "structured="
                    ),

                    normalized_source.find(
                        "json_schema"
                    ),

                    normalized_source.find(
                        "json_mode"
                    ),
                ]
                if position
                >=
                0
            ]
            or
            [
                -1
            ]
        )

        unconditional_gemini_first = bool(
            gemini_guard_position
            >=
            0
            and
            gemini_return_position
            >
            gemini_guard_position
            and
            (
                structured_position
                < 0
                or
                gemini_return_position
                <
                structured_position
            )
        )

        record(
            "director_not_unconditional_gemini_first",
            not unconditional_gemini_first,
            (
                "critical: structured Creative Brain "
                "must not be blindly routed to Gemini"
            ),
        )

        #
        # We want evidence that strict schemas have a path
        # to OpenAI structured output.
        #

        has_openai_response_path = bool(
            (
                "_call_openai_response_once"
                in source
            )
            or
            (
                "OPENAI_RESPONSES_URL"
                in source
            )
        )

        record(
            "director_has_strict_openai_path",
            has_openai_response_path,
        )

    else:

        record(
            "director_not_unconditional_gemini_first",
            False,
            "call_openai_director missing",
        )

        record(
            "director_has_strict_openai_path",
            False,
            "call_openai_director missing",
        )


# =========================================================
# CREATIVE BRAIN CONTRACT
# =========================================================

if creative_brain:

    record(
        "creative_run_exists",
        callable(
            getattr(
                creative_brain,
                "run_creative_brain",
                None,
            )
        ),
    )

    source = ""

    try:

        source = inspect.getsource(
            creative_brain
            .run_creative_brain
        )

    except Exception:

        pass

    record(
        "creative_technical_failure_contract",
        (
            (
                "technical_failure"
                in source
            )
            or
            hasattr(
                creative_brain,
                "IdeationParseError",
            )
        ),
    )


# =========================================================
# CROSS-MODULE IMPORT CONTRACT
# =========================================================

if (
    production
    and
    brand_memory
):

    record(
        "production_memory_loader_contract",
        callable(
            getattr(
                brand_memory,
                "load_relevant_visual_references",
                None,
            )
        )
        and
        callable(
            getattr(
                production,
                "load_runtime_references",
                None,
            )
        ),
    )


if (
    telegram_runtime
    and
    production
):

    record(
        "telegram_production_contract",
        callable(
            getattr(
                production,
                "run_production",
                None,
            )
        )
        and
        callable(
            getattr(
                telegram_runtime,
                "generate_masterpiece_images",
                None,
            )
        ),
    )


if (
    telegram_runtime
    and
    creative_brain
):

    record(
        "telegram_creative_contract",
        callable(
            getattr(
                creative_brain,
                "run_creative_brain",
                None,
            )
        )
        and
        callable(
            getattr(
                telegram_runtime,
                "creative_runtime_state",
                None,
            )
        ),
    )


# =========================================================
# NO-TEXT / NO-LOGO CONTRACT
# =========================================================

if stc_skill:

    guard = str(
        getattr(
            stc_skill,
            "STC_BANK_IMAGE_GUARD",
            "",
        )
    ).lower()

    record(
        "stc_guard_no_text",
        (
            "no visible"
            in guard
            or
            "no headline"
            in guard
        ),
    )

    record(
        "stc_guard_no_logo",
        (
            "stc bank logo"
            in guard
            or
            "no logo"
            in guard
        ),
    )

    record(
        "stc_guard_no_neon_default",
        (
            "neon"
            in guard
        ),
    )


# =========================================================
# FINAL REPORT
# =========================================================

print("")
print(
    "=============================================="
)
print(
    " XPAND VISUAL STACK INTEGRATION AUDIT V1.0"
)
print(
    " ZERO-COST / ZERO-API"
)
print(
    "=============================================="
)
print("")


passed_count = 0

failed_count = 0


for name, passed, detail in (
    RESULTS
):

    if passed:

        passed_count += 1

        print(
            "✅",
            name,
            (
                "| "
                +
                detail
                if detail
                else ""
            ),
        )

    else:

        failed_count += 1

        print(
            "❌",
            name,
            (
                "| "
                +
                detail
                if detail
                else ""
            ),
        )


print("")
print(
    "----------------------------------------------"
)
print(
    "Passed:",
    passed_count,
)
print(
    "Failed:",
    failed_count,
)
print(
    "----------------------------------------------"
)
print("")


CRITICAL_TESTS = {
    "import_xpand_image_engine",
    "import_xpand_creative_brain",
    "import_xpand_stc_bank_skill",
    "import_xpand_brand_research",
    "import_xpand_brand_memory",
    "import_xpand_production_engine",
    "import_xpand_image_telegram",
    "creative_brain_v5",
    "stc_skill_v3",
    "brand_research_v2",
    "brand_memory_v3",
    "production_v5",
    "telegram_v3_4",
    "telegram_install_exists",
    "stc_style_question_required",
    "stc_merchant_semantics",
    "production_max_two_images",
    "production_max_two_vision",
    "production_nano_banana_2",
    "production_no_mandatory_pro",
    "image_engine_nano_banana_2",
    "image_engine_best_not_pro",
    "director_not_unconditional_gemini_first",
    "director_has_strict_openai_path",
    "telegram_production_contract",
    "telegram_creative_contract",
}


critical_failures = [
    name
    for name, passed, _
    in RESULTS
    if (
        name
        in
        CRITICAL_TESTS
        and
        not passed
    )
]


if critical_failures:

    print(
        "❌ XPAND VISUAL STACK: NOT READY"
    )

    print("")
    print(
        "Critical failures:"
    )

    for item in critical_failures:

        print(
            " -",
            item,
        )

    print("")
    print(
        "🚫 Do NOT run a paid STC generation yet."
    )

    print(
        "🚫 No API calls were made by this audit."
    )

    sys.exit(
        1
    )


print(
    "✅ XPAND VISUAL STACK: READY FOR CONTROLLED LIVE TEST"
)

print("")
print(
    "Expected STC live path:"
)

print(
    "STC request"
)

print(
    "→ style question"
)

print(
    "→ cached/local brand intelligence"
)

print(
    "→ Creative Brain V5"
)

print(
    "→ max 3 curated DNA refs"
)

print(
    "→ max 2 physical refs"
)

print(
    "→ Nano Banana 2"
)

print(
    "→ 1 Vision QA"
)

print(
    "→ second Nano Banana 2 only if QA finds a real defect"
)

print(
    "→ Telegram delivery"
)

print("")
print(
    "💰 Normal production target:"
)

print(
    "1 image call + 1 Vision QA"
)

print("")
print(
    "💰 Maximum production target:"
)

print(
    "2 image calls + 2 Vision QA"
)

print("")
print(
    "🚫 Nano Banana Pro is not mandatory"
)

print(
    "🚫 No API calls were made by this audit"
)

print(
    "🚫 No Vision calls were made by this audit"
)

print(
    "🚫 No images were generated by this audit"
)

print("")
