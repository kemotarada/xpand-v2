# =========================================================
# KEMO REAL PUBLISH TELEGRAM BRIDGE V1.3
#
# FIXES:
#
# - Explicit Karim approval
# - Real project_publish job
# - Recovery from blocked review state
# - Recovery from blocked publishing state after deploy failure
# - Background production URL monitoring
# - Final real URL -> Telegram
#
# Existing stack preserved:
# - main.py
# - desktop_runner.py
# - projects_runner.py
# - projects_media_runner.py when installed
#
# =========================================================

import time
import threading
import urllib.parse

import projects_runner
import main as kemo


# =========================================================
# OPTIONAL MEDIA LAYER
# =========================================================

MEDIA_AVAILABLE = False
BASE_RUNNER = projects_runner

try:
    import projects_media_runner

    MEDIA_AVAILABLE = True
    BASE_RUNNER = projects_media_runner

except Exception as error:
    print(
        "⚠️ Project media layer: "
        + str(error)
    )


# =========================================================
# VERSION
# =========================================================

VERSION = "1.3"


# =========================================================
# PRESERVE EXISTING KEMO
# =========================================================

EXISTING_KEMO_ASK = kemo.ask_kemo


# =========================================================
# SETTINGS
# =========================================================

MONITOR_SECONDS = 600
POLL_SECONDS = 3


# =========================================================
# MONITORS
# =========================================================

MONITOR_LOCK = threading.Lock()
ACTIVE_MONITORS = set()


# =========================================================
# HELPERS
# =========================================================

def clean_text(value, limit=5000):
    return (
        str(
            value
            if value is not None
            else ""
        )
        .replace("\x00", "")
        .strip()[:limit]
    )


