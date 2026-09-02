# =========================================================
# KEMO ADMIN PENDING CODE REVIEW V1.0
#
# PURPOSE
# ---------------------------------------------------------
# Adds READ-ONLY review of an existing Pending Code change
# BEFORE GitHub Commit / Deploy.
#
# Example command:
#
#   كيمو راجع التعديل 42fca252
#
# It will:
#
# - load Pending from PostgreSQL
# - read its full modified files
# - load current GitHub versions
# - compare base SHA against current GitHub SHA
# - validate package.json when present
# - give Pending code + current code to AI reviewer
# - return SAFE TO PUBLISH: YES / NO
#
# It NEVER:
#
# - changes Pending
# - updates database
# - commits
# - deploys
# - modifies GitHub
#
# Existing stack preserved:
#
# agent_factory_admin.py
# agent_factory_admin_resilient.py
# agent_factory_admin_focus.py
# agent_factory_admin_sync.py
# agent_factory_admin_inspect.py
#
# =========================================================


import re
import json

import agent_factory_admin as admin
import agent_factory_admin_inspect as inspect


# =========================================================
# VERSION
# =========================================================

VERSION = "1.0"


# =========================================================
# LIMITS
# =========================================================

MAX_FILE_CHARS = 120000

MAX_TOTAL_CONTEXT_CHARS = 650000

MAX_REVIEW_OUTPUT_CHARS = 30000


# =========================================================
# EXISTING ROUTER
# =========================================================

FALLBACK_ADMIN_HANDLER = None


# =========================================================
# HELPERS
# =========================================================

def clean_text(
    value,
    max_length=20000
):

    return str(
        value
        if value is not None
        else
        ""
    ).replace(
        "\x00",
        ""
    ).strip()[:max_length]


def normalize_text(
    value
):

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
# REVIEW INTENT
# =========================================================

REVIEW_MARKERS = [

    "راجع التعديل",
    "مراجعه التعديل",
    "مراجعة التعديل",

    "راجع pending",
    "راجع ال pending",

    "افحص التعديل المعلق",
    "افحص التعديل المعلّق",

    "review pending",
    "review change",
]


PENDING_ID_PATTERN = re.compile(
    r"\b([0-9a-fA-F]{8}(?:-[0-9a-fA-F-]{20,})?)\b"
)


def extract_pending_prefix(
    raw
):

    match = PENDING_ID_PATTERN.search(
        clean_text(
            raw,
            10000
        )
    )


    if not match:

        return ""


    return clean_text(
        match.group(
            1
        ),
        100
    )


def is_pending_review_request(
    raw
):

    text = normalize_text(
        raw
    )


    has_marker = any(
        normalize_text(
            marker
        )
        in
        text
        for marker
        in REVIEW_MARKERS
    )


    prefix = extract_pending_prefix(
        raw
    )


    return bool(
        has_marker
        and
        prefix
    )


# =========================================================
# PENDING DATA NORMALIZATION
# =========================================================

def normalize_pending_changes(
    raw_changes
):

    changes = raw_changes


    if isinstance(
        changes,
        str
    ):

        try:

            changes = json.loads(
                changes
            )

        except Exception as error:

            raise RuntimeError(
                (
                    "Pending changes JSON is invalid: "
                    +
                    clean_text(
                        error,
                        500
                    )
                )
            )


    if isinstance(
        changes,
        dict
    ):

        # Support possible wrapper shapes.

        if isinstance(
            changes.get(
                "files"
            ),
            list
        ):

            changes = changes[
                "files"
            ]


        elif isinstance(
            changes.get(
                "changes"
            ),
            list
        ):

            changes = changes[
                "changes"
            ]


        else:

            changes = [
                changes
            ]


    if not isinstance(
        changes,
        list
    ):

        raise RuntimeError(
            "Pending changes must be a list."
        )


    normalized = []


    for item in changes:

        if not isinstance(
            item,
            dict
        ):

            continue


        path = clean_text(
            (
                item.get(
                    "path"
                )
                or
                item.get(
                    "file"
                )
                or
                item.get(
                    "filename"
                )
                or
                ""
            ),
            2000
        )


        content = str(
            (
                item.get(
                    "content"
                )
                if item.get(
                    "content"
                )
                is not None
                else
                item.get(
                    "new_content"
                )
                if item.get(
                    "new_content"
                )
                is not None
                else
                ""
            )
        )


        base_sha = clean_text(
            (
                item.get(
                    "base_sha"
                )
                or
                item.get(
                    "sha"
                )
                or
                ""
            ),
            200
        )


        if not path:

            continue


        normalized.append(
            {
                "path":
                    path,

                "content":
                    content,

                "base_sha":
                    base_sha,
            }
        )


    if not normalized:

        raise RuntimeError(
            "Pending contains no readable modified files."
        )


    return normalized


