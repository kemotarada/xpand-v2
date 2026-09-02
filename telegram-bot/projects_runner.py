# =========================================================
# KEMO PROJECT TELEGRAM BRIDGE V1.3
#
# REAL COMMAND EXECUTION + VERIFIED START
#
# Telegram text + voice
#        ↓
# Project Router
#        ↓
# Kemo Projects API
#        ↓
# builder_agent.py on Karim's PC
#
# GUARANTEES:
#
# - main.py untouched
# - desktop_runner.py untouched
# - publishing wrapper remains compatible
#
# - CREATE:
#   Must create a REAL project + REAL job.
#
# - REVISION:
#   Must create a REAL revision job.
#
# - REBUILD FROM ZERO:
#   Must create a NEW project + project_initialize job.
#
# - "STARTED":
#   Kemo may say "بدأ فعليًا" ONLY when:
#
#       worker online
#       +
#       proof.verifiedWorking == True
#       +
#       activeJob.id == expected Job ID
#
# - If not started:
#   Kemo explicitly says it is queued.
#
# - Background verification:
#   Kemo automatically sends confirmation when
#   the SAME JOB really starts.
#
# NO FAKE WORKING.
# NO FAKE START.
# NO FAKE PUBLISHING.
# =========================================================

import os
import re
import json
import time
import threading
import urllib.request
import urllib.error
import urllib.parse

import desktop_runner
import main as kemo


# =========================================================
# VERSION
# =========================================================

VERSION = "1.3"


# =========================================================
# ENV
# =========================================================

KEMO_PROJECTS_URL = (
    os.environ.get(
        "KEMO_PROJECTS_URL",
        ""
    )
    .strip()
    .rstrip("/")
)


KEMO_PROJECTS_KEY = (
    os.environ.get(
        "KEMO_PROJECTS_KEY",
        ""
    )
    .strip()
)


# =========================================================
# SETTINGS
# =========================================================

HTTP_TIMEOUT = 25

MAX_PROJECTS = 30

SCREENSHOT_PRIORITY = 500

REVISION_PRIORITY = 600


# How long Telegram request waits for a real claim.
VERIFY_START_SECONDS = 18

VERIFY_START_POLL_SECONDS = 1


# If not started immediately, monitor in background.
BACKGROUND_VERIFY_SECONDS = 900

BACKGROUND_VERIFY_POLL_SECONDS = 2


# =========================================================
# BACKGROUND MONITORS
# =========================================================

MONITOR_LOCK = threading.Lock()

ACTIVE_MONITORS = set()


# =========================================================
# KEEP EXISTING DESKTOP WRAPPER
# =========================================================

EXISTING_KEMO_ASK = (
    kemo.ask_kemo
)


# =========================================================
# TEXT HELPERS
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


def normalized(
    value
):

    try:

        return kemo.normalize_text(
            value
        )

    except Exception:

        text = (
            str(
                value or ""
            )
            .lower()
        )

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
            r"\s+",
            " ",
            text
        )

        return text.strip()


def contains_any(
    text,
    values
):

    source = normalized(
        text
    )

    for item in values:

        if normalized(
            item
        ) in source:

            return True

    return False


def safe_int(
    value,
    fallback=0
):

    try:

        return int(
            float(
                value
            )
        )

    except Exception:

        return fallback


# =========================================================
# CONFIG
# =========================================================

def projects_configured():

    return bool(
        KEMO_PROJECTS_URL
        and
        KEMO_PROJECTS_KEY
    )


# =========================================================
# HTTP
# =========================================================

def projects_request(
    method,
    endpoint,
    payload=None,
    authenticated=True,
    timeout=HTTP_TIMEOUT
):

    if not KEMO_PROJECTS_URL:

        raise RuntimeError(
            "KEMO_PROJECTS_URL missing"
        )


    url = (
        KEMO_PROJECTS_URL
        +
        endpoint
    )


    body = None


    if payload is not None:

        body = json.dumps(
            payload,
            ensure_ascii=False
        ).encode(
            "utf-8"
        )


    request = urllib.request.Request(
        url,
        data=body,
        method=method
    )


    request.add_header(
        "Accept",
        "application/json"
    )


    request.add_header(
        "User-Agent",
        (
            "KemoProjectsTelegram/"
            +
            VERSION
        )
    )


    if payload is not None:

        request.add_header(
            "Content-Type",
            "application/json"
        )


    if authenticated:

        if not KEMO_PROJECTS_KEY:

            raise RuntimeError(
                "KEMO_PROJECTS_KEY missing"
            )


        request.add_header(
            "X-Kemo-Projects-Key",
            KEMO_PROJECTS_KEY
        )


    try:

        with urllib.request.urlopen(
            request,
            timeout=timeout
        ) as response:

            raw = (
                response
                .read()
                .decode(
                    "utf-8",
                    errors="replace"
                )
            )


            if not raw:

                return {}


            return json.loads(
                raw
            )


    except urllib.error.HTTPError as error:

        try:

            raw = (
                error
                .read()
                .decode(
                    "utf-8",
                    errors="replace"
                )
            )

        except Exception:

            raw = ""


        raise RuntimeError(
            (
                "Projects HTTP "
                +
                str(
                    error.code
                )
                +
                ": "
                +
                clean_text(
                    raw,
                    2000
                )
            )
        )


    except urllib.error.URLError as error:

        raise RuntimeError(
            (
                "Projects network error: "
                +
                str(
                    error
                )
            )
        )