def normalize_text(value):
    text = clean_text(
        value,
        5000
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

    return " ".join(
        text.split()
    )


def safe_int(value, fallback=0):
    try:
        return int(
            float(value)
        )

    except Exception:
        return fallback


# =========================================================
# INTENTS
# =========================================================

PUBLISH_PHRASES = [
    "انشر الموقع",
    "انشر المشروع",
    "انشرلي الموقع",
    "انشر لي الموقع",
    "انشرلي المشروع",
    "انشر لي المشروع",

    "ارفع الموقع",
    "ارفع المشروع",

    "خلي الموقع لايف",
    "خلي المشروع لايف",

    "طلع الموقع لايف",
    "اطلع الموقع لايف",

    "انشر النسخه",
    "انشر النسخة",

    "انشر اخر نسخه",
    "انشر آخر نسخة",

    "انشر التعديلات",

    "publish website",
    "publish project",
    "deploy website",
    "deploy project",
    "make website live",
]


STATUS_PHRASES = [
    "وين وصل النشر",
    "شو صار بالنشر",
    "حالة النشر",
    "حاله النشر",

    "وين رابط الموقع",
    "اعطيني رابط الموقع",
    "ابعتلي رابط الموقع",
    "ابعثلي رابط الموقع",
    "رابط الموقع النهائي",
]


def contains_phrase(text, phrases):
    source = normalize_text(text)

    for phrase in phrases:
        if normalize_text(phrase) in source:
            return True

    return False


def is_publish_request(text):
    return contains_phrase(
        text,
        PUBLISH_PHRASES
    )


def is_publish_status_request(text):
    return contains_phrase(
        text,
        STATUS_PHRASES
    )


# =========================================================
# TELEGRAM SEND
# =========================================================

def send_telegram(chat_id, text):
    try:
        kemo.send_message(
            chat_id,
            text
        )

        return True

    except Exception as error:
        print(
            "⚠️ Publish Telegram: "
            + str(error)
        )

        return False


# =========================================================
# REPORT
# =========================================================

def get_report(project_id):
    return projects_runner.get_project_report(
        project_id
    )


def get_project_from_report(report):
    if not isinstance(
        report,
        dict
    ):
        return {}

    project = report.get(
        "project"
    )

    if isinstance(
        project,
        dict
    ):
        return project

    return {}


def get_proof_from_report(report):
    if not isinstance(
        report,
        dict
    ):
        return {}

    proof = report.get(
        "proof"
    )

    if isinstance(
        proof,
        dict
    ):
        return proof

    return {}


def extract_state(report):
    project = get_project_from_report(
        report
    )

    proof = get_proof_from_report(
        report
    )

    url = clean_text(
        project.get("production_url")
        or
        project.get("productionUrl")
        or
        proof.get("productionUrl"),
        3000
    )

    status = clean_text(
        project.get("status"),
        100
    ).lower()

    stage = clean_text(
        project.get("stage"),
        100
    ).lower()

    progress = safe_int(
        project.get("progress"),
        0
    )

    approved = bool(
        project.get("publish_approved")
        or
        project.get("publishApproved")
        or
        proof.get("publishApproved")
    )

    last_error = clean_text(
        project.get("last_error"),
        2000
    )

    return {
        "url": url,
        "status": status,
        "stage": stage,
        "progress": progress,
        "approved": approved,
        "lastError": last_error,
    }


def project_state(project_id):
    try:
        report = get_report(
            project_id
        )

        state = extract_state(
            report
        )

        state["report"] = report

        return state

    except Exception as error:
        return {
            "url": "",
            "status": "",
            "stage": "",
            "progress": 0,
            "approved": False,
            "lastError": str(error),
            "report": {},
        }


# =========================================================
# EXPLICIT APPROVAL
# =========================================================

def approve_publish(project_id):
    encoded = urllib.parse.quote(
        str(project_id),
        safe=""
    )

    response = projects_runner.projects_post(
        (
            "/api/projects/"
            + encoded
            + "/approve-publish"
        ),
        {
            "approved": True,
            "source": "telegram_explicit_publish_command",
        },
        timeout=25
    )

    if (
        not isinstance(response, dict)
        or
        response.get("ok") is False
    ):
        raise RuntimeError(
            "Publish approval failed: "
            + str(response)
        )

    if response.get(
        "publishApproved"
    ) is not True:
        raise RuntimeError(
            "Publish approval was not confirmed"
        )

    return response


# =========================================================
# QUEUE PUBLISH JOB
# =========================================================

def queue_publish_job(
    project_id,
    chat_id,
    user_id,
    request_text
):
    encoded = urllib.parse.quote(
        str(project_id),
        safe=""
    )

    return projects_runner.projects_post(
        (
            "/api/projects/"
            + encoded
            + "/jobs"
        ),
        {
            "jobType": "project_publish",

            "priority": 1000,

            "maxAttempts": 5,

            "payload": {
                "approvedBy": "Karim",
                "explicitApproval": True,
                "approvalSource": "telegram",
                "chatId": chat_id,
                "userId": user_id,
                "request": clean_text(
                    request_text,
                    3000
                ),
            }
        },
        timeout=25
    )


# =========================================================
# READY / RECOVERY CHECK
# =========================================================

def project_can_publish(state):
    status = state.get(
        "status",
        ""
    )

    stage = state.get(
        "stage",
        ""
    )

    progress = state.get(
        "progress",
        0
    )

    # Normal ready states.
    if status in {
        "review_ready",
        "ready",
        "completed",
    }:
        return True

    # =====================================================
    # RECOVERY
    #
    # A website that was already built can become BLOCKED
    # because GitHub publishing failed.
    #
    # In that case the WEBSITE is not broken.
    # Only the deploy failed.
    #
    # We allow Karim to explicitly retry publishing.
    # =====================================================

    if (
        status == "blocked"
        and
        progress >= 90
        and
        stage in {
            "review_ready",
            "qa",
            "completed",
            "publishing",
        }
    ):
        print("")
        print(
            "♻️ BLOCKED PUBLISH RECOVERY"
        )
        print(
            "Status: " + status
        )
        print(
            "Stage: " + stage
        )
        print(
            "Progress: " + str(progress)
        )
        print(
            "✅ Explicit publish retry allowed"
        )
        print("")

        return True

    return False


# =========================================================
# BACKGROUND MONITOR
# =========================================================

def monitor_publish(
    chat_id,
    project_id,
    project_name
):
    key = str(
        project_id
    )

    started = time.monotonic()

    try:
        while (
            time.monotonic()
            -
            started
            <
            MONITOR_SECONDS
        ):
            state = project_state(
                project_id
            )

            url = state.get(
                "url",
                ""
            )

            if url:
                message = (
                    "✅ تم نشر الموقع فعليًا\n\n"
                    +
                    "📁 "
                    +
                    project_name
                    +
                    "\n\n"
                    +
                    "🌐 الرابط النهائي:\n"
                    +
                    url
                )

                send_telegram(
                    chat_id,
                    message
                )

                try:
                    kemo.save_message(
                        chat_id,
                        "assistant",
                        message
                    )

                except Exception:
                    pass

                return

            status = state.get(
                "status",
                ""
            )

            if status in {
                "failed",
                "error",
                "publish_failed",
            }:
                send_telegram(
                    chat_id,
                    (
                        "❌ النشر فشل قبل ما يطلع رابط نهائي.\n"
                        +
                        "الحالة: "
                        +
                        status
                    )
                )

                return

            time.sleep(
                POLL_SECONDS
            )

        send_telegram(
            chat_id,
            (
                "🟡 النشر أخذ وقت أطول من المتوقع، "
                "بس ما رح أعطيك رابط وهمي. "
                "ابعتلي «وين وصل النشر؟» وأنا بفحصه."
            )
        )

    finally:
        with MONITOR_LOCK:
            ACTIVE_MONITORS.discard(
                key
            )


def start_monitor(
    chat_id,
    project_id,
    project_name
):
    key = str(
        project_id
    )

    with MONITOR_LOCK:
        if key in ACTIVE_MONITORS:
            return False

        ACTIVE_MONITORS.add(
            key
        )

    thread = threading.Thread(
        target=monitor_publish,
        args=(
            chat_id,
            project_id,
            project_name,
        ),
        daemon=True
    )

    thread.start()

    return True


# =========================================================
# PUBLISH STATUS
# =========================================================

def handle_status(
    user_id,
    request_text
):
    project = projects_runner.choose_project(
        user_id,
        request_text
    )

    if not project:
        return (
            "ما لقيت مشروع أفحصه."
        )

    project_id = projects_runner.get_project_id(
        project
    )

    project_name = projects_runner.get_project_name(
        project
    )

    state = project_state(
        project_id
    )

    if state.get(
        "url"
    ):
        return (
            "الموقع منشور فعليًا ✅\n\n"
            +
            "📁 "
            +
            project_name
            +
            "\n"
            +
            "🌐 "
            +
            state["url"]
        )

    return (
        "📁 "
        +
        project_name
        +
        "\n"
        +
        "📊 "
        +
        str(
            state.get(
                "progress",
                0
            )
        )
        +
        "%\n"
        +
        "📌 الحالة: "
        +
        (
            state.get("status")
            or
            "غير محددة"
        )
        +
        "\n"
        +
        "🧩 المرحلة: "
        +
        (
            state.get("stage")
            or
            "غير محددة"
        )
    )


# =========================================================
# HANDLE PUBLISH
# =========================================================

def handle_publish(
    chat_id,
    user_id,
    request_text
):
    project = projects_runner.choose_project(
        user_id,
        request_text
    )

    if not project:
        return (
            "ما لقيت مشروع موقع جاهز للنشر."
        )

    project_id = projects_runner.get_project_id(
        project
    )

    project_name = projects_runner.get_project_name(
        project
    )

    if not project_id:
        return (
            "لقيت المشروع، بس Project ID ناقص."
        )

    state = project_state(
        project_id
    )

    if state.get(
        "url"
    ):
        return (
            "الموقع منشور فعليًا ✅\n\n"
            +
            "🌐 "
            +
            state["url"]
        )

    if not project_can_publish(
        state
    ):
        return (
            "المشروع مش جاهز للنشر حاليًا.\n"
            +
            "📌 الحالة: "
            +
            (
                state.get("status")
                or
                "غير محددة"
            )
            +
            "\n"
            +
            "🧩 المرحلة: "
            +
            (
                state.get("stage")
                or
                "غير محددة"
            )
            +
            "\n"
            +
            "📊 "
            +
            str(
                state.get(
                    "progress",
                    0
                )
            )
            +
            "%"
        )

    health = projects_runner.projects_health()

    workers = (
        projects_runner
        .active_workers_from_health(
            health
        )
    )

    if workers <= 0:
        return (
            "المشروع جاهز، بس Publisher مش Online هسّا."
        )

    # Explicit Telegram command from Karim.
    approve_publish(
        project_id
    )

    result = queue_publish_job(
        project_id,
        chat_id,
        user_id,
        request_text
    )

    if (
        not isinstance(result, dict)
        or
        result.get("ok") is False
    ):
        raise RuntimeError(
            "Publish job failed: "
            + str(result)
        )

    job_id = clean_text(
        result.get("jobId"),
        200
    )

    start_monitor(
        chat_id,
        project_id,
        project_name
    )

    return (
        "🚀 سجلت موافقتك على النشر رسميًا ✅\n\n"
        +
        "📁 "
        +
        project_name
        +
        "\n"
        +
        "🟢 Publisher Online\n"
        +
        "📤 أنشأت Publish Job جديد وحقيقي.\n"
        +
        (
            (
                "⚙️ Job: "
                +
                job_id
                +
                "\n"
            )
            if job_id
            else
            ""
        )
        +
        "\nرح أبعتلك الرابط تلقائيًا أول ما يصير Live."
    )


# =========================================================
# MASTER WRAPPER
# =========================================================

def ask_kemo_with_publish(
    chat_id,
    user_id,
    user_message
):
    if is_publish_request(
        user_message
    ):
        try:
            return handle_publish(
                chat_id,
                user_id,
                user_message
            )

        except Exception as error:
            print(
                "❌ Publisher router: "
                + str(error)
            )

            return (
                "صار خلل بالنشر الحقيقي: "
                +
                clean_text(
                    error,
                    1000
                )
            )

    if is_publish_status_request(
        user_message
    ):
        try:
            return handle_status(
                user_id,
                user_message
            )

        except Exception as error:
            return (
                "ما قدرت أفحص حالة النشر: "
                +
                clean_text(
                    error,
                    800
                )
            )

    return EXISTING_KEMO_ASK(
        chat_id,
        user_id,
        user_message
    )


# =========================================================
# INSTALL
# =========================================================

kemo.ask_kemo = ask_kemo_with_publish


# =========================================================
# MAIN
# =========================================================

def main():
    print("")
    print(
        "=========================================="
    )
    print(
        " KEMO REAL PUBLISH TELEGRAM BRIDGE V1.3"
    )
    print(
        " BLOCKED PUBLISHING RECOVERY"
    )
    print(
        "=========================================="
    )
    print("")

    print(
        "✅ Explicit approval"
    )

    print(
        "✅ New real publish jobs"
    )

    print(
        "✅ Blocked review recovery"
    )

    print(
        "✅ Blocked publishing recovery"
    )

    print(
        "✅ Publisher verification"
    )

    print(
        "✅ Background URL monitor"
    )

    print(
        "✅ Real production URL -> Telegram"
    )

    print(
        (
            "✅ Media layer: "
            +
            (
                "ACTIVE"
                if MEDIA_AVAILABLE
                else
                "not installed"
            )
        )
    )

    print("")

    BASE_RUNNER.main()


if __name__ == "__main__":
    main()
