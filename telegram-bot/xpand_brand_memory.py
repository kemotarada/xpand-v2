# =========================================================
# XPAND BRAND MEMORY V1.0
#
# Persistent per-brand creative memory for XPAND.
#
# Supports:
# - Separate memory per client / brand
# - Active brand context
# - Approved creative directions
# - Rejected creative directions
# - User preferences / corrections
# - Visual references
# - Product Lock metadata
# - Campaign Visual Bibles
#
# IMPORTANT:
# - Does NOT store raw image bytes in PostgreSQL.
# - Stores Telegram file IDs + structured visual DNA.
# - Sensitive banking/card data must NEVER be stored.
# =========================================================

from __future__ import annotations

import json
import re

from typing import (
    Any,
    Dict,
    List,
    Optional,
)


VERSION = "1.0"

MODULE_NAME = "XPAND Brand Memory"


# =========================================================
# HELPERS
# =========================================================

def clean_text(
    value: Any,
    limit: int = 12000
) -> str:

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


def normalize_text(
    value: Any
) -> str:

    text = clean_text(
        value,
        12000
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


def contains_any(
    text: str,
    markers: List[str]
) -> bool:

    source = normalize_text(
        text
    )

    return any(
        normalize_text(marker)
        in source
        for marker in markers
    )


def safe_brand_id(
    value: Any
) -> str:

    text = normalize_text(
        value
    )

    aliases = {
        "stc": "stc_bank",
        "stc bank": "stc_bank",
        "stcbank": "stc_bank",
        "بنك stc": "stc_bank",
        "بنك اس تي سي": "stc_bank",
        "xpand": "xpand",
        "اكسباند": "xpand",
        "إكسباند": "xpand",
    }

    if text in aliases:
        return aliases[text]

    text = re.sub(
        r"[^a-z0-9\u0600-\u06ff]+",
        "_",
        text
    ).strip("_")

    return text[:100]


def json_string(
    value: Any
) -> str:

    return json.dumps(
        value
        if value is not None
        else {},
        ensure_ascii=False
    )


def parse_json(
    value: Any,
    default: Any = None
) -> Any:

    if default is None:
        default = {}

    if isinstance(
        value,
        (
            dict,
            list,
        )
    ):
        return value

    if not value:
        return default

    try:
        return json.loads(
            str(value)
        )

    except Exception:
        return default


# =========================================================
# DATABASE
# =========================================================

def ensure_tables(
    core
) -> None:

    with core.db_connect() as conn:

        with conn.cursor() as cur:

            # -------------------------------------------------
            # BRAND PROFILE
            # -------------------------------------------------

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS
                xpand_brand_profiles
                (
                    user_id BIGINT NOT NULL,

                    brand_id TEXT NOT NULL,

                    brand_name TEXT NOT NULL,

                    profile_json JSONB NOT NULL
                        DEFAULT '{}'::jsonb,

                    active BOOLEAN NOT NULL
                        DEFAULT TRUE,

                    created_at TIMESTAMPTZ NOT NULL
                        DEFAULT NOW(),

                    updated_at TIMESTAMPTZ NOT NULL
                        DEFAULT NOW(),

                    PRIMARY KEY (
                        user_id,
                        brand_id
                    )
                );
                """
            )

            # -------------------------------------------------
            # BRAND RULES
            # -------------------------------------------------

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS
                xpand_brand_rules
                (
                    id BIGSERIAL PRIMARY KEY,

                    user_id BIGINT NOT NULL,

                    brand_id TEXT NOT NULL,

                    rule_type TEXT NOT NULL,

                    content TEXT NOT NULL,

                    source_channel TEXT NOT NULL
                        DEFAULT 'telegram_text',

                    active BOOLEAN NOT NULL
                        DEFAULT TRUE,

                    created_at TIMESTAMPTZ NOT NULL
                        DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_xpand_brand_rules_lookup
                ON xpand_brand_rules
                (
                    user_id,
                    brand_id,
                    active,
                    created_at DESC
                );
                """
            )

            # -------------------------------------------------
            # VISUAL REFERENCES
            # -------------------------------------------------

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS
                xpand_visual_references
                (
                    id BIGSERIAL PRIMARY KEY,

                    user_id BIGINT NOT NULL,

                    brand_id TEXT NOT NULL
                        DEFAULT '',

                    telegram_file_id TEXT NOT NULL
                        DEFAULT '',

                    telegram_file_unique_id TEXT NOT NULL
                        DEFAULT '',

                    reference_role TEXT NOT NULL
                        DEFAULT 'style_reference',

                    user_note TEXT NOT NULL
                        DEFAULT '',

                    dna_json JSONB NOT NULL
                        DEFAULT '{}'::jsonb,

                    product_lock_json JSONB NOT NULL
                        DEFAULT '{}'::jsonb,

                    active BOOLEAN NOT NULL
                        DEFAULT TRUE,

                    created_at TIMESTAMPTZ NOT NULL
                        DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_xpand_visual_reference_lookup
                ON xpand_visual_references
                (
                    user_id,
                    brand_id,
                    active,
                    created_at DESC
                );
                """
            )

            # -------------------------------------------------
            # ACTIVE BRAND / CAMPAIGN CONTEXT
            # -------------------------------------------------

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS
                xpand_brand_context
                (
                    user_id BIGINT PRIMARY KEY,

                    active_brand_id TEXT NOT NULL
                        DEFAULT '',

                    active_campaign_key TEXT NOT NULL
                        DEFAULT '',

                    updated_at TIMESTAMPTZ NOT NULL
                        DEFAULT NOW()
                );
                """
            )

            # -------------------------------------------------
            # CAMPAIGN VISUAL BIBLE
            # -------------------------------------------------

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS
                xpand_campaign_bibles
                (
                    id BIGSERIAL PRIMARY KEY,

                    user_id BIGINT NOT NULL,

                    brand_id TEXT NOT NULL,

                    campaign_key TEXT NOT NULL,

                    title TEXT NOT NULL
                        DEFAULT '',

                    bible_json JSONB NOT NULL
                        DEFAULT '{}'::jsonb,

                    active BOOLEAN NOT NULL
                        DEFAULT TRUE,

                    created_at TIMESTAMPTZ NOT NULL
                        DEFAULT NOW(),

                    updated_at TIMESTAMPTZ NOT NULL
                        DEFAULT NOW(),

                    UNIQUE (
                        user_id,
                        brand_id,
                        campaign_key
                    )
                );
                """
            )


# =========================================================
# BRAND PROFILE
# =========================================================

def upsert_brand_profile(
    core,
    user_id,
    brand_id: str,
    brand_name: str,
    profile: Dict[str, Any]
) -> None:

    ensure_tables(
        core
    )

    brand_id = safe_brand_id(
        brand_id
    )

    if not brand_id:
        return

    with core.db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO xpand_brand_profiles
                (
                    user_id,
                    brand_id,
                    brand_name,
                    profile_json,
                    active,
                    updated_at
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s::jsonb,
                    TRUE,
                    NOW()
                )

                ON CONFLICT
                (
                    user_id,
                    brand_id
                )
                DO UPDATE SET

                    brand_name =
                        EXCLUDED.brand_name,

                    profile_json =
                        EXCLUDED.profile_json,

                    active =
                        TRUE,

                    updated_at =
                        NOW();
                """,
                (
                    user_id,
                    brand_id,
                    clean_text(
                        brand_name,
                        300
                    ),
                    json_string(
                        profile
                    ),
                )
            )


