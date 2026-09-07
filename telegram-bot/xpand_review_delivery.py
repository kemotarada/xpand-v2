"""Opt-in, private diagnostic delivery. Never calls an image/vision provider."""
import json
import math
import threading
import time


_REVIEW_SESSIONS = {}
_REVIEW_LOCK = threading.Lock()
_REVIEW_TTL_SECONDS = 24 * 60 * 60


def _private_scope(chat_id, user_id):
    chat, user = str(chat_id), str(user_id)
    return (chat, user) if chat == user and user.isdigit() and int(user) > 0 else None


def handle_review_command(core, chat_id, user_id, text):
    command = str(text or "").strip().lower()
    enabled = command in {"/xpand_review_on", "فعّل مراجعة المسودات"}
    disabled = command in {"/xpand_review_off", "أوقف مراجعة المسودات"}
    if not enabled and not disabled:
        return False
    scope = _private_scope(chat_id, user_id)
    if scope is None:
        core.send_message(chat_id, "فعّل مراجعة المسودات في محادثتك الخاصة مع البوت فقط.")
        return True
    with _REVIEW_LOCK:
        if enabled:
            now = time.monotonic()
            expired = [key for key, expiry in _REVIEW_SESSIONS.items() if expiry <= now]
            for key in expired:
                _REVIEW_SESSIONS.pop(key, None)
            _REVIEW_SESSIONS[scope] = now + _REVIEW_TTL_SECONDS
        else:
            _REVIEW_SESSIONS.pop(scope, None)
    core.send_message(
        chat_id,
        (
            "تم تفعيل مراجعة المسودات لهذه المحادثة لمدة 24 ساعة أو حتى إعادة تشغيل البوت. "
            "إذا رُفضت الصورة ستصلك كملف «للتشخيص — غير معتمدة» مع تقرير الجودة، "
            "دون إضافة استدعاء توليد. لا يسترجع هذا صور المحاولات السابقة.\n"
            "للإيقاف: /xpand_review_off"
        ) if enabled else "تم إيقاف مراجعة المسودات. ستصلك الصور المجتازة فقط.",
    )
    return True


def review_enabled(chat_id, user_id):
    scope = _private_scope(chat_id, user_id)
    if scope is None:
        return False
    with _REVIEW_LOCK:
        expiry = _REVIEW_SESSIONS.get(scope, 0)
        if expiry <= time.monotonic():
            _REVIEW_SESSIONS.pop(scope, None)
            return False
        return True


def _score(value):
    try:
        number = float(value)
        return max(0.0, min(100.0, number)) if math.isfinite(number) else 0.0
    except (TypeError, ValueError):
        return 0.0


def _texts(value, limit=12):
    if not isinstance(value, (list, tuple)):
        return []
    return [str(item)[:500] for item in value[:limit] if isinstance(item, str)]


def collect_rejected_candidate(candidates, production):
    """Keep the highest-scored rejected final and its matching QA in memory."""
    image = getattr(production, "final_image", None)
    qa = getattr(production, "qa", None)
    raw = getattr(qa, "raw", {}) or {}
    if (
        image is None or not getattr(image, "image_bytes", b"")
        or qa is None
        or getattr(production, "ok", False)
        or getattr(qa, "passed", False)
        or (isinstance(raw, dict) and raw.get("provider_failure"))
    ):
        return
    if not candidates or _score(qa.score) > _score(candidates[0].qa.score):
        candidates[:] = [production]


def deliver_rejected_candidate(core, *, chat_id, user_id, candidates, send_document):
    """Send two labelled documents, not the approved-image delivery path."""
    if not review_enabled(chat_id, user_id) or not candidates:
        return {"image_sent": False, "report_sent": False}
    production = candidates[0]
    image, qa = production.final_image, production.qa
    blockers = _texts(getattr(qa, "critical_blockers", []))
    problems = _texts(getattr(qa, "problems", []))
    scores = getattr(qa, "scores", {})
    scores = scores if isinstance(scores, dict) else {}
    # Allowlisted QA fields only: no prompts, tokens, provider responses,
    # environment values, production telemetry, or other users' records.
    allowed_scores = {
        "concept_execution", "message_clarity_without_text", "brand_alignment",
        "brand_identity_strength", "advertising_readiness", "scene_originality",
        "service_integration", "realism", "camera_perspective",
        "reference_adherence", "copy_space_composition", "text_logo_compliance",
    }
    report = {
        "status": "diagnostic_draft_not_approved",
        "approved": False,
        "qa_passed": False,
        "note": "للتشخيص فقط — ليست إعلانًا معتمدًا. تقييمات آلية تحتاج مراجعة بصرية.",
        "score_out_of_100": _score(qa.score),
        "scores": {key: _score(scores[key]) for key in allowed_scores if key in scores},
        "critical_blockers": blockers,
        "problems": problems,
        "correction_instruction": str(getattr(qa, "correction_instruction", "") or "")[:1600],
        "no_additional_generation_calls": True,
    }
    reasons = blockers or problems or ["لم تجتز شروط الجودة النهائية."]
    caption = (
        "مسودة للتشخيص — غير معتمدة\n"
        "لا تستخدم كإعلان نهائي.\n"
        f"التقييم الآلي: {report['score_out_of_100']:.2f}/100\n"
        "أسباب الرفض:\n" + "\n".join("- " + text[:190] for text in reasons[:3])
    )[:950]
    mime = str(getattr(image, "mime_type", "") or "image/png").lower()
    extension = {"image/jpeg": "jpg", "image/jpg": "jpg", "image/png": "png",
                 "image/webp": "webp"}.get(mime, "bin")
    outcome = {"image_sent": False, "report_sent": False, "approved": False}
    try:
        send_document(core, chat_id, image.image_bytes,
                      "xpand-UNAPPROVED-diagnostic." + extension, mime, caption)
        outcome["image_sent"] = True
        send_document(
            core, chat_id, json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8"),
            "xpand-UNAPPROVED-quality-report.json", "application/json",
            "تقرير تشخيص المسودة — أسباب الرفض وتقييمات الجودة، وليس موافقة للنشر.",
        )
        outcome["report_sent"] = True
    except Exception as error:
        # A send may have applied before a transport error: never auto-retry it,
        # never spend another image call, and never log a Telegram token/URL.
        outcome["send_error_type"] = type(error).__name__
        print("DIAGNOSTIC_DELIVERY_FAILED | error_type=" + type(error).__name__, flush=True)
    finally:
        candidates.clear()
    return outcome