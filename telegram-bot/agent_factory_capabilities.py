# =========================================================
# KEMO AGENT CAPABILITY ENGINE V1.0
#
# Dynamic capabilities for Kemo Agent Factory.
#
# Karim:
# "كيمو ضيف لـ XPAND Agent ميزة الفويس"
#
#            ↓
#
# Capability Registry
#            ↓
#
# Voice Capability installed
#            ↓
#
# XPAND receives Telegram voice
#            ↓
#
# STT -> General Agent AI -> TTS
#            ↓
#
# XPAND replies with Telegram Voice
#
#
# IMPORTANT:
# - agent_factory_runner.py stays untouched
# - existing Kemo stays untouched
# - websites/publisher stay untouched
# - child bot token is never stored
# - capabilities are persisted in Postgres
# - no fake feature verification
# =========================================================

import re
import json
import time
import uuid
import urllib.request
import urllib.error

import agent_factory_runner as factory
import main as kemo


# =========================================================
# VERSION
# =========================================================

VERSION = "1.0"


# =========================================================
# SETTINGS
# =========================================================

MAX_CHILD_VOICE_BYTES = 20 * 1024 * 1024

VOICE_CAPABILITY = "voice"

XPAND_AGENT_SLUG = "xpand"


# =========================================================
# EXISTING RUNTIME REFERENCES
# =========================================================

EXISTING_FACTORY_ASK = (
    kemo.ask_kemo
)


ORIGINAL_CHILD_MESSAGE_PROCESSOR = (
    factory.process_child_message
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


def now_iso():

    try:

        return kemo.now_iso()

    except Exception:

        from datetime import datetime

        return (
            datetime.utcnow()
            .isoformat()
            +
            "Z"
        )


def resolve_xpand_runtime_profile():
    profile = {
        "system_prompt": "",
        "provider": "",
        "model": "",
        "style": "",
        "voice_profile": "",
        "voice": "",
    }

    try:
        runtime = getattr(
            kemo,
            "agent_runtime_admin_profile",
            None
        )

        if callable(runtime):
            runtime = runtime(
                XPAND_AGENT_SLUG
            )
    except Exception:
        runtime = None

    if isinstance(
        runtime,
        dict
    ):
        profile["system_prompt"] = clean_text(
            runtime.get(
                "system_prompt"
            )
            or
            runtime.get(
                "systemPrompt"
            )
            or
            runtime.get(
                "system_prompt_md"
            ),
            50000
        )
        profile["provider"] = clean_text(
            runtime.get(
                "provider"
            ),
            100
        )
        profile["model"] = clean_text(
            runtime.get(
                "model"
            ),
            100
        )
        profile["style"] = clean_text(
            runtime.get(
                "style"
            ),
            2000
        )
        profile["voice_profile"] = clean_text(
            runtime.get(
                "voice_profile"
            )
            or
            runtime.get(
                "voiceProfile"
            ),
            2000
        )
        profile["voice"] = clean_text(
            runtime.get(
                "voice"
            ),
            100
        )

    return profile


# =========================================================
# CAPABILITY DATABASE
# =========================================================

def ensure_capability_tables():

    with factory.db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS
                kemo_agent_factory_capabilities
                (
                    agent_id TEXT NOT NULL,

                    capability TEXT NOT NULL,

                    enabled BOOLEAN NOT NULL
                        DEFAULT TRUE,

                    status TEXT NOT NULL
                        DEFAULT 'installed',

                    config JSONB NOT NULL
                        DEFAULT '{}'::jsonb,

                    installed_at TIMESTAMPTZ
                        NOT NULL
                        DEFAULT NOW(),

                    updated_at TIMESTAMPTZ
                        NOT NULL
                        DEFAULT NOW(),

                    verified_at TIMESTAMPTZ,

                    last_error TEXT,

                    PRIMARY KEY
                    (
                        agent_id,
                        capability
                    )
                );
                """
            )


            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_kemo_agent_capabilities_enabled

                ON kemo_agent_factory_capabilities
                (
                    agent_id,
                    enabled
                );
                """
            )


    print(
        "✅ Agent Capability database: READY"
    )


# =========================================================
# CAPABILITY STORAGE
# =========================================================

