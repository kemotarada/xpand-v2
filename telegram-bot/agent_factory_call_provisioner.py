# =========================================================
# KEMO AGENT FACTORY - LIVE CALL PROVISIONER V1.0
#
# Purpose:
#
# Kemo can understand commands such as:
#
#   كيمو ضيف لـ XPAND ميزة المكالمة
#   فعل الاتصال المباشر لوكيل XPAND
#   ركب live call لـ XPAND
#
# Then, only after real backend evidence, it can:
#
# - Resolve the target managed agent
# - Fetch the managed Telegram bot token securely
# - Load that agent's own profile/system prompt
# - Require that agent's own Gemini key
# - Require that agent's own database URL
# - Create/find a dedicated Railway project
# - Create/find a dedicated Railway call service
# - Deploy agent_templates/live_call
# - Set agent-isolated Railway variables
# - Generate Railway HTTPS domain
# - Wait for deployment SUCCESS
# - Verify /api/health
# - Configure Telegram WebApp call button
#
# IMPORTANT:
#
# Deployment success != real call verification.
#
# The capability becomes:
#
#   ready_for_real_test
#
# only after:
# - deployment SUCCESS
# - /api/health PASS
# - Telegram call button configured
#
# It becomes:
#
#   verified
#
# only after a real ended call contains an actual
# user + assistant transcript.
#
# Shared code.
# Isolated agent secrets.
# No fake success.
# =========================================================


import os
import re
import json
import time
import secrets
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone


# =========================================================
# EXISTING KEMO AGENT FACTORY STACK
# =========================================================

import agent_factory_profiles as profiles
import agent_factory_commands as commands
import agent_factory_capabilities as capabilities
import agent_factory_runner as factory


try:
    import main as kemo
except Exception:
    kemo = getattr(
        factory,
        "kemo",
        None
    )


if kemo is None:
    raise RuntimeError(
        "Kemo core module was not found."
    )


# =========================================================
# CONSTANTS
# =========================================================

VERSION = "1.0"


RAILWAY_GRAPHQL_URL = (
    "https://backboard.railway.com/graphql/v2"
)


DEFAULT_GITHUB_REPO = (
    "kemotarada/kemo-telegram-bot"
)


DEFAULT_GITHUB_BRANCH = (
    "main"
)


CALL_TEMPLATE_ROOT = (
    "/agent_templates/live_call"
)


CALL_HEALTH_PATH = (
    "/api/health"
)


DEPLOY_TIMEOUT_SECONDS = int(
    os.getenv(
        "AGENT_FACTORY_DEPLOY_TIMEOUT_SECONDS",
        "720"
    )
    or
    "720"
)


HEALTH_TIMEOUT_SECONDS = int(
    os.getenv(
        "AGENT_FACTORY_HEALTH_TIMEOUT_SECONDS",
        "180"
    )
    or
    "180"
)


POLL_SECONDS = 5


BASE_DIR = Path(
    __file__
).resolve().parent


AGENTS_DIR = (
    BASE_DIR
    /
    "agents"
)


# =========================================================
# TEXT HELPERS
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
    ).strip()[:max_length]


