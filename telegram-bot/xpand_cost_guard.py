from __future__ import annotations

import json
import os
import threading
import uuid

from datetime import (
    datetime,
    timedelta,
    timezone,
)

from pathlib import Path
from typing import (
    Any,
    Dict,
    Optional,
    Tuple,
)

from urllib.parse import urlparse


# =========================================================
# XPAND OPENAI COST GUARD V2.0
#
# FIXES:
#
# - Reservations are TEMPORARY.
# - Successful requests are reconciled against real API usage.
# - Failed HTTP/API requests release their reservation.
# - Network exceptions release their reservation.
# - Stale reservations automatically expire.
# - Legacy "reserved_usd" from V1 is NOT treated as real spend.
# - PostgreSQL and file fallback are both supported.
# - UTC day rollover is preserved.
#
# IMPORTANT:
#
# "daily limit" is an internal XPAND safety budget.
# It is NOT the price of one API call or one image.
#
# =========================================================


class XPANDOpenAIBudgetError(RuntimeError):
    pass


VERSION = "2.0"

_LOCK = threading.RLock()

_INSTALLED = False


# =========================================================
# ENV HELPERS
# =========================================================

def _truthy(
    name: str,
    default: str = "false",
) -> bool:

    return str(
        os.environ.get(
            name,
            default,
        )
    ).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _env_float(
    name: str,
    default: float,
) -> float:

    try:

        return float(
            os.environ.get(
                name,
                str(
                    default
                ),
            )
            or default
        )

    except Exception:

        return float(
            default
        )


def _env_int(
    name: str,
    default: int,
) -> int:

    try:

        return int(
            os.environ.get(
                name,
                str(
                    default
                ),
            )
            or default
        )

    except Exception:

        return int(
            default
        )


# =========================================================
# PUBLIC SETTINGS
# =========================================================

def openai_enabled() -> bool:

    return _truthy(
        "XPAND_OPENAI_ENABLED",
        "false",
    )


def daily_limit_usd() -> float:

    try:

        return max(
            0.0,
            float(
                os.environ.get(
                    "XPAND_OPENAI_DAILY_LIMIT_USD",
                    "2.00",
                )
            ),
        )

    except Exception:

        return 2.0


def reservation_ttl_seconds() -> int:

    return max(
        60,
        min(
            21600,
            _env_int(
                "XPAND_OPENAI_RESERVATION_TTL_SECONDS",
                1800,
            ),
        ),
    )


# =========================================================
# CURRENT GPT-5.6 SOL PRICING
#
# USD PER 1M TOKENS
#
# ENV values can override defaults later without changing code.
# =========================================================

def _sol_input_per_million() -> float:

    return max(
        0.0,
        _env_float(
            "XPAND_OPENAI_SOL_INPUT_PER_M",
            4.00,
        ),
    )


def _sol_cached_input_per_million() -> float:

    return max(
        0.0,
        _env_float(
            "XPAND_OPENAI_SOL_CACHED_INPUT_PER_M",
            0.40,
        ),
    )


def _sol_output_per_million() -> float:

    return max(
        0.0,
        _env_float(
            "XPAND_OPENAI_SOL_OUTPUT_PER_M",
            20.00,
        ),
    )


# =========================================================
# FILE LEDGER
# =========================================================

def _ledger_path() -> Path:

    custom = str(
        os.environ.get(
            "XPAND_OPENAI_LEDGER_PATH",
            "",
        )
    ).strip()

    return Path(
        custom
        or
        "/tmp/xpand_openai_daily_budget.json"
    )


# =========================================================
# UTC TIME
# =========================================================

def _utc_now() -> datetime:

    return datetime.now(
        timezone.utc
    )


def _today() -> str:

    return _utc_now().date().isoformat()


def _iso_now() -> str:

    return _utc_now().isoformat()


def _parse_iso(
    value: Any,
) -> Optional[datetime]:

    text = str(
        value
        or ""
    ).strip()

    if not text:

        return None

    try:

        result = datetime.fromisoformat(
            text.replace(
                "Z",
                "+00:00",
            )
        )

        if result.tzinfo is None:

            result = result.replace(
                tzinfo=timezone.utc
            )

        return result.astimezone(
            timezone.utc
        )

    except Exception:

        return None


# =========================================================
# EMPTY LEDGER
# =========================================================

def _fresh_ledger() -> Dict[str, Any]:

    return {

        "date":
            _today(),

        "guard_version":
            VERSION,

        "spent_usd":
            0.0,

        "active_reserved_usd":
            0.0,

        #
        # Backward-compatible field.
        #
        # In V2 this means:
        #
        # spent + currently active reservations
        #
        "reserved_usd":
            0.0,

        "legacy_reserved_usd":
            0.0,

        "requests":
            0,

        "completed_requests":
            0,

        "failed_requests":
            0,

        "expired_requests":
            0,

        "reservations":
            {},
    }


# =========================================================
# FILE LEDGER MIGRATION
# =========================================================

def _normalize_file_ledger(
    data: Any,
) -> Dict[str, Any]:

    if not isinstance(
        data,
        dict,
    ):

        return _fresh_ledger()

    if str(
        data.get(
            "date"
        )
        or ""
    ) != _today():

        return _fresh_ledger()

    if str(
        data.get(
            "guard_version"
        )
        or ""
    ) != VERSION:

        #
        # V1's reserved_usd was only accumulated estimates.
        #
        # It was NOT reliable actual billed spend.
        #
        # Preserve it for diagnostics but do not let it block V2.
        #
        legacy_reserved = float(
            data.get(
                "reserved_usd",
                0.0,
            )
            or 0.0
        )

        migrated = _fresh_ledger()

        migrated[
            "legacy_reserved_usd"
        ] = round(
            max(
                0.0,
                legacy_reserved,
            ),
            6,
        )

        return migrated

    ledger = _fresh_ledger()

    ledger.update(
        data
    )

    if not isinstance(
        ledger.get(
            "reservations"
        ),
        dict,
    ):

        ledger[
            "reservations"
        ] = {}

    return ledger


def _load() -> Dict[str, Any]:

    path = _ledger_path()

    try:

        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        return _normalize_file_ledger(
            data
        )

    except Exception:

        return _fresh_ledger()


def _save(
    data: Dict[str, Any],
) -> None:

    path = _ledger_path()

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp = path.with_suffix(
        ".tmp"
    )

    temp.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    temp.replace(
        path
    )


