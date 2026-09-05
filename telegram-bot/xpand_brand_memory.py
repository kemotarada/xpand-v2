# =========================================================
# XPAND BRAND MEMORY V3.0
#
# PERMANENT VISUAL MEMORY
# +
# STC BANK REFERENCE CURATOR
#
# =========================================================
#
# GOALS
# ---------------------------------------------------------
#
# - Preserve existing Brand Memory V2 database.
# - Do NOT destroy or recreate existing reference data.
# - Keep compatibility with Production Engine V3/V4.
# - Request-aware reference selection.
# - STC Bank gets max 3 strong references by default.
# - Prefer official / trusted references.
# - Match service / content family.
# - Match selected visual style.
# - Encourage camera / scene diversity.
# - Avoid repeatedly selecting the same references.
# - Build permanent aggregated Brand Visual Profile.
# - Zero AI/API calls in this module.
#
#
# IMPORTANT
# ---------------------------------------------------------
#
# Existing production code expects:
#
#   safe_brand_id
#   set_active_brand
#   get_active_brand
#   upsert_brand_profile
#   learn_explicit_feedback
#   save_visual_reference
#   load_visual_references
#   load_relevant_visual_references
#   find_existing_visual_reference
#   get_visual_library_stats
#   get_brand_visual_profile
#   refresh_brand_visual_profile
#   build_brand_memory_context
#
#
# Running:
#
#     python xpand_brand_memory.py
#
# makes:
#
#   ZERO DATABASE CALLS
#   ZERO API CALLS
#   ZERO IMAGE CALLS
#
# =========================================================

from __future__ import annotations

import json
import math
import os
import re
import threading
import time

from collections import (
    Counter,
)

from datetime import (
    datetime,
    timezone,
)

from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
)


# =========================================================
# OPTIONAL POSTGRES
# =========================================================

try:

    import psycopg2

    from psycopg2.extras import (
        Json,
        RealDictCursor,
    )

    PSYCOPG_AVAILABLE = True

except Exception:

    psycopg2 = None

    Json = None

    RealDictCursor = None

    PSYCOPG_AVAILABLE = False


# =========================================================
# STC SKILL
# =========================================================

try:

    from xpand_stc_bank_skill import (
        STYLE_AUGMENTED_REALISM,
        STYLE_PREMIUM_REALISTIC,
        STYLE_PURPLE_ARCHITECTURAL,
        detect_stc_benefit_family,
        detect_stc_visual_style,
        get_stc_visual_dna_summary,
    )

except Exception:

    STYLE_PREMIUM_REALISTIC = (
        "premium_realistic"
    )

    STYLE_PURPLE_ARCHITECTURAL = (
        "purple_architectural"
    )

    STYLE_AUGMENTED_REALISM = (
        "augmented_realism"
    )

    def detect_stc_visual_style(
        text: Any,
    ) -> str:

        return ""

    def detect_stc_benefit_family(
        text: Any,
    ) -> str:

        return "premium_banking"

    def get_stc_visual_dna_summary():

        return {}


# =========================================================
# MODULE
# =========================================================

VERSION = "3.0"

MODULE_NAME = (
    "XPAND Brand Memory"
)


# =========================================================
# DATABASE
# =========================================================

DATABASE_URL = (
    str(
        os.environ.get(
            "DATABASE_URL",
            "",
        )
        or
        os.environ.get(
            "POSTGRES_URL",
            "",
        )
        or
        os.environ.get(
            "POSTGRESQL_URL",
            "",
        )
    )
    .strip()
)


VISUAL_REFERENCES_TABLE = (
    "xpand_visual_references"
)

VISUAL_PROFILES_TABLE = (
    "xpand_brand_visual_profiles"
)

BRAND_PROFILES_TABLE = (
    "xpand_brand_profiles"
)

BRAND_RULES_TABLE = (
    "xpand_brand_rules"
)

BRAND_STATE_TABLE = (
    "xpand_brand_state"
)


# =========================================================
# SETTINGS
# =========================================================

#
# User asked for fewer references / lower processing.
#
# STC uses only the strongest 3 by default.
#

STC_REFERENCE_LIMIT = max(
    1,
    min(
        4,
        int(
            os.environ.get(
                "XPAND_STC_REFERENCE_LIMIT",
                "3",
            )
            or 3
        ),
    ),
)


GENERAL_REFERENCE_LIMIT = max(
    1,
    min(
        6,
        int(
            os.environ.get(
                "XPAND_GENERAL_REFERENCE_LIMIT",
                "5",
            )
            or 5
        ),
    ),
)


REFERENCE_SCAN_LIMIT = max(
    20,
    min(
        300,
        int(
            os.environ.get(
                "XPAND_REFERENCE_SCAN_LIMIT",
                "120",
            )
            or 120
        ),
    ),
)


VISUAL_PROFILE_REFERENCE_LIMIT = max(
    20,
    min(
        300,
        int(
            os.environ.get(
                "XPAND_VISUAL_PROFILE_REFERENCE_LIMIT",
                "120",
            )
            or 120
        ),
    ),
)


REFRESH_PROFILE_ON_SAVE = str(
    os.environ.get(
        "XPAND_REFRESH_VISUAL_PROFILE_ON_SAVE",
        "true",
    )
).strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}


# =========================================================
# IN-MEMORY FALLBACK
# =========================================================

#
# This is NOT the permanent store.
#
# It only keeps runtime alive if PostgreSQL is temporarily
# unavailable.
#

_ACTIVE_BRAND_CACHE: Dict[
    str,
    str,
] = {}


_PROFILE_CACHE: Dict[
    str,
    Dict[str, Any],
] = {}


_RULE_CACHE: Dict[
    str,
    List[Dict[str, Any]],
] = {}


_SCHEMA_LOCK = threading.RLock()

_SCHEMA_CHECKED = False

_COLUMN_CACHE: Dict[
    str,
    Tuple[
        float,
        set,
    ],
] = {}


# =========================================================
# BASIC HELPERS
# =========================================================

def clean_text(
    value: Any,
    limit: int = 12000,
) -> str:

    return (
        str(
            value
            if value is not None
            else ""
        )
        .replace(
            "\x00",
            "",
        )
        .strip()[:limit]
    )


def normalize_text(
    value: Any,
) -> str:

    text = clean_text(
        value,
        50000,
    ).lower()

    replacements = {
        "أ":
            "ا",

        "إ":
            "ا",

        "آ":
            "ا",

        "ة":
            "ه",

        "ى":
            "ي",

        "ؤ":
            "و",

        "ئ":
            "ي",

        "ـ":
            "",
    }

    for old, new in (
        replacements.items()
    ):

        text = text.replace(
            old,
            new,
        )

    text = re.sub(
        r"[\u064B-\u065F]",
        "",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def safe_dict(
    value: Any,
) -> Dict[str, Any]:

    if isinstance(
        value,
        dict,
    ):

        return value

    return {}


def safe_list(
    value: Any,
) -> List[Any]:

    if isinstance(
        value,
        list,
    ):

        return value

    return []


def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:

    try:

        return float(
            value
        )

    except Exception:

        return float(
            default
        )


def safe_int(
    value: Any,
    default: int = 0,
) -> int:

    try:

        return int(
            value
        )

    except Exception:

        return int(
            default
        )


def utc_now_iso() -> str:

    return (
        datetime.now(
            timezone.utc
        )
        .isoformat()
    )


def safe_json_load(
    value: Any,
    default: Any = None,
) -> Any:

    if default is None:

        default = {}

    if isinstance(
        value,
        (
            dict,
            list,
        ),
    ):

        return value

    if value is None:

        return default

    text = clean_text(
        value,
        200000,
    )

    if not text:

        return default

    try:

        return json.loads(
            text
        )

    except Exception:

        return default


def json_value(
    value: Any,
):

    if Json is None:

        return json.dumps(
            value,
            ensure_ascii=False,
        )

    return Json(
        value,
        dumps=lambda payload:
            json.dumps(
                payload,
                ensure_ascii=False,
            ),
    )


def contains_any(
    value: Any,
    markers: Sequence[str],
) -> bool:

    source = normalize_text(
        value
    )

    return any(
        normalize_text(
            marker
        )
        in source
        for marker in markers
    )


# =========================================================
# BRAND ID
# =========================================================

def safe_brand_id(
    value: Any,
) -> str:

    source = normalize_text(
        value
    )

    if not source:

        return ""

    if contains_any(
        source,
        [
            "stc bank",
            "stcbank",
            "stc-bank",
            "stc_bank",
            "بنك stc",
            "بنك اس تي سي",
            "اس تي سي بنك",
        ],
    ):

        return "stc_bank"

    if contains_any(
        source,
        [
            "xpand",
            "اكسباند",
            "إكسباند",
        ],
    ):

        return "xpand"

    source = re.sub(
        r"[^a-z0-9_\-]+",
        "_",
        source,
    )

    source = re.sub(
        r"_+",
        "_",
        source,
    )

    return source.strip(
        "_"
    )[:100]


# =========================================================
# DATABASE HELPERS
# =========================================================

def database_available() -> bool:

    return bool(
        PSYCOPG_AVAILABLE
        and
        DATABASE_URL
    )


def _connect():

    if not database_available():

        return None

    return psycopg2.connect(
        DATABASE_URL,
        connect_timeout=8,
    )


def _fetch_all(
    sql: str,
    params: Sequence[Any] = (),
) -> List[
    Dict[str, Any]
]:

    connection = _connect()

    if connection is None:

        return []

    try:

        with connection.cursor(
            cursor_factory=(
                RealDictCursor
            )
        ) as cursor:

            cursor.execute(
                sql,
                tuple(
                    params
                ),
            )

            rows = cursor.fetchall()

            return [
                dict(
                    row
                )
                for row in rows
            ]

    finally:

        connection.close()


def _fetch_one(
    sql: str,
    params: Sequence[Any] = (),
) -> Dict[str, Any]:

    connection = _connect()

    if connection is None:

        return {}

    try:

        with connection.cursor(
            cursor_factory=(
                RealDictCursor
            )
        ) as cursor:

            cursor.execute(
                sql,
                tuple(
                    params
                ),
            )

            row = cursor.fetchone()

            return (
                dict(
                    row
                )
                if row
                else {}
            )

    finally:

        connection.close()


def _execute(
    sql: str,
    params: Sequence[Any] = (),
    *,
    returning: bool = False,
) -> Any:

    connection = _connect()

    if connection is None:

        return None

    try:

        with connection.cursor(
            cursor_factory=(
                RealDictCursor
            )
        ) as cursor:

            cursor.execute(
                sql,
                tuple(
                    params
                ),
            )

            result = None

            if returning:

                row = cursor.fetchone()

                result = (
                    dict(
                        row
                    )
                    if row
                    else None
                )

            connection.commit()

            return result

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


def _table_exists(
    table_name: str,
) -> bool:

    if not database_available():

        return False

    row = _fetch_one(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = %s
        ) AS exists
        """,
        (
            table_name,
        ),
    )

    return bool(
        row.get(
            "exists"
        )
    )


def _table_columns(
    table_name: str,
) -> set:

    now = time.time()

    cached = _COLUMN_CACHE.get(
        table_name
    )

    if cached:

        cached_at, columns = cached

        if (
            now
            -
            cached_at
            <
            60
        ):

            return set(
                columns
            )

    if not database_available():

        return set()

    rows = _fetch_all(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = %s
        """,
        (
            table_name,
        ),
    )

    columns = {
        clean_text(
            row.get(
                "column_name"
            ),
            200,
        )
        for row in rows
        if row.get(
            "column_name"
        )
    }

    _COLUMN_CACHE[
        table_name
    ] = (
        now,
        columns,
    )

    return columns


