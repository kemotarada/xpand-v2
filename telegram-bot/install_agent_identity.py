# =========================================================
# XPAND V2 - AGENT IDENTITY INSTALLER
#
# الهدف:
# أخذ Master System Prompt الأصلي من نسخة Kemo
# وتحويل الهوية فقط إلى XPAND بدون تعديل البنية الداخلية.
#
# نحافظ على:
# - الذاكرة
# - الفويس
# - البحث
# - التذكيرات
# - Agent Factory
# - Desktop
# - Call
# - الأدوات
#
# ولا نغيّر:
# - أسماء الجداول
# - أسماء KEMO_* environment variables
# - أسماء modules/functions الداخلية
# =========================================================

import os

import psycopg

import main


# =========================================================
# SETTINGS
# =========================================================

DATABASE_URL = str(
    os.getenv(
        "DATABASE_URL",
        ""
    )
    or
    ""
).strip()


AGENT_NAME = str(
    os.getenv(
        "AGENT_NAME",
        "XPAND"
    )
    or
    "XPAND"
).strip()


AGENT_NAME_AR = str(
    os.getenv(
        "AGENT_NAME_AR",
        "إكسباند"
    )
    or
    "إكسباند"
).strip()


OWNER_NAME = str(
    os.getenv(
        "AGENT_OWNER_NAME",
        "كريم"
    )
    or
    "كريم"
).strip()


# =========================================================
# BUILD PROMPT
# =========================================================

def build_agent_prompt():

    original = str(
        main.MASTER_SYSTEM_PROMPT
        or
        ""
    )

    if not original.strip():

        raise RuntimeError(
            "Original Master System Prompt is empty."
        )


    # =====================================================
    # الهوية فقط.
    #
    # هذا الاستبدال يتم داخل البرومت فقط،
    # وليس داخل الكود أو أسماء المتغيرات والجداول.
    # =====================================================

    replacements = [
        (
            "KEMO",
            AGENT_NAME.upper()
        ),
        (
            "Kemo",
            AGENT_NAME
        ),
        (
            "kemo",
            AGENT_NAME.lower()
        ),
        (
            "كيمو",
            AGENT_NAME_AR
        ),
    ]


    result = original


    for old, new in replacements:

        result = result.replace(
            old,
            new
        )


    # =====================================================
    # طبقة هوية قوية فوق البرومت الأصلي.
    # =====================================================

    identity_header = f"""
==================================================
AGENT IDENTITY — AUTHORITATIVE
==================================================

اسمك الرسمي هو: {AGENT_NAME}
واسمك بالعربية: {AGENT_NAME_AR}

أنت نفس الوكيل في جميع القنوات:

- Telegram Text
- Telegram Voice
- Live Call
- Memory
- Web Search
- Reminders
- Desktop / Browser tools
- Agent Factory capabilities

المستخدم الأساسي هو: {OWNER_NAME}

ممنوع أن تعرّف نفسك باسم Kemo أو كيمو.

أي ظهور لاسم Kemo في أسماء تقنية داخلية أو أسماء جداول
أو متغيرات أو تاريخ النظام لا يغيّر هويتك.

هويتك الوحيدة أمام المستخدم هي:

{AGENT_NAME}

يجب أن تكون الشخصية والذاكرة وطريقة الكلام موحدة
بين النص والفويس والمكالمة.

==================================================
""".strip()


    return (
        identity_header
        +
        "\n\n"
        +
        result
    ).strip()


# =========================================================
# INSTALL
# =========================================================

def install():

    if not DATABASE_URL:

        raise RuntimeError(
            "DATABASE_URL is missing."
        )


    prompt = build_agent_prompt()


    # مهم جداً:
    #
    # نستخدم نفس MASTER_PROMPT_VERSION الموجود بالكود.
    #
    # لأن main.py إذا وجد Version مختلف،
    # سيعيد كتابة Kemo prompt الأصلي عند التشغيل.
    #
    # بهذه الطريقة سيعتبر قاعدة البيانات محدثة
    # ولن يستبدل XPAND prompt عند كل Restart.
    #

    prompt_version = str(
        main.MASTER_PROMPT_VERSION
        or
        ""
    ).strip()


    if not prompt_version:

        raise RuntimeError(
            "MASTER_PROMPT_VERSION is missing."
        )


    with psycopg.connect(
        DATABASE_URL
    ) as conn:

        with conn.cursor() as cur:

            cur.execute(
                """
                INSERT INTO kemo_config
                (
                    config_key,
                    config_value,
                    updated_at
                )
                VALUES
                (
                    'master_system_prompt',
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
                    prompt,
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
                VALUES
                (
                    'master_system_prompt_version',
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
                    prompt_version,
                )
            )


        conn.commit()


    print("")
    print(
        "=============================================="
    )
    print(
        " XPAND V2 IDENTITY INSTALLED"
    )
    print(
        "=============================================="
    )
    print(
        f"✅ Agent Name: {AGENT_NAME}"
    )
    print(
        f"✅ Arabic Name: {AGENT_NAME_AR}"
    )
    print(
        f"✅ Owner: {OWNER_NAME}"
    )
    print(
        "✅ Master Prompt updated"
    )
    print(
        "✅ Same prompt shared with Call"
    )
    print(
        "✅ Text + Voice + Call identity unified"
    )
    print(
        "✅ Internal KEMO_* names preserved safely"
    )
    print(
        "=============================================="
    )
    print("")


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    install()
