python - <<'PY'
from pathlib import Path
from datetime import datetime
import shutil
import re
import py_compile

# =========================================================
# LOCATE FILE
# =========================================================

candidates = [
    Path("/app/telegram-bot/xpand_image_telegram.py"),
    Path("/app/xpand_image_telegram.py"),
    Path.cwd() / "telegram-bot" / "xpand_image_telegram.py",
    Path.cwd() / "xpand_image_telegram.py",
]

path = next(
    (p for p in candidates if p.is_file()),
    None
)

if path is None:
    hits = list(Path("/app").rglob("xpand_image_telegram.py"))

    if hits:
        hits.sort(
            key=lambda p: (
                0 if "telegram-bot" in str(p) else 1,
                len(str(p))
            )
        )
        path = hits[0]

if path is None:
    raise SystemExit(
        "❌ xpand_image_telegram.py not found"
    )

print("📄 File:", path)

source = path.read_text(
    encoding="utf-8"
)

original = source

# =========================================================
# BACKUP
# =========================================================

stamp = datetime.now().strftime(
    "%Y%m%d-%H%M%S"
)

backup = path.with_name(
    path.name + ".bak-" + stamp
)

shutil.copy2(
    path,
    backup
)

print("💾 Backup:", backup)

# =========================================================
# VERSION
# =========================================================

source = source.replace(
    'VERSION = "3.2"',
    'VERSION = "3.2.1"',
    1
)

# =========================================================
# DEFAULT SMART FALLBACK
# =========================================================

source = source.replace(
    '"XPAND_MASTERPIECE_ALLOW_SMART_FALLBACK",\n        "false"',
    '"XPAND_MASTERPIECE_ALLOW_SMART_FALLBACK",\n        "true"',
    1
)

# =========================================================
# REPLACE CREATIVE QUALITY + MASTERPIECE GUARD
# =========================================================

guard_start_marker = """# =========================================================
# CREATIVE QUALITY
# ========================================================="""

guard_end_marker = """# =========================================================
# PRE-GENERATION ORCHESTRATION
# ========================================================="""

start = source.find(
    guard_start_marker
)

end = source.find(
    guard_end_marker,
    start
)

if start < 0 or end < 0:
    raise SystemExit(
        "❌ Creative Quality / Guard section not found"
    )