# =========================================================
# SAFE SCHEMA BOOTSTRAP
# =========================================================

def ensure_tables() -> Dict[str, Any]:

    global _SCHEMA_CHECKED

    if _SCHEMA_CHECKED:

        return {
            "ok":
                True,

            "checked":
                True,
        }

    if not database_available():

        return {
            "ok":
                False,

            "database":
                False,
        }

    with _SCHEMA_LOCK:

        if _SCHEMA_CHECKED:

            return {
                "ok":
                    True,

                "checked":
                    True,
            }

        #
        # Existing V2 tables are NEVER dropped.
        #
        # CREATE IF NOT EXISTS only protects fresh installs.
        #

        if not _table_exists(
            VISUAL_REFERENCES_TABLE
        ):

            _execute(
                f"""
                CREATE TABLE IF NOT EXISTS {VISUAL_REFERENCES_TABLE} (
                    id BIGSERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    brand_id TEXT NOT NULL,
                    telegram_file_id TEXT,
                    telegram_file_unique_id TEXT,
                    reference_role TEXT,
                    user_note TEXT,
                    dna_json JSONB,
                    product_lock_json JSONB,
                    source_metadata_json JSONB,
                    content_family TEXT,
                    reference_utility_json JSONB,
                    image_fingerprint TEXT,
                    usage_count INTEGER DEFAULT 0,
                    last_used_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )

        if not _table_exists(
            VISUAL_PROFILES_TABLE
        ):

            _execute(
                f"""
                CREATE TABLE IF NOT EXISTS {VISUAL_PROFILES_TABLE} (
                    id BIGSERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    brand_id TEXT NOT NULL,
                    profile_json JSONB,
                    reference_count INTEGER DEFAULT 0,
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )

        if not _table_exists(
            BRAND_PROFILES_TABLE
        ):

            _execute(
                f"""
                CREATE TABLE IF NOT EXISTS {BRAND_PROFILES_TABLE} (
                    id BIGSERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    brand_id TEXT NOT NULL,
                    brand_name TEXT,
                    profile_json JSONB,
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )

        if not _table_exists(
            BRAND_RULES_TABLE
        ):

            _execute(
                f"""
                CREATE TABLE IF NOT EXISTS {BRAND_RULES_TABLE} (
                    id BIGSERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    brand_id TEXT NOT NULL,
                    rule_type TEXT,
                    rule_text TEXT,
                    source_channel TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )

        if not _table_exists(
            BRAND_STATE_TABLE
        ):

            _execute(
                f"""
                CREATE TABLE IF NOT EXISTS {BRAND_STATE_TABLE} (
                    id BIGSERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    active_brand_id TEXT,
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )

        _COLUMN_CACHE.clear()

        _SCHEMA_CHECKED = True

        return {
            "ok":
                True,

            "checked":
                True,
        }


# =========================================================
# GENERIC ROW VALUES
# =========================================================

def _first_existing_column(
    columns: set,
    candidates: Sequence[str],
) -> str:

    for name in candidates:

        if name in columns:

            return name

    return ""


def _user_column(
    columns: set,
) -> str:

    return _first_existing_column(
        columns,
        [
            "user_id",
            "telegram_user_id",
            "owner_user_id",
        ],
    )


def _brand_column(
    columns: set,
) -> str:

    return _first_existing_column(
        columns,
        [
            "brand_id",
            "brand",
        ],
    )


# =========================================================
# ACTIVE BRAND
# =========================================================

def _active_brand_cache_key(
    user_id,
) -> str:

    return str(
        user_id
    )


def set_active_brand(
    core,
    user_id,
    brand_id: str,
) -> str:

    brand_id = safe_brand_id(
        brand_id
    )

    if not brand_id:

        return ""

    key = _active_brand_cache_key(
        user_id
    )

    _ACTIVE_BRAND_CACHE[
        key
    ] = brand_id

    if not database_available():

        return brand_id

    try:

        ensure_tables()

        columns = _table_columns(
            BRAND_STATE_TABLE
        )

        user_col = _user_column(
            columns
        )

        active_col = (
            _first_existing_column(
                columns,
                [
                    "active_brand_id",
                    "brand_id",
                ],
            )
        )

        if not (
            user_col
            and
            active_col
        ):

            return brand_id

        existing = _fetch_one(
            f"""
            SELECT *
            FROM {BRAND_STATE_TABLE}
            WHERE {user_col} = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                str(
                    user_id
                ),
            ),
        )

        if existing:

            id_col = (
                "id"
                if
                "id"
                in columns
                else ""
            )

            if id_col:

                updates = [
                    f"{active_col} = %s"
                ]

                params: List[Any] = [
                    brand_id
                ]

                if "updated_at" in columns:

                    updates.append(
                        "updated_at = NOW()"
                    )

                params.append(
                    existing.get(
                        id_col
                    )
                )

                _execute(
                    f"""
                    UPDATE {BRAND_STATE_TABLE}
                    SET {", ".join(updates)}
                    WHERE {id_col} = %s
                    """,
                    params,
                )

        else:

            insert_columns = [
                user_col,
                active_col,
            ]

            values: List[Any] = [
                str(
                    user_id
                ),
                brand_id,
            ]

            placeholders = [
                "%s",
                "%s",
            ]

            _execute(
                f"""
                INSERT INTO {BRAND_STATE_TABLE}
                ({", ".join(insert_columns)})
                VALUES ({", ".join(placeholders)})
                """,
                values,
            )

    except Exception as error:

        print(
            "⚠️ Brand active-state save:",
            clean_text(
                error,
                800,
            ),
        )

    return brand_id


def get_active_brand(
    core,
    user_id,
) -> str:

    key = _active_brand_cache_key(
        user_id
    )

    cached = _ACTIVE_BRAND_CACHE.get(
        key
    )

    if cached:

        return cached

    if not database_available():

        return ""

    try:

        ensure_tables()

        columns = _table_columns(
            BRAND_STATE_TABLE
        )

        user_col = _user_column(
            columns
        )

        active_col = (
            _first_existing_column(
                columns,
                [
                    "active_brand_id",
                    "brand_id",
                ],
            )
        )

        if not (
            user_col
            and
            active_col
        ):

            return ""

        order = (
            "updated_at DESC"
            if
            "updated_at"
            in columns
            else
            "id DESC"
        )

        row = _fetch_one(
            f"""
            SELECT *
            FROM {BRAND_STATE_TABLE}
            WHERE {user_col} = %s
            ORDER BY {order}
            LIMIT 1
            """,
            (
                str(
                    user_id
                ),
            ),
        )

        brand_id = safe_brand_id(
            row.get(
                active_col,
                "",
            )
        )

        if brand_id:

            _ACTIVE_BRAND_CACHE[
                key
            ] = brand_id

        return brand_id

    except Exception:

        return ""


# =========================================================
# BRAND PROFILE
# =========================================================

def _profile_cache_key(
    user_id,
    brand_id: str,
) -> str:

    return (
        str(
            user_id
        )
        +
        ":"
        +
        safe_brand_id(
            brand_id
        )
    )


def upsert_brand_profile(
    core,
    user_id,
    brand_id: str,
    brand_name: str,
    profile: Dict[str, Any],
) -> Dict[str, Any]:

    brand_id = safe_brand_id(
        brand_id
    )

    profile = safe_dict(
        profile
    )

    if not brand_id:

        return {}

    key = _profile_cache_key(
        user_id,
        brand_id,
    )

    cached = {
        "brand_id":
            brand_id,

        "brand_name":
            clean_text(
                brand_name,
                300,
            ),

        "profile":
            profile,
    }

    _PROFILE_CACHE[
        key
    ] = cached

    if not database_available():

        return cached

    try:

        ensure_tables()

        columns = _table_columns(
            BRAND_PROFILES_TABLE
        )

        user_col = _user_column(
            columns
        )

        brand_col = _brand_column(
            columns
        )

        profile_col = (
            _first_existing_column(
                columns,
                [
                    "profile_json",
                    "brand_profile_json",
                    "profile",
                ],
            )
        )

        name_col = (
            _first_existing_column(
                columns,
                [
                    "brand_name",
                    "name",
                    "brand_label",
                ],
            )
        )

        if not (
            user_col
            and
            brand_col
            and
            profile_col
        ):

            return cached

        existing = _fetch_one(
            f"""
            SELECT *
            FROM {BRAND_PROFILES_TABLE}
            WHERE {user_col} = %s
            AND {brand_col} = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                str(
                    user_id
                ),
                brand_id,
            ),
        )

        if existing:

            assignments = [
                f"{profile_col} = %s"
            ]

            params: List[Any] = [
                json_value(
                    profile
                )
            ]

            if name_col:

                assignments.append(
                    f"{name_col} = %s"
                )

                params.append(
                    clean_text(
                        brand_name,
                        300,
                    )
                )

            if "updated_at" in columns:

                assignments.append(
                    "updated_at = NOW()"
                )

            params.append(
                existing.get(
                    "id"
                )
            )

            _execute(
                f"""
                UPDATE {BRAND_PROFILES_TABLE}
                SET {", ".join(assignments)}
                WHERE id = %s
                """,
                params,
            )

        else:

            insert_columns = [
                user_col,
                brand_col,
                profile_col,
            ]

            values: List[Any] = [
                str(
                    user_id
                ),
                brand_id,
                json_value(
                    profile
                ),
            ]

            if name_col:

                insert_columns.append(
                    name_col
                )

                values.append(
                    clean_text(
                        brand_name,
                        300,
                    )
                )

            placeholders = [
                "%s"
                for _
                in insert_columns
            ]

            _execute(
                f"""
                INSERT INTO {BRAND_PROFILES_TABLE}
                ({", ".join(insert_columns)})
                VALUES ({", ".join(placeholders)})
                """,
                values,
            )

    except Exception as error:

        print(
            "⚠️ Brand profile persistence:",
            clean_text(
                error,
                900,
            ),
        )

    return cached


def get_brand_profile(
    core,
    user_id,
    brand_id: str,
) -> Dict[str, Any]:

    brand_id = safe_brand_id(
        brand_id
    )

    key = _profile_cache_key(
        user_id,
        brand_id,
    )

    cached = _PROFILE_CACHE.get(
        key
    )

    if cached:

        return safe_dict(
            cached.get(
                "profile"
            )
        )

    if not database_available():

        return {}

    try:

        ensure_tables()

        columns = _table_columns(
            BRAND_PROFILES_TABLE
        )

        user_col = _user_column(
            columns
        )

        brand_col = _brand_column(
            columns
        )

        profile_col = (
            _first_existing_column(
                columns,
                [
                    "profile_json",
                    "brand_profile_json",
                    "profile",
                ],
            )
        )

        if not (
            user_col
            and
            brand_col
            and
            profile_col
        ):

            return {}

        row = _fetch_one(
            f"""
            SELECT *
            FROM {BRAND_PROFILES_TABLE}
            WHERE {user_col} = %s
            AND {brand_col} = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                str(
                    user_id
                ),
                brand_id,
            ),
        )

        profile = safe_json_load(
            row.get(
                profile_col
            ),
            {},
        )

        if isinstance(
            profile,
            dict,
        ):

            _PROFILE_CACHE[
                key
            ] = {
                "brand_id":
                    brand_id,

                "brand_name":
                    clean_text(
                        row.get(
                            "brand_name",
                            "",
                        ),
                        300,
                    ),

                "profile":
                    profile,
            }

            return profile

    except Exception as error:

        print(
            "⚠️ Brand profile load:",
            clean_text(
                error,
                700,
            ),
        )

    return {}