def install_capability(
    agent_id,
    capability,
    config=None
):

    if not isinstance(
        config,
        dict
    ):

        config = {}


    with factory.db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO
                kemo_agent_factory_capabilities
                (
                    agent_id,
                    capability,
                    enabled,
                    status,
                    config,
                    installed_at,
                    updated_at,
                    verified_at,
                    last_error
                )

                VALUES
                (
                    %s,
                    %s,
                    TRUE,
                    'installed',
                    %s::jsonb,
                    NOW(),
                    NOW(),
                    NULL,
                    NULL
                )

                ON CONFLICT
                (
                    agent_id,
                    capability
                )

                DO UPDATE SET
                    enabled = TRUE,
                    status = 'installed',
                    config = EXCLUDED.config,
                    updated_at = NOW(),
                    last_error = NULL;
                """,
                (
                    agent_id,
                    capability,
                    json.dumps(
                        config,
                        ensure_ascii=False
                    )
                )
            )


def capability_record(
    agent_id,
    capability
):

    with factory.db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    enabled,
                    status,
                    config,
                    verified_at,
                    last_error

                FROM
                    kemo_agent_factory_capabilities

                WHERE
                    agent_id = %s

                    AND capability = %s

                LIMIT 1;
                """,
                (
                    agent_id,
                    capability
                )
            )


            row = cur.fetchone()


    if not row:

        return None


    return {
        "enabled":
            bool(
                row[0]
            ),

        "status":
            clean_text(
                row[1],
                100
            ),

        "config":
            (
                row[2]
                if isinstance(
                    row[2],
                    dict
                )
                else
                {}
            ),

        "verifiedAt":
            row[3],

        "lastError":
            clean_text(
                row[4],
                2000
            )
    }


def capability_enabled(
    agent_id,
    capability
):

    record = capability_record(
        agent_id,
        capability
    )


    return bool(
        record
        and
        record.get(
            "enabled"
        )
    )


def mark_capability_verified(
    agent_id,
    capability
):

    existing = capability_record(
        agent_id,
        capability
    )


    already_verified = bool(
        existing
        and
        existing.get(
            "verifiedAt"
        )
    )


    with factory.db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE
                    kemo_agent_factory_capabilities

                SET
                    status = 'verified',
                    verified_at =
                        COALESCE(
                            verified_at,
                            NOW()
                        ),
                    updated_at = NOW(),
                    last_error = NULL

                WHERE
                    agent_id = %s

                    AND capability = %s;
                """,
                (
                    agent_id,
                    capability
                )
            )


    return not already_verified


def mark_capability_error(
    agent_id,
    capability,
    error
):

    with factory.db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE
                    kemo_agent_factory_capabilities

                SET
                    status = 'error',
                    last_error = %s,
                    updated_at = NOW()

                WHERE
                    agent_id = %s

                    AND capability = %s;
                """,
                (
                    clean_text(
                        error,
                        3000
                    ),
                    agent_id,
                    capability
                )
            )


# =========================================================
# AGENT LOOKUP
# =========================================================

def find_agent_for_request(
    owner_user_id,
    raw_request
):

    agents = factory.list_owner_agents(
        owner_user_id
    )


    if not agents:

        return None


    source = normalized(
        raw_request
    )


    best = None

    best_score = 0


    for agent in agents:

        status = clean_text(
            agent.get(
                "status"
            ),
            100
        ).lower()


        if status not in {
            "active",
            "worker_starting"
        }:

            continue


        agent_name = clean_text(
            agent.get(
                "agent_name"
            ),
            150
        )


        bot_username = clean_text(
            agent.get(
                "bot_username"
            ),
            150
        )


        score = 0


        normalized_name = normalized(
            agent_name
        )


        normalized_username = normalized(
            bot_username
        )


        if (
            normalized_name
            and
            normalized_name
            in source
        ):

            score += 100


        if (
            normalized_username
            and
            normalized_username
            in source
        ):

            score += 100


        words = [
            word
            for word in normalized_name.split()
            if len(
                word
            )
            >=
            3
            and
            word
            not in {
                "agent",
                "وكيل"
            }
        ]


        for word in words:

            if word in source:

                score += 20


        if score > best_score:

            best = agent

            best_score = score


    if best:

        return best


    active_agents = [
        agent
        for agent in agents
        if clean_text(
            agent.get(
                "status"
            ),
            100
        ).lower()
        ==
        "active"
    ]


    if len(
        active_agents
    ) == 1:

        return active_agents[
            0
        ]


    return None


