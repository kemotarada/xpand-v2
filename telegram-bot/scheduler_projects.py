# =========================================================
# KEMO SCHEDULER + PROJECTS V5.0
#
# SAME RAILWAY SERVICE
#
# Keeps existing scheduler.py untouched:
# - Persistent reminders
# - Market Hunter
#
# Adds:
# - Background project manager
# - Real worker queue
# - Worker heartbeat
# - Verified working state
# - Progress tracking
# - Activity timeline
# - Screenshot proof -> Telegram
# - Preview URL tracking
# - Production URL tracking
# - QA tracking
# - Publish approval gate
#
# Start command:
# python scheduler_projects.py
#
# Safety:
# - No arbitrary shell execution
# - Internal API protected with KEMO_PROJECTS_KEY
# - Publishing requires explicit approval
# =========================================================

import os
import re
import io
import json
import time
import uuid
import hmac
import base64
import hashlib
import threading
import urllib.request
import urllib.error
import urllib.parse

from datetime import datetime
from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
)

import psycopg
from psycopg.rows import dict_row

import scheduler


# =========================================================
# VERSION
# =========================================================

VERSION = "5.0"


# =========================================================
# ENV
# =========================================================

PORT = int(
    os.environ.get(
        "PORT",
        "8080"
    )
)


DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    ""
).strip()


KEMO_PROJECTS_KEY = os.environ.get(
    "KEMO_PROJECTS_KEY",
    ""
).strip()


TELEGRAM_BOT_TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN",
    ""
).strip()


ALLOWED_USER_RAW = os.environ.get(
    "TELEGRAM_ALLOWED_USER_ID",
    "0"
).strip()


try:

    TELEGRAM_ALLOWED_USER_ID = int(
        ALLOWED_USER_RAW
    )

except Exception:

    TELEGRAM_ALLOWED_USER_ID = 0


# =========================================================
# SETTINGS
# =========================================================

MAX_JSON_BODY_BYTES = (
    16
    *
    1024
    *
    1024
)


MAX_SCREENSHOT_BYTES = (
    9
    *
    1024
    *
    1024
)


WORKER_ONLINE_SECONDS = 30


PROJECT_ACTIVITY_FRESH_SECONDS = 120


PROJECT_JOB_STUCK_MINUTES = 15


PROJECT_MAINTENANCE_SECONDS = 60


PROJECT_SERVER_STARTED_AT = (
    datetime.utcnow()
    .isoformat()
    +
    "Z"
)


# =========================================================
# RUNTIME
# =========================================================

SCHEDULER_THREAD = None


# =========================================================
# TEXT
# =========================================================

def clean_text(
    value,
    limit=5000
):

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


def safe_int(
    value,
    fallback=0
):

    try:

        return int(
            value
        )

    except Exception:

        return fallback


def clamp(
    value,
    minimum,
    maximum
):

    return max(
        minimum,
        min(
            maximum,
            value
        )
    )


def now_iso():

    return (
        datetime.utcnow()
        .isoformat()
        +
        "Z"
    )


def valid_uuid(
    value
):

    try:

        return str(
            uuid.UUID(
                str(
                    value
                )
            )
        )

    except Exception:

        return None


def create_uuid():

    return str(
        uuid.uuid4()
    )


def json_default(
    value
):

    return str(
        value
    )


# =========================================================
# DATABASE
# =========================================================

def db_connect():

    return psycopg.connect(
        DATABASE_URL,
        connect_timeout=10,
        row_factory=dict_row
    )


# =========================================================
# AUTH
# =========================================================

def safe_secret_equal(
    supplied,
    expected
):

    supplied = str(
        supplied or ""
    )

    expected = str(
        expected or ""
    )

    if (
        not supplied
        or
        not expected
    ):

        return False


    try:

        return hmac.compare_digest(
            supplied,
            expected
        )

    except Exception:

        return False


def resolve_user_id(
    value=None
):

    requested = safe_int(
        value,
        0
    )


    if TELEGRAM_ALLOWED_USER_ID:

        if (
            requested
            and
            requested
            !=
            TELEGRAM_ALLOWED_USER_ID
        ):

            raise RuntimeError(
                "Unauthorized user"
            )


        return TELEGRAM_ALLOWED_USER_ID


    if requested <= 0:

        raise RuntimeError(
            "Valid userId required"
        )


    return requested


# =========================================================
# DATABASE INIT
# =========================================================

def init_projects_database():

    print(
        "🗄️ Preparing Kemo Projects database..."
    )


    with db_connect() as conn:

        with conn.cursor() as cur:

            # =================================================
            # PROJECTS
            # =================================================

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS
                kemo_projects (

                    id UUID PRIMARY KEY,

                    user_id BIGINT NOT NULL,

                    project_type TEXT
                    NOT NULL DEFAULT 'website',

                    name TEXT NOT NULL,

                    brief TEXT
                    NOT NULL DEFAULT '',

                    status TEXT
                    NOT NULL DEFAULT 'queued',

                    stage TEXT
                    NOT NULL DEFAULT 'intake',

                    progress INTEGER
                    NOT NULL DEFAULT 0,

                    current_task TEXT
                    NOT NULL DEFAULT '',

                    last_completed TEXT
                    NOT NULL DEFAULT '',

                    worker_id TEXT,

                    local_path TEXT,

                    repo_url TEXT,

                    preview_url TEXT,

                    production_url TEXT,

                    last_screenshot_file_id TEXT,

                    last_screenshot_at TIMESTAMPTZ,

                    quality_score INTEGER,

                    qa_report JSONB
                    NOT NULL DEFAULT '{}'::jsonb,

                    publish_approved BOOLEAN
                    NOT NULL DEFAULT FALSE,

                    publish_approved_at TIMESTAMPTZ,

                    publish_approval_source TEXT,

                    last_error TEXT,

                    metadata JSONB
                    NOT NULL DEFAULT '{}'::jsonb,

                    started_at TIMESTAMPTZ,

                    completed_at TIMESTAMPTZ,

                    created_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW(),

                    updated_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW()
                );
                """
            )


            # Existing table upgrades.
            cur.execute(
                """
                ALTER TABLE kemo_projects

                ADD COLUMN IF NOT EXISTS
                last_screenshot_file_id TEXT;
                """
            )


            cur.execute(
                """
                ALTER TABLE kemo_projects

                ADD COLUMN IF NOT EXISTS
                last_screenshot_at TIMESTAMPTZ;
                """
            )


            cur.execute(
                """
                ALTER TABLE kemo_projects

                ADD COLUMN IF NOT EXISTS
                quality_score INTEGER;
                """
            )


            cur.execute(
                """
                ALTER TABLE kemo_projects

                ADD COLUMN IF NOT EXISTS
                qa_report JSONB
                NOT NULL DEFAULT '{}'::jsonb;
                """
            )


            cur.execute(
                """
                ALTER TABLE kemo_projects

                ADD COLUMN IF NOT EXISTS
                publish_approved BOOLEAN
                NOT NULL DEFAULT FALSE;
                """
            )


            cur.execute(
                """
                ALTER TABLE kemo_projects

                ADD COLUMN IF NOT EXISTS
                publish_approved_at TIMESTAMPTZ;
                """
            )


            cur.execute(
                """
                ALTER TABLE kemo_projects

                ADD COLUMN IF NOT EXISTS
                publish_approval_source TEXT;
                """
            )


            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_kemo_projects_user_updated

                ON kemo_projects (
                    user_id,
                    updated_at DESC
                );
                """
            )


            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_kemo_projects_status

                ON kemo_projects (
                    status,
                    updated_at DESC
                );
                """
            )


            # =================================================
            # PROJECT EVENTS
            # =================================================

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS
                kemo_project_events (

                    id BIGSERIAL PRIMARY KEY,

                    project_id UUID
                    NOT NULL
                    REFERENCES kemo_projects(id)
                    ON DELETE CASCADE,

                    event_type TEXT NOT NULL,

                    stage TEXT
                    NOT NULL DEFAULT '',

                    message TEXT NOT NULL,

                    metadata JSONB
                    NOT NULL DEFAULT '{}'::jsonb,

                    created_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW()
                );
                """
            )


            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_kemo_project_events_project

                ON kemo_project_events (
                    project_id,
                    created_at DESC
                );
                """
            )


            # =================================================
            # PROJECT JOB QUEUE
            # =================================================

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS
                kemo_project_jobs (

                    id UUID PRIMARY KEY,

                    project_id UUID
                    NOT NULL
                    REFERENCES kemo_projects(id)
                    ON DELETE CASCADE,

                    job_type TEXT NOT NULL,

                    payload JSONB
                    NOT NULL DEFAULT '{}'::jsonb,

                    priority INTEGER
                    NOT NULL DEFAULT 100,

                    status TEXT
                    NOT NULL DEFAULT 'pending',

                    worker_id TEXT,

                    attempts INTEGER
                    NOT NULL DEFAULT 0,

                    max_attempts INTEGER
                    NOT NULL DEFAULT 3,

                    locked_at TIMESTAMPTZ,

                    started_at TIMESTAMPTZ,

                    completed_at TIMESTAMPTZ,

                    last_error TEXT,

                    result JSONB
                    NOT NULL DEFAULT '{}'::jsonb,

                    created_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW(),

                    updated_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW()
                );
                """
            )


            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_kemo_project_jobs_queue

                ON kemo_project_jobs (
                    status,
                    priority DESC,
                    created_at ASC
                );
                """
            )


            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_kemo_project_jobs_project

                ON kemo_project_jobs (
                    project_id,
                    created_at DESC
                );
                """
            )


            # =================================================
            # WORKERS
            # =================================================

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS
                kemo_project_workers (

                    worker_id TEXT PRIMARY KEY,

                    computer TEXT
                    NOT NULL DEFAULT '',

                    status TEXT
                    NOT NULL DEFAULT 'online',

                    current_project_id UUID,

                    current_job_id UUID,

                    current_task TEXT
                    NOT NULL DEFAULT '',

                    capabilities JSONB
                    NOT NULL DEFAULT '[]'::jsonb,

                    metadata JSONB
                    NOT NULL DEFAULT '{}'::jsonb,

                    last_seen_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW(),

                    created_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW(),

                    updated_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW()
                );
                """
            )


            # =================================================
            # PROJECT LESSONS
            #
            # Future:
            # design preferences / corrections / feedback.
            # =================================================

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS
                kemo_project_lessons (

                    id BIGSERIAL PRIMARY KEY,

                    user_id BIGINT NOT NULL,

                    project_id UUID
                    REFERENCES kemo_projects(id)
                    ON DELETE SET NULL,

                    category TEXT
                    NOT NULL DEFAULT 'general',

                    content TEXT NOT NULL,

                    source TEXT
                    NOT NULL DEFAULT 'project',

                    importance INTEGER
                    NOT NULL DEFAULT 3,

                    created_at TIMESTAMPTZ
                    NOT NULL DEFAULT NOW()
                );
                """
            )


            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_kemo_project_lessons_user

                ON kemo_project_lessons (
                    user_id,
                    importance DESC,
                    created_at DESC
                );
                """
            )


    print(
        "✅ Kemo Projects database ready"
    )


# =========================================================
# PROJECT HELPERS
# =========================================================

def get_project(
    project_id,
    require_user=True
):

    project_id = valid_uuid(
        project_id
    )


    if not project_id:

        return None


    with db_connect() as conn:

        with conn.cursor() as cur:

            if (
                require_user
                and
                TELEGRAM_ALLOWED_USER_ID
            ):

                cur.execute(
                    """
                    SELECT *

                    FROM kemo_projects

                    WHERE
                        id = %s
                        AND user_id = %s

                    LIMIT 1;
                    """,
                    (
                        project_id,
                        TELEGRAM_ALLOWED_USER_ID
                    )
                )

            else:

                cur.execute(
                    """
                    SELECT *

                    FROM kemo_projects

                    WHERE id = %s

                    LIMIT 1;
                    """,
                    (
                        project_id,
                    )
                )


            return cur.fetchone()


def add_project_event(
    project_id,
    event_type,
    message,
    stage="",
    metadata=None
):

    project_id = valid_uuid(
        project_id
    )


    if not project_id:

        return


    with db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO kemo_project_events (
                    project_id,
                    event_type,
                    stage,
                    message,
                    metadata
                )

                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s::jsonb
                );
                """,
                (
                    project_id,

                    clean_text(
                        event_type,
                        100
                    ),

                    clean_text(
                        stage,
                        100
                    ),

                    clean_text(
                        message,
                        5000
                    ),

                    json.dumps(
                        metadata or {},
                        ensure_ascii=False
                    )
                )
            )