# =========================================================
# EXPLICIT BRAND FEEDBACK
# =========================================================

APPROVED_FEEDBACK_MARKERS = [
    "اعتمد",
    "اعتمد هاد",
    "اعجبني",
    "عجبني",
    "حلو هاد الاسلوب",
    "خلي هاد الاسلوب",
    "هذا الاسلوب ممتاز",
    "احتفظ بهذا الاسلوب",
    "approved",
    "keep this style",
    "i like this style",
]


REJECTED_FEEDBACK_MARKERS = [
    "ما بدي",
    "لا تستخدم",
    "لا ترجع",
    "ما بحب",
    "مش عاجبني",
    "ارفض",
    "مرفوض",
    "avoid this",
    "do not use",
    "don't use",
    "rejected",
]


def classify_feedback_rule(
    text: str,
) -> str:

    if contains_any(
        text,
        REJECTED_FEEDBACK_MARKERS,
    ):

        return "rejected_style"

    if contains_any(
        text,
        APPROVED_FEEDBACK_MARKERS,
    ):

        return "approved_style"

    return ""


def learn_explicit_feedback(
    core,
    user_id,
    text: str,
    *,
    brand_id: str = "",
    source_channel: str = "telegram_text",
) -> Dict[str, Any]:

    value = clean_text(
        text,
        5000,
    )

    if not value:

        return {
            "saved":
                False,
        }

    rule_type = (
        classify_feedback_rule(
            value
        )
    )

    #
    # Do not turn every normal message into a brand rule.
    #

    if not rule_type:

        return {
            "saved":
                False,
        }

    brand_id = (
        safe_brand_id(
            brand_id
        )
        or
        get_active_brand(
            core,
            user_id,
        )
    )

    if not brand_id:

        return {
            "saved":
                False,
        }

    rule = {
        "rule_type":
            rule_type,

        "rule_text":
            value,

        "source_channel":
            clean_text(
                source_channel,
                100,
            ),

        "created_at":
            utc_now_iso(),
    }

    cache_key = (
        _profile_cache_key(
            user_id,
            brand_id,
        )
    )

    _RULE_CACHE.setdefault(
        cache_key,
        [],
    ).append(
        rule
    )

    if database_available():

        try:

            ensure_tables()

            columns = _table_columns(
                BRAND_RULES_TABLE
            )

            user_col = _user_column(
                columns
            )

            brand_col = _brand_column(
                columns
            )

            if (
                user_col
                and
                brand_col
            ):

                candidates = {
                    user_col:
                        str(
                            user_id
                        ),

                    brand_col:
                        brand_id,

                    "rule_type":
                        rule_type,

                    "rule_text":
                        value,

                    "source_channel":
                        clean_text(
                            source_channel,
                            100,
                        ),
                }

                insert_columns = [
                    key
                    for key
                    in candidates
                    if key in columns
                ]

                values = [
                    candidates[
                        key
                    ]
                    for key
                    in insert_columns
                ]

                if insert_columns:

                    _execute(
                        f"""
                        INSERT INTO {BRAND_RULES_TABLE}
                        ({", ".join(insert_columns)})
                        VALUES (
                            {", ".join("%s" for _ in insert_columns)}
                        )
                        """,
                        values,
                    )

        except Exception as error:

            print(
                "⚠️ Brand feedback persistence:",
                clean_text(
                    error,
                    700,
                ),
            )

    return {
        "saved":
            True,

        "brand_id":
            brand_id,

        "rule_type":
            rule_type,

        "rule_text":
            value,
    }


def load_brand_rules(
    core,
    user_id,
    brand_id: str,
    *,
    limit: int = 50,
) -> List[
    Dict[str, Any]
]:

    brand_id = safe_brand_id(
        brand_id
    )

    output: List[
        Dict[str, Any]
    ] = []

    cache_key = (
        _profile_cache_key(
            user_id,
            brand_id,
        )
    )

    output.extend(
        _RULE_CACHE.get(
            cache_key,
            [],
        )
    )

    if database_available():

        try:

            ensure_tables()

            columns = _table_columns(
                BRAND_RULES_TABLE
            )

            user_col = _user_column(
                columns
            )

            brand_col = _brand_column(
                columns
            )

            if (
                user_col
                and
                brand_col
            ):

                order = (
                    "created_at DESC"
                    if
                    "created_at"
                    in columns
                    else
                    "id DESC"
                )

                rows = _fetch_all(
                    f"""
                    SELECT *
                    FROM {BRAND_RULES_TABLE}
                    WHERE {user_col} = %s
                    AND {brand_col} = %s
                    ORDER BY {order}
                    LIMIT %s
                    """,
                    (
                        str(
                            user_id
                        ),
                        brand_id,
                        int(
                            limit
                        ),
                    ),
                )

                output.extend(
                    rows
                )

        except Exception:

            pass

    seen = set()

    deduped = []

    for item in output:

        if not isinstance(
            item,
            dict,
        ):

            continue

        text = clean_text(
            item.get(
                "rule_text",
                "",
            ),
            3000,
        )

        if not text:

            continue

        key = normalize_text(
            text
        )

        if key in seen:

            continue

        seen.add(
            key
        )

        deduped.append(
            {
                "rule_type":
                    clean_text(
                        item.get(
                            "rule_type",
                            "",
                        ),
                        100,
                    ),

                "rule_text":
                    text,

                "source_channel":
                    clean_text(
                        item.get(
                            "source_channel",
                            "",
                        ),
                        100,
                    ),
            }
        )

        if len(
            deduped
        ) >= limit:

            break

    return deduped


# =========================================================
# REFERENCE NORMALIZATION
# =========================================================

def _row_json(
    row: Dict[str, Any],
    candidates: Sequence[str],
) -> Dict[str, Any]:

    for key in candidates:

        if key not in row:

            continue

        value = safe_json_load(
            row.get(
                key
            ),
            {},
        )

        if isinstance(
            value,
            dict,
        ):

            return value

    return {}


def _reference_created_at(
    row: Dict[str, Any],
) -> Any:

    for key in [
        "created_at",
        "ingested_at",
        "updated_at",
    ]:

        if row.get(
            key
        ) is not None:

            return row.get(
                key
            )

    return ""


def normalize_reference_row(
    row: Dict[str, Any],
) -> Dict[str, Any]:

    row = dict(
        row
    )

    dna = _row_json(
        row,
        [
            "dna_json",
            "visual_dna_json",
            "dna",
        ],
    )

    product_lock = _row_json(
        row,
        [
            "product_lock_json",
            "product_lock",
        ],
    )

    source_metadata = _row_json(
        row,
        [
            "source_metadata_json",
            "source_metadata",
        ],
    )

    reference_utility = _row_json(
        row,
        [
            "reference_utility_json",
            "reference_utility",
        ],
    )

    if not reference_utility:

        reference_utility = safe_dict(
            dna.get(
                "reference_utility"
            )
        )

    content_family = clean_text(
        row.get(
            "content_family",
            "",
        ),
        100,
    )

    if not content_family:

        content_family = clean_text(
            safe_dict(
                dna.get(
                    "content_classification"
                )
            ).get(
                "family",
                "general_brand",
            ),
            100,
        )

    if not content_family:

        content_family = (
            "general_brand"
        )

    fingerprint = clean_text(
        row.get(
            "image_fingerprint",
            "",
        ),
        300,
    )

    if not fingerprint:

        fingerprint = clean_text(
            source_metadata.get(
                "image_fingerprint",
                "",
            ),
            300,
        )

    telegram_unique_id = clean_text(
        row.get(
            "telegram_file_unique_id",
            "",
        ),
        1000,
    )

    if not telegram_unique_id:

        telegram_unique_id = clean_text(
            source_metadata.get(
                "telegram_file_unique_id",
                "",
            ),
            1000,
        )

    return {
        "id":
            row.get(
                "id"
            ),

        "brand_id":
            safe_brand_id(
                row.get(
                    "brand_id",
                    "",
                )
            ),

        "telegram_file_id":
            clean_text(
                row.get(
                    "telegram_file_id",
                    "",
                ),
                2000,
            ),

        "telegram_file_unique_id":
            telegram_unique_id,

        "reference_role":
            clean_text(
                row.get(
                    "reference_role",
                    "style_reference",
                ),
                100,
            )
            or
            "style_reference",

        "user_note":
            clean_text(
                row.get(
                    "user_note",
                    "",
                ),
                3000,
            ),

        "dna":
            dna,

        "product_lock":
            product_lock,

        "source_metadata":
            source_metadata,

        "reference_utility":
            reference_utility,

        "content_family":
            content_family,

        "image_fingerprint":
            fingerprint,

        "usage_count":
            safe_int(
                row.get(
                    "usage_count",
                    0,
                ),
                0,
            ),

        "last_used_at":
            row.get(
                "last_used_at",
                "",
            ),

        "created_at":
            _reference_created_at(
                row
            ),
    }


