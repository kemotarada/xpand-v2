# =========================================================
# XPAND VISUAL STACK INTEGRATION AUDIT V1.1
#
# ZERO API
# ZERO DATABASE
# ZERO IMAGE
#
# =========================================================
#
# V1.1 FIX
# ---------------------------------------------------------
#
# V1.0 checked only the literal source text of:
#
#     call_openai_director()
#
# for:
#
#     _call_openai_response_once
#     OPENAI_RESPONSES_URL
#
# That can produce a FALSE NEGATIVE when the director routes
# through another internal helper.
#
# V1.1 follows the actual reachable Python function graph:
#
# call_openai_director
#        ↓
# internal helper
#        ↓
# OpenAI Responses request
#        ↓
# strict JSON schema
#
# WITHOUT calling any provider.
#
# =========================================================

from __future__ import annotations

import inspect
import sys

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
)


# =========================================================
# RESULTS
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
            str(
                name
            ),
            bool(
                passed
            ),
            str(
                detail
                or ""
            ),
        )
    )


# =========================================================
# VERSION
# =========================================================

def version_tuple(
    value: Any,
) -> Tuple[int, ...]:

    text = str(
        value
        or ""
    ).strip()

    output = []

    for token in text.split(
        "."
    ):

        digits = ""

        for char in token:

            if char.isdigit():

                digits += char

            else:

                break

        output.append(
            int(
                digits
                or 0
            )
        )

    return tuple(
        output
    )


def version_at_least(
    actual: Any,
    minimum: str,
) -> bool:

    left = version_tuple(
        actual
    )

    right = version_tuple(
        minimum
    )

    length = max(
        len(
            left
        ),
        len(
            right
        ),
    )

    left += (
        0,
    ) * (
        length
        -
        len(
            left
        )
    )

    right += (
        0,
    ) * (
        length
        -
        len(
            right
        )
    )

    return (
        left
        >=
        right
    )


# =========================================================
# IMPORT
# =========================================================