def get_brand_profile(
    core,
    user_id,
    brand_id: str
) -> Dict[str, Any]:

    ensure_tables(
        core
    )

    brand_id = safe_brand_id(
        brand_id
    )

    if not brand_id:
        return {}

    with core.db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    brand_name,
                    profile_json
                FROM xpand_brand_profiles
                WHERE
                    user_id = %s
                    AND brand_id = %s
                    AND active = TRUE
                LIMIT 1;
                """,
                (
                    user_id,
                    brand_id,
                )
            )

            row = cur.fetchone()

    if not row:
        return {}

    return {
        "brand_id":
            brand_id,

        "brand_name":
            clean_text(
                row[0],
                300
            ),

        "profile":
            parse_json(
                row[1],
                {}
            ),
    }


# =========================================================
# ACTIVE CONTEXT
# =========================================================

def set_active_brand(
    core,
    user_id,
    brand_id: str,
    campaign_key: str = ""
) -> None:

    ensure_tables(
        core
    )

    brand_id = safe_brand_id(
        brand_id
    )

    with core.db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO xpand_brand_context
                (
                    user_id,
                    active_brand_id,
                    active_campaign_key,
                    updated_at
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    NOW()
                )

                ON CONFLICT
                (
                    user_id
                )
                DO UPDATE SET

                    active_brand_id =
                        EXCLUDED.active_brand_id,

                    active_campaign_key =
                        CASE
                            WHEN
                                EXCLUDED.active_campaign_key <> ''
                            THEN
                                EXCLUDED.active_campaign_key
                            ELSE
                                xpand_brand_context.active_campaign_key
                        END,

                    updated_at =
                        NOW();
                """,
                (
                    user_id,
                    brand_id,
                    clean_text(
                        campaign_key,
                        200
                    ),
                )
            )