new_guard = r'''# =========================================================
# CREATIVE QUALITY / RUNTIME STATE
# =========================================================

def creative_quality_metadata(
    response
) -> Dict[str, Any]:

    if response is None:
        return {}

    return safe_dict(
        getattr(
            response,
            "metadata",
            {}
        )
    )


def creative_quality_passed(
    response
) -> bool:

    if response is None:
        return False

    winner = getattr(
        response,
        "winner",
        None
    )

    if winner is None:
        return False

    metadata = creative_quality_metadata(
        response
    )

    return bool(
        metadata.get(
            "quality_gate_passed",
            False
        )
        and
        getattr(
            winner,
            "quality_gate_passed",
            False
        )
        and
        getattr(
            winner,
            "evaluation_valid",
            False
        )
    )


def creative_runtime_state(
    response
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

            "quality_target_blocks_production":
                False,

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
        None
    )

    technical_failure = bool(
        metadata.get(
            "technical_failure",
            False
        )
    )

    quality_gate_evaluated = bool(
        metadata.get(
            "quality_gate_evaluated",
            winner is not None
        )
    )

    quality_gate_passed = bool(
        metadata.get(
            "quality_gate_passed",
            False
        )
    )

    allow_fallback = bool(
        metadata.get(
            "allow_smart_engine_fallback",
            False
        )
    )

    quality_target_blocks = bool(
        metadata.get(
            "quality_target_blocks_production",
            False
        )
    )

    failure_reason = clean_text(
        metadata.get(
            "failure_reason",
            ""
        ),
        1000
    )

    if (
        technical_failure
        or
        not quality_gate_evaluated
    ):

        state = "technical_failure"

        allow_fallback = True

    elif creative_quality_passed(
        response
    ):

        state = "approved"

    else:

        state = "quality_failed"

        if not quality_target_blocks:
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

        "quality_target_blocks_production":
            quality_target_blocks,

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
    prepared: Dict[str, Any]
) -> Dict[str, Any]:

    creative_mode = clean_text(
        prepared.get(
            "creative_mode",
            ""
        ),
        100
    )

    if (
        creative_mode
        !=
        CREATIVE_MODE_MASTERPIECE
    ):

        return {
            "allowed":
                True,

            "route":
                "normal",

            "code":
                "not_masterpiece",

            "message":
                "Normal visual route.",
        }

    #
    # Campaign validation remains strict.
    #

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
        "state",
        "technical_failure"
    )

    #
    # Valid Masterpiece direction.
    #

    if state == "approved":

        return {
            "allowed":
                True,

            "route":
                "masterpiece",

            "code":
                "passed",

            "message":
                "Masterpiece Integration Guard passed.",

            "creative_state":
                state,
        }

    #
    # Technical failure is NOT a quality rejection.
    #
    # Examples:
    # - model returned wrong JSON schema
    # - parser failure
    # - transport/provider failure
    # - no real evaluation happened
    #

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
                    "Creative Brain technical failure; "
                    "continue with Smart Engine fallback."
                ),

            "creative_state":
                state,

            "failure_reason":
                runtime.get(
                    "failure_reason",
                    ""
                ),
        }

    #
    # A real creative-quality miss may still continue
    # when Creative Brain explicitly says the target
    # must not block production.
    #

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
                    "Creative quality target was not reached; "
                    "continue with Smart Engine fallback."
                ),

            "creative_state":
                state,
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
                "and Smart Engine fallback is disabled."
            ),

        "creative_state":
            state,
    }


def enforce_masterpiece_guard(
    prepared: Dict[str, Any]
) -> Dict[str, Any]:

    status = masterpiece_guard_status(
        prepared
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
        print(
            "🛑 No image generation was started."
        )
        print(
            "🛑 Smart Engine fallback is blocked."
        )
        print("")

        raise MasterpieceGuardError(
            status.get(
                "message"
            )
            or
            (
                "Masterpiece Integration Guard "
                "blocked production."
            )
        )

    route = status.get(
        "route",
        "masterpiece"
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

    else:

        print(
            "✅ Visual integration guard passed."
        )

    return status


'''

source = (
    source[:start]
    +
    new_guard
    +
    source[end:]
)

# =========================================================
# PROTECT generate_masterpiece_images DOUBLE GUARD
# =========================================================

gm_start = source.find(
    "def generate_masterpiece_images("
)

gm_end = source.find(
    """# =========================================================
# TELEGRAM API
# =========================================================""",
    gm_start
)

if gm_start < 0 or gm_end < 0:
    raise SystemExit(
        "❌ generate_masterpiece_images section not found"
    )

gm = source[
    gm_start:
    gm_end
]

old_double_guard = """    enforce_masterpiece_guard(
        prepared
    )"""

new_double_guard = """    guard_status = enforce_masterpiece_guard(
        prepared
    )

    if (
        guard_status.get(
            "route"
        )
        !=
        "masterpiece"
    ):

        return (
            [],
            [],
            [
                (
                    "masterpiece_skipped: "
                    +
                    clean_text(
                        guard_status.get(
                            "code",
                            "smart_fallback"
                        ),
                        500
                    )
                )
            ],
        )"""

if old_double_guard not in gm:
    raise SystemExit(
        "❌ Masterpiece double guard not found"
    )

gm = gm.replace(
    old_double_guard,
    new_double_guard,
    1
)

source = (
    source[:gm_start]
    +
    gm
    +
    source[gm_end:]
)

# =========================================================
# PATCH generate_and_deliver
# =========================================================

gd_start = source.find(
    "def generate_and_deliver("
)

gd_end = source.find(
    """# =========================================================
# VISUAL TOKEN STORE
# =========================================================""",
    gd_start
)

if gd_start < 0 or gd_end < 0:
    raise SystemExit(
        "❌ generate_and_deliver section not found"
    )

gd = source[
    gd_start:
    gd_end
]

gd = gd.replace(
    "    creative_score = 0.0",
    "    creative_score = None",
    1
)

masterpiece_marker = """    # =====================================================
    # MASTERPIECE
    # =====================================================
"""

smart_marker = """    # =====================================================
    # NORMAL SMART ENGINE
    # =====================================================
"""

mp_pos = gd.find(
    masterpiece_marker
)