# =========================================================
# LOAD CURRENT GITHUB FILE
# =========================================================

def load_current_github_file(
    path
):

    try:

        data = admin.github_get_file(
            path
        )


        return {
            "exists":
                True,

            "sha":
                clean_text(
                    data.get(
                        "sha"
                    ),
                    200
                ),

            "content":
                str(
                    data.get(
                        "content"
                    )
                    or
                    ""
                ),
        }


    except Exception as error:

        # New files may not exist yet.

        return {
            "exists":
                False,

            "sha":
                "",

            "content":
                "",

            "error":
                clean_text(
                    error,
                    800
                ),
        }


# =========================================================
# STATIC PACKAGE.JSON VALIDATION
# =========================================================

def validate_package_json(
    content
):

    try:

        package = json.loads(
            content
        )


    except Exception as error:

        return {
            "status":
                "FAIL",

            "reason":
                (
                    "Invalid JSON: "
                    +
                    clean_text(
                        error,
                        500
                    )
                ),
        }


    if not isinstance(
        package,
        dict
    ):

        return {
            "status":
                "FAIL",

            "reason":
                "package.json root is not an object.",
        }


    dependencies = (
        package.get(
            "dependencies"
        )
        or
        {}
    )


    if not isinstance(
        dependencies,
        dict
    ):

        return {
            "status":
                "FAIL",

            "reason":
                "dependencies is not an object.",
        }


    return {
        "status":
            "PASS",

        "reason":
            "JSON parsed successfully.",

        "has_ws":
            "ws"
            in
            dependencies,

        "has_express":
            "express"
            in
            dependencies,

        "has_pg":
            "pg"
            in
            dependencies,
    }


# =========================================================
# BUILD REVIEW SNAPSHOT
# =========================================================

def build_pending_review_snapshot(
    pending
):

    changes = normalize_pending_changes(
        pending.get(
            "changes"
        )
    )


    snapshots = []

    stale_files = []

    package_validation = None

    total_chars = 0


    for change in changes:

        path = change[
            "path"
        ]


        pending_content = change[
            "content"
        ]


        base_sha = change[
            "base_sha"
        ]


        current = load_current_github_file(
            path
        )


        current_sha = clean_text(
            current.get(
                "sha"
            ),
            200
        )


        base_matches = None


        if base_sha:

            base_matches = bool(
                current_sha
                and
                current_sha
                ==
                base_sha
            )


            if not base_matches:

                stale_files.append(
                    path
                )


        if path.endswith(
            "/package.json"
        ) or path == "package.json":

            package_validation = (
                validate_package_json(
                    pending_content
                )
            )


        pending_limited = (
            pending_content[
                :MAX_FILE_CHARS
            ]
        )


        current_limited = (
            current.get(
                "content",
                ""
            )[
                :MAX_FILE_CHARS
            ]
        )


        projected = (
            total_chars
            +
            len(
                pending_limited
            )
            +
            len(
                current_limited
            )
        )


        if (
            projected
            >
            MAX_TOTAL_CONTEXT_CHARS
        ):

            raise RuntimeError(
                (
                    "Pending is too large for safe review context. "
                    "Review smaller changes separately."
                )
            )


        total_chars = projected


        snapshots.append(
            {
                "path":
                    path,

                "base_sha":
                    base_sha,

                "current_sha":
                    current_sha,

                "base_matches":
                    base_matches,

                "current_exists":
                    bool(
                        current.get(
                            "exists"
                        )
                    ),

                "pending_content":
                    pending_limited,

                "current_content":
                    current_limited,
            }
        )


    return {
        "changes":
            changes,

        "snapshots":
            snapshots,

        "stale_files":
            stale_files,

        "package_validation":
            package_validation,
    }