# =========================================================
# FEATURE REQUEST DETECTOR
# =========================================================

FEATURE_ADD_MARKERS = [
    "ضيف ميزة",
    "اضف ميزة",
    "أضف ميزة",
    "ضيف خاصية",
    "اضف خاصية",
    "أضف خاصية",
    "ركب ميزة",
    "ركب خاصية",
    "فعل ميزة",
    "فعّل ميزة",
    "زود ميزة",
    "add feature",
    "add capability",
    "enable feature",
]


VOICE_MARKERS = [
    "فويس",
    "فوويس",
    "صوت",
    "صوتي",
    "رساله صوتيه",
    "رسالة صوتية",
    "يرد علي فويس",
    "يرد بصوت",
    "ابعث فويس",
    "ابعت فويس",
    "voice",
    "voice message",
    "speech",
]


def contains_marker(
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


def detect_capability_request(
    text
):

    raw = clean_text(
        text,
        5000
    )


    if not raw:

        return None


    if not contains_marker(
        raw,
        FEATURE_ADD_MARKERS
    ):

        return None


    if contains_marker(
        raw,
        VOICE_MARKERS
    ):

        return {
            "capability":
                VOICE_CAPABILITY
        }


    return {
        "capability":
            "unknown"
    }


# =========================================================
# VOICE ENGINE READINESS
# =========================================================

def voice_engine_readiness():

    checks = {
        "stt":
            callable(
                getattr(
                    kemo,
                    "transcribe_voice",
                    None
                )
            ),

        "tts":
            callable(
                getattr(
                    kemo,
                    "text_to_voice_ogg",
                    None
                )
            ),

        "childTelegram":
            callable(
                getattr(
                    factory,
                    "child_bot_request",
                    None
                )
            ),

        "generalAI":
            callable(
                getattr(
                    factory,
                    "general_agent_answer",
                    None
                )
            ),
    }


    return {
        "ready":
            all(
                checks.values()
            ),

        "checks":
            checks
    }


# =========================================================
# XPAND VOICE RUNTIME PROFILE
# =========================================================

def xpand_voice_runtime_settings():
    runtime = resolve_xpand_runtime_profile()
    fallback_profile = {
        "system_prompt": clean_text(
            getattr(
                kemo,
                "XPAND_SYSTEM_PROMPT",
                ""
            ),
            50000
        ),
        "voice_profile": "",
        "voice": "",
        "style": "",
    }

    return {
        "system_prompt": runtime.get(
            "system_prompt"
        )
        or fallback_profile["system_prompt"],
        "voice_profile": runtime.get(
            "voice_profile"
        )
        or fallback_profile["voice_profile"],
        "voice": runtime.get(
            "voice"
        )
        or fallback_profile["voice"],
        "style": runtime.get(
            "style"
        )
        or fallback_profile["style"],
        "provider": runtime.get(
            "provider"
        )
        or "openai",
        "model": runtime.get(
            "model"
        )
        or "",
    }


# =========================================================
# INSTALL VOICE CAPABILITY
# =========================================================

def install_voice_for_agent(
    agent
):

    readiness = voice_engine_readiness()


    if not readiness[
        "ready"
    ]:

        missing = [
            name
            for name, ready
            in readiness[
                "checks"
            ].items()
            if not ready
        ]


        raise RuntimeError(
            (
                "Voice engine components missing: "
                +
                ", ".join(
                    missing
                )
            )
        )


    agent_id = clean_text(
        agent.get(
            "id"
        ),
        200
    )


    if not agent_id:

        raise RuntimeError(
            "Agent ID missing"
        )


    xpand_profile = xpand_voice_runtime_settings()


    install_capability(
        agent_id,
        VOICE_CAPABILITY,
        {
            "input":
                "telegram_voice",

            "speechToText":
                "kemo.transcribe_voice",

            "replyMode":
                "voice_to_voice",

            "textToSpeech":
                "kemo.text_to_voice_ogg",

            "installedBy":
                "Kemo Agent Capability Engine",

            "engineVersion":
                VERSION,

            "xpandRuntime": {
                "system_prompt": xpand_profile["system_prompt"],
                "voice_profile": xpand_profile["voice_profile"],
                "provider": xpand_profile["provider"],
                "model": xpand_profile["model"],
                "voice": xpand_profile["voice"],
                "style": xpand_profile["style"],
            }
        }
    )


    proof = capability_record(
        agent_id,
        VOICE_CAPABILITY
    )


    if not (
        proof
        and
        proof.get(
            "enabled"
        )
    ):

        raise RuntimeError(
            "Voice capability was not persisted"
        )


    return proof


# =========================================================
# CHILD FILE DOWNLOAD
# =========================================================

def child_get_file_bytes(
    token,
    file_id
):

    info = factory.child_bot_request(
        token,
        "getFile",
        {
            "file_id":
                file_id
        },
        timeout=20
    )


    file_path = (
        info.get(
            "result",
            {}
        ).get(
            "file_path"
        )
    )


    if not file_path:

        raise RuntimeError(
            "Child Telegram file path missing"
        )


    url = (
        "https://api.telegram.org/"
        "file/bot"
        +
        token
        +
        "/"
        +
        file_path
    )


    request = urllib.request.Request(
        url,
        method="GET"
    )


    with urllib.request.urlopen(
        request,
        timeout=60
    ) as response:

        return response.read()


# =========================================================
# CHILD SEND VOICE
# =========================================================

def child_send_voice_bytes(
    token,
    chat_id,
    audio_bytes
):

    if not audio_bytes:

        raise RuntimeError(
            "Voice audio is empty"
        )


    boundary = (
        "----KemoAgent"
        +
        uuid.uuid4().hex
    )


    parts = []


    parts.append(
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="chat_id"\r\n\r\n'
            f"{chat_id}\r\n"
        ).encode(
            "utf-8"
        )
    )


    parts.append(
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="voice"; '
            f'filename="agent.ogg"\r\n'
            f"Content-Type: audio/ogg\r\n\r\n"
        ).encode(
            "utf-8"
        )
    )


    parts.append(
        audio_bytes
    )


    parts.append(
        b"\r\n"
    )


    parts.append(
        (
            f"--{boundary}--\r\n"
        ).encode(
            "utf-8"
        )
    )


    body = b"".join(
        parts
    )


    url = (
        "https://api.telegram.org/"
        "bot"
        +
        token
        +
        "/sendVoice"
    )


    request = urllib.request.Request(
        url,
        data=body,
        method="POST"
    )


    request.add_header(
        "Content-Type",
        (
            "multipart/form-data; "
            f"boundary={boundary}"
        )
    )


    with urllib.request.urlopen(
        request,
        timeout=120
    ) as response:

        raw = (
            response
            .read()
            .decode(
                "utf-8",
                errors="replace"
            )
        )


    result = json.loads(
        raw
    )


    if not result.get(
        "ok"
    ):

        raise RuntimeError(
            (
                "Child sendVoice failed: "
                +
                clean_text(
                    result,
                    1500
                )
            )
        )


    return result


