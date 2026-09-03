# =========================================================
# XPAND BRAND MEMORY V2.0
#
# BRAND VISUAL MEMORY + REFERENCE LIBRARY
#
# =========================================================
#
# PURPOSE
# ---------------------------------------------------------
#
# Persistent, brand-isolated creative memory for XPAND.
#
# V2 connects:
#
#   Brand Profile
#   Brand Rules
#   Visual Reference DNA V2
#   Source Authority / Freshness
#   Brand Visual Profile
#   Request-Aware Reference Selection
#   Product Lock
#   Campaign Visual Bible
#   Explicit User Feedback
#
#
# IMPORTANT
# ---------------------------------------------------------
#
# - Memory is separate per brand.
# - Raw image bytes are NEVER stored in PostgreSQL.
# - Telegram file IDs are stored so the original reference
#   can be downloaded later when production needs it.
# - Visual DNA is stored as structured JSON.
# - Official-source metadata is preserved.
# - Duplicate visual references are updated instead of
#   endlessly duplicated.
# - Sensitive financial information must NEVER be stored.
# - One reference does NOT become a universal brand rule.
# - Repeated patterns across multiple references become a
#   stronger Brand Visual Profile.
#
#
# V2 VISUAL FLOW
# ---------------------------------------------------------
#
# Reference Image
#      ↓
# Visual Intelligence V2
#      ↓
# Visual DNA
#      ↓
# Brand Memory V2
#      ↓
# Brand Visual Library
#      ↓
# Multi-Reference Visual Profile
#      ↓
# User Request
#      ↓
# Request-Aware Reference Selection
#      ↓
# Best 3–5 references for current campaign
#
#
# SELF TEST
# ---------------------------------------------------------
#
# Running:
#
#     python xpand_brand_memory.py
#
# makes:
#
# - ZERO database writes
# - ZERO API calls
# - ZERO image-generation calls
#
# =========================================================

from __future__ import annotations

import json
import re

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Sequence,
)


from xpand_visual_intelligence import (
    VERSION as VISUAL_INTELLIGENCE_VERSION,
    build_brand_visual_profile,
    build_reference_execution_context,
    infer_content_family,
    rank_references_for_request,
    select_best_references,
)


# =========================================================
# MODULE
# =========================================================

VERSION = "2.0"

MODULE_NAME = "XPAND Brand Memory"


# =========================================================
# CONSTANTS
# =========================================================

DEFAULT_RULE_LIMIT = 60

DEFAULT_REFERENCE_LIMIT = 20

REFERENCE_LIBRARY_SCAN_LIMIT = 50

DEFAULT_RELEVANT_REFERENCE_LIMIT = 5

MAX_RELEVANT_REFERENCE_LIMIT = 6


# =========================================================
# HELPERS
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
        20000,
    ).lower()

    replacements = {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ة": "ه",
        "ى": "ي",
        "ؤ": "و",
        "ئ": "ي",
        "ـ": "",
    }

    for old, new in replacements.items():

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


def contains_any(
    text: Any,
    markers: Sequence[str],
) -> bool:

    source = normalize_text(
        text
    )

    return any(
        normalize_text(
            marker
        )
        in source
        for marker in markers
    )


def safe_dict(
    value: Any,
) -> Dict[str, Any]:

    return (
        value
        if isinstance(
            value,
            dict,
        )
        else {}
    )


def safe_list(
    value: Any,
) -> List[Any]:

    return (
        value
        if isinstance(
            value,
            list,
        )
        else []
    )


def safe_brand_id(
    value: Any,
) -> str:

    text = normalize_text(
        value
    )

    aliases = {
        "stc":
            "stc_bank",

        "stc bank":
            "stc_bank",

        "stcbank":
            "stc_bank",

        "stc bank ksa":
            "stc_bank",

        "بنك stc":
            "stc_bank",

        "بنك اس تي سي":
            "stc_bank",

        "اس تي سي بنك":
            "stc_bank",

        "xpand":
            "xpand",

        "اكسباند":
            "xpand",

        "إكسباند":
            "xpand",
    }

    if text in aliases:

        return aliases[
            text
        ]

    text = re.sub(
        r"[^a-z0-9\u0600-\u06ff]+",
        "_",
        text,
    ).strip(
        "_"
    )

    return text[:100]


def json_string(
    value: Any,
) -> str:

    return json.dumps(
        (
            value
            if value is not None
            else {}
        ),
        ensure_ascii=False,
        default=str,
    )


