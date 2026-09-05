# =========================================================
# XPAND VISUAL STACK INTEGRATION AUDIT V2.0
#
# ZERO API
# ZERO DATABASE
# ZERO IMAGE
#
# =========================================================
#
# CURRENT MASTERPIECE ARCHITECTURE
# ---------------------------------------------------------
#
# STC request
#      ↓
# Canonical STC Policy
#      ↓
# Telegram V3.6
#      ↓
# Creative Brain V5.6
#      ↓
# GPT-5.6 Sol Creative Director
#      ↓
# Permanent STC Brand Kit
#      ↓
# Nano Banana 2 PREVISUALIZATION ONLY
#      ↓
# Gemini Preview Audit
#      ↓
# GPT-Image-2 FINAL
#      ↓
# GPT-5.6 Sol Final QA
#      ↓
# GPT-Image-2 repair only if required
#      ↓
# Telegram delivery
#
#
# HARD REGRESSION CHECKS
# ---------------------------------------------------------
#
# - premium cannot erase digital_banking
# - premium cannot erase merchant_payments
# - GPT-Image-2 is mandatory Masterpiece final
# - Gemini cannot become Masterpiece final
# - Nano Banana 2 is preview only
# - immutable final locks enabled
# - 15–22% copy space preserved
# - giant blank upper third blocked
# - phone/POS fusion blocked
# - invented payment hardware blocked
# - random stone/travertine pedestal blocked
# - STC references remain visual authority
# - quality rejection cannot fall to Smart
#
#
# RUN
# ---------------------------------------------------------
#
# python xpand_visual_stack_test.py
#
# =========================================================

from __future__ import annotations

import inspect
import sys

from typing import (
    Any,
    Dict,
    List,
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
            str(name),
            bool(passed),
            str(detail or ""),
        )
    )


# =========================================================
# VERSION HELPERS
# =========================================================

def version_tuple(
    value: Any,
) -> Tuple[int, ...]:

    text = str(
        value
        or ""
    ).strip()

    output: List[int] = []

    for token in text.split("."):

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

    return tuple(output)


def version_at_least(
    actual: Any,
    minimum: str,
) -> bool:

    left = version_tuple(actual)
    right = version_tuple(minimum)

    length = max(
        len(left),
        len(right),
    )

    left += (
        0,
    ) * (
        length
        -
        len(left)
    )

    right += (
        0,
    ) * (
        length
        -
        len(right)
    )

    return left >= right


# =========================================================
# SAFE IMPORT
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
            str(error),
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