# =========================================================
# CHILD VOICE PROCESSOR
# =========================================================

def process_child_voice(
    agent,
    token,
    message
):

    voice = message.get(
        "voice"
    )


    if not isinstance(
        voice,
        dict
    ):

        return


    agent_id = clean_text(
        agent.get(
            "id"
        ),
        200
    )


    chat = message.get(
        "chat",
        {}
    )


    from_user = message.get(
        "from",
        {}
    )


    chat_id = chat.get(
        "id"
    )


    user_id = from_user.get(
        "id"
    )


    if not chat_id:

        return


    file_size = (
        voice.get(
            "file_size",
            0
        )
        or
        0
    )


    if file_size > MAX_CHILD_VOICE_BYTES:

        factory.child_send_message(
            token,
            chat_id,
            "الفويس كبير زيادة، جرّب تسجيل أقصر."
        )

        return


    try:

        factory.child_bot_request(
            token,
            "sendChatAction",
            {
                "chat_id":
                    chat_id,

                "action":
                    "typing"
            },
            timeout=10
        )


    except Exception:

        pass


    try:

        audio_bytes = child_get_file_bytes(
            token,
            voice.get(
                "file_id"
            )
        )


        transcript = kemo.transcribe_voice(
            audio_bytes,
            voice.get(
                "mime_type"
            )
            or
            "audio/ogg"
        )


        transcript = clean_text(
            transcript,
            12000
        )


        if not transcript:

            raise RuntimeError(
                "Voice transcription was empty"
            )


        print(
            (
                "🎙️ CHILD VOICE | "
                +
                clean_text(
                    agent.get(
                        "agent_name"
                    ),
                    100
                )
                +
                " | "
                +
                transcript[:250]
            )
        )


        history = factory.get_agent_history(
            agent_id,
            chat_id
        )


        factory.save_agent_message(
            agent_id,
            chat_id,
            user_id,
            "user",
            transcript
        )


        answer = factory.general_agent_answer(
            agent,
            chat_id,
            transcript,
            history
        )


        answer = clean_text(
            answer,
            12000
        )


        factory.save_agent_message(
            agent_id,
            chat_id,
            user_id,
            "assistant",
            answer
        )


        try:

            factory.child_bot_request(
                token,
                "sendChatAction",
                {
                    "chat_id":
                        chat_id,

                    "action":
                        "record_voice"
                },
                timeout=10
            )


        except Exception:

            pass


        voice_reply = kemo.text_to_voice_ogg(
            answer
        )


        child_send_voice_bytes(
            token,
            chat_id,
            voice_reply
        )


        first_verified = mark_capability_verified(
            agent_id,
            VOICE_CAPABILITY
        )


        print(
            (
                "✅ CHILD VOICE VERIFIED | "
                +
                clean_text(
                    agent.get(
                        "agent_name"
                    ),
                    100
                )
            )
        )


        if first_verified:

            try:

                factory.manager_send_message(
                    agent.get(
                        "owner_chat_id"
                    ),
                    (
                        "✅ ميزة Voice على "
                        +
                        clean_text(
                            agent.get(
                                "agent_name"
                            ),
                            100
                        )
                        +
                        " تم التحقق منها فعليًا.\n\n"
                        "🎙️ استقبل Voice حقيقي\n"
                        "✅ تم تحويله لنص\n"
                        "🧠 تم توليد الرد\n"
                        "🔊 تم إرسال Voice حقيقي من الوكيل"
                    )
                )


            except Exception as error:

                print(
                    (
                        "⚠️ Voice verification notification: "
                        +
                        str(
                            error
                        )
                    )
                )


    except Exception as error:

        print(
            (
                "❌ CHILD VOICE ERROR | "
                +
                str(
                    error
                )
            )
        )


        mark_capability_error(
            agent_id,
            VOICE_CAPABILITY,
            error
        )


        try:

            factory.child_send_message(
                token,
                chat_id,
                (
                    "صار خلل مؤقت بالفويس. "
                    "جرّب التسجيل مرة ثانية."
                )
            )


        except Exception:

            pass


