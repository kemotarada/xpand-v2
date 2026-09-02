# =========================================================
# KEMO SCHEDULER RUNTIME V5.1
#
# ACTIVE JOB LEASE FIX
#
# Keeps scheduler_projects.py untouched.
#
# Fix:
# - Project worker heartbeat renews the active job lock.
# - Long website builds are no longer falsely recovered
#   as stale after 15 minutes.
# - Existing scheduler / reminders / market hunter preserved.
# - Existing publishing approval preserved.
# =========================================================

import scheduler_projects as projects


# =========================================================
# VERSION
# =========================================================

VERSION = "5.1"


# =========================================================
# PRESERVE ORIGINAL HEARTBEAT
# =========================================================

ORIGINAL_WORKER_HEARTBEAT = (
    projects.worker_heartbeat
)


# =========================================================
# HEARTBEAT + ACTIVE JOB LEASE RENEWAL
# =========================================================

def worker_heartbeat_v51(
    payload
):
    # First preserve all original heartbeat behavior.
    result = ORIGINAL_WORKER_HEARTBEAT(
        payload
    )

    try:
        worker_id = projects.clean_text(
            payload.get(
                "workerId"
            ),
            200
        )

        current_job_id = projects.valid_uuid(
            payload.get(
                "currentJobId"
            )
        )

        if (
            worker_id
            and
            current_job_id
        ):
            with projects.db_connect() as conn:

                with conn.cursor() as cur:

                    cur.execute(
                        """
                        UPDATE kemo_project_jobs

                        SET
                            locked_at =
                                NOW(),

                            updated_at =
                                NOW()

                        WHERE
                            id = %s

                            AND worker_id =
                                %s

                            AND status =
                                'working';
                        """,
                        (
                            current_job_id,
                            worker_id
                        )
                    )

    except Exception as error:
        # Heartbeat itself must never crash because
        # lease renewal had a temporary DB issue.
        print(
            (
                "⚠️ Active job lease renewal: "
                +
                str(
                    error
                )
            )
        )

    return result


# =========================================================
# INSTALL FIX
# =========================================================

projects.worker_heartbeat = (
    worker_heartbeat_v51
)


# Extra safety margin.
#
# Active jobs will normally keep renewing locked_at.
# This only matters if heartbeats really stop.
projects.PROJECT_JOB_STUCK_MINUTES = 60


# Health/version reporting.
projects.VERSION = VERSION


# =========================================================
# MAIN
# =========================================================

def main():
    print("")
    print(
        "=========================================="
    )
    print(
        " KEMO SCHEDULER RUNTIME V5.1"
    )
    print(
        " ACTIVE JOB LEASE FIX"
    )
    print(
        "=========================================="
    )
    print("")

    print(
        "✅ scheduler_projects.py preserved"
    )

    print(
        "✅ Original scheduler preserved"
    )

    print(
        "✅ Worker heartbeat preserved"
    )

    print(
        "✅ Active job lock renewal enabled"
    )

    print(
        "✅ Long website jobs protected"
    )

    print(
        "✅ Stale recovery safety: 60 minutes"
    )

    print(
        "🛡️ Publishing approval preserved"
    )

    print("")

    projects.main()


if __name__ == "__main__":
    main()