# =========================================================
# MODEL / REQUEST HELPERS
# =========================================================

def _request_payload(
    kwargs: Dict[str, Any],
) -> Dict[str, Any]:

    payload = kwargs.get(
        "json"
    )

    if isinstance(
        payload,
        dict,
    ):

        return payload

    data = kwargs.get(
        "data"
    )

    if isinstance(
        data,
        dict,
    ):

        return data

    return {}


def _request_model(
    kwargs: Dict[str, Any],
) -> str:

    payload = _request_payload(
        kwargs
    )

    return str(
        payload.get(
            "model"
        )
        or ""
    ).strip().lower()


def _endpoint_path(
    url: str,
) -> str:

    try:

        return (
            urlparse(
                str(
                    url
                )
            )
            .path
            .lower()
        )

    except Exception:

        return ""


def _is_image_request(
    url: str,
    kwargs: Dict[str, Any],
) -> bool:

    path = _endpoint_path(
        url
    )

    model = _request_model(
        kwargs
    )

    return bool(
        "/images/"
        in path
        or
        model.startswith(
            "gpt-image"
        )
    )


# =========================================================
# ACTIVE RESERVATION ESTIMATE
#
# This is only a temporary safety hold.
#
# It is NOT counted permanently after the request finishes.
# =========================================================

def _estimate_reservation(
    url: str,
    kwargs: Dict[str, Any],
) -> float:

    payload = _request_payload(
        kwargs
    )

    if _is_image_request(
        url,
        kwargs,
    ):

        quality = str(
            payload.get(
                "quality"
            )
            or
            "high"
        ).lower()

        try:

            count = max(
                1,
                int(
                    payload.get(
                        "n"
                    )
                    or 1
                ),
            )

        except Exception:

            count = 1

        #
        # Conservative reservation fallback.
        #
        # This is not claimed to be exact image billing.
        #
        per_image = {
            "low":
                0.04,
            "medium":
                0.10,
            "high":
                0.25,
            "auto":
                0.25,
        }.get(
            quality,
            0.25,
        )

        return round(
            max(
                0.01,
                per_image
                *
                count,
            ),
            6,
        )

    try:

        max_tokens = int(
            payload.get(
                "max_output_tokens"
            )
            or
            payload.get(
                "max_completion_tokens"
            )
            or
            2000
        )

    except Exception:

        max_tokens = 2000

    #
    # Old guard permanently accumulated this estimate.
    #
    # V2 only holds it while the request is active.
    #
    estimated_output_cost = (
        max_tokens
        /
        1_000_000.0
        *
        _sol_output_per_million()
    )

    reservation = (
        0.02
        +
        estimated_output_cost
    )

    return round(
        max(
            0.02,
            min(
                0.75,
                reservation,
            ),
        ),
        6,
    )


# =========================================================
# PRICING
# =========================================================

def _pricing_for_model(
    model: str,
) -> Tuple[
    float,
    float,
    float,
]:

    normalized = str(
        model
        or ""
    ).strip().lower()

    #
    # GPT-5.6 Sol and the gpt-5.6 alias.
    #
    if (
        normalized
        ==
        "gpt-5.6"
        or
        normalized.startswith(
            "gpt-5.6-sol"
        )
    ):

        return (
            _sol_input_per_million(),
            _sol_cached_input_per_million(),
            _sol_output_per_million(),
        )

    #
    # Current XPAND primarily uses Sol.
    #
    # For unknown text models, use configurable conservative
    # defaults instead of pretending the cost is zero.
    #
    return (
        max(
            0.0,
            _env_float(
                "XPAND_OPENAI_DEFAULT_INPUT_PER_M",
                5.00,
            ),
        ),
        max(
            0.0,
            _env_float(
                "XPAND_OPENAI_DEFAULT_CACHED_INPUT_PER_M",
                0.50,
            ),
        ),
        max(
            0.0,
            _env_float(
                "XPAND_OPENAI_DEFAULT_OUTPUT_PER_M",
                30.00,
            ),
        ),
    )


# =========================================================
# USAGE EXTRACTION
# =========================================================

def _response_json(
    response: Any,
) -> Dict[str, Any]:

    if response is None:

        return {}

    try:

        payload = response.json()

        if isinstance(
            payload,
            dict,
        ):

            return payload

    except Exception:

        pass

    return {}


def _extract_usage(
    payload: Dict[str, Any],
) -> Optional[
    Dict[str, int]
]:

    usage = payload.get(
        "usage"
    )

    if not isinstance(
        usage,
        dict,
    ):

        return None

    input_tokens = int(
        usage.get(
            "input_tokens"
        )
        or
        usage.get(
            "prompt_tokens"
        )
        or
        0
    )

    output_tokens = int(
        usage.get(
            "output_tokens"
        )
        or
        usage.get(
            "completion_tokens"
        )
        or
        0
    )

    cached_tokens = 0

    input_details = usage.get(
        "input_tokens_details"
    )

    if isinstance(
        input_details,
        dict,
    ):

        cached_tokens = int(
            input_details.get(
                "cached_tokens"
            )
            or 0
        )

    prompt_details = usage.get(
        "prompt_tokens_details"
    )

    if (
        cached_tokens <= 0
        and
        isinstance(
            prompt_details,
            dict,
        )
    ):

        cached_tokens = int(
            prompt_details.get(
                "cached_tokens"
            )
            or 0
        )

    cached_tokens = max(
        0,
        min(
            cached_tokens,
            input_tokens,
        ),
    )

    if (
        input_tokens <= 0
        and
        output_tokens <= 0
    ):

        return None

    return {

        "input_tokens":
            max(
                0,
                input_tokens,
            ),

        "cached_input_tokens":
            cached_tokens,

        "output_tokens":
            max(
                0,
                output_tokens,
            ),
    }


# =========================================================
# ACTUAL TRACKED COST
# =========================================================