# =========================================================
# PATCH CHILD MESSAGE PROCESSOR
# =========================================================

def process_child_message_with_capabilities(
    agent,
    token,
    message
):

    if not isinstance(
        message,
        dict
    ):

        return


    voice = message.get(
        "voice"
    )


    if voice:

        agent_id = clean_text(
            agent.get(
                "id"
            ),
            200
        )


        if not capability_enabled(
            agent_id,
            VOICE_CAPABILITY
        ):

            chat_id = (
                message
                .get(
                    "chat",
                    {}
                )
                .get(
                    "id"
                )
            )


            if chat_id:

                factory.child_send_message(
                    token,
                    chat_id,
                    (
                        "ميزة الفويس مش مفعّلة عندي حالياً."
                    )
                )


            return


        return process_child_voice(
            agent,
            token,
            message
        )


    return ORIGINAL_CHILD_MESSAGE_PROCESSOR(
        agent,
        token,
        message
    )


# =========================================================
# CAPABILITY COMMAND HANDLER
# =========================================================

def handle_capability_request(
    chat_id,
    user_id,
    text
):

    request = detect_capability_request(
        text
    )


    if not request:

        return None


    if (
        user_id
        !=
        factory.allowed_owner_user_id()
    ):

        return (
            "تعديل ميزات الوكلاء متاح لصاحب Kemo فقط."
        )


    capability = request.get(
        "capability"
    )


    agent = find_agent_for_request(
        user_id,
        text
    )


    if not agent:

        return (
            "فهمت إنك بدك تضيف ميزة لوكيل، "
            "بس ما قدرت أحدد أي Agent تقصد."
        )


    agent_name = clean_text(
        agent.get(
            "agent_name"
        ),
        150
    )


    if capability == VOICE_CAPABILITY:

        try:

            proof = install_voice_for_agent(
                agent
            )


            return (
                "✅ ركبت ميزة Voice فعليًا على "
                +
                agent_name
                +
                ".\n\n"
                "🎙️ Voice Input: ENABLED\n"
                "🧠 Speech-to-Text: READY\n"
                "🔊 Voice Reply: ENABLED\n"
                "💾 Capability Registry: VERIFIED\n\n"
                "الحالة: الميزة مركبة ومفعلة، "
                "لكن ما رح أعتبرها مجرّبة 100% قبل اختبار حقيقي.\n\n"
                "ابعث هسّا Voice للوكيل؛ "
                "إذا استلمه ورد عليك Voice، "
                "رح أوثقها تلقائيًا كـ VERIFIED."
            )


        except Exception as error:

            print(
                (
                    "❌ Voice capability install: "
                    +
                    str(
                        error
                    )
                )
            )


            return (
                "❌ ما قدرت أركب ميزة Voice على "
                +
                agent_name
                +
                ".\n"
                "السبب: "
                +
                clean_text(
                    error,
                    1000
                )
            )


    return (
        "فهمت طلب إضافة الميزة، "
        "لكن هاي Capability لسه مش موجودة بالمكتبة."
    )


