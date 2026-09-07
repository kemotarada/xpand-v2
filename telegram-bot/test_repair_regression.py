import ast
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
            "qa_flags_text_logo_failure",
            "qa_flags_copy_space_failure",
            "build_final_repair_prompt",
            extra={
                "reference_role_manifest": no_reference_manifest,
                "qa_feedback_summary": lambda value: "QA failure",
                "build_immutable_final_locks": (
                    lambda **kwargs: "LOCK authority="
                    + str(kwargs["reference_authority"])
                ),
                "fit_prompt_with_immutable_locks": (
                    lambda core, locks, **kwargs: core + "\n" + locks
                ),
                "CORRECTION_PROMPT_BUDGET": 7600,
            },
        )

        prompt = namespace["build_final_repair_prompt"](
            qa=qa(),
            compiled=types.SimpleNamespace(prompt="approved"),
            original_request="STC merchant campaign",
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

    def test_mixed_text_logo_and_copy_space_allows_bounded_reframe(self):
        namespace = load_functions(
            "qa_flags_text_logo_failure",
            "qa_flags_copy_space_failure",
            "build_final_repair_prompt",
            extra={
                "reference_role_manifest": (
                    lambda *args, **kwargs: "must not be reached"
                ),
                "qa_feedback_summary": lambda value: "mixed QA failure",
                "build_immutable_final_locks": (
                    lambda **kwargs: "NO artificial blank panel"
                ),
                "fit_prompt_with_immutable_locks": (
                    lambda core, locks, **kwargs: core + "\n" + locks
                ),
                "CORRECTION_PROMPT_BUDGET": 7600,
            },
        )
        mixed = qa(
            scores={
                "text_logo_compliance": 25.0,
                "copy_space_composition": 70.0,
                "advertising_readiness": 76.0,
            },
            critical_blockers=[
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
        )

        prompt = namespace["build_final_repair_prompt"](
            qa=mixed,
            compiled=types.SimpleNamespace(prompt="approved"),
            original_request="STC merchant campaign",
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


if __name__ == "__main__":
    unittest.main()