stc_policy = safe_import(
    "xpand_stc_policy"
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


def module_source(
    module: Any,
) -> str:

    if module is None:
        return ""

    try:

        return inspect.getsource(
            module
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
            "",
        )
        ==
        getattr(
            module,
            "__name__",
            "",
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
            found[name] = function

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
# OPENAI STRICT PATH
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

    return bool(
        (
            "OPENAI_RESPONSES_URL"
            in source
        )
        or
        (
            "OPENAI_RESPONSES_URL"
            in names
        )
        or
        (
            "/v1/responses"
            in source
        )
        or
        (
            "api.openai.com/v1/responses"
            in source
        )
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
            "schema_helpers":
                [],
        }

    reachable = (
        reachable_functions(
            module,
            director,
        )
    )

    openai_helpers: List[str] = []
    strict_helpers: List[str] = []
    schema_helpers: List[str] = []

    for name, function in (
        reachable.items()
    ):

        uses_openai = (
            function_uses_openai_responses(
                function
            )
        )

        has_schema = (
            function_has_strict_schema(
                function
            )
        )

        if uses_openai:

            openai_helpers.append(
                name
            )

        if has_schema:

            schema_helpers.append(
                name
            )

        if (
            uses_openai
            and
            has_schema
        ):

            strict_helpers.append(
                name
            )

    direct_chain = bool(
        strict_helpers
    )

    split_chain = bool(
        openai_helpers
        and
        schema_helpers
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

    gemini_if = compact.find(
        "ifgemini_api_key:"
    )

    gemini_return = compact.find(
        "returncall_gemini_director("
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
                "structured routing evaluated before blind Gemini fallback"
                if not blind
                else
                "historical blind Gemini-first route detected"
            ),
    }


# =========================================================
# MODULE VERSIONS
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
        "image_engine_v3",
        version_at_least(
            value,
            "3.0",
        ),
        "actual="
        +
        str(value),
    )


if creative_brain:

    value = getattr(
        creative_brain,
        "VERSION",
        "",
    )

    record(
        "creative_brain_v5_6",
        version_at_least(
            value,
            "5.6",
        ),
        "actual="
        +
        str(value),
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
        str(value),
    )


if stc_policy:

    value = getattr(
        stc_policy,
        "VERSION",
        "",
    )

    record(
        "stc_policy_v1",
        version_at_least(
            value,
            "1.0",
        ),
        "actual="
        +
        str(value),
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
        str(value),
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
        str(value),
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
        "production_v6",
        version_at_least(
            value,
            "6.0.1",
        ),
        "actual="
        +
        str(value),
    )


if telegram_runtime:

    value = getattr(
        telegram_runtime,
        "VERSION",
        "",
    )

    record(
        "telegram_v3_6",
        version_at_least(
            value,
            "3.6",
        ),
        "actual="
        +
        str(value),
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
        "telegram_masterpiece_exists",
        callable(
            getattr(
                telegram_runtime,
                "generate_masterpiece_images",
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

    source = module_source(
        telegram_runtime
    )

    record(
        "telegram_uses_canonical_stc_policy",
        (
            "resolve_stc_benefit_family"
            in source
            or
            "resolve_stc_benefit_family_id"
            in source
        ),
    )

    record(
        "telegram_quality_failure_blocks_smart",
        (
            "quality_failure"
            in source
            and
            "Smart fallback"
            in source
        ),
    )


# =========================================================
# STC CANONICAL POLICY
# =========================================================

if stc_policy:

    resolver = getattr(
        stc_policy,
        "resolve_stc_benefit_family_id",
        None,
    )

    if callable(
        resolver
    ):

        merchant_request = (
            "أنشئ إعلان STC Bank عن خدمات "
            "التجارة الإلكترونية ونقاط البيع"
        )

        transfer_request = (
            "STC Bank حوالتك حول العالم "
            "وتقدر تتبعها من التطبيق"
        )

        record(
            "policy_merchant_payments",
            (
                resolver(
                    merchant_request
                )
                ==
                "merchant_payments"
            ),
        )

        record(
            "policy_digital_banking",
            (
                resolver(
                    transfer_request
                )
                ==
                "digital_banking"
            ),
        )

        record(
            "policy_premium_cannot_erase_merchant",
            (
                resolver(
                    merchant_request,
                    "premium",
                )
                ==
                "merchant_payments"
            ),
        )

        record(
            "policy_premium_cannot_erase_digital",
            (
                resolver(
                    transfer_request,
                    "premium",
                )
                ==
                "digital_banking"
            ),
        )

    else:

        record(
            "policy_merchant_payments",
            False,
            "resolver missing",
        )

        record(
            "policy_digital_banking",
            False,
            "resolver missing",
        )

        record(
            "policy_premium_cannot_erase_merchant",
            False,
            "resolver missing",
        )

        record(
            "policy_premium_cannot_erase_digital",
            False,
            "resolver missing",
        )

    creative_builder = getattr(
        stc_policy,
        "build_creative_constitution_text",
        None,
    )

    final_builder = getattr(
        stc_policy,
        "build_final_render_locks_text",
        None,
    )

    record(
        "policy_creative_constitution_exists",
        callable(
            creative_builder
        ),
    )

    record(
        "policy_final_render_locks_exists",
        callable(
            final_builder
        ),
    )

    if callable(
        final_builder
    ):

        final_lock_text = final_builder(
            (
                "خدمات التجارة الإلكترونية "
                "ونقاط البيع"
            ),
            "premium",
            "premium_realistic",
        )

        record(
            "policy_copy_space_15_22",
            (
                "15–22%"
                in final_lock_text
            ),
        )

        record(
            "policy_no_giant_upper_third",
            (
                "giant blank upper third"
                in final_lock_text
            ),
        )

        record(
            "policy_reference_authority",
            (
                "reference images have authority"
                in final_lock_text.lower()
            ),
        )


# =========================================================
# STC SKILL CONTRACT
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
        "stc_skill_merchant_semantics",
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
# BRAND RESEARCH
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
# BRAND MEMORY
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
# PRODUCTION V6 CONTRACT
# =========================================================

if production:

    status = (
        production
        .get_production_engine_status()
    )

    record(
        "production_previs_nano_banana_2",
        (
            "gemini-3.1-flash-image"
            in str(
                status.get(
                    "nano_banana_2_model",
                    "",
                )
            )
        ),
        "actual="
        +
        str(
            status.get(
                "nano_banana_2_model"
            )
        ),
    )

    record(
        "production_nano_banana_preview_only",
        (
            status.get(
                "nano_banana_role"
            )
            ==
            "previsualization_only"
        ),
        "actual="
        +
        str(
            status.get(
                "nano_banana_role"
            )
        ),
    )

    record(
        "production_final_gpt_image_2",
        (
            status.get(
                "final_image_model"
            )
            ==
            "gpt-image-2"
        ),
        "actual="
        +
        str(
            status.get(
                "final_image_model"
            )
        ),
    )

    record(
        "production_final_renderer_openai",
        (
            status.get(
                "final_renderer"
            )
            ==
            "openai"
        ),
        "actual="
        +
        str(
            status.get(
                "final_renderer"
            )
        ),
    )

    record(
        "production_openai_final_mandatory",
        bool(
            status.get(
                "mandatory_openai_final"
            )
        ),
        "actual="
        +
        str(
            status.get(
                "mandatory_openai_final"
            )
        ),
    )

    record(
        "production_gemini_final_forbidden",
        (
            status.get(
                "gemini_final_allowed"
            )
            is False
        ),
        "actual="
        +
        str(
            status.get(
                "gemini_final_allowed"
            )
        ),
    )

    record(
        "production_gemini_pro_final_forbidden",
        (
            status.get(
                "gemini_pro_final"
            )
            is False
        ),
        "actual="
        +
        str(
            status.get(
                "gemini_pro_final"
            )
        ),
    )

    record(
        "production_one_previsualization",
        int(
            status.get(
                "previsualization_calls",
                999,
            )
        )
        ==
        1,
        "actual="
        +
        str(
            status.get(
                "previsualization_calls"
            )
        ),
    )

    record(
        "production_max_two_final_images",
        int(
            status.get(
                "max_image_calls",
                999,
            )
        )
        <=
        2,
        "actual="
        +
        str(
            status.get(
                "max_image_calls"
            )
        ),
    )

    record(
        "production_max_two_final_vision",
        int(
            status.get(
                "max_vision_calls",
                999,
            )
        )
        <=
        2,
        "actual="
        +
        str(
            status.get(
                "max_vision_calls"
            )
        ),
    )

    record(
        "production_one_preview_audit",
        int(
            status.get(
                "preview_audit_calls",
                999,
            )
        )
        ==
        1,
        "actual="
        +
        str(
            status.get(
                "preview_audit_calls"
            )
        ),
    )

    record(
        "production_stc_five_pack_refs",
        int(
            status.get(
                "stc_physical_reference_limit",
                0,
            )
        )
        >=
        5,
        "actual="
        +
        str(
            status.get(
                "stc_physical_reference_limit"
            )
        ),
    )

    record(
        "production_stc_three_render_refs",
        int(
            status.get(
                "stc_render_reference_limit",
                999,
            )
        )
        <=
        3,
        "actual="
        +
        str(
            status.get(
                "stc_render_reference_limit"
            )
        ),
    )

    record(
        "production_stc_three_final_refs",
        int(
            status.get(
                "stc_final_reference_limit",
                999,
            )
        )
        <=
        3,
        "actual="
        +
        str(
            status.get(
                "stc_final_reference_limit"
            )
        ),
    )

    record(
        "production_stc_two_repair_refs",
        int(
            status.get(
                "stc_edit_reference_limit",
                999,
            )
        )
        <=
        2,
        "actual="
        +
        str(
            status.get(
                "stc_edit_reference_limit"
            )
        ),
    )

    record(
        "production_stc_brand_kit_available",
        bool(
            status.get(
                "stc_brand_kit_available"
            )
        ),
        "actual="
        +
        str(
            status.get(
                "stc_brand_kit_available"
            )
        ),
    )

    record(
        "production_stc_brand_pack_required",
        bool(
            status.get(
                "stc_brand_pack_required"
            )
        ),
        "actual="
        +
        str(
            status.get(
                "stc_brand_pack_required"
            )
        ),
    )

    record(
        "production_stc_high_alert",
        bool(
            status.get(
                "stc_high_alert_enabled"
            )
        ),
        "actual="
        +
        str(
            status.get(
                "stc_high_alert_enabled"
            )
        ),
    )

    record(
        "production_stc_qa_target_92",
        float(
            status.get(
                "stc_qa_target",
                0,
            )
        )
        >=
        92.0,
        "actual="
        +
        str(
            status.get(
                "stc_qa_target"
            )
        ),
    )

    record(
        "production_stc_release_floor_88",
        float(
            status.get(
                "stc_qa_release_floor",
                0,
            )
        )
        >=
        88.0,
        "actual="
        +
        str(
            status.get(
                "stc_qa_release_floor"
            )
        ),
    )

    record(
        "production_copy_space_15_22",
        (
            status.get(
                "copy_space_policy"
            )
            ==
            "15-22_percent_integrated"
        ),
        "actual="
        +
        str(
            status.get(
                "copy_space_policy"
            )
        ),
    )

    record(
        "production_reality_firewall",
        bool(
            status.get(
                "physical_reality_firewall"
            )
        ),
    )

    record(
        "production_invented_hardware_ban",
        bool(
            status.get(
                "invented_payment_hardware_ban"
            )
        ),
    )

    record(
        "production_phone_pos_fusion_ban",
        bool(
            status.get(
                "phone_pos_fusion_ban"
            )
        ),
    )

    record(
        "production_stone_pedestal_ban",
        bool(
            status.get(
                "stone_pedestal_ban"
            )
        ),
    )

    record(
        "production_generic_camera_guard",
        bool(
            status.get(
                "generic_camera_guard"
            )
        ),
    )

    record(
        "production_reference_authority",
        bool(
            status.get(
                "reference_authority"
            )
        ),
    )

    record(
        "production_merchant_message_lock",
        bool(
            status.get(
                "merchant_message_lock"
            )
        ),
    )

    record(
        "production_immutable_final_locks",
        bool(
            status.get(
                "immutable_final_locks"
            )
        ),
    )

    record(
        "production_immutable_sentinel",
        bool(
            str(
                status.get(
                    "immutable_lock_sentinel",
                    "",
                )
            ).strip()
        ),
        "actual="
        +
        str(
            status.get(
                "immutable_lock_sentinel"
            )
        ),
    )


# =========================================================
# PRODUCTION SOURCE REGRESSIONS
# =========================================================

if production:

    source = module_source(
        production
    )

    record(
        "production_final_prompt_blocks_giant_upper_space",
        (
            "NO giant blank upper third"
            in source
        ),
    )

    record(
        "production_final_prompt_blocks_phone_pos",
        (
            "NO phone/POS fusion"
            in source
        ),
    )

    record(
        "production_final_prompt_blocks_invented_hardware",
        (
            "NO invented payment hardware"
            in source
        ),
    )

    record(
        "production_final_prompt_blocks_stone",
        (
            "NO random travertine pedestal"
            in source
            or
            "random stone pedestal"
            in source
        ),
    )

    record(
        "production_final_prompt_has_reference_authority",
        (
            "VISUAL AUTHORITY"
            in source
            or
            "REFERENCE AUTHORITY"
            in source
        ),
    )

    record(
        "production_immutable_compiler_exists",
        callable(
            getattr(
                production,
                "fit_prompt_with_immutable_locks",
                None,
            )
        ),
    )


# =========================================================
# IMAGE ENGINE V3
# =========================================================

if image_engine:

    status = {}

    try:

        status = (
            image_engine
            .get_image_engine_status()
        )

    except Exception:

        status = {}

    fast_model = str(
        getattr(
            image_engine,
            "GOOGLE_IMAGE_FAST_MODEL",
            "",
        )
    )

    final_model = str(
        getattr(
            image_engine,
            "OPENAI_IMAGE_MODEL",
            "",
        )
    )

    record(
        "image_engine_nano_banana_2",
        (
            "gemini-3.1-flash-image"
            in fast_model
        ),
        "actual="
        +
        fast_model,
    )

    record(
        "image_engine_openai_final_model",
        (
            final_model
            ==
            "gpt-image-2"
        ),
        "actual="
        +
        final_model,
    )

    best_final = str(
        status.get(
            "best_final_model",
            "",
        )
    )

    record(
        "image_engine_best_final_gpt_image_2",
        (
            best_final
            ==
            "gpt-image-2"
        ),
        "actual="
        +
        best_final,
    )

    source = module_source(
        image_engine
    )

    record(
        "image_engine_openai_multi_reference",
        (
            "edit_with_openai_multi"
            in source
        ),
    )


# =========================================================
# STRICT OPENAI DIRECTOR
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

    detail_parts: List[str] = []

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
# CREATIVE BRAIN
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

    source = module_source(
        creative_brain
    )

    record(
        "creative_technical_failure_contract",
        (
            "technical_failure"
            in source
        ),
    )

    record(
        "creative_targeted_repair_present",
        (
            "targeted"
            in source.lower()
            and
            "repair"
            in source.lower()
        ),
    )

    record(
        "creative_strict_release_present",
        (
            "strict"
            in source.lower()
            and
            "qualified"
            in source.lower()
        ),
    )


# =========================================================
# CROSS-MODULE CONTRACTS
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


if (
    telegram_runtime
    and
    stc_policy
):

    telegram_source = (
        module_source(
            telegram_runtime
        )
    )

    record(
        "telegram_policy_integration_contract",
        (
            "xpand_stc_policy"
            in telegram_source
            or
            "resolve_stc_benefit_family"
            in telegram_source
        ),
    )


# =========================================================
# STC IMAGE GUARD
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
    " XPAND VISUAL STACK INTEGRATION AUDIT V2.0"
)
print(
    " ZERO-COST / ZERO-API / ZERO-IMAGE"
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
# CRITICAL TESTS
# =========================================================

CRITICAL_TESTS = {

    # imports
    "import_xpand_image_engine",
    "import_xpand_creative_brain",
    "import_xpand_stc_bank_skill",
    "import_xpand_stc_policy",
    "import_xpand_brand_research",
    "import_xpand_brand_memory",
    "import_xpand_production_engine",
    "import_xpand_image_telegram",

    # versions
    "image_engine_v3",
    "creative_brain_v5_6",
    "stc_skill_v3",
    "stc_policy_v1",
    "brand_research_v2",
    "brand_memory_v3",
    "production_v6",
    "telegram_v3_6",

    # canonical service identity
    "policy_merchant_payments",
    "policy_digital_banking",
    "policy_premium_cannot_erase_merchant",
    "policy_premium_cannot_erase_digital",
    "telegram_uses_canonical_stc_policy",
    "telegram_policy_integration_contract",

    # production architecture
    "production_previs_nano_banana_2",
    "production_nano_banana_preview_only",
    "production_final_gpt_image_2",
    "production_final_renderer_openai",
    "production_openai_final_mandatory",
    "production_gemini_final_forbidden",
    "production_gemini_pro_final_forbidden",

    # STC reference architecture
    "production_stc_five_pack_refs",
    "production_stc_three_render_refs",
    "production_stc_three_final_refs",
    "production_stc_brand_kit_available",
    "production_stc_brand_pack_required",

    # quality architecture
    "production_stc_high_alert",
    "production_stc_qa_target_92",
    "production_stc_release_floor_88",
    "production_immutable_final_locks",
    "production_immutable_sentinel",

    # physical regressions
    "production_invented_hardware_ban",
    "production_phone_pos_fusion_ban",
    "production_stone_pedestal_ban",
    "production_reference_authority",
    "production_copy_space_15_22",
    "production_final_prompt_blocks_giant_upper_space",
    "production_immutable_compiler_exists",

    # engine final
    "image_engine_openai_final_model",
    "image_engine_best_final_gpt_image_2",
    "image_engine_openai_multi_reference",

    # director
    "director_not_unconditional_gemini_first",
    "director_has_strict_openai_path",
    "director_openai_model_sol",

    # contracts
    "telegram_install_exists",
    "telegram_masterpiece_exists",
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
        "❌ XPAND VISUAL STACK V2: NOT READY"
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
    "✅ XPAND VISUAL STACK V2: READY FOR CONTROLLED LIVE TEST"
)

print("")

print(
    "Current STC Masterpiece path:"
)

print(
    "STC request"
)

print(
    "→ Canonical STC Policy"
)

print(
    "→ Telegram V3.6"
)

print(
    "→ Creative Brain V5.6"
)

print(
    "→ GPT-5.6 Sol Creative Director"
)

print(
    "→ Permanent STC Brand Pack"
)

print(
    "→ 3 selected physical STC references"
)

print(
    "→ Nano Banana 2 1K PREVISUALIZATION ONLY"
)

print(
    "→ Gemini Preview Audit"
)

print(
    "→ GPT-Image-2 FINAL"
)

print(
    "→ Immutable Final Locks"
)

print(
    "→ GPT-5.6 Sol Final QA"
)

print(
    "→ GPT-Image-2 repair only when required"
)

print(
    "→ Telegram delivery"
)

print("")

print(
    "Final-provider policy:"
)

print(
    "✅ GPT-Image-2 is mandatory Masterpiece final"
)

print(
    "🚫 Gemini cannot be Masterpiece final"
)

print(
    "🚫 Gemini Pro final escalation is disabled"
)

print("")

print(
    "STC quality locks:"
)

print(
    "✅ STC QA target >= 92"
)

print(
    "✅ STC release floor >= 88"
)

print(
    "✅ 15–22% integrated copy space"
)

print(
    "✅ Giant blank upper third blocked"
)

print(
    "✅ Invented payment hardware blocked"
)

print(
    "✅ Phone/POS fusion blocked"
)

print(
    "✅ Random stone/travertine pedestal blocked"
)

print(
    "✅ STC reference authority preserved"
)

print(
    "✅ Canonical benefit family preserved"
)

print("")

print(
    "💰 Normal Masterpiece production:"
)

print(
    "1 Nano Banana 2 previs"
)

print(
    "+ 1 Gemini preview audit"
)

print(
    "+ 1 GPT-Image-2 final"
)

print(
    "+ 1 GPT-5.6 Sol final QA"
)

print("")

print(
    "💰 Maximum Masterpiece production:"
)

print(
    "1 Nano Banana 2 previs"
)

print(
    "+ 1 Gemini preview audit"
)

print(
    "+ 2 GPT-Image-2 final/repair calls"
)

print(
    "+ 2 GPT-5.6 Sol final QA calls"
)

print("")

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