# =========================================================
# WRAP KEMO
# =========================================================

def ask_kemo_with_capabilities(
    chat_id,
    user_id,
    user_message
):

    try:

        capability_answer = handle_capability_request(
            chat_id,
            user_id,
            user_message
        )


    except Exception as error:

        print(
            (
                "❌ Capability router: "
                +
                str(
                    error
                )
            )
        )


        capability_answer = (
            "صار خلل بمحرك ميزات الوكلاء. "
            "ما رح أدّعي إن الميزة تركبت قبل التحقق."
        )


    if capability_answer is not None:

        try:

            kemo.save_message(
                chat_id,
                "assistant",
                capability_answer
            )


        except Exception:

            pass


        return capability_answer


    return EXISTING_FACTORY_ASK(
        chat_id,
        user_id,
        user_message
    )


# =========================================================
# INSTALL ENGINE
# =========================================================

factory.process_child_message = (
    process_child_message_with_capabilities
)


kemo.ask_kemo = (
    ask_kemo_with_capabilities
)


# =========================================================
# STARTUP CHECKS
# =========================================================

def verify_voice_engine():

    readiness = voice_engine_readiness()


    print(
        (
            "✅ STT engine: "
            +
            (
                "READY"
                if readiness[
                    "checks"
                ][
                    "stt"
                ]
                else
                "MISSING"
            )
        )
    )


    print(
        (
            "✅ TTS engine: "
            +
            (
                "READY"
                if readiness[
                    "checks"
                ][
                    "tts"
                ]
                else
                "MISSING"
            )
        )
    )


    if not readiness[
        "ready"
    ]:

        raise RuntimeError(
            "Voice capability engine is incomplete"
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
        " KEMO AGENT CAPABILITY ENGINE V1.0"
    )
    print(
        " DYNAMIC AGENT FEATURES"
    )
    print(
        "=============================================="
    )
    print("")

    print(
        "✅ Agent Factory preserved"
    )

    print(
        "✅ Dynamic Capability Registry"
    )

    print(
        "✅ Voice capability installer"
    )

    print(
        "✅ Voice -> STT"
    )

    print(
        "✅ STT -> General Agent AI"
    )

    print(
        "✅ AI -> TTS"
    )

    print(
        "✅ TTS -> Telegram Voice"
    )

    print(
        "✅ Real voice verification"
    )

    print(
        "✅ Capability persistence"
    )

    print(
        "🚫 No fake feature verification"
    )

    print("")


# =========================================================
# MAIN
# =========================================================

def main():

    print_header()


    ensure_capability_tables()


    verify_voice_engine()


    print(
        "✅ CHILD VOICE HANDLER PATCHED"
    )


    print(
        "✅ CAPABILITY ENGINE ONLINE"
    )


    print(
        "➡️ Starting Agent Factory..."
    )


    print("")


    factory.main()


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    try:

        main()


    except KeyboardInterrupt:

        print("")
        print(
            "👋 Kemo Agent Capability Engine stopped."
        )


    except Exception as error:

        print("")
        print(
            (
                "❌ Capability Engine startup failed: "
                +
                str(
                    error
                )
            )
        )
        print("")

        raise