def normalize_text(
    value
):
    value = clean_text(
        value,
        10000
    ).lower()

    value = (
        value
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

    value = re.sub(
        r"[\u064B-\u065F]",
        "",
        value
    )

    value = re.sub(
        r"[^a-z0-9\u0600-\u06ff_@.\-\s]",
        " ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


def contains_any(
    value,
    markers
):
    source = normalize_text(
        value
    )

    return any(
        normalize_text(
            marker
        )
        in
        source
        for marker
        in markers
    )


def slugify(
    value
):
    value = normalize_text(
        value
    )

    value = re.sub(
        r"[^a-z0-9]+",
        "-",
        value
    )

    value = value.strip(
        "-"
    )

    return (
        value
        or
        "agent"
    )[:60]


def secret_prefix(
    slug
):
    value = re.sub(
        r"[^A-Za-z0-9]+",
        "_",
        str(
            slug
            or
            ""
        )
    )

    return (
        value
        .strip(
            "_"
        )
        .upper()
    )


def now_iso():
    return datetime.now(
        timezone.utc
    ).isoformat()


# =========================================================
# DATABASE DRIVER
# =========================================================

def get_database_url():
    value = clean_text(
        os.getenv(
            "DATABASE_URL"
        ),
        10000
    )

    if value:
        return value

    value = clean_text(
        getattr(
            kemo,
            "DATABASE_URL",
            ""
        ),
        10000
    )

    return value


def db_connect(
    database_url=None
):
    url = clean_text(
        database_url
        or
        get_database_url(),
        10000
    )

    if not url:
        raise RuntimeError(
            "DATABASE_URL is missing."
        )

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
        raise RuntimeError(
            (
                "PostgreSQL driver missing. "
                "Expected psycopg2 or psycopg."
            )
        )


def fetch_one_dict(
    conn,
    query,
    params=None
):
    params = params or ()

    with conn.cursor() as cur:
        cur.execute(
            query,
            params
        )

        row = cur.fetchone()

        if row is None:
            return None

        columns = [
            item[0]
            for item
            in cur.description
        ]

        return dict(
            zip(
                columns,
                row
            )
        )


def fetch_all_dicts(
    conn,
    query,
    params=None
):
    params = params or ()

    with conn.cursor() as cur:
        cur.execute(
            query,
            params
        )

        rows = cur.fetchall()

        columns = [
            item[0]
            for item
            in cur.description
        ]

        return [
            dict(
                zip(
                    columns,
                    row
                )
            )
            for row
            in rows
        ]


# =========================================================
# CALL DEPLOYMENT REGISTRY
# =========================================================

def init_call_registry():
    with db_connect() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS
                kemo_agent_factory_call_deployments
                (
                    id BIGSERIAL PRIMARY KEY,

                    owner_user_id BIGINT NOT NULL,

                    agent_db_id TEXT,

                    agent_slug TEXT NOT NULL,

                    agent_name TEXT NOT NULL,

                    bot_username TEXT,

                    railway_project_id TEXT,

                    railway_environment_id TEXT,

                    railway_service_id TEXT,

                    railway_domain TEXT,

                    railway_deployment_id TEXT,

                    status TEXT NOT NULL
                        DEFAULT 'not_installed',

                    health_json JSONB NOT NULL
                        DEFAULT '{}'::jsonb,

                    last_error TEXT,

                    created_at TIMESTAMPTZ NOT NULL
                        DEFAULT NOW(),

                    updated_at TIMESTAMPTZ NOT NULL
                        DEFAULT NOW(),

                    verified_at TIMESTAMPTZ,

                    UNIQUE(
                        owner_user_id,
                        agent_slug
                    )
                );
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_agent_factory_call_status

                ON
                    kemo_agent_factory_call_deployments
                    (
                        owner_user_id,
                        status,
                        updated_at DESC
                    );
                """
            )

        conn.commit()


def get_call_registry(
    owner_user_id,
    agent_slug
):
    with db_connect() as conn:

        return fetch_one_dict(
            conn,
            """
            SELECT *
            FROM
                kemo_agent_factory_call_deployments
            WHERE
                owner_user_id = %s
                AND agent_slug = %s
            LIMIT 1;
            """,
            (
                int(
                    owner_user_id
                ),
                agent_slug
            )
        )


REGISTRY_FIELDS = {
    "agent_db_id",
    "agent_name",
    "bot_username",
    "railway_project_id",
    "railway_environment_id",
    "railway_service_id",
    "railway_domain",
    "railway_deployment_id",
    "status",
    "health_json",
    "last_error",
    "verified_at",
}


def update_call_registry(
    owner_user_id,
    agent_slug,
    **values
):
    safe_values = {
        key:
            value
        for (
            key,
            value
        )
        in values.items()
        if key in REGISTRY_FIELDS
    }

    agent_name = clean_text(
        safe_values.get(
            "agent_name"
        )
        or
        agent_slug,
        300
    )

    bot_username = clean_text(
        safe_values.get(
            "bot_username"
        ),
        300
    )

    with db_connect() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO
                    kemo_agent_factory_call_deployments
                    (
                        owner_user_id,
                        agent_slug,
                        agent_name,
                        bot_username
                    )

                VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s
                    )

                ON CONFLICT
                    (
                        owner_user_id,
                        agent_slug
                    )

                DO NOTHING;
                """,
                (
                    int(
                        owner_user_id
                    ),
                    agent_slug,
                    agent_name,
                    bot_username
                )
            )

            for (
                key,
                value
            ) in safe_values.items():

                if key == "health_json":

                    cur.execute(
                        """
                        UPDATE
                            kemo_agent_factory_call_deployments

                        SET
                            health_json = %s::jsonb,
                            updated_at = NOW()

                        WHERE
                            owner_user_id = %s
                            AND agent_slug = %s;
                        """,
                        (
                            json.dumps(
                                value
                                if isinstance(
                                    value,
                                    dict
                                )
                                else
                                {},
                                ensure_ascii=False
                            ),
                            int(
                                owner_user_id
                            ),
                            agent_slug
                        )
                    )

                elif key == "verified_at":

                    cur.execute(
                        """
                        UPDATE
                            kemo_agent_factory_call_deployments

                        SET
                            verified_at = %s,
                            updated_at = NOW()

                        WHERE
                            owner_user_id = %s
                            AND agent_slug = %s;
                        """,
                        (
                            value,
                            int(
                                owner_user_id
                            ),
                            agent_slug
                        )
                    )

                else:

                    cur.execute(
                        f"""
                        UPDATE
                            kemo_agent_factory_call_deployments

                        SET
                            {key} = %s,
                            updated_at = NOW()

                        WHERE
                            owner_user_id = %s
                            AND agent_slug = %s;
                        """,
                        (
                            value,
                            int(
                                owner_user_id
                            ),
                            agent_slug
                        )
                    )

        conn.commit()


# =========================================================
# AGENT FACTORY DATABASE LOOKUP
# =========================================================

def load_factory_agents():
    try:
        with db_connect() as conn:

            rows = fetch_all_dicts(
                conn,
                """
                SELECT
                    row_to_json(a)::text
                        AS agent_json

                FROM
                    kemo_agent_factory_agents a

                ORDER BY
                    created_at DESC

                LIMIT 250;
                """
            )

        agents = []

        for row in rows:

            raw = row.get(
                "agent_json"
            )

            if isinstance(
                raw,
                dict
            ):
                data = raw

            else:
                try:
                    data = json.loads(
                        raw
                    )
                except Exception:
                    continue

            if isinstance(
                data,
                dict
            ):
                agents.append(
                    data
                )

        return agents

    except Exception as error:
        print(
            (
                "⚠️ Agent registry lookup: "
                +
                str(
                    error
                )
            )
        )

        return []


def first_value(
    data,
    keys
):
    for key in keys:

        value = data.get(
            key
        )

        if (
            value is not None
            and
            str(
                value
            ).strip()
        ):
            return value

    return None


def agent_display_name(
    row
):
    return clean_text(
        first_value(
            row,
            [
                "name",
                "agent_name",
                "display_name",
                "bot_name",
            ]
        ),
        300
    )


def agent_username(
    row
):
    value = clean_text(
        first_value(
            row,
            [
                "bot_username",
                "telegram_username",
                "username",
            ]
        ),
        300
    )

    if (
        value
        and
        not value.startswith(
            "@"
        )
    ):
        value = (
            "@"
            +
            value
        )

    return value


def agent_db_id(
    row
):
    return clean_text(
        first_value(
            row,
            [
                "id",
                "agent_id",
                "uuid",
            ]
        ),
        300
    )


def managed_bot_user_id(
    row
):
    preferred_keys = [
        "managed_bot_user_id",
        "telegram_bot_user_id",
        "bot_user_id",
        "telegram_bot_id",
        "managed_bot_id",
        "bot_id",
    ]

    for key in preferred_keys:

        value = row.get(
            key
        )

        try:
            number = int(
                value
            )

            if number > 0:
                return number

        except Exception:
            pass

    for (
        key,
        value
    ) in row.items():

        key_lower = str(
            key
        ).lower()

        if (
            "bot"
            not in key_lower
            or
            "id"
            not in key_lower
        ):
            continue

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
# FILESYSTEM AGENT PROFILES
# =========================================================

def scan_agent_profiles():
    result = []

    if not AGENTS_DIR.exists():
        return result

    for folder in AGENTS_DIR.iterdir():

        if not folder.is_dir():
            continue

        agent_json_path = (
            folder
            /
            "agent.json"
        )

        if not agent_json_path.exists():
            continue

        try:
            data = json.loads(
                agent_json_path.read_text(
                    encoding="utf-8"
                )
            )

        except Exception as error:
            print(
                (
                    "⚠️ Profile "
                    +
                    folder.name
                    +
                    ": "
                    +
                    str(
                        error
                    )
                )
            )

            continue

        system_prompt_path = (
            folder
            /
            "system_prompt.md"
        )

        prompt = ""

        if system_prompt_path.exists():
            try:
                prompt = (
                    system_prompt_path
                    .read_text(
                        encoding="utf-8"
                    )
                    .strip()
                )

            except Exception:
                prompt = ""

        username = clean_text(
            (
                data.get(
                    "telegram",
                    {}
                )
                or
                {}
            ).get(
                "username"
            )
            or
            data.get(
                "telegram_username"
            ),
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

        result.append(
            {
                "slug":
                    clean_text(
                        data.get(
                            "slug"
                        )
                        or
                        data.get(
                            "agent_id"
                        )
                        or
                        folder.name,
                        100
                    ),

                "name":
                    clean_text(
                        data.get(
                            "name"
                        )
                        or
                        data.get(
                            "agent_name"
                        )
                        or
                        folder.name,
                        300
                    ),

                "username":
                    username,

                "prompt":
                    prompt,

                "folder":
                    folder,
            }
        )

    return result


def profile_matches_row(
    profile,
    row
):
    profile_name = normalize_text(
        profile.get(
            "name"
        )
    )

    profile_username = normalize_text(
        profile.get(
            "username"
        )
    )

    row_name = normalize_text(
        agent_display_name(
            row
        )
    )

    row_username = normalize_text(
        agent_username(
            row
        )
    )

    if (
        profile_username
        and
        row_username
        and
        profile_username
        ==
        row_username
    ):
        return True

    if (
        profile_name
        and
        row_name
        and
        profile_name
        ==
        row_name
    ):
        return True

    return False


def resolve_target_agent(
    user_message
):
    message = normalize_text(
        user_message
    )

    profiles_list = scan_agent_profiles()
    db_agents = load_factory_agents()

    # First:
    # match filesystem profile name / username / slug.

    for profile in profiles_list:

        candidates = [
            profile.get(
                "name"
            ),
            profile.get(
                "username"
            ),
            profile.get(
                "slug"
            ),
        ]

        if any(
            normalize_text(
                item
            )
            and
            normalize_text(
                item
            )
            in message
            for item
            in candidates
        ):

            matching_row = None

            for row in db_agents:

                if profile_matches_row(
                    profile,
                    row
                ):
                    matching_row = row
                    break

            return {
                "profile":
                    profile,

                "row":
                    matching_row,
            }

    # Second:
    # match DB agent names.

    for row in db_agents:

        name = agent_display_name(
            row
        )

        username = agent_username(
            row
        )

        if (
            (
                name
                and
                normalize_text(
                    name
                )
                in message
            )
            or
            (
                username
                and
                normalize_text(
                    username
                )
                in message
            )
        ):

            profile = None

            for item in profiles_list:

                if profile_matches_row(
                    item,
                    row
                ):
                    profile = item
                    break

            if profile is None:

                fallback_slug = slugify(
                    name
                    or
                    username
                    or
                    "agent"
                )

                profile = {
                    "slug":
                        fallback_slug,

                    "name":
                        name
                        or
                        fallback_slug,

                    "username":
                        username,

                    "prompt":
                        "",
                }

            return {
                "profile":
                    profile,

                "row":
                    row,
            }

    return None


# =========================================================
# TELEGRAM MANAGED BOT
# =========================================================

def manager_bot_token():
    candidates = [
        getattr(
            factory,
            "TELEGRAM_BOT_TOKEN",
            ""
        ),

        getattr(
            kemo,
            "TELEGRAM_BOT_TOKEN",
            ""
        ),

        os.getenv(
            "TELEGRAM_BOT_TOKEN",
            ""
        ),
    ]

    for candidate in candidates:

        value = clean_text(
            candidate,
            10000
        )

        if value:
            return value

    return ""


def telegram_api(
    bot_token,
    method,
    payload=None,
    timeout=30
):
    token = clean_text(
        bot_token,
        10000
    )

    if not token:
        raise RuntimeError(
            "Telegram bot token missing."
        )

    url = (
        "https://api.telegram.org/bot"
        +
        token
        +
        "/"
        +
        method
    )

    body = json.dumps(
        payload
        or {},
        ensure_ascii=False
    ).encode(
        "utf-8"
    )

    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type":
                "application/json",
        }
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout
        ) as response:

            raw = response.read()

    except urllib.error.HTTPError as error:

        raw = error.read()

        try:
            data = json.loads(
                raw.decode(
                    "utf-8"
                )
            )

            message = (
                data.get(
                    "description"
                )
                or
                str(
                    error
                )
            )

        except Exception:
            message = str(
                error
            )

        raise RuntimeError(
            message
        )

    data = json.loads(
        raw.decode(
            "utf-8"
        )
    )

    if not data.get(
        "ok"
    ):
        raise RuntimeError(
            data.get(
                "description"
            )
            or
            "Telegram request failed."
        )

    return data.get(
        "result"
    )


