"""Offline tests; no bot imports, provider calls, or credentials."""
import ast
from pathlib import Path
import unittest


SOURCE = Path(__file__).with_name("xpand_image_telegram.py")
TREE = ast.parse(SOURCE.read_text(encoding="utf-8"))
FUNCTIONS = [
    node for node in TREE.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "production_failure_message"
]
NAMESPACE = {}
exec(compile(ast.Module(body=FUNCTIONS, type_ignores=[]), str(SOURCE), "exec"),
     NAMESPACE)
message = NAMESPACE["production_failure_message"]


class FailureReportingTests(unittest.TestCase):
    def test_quality_rejection_is_not_provider_failure(self):
        text = message("quality_failure", [{"errors": []}])
        self.assertIn("رفض جودة", text)
        self.assertNotIn("تعثرت", text)

    def test_repair_error_is_not_hidden_by_previous_qa(self):
        text = message("quality_failure", [
            {"errors": ["final_repair: do-not-leak-provider-response"]}
        ])
        self.assertIn("تعثرت محاولة", text)
        self.assertIn("FINAL_REPAIR_FAILURE", text)
        self.assertNotIn("do-not-leak", text)

    def test_technical_error_does_not_blame_billing(self):
        text = message("technical_failure", [])
        self.assertIn("خطأ تقني", text)
        self.assertNotIn("رفض جودة", text)

    def test_bad_metadata_row_is_ignored(self):
        self.assertIn("رفض جودة", message("quality_failure", [None, {}]))


if __name__ == "__main__":
    unittest.main()