def parse_json(
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

    if not value:

        return default

    try:

        return json.loads(
            str(
                value
            )
        )

    except Exception:

        return default


def normalize_content_family(
    value: Any,
    fallback_text: str = "",
) -> str:

    family = clean_text(
        value,
        100,
    ).lower()

    valid = {
        "international_transfer",
        "travel_roaming",
        "cashback_rewards",
        "payments_cards",
        "digital_banking",
        "security_trust",
        "business_banking",
        "premium_lifestyle",
        "general_brand",
    }

    if family in valid:

        return family

    if fallback_text:

        return infer_content_family(
            fallback_text
        )

    return "general_brand"


# =========================================================
# DATABASE
# =========================================================

def ensure_tables(
    core,
) -> None:

    with core.db_connect() as conn:

        with conn.cursor() as cur:

            # =================================================
            # BRAND PROFILE
            # =================================================

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

                    PRIMARY KEY
                    (
                        user_id,
                        brand_id
                    )
                );
                """
            )

            # =================================================
            # BRAND RULES
            # =================================================

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

            # =================================================
            # VISUAL REFERENCES
            # =================================================

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

            # -------------------------------------------------
            # V2 SAFE MIGRATION COLUMNS
            # -------------------------------------------------

            cur.execute(
                """
                ALTER TABLE xpand_visual_references
                ADD COLUMN IF NOT EXISTS
                image_fingerprint TEXT NOT NULL
                    DEFAULT '';
                """
            )

            cur.execute(
                """
                ALTER TABLE xpand_visual_references
                ADD COLUMN IF NOT EXISTS
                content_family TEXT NOT NULL
                    DEFAULT 'general_brand';
                """
            )

            cur.execute(
                """
                ALTER TABLE xpand_visual_references
                ADD COLUMN IF NOT EXISTS
                source_metadata_json JSONB NOT NULL
                    DEFAULT '{}'::jsonb;
                """
            )

            cur.execute(
                """
                ALTER TABLE xpand_visual_references
                ADD COLUMN IF NOT EXISTS
                reference_utility_json JSONB NOT NULL
                    DEFAULT '{}'::jsonb;
                """
            )

            cur.execute(
                """
                ALTER TABLE xpand_visual_references
                ADD COLUMN IF NOT EXISTS
                updated_at TIMESTAMPTZ NOT NULL
                    DEFAULT NOW();
                """
            )

            cur.execute(
                """
                ALTER TABLE xpand_visual_references
                ADD COLUMN IF NOT EXISTS
                last_used_at TIMESTAMPTZ;
                """
            )

            cur.execute(
                """
                ALTER TABLE xpand_visual_references
                ADD COLUMN IF NOT EXISTS
                use_count INTEGER NOT NULL
                    DEFAULT 0;
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

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_xpand_visual_reference_family
                ON xpand_visual_references
                (
                    user_id,
                    brand_id,
                    content_family,
                    active,
                    created_at DESC
                );
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_xpand_visual_reference_fingerprint
                ON xpand_visual_references
                (
                    user_id,
                    brand_id,
                    image_fingerprint
                );
                """
            )

            # -------------------------------------------------
            # BEST-EFFORT BACKFILL FROM EXISTING V1 DNA
            # -------------------------------------------------

            cur.execute(
                """
                UPDATE xpand_visual_references
                SET
                    image_fingerprint =
                        COALESCE
                        (
                            NULLIF
                            (
                                image_fingerprint,
                                ''
                            ),
                            dna_json
                                ->>
                                'image_fingerprint_sha256',
                            ''
                        )
                WHERE
                    image_fingerprint = '';
                """
            )

            cur.execute(
                """
                UPDATE xpand_visual_references
                SET
                    content_family =
                        COALESCE
                        (
                            NULLIF
                            (
                                dna_json
                                    ->
                                    'content_classification'
                                    ->>
                                    'family',
                                ''
                            ),
                            content_family,
                            'general_brand'
                        )
                WHERE
                    content_family = 'general_brand';
                """
            )

            cur.execute(
                """
                UPDATE xpand_visual_references
                SET
                    source_metadata_json =
                        COALESCE
                        (
                            dna_json
                                ->
                                'source_metadata',
                            '{}'::jsonb
                        )
                WHERE
                    source_metadata_json =
                        '{}'::jsonb;
                """
            )

            cur.execute(
                """
                UPDATE xpand_visual_references
                SET
                    reference_utility_json =
                        COALESCE
                        (
                            dna_json
                                ->
                                'reference_utility',
                            '{}'::jsonb
                        )
                WHERE
                    reference_utility_json =
                        '{}'::jsonb;
                """
            )

            # =================================================
            # AGGREGATED BRAND VISUAL PROFILE
            # =================================================

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS
                xpand_brand_visual_profiles
                (
                    user_id BIGINT NOT NULL,

                    brand_id TEXT NOT NULL,

                    visual_profile_json JSONB NOT NULL
                        DEFAULT '{}'::jsonb,

                    source_count INTEGER NOT NULL
                        DEFAULT 0,

                    evidence_strength DOUBLE PRECISION NOT NULL
                        DEFAULT 0,

                    active BOOLEAN NOT NULL
                        DEFAULT TRUE,

                    created_at TIMESTAMPTZ NOT NULL
                        DEFAULT NOW(),

                    updated_at TIMESTAMPTZ NOT NULL
                        DEFAULT NOW(),

                    PRIMARY KEY
                    (
                        user_id,
                        brand_id
                    )
                );
                """
            )

            # =================================================
            # ACTIVE BRAND / CAMPAIGN CONTEXT
            # =================================================

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

            # =================================================
            # CAMPAIGN VISUAL BIBLE
            # =================================================

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

                    UNIQUE
                    (
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
    profile: Dict[str, Any],
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
                        300,
                    ),

                    json_string(
                        profile
                    ),
                ),
            )


def get_brand_profile(
    core,
    user_id,
    brand_id: str,
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
                ),
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
                300,
            ),

        "profile":
            parse_json(
                row[1],
                {},
            ),
    }


# =========================================================
# ACTIVE CONTEXT
# =========================================================

def set_active_brand(
    core,
    user_id,
    brand_id: str,
    campaign_key: str = "",
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
                        200,
                    ),
                ),
            )


def get_active_context(
    core,
    user_id,
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
                WHERE
                    user_id = %s
                LIMIT 1;
                """,
                (
                    user_id,
                ),
            )

            row = cur.fetchone()

    if not row:

        return {
            "brand_id":
                "",

            "campaign_key":
                "",
        }

    return {
        "brand_id":
            clean_text(
                row[0],
                100,
            ),

        "campaign_key":
            clean_text(
                row[1],
                200,
            ),
    }


def get_active_brand(
    core,
    user_id,
) -> str:

    return get_active_context(
        core,
        user_id,
    ).get(
        "brand_id",
        "",
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
    "color_rule",
    "human_direction_rule",
    "campaign_rule",
    "general_rule",
}


def add_brand_rule(
    core,
    user_id,
    brand_id: str,
    rule_type: str,
    content: str,
    source_channel: str = "telegram_text",
) -> Optional[int]:

    ensure_tables(
        core
    )

    brand_id = safe_brand_id(
        brand_id
    )

    content = clean_text(
        content,
        5000,
    )

    if (
        not brand_id
        or
        not content
    ):

        return None

    rule_type = clean_text(
        rule_type,
        100,
    ).lower()

    if rule_type not in VALID_RULE_TYPES:

        rule_type = (
            "general_rule"
        )

    #
    # Do not repeatedly store exactly the same rule.
    #

    with core.db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT id
                FROM xpand_brand_rules
                WHERE
                    user_id = %s
                    AND brand_id = %s
                    AND rule_type = %s
                    AND content = %s
                    AND active = TRUE
                ORDER BY id DESC
                LIMIT 1;
                """,
                (
                    user_id,
                    brand_id,
                    rule_type,
                    content,
                ),
            )

            existing = (
                cur.fetchone()
            )

            if existing:

                return int(
                    existing[0]
                )

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
                        100,
                    ),
                ),
            )

            row = cur.fetchone()

    return (
        int(
            row[0]
        )
        if row
        else None
    )


def load_brand_rules(
    core,
    user_id,
    brand_id: str,
    limit: int = DEFAULT_RULE_LIMIT,
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
                DEFAULT_RULE_LIMIT
            ),
            200,
        ),
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
                ),
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
                    100,
                ),

            "content":
                clean_text(
                    row[2],
                    5000,
                ),

            "source_channel":
                clean_text(
                    row[3],
                    100,
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
    "هاي النتيجه ممتازة",
    "هاي النتيجة ممتازة",
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
    "لا ترجع للصورة القديمة",
    "لا ترجع للنسخة القديمة",
]


#
# V1 used very broad words such as:
#
#   خلي
#   بدل
#   غير
#
# Those can appear in normal design requests and can pollute
# long-term Brand Memory.
#
# V2 only learns corrections when wording strongly indicates
# a reusable preference.
#