def fetch_managed_bot_token(
    agent_row
):
    if not agent_row:
        raise RuntimeError(
            (
                "الوكيل موجود في ملفات Kemo، "
                "لكن سجل Telegram Managed Bot "
                "مش موجود في قاعدة البيانات."
            )
        )

    bot_user_id = managed_bot_user_id(
        agent_row
    )

    if not bot_user_id:
        raise RuntimeError(
            (
                "لقيت الوكيل، بس ما لقيت "
                "Managed Bot user_id في سجله."
            )
        )

    manager_token = manager_bot_token()

    if not manager_token:
        raise RuntimeError(
            "Manager Telegram token is missing."
        )

    child_token = telegram_api(
        manager_token,
        "getManagedBotToken",
        {
            "user_id":
                int(
                    bot_user_id
                )
        }
    )

    child_token = clean_text(
        child_token,
        10000
    )

    if not child_token:
        raise RuntimeError(
            "Telegram returned an empty managed bot token."
        )

    child_me = telegram_api(
        child_token,
        "getMe",
        {}
    )

    returned_id = int(
        child_me.get(
            "id"
        )
        or
        0
    )

    if (
        returned_id
        !=
        int(
            bot_user_id
        )
    ):
        raise RuntimeError(
            (
                "Managed bot token verification failed. "
                "Telegram bot ID mismatch."
            )
        )

    return {
        "token":
            child_token,

        "bot_user_id":
            bot_user_id,

        "username":
            (
                "@"
                +
                clean_text(
                    child_me.get(
                        "username"
                    ),
                    300
                )
            )
            if child_me.get(
                "username"
            )
            else
            "",

        "name":
            clean_text(
                child_me.get(
                    "first_name"
                ),
                300
            ),
    }


# =========================================================
# AGENT SECRETS
# =========================================================

def get_agent_secret(
    prefix,
    name
):
    key = (
        prefix
        +
        "_"
        +
        name
    )

    value = clean_text(
        os.getenv(
            key
        ),
        100000
    )

    return value


def load_agent_runtime_secrets(
    slug
):
    prefix = secret_prefix(
        slug
    )

    result = {
        "prefix":
            prefix,

        "gemini_api_key":
            get_agent_secret(
                prefix,
                "GEMINI_API_KEY"
            ),

        "database_url":
            get_agent_secret(
                prefix,
                "DATABASE_URL"
            ),

        "tavily_api_key":
            get_agent_secret(
                prefix,
                "TAVILY_API_KEY"
            ),

        "live_model":
            get_agent_secret(
                prefix,
                "LIVE_MODEL"
            ),

        "voice":
            get_agent_secret(
                prefix,
                "VOICE"
            ),

        "timezone":
            get_agent_secret(
                prefix,
                "TIMEZONE"
            ),
    }

    allow_shared_db = (
        clean_text(
            os.getenv(
                "AGENT_FACTORY_ALLOW_SHARED_DATABASE"
            )
        ).lower()
        in
        {
            "1",
            "true",
            "yes",
            "on",
        }
    )

    if (
        not result[
            "database_url"
        ]
        and
        allow_shared_db
    ):

        result[
            "database_url"
        ] = get_database_url()

        result[
            "using_shared_database"
        ] = True

    else:
        result[
            "using_shared_database"
        ] = False

    return result


# =========================================================
# RAILWAY API
# =========================================================

def railway_token():
    return clean_text(
        os.getenv(
            "RAILWAY_API_TOKEN"
        )
        or
        os.getenv(
            "RAILWAY_TOKEN"
        ),
        10000
    )


def railway_graphql(
    query,
    variables=None,
    timeout=60
):
    token = railway_token()

    if not token:
        raise RuntimeError(
            (
                "RAILWAY_API_TOKEN مش موجود. "
                "ما رح أنشئ أي Railway resource "
                "بدون Factory token."
            )
        )

    payload = json.dumps(
        {
            "query":
                query,

            "variables":
                variables
                or
                {},
        }
    ).encode(
        "utf-8"
    )

    request = urllib.request.Request(
        RAILWAY_GRAPHQL_URL,
        data=payload,
        method="POST",
        headers={
            "Authorization":
                (
                    "Bearer "
                    +
                    token
                ),

            "Content-Type":
                "application/json",

            "Accept":
                "application/json",
        }
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=timeout
        ) as response:

            raw = response.read()

    except urllib.error.HTTPError as error:

        raw = error.read()

        try:
            data = json.loads(
                raw.decode(
                    "utf-8"
                )
            )

            raise RuntimeError(
                (
                    "Railway HTTP "
                    +
                    str(
                        error.code
                    )
                    +
                    ": "
                    +
                    clean_text(
                        data,
                        3000
                    )
                )
            )

        except json.JSONDecodeError:
            raise RuntimeError(
                (
                    "Railway HTTP "
                    +
                    str(
                        error.code
                    )
                )
            )

    data = json.loads(
        raw.decode(
            "utf-8"
        )
    )

    errors = data.get(
        "errors"
    )

    if errors:

        messages = []

        for error in errors:

            if isinstance(
                error,
                dict
            ):
                messages.append(
                    clean_text(
                        error.get(
                            "message"
                        ),
                        1000
                    )
                )

        raise RuntimeError(
            (
                "Railway GraphQL: "
                +
                " | ".join(
                    item
                    for item
                    in messages
                    if item
                )
            )
        )

    return data.get(
        "data"
    ) or {}


# =========================================================
# RAILWAY PROJECT
# =========================================================

def railway_get_project(
    project_id
):
    data = railway_graphql(
        """
        query Project($id: String!) {
          project(id: $id) {
            id
            name

            services {
              edges {
                node {
                  id
                  name
                }
              }
            }

            environments {
              edges {
                node {
                  id
                  name
                }
              }
            }
          }
        }
        """,
        {
            "id":
                project_id
        }
    )

    return data.get(
        "project"
    )