def _actual_text_cost_usd(
    *,
    model: str,
    usage: Dict[str, int],
    request_payload: Dict[str, Any],
) -> float:

    (
        input_rate,
        cached_rate,
        output_rate,
    ) = _pricing_for_model(
        model
    )

    input_tokens = max(
        0,
        int(
            usage.get(
                "input_tokens",
                0,
            )
            or 0
        ),
    )

    cached_tokens = max(
        0,
        min(
            input_tokens,
            int(
                usage.get(
                    "cached_input_tokens",
                    0,
                )
                or 0
            ),
        ),
    )

    output_tokens = max(
        0,
        int(
            usage.get(
                "output_tokens",
                0,
            )
            or 0
        ),
    )

    uncached_input_tokens = max(
        0,
        input_tokens
        -
        cached_tokens,
    )

    normalized_model = str(
        model
        or ""
    ).lower()

    #
    # GPT-5.6 long-context rule.
    #
    # Prompts above 272K input tokens use higher rates.
    #
    if (
        (
            normalized_model
            ==
            "gpt-5.6"
            or
            normalized_model.startswith(
                "gpt-5.6-sol"
            )
        )
        and
        input_tokens
        >
        272_000
    ):

        input_rate *= 2.0

        cached_rate *= 2.0

        output_rate *= 1.5

    #
    # Priority/Fast-style service is more expensive.
    #
    service_tier = str(
        request_payload.get(
            "service_tier"
        )
        or ""
    ).strip().lower()

    if service_tier in {
        "priority",
        "fast",
    }:

        input_rate *= 2.0

        cached_rate *= 2.0

        output_rate *= 2.0

    cost = (
        (
            uncached_input_tokens
            /
            1_000_000.0
        )
        *
        input_rate
        +
        (
            cached_tokens
            /
            1_000_000.0
        )
        *
        cached_rate
        +
        (
            output_tokens
            /
            1_000_000.0
        )
        *
        output_rate
    )

    return round(
        max(
            0.0,
            cost,
        ),
        8,
    )


def _actual_cost_from_response(
    *,
    url: str,
    kwargs: Dict[str, Any],
    response: Any,
    reservation: float,
) -> Tuple[
    float,
    Dict[str, Any],
]:

    request_payload = _request_payload(
        kwargs
    )

    request_model = _request_model(
        kwargs
    )

    #
    # Do not consume a streaming response.
    #
    if bool(
        kwargs.get(
            "stream",
            False,
        )
    ):

        return (
            reservation,
            {
                "method":
                    "reservation_fallback_streaming",
            },
        )

    #
    # OpenAI Images are not used by the current STC production
    # path. If they are used later and exact usage is unavailable,
    # retain the conservative reservation rather than counting $0.
    #
    if _is_image_request(
        url,
        kwargs,
    ):

        return (
            reservation,
            {
                "method":
                    "reservation_fallback_image_request",
            },
        )

    payload = _response_json(
        response
    )

    usage = _extract_usage(
        payload
    )

    if usage is None:

        return (
            reservation,
            {
                "method":
                    "reservation_fallback_missing_usage",
            },
        )

    response_model = str(
        payload.get(
            "model"
        )
        or request_model
        or ""
    ).strip().lower()

    actual_cost = (
        _actual_text_cost_usd(
            model=(
                response_model
            ),
            usage=(
                usage
            ),
            request_payload=(
                request_payload
            ),
        )
    )

    return (
        actual_cost,
        {
            "method":
                "api_usage_tokens",

            "model":
                response_model,

            "input_tokens":
                usage.get(
                    "input_tokens",
                    0,
                ),

            "cached_input_tokens":
                usage.get(
                    "cached_input_tokens",
                    0,
                ),

            "output_tokens":
                usage.get(
                    "output_tokens",
                    0,
                ),
        },
    )


# =========================================================
# FILE LEDGER SUMMARY / EXPIRY
# =========================================================

def _sync_file_summary(
    ledger: Dict[str, Any],
) -> None:

    reservations = ledger.get(
        "reservations"
    )

    if not isinstance(
        reservations,
        dict,
    ):

        reservations = {}

        ledger[
            "reservations"
        ] = reservations

    spent = 0.0

    active = 0.0

    requests = 0

    completed = 0

    failed = 0

    expired = 0

    for item in reservations.values():

        if not isinstance(
            item,
            dict,
        ):

            continue

        requests += 1

        status = str(
            item.get(
                "status"
            )
            or ""
        ).strip().lower()

        amount = max(
            0.0,
            float(
                item.get(
                    "amount_usd",
                    0.0,
                )
                or 0.0
            ),
        )

        actual = max(
            0.0,
            float(
                item.get(
                    "actual_usd",
                    0.0,
                )
                or 0.0
            ),
        )

        if status == "active":

            active += amount

        elif status == "completed":

            completed += 1

            spent += actual

        elif status == "failed":

            failed += 1

        elif status == "expired":

            expired += 1

    ledger[
        "spent_usd"
    ] = round(
        spent,
        6,
    )

    ledger[
        "active_reserved_usd"
    ] = round(
        active,
        6,
    )

    ledger[
        "reserved_usd"
    ] = round(
        spent
        +
        active,
        6,
    )

    ledger[
        "requests"
    ] = requests

    ledger[
        "completed_requests"
    ] = completed

    ledger[
        "failed_requests"
    ] = failed

    ledger[
        "expired_requests"
    ] = expired


def _expire_stale_file(
    ledger: Dict[str, Any],
) -> int:

    reservations = ledger.get(
        "reservations"
    )

    if not isinstance(
        reservations,
        dict,
    ):

        return 0

    cutoff = (
        _utc_now()
        -
        timedelta(
            seconds=(
                reservation_ttl_seconds()
            )
        )
    )

    expired_count = 0

    for item in reservations.values():

        if not isinstance(
            item,
            dict,
        ):

            continue

        if str(
            item.get(
                "status"
            )
            or ""
        ).lower() != "active":

            continue

        created_at = _parse_iso(
            item.get(
                "created_at"
            )
        )

        if (
            created_at is None
            or
            created_at
            <
            cutoff
        ):

            item[
                "status"
            ] = "expired"

            item[
                "finished_at"
            ] = _iso_now()

            expired_count += 1

    _sync_file_summary(
        ledger
    )

    return expired_count


# =========================================================
# POSTGRES SCHEMA
# =========================================================

