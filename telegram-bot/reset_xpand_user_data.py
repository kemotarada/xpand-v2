# =========================================================
# XPAND USER DATA RESET V1.0
#
# PURPOSE:
# - Remove all old user-specific data from XPAND database
# - Start XPAND fresh for Ihab
#
# PRESERVED:
# - Database schema
# - kemo_config
# - Agent Factory
# - Agent capability registry
# - Runtime secrets
# - API keys
# - Telegram bot token
#
# IMPORTANT:
# This script performs a destructive ONE-TIME cleanup.
# It deletes data, but does NOT drop tables.
# =========================================================


import os
import sys

import psycopg


# =========================================================
# SETTINGS
# =========================================================

VERSION = "1.0"

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    ""
).strip()

EXPECTED_USER_RAW = os.environ.get(
    "TELEGRAM_ALLOWED_USER_ID",
    ""
).strip()


# =========================================================
# TABLES TO CLEAR
# =========================================================

#
# Only user/personal/conversation state belongs here.
#
# DO NOT add:
# - kemo_config
# - agent registry tables
# - capability registry tables
# - deployment/configuration tables
#

USER_DATA_TABLES = [
    "memory_learning_jobs",
    "canonical_fact_history",
    "canonical_facts",
    "memory_archive",
    "call_artifacts",
    "dialect_terms",
    "reminder_dialog_state",
    "scheduled_jobs",
    "conversation_state",
    "lessons",
    "profile_facts",
    "memories",
    "messages",
    "kemo_events",

    # May be created by the scheduler / market hunter stack.
    # It is cleared only if it exists.
    "market_opportunities",
]


# =========================================================
# PRESERVED TABLES
# =========================================================

PRESERVED_TABLES = [
    "kemo_config",
    "processed_updates",
]


# =========================================================
# HELPERS
# =========================================================

def db_connect():

    return psycopg.connect(
        DATABASE_URL,
        connect_timeout=10
    )


def validate_environment():

    if not DATABASE_URL:

        raise RuntimeError(
            "DATABASE_URL missing"
        )


    if not EXPECTED_USER_RAW:

        raise RuntimeError(
            "TELEGRAM_ALLOWED_USER_ID missing"
        )


    try:

        user_id = int(
            EXPECTED_USER_RAW
        )

    except ValueError:

        raise RuntimeError(
            "TELEGRAM_ALLOWED_USER_ID is not a valid integer"
        )


    if user_id <= 0:

        raise RuntimeError(
            "TELEGRAM_ALLOWED_USER_ID is invalid"
        )


    return user_id


