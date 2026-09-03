# =========================================================
# XPAND AGENT FACTORY - AI PROVIDER ROUTER V1.0
#
# PURPOSE
# ---------------------------------------------------------
# Per-agent AI provider routing.
#
# Current policy:
#
#   Kemo  -> existing Gemini runtime (UNCHANGED)
#   XPAND -> OpenAI Responses API
#
# This file DOES NOT:
# - modify Kemo's Gemini configuration
# - replace Kemo's ask_kemo()
# - remove XPAND voice
# - remove XPAND memory
# - delete XPAND Gemini key
# - store OpenAI secrets in Git
#
# XPAND Gemini key may remain present for rollback,
# but it is NOT used as an automatic fallback by default.
#
# Real verification required:
# - successful XPAND text response
# - successful XPAND voice response
#
# =========================================================


import os
import re
import json
import inspect
import urllib.request
import urllib.error

from pathlib import Path


# =========================================================
# LOAD COMPLETE EXISTING STACK
#
# call provisioner imports:
# profiles -> commands -> capabilities -> factory -> Kemo
# =========================================================

import agent_factory_call_provisioner as call_stack


factory = call_stack.factory
profiles = call_stack.profiles
commands = call_stack.commands
capabilities = call_stack.capabilities
kemo = call_stack.kemo


# =========================================================
# VERSION
# =========================================================

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


XPAND_AGENT_JSON = (
    XPAND_DIR
    /
    "agent.json"
)


XPAND_CAPABILITIES_JSON = (
    XPAND_DIR
    /
    "capabilities.json"
)


XPAND_SYSTEM_PROMPT = (
    XPAND_DIR
    /
    "system_prompt.md"
)


# =========================================================
# OPENAI CONFIG
# =========================================================

XPAND_OPENAI_API_KEY = str(
    os.getenv(
        "XPAND_OPENAI_API_KEY",
        ""
    )
).strip()


XPAND_OPENAI_MODEL = str(
    os.getenv(
        "XPAND_OPENAI_MODEL",
        "gpt-5.6-terra"
    )
).strip()


XPAND_OPENAI_TIMEOUT_SECONDS = max(
    15,
    int(
        os.getenv(
            "XPAND_OPENAI_TIMEOUT_SECONDS",
            "90"
        )
        or
        "90"
    )
)


XPAND_OPENAI_MAX_OUTPUT_TOKENS = max(
    200,
    int(
        os.getenv(
            "XPAND_OPENAI_MAX_OUTPUT_TOKENS",
            "1800"
        )
        or
        "1800"
    )
)


# ---------------------------------------------------------
# IMPORTANT
#
# false = XPAND will NOT silently use Gemini if OpenAI fails.
#
# This preserves clear provider isolation.
# ---------------------------------------------------------

XPAND_ALLOW_GEMINI_FALLBACK = (
    str(
        os.getenv(
            "XPAND_ALLOW_GEMINI_FALLBACK",
            "false"
        )
    )
    .strip()
    .lower()
    in {
        "1",
        "true",
        "yes",
        "on",
    }
)


OPENAI_RESPONSES_URL = (
    "https://api.openai.com/v1/responses"
)


# =========================================================
# TEXT HELPERS
# =========================================================

