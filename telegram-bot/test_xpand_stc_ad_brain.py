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
        self.assertTrue(copy.factuality_note)
        self.assertEqual(copy.brand_memory_tag, "stc_bank_merchant_2024_v2")
        self.assertIn("twitter", copy.channel_variants)
        self.assertIn("instagram", copy.channel_variants)
        self.assertIn("linkedin", copy.channel_variants)
        self.assertIn("whatsapp", copy.channel_variants)

    def test_generate_premium_copy_international_transfer(self):
        copies = self.brain.generate_premium_copy("international_transfer")
        self.assertGreater(len(copies), 0)
        copy = copies[0]
        self.assertTrue(copy.headline_ar)
        self.assertTrue(copy.headline_en)
        self.assertTrue(copy.factuality_note)
        self.assertEqual(copy.brand_memory_tag, "stc_bank_remittance_2024_v2")
        self.assertIn("tiktok", copy.channel_variants)

    def test_generate_all_benefit_families_copy(self):
        families = [
            "merchant_payments",
            "international_transfer",
            "wealth_management",
            "savings_vaults",
            "business_financing",
            "digital_wallets",
            "card_issuing",
            "corporate_expense_management"
        ]
        for family in families:
            copies = self.brain.generate_premium_copy(family)
            self.assertGreater(len(copies), 0, f"Expected copy for {family}")
            for item in copies:
                self.assertTrue(item.headline_ar)
                self.assertTrue(item.headline_en)
                self.assertTrue(item.factuality_note)
                self.assertTrue(item.brand_memory_tag)
                self.assertTrue(item.saudi_cultural_fit)
                self.assertIsInstance(item.to_dict(), dict)


if __name__ == "__main__":
    unittest.main()