# =========================================================
# REVIEW CONTEXT
# =========================================================

def build_review_context(
    pending,
    snapshot
):

    parts = []


    parts.append(
        """
============================================================
PENDING METADATA
============================================================
"""
    )


    parts.append(
        (
            "ID: "
            +
            clean_text(
                pending.get(
                    "id"
                ),
                200
            )
            +
            "\n"
        )
    )


    parts.append(
        (
            "STATUS: "
            +
            clean_text(
                pending.get(
                    "status"
                ),
                200
            )
            +
            "\n"
        )
    )


    parts.append(
        (
            "AGENT: "
            +
            clean_text(
                (
                    pending.get(
                        "agent_slug"
                    )
                    or
                    pending.get(
                        "agent_name"
                    )
                ),
                500
            )
            +
            "\n"
        )
    )


    parts.append(
        (
            "SUMMARY:\n"
            +
            clean_text(
                pending.get(
                    "summary"
                ),
                8000
            )
            +
            "\n\n"
        )
    )


    parts.append(
        (
            "OWNER ORIGINAL REQUEST:\n"
            +
            clean_text(
                pending.get(
                    "request_text"
                ),
                30000
            )
            +
            "\n"
        )
    )


    package_validation = snapshot.get(
        "package_validation"
    )


    if package_validation:

        parts.append(
            (
                "\n"
                "STATIC PACKAGE.JSON VALIDATION:\n"
                +
                json.dumps(
                    package_validation,
                    ensure_ascii=False,
                    indent=2
                )
                +
                "\n"
            )
        )


    stale_files = snapshot.get(
        "stale_files"
    ) or []


    parts.append(
        (
            "\n"
            "BASE SHA STATUS:\n"
            +
            (
                "STALE FILES: "
                +
                ", ".join(
                    stale_files
                )
                if stale_files
                else
                "No detected base SHA conflicts."
            )
            +
            "\n"
        )
    )


    for item in snapshot[
        "snapshots"
    ]:

        path = item[
            "path"
        ]


        parts.append(
            (
                "\n\n"
                "============================================================\n"
                "FILE: "
                +
                path
                +
                "\n"
                "============================================================\n"
                "BASE_SHA: "
                +
                (
                    item[
                        "base_sha"
                    ]
                    or
                    "NONE"
                )
                +
                "\n"
                "CURRENT_SHA: "
                +
                (
                    item[
                        "current_sha"
                    ]
                    or
                    "NONE"
                )
                +
                "\n"
                "BASE_MATCHES_CURRENT: "
                +
                str(
                    item[
                        "base_matches"
                    ]
                )
                +
                "\n"
                "CURRENT_FILE_EXISTS: "
                +
                str(
                    item[
                        "current_exists"
                    ]
                )
                +
                "\n\n"
                "---------------- CURRENT GITHUB VERSION ----------------\n"
                +
                item[
                    "current_content"
                ]
                +
                "\n\n"
                "---------------- PENDING MODIFIED VERSION ----------------\n"
                +
                item[
                    "pending_content"
                ]
                +
                "\n"
            )
        )


    return "".join(
        parts
    )


# =========================================================
# AI REVIEW
# =========================================================