def clean_text(
    value,
    max_length=12000
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


def normalize_text(
    value
):
    text = clean_text(
        value,
        10000
    ).lower()

    text = (
        text
        .replace(
            "أ",
            "ا"
        )
        .replace(
            "إ",
            "ا"
        )
        .replace(
            "آ",
            "ا"
        )
        .replace(
            "ة",
            "ه"
        )
        .replace(
            "ى",
            "ي"
        )
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
# JSON HELPERS
# =========================================================

def load_json_file(
    path
):
    try:

        if not path.exists():
            return {}

        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        if isinstance(
            data,
            dict
        ):
            return data

    except Exception as error:

        print(
            (
                "⚠️ AI Provider JSON | "
                +
                path.name
                +
                " | "
                +
                clean_text(
                    error,
                    500
                )
            )
        )

    return {}


def load_text_file(
    path
):
    try:

        if not path.exists():
            return ""

        return clean_text(
            path.read_text(
                encoding="utf-8"
            ),
            60000
        )

    except Exception as error:

        print(
            (
                "⚠️ AI Provider text | "
                +
                path.name
                +
                " | "
                +
                clean_text(
                    error,
                    500
                )
            )
        )

        return ""


# =========================================================
# XPAND PROFILE
# =========================================================

def load_xpand_profile():

    agent_json = load_json_file(
        XPAND_AGENT_JSON
    )

    capabilities_json = load_json_file(
        XPAND_CAPABILITIES_JSON
    )

    system_prompt = load_text_file(
        XPAND_SYSTEM_PROMPT
    )

    stc_prompt = load_text_file(
        XPAND_SYSTEM_PROMPT.parent / "stc_bank_system_prompt.md"
    )
    if stc_prompt:
        system_prompt = (
            system_prompt
            + "\n\nتعليمات STC Bank التالية هي الأحدث وتتقدم على أي قاعدة سابقة متعارضة:\n\n"
            + stc_prompt
        ).strip()

    name = clean_text(
        agent_json.get(
            "name"
        )
        or
        agent_json.get(
            "agent_name"
        )
        or
        "XPAND Agent",
        300
    )

    slug = clean_text(
        agent_json.get(
            "slug"
        )
        or
        agent_json.get(
            "agent_id"
        )
        or
        "xpand",
        100
    ).lower()

    telegram = (
        agent_json.get(
            "telegram"
        )
        or
        {}
    )

    username = clean_text(
        telegram.get(
            "username"
        )
        or
        agent_json.get(
            "telegram_username"
        )
        or
        "@XPAND_ihabBot",
        300
    )

    if (
        username
        and
        not username.startswith(
            "@"
        )
    ):
        username = (
            "@"
            +
            username
        )

    return {
        "name":
            name,

        "slug":
            slug,

        "username":
            username,

        "system_prompt":
            system_prompt,

        "agent_json":
            agent_json,

        "capabilities_json":
            capabilities_json,
    }


# =========================================================
# CAPABILITY SUMMARY
# =========================================================

def extract_enabled_capabilities(
    manifest
):
    if not isinstance(
        manifest,
        dict
    ):
        return []

    enabled = []

    # Different manifest layouts are supported.

    candidates = []

    if isinstance(
        manifest.get(
            "capabilities"
        ),
        dict
    ):
        candidates.append(
            manifest.get(
                "capabilities"
            )
        )

    candidates.append(
        manifest
    )

    seen = set()

    for container in candidates:

        if not isinstance(
            container,
            dict
        ):
            continue

        for (
            name,
            config
        ) in container.items():

            if not isinstance(
                config,
                dict
            ):
                continue

            is_enabled = (
                config.get(
                    "enabled"
                )
                is True
            )

            if not is_enabled:
                continue

            capability_name = clean_text(
                name,
                100
            )

            if (
                capability_name
                and
                capability_name
                not in seen
            ):
                enabled.append(
                    capability_name
                )

                seen.add(
                    capability_name
                )

    return enabled


# =========================================================
# XPAND IDENTIFIERS
# =========================================================

def xpand_identifiers():
    profile = load_xpand_profile()

    values = {
        "xpand",
        "xpand agent",
        "@xpand_ihabbot",
        "xpand_ihabbot",
    }

    for value in [
        profile.get(
            "slug"
        ),
        profile.get(
            "name"
        ),
        profile.get(
            "username"
        ),
    ]:

        normalized = normalize_text(
            value
        )

        if normalized:
            values.add(
                normalized
            )

            values.add(
                normalized.lstrip(
                    "@"
                )
            )

    return {
        item
        for item
        in values
        if item
    }


IDENTITY_KEYS = {
    "agent",
    "agent_id",
    "agent_name",
    "agent_slug",
    "slug",
    "name",
    "display_name",
    "bot",
    "bot_name",
    "bot_username",
    "telegram_username",
    "username",
    "managed_bot_username",
}


# =========================================================
# DEEP IDENTITY EXTRACTION
# =========================================================

def collect_identity_values(
    value,
    output=None,
    depth=0
):
    if output is None:
        output = set()

    if depth > 5:
        return output

    if isinstance(
        value,
        dict
    ):

        for (
            key,
            item
        ) in value.items():

            key_normalized = str(
                key
            ).strip().lower()

            if (
                key_normalized
                in IDENTITY_KEYS
            ):

                if isinstance(
                    item,
                    (
                        str,
                        int,
                    )
                ):

                    text = normalize_text(
                        item
                    )

                    if text:
                        output.add(
                            text
                        )

                        output.add(
                            text.lstrip(
                                "@"
                            )
                        )

            if isinstance(
                item,
                (
                    dict,
                    list,
                    tuple,
                )
            ):

                collect_identity_values(
                    item,
                    output,
                    depth + 1
                )

    elif isinstance(
        value,
        (
            list,
            tuple,
        )
    ):

        for item in value:

            collect_identity_values(
                item,
                output,
                depth + 1
            )

    return output


# =========================================================
# FUNCTION ARGUMENT BINDING
# =========================================================

ORIGINAL_GENERAL_AGENT_ANSWER = (
    factory.general_agent_answer
)


try:

    ORIGINAL_SIGNATURE = inspect.signature(
        ORIGINAL_GENERAL_AGENT_ANSWER
    )

except Exception:

    ORIGINAL_SIGNATURE = None


def bind_original_arguments(
    args,
    kwargs
):
    if ORIGINAL_SIGNATURE is None:
        return {}

    try:

        bound = ORIGINAL_SIGNATURE.bind_partial(
            *args,
            **kwargs
        )

        return dict(
            bound.arguments
        )

    except Exception:

        return {}


# =========================================================
# TARGET AGENT DETECTION
# =========================================================

def is_xpand_agent_call(
    args,
    kwargs
):
    bound = bind_original_arguments(
        args,
        kwargs
    )

    identities = set()

    # Prefer parameters whose names clearly describe
    # an agent or bot identity.

    for (
        name,
        value
    ) in bound.items():

        lowered = str(
            name
        ).lower()

        if (
            "agent"
            in lowered
            or
            "bot"
            in lowered
            or
            "profile"
            in lowered
        ):

            if isinstance(
                value,
                (
                    str,
                    int,
                )
            ):

                normalized = normalize_text(
                    value
                )

                if normalized:
                    identities.add(
                        normalized
                    )

                    identities.add(
                        normalized.lstrip(
                            "@"
                        )
                    )

            collect_identity_values(
                value,
                identities
            )

    # Also inspect structured arguments.
    # We intentionally do NOT classify based only on the
    # user's message text.

    for value in args:

        if isinstance(
            value,
            (
                dict,
                list,
                tuple,
            )
        ):

            collect_identity_values(
                value,
                identities
            )

    for value in kwargs.values():

        if isinstance(
            value,
            (
                dict,
                list,
                tuple,
            )
        ):

            collect_identity_values(
                value,
                identities
            )

    targets = xpand_identifiers()

    for identity in identities:

        if identity in targets:
            return True

        if (
            "xpand"
            in identity
            and
            (
                "agent"
                in identity
                or
                "bot"
                in identity
                or
                identity
                ==
                "xpand"
            )
        ):
            return True

    return False


# =========================================================
# USER MESSAGE EXTRACTION
# =========================================================

MESSAGE_PARAMETER_NAMES = [
    "user_message",
    "message_text",
    "user_text",
    "message",
    "text",
    "prompt",
    "content",
    "query",
]


def extract_message_from_value(
    value
):
    if isinstance(
        value,
        str
    ):
        return clean_text(
            value,
            12000
        )

    if isinstance(
        value,
        dict
    ):

        for key in [
            "text",
            "message",
            "content",
            "caption",
            "query",
        ]:

            candidate = value.get(
                key
            )

            if isinstance(
                candidate,
                str
            ):

                candidate = clean_text(
                    candidate,
                    12000
                )

                if candidate:
                    return candidate

    return ""


def extract_user_message(
    args,
    kwargs
):
    bound = bind_original_arguments(
        args,
        kwargs
    )

    # First prefer parameter names that are explicitly used
    # in the project for user content.
    for key in MESSAGE_PARAMETER_NAMES:

        if key in bound:

            message = extract_message_from_value(
                bound.get(
                    key
                )
            )

            if message:
                return message

        if key in kwargs:

            message = extract_message_from_value(
                kwargs.get(
                    key
                )
            )

            if message:
                return message

    # Then inspect structured positional / keyword arguments
    # without guessing unsupported schemas.
    for value in args:

        message = extract_message_from_value(
            value
        )

        if message:
            return message

    for value in kwargs.values():

        message = extract_message_from_value(
            value
        )

        if message:
            return message

    return ""


def xpand_database_url():
    return clean_text(
        os.getenv(
            "XPAND_DATABASE_URL"
        )
        or
        getattr(
            kemo,
            "xpand_database_url",
            ""
        )
        or
        getattr(
            kemo,
            "XPAND_DATABASE_URL",
            ""
        )
        or
        "",
        10000
    )


def resolve_xpand_runtime_profile():
    profile = {
        "system_prompt": "",
        "provider": "",
        "model": "",
        "style": "",
        "voice_profile": "",
        "voice": "",
        "admin_profile_found": False,
        "admin_profile_version": None,
        "admin_profile_source": "fallback",
    }

    db_url = xpand_database_url()

    print(
        "XPAND DB CHECK | db_source=xpand | agent_id=xpand"
    )

    if not db_url:
        print(
            "XPAND ADMIN PROFILE LOAD | found=false | version=N | source=xpand_database"
        )
        return profile

    conn = None

    try:
        try:
            import psycopg2
            conn = psycopg2.connect(
                db_url
            )
        except ImportError:
            import psycopg
            conn = psycopg.connect(
                db_url
            )

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    system_prompt,
                    voice_profile,
                    learning_notes,
                    version
                FROM
                    agent_runtime_admin_profile
                WHERE
                    agent_id = %s
                LIMIT 1;
                """,
                (
                    "xpand",
                )
            )

            row = cur.fetchone()

        if row:
            profile["admin_profile_found"] = True
            profile["admin_profile_source"] = "xpand_database"
            profile["admin_profile_version"] = row[3]
            profile["voice_profile"] = clean_text(
                row[1],
                2000
            )
            profile["style"] = clean_text(
                row[2],
                2000
            )
            system_prompt = clean_text(
                row[0],
                50000
            )
            if system_prompt:
                profile["system_prompt"] = system_prompt

        print(
            (
                "XPAND ADMIN PROFILE LOAD | found="
                +
                ("true" if profile["admin_profile_found"] else "false")
                +
                " | version="
                +
                str(
                    profile["admin_profile_version"]
                    if profile["admin_profile_version"] is not None
                    else
                    "N"
                )
                +
                " | source=xpand_database"
            )
        )

    except Exception:
        print(
            "XPAND ADMIN PROFILE LOAD | found=false | version=N | source=xpand_database"
        )

    finally:
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass

    if not profile["system_prompt"]:
        profile["system_prompt"] = load_text_file(
            XPAND_SYSTEM_PROMPT
        )
        profile["admin_profile_source"] = "fallback"

    return profile


# =========================================================
# USER ID EXTRACTION
# =========================================================

def extract_user_id(
    args,
    kwargs
):
    bound = bind_original_arguments(
        args,
        kwargs
    )

    candidates = [
        "user_id",
        "owner_user_id",
        "telegram_user_id",
        "chat_id",
    ]

    for key in candidates:

        value = (
            bound.get(
                key
            )
            if key in bound
            else
            kwargs.get(
                key
            )
        )

        try:

            number = int(
                value
            )

            if number > 0:
                return number

        except Exception:
            pass

    return None


# =========================================================
# DATABASE
# =========================================================

def database_url():
    return clean_text(
        xpand_database_url(),
        10000
    )


def db_connect():
    url = database_url()

    if not url:
        return None

    try:

        import psycopg2

        return psycopg2.connect(
            url
        )

    except ImportError:
        pass

    try:

        import psycopg

        return psycopg.connect(
            url
        )

    except ImportError:
        return None


# =========================================================
# SAFE RECENT XPAND MEMORY
#
# Reads only from the existing CHILD AGENT message table.
#
# It does not query:
# - Kemo messages
# - Kemo memories
# - Kemo canonical facts
# - Kemo profile facts
# =========================================================

def get_table_columns(
    conn,
    table_name
):
    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    column_name

                FROM
                    information_schema.columns

                WHERE
                    table_schema = current_schema()
                    AND table_name = %s;
                """,
                (
                    table_name,
                )
            )

            return {
                row[0]
                for row
                in cur.fetchall()
            }

    except Exception:

        return set()


def load_recent_xpand_history(
    user_id=None,
    limit=24
):
    conn = db_connect()

    if conn is None:
        return []

    table_name = (
        "kemo_agent_factory_messages"
    )

    try:

        columns = get_table_columns(
            conn,
            table_name
        )

        if not columns:
            return []

        identity_columns = [
            item
            for item
            in [
                "agent_slug",
                "slug",
                "agent_name",
                "bot_username",
                "telegram_username",
                "username",
            ]
            if item in columns
        ]

        # If we cannot identify the child agent safely,
        # do not read rows.
        #
        # Privacy > recall.

        if not identity_columns:
            return []

        identifiers = sorted(
            xpand_identifiers()
        )

        where_parts = []
        params = []

        for column in identity_columns:

            placeholders = ", ".join(
                [
                    "%s"
                    for _
                    in identifiers
                ]
            )

            where_parts.append(
                (
                    "LOWER(CAST("
                    +
                    '"'
                    +
                    column
                    +
                    '"'
                    +
                    " AS TEXT)) "
                    +
                    "IN ("
                    +
                    placeholders
                    +
                    ")"
                )
            )

            params.extend(
                identifiers
            )

        user_filter_column = None

        if user_id:

            for candidate in [
                "owner_user_id",
                "telegram_user_id",
                "user_id",
                "chat_id",
            ]:

                if candidate in columns:

                    user_filter_column = (
                        candidate
                    )

                    break

        where_sql = (
            "("
            +
            " OR ".join(
                where_parts
            )
            +
            ")"
        )

        if (
            user_filter_column
            and
            user_id
        ):

            where_sql += (
                " AND CAST("
                +
                '"'
                +
                user_filter_column
                +
                '"'
                +
                " AS TEXT) = %s"
            )

            params.append(
                str(
                    user_id
                )
            )

        order_column = None

        for candidate in [
            "created_at",
            "id",
        ]:

            if candidate in columns:

                order_column = (
                    candidate
                )

                break

        order_sql = (
            (
                ' ORDER BY "'
                +
                order_column
                +
                '" DESC'
            )
            if order_column
            else
            ""
        )

        query = (
            "SELECT row_to_json(m)::text "
            +
            "FROM "
            +
            table_name
            +
            " m "
            +
            "WHERE "
            +
            where_sql
            +
            order_sql
            +
            " LIMIT %s"
        )

        params.append(
            int(
                max(
                    1,
                    min(
                        limit,
                        50
                    )
                )
            )
        )

        with conn.cursor() as cur:

            cur.execute(
                query,
                tuple(
                    params
                )
            )

            raw_rows = cur.fetchall()

        history = []

        for row in reversed(
            raw_rows
        ):

            try:

                item = json.loads(
                    row[0]
                )

            except Exception:
                continue

            if not isinstance(
                item,
                dict
            ):
                continue

            role = ""

            for key in [
                "role",
                "message_role",
                "sender_role",
                "author",
            ]:

                value = clean_text(
                    item.get(
                        key
                    ),
                    50
                ).lower()

                if value:
                    role = value
                    break

            content = ""

            for key in [
                "content",
                "text",
                "message_text",
                "message",
                "body",
            ]:

                value = item.get(
                    key
                )

                if isinstance(
                    value,
                    str
                ):

                    value = clean_text(
                        value,
                        4000
                    )

                    if value:
                        content = value
                        break

            if not content:
                continue

            if role in {
                "assistant",
                "agent",
                "bot",
                "model",
            }:

                normalized_role = (
                    "assistant"
                )

            else:

                normalized_role = (
                    "user"
                )

            history.append(
                {
                    "role":
                        normalized_role,

                    "text":
                        content,
                }
            )

        return history[-limit:]

    except Exception as error:

        print(
            (
                "⚠️ XPAND memory context skipped | "
                +
                clean_text(
                    error,
                    500
                )
            )
        )

        return []

    finally:

        try:
            conn.close()

        except Exception:
            pass


# =========================================================
# OPENAI SYSTEM INSTRUCTIONS
# =========================================================

def build_xpand_instructions():
    profile = load_xpand_profile()
    runtime_profile = resolve_xpand_runtime_profile()

    system_prompt = clean_text(
        runtime_profile.get(
            "system_prompt"
        )
        or
        profile.get(
            "system_prompt"
        ),
        50000
    )

    print(
        (
            "XPAND TEXT SYSTEM PROMPT | source="
            +
            (
                "admin_profile"
                if runtime_profile.get(
                    "admin_profile_found"
                )
                and
                runtime_profile.get(
                    "system_prompt"
                )
                else
                "fallback"
            )
        )
    )

    if not system_prompt:

        system_prompt = """
أنت XPAND Agent.

أنت وكيل ذكاء اصطناعي مستقل خاص بـXPAND.

رد بلغة المستخدم بشكل طبيعي ومفيد.

لا تدّعِ أنك Kemo.
لا تستخدم ذاكرة Kemo الشخصية.
لا تدّعِ تنفيذ شيء لم يتم فعلياً.
لا تكشف الأسرار أو مفاتيح API.
""".strip()

    enabled_capabilities = (
        extract_enabled_capabilities(
            profile.get(
                "capabilities_json"
            )
            or
            {}
        )
    )

    capability_text = (
        "\n".join(
            (
                "- "
                +
                item
            )
            for item
            in enabled_capabilities
        )
        if enabled_capabilities
        else
        "- general_chat"
    )

    return (
        system_prompt
        +
        """

==================================================
XPAND RUNTIME PROVIDER
==================================================

أنت تعمل الآن من خلال OpenAI كعقل المحادثة الخاص بـXPAND.

هذا التغيير خاص بـXPAND فقط.

Kemo مساعد منفصل تماماً ويستخدم Provider خاص فيه.

ممنوع:
- الادعاء أنك Kemo
- استخدام ذاكرة Kemo الشخصية
- استخدام أسرار Kemo
- استخدام أسرار وكيل آخر
- اختراع Capability غير مفعلة
- قول "تم" عن فعل خارجي لم يؤكده Runtime

Capabilities المفعلة حالياً:
"""
        +
        capability_text
        +
        """

بالنسبة للفويس:
إذا وصلك نص ناتج عن Voice STT، تعامل معه كرسالة المستخدم العادية.
مسار STT/TTS تديره بنية XPAND الخارجية، وليس مطلوباً منك وصفه للمستخدم.

جاوب بشكل طبيعي ومباشر.
"""
    ).strip()


# =========================================================
# CONVERSATION INPUT
# =========================================================
def build_openai_input(
    current_message,
    history
):
    sections = []

    if history:

        lines = []

        for item in history[-24:]:

            role = (
                "XPAND"
                if item.get(
                    "role"
                )
                ==
                "assistant"
                else
                "USER"
            )

            text = clean_text(
                item.get(
                    "text"
                ),
                2500
            )

            if not text:
                continue

            lines.append(
                (
                    role
                    +
                    ": "
                    +
                    text
                )
            )

        if lines:

            sections.append(
                (
                    "=== RECENT XPAND CONVERSATION ===\n"
                    +
                    "\n".join(
                        lines
                    )
                )
            )

    sections.append(
        (
            "=== CURRENT USER MESSAGE ===\n"
            +
            clean_text(
                current_message,
                12000
            )
        )
    )

    return "\n\n".join(
        sections
    )


# =========================================================
# OPENAI RESPONSE TEXT
# =========================================================
def extract_openai_text(
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

        direct = clean_text(
            direct,
            12000
        )

        if direct:
            return direct

    pieces = []

    output = data.get(
        "output"
    )

    if not isinstance(
        output,
        list
    ):
        output = []

    for item in output:

        if not isinstance(
            item,
            dict
        ):
            continue

        content = item.get(
            "content"
        )

        if not isinstance(
            content,
            list
        ):
            continue

        for part in content:

            if not isinstance(
                part,
                dict
            ):
                continue

            text = part.get(
                "text"
            )

            if isinstance(
                text,
                str
            ):

                text = clean_text(
                    text,
                    12000
                )

                if text:
                    pieces.append(
                        text
                    )

    return clean_text(
        "\n".join(
            pieces
        ),
        12000
    )


# =========================================================
# OPENAI REQUEST
# =========================================================
def call_xpand_openai(
    current_message,
    history=None
):
    if not XPAND_OPENAI_API_KEY:

        raise RuntimeError(
            "XPAND_OPENAI_API_KEY is missing."
        )

    runtime_profile = resolve_xpand_runtime_profile()
    selected_model = clean_text(
        runtime_profile.get(
            "model"
        )
        or
        XPAND_OPENAI_MODEL,
        200
    )

    selected_provider = clean_text(
        runtime_profile.get(
            "provider"
        )
        or
        "openai",
        100
    )

    selected_style = clean_text(
        runtime_profile.get(
            "style"
        ),
        5000
    )

    if not selected_model:

        raise RuntimeError(
            "XPAND_OPENAI_MODEL is missing."
        )

    history = (
        history
        if isinstance(
            history,
            list
        )
        else
        []
    )

    payload = {
        "model":
            selected_model,

        "instructions":
            build_xpand_instructions(),

        "input":
            build_openai_input(
                current_message,
                history
            ),

        "max_output_tokens":
            XPAND_OPENAI_MAX_OUTPUT_TOKENS,

        # We do not depend on OpenAI-side conversation storage.
        # XPAND's existing memory remains under Kemo's
        # agent-scoped persistence.
        "store":
            False,
    }

    if selected_style:
        payload["metadata"] = {
            "agent": "xpand",
            "provider": selected_provider,
            "style": selected_style,
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
                    XPAND_OPENAI_API_KEY
                ),

            "Content-Type":
                "application/json",

            "Accept":
                "application/json",

            "User-Agent":
                (
                    "Kemo-Agent-Factory/"
                    +
                    VERSION
                ),
        }
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=XPAND_OPENAI_TIMEOUT_SECONDS
        ) as response:

            raw = response.read()

            status = int(
                response.status
            )

    except urllib.error.HTTPError as error:

        raw = error.read()

        message = ""

        try:

            error_data = json.loads(
                raw.decode(
                    "utf-8"
                )
            )

            message = clean_text(
                (
                    error_data.get(
                        "error"
                    )
                    or
                    {}
                ).get(
                    "message"
                ),
                1000
            )

        except Exception:
            message = ""

        raise RuntimeError(
            (
                "OpenAI HTTP "
                +
                str(
                    error.code
                )
                +
                (
                    (
                        ": "
                        +
                        message
                    )
                    if message
                    else
                    ""
                )
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
                    700
                )
            )
        )

    if status < 200 or status >= 300:

        raise RuntimeError(
            (
                "OpenAI HTTP "
                +
                str(
                    status
                )
            )
        )

    try:

        data = json.loads(
            raw.decode(
                "utf-8"
            )
        )

    except Exception:

        raise RuntimeError(
            "OpenAI returned invalid JSON."
        )

    answer = extract_openai_text(
        data
    )

    if not answer:

        raise RuntimeError(
            "OpenAI returned no assistant text."
        )

    return answer