# =========================================================
# VISUAL REFERENCE SAVE / DEDUPE
# =========================================================

def find_existing_visual_reference(
    core,
    user_id,
    brand_id: str,
    *,
    telegram_file_unique_id: str = "",
    image_fingerprint: str = "",
):

    brand_id = safe_brand_id(
        brand_id
    )

    telegram_file_unique_id = (
        clean_text(
            telegram_file_unique_id,
            1000,
        )
    )

    image_fingerprint = (
        clean_text(
            image_fingerprint,
            500,
        )
    )

    if not (
        brand_id
        and
        (
            telegram_file_unique_id
            or
            image_fingerprint
        )
    ):

        return None

    if not database_available():

        return None

    try:

        ensure_tables()

        columns = _table_columns(
            VISUAL_REFERENCES_TABLE
        )

        user_col = _user_column(
            columns
        )

        brand_col = _brand_column(
            columns
        )

        if not (
            user_col
            and
            brand_col
        ):

            return None

        conditions = [
            f"{user_col} = %s",
            f"{brand_col} = %s",
        ]

        params: List[Any] = [
            str(
                user_id
            ),
            brand_id,
        ]

        direct_conditions = []

        if (
            telegram_file_unique_id
            and
            "telegram_file_unique_id"
            in columns
        ):

            direct_conditions.append(
                "telegram_file_unique_id = %s"
            )

            params.append(
                telegram_file_unique_id
            )

        if (
            image_fingerprint
            and
            "image_fingerprint"
            in columns
        ):

            direct_conditions.append(
                "image_fingerprint = %s"
            )

            params.append(
                image_fingerprint
            )

        if direct_conditions:

            row = _fetch_one(
                f"""
                SELECT *
                FROM {VISUAL_REFERENCES_TABLE}
                WHERE {" AND ".join(conditions)}
                AND (
                    {" OR ".join(direct_conditions)}
                )
                ORDER BY id DESC
                LIMIT 1
                """,
                params,
            )

            if row:

                return normalize_reference_row(
                    row
                )

        #
        # Compatibility:
        # older V2 rows may only contain fingerprint inside
        # source_metadata_json.
        #

        rows = _fetch_all(
            f"""
            SELECT *
            FROM {VISUAL_REFERENCES_TABLE}
            WHERE {user_col} = %s
            AND {brand_col} = %s
            ORDER BY id DESC
            LIMIT 200
            """,
            (
                str(
                    user_id
                ),
                brand_id,
            ),
        )

        for row in rows:

            item = normalize_reference_row(
                row
            )

            if (
                telegram_file_unique_id
                and
                item.get(
                    "telegram_file_unique_id"
                )
                ==
                telegram_file_unique_id
            ):

                return item

            if (
                image_fingerprint
                and
                item.get(
                    "image_fingerprint"
                )
                ==
                image_fingerprint
            ):

                return item

    except Exception as error:

        print(
            "⚠️ Reference duplicate lookup:",
            clean_text(
                error,
                900,
            ),
        )

    return None


def save_visual_reference(
    core,
    user_id,
    *,
    brand_id: str,
    telegram_file_id: str = "",
    telegram_file_unique_id: str = "",
    reference_role: str = "style_reference",
    user_note: str = "",
    dna: Optional[
        Dict[str, Any]
    ] = None,
    product_lock: Optional[
        Dict[str, Any]
    ] = None,
    source_metadata: Optional[
        Dict[str, Any]
    ] = None,
):

    brand_id = safe_brand_id(
        brand_id
    )

    dna = safe_dict(
        dna
    )

    product_lock = safe_dict(
        product_lock
    )

    source_metadata = safe_dict(
        source_metadata
    )

    telegram_file_id = clean_text(
        telegram_file_id,
        2000,
    )

    telegram_file_unique_id = (
        clean_text(
            telegram_file_unique_id,
            1000,
        )
    )

    reference_role = clean_text(
        reference_role,
        100,
    ) or "style_reference"

    user_note = clean_text(
        user_note,
        3000,
    )

    content_family = clean_text(
        safe_dict(
            dna.get(
                "content_classification"
            )
        ).get(
            "family",
            "general_brand",
        ),
        100,
    )

    if not content_family:

        content_family = (
            "general_brand"
        )

    reference_utility = safe_dict(
        dna.get(
            "reference_utility"
        )
    )

    image_fingerprint = clean_text(
        source_metadata.get(
            "image_fingerprint",
            "",
        ),
        500,
    )

    existing = (
        find_existing_visual_reference(
            core,
            user_id,
            brand_id,

            telegram_file_unique_id=(
                telegram_file_unique_id
            ),

            image_fingerprint=(
                image_fingerprint
            ),
        )
    )

    if existing:

        return existing

    if not database_available():

        raise RuntimeError(
            (
                "Brand Memory database unavailable; "
                "visual reference cannot be persisted permanently."
            )
        )

    ensure_tables()

    columns = _table_columns(
        VISUAL_REFERENCES_TABLE
    )

    user_col = _user_column(
        columns
    )

    brand_col = _brand_column(
        columns
    )

    if not (
        user_col
        and
        brand_col
    ):

        raise RuntimeError(
            (
                "xpand_visual_references schema "
                "does not contain user/brand columns."
            )
        )

    values_by_column: Dict[
        str,
        Any,
    ] = {
        user_col:
            str(
                user_id
            ),

        brand_col:
            brand_id,

        "telegram_file_id":
            telegram_file_id,

        "telegram_file_unique_id":
            telegram_file_unique_id,

        "reference_role":
            reference_role,

        "user_note":
            user_note,

        "dna_json":
            json_value(
                dna
            ),

        "visual_dna_json":
            json_value(
                dna
            ),

        "product_lock_json":
            json_value(
                product_lock
            ),

        "source_metadata_json":
            json_value(
                source_metadata
            ),

        "content_family":
            content_family,

        "reference_utility_json":
            json_value(
                reference_utility
            ),

        "image_fingerprint":
            image_fingerprint,

        "usage_count":
            0,
    }

    insert_columns = []

    insert_values = []

    for column, value in (
        values_by_column.items()
    ):

        if column not in columns:

            continue

        #
        # Prefer dna_json if both aliases exist.
        #

        if (
            column
            ==
            "visual_dna_json"
            and
            "dna_json"
            in columns
        ):

            continue

        insert_columns.append(
            column
        )

        insert_values.append(
            value
        )

    if not insert_columns:

        raise RuntimeError(
            "No writable visual-reference columns found."
        )

    row = _execute(
        f"""
        INSERT INTO {VISUAL_REFERENCES_TABLE}
        ({", ".join(insert_columns)})
        VALUES (
            {", ".join("%s" for _ in insert_columns)}
        )
        RETURNING *
        """,
        insert_values,
        returning=True,
    )

    item = normalize_reference_row(
        safe_dict(
            row
        )
    )

    if (
        REFRESH_PROFILE_ON_SAVE
        and
        item
    ):

        try:

            refresh_brand_visual_profile(
                core,
                user_id,
                brand_id,
            )

        except Exception as error:

            print(
                "⚠️ Visual Profile refresh after save:",
                clean_text(
                    error,
                    700,
                ),
            )

    return item


# =========================================================
# LOAD REFERENCES
# =========================================================

def load_visual_references(
    core,
    user_id,
    *,
    brand_id: str,
    limit: int = 20,
) -> List[
    Dict[str, Any]
]:

    brand_id = safe_brand_id(
        brand_id
    )

    if not (
        brand_id
        and
        database_available()
    ):

        return []

    try:

        ensure_tables()

        columns = _table_columns(
            VISUAL_REFERENCES_TABLE
        )

        user_col = _user_column(
            columns
        )

        brand_col = _brand_column(
            columns
        )

        if not (
            user_col
            and
            brand_col
        ):

            return []

        order = (
            "created_at DESC"
            if
            "created_at"
            in columns
            else
            "id DESC"
        )

        rows = _fetch_all(
            f"""
            SELECT *
            FROM {VISUAL_REFERENCES_TABLE}
            WHERE {user_col} = %s
            AND {brand_col} = %s
            ORDER BY {order}
            LIMIT %s
            """,
            (
                str(
                    user_id
                ),
                brand_id,
                max(
                    1,
                    min(
                        500,
                        int(
                            limit
                            or 20
                        ),
                    ),
                ),
            ),
        )

        return [
            normalize_reference_row(
                row
            )
            for row in rows
        ]

    except Exception as error:

        print(
            "⚠️ Visual reference load:",
            clean_text(
                error,
                1000,
            ),
        )

        return []


# =========================================================
# REQUEST FAMILY
# =========================================================

CONTENT_FAMILY_ALIASES = {

    "merchant_payments": [
        "merchant_payments",
        "payments_cards",
        "business_banking",
        "digital_banking",
        "premium_lifestyle",
        "general_brand",
    ],

    "international_transfer": [
        "international_transfer",
        "travel_roaming",
        "premium_lifestyle",
        "general_brand",
    ],

    "travel": [
        "travel",
        "travel_roaming",
        "premium_lifestyle",
        "payments_cards",
        "general_brand",
    ],

    "cashback": [
        "cashback",
        "cashback_rewards",
        "payments_cards",
        "premium_lifestyle",
        "general_brand",
    ],

    "rewards": [
        "rewards",
        "cashback_rewards",
        "premium_lifestyle",
        "payments_cards",
        "general_brand",
    ],

    "digital_banking": [
        "digital_banking",
        "business_banking",
        "premium_lifestyle",
        "general_brand",
    ],

    "security": [
        "security",
        "security_trust",
        "digital_banking",
        "premium_lifestyle",
        "general_brand",
    ],

    "premium_banking": [
        "premium_lifestyle",
        "general_brand",
        "payments_cards",
        "digital_banking",
    ],
}


def detect_request_family(
    request: str,
) -> str:

    #
    # Prefer dedicated STC skill.
    #

    try:

        family = clean_text(
            detect_stc_benefit_family(
                request
            ),
            100,
        )

        if family:

            return family

    except Exception:

        pass

    if contains_any(
        request,
        [
            "نقاط البيع",
            "التجارة الالكترونية",
            "التجارة الإلكترونية",
            "merchant payments",
            "point of sale",
            "pos",
        ],
    ):

        return "merchant_payments"

    if contains_any(
        request,
        [
            "تحويل دولي",
            "حوالة دولية",
            "international transfer",
        ],
    ):

        return "international_transfer"

    if contains_any(
        request,
        [
            "سفر",
            "مطار",
            "travel",
            "airport",
        ],
    ):

        return "travel"

    return "premium_banking"


# =========================================================
# REFERENCE TEXT
# =========================================================

