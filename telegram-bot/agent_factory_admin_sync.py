# =========================================================
# KEMO ADMIN DIRECT PROFILE SYNC V1.0
#
# PURPOSE
# ---------------------------------------------------------
# Adds a DIRECT database profile-sync command above the
# existing Kemo Agent Admin stack.
#
# This command DOES NOT use:
# - Gemini
# - OpenAI
# - GitHub code generation
# - Pending changes
#
# Flow:
#
# Kemo permanent profile
#        |
#        v
# kemo_agent_admin_profiles
#        |
#        v
# agent-specific database
#        |
#        v
# agent_runtime_admin_profile
#        |
#        v
# verification SELECT
#
# Existing stack preserved:
#
# agent_factory_admin.py
# agent_factory_admin_resilient.py
# agent_factory_admin_focus.py
#
# =========================================================


import re

import agent_factory_admin as admin
import agent_factory_admin_focus as focus


# =========================================================
# VERSION
# =========================================================

VERSION = "1.0"


# =========================================================
# SAVE ORIGINAL ADMIN ROUTER
# =========================================================

ORIGINAL_ADMIN_HANDLER = (
    admin.handle_agent_admin_command
)


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
# DIRECT SYNC INTENT
# =========================================================

SYNC_MARKERS = [

    "مزامنه",
    "مزامنة",

    "زامن",
    "زامِن",

    "اعد مزامنه",
    "اعد مزامنة",

    "أعد مزامنة",
    "أعد مزامنه",

    "sync profile",
    "profile sync",
    "resync profile",
    "sync the profile",
]


PROFILE_MARKERS = [

    "بروفايل",
    "البروفايل",

    "profile",

    "agent_runtime_admin_profile",

    "kemo_agent_admin_profiles",

    "system prompt",
    "system_prompt",

    "السيستم برومت",
    "السستم برومت",
]


def is_direct_profile_sync_request(
    raw
):

    text = normalize_text(
        raw
    )


    has_sync = any(
        normalize_text(
            marker
        )
        in
        text
        for marker
        in SYNC_MARKERS
    )


    has_profile = any(
        normalize_text(
            marker
        )
        in
        text
        for marker
        in PROFILE_MARKERS
    )


    return bool(
        has_sync
        and
        has_profile
    )


# =========================================================
# JSON NORMALIZER
# =========================================================

def normalize_json_value(
    value,
    default
):

    if value is None:

        return default


    return value


# =========================================================
# VERIFY TARGET DATABASE RECORD
# =========================================================

