# =========================================================
# KEMO ADMIN GITHUB HISTORY VERIFY V1.1
#
# FIX:
# ---------------------------------------------------------
# V1.0 used pending_change_by_prefix(), which may only return
# currently pending changes.
#
# After a Pending is approved, its status changes and the old
# loader may no longer find it.
#
# V1.1 reads kemo_agent_admin_pending_code directly and can
# load BOTH:
#
# - published/applied Pending
# - still-pending rollback
#
# It then uses the published record's REAL commit_sha,
# resolves the real GitHub parent commit, and compares the
# rollback Pending byte-for-byte with that parent.
#
# READ ONLY:
# - no Pending changes
# - no GitHub writes
# - no Commit
# - no Deploy
# - no Gemini
# - no OpenAI
# =========================================================


import os
import re
import json
import base64
import hashlib
import urllib.request
import urllib.error
import urllib.parse

import psycopg
from psycopg.rows import dict_row

import agent_factory_admin as admin
import agent_factory_admin_review as review


# =========================================================
# VERSION
# =========================================================

VERSION = "1.1"


# =========================================================
# ROUTER
# =========================================================

FALLBACK_ADMIN_HANDLER = None


# =========================================================
# FILES
# =========================================================

XPAND_LIVE_CALL_FILES = [

    "agent_templates/live_call/server.js",

    "agent_templates/live_call/app.js",

    "agent_templates/live_call/package.json",
]


# =========================================================
# HELPERS
# =========================================================

def clean_text(value, max_length=20000):

    return str(
        value
        if value is not None
        else
        ""
    ).replace(
        "\x00",
        ""
    ).strip()[:max_length]