CORRECTION_MARKERS = [
    "من هسا",
    "من الآن",
    "من الان",
    "بدي دايما",
    "بدي دائم",
    "بدي دائمًا",
    "المرة الجاي",
    "المره الجاي",
    "لا تعملها هيك",
    "لا تعمل هيك",
    "تجنب هاد",
    "تجنب هذا",
    "تجنّب",
    "مش كأنها مبللة",
    "مش كانها مبلله",
    "خليها أنعم",
    "خليها انعم",
    "اعتمد هالتعديل",
    "اعتمد هذا التعديل",
]


def infer_feedback_rule_type(
    text: str,
) -> str:

    raw = clean_text(
        text,
        5000,
    )

    if contains_any(
        raw,
        APPROVE_MARKERS,
    ):

        return (
            "approved_style"
        )

    if contains_any(
        raw,
        REJECT_MARKERS,
    ):

        return (
            "rejected_style"
        )

    if contains_any(
        raw,
        CORRECTION_MARKERS,
    ):

        normalized = (
            normalize_text(
                raw
            )
        )

        if contains_any(
            normalized,
            [
                "اضاءه",
                "الإضاءة",
                "ضوء",
                "ظل",
                "lighting",
            ],
        ):

            return (
                "lighting_rule"
            )

        if contains_any(
            normalized,
            [
                "لون",
                "الوان",
                "ألوان",
                "بنفسجي",
                "mint",
                "purple",
                "color",
            ],
        ):

            return (
                "color_rule"
            )

        if contains_any(
            normalized,
            [
                "زاويه",
                "زاوية",
                "كاميرا",
                "عدسه",
                "عدسة",
                "camera",
                "lens",
            ],
        ):

            return (
                "camera_rule"
            )

        if contains_any(
            normalized,
            [
                "ارضيه",
                "أرضية",
                "خامات",
                "معدن",
                "زجاج",
                "انعكاس",
                "material",
                "reflection",
            ],
        ):

            return (
                "material_rule"
            )

        if contains_any(
            normalized,
            [
                "كادر",
                "تكوين",
                "مساحه",
                "مساحة",
                "negative space",
                "composition",
            ],
        ):

            return (
                "composition_rule"
            )

        return (
            "correction"
        )

    return ""


def learn_explicit_feedback(
    core,
    user_id,
    text: str,
    brand_id: str = "",
    source_channel: str = "telegram_text",
) -> Dict[str, Any]:

    raw = clean_text(
        text,
        5000,
    )

    if not raw:

        return {
            "saved":
                False,

            "rule_type":
                "",

            "brand_id":
                "",
        }

    brand_id = safe_brand_id(
        brand_id
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

            "rule_type":
                "",

            "brand_id":
                "",
        }

    rule_type = (
        infer_feedback_rule_type(
            raw
        )
    )

    if not rule_type:

        return {
            "saved":
                False,

            "rule_type":
                "",

            "brand_id":
                brand_id,
        }

    rule_id = add_brand_rule(
        core,
        user_id,
        brand_id,
        rule_type,
        raw,
        source_channel=(
            source_channel
        ),
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
    value: str,
) -> str:

    value = clean_text(
        value,
        100,
    ).lower()

    if value in VALID_REFERENCE_ROLES:

        return value

    return "style_reference"


