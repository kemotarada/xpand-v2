"""Text-only STC design continuity, shared by Telegram text and voice routes.

Sessions are isolated by (chat, user), bounded, and expire after two hours.
They intentionally live in worker memory, like the existing pending-style flow.
After a worker restart the user must restate the brief; no context is invented.
"""
import copy
import json
import re
import threading
import time
from types import SimpleNamespace

from xpand_stc_skill_runtime import prompt_direction, clean_public_prompt

VERSION = "stc-design-session-v4.2"
TTL_SECONDS = 7200
MAX_SESSIONS = 256
_sessions = {}
_lock = threading.RLock()

CONSTRAINTS = """This is a text-only STC design task. Never call image tools.
All follow-up ideas obey the loaded STC skill and the user's exclusions.
No text or logos inside the proposed image, no graphic overlays, decorative
lines, glowing routes, particles, holograms, world-map collages or decorative
ribbons. Real architectural edges and physical reflections are allowed.
Do not turn a travel SIM/eSIM service into a metallic bank-sized travel card.
Describe visible service proof. Camera, environment and mechanism must vary
between alternatives, rather than merely changing props or surface materials.
For an ideas-only request, write the title, core_idea and marketing_message
in concise Arabic; camera terminology may be English. Do not write a final prompt.
"""


def norm(text):
    text = str(text or "").lower().translate(str.maketrans("أإآى", "اااي"))
    return re.sub(r"[\u064b-\u065f\u0670]", "", text)


def get_session(chat_id, user_id):
    with _lock:
        now = time.time()
        for key in list(_sessions):
            if now - _sessions[key]["updated"] > TTL_SECONDS:
                del _sessions[key]
        return copy.deepcopy(_sessions.get((str(chat_id), str(user_id))))


def save_session(chat_id, user_id, state):
    with _lock:
        key = (str(chat_id), str(user_id))
        if key not in _sessions and len(_sessions) >= MAX_SESSIONS:
            oldest = min(_sessions, key=lambda k: _sessions[k]["updated"])
            del _sessions[oldest]
        _sessions[key] = copy.deepcopy(dict(state, updated=time.time()))


def wants_ideas(text):
    value = norm(text)
    # A negated final-prompt mention must not turn a brainstorm into a prompt.
    return bool(re.search(r"افكار|فكرتين|ثلاث افكار|\bideas?\b|\bconcepts?\b|brainstorm", value)) and not bool(
        re.search(r"حول.{0,35}(?:برومت|برومبت|prompt)|اكتب.{0,20}برومت.{0,15}(?:للفكرة|للفكره)", value))


def choice_number(text):
    value = norm(text).strip().translate(str.maketrans("١٢٣٤٥", "12345"))
    # Bare choices or explicit selection phrases, never an aspect ratio.
    match = re.fullmatch(r"([1-5])[.!؟]?", value)
    if not match:
        match = re.search(r"(?:اختار|اختر|اختيار|الفكرة|الفكره|الخيار|choose|option)\s*(?:رقم\s*)?([1-5])\b", value)
    if match:
        return int(match.group(1))
    if re.search(r"اختار|اختر|الفكرة|الفكره|الخيار|عدل|choose|option", value) or re.fullmatch(
        r"(?:الاول[ىي]?|الثاني[ةه]?|الثالث[ةه]?|الرابع[ةه]?|الخامس[ةه]?)[.!؟]?", value):
        for i, word in enumerate(("الاول", "الثاني", "الثالث", "الرابع", "الخامس"), 1):
            if word in value:
                return i
    return None