def is_deploy_job(
    job_type
):

    value = clean_text(
        job_type,
        200
    ).lower()


    markers = [
        "deploy",
        "publish",
        "production",
        "go_live",
        "go-live",
        "نشر",
    ]


    return any(
        marker in value
        for marker in markers
    )


# =========================================================
# TELEGRAM PHOTO
# =========================================================

def telegram_send_photo_bytes(
    chat_id,
    image_bytes,
    caption="",
    mime_type="image/jpeg"
):

    if not TELEGRAM_BOT_TOKEN:

        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN missing"
        )


    if not image_bytes:

        raise RuntimeError(
            "Screenshot is empty"
        )


    if (
        len(
            image_bytes
        )
        >
        MAX_SCREENSHOT_BYTES
    ):

        raise RuntimeError(
            "Screenshot is too large"
        )


    boundary = (
        "----KemoBoundary"
        +
        uuid.uuid4().hex
    )


    extension = (
        "png"
        if mime_type
        ==
        "image/png"
        else
        "jpg"
    )


    buffer = io.BytesIO()


    def write_text(
        value
    ):

        buffer.write(
            value.encode(
                "utf-8"
            )
        )


    # chat_id
    write_text(
        f"--{boundary}\r\n"
    )

    write_text(
        (
            'Content-Disposition: form-data; '
            'name="chat_id"\r\n\r\n'
        )
    )

    write_text(
        str(
            chat_id
        )
    )

    write_text(
        "\r\n"
    )


    # caption
    if caption:

        write_text(
            f"--{boundary}\r\n"
        )

        write_text(
            (
                'Content-Disposition: form-data; '
                'name="caption"\r\n\r\n'
            )
        )

        write_text(
            clean_text(
                caption,
                1000
            )
        )

        write_text(
            "\r\n"
        )


    # photo
    write_text(
        f"--{boundary}\r\n"
    )

    write_text(
        (
            'Content-Disposition: form-data; '
            'name="photo"; '
            f'filename="kemo_project.{extension}"'
            "\r\n"
        )
    )

    write_text(
        f"Content-Type: {mime_type}\r\n\r\n"
    )

    buffer.write(
        image_bytes
    )

    write_text(
        "\r\n"
    )

    write_text(
        f"--{boundary}--\r\n"
    )


    body = buffer.getvalue()


    url = (
        "https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/"
        "sendPhoto"
    )


    request = urllib.request.Request(
        url,
        data=body,
        method="POST"
    )


    request.add_header(
        "Content-Type",
        (
            "multipart/form-data; "
            f"boundary={boundary}"
        )
    )


    request.add_header(
        "Content-Length",
        str(
            len(
                body
            )
        )
    )


    try:

        with urllib.request.urlopen(
            request,
            timeout=60
        ) as response:

            result = json.loads(
                response
                .read()
                .decode(
                    "utf-8"
                )
            )


    except urllib.error.HTTPError as error:

        raw = error.read().decode(
            "utf-8",
            errors="replace"
        )

        raise RuntimeError(
            (
                "Telegram screenshot error: "
                +
                raw[:1500]
            )
        )


    if not result.get(
        "ok"
    ):

        raise RuntimeError(
            (
                "Telegram screenshot failed: "
                +
                str(
                    result
                )[:1500]
            )
        )


    photos = (
        result
        .get(
            "result",
            {}
        )
        .get(
            "photo",
            []
        )
        or []
    )


    file_id = None


    if photos:

        file_id = photos[-1].get(
            "file_id"
        )


    return {
        "ok":
            True,

        "fileId":
            file_id,

        "messageId":
            (
                result
                .get(
                    "result",
                    {}
                )
                .get(
                    "message_id"
                )
            )
    }


# =========================================================
# CREATE PROJECT
# =========================================================