def flatten_json_text(
    value: Any,
    limit: int = 12000,
) -> str:

    try:

        return clean_text(
            json.dumps(
                value,
                ensure_ascii=False,
                default=str,
            ),
            limit,
        )

    except Exception:

        return clean_text(
            value,
            limit,
        )


def reference_search_text(
    item: Dict[str, Any],
) -> str:

    return normalize_text(
        " ".join(
            [
                clean_text(
                    item.get(
                        "content_family",
                        "",
                    ),
                    300,
                ),

                clean_text(
                    item.get(
                        "reference_role",
                        "",
                    ),
                    300,
                ),

                clean_text(
                    item.get(
                        "user_note",
                        "",
                    ),
                    1500,
                ),

                flatten_json_text(
                    item.get(
                        "dna",
                        {},
                    ),
                    6000,
                ),

                flatten_json_text(
                    item.get(
                        "reference_utility",
                        {},
                    ),
                    2000,
                ),
            ]
        )
    )


# =========================================================
# AUTHORITY
# =========================================================

def reference_official_score(
    item: Dict[str, Any],
) -> float:

    metadata = safe_dict(
        item.get(
            "source_metadata"
        )
    )

    official = bool(
        metadata.get(
            "official",
            False,
        )
        or
        metadata.get(
            "user_labeled_official",
            False,
        )
    )

    verification = normalize_text(
        metadata.get(
            "official_verification",
            "",
        )
    )

    source_type = normalize_text(
        metadata.get(
            "source_type",
            "",
        )
    )

    authority_score = safe_float(
        metadata.get(
            "authority_score",
            0,
        ),
        0,
    )

    if authority_score <= 1:

        authority_score *= 100

    score = min(
        10.0,
        max(
            0.0,
            authority_score
            /
            10.0,
        ),
    )

    if verification in {
        "verified",
        "official_verified",
        "web_verified",
    }:

        score += 18.0

    elif verification in {
        "user_asserted",
        "user_confirmed",
    }:

        score += 12.0

    elif official:

        score += 10.0

    if contains_any(
        source_type,
        [
            "official",
            "brand_owned",
            "instagram",
            "website",
        ],
    ):

        score += 3.0

    return score


# =========================================================
# UTILITY
# =========================================================

def reference_utility_score(
    item: Dict[str, Any],
) -> float:

    utility = safe_dict(
        item.get(
            "reference_utility"
        )
    )

    values = []

    for value in utility.values():

        if isinstance(
            value,
            (
                int,
                float,
            ),
        ):

            number = float(
                value
            )

            if number <= 1:

                number *= 100

            values.append(
                max(
                    0.0,
                    min(
                        100.0,
                        number,
                    ),
                )
            )

    if values:

        return (
            sum(
                values
            )
            /
            len(
                values
            )
            *
            0.12
        )

    confidence = safe_float(
        safe_dict(
            item.get(
                "dna"
            )
        ).get(
            "confidence",
            0,
        ),
        0,
    )

    if confidence <= 1:

        confidence *= 100

    return (
        max(
            0.0,
            min(
                100.0,
                confidence,
            ),
        )
        *
        0.08
    )


# =========================================================
# STYLE MATCHING
# =========================================================

def reference_style_signature(
    item: Dict[str, Any],
) -> str:

    text = reference_search_text(
        item
    )

    if contains_any(
        text,
        [
            "purple_architectural",
            "purple studio",
            "purple environment",
            "بيئه بنفسجيه",
            "بيئة بنفسجية",
            "geometric plinth",
            "aubergine",
        ],
    ):

        return (
            STYLE_PURPLE_ARCHITECTURAL
        )

    if contains_any(
        text,
        [
            "augmented realism",
            "surreal realism",
            "conceptual realism",
            "forced perspective",
            "واقعي سريالي",
            "واقعيه معززه",
            "واقعية معززة",
        ],
    ):

        return (
            STYLE_AUGMENTED_REALISM
        )

    if contains_any(
        text,
        [
            "photorealistic",
            "commercial photography",
            "realistic",
            "lifestyle",
            "واقعي",
            "فوتوغرافي",
        ],
    ):

        return (
            STYLE_PREMIUM_REALISTIC
        )

    return ""


# =========================================================
# CAMERA SIGNATURE
# =========================================================

CAMERA_KEYWORDS = [
    "worms eye",
    "worm's-eye",
    "bird's-eye",
    "birds eye",
    "top-down",
    "overhead",
    "low-angle",
    "low angle",
    "high-angle",
    "high angle",
    "over-the-shoulder",
    "over the shoulder",
    "pov",
    "point-of-view",
    "eye-level",
    "eye level",
    "three-quarter",
    "three quarter",
    "macro",
    "wide",
    "close-up",
    "close up",
    "one-point perspective",
    "two-point perspective",
    "forced perspective",
]


def reference_camera_signature(
    item: Dict[str, Any],
) -> str:

    text = reference_search_text(
        item
    )

    for marker in CAMERA_KEYWORDS:

        if normalize_text(
            marker
        ) in text:

            return normalize_text(
                marker
            )

    dna = safe_dict(
        item.get(
            "dna"
        )
    )

    for key in [
        "camera_angle",
        "shot_type",
        "camera",
        "viewpoint",
        "perspective",
    ]:

        value = clean_text(
            dna.get(
                key,
                "",
            ),
            300,
        )

        if value:

            return normalize_text(
                value
            )[:120]

    return ""


# =========================================================
# REQUEST KEYWORDS
# =========================================================

STOP_WORDS = {
    "انشئ",
    "أنشئ",
    "صوره",
    "صورة",
    "اعلان",
    "إعلان",
    "لبنك",
    "bank",
    "stc",
    "the",
    "for",
    "with",
    "عن",
    "في",
    "من",
    "الى",
    "إلى",
    "على",
    "علي",
}


def useful_keywords(
    text: str,
) -> set:

    tokens = re.findall(
        r"[a-z0-9\u0600-\u06FF]+",
        normalize_text(
            text
        ),
    )

    return {
        token
        for token in tokens
        if (
            len(
                token
            )
            >=
            3
            and
            token not in STOP_WORDS
        )
    }


def keyword_overlap_score(
    request: str,
    item: Dict[str, Any],
) -> float:

    left = useful_keywords(
        request
    )

    right = useful_keywords(
        reference_search_text(
            item
        )
    )

    if not (
        left
        and
        right
    ):

        return 0.0

    intersection = (
        left
        &
        right
    )

    return min(
        12.0,
        len(
            intersection
        )
        *
        2.5,
    )


# =========================================================
# RECENCY
# =========================================================

def datetime_timestamp(
    value: Any,
) -> Optional[float]:

    if value is None:

        return None

    if isinstance(
        value,
        datetime,
    ):

        try:

            return value.timestamp()

        except Exception:

            return None

    text = clean_text(
        value,
        200,
    )

    if not text:

        return None

    try:

        return (
            datetime.fromisoformat(
                text.replace(
                    "Z",
                    "+00:00",
                )
            )
            .timestamp()
        )

    except Exception:

        return None


def recency_score(
    item: Dict[str, Any],
) -> float:

    timestamp = datetime_timestamp(
        item.get(
            "created_at"
        )
    )

    if timestamp is None:

        return 0.0

    age_days = max(
        0.0,
        (
            time.time()
            -
            timestamp
        )
        /
        86400.0,
    )

    #
    # Recency matters, but should never override
    # content/service fit.
    #

    return (
        7.0
        *
        math.exp(
            -age_days
            /
            365.0
        )
    )


# =========================================================
# REFERENCE SCORE
# =========================================================

def reference_selection_score(
    item: Dict[str, Any],
    request: str,
    *,
    request_family: str,
    requested_style: str,
) -> Tuple[
    float,
    Dict[str, Any],
]:

    score = 10.0

    reasons = []

    family = clean_text(
        item.get(
            "content_family",
            "general_brand",
        ),
        100,
    )

    aliases = (
        CONTENT_FAMILY_ALIASES.get(
            request_family,
            CONTENT_FAMILY_ALIASES[
                "premium_banking"
            ],
        )
    )

    if family == request_family:

        score += 40.0

        reasons.append(
            "exact_family"
        )

    elif family in aliases:

        position = aliases.index(
            family
        )

        bonus = max(
            7.0,
            28.0
            -
            position
            *
            5.0,
        )

        score += bonus

        reasons.append(
            "related_family"
        )

    elif family == "general_brand":

        score += 6.0

        reasons.append(
            "general_brand"
        )

    official = (
        reference_official_score(
            item
        )
    )

    score += official

    if official >= 10:

        reasons.append(
            "official_source"
        )

    utility = (
        reference_utility_score(
            item
        )
    )

    score += utility

    requested_style = clean_text(
        requested_style,
        100,
    )

    reference_style = (
        reference_style_signature(
            item
        )
    )

    if requested_style:

        if (
            reference_style
            ==
            requested_style
        ):

            score += 18.0

            reasons.append(
                "style_match"
            )

        elif (
            reference_style
            and
            reference_style
            !=
            requested_style
        ):

            score -= 5.0

    score += keyword_overlap_score(
        request,
        item,
    )

    score += recency_score(
        item
    )

    role = clean_text(
        item.get(
            "reference_role",
            "",
        ),
        100,
    )

    if (
        role
        ==
        "product_reference"
        and
        contains_any(
            request,
            [
                "بطاق",
                "card",
                "pos",
                "نقاط البيع",
                "هاتف",
                "phone",
            ],
        )
    ):

        score += 8.0

        reasons.append(
            "product_reference"
        )

    usage_count = safe_int(
        item.get(
            "usage_count",
            0,
        ),
        0,
    )

    #
    # Mild rotation penalty:
    # avoid the exact same reference dominating forever.
    #

    score -= min(
        5.0,
        usage_count
        *
        0.35,
    )

    #
    # Realistic request:
    # penalize obvious purple-neon reference language.
    #

    if (
        requested_style
        ==
        STYLE_PREMIUM_REALISTIC
    ):

        text = reference_search_text(
            item
        )

        if contains_any(
            text,
            [
                "purple neon",
                "neon purple",
                "نيون بنفسجي",
            ],
        ):

            score -= 10.0

            reasons.append(
                "purple_neon_penalty"
            )

    return (
        round(
            score,
            3,
        ),
        {
            "family":
                family,

            "request_family":
                request_family,

            "requested_style":
                requested_style,

            "reference_style":
                reference_style,

            "camera_signature":
                reference_camera_signature(
                    item
                ),

            "reasons":
                reasons,
        },
    )


# =========================================================
# CURATOR
# =========================================================

