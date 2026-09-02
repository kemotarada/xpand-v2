# =========================================================
# KEMO ADMIN RESILIENT AI V1.1
#
# FIXES
# ---------------------------------------------------------
# 1. Gemini remains primary.
# 2. OpenAI automatic fallback.
# 3. OpenAI uses STRICT Structured Outputs / JSON Schema.
# 4. No more free-form JSON parsing failures.
# 5. Repository scanner searches REAL FILE CONTENT
#    to discover XPAND Telegram voice handler.
# 6. agent_factory_profiles.py and live_call/server.js
#    are forced into XPAND central-profile requests.
# 7. Existing approval / GitHub protections are preserved.
#
# =========================================================


import os
import json
import time
import re
import urllib.request
import urllib.error

import agent_factory_admin as admin


# =========================================================
# VERSION
# =========================================================

VERSION = "1.1"


# =========================================================
# ORIGINAL ADMIN FUNCTIONS
# =========================================================

ORIGINAL_GEMINI_FACTORY_AI_JSON = (
    admin.factory_ai_json
)


# =========================================================
# OPENAI CONFIG
# =========================================================

OPENAI_ADMIN_API_KEY = str(
    os.getenv(
        "KEMO_ADMIN_OPENAI_API_KEY",
        ""
    )
).strip()


OPENAI_ADMIN_MODEL = str(
    os.getenv(
        "KEMO_ADMIN_OPENAI_MODEL",
        "gpt-5.4-mini"
    )
).strip()


OPENAI_RESPONSES_URL = (
    "https://api.openai.com/v1/responses"
)


OPENAI_TIMEOUT_SECONDS = max(
    60,
    int(
        os.getenv(
            "KEMO_ADMIN_OPENAI_TIMEOUT_SECONDS",
            "240"
        )
        or
        240
    )
)


OPENAI_MAX_CODE_OUTPUT_TOKENS = max(
    12000,
    int(
        os.getenv(
            "KEMO_ADMIN_OPENAI_MAX_OUTPUT_TOKENS",
            "30000"
        )
        or
        30000
    )
)


# =========================================================
# DISCOVERY CONFIG
# =========================================================

MAX_DISCOVERY_READ_FILES = 20

MAX_SELECTED_FILES = 8


SOURCE_EXTENSIONS = (
    ".py",
    ".js",
    ".mjs",
    ".cjs",
    ".ts",
    ".tsx",
    ".json",
)


# =========================================================
# HELPERS
# =========================================================