def create_project(
    payload
):

    user_id = resolve_user_id(
        payload.get(
            "userId"
        )
    )


    name = clean_text(
        payload.get(
            "name"
        ),
        300
    )


    brief = clean_text(
        payload.get(
            "brief"
        ),
        30000
    )


    project_type = clean_text(
        payload.get(
            "projectType"
        )
        or
        "website",
        100
    )


    metadata = payload.get(
        "metadata"
    )


    if not isinstance(
        metadata,
        dict
    ):

        metadata = {}


    if not name:

        raise RuntimeError(
            "Project name required"
        )


    project_id = create_uuid()

    job_id = create_uuid()


    with db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO kemo_projects (
                    id,
                    user_id,
                    project_type,
                    name,
                    brief,
                    status,
                    stage,
                    progress,
                    current_task,
                    metadata
                )

                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    'queued',
                    'intake',
                    0,
                    'Waiting for Kemo Project Worker',
                    %s::jsonb
                );
                """,
                (
                    project_id,
                    user_id,
                    project_type,
                    name,
                    brief,
                    json.dumps(
                        metadata,
                        ensure_ascii=False
                    )
                )
            )


            cur.execute(
                """
                INSERT INTO kemo_project_jobs (
                    id,
                    project_id,
                    job_type,
                    payload,
                    priority,
                    status
                )

                VALUES (
                    %s,
                    %s,
                    'project_initialize',
                    %s::jsonb,
                    100,
                    'pending'
                );
                """,
                (
                    job_id,
                    project_id,

                    json.dumps(
                        {
                            "projectId":
                                project_id,

                            "userId":
                                user_id,

                            "projectType":
                                project_type,

                            "name":
                                name,

                            "brief":
                                brief,

                            "metadata":
                                metadata
                        },
                        ensure_ascii=False
                    )
                )
            )


    add_project_event(
        project_id,
        "project_created",
        (
            "Project created: "
            +
            name
        ),
        stage="intake",
        metadata={
            "jobId":
                job_id
        }
    )


    print(
        (
            "📁 Project created | "
            +
            project_id
            +
            " | "
            +
            name
        )
    )


    return {
        "ok":
            True,

        "projectId":
            project_id,

        "jobId":
            job_id,

        "status":
            "queued",

        "stage":
            "intake",

        "progress":
            0
    }


# =========================================================
# LIST PROJECTS
# =========================================================

def list_projects(
    user_id
):

    user_id = resolve_user_id(
        user_id
    )


    with db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT *

                FROM kemo_projects

                WHERE user_id = %s

                ORDER BY
                    updated_at DESC

                LIMIT 100;
                """,
                (
                    user_id,
                )
            )


            return {
                "ok":
                    True,

                "projects":
                    cur.fetchall()
            }


# =========================================================
# PROJECT DETAILS
# =========================================================

def project_details(
    project_id
):

    project = get_project(
        project_id
    )


    if not project:

        raise RuntimeError(
            "Project not found"
        )


    return {
        "ok":
            True,

        "project":
            project
    }


# =========================================================
# PROJECT EVENTS
# =========================================================

def project_events(
    project_id
):

    project = get_project(
        project_id
    )


    if not project:

        raise RuntimeError(
            "Project not found"
        )


    with db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT *

                FROM kemo_project_events

                WHERE project_id = %s

                ORDER BY
                    created_at DESC

                LIMIT 200;
                """,
                (
                    project[
                        "id"
                    ],
                )
            )


            return {
                "ok":
                    True,

                "events":
                    cur.fetchall()
            }


# =========================================================
# PROJECT REPORT / PROOF
# =========================================================

def project_report(
    project_id
):

    project = get_project(
        project_id
    )


    if not project:

        raise RuntimeError(
            "Project not found"
        )


    with db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    event_type,
                    stage,
                    message,
                    metadata,
                    created_at

                FROM kemo_project_events

                WHERE project_id = %s

                ORDER BY
                    created_at DESC

                LIMIT 40;
                """,
                (
                    project[
                        "id"
                    ],
                )
            )


            events = cur.fetchall()


            cur.execute(
                """
                SELECT
                    id,
                    job_type,
                    status,
                    worker_id,
                    attempts,
                    max_attempts,
                    started_at,
                    completed_at,
                    last_error,
                    updated_at

                FROM kemo_project_jobs

                WHERE project_id = %s

                ORDER BY
                    created_at DESC

                LIMIT 40;
                """,
                (
                    project[
                        "id"
                    ],
                )
            )


            jobs = cur.fetchall()


            worker = None


            if project.get(
                "worker_id"
            ):

                cur.execute(
                    """
                    SELECT *

                    FROM kemo_project_workers

                    WHERE worker_id = %s

                    LIMIT 1;
                    """,
                    (
                        project[
                            "worker_id"
                        ],
                    )
                )


                worker = cur.fetchone()


            cur.execute(
                """
                SELECT
                    id,
                    job_type,
                    worker_id,
                    updated_at

                FROM kemo_project_jobs

                WHERE
                    project_id = %s
                    AND status = 'working'

                ORDER BY
                    updated_at DESC

                LIMIT 1;
                """,
                (
                    project[
                        "id"
                    ],
                )
            )


            active_job = cur.fetchone()


    worker_online = False

    worker_age_seconds = None


    if (
        worker
        and
        worker.get(
            "last_seen_at"
        )
    ):

        try:

            last_seen = worker[
                "last_seen_at"
            ]


            now = datetime.now(
                last_seen.tzinfo
            )


            worker_age_seconds = (
                now
                -
                last_seen
            ).total_seconds()


            worker_online = (
                worker_age_seconds
                <
                WORKER_ONLINE_SECONDS
            )


        except Exception:

            worker_online = False


    activity_fresh = False

    activity_age_seconds = None


    try:

        updated_at = project[
            "updated_at"
        ]


        now = datetime.now(
            updated_at.tzinfo
        )


        activity_age_seconds = (
            now
            -
            updated_at
        ).total_seconds()


        activity_fresh = (
            activity_age_seconds
            <
            PROJECT_ACTIVITY_FRESH_SECONDS
        )


    except Exception:

        activity_fresh = False


    verified_working = bool(
        project.get(
            "status"
        )
        ==
        "working"

        and
        worker_online

        and
        active_job

        and
        activity_fresh
    )


    return {
        "ok":
            True,

        "project":
            project,

        "worker": {
            "online":
                worker_online,

            "ageSeconds":
                worker_age_seconds,

            "info":
                worker
        },

        "activeJob":
            active_job,

        "jobs":
            jobs,

        "recentEvents":
            events,

        "proof": {
            "verifiedWorking":
                verified_working,

            "workerOnline":
                worker_online,

            "activityFresh":
                activity_fresh,

            "activityAgeSeconds":
                activity_age_seconds,

            "lastScreenshotFileId":
                project.get(
                    "last_screenshot_file_id"
                ),

            "lastScreenshotAt":
                project.get(
                    "last_screenshot_at"
                ),

            "previewUrl":
                project.get(
                    "preview_url"
                ),

            "productionUrl":
                project.get(
                    "production_url"
                ),

            "qualityScore":
                project.get(
                    "quality_score"
                ),

            "publishApproved":
                bool(
                    project.get(
                        "publish_approved"
                    )
                )
        }
    }


# =========================================================
# ADD PROJECT JOB
# =========================================================

def add_project_job(
    project_id,
    payload
):

    project = get_project(
        project_id
    )


    if not project:

        raise RuntimeError(
            "Project not found"
        )


    job_type = clean_text(
        payload.get(
            "jobType"
        ),
        150
    )


    if not job_type:

        raise RuntimeError(
            "jobType required"
        )


    if (
        is_deploy_job(
            job_type
        )
        and
        not project.get(
            "publish_approved"
        )
    ):

        raise RuntimeError(
            (
                "Publishing is not approved. "
                "Karim must explicitly approve first."
            )
        )


    job_payload = payload.get(
        "payload"
    )


    if not isinstance(
        job_payload,
        dict
    ):

        job_payload = {}


    priority = clamp(
        safe_int(
            payload.get(
                "priority"
            ),
            100
        ),
        1,
        1000
    )


    max_attempts = clamp(
        safe_int(
            payload.get(
                "maxAttempts"
            ),
            3
        ),
        1,
        10
    )


    job_id = create_uuid()


    with db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO kemo_project_jobs (
                    id,
                    project_id,
                    job_type,
                    payload,
                    priority,
                    max_attempts,
                    status
                )

                VALUES (
                    %s,
                    %s,
                    %s,
                    %s::jsonb,
                    %s,
                    %s,
                    'pending'
                );
                """,
                (
                    job_id,
                    project[
                        "id"
                    ],
                    job_type,

                    json.dumps(
                        job_payload,
                        ensure_ascii=False
                    ),

                    priority,
                    max_attempts
                )
            )


    add_project_event(
        project[
            "id"
        ],
        "job_queued",
        (
            "Queued job: "
            +
            job_type
        ),
        stage=project.get(
            "stage"
        )
        or
        "",
        metadata={
            "jobId":
                job_id,

            "priority":
                priority
        }
    )


    return {
        "ok":
            True,

        "jobId":
            job_id,

        "status":
            "pending"
    }


# =========================================================
# WORKER HEARTBEAT
# =========================================================

def worker_heartbeat(
    payload
):

    worker_id = clean_text(
        payload.get(
            "workerId"
        ),
        200
    )


    if not worker_id:

        raise RuntimeError(
            "workerId required"
        )


    computer = clean_text(
        payload.get(
            "computer"
        ),
        300
    )


    current_project_id = valid_uuid(
        payload.get(
            "currentProjectId"
        )
    )


    current_job_id = valid_uuid(
        payload.get(
            "currentJobId"
        )
    )


    current_task = clean_text(
        payload.get(
            "currentTask"
        ),
        2000
    )


    capabilities = payload.get(
        "capabilities"
    )


    if not isinstance(
        capabilities,
        list
    ):

        capabilities = []


    capabilities = capabilities[
        :100
    ]


    metadata = payload.get(
        "metadata"
    )


    if not isinstance(
        metadata,
        dict
    ):

        metadata = {}


    with db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO kemo_project_workers (
                    worker_id,
                    computer,
                    status,
                    current_project_id,
                    current_job_id,
                    current_task,
                    capabilities,
                    metadata,
                    last_seen_at
                )

                VALUES (
                    %s,
                    %s,
                    'online',
                    %s,
                    %s,
                    %s,
                    %s::jsonb,
                    %s::jsonb,
                    NOW()
                )

                ON CONFLICT (
                    worker_id
                )

                DO UPDATE SET

                    computer =
                        EXCLUDED.computer,

                    status =
                        'online',

                    current_project_id =
                        EXCLUDED.current_project_id,

                    current_job_id =
                        EXCLUDED.current_job_id,

                    current_task =
                        EXCLUDED.current_task,

                    capabilities =
                        EXCLUDED.capabilities,

                    metadata =
                        EXCLUDED.metadata,

                    last_seen_at =
                        NOW(),

                    updated_at =
                        NOW();
                """,
                (
                    worker_id,
                    computer,
                    current_project_id,
                    current_job_id,
                    current_task,

                    json.dumps(
                        capabilities,
                        ensure_ascii=False
                    ),

                    json.dumps(
                        metadata,
                        ensure_ascii=False
                    )
                )
            )


    return {
        "ok":
            True,

        "workerId":
            worker_id,

        "serverTime":
            now_iso()
    }