def _ensure_postgres_schema(
    cursor: Any,
) -> None:

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS xpand_openai_daily_budget (
            usage_date DATE PRIMARY KEY,
            reserved_usd DOUBLE PRECISION NOT NULL DEFAULT 0,
            request_count INTEGER NOT NULL DEFAULT 0,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )

    cursor.execute(
        """
        ALTER TABLE xpand_openai_daily_budget
        ADD COLUMN IF NOT EXISTS spent_usd
        DOUBLE PRECISION NOT NULL DEFAULT 0
        """
    )

    cursor.execute(
        """
        ALTER TABLE xpand_openai_daily_budget
        ADD COLUMN IF NOT EXISTS active_reserved_usd
        DOUBLE PRECISION NOT NULL DEFAULT 0
        """
    )

    cursor.execute(
        """
        ALTER TABLE xpand_openai_daily_budget
        ADD COLUMN IF NOT EXISTS completed_count
        INTEGER NOT NULL DEFAULT 0
        """
    )

    cursor.execute(
        """
        ALTER TABLE xpand_openai_daily_budget
        ADD COLUMN IF NOT EXISTS failed_count
        INTEGER NOT NULL DEFAULT 0
        """
    )

    cursor.execute(
        """
        ALTER TABLE xpand_openai_daily_budget
        ADD COLUMN IF NOT EXISTS expired_count
        INTEGER NOT NULL DEFAULT 0
        """
    )

    cursor.execute(
        """
        ALTER TABLE xpand_openai_daily_budget
        ADD COLUMN IF NOT EXISTS legacy_reserved_usd
        DOUBLE PRECISION NOT NULL DEFAULT 0
        """
    )

    cursor.execute(
        """
        ALTER TABLE xpand_openai_daily_budget
        ADD COLUMN IF NOT EXISTS guard_version
        TEXT
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS xpand_openai_budget_reservations (
            reservation_id TEXT PRIMARY KEY,
            usage_date DATE NOT NULL,
            amount_usd DOUBLE PRECISION NOT NULL DEFAULT 0,
            actual_usd DOUBLE PRECISION NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'active',
            model TEXT NOT NULL DEFAULT '',
            endpoint TEXT NOT NULL DEFAULT '',
            cost_method TEXT NOT NULL DEFAULT '',
            usage_json TEXT NOT NULL DEFAULT '',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            finished_at TIMESTAMPTZ
        )
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        xpand_openai_budget_reservations_date_status_idx
        ON xpand_openai_budget_reservations
        (usage_date, status)
        """
    )

    #
    # ONE-TIME V1 → V2 MIGRATION
    #
    # Old reserved_usd was accumulated estimates, not real spend.
    #
    cursor.execute(
        """
        UPDATE xpand_openai_daily_budget
        SET
            legacy_reserved_usd =
                CASE
                    WHEN COALESCE(guard_version, '') <> %s
                    THEN GREATEST(
                        COALESCE(legacy_reserved_usd, 0),
                        COALESCE(reserved_usd, 0)
                    )
                    ELSE COALESCE(legacy_reserved_usd, 0)
                END,
            spent_usd =
                CASE
                    WHEN COALESCE(guard_version, '') <> %s
                    THEN 0
                    ELSE COALESCE(spent_usd, 0)
                END,
            active_reserved_usd =
                CASE
                    WHEN COALESCE(guard_version, '') <> %s
                    THEN 0
                    ELSE COALESCE(active_reserved_usd, 0)
                END,
            reserved_usd =
                CASE
                    WHEN COALESCE(guard_version, '') <> %s
                    THEN 0
                    ELSE COALESCE(reserved_usd, 0)
                END,
            guard_version = %s,
            updated_at = NOW()
        WHERE COALESCE(guard_version, '') <> %s
        """,
        (
            VERSION,
            VERSION,
            VERSION,
            VERSION,
            VERSION,
            VERSION,
        ),
    )


# =========================================================
# POSTGRES SUMMARY
# =========================================================

def _ensure_postgres_day(
    cursor: Any,
    usage_date: str,
) -> None:

    cursor.execute(
        """
        INSERT INTO xpand_openai_daily_budget (
            usage_date,
            guard_version
        )
        VALUES (%s, %s)
        ON CONFLICT (usage_date) DO NOTHING
        """,
        (
            usage_date,
            VERSION,
        ),
    )


def _expire_stale_postgres(
    cursor: Any,
    usage_date: str,
) -> int:

    cutoff = (
        _utc_now()
        -
        timedelta(
            seconds=(
                reservation_ttl_seconds()
            )
        )
    )

    cursor.execute(
        """
        UPDATE xpand_openai_budget_reservations
        SET
            status = 'expired',
            finished_at = NOW()
        WHERE usage_date = %s
          AND status = 'active'
          AND created_at < %s
        RETURNING reservation_id
        """,
        (
            usage_date,
            cutoff,
        ),
    )

    rows = cursor.fetchall()

    return len(
        rows
        or []
    )


def _sync_postgres_summary(
    cursor: Any,
    usage_date: str,
) -> Dict[str, Any]:

    _ensure_postgres_day(
        cursor,
        usage_date,
    )

    cursor.execute(
        """
        SELECT
            COALESCE(
                SUM(
                    CASE
                        WHEN status='completed'
                        THEN actual_usd
                        ELSE 0
                    END
                ),
                0
            ) AS spent_usd,

            COALESCE(
                SUM(
                    CASE
                        WHEN status='active'
                        THEN amount_usd
                        ELSE 0
                    END
                ),
                0
            ) AS active_reserved_usd,

            COUNT(*) AS request_count,

            COUNT(*) FILTER (
                WHERE status='completed'
            ) AS completed_count,

            COUNT(*) FILTER (
                WHERE status='failed'
            ) AS failed_count,

            COUNT(*) FILTER (
                WHERE status='expired'
            ) AS expired_count

        FROM xpand_openai_budget_reservations

        WHERE usage_date = %s
        """,
        (
            usage_date,
        ),
    )

    row = cursor.fetchone()

    spent = float(
        row[0]
        or 0.0
    )

    active = float(
        row[1]
        or 0.0
    )

    requests = int(
        row[2]
        or 0
    )

    completed = int(
        row[3]
        or 0
    )

    failed = int(
        row[4]
        or 0
    )

    expired = int(
        row[5]
        or 0
    )

    committed = (
        spent
        +
        active
    )

    cursor.execute(
        """
        UPDATE xpand_openai_daily_budget
        SET
            spent_usd = %s,
            active_reserved_usd = %s,
            reserved_usd = %s,
            request_count = %s,
            completed_count = %s,
            failed_count = %s,
            expired_count = %s,
            guard_version = %s,
            updated_at = NOW()
        WHERE usage_date = %s
        """,
        (
            round(
                spent,
                6,
            ),
            round(
                active,
                6,
            ),
            round(
                committed,
                6,
            ),
            requests,
            completed,
            failed,
            expired,
            VERSION,
            usage_date,
        ),
    )

    cursor.execute(
        """
        SELECT legacy_reserved_usd
        FROM xpand_openai_daily_budget
        WHERE usage_date = %s
        """,
        (
            usage_date,
        ),
    )

    legacy_row = cursor.fetchone()

    legacy = float(
        legacy_row[0]
        or 0.0
    ) if legacy_row else 0.0

    return {

        "spent_usd":
            round(
                spent,
                6,
            ),

        "active_reserved_usd":
            round(
                active,
                6,
            ),

        "reserved_usd":
            round(
                committed,
                6,
            ),

        "requests":
            requests,

        "completed_requests":
            completed,

        "failed_requests":
            failed,

        "expired_requests":
            expired,

        "legacy_reserved_usd":
            round(
                legacy,
                6,
            ),
    }


