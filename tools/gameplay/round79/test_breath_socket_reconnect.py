"""Round79K: socket reconnect must preserve saved room AND Breath."""
import unittest

from breath_socket_reconnect import require_saved_login_banner

class SavedBreathLoginTests(unittest.TestCase):
    def setUp(self):
        # Mirrors the native login after entering the Annex:
        # optional telnet negotiation, ANSI room title and numeric HUD.
        self.banner=(
            b"\xff\xfc\x01\n\r\r### Hdnecroqa the Mannish Necromancer just logged in."
            b"\n\r\x1b[36mNecromancer Trial Annex\n\r"
            b"\x1b[37mA private second room for follower verification.\n\r"
            b"\x1b[1;32mHP 1000/1000\x1b[0m | "
            b"\x1b[1;34mMP 110/110\x1b[0m | "
            b"\x1b[1;36mBreath 94/100\x1b[0m: "
        )

    def test_saved_room_and_breath_are_both_preserved(self):
        result=require_saved_login_banner(
            self.banner,"Necromancer Trial Annex",94)
        self.assertIn("Necromancer Trial Annex",result)
        self.assertIn("Breath 94/100",result)

    def test_legacy_seed_room_expectation_is_invalid(self):
        with self.assertRaisesRegex(AssertionError,"saved room"):
            require_saved_login_banner(
                self.banner,"Necromancer Grave Trial",94)

    def test_wrong_breath_denied(self):
        with self.assertRaisesRegex(AssertionError,"Breath mismatch"):
            require_saved_login_banner(
                self.banner,"Necromancer Trial Annex",100)

    def test_missing_room_denied(self):
        with self.assertRaisesRegex(AssertionError,"saved room"):
            require_saved_login_banner(b"HP 100/100 | Breath 94/100",
                                       "Necromancer Trial Annex",94)

    def test_missing_breath_denied(self):
        with self.assertRaisesRegex(AssertionError,"Breath mismatch"):
            require_saved_login_banner(
                b"Necromancer Trial Annex\nHP 1000/1000",
                "Necromancer Trial Annex",94)

    def test_invalid_expected_values_denied(self):
        for value in (-1,101,"94",None):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    require_saved_login_banner(
                        self.banner,"Necromancer Trial Annex",value)

    def test_non_socket_source_denied(self):
        with self.assertRaises(TypeError):
            require_saved_login_banner(
                "Necromancer Trial Annex | Breath 94/100",
                "Necromancer Trial Annex",94)

if __name__=="__main__":
    unittest.main(verbosity=2)