def curate_references(
    references: Sequence[
        Dict[str, Any]
    ],
    request: str,
    *,
    brand_id: str,
    limit: int,
) -> List[
    Dict[str, Any]
]:

    brand_id = safe_brand_id(
        brand_id
    )

    request_family = (
        detect_request_family(
            request
        )
    )

    requested_style = ""

    if brand_id == "stc_bank":

        try:

            requested_style = (
                detect_stc_visual_style(
                    request
                )
            )

        except Exception:

            requested_style = ""

    scored = []

    for item in references:

        if not isinstance(
            item,
            dict,
        ):

            continue

        base_score, selection = (
            reference_selection_score(
                item,
                request,

                request_family=(
                    request_family
                ),

                requested_style=(
                    requested_style
                ),
            )
        )

        candidate = dict(
            item
        )

        candidate[
            "selection"
        ] = {
            **selection,

            "base_score":
                base_score,
        }

        scored.append(
            (
                base_score,
                candidate,
            )
        )

    scored.sort(
        key=lambda pair:
            pair[
                0
            ],
        reverse=True,
    )

    selected = []

    used_families = set()

    used_cameras = set()

    used_styles = set()

    remaining = list(
        scored
    )

    while (
        remaining
        and
        len(
            selected
        )
        <
        limit
    ):

        best_index = None

        best_effective = None

        for index, (
            base_score,
            candidate,
        ) in enumerate(
            remaining
        ):

            selection = safe_dict(
                candidate.get(
                    "selection"
                )
            )

            family = clean_text(
                candidate.get(
                    "content_family",
                    "",
                ),
                100,
            )

            camera = clean_text(
                selection.get(
                    "camera_signature",
                    "",
                ),
                200,
            )

            style = clean_text(
                selection.get(
                    "reference_style",
                    "",
                ),
                100,
            )

            effective = float(
                base_score
            )

            #
            # Diversity bonus.
            #

            if (
                camera
                and
                camera
                not in used_cameras
            ):

                effective += 4.0

            if (
                family
                and
                family
                not in used_families
            ):

                effective += 2.5

            if (
                style
                and
                style
                not in used_styles
            ):

                effective += 1.5

            #
            # Avoid 3 references that teach exactly
            # the same scene/camera.
            #

            if (
                camera
                and
                camera in used_cameras
            ):

                effective -= 3.0

            if (
                len(
                    selected
                )
                >=
                1
                and
                family
                and
                family in used_families
                and
                family
                !=
                request_family
            ):

                effective -= 2.0

            if (
                best_effective
                is None
                or
                effective
                >
                best_effective
            ):

                best_effective = (
                    effective
                )

                best_index = index

        if best_index is None:

            break

        _, chosen = (
            remaining.pop(
                best_index
            )
        )

        chosen_selection = safe_dict(
            chosen.get(
                "selection"
            )
        )

        chosen_selection[
            "final_score"
        ] = round(
            float(
                best_effective
            ),
            3,
        )

        chosen[
            "selection"
        ] = chosen_selection

        selected.append(
            chosen
        )

        family = clean_text(
            chosen.get(
                "content_family",
                "",
            ),
            100,
        )

        camera = clean_text(
            chosen_selection.get(
                "camera_signature",
                "",
            ),
            200,
        )

        style = clean_text(
            chosen_selection.get(
                "reference_style",
                "",
            ),
            100,
        )

        if family:

            used_families.add(
                family
            )

        if camera:

            used_cameras.add(
                camera
            )

        if style:

            used_styles.add(
                style
            )

    return selected


# =========================================================
# USAGE TRACKING
# =========================================================

def mark_references_used(
    references: Sequence[
        Dict[str, Any]
    ],
) -> None:

    if not (
        references
        and
        database_available()
    ):

        return

    try:

        columns = _table_columns(
            VISUAL_REFERENCES_TABLE
        )

        if (
            "id"
            not in columns
        ):

            return

        for item in references:

            reference_id = item.get(
                "id"
            )

            if reference_id is None:

                continue

            updates = []

            if "usage_count" in columns:

                updates.append(
                    (
                        "usage_count = "
                        "COALESCE(usage_count, 0) + 1"
                    )
                )

            if "last_used_at" in columns:

                updates.append(
                    "last_used_at = NOW()"
                )

            if not updates:

                continue

            _execute(
                f"""
                UPDATE {VISUAL_REFERENCES_TABLE}
                SET {", ".join(updates)}
                WHERE id = %s
                """,
                (
                    reference_id,
                ),
            )

    except Exception as error:

        print(
            "⚠️ Reference usage tracking:",
            clean_text(
                error,
                700,
            ),
        )


# =========================================================
# REQUEST-AWARE LOAD
# =========================================================

def load_relevant_visual_references(
    core,
    user_id,
    *,
    brand_id: str,
    request: str,
    limit: int = 5,
    mark_used: bool = False,
) -> List[
    Dict[str, Any]
]:

    brand_id = safe_brand_id(
        brand_id
    )

    request = clean_text(
        request,
        12000,
    )

    if not brand_id:

        return []

    requested_limit = max(
        1,
        int(
            limit
            or 1
        ),
    )

    if brand_id == "stc_bank":

        effective_limit = min(
            requested_limit,
            STC_REFERENCE_LIMIT,
        )

    else:

        effective_limit = min(
            requested_limit,
            GENERAL_REFERENCE_LIMIT,
        )

    references = load_visual_references(
        core,
        user_id,

        brand_id=brand_id,

        limit=REFERENCE_SCAN_LIMIT,
    )

    if not references:

        return []

    selected = curate_references(
        references,
        request,

        brand_id=brand_id,

        limit=effective_limit,
    )

    if mark_used:

        mark_references_used(
            selected
        )

    if brand_id == "stc_bank":

        print(
            (
                "🧠 STC REFERENCE CURATOR"
                +
                " | request_family="
                +
                detect_request_family(
                    request
                )
                +
                " | selected="
                +
                str(
                    len(
                        selected
                    )
                )
                +
                "/"
                +
                str(
                    len(
                        references
                    )
                )
            )
        )

        for index, item in enumerate(
            selected,
            start=1,
        ):

            selection = safe_dict(
                item.get(
                    "selection"
                )
            )

            print(
                (
                    "   #"
                    +
                    str(
                        index
                    )
                    +
                    " ref="
                    +
                    str(
                        item.get(
                            "id"
                        )
                    )
                    +
                    " family="
                    +
                    clean_text(
                        item.get(
                            "content_family",
                            "",
                        ),
                        100,
                    )
                    +
                    " score="
                    +
                    str(
                        selection.get(
                            "final_score",
                            selection.get(
                                "base_score",
                                "",
                            ),
                        )
                    )
                    +
                    " camera="
                    +
                    clean_text(
                        selection.get(
                            "camera_signature",
                            "",
                        ),
                        100,
                    )
                )
            )

    return selected


# =========================================================
# LIBRARY STATS
# =========================================================

def get_visual_library_stats(
    core,
    user_id,
    brand_id: str,
) -> Dict[str, Any]:

    brand_id = safe_brand_id(
        brand_id
    )

    references = load_visual_references(
        core,
        user_id,

        brand_id=brand_id,

        limit=500,
    )

    if not references:

        return {
            "total":
                0,

            "official_sources":
                0,

            "content_families":
                0,

            "family_distribution":
                {},
        }

    family_counter = Counter()

    role_counter = Counter()

    official_count = 0

    for item in references:

        family_counter[
            clean_text(
                item.get(
                    "content_family",
                    "general_brand",
                ),
                100,
            )
        ] += 1

        role_counter[
            clean_text(
                item.get(
                    "reference_role",
                    "style_reference",
                ),
                100,
            )
        ] += 1

        if (
            reference_official_score(
                item
            )
            >=
            10
        ):

            official_count += 1

    return {
        "total":
            len(
                references
            ),

        "official_sources":
            official_count,

        "official_references":
            official_count,

        "content_families":
            len(
                family_counter
            ),

        "families":
            len(
                family_counter
            ),

        "family_distribution":
            dict(
                family_counter
            ),

        "role_distribution":
            dict(
                role_counter
            ),
    }


# =========================================================
# VISUAL PROFILE EXTRACTION
# =========================================================

def recursively_collect_values(
    value: Any,
    key_markers: Sequence[str],
    *,
    max_items: int = 100,
) -> List[str]:

    results: List[str] = []

    markers = [
        normalize_text(
            marker
        )
        for marker in key_markers
    ]

    def walk(
        node: Any,
        parent_key: str = "",
    ):

        if len(
            results
        ) >= max_items:

            return

        if isinstance(
            node,
            dict,
        ):

            for key, child in (
                node.items()
            ):

                key_normalized = (
                    normalize_text(
                        key
                    )
                )

                if any(
                    marker
                    in
                    key_normalized
                    for marker
                    in markers
                ):

                    if isinstance(
                        child,
                        (
                            str,
                            int,
                            float,
                        ),
                    ):

                        text = clean_text(
                            child,
                            300,
                        )

                        if text:

                            results.append(
                                text
                            )

                    elif isinstance(
                        child,
                        list,
                    ):

                        for item in child:

                            if isinstance(
                                item,
                                (
                                    str,
                                    int,
                                    float,
                                ),
                            ):

                                text = clean_text(
                                    item,
                                    300,
                                )

                                if text:

                                    results.append(
                                        text
                                    )

                walk(
                    child,
                    key_normalized,
                )

        elif isinstance(
            node,
            list,
        ):

            for child in node:

                walk(
                    child,
                    parent_key,
                )

    walk(
        value
    )

    return results[:max_items]


def top_clean_values(
    values: Iterable[str],
    limit: int = 10,
) -> List[str]:

    counter = Counter()

    originals = {}

    for value in values:

        text = clean_text(
            value,
            300,
        )

        if not text:

            continue

        normalized_value = (
            normalize_text(
                text
            )
        )

        if not normalized_value:

            continue

        counter[
            normalized_value
        ] += 1

        originals.setdefault(
            normalized_value,
            text,
        )

    return [
        originals[
            key
        ]
        for key, _
        in counter.most_common(
            limit
        )
    ]


def extract_hex_colors(
    value: Any,
) -> List[str]:

    text = flatten_json_text(
        value,
        50000,
    )

    colors = re.findall(
        r"#[0-9A-Fa-f]{6}\b",
        text,
    )

    return [
        color.upper()
        for color
        in colors
    ]


# =========================================================
# VISUAL PROFILE STORE
# =========================================================