def projects_get(
    endpoint,
    authenticated=True,
    timeout=HTTP_TIMEOUT
):

    return projects_request(
        "GET",
        endpoint,
        payload=None,
        authenticated=authenticated,
        timeout=timeout
    )


def projects_post(
    endpoint,
    payload,
    timeout=HTTP_TIMEOUT
):

    return projects_request(
        "POST",
        endpoint,
        payload=payload,
        authenticated=True,
        timeout=timeout
    )


# =========================================================
# HEALTH
# =========================================================

def projects_health():

    try:

        response = projects_get(
            "/api/health",
            authenticated=False,
            timeout=10
        )


        if isinstance(
            response,
            dict
        ):

            return response


    except Exception as error:

        return {
            "ok":
                False,

            "error":
                str(
                    error
                )
        }


    return {
        "ok":
            False
    }


def active_workers_from_health(
    health
):

    if not isinstance(
        health,
        dict
    ):

        return 0


    project_health = health.get(
        "projects"
    )


    if isinstance(
        project_health,
        dict
    ):

        return safe_int(
            project_health.get(
                "activeWorkers"
            ),
            0
        )


    return safe_int(
        health.get(
            "activeWorkers"
        ),
        0
    )


# =========================================================
# PROJECT API
# =========================================================

def list_projects(
    user_id
):

    encoded_user = urllib.parse.quote(
        str(
            user_id
        ),
        safe=""
    )


    response = projects_get(
        (
            "/api/projects"
            +
            "?userId="
            +
            encoded_user
        )
    )


    if not isinstance(
        response,
        dict
    ):

        return []


    projects = response.get(
        "projects"
    )


    if not isinstance(
        projects,
        list
    ):

        return []


    return [
        item
        for item in projects
        if isinstance(
            item,
            dict
        )
    ][
        :MAX_PROJECTS
    ]


def create_project(
    user_id,
    chat_id,
    name,
    brief,
    raw_request,
    extra_metadata=None
):

    metadata = {
        "source":
            "telegram",

        "chatId":
            chat_id,

        "originalRequest":
            clean_text(
                raw_request,
                5000
            )
    }


    if isinstance(
        extra_metadata,
        dict
    ):

        metadata.update(
            extra_metadata
        )


    return projects_post(
        "/api/projects",
        {
            "userId":
                user_id,

            "projectType":
                "website",

            "name":
                clean_text(
                    name,
                    300
                ),

            "brief":
                clean_text(
                    brief,
                    30000
                ),

            "metadata":
                metadata
        },
        timeout=30
    )


def get_project_report(
    project_id
):

    encoded = urllib.parse.quote(
        str(
            project_id
        ),
        safe=""
    )


    return projects_get(
        (
            "/api/projects/"
            +
            encoded
            +
            "/report"
        ),
        timeout=25
    )


def queue_project_job(
    project_id,
    job_type,
    payload=None,
    priority=100
):

    encoded = urllib.parse.quote(
        str(
            project_id
        ),
        safe=""
    )


    if not isinstance(
        payload,
        dict
    ):

        payload = {}


    return projects_post(
        (
            "/api/projects/"
            +
            encoded
            +
            "/jobs"
        ),
        {
            "jobType":
                clean_text(
                    job_type,
                    150
                ),

            "payload":
                payload,

            "priority":
                priority
        },
        timeout=25
    )


# =========================================================
# PROJECT HELPERS
# =========================================================

def get_project_id(
    project
):

    if not isinstance(
        project,
        dict
    ):

        return ""


    return clean_text(
        project.get(
            "id"
        )
        or
        project.get(
            "projectId"
        )
        or
        project.get(
            "project_id"
        ),
        200
    )


def get_project_name(
    project
):

    if not isinstance(
        project,
        dict
    ):

        return "مشروع الموقع"


    return clean_text(
        project.get(
            "name"
        )
        or
        project.get(
            "project_name"
        )
        or
        project.get(
            "projectName"
        )
        or
        "مشروع الموقع",
        300
    )


def get_project_brief(
    project
):

    if not isinstance(
        project,
        dict
    ):

        return ""


    return clean_text(
        project.get(
            "brief"
        )
        or
        project.get(
            "project_brief"
        )
        or
        project.get(
            "projectBrief"
        ),
        20000
    )


def get_project_status(
    project
):

    if not isinstance(
        project,
        dict
    ):

        return ""


    return clean_text(
        project.get(
            "status"
        ),
        100
    )


def get_project_progress(
    project
):

    if not isinstance(
        project,
        dict
    ):

        return 0


    return safe_int(
        project.get(
            "progress"
        ),
        0
    )


def get_job_id(
    job
):

    if not isinstance(
        job,
        dict
    ):

        return ""


    return clean_text(
        job.get(
            "id"
        )
        or
        job.get(
            "jobId"
        )
        or
        job.get(
            "job_id"
        ),
        200
    )


# =========================================================
# PROJECT SELECTION
# =========================================================

def choose_project(
    user_id,
    raw_request
):

    projects = list_projects(
        user_id
    )


    if not projects:

        return None


    request_normalized = normalized(
        raw_request
    )


    best = None

    best_score = 0


    for project in projects:

        name = normalized(
            get_project_name(
                project
            )
        )


        if not name:

            continue


        score = 0


        if name in request_normalized:

            score = 100


        else:

            words = [
                word
                for word in name.split()
                if len(
                    word
                )
                >=
                3
            ]


            for word in words:

                if word in request_normalized:

                    score += 10


        if score > best_score:

            best_score = score

            best = project


    if best is not None:

        return best


    # Newest project is first.
    return projects[0]


# =========================================================
# PROJECT NAME
# =========================================================