def get_active_context(
    core,
    user_id
) -> Dict[str, str]:

    ensure_tables(
        core
    )

    with core.db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    active_brand_id,
                    active_campaign_key
                FROM xpand_brand_context
                WHERE user_id = %s
                LIMIT 1;
                """,
                (
                    user_id,
                )
            )

            row = cur.fetchone()

    if not row:
        return {
            "brand_id": "",
            "campaign_key": "",
        }

    return {
        "brand_id":
            clean_text(
                row[0],
                100
            ),

        "campaign_key":
            clean_text(
                row[1],
                200
            ),
    }


def get_active_brand(
    core,
    user_id
) -> str:

    return get_active_context(
        core,
        user_id
    ).get(
        "brand_id",
        ""
    )


# =========================================================
# BRAND RULES
# =========================================================

VALID_RULE_TYPES = {
    "approved_style",
    "rejected_style",
    "preference",
    "correction",
    "product_rule",
    "camera_rule",
    "lighting_rule",
    "material_rule",
    "composition_rule",
    "campaign_rule",
    "general_rule",
}


def add_brand_rule(
    core,
    user_id,
    brand_id: str,
    rule_type: str,
    content: str,
    source_channel: str = "telegram_text"
) -> Optional[int]:

    ensure_tables(
        core
    )

    brand_id = safe_brand_id(
        brand_id
    )

    content = clean_text(
        content,
        5000
    )

    if (
        not brand_id
        or
        not content
    ):
        return None

    rule_type = clean_text(
        rule_type,
        100
    ).lower()

    if rule_type not in VALID_RULE_TYPES:
        rule_type = "general_rule"

    with core.db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO xpand_brand_rules
                (
                    user_id,
                    brand_id,
                    rule_type,
                    content,
                    source_channel,
                    active
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    TRUE
                )
                RETURNING id;
                """,
                (
                    user_id,
                    brand_id,
                    rule_type,
                    content,
                    clean_text(
                        source_channel,
                        100
                    ),
                )
            )

            row = cur.fetchone()

    return (
        int(
            row[0]
        )
        if row
        else
        None
    )


