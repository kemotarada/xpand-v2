"""XPAND Telegram advertising-reference intake.

Receives one image or a Telegram media album, runs the existing visual
intelligence engine on every image, synthesizes shared campaign DNA, and
persists both the references and generation rules for future STC work.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from xpand_brand_memory import (
    get_brand_profile,
    safe_brand_id,
    save_visual_reference,
    upsert_brand_profile,
)
from xpand_image_engine import call_openai_director
from xpand_visual_intelligence import analyze_visual_reference, extract_json_object

try:
    from xpand_brand_research import detect_brand
except Exception:
    detect_brand = None

_VERSION = "1.0"
_ALBUM_WAIT_SECONDS = 3.5
_ALBUMS: Dict[Tuple[str, str], Dict[str, Any]] = {}
_ALBUM_LOCK = threading.RLock()


def _text(value: Any, limit: int = 1800) -> str:
    if value is None:
        return ""
    return str(value).strip()[:limit]


def _bounded(value: Any, depth: int = 0) -> Any:
    if depth >= 3:
        return _text(value, 700)
    if isinstance(value, dict):
        return {str(k): _bounded(v, depth + 1) for k, v in list(value.items())[:32]}
    if isinstance(value, list):
        return [_bounded(v, depth + 1) for v in value[:24]]
    if isinstance(value, str):
        return value[:1600]
    return value


def _image_descriptor(message: Dict[str, Any]) -> Dict[str, Any] | None:
    photo = message.get("photo")
    if isinstance(photo, list) and photo:
        item = photo[-1]
        if isinstance(item, dict) and item.get("file_id"):
            return {
                "file_id": item.get("file_id", ""),
                "file_unique_id": item.get("file_unique_id", ""),
                "mime_type": "image/jpeg",
            }
    document = message.get("document")
    if isinstance(document, dict) and document.get("file_id"):
        mime = _text(document.get("mime_type"), 100).lower()
        if mime.startswith("image/"):
            return {
                "file_id": document.get("file_id", ""),
                "file_unique_id": document.get("file_unique_id", ""),
                "mime_type": mime,
            }
    return None


def _brand_for_caption(caption: str) -> str:
    source = _text(caption, 2000).lower()
    if any(marker in source for marker in ("stc", "stc bank", "بنك اس تي سي", "بنك stc", "بنك", "بطاقة")):
        return "stc_bank"
    if detect_brand:
        try:
            detected = safe_brand_id(detect_brand(caption))
            if detected:
                return detected
        except Exception:
            pass
    # This intake is intentionally STC-first; a caption can explicitly
    # name another brand before the image is processed.
    return "stc_bank"


def _download(core: Any, message: Dict[str, Any]) -> Dict[str, Any] | None:
    descriptor = _image_descriptor(message)
    if not descriptor:
        return None
    raw = core.get_telegram_file_bytes(descriptor["file_id"])
    if not raw:
        raise RuntimeError("Telegram returned an empty image")
    descriptor["image_bytes"] = raw
    return descriptor


def _analysis_digest(item: Dict[str, Any]) -> Dict[str, Any]:
    keys = (
        "summary", "observed_facts", "inferred_rules",
        "single_reference_limitations", "content_classification",
        "visual_hook", "advertising_strategy", "camera", "perspective",
        "composition", "typography_system", "lighting", "materials",
        "color_palette", "art_direction", "human_direction",
        "relationships", "visual_success_reasons", "generation_risks",
        "visual_fingerprint", "product_lock",
    )
    return {key: _bounded(item.get(key)) for key in keys if item.get(key)}


def _synthesize(analyses: List[Dict[str, Any]], brand_id: str) -> Dict[str, Any]:
    source = [_analysis_digest(item) for item in analyses]
    prompt = (
        "You are XPAND Campaign Visual Intelligence.\n"
        "Synthesize the following individual advertising-image analyses into a "
        "professional comparative campaign analysis for " + brand_id + ".\n"
        "Do not transcribe or reproduce sensitive financial text. Separate "
        "observed repeated evidence from inference, interpretation and uncertainty. "
        "Only repeated patterns may become brand rules. Return JSON only, with values "
        "in Arabic where natural.\n\n"
        "Required JSON shape:\n"
        "{\n"
        "  \"executive_summary\": \"\",\n"
        "  \"shared_visual_dna\": {\"composition\": \"\", \"palette\": \"\", \"lighting\": \"\", \"camera\": \"\", \"materials\": \"\", \"typography\": \"\", \"art_direction\": \"\"},\n"
        "  \"shared_advertising_strategy\": {\"objective\": \"\", \"audience\": \"\", \"persuasion\": \"\", \"emotional_territory\": \"\"},\n"
        "  \"repeated_rules\": [],\n"
        "  \"image_specific_differences\": [],\n"
        "  \"observed_facts\": [],\n"
        "  \"inferences\": [],\n"
        "  \"uncertainties\": [],\n"
        "  \"generation_reference\": {\"preserve\": [], \"adapt\": [], \"avoid\": [], \"reconstruction_prompt\": \"\"},\n"
        "  \"generation_rules\": []\n"
        "}\n\n"
        "INDIVIDUAL ANALYSES:\n" + json.dumps(source, ensure_ascii=False)
    )
    try:
        raw = call_openai_director(prompt, json_mode=True)
        result = extract_json_object(raw)
        if isinstance(result, dict) and result:
            return result
    except Exception as error:
        print("⚠️ XPAND campaign synthesis:", _text(error, 900))
    fingerprints = []
    rules = []
    for item in analyses:
        fp = item.get("visual_fingerprint", {})
        if isinstance(fp, dict):
            fingerprints.extend(fp.get("transferable_rules", [])[:8])
        rules.extend(item.get("inferred_rules", [])[:5])
    return {
        "executive_summary": "تم حفظ التحليلات الفردية؛ تعذر توليد المقارنة الآلية الكاملة.",
        "shared_visual_dna": {},
        "shared_advertising_strategy": {},
        "repeated_rules": list(dict.fromkeys([_text(x, 800) for x in rules if _text(x)]))[:30],
        "image_specific_differences": [],
        "observed_facts": [],
        "inferences": [],
        "uncertainties": ["لم يكتمل توليف المقارنة بسبب تعذر استجابة نموذج التوليد."],
        "generation_reference": {"preserve": fingerprints[:20], "adapt": [], "avoid": [], "reconstruction_prompt": ""},
        "generation_rules": fingerprints[:20],
    }


def _persist(core: Any, user_id: Any, brand_id: str, analyses: List[Dict[str, Any]], synthesis: Dict[str, Any], set_id: str) -> None:
    profile = get_brand_profile(core, user_id, brand_id) or {}
    rules = list(profile.get("visual_dna", [])) if isinstance(profile.get("visual_dna"), list) else []
    rules.extend(synthesis.get("generation_rules", []) if isinstance(synthesis.get("generation_rules"), list) else [])
    generation = synthesis.get("generation_reference", {})
    if isinstance(generation, dict):
        for key in ("preserve", "adapt", "avoid"):
            values = generation.get(key, [])
            if isinstance(values, list):
                rules.extend(values)
    deduped = []
    for rule in rules:
        value = _text(rule, 1000)
        if value and value not in deduped:
            deduped.append(value)
    profile["visual_dna"] = deduped[-120:]
    profile["latest_uploaded_campaign_analysis"] = _bounded(synthesis)
    profile["latest_uploaded_campaign_analysis_meta"] = {
        "set_id": set_id, "image_count": len(analyses),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": "telegram_user_upload",
    }
    upsert_brand_profile(core, user_id, brand_id, "STC Bank KSA" if brand_id == "stc_bank" else brand_id, profile)


def _format_value(value: Any, indent: str = "") -> List[str]:
    if isinstance(value, dict):
        lines = []
        for key, child in list(value.items())[:24]:
            label = str(key).replace("_", " ")
            if isinstance(child, (dict, list)):
                lines.append(indent + "• " + label + ":")
                lines.extend(_format_value(child, indent + "  "))
            elif _text(child):
                lines.append(indent + "• " + label + ": " + _text(child, 1000))
        return lines
    if isinstance(value, list):
        return [indent + "• " + _text(item, 1000) for item in value[:24] if _text(item)]
    return [indent + _text(value, 1200)] if _text(value) else []


def _format_report(analyses: List[Dict[str, Any]], synthesis: Dict[str, Any], brand_id: str) -> str:
    lines = ["✅ اكتمل تحليل المرجع الإعلاني", "", f"العلامة: {brand_id} | عدد الصور: {len(analyses)}", "", "━━ التحليل الفردي لكل صورة ━━"]
    sections = ("summary", "observed_facts", "inferred_rules", "advertising_strategy", "camera", "perspective", "composition", "typography_system", "lighting", "materials", "color_palette", "art_direction", "human_direction", "visual_fingerprint", "generation_risks")
    for index, item in enumerate(analyses, 1):
        lines.extend(["", f"الصورة {index}"])
        for key in sections:
            value = item.get(key)
            if value:
                lines.append("" + key.replace("_", " ") + ":")
                lines.extend(_format_value(value, "  "))
    lines.extend(["", "━━ المقارنة والـDNA المشترك ━━"])
    for key, value in synthesis.items():
        if value:
            lines.append("" + str(key).replace("_", " ") + ":")
            lines.extend(_format_value(value, "  "))
    lines.extend(["", "تم حفظ كل صورة كمرجع بصري، وحُفظت المقارنة كذاكرة حملة STC Bank. سيستخدمها XPAND تلقائيًا في طلبات الصور القادمة مع الحفاظ على الأصالة وعدم نسخ الإعلان."])
    return "\n".join(lines)


def _process_batch(core: Any, chat_id: Any, user_id: Any, messages: List[Dict[str, Any]], caption: str, set_id: str) -> None:
    core.send_action(chat_id, "typing")
    brand_id = _brand_for_caption(caption)
    analyses: List[Dict[str, Any]] = []
    for index, message in enumerate(messages, 1):
        try:
            image = _download(core, message)
            if not image:
                continue
            note = caption or "STC Bank advertising campaign reference set"
            dna = analyze_visual_reference(
                image["image_bytes"], image["mime_type"],
                user_note=note,
                brand_context="This is a user-supplied advertising reference for future original STC Bank campaign generation.",
                role_hint="campaign_reference",
                source_metadata={
                    "source_type": "telegram_user_upload",
                    "source_authority": "user_supplied",
                    "media_group_id": message.get("media_group_id", ""),
                    "image_index": index,
                    "campaign_set_id": set_id,
                },
            )
            save_visual_reference(
                core, user_id, brand_id=brand_id,
                telegram_file_id=image.get("file_id", ""),
                telegram_file_unique_id=image.get("file_unique_id", ""),
                reference_role="campaign_reference", user_note=note, dna=dna,
                product_lock=dna.get("product_lock", {}),
                source_metadata={
                    "source_type": "telegram_user_upload",
                    "source_authority": "user_supplied",
                    "media_group_id": message.get("media_group_id", ""),
                    "campaign_set_id": set_id,
                    "image_fingerprint": dna.get("image_fingerprint_sha256", ""),
                },
            )
            analyses.append(dna)
        except Exception as error:
            print("⚠️ XPAND image analysis:", _text(error, 1200))
    if not analyses:
        core.send_message(chat_id, "لم أستطع قراءة أي صورة صالحة من المجموعة. ابعث الصور مرة ثانية بصيغة JPG أو PNG.")
        return
    synthesis = _synthesize(analyses, brand_id)
    try:
        _persist(core, user_id, brand_id, analyses, synthesis, set_id)
    except Exception as error:
        print("⚠️ XPAND campaign memory:", _text(error, 1200))
    core.send_message(chat_id, _format_report(analyses, synthesis, brand_id))


def _flush_album(core: Any, key: Tuple[str, str]) -> None:
    with _ALBUM_LOCK:
        state = _ALBUMS.pop(key, None)
    if not state:
        return
    _process_batch(core, state["chat_id"], state["user_id"], state["messages"], state.get("caption", ""), state["set_id"])


def _handle(core: Any, chat_id: Any, user_id: Any, message: Dict[str, Any]) -> bool:
    descriptor = _image_descriptor(message)
    if not descriptor:
        return False
    group_id = _text(message.get("media_group_id"), 200)
    if group_id:
        key = (str(chat_id), group_id)
        with _ALBUM_LOCK:
            state = _ALBUMS.setdefault(key, {
                "chat_id": chat_id, "user_id": user_id, "messages": [],
                "caption": _text(message.get("caption"), 3000),
                "set_id": "telegram-" + group_id,
            })
            if message.get("caption"):
                state["caption"] = _text(message.get("caption"), 3000)
            state["messages"].append(message)
            old_timer = state.get("timer")
            if old_timer:
                old_timer.cancel()
            timer = threading.Timer(_ALBUM_WAIT_SECONDS, _flush_album, args=(core, key))
            timer.daemon = True
            state["timer"] = timer
            first = len(state["messages"]) == 1
            timer.start()
        if first:
            core.send_message(chat_id, "استلمت مجموعة الصور. سأحلل كل صورة بالتفصيل ثم أستخرج الـDNA الإعلاني المشترك وأحفظه لطلبات STC Bank القادمة.")
        return True
    _process_batch(core, chat_id, user_id, [message], _text(message.get("caption"), 3000), "telegram-single-" + _text(message.get("message_id"), 80))
    return True


def install(core: Any) -> Dict[str, Any]:
    if getattr(core, "_XPAND_VISUAL_REFERENCE_INTAKE_INSTALLED", False):
        return {"ok": True, "already_installed": True, "version": _VERSION}
    core.handle_image_message = lambda chat_id, user_id, message: _handle(core, chat_id, user_id, message)
    core._XPAND_VISUAL_REFERENCE_INTAKE_INSTALLED = True
    print("✅ XPAND multi-image advertising reference intake: READY")
    return {"ok": True, "version": _VERSION, "multi_image": True}