# =========================================================
# XPAND PROVIDER ANSWER
# =========================================================
def xpand_openai_answer(
    args,
    kwargs
):
    user_message = extract_user_message(
        args,
        kwargs
    )

    if not user_message:

        raise RuntimeError(
            (
                "Could not resolve XPAND "
                "user message from runtime."
            )
        )

    user_id = extract_user_id(
        args,
        kwargs
    )

    history = load_recent_xpand_history(
        user_id=user_id,
        limit=24
    )

    # Avoid duplicating the current incoming message
    # if the lower runtime saved it before asking AI.

    if history:

        last = history[-1]

        if (
            last.get(
                "role"
            )
            ==
            "user"
            and
            normalize_text(
                last.get(
                    "text"
                )
            )
            ==
            normalize_text(
                user_message
            )
        ):

            history = history[:-1]

    runtime_profile = resolve_xpand_runtime_profile()

    print(
        (
            "🧠 XPAND AI PROVIDER | "
            +
            clean_text(
                runtime_profile.get(
                    "provider"
                )
                or
                "openai",
                50
            ).upper()
            +
            " | "
            +
            clean_text(
                runtime_profile.get(
                    "model"
                )
                or
                XPAND_OPENAI_MODEL,
                120
            )
        )
    )

    return call_xpand_openai(
        user_message,
        history
    )