def load_brand_rules(
    core,
    user_id,
    brand_id: str,
    limit: int = 60
) -> List[Dict[str, Any]]:

    ensure_tables(
        core
    )

    brand_id = safe_brand_id(
        brand_id
    )

    if not brand_id:
        return []

    limit = max(
        1,
        min(
            int(
                limit
                or
                60
            ),
            200
        )
    )

    with core.db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    id,
                    rule_type,
                    content,
                    source_channel,
                    created_at
                FROM xpand_brand_rules
                WHERE
                    user_id = %s
                    AND brand_id = %s
                    AND active = TRUE
                ORDER BY
                    created_at DESC,
                    id DESC
                LIMIT %s;
                """,
                (
                    user_id,
                    brand_id,
                    limit,
                )
            )

            rows = cur.fetchall()

    return [
        {
            "id":
                int(
                    row[0]
                ),

            "rule_type":
                clean_text(
                    row[1],
                    100
                ),

            "content":
                clean_text(
                    row[2],
                    5000
                ),

            "source_channel":
                clean_text(
                    row[3],
                    100
                ),

            "created_at":
                str(
                    row[4]
                ),
        }
        for row in rows
    ]


# =========================================================
# EXPLICIT FEEDBACK LEARNING
# =========================================================

APPROVE_MARKERS = [
    "هذا ممتاز",
    "هاد ممتاز",
    "هاي ممتازة",
    "هاي ممتازه",
    "اعتمد هذا الاسلوب",
    "اعتمد هذا الأسلوب",
    "اعتمد هاد الاسلوب",
    "اعتمد هاد الأسلوب",
    "اعتمدها",
    "ثبت هذا الاسلوب",
    "ثبّت هذا الأسلوب",
    "خلي هاد مرجع",
    "خلي هذا مرجع",
    "هذا المرجع ممتاز",
]


REJECT_MARKERS = [
    "لا ترجع لهذا الاسلوب",
    "لا ترجع لهذا الأسلوب",
    "لا ترجع لهاد الاسلوب",
    "لا ترجع لهاد الأسلوب",
    "لا تستخدم هذا الاسلوب",
    "لا تستخدم هذا الأسلوب",
    "لا تستخدم هاد الاسلوب",
    "لا تستخدم هاد الأسلوب",
    "ما بدي هذا الاسلوب",
    "ما بدي هذا الأسلوب",
    "ما بدي هاد الاسلوب",
    "ما بدي هاد الأسلوب",
    "لا تعيد هاي الفكرة",
    "لا تعيد هاد",
    "لا تعيد هذا",
]


CORRECTION_MARKERS = [
    "خلي",
    "بدل",
    "غير",
    "غيّر",
    "مش هيك",
    "الصحيح",
    "المفروض",
    "من هسا",
    "بدي دايما",
    "بدي دائم",
]


def learn_explicit_feedback(
    core,
    user_id,
    text: str,
    brand_id: str = "",
    source_channel: str = "telegram_text"
) -> Dict[str, Any]:

    raw = clean_text(
        text,
        5000
    )

    if not raw:
        return {
            "saved": False,
            "rule_type": "",
            "brand_id": "",
        }

    brand_id = safe_brand_id(
        brand_id
        or
        get_active_brand(
            core,
            user_id
        )
    )

    if not brand_id:
        return {
            "saved": False,
            "rule_type": "",
            "brand_id": "",
        }

    rule_type = ""

    if contains_any(
        raw,
        APPROVE_MARKERS
    ):
        rule_type = "approved_style"

    elif contains_any(
        raw,
        REJECT_MARKERS
    ):
        rule_type = "rejected_style"

    elif contains_any(
        raw,
        CORRECTION_MARKERS
    ):
        rule_type = "correction"

    if not rule_type:
        return {
            "saved": False,
            "rule_type": "",
            "brand_id": brand_id,
        }

    rule_id = add_brand_rule(
        core,
        user_id,
        brand_id,
        rule_type,
        raw,
        source_channel=
            source_channel
    )

    return {
        "saved":
            bool(
                rule_id
            ),

        "rule_id":
            rule_id,

        "rule_type":
            rule_type,

        "brand_id":
            brand_id,
    }


# =========================================================
# VISUAL REFERENCES
# =========================================================

VALID_REFERENCE_ROLES = {
    "product_reference",
    "environment_reference",
    "camera_reference",
    "color_reference",
    "style_reference",
    "lighting_reference",
    "composition_reference",
    "person_reference",
    "campaign_reference",
    "mixed_reference",
}


def normalize_reference_role(
    value: str
) -> str:

    value = clean_text(
        value,
        100
    ).lower()

    if value in VALID_REFERENCE_ROLES:
        return value

    return "style_reference"


def save_visual_reference(
    core,
    user_id,
    *,
    brand_id: str = "",
    telegram_file_id: str = "",
    telegram_file_unique_id: str = "",
    reference_role: str = "style_reference",
    user_note: str = "",
    dna: Optional[Dict[str, Any]] = None,
    product_lock: Optional[Dict[str, Any]] = None
) -> Optional[int]:

    ensure_tables(
        core
    )

    brand_id = safe_brand_id(
        brand_id
    )

    reference_role = normalize_reference_role(
        reference_role
    )

    with core.db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO xpand_visual_references
                (
                    user_id,
                    brand_id,
                    telegram_file_id,
                    telegram_file_unique_id,
                    reference_role,
                    user_note,
                    dna_json,
                    product_lock_json,
                    active
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s::jsonb,
                    %s::jsonb,
                    TRUE
                )
                RETURNING id;
                """,
                (
                    user_id,
                    brand_id,
                    clean_text(
                        telegram_file_id,
                        1500
                    ),
                    clean_text(
                        telegram_file_unique_id,
                        1500
                    ),
                    reference_role,
                    clean_text(
                        user_note,
                        5000
                    ),
                    json_string(
                        dna
                        or
                        {}
                    ),
                    json_string(
                        product_lock
                        or
                        {}
                    ),
                )
            )

            row = cur.fetchone()

    if brand_id:
        set_active_brand(
            core,
            user_id,
            brand_id
        )

    return (
        int(
            row[0]
        )
        if row
        else
        None
    )


