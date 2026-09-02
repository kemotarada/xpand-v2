# =========================================================
# KEMO AGENT ADMIN - FOCUSED RUNTIME V1.1
#
# PURPOSE
# ---------------------------------------------------------
# Smart focused repository context for XPAND.
#
# Supports TWO focused modes:
#
# 1) XPAND unified profile/runtime:
#    - Text
#    - Telegram Voice
#    - Live Call server
#
# 2) XPAND Live Call architecture:
#    - server.js
#    - app.js
#    - package.json
#
# This fixes large Live Call changes that require both
# backend and browser/frontend code.
#
# Existing resilient AI / approval protections preserved.
# =========================================================


import re

import agent_factory_admin as admin
import agent_factory_admin_resilient as resilient


# =========================================================
# VERSION
# =========================================================

VERSION = "1.1"


# =========================================================
# XPAND UNIFIED PROFILE / RUNTIME FILES
# =========================================================

XPAND_UNIFIED_RUNTIME_FILES = [

    # XPAND text / provider runtime
    "agent_factory_ai_providers.py",

    # XPAND Telegram voice runtime
    "agent_factory_capabilities.py",

    # XPAND Live Call backend
    "agent_templates/live_call/server.js",
]


# =========================================================
# XPAND LIVE CALL ARCHITECTURE FILES
#
# Used when a request changes:
#
# - WebSocket
# - browser audio playback
# - WebRTC output behavior
# - Gemini TTS streaming
# - package dependencies
#
# =========================================================

XPAND_LIVE_CALL_ARCHITECTURE_FILES = [

    "agent_templates/live_call/server.js",

    "agent_templates/live_call/app.js",

    "agent_templates/live_call/package.json",
]


# =========================================================
# SAVE RESILIENT SELECTOR
# =========================================================

ORIGINAL_RESILIENT_SELECTOR = (
    resilient.smart_choose_files_for_request
)


# =========================================================
# HELPERS
# =========================================================

def clean_text(
    value,
    max_length=20000
):

    return str(
        value
        if value is not None
        else
        ""
    ).replace(
        "\x00",
        ""
    ).strip()[:max_length]


def normalize(
    value
):

    text = clean_text(
        value,
        50000
    ).lower()


    replacements = {

        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ة": "ه",
        "ى": "ي",
        "ؤ": "و",
        "ئ": "ي",
    }


    for old, new in replacements.items():

        text = text.replace(
            old,
            new
        )


    text = re.sub(
        r"[\u064B-\u065F]",
        "",
        text
    )


    text = re.sub(
        r"\s+",
        " ",
        text
    )


    return text.strip()


# =========================================================
# XPAND DETECTION
# =========================================================

def is_xpand_request(
    raw,
    agent_name
):

    text = normalize(
        (
            clean_text(
                raw,
                40000
            )
            +
            "\n"
            +
            clean_text(
                agent_name,
                1000
            )
        )
    )


    return (
        "xpand"
        in
        text
    )


# =========================================================
# DETECT LARGE LIVE CALL ARCHITECTURE REQUEST
#
# IMPORTANT:
#
# This check runs BEFORE unified-runtime detection.
#
# =========================================================

def is_xpand_live_call_architecture_request(
    raw,
    agent_name
):

    if not is_xpand_request(
        raw,
        agent_name
    ):

        return False


    text = normalize(
        raw
    )


    call_markers = [

        "live_call",
        "live call",
        "livecall",

        "مكالمه",
        "مكالمة",

        "الاتصال",
        "المكالمه",
        "المكالمة",
    ]


    architecture_markers = [

        # Browser/frontend
        "app.js",
        "browser",
        "frontend",
        "المتصفح",

        # WebSocket
        "websocket",
        "web socket",
        " ws ",
        "حزمه ws",
        "حزمة ws",

        # Package/dependency
        "package.json",
        "dependency",
        "dependencies",
        "npm",

        # Gemini TTS
        "gemini tts",
        "iapetus",
        "gemini-3.1-flash-tts-preview",

        # Streaming/audio
        "streaming",
        "audio stream",
        "audio chunks",
        "audio chunk",
        "tts stream",

        # Realtime output
        "output_modalities",
        "output modalities",
        "text only",
        "text-only",

        # Interruption
        "interrupt",
        "interruption",
        "مقاطعه",
        "مقاطعة",

        # Audio playback
        "audio player",
        "تشغيل الصوت",
        "منع التداخل",
        "تداخل الصوت",
    ]


    has_call = any(
        marker in text
        for marker
        in call_markers
    )


    has_architecture = any(
        marker in text
        for marker
        in architecture_markers
    )


    return bool(
        has_call
        and
        has_architecture
    )