def automatic_project_name(
    raw_request
):

    text = clean_text(
        raw_request,
        5000
    )


    patterns = [
        r"شركة\s+([^\n،,.]{2,60})",
        r"شركه\s+([^\n،,.]{2,60})",
        r"لمطعم\s+([^\n،,.]{2,60})",
        r"لمحل\s+([^\n،,.]{2,60})",
        r"لشركة\s+([^\n،,.]{2,60})",
        r"لشركه\s+([^\n،,.]{2,60})",
    ]


    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )


        if match:

            candidate = clean_text(
                match.group(
                    1
                ),
                80
            )


            if candidate:

                return (
                    "موقع "
                    +
                    candidate
                )


    return (
        "مشروع موقع "
        +
        time.strftime(
            "%m-%d %H:%M"
        )
    )


# =========================================================
# EXACT JOB VERIFICATION
# =========================================================

def inspect_job_start(
    project_id,
    expected_job_id
):

    response = get_project_report(
        project_id
    )


    if not isinstance(
        response,
        dict
    ):

        return {
            "verified":
                False,

            "reason":
                "invalid_report"
        }


    project = response.get(
        "project"
    )


    if not isinstance(
        project,
        dict
    ):

        project = {}


    worker = response.get(
        "worker"
    )


    if not isinstance(
        worker,
        dict
    ):

        worker = {}


    proof = response.get(
        "proof"
    )


    if not isinstance(
        proof,
        dict
    ):

        proof = {}


    active_job = response.get(
        "activeJob"
    )


    if not isinstance(
        active_job,
        dict
    ):

        active_job = {}


    expected_job_id = clean_text(
        expected_job_id,
        200
    )


    active_job_id = get_job_id(
        active_job
    )


    worker_online = bool(
        worker.get(
            "online"
        )
        or
        proof.get(
            "workerOnline"
        )
    )


    verified_working = bool(
        proof.get(
            "verifiedWorking"
        )
    )


    exact_job = bool(
        expected_job_id
        and
        active_job_id
        and
        expected_job_id
        ==
        active_job_id
    )


    status = get_project_status(
        project
    ).lower()


    progress = get_project_progress(
        project
    )


    stage = clean_text(
        project.get(
            "stage"
        ),
        200
    )


    worker_info = worker.get(
        "info"
    )


    if not isinstance(
        worker_info,
        dict
    ):

        worker_info = {}


    worker_id = clean_text(
        active_job.get(
            "worker_id"
        )
        or
        active_job.get(
            "workerId"
        )
        or
        worker_info.get(
            "worker_id"
        )
        or
        worker_info.get(
            "workerId"
        ),
        200
    )


    verified = bool(
        worker_online
        and
        verified_working
        and
        exact_job
        and
        status
        ==
        "working"
    )


    if verified:

        reason = "verified"


    elif not worker_online:

        reason = "worker_offline"


    elif not active_job_id:

        reason = "not_claimed"


    elif not exact_job:

        reason = "different_job_running"


    elif not verified_working:

        reason = "not_verified_working"


    else:

        reason = "not_working"


    return {
        "verified":
            verified,

        "reason":
            reason,

        "project":
            project,

        "worker":
            worker,

        "proof":
            proof,

        "activeJob":
            active_job,

        "expectedJobId":
            expected_job_id,

        "activeJobId":
            active_job_id,

        "workerOnline":
            worker_online,

        "verifiedWorking":
            verified_working,

        "exactJob":
            exact_job,

        "workerId":
            worker_id,

        "status":
            status,

        "progress":
            progress,

        "stage":
            stage
    }


def wait_for_job_start(
    project_id,
    job_id,
    timeout_seconds=VERIFY_START_SECONDS
):

    started = time.monotonic()


    last_state = {
        "verified":
            False,

        "reason":
            "waiting"
    }


    while (
        time.monotonic()
        -
        started
        <
        timeout_seconds
    ):

        try:

            last_state = inspect_job_start(
                project_id,
                job_id
            )


            if last_state.get(
                "verified"
            ):

                return last_state


        except Exception as error:

            last_state = {
                "verified":
                    False,

                "reason":
                    "verification_error",

                "error":
                    str(
                        error
                    )
            }


        time.sleep(
            VERIFY_START_POLL_SECONDS
        )


    return last_state


# =========================================================
# TELEGRAM SEND
# =========================================================

def send_telegram(
    chat_id,
    text
):

    try:

        sender = getattr(
            kemo,
            "send_message",
            None
        )


        if callable(
            sender
        ):

            sender(
                chat_id,
                text
            )

            return True


    except Exception as error:

        print(
            (
                "⚠️ Project Telegram send: "
                +
                str(
                    error
                )
            )
        )


    return False


# =========================================================
# VERIFIED START MESSAGES
# =========================================================

def verified_start_message(
    action_name,
    project_name,
    project_id,
    job_id,
    state
):

    lines = [
        (
            "✅ "
            +
            action_name
            +
            " بدأ فعليًا الآن"
        ),

        (
            "📁 "
            +
            clean_text(
                project_name,
                300
            )
        ),

        (
            "🆔 Project: "
            +
            clean_text(
                project_id,
                200
            )
        ),

        (
            "⚙️ Job: "
            +
            clean_text(
                job_id,
                200
            )
        ),

        (
            "🔒 Verified: "
            "نفس الـJob انمسك من الـWorker فعليًا."
        )
    ]


    worker_id = clean_text(
        state.get(
            "workerId"
        ),
        200
    )


    if worker_id:

        lines.append(
            (
                "🖥️ Worker: "
                +
                worker_id
            )
        )


    lines.append(
        (
            "📊 التقدم الحقيقي: "
            +
            str(
                safe_int(
                    state.get(
                        "progress"
                    ),
                    0
                )
            )
            +
            "%"
        )
    )


    stage = clean_text(
        state.get(
            "stage"
        ),
        200
    )


    if stage:

        lines.append(
            (
                "🧩 المرحلة: "
                +
                stage
            )
        )


    return "\n".join(
        lines
    )