def load_visual_references(
    core,
    user_id,
    *,
    brand_id: str = "",
    limit: int = 12
) -> List[Dict[str, Any]]:

    ensure_tables(
        core
    )

    brand_id = safe_brand_id(
        brand_id
    )

    limit = max(
        1,
        min(
            int(
                limit
                or
                12
            ),
            50
        )
    )

    if brand_id:

        sql = """
            SELECT
                id,
                brand_id,
                telegram_file_id,
                telegram_file_unique_id,
                reference_role,
                user_note,
                dna_json,
                product_lock_json,
                created_at
            FROM xpand_visual_references
            WHERE
                user_id = %s
                AND brand_id = %s
                AND active = TRUE
            ORDER BY
                created_at DESC,
                id DESC
            LIMIT %s;
        """

        params = (
            user_id,
            brand_id,
            limit,
        )

    else:

        sql = """
            SELECT
                id,
                brand_id,
                telegram_file_id,
                telegram_file_unique_id,
                reference_role,
                user_note,
                dna_json,
                product_lock_json,
                created_at
            FROM xpand_visual_references
            WHERE
                user_id = %s
                AND active = TRUE
            ORDER BY
                created_at DESC,
                id DESC
            LIMIT %s;
        """

        params = (
            user_id,
            limit,
        )

    with core.db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                sql,
                params
            )

            rows = cur.fetchall()

    output = []

    for row in rows:

        output.append(
            {
                "id":
                    int(
                        row[0]
                    ),

                "brand_id":
                    clean_text(
                        row[1],
                        100
                    ),

                "telegram_file_id":
                    clean_text(
                        row[2],
                        1500
                    ),

                "telegram_file_unique_id":
                    clean_text(
                        row[3],
                        1500
                    ),

                "reference_role":
                    clean_text(
                        row[4],
                        100
                    ),

                "user_note":
                    clean_text(
                        row[5],
                        5000
                    ),

                "dna":
                    parse_json(
                        row[6],
                        {}
                    ),

                "product_lock":
                    parse_json(
                        row[7],
                        {}
                    ),

                "created_at":
                    str(
                        row[8]
                    ),
            }
        )

    return output


# =========================================================
# CAMPAIGN VISUAL BIBLE
# =========================================================