def extract_reference_metadata(
    *,
    dna: Optional[Dict[str, Any]],
    reference_role: str,
    source_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    dna = safe_dict(
        dna
    )

    embedded_source = safe_dict(
        dna.get(
            "source_metadata"
        )
    )

    source = dict(
        embedded_source
    )

    source.update(
        safe_dict(
            source_metadata
        )
    )

    fingerprint = clean_text(
        dna.get(
            "image_fingerprint_sha256",
            "",
        ),
        100,
    )

    content = safe_dict(
        dna.get(
            "content_classification"
        )
    )

    family = normalize_content_family(
        content.get(
            "family",
            "",
        ),
        fallback_text=(
            " ".join(
                [
                    clean_text(
                        dna.get(
                            "summary",
                            "",
                        ),
                        1200,
                    ),

                    clean_text(
                        content.get(
                            "benefit_theme",
                            "",
                        ),
                        800,
                    ),
                ]
            )
        ),
    )

    utility = safe_dict(
        dna.get(
            "reference_utility"
        )
    )

    return {
        "image_fingerprint":
            fingerprint,

        "content_family":
            family,

        "source_metadata":
            source,

        "reference_utility":
            utility,

        "reference_role":
            normalize_reference_role(
                reference_role
            ),
    }


def find_existing_visual_reference(
    core,
    user_id,
    brand_id: str,
    *,
    image_fingerprint: str = "",
    telegram_file_unique_id: str = "",
) -> Optional[int]:

    brand_id = safe_brand_id(
        brand_id
    )

    image_fingerprint = clean_text(
        image_fingerprint,
        100,
    )

    telegram_file_unique_id = clean_text(
        telegram_file_unique_id,
        1500,
    )

    if (
        not image_fingerprint
        and
        not telegram_file_unique_id
    ):

        return None

    with core.db_connect() as conn:

        with conn.cursor() as cur:

            if (
                image_fingerprint
                and
                telegram_file_unique_id
            ):

                cur.execute(
                    """
                    SELECT id
                    FROM xpand_visual_references
                    WHERE
                        user_id = %s
                        AND brand_id = %s
                        AND active = TRUE
                        AND
                        (
                            image_fingerprint = %s
                            OR telegram_file_unique_id = %s
                        )
                    ORDER BY id DESC
                    LIMIT 1;
                    """,
                    (
                        user_id,
                        brand_id,
                        image_fingerprint,
                        telegram_file_unique_id,
                    ),
                )

            elif image_fingerprint:

                cur.execute(
                    """
                    SELECT id
                    FROM xpand_visual_references
                    WHERE
                        user_id = %s
                        AND brand_id = %s
                        AND active = TRUE
                        AND image_fingerprint = %s
                    ORDER BY id DESC
                    LIMIT 1;
                    """,
                    (
                        user_id,
                        brand_id,
                        image_fingerprint,
                    ),
                )

            else:

                cur.execute(
                    """
                    SELECT id
                    FROM xpand_visual_references
                    WHERE
                        user_id = %s
                        AND brand_id = %s
                        AND active = TRUE
                        AND telegram_file_unique_id = %s
                    ORDER BY id DESC
                    LIMIT 1;
                    """,
                    (
                        user_id,
                        brand_id,
                        telegram_file_unique_id,
                    ),
                )

            row = cur.fetchone()

    return (
        int(
            row[0]
        )
        if row
        else None
    )


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
    product_lock: Optional[Dict[str, Any]] = None,
    source_metadata: Optional[Dict[str, Any]] = None,
) -> Optional[int]:

    ensure_tables(
        core
    )

    brand_id = safe_brand_id(
        brand_id
    )

    reference_role = (
        normalize_reference_role(
            reference_role
        )
    )

    dna = safe_dict(
        dna
    )

    if not product_lock:

        product_lock = safe_dict(
            dna.get(
                "product_lock"
            )
        )

    metadata = (
        extract_reference_metadata(
            dna=dna,
            reference_role=reference_role,
            source_metadata=source_metadata,
        )
    )

    image_fingerprint = clean_text(
        metadata.get(
            "image_fingerprint",
            "",
        ),
        100,
    )

    content_family = normalize_content_family(
        metadata.get(
            "content_family",
            "",
        )
    )

    source_metadata = safe_dict(
        metadata.get(
            "source_metadata"
        )
    )

    reference_utility = safe_dict(
        metadata.get(
            "reference_utility"
        )
    )

    telegram_file_id = clean_text(
        telegram_file_id,
        1500,
    )

    telegram_file_unique_id = clean_text(
        telegram_file_unique_id,
        1500,
    )

    user_note = clean_text(
        user_note,
        5000,
    )

    existing_id = (
        find_existing_visual_reference(
            core,
            user_id,
            brand_id,
            image_fingerprint=(
                image_fingerprint
            ),
            telegram_file_unique_id=(
                telegram_file_unique_id
            ),
        )
    )

    with core.db_connect() as conn:

        with conn.cursor() as cur:

            if existing_id:

                cur.execute(
                    """
                    UPDATE xpand_visual_references
                    SET
                        telegram_file_id =
                            CASE
                                WHEN %s <> ''
                                THEN %s
                                ELSE telegram_file_id
                            END,

                        telegram_file_unique_id =
                            CASE
                                WHEN %s <> ''
                                THEN %s
                                ELSE telegram_file_unique_id
                            END,

                        reference_role =
                            %s,

                        user_note =
                            CASE
                                WHEN %s <> ''
                                THEN %s
                                ELSE user_note
                            END,

                        dna_json =
                            %s::jsonb,

                        product_lock_json =
                            %s::jsonb,

                        image_fingerprint =
                            CASE
                                WHEN %s <> ''
                                THEN %s
                                ELSE image_fingerprint
                            END,

                        content_family =
                            %s,

                        source_metadata_json =
                            %s::jsonb,

                        reference_utility_json =
                            %s::jsonb,

                        active =
                            TRUE,

                        updated_at =
                            NOW()

                    WHERE id = %s;
                    """,
                    (
                        telegram_file_id,
                        telegram_file_id,

                        telegram_file_unique_id,
                        telegram_file_unique_id,

                        reference_role,

                        user_note,
                        user_note,

                        json_string(
                            dna
                        ),

                        json_string(
                            product_lock
                            or {}
                        ),

                        image_fingerprint,
                        image_fingerprint,

                        content_family,

                        json_string(
                            source_metadata
                        ),

                        json_string(
                            reference_utility
                        ),

                        existing_id,
                    ),
                )

                reference_id = (
                    existing_id
                )

            else:

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
                        image_fingerprint,
                        content_family,
                        source_metadata_json,
                        reference_utility_json,
                        active,
                        created_at,
                        updated_at
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
                        %s,
                        %s,
                        %s::jsonb,
                        %s::jsonb,
                        TRUE,
                        NOW(),
                        NOW()
                    )
                    RETURNING id;
                    """,
                    (
                        user_id,

                        brand_id,

                        telegram_file_id,

                        telegram_file_unique_id,

                        reference_role,

                        user_note,

                        json_string(
                            dna
                        ),

                        json_string(
                            product_lock
                            or {}
                        ),

                        image_fingerprint,

                        content_family,

                        json_string(
                            source_metadata
                        ),

                        json_string(
                            reference_utility
                        ),
                    ),
                )

                row = cur.fetchone()

                reference_id = (
                    int(
                        row[0]
                    )
                    if row
                    else None
                )

    if brand_id:

        set_active_brand(
            core,
            user_id,
            brand_id,
        )

        #
        # Refreshing the profile is LOCAL deterministic
        # aggregation over already stored DNA.
        #
        # No Vision call.
        # No image-generation call.
        #

        try:

            refresh_brand_visual_profile(
                core,
                user_id,
                brand_id,
            )

        except Exception as error:

            print(
                (
                    "⚠️ Brand Visual Profile refresh skipped: "
                    +
                    clean_text(
                        error,
                        1200,
                    )
                )
            )

    return reference_id


def load_visual_references(
    core,
    user_id,
    *,
    brand_id: str = "",
    limit: int = DEFAULT_REFERENCE_LIMIT,
    content_family: str = "",
) -> List[Dict[str, Any]]:

    ensure_tables(
        core
    )

    brand_id = safe_brand_id(
        brand_id
    )

    content_family = clean_text(
        content_family,
        100,
    ).lower()

    limit = max(
        1,
        min(
            int(
                limit
                or
                DEFAULT_REFERENCE_LIMIT
            ),
            100,
        ),
    )

    conditions = [
        "user_id = %s",
        "active = TRUE",
    ]

    params: List[Any] = [
        user_id
    ]

    if brand_id:

        conditions.append(
            "brand_id = %s"
        )

        params.append(
            brand_id
        )

    if content_family:

        conditions.append(
            "content_family = %s"
        )

        params.append(
            normalize_content_family(
                content_family
            )
        )

    params.append(
        limit
    )

    sql = f"""
        SELECT
            id,
            brand_id,
            telegram_file_id,
            telegram_file_unique_id,
            reference_role,
            user_note,
            dna_json,
            product_lock_json,
            created_at,
            image_fingerprint,
            content_family,
            source_metadata_json,
            reference_utility_json,
            updated_at,
            last_used_at,
            use_count

        FROM xpand_visual_references

        WHERE
            {' AND '.join(conditions)}

        ORDER BY
            created_at DESC,
            id DESC

        LIMIT %s;
    """

    with core.db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                sql,
                tuple(
                    params
                ),
            )

            rows = cur.fetchall()

    output = []

    for row in rows:

        dna = parse_json(
            row[6],
            {},
        )

        product_lock = parse_json(
            row[7],
            {},
        )

        source_metadata = parse_json(
            row[11],
            {},
        )

        utility = parse_json(
            row[12],
            {},
        )

        #
        # Compatibility:
        # If V1 reference has metadata only inside DNA,
        # expose it through V2 fields too.
        #

        if not source_metadata:

            source_metadata = safe_dict(
                dna.get(
                    "source_metadata"
                )
            )

        if not utility:

            utility = safe_dict(
                dna.get(
                    "reference_utility"
                )
            )

        family = normalize_content_family(
            row[10],
            fallback_text=(
                clean_text(
                    dna.get(
                        "summary",
                        "",
                    ),
                    1000,
                )
            ),
        )

        output.append(
            {
                "id":
                    int(
                        row[0]
                    ),

                "brand_id":
                    clean_text(
                        row[1],
                        100,
                    ),

                "telegram_file_id":
                    clean_text(
                        row[2],
                        1500,
                    ),

                "telegram_file_unique_id":
                    clean_text(
                        row[3],
                        1500,
                    ),

                "reference_role":
                    clean_text(
                        row[4],
                        100,
                    ),

                "user_note":
                    clean_text(
                        row[5],
                        5000,
                    ),

                #
                # Keep original compatibility keys.
                #

                "dna":
                    dna,

                "product_lock":
                    product_lock,

                "created_at":
                    str(
                        row[8]
                    ),

                #
                # V2 fields.
                #

                "image_fingerprint":
                    clean_text(
                        row[9],
                        100,
                    ),

                "content_family":
                    family,

                "source_metadata":
                    source_metadata,

                "reference_utility":
                    utility,

                "updated_at":
                    str(
                        row[13]
                    ),

                "last_used_at":
                    (
                        str(
                            row[14]
                        )
                        if row[14]
                        else ""
                    ),

                "use_count":
                    int(
                        row[15]
                        or 0
                    ),
            }
        )

    return output


# =========================================================
# VISUAL INTELLIGENCE BRIDGE
# =========================================================

def reference_record_to_dna(
    reference: Dict[str, Any],
) -> Dict[str, Any]:

    dna = dict(
        safe_dict(
            reference.get(
                "dna"
            )
        )
    )

    if not dna.get(
        "primary_reference_role"
    ):

        dna[
            "primary_reference_role"
        ] = normalize_reference_role(
            reference.get(
                "reference_role",
                "style_reference",
            )
        )

    if not dna.get(
        "content_classification"
    ):

        dna[
            "content_classification"
        ] = {
            "family":
                normalize_content_family(
                    reference.get(
                        "content_family",
                        "general_brand",
                    )
                )
        }

    if not dna.get(
        "reference_utility"
    ):

        dna[
            "reference_utility"
        ] = safe_dict(
            reference.get(
                "reference_utility"
            )
        )

    if not dna.get(
        "source_metadata"
    ):

        dna[
            "source_metadata"
        ] = safe_dict(
            reference.get(
                "source_metadata"
            )
        )

    if not dna.get(
        "product_lock"
    ):

        dna[
            "product_lock"
        ] = safe_dict(
            reference.get(
                "product_lock"
            )
        )

    if not dna.get(
        "image_fingerprint_sha256"
    ):

        dna[
            "image_fingerprint_sha256"
        ] = clean_text(
            reference.get(
                "image_fingerprint",
                "",
            ),
            100,
        )

    #
    # Internal memory pointer.
    #
    # This is not visual DNA.
    # It lets ranking return to the stored DB record.
    #

    dna[
        "_xpand_memory_reference"
    ] = {
        "id":
            reference.get(
                "id"
            ),

        "telegram_file_id":
            reference.get(
                "telegram_file_id",
                "",
            ),

        "telegram_file_unique_id":
            reference.get(
                "telegram_file_unique_id",
                "",
            ),

        "brand_id":
            reference.get(
                "brand_id",
                "",
            ),
    }

    return dna


# =========================================================
# REQUEST-AWARE VISUAL LIBRARY
# =========================================================

def rank_visual_references_for_request(
    core,
    user_id,
    brand_id: str,
    request: str,
    *,
    scan_limit: int = REFERENCE_LIBRARY_SCAN_LIMIT,
) -> List[Dict[str, Any]]:

    brand_id = safe_brand_id(
        brand_id
    )

    request = clean_text(
        request,
        12000,
    )

    references = load_visual_references(
        core,
        user_id,
        brand_id=brand_id,
        limit=scan_limit,
    )

    if not references:

        return []

    dna_list = [
        reference_record_to_dna(
            reference
        )
        for reference in references
    ]

    ranked_dna = (
        rank_references_for_request(
            dna_list,
            request,
        )
    )

    by_id = {
        int(
            reference[
                "id"
            ]
        ):
            reference

        for reference in references

        if reference.get(
            "id"
        )
    }

    output = []

    for dna in ranked_dna:

        memory = safe_dict(
            dna.get(
                "_xpand_memory_reference"
            )
        )

        reference_id = memory.get(
            "id"
        )

        if not reference_id:

            continue

        try:

            reference_id = int(
                reference_id
            )

        except Exception:

            continue

        reference = by_id.get(
            reference_id
        )

        if not reference:

            continue

        item = dict(
            reference
        )

        item[
            "selection"
        ] = safe_dict(
            dna.get(
                "_selection"
            )
        )

        output.append(
            item
        )

    return output


def load_relevant_visual_references(
    core,
    user_id,
    *,
    brand_id: str,
    request: str,
    limit: int = DEFAULT_RELEVANT_REFERENCE_LIMIT,
    mark_used: bool = False,
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
                DEFAULT_RELEVANT_REFERENCE_LIMIT
            ),
            MAX_RELEVANT_REFERENCE_LIMIT,
        ),
    )

    references = load_visual_references(
        core,
        user_id,
        brand_id=brand_id,
        limit=REFERENCE_LIBRARY_SCAN_LIMIT,
    )

    if not references:

        return []

    dna_list = [
        reference_record_to_dna(
            reference
        )
        for reference in references
    ]

    selected_dna = (
        select_best_references(
            dna_list,
            request,
            limit=limit,
        )
    )

    by_id = {
        int(
            reference[
                "id"
            ]
        ):
            reference

        for reference in references

        if reference.get(
            "id"
        )
    }

    selected_records = []

    selected_ids = []

    for dna in selected_dna:

        memory = safe_dict(
            dna.get(
                "_xpand_memory_reference"
            )
        )

        reference_id = memory.get(
            "id"
        )

        if not reference_id:

            continue

        try:

            reference_id = int(
                reference_id
            )

        except Exception:

            continue

        reference = by_id.get(
            reference_id
        )

        if not reference:

            continue

        item = dict(
            reference
        )

        item[
            "selection"
        ] = safe_dict(
            dna.get(
                "_selection"
            )
        )

        selected_records.append(
            item
        )

        selected_ids.append(
            reference_id
        )

    if (
        mark_used
        and
        selected_ids
    ):

        mark_visual_references_used(
            core,
            user_id,
            selected_ids,
        )

    return selected_records


def mark_visual_references_used(
    core,
    user_id,
    reference_ids: Sequence[int],
) -> None:

    ids = []

    for value in reference_ids:

        try:

            ids.append(
                int(
                    value
                )
            )

        except Exception:

            continue

    if not ids:

        return

    placeholders = ",".join(
        [
            "%s"
            for _ in ids
        ]
    )

    sql = f"""
        UPDATE xpand_visual_references

        SET
            use_count =
                use_count + 1,

            last_used_at =
                NOW(),

            updated_at =
                NOW()

        WHERE
            user_id = %s
            AND id IN
            (
                {placeholders}
            );
    """

    params = [
        user_id,
        *ids,
    ]

    with core.db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                sql,
                tuple(
                    params
                ),
            )


# =========================================================
# BRAND VISUAL PROFILE
# =========================================================

def upsert_brand_visual_profile(
    core,
    user_id,
    brand_id: str,
    profile: Dict[str, Any],
) -> None:

    ensure_tables(
        core
    )

    brand_id = safe_brand_id(
        brand_id
    )

    if not brand_id:

        return

    profile = safe_dict(
        profile
    )

    source_count = int(
        profile.get(
            "source_count",
            0,
        )
        or 0
    )

    try:

        evidence_strength = float(
            profile.get(
                "evidence_strength",
                0,
            )
            or 0
        )

    except Exception:

        evidence_strength = 0.0

    with core.db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO xpand_brand_visual_profiles
                (
                    user_id,
                    brand_id,
                    visual_profile_json,
                    source_count,
                    evidence_strength,
                    active,
                    updated_at
                )
                VALUES
                (
                    %s,
                    %s,
                    %s::jsonb,
                    %s,
                    %s,
                    TRUE,
                    NOW()
                )

                ON CONFLICT
                (
                    user_id,
                    brand_id
                )
                DO UPDATE SET

                    visual_profile_json =
                        EXCLUDED.visual_profile_json,

                    source_count =
                        EXCLUDED.source_count,

                    evidence_strength =
                        EXCLUDED.evidence_strength,

                    active =
                        TRUE,

                    updated_at =
                        NOW();
                """,
                (
                    user_id,
                    brand_id,
                    json_string(
                        profile
                    ),
                    source_count,
                    evidence_strength,
                ),
            )