def railway_find_project_by_name(
    project_name
):
    data = railway_graphql(
        """
        query Projects {
          projects(first: 100) {
            edges {
              node {
                id
                name
              }
            }
          }
        }
        """
    )

    edges = (
        (
            data.get(
                "projects"
            )
            or
            {}
        ).get(
            "edges"
        )
        or
        []
    )

    for edge in edges:

        node = (
            edge.get(
                "node"
            )
            or
            {}
        )

        if (
            clean_text(
                node.get(
                    "name"
                )
            ).lower()
            ==
            project_name.lower()
        ):
            return node

    return None


def railway_create_project(
    project_name
):
    data = railway_graphql(
        """
        mutation ProjectCreate(
          $input: ProjectCreateInput!
        ) {
          projectCreate(
            input: $input
          ) {
            id
            name
          }
        }
        """,
        {
            "input": {
                "name":
                    project_name,

                "description":
                    (
                        "Kemo Agent Factory isolated project."
                    ),
            }
        }
    )

    project = data.get(
        "projectCreate"
    )

    if not project:
        raise RuntimeError(
            "Railway projectCreate returned no project."
        )

    return project


# =========================================================
# RAILWAY ENVIRONMENT
# =========================================================

def railway_get_or_create_environment(
    project_id
):
    project = railway_get_project(
        project_id
    )

    if not project:
        raise RuntimeError(
            "Railway project not found."
        )

    environments = (
        (
            project.get(
                "environments"
            )
            or
            {}
        ).get(
            "edges"
        )
        or
        []
    )

    for edge in environments:

        node = (
            edge.get(
                "node"
            )
            or
            {}
        )

        if (
            clean_text(
                node.get(
                    "name"
                )
            ).lower()
            ==
            "production"
        ):

            return node

    if environments:

        node = (
            environments[0].get(
                "node"
            )
            or
            {}
        )

        if node.get(
            "id"
        ):
            return node

    data = railway_graphql(
        """
        mutation EnvironmentCreate(
          $input: EnvironmentCreateInput!
        ) {
          environmentCreate(
            input: $input
          ) {
            id
            name
          }
        }
        """,
        {
            "input": {
                "projectId":
                    project_id,

                "name":
                    "production",
            }
        }
    )

    environment = data.get(
        "environmentCreate"
    )

    if not environment:
        raise RuntimeError(
            "Railway environmentCreate failed."
        )

    return environment


# =========================================================
# RAILWAY SERVICE
# =========================================================

def railway_find_service(
    project_id,
    service_name
):
    project = railway_get_project(
        project_id
    )

    if not project:
        return None

    edges = (
        (
            project.get(
                "services"
            )
            or
            {}
        ).get(
            "edges"
        )
        or
        []
    )

    for edge in edges:

        node = (
            edge.get(
                "node"
            )
            or
            {}
        )

        if (
            clean_text(
                node.get(
                    "name"
                )
            ).lower()
            ==
            service_name.lower()
        ):
            return node

    return None


def railway_create_call_service(
    project_id,
    environment_id,
    service_name
):
    repo = clean_text(
        os.getenv(
            "AGENT_FACTORY_GITHUB_REPO"
        )
        or
        DEFAULT_GITHUB_REPO,
        500
    )

    branch = clean_text(
        os.getenv(
            "AGENT_FACTORY_GITHUB_BRANCH"
        )
        or
        DEFAULT_GITHUB_BRANCH,
        200
    )

    data = railway_graphql(
        """
        mutation ServiceCreate(
          $input: ServiceCreateInput!
        ) {
          serviceCreate(
            input: $input
          ) {
            id
            name
          }
        }
        """,
        {
            "input": {
                "projectId":
                    project_id,

                "environmentId":
                    environment_id,

                "name":
                    service_name,

                "branch":
                    branch,

                "source": {
                    "repo":
                        repo
                },
            }
        }
    )

    service = data.get(
        "serviceCreate"
    )

    if not service:
        raise RuntimeError(
            "Railway serviceCreate returned no service."
        )

    return service


def railway_configure_service(
    service_id,
    environment_id
):
    data = railway_graphql(
        """
        mutation ServiceInstanceUpdate(
          $serviceId: String!,
          $environmentId: String!,
          $input: ServiceInstanceUpdateInput!
        ) {
          serviceInstanceUpdate(
            serviceId: $serviceId,
            environmentId: $environmentId,
            input: $input
          )
        }
        """,
        {
            "serviceId":
                service_id,

            "environmentId":
                environment_id,

            "input": {
                "rootDirectory":
                    CALL_TEMPLATE_ROOT,

                "startCommand":
                    "npm start",

                "healthcheckPath":
                    CALL_HEALTH_PATH,

                "numReplicas":
                    1,
            }
        }
    )

    if (
        data.get(
            "serviceInstanceUpdate"
        )
        is not True
    ):
        raise RuntimeError(
            "Railway service settings were not confirmed."
        )

    return True


# =========================================================
# RAILWAY VARIABLES
# =========================================================

def railway_set_variables(
    project_id,
    environment_id,
    service_id,
    variables
):
    safe_variables = {}

    for (
        key,
        value
    ) in variables.items():

        if value is None:
            continue

        value = str(
            value
        )

        if not value:
            continue

        safe_variables[
            str(
                key
            )
        ] = value

    data = railway_graphql(
        """
        mutation VariableCollectionUpsert(
          $input: VariableCollectionUpsertInput!
        ) {
          variableCollectionUpsert(
            input: $input
          )
        }
        """,
        {
            "input": {
                "projectId":
                    project_id,

                "environmentId":
                    environment_id,

                "serviceId":
                    service_id,

                "variables":
                    safe_variables,

                "replace":
                    False,
            }
        }
    )

    if (
        data.get(
            "variableCollectionUpsert"
        )
        is not True
    ):
        raise RuntimeError(
            "Railway variables were not confirmed."
        )

    return True


# =========================================================
# RAILWAY DOMAIN
# =========================================================

def extract_domain_from_value(
    value
):
    if isinstance(
        value,
        str
    ):

        if (
            "railway.app"
            in value
        ):
            return value.strip()

        return ""

    if isinstance(
        value,
        dict
    ):

        for (
            key,
            item
        ) in value.items():

            if (
                str(
                    key
                ).lower()
                ==
                "domain"
                and
                isinstance(
                    item,
                    str
                )
                and
                "railway.app"
                in item
            ):
                return item.strip()

            found = extract_domain_from_value(
                item
            )

            if found:
                return found

    if isinstance(
        value,
        list
    ):

        for item in value:

            found = extract_domain_from_value(
                item
            )

            if found:
                return found

    return ""


def railway_existing_domain(
    project_id,
    environment_id,
    service_id
):
    try:
        data = railway_graphql(
            """
            query Domains(
              $projectId: String!,
              $environmentId: String!,
              $serviceId: String!
            ) {
              domains(
                projectId: $projectId,
                environmentId: $environmentId,
                serviceId: $serviceId
              )
            }
            """,
            {
                "projectId":
                    project_id,

                "environmentId":
                    environment_id,

                "serviceId":
                    service_id,
            }
        )

        return extract_domain_from_value(
            data.get(
                "domains"
            )
        )

    except Exception:
        return ""


def railway_get_or_create_domain(
    project_id,
    environment_id,
    service_id
):
    existing = railway_existing_domain(
        project_id,
        environment_id,
        service_id
    )

    if existing:
        return existing

    try:
        data = railway_graphql(
            """
            mutation ServiceDomainCreate(
              $serviceId: String!,
              $environmentId: String!
            ) {
              serviceDomainCreate(
                serviceId: $serviceId,
                environmentId: $environmentId
              ) {
                domain
              }
            }
            """,
            {
                "serviceId":
                    service_id,

                "environmentId":
                    environment_id,
            }
        )

        domain = (
            (
                data.get(
                    "serviceDomainCreate"
                )
                or
                {}
            ).get(
                "domain"
            )
            or
            ""
        )

        if domain:
            return domain

    except Exception as error:

        print(
            (
                "⚠️ Railway domain create: "
                +
                str(
                    error
                )
            )
        )

        time.sleep(
            2
        )

        existing = railway_existing_domain(
            project_id,
            environment_id,
            service_id
        )

        if existing:
            return existing

        raise

    raise RuntimeError(
        "Railway domain was not returned."
    )