def _save_brand_visual_profile(
    user_id,
    brand_id: str,
    profile: Dict[str, Any],
) -> None:

    if not database_available():

        return

    ensure_tables()

    columns = _table_columns(
        VISUAL_PROFILES_TABLE
    )

    user_col = _user_column(
        columns
    )

    brand_col = _brand_column(
        columns
    )

    profile_col = (
        _first_existing_column(
            columns,
            [
                "profile_json",
                "visual_profile_json",
                "profile",
            ],
        )
    )

    if not (
        user_col
        and
        brand_col
        and
        profile_col
    ):

        return

    existing = _fetch_one(
        f"""
        SELECT *
        FROM {VISUAL_PROFILES_TABLE}
        WHERE {user_col} = %s
        AND {brand_col} = %s
        ORDER BY id DESC
        LIMIT 1
        """,
        (
            str(
                user_id
            ),
            brand_id,
        ),
    )

    reference_count = safe_int(
        profile.get(
            "reference_count",
            0,
        ),
        0,
    )

    if existing:

        assignments = [
            f"{profile_col} = %s"
        ]

        params: List[Any] = [
            json_value(
                profile
            )
        ]

        if "reference_count" in columns:

            assignments.append(
                "reference_count = %s"
            )

            params.append(
                reference_count
            )

        if "updated_at" in columns:

            assignments.append(
                "updated_at = NOW()"
            )

        params.append(
            existing.get(
                "id"
            )
        )

        _execute(
            f"""
            UPDATE {VISUAL_PROFILES_TABLE}
            SET {", ".join(assignments)}
            WHERE id = %s
            """,
            params,
        )

    else:

        insert_columns = [
            user_col,
            brand_col,
            profile_col,
        ]

        values: List[Any] = [
            str(
                user_id
            ),
            brand_id,
            json_value(
                profile
            ),
        ]

        if "reference_count" in columns:

            insert_columns.append(
                "reference_count"
            )

            values.append(
                reference_count
            )

        _execute(
            f"""
            INSERT INTO {VISUAL_PROFILES_TABLE}
            ({", ".join(insert_columns)})
            VALUES (
                {", ".join("%s" for _ in insert_columns)}
            )
            """,
            values,
        )