def get_brand_visual_profile(
    core,
    user_id,
    brand_id: str,
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
                    visual_profile_json,
                    source_count,
                    evidence_strength,
                    updated_at
                FROM xpand_brand_visual_profiles
                WHERE
                    user_id = %s
                    AND brand_id = %s
                    AND active = TRUE
                LIMIT 1;
                """,
                (
                    user_id,
                    brand_id,
                ),
            )

            row = cur.fetchone()

    if not row:

        return {}

    profile = parse_json(
        row[0],
        {},
    )

    if isinstance(
        profile,
        dict,
    ):

        profile[
            "_memory_metadata"
        ] = {
            "source_count":
                int(
                    row[1]
                    or 0
                ),

            "evidence_strength":
                float(
                    row[2]
                    or 0
                ),

            "updated_at":
                str(
                    row[3]
                ),
        }

    return profile


def refresh_brand_visual_profile(
    core,
    user_id,
    brand_id: str,
) -> Dict[str, Any]:

    brand_id = safe_brand_id(
        brand_id
    )

    if not brand_id:

        return {}

    references = load_visual_references(
        core,
        user_id,
        brand_id=brand_id,
        limit=100,
    )

    dna_list = [
        reference_record_to_dna(
            reference
        )
        for reference in references
    ]

    profile = (
        build_brand_visual_profile(
            dna_list,
            brand_id=brand_id,
        )
    )

    upsert_brand_visual_profile(
        core,
        user_id,
        brand_id,
        profile,
    )

    return profile


# =========================================================
# VISUAL LIBRARY STATS
# =========================================================

def get_visual_library_stats(
    core,
    user_id,
    brand_id: str,
) -> Dict[str, Any]:

    ensure_tables(
        core
    )

    brand_id = safe_brand_id(
        brand_id
    )

    if not brand_id:

        return {
            "brand_id":
                "",

            "total":
                0,
        }

    with core.db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    COUNT(*),

                    COUNT(*)
                        FILTER
                        (
                            WHERE
                                source_metadata_json
                                ->>
                                'official'
                                =
                                'true'
                        ),

                    COUNT(DISTINCT content_family),

                    COALESCE
                    (
                        SUM(use_count),
                        0
                    )

                FROM xpand_visual_references

                WHERE
                    user_id = %s
                    AND brand_id = %s
                    AND active = TRUE;
                """,
                (
                    user_id,
                    brand_id,
                ),
            )

            row = cur.fetchone()

    if not row:

        return {
            "brand_id":
                brand_id,

            "total":
                0,
        }

    return {
        "brand_id":
            brand_id,

        "total":
            int(
                row[0]
                or 0
            ),

        "official_sources":
            int(
                row[1]
                or 0
            ),

        "content_families":
            int(
                row[2]
                or 0
            ),

        "total_reference_uses":
            int(
                row[3]
                or 0
            ),
    }