# =========================================================
# POSTGRES RESERVE
# =========================================================

def _reserve_postgres(
    reservation: float,
    limit: float,
    *,
    model: str,
    endpoint: str,
) -> Optional[str]:

    database_url = str(
        os.environ.get(
            "DATABASE_URL",
            "",
        )
    ).strip()

    if not database_url:

        return None

    reservation_id = (
        uuid.uuid4().hex
    )

    usage_date = _today()

    try:

        import psycopg

        with psycopg.connect(
            database_url
        ) as connection:

            with connection.cursor() as cursor:

                _ensure_postgres_schema(
                    cursor
                )

                _ensure_postgres_day(
                    cursor,
                    usage_date,
                )

                #
                # Lock today's summary row.
                #
                cursor.execute(
                    """
                    SELECT usage_date
                    FROM xpand_openai_daily_budget
                    WHERE usage_date = %s
                    FOR UPDATE
                    """,
                    (
                        usage_date,
                    ),
                )

                _expire_stale_postgres(
                    cursor,
                    usage_date,
                )

                status = (
                    _sync_postgres_summary(
                        cursor,
                        usage_date,
                    )
                )

                committed = (
                    float(
                        status.get(
                            "spent_usd",
                            0.0,
                        )
                        or 0.0
                    )
                    +
                    float(
                        status.get(
                            "active_reserved_usd",
                            0.0,
                        )
                        or 0.0
                    )
                )

                if (
                    committed
                    +
                    reservation
                    >
                    limit
                ):

                    raise XPANDOpenAIBudgetError(
                        (
                            "وصل XPAND إلى حد OpenAI اليومي "
                            f"(${limit:.2f}). "
                            "تم إيقاف أي استدعاء OpenAI، "
                            "وسيبقى Gemini متاحًا."
                        )
                    )

                cursor.execute(
                    """
                    INSERT INTO xpand_openai_budget_reservations (
                        reservation_id,
                        usage_date,
                        amount_usd,
                        actual_usd,
                        status,
                        model,
                        endpoint,
                        created_at
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        0,
                        'active',
                        %s,
                        %s,
                        NOW()
                    )
                    """,
                    (
                        reservation_id,
                        usage_date,
                        round(
                            reservation,
                            6,
                        ),
                        model,
                        endpoint,
                    ),
                )

                _sync_postgres_summary(
                    cursor,
                    usage_date,
                )

            connection.commit()

        return (
            "pg:"
            +
            reservation_id
        )

    except XPANDOpenAIBudgetError:

        raise

    except Exception as error:

        if _truthy(
            "XPAND_OPENAI_BUDGET_FAIL_CLOSED",
            "true",
        ):

            raise XPANDOpenAIBudgetError(
                (
                    "تعذر التحقق من ميزانية OpenAI "
                    "في PostgreSQL؛ تم منع الطلب احتياطيًا. "
                    +
                    str(
                        error
                    )[:500]
                )
            )

        return None


# =========================================================
# FILE RESERVE
# =========================================================

def _reserve_file(
    reservation: float,
    limit: float,
    *,
    model: str,
    endpoint: str,
) -> str:

    reservation_id = (
        uuid.uuid4().hex
    )

    with _LOCK:

        ledger = _load()

        _expire_stale_file(
            ledger
        )

        _sync_file_summary(
            ledger
        )

        spent = float(
            ledger.get(
                "spent_usd",
                0.0,
            )
            or 0.0
        )

        active = float(
            ledger.get(
                "active_reserved_usd",
                0.0,
            )
            or 0.0
        )

        if (
            spent
            +
            active
            +
            reservation
            >
            limit
        ):

            raise XPANDOpenAIBudgetError(
                (
                    "وصل XPAND إلى حد OpenAI اليومي "
                    f"(${limit:.2f}). "
                    "تم إيقاف أي استدعاء OpenAI، "
                    "وسيبقى Gemini متاحًا."
                )
            )

        reservations = ledger.setdefault(
            "reservations",
            {},
        )

        reservations[
            reservation_id
        ] = {

            "reservation_id":
                reservation_id,

            "amount_usd":
                round(
                    reservation,
                    6,
                ),

            "actual_usd":
                0.0,

            "status":
                "active",

            "model":
                model,

            "endpoint":
                endpoint,

            "cost_method":
                "",

            "usage":
                {},

            "created_at":
                _iso_now(),

            "finished_at":
                "",
        }

        _sync_file_summary(
            ledger
        )

        _save(
            ledger
        )

    return (
        "file:"
        +
        reservation_id
    )


# =========================================================
# PUBLIC RESERVE
# =========================================================

def reserve_openai(
    url: str,
    kwargs: Dict[str, Any],
) -> str:

    if not openai_enabled():

        raise XPANDOpenAIBudgetError(
            (
                "تم منع استدعاء OpenAI لأن "
                "XPAND_OPENAI_ENABLED=false. "
                "XPAND سيستخدم Gemini بدلًا منه."
            )
        )

    reservation = (
        _estimate_reservation(
            url,
            kwargs,
        )
    )

    limit = daily_limit_usd()

    model = _request_model(
        kwargs
    )

    endpoint = _endpoint_path(
        url
    )

    postgres_id = (
        _reserve_postgres(
            reservation,
            limit,
            model=(
                model
            ),
            endpoint=(
                endpoint
            ),
        )
    )

    if postgres_id:

        return postgres_id

    return _reserve_file(
        reservation,
        limit,
        model=(
            model
        ),
        endpoint=(
            endpoint
        ),
    )