# =========================================================
# DETECT XPAND UNIFIED PROFILE REQUEST
# =========================================================

def is_xpand_unified_runtime_request(
    raw,
    agent_name
):

    if not is_xpand_request(
        raw,
        agent_name
    ):

        return False


    text = normalize(
        raw
    )


    # -----------------------------------------------------
    # Strong direct marker
    # -----------------------------------------------------

    if (
        "agent_runtime_admin_profile"
        in
        text
    ):

        return True


    system_markers = [

        "system prompt",
        "system_prompt",

        "سيستيم برومت",
        "سستيم برومت",
        "برومت",
    ]


    voice_markers = [

        "voice",
        "voice profile",

        "فويس",

        "صوت",
        "صوتيه",
        "صوتية",
    ]


    call_markers = [

        "live_call",
        "live call",

        "مكالمه",
        "مكالمة",

        "الاتصال",
    ]


    telegram_markers = [

        "telegram",

        "تلجرام",
        "تيليجرام",

        "رسائل صوتيه",
        "رسائل صوتية",
    ]


    provider_markers = [

        "provider",
        "model",
        "style",
        "voice profile",

        "موديل",
    ]


    has_system = any(
        marker in text
        for marker
        in system_markers
    )


    has_voice = any(
        marker in text
        for marker
        in voice_markers
    )


    has_call = any(
        marker in text
        for marker
        in call_markers
    )


    has_telegram = any(
        marker in text
        for marker
        in telegram_markers
    )


    has_provider = any(
        marker in text
        for marker
        in provider_markers
    )


    score = sum(
        [
            bool(
                has_system
            ),

            bool(
                has_voice
            ),

            bool(
                has_call
            ),

            bool(
                has_telegram
            ),

            bool(
                has_provider
            ),
        ]
    )


    return (
        score
        >=
        2
    )


# =========================================================
# VALIDATE FOCUSED FILES
# =========================================================

def validate_focused_files(
    wanted_files,
    context_name
):

    repository_paths = set(
        admin.github_tree()
    )


    if not repository_paths:

        raise RuntimeError(
            "GitHub repository tree is empty."
        )


    missing = [

        path
        for path
        in wanted_files

        if path not in repository_paths
    ]


    if missing:

        raise RuntimeError(
            (
                context_name
                +
                " files missing from repository: "
                +
                ", ".join(
                    missing
                )
            )
        )


    selected = []


    for path in wanted_files:

        if not admin.safe_code_path(
            path
        ):

            raise RuntimeError(
                (
                    "Focused path rejected by safe_code_path: "
                    +
                    path
                )
            )


        selected.append(
            path
        )


    return selected


# =========================================================
# LIVE CALL ARCHITECTURE SELECTOR
# =========================================================

def select_live_call_architecture_files():

    selected = validate_focused_files(

        XPAND_LIVE_CALL_ARCHITECTURE_FILES,

        "XPAND live-call architecture"
    )


    print("")

    print(
        "================================================"
    )

    print(
        " 🎧 XPAND LIVE CALL ARCHITECTURE CONTEXT"
    )

    print(
        "================================================"
    )

    print("")


    for path in selected:

        print(
            (
                "🎧 LIVE CALL FILE | "
                +
                path
            )
        )


    print("")

    print(
        (
            "✅ XPAND LIVE CALL FILES | "
            +
            ", ".join(
                selected
            )
        )
    )

    print("")


    return selected


# =========================================================
# UNIFIED RUNTIME SELECTOR
# =========================================================