# =========================================================
# CLAIM NEXT JOB
# =========================================================

def claim_next_project_job(
    payload
):

    worker_id = clean_text(
        payload.get(
            "workerId"
        ),
        200
    )


    if not worker_id:

        raise RuntimeError(
            "workerId required"
        )


    with db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT

                    j.*,

                    p.user_id,

                    p.project_type,

                    p.name
                    AS project_name,

                    p.brief
                    AS project_brief,

                    p.metadata
                    AS project_metadata,

                    p.publish_approved

                FROM kemo_project_jobs j

                JOIN kemo_projects p
                    ON p.id =
                    j.project_id

                WHERE

                    j.status =
                    'pending'

                    AND
                    j.attempts
                    <
                    j.max_attempts

                    AND
                    p.status
                    NOT IN (
                        'completed',
                        'cancelled'
                    )

                ORDER BY

                    j.priority DESC,

                    j.created_at ASC

                FOR UPDATE
                OF j
                SKIP LOCKED

                LIMIT 1;
                """
            )


            job = cur.fetchone()


            if not job:

                return {
                    "ok":
                        True,

                    "job":
                        None
                }


            # Extra server-side deploy safety.
            if (
                is_deploy_job(
                    job[
                        "job_type"
                    ]
                )
                and
                not job.get(
                    "publish_approved"
                )
            ):

                cur.execute(
                    """
                    UPDATE kemo_project_jobs

                    SET
                        status =
                            'blocked',

                        last_error =
                            'Waiting for Karim publishing approval',

                        updated_at =
                            NOW()

                    WHERE id = %s;
                    """,
                    (
                        job[
                            "id"
                        ],
                    )
                )


                return {
                    "ok":
                        True,

                    "job":
                        None
                }


            cur.execute(
                """
                UPDATE kemo_project_jobs

                SET
                    status =
                        'working',

                    worker_id =
                        %s,

                    attempts =
                        attempts + 1,

                    locked_at =
                        NOW(),

                    started_at =
                        COALESCE(
                            started_at,
                            NOW()
                        ),

                    updated_at =
                        NOW()

                WHERE id = %s

                RETURNING *;
                """,
                (
                    worker_id,
                    job[
                        "id"
                    ]
                )
            )


            updated_job = cur.fetchone()


            cur.execute(
                """
                UPDATE kemo_projects

                SET
                    status =
                        'working',

                    worker_id =
                        %s,

                    current_task =
                        %s,

                    started_at =
                        COALESCE(
                            started_at,
                            NOW()
                        ),

                    updated_at =
                        NOW()

                WHERE id = %s;
                """,
                (
                    worker_id,
                    job[
                        "job_type"
                    ],
                    job[
                        "project_id"
                    ]
                )
            )


            cur.execute(
                """
                INSERT INTO kemo_project_events (
                    project_id,
                    event_type,
                    stage,
                    message,
                    metadata
                )

                VALUES (
                    %s,
                    'job_started',
                    '',
                    %s,
                    %s::jsonb
                );
                """,
                (
                    job[
                        "project_id"
                    ],

                    (
                        "Worker started: "
                        +
                        job[
                            "job_type"
                        ]
                    ),

                    json.dumps(
                        {
                            "workerId":
                                worker_id,

                            "jobId":
                                str(
                                    job[
                                        "id"
                                    ]
                                )
                        },
                        ensure_ascii=False
                    )
                )
            )


    output = dict(
        updated_job
    )


    output[
        "userId"
    ] = str(
        job[
            "user_id"
        ]
    )


    output[
        "projectType"
    ] = job[
        "project_type"
    ]


    output[
        "projectName"
    ] = job[
        "project_name"
    ]


    output[
        "projectBrief"
    ] = job[
        "project_brief"
    ]


    output[
        "projectMetadata"
    ] = job[
        "project_metadata"
    ]


    output[
        "publishApproved"
    ] = bool(
        job[
            "publish_approved"
        ]
    )


    print(
        (
            "⚡ Worker claimed job | "
            +
            worker_id
            +
            " | "
            +
            str(
                updated_job[
                    "job_type"
                ]
            )
        )
    )


    return {
        "ok":
            True,

        "job":
            output
    }


# =========================================================
# PROJECT PROGRESS
# =========================================================

def update_project_progress(
    project_id,
    payload
):

    project = get_project(
        project_id
    )


    if not project:

        raise RuntimeError(
            "Project not found"
        )


    progress = project[
        "progress"
    ]


    if (
        payload.get(
            "progress"
        )
        is not None
    ):

        progress = clamp(
            safe_int(
                payload.get(
                    "progress"
                ),
                progress
            ),
            0,
            100
        )


    stage = clean_text(
        payload.get(
            "stage"
        )
        if payload.get(
            "stage"
        )
        is not None
        else
        project.get(
            "stage"
        ),
        100
    )


    status = clean_text(
        payload.get(
            "status"
        )
        if payload.get(
            "status"
        )
        is not None
        else
        project.get(
            "status"
        ),
        100
    )


    allowed_statuses = {
        "queued",
        "working",
        "reviewing",
        "review_ready",
        "awaiting_publish_approval",
        "publishing",
        "blocked",
        "completed",
        "cancelled",
    }


    if status not in allowed_statuses:

        status = project[
            "status"
        ]


    current_task = clean_text(
        (
            payload.get(
                "currentTask"
            )
            if payload.get(
                "currentTask"
            )
            is not None
            else project.get(
                "current_task"
            )
        ),
        2000
    )


    last_completed = clean_text(
        (
            payload.get(
                "lastCompleted"
            )
            if payload.get(
                "lastCompleted"
            )
            is not None
            else project.get(
                "last_completed"
            )
        ),
        2000
    )


    local_path = clean_text(
        payload.get(
            "localPath"
        ),
        3000
    )


    repo_url = clean_text(
        payload.get(
            "repoUrl"
        ),
        3000
    )


    preview_url = clean_text(
        payload.get(
            "previewUrl"
        ),
        3000
    )


    quality_score = None


    if (
        payload.get(
            "qualityScore"
        )
        is not None
    ):

        quality_score = clamp(
            safe_int(
                payload.get(
                    "qualityScore"
                ),
                0
            ),
            0,
            100
        )


    qa_report = payload.get(
        "qaReport"
    )


    if not isinstance(
        qa_report,
        dict
    ):

        qa_report = None


    metadata = payload.get(
        "metadata"
    )


    if not isinstance(
        metadata,
        dict
    ):

        metadata = None


    with db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE kemo_projects

                SET

                    progress =
                        %s,

                    stage =
                        %s,

                    status =
                        %s,

                    current_task =
                        %s,

                    last_completed =
                        %s,

                    local_path =
                        CASE
                            WHEN %s = ''
                            THEN local_path
                            ELSE %s
                        END,

                    repo_url =
                        CASE
                            WHEN %s = ''
                            THEN repo_url
                            ELSE %s
                        END,

                    preview_url =
                        CASE
                            WHEN %s = ''
                            THEN preview_url
                            ELSE %s
                        END,

                    quality_score =
                        COALESCE(
                            %s,
                            quality_score
                        ),

                    qa_report =
                        CASE
                            WHEN %s::jsonb
                            IS NULL
                            THEN qa_report
                            ELSE %s::jsonb
                        END,

                    metadata =
                        CASE
                            WHEN %s::jsonb
                            IS NULL
                            THEN metadata
                            ELSE
                                metadata
                                ||
                                %s::jsonb
                        END,

                    last_error =
                        NULL,

                    updated_at =
                        NOW()

                WHERE id = %s

                RETURNING *;
                """,
                (
                    progress,
                    stage,
                    status,
                    current_task,
                    last_completed,

                    local_path,
                    local_path,

                    repo_url,
                    repo_url,

                    preview_url,
                    preview_url,

                    quality_score,

                    (
                        json.dumps(
                            qa_report,
                            ensure_ascii=False
                        )
                        if qa_report
                        is not None
                        else None
                    ),

                    (
                        json.dumps(
                            qa_report,
                            ensure_ascii=False
                        )
                        if qa_report
                        is not None
                        else None
                    ),

                    (
                        json.dumps(
                            metadata,
                            ensure_ascii=False
                        )
                        if metadata
                        is not None
                        else None
                    ),

                    (
                        json.dumps(
                            metadata,
                            ensure_ascii=False
                        )
                        if metadata
                        is not None
                        else None
                    ),

                    project[
                        "id"
                    ]
                )
            )


            updated = cur.fetchone()


    message = clean_text(
        payload.get(
            "message"
        ),
        5000
    )


    if not message:

        if current_task:

            message = (
                "Working: "
                +
                current_task
            )

        else:

            message = (
                "Project progress updated"
            )


    add_project_event(
        project[
            "id"
        ],
        "progress",
        message,
        stage=stage,
        metadata={
            "progress":
                progress,

            "currentTask":
                current_task,

            "lastCompleted":
                last_completed,

            "qualityScore":
                quality_score
        }
    )


    print(
        (
            "📈 Project progress | "
            +
            str(
                project[
                    "id"
                ]
            )
            +
            " | "
            +
            str(
                progress
            )
            +
            "%"
            +
            " | "
            +
            stage
        )
    )


    return {
        "ok":
            True,

        "project":
            updated
    }