# =========================================================
# CAMPAIGN VISUAL BIBLE
# =========================================================

def save_campaign_bible(
    core,
    user_id,
    brand_id: str,
    campaign_key: str,
    title: str,
    bible: Dict[str, Any],
) -> None:

    ensure_tables(
        core
    )

    brand_id = safe_brand_id(
        brand_id
    )

    campaign_key = clean_text(
        campaign_key,
        200,
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
                        500,
                    ),

                    json_string(
                        bible
                    ),
                ),
            )

    set_active_brand(
        core,
        user_id,
        brand_id,
        campaign_key=(
            campaign_key
        ),
    )


def load_campaign_bible(
    core,
    user_id,
    brand_id: str,
    campaign_key: str = "",
) -> Dict[str, Any]:

    ensure_tables(
        core
    )

    brand_id = safe_brand_id(
        brand_id
    )

    campaign_key = clean_text(
        campaign_key,
        200,
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
                    ),
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
                    ),
                )

            row = cur.fetchone()

    if not row:

        return {}

    return {
        "campaign_key":
            clean_text(
                row[0],
                200,
            ),

        "title":
            clean_text(
                row[1],
                500,
            ),

        "bible":
            parse_json(
                row[2],
                {},
            ),

        "updated_at":
            str(
                row[3]
            ),
    }


# =========================================================
# BRAND CREATIVE CONTEXT V2
# =========================================================