def safe_import(
    module_name: str,
):

    try:

        module = __import__(
            module_name
        )

        record(
            "import_"
            +
            module_name,
            True,
        )

        return module

    except Exception as error:

        record(
            "import_"
            +
            module_name,
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
# SAFE SOURCE
# =========================================================

def safe_source(
    value: Any,
) -> str:

    try:

        return inspect.getsource(
            value
        )

    except Exception:

        return ""


# =========================================================
# FUNCTION GRAPH
# =========================================================

def same_module_function(
    module,
    value: Any,
) -> bool:

    if not inspect.isfunction(
        value
    ):

        return False

    return (
        getattr(
            value,
            "__module__",
            ""
        )
        ==
        getattr(
            module,
            "__name__",
            ""
        )
    )


def reachable_functions(
    module,
    root_function,
    *,
    max_depth: int = 8,
) -> Dict[
    str,
    Any,
]:

    found: Dict[
        str,
        Any,
    ] = {}

    visited: Set[int] = set()

    def walk(
        function,
        depth: int,
    ) -> None:

        if function is None:

            return

        if not inspect.isfunction(
            function
        ):

            return

        identity = id(
            function
        )

        if identity in visited:

            return

        visited.add(
            identity
        )

        name = getattr(
            function,
            "__name__",
            "",
        )

        if name:

            found[
                name
            ] = function

        if depth >= max_depth:

            return

        code = getattr(
            function,
            "__code__",
            None,
        )

        if code is None:

            return

        for referenced_name in (
            code.co_names
        ):

            candidate = getattr(
                module,
                referenced_name,
                None,
            )

            if not same_module_function(
                module,
                candidate,
            ):

                continue

            walk(
                candidate,
                depth + 1,
            )

    walk(
        root_function,
        0,
    )

    return found


# =========================================================
# OPENAI STRICT PATH DISCOVERY
# =========================================================

def function_uses_openai_responses(
    function: Any,
) -> bool:

    source = safe_source(
        function
    )

    code = getattr(
        function,
        "__code__",
        None,
    )

    names = set(
        getattr(
            code,
            "co_names",
            (),
        )
    )

    signals = [
        (
            "OPENAI_RESPONSES_URL"
            in source
        ),

        (
            "OPENAI_RESPONSES_URL"
            in names
        ),

        (
            "/v1/responses"
            in source
        ),

        (
            "api.openai.com/v1/responses"
            in source
        ),
    ]

    return any(
        signals
    )


def function_has_strict_schema(
    function: Any,
) -> bool:

    source = safe_source(
        function
    )

    compact = (
        source
        .replace(
            " ",
            ""
        )
        .replace(
            "\n",
            ""
        )
        .replace(
            "'",
            '"'
        )
        .lower()
    )

    schema_signal = bool(
        (
            "json_schema"
            in compact
        )
        or
        (
            '"type":"json_schema"'
            in compact
        )
    )

    strict_signal = bool(
        (
            '"strict":true'
            in compact
        )
        or
        (
            "strict=true"
            in compact
        )
    )

    response_format_signal = bool(
        (
            '"format"'
            in compact
        )
        or
        (
            "response_format"
            in compact
        )
        or
        (
            '"text"'
            in compact
        )
    )

    return bool(
        schema_signal
        and
        strict_signal
        and
        response_format_signal
    )


def discover_strict_openai_path(
    module,
) -> Dict[str, Any]:

    director = getattr(
        module,
        "call_openai_director",
        None,
    )

    if not callable(
        director
    ):

        return {
            "found":
                False,

            "reason":
                "call_openai_director_missing",

            "reachable":
                [],

            "strict_helpers":
                [],

            "openai_helpers":
                [],
        }

    reachable = (
        reachable_functions(
            module,
            director,
        )
    )

    openai_helpers = []

    strict_helpers = []

    for name, function in (
        reachable.items()
    ):

        if function_uses_openai_responses(
            function
        ):

            openai_helpers.append(
                name
            )

        if (
            function_uses_openai_responses(
                function
            )
            and
            function_has_strict_schema(
                function
            )
        ):

            strict_helpers.append(
                name
            )

    #
    # Some implementations keep schema construction in one
    # helper and HTTP POST in another helper.
    #
    # Therefore also accept a REACHABLE chain where:
    #
    # - one reachable function uses OpenAI Responses
    # - another reachable function contains strict schema
    #

    schema_helpers = []

    for name, function in (
        reachable.items()
    ):

        if function_has_strict_schema(
            function
        ):

            schema_helpers.append(
                name
            )

    split_chain = bool(
        openai_helpers
        and
        schema_helpers
    )

    direct_chain = bool(
        strict_helpers
    )

    return {
        "found":
            bool(
                direct_chain
                or
                split_chain
            ),

        "reason":
            (
                "strict_openai_path_found"
                if
                (
                    direct_chain
                    or
                    split_chain
                )
                else
                "strict_openai_path_not_found"
            ),

        "reachable":
            sorted(
                reachable.keys()
            ),

        "strict_helpers":
            sorted(
                strict_helpers
            ),

        "openai_helpers":
            sorted(
                openai_helpers
            ),

        "schema_helpers":
            sorted(
                schema_helpers
            ),
    }


# =========================================================
# DIRECTOR ROUTING
# =========================================================

def director_is_not_blind_gemini(
    module,
) -> Dict[str, Any]:

    director = getattr(
        module,
        "call_openai_director",
        None,
    )

    if not callable(
        director
    ):

        return {
            "passed":
                False,

            "detail":
                "call_openai_director missing",
        }

    source = safe_source(
        director
    )

    compact = (
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
    # Historical broken behavior:
    #
    # if GEMINI_API_KEY:
    #     return call_gemini_director(...)
    #
    # before structured/json classification.
    #

    gemini_if = (
        compact.find(
            "ifgemini_api_key:"
        )
    )

    gemini_return = (
        compact.find(
            "returncall_gemini_director("
        )
    )

    routing_markers = [
        compact.find(
            "structured="
        ),

        compact.find(
            "json_schema"
        ),

        compact.find(
            "json_mode"
        ),

        compact.find(
            "structured"
        ),
    ]

    routing_markers = [
        position
        for position
        in routing_markers
        if position >= 0
    ]

    first_routing = (
        min(
            routing_markers
        )
        if routing_markers
        else
        -1
    )

    blind = bool(
        gemini_if >= 0
        and
        gemini_return
        >
        gemini_if
        and
        (
            first_routing < 0
            or
            gemini_return
            <
            first_routing
        )
    )

    return {
        "passed":
            not blind,

        "detail":
            (
                "structured routing is evaluated before "
                "blind Gemini fallback"
                if not blind
                else
                "historical blind Gemini-first route detected"
            ),
    }


# =========================================================
# VERSION TESTS
# =========================================================

if image_engine:

    value = getattr(
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
            value,
            "2.0",
        ),
        "actual="
        +
        str(
            value
        ),
    )


if creative_brain:

    value = getattr(
        creative_brain,
        "VERSION",
        "",
    )

    record(
        "creative_brain_v5",
        version_at_least(
            value,
            "5.0",
        ),
        "actual="
        +
        str(
            value
        ),
    )


if stc_skill:

    value = getattr(
        stc_skill,
        "VERSION",
        "",
    )

    record(
        "stc_skill_v3",
        version_at_least(
            value,
            "3.0",
        ),
        "actual="
        +
        str(
            value
        ),
    )


if brand_research:

    value = getattr(
        brand_research,
        "VERSION",
        "",
    )

    record(
        "brand_research_v2",
        version_at_least(
            value,
            "2.0",
        ),
        "actual="
        +
        str(
            value
        ),
    )


if brand_memory:

    value = getattr(
        brand_memory,
        "VERSION",
        "",
    )

    record(
        "brand_memory_v3",
        version_at_least(
            value,
            "3.0",
        ),
        "actual="
        +
        str(
            value
        ),
    )


if production:

    value = getattr(
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
            value,
            "5.0",
        ),
        "actual="
        +
        str(
            value
        ),
    )


