# =========================================================
# KEMO AGENT FACTORY - AI POLICY ENFORCEMENT V1.0
#
# PURPOSE
# ---------------------------------------------------------
# Make agents/xpand/ai.json the authoritative AI policy
# for XPAND.
#
# GUARANTEE FOR XPAND:
#
#   General chat reasoning      -> OpenAI
#   Voice reasoning             -> OpenAI
#   Future capability reasoning -> OpenAI Gateway
#
# Gemini is allowed for XPAND ONLY where ai.json explicitly
# defines a non-reasoning role such as:
#
#   STT -> speech_to_text_only
#   TTS -> text_to_speech_only
#
# KEMO:
#
#   Existing Gemini runtime is untouched.
#
# IMPORTANT:
#
# This module fails CLOSED for XPAND reasoning.
# If OpenAI fails, XPAND does NOT silently fall back
# to Gemini.
#
# =========================================================


import os
import json
import threading
from pathlib import Path


# =========================================================
# EXISTING VERIFIED PROVIDER STACK
# =========================================================

import agent_factory_ai_providers as providers


factory = providers.factory
profiles = providers.profiles
commands = providers.commands
capabilities = providers.capabilities
kemo = providers.kemo


VERSION = "1.0"


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(
    __file__
).resolve().parent


XPAND_DIR = (
    BASE_DIR
    /
    "agents"
    /
    "xpand"
)


XPAND_AI_POLICY_FILE = (
    XPAND_DIR
    /
    "ai.json"
)


XPAND_AGENT_FILE = (
    XPAND_DIR
    /
    "agent.json"
)


XPAND_CAPABILITIES_FILE = (
    XPAND_DIR
    /
    "capabilities.json"
)


XPAND_SYSTEM_PROMPT_FILE = (
    XPAND_DIR
    /
    "system_prompt.md"
)


# =========================================================
# CACHE
# =========================================================

_policy_cache = {
    "mtime": None,
    "data": None,
}


_policy_lock = threading.RLock()


# =========================================================
# HELPERS
# =========================================================