def save_campaign_bible(
    core,
    user_id,
    brand_id: str,
    campaign_key: str,
    title: str,
    bible: Dict[str, Any]
) -> None:

    ensure_tables(
        core
    )

    brand_id = safe_brand_id(
        brand_id
    )

    campaign_key = clean_text(
        campaign_key,
        200
    )

    if (
        not brand_id
        or
        not campaign_key
    ):
        return

    with core.db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO xpand_campaign_bibles
                (
                    user_id,
                    brand_id,
                    campaign_key,
                    title,
                    bible_json,
                    active,
                    updated_at
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s::jsonb,
                    TRUE,
                    NOW()
                )

                ON CONFLICT
                (
                    user_id,
                    brand_id,
                    campaign_key
                )
                DO UPDATE SET

                    title =
                        EXCLUDED.title,

                    bible_json =
                        EXCLUDED.bible_json,

                    active =
                        TRUE,

                    updated_at =
                        NOW();
                """,
                (
                    user_id,
                    brand_id,
                    campaign_key,
                    clean_text(
                        title,
                        500
                    ),
                    json_string(
                        bible
                    ),
                )
            )

    set_active_brand(
        core,
        user_id,
        brand_id,
        campaign_key=
            campaign_key
    )


def load_campaign_bible(
    core,
    user_id,
    brand_id: str,
    campaign_key: str = ""
) -> Dict[str, Any]:

    ensure_tables(
        core
    )

    brand_id = safe_brand_id(
        brand_id
    )

    campaign_key = clean_text(
        campaign_key,
        200
    )

    if not brand_id:
        return {}

    with core.db_connect() as conn:

        with conn.cursor() as cur:

            if campaign_key:

                cur.execute(
                    """
                    SELECT
                        campaign_key,
                        title,
                        bible_json,
                        updated_at
                    FROM xpand_campaign_bibles
                    WHERE
                        user_id = %s
                        AND brand_id = %s
                        AND campaign_key = %s
                        AND active = TRUE
                    LIMIT 1;
                    """,
                    (
                        user_id,
                        brand_id,
                        campaign_key,
                    )
                )

            else:

                cur.execute(
                    """
                    SELECT
                        campaign_key,
                        title,
                        bible_json,
                        updated_at
                    FROM xpand_campaign_bibles
                    WHERE
                        user_id = %s
                        AND brand_id = %s
                        AND active = TRUE
                    ORDER BY
                        updated_at DESC,
                        id DESC
                    LIMIT 1;
                    """,
                    (
                        user_id,
                        brand_id,
                    )
                )

            row = cur.fetchone()

    if not row:
        return {}

    return {
        "campaign_key":
            clean_text(
                row[0],
                200
            ),

        "title":
            clean_text(
                row[1],
                500
            ),

        "bible":
            parse_json(
                row[2],
                {}
            ),

        "updated_at":
            str(
                row[3]
            ),
    }


# =========================================================
# BRAND CREATIVE CONTEXT
# =========================================================

def build_brand_memory_context(
    core,
    user_id,
    brand_id: str,
    *,
    max_rules: int = 40,
    max_references: int = 10
) -> Dict[str, Any]:

    brand_id = safe_brand_id(
        brand_id
    )

    if not brand_id:
        return {
            "brand_id": "",
            "profile": {},
            "rules": [],
            "references": [],
            "campaign": {},
        }

    profile = get_brand_profile(
        core,
        user_id,
        brand_id
    )

    rules = load_brand_rules(
        core,
        user_id,
        brand_id,
        limit=
            max_rules
    )

    references = load_visual_references(
        core,
        user_id,
        brand_id=
            brand_id,
        limit=
            max_references
    )

    campaign = load_campaign_bible(
        core,
        user_id,
        brand_id
    )

    return {
        "brand_id":
            brand_id,

        "profile":
            profile,

        "rules":
            rules,

        "references":
            references,

        "campaign":
            campaign,
    }


# =========================================================
# SELF TEST
# =========================================================

if __name__ == "__main__":

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND BRAND MEMORY V1.0"
    )
    print(
        "=========================================="
    )
    print("")
    print(
        "✅ Per-brand profiles"
    )
    print(
        "✅ Approved / rejected style rules"
    )
    print(
        "✅ Visual Reference DNA storage"
    )
    print(
        "✅ Product Lock storage"
    )
    print(
        "✅ Active brand context"
    )
    print(
        "✅ Campaign Visual Bible"
    )
    print(
        "✅ Explicit feedback learning"
    )
    print(
        "🚫 No raw image bytes stored in PostgreSQL"
    )
    print("")