smart_pos = gd.find(
    smart_marker,
    mp_pos
)

if mp_pos < 0 or smart_pos < 0:
    raise SystemExit(
        "❌ Masterpiece / Smart routing markers not found"
    )

new_routing = r'''    # =====================================================
    # MASTERPIECE / SMART FALLBACK ROUTING
    # =====================================================

    guard_status = {
        "allowed":
            True,

        "route":
            "normal",

        "code":
            "not_masterpiece",
    }

    if use_masterpiece:

        guard_status = (
            enforce_masterpiece_guard(
                prepared
            )
        )

        if (
            guard_status.get(
                "route"
            )
            ==
            "masterpiece"
        ):

            try:

                core.send_message(
                    chat_id,
                    (
                        "تمام، Masterpiece Gate اجتاز. "
                        "هسا ببدأ الإنتاج الفعلي والمراجعة البصرية."
                    )
                )

            except Exception:

                pass

            (
                images,
                production_metadata,
                masterpiece_errors,
            ) = generate_masterpiece_images(
                core=
                    core,

                user_id=
                    user_id,

                request_text=
                    prompt,

                prepared=
                    prepared,

                number=
                    number,

                aspect_ratio=
                    aspect_ratio
            )

            pipeline_errors.extend(
                masterpiece_errors
            )

            if not images:

                print(
                    (
                        "⚠️ Masterpiece returned no image; "
                        "Smart Engine fallback remains available."
                    )
                )

        else:

            print(
                (
                    "⚡ Masterpiece production skipped"
                    +
                    " | route="
                    +
                    clean_text(
                        guard_status.get(
                            "route",
                            ""
                        ),
                        100
                    )
                    +
                    " | reason="
                    +
                    clean_text(
                        guard_status.get(
                            "code",
                            ""
                        ),
                        500
                    )
                )
            )
'''

gd = (
    gd[:mp_pos]
    +
    new_routing
    +
    "\n\n"
    +
    gd[smart_pos:]
)

old_condition = """    if not images and (
        not use_masterpiece
        or MASTERPIECE_ALLOW_SMART_FALLBACK
    ):
"""

new_condition = """    if not images and (
        not use_masterpiece
        or
        guard_status.get(
            "route"
        )
        ==
        "smart_fallback"
        or
        MASTERPIECE_ALLOW_SMART_FALLBACK
    ):
"""

if old_condition not in gd:
    raise SystemExit(
        "❌ Smart Engine fallback condition not found"
    )

gd = gd.replace(
    old_condition,
    new_condition,
    1
)

old_no_images = """    if not images:
        raise MasterpieceGuardError(
            "لم يتم تسليم صورة لأن جميع نتائج Masterpiece فشلت في بوابة الجودة."
        )
"""

new_no_images = """    if not images:
        raise RuntimeError(
            "لم يتم تسليم صورة لأن جميع مسارات التوليد المتاحة لم تُرجع صورة."
        )
"""

if old_no_images in gd:
    gd = gd.replace(
        old_no_images,
        new_no_images,
        1
    )

source = (
    source[:gd_start]
    +
    gd
    +
    source[gd_end:]
)

# =========================================================
# VALIDATION
# =========================================================

required_markers = [
    '"creative_brain_technical_fallback"',
    '"smart_fallback"',
    "creative_runtime_state",
    "MASTERPIECE / SMART FALLBACK ROUTING",
    "creative_score = None",
]

missing = [
    marker
    for marker in required_markers
    if marker not in source
]

if missing:
    raise SystemExit(
        "❌ Patch validation failed: "
        + ", ".join(missing)
    )

compile(
    source,
    str(path),
    "exec"
)

# =========================================================
# WRITE
# =========================================================

path.write_text(
    source,
    encoding="utf-8"
)

py_compile.compile(
    str(path),
    doraise=True
)

print("")
print("==========================================")
print(" ✅ XPAND IMAGE TELEGRAM PATCH COMPLETE")
print("==========================================")
print("file =", path)
print("backup =", backup)
print("version = 3.2.1")
print("syntax = PASS")
print("technical_failure -> smart_fallback = ENABLED")
print("quality_target -> smart_fallback = ENABLED")
print("strict campaign guard = PRESERVED")
print("creative_score without evaluation = None")
print("==========================================")
print("")
PY