def normalize_text(value):

    text = clean_text(
        value,
        50000
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


def sha256_bytes(data):

    return hashlib.sha256(
        data
    ).hexdigest()


def yes_no(value):

    return (
        "YES"
        if value
        else
        "NO"
    )


# =========================================================
# REQUEST DETECTION
# =========================================================

PENDING_ID_PATTERN = re.compile(
    r"\b("
    r"[0-9a-fA-F]{8}"
    r"(?:-[0-9a-fA-F]{4}"
    r"-[0-9a-fA-F]{4}"
    r"-[0-9a-fA-F]{4}"
    r"-[0-9a-fA-F]{12})?"
    r")\b"
)


HISTORY_MARKERS = [

    "github history",
    "git history",

    "تاريخ github",
    "تاريخ git",

    "تحقق من rollback",
    "تحقق rollback",

    "verify rollback",

    "قارن pending",
    "قارن التعديل",
]


def extract_all_ids(raw):

    result = []

    for value in PENDING_ID_PATTERN.findall(
        clean_text(
            raw,
            30000
        )
    ):

        value = clean_text(
            value,
            100
        )

        if (
            value
            and
            value not in result
        ):

            result.append(
                value
            )

    return result


def is_history_verify_request(raw):

    text = normalize_text(
        raw
    )

    has_marker = any(
        normalize_text(marker)
        in text
        for marker
        in HISTORY_MARKERS
    )

    ids = extract_all_ids(
        raw
    )

    return bool(
        has_marker
        and
        len(ids) >= 2
    )


def extract_history_pair(raw):

    ids = extract_all_ids(
        raw
    )

    if len(ids) < 2:

        raise RuntimeError(
            "لازم ترسل رقم التعديل المنشور ورقم Rollback Pending."
        )

    # Recommended order:
    #
    # 1) published/source Pending
    # 2) rollback Pending

    return {
        "source":
            ids[0],

        "rollback":
            ids[1],
    }


# =========================================================
# ADMIN DATABASE
# =========================================================

def admin_database_url():

    # Main Kemo database normally uses DATABASE_URL.
    #
    # Extra names are accepted as safety/future support.

    candidates = [

        "KEMO_ADMIN_DATABASE_URL",

        "KEMO_DATABASE_URL",

        "DATABASE_URL",
    ]

    for name in candidates:

        value = clean_text(
            os.getenv(
                name,
                ""
            ),
            10000
        )

        if value:

            return value

    raise RuntimeError(
        "Kemo admin database URL is not configured."
    )


# =========================================================
# LOAD ANY PENDING STATUS
#
# IMPORTANT:
#
# Unlike pending_change_by_prefix(), this reads the table
# directly and DOES NOT require status=pending_approval.
#
# Therefore it can read:
#
# - applied
# - failed
# - pending_approval
# - any historical record
#
# =========================================================

def pending_by_prefix_any_status(
    owner_id,
    prefix
):

    prefix = clean_text(
        prefix,
        100
    )

    if not prefix:

        raise RuntimeError(
            "Pending prefix is empty."
        )

    database_url = admin_database_url()

    query = """
        SELECT
            id,
            owner_user_id,
            agent_slug,
            agent_name,
            request_text,
            summary,
            changes,
            status,
            github_branch,
            created_at,
            updated_at,
            applied_at,
            commit_sha,
            last_error

        FROM
            kemo_agent_admin_pending_code

        WHERE
            owner_user_id = %s

            AND

            id LIKE %s

        ORDER BY
            created_at DESC

        LIMIT 3;
    """

    with psycopg.connect(
        database_url,
        row_factory=dict_row
    ) as conn:

        with conn.cursor() as cur:

            cur.execute(
                query,
                (
                    int(owner_id),
                    prefix + "%",
                )
            )

            rows = cur.fetchall()

    if not rows:

        return None

    if len(rows) > 1:

        exact = [

            row

            for row in rows

            if clean_text(
                row.get("id"),
                200
            ).lower()
            ==
            prefix.lower()
        ]

        if len(exact) == 1:

            return dict(
                exact[0]
            )

        raise RuntimeError(
            (
                "Pending prefix is ambiguous: "
                +
                prefix
            )
        )

    return dict(
        rows[0]
    )


# =========================================================
# LOAD RECORDS
# =========================================================

def load_source_record(
    owner_id,
    prefix
):

    pending = pending_by_prefix_any_status(
        owner_id,
        prefix
    )

    if not pending:

        raise RuntimeError(
            (
                "Published Pending not found in history: "
                +
                prefix
            )
        )

    commit_sha = clean_text(
        pending.get(
            "commit_sha"
        ),
        200
    )

    if not commit_sha:

        raise RuntimeError(
            (
                "Pending "
                +
                prefix
                +
                " exists but has no commit_sha. "
                "Its status is: "
                +
                clean_text(
                    pending.get(
                        "status"
                    ),
                    200
                )
            )
        )

    return pending


def load_rollback_record(
    owner_id,
    prefix
):

    pending = pending_by_prefix_any_status(
        owner_id,
        prefix
    )

    if not pending:

        raise RuntimeError(
            (
                "Rollback Pending not found: "
                +
                prefix
            )
        )

    return pending


# =========================================================
# PENDING CHANGES
# =========================================================

def pending_file_map(
    pending
):

    changes = review.normalize_pending_changes(
        pending.get(
            "changes"
        )
    )

    result = {}

    for item in changes:

        path = clean_text(
            item.get(
                "path"
            ),
            3000
        )

        if not path:

            continue

        result[path] = str(
            item.get(
                "content"
            )
            or
            ""
        )

    return result


# =========================================================
# GITHUB CONFIG
# =========================================================

def normalize_repo_name(value):

    repo = clean_text(
        value,
        5000
    ).replace(
        "\\",
        "/"
    )

    if not repo:

        return ""

    if repo.startswith(
        "git@github.com:"
    ):

        repo = repo.split(
            ":",
            1
        )[1]

    prefixes = [

        "https://github.com/",

        "http://github.com/",

        "https://api.github.com/repos/",
    ]

    for prefix in prefixes:

        if repo.startswith(
            prefix
        ):

            repo = repo[
                len(prefix):
            ]

    repo = repo.strip(
        "/"
    )

    if repo.endswith(
        ".git"
    ):

        repo = repo[:-4]

    pieces = [

        piece

        for piece in repo.split(
            "/"
        )

        if piece
    ]

    if len(pieces) < 2:

        return ""

    return (
        pieces[0]
        +
        "/"
        +
        pieces[1]
    )


def github_repository():

    for env_name in [

        "GITHUB_REPOSITORY",

        "KEMO_GITHUB_REPOSITORY",

        "KEMO_GITHUB_REPO",

        "GITHUB_REPO",
    ]:

        value = normalize_repo_name(
            os.getenv(
                env_name,
                ""
            )
        )

        if value:

            return value

    # Current repository fallback.

    return (
        "kemotarada/"
        "kemo-telegram-bot"
    )


def github_token():

    for env_name in [

        "GITHUB_TOKEN",

        "GH_TOKEN",

        "GITHUB_PAT",

        "GITHUB_API_TOKEN",

        "KEMO_GITHUB_TOKEN",

        "KEMO_GITHUB_PAT",

        "KEMO_ADMIN_GITHUB_TOKEN",
    ]:

        value = clean_text(
            os.getenv(
                env_name,
                ""
            ),
            10000
        )

        if value:

            return value

    return ""


# =========================================================
# GITHUB API
# =========================================================

def github_api_get(
    path,
    query=None
):

    url = (
        "https://api.github.com"
        +
        path
    )

    if query:

        url += (
            "?"
            +
            urllib.parse.urlencode(
                query
            )
        )

    headers = {

        "Accept":
            "application/vnd.github+json",

        "X-GitHub-Api-Version":
            "2022-11-28",

        "User-Agent":
            (
                "Kemo-History-Verify/"
                +
                VERSION
            ),
    }

    token = github_token()

    if token:

        headers[
            "Authorization"
        ] = (
            "Bearer "
            +
            token
        )

    request = urllib.request.Request(
        url,
        method="GET",
        headers=headers
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=45
        ) as response:

            raw = response.read()

    except urllib.error.HTTPError as error:

        body = error.read().decode(
            "utf-8",
            errors="replace"
        )

        message = ""

        try:

            parsed = json.loads(
                body
            )

            message = clean_text(
                parsed.get(
                    "message"
                ),
                1000
            )

        except Exception:

            message = clean_text(
                body,
                1000
            )

        raise RuntimeError(
            (
                "GitHub HTTP "
                +
                str(error.code)
                +
                (
                    " | "
                    +
                    message
                    if message
                    else
                    ""
                )
            )
        )

    try:

        return json.loads(
            raw.decode(
                "utf-8"
            )
        )

    except Exception as error:

        raise RuntimeError(
            (
                "GitHub returned invalid JSON: "
                +
                clean_text(
                    error,
                    1000
                )
            )
        )


def github_commit(
    commit_sha
):

    repo = github_repository()

    sha = urllib.parse.quote(
        clean_text(
            commit_sha,
            200
        ),
        safe=""
    )

    return github_api_get(
        (
            "/repos/"
            +
            repo
            +
            "/commits/"
            +
            sha
        )
    )


def github_file_bytes_at_commit(
    path,
    commit_sha
):

    repo = github_repository()

    safe_path = urllib.parse.quote(
        clean_text(
            path,
            3000
        ),
        safe="/"
    )

    data = github_api_get(

        (
            "/repos/"
            +
            repo
            +
            "/contents/"
            +
            safe_path
        ),

        query={
            "ref":
                clean_text(
                    commit_sha,
                    200
                )
        }
    )

    if not isinstance(
        data,
        dict
    ):

        raise RuntimeError(
            (
                "Invalid GitHub file response for "
                +
                path
            )
        )

    if data.get(
        "type"
    ) != "file":

        raise RuntimeError(
            (
                "GitHub path is not a file: "
                +
                path
            )
        )

    encoding = clean_text(
        data.get(
            "encoding"
        ),
        100
    ).lower()

    content = data.get(
        "content"
    )

    if (
        encoding == "base64"
        and
        isinstance(
            content,
            str
        )
    ):

        return base64.b64decode(
            content
        )

    raise RuntimeError(
        (
            "Unsupported GitHub encoding for "
            +
            path
            +
            ": "
            +
            encoding
        )
    )


# =========================================================
# PARENT COMMIT
# =========================================================

def resolve_parent_commit(
    published_sha
):

    commit = github_commit(
        published_sha
    )

    parents = (
        commit.get(
            "parents"
        )
        or
        []
    )

    if not parents:

        raise RuntimeError(
            "Published commit has no parent."
        )

    parent_sha = clean_text(
        parents[0].get(
            "sha"
        ),
        200
    )

    if not parent_sha:

        raise RuntimeError(
            "Parent commit SHA is missing."
        )

    return (
        parent_sha,
        commit
    )


# =========================================================
# COMMIT FILES
# =========================================================

def commit_changed_paths(
    commit
):

    result = []

    for item in (
        commit.get(
            "files"
        )
        or
        []
    ):

        if not isinstance(
            item,
            dict
        ):

            continue

        name = clean_text(
            item.get(
                "filename"
            ),
            3000
        )

        if (
            name
            and
            name not in result
        ):

            result.append(
                name
            )

    return result


# =========================================================
# EXACT VERIFY
# =========================================================

def verify_rollback(
    owner_id,
    source_prefix,
    rollback_prefix
):

    source = load_source_record(
        owner_id,
        source_prefix
    )

    rollback = load_rollback_record(
        owner_id,
        rollback_prefix
    )

    published_sha = clean_text(
        source.get(
            "commit_sha"
        ),
        200
    )

    parent_sha, commit = (
        resolve_parent_commit(
            published_sha
        )
    )

    rollback_files = pending_file_map(
        rollback
    )

    expected_paths = set(
        XPAND_LIVE_CALL_FILES
    )

    rollback_paths = set(
        rollback_files.keys()
    )

    file_set_exact = (
        rollback_paths
        ==
        expected_paths
    )

    changed_paths = set(
        commit_changed_paths(
            commit
        )
    )

    source_touched_expected = (
        expected_paths.issubset(
            changed_paths
        )
    )

    comparisons = {}

    all_match = True

    for path in XPAND_LIVE_CALL_FILES:

        rollback_text = rollback_files.get(
            path
        )

        if rollback_text is None:

            comparisons[path] = {
                "match":
                    False,

                "error":
                    "missing from rollback Pending",
            }

            all_match = False

            continue

        try:

            parent_bytes = github_file_bytes_at_commit(
                path,
                parent_sha
            )

        except Exception as error:

            comparisons[path] = {
                "match":
                    False,

                "error":
                    clean_text(
                        error,
                        1000
                    ),
            }

            all_match = False

            continue

        rollback_bytes = rollback_text.encode(
            "utf-8"
        )

        match = (
            rollback_bytes
            ==
            parent_bytes
        )

        comparisons[path] = {

            "match":
                match,

            "parent_sha256":
                sha256_bytes(
                    parent_bytes
                ),

            "rollback_sha256":
                sha256_bytes(
                    rollback_bytes
                ),

            "parent_size":
                len(
                    parent_bytes
                ),

            "rollback_size":
                len(
                    rollback_bytes
                ),
        }

        if not match:

            all_match = False

    rollback_status = clean_text(
        rollback.get(
            "status"
        ),
        200
    )

    rollback_still_pending = (
        rollback_status
        in {
            "pending_approval",
            "pending",
        }
    )

    verified = bool(

        all_match

        and

        file_set_exact

        and

        source_touched_expected

        and

        rollback_still_pending
    )

    return {

        "source_id":
            clean_text(
                source.get(
                    "id"
                ),
                200
            ),

        "source_status":
            clean_text(
                source.get(
                    "status"
                ),
                200
            ),

        "rollback_id":
            clean_text(
                rollback.get(
                    "id"
                ),
                200
            ),

        "rollback_status":
            rollback_status,

        "published_sha":
            published_sha,

        "parent_sha":
            parent_sha,

        "source_touched_expected":
            source_touched_expected,

        "file_set_exact":
            file_set_exact,

        "comparisons":
            comparisons,

        "all_match":
            all_match,

        "verified":
            verified,
    }


# =========================================================
# FORMAT RESULT
# =========================================================

def format_result(
    result
):

    comparisons = result[
        "comparisons"
    ]

    server = comparisons.get(
        "agent_templates/live_call/server.js",
        {}
    )

    app = comparisons.get(
        "agent_templates/live_call/app.js",
        {}
    )

    package = comparisons.get(
        "agent_templates/live_call/package.json",
        {}
    )

    lines = [

        (
            "GITHUB HISTORY VERIFY: "
            +
            (
                "PASS"
                if result["verified"]
                else
                "FAIL"
            )
        ),

        "",

        (
            "SOURCE PENDING: "
            +
            result[
                "source_id"
            ]
        ),

        (
            "SOURCE STATUS: "
            +
            result[
                "source_status"
            ]
        ),

        (
            "ROLLBACK PENDING: "
            +
            result[
                "rollback_id"
            ]
        ),

        (
            "ROLLBACK STATUS: "
            +
            result[
                "rollback_status"
            ]
        ),

        "",

        (
            "PUBLISHED COMMIT SHA: "
            +
            result[
                "published_sha"
            ]
        ),

        (
            "PARENT COMMIT SHA: "
            +
            result[
                "parent_sha"
            ]
        ),

        "",

        (
            "SOURCE COMMIT TOUCHED EXPECTED FILES: "
            +
            yes_no(
                result[
                    "source_touched_expected"
                ]
            )
        ),

        (
            "ROLLBACK FILE SET EXACT: "
            +
            yes_no(
                result[
                    "file_set_exact"
                ]
            )
        ),

        "",

        (
            "server.js MATCHES PARENT: "
            +
            yes_no(
                server.get(
                    "match"
                )
            )
        ),

        (
            "app.js MATCHES PARENT: "
            +
            yes_no(
                app.get(
                    "match"
                )
            )
        ),

        (
            "package.json MATCHES PARENT: "
            +
            yes_no(
                package.get(
                    "match"
                )
            )
        ),

        "",

        (
            "ROLLBACK VERIFIED: "
            +
            yes_no(
                result[
                    "verified"
                ]
            )
        ),

        "",

        "DETAILS:",
    ]

    if result[
        "verified"
    ]:

        lines.append(
            "- Rollback matches the real Parent Commit byte-for-byte."
        )

    else:

        if not result[
            "source_touched_expected"
        ]:

            lines.append(
                "- Published commit did not touch all three expected Live Call files."
            )

        if not result[
            "file_set_exact"
        ]:

            lines.append(
                "- Rollback Pending does not contain exactly the expected three files."
            )

        for path, data in comparisons.items():

            if data.get(
                "match"
            ):

                continue

            error = clean_text(
                data.get(
                    "error"
                ),
                1000
            )

            if error:

                lines.append(
                    (
                        "- "
                        +
                        path
                        +
                        ": "
                        +
                        error
                    )
                )

            else:

                lines.append(
                    (
                        "- "
                        +
                        path
                        +
                        ": content differs from Parent Commit."
                    )
                )

    lines.extend(
        [

            "",

            "🔎 GitHub History: READ-ONLY",

            "🔒 Pending content: NOT CHANGED",

            "🔒 Commit: NOT CREATED",

            "🔒 Deploy: NOT TRIGGERED",

            "🧠 Gemini/OpenAI used: NO",
        ]
    )

    return "\n".join(
        lines
    )


# =========================================================
# HANDLER
# =========================================================

def handle_history_verify(
    user_id,
    raw
):

    admin.require_owner(
        user_id
    )

    pair = extract_history_pair(
        raw
    )

    print(
        (
            "🕘 ADMIN ROUTER: GITHUB HISTORY VERIFY V1.1"
            +
            " | source="
            +
            pair["source"]
            +
            " | rollback="
            +
            pair["rollback"]
        )
    )

    result = verify_rollback(

        user_id,

        pair[
            "source"
        ],

        pair[
            "rollback"
        ]
    )

    print(
        (
            "✅ GITHUB HISTORY VERIFY V1.1"
            +
            " | published="
            +
            result[
                "published_sha"
            ]
            +
            " | parent="
            +
            result[
                "parent_sha"
            ]
            +
            " | verified="
            +
            str(
                result[
                    "verified"
                ]
            ).lower()
        )
    )

    return format_result(
        result
    )


# =========================================================
# ROUTER WRAPPER
# =========================================================

def admin_handler_with_history(
    chat_id,
    user_id,
    raw
):

    raw_text = clean_text(
        raw,
        70000
    )

    if is_history_verify_request(
        raw_text
    ):

        try:

            return handle_history_verify(
                user_id,
                raw_text
            )

        except PermissionError:

            return (
                "فحص GitHub History متاح لصاحب Kemo فقط."
            )

        except Exception as error:

            print(
                (
                    "❌ GITHUB HISTORY VERIFY V1.1 | "
                    +
                    clean_text(
                        error,
                        3000
                    )
                )
            )

            return (
                "فشل التحقق من GitHub History، "
                "وما رح أخمّن النتيجة.\n\n"
                "السبب:\n"
                +
                clean_text(
                    error,
                    2200
                )
                +
                "\n\n"
                "🔒 Pending: NOT CHANGED\n"
                "🔒 Commit: NOT CREATED\n"
                "🔒 Deploy: NOT TRIGGERED"
            )

    return FALLBACK_ADMIN_HANDLER(
        chat_id,
        user_id,
        raw
    )


# =========================================================
# INSTALL
# =========================================================

def install_history_verify():

    global FALLBACK_ADMIN_HANDLER

    # Preserve existing stack.

    review.install_pending_review()

    FALLBACK_ADMIN_HANDLER = (
        admin.handle_agent_admin_command
    )

    admin.handle_agent_admin_command = (
        admin_handler_with_history
    )

    print("")

    print(
        "================================================"
    )

    print(
        " KEMO ADMIN GITHUB HISTORY VERIFY V1.1"
    )

    print(
        " APPLIED + PENDING HISTORY SUPPORT"
    )

    print(
        "================================================"
    )

    print("")

    print(
        "✅ Historical Pending database reader: ACTIVE"
    )

    print(
        "✅ Applied Pending lookup: ACTIVE"
    )

    print(
        "✅ commit_sha lookup: ACTIVE"
    )

    print(
        "✅ GitHub Parent Commit resolver: ACTIVE"
    )

    print(
        "✅ Historical file reader: ACTIVE"
    )

    print(
        "✅ Byte-for-byte comparison: ACTIVE"
    )

    print(
        "✅ Pending Review: PRESERVED"
    )

    print(
        "✅ Repository Inspector: PRESERVED"
    )

    print(
        "✅ Direct Profile Sync: PRESERVED"
    )

    print(
        "✅ Code Admin: PRESERVED"
    )

    print(
        "🔒 History Verify is READ ONLY"
    )

    print(
        "🧠 Gemini/OpenAI used: NO"
    )

    print("")


# =========================================================
# MAIN
# =========================================================

def main():

    install_history_verify()

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
            "👋 Kemo GitHub History Verify stopped."
        )

    except Exception as error:

        print("")

        print(
            (
                "❌ Kemo GitHub History Verify startup failed | "
                +
                clean_text(
                    error,
                    3000
                )
            )
        )

        print("")

        raise