# =========================================================
# SCREENSHOT PROOF
# =========================================================

def project_screenshot(
    project_id,
    payload
):

    project = get_project(
        project_id
    )


    if not project:

        raise RuntimeError(
            "Project not found"
        )


    raw_base64 = clean_text(
        payload.get(
            "imageBase64"
        ),
        (
            MAX_JSON_BODY_BYTES
            *
            2
        )
    )


    if not raw_base64:

        raise RuntimeError(
            "imageBase64 required"
        )


    # Support data:image/...;base64,...
    if (
        raw_base64.startswith(
            "data:"
        )
        and
        ","
        in raw_base64
    ):

        raw_base64 = raw_base64.split(
            ",",
            1
        )[1]


    try:

        image_bytes = base64.b64decode(
            raw_base64,
            validate=False
        )

    except Exception:

        raise RuntimeError(
            "Invalid screenshot base64"
        )


    if (
        not image_bytes
        or
        len(
            image_bytes
        )
        >
        MAX_SCREENSHOT_BYTES
    ):

        raise RuntimeError(
            "Screenshot size is invalid"
        )


    mime_type = clean_text(
        payload.get(
            "mimeType"
        )
        or
        "image/jpeg",
        100
    )


    if mime_type not in {
        "image/jpeg",
        "image/png",
    }:

        mime_type = "image/jpeg"


    caption = clean_text(
        payload.get(
            "caption"
        ),
        900
    )


    if not caption:

        caption = (
            "🛠️ Kemo Project Update\n"
            +
            project[
                "name"
            ]
            +
            "\n"
            +
            str(
                project[
                    "progress"
                ]
            )
            +
            "% — "
            +
            (
                project.get(
                    "current_task"
                )
                or
                project.get(
                    "stage"
                )
                or
                ""
            )
        )


    telegram_result = (
        telegram_send_photo_bytes(
            project[
                "user_id"
            ],
            image_bytes,
            caption=caption,
            mime_type=mime_type
        )
    )


    file_id = telegram_result.get(
        "fileId"
    )


    with db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE kemo_projects

                SET

                    last_screenshot_file_id =
                        %s,

                    last_screenshot_at =
                        NOW(),

                    updated_at =
                        NOW()

                WHERE id = %s;
                """,
                (
                    file_id,
                    project[
                        "id"
                    ]
                )
            )


    add_project_event(
        project[
            "id"
        ],
        "screenshot",
        "Project screenshot sent to Telegram",
        stage=project.get(
            "stage"
        )
        or
        "",
        metadata={
            "telegramFileId":
                file_id,

            "telegramMessageId":
                telegram_result.get(
                    "messageId"
                )
        }
    )


    print(
        (
            "📸 Project screenshot sent | "
            +
            str(
                project[
                    "id"
                ]
            )
        )
    )


    return {
        "ok":
            True,

        "sentToTelegram":
            True,

        "telegramFileId":
            file_id,

        "telegramMessageId":
            telegram_result.get(
                "messageId"
            )
    }


# =========================================================
# PUBLISH APPROVAL
# =========================================================

def approve_project_publish(
    project_id,
    payload
):

    project = get_project(
        project_id
    )


    if not project:

        raise RuntimeError(
            "Project not found"
        )


    approved = (
        payload.get(
            "approved"
        )
        is True
    )


    if not approved:

        raise RuntimeError(
            (
                "approved=true required. "
                "Publishing approval must be explicit."
            )
        )


    source = clean_text(
        payload.get(
            "source"
        )
        or
        "karim_confirmation",
        200
    )


    with db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE kemo_projects

                SET

                    publish_approved =
                        TRUE,

                    publish_approved_at =
                        NOW(),

                    publish_approval_source =
                        %s,

                    status =
                        CASE
                            WHEN status =
                                'awaiting_publish_approval'
                            THEN
                                'review_ready'
                            ELSE
                                status
                        END,

                    updated_at =
                        NOW()

                WHERE id = %s

                RETURNING *;
                """,
                (
                    source,
                    project[
                        "id"
                    ]
                )
            )


            updated = cur.fetchone()


            # Unblock deploy jobs.
            cur.execute(
                """
                UPDATE kemo_project_jobs

                SET
                    status =
                        'pending',

                    last_error =
                        NULL,

                    updated_at =
                        NOW()

                WHERE
                    project_id = %s

                    AND status =
                        'blocked'

                    AND (
                        LOWER(job_type)
                        LIKE '%%deploy%%'

                        OR

                        LOWER(job_type)
                        LIKE '%%publish%%'

                        OR

                        LOWER(job_type)
                        LIKE '%%production%%'
                    );
                """,
                (
                    project[
                        "id"
                    ],
                )
            )


    add_project_event(
        project[
            "id"
        ],
        "publish_approved",
        "Karim approved publishing",
        stage=project.get(
            "stage"
        )
        or
        "",
        metadata={
            "source":
                source
        }
    )


    return {
        "ok":
            True,

        "publishApproved":
            True,

        "project":
            updated
    }


# =========================================================
# SAVE PROJECT LESSON
# =========================================================