def verify_agent_runtime_profile(
    slug
):

    slug = clean_text(
        slug,
        100
    ).lower()


    database_url = (
        admin.agent_database_url(
            slug
        )
    )


    if not database_url:

        raise RuntimeError(
            (
                "No agent database URL found for "
                +
                slug
                +
                "."
            )
        )


    with admin.db_connect(
        database_url
    ) as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    agent_id,
                    system_prompt,
                    voice_profile,
                    learning_notes,
                    version,
                    updated_at

                FROM
                    agent_runtime_admin_profile

                WHERE
                    agent_id = %s

                LIMIT 1;
                """,
                (
                    slug,
                )
            )


            row = cur.fetchone()


            if not row:

                return {

                    "found":
                        False,

                    "agent_id":
                        slug,

                    "system_prompt":
                        "",

                    "voice_profile":
                        {},

                    "learning_notes":
                        [],

                    "version":
                        None,
                }


            return {

                "found":
                    True,

                "agent_id":
                    clean_text(
                        row[0],
                        100
                    ),

                "system_prompt":
                    str(
                        row[1]
                        or
                        ""
                    ),

                "voice_profile":
                    normalize_json_value(
                        row[2],
                        {}
                    ),

                "learning_notes":
                    normalize_json_value(
                        row[3],
                        []
                    ),

                "version":
                    int(
                        row[4]
                        or
                        0
                    ),

                "updated_at":
                    row[5],
            }


# =========================================================
# COMPARE SOURCE AND TARGET
# =========================================================

def profiles_match(
    source,
    target
):

    if not source:

        return False


    if not target:

        return False


    if not target.get(
        "found"
    ):

        return False


    source_prompt = str(
        source.get(
            "system_prompt"
        )
        or
        ""
    )


    target_prompt = str(
        target.get(
            "system_prompt"
        )
        or
        ""
    )


    source_voice = (
        source.get(
            "voice_profile"
        )
        or
        {}
    )


    target_voice = (
        target.get(
            "voice_profile"
        )
        or
        {}
    )


    source_notes = (
        source.get(
            "learning_notes"
        )
        or
        []
    )


    target_notes = (
        target.get(
            "learning_notes"
        )
        or
        []
    )


    source_version = int(
        source.get(
            "version"
        )
        or
        0
    )


    target_version = int(
        target.get(
            "version"
        )
        or
        0
    )


    return bool(

        source_prompt
        ==
        target_prompt

        and

        source_voice
        ==
        target_voice

        and

        source_notes
        ==
        target_notes

        and

        source_version
        ==
        target_version
    )


# =========================================================
# DIRECT PROFILE SYNC
# =========================================================

def direct_profile_sync(
    user_id,
    resolved
):

    # -----------------------------------------------------
    # OWNER ONLY
    # -----------------------------------------------------

    admin.require_owner(
        user_id
    )


    profile_info = (
        resolved.get(
            "profile"
        )
        or
        {}
    )


    slug = clean_text(
        profile_info.get(
            "slug"
        )
        or
        "",
        100
    ).lower()


    agent_name = clean_text(
        profile_info.get(
            "name"
        )
        or
        slug,
        300
    )


    if not slug:

        raise RuntimeError(
            "Could not determine target agent."
        )


    # =====================================================
    # READ SOURCE FROM KEMO PERMANENT ADMIN DATABASE
    #
    # IMPORTANT:
    # We DO NOT call ensure_admin_profile().
    #
    # We must NOT create a new profile or change version.
    # =====================================================

    source = admin.get_admin_profile(
        user_id,
        slug
    )


    if not source:

        print(
            (
                "❌ DIRECT PROFILE SYNC | target="
                +
                slug
                +
                " | source_found=false"
            )
        )


        return (
            "PROFILE SYNC: FAILED\n"
            "found=false\n"
            "version=N\n\n"
            "ما لقيت البروفايل الدائم للوكيل داخل "
            "kemo_agent_admin_profiles."
        )


    source_version = int(
        source.get(
            "version"
        )
        or
        0
    )


    print(
        (
            "🔄 DIRECT PROFILE SYNC | target="
            +
            slug
            +
            " | source_version="
            +
            str(
                source_version
            )
        )
    )


    # =====================================================
    # WRITE EXACT SAME PROFILE INTO AGENT DATABASE
    #
    # Existing admin function performs UPSERT into:
    #
    # agent_runtime_admin_profile
    #
    # No version increment.
    # No System Prompt modification.
    # No learning note added.
    # =====================================================

    sync_ok = (
        admin.sync_profile_to_agent_database(
            source
        )
    )


    if not sync_ok:

        print(
            (
                "❌ DIRECT PROFILE SYNC | target="
                +
                slug
                +
                " | write=false"
            )
        )


        return (
            "PROFILE SYNC: FAILED\n"
            "found=false\n"
            "version=N"
        )


    # =====================================================
    # VERIFY WITH A REAL SELECT
    # =====================================================

    target = verify_agent_runtime_profile(
        slug
    )


    found = bool(
        target.get(
            "found"
        )
    )


    target_version = (
        target.get(
            "version"
        )
    )


    matched = profiles_match(
        source,
        target
    )


    print(
        (
            "✅ DIRECT PROFILE VERIFY"
            +
            " | target="
            +
            slug
            +
            " | found="
            +
            str(
                found
            ).lower()
            +
            " | version="
            +
            (
                str(
                    target_version
                )
                if target_version is not None
                else "N"
            )
            +
            " | matched="
            +
            str(
                matched
            ).lower()
        )
    )


    # =====================================================
    # NEVER CLAIM SUCCESS UNLESS SELECT + MATCH SUCCEEDED
    # =====================================================

    if (
        not found
        or
        not matched
    ):

        return (
            agent_name
            +
            " PROFILE SYNC: FAILED\n"
            "found="
            +
            str(
                found
            ).lower()
            +
            "\nversion="
            +
            (
                str(
                    target_version
                )
                if target_version is not None
                else
                "N"
            )
        )


    return (
        agent_name
        +
        " PROFILE SYNC: SUCCESS\n"
        "found=true\n"
        "version="
        +
        str(
            target_version
        )
    )


# =========================================================
# DIRECT SYNC ROUTER
#
# IMPORTANT:
#
# This runs BEFORE the normal:
#
# - CODE router
# - PROFILE update router
# - Gemini
# - OpenAI
#
# =========================================================

def admin_handler_with_direct_sync(
    chat_id,
    user_id,
    raw
):

    raw_text = clean_text(
        raw,
        70000
    )


    if is_direct_profile_sync_request(
        raw_text
    ):

        resolved = (
            admin.call_stack
            .resolve_target_agent(
                raw_text
            )
        )


        if resolved:

            print(
                "🔄 ADMIN ROUTER: DIRECT PROFILE SYNC"
            )


            return direct_profile_sync(
                user_id,
                resolved
            )


    # -----------------------------------------------------
    # EVERYTHING ELSE CONTINUES THROUGH EXISTING ADMIN CORE
    # -----------------------------------------------------

    return ORIGINAL_ADMIN_HANDLER(
        chat_id,
        user_id,
        raw
    )


# =========================================================
# INSTALL
# =========================================================

def install_direct_sync():

    # -----------------------------------------------------
    # Preserve:
    #
    # Focused XPAND runtime context
    # Resilient Gemini/OpenAI fallback
    # Strict JSON
    # GitHub approval gate
    # -----------------------------------------------------

    focus.install_focused_admin()


    # -----------------------------------------------------
    # Add direct DB synchronization above normal routing.
    # -----------------------------------------------------

    admin.handle_agent_admin_command = (
        admin_handler_with_direct_sync
    )


    print("")

    print(
        "================================================"
    )

    print(
        " KEMO ADMIN DIRECT PROFILE SYNC V1.0"
    )

    print(
        " DATABASE -> AGENT DATABASE"
    )

    print(
        "================================================"
    )

    print("")


    print(
        "✅ Direct profile synchronization: ACTIVE"
    )


    print(
        "✅ kemo_agent_admin_profiles source: ACTIVE"
    )


    print(
        "✅ agent_runtime_admin_profile target: ACTIVE"
    )


    print(
        "✅ Real SELECT verification: ACTIVE"
    )


    print(
        "✅ Version-preserving sync: ACTIVE"
    )


    print(
        "✅ System Prompt preserved"
    )


    print(
        "✅ Voice Profile preserved"
    )


    print(
        "✅ Learning notes preserved"
    )


    print(
        "✅ Existing focused runtime: PRESERVED"
    )


    print(
        "✅ Existing resilient AI: PRESERVED"
    )


    print(
        "🔒 Gemini/OpenAI bypassed for direct sync"
    )


    print(
        "🔒 GitHub bypassed for direct sync"
    )


    print(
        "🔒 No version increment"
    )


    print(
        "🔒 No Commit"
    )


    print(
        "🔒 No Deploy"
    )


    print("")


# =========================================================
# MAIN
# =========================================================

def main():

    install_direct_sync()


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
            "👋 Kemo Admin Direct Profile Sync stopped."
        )


    except Exception as error:

        print("")

        print(
            (
                "❌ Kemo Admin Direct Profile Sync failed | "
                +
                clean_text(
                    error,
                    3000
                )
            )
        )

        print("")

        raise