def queued_message(
    action_name,
    project_name,
    project_id,
    job_id,
    state
):

    lines = [
        (
            "✅ سجلت طلب "
            +
            action_name
            +
            " فعليًا بالنظام."
        ),

        (
            "📁 "
            +
            clean_text(
                project_name,
                300
            )
        ),

        (
            "🆔 Project: "
            +
            clean_text(
                project_id,
                200
            )
        ),

        (
            "⚙️ Job: "
            +
            clean_text(
                job_id,
                200
            )
        ),

        "🟡 لكن التنفيذ لسه ما بدأ فعليًا."
    ]


    reason = clean_text(
        state.get(
            "reason"
        ),
        100
    )


    if reason == "different_job_running":

        lines.append(
            "⏳ الـBuilder مشغول حاليًا بـJob ثاني."
        )


    elif reason == "worker_offline":

        lines.append(
            "🔴 الـBuilder مش Online هسّا."
        )


    elif reason == "not_claimed":

        lines.append(
            "⏳ نفس الـJob لسه موجود بالطابور وما تم استلامه."
        )


    else:

        lines.append(
            "⏳ بستنى إثبات استلام نفس الـJob."
        )


    lines.append(
        (
            "🔒 ما رح أقول إنه بدأ "
            "إلا بعد ما السيرفر يثبت الاستلام الحقيقي."
        )
    )


    lines.append(
        (
            "📩 رح أبعتلك تأكيد تلقائي أول ما يبدأ."
        )
    )


    return "\n".join(
        lines
    )


# =========================================================
# BACKGROUND VERIFICATION
# =========================================================

def monitor_job_start(
    chat_id,
    action_name,
    project_name,
    project_id,
    job_id
):

    key = (
        str(
            project_id
        )
        +
        ":"
        +
        str(
            job_id
        )
    )


    started = time.monotonic()


    try:

        while (
            time.monotonic()
            -
            started
            <
            BACKGROUND_VERIFY_SECONDS
        ):

            try:

                state = inspect_job_start(
                    project_id,
                    job_id
                )


                if state.get(
                    "verified"
                ):

                    message = verified_start_message(
                        action_name,
                        project_name,
                        project_id,
                        job_id,
                        state
                    )


                    if send_telegram(
                        chat_id,
                        message
                    ):

                        try:

                            kemo.save_message(
                                chat_id,
                                "assistant",
                                message
                            )

                        except Exception:

                            pass


                    print(
                        (
                            "✅ VERIFIED JOB START | "
                            +
                            str(
                                job_id
                            )
                        )
                    )


                    return


            except Exception as error:

                print(
                    (
                        "⚠️ Job start monitor: "
                        +
                        str(
                            error
                        )
                    )
                )


            time.sleep(
                BACKGROUND_VERIFY_POLL_SECONDS
            )


        print(
            (
                "🟡 JOB START VERIFY TIMEOUT | "
                +
                str(
                    job_id
                )
            )
        )


    finally:

        with MONITOR_LOCK:

            ACTIVE_MONITORS.discard(
                key
            )


def start_job_monitor(
    chat_id,
    action_name,
    project_name,
    project_id,
    job_id
):

    key = (
        str(
            project_id
        )
        +
        ":"
        +
        str(
            job_id
        )
    )


    with MONITOR_LOCK:

        if key in ACTIVE_MONITORS:

            return False


        ACTIVE_MONITORS.add(
            key
        )


    thread = threading.Thread(
        target=monitor_job_start,
        args=(
            chat_id,
            action_name,
            project_name,
            project_id,
            job_id,
        ),
        daemon=True
    )


    thread.start()


    return True


# =========================================================
# STANDARD JOB RESPONSE
# =========================================================

def confirm_or_queue(
    chat_id,
    action_name,
    project_name,
    project_id,
    job_id
):

    state = wait_for_job_start(
        project_id,
        job_id
    )


    if state.get(
        "verified"
    ):

        return verified_start_message(
            action_name,
            project_name,
            project_id,
            job_id,
            state
        )


    start_job_monitor(
        chat_id,
        action_name,
        project_name,
        project_id,
        job_id
    )


    return queued_message(
        action_name,
        project_name,
        project_id,
        job_id,
        state
    )


# =========================================================
# INTENT MARKERS
# =========================================================

CREATE_MARKERS = [
    "اعملي موقع",
    "اعمللي موقع",
    "اعمل لي موقع",
    "اعمل موقع",
    "سويلي موقع",
    "سوي موقع",
    "ابنيلي موقع",
    "ابني موقع",
    "صمملي موقع",
    "صمم موقع",
    "انشئ موقع",
    "أنشئ موقع",
    "بدي موقع لشركة",
    "بدي موقع لشركه",
    "بدي ويبسايت",
    "اعملي ويبسايت",
    "اعمل ويبسايت",
    "ابني ويبسايت",
    "صمم ويبسايت",
    "create website",
    "create a website",
    "build website",
    "build a website",
    "design website",
    "design a website",
]