def save_project_lesson(
    project_id,
    payload
):

    project = get_project(
        project_id
    )


    if not project:

        raise RuntimeError(
            "Project not found"
        )


    content = clean_text(
        payload.get(
            "content"
        ),
        6000
    )


    if not content:

        raise RuntimeError(
            "Lesson content required"
        )


    category = clean_text(
        payload.get(
            "category"
        )
        or
        "design_preference",
        100
    )


    source = clean_text(
        payload.get(
            "source"
        )
        or
        "karim_feedback",
        100
    )


    importance = clamp(
        safe_int(
            payload.get(
                "importance"
            ),
            4
        ),
        1,
        5
    )


    with db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO kemo_project_lessons (
                    user_id,
                    project_id,
                    category,
                    content,
                    source,
                    importance
                )

                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )

                RETURNING id;
                """,
                (
                    project[
                        "user_id"
                    ],
                    project[
                        "id"
                    ],
                    category,
                    content,
                    source,
                    importance
                )
            )


            lesson_id = cur.fetchone()[
                "id"
            ]


    add_project_event(
        project[
            "id"
        ],
        "lesson_saved",
        content,
        stage=project.get(
            "stage"
        )
        or
        "",
        metadata={
            "lessonId":
                lesson_id,

            "category":
                category,

            "importance":
                importance
        }
    )


    return {
        "ok":
            True,

        "lessonId":
            lesson_id
    }


# =========================================================
# COMPLETE JOB
# =========================================================

def complete_project_job(
    job_id,
    payload
):

    job_id = valid_uuid(
        job_id
    )


    if not job_id:

        raise RuntimeError(
            "Invalid job id"
        )


    worker_id = clean_text(
        payload.get(
            "workerId"
        ),
        200
    )


    if not worker_id:

        raise RuntimeError(
            "workerId required"
        )


    result_data = payload.get(
        "result"
    )


    if not isinstance(
        result_data,
        dict
    ):

        result_data = {}


    completed_message = clean_text(
        payload.get(
            "completedMessage"
        ),
        2000
    )


    with db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE kemo_project_jobs

                SET

                    status =
                        'completed',

                    result =
                        %s::jsonb,

                    completed_at =
                        NOW(),

                    updated_at =
                        NOW()

                WHERE

                    id = %s

                    AND worker_id =
                        %s

                    AND status =
                        'working'

                RETURNING *;
                """,
                (
                    json.dumps(
                        result_data,
                        ensure_ascii=False
                    ),

                    job_id,
                    worker_id
                )
            )


            job = cur.fetchone()


            if not job:

                raise RuntimeError(
                    "Working job not found"
                )


            if not completed_message:

                completed_message = (
                    "Completed: "
                    +
                    job[
                        "job_type"
                    ]
                )


            cur.execute(
                """
                UPDATE kemo_projects

                SET

                    last_completed =
                        %s,

                    current_task =
                        '',

                    updated_at =
                        NOW()

                WHERE id = %s;
                """,
                (
                    completed_message,
                    job[
                        "project_id"
                    ]
                )
            )


            cur.execute(
                """
                UPDATE kemo_project_workers

                SET
                    current_job_id =
                        NULL,

                    current_task =
                        '',

                    updated_at =
                        NOW()

                WHERE worker_id =
                    %s;
                """,
                (
                    worker_id,
                )
            )


    add_project_event(
        job[
            "project_id"
        ],
        "job_completed",
        completed_message,
        metadata={
            "jobId":
                job_id,

            "workerId":
                worker_id
        }
    )


    print(
        (
            "✅ Project job completed | "
            +
            str(
                job[
                    "job_type"
                ]
            )
        )
    )


    return {
        "ok":
            True,

        "job":
            job
    }


# =========================================================
# FAIL JOB
# =========================================================

def fail_project_job(
    job_id,
    payload
):

    job_id = valid_uuid(
        job_id
    )


    if not job_id:

        raise RuntimeError(
            "Invalid job id"
        )


    worker_id = clean_text(
        payload.get(
            "workerId"
        ),
        200
    )


    error_text = clean_text(
        payload.get(
            "error"
        )
        or
        "Unknown worker error",
        5000
    )


    if not worker_id:

        raise RuntimeError(
            "workerId required"
        )


    with db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT *

                FROM kemo_project_jobs

                WHERE
                    id = %s
                    AND worker_id = %s

                FOR UPDATE;
                """,
                (
                    job_id,
                    worker_id
                )
            )


            job = cur.fetchone()


            if not job:

                raise RuntimeError(
                    "Job not found"
                )


            permanent_failure = (
                int(
                    job[
                        "attempts"
                    ]
                )
                >=
                int(
                    job[
                        "max_attempts"
                    ]
                )
            )


            next_status = (
                "failed"
                if permanent_failure
                else
                "pending"
            )


            cur.execute(
                """
                UPDATE kemo_project_jobs

                SET

                    status =
                        %s,

                    last_error =
                        %s,

                    worker_id =
                        CASE
                            WHEN %s =
                                'pending'
                            THEN NULL
                            ELSE worker_id
                        END,

                    locked_at =
                        CASE
                            WHEN %s =
                                'pending'
                            THEN NULL
                            ELSE locked_at
                        END,

                    updated_at =
                        NOW()

                WHERE id = %s;
                """,
                (
                    next_status,
                    error_text,
                    next_status,
                    next_status,
                    job_id
                )
            )


            if permanent_failure:

                cur.execute(
                    """
                    UPDATE kemo_projects

                    SET

                        status =
                            'blocked',

                        last_error =
                            %s,

                        current_task =
                            '',

                        updated_at =
                            NOW()

                    WHERE id = %s;
                    """,
                    (
                        error_text,
                        job[
                            "project_id"
                        ]
                    )
                )


            else:

                cur.execute(
                    """
                    UPDATE kemo_projects

                    SET

                        last_error =
                            %s,

                        updated_at =
                            NOW()

                    WHERE id = %s;
                    """,
                    (
                        error_text,
                        job[
                            "project_id"
                        ]
                    )
                )


    add_project_event(
        job[
            "project_id"
        ],
        (
            "job_failed"
            if permanent_failure
            else
            "job_retry"
        ),
        error_text,
        metadata={
            "jobId":
                job_id,

            "workerId":
                worker_id,

            "attempts":
                job[
                    "attempts"
                ],

            "maxAttempts":
                job[
                    "max_attempts"
                ]
        }
    )


    return {
        "ok":
            True,

        "permanentFailure":
            permanent_failure,

        "status":
            next_status
    }


# =========================================================
# COMPLETE PROJECT
# =========================================================

def complete_project(
    project_id,
    payload
):

    project = get_project(
        project_id
    )


    if not project:

        raise RuntimeError(
            "Project not found"
        )


    production_url = clean_text(
        payload.get(
            "productionUrl"
        ),
        3000
    )


    preview_url = clean_text(
        payload.get(
            "previewUrl"
        ),
        3000
    )


    message = clean_text(
        payload.get(
            "message"
        )
        or
        "Project completed",
        2000
    )


    quality_score = None


    if (
        payload.get(
            "qualityScore"
        )
        is not None
    ):

        quality_score = clamp(
            safe_int(
                payload.get(
                    "qualityScore"
                ),
                0
            ),
            0,
            100
        )


    qa_report = payload.get(
        "qaReport"
    )


    if not isinstance(
        qa_report,
        dict
    ):

        qa_report = {}


    # Production URL means something was published.
    # Publishing must have Karim's approval.
    if (
        production_url
        and
        not project.get(
            "publish_approved"
        )
    ):

        raise RuntimeError(
            (
                "Cannot store production URL: "
                "publishing was not approved by Karim."
            )
        )


    with db_connect() as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE kemo_projects

                SET

                    status =
                        'completed',

                    stage =
                        'completed',

                    progress =
                        100,

                    current_task =
                        '',

                    last_completed =
                        %s,

                    production_url =
                        CASE
                            WHEN %s = ''
                            THEN production_url
                            ELSE %s
                        END,

                    preview_url =
                        CASE
                            WHEN %s = ''
                            THEN preview_url
                            ELSE %s
                        END,

                    quality_score =
                        COALESCE(
                            %s,
                            quality_score
                        ),

                    qa_report =
                        CASE
                            WHEN %s::jsonb =
                                '{}'::jsonb
                            THEN qa_report
                            ELSE %s::jsonb
                        END,

                    last_error =
                        NULL,

                    completed_at =
                        NOW(),

                    updated_at =
                        NOW()

                WHERE id = %s

                RETURNING *;
                """,
                (
                    message,

                    production_url,
                    production_url,

                    preview_url,
                    preview_url,

                    quality_score,

                    json.dumps(
                        qa_report,
                        ensure_ascii=False
                    ),

                    json.dumps(
                        qa_report,
                        ensure_ascii=False
                    ),

                    project[
                        "id"
                    ]
                )
            )


            updated = cur.fetchone()


    add_project_event(
        project[
            "id"
        ],
        "project_completed",
        message,
        stage="completed",
        metadata={
            "productionUrl":
                production_url,

            "previewUrl":
                preview_url,

            "qualityScore":
                quality_score
        }
    )


    print(
        (
            "🏁 Project completed | "
            +
            str(
                project[
                    "id"
                ]
            )
        )
    )


    return {
        "ok":
            True,

        "project":
            updated
    }


# =========================================================
# RECOVER STUCK PROJECT JOBS
# =========================================================

