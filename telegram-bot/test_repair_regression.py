import ast
import json
import types
import unittest
from pathlib import Path


SOURCE_PATH = Path(__file__).with_name("xpand_production_engine.py")
SOURCE = SOURCE_PATH.read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def load_functions(*names, extra=None):
    selected = [
        node
        for node in TREE.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in names
    ]
    namespace = {
        "Optional": object,
        "Sequence": object,
        "QAEvaluation": object,
        "CompiledPrompt": object,
        "ProductionReference": object,
        "safe_dict": lambda value: value if isinstance(value, dict) else {},
        "clamp_score": lambda value: max(0.0, min(100.0, float(value))),
        "clean_text": lambda value, limit: str(value or "").strip()[:limit],
    }
    namespace.update(extra or {})
    module = ast.Module(
        body=[
            ast.ImportFrom(
                module="__future__",
                names=[ast.alias(name="annotations")],
                level=0,
            ),
            *selected,
        ],
        type_ignores=[],
    )
    ast.fix_missing_locations(module)
    exec(compile(module, str(SOURCE_PATH), "exec"), namespace)
    return namespace


def qa(**overrides):
    values = {
        "score": 84.2,
        "scores": {"text_logo_compliance": 25.0},
        "critical_blockers": ["Remove generated logos and readable text."],
        "problems": [],
        "correction_instruction": "Remove marks from the card.",
        "raw": {"_xpand_flags": {"unwanted_text_or_logo": True}},
    }
    values.update(overrides)
    return types.SimpleNamespace(**values)


