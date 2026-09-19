# test_xpand_stc_ad_brain.py
from __future__ import annotations

import unittest
from xpand_stc_ad_brain import STCAdBrain, AdConcept, AdCopy


class TestSTCAdBrain(unittest.TestCase):
    def setUp(self):
        self.brain = STCAdBrain()

    def test_generate_concepts_merchant_payments(self):
        concepts = self.brain.generate_concepts("merchant_payments", "purple_architectural")
        self.assertGreaterEqual(len(concepts), 6, "Expected at least 6 merchant payment concepts")
        for concept in concepts:
            self.assertIsInstance(concept, AdConcept)
            self.assertTrue(concept.concept_id)
            self.assertTrue(concept.title)
            self.assertTrue(concept.core_idea)

    def test_shortlist_diversity(self):
        concepts = self.brain.generate_concepts("merchant_payments", "purple_architectural")
        shortlisted = self.brain.shortlist(concepts, top_n=3)
        self.assertEqual(len(shortlisted), 3, "Expected exactly 3 shortlisted concepts")
        
        # Ensure diversity tags reduce overlap
        tag_sets = [set(c.diversity_tags) for c in shortlisted]
        self.assertGreater(len(tag_sets), 0)

    def test_generate_premium_copy_merchant_payments(self):
        copies = self.brain.generate_premium_copy("merchant_payments")
        self.assertGreater(len(copies), 0)
        copy = copies[0]
        self.assertIsInstance(copy, AdCopy)
        self.assertTrue(copy.headline_ar)
        self.assertTrue(copy.headline_en)
        self.assertTrue(copy.hook_ar)
        self.assertTrue(copy.hook_en)
        self.assertIn("stc bank", copy.body_copy_en.lower())

    def test_generate_premium_copy_international_transfer(self):
        copies = self.brain.generate_premium_copy("international_transfer")
        self.assertGreater(len(copies), 0)
        copy = copies[0]
        self.assertTrue(copy.headline_ar)
        self.assertTrue(copy.headline_en)


if __name__ == "__main__":
    unittest.main()
