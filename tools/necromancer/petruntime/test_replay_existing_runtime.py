import re
from types import SimpleNamespace
import unittest

from replay_existing_runtime import correct_movement


SOURCE = """def replay(command, view, require, owner, faithful):
    command(owner, 'north'); one_pet(owner, 'Necromancer Trial Annex')
    durable_logout(owner)
    assert_disk_inventory(owner)
    command(faithful,'north'); one_pet(faithful, 'Necromancer Trial Annex')
"""


class ReplayMovementTest(unittest.TestCase):
    def test_preserves_assertions_and_is_idempotent(self):
        corrected, count = correct_movement(SOURCE)
        self.assertEqual(count, 2)
        for line in ('    durable_logout(owner)\n', '    assert_disk_inventory(owner)\n',
                     "; one_pet(faithful, 'Necromancer Trial Annex')"):
            self.assertIn(line, corrected)
        self.assertEqual(correct_movement(corrected), (corrected, 0))

    def run_moves(self, responses, room='Necromancer Trial Annex'):
        clock = [0]
        calls = []

        def sleep(delay):
            clock[0] += delay

        def command(client, verb):
            calls.append((client, verb))
            return next(responses)

        def require(text, marker):
            if marker not in text:
                raise RuntimeError('Wrong room')

        scope = dict(re=re, time=SimpleNamespace(monotonic=lambda: clock[0], sleep=sleep),
                     one_pet=lambda *_: None, durable_logout=lambda _: None,
                     assert_disk_inventory=lambda _: None)
        exec(correct_movement(SOURCE)[0], scope)
        scope['replay'](command, lambda _: room, require, 'owner', 'faithful')
        return calls, clock[0]

    def test_singular_plural_and_success(self):
        calls, seconds = self.run_moves(iter([
            'Please wait 1 more second.', 'Please wait 2 more seconds.',
            'Necromancer Trial Annex', 'Necromancer Trial Annex']))
        self.assertEqual(calls, [('owner', 'north')] * 3 + [('faithful', 'north')])
        self.assertAlmostEqual(seconds, 3.4)

    def test_success_via_room_view(self):
        calls, seconds = self.run_moves(iter(['You move north.', 'You move north.']))
        self.assertEqual(len(calls), 2)
        self.assertEqual(seconds, 0)

    def test_unexpected_failure_is_not_retried(self):
        with self.assertRaisesRegex(RuntimeError, 'Wrong room'):
            self.run_moves(iter(['The passage is blocked.']), room='Necromancer Grave Trial')

    def test_bounds_attempts_and_delay(self):
        for replies in (['Please wait 1 more second.'] * 6,
                        ['Please wait 45 more seconds.']):
            with self.assertRaisesRegex(RuntimeError, 'retry budget'):
                self.run_moves(iter(replies))


if __name__ == '__main__':
    unittest.main()
