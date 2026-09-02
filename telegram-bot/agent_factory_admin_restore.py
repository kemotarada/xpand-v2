# =========================================================
# KEMO ADMIN EXACT PARENT RESTORE V1.1
#
# FLEXIBLE / DETERMINISTIC ROLLBACK
#
# V1.0 assumed every rollback must contain the three
# XPAND Live Call files.
#
# V1.1 determines the REAL file set from the published
# GitHub commit itself.
#
# Therefore it supports:
# - one-file commits
# - two-file commits
# - three-file commits
# - other safe code-file commits
#
# It copies exact bytes from the REAL Parent Commit into a
# new Pending.
#
# NO AI.
# NO CODE GENERATION.
# NO COMMIT.
# NO DEPLOY.
# =========================================================

import re
import uuid

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

import agent_factory_admin as admin
import agent_factory_admin_history as history


VERSION = "1.1"

FALLBACK_ADMIN_HANDLER = None


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


# =========================================================
# REQUEST DETECTION
# =========================================================

RESTORE_MARKERS = [

    "exact parent restore",

    "parent restore",

    "exact restore",

    "جهز rollback",

    "جهز رولباك",

    "انشئ rollback",

    "انشئ رولباك",

    "rollback حقيقي",

    "رولباك حقيقي",

    "استرجع parent",

    "استرجاع parent",
]


def is_exact_restore_request(raw):

    text = normalize_text(
        raw
    )

    ids = history.extract_all_ids(
        raw
    )

    has_marker = any(
        normalize_text(marker)
        in text
        for marker
        in RESTORE_MARKERS
    )

    return bool(
        has_marker
        and
        len(ids) >= 1
    )


def source_pending_id(raw):

    ids = history.extract_all_ids(
        raw
    )

    if not ids:

        return ""

    return ids[0]


# =========================================================
# CURRENT GITHUB BASE SHA
# =========================================================

def current_github_sha(path):

    data = admin.github_get_file(
        path
    )

    sha = clean_text(
        data.get("sha"),
        200
    )

    if not sha:

        raise RuntimeError(
            "Current GitHub SHA missing for "
            +
            path
        )

    return sha


# =========================================================
# REQUESTED FILE FILTER
#
# If the user explicitly writes file paths in the command,
# only those paths are restored, but ONLY if the published
# source commit actually changed them.
#
# If no paths are explicitly requested, all files changed
# by the source commit are restored.
# =========================================================

PATH_PATTERN = re.compile(
    r"\b("
    r"(?:agents|agent_templates|src|app|lib|config|scripts)"
    r"/[A-Za-z0-9_./\-]+"
    r")\b"
)


def requested_paths(raw):

    result = []

    for value in PATH_PATTERN.findall(
        clean_text(
            raw,
            50000
        )
    ):

        path = clean_text(
            value,
            3000
        ).rstrip(
            ".,:;)"
        )

        if (
            path
            and
            path not in result
        ):

            result.append(
                path
            )

    return result


# =========================================================
# SAFE SOURCE FILE SET
# =========================================================

def determine_restore_paths(
    published_commit,
    raw_request
):

    changed_paths = history.commit_changed_paths(
        published_commit
    )

    if not changed_paths:

        raise RuntimeError(
            "Published commit reports no changed files."
        )

    requested = requested_paths(
        raw_request
    )

    if requested:

        invalid = [
            path
            for path
            in requested
            if path not in changed_paths
        ]

        if invalid:

            raise RuntimeError(
                (
                    "Requested restore path was not changed "
                    "by the published commit: "
                    +
                    ", ".join(
                        invalid
                    )
                )
            )

        restore_paths = requested

    else:

        restore_paths = list(
            changed_paths
        )

    if not restore_paths:

        raise RuntimeError(
            "No files selected for restore."
        )

    for path in restore_paths:

        if not admin.safe_code_path(
            path
        ):

            raise RuntimeError(
                "Unsafe code path rejected: "
                +
                path
            )

    return restore_paths


# =========================================================
# CREATE EXACT PARENT RESTORE
# =========================================================