# =========================================================
# PROVIDER ROUTER
# =========================================================
def provider_general_agent_answer(
    *args,
    **kwargs
):
    # -----------------------------------------------------
    # XPAND
    # -----------------------------------------------------

    if is_xpand_agent_call(
        args,
        kwargs
    ):

        try:

            answer = xpand_openai_answer(
                args,
                kwargs
            )

            print(
                (
                    "✅ XPAND OPENAI RESPONSE | "
                    +
                    clean_text(
                        resolve_xpand_runtime_profile().get(
                            "model"
                        )
                        or
                        XPAND_OPENAI_MODEL,
                        120
                    )
                )
            )

            return answer

        except Exception as error:

            print(
                (
                    "❌ XPAND OPENAI ERROR | "
                    +
                    clean_text(
                        error,
                        1200
                    )
                )
            )

            if XPAND_ALLOW_GEMINI_FALLBACK:

                print(
                    (
                        "⚠️ XPAND explicit Gemini "
                        "fallback enabled"
                    )
                )

                return ORIGINAL_GENERAL_AGENT_ANSWER(
                    *args,
                    **kwargs
                )

            # Strict provider isolation.
            #
            # Do NOT silently send the message to Gemini.

            return (
                "صار خلل مؤقت باتصال XPAND "
                "مع محرك OpenAI. "
                "ما حولت طلبك تلقائياً لـGemini "
                "حتى ما أخلط مزودات الوكيل. "
                "جرّب مرة ثانية بعد شوي."
            )

    # -----------------------------------------------------
    # ALL OTHER AGENTS
    #
    # Preserve the complete previous runtime.
    # -----------------------------------------------------

    return ORIGINAL_GENERAL_AGENT_ANSWER(
        *args,
        **kwargs
    )