def select_unified_runtime_files():

    selected = validate_focused_files(

        XPAND_UNIFIED_RUNTIME_FILES,

        "XPAND unified runtime"
    )


    print("")

    print(
        "================================================"
    )

    print(
        " 🎯 XPAND FOCUSED RUNTIME CONTEXT"
    )

    print(
        "================================================"
    )

    print("")


    for path in selected:

        print(
            (
                "🎯 FOCUSED FILE | "
                +
                path
            )
        )


    print("")

    print(
        (
            "✅ XPAND FOCUSED FILES | "
            +
            ", ".join(
                selected
            )
        )
    )

    print("")


    return selected


# =========================================================
# SMART FOCUSED SELECTOR
# =========================================================

def focused_choose_files_for_request(
    raw,
    agent_name
):

    # =====================================================
    # FIRST PRIORITY:
    # Large XPAND Live Call architecture changes.
    #
    # This is the fix that allows:
    #
    # server.js
    # app.js
    # package.json
    #
    # to appear together in one Pending.
    # =====================================================

    if is_xpand_live_call_architecture_request(
        raw,
        agent_name
    ):

        return (
            select_live_call_architecture_files()
        )


    # =====================================================
    # SECOND PRIORITY:
    # Existing XPAND unified profile/runtime.
    # =====================================================

    if is_xpand_unified_runtime_request(
        raw,
        agent_name
    ):

        return (
            select_unified_runtime_files()
        )


    # =====================================================
    # EVERYTHING ELSE:
    # Existing repository discovery.
    # =====================================================

    return ORIGINAL_RESILIENT_SELECTOR(
        raw,
        agent_name
    )


# =========================================================
# INSTALL
# =========================================================

def install_focused_admin():

    # -----------------------------------------------------
    # Install resilient layer:
    #
    # Gemini primary
    # OpenAI fallback
    # Strict JSON
    # retry/backoff
    # -----------------------------------------------------

    resilient.install_resilient_ai()


    # -----------------------------------------------------
    # Override repository selection only.
    # -----------------------------------------------------

    admin.choose_files_for_request = (
        focused_choose_files_for_request
    )


    # -----------------------------------------------------
    # Give multi-file architecture changes enough room.
    # -----------------------------------------------------

    admin.MAX_CODE_FILES = 8


    admin.MAX_REPO_CONTEXT_CHARS = (
        600000
    )


    print("")

    print(
        "================================================"
    )

    print(
        " KEMO ADMIN FOCUSED RUNTIME V1.1"
    )

    print(
        " XPAND RUNTIME + LIVE CALL ARCHITECTURE"
    )

    print(
        "================================================"
    )

    print("")


    print(
        "✅ Existing resilient AI: ACTIVE"
    )


    print(
        "✅ Gemini primary: ACTIVE"
    )


    print(
        "✅ OpenAI fallback: ACTIVE"
    )


    print(
        "✅ Strict JSON: ACTIVE"
    )


    print(
        "✅ XPAND unified runtime context: ACTIVE"
    )


    print(
        "✅ XPAND Live Call architecture context: ACTIVE"
    )


    print(
        "✅ Live Call server.js selectable"
    )


    print(
        "✅ Live Call app.js selectable"
    )


    print(
        "✅ Live Call package.json selectable"
    )


    print(
        "✅ Repository noise reduced"
    )


    print(
        "🔒 GitHub approval gate preserved"
    )


    print(
        "🔒 Automatic Commit: DISABLED"
    )


    print(
        "🔒 Production changes: DISABLED until approval"
    )


    print("")


    return True


# =========================================================
# MAIN
# =========================================================

def main():

    install_focused_admin()


    admin.main()


# =========================================================
# ENTRY
# =========================================================

if __name__ == "__main__":

    try:

        main()


    except KeyboardInterrupt:

        print("")

        print(
            "👋 Kemo Admin Focused Runtime stopped."
        )


    except Exception as error:

        print("")

        print(
            (
                "❌ Kemo Admin Focused Runtime failed | "
                +
                clean_text(
                    error,
                    3000
                )
            )
        )

        print("")

        raise