REBUILD_MARKERS = [
    "عيد من جديد",
    "أعيد من جديد",
    "اعيد من جديد",
    "اعد من جديد",
    "عيده من جديد",
    "أعيده من جديد",
    "اعيده من جديد",
    "اعمل من جديد",
    "اعمله من جديد",
    "ابدأ من جديد",
    "ابدا من جديد",
    "بلش من جديد",
    "من الصفر",
    "ابدأ من الصفر",
    "ابدا من الصفر",
    "بلش من الصفر",
    "عيد المشروع",
    "عيد الموقع",
    "أعد المشروع",
    "اعد المشروع",
    "أعد الموقع",
    "اعد الموقع",
    "اعمل واحد جديد",
    "اعمل واحد جديد من الصفر",
    "اعمل موقع جديد بدل",
    "امسح وابدأ",
    "امسح وابدا",
    "امسح وبلش",
    "rebuild from scratch",
    "start from scratch",
    "redo website",
    "rebuild website",
]


DISSATISFIED_MARKERS = [
    "مش حلو",
    "مش عاجبني",
    "ما عجبني",
    "سيء جدا",
    "سيئ جدا",
    "سيء جداً",
    "سيئ جداً",
    "مش بالمستوى",
    "ضعيف",
]


STATUS_MARKERS = [
    "وين وصلت بالمشروع",
    "وين وصلت بالموقع",
    "وين وصل المشروع",
    "وين وصل الموقع",
    "وين صرت بالمشروع",
    "وين صرت بالموقع",
    "شو صار بالمشروع",
    "شو صار بالموقع",
    "شو وضع المشروع",
    "شو وضع الموقع",
    "حالة المشروع",
    "حاله المشروع",
    "حالة الموقع",
    "حاله الموقع",
    "نسبة المشروع",
    "نسبه المشروع",
    "نسبة الموقع",
    "نسبه الموقع",
    "تقدم المشروع",
    "تقدم الموقع",
    "project status",
    "website status",
    "site progress",
]


SCREENSHOT_MARKERS = [
    "صورلي المشروع",
    "صور لي المشروع",
    "صورلي الموقع",
    "صور لي الموقع",
    "سكرين شوت للمشروع",
    "سكرين شوت للموقع",
    "سكرينشوت للمشروع",
    "سكرينشوت للموقع",
    "ورجيني الموقع",
    "ورجيني المشروع",
    "فرجيني الموقع",
    "فرجيني المشروع",
    "ابعتلي صورة الموقع",
    "ابعتلي صوره الموقع",
    "ابعتلي صورة المشروع",
    "ورجيني وين وصلت",
    "screenshot website",
    "screenshot project",
]


LIST_MARKERS = [
    "مشاريعي",
    "شو مشاريعي",
    "شو المشاريع",
    "اعرض المشاريع",
    "اعرضلي المشاريع",
    "قائمة المشاريع",
    "قائمه المشاريع",
    "my projects",
    "list projects",
]


PUBLISH_MARKERS = [
    "انشر الموقع",
    "انشر المشروع",
    "ارفع الموقع",
    "خلي الموقع لايف",
    "اطلع الموقع لايف",
    "publish website",
    "deploy website",
]


REVISION_MARKERS = [
    "عدل",
    "عدّل",
    "غير",
    "غيّر",
    "بدل",
    "بدّل",
    "حسن",
    "حسّن",
    "اضف",
    "أضف",
    "احذف",
    "شيل",
    "كبر",
    "كبّر",
    "صغر",
    "صغّر",
    "خلي",
    "خلّي",
    "غيرلي",
    "عدلي",
    "صحح",
    "صحّح",
    "ظبط",
    "زبط",
    "modify",
    "update",
    "revise",
    "change",
    "improve",
]


PROJECT_CONTEXT_MARKERS = [
    "المشروع",
    "مشروع",
    "الموقع",
    "موقع",
    "ويبسايت",
    "ويب سايت",
    "website",
    "الهيرو",
    "hero",
    "الثيم",
    "التصميم",
    "اللون",
    "الألوان",
    "الالوان",
    "الفونت",
    "الخط",
    "القسم",
    "السكشن",
    "section",
    "المحتوى",
    "النص",
    "الصور",
    "الواجهة",
]


# =========================================================
# INTENT DETECTOR
# =========================================================

def detect_project_action(
    text
):

    raw = clean_text(
        text,
        5000
    )


    if not raw:

        return None


    # Publishing wrapper sits above this file,
    # but keep compatibility.
    if contains_any(
        raw,
        PUBLISH_MARKERS
    ):

        return "publish"


    if contains_any(
        raw,
        LIST_MARKERS
    ):

        return "list"


    if contains_any(
        raw,
        STATUS_MARKERS
    ):

        return "status"


    if contains_any(
        raw,
        SCREENSHOT_MARKERS
    ):

        return "screenshot"


    # Strong rebuild commands ALWAYS win.
    if contains_any(
        raw,
        REBUILD_MARKERS
    ):

        return "rebuild"


    # "مش حلو / سيء" + project context = rebuild.
    if (
        contains_any(
            raw,
            DISSATISFIED_MARKERS
        )
        and
        contains_any(
            raw,
            PROJECT_CONTEXT_MARKERS
        )
    ):

        return "rebuild"


    if contains_any(
        raw,
        CREATE_MARKERS
    ):

        return "create"


    if (
        contains_any(
            raw,
            REVISION_MARKERS
        )
        and
        contains_any(
            raw,
            PROJECT_CONTEXT_MARKERS
        )
    ):

        return "revision"


    return None


# =========================================================
# CREATE PROJECT
# =========================================================