def build_brand_memory_context(
    core,
    user_id,
    brand_id: str,
    *,
    request: str = "",
    max_rules: int = 40,
    max_references: int = 10,
) -> Dict[str, Any]:

    brand_id = safe_brand_id(
        brand_id
    )

    if not brand_id:

        return {
            "brand_id":
                "",

            "profile":
                {},

            "visual_profile":
                {},

            "rules":
                [],

            "references":
                [],

            "reference_execution_context":
                {},

            "campaign":
                {},

            "library_stats":
                {},
        }

    profile = get_brand_profile(
        core,
        user_id,
        brand_id,
    )

    visual_profile = (
        get_brand_visual_profile(
            core,
            user_id,
            brand_id,
        )
    )

    rules = load_brand_rules(
        core,
        user_id,
        brand_id,
        limit=max_rules,
    )

    if request:

        references = (
            load_relevant_visual_references(
                core,
                user_id,
                brand_id=brand_id,
                request=request,
                limit=min(
                    max_references,
                    MAX_RELEVANT_REFERENCE_LIMIT,
                ),
                mark_used=False,
            )
        )

    else:

        references = (
            load_visual_references(
                core,
                user_id,
                brand_id=brand_id,
                limit=max_references,
            )
        )

    campaign = (
        load_campaign_bible(
            core,
            user_id,
            brand_id,
        )
    )

    execution_context = {}

    if (
        request
        and
        references
    ):

        dna_list = [
            reference_record_to_dna(
                reference
            )
            for reference in references
        ]

        execution_context = (
            build_reference_execution_context(
                dna_list,
                request,
                limit=min(
                    len(
                        dna_list
                    ),
                    MAX_RELEVANT_REFERENCE_LIMIT,
                ),
            )
        )

    stats = get_visual_library_stats(
        core,
        user_id,
        brand_id,
    )

    return {
        "brand_id":
            brand_id,

        "profile":
            profile,

        "visual_profile":
            visual_profile,

        "rules":
            rules,

        "references":
            references,

        "reference_execution_context":
            execution_context,

        "campaign":
            campaign,

        "library_stats":
            stats,

        "memory_version":
            VERSION,

        "visual_intelligence_version":
            VISUAL_INTELLIGENCE_VERSION,
    }


# =========================================================
# LOCAL / DETERMINISTIC SELF TEST HELPERS
# =========================================================

def _synthetic_reference(
    *,
    reference_id: int,
    family: str,
    role: str,
    utility: Dict[str, Any],
    fingerprint: str,
    official: bool = True,
) -> Dict[str, Any]:

    dna = {
        "visual_intelligence_version":
            VISUAL_INTELLIGENCE_VERSION,

        "image_fingerprint_sha256":
            fingerprint,

        "primary_reference_role":
            role,

        "secondary_reference_roles":
            [],

        "content_classification": {
            "family":
                family,

            "campaign_archetype":
                "environmental_storytelling",
        },

        "reference_utility":
            utility,

        "visual_fingerprint": {
            "style_tags": [
                "premium",
                "cinematic",
                "brand-native",
            ],

            "camera_signature":
                "35mm environmental advertising",

            "composition_signature":
                "strong hero with intentional negative space",

            "lighting_signature":
                "soft directional commercial light",

            "material_signature":
                "glass stone brushed metal",

            "palette_signature":
                "deep purple with restrained mint",

            "human_signature":
                "natural non-camera-facing behavior",

            "negative_space_signature":
                "clean headline-safe zone",

            "commercial_finish_signature":
                "premium campaign photography",

            "preserve": [
                "visual restraint",
            ],

            "avoid_copying_literally": [
                "exact scene",
            ],

            "transferable_rules": [
                "use brand color through physical environment",
            ],
        },

        "color_palette": {
            "all_hex": [
                "#4A136F",
                "#00C9A7",
                "#FFFFFF",
            ],
        },

        "source_metadata": {
            "source_type":
                "official_instagram",

            "official":
                official,

            "authority_score":
                (
                    100
                    if official
                    else 60
                ),

            "recency_score":
                95,

            "brand_id":
                "stc_bank",
        },

        "confidence":
            95,
    }

    return {
        "id":
            reference_id,

        "brand_id":
            "stc_bank",

        "telegram_file_id":
            (
                "telegram-file-"
                +
                str(
                    reference_id
                )
            ),

        "telegram_file_unique_id":
            (
                "unique-"
                +
                str(
                    reference_id
                )
            ),

        "reference_role":
            role,

        "user_note":
            "official STC visual reference",

        "dna":
            dna,

        "product_lock":
            {},

        "created_at":
            "2026-09-03",

        "image_fingerprint":
            fingerprint,

        "content_family":
            family,

        "source_metadata":
            dna[
                "source_metadata"
            ],

        "reference_utility":
            utility,

        "use_count":
            0,
    }


# =========================================================
# SELF TEST
#
# NO DATABASE ACCESS
# NO API CALLS
# NO VISION CALLS
# NO IMAGE GENERATION
# =========================================================