def recover_stuck_project_jobs():

    try:

        with db_connect() as conn:

            with conn.cursor() as cur:

                # Retry jobs that still have attempts.
                cur.execute(
                    """
                    UPDATE kemo_project_jobs

                    SET

                        status =
                            'pending',

                        worker_id =
                            NULL,

                        locked_at =
                            NULL,

                        last_error =
                            COALESCE(
                                last_error,
                                ''
                            )
                            ||
                            CASE
                                WHEN
                                    last_error
                                    IS NULL
                                    OR
                                    last_error =
                                    ''
                                THEN ''
                                ELSE E'\\n'
                            END
                            ||
                            'Recovered after stale worker',

                        updated_at =
                            NOW()

                    WHERE

                        status =
                            'working'

                        AND
                        locked_at
                        <
                        NOW()
                        -
                        (
                            %s
                            *
                            INTERVAL
                            '1 minute'
                        )

                        AND attempts
                        <
                        max_attempts;
                    """,
                    (
                        PROJECT_JOB_STUCK_MINUTES,
                    )
                )


                recovered = cur.rowcount


                # Permanent failures.
                cur.execute(
                    """
                    UPDATE kemo_project_jobs

                    SET

                        status =
                            'failed',

                        last_error =
                            COALESCE(
                                last_error,
                                'Worker became stale'
                            ),

                        updated_at =
                            NOW()

                    WHERE

                        status =
                            'working'

                        AND
                        locked_at
                        <
                        NOW()
                        -
                        (
                            %s
                            *
                            INTERVAL
                            '1 minute'
                        )

                        AND attempts
                        >=
                        max_attempts;
                    """,
                    (
                        PROJECT_JOB_STUCK_MINUTES,
                    )
                )


                failed = cur.rowcount


        if recovered:

            print(
                (
                    "♻️ Recovered "
                    +
                    str(
                        recovered
                    )
                    +
                    " stale project job(s)"
                )
            )


        if failed:

            print(
                (
                    "❌ Marked "
                    +
                    str(
                        failed
                    )
                    +
                    " project job(s) failed"
                )
            )


    except Exception as error:

        print(
            (
                "⚠️ Project job recovery: "
                +
                str(
                    error
                )
            )
        )


# =========================================================
# PROJECT MAINTENANCE LOOP
# =========================================================

def project_maintenance_loop():

    while True:

        try:

            recover_stuck_project_jobs()

        except Exception as error:

            print(
                (
                    "⚠️ Project maintenance: "
                    +
                    str(
                        error
                    )
                )
            )


        time.sleep(
            PROJECT_MAINTENANCE_SECONDS
        )


# =========================================================
# HEALTH
# =========================================================