def handle_create(
    chat_id,
    user_id,
    raw
):

    project_name = automatic_project_name(
        raw
    )


    response = create_project(
        user_id,
        chat_id,
        project_name,
        raw,
        raw
    )


    if (
        not isinstance(
            response,
            dict
        )
        or
        response.get(
            "ok"
        )
        is False
    ):

        raise RuntimeError(
            "Project creation failed"
        )


    project_id = clean_text(
        response.get(
            "projectId"
        )
        or
        response.get(
            "project_id"
        ),
        200
    )


    job_id = clean_text(
        response.get(
            "jobId"
        )
        or
        response.get(
            "job_id"
        ),
        200
    )


    if (
        not project_id
        or
        not job_id
    ):

        raise RuntimeError(
            "Project ID or Job ID missing"
        )


    return confirm_or_queue(
        chat_id,
        "بناء المشروع",
        project_name,
        project_id,
        job_id
    )


# =========================================================
# REBUILD FROM ZERO
# =========================================================

def handle_rebuild(
    chat_id,
    user_id,
    raw
):

    selected = choose_project(
        user_id,
        raw
    )


    if not selected:

        return (
            "فهمت إنك بدك أعيده من الصفر، "
            "بس ما لقيت مشروع سابق أعيد بناءه."
        )


    old_project_id = get_project_id(
        selected
    )


    project_name = get_project_name(
        selected
    )


    old_brief = get_project_brief(
        selected
    )


    rebuild_brief = (
        "REBUILD THIS WEBSITE COMPLETELY FROM SCRATCH.\n\n"
        "Do NOT patch the previous design.\n"
        "Do NOT reuse the old layout just because it exists.\n"
        "Start again with research, visual direction, structure, "
        "content, imagery direction, UI system and QA.\n\n"
        "ORIGINAL PROJECT BRIEF:\n"
        +
        old_brief
        +
        "\n\n"
        "KARIM'S NEW FEEDBACK / REBUILD REQUEST:\n"
        +
        clean_text(
            raw,
            10000
        )
        +
        "\n\n"
        "IMPORTANT:\n"
        "Treat Karim's newest feedback as the highest priority."
    )


    response = create_project(
        user_id,
        chat_id,
        project_name,
        rebuild_brief,
        raw,
        extra_metadata={
            "rebuild":
                True,

            "rebuildFromScratch":
                True,

            "rebuildOfProjectId":
                old_project_id,

            "reason":
                "telegram_rebuild_request"
        }
    )


    if (
        not isinstance(
            response,
            dict
        )
        or
        response.get(
            "ok"
        )
        is False
    ):

        raise RuntimeError(
            "Rebuild project creation failed"
        )


    new_project_id = clean_text(
        response.get(
            "projectId"
        )
        or
        response.get(
            "project_id"
        ),
        200
    )


    job_id = clean_text(
        response.get(
            "jobId"
        )
        or
        response.get(
            "job_id"
        ),
        200
    )


    if (
        not new_project_id
        or
        not job_id
    ):

        raise RuntimeError(
            "Rebuild Project ID or Job ID missing"
        )


    return confirm_or_queue(
        chat_id,
        "إعادة البناء من الصفر",
        project_name,
        new_project_id,
        job_id
    )


# =========================================================
# REVISION
# =========================================================

def handle_revision(
    chat_id,
    user_id,
    raw
):

    selected = choose_project(
        user_id,
        raw
    )


    if not selected:

        return (
            "فهمت التعديل، بس ما لقيت مشروع أطبقه عليه."
        )


    project_id = get_project_id(
        selected
    )


    project_name = get_project_name(
        selected
    )


    status = get_project_status(
        selected
    ).lower()


    if not project_id:

        return (
            "لقيت المشروع بس Project ID ناقص."
        )


    # Completed/published projects are cloned into
    # a fresh working project because the scheduler
    # does not claim normal jobs from completed projects.
    if status in {
        "completed",
        "cancelled",
    }:

        old_brief = get_project_brief(
            selected
        )


        revision_brief = (
            "CREATE A FRESH WORKING VERSION OF THIS WEBSITE.\n\n"
            "ORIGINAL PROJECT BRIEF:\n"
            +
            old_brief
            +
            "\n\n"
            "KARIM'S NEW REVISION REQUEST:\n"
            +
            clean_text(
                raw,
                10000
            )
            +
            "\n\n"
            "Keep what is useful from the business brief, "
            "but rebuild whatever is required to satisfy "
            "the newest feedback."
        )


        response = create_project(
            user_id,
            chat_id,
            project_name,
            revision_brief,
            raw,
            extra_metadata={
                "revisionClone":
                    True,

                "revisionOfProjectId":
                    project_id,

                "reason":
                    "revision_after_completed_project"
            }
        )


        new_project_id = clean_text(
            (
                response.get(
                    "projectId"
                )
                if isinstance(
                    response,
                    dict
                )
                else ""
            ),
            200
        )


        job_id = clean_text(
            (
                response.get(
                    "jobId"
                )
                if isinstance(
                    response,
                    dict
                )
                else ""
            ),
            200
        )


        if (
            not new_project_id
            or
            not job_id
        ):

            raise RuntimeError(
                "Revision clone creation failed"
            )


        return confirm_or_queue(
            chat_id,
            "تنفيذ التعديل",
            project_name,
            new_project_id,
            job_id
        )


    # Normal active-project revision.
    response = queue_project_job(
        project_id,
        "project_revision",
        {
            "feedback":
                clean_text(
                    raw,
                    10000
                ),

            "source":
                "telegram",

            "chatId":
                chat_id,

            "userId":
                user_id
        },
        priority=REVISION_PRIORITY
    )


    job_id = clean_text(
        (
            response.get(
                "jobId"
            )
            if isinstance(
                response,
                dict
            )
            else ""
        ),
        200
    )


    if not job_id:

        raise RuntimeError(
            "Revision Job ID missing"
        )


    return confirm_or_queue(
        chat_id,
        "تنفيذ التعديل",
        project_name,
        project_id,
        job_id
    )