# =========================================================
# INSTALL PATCH
# =========================================================
def install_provider_router():

    factory.general_agent_answer = (
        provider_general_agent_answer
    )

    # Some modules may access factory through their own
    # imported module reference. Keep those references
    # pointed at the same patched factory module.

    try:
        capabilities.factory.general_agent_answer = (
            provider_general_agent_answer
        )
    except Exception:
        pass

    try:
        commands.factory.general_agent_answer = (
            provider_general_agent_answer
        )
    except Exception:
        pass

    try:
        profiles.factory.general_agent_answer = (
            provider_general_agent_answer
        )
    except Exception:
        pass

    return True


# =========================================================
# STARTUP CHECKS
# =========================================================
def startup_checks():

    profile = load_xpand_profile()
    runtime_profile = resolve_xpand_runtime_profile()

    return {
        "openaiKey":
            bool(
                XPAND_OPENAI_API_KEY
            ),

        "openaiModel":
            bool(
                runtime_profile.get(
                    "model"
                )
                or
                XPAND_OPENAI_MODEL
            ),

        "profile":
            bool(
                profile.get(
                    "name"
                )
            ),

        "systemPrompt":
            bool(
                runtime_profile.get(
                    "system_prompt"
                )
                or
                profile.get(
                    "system_prompt"
                )
            ),

        "capabilities":
            XPAND_CAPABILITIES_JSON.exists(),

        "originalAgentBrain":
            callable(
                ORIGINAL_GENERAL_AGENT_ANSWER
            ),

        "kemoBrain":
            callable(
                getattr(
                    kemo,
                    "ask_kemo",
                    None
                )
            ),
    }