def route_turn(runtime, chat_id, user_id, text):
    """Return a design task or None; ordinary chat and image requests stay intact."""
    value = norm(text)
    state = get_session(chat_id, user_id)
    if value.strip() in {"الغاء التصميم", "انهاء التصميم", "cancel design", "/cancel_design"}:
        with _lock:
            _sessions.pop((str(chat_id), str(user_id)), None)
        return {"reply": "تم إنهاء جلسة التصميم."}
    # Explicit rendering continues through the existing image pipeline.
    if re.search(r"(?:انشئ|ولد|ولّد|صمم|اعمل|ارسم)\s+(?:لي\s*)?(?:الصورة|صورة)|(?:generate|render|create)\s+(?:the |an? )?image", value):
        return None
    if not runtime.is_stc_bank_request(text) and re.search(
        r"لمطعم|لمقهي|لسيارة|لشرك[ةه]|لبنك (?:اخر|ثاني)|لبراند (?:اخر|ثاني)|for (?:a restaurant|another brand)", value):
        return None
    ideas = wants_ideas(text)
    selected = choice_number(text)
    explicit = runtime.is_stc_bank_request(text)
    fresh = bool(re.search(r"طلب جديد|مشروع جديد|تصميم جديد|new brief|new project", value))
    followup = bool(re.search(
        r"الفكرة|الفكره|برومت|برومبت|\bprompt\b|المشهد|التكوين|المنظور|زاوية التصوير|"
        r"اعد تطوير|عدل عليها|طورها|غير الزاوية|نفس الاسلوب|نفس الستايل|"
        r"\b(?:revise|refine|composition|perspective|camera angle|same style)\b", value))
    if explicit and (ideas or runtime.is_stc_prompt_only_request(text)):
        if fresh or not state or not followup:
            state = None
    elif not (state and (ideas or followup or selected or runtime.resolve_stc_style_reply(text)
                        or value.strip() in {"غيرها", "غيره", "طورها", "كمل", "فكرة ثانية", "فكرة اخرى"})):
        return None
    if state is None and not explicit:
        return None
    if selected and state and not state.get("choices"):
        return {"reply": "ما في قائمة أفكار محفوظة للاختيار؛ اطلب عرض الأفكار أولًا."}
    if selected and state and selected > len(state.get("choices", [])):
        return {"reply": "رقم الفكرة خارج القائمة المعروضة؛ اختار رقمًا منها."}
    return {"state": state, "text": text, "mode": "ideas" if ideas else "prompt", "choice": selected}


def concept_allowed(concept):
    if not (getattr(concept, "evaluation_valid", False) and getattr(concept, "quality_gate_passed", False)):
        return False
    # Inspect the proposed scene, not the evaluator's list of risks/rejections.
    scene = norm(" ".join(str(getattr(concept, key, "")) for key in (
        "core_idea", "hero_element", "supporting_elements", "environment", "visual_metaphor")))
    forbidden = r"hologram|particles|neon (?:trail|line)|glowing (?:route|line|path)|world map|ribbon|هولوغرام|بارتكل|جزيئات مضيئة|خريطة العالم|خريطة مضيئة|خطوط مضيئة|شريط حريري"
    return not re.search(forbidden, scene)