if telegram_runtime:

    value = getattr(
        telegram_runtime,
        "VERSION",
        "",
    )

    record(
        "telegram_v3_4",
        version_at_least(
            value,
            "3.4",
        ),
        "actual="
        +
        str(
            value
        ),
    )


# =========================================================
# TELEGRAM CONTRACT
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
# STC CONTRACT
# =========================================================

if stc_skill:

    base_request = (
        "أنشئ صورة إعلانية لبنك STC Bank "
        "عن خدمات التجارة الإلكترونية ونقاط البيع"
    )

    realistic_request = (
        base_request
        +
        " واقعي فوتوغرافي"
    )

    record(
        "stc_style_question_required",
        bool(
            stc_skill
            .stc_style_question_needed(
                base_request
            )
        ),
    )

    record(
        "stc_explicit_style_bypass",
        not bool(
            stc_skill
            .stc_style_question_needed(
                realistic_request
            )
        ),
    )

    record(
        "stc_merchant_semantics",
        (
            stc_skill
            .detect_stc_benefit_family(
                base_request
            )
            ==
            "merchant_payments"
        ),
    )


# =========================================================
# RESEARCH CONTRACT
# =========================================================

if brand_research:

    profile = (
        getattr(
            brand_research,
            "BRAND_PROFILES",
            {},
        )
        .get(
            "stc_bank",
            {},
        )
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
        "actual="
        +
        str(
            profile.get(
                "default_mode"
            )
        ),
    )

    research_calls = int(
        getattr(
            brand_research,
            "RESEARCH_MAX_CALLS",
            999,
        )
    )

    record(
        "research_max_three_calls",
        research_calls
        <=
        3,
        "actual="
        +
        str(
            research_calls
        ),
    )

    cache_ttl = int(
        getattr(
            brand_research,
            "RESEARCH_CACHE_TTL_SECONDS",
            0,
        )
    )

    record(
        "research_cache_24h_or_more",
        cache_ttl
        >=
        86400,
        "actual="
        +
        str(
            cache_ttl
        ),
    )