def table_exists(
    cur,
    table_name
):

    cur.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE
                table_schema = 'public'
                AND table_name = %s
        );
        """,
        (
            table_name,
        )
    )


    row = cur.fetchone()


    return bool(
        row
        and
        row[0]
    )


def table_count(
    cur,
    table_name
):

    cur.execute(
        f'SELECT COUNT(*) FROM "{table_name}";'
    )


    row = cur.fetchone()


    return (
        int(
            row[0]
        )
        if row
        else 0
    )


def delete_table_rows(
    cur,
    table_name
):

    before = table_count(
        cur,
        table_name
    )


    cur.execute(
        f'DELETE FROM "{table_name}";'
    )


    after = table_count(
        cur,
        table_name
    )


    return {
        "before":
            before,

        "deleted":
            before - after,

        "after":
            after,
    }


# =========================================================
# RESET
# =========================================================

def reset_user_data():

    ihab_user_id = validate_environment()


    print("")

    print(
        "=============================================="
    )

    print(
        " XPAND USER DATA RESET V1.0"
    )

    print(
        "=============================================="
    )

    print("")

    print(
        "Target environment:"
    )

    print(
        "XPAND production database"
    )

    print("")

    print(
        "Authorized Telegram user:"
    )

    print(
        str(
            ihab_user_id
        )
    )

    print("")

    print(
        "⚠️ Removing old user data..."
    )

    print("")


    deleted_total = 0

    cleared_tables = []

    skipped_tables = []


    with db_connect() as conn:

        with conn.cursor() as cur:

            # =============================================
            # TRANSACTION-LEVEL LOCK
            #
            # Prevent two reset jobs from running at once.
            # =============================================

            cur.execute(
                """
                SELECT pg_advisory_xact_lock(
                    880022001
                );
                """
            )


            # =============================================
            # CLEAR USER DATA
            # =============================================

            for table_name in USER_DATA_TABLES:

                if not table_exists(
                    cur,
                    table_name
                ):

                    print(
                        (
                            "ℹ️ "
                            +
                            table_name
                            +
                            ": table not found — skipped"
                        )
                    )

                    skipped_tables.append(
                        table_name
                    )

                    continue


                result = delete_table_rows(
                    cur,
                    table_name
                )


                deleted_total += result[
                    "deleted"
                ]


                cleared_tables.append(
                    table_name
                )


                print(
                    (
                        "✅ "
                        +
                        table_name
                        +
                        ": deleted "
                        +
                        str(
                            result[
                                "deleted"
                            ]
                        )
                        +
                        " row(s)"
                    )
                )


            # =============================================
            # STORE SAFE RESET MARKER
            #
            # This does NOT store personal data.
            # kemo_config itself is preserved.
            # =============================================

            if table_exists(
                cur,
                "kemo_config"
            ):

                cur.execute(
                    """
                    INSERT INTO kemo_config
                    (
                        config_key,
                        config_value,
                        updated_at
                    )
                    VALUES (
                        'xpand_user_data_reset_version',
                        %s,
                        NOW()
                    )
                    ON CONFLICT(config_key)
                    DO UPDATE SET
                        config_value =
                        EXCLUDED.config_value,
                        updated_at =
                        NOW();
                    """,
                    (
                        VERSION,
                    )
                )


                cur.execute(
                    """
                    INSERT INTO kemo_config
                    (
                        config_key,
                        config_value,
                        updated_at
                    )
                    VALUES (
                        'xpand_primary_user_name',
                        'إيهاب',
                        NOW()
                    )
                    ON CONFLICT(config_key)
                    DO UPDATE SET
                        config_value =
                        EXCLUDED.config_value,
                        updated_at =
                        NOW();
                    """
                )


            # Context manager commits only if every
            # statement completed successfully.


    print("")

    print(
        "=============================================="
    )

    print(
        " RESET COMPLETE"
    )

    print(
        "=============================================="
    )

    print("")

    print(
        (
            "✅ Total deleted rows: "
            +
            str(
                deleted_total
            )
        )
    )

    print("")

    print(
        "✅ Old conversations removed"
    )

    print(
        "✅ Old contextual memories removed"
    )

    print(
        "✅ Old profile facts removed"
    )

    print(
        "✅ Old canonical facts removed"
    )

    print(
        "✅ Canonical fact history removed"
    )

    print(
        "✅ Full memory archive removed"
    )

    print(
        "✅ Background memory jobs removed"
    )

    print(
        "✅ Old lessons removed"
    )

    print(
        "✅ Old dialect learning removed"
    )

    print(
        "✅ Old call memory removed"
    )

    print(
        "✅ Old reminders removed"
    )

    print(
        "✅ Old event history removed"
    )

    print(
        "✅ Old market opportunity history removed when present"
    )

    print("")

    print(
        "🔒 kemo_config preserved"
    )

    print(
        "🔒 Database schema preserved"
    )

    print(
        "🔒 Agent Factory preserved"
    )

    print(
        "🔒 Capability registry preserved"
    )

    print(
        "🔒 Secrets preserved"
    )

    print("")

    print(
        "✅ XPAND user memory is now clean."
    )

    print(
        "➡️ Ready to start fresh with Ihab."
    )

    print("")


# =========================================================
# MAIN
# =========================================================

def main():

    try:

        reset_user_data()


    except KeyboardInterrupt:

        print("")

        print(
            "❌ Reset cancelled."
        )

        sys.exit(
            1
        )


    except Exception as error:

        print("")

        print(
            (
                "❌ XPAND user data reset failed: "
                +
                str(
                    error
                )
            )
        )

        print("")

        print(
            "No successful completion was recorded."
        )

        print("")

        sys.exit(
            1
        )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    main()