def run_turn(runtime, core, chat_id, user_id, task):
    if "reply" in task:
        return task["reply"]
    text, mode = task["text"], task["mode"]
    previous = task.get("state") or {}
    base = previous.get("brief", text)
    # Keep original purpose and last result separate from latest instructions.
    brief = base if not previous else (
        base + "\nLATEST USER REVISION (takes priority):\n" + text)
    style = runtime.detect_stc_visual_style(text) or previous.get("style", "")
    if not style:
        style = runtime.detect_stc_visual_style(brief)
    if not style:
        runtime.remember_pending_stc_style(chat_id=chat_id, user_id=user_id,
            request_text=brief, source_channel="telegram_text")
        return runtime.get_stc_style_question()
    direction = prompt_direction(style)
    selected = task.get("choice")
    chosen = previous.get("choices", [])[selected - 1] if selected else None
    request = brief + "\n" + CONSTRAINTS
    if previous.get("last_answer"):
        request += "\nPREVIOUS DESIGN, FOR REVISION ONLY:\n" + previous["last_answer"][:6000]
    if chosen:
        request += "\nUSER-SELECTED CONCEPT; KEEP ITS MECHANISM:\n" + json.dumps(chosen, ensure_ascii=False)
    if len(request) > 12000:
        raise RuntimeError("سياق التصميم صار طويلًا؛ أرسل طلبًا جديدًا مختصرًا يجمع الفكرة والقيود الحالية، وابدأه بعبارة طلب جديد لبنك STC.")
    # Only a bare selection reuses review. Any revision must be reviewed again.
    bare_selection = chosen and bool(re.fullmatch(
        r"\s*(?:(?:اختار|اختر|choose)\s*)?(?:(?:الفكرة|الفكره|الخيار|option)\s*)?(?:رقم\s*)?(?:[1-5١-٥]|الاول[ىي]?|الثاني[ةه]?|الثالث[ةه]?|الرابع[ةه]?|الخامس[ةه]?)\s*[.!؟]?", norm(text)))
    if bare_selection:
        winner = runtime.concept_from_dict(chosen) if hasattr(runtime, "concept_from_dict") else SimpleNamespace(**chosen)
        response = SimpleNamespace(winner=winner)
        winner_instruction = runtime.build_winner_instruction(response)
        approved = [winner]
    else:
        print(f"▶ {VERSION} route={mode} stage=creative_review", flush=True)
        creative_request, family = runtime.build_creative_request(request, style)
        # The creative brain also loads the canonical skill. These instructions
        # reach it before ideation, not just the final text compiler.
        response = runtime.run_creative_brain(
            user_request=creative_request,
            brand_context={"brand_id": "stc_bank", "benefit_family": family},
            visual_references=[], style_hint=style,
            mode=runtime.CREATIVE_MODE_MASTERPIECE, top_count=3 if mode == "ideas" else 1)
        if not runtime.creative_quality_passed(response):
            raise RuntimeError("الفكرة لم تجتز المراجعة الإبداعية؛ لم يتم توليد صورة أو تسليم برومت غير معتمد.")
        candidates = [response.winner] + list(getattr(response, "top_concepts", []))
        approved, seen = [], set()
        for candidate in candidates:
            fingerprint = str(getattr(candidate, "core_idea", "")).strip()
            if fingerprint and fingerprint not in seen and concept_allowed(candidate):
                seen.add(fingerprint)
                approved.append(candidate)
        if not approved:
            raise RuntimeError("الأفكار خالفت قيود المشهد أو لم تجتز المراجعة؛ أعد طلب تطويرها.")
        response = SimpleNamespace(winner=approved[0])
        winner_instruction = runtime.build_winner_instruction(response)
    if not winner_instruction:
        raise RuntimeError("تعذر تحميل تفاصيل الفكرة المختارة؛ لم يتم توليد صورة.")
    if mode == "ideas":
        approved = approved[:3]
        lines = ["أفكار اجتازت المراجعة ضمن الأسلوب المختار:"]
        if len(approved) < 3:
            lines.append("اجتازت المراجعة " + str(len(approved)) + " من الأفكار فقط؛ لم أُكمل العدد بأفكار غير معتمدة.")
        # Render the reviewed concepts directly: no second writer invents
        # glowing routes or changes the options after their review.
        for index, concept in enumerate(approved, 1):
            lines.append(f"{index}) {concept.title}\nالمشهد: {concept.core_idea}\nالمعنى: {concept.marketing_message}\nزاوية التصوير: {concept.camera_angle}")
        lines.append("اختار رقم الفكرة، أو اطلب تعديلًا عليها.")
        answer = clean_public_prompt("\n\n".join(lines))
        choices = [runtime.concept_to_dict(item) for item in approved]
    else:
        writer = getattr(core, "_xpand_prompt_only_ask", None)
        if not callable(writer):
            raise RuntimeError("مسار كتابة البرومت غير متصل؛ أعد تشغيل الوكيل بعد تثبيت التحديث.")
        answer = clean_public_prompt(writer(chat_id, user_id,
            "STC PROMPT-ONLY TASK. Compile the reviewed winner into one standalone English image prompt. "
            "Preserve its visible benefit proof, action and spatial mechanism; do not invent a new idea. "
            "No scores, reference IDs, file paths or unattached references.\n" + CONSTRAINTS
            + "\n" + direction + "\nUSER BRIEF:\n" + brief + winner_instruction))
        if not answer:
            raise RuntimeError("لم يرجع كاتب البرومت نصًا؛ لم يتم توليد أي صورة.")
        choices = previous.get("choices", [])
    save_session(chat_id, user_id, {"brief": brief, "style": style,
        "choices": choices, "last_answer": answer, "mode": mode})
    print(f"✅ {VERSION} route={mode} reviewed={len(approved)} source={'selection' if bare_selection else 'creative_brain'}", flush=True)
    return answer