def review_pending_with_ai(
    pending,
    snapshot,
    context
):

    pending_id = clean_text(
        pending.get(
            "id"
        ),
        200
    )


    review_request = """
You are reviewing an EXISTING Kemo Pending Code change.

This is READ-ONLY validation.

You are given:

1. the owner's original request
2. the complete pending modified files
3. current GitHub versions of those files
4. base SHA comparison
5. static package.json validation when applicable

DO NOT:
- modify code
- create a Pending
- commit
- deploy
- assume code works without verifying it from the supplied source

IMPORTANT REVIEW RULES:

- Treat the pending modified versions as the code that would
  be committed if approved.
- Compare them against current GitHub code.
- Detect stale base SHA conflicts.
- Detect syntax/configuration problems visible from source.
- Verify that the pending actually implements the owner's
  original request.
- Detect pseudo-code, placeholders, incomplete functions,
  missing frontend/backend halves, mismatched event names,
  duplicated responses, unsafe secret handling, broken
  WebSocket paths, audio-format mismatches, or likely runtime
  regressions.
- If something cannot be proven from source alone, say so.
- Do not mark PASS just because the summary claims it.
- SAFE TO PUBLISH may be YES only when there are no known
  blocking issues in the supplied code.
- If any blocking item is FAIL, SAFE TO PUBLISH must be NO.

For XPAND Live Call changes, specifically verify:

- package.json validity
- ws dependency
- WebSocket server wiring
- WSS compatibility behind Railway HTTPS
- OpenAI Realtime text-only output
- actual OpenAI event names used by frontend
- Gemini TTS request implementation
- Gemini model and Iapetus voice
- Gemini returned audio MIME / encoding
- browser playback compatibility
- response deduplication
- user interruption
- no simultaneous OpenAI voice
- WebRTC microphone remains active
- GEMINI_API_KEY never reaches browser
- System Prompt / database secrets are not logged
- no dependency on main.py runtime from Node service

Return ONLY this format:

PENDING: <id/prefix>
PENDING STATUS: PASS/FAIL
REQUEST COVERAGE: PASS/FAIL
FILE SET: PASS/FAIL
BASE SHA: PASS/FAIL
PACKAGE JSON: PASS/FAIL/N/A
WEBSOCKET SERVER: PASS/FAIL/N/A
WSS RAILWAY: PASS/FAIL/N/A
OPENAI TEXT ONLY: PASS/FAIL/N/A
OPENAI EVENT HANDLING: PASS/FAIL/N/A
GEMINI TTS REQUEST: PASS/FAIL/N/A
GEMINI AUDIO FORMAT: PASS/FAIL/N/A
BROWSER AUDIO PLAYBACK: PASS/FAIL/N/A
INTERRUPTION: PASS/FAIL/N/A
WEBRTC MICROPHONE PRESERVED: PASS/FAIL/N/A
SECRET SAFETY: PASS/FAIL
SAFE TO PUBLISH: YES/NO
ISSUES:
- ...
- ...

If there are no issues write:
ISSUES:
- NONE
""".strip()


    raw = (
        review_request
        +
        "\n\n"
        "PENDING ID:\n"
        +
        pending_id
    )


    answer = inspect.repository_inspect_ai(
        raw,
        context
    )


    return clean_text(
        answer,
        MAX_REVIEW_OUTPUT_CHARS
    )


# =========================================================
# REVIEW HANDLER
# =========================================================