# =========================================================
# SCREENSHOT
# =========================================================

def handle_screenshot(
    chat_id,
    user_id,
    raw
):

    selected = choose_project(
        user_id,
        raw
    )


    if not selected:

        return (
            "ما لقيت مشروع عشان أصوره."
        )


    project_id = get_project_id(
        selected
    )


    project_name = get_project_name(
        selected
    )


    if not project_id:

        return (
            "لقيت المشروع بس Project ID ناقص."
        )


    response = queue_project_job(
        project_id,
        "refresh_screenshot",
        {
            "source":
                "telegram",

            "chatId":
                chat_id,

            "userId":
                user_id,

            "request":
                clean_text(
                    raw,
                    3000
                )
        },
        priority=SCREENSHOT_PRIORITY
    )


    job_id = clean_text(
        (
            response.get(
                "jobId"
            )
            if isinstance(
                response,
                dict
            )
            else ""
        ),
        200
    )


    if not job_id:

        raise RuntimeError(
            "Screenshot Job ID missing"
        )


    return confirm_or_queue(
        chat_id,
        "تحديث الـScreenshot",
        project_name,
        project_id,
        job_id
    )


# =========================================================
# LIST PROJECTS
# =========================================================

def handle_list(
    user_id
):

    projects = list_projects(
        user_id
    )


    if not projects:

        return (
            "ما عندك مشاريع مواقع مسجلة حاليًا."
        )


    lines = [
        "مشاريعك:"
    ]


    for project in projects[:10]:

        lines.append(
            (
                "• "
                +
                get_project_name(
                    project
                )
                +
                " — "
                +
                str(
                    get_project_progress(
                        project
                    )
                )
                +
                "%"
                +
                " — "
                +
                get_project_status(
                    project
                )
            )
        )


    return "\n".join(
        lines
    )


# =========================================================
# STATUS
# =========================================================

def handle_status(
    user_id,
    raw
):

    selected = choose_project(
        user_id,
        raw
    )


    if not selected:

        return (
            "ما لقيت مشروع موقع مسجل عندي."
        )


    project_id = get_project_id(
        selected
    )


    if not project_id:

        return (
            "لقيت المشروع، بس Project ID ناقص."
        )


    response = get_project_report(
        project_id
    )


    if not isinstance(
        response,
        dict
    ):

        raise RuntimeError(
            "Invalid project report"
        )


    project = response.get(
        "project"
    )


    if not isinstance(
        project,
        dict
    ):

        project = selected


    worker = response.get(
        "worker"
    )


    if not isinstance(
        worker,
        dict
    ):

        worker = {}


    proof = response.get(
        "proof"
    )


    if not isinstance(
        proof,
        dict
    ):

        proof = {}


    active_job = response.get(
        "activeJob"
    )


    if not isinstance(
        active_job,
        dict
    ):

        active_job = {}


    name = get_project_name(
        project
    )


    progress = get_project_progress(
        project
    )


    status = get_project_status(
        project
    )


    stage = clean_text(
        project.get(
            "stage"
        ),
        200
    )


    current_task = clean_text(
        project.get(
            "current_task"
        )
        or
        project.get(
            "currentTask"
        )
        or
        active_job.get(
            "job_type"
        )
        or
        active_job.get(
            "jobType"
        ),
        600
    )


    last_completed = clean_text(
        project.get(
            "last_completed"
        )
        or
        project.get(
            "lastCompleted"
        ),
        600
    )


    worker_online = bool(
        worker.get(
            "online"
        )
        or
        proof.get(
            "workerOnline"
        )
    )


    verified_working = bool(
        proof.get(
            "verifiedWorking"
        )
    )


    active_job_id = get_job_id(
        active_job
    )


    quality_score = project.get(
        "quality_score"
    )


    if quality_score is None:

        quality_score = project.get(
            "qualityScore"
        )


    preview_url = clean_text(
        project.get(
            "preview_url"
        )
        or
        project.get(
            "previewUrl"
        )
        or
        proof.get(
            "previewUrl"
        ),
        2000
    )


    production_url = clean_text(
        project.get(
            "production_url"
        )
        or
        project.get(
            "productionUrl"
        )
        or
        proof.get(
            "productionUrl"
        ),
        2000
    )


    lines = [
        (
            "📁 "
            +
            name
        ),

        (
            "📊 التقدم الحقيقي: "
            +
            str(
                progress
            )
            +
            "%"
        ),

        (
            "📌 الحالة: "
            +
            (
                status
                or
                "غير محددة"
            )
        )
    ]


    if stage:

        lines.append(
            (
                "🧩 المرحلة: "
                +
                stage
            )
        )


    if current_task:

        lines.append(
            (
                "⚙️ شغال على: "
                +
                current_task
            )
        )


    if active_job_id:

        lines.append(
            (
                "🧾 Active Job: "
                +
                active_job_id
            )
        )


    if last_completed:

        lines.append(
            (
                "✅ آخر مهمة خلصها: "
                +
                last_completed
            )
        )


    if quality_score is not None:

        lines.append(
            (
                "🎯 Quality: "
                +
                str(
                    quality_score
                )
                +
                "/100"
            )
        )


    if verified_working:

        lines.append(
            (
                "🟢 متحقق من السيرفر إنه شغال فعليًا الآن."
            )
        )


    elif worker_online:

        lines.append(
            (
                "🟡 الـBuilder Online، "
                "لكن ما في Active Job متحقق منه هسّا."
            )
        )


    else:

        lines.append(
            "🔴 الـBuilder مش Online حاليًا."
        )


    if preview_url:

        lines.append(
            (
                "👀 Preview: "
                +
                preview_url
            )
        )


    if production_url:

        lines.append(
            (
                "🌐 Final: "
                +
                production_url
            )
        )


    return "\n".join(
        lines
    )