def clean_text(
    value,
    max_length=10000
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


def normalize_agent_id(
    value
):
    return (
        clean_text(
            value,
            300
        )
        .lower()
        .replace(
            "@",
            ""
        )
        .replace(
            "_",
            "-"
        )
        .replace(
            " ",
            "-"
        )
    )


def read_json(
    path
):
    if not path.exists():

        raise RuntimeError(
            (
                "Required policy file missing: "
                +
                str(
                    path
                )
            )
        )

    try:

        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except Exception as error:

        raise RuntimeError(
            (
                "Invalid JSON in "
                +
                path.name
                +
                ": "
                +
                clean_text(
                    error,
                    1000
                )
            )
        )

    if not isinstance(
        data,
        dict
    ):

        raise RuntimeError(
            (
                path.name
                +
                " must contain a JSON object."
            )
        )

    return data


# =========================================================
# LOAD XPAND AI POLICY
# =========================================================

def load_xpand_ai_policy(
    force=False
):
    with _policy_lock:

        if not XPAND_AI_POLICY_FILE.exists():

            raise RuntimeError(
                (
                    "XPAND AI policy missing: "
                    +
                    str(
                        XPAND_AI_POLICY_FILE
                    )
                )
            )

        stat = XPAND_AI_POLICY_FILE.stat()

        mtime = stat.st_mtime_ns

        if (
            not force
            and
            _policy_cache[
                "data"
            ]
            is not None
            and
            _policy_cache[
                "mtime"
            ]
            ==
            mtime
        ):

            return _policy_cache[
                "data"
            ]

        data = read_json(
            XPAND_AI_POLICY_FILE
        )

        _policy_cache[
            "mtime"
        ] = mtime

        _policy_cache[
            "data"
        ] = data

        return data


# =========================================================
# POLICY ACCESSORS
# =========================================================

def xpand_primary_provider():
    policy = load_xpand_ai_policy()

    provider = (
        policy.get(
            "provider"
        )
        or
        {}
    )

    return clean_text(
        provider.get(
            "primary"
        ),
        100
    ).lower()


def xpand_policy_model():
    policy = load_xpand_ai_policy()

    provider = (
        policy.get(
            "provider"
        )
        or
        {}
    )

    return clean_text(
        provider.get(
            "model"
        ),
        300
    )


def xpand_runtime_model():

    return clean_text(
        os.getenv(
            "XPAND_OPENAI_MODEL"
        )
        or
        getattr(
            providers,
            "XPAND_OPENAI_MODEL",
            ""
        ),
        300
    )


def xpand_openai_key_ready():

    return bool(
        clean_text(
            os.getenv(
                "XPAND_OPENAI_API_KEY"
            )
            or
            getattr(
                providers,
                "XPAND_OPENAI_API_KEY",
                ""
            ),
            10000
        )
    )


def xpand_routing_policy():
    policy = load_xpand_ai_policy()

    value = policy.get(
        "routing_policy"
    )

    return (
        value
        if isinstance(
            value,
            dict
        )
        else
        {}
    )


def xpand_voice_policy():
    policy = load_xpand_ai_policy()

    value = policy.get(
        "voice_pipeline"
    )

    return (
        value
        if isinstance(
            value,
            dict
        )
        else
        {}
    )


def xpand_future_capability_policy():
    policy = load_xpand_ai_policy()

    value = policy.get(
        "future_capability_policy"
    )

    return (
        value
        if isinstance(
            value,
            dict
        )
        else
        {}
    )


# =========================================================
# STRICT XPAND POLICY VALIDATION
# =========================================================

def validate_xpand_ai_policy():

    policy = load_xpand_ai_policy(
        force=True
    )

    errors = []

    agent_id = clean_text(
        policy.get(
            "agent_id"
        ),
        100
    ).lower()

    if agent_id != "xpand":

        errors.append(
            (
                "ai.json agent_id must be xpand; got "
                +
                repr(
                    agent_id
                )
            )
        )

    provider = (
        policy.get(
            "provider"
        )
        or
        {}
    )

    primary = clean_text(
        provider.get(
            "primary"
        ),
        100
    ).lower()

    if primary != "openai":

        errors.append(
            (
                "XPAND primary provider must be openai; got "
                +
                repr(
                    primary
                )
            )
        )

    policy_model = clean_text(
        provider.get(
            "model"
        ),
        300
    )

    if not policy_model:

        errors.append(
            "XPAND OpenAI model missing from ai.json."
        )

    runtime_model = xpand_runtime_model()

    if not runtime_model:

        errors.append(
            "XPAND_OPENAI_MODEL is missing."
        )

    elif (
        policy_model
        and
        runtime_model
        !=
        policy_model
    ):

        errors.append(
            (
                "XPAND model mismatch: ai.json="
                +
                policy_model
                +
                " ENV="
                +
                runtime_model
            )
        )

    if not xpand_openai_key_ready():

        errors.append(
            "XPAND_OPENAI_API_KEY is missing."
        )

    routing = xpand_routing_policy()

    if (
        clean_text(
            routing.get(
                "all_agent_reasoning"
            ),
            100
        ).lower()
        !=
        "openai"
    ):

        errors.append(
            (
                "all_agent_reasoning must be openai."
            )
        )

    if (
        routing.get(
            "all_new_capabilities_inherit_provider"
        )
        is not True
    ):

        errors.append(
            (
                "all_new_capabilities_inherit_provider "
                "must be true."
            )
        )

    if (
        routing.get(
            "capabilities_must_use_agent_ai_gateway"
        )
        is not True
    ):

        errors.append(
            (
                "capabilities_must_use_agent_ai_gateway "
                "must be true."
            )
        )

    if (
        routing.get(
            "allow_direct_gemini_reasoning"
        )
        is not False
    ):

        errors.append(
            (
                "allow_direct_gemini_reasoning "
                "must be false."
            )
        )

    if (
        routing.get(
            "allow_silent_provider_fallback"
        )
        is not False
    ):

        errors.append(
            (
                "allow_silent_provider_fallback "
                "must be false."
            )
        )

    fallback_provider = routing.get(
        "fallback_provider"
    )

    if fallback_provider not in {
        None,
        "",
    }:

        errors.append(
            (
                "fallback_provider must be null."
            )
        )

    voice = xpand_voice_policy()

    voice_reasoning = (
        voice.get(
            "reasoning"
        )
        or
        {}
    )

    if (
        clean_text(
            voice_reasoning.get(
                "provider"
            ),
            100
        ).lower()
        !=
        "openai"
    ):

        errors.append(
            (
                "XPAND voice reasoning provider "
                "must be openai."
            )
        )

    voice_reasoning_model = clean_text(
        voice_reasoning.get(
            "model"
        ),
        300
    )

    if (
        policy_model
        and
        voice_reasoning_model
        !=
        policy_model
    ):

        errors.append(
            (
                "XPAND voice reasoning model must match "
                "primary OpenAI model."
            )
        )

    stt = (
        voice.get(
            "stt"
        )
        or
        {}
    )

    tts = (
        voice.get(
            "tts"
        )
        or
        {}
    )

    if (
        clean_text(
            stt.get(
                "provider"
            ),
            100
        ).lower()
        ==
        "gemini"
    ):

        if (
            clean_text(
                stt.get(
                    "role"
                ),
                100
            ).lower()
            !=
            "speech_to_text_only"
        ):

            errors.append(
                (
                    "Gemini STT is allowed only with "
                    "speech_to_text_only role."
                )
            )

    if (
        clean_text(
            tts.get(
                "provider"
            ),
            100
        ).lower()
        ==
        "gemini"
    ):

        if (
            clean_text(
                tts.get(
                    "role"
                ),
                100
            ).lower()
            !=
            "text_to_speech_only"
        ):

            errors.append(
                (
                    "Gemini TTS is allowed only with "
                    "text_to_speech_only role."
                )
            )

    return {
        "ok":
            not errors,

        "errors":
            errors,

        "policy":
            policy,

        "provider":
            primary,

        "model":
            policy_model,

        "runtimeModel":
            runtime_model,
    }


# =========================================================
# FAIL-CLOSED POLICY CHECK
# =========================================================

def require_xpand_openai_policy(
    capability_name="general_chat"
):

    validation = validate_xpand_ai_policy()

    if not validation[
        "ok"
    ]:

        raise RuntimeError(
            (
                "XPAND AI policy violation: "
                +
                " | ".join(
                    validation[
                        "errors"
                    ]
                )
            )
        )

    capability_name = clean_text(
        capability_name,
        200
    ).lower()

    future_policy = (
        xpand_future_capability_policy()
    )

    configured_route = clean_text(
        future_policy.get(
            capability_name
        ),
        200
    ).lower()

    # If capability is specifically declared,
    # it must point to OpenAI reasoning.

    if (
        configured_route
        and
        configured_route
        !=
        "openai_reasoning"
    ):

        raise RuntimeError(
            (
                "XPAND capability "
                +
                capability_name
                +
                " is not allowed to use "
                "non-OpenAI reasoning."
            )
        )

    return {
        "ok":
            True,

        "agentId":
            "xpand",

        "provider":
            validation[
                "provider"
            ],

        "model":
            validation[
                "model"
            ],

        "capability":
            capability_name,
    }


# =========================================================
# GENERIC AGENT POLICY LOOKUP
#
# This is the function future capabilities should use.
# =========================================================

def get_agent_ai_policy(
    agent_id
):

    normalized = normalize_agent_id(
        agent_id
    )

    if normalized in {
        "xpand",
        "xpand-agent",
        "xpand-ihabbot",
    }:

        validation = (
            validate_xpand_ai_policy()
        )

        return {
            "agentId":
                "xpand",

            "provider":
                validation[
                    "provider"
                ],

            "model":
                validation[
                    "model"
                ],

            "valid":
                validation[
                    "ok"
                ],

            "errors":
                validation[
                    "errors"
                ],
        }

    # Kemo is intentionally not routed through
    # XPAND's policy layer.

    if normalized in {
        "kemo",
        "mykemobot",
    }:

        return {
            "agentId":
                "kemo",

            "provider":
                "existing_kemo_runtime",

            "model":
                None,

            "valid":
                True,

            "errors":
                [],
        }

    return {
        "agentId":
            normalized,

        "provider":
            None,

        "model":
            None,

        "valid":
            False,

        "errors": [
            (
                "No explicit AI policy registered "
                "for this agent."
            )
        ],
    }


# =========================================================
# XPAND REASONING GATEWAY
#
# ALL FUTURE XPAND CAPABILITIES SHOULD CALL:
#
#   agent_ai_reason(
#       agent_id="xpand",
#       capability_name="crm",
#       user_message="..."
#   )
#
# instead of calling Gemini/OpenAI directly.
# =========================================================

def agent_ai_reason(
    agent_id,
    capability_name,
    user_message,
    *,
    history=None,
    user_id=None,
    extra_context=None
):

    normalized = normalize_agent_id(
        agent_id
    )

    capability_name = clean_text(
        capability_name
        or
        "general_chat",
        200
    ).lower()

    user_message = clean_text(
        user_message,
        20000
    )

    if not user_message:

        raise RuntimeError(
            "AI Gateway received an empty message."
        )

    # =====================================================
    # XPAND
    # =====================================================

    if normalized in {
        "xpand",
        "xpand-agent",
        "xpand-ihabbot",
    }:

        route = require_xpand_openai_policy(
            capability_name
        )

        conversation_history = (
            history
            if isinstance(
                history,
                list
            )
            else
            []
        )

        if (
            not conversation_history
            and
            user_id
        ):

            try:

                conversation_history = (
                    providers
                    .load_recent_xpand_history(
                        user_id=user_id,
                        limit=24
                    )
                )

            except Exception as error:

                print(
                    (
                        "⚠️ XPAND AI Gateway memory skipped | "
                        +
                        clean_text(
                            error,
                            700
                        )
                    )
                )

                conversation_history = []

        final_message = user_message

        if extra_context:

            final_message = (
                clean_text(
                    extra_context,
                    12000
                )
                +
                "\n\n"
                +
                user_message
            )

        print(
            (
                "🧠 AGENT AI GATEWAY | "
                "XPAND | "
                +
                capability_name
                +
                " | OPENAI | "
                +
                route[
                    "model"
                ]
            )
        )

        answer = providers.call_xpand_openai(
            final_message,
            conversation_history
        )

        print(
            (
                "✅ AGENT AI GATEWAY RESPONSE | "
                "XPAND | "
                +
                capability_name
                +
                " | OPENAI | "
                +
                route[
                    "model"
                ]
            )
        )

        return answer

    # =====================================================
    # KEMO
    #
    # We deliberately do not reroute Kemo here.
    # =====================================================

    if normalized in {
        "kemo",
        "mykemobot",
    }:

        raise RuntimeError(
            (
                "Kemo must use its existing runtime. "
                "XPAND AI Gateway does not replace "
                "Kemo's Gemini stack."
            )
        )

    # =====================================================
    # UNKNOWN AGENT
    #
    # Fail closed until that agent gets its own ai.json.
    # =====================================================

    raise RuntimeError(
        (
            "Agent "
            +
            normalized
            +
            " has no registered AI provider policy."
        )
    )


# =========================================================
# PROVIDER ASSERTION FOR CAPABILITY INSTALLERS
#
# Future installers can call:
#
#   enforce_capability_ai("xpand", "crm")
#
# before installing reasoning-dependent capability.
# =========================================================

def enforce_capability_ai(
    agent_id,
    capability_name
):

    normalized = normalize_agent_id(
        agent_id
    )

    if normalized in {
        "xpand",
        "xpand-agent",
        "xpand-ihabbot",
    }:

        result = require_xpand_openai_policy(
            capability_name
        )

        return {
            "allowed":
                True,

            "agentId":
                "xpand",

            "capability":
                capability_name,

            "provider":
                "openai",

            "model":
                result[
                    "model"
                ],

            "gateway":
                "agent_ai_reason",
        }

    return {
        "allowed":
            False,

        "agentId":
            normalized,

        "capability":
            capability_name,

        "provider":
            None,

        "model":
            None,

        "gateway":
            None,

        "reason":
            (
                "No explicit capability AI policy "
                "registered for this agent."
            ),
    }


# =========================================================
# PRESERVE VERIFIED OPENAI FUNCTION
# =========================================================

ORIGINAL_OPENAI_CALL = (
    providers.call_xpand_openai
)


# =========================================================
# GUARDED OPENAI CALL
#
# Even if existing XPAND code calls call_xpand_openai()
# directly, policy gets checked first.
# =========================================================

def guarded_xpand_openai_call(
    current_message,
    history=None
):

    require_xpand_openai_policy(
        "general_chat"
    )

    return ORIGINAL_OPENAI_CALL(
        current_message,
        history
    )


# =========================================================
# PRESERVE VERIFIED PROVIDER ROUTER
# =========================================================

ORIGINAL_PROVIDER_ROUTER = (
    providers.provider_general_agent_answer
)


# =========================================================
# POLICY-WRAPPED GENERAL AGENT ROUTER
# =========================================================

def policy_general_agent_answer(
    *args,
    **kwargs
):

    try:

        is_xpand = (
            providers.is_xpand_agent_call(
                args,
                kwargs
            )
        )

    except Exception:

        is_xpand = False

    if is_xpand:

        try:

            policy = require_xpand_openai_policy(
                "general_chat"
            )

            print(
                (
                    "🔐 XPAND AI POLICY | OPENAI | "
                    +
                    policy[
                        "model"
                    ]
                )
            )

        except Exception as error:

            print(
                (
                    "❌ XPAND AI POLICY BLOCK | "
                    +
                    clean_text(
                        error,
                        1500
                    )
                )
            )

            # Fail closed.
            #
            # NEVER call the lower Gemini path.

            return (
                "صار خلل بإعداد محرك XPAND، "
                "فوقفت التحويل بدل ما أستخدم Gemini "
                "بالغلط. "
                "إعداد OpenAI لازم يتصلح أول."
            )

    return ORIGINAL_PROVIDER_ROUTER(
        *args,
        **kwargs
    )


# =========================================================
# ENFORCE NO GEMINI FALLBACK
# =========================================================

def enforce_no_xpand_gemini_fallback():

    routing = xpand_routing_policy()

    allow_fallback = (
        routing.get(
            "allow_silent_provider_fallback"
        )
        is True
    )

    direct_gemini = (
        routing.get(
            "allow_direct_gemini_reasoning"
        )
        is True
    )

    if (
        allow_fallback
        or
        direct_gemini
    ):

        raise RuntimeError(
            (
                "XPAND ai.json unexpectedly allows "
                "Gemini reasoning/fallback."
            )
        )

    # The old provider router already supports this flag.
    # Force it OFF according to ai.json.

    providers.XPAND_ALLOW_GEMINI_FALLBACK = False

    return True


# =========================================================
# INSTALL POLICY
# =========================================================

def install_ai_policy():

    validation = validate_xpand_ai_policy()

    if not validation[
        "ok"
    ]:

        # Do NOT crash Kemo.
        #
        # Kemo must remain available even if XPAND policy
        # is temporarily invalid.

        print(
            (
                "❌ XPAND AI POLICY INVALID | "
                +
                " | ".join(
                    validation[
                        "errors"
                    ]
                )
            )
        )

    enforce_no_xpand_gemini_fallback()

    # First install the already verified provider router.

    providers.install_provider_router()

    # Guard direct OpenAI calls.

    providers.call_xpand_openai = (
        guarded_xpand_openai_call
    )

    # Put policy wrapper above the provider router.

    factory.general_agent_answer = (
        policy_general_agent_answer
    )

    # Keep all modules pointing to the policy-controlled
    # factory function.

    try:

        capabilities.factory.general_agent_answer = (
            policy_general_agent_answer
        )

    except Exception:

        pass

    try:

        commands.factory.general_agent_answer = (
            policy_general_agent_answer
        )

    except Exception:

        pass

    try:

        profiles.factory.general_agent_answer = (
            policy_general_agent_answer
        )

    except Exception:

        pass

    return validation


# =========================================================
# RUNTIME STATUS
# =========================================================

def runtime_status():

    validation = validate_xpand_ai_policy()

    voice = xpand_voice_policy()

    stt = (
        voice.get(
            "stt"
        )
        or
        {}
    )

    reasoning = (
        voice.get(
            "reasoning"
        )
        or
        {}
    )

    tts = (
        voice.get(
            "tts"
        )
        or
        {}
    )

    return {
        "version":
            VERSION,

        "agentId":
            "xpand",

        "policyValid":
            validation[
                "ok"
            ],

        "errors":
            validation[
                "errors"
            ],

        "primaryProvider":
            validation[
                "provider"
            ],

        "model":
            validation[
                "model"
            ],

        "runtimeModel":
            validation[
                "runtimeModel"
            ],

        "openaiKeyReady":
            xpand_openai_key_ready(),

        "geminiReasoningAllowed":
            False,

        "silentFallbackAllowed":
            False,

        "futureCapabilitiesUseGateway":
            True,

        "voice": {
            "sttProvider":
                clean_text(
                    stt.get(
                        "provider"
                    ),
                    100
                ),

            "sttRole":
                clean_text(
                    stt.get(
                        "role"
                    ),
                    100
                ),

            "reasoningProvider":
                clean_text(
                    reasoning.get(
                        "provider"
                    ),
                    100
                ),

            "reasoningModel":
                clean_text(
                    reasoning.get(
                        "model"
                    ),
                    300
                ),

            "ttsProvider":
                clean_text(
                    tts.get(
                        "provider"
                    ),
                    100
                ),

            "ttsRole":
                clean_text(
                    tts.get(
                        "role"
                    ),
                    100
                ),
        },
    }


# =========================================================
# STARTUP
# =========================================================

def main():

    validation = install_ai_policy()

    status = runtime_status()

    print("")

    print(
        "================================================"
    )

    print(
        " KEMO AGENT FACTORY AI POLICY V1.0"
    )

    print(
        " XPAND OPENAI ENFORCEMENT"
    )

    print(
        "================================================"
    )

    print("")

    print(
        (
            "✅ XPAND ai.json: "
            +
            (
                "VALID"
                if status[
                    "policyValid"
                ]
                else
                "INVALID"
            )
        )
    )

    print(
        (
            "✅ XPAND primary provider: "
            +
            clean_text(
                status[
                    "primaryProvider"
                ]
                or
                "MISSING"
            ).upper()
        )
    )

    print(
        (
            "✅ XPAND policy model: "
            +
            (
                status[
                    "model"
                ]
                or
                "MISSING"
            )
        )
    )

    print(
        (
            "✅ XPAND runtime model: "
            +
            (
                status[
                    "runtimeModel"
                ]
                or
                "MISSING"
            )
        )
    )

    print(
        (
            "✅ XPAND OpenAI key: "
            +
            (
                "READY"
                if status[
                    "openaiKeyReady"
                ]
                else
                "MISSING"
            )
        )
    )

    print(
        "✅ General chat reasoning -> OPENAI"
    )

    print(
        "✅ Voice reasoning -> OPENAI"
    )

    print(
        "✅ Future capability reasoning -> AGENT AI GATEWAY"
    )

    print(
        (
            "✅ Voice STT -> "
            +
            (
                status[
                    "voice"
                ][
                    "sttProvider"
                ]
                or
                "unknown"
            ).upper()
            +
            " (speech only)"
        )
    )

    print(
        (
            "✅ Voice AI Brain -> "
            +
            (
                status[
                    "voice"
                ][
                    "reasoningProvider"
                ]
                or
                "unknown"
            ).upper()
            +
            " | "
            +
            (
                status[
                    "voice"
                ][
                    "reasoningModel"
                ]
                or
                "unknown"
            )
        )
    )

    print(
        (
            "✅ Voice TTS -> "
            +
            (
                status[
                    "voice"
                ][
                    "ttsProvider"
                ]
                or
                "unknown"
            ).upper()
            +
            " (speech only)"
        )
    )

    print(
        "🚫 XPAND direct Gemini reasoning: BLOCKED"
    )

    print(
        "🚫 XPAND silent Gemini fallback: BLOCKED"
    )

    print(
        "🔒 Kemo Gemini runtime: UNCHANGED"
    )

    print(
        "🔒 Kemo memory remains isolated"
    )

    print(
        "🔒 XPAND OpenAI key remains ENV ONLY"
    )

    if not validation[
        "ok"
    ]:

        for error in validation[
            "errors"
        ]:

            print(
                (
                    "❌ POLICY ERROR | "
                    +
                    error
                )
            )

    print("")

    print(
        "✅ XPAND AI POLICY GATE ONLINE"
    )

    print("")

    # IMPORTANT:
    #
    # Do NOT call providers.main() here because that would
    # reinstall its router above this policy wrapper.
    #
    # Start the lower existing stack directly instead.

    providers.call_stack.main()


# =========================================================
# ENTRY
# =========================================================

if __name__ == "__main__":

    main()