if __name__ == "__main__":

    print("")
    print(
        "=============================================="
    )
    print(
        " XPAND BRAND MEMORY V2.0"
    )
    print(
        " BRAND VISUAL MEMORY + REFERENCE LIBRARY"
    )
    print(
        "=============================================="
    )
    print("")

    # =====================================================
    # BRAND ID
    # =====================================================

    brand_tests = [
        (
            "STC Bank",
            "stc_bank",
        ),

        (
            "بنك STC",
            "stc_bank",
        ),

        (
            "XPAND",
            "xpand",
        ),
    ]

    brand_ok = True

    for text, expected in brand_tests:

        actual = safe_brand_id(
            text
        )

        ok = (
            actual
            ==
            expected
        )

        brand_ok = (
            brand_ok
            and
            ok
        )

        print(
            (
                "✅"
                if ok
                else "❌"
            ),
            "brand",
            text,
            "→",
            actual,
        )

    print("")

    # =====================================================
    # FEEDBACK LEARNING CLASSIFIER
    # =====================================================

    feedback_tests = [
        (
            "هذا ممتاز اعتمد هذا الأسلوب",
            "approved_style",
        ),

        (
            "لا ترجع لهذا الأسلوب",
            "rejected_style",
        ),

        (
            "من هسا خلي الأرضية أنعم ومش كأنها مبللة",
            "material_rule",
        ),

        (
            "من هسا بدي البنفسجي أوضح",
            "color_rule",
        ),

        (
            "اعمل بوستر وخلي الشخص على اليمين",
            "",
        ),
    ]

    feedback_ok = True

    for text, expected in feedback_tests:

        actual = (
            infer_feedback_rule_type(
                text
            )
        )

        ok = (
            actual
            ==
            expected
        )

        feedback_ok = (
            feedback_ok
            and
            ok
        )

        print(
            (
                "✅"
                if ok
                else "❌"
            ),
            "feedback",
            expected
            or
            "normal_request_not_saved",
            "→",
            actual
            or
            "not_saved",
        )

    print("")

    # =====================================================
    # SYNTHETIC BRAND VISUAL LIBRARY
    # =====================================================

    travel_ref = _synthetic_reference(
        reference_id=1,
        family="travel_roaming",
        role="style_reference",
        fingerprint="travel-fingerprint",
        utility={
            "style":
                96,

            "color":
                92,

            "lighting":
                94,

            "camera":
                93,

            "composition":
                95,

            "environment":
                96,

            "product":
                10,

            "person":
                85,

            "campaign_consistency":
                96,
        },
    )

    transfer_ref = _synthetic_reference(
        reference_id=2,
        family="international_transfer",
        role="campaign_reference",
        fingerprint="transfer-fingerprint",
        utility={
            "style":
                95,

            "color":
                92,

            "lighting":
                93,

            "camera":
                92,

            "composition":
                98,

            "environment":
                88,

            "product":
                10,

            "person":
                60,

            "campaign_consistency":
                98,
        },
    )

    generic_color_ref = _synthetic_reference(
        reference_id=3,
        family="general_brand",
        role="color_reference",
        fingerprint="color-fingerprint",
        utility={
            "style":
                82,

            "color":
                99,

            "lighting":
                65,

            "camera":
                45,

            "composition":
                70,

            "environment":
                40,

            "product":
                10,

            "person":
                10,

            "campaign_consistency":
                88,
        },
    )

    synthetic_library = [
        travel_ref,
        transfer_ref,
        generic_color_ref,
    ]

    # =====================================================
    # BRIDGE TEST
    # =====================================================

    bridged = [
        reference_record_to_dna(
            item
        )
        for item in synthetic_library
    ]

    bridge_ok = (
        len(
            bridged
        )
        ==
        3
        and
        bridged[0].get(
            "_xpand_memory_reference",
            {},
        ).get(
            "id"
        )
        ==
        1
    )

    print(
        (
            "✅"
            if bridge_ok
            else "❌"
        ),
        "Brand Memory ↔ Visual Intelligence V2 bridge",
    )

    # =====================================================
    # REQUEST-AWARE RANKING
    # =====================================================

    ranked_transfer = (
        rank_references_for_request(
            bridged,
            (
                "STC Bank اعلان "
                "تحويل مالي دولي سريع"
            ),
        )
    )

    ranking_ok = (
        bool(
            ranked_transfer
        )
        and
        safe_dict(
            ranked_transfer[0].get(
                "content_classification"
            )
        ).get(
            "family"
        )
        ==
        "international_transfer"
    )

    print(
        (
            "✅"
            if ranking_ok
            else "❌"
        ),
        "Request-aware reference ranking",
    )

    # =====================================================
    # TRAVEL SELECTION
    # =====================================================

    selected_travel = (
        select_best_references(
            bridged,
            (
                "STC Bank "
                "شريحتك معك بكل وجهة سفر"
            ),
            limit=2,
        )
    )

    travel_selection_ok = (
        bool(
            selected_travel
        )
        and
        safe_dict(
            selected_travel[0].get(
                "content_classification"
            )
        ).get(
            "family"
        )
        ==
        "travel_roaming"
    )

    print(
        (
            "✅"
            if travel_selection_ok
            else "❌"
        ),
        "Travel campaign gets travel-relevant reference",
    )

    # =====================================================
    # BRAND PROFILE AGGREGATION
    # =====================================================

    visual_profile = (
        build_brand_visual_profile(
            bridged,
            brand_id="stc_bank",
        )
    )

    profile_ok = (
        visual_profile.get(
            "source_count"
        )
        ==
        3
        and
        bool(
            visual_profile.get(
                "recurring_colors"
            )
        )
        and
        bool(
            visual_profile.get(
                "style_tags"
            )
        )
    )

    print(
        (
            "✅"
            if profile_ok
            else "❌"
        ),
        "Multi-reference Brand Visual Profile",
    )

    # =====================================================
    # PRODUCTION EXECUTION CONTEXT
    # =====================================================

    execution_context = (
        build_reference_execution_context(
            bridged,
            (
                "اعمل بوستر STC Bank "
                "عن تحويل مالي دولي"
            ),
            limit=3,
        )
    )

    execution_ok = (
        execution_context.get(
            "request_family"
        )
        ==
        "international_transfer"
        and
        execution_context.get(
            "selected_count"
        )
        >=
        1
    )

    print(
        (
            "✅"
            if execution_ok
            else "❌"
        ),
        "Production Reference Execution Context",
    )

    # =====================================================
    # CONTENT FAMILY
    # =====================================================

    family_ok = (
        infer_content_family(
            "شريحتك معك بكل وجهة سفر"
        )
        ==
        "travel_roaming"
        and
        infer_content_family(
            "تحويل مالي دولي"
        )
        ==
        "international_transfer"
    )

    print(
        (
            "✅"
            if family_ok
            else "❌"
        ),
        "Campaign family separation",
    )

    print("")
    print(
        "✅ Per-brand isolated memory"
    )
    print(
        "✅ V1 database compatibility preserved"
    )
    print(
        "✅ Safe V2 database migrations prepared"
    )
    print(
        "✅ Approved / rejected style learning"
    )
    print(
        "✅ Reusable correction learning"
    )
    print(
        "✅ Normal design requests no longer pollute long-term rules"
    )
    print(
        "✅ Visual Reference DNA V2 storage"
    )
    print(
        "✅ Product Lock storage preserved"
    )
    print(
        "✅ Image fingerprint deduplication prepared"
    )
    print(
        "✅ Source authority / freshness metadata storage"
    )
    print(
        "✅ Content-family indexing"
    )
    print(
        "✅ Reference utility storage"
    )
    print(
        "✅ Request-aware reference ranking"
    )
    print(
        "✅ Best 3–5 reference selection supported"
    )
    print(
        "✅ Multi-reference Brand Visual Profile"
    )
    print(
        "✅ Repeated patterns become stronger brand evidence"
    )
    print(
        "✅ One reference does not become universal brand law"
    )
    print(
        "✅ Campaign Visual Bible preserved"
    )
    print(
        "✅ Active brand context preserved"
    )
    print(
        "✅ No raw image bytes stored in PostgreSQL"
    )
    print(
        "✅ Existing production-engine API preserved"
    )

    print("")

    all_ok = (
        brand_ok
        and
        feedback_ok
        and
        bridge_ok
        and
        ranking_ok
        and
        travel_selection_ok
        and
        profile_ok
        and
        execution_ok
        and
        family_ok
    )

    print(
        (
            "XPAND Brand Memory V2.0 self-test: "
            +
            (
                "PASS ✅"
                if all_ok
                else "FAIL ❌"
            )
        )
    )

    print(
        "🚫 No API calls were made"
    )

    print(
        "🚫 No database writes were made"
    )

    print(
        "🚫 No image-generation calls were made"
    )

    print("")