def create_exact_parent_restore(
    owner_id,
    source_prefix,
    raw_request
):

    admin.require_owner(
        owner_id
    )

    # -----------------------------------------------------
    # Load historical source Pending.
    # -----------------------------------------------------

    source = history.pending_by_prefix_any_status(
        owner_id,
        source_prefix
    )

    if not source:

        raise RuntimeError(
            "Published Pending not found: "
            +
            source_prefix
        )

    published_sha = clean_text(
        source.get("commit_sha"),
        200
    )

    if not published_sha:

        raise RuntimeError(
            (
                "Source Pending has no published commit_sha. "
                "Status: "
                +
                clean_text(
                    source.get("status"),
                    200
                )
            )
        )

    # -----------------------------------------------------
    # Resolve real GitHub Parent Commit.
    # -----------------------------------------------------

    parent_sha, published_commit = (
        history.resolve_parent_commit(
            published_sha
        )
    )

    # -----------------------------------------------------
    # Determine exact file set dynamically.
    # -----------------------------------------------------

    restore_paths = determine_restore_paths(
        published_commit,
        raw_request
    )

    # -----------------------------------------------------
    # Build exact changes from Parent Commit bytes.
    # -----------------------------------------------------

    changes = []

    parent_bytes_map = {}

    for path in restore_paths:

        parent_bytes = (
            history.github_file_bytes_at_commit(
                path,
                parent_sha
            )
        )

        try:

            parent_content = parent_bytes.decode(
                "utf-8"
            )

        except Exception as error:

            raise RuntimeError(
                (
                    "Parent file is not valid UTF-8: "
                    +
                    path
                    +
                    " | "
                    +
                    clean_text(
                        error,
                        500
                    )
                )
            )

        base_sha = current_github_sha(
            path
        )

        parent_bytes_map[
            path
        ] = parent_bytes

        changes.append(
            {
                "path":
                    path,

                "content":
                    parent_content,

                "base_sha":
                    base_sha,
            }
        )

    # -----------------------------------------------------
    # Create new database Pending.
    # -----------------------------------------------------

    pending_id = str(
        uuid.uuid4()
    )

    agent_slug = clean_text(
        source.get("agent_slug"),
        200
    ) or "xpand"

    agent_name = clean_text(
        source.get("agent_name"),
        500
    ) or "XPAND Agent"

    branch = clean_text(
        source.get("github_branch"),
        200
    ) or "main"

    summary = (
        "Deterministic Exact Parent Restore of "
        +
        ", ".join(
            restore_paths
        )
        +
        " from Parent Commit "
        +
        parent_sha
        +
        " of published commit "
        +
        published_sha
        +
        ". Files copied exactly from GitHub history. "
        "No AI code generation used."
    )

    database_url = history.admin_database_url()

    with psycopg.connect(
        database_url,
        row_factory=dict_row
    ) as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO
                    kemo_agent_admin_pending_code
                (
                    id,
                    owner_user_id,
                    agent_slug,
                    agent_name,
                    request_text,
                    summary,
                    changes,
                    status,
                    github_branch
                )

                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    'pending_approval',
                    %s
                );
                """,
                (
                    pending_id,
                    int(owner_id),
                    agent_slug,
                    agent_name,
                    clean_text(
                        raw_request,
                        50000
                    ),
                    summary,
                    Jsonb(
                        changes
                    ),
                    branch,
                )
            )

        conn.commit()

    # -----------------------------------------------------
    # Read Pending back from database.
    # -----------------------------------------------------

    saved = history.pending_by_prefix_any_status(
        owner_id,
        pending_id
    )

    if not saved:

        raise RuntimeError(
            (
                "Restore Pending was inserted but "
                "could not be read back."
            )
        )

    saved_status = clean_text(
        saved.get("status"),
        200
    )

    if saved_status != "pending_approval":

        raise RuntimeError(
            (
                "Restore Pending has unexpected status: "
                +
                saved_status
            )
        )

    saved_files = history.pending_file_map(
        saved
    )

    # -----------------------------------------------------
    # Verify exact file set.
    # -----------------------------------------------------

    expected_set = set(
        restore_paths
    )

    saved_set = set(
        saved_files.keys()
    )

    file_set_exact = (
        expected_set
        ==
        saved_set
    )

    # -----------------------------------------------------
    # Byte-for-byte verification.
    # -----------------------------------------------------

    verification = {}

    all_match = True

    for path in restore_paths:

        saved_content = saved_files.get(
            path
        )

        if saved_content is None:

            verification[
                path
            ] = False

            all_match = False

            continue

        saved_bytes = saved_content.encode(
            "utf-8"
        )

        match = (
            saved_bytes
            ==
            parent_bytes_map[
                path
            ]
        )

        verification[
            path
        ] = match

        if not match:

            all_match = False

    verified = bool(
        file_set_exact
        and
        all_match
    )

    # -----------------------------------------------------
    # Fail closed.
    # -----------------------------------------------------

    if not verified:

        lines = [

            "EXACT PARENT RESTORE: FAILED",

            "",

            (
                "PENDING ID: "
                +
                pending_id[:8]
            ),

            (
                "FILE SET EXACT: "
                +
                (
                    "YES"
                    if file_set_exact
                    else
                    "NO"
                )
            ),

            "",
        ]

        for path in restore_paths:

            lines.append(
                (
                    path
                    +
                    " MATCHES PARENT: "
                    +
                    (
                        "YES"
                        if verification.get(
                            path
                        )
                        else
                        "NO"
                    )
                )
            )

        lines.extend(
            [

                "",

                "Do NOT approve this Pending.",

                "",

                "🔒 GitHub Commit: NOT CREATED",

                "🔒 Production: NOT CHANGED",
            ]
        )

        return "\n".join(
            lines
        )

    # -----------------------------------------------------
    # Success response.
    # -----------------------------------------------------

    lines = [

        "✅ EXACT PARENT RESTORE READY",

        "",

        (
            "SOURCE PENDING: "
            +
            clean_text(
                source.get("id"),
                200
            )
        ),

        (
            "PUBLISHED COMMIT: "
            +
            published_sha
        ),

        (
            "PARENT COMMIT: "
            +
            parent_sha
        ),

        "",

        "FILE SET:",
    ]

    for path in restore_paths:

        lines.append(
            "- "
            +
            path
        )

    lines.append(
        ""
    )

    for path in restore_paths:

        lines.append(
            (
                path
                +
                " MATCHES PARENT: YES"
            )
        )

    lines.extend(
        [

            "",

            (
                "🆔 رقم التعديل: "
                +
                pending_id[:8]
            ),

            "",

            "🔒 GitHub Commit: NOT CREATED",

            "🔒 Production: NOT CHANGED",

            "🧠 Gemini/OpenAI used: NO",
        ]
    )

    return "\n".join(
        lines
    )


# =========================================================
# ROUTER
# =========================================================

def admin_handler_with_exact_restore(
    chat_id,
    user_id,
    raw
):

    raw_text = clean_text(
        raw,
        70000
    )

    if is_exact_restore_request(
        raw_text
    ):

        prefix = source_pending_id(
            raw_text
        )

        try:

            print(
                (
                    "♻️ ADMIN ROUTER: EXACT PARENT RESTORE V1.1"
                    +
                    " | source="
                    +
                    prefix
                )
            )

            return create_exact_parent_restore(
                user_id,
                prefix,
                raw_text
            )

        except PermissionError:

            return (
                "Exact Parent Restore متاح لصاحب Kemo فقط."
            )

        except Exception as error:

            print(
                (
                    "❌ EXACT PARENT RESTORE V1.1 | "
                    +
                    clean_text(
                        error,
                        3000
                    )
                )
            )

            return (
                "فشل تجهيز Exact Parent Restore، "
                "وما رح أنشئ Rollback تخميني.\n\n"
                "السبب:\n"
                +
                clean_text(
                    error,
                    2200
                )
                +
                "\n\n"
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

def install_exact_restore():

    global FALLBACK_ADMIN_HANDLER

    # Preserve full existing admin stack.

    history.install_history_verify()

    FALLBACK_ADMIN_HANDLER = (
        admin.handle_agent_admin_command
    )

    admin.handle_agent_admin_command = (
        admin_handler_with_exact_restore
    )

    print("")

    print(
        "================================================"
    )

    print(
        " KEMO ADMIN EXACT PARENT RESTORE V1.1"
    )

    print(
        " FLEXIBLE DETERMINISTIC ROLLBACK"
    )

    print(
        "================================================"
    )

    print("")

    print(
        "✅ Historical Pending loader: ACTIVE"
    )

    print(
        "✅ Real GitHub Parent resolver: ACTIVE"
    )

    print(
        "✅ Dynamic source commit file set: ACTIVE"
    )

    print(
        "✅ Single-file rollback support: ACTIVE"
    )

    print(
        "✅ Multi-file rollback support: ACTIVE"
    )

    print(
        "✅ Exact historical file reader: ACTIVE"
    )

    print(
        "✅ Current base SHA capture: ACTIVE"
    )

    print(
        "✅ Deterministic Pending creation: ACTIVE"
    )

    print(
        "✅ Byte-for-byte readback verification: ACTIVE"
    )

    print(
        "✅ GitHub History Verify: PRESERVED"
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
        "🔒 Exact Restore cannot Commit automatically"
    )

    print(
        "🔒 Exact Restore cannot Deploy automatically"
    )

    print(
        "🧠 Gemini/OpenAI used for rollback: NO"
    )

    print("")


# =========================================================
# MAIN
# =========================================================

def main():

    install_exact_restore()

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
            "👋 Kemo Exact Parent Restore stopped."
        )

    except Exception as error:

        print("")

        print(
            (
                "❌ Kemo Exact Parent Restore startup failed | "
                +
                clean_text(
                    error,
                    3000
                )
            )
        )

        print("")

        raise