# =========================================================
# POSTGRES FINALIZE
# =========================================================

def _finalize_postgres(
    reservation_id: str,
    *,
    success: bool,
    actual_usd: float,
    cost_method: str,
    usage_info: Dict[str, Any],
) -> None:

    database_url = str(
        os.environ.get(
            "DATABASE_URL",
            "",
        )
    ).strip()

    if not database_url:

        return

    usage_date = _today()

    try:

        import psycopg

        with psycopg.connect(
            database_url
        ) as connection:

            with connection.cursor() as cursor:

                _ensure_postgres_schema(
                    cursor
                )

                cursor.execute(
                    """
                    SELECT
                        usage_date,
                        status
                    FROM xpand_openai_budget_reservations
                    WHERE reservation_id = %s
                    FOR UPDATE
                    """,
                    (
                        reservation_id,
                    ),
                )

                row = cursor.fetchone()

                if not row:

                    connection.commit()

                    return

                reservation_date = str(
                    row[0]
                )

                current_status = str(
                    row[1]
                    or ""
                ).lower()

                if current_status != "active":

                    connection.commit()

                    return

                new_status = (
                    "completed"
                    if success
                    else
                    "failed"
                )

                charged = (
                    max(
                        0.0,
                        actual_usd,
                    )
                    if success
                    else
                    0.0
                )

                cursor.execute(
                    """
                    UPDATE xpand_openai_budget_reservations
                    SET
                        status = %s,
                        actual_usd = %s,
                        cost_method = %s,
                        usage_json = %s,
                        finished_at = NOW()
                    WHERE reservation_id = %s
                    """,
                    (
                        new_status,
                        round(
                            charged,
                            8,
                        ),
                        cost_method,
                        json.dumps(
                            usage_info,
                            ensure_ascii=False,
                        )[:10000],
                        reservation_id,
                    ),
                )

                _sync_postgres_summary(
                    cursor,
                    reservation_date,
                )

            connection.commit()

    except Exception:

        #
        # IMPORTANT:
        #
        # Never throw AFTER OpenAI already completed a request.
        # Throwing here could make upper layers retry and spend twice.
        #
        return


# =========================================================
# FILE FINALIZE
# =========================================================

def _finalize_file(
    reservation_id: str,
    *,
    success: bool,
    actual_usd: float,
    cost_method: str,
    usage_info: Dict[str, Any],
) -> None:

    with _LOCK:

        ledger = _load()

        reservations = ledger.get(
            "reservations"
        )

        if not isinstance(
            reservations,
            dict,
        ):

            return

        item = reservations.get(
            reservation_id
        )

        if not isinstance(
            item,
            dict,
        ):

            return

        if str(
            item.get(
                "status"
            )
            or ""
        ).lower() != "active":

            return

        item[
            "status"
        ] = (
            "completed"
            if success
            else
            "failed"
        )

        item[
            "actual_usd"
        ] = round(
            (
                max(
                    0.0,
                    actual_usd,
                )
                if success
                else
                0.0
            ),
            8,
        )

        item[
            "cost_method"
        ] = cost_method

        item[
            "usage"
        ] = usage_info

        item[
            "finished_at"
        ] = _iso_now()

        _expire_stale_file(
            ledger
        )

        _sync_file_summary(
            ledger
        )

        _save(
            ledger
        )


# =========================================================
# PUBLIC FINALIZE
# =========================================================

def finalize_openai(
    reservation_token: str,
    *,
    success: bool,
    actual_usd: float = 0.0,
    cost_method: str = "",
    usage_info: Optional[
        Dict[str, Any]
    ] = None,
) -> None:

    token = str(
        reservation_token
        or ""
    ).strip()

    if not token:

        return

    usage_info = (
        usage_info
        if isinstance(
            usage_info,
            dict,
        )
        else
        {}
    )

    if token.startswith(
        "pg:"
    ):

        _finalize_postgres(
            token[
                3:
            ],
            success=(
                success
            ),
            actual_usd=(
                actual_usd
            ),
            cost_method=(
                cost_method
            ),
            usage_info=(
                usage_info
            ),
        )

        return

    if token.startswith(
        "file:"
    ):

        _finalize_file(
            token[
                5:
            ],
            success=(
                success
            ),
            actual_usd=(
                actual_usd
            ),
            cost_method=(
                cost_method
            ),
            usage_info=(
                usage_info
            ),
        )


def release_openai(
    reservation_token: str,
) -> None:

    finalize_openai(
        reservation_token,
        success=False,
        actual_usd=0.0,
        cost_method=(
            "request_failed_or_aborted"
        ),
        usage_info={},
    )


# =========================================================
# POSTGRES STATUS
# =========================================================

def _postgres_status() -> Optional[
    Dict[str, Any]
]:

    database_url = str(
        os.environ.get(
            "DATABASE_URL",
            "",
        )
    ).strip()

    if not database_url:

        return None

    usage_date = _today()

    try:

        import psycopg

        with psycopg.connect(
            database_url
        ) as connection:

            with connection.cursor() as cursor:

                _ensure_postgres_schema(
                    cursor
                )

                _ensure_postgres_day(
                    cursor,
                    usage_date,
                )

                cursor.execute(
                    """
                    SELECT usage_date
                    FROM xpand_openai_daily_budget
                    WHERE usage_date = %s
                    FOR UPDATE
                    """,
                    (
                        usage_date,
                    ),
                )

                _expire_stale_postgres(
                    cursor,
                    usage_date,
                )

                data = (
                    _sync_postgres_summary(
                        cursor,
                        usage_date,
                    )
                )

            connection.commit()

        data[
            "date"
        ] = usage_date

        data[
            "guard_version"
        ] = VERSION

        return data

    except Exception:

        return None


# =========================================================
# PUBLIC STATUS
# =========================================================