# =========================================================
# MEMORY CONTRACT
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

    reference_limit = int(
        getattr(
            brand_memory,
            "STC_REFERENCE_LIMIT",
            999,
        )
    )

    record(
        "memory_stc_max_three_refs",
        reference_limit
        <=
        3,
        "actual="
        +
        str(
            reference_limit
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
# PRODUCTION CONTRACT
# =========================================================

if production:

    max_images = int(
        getattr(
            production,
            "MASTERPIECE_MAX_IMAGE_CALLS",
            999,
        )
    )

    max_vision = int(
        getattr(
            production,
            "MASTERPIECE_MAX_VISION_CALLS",
            999,
        )
    )

    dna_refs = int(
        getattr(
            production,
            "SMART_REFERENCE_SELECTION_LIMIT",
            999,
        )
    )

    physical_refs = int(
        getattr(
            production,
            "MAX_PHYSICAL_REFERENCE_IMAGES",
            999,
        )
    )

    record(
        "production_max_two_images",
        max_images
        <=
        2,
        "actual="
        +
        str(
            max_images
        ),
    )

    record(
        "production_max_two_vision",
        max_vision
        <=
        2,
        "actual="
        +
        str(
            max_vision
        ),
    )

    record(
        "production_max_three_dna_refs",
        dna_refs
        <=
        3,
        "actual="
        +
        str(
            dna_refs
        ),
    )

    record(
        "production_max_two_physical_refs",
        physical_refs
        <=
        2,
        "actual="
        +
        str(
            physical_refs
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
        "actual="
        +
        model,
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
        "actual="
        +
        str(
            status.get(
                "nano_banana_pro_required"
            )
        ),
    )


# =========================================================
# IMAGE ENGINE ROUTE
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
        "actual="
        +
        fast_model,
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
        "actual="
        +
        str(
            best_use_pro
        ),
    )


# =========================================================
# DIRECTOR AUDIT V1.1
# =========================================================

if image_engine:

    routing = (
        director_is_not_blind_gemini(
            image_engine
        )
    )

    record(
        "director_not_unconditional_gemini_first",
        bool(
            routing.get(
                "passed"
            )
        ),
        routing.get(
            "detail",
            "",
        ),
    )

    strict_path = (
        discover_strict_openai_path(
            image_engine
        )
    )

    detail_parts = []

    if strict_path.get(
        "strict_helpers"
    ):

        detail_parts.append(
            (
                "strict="
                +
                ",".join(
                    strict_path[
                        "strict_helpers"
                    ]
                )
            )
        )

    if strict_path.get(
        "openai_helpers"
    ):

        detail_parts.append(
            (
                "openai="
                +
                ",".join(
                    strict_path[
                        "openai_helpers"
                    ]
                )
            )
        )

    if strict_path.get(
        "schema_helpers"
    ):

        detail_parts.append(
            (
                "schema="
                +
                ",".join(
                    strict_path[
                        "schema_helpers"
                    ]
                )
            )
        )

    if not detail_parts:

        detail_parts.append(
            strict_path.get(
                "reason",
                "",
            )
        )

    record(
        "director_has_strict_openai_path",
        bool(
            strict_path.get(
                "found"
            )
        ),
        " | ".join(
            detail_parts
        ),
    )

    #
    # Extra evidence:
    # model must be Sol for structured Director.
    #

    openai_director_model = str(
        getattr(
            image_engine,
            "OPENAI_DIRECTOR_MODEL",
            "",
        )
    ).lower()

    record(
        "director_openai_model_sol",
        (
            "gpt-5.6-sol"
            in
            openai_director_model
        ),
        "actual="
        +
        openai_director_model,
    )


# =========================================================
# CREATIVE CONTRACT
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

    module_source = safe_source(
        creative_brain
    )

    record(
        "creative_technical_failure_contract",
        (
            "technical_failure"
            in
            module_source
        ),
    )


# =========================================================
# CROSS MODULE
# =========================================================

if (
    production
    and
    brand_memory
):

    record(
        "production_memory_loader_contract",
        (
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
        (
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
        (
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
            )
        ),
    )


# =========================================================
# STC GUARD
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
            or
            "no text"
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
# REPORT
# =========================================================

print("")
print(
    "=============================================="
)
print(
    " XPAND VISUAL STACK INTEGRATION AUDIT V1.1"
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


for (
    name,
    passed,
    detail,
) in RESULTS:

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


# =========================================================
# CRITICAL
# =========================================================

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
    "director_openai_model_sol",

    "telegram_production_contract",
    "telegram_creative_contract",
}


critical_failures = [
    name
    for (
        name,
        passed,
        _
    )
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

    for item in (
        critical_failures
    ):

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

    print(
        "🚫 No Vision calls were made by this audit."
    )

    print(
        "🚫 No images were generated by this audit."
    )

    sys.exit(
        1
    )


# =========================================================
# READY
# =========================================================

print(
    "✅ XPAND VISUAL STACK: READY FOR CONTROLLED LIVE TEST"
)

print("")

print(
    "Expected STC path:"
)

print(
    "STC request"
)

print(
    "→ style selection"
)

print(
    "→ cached/local Brand Research"
)

print(
    "→ Creative Brain V5"
)

print(
    "→ strict structured OpenAI Director"
)

print(
    "→ max 3 curated reference DNA"
)

print(
    "→ max 2 physical references"
)

print(
    "→ Nano Banana 2"
)

print(
    "→ one Vision QA"
)

print(
    "→ second Nano Banana 2 only if a real defect exists"
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
