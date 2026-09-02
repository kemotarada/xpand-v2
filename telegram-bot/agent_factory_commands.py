# =========================================================
# KEMO AGENT FACTORY NATURAL COMMANDS V1.1
#
# Understand natural Karim commands such as:
#
# كيمو ضيف لـ XPAND Agent ميزة الفويس
# كيمو خلي XPAND يرد علي فويس
# كيمو ركب الصوت على XPAND
# كيمو بدي XPAND يستقبل ويرد فويس
#
# IMPORTANT:
# - No fake "working"
# - No fake "installing"
# - Feature is considered INSTALLED only after DB persistence
# - Feature is considered VERIFIED only after real use
# =========================================================

import re

import agent_factory_capabilities as capabilities
import main as kemo


# =========================================================
# VERSION
# =========================================================

VERSION = "1.1"


# =========================================================
# EXISTING STACK
# =========================================================

EXISTING_KEMO_ASK = (
    kemo.ask_kemo
)


# =========================================================
# HELPERS
# =========================================================

def clean_text(
    value,
    limit=5000
):

    return (
        str(
            value
            if value is not None
            else ""
        )
        .replace(
            "\x00",
            ""
        )
        .strip()[:limit]
    )


def normalized(
    value
):

    try:

        return kemo.normalize_text(
            value
        )

    except Exception:

        text = clean_text(
            value,
            5000
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
            r"\s+",
            " ",
            text
        )

        return text.strip()


# =========================================================
# NATURAL FEATURE LANGUAGE
# =========================================================

FEATURE_ACTION_MARKERS = [
    "ضيف",
    "اضف",
    "أضف",
    "ركب",
    "ركّب",
    "فعل",
    "فعّل",
    "زود",
    "زوّد",
    "خلي",
    "خلّي",
    "بدي",
    "اجعل",
    "add",
    "enable",
    "install",
]


VOICE_MARKERS = [
    "فويس",
    "فوويس",
    "صوت",
    "صوتي",
    "صوتية",
    "صوتيه",
    "رسالة صوتية",
    "رساله صوتيه",
    "يرد فويس",
    "يرد علي فويس",
    "يرد بصوت",
    "يستقبل فويس",
    "ابعثله فويس",
    "ابعتله فويس",
    "voice",
    "voice message",
    "speech",
    "audio",
]


AGENT_CONTEXT_MARKERS = [
    "agent",
    "وكيل",
]


def contains_any(
    text,
    markers
):

    source = normalized(
        text
    )

    for marker in markers:

        if normalized(
            marker
        ) in source:

            return True

    return False


# =========================================================
# ROBUST VOICE FEATURE DETECTION
# =========================================================

def detect_voice_feature_request(
    text
):

    raw = clean_text(
        text,
        5000
    )

    if not raw:

        return False


    has_voice = contains_any(
        raw,
        VOICE_MARKERS
    )


    if not has_voice:

        return False


    has_action = contains_any(
        raw,
        FEATURE_ACTION_MARKERS
    )


    has_agent_context = contains_any(
        raw,
        AGENT_CONTEXT_MARKERS
    )


    # Accept natural phrases like:
    #
    # "ضيف لـ XPAND Agent ميزة الفويس"
    # "خلي XPAND يرد علي فويس"
    # "بدي XPAND يستقبل فويس ويرد فويس"
    #
    return bool(
        has_voice
        and
        has_action
        and
        has_agent_context
    )


# =========================================================
# VOICE INSTALL COMMAND
# =========================================================