# =========================================================
# MAIN
# =========================================================
def main():

    install_provider_router()

    checks = startup_checks()

    print("")

    print(
        "=============================================="
    )

    print(
        " XPAND AGENT FACTORY AI PROVIDERS V1.0"
    )

    print(
        " PER-AGENT MODEL ROUTING"
    )

    print(
        "=============================================="
    )

    print("")

    print(
        (
            "✅ XPAND OpenAI API Key: "
            +
            (
                "READY"
                if checks[
                    "openaiKey"
                ]
                else
                "MISSING"
            )
        )
    )

    print(
        (
            "✅ XPAND OpenAI Model: "
            +
            (
                clean_text(
                    resolve_xpand_runtime_profile().get(
                        "model"
                    )
                    or
                    XPAND_OPENAI_MODEL,
                    120
                )
                if checks[
                    "openaiModel"
                ]
                else
                "MISSING"
            )
        )
    )

    print(
        (
            "✅ XPAND profile: "
            +
            (
                "READY"
                if checks[
                    "profile"
                ]
                else
                "MISSING"
            )
        )
    )

    print(
        (
            "✅ XPAND system_prompt.md: "
            +
            (
                "READY"
                if checks[
                    "systemPrompt"
                ]
                else
                "MISSING"
            )
        )
    )

    print(
        (
            "✅ XPAND capabilities.json: "
            +
            (
                "READY"
                if checks[
                    "capabilities"
                ]
                else
                "MISSING"
            )
        )
    )

    print(
        "✅ XPAND provider: OPENAI"
    )

    print(
        "✅ XPAND text route: OPENAI"
    )

    print(
        "✅ XPAND voice AI route: OPENAI"
    )

    print(
        "✅ Existing XPAND STT/TTS preserved"
    )

    print(
        (
            "✅ Gemini fallback for XPAND: "
            +
            (
                "ENABLED"
                if XPAND_ALLOW_GEMINI_FALLBACK
                else
                "DISABLED"
            )
        )
    )

    print(
        "🔒 Kemo AI provider: UNCHANGED"
    )

    print(
        "🔒 Kemo Gemini runtime: PRESERVED"
    )

    print(
        "🔒 XPAND personal memory: NOT exposed to XPAND"
    )

    print(
        "🔒 XPAND OpenAI key: ENV ONLY"
    )

    print(
        "🚫 XPAND is NOT marked OpenAI VERIFIED yet"
    )

    print(
        "✅ Real Telegram text test required"
    )

    print(
        "✅ Real Telegram voice test required"
    )

    print("")

    print(
        "✅ AI PROVIDER ROUTER ONLINE"
    )

    print("")

    # Continue into the complete existing runtime:
    #
    # call provisioner
    # -> profiles
    # -> commands
    # -> capabilities
    # -> agent factory
    # -> Kemo

    call_stack.main()


# =========================================================
# ENTRY
# =========================================================

if __name__ == "__main__":
    main()