# =========================================================
# RAILWAY DEPLOY
# =========================================================

def railway_trigger_deploy(
    service_id,
    environment_id
):
    data = railway_graphql(
        """
        mutation Deploy(
          $serviceId: String!,
          $environmentId: String!
        ) {
          serviceInstanceDeployV2(
            serviceId: $serviceId,
            environmentId: $environmentId
          )
        }
        """,
        {
            "serviceId":
                service_id,

            "environmentId":
                environment_id,
        }
    )

    deployment_id = clean_text(
        data.get(
            "serviceInstanceDeployV2"
        ),
        300
    )

    if not deployment_id:
        raise RuntimeError(
            "Railway deployment ID was not returned."
        )

    return deployment_id


def railway_deployment(
    deployment_id
):
    data = railway_graphql(
        """
        query Deployment(
          $id: String!
        ) {
          deployment(
            id: $id
          ) {
            id
            status
            createdAt
            updatedAt
            url
            staticUrl
          }
        }
        """,
        {
            "id":
                deployment_id
        }
    )

    return data.get(
        "deployment"
    )


DEPLOY_SUCCESS_STATUSES = {
    "SUCCESS",
}


DEPLOY_FAILURE_STATUSES = {
    "FAILED",
    "CRASHED",
    "CANCELLED",
    "REMOVED",
}


def wait_for_deployment(
    deployment_id
):
    deadline = (
        time.time()
        +
        DEPLOY_TIMEOUT_SECONDS
    )

    last_status = ""

    while time.time() < deadline:

        deployment = railway_deployment(
            deployment_id
        )

        if not deployment:

            time.sleep(
                POLL_SECONDS
            )

            continue

        status = clean_text(
            deployment.get(
                "status"
            ),
            100
        ).upper()

        if (
            status
            and
            status
            !=
            last_status
        ):
            print(
                (
                    "🚆 Railway deployment | "
                    +
                    deployment_id
                    +
                    " | "
                    +
                    status
                )
            )

            last_status = status

        if status in DEPLOY_SUCCESS_STATUSES:

            return deployment

        if status in DEPLOY_FAILURE_STATUSES:

            raise RuntimeError(
                (
                    "Railway deployment ended with "
                    +
                    status
                )
            )

        time.sleep(
            POLL_SECONDS
        )

    raise RuntimeError(
        (
            "Railway deployment verification timed out "
            "before SUCCESS."
        )
    )


# =========================================================
# HTTP HEALTH
# =========================================================