# =========================================================
# LEGACY PUBLISH FALLBACK
# =========================================================

def handle_publish(
    user_id,
    raw
):

    selected = choose_project(
        user_id,
        raw
    )


    if selected:

        return (
            "طلب النشر لازم يمر من Publisher الحقيقي. "
            "مش رح أعطيك نجاح وهمي."
        )


    return (
        "ما لقيت مشروع جاهز للنشر."
    )


# =========================================================
# ROUTER
# =========================================================

def handle_project_request(
    chat_id,
    user_id,
    text
):

    raw = clean_text(
        text,
        5000
    )


    action = detect_project_action(
        raw
    )


    if not action:

        return None


    if not projects_configured():

        return (
            "ربط المشاريع ناقص عندي. "
            "KEMO_PROJECTS_URL أو KEMO_PROJECTS_KEY مش موجود."
        )


    if action == "create":

        return handle_create(
            chat_id,
            user_id,
            raw
        )


    if action == "rebuild":

        return handle_rebuild(
            chat_id,
            user_id,
            raw
        )


    if action == "revision":

        return handle_revision(
            chat_id,
            user_id,
            raw
        )


    if action == "status":

        return handle_status(
            user_id,
            raw
        )


    if action == "screenshot":

        return handle_screenshot(
            chat_id,
            user_id,
            raw
        )


    if action == "list":

        return handle_list(
            user_id
        )


    if action == "publish":

        return handle_publish(
            user_id,
            raw
        )


    return None


# =========================================================
# WRAPPED KEMO
# =========================================================

def ask_kemo_with_projects(
    chat_id,
    user_id,
    user_message
):

    try:

        project_answer = (
            handle_project_request(
                chat_id,
                user_id,
                user_message
            )
        )


    except Exception as error:

        print(
            (
                "❌ Project router: "
                +
                str(
                    error
                )
            )
        )


        project_answer = (
            "صار خلل بتنفيذ طلب المشروع. "
            "ما رح أدّعي إنه اشتغل قبل ما أتأكد."
        )


    if project_answer is not None:

        try:

            kemo.save_message(
                chat_id,
                "assistant",
                project_answer
            )

        except Exception as error:

            print(
                (
                    "⚠️ Project answer memory: "
                    +
                    str(
                        error
                    )
                )
            )


        return project_answer


    # Not a project command.
    # Continue to existing desktop_runner / Kemo V7.
    return EXISTING_KEMO_ASK(
        chat_id,
        user_id,
        user_message
    )


# =========================================================
# INSTALL WRAPPER
# =========================================================

kemo.ask_kemo = (
    ask_kemo_with_projects
)


# =========================================================
# START
# =========================================================

def main():

    print("")
    print(
        "========================================"
    )
    print(
        " KEMO PROJECT TELEGRAM BRIDGE V1.3"
    )
    print(
        " REAL COMMAND EXECUTION"
    )
    print(
        " VERIFIED START FOR EVERY JOB"
    )
    print(
        "========================================"
    )
    print("")


    print(
        "✅ main.py preserved"
    )


    print(
        "✅ desktop_runner.py preserved"
    )


    print(
        "✅ Telegram text projects"
    )


    print(
        "✅ Telegram voice projects"
    )


    print(
        "✅ Create commands -> real jobs"
    )


    print(
        "✅ Revision commands -> real jobs"
    )


    print(
        "✅ Rebuild from zero -> NEW real project"
    )


    print(
        "✅ Completed project revision -> fresh working version"
    )


    print(
        "✅ Exact Job ID verification"
    )


    print(
        "✅ verifiedWorking required"
    )


    print(
        "✅ Worker Online required"
    )


    print(
        "✅ Background verified-start confirmation"
    )


    print(
        "🚫 No fake project start"
    )


    print(
        "🚫 No fake revision start"
    )


    print(
        "🚫 No fake rebuild start"
    )


    print(
        "🚫 No fake publishing"
    )


    print(
        (
            "✅ Projects URL: "
            +
            (
                "configured"
                if KEMO_PROJECTS_URL
                else
                "MISSING"
            )
        )
    )


    print(
        (
            "✅ Projects key: "
            +
            (
                "configured"
                if KEMO_PROJECTS_KEY
                else
                "MISSING"
            )
        )
    )


    health = projects_health()


    if health.get(
        "ok"
    ):

        print(
            "✅ Project Manager API: ONLINE"
        )


        print(
            (
                "✅ Active project workers: "
                +
                str(
                    active_workers_from_health(
                        health
                    )
                )
            )
        )


    else:

        print(
            (
                "⚠️ Project Manager API: "
                +
                clean_text(
                    health.get(
                        "error"
                    )
                    or
                    "OFFLINE",
                    1000
                )
            )
        )


    print("")
    print(
        "➡️ Starting Desktop + Kemo V7..."
    )
    print("")


    desktop_runner.main()


if __name__ == "__main__":

    main()
