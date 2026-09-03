from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse


class XPANDOpenAIBudgetError(RuntimeError):
    pass


_LOCK = threading.RLock()
_INSTALLED = False


def _truthy(name: str, default: str = "false") -> bool:
    return str(os.environ.get(name, default)).strip().lower() in {
        "1", "true", "yes", "on"
    }


def openai_enabled() -> bool:
    return _truthy("XPAND_OPENAI_ENABLED", "false")


def daily_limit_usd() -> float:
    try:
        return max(0.0, float(os.environ.get("XPAND_OPENAI_DAILY_LIMIT_USD", "2.00")))
    except Exception:
        return 2.0


def _ledger_path() -> Path:
    custom = str(os.environ.get("XPAND_OPENAI_LEDGER_PATH", "")).strip()
    return Path(custom or "/tmp/xpand_openai_daily_budget.json")


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _load() -> Dict[str, Any]:
    path = _ledger_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and data.get("date") == _today():
            return data
    except Exception:
        pass
    return {"date": _today(), "reserved_usd": 0.0, "requests": 0}


def _save(data: Dict[str, Any]) -> None:
    path = _ledger_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    temp.replace(path)


def _estimate_reservation(url: str, kwargs: Dict[str, Any]) -> float:
    payload = kwargs.get("json") if isinstance(kwargs.get("json"), dict) else {}
    data = kwargs.get("data") if isinstance(kwargs.get("data"), dict) else {}
    model = str(payload.get("model") or data.get("model") or "").lower()
    path = urlparse(url).path.lower()
    if "/images/" in path or "image" in model:
        quality = str(payload.get("quality") or data.get("quality") or "high").lower()
        count = int(payload.get("n") or data.get("n") or 1)
        per_image = {"low": 0.04, "medium": 0.10, "high": 0.25, "auto": 0.25}.get(quality, 0.25)
        return max(0.01, per_image * max(1, count))
    max_tokens = int(payload.get("max_output_tokens") or 2000)
    return max(0.01, min(0.50, 0.01 + (max_tokens / 1_000_000.0) * 20.0))


def _reserve_postgres(reservation: float, limit: float) -> bool:
    database_url = str(os.environ.get("DATABASE_URL", "")).strip()
    if not database_url:
        return False
    try:
        import psycopg
        with psycopg.connect(database_url) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS xpand_openai_daily_budget (
                        usage_date DATE PRIMARY KEY,
                        reserved_usd DOUBLE PRECISION NOT NULL DEFAULT 0,
                        request_count INTEGER NOT NULL DEFAULT 0,
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """
                )
                cursor.execute(
                    "INSERT INTO xpand_openai_daily_budget (usage_date) VALUES (CURRENT_DATE) "
                    "ON CONFLICT (usage_date) DO NOTHING"
                )
                cursor.execute(
                    "SELECT reserved_usd FROM xpand_openai_daily_budget "
                    "WHERE usage_date=CURRENT_DATE FOR UPDATE"
                )
                spent = float(cursor.fetchone()[0] or 0.0)
                if spent + reservation > limit:
                    raise XPANDOpenAIBudgetError(
                        f"وصل XPAND إلى حد OpenAI اليومي (${limit:.2f}). "
                        "تم إيقاف أي استدعاء OpenAI، وسيبقى Gemini متاحًا."
                    )
                cursor.execute(
                    "UPDATE xpand_openai_daily_budget SET reserved_usd=%s, "
                    "request_count=request_count+1, updated_at=NOW() WHERE usage_date=CURRENT_DATE",
                    (round(spent + reservation, 6),),
                )
            connection.commit()
        return True
    except XPANDOpenAIBudgetError:
        raise
    except Exception as error:
        if _truthy("XPAND_OPENAI_BUDGET_FAIL_CLOSED", "true"):
            raise XPANDOpenAIBudgetError(
                "تعذر التحقق من ميزانية OpenAI في PostgreSQL؛ تم منع الطلب احتياطيًا. "
                + str(error)[:500]
            )
        return False


def reserve_openai(url: str, kwargs: Dict[str, Any]) -> None:
    if not openai_enabled():
        raise XPANDOpenAIBudgetError(
            "تم منع استدعاء OpenAI لأن XPAND_OPENAI_ENABLED=false. "
            "XPAND سيستخدم Gemini بدلًا منه."
        )
    reservation = _estimate_reservation(url, kwargs)
    limit = daily_limit_usd()
    if _reserve_postgres(reservation, limit):
        return
    with _LOCK:
        ledger = _load()
        spent = float(ledger.get("reserved_usd", 0.0) or 0.0)
        if spent + reservation > limit:
            raise XPANDOpenAIBudgetError(
                f"وصل XPAND إلى حد OpenAI اليومي (${limit:.2f}). "
                "تم إيقاف أي استدعاء OpenAI، وسيبقى Gemini متاحًا."
            )
        ledger["reserved_usd"] = round(spent + reservation, 6)
        ledger["requests"] = int(ledger.get("requests", 0) or 0) + 1
        _save(ledger)


def budget_status() -> Dict[str, Any]:
    database_url = str(os.environ.get("DATABASE_URL", "")).strip()
    if database_url:
        try:
            import psycopg
            with psycopg.connect(database_url) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT reserved_usd, request_count FROM xpand_openai_daily_budget "
                        "WHERE usage_date=CURRENT_DATE"
                    )
                    row = cursor.fetchone()
            data = {
                "date": _today(),
                "reserved_usd": float(row[0] or 0.0) if row else 0.0,
                "requests": int(row[1] or 0) if row else 0,
            }
        except Exception:
            data = _load()
    else:
        data = _load()
    data["enabled"] = openai_enabled()
    data["limit_usd"] = daily_limit_usd()
    data["remaining_usd"] = max(
        0.0, data["limit_usd"] - float(data.get("reserved_usd", 0.0) or 0.0)
    )
    return data


def install_requests_guard() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    import requests

    original = requests.sessions.Session.request

    def guarded_request(session, method, url, *args, **kwargs):
        host = (urlparse(str(url)).hostname or "").lower()
        if host == "api.openai.com" or host.endswith(".openai.com"):
            reserve_openai(str(url), kwargs)
        return original(session, method, url, *args, **kwargs)

    requests.sessions.Session.request = guarded_request
    _INSTALLED = True