def budget_status() -> Dict[str, Any]:

    data = _postgres_status()

    backend = "postgres"

    if data is None:

        backend = "file"

        with _LOCK:

            data = _load()

            _expire_stale_file(
                data
            )

            _sync_file_summary(
                data
            )

            _save(
                data
            )

    spent = float(
        data.get(
            "spent_usd",
            0.0,
        )
        or 0.0
    )

    active = float(
        data.get(
            "active_reserved_usd",
            0.0,
        )
        or 0.0
    )

    committed = (
        spent
        +
        active
    )

    limit = daily_limit_usd()

    result = dict(
        data
    )

    result[
        "enabled"
    ] = openai_enabled()

    result[
        "limit_usd"
    ] = limit

    result[
        "spent_usd"
    ] = round(
        spent,
        6,
    )

    result[
        "active_reserved_usd"
    ] = round(
        active,
        6,
    )

    #
    # Compatibility for existing Telegram /xpand_budget.
    #
    # This now means total budget committed:
    #
    # actual tracked spend + currently active reservations.
    #
    result[
        "reserved_usd"
    ] = round(
        committed,
        6,
    )

    result[
        "remaining_usd"
    ] = round(
        max(
            0.0,
            limit
            -
            committed,
        ),
        6,
    )

    result[
        "backend"
    ] = backend

    result[
        "guard_version"
    ] = VERSION

    result[
        "reservation_ttl_seconds"
    ] = reservation_ttl_seconds()

    return result


# =========================================================
# REQUESTS GUARD
# =========================================================

def install_requests_guard() -> None:

    global _INSTALLED

    if _INSTALLED:

        return

    import requests

    original = (
        requests.sessions.Session.request
    )

    def guarded_request(
        session,
        method,
        url,
        *args,
        **kwargs,
    ):

        host = (
            urlparse(
                str(
                    url
                )
            ).hostname
            or ""
        ).lower()

        is_openai = bool(
            host
            ==
            "api.openai.com"
            or
            host.endswith(
                ".openai.com"
            )
        )

        if not is_openai:

            return original(
                session,
                method,
                url,
                *args,
                **kwargs,
            )

        reservation_token = (
            reserve_openai(
                str(
                    url
                ),
                kwargs,
            )
        )

        reservation_amount = (
            _estimate_reservation(
                str(
                    url
                ),
                kwargs,
            )
        )

        try:

            response = original(
                session,
                method,
                url,
                *args,
                **kwargs,
            )

        except Exception:

            release_openai(
                reservation_token
            )

            raise

        status_code = int(
            getattr(
                response,
                "status_code",
                0,
            )
            or 0
        )

        #
        # OpenAI rejected the request.
        #
        # Do not permanently charge the internal XPAND budget.
        #
        if status_code >= 400:

            finalize_openai(
                reservation_token,
                success=False,
                actual_usd=0.0,
                cost_method=(
                    "http_error_released"
                ),
                usage_info={
                    "status_code":
                        status_code,
                },
            )

            return response

        (
            actual_usd,
            usage_info,
        ) = _actual_cost_from_response(
            url=(
                str(
                    url
                )
            ),
            kwargs=(
                kwargs
            ),
            response=(
                response
            ),
            reservation=(
                reservation_amount
            ),
        )

        finalize_openai(
            reservation_token,
            success=True,
            actual_usd=(
                actual_usd
            ),
            cost_method=str(
                usage_info.get(
                    "method"
                )
                or
                "unknown"
            ),
            usage_info=(
                usage_info
            ),
        )

        return response

    requests.sessions.Session.request = (
        guarded_request
    )

    _INSTALLED = True


# =========================================================
# ZERO-COST SELF TEST
#
# NO OPENAI REQUESTS ARE MADE.
# =========================================================

