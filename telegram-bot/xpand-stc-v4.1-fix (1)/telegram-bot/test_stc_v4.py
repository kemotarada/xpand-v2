"""Behavioral regression tests; no provider, Telegram or database calls."""
import hashlib
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import xpand_image_telegram as t
from xpand_stc_bank_skill import detect_stc_visual_style, stc_style_question_needed
from xpand_stc_brand_kit import load_default_stc_brand_kit
from xpand_stc_skill_runtime import SKILL_ROOT, core_direction, style_direction, clean_public_prompt
from xpand_creative_brain import CreativeConcept

class STCV4Tests(unittest.TestCase):
    def test_reference_integrity(self):
        atlas=json.loads((SKILL_ROOT/'references/reference-atlas.json').read_text())
        self.assertEqual(len(atlas),17)
        for row in atlas:
            p=Path(__file__).parent/'brand_assets'/row['path']
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),row['sha256'])

    def test_reference_style_and_small_budgets(self):
        kit=load_default_stc_brand_kit()
        for style in ['premium_realistic','purple_architectural','augmented_realism']:
            for limit in [1,3,5]:
                refs=kit.select_assets('merchant_payments',style,max_total=limit)
                self.assertTrue(refs)
                self.assertLessEqual(len(refs),limit)
                self.assertTrue(kit.is_style_reference(refs[0]))
                for ref in refs:
                    self.assertTrue(kit._visual_family_matches(ref,style),ref.asset_id)

    def test_runtime_loading(self):
        self.assertEqual(core_direction(),(SKILL_ROOT/'SKILL.md').read_text().strip())
        self.assertEqual(style_direction('purple_architectural'),style_direction('premium_purple_architecture'))
        self.assertIn(style_direction('premium_realistic'),load_default_stc_brand_kit().build_brand_grounding_text('premium_realistic'))

    def test_style_question_and_short_reply(self):
        self.assertTrue(stc_style_question_needed('بدي برومت فاخر لبنك STC عن السفر'))
        self.assertFalse(stc_style_question_needed('بدي برومت لبنك STC بيئة بنفسجية'))
        self.assertEqual(t.resolve_stc_style_reply('فانتزي'),'augmented_realism')
        self.assertEqual(t.resolve_stc_style_reply('واقعي'),'premium_realistic')

    def test_prompt_resume_never_generates(self):
        brief='بدي برومت لبنك STC عن شريحة السفر 4:5'
        t.remember_pending_stc_style(chat_id=901,user_id=902,request_text=brief,source_channel='telegram_text')
        self.assertIsNone(t.consume_pending_stc_style_reply(chat_id=901,user_id=999,text='2'))
        request,channel=t.consume_pending_stc_style_reply(chat_id=901,user_id=902,text='2')
        self.assertIn(brief,request)
        self.assertEqual(detect_stc_visual_style(request),'purple_architectural')
        sent=[]; calls=[]
        def writer(chat,user,text):
            calls.append(text)
            return 'Photograph the travel scene.'
        core=SimpleNamespace(_xpand_prompt_only_ask=writer,send_message=lambda c,text:sent.append(text))
        winner=CreativeConcept(core_idea='A traveler pauses at the departure bench with luggage and phone.',
            quality_gate_passed=True,evaluation_valid=True)
        reviewed=SimpleNamespace(winner=winner,ok=True,metadata={'quality_gate_passed':True})
        with patch.object(t,'prepare_generation_input',side_effect=AssertionError('Must not generate')), \
             patch.object(t,'run_creative_brain',return_value=reviewed) as brain:
            result=t.generate_and_deliver(core,901,902,request)
        self.assertEqual(brain.call_count,1)
        self.assertEqual(brain.call_args.kwargs['style_hint'],'purple_architectural')
        self.assertEqual(brain.call_args.kwargs['top_count'],1)
        self.assertEqual(result['output_kind'],'prompt')
        self.assertEqual(sent,['Photograph the travel scene.'])
        self.assertIn(style_direction('purple_architectural'),calls[0])
        self.assertIn(winner.core_idea,calls[0])
        self.assertFalse(t.get_pending_stc_style(chat_id=901,user_id=902))

    def test_failed_review_does_not_write_or_generate(self):
        core=SimpleNamespace(_xpand_prompt_only_ask=lambda *a: self.fail('Unreviewed output'),
                             send_message=lambda *a: self.fail('Unreviewed delivery'))
        rejected=SimpleNamespace(winner=None,ok=False,metadata={'quality_gate_passed':False})
        with patch.object(t,'run_creative_brain',return_value=rejected), \
             patch.object(t,'prepare_generation_input',side_effect=AssertionError('Must not generate')):
            with self.assertRaisesRegex(RuntimeError,'لم تجتز'):
                t.generate_and_deliver(core,1,2,'بدي برومت لبنك STC بيئة بنفسجية')

    def test_standalone_prompt_has_no_repository_reference_ids(self):
        returned='Violet gradients across the planes, inspired by stc_curated_02, with satin contrast.'
        self.assertEqual(clean_public_prompt(returned),
                         'Violet gradients across the planes, with satin contrast.')
        self.assertEqual(clean_public_prompt('A real plane with satin contrast.'),
                         'A real plane with satin contrast.')

    def test_other_routes(self):
        self.assertFalse(t.is_stc_prompt_only_request('أنشئ صورة لبنك STC بيئة بنفسجية'))
        self.assertFalse(t.is_stc_prompt_only_request('STC Bank write a prompt and generate the image'))
        self.assertFalse(t.is_stc_prompt_only_request('اكتب برومت لسيارة'))
        self.assertTrue(t.looks_like_image_generation_request('اعطيني برومت لبنك STC'))

if __name__=='__main__':
    unittest.main()