def handle_pending_review(
    user_id,
    prefix
):

    admin.require_owner(
        user_id
    )


    print(
        (
            "🧪 ADMIN ROUTER: PENDING CODE REVIEW"
            +
            " | prefix="
            +
            prefix
        )
    )


    pending = admin.pending_change_by_prefix(
        user_id,
        prefix
    )


    if not pending:

        return (
            "ما لقيت Pending بهذا الرقم:\n"
            +
            prefix
        )


    status = clean_text(
        pending.get(
            "status"
        ),
        200
    )


    if status not in {
        "pending_approval",
        "pending",
    }:

        return (
            "التعديل موجود، لكنه مش بحالة Pending قابلة للمراجعة.\n\n"
            "status="
            +
            status
        )


    snapshot = build_pending_review_snapshot(
        pending
    )


    context = build_review_context(
        pending,
        snapshot
    )


    answer = review_pending_with_ai(
        pending,
        snapshot,
        context
    )


    stale_files = snapshot.get(
        "stale_files"
    ) or []


    footer = (
        "\n\n"
        "🔎 Pending Review: READ-ONLY\n"
        "🔒 Pending content: NOT CHANGED\n"
        "🔒 GitHub Commit: NOT CREATED\n"
        "🔒 Deploy: NOT TRIGGERED"
    )


    if stale_files:

        footer += (
            "\n⚠️ Base SHA conflict detected: "
            +
            ", ".join(
                stale_files
            )
        )


    return (
        answer
        +
        footer
    )


# =========================================================
# ROUTER WRAPPER
# =========================================================

def admin_handler_with_pending_review(
    chat_id,
    user_id,
    raw
):

    raw_text = clean_text(
        raw,
        70000
    )


    if is_pending_review_request(
        raw_text
    ):

        prefix = extract_pending_prefix(
            raw_text
        )


        try:

            return handle_pending_review(
                user_id,
                prefix
            )


        except PermissionError:

            return (
                "مراجعة تعديلات الوكلاء متاحة لصاحب Kemo فقط."
            )


        except Exception as error:

            print(
                (
                    "❌ PENDING CODE REVIEW | "
                    +
                    clean_text(
                        error,
                        3000
                    )
                )
            )


            return (
                "صار خلل أثناء مراجعة التعديل، "
                "وما رح أخمّن النتيجة.\n\n"
                "السبب:\n"
                +
                clean_text(
                    error,
                    2000
                )
            )


    return FALLBACK_ADMIN_HANDLER(
        chat_id,
        user_id,
        raw
    )


# =========================================================
# INSTALL
# =========================================================

def install_pending_review():

    global FALLBACK_ADMIN_HANDLER


    # -----------------------------------------------------
    # Install all existing layers first:
    #
    # Inspect
    # Sync
    # Focus
    # Resilient AI
    # Code Admin
    # -----------------------------------------------------

    inspect.install_repository_inspect()


    # -----------------------------------------------------
    # Capture full existing router.
    # -----------------------------------------------------

    FALLBACK_ADMIN_HANDLER = (
        admin.handle_agent_admin_command
    )


    # -----------------------------------------------------
    # Add Pending Review above everything else.
    # -----------------------------------------------------

    admin.handle_agent_admin_command = (
        admin_handler_with_pending_review
    )


    print("")

    print(
        "================================================"
    )

    print(
        " KEMO ADMIN PENDING CODE REVIEW V1.0"
    )

    print(
        " PRE-COMMIT READ-ONLY VALIDATION"
    )

    print(
        "================================================"
    )

    print("")


    print(
        "✅ Pending database loader: ACTIVE"
    )


    print(
        "✅ Pending modified-file reader: ACTIVE"
    )


    print(
        "✅ Current GitHub comparison: ACTIVE"
    )


    print(
        "✅ Base SHA conflict detection: ACTIVE"
    )


    print(
        "✅ package.json validation: ACTIVE"
    )


    print(
        "✅ AI code review: ACTIVE"
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
        "✅ XPAND focused runtime: PRESERVED"
    )


    print(
        "🔒 Pending Review cannot modify Pending"
    )


    print(
        "🔒 Pending Review cannot Commit"
    )


    print(
        "🔒 Pending Review cannot Deploy"
    )


    print("")


# =========================================================
# MAIN
# =========================================================

def main():

    install_pending_review()


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
            "👋 Kemo Pending Review stopped."
        )


    except Exception as error:

        print("")

        print(
            (
                "❌ Kemo Pending Review startup failed | "
                +
                clean_text(
                    error,
                    3000
                )
            )
        )

        print("")

        raise