def build_health():

    active_workers = 0

    pending_jobs = 0

    active_projects = 0


    try:

        with db_connect() as conn:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT COUNT(*) AS count

                    FROM kemo_project_workers

                    WHERE
                        last_seen_at
                        >
                        NOW()
                        -
                        INTERVAL '30 seconds';
                    """
                )


                active_workers = int(
                    cur.fetchone()[
                        "count"
                    ]
                )


                cur.execute(
                    """
                    SELECT COUNT(*) AS count

                    FROM kemo_project_jobs

                    WHERE status =
                        'pending';
                    """
                )


                pending_jobs = int(
                    cur.fetchone()[
                        "count"
                    ]
                )


                cur.execute(
                    """
                    SELECT COUNT(*) AS count

                    FROM kemo_projects

                    WHERE status
                    IN (
                        'queued',
                        'working',
                        'reviewing',
                        'review_ready',
                        'awaiting_publish_approval',
                        'publishing',
                        'blocked'
                    );
                    """
                )


                active_projects = int(
                    cur.fetchone()[
                        "count"
                    ]
                )


    except Exception:

        pass


    scheduler_alive = bool(
        SCHEDULER_THREAD
        and
        SCHEDULER_THREAD.is_alive()
    )


    return {
        "ok":
            True,

        "service":
            "kemo-scheduler",

        "version":
            VERSION,

        "mode":
            "scheduler-plus-project-manager",

        "existingScheduler":
            {
                "alive":
                    scheduler_alive,

                "reminders":
                    True,

                "marketHunter":
                    True
            },

        "projects":
            {
                "enabled":
                    True,

                "realProgressTracking":
                    True,

                "workerHeartbeat":
                    True,

                "verifiedWorkingProof":
                    True,

                "timeline":
                    True,

                "telegramScreenshots":
                    True,

                "previewTracking":
                    True,

                "productionUrlTracking":
                    True,

                "qaTracking":
                    True,

                "publishApprovalRequired":
                    True,

                "activeWorkers":
                    active_workers,

                "pendingJobs":
                    pending_jobs,

                "activeProjects":
                    active_projects
            },

        "startedAt":
            PROJECT_SERVER_STARTED_AT,

        "serverTime":
            now_iso()
    }


# =========================================================
# HTTP HANDLER
# =========================================================

class KemoProjectsHandler(
    BaseHTTPRequestHandler
):

    server_version = (
        "KemoProjects/"
        +
        VERSION
    )


    def log_message(
        self,
        format,
        *args
    ):

        # Keep Railway logs clean.
        return


    # =====================================================
    # RESPONSE
    # =====================================================

    def send_json(
        self,
        status_code,
        payload
    ):

        body = json.dumps(
            payload,
            ensure_ascii=False,
            default=json_default
        ).encode(
            "utf-8"
        )


        self.send_response(
            status_code
        )


        self.send_header(
            "Content-Type",
            (
                "application/json; "
                "charset=utf-8"
            )
        )


        self.send_header(
            "Content-Length",
            str(
                len(
                    body
                )
            )
        )


        self.send_header(
            "Cache-Control",
            "no-store"
        )


        self.send_header(
            "X-Content-Type-Options",
            "nosniff"
        )


        self.end_headers()


        self.wfile.write(
            body
        )


    # =====================================================
    # AUTH
    # =====================================================

    def authenticated(
        self
    ):

        supplied = self.headers.get(
            "X-Kemo-Projects-Key",
            ""
        )


        return safe_secret_equal(
            supplied,
            KEMO_PROJECTS_KEY
        )


    def require_auth(
        self
    ):

        if not KEMO_PROJECTS_KEY:

            self.send_json(
                503,
                {
                    "ok":
                        False,

                    "error":
                        (
                            "KEMO_PROJECTS_KEY "
                            "is not configured"
                        )
                }
            )

            return False


        if not self.authenticated():

            self.send_json(
                401,
                {
                    "ok":
                        False,

                    "error":
                        "Unauthorized"
                }
            )

            return False


        return True


    # =====================================================
    # BODY
    # =====================================================

    def read_json(
        self
    ):

        raw_length = self.headers.get(
            "Content-Length",
            "0"
        )


        try:

            length = int(
                raw_length
            )

        except Exception:

            length = 0


        if length < 0:

            length = 0


        if (
            length
            >
            MAX_JSON_BODY_BYTES
        ):

            raise RuntimeError(
                "Request body too large"
            )


        raw = (
            self.rfile.read(
                length
            )
            if length
            else b"{}"
        )


        if not raw:

            return {}


        try:

            result = json.loads(
                raw.decode(
                    "utf-8"
                )
            )


        except Exception:

            raise RuntimeError(
                "Invalid JSON body"
            )


        if not isinstance(
            result,
            dict
        ):

            raise RuntimeError(
                "JSON object required"
            )


        return result


    # =====================================================
    # URL
    # =====================================================

    def parsed_url(
        self
    ):

        return urllib.parse.urlparse(
            self.path
        )


    # =====================================================
    # GET
    # =====================================================

    def do_GET(
        self
    ):

        parsed = self.parsed_url()

        path = parsed.path.rstrip(
            "/"
        )


        if not path:

            path = "/"


        # ---------------------------------------------
        # ROOT
        # ---------------------------------------------

        if path == "/":

            return self.send_json(
                200,
                {
                    "ok":
                        True,

                    "service":
                        "Kemo Scheduler + Projects",

                    "version":
                        VERSION
                }
            )


        # ---------------------------------------------
        # PUBLIC HEALTH
        # ---------------------------------------------

        if path in {
            "/api/health",
            "/health",
        }:

            return self.send_json(
                200,
                build_health()
            )


        if not self.require_auth():

            return


        try:

            # =========================================
            # LIST PROJECTS
            # =========================================

            if path == "/api/projects":

                query = urllib.parse.parse_qs(
                    parsed.query
                )


                user_id = (
                    query.get(
                        "userId",
                        [
                            TELEGRAM_ALLOWED_USER_ID
                        ]
                    )[0]
                )


                return self.send_json(
                    200,
                    list_projects(
                        user_id
                    )
                )


            # =========================================
            # REPORT
            # =========================================

            match = re.fullmatch(
                (
                    r"/api/projects/"
                    r"([0-9a-fA-F\-]+)/"
                    r"report"
                ),
                path
            )


            if match:

                return self.send_json(
                    200,
                    project_report(
                        match.group(
                            1
                        )
                    )
                )


            # =========================================
            # EVENTS
            # =========================================

            match = re.fullmatch(
                (
                    r"/api/projects/"
                    r"([0-9a-fA-F\-]+)/"
                    r"events"
                ),
                path
            )


            if match:

                return self.send_json(
                    200,
                    project_events(
                        match.group(
                            1
                        )
                    )
                )


            # =========================================
            # DETAILS
            # =========================================

            match = re.fullmatch(
                (
                    r"/api/projects/"
                    r"([0-9a-fA-F\-]+)"
                ),
                path
            )


            if match:

                return self.send_json(
                    200,
                    project_details(
                        match.group(
                            1
                        )
                    )
                )


            return self.send_json(
                404,
                {
                    "ok":
                        False,

                    "error":
                        "Not found"
                }
            )


        except Exception as error:

            return self.send_json(
                400,
                {
                    "ok":
                        False,

                    "error":
                        str(
                            error
                        )
                }
            )


    # =====================================================
    # POST
    # =====================================================

    def do_POST(
        self
    ):

        if not self.require_auth():

            return


        parsed = self.parsed_url()

        path = parsed.path.rstrip(
            "/"
        )


        try:

            body = self.read_json()


            # =========================================
            # CREATE PROJECT
            # =========================================

            if path == "/api/projects":

                return self.send_json(
                    200,
                    create_project(
                        body
                    )
                )


            # =========================================
            # WORKER HEARTBEAT
            # =========================================

            if (
                path
                ==
                "/api/worker/heartbeat"
            ):

                return self.send_json(
                    200,
                    worker_heartbeat(
                        body
                    )
                )


            # =========================================
            # WORKER NEXT JOB
            # =========================================

            if (
                path
                ==
                "/api/worker/next-job"
            ):

                return self.send_json(
                    200,
                    claim_next_project_job(
                        body
                    )
                )


            # =========================================
            # ADD JOB
            # =========================================

            match = re.fullmatch(
                (
                    r"/api/projects/"
                    r"([0-9a-fA-F\-]+)/"
                    r"jobs"
                ),
                path
            )


            if match:

                return self.send_json(
                    200,
                    add_project_job(
                        match.group(
                            1
                        ),
                        body
                    )
                )


            # =========================================
            # PROGRESS
            # =========================================

            match = re.fullmatch(
                (
                    r"/api/projects/"
                    r"([0-9a-fA-F\-]+)/"
                    r"progress"
                ),
                path
            )


            if match:

                return self.send_json(
                    200,
                    update_project_progress(
                        match.group(
                            1
                        ),
                        body
                    )
                )


            # =========================================
            # SCREENSHOT
            # =========================================

            match = re.fullmatch(
                (
                    r"/api/projects/"
                    r"([0-9a-fA-F\-]+)/"
                    r"screenshot"
                ),
                path
            )


            if match:

                return self.send_json(
                    200,
                    project_screenshot(
                        match.group(
                            1
                        ),
                        body
                    )
                )


            # =========================================
            # PUBLISH APPROVAL
            # =========================================

            match = re.fullmatch(
                (
                    r"/api/projects/"
                    r"([0-9a-fA-F\-]+)/"
                    r"approve-publish"
                ),
                path
            )


            if match:

                return self.send_json(
                    200,
                    approve_project_publish(
                        match.group(
                            1
                        ),
                        body
                    )
                )


            # =========================================
            # PROJECT LESSON
            # =========================================

            match = re.fullmatch(
                (
                    r"/api/projects/"
                    r"([0-9a-fA-F\-]+)/"
                    r"lesson"
                ),
                path
            )


            if match:

                return self.send_json(
                    200,
                    save_project_lesson(
                        match.group(
                            1
                        ),
                        body
                    )
                )


            # =========================================
            # COMPLETE PROJECT
            # =========================================

            match = re.fullmatch(
                (
                    r"/api/projects/"
                    r"([0-9a-fA-F\-]+)/"
                    r"complete"
                ),
                path
            )


            if match:

                return self.send_json(
                    200,
                    complete_project(
                        match.group(
                            1
                        ),
                        body
                    )
                )


            # =========================================
            # COMPLETE JOB
            # =========================================

            match = re.fullmatch(
                (
                    r"/api/jobs/"
                    r"([0-9a-fA-F\-]+)/"
                    r"complete"
                ),
                path
            )


            if match:

                return self.send_json(
                    200,
                    complete_project_job(
                        match.group(
                            1
                        ),
                        body
                    )
                )


            # =========================================
            # FAIL JOB
            # =========================================

            match = re.fullmatch(
                (
                    r"/api/jobs/"
                    r"([0-9a-fA-F\-]+)/"
                    r"fail"
                ),
                path
            )


            if match:

                return self.send_json(
                    200,
                    fail_project_job(
                        match.group(
                            1
                        ),
                        body
                    )
                )


            return self.send_json(
                404,
                {
                    "ok":
                        False,

                    "error":
                        "Not found"
                }
            )


        except Exception as error:

            print(
                (
                    "⚠️ Projects API: "
                    +
                    str(
                        error
                    )
                )
            )


            return self.send_json(
                400,
                {
                    "ok":
                        False,

                    "error":
                        str(
                            error
                        )
                }
            )


# =========================================================
# EXISTING SCHEDULER THREAD
# =========================================================

def run_existing_scheduler():

    print(
        "🔄 Starting original scheduler.py..."
    )


    try:

        scheduler.main()


    except Exception as error:

        print(
            (
                "❌ Original scheduler crashed: "
                +
                str(
                    error
                )
            )
        )


# =========================================================
# START PROJECT SERVER
# =========================================================

def start_projects_server():

    server = ThreadingHTTPServer(
        (
            "0.0.0.0",
            PORT
        ),
        KemoProjectsHandler
    )


    server.daemon_threads = True


    print("")
    print(
        "========================================"
    )
    print(
        " KEMO SCHEDULER + PROJECTS V5.0"
    )
    print(
        " SAME SERVICE / BACKGROUND PROJECTS"
    )
    print(
        "========================================"
    )
    print("")

    print(
        (
            "✅ Port: "
            +
            str(
                PORT
            )
        )
    )

    print(
        "✅ Original scheduler.py: PRESERVED"
    )

    print(
        "✅ Persistent reminders: PRESERVED"
    )

    print(
        "✅ Market Hunter: PRESERVED"
    )

    print(
        "✅ Project Manager API: READY"
    )

    print(
        "✅ Background worker queue: READY"
    )

    print(
        "✅ Real worker heartbeat: READY"
    )

    print(
        "✅ Verified working proof: READY"
    )

    print(
        "✅ Project progress: READY"
    )

    print(
        "✅ Activity timeline: READY"
    )

    print(
        "✅ Screenshot -> Telegram: READY"
    )

    print(
        "✅ Preview URL tracking: READY"
    )

    print(
        "✅ QA score/report tracking: READY"
    )

    print(
        "✅ Project lessons: READY"
    )

    print(
        "✅ Final production URL tracking: READY"
    )

    print(
        "🛡️ Publishing requires Karim approval"
    )

    print(
        "🔐 Projects API key: configured"
    )

    print(
        "🚫 Fake working status: DISABLED"
    )

    print("")


    server.serve_forever(
        poll_interval=0.25
    )


# =========================================================
# MAIN
# =========================================================

def main():

    global SCHEDULER_THREAD


    # =====================================================
    # REQUIRED ENV
    # =====================================================

    if not DATABASE_URL:

        print(
            "❌ DATABASE_URL missing"
        )

        return


    if not KEMO_PROJECTS_KEY:

        print(
            "❌ KEMO_PROJECTS_KEY missing"
        )

        return


    if not TELEGRAM_BOT_TOKEN:

        print(
            "❌ TELEGRAM_BOT_TOKEN missing"
        )

        return


    if TELEGRAM_ALLOWED_USER_ID <= 0:

        print(
            "❌ TELEGRAM_ALLOWED_USER_ID missing"
        )

        return


    # =====================================================
    # PROJECT DB
    # =====================================================

    try:

        init_projects_database()


    except Exception as error:

        print(
            (
                "❌ Projects database: "
                +
                str(
                    error
                )
            )
        )

        return


    # =====================================================
    # ORIGINAL SCHEDULER
    # =====================================================

    SCHEDULER_THREAD = threading.Thread(
        target=run_existing_scheduler,
        name="kemo-original-scheduler",
        daemon=True
    )


    SCHEDULER_THREAD.start()


    # =====================================================
    # PROJECT MAINTENANCE
    # =====================================================

    maintenance_thread = threading.Thread(
        target=project_maintenance_loop,
        name="kemo-project-maintenance",
        daemon=True
    )


    maintenance_thread.start()


    # =====================================================
    # PROJECT HTTP SERVER
    # =====================================================

    try:

        start_projects_server()


    except KeyboardInterrupt:

        print(
            "🛑 Kemo Scheduler + Projects stopped"
        )


    except Exception as error:

        print(
            (
                "❌ Projects server: "
                +
                str(
                    error
                )
            )
        )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    main()