def http_json(
    url,
    timeout=20
):
    request = urllib.request.Request(
        url,
        method="GET",
        headers={
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

    with urllib.request.urlopen(
        request,
        timeout=timeout
    ) as response:

        body = response.read()

        status = int(
            response.status
        )

    data = json.loads(
        body.decode(
            "utf-8"
        )
    )

    return (
        status,
        data
    )


def wait_for_health(
    domain,
    expected_slug,
    expected_name
):
    domain = clean_text(
        domain,
        1000
    )

    if not domain:
        raise RuntimeError(
            "Health domain missing."
        )

    if domain.startswith(
        "http://"
    ) or domain.startswith(
        "https://"
    ):
        base_url = domain.rstrip(
            "/"
        )

    else:
        base_url = (
            "https://"
            +
            domain.rstrip(
                "/"
            )
        )

    health_url = (
        base_url
        +
        CALL_HEALTH_PATH
    )

    deadline = (
        time.time()
        +
        HEALTH_TIMEOUT_SECONDS
    )

    last_error = None

    while time.time() < deadline:

        try:
            status_code, data = http_json(
                health_url,
                timeout=20
            )

            if (
                status_code
                ==
                200
                and
                data.get(
                    "ok"
                )
                is True
            ):

                returned_slug = normalize_text(
                    data.get(
                        "agentId"
                    )
                )

                expected_slug_normalized = normalize_text(
                    expected_slug
                )

                if (
                    returned_slug
                    !=
                    expected_slug_normalized
                ):
                    raise RuntimeError(
                        (
                            "Health agentId mismatch. "
                            "Expected "
                            +
                            expected_slug
                            +
                            ", got "
                            +
                            clean_text(
                                data.get(
                                    "agentId"
                                )
                            )
                        )
                    )

                if (
                    data.get(
                        "isolatedSecrets"
                    )
                    is not True
                ):
                    raise RuntimeError(
                        "Health did not confirm isolatedSecrets."
                    )

                if (
                    data.get(
                        "kemoPersonalMemory"
                    )
                    is not False
                ):
                    raise RuntimeError(
                        (
                            "Health did not confirm "
                            "Kemo personal memory isolation."
                        )
                    )

                if (
                    data.get(
                        "telegramConfigured"
                    )
                    is not True
                ):
                    raise RuntimeError(
                        "Telegram is not configured."
                    )

                if (
                    data.get(
                        "geminiConfigured"
                    )
                    is not True
                ):
                    raise RuntimeError(
                        "Gemini is not configured."
                    )

                if (
                    data.get(
                        "databaseConfigured"
                    )
                    is not True
                ):
                    raise RuntimeError(
                        "Agent database is not configured."
                    )

                if (
                    data.get(
                        "callSecretConfigured"
                    )
                    is not True
                ):
                    raise RuntimeError(
                        "Agent call secret is not configured."
                    )

                return {
                    "url":
                        base_url,

                    "healthUrl":
                        health_url,

                    "data":
                        data,
                }

        except Exception as error:
            last_error = error

        time.sleep(
            POLL_SECONDS
        )

    raise RuntimeError(
        (
            "Health verification failed: "
            +
            clean_text(
                last_error,
                1000
            )
        )
    )


# =========================================================
# TELEGRAM CALL BUTTON
# =========================================================

def configure_child_call_button(
    child_token,
    owner_user_id,
    agent_name,
    call_url
):
    button_text = (
        "📞 مكالمة "
        +
        clean_text(
            agent_name,
            40
        )
    )[:64]

    telegram_api(
        child_token,
        "setChatMenuButton",
        {
            "chat_id":
                int(
                    owner_user_id
                ),

            "menu_button": {
                "type":
                    "web_app",

                "text":
                    button_text,

                "web_app": {
                    "url":
                        call_url
                },
            }
        }
    )

    telegram_api(
        child_token,
        "sendMessage",
        {
            "chat_id":
                int(
                    owner_user_id
                ),

            "text":
                (
                    "📞 ميزة المكالمة المباشرة جاهزة للتجربة.\n\n"
                    "اضغط الزر واعمل أول مكالمة حقيقية."
                ),

            "reply_markup": {
                "inline_keyboard": [
                    [
                        {
                            "text":
                                button_text,

                            "web_app": {
                                "url":
                                    call_url
                            }
                        }
                    ]
                ]
            }
        }
    )

    return True


# =========================================================
# OPTIONAL CAPABILITY REGISTRY SYNC
# =========================================================

def try_sync_capability(
    agent_row,
    status,
    config=None,
    verified=False
):
    config = (
        config
        if isinstance(
            config,
            dict
        )
        else
        {}
    )

    possible_functions = [
        "set_agent_capability",
        "save_agent_capability",
        "upsert_agent_capability",
        "set_capability",
    ]

    for name in possible_functions:

        fn = getattr(
            capabilities,
            name,
            None
        )

        if not callable(
            fn
        ):
            continue

        attempts = [
            lambda:
                fn(
                    agent_row,
                    "live_call",
                    enabled=True,
                    status=status,
                    config=config,
                    verified=verified
                ),

            lambda:
                fn(
                    agent_row,
                    "live_call",
                    True,
                    status,
                    config
                ),
        ]

        for attempt in attempts:

            try:
                attempt()

                return True

            except TypeError:
                continue

            except Exception as error:

                print(
                    (
                        "⚠️ Capability sync: "
                        +
                        str(
                            error
                        )
                    )
                )

                return False

    return False


# =========================================================
# REAL CALL VERIFICATION
# =========================================================

def verify_real_call_from_agent_db(
    agent_slug,
    agent_database_url
):
    if not agent_database_url:
        return {
            "verified":
                False,

            "reason":
                "agent database missing",
        }

    try:
        with db_connect(
            agent_database_url
        ) as conn:

            row = fetch_one_dict(
                conn,
                """
                SELECT
                    transcript,
                    started_at,
                    ended_at

                FROM
                    agent_call_sessions

                WHERE
                    agent_id = %s
                    AND status = 'ended'

                ORDER BY
                    ended_at DESC

                LIMIT 1;
                """,
                (
                    agent_slug,
                )
            )

    except Exception as error:

        return {
            "verified":
                False,

            "reason":
                clean_text(
                    error,
                    1000
                ),
        }

    if not row:

        return {
            "verified":
                False,

            "reason":
                "no ended call found",
        }

    transcript = row.get(
        "transcript"
    )

    if isinstance(
        transcript,
        str
    ):
        try:
            transcript = json.loads(
                transcript
            )
        except Exception:
            transcript = []

    if not isinstance(
        transcript,
        list
    ):
        transcript = []

    user_turns = [
        item
        for item
        in transcript
        if (
            isinstance(
                item,
                dict
            )
            and
            item.get(
                "role"
            )
            ==
            "user"
            and
            clean_text(
                item.get(
                    "text"
                )
            )
        )
    ]

    assistant_turns = [
        item
        for item
        in transcript
        if (
            isinstance(
                item,
                dict
            )
            and
            item.get(
                "role"
            )
            ==
            "assistant"
            and
            clean_text(
                item.get(
                    "text"
                )
            )
        )
    ]

    verified = bool(
        user_turns
        and
        assistant_turns
    )

    return {
        "verified":
            verified,

        "turns":
            len(
                transcript
            ),

        "userTurns":
            len(
                user_turns
            ),

        "assistantTurns":
            len(
                assistant_turns
            ),

        "endedAt":
            str(
                row.get(
                    "ended_at"
                )
                or
                ""
            ),

        "reason":
            (
                "real transcript found"
                if verified
                else
                "ended call has no real two-way transcript"
            ),
    }


# =========================================================
# INSTALL LIVE CALL
# =========================================================

def install_live_call(
    owner_user_id,
    resolved
):
    profile = (
        resolved.get(
            "profile"
        )
        or
        {}
    )

    agent_row = resolved.get(
        "row"
    )

    agent_slug = clean_text(
        profile.get(
            "slug"
        ),
        100
    )

    agent_name = clean_text(
        profile.get(
            "name"
        )
        or
        agent_slug,
        300
    )

    bot_username = clean_text(
        profile.get(
            "username"
        ),
        300
    )

    system_prompt = clean_text(
        profile.get(
            "prompt"
        ),
        60000
    )

    if not agent_slug:
        raise RuntimeError(
            "Agent slug missing."
        )

    if not system_prompt:
        raise RuntimeError(
            (
                "ملف system_prompt.md لهذا الوكيل "
                "مش موجود أو فاضي."
            )
        )

    init_call_registry()

    existing = get_call_registry(
        owner_user_id,
        agent_slug
    )

    if (
        existing
        and
        existing.get(
            "status"
        )
        ==
        "verified"
        and
        existing.get(
            "railway_domain"
        )
    ):
        return {
            "alreadyVerified":
                True,

            "agentSlug":
                agent_slug,

            "agentName":
                agent_name,

            "url":
                (
                    "https://"
                    +
                    clean_text(
                        existing.get(
                            "railway_domain"
                        )
                    ).replace(
                        "https://",
                        ""
                    )
                ),
        }

    agent_secrets = load_agent_runtime_secrets(
        agent_slug
    )

    prefix = agent_secrets[
        "prefix"
    ]

    missing = []

    if not railway_token():
        missing.append(
            "RAILWAY_API_TOKEN"
        )

    if not agent_secrets[
        "gemini_api_key"
    ]:
        missing.append(
            (
                prefix
                +
                "_GEMINI_API_KEY"
            )
        )

    if not agent_secrets[
        "database_url"
    ]:
        missing.append(
            (
                prefix
                +
                "_DATABASE_URL"
            )
        )

    if missing:

        update_call_registry(
            owner_user_id,
            agent_slug,
            agent_name=agent_name,
            bot_username=bot_username,
            agent_db_id=(
                agent_db_id(
                    agent_row
                )
                if agent_row
                else
                ""
            ),
            status="blocked_missing_secrets",
            last_error=(
                "Missing: "
                +
                ", ".join(
                    missing
                )
            ),
        )

        return {
            "blocked":
                True,

            "agentSlug":
                agent_slug,

            "agentName":
                agent_name,

            "missing":
                missing,
        }

    managed_bot = fetch_managed_bot_token(
        agent_row
    )

    if managed_bot.get(
        "username"
    ):
        bot_username = managed_bot[
            "username"
        ]

    update_call_registry(
        owner_user_id,
        agent_slug,
        agent_name=agent_name,
        bot_username=bot_username,
        agent_db_id=(
            agent_db_id(
                agent_row
            )
            if agent_row
            else
            ""
        ),
        status="provisioning",
        last_error=None,
    )

    print(
        (
            "📞 LIVE CALL PROVISION | "
            +
            agent_name
            +
            " | STARTED"
        )
    )

    project_name = (
        slugify(
            agent_slug
        )
        +
        "-agent"
    )

    service_name = (
        slugify(
            agent_slug
        )
        +
        "-call"
    )

    project_id = clean_text(
        (
            existing
            or
            {}
        ).get(
            "railway_project_id"
        ),
        300
    )

    project = None

    if project_id:
        try:
            project = railway_get_project(
                project_id
            )
        except Exception:
            project = None

    if not project:

        project = railway_find_project_by_name(
            project_name
        )

    if not project:

        project = railway_create_project(
            project_name
        )

    project_id = clean_text(
        project.get(
            "id"
        ),
        300
    )

    if not project_id:
        raise RuntimeError(
            "Railway project ID missing."
        )

    update_call_registry(
        owner_user_id,
        agent_slug,
        railway_project_id=project_id,
        status="project_ready",
    )

    environment = railway_get_or_create_environment(
        project_id
    )

    environment_id = clean_text(
        environment.get(
            "id"
        ),
        300
    )

    if not environment_id:
        raise RuntimeError(
            "Railway environment ID missing."
        )

    update_call_registry(
        owner_user_id,
        agent_slug,
        railway_environment_id=environment_id,
        status="environment_ready",
    )

    service_id = clean_text(
        (
            existing
            or
            {}
        ).get(
            "railway_service_id"
        ),
        300
    )

    service = None

    if service_id:
        try:
            service = railway_find_service(
                project_id,
                service_name
            )

            if (
                service
                and
                clean_text(
                    service.get(
                        "id"
                    )
                )
                !=
                service_id
            ):
                service = None

        except Exception:
            service = None

    if not service:

        service = railway_find_service(
            project_id,
            service_name
        )

    if not service:

        service = railway_create_call_service(
            project_id,
            environment_id,
            service_name
        )

    service_id = clean_text(
        service.get(
            "id"
        ),
        300
    )

    if not service_id:
        raise RuntimeError(
            "Railway service ID missing."
        )

    update_call_registry(
        owner_user_id,
        agent_slug,
        railway_service_id=service_id,
        status="service_ready",
    )

    railway_configure_service(
        service_id,
        environment_id
    )

    update_call_registry(
        owner_user_id,
        agent_slug,
        status="service_configured",
    )

    call_secret = secrets.token_urlsafe(
        48
    )

    variables = {
        "AGENT_ID":
            agent_slug,

        "AGENT_NAME":
            agent_name,

        "AGENT_SECRET_PREFIX":
            prefix,

        (
            prefix
            +
            "_TELEGRAM_BOT_TOKEN"
        ):
            managed_bot[
                "token"
            ],

        (
            prefix
            +
            "_TELEGRAM_ALLOWED_USER_ID"
        ):
            str(
                int(
                    owner_user_id
                )
            ),

        (
            prefix
            +
            "_GEMINI_API_KEY"
        ):
            agent_secrets[
                "gemini_api_key"
            ],

        (
            prefix
            +
            "_DATABASE_URL"
        ):
            agent_secrets[
                "database_url"
            ],

        (
            prefix
            +
            "_CALL_SECRET"
        ):
            call_secret,

        (
            prefix
            +
            "_SYSTEM_PROMPT"
        ):
            system_prompt,

        (
            prefix
            +
            "_TIMEZONE"
        ):
            (
                agent_secrets[
                    "timezone"
                ]
                or
                "Asia/Hebron"
            ),

        (
            prefix
            +
            "_LIVE_MODEL"
        ):
            (
                agent_secrets[
                    "live_model"
                ]
                or
                "gemini-3.1-flash-live-preview"
            ),

        (
            prefix
            +
            "_VOICE"
        ):
            (
                agent_secrets[
                    "voice"
                ]
                or
                "Iapetus"
            ),
    }

    if agent_secrets[
        "tavily_api_key"
    ]:

        variables[
            (
                prefix
                +
                "_TAVILY_API_KEY"
            )
        ] = agent_secrets[
            "tavily_api_key"
        ]

    railway_set_variables(
        project_id,
        environment_id,
        service_id,
        variables
    )

    update_call_registry(
        owner_user_id,
        agent_slug,
        status="variables_configured",
    )

    domain = railway_get_or_create_domain(
        project_id,
        environment_id,
        service_id
    )

    domain = clean_text(
        domain,
        1000
    )

    update_call_registry(
        owner_user_id,
        agent_slug,
        railway_domain=domain,
        status="domain_ready",
    )

    deployment_id = railway_trigger_deploy(
        service_id,
        environment_id
    )

    update_call_registry(
        owner_user_id,
        agent_slug,
        railway_deployment_id=deployment_id,
        status="deploying",
    )

    deployment = wait_for_deployment(
        deployment_id
    )

    update_call_registry(
        owner_user_id,
        agent_slug,
        status="deployment_success",
    )

    health = wait_for_health(
        domain,
        agent_slug,
        agent_name
    )

    update_call_registry(
        owner_user_id,
        agent_slug,
        status="health_verified",
        health_json=health[
            "data"
        ],
    )

    configure_child_call_button(
        managed_bot[
            "token"
        ],
        owner_user_id,
        agent_name,
        health[
            "url"
        ]
    )

    update_call_registry(
        owner_user_id,
        agent_slug,
        status="ready_for_real_test",
        last_error=None,
    )

    try_sync_capability(
        agent_row,
        status="ready_for_real_test",
        verified=False,
        config={
            "url":
                health[
                    "url"
                ],

            "railwayProjectId":
                project_id,

            "railwayServiceId":
                service_id,

            "deploymentId":
                deployment_id,

            "isolatedSecrets":
                True,
        }
    )

    print(
        (
            "✅ LIVE CALL READY FOR REAL TEST | "
            +
            agent_name
            +
            " | "
            +
            health[
                "url"
            ]
        )
    )

    return {
        "ok":
            True,

        "alreadyVerified":
            False,

        "agentSlug":
            agent_slug,

        "agentName":
            agent_name,

        "botUsername":
            bot_username,

        "projectId":
            project_id,

        "environmentId":
            environment_id,

        "serviceId":
            service_id,

        "deploymentId":
            deployment_id,

        "deploymentStatus":
            deployment.get(
                "status"
            ),

        "url":
            health[
                "url"
            ],

        "health":
            health[
                "data"
            ],

        "status":
            "ready_for_real_test",
    }


# =========================================================
# VERIFY CAPABILITY AFTER REAL CALL
# =========================================================

def verify_live_call(
    owner_user_id,
    resolved
):
    profile = (
        resolved.get(
            "profile"
        )
        or
        {}
    )

    agent_row = resolved.get(
        "row"
    )

    agent_slug = clean_text(
        profile.get(
            "slug"
        ),
        100
    )

    agent_name = clean_text(
        profile.get(
            "name"
        )
        or
        agent_slug,
        300
    )

    if not agent_slug:
        raise RuntimeError(
            "Agent slug missing."
        )

    init_call_registry()

    registry = get_call_registry(
        owner_user_id,
        agent_slug
    )

    if not registry:
        return {
            "installed":
                False,

            "verified":
                False,

            "agentName":
                agent_name,
        }

    agent_secrets = load_agent_runtime_secrets(
        agent_slug
    )

    result = verify_real_call_from_agent_db(
        agent_slug,
        agent_secrets[
            "database_url"
        ]
    )

    if result.get(
        "verified"
    ):

        update_call_registry(
            owner_user_id,
            agent_slug,
            status="verified",
            verified_at=datetime.now(
                timezone.utc
            ),
            last_error=None,
        )

        try_sync_capability(
            agent_row,
            status="verified",
            verified=True,
            config={
                "url":
                    (
                        "https://"
                        +
                        clean_text(
                            registry.get(
                                "railway_domain"
                            )
                        ).replace(
                            "https://",
                            ""
                        )
                    ),

                "realCall":
                    result,
            }
        )

    return {
        "installed":
            True,

        "verified":
            bool(
                result.get(
                    "verified"
                )
            ),

        "agentName":
            agent_name,

        "registry":
            registry,

        "realCall":
            result,
    }


# =========================================================
# COMMAND DETECTION
# =========================================================

CALL_MARKERS = [
    "مكالمة",
    "المكالمة",
    "اتصال مباشر",
    "الاتصال المباشر",
    "اتصال صوتي",
    "الاتصال الصوتي",
    "محادثة مباشرة",
    "محادثة صوتية",
    "live call",
    "voice call",
    "call feature",
]


INSTALL_MARKERS = [
    "ضيف",
    "اضف",
    "ركب",
    "ثبت",
    "فعل",
    "فعّل",
    "شغل",
    "بدي",
    "خليه",
    "خلي",
    "اعطيه",
    "اعطية",
]


STATUS_MARKERS = [
    "حالة",
    "الحالة",
    "status",
    "شو صار",
    "جاهز",
    "شغال",
]


VERIFY_MARKERS = [
    "تحقق",
    "تأكد",
    "تاكد",
    "افحص",
    "اختبر",
    "verify",
    "verified",
]


def is_call_related(
    text
):
    return contains_any(
        text,
        CALL_MARKERS
    )


def is_call_install_command(
    text
):
    return (
        is_call_related(
            text
        )
        and
        contains_any(
            text,
            INSTALL_MARKERS
        )
    )


def is_call_status_command(
    text
):
    return (
        is_call_related(
            text
        )
        and
        contains_any(
            text,
            STATUS_MARKERS
            +
            VERIFY_MARKERS
        )
    )


# =========================================================
# HUMAN ANSWERS
# =========================================================

def missing_secrets_answer(
    result
):
    missing = (
        result.get(
            "missing"
        )
        or
        []
    )

    return (
        "لقيت "
        +
        result[
            "agentName"
        ]
        +
        " ✅\n\n"
        +
        "بس ما بلشت إنشاء خدمة المكالمة، "
        +
        "لأنه ناقص مفاتيح لازمة للفصل الآمن:\n\n"
        +
        "\n".join(
            (
                "• "
                +
                item
            )
            for item
            in missing
        )
        +
        "\n\n"
        +
        "ما استخدمت مفاتيح Kemo كبديل، "
        +
        "عشان نظل محافظين على عزل كل وكيل."
    )


def ready_test_answer(
    result
):
    return (
        "جهزت البنية الفعلية لمكالمة "
        +
        result[
            "agentName"
        ]
        +
        " ✅\n\n"
        +
        "• Railway deployment: SUCCESS\n"
        +
        "• Health check: PASS\n"
        +
        "• Secrets: خاصة بالوكيل\n"
        +
        "• ذاكرة Kemo: غير مربوطة\n"
        +
        "• زر المكالمة: انضاف على Telegram\n\n"
        +
        "📞 هسّا اعمل مكالمة حقيقية معه من الزر.\n\n"
        +
        "مهم: لسه ما بسمي ميزة المكالمة "
        +
        "Verified لحد ما يصير اختبار صوتي فعلي "
        +
        "ويظهر User + Agent transcript."
    )


def verified_answer(
    result
):
    if result.get(
        "verified"
    ):

        real_call = (
            result.get(
                "realCall"
            )
            or
            {}
        )

        return (
            "✅ مكالمة "
            +
            result[
                "agentName"
            ]
            +
            " صارت Verified فعليًا.\n\n"
            +
            "لقيت مكالمة منتهية فيها "
            +
            str(
                real_call.get(
                    "userTurns",
                    0
                )
            )
            +
            " جزء كلام منك و "
            +
            str(
                real_call.get(
                    "assistantTurns",
                    0
                )
            )
            +
            " رد من الوكيل.\n\n"
            +
            "الحالة: LIVE CALL VERIFIED ✅"
        )

    if not result.get(
        "installed"
    ):

        return (
            "ميزة المكالمة مش مركبة لهذا الوكيل لسه."
        )

    reason = clean_text(
        (
            result.get(
                "realCall"
            )
            or
            {}
        ).get(
            "reason"
        ),
        500
    )

    return (
        "خدمة المكالمة مركبة، "
        +
        "بس لسه ما عندي دليل على مكالمة صوتية "
        +
        "ثنائية ناجحة.\n\n"
        +
        "الحالة: READY FOR REAL TEST\n"
        +
        (
            "التحقق: "
            +
            reason
            if reason
            else
            ""
        )
    )


# =========================================================
# MANAGER COMMAND ROUTER
# =========================================================

def handle_call_manager_command(
    chat_id,
    user_id,
    user_message
):
    text = clean_text(
        user_message,
        10000
    )

    if not is_call_related(
        text
    ):
        return None

    resolved = resolve_target_agent(
        text
    )

    if not resolved:
        return None

    if is_call_status_command(
        text
    ):

        try:
            result = verify_live_call(
                user_id,
                resolved
            )

            return verified_answer(
                result
            )

        except Exception as error:

            print(
                (
                    "❌ Call verify: "
                    +
                    str(
                        error
                    )
                )
            )

            return (
                "قدرت أحدد الوكيل، "
                "بس فشل فحص المكالمة:\n"
                +
                clean_text(
                    error,
                    1000
                )
            )

    if not is_call_install_command(
        text
    ):
        return None

    try:

        result = install_live_call(
            user_id,
            resolved
        )

        if result.get(
            "blocked"
        ):

            return missing_secrets_answer(
                result
            )

        if result.get(
            "alreadyVerified"
        ):

            return (
                "ميزة المكالمة على "
                +
                result[
                    "agentName"
                ]
                +
                " Verified من قبل ✅\n"
                +
                result[
                    "url"
                ]
            )

        return ready_test_answer(
            result
        )

    except Exception as error:

        profile = (
            resolved.get(
                "profile"
            )
            or
            {}
        )

        agent_slug = clean_text(
            profile.get(
                "slug"
            ),
            100
        )

        agent_name = clean_text(
            profile.get(
                "name"
            )
            or
            agent_slug,
            300
        )

        print(
            (
                "❌ LIVE CALL PROVISION FAILED | "
                +
                agent_name
                +
                " | "
                +
                str(
                    error
                )
            )
        )

        if agent_slug:

            try:
                update_call_registry(
                    user_id,
                    agent_slug,
                    agent_name=agent_name,
                    status="failed",
                    last_error=clean_text(
                        error,
                        3000
                    ),
                )

            except Exception:
                pass

        return (
            "ما رح أحكيلك إنها تركبت، "
            "لأن التجهيز فشل فعليًا.\n\n"
            "السبب:\n"
            +
            clean_text(
                error,
                1500
            )
        )


# =========================================================
# WRAP EXISTING KEMO BRAIN
# =========================================================

ORIGINAL_ASK_KEMO = (
    kemo.ask_kemo
)


def ask_kemo_with_call_provisioner(
    chat_id,
    user_id,
    user_message
):
    try:

        answer = handle_call_manager_command(
            chat_id,
            user_id,
            user_message
        )

    except Exception as error:

        print(
            (
                "❌ Call provisioner router: "
                +
                str(
                    error
                )
            )
        )

        answer = None

    if answer is not None:
        return answer

    return ORIGINAL_ASK_KEMO(
        chat_id,
        user_id,
        user_message
    )


kemo.ask_kemo = (
    ask_kemo_with_call_provisioner
)


# =========================================================
# STARTUP PREFLIGHT
# =========================================================

def startup_preflight():
    checks = {
        "database":
            bool(
                get_database_url()
            ),

        "railwayToken":
            bool(
                railway_token()
            ),

        "managerTelegramToken":
            bool(
                manager_bot_token()
            ),

        "callTemplate":
            (
                BASE_DIR
                /
                "agent_templates"
                /
                "live_call"
                /
                "server.js"
            ).exists(),

        "callTemplatePackage":
            (
                BASE_DIR
                /
                "agent_templates"
                /
                "live_call"
                /
                "package.json"
            ).exists(),

        "agentsFolder":
            AGENTS_DIR.exists(),
    }

    return checks


# =========================================================
# MAIN
# =========================================================

def main():

    print("")

    print(
        "=============================================="
    )

    print(
        " KEMO AGENT FACTORY CALL PROVISIONER V1.0"
    )

    print(
        "=============================================="
    )

    checks = startup_preflight()

    print(
        (
            "✅ Database: "
            +
            (
                "READY"
                if checks[
                    "database"
                ]
                else
                "MISSING"
            )
        )
    )

    print(
        (
            "✅ Railway Factory Token: "
            +
            (
                "READY"
                if checks[
                    "railwayToken"
                ]
                else
                "MISSING"
            )
        )
    )

    print(
        (
            "✅ Manager Telegram Token: "
            +
            (
                "READY"
                if checks[
                    "managerTelegramToken"
                ]
                else
                "MISSING"
            )
        )
    )

    print(
        (
            "✅ Live Call Template: "
            +
            (
                "READY"
                if (
                    checks[
                        "callTemplate"
                    ]
                    and
                    checks[
                        "callTemplatePackage"
                    ]
                )
                else
                "MISSING"
            )
        )
    )

    print(
        (
            "✅ Agent Profiles: "
            +
            (
                "READY"
                if checks[
                    "agentsFolder"
                ]
                else
                "MISSING"
            )
        )
    )

    try:

        init_call_registry()

        print(
            "✅ Call deployment registry: READY"
        )

    except Exception as error:

        print(
            (
                "⚠️ Call deployment registry: "
                +
                str(
                    error
                )
            )
        )

    print(
        "✅ Natural live-call command router: ONLINE"
    )

    print(
        "✅ Per-agent Gemini isolation enforced"
    )

    print(
        "✅ Per-agent Telegram token isolation enforced"
    )

    print(
        "✅ Per-agent database isolation enforced by default"
    )

    print(
        "✅ Deployment SUCCESS required"
    )

    print(
        "✅ Health verification required"
    )

    print(
        "✅ Real call required before VERIFIED"
    )

    print(
        "🔒 Kemo secrets are never used as agent fallback"
    )

    print("")

    profiles.main()


# =========================================================
# ENTRY
# =========================================================

if __name__ == "__main__":
    main()