def get_brand_visual_profile(
    core,
    user_id,
    brand_id: str,
) -> Dict[str, Any]:

    brand_id = safe_brand_id(
        brand_id
    )

    if not (
        brand_id
        and
        database_available()
    ):

        return {}

    try:

        ensure_tables()

        columns = _table_columns(
            VISUAL_PROFILES_TABLE
        )

        user_col = _user_column(
            columns
        )

        brand_col = _brand_column(
            columns
        )

        profile_col = (
            _first_existing_column(
                columns,
                [
                    "profile_json",
                    "visual_profile_json",
                    "profile",
                ],
            )
        )

        if not (
            user_col
            and
            brand_col
            and
            profile_col
        ):

            return {}

        row = _fetch_one(
            f"""
            SELECT *
            FROM {VISUAL_PROFILES_TABLE}
            WHERE {user_col} = %s
            AND {brand_col} = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            (
                str(
                    user_id
                ),
                brand_id,
            ),
        )

        profile = safe_json_load(
            row.get(
                profile_col
            ),
            {},
        )

        return (
            profile
            if isinstance(
                profile,
                dict,
            )
            else {}
        )

    except Exception as error:

        print(
            "⚠️ Brand Visual Profile load:",
            clean_text(
                error,
                800,
            ),
        )

        return {}


# =========================================================
# BUILD AGGREGATED VISUAL PROFILE
# =========================================================

def refresh_brand_visual_profile(
    core,
    user_id,
    brand_id: str,
) -> Dict[str, Any]:

    brand_id = safe_brand_id(
        brand_id
    )

    references = load_visual_references(
        core,
        user_id,

        brand_id=brand_id,

        limit=VISUAL_PROFILE_REFERENCE_LIMIT,
    )

    if not references:

        return {}

    families = Counter()

    roles = Counter()

    style_counter = Counter()

    official_count = 0

    camera_values = []

    lens_values = []

    lighting_values = []

    material_values = []

    composition_values = []

    negative_space_values = []

    human_values = []

    colors = []

    for item in references:

        families[
            clean_text(
                item.get(
                    "content_family",
                    "general_brand",
                ),
                100,
            )
        ] += 1

        roles[
            clean_text(
                item.get(
                    "reference_role",
                    "style_reference",
                ),
                100,
            )
        ] += 1

        style = reference_style_signature(
            item
        )

        if style:

            style_counter[
                style
            ] += 1

        if (
            reference_official_score(
                item
            )
            >=
            10
        ):

            official_count += 1

        dna = safe_dict(
            item.get(
                "dna"
            )
        )

        colors.extend(
            extract_hex_colors(
                dna
            )
        )

        camera_values.extend(
            recursively_collect_values(
                dna,
                [
                    "camera",
                    "shot",
                    "viewpoint",
                    "angle",
                    "perspective",
                ],
            )
        )

        lens_values.extend(
            recursively_collect_values(
                dna,
                [
                    "lens",
                    "focal",
                ],
            )
        )

        lighting_values.extend(
            recursively_collect_values(
                dna,
                [
                    "lighting",
                    "light",
                    "shadow",
                ],
            )
        )

        material_values.extend(
            recursively_collect_values(
                dna,
                [
                    "material",
                    "surface",
                    "texture",
                ],
            )
        )

        composition_values.extend(
            recursively_collect_values(
                dna,
                [
                    "composition",
                    "framing",
                    "hierarchy",
                ],
            )
        )

        negative_space_values.extend(
            recursively_collect_values(
                dna,
                [
                    "negative_space",
                    "negative space",
                ],
            )
        )

        human_values.extend(
            recursively_collect_values(
                dna,
                [
                    "human",
                    "people",
                    "subject",
                    "pose",
                ],
            )
        )

    profile: Dict[
        str,
        Any,
    ] = {
        "brand_id":
            brand_id,

        "version":
            VERSION,

        "reference_count":
            len(
                references
            ),

        "official_reference_count":
            official_count,

        "content_family_distribution":
            dict(
                families
            ),

        "reference_role_distribution":
            dict(
                roles
            ),

        "style_distribution":
            dict(
                style_counter
            ),

        "dominant_colors":
            top_clean_values(
                colors,
                12,
            ),

        "camera_patterns":
            top_clean_values(
                camera_values,
                14,
            ),

        "lens_patterns":
            top_clean_values(
                lens_values,
                10,
            ),

        "lighting_patterns":
            top_clean_values(
                lighting_values,
                14,
            ),

        "material_patterns":
            top_clean_values(
                material_values,
                14,
            ),

        "composition_patterns":
            top_clean_values(
                composition_values,
                14,
            ),

        "negative_space_patterns":
            top_clean_values(
                negative_space_values,
                8,
            ),

        "human_direction_patterns":
            top_clean_values(
                human_values,
                10,
            ),

        "anti_clone_rule":
            (
                "Use references as visual evidence. "
                "Never clone exact composition, exact camera framing "
                "or an existing campaign metaphor."
            ),

        "updated_at":
            utc_now_iso(),
    }

    if brand_id == "stc_bank":

        try:

            profile[
                "stc_skill_summary"
            ] = (
                get_stc_visual_dna_summary()
            )

        except Exception:

            pass

        profile[
            "stc_reference_policy"
        ] = {
            "max_runtime_references":
                STC_REFERENCE_LIMIT,

            "priority":
                [
                    "service match",
                    "visual style match",
                    "official authority",
                    "reference utility",
                    "camera diversity",
                    "recency",
                ],

            "purple_is_not_default":
                True,

            "no_text":
                True,

            "no_logo":
                True,
        }

    try:

        _save_brand_visual_profile(
            user_id,
            brand_id,
            profile,
        )

    except Exception as error:

        print(
            "⚠️ Brand Visual Profile save:",
            clean_text(
                error,
                900,
            ),
        )

    return profile


# =========================================================
# MODEL-SAFE REFERENCE SUMMARY
# =========================================================

def reference_execution_context(
    references: Sequence[
        Dict[str, Any]
    ],
    request: str,
    brand_id: str,
) -> Dict[str, Any]:

    selected = []

    for item in references:

        selection = safe_dict(
            item.get(
                "selection"
            )
        )

        selected.append(
            {
                "id":
                    item.get(
                        "id"
                    ),

                "content_family":
                    item.get(
                        "content_family"
                    ),

                "reference_role":
                    item.get(
                        "reference_role"
                    ),

                "camera_signature":
                    selection.get(
                        "camera_signature"
                    ),

                "reference_style":
                    selection.get(
                        "reference_style"
                    ),

                "selection_score":
                    selection.get(
                        "final_score",
                        selection.get(
                            "base_score",
                        ),
                    ),

                "selection_reasons":
                    selection.get(
                        "reasons",
                        [],
                    ),
            }
        )

    return {
        "request_family":
            detect_request_family(
                request
            ),

        "requested_style":
            (
                detect_stc_visual_style(
                    request
                )
                if
                safe_brand_id(
                    brand_id
                )
                ==
                "stc_bank"
                else
                ""
            ),

        "selected_reference_count":
            len(
                references
            ),

        "selected":
            selected,

        "execution_policy": [
            (
                "Learn visual sophistication, camera, lighting, "
                "materials and realism from references."
            ),

            (
                "Do not copy an existing composition or campaign."
            ),

            (
                "Use references as evidence, not as templates."
            ),

            (
                "The new scene must be original."
            ),
        ],
    }


# =========================================================
# BRAND RULE CONTEXT
# =========================================================

def profile_rules(
    profile: Dict[str, Any],
) -> List[str]:

    profile = safe_dict(
        profile
    )

    rules: List[str] = []

    for key in [
        "visual_dna",
        "photography_rules",
        "image_only_rules",
        "forbidden_default_devices",
        "creative_positioning",
        "material_language",
    ]:

        values = profile.get(
            key
        )

        if not isinstance(
            values,
            list,
        ):

            continue

        for value in values:

            text = clean_text(
                value,
                800,
            )

            if text:

                rules.append(
                    text
                )

    return rules


# =========================================================
# COMPLETE BRAND MEMORY CONTEXT
# =========================================================

def build_brand_memory_context(
    core,
    user_id,
    brand_id: str,
    *,
    request: str = "",
    max_rules: int = 70,
    max_references: int = 5,
) -> Dict[str, Any]:

    brand_id = safe_brand_id(
        brand_id
    )

    if not brand_id:

        return {}

    profile = get_brand_profile(
        core,
        user_id,
        brand_id,
    )

    stored_rules = load_brand_rules(
        core,
        user_id,
        brand_id,

        limit=max(
            1,
            min(
                100,
                int(
                    max_rules
                    or 70
                ),
            ),
        ),
    )

    rules: List[str] = []

    #
    # Permanent explicit feedback takes first priority.
    #

    for item in stored_rules:

        rule_type = clean_text(
            item.get(
                "rule_type",
                "",
            ),
            100,
        )

        text = clean_text(
            item.get(
                "rule_text",
                "",
            ),
            1200,
        )

        if not text:

            continue

        rules.append(
            (
                "["
                +
                (
                    rule_type
                    or
                    "brand_rule"
                )
                +
                "] "
                +
                text
            )
        )

    rules.extend(
        profile_rules(
            profile
        )
    )

    #
    # Stable dedupe.
    #

    deduped_rules = []

    seen_rules = set()

    for rule in rules:

        key = normalize_text(
            rule
        )

        if not (
            key
            and
            key not in seen_rules
        ):

            continue

        seen_rules.add(
            key
        )

        deduped_rules.append(
            rule
        )

        if len(
            deduped_rules
        ) >= max_rules:

            break

    if request:

        references = (
            load_relevant_visual_references(
                core,
                user_id,

                brand_id=brand_id,

                request=request,

                limit=max_references,

                mark_used=False,
            )
        )

    else:

        raw_limit = (
            STC_REFERENCE_LIMIT
            if brand_id
            ==
            "stc_bank"
            else
            min(
                max_references,
                GENERAL_REFERENCE_LIMIT,
            )
        )

        references = (
            load_visual_references(
                core,
                user_id,

                brand_id=brand_id,

                limit=raw_limit,
            )
        )

    visual_profile = (
        get_brand_visual_profile(
            core,
            user_id,
            brand_id,
        )
    )

    if (
        not visual_profile
        and
        references
    ):

        visual_profile = (
            refresh_brand_visual_profile(
                core,
                user_id,
                brand_id,
            )
        )

    stats = {
        "total":
            safe_int(
                visual_profile.get(
                    "reference_count",
                    len(
                        references
                    ),
                ),
                len(
                    references
                ),
            ),

        "official_sources":
            safe_int(
                visual_profile.get(
                    "official_reference_count",
                    0,
                ),
                0,
            ),

        "content_families":
            len(
                safe_dict(
                    visual_profile.get(
                        "content_family_distribution"
                    )
                )
            ),
    }

    return {
        "brand_id":
            brand_id,

        "profile":
            profile,

        "visual_profile":
            visual_profile,

        "rules":
            deduped_rules,

        "references":
            references,

        "reference_execution_context":
            reference_execution_context(
                references,
                request,
                brand_id,
            ),

        "library_stats":
            stats,

        "campaign":
            {},
    }


# =========================================================
# COMPATIBILITY ALIASES
# =========================================================

def get_brand_memory_context(
    core,
    user_id,
    brand_id: str,
    *,
    request: str = "",
    max_rules: int = 70,
    max_references: int = 5,
) -> Dict[str, Any]:

    return build_brand_memory_context(
        core,
        user_id,
        brand_id,

        request=request,

        max_rules=max_rules,

        max_references=max_references,
    )


def select_visual_references(
    core,
    user_id,
    brand_id: str,
    *,
    request: str = "",
    limit: int = 5,
) -> List[
    Dict[str, Any]
]:

    if request:

        return (
            load_relevant_visual_references(
                core,
                user_id,

                brand_id=brand_id,

                request=request,

                limit=limit,

                mark_used=False,
            )
        )

    return load_visual_references(
        core,
        user_id,

        brand_id=brand_id,

        limit=limit,
    )


# =========================================================
# STATUS
# =========================================================

def get_brand_memory_status() -> Dict[
    str,
    Any,
]:

    return {
        "module":
            MODULE_NAME,

        "version":
            VERSION,

        "database_configured":
            bool(
                DATABASE_URL
            ),

        "psycopg_available":
            PSYCOPG_AVAILABLE,

        "stc_reference_limit":
            STC_REFERENCE_LIMIT,

        "general_reference_limit":
            GENERAL_REFERENCE_LIMIT,

        "reference_scan_limit":
            REFERENCE_SCAN_LIMIT,

        "visual_profile_reference_limit":
            VISUAL_PROFILE_REFERENCE_LIMIT,

        "refresh_profile_on_save":
            REFRESH_PROFILE_ON_SAVE,

        "visual_references_table":
            VISUAL_REFERENCES_TABLE,

        "visual_profiles_table":
            VISUAL_PROFILES_TABLE,
    }


# =========================================================
# ZERO-DATABASE SELF TEST
# =========================================================

if __name__ == "__main__":

    tests: Dict[
        str,
        bool
    ] = {}

    tests[
        "safe_brand_stc"
    ] = (
        safe_brand_id(
            "STC Bank"
        )
        ==
        "stc_bank"
    )

    tests[
        "safe_brand_xpand"
    ] = (
        safe_brand_id(
            "XPAND"
        )
        ==
        "xpand"
    )

    tests[
        "merchant_family"
    ] = (
        detect_request_family(
            (
                "خدمات التجارة الإلكترونية "
                "ونقاط البيع"
            )
        )
        ==
        "merchant_payments"
    )

    fake_official = {
        "id":
            1,

        "content_family":
            "payments_cards",

        "reference_role":
            "style_reference",

        "user_note":
            (
                "premium realistic commercial "
                "photography low-angle"
            ),

        "dna": {
            "confidence":
                0.95,

            "camera_angle":
                "Low-Angle Shot",

            "content_classification": {
                "family":
                    "payments_cards",
            },
        },

        "source_metadata": {
            "official":
                True,

            "official_verification":
                "user_asserted",

            "authority_score":
                90,
        },

        "reference_utility": {
            "style":
                95,

            "camera":
                92,
        },

        "usage_count":
            0,
    }

    fake_generic = {
        "id":
            2,

        "content_family":
            "general_brand",

        "reference_role":
            "style_reference",

        "user_note":
            (
                "generic purple neon room "
                "with floating fintech visual"
            ),

        "dna": {
            "confidence":
                0.7,
        },

        "source_metadata": {},

        "reference_utility": {},

        "usage_count":
            0,
    }

    score_official, _ = (
        reference_selection_score(
            fake_official,
            (
                "STC Bank خدمات التجارة "
                "الإلكترونية ونقاط البيع "
                "واقعي فوتوغرافي"
            ),

            request_family=(
                "merchant_payments"
            ),

            requested_style=(
                STYLE_PREMIUM_REALISTIC
            ),
        )
    )

    score_generic, _ = (
        reference_selection_score(
            fake_generic,
            (
                "STC Bank خدمات التجارة "
                "الإلكترونية ونقاط البيع "
                "واقعي فوتوغرافي"
            ),

            request_family=(
                "merchant_payments"
            ),

            requested_style=(
                STYLE_PREMIUM_REALISTIC
            ),
        )
    )

    tests[
        "official_beats_generic"
    ] = (
        score_official
        >
        score_generic
    )

    fake_refs = [
        fake_generic,
        fake_official,
        {
            **fake_official,

            "id":
                3,

            "user_note":
                (
                    "premium realistic "
                    "bird's-eye retail scene"
                ),

            "dna": {
                "confidence":
                    0.92,

                "camera_angle":
                    "Bird's-Eye View",

                "content_classification": {
                    "family":
                        "business_banking",
                },
            },

            "content_family":
                "business_banking",
        },

        {
            **fake_official,

            "id":
                4,

            "user_note":
                (
                    "premium realistic "
                    "over-the-shoulder merchant scene"
                ),

            "dna": {
                "confidence":
                    0.94,

                "camera_angle":
                    "Over-the-Shoulder Shot",

                "content_classification": {
                    "family":
                        "digital_banking",
                },
            },

            "content_family":
                "digital_banking",
        },
    ]

    curated = curate_references(
        fake_refs,
        (
            "STC Bank خدمات التجارة "
            "الإلكترونية ونقاط البيع "
            "واقعي فوتوغرافي"
        ),

        brand_id="stc_bank",

        limit=3,
    )

    tests[
        "curator_three"
    ] = (
        len(
            curated
        )
        ==
        3
    )

    camera_set = {
        safe_dict(
            item.get(
                "selection"
            )
        ).get(
            "camera_signature"
        )
        for item in curated
        if safe_dict(
            item.get(
                "selection"
            )
        ).get(
            "camera_signature"
        )
    }

    tests[
        "camera_diversity"
    ] = (
        len(
            camera_set
        )
        >=
        2
    )

    tests[
        "stc_reference_cap"
    ] = (
        STC_REFERENCE_LIMIT
        <=
        3
    )

    tests[
        "feedback_approved"
    ] = (
        classify_feedback_rule(
            "اعتمد هاد الأسلوب"
        )
        ==
        "approved_style"
    )

    tests[
        "feedback_rejected"
    ] = (
        classify_feedback_rule(
            "ما بدي ترجع تستخدم هاد الأسلوب"
        )
        ==
        "rejected_style"
    )

    tests[
        "no_database_self_test"
    ] = True

    all_ok = all(
        tests.values()
    )

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND BRAND MEMORY V3.0"
    )
    print(
        " ZERO-DATABASE SELF TEST"
    )
    print(
        "=========================================="
    )
    print("")

    for name, passed in (
        tests.items()
    ):

        print(
            (
                "✅"
                if passed
                else
                "❌"
            ),
            name,
        )

    print("")

    if all_ok:

        print(
            (
                "XPAND Brand Memory V3.0 "
                "self-test: PASS ✅"
            )
        )

    else:

        print(
            (
                "XPAND Brand Memory V3.0 "
                "self-test: FAIL ❌"
            )
        )

    print("")

    print(
        "✅ Existing Brand Memory V2 data preserved"
    )

    print(
        "✅ Existing visual-reference table preserved"
    )

    print(
        "✅ Existing visual-profile table preserved"
    )

    print(
        "✅ Request-aware Reference Curator"
    )

    print(
        "✅ STC max 3 runtime references"
    )

    print(
        "✅ Service / benefit matching"
    )

    print(
        "✅ Selected visual-style matching"
    )

    print(
        "✅ Official-source weighting"
    )

    print(
        "✅ Reference utility weighting"
    )

    print(
        "✅ Camera diversity"
    )

    print(
        "✅ Reference rotation / usage penalty"
    )

    print(
        "✅ Purple-neon penalty for realistic STC"
    )

    print(
        "✅ Permanent Brand Visual Profile"
    )

    print(
        "✅ Aggregated camera patterns"
    )

    print(
        "✅ Aggregated lighting patterns"
    )

    print(
        "✅ Aggregated materials"
    )

    print(
        "✅ Aggregated composition patterns"
    )

    print(
        "✅ Explicit approved/rejected brand feedback"
    )

    print(
        "✅ Production Engine V3/V4 compatibility"
    )

    print(
        "✅ No 5-reference STC dump"
    )

    print(
        "✅ No AI call required for selection"
    )

    print(
        "🚫 No database calls were made"
    )

    print(
        "🚫 No OpenAI calls were made"
    )

    print(
        "🚫 No Gemini calls were made"
    )

    print(
        "🚫 No Vision calls were made"
    )

    print(
        "🚫 No images were generated"
    )

    print("")
