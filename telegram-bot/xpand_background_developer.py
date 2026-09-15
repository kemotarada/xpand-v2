"""Autonomous XPAND developer worker for Kemo's Railway service."""
import json
import os
import threading
import time
import traceback
import urllib.parse
import urllib.request


INTERVAL_SECONDS = max(
    3600,
    int(os.getenv("XPAND_AUTONOMOUS_DEVELOPER_INTERVAL_SECONDS", "7200")),
)

PROMPT = """Run one focused autonomous XPAND development cycle.

Repository: kemotarada/xpand-v2, branch: main.
Inspect recent commits and one content or brand subsystem first. Prioritize premium STC Bank advertising copy in Arabic and English: benefit extraction, hooks, headlines, body copy, CTAs, Saudi cultural fit, channel variants, factuality, and Brand Memory. Use only bounded public research when useful. Never invent offers, rates, eligibility, financial claims, or private data.

Make one small, coherent, reversible improvement. Preserve Gemini as the official image route. Never change image-provider mode, secrets, production variables, deployments, Telegram behavior, or billing. Use the existing safe file-selection, Gemini coding, secret scanning, path normalization, validation, and atomic GitHub commit pipeline. Run targeted validation before commit. If no safe improvement is ready, do not commit and report why.

Return a concise structured result with summary, files, tests, and next_step. The worker will commit only after the existing validation pipeline succeeds."""

_lock = threading.Lock()
_started = False


def _owner_id():
    raw = (
        os.getenv("TELEGRAM_ALLOWED_USER_ID", "").strip()
        or os.getenv("OWNER_USER_ID", "").strip()
    )
    return int(raw) if raw.lstrip("-").isdigit() else 0


def _send_telegram(text):
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_ALLOWED_USER_ID", "").strip()
    if not token or not chat_id:
        print("⚠️ Autonomous developer report skipped: Telegram settings missing")
        return
    payload = urllib.parse.urlencode(
        {"chat_id": chat_id, "text": text[:3900]}
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.telegram.org/bot" + token + "/sendMessage",
        data=payload,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response.read()
    except Exception as error:
        print("⚠️ Autonomous developer Telegram report failed: " + str(error))


def _pending_by_id(admin, owner_id, change_id):
    with admin.db_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, owner_user_id, agent_slug, agent_name,
                       request_text, summary, changes, status,
                       github_branch, created_at
                FROM kemo_agent_admin_pending_code
                WHERE id = %s AND owner_user_id = %s
                  AND status = 'pending_approval'
                LIMIT 1;
                """,
                (change_id, int(owner_id)),
            )
            return admin.row_to_dict(cur, cur.fetchone())


def run_cycle():
    if not _lock.acquire(blocking=False):
        print("⏭️ Autonomous XPAND cycle skipped: previous cycle is still running")
        return
    admin = None
    try:
        import agent_factory_admin as admin

        owner_id = _owner_id()
        if not owner_id:
            raise RuntimeError("TELEGRAM_ALLOWED_USER_ID is missing")

        resolved = admin.call_stack.resolve_target_agent("XPAND")
        if not resolved:
            raise RuntimeError("XPAND target agent could not be resolved")

        staged = admin.stage_code_change(owner_id, resolved, PROMPT)
        pending = _pending_by_id(admin, owner_id, staged["id"])
        if not pending:
            raise RuntimeError("Autonomous change was not found after staging")

        commit_sha = admin.apply_pending_change(owner_id, pending)
        report = (
            "✅ Kemo autonomous XPAND cycle completed.\n\n"
            "Summary: " + str(staged.get("summary", "validated improvement")) + "\n"
            "Files: " + ", ".join(staged.get("files", [])) + "\n"
            "GitHub commit: " + commit_sha[:12] + "\n"
            "Validation: safe pipeline passed\n"
            "Next: continue with one focused STC Bank or Brand Memory improvement."
        )
        print(report)
        _send_telegram(report)
    except Exception as error:
        if admin is not None and isinstance(error, admin.NoSafeCodeChange):
            report = (
                "ℹ️ Kemo autonomous XPAND cycle completed with no commit.\n\n"
                "Reason: " + str(error)[:1800] + "\n"
                "No safe change was ready; nothing was modified."
            )
            print(report)
            _send_telegram(report)
            return

        report = (
            "⚠️ Kemo autonomous XPAND cycle stopped safely.\n\n"
            "Reason: " + str(error)[:1800] + "\n"
            "No unvalidated commit was created."
        )
        print(report)
        traceback.print_exc()
        _send_telegram(report)
    finally:
        _lock.release()


def _loop():
    while True:
        run_cycle()
        time.sleep(INTERVAL_SECONDS)


def start():
    global _started
    if _started:
        return False
    if os.getenv("XPAND_AUTONOMOUS_DEVELOPER_ENABLED", "false").lower() not in {
        "1", "true", "yes", "on"
    }:
        print("ℹ️ Autonomous XPAND developer is disabled")
        return False
    _started = True
    thread = threading.Thread(
        target=_loop,
        name="xpand-autonomous-developer",
        daemon=True,
    )
    thread.start()
    print(
        "✅ Autonomous XPAND developer started; interval="
        + str(INTERVAL_SECONDS)
        + "s"
    )
    return True
