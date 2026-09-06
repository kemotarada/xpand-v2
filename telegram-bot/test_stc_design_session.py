"""Regression coverage for the real prompt -> critique -> choices -> selection flow."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import xpand_image_telegram as t
import xpand_stc_design_session as s
from xpand_creative_brain import CreativeConcept

BRIEF = 'بدي برومت فقط لبنك STC عن شريحة السفر شريحتك معك بكل وجهة مقاس 4:5 بيئة بنفسجية استوديو'
FEEDBACK = ('الفكرة الحالية تعتمد على اختلاف الخامات أكثر من توصيل فائدة شريحة السفر. '
            'أعد تطوير الفكرة واقترح 3 أفكار مختلفة جذريًا في تكوين المشهد وزاوية التصوير. '
            'لا تستخدم خطوط مضيئة ولا تكتب البرومت النهائي حتى أختار الفكرة.')


def concept(name):
    return CreativeConcept(title=name, core_idea='مشهد سفر ' + name,
        marketing_message='الاتصال أثناء السفر', camera_angle='Low-angle shot',
        quality_gate_passed=True, evaluation_valid=True)


def reviewed(*items):
    return SimpleNamespace(winner=items[0], top_concepts=list(items), ok=True,
                           metadata={'quality_gate_passed': True})


class DesignSessionTests(unittest.TestCase):
    def setUp(self):
        s._sessions.clear()
        self.writer = Mock(return_value='A polished photographic travel scene. No text or logos.')
        self.sent = Mock()
        self.core = SimpleNamespace(_xpand_prompt_only_ask=self.writer, send_message=self.sent)

    def start(self):
        with patch.object(t, 'run_creative_brain', return_value=reviewed(concept('الأصل'))):
            t.generate_and_deliver(self.core, 10, 20, BRIEF)

    def test_exact_followup_uses_review_without_final_prompt_or_image(self):
        self.start()
        self.writer.reset_mock()
        with patch.object(t, 'run_creative_brain', return_value=reviewed(concept('المطار'), concept('الأمتعة'), concept('المقعد'))) as brain, \
             patch.object(t, 'prepare_generation_input', side_effect=AssertionError('No images')):
            self.assertTrue(t.handle_text_image_request(self.core, 10, 20, FEEDBACK))
        self.assertEqual(brain.call_count, 1)
        args = brain.call_args.kwargs
        self.assertEqual(args['top_count'], 3)
        self.assertEqual(args['style_hint'], 'purple_architectural')
        self.assertIn('4:5', args['user_request'])
        self.assertIn('شريحة السفر', args['user_request'])
        self.assertIn('لا تستخدم خطوط مضيئة', args['user_request'])
        self.writer.assert_not_called()
        self.assertEqual(len(s.get_session(10, 20)['choices']), 3)

    def test_selection_compiles_exact_second_option_without_new_ideation(self):
        self.start()
        with patch.object(t, 'run_creative_brain', return_value=reviewed(concept('الأول'), concept('الثاني'), concept('الثالث'))):
            t.handle_text_image_request(self.core, 10, 20, FEEDBACK)
        self.writer.reset_mock()
        with patch.object(t, 'run_creative_brain', side_effect=AssertionError('Do not replace selection')):
            self.assertTrue(t.handle_text_image_request(self.core, 10, 20, 'اختار الفكرة الثانية'))
        supplied = self.writer.call_args.args[2]
        approved_block = supplied.split('XPAND APPROVED CREATIVE DIRECTION')[-1]
        self.assertIn('مشهد سفر الثاني', approved_block)
        self.assertNotIn('مشهد سفر الأول', approved_block)

    def test_revised_selection_is_reviewed_and_keeps_selected_context(self):
        self.start()
        with patch.object(t, 'run_creative_brain', return_value=reviewed(concept('الأول'), concept('الثاني'))):
            t.handle_text_image_request(self.core, 10, 20, FEEDBACK)
        with patch.object(t, 'run_creative_brain', return_value=reviewed(concept('الثاني المعدل'))) as brain:
            t.handle_text_image_request(self.core, 10, 20, 'اختار الثانية وعدل زاوية التصوير لتكون منخفضة')
        self.assertIn('USER-SELECTED CONCEPT', brain.call_args.kwargs['user_request'])

    def test_ordinary_chat_other_brands_and_other_users_are_not_captured(self):
        self.start()
        for text in ['مرحبا', 'تم', 'كم الساعة؟', 'بدي 3 أفكار لمطعم', '4:5']:
            self.assertIsNone(s.route_turn(t, 10, 20, text), text)
        self.assertIsNone(s.route_turn(t, 10, 99, FEEDBACK))
        self.assertIsNone(s.route_turn(t, 99, 20, FEEDBACK))

    def test_expiry_and_cancel(self):
        self.start()
        with patch.object(s.time, 'time', return_value=s.time.time() + s.TTL_SECONDS + 1):
            self.assertIsNone(s.route_turn(t, 10, 20, FEEDBACK))
        self.start()
        self.assertIn('إنهاء', t.stc_design_reply(self.core, 10, 20, 'الغاء التصميم'))
        self.assertIsNone(s.get_session(10, 20))

    def test_unsafe_options_filtered_and_count_is_honest(self):
        self.start()
        bad = concept('خريطة')
        bad.core_idea = 'World map with glowing routes'
        with patch.object(t, 'run_creative_brain', return_value=reviewed(concept('المقعد'), bad)):
            t.handle_text_image_request(self.core, 10, 20, FEEDBACK)
        answer = self.sent.call_args.args[1]
        self.assertNotIn('World map', answer)
        self.assertIn('1 من الأفكار فقط', answer)
        self.assertEqual(len(s.get_session(10, 20)['choices']), 1)

    def test_failed_review_never_falls_back_to_chat(self):
        self.start()
        before = s.get_session(10, 20)
        self.writer.reset_mock()
        with patch.object(t, 'run_creative_brain', return_value=SimpleNamespace(winner=None, ok=False)):
            self.assertTrue(t.handle_text_image_request(self.core, 10, 20, FEEDBACK))
        self.writer.assert_not_called()
        self.assertIn('لم تجتز', self.sent.call_args.args[1])
        self.assertEqual(before, s.get_session(10, 20))

    def test_voice_wrapper_uses_same_session_before_generic_chat(self):
        original = Mock(return_value='generic chat')
        core = SimpleNamespace(ask_kemo=original, send_message=Mock())
        with patch.object(t, 'get_image_engine_status', return_value={}):
            t.install(core)
        s.save_session(10, 20, {'brief': BRIEF, 'style': 'purple_architectural', 'choices': [], 'last_answer': 'previous'})
        with patch.object(t, 'run_creative_brain', return_value=reviewed(concept('الأمتعة'))):
            answer = core.ask_kemo(10, 20, FEEDBACK)
        self.assertIn('الأمتعة', answer)
        original.assert_not_called()
        core.send_message.assert_not_called()  # voice caller owns delivery

    def test_initial_ideas_style_gate_and_resume(self):
        text = 'اقترح 3 أفكار لبنك STC عن شريحة السفر'
        answer = t.stc_design_reply(self.core, 40, 50, text)
        self.assertIn('أسلوب', answer)
        resumed, _ = t.consume_pending_stc_style_reply(chat_id=40, user_id=50, text='2')
        with patch.object(t, 'run_creative_brain', return_value=reviewed(concept('المطار'))):
            result = t.generate_and_deliver(self.core, 40, 50, resumed)
        self.assertEqual(result['output_kind'], 'ideas')
        self.writer.assert_not_called()

    def test_explicit_rendering_and_non_stc_prompts_keep_existing_route(self):
        self.start()
        self.assertIsNone(s.route_turn(t, 10, 20, 'ولد الصورة'))
        self.assertIsNone(s.route_turn(t, 10, 20, 'STC Bank write a prompt and generate the image'))
        self.assertIsNone(s.route_turn(t, 10, 20, 'اكتب برومت لسيارة'))

    def test_short_followups_and_style_switch(self):
        self.start()
        self.assertIsNotNone(s.route_turn(t, 10, 20, 'بدي برومت ثاني'))
        self.assertIsNotNone(s.route_turn(t, 10, 20, 'غيرها'))
        self.assertEqual(s.choice_number('الثانية'), 2)
        with patch.object(t, 'run_creative_brain', return_value=reviewed(concept('الواقعي'))) as brain:
            t.handle_text_image_request(self.core, 10, 20, 'واقعي')
        self.assertEqual(brain.call_args.kwargs['style_hint'], 'premium_realistic')

    def test_fresh_brief_resets_old_service(self):
        self.start()
        task = s.route_turn(t, 10, 20, 'طلب جديد لبنك STC برومت عن التمويل بأسلوب واقعي')
        self.assertIsNone(task['state'])


if __name__ == '__main__':
    unittest.main()
