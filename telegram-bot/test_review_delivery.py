import ast
import importlib.util
import inspect
import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Tuple

import pytest


HERE = Path(__file__).resolve().parent


def _load_review_module():
    spec = importlib.util.spec_from_file_location(
        "review_delivery_under_test", HERE / "xpand_review_delivery.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


review = _load_review_module()


@pytest.fixture(autouse=True)
def clean_review_sessions():
    review._REVIEW_SESSIONS.clear()
    yield
    review._REVIEW_SESSIONS.clear()


class Core:
    def __init__(self):
        self.messages = []
        self.actions = []

    def send_message(self, chat_id, text):
        self.messages.append((chat_id, text))

    def send_action(self, chat_id, action):
        self.actions.append((chat_id, action))


def _production(
    score=50,
    *,
    image_bytes=b"original-image",
    passed=False,
    ok=False,
    raw=None,
):
    image = (
        SimpleNamespace(
            image_bytes=image_bytes,
            mime_type="image/png",
            metadata={"existing": "unchanged"},
        )
        if image_bytes is not None
        else None
    )
    qa = SimpleNamespace(
        score=score,
        passed=passed,
        raw={} if raw is None else raw,
        scores={
            "realism": 81,
            "brand_alignment": "72.5",
            "not_allowlisted": 99,
        },
        critical_blockers=["bad logo"],
        problems=["weak hierarchy"],
        correction_instruction="fix composition",
        decision="reject",
    )
    return SimpleNamespace(
        final_image=image,
        qa=qa,
        ok=ok,
        best_score=score,
        telemetry={"secret_token": "TELEMETRY-SECRET"},
        errors=["RAW-PRODUCTION-ERROR"],
    )


def _enable(core, chat_id=101, user_id=101):
    assert review.handle_review_command(
        core, chat_id, user_id, "/xpand_review_on"
    )


def test_review_opt_in_is_private_per_user_and_expires(monkeypatch):
    core = Core()
    now = [1000.0]
    monkeypatch.setattr(review.time, "monotonic", lambda: now[0])

    assert review.handle_review_command(core, 1, 1, "not a command") is False
    assert review.review_enabled(1, 1) is False

    assert review.handle_review_command(core, -77, 1, "/xpand_review_on") is True
    assert review.review_enabled(-77, 1) is False
    assert review.review_enabled(1, 1) is False
    assert "الخاصة" in core.messages[-1][1]

    _enable(core, 1, 1)
    assert review.review_enabled(1, 1) is True
    assert review.review_enabled(2, 2) is False
    assert review.review_enabled(1, 2) is False

    now[0] += review._REVIEW_TTL_SECONDS
    assert review.review_enabled(1, 1) is False
    assert ("1", "1") not in review._REVIEW_SESSIONS


def test_review_off_disables_only_same_private_recipient():
    core = Core()
    _enable(core, 11, 11)
    _enable(core, 22, 22)

    assert review.handle_review_command(core, 11, 11, "/xpand_review_off")
    assert review.review_enabled(11, 11) is False
    assert review.review_enabled(22, 22) is True


def test_collect_keeps_highest_matching_rejected_candidate_without_mutation():
    low = _production(20)
    high = _production(90)
    middle = _production(60)
    original_metadata = dict(high.final_image.metadata)
    candidates = []

    review.collect_rejected_candidate(candidates, low)
    review.collect_rejected_candidate(candidates, high)
    review.collect_rejected_candidate(candidates, middle)

    assert candidates == [high]
    assert candidates[0].qa is high.qa
    assert candidates[0].final_image is high.final_image
    assert high.final_image.metadata == original_metadata
    assert high.ok is False
    assert high.qa.passed is False


@pytest.mark.parametrize(
    "production",
    [
        _production(image_bytes=None),
        _production(image_bytes=b""),
        SimpleNamespace(final_image=SimpleNamespace(image_bytes=b"x"), qa=None, ok=False),
        _production(passed=True),
        _production(ok=True),
        _production(raw={"provider_failure": True, "response": "secret"}),
    ],
)
def test_missing_approved_and_provider_failure_are_not_collected(production):
    sentinel = _production(10)
    candidates = [sentinel]
    review.collect_rejected_candidate(candidates, production)
    assert candidates == [sentinel]


def test_delivery_sends_original_and_allowlisted_unapproved_report_to_same_private_chat():
    core = Core()
    _enable(core, 303, 303)
    production = _production(
        87.25,
        raw={"provider_response": "RAW-QA-SECRET", "provider_failure": False},
    )
    candidates = [production]
    calls = []

    def send_document(*args):
        calls.append(args)

    outcome = review.deliver_rejected_candidate(
        core,
        chat_id=303,
        user_id=303,
        candidates=candidates,
        send_document=send_document,
    )

    assert outcome == {
        "image_sent": True,
        "report_sent": True,
        "approved": False,
    }
    assert candidates == []
    assert len(calls) == 2
    assert calls[0][0] is core and calls[1][0] is core
    assert calls[0][1] == calls[1][1] == 303
    assert calls[0][2] == b"original-image"
    assert "UNAPPROVED" in calls[0][3]
    assert "UNAPPROVED" in calls[1][3]

    report = json.loads(calls[1][2].decode("utf-8"))
    assert report["status"] == "diagnostic_draft_not_approved"
    assert report["approved"] is False
    assert report["qa_passed"] is False
    assert report["no_additional_generation_calls"] is True
    assert report["score_out_of_100"] == 87.25
    assert report["scores"] == {"brand_alignment": 72.5, "realism": 81.0}
    serialized = json.dumps(report, ensure_ascii=False)
    assert "RAW-QA-SECRET" not in serialized
    assert "TELEMETRY-SECRET" not in serialized
    assert "RAW-PRODUCTION-ERROR" not in serialized
    assert "not_allowlisted" not in serialized
    assert production.ok is False
    assert production.qa.passed is False


def test_disabled_other_user_and_group_never_deliver():
    core = Core()
    _enable(core, 41, 41)

    for chat_id, user_id in [(42, 42), (41, 99), (-41, 41)]:
        candidate = [_production()]
        sends = []
        result = review.deliver_rejected_candidate(
            core,
            chat_id=chat_id,
            user_id=user_id,
            candidates=candidate,
            send_document=lambda *args: sends.append(args),
        )
        assert result == {"image_sent": False, "report_sent": False}
        assert sends == []
        assert len(candidate) == 1


@pytest.mark.parametrize(
    ("fail_at", "expected_calls", "image_sent", "report_sent"),
    [(1, 1, False, False), (2, 2, True, False)],
)
def test_send_failure_is_not_retried_and_reports_partial_success(
    fail_at, expected_calls, image_sent, report_sent
):
    core = Core()
    _enable(core, 55, 55)
    candidates = [_production()]
    calls = []

    def failing_send(*args):
        calls.append(args)
        if len(calls) == fail_at:
            raise ConnectionError("transport details must not escape")

    result = review.deliver_rejected_candidate(
        core,
        chat_id=55,
        user_id=55,
        candidates=candidates,
        send_document=failing_send,
    )

    assert len(calls) == expected_calls
    assert result["image_sent"] is image_sent
    assert result["report_sent"] is report_sent
    assert result["approved"] is False
    assert result["send_error_type"] == "ConnectionError"
    assert candidates == []
    assert "transport details must not escape" not in json.dumps(result)


def _extract_function(name):
    source = (HERE / "xpand_image_telegram.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
    )
    module = ast.Module(body=[function], type_ignores=[])
    ast.fix_missing_locations(module)
    return compile(module, str(HERE / "xpand_image_telegram.py"), "exec")


def _masterpiece_namespace(production, run_calls, collect_calls):
    def run_production(**kwargs):
        run_calls.append(kwargs)
        return production

    def collect(candidates, value):
        collect_calls.append((candidates, value))
        review.collect_rejected_candidate(candidates, value)

    namespace = {
        "Any": Any,
        "Dict": Dict,
        "List": List,
        "Tuple": Tuple,
        "MASTERPIECE_MAX_IMAGES": 4,
        "MASTERPIECE_REQUIRE_QA": True,
        "STC_REQUIRE_PRODUCTION_QA": True,
        "PRODUCTION_MODE_MASTERPIECE": "masterpiece",
        "TARGET_OPENAI": "openai",
        "enforce_masterpiece_guard": lambda prepared: {"route": "masterpiece"},
        "clean_text": lambda value, limit=500: str(value)[:limit],
        "safe_dict": lambda value: value if isinstance(value, dict) else {},
        "safe_float": lambda value, default=0: float(value),
        "object_list": lambda value: list(value or []),
        "is_stc_high_alert_prepared": lambda prepared: False,
        "creative_direction_for_index": lambda response, index: ("direction", "camera"),
        "qa_metadata": lambda qa: {
            "evaluated": qa is not None,
            "passed": bool(getattr(qa, "passed", False)),
            "score": getattr(qa, "score", 0),
            "decision": getattr(qa, "decision", ""),
            "critical_blockers": getattr(qa, "critical_blockers", []),
            "problems": getattr(qa, "problems", []),
            "correction_instruction": getattr(qa, "correction_instruction", ""),
        },
        "run_production": run_production,
        "collect_rejected_candidate": collect,
    }
    exec(_extract_function("generate_masterpiece_images"), namespace)
    return namespace


def _prepared():
    return {
        "creative_response": object(),
        "brand_id": "brand",
        "model_brand_context": {},
        "canonical_benefit_family": "benefit",
        "stc_policy_applied": False,
    }


def test_ast_masterpiece_rejection_collected_but_never_approved():
    production = _production(64)
    run_calls, collect_calls, candidates = [], [], []
    namespace = _masterpiece_namespace(production, run_calls, collect_calls)

    images, metadata, errors = namespace["generate_masterpiece_images"](
        core=object(),
        user_id=7,
        request_text="request",
        prepared=_prepared(),
        number=1,
        aspect_ratio="1:1",
        diagnostic_candidates=candidates,
    )

    assert len(run_calls) == 1
    assert collect_calls == [(candidates, production)]
    assert candidates == [production]
    assert images == []
    assert metadata[0]["qa_passed"] is False
    assert errors == ["masterpiece_qa_failed:64.0"]
    assert production.final_image.metadata == {"existing": "unchanged"}


def test_ast_masterpiece_default_is_backward_compatible_and_passing_qa_unchanged():
    approved = _production(96, passed=True, ok=True)
    run_calls, collect_calls = [], []
    namespace = _masterpiece_namespace(approved, run_calls, collect_calls)
    function = namespace["generate_masterpiece_images"]

    assert inspect.signature(function).parameters["diagnostic_candidates"].default is None
    images, metadata, errors = function(
        core=object(),
        user_id=8,
        request_text="request",
        prepared=_prepared(),
        number=1,
        aspect_ratio="1:1",
    )

    assert len(run_calls) == 1
    assert collect_calls == []
    assert images == [approved.final_image]
    assert metadata[0]["qa_passed"] is True
    assert errors == []
    assert approved.final_image.metadata["qa_passed"] is True


def test_ast_generate_and_deliver_diagnostic_return_skips_fallback(monkeypatch):
    session_module = types.ModuleType("xpand_stc_design_session")
    session_module.wants_ideas = lambda text: False
    session_module.route_turn = lambda *args: None
    session_module.run_turn = lambda *args: None
    monkeypatch.setitem(sys.modules, "xpand_stc_design_session", session_module)

    candidate = _production(70)
    calls = {"masterpiece": 0, "deliver": 0, "fallback": 0}

    def generate_masterpiece_images(**kwargs):
        calls["masterpiece"] += 1
        kwargs["diagnostic_candidates"].append(candidate)
        return [], [{"qa_passed": False}], ["masterpiece_qa_failed:70.0"]

    def deliver(*args, **kwargs):
        calls["deliver"] += 1
        assert kwargs["chat_id"] == kwargs["user_id"] == 909
        assert kwargs["candidates"] == [candidate]
        return {"image_sent": True, "report_sent": True, "approved": False}

    def forbidden_fallback(*args, **kwargs):
        calls["fallback"] += 1
        raise AssertionError("normal/fallback image generation must not run")

    prepared = {
        "final_prompt": "final",
        "brand_id": "brand",
        "canonical_benefit_family": "",
        "creative_mode": "masterpiece",
        "creative_response": None,
        "references": [],
        "campaign_required": False,
        "campaign_validated": False,
        "stc_policy_applied": False,
    }
    namespace = {
        "Any": Any,
        "Dict": Dict,
        "List": List,
        "Tuple": Tuple,
        "CREATIVE_MODE_MASTERPIECE": "masterpiece",
        "TARGET_OPENAI": "openai",
        "extract_image_prompt": lambda text: "prompt",
        "stc_style_question_needed": lambda prompt: False,
        "get_stc_style_question": lambda: "",
        "is_stc_prompt_only_request": lambda text: False,
        "is_stc_bank_request": lambda text: False,
        "detect_requested_image_count": lambda prompt: 1,
        "detect_aspect_ratio": lambda prompt: "1:1",
        "detect_image_size": lambda prompt: "1024x1024",
        "prepare_generation_input": lambda core, user, prompt: prepared,
        "clean_text": lambda value, limit=500: str(value or "")[:limit],
        "creative_runtime_state": lambda response: {
            "state": "",
            "technical_failure": False,
            "quality_gate_evaluated": True,
            "quality_gate_passed": False,
        },
        "safe_float": lambda value, default=0: float(value),
        "is_stc_high_alert_prepared": lambda prepared: False,
        "review_enabled": lambda chat, user: chat == user == 909,
        "enforce_masterpiece_guard": lambda prepared: {"route": "masterpiece"},
        "generate_masterpiece_images": generate_masterpiece_images,
        "classify_masterpiece_failure": lambda metadata, errors: "quality_failure",
        "deliver_rejected_candidate": deliver,
        "send_document_bytes": object(),
        "generate_image": forbidden_fallback,
    }
    exec(_extract_function("generate_and_deliver"), namespace)

    result = namespace["generate_and_deliver"](Core(), 909, 909, "make image")

    assert result["output_kind"] == "diagnostic_draft"
    assert result["approved"] is False
    assert result["qa_passed"] is False
    assert result["images"] == []
    assert calls == {"masterpiece": 1, "deliver": 1, "fallback": 0}