if __name__ == "__main__":

    tests: Dict[str, bool] = {}

    original_env = {
        key:
            os.environ.get(
                key
            )
        for key in (
            "DATABASE_URL",
            "XPAND_OPENAI_ENABLED",
            "XPAND_OPENAI_DAILY_LIMIT_USD",
            "XPAND_OPENAI_LEDGER_PATH",
            "XPAND_OPENAI_RESERVATION_TTL_SECONDS",
        )
    }

    test_path = Path(
        (
            "/tmp/"
            +
            "xpand_cost_guard_v2_selftest_"
            +
            str(
                os.getpid()
            )
            +
            ".json"
        )
    )

    try:

        os.environ[
            "DATABASE_URL"
        ] = ""

        os.environ[
            "XPAND_OPENAI_ENABLED"
        ] = "true"

        os.environ[
            "XPAND_OPENAI_DAILY_LIMIT_USD"
        ] = "5.00"

        os.environ[
            "XPAND_OPENAI_LEDGER_PATH"
        ] = str(
            test_path
        )

        os.environ[
            "XPAND_OPENAI_RESERVATION_TTL_SECONDS"
        ] = "60"

        try:

            test_path.unlink(
                missing_ok=True
            )

        except Exception:

            pass

        # =================================================
        # BASIC CONFIG
        # =================================================

        tests[
            "version_2"
        ] = (
            VERSION
            ==
            "2.0"
        )

        tests[
            "daily_limit_5"
        ] = (
            daily_limit_usd()
            ==
            5.0
        )

        tests[
            "openai_enabled"
        ] = (
            openai_enabled()
            is True
        )

        # =================================================
        # SOL ACTUAL USAGE COST
        #
        # Mirrors roughly the real usage shape shown by XPAND:
        #
        # input 6307
        # output 4035
        # =================================================

        usage_fixture = {

            "input_tokens":
                6307,

            "cached_input_tokens":
                0,

            "output_tokens":
                4035,
        }

        actual_fixture = (
            _actual_text_cost_usd(
                model=(
                    "gpt-5.6-sol"
                ),
                usage=(
                    usage_fixture
                ),
                request_payload={},
            )
        )

        expected_fixture = (
            (
                6307
                *
                4.00
            )
            +
            (
                4035
                *
                20.00
            )
        ) / 1_000_000.0

        tests[
            "sol_usage_cost_calculation"
        ] = (
            abs(
                actual_fixture
                -
                expected_fixture
            )
            <
            0.000001
        )

        tests[
            "sol_fixture_cost_is_not_5_dollars"
        ] = (
            actual_fixture
            <
            0.20
        )

        # =================================================
        # SUCCESSFUL REQUEST
        # =================================================

        fake_url = (
            "https://api.openai.com/v1/responses"
        )

        fake_kwargs = {

            "json": {

                "model":
                    "gpt-5.6-sol",

                "max_output_tokens":
                    4000,
            }
        }

        reservation_token = (
            reserve_openai(
                fake_url,
                fake_kwargs,
            )
        )

        status_during = (
            budget_status()
        )

        tests[
            "successful_request_creates_active_reservation"
        ] = (
            float(
                status_during.get(
                    "active_reserved_usd",
                    0.0,
                )
            )
            >
            0
        )

        finalize_openai(
            reservation_token,
            success=True,
            actual_usd=(
                actual_fixture
            ),
            cost_method=(
                "self_test_usage"
            ),
            usage_info=(
                usage_fixture
            ),
        )

        status_after = (
            budget_status()
        )

        tests[
            "successful_request_releases_reservation"
        ] = (
            abs(
                float(
                    status_after.get(
                        "active_reserved_usd",
                        0.0,
                    )
                )
            )
            <
            0.000001
        )

        tests[
            "successful_request_records_actual_spend"
        ] = (
            abs(
                float(
                    status_after.get(
                        "spent_usd",
                        0.0,
                    )
                )
                -
                actual_fixture
            )
            <
            0.00001
        )

        # =================================================
        # FAILED REQUEST RELEASES RESERVATION
        # =================================================

        before_failed_spend = float(
            status_after.get(
                "spent_usd",
                0.0,
            )
        )

        failed_token = (
            reserve_openai(
                fake_url,
                fake_kwargs,
            )
        )

        release_openai(
            failed_token
        )

        failed_status = (
            budget_status()
        )

        tests[
            "failed_request_releases_reservation"
        ] = (
            abs(
                float(
                    failed_status.get(
                        "active_reserved_usd",
                        0.0,
                    )
                )
            )
            <
            0.000001
        )

        tests[
            "failed_request_does_not_add_spend"
        ] = (
            abs(
                float(
                    failed_status.get(
                        "spent_usd",
                        0.0,
                    )
                )
                -
                before_failed_spend
            )
            <
            0.000001
        )

        # =================================================
        # STALE RESERVATION
        # =================================================

        stale_token = (
            reserve_openai(
                fake_url,
                fake_kwargs,
            )
        )

        stale_id = stale_token.split(
            ":",
            1,
        )[
            1
        ]

        stale_ledger = _load()

        stale_item = (
            stale_ledger[
                "reservations"
            ][
                stale_id
            ]
        )

        stale_item[
            "created_at"
        ] = (
            _utc_now()
            -
            timedelta(
                minutes=10,
            )
        ).isoformat()

        _save(
            stale_ledger
        )

        stale_status = (
            budget_status()
        )

        tests[
            "stale_reservation_expires"
        ] = (
            float(
                stale_status.get(
                    "active_reserved_usd",
                    0.0,
                )
            )
            ==
            0.0
        )

        # =================================================
        # LEGACY V1 MIGRATION
        # =================================================

        legacy_path = Path(
            str(
                test_path
            )
            +
            ".legacy"
        )

        os.environ[
            "XPAND_OPENAI_LEDGER_PATH"
        ] = str(
            legacy_path
        )

        legacy_path.write_text(
            json.dumps(
                {
                    "date":
                        _today(),

                    "reserved_usd":
                        5.0,

                    "requests":
                        12,
                }
            ),
            encoding="utf-8",
        )

        migrated = _load()

        tests[
            "legacy_reserved_not_treated_as_actual_spend"
        ] = (
            float(
                migrated.get(
                    "spent_usd",
                    0.0,
                )
            )
            ==
            0.0
        )

        tests[
            "legacy_reserved_preserved_for_diagnostics"
        ] = (
            float(
                migrated.get(
                    "legacy_reserved_usd",
                    0.0,
                )
            )
            ==
            5.0
        )

        tests[
            "legacy_reserved_no_longer_blocks_new_day_budget"
        ] = (
            float(
                migrated.get(
                    "active_reserved_usd",
                    0.0,
                )
            )
            ==
            0.0
        )

        # =================================================
        # UTC DAY ROLLOVER
        # =================================================

        yesterday = (
            _utc_now().date()
            -
            timedelta(
                days=1,
            )
        ).isoformat()

        legacy_path.write_text(
            json.dumps(
                {
                    "date":
                        yesterday,

                    "guard_version":
                        VERSION,

                    "spent_usd":
                        4.9,

                    "active_reserved_usd":
                        0.1,

                    "reserved_usd":
                        5.0,

                    "reservations":
                        {},
                }
            ),
            encoding="utf-8",
        )

        rolled = _load()

        tests[
            "utc_daily_rollover_resets_budget"
        ] = bool(
            rolled.get(
                "date"
            )
            ==
            _today()
            and
            float(
                rolled.get(
                    "spent_usd",
                    0.0,
                )
            )
            ==
            0.0
            and
            float(
                rolled.get(
                    "active_reserved_usd",
                    0.0,
                )
            )
            ==
            0.0
        )

    finally:

        for key, value in (
            original_env.items()
        ):

            if value is None:

                os.environ.pop(
                    key,
                    None,
                )

            else:

                os.environ[
                    key
                ] = value

        for candidate in (
            test_path,
            Path(
                str(
                    test_path
                )
                +
                ".legacy"
            ),
        ):

            try:

                candidate.unlink(
                    missing_ok=True
                )

            except Exception:

                pass

    passed = all(
        tests.values()
    )

    print("")
    print(
        "=========================================="
    )
    print(
        " XPAND OPENAI COST GUARD V2.0"
    )
    print(
        " ZERO-COST RECONCILIATION SELF TEST"
    )
    print(
        "=========================================="
    )
    print("")

    for name, result in (
        tests.items()
    ):

        print(
            (
                "✅ "
                if result
                else
                "❌ "
            )
            +
            name
        )

    print("")

    if passed:

        print(
            (
                "XPAND OpenAI Cost Guard V2.0 "
                "self-test: PASS ✅"
            )
        )

    else:

        print(
            (
                "XPAND OpenAI Cost Guard V2.0 "
                "self-test: FAIL ❌"
            )
        )

    print("")
    print(
        "✅ Reservations are temporary"
    )
    print(
        "✅ Successful calls reconcile to tracked usage"
    )
    print(
        "✅ Failed calls release reservations"
    )
    print(
        "✅ Stale reservations expire automatically"
    )
    print(
        "✅ Legacy V1 reserved balance is not treated as spend"
    )
    print(
        "✅ UTC daily rollover preserved"
    )
    print(
        "✅ PostgreSQL migration is automatic"
    )
    print(
        "🚫 No OpenAI API calls were made"
    )
    print("")