def handle_natural_voice_command(
    chat_id,
    user_id,
    raw
):

    if (
        user_id
        !=
        capabilities.factory.allowed_owner_user_id()
    ):

        return (
            "تعديل ميزات الوكلاء متاح لصاحب Kemo فقط."
        )


    agent = capabilities.find_agent_for_request(
        user_id,
        raw
    )


    if not agent:

        return (
            "فهمت إنك بدك تضيف Voice لوكيل، "
            "بس ما قدرت أحدد أي Agent تقصد."
        )


    agent_id = clean_text(
        agent.get(
            "id"
        ),
        200
    )


    agent_name = clean_text(
        agent.get(
            "agent_name"
        )
        or
        "Agent",
        150
    )


    username = clean_text(
        agent.get(
            "bot_username"
        ),
        150
    )


    existing = capabilities.capability_record(
        agent_id,
        capabilities.VOICE_CAPABILITY
    )


    # =====================================================
    # ALREADY VERIFIED
    # =====================================================

    if (
        existing
        and
        existing.get(
            "enabled"
        )
        and
        existing.get(
            "verifiedAt"
        )
    ):

        return (
            "✅ ميزة Voice موجودة ومتحقق منها فعليًا على "
            +
            agent_name
            +
            ".\n\n"
            +
            (
                "🤖 @"
                +
                username
                +
                "\n"
                if username
                else
                ""
            )
            +
            "🎙️ Voice Input: VERIFIED\n"
            "🧠 Speech-to-Text: VERIFIED\n"
            "🔊 Voice Reply: VERIFIED"
        )


    # =====================================================
    # ALREADY INSTALLED BUT NOT TESTED
    # =====================================================

    if (
        existing
        and
        existing.get(
            "enabled"
        )
    ):

        return (
            "✅ ميزة Voice مركبة أصلًا على "
            +
            agent_name
            +
            ".\n\n"
            "لكن لسه ما عندي اختبار Voice حقيقي ناجح "
            "يثبتها 100%.\n\n"
            +
            (
                "افتح @"
                +
                username
                +
                " وابعتله Voice الآن."
                if username
                else
                "ابعث للوكيل Voice الآن."
            )
        )


    # =====================================================
    # REAL INSTALLATION
    # =====================================================

    readiness = capabilities.voice_engine_readiness()


    if not readiness.get(
        "ready"
    ):

        missing = [
            key
            for key, value
            in readiness.get(
                "checks",
                {}
            ).items()
            if not value
        ]


        return (
            "❌ ما قدرت أركب Voice على "
            +
            agent_name
            +
            ".\n\n"
            "في مكونات ناقصة فعليًا: "
            +
            ", ".join(
                missing
            )
        )


    try:

        proof = capabilities.install_voice_for_agent(
            agent
        )


    except Exception as error:

        return (
            "❌ فشل تركيب Voice على "
            +
            agent_name
            +
            ".\n\n"
            "السبب: "
            +
            clean_text(
                error,
                1200
            )
        )


    # =====================================================
    # VERIFY DATABASE PERSISTENCE
    # =====================================================

    saved = capabilities.capability_record(
        agent_id,
        capabilities.VOICE_CAPABILITY
    )


    if not (
        saved
        and
        saved.get(
            "enabled"
        )
    ):

        return (
            "❌ حاولت أركب Voice على "
            +
            agent_name
            +
            " لكن قاعدة البيانات ما أكدت التفعيل.\n\n"
            "الحالة: غير مفعلة."
        )


    return (
        "✅ ركبت ميزة Voice فعليًا على "
        +
        agent_name
        +
        ".\n\n"
        +
        (
            "🤖 @"
            +
            username
            +
            "\n"
            if username
            else
            ""
        )
        +
        "🎙️ Voice Input: ENABLED\n"
        "🧠 Speech-to-Text: READY\n"
        "🔊 Voice Reply: ENABLED\n"
        "💾 Capability Registry: VERIFIED\n\n"
        "الحالة: الميزة مركبة فعليًا، "
        "لكن مش رح أعتبرها VERIFIED 100% قبل تجربة حقيقية.\n\n"
        "ابعث هسّا Voice للوكيل. "
        "إذا استلمه ورد عليك Voice، "
        "رح تتسجل الميزة تلقائيًا كـ VERIFIED."
    )


# =========================================================
# NATURAL COMMAND ROUTER
# =========================================================

def handle_natural_agent_command(
    chat_id,
    user_id,
    text
):

    raw = clean_text(
        text,
        5000
    )


    if not raw:

        return None


    if detect_voice_feature_request(
        raw
    ):

        return handle_natural_voice_command(
            chat_id,
            user_id,
            raw
        )


    return None


# =========================================================
# KEMO WRAPPER
# =========================================================

def ask_kemo_with_natural_agent_commands(
    chat_id,
    user_id,
    user_message
):

    try:

        answer = handle_natural_agent_command(
            chat_id,
            user_id,
            user_message
        )


    except Exception as error:

        print(
            (
                "❌ Natural Agent Command Router: "
                +
                str(
                    error
                )
            )
        )


        answer = (
            "صار خلل بتنفيذ أمر الوكيل. "
            "ما رح أقول إن الميزة تركبت قبل ما أتأكد."
        )


    if answer is not None:

        try:

            kemo.save_message(
                chat_id,
                "assistant",
                answer
            )

        except Exception:

            pass


        return answer


    return EXISTING_KEMO_ASK(
        chat_id,
        user_id,
        user_message
    )


# =========================================================
# INSTALL
# =========================================================

kemo.ask_kemo = (
    ask_kemo_with_natural_agent_commands
)


# =========================================================
# HEADER
# =========================================================

def print_header():

    print("")
    print(
        "=============================================="
    )
    print(
        " KEMO AGENT FACTORY COMMANDS V1.1"
    )
    print(
        " NATURAL LANGUAGE FEATURE CONTROL"
    )
    print(
        "=============================================="
    )
    print("")

    print(
        "✅ Natural agent feature commands"
    )

    print(
        "✅ Agent name can appear anywhere in command"
    )

    print(
        "✅ XPAND voice request detection"
    )

    print(
        "✅ Real capability installation"
    )

    print(
        "✅ Database persistence verification"
    )

    print(
        "✅ Real-use verification required"
    )

    print(
        "🚫 No fake 'working on it'"
    )

    print(
        "🚫 No fake feature activation"
    )

    print("")


# =========================================================
# MAIN
# =========================================================

def main():

    print_header()


    print(
        "✅ NATURAL COMMAND ROUTER ONLINE"
    )

    print(
        "➡️ Starting Capability Engine..."
    )

    print("")


    capabilities.main()


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    main()
