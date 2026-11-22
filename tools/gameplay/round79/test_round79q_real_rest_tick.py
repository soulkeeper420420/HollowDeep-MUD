"""Round79Q: test natural real-socket Breath pulse validation semantics."""
import unittest
from pathlib import Path

import round79q_real_rest_tick as tick

class Round79QNaturalRestTickTests(unittest.TestCase):
    def test_parse_numeric_native_prompt(self):
        self.assertEqual(tick.parse_breath(
            "HP 1000/1000 | MP 110/110 | Breath 74/100: "),74)

    def test_last_numeric_value_wins_if_multiple_prompts(self):
        self.assertEqual(tick.parse_breath(
            "Breath 94/100:\r\nBreath 76/100: "),76)

    def test_missing_hud_fails_closed(self):
        with self.assertRaisesRegex(AssertionError,"HUD missing"):
            tick.parse_breath("HP 100/100, MP 10/10")

    def test_invalid_hud_fails_closed(self):
        with self.assertRaisesRegex(AssertionError,"Invalid"):
            tick.parse_breath("Breath 101/100:")

    def test_exact_fifteen_is_distinct_from_normal_five(self):
        self.assertEqual(tick.check_pulse_transition(75,90),"rest_plus15")
        self.assertEqual(tick.check_pulse_transition(75,80),"normal_plus5")
        self.assertEqual(tick.check_pulse_transition(75,75),"unchanged")

    def test_two_normal_five_pulses_do_not_pass_as_rest(self):
        with self.assertRaisesRegex(AssertionError,"Unexpected"):
            tick.check_pulse_transition(75,85)

    def test_overshoot_or_rollback_fails_closed(self):
        with self.assertRaisesRegex(AssertionError,"Unexpected"):
            tick.check_pulse_transition(75,91)
        with self.assertRaisesRegex(AssertionError,"Unexpected"):
            tick.check_pulse_transition(75,73)

    def test_capped_rest_pulse_is_not_false_positive(self):
        with self.assertRaisesRegex(AssertionError,"Unexpected"):
            tick.check_pulse_transition(92,100)
        with self.assertRaisesRegex(AssertionError,"Unexpected"):
            tick.check_pulse_transition(88,100)

    def test_breath_bounds(self):
        with self.assertRaisesRegex(AssertionError,"Out-of-range"):
            tick.check_pulse_transition(-1,15)
        with self.assertRaisesRegex(AssertionError,"Out-of-range"):
            tick.check_pulse_transition(80,101)

    def test_opt_in_original_socket_script_and_safety(self):
        original=(Path(__file__).parent/"check_breath_rest_socket.py").read_text()
        self.assertIn('os.environ.get("HD79Q_TIMED_REST")=="1"',original)
        self.assertIn("run_natural_rest_tick(returning,prior,ask,clean)",
                      original)
        self.assertLess(
            original.index('ask(returning,"skills","Breath 94/100")'),
            original.index("run_natural_rest_tick(returning,prior,ask,clean)"))
        self.assertIn("with prior[\"connect_game\"](port,process) as returning:",
                      original)

    def test_do_not_modify_game_or_clock(self):
        source=(Path(__file__).parent/"round79q_real_rest_tick.py").read_text()
        self.assertNotIn("os.utime",source)
        self.assertNotIn("time.time =",source)
        self.assertNotIn("hd_breath_store_step",source)
        self.assertNotIn("write_bytes(",source)
        self.assertNotIn("write_text(",source)

if __name__=="__main__":
    unittest.main(verbosity=2)