class RepairRegressionTests(unittest.TestCase):
    def test_source_parses(self):
        self.assertIsInstance(TREE, ast.Module)

    def test_text_logo_failure_detection_is_conservative(self):
        namespace = load_functions("qa_flags_text_logo_failure")
        detect = namespace["qa_flags_text_logo_failure"]

        self.assertTrue(detect(qa()))
        self.assertTrue(
            detect(
                qa(
                    scores={"text_logo_compliance": 100.0},
                    critical_blockers=["Readable lettering remains on screen"],
                    raw={"_xpand_flags": {}},
                )
            )
        )
        self.assertFalse(
            detect(
                qa(
                    scores={"text_logo_compliance": 100.0},
                    critical_blockers=[],
                    problems=[],
                    raw={"_xpand_flags": {}},
                )
            )
        )

    def test_surgical_prompt_uses_failed_final_without_references(self):
        def no_reference_manifest(*args, **kwargs):
            raise AssertionError("brand references must not be described")

        namespace = load_functions(
            "fit_prompt_for_api",
            "fit_prompt_with_immutable_locks",
            "qa_flags_text_logo_failure",
            "qa_flags_copy_space_failure",
            "build_final_repair_prompt",
            extra={
                "reference_role_manifest": no_reference_manifest,
                "qa_feedback_summary": lambda value: "QA failure",
                "build_immutable_final_locks": (
                    lambda **kwargs: (
                        "LOCK authority="
                        + str(kwargs["reference_authority"])
                        + "\n"
                        + ("BASE FINAL LOCK. " * 230)
                        + "\nEND_BASE_FINAL_LOCK"
                    )
                ),
                "CORRECTION_PROMPT_BUDGET": 7600,
                "IMMUTABLE_LOCK_SENTINEL": (
                    "XPAND_IMMUTABLE_FINAL_LOCKS_V601"
                ),
                "compact_json": (
                    lambda value, limit: json.dumps(value)[:limit]
                ),
            },
        )

        correction_marker = (
            "REMOVE_DIAGNOSED_CARD_MARKS_WITHOUT_REDESIGN"
        )
        blocker_marker = (
            "BLOCKER_REMOVE_READABLE_TEXT_AND_LOGOS"
        )
        long_request = (
            "STC merchant campaign connecting physical POS acceptance "
            "with e-commerce checkout in one premium Saudi scene; "
            "preserve believable hardware, intentional camera, integrated "
            "copy space, restrained purple light and photographic materials. "
            * 24
        )
        prompt = namespace["build_final_repair_prompt"](
            qa=qa(
                correction_instruction=correction_marker,
                critical_blockers=[blocker_marker],
            ),
            compiled=types.SimpleNamespace(
                prompt=(
                    "Approved campaign contract with photographic detail. "
                    * 180
                )
            ),
            original_request=long_request,
            references=[object()],
            aspect_ratio="4:5",
            requested_size="2K",
            action="targeted_repair",
        )

        self.assertIn("PRIMARY AND ONLY", prompt)
        self.assertIn("Preserve the already-good advertising message", prompt)
        self.assertIn("camera, perspective", prompt)
        self.assertIn("fake banking UI", prompt)
        self.assertIn("No Images 2+ are attached", prompt)
        self.assertIn("authority=False", prompt)
        self.assertLessEqual(len(prompt), 7600)
        self.assertIn("[XPAND COMPACTED", prompt)
        sentinel_at = prompt.index(
            "XPAND_IMMUTABLE_FINAL_LOCKS_V601"
        )
        self.assertGreater(
            prompt.index("XPAND_REPAIR_SCOPE_V601"),
            sentinel_at,
        )
        self.assertGreater(prompt.index(correction_marker), sentinel_at)
        self.assertGreater(prompt.index(blocker_marker), sentinel_at)
        self.assertIn("END_XPAND_REPAIR_SCOPE_V601", prompt)

    def test_mixed_text_logo_and_copy_space_allows_bounded_reframe(self):
        namespace = load_functions(
            "fit_prompt_for_api",
            "fit_prompt_with_immutable_locks",
            "qa_flags_text_logo_failure",
            "qa_flags_copy_space_failure",
            "build_final_repair_prompt",
            extra={
                "reference_role_manifest": (
                    lambda *args, **kwargs: "must not be reached"
                ),
                "qa_feedback_summary": lambda value: "mixed QA failure",
                "build_immutable_final_locks": (
                    lambda **kwargs: (
                        "NO artificial blank panel\n"
                        + ("BASE COMPOSITION LOCK. " * 190)
                        + "\nEND_BASE_COMPOSITION_LOCK"
                    )
                ),
                "CORRECTION_PROMPT_BUDGET": 7600,
                "IMMUTABLE_LOCK_SENTINEL": (
                    "XPAND_IMMUTABLE_FINAL_LOCKS_V601"
                ),
                "compact_json": (
                    lambda value, limit: json.dumps(value)[:limit]
                ),
            },
        )
        correction_marker = (
            "MIXED_REMOVE_MARKS_AND_TIGHTEN_COPY_SPACE"
        )
        blocker_marker = (
            "MIXED_BLOCKER_TEXT_LOGO_AND_EMPTY_SPACE"
        )
        long_request = (
            "STC merchant ecosystem campaign showing online and physical "
            "payment acceptance together without readable interfaces; "
            "retain the premium established scene while integrating useful "
            "copy space rather than an artificial empty upper panel. "
            * 24
        )
        mixed = qa(
            scores={
                "text_logo_compliance": 25.0,
                "copy_space_composition": 70.0,
                "advertising_readiness": 76.0,
            },
            critical_blockers=[
                blocker_marker,
                "Remove all generated logos, symbols and readable text from the card and laptop screen before release.",
                "stc_advertising_readiness_below_84",
                "stc_text_logo_compliance_below_95",
                "stc_copy_space_composition_below_80",
                "stc_excessive_empty_copy_space",
                "stc_unwanted_text_or_logo",
            ],
            raw={
                "_xpand_flags": {
                    "unwanted_text_or_logo": True,
                    "excessive_empty_copy_space": True,
                }
            },
            correction_instruction=correction_marker,
        )

        prompt = namespace["build_final_repair_prompt"](
            qa=mixed,
            compiled=types.SimpleNamespace(
                prompt=(
                    "Approved mixed-channel campaign contract. "
                    * 190
                )
            ),
            original_request=long_request,
            references=[object()],
            aspect_ratio="4:5",
            requested_size="2K",
            action="targeted_repair",
        )

        self.assertIn("narrowly bounded", prompt)
        self.assertIn("minimally crop, reframe, scale", prompt)
        self.assertIn("Do not create or", prompt)
        self.assertIn("expand empty space", prompt)
        self.assertIn("No Images 2+ are attached", prompt)
        self.assertNotIn(
            "Preserve the existing composition. Do not recompose",
            prompt,
        )
        self.assertLessEqual(len(prompt), 7600)
        sentinel_at = prompt.index(
            "XPAND_IMMUTABLE_FINAL_LOCKS_V601"
        )
        self.assertGreater(prompt.index(correction_marker), sentinel_at)
        self.assertGreater(prompt.index(blocker_marker), sentinel_at)
        self.assertGreater(
            prompt.index("REPAIR MODE — IMMUTABLE"),
            sentinel_at,
        )
        self.assertIn("END_XPAND_REPAIR_SCOPE_V601", prompt)

    def test_preview_blocker_is_in_immutable_final_corrections(self):
        namespace = load_functions(
            "preview_blocker_corrections",
            "build_final_renderer_prompt",
            extra={
                "is_stc_bank_request": lambda request: True,
                "build_stc_visual_constitution": lambda request: "constitution",
                "reference_role_manifest": lambda refs, **kwargs: "manifest",
                "qa_feedback_summary": lambda value: "audit",
                "build_immutable_final_locks": lambda **kwargs: "FINAL LOCKS",
                # Simulate total loss of the compressible core.
                "fit_prompt_with_immutable_locks": (
                    lambda core, locks, **kwargs: locks
                ),
                "FINAL_PROMPT_BUDGET": 8800,
            },
        )

        prompt = namespace["build_final_renderer_prompt"](
            compiled=types.SimpleNamespace(prompt="approved"),
            original_request="STC campaign",
            preview_qa=qa(
                critical_blockers=[
                    "Generated text and brand marks violate image-only mandate."
                ]
            ),
            references=[],
            aspect_ratio="4:5",
            requested_size="2K",
        )

        self.assertIn("PREVIEW BLOCKER CORRECTIONS", prompt)
        self.assertIn("Generated text and brand marks", prompt)
        self.assertIn("FINAL LOCKS", prompt)

    def test_repair_edit_wiring_uses_primary_candidate_and_zero_refs(self):
        run_production = next(
            node
            for node in TREE.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "run_production"
        )
        calls = [
            node
            for node in ast.walk(run_production)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "openai_multi_reference_edit"
        ]
        self.assertGreaterEqual(len(calls), 2)
        repair_call = calls[-1]
        keywords = {
            item.arg: ast.unparse(item.value)
            for item in repair_call.keywords
        }
        self.assertEqual(keywords["working_image"], "first_final")
        self.assertEqual(keywords["references"], "repair_refs")
        self.assertEqual(keywords["max_reference_images"], "len(repair_refs)")

        assignments = [
            node
            for node in ast.walk(run_production)
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name)
                and target.id == "repair_refs"
                for target in node.targets
            )
        ]
        self.assertEqual(len(assignments), 1)
        rendered = ast.unparse(assignments[0].value)
        self.assertIn("[] if text_logo_surgical else", rendered)

    def test_repair_prompt_build_is_inside_classified_repair_try(self):
        run_production = next(
            node
            for node in TREE.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "run_production"
        )
        prompt_calls = [
            node
            for node in ast.walk(run_production)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "build_final_repair_prompt"
        ]
        self.assertEqual(len(prompt_calls), 1)
        repair_try = next(
            node
            for node in ast.walk(run_production)
            if isinstance(node, ast.Try)
            and prompt_calls[0] in list(ast.walk(node))
        )
        rendered = ast.unparse(repair_try)
        self.assertIn('"repair_prompt_build"', SOURCE)
        self.assertIn("'phase': repair_phase", rendered)
        self.assertIn("'provider': FINAL_IMAGE_MODEL", rendered)
        self.assertIn("'final_qa': final_qa_log", rendered)
        self.assertIn("telemetry['final_repair_error']", rendered)
        self.assertIn("Original GPT-Image-2 final preserved", rendered)
        self.assertIn("FINAL_REPAIR_FAILURE", rendered)
        self.assertIn("' | phase=' + repair_phase", rendered)
        self.assertIn("' | provider=' + FINAL_IMAGE_MODEL", rendered)
        self.assertIn("' | first_qa=' + str(final_qa_log)", rendered)
        self.assertIn("type(error).__name__", rendered)
        self.assertIn("flush=True", rendered)

    def test_qa_schema_and_prompt_anchor_explicit_zero_to_100_scale(self):
        self.assertIn('"minimum":\n            0', SOURCE)
        self.assertIn('"maximum":\n            100', SOURCE)
        self.assertIn("0 = complete failure", SOURCE)
        self.assertIn("50 = materially flawed/average", SOURCE)
        self.assertIn("100 = fully excellent", SOURCE)
        self.assertIn(
            "preserving values as legitimate 0-100 scores",
            SOURCE,
        )


if __name__ == "__main__":
    unittest.main()