def clean_text(
    value,
    max_length=5000
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

    return re.sub(
        r"\s+",
        " ",
        clean_text(
            value,
            200000
        ).lower()
    ).strip()


# =========================================================
# DETECT ADMIN AI TASK
#
# agent_factory_admin uses factory_ai_json() mainly for:
#
# A) file planner:
#       {"paths": [...], "reason": "..."}
#
# B) code generator:
#       {"summary": "...", "files": [...]}
#
# =========================================================

def detect_task_kind(
    system_instruction
):

    text = normalize(
        system_instruction
    )


    if (
        '"paths"'
        in
        text

        or

        (
            "select"
            in
            text
            and
            "existing"
            in
            text
            and
            "files"
            in
            text
        )
    ):

        return "planner"


    return "code"


# =========================================================
# STRICT OPENAI SCHEMAS
# =========================================================

def planner_schema():

    return {

        "type":
            "object",

        "properties": {

            "paths": {

                "type":
                    "array",

                "items": {

                    "type":
                        "string"
                }
            },

            "reason": {

                "type":
                    "string"
            }
        },

        "required": [
            "paths",
            "reason"
        ],

        "additionalProperties":
            False
    }


def code_schema():

    return {

        "type":
            "object",

        "properties": {

            "summary": {

                "type":
                    "string"
            },

            "files": {

                "type":
                    "array",

                "items": {

                    "type":
                        "object",

                    "properties": {

                        "path": {

                            "type":
                                "string"
                        },

                        "content": {

                            "type":
                                "string"
                        }
                    },

                    "required": [
                        "path",
                        "content"
                    ],

                    "additionalProperties":
                        False
                }
            }
        },

        "required": [
            "summary",
            "files"
        ],

        "additionalProperties":
            False
    }


# =========================================================
# OPENAI RESPONSE TEXT
# =========================================================

def extract_openai_output_text(
    data
):

    if not isinstance(
        data,
        dict
    ):

        return ""


    direct = data.get(
        "output_text"
    )


    if isinstance(
        direct,
        str
    ):

        direct = direct.strip()


        if direct:

            return direct


    pieces = []


    for item in (
        data.get(
            "output"
        )
        or
        []
    ):

        if not isinstance(
            item,
            dict
        ):

            continue


        content_list = (
            item.get(
                "content"
            )
            or
            []
        )


        for content in content_list:

            if not isinstance(
                content,
                dict
            ):

                continue


            content_type = clean_text(
                content.get(
                    "type"
                ),
                100
            )


            if content_type not in {
                "output_text",
                "text",
            }:

                continue


            text = content.get(
                "text"
            )


            if isinstance(
                text,
                str
            ):

                pieces.append(
                    text
                )


    return "\n".join(
        pieces
    ).strip()


# =========================================================
# OPENAI ERROR
# =========================================================

def parse_openai_error(
    raw,
    status
):

    try:

        data = json.loads(
            raw.decode(
                "utf-8",
                errors="replace"
            )
        )


        error = (
            data.get(
                "error"
            )
            or
            {}
        )


        message = (
            error.get(
                "message"
            )
            or
            data.get(
                "message"
            )
            or
            ""
        )


        code = (
            error.get(
                "code"
            )
            or
            error.get(
                "type"
            )
            or
            ""
        )


        result = (
            "OpenAI HTTP "
            +
            str(
                status
            )
        )


        if code:

            result += (
                " | "
                +
                clean_text(
                    code,
                    200
                )
            )


        if message:

            result += (
                " | "
                +
                clean_text(
                    message,
                    1500
                )
            )


        return result


    except Exception:

        return (
            "OpenAI HTTP "
            +
            str(
                status
            )
            +
            " | "
            +
            clean_text(
                raw.decode(
                    "utf-8",
                    errors="replace"
                ),
                1500
            )
        )


# =========================================================
# OPENAI STRICT STRUCTURED OUTPUT
# =========================================================

def openai_factory_ai_json(
    system_instruction,
    user_prompt
):

    if not OPENAI_ADMIN_API_KEY:

        raise RuntimeError(
            "KEMO_ADMIN_OPENAI_API_KEY is missing."
        )


    task_kind = detect_task_kind(
        system_instruction
    )


    if task_kind == "planner":

        schema_name = (
            "kemo_repository_file_plan"
        )


        schema = planner_schema()


        max_output_tokens = 5000


    else:

        schema_name = (
            "kemo_full_file_code_change"
        )


        schema = code_schema()


        max_output_tokens = (
            OPENAI_MAX_CODE_OUTPUT_TOKENS
        )


    payload = {

        "model":
            OPENAI_ADMIN_MODEL,

        "instructions":
            str(
                system_instruction
                or
                ""
            ),

        "input": [
            {
                "role":
                    "user",

                "content":
                    str(
                        user_prompt
                        or
                        ""
                    )
            }
        ],

        "store":
            False,

        "max_output_tokens":
            max_output_tokens,

        "text": {

            "format": {

                "type":
                    "json_schema",

                "name":
                    schema_name,

                "strict":
                    True,

                "schema":
                    schema
            }
        }
    }


    body = json.dumps(
        payload,
        ensure_ascii=False
    ).encode(
        "utf-8"
    )


    request = urllib.request.Request(
        OPENAI_RESPONSES_URL,
        data=body,
        method="POST",
        headers={
            "Authorization":
                (
                    "Bearer "
                    +
                    OPENAI_ADMIN_API_KEY
                ),

            "Content-Type":
                "application/json",

            "Accept":
                "application/json",

            "User-Agent":
                (
                    "Kemo-Agent-Admin-Resilient/"
                    +
                    VERSION
                ),
        }
    )


    try:

        with urllib.request.urlopen(
            request,
            timeout=OPENAI_TIMEOUT_SECONDS
        ) as response:

            raw = response.read()


    except urllib.error.HTTPError as error:

        raw = error.read()


        raise RuntimeError(
            parse_openai_error(
                raw,
                error.code
            )
        )


    except urllib.error.URLError as error:

        raise RuntimeError(
            (
                "OpenAI network error: "
                +
                clean_text(
                    getattr(
                        error,
                        "reason",
                        error
                    ),
                    1200
                )
            )
        )


    except Exception as error:

        raise RuntimeError(
            (
                "OpenAI request failed: "
                +
                clean_text(
                    error,
                    1200
                )
            )
        )


    try:

        data = json.loads(
            raw.decode(
                "utf-8"
            )
        )


    except Exception as error:

        raise RuntimeError(
            (
                "OpenAI returned invalid HTTP JSON: "
                +
                clean_text(
                    error,
                    800
                )
            )
        )


    if data.get(
        "error"
    ):

        raise RuntimeError(
            (
                "OpenAI response error: "
                +
                clean_text(
                    data.get(
                        "error"
                    ),
                    1800
                )
            )
        )


    status = clean_text(
        data.get(
            "status"
        ),
        100
    )


    if status == "incomplete":

        incomplete_details = (
            data.get(
                "incomplete_details"
            )
            or
            {}
        )


        raise RuntimeError(
            (
                "OpenAI response incomplete"
                +
                " | "
                +
                clean_text(
                    incomplete_details,
                    1000
                )
            )
        )


    output_text = (
        extract_openai_output_text(
            data
        )
    )


    if not output_text:

        raise RuntimeError(
            (
                "OpenAI returned no structured output text"
                +
                (
                    " | status="
                    +
                    status
                    if status
                    else
                    ""
                )
            )
        )


    try:

        result = json.loads(
            output_text
        )


    except Exception:

        # Extra safety only.
        result = (
            admin.extract_json_object(
                output_text
            )
        )


    if not isinstance(
        result,
        dict
    ):

        raise RuntimeError(
            "OpenAI structured output was not an object."
        )


    print(
        (
            "✅ ADMIN AI | OPENAI STRICT JSON"
            +
            " | task="
            +
            task_kind
            +
            " | model="
            +
            OPENAI_ADMIN_MODEL
        )
    )


    return result


# =========================================================
# RESILIENT AI PROVIDER
# =========================================================

def resilient_factory_ai_json(
    system_instruction,
    user_prompt
):

    errors = []


    # -----------------------------------------------------
    # GEMINI PRIMARY
    #
    # Existing Gemini function already rotates its models.
    # -----------------------------------------------------

    try:

        print(
            "🧠 ADMIN AI | GEMINI PRIMARY"
        )


        return (
            ORIGINAL_GEMINI_FACTORY_AI_JSON(
                system_instruction,
                user_prompt
            )
        )


    except Exception as error:

        message = clean_text(
            error,
            2000
        )


        errors.append(
            (
                "Gemini: "
                +
                message
            )
        )


        print(
            (
                "⚠️ ADMIN AI GEMINI FAILED | "
                +
                message
            )
        )


    # -----------------------------------------------------
    # OPENAI FALLBACK
    # -----------------------------------------------------

    if OPENAI_ADMIN_API_KEY:

        try:

            print(
                (
                    "🧠 ADMIN AI | OPENAI FALLBACK"
                    +
                    " | model="
                    +
                    OPENAI_ADMIN_MODEL
                )
            )


            return openai_factory_ai_json(
                system_instruction,
                user_prompt
            )


        except Exception as error:

            message = clean_text(
                error,
                2000
            )


            errors.append(
                (
                    "OpenAI: "
                    +
                    message
                )
            )


            print(
                (
                    "⚠️ ADMIN AI OPENAI FAILED | "
                    +
                    message
                )
            )


    else:

        errors.append(
            "OpenAI fallback key missing."
        )


    # -----------------------------------------------------
    # SHORT BACKOFF
    # -----------------------------------------------------

    delay_seconds = 5


    print(
        (
            "⏳ ADMIN AI RETRY BACKOFF | "
            +
            str(
                delay_seconds
            )
            +
            "s"
        )
    )


    time.sleep(
        delay_seconds
    )


    # -----------------------------------------------------
    # SECOND OPENAI ATTEMPT FIRST
    #
    # If Gemini is overloaded, don't hammer it immediately.
    # -----------------------------------------------------

    if OPENAI_ADMIN_API_KEY:

        try:

            print(
                (
                    "🧠 ADMIN AI | OPENAI RETRY"
                    +
                    " | model="
                    +
                    OPENAI_ADMIN_MODEL
                )
            )


            return openai_factory_ai_json(
                system_instruction,
                user_prompt
            )


        except Exception as error:

            message = clean_text(
                error,
                2000
            )


            errors.append(
                (
                    "OpenAI retry: "
                    +
                    message
                )
            )


            print(
                (
                    "⚠️ ADMIN AI OPENAI RETRY FAILED | "
                    +
                    message
                )
            )


    # -----------------------------------------------------
    # LAST GEMINI ATTEMPT
    # -----------------------------------------------------

    try:

        print(
            "🧠 ADMIN AI | GEMINI FINAL RETRY"
        )


        return (
            ORIGINAL_GEMINI_FACTORY_AI_JSON(
                system_instruction,
                user_prompt
            )
        )


    except Exception as error:

        message = clean_text(
            error,
            2000
        )


        errors.append(
            (
                "Gemini retry: "
                +
                message
            )
        )


    raise RuntimeError(
        (
            "All Kemo Admin AI providers failed.\n"
            +
            "\n".join(
                errors[-4:]
            )
        )
    )


# =========================================================
# REPOSITORY DISCOVERY
#
# Previous version let the AI choose from FILE NAMES only.
#
# This version reads likely source files and searches their
# actual CONTENT for:
#
# - XPAND
# - Telegram
# - voice
# - TTS
# - sendVoice / send_voice
# - audio
#
# =========================================================

PATH_KEYWORDS = {

    "xpand":
        16,

    "voice":
        16,

    "tts":
        16,

    "audio":
        12,

    "telegram":
        12,

    "profile":
        8,

    "provider":
        8,

    "factory":
        5,

    "main.py":
        8,

    "runner":
        3,
}


CONTENT_MARKERS = {

    "sendvoice":
        40,

    "send_voice":
        40,

    "send_audio":
        35,

    "voice_message":
        35,

    "voice reply":
        30,

    "tts":
        24,

    "text_to_speech":
        24,

    "text-to-speech":
        24,

    "generate_voice":
        24,

    "speech":
        12,

    "telegram":
        10,

    "xpand":
        14,

    "ask_xpand":
        20,

    "audio":
        10,

    "voice":
        12,

    "sendmessage":
        5,

    "send_message":
        5,
}


# =========================================================
# PATH SCORE
# =========================================================

def path_score(
    path
):

    lower = path.lower()


    if not lower.endswith(
        SOURCE_EXTENSIONS
    ):

        return -1000


    score = 0


    for marker, weight in (
        PATH_KEYWORDS.items()
    ):

        if marker in lower:

            score += weight


    # Known central files from current project.

    known_bonus = {

        "agent_factory_profiles.py":
            30,

        "agent_factory_ai_providers.py":
            18,

        "agent_factory_runner.py":
            12,

        "agent_factory_commands.py":
            10,

        "main.py":
            18,

        "agent_factory_openai_call_provisioner.py":
            12,

        "agent_factory_call_provisioner.py":
            10,
    }


    score += known_bonus.get(
        path,
        0
    )


    return score


# =========================================================
# CONTENT SCORE
# =========================================================

def content_score(
    path,
    content
):

    text = str(
        content
        or
        ""
    ).lower()


    score = path_score(
        path
    )


    for marker, weight in (
        CONTENT_MARKERS.items()
    ):

        if marker in text:

            score += weight


    # Strong combinations.

    if (
        "xpand"
        in
        text

        and

        "voice"
        in
        text
    ):

        score += 35


    if (
        "telegram"
        in
        text

        and

        "voice"
        in
        text
    ):

        score += 40


    if (
        "xpand"
        in
        text

        and

        "telegram"
        in
        text
    ):

        score += 25


    if (
        "sendvoice"
        in
        text

        or

        "send_voice"
        in
        text
    ):

        score += 60


    return score


# =========================================================
# CANDIDATE FILES
# =========================================================

def repository_voice_candidates(
    paths
):

    ranked = []


    for path in paths:

        score = path_score(
            path
        )


        if score < 0:

            continue


        ranked.append(
            (
                score,
                path
            )
        )


    ranked.sort(
        key=lambda item: (
            -item[0],
            item[1]
        )
    )


    candidates = [
        path
        for _score, path
        in ranked[
            :MAX_DISCOVERY_READ_FILES
        ]
    ]


    # Force a few generic central files into inspection
    # even if filenames don't say "voice".

    for known in [

        "main.py",

        "agent_factory_profiles.py",

        "agent_factory_ai_providers.py",

        "agent_factory_runner.py",

        "agent_factory_commands.py",
    ]:

        if (
            known
            in
            paths

            and

            known
            not in
            candidates
        ):

            candidates.append(
                known
            )


    return candidates[
        :MAX_DISCOVERY_READ_FILES
    ]


# =========================================================
# SMART FILE SELECTION
# =========================================================

def smart_choose_files_for_request(
    raw,
    agent_name
):

    paths = admin.github_tree()


    if not paths:

        raise RuntimeError(
            "GitHub repository tree is empty."
        )


    selected = []


    # =====================================================
    # MANDATORY CENTRAL XPAND FILES
    # =====================================================

    mandatory = [

        "agent_factory_profiles.py",

        "agent_templates/live_call/server.js",
    ]


    for path in mandatory:

        if (
            path
            in
            paths

            and

            admin.safe_code_path(
                path
            )

            and

            path
            not in
            selected
        ):

            selected.append(
                path
            )


    # =====================================================
    # READ LIKELY FILES
    # =====================================================

    scored = []


    candidates = repository_voice_candidates(
        paths
    )


    print(
        (
            "🔎 ADMIN REPO DISCOVERY | candidates="
            +
            str(
                len(
                    candidates
                )
            )
        )
    )


    for path in candidates:

        if path in selected:

            continue


        try:

            file_data = (
                admin.github_get_file(
                    path
                )
            )


            score = content_score(
                path,
                file_data.get(
                    "content"
                )
            )


            scored.append(
                (
                    score,
                    path
                )
            )


            if score >= 50:

                print(
                    (
                        "🔎 VOICE CANDIDATE | score="
                        +
                        str(
                            score
                        )
                        +
                        " | "
                        +
                        path
                    )
                )


        except Exception as error:

            print(
                (
                    "⚠️ Repo discovery skipped | "
                    +
                    path
                    +
                    " | "
                    +
                    clean_text(
                        error,
                        500
                    )
                )
            )


    scored.sort(
        key=lambda item: (
            -item[0],
            item[1]
        )
    )


    # =====================================================
    # ADD TOP ACTUAL CONTENT MATCHES
    # =====================================================

    for score, path in scored:

        if len(
            selected
        ) >= MAX_SELECTED_FILES:

            break


        if score <= 0:

            continue


        if path in selected:

            continue


        selected.append(
            path
        )


    # =====================================================
    # SAFETY
    # =====================================================

    if not selected:

        raise RuntimeError(
            "Could not discover safe repository files."
        )


    print(
        (
            "✅ SMART SELECTED FILES | "
            +
            ", ".join(
                selected
            )
        )
    )


    return selected


# =========================================================
# INSTALL PATCHES
# =========================================================

def install_resilient_ai():

    # -----------------------------------------------------
    # AI fallback
    # -----------------------------------------------------

    admin.factory_ai_json = (
        resilient_factory_ai_json
    )


    # -----------------------------------------------------
    # Repository content discovery
    # -----------------------------------------------------

    admin.choose_files_for_request = (
        smart_choose_files_for_request
    )


    # -----------------------------------------------------
    # Give central multi-file request enough room.
    # -----------------------------------------------------

    admin.MAX_CODE_FILES = (
        MAX_SELECTED_FILES
    )


    admin.MAX_REPO_CONTEXT_CHARS = (
        260000
    )


    print("")

    print(
        "================================================"
    )

    print(
        " KEMO ADMIN RESILIENT AI V1.1"
    )

    print(
        " STRICT JSON + REPOSITORY DISCOVERY"
    )

    print(
        "================================================"
    )

    print("")


    print(
        "✅ Gemini primary coding engine"
    )


    print(
        (
            "✅ OpenAI fallback: "
            +
            (
                "READY"
                if OPENAI_ADMIN_API_KEY
                else
                "MISSING"
            )
        )
    )


    print(
        (
            "✅ OpenAI admin model: "
            +
            OPENAI_ADMIN_MODEL
        )
    )


    print(
        "✅ OpenAI Structured Outputs: STRICT JSON SCHEMA"
    )


    print(
        "✅ Planner JSON schema"
    )


    print(
        "✅ Full-file code JSON schema"
    )


    print(
        "✅ Repository content scanner"
    )


    print(
        "✅ Telegram voice handler discovery"
    )


    print(
        "✅ XPAND central profile file forced"
    )


    print(
        "✅ XPAND live_call/server.js forced"
    )


    print(
        "✅ Gemini 500/503 failover"
    )


    print(
        "✅ Retry/backoff enabled"
    )


    print(
        "🔒 Existing GitHub approval protection preserved"
    )


    print(
        "🔒 No automatic Commit"
    )


    print("")


# =========================================================
# MAIN
# =========================================================

def main():

    install_resilient_ai()


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
            "👋 Kemo Admin Resilient AI stopped."
        )


    except Exception as error:

        print("")

        print(
            (
                "❌ Kemo Admin Resilient startup failed | "
                +
                clean_text(
                    error,
                    3000
                )
            )
        )

        print("")

